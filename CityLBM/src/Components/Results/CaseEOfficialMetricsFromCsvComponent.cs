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
    /// Computes official AIJ Case E z=2 m metrics from a completed probe CSV.
    /// </summary>
    public class CaseEOfficialMetricsFromCsvComponent : GH_Component
    {
        private const int RequiredProbeCount = 80;
        private const double OfficialHeightM = 2.0;
        private const double MaeThresholdPp = 15.0;
        private const double R2Threshold = 0.0;
        private const double PearsonThreshold = 0.0;
        private const string RequiredCase = "ac";
        private const string RequiredWindDirection = "N";
        private const string RequiredSamplingMode = "raw_trilinear";

        public CaseEOfficialMetricsFromCsvComponent()
            : base(
                "Case E Official Metrics From CSV",
                "CaseE CSV Metrics",
                "Computes AIJ Case E official z=2 m MAE/RMSE/bias/R2/Pearson from a probe CSV and keeps formal release blocked unless the metric gate passes.",
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

            pManager[0].Optional = true;
            pManager[1].Optional = true;
            pManager[2].Optional = true;
            pManager[3].Optional = true;
            pManager[4].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R", "Panel-ready metric report and claim boundary.", GH_ParamAccess.item);
            pManager.AddTextParameter("Metric Rows", "M", "Computed metric rows.", GH_ParamAccess.list);
            pManager.AddTextParameter("Gate Checks", "Checks", "Official protocol and metric pass/fail checks.", GH_ParamAccess.list);
            pManager.AddBooleanParameter("Official Metric Gate", "Gate", "True only when official z=2 m MAE/R2/Pearson checks pass.", GH_ParamAccess.item);
            pManager.AddBooleanParameter("Formal Release Allowed", "Formal", "Always false here; formal release also requires release_gate.json, Case A, Rhino load, and trace evidence.", GH_ParamAccess.item);
            pManager.AddTextParameter("Claim Readiness", "Ready", "Claim readiness classification for this CSV.", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string csvPath = "";
            string samplingMode = RequiredSamplingMode;
            double validationHeight = OfficialHeightM;
            string caseName = RequiredCase;
            string windDirection = RequiredWindDirection;
            DA.GetData(0, ref csvPath);
            DA.GetData(1, ref samplingMode);
            DA.GetData(2, ref validationHeight);
            DA.GetData(3, ref caseName);
            DA.GetData(4, ref windDirection);

            MetricAudit audit = ComputeAudit(csvPath, samplingMode, validationHeight, caseName, windDirection);
            DA.SetData(0, audit.Report);
            DA.SetDataList(1, audit.MetricRows);
            DA.SetDataList(2, audit.GateChecks);
            DA.SetData(3, audit.OfficialMetricGate);
            DA.SetData(4, false);
            DA.SetData(5, audit.ClaimReadiness);
        }

        private static MetricAudit ComputeAudit(string csvPath, string samplingMode, double validationHeight, string caseName, string windDirection)
        {
            string trimmedPath = (csvPath ?? "").Trim().Trim('"');
            string mode = string.IsNullOrWhiteSpace(samplingMode) ? RequiredSamplingMode : samplingMode.Trim();
            string caseValue = string.IsNullOrWhiteSpace(caseName) ? RequiredCase : caseName.Trim();
            string directionValue = string.IsNullOrWhiteSpace(windDirection) ? RequiredWindDirection : windDirection.Trim();
            var failures = new List<string>();
            var rows = new List<ProbeRow>();

            bool officialCase = string.Equals(caseValue, RequiredCase, StringComparison.OrdinalIgnoreCase);
            bool officialWindDirection = string.Equals(directionValue, RequiredWindDirection, StringComparison.OrdinalIgnoreCase);
            bool officialHeight = Math.Abs(validationHeight - OfficialHeightM) < 1e-9;
            bool officialSampling = string.Equals(mode, RequiredSamplingMode, StringComparison.OrdinalIgnoreCase);

            if (string.IsNullOrWhiteSpace(trimmedPath))
            {
                failures.Add("No probe CSV supplied.");
                return BuildAudit("", mode, validationHeight, caseValue, directionValue, officialCase, officialWindDirection, officialHeight, officialSampling, failures, rows);
            }

            string fullPath = Path.GetFullPath(trimmedPath);
            if (!File.Exists(fullPath))
            {
                failures.Add("Probe CSV does not exist.");
                return BuildAudit(fullPath, mode, validationHeight, caseValue, directionValue, officialCase, officialWindDirection, officialHeight, officialSampling, failures, rows);
            }

            try
            {
                rows = ReadProbeRows(fullPath, failures);
            }
            catch (IOException ex)
            {
                failures.Add("Probe CSV could not be read: " + ex.Message);
            }
            catch (UnauthorizedAccessException ex)
            {
                failures.Add("Probe CSV could not be read: " + ex.Message);
            }

            return BuildAudit(fullPath, mode, validationHeight, caseValue, directionValue, officialCase, officialWindDirection, officialHeight, officialSampling, failures, rows);
        }

        private static MetricAudit BuildAudit(
            string path,
            string samplingMode,
            double validationHeight,
            string caseName,
            string windDirection,
            bool officialCase,
            bool officialWindDirection,
            bool officialHeight,
            bool officialSampling,
            IList<string> failures,
            IList<ProbeRow> rows)
        {
            if (rows.Count != RequiredProbeCount)
            {
                failures.Add("Expected 80 official ac+N probe rows; found " + rows.Count.ToString(CultureInfo.InvariantCulture) + ".");
            }

            bool idsOneToEighty = rows.Count == RequiredProbeCount && Enumerable.Range(1, RequiredProbeCount).All(id => rows.Any(row => row.Id == id));
            if (rows.Count > 0 && !idsOneToEighty)
            {
                failures.Add("Probe IDs must be exactly 1..80 for the official Case E probe set.");
            }

            MetricValues metrics = rows.Count > 0 ? MetricValues.FromRows(rows) : MetricValues.Empty();
            bool maePass = rows.Count > 0 && metrics.MaePp < MaeThresholdPp;
            bool r2Pass = rows.Count > 0 && metrics.R2 > R2Threshold;
            bool pearsonPass = rows.Count > 0 && metrics.Pearson > PearsonThreshold;
            bool protocolPass = failures.Count == 0 && officialCase && officialWindDirection && officialHeight && officialSampling;
            bool gate = protocolPass && maePass && r2Pass && pearsonPass;

            var metricRows = new List<string>
            {
                "case=" + caseName + "; wind_direction=" + windDirection + "; height_m=" + validationHeight.ToString("0.########", CultureInfo.InvariantCulture) + "; sampling_mode=" + samplingMode,
                "n=" + rows.Count.ToString(CultureInfo.InvariantCulture),
                "MAE_pp=" + metrics.MaePp.ToString("0.############", CultureInfo.InvariantCulture),
                "RMSE_pp=" + metrics.RmsePp.ToString("0.############", CultureInfo.InvariantCulture),
                "bias_pp=" + metrics.BiasPp.ToString("0.############", CultureInfo.InvariantCulture),
                "R2=" + metrics.R2.ToString("0.############", CultureInfo.InvariantCulture),
                "Pearson=" + metrics.Pearson.ToString("0.############", CultureInfo.InvariantCulture)
            };

            var checks = new List<string>
            {
                "official_case_check=" + officialCase.ToString().ToLowerInvariant(),
                "wind_direction_check=" + officialWindDirection.ToString().ToLowerInvariant(),
                "height_2m_check=" + officialHeight.ToString().ToLowerInvariant(),
                "sampling_raw_trilinear_check=" + officialSampling.ToString().ToLowerInvariant(),
                "probe_count_check=" + (rows.Count == RequiredProbeCount).ToString().ToLowerInvariant(),
                "probe_id_check=" + idsOneToEighty.ToString().ToLowerInvariant(),
                "mae_check=" + maePass.ToString().ToLowerInvariant(),
                "r2_check=" + r2Pass.ToString().ToLowerInvariant(),
                "pearson_check=" + pearsonPass.ToString().ToLowerInvariant(),
                "official_z2m_metric_gate=" + gate.ToString().ToLowerInvariant(),
                "formal_release_allowed=false"
            };

            foreach (string failure in failures.Distinct())
            {
                checks.Add("failure=" + failure);
            }

            string readiness;
            if (gate)
            {
                readiness = "metric_gate_passed_release_gate_still_required";
            }
            else if (protocolPass)
            {
                readiness = "limitations_ready_negative_validation";
            }
            else
            {
                readiness = "blocked_protocol_or_csv";
            }

            string report = BuildReport(path, samplingMode, validationHeight, caseName, windDirection, metricRows, checks, readiness);
            return new MetricAudit(report, metricRows, checks, gate, readiness);
        }

        private static List<ProbeRow> ReadProbeRows(string path, IList<string> failures)
        {
            string[] lines = File.ReadAllLines(path);
            var rows = new List<ProbeRow>();
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
                    rows.Add(new ProbeRow(id, observed, predicted));
                }
            }

            return rows;
        }

        private static string BuildReport(
            string path,
            string samplingMode,
            double validationHeight,
            string caseName,
            string windDirection,
            IEnumerable<string> metricRows,
            IEnumerable<string> checks,
            string readiness)
        {
            var sb = new StringBuilder();
            sb.AppendLine("AIJ Case E Official Metrics From CSV");
            sb.AppendLine();
            sb.AppendLine("probe_csv: " + (string.IsNullOrWhiteSpace(path) ? "<not supplied>" : path));
            sb.AppendLine("case: " + caseName);
            sb.AppendLine("wind_direction: " + windDirection);
            sb.AppendLine("validation_height_m: " + validationHeight.ToString("0.########", CultureInfo.InvariantCulture));
            sb.AppendLine("sampling_mode: " + samplingMode);
            sb.AppendLine("claim_readiness: " + readiness);
            sb.AppendLine("formal_release_allowed: false");
            sb.AppendLine();
            AppendList(sb, "metric_rows", metricRows);
            AppendList(sb, "gate_checks", checks);
            sb.AppendLine("thresholds:");
            sb.AppendLine("- MAE threshold: < 15.0 pp");
            sb.AppendLine("- R2 threshold: > 0.0");
            sb.AppendLine("- Pearson threshold: > 0.0");
            sb.AppendLine();
            sb.AppendLine("boundary: This component computes metrics from a supplied CSV only. Formal v0.4.0 also requires completed solver logs, release_gate.json, Case A regression, Rhino new-GHA load evidence, and full artifact traceability. Diagnostic z offsets, z_plus_half, calibration, or non-raw_trilinear sampling cannot be used as official validation.");
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
            get { return new Guid("6189C8B7-3E79-4C0B-BC1D-4E85D7E90493"); }
        }

        private sealed class ProbeRow
        {
            public ProbeRow(int id, double observed, double predicted)
            {
                Id = id;
                Observed = observed;
                Predicted = predicted;
            }

            public int Id { get; private set; }
            public double Observed { get; private set; }
            public double Predicted { get; private set; }
        }

        private sealed class MetricValues
        {
            public double MaePp { get; private set; }
            public double RmsePp { get; private set; }
            public double BiasPp { get; private set; }
            public double R2 { get; private set; }
            public double Pearson { get; private set; }

            public static MetricValues Empty()
            {
                return new MetricValues
                {
                    MaePp = double.NaN,
                    RmsePp = double.NaN,
                    BiasPp = double.NaN,
                    R2 = double.NaN,
                    Pearson = double.NaN,
                };
            }

            public static MetricValues FromRows(IList<ProbeRow> rows)
            {
                double[] residuals = rows.Select(row => row.Predicted - row.Observed).ToArray();
                double mae = residuals.Select(Math.Abs).Average();
                double rmse = Math.Sqrt(residuals.Select(value => value * value).Average());
                double bias = residuals.Average();
                double observedMean = rows.Select(row => row.Observed).Average();
                double ssRes = rows.Select(row => Math.Pow(row.Predicted - row.Observed, 2.0)).Sum();
                double ssTot = rows.Select(row => Math.Pow(row.Observed - observedMean, 2.0)).Sum();
                double r2 = ssTot > 0.0 ? 1.0 - ssRes / ssTot : double.NaN;
                double pearson = ComputePearson(rows);

                return new MetricValues
                {
                    MaePp = mae * 100.0,
                    RmsePp = rmse * 100.0,
                    BiasPp = bias * 100.0,
                    R2 = r2,
                    Pearson = pearson,
                };
            }

            private static double ComputePearson(IList<ProbeRow> rows)
            {
                double observedMean = rows.Select(row => row.Observed).Average();
                double predictedMean = rows.Select(row => row.Predicted).Average();
                double covariance = rows.Select(row => (row.Observed - observedMean) * (row.Predicted - predictedMean)).Sum();
                double observedVariance = rows.Select(row => Math.Pow(row.Observed - observedMean, 2.0)).Sum();
                double predictedVariance = rows.Select(row => Math.Pow(row.Predicted - predictedMean, 2.0)).Sum();
                double denominator = Math.Sqrt(observedVariance * predictedVariance);
                return denominator > 0.0 ? covariance / denominator : double.NaN;
            }
        }

        private sealed class MetricAudit
        {
            public MetricAudit(string report, List<string> metricRows, List<string> gateChecks, bool gate, string readiness)
            {
                Report = report;
                MetricRows = metricRows;
                GateChecks = gateChecks;
                OfficialMetricGate = gate;
                ClaimReadiness = readiness;
            }

            public string Report { get; private set; }
            public List<string> MetricRows { get; private set; }
            public List<string> GateChecks { get; private set; }
            public bool OfficialMetricGate { get; private set; }
            public string ClaimReadiness { get; private set; }
        }
    }
}
