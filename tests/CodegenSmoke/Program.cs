using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using CityLBM.Core;
using CityLBM.Solver;
using Newtonsoft.Json.Linq;
using Rhino.Geometry;

namespace CityLBM.CodegenSmoke
{
    internal static class Program
    {
        private static int Main()
        {
            ConfigureRhinoNativeRuntime();

            bool acquiredSmokeLock = false;
            var smokeLock = new System.Threading.Mutex(false, "Local\\CityLBMCodegenSmoke");
            try
            {
                acquiredSmokeLock = smokeLock.WaitOne(TimeSpan.FromSeconds(60));
                if (!acquiredSmokeLock)
                    throw new TimeoutException("Timed out waiting for the shared CodegenSmoke temp-directory lock.");

                var scene = BuildScene();
                var grid = new CartesianGrid
                {
                Nx = 16,
                Ny = 16,
                Nz = 16,
                Dx = 2.0,
                Origin = new Point3d(-60, -120, -4),
                DomainBounds = new BoundingBox(new Point3d(-60, -120, -4), new Point3d(70, 60, 70))
            };
                var settings = new SimulationSettings
                {
                    TimeSteps = 1000,
                    SaveInterval = 100,
                    VtkSaveStartStep = 250,
                    EnableSyntheticTurbulentInlet = true,
                    SyntheticTurbulenceIntensityScale = 1.0,
                    SyntheticTurbulenceCorrelationCells = 4.0,
                    SyntheticTurbulenceLengthScaleSource = "aij_length_scale_verified: smoke-test archived integral length evidence",
                    SyntheticTurbulenceUpdateInterval = 7,
                    SyntheticTurbulenceMaxFractionOfMean = 0.42
                };

                string fakeFluidX3DRoot = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source");
                var solver = new FluidX3DInterface(fakeFluidX3DRoot);
                string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "stg_codegen_smoke");
                Directory.CreateDirectory(caseDir);
                Directory.CreateDirectory(Path.Combine(caseDir, "output"));
                string setupPath = Path.Combine(caseDir, "setup.cpp");
                string definesPath = Path.Combine(caseDir, "defines.hpp");
                string graphicsDefinesPath = Path.Combine(caseDir, "defines_graphics.hpp");
                string stlPath = Path.Combine(caseDir, "buildings.stl");

                InvokePrivate(
                    solver,
                    "GenerateSetupCpp",
                    scene,
                    grid,
                    settings,
                    setupPath,
                    "buildings.stl",
                    "output");
                InvokePrivate(solver, "GenerateDefinesHpp", scene, grid, settings, definesPath, false);
                InvokePrivate(solver, "GenerateDefinesHpp", scene, grid, settings, graphicsDefinesPath, true);
                WriteSmokeBinaryStl(stlPath);
                InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
                InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

                string setup = File.ReadAllText(setupPath);
                string defines = File.ReadAllText(definesPath);
                string graphicsDefines = File.ReadAllText(graphicsDefinesPath);
                string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
                string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));
                string nativeManifest = File.ReadAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.json"));

                Require(setup, "profile_k_lbm[profile_count]");
                Require(setup, "profile_r11_lbm[profile_count]");
                Require(setup, "profile_r22_lbm[profile_count]");
                Require(setup, "profile_r33_lbm[profile_count]");
                Require(setup, "profile_r12_lbm[profile_count]");
                Require(setup, "profile_r13_lbm[profile_count]");
                Require(setup, "profile_r23_lbm[profile_count]");
                Require(setup, "Reynolds-stress arrays are derived from the isotropic-k assumption");
                Require(setup, "const float profile_origin_z_m = -4.00000000f;");
                Require(setup, "float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * 2.00000000f;");
                Require(setup, "citylbm_stg_mode_count");
                Require(setup, "citylbm_stg_norm_x");
                Require(setup, "citylbm_stg_norm_y");
                Require(setup, "citylbm_stg_norm_z");
                Require(setup, "fluct_x *= citylbm_stg_norm_x");
                Require(setup, "fluct_y *= citylbm_stg_norm_y");
                Require(setup, "fluct_z *= citylbm_stg_norm_z");
                Require(setup, "citylbm_stg_target_sigma");
            Require(setup, "citylbm_stg_layer_corrected_sum_sq_x");
            Require(setup, "citylbm_stg_layer_rms_scale_x");
            Require(setup, "target_sigma.x / rms_x");
            Require(setup, "citylbm_stg_layer_tensor_whitening_valid");
            Require(setup, "citylbm_stg_layer_corrected_sum_xy");
            Require(setup, "CityLBMReynoldsCholesky target_l = citylbm_stg_target_reynolds_cholesky(z_m);");
            Require(setup, "u_in.x = mean.x + citylbm_stg_scale * target_l.l11 * w1;");
            Require(setup, "u_in.x = mean.x + fluct_x * citylbm_stg_layer_rms_scale_x[z];");
                RequireNotContains(setup, "sqrtf(6.0f / (float)citylbm_stg_mode_count)");
                Require(setup, "citylbm_mode_amplitude");
                Require(setup, "ak*kx");
                Require(setup, "continuous-step Taylor frozen-turbulence advection");
                Require(setup, "float citylbm_stg_advect_steps = (float)t_step * citylbm_stg_temporal_step_scale;");
                Require(setup, "float advected_x = (float)x - dir_x * mean_mag * citylbm_stg_advect_steps;");
                Require(setup, "float phase = kx * advected_x + ky * advected_y + kz * advected_z;");
                Require(setup, "Target component RMS uses measured diagonal RMS");
                Require(setup, "nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx");
                Require(setup, "no longer clamps tau to 0.55");
                Require(setup, "LBM lbm(SX, SY, SZ, 1.29310345E-007f)");
                Require(defines, "velocity_scale_mps_to_lbm");
                Require(defines, "nu_lbm = nu_physical * velocity_scale_mps_to_lbm / dx");
                Require(defines, "#define TAU 5.00000388E-001f");
                RequireNotContains(defines, Environment.NewLine + "#define GRAPHICS");
                Require(graphicsDefines, "#define GRAPHICS_LSF             4u");
                Require(graphicsDefines, "#define GRAPHICS_LSQ             8u");
                Require(graphicsDefines, "#define GRAPHICS_LSP             4u");
                Require(setup, "citylbm_stg_update_interval = 7u");
                Require(setup, "float citylbm_stg_prev_t_step = t_step > citylbm_stg_update_interval ? (float)(t_step - citylbm_stg_update_interval) : 0.0f;");
                Require(setup, "return direction * (float)h * 0.25f / citylbm_stg_corr_cells");
                Require(setup, "citylbm_stg_max_fraction = 0.420000f");
                Require(setup, "citylbm_stg_min_streamwise_fraction = 0.000000f");
                Require(setup, "Default is no streamwise clipping");
                Require(setup, "if(citylbm_stg_min_streamwise_fraction > 0.0f)");
                RequireNotContains(setup, "0.05f * (mean_mag");
                Require(setup, "#include <fstream>");
                Require(setup, "#include <vector>");
                Require(setup, "citylbm_inlet_diagnostics_csv");
                Require(setup, "_inlet_turbulence_stats.csv");
                Require(setup, "target_U_mps");
                Require(setup, "target_k_m2s2");
                Require(setup, "target_r11_m2s2");
                Require(setup, "target_r12_m2s2");
                Require(setup, "measured_r11_m2s2");
                Require(setup, "measured_r12_m2s2");
                Require(setup, "sum_xy += ux*uy");
                Require(setup, "measured_r12 = sum_xy * inv - mean_x * mean_y");
                Require(setup, "effective_sample_z_cell");
                Require(setup, "Runtime inlet diagnostics: written by the generated FluidX3D case");
                Require(setup, "syntheticTurbulentInlet");
                Require(setup, "applySyntheticTurbulentInlet");
                Require(setup, "synthetic_eddy_count");
                Require(setup, "updateSyntheticEddyPlane");
                Require(setup, "updateTemporalFilter");
                Require(setup, "bool citylbm_sem_eddy_initialized = false;");
                Require(setup, "initializeSyntheticEddyPopulation");
                Require(setup, "wrapSyntheticEddyPopulation");
                Require(setup, "sem_eddy[m].eddy_center_x += dir_x * advect;");
                Require(setup, "sem_eddy[m].eddy_center_y += dir_y * advect;");
                Require(setup, "sem_eddy[m].eddy_center_z += dir_z * advect;");
                RequireNotContains(setup, "sem_eddy[m].eddy_center_x = hash01(seed + 11u) * (float)Nx - dir_x * advect;");
                RequireNotContains(setup, "sem_eddy[m].eddy_center_y = hash01(seed + 23u) * (float)Ny - dir_y * advect;");
                RequireNotContains(setup, "sem_eddy[m].eddy_center_z = hash01(seed + 37u) * (float)Nz - dir_z * advect;");
                RequireNotContains(setup, "updateDigitalFilter");
                Require(setup, "turbulentWind");
                Require(setup, "applyInlet");
                Require(setup, "compactCosine");
                Require(setup, "periodicDistance");
                Require(setup, "GRAPHICS mode uses the same STG refresh loop as batch mode");
                Require(setup, "const uint citylbm_total_steps = 1000u;");
                Require(setup, "const uint citylbm_save_interval = 100u;");
                Require(setup, "const uint citylbm_vtk_save_start_step = 250u;");
                Require(setup, "uint citylbm_next_vtk_save_step = citylbm_vtk_save_start_step > 0u ? citylbm_vtk_save_start_step : citylbm_save_interval;");
                Require(setup, "const bool citylbm_has_vtk_schedule = citylbm_next_vtk_save_step <= citylbm_total_steps;");
                Require(setup, "bool citylbm_should_save_vtk = citylbm_has_vtk_schedule");
                Require(setup, "while(citylbm_next_vtk_save_step <= (uint)lbm.get_t()) citylbm_next_vtk_save_step += citylbm_save_interval;");
                Require(setup, "steps_to_run = remaining < citylbm_stg_update_interval ? remaining : citylbm_stg_update_interval");
                Require(setup, "refresh saved VTK inlet boundary to the current CustomTable+k/Rij target");
                Require(setup, "if(lbm.flags[n] == TYPE_E &&");
                Require(setup, "lbm.flags.read_from_device();");
                Require(setup, "lbm.flags.write_to_device();");
                Require(setup, "lbm.reconstruct_inlet_stress_boundaries();");
                Require(defines, "#define RECONSTRUCT_INLET_STRESS_DDF");
                Require(defines, "#define INLET_STRESS_U_REF_LBM 0.10000000f");
                Require(setup, "initialize all TYPE_E boundary velocities");
                Require(setup, "fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces");
                Require(setup, "Outlet/lateral/top TYPE_E faces receive the mean profile velocity");
                Require(setup, "if(lbm.flags[n] != TYPE_E) return;");
                Require(setup, "float3 u_e = windProfile(z);");
                Require(setup, "equivalent rough-wall drag in the near-ground layer");
                Require(setup, "rough_wall_function");
                Require(setup, "rough_wall_drag_limit");
                Require(setup, "apply_rough_wall();");
                Require(setup, "lbm.F.x[n] = -rough_wall_drag * ux / horizontal_speed;");
                Require(setup, "profile-maintenance FORCE_FIELD buffer near open boundaries");
                Require(setup, "boundary_profile_maintenance_layer_cells = 8.0f");
                Require(setup, "boundary_profile_maintenance_gain = 0.00150000f");
                Require(setup, "boundary_profile_maintenance_max_force = 0.00030000f");
                Require(setup, "apply_boundary_profile_maintenance_buffer();");
                Require(setup, "lbm.F.x[n] += force_scale * target.x;");
                Require(setup, "lbm.F.write_to_device();");
                Require(metadata, "divergence-reduced spectral modes");
                Require(metadata, "persistent compact synthetic eddies");
                Require(metadata, "continuous-step Taylor frozen-turbulence phase advection");
                Require(metadata, "persistent synthetic_eddy centers advected/wrapped");
                Require(metadata, "projected normal to synthetic wave vectors");
                Require(metadata, "component RMS target sigma=sqrt(2k/3)");
                Require(metadata, "per_z_cell inlet-face RMS rescaling");
                Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingCorrection\": true");
                Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingScope\": \"per_z_cell_inlet_layer\"");
                Require(metadata, "actual inlet-face RMS matches the k-derived target sigma=sqrt(2k/3)");
                Require(metadata, "\"SyntheticTurbulenceUpdateInterval\": 7");
                Require(metadata, "\"SyntheticTurbulenceMinimumRecommendedRefreshes\": 200");
                Require(metadata, "\"SyntheticTurbulenceExpectedFinalWindowRefreshCount\": 107");
                Require(metadata, "\"SyntheticTurbulentInletTemporalSamplingGate\": \"diagnostic_only_insufficient_stg_refreshes_in_average_window\"");
                Require(metadata, "\"SyntheticTurbulenceMaxFractionOfMean\": 0.42");
                Require(metadata, "\"SyntheticTurbulenceMinStreamwiseFraction\": 0.0");
                Require(metadata, "\"SyntheticTurbulenceStreamwiseClippingTreatment\": \"disabled_no_streamwise_clipping_of_k_perturbations\"");
                Require(metadata, "\"SyntheticTurbulenceCorrelationLengthM\": 8.0");
                Require(metadata, "aij_length_scale_verified: smoke-test archived integral length evidence");
                Require(metadata, "\"SyntheticTurbulentInletLengthScaleGate\": \"pass\"");
                Require(metadata, "fluidx3d_RECONSTRUCT_INLET_STRESS_DDF");
                Require(metadata, "after macroscopic velocity update");
                Require(metadata, "\"InletDistributionFunctionReconstruction\": true");
                Require(metadata, "\"SyntheticTurbulentInletPaperGradeStatus\": \"diagnostic_only_until_distribution_reconstruction_reynolds_stress_or_precursor_evidence_and_native_u_k_correlation_gates_pass\"");
                Require(metadata, "\"RuntimeInletDiagnosticsCsv\":");
                Require(metadata, "_inlet_turbulence_stats.csv");
                Require(metadata, "generated_setup_cpp_applyInlet_writes_profile_layer_U_RMS_k_csv");
                Require(metadata, "target_r11_m2s2");
                Require(metadata, "measured_r12_m2s2");
                Require(metadata, "effective_sample_z_cell");
                RequireNotContains(metadata, "diagnostic_only_until_distribution_reconstruction_or_native_k_preservation_gate_passes");
                Require(metadata, "\"PaperGradeTurbulentInletPrerequisiteGate\": \"fail\"");
                Require(metadata, "measured_or_precursor_reynolds_stress_tensor");
                Require(metadata, "empty_tunnel_U_k_correlation_preservation_gate");
                Require(metadata, "\"InletReynoldsStressTensorAvailable\": false");
                Require(metadata, "isotropic_from_k_only_R11_R22_R33_2k_over_3_R12_R13_R23_0");
                Require(metadata, "\"InletReynoldsStressTensorSource\": \"isotropic_k_assumption_from_AF_k_column\"");
                Require(metadata, "\"InletReynoldsStressTensorPaperGradeGate\": \"fail_requires_measured_or_precursor_tensor_and_distribution_consistent_inlet\"");
                Require(metadata, "\"InletReynoldsStressComponents\"");
                Require(metadata, "\"R11\": \"2k/3\"");
                Require(metadata, "\"R12\": \"0\"");
                Require(metadata, "\"InletReynoldsStressOffDiagonalTreatment\": \"R12=R13=R23=0 isotropic assumption\"");
                Require(metadata, "\"VtkSaveStartStep\": 250");
                Require(metadata, "\"ExpectedVtkFrameCount\": 9");
                Require(metadata, "\"ExpectedVtkSourceTimeSteps\"");
                Require(metadata, "\"SaveStartStep\": 250");
                Require(metadata, "\"TimeAveragingRunGate\": \"smoke_only_too_few_frames_for_validation\"");
                Require(metadata, "\"PaperRecommendedAveragingFrames\": 40");
                Require(metadata, "\"PaperRecommendedAverageStepSpan\": 20000");
                Require(metadata, "\"ExpectedPaperAverageStepSpan\": 750");
                Require(metadata, "\"PaperRecommendedAdaptiveAveragingFrames\": 201");
                Require(metadata, "\"ExpectedAdaptivePaperAverageStepSpan\": 750");
                Require(metadata, "automatically increase the final-window frame count");
                Require(metadata, "\"TimeAveragingPaperGate\": \"diagnostic_only_extend_time_steps_or_reduce_save_interval\"");
                Require(metadata, "Mode 1/2/3 require ExpectedVtkFrameCount");
                Require(metadata, "\"LbmTau\"");
                Require(metadata, "\"LbmNu\"");
                Require(metadata, "nu_lbm = nu_SI * VelocityScaleMpsToLbm / dx");
                Require(metadata, "not_clamped_in_case_generation");
                Require(metadata, "\"EstimatedReynoldsNumber\"");
                Require(metadata, "\"VelocitySet\": \"D3Q19\"");
                Require(metadata, "\"LesModel\"");
                Require(metadata, "\"LbmStabilityGate\": \"requires_solver_log_and_runtime_statistics\"");
                Require(metadata, "\"SolverStabilityWarnings\": \"not_available_until_solver_log_is_archived\"");
                Require(metadata, "\"ProfileOriginZM\": -4.0");
                Require(audit, "inlet_distribution_consistency");
                Require(audit, "inlet_reynolds_stress_tensor");
                Require(audit, "R11=R22=R33=2k/3");
                Require(audit, "inlet_turbulence_length_scale");
                Require(audit, "inlet_temporal_sampling");
                Require(audit, "\"Key\": \"inlet_temporal_sampling\"");
                Require(audit, "\"Status\": \"fail\"");
                Require(audit, "expected to sample 107 inlet refreshes");
                Require(audit, "recommended minimum=200");
                Require(audit, "source='aij_length_scale_verified: smoke-test archived integral length evidence', gate=pass");
                Require(audit, "streamwise clipping fraction 0.000");
                Require(audit, "STG-lite");
                Require(audit, "LbmTau=");
                Require(audit, "VelocitySet=D3Q19");
                Require(audit, "VtkSaveStartStep=250");
                Require(audit, "ExpectedVtkFrameCount=9");
                Require(audit, "\"Key\": \"time_averaging\"");
                Require(audit, "\"Status\": \"fail\"");
                Require(audit, "PaperRecommendedAveragingFrames=40");
                Require(audit, "PaperRecommendedAdaptiveAveragingFrames=201");
                Require(audit, "ExpectedPaperAverageStepSpan=750");
                Require(audit, "ExpectedAdaptivePaperAverageStepSpan=750");
                Require(audit, "ProfileOriginZM=-4.000");
                Require(audit, "\"Key\": \"native_fluidx3d_baseline\"");
                Require(audit, "native_fluidx3d_baseline_manifest.json and native_preconditions_audit.json");
                Require(audit, "no newly-run native FluidX3D solver manifest");
                Require(audit, "Generated files only prove traceability");
                RequireNotContains(audit, "\"Key\": \"native_fluidx3d_baseline\",\r\n      \"Status\": \"pass\"");
                RequireNotContains(audit, "\"Key\": \"native_fluidx3d_baseline\",\n      \"Status\": \"pass\"");
                Require(nativeManifest, "NativeFluidX3DPathExplicitlyProvided");
                Require(nativeManifest, "NativeFluidX3DSourceValidation");
                Require(nativeManifest, "\"PaperRecommendedAveragingFrames\": 40");
                Require(nativeManifest, "\"PaperRecommendedAverageStepSpan\": 20000");
                Require(nativeManifest, "\"PaperRecommendedAdaptiveAveragingFrames\": 201");
                Require(nativeManifest, "\"VtkSaveStartStep\": 250");
                Require(nativeManifest, "\"ExpectedVtkFrameCount\": 9");
                Require(nativeManifest, "\"ExpectedAdaptivePaperAverageStepSpan\": 750");
                Require(nativeManifest, "\"LbmStabilityGate\": \"requires_solver_log_and_runtime_statistics\"");
                Require(nativeManifest, "nu_lbm = nu_SI * VelocityScaleMpsToLbm / dx");
                Require(nativeManifest, "not_clamped_in_case_generation");
                Require(nativeManifest, "\"SyntheticTurbulenceMinStreamwiseFraction\": 0.0");
                Require(nativeManifest, "disabled_no_streamwise_clipping_of_k_perturbations");
                Require(nativeManifest, "\"BaselineId\": \"citylbm-v0.4.0-stg_codegen_smoke-");
                Require(nativeManifest, "Native FluidX3D original setup");
                Require(nativeManifest, "Native FluidX3D lbm.hpp");
                Require(nativeManifest, "auto-detected paths are not sufficient evidence");
                Require(nativeManifest, "aij_length_scale_verified: smoke-test archived integral length evidence");
                Require(nativeManifest, "\"SyntheticTurbulentInletMethod\": \"STG-lite plus synthetic_eddy diagnostic inlet");
                Require(nativeManifest, "\"SyntheticTurbulentInletDistributionTreatment\": \"fluidx3d_RECONSTRUCT_INLET_STRESS_DDF");
                Require(nativeManifest, "\"InletDistributionFunctionReconstruction\": true");
                Require(nativeManifest, "\"SyntheticTurbulentInletPaperGradeStatus\": \"diagnostic_only_until_distribution_reconstruction_reynolds_stress_or_precursor_evidence_and_native_u_k_correlation_gates_pass\"");
                Require(nativeManifest, "\"PaperGradeTurbulentInletPrerequisiteGate\": \"fail\"");
                Require(nativeManifest, "measured_or_precursor_reynolds_stress_tensor");
                RequireNotContains(nativeManifest, "inlet_distribution_function_reconstruction");
                Require(nativeManifest, "empty_tunnel_U_k_correlation_preservation_gate");
                Require(metadata, "ClearanceChecks");
                Require(metadata, "DomainContainsBuildings");
                Require(metadata, "BlockageDiagnostics");
                Require(metadata, "ApproxFrontalBlockageRatio");
                Require(metadata, "blockage_diagnostic_ok_verify_against_aij");
                Require(metadata, "diagnostic_clearance_thresholds_satisfied");
                Require(metadata, "reduce zero-speed/open-box profile damping");
                Require(metadata, "diagnostic_only_missing_aij_boundary_protocol_evidence");
                Require(metadata, "not matched to official AIJ wind-tunnel boundary/fetch/roughness evidence");
                Require(metadata, "\"BoundaryConditionMethodClass\": \"citylbm_type_e_profile_maintenance_buffer_diagnostic\"");
                Require(metadata, "\"BoundaryConditionPaperGradeStatus\": \"diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass\"");
                Require(metadata, "\"BoundaryVelocityInitializationMethod\": \"fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces_plus_profile_maintenance_FORCE_FIELD_buffer\"");
                Require(metadata, "\"BoundaryProfileMaintenanceBufferApplied\": true");
                Require(metadata, "\"BoundaryProfileMaintenanceBufferLayerCells\": 8.0");
                Require(metadata, "\"BoundaryProfileMaintenanceBufferGain\": 0.0015");
                Require(metadata, "\"BoundaryProfileMaintenanceBufferMaxForceLbm\": 0.0003");
                Require(metadata, "\"BoundaryOutletTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_plus_profile_maintenance_FORCE_FIELD_buffer_not_validated_pressure_or_non_reflecting_outlet\"");
                Require(metadata, "\"BoundarySideTopTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_plus_profile_maintenance_FORCE_FIELD_buffer_not_periodic_or_wind_tunnel_equivalent\"");
                Require(metadata, "\"BoundaryRoughnessBoundaryTreatment\": \"TYPE_S_no_slip_plus_near_ground_equivalent_rough_wall_drag_FORCE_FIELD_from_RoughnessLength\"");
                Require(metadata, "\"BoundaryDevelopmentTreatment\": \"none_no_precursor_or_recycling_development_field\"");
                Require(metadata, "\"BoundaryFixedMeanVelocityOutletRisk\"");
                Require(metadata, "\"CoordinateProtocol\"");
                Require(metadata, "streamwise; positive downstream");
                Require(metadata, "streamwise velocity compared with FluidX3D u.x");
                Require(metadata, "\"Ux_over_Uref\"");
                Require(metadata, "\"SamplingMethod\": \"nearest-valid\"");
                Require(metadata, "\"PaperGradeBoundaryPrerequisiteGate\": \"fail\"");
                Require(metadata, "non_reflecting_or_validated_outlet_state");
                Require(metadata, "side_top_boundary_pair_mapping_or_wind_tunnel_equivalence");
                RequireNotContains(metadata, "rough_wall_or_wall_function_action");
                Require(metadata, "precursor_or_recycling_development_field");
                Require(metadata, "official_blockage_fetch_clearance_evidence");
                Require(audit, "BoundaryProfileMaintenanceBufferApplied=true");
                Require(audit, "\"Key\": \"wall_roughness_model\"");
                Require(audit, "near-ground equivalent rough-wall drag into FluidX3D FORCE_FIELD");
                Require(metadata, "\"BoundaryNonReflectingOutletImplemented\": false");
                Require(metadata, "\"BoundaryRoughWallFunctionImplemented\": true");
                Require(audit, "BoundaryProtocolEvidenceGate=diagnostic_only_missing_aij_boundary_protocol_evidence");
                Require(nativeManifest, "\"BoundaryConditionMethodClass\": \"citylbm_type_e_profile_maintenance_buffer_diagnostic\"");
                Require(nativeManifest, "\"BoundaryVelocityInitializationMethod\": \"fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces_plus_profile_maintenance_FORCE_FIELD_buffer\"");
                Require(nativeManifest, "\"BoundaryProfileMaintenanceBufferApplied\": true");
                Require(nativeManifest, "\"BoundaryOutletTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_plus_profile_maintenance_FORCE_FIELD_buffer_not_validated_pressure_or_non_reflecting_outlet\"");
                Require(nativeManifest, "\"PaperGradeBoundaryPrerequisiteGate\": \"fail\"");
                Require(nativeManifest, "official_blockage_fetch_clearance_evidence");

                TestFluidX3DSourceValidation();
                TestSyntheticInletRequiresCompleteKProfile();
                TestCustomTableMeasuredDiagonalRmsCodegen();
                TestCustomTableFullReynoldsStressTensorCodegen();
                TestCaseAFullReynoldsStressTensorCodegen();
                TestProbeComponentSourceGuard();
                TestSimulationSettingsAijValidationPreflightBaseline();
                TestRunSimulationValidationDefaults();

                Console.WriteLine("Codegen smoke passed.");
                Console.WriteLine(caseDir);
                return 0;
            }
            catch (TargetInvocationException ex)
            {
                Exception inner = ex.InnerException ?? ex;
                Console.Error.WriteLine(inner.GetType().FullName);
                Console.Error.WriteLine(inner.Message);
                Console.Error.WriteLine(inner.StackTrace);
                return 1;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.GetType().FullName);
                Console.Error.WriteLine(ex.Message);
                Console.Error.WriteLine(ex.StackTrace);
                return 1;
            }
            finally
            {
                if (acquiredSmokeLock)
                    smokeLock.ReleaseMutex();
                smokeLock.Dispose();
            }
        }

        [DllImport("kernel32", SetLastError = true)]
        private static extern bool SetDllDirectory(string lpPathName);

        private static void ConfigureRhinoNativeRuntime()
        {
            const string Rhino7SystemDir = @"C:\Program Files\Rhino 7\System";
            if (!Directory.Exists(Rhino7SystemDir))
                return;

            string currentPath = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
            if (currentPath.IndexOf(Rhino7SystemDir, StringComparison.OrdinalIgnoreCase) < 0)
                Environment.SetEnvironmentVariable("PATH", Rhino7SystemDir + Path.PathSeparator + currentPath);

            SetDllDirectory(Rhino7SystemDir);
        }

        private static Scene BuildScene()
        {
            var scene = new Scene("stg_codegen_smoke")
            {
                WindProfile = WindProfileType.CustomTable,
                WindProfileCsvPath = "AF_smoke.csv",
                WindDirection = new Vector3d(0, -1, 0),
                WindSpeed = 3.928296,
                ReferenceHeight = 15.9
            };
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.5, U = 2.5, HasK = true, K = 0.25 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 15.9, U = 3.928296, HasK = true, K = 0.55 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 60.0, U = 5.8, HasK = true, K = 0.80 });
            SetSceneBounds(scene, new BoundingBox(new Point3d(0, 0, 0), new Point3d(10, 10, 10)));
            return scene;
        }

        private static void SetSceneBounds(Scene scene, BoundingBox bounds)
        {
            var property = typeof(Scene).GetProperty("Bounds", BindingFlags.Instance | BindingFlags.Public);
            if (property == null)
                throw new MissingMemberException(typeof(Scene).FullName, "Bounds");
            property.SetValue(scene, bounds, null);
        }

        private static void InvokePrivate(object target, string methodName, params object[] args)
        {
            var method = target.GetType().GetMethod(methodName, BindingFlags.Instance | BindingFlags.NonPublic);
            if (method == null)
                throw new MissingMethodException(target.GetType().FullName, methodName);
            method.Invoke(target, args);
        }

        private static void Require(string text, string expected)
        {
            if (!text.Contains(expected))
                throw new InvalidOperationException("Generated case missing: " + expected);
        }

        private static void RequireNotContains(string text, string unexpected)
        {
            if (text.Contains(unexpected))
                throw new InvalidOperationException("Generated case unexpectedly contains: " + unexpected);
        }

        private static void WriteSmokeBinaryStl(string path)
        {
            using (var writer = new BinaryWriter(File.Open(path, FileMode.Create)))
            {
                writer.Write(new byte[80]);
                writer.Write((uint)1);
                writer.Write(0.0f);
                writer.Write(0.0f);
                writer.Write(1.0f);
                writer.Write(-1000.0f);
                writer.Write(-1000.0f);
                writer.Write(-1000.0f);
                writer.Write(-999.0f);
                writer.Write(-1000.0f);
                writer.Write(-1000.0f);
                writer.Write(-1000.0f);
                writer.Write(-999.0f);
                writer.Write(-1000.0f);
                writer.Write((ushort)0);
            }
        }

        private static void TestFluidX3DSourceValidation()
        {
            string root = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source_validation");

            var valid = FluidX3DInterface.ValidateFluidX3DSourcePath(root, out string validMessage);
            if (!valid.IsValid || !valid.HasMakefile || !valid.HasSetupCpp || !valid.HasLbmHpp || !valid.HasLbmCpp)
                throw new InvalidOperationException("Valid fake FluidX3D source path was rejected: " + validMessage);

            var explicitSolver = new FluidX3DInterface(root);
            if (!explicitSolver.HasExplicitFluidX3DPath)
                throw new InvalidOperationException("Explicit FluidX3D path was not recorded.");

            var autoSolver = new FluidX3DInterface("");
            if (autoSolver.HasExplicitFluidX3DPath)
                throw new InvalidOperationException("Empty FluidX3D path was incorrectly recorded as explicit.");

            string incompleteRoot = Path.Combine(Path.GetTempPath(), "CityLBM", "fake_fluidx3d_incomplete");
            Directory.CreateDirectory(Path.Combine(incompleteRoot, "src"));
            File.WriteAllText(Path.Combine(incompleteRoot, "Makefile"), "# fake build file");
            var invalid = FluidX3DInterface.ValidateFluidX3DSourcePath(incompleteRoot, out string invalidMessage);
            if (invalid.IsValid || !invalidMessage.Contains("src/setup.cpp"))
                throw new InvalidOperationException("Incomplete FluidX3D source path was not rejected.");
        }

        private static void TestSyntheticInletRequiresCompleteKProfile()
        {
            var scene = new Scene("stg_partial_k_guard")
            {
                WindProfile = WindProfileType.CustomTable,
                WindProfileCsvPath = "AF_partial_k.csv",
                WindDirection = new Vector3d(0, -1, 0),
                WindSpeed = 3.928296,
                ReferenceHeight = 15.9
            };
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.5, U = 2.5, HasK = true, K = 0.25 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 15.9, U = 3.928296, HasK = false, K = 0.0 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 60.0, U = 5.8, HasK = true, K = 0.80 });
            SetSceneBounds(scene, new BoundingBox(new Point3d(0, 0, 0), new Point3d(10, 10, 10)));

            var grid = new CartesianGrid
            {
                Nx = 16,
                Ny = 16,
                Nz = 16,
                Dx = 2.0,
                Origin = new Point3d(-60, -120, 0),
                DomainBounds = new BoundingBox(new Point3d(-60, -120, 0), new Point3d(70, 60, 70))
            };
            var settings = new SimulationSettings
            {
                TimeSteps = 1000,
                SaveInterval = 100,
                EnableSyntheticTurbulentInlet = true,
                SyntheticTurbulenceLengthScaleSource = "aij_length_scale_verified: smoke-test archived integral length evidence"
            };

            string fakeFluidX3DRoot = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source_partial_k_guard");
            var solver = new FluidX3DInterface(fakeFluidX3DRoot);
            string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "stg_partial_k_guard");
            Directory.CreateDirectory(caseDir);
            Directory.CreateDirectory(Path.Combine(caseDir, "output"));
            string setupPath = Path.Combine(caseDir, "setup.cpp");

            InvokePrivate(
                solver,
                "GenerateSetupCpp",
                scene,
                grid,
                settings,
                setupPath,
                "buildings.stl",
                "output");
            InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);

            string setup = File.ReadAllText(setupPath);
            string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
            string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));

            Require(setup, "profile_k_lbm[profile_count]");
            RequireNotContains(setup, "float3 syntheticTurbulentInlet(");
            RequireNotContains(setup, "void applySyntheticTurbulentInlet(");
            Require(metadata, "\"CustomProfileKComplete\": false");
            Require(metadata, "\"KColumnStatus\": \"invalid_partial_k_column\"");
            Require(metadata, "\"SyntheticTurbulentInletRequested\": true");
            Require(metadata, "\"SyntheticTurbulentInletInjected\": false");
            Require(metadata, "\"SyntheticTurbulentInletBlockedReason\": \"custom_profile_k_column_incomplete\"");
            Require(metadata, "requires k to be present on every CustomTable profile row before injection");
            Require(audit, "No synthetic turbulent inlet length scale is active.");
            Require(audit, "AF k is available, but no turbulent fluctuation is injected into the inlet.");
        }

        private static void TestCustomTableMeasuredDiagonalRmsCodegen()
        {
            var scene = new Scene("stg_measured_diagonal_rms")
            {
                WindProfile = WindProfileType.CustomTable,
                WindProfileCsvPath = "AF_rms_smoke.csv",
                WindDirection = new Vector3d(0, -1, 0),
                WindSpeed = 3.928296,
                ReferenceHeight = 15.9
            };
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.5, U = 2.5, HasK = true, K = 0.25, HasRms = true, URms = 0.30, VRms = 0.20, WRms = 0.10 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 15.9, U = 3.928296, HasK = true, K = 0.55, HasRms = true, URms = 0.50, VRms = 0.35, WRms = 0.25 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 60.0, U = 5.8, HasK = true, K = 0.80, HasRms = true, URms = 0.70, VRms = 0.45, WRms = 0.30 });
            SetSceneBounds(scene, new BoundingBox(new Point3d(0, 0, 0), new Point3d(10, 10, 10)));

            var grid = new CartesianGrid
            {
                Nx = 16,
                Ny = 16,
                Nz = 16,
                Dx = 2.0,
                Origin = new Point3d(-60, -120, -4),
                DomainBounds = new BoundingBox(new Point3d(-60, -120, -4), new Point3d(70, 60, 70))
            };
            var settings = new SimulationSettings
            {
                TimeSteps = 1000,
                SaveInterval = 100,
                EnableSyntheticTurbulentInlet = true,
                SyntheticTurbulenceLengthScaleSource = "aij_length_scale_verified: smoke-test archived integral length evidence"
            };

            string fakeFluidX3DRoot = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source_measured_diagonal_rms");
            var solver = new FluidX3DInterface(fakeFluidX3DRoot);
            string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "stg_measured_diagonal_rms");
            Directory.CreateDirectory(caseDir);
            Directory.CreateDirectory(Path.Combine(caseDir, "output"));
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            string definesPath = Path.Combine(caseDir, "defines.hpp");
            string stlPath = Path.Combine(caseDir, "buildings.stl");

            InvokePrivate(
                solver,
                "GenerateSetupCpp",
                scene,
                grid,
                settings,
                setupPath,
                "buildings.stl",
                "output");
            InvokePrivate(solver, "GenerateDefinesHpp", scene, grid, settings, definesPath, true);
            WriteSmokeBinaryStl(stlPath);
            InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
            InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

            string setup = File.ReadAllText(setupPath);
            string defines = File.ReadAllText(definesPath);
            string domainOrigin = File.ReadAllText(Path.Combine(caseDir, "domain_origin.json"));
            string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
            string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));
            string nativeManifest = File.ReadAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.json"));

            Require(setup, "profile_has_measured_diagonal_rms = true");
            Require(setup, "profile_u_rms_lbm[profile_count]");
            Require(setup, "profile_v_rms_lbm[profile_count]");
            Require(setup, "profile_w_rms_lbm[profile_count]");
            Require(setup, "R11=u_rms^2, R22=v_rms^2, R33=w_rms^2");
            Require(setup, "citylbm_stg_target_sigma_xyz");
            Require(setup, "sigma.x * fluct_x");
            Require(setup, "target_sigma.x / rms_x");
            Require(metadata, "\"CustomProfileHasMeasuredDiagonalRms\": true");
            Require(metadata, "\"MeasuredDiagonalRmsColumnStatus\": \"read_from_csv_and_used_for_STG_component_targets\"");
            Require(metadata, "measured_diagonal_rms_from_af_R11_u_rms2_R22_v_rms2_R33_w_rms2");
            Require(metadata, "\"InletReynoldsStressTensorSource\": \"measured_diagonal_rms_from_AF_columns\"");
            Require(metadata, "\"R11\": \"u_rms^2\"");
            Require(metadata, "\"R22\": \"v_rms^2\"");
            Require(metadata, "\"R33\": \"w_rms^2\"");
            Require(metadata, "offdiagonal_covariances_missing");
            Require(audit, "STG-lite uses measured diagonal RMS");
            Require(audit, "R11=u_rms^2");
            Require(audit, "off-diagonal");
        }

        private static void TestCustomTableFullReynoldsStressTensorCodegen()
        {
            var scene = new Scene("AIJ_CaseE_stg_full_reynolds_stress_tensor")
            {
                WindProfile = WindProfileType.CustomTable,
                WindProfileCsvPath = "AF_full_tensor_smoke.csv",
                WindDirection = new Vector3d(0, -1, 0),
                WindSpeed = 3.928296,
                ReferenceHeight = 15.9
            };
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.5, U = 2.5, HasK = true, K = 0.25, HasReynoldsStressTensor = true, R11 = 0.090, R22 = 0.040, R33 = 0.020, R12 = -0.010, R13 = 0.002, R23 = -0.001 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 15.9, U = 3.928296, HasK = true, K = 0.55, HasReynoldsStressTensor = true, R11 = 0.250, R22 = 0.120, R33 = 0.070, R12 = -0.030, R13 = 0.004, R23 = -0.003 });
            scene.CustomWindProfile.Add(new WindProfileSample { Z = 60.0, U = 5.8, HasK = true, K = 0.80, HasReynoldsStressTensor = true, R11 = 0.490, R22 = 0.200, R33 = 0.110, R12 = -0.050, R13 = 0.006, R23 = -0.004 });
            SetSceneBounds(scene, new BoundingBox(new Point3d(0, 0, 0), new Point3d(10, 10, 10)));

            var grid = new CartesianGrid
            {
                Nx = 16,
                Ny = 16,
                Nz = 16,
                Dx = 2.0,
                Origin = new Point3d(-60, -120, -4),
                DomainBounds = new BoundingBox(new Point3d(-60, -120, -4), new Point3d(70, 60, 70))
            };
            var settings = new SimulationSettings
            {
                TimeSteps = 1000,
                SaveInterval = 100,
                EnableSyntheticTurbulentInlet = true,
                SyntheticTurbulenceLengthScaleSource = "aij_length_scale_verified: smoke-test archived integral length evidence"
            };

            string fakeFluidX3DRoot = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source_full_reynolds_tensor");
            var solver = new FluidX3DInterface(fakeFluidX3DRoot);
            string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "stg_full_reynolds_stress_tensor");
            Directory.CreateDirectory(caseDir);
            Directory.CreateDirectory(Path.Combine(caseDir, "output"));
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            string definesPath = Path.Combine(caseDir, "defines.hpp");
            string stlPath = Path.Combine(caseDir, "buildings.stl");

            InvokePrivate(
                solver,
                "GenerateSetupCpp",
                scene,
                grid,
                settings,
                setupPath,
                "buildings.stl",
                "output");
            InvokePrivate(solver, "GenerateDefinesHpp", scene, grid, settings, definesPath, true);
            WriteSmokeBinaryStl(stlPath);
            InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
            InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

            string setup = File.ReadAllText(setupPath);
            string defines = File.ReadAllText(definesPath);
            string domainOrigin = File.ReadAllText(Path.Combine(caseDir, "domain_origin.json"));
            string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
            string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));
            string nativeManifest = File.ReadAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.json"));

            Require(setup, "profile_has_full_reynolds_stress_tensor = true");
            Require(setup, "Reynolds-stress arrays use measured/precursor full tensor columns");
            Require(setup, "profile_r12_lbm[profile_count]");
            Require(setup, "profile_r13_lbm[profile_count]");
            Require(setup, "profile_r23_lbm[profile_count]");
            Require(setup, "CityLBMReynoldsCholesky");
            Require(setup, "citylbm_stg_target_reynolds_cholesky");
            Require(setup, "perturbation = float3(l.l11 * fluct_x");
            Require(setup, "covariance whitening/re-coloring");
            Require(setup, "citylbm_stg_layer_tensor_whitening_valid");
            Require(defines, "#define RECONSTRUCT_INLET_STRESS_DDF");
            Require(metadata, "\"AijCase\": \"CaseE\"");
            Require(metadata, "\"CaseName\": \"CaseE\"");
            Require(metadata, "\"CustomProfileHasFullReynoldsStressTensor\": true");
            Require(metadata, "\"CustomProfileReynoldsStressTensorComplete\": true");
            Require(metadata, "measured_or_precursor_full_tensor_from_csv_R11_R22_R33_R12_R13_R23");
            Require(metadata, "\"HasFullReynoldsStressTensor\": true");
            Require(metadata, "\"R12M2s2\": -0.01");
            Require(metadata, "\"R23M2s2\": -0.001");
            Require(metadata, "\"InletReynoldsStressTensorAvailable\": true");
            Require(metadata, "\"InletReynoldsStressTensorSource\": \"full_reynolds_stress_tensor_from_CustomTable_CSV\"");
            Require(metadata, "\"R11\": \"R11_csv\"");
            Require(metadata, "\"R12\": \"R12_csv\"");
            Require(metadata, "\"SyntheticTurbulentInletFullTensorCovariancePreservingCorrection\": true");
            Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingCorrection\": true");
            Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingScope\": \"per_z_cell_inlet_layer\"");
            Require(metadata, "covariance whitening/re-coloring");
            Require(metadata, "paper-grade use still requires native R_ij preservation evidence");
            RequireNotContains(metadata, "measured_or_precursor_reynolds_stress_tensor");
            Require(domainOrigin, "\"DomainOriginX\": -60.0");
            Require(nativeManifest, "Domain origin");
            Require(nativeManifest, "buildings.stl");
            Require(audit, "per-layer covariance whitening/re-coloring");
            Require(audit, "U/k/Rij/correlation preservation");
            Require(audit, "\"Status\": \"partial\"");
        }

        private static void TestCaseAFullReynoldsStressTensorCodegen()
        {
            var scene = new Scene("casea_full_reynolds_stress_tensor")
            {
                WindProfile = WindProfileType.CustomTable,
                WindProfileCsvPath = "AF_caseA.csv",
                WindDirection = new Vector3d(1, 0, 0),
                WindSpeed = 4.491,
                ReferenceHeight = 0.16
            };
            string officialAfCsv = Environment.GetEnvironmentVariable("CITYLBM_CODEGEN_CASEA_AF_CSV") ?? "";
            if (!string.IsNullOrWhiteSpace(officialAfCsv) && File.Exists(officialAfCsv))
            {
                scene.WindProfileCsvPath = Path.GetFullPath(officialAfCsv);
                foreach (var sample in LoadOfficialAfProfile(officialAfCsv))
                    scene.CustomWindProfile.Add(sample);
            }
            else
            {
                scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.01, U = 2.7, HasK = true, K = 0.20, HasReynoldsStressTensor = true, R11 = 0.060, R22 = 0.030, R33 = 0.020, R12 = -0.006, R13 = 0.001, R23 = -0.001 });
                scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.16, U = 4.491, HasK = true, K = 0.42, HasReynoldsStressTensor = true, R11 = 0.180, R22 = 0.090, R33 = 0.050, R12 = -0.018, R13 = 0.002, R23 = -0.002 });
                scene.CustomWindProfile.Add(new WindProfileSample { Z = 0.28, U = 5.3, HasK = true, K = 0.55, HasReynoldsStressTensor = true, R11 = 0.260, R22 = 0.120, R33 = 0.070, R12 = -0.026, R13 = 0.003, R23 = -0.003 });
            }

            var grid = new CartesianGrid
            {
                Nx = 547,
                Ny = 280,
                Nz = 160,
                Dx = 0.006,
                Origin = new Point3d(-0.84, -0.84, 0.0),
                DomainBounds = new BoundingBox(new Point3d(-0.84, -0.84, 0.0), new Point3d(2.44, 0.84, 0.96))
            };
            var settings = new SimulationSettings
            {
                TimeSteps = ReadIntEnv("CITYLBM_CODEGEN_CASEA_TIME_STEPS", 1000),
                SaveInterval = ReadIntEnv("CITYLBM_CODEGEN_CASEA_SAVE_INTERVAL", 100),
                EnableSyntheticTurbulentInlet = true,
                SyntheticTurbulenceLengthScaleSource = "aij_length_scale_verified: case-a smoke-test archived integral length evidence"
            };

            string fakeFluidX3DRoot = CreateFakeFluidX3DSourceTree("fake_fluidx3d_source_casea_full_reynolds_tensor");
            var solver = new FluidX3DInterface(fakeFluidX3DRoot);
            string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "casea_full_reynolds_stress_tensor");
            Directory.CreateDirectory(caseDir);
            Directory.CreateDirectory(Path.Combine(caseDir, "output"));
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            string definesPath = Path.Combine(caseDir, "defines.hpp");
            string stlPath = Path.Combine(caseDir, "buildings.stl");

            InvokePrivate(
                solver,
                "GenerateSetupCpp",
                scene,
                grid,
                settings,
                setupPath,
                "buildings.stl",
                "output");
            InvokePrivate(solver, "GenerateDefinesHpp", scene, grid, settings, definesPath, true);
            WriteCaseAStandardBlockBinaryStl(stlPath);
            InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
            InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
            PatchCaseAStandardBlockMetadata(Path.Combine(caseDir, "case_metadata.json"));
            InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
            InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

            string setup = File.ReadAllText(setupPath);
            string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));

            Require(setup, "const float dir_x = 1.000000f;");
            Require(setup, "const float dir_y = 0.000000f;");
            Require(setup, "const float dir_z = 0.000000f;");
            Require(metadata, "\"ReferenceHeightM\": 0.16");
            Require(metadata, "\"ReferenceWindSpeedMps\": 4.491");
            Require(metadata, "\"GeometryBuildingCount\": 1");
            Require(metadata, "\"GeometryBuildingHeightM\": 0.16");
            if (string.IsNullOrWhiteSpace(officialAfCsv) || !File.Exists(officialAfCsv))
            {
                Require(setup, "profile_has_full_reynolds_stress_tensor = true");
                Require(metadata, "\"CustomProfileHasFullReynoldsStressTensor\": true");
            }
            else
            {
                Require(setup, "profile_has_measured_diagonal_rms = true");
                Require(setup, "profile_has_full_reynolds_stress_tensor = false");
                Require(metadata, "\"CustomProfileRows\": 24");
                Require(metadata, "\"CustomProfileHasMeasuredDiagonalRms\": true");
                Require(metadata, "\"CustomProfileHasFullReynoldsStressTensor\": false");
                Require(metadata, "\"KMaxM2s2\": 0.661");
            }
        }

        private static List<WindProfileSample> LoadOfficialAfProfile(string csvPath)
        {
            var lines = File.ReadAllLines(csvPath);
            if (lines.Length < 2)
                throw new InvalidOperationException("Official AF CSV has no data rows: " + csvPath);

            string[] header = SplitCsvLine(lines[0]);
            int zIndex = FindHeaderIndex(header, h => IsHeader(h, "z", "zm", "height", "heightm"));
            int uIndex = FindHeaderIndex(header, h => IsHeader(h, "u", "ums", "umps", "umean", "meanu"));
            int kIndex = FindHeaderIndex(header, h => IsHeader(h, "k", "km2s2", "tke"));
            int uRmsIndex = FindHeaderIndex(header, h => IsHeader(h, "urms", "urmsms", "rmsu"));
            int vRmsIndex = FindHeaderIndex(header, h => IsHeader(h, "vrms", "vrmsms", "rmsv"));
            int wRmsIndex = FindHeaderIndex(header, h => IsHeader(h, "wrms", "wrmsms", "rmsw"));
            if (zIndex < 0 || uIndex < 0 || kIndex < 0)
                throw new InvalidOperationException("Official AF CSV must include z, U and k columns: " + csvPath);

            bool hasRms = uRmsIndex >= 0 && vRmsIndex >= 0 && wRmsIndex >= 0;
            var samples = new List<WindProfileSample>();
            for (int i = 1; i < lines.Length; i++)
            {
                string line = lines[i].Trim();
                if (line.Length == 0 || line.StartsWith("#"))
                    continue;
                string[] parts = SplitCsvLine(line);
                double z = ParseRequired(parts, zIndex, "z", i + 1);
                double u = ParseRequired(parts, uIndex, "U", i + 1);
                double k = ParseRequired(parts, kIndex, "k", i + 1);
                var sample = new WindProfileSample
                {
                    Z = z,
                    U = u,
                    HasK = true,
                    K = k,
                };
                if (hasRms)
                {
                    sample.HasRms = true;
                    sample.URms = ParseRequired(parts, uRmsIndex, "u_rms", i + 1);
                    sample.VRms = ParseRequired(parts, vRmsIndex, "v_rms", i + 1);
                    sample.WRms = ParseRequired(parts, wRmsIndex, "w_rms", i + 1);
                }
                samples.Add(sample);
            }
            if (samples.Count < 5)
                throw new InvalidOperationException("Official AF CSV produced too few valid rows: " + samples.Count);
            return samples.OrderBy(sample => sample.Z).ToList();
        }

        private static int ReadIntEnv(string name, int defaultValue)
        {
            string value = Environment.GetEnvironmentVariable(name) ?? "";
            if (string.IsNullOrWhiteSpace(value))
                return defaultValue;
            if (!int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out int parsed) || parsed <= 0)
                throw new InvalidOperationException($"Environment variable {name} must be a positive integer.");
            return parsed;
        }

        private static string[] SplitCsvLine(string line)
        {
            return line.Split(new[] { ',', ';', '\t' }, StringSplitOptions.None)
                .Select(part => part.Trim())
                .ToArray();
        }

        private static int FindHeaderIndex(string[] headers, Func<string, bool> predicate)
        {
            for (int i = 0; i < headers.Length; i++)
            {
                if (predicate(NormalizeHeader(headers[i])))
                    return i;
            }
            return -1;
        }

        private static bool IsHeader(string header, params string[] accepted)
        {
            return accepted.Any(value => string.Equals(header, value, StringComparison.OrdinalIgnoreCase));
        }

        private static string NormalizeHeader(string header)
        {
            var chars = header
                .Trim()
                .ToLowerInvariant()
                .Where(char.IsLetterOrDigit)
                .ToArray();
            return new string(chars);
        }

        private static double ParseRequired(string[] parts, int index, string label, int lineNumber)
        {
            if (index < 0 || index >= parts.Length ||
                !double.TryParse(parts[index], NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
                throw new InvalidOperationException($"Cannot parse {label} at AF CSV line {lineNumber}.");
            return value;
        }

        private static void PatchCaseAStandardBlockMetadata(string metadataPath)
        {
            var metadata = JObject.Parse(File.ReadAllText(metadataPath));
            metadata["GeometryScaleEvidenceGate"] = "casea_standard_block_stl_verified_model_scale";
            metadata["GeometryBuildingCount"] = 1;
            metadata["GeometryBuildingHeightM"] = 0.16;
            metadata["GeometryPhysicalUnitAssumption"] = "AIJ_CaseA_standard_block_model_scale_meters_B0.08_D0.08_H0.16";
            File.WriteAllText(metadataPath, metadata.ToString());
        }

        private static void WriteCaseAStandardBlockBinaryStl(string path)
        {
            var vertices = new[]
            {
                Tuple.Create(-0.04f, -0.04f, 0.00f),
                Tuple.Create(0.04f, -0.04f, 0.00f),
                Tuple.Create(0.04f, 0.04f, 0.00f),
                Tuple.Create(-0.04f, 0.04f, 0.00f),
                Tuple.Create(-0.04f, -0.04f, 0.16f),
                Tuple.Create(0.04f, -0.04f, 0.16f),
                Tuple.Create(0.04f, 0.04f, 0.16f),
                Tuple.Create(-0.04f, 0.04f, 0.16f),
            };
            var faces = new[]
            {
                Tuple.Create(0, 3, 2), Tuple.Create(0, 2, 1),
                Tuple.Create(4, 5, 6), Tuple.Create(4, 6, 7),
                Tuple.Create(0, 1, 5), Tuple.Create(0, 5, 4),
                Tuple.Create(1, 2, 6), Tuple.Create(1, 6, 5),
                Tuple.Create(2, 3, 7), Tuple.Create(2, 7, 6),
                Tuple.Create(3, 0, 4), Tuple.Create(3, 4, 7),
            };

            using (var writer = new BinaryWriter(File.Open(path, FileMode.Create)))
            {
                byte[] header = new byte[80];
                var text = System.Text.Encoding.ASCII.GetBytes("AIJ Case A 1:1:2 box");
                Array.Copy(text, header, text.Length);
                writer.Write(header);
                writer.Write((uint)faces.Length);
                foreach (var face in faces)
                {
                    writer.Write(0.0f);
                    writer.Write(0.0f);
                    writer.Write(0.0f);
                    foreach (var vertexIndex in new[] { face.Item1, face.Item2, face.Item3 })
                    {
                        var vertex = vertices[vertexIndex];
                        writer.Write(vertex.Item1);
                        writer.Write(vertex.Item2);
                        writer.Write(vertex.Item3);
                    }
                    writer.Write((ushort)0);
                }
            }
        }

        private static string CreateFakeFluidX3DSourceTree(string name)
        {
            string root = Path.Combine(Path.GetTempPath(), "CityLBM", name);
            string src = Path.Combine(root, "src");
            Directory.CreateDirectory(src);

            File.WriteAllText(Path.Combine(root, "Makefile"), "# fake build file");
            File.WriteAllText(Path.Combine(src, "setup.cpp"), "// setup");
            File.WriteAllText(
                Path.Combine(src, "defines.hpp"),
                "#define TYPE_E 2u\n#define EQUILIBRIUM_BOUNDARIES\n#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n#define RECONSTRUCT_INLET_STRESS_DDF\n");
            File.WriteAllText(
                Path.Combine(src, "kernel.cpp"),
                @"kernel void reconstruct_equilibrium_boundaries(global fpxx* fi, const global float* rho, const global float* u, const global uchar* flags, const ulong t) {
    const uxx n = get_global_id(0);
    if((flags[n]&TYPE_BO)!=TYPE_E) return;
    uxx j[def_velocity_set];
    float feq[def_velocity_set];
    calculate_f_eq(rho[n], u[n], u[def_N+(ulong)n], u[2ul*def_N+(ulong)n], feq);
    store_f(n, feq, fi, j, t);
}
kernel void reconstruct_inlet_stress_boundaries(global fpxx* fi) {}
kernel void stream_collide(global fpxx* fi, global float* rho, global float* u, global uchar* flags) {
    const uchar flagsn_bo = flags[n]&TYPE_BO;
    float rhon, uxn, uyn, uzn;
    if(flagsn_bo==TYPE_E) {
        rhon = rho[n];
        uxn = u[n];
        uyn = u[def_N+(ulong)n];
        uzn = u[2ul*def_N+(ulong)n];
    }
    float feq[def_velocity_set];
    for(uint i=0u; i<def_velocity_set; i++) fhn[i] = flagsn_bo==TYPE_E ? feq[i] : fhn[i];
}
// CASEA_DEVICE_SEM_STRESS_DDF
");
            File.WriteAllText(
                Path.Combine(src, "lbm.hpp"),
                "#ifdef RECONSTRUCT_INLET_STRESS_DDF\nvoid reconstruct_inlet_stress_boundaries();\n#endif\n#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\nvoid reconstruct_equilibrium_boundaries();\n#endif\n");
            File.WriteAllText(
                Path.Combine(src, "lbm.cpp"),
                "auto k = Kernel(device, N, \"reconstruct_equilibrium_boundaries\", fi, rho, u, flags, t);\n#ifdef RECONSTRUCT_INLET_STRESS_DDF\nvoid LBM::reconstruct_inlet_stress_boundaries() {}\n#endif\n#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\nvoid LBM::reconstruct_equilibrium_boundaries() {}\n#endif\n");
            return root;
        }

        private static void TestProbeComponentSourceGuard()
        {
            string repoRoot = FindRepositoryRoot();
            string probePath = Path.Combine(repoRoot, "src", "Components", "Results", "ProbeComponent.cs");
            string[] lines = File.ReadAllLines(probePath);
            bool hasExecutableGuard = false;
            foreach (string line in lines)
            {
                string trimmed = line.TrimStart();
                if (trimmed.StartsWith("//", StringComparison.Ordinal) &&
                    trimmed.Contains("if (fieldPoints.Count != fieldVelocities.Count)"))
                {
                    throw new InvalidOperationException("Probe count guard is commented out in ProbeComponent.cs.");
                }

                if (trimmed.StartsWith("if (fieldPoints.Count != fieldVelocities.Count)", StringComparison.Ordinal))
                {
                    hasExecutableGuard = true;
                }
            }

            if (!hasExecutableGuard)
                throw new InvalidOperationException("ProbeComponent.cs is missing executable Points/Velocity count validation.");
        }

        private static void TestRunSimulationValidationDefaults()
        {
            string repoRoot = FindRepositoryRoot();
            string componentPath = Path.Combine(repoRoot, "src", "Components", "Simulation", "RunSimulationComponent.cs");
            string source = File.ReadAllText(componentPath);

            Require(source, "validation preflight default is 40000");
            Require(source, "validation preflight default is 1000");
            Require(source, "AIJ Validation Preset");
            Require(source, "CreateAijValidationPreflightBaseline");
            Require(source, "TimeSteps >= 40000");
            Require(source, "SaveInterval <= 1000");
            Require(source, "Missing length-scale/boundary/native evidence will still block formal runs");
            Require(source, "GH_ParamAccess.item, 40000");
            Require(source, "GH_ParamAccess.item, 1000");
            Require(source, "int timeSteps = 40000;");
            Require(source, "int saveInterval = 1000;");
            Require(source, "settings.TimeSteps = Math.Max(settings.TimeSteps, timeSteps);");
            Require(source, "settings.SaveInterval = saveInterval > 0");
            Require(source, "settings.SyntheticTurbulenceModeCount = Math.Max(");
            Require(source, "CustomTable k column is complete, but Synthetic Inlet is off");
            Require(source, "k will be recorded and converted only; it will not create inlet turbulence in FluidX3D");
            Require(source, "STG-lite uses velocity-field inlet perturbations only");
            Require(source, "MinimumValidationStgRefreshes");
            Require(source, "ExpectedFinalWindowStgRefreshCount");
            Require(source, "validation requires at least {MinimumValidationStgRefreshes} inlet refreshes");
            Require(source, "Synthetic Inlet is active but the final averaging window has only");
            Require(source, "HasCompleteCustomProfileK");
            RequireNotContains(source, "Validation default is 10000");
            RequireNotContains(source, "Validation default is 500");
            RequireNotContains(source, "int timeSteps = 10000;");
            RequireNotContains(source, "int saveInterval = 500;");
        }

        private static void TestSimulationSettingsAijValidationPreflightBaseline()
        {
            var settings = SimulationSettings.CreateAijValidationPreflightBaseline();
            if (settings.TimeSteps != 40000)
                throw new InvalidOperationException("AIJ baseline TimeSteps should be 40000.");
            if (settings.SaveInterval != 1000)
                throw new InvalidOperationException("AIJ baseline SaveInterval should be 1000.");
            if (!settings.EnableSyntheticTurbulentInlet)
                throw new InvalidOperationException("AIJ baseline should enable STG-lite for CustomTable+k preflight.");
            if (settings.SyntheticTurbulenceModeCount != 128)
                throw new InvalidOperationException("AIJ baseline STG mode count should be 128.");
            if (settings.SyntheticTurbulenceUpdateInterval != 25)
                throw new InvalidOperationException("AIJ baseline STG update interval should be 25.");
            if (settings.SyntheticTurbulenceLengthScaleSource != "")
                throw new InvalidOperationException("AIJ baseline must not fabricate a length-scale evidence tag.");
        }

        private static string FindRepositoryRoot()
        {
            string current = Directory.GetCurrentDirectory();
            while (!string.IsNullOrEmpty(current))
            {
                if (File.Exists(Path.Combine(current, "CityLBM.csproj")) &&
                    Directory.Exists(Path.Combine(current, "src")))
                {
                    return current;
                }

                current = Directory.GetParent(current)?.FullName;
            }

            throw new DirectoryNotFoundException("Could not locate CityLBM repository root.");
        }
    }
}
