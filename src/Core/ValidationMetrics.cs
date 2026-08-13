using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;
using CityLBM.Solver;

namespace CityLBM.Core
{
    public class ValidationMetricsResult
    {
        public int ValidCount { get; set; }
        public int FailedCount { get; set; }
        public double MAE { get; set; } = double.NaN;
        public double RMSE { get; set; } = double.NaN;
        public double Bias { get; set; } = double.NaN;
        public double BiasRatio { get; set; } = double.NaN;
        public double R2 { get; set; } = double.NaN;
        public double RegressionSlope { get; set; } = double.NaN;
        public double RegressionIntercept { get; set; } = double.NaN;
    }

    public static class ValidationMetrics
    {
        public static ValidationMetricsResult Compute(IList<double> simulated, IList<double> observed)
        {
            if (simulated == null) throw new ArgumentNullException(nameof(simulated));
            if (observed == null) throw new ArgumentNullException(nameof(observed));

            int n = Math.Min(simulated.Count, observed.Count);
            var pairs = new List<Tuple<double, double>>(n);
            int failed = Math.Abs(simulated.Count - observed.Count);

            for (int i = 0; i < n; i++)
            {
                double s = simulated[i];
                double o = observed[i];
                if (IsFinite(s) && IsFinite(o))
                    pairs.Add(Tuple.Create(s, o));
                else
                    failed++;
            }

            var result = new ValidationMetricsResult
            {
                ValidCount = pairs.Count,
                FailedCount = failed
            };

            if (pairs.Count == 0)
                return result;

            double sumAbs = 0.0;
            double sumSq = 0.0;
            double sumErr = 0.0;
            double sumObs = 0.0;
            double sumSim = 0.0;

            foreach (var pair in pairs)
            {
                double err = pair.Item1 - pair.Item2;
                sumAbs += Math.Abs(err);
                sumSq += err * err;
                sumErr += err;
                sumSim += pair.Item1;
                sumObs += pair.Item2;
            }

            double meanObs = sumObs / pairs.Count;
            double meanSim = sumSim / pairs.Count;
            result.MAE = sumAbs / pairs.Count;
            result.RMSE = Math.Sqrt(sumSq / pairs.Count);
            result.Bias = sumErr / pairs.Count;
            result.BiasRatio = Math.Abs(meanObs) > 1.0e-12 ? result.Bias / meanObs : double.NaN;

            double ssTot = 0.0;
            double ssRes = 0.0;
            double cov = 0.0;
            double varObs = 0.0;
            foreach (var pair in pairs)
            {
                double s = pair.Item1;
                double o = pair.Item2;
                ssTot += (o - meanObs) * (o - meanObs);
                ssRes += (s - o) * (s - o);
                cov += (o - meanObs) * (s - meanSim);
                varObs += (o - meanObs) * (o - meanObs);
            }

            result.R2 = ssTot > 1.0e-12 ? 1.0 - ssRes / ssTot : double.NaN;
            result.RegressionSlope = varObs > 1.0e-12 ? cov / varObs : double.NaN;
            result.RegressionIntercept = IsFinite(result.RegressionSlope)
                ? meanSim - result.RegressionSlope * meanObs
                : double.NaN;

            return result;
        }

        public static VTKResult AverageVelocityResults(IList<VTKResult> results)
        {
            if (results == null || results.Count == 0)
                return null;

            var first = results[0];
            if (first.Points == null || first.Velocities == null)
                return null;

            int n = first.Points.Count;
            if (n == 0 || first.Velocities.Count != n)
                return null;

            var sum = new Vector3d[n];
            var speedSums = new double[n];
            var speedSqSums = new double[n];
            int validFrames = 0;

            foreach (var result in results)
            {
                if (result == null || result.Points == null || result.Velocities == null)
                    continue;
                if (result.Points.Count != n || result.Velocities.Count != n)
                    return null;

                for (int i = 0; i < n; i++)
                {
                    sum[i] += result.Velocities[i];
                    double speed = result.Velocities[i].Length;
                    speedSums[i] += speed;
                    speedSqSums[i] += speed * speed;
                }
                validFrames++;
            }

            if (validFrames == 0)
                return null;

            var averagedVelocities = sum.Select(v => v / validFrames).ToList();
            double meanSpeed = averagedVelocities.Count > 0
                ? averagedVelocities.Average(v => v.Length)
                : double.NaN;
            double meanSpeedStdDev = double.NaN;
            double maxSpeedStdDev = double.NaN;
            if (validFrames > 1 && n > 0)
            {
                double stdSum = 0.0;
                double stdMax = 0.0;
                for (int i = 0; i < n; i++)
                {
                    double mean = speedSums[i] / validFrames;
                    double variance = Math.Max(0.0, speedSqSums[i] / validFrames - mean * mean);
                    double std = Math.Sqrt(variance);
                    stdSum += std;
                    if (std > stdMax) stdMax = std;
                }
                meanSpeedStdDev = stdSum / n;
                maxSpeedStdDev = stdMax;
            }

            return new VTKResult
            {
                FilePath = first.FilePath,
                TimeStep = results.Max(r => r.TimeStep),
                RawPointCount = first.RawPointCount,
                Points = new List<Point3d>(first.Points),
                Velocities = averagedVelocities,
                Scalars = new Dictionary<string, List<double>>(),
                AveragedFrameCount = validFrames,
                MeanSpeed = meanSpeed,
                MeanSpeedStdDev = meanSpeedStdDev,
                MaxSpeedStdDev = maxSpeedStdDev,
                MeanSpeedStdDevRatio = IsFinite(meanSpeed) && IsFinite(meanSpeedStdDev) && Math.Abs(meanSpeed) > 1.0e-12
                    ? meanSpeedStdDev / meanSpeed
                    : double.NaN,
                MaxSpeedStdDevRatio = IsFinite(meanSpeed) && IsFinite(maxSpeedStdDev) && Math.Abs(meanSpeed) > 1.0e-12
                    ? maxSpeedStdDev / meanSpeed
                    : double.NaN,
                SourceTimeSteps = results
                    .Where(r => r != null)
                    .Select(r => r.TimeStep)
                    .OrderBy(t => t)
                    .ToList()
            };
        }

        private static bool IsFinite(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }
    }
}
