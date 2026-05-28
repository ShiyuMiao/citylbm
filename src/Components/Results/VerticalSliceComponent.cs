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
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 竖直切面可视化组件（索引模式）
    /// 通过整数序号选择截面，自动推算物理坐标位置。
    /// 默认 XZ 竖直切面，可选 XY/YZ 平面。
    /// 支持结构化网格：自动检测行列关系，构建精确四边面。
    /// </summary>
    public class VerticalSliceComponent : GH_Component
    {
        public enum SliceOrientation
        {
            XZ_Plane = 0,  // 竖直切面（沿 Y 轴截取）
            XY_Plane = 1,  // 水平切面（沿 Z 轴截取）
            YZ_Plane = 2   // 竖直切面（沿 X 轴截取）
        }

        public VerticalSliceComponent()
            : base("Vertical Slice", "VSlice",
                   "竖直/水平切面（输入序号选择截面，0=底部）",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt", "网格点坐标（来自 Read VTK）", GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V", "速度向量（来自 Read VTK）", GH_ParamAccess.list);
            pManager.AddIntegerParameter("Slice Index", "Idx",
                "截面序号（从 0 开始，0=底部/前端/左侧）。\n" +
                "留空自动选中间截面。",
                GH_ParamAccess.item, -1);
            pManager[2].Optional = true;
            pManager.AddIntegerParameter("Orientation", "O",
                "切面方向：\n" +
                "  0 = XZ 竖直切面（默认，沿 Y 轴截取）\n" +
                "  1 = XY 水平切面（沿 Z 轴截取）\n" +
                "  2 = YZ 竖直切面（沿 X 轴截取）",
                GH_ParamAccess.item, 0);
            pManager.AddNumberParameter("Grid Spacing", "GS",
                "网格间距（来自 Read VTK 的 GS 输出）。\n" +
                "留空时自动从点云估算。",
                GH_ParamAccess.item, 0.0);
            pManager[4].Optional = true;
            pManager.AddNumberParameter("Tolerance", "T",
                "切片厚度容差（m）。留空自动。",
                GH_ParamAccess.item, 0.0);
            pManager[5].Optional = true;
            pManager.AddColourParameter("Color Low", "CL", "低速颜色", GH_ParamAccess.item, Color.Blue);
            pManager.AddColourParameter("Color High", "CH", "高速颜色", GH_ParamAccess.item, Color.Red);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Slice List", "L",
                "所有可用截面列表（序号: 物理坐标），用于选择 Idx",
                GH_ParamAccess.list);
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
            int sliceIndex = -1;
            int orientationInt = 0;
            double gridSpacing = 0.0;
            double tolerance = 0.0;
            Color colorLow = Color.Blue;
            Color colorHigh = Color.Red;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetData(2, ref sliceIndex);
            DA.GetData(3, ref orientationInt);
            DA.GetData(4, ref gridSpacing);
            DA.GetData(5, ref tolerance);
            DA.GetData(6, ref colorLow);
            DA.GetData(7, ref colorHigh);

            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据");
                DA.SetDataList(0, new List<string>());
                return;
            }

            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数和速度数不匹配");
                return;
            }

            // 解析切面方向
            SliceOrientation orientation;
            if (orientationInt >= 0 && orientationInt <= 2)
                orientation = (SliceOrientation)orientationInt;
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "不支持的切面方向，使用默认 XZ 平面");
                orientation = SliceOrientation.XZ_Plane;
            }

            // ── 核心改进：从实际点云提取截面层坐标（不再依赖 VTK 原始间距）──
            // ReadVTK 可能做了 Subsample 采样（step > 1），导致实际点间距 > VTK 原始间距。
            // 如果用 VTK 原始 GS 推算截面坐标，会算出实际不存在的截面位置。
            // 因此直接从点云中提取唯一坐标值来确定截面列表。

            BoundingBox bbox = new BoundingBox(points);
            string axisName;

            // 1) 收集切片轴方向的坐标值
            var axisCoords = new List<double>(points.Count);
            switch (orientation)
            {
                case SliceOrientation.XZ_Plane:
                    axisName = "Y";
                    foreach (var pt in points) axisCoords.Add(pt.Y);
                    break;
                case SliceOrientation.XY_Plane:
                    axisName = "Z";
                    foreach (var pt in points) axisCoords.Add(pt.Z);
                    break;
                case SliceOrientation.YZ_Plane:
                    axisName = "X";
                    foreach (var pt in points) axisCoords.Add(pt.X);
                    break;
                default:
                    axisName = "Y";
                    foreach (var pt in points) axisCoords.Add(pt.Y);
                    break;
            }

            // 2) 聚类为唯一层级（使用 VTK 原始间距作为聚类容差，如果有的话）
            double clusterTol;
            if (gridSpacing > 0)
                clusterTol = gridSpacing * 0.4; // 精确匹配
            else
                clusterTol = EstimateGridSpacing(points) * 0.4;

            var uniqueCoords = ClusterCoords(axisCoords.ToArray(), clusterTol);
            int layerCount = uniqueCoords.Count;

            // 3) 自动估算实际采样间距（用于容差和网格面构建）
            double actualSpacing = EstimateGridSpacing(points);
            if (layerCount > 1)
            {
                // 用相邻截面间距的平均值
                double sumGap = 0;
                for (int i = 1; i < layerCount; i++)
                    sumGap += uniqueCoords[i] - uniqueCoords[i - 1];
                actualSpacing = sumGap / (layerCount - 1);
            }
            actualSpacing = Math.Max(0.1, actualSpacing);

            // 自动容差（基于实际采样间距，而非 VTK 原始间距）
            if (tolerance <= 0)
                tolerance = actualSpacing * 0.5;

            // 4) 生成截面列表：序号 → 物理坐标
            var sliceList = new List<string>();
            for (int i = 0; i < layerCount; i++)
            {
                sliceList.Add($"[{i}] {axisName} = {uniqueCoords[i]:F2} m");
            }

            // 序号自动选中间
            int actualIndex;
            if (sliceIndex < 0 || sliceIndex >= layerCount)
            {
                actualIndex = layerCount / 2;
                if (sliceIndex < 0)
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                        $"未指定截面序号，自动选择中间截面 [{actualIndex}]");
                else
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                        $"截面序号 {sliceIndex} 超出范围 [0, {layerCount - 1}]，自动使用 [{actualIndex}]");
            }
            else
            {
                actualIndex = sliceIndex;
            }

            // 5) 计算截面物理坐标（直接用实际存在的坐标）
            double sliceCoord = uniqueCoords[actualIndex];
            double minCoord = uniqueCoords[0];
            double maxCoord = uniqueCoords[layerCount - 1];

            // 构建切片平面
            Plane slicePlane;
            string posDescription;
            switch (orientation)
            {
                case SliceOrientation.XZ_Plane:
                    slicePlane = new Plane(new Point3d(0, sliceCoord, 0), Vector3d.YAxis);
                    posDescription = $"Y = {sliceCoord:F2} m (#{actualIndex}/{layerCount - 1})";
                    break;
                case SliceOrientation.XY_Plane:
                    slicePlane = new Plane(new Point3d(0, 0, sliceCoord), Vector3d.ZAxis);
                    posDescription = $"Z = {sliceCoord:F2} m (#{actualIndex}/{layerCount - 1})";
                    break;
                case SliceOrientation.YZ_Plane:
                    slicePlane = new Plane(new Point3d(sliceCoord, 0, 0), Vector3d.XAxis);
                    posDescription = $"X = {sliceCoord:F2} m (#{actualIndex}/{layerCount - 1})";
                    break;
                default:
                    slicePlane = new Plane(new Point3d(0, sliceCoord, 0), Vector3d.YAxis);
                    posDescription = $"自动 (#{actualIndex})";
                    break;
            }

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

            // 输出截面列表（总是输出）
            DA.SetDataList(0, sliceList);

            if (slicePoints.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    $"截面 [{actualIndex}] {posDescription} 上没有找到点（容差 {tolerance:F3} m）。" +
                    "尝试增大 Tolerance 或更换截面序号。");
                DA.SetDataList(1, slicePoints);
                DA.SetDataList(2, sliceVelocities);
                DA.SetDataList(3, magnitudes);
                DA.SetData(4, new Mesh());
                DA.SetData(5, 0.0);
                DA.SetData(6, 0.0);
                DA.SetData(7, "无切片数据");
                return;
            }

            // 计算值范围
            double minVal = magnitudes.Min();
            double maxVal = magnitudes.Max();

            // 创建切片网格 —— 结构化网格感知
            Mesh sliceMesh = CreateStructuredSliceMesh(slicePoints, magnitudes, gridSpacing, slicePlane,
                minVal, maxVal, colorLow, colorHigh);

            // 切面方向描述
            string orientDesc;
            switch (orientation)
            {
                case SliceOrientation.XZ_Plane:
                    orientDesc = "XZ 竖直切面 (Y=恒定)"; break;
                case SliceOrientation.XY_Plane:
                    orientDesc = "XY 水平切面 (Z=恒定)"; break;
                case SliceOrientation.YZ_Plane:
                    orientDesc = "YZ 竖直切面 (X=恒定)"; break;
                default:
                    orientDesc = "未知"; break;
            }

            // 构建 Info
            string info = $"══════════════════════════════\n" +
                          $"  竖直/水平切面信息\n" +
                          $"══════════════════════════════\n" +
                          $"  切面方向:   {orientDesc}\n" +
                          $"  截面序号:   [{actualIndex}] / {layerCount - 1}\n" +
                          $"  物理位置:   {posDescription}\n" +
                          $"  网格间距:   {gridSpacing:F3} m\n" +
                          $"  截面总数:   {layerCount}\n" +
                          $"  切片点数:   {slicePoints.Count:N0}\n" +
                          $"  网格面数:   {sliceMesh.Faces.Count:N0}\n" +
                          $"  速度范围:   {minVal:E3} ~ {maxVal:E3}\n" +
                          $"  坐标范围:   {minCoord:F2} ~ {maxCoord:F2} m\n" +
                          $"══════════════════════════════";

            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                $"切片提取完成：[{actualIndex}] {posDescription}，{slicePoints.Count:N0} 个点，" +
                $"{sliceMesh.Faces.Count:N0} 个面，速度 {minVal:E3} ~ {maxVal:E3}");

            DA.SetDataList(1, slicePoints);
            DA.SetDataList(2, sliceVelocities);
            DA.SetDataList(3, magnitudes);
            DA.SetData(4, sliceMesh);
            DA.SetData(5, minVal);
            DA.SetData(6, maxVal);
            DA.SetData(7, info);
        }

        /// <summary>
        /// 创建切片网格 —— 结构化网格感知版本
        /// 
        /// 核心思路：FluidX3D 的 VTK 是 STRUCTURED_POINTS，切片上的点构成规则二维网格。
        /// 检测两个平面坐标轴方向上的等间距层级，建立 (row, col) 索引，
        /// 然后直接按行-列连接四边面。不需要"投影网格化"。
        /// 
        /// 回退方案：如果检测不到结构化关系，退化为 Delaunay 三角化。
        /// </summary>
        private Mesh CreateStructuredSliceMesh(List<Point3d> points, List<double> values,
            double gridSpacing, Plane plane, double minVal, double maxVal,
            Color colorLow, Color colorHigh)
        {
            Mesh mesh = new Mesh();

            // 安全检查：确保输入数据有效且数量匹配
            if (points == null || values == null || points.Count == 0 || values.Count == 0)
                return mesh;

            if (points.Count != values.Count)
            {
                // 数据不匹配，记录警告并取最小数量
                int minCount = Math.Min(points.Count, values.Count);
                if (minCount == 0) return mesh;
                points = points.GetRange(0, minCount);
                values = values.GetRange(0, minCount);
            }

            double valRange = maxVal - minVal;
            if (valRange < 1e-10) valRange = 1.0;

            // 平面局部坐标系
            Vector3d axisU = plane.XAxis;
            Vector3d axisV = plane.YAxis;
            Point3d origin = plane.Origin;

            // 投影到平面 UV 坐标
            int n = points.Count;
            var uCoords = new double[n];
            var vCoords = new double[n];

            for (int i = 0; i < n; i++)
            {
                Vector3d delta = points[i] - origin;
                uCoords[i] = delta * axisU;
                vCoords[i] = delta * axisV;
            }

            // 收集唯一坐标值（按网格间距归类）
            double halfSpacing = gridSpacing * 0.4; // 容差
            var uniqueU = ClusterCoords(uCoords, halfSpacing);
            var uniqueV = ClusterCoords(vCoords, halfSpacing);

            int nu = uniqueU.Count;
            int nv = uniqueV.Count;

            // 如果检测到的网格太小或太大，回退到投影网格化
            if (nu < 2 || nv < 2 || nu * nv > n * 3)
            {
                // 回退方案：简单投影网格化
                return CreateFallbackMesh(points, values, gridSpacing, plane, minVal, maxVal, colorLow, colorHigh);
            }

            // 建立每个点的 (row, col) 索引
            // gridVerts[row, col] = 顶点在 mesh 中的索引（-1 表示缺失）
            int[,] gridVerts = new int[nv, nu];
            for (int r = 0; r < nv; r++)
                for (int c = 0; c < nu; c++)
                    gridVerts[r, c] = -1;

            for (int i = 0; i < n; i++)
            {
                int col = FindClosestIndex(uniqueU, uCoords[i], halfSpacing);
                int row = FindClosestIndex(uniqueV, vCoords[i], halfSpacing);

                if (col >= 0 && row >= 0 && gridVerts[row, col] < 0)
                {
                    gridVerts[row, col] = mesh.Vertices.Count;
                    mesh.Vertices.Add(
                        (float)points[i].X,
                        (float)points[i].Y,
                        (float)points[i].Z);
                }
            }

            // 连接四边面
            for (int r = 0; r < nv - 1; r++)
            {
                for (int c = 0; c < nu - 1; c++)
                {
                    int v00 = gridVerts[r, c];
                    int v10 = gridVerts[r, c + 1];
                    int v01 = gridVerts[r + 1, c];
                    int v11 = gridVerts[r + 1, c + 1];

                    // 只要有3个顶点就构建面（用三角形补缺）
                    if (v00 >= 0 && v10 >= 0 && v11 >= 0 && v01 >= 0)
                    {
                        // 完整四边面
                        mesh.Faces.AddFace(v00, v10, v11, v01);
                    }
                    else if (v00 >= 0 && v10 >= 0 && v11 >= 0)
                    {
                        mesh.Faces.AddFace(v00, v10, v11);
                    }
                    else if (v00 >= 0 && v01 >= 0 && v11 >= 0)
                    {
                        mesh.Faces.AddFace(v00, v11, v01);
                    }
                    else if (v10 >= 0 && v11 >= 0 && v01 >= 0)
                    {
                        mesh.Faces.AddFace(v10, v11, v01);
                    }
                    else if (v00 >= 0 && v10 >= 0 && v01 >= 0)
                    {
                        mesh.Faces.AddFace(v00, v10, v01);
                    }
                }
            }

            // 顶点着色
            mesh.VertexColors.Clear();
            for (int i = 0; i < mesh.Vertices.Count; i++)
            {
                mesh.VertexColors.SetColor(i, Color.Gray);
            }
            // 用原始点数据着色
            for (int i = 0; i < n; i++)
            {
                int col = FindClosestIndex(uniqueU, uCoords[i], halfSpacing);
                int row = FindClosestIndex(uniqueV, vCoords[i], halfSpacing);
                if (col >= 0 && row >= 0)
                {
                    int vi = gridVerts[row, col];
                    if (vi >= 0)
                    {
                        double t = (values[i] - minVal) / valRange;
                        mesh.VertexColors.SetColor(vi, InterpolateColor(colorLow, colorHigh, t));
                    }
                }
            }

            mesh.Normals.ComputeNormals();
            return mesh;
        }

        /// <summary>
        /// 将坐标值聚类为唯一层级（容差内视为同一层）
        /// </summary>
        private List<double> ClusterCoords(double[] coords, double tolerance)
        {
            var sorted = new List<double>(coords);
            sorted.Sort();

            var clusters = new List<double>();
            foreach (double c in sorted)
            {
                if (clusters.Count == 0 || Math.Abs(c - clusters[clusters.Count - 1]) > tolerance)
                {
                    clusters.Add(c);
                }
            }
            return clusters;
        }

        /// <summary>
        /// 在已排序的唯一值列表中找最近索引
        /// </summary>
        private int FindClosestIndex(List<double> uniqueValues, double value, double tolerance)
        {
            int best = -1;
            double bestDist = double.MaxValue;
            for (int i = 0; i < uniqueValues.Count; i++)
            {
                double d = Math.Abs(value - uniqueValues[i]);
                if (d < bestDist)
                {
                    bestDist = d;
                    best = i;
                }
            }
            if (bestDist > tolerance)
                return -1;
            return best;
        }

        /// <summary>
        /// 回退方案：基于网格间距的简单四边面连接
        /// 用于非结构化或检测不到规则网格的情况
        /// </summary>
        private Mesh CreateFallbackMesh(List<Point3d> points, List<double> values,
            double gridSpacing, Plane plane, double minVal, double maxVal,
            Color colorLow, Color colorHigh)
        {
            Mesh mesh = new Mesh();
            double valRange = maxVal - minVal;
            if (valRange < 1e-10) valRange = 1.0;

            Vector3d axisU = plane.XAxis;
            Vector3d axisV = plane.YAxis;
            Point3d origin = plane.Origin;

            // 投影到 UV 并网格化
            var uvCoords = new List<(int index, double u, double v, double value)>(points.Count);
            for (int i = 0; i < points.Count; i++)
            {
                Vector3d delta = points[i] - origin;
                double u = delta * axisU;
                double v = delta * axisV;
                uvCoords.Add((i, u, v, values[i]));
            }

            double minU = uvCoords.Min(c => c.u);
            double maxU = uvCoords.Max(c => c.u);
            double minV = uvCoords.Min(c => c.v);
            double maxV = uvCoords.Max(c => c.v);

            // 使用精确的网格间距（不再乘 1.2）
            double gridSize = Math.Max(0.01, gridSpacing);

            var gridData = new Dictionary<string, (int vertIdx, double value)>();

            for (int i = 0; i < uvCoords.Count; i++)
            {
                var c = uvCoords[i];
                int gu = (int)Math.Round((c.u - minU) / gridSize);
                int gv = (int)Math.Round((c.v - minV) / gridSize);
                string key = $"{gu}_{gv}";

                if (!gridData.ContainsKey(key))
                {
                    mesh.Vertices.Add((float)points[c.index].X,
                                      (float)points[c.index].Y,
                                      (float)points[c.index].Z);
                    gridData[key] = (mesh.Vertices.Count - 1, c.value);
                }
            }

            int nu = (int)Math.Round((maxU - minU) / gridSize) + 1;
            int nv = (int)Math.Round((maxV - minV) / gridSize) + 1;

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
        /// 估算点云的平均网格间距
        /// </summary>
        private double EstimateGridSpacing(List<Point3d> points)
        {
            if (points.Count < 2) return 1.0;
            BoundingBox bbox = new BoundingBox(points);
            double dx = bbox.Max.X - bbox.Min.X;
            double dy = bbox.Max.Y - bbox.Min.Y;
            double dz = bbox.Max.Z - bbox.Min.Z;

            double area = Math.Max(dx * dy, Math.Max(dx * dz, dy * dz));
            if (area < 1e-10) area = dx + dy + dz;
            double spacing = Math.Sqrt(area / points.Count);
            return Math.Max(0.1, spacing);
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
            get { return IconLoader.Load("VerticalSlice.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("D7E2F3A4-B1C5-4D8E-A9F0-2B3C4D5E6F7A"); }
        }
    }
}
