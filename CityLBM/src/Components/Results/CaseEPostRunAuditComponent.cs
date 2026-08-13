using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Checks whether a completed AIJ Case E probe CSV is ready for the official z=2 m audit path.
    /// </summary>
    public class CaseEPostRunAuditComponent : GH_Component
    {
        private const string RequiredCase = "ac";
        private const string RequiredWindDirection = "N";
        private const string RequiredSamplingMode = "raw_trilinear";
        private const int RequiredProbeCount = 80;
        private const int MinimumSteps = 48000;
        private const int MinimumSpinup = 12000;

        public CaseEPostRunAuditComponent()
            : base(
                "Case E Post-run Audit",
                "CaseE Audit",
                "Checks AIJ Case E official z=2 m probe CSV readiness and prints the required audit command.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Candidate CSV",
                "CSV",
                "Path to a completed casee_probe_time_mean.csv candidate. Leave blank to show the armed handoff template.",
                GH_ParamAccess.item,
                "");
            pManager.AddTextParameter(
                "Release Target",
                "Tag",
                "Release target for the generated official audit command.",
                GH_ParamAccess.item,
                "v0.4.0");
            pManager.AddTextParameter(
                "Repository Root",
                "Root",
                "Optional CityLBM repository root used to build an absolute audit script path.",
                GH_ParamAccess.item,
                "");

            pManager[0].Optional = true;
            pManager[1].Optional = true;
            pManager[2].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Audit Command", "Cmd", "Command that must be run before any paper or release accuracy claim.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Ready", "Claim readiness state for the supplied candidate.", GH_ParamAccess.item);
            pManager.AddBooleanParameter("Ready For Official Audit", "Gate", "True only when CSV, protocol manifest, and complete log evidence are structurally admissible.", GH_ParamAccess.item);
            pManager.AddBooleanParameter("Formal Result Allowed Now", "Formal", "Always false in this component; formal permission comes only from casee_audit.py and release_gate.json.", GH_ParamAccess.item);
            pManager.AddTextParameter("Candidate SHA256", "SHA", "SHA256 of the supplied candidate CSV, when readable.", GH_ParamAccess.item);
            pManager.AddTextParameter("Protocol Report", "Report", "Panel-ready report explaining checks, failures, and claim boundaries.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string candidateCsv = "";
            string releaseTarget = "v0.4.0";
            string repositoryRoot = "";
            DA.GetData(0, ref candidateCsv);
            DA.GetData(1, ref releaseTarget);
            DA.GetData(2, ref repositoryRoot);

            if (string.IsNullOrWhiteSpace(releaseTarget))
            {
                releaseTarget = "v0.4.0";
            }

            CandidateAudit audit = AuditCandidate(candidateCsv, releaseTarget, repositoryRoot);
            DA.SetData(0, audit.AuditCommand);
            DA.SetData(1, audit.ClaimReadiness);
            DA.SetData(2, audit.ReadyForOfficialAudit);
            DA.SetData(3, false);
            DA.SetData(4, audit.CandidateSha256);
            DA.SetData(5, audit.Report);
        }

        private static CandidateAudit AuditCandidate(string candidateCsv, string releaseTarget, string repositoryRoot)
        {
            string trimmedCandidate = (candidateCsv ?? "").Trim().Trim('"');
            string auditCommand = BuildAuditCommand(trimmedCandidate, releaseTarget, repositoryRoot);
            var failures = new List<string>();
            var notes = new List<string>();
            string sha = "";

            if (string.IsNullOrWhiteSpace(trimmedCandidate))
            {
                return CandidateAudit.Create(
                    auditCommand,
                    "armed_no_candidate",
                    false,
                    "",
                    BuildReport(
                        "",
                        releaseTarget,
                        auditCommand,
                        "armed_no_candidate",
                        false,
                        "",
                        new List<string> { "No candidate CSV supplied." },
                        new List<string> { "Run FluidX3D first and supply the completed casee_probe_time_mean.csv." }));
            }

            string fullCandidate = Path.GetFullPath(trimmedCandidate);
            if (!File.Exists(fullCandidate))
            {
                failures.Add("Candidate CSV does not exist.");
                return CandidateAudit.Create(
                    auditCommand,
                    "blocked_candidate_missing",
                    false,
                    "",
                    BuildReport(fullCandidate, releaseTarget, auditCommand, "blocked_candidate_missing", false, "", failures, notes));
            }

            sha = ComputeSha256(fullCandidate);
            CsvCheck csvCheck = CheckCsv(fullCandidate);
            failures.AddRange(csvCheck.Failures);
            notes.AddRange(csvCheck.Notes);

            ProtocolCheck protocolCheck = CheckProtocolEvidence(fullCandidate);
            failures.AddRange(protocolCheck.Failures);
            notes.AddRange(protocolCheck.Notes);

            bool ready = csvCheck.Passed && protocolCheck.Passed;
            string readiness = ready ? "ready_for_casee_audit_not_formal_result" : "blocked_candidate_protocol";
            string report = BuildReport(fullCandidate, releaseTarget, auditCommand, readiness, ready, sha, failures, notes);
            return CandidateAudit.Create(auditCommand, readiness, ready, sha, report);
        }

        private static CsvCheck CheckCsv(string path)
        {
            var failures = new List<string>();
            var notes = new List<string>();
            string[] lines = File.ReadAllLines(path);
            if (lines.Length < 2)
            {
                failures.Add("Candidate CSV has no data rows.");
                return new CsvCheck(false, failures, notes);
            }

            string[] headers = SplitCsvLine(lines[0]);
            int noIndex = IndexOf(headers, "No.");
            int officialIndex = IndexOf(headers, "official_velocity_ratio");
            int predictedIndex = IndexOf(headers, "predicted_velocity_ratio");
            if (noIndex < 0) failures.Add("Missing required column: No.");
            if (officialIndex < 0) failures.Add("Missing required column: official_velocity_ratio.");
            if (predictedIndex < 0) failures.Add("Missing required column: predicted_velocity_ratio.");
            if (failures.Count > 0)
            {
                return new CsvCheck(false, failures, notes);
            }

            int validRows = 0;
            var probeIds = new HashSet<int>();
            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i]))
                {
                    continue;
                }

                string[] cells = SplitCsvLine(lines[i]);
                if (cells.Length <= Math.Max(noIndex, Math.Max(officialIndex, predictedIndex)))
                {
                    failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has too few columns.");
                    continue;
                }

                if (int.TryParse(cells[noIndex], NumberStyles.Integer, CultureInfo.InvariantCulture, out int probeId))
                {
                    probeIds.Add(probeId);
                }
                else
                {
                    failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-integer No. value.");
                }

                if (!double.TryParse(cells[officialIndex], NumberStyles.Float, CultureInfo.InvariantCulture, out _))
                {
                    failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-numeric official_velocity_ratio.");
                }

                if (!double.TryParse(cells[predictedIndex], NumberStyles.Float, CultureInfo.InvariantCulture, out _))
                {
                    failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-numeric predicted_velocity_ratio.");
                }

                validRows++;
            }

            if (validRows != RequiredProbeCount)
            {
                failures.Add("Expected 80 official ac+N probe rows; found " + validRows.ToString(CultureInfo.InvariantCulture) + ".");
            }

            bool idsOneToEighty = probeIds.Count == RequiredProbeCount && Enumerable.Range(1, RequiredProbeCount).All(probeIds.Contains);
            if (!idsOneToEighty)
            {
                failures.Add("Probe IDs must be exactly 1..80 for the official Case E probe set.");
            }

            notes.Add("CSV rows checked: " + validRows.ToString(CultureInfo.InvariantCulture));
            return new CsvCheck(failures.Count == 0, failures, notes);
        }

        private static ProtocolCheck CheckProtocolEvidence(string candidatePath)
        {
            var failures = new List<string>();
            var notes = new List<string>();
            string directory = Path.GetDirectoryName(candidatePath) ?? "";
            if (!Directory.Exists(directory))
            {
                failures.Add("Candidate directory is not readable.");
                return new ProtocolCheck(false, failures, notes);
            }

            string manifestText = ReadSidecarText(directory, "*manifest*.json");
            if (string.IsNullOrWhiteSpace(manifestText))
            {
                failures.Add("No sidecar manifest JSON found near the candidate CSV.");
            }
            else
            {
                RequireRegex(manifestText, "\"case\"\\s*:\\s*\"" + RequiredCase + "\"", "Manifest must state case=ac.", failures);
                RequireRegex(manifestText, "\"wind_direction\"\\s*:\\s*\"" + RequiredWindDirection + "\"|\"Wind_direction\"\\s*:\\s*\"" + RequiredWindDirection + "\"", "Manifest must state Wind_direction=N.", failures);
                RequireRegex(manifestText, "\"validation_height_m\"\\s*:\\s*2(?:\\.0+)?|\"height_m\"\\s*:\\s*2(?:\\.0+)?", "Manifest must state official z=2 m validation height.", failures);
                RequireRegex(manifestText, "\"probe_count\"\\s*:\\s*80|\"n_probes\"\\s*:\\s*80", "Manifest must state 80 official probes.", failures);
                RequireRegex(manifestText, "\"sampling_mode\"\\s*:\\s*\"" + RequiredSamplingMode + "\"|\"formal_sampling_mode\"\\s*:\\s*\"" + RequiredSamplingMode + "\"", "Manifest must state raw_trilinear formal sampling.", failures);

                int steps = ExtractInt(manifestText, "\"steps\"\\s*:\\s*(\\d+)|\"time_steps\"\\s*:\\s*(\\d+)");
                int spinup = ExtractInt(manifestText, "\"spinup\"\\s*:\\s*(\\d+)|\"spinup_steps\"\\s*:\\s*(\\d+)");
                if (steps < MinimumSteps)
                {
                    failures.Add("Manifest steps must be >= 48000; found " + steps.ToString(CultureInfo.InvariantCulture) + ".");
                }

                if (spinup < MinimumSpinup)
                {
                    failures.Add("Manifest spinup must be >= 12000; found " + spinup.ToString(CultureInfo.InvariantCulture) + ".");
                }

                notes.Add("Manifest protocol fields checked.");
            }

            string logText = ReadSidecarText(directory, "*.log");
            bool completeLog = Regex.IsMatch(logText, "simulation\\s+(completed|finished|ended)|run\\s+(completed|finished)|FluidX3D.*finished", RegexOptions.IgnoreCase);
            if (!completeLog)
            {
                failures.Add("No complete FluidX3D run log evidence found near the candidate CSV.");
            }
            else
            {
                notes.Add("Complete run log marker found.");
            }

            return new ProtocolCheck(failures.Count == 0, failures, notes);
        }

        private static string BuildAuditCommand(string candidateCsv, string releaseTarget, string repositoryRoot)
        {
            string script = "docs/experiments/casee/tools/casee_audit.py";
            string root = (repositoryRoot ?? "").Trim().Trim('"');
            if (!string.IsNullOrWhiteSpace(root))
            {
                script = Path.Combine(Path.GetFullPath(root), script);
            }

            string predicted = string.IsNullOrWhiteSpace(candidateCsv) ? "<new_casee_probe_time_mean.csv>" : Path.GetFullPath(candidateCsv);
            return "python \"" + script + "\" --release-target " + releaseTarget + " --predicted \"" + predicted + "\"";
        }

        private static string BuildReport(
            string candidatePath,
            string releaseTarget,
            string auditCommand,
            string readiness,
            bool ready,
            string sha,
            IList<string> failures,
            IList<string> notes)
        {
            var sb = new StringBuilder();
            sb.AppendLine("CityLBM Case E Post-run Audit Handoff");
            sb.AppendLine();
            sb.AppendLine("case: AIJ Case E");
            sb.AppendLine("condition: ac");
            sb.AppendLine("wind_direction: N");
            sb.AppendLine("formal_height_m: 2");
            sb.AppendLine("formal_sampling_mode: raw_trilinear");
            sb.AppendLine("required_probe_count: 80");
            sb.AppendLine("release_target: " + releaseTarget);
            sb.AppendLine("candidate_csv: " + (string.IsNullOrWhiteSpace(candidatePath) ? "<not supplied>" : candidatePath));
            sb.AppendLine("candidate_sha256: " + sha);
            sb.AppendLine("claim_readiness: " + readiness);
            sb.AppendLine("ready_for_official_audit: " + ready.ToString(CultureInfo.InvariantCulture).ToLowerInvariant());
            sb.AppendLine("formal_result_allowed_now: false");
            sb.AppendLine();
            sb.AppendLine("audit_command:");
            sb.AppendLine(auditCommand);
            sb.AppendLine();
            sb.AppendLine("checks:");
            if (failures.Count == 0)
            {
                sb.AppendLine("- structural candidate gate passed");
            }
            else
            {
                foreach (string failure in failures)
                {
                    sb.AppendLine("- FAIL: " + failure);
                }
            }

            foreach (string note in notes)
            {
                sb.AppendLine("- NOTE: " + note);
            }

            sb.AppendLine();
            sb.AppendLine("boundary: This component is protocol-control evidence only. It does not compute R2, does not run CFD, does not improve official AIJ Case E z=2 m metrics, and does not permit formal v0.4.0.");
            return sb.ToString();
        }

        private static string[] SplitCsvLine(string line)
        {
            return line.Split(',').Select(cell => cell.Trim().Trim('"')).ToArray();
        }

        private static int IndexOf(string[] headers, string name)
        {
            for (int i = 0; i < headers.Length; i++)
            {
                if (string.Equals(headers[i], name, StringComparison.OrdinalIgnoreCase))
                {
                    return i;
                }
            }

            return -1;
        }

        private static string ReadSidecarText(string directory, string pattern)
        {
            var sb = new StringBuilder();
            foreach (string file in Directory.GetFiles(directory, pattern).OrderBy(x => x))
            {
                try
                {
                    sb.AppendLine(File.ReadAllText(file));
                }
                catch (IOException)
                {
                }
                catch (UnauthorizedAccessException)
                {
                }
            }

            return sb.ToString();
        }

        private static void RequireRegex(string text, string pattern, string message, IList<string> failures)
        {
            if (!Regex.IsMatch(text, pattern, RegexOptions.IgnoreCase))
            {
                failures.Add(message);
            }
        }

        private static int ExtractInt(string text, string pattern)
        {
            Match match = Regex.Match(text, pattern, RegexOptions.IgnoreCase);
            if (!match.Success)
            {
                return 0;
            }

            for (int i = 1; i < match.Groups.Count; i++)
            {
                if (int.TryParse(match.Groups[i].Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out int value))
                {
                    return value;
                }
            }

            return 0;
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

        protected override Bitmap Icon
        {
            get { return null!; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("19B94D68-EB71-41C0-B4AB-35DAFECE4079"); }
        }

        private sealed class CandidateAudit
        {
            public string AuditCommand { get; private set; } = "";
            public string ClaimReadiness { get; private set; } = "";
            public bool ReadyForOfficialAudit { get; private set; }
            public string CandidateSha256 { get; private set; } = "";
            public string Report { get; private set; } = "";

            public static CandidateAudit Create(string command, string readiness, bool ready, string sha, string report)
            {
                return new CandidateAudit
                {
                    AuditCommand = command,
                    ClaimReadiness = readiness,
                    ReadyForOfficialAudit = ready,
                    CandidateSha256 = sha,
                    Report = report,
                };
            }
        }

        private sealed class CsvCheck
        {
            public CsvCheck(bool passed, List<string> failures, List<string> notes)
            {
                Passed = passed;
                Failures = failures;
                Notes = notes;
            }

            public bool Passed { get; private set; }
            public List<string> Failures { get; private set; }
            public List<string> Notes { get; private set; }
        }

        private sealed class ProtocolCheck
        {
            public ProtocolCheck(bool passed, List<string> failures, List<string> notes)
            {
                Passed = passed;
                Failures = failures;
                Notes = notes;
            }

            public bool Passed { get; private set; }
            public List<string> Failures { get; private set; }
            public List<string> Notes { get; private set; }
        }
    }
}
