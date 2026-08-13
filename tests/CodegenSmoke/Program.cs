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
                InvokePrivate(solver, "GenerateDefinesHpp", grid, settings, definesPath, true);
                File.WriteAllText(stlPath, "solid smoke\nendsolid smoke\n");
                InvokePrivate(solver, "SaveDomainOrigin", caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
                InvokePrivate(solver, "SaveCaseMetadata", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveValidationProtocolAudit", caseDir, scene, grid, settings);
                InvokePrivate(solver, "SaveNativeFluidX3DBaselineManifest", caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

                string setup = File.ReadAllText(setupPath);
                string metadata = File.ReadAllText(Path.Combine(caseDir, "case_metadata.json"));
                string audit = File.ReadAllText(Path.Combine(caseDir, "validation_protocol_audit.json"));
                string nativeManifest = File.ReadAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.json"));

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
                Require(setup, "GRAPHICS mode uses the same STG refresh loop as batch mode");
                Require(setup, "steps_to_run = remaining < citylbm_stg_update_interval ? remaining : citylbm_stg_update_interval");
                Require(setup, "if(lbm.flags[n] == TYPE_E &&");
                Require(setup, "lbm.flags.read_from_device();");
                Require(setup, "initialize all TYPE_E boundary velocities");
                Require(setup, "if(lbm.flags[n] != TYPE_E) return;");
                Require(setup, "float3 u_e = windProfile(z);");
                Require(metadata, "divergence-reduced spectral modes");
                Require(metadata, "projected normal to synthetic wave vectors");
                Require(metadata, "component RMS target sigma=sqrt(2k/3)");
                Require(metadata, "\"SyntheticTurbulenceUpdateInterval\": 7");
                Require(metadata, "\"SyntheticTurbulenceMaxFractionOfMean\": 0.42");
                Require(metadata, "refreshed on TYPE_E inlet nodes in batch and graphics modes");
                Require(metadata, "\"ExpectedVtkFrameCount\": 10");
                Require(metadata, "\"TimeAveragingRunGate\": \"pass_minimum_frame_count\"");
                Require(metadata, "Mode 1/2/3 require ExpectedVtkFrameCount");
                Require(audit, "inlet_distribution_consistency");
                Require(audit, "STG-lite");
                Require(audit, "ExpectedVtkFrameCount=10");
                Require(nativeManifest, "NativeFluidX3DPathExplicitlyProvided");
                Require(nativeManifest, "NativeFluidX3DSourceValidation");
                Require(nativeManifest, "Native FluidX3D original setup");
                Require(nativeManifest, "Native FluidX3D lbm.hpp");
                Require(nativeManifest, "auto-detected paths are not sufficient evidence");
                Require(metadata, "ClearanceChecks");
                Require(metadata, "DomainContainsBuildings");
                Require(metadata, "BlockageDiagnostics");
                Require(metadata, "ApproxFrontalBlockageRatio");
                Require(metadata, "blockage_diagnostic_ok_verify_against_aij");
                Require(metadata, "diagnostic_clearance_thresholds_satisfied");
                Require(metadata, "avoid zero-speed boundary damping");
                Require(audit, "diagnostic_clearance_ok_verify_against_aij");

                TestFluidX3DSourceValidation();
                TestProbeComponentSourceGuard();

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
