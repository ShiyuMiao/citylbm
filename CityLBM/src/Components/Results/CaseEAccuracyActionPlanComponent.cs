using System;
using System.Collections.Generic;
using System.Drawing;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Reports the current Case E accuracy gap and claim-safe next actions.
    /// </summary>
    public class CaseEAccuracyActionPlanComponent : GH_Component
    {
        private const double OfficialMaePp = 21.111408125;
        private const double OfficialR2 = -2.006330362229977;
        private const double OfficialPearson = 0.11575649438573923;
        private const double MaeThresholdPp = 15.0;
        private const double R2Threshold = 0.0;
        private const double PearsonThreshold = 0.0;
        private const int OfficialProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const string OfficialSamplingMode = "raw_trilinear";

        public CaseEAccuracyActionPlanComponent()
            : base(
                "Case E Accuracy Action Plan",
                "CaseE Plan",
                "Reports the official AIJ Case E z=2 m accuracy gap, next actions, and forbidden claim boundary.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Release Target",
                "Tag",
                "Optional release target label for the report. Formal v0.4.0 remains blocked until release_gate.json passes.",
                GH_ParamAccess.item,
                "v0.4.0");
            pManager[0].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready official metric gap and accuracy action plan.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Claim", "Current claim readiness for paper and release use.", GH_ParamAccess.item);
            pManager.AddBooleanParameter("Formal Release Allowed", "Formal", "False until official z=2 m gates pass in release_gate.json.", GH_ParamAccess.item);
            pManager.AddNumberParameter("MAE Gap pp", "MAEGap", "Current MAE percentage-point gap to the <15 pp release threshold.", GH_ParamAccess.item);
            pManager.AddNumberParameter("R2 Gap", "R2Gap", "Current R2 gap to a positive official z=2 m value.", GH_ParamAccess.item);
            pManager.AddTextParameter("Next Actions", "Actions", "Ordered claim-safe next actions before any formal accuracy claim.", GH_ParamAccess.list);
            pManager.AddTextParameter("Boundary", "B", "Forbidden claims and default-promotion boundary.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string releaseTarget = "v0.4.0";
            DA.GetData(0, ref releaseTarget);

            double maeGap = Math.Max(0.0, OfficialMaePp - MaeThresholdPp);
            double r2Gap = Math.Max(0.0, R2Threshold - OfficialR2);
            string claimReadiness = "limitations_ready_action_plan; blocked_formal_accuracy_release";
            string boundary =
                "default_setting_allowed: false; This component is software workflow evidence only. " +
                "It must not be cited as predictive accuracy, mesh independence, LES improvement, formal v0.4.0, " +
                "diagnostic sampling as official validation, or post-hoc affine calibration as predictive validation.";

            var actions = BuildActions();
            string report = BuildReport(releaseTarget, maeGap, r2Gap, claimReadiness, actions, boundary);

            DA.SetData(0, report);
            DA.SetData(1, claimReadiness);
            DA.SetData(2, false);
            DA.SetData(3, maeGap);
            DA.SetData(4, r2Gap);
            DA.SetDataList(5, actions);
            DA.SetData(6, boundary);
        }

        private static List<string> BuildActions()
        {
            return new List<string>
            {
                "A001 keep formal v0.4.0 release blocked until release_gate.json passes official z=2 m raw_trilinear metrics",
                "A002 complete Rhino/GHA manual load evidence before claiming the new CityLBM GHA was used",
                "A003 recover GPU runtime and official-run preflight before scheduling new long FluidX3D runs",
                "A004 run the wall-model official follow-up after recovery and audit with casee_audit.py",
                "A005 run the AF-k/no-SGS inlet official follow-up after recovery and audit with casee_audit.py",
                "A006 run the C016 channel-response follow-up only after leakage and default-promotion guards pass",
                "A007 audit every new Case E probe CSV with official case=ac, Wind_direction=N, z=2 m, 80 probes, raw_trilinear",
                "A008 reject post-hoc affine calibration as a default setting or predictive validation result"
            };
        }

        private static string BuildReport(
            string releaseTarget,
            double maeGap,
            double r2Gap,
            string claimReadiness,
            IEnumerable<string> actions,
            string boundary)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Accuracy Action Plan");
            sb.AppendLine();
            sb.AppendLine("release_target: " + (string.IsNullOrWhiteSpace(releaseTarget) ? "v0.4.0" : releaseTarget));
            sb.AppendLine("case: ac");
            sb.AppendLine("wind_direction: N");
            sb.AppendLine("validation_height_m: " + OfficialHeightM.ToString("0.0"));
            sb.AppendLine("probe_count: " + OfficialProbeCount);
            sb.AppendLine("sampling_mode: " + OfficialSamplingMode);
            sb.AppendLine();
            sb.AppendLine("official_mae_pp: " + OfficialMaePp.ToString("0.000000"));
            sb.AppendLine("official_r2: " + OfficialR2.ToString("0.000000"));
            sb.AppendLine("official_pearson: " + OfficialPearson.ToString("0.000000"));
            sb.AppendLine("mae_threshold_pp: < " + MaeThresholdPp.ToString("0.0"));
            sb.AppendLine("r2_threshold: > " + R2Threshold.ToString("0.0"));
            sb.AppendLine("pearson_threshold: > " + PearsonThreshold.ToString("0.0"));
            sb.AppendLine("mae_gap_pp: " + maeGap.ToString("0.000000"));
            sb.AppendLine("r2_gap: " + r2Gap.ToString("0.000000"));
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine("claim_readiness: " + claimReadiness);
            sb.AppendLine();
            sb.AppendLine("next_actions:");
            foreach (string action in actions)
            {
                sb.AppendLine("- " + action);
            }
            sb.AppendLine();
            sb.AppendLine("boundary: " + boundary);
            return sb.ToString();
        }

        protected override Bitmap Icon
        {
            get { return null!; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("862C4BA3-B4EC-4E33-88CA-0F7345708B68"); }
        }
    }
}
