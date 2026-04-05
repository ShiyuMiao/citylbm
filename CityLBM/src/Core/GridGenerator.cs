using System;
using System.Collections.Generic;
using Rhino.Geometry;

namespace CityLBM.Core
{
    /// <summary>
    /// 笛卡尔网格生成器
    /// 将城市场景转换为结构化网格用于 LBM 模拟
    /// </summary>
    public class GridGenerator
    {
        #region Properties

        /// <summary>
        /// 网格分辨率（每个格子的尺寸，单位：米）
        /// </summary>
        public double CellSize { get; set; }

        /// <summary>
        /// 生成的网格
        /// </summary>
        public CartesianGrid Grid { get; private set; }

        /// <summary>
        /// 网格统计信息
        /// </summary>
        public GridStatistics Statistics { get; private set; }

        #endregion

        #region Constructor

        public GridGenerator(double cellSize = 1.0)
        {
            CellSize = cellSize;
            Grid = new CartesianGrid();
            Statistics = new GridStatistics();
        }

        #endregion

        #region Public Methods

        /// <summary>
        /// 为场景生成计算网格
        /// </summary>
        public CartesianGrid Generate(Scene scene)
        {
            if (scene == null || !scene.Bounds.IsValid)
            {
                throw new ArgumentException("Invalid scene");
            }

            // 获取模拟域
            BoundingBox domain = scene.GetSimulationDomain();

            // 计算网格尺寸
            int nx = (int)Math.Ceiling((domain.Max.X - domain.Min.X) / CellSize);
            int ny = (int)Math.Ceiling((domain.Max.Y - domain.Min.Y) / CellSize);
            int nz = (int)Math.Ceiling((domain.Max.Z - domain.Min.Z) / CellSize);

            // 创建网格
            Grid = new CartesianGrid
            {
                Nx = nx,
                Ny = ny,
                Nz = nz,
                Dx = CellSize,
                Origin = domain.Min,
                DomainBounds = domain
            };

            // 初始化标记数组
            Grid.Flags = new CellFlag[nx, ny, nz];

            // 标记所有单元格为流体
            for (int i = 0; i < nx; i++)
                for (int j = 0; j < ny; j++)
                    for (int k = 0; k < nz; k++)
                        Grid.Flags[i, j, k] = CellFlag.Fluid;

            // 标记建筑物单元格
            int obstacleCount = 0;
            foreach (var mesh in scene.BuildingMeshes)
            {
                obstacleCount += MarkBuildingCells(mesh);
            }

            // 标记边界条件
            ApplyBoundaryConditions(scene);

            // 更新统计信息
            Statistics = new GridStatistics
            {
                TotalCells = nx * ny * nz,
                FluidCells = CountCells(CellFlag.Fluid),
                ObstacleCells = obstacleCount,
                BoundaryCells = CountCells(CellFlag.Boundary),
                Nx = nx,
                Ny = ny,
                Nz = nz
            };

            return Grid;
        }

        #endregion

        #region Private Methods

        /// <summary>
        /// 标记建筑物单元格
        /// </summary>
        private int MarkBuildingCells(Mesh buildingMesh)
        {
            int count = 0;
            BoundingBox meshBounds = buildingMesh.GetBoundingBox(false);

            // 遍历可能与建筑物相交的单元格
            int iMin = Math.Max(0, (int)((meshBounds.Min.X - Grid.Origin.X) / CellSize) - 1);
            int iMax = Math.Min(Grid.Nx - 1, (int)((meshBounds.Max.X - Grid.Origin.X) / CellSize) + 1);
            int jMin = Math.Max(0, (int)((meshBounds.Min.Y - Grid.Origin.Y) / CellSize) - 1);
            int jMax = Math.Min(Grid.Ny - 1, (int)((meshBounds.Max.Y - Grid.Origin.Y) / CellSize) + 1);
            int kMin = Math.Max(0, (int)((meshBounds.Min.Z - Grid.Origin.Z) / CellSize) - 1);
            int kMax = Math.Min(Grid.Nz - 1, (int)((meshBounds.Max.Z - Grid.Origin.Z) / CellSize) + 1);

            for (int i = iMin; i <= iMax; i++)
            {
                for (int j = jMin; j <= jMax; j++)
                {
                    for (int k = kMin; k <= kMax; k++)
                    {
                        // 计算单元格中心点
                        Point3d cellCenter = new Point3d(
                            Grid.Origin.X + (i + 0.5) * CellSize,
                            Grid.Origin.Y + (j + 0.5) * CellSize,
                            Grid.Origin.Z + (k + 0.5) * CellSize
                        );

                        // 检查点是否在建筑物内
                        if (IsPointInMesh(cellCenter, buildingMesh))
                        {
                            Grid.Flags[i, j, k] = CellFlag.Obstacle;
                            count++;
                        }
                    }
                }
            }

            return count;
        }

        /// <summary>
        /// 检查点是否在 Mesh 内部
        /// </summary>
        private bool IsPointInMesh(Point3d point, Mesh mesh)
        {
            // 简化方法：使用射线检测
            // 从点向任意方向发射射线，统计与 mesh 的交点数
            // 奇数次 = 内部，偶数次 = 外部

            Ray3d ray = new Ray3d(point, Vector3d.ZAxis);
            int intersections = 0;

            foreach (var face in mesh.Faces)
            {
                Point3d v0 = mesh.Vertices[face.A];
                Point3d v1 = mesh.Vertices[face.B];
                Point3d v2 = mesh.Vertices[face.C];
                Point3d v3 = face.IsQuad ? mesh.Vertices[face.D] : v2;

                // 检查射线与三角形的交点
                double t;
                if (RayTriangleIntersection(ray, v0, v1, v2, out t))
                {
                    intersections++;
                }
                if (face.IsQuad && RayTriangleIntersection(ray, v2, v3, v0, out t))
                {
                    intersections++;
                }
            }

            return (intersections % 2) == 1;
        }

        /// <summary>
        /// 射线与三角形求交
        /// </summary>
        private bool RayTriangleIntersection(Ray3d ray, Point3d v0, Point3d v1, Point3d v2, out double t)
        {
            t = 0;
            const double EPSILON = 1e-6;

            Vector3d edge1 = v1 - v0;
            Vector3d edge2 = v2 - v0;
            Vector3d h = Vector3d.CrossProduct(ray.Direction, edge2);
            double a = Vector3d.Multiply(edge1, h);

            if (a > -EPSILON && a < EPSILON)
                return false;

            double f = 1.0 / a;
            Vector3d s = ray.Position - v0;
            double u = f * Vector3d.Multiply(s, h);

            if (u < 0.0 || u > 1.0)
                return false;

            Vector3d q = Vector3d.CrossProduct(s, edge1);
            double v = f * Vector3d.Multiply(ray.Direction, q);

            if (v < 0.0 || u + v > 1.0)
                return false;

            t = f * Vector3d.Multiply(edge2, q);

            return t > EPSILON;
        }

        /// <summary>
        /// 应用边界条件
        /// </summary>
        private void ApplyBoundaryConditions(Scene scene)
        {
            // 标记入口边界（风向的上游）
            if (Math.Abs(scene.WindDirection.X) > Math.Abs(scene.WindDirection.Y))
            {
                // X 方向主导风
                int inletFace = scene.WindDirection.X > 0 ? 0 : Grid.Nx - 1;
                for (int j = 0; j < Grid.Ny; j++)
                    for (int k = 0; k < Grid.Nz; k++)
                        if (Grid.Flags[inletFace, j, k] == CellFlag.Fluid)
                            Grid.Flags[inletFace, j, k] = CellFlag.Inlet;
            }
            else
            {
                // Y 方向主导风
                int inletFace = scene.WindDirection.Y > 0 ? 0 : Grid.Ny - 1;
                for (int i = 0; i < Grid.Nx; i++)
                    for (int k = 0; k < Grid.Nz; k++)
                        if (Grid.Flags[i, inletFace, k] == CellFlag.Fluid)
                            Grid.Flags[i, inletFace, k] = CellFlag.Inlet;
            }

            // 标记地面（底部）
            for (int i = 0; i < Grid.Nx; i++)
                for (int j = 0; j < Grid.Ny; j++)
                    if (Grid.Flags[i, j, 0] == CellFlag.Fluid)
                        Grid.Flags[i, j, 0] = CellFlag.Wall;
        }

        /// <summary>
        /// 统计特定类型的单元格数量
        /// </summary>
        private int CountCells(CellFlag flag)
        {
            int count = 0;
            for (int i = 0; i < Grid.Nx; i++)
                for (int j = 0; j < Grid.Ny; j++)
                    for (int k = 0; k < Grid.Nz; k++)
                        if (Grid.Flags[i, j, k] == flag)
                            count++;
            return count;
        }

        #endregion
    }

    /// <summary>
    /// 笛卡尔网格
    /// </summary>
    public class CartesianGrid
    {
        public int Nx { get; set; }
        public int Ny { get; set; }
        public int Nz { get; set; }
        public double Dx { get; set; }
        public Point3d Origin { get; set; }
        public BoundingBox DomainBounds { get; set; }
        public CellFlag[,,] Flags { get; set; }

        public int TotalCells => Nx * Ny * Nz;
    }

    /// <summary>
    /// 单元格标记类型
    /// </summary>
    public enum CellFlag
    {
        Fluid = 0,      // 流体
        Obstacle = 1,   // 障碍物（建筑物）
        Wall = 2,       // 墙壁（地面）
        Inlet = 3,      // 入口边界
        Outlet = 4,     // 出口边界
        Boundary = 5    // 其他边界
    }

    /// <summary>
    /// 网格统计信息
    /// </summary>
    public class GridStatistics
    {
        public int TotalCells { get; set; }
        public int FluidCells { get; set; }
        public int ObstacleCells { get; set; }
        public int BoundaryCells { get; set; }
        public int Nx { get; set; }
        public int Ny { get; set; }
        public int Nz { get; set; }
    }
}
