using System;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Rendering;
using CityLBM.Utils;

namespace CityLBM.Components.Scene
{
    /// <summary>
    /// 风条件可视化组件
    /// 配合 WindCompassConduit 在 Rhino 视口中显示风向指南针和风剖面
    /// </summary>
    public class WindConditionComponent : GH_Component
    {
        private WindCompassConduit _conduit;
        private bool _conduitEnabled = false;

        public WindConditionComponent()
            : base("Wind Condition", "WindCond",
                   "可视化风场条件：在 Rhino 视口中显示风向指南针和风速剖面。\n" +
                   "风向角度：0°=北风（从北来），90°=东风（从东来）。\n" +
                   "连接 Scene 可自动获取风场参数，也可手动输入覆盖。",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S",
                "CityLBM 场景对象（可选）。连接后自动提取风场参数。",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Wind Direction", "WD",
                "来风方向角度（度）。\n0° = 北风（从北来），90° = 东风（从东来）。\n" +
                "若连接 Scene，此输入可覆盖 Scene 中的风向设置。",
                GH_ParamAccess.item, 0.0);

            pManager.AddNumberParameter("Wind Speed", "WS",
                "参考风速 (m/s)。若连接 Scene，此输入可覆盖 Scene 中的风速设置。",
                GH_ParamAccess.item, 5.0);

            pManager.AddPointParameter("Origin", "O",
                "指南针基准点（可选）。默认使用 Scene 的计算域中心或原点。",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Compass Radius", "R",
                "指南针显示半径（米）。默认 20m。",
                GH_ParamAccess.item, 20.0);

            pManager.AddBooleanParameter("Show Profile", "SP",
                "是否显示风剖面曲线（在入口边界处）。需要连接 Scene。",
                GH_ParamAccess.item, true);

            // 设置可选参数
            pManager[0].Optional = true;
            pManager[3].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Info", "I", "风场信息摘要", GH_ParamAccess.item);
            pManager.AddVectorParameter("Wind Vector", "WV", "来风方向向量", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 默认值
            double windDirection = 0.0;
            double windSpeed = 5.0;
            Point3d origin = Point3d.Unset;
            double compassRadius = 20.0;
            bool showProfile = true;

            Core.Scene scene = null;

            // 尝试获取 Scene
            IGH_Goo sceneGoo = null;
            if (DA.GetData(0, ref sceneGoo))
            {
                if (sceneGoo is GH_Scene ghScene && ghScene.Value != null)
                {
                    scene = ghScene.Value;
                }
            }

            // 从 Scene 提取参数（如果未手动覆盖）
            if (scene != null)
            {
                // 从风向向量计算角度
                Vector3d windDir = scene.WindDirection;
                if (windDir.IsValid && !windDir.IsZero)
                {
                    // 风向向量转换为角度（0=北风，90=东风）
                    // 向量(1,0,0) = 东风 = 90度
                    // 向量(0,-1,0) = 北风 = 0度
                    windDirection = Math.Atan2(windDir.X, -windDir.Y) * 180.0 / Math.PI;
                    if (windDirection < 0) windDirection += 360.0;
                }

                windSpeed = scene.WindSpeed;

                // 使用计算域中心作为原点
                BoundingBox domain = scene.GetSimulationDomain();
                if (domain.IsValid)
                {
                    origin = new Point3d(
                        (domain.Min.X + domain.Max.X) / 2.0,
                        (domain.Min.Y + domain.Max.Y) / 2.0,
                        domain.Min.Z);
                }
            }

            // 获取手动输入（覆盖 Scene 参数）
            DA.GetData(1, ref windDirection);
            DA.GetData(2, ref windSpeed);

            Point3d manualOrigin = Point3d.Unset;
            if (DA.GetData(3, ref manualOrigin))
            {
                origin = manualOrigin;
            }

            // 如果仍然没有原点，使用默认
            if (!origin.IsValid)
            {
                origin = Point3d.Origin;
            }

            DA.GetData(4, ref compassRadius);
            DA.GetData(5, ref showProfile);

            // 验证参数
            windDirection = NormalizeAngle(windDirection);
            if (windSpeed < 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "风速不能为负，已取绝对值");
                windSpeed = Math.Abs(windSpeed);
            }
            if (compassRadius < 1.0)
            {
                compassRadius = 1.0;
            }

            // 计算风向向量
            double angleRad = windDirection * Math.PI / 180.0;
            Vector3d windVector = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);
            windVector.Unitize();

            // 初始化或更新 Conduit
            InitializeConduit();

            // 更新 Conduit 数据
            _conduit.SetWindData(windDirection, windSpeed, origin, compassRadius);

            // 如果连接了 Scene，传递风廓线参数
            if (scene != null && showProfile)
            {
                WindProfileType profile = (WindProfileType)(int)scene.WindProfile;
                _conduit.SetWindProfile(
                    profile,
                    scene.ReferenceHeight,
                    scene.RoughnessLength,
                    scene.PowerLawAlpha,
                    scene.VonKarmanConstant);
                _conduit.SetDomainBounds(scene.GetSimulationDomain());
            }

            // 启用 Conduit
            if (!_conduitEnabled)
            {
                _conduit.Enabled = true;
                _conduitEnabled = true;
            }

            // 构建信息输出
            string dirText = GetDirectionText(windDirection);
            string info = $"风向: {dirText} ({windDirection:F1}°)\n" +
                         $"风速: {windSpeed:F2} m/s\n" +
                         $"向量: ({windVector.X:F3}, {windVector.Y:F3}, {windVector.Z:F3})\n" +
                         $"基准点: ({origin.X:F2}, {origin.Y:F2}, {origin.Z:F2})\n" +
                         $"显示半径: {compassRadius:F1}m";

            if (scene != null)
            {
                info += $"\n风廓线: {scene.WindProfile}\n" +
                       $"参考高度: {scene.ReferenceHeight:F1}m\n" +
                       $"粗糙度: z₀={scene.RoughnessLength:F3}m, α={scene.PowerLawAlpha:F2}";
            }

            DA.SetData(0, info);
            DA.SetData(1, windVector);
        }

        /// <summary>
        /// 初始化 DisplayConduit
        /// </summary>
        private void InitializeConduit()
        {
            if (_conduit == null)
            {
                _conduit = new WindCompassConduit();
            }
        }

        /// <summary>
        /// 组件从文档移除时清理 Conduit
        /// </summary>
        public override void RemovedFromDocument(GH_Document document)
        {
            CleanupConduit();
            base.RemovedFromDocument(document);
        }

        /// <summary>
        /// 文档关闭时清理
        /// </summary>
        public override void DocumentContextChanged(GH_Document document, GH_DocumentContext context)
        {
            if (context == GH_DocumentContext.Close)
            {
                CleanupConduit();
            }
            base.DocumentContextChanged(document, context);
        }

        /// <summary>
        /// 清理 Conduit 资源
        /// </summary>
        private void CleanupConduit()
        {
            if (_conduit != null)
            {
                _conduit.Enabled = false;
                _conduit.Clear();
                _conduit = null;
                _conduitEnabled = false;
            }
        }

        /// <summary>
        /// 将角度归一化到 [0, 360)
        /// </summary>
        private double NormalizeAngle(double angle)
        {
            while (angle < 0) angle += 360.0;
            while (angle >= 360.0) angle -= 360.0;
            return angle;
        }

        /// <summary>
        /// 获取风向文字描述
        /// </summary>
        private string GetDirectionText(double degrees)
        {
            string[] directions = { "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW" };
            int index = (int)((degrees + 11.25) / 22.5) % 16;
            return directions[index];
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("WindCondition.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("E7F3A2B5-4C8D-4E1F-9A6B-2D5C8E1F4A7B"); }
        }
    }
}
