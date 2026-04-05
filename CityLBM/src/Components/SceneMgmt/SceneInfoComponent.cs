using System;
using System.Drawing;
using Grasshopper.Kernel;
using CityLBM.Utils;
using CityLBM.Core;
using Rhino.Geometry;

namespace CityLBM.Components.SceneMgmt
{
    /// <summary>
    /// 显示场景信息组件
    /// </summary>
    public class SceneInfoComponent : GH_Component
    {
        public SceneInfoComponent()
            : base("Scene Info", "Info",
                   "显示CityLBM场景的统计信息",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM场景对象", GH_ParamAccess.item);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Name", "N", "场景名称", GH_ParamAccess.item);
            pManager.AddIntegerParameter("Building Count", "BC", "建筑物数量", GH_ParamAccess.item);
            pManager.AddIntegerParameter("Total Vertices", "TV", "总顶点数", GH_ParamAccess.item);
            pManager.AddIntegerParameter("Total Faces", "TF", "总面数", GH_ParamAccess.item);
            pManager.AddNumberParameter("Wind Speed", "V", "风速 (m/s)", GH_ParamAccess.item);
            pManager.AddVectorParameter("Wind Direction", "D", "风场方向", GH_ParamAccess.item);
            pManager.AddBoxParameter("Domain Bounds", "B", "计算域边界框", GH_ParamAccess.item);
            pManager.AddTextParameter("Validation", "Val", "验证状态", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 获取Scene
            GH_Scene ghScene = null;
            if (!DA.GetData(0, ref ghScene) || ghScene == null || !ghScene.IsValid)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "需要有效的场景对象");
                return;
            }

            Scene scene = ghScene.Value;

            // 验证场景
            string validationMsg = "";
            bool isValid = scene.Validate(out validationMsg);

            // 获取统计信息
            SceneStatistics stats = scene.GetStatistics();

            // 输出信息
            DA.SetData(0, scene.Name);
            DA.SetData(1, stats.BuildingCount);
            DA.SetData(2, stats.TotalVertices);
            DA.SetData(3, stats.TotalFaces);
            DA.SetData(4, stats.WindSpeed);
            DA.SetData(5, stats.WindDirection);

            if (stats.DomainBounds.IsValid)
            {
                DA.SetData(6, new Box(stats.DomainBounds));
            }
            else
            {
                DA.SetData(6, Box.Unset);
            }

            DA.SetData(7, isValid ? "✓ Valid" : "✗ " + validationMsg);

            // 如果场景无效，显示警告
            if (!isValid)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, validationMsg);
            }
        }

        protected override Bitmap Icon
        {
            get
            {
                return null;
            }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("E5F8B3C9-8D0A-6F9E-1C2B-4E6D7A0B3C9A"); }
        }
    }
}
