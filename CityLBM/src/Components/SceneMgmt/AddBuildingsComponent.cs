using System;
using System.Collections.Generic;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.SceneMgmt
{
    /// <summary>
    /// 添加建筑物到场景组件
    /// </summary>
    public class AddBuildingsComponent : GH_Component
    {
        public AddBuildingsComponent()
            : base("Add Buildings", "AddBld",
                   "向CityLBM场景添加建筑物Mesh",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "CityLBM场景对象", GH_ParamAccess.item);
            pManager.AddMeshParameter("Buildings", "B", "建筑物Mesh（单个或列表）", GH_ParamAccess.list);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S", "更新后的CityLBM场景对象", GH_ParamAccess.item);
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

            // 获取Mesh列表
            var meshList = new List<Mesh>();
            List<GH_Mesh> ghMeshes = new List<GH_Mesh>();
            if (!DA.GetDataList(1, ghMeshes))
            {
                // 尝试获取单个Mesh
                GH_Mesh ghMesh = null;
                if (DA.GetData(1, ref ghMesh) && ghMesh != null && ghMesh.Value != null)
                {
                    meshList.Add(ghMesh.Value);
                }
            }
            else
            {
                foreach (var ghMesh in ghMeshes)
                {
                    if (ghMesh != null && ghMesh.Value != null)
                    {
                        meshList.Add(ghMesh.Value);
                    }
                }
            }

            if (meshList.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有添加任何有效的Mesh，组件未更新场景");
                return;
            }

            // 添加到场景
            try
            {
                scene.AddBuildings(meshList);
            }
            catch (Exception ex)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, ex.Message);
                return;
            }

            // 输出更新后的场景
            DA.SetData(0, new GH_Scene(scene));
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
            get { return new Guid("D4E7F2A8-7C9B-5E8D-0B1A-3E5C6D9F8A2B"); }
        }
    }
}
