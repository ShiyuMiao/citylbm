using System;
using System.Drawing;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// VTK 云图可视化组件
    /// 直接以 VTK 文件为数据源，内部完成读取、采样、可视化的全流程
    /// 
    /// 模式：
    ///   0 = 水平切片（指定 Z 高度的云图切片，解决 Z 方向数据被压平的 bug）
    ///   1 = 多层切片（Z 方向自动等距生成多层水平切片）
    ///   2 = 等值线（Marching Squares）
    ///   3 = 流线
    /// </summary>
    public class VTKCloudVisualizationComponent : GH_Component
    {
        public VTKCloudVisualizationComponent()
            : base("VTK Cloud Map", "Cloud",
                   "直接读取 VTK 结果文件并可视化为彩色云图（速度/压力等）",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddTextParameter("VTK Path", "P",
                "VTK 文件路径或包含 VTK 文件的目录。\n" +
                "留空则自动搜索 %TEMP%\\CityLBM 下最新模拟的 output 目录。",
                GH_ParamAccess.item, "");

            pManager.AddIntegerParameter("Time Step", "T",
                "时间步筛选：\n" +
                "  -2 = 自动选最后一个时间步（默认，推荐）\n" +
                "  -1 = 读取全部 VTK 文件\n" +
                "  >=0 = 读取指定时间步",
                GH_ParamAccess.item, -2);

            pManager.AddNumberParameter("Subsample Spacing", "SS",
                "可视化采样间距（物理单位，默认 5 m）。\n" +
                "设为 0 或负数时不做采样。",
                GH_ParamAccess.item, 5.0);

            pManager.AddIntegerParameter("Mode", "M",
                "显示模式:\n" +
                "  0 = 水平切片（指定 Z 高度，显示该高度云图）\n" +
                "  1 = 多层切片（Z 方向自动等距生成多层水平切片）\n" +
                "  2 = 等值线（Marching Squares，指定 Z 高度）\n" +
                "  3 = 流线",
                GH_ParamAccess.item, 0);

            pManager.AddNumberParameter("Slice Z", "Z",
                "水平切片的 Z 高度（模式 0/2 使用）。\n" +
                "留空或设为 NaN 时自动取域中间高度。",
                GH_ParamAccess.item, double.NaN);

            pManager.AddIntegerParameter("Slice Count", "SC",
                "多层切片数量（仅模式 1），默认 5 层。",
                GH_ParamAccess.item, 5);

            pManager.AddNumberParameter("Grid Size", "G", "网格尺寸（用于切片和等值线模式，0=自动）", GH_ParamAccess.item, 0.0);
            pManager.AddIntegerParameter("Contour Count", "N", "等值线数量（仅模式 2）", GH_ParamAccess.item, 10);
            pManager.AddColourParameter("Color Low", "CL", "低值颜色", GH_ParamAccess.item, Color.Blue);
            pManager.AddColourParameter("Color High", "CH", "高值颜色", GH_ParamAccess.item, Color.Red);
            pManager.AddBooleanParameter("Use Gradient", "UG", "使用渐变色带（蓝->青->绿->黄->红）", GH_ParamAccess.item, true);

            pManager[0].Optional = true;
            pManager[1].Optional = true;
            pManager[2].Optional = true;
            pManager[4].Optional = true;
            pManager[5].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddMeshParameter("Mesh", "M", "可视化网格（内嵌顶点颜色）", GH_ParamAccess.item);
            pManager.AddCurveParameter("Contours", "Co", "等值线（仅等值线模式）", GH_ParamAccess.list);
            pManager.AddNumberParameter("Min Value", "Min", "最小值", GH_ParamAccess.item);
            pManager.AddNumberParameter("Max Value", "Max", "最大值", GH_ParamAccess.item);
            pManager.AddTextParameter("Legend", "L", "图例信息", GH_ParamAccess.item);
            pManager.AddTextParameter("Info", "I", "读取和采样信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string vtkPath = "";
            int timeStep = -2;
            double subsampleSpacing = 5.0;
            int mode = 0;
            double sliceZ = double.NaN;
            int sliceCount = 5;
            double gridSize = 0.0;
            int contourCount = 10;
            Color colorLow = Color.Blue;
            Color colorHigh = Color.Red;
            bool useGradient = true;

            DA.GetData(0, ref vtkPath);
            DA.GetData(1, ref timeStep);
            DA.GetData(2, ref subsampleSpacing);
            DA.GetData(3, ref mode);
            DA.GetData(4, ref sliceZ);
            DA.GetData(5, ref sliceCount);
            DA.GetData(6, ref gridSize);
            DA.GetData(7, ref contourCount);
            DA.GetData(8, ref colorLow);
            DA.GetData(9, ref colorHigh);
            DA.GetData(10, ref useGradient);

            // ── VTK Path 为空时自动搜索最新 Case 的 output 目录 ──
            if (string.IsNullOrEmpty(vtkPath))
            {
                vtkPath = FindLatestOutputDir();
                if (!string.IsNullOrEmpty(vtkPath))
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"自动找到输出目录: {vtkPath}");
            }

            if (string.IsNullOrEmpty(vtkPath))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "未找到 VTK 输出目录。\n" +
                    "请先运行模拟，或手动指定 VTK Path。");
                return;
            }

            // ── 收集 VTK 文件 ──
            List<string> vtkFiles = new List<string>();
            if (Directory.Exists(vtkPath))
            {
                string[] files = Directory.GetFiles(vtkPath, "*.vtk");
                Array.Sort(files);
                vtkFiles.AddRange(files);
            }
            else if (File.Exists(vtkPath))
            {
                vtkFiles.Add(vtkPath);
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, $"路径不存在: {vtkPath}");
                return;
            }

            if (vtkFiles.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "目录中未找到 .vtk 文件");
                return;
            }

            // ── 第一步：探测网格间距 ──
            double detectedSpacing = 0.0;
            try
            {
                VTKGridInfo gridInfo = ProbeGridSpacing(vtkFiles[0]);
                detectedSpacing = gridInfo.MinSpacing;
            }
            catch { }

            // ── 第二步：计算采样步长 ──
            int step;
            int maxStep = 1000;
            if (subsampleSpacing > 0 && detectedSpacing > 1e-10)
                step = Math.Min(Math.Max(1, (int)Math.Round(subsampleSpacing / detectedSpacing)), maxStep);
            else
                step = 1;

            // ── 第三步：处理 -2（自动选最后一个时间步）──
            if (timeStep == -2)
            {
                int latestStep = -1;
                string bestFile = null;
                foreach (string file in vtkFiles)
                {
                    try
                    {
                        int ts = ExtractTimeStepFromFilename(file);
                        if (ts > latestStep) { latestStep = ts; bestFile = file; }
                    }
                    catch { }
                }
                if (bestFile == null)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "无法从文件名中提取时间步");
                    return;
                }
                vtkFiles = new List<string> { bestFile };
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"自动选择最后时间步: T={latestStep}");
            }

            // ── 第四步：读取 VTK 文件 ──
            List<Point3d> allPoints = new List<Point3d>();
            List<Vector3d> allVelocities = new List<Vector3d>();
            int totalRawPoints = 0;

            foreach (string file in vtkFiles)
            {
                try
                {
                    var result = ParseVTKFile(file, step);
                    if (result.Points != null)
                    {
                        allPoints.AddRange(result.Points);
                        totalRawPoints += result.RawPointCount;
                    }
                    if (result.Velocities != null)
                        allVelocities.AddRange(result.Velocities);
                }
                catch (Exception ex)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                        $"读取文件失败: {Path.GetFileName(file)} - {ex.Message}");
                }
            }

            if (allPoints.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "未读到有效 VTK 数据");
                return;
            }

            // ── 第五步：确定标量场（速度大小）──
            List<double> values;
            string fieldName;

            if (allVelocities.Count > 0 && allVelocities.Count == allPoints.Count)
            {
                values = allVelocities.ConvertAll(v => v.Length);
                fieldName = "速度大小";
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "VTK 文件中未找到速度数据，无法生成云图");
                return;
            }

            // ── 第六步：计算值范围和域信息 ──
            double minVal = values.Min();
            double maxVal = values.Max();
            double range = maxVal - minVal;
            if (range < 1e-10) range = 1.0;

            BoundingBox domainBbox = new BoundingBox(allPoints);
            double domainMinZ = domainBbox.Min.Z;
            double domainMaxZ = domainBbox.Max.Z;
            double domainMidZ = (domainMinZ + domainMaxZ) / 2.0;

            // 自动网格尺寸
            if (gridSize <= 0)
                gridSize = EstimatePointSize(allPoints) * 1.2;
            if (gridSize < 0.1) gridSize = 1.0;

            // 如果 sliceZ 未指定，使用域中间高度
            if (double.IsNaN(sliceZ))
                sliceZ = domainMidZ;

            // ── 第七步：根据模式生成可视化 ──
            Mesh visualMesh = new Mesh();
            List<Color> colors = new List<Color>();
            List<Curve> contours = new List<Curve>();

            switch (mode)
            {
                case 0: // 水平切片（指定 Z 高度）
                    {
                        double zTol = gridSize * 0.5; // Z 方向容差
                        (visualMesh, colors) = CreateHorizontalSlice(
                            allPoints, values, sliceZ, zTol, gridSize,
                            minVal, maxVal, colorLow, colorHigh, useGradient);
                        AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                            $"水平切片 Z = {sliceZ:F2} m（域范围 {domainMinZ:F1} ~ {domainMaxZ:F1} m）");
                    }
                    break;

                case 1: // 多层切片
                    {
                        sliceCount = Math.Max(2, Math.Min(sliceCount, 50));
                        double zStep = (domainMaxZ - domainMinZ) / (sliceCount + 1);
                        double zTol = Math.Max(zStep * 0.4, gridSize * 0.5);

                        for (int s = 1; s <= sliceCount; s++)
                        {
                            double z = domainMinZ + s * zStep;
                            var (sliceMesh, sliceColors) = CreateHorizontalSlice(
                                allPoints, values, z, zTol, gridSize,
                                minVal, maxVal, colorLow, colorHigh, useGradient);
                            visualMesh.Append(sliceMesh);
                            colors.AddRange(sliceColors);
                        }
                        AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                            $"多层切片 {sliceCount} 层，Z 范围 {domainMinZ:F1} ~ {domainMaxZ:F1} m");
                    }
                    break;

                case 2: // 等值线（水平切片 + Marching Squares）
                    {
                        double zTol = gridSize * 0.5;
                        (visualMesh, colors, contours) = CreateContourVisualization(
                            allPoints, values, sliceZ, zTol, gridSize,
                            minVal, maxVal, contourCount, colorLow, colorHigh);
                        AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                            $"等值线切片 Z = {sliceZ:F2} m");
                    }
                    break;

                case 3: // 流线
                    (visualMesh, colors) = CreateStreamlineVisualization(allPoints, allVelocities, values,
                        minVal, maxVal, colorLow, colorHigh, useGradient);
                    break;

                default:
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, $"未知模式: {mode}");
                    break;
            }

            // 将颜色直接内嵌到 Mesh 顶点颜色中
            ApplyVertexColors(visualMesh, colors);

            // 生成图例
            string legend = GenerateLegend(fieldName, minVal, maxVal, colorLow, colorHigh, useGradient);

            // 生成 Info
            double samplingRate = totalRawPoints > 0 ? 100.0 * allPoints.Count / totalRawPoints : 100.0;
            string spacingStr = detectedSpacing > 0 ? $"{detectedSpacing:F3} m" : "未知";
            string stepDesc = subsampleSpacing > 0
                ? $"自动 Step={step}（{subsampleSpacing:F1} m / {spacingStr}）"
                : "不采样";

            string info =
                $"VTK 文件数: {vtkFiles.Count}\n" +
                $"原始点数:   {totalRawPoints:N0}\n" +
                $"采样后点数: {allPoints.Count:N0}  ({samplingRate:F1}%)\n" +
                $"网格间距:   {spacingStr}\n" +
                $"采样策略:   {stepDesc}\n" +
                $"Z 域范围:   {domainMinZ:F2} ~ {domainMaxZ:F2} m\n" +
                $"显示模式:   {GetModeName(mode)}\n" +
                $"{fieldName} 范围: {minVal:E4} ~ {maxVal:E4}";

            // ── 输出 ──
            DA.SetData(0, visualMesh);
            DA.SetDataList(1, contours);
            DA.SetData(2, minVal);
            DA.SetData(3, maxVal);
            DA.SetData(4, legend);
            DA.SetData(5, info);
        }

        // ══════════════════════════════════════════════════════════════
        // 核心：水平切片（指定 Z 高度，XY 平面网格化）
        // 只选取 |Z - sliceZ| < zTol 的点，确保切片在正确高度
        // ══════════════════════════════════════════════════════════════

        private (Mesh, List<Color>) CreateHorizontalSlice(
            List<Point3d> points, List<double> values,
            double sliceZ, double zTol, double gridSize,
            double minVal, double maxVal,
            Color colorLow, Color colorHigh, bool useGradient)
        {
            Mesh mesh = new Mesh();
            List<Color> colors = new List<Color>();

            if (points.Count == 0) return (mesh, colors);

            BoundingBox bbox = new BoundingBox(points);
            Point3d bmin = bbox.Min;
            Point3d bmax = bbox.Max;

            // 在 XY 平面网格化，同时要求 Z 在切片高度附近
            var gridCells = new Dictionary<string, (int index, double value)>();

            for (int i = 0; i < points.Count; i++)
            {
                Point3d pt = points[i];

                // 只取 Z 在切片高度 ± zTol 范围内的点
                if (Math.Abs(pt.Z - sliceZ) > zTol)
                    continue;

                int gx = (int)Math.Floor((pt.X - bmin.X) / gridSize);
                int gy = (int)Math.Floor((pt.Y - bmin.Y) / gridSize);
                string key = $"{gx}_{gy}";

                if (!gridCells.ContainsKey(key))
                {
                    // 顶点放在实际的切片高度，而非原始点 Z
                    mesh.Vertices.Add((float)pt.X, (float)pt.Y, (float)sliceZ);
                    gridCells[key] = (mesh.Vertices.Count - 1, values[i]);
                }
            }

            if (gridCells.Count == 0)
                return (mesh, colors);

            // 创建网格面
            int nx = (int)Math.Ceiling((bmax.X - bmin.X) / gridSize);
            int ny = (int)Math.Ceiling((bmax.Y - bmin.Y) / gridSize);

            for (int i = 0; i < nx - 1; i++)
            {
                for (int j = 0; j < ny - 1; j++)
                {
                    string k00 = $"{i}_{j}";
                    string k10 = $"{i + 1}_{j}";
                    string k01 = $"{i}_{j + 1}";
                    string k11 = $"{i + 1}_{j + 1}";

                    bool has00 = gridCells.ContainsKey(k00);
                    bool has10 = gridCells.ContainsKey(k10);
                    bool has01 = gridCells.ContainsKey(k01);
                    bool has11 = gridCells.ContainsKey(k11);

                    if (has00 && has10 && has01 && has11)
                    {
                        int a = gridCells[k00].index;
                        int b = gridCells[k10].index;
                        int c = gridCells[k11].index;
                        int d = gridCells[k01].index;
                        mesh.Faces.AddFace(a, b, c);
                        mesh.Faces.AddFace(a, c, d);
                    }
                    else
                    {
                        if (has00 && has10 && has01)
                            mesh.Faces.AddFace(gridCells[k00].index, gridCells[k10].index, gridCells[k01].index);
                        else if (has00 && has10 && has11)
                            mesh.Faces.AddFace(gridCells[k00].index, gridCells[k10].index, gridCells[k11].index);
                        else if (has00 && has01 && has11)
                            mesh.Faces.AddFace(gridCells[k00].index, gridCells[k01].index, gridCells[k11].index);
                        else if (has10 && has01 && has11)
                            mesh.Faces.AddFace(gridCells[k10].index, gridCells[k01].index, gridCells[k11].index);
                    }
                }
            }

            // 按顶点顺序着色
            var colorMap = new Dictionary<int, Color>();
            foreach (var kv in gridCells)
            {
                double t = (kv.Value.value - minVal) / (maxVal - minVal);
                colorMap[kv.Value.index] = InterpolateColor(colorLow, colorHigh, t, useGradient);
            }
            for (int vi = 0; vi < mesh.Vertices.Count; vi++)
            {
                colors.Add(colorMap.TryGetValue(vi, out Color c) ? c : Color.Gray);
            }

            mesh.Normals.ComputeNormals();
            return (mesh, colors);
        }

        // ══════════════════════════════════════════════════════════════
        // 模式 2: 等值线（水平切片 + Marching Squares）
        // ══════════════════════════════════════════════════════════════

        private (Mesh, List<Color>, List<Curve>) CreateContourVisualization(
            List<Point3d> points, List<double> values,
            double sliceZ, double zTol, double gridSize,
            double minVal, double maxVal, int contourCount,
            Color colorLow, Color colorHigh)
        {
            Mesh mesh = new Mesh();
            List<Color> colors = new List<Color>();
            List<Curve> contours = new List<Curve>();

            if (points.Count < 4) return (mesh, colors, contours);

            // 先筛选出 Z 在切片高度附近的点
            var slicePoints = new List<Point3d>();
            var sliceValues = new List<double>();
            for (int i = 0; i < points.Count; i++)
            {
                if (Math.Abs(points[i].Z - sliceZ) <= zTol)
                {
                    slicePoints.Add(points[i]);
                    sliceValues.Add(values[i]);
                }
            }

            if (slicePoints.Count < 4) return (mesh, colors, contours);

            BoundingBox bbox = new BoundingBox(slicePoints);
            Point3d min = bbox.Min;
            Point3d max = bbox.Max;

            int nx = (int)Math.Ceiling((max.X - min.X) / gridSize);
            int ny = (int)Math.Ceiling((max.Y - min.Y) / gridSize);
            if (nx < 2 || ny < 2) return (mesh, colors, contours);

            double[,] gridVal = new double[nx + 1, ny + 1];
            int[,] gridCount = new int[nx + 1, ny + 1];
            bool[,] gridValid = new bool[nx + 1, ny + 1];

            for (int i = 0; i < slicePoints.Count; i++)
            {
                Point3d pt = slicePoints[i];
                int gx = Math.Max(0, Math.Min(nx, (int)Math.Round((pt.X - min.X) / gridSize)));
                int gy = Math.Max(0, Math.Min(ny, (int)Math.Round((pt.Y - min.Y) / gridSize)));

                gridVal[gx, gy] += sliceValues[i];
                gridCount[gx, gy]++;
                gridValid[gx, gy] = true;
            }

            for (int i = 0; i <= nx; i++)
                for (int j = 0; j <= ny; j++)
                    if (gridCount[i, j] > 0)
                        gridVal[i, j] /= gridCount[i, j];

            // 创建底色网格 Mesh（顶点放在切片高度）
            var vertMap = new Dictionary<string, int>();
            for (int i = 0; i <= nx; i++)
            {
                for (int j = 0; j <= ny; j++)
                {
                    if (gridValid[i, j])
                    {
                        string key = $"{i}_{j}";
                        double x = min.X + i * gridSize;
                        double y = min.Y + j * gridSize;
                        mesh.Vertices.Add((float)x, (float)y, (float)sliceZ);
                        vertMap[key] = mesh.Vertices.Count - 1;

                        double t = (gridVal[i, j] - minVal) / (maxVal - minVal);
                        colors.Add(InterpolateColor(colorLow, colorHigh, t, true));
                    }
                }
            }

            for (int i = 0; i < nx; i++)
            {
                for (int j = 0; j < ny; j++)
                {
                    string k00 = $"{i}_{j}";
                    string k10 = $"{i + 1}_{j}";
                    string k01 = $"{i}_{j + 1}";
                    string k11 = $"{i + 1}_{j + 1}";

                    if (vertMap.ContainsKey(k00) && vertMap.ContainsKey(k10) &&
                        vertMap.ContainsKey(k01) && vertMap.ContainsKey(k11))
                    {
                        mesh.Faces.AddFace(vertMap[k00], vertMap[k10], vertMap[k11], vertMap[k01]);
                    }
                }
            }

            mesh.Normals.ComputeNormals();

            // Marching Squares 等值线（所有等值线在切片高度 Z = sliceZ）
            double stepVal = (maxVal - minVal) / (contourCount + 1);
            for (int c = 1; c <= contourCount; c++)
            {
                double level = minVal + c * stepVal;
                List<Polyline> levelLines = MarchingSquares(gridVal, gridValid,
                    nx, ny, gridSize, min, sliceZ, level);
                foreach (var polyline in levelLines)
                    contours.Add(polyline.ToNurbsCurve());
            }

            return (mesh, colors, contours);
        }

        private List<Polyline> MarchingSquares(
            double[,] gridVal, bool[,] gridValid,
            int nx, int ny, double gridSize, Point3d gridMin, double sliceZ, double level)
        {
            var segments = new List<(Point3d p1, Point3d p2)>();

            for (int i = 0; i < nx; i++)
            {
                for (int j = 0; j < ny; j++)
                {
                    if (!gridValid[i, j] || !gridValid[i + 1, j] || !gridValid[i, j + 1] || !gridValid[i + 1, j + 1])
                        continue;

                    double val00 = gridVal[i, j];
                    double val10 = gridVal[i + 1, j];
                    double val01 = gridVal[i, j + 1];
                    double val11 = gridVal[i + 1, j + 1];

                    int msCase = 0;
                    if (val00 >= level) msCase |= 1;
                    if (val10 >= level) msCase |= 2;
                    if (val11 >= level) msCase |= 4;
                    if (val01 >= level) msCase |= 8;

                    if (msCase == 0 || msCase == 15) continue;

                    // 所有顶点 Z 坐标固定为 sliceZ
                    Point3d p00 = new Point3d(gridMin.X + i * gridSize, gridMin.Y + j * gridSize, sliceZ);
                    Point3d p10 = new Point3d(gridMin.X + (i + 1) * gridSize, gridMin.Y + j * gridSize, sliceZ);
                    Point3d p01 = new Point3d(gridMin.X + i * gridSize, gridMin.Y + (j + 1) * gridSize, sliceZ);
                    Point3d p11 = new Point3d(gridMin.X + (i + 1) * gridSize, gridMin.Y + (j + 1) * gridSize, sliceZ);

                    Point3d? eBottom = LerpEdge(p00, p10, val00, val10, level);
                    Point3d? eRight = LerpEdge(p10, p11, val10, val11, level);
                    Point3d? eTop = LerpEdge(p11, p01, val11, val01, level);
                    Point3d? eLeft = LerpEdge(p01, p00, val01, val00, level);

                    switch (msCase)
                    {
                        case 1: case 14:
                            if (eBottom.HasValue && eLeft.HasValue) segments.Add((eBottom.Value, eLeft.Value));
                            break;
                        case 2: case 13:
                            if (eBottom.HasValue && eRight.HasValue) segments.Add((eBottom.Value, eRight.Value));
                            break;
                        case 3: case 12:
                            if (eLeft.HasValue && eRight.HasValue) segments.Add((eLeft.Value, eRight.Value));
                            break;
                        case 4: case 11:
                            if (eRight.HasValue && eTop.HasValue) segments.Add((eRight.Value, eTop.Value));
                            break;
                        case 5:
                            if (eBottom.HasValue && eRight.HasValue) segments.Add((eBottom.Value, eRight.Value));
                            if (eTop.HasValue && eLeft.HasValue) segments.Add((eTop.Value, eLeft.Value));
                            break;
                        case 6: case 9:
                            if (eBottom.HasValue && eTop.HasValue) segments.Add((eBottom.Value, eTop.Value));
                            break;
                        case 7: case 8:
                            if (eTop.HasValue && eLeft.HasValue) segments.Add((eTop.Value, eLeft.Value));
                            break;
                        case 10:
                            if (eBottom.HasValue && eLeft.HasValue) segments.Add((eBottom.Value, eLeft.Value));
                            if (eRight.HasValue && eTop.HasValue) segments.Add((eRight.Value, eTop.Value));
                            break;
                    }
                }
            }

            return ConnectSegments(segments);
        }

        private Point3d? LerpEdge(Point3d p1, Point3d p2, double val1, double val2, double level)
        {
            if ((val1 < level && val2 >= level) || (val2 < level && val1 >= level))
            {
                double t = (level - val1) / (val2 - val1);
                t = Math.Max(0, Math.Min(1, t));
                return new Point3d(
                    p1.X + t * (p2.X - p1.X),
                    p1.Y + t * (p2.Y - p1.Y),
                    p1.Z + t * (p2.Z - p1.Z));
            }
            return null;
        }

        private List<Polyline> ConnectSegments(List<(Point3d p1, Point3d p2)> segments)
        {
            var polylines = new List<Polyline>();
            if (segments.Count == 0) return polylines;

            var used = new bool[segments.Count];
            double tol = 0.001;

            for (int start = 0; start < segments.Count; start++)
            {
                if (used[start]) continue;

                var chain = new List<Point3d>();
                chain.Add(segments[start].p1);
                chain.Add(segments[start].p2);
                used[start] = true;

                bool extended = true;
                while (extended)
                {
                    extended = false;
                    Point3d endPt = chain[chain.Count - 1];
                    for (int k = 0; k < segments.Count; k++)
                    {
                        if (used[k]) continue;
                        if (endPt.DistanceTo(segments[k].p1) < tol)
                        {
                            chain.Add(segments[k].p2); used[k] = true; extended = true; break;
                        }
                        if (endPt.DistanceTo(segments[k].p2) < tol)
                        {
                            chain.Add(segments[k].p1); used[k] = true; extended = true; break;
                        }
                    }
                }

                extended = true;
                while (extended)
                {
                    extended = false;
                    Point3d startPt = chain[0];
                    for (int k = 0; k < segments.Count; k++)
                    {
                        if (used[k]) continue;
                        if (startPt.DistanceTo(segments[k].p1) < tol)
                        {
                            chain.Insert(0, segments[k].p2); used[k] = true; extended = true; break;
                        }
                        if (startPt.DistanceTo(segments[k].p2) < tol)
                        {
                            chain.Insert(0, segments[k].p1); used[k] = true; extended = true; break;
                        }
                    }
                }

                if (chain.Count >= 2)
                    polylines.Add(new Polyline(chain));
            }

            return polylines;
        }

        // ══════════════════════════════════════════════════════════════
        // 模式 3: 流线
        // ══════════════════════════════════════════════════════════════

        private (Mesh, List<Color>) CreateStreamlineVisualization(
            List<Point3d> points, List<Vector3d> velocities, List<double> values,
            double minVal, double maxVal, Color colorLow, Color colorHigh, bool useGradient)
        {
            Mesh mesh = new Mesh();
            List<Color> colors = new List<Color>();

            if (velocities.Count == 0 || velocities.Count != points.Count)
                return (mesh, colors);

            int maxStreamlinePoints = 10000;
            if (points.Count > maxStreamlinePoints)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                    $"流线模式仅支持 {maxStreamlinePoints} 个点以下，当前 {points.Count:N0} 个点。\n" +
                    "请增大 Subsample Spacing。");
                return (mesh, colors);
            }

            int seedSkip = Math.Max(1, points.Count / 200);
            int maxSteps = 50;
            double stepSize = EstimatePointSize(points) * 2;

            for (int seed = 0; seed < points.Count; seed += seedSkip)
            {
                Point3d currentPt = points[seed];
                Vector3d currentVel = velocities[seed];

                if (currentVel.IsZero || !currentVel.IsValid) continue;

                List<Point3d> streamlinePoints = new List<Point3d> { currentPt };

                for (int s = 0; s < maxSteps; s++)
                {
                    int nearestIdx = FindNearestPoint(currentPt, points);
                    Vector3d vel = velocities[nearestIdx];

                    if (vel.IsZero || !vel.IsValid) break;

                    vel.Unitize();
                    Point3d nextPt = currentPt + vel * stepSize;

                    if (!IsPointInDomain(nextPt, points)) break;

                    streamlinePoints.Add(nextPt);
                    currentPt = nextPt;
                }

                if (streamlinePoints.Count > 2)
                {
                    double val = values[seed];
                    double t = (val - minVal) / (maxVal - minVal);
                    Color color = InterpolateColor(colorLow, colorHigh, t, useGradient);

                    Mesh pipeMesh = CreatePolylinePipe(streamlinePoints, stepSize * 0.2);
                    mesh.Append(pipeMesh);
                    for (int i = 0; i < pipeMesh.Vertices.Count; i++)
                        colors.Add(color);
                }
            }

            mesh.Normals.ComputeNormals();
            return (mesh, colors);
        }

        // ══════════════════════════════════════════════════════════════
        // VTK 解析（与 ReadVTKComponent 共享逻辑，独立实现以避免耦合）
        // ══════════════════════════════════════════════════════════════

        private struct VTKGridInfo
        {
            public double MinSpacing;
        }

        private VTKGridInfo ProbeGridSpacing(string vtkPath)
        {
            VTKGridInfo info = new VTKGridInfo();

            byte[] buf = new byte[2048];
            int n;
            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
                n = fs.Read(buf, 0, buf.Length);

            string header = System.Text.Encoding.ASCII.GetString(buf, 0, n);
            string[] lines = header.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

            foreach (string line in lines)
            {
                string t = line.Trim();
                if (t.StartsWith("SPACING"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        float sp = 0;
                        for (int i = 1; i <= 3; i++)
                        {
                            float v;
                            if (float.TryParse(p[i], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out v) && v > 1e-10)
                            {
                                if (sp == 0 || v < sp) sp = v;
                            }
                        }
                        info.MinSpacing = sp;
                    }
                }
            }

            return info;
        }

        private class VTKResultData
        {
            public List<Point3d> Points = new List<Point3d>();
            public List<Vector3d> Velocities = new List<Vector3d>();
            public int RawPointCount = 0;
        }

        private VTKResultData ParseVTKFile(string vtkPath, int step)
        {
            var result = new VTKResultData();

            bool isBinary = false;
            using (StreamReader sr = new StreamReader(vtkPath))
            {
                string line;
                while ((line = sr.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (line == "BINARY") { isBinary = true; break; }
                    if (line == "ASCII") { isBinary = false; break; }
                }
            }

            if (isBinary)
                ParseBinaryVTK(vtkPath, result, step);
            else
                ParseASCIIVTK(vtkPath, result, step);

            return result;
        }

        private void ParseASCIIVTK(string vtkPath, VTKResultData result, int step)
        {
            using (StreamReader reader = new StreamReader(vtkPath))
            {
                string line;
                bool readingPoints = false;
                bool readingVelocities = false;
                bool readingScalars = false;
                bool skipLookupTable = false;
                int expectedPointCount = 0;
                int rawIdx = 0;

                int[] dims = null;
                float[] org = null;
                float[] spc = null;

                while ((line = reader.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (string.IsNullOrEmpty(line)) continue;
                    if (line.StartsWith("#") || line == "ASCII") continue;

                    if (line.StartsWith("DATASET"))
                    {
                        if (line.Contains("STRUCTURED_POINTS"))
                        {
                            dims = new int[3]; org = new float[3]; spc = new float[3];
                        }
                        continue;
                    }

                    if (dims != null)
                    {
                        if (line.StartsWith("DIMENSIONS"))
                        {
                            string[] p = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 4)
                            {
                                int.TryParse(p[1], out dims[0]);
                                int.TryParse(p[2], out dims[1]);
                                int.TryParse(p[3], out dims[2]);
                                expectedPointCount = dims[0] * dims[1] * dims[2];
                            }
                            continue;
                        }
                        if (line.StartsWith("ORIGIN"))
                        {
                            string[] p = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 4)
                            {
                                float.TryParse(p[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out org[0]);
                                float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out org[1]);
                                float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out org[2]);
                            }
                            continue;
                        }
                        if (line.StartsWith("SPACING"))
                        {
                            string[] p = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 4)
                            {
                                float.TryParse(p[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spc[0]);
                                float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spc[1]);
                                float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spc[2]);
                            }
                            continue;
                        }
                    }

                    if (line.StartsWith("POINTS"))
                    {
                        string[] parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length >= 2) int.TryParse(parts[1], out expectedPointCount);
                        result.RawPointCount = expectedPointCount;
                        readingPoints = true; readingVelocities = false; readingScalars = false;
                        rawIdx = 0;
                        continue;
                    }

                    if (line.StartsWith("POINT_DATA"))
                    {
                        if (dims != null && result.Points.Count == 0 && expectedPointCount > 0)
                            GenerateStructuredPoints(result, dims, org, spc, step);
                        readingPoints = false;
                        continue;
                    }

                    if (line.StartsWith("VECTORS"))
                    {
                        readingVelocities = true; readingScalars = false; readingPoints = false;
                        rawIdx = 0;
                        continue;
                    }

                    if (line.StartsWith("SCALARS"))
                    {
                        readingScalars = true; readingVelocities = false; readingPoints = false;
                        skipLookupTable = false;
                        rawIdx = 0;
                        continue;
                    }

                    if (line.StartsWith("LOOKUP_TABLE")) { skipLookupTable = true; continue; }

                    if (line.StartsWith("CELL_DATA") || line.StartsWith("CELLS") || line.StartsWith("POLYGONS"))
                    {
                        readingPoints = readingVelocities = readingScalars = false;
                        continue;
                    }

                    if (readingPoints && rawIdx < expectedPointCount)
                    {
                        string[] c = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        if (c.Length >= 3 &&
                            double.TryParse(c[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double x) &&
                            double.TryParse(c[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double y) &&
                            double.TryParse(c[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double z))
                        {
                            if (rawIdx % step == 0)
                                result.Points.Add(new Point3d(x, y, z));
                            rawIdx++;
                        }
                        continue;
                    }

                    if (readingVelocities)
                    {
                        string[] c = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        if (c.Length >= 3 &&
                            double.TryParse(c[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double vx) &&
                            double.TryParse(c[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double vy) &&
                            double.TryParse(c[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double vz))
                        {
                            if (rawIdx % step == 0)
                                result.Velocities.Add(new Vector3d(vx, vy, vz));
                            rawIdx++;
                        }
                        continue;
                    }

                    if (readingScalars)
                    {
                        if (skipLookupTable && !double.TryParse(line, out _))
                        {
                            skipLookupTable = false;
                            continue;
                        }
                        rawIdx++;
                        continue;
                    }
                }

                if (dims != null && result.Points.Count == 0 && expectedPointCount > 0)
                    GenerateStructuredPoints(result, dims, org, spc, step);

                if (result.RawPointCount == 0)
                    result.RawPointCount = expectedPointCount;
            }
        }

        private List<int> GenerateStructuredPoints(VTKResultData result, int[] dims, float[] org, float[] spc, int step)
        {
            int nx = dims[0], ny = dims[1], nz = dims[2];
            result.RawPointCount = nx * ny * nz;

            var sampledIndices = new List<int>();
            for (int k = 0; k < nz; k += step)
                for (int j = 0; j < ny; j += step)
                    for (int i = 0; i < nx; i += step)
                    {
                        result.Points.Add(new Point3d(org[0] + i * spc[0], org[1] + j * spc[1], org[2] + k * spc[2]));
                        sampledIndices.Add(i + j * nx + k * nx * ny);
                    }

            return sampledIndices;
        }

        private void ParseBinaryVTK(string vtkPath, VTKResultData result, int step)
        {
            byte[] headerBuf = new byte[4096];
            int headerLen;
            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
                headerLen = fs.Read(headerBuf, 0, headerBuf.Length);

            int headerEndPos = FindBinaryHeaderEnd(headerBuf, headerLen);
            if (headerEndPos < 0)
                throw new Exception("无法找到 VTK 二进制头部结束位置");

            string header = System.Text.Encoding.ASCII.GetString(headerBuf, 0, headerEndPos);
            string[] lines = header.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

            int[] dimensions = new int[3];
            float[] origin = new float[3];
            float[] spacing = new float[3];
            int pointCount = 0;
            bool isStructured = false;
            string dataType = "float";

            var dataSections = new List<DataSection>();

            foreach (string rawLine in lines)
            {
                string t = rawLine.Trim();

                if (t.StartsWith("DIMENSIONS"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        int.TryParse(p[1], out dimensions[0]);
                        int.TryParse(p[2], out dimensions[1]);
                        int.TryParse(p[3], out dimensions[2]);
                        pointCount = dimensions[0] * dimensions[1] * dimensions[2];
                        isStructured = true;
                    }
                }
                else if (t.StartsWith("ORIGIN"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        float.TryParse(p[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out origin[0]);
                        float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out origin[1]);
                        float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out origin[2]);
                    }
                }
                else if (t.StartsWith("SPACING"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        float.TryParse(p[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spacing[0]);
                        float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spacing[1]);
                        float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out spacing[2]);
                    }
                }
                else if (t.StartsWith("POINT_DATA"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 2) int.TryParse(p[1], out pointCount);
                }
                else if (t.StartsWith("VECTORS"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 3) dataType = p[2];
                    dataSections.Add(new DataSection
                    {
                        Type = "VECTORS",
                        Name = p.Length > 1 ? p[1] : "velocity",
                        DataType = dataType,
                        Components = 3
                    });
                }
                else if (t.StartsWith("SCALARS"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    int numComp = 1;
                    if (p.Length >= 4) int.TryParse(p[3], out numComp);
                    dataSections.Add(new DataSection
                    {
                        Type = "SCALARS",
                        Name = p.Length > 1 ? p[1] : "scalar",
                        DataType = p.Length > 2 ? p[2] : "float",
                        Components = numComp
                    });
                }
            }

            result.RawPointCount = pointCount;

            List<int> sampledIndices = null;
            if (isStructured && pointCount > 0)
                sampledIndices = GenerateStructuredPoints(result, dimensions, origin, spacing, step);

            if (dataSections.Count == 0) return;

            long filePos = headerEndPos;

            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
            {
                foreach (var section in dataSections)
                {
                    int bytesPerValue = section.DataType == "double" ? 8 : 4;
                    int bytesPerPoint = section.Components * bytesPerValue;
                    long sectionBytes = (long)pointCount * bytesPerPoint;

                    byte[] sectionData = new byte[sectionBytes];
                    fs.Seek(filePos, SeekOrigin.Begin);
                    int totalRead = 0;
                    while (totalRead < sectionBytes)
                    {
                        int got = fs.Read(sectionData, totalRead, (int)sectionBytes - totalRead);
                        if (got == 0) break;
                        totalRead += got;
                    }

                    if (totalRead < sectionBytes) { filePos += totalRead; continue; }

                    bool treatAsVector = (section.Type == "SCALARS" && section.Components == 3);
                    if (!treatAsVector && section.Type == "SCALARS")
                    {
                        string nameLower = (section.Name ?? "").ToLowerInvariant();
                        if (nameLower == "velocity" || nameLower == "u" || nameLower == "data")
                            treatAsVector = true;
                    }

                    if (section.Type == "VECTORS" || treatAsVector)
                    {
                        if (sampledIndices != null && result.Points.Count > 0)
                        {
                            result.Velocities = new List<Vector3d>(sampledIndices.Count);
                            foreach (int idx in sampledIndices)
                            {
                                int off = idx * bytesPerPoint;
                                if (off + bytesPerPoint <= sectionData.Length)
                                {
                                    double vx, vy, vz;
                                    if (section.DataType == "double")
                                    {
                                        vx = ReadBigEndianDouble(sectionData, off);
                                        vy = ReadBigEndianDouble(sectionData, off + 8);
                                        vz = ReadBigEndianDouble(sectionData, off + 16);
                                    }
                                    else
                                    {
                                        vx = ReadBigEndianFloat(sectionData, off);
                                        vy = ReadBigEndianFloat(sectionData, off + 4);
                                        vz = ReadBigEndianFloat(sectionData, off + 8);
                                    }
                                    result.Velocities.Add(new Vector3d(vx, vy, vz));
                                }
                            }
                        }
                        else
                        {
                            result.Velocities = new List<Vector3d>();
                            for (int rawIdx = 0; rawIdx < pointCount; rawIdx++)
                            {
                                if (rawIdx % step == 0)
                                {
                                    int off = rawIdx * bytesPerPoint;
                                    double vx, vy, vz;
                                    if (section.DataType == "double")
                                    {
                                        vx = ReadBigEndianDouble(sectionData, off);
                                        vy = ReadBigEndianDouble(sectionData, off + 8);
                                        vz = ReadBigEndianDouble(sectionData, off + 16);
                                    }
                                    else
                                    {
                                        vx = ReadBigEndianFloat(sectionData, off);
                                        vy = ReadBigEndianFloat(sectionData, off + 4);
                                        vz = ReadBigEndianFloat(sectionData, off + 8);
                                    }
                                    result.Velocities.Add(new Vector3d(vx, vy, vz));
                                }
                            }
                        }
                    }

                    filePos += sectionBytes;
                }
            }
        }

        private struct DataSection
        {
            public string Type;
            public string Name;
            public string DataType;
            public int Components;
        }

        private int FindBinaryHeaderEnd(byte[] bytes, int length)
        {
            int scanLen = Math.Min(length, 4096);
            int lastDataKeywordEnd = -1;

            for (int i = 0; i < scanLen; i++)
            {
                string candidate = System.Text.Encoding.ASCII.GetString(bytes, i, Math.Min(20, scanLen - i));
                if (candidate.StartsWith("VECTORS") || candidate.StartsWith("SCALARS") ||
                    candidate.StartsWith("LOOKUP_TABLE"))
                {
                    for (int j = i; j < scanLen; j++)
                    {
                        if (bytes[j] == (byte)'\n')
                        {
                            lastDataKeywordEnd = j + 1;
                            break;
                        }
                    }
                }
            }

            if (lastDataKeywordEnd > 0) return lastDataKeywordEnd;

            for (int i = 0; i < scanLen - 1; i++)
            {
                if (bytes[i] == (byte)'\n' && bytes[i + 1] == (byte)'\n') return i + 1;
            }
            for (int i = 0; i < scanLen - 3; i++)
            {
                if (bytes[i] == '\r' && bytes[i + 1] == '\n' && bytes[i + 2] == '\r' && bytes[i + 3] == '\n') return i + 2;
            }

            return -1;
        }

        // ══════════════════════════════════════════════════════════════
        // 辅助方法
        // ══════════════════════════════════════════════════════════════

        private string FindLatestOutputDir()
        {
            string baseDir = Path.Combine(Path.GetTempPath(), "CityLBM");
            if (!Directory.Exists(baseDir)) return null;

            string bestDir = null;
            DateTime bestTime = DateTime.MinValue;

            try
            {
                foreach (var caseDir in Directory.GetDirectories(baseDir))
                {
                    string outputDir = Path.Combine(caseDir, "output");
                    if (!Directory.Exists(outputDir)) continue;

                    var vtkFiles = Directory.GetFiles(outputDir, "*.vtk");
                    if (vtkFiles.Length == 0) continue;

                    foreach (var f in vtkFiles)
                    {
                        DateTime writeTime = File.GetLastWriteTime(f);
                        if (writeTime > bestTime)
                        {
                            bestTime = writeTime;
                            bestDir = outputDir;
                        }
                    }
                }
            }
            catch { }

            return bestDir;
        }

        private void ApplyVertexColors(Mesh mesh, List<Color> colors)
        {
            if (mesh == null || mesh.Vertices.Count == 0 || colors.Count == 0)
                return;

            mesh.VertexColors.Clear();
            int count = Math.Min(mesh.Vertices.Count, colors.Count);
            for (int i = 0; i < count; i++)
                mesh.VertexColors.SetColor(i, colors[i]);
            for (int i = count; i < mesh.Vertices.Count; i++)
                mesh.VertexColors.SetColor(i, Color.Gray);
        }

        private double EstimatePointSize(List<Point3d> points)
        {
            if (points.Count < 2) return 1.0;
            BoundingBox bbox = new BoundingBox(points);
            double dx = bbox.Max.X - bbox.Min.X;
            double dy = bbox.Max.Y - bbox.Min.Y;
            double dz = bbox.Max.Z - bbox.Min.Z;

            double area = Math.Max(dx * dy, Math.Max(dx * dz, dy * dz));
            if (area < 1e-10)
                return Math.Max(0.1, (dx + dy + dz) / Math.Max(1, points.Count));

            return Math.Max(0.1, Math.Sqrt(area / points.Count));
        }

        private Color InterpolateColor(Color c1, Color c2, double t, bool useGradient = true)
        {
            t = Math.Max(0, Math.Min(1, t));

            if (useGradient)
            {
                if (t < 0.25)
                {
                    double s = t / 0.25;
                    return Color.FromArgb(255, 0, (int)(255 * s), 255);
                }
                else if (t < 0.5)
                {
                    double s = (t - 0.25) / 0.25;
                    return Color.FromArgb(255, 0, 255, (int)(255 * (1 - s)));
                }
                else if (t < 0.75)
                {
                    double s = (t - 0.5) / 0.25;
                    return Color.FromArgb(255, (int)(255 * s), 255, 0);
                }
                else
                {
                    double s = (t - 0.75) / 0.25;
                    return Color.FromArgb(255, 255, (int)(255 * (1 - s)), 0);
                }
            }
            else
            {
                int r = (int)(c1.R + t * (c2.R - c1.R));
                int g = (int)(c1.G + t * (c2.G - c1.G));
                int b = (int)(c1.B + t * (c2.B - c1.B));
                return Color.FromArgb(255,
                    Math.Max(0, Math.Min(255, r)),
                    Math.Max(0, Math.Min(255, g)),
                    Math.Max(0, Math.Min(255, b)));
            }
        }

        private int FindNearestPoint(Point3d pt, List<Point3d> points)
        {
            int nearest = 0;
            double minDist = double.MaxValue;
            for (int i = 0; i < points.Count; i++)
            {
                double d = pt.DistanceToSquared(points[i]);
                if (d < minDist) { minDist = d; nearest = i; }
            }
            return nearest;
        }

        private bool IsPointInDomain(Point3d pt, List<Point3d> domainPoints)
        {
            BoundingBox bbox = new BoundingBox(domainPoints);
            return bbox.Contains(pt);
        }

        private Mesh CreatePolylinePipe(List<Point3d> points, double radius)
        {
            Mesh pipe = new Mesh();
            int segments = 8;

            for (int i = 0; i < points.Count; i++)
            {
                Point3d pt = points[i];
                Vector3d dir;

                if (i < points.Count - 1)
                    dir = points[i + 1] - pt;
                else
                    dir = pt - points[i - 1];

                dir.Unitize();

                Vector3d up = Math.Abs(dir.Z) < 0.99 ? new Vector3d(0, 0, 1) : new Vector3d(1, 0, 0);
                Vector3d right = Vector3d.CrossProduct(dir, up);
                right.Unitize();
                up = Vector3d.CrossProduct(right, dir);
                up.Unitize();

                for (int j = 0; j < segments; j++)
                {
                    double angle = 2 * Math.PI * j / segments;
                    Point3d p = pt + radius * (Math.Cos(angle) * right + Math.Sin(angle) * up);
                    pipe.Vertices.Add((float)p.X, (float)p.Y, (float)p.Z);
                }

                if (i > 0)
                {
                    int prevBase = (i - 1) * segments;
                    int currBase = i * segments;
                    for (int j = 0; j < segments; j++)
                    {
                        int next = (j + 1) % segments;
                        pipe.Faces.AddFace(prevBase + j, prevBase + next, currBase + next, currBase + j);
                    }
                }
            }

            return pipe;
        }

        private string GenerateLegend(string fieldName, double minVal, double maxVal, Color cLow, Color cHigh, bool useGradient = true)
        {
            string colorScheme = useGradient ? "蓝->青->绿->黄->红（渐变）" : $"{ColorTranslator.ToHtml(cLow)} -> {ColorTranslator.ToHtml(cHigh)}（双色）";
            return $"===============================\n" +
                   $"  {fieldName} 云图图例\n" +
                   $"===============================\n" +
                   $"  最大值: {maxVal:E4}\n" +
                   $"  最小值: {minVal:E4}\n" +
                   $"  范围:   {maxVal - minVal:E4}\n" +
                   $"-------------------------------\n" +
                   $"  颜色映射: {colorScheme}\n" +
                   $"===============================";
        }

        private string GetModeName(int mode)
        {
            switch (mode)
            {
                case 0: return "水平切片";
                case 1: return "多层切片";
                case 2: return "等值线";
                case 3: return "流线";
                default: return $"未知({mode})";
            }
        }

        private double ReadBigEndianDouble(byte[] bytes, int offset)
        {
            byte[] v = new byte[8];
            Array.Copy(bytes, offset, v, 0, 8);
            if (BitConverter.IsLittleEndian) Array.Reverse(v);
            return BitConverter.ToDouble(v, 0);
        }

        private float ReadBigEndianFloat(byte[] bytes, int offset)
        {
            byte[] v = new byte[4];
            Array.Copy(bytes, offset, v, 0, 4);
            if (BitConverter.IsLittleEndian) Array.Reverse(v);
            return BitConverter.ToSingle(v, 0);
        }

        private int ExtractTimeStepFromFilename(string filename)
        {
            string name = Path.GetFileNameWithoutExtension(filename);
            string[] parts = name.Split('_');
            if (parts.Length > 1 && int.TryParse(parts[parts.Length - 1], out int ts))
                return ts;
            return 0;
        }

        protected override Bitmap Icon => null;

        public override Guid ComponentGuid => new Guid("D6E2F4A8-B1C3-4D5E-9F7A-2B3C4D5E6F7A");
    }
}
