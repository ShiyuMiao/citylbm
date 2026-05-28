using System;
using System.Drawing;
using Grasshopper.Kernel;
using Rhino.Geometry;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Scene
{
    /// <summary>
    /// 绝对尺寸计算域组件
    /// 直接输入 Lx / Ly / Lz 三个方向的物理长度定义计算域。
    ///   - XY 平面：以建筑群包围盒中心为对称中心
    ///   - Z 方向：从地面 (Z=0) 向上延伸至 Lz
    /// 
    /// 与 Domain Designer（偏移量模式）的区别：
    ///   Domain Designer 以建筑包围盒底面中心为基准，输入各方向的偏移距离。
    ///   Absolute Domain 以建筑群中心为基准，直接输入总长度，更直观。
    /// </summary>
    public class AbsoluteDomainComponent : GH_Component
    {
        public AbsoluteDomainComponent()
            : base("Absolute Domain", "AbsDom",
                   "用绝对尺寸定义计算域（默认：500m×500m×100m 城市风场）。\n\n" +
                   "输入 Lx / Ly / Lz 三个方向的物理长度 (m)：\n" +
                   "  XY 平面以建筑群中心为对称中心\n" +
                   "  Z 方向从地面 (Z=0) 向上至 Lz\n\n" +
                   "连接 Scene 端子后自动替换自动扩展模式。\n" +
                   "如需恢复自动扩展，断开此电池即可。",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM 场景对象（需先添加建筑物）", GH_ParamAccess.item);

            pManager.AddNumberParameter("Length X", "Lx",
                "X 方向总长度 (m)\n" +
                "以建筑群中心为对称中心，向两侧各延伸 Lx/2\n" +
                "默认500m（适合城市风场模拟）",
                GH_ParamAccess.item, 500.0);

            pManager.AddNumberParameter("Length Y", "Ly",
                "Y 方向总长度 (m)\n" +
                "以建筑群中心为对称中心，向两侧各延伸 Ly/2\n" +
                "默认500m（适合城市风场模拟）",
                GH_ParamAccess.item, 500.0);

            pManager.AddNumberParameter("Height", "Lz",
                "计算域总高度 (m)\n" +
                "从地面 (Z=0) 向上延伸至 Lz\n" +
                "默认100m（适合城市风环境）",
                GH_ParamAccess.item, 100.0);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "更新后的 CityLBM 场景对象", GH_ParamAccess.item);
            pManager.AddBrepParameter("Domain Box", "Box", "计算域包围盒可视化（半透明蓝色方块）", GH_ParamAccess.item);
            pManager.AddTextParameter("Domain Info", "Info", "计算域尺寸信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 获取 Scene
            GH_Scene ghScene = null;
            if (!DA.GetData(0, ref ghScene) || ghScene == null || !ghScene.IsValid)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "需要有效的场景对象（需先添加建筑物）");
                return;
            }

            Core.Scene scene = ghScene.Value;

            if (scene.BuildingMeshes.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "场景中没有建筑物，请先用 Add Buildings 添加建筑");
                return;
            }

            // 读取尺寸参数
            double lx = 500.0, ly = 500.0, lz = 100.0;
            DA.GetData(1, ref lx);
            DA.GetData(2, ref ly);
            DA.GetData(3, ref lz);

            // 验证
            if (lx <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Lx 必须大于 0");
                return;
            }
            if (ly <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Ly 必须大于 0");
                return;
            }
            if (lz <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Lz 必须大于 0");
                return;
            }

            // 创建 AbsoluteDomainDefinition
            var absDomain = new AbsoluteDomainDefinition
            {
                Lx = lx,
                Ly = ly,
                Lz = lz
            };

            // 应用到 Scene
            scene.SetAbsoluteDomain(absDomain);

            // 获取计算域
            BoundingBox domainBox = scene.GetSimulationDomain();
            double centerX = (scene.Bounds.Min.X + scene.Bounds.Max.X) / 2.0;
            double centerY = (scene.Bounds.Min.Y + scene.Bounds.Max.Y) / 2.0;
            double buildingH = scene.Bounds.Max.Z - scene.Bounds.Min.Z;

            // 检查是否包含建筑物（修复：Z 方向允许建筑底面紧贴地面）
            bool containsXY = domainBox.Min.X <= scene.Bounds.Min.X && domainBox.Max.X >= scene.Bounds.Max.X &&
                             domainBox.Min.Y <= scene.Bounds.Min.Y && domainBox.Max.Y >= scene.Bounds.Max.Y;
            bool containsZ = domainBox.Max.Z >= scene.Bounds.Max.Z;
            bool zBottomOK = scene.Bounds.Min.Z >= -0.001;

            if (!containsXY || !containsZ || !zBottomOK)
            {
                string issues = "";
                if (!containsXY) issues += "Lx/Ly 不足；";
                if (!containsZ) issues += "Lz 高度不足；";
                if (!zBottomOK) issues += "建筑底部低于地面；";

                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    "计算域未完全包含建筑物！\n" +
                    $"问题：{issues}\n" +
                    $"建筑 XY 范围: [{scene.Bounds.Min.X:F1}, {scene.Bounds.Max.X:F1}] x [{scene.Bounds.Min.Y:F1}, {scene.Bounds.Max.Y:F1}]\n" +
                    $"域 XY 范围:   [{domainBox.Min.X:F1}, {domainBox.Max.X:F1}] x [{domainBox.Min.Y:F1}, {domainBox.Max.Y:F1}]\n" +
                    "提示：建筑底面可以紧贴 Z=0。");
            }

            // 可视化 Brep
            var brepBox = new Box(Plane.WorldXY,
                new Interval(domainBox.Min.X, domainBox.Max.X),
                new Interval(domainBox.Min.Y, domainBox.Max.Y),
                new Interval(domainBox.Min.Z, domainBox.Max.Z));
            Brep domainBrep = brepBox.ToBrep();

            // 信息文本
            double dz = domainBox.Max.Z - domainBox.Max.Z; // =0 since Z_min=0, Z_max=Lz
            string info = string.Format(
                "=== Absolute Domain ===\n" +
                "Lx = {0:F2} m  (X: [{1:F2}, {2:F2}])\n" +
                "Ly = {3:F2} m  (Y: [{4:F2}, {5:F2}])\n" +
                "Lz = {6:F2} m  (Z: [{7:F2}, {8:F2}])\n\n" +
                "建筑群中心: ({9:F2}, {10:F2})\n" +
                "建筑高度:   {11:F2} m\n" +
                "域高/建筑高: {12:F1}",
                lx, domainBox.Min.X, domainBox.Max.X,
                ly, domainBox.Min.Y, domainBox.Max.Y,
                lz, domainBox.Min.Z, domainBox.Max.Z,
                centerX, centerY,
                buildingH,
                buildingH > 0 ? lz / buildingH : 0
            );

            // 输出
            DA.SetData(0, new GH_Scene(scene));
            DA.SetData(1, domainBrep);
            DA.SetData(2, info);
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("DomainDesigner.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("A1B2C3D4-E5F6-7890-ABCD-EF1234567890"); }
        }

        public override GH_Exposure Exposure
        {
            get { return GH_Exposure.tertiary; }
        }
    }
}
