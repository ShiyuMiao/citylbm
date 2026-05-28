using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// RK4 流线追踪器 - 支持自适应步长
    /// 风速大的地方流线更长，风速小的地方自动缩短
    /// </summary>
    public static class StreamlineTracer
    {
        /// <summary>
        /// 自适应流线追踪 - 风速大的地方步长更大，流线更长
        /// </summary>
        public static List<Polyline> TraceAdaptive(
            IList<Point3d> seeds,
            IList<Point3d> points,
            IList<Vector3d> velocities,
            double baseStepSize,
            int maxSteps,
            BoundingBox bounds,
            double minSpeed = 0.1,
            bool useAdaptive = true)
        {
            if (seeds == null || seeds.Count == 0) return new List<Polyline>();
            if (points == null || velocities == null || points.Count != velocities.Count)
                throw new ArgumentException("Points and velocities must have same count");

            var field = new VelocityField(points, velocities);
            var streamlines = new List<Polyline>(seeds.Count);

            // 计算全局最大速度用于归一化
            double globalMaxSpeed = velocities.Max(v => v.Length);
            if (globalMaxSpeed < 1e-6) globalMaxSpeed = 1.0;

            foreach (var seed in seeds)
            {
                var streamline = TraceSingleAdaptive(seed, field, baseStepSize, maxSteps, 
                    bounds, minSpeed, useAdaptive, globalMaxSpeed);
                if (streamline != null && streamline.Count >= 2)
                    streamlines.Add(streamline);
            }

            return streamlines;
        }

        /// <summary>
        /// 追踪单条流线（正向 + 反向，自适应步长）
        /// </summary>
        private static Polyline TraceSingleAdaptive(
            Point3d seed,
            VelocityField field,
            double baseStepSize,
            int maxSteps,
            BoundingBox bounds,
            double minSpeed,
            bool useAdaptive,
            double globalMaxSpeed)
        {
            // 正向追踪
            var forward = IntegrateRK4Adaptive(seed, field, baseStepSize, maxSteps, 
                bounds, minSpeed, useAdaptive, globalMaxSpeed, 1.0);
            
            // 反向追踪
            var backward = IntegrateRK4Adaptive(seed, field, baseStepSize, maxSteps, 
                bounds, minSpeed, useAdaptive, globalMaxSpeed, -1.0);

            // 合并：反向（逆序）+ 种子点 + 正向
            var merged = new List<Point3d>();

            for (int i = backward.Count - 1; i > 0; i--)
                merged.Add(backward[i]);

            merged.AddRange(forward);

            if (merged.Count < 2) return null;
            return new Polyline(merged);
        }

        /// <summary>
        /// RK4 自适应步长积分
        /// 风速大时步长更大，流线更长；风速小时步长更小，流线更短
        /// </summary>
        private static List<Point3d> IntegrateRK4Adaptive(
            Point3d start,
            VelocityField field,
            double baseStepSize,
            int maxSteps,
            BoundingBox bounds,
            double minSpeed,
            bool useAdaptive,
            double globalMaxSpeed,
            double direction)
        {
            var pts = new List<Point3d>(maxSteps) { start };
            Point3d p = start;

            for (int step = 0; step < maxSteps; step++)
            {
                // 获取当前点速度
                Vector3d v = field.Interpolate(p);
                double speed = v.Length;

                // 速度太小则停止
                if (speed < minSpeed)
                    break;

                // 计算自适应步长
                double stepSize = baseStepSize;
                if (useAdaptive)
                {
                    // 风速越大，步长越大（1x 到 3x）
                    double speedRatio = speed / globalMaxSpeed;
                    double adaptiveFactor = 1.0 + speedRatio * 2.0; // 1.0 ~ 3.0
                    stepSize = baseStepSize * adaptiveFactor;
                }

                double h = stepSize * direction;

                // RK4 积分
                Vector3d k1 = field.Interpolate(p);
                Vector3d k2 = field.Interpolate(p + k1 * (h * 0.5));
                Vector3d k3 = field.Interpolate(p + k2 * (h * 0.5));
                Vector3d k4 = field.Interpolate(p + k3 * h);

                Vector3d dp = (k1 + k2 * 2.0 + k3 * 2.0 + k4) * (h / 6.0);

                // 检查位移是否合理
                if (dp.Length < 1e-10)
                    break;

                // 更新位置
                p = p + dp;

                // 检查是否出界
                if (!bounds.Contains(p))
                    break;

                // 检查是否形成环路（与前面的点太接近）
                bool isLoop = false;
                for (int i = Math.Max(0, pts.Count - 20); i < pts.Count; i++)
                {
                    if (p.DistanceTo(pts[i]) < stepSize * 0.1)
                    {
                        isLoop = true;
                        break;
                    }
                }
                if (isLoop) break;

                pts.Add(p);
            }

            return pts;
        }

        /// <summary>
        /// 标准 RK4 流线追踪（非自适应，保持向后兼容）
        /// </summary>
        public static List<Polyline> Trace(
            IList<Point3d> seeds,
            IList<Point3d> points,
            IList<Vector3d> velocities,
            double stepSize,
            int maxSteps,
            BoundingBox bounds,
            double minSpeed = 0.01)
        {
            return TraceAdaptive(seeds, points, velocities, stepSize, maxSteps, bounds, minSpeed, false);
        }

        /// <summary>
        /// 计算每条流线的平均速度
        /// </summary>
        public static List<double> ComputeAverageSpeeds(
            List<Polyline> streamlines,
            IList<Point3d> fieldPoints,
            IList<Vector3d> fieldVelocities)
        {
            var field = new VelocityField(fieldPoints, fieldVelocities);
            var speeds = new List<double>(streamlines.Count);

            foreach (var line in streamlines)
            {
                double totalSpeed = 0.0;
                int count = 0;

                foreach (var pt in line)
                {
                    Vector3d v = field.Interpolate(pt);
                    totalSpeed += v.Length;
                    count++;
                }

                speeds.Add(count > 0 ? totalSpeed / count : 0.0);
            }

            return speeds;
        }
    }

    /// <summary>
    /// 速度场加速结构（基于空间哈希的最近邻插值）
    /// </summary>
    internal class VelocityField
    {
        private readonly Dictionary<long, List<int>> _grid;
        private readonly IList<Point3d> _pts;
        private readonly IList<Vector3d> _vel;
        private readonly double _cellSize;
        private readonly BoundingBox _bounds;

        public VelocityField(IList<Point3d> pts, IList<Vector3d> vel, double cellSize = 0)
        {
            _pts = pts;
            _vel = vel;
            _bounds = new BoundingBox(pts);

            if (cellSize <= 0)
            {
                double volume = _bounds.Volume;
                if (volume > 1e-10)
                    cellSize = Math.Pow(volume / pts.Count, 1.0 / 3.0) * 2.0;
                else
                    cellSize = 1.0;
            }
            _cellSize = cellSize;

            _grid = new Dictionary<long, List<int>>(pts.Count);
            for (int i = 0; i < pts.Count; i++)
            {
                long h = Hash(_pts[i]);
                if (!_grid.TryGetValue(h, out var list))
                {
                    list = new List<int>();
                    _grid[h] = list;
                }
                list.Add(i);
            }
        }

        /// <summary>
        /// 三线性插值获取任意位置的速度
        /// </summary>
        public Vector3d Interpolate(Point3d p)
        {
            var nearbyIndices = GetNearbyIndices(p);
            if (nearbyIndices.Count == 0) return Vector3d.Zero;

            double weightSum = 0.0;
            Vector3d result = Vector3d.Zero;

            foreach (int idx in nearbyIndices)
            {
                double dist = p.DistanceTo(_pts[idx]);
                if (dist < 1e-10) return _vel[idx];

                double w = 1.0 / (dist * dist);
                weightSum += w;
                result += _vel[idx] * w;
            }

            return weightSum > 0 ? result / weightSum : Vector3d.Zero;
        }

        private List<int> GetNearbyIndices(Point3d p)
        {
            var result = new List<int>();

            int ix = (int)(p.X / _cellSize);
            int iy = (int)(p.Y / _cellSize);
            int iz = (int)(p.Z / _cellSize);

            for (int dx = -1; dx <= 1; dx++)
                for (int dy = -1; dy <= 1; dy++)
                    for (int dz = -1; dz <= 1; dz++)
                    {
                        long h = Hash(ix + dx, iy + dy, iz + dz);
                        if (_grid.TryGetValue(h, out var list))
                            result.AddRange(list);
                    }

            return result;
        }

        private long Hash(Point3d p)
        {
            return Hash(
                (int)(p.X / _cellSize),
                (int)(p.Y / _cellSize),
                (int)(p.Z / _cellSize));
        }

        private long Hash(int ix, int iy, int iz)
        {
            const long P1 = 73856093;
            const long P2 = 19349663;
            const long P3 = 83492791;
            return (ix * P1) ^ (iy * P2) ^ (iz * P3);
        }
    }
}
