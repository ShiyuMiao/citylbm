using System;
using System.Collections.Generic;
using System.Drawing;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Reports the formal AIJ Case E official z=2 m metric gate.
    /// </summary>
    public class CaseEOfficialMetricGateComponent : GH_Component
    {
        private const int OfficialProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const double OfficialMaePp = 21.111408125;
        private const double OfficialRmsePp = 27.72103208243715;
        private const double OfficialBiasPp = -16.409216;
        private const double OfficialR2 = -2.006330362229977;
        private const double OfficialPearson = 0.11575649438573923;
        private const double MaeThresholdPp = 15.0;
        private const double R2Threshold = 0.0;
        private const double PearsonThreshold = 0.0;
        private const string OfficialSamplingMode = "raw_trilinear";
        private const string EvidenceType = "preexisting_artifact";

        public CaseEOfficialMetricGateComponent()
            : base(
                "Case E Official Metric Gate",
                "CaseE Gate",
                "Reports the official AIJ Case E z=2 m metric gate, thresholds, verdict, and forbidden claim boundary.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Release Target",
                "Tag",
                "Optional release target label. Formal v0.4.0 remains blocked until release_gate.json passes.",
                GH_ParamAccess.item,
                "v0.4.0");
            pManager[0].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready official metric gate report.", GH_ParamAccess.item);
            pManager.AddTextParameter("Metric Rows", "M", "Official Case E z=2 m metric rows.", GH_ParamAccess.list);
            pManager.AddTextParameter("Threshold Rows", "T", "Formal release threshold rows.", GH_ParamAccess.list);
            pManager.AddTextParameter("Gate Checks", "Checks", "Pass/fail checks for the formal metric gate.", GH_ParamAccess.list);
            pManager.AddTextParameter("Forbidden Claims", "No", "Claims blocked by the current official metric gate.", GH_ParamAccess.list);
            pManager.AddBooleanParameter("Formal Release Allowed", "Formal", "False while MAE, R2, and release evidence gates fail.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Ready", "Current claim readiness classification.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string releaseTarget = "v0.4.0";
            DA.GetData(0, ref releaseTarget);

            var metricRows = BuildMetricRows();
            var thresholdRows = BuildThresholdRows();
            var gateChecks = BuildGateChecks();
            var forbiddenClaims = BuildForbiddenClaims();
            string claimReadiness = "limitations_ready_negative_validation; blocked_formal_accuracy_release";
            string report = BuildReport(releaseTarget, metricRows, thresholdRows, gateChecks, forbiddenClaims, claimReadiness);

            DA.SetData(0, report);
            DA.SetDataList(1, metricRows);
            DA.SetDataList(2, thresholdRows);
            DA.SetDataList(3, gateChecks);
            DA.SetDataList(4, forbiddenClaims);
            DA.SetData(5, false);
            DA.SetData(6, claimReadiness);
        }

        private static List<string> BuildMetricRows()
        {
            return new List<string>
            {
                "n=80; case=ac; wind_direction=N; height_m=2.0; sampling_mode=raw_trilinear",
                "MAE_pp=21.111408125",
                "RMSE_pp=27.72103208243715",
                "bias_pp=-16.409216",
                "R2=-2.006330362229977",
                "Pearson=0.11575649438573923"
            };
        }

        private static List<string> BuildThresholdRows()
        {
            return new List<string>
            {
                "MAE threshold: < 15.0 pp",
                "R2 threshold: > 0.0",
                "Pearson threshold: > 0.0",
                "Formal protocol: official z=2 m, 80 ac+N probes, raw_trilinear",
                "Forbidden substitutes: z_plus_half, z+4.5 m, diagnostic sampling, post-hoc affine calibration"
            };
        }

        private static List<string> BuildGateChecks()
        {
            bool maePass = OfficialMaePp < MaeThresholdPp;
            bool r2Pass = OfficialR2 > R2Threshold;
            bool pearsonPass = OfficialPearson > PearsonThreshold;
            bool metricGatePass = maePass && r2Pass && pearsonPass;

            return new List<string>
            {
                "official_protocol_check=true",
                "probe_count_check=true",
                "sampling_mode_check=true",
                "mae_check=" + maePass.ToString().ToLowerInvariant(),
                "r2_check=" + r2Pass.ToString().ToLowerInvariant(),
                "pearson_check=" + pearsonPass.ToString().ToLowerInvariant(),
                "official_z2m_metric_gate=" + metricGatePass.ToString().ToLowerInvariant(),
                "formal_release_allowed=false"
            };
        }

        private static List<string> BuildForbiddenClaims()
        {
            return new List<string>
            {
                "Do not claim predictive accuracy.",
                "Do not claim research-grade wind-field accuracy.",
                "Do not claim mesh independence.",
                "Do not claim LES improvement.",
                "Do not claim formal v0.4.0 release readiness.",
                "Do not claim diagnostic sampling, z-offset, or post-hoc calibration as official validation."
            };
        }

        private static string BuildReport(
            string releaseTarget,
            IEnumerable<string> metricRows,
            IEnumerable<string> thresholdRows,
            IEnumerable<string> gateChecks,
            IEnumerable<string> forbiddenClaims,
            string claimReadiness)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Official Metric Gate");
            sb.AppendLine();
            sb.AppendLine("release_target: " + (string.IsNullOrWhiteSpace(releaseTarget) ? "v0.4.0" : releaseTarget));
            sb.AppendLine("evidence_type: " + EvidenceType);
            sb.AppendLine("case: ac");
            sb.AppendLine("wind_direction: N");
            sb.AppendLine("validation_height_m: " + OfficialHeightM.ToString("0.0"));
            sb.AppendLine("probe_count: " + OfficialProbeCount);
            sb.AppendLine("sampling_mode: " + OfficialSamplingMode);
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine("claim_readiness: " + claimReadiness);
            sb.AppendLine();
            AppendList(sb, "metric_rows", metricRows);
            AppendList(sb, "threshold_rows", thresholdRows);
            AppendList(sb, "gate_checks", gateChecks);
            AppendList(sb, "forbidden_claims", forbiddenClaims);
            sb.AppendLine("boundary: This component reports the current official metric gate only. It does not run CFD, update metrics, promote defaults, prove Rhino loaded the plugin, or permit formal v0.4.0.");
            return sb.ToString();
        }

        private static void AppendList(StringBuilder sb, string title, IEnumerable<string> rows)
        {
            sb.AppendLine(title + ":");
            foreach (string row in rows)
            {
                sb.AppendLine("- " + row);
            }
            sb.AppendLine();
        }

        protected override Bitmap Icon
        {
            get { return null!; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("E0A4B8D7-0269-4090-9F50-9125A84D43DF"); }
        }
    }
}
