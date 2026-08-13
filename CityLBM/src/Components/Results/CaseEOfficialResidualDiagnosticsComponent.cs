using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Produces residual diagnostics for official AIJ Case E probe CSVs.
    /// </summary>
    public class CaseEOfficialResidualDiagnosticsComponent : GH_Component
    {
        private const int RequiredProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const string RequiredCase = "ac";
        private const string RequiredWindDirection = "N";
        private const string RequiredSamplingMode = "raw_trilinear";

        public CaseEOfficialResidualDiagnosticsComponent()
            : base(
                "Case E Official Residual Diagnostics",
                "CaseE Residuals",
                "Summarizes official AIJ Case E z=2 m probe residuals, top-error probes, and observed-speed groups from a completed probe CSV.",
                "CityLBM",
                "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter(
                "Probe CSV",
                "CSV",
                "Path to a completed official Case E probe CSV with No., official_velocity_ratio, and predicted_velocity_ratio columns.",
                GH_ParamAccess.item,
                "");
            pManager.AddIntegerParameter(
                "Top Count",
                "Top",
                "Number of highest absolute-residual probes to report.",
                GH_ParamAccess.item,
                10);
            pManager.AddTextParameter(
                "Sampling Mode",
                "Mode",
                "Formal mode must be raw_trilinear. Diagnostic modes are reported as non-formal.",
                GH_ParamAccess.item,
                RequiredSamplingMode);
            pManager.AddNumberParameter(
                "Validation Height m",
                "z",
                "Formal AIJ Case E validation height must be 2.0 m.",
                GH_ParamAccess.item,
                OfficialHeightM);
            pManager.AddTextParameter(
                "Case",
                "Case",
                "Formal AIJ Case E condition must be ac.",
                GH_ParamAccess.item,
                RequiredCase);
            pManager.AddTextParameter(
                "Wind Direction",
                "Dir",
                "Formal AIJ Case E wind direction must be N.",
                GH_ParamAccess.item,
                RequiredWindDirection);

            for (int i = 0; i < 6; i++)
            {
                pManager[i].Optional = true;
            }
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready residual diagnostic report and claim boundary.", GH_ParamAccess.item);
            pManager.AddTextParameter("Top Residual Rows", "TopRows", "Highest absolute-residual probe rows.", GH_ParamAccess.list);
            pManager.AddTextParameter("Group Rows", "Groups", "Observed-speed group residual summaries.", GH_ParamAccess.list);
            pManager.AddTextParameter("Risk Rows", "Risk", "Protocol and interpretation risks.", GH_ParamAccess.list);
            pManager.AddBooleanParameter("Formal Diagnostic Ready", "Ready", "True only when the CSV and protocol fields match the official diagnostic path.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Claim", "Claim readiness classification for this residual diagnostic.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string csvPath = "";
            int topCount = 10;
            string samplingMode = RequiredSamplingMode;
            double validationHeight = OfficialHeightM;
            string caseName = RequiredCase;
            string windDirection = RequiredWindDirection;
            DA.GetData(0, ref csvPath);
            DA.GetData(1, ref topCount);
            DA.GetData(2, ref samplingMode);
            DA.GetData(3, ref validationHeight);
            DA.GetData(4, ref caseName);
            DA.GetData(5, ref windDirection);

            ResidualAudit audit = BuildAudit(csvPath, topCount, samplingMode, validationHeight, caseName, windDirection);
            DA.SetData(0, audit.Report);
            DA.SetDataList(1, audit.TopRows);
            DA.SetDataList(2, audit.GroupRows);
            DA.SetDataList(3, audit.RiskRows);
            DA.SetData(4, audit.FormalDiagnosticReady);
            DA.SetData(5, audit.ClaimReadiness);
        }

        private static ResidualAudit BuildAudit(string csvPath, int topCount, string samplingMode, double validationHeight, string caseName, string windDirection)
        {
            string trimmedPath = (csvPath ?? "").Trim().Trim('"');
            string mode = string.IsNullOrWhiteSpace(samplingMode) ? RequiredSamplingMode : samplingMode.Trim();
            string caseValue = string.IsNullOrWhiteSpace(caseName) ? RequiredCase : caseName.Trim();
            string directionValue = string.IsNullOrWhiteSpace(windDirection) ? RequiredWindDirection : windDirection.Trim();
            int safeTopCount = Math.Max(1, Math.Min(topCount, RequiredProbeCount));
            var failures = new List<string>();
            var rows = new List<ProbeResidual>();

            bool officialCase = string.Equals(caseValue, RequiredCase, StringComparison.OrdinalIgnoreCase);
            bool officialWindDirection = string.Equals(directionValue, RequiredWindDirection, StringComparison.OrdinalIgnoreCase);
            bool officialHeight = Math.Abs(validationHeight - OfficialHeightM) < 1e-9;
            bool officialSampling = string.Equals(mode, RequiredSamplingMode, StringComparison.OrdinalIgnoreCase);

            if (string.IsNullOrWhiteSpace(trimmedPath))
            {
                failures.Add("No probe CSV supplied.");
            }
            else
            {
                string fullPath = Path.GetFullPath(trimmedPath);
                if (!File.Exists(fullPath))
                {
                    failures.Add("Probe CSV does not exist.");
                    trimmedPath = fullPath;
                }
                else
                {
                    trimmedPath = fullPath;
                    rows = ReadRows(fullPath, failures);
                }
            }

            if (rows.Count != RequiredProbeCount)
            {
                failures.Add("Expected 80 official ac+N probe rows; found " + rows.Count.ToString(CultureInfo.InvariantCulture) + ".");
            }

            bool idsOneToEighty = rows.Count == RequiredProbeCount && Enumerable.Range(1, RequiredProbeCount).All(id => rows.Any(row => row.Id == id));
            if (rows.Count > 0 && !idsOneToEighty)
            {
                failures.Add("Probe IDs must be exactly 1..80 for the official Case E probe set.");
            }

            bool formalReady = failures.Count == 0 && officialCase && officialWindDirection && officialHeight && officialSampling && idsOneToEighty;
            string readiness = formalReady ? "limitations_ready_residual_diagnostic" : "blocked_protocol_or_csv";
            var topRows = BuildTopRows(rows, safeTopCount);
            var groupRows = BuildGroupRows(rows);
            var riskRows = BuildRiskRows(failures, officialCase, officialWindDirection, officialHeight, officialSampling, idsOneToEighty);
            string report = BuildReport(trimmedPath, caseValue, directionValue, validationHeight, mode, topRows, groupRows, riskRows, formalReady, readiness);
            return new ResidualAudit(report, topRows, groupRows, riskRows, formalReady, readiness);
        }

        private static List<ProbeResidual> ReadRows(string path, IList<string> failures)
        {
            string[] lines = File.ReadAllLines(path);
            var rows = new List<ProbeResidual>();
            if (lines.Length < 2)
            {
                failures.Add("Probe CSV has no data rows.");
                return rows;
            }

            string[] headers = SplitCsvLine(lines[0]);
            int idIndex = IndexOf(headers, "No.");
            int observedIndex = IndexOf(headers, "official_velocity_ratio");
            int predictedIndex = IndexOf(headers, "predicted_velocity_ratio");
            if (observedIndex < 0)
            {
                observedIndex = IndexOf(headers, "observed_velocity_ratio");
            }

            if (predictedIndex < 0)
            {
                predictedIndex = IndexOf(headers, "simulated_velocity_ratio");
            }

            if (idIndex < 0) failures.Add("Missing required column: No.");
            if (observedIndex < 0) failures.Add("Missing required column: official_velocity_ratio.");
            if (predictedIndex < 0) failures.Add("Missing required column: predicted_velocity_ratio.");
            if (failures.Count > 0)
            {
                return rows;
            }

            int maxIndex = Math.Max(idIndex, Math.Max(observedIndex, predictedIndex));
            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i]))
                {
                    continue;
                }

                string[] cells = SplitCsvLine(lines[i]);
                if (cells.Length <= maxIndex)
                {
                    failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has too few columns.");
                    continue;
                }

                bool idOk = int.TryParse(cells[idIndex], NumberStyles.Integer, CultureInfo.InvariantCulture, out int id);
                bool observedOk = double.TryParse(cells[observedIndex], NumberStyles.Float, CultureInfo.InvariantCulture, out double observed);
                bool predictedOk = double.TryParse(cells[predictedIndex], NumberStyles.Float, CultureInfo.InvariantCulture, out double predicted);
                if (!idOk) failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-integer No. value.");
                if (!observedOk) failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-numeric official velocity ratio.");
                if (!predictedOk) failures.Add("Row " + (i + 1).ToString(CultureInfo.InvariantCulture) + " has a non-numeric predicted velocity ratio.");

                if (idOk && observedOk && predictedOk)
                {
                    rows.Add(new ProbeResidual(id, observed, predicted));
                }
            }

            return rows;
        }

        private static List<string> BuildTopRows(IList<ProbeResidual> rows, int topCount)
        {
            return rows
                .OrderByDescending(row => row.AbsResidualPp)
                .ThenBy(row => row.Id)
                .Take(topCount)
                .Select(row => string.Format(
                    CultureInfo.InvariantCulture,
                    "No={0}; official={1:0.######}; predicted={2:0.######}; residual_pp={3:0.######}; abs_residual_pp={4:0.######}; sign={5}",
                    row.Id,
                    row.Observed,
                    row.Predicted,
                    row.ResidualPp,
                    row.AbsResidualPp,
                    row.ResidualPp >= 0.0 ? "over" : "under"))
                .ToList();
        }

        private static List<string> BuildGroupRows(IList<ProbeResidual> rows)
        {
            if (rows.Count == 0)
            {
                return new List<string> { "group=none; n=0" };
            }

            double q33 = Quantile(rows.Select(row => row.Observed).OrderBy(value => value).ToList(), 1.0 / 3.0);
            double q67 = Quantile(rows.Select(row => row.Observed).OrderBy(value => value).ToList(), 2.0 / 3.0);
            var groups = new Dictionary<string, List<ProbeResidual>>
            {
                { "low_official_speed", rows.Where(row => row.Observed <= q33).ToList() },
                { "mid_official_speed", rows.Where(row => row.Observed > q33 && row.Observed <= q67).ToList() },
                { "high_official_speed", rows.Where(row => row.Observed > q67).ToList() },
            };

            var output = new List<string>();
            foreach (var item in groups)
            {
                List<ProbeResidual> group = item.Value;
                if (group.Count == 0)
                {
                    output.Add("group=" + item.Key + "; n=0");
                    continue;
                }

                double mae = group.Select(row => row.AbsResidualPp).Average();
                double bias = group.Select(row => row.ResidualPp).Average();
                double underFraction = group.Count(row => row.ResidualPp < 0.0) / (double)group.Count;
                output.Add(string.Format(
                    CultureInfo.InvariantCulture,
                    "group={0}; n={1}; official_min={2:0.######}; official_max={3:0.######}; mae_pp={4:0.######}; bias_pp={5:0.######}; under_fraction={6:0.######}",
                    item.Key,
                    group.Count,
                    group.Min(row => row.Observed),
                    group.Max(row => row.Observed),
                    mae,
                    bias,
                    underFraction));
            }

            return output;
        }

        private static List<string> BuildRiskRows(IList<string> failures, bool officialCase, bool officialWindDirection, bool officialHeight, bool officialSampling, bool idsOneToEighty)
        {
            var risks = new List<string>
            {
                "formal_accuracy_claim_supported=false",
                "formal_release_allowed=false",
                "residual_diagnostics_do_not_improve_metrics=true",
                "diagnostic_sampling_not_formal=true",
                "posthoc_calibration_not_validation=true",
                "official_case_check=" + officialCase.ToString().ToLowerInvariant(),
                "wind_direction_check=" + officialWindDirection.ToString().ToLowerInvariant(),
                "height_2m_check=" + officialHeight.ToString().ToLowerInvariant(),
                "sampling_raw_trilinear_check=" + officialSampling.ToString().ToLowerInvariant(),
                "probe_id_check=" + idsOneToEighty.ToString().ToLowerInvariant(),
            };
            foreach (string failure in failures.Distinct())
            {
                risks.Add("failure=" + failure);
            }

            return risks;
        }

        private static string BuildReport(
            string path,
            string caseName,
            string windDirection,
            double validationHeight,
            string samplingMode,
            IEnumerable<string> topRows,
            IEnumerable<string> groupRows,
            IEnumerable<string> riskRows,
            bool formalReady,
            string readiness)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Official Residual Diagnostics");
            sb.AppendLine();
            sb.AppendLine("probe_csv: " + (string.IsNullOrWhiteSpace(path) ? "<not supplied>" : path));
            sb.AppendLine("case: " + caseName);
            sb.AppendLine("wind_direction: " + windDirection);
            sb.AppendLine("validation_height_m: " + validationHeight.ToString("0.########", CultureInfo.InvariantCulture));
            sb.AppendLine("sampling_mode: " + samplingMode);
            sb.AppendLine("formal_diagnostic_ready: " + formalReady.ToString().ToLowerInvariant());
            sb.AppendLine("claim_readiness: " + readiness);
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine();
            AppendList(sb, "top_residual_rows", topRows);
            AppendList(sb, "group_rows", groupRows);
            AppendList(sb, "risk_rows", riskRows);
            sb.AppendLine("boundary: This component summarizes residual structure from a supplied CSV only. It does not run FluidX3D, improve official z=2 m metrics, prove Rhino loaded the plugin, support post-hoc calibration as validation, or permit formal v0.4.0.");
            return sb.ToString();
        }

        private static double Quantile(IList<double> sortedValues, double probability)
        {
            if (sortedValues.Count == 0)
            {
                return double.NaN;
            }

            if (sortedValues.Count == 1)
            {
                return sortedValues[0];
            }

            double position = (sortedValues.Count - 1) * probability;
            int lower = (int)Math.Floor(position);
            int upper = (int)Math.Ceiling(position);
            if (lower == upper)
            {
                return sortedValues[lower];
            }

            double fraction = position - lower;
            return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * fraction;
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

        protected override Bitmap Icon
        {
            get { return null!; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("9BAEAB1F-6F24-4679-B940-D4E97DE0D54B"); }
        }

        private sealed class ProbeResidual
        {
            public ProbeResidual(int id, double observed, double predicted)
            {
                Id = id;
                Observed = observed;
                Predicted = predicted;
            }

            public int Id { get; private set; }
            public double Observed { get; private set; }
            public double Predicted { get; private set; }
            public double ResidualPp { get { return (Predicted - Observed) * 100.0; } }
            public double AbsResidualPp { get { return Math.Abs(ResidualPp); } }
        }

        private sealed class ResidualAudit
        {
            public ResidualAudit(string report, List<string> topRows, List<string> groupRows, List<string> riskRows, bool formalReady, string readiness)
            {
                Report = report;
                TopRows = topRows;
                GroupRows = groupRows;
                RiskRows = riskRows;
                FormalDiagnosticReady = formalReady;
                ClaimReadiness = readiness;
            }

            public string Report { get; private set; }
            public List<string> TopRows { get; private set; }
            public List<string> GroupRows { get; private set; }
            public List<string> RiskRows { get; private set; }
            public bool FormalDiagnosticReady { get; private set; }
            public string ClaimReadiness { get; private set; }
        }
    }
}
