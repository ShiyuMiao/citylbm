using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using Grasshopper.Kernel;
using Rhino.Geometry;
using CityLBM.Core;
using CityLBM.Utils;

namespace CityLBM.Components.Scene
{
    public class CreateSceneComponent : GH_Component
    {
        public CreateSceneComponent()
            : base("Create Scene", "Scene",
                   "Create a CityLBM urban wind simulation scene. WP=3 uses a custom z,U,k CSV profile.",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter("Name", "N", "Scene name", GH_ParamAccess.item, "CityLBM Scene");
            pManager.AddNumberParameter("Wind Speed", "V",
                "Reference wind speed Uref (m/s). For WP=3 this is metadata/normalization; the CSV controls U(z).",
                GH_ParamAccess.item, 5.0);
            pManager.AddVectorParameter("Wind Direction", "D",
                "Unit wind direction vector. AIJ Case E N wind uses (0,-1,0).",
                GH_ParamAccess.item, new Vector3d(1, 0, 0));
            pManager.AddIntegerParameter("Wind Profile", "WP",
                "0=Uniform, 1=PowerLaw, 2=Logarithmic, 3=CustomTable z,U,k CSV.",
                GH_ParamAccess.item, 1);
            pManager.AddNumberParameter("Reference Height", "Zr",
                "Reference height z_ref (m). For WP=3 this is metadata/normalization.",
                GH_ParamAccess.item, 10.0);
            pManager.AddIntegerParameter("Roughness Category", "RC",
                "GB 50009 roughness category: A=0, B=1, C=2, D=3, Custom=99.",
                GH_ParamAccess.item, 2);
            pManager.AddNumberParameter("Roughness Length", "Z0",
                "Custom roughness length z0 (m), used only when RC=99.",
                GH_ParamAccess.item, 0.3);
            pManager.AddNumberParameter("Domain Extension", "E",
                "Automatic domain extension ratio when no custom domain is connected.",
                GH_ParamAccess.item, 0.2);
            pManager.AddTextParameter("Wind Profile CSV", "CSV",
                "CustomTable input for WP=3. Expected columns: z(m), U(m/s), optional k(m2/s2). If k is present it must be present on every valid row.",
                GH_ParamAccess.item, "");
            pManager[8].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM scene object", GH_ParamAccess.item);
            pManager.AddTextParameter("Profile Info", "Info", "Wind profile summary", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string name = "CityLBM Scene";
            double windSpeed = 5.0;
            Vector3d windDir = new Vector3d(1, 0, 0);
            int windProfileInt = 1;
            double refHeight = 10.0;
            int roughnessCategoryInt = 2;
            double roughnessLength = 0.3;
            double extension = 0.2;
            string profileCsvPath = "";

            if (!DA.GetData(0, ref name)) return;
            if (!DA.GetData(1, ref windSpeed)) return;
            if (!DA.GetData(2, ref windDir)) return;
            if (!DA.GetData(3, ref windProfileInt)) return;
            if (!DA.GetData(4, ref refHeight)) return;
            if (!DA.GetData(5, ref roughnessCategoryInt)) return;
            if (!DA.GetData(6, ref roughnessLength)) return;
            if (!DA.GetData(7, ref extension)) return;
            DA.GetData(8, ref profileCsvPath);

            if (windSpeed <= 0.0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Wind Speed must be greater than 0.");
                return;
            }
            if (refHeight <= 0.0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Reference Height must be greater than 0.");
                return;
            }

            WindProfileType windProfile;
            if (windProfileInt >= 0 && windProfileInt <= 3)
                windProfile = (WindProfileType)windProfileInt;
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "Invalid Wind Profile. Reset to Uniform(0).");
                windProfile = WindProfileType.Uniform;
            }

            RoughnessCategory roughnessCategory;
            double z0;
            double alpha;
            if (roughnessCategoryInt == 99)
            {
                roughnessCategory = RoughnessCategory.Custom;
                if (roughnessLength <= 0.0)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "Custom z0 must be greater than 0. Reset to 0.3 m.");
                    roughnessLength = 0.3;
                }
                z0 = roughnessLength;
                alpha = 0.22;
            }
            else if (roughnessCategoryInt >= 0 && roughnessCategoryInt <= 3)
            {
                roughnessCategory = (RoughnessCategory)roughnessCategoryInt;
                var rp = Core.Scene.GetRoughnessParams(roughnessCategory);
                z0 = rp.Item1;
                alpha = rp.Item2;
                roughnessLength = z0;
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "Invalid Roughness Category. Reset to C.");
                roughnessCategory = RoughnessCategory.C;
                var rp = Core.Scene.GetRoughnessParams(RoughnessCategory.C);
                z0 = rp.Item1;
                alpha = rp.Item2;
                roughnessLength = z0;
            }

            if (windProfile == WindProfileType.Logarithmic && refHeight <= z0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    $"Logarithmic profile requires Zr ({refHeight:F2} m) > z0 ({z0:F3} m).");
                return;
            }

            double kappa = 0.41;
            double uStar = 0.0;
            if (windProfile == WindProfileType.Logarithmic)
                uStar = windSpeed * kappa / Math.Log(refHeight / z0);

            Core.Scene scene = new Core.Scene(name)
            {
                WindSpeed = windSpeed,
                DomainExtensionRatio = extension,
                WindProfile = windProfile,
                ReferenceHeight = Math.Max(refHeight, 0.1),
                RoughnessCategory = roughnessCategory,
                RoughnessLength = z0,
                PowerLawAlpha = alpha,
                VonKarmanConstant = kappa
            };

            if (windDir.IsValid && !windDir.IsZero)
            {
                windDir.Unitize();
                scene.WindDirection = windDir;
            }

            string customProfileReport = "";
            if (windProfile == WindProfileType.CustomTable)
            {
                if (!TryLoadCustomWindProfile(profileCsvPath, out List<WindProfileSample> samples,
                    out customProfileReport, out string loadError))
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Error, loadError);
                    return;
                }

                scene.WindProfileCsvPath = Path.GetFullPath(profileCsvPath);
                scene.CustomWindProfile = samples;
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    "CustomTable profile loaded. U(z) is read from CSV; Wind Speed is retained as Uref/normalization metadata.");
            }

            string profileInfo = BuildProfileInfo(windProfile, windSpeed, refHeight, z0, alpha, uStar, kappa);
            if (!string.IsNullOrEmpty(customProfileReport))
                profileInfo += "\n\n" + customProfileReport;

            DA.SetData(0, new GH_Scene(scene));
            DA.SetData(1, profileInfo);
        }

        private bool TryLoadCustomWindProfile(string csvPath, out List<WindProfileSample> samples,
            out string report, out string error)
        {
            samples = new List<WindProfileSample>();
            report = "";
            error = "";

            if (string.IsNullOrWhiteSpace(csvPath))
            {
                error = "WP=3 CustomTable requires Wind Profile CSV. Expected columns: z(m), U(m/s), optional k(m2/s2). If k is present it must be present on every valid row.";
                return false;
            }

            if (!File.Exists(csvPath))
            {
                error = "Wind Profile CSV not found: " + csvPath;
                return false;
            }

            int skipped = 0;
            int kRows = 0;
            foreach (string rawLine in File.ReadLines(csvPath))
            {
                string line = rawLine.Trim();
                if (line.Length == 0 || line.StartsWith("#"))
                    continue;

                string[] parts = line.Split(new[] { ',', ';', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length < 2)
                {
                    skipped++;
                    continue;
                }

                if (!double.TryParse(parts[0].Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out double z) ||
                    !double.TryParse(parts[1].Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out double u))
                {
                    skipped++;
                    continue;
                }

                if (z < 0.0 || u < 0.0)
                {
                    skipped++;
                    continue;
                }

                bool hasK = false;
                double k = 0.0;
                if (parts.Length >= 3 &&
                    double.TryParse(parts[2].Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out double parsedK))
                {
                    hasK = true;
                    k = Math.Max(0.0, parsedK);
                    kRows++;
                }

                samples.Add(new WindProfileSample { Z = z, U = u, HasK = hasK, K = k });
            }

            samples = samples.OrderBy(s => s.Z).ToList();
            if (samples.Count < 2)
            {
                error = "Wind Profile CSV must contain at least two valid z,U rows: " + csvPath;
                return false;
            }

            bool hasAnyK = samples.Any(s => s.HasK);
            bool hasPartialK = hasAnyK && samples.Any(s => !s.HasK);
            if (hasPartialK)
            {
                error = "Wind Profile CSV has an incomplete k column. For validation, z,U,k lengths must match; every valid z,U row must include k(m2/s2), or no rows should include k.";
                return false;
            }

            for (int i = 1; i < samples.Count; i++)
            {
                if (Math.Abs(samples[i].Z - samples[i - 1].Z) <= 1.0e-9)
                {
                    error = $"Wind Profile CSV contains duplicate z values at {samples[i].Z:F6} m. CustomTable validation requires unique heights for traceable interpolation.";
                    return false;
                }
            }

            report += (report.Length > 0 ? "\n" : "") +
                      "CustomTable profile\n" +
                      "  CSV: " + Path.GetFullPath(csvPath) + "\n" +
                      $"  Rows: {samples.Count}, skipped: {skipped}\n" +
                      $"  z range: {samples[0].Z:F3} to {samples[samples.Count - 1].Z:F3} m\n" +
                      $"  U range: {samples.Min(s => s.U):F4} to {samples.Max(s => s.U):F4} m/s\n" +
                      $"  k column: {(hasAnyK ? $"{kRows} rows, SI m2/s2" : "not provided")}\n" +
                      "  Note: v0.3.0 records and converts k. If provided, k must be complete for all rows. Run Simulation can optionally use it for experimental STG-lite inlet fluctuations.";
            return true;
        }

        private string BuildProfileInfo(WindProfileType profile, double v, double zr,
            double z0, double alpha, double uStar, double kappa)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("Wind profile summary");
            sb.AppendLine($"Type: {profile}");
            sb.AppendLine($"Uref metadata: {v:F4} m/s @ Zr={zr:F3} m");

            switch (profile)
            {
                case WindProfileType.Uniform:
                    sb.AppendLine($"U(z) = {v:F4} m/s");
                    break;
                case WindProfileType.PowerLaw:
                    sb.AppendLine($"U(z) = {v:F4} * (z/{zr:F3})^{alpha:F3}");
                    sb.AppendLine($"alpha={alpha:F3}, z0={z0:F4} m");
                    break;
                case WindProfileType.Logarithmic:
                    sb.AppendLine($"U(z) = ({uStar:F5}/{kappa:F3}) * ln(z/{z0:F4})");
                    sb.AppendLine($"u*={uStar:F5} m/s, kappa={kappa:F3}");
                    break;
                case WindProfileType.CustomTable:
                    sb.AppendLine("U(z) is linearly interpolated from Wind Profile CSV.");
                    sb.AppendLine("CSV columns: z(m), U(m/s), optional k(m2/s2). If k is present, every valid row must include it.");
                    sb.AppendLine("k is converted and recorded in metadata; Run Simulation can optionally use it for experimental STG-lite inlet fluctuations.");
                    break;
            }

            return sb.ToString().TrimEnd();
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("CreateScene.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A"); }
        }
    }
}
