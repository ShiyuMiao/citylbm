using System;
using System.Drawing;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Solver;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 切片可视化组件
    /// 在指定平面上提取速度场切片并可视化
    /// 支持任意方向平面：按平面的 U/V 轴投影进行网格化
    /// </summary>
    public class SliceVisualizationComponent : GH_Component
    {
        public SliceVisualizationComponent()
            : base("Velocity Slice", "Slice",
                   "在指定平面上提取速度场切片（支持任意方向平面）",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt", "网格点坐标", GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V", "速度向量", GH_ParamAccess.list);
            pManager.AddPlaneParameter("Slice Plane", "P",
                "切片平面。\n" +
                "⚠ 重要：平面原点必须位于点云范围内！\n" +
                "留空时自动使用点云中心高度的水平面。\n" +
                "示例：右键 → Set One Plane，在 Rhino 中指定平面位置。",
                GH_ParamAccess.item);
            pManager[2].Optional = true;
            pManager.AddNumberParameter("Tolerance", "T",
                "切片厚度容差（m）。留空时自动估算为网格间距的 1.5 倍。",
                GH_ParamAccess.item);
            pManager[3].Optional = true;
            pManager.AddNumberParameter("Grid Size", "G", "输出网格尺寸（自动估算时设为 0）", GH_ParamAccess.item, 0.0);
            pManager.AddColourParameter("Color Low", "CL", "低速颜色", GH_ParamAccess.item, Color.Blue);
            pManager.AddColourParameter("Color High", "CH", "高速颜色", GH_ParamAccess.item, Color.Red);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddPointParameter("Slice Points", "Pt", "切片上的点", GH_ParamAccess.list);
            pManager.AddVectorParameter("Slice Velocity", "V", "切片上的速度", GH_ParamAccess.list);
            pManager.AddNumberParameter("Velocity Magnitude", "M", "速度大小", GH_ParamAccess.list);
            pManager.AddMeshParameter("Slice Mesh", "Mesh", "带顶点颜色的切片网格", GH_ParamAccess.item);
            pManager.AddNumberParameter("Min Value", "Min", "切片上的最小速度", GH_ParamAccess.item);
            pManager.AddNumberParameter("Max Value", "Max", "切片上的最大速度", GH_ParamAccess.item);
            pManager.AddTextParameter("Info", "I", "切片信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            Plane slicePlane = Plane.Unset;
            double tolerance = -1.0; // -1 = 自动
            double gridSize = 0.0; // 0 = 自动
            Color colorLow = Color.Blue;
            Color colorHigh = Color.Red;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetData(2, ref slicePlane);
            DA.GetData(3, ref tolerance);
            DA.GetData(4, ref gridSize);
            DA.GetData(5, ref colorLow);
            DA.GetData(6, ref colorHigh);

            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据");
                return;
            }

            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数和速度数不匹配");
                return;
            }

            // 先估算网格间距（用于自动容差）
            double autoSpacing = EstimateGridSpacing(points);

            // 自动平面：使用点云中心高度的水平面
            if (!slicePlane.IsValid)
            {
                BoundingBox bbox0 = new BoundingBox(points);
                Point3d center = bbox0.Center;
                slicePlane = new Plane(center, Vector3d.ZAxis);
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"未指定切片平面，自动使用点云中心水平面（Z={center.Z:F1} m）");
            }

            // 自动容差：1.5 倍网格间距
            if (tolerance <= 0)
                tolerance = autoSpacing * 1.5;

            // 提取切片上的点
            List<Point3d> slicePoints = new List<Point3d>();
            List<Vector3d> sliceVelocities = new List<Vector3d>();
            List<double> magnitudes = new List<double>();

            for (int i = 0; i < points.Count; i++)
            {
                Point3d pt = points[i];
                double dist = slicePlane.DistanceTo(pt);

                if (Math.Abs(dist) < tolerance)
                {
                    slicePoints.Add(pt);
                    sliceVelocities.Add(velocities[i]);
                    magnitudes.Add(velocities[i].Length);
                }
            }

            if (slicePoints.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    $"切片平面上没有找到点（容差 {tolerance} m）。" +
                    "尝试增大 Tolerance 或调整切片平面位置。");
                DA.SetDataList(0, slicePoints);
                DA.SetDataList(1, sliceVelocities);
                DA.SetDataList(2, magnitudes);
                DA.SetData(3, new Mesh());
                DA.SetData(4, 0.0);
                DA.SetData(5, 0.0);
                DA.SetData(6, "无切片数据");
                return;
            }

            // 计算值范围
            double minVal = magnitudes.Min();
            double maxVal = magnitudes.Max();

            // 自动估算网格尺寸：基于切片点的 2D 间距
            if (gridSize <= 0)
            {
                gridSize = EstimateGridSpacing(slicePoints);
                // 网格尺寸用 1.2 倍间距（覆盖相邻格子）
                gridSize = Math.Max(0.1, gridSize * 1.2);
            }

            // 创建切片网格（按平面 U/V 轴投影网格化）
            Mesh sliceMesh = CreateSliceMesh(slicePoints, magnitudes, gridSize, slicePlane,
                minVal, maxVal, colorLow, colorHigh);

            // 构建 Info 文本
            string planeDesc = GetPlaneDescription(slicePlane);
            string info = $"══════════════════════════════\n" +
                          $"  速度场切片信息\n" +
                          $"══════════════════════════════\n" +
                          $"  切片方向: {planeDesc}\n" +
                          $"  切片厚度: {tolerance} m\n" +
                          $"  网格尺寸: {gridSize:F2} m\n" +
                          $"  切片点数: {slicePoints.Count:N0}\n" +
                          $"  速度范围: {minVal:E3} ~ {maxVal:E3}\n" +
                          $"══════════════════════════════";

            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                $"切片提取完成：{slicePoints.Count:N0} 个点，速度 {minVal:E3} ~ {maxVal:E3}，网格 {gridSize:F2} m");

            DA.SetDataList(0, slicePoints);
            DA.SetDataList(1, sliceVelocities);
            DA.SetDataList(2, magnitudes);
            DA.SetData(3, sliceMesh);
            DA.SetData(4, minVal);
            DA.SetData(5, maxVal);
            DA.SetData(6, info);
        }

        /// <summary>
        /// 创建切片网格 —— 按平面 U/V 轴投影进行网格化
        /// 支持任意方向平面（XY / XZ / YZ / 倾斜）
        /// </summary>
        private Mesh CreateSliceMesh(List<Point3d> points, List<double> values,
            double gridSize, Plane plane, double minVal, double maxVal,
            Color colorLow, Color colorHigh)
        {
            Mesh mesh = new Mesh();

            if (points.Count == 0 || values.Count == 0 || points.Count != values.Count)
                return mesh;

            double valRange = maxVal - minVal;
            if (valRange < 1e-10) valRange = 1.0;

            // 平面局部坐标系：U 轴、V 轴
            Vector3d axisU = plane.XAxis;
            Vector3d axisV = plane.YAxis;
            Point3d origin = plane.Origin;

            // 将所有点投影到平面坐标系 (u, v)，记录索引
            var uvCoords = new List<(int index, double u, double v, double value)>(points.Count);
            for (int i = 0; i < points.Count; i++)
            {
                Point3d pt = points[i];
                // 投影到平面坐标：u = dot(pt - origin, axisU), v = dot(pt - origin, axisV)
                Vector3d delta = pt - origin;
                double u = delta * axisU;
                double v = delta * axisV;
                uvCoords.Add((i, u, v, values[i]));
            }

            // 找到 UV 范围
            double minU = uvCoords.Min(c => c.u);
            double maxU = uvCoords.Max(c => c.u);
            double minV = uvCoords.Min(c => c.v);
            double maxV = uvCoords.Max(c => c.v);

            // 创建网格索引（按 UV 坐标网格化）
            Dictionary<string, (int vertIdx, double value)> gridData =
                new Dictionary<string, (int, double)>();

            for (int i = 0; i < uvCoords.Count; i++)
            {
                var c = uvCoords[i];
                int gu = (int)Math.Floor((c.u - minU) / gridSize);
                int gv = (int)Math.Floor((c.v - minV) / gridSize);
                string key = $"{gu}_{gv}";

                if (!gridData.ContainsKey(key))
                {
                    mesh.Vertices.Add((float)points[c.index].X,
                                      (float)points[c.index].Y,
                                      (float)points[c.index].Z);
                    gridData[key] = (mesh.Vertices.Count - 1, c.value);
                }
            }

            // 创建网格面
            int nu = (int)Math.Ceiling((maxU - minU) / gridSize);
            int nv = (int)Math.Ceiling((maxV - minV) / gridSize);

            for (int i = 0; i < nu - 1; i++)
            {
                for (int j = 0; j < nv - 1; j++)
                {
                    string k00 = $"{i}_{j}";
                    string k10 = $"{i + 1}_{j}";
                    string k01 = $"{i}_{j + 1}";
                    string k11 = $"{i + 1}_{j + 1}";

                    if (gridData.ContainsKey(k00) && gridData.ContainsKey(k10) &&
                        gridData.ContainsKey(k01) && gridData.ContainsKey(k11))
                    {
                        mesh.Faces.AddFace(
                            gridData[k00].vertIdx,
                            gridData[k10].vertIdx,
                            gridData[k11].vertIdx,
                            gridData[k01].vertIdx);
                    }
                }
            }

            // 按顶点顺序着色
            mesh.VertexColors.Clear();
            if (mesh.Vertices.Count > 0)
            {
                var colorMap = new Dictionary<int, Color>();
                foreach (var kv in gridData)
                {
                    double t = (kv.Value.value - minVal) / valRange;
                    colorMap[kv.Value.vertIdx] = InterpolateColor(colorLow, colorHigh, t);
                }
                for (int vi = 0; vi < mesh.Vertices.Count; vi++)
                {
                    if (colorMap.TryGetValue(vi, out Color c))
                        mesh.VertexColors.SetColor(vi, c);
                    else
                        mesh.VertexColors.SetColor(vi, Color.Gray);
                }
            }

            mesh.Normals.ComputeNormals();
            return mesh;
        }

        /// <summary>
        /// 估算点云的平均网格间距（基于 2D 面积密度）
        /// 对于 LBM 点云，点数 = nx × ny，面积 = nx×dy × ny×dy
        /// 所以间距 ≈ sqrt(面积 / 点数)
        /// </summary>
        private double EstimateGridSpacing(List<Point3d> points)
        {
            if (points.Count < 2) return 1.0;
            BoundingBox bbox = new BoundingBox(points);
            // 用最大二维投影面积估算
            double dx = bbox.Max.X - bbox.Min.X;
            double dy = bbox.Max.Y - bbox.Min.Y;
            double dz = bbox.Max.Z - bbox.Min.Z;

            // 取最大的两个维度面积
            double area = Math.Max(dx * dy, Math.Max(dx * dz, dy * dz));
            if (area < 1e-10) area = dx + dy + dz; // 退化情况
            double spacing = Math.Sqrt(area / points.Count);
            return Math.Max(0.1, spacing);
        }

        /// <summary>
        /// 获取平面方向的文本描述
        /// </summary>
        private string GetPlaneDescription(Plane plane)
        {
            Vector3d normal = plane.Normal;
            normal.Unitize();

            // 检查接近标准平面
            if (Math.Abs(normal.Z - 1.0) < 0.01)
                return "水平面 (Z=恒定)";
            if (Math.Abs(normal.Z + 1.0) < 0.01)
                return "水平面 (Z=恒定, 反向)";
            if (Math.Abs(normal.X - 1.0) < 0.01)
                return "垂直面 (X=恒定)";
            if (Math.Abs(normal.X + 1.0) < 0.01)
                return "垂直面 (X=恒定, 反向)";
            if (Math.Abs(normal.Y - 1.0) < 0.01)
                return "垂直面 (Y=恒定)";
            if (Math.Abs(normal.Y + 1.0) < 0.01)
                return "垂直面 (Y=恒定, 反向)";

            return $"倾斜面 (法线 N={normal.X:F2}, {normal.Y:F2}, {normal.Z:F2})";
        }

        private Color InterpolateColor(Color c1, Color c2, double t)
        {
            t = Math.Max(0, Math.Min(1, t));
            int r = (int)(c1.R + t * (c2.R - c1.R));
            int g = (int)(c1.G + t * (c2.G - c1.G));
            int b = (int)(c1.B + t * (c2.B - c1.B));
            return Color.FromArgb(255,
                Math.Max(0, Math.Min(255, r)),
                Math.Max(0, Math.Min(255, g)),
                Math.Max(0, Math.Min(255, b)));
        }

        protected override Bitmap Icon
        {
            get { return null; }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("C5D9E1F4-A0B6-4C7D-9E8F-1A2B3C4D5E6F"); }
        }
    }
}
