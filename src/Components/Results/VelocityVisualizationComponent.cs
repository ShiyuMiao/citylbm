using System;
using System.Drawing;
using System.Collections.Generic;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Solver;
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 速度场可视化组件
    /// 将 VTK 速度数据转换为线箭头可视化
    /// </summary>
    public class VelocityVisualizationComponent : GH_Component
    {
        public VelocityVisualizationComponent()
            : base("Visualize Velocity", "VisVel",
                   "将速度场数据可视化为线箭头（箭头长度表示速度大小）",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt", "网格点坐标", GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V", "速度向量", GH_ParamAccess.list);
            pManager.AddNumberParameter("Scale", "S", "箭头缩放比例（1.0 = 默认大小，2.0 = 两倍长）", GH_ParamAccess.item, 1.0);
            pManager.AddIntegerParameter("Skip", "K", "采样间隔（每隔几个点显示一个箭头，3=默认，1=不跳过）", GH_ParamAccess.item, 3);
            pManager.AddNumberParameter("Slice Z", "Z",
                "Z 切片高度（可选）。\n" +
                "设置后只显示该高度附近的箭头，避免多层重叠。\n" +
                "留空（NaN）显示全部层。",
                GH_ParamAccess.item, double.NaN);
            pManager.AddNumberParameter("Z Tolerance", "ZT",
                "Z 方向容差（用于 Slice Z 过滤，默认自动计算）。",
                GH_ParamAccess.item, 0.0);
            pManager.AddIntegerParameter("Arrow Style", "AS",
                "箭头样式：\n" +
                "  0 = 简单线段（每个点1条线，便于与点云一一对应）\n" +
                "  1 = 带箭头翼（默认，每个点3条线）",
                GH_ParamAccess.item, 1);
            pManager.AddColourParameter("Color Low", "CL", "低速颜色", GH_ParamAccess.item, Color.Blue);
            pManager.AddColourParameter("Color High", "CH", "高速颜色", GH_ParamAccess.item, Color.Red);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddCurveParameter("Arrows", "A", "速度箭头线（每个箭头3条线：杆+两翼，或1条线）", GH_ParamAccess.list);
            pManager.AddColourParameter("Colors", "C", "箭头颜色（与箭头线一一对应）", GH_ParamAccess.list);
            pManager.AddNumberParameter("Magnitude", "M", "速度大小（与原始点/箭头组一一对应）", GH_ParamAccess.list);
            pManager.AddPointParameter("Arrow Points", "AP", "箭头起点坐标（与Magnitude一一对应，用于与点云对齐）", GH_ParamAccess.list);
            pManager.AddTextParameter("Log", "Log", "执行日志（用于诊断）", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 创建日志记录器
            var logger = new ComponentLogger("VelocityVis");
            
            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            double scale = 1.0;
            int skip = 3;
            double sliceZ = double.NaN;
            double zTolerance = 0.0;
            int arrowStyle = 1; // 默认带箭头翼
            Color colorLow = Color.Blue;
            Color colorHigh = Color.Red;

            if (!DA.GetDataList(0, points)) 
            {
                DA.SetData(4, logger.GetLog());
                return;
            }
            if (!DA.GetDataList(1, velocities)) 
            {
                DA.SetData(4, logger.GetLog());
                return;
            }
            DA.GetData(2, ref scale);
            DA.GetData(3, ref skip);
            DA.GetData(4, ref sliceZ);
            DA.GetData(5, ref zTolerance);
            DA.GetData(6, ref arrowStyle);
            DA.GetData(7, ref colorLow);
            DA.GetData(8, ref colorHigh);
            
            logger.Config("输入点数", points.Count);
            logger.Config("输入速度数", velocities.Count);
            logger.Config("缩放比例", scale);
            logger.Config("采样间隔", skip);
            
            if (!double.IsNaN(sliceZ))
            {
                logger.Config("Z切片", $"{sliceZ:F2}m");
                logger.Config("Z容差", zTolerance > 0 ? $"{zTolerance:F3}m" : "自动");
            }
            else
            {
                logger.Info("显示全部层（无Z切片）");
            }

            if (points.Count == 0 || velocities.Count == 0)
            {
                logger.Warning("没有输入数据");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据");
                DA.SetData(4, logger.GetLog());
                return;
            }

            if (points.Count != velocities.Count)
            {
                logger.Error($"点数({points.Count})和速度数({velocities.Count})不匹配");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数和速度数不匹配");
                DA.SetData(4, logger.GetLog());
                return;
            }
            
            // 记录数据范围
            double dataMinZ = points.Min(p => p.Z);
            double dataMaxZ = points.Max(p => p.Z);
            logger.Range("输入数据Z范围", dataMinZ, dataMaxZ);

            // ── Z 切片过滤 ──
            bool useSlice = !double.IsNaN(sliceZ);
            if (useSlice)
            {
                // 自动计算 Z 容差：检测采样后的 Z 间距
                if (zTolerance <= 0)
                {
                    var zSet = new SortedSet<double>();
                    foreach (var pt in points)
                        zSet.Add(pt.Z);
                    var zArr = zSet.ToArray();
                    double minZGap = double.MaxValue;
                    for (int i = 1; i < zArr.Length; i++)
                    {
                        double gap = zArr[i] - zArr[i - 1];
                        if (gap > 1e-10 && gap < minZGap)
                            minZGap = gap;
                    }
                    zTolerance = minZGap < double.MaxValue ? minZGap * 0.45 : 1.0;
                }

                // 过滤：只保留 |Z - sliceZ| <= zTolerance 的点
                var filteredPts = new List<Point3d>();
                var filteredVels = new List<Vector3d>();
                for (int i = 0; i < points.Count; i++)
                {
                    if (Math.Abs(points[i].Z - sliceZ) <= zTolerance)
                    {
                        filteredPts.Add(points[i]);
                        filteredVels.Add(velocities[i]);
                    }
                }
                points = filteredPts;
                velocities = filteredVels;

                if (points.Count > 0)
                {
                    logger.Info($"Z 切片: {sliceZ:F2}m (容差 ±{zTolerance:F2}m)，筛选后 {points.Count} 个点");
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                        $"Z 切片: {sliceZ:F2} m (容差 ±{zTolerance:F2} m)，筛选后 {points.Count} 个点");
                }
                else
                {
                    logger.Warning($"Z={sliceZ:F2}m 附近没有找到点（容差 ±{zTolerance:F2}m）");
                    logger.Info($"可用 Z 范围: [{dataMinZ:F1}, {dataMaxZ:F1}] m");
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                        $"Z={sliceZ:F2} 附近没有找到点（容差 ±{zTolerance:F2} m）。\n" +
                        $"可用 Z 层高度可通过 Read VTK 的 Points 输出查看。");
                    DA.SetDataList(0, new List<Curve>());
                    DA.SetDataList(1, new List<Color>());
                    DA.SetDataList(2, new List<double>());
                    DA.SetData(4, logger.GetLog());
                    return;
                }
            }

            // 计算速度范围
            double minMag = double.MaxValue;
            double maxMag = double.MinValue;
            foreach (Vector3d vel in velocities)
            {
                double mag = vel.Length;
                if (mag < minMag) minMag = mag;
                if (mag > maxMag) maxMag = mag;
            }

            // 自动计算箭头长度基准
            // 策略：让最大速度对应的箭头长度 = 域对角线长度的 5%
            double domainSize = 1.0;
            if (points.Count > 1)
            {
                double minX = double.MaxValue, maxX = double.MinValue;
                double minY = double.MaxValue, maxY = double.MinValue;
                double minZ = double.MaxValue, maxZ = double.MinValue;
                foreach (var pt in points)
                {
                    if (pt.X < minX) minX = pt.X;
                    if (pt.X > maxX) maxX = pt.X;
                    if (pt.Y < minY) minY = pt.Y;
                    if (pt.Y > maxY) maxY = pt.Y;
                    if (pt.Z < minZ) minZ = pt.Z;
                    if (pt.Z > maxZ) maxZ = pt.Z;
                }
                domainSize = Math.Sqrt(
                    (maxX - minX) * (maxX - minX) +
                    (maxY - minY) * (maxY - minY) +
                    (maxZ - minZ) * (maxZ - minZ));
            }
            // 默认箭头长度 = 域对角线 * 5% * scale * (当前速度/最大速度)
            double autoLength = domainSize * 0.05 * scale;

            // 过滤最小速度阈值：小于此值的速度视为零（避免噪声箭头）
            double minThreshold = maxMag * 0.01;

            // 生成箭头曲线
            List<Curve> arrows = new List<Curve>();
            List<Color> colors = new List<Color>();
            List<double> magnitudes = new List<double>();
            List<Point3d> arrowPoints = new List<Point3d>(); // 箭头起点，与 magnitudes 一一对应

            for (int i = 0; i < points.Count; i += skip)
            {
                Point3d pt = points[i];
                Vector3d vel = velocities[i];
                double mag = vel.Length;

                if (mag < minThreshold)
                    continue;

                // 计算箭头长度：按速度大小线性缩放
                double arrowLength;
                if (maxMag > 1e-10)
                {
                    double t = mag / maxMag;
                    arrowLength = autoLength * (0.15 + 0.85 * t);
                }
                else
                {
                    arrowLength = autoLength * 0.5;
                }

                // 创建线箭头（线段 + V 形箭头尖端）
                List<Curve> arrowCurves = CreateArrowLines(pt, vel, arrowLength);
                arrows.AddRange(arrowCurves);

                // 计算颜色
                double ct = maxMag > minMag ? (mag - minMag) / (maxMag - minMag) : 0.5;
                Color color = InterpolateColor(colorLow, colorHigh, ct);
                for (int c = 0; c < arrowCurves.Count; c++)
                    colors.Add(color);

                magnitudes.Add(mag);
                arrowPoints.Add(pt); // 记录箭头起点，与 magnitudes 一一对应
            }

            if (arrows.Count == 0)
            {
                logger.Warning("所有速度向量均为零或低于阈值，无法生成箭头");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    "所有速度向量均为零或低于阈值，无法生成箭头");
            }
            else
            {
                logger.Info($"生成 {arrows.Count} 条箭头线");
                logger.Info($"域大小 {domainSize:F1}m, 缩放 {scale:F1}x");
                logger.Range("速度范围", minMag, maxMag);
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"生成 {arrows.Count} 条箭头线（域大小 {domainSize:F1} m，缩放 {scale:F1}x，" +
                    $"最大速度 {maxMag:E3}，最小阈值 {minThreshold:E3}）");
            }

            DA.SetDataList(0, arrows);
            DA.SetDataList(1, colors);
            DA.SetDataList(2, magnitudes);
            DA.SetDataList(3, arrowPoints);
            DA.SetData(4, logger.GetLog());
        }

        /// <summary>
        /// 创建带 V 形箭头尖的箭头线：杆 + 两翼箭头
        /// </summary>
        private List<Curve> CreateArrowLines(Point3d start, Vector3d direction, double length)
        {
            List<Curve> curves = new List<Curve>();

            Vector3d dir = direction;
            dir.Unitize();

            // 终点 = 起点 + 方向 × 长度
            Point3d end = start + dir * length;

            // 主杆
            curves.Add(new LineCurve(start, end));

            // V 形箭头尖（两翼各为总长度的 20%，翼展 60°）
            double headLen = length * 0.20;
            double headAngle = Math.PI / 3.0; // 60° 翼展角

            // 构造垂直于 dir 的两个平面方向
            Vector3d perp;
            if (Math.Abs(dir.Z) < 0.99)
                perp = Vector3d.CrossProduct(dir, Vector3d.ZAxis);
            else
                perp = Vector3d.CrossProduct(dir, Vector3d.YAxis);
            perp.Unitize();

            Vector3d back = -dir; // 箭头指向后方

            // 左翼
            Vector3d wingL = back + perp * Math.Tan(headAngle / 2.0);
            wingL.Unitize();
            Point3d wingL_End = end + wingL * headLen;
            curves.Add(new LineCurve(end, wingL_End));

            // 右翼
            Vector3d wingR = back - perp * Math.Tan(headAngle / 2.0);
            wingR.Unitize();
            Point3d wingR_End = end + wingR * headLen;
            curves.Add(new LineCurve(end, wingR_End));

            return curves;
        }

        private Color InterpolateColor(Color c1, Color c2, double t)
        {
            int r = (int)(c1.R + t * (c2.R - c1.R));
            int g = (int)(c1.G + t * (c2.G - c1.G));
            int b = (int)(c1.B + t * (c2.B - c1.B));
            return Color.FromArgb(255, Math.Max(0, Math.Min(255, r)), Math.Max(0, Math.Min(255, g)), Math.Max(0, Math.Min(255, b)));
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("VelocityVisualization.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("B4C8D0E3-9F5A-4B6C-8D7E-0F1A2B3C4D5E"); }
        }
    }
}
