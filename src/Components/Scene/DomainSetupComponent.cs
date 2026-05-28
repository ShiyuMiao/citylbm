using System;
using System.Collections.Generic;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Rendering;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Scene
{
    /// <summary>
    /// AIJ 标准计算域设置组件
    /// 根据建筑体块和风向自动计算 AIJ 规范计算域（迎风5H，背风15H，侧面5H，顶部5H）
    /// 提供可视化预览，防止建筑画在计算域外面
    /// </summary>
    public class DomainSetupComponent : GH_Component
    {
        private DomainPreviewerConduit _conduit;
        private bool _conduitEnabled = false;

        // AIJ 默认系数
        private const double DEFAULT_UPSTREAM_RATIO = 5.0;    // 迎风面 5H
        private const double DEFAULT_DOWNSTREAM_RATIO = 15.0; // 背风面 15H
        private const double DEFAULT_SIDE_RATIO = 5.0;        // 侧面 5H
        private const double DEFAULT_TOP_RATIO = 5.0;         // 顶部 5H

        public DomainSetupComponent()
            : base("Domain Setup", "DomainSetup",
                   "基于 AIJ 规范自动计算流体计算域。\n" +
                   "根据建筑体块和风向自动推算：\n" +
                   "  迎风面 = 5 × 建筑高度\n" +
                   "  背风面 = 15 × 建筑高度\n" +
                   "  侧面 = 5 × 建筑高度\n" +
                   "  顶部 = 5 × 建筑高度\n" +
                   "可视化预览帮助确认边界条件设置。",
                   "CityLBM", "Scene")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGeometryParameter("Buildings", "B",
                "建筑体块（Brep 或 Mesh）。支持多个建筑，自动计算整体包围盒。",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Wind Direction", "WD",
                "来风方向角度（度）。0°=北风，90°=东风。用于确定入口/出口位置。",
                GH_ParamAccess.item, 0.0);

            pManager.AddNumberParameter("Upstream Ratio", "UR",
                "迎风面距离系数（相对于建筑高度）。默认 5（AIJ 推荐）。",
                GH_ParamAccess.item, DEFAULT_UPSTREAM_RATIO);

            pManager.AddNumberParameter("Downstream Ratio", "DR",
                "背风面距离系数（相对于建筑高度）。默认 15（AIJ 推荐）。",
                GH_ParamAccess.item, DEFAULT_DOWNSTREAM_RATIO);

            pManager.AddNumberParameter("Side Ratio", "SR",
                "侧面距离系数（相对于建筑高度）。默认 5（AIJ 推荐）。",
                GH_ParamAccess.item, DEFAULT_SIDE_RATIO);

            pManager.AddNumberParameter("Top Ratio", "TR",
                "顶部距离系数（相对于建筑高度）。默认 5（AIJ 推荐）。",
                GH_ParamAccess.item, DEFAULT_TOP_RATIO);

            pManager.AddNumberParameter("Custom Height", "H",
                "自定义参考高度（米）。默认 0 表示使用建筑最大高度。",
                GH_ParamAccess.item, 0.0);

            pManager.AddBooleanParameter("Preview", "P",
                "是否在视口中预览计算域。",
                GH_ParamAccess.item, true);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S",
                "CityLBM 场景对象（包含计算域设置）。可连接到后续组件。",
                GH_ParamAccess.item);

            pManager.AddBrepParameter("Domain Box", "Box",
                "计算域边界框（Brep 形式）。",
                GH_ParamAccess.item);

            pManager.AddTextParameter("Domain Info", "Info",
                "计算域详细信息。",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Dimensions", "Dim",
                "计算域尺寸 [Lx, Ly, Lz]（米）。",
                GH_ParamAccess.list);

            pManager.AddPointParameter("Building Center", "BC",
                "建筑群中心点。",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Building Height", "BH",
                "建筑参考高度（米）。",
                GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 获取输入
            List<IGH_GeometricGoo> buildingGeos = new List<IGH_GeometricGoo>();
            double windDirection = 0.0;
            double upstreamRatio = DEFAULT_UPSTREAM_RATIO;
            double downstreamRatio = DEFAULT_DOWNSTREAM_RATIO;
            double sideRatio = DEFAULT_SIDE_RATIO;
            double topRatio = DEFAULT_TOP_RATIO;
            double customHeight = 0.0;
            bool preview = true;

            if (!DA.GetDataList(0, buildingGeos) || buildingGeos.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "请至少输入一个建筑体块");
                return;
            }

            DA.GetData(1, ref windDirection);
            DA.GetData(2, ref upstreamRatio);
            DA.GetData(3, ref downstreamRatio);
            DA.GetData(4, ref sideRatio);
            DA.GetData(5, ref topRatio);
            DA.GetData(6, ref customHeight);
            DA.GetData(7, ref preview);

            // 归一化风向角度
            windDirection = NormalizeAngle(windDirection);

            // 验证系数
            if (upstreamRatio < 1) upstreamRatio = 1;
            if (downstreamRatio < 1) downstreamRatio = 1;
            if (sideRatio < 1) sideRatio = 1;
            if (topRatio < 0.5) topRatio = 0.5;

            // 提取建筑几何并计算包围盒
            List<Mesh> buildingMeshes = new List<Mesh>();
            BoundingBox buildingBounds = BoundingBox.Unset;

            foreach (var geo in buildingGeos)
            {
                if (geo == null) continue;

                Mesh mesh = null;

                // 尝试转换为 Mesh
                if (geo is GH_Mesh ghMesh)
                {
                    mesh = ghMesh.Value;
                }
                else if (geo is GH_Brep ghBrep)
                {
                    // Brep 转换为 Mesh
                    var brep = ghBrep.Value;
                    if (brep != null && brep.IsValid)
                    {
                        var mp = MeshingParameters.Default;
                        mp.MinimumEdgeLength = 0.1;
                        mp.MaximumEdgeLength = 5.0;
                        Mesh[] meshes = Mesh.CreateFromBrep(brep, mp);
                        if (meshes != null && meshes.Length > 0)
                        {
                            var merged = new Mesh();
                            foreach (var m in meshes) merged.Append(m);
                            mesh = merged;
                        }
                    }
                }
                else if (geo is GH_Surface ghSrf)
                {
                    var brep = ghSrf.Value;
                    if (brep != null)
                    {
                        var mp = MeshingParameters.Default;
                        Mesh[] meshes = Mesh.CreateFromBrep(brep, mp);
                        if (meshes != null && meshes.Length > 0)
                        {
                            var merged = new Mesh();
                            foreach (var m in meshes) merged.Append(m);
                            mesh = merged;
                        }
                    }
                }

                if (mesh != null && mesh.IsValid)
                {
                    buildingMeshes.Add(mesh);
                    var bounds = mesh.GetBoundingBox(false);
                    if (buildingBounds.IsValid)
                        buildingBounds.Union(bounds);
                    else
                        buildingBounds = bounds;
                }
            }

            if (buildingMeshes.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "无法从输入提取有效的建筑几何");
                return;
            }

            // 计算建筑参数
            double buildingHeight = customHeight > 0
                ? customHeight
                : buildingBounds.Max.Z - buildingBounds.Min.Z;

            Point3d buildingCenter = new Point3d(
                (buildingBounds.Min.X + buildingBounds.Max.X) / 2.0,
                (buildingBounds.Min.Y + buildingBounds.Max.Y) / 2.0,
                buildingBounds.Min.Z);

            // 根据风向计算计算域尺寸
            // 风向角度：0=北风（从北来，向南吹），90=东风（从东来，向西吹）
            double angleRad = windDirection * Math.PI / 180.0;
            Vector3d windDir = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);

            // 计算上游/下游在 X/Y 方向的投影
            // 上游距离 = 来风方向的反方向
            double upstreamDist = buildingHeight * upstreamRatio;
            double downstreamDist = buildingHeight * downstreamRatio;
            double sideDist = buildingHeight * sideRatio;
            double topDist = buildingHeight * topRatio;

            // 计算计算域边界
            // 以建筑中心为基准，根据风向确定各方向扩展
            Vector3d upstreamDir = -windDir;
            upstreamDir.Unitize();
            Vector3d sideDir = Vector3d.CrossProduct(Vector3d.ZAxis, windDir);
            sideDir.Unitize();

            // 计算域边界（相对于建筑中心）
            double xMinus, xPlus, yMinus, yPlus;

            // 根据风向确定 X/Y 方向的上下游
            if (Math.Abs(windDir.X) > Math.Abs(windDir.Y))
            {
                // 主要是 X 方向来风
                if (windDir.X > 0) // 从东来（西风）
                {
                    xMinus = upstreamDist;
                    xPlus = downstreamDist;
                }
                else // 从西来（东风）
                {
                    xMinus = downstreamDist;
                    xPlus = upstreamDist;
                }
                yMinus = yPlus = sideDist;
            }
            else
            {
                // 主要是 Y 方向来风
                xMinus = xPlus = sideDist;
                if (windDir.Y > 0) // 从南来（北风）
                {
                    yMinus = upstreamDist;
                    yPlus = downstreamDist;
                }
                else // 从北来（南风）
                {
                    yMinus = downstreamDist;
                    yPlus = upstreamDist;
                }
            }

            // 创建 DomainDefinition
            var domainDef = new DomainDefinition
            {
                XMinus = xMinus,
                XPlus = xPlus,
                YMinus = yMinus,
                YPlus = yPlus,
                Height = topDist
            };

            // 创建场景
            Core.Scene scene = new Core.Scene("AIJ_Domain_Scene");
            foreach (var mesh in buildingMeshes)
            {
                scene.AddBuilding(mesh);
            }

            // 设置风向和风速
            scene.SetWindCondition(windDir, 5.0); // 默认风速5m/s
            scene.SetCustomDomain(domainDef);

            // 获取计算域边界框
            BoundingBox domainBox = scene.GetSimulationDomain();

            // 创建 Brep 输出
            Brep domainBrep = Brep.CreateFromBox(domainBox);

            // 构建信息文本
            string dirText = GetDirectionText(windDirection);
            string info = $"═══ AIJ 计算域设置 ═══\n" +
                         $"风向: {dirText} ({windDirection:F1}°)\n" +
                         $"建筑高度: {buildingHeight:F2} m\n" +
                         $"建筑中心: ({buildingCenter.X:F2}, {buildingCenter.Y:F2}, {buildingCenter.Z:F2})\n\n" +
                         $"计算域尺寸:\n" +
                         $"  X- (上游): {xMinus:F2} m\n" +
                         $"  X+ (下游): {xPlus:F2} m\n" +
                         $"  Y- (左侧): {yMinus:F2} m\n" +
                         $"  Y+ (右侧): {yPlus:F2} m\n" +
                         $"  Z (高度): {topDist:F2} m\n\n" +
                         $"总尺寸: {domainBox.Max.X - domainBox.Min.X:F2} × " +
                         $"{domainBox.Max.Y - domainBox.Min.Y:F2} × " +
                         $"{domainBox.Max.Z - domainBox.Min.Z:F2} m\n\n" +
                         $"边界条件:\n" +
                         $"  入口: Velocity Inlet\n" +
                         $"  出口: Pressure Outlet (P=0)\n" +
                         $"  侧面/顶面: Slip Wall\n" +
                         $"  地面: No-Slip Wall";

            // 验证建筑是否在计算域内
            if (!domainBox.Contains(buildingBounds))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    "警告：建筑体块超出计算域边界！请检查输入几何或调整系数。");
            }

            // 初始化并更新 Conduit
            if (preview)
            {
                InitializeConduit();
                _conduit.SetDomain(domainBox, windDirection);

                if (!_conduitEnabled)
                {
                    _conduit.Enabled = true;
                    _conduitEnabled = true;
                }
            }
            else
            {
                CleanupConduit();
            }

            // 输出
            DA.SetData(0, new GH_Scene(scene));
            DA.SetData(1, domainBrep);
            DA.SetData(2, info);
            DA.SetDataList(3, new List<double>
            {
                domainBox.Max.X - domainBox.Min.X,
                domainBox.Max.Y - domainBox.Min.Y,
                domainBox.Max.Z - domainBox.Min.Z
            });
            DA.SetData(4, buildingCenter);
            DA.SetData(5, buildingHeight);
        }

        /// <summary>
        /// 初始化 DisplayConduit
        /// </summary>
        private void InitializeConduit()
        {
            if (_conduit == null)
            {
                _conduit = new DomainPreviewerConduit();
            }
        }

        /// <summary>
        /// 组件从文档移除时清理 Conduit
        /// </summary>
        public override void RemovedFromDocument(GH_Document document)
        {
            CleanupConduit();
            base.RemovedFromDocument(document);
        }

        /// <summary>
        /// 文档关闭时清理
        /// </summary>
        public override void DocumentContextChanged(GH_Document document, GH_DocumentContext context)
        {
            if (context == GH_DocumentContext.Close)
            {
                CleanupConduit();
            }
            base.DocumentContextChanged(document, context);
        }

        /// <summary>
        /// 清理 Conduit 资源
        /// </summary>
        private void CleanupConduit()
        {
            if (_conduit != null)
            {
                _conduit.Enabled = false;
                _conduit.Clear();
                _conduit = null;
                _conduitEnabled = false;
            }
        }

        /// <summary>
        /// 将角度归一化到 [0, 360)
        /// </summary>
        private double NormalizeAngle(double angle)
        {
            while (angle < 0) angle += 360.0;
            while (angle >= 360.0) angle -= 360.0;
            return angle;
        }

        /// <summary>
        /// 获取风向文字描述
        /// </summary>
        private string GetDirectionText(double degrees)
        {
            string[] directions = { "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW" };
            int index = (int)((degrees + 11.25) / 22.5) % 16;
            return directions[index];
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("DomainSetup.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("D5E8F2A1-7B4C-4D9E-8F3A-6C2E5B8D1F4A"); }
        }
    }
}
