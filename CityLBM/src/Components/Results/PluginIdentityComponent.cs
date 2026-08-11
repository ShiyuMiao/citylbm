using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Reports the loaded CityLBM plugin identity from inside Grasshopper.
    /// </summary>
    public class PluginIdentityComponent : GH_Component
    {
        public PluginIdentityComponent()
            : base(
                "Plugin Identity",
                "Identity",
                "Reports the loaded CityLBM plugin version, GHA path, SHA256, and manual evidence template.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Operator",
                "Op",
                "Optional operator name to include in the manual Rhino/GHA load evidence template.",
                GH_ParamAccess.item,
                "");
            pManager[0].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Human-readable plugin identity report for a Grasshopper Panel.", GH_ParamAccess.item);
            pManager.AddTextParameter("Plugin Version", "V", "CityLBM public plugin version.", GH_ParamAccess.item);
            pManager.AddTextParameter("Assembly Version", "AV", "CityLBM assembly version.", GH_ParamAccess.item);
            pManager.AddTextParameter("GHA Path", "Path", "Loaded CityLBM assembly path as observed by Grasshopper.", GH_ParamAccess.item);
            pManager.AddTextParameter("GHA SHA256", "SHA", "SHA256 of the loaded CityLBM assembly path, when readable.", GH_ParamAccess.item);
            pManager.AddTextParameter("Manifest Template", "JSON", "Manual rhino_gha_load_manifest.json template. Replace operator/Rhino/Grasshopper fields with observed session evidence.", GH_ParamAccess.item);
            pManager.AddTextParameter("Boundary", "B", "Claim boundary for this identity evidence.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string operatorName = "";
            DA.GetData(0, ref operatorName);

            string assemblyPath = Assembly.GetExecutingAssembly().Location ?? "";
            string digest = File.Exists(assemblyPath) ? ComputeSha256(assemblyPath) : "";
            string checkedAt = DateTime.UtcNow.ToString("o");
            string boundary =
                "This component proves only the CityLBM plugin identity loaded in the current Grasshopper process. " +
                "It is not CFD accuracy evidence and must not change official AIJ Case E z=2 m metrics.";

            string report = BuildReport(checkedAt, operatorName, assemblyPath, digest, boundary);
            string manifestTemplate = BuildManifestTemplate(checkedAt, operatorName, digest);

            DA.SetData(0, report);
            DA.SetData(1, CityLBMPlugin.PluginVersion);
            DA.SetData(2, CityLBMPlugin.PluginAssemblyVersion);
            DA.SetData(3, assemblyPath);
            DA.SetData(4, digest);
            DA.SetData(5, manifestTemplate);
            DA.SetData(6, boundary);
        }

        private static string ComputeSha256(string path)
        {
            using (var stream = File.OpenRead(path))
            using (var sha = SHA256.Create())
            {
                byte[] hash = sha.ComputeHash(stream);
                var sb = new StringBuilder(hash.Length * 2);
                foreach (byte b in hash)
                {
                    sb.Append(b.ToString("x2"));
                }
                return sb.ToString();
            }
        }

        private static string BuildReport(string checkedAt, string operatorName, string assemblyPath, string digest, string boundary)
        {
            var sb = new StringBuilder();
            sb.AppendLine("CityLBM Plugin Identity");
            sb.AppendLine();
            sb.AppendLine("checked_at_utc: " + checkedAt);
            sb.AppendLine("operator: " + (string.IsNullOrWhiteSpace(operatorName) ? "manual-operator-name" : operatorName));
            sb.AppendLine("plugin_version: " + CityLBMPlugin.PluginVersion);
            sb.AppendLine("assembly_version: " + CityLBMPlugin.PluginAssemblyVersion);
            sb.AppendLine("loaded_assembly_path: " + assemblyPath);
            sb.AppendLine("loaded_assembly_sha256: " + digest);
            sb.AppendLine();
            sb.AppendLine("boundary: " + boundary);
            return sb.ToString();
        }

        private static string BuildManifestTemplate(string checkedAt, string operatorName, string digest)
        {
            string op = string.IsNullOrWhiteSpace(operatorName) ? "manual-operator-name" : operatorName;
            var sb = new StringBuilder();
            sb.AppendLine("{");
            sb.AppendLine("  \"checked_at\": \"" + JsonEscape(checkedAt) + "\",");
            sb.AppendLine("  \"operator\": \"" + JsonEscape(op) + "\",");
            sb.AppendLine("  \"rhino_version\": \"paste Rhino About/SystemInfo version string\",");
            sb.AppendLine("  \"grasshopper_version\": \"paste Grasshopper version string\",");
            sb.AppendLine("  \"observed_plugin_version\": \"" + JsonEscape(CityLBMPlugin.PluginVersion) + "\",");
            sb.AppendLine("  \"observed_assembly_version\": \"" + JsonEscape(CityLBMPlugin.PluginAssemblyVersion) + "\",");
            sb.AppendLine("  \"observed_gha_sha256\": \"" + JsonEscape(digest) + "\",");
            sb.AppendLine("  \"evidence_artifacts\": [");
            sb.AppendLine("    \"docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png\",");
            sb.AppendLine("    \"docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt\"");
            sb.AppendLine("  ],");
            sb.AppendLine("  \"notes\": \"Generated by the CityLBM Plugin Identity component inside Grasshopper. Add screenshot/log evidence before using this as rhino_gha_load_manifest.json.\"");
            sb.AppendLine("}");
            return sb.ToString();
        }

        private static string JsonEscape(string value)
        {
            if (value == null) return "";
            return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        protected override Bitmap Icon
        {
            get { return null!; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("7B5126DD-4C5F-4C27-8E4C-142792314E55"); }
        }
    }
}
