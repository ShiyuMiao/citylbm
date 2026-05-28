using System;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Scene
{
    /// <summary>
    /// 计算域设计组件
    /// 允许用户自定义模拟计算域的大小和位置
    /// 
    /// 坐标系约定（与 Rhino/CityLBM 一致）：
    ///   X = 流向（来流方向）
    ///   Y = 展向
    ///   Z = 竖直向上
    ///   地面 = Z = 0 平面
    /// 
    /// 基准点 (Base Point) 定义：
    ///   建筑物包围盒底面中心在地面 (Z=0) 上的投影点
    ///   BaseX = (建筑群 X_min + X_max) / 2
    ///   BaseY = (建筑群 Y_min + Y_max) / 2
    ///   BaseZ = 0（地面）
    /// 
    /// 计算域对齐方式：
    ///   X 方向：以基准点为中心，-X 为上游（逆风），+X 为下游（顺风）
    ///     X Minus = 基准点到上游边界的距离
    ///     X Plus  = 基准点到下游边界的距离
    ///   Y 方向：以基准点为中心，向两侧对称或不对称扩展
    ///     Y Minus = 基准点到 -Y 侧边界的距离
    ///     Y Plus  = 基准点到 +Y 侧边界的距离
    ///   Z 方向：从地面 (Z=0) 向上延伸
    ///     Height = 计算域总高度
    /// </summary>
    public class DomainDesignerComponent : GH_Component
    {
        public DomainDesignerComponent()
            : base("Domain Designer", "Domain",
                   "自定义模拟计算域的大小和位置（默认：500m×500m×100m 城市风场）。\n" +
                   "基准点为建筑物包围盒底面中心在地面(Z=0)上的投影。\n" +
                   "X方向: -X为上游(逆风), +X为下游(顺风)。\n" +
                   "Y方向: 展向两侧扩展。\n" +
                   "Z方向: 从地面向上延伸。",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM场景对象（需先添加建筑物）", GH_ParamAccess.item);

            // X 方向（流向）
            pManager.AddNumberParameter("X Minus", "X-", "上游距离（逆风方向，单位m）\n从基准点到计算域-X边界的距离\n默认200m（适合500m×500m城市风场）", GH_ParamAccess.item, 200.0);
            pManager.AddNumberParameter("X Plus", "X+", "下游距离（顺风方向，单位m）\n从基准点到计算域+X边界的距离\n默认300m（适合500m×500m城市风场）", GH_ParamAccess.item, 300.0);

            // Y 方向（展向）
            pManager.AddNumberParameter("Y Minus", "Y-", "展向-距离（单位m）\n从基准点到计算域-Y边界的距离\n默认250m（适合500m×500m城市风场）", GH_ParamAccess.item, 250.0);
            pManager.AddNumberParameter("Y Plus", "Y+", "展向+距离（单位m）\n从基准点到计算域+Y边界的距离\n默认250m（适合500m×500m城市风场）", GH_ParamAccess.item, 250.0);

            // Z 方向（高度）
            pManager.AddNumberParameter("Height", "H", "计算域总高度（从地面向上，单位m）\n默认100m（适合城市风环境模拟）", GH_ParamAccess.item, 100.0);

            // 可选：自动按建筑高度H的倍数设置
            pManager.AddNumberParameter("Auto Scale", "S", "自动缩放因子（可选）\n输入后，X-/X+/Y-/Y+/Height 将乘以此因子\n输入0或负数则忽略", GH_ParamAccess.item, 0.0);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "更新后的CityLBM场景对象", GH_ParamAccess.item);
            pManager.AddPointParameter("Base Point", "BP", "计算域基准点\n（建筑物包围盒底面中心在地面上的投影）", GH_ParamAccess.item);
            pManager.AddBrepParameter("Domain Box", "Box", "计算域包围盒可视化\n（半透明蓝色方块）", GH_ParamAccess.item);
            pManager.AddTextParameter("Domain Info", "Info", "计算域信息文本\n（尺寸和对齐详情）", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // ===== 获取 Scene =====
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

            // ===== 读取距离参数 =====
            double xMinus = 200.0, xPlus = 300.0;
            double yMinus = 250.0, yPlus = 250.0;
            double height = 100.0;
            double autoScale = 0.0;

            DA.GetData(1, ref xMinus);
            DA.GetData(2, ref xPlus);
            DA.GetData(3, ref yMinus);
            DA.GetData(4, ref yPlus);
            DA.GetData(5, ref height);
            DA.GetData(6, ref autoScale);

            // ===== 自动缩放 =====
            if (autoScale > 0)
            {
                double buildingHeight = scene.Bounds.Max.Z - scene.Bounds.Min.Z;
                double scale = buildingHeight * autoScale;
                xMinus *= scale;
                xPlus *= scale;
                yMinus *= scale;
                yPlus *= scale;
                height *= scale;

                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"自动缩放: 建筑高度={buildingHeight:F3}m × {autoScale:F1} = 缩放因子 {scale:F3}m");
            }

            // ===== 验证 =====
            if (xMinus <= 0 || xPlus <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "X 方向距离必须大于0");
                return;
            }
            if (yMinus <= 0 || yPlus <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Y 方向距离必须大于0");
                return;
            }
            if (height <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "计算域高度必须大于0");
                return;
            }

            // ===== 创建 DomainDefinition =====
            var domainDef = new DomainDefinition
            {
                XMinus = xMinus,
                XPlus = xPlus,
                YMinus = yMinus,
                YPlus = yPlus,
                Height = height
            };

            // ===== 应用到 Scene =====
            scene.SetCustomDomain(domainDef);

            // ===== 获取计算域信息 =====
            BoundingBox domainBox = scene.GetSimulationDomain();
            Point3d basePoint = scene.GetDomainBasePoint();

            // ===== 检查计算域是否包含建筑物 =====
            // 修复：Z 方向允许建筑底面紧贴地面（Z=0），只检查 XY 平面和 Z 正方向
            bool containsXY = domainBox.Min.X <= scene.Bounds.Min.X && domainBox.Max.X >= scene.Bounds.Max.X &&
                             domainBox.Min.Y <= scene.Bounds.Min.Y && domainBox.Max.Y >= scene.Bounds.Max.Y;
            bool containsZ = domainBox.Max.Z >= scene.Bounds.Max.Z; // 只检查顶部是否足够高
            // Z 底部：允许建筑从 Z=0 开始，即使 domainBox.Min.Z=0 且 scene.Bounds.Min.Z=0
            bool zBottomOK = scene.Bounds.Min.Z >= -0.001; // 允许微小负值（浮点误差）

            if (!containsXY || !containsZ || !zBottomOK)
            {
                string issues = "";
                if (!containsXY) issues += "XY 平面范围不足；";
                if (!containsZ) issues += "Z 方向顶部高度不足；";
                if (!zBottomOK) issues += "建筑底部低于地面（Z<0）；";

                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    "⚠️ 计算域未完全包含建筑物！\n" +
                    $"问题：{issues}\n" +
                    $"建筑物范围: X[{scene.Bounds.Min.X:F3}, {scene.Bounds.Max.X:F3}], " +
                    $"Y[{scene.Bounds.Min.Y:F3}, {scene.Bounds.Max.Y:F3}], " +
                    $"Z[{scene.Bounds.Min.Z:F3}, {scene.Bounds.Max.Z:F3}]\n" +
                    $"计算域范围: X[{domainBox.Min.X:F3}, {domainBox.Max.X:F3}], " +
                    $"Y[{domainBox.Min.Y:F3}, {domainBox.Max.Y:F3}], " +
                    $"Z[{domainBox.Min.Z:F3}, {domainBox.Max.Z:F3}]\n" +
                    "提示：建筑底面可以紧贴 Z=0，但必须保证 XY 平面和 Z 顶部在域内。");
            }

            // ===== 创建可视化 Brep =====
            Brep domainBrep = CreateDomainVisualizationBox(domainBox);

            // ===== 生成信息文本 =====
            string info = GenerateDomainInfo(domainDef, scene, domainBox, basePoint);

            // ===== 输出 =====
            DA.SetData(0, new GH_Scene(scene));
            DA.SetData(1, basePoint);
            DA.SetData(2, domainBrep);
            DA.SetData(3, info);
        }

        /// <summary>
        /// 创建计算域可视化方块
        /// </summary>
        private Brep CreateDomainVisualizationBox(BoundingBox box)
        {
            var brepBox = new Box(Plane.WorldXY,
                new Interval(box.Min.X, box.Max.X),
                new Interval(box.Min.Y, box.Max.Y),
                new Interval(box.Min.Z, box.Max.Z));
            return brepBox.ToBrep();
        }

        /// <summary>
        /// 生成计算域信息文本
        /// </summary>
        private string GenerateDomainInfo(DomainDefinition domDef, Core.Scene scene,
            BoundingBox domainBox, Point3d basePoint)
        {
            double dx = domainBox.Max.X - domainBox.Min.X;
            double dy = domainBox.Max.Y - domainBox.Min.Y;
            double dz = domainBox.Max.Z - domainBox.Min.Z;
            double buildingH = scene.Bounds.Max.Z - scene.Bounds.Min.Z;

            return string.Format(
                "═══ CityLBM 计算域定义 ═══\n" +
                "✓ 已应用自定义计算域 (UseCustomDomain = true)\n\n" +
                "基准点 (Base Point):\n" +
                "  位置: 建筑物包围盒底面中心在地面(Z=0)上的投影\n" +
                "  坐标: ({0:F3}, {1:F3}, {2:F3})\n\n" +
                "计算域尺寸:\n" +
                "  X方向: {3:F3} m (上游{4:F3}m + 下游{5:F3}m)\n" +
                "  Y方向: {6:F3} m (两侧各{7:F3}m + {8:F3}m)\n" +
                "  Z方向: {9:F3} m (高度)\n\n" +
                "计算域范围:\n" +
                "  X: [{10:F3}, {11:F3}]\n" +
                "  Y: [{12:F3}, {13:F3}]\n" +
                "  Z: [{14:F3}, {15:F3}]\n\n" +
                "建筑物高度: {16:F3} m\n" +
                "建筑高/域高比: {17:F2}\n" +
                "风向上游/建筑高比: {18:F1}H\n" +
                "风向下游/建筑高比: {19:F1}H",
                basePoint.X, basePoint.Y, basePoint.Z,
                dx, domDef.XMinus, domDef.XPlus,
                dy, domDef.YMinus, domDef.YPlus,
                dz,
                domainBox.Min.X, domainBox.Max.X,
                domainBox.Min.Y, domainBox.Max.Y,
                domainBox.Min.Z, domainBox.Max.Z,
                buildingH,
                buildingH > 0 ? dz / buildingH : 0,
                buildingH > 0 ? domDef.XMinus / buildingH : 0,
                buildingH > 0 ? domDef.XPlus / buildingH : 0
            );
        }

        protected override Bitmap Icon
        {
            get
            {
                return IconLoader.Load("DomainDesigner.png");
            }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("E5A2B8C1-3D7F-4A6E-B9C0-1F8D5E3A7B2C"); }
        }

        public override GH_Exposure Exposure
        {
            // 开发阶段显示为实验性
            get { return GH_Exposure.tertiary; }
        }
    }
}
