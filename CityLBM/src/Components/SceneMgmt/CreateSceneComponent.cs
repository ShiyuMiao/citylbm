using System;
using System.Drawing;
using Grasshopper.Kernel;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.SceneMgmt
{
    /// <summary>
    /// 创建CityLBM场景组件
    /// 用于初始化一个新的模拟场景
    /// </summary>
    public class CreateSceneComponent : GH_Component
    {
        public CreateSceneComponent()
            : base("Create Scene", "Scene",
                   "创建CityLBM城市风场模拟场景",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter("Name", "N", "场景名称", GH_ParamAccess.item, "CityLBM Scene");
            pManager.AddNumberParameter("Wind Speed", "V", "风速 (m/s)", GH_ParamAccess.item, 5.0);
            pManager.AddVectorParameter("Wind Direction", "D", "风场方向（单位向量）", GH_ParamAccess.item, new Rhino.Geometry.Vector3d(1, 0, 0));
            pManager.AddNumberParameter("Domain Extension", "E", "计算域扩展比例 (0-1)", GH_ParamAccess.item, 0.2);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM场景对象", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string name = "CityLBM Scene";
            double windSpeed = 5.0;
            Rhino.Geometry.Vector3d windDir = new Rhino.Geometry.Vector3d(1, 0, 0);
            double extension = 0.2;

            // 读取输入参数
            if (!DA.GetData(0, ref name)) return;
            if (!DA.GetData(1, ref windSpeed)) return;
            if (!DA.GetData(2, ref windDir)) return;
            if (!DA.GetData(3, ref extension)) return;

            // 验证输入
            if (windSpeed <= 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "风速必须大于0");
                return;
            }

            if (extension < 0 || extension > 1)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "扩展比例建议在0-1之间");
            }

            // 创建场景
            Scene scene = new Scene(name);
            scene.WindSpeed = windSpeed;
            scene.DomainExtensionRatio = extension;

            // 标准化风向向量
            if (windDir.IsValid && !windDir.IsZero)
            {
                windDir.Unitize();
                scene.WindDirection = windDir;
            }

            // 输出场景
            DA.SetData(0, new GH_Scene(scene));
        }

        protected override Bitmap Icon
        {
            get
            {
                // TODO: 添加图标
                return null;
            }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A"); }
        }
    }
}
