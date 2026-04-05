using System;
using System.Collections.Generic;
using Rhino.Geometry;

namespace CityLBM.Core
{
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
        /// 场景边界框
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
        /// </summary>
        public double WindSpeed { get; set; }

        /// <summary>
        /// 地面高度（Z=0平面）
        /// </summary>
        public double GroundHeight { get; set; }

        /// <summary>
        /// 模拟区域扩展比例（相对于建筑物边界框）
        /// </summary>
        public double DomainExtensionRatio { get; set; }

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
        /// 计算场景边界框
        /// </summary>
        public void CalculateBounds()
        {
            UpdateBounds();
        }

        /// <summary>
        /// 获取模拟计算域（包含扩展的区域）
        /// </summary>
        public BoundingBox GetSimulationDomain()
        {
            if (!Bounds.IsValid)
            {
                UpdateBounds();
            }

            // 计算扩展距离
            double extension = DomainExtensionRatio * Bounds.Diagonal.Length;

            // 创建扩展后的边界框
            BoundingBox domain = Bounds;
            domain = new BoundingBox(
                new Point3d(domain.Min.X - extension, domain.Min.Y - extension, GroundHeight),
                new Point3d(domain.Max.X + extension, domain.Max.Y + extension, domain.Max.Z + extension)
            );

            return domain;
        }

        /// <summary>
        /// 获取场景统计信息
        /// </summary>
        public SceneStatistics GetStatistics()
        {
            int totalVertices = 0;
            int totalFaces = 0;
            double totalVolume = 0;

            foreach (var mesh in BuildingMeshes)
            {
                totalVertices += mesh.Vertices.Count;
                totalFaces += mesh.Faces.Count;
                // 简化计算：假设Mesh是闭合的
                if (mesh.IsClosed)
                {
                    AreaMassProperties amp = AreaMassProperties.Compute(mesh);
                    // 注意：这里只是简化统计
                }
            }

            return new SceneStatistics
            {
                BuildingCount = BuildingMeshes.Count,
                TotalVertices = totalVertices,
                TotalFaces = totalFaces,
                DomainBounds = GetSimulationDomain(),
                WindSpeed = WindSpeed,
                WindDirection = WindDirection
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

            return true;
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
    }
}
