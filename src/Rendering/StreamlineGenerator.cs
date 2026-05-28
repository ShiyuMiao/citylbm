using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// 流线图生成器 - 从 VTK 速度场计算流线
    /// 支持 RK4 积分和多种种子点生成策略
    /// </summary>
    public static class StreamlineGenerator
    {
        #region 流线计算参数

        /// <summary>
        /// 流线积分参数
        /// </summary>
        public class StreamlineParams
        {
            /// <summary>最大积分步数</summary>
            public int MaxSteps { get; set; } = 500;
            
            /// <summary>积分步长（物理单位：米）</summary>
            public double StepSize { get; set; } = 0.5;
            
            /// <summary>最小速度阈值（低于此值停止积分）</summary>
            public double MinVelocity { get; set; } = 0.01;
            
            /// <summary>最大流线长度（米）</summary>
            public double MaxLength { get; set; } = 500.0;
            
            /// <summary>是否双向积分（向前和向后）</summary>
            public bool Bidirectional { get; set; } = true;
            
            /// <summary>是否使用自适应步长</summary>
            public bool AdaptiveStep { get; set; } = true;
        }

        #endregion

        #region 种子点生成

        /// <summary>
        /// 在指定平面上生成均匀分布的种子点网格
        /// </summary>
        public static List<Point3d> GenerateGridSeeds(
            Plane plane,
            double width,
            double height,
            int countX,
            int countY)
        {
            var seeds = new List<Point3d>();
            
            for (int i = 0; i < countX; i++)
            {
                for (int j = 0; j < countY; j++)
                {
                    double u = (i + 0.5) / countX - 0.5;  // -0.5 to 0.5
                    double v = (j + 0.5) / countY - 0.5;
                    
                    Point3d pt = plane.Origin 
                        + plane.XAxis * u * width 
                        + plane.YAxis * v * height;
                    
                    seeds.Add(pt);
                }
            }
            
            return seeds;
        }

        /// <summary>
        /// 在指定区域内生成随机种子点
        /// </summary>
        public static List<Point3d> GenerateRandomSeeds(
            BoundingBox bounds,
            int count,
            Random random = null)
        {
            random ??= new Random();
            var seeds = new List<Point3d>();
            
            for (int i = 0; i < count; i++)
            {
                double x = bounds.Min.X + random.NextDouble() * (bounds.Max.X - bounds.Min.X);
                double y = bounds.Min.Y + random.NextDouble() * (bounds.Max.Y - bounds.Min.Y);
                double z = bounds.Min.Z + random.NextDouble() * (bounds.Max.Z - bounds.Min.Z);
                seeds.Add(new Point3d(x, y, z));
            }
            
            return seeds;
        }

        /// <summary>
        /// 在建筑周围生成环形种子点（用于观察绕流）
        /// </summary>
        public static List<Point3d> GenerateCircleSeeds(
            Point3d center,
            double radius,
            int count,
            Plane plane)
        {
            var seeds = new List<Point3d>();
            
            for (int i = 0; i < count; i++)
            {
                double angle = 2 * Math.PI * i / count;
                Vector3d offset = plane.XAxis * Math.Cos(angle) * radius
                                + plane.YAxis * Math.Sin(angle) * radius;
                seeds.Add(center + offset);
            }
            
            return seeds;
        }

        /// <summary>
        /// 在入口边界生成种子点（用于风场分析）
        /// </summary>
        public static List<Point3d> GenerateInletSeeds(
            BoundingBox domainBounds,
            double inletX,
            int countY,
            int countZ,
            double margin = 5.0)
        {
            var seeds = new List<Point3d>();
            
            double yMin = domainBounds.Min.Y + margin;
            double yMax = domainBounds.Max.Y - margin;
            double zMin = domainBounds.Min.Z + margin;
            double zMax = domainBounds.Max.Z - margin;
            
            for (int i = 0; i < countY; i++)
            {
                for (int j = 0; j < countZ; j++)
                {
                    double y = yMin + (yMax - yMin) * (i + 0.5) / countY;
                    double z = zMin + (zMax - zMin) * (j + 0.5) / countZ;
                    seeds.Add(new Point3d(inletX, y, z));
                }
            }
            
            return seeds;
        }

        #endregion

        #region 流线积分

        /// <summary>
        /// 从种子点计算单条流线
        /// </summary>
        public static Polyline ComputeStreamline(
            Point3d seed,
            IList<Point3d> gridPoints,
            IList<Vector3d> velocities,
            StreamlineParams param,
            bool forward = true)
        {
            var streamline = new Polyline { seed };
            Point3d current = seed;
            double totalLength = 0.0;
            
            // 空间哈希加速
            var spatialHash = new SpatialHash(gridPoints, 5.0);
            
            for (int step = 0; step < param.MaxSteps; step++)
            {
                // 使用 RK4 积分
                Vector3d v1 = InterpolateVelocity(current, gridPoints, velocities, spatialHash);
                if (!forward) v1 = -v1;
                
                if (v1.Length < param.MinVelocity)
                    break;
                
                // 自适应步长
                double dt = param.StepSize;
                if (param.AdaptiveStep)
                {
                    // 速度大时步长小，保证精度
                    dt = Math.Min(param.StepSize, param.StepSize * 2.0 / (1.0 + v1.Length));
                }
                
                // RK4 积分
                Point3d k1 = current + v1 * (dt * 0.5);
                Vector3d v2 = InterpolateVelocity(k1, gridPoints, velocities, spatialHash);
                if (!forward) v2 = -v2;
                
                Point3d k2 = current + v2 * (dt * 0.5);
                Vector3d v3 = InterpolateVelocity(k2, gridPoints, velocities, spatialHash);
                if (!forward) v3 = -v3;
                
                Point3d k3 = current + v3 * dt;
                Vector3d v4 = InterpolateVelocity(k3, gridPoints, velocities, spatialHash);
                if (!forward) v4 = -v4;
                
                Vector3d delta = (v1 + v2 * 2.0 + v3 * 2.0 + v4) * (dt / 6.0);
                Point3d next = current + delta;
                
                // 检查步长
                double stepLen = current.DistanceTo(next);
                if (stepLen < 1e-6)
                    break;
                
                totalLength += stepLen;
                if (totalLength > param.MaxLength)
                    break;
                
                streamline.Add(next);
                current = next;
            }
            
            return streamline;
        }

        /// <summary>
        /// 计算完整流线（双向）
        /// </summary>
        public static Polyline ComputeFullStreamline(
            Point3d seed,
            IList<Point3d> gridPoints,
            IList<Vector3d> velocities,
            StreamlineParams param)
        {
            if (!param.Bidirectional)
            {
                return ComputeStreamline(seed, gridPoints, velocities, param, true);
            }
            
            // 向后积分
            var backward = ComputeStreamline(seed, gridPoints, velocities, param, false);
            
            // 向前积分
            var forward = ComputeStreamline(seed, gridPoints, velocities, param, true);
            
            // 合并（去掉重复的种子点）
            var full = new Polyline();
            
            // 添加反向部分（倒序，去掉种子点）
            for (int i = backward.Count - 1; i > 0; i--)
                full.Add(backward[i]);
            
            // 添加正向部分
            foreach (var pt in forward)
                full.Add(pt);
            
            return full;
        }

        /// <summary>
        /// 批量计算多条流线
        /// </summary>
        public static List<Polyline> ComputeStreamlines(
            IList<Point3d> seeds,
            IList<Point3d> gridPoints,
            IList<Vector3d> velocities,
            StreamlineParams param,
            IProgress<string> progress = null)
        {
            var streamlines = new List<Polyline>();
            int total = seeds.Count;
            
            for (int i = 0; i < total; i++)
            {
                var line = ComputeFullStreamline(seeds[i], gridPoints, velocities, param);
                if (line.Count >= 2)
                    streamlines.Add(line);
                
                if (i % 10 == 0)
                    progress?.Report($"计算流线 {i+1}/{total}...");
            }
            
            return streamlines;
        }

        #endregion

        #region 速度插值

        /// <summary>
        /// 使用 IDW（反距离加权）插值获取任意位置的速度
        /// </summary>
        private static Vector3d InterpolateVelocity(
            Point3d pt,
            IList<Point3d> gridPoints,
            IList<Vector3d> velocities,
            SpatialHash spatialHash)
        {
            // 搜索附近点
            var neighbors = spatialHash.FindNearby(pt, 4);  // 找最近的4个点
            
            if (neighbors.Count == 0)
                return Vector3d.Zero;
            
            // IDW 插值
            double weightSum = 0;
            Vector3d velocitySum = Vector3d.Zero;
            
            foreach (int idx in neighbors)
            {
                double dist = pt.DistanceTo(gridPoints[idx]);
                if (dist < 1e-6)
                    return velocities[idx];  // 正好在格点上
                
                double weight = 1.0 / (dist * dist);  // 反距离平方
                weightSum += weight;
                velocitySum += velocities[idx] * weight;
            }
            
            return weightSum > 0 ? velocitySum / weightSum : Vector3d.Zero;
        }

        #endregion

        #region 流线渲染数据

        /// <summary>
        /// 将流线转换为带颜色的线段（用于可视化）
        /// </summary>
        public static List<Line> StreamlinesToLines(
            List<Polyline> streamlines,
            IList<Point3d> gridPoints,
            IList<Vector3d> velocities,
            out List<Color> colors,
            Color colorLow,
            Color colorHigh,
            double speedMin = double.NaN,
            double speedMax = double.NaN)
        {
            var lines = new List<Line>();
            colors = new List<Color>();
            
            // 计算速度范围
            double vMin = double.IsNaN(speedMin) ? velocities.Min(v => v.Length) : speedMin;
            double vMax = double.IsNaN(speedMax) ? velocities.Max(v => v.Length) : speedMax;
            double vRange = Math.Max(vMax - vMin, 1e-10);
            
            var spatialHash = new SpatialHash(gridPoints, 5.0);
            
            foreach (var streamline in streamlines)
            {
                for (int i = 0; i < streamline.Count - 1; i++)
                {
                    lines.Add(new Line(streamline[i], streamline[i + 1]));
                    
                    // 计算中点速度用于着色
                    Point3d mid = (streamline[i] + streamline[i + 1]) / 2;
                    Vector3d v = InterpolateVelocity(mid, gridPoints, velocities, spatialHash);
                    double t = (v.Length - vMin) / vRange;
                    colors.Add(InterpolateColor(colorLow, colorHigh, t));
                }
            }
            
            return lines;
        }

        /// <summary>
        /// 颜色插值
        /// </summary>
        private static Color InterpolateColor(Color a, Color b, double t)
        {
            t = Math.Max(0, Math.Min(1, t));
            return Color.FromArgb(
                (int)(a.R + (b.R - a.R) * t),
                (int)(a.G + (b.G - a.G) * t),
                (int)(a.B + (b.B - a.B) * t));
        }

        #endregion

        #region 空间哈希（加速最近邻搜索）

        /// <summary>
        /// 简单空间哈希用于加速速度插值
        /// </summary>
        private class SpatialHash
        {
            private readonly Dictionary<long, List<int>> _buckets;
            private readonly double _cellSize;
            private readonly IList<Point3d> _points;
            
            public SpatialHash(IList<Point3d> points, double cellSize)
            {
                _points = points;
                _cellSize = cellSize;
                _buckets = new Dictionary<long, List<int>>();
                
                for (int i = 0; i < points.Count; i++)
                {
                    long hash = HashPoint(points[i]);
                    if (!_buckets.ContainsKey(hash))
                        _buckets[hash] = new List<int>();
                    _buckets[hash].Add(i);
                }
            }
            
            private long HashPoint(Point3d pt)
            {
                int ix = (int)Math.Floor(pt.X / _cellSize);
                int iy = (int)Math.Floor(pt.Y / _cellSize);
                int iz = (int)Math.Floor(pt.Z / _cellSize);
                return ((long)ix * 73856093) ^ ((long)iy * 19349663) ^ ((long)iz * 83492791);
            }
            
            public List<int> FindNearby(Point3d pt, int count)
            {
                var result = new List<int>();
                var distances = new List<(int idx, double dist)>();
                
                // 搜索相邻的哈希桶
                int ix = (int)Math.Floor(pt.X / _cellSize);
                int iy = (int)Math.Floor(pt.Y / _cellSize);
                int iz = (int)Math.Floor(pt.Z / _cellSize);
                
                for (int dx = -1; dx <= 1; dx++)
                for (int dy = -1; dy <= 1; dy++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    long hash = ((long)(ix + dx) * 73856093) 
                              ^ ((long)(iy + dy) * 19349663) 
                              ^ ((long)(iz + dz) * 83492791);
                    
                    if (_buckets.TryGetValue(hash, out var bucket))
                    {
                        foreach (int idx in bucket)
                        {
                            double dist = pt.DistanceTo(_points[idx]);
                            distances.Add((idx, dist));
                        }
                    }
                }
                
                // 返回最近的 count 个点
                return distances
                    .OrderBy(x => x.dist)
                    .Take(count)
                    .Select(x => x.idx)
                    .ToList();
            }
        }

        #endregion
    }
}
