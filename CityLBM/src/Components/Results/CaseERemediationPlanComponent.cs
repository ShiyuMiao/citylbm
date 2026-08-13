using System;
using System.Collections.Generic;
using System.Drawing;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Exposes the current Case E release blockers and remediation checks.
    /// </summary>
    public class CaseERemediationPlanComponent : GH_Component
    {
        private const double OfficialMaePp = 21.111408125;
        private const double OfficialRmsePp = 27.72103208243715;
        private const double OfficialBiasPp = -16.409216;
        private const double OfficialR2 = -2.006330362229977;
        private const double OfficialPearson = 0.11575649438573923;
        private const int OfficialProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const string OfficialSamplingMode = "raw_trilinear";
        private const string EvidenceType = "preexisting_artifact";

        public CaseERemediationPlanComponent()
            : base(
                "Case E Remediation Plan",
                "CaseE FixPlan",
                "Reports the current Case E release blockers, required actions, verification commands, and forbidden claim boundary.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Release Target",
                "Tag",
                "Optional release target label for the remediation plan. Formal v0.4.0 remains blocked until release_gate.json passes.",
                GH_ParamAccess.item,
                "v0.4.0");
            pManager[0].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready Case E blocker and remediation plan.", GH_ParamAccess.item);
            pManager.AddTextParameter("Blockers", "Block", "Current release blockers with severity and evidence.", GH_ParamAccess.list);
            pManager.AddTextParameter("Required Actions", "Act", "Required actions before another formal accuracy claim or release.", GH_ParamAccess.list);
            pManager.AddTextParameter("Verification", "Verify", "Commands or artifacts that must prove each blocker is resolved.", GH_ParamAccess.list);
            pManager.AddTextParameter("Pass Conditions", "Pass", "Release-safe pass conditions for each blocker.", GH_ParamAccess.list);
            pManager.AddTextParameter("Forbidden Claims", "No", "Claims that remain unsupported until the blockers are resolved.", GH_ParamAccess.list);
            pManager.AddTextParameter("Next Experiments", "Next", "Ordered official follow-up experiments after environment recovery.", GH_ParamAccess.list);
            pManager.AddBooleanParameter("Formal Release Allowed", "Formal", "False until official z=2 m release gates pass.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Ready", "Current claim readiness classification.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string releaseTarget = "v0.4.0";
            DA.GetData(0, ref releaseTarget);

            var blockers = BuildBlockers();
            var actions = BuildActions();
            var verification = BuildVerification();
            var passConditions = BuildPassConditions();
            var forbiddenClaims = BuildForbiddenClaims();
            var nextExperiments = BuildNextExperiments();
            string claimReadiness = "blocked_followup_plan; paper_ready_limitations_support";
            string report = BuildReport(
                releaseTarget,
                blockers,
                actions,
                verification,
                passConditions,
                forbiddenClaims,
                nextExperiments,
                claimReadiness);

            DA.SetData(0, report);
            DA.SetDataList(1, blockers);
            DA.SetDataList(2, actions);
            DA.SetDataList(3, verification);
            DA.SetDataList(4, passConditions);
            DA.SetDataList(5, forbiddenClaims);
            DA.SetDataList(6, nextExperiments);
            DA.SetData(7, false);
            DA.SetData(8, claimReadiness);
        }

        private static List<string> BuildBlockers()
        {
            return new List<string>
            {
                "B001 official_z2m_metric_gate: critical; official z=2 m raw_trilinear n=80; MAE=21.111408 pp; RMSE=27.721032 pp; bias=-16.409216 pp; R2=-2.006330; Pearson=0.115756",
                "B002 rhino_new_gha_load: critical; Rhino/Grasshopper manual evidence for the new tracked GHA is still absent",
                "B003 gpu_runtime: critical; nvidia-smi reports GPU is lost, so new long FluidX3D runs are not allowed",
                "B004 vs_cpp_build_tools: major; Visual Studio Build Tools 2022 C++ recovery remains blocked while C: drive space is unavailable",
                "B005 dx1_high_resolution_run: major; dx=1 m official run is not started and cannot support mesh independence"
            };
        }

        private static List<string> BuildActions()
        {
            return new List<string>
            {
                "B001 run a new official z=2 m raw_trilinear Case E experiment only after a physically defensible wall, inlet, voxelization, or probe implementation change",
                "B002 load CityLBM/bin/CityLBM.gha in Rhino/Grasshopper and record version plus SHA256 evidence",
                "B003 recover the NVIDIA runtime before scheduling any additional long native FluidX3D validation run",
                "B004 free enough C: drive space or redirect installer cache, approve UAC, and install the VS Build Tools 2022 C++ workload",
                "B005 run a user-confirmed dx=1 allocation or official run only after GPU and memory checks pass"
            };
        }

        private static List<string> BuildVerification()
        {
            return new List<string>
            {
                "B001 python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_official_casee_probe_time_mean.csv>",
                "B002 manual Rhino/Grasshopper manifest plus screenshot/log showing CityLBM version 0.4.0-rc and matching GHA SHA256",
                "B003 nvidia-smi must return 0 and report the target GPU without GPU-lost errors",
                "B004 vswhere must find Microsoft.VisualStudio.Component.VC.Tools.x86.x64 and vcvars64.bat/cl.exe must be available",
                "B005 completed official dx=1 z=2 m raw_trilinear 80-probe CSV plus complete run log"
            };
        }

        private static List<string> BuildPassConditions()
        {
            return new List<string>
            {
                "B001 n=80, height=2 m, sampling=raw_trilinear, MAE clearly below prior near-20 pp level, R2>0, Pearson>0",
                "B002 the Rhino/Grasshopper session demonstrably loads the new tracked GHA, not an old installed copy",
                "B003 GPU runtime ready; long FluidX3D follow-up allowed only after preflight passes",
                "B004 Windows native C++ build chain complete with VC tools available",
                "B005 dx=1 m result exists before any mesh-independence discussion"
            };
        }

        private static List<string> BuildForbiddenClaims()
        {
            return new List<string>
            {
                "Do not claim predictive accuracy.",
                "Do not claim mesh independence.",
                "Do not claim LES improvement.",
                "Do not claim formal v0.4.0 release readiness.",
                "Do not claim Rhino loaded the new GHA until manual load evidence exists.",
                "Do not claim diagnostic sampling, z-offsets, or post-hoc affine calibration as official validation."
            };
        }

        private static List<string> BuildNextExperiments()
        {
            return new List<string>
            {
                "P1 casee_wall_model_followup: run after GPU recovery and a defensible wall/roughness/voxelization implementation change",
                "P2 casee_inlet_turbulence_followup: run after full-plane AF_caseE z,U,k inlet parameters are changed from documented evidence",
                "P3 casee_dx1_feasibility_or_run: run only after GPU runtime and memory/runtime estimates are acceptable"
            };
        }

        private static string BuildReport(
            string releaseTarget,
            IEnumerable<string> blockers,
            IEnumerable<string> actions,
            IEnumerable<string> verification,
            IEnumerable<string> passConditions,
            IEnumerable<string> forbiddenClaims,
            IEnumerable<string> nextExperiments,
            string claimReadiness)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Remediation Plan");
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
            sb.AppendLine("official_bias_pp: " + OfficialBiasPp.ToString("0.000000"));
            sb.AppendLine("official_r2: " + OfficialR2.ToString("0.000000"));
            sb.AppendLine("official_pearson: " + OfficialPearson.ToString("0.000000"));
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine("claim_readiness: " + claimReadiness);
            sb.AppendLine();
            AppendList(sb, "blockers", blockers);
            AppendList(sb, "required_actions", actions);
            AppendList(sb, "verification", verification);
            AppendList(sb, "pass_conditions", passConditions);
            AppendList(sb, "forbidden_claims", forbiddenClaims);
            AppendList(sb, "next_experiments", nextExperiments);
            sb.AppendLine("boundary: This plan is operational and paper-limitations support only. It does not run CFD, update metrics, promote defaults, prove Rhino loaded the plugin, or permit formal v0.4.0.");
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
            get { return new Guid("3F46B886-F94E-492D-9D4F-FA6F170BF1D2"); }
        }
    }
}
