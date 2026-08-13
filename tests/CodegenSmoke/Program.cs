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
                Origin = new Point3d(-60, -120, 0),
                DomainBounds = new BoundingBox(new Point3d(-60, -120, 0), new Point3d(70, 60, 70))
            };
                var settings = new SimulationSettings
                {
                    TimeSteps = 1000,
                    SaveInterval = 100,
                    EnableSyntheticTurbulentInlet = true,
                    SyntheticTurbulenceIntensityScale = 1.0,
                    SyntheticTurbulenceCorrelationCells = 4.0,
                    SyntheticTurbulenceUpdateInterval = 7,
                    SyntheticTurbulenceMaxFractionOfMean = 0.42
                };

                var solver = new FluidX3DInterface("__no_fluidx3d_autodetect__");
                string caseDir = Path.Combine(Path.GetTempPath(), "CityLBM", "stg_codegen_smoke");
                Directory.CreateDirectory(caseDir);
                Directory.CreateDirectory(Path.Combine(caseDir, "output"));

                InvokePrivate(
                    solver,
                    "GenerateSetupCpp",
                    scene,
                    grid,
                    settings,
                    Path.Combine(caseDir, "setup.cpp"),
                    "buildings.stl",
                    "output");
                InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);

                string setup = File.ReadAllText(Path.Combine(caseDir, "setup.cpp"));
                string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
                string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));

                Require(setup, "profile_k_lbm[profile_count]");
                Require(setup, "citylbm_stg_mode_count");
                Require(setup, "sqrtf(6.0f / (float)citylbm_stg_mode_count)");
                Require(setup, "citylbm_mode_amplitude");
                Require(setup, "ak*kx");
                Require(setup, "Target component RMS follows isotropic k");
                Require(setup, "citylbm_stg_update_interval = 7u");
                Require(setup, "citylbm_stg_max_fraction = 0.420000f");
                Require(setup, "syntheticTurbulentInlet");
                Require(setup, "applySyntheticTurbulentInlet");
                Require(metadata, "divergence-reduced spectral modes");
                Require(metadata, "projected normal to synthetic wave vectors");
                Require(metadata, "component RMS target sigma=sqrt(2k/3)");
                Require(metadata, "\"SyntheticTurbulenceUpdateInterval\": 7");
                Require(metadata, "\"SyntheticTurbulenceMaxFractionOfMean\": 0.42");
                Require(metadata, "velocity_field_only_no_distribution_function_reconstruction");
                Require(audit, "inlet_distribution_consistency");
                Require(audit, "STG-lite");
                Require(metadata, "ClearanceChecks");
                Require(metadata, "DomainContainsBuildings");
                Require(metadata, "BlockageDiagnostics");
                Require(metadata, "ApproxFrontalBlockageRatio");
                Require(metadata, "blockage_diagnostic_ok_verify_against_aij");
                Require(metadata, "diagnostic_clearance_thresholds_satisfied");
                Require(audit, "diagnostic_clearance_ok_verify_against_aij");

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
    }
}
