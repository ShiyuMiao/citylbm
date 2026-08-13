using System;
using System.Collections.Generic;
using System.Drawing;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Exports claim-safe Case E paper statements and limitations.
    /// </summary>
    public class CaseEPaperClaimCardComponent : GH_Component
    {
        private const double OfficialMaePp = 21.111408125;
        private const double OfficialRmsePp = 27.72103208243715;
        private const double OfficialR2 = -2.006330362229977;
        private const double OfficialPearson = 0.11575649438573923;
        private const int OfficialProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const string OfficialSamplingMode = "raw_trilinear";
        private const string EvidenceType = "preexisting_artifact";

        public CaseEPaperClaimCardComponent()
            : base(
                "Case E Paper Claim Card",
                "CaseE Claims",
                "Exports paper-safe Case E statements, limitations, evidence paths, and forbidden claims.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Release Target",
                "Tag",
                "Optional release target label for the paper claim card. Formal v0.4.0 remains blocked until release_gate.json passes.",
                GH_ParamAccess.item,
                "v0.4.0");
            pManager[0].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready paper claim card for AIJ Case E.", GH_ParamAccess.item);
            pManager.AddTextParameter("Paper Ready Claims", "Claims", "Statements that can be used in Results/Methods with the stated evidence boundary.", GH_ParamAccess.list);
            pManager.AddTextParameter("Limitations", "Limits", "Statements that belong in limitations or discussion, not accuracy claims.", GH_ParamAccess.list);
            pManager.AddTextParameter("Forbidden Claims", "No", "Claims that this evidence does not support.", GH_ParamAccess.list);
            pManager.AddTextParameter("Evidence Paths", "Paths", "Primary artifacts to cite for the current Case E evidence chain.", GH_ParamAccess.list);
            pManager.AddBooleanParameter("Formal Release Allowed", "Formal", "False until official z=2 m release gates pass.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Ready", "Current claim readiness classification.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string releaseTarget = "v0.4.0";
            DA.GetData(0, ref releaseTarget);

            var paperReadyClaims = BuildPaperReadyClaims();
            var limitations = BuildLimitations();
            var forbiddenClaims = BuildForbiddenClaims();
            var evidencePaths = BuildEvidencePaths();
            string claimReadiness = "paper_ready_negative_validation_and_limitations; blocked_formal_accuracy_release";
            string report = BuildReport(
                releaseTarget,
                paperReadyClaims,
                limitations,
                forbiddenClaims,
                evidencePaths,
                claimReadiness);

            DA.SetData(0, report);
            DA.SetDataList(1, paperReadyClaims);
            DA.SetDataList(2, limitations);
            DA.SetDataList(3, forbiddenClaims);
            DA.SetDataList(4, evidencePaths);
            DA.SetData(5, false);
            DA.SetData(6, claimReadiness);
        }

        private static List<string> BuildPaperReadyClaims()
        {
            return new List<string>
            {
                "C001 official z=2 m Case E validation is currently a negative-validation result: MAE=21.111408 pp, R2=-2.006330, Pearson=0.115756, n=80, raw_trilinear.",
                "C002 CityLBM v0.4.0-rc evidence supports a reproducible Rhino/GH to FluidX3D to report workflow, but not formal predictive accuracy.",
                "C003 The current paper-ready contribution is a traceable diagnostic workflow with explicit release gates, claim gates, and default-promotion guards.",
                "C004 Case A remains a smoke-regression guard for the workflow; it is not a substitute for Case E accuracy validation.",
                "C005 Follow-up wall, inlet, and C016 channel-response settings are pre-registered experimental switches until official raw_trilinear metrics pass."
            };
        }

        private static List<string> BuildLimitations()
        {
            return new List<string>
            {
                "L001 official z=2 m R2 remains negative, so Case E does not meet the formal v0.4.0 accuracy gate.",
                "L002 MAE remains above the <15 pp project release threshold by 6.111408 pp.",
                "L003 Rhino/Grasshopper manual new-GHA load evidence remains blocked until a real session records version and SHA256 evidence.",
                "L004 GPU runtime is currently blocked by a GPU-lost state, so no new long FluidX3D follow-up run is scheduled from this evidence.",
                "L005 z+4.5 m, z_plus_half, diagnostic sampling, and post-hoc affine calibration are not official validation substitutes.",
                "L006 VS C++ Build Tools and C: drive space remain operational blockers for native build-chain completeness."
            };
        }

        private static List<string> BuildForbiddenClaims()
        {
            return new List<string>
            {
                "F001 Do not claim predictive accuracy.",
                "F002 Do not claim mesh independence.",
                "F003 Do not claim LES improvement.",
                "F004 Do not claim formal v0.4.0 release readiness.",
                "F005 Do not claim diagnostic sampling or z-offset results as official z=2 m validation.",
                "F006 Do not use post-hoc affine calibration as predictive validation.",
                "F007 Do not state that Rhino loaded the new GHA until the manual manifest and screenshot/log evidence exist."
            };
        }

        private static List<string> BuildEvidencePaths()
        {
            return new List<string>
            {
                "docs/experiments/casee/results/release_gate.json",
                "docs/experiments/casee/results/casee_metrics.csv",
                "docs/experiments/casee/results/casee_validation_report.md",
                "docs/experiments/casee/results/casee_reproducibility_suite.json",
                "docs/experiments/casee/results/casee_paper_evidence_gate.json",
                "docs/experiments/casee/results/casee_publication_readiness_gate.json",
                "docs/experiments/casee/results/citylbm_software_feedback_matrix.json",
                "docs/experiments/casee/results/casee_remaining_blockers.json",
                "docs/experiments/casee/results/casee_next_experiment_runbook.json"
            };
        }

        private static string BuildReport(
            string releaseTarget,
            IEnumerable<string> paperReadyClaims,
            IEnumerable<string> limitations,
            IEnumerable<string> forbiddenClaims,
            IEnumerable<string> evidencePaths,
            string claimReadiness)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Paper Claim Card");
            sb.AppendLine();
            sb.AppendLine("release_target: " + (string.IsNullOrWhiteSpace(releaseTarget) ? "v0.4.0" : releaseTarget));
            sb.AppendLine("evidence_type: " + EvidenceType);
            sb.AppendLine("case: ac");
            sb.AppendLine("wind_direction: N");
            sb.AppendLine("validation_height_m: " + OfficialHeightM.ToString("0.0"));
            sb.AppendLine("probe_count: " + OfficialProbeCount);
            sb.AppendLine("sampling_mode: " + OfficialSamplingMode);
            sb.AppendLine("official_mae_pp: " + OfficialMaePp.ToString("0.000000"));
            sb.AppendLine("official_rmse_pp: " + OfficialRmsePp.ToString("0.000000"));
            sb.AppendLine("official_r2: " + OfficialR2.ToString("0.000000"));
            sb.AppendLine("official_pearson: " + OfficialPearson.ToString("0.000000"));
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine("claim_readiness: " + claimReadiness);
            sb.AppendLine();
            AppendList(sb, "paper_ready_claims", paperReadyClaims);
            AppendList(sb, "limitations", limitations);
            AppendList(sb, "forbidden_claims", forbiddenClaims);
            AppendList(sb, "evidence_paths", evidencePaths);
            sb.AppendLine("boundary: This card is paper-writing support only. It does not run CFD, update metrics, promote defaults, prove Rhino loaded the plugin, or permit formal v0.4.0.");
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
            get { return new Guid("BA36730E-EEE4-4DB6-A360-61F889517DF1"); }
        }
    }
}
