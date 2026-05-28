using System;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using CityLBM.Core;
using CityLBM.Utils;

namespace CityLBM.Components.Simulation
{
    /// <summary>
    /// 网格生成组件
    /// 将场景转换为笛卡尔网格用于 LBM 模拟
    /// </summary>
    public class GridGeneratorComponent : GH_Component
    {
        public GridGeneratorComponent()
            : base("Generate Grid", "Grid",
                   "为城市场景生成笛卡尔网格",
                   "CityLBM", "Simulation")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM 场景对象", GH_ParamAccess.item);
            pManager.AddNumberParameter("Cell Size", "dx", "网格单元尺寸（米）。输入0或负数启用自动优化", GH_ParamAccess.item, 1.0);
            pManager.AddBooleanParameter("Auto Optimize", "Auto", "自动优化网格大小（推荐）", GH_ParamAccess.item, true);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Grid", "G", "生成的笛卡尔网格", GH_ParamAccess.item);
            pManager.AddTextParameter("Info", "I", "网格统计信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            GH_Scene ghScene = null;
            double cellSize = 1.0;
            bool autoOptimize = true;

            if (!DA.GetData(0, ref ghScene)) return;
            if (!DA.GetData(1, ref cellSize)) return;
            DA.GetData(2, ref autoOptimize);

            if (ghScene == null || ghScene.Value == null)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "场景对象无效");
                return;
            }

            Core.Scene scene = ghScene.Value;

            // 验证场景
            if (!scene.Validate(out string errorMsg))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, errorMsg);
                return;
            }

            // 获取计算域信息
            var domain = scene.GetSimulationDomain();
            double domainLx = domain.Max.X - domain.Min.X;
            double domainLy = domain.Max.Y - domain.Min.Y;
            double domainLz = domain.Max.Z - domain.Min.Z;

            // 自动优化网格大小
            double optimizedCellSize = cellSize;
            string optimizationInfo = "";
            
            if (autoOptimize || cellSize <= 0)
            {
                optimizedCellSize = CalculateOptimalCellSize(domainLx, domainLy, domainLz);
                optimizationInfo = $"\n[自动优化] 原始 dx={cellSize:F2}m → 优化 dx={optimizedCellSize:F2}m";
                
                if (cellSize > 0 && Math.Abs(cellSize - optimizedCellSize) > 0.01)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, 
                        $"网格已自动优化: {cellSize:F2}m → {optimizedCellSize:F2}m\n" +
                        $"目标: 总格点数控制在 100-500万之间，确保模拟效率");
                }
            }

            // 生成网格
            GridGenerator generator = new GridGenerator(optimizedCellSize);
            CartesianGrid grid = generator.Generate(scene);

            // 计算预估模拟时间
            string timeEstimate = EstimateSimulationTime(grid.Nx, grid.Ny, grid.Nz);

            string domainMode = scene.UseAbsoluteDomain ? "绝对尺寸" :
                               (scene.UseCustomDomain ? "自定义偏移" : "自动扩展");

            // 输出
            DA.SetData(0, new GH_CartesianGrid(grid));
            DA.SetData(1, $"═══ 网格信息 ═══\n" +
                         $"网格尺寸: {grid.Nx} x {grid.Ny} x {grid.Nz}\n" +
                         $"总单元格: {generator.Statistics.TotalCells:N0}\n" +
                         $"流体单元: {generator.Statistics.FluidCells:N0}\n" +
                         $"障碍物单元: {generator.Statistics.ObstacleCells:N0}{optimizationInfo}\n\n" +
                         $"═══ 计算域信息 ═══\n" +
                         $"域模式: {domainMode}\n" +
                         $"域尺寸: {domainLx:F2}m x {domainLy:F2}m x {domainLz:F2}m\n" +
                         $"域范围: X[{domain.Min.X:F2}, {domain.Max.X:F2}] Y[{domain.Min.Y:F2}, {domain.Max.Y:F2}] Z[{domain.Min.Z:F2}, {domain.Max.Z:F2}]\n\n" +
                         $"═══ 性能预估 ═══\n" +
                         $"预估时间: {timeEstimate}\n" +
                         $"建议: 总格点数 {(grid.Nx * grid.Ny * grid.Nz > 5000000 ? "⚠️ 偏大，建议减小计算域或增大dx" : "✓ 适中")}");
        }

        /// <summary>
        /// 根据计算域尺寸自动计算最优网格间距
        /// 目标：总格点数控制在 100-500万之间
        /// </summary>
        private double CalculateOptimalCellSize(double lx, double ly, double lz)
        {
            // 目标总格点数范围
            const long targetCellsMin = 1000000;   // 100万
            const long targetCellsMax = 5000000;   // 500万
            const long targetCellsIdeal = 2500000; // 250万（理想值）

            // 计算域体积
            double volume = lx * ly * lz;

            // 根据目标格点数反推网格间距
            // N = V / dx^3 → dx = (V/N)^(1/3)
            double dxIdeal = Math.Pow(volume / targetCellsIdeal, 1.0 / 3.0);
            
            // 限制 dx 范围（城市风环境合理范围）
            double dxMin = 0.5;  // 最小 0.5m（精细模拟）
            double dxMax = 10.0; // 最大 10m（快速预览）
            
            dxIdeal = Math.Max(dxMin, Math.Min(dxMax, dxIdeal));

            // 向上取整到 0.5m 的倍数（便于理解）
            dxIdeal = Math.Ceiling(dxIdeal * 2) / 2;

            // 验证总格点数是否在目标范围内
            long nx = (long)Math.Ceiling(lx / dxIdeal);
            long ny = (long)Math.Ceiling(ly / dxIdeal);
            long nz = (long)Math.Ceiling(lz / dxIdeal);
            long totalCells = nx * ny * nz;

            // 如果超出范围，微调 dx
            if (totalCells > targetCellsMax)
            {
                // 格点太多，增大 dx
                dxIdeal = Math.Pow(volume / targetCellsMax, 1.0 / 3.0);
                dxIdeal = Math.Ceiling(dxIdeal * 2) / 2;
            }
            else if (totalCells < targetCellsMin)
            {
                // 格点太少，减小 dx（但不低于最小值）
                dxIdeal = Math.Pow(volume / targetCellsMin, 1.0 / 3.0);
                dxIdeal = Math.Max(dxMin, dxIdeal);
                dxIdeal = Math.Ceiling(dxIdeal * 2) / 2;
            }

            return dxIdeal;
        }

        /// <summary>
        /// 根据网格大小预估模拟时间
        /// </summary>
        private string EstimateSimulationTime(int nx, int ny, int nz)
        {
            long totalCells = (long)nx * ny * nz;
            
            // 基于 RTX 3060 的经验估算（D3Q19, FP32）
            // 约 100万格点/秒 的处理能力
            double cellsPerSecond = 1000000;
            
            // 2000 步的总计算量
            double totalOperations = totalCells * 2000;
            double estimatedSeconds = totalOperations / cellsPerSecond;

            if (estimatedSeconds < 60)
                return $"约 {estimatedSeconds:F0} 秒";
            else if (estimatedSeconds < 3600)
                return $"约 {estimatedSeconds/60:F1} 分钟";
            else
                return $"约 {estimatedSeconds/3600:F1} 小时 ⚠️";
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("GridGenerator.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("E8F4A2D1-7B3C-4E8D-9A5F-3D6E7C8B9A1E"); }
        }
    }

    /// <summary>
    /// 笛卡尔网格包装类（用于 Grasshopper 数据传递）
    /// </summary>
    public class GH_CartesianGrid : GH_Goo<CartesianGrid>
    {
        public GH_CartesianGrid() { }
        public GH_CartesianGrid(CartesianGrid grid) : base(grid) { }

        public override IGH_Goo Duplicate()
        {
            return new GH_CartesianGrid(Value);
        }

        public override string ToString()
        {
            if (Value == null) return "Null Grid";
            return $"Cartesian Grid: {Value.Nx} x {Value.Ny} x {Value.Nz}";
        }

        public override string TypeName => "CartesianGrid";
        public override string TypeDescription => "笛卡尔网格用于 LBM 模拟";
        public override bool IsValid => Value != null;
    }
}
