using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// VTK 数据切面提取工具类
    /// 支持水平切面（固定 Z）和垂直切面（固定 X 或 Y）
    /// </summary>
    public static class SliceExtractor
    {
        #region 水平切面 (Horizontal Slice - 行人高度风速分析)

        /// <summary>
        /// 在指定 Z 高度提取二维速度切面，返回带 VertexColor 的 Mesh
        /// </summary>
        /// <param name="points">VTK 点坐标列表</param>
        /// <param name="velocities">速度向量列表</param>
        /// <param name="targetZ">目标高度（物理坐标，m）</param>
        /// <param name="tolerance">Z 方向容差（默认自动计算）</param>
        /// <param name="colorLow">低速颜色</param>
        /// <param name="colorHigh">高速颜色</param>
        /// <param name="speedMin">速度范围最小值（用于伪彩色，auto 时计算）</param>
        /// <param name="speedMax">速度范围最大值（用于伪彩色，auto 时计算）</param>
        /// <returns>带顶点色的 Mesh，失败返回 null</returns>
        public static Mesh ExtractHorizontalSlice(
            IList<Point3d> points,
            IList<Vector3d> velocities,
            double targetZ,
            double tolerance = -1,
            Color? colorLow = null,
            Color? colorHigh = null,
            double speedMin = double.NaN,
            double speedMax = double.NaN)
        {
            if (points == null || velocities == null || points.Count == 0)
                return null;

            // 自动计算容差：取点云 Z 方向平均间距的 0.5 倍
            // 修复：如果估计失败，使用默认容差 0.5m
            if (tolerance <= 0)
            {
                double zSpacing = EstimateZSpacing(points);
                tolerance = zSpacing > 1e-6 ? zSpacing * 0.5 : 0.5;
            }

            // 调试：输出容差信息
            System.Diagnostics.Debug.WriteLine($"[SliceExtractor] TargetZ={targetZ}, Tolerance={tolerance}, Points={points.Count}");

            // 筛选目标高度的点
            var sliceData = new List<SlicePoint>();
            for (int i = 0; i < points.Count; i++)
            {
                double dz = Math.Abs(points[i].Z - targetZ);
                if (dz <= tolerance)
                {
                    // 修复：将点投影到精确的 targetZ 高度（水平切面所有点 Z 相同）
                    Point3d projectedPoint = new Point3d(points[i].X, points[i].Y, targetZ);
                    sliceData.Add(new SlicePoint
                    {
                        Index = i,
                        Point = projectedPoint,
                        Velocity = i < velocities.Count ? velocities[i] : Vector3d.Zero,
                        ZDistance = dz
                    });
                }
            }

            System.Diagnostics.Debug.WriteLine($"[SliceExtractor] 筛选到 {sliceData.Count} 个点在 Z={targetZ}±{tolerance} 范围内");

            if (sliceData.Count < 3)
                return null;

            // 按 Z 距离排序，优先选择最接近 targetZ 的点（去重）
            sliceData = sliceData.OrderBy(p => p.ZDistance).ToList();

            // 构建网格
            Mesh mesh = BuildMeshFromSlicePoints(sliceData, out List<double> speeds);
            if (mesh == null) return null;

            // 计算速度范围
            double vMin = double.IsNaN(speedMin) ? speeds.Min() : speedMin;
            double vMax = double.IsNaN(speedMax) ? speeds.Max() : speedMax;
            double vRange = Math.Max(vMax - vMin, 1e-10);

            // 应用顶点色
            Color cLow = colorLow ?? Color.Blue;
            Color cHigh = colorHigh ?? Color.Red;

            mesh.VertexColors.Clear();
            for (int i = 0; i < speeds.Count; i++)
            {
                double t = (speeds[i] - vMin) / vRange;
                mesh.VertexColors.Add(InterpolateColor(cLow, cHigh, t));
            }

            // 优化：平滑法线计算，让云图渲染更平滑
            mesh.Normals.ComputeNormals();
            
            // 对于水平切面，统一法线为 Z 轴方向，避免光照造成的视觉噪点
            for (int i = 0; i < mesh.Normals.Count; i++)
            {
                mesh.Normals[i] = new Vector3f(0, 0, 1);
            }
            
            return mesh;
        }

        #endregion

        #region 垂直切面 (Vertical Slice)

        /// <summary>
        /// 提取垂直切面（固定 X 或 Y 的剖面）
        /// </summary>
        /// <param name="points">VTK 点坐标</param>
        /// <param name="velocities">速度向量</param>
        /// <param name="plane">切面平面（通常为 YZ 平面 X=const 或 XZ 平面 Y=const）</param>
        /// <param name="tolerance">到平面的距离容差</param>
        /// <param name="colorLow">低速颜色</param>
        /// <param name="colorHigh">高速颜色</param>
        /// <returns>带顶点色的 Mesh</returns>
        public static Mesh ExtractVerticalSlice(
            IList<Point3d> points,
            IList<Vector3d> velocities,
            Plane plane,
            double tolerance = -1,
            Color? colorLow = null,
            Color? colorHigh = null)
        {
            if (points == null || velocities == null || points.Count == 0)
                return null;

            // 自动容差
            if (tolerance <= 0)
                tolerance = EstimateXYSpacing(points) * 0.5;

            // 筛选平面附近的点
            var sliceData = new List<SlicePoint>();
            for (int i = 0; i < points.Count; i++)
            {
                double dist = Math.Abs(plane.DistanceTo(points[i]));
                if (dist <= tolerance)
                {
                    sliceData.Add(new SlicePoint
                    {
                        Index = i,
                        Point = points[i],
                        Velocity = i < velocities.Count ? velocities[i] : Vector3d.Zero,
                        ZDistance = dist
                    });
                }
            }

            if (sliceData.Count < 3)
                return null;

            sliceData = sliceData.OrderBy(p => p.ZDistance).ToList();

            Mesh mesh = BuildMeshFromSlicePoints(sliceData, out List<double> speeds);
            if (mesh == null) return null;

            double vMin = speeds.Min();
            double vMax = speeds.Max();
            double vRange = Math.Max(vMax - vMin, 1e-10);

            Color cLow = colorLow ?? Color.Blue;
            Color cHigh = colorHigh ?? Color.Red;

            mesh.VertexColors.Clear();
            for (int i = 0; i < speeds.Count; i++)
            {
                double t = (speeds[i] - vMin) / vRange;
                mesh.VertexColors.Add(InterpolateColor(cLow, cHigh, t));
            }

            mesh.Normals.ComputeNormals();
            return mesh;
        }

        #endregion

        #region 多高度批量切面

        /// <summary>
        /// 批量提取多个高度的水平切面（用于风廓线可视化）
        /// </summary>
        public static List<Mesh> ExtractMultipleHorizontalSlices(
            IList<Point3d> points,
            IList<Vector3d> velocities,
            double[] heights,
            double tolerance = -1,
            Color? colorLow = null,
            Color? colorHigh = null)
        {
            var results = new List<Mesh>();

            // 统一速度范围（跨所有高度）
            double globalMin = velocities.Min(v => v.Length);
            double globalMax = velocities.Max(v => v.Length);

            foreach (double h in heights)
            {
                Mesh mesh = ExtractHorizontalSlice(
                    points, velocities, h, tolerance,
                    colorLow, colorHigh, globalMin, globalMax);
                results.Add(mesh);
            }

            return results;
        }

        #endregion

        #region 内部辅助方法

        private class SlicePoint
        {
            public int Index;
            public Point3d Point;
            public Vector3d Velocity;
            public double ZDistance;  // 到切面的距离（用于排序）
        }

        /// <summary>
        /// 从切面点构建 Mesh（支持结构化和半结构化网格）
        /// </summary>
        private static Mesh BuildMeshFromSlicePoints(List<SlicePoint> sliceData, out List<double> speeds)
        {
            speeds = new List<double>();
            var mesh = new Mesh();

            // 检测是否为结构化网格（规则格网）
            bool isStructured = DetectStructuredGrid(sliceData);

            if (isStructured)
            {
                // 结构化网格：按 X/Y 排序构建矩形格网
                BuildStructuredMesh(sliceData, mesh, speeds);
            }
            else
            {
                // 非结构化：使用 Delaunay 三角剖分
                BuildUnstructuredMesh(sliceData, mesh, speeds);
            }

            return mesh.Faces.Count > 0 ? mesh : null;
        }

        /// <summary>
        /// 检测是否为结构化网格（点按规则格网排列）
        /// </summary>
        private static bool DetectStructuredGrid(List<SlicePoint> data)
        {
            if (data.Count < 9) return false;

            // 统计唯一点数
            int uniqueX = data.Select(p => Math.Round(p.Point.X, 6)).Distinct().Count();
            int uniqueY = data.Select(p => Math.Round(p.Point.Y, 6)).Distinct().Count();

            // 如果 X/Y 方向点数乘积接近总点数，认为是结构化
            double ratio = (double)(uniqueX * uniqueY) / data.Count;
            return ratio > 0.8 && uniqueX > 2 && uniqueY > 2;
        }

        /// <summary>
        /// 构建结构化网格（矩形格网）
        /// 防坑：用 try-catch 包裹，精度问题导致越界时降级为点云
        /// </summary>
        private static void BuildStructuredMesh(List<SlicePoint> data, Mesh mesh, List<double> speeds)
        {
            try
            {
                // 按 X 然后 Y 排序
                var sorted = data
                    .OrderBy(p => Math.Round(p.Point.Y, 6))
                    .ThenBy(p => Math.Round(p.Point.X, 6))
                    .ToList();

                // 确定网格尺寸
                int nx = sorted.Select(p => Math.Round(p.Point.X, 6)).Distinct().Count();
                int ny = sorted.Count / nx;

                // 验证网格尺寸一致性（防坑：精度抖动导致 nx*ny != sorted.Count）
                if (nx < 2 || ny < 2 || nx * ny != sorted.Count)
                {
                    BuildUnstructuredMesh(data, mesh, speeds);
                    return;
                }

                // 添加顶点和速度
                foreach (var pt in sorted)
                {
                    mesh.Vertices.Add(pt.Point);
                    speeds.Add(pt.Velocity.Length);
                }

                // 构建四边形面（拆分为两个三角形）
                for (int y = 0; y < ny - 1; y++)
                {
                    for (int x = 0; x < nx - 1; x++)
                    {
                        int i0 = y * nx + x;
                        int i1 = i0 + 1;
                        int i2 = (y + 1) * nx + x;
                        int i3 = i2 + 1;

                        // 边界检查（防坑）
                        if (i3 >= sorted.Count) continue;

                        // 两个三角形组成一个四边形
                        mesh.Faces.AddFace(i0, i1, i3);
                        mesh.Faces.AddFace(i0, i3, i2);
                    }
                }
            }
            catch
            {
                // 任何异常都降级为非结构化
                BuildUnstructuredMesh(data, mesh, speeds);
            }
        }

        /// <summary>
        /// 构建非结构化网格 - 使用简单网格化方法
        /// 将点云投影到 XY 平面，按位置排序后构建三角形
        /// </summary>
        private static void BuildUnstructuredMesh(List<SlicePoint> data, Mesh mesh, List<double> speeds)
        {
            if (data.Count < 3) return;

            // 投影到 XY 平面（水平切面）或 XZ/YZ 平面（垂直切面）
            // 检测切面方向
            bool isHorizontal = data.Select(p => p.Point.Z).Distinct().Count() == 1;

            // 按位置排序（水平切面按 X/Y，垂直切面按主要方向）
            List<SlicePoint> sorted;
            if (isHorizontal)
            {
                // 水平切面：按 X 然后 Y 排序
                sorted = data.OrderBy(p => p.Point.Y).ThenBy(p => p.Point.X).ToList();
            }
            else
            {
                // 垂直切面：按 Z 然后另一方向排序
                sorted = data.OrderBy(p => p.Point.Z).ThenBy(p => p.Point.X + p.Point.Y).ToList();
            }

            // 添加顶点
            foreach (var pt in sorted)
            {
                mesh.Vertices.Add(pt.Point);
                speeds.Add(pt.Velocity.Length);
            }

            // 简单网格化：将点云划分为小三角形
            // 策略：按排序后的顺序，每3个相邻点构成一个三角形
            // 更优策略：使用扫描线方法构建三角带
            BuildTriangulationFromSortedPoints(sorted, mesh);
        }

        /// <summary>
        /// 从排序后的点构建三角剖分
        /// 使用扫描线方法，每行构建三角形带
        /// </summary>
        private static void BuildTriangulationFromSortedPoints(List<SlicePoint> sorted, Mesh mesh)
        {
            if (sorted.Count < 3) return;

            // 估计每行的点数（通过检测坐标变化）
            int pointsPerRow = EstimatePointsPerRow(sorted);
            if (pointsPerRow < 2)
            {
                // 无法确定行结构，使用简单三角化
                BuildSimpleTriangulation(sorted, mesh);
                return;
            }

            int nRows = sorted.Count / pointsPerRow;

            // 构建三角形带
            for (int row = 0; row < nRows - 1; row++)
            {
                for (int col = 0; col < pointsPerRow - 1; col++)
                {
                    int i0 = row * pointsPerRow + col;
                    int i1 = i0 + 1;
                    int i2 = (row + 1) * pointsPerRow + col;
                    int i3 = i2 + 1;

                    // 边界检查
                    if (i3 >= sorted.Count) continue;

                    // 两个三角形组成四边形
                    // 检查三角形有效性（非退化）
                    if (IsValidTriangle(mesh.Vertices[i0], mesh.Vertices[i1], mesh.Vertices[i3]))
                        mesh.Faces.AddFace(i0, i1, i3);
                    if (IsValidTriangle(mesh.Vertices[i0], mesh.Vertices[i3], mesh.Vertices[i2]))
                        mesh.Faces.AddFace(i0, i3, i2);
                }
            }
        }

        /// <summary>
        /// 估计每行点数（通过检测坐标变化模式）
        /// </summary>
        private static int EstimatePointsPerRow(List<SlicePoint> sorted)
        {
            if (sorted.Count < 4) return sorted.Count;

            // 检测坐标变化最大的方向
            double dx = Math.Abs(sorted[1].Point.X - sorted[0].Point.X);
            double dy = Math.Abs(sorted[1].Point.Y - sorted[0].Point.Y);

            // 找到第一个坐标变化方向改变的位置
            for (int i = 2; i < Math.Min(sorted.Count, 100); i++)
            {
                double dx2 = Math.Abs(sorted[i].Point.X - sorted[i - 1].Point.X);
                double dy2 = Math.Abs(sorted[i].Point.Y - sorted[i - 1].Point.Y);

                // 如果主要变化方向改变了，说明是新的一行
                if ((dx > dy && dx2 < dy2) || (dx < dy && dx2 > dy2))
                {
                    return i;
                }
            }

            // 默认：尝试平方根估计
            int estimated = (int)Math.Sqrt(sorted.Count);
            return Math.Max(2, estimated);
        }

        /// <summary>
        /// 简单三角化（当无法确定行结构时使用）
        /// 使用扇形三角化
        /// </summary>
        private static void BuildSimpleTriangulation(List<SlicePoint> sorted, Mesh mesh)
        {
            // 找到中心点
            var centroid = new Point3d(
                sorted.Average(p => p.Point.X),
                sorted.Average(p => p.Point.Y),
                sorted.Average(p => p.Point.Z));

            // 按角度排序
            var angleSorted = sorted.Select((p, idx) => new
            {
                Index = idx,
                Point = p,
                Angle = Math.Atan2(p.Point.Y - centroid.Y, p.Point.X - centroid.X)
            }).OrderBy(x => x.Angle).ToList();

            // 构建扇形三角形
            for (int i = 0; i < angleSorted.Count - 1; i++)
            {
                int i0 = angleSorted[i].Index;
                int i1 = angleSorted[i + 1].Index;
                int i2 = angleSorted[0].Index; // 中心点

                if (IsValidTriangle(mesh.Vertices[i0], mesh.Vertices[i1], mesh.Vertices[i2]))
                    mesh.Faces.AddFace(i0, i1, i2);
            }
        }

        /// <summary>
        /// 检查三角形是否有效（非退化）
        /// </summary>
        private static bool IsValidTriangle(Point3d a, Point3d b, Point3d c)
        {
            double area = 0.5 * Vector3d.CrossProduct(b - a, c - a).Length;
            return area > 1e-10; // 面积大于阈值
        }

        /// <summary>
        /// 估计 Z 方向网格间距
        /// </summary>
        private static double EstimateZSpacing(IList<Point3d> points)
        {
            var zs = points.Select(p => p.Z).Distinct().OrderBy(z => z).ToList();
            if (zs.Count < 2) return 1.0;

            var diffs = new List<double>();
            for (int i = 1; i < zs.Count; i++)
                diffs.Add(zs[i] - zs[i - 1]);

            return diffs.Where(d => d > 1e-6).DefaultIfEmpty(1.0).Median();
        }

        /// <summary>
        /// 估计 XY 方向网格间距
        /// </summary>
        private static double EstimateXYSpacing(IList<Point3d> points)
        {
            if (points.Count < 2) return 1.0;

            var sample = points.Take(Math.Min(100, points.Count)).ToList();
            var diffs = new List<double>();

            for (int i = 1; i < sample.Count; i++)
            {
                double dx = Math.Abs(sample[i].X - sample[i - 1].X);
                double dy = Math.Abs(sample[i].Y - sample[i - 1].Y);
                if (dx > 1e-6) diffs.Add(dx);
                if (dy > 1e-6) diffs.Add(dy);
            }

            return diffs.DefaultIfEmpty(1.0).Median();
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
    }

    #region 扩展方法

    internal static class LinqExtensions
    {
        public static double Median(this IEnumerable<double> source)
        {
            var sorted = source.OrderBy(x => x).ToList();
            int n = sorted.Count;
            if (n == 0) return 0;
            if (n % 2 == 1) return sorted[n / 2];
            return (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0;
        }
    }

    #endregion
}
