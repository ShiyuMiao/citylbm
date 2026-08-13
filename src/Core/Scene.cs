using System;
using System.Collections.Generic;
using Rhino.Geometry;

namespace CityLBM.Core
{
    /// <summary>
    /// 风廓线类型
    /// </summary>
    public enum WindProfileType
    {
        /// <summary>均匀来流（默认，向后兼容）</summary>
        Uniform = 0,
        /// <summary>幂律风廓线：U(z) = U_ref × (z / z_ref)^α</summary>
        PowerLaw = 1,
        /// <summary>对数律风廓线：U(z) = (u* / κ) × ln(z / z₀)</summary>
        Logarithmic = 2,
        CustomTable = 3
    }

    public class WindProfileSample
    {
        public double Z { get; set; }
        public double U { get; set; }
        public bool HasK { get; set; }
        public double K { get; set; }
    }

    /// <summary>
    /// 地面粗糙度类别（基于 GB 50009-2012 建筑结构荷载规范）
    /// </summary>
    public enum RoughnessCategory
    {
        /// <summary>A 类：近海海面、海岛、海岸、湖岸及沙漠地区（z₀=0.01m, α=0.12）</summary>
        A = 0,
        /// <summary>B 类：田野、乡村、丛林、丘陵及房屋比较稀疏的乡镇（z₀=0.05m, α=0.15）</summary>
        B = 1,
        /// <summary>C 类：有密集建筑群的城市市区（z₀=0.3m, α=0.22）</summary>
        C = 2,
        /// <summary>D 类：有密集建筑群且房屋较高的城市市区（z₀=1.0m, α=0.30）</summary>
        D = 3,
        /// <summary>自定义：用户手动指定 z₀ 和 α</summary>
        Custom = 99
    }

    /// <summary>
    /// CityLBM 场景类
    /// 管理城市风场模拟的场景数据，包括建筑物、边界条件、风场参数等
    /// </summary>
    public class Scene
    {
        #region Properties

        /// <summary>
        /// 场景名称
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// 场景边界框（建筑物包围盒）
        /// </summary>
        public BoundingBox Bounds { get; private set; }

        /// <summary>
        /// 建筑物Mesh集合
        /// </summary>
        public List<Mesh> BuildingMeshes { get; private set; }

        /// <summary>
        /// 风场方向
        /// </summary>
        public Vector3d WindDirection { get; set; }

        /// <summary>
        /// 风场速度 (m/s)
        /// 当 WindProfileType != Uniform 时，此值作为参考高度处的风速 U_ref
        /// </summary>
        public double WindSpeed { get; set; }

        /// <summary>
        /// 地面高度（Z=0平面）
        /// </summary>
        public double GroundHeight { get; set; }

        /// <summary>
        /// 风廓线类型（默认 Uniform 向后兼容）
        /// </summary>
        public WindProfileType WindProfile { get; set; }

        public string WindProfileCsvPath { get; set; }

        public List<WindProfileSample> CustomWindProfile { get; set; }

        /// <summary>
        /// 参考高度 z_ref (m)
        /// 风廓线的参考高度，WindSpeed 在此高度处等于 U_ref
        /// 默认 10m（标准气象站测风高度）
        /// </summary>
        public double ReferenceHeight { get; set; }

        /// <summary>
        /// 地面粗糙度类别（默认 C 类：有密集建筑群的城市市区）
        /// </summary>
        public RoughnessCategory RoughnessCategory { get; set; }

        /// <summary>
        /// 地面粗糙度长度 z₀ (m)
        /// 用于对数律风廓线和幂律指数推导
        /// </summary>
        public double RoughnessLength { get; set; }

        /// <summary>
        /// 幂律风廓线指数 α
        /// U(z) = U_ref × (z / z_ref)^α
        /// </summary>
        public double PowerLawAlpha { get; set; }

        /// <summary>
        /// von Kármán 常数 κ（默认 0.41，对数律风廓线使用）
        /// </summary>
        public double VonKarmanConstant { get; set; }

        /// <summary>
        /// 根据粗糙度类别自动获取粗糙度参数（z₀, α）
        /// </summary>
        /// <returns>元组 (z₀ in meters, α exponent)</returns>
        public static Tuple<double, double> GetRoughnessParams(RoughnessCategory category)
        {
            switch (category)
            {
                case RoughnessCategory.A: return Tuple.Create(0.01, 0.12);
                case RoughnessCategory.B: return Tuple.Create(0.05, 0.15);
                case RoughnessCategory.C: return Tuple.Create(0.30, 0.22);
                case RoughnessCategory.D: return Tuple.Create(1.00, 0.30);
                default: return Tuple.Create(0.30, 0.22); // 默认 C 类
            }
        }

        /// <summary>
        /// 计算指定高度处的风速（基于当前风廓线设置）
        /// </summary>
        /// <param name="height">距地面高度 z (m)</param>
        /// <returns>该高度处的风速 (m/s)</returns>
        public double GetWindSpeedAtHeight(double height)
        {
            if (height <= 0) return 0;

            switch (WindProfile)
            {
                case WindProfileType.Uniform:
                    return WindSpeed;

                case WindProfileType.PowerLaw:
                    // U(z) = U_ref × (z / z_ref)^α
                    double zRef = Math.Max(ReferenceHeight, 0.1);
                    return WindSpeed * Math.Pow(height / zRef, PowerLawAlpha);

                case WindProfileType.Logarithmic:
                    // U(z) = (u* / κ) × ln(z / z₀)
                    // 由 U(z_ref) = U_ref 反推 u*
                    double z0 = Math.Max(RoughnessLength, 1e-6);
                    double kappa = Math.Max(VonKarmanConstant, 0.1);
                    double zRefLog = Math.Max(ReferenceHeight, 0.1);
                    double uStar = WindSpeed * kappa / Math.Log(zRefLog / z0);
                    return (uStar / kappa) * Math.Log(height / z0);

                case WindProfileType.CustomTable:
                    return InterpolateCustomWindSpeed(height);

                default:
                    return WindSpeed;
            }
        }

        public double? GetTurbulentKAtHeight(double height)
        {
            if (CustomWindProfile == null || CustomWindProfile.Count == 0)
                return null;

            var samples = CustomWindProfile.FindAll(s => s.HasK);
            if (samples.Count == 0)
                return null;

            if (height <= samples[0].Z) return Math.Max(0.0, samples[0].K);
            if (height >= samples[samples.Count - 1].Z) return Math.Max(0.0, samples[samples.Count - 1].K);

            for (int i = 0; i < samples.Count - 1; i++)
            {
                var a = samples[i];
                var b = samples[i + 1];
                if (height >= a.Z && height <= b.Z)
                {
                    double t = (height - a.Z) / Math.Max(b.Z - a.Z, 1.0e-12);
                    return Math.Max(0.0, a.K + t * (b.K - a.K));
                }
            }

            return null;
        }

        private double InterpolateCustomWindSpeed(double height)
        {
            if (CustomWindProfile == null || CustomWindProfile.Count == 0)
                return WindSpeed;

            var samples = CustomWindProfile;
            if (height <= samples[0].Z) return Math.Max(0.0, samples[0].U);
            if (height >= samples[samples.Count - 1].Z) return Math.Max(0.0, samples[samples.Count - 1].U);

            for (int i = 0; i < samples.Count - 1; i++)
            {
                var a = samples[i];
                var b = samples[i + 1];
                if (height >= a.Z && height <= b.Z)
                {
                    double t = (height - a.Z) / Math.Max(b.Z - a.Z, 1.0e-12);
                    return Math.Max(0.0, a.U + t * (b.U - a.U));
                }
            }

            return WindSpeed;
        }

        /// <summary>
        /// 模拟区域扩展比例（相对于建筑物边界框）
        /// 保留向后兼容，当 UseCustomDomain=false 时生效
        /// </summary>
        public double DomainExtensionRatio { get; set; }

        /// <summary>
        /// 是否使用自定义计算域
        /// true: 使用 CustomDomain（由 DomainDesigner 组件设置）
        /// false: 使用 DomainExtensionRatio 自动扩展
        /// </summary>
        public bool UseCustomDomain { get; set; }

        /// <summary>
        /// 自定义计算域边界框
        /// 基准点为建筑物包围盒底面中心在地面的投影
        /// Domain 由各方向的偏移量定义
        /// </summary>
        public DomainDefinition? CustomDomain { get; set; }

        /// <summary>
        /// 是否使用绝对尺寸计算域（直接给 Lx/Ly/Lz）
        /// 优先级高于 UseCustomDomain（偏移量模式）
        /// </summary>
        public bool UseAbsoluteDomain { get; set; }

        /// <summary>
        /// 绝对尺寸计算域定义（Lx × Ly × Lz，以建筑群中心为 XY 中心，Z 从地面起）
        /// </summary>
        public AbsoluteDomainDefinition? AbsoluteDomain { get; set; }

        #endregion

        #region Constructor

        public Scene(string name = "CityLBM Scene")
        {
            Name = name;
            BuildingMeshes = new List<Mesh>();
            WindDirection = new Vector3d(1, 0, 0); // 默认X方向
            WindSpeed = 5.0; // 默认5 m/s
            GroundHeight = 0.0;
            DomainExtensionRatio = 0.2; // 默认扩展20%
            UseCustomDomain = false;
            CustomDomain = null;

            // 风廓线参数（默认幂律风廓线，适合城市风环境）
            WindProfile = WindProfileType.PowerLaw;
            ReferenceHeight = 10.0;     // 默认 10m 标准气象站高度
            RoughnessCategory = RoughnessCategory.C;  // 默认 C 类（城市密集建筑群）
            var roughnessParams = GetRoughnessParams(RoughnessCategory.C);
            RoughnessLength = roughnessParams.Item1;  // 0.30 m
            PowerLawAlpha = roughnessParams.Item2;    // 0.22
            VonKarmanConstant = 0.41;
            WindProfileCsvPath = "";
            CustomWindProfile = new List<WindProfileSample>();

            UseAbsoluteDomain = false;
            AbsoluteDomain = null;
        }

        #endregion

        #region Public Methods

        /// <summary>
        /// 添加建筑物Mesh到场景
        /// </summary>
        public void AddBuilding(Mesh mesh)
        {
            if (mesh == null || !mesh.IsValid)
            {
                throw new ArgumentException("Invalid mesh");
            }

            BuildingMeshes.Add(mesh);
            UpdateBounds();
        }

        /// <summary>
        /// 批量添加建筑物Mesh
        /// </summary>
        public void AddBuildings(IEnumerable<Mesh> meshes)
        {
            if (meshes == null) return;

            foreach (var mesh in meshes)
            {
                if (mesh != null && mesh.IsValid)
                {
                    BuildingMeshes.Add(mesh);
                }
            }

            UpdateBounds();
        }

        /// <summary>
        /// 设置风场条件
        /// </summary>
        public void SetWindCondition(Vector3d direction, double speed)
        {
            if (!direction.IsValid || direction.IsZero)
            {
                throw new ArgumentException("Invalid wind direction");
            }

            WindDirection = direction;
            WindDirection.Unitize();
            WindSpeed = Math.Abs(speed);
        }

        /// <summary>
        /// 设置自定义计算域
        /// </summary>
        public void SetCustomDomain(DomainDefinition domain)
        {
            CustomDomain = domain;
            UseCustomDomain = true;
            // 关闭绝对尺寸域模式（两者互斥）
            UseAbsoluteDomain = false;
        }

        /// <summary>
        /// 设置绝对尺寸计算域（Lx × Ly × Lz）
        /// </summary>
        public void SetAbsoluteDomain(AbsoluteDomainDefinition domain)
        {
            AbsoluteDomain = domain;
            UseAbsoluteDomain = true;
            // 关闭偏移量域模式（两者互斥）
            UseCustomDomain = false;
        }

        /// <summary>
        /// 清除自定义计算域，恢复为自动扩展模式
        /// </summary>
        public void ClearCustomDomain()
        {
            CustomDomain = null;
            UseCustomDomain = false;
            AbsoluteDomain = null;
            UseAbsoluteDomain = false;
        }

        /// <summary>
        /// 计算场景边界框
        /// </summary>
        public void CalculateBounds()
        {
            UpdateBounds();
        }

        /// <summary>
        /// 获取模拟计算域
        /// 优先级：AbsoluteDomain > CustomDomain（偏移量） > 自动扩展
        /// </summary>
        public BoundingBox GetSimulationDomain()
        {
            if (!Bounds.IsValid)
            {
                UpdateBounds();
            }

            // 优先：绝对尺寸域（Lx × Ly × Lz，以建筑群中心为 XY 中心）
            if (UseAbsoluteDomain && AbsoluteDomain.HasValue)
            {
                return AbsoluteDomain.Value.ComputeDomainBox(Bounds, GroundHeight);
            }

            // 次优先：偏移量自定义域
            if (UseCustomDomain && CustomDomain.HasValue)
            {
                return CustomDomain.Value.ComputeDomainBox(Bounds, GroundHeight);
            }

            // 自动扩展模式（向后兼容）
            double extension = DomainExtensionRatio * Bounds.Diagonal.Length;

            return new BoundingBox(
                new Point3d(Bounds.Min.X - extension, Bounds.Min.Y - extension, GroundHeight),
                new Point3d(Bounds.Max.X + extension, Bounds.Max.Y + extension, Bounds.Max.Z + extension)
            );
        }

        /// <summary>
        /// 获取计算域基准点信息（用于显示和调试）
        /// 基准点 = 建筑物包围盒底面中心在 Z=GroundHeight 平面上的投影
        /// </summary>
        public Point3d GetDomainBasePoint()
        {
            if (!Bounds.IsValid)
            {
                UpdateBounds();
            }

            double cx = (Bounds.Min.X + Bounds.Max.X) / 2.0;
            double cy = (Bounds.Min.Y + Bounds.Max.Y) / 2.0;

            return new Point3d(cx, cy, GroundHeight);
        }

        /// <summary>
        /// 获取场景统计信息
        /// </summary>
        public SceneStatistics GetStatistics()
        {
            int totalVertices = 0;
            int totalFaces = 0;

            foreach (var mesh in BuildingMeshes)
            {
                totalVertices += mesh.Vertices.Count;
                totalFaces += mesh.Faces.Count;
            }

            return new SceneStatistics
            {
                BuildingCount = BuildingMeshes.Count,
                TotalVertices = totalVertices,
                TotalFaces = totalFaces,
                DomainBounds = GetSimulationDomain(),
                WindSpeed = WindSpeed,
                WindDirection = WindDirection,
                UseCustomDomain = UseCustomDomain
            };
        }

        /// <summary>
        /// 验证场景有效性
        /// </summary>
        public bool Validate(out string errorMessage)
        {
            errorMessage = string.Empty;

            if (BuildingMeshes.Count == 0)
            {
                errorMessage = "场景中没有建筑物";
                return false;
            }

            if (!Bounds.IsValid)
            {
                errorMessage = "场景边界无效";
                return false;
            }

            if (WindSpeed <= 0)
            {
                errorMessage = "风速必须大于0";
                return false;
            }

            // 风廓线参数验证
            if (WindProfile != WindProfileType.Uniform)
            {
                if (ReferenceHeight <= 0)
                {
                    errorMessage = "参考高度 (ReferenceHeight) 必须大于0";
                    return false;
                }
                if (RoughnessLength <= 0 && WindProfile == WindProfileType.Logarithmic)
                {
                    errorMessage = "对数律风廓线的粗糙度长度 (RoughnessLength) 必须大于0";
                    return false;
                }
            }

            // 验证自定义计算域是否包含建筑物
            if (UseCustomDomain && CustomDomain.HasValue)
            {
                var domain = GetSimulationDomain();
                if (!domain.Contains(Bounds))
                {
                    AddRuntimeMessageWarning("计算域未完全包含建筑物包围盒，可能导致建筑被截断");
                }
            }

            return true;
        }

        private void AddRuntimeMessageWarning(string msg)
        {
            // 用于验证时的警告提示（由组件调用者展示）
        }

        #endregion

        #region Private Methods

        /// <summary>
        /// 更新场景边界框
        /// </summary>
        private void UpdateBounds()
        {
            if (BuildingMeshes.Count == 0)
            {
                Bounds = BoundingBox.Unset;
                return;
            }

            BoundingBox bounds = BuildingMeshes[0].GetBoundingBox(false);
            for (int i = 1; i < BuildingMeshes.Count; i++)
            {
                bounds.Union(BuildingMeshes[i].GetBoundingBox(false));
            }

            Bounds = bounds;
        }

        #endregion
    }

    /// <summary>
    /// 自定义计算域定义
    /// 
    /// 基准点 (Base Point):
    ///   建筑物包围盒底面中心在地面 (Z=GroundHeight) 上的投影点。
    ///   BaseX = (Bounds.Min.X + Bounds.Max.X) / 2
    ///   BaseY = (Bounds.Min.Y + Bounds.Max.Y) / 2
    ///   BaseZ = GroundHeight (默认 0)
    /// 
    /// 对齐方式:
    ///   - X/Y 方向：以基准点为中心向两侧对称扩展
    ///     domainX_min = BaseX - XMinus,  domainX_max = BaseX + XPlus
    ///     domainY_min = BaseY - YMinus,  domainY_max = BaseY + YPlus
    ///     （其中 XMinus/XPlus 是相对于基准点在 -X/+X 方向的距离，
    ///       当风向为 +X 时，XMinus = 上游距离，XPlus = 下游距离）
    ///   - Z 方向：从地面 (Z=0) 向上延伸
    ///     domainZ_min = GroundHeight (=0)
    ///     domainZ_max = GroundHeight + Height
    /// </summary>
    public struct DomainDefinition
    {
        /// <summary>
        /// 基准点到计算域 -X 边缘的距离（上游距离，逆风方向）
        /// </summary>
        public double XMinus { get; set; }

        /// <summary>
        /// 基准点到计算域 +X 边缘的距离（下游距离，顺风方向）
        /// </summary>
        public double XPlus { get; set; }

        /// <summary>
        /// 基准点到计算域 -Y 边缘的距离（展向左距离）
        /// </summary>
        public double YMinus { get; set; }

        /// <summary>
        /// 基准点到计算域 +Y 边缘的距离（展向右距离）
        /// </summary>
        public double YPlus { get; set; }

        /// <summary>
        /// 计算域总高度（从地面向上）
        /// </summary>
        public double Height { get; set; }

        /// <summary>
        /// 根据建筑物包围盒和地面高度计算实际计算域边界框
        /// 修复：基准点改为原点 (0, 0, 0)，不再以建筑物中心为基准
        /// </summary>
        public BoundingBox ComputeDomainBox(BoundingBox buildingBounds, double groundHeight)
        {
            // 基准点 = 原点 (0, 0, 0)
            return new BoundingBox(
                new Point3d(-XMinus, -YMinus, groundHeight),
                new Point3d(XPlus, YPlus, groundHeight + Height)
            );
        }

        /// <summary>
        /// 获取基准点坐标（修复：始终返回原点）
        /// </summary>
        public Point3d GetBasePoint(BoundingBox buildingBounds, double groundHeight)
        {
            return new Point3d(0, 0, groundHeight);
        }

        public override string ToString()
        {
            return $"Domain: X[-{XMinus:F2}, +{XPlus:F2}] Y[-{YMinus:F2}, +{YPlus:F2}] H={Height:F2}";
        }
    }

    /// <summary>
    /// 绝对尺寸计算域定义
    /// 
    /// 直接指定计算域三个方向的物理长度（米），Z 方向最小值固定为地面 (Z=0)。
    /// 计算域原点 (X_min, Y_min) 由建筑物包围盒中心决定：
    ///   X_min = BuildingCenter.X - Lx/2
    ///   Y_min = BuildingCenter.Y - Ly/2
    ///   Z_min = GroundHeight (=0)
    ///   Z_max = GroundHeight + Lz
    /// 
    /// 适用场景：
    ///   - 用户已知希望模拟的物理域尺寸（例如 200m × 200m × 100m）
    ///   - 不需要相对于建筑包围盒偏移，直接给绝对长度
    /// </summary>
    public struct AbsoluteDomainDefinition
    {
        /// <summary>X 方向总长度 (m)</summary>
        public double Lx { get; set; }

        /// <summary>Y 方向总长度 (m)</summary>
        public double Ly { get; set; }

        /// <summary>Z 方向总高度 (m)，从地面 (Z=0) 向上</summary>
        public double Lz { get; set; }

        /// <summary>
        /// 根据建筑物包围盒和地面高度计算实际计算域边界框
        /// 以建筑群中心为 XY 中心，Z 从地面向上
        /// </summary>
        public BoundingBox ComputeDomainBox(BoundingBox buildingBounds, double groundHeight)
        {
            double centerX = (buildingBounds.Min.X + buildingBounds.Max.X) / 2.0;
            double centerY = (buildingBounds.Min.Y + buildingBounds.Max.Y) / 2.0;

            return new BoundingBox(
                new Point3d(centerX - Lx / 2.0, centerY - Ly / 2.0, groundHeight),
                new Point3d(centerX + Lx / 2.0, centerY + Ly / 2.0, groundHeight + Lz)
            );
        }

        public override string ToString()
        {
            return $"AbsDomain: Lx={Lx:F2}m, Ly={Ly:F2}m, Lz={Lz:F2}m";
        }
    }

    /// <summary>
    /// 场景统计信息
    /// </summary>
    public class SceneStatistics
    {
        public int BuildingCount { get; set; }
        public int TotalVertices { get; set; }
        public int TotalFaces { get; set; }
        public BoundingBox DomainBounds { get; set; }
        public double WindSpeed { get; set; }
        public Vector3d WindDirection { get; set; }
        public bool UseCustomDomain { get; set; }
    }
}
