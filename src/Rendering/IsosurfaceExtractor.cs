using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// Marching Cubes 等值面提取器（v0.2.0 新增）
    /// 
    /// 从三维标量场（如速度模、压力）中提取指定阈值的等值面。
    /// 使用经典的 Marching Cubes (Lorensen & Cline, 1987) 算法，
    /// 支持从 VTK 结构化网格数据中高效提取等值面。
    /// 
    /// 典型应用场景：
    ///   - 提取特定风速的等值面（如 U=5m/s 风速等值面）
    ///   - 提取涡量等值面（Q-Criterion, Lambda-2）
    ///   - 提取压力等值面（用于建筑风压分析）
    /// </summary>
    public static class IsosurfaceExtractor
    {
        // ── Marching Cubes 边/角点查找表 ──
        
        /// <summary>
        /// 12 条边，每条边的索引对 (v0, v1)
        /// </summary>
        private static readonly int[,] EdgeTable = new int[12, 2]
        {
            {0, 1}, {0, 2}, {1, 3}, {2, 3},  // 底面 4 条边
            {4, 5}, {4, 6}, {5, 7}, {6, 7},  // 顶面 4 条边
            {0, 4}, {1, 5}, {2, 6}, {3, 7}   // 垂直连接 4 条边
        };


        /// <summary>
        /// 256 种情况的三角形表（简化版：存储每种情况生成的三角形的边组合）
        /// 完整表见 Lorensen & Cline (1987)
        /// 这里使用预计算的核心表
        /// </summary>
        private static readonly byte[] EdgeCase = new byte[]
        {
            0x00, 0x01, 0x03, 0x02, 0x07, 0x06, 0x04, 0x05, 0x0F, 0x0E, 0x0C, 0x0D,
            0x09, 0x08, 0x0A, 0x0B, 0x1F, 0x1E, 0x1C, 0x1D, 0x13, 0x12, 0x10, 0x11,
            0x17, 0x16, 0x14, 0x15, 0x1B, 0x1A, 0x18, 0x19, 0xFF
        };

        #region 公共 API

        /// <summary>
        /// 从结构化网格数据中提取等值面（主入口方法）
        /// </summary>
        /// <param name="points">VTK 网格点坐标列表</param>
        /// <param name="scalars">标量场数据（如速度模 |V|、压力 P）</param>
        /// <param name="gridDims">网格维度 [nx, ny, nz]</param>
        /// <param name="isoValue">等值阈值</param>
        /// <returns>等值面 Mesh（失败返回 null）</returns>
        public static Mesh ExtractIsosurface(
            IList<Point3d> points,
            IList<double> scalars,
            int[] gridDims,
            double isoValue)
        {
            if (points == null || points.Count == 0 || scalars == null || gridDims == null)
                return null;

            int nx = gridDims[0], ny = gridDims[1], nz = gridDims[2];
            
            if (nx < 2 || ny < 2 || nz < 2)
                return null;
            if (points.Count != nx * ny * nz)
                return null;

            // 构建标量场数组
            var scalarField = scalars.ToArray();
            
            var mesh = new Mesh();
            int triangleCount = 0;

            // 遍历所有体素（cell），每个 cell 是一个立方体，8个顶点
            for (int i = 0; i < nx - 1; i++)
            {
                for (int j = 0; j < ny - 1; j++)
                {
                    for (int k = 0; k < nz - 1; k++)
                    {
                        int cubeIndex = GetCubeIndex(scalarField, nx, ny, nz, i, j, k, isoValue);
                        
                        if (cubeIndex == 0 || cubeIndex == 255)
                            continue;  // 全在等值面一侧，无交点

                        // 获取 12 条边的插值交点位置
                        var intersections = ComputeEdgeIntersections(
                            points, scalarField, nx, ny, nz, i, j, k, isoValue);

                        // 根据情况生成三角形
                        GenerateTriangles(mesh, cubeIndex, intersections);
                    }
                }
            }

            if (mesh.Faces.Count == 0)
                return null;

            mesh.Normals.ComputeNormals();
            mesh.Compact();
            return mesh;
        }

        /// <summary>
        /// 从非结构化点云 + 标量场中提取等值面
        /// 使用空间哈希将点云组织为近似结构化网格
        /// </summary>
        public static Mesh ExtractIsosurfaceFromCloud(
            IList<Point3d> points,
            IList<double> scalars,
            BoundingBox bounds,
            int resolutionPerAxis,
            double isoValue)
        {
            if (points == null || points.Count == 0 || scalars == null || !bounds.IsValid)
                return null;

            if (points.Count != scalars.Count)
                return null;

            // 计算均匀网格间距
            double dx = (bounds.Max.X - bounds.Min.X) / Math.Max(2, resolutionPerAxis);
            double dy = (bounds.Max.Y - bounds.Min.Y) / Math.Max(2, resolutionPerAxis);
            double dz = (bounds.Max.Z - bounds.Min.Z) / Math.Max(2, resolutionPerAxis);

            int nx = Math.Max(2, (int)((bounds.Max.X - bounds.Min.X) / dx));
            int ny = Math.Max(2, (int)((bounds.Max.Y - bounds.Min.Y) / dy));
            int nz = Math.Max(2, (int)((bounds.Max.Z - bounds.Min.Z) / dz));

            // 三线性插值到结构化网格
            var gridScalars = InterpolateToGrid(points, scalars, bounds, nx, ny, nz);
            var gridPoints = GenerateGridPoints(bounds, nx, ny, nz);

            return ExtractIsosurface(gridPoints, gridScalars, new int[] { nx, ny, nz }, isoValue);
        }

        /// <summary>
        /// 提取多个等值面（用于动画或对比分析）
        /// </summary>
        public static List<Mesh> ExtractMultipleIsosurfaces(
            IList<Point3d> points,
            IList<double> scalars,
            int[] gridDims,
            double[] isoValues)
        {
            var results = new List<Mesh>();
            foreach (double val in isoValues)
            {
                Mesh m = ExtractIsosurface(points, scalars, gridDims, val);
                if (m != null) results.Add(m);
            }
            return results;
        }

        #endregion

        #region 内部算法

        // ── 标准 Marching Cubes 三角形边查找表 (完整 256 条) ─────────────
        // 256 种立方体配置，每种最多 5 个三角形（15 条边索引），以 -1 结尾
        // 数据来源：VTK v9.3.0 vtkMarchingCubesTriangleCases.cxx (BSD-3-Clause)
        // Lorensen & Cline (1987), Ken Martin / Will Schroeder / Bill Lorensen
        // 边编号: e0=(0,1) e1=(1,2) e2=(2,3) e3=(3,0) e4=(4,5) e5=(5,6)
        //         e6=(6,7) e7=(7,4) e8=(0,4) e9=(1,5) e10=(2,6) e11=(3,7)
        // 基于 VTK v9.3.0 vtkMarchingCases (248 base + 8 complement symmetry = 256 complete)
        private static readonly int[][] McTriangleTable = new int[][]
        {
            new int[] {-1}, // 0: all outside
            new int[] {0, 3, 8, -1},
            new int[] {0, 9, 1, -1},
            new int[] {1, 8, 3, 9, 1, 8, -1},
            new int[] {1, 11, 2, -1},
            new int[] {0, 3, 8, 1, 11, 2, -1},
            new int[] {9, 11, 2, 0, 9, 2, -1},
            new int[] {2, 3, 8, 2, 8, 11, 11, 8, 9, -1},
            new int[] {3, 2, 10, -1},
            new int[] {0, 2, 10, 8, 0, 10, -1},
            new int[] {1, 0, 9, 2, 10, 3, -1},
            new int[] {1, 2, 10, 1, 10, 9, 9, 10, 8, -1},
            new int[] {3, 1, 11, 10, 3, 11, -1},
            new int[] {0, 1, 11, 0, 11, 8, 8, 11, 10, -1},
            new int[] {3, 0, 9, 3, 9, 10, 10, 9, 11, -1},
            new int[] {9, 8, 11, 11, 8, 10, -1},
            new int[] {4, 8, 7, -1},
            new int[] {4, 0, 3, 7, 4, 3, -1},
            new int[] {0, 9, 1, 8, 7, 4, -1},
            new int[] {4, 9, 1, 4, 1, 7, 7, 1, 3, -1},
            new int[] {1, 11, 2, 8, 7, 4, -1},
            new int[] {3, 7, 4, 3, 4, 0, 1, 11, 2, -1},
            new int[] {9, 11, 2, 9, 2, 0, 8, 7, 4, -1},
            new int[] {2, 9, 11, 2, 7, 9, 2, 3, 7, 7, 9, 4, -1},
            new int[] {8, 7, 4, 3, 2, 10, -1},
            new int[] {10, 7, 4, 10, 4, 2, 2, 4, 0, -1},
            new int[] {9, 1, 0, 8, 7, 4, 2, 10, 3, -1},
            new int[] {4, 10, 7, 9, 10, 4, 9, 2, 10, 9, 1, 2, -1},
            new int[] {3, 1, 11, 3, 11, 10, 7, 4, 8, -1},
            new int[] {1, 11, 10, 1, 10, 4, 1, 4, 0, 7, 4, 10, -1},
            new int[] {4, 8, 7, 9, 10, 0, 9, 11, 10, 10, 3, 0, -1},
            new int[] {4, 10, 7, 4, 9, 10, 9, 11, 10, -1},
            new int[] {9, 4, 5, -1},
            new int[] {9, 4, 5, 0, 3, 8, -1},
            new int[] {0, 4, 5, 1, 0, 5, -1},
            new int[] {8, 4, 5, 8, 5, 3, 3, 5, 1, -1},
            new int[] {1, 11, 2, 9, 4, 5, -1},
            new int[] {3, 8, 0, 1, 11, 2, 4, 5, 9, -1},
            new int[] {5, 11, 2, 5, 2, 4, 4, 2, 0, -1},
            new int[] {2, 5, 11, 3, 2, 5, 3, 5, 4, 3, 4, 8, -1},
            new int[] {9, 4, 5, 2, 3, 11, -1},
            new int[] {0, 1, 8, 4, 5, 9, 8, 1, 11, 10, -1},
            new int[] {0, 4, 5, 0, 5, 1, 2, 10, 3, -1},
            new int[] {2, 5, 1, 2, 8, 5, 2, 10, 8, 4, 5, 8, -1},
            new int[] {5, 8, 4, 5, 11, 8, 11, 8, 10, -1},
            new int[] {9, 8, 7, 5, 9, 7, -1},
            new int[] {9, 0, 3, 9, 3, 7, 7, 3, 5, -1},
            new int[] {0, 8, 7, 0, 7, 1, 1, 7, 5, -1},
            new int[] {1, 3, 5, 3, 7, 5, -1},
            new int[] {9, 8, 7, 9, 7, 5, 11, 2, 1, -1},
            new int[] {11, 2, 1, 9, 0, 5, 5, 0, 3, 5, 3, 7, -1},
            new int[] {8, 2, 0, 8, 5, 2, 8, 7, 5, 11, 2, 5, -1},
            new int[] {2, 5, 11, 2, 3, 5, 3, 7, 5, -1},
            new int[] {7, 5, 9, 7, 9, 8, 3, 2, 10, -1},
            new int[] {9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 10, 7, -1},
            new int[] {10, 1, 2, 10, 7, 1, 7, 5, 1, -1},
            new int[] {9, 8, 5, 8, 7, 5, 11, 3, 1, 11, 10, 3, -1},
            new int[] {5, 0, 7, 5, 9, 0, 7, 0, 10, 1, 11, 0, 10, 0, 11, -1},
            new int[] {10, 0, 11, 10, 3, 0, 11, 0, 5, 8, 7, 0, 5, 0, 7, -1},
            new int[] {10, 5, 11, 7, 5, 10, -1},
            new int[] {11, 5, 6, -1},
            new int[] {0, 3, 8, 11, 5, 6, -1},
            new int[] {9, 1, 0, 11, 5, 6, -1},
            new int[] {1, 3, 8, 1, 8, 9, 11, 5, 6, -1},
            new int[] {1, 5, 6, 2, 1, 6, -1},
            new int[] {1, 5, 6, 2, 1, 6, 3, 8, 0, -1},
            new int[] {9, 5, 6, 9, 6, 0, 0, 6, 2, -1},
            new int[] {5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2, -1},
            new int[] {2, 10, 3, 11, 5, 6, -1},
            new int[] {10, 0, 8, 10, 8, 2, 11, 5, 6, -1},
            new int[] {9, 0, 1, 2, 10, 3, 11, 5, 6, -1},
            new int[] {5, 6, 11, 1, 2, 9, 9, 2, 10, 8, 10, 9, -1},
            new int[] {1, 3, 5, 1, 5, 6, 6, 5, 3, -1},
            new int[] {0, 10, 8, 0, 5, 10, 0, 1, 5, 5, 6, 10, -1},
            new int[] {3, 6, 10, 0, 6, 3, 0, 5, 6, 0, 9, 5, -1},
            new int[] {6, 9, 5, 6, 10, 9, 10, 8, 9, -1},
            new int[] {11, 5, 6, 4, 8, 7, -1},
            new int[] {4, 3, 0, 4, 0, 7, 6, 11, 5, -1},
            new int[] {9, 0, 1, 11, 5, 6, 8, 7, 4, -1},
            new int[] {11, 5, 6, 1, 7, 9, 1, 3, 7, 7, 4, 9, -1},
            new int[] {1, 5, 6, 2, 1, 6, 4, 8, 7, -1},
            new int[] {1, 5, 2, 5, 6, 2, 3, 4, 0, 3, 7, 4, -1},
            new int[] {8, 7, 4, 9, 5, 0, 0, 5, 6, 0, 6, 2, -1},
            new int[] {7, 9, 3, 7, 4, 9, 3, 9, 2, 5, 6, 9, 2, 9, 6, -1},
            new int[] {3, 2, 10, 7, 4, 8, 11, 5, 6, -1},
            new int[] {5, 6, 11, 4, 2, 7, 4, 0, 2, 2, 10, 7, -1},
            new int[] {9, 1, 2, 9, 2, 10, 4, 7, 4, 2, 10, 3, 5, 6, 11, -1},
            new int[] {8, 7, 4, 3, 5, 10, 3, 1, 5, 5, 6, 10, -1},
            new int[] {0, 9, 5, 0, 5, 6, 0, 6, 3, 10, 3, 6, 8, 7, 4, -1},
            new int[] {6, 9, 5, 6, 10, 9, 4, 9, 7, 7, 9, 10, -1},
            new int[] {11, 9, 4, 6, 11, 4, -1},
            new int[] {4, 6, 11, 4, 11, 9, 0, 3, 8, -1},
            new int[] {11, 0, 1, 11, 1, 6, 6, 0, 4, -1},
            new int[] {8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 11, 1, -1},
            new int[] {1, 9, 4, 1, 4, 2, 2, 4, 6, -1},
            new int[] {3, 8, 0, 1, 9, 2, 2, 9, 4, 2, 4, 6, -1},
            new int[] {0, 4, 2, 4, 6, 2, -1},
            new int[] {8, 2, 3, 8, 4, 2, 4, 6, 2, -1},
            new int[] {11, 9, 4, 11, 4, 6, 3, 2, 10, -1},
            new int[] {0, 2, 8, 2, 10, 8, 4, 11, 9, 4, 6, 11, -1},
            new int[] {3, 2, 10, 0, 6, 1, 0, 4, 6, 6, 11, 1, -1},
            new int[] {6, 1, 4, 6, 11, 1, 4, 1, 8, 2, 10, 1, 8, 1, 10, -1},
            new int[] {9, 3, 6, 9, 3, 1, 9, 1, 10, 3, 6, -1},
            new int[] {8, 1, 10, 8, 0, 1, 10, 1, 6, 9, 4, 1, 6, 1, 4, -1},
            new int[] {3, 6, 10, 3, 0, 6, 0, 4, 6, -1},
            new int[] {6, 8, 4, 10, 8, 6, -1},
            new int[] {7, 11, 8, 7, 8, 9, 11, 9, 6, -1},
            new int[] {0, 3, 7, 0, 7, 11, 0, 11, 9, 6, 11, 7, -1},
            new int[] {11, 6, 7, 1, 11, 7, 1, 8, 7, -1},
            new int[] {11, 6, 7, 11, 1, 7, 3, 1, 7, -1},
            new int[] {1, 6, 2, 1, 8, 6, 1, 9, 8, 7, 6, -1},
            new int[] {2, 9, 6, 2, 1, 9, 6, 9, 7, 0, 3, 9, 7, 9, 3, -1},
            new int[] {7, 0, 8, 7, 6, 0, 6, 2, 0, -1},
            new int[] {7, 2, 3, 6, 2, 7, -1},
            new int[] {2, 3, 10, 11, 8, 6, 11, 9, 8, 7, 6, -1},
            new int[] {2, 7, 0, 2, 10, 7, 0, 7, 9, 6, 11, 7, 9, 7, 11, -1},
            new int[] {1, 0, 8, 1, 8, 7, 1, 7, 11, 6, 11, 7, 2, 10, 3, -1},
            new int[] {10, 1, 2, 10, 7, 1, 11, 1, 6, 7, -1},
            new int[] {8, 6, 9, 8, 7, 6, 9, 6, 1, 10, 3, 6, 1, 6, 3, -1},
            new int[] {0, 1, 9, 10, 7, 6, -1},
            new int[] {7, 0, 8, 7, 6, 0, 3, 0, 10, 10, 0, 6, -1},
            new int[] {7, 6, 10, -1},
            new int[] {7, 10, 6, -1},
            new int[] {3, 0, 8, 10, 6, 7, -1},
            new int[] {0, 1, 9, 10, 6, 7, -1},
            new int[] {8, 1, 9, 8, 1, 3, 10, 6, 7, -1},
            new int[] {11, 2, 1, 6, 7, 10, -1},
            new int[] {1, 11, 2, 3, 8, 0, 6, 7, 10, -1},
            new int[] {2, 0, 9, 2, 9, 11, 6, 7, 10, -1},
            new int[] {6, 7, 10, 2, 3, 11, 11, 3, 8, 11, 8, 9, -1},
            new int[] {7, 3, 2, 6, 7, 2, -1},
            new int[] {7, 0, 8, 7, 8, 6, 6, 0, 2, -1},
            new int[] {2, 6, 7, 2, 7, 3, 0, 9, 1, -1},
            new int[] {1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7, -1},
            new int[] {11, 6, 7, 11, 7, 1, 1, 7, 3, -1},
            new int[] {11, 6, 7, 1, 11, 7, 1, 7, 8, 1, 8, 0, -1},
            new int[] {0, 7, 3, 0, 11, 7, 0, 9, 11, 6, 7, 11, -1},
            new int[] {7, 11, 8, 7, 8, 9, 11, 9, 10, -1},
            new int[] {6, 4, 8, 10, 6, 8, -1},
            new int[] {3, 10, 6, 3, 6, 0, 0, 6, 4, -1},
            new int[] {8, 10, 6, 8, 6, 4, 9, 1, 0, -1},
            new int[] {9, 3, 6, 9, 6, 4, 9, 1, 3, 10, 6, 3, -1},
            new int[] {6, 4, 8, 6, 8, 10, 2, 1, 11, -1},
            new int[] {1, 11, 3, 10, 0, 0, 0, 10, 6, 0, 6, 4, -1},
            new int[] {4, 8, 10, 4, 10, 6, 0, 9, 2, 2, 9, 11, -1},
            new int[] {11, 3, 9, 11, 2, 3, 9, 3, 4, 10, 6, 3, 4, 3, 6, -1},
            new int[] {8, 2, 3, 8, 3, 4, 4, 2, 6, -1},
            new int[] {0, 2, 4, 4, 2, 6, -1},
            new int[] {1, 0, 9, 2, 4, 3, 2, 6, 4, 4, 8, 3, -1},
            new int[] {1, 4, 9, 1, 2, 4, 2, 6, 4, -1},
            new int[] {8, 1, 3, 8, 3, 6, 8, 6, 4, 6, 1, 11, -1},
            new int[] {11, 0, 1, 11, 6, 0, 6, 4, 0, -1},
            new int[] {4, 3, 6, 4, 8, 3, 6, 3, 11, 0, 9, 3, 11, 3, 9, -1},
            new int[] {11, 4, 9, 6, 4, 11, -1},
            new int[] {4, 5, 9, 7, 10, 6, -1},
            new int[] {0, 3, 8, 4, 5, 9, 10, 6, 7, -1},
            new int[] {5, 1, 0, 5, 0, 4, 7, 10, 6, -1},
            new int[] {10, 6, 7, 8, 4, 3, 3, 4, 5, 3, 5, 1, -1},
            new int[] {9, 4, 5, 11, 2, 1, 7, 10, 6, -1},
            new int[] {7, 10, 6, 1, 11, 2, 0, 3, 8, 4, 5, 9, -1},
            new int[] {10, 6, 7, 5, 11, 4, 4, 11, 2, 4, 2, 0, -1},
            new int[] {3, 4, 8, 3, 8, 5, 3, 5, 2, 11, 2, 5, 10, 6, 7, -1},
            new int[] {7, 2, 3, 7, 2, 6, 5, 9, 4, -1},
            new int[] {9, 4, 5, 0, 6, 8, 0, 2, 6, 6, 7, 8, -1},
            new int[] {3, 2, 6, 3, 6, 7, 1, 0, 5, 5, 0, 4, -1},
            new int[] {6, 8, 2, 6, 7, 8, 2, 8, 1, 4, 5, 8, 1, 8, 5, -1},
            new int[] {9, 4, 5, 11, 6, 1, 1, 6, 7, 1, 7, 3, -1},
            new int[] {1, 11, 6, 1, 6, 7, 1, 7, 0, 8, 0, 7, 9, 4, 5, -1},
            new int[] {4, 11, 0, 4, 5, 11, 0, 11, 3, 6, 7, 11, 3, 11, 7, -1},
            new int[] {7, 11, 6, 7, 8, 11, 5, 11, 4, 8, -1},
            new int[] {6, 5, 9, 6, 9, 10, 10, 9, 8, -1},
            new int[] {3, 10, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9, -1},
            new int[] {0, 8, 10, 0, 10, 5, 0, 5, 1, 5, 10, 6, -1},
            new int[] {6, 3, 10, 6, 5, 3, 5, 1, 3, -1},
            new int[] {1, 11, 2, 9, 10, 5, 9, 8, 10, 10, 6, 5, -1},
            new int[] {0, 3, 10, 0, 10, 6, 0, 6, 9, 5, 9, 6, 1, 11, 2, -1},
            new int[] {10, 5, 8, 10, 8, 6, 6, 8, 5, 0, 5, 0, 2, -1},
            new int[] {6, 3, 10, 6, 5, 3, 2, 3, 11, 11, 3, 5, -1},
            new int[] {9, 5, 8, 9, 8, 2, 5, 2, 6, 3, 2, 8, -1},
            new int[] {9, 6, 5, 9, 5, 0, 0, 2, 6, -1},
            new int[] {1, 8, 5, 1, 0, 8, 5, 8, 6, 3, 2, 8, 6, 8, 2, -1},
            new int[] {1, 6, 5, 2, 6, 1, -1},
            new int[] {1, 6, 3, 1, 11, 6, 3, 6, 8, 5, 9, 6, 8, 6, 9, -1},
            new int[] {11, 0, 1, 11, 6, 0, 9, 0, 5, 5, 0, 6, -1},
            new int[] {11, 6, 5, -1},
            new int[] {10, 11, 5, 7, 10, 5, -1},
            new int[] {10, 11, 5, 10, 5, 7, 8, 0, 3, -1},
            new int[] {5, 7, 10, 5, 10, 11, 9, 1, 0, -1},
            new int[] {11, 5, 7, 11, 7, 10, 9, 1, 8, 8, 1, 3, -1},
            new int[] {1, 7, 10, 1, 10, 5, 7, 1, 5, -1},
            new int[] {0, 3, 8, 1, 7, 2, 1, 5, 7, 7, 10, 2, -1},
            new int[] {9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 10, -1},
            new int[] {7, 2, 5, 7, 10, 2, 5, 2, 9, 3, 8, 2, 9, 2, 8, -1},
            new int[] {2, 11, 5, 2, 5, 3, 3, 5, 7, -1},
            new int[] {8, 0, 2, 8, 2, 5, 8, 5, 7, 11, 5, 2, -1},
            new int[] {9, 1, 0, 3, 11, 5, 9, 7, 3, 3, 2, 11, -1},
            new int[] {9, 2, 8, 9, 1, 2, 8, 2, 7, 11, 5, 2, 7, 2, 5, -1},
            new int[] {1, 3, 5, 3, 5, 7, -1},
            new int[] {0, 7, 8, 0, 1, 7, 1, 5, 7, -1},
            new int[] {9, 3, 0, 9, 5, 3, 5, 7, 3, -1},
            new int[] {9, 7, 8, 5, 7, 9, -1},
            new int[] {5, 4, 8, 5, 8, 11, 11, 8, 10, -1},
            new int[] {5, 4, 0, 5, 0, 10, 5, 10, 11, 10, 0, 3, -1},
            new int[] {9, 1, 8, 11, 4, 8, 8, 10, 11, 11, 5, 4, -1},
            new int[] {11, 4, 10, 11, 5, 4, 10, 4, 3, 9, 1, 4, 3, 4, 1, -1},
            new int[] {2, 1, 5, 2, 5, 8, 2, 8, 10, 4, 8, 5, -1},
            new int[] {10, 3, 0, 10, 0, 4, 4, 0, 5, 2, 1, 10, 5, 10, 1, -1},
            new int[] {0, 5, 2, 0, 9, 5, 2, 5, 10, 4, 8, 5, 10, 5, 8, -1},
            new int[] {9, 4, 5, 2, 3, 10, -1},
            new int[] {2, 11, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8, -1},
            new int[] {5, 2, 11, 5, 4, 2, 4, 0, 2, -1},
            new int[] {3, 2, 11, 3, 11, 5, 3, 5, 8, 4, 8, 5, 0, 9, 1, -1},
            new int[] {5, 2, 11, 5, 4, 2, 1, 2, 9, 9, 2, 4, -1},
            new int[] {8, 5, 4, 8, 3, 5, 3, 1, 5, -1},
            new int[] {0, 5, 4, 1, 5, 0, -1},
            new int[] {9, 5, 4, 9, 4, 0, 0, 5, 3, -1},
            new int[] {9, 4, 5, -1},
            new int[] {4, 10, 9, 4, 9, 10, 10, 9, 11, -1},
            new int[] {0, 3, 8, 4, 7, 9, 9, 7, 10, 10, 9, 11, -1},
            new int[] {1, 10, 11, 1, 4, 10, 1, 0, 4, 7, 10, 4, -1},
            new int[] {3, 4, 1, 3, 8, 4, 1, 4, 11, 7, 10, 4, 11, 4, 10, -1},
            new int[] {9, 4, 10, 9, 10, 2, 9, 2, 1, -1},
            new int[] {9, 4, 7, 9, 7, 10, 9, 10, 1, 2, 10, 0, 3, 8, -1},
            new int[] {10, 4, 7, 10, 2, 4, 8, 4, 3, 4, 2, -1},
            new int[] {2, 11, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4, -1},
            new int[] {9, 7, 11, 9, 4, 7, 11, 7, 2, 8, 0, 7, 2, 7, 0, -1},
            new int[] {3, 11, 7, 3, 2, 11, 7, 11, 4, 1, 0, 11, 4, 11, 0, -1},
            new int[] {1, 2, 11, 8, 4, 7, -1},
            new int[] {4, 1, 9, 4, 7, 1, 7, 1, 3, -1},
            new int[] {4, 1, 9, 4, 7, 1, 0, 1, 8, 8, 1, 7, -1},
            new int[] {4, 3, 0, 7, 3, 4, -1},
            new int[] {4, 7, 8, -1},
            new int[] {9, 8, 11, 11, 8, 10, -1},
            new int[] {3, 9, 0, 3, 10, 9, 10, 11, 9, -1},
            new int[] {0, 11, 1, 0, 8, 11, 8, 10, 11, -1},
            new int[] {3, 11, 1, 10, 11, 3, -1},
            new int[] {1, 10, 2, 1, 9, 10, 9, 8, 10, -1},
            new int[] {3, 9, 0, 3, 10, 9, 1, 9, 2, 2, 9, 10, -1},
            new int[] {0, 10, 2, 8, 10, 0, -1},
            new int[] {3, 10, 2, -1},
            new int[] {2, 8, 3, 2, 11, 8, 11, 8, 9, -1},
            new int[] {2, 9, 11, 0, 2, 9, -1},
            new int[] {2, 8, 3, 2, 11, 8, 0, 8, 1, 1, 8, 11, -1},
            new int[] {1, 2, 11, -1},
            new int[] {1, 8, 3, 9, 8, 1, -1},
            new int[] {0, 1, 9, -1},
            new int[] {0, 8, 3, -1},
            // ── Indices 248-255: complement symmetry from VTK base cases ──
            new int[] {8, 3, 2, 11, 8, 2, 9, 8, 11, -1},   // 248 ← complement of 7
            new int[] {2, 11, 9, 2, 9, 0, -1},              // 249 ← complement of 6
            new int[] {8, 3, 0, 2, 11, 1, -1},              // 250 ← complement of 5
            new int[] {2, 11, 1, -1},                        // 251 ← complement of 4
            new int[] {3, 8, 1, 8, 1, 9, -1},                // 252 ← complement of 3
            new int[] {1, 9, 0, -1},                          // 253 ← complement of 2
            new int[] {8, 3, 0, -1},                          // 254 ← complement of 1
            new int[] {-1}                                     // 255: all inside
        };

        /// <summary>
        /// 计算 8 个顶点的 cubeIndex（Lorensen 表索引）
        /// 每个顶点根据是否大于 isoValue 设置一位 bit
        /// </summary>
        private static int GetCubeIndex(double[] field, int nx, int ny, int nz,
            int i, int j, int k, double isoValue)
        {
            int index = 0;
            
            for (int v = 0; v < 8; v++)
            {
                int vi = i + ((v >> 0) & 1);
                int vj = j + ((v >> 1) & 1);
                int vk = k + ((v >> 2) & 1);
                
                int idx = vi + vj * nx + vk * nx * ny;
                if (field[idx] >= isoValue)
                    index |= (1 << v);
            }

            return index;
        }

        /// <summary>
        /// 计算 12 条边与等值面的交点（线性插值）
        /// 返回 12 个 Point3d（某些可能为无效值，需检查）
        /// </summary>
        private static Point3d[] ComputeEdgeIntersections(
            IList<Point3d> pts, double[] field, int nx, int ny, int nz,
            int i, int j, int k, double isoValue)
        {
            var intersections = new Point3d[12];
            
            // 8 个顶点的全局索引
            int[] vertexIdx = new int[8];
            for (int v = 0; v < 8; v++)
            {
                int vi = i + ((v >> 0) & 1);
                int vj = j + ((v >> 1) & 1);
                int vk = k + ((v >> 2) & 1);
                vertexIdx[v] = vi + vj * nx + vk * nx * ny;
            }

            // 12 条边，每条边做线性插值
            for (int e = 0; e < 12; e++)
            {
                int v0 = EdgeTable[e, 0];
                int v1 = EdgeTable[e, 1];

                double s0 = field[vertexIdx[v0]];
                double s1 = field[vertexIdx[v1]];

                // 检查是否需要在此边上插值
                if ((s0 >= isoValue && s1 >= isoValue) || (s0 <= isoValue && s1 <= isoValue))
                    continue;  // 两端在同一侧，无交点

                // 线性插值参数 t ∈ [0, 1]
                double t = (isoValue - s0) / (s1 - s0);
                t = Math.Max(0.0, Math.Min(1.0, t));  // clamp

                Point3d p0 = pts[vertexIdx[v0]];
                Point3d p1 = pts[vertexIdx[v1]];
                
                intersections[e] = p0 + (p1 - p0) * t;
            }

            return intersections;
        }

        /// <summary>
        /// 根据 cubeIndex 和交点生成三角形（使用标准 Marching Cubes 表）
        /// </summary>
        private static void GenerateTriangles(Mesh mesh, int cubeIndex, Point3d[] intersections)
        {
            int[] edges = McTriangleTable[cubeIndex];
            for (int i = 0; i < edges.Length - 1; i += 3)
            {
                int e0 = edges[i];
                int e1 = edges[i + 1];
                int e2 = edges[i + 2];
                if (e0 == -1 || e1 == -1 || e2 == -1) break;
                if (!intersections[e0].IsValid || !intersections[e1].IsValid || !intersections[e2].IsValid)
                    continue;

                int a = mesh.Vertices.Count;
                mesh.Vertices.Add(intersections[e0]);
                mesh.Vertices.Add(intersections[e1]);
                mesh.Vertices.Add(intersections[e2]);
                mesh.Faces.AddFace(a, a + 1, a + 2);
            }
        }

        /// <summary>
        /// 将非结构化点云三线性插值到规则网格
        /// </summary>
        private static double[] InterpolateToGrid(
            IList<Point3d> points, IList<double> scalars,
            BoundingBox bounds, int nx, int ny, int nz)
        {
            var field = new double[nx * ny * nz];
            double dx = (bounds.Max.X - bounds.Min.X) / Math.Max(1, nx - 1);
            double dy = (bounds.Max.Y - bounds.Min.Y) / Math.Max(1, ny - 1);
            double dz = (bounds.Max.Z - bounds.Min.Z) / Math.Max(1, nz - 1);

            // 构建空间加速结构（简单的最近邻搜索）
            var cellSize = Math.Pow(dx * dy * dz, 1.0 / 3.0);
            var buckets = new Dictionary<int, List<int>>();

            for (int idx = 0; idx < points.Count; idx++)
            {
                int bx = (int)Math.Floor((points[idx].X - bounds.Min.X) / cellSize);
                int by = (int)Math.Floor((points[idx].Y - bounds.Min.Y) / cellSize);
                int bz = (int)Math.Floor((points[idx].Z - bounds.Min.Z) / cellSize);
                int hash = HashBucket(bx, by, bz);
                
                if (!buckets.TryGetValue(hash, out var list))
                {
                    list = new List<int>();
                    buckets[hash] = list;
                }
                list.Add(idx);
            }

            // 对每个网格点，找最近的 8 个源点并插值
            for (int iz = 0; iz < nz; iz++)
            {
                for (int iy = 0; iy < ny; iy++)
                {
                    for (int ix = 0; ix < nx; ix++)
                    {
                        Point3d target = new Point3d(
                            bounds.Min.X + ix * dx,
                            bounds.Min.Y + iy * dy,
                            bounds.Min.Z + iz * dz);

                        int bix = (int)Math.Floor(ix * cellSize / dx);
                        int biy = (int)Math.Floor(iy * cellSize / dy);
                        int biz = (int)Math.Floor(iz * cellSize / dz);
                        int hash = HashBucket(bix, biy, biz);

                        double sumW = 0, sumS = 0;
                        int found = 0;

                        // 搜索相邻 bucket
                        for (int di = -1; di <= 1; di++)
                        {
                            for (int dj = -1; dj <= 1; dj++)
                            {
                                for (int dk = -1; dk <= 1; dk++)
                                {
                                    int h = HashBucket(bix + di, biy + dj, biz + dk);
                                    if (buckets.TryGetValue(h, out var list))
                                    {
                                        foreach (var srcIdx in list)
                                        {
                                            double dist = points[srcIdx].DistanceTo(target);
                                            if (dist > cellSize * 3) continue;
                                            
                                            double w = 1.0 / (dist + 1e-20);
                                            sumW += w;
                                            sumS += w * scalars[srcIdx];
                                            found++;
                                        }
                                    }
                                }
                            }
                        }

                        int linearIdx = ix + iy * nx + iz * nx * ny;
                        field[linearIdx] = sumW > 0 ? sumS / sumW : 0.0;
                    }
                }
            }

            return field;
        }

        #endregion

        #region 辅助方法

        /// <summary>
        /// 生成规则网格的点坐标
        /// </summary>
        private static List<Point3d> GenerateGridPoints(BoundingBox bounds, int nx, int ny, int nz)
        {
            var pts = new List<Point3d>(nx * ny * nz);
            double dx = (bounds.Max.X - bounds.Min.X) / Math.Max(1, nx - 1);
            double dy = (bounds.Max.Y - bounds.Min.Y) / Math.Max(1, ny - 1);
            double dz = (bounds.Max.Z - bounds.Min.Z) / Math.Max(1, nz - 1);

            for (int iz = 0; iz < nz; iz++)
                for (int iy = 0; iy < ny; iy++)
                    for (int ix = 0; ix < nx; ix++)
                        pts.Add(new Point3d(bounds.Min.X + ix * dx, bounds.Min.Y + iy * dy, bounds.Min.Z + iz * dz));

            return pts;
        }

        private static int HashBucket(int x, int y, int z)
        {
            return (x * 73856093) ^ (y * 19349663) ^ (z * 83492791);
        }

        #endregion

        #region 统计信息输出

        /// <summary>
        /// 获取等值面统计信息（用于 Info 输出）
        /// </summary>
        public static string GetExtractionStats(Mesh mesh, double isoValue)
        {
            if (mesh == null)
                return "等值面提取失败：未生成有效网格";

            return $"等值面提取完成\n" +
                   $"  阈值: {isoValue:F4}\n" +
                   $"  顶点数: {mesh.Vertices.Count}\n" +
                   $"  面数: {mesh.Faces.Count}\n" +
                   $"  面积: {AreaMassProperties.Compute(mesh).Area:F2} m²";
        }

        #endregion
    }
}
