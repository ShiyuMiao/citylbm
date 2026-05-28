using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Rendering;
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// VTK 等值面提取组件（v0.2.0 新增）
    /// 
    /// 使用 Marching Cubes 算法从 VTK 标量场中提取等值面。
    /// 支持从速度模、压力等标量场中提取指定阈值的等值面 Mesh。
    /// 
    /// 典型用途：
    ///   - 风速等值面：可视化特定风速的空间分布
    ///   - 压力等值面：分析建筑表面风压分布
    ///   - 涡量等值面：识别湍流区域
    /// </summary>
    public class IsosurfaceComponent : GH_Component
    {
        public IsosurfaceComponent()
            : base("Isosurface", "Iso",
                   "Marching Cubes 等值面提取【v0.2.0】\n" +
                   "从 VTK 标量场数据中提取指定阈值的等值面 Mesh。\n" +
                   "支持结构化网格和非结构化点云两种输入模式。",
                   "CityLBM", "Results")
        { }

        public override Guid ComponentGuid => new Guid("B3D7E1F4-9A2C-4B6D-8E5F-1A2B3C4D5E6F7");

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            // 输入点坐标和速度向量（来自 ReadVTK）
            pManager.AddPointParameter("Points", "Pt",
                "VTK 网格点坐标（来自 ReadVTK 的 Points 输出）",
                GH_ParamAccess.list);

            pManager.AddVectorParameter("Velocity", "V",
                "速度向量（来自 ReadVTK 的 Velocity 输出，用于计算速度模 |V|）",
                GH_ParamAccess.list);

            // 可选：直接输入标量场（优先使用）
            pManager.AddNumberParameter("Scalars", "Scal",
                "自定义标量场数据（如压力、涡量等）\n" +
                "若提供则使用此字段；否则使用 |V| 作为标量场",
                GH_ParamAccess.list);

            // 等值参数
            pManager.AddNumberParameter("Iso Value", "Val",
                "等值阈值\n" +
                "- 速度模模式: 提取 |V| = Val 的等值面 (m/s)\n" +
                "- 典型值: 2, 3, 5 m/s",
                GH_ParamAccess.item, 3.0);

            pManager.AddIntegerParameter("Grid Dims", "Dims",
                "网格维度 [nx, ny, nz]（可选，用于加速结构化网格处理）\n" +
                "留空则自动检测",
                GH_ParamAccess.list);
            pManager[4].Optional = true;

            // 模式选择
            pManager.AddIntegerParameter("Mode", "Mode",
                "标量场来源:\n" +
                "  0 = 速度模 |V|（默认）\n" +
                "  1 = 自定义 Scalars 输入",
                GH_ParamAccess.item, 0);

            // 所有参数可选（除 Points 和 Velocity）
            pManager[0].Optional = true;
            pManager[1].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddMeshParameter("Isosurface", "ISO",
                "等值面 Mesh（阈值 = Iso Value 处的曲面）",
                GH_ParamAccess.item);
            
            pManager.AddTextParameter("Info", "I",
                "等值面统计信息（顶点数、面数、面积等）",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Volume", "Vol",
                "等值面包围的体积估算（m³）",
                GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            var logger = new ComponentLogger("Isosurface");

            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            List<double> customScalars = null;
            double isoValue = 3.0;
            int[] gridDims = null;
            int mode = 0;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetDataList(2, customScalars);
            DA.GetData(3, ref isoValue);
            // 读取网格维度列表 [nx, ny, nz]
            var gridDimsList = new List<int>();
            if (DA.GetDataList(4, gridDimsList) && gridDimsList.Count == 3)
            {
                gridDims = gridDimsList.ToArray();
            }
            DA.GetData(5, ref mode);

            // 参数验证
            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "需要 Points 和 Velocity 数据（请连接 ReadVTK 的输出端）");
                return;
            }

            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "Points 和 Velocity 数量不匹配");
                return;
            }

            logger.Info($"输入点数: {points.Count}, 等值阈值: {isoValue:F3}, 模式: {(mode == 0 ? "速度模" : "自定义标量")}");

            // ── 构建标量场 ──────────────────────────────────────
            List<double> scalars;
            
            if (mode == 1 && customScalars != null && customScalars.Count == points.Count)
            {
                // 模式 1：用户提供的自定义标量场
                scalars = customScalars;
                logger.Info("使用自定义标量场");
            }
            else
            {
                // 模式 0：计算速度模 |V|
                scalars = velocities.Select(v => v.Length).ToList();
                logger.Info("计算速度模 |V| 作为标量场");

                double vMin = scalars.Min();
                double vMax = scalars.Max();
                logger.DataSummary("标量场统计", new Dictionary<string, object> 
                {
                    ["最小"] = vMin, ["最大"] = vMax, ["平均"] = scalars.Average()
                });
            }

            // ── 尝试自动检测网格维度 ────────────────────────────
            string gridDimsStr = "";
            if (gridDims == null || gridDims.Length != 3)
            {
                // 自动检测：假设为均匀立方体网格
                gridDims = DetectGridDimensions(points);
                if (gridDims != null)
                    gridDimsStr = $"自动检测: [{gridDims[0]}×{gridDims[1]}×{gridDims[2]}]";
                else
                    gridDimsStr = "非结构化网格（使用空间插值）";
            }
            else
            {
                gridDimsStr = $"用户提供: [{gridDims[0]}×{gridDims[1]}×{gridDims[2]}]";
            }
            
            logger.Info(gridDimsStr);

            // ── 提取等值面 ────────────────────────────────────────
            logger.StepStart("Marching Cubes 等值面提取");
            
            Mesh isosurface;
            DateTime startTime = DateTime.Now;

            if (gridDims != null && gridDims[0] >= 2 && gridDims[1] >= 2 && gridDims[2] >= 2)
            {
                // 结构化网格模式（快速路径）
                isosurface = IsosurfaceExtractor.ExtractIsosurface(
                    points, scalars, gridDims, isoValue);
            }
            else
            {
                // 非结构化点云模式（使用边界框 + 网格化插值）
                var bounds = new BoundingBox(points);
                int resolution = Math.Min(
                    (int)Math.Pow(points.Count / 10.0, 1.0/3.0),
                    64  // 最大 64^3 分辨率
                );
                
                isosurface = IsosurfaceExtractor.ExtractIsosurfaceFromCloud(
                    points, scalars, bounds, resolution, isoValue);
            }

            TimeSpan elapsed = DateTime.Now - startTime;
            logger.StepEnd("Marching Cubes", $"{elapsed.TotalMilliseconds:F0} ms");

            // ── 输出结果 ────────────────────────────────────────
            if (isosurface != null && isosurface.Faces.Count > 0)
            {
                DA.SetData(0, isosurface);
                
                double volume = ComputeEnclosedVolume(isosurface);
                double area = AreaMassProperties.Compute(isosurface).Area;

                string info = IsosurfaceExtractor.GetExtractionStats(isosurface, isoValue) + "\n\n" +
                             $"提取耗时: {elapsed.TotalMilliseconds:F0} ms\n" +
                             $"网格模式: {gridDimsStr}\n" +
                             $"体积估算: {volume:F2} m³";

                DA.SetData(1, info);
                DA.SetData(2, volume);
                
                logger.Finish();

                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"✓ 成功提取等值面: {isoValue} → {isosurface.Vertices.Count}顶点, {isosurface.Faces.Count}面");
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    $"未能在当前阈值 ({isoValue}) 找到有效的等值面。\n" +
                    "建议：调整 Iso Value 或检查标量场范围。");
                
                DA.SetData(0, null);
                DA.SetData(1, "未找到有效等值面");
                DA.SetData(2, 0);
            }
        }

        #region 辅助方法

        /// <summary>
        /// 尝试检测结构化网格的维度
        /// </summary>
        private static int[] DetectGridDimensions(IList<Point3d> pts)
        {
            if (pts.Count < 8) return null;

            // 方法：通过找唯一 X、Y、Z 坐标数来推断网格维度
            try
            {
                // 取前几个点的坐标精度来判断是否为规则网格
                var xVals = pts.Take(Math.Min(pts.Count, 100)).Select(p => Math.Round(p.X, 6)).Distinct().ToList();
                var yVals = pts.Take(Math.Min(pts.Count, 100)).Select(p => Math.Round(p.Y, 6)).Distinct().ToList();
                var zVals = pts.Take(Math.Min(pts.Count, 100)).Select(p => Math.Round(p.Z, 6)).Distinct().ToList();

                // 检查总点数是否等于 nx*ny*nz
                long total = (long)xVals.Count * yVals.Count * zVals.Count;
                if (Math.Abs(total - pts.Count) < total * 0.01)  // 容差 1%
                {
                    return new int[] { xVals.Count, yVals.Count, zVals.Count };
                }
            }
            catch { }
            return null;
        }

        /// <summary>
        /// 估算封闭 Mesh 包围的体积（简化方法）
        /// </summary>
        private static double ComputeEnclosedVolume(Mesh mesh)
        {
            if (mesh == null || !mesh.IsClosed)
                return 0.0;

            try
            {
                var vmp = VolumeMassProperties.Compute(mesh);
                return Math.Abs(vmp.Volume);
            }
            catch
            {
                return 0.0;
            }
        }

        #endregion

        protected override Bitmap Icon => IconLoader.Load("Isosurface.png");
    }
}
