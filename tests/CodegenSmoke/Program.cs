using System;
using System.IO;
using System.Reflection;
using CityLBM.Core;
using CityLBM.Solver;
using Rhino.Geometry;

namespace CityLBM.CodegenSmoke
{
    internal static class Program
    {
        private static int Main()
        {
            try
            {
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
                File.WriteAllText(stlPath, "solid smoke\nendsolid smoke\n");
                InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
                InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

                string setup = File.ReadAllText(setupPath);
                string defines = File.ReadAllText(definesPath);
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
                Require(setup, "target_sigma / rms_x");
                Require(setup, "u_in.x = mean.x + (u_in.x - mean.x - citylbm_stg_layer_mean_correction_x[z]) * citylbm_stg_layer_rms_scale_x[z];");
                RequireNotContains(setup, "sqrtf(6.0f / (float)citylbm_stg_mode_count)");
                Require(setup, "citylbm_mode_amplitude");
                Require(setup, "ak*kx");
                Require(setup, "Taylor frozen-turbulence advection");
                Require(setup, "float advected_x = (float)x - dir_x * mean_mag * (float)t_step;");
                Require(setup, "float phase = kx * advected_x + ky * advected_y + kz * advected_z;");
                Require(setup, "Target component RMS follows isotropic k");
                Require(setup, "nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx");
                Require(setup, "no longer clamps tau to 0.55");
                Require(setup, "LBM lbm(SX, SY, SZ, 1.29310345E-007f)");
                Require(defines, "velocity_scale_mps_to_lbm");
                Require(defines, "nu_lbm = nu_physical * velocity_scale_mps_to_lbm / dx");
                Require(defines, "#define TAU 5.00000388E-001f");
                Require(setup, "citylbm_stg_update_interval = 7u");
                Require(setup, "citylbm_stg_max_fraction = 0.420000f");
                Require(setup, "citylbm_stg_min_streamwise_fraction = 0.000000f");
                Require(setup, "Default is no streamwise clipping");
                Require(setup, "if(citylbm_stg_min_streamwise_fraction > 0.0f)");
                RequireNotContains(setup, "0.05f * (mean_mag");
                Require(setup, "syntheticTurbulentInlet");
                Require(setup, "applySyntheticTurbulentInlet");
                Require(setup, "synthetic_eddy_count");
                Require(setup, "updateSyntheticEddyPlane");
                Require(setup, "updateTemporalFilter");
                Require(setup, "turbulentWind");
                Require(setup, "applyInlet");
                Require(setup, "compactCosine");
                Require(setup, "periodicDistance");
                Require(setup, "GRAPHICS mode uses the same STG refresh loop as batch mode");
                Require(setup, "steps_to_run = remaining < citylbm_stg_update_interval ? remaining : citylbm_stg_update_interval");
                Require(setup, "if(lbm.flags[n] == TYPE_E &&");
                Require(setup, "lbm.flags.read_from_device();");
                Require(setup, "lbm.flags.write_to_device();");
                Require(setup, "initialize all TYPE_E boundary velocities");
                Require(setup, "fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces");
                Require(setup, "Outlet/lateral/top TYPE_E faces receive the mean profile velocity");
                Require(setup, "if(lbm.flags[n] != TYPE_E) return;");
                Require(setup, "float3 u_e = windProfile(z);");
                Require(metadata, "divergence-reduced spectral modes");
                Require(metadata, "Taylor frozen-turbulence phase advection");
                Require(metadata, "projected normal to synthetic wave vectors");
                Require(metadata, "component RMS target sigma=sqrt(2k/3)");
                Require(metadata, "per_z_cell inlet-face RMS rescaling");
                Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingCorrection\": true");
                Require(metadata, "\"SyntheticTurbulentInletLayerwiseRmsPreservingScope\": \"per_z_cell_inlet_layer\"");
                Require(metadata, "actual inlet-face RMS matches the k-derived target sigma=sqrt(2k/3)");
                Require(metadata, "\"SyntheticTurbulenceUpdateInterval\": 7");
                Require(metadata, "\"SyntheticTurbulenceMinimumRecommendedRefreshes\": 200");
                Require(metadata, "\"SyntheticTurbulenceExpectedFinalWindowRefreshCount\": 128");
                Require(metadata, "\"SyntheticTurbulentInletTemporalSamplingGate\": \"diagnostic_only_insufficient_stg_refreshes_in_average_window\"");
                Require(metadata, "\"SyntheticTurbulenceMaxFractionOfMean\": 0.42");
                Require(metadata, "\"SyntheticTurbulenceMinStreamwiseFraction\": 0.0");
                Require(metadata, "\"SyntheticTurbulenceStreamwiseClippingTreatment\": \"disabled_no_streamwise_clipping_of_k_perturbations\"");
                Require(metadata, "\"SyntheticTurbulenceCorrelationLengthM\": 8.0");
                Require(metadata, "aij_length_scale_verified: smoke-test archived integral length evidence");
                Require(metadata, "\"SyntheticTurbulentInletLengthScaleGate\": \"pass\"");
                Require(metadata, "refreshed on TYPE_E inlet nodes in batch and graphics modes");
                Require(metadata, "\"InletDistributionFunctionReconstruction\": false");
                Require(metadata, "\"SyntheticTurbulentInletPaperGradeStatus\": \"diagnostic_only_until_distribution_reconstruction_reynolds_stress_or_precursor_evidence_and_native_u_k_correlation_gates_pass\"");
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
                Require(metadata, "\"ExpectedVtkFrameCount\": 10");
                Require(metadata, "\"TimeAveragingRunGate\": \"smoke_only_too_few_frames_for_validation\"");
                Require(metadata, "\"PaperRecommendedAveragingFrames\": 40");
                Require(metadata, "\"PaperRecommendedAverageStepSpan\": 20000");
                Require(metadata, "\"ExpectedPaperAverageStepSpan\": 900");
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
                Require(audit, "expected to sample 128 inlet refreshes");
                Require(audit, "recommended minimum=200");
                Require(audit, "source='aij_length_scale_verified: smoke-test archived integral length evidence', gate=pass");
                Require(audit, "streamwise clipping fraction 0.000");
                Require(audit, "STG-lite");
                Require(audit, "LbmTau=");
                Require(audit, "VelocitySet=D3Q19");
                Require(audit, "ExpectedVtkFrameCount=10");
                Require(audit, "\"Key\": \"time_averaging\"");
                Require(audit, "\"Status\": \"fail\"");
                Require(audit, "PaperRecommendedAveragingFrames=40");
                Require(audit, "ExpectedPaperAverageStepSpan=900");
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
                Require(nativeManifest, "\"LbmStabilityGate\": \"requires_solver_log_and_runtime_statistics\"");
                Require(nativeManifest, "nu_lbm = nu_SI * VelocityScaleMpsToLbm / dx");
                Require(nativeManifest, "not_clamped_in_case_generation");
                Require(nativeManifest, "\"SyntheticTurbulenceMinStreamwiseFraction\": 0.0");
                Require(nativeManifest, "disabled_no_streamwise_clipping_of_k_perturbations");
                Require(nativeManifest, "\"BaselineId\": \"citylbm-v0.3.0-stg_codegen_smoke-");
                Require(nativeManifest, "Native FluidX3D original setup");
                Require(nativeManifest, "Native FluidX3D lbm.hpp");
                Require(nativeManifest, "auto-detected paths are not sufficient evidence");
                Require(nativeManifest, "aij_length_scale_verified: smoke-test archived integral length evidence");
                Require(nativeManifest, "\"SyntheticTurbulentInletMethod\": \"STG-lite plus synthetic_eddy velocity-field-only diagnostic inlet");
                Require(nativeManifest, "\"SyntheticTurbulentInletDistributionTreatment\": \"velocity_field_only_no_distribution_function_reconstruction\"");
                Require(nativeManifest, "\"InletDistributionFunctionReconstruction\": false");
                Require(nativeManifest, "\"SyntheticTurbulentInletPaperGradeStatus\": \"diagnostic_only_until_distribution_reconstruction_reynolds_stress_or_precursor_evidence_and_native_u_k_correlation_gates_pass\"");
                Require(nativeManifest, "\"PaperGradeTurbulentInletPrerequisiteGate\": \"fail\"");
                Require(nativeManifest, "measured_or_precursor_reynolds_stress_tensor");
                Require(nativeManifest, "inlet_distribution_function_reconstruction");
                Require(nativeManifest, "empty_tunnel_U_k_correlation_preservation_gate");
                Require(metadata, "ClearanceChecks");
                Require(metadata, "DomainContainsBuildings");
                Require(metadata, "BlockageDiagnostics");
                Require(metadata, "ApproxFrontalBlockageRatio");
                Require(metadata, "blockage_diagnostic_ok_verify_against_aij");
                Require(metadata, "diagnostic_clearance_thresholds_satisfied");
                Require(metadata, "avoid zero-speed boundary damping");
                Require(metadata, "diagnostic_only_missing_aij_boundary_protocol_evidence");
                Require(metadata, "not matched to official AIJ wind-tunnel boundary/fetch/roughness evidence");
                Require(metadata, "\"BoundaryConditionMethodClass\": \"citylbm_type_e_box_simplified\"");
                Require(metadata, "\"BoundaryConditionPaperGradeStatus\": \"diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass\"");
                Require(metadata, "\"BoundaryVelocityInitializationMethod\": \"fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces\"");
                Require(metadata, "\"BoundaryOutletTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_not_non_reflecting_or_validated_pressure_outlet\"");
                Require(metadata, "\"BoundarySideTopTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_not_periodic_or_wind_tunnel_equivalent\"");
                Require(metadata, "\"BoundaryRoughnessBoundaryTreatment\": \"TYPE_S_no_slip_only_no_rough_wall_or_wall_function_action\"");
                Require(metadata, "\"BoundaryDevelopmentTreatment\": \"none_no_precursor_or_recycling_development_field\"");
                Require(metadata, "\"BoundaryFixedMeanVelocityOutletRisk\"");
                Require(metadata, "\"PaperGradeBoundaryPrerequisiteGate\": \"fail\"");
                Require(metadata, "non_reflecting_or_validated_outlet_state");
                Require(metadata, "side_top_boundary_pair_mapping_or_wind_tunnel_equivalence");
                Require(metadata, "rough_wall_or_wall_function_action");
                Require(metadata, "precursor_or_recycling_development_field");
                Require(metadata, "official_blockage_fetch_clearance_evidence");
                Require(metadata, "\"BoundaryNonReflectingOutletImplemented\": false");
                Require(metadata, "\"BoundaryRoughWallFunctionImplemented\": false");
                Require(audit, "BoundaryProtocolEvidenceGate=diagnostic_only_missing_aij_boundary_protocol_evidence");
                Require(nativeManifest, "\"BoundaryConditionMethodClass\": \"citylbm_type_e_box_simplified\"");
                Require(nativeManifest, "\"BoundaryVelocityInitializationMethod\": \"fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces\"");
                Require(nativeManifest, "\"BoundaryOutletTreatment\": \"TYPE_E_fixed_mean_velocity_equilibrium_not_non_reflecting_or_validated_pressure_outlet\"");
                Require(nativeManifest, "\"PaperGradeBoundaryPrerequisiteGate\": \"fail\"");
                Require(nativeManifest, "official_blockage_fetch_clearance_evidence");

                TestFluidX3DSourceValidation();
                TestSyntheticInletRequiresCompleteKProfile();
                TestProbeComponentSourceGuard();
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

        private static string CreateFakeFluidX3DSourceTree(string name)
        {
            string root = Path.Combine(Path.GetTempPath(), "CityLBM", name);
            string src = Path.Combine(root, "src");
            Directory.CreateDirectory(src);

            File.WriteAllText(Path.Combine(root, "Makefile"), "# fake build file");
            File.WriteAllText(Path.Combine(src, "setup.cpp"), "// setup");
            File.WriteAllText(Path.Combine(src, "defines.hpp"), "// defines");
            File.WriteAllText(Path.Combine(src, "lbm.hpp"), "// lbm hpp");
            File.WriteAllText(Path.Combine(src, "lbm.cpp"), "// lbm cpp");
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
            Require(source, "GH_ParamAccess.item, 40000");
            Require(source, "GH_ParamAccess.item, 1000");
            Require(source, "int timeSteps = 40000;");
            Require(source, "int saveInterval = 1000;");
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
