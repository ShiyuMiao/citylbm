using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 模拟结果统计分析组件
    /// 基于 VTK 读取结果，提取关键风环境指标，输出详实的统计数据可接入 GH Panel 观察
    /// </summary>
    public class SimulationStatsComponent : GH_Component
    {
        /// <summary>风速等级定义</summary>
        private struct WindClass
        {
            public string Name;
            public double Low;
            public double High;
            public string Desc;
        }
        public SimulationStatsComponent()
            : base("Simulation Stats", "Stats",
                   "风环境模拟结果统计分析。提取关键风速指标，输出详实统计报告接入 Panel。",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt", "VTK 读取的点坐标", GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V", "VTK 读取的速度向量", GH_ParamAccess.list);
            pManager.AddNumberParameter("Grid Spacing", "GS", "原始网格间距（m），来自 Read VTK 的 Grid Spacing 输出", GH_ParamAccess.item, 0.0);
            pManager.AddTextParameter("Scene Info", "SI", "场景信息文本（可选），来自 Scene Info 输出", GH_ParamAccess.item, "");

            pManager[0].Optional = true;
            pManager[2].Optional = true;
            pManager[3].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Report", "R",
                "完整统计报告（Markdown 格式，可直接接入 GH Panel）",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Max Wind Speed", "Vmax", "最大风速 (m/s)", GH_ParamAccess.item);
            pManager.AddNumberParameter("Mean Wind Speed", "Vmean", "平均风速 (m/s)", GH_ParamAccess.item);
            pManager.AddNumberParameter("Min Wind Speed", "Vmin", "最小风速 (m/s)", GH_ParamAccess.item);
            pManager.AddNumberParameter("Std Wind Speed", "Vstd", "风速标准差 (m/s)", GH_ParamAccess.item);

            pManager.AddNumberParameter("Max Vertical", "Wmax", "最大垂直风速 (m/s)，正值=上升气流", GH_ParamAccess.item);
            pManager.AddNumberParameter("Min Vertical", "Wmin", "最小垂直风速 (m/s)，负值=下沉气流", GH_ParamAccess.item);

            pManager.AddNumberParameter("Median Wind Speed", "Vmed", "风速中位数 (m/s)", GH_ParamAccess.item);

            pManager.AddTextParameter("Wind Speed Classes", "Class",
                "风速等级分布占比（表格文本）",
                GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            double gridSpacing = 0.0;
            string sceneInfo = "";

            DA.GetDataList(0, points);
            DA.GetDataList(1, velocities);
            DA.GetData(2, ref gridSpacing);
            DA.GetData(3, ref sceneInfo);

            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据。请先连接 Read VTK 组件。");
                return;
            }

            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数和速度数不匹配。");
                return;
            }

            // ── 计算速度大小 ──────────────────────────────────
            int n = velocities.Count;
            var speeds = new double[n];
            double vMax = double.MinValue, vMin = double.MaxValue;
            double vSum = 0.0, vSumSq = 0.0;
            double wMax = double.MinValue, wMin = double.MaxValue; // 垂直风速

            for (int i = 0; i < n; i++)
            {
                double spd = velocities[i].Length;
                speeds[i] = spd;
                vSum += spd;
                vSumSq += spd * spd;
                if (spd > vMax) vMax = spd;
                if (spd < vMin) vMin = spd;

                double w = velocities[i].Z; // 垂直分量
                if (w > wMax) wMax = w;
                if (w < wMin) wMin = w;
            }

            double vMean = vSum / n;
            double vStd = Math.Sqrt(Math.Max(0, vSumSq / n - vMean * vMean));

            // 中位数
            var sortedSpeeds = (double[])speeds.Clone();
            Array.Sort(sortedSpeeds);
            double vMedian = n % 2 == 0
                ? (sortedSpeeds[n / 2 - 1] + sortedSpeeds[n / 2]) / 2.0
                : sortedSpeeds[n / 2];

            // ── 风向统计（平均水平风向）──────────────────────
            double uSum = 0, vComponentSum = 0;
            foreach (var vel in velocities)
            {
                uSum += vel.X; // 沿 X（通常为来流方向）
                vComponentSum += vel.Y;
            }
            double meanAngle = Math.Atan2(vComponentSum, uSum) * 180.0 / Math.PI;
            if (meanAngle < 0) meanAngle += 360.0;

            // ── 水平风速统计（去掉垂直分量）──────────────────
            double hMax = 0, hMean = 0;
            for (int i = 0; i < n; i++)
            {
                double h = Math.Sqrt(velocities[i].X * velocities[i].X + velocities[i].Y * velocities[i].Y);
                if (h > hMax) hMax = h;
                hMean += h;
            }
            hMean /= n;

            // ── 域信息 ──────────────────────────────────────
            BoundingBox bbox = new BoundingBox(points);
            double domainX = bbox.Max.X - bbox.Min.X;
            double domainY = bbox.Max.Y - bbox.Min.Y;
            double domainZ = bbox.Max.Z - bbox.Min.Z;

            // ── 湍流强度估算 ────────────────────────────────
            // TI = σ_v / V_mean
            double turbulenceIntensity = vMean > 1e-10 ? vStd / vMean * 100.0 : 0.0;

            // ── 风速等级分布 ────────────────────────────────
            // 按《建筑结构荷载规范》GB 50009 及风环境舒适度评价标准
            var classes = new WindClass[]
            {
                new WindClass { Name = "静风", Low = 0.0, High = 0.3, Desc = "无感" },
                new WindClass { Name = "微风", Low = 0.3, High = 1.0, Desc = "几乎无感" },
                new WindClass { Name = "轻风", Low = 1.0, High = 1.5, Desc = "站立时面部感觉" },
                new WindClass { Name = "和风", Low = 1.5, High = 3.3, Desc = "步行舒适" },
                new WindClass { Name = "清风", Low = 3.3, High = 5.4, Desc = "步行时头发飘动" },
                new WindClass { Name = "强风", Low = 5.4, High = 8.0, Desc = "不舒适，举伞困难" },
                new WindClass { Name = "疾风", Low = 8.0, High = 10.8, Desc = "严重影响行走" },
                new WindClass { Name = "大风", Low = 10.8, High = double.MaxValue, Desc = "危险" }
            };

            var classCounts = new int[classes.Length];
            for (int i = 0; i < n; i++)
            {
                for (int c = 0; c < classes.Length; c++)
                {
                    if (speeds[i] >= classes[c].Low && speeds[i] < classes[c].High)
                    {
                        classCounts[c]++;
                        break;
                    }
                }
            }

            // ── 风环境舒适度评价（Lawson 标准）──────────────
            string comfortOverall;
            double comfortPct;
            // 舒适：风速 ≤ 5.4 m/s 的比例
            int comfortCount = 0;
            for (int i = 0; i < n; i++)
                if (speeds[i] <= 5.4) comfortCount++;
            comfortPct = 100.0 * comfortCount / n;

            if (comfortPct >= 80)
                comfortOverall = "优秀 - 大部分区域风速舒适";
            else if (comfortPct >= 60)
                comfortOverall = "良好 - 多数区域风速可接受";
            else if (comfortPct >= 40)
                comfortOverall = "一般 - 部分区域存在风速过高";
            else
                comfortOverall = "较差 - 大面积区域风速不舒适";

            // ── 构建报告 ────────────────────────────────────
            string report = BuildReport(
                points.Count, vMax, vMin, vMean, vMedian, vStd,
                wMax, wMin, hMax, hMean,
                meanAngle, turbulenceIntensity, comfortOverall, comfortPct,
                domainX, domainY, domainZ, gridSpacing,
                classes, classCounts, n, sceneInfo);

            // ── 构建等级分布表 ──────────────────────────────
            string classTable = BuildClassTable(classes, classCounts, n);

            // ── 输出 ────────────────────────────────────────
            DA.SetData(0, report);
            DA.SetData(1, vMax);
            DA.SetData(2, vMean);
            DA.SetData(3, vMin);
            DA.SetData(4, vStd);
            DA.SetData(5, wMax);
            DA.SetData(6, wMin);
            DA.SetData(7, vMedian);
            DA.SetData(8, classTable);
        }

        // ══════════════════════════════════════════════════════════════
        // 报告生成
        // ══════════════════════════════════════════════════════════════

        private string BuildReport(
            int pointCount,
            double vMax, double vMin, double vMean, double vMedian, double vStd,
            double wMax, double wMin, double hMax, double hMean,
            double meanAngle, double ti, string comfort, double comfortPct,
            double dx, double dy, double dz, double gridSpacing,
            WindClass[] classes,
            int[] classCounts, int total, string sceneInfo)
        {
            var sb = new System.Text.StringBuilder();

            sb.AppendLine("╔══════════════════════════════════════════════════════════╗");
            sb.AppendLine("║          CityLBM 风环境模拟结果统计报告                  ║");
            sb.AppendLine("╚══════════════════════════════════════════════════════════╝");
            sb.AppendLine();

            // 场景信息
            if (!string.IsNullOrWhiteSpace(sceneInfo))
            {
                sb.AppendLine("━━━━━━━━━━ 场景信息 ━━━━━━━━━━");
                sb.AppendLine(sceneInfo);
                sb.AppendLine();
            }

            // 数据概览
            sb.AppendLine("━━━━━━━━━━ 数据概览 ━━━━━━━━━━");
            sb.AppendLine($"  统计点数:       {pointCount:N0}");
            string gridStr = gridSpacing > 1e-10 ? $"{gridSpacing:F3} m" : "未知";
            sb.AppendLine($"  网格间距:       {gridStr}");
            sb.AppendLine($"  域尺寸 X:       {dx:F1} m");
            sb.AppendLine($"  域尺寸 Y:       {dy:F1} m");
            sb.AppendLine($"  域尺寸 Z:       {dz:F1} m");
            sb.AppendLine($"  域体积:         {(dx * dy * dz):F0} m³");
            sb.AppendLine();

            // 风速统计
            sb.AppendLine("━━━━━━━━━━ 风速统计 ━━━━━━━━━━");
            sb.AppendLine($"  最大风速:       {vMax:F4} m/s");
            sb.AppendLine($"  最小风速:       {vMin:F4} m/s");
            sb.AppendLine($"  平均风速:       {vMean:F4} m/s");
            sb.AppendLine($"  风速中位数:     {vMedian:F4} m/s");
            sb.AppendLine($"  风速标准差:     {vStd:F4} m/s");
            sb.AppendLine();

            // 分量统计
            sb.AppendLine("━━━━━━━━━━ 分量统计 ━━━━━━━━━━");
            sb.AppendLine($"  最大水平风速:   {hMax:F4} m/s");
            sb.AppendLine($"  平均水平风速:   {hMean:F4} m/s");
            sb.AppendLine($"  最大上升气流:   {wMax:F4} m/s");
            sb.AppendLine($"  最大下沉气流:   {wMin:F4} m/s");
            sb.AppendLine($"  平均风向角:     {meanAngle:F1}° (从+X轴逆时针)");
            sb.AppendLine();

            // 湍流特征
            sb.AppendLine("━━━━━━━━━━ 湍流特征 ━━━━━━━━━━");
            sb.AppendLine($"  湍流强度 TI:    {ti:F1}%");
            if (ti < 5)
                sb.AppendLine($"  湍流等级:       低（平稳流场）");
            else if (ti < 20)
                sb.AppendLine($"  湍流等级:       中等");
            else
                sb.AppendLine($"  湍流等级:       高（湍流剧烈）");
            sb.AppendLine();

            // 风速等级分布
            sb.AppendLine("━━━━━━━━━━ 风速等级分布 ━━━━━━━━━━");
            sb.AppendLine($"  {"等级",-8}  {"范围 (m/s)",-16}  {"点数",-10}  {"占比",-8}  说明");
            sb.AppendLine($"  {new string('─', 60)}");
            for (int i = 0; i < classes.Length; i++)
            {
                string range = classes[i].High == double.MaxValue
                    ? $"> {classes[i].Low:F1}"
                    : $"{classes[i].Low:F1} ~ {classes[i].High:F1}";
                string pct = $"{100.0 * classCounts[i] / total:F1}%";
                string bar = new string('█', (int)(100.0 * classCounts[i] / total / 2));
                sb.AppendLine($"  {classes[i].Name,-8}  {range,-16}  {classCounts[i],-10:N0}  {pct,-8}  {classes[i].Desc}  {bar}");
            }
            sb.AppendLine();

            // 舒适度评价
            sb.AppendLine("━━━━━━━━━━ 舒适度评价 (Lawson 标准) ━━━━━━━━━━");
            sb.AppendLine($"  舒适阈值:       ≤ 5.4 m/s");
            sb.AppendLine($"  舒适区域占比:   {comfortPct:F1}%");
            sb.AppendLine($"  综合评价:       {comfort}");
            sb.AppendLine();

            // 参考标准
            sb.AppendLine("━━━━━━━━━━ 参考标准 ━━━━━━━━━━");
            sb.AppendLine("  • Lawson 风舒适度标准 (Pedestrian Wind Comfort)");
            sb.AppendLine("  • 舒适区: 风速 ≤ 5.4 m/s (步行舒适上限)");
            sb.AppendLine("  • 可接受区: 风速 5.4 ~ 8.0 m/s (举伞困难)");
            sb.AppendLine("  • 不舒适区: 风速 > 8.0 m/s (影响行人安全)");

            return sb.ToString();
        }

        private string BuildClassTable(
            WindClass[] classes,
            int[] classCounts, int total)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("等级\t范围(m/s)\t点数\t占比");
            sb.AppendLine("─\t─\t─\t─");
            for (int i = 0; i < classes.Length; i++)
            {
                string range = classes[i].High == double.MaxValue
                    ? $"> {classes[i].Low:F1}"
                    : $"{classes[i].Low:F1}~{classes[i].High:F1}";
                string pct = $"{100.0 * classCounts[i] / total:F1}%";
                sb.AppendLine($"{classes[i].Name}\t{range}\t{classCounts[i]:N0}\t{pct}");
            }
            return sb.ToString();
        }

        protected override Bitmap Icon => null;

        public override Guid ComponentGuid
            => new Guid("D4E5F6A7-B8C9-4D0E-A1B2-C3D4E5F6A7B8");
    }
}
