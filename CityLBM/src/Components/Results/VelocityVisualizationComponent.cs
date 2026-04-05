using System;
using System.Drawing;
using System.Collections.Generic;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Solver;

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
            pManager.AddColourParameter("Color Low", "CL", "低速颜色", GH_ParamAccess.item, Color.Blue);
            pManager.AddColourParameter("Color High", "CH", "高速颜色", GH_ParamAccess.item, Color.Red);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddCurveParameter("Arrows", "A", "速度箭头线", GH_ParamAccess.list);
            pManager.AddColourParameter("Colors", "C", "箭头颜色", GH_ParamAccess.list);
            pManager.AddNumberParameter("Magnitude", "M", "速度大小", GH_ParamAccess.list);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            double scale = 1.0;
            int skip = 3;
            Color colorLow = Color.Blue;
            Color colorHigh = Color.Red;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetData(2, ref scale);
            DA.GetData(3, ref skip);
            DA.GetData(4, ref colorLow);
            DA.GetData(5, ref colorHigh);

            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据");
                return;
            }

            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数和速度数不匹配");
                return;
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
            }

            if (arrows.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    "所有速度向量均为零或低于阈值，无法生成箭头");
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"生成 {arrows.Count} 条箭头线（域大小 {domainSize:F1} m，缩放 {scale:F1}x，" +
                    $"最大速度 {maxMag:E3}，最小阈值 {minThreshold:E3}）");
            }

            DA.SetDataList(0, arrows);
            DA.SetDataList(1, colors);
            DA.SetDataList(2, magnitudes);
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
            get { return null; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("B4C8D0E3-9F5A-4B6C-8D7E-0F1A2B3C4D5E"); }
        }
    }
}
