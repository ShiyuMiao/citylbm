using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper.Kernel;
using Rhino.Geometry;
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// Lawson 2001 行人风舒适度自动评级组件（v0.2.0 新增）
    /// 
    /// 基于 Lawson 2001 标准（5% 超越概率）对行人高度风速进行舒适度评级。
    /// 同时支持安全评估（0.023% 超越概率，约每年 2 小时）。
    /// 
    /// 典型用途：
    ///   - 评估城市公共空间行人风舒适度
    ///   - 筛选不满足舒适度的区域
    ///   - 作为风环境优化的目标函数
    /// </summary>
    public class LawsonComfortComponent : GH_Component
    {
        // ── Lawson 2001 舒适度阈值（5% 超越概率）──
        // 来源：Lawson (2001), "Building Aerodynamics for Architects and Engineers"
        private static readonly double[] ComfortThresholds = new double[]
        {
            4.0,   // Category A: 坐姿，≤ 4 m/s
            6.0,   // Category B: 站立，≤ 6 m/s
            8.0,   // Category C: 步行，≤ 8 m/s
            10.0,  // Category D: 快走，≤ 10 m/s
            // > 10 m/s: Category E（不舒适）
        };

        // ── Lawson 2001 安全阈值（0.023% 超越概率 ≈ 2 小时/年）──
        private static readonly double SafetyThreshold15 = 15.0;  // m/s
        private static readonly double SafetyThreshold20 = 20.0;  // m/s

        public LawsonComfortComponent()
            : base("Lawson Comfort", "Lawson",
                   "Lawson 2001 行人风舒适度自动评级【v0.2.0】\n" +
                   "基于 5% 超越概率标准对风速数据进行舒适度分级。\n" +
                   "同时支持安全评估（0.023% 超越概率）。",
                   "CityLBM", "Results")
        { }

        public override Guid ComponentGuid => new Guid("C4E8F2A1-7B3D-4C5E-9F1A-2D3E4F5A6B7C");

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            // 风速输入（通常来自 ReadVTK 在特定高度采样）
            pManager.AddNumberParameter("Wind Speed", "V",
                "风速数据（m/s）\n" +
                "可接入 ReadVTK 的速度模，或在特定高度（1.5 m）采样后的风速。\n" +
                "支持单值和列表输入。",
                GH_ParamAccess.list);

            // 评级模式
            pManager.AddIntegerParameter("Mode", "M",
                "评级模式：\n" +
                "  0 = 舒适度评级（Lawson 2001 五类）\n" +
                "  1 = 安全评估（Safe / Unsafe / Dangerous）\n" +
                "  2 = 详细输出（同时输出舒适度类别和安全等级）",
                GH_ParamAccess.item, 0);

            // 可选：活动类型（用于针对性评估）
            pManager.AddIntegerParameter("Activity", "A",
                "活动类型（仅 Mode=0 时有效）：\n" +
                "  0 = 坐姿（Category A，≤ 4 m/s）\n" +
                "  1 = 站立（Category B，≤ 6 m/s）\n" +
                "  2 = 步行（Category C，≤ 8 m/s）\n" +
                "  3 = 快走（Category D，≤ 10 m/s）\n" +
                "  4 = 通用（输出所有类别，默认）",
                GH_ParamAccess.item, 4);

            // 所有输入均为必填（除 Activity 外）
            pManager[1].Optional = true;
            pManager[2].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            // 舒适度类别（A/B/C/D/E）
            pManager.AddIntegerParameter("Category", "C",
                "舒适度类别（Lawson 2001）\n" +
                "  0 = A（坐姿，≤ 4 m/s）\n" +
                "  1 = B（站立，≤ 6 m/s）\n" +
                "  2 = C（步行，≤ 8 m/s）\n" +
                "  3 = D（快走，≤ 10 m/s）\n" +
                "  4 = E（不舒适，> 10 m/s）\n" +
                "  -1 = 未评估",
                GH_ParamAccess.list);

            // 类别描述（字符串）
            pManager.AddTextParameter("Category Name", "CN",
                "舒适度类别名称（A/B/C/D/E）",
                GH_ParamAccess.list);

            // 是否舒适（布尔值）
            pManager.AddBooleanParameter("Is Comfortable", "OK",
                "是否舒适（根据活动类型判断）\n" +
                "True = 舒适，False = 不舒适",
                GH_ParamAccess.list);

            // 风速统计信息
            pManager.AddTextParameter("Info", "I",
                "统计信息（最大值、不合格比例等）",
                GH_ParamAccess.item);

            // 安全等级（Mode=1 或 2 时有效）
            pManager.AddIntegerParameter("Safety Level", "S",
                "安全等级（Lawson 2001）\n" +
                "  0 = 安全（≤ 15 m/s）\n" +
                "  1 = 不安全（15~20 m/s，对弱势群体制危险）\n" +
                "  2 = 危险（> 20 m/s，对公众危险）\n" +
                "  -1 = 未评估",
                GH_ParamAccess.list);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            var windSpeeds = new List<double>();
            int mode = 0;
            int activity = 4;

            if (!DA.GetDataList(0, windSpeeds)) return;
            DA.GetData(1, ref mode);
            DA.GetData(2, ref activity);

            // 参数校验
            if (windSpeeds.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "风速数据为空！");
                return;
            }

            mode = Math.Max(0, Math.Min(2, mode));
            activity = Math.Max(0, Math.Min(4, activity));

            // ── 舒适度评级（Mode = 0 或 2）────────────────────
            var categories = new List<int>();
            var categoryNames = new List<string>();
            var isComfortable = new List<bool>();

            if (mode == 0 || mode == 2)
            {
                foreach (double speed in windSpeeds)
                {
                    int cat = GetComfortCategory(speed);
                    categories.Add(cat);
                    categoryNames.Add(GetCategoryName(cat));
                    isComfortable.Add(IsComfortableForActivity(speed, activity));
                }
            }

            // ── 安全评估（Mode = 1 或 2）──────────────────────
            var safetyLevels = new List<int>();

            if (mode == 1 || mode == 2)
            {
                foreach (double speed in windSpeeds)
                {
                    safetyLevels.Add(GetSafetyLevel(speed));
                }
            }

            // ── 统计信息 ─────────────────────────────────────
            double maxSpeed = windSpeeds.Max();
            double avgSpeed = windSpeeds.Average();
            int uncomfortableCount = windSpeeds.Count(s => s > 10.0);
            double uncomfortableRatio = (double)uncomfortableCount / windSpeeds.Count;

            string info = $"Lawson 2001 评级结果\n" +
                          $"  数据点数: {windSpeeds.Count}\n" +
                          $"  最大风速: {maxSpeed:F2} m/s\n" +
                          $"  平均风速: {avgSpeed:F2} m/s\n" +
                          $"  不舒适点比例: {uncomfortableRatio:P1}\n" +
                          $"  活动类型: {GetActivityName(activity)}";

            // ── 设置输出 ─────────────────────────────────────
            if (mode == 0 || mode == 2)
            {
                DA.SetDataList(0, categories);
                DA.SetDataList(1, categoryNames);
                DA.SetDataList(2, isComfortable);
            }

            DA.SetData(3, info);

            if (mode == 1 || mode == 2)
            {
                DA.SetDataList(4, safetyLevels);
            }

            // ── 运行时提示 ─────────────────────────────────
            if (uncomfortableRatio > 0.05)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    $"超过 5% 的点不满足 Lawson 舒适度要求！（{uncomfortableRatio:P1}）");
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"✓ Lawson 评级完成：最大风速 {maxSpeed:F1} m/s，不舒适点 {uncomfortableRatio:P1}");
            }
        }

        #region 评级核心方法

        /// <summary>
        /// 根据风速返回 Lawson 2001 舒适度类别
        /// </summary>
        private static int GetComfortCategory(double speed)
        {
            if (speed <= 4.0) return 0;  // Category A
            if (speed <= 6.0) return 1;  // Category B
            if (speed <= 8.0) return 2;  // Category C
            if (speed <= 10.0) return 3; // Category D
            return 4;                      // Category E
        }

        /// <summary>
        /// 返回类别名称
        /// </summary>
        private static string GetCategoryName(int category)
        {
            switch (category)
            {
                case 0: return "A";
                case 1: return "B";
                case 2: return "C";
                case 3: return "D";
                case 4: return "E";
                default: return "?";
            }
        }

        /// <summary>
        /// 根据活动类型判断该点是否舒适
        /// </summary>
        private static bool IsComfortableForActivity(double speed, int activity)
        {
            double threshold = activity == 4 ? 10.0 : ComfortThresholds[activity];
            return speed <= threshold;
        }

        /// <summary>
        /// 根据风速返回安全等级（Lawson 2001）
        /// </summary>
        private static int GetSafetyLevel(double speed)
        {
            if (speed <= SafetyThreshold15) return 0;  // Safe
            if (speed <= SafetyThreshold20) return 1;  // Unsafe (vulnerable groups)
            return 2;                      // Dangerous (general public)
        }

        /// <summary>
        /// 返回活动类型名称
        /// </summary>
        private static string GetActivityName(int activity)
        {
            switch (activity)
            {
                case 0: return "坐姿 (Category A)";
                case 1: return "站立 (Category B)";
                case 2: return "步行 (Category C)";
                case 3: return "快走 (Category D)";
                case 4: return "通用（全类别）";
                default: return "未知";
            }
        }

        #endregion

        protected override Bitmap Icon => IconLoader.Load("Lawson.png");
    }
}
