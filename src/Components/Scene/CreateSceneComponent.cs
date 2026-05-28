using System;
using System.Drawing;
using Grasshopper.Kernel;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Scene
{
    /// <summary>
    /// 创建CityLBM场景组件
    /// 支持风廓线类型选择：均匀 / 幂律 / 对数律
    /// 风廓线通过"参考高度处已知风速"自动推算全域风速分布
    /// </summary>
    public class CreateSceneComponent : GH_Component
    {
        public CreateSceneComponent()
            : base("Create Scene", "Scene",
                   "创建 CityLBM 城市风场模拟场景。\n\n" +
                   "【风廓线输入逻辑】（默认：幂律风廓线，适合城市风环境）\n" +
                   "输入参考高度 Zr 处的已知风速 V，插件自动推算整个计算域的竖向风速分布：\n" +
                   "  Uniform(0)  — 全域均匀风速（风速=V，忽略高度）\n" +
                   "  PowerLaw(1) — 幂律：U(z) = V × (z/Zr)^α（默认，城市风环境推荐）\n" +
                   "  Log(2)      — 对数律：U(z) = (u*/κ)×ln(z/z₀)，由V@Zr反推u*\n\n" +
                   "【粗糙度类别 GB 50009】\n" +
                   "  A(0)=近海 α=0.12 z₀=0.01m\n" +
                   "  B(1)=田野 α=0.15 z₀=0.05m\n" +
                   "  C(2)=城市 α=0.22 z₀=0.30m（默认）\n" +
                   "  D(3)=密集城市 α=0.30 z₀=1.00m\n" +
                   "  99=自定义 z₀",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter("Name", "N", "场景名称", GH_ParamAccess.item, "CityLBM Scene");

            pManager.AddNumberParameter("Wind Speed", "V",
                "参考高度 Zr 处的已知风速 (m/s)\n" +
                "→ 插件以此为基准自动推算全域风廓线\n" +
                "  Uniform模式: 全域均匀该风速\n" +
                "  PowerLaw:    V = U_ref @ Zr\n" +
                "  Log:         V = U(Zr)，反推摩擦速度 u*",
                GH_ParamAccess.item, 5.0);

            pManager.AddVectorParameter("Wind Direction", "D",
                "风场方向（单位向量，默认+X方向）",
                GH_ParamAccess.item, new Rhino.Geometry.Vector3d(1, 0, 0));

            pManager.AddIntegerParameter("Wind Profile", "WP",
                "风廓线类型\n" +
                "0 = Uniform — 均匀来流（忽略高度，向后兼容）\n" +
                "1 = PowerLaw — 幂律风廓线 U=V×(z/Zr)^α（默认，城市风环境推荐）\n" +
                "2 = Logarithmic — 对数律 U=(u*/κ)×ln(z/z₀)",
                GH_ParamAccess.item, 1);

            pManager.AddNumberParameter("Reference Height", "Zr",
                "参考高度 z_ref (m)\n" +
                "Wind Speed 的测量/已知高度\n" +
                "默认 10m（标准气象站测风高度）",
                GH_ParamAccess.item, 10.0);

            pManager.AddIntegerParameter("Roughness Category", "RC",
                "地面粗糙度类别（GB 50009-2012）\n" +
                "A(0)=近海 z₀=0.01m α=0.12\n" +
                "B(1)=田野 z₀=0.05m α=0.15\n" +
                "C(2)=城市 z₀=0.30m α=0.22（默认）\n" +
                "D(3)=密集城市 z₀=1.00m α=0.30\n" +
                "99=自定义（需连接 Z0 端子）",
                GH_ParamAccess.item, 2);

            pManager.AddNumberParameter("Roughness Length", "Z0",
                "自定义粗糙度长度 z₀ (m)\n" +
                "仅当 Roughness Category=99 时生效\n" +
                "其他类别由 RC 自动设定，此输入忽略",
                GH_ParamAccess.item, 0.3);

            pManager.AddNumberParameter("Domain Extension", "E",
                "计算域自动扩展比例 (0~1)\n" +
                "相对于建筑包围盒对角线长度的百分比\n" +
                "仅在未连接 Domain Designer 时生效",
                GH_ParamAccess.item, 0.2);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM 场景对象", GH_ParamAccess.item);
            pManager.AddTextParameter("Profile Info", "Info",
                "风廓线参数摘要（方便确认推算结果）", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string name = "CityLBM Scene";
            double windSpeed = 5.0;
            Rhino.Geometry.Vector3d windDir = new Rhino.Geometry.Vector3d(1, 0, 0);
            int windProfileInt = 1;  // 默认使用幂律风廓线
            double refHeight = 10.0;
            int roughnessCategoryInt = 2;  // 默认城市类别
            double roughnessLength = 0.3;
            double extension = 0.2;

            if (!DA.GetData(0, ref name)) return;
            if (!DA.GetData(1, ref windSpeed)) return;
            if (!DA.GetData(2, ref windDir)) return;
            if (!DA.GetData(3, ref windProfileInt)) return;
            if (!DA.GetData(4, ref refHeight)) return;
            if (!DA.GetData(5, ref roughnessCategoryInt)) return;
            if (!DA.GetData(6, ref roughnessLength)) return;
            if (!DA.GetData(7, ref extension)) return;

            // 验证风速
            if (windSpeed <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "风速必须大于 0");
                return;
            }
            if (refHeight <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "参考高度 Zr 必须大于 0");
                return;
            }

            // 解析风廓线类型
            WindProfileType windProfile;
            if (windProfileInt >= 0 && windProfileInt <= 2)
                windProfile = (WindProfileType)windProfileInt;
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "无效的风廓线类型，已重置为 Uniform(0)");
                windProfile = WindProfileType.Uniform;
            }

            // 解析粗糙度类别，自动获取 z0 / alpha
            RoughnessCategory roughnessCategory;
            double z0, alpha;

            if (roughnessCategoryInt == 99)
            {
                roughnessCategory = RoughnessCategory.Custom;
                if (roughnessLength <= 0)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "自定义 z₀ 必须 > 0，已重置为 0.3m (C类)");
                    roughnessLength = 0.3;
                }
                z0 = roughnessLength;
                alpha = 0.22; // 自定义时 alpha 默认取 C 类（也可额外添加输入端子）
            }
            else if (roughnessCategoryInt >= 0 && roughnessCategoryInt <= 3)
            {
                roughnessCategory = (RoughnessCategory)roughnessCategoryInt;
                var rp = Core.Scene.GetRoughnessParams(roughnessCategory);
                z0 = rp.Item1;
                alpha = rp.Item2;
                roughnessLength = z0;
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "无效的粗糙度类别，已使用默认 C 类（城市）");
                roughnessCategory = RoughnessCategory.C;
                var rp = Core.Scene.GetRoughnessParams(RoughnessCategory.C);
                z0 = rp.Item1;
                alpha = rp.Item2;
                roughnessLength = z0;
            }

            // 参考高度警告
            if (windProfile != WindProfileType.Uniform && refHeight < 1.0)
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "参考高度较小，建议使用标准气象站高度 10m");

            // 对数律：检查 z_ref > z0，否则无法推算 u*
            if (windProfile == WindProfileType.Logarithmic && refHeight <= z0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    $"对数律要求参考高度 Zr ({refHeight:F2}m) > z₀ ({z0:F3}m)，请增大 Zr 或减小 z₀");
                return;
            }

            // 推算对数律摩擦速度 u*（从参考高度处已知风速反推）
            double kappa = 0.41;
            double uStar = 0;
            if (windProfile == WindProfileType.Logarithmic)
            {
                uStar = windSpeed * kappa / Math.Log(refHeight / z0);
            }

            // 创建场景
            Core.Scene scene = new Core.Scene(name);
            scene.WindSpeed = windSpeed;
            scene.DomainExtensionRatio = extension;

            if (windDir.IsValid && !windDir.IsZero)
            {
                windDir.Unitize();
                scene.WindDirection = windDir;
            }

            scene.WindProfile = windProfile;
            scene.ReferenceHeight = Math.Max(refHeight, 0.1);
            scene.RoughnessCategory = roughnessCategory;
            scene.RoughnessLength = z0;
            scene.PowerLawAlpha = alpha;
            scene.VonKarmanConstant = kappa;

            // 生成风廓线参数摘要
            string profileInfo = BuildProfileInfo(windProfile, windSpeed, refHeight, z0, alpha, uStar, kappa);

            DA.SetData(0, new GH_Scene(scene));
            DA.SetData(1, profileInfo);
        }

        /// <summary>
        /// 构建风廓线参数摘要文本，方便用户确认推算结果
        /// </summary>
        private string BuildProfileInfo(WindProfileType profile, double V, double Zr,
                                         double z0, double alpha, double uStar, double kappa)
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("═══ 风廓线参数摘要 ═══");
            sb.AppendLine($"类型: {profile}");
            sb.AppendLine($"参考风速 V = {V:F2} m/s @ Zr = {Zr:F1} m");

            switch (profile)
            {
                case WindProfileType.Uniform:
                    sb.AppendLine("全域均匀风速，忽略高度变化");
                    sb.AppendLine($"U(z) = {V:F2} m/s（常数）");
                    break;

                case WindProfileType.PowerLaw:
                    sb.AppendLine($"粗糙度指数 α = {alpha:F2}");
                    sb.AppendLine($"公式: U(z) = {V:F2} × (z/{Zr:F1})^{alpha:F2}");
                    sb.AppendLine($"示例: U(5m) = {V * Math.Pow(5.0 / Zr, alpha):F2} m/s");
                    sb.AppendLine($"      U(10m) = {V * Math.Pow(10.0 / Zr, alpha):F2} m/s");
                    sb.AppendLine($"      U(30m) = {V * Math.Pow(30.0 / Zr, alpha):F2} m/s");
                    sb.AppendLine($"      U(50m) = {V * Math.Pow(50.0 / Zr, alpha):F2} m/s");
                    break;

                case WindProfileType.Logarithmic:
                    sb.AppendLine($"粗糙度长度 z₀ = {z0:F3} m");
                    sb.AppendLine($"von Kármán κ = {kappa:F2}");
                    sb.AppendLine($"摩擦速度 u* = {uStar:F4} m/s（由V@Zr反推）");
                    sb.AppendLine($"公式: U(z) = ({uStar:F4}/{kappa:F2})×ln(z/{z0:F3})");
                    if (5.0 > z0) sb.AppendLine($"示例: U(5m) = {(uStar / kappa) * Math.Log(5.0 / z0):F2} m/s");
                    sb.AppendLine($"      U(10m) = {(uStar / kappa) * Math.Log(10.0 / z0):F2} m/s");
                    sb.AppendLine($"      U(30m) = {(uStar / kappa) * Math.Log(30.0 / z0):F2} m/s");
                    sb.AppendLine($"      U(50m) = {(uStar / kappa) * Math.Log(50.0 / z0):F2} m/s");
                    break;
            }
            return sb.ToString().TrimEnd();
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("CreateScene.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A"); }
        }
    }
}

