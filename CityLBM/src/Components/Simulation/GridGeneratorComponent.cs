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
            pManager.AddNumberParameter("Cell Size", "dx", "网格单元尺寸（米）", GH_ParamAccess.item, 1.0);
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

            if (!DA.GetData(0, ref ghScene)) return;
            if (!DA.GetData(1, ref cellSize)) return;

            if (ghScene == null || ghScene.Value == null)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "场景对象无效");
                return;
            }

            Scene scene = ghScene.Value;

            // 验证场景
            if (!scene.Validate(out string errorMsg))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, errorMsg);
                return;
            }

            // 生成网格
            GridGenerator generator = new GridGenerator(cellSize);
            CartesianGrid grid = generator.Generate(scene);

            // 输出
            DA.SetData(0, new GH_CartesianGrid(grid));
            DA.SetData(1, $"网格尺寸: {grid.Nx} x {grid.Ny} x {grid.Nz}\n" +
                         $"总单元格: {generator.Statistics.TotalCells}\n" +
                         $"流体单元: {generator.Statistics.FluidCells}\n" +
                         $"障碍物单元: {generator.Statistics.ObstacleCells}");
        }

        protected override Bitmap Icon
        {
            get { return null; }
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
