using System;
using System.Drawing;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Solver;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// VTK 结果读取组件（含 Subsample 采样）
    /// 读取 FluidX3D 输出的 VTK 文件，基于物理间距进行降采样后输出 GH 数据
    /// </summary>
    public class ReadVTKComponent : GH_Component
    {
        public ReadVTKComponent()
            : base("Read VTK", "VTK",
                   "读取 FluidX3D 输出的 VTK 结果文件（支持按物理间距降采样）",
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
                "  -1 = 读取全部 VTK 文件（所有时间步展平输出）\n" +
                "  ≥0 = 读取指定时间步",
                GH_ParamAccess.item, -2);

            pManager.AddNumberParameter("Subsample Spacing", "SS",
                "可视化采样间距（物理单位，默认 5 m）。\n" +
                "组件自动将此值除以网格间距得到整数步长 Step。\n" +
                "设为 0 或负数时不做采样（输出全部点）。",
                GH_ParamAccess.item, 5.0);

            pManager.AddIntegerParameter("Subsample Step", "SK",
                "手动指定采样步长（每隔几个格点取一个）。\n" +
                "-1 = 自动（由 Subsample Spacing 计算），\n" +
                " 1 = 不采样（输出全部），\n" +
                " N = 每 N 个格点取 1 个。",
                GH_ParamAccess.item, -1);

            // VTK Path 为可选（留空自动搜索），其余参数保持可选
            pManager[0].Optional = true;
            pManager[1].Optional = true;
            pManager[2].Optional = true;
            pManager[3].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt",
                "采样后的网格点坐标（所有时间步展平）",
                GH_ParamAccess.list);

            pManager.AddVectorParameter("Velocity", "V",
                "采样后的速度向量（所有时间步展平）",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Pressure", "P",
                "压力值（如果有）",
                GH_ParamAccess.list);

            pManager.AddIntegerParameter("Time Step", "T",
                "每个输出点对应的时间步",
                GH_ParamAccess.list);

            pManager.AddTextParameter("Info", "I",
                "结果信息（包含采样参数）",
                GH_ParamAccess.item);

            pManager.AddNumberParameter("Grid Spacing", "GS",
                "VTK 文件的原始网格间距（如为结构化网格则为平均值）",
                GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            string vtkPath = "";
            int timeStep  = -1;
            double subsampleSpacing = 5.0;
            int manualStep = -1;

            DA.GetData(0, ref vtkPath);  // 可选，留空自动搜索
            DA.GetData(1, ref timeStep);
            DA.GetData(2, ref subsampleSpacing);
            DA.GetData(3, ref manualStep);

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
                    "请先运行模拟，或将 Run Simulation 的 Output Dir 输出端连接到 VTK Path 输入端。");
                return;
            }

            // ── 收集 VTK 文件 ──────────────────────────────────────
            List<string> vtkFiles = new List<string>();
            if (Directory.Exists(vtkPath))
            {
                string[] files = Directory.GetFiles(vtkPath, "*.vtk");
                Array.Sort(files); // 按名称排序，使时间步有序
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

            // ── 第一步：先读第一个文件探测网格间距 ───────────────────
            double detectedSpacing = 0.0;
            try
            {
                VTKGridInfo gridInfo = ProbeGridSpacing(vtkFiles[0]);
                detectedSpacing = gridInfo.MinSpacing;
            }
            catch
            {
                // 探测失败则维持 0
            }

            // ── 第二步：计算最终 step ──────────────────────────────
            int step;
            int maxStep = 1000; // 采样步长上限，防止 step 过大导致无输出点
            if (manualStep > 0)
            {
                // 用户手动指定
                step = Math.Min(manualStep, maxStep);
            }
            else if (subsampleSpacing > 0 && detectedSpacing > 1e-10)
            {
                // 自动：物理间距 / 格点间距，至少 1
                step = Math.Max(1, (int)Math.Round(subsampleSpacing / detectedSpacing));
                step = Math.Min(step, maxStep);
            }
            else
            {
                // 不采样
                step = 1;
            }

            // ── 第三步：处理 -2（自动选最后一个时间步）──────────────
            if (timeStep == -2)
            {
                // 先从文件名中提取所有时间步，选最大的
                int latestStep = -1;
                string bestFile = null;
                foreach (string file in vtkFiles)
                {
                    try
                    {
                        int ts = ExtractTimeStepFromFilename(file);
                        if (ts > latestStep)
                        {
                            latestStep = ts;
                            bestFile = file;
                        }
                    }
                    catch { }
                }

                if (bestFile == null)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "无法从文件名中提取时间步，请手动指定 T 或设为 -1");
                    return;
                }

                // 只保留最后一个时间步对应的文件
                var filteredFiles = new List<string>();
                foreach (string file in vtkFiles)
                {
                    try
                    {
                        int ts = ExtractTimeStepFromFilename(file);
                        if (ts == latestStep)
                        {
                            filteredFiles.Add(file);
                            break;
                        }
                    }
                    catch { }
                }

                // 更新 vtkFiles 为过滤后的列表
                vtkFiles = filteredFiles;
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                    $"自动选择最后时间步: T={latestStep} ({Path.GetFileName(bestFile)})");
            }

            // ── 第四步：正式读取并采样 ─────────────────────────────
            List<VTKResult> results = new List<VTKResult>();
            foreach (string file in vtkFiles)
            {
                try
                {
                    VTKResult result = ParseVTKFile(file, step);
                    // timeStep == -2 时 vtkFiles 已被过滤为 1 个文件，直接加入
                    // timeStep == -1 时读取全部
                    // timeStep >= 0 时按指定步数过滤
                    if (timeStep == -2 || timeStep == -1 || result.TimeStep == timeStep)
                        results.Add(result);
                }
                catch (Exception ex)
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
                        $"读取文件失败: {Path.GetFileName(file)} - {ex.Message}");
                }
            }

            if (results.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "未找到有效 VTK 结果");
                return;
            }

            // ── 第五步：展平输出 ───────────────────────────────────
            List<Point3d>  allPoints      = new List<Point3d>();
            List<Vector3d> allVelocities  = new List<Vector3d>();
            List<double>   allPressures   = new List<double>();
            List<int>      allTimeSteps   = new List<int>();

            int totalRawPoints = 0;
            foreach (VTKResult result in results)
            {
                if (result.Points != null)
                {
                    allPoints.AddRange(result.Points);
                    totalRawPoints += result.RawPointCount;
                }
                if (result.Velocities != null)
                    allVelocities.AddRange(result.Velocities);
                if (result.Scalars.ContainsKey("pressure"))
                    allPressures.AddRange(result.Scalars["pressure"]);
                if (result.Points != null)
                {
                    for (int i = 0; i < result.Points.Count; i++)
                        allTimeSteps.Add(result.TimeStep);
                }
            }

            // ── 输出 ───────────────────────────────────────────────
            DA.SetDataList(0, allPoints);
            DA.SetDataList(1, allVelocities);
            DA.SetDataList(2, allPressures);
            DA.SetDataList(3, allTimeSteps);

            // 构建 Info 文本
            double samplingRate = totalRawPoints > 0
                ? 100.0 * allPoints.Count / totalRawPoints
                : 100.0;

            string spacingStr = detectedSpacing > 0
                ? $"{detectedSpacing:F3} m"
                : "未知";

            string stepDesc = manualStep > 0
                ? $"手动 Step={step}"
                : (subsampleSpacing > 0
                    ? $"自动 Step={step}（{subsampleSpacing:F1} m ÷ {spacingStr}）"
                    : "不采样");

            DA.SetData(4,
                $"读取了 {results.Count} 个 VTK 文件\n" +
                $"原始点数:   {totalRawPoints:N0}\n" +
                $"输出点数:   {allPoints.Count:N0}  ({samplingRate:F1}%)\n" +
                $"速度向量数: {allVelocities.Count:N0}\n" +
                $"网格间距:   {spacingStr}\n" +
                $"采样策略:   {stepDesc}\n" +
                $"时间步范围: {results.Min(r => r.TimeStep)} → {results.Max(r => r.TimeStep)}");

            DA.SetData(5, detectedSpacing);
        }

        // ══════════════════════════════════════════════════════════════
        // 探测网格间距（只读头部，不读完整数据）
        // ══════════════════════════════════════════════════════════════

        private struct VTKGridInfo
        {
            public double MinSpacing;
            public int[]  Dimensions;
        }

        private VTKGridInfo ProbeGridSpacing(string vtkPath)
        {
            VTKGridInfo info = new VTKGridInfo
            {
                Dimensions = new int[3],
                MinSpacing = 0.0
            };

            // 读前 2 KB，足够包含所有头部信息
            byte[] buf = new byte[2048];
            int n;
            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
                n = fs.Read(buf, 0, buf.Length);

            string header = System.Text.Encoding.ASCII.GetString(buf, 0, n);
            string[] lines = header.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

            float[] spacing  = null;
            int[]   dims     = null;

            foreach (string line in lines)
            {
                string t = line.Trim();

                if (t.StartsWith("SPACING"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        spacing = new float[3];
                        float.TryParse(p[1], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[0]);
                        float.TryParse(p[2], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[1]);
                        float.TryParse(p[3], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[2]);
                    }
                }
                else if (t.StartsWith("DIMENSIONS"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        dims = new int[3];
                        int.TryParse(p[1], out dims[0]);
                        int.TryParse(p[2], out dims[1]);
                        int.TryParse(p[3], out dims[2]);
                    }
                }
            }

            if (spacing != null)
            {
                // 取 x/y 平面中最小的非零间距
                double sp = double.MaxValue;
                for (int i = 0; i < 3; i++)
                    if (spacing[i] > 1e-10 && spacing[i] < sp)
                        sp = spacing[i];
                info.MinSpacing = sp < double.MaxValue ? sp : 0.0;
            }

            if (dims != null)
                info.Dimensions = dims;

            return info;
        }

        // ══════════════════════════════════════════════════════════════
        // 主解析入口
        // ══════════════════════════════════════════════════════════════

        private VTKResult ParseVTKFile(string vtkPath, int step)
        {
            VTKResult result = new VTKResult
            {
                FilePath  = vtkPath,
                TimeStep  = ExtractTimeStepFromFilename(vtkPath),
                RawPointCount = 0
            };

            bool isBinary = false;
            using (StreamReader sr = new StreamReader(vtkPath))
            {
                string line;
                while ((line = sr.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (line == "BINARY") { isBinary = true;  break; }
                    if (line == "ASCII")  { isBinary = false; break; }
                }
            }

            if (isBinary)
                ParseBinaryVTK(vtkPath, result, step);
            else
                ParseASCIIVTK(vtkPath, result, step);

            return result;
        }

        // ══════════════════════════════════════════════════════════════
        // ASCII VTK 解析（带 step 采样）
        // ══════════════════════════════════════════════════════════════

        private void ParseASCIIVTK(string vtkPath, VTKResult result, int step)
        {
            using (StreamReader reader = new StreamReader(vtkPath))
            {
                string line;
                bool readingPoints    = false;
                bool readingVelocities = false;
                bool readingScalars   = false;
                bool skipLookupTable  = false;
                string currentScalar  = "";
                List<double> currentScalarValues = null;
                int expectedPointCount = 0;
                int rawIdx = 0; // 当前读到第几个原始点

                // 用于 STRUCTURED_POINTS 生成坐标
                int[] dims    = null;
                float[] org   = null;
                float[] spc   = null;

                while ((line = reader.ReadLine()) != null)
                {
                    line = line.Trim();
                    if (string.IsNullOrEmpty(line)) continue;

                    if (line.StartsWith("#") || line == "ASCII") continue;

                    if (line.StartsWith("DATASET"))
                    {
                        // 记录数据集类型
                        if (line.Contains("STRUCTURED_POINTS"))
                        {
                            dims = new int[3];
                            org  = new float[3];
                            spc  = new float[3];
                        }
                        continue;
                    }

                    // ── STRUCTURED_POINTS 头部 ────────────────────────
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
                                float.TryParse(p[1], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out org[0]);
                                float.TryParse(p[2], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out org[1]);
                                float.TryParse(p[3], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out org[2]);
                            }
                            continue;
                        }
                        if (line.StartsWith("SPACING"))
                        {
                            string[] p = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 4)
                            {
                                float.TryParse(p[1], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out spc[0]);
                                float.TryParse(p[2], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out spc[1]);
                                float.TryParse(p[3], System.Globalization.NumberStyles.Float,
                                    System.Globalization.CultureInfo.InvariantCulture, out spc[2]);
                            }
                            continue;
                        }
                    }

                    // ── POINTS 节（非结构化） ─────────────────────────
                    if (line.StartsWith("POINTS"))
                    {
                        string[] parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length >= 2)
                            int.TryParse(parts[1], out expectedPointCount);
                        result.RawPointCount = expectedPointCount;

                        int cap = (expectedPointCount / step) + 1;
                        result.Points     = new List<Point3d>(cap);
                        result.Velocities = null; // 先清空，等 VECTORS 节再填

                        readingPoints     = true;
                        readingVelocities = false;
                        readingScalars    = false;
                        rawIdx = 0;
                        continue;
                    }

                    // ── POINT_DATA ────────────────────────────────────
                    if (line.StartsWith("POINT_DATA"))
                    {
                        // STRUCTURED_POINTS 在这里才生成坐标（已经知道 dims / org / spc）
                        if (dims != null && result.Points == null && expectedPointCount > 0)
                            _ = GenerateStructuredPoints(result, dims, org, spc, step);

                        readingPoints = false;
                        continue;
                    }

                    // ── VECTORS ───────────────────────────────────────
                    if (line.StartsWith("VECTORS"))
                    {
                        readingVelocities = true;
                        readingScalars    = false;
                        readingPoints     = false;
                        if (result.Velocities == null)
                        {
                            int cap = result.Points != null ? result.Points.Count : 64;
                            result.Velocities = new List<Vector3d>(cap);
                        }
                        rawIdx = 0;
                        continue;
                    }

                    // ── SCALARS ───────────────────────────────────────
                    if (line.StartsWith("SCALARS"))
                    {
                        if (readingScalars && currentScalarValues != null && currentScalarValues.Count > 0)
                            result.Scalars[currentScalar] = currentScalarValues;

                        string[] parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        currentScalar       = parts.Length > 1 ? parts[1] : "scalar";
                        currentScalarValues = new List<double>();
                        readingScalars    = true;
                        readingVelocities = false;
                        readingPoints     = false;
                        skipLookupTable   = false;
                        rawIdx = 0;
                        continue;
                    }

                    if (line.StartsWith("LOOKUP_TABLE"))
                    {
                        skipLookupTable = true;
                        continue;
                    }

                    if (line.StartsWith("CELL_DATA") || line.StartsWith("CELLS") || line.StartsWith("POLYGONS"))
                    {
                        if (readingScalars && currentScalarValues != null && currentScalarValues.Count > 0)
                            result.Scalars[currentScalar] = currentScalarValues;
                        readingPoints = readingVelocities = readingScalars = false;
                        continue;
                    }

                    // ── 解析点坐标 ────────────────────────────────────
                    if (readingPoints && rawIdx < expectedPointCount)
                    {
                        string[] c = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        if (c.Length >= 3 &&
                            double.TryParse(c[0], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double x) &&
                            double.TryParse(c[1], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double y) &&
                            double.TryParse(c[2], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double z))
                        {
                            if (rawIdx % step == 0)
                                result.Points.Add(new Point3d(x, y, z));
                            rawIdx++;
                        }
                        continue;
                    }

                    // ── 解析速度向量 ──────────────────────────────────
                    if (readingVelocities)
                    {
                        string[] c = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        if (c.Length >= 3 &&
                            double.TryParse(c[0], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double vx) &&
                            double.TryParse(c[1], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double vy) &&
                            double.TryParse(c[2], System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double vz))
                        {
                            if (rawIdx % step == 0)
                                result.Velocities.Add(new Vector3d(vx, vy, vz));
                            rawIdx++;
                        }
                        continue;
                    }

                    // ── 解析标量 ──────────────────────────────────────
                    if (readingScalars)
                    {
                        if (skipLookupTable && !double.TryParse(line, out _))
                        {
                            skipLookupTable = false;
                            continue;
                        }
                        if (double.TryParse(line, System.Globalization.NumberStyles.Float,
                                System.Globalization.CultureInfo.InvariantCulture, out double val))
                        {
                            if (rawIdx % step == 0)
                                currentScalarValues.Add(val);
                            rawIdx++;
                        }
                        continue;
                    }
                }

                // 保存最后一个标量
                if (readingScalars && currentScalarValues != null && currentScalarValues.Count > 0)
                    result.Scalars[currentScalar] = currentScalarValues;

                // STRUCTURED_POINTS 如果还没生成坐标（没有 POINT_DATA 节的情况）
                if (dims != null && result.Points == null && expectedPointCount > 0)
                    _ = GenerateStructuredPoints(result, dims, org, spc, step);

                // 修正原始点数
                if (result.RawPointCount == 0)
                    result.RawPointCount = expectedPointCount;
            }
        }

        /// <summary>
        /// 为 STRUCTURED_POINTS 数据集生成采样后的坐标列表。
        /// 同时生成线性索引映射表，保证 Binary 速度数据按相同的采样点取值。
        /// 采样规则：i、j、k 三个方向均以 step 步进。
        /// 线性索引 = i + j*nx + k*nx*ny
        /// </summary>
        /// <returns>采样点的线性索引列表（与 result.Points 一一对应）</returns>
        private List<int> GenerateStructuredPoints(VTKResult result, int[] dims,
            float[] org, float[] spc, int step)
        {
            int nx = dims[0], ny = dims[1], nz = dims[2];
            result.RawPointCount = nx * ny * nz;

            int estCap = (nx / step + 1) * (ny / step + 1) * (nz / step + 1);
            result.Points = new List<Point3d>(estCap);
            var sampledIndices = new List<int>(estCap);

            for (int k = 0; k < nz; k += step)
                for (int j = 0; j < ny; j += step)
                    for (int i = 0; i < nx; i += step)
                    {
                        double x = org[0] + i * spc[0];
                        double y = org[1] + j * spc[1];
                        double z = org[2] + k * spc[2];
                        result.Points.Add(new Point3d(x, y, z));
                        sampledIndices.Add(i + j * nx + k * nx * ny);
                    }

            return sampledIndices;
        }

        // ══════════════════════════════════════════════════════════════
        // Binary VTK 解析（带 step 采样）
        // ══════════════════════════════════════════════════════════════

        private void ParseBinaryVTK(string vtkPath, VTKResult result, int step)
        {
            // ── 第一阶段：解析头部 ──────────────────────────────────
            // FluidX3D write_device_to_vtk 输出格式：
            //   # vtk DataFile Version 2.0
            //   FluidX3D
            //   BINARY
            //   DATASET STRUCTURED_POINTS
            //   DIMENSIONS nx ny nz
            //   ORIGIN ox oy oz
            //   SPACING dx dy dz
            //   POINT_DATA count
            //   VECTORS velocity float
            //   [binary: count * 3 floats, big-endian]
            //
            // 也可能有 SCALARS 段（在 VECTORS 之后），但 FluidX3D 默认只输出 VECTORS。

            byte[] headerBuf = new byte[4096];
            int headerLen;
            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
                headerLen = fs.Read(headerBuf, 0, headerBuf.Length);

            // 找到头部结束位置：最后一个非空文本行后的换行符
            int headerEndPos = FindBinaryHeaderEnd(headerBuf, headerLen);
            if (headerEndPos < 0)
                throw new Exception("无法找到 VTK 二进制头部结束位置");

            string header = System.Text.Encoding.ASCII.GetString(headerBuf, 0, headerEndPos);
            string[] lines = header.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

            int[]   dimensions = new int[3];
            float[] origin     = new float[3];
            float[] spacing    = new float[3];
            int     pointCount = 0;
            bool    isStructured = false;
            string  dataType     = "float";  // VECTORS 行的数据类型

            // 数据段描述：记录每个段的类型、数据类型和偏移
            var dataSections = new List<DataSection>();
            int currentSectionStart = -1;

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
                        pointCount   = dimensions[0] * dimensions[1] * dimensions[2];
                        isStructured = true;
                    }
                }
                else if (t.StartsWith("ORIGIN"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        float.TryParse(p[1], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out origin[0]);
                        float.TryParse(p[2], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out origin[1]);
                        float.TryParse(p[3], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out origin[2]);
                    }
                }
                else if (t.StartsWith("SPACING"))
                {
                    string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (p.Length >= 4)
                    {
                        float.TryParse(p[1], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[0]);
                        float.TryParse(p[2], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[1]);
                        float.TryParse(p[3], System.Globalization.NumberStyles.Float,
                            System.Globalization.CultureInfo.InvariantCulture, out spacing[2]);
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
                    // 格式: VECTORS name datatype
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
                    // 格式: SCALARS name datatype numComponents
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
                // LOOKUP_TABLE 标志 SCALARS 数据的开始
                // （注意：SCALARS 可能没有 LOOKUP_TABLE，直接跟数据）
            }

            result.RawPointCount = pointCount;

            // ── 第二阶段：生成坐标（结构化网格采样） ────────────────
            List<int> sampledIndices = null;
            if (isStructured && pointCount > 0)
            {
                sampledIndices = GenerateStructuredPoints(result, dimensions, origin, spacing, step);
            }

            // ── 第三阶段：读取二进制数据 ────────────────────────────
            // FluidX3D 默认只输出 VECTORS，但也要支持 SCALARS 段
            if (dataSections.Count == 0)
                return;

            long filePos = headerEndPos; // 二进制数据从这里开始

            using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
            {
                foreach (var section in dataSections)
                {
                    int bytesPerValue = section.DataType == "double" ? 8 : 4;
                    int bytesPerPoint = section.Components * bytesPerValue;

                    // 读取该段的所有数据
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

                    if (totalRead < sectionBytes)
                    {
                        // 数据不足，跳过此段
                        filePos += totalRead;
                        continue;
                    }

                    // ── 3 分量 SCALARS（如 FluidX3D 的 SCALARS data float 3）视为向量 ──
                    bool treatAsVector = (section.Type == "SCALARS" && section.Components == 3);
                    // 检查名称是否包含 velocity / u / v / w（也是速度的标志）
                    if (!treatAsVector && section.Type == "SCALARS")
                    {
                        string nameLower = (section.Name ?? "").ToLowerInvariant();
                        if (nameLower == "velocity" || nameLower == "u" || nameLower == "data")
                            treatAsVector = true;
                    }

                    if (section.Type == "VECTORS" || treatAsVector)
                    {
                        // 读取速度向量，按采样索引取值
                        if (sampledIndices != null && result.Points != null)
                        {
                            // 结构化网格：用采样索引表精准取值
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
                            // 非结构化：线性步进采样
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

                        // 如果是 SCALARS 被当作向量，也存一份到 Scalars 里
                        if (treatAsVector)
                        {
                            result.Scalars[section.Name] = result.Velocities
                                .Select(v => v.Length).ToList();
                        }
                    }
                    else if (section.Type == "SCALARS")
                    {
                        // 读取标量数据（单分量）
                        var values = new List<double>();
                        if (sampledIndices != null)
                        {
                            foreach (int idx in sampledIndices)
                            {
                                int off = idx * bytesPerValue;
                                if (off + bytesPerValue <= sectionData.Length)
                                {
                                    double val = section.DataType == "double"
                                        ? ReadBigEndianDouble(sectionData, off)
                                        : ReadBigEndianFloat(sectionData, off);
                                    values.Add(val);
                                }
                            }
                        }
                        else
                        {
                            for (int rawIdx = 0; rawIdx < pointCount; rawIdx++)
                            {
                                if (rawIdx % step == 0)
                                {
                                    int off = rawIdx * bytesPerValue;
                                    double val = section.DataType == "double"
                                        ? ReadBigEndianDouble(sectionData, off)
                                        : ReadBigEndianFloat(sectionData, off);
                                    values.Add(val);
                                }
                            }
                        }
                        result.Scalars[section.Name] = values;
                    }

                    filePos += sectionBytes;
                }
            }
        }

        private struct DataSection
        {
            public string Type;       // "VECTORS" or "SCALARS"
            public string Name;       // variable name
            public string DataType;   // "float" or "double"
            public int Components;    // 3 for VECTORS, 1 for SCALARS (default)
        }

        /// <summary>
        /// 找到 Binary VTK 头部的结束位置。
        /// 头部是纯文本，最后一行（VECTORS / LOOKUP_TABLE / 无 LOOKUP_TABLE 的 SCALARS）之后紧跟二进制数据。
        /// 关键规则：
        ///   - VECTORS 行之后直接是二进制数据
        ///   - SCALARS 行之后可能有 LOOKUP_TABLE 行，LOOKUP_TABLE 行之后才是二进制数据
        ///   - 如果 SCALARS 后面没有 LOOKUP_TABLE，则 SCALARS 行之后直接是二进制数据
        /// 策略：先找最后一个数据关键字行（VECTORS / SCALARS / LOOKUP_TABLE），返回其后的 \n+1。
        /// </summary>
        private int FindBinaryHeaderEnd(byte[] bytes, int length)
        {
            int scanLen = Math.Min(length, 4096);
            int lastDataKeywordEnd = -1; // 最后一个数据关键字行的 \n+1 位置

            for (int i = 0; i < scanLen; i++)
            {
                string candidate = System.Text.Encoding.ASCII.GetString(bytes, i, Math.Min(20, scanLen - i));
                if (candidate.StartsWith("VECTORS") || candidate.StartsWith("SCALARS") ||
                    candidate.StartsWith("LOOKUP_TABLE"))
                {
                    // 找到数据关键字，找这行的末尾换行符
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

            if (lastDataKeywordEnd > 0)
                return lastDataKeywordEnd;

            // 备用方案：找连续两个 \n（空行）
            for (int i = 0; i < scanLen - 1; i++)
            {
                if (bytes[i] == (byte)'\n' && bytes[i + 1] == (byte)'\n')
                    return i + 1;
            }
            // 找 \r\n\r\n
            for (int i = 0; i < scanLen - 3; i++)
            {
                if (bytes[i] == '\r' && bytes[i + 1] == '\n' && bytes[i + 2] == '\r' && bytes[i + 3] == '\n')
                    return i + 2;
            }

            return -1;
        }

        // ══════════════════════════════════════════════════════════════
        // 自动搜索最新 Case 的 output 目录
        // ══════════════════════════════════════════════════════════════

        /// <summary>
        /// 在 %TEMP%\CityLBM\ 下搜索最近修改的包含 .vtk 文件的 output 目录。
        /// 搜索策略：
        ///   1. 遍历所有 Case 子目录
        ///   2. 检查 Case/output/ 是否存在 VTK 文件
        ///   3. 按 output 目录最近修改时间排序，选最新的
        /// </summary>
        private string FindLatestOutputDir()
        {
            string baseDir = Path.Combine(Path.GetTempPath(), "CityLBM");
            if (!Directory.Exists(baseDir))
                return null;

            string bestDir = null;
            DateTime bestTime = DateTime.MinValue;

            try
            {
                foreach (var caseDir in Directory.GetDirectories(baseDir))
                {
                    string outputDir = Path.Combine(caseDir, "output");
                    if (!Directory.Exists(outputDir))
                        continue;

                    // 检查是否有 VTK 文件
                    var vtkFiles = Directory.GetFiles(outputDir, "*.vtk");
                    if (vtkFiles.Length == 0)
                        continue;

                    // 找到最近的文件修改时间
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

        // ══════════════════════════════════════════════════════════════
        // 工具方法
        // ══════════════════════════════════════════════════════════════

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

        // 保留 BinaryReader 重载（内部已不用，保留避免编译警告）
        private float ReadBigEndianFloat(BinaryReader reader)
        {
            byte[] b = reader.ReadBytes(4);
            if (BitConverter.IsLittleEndian) Array.Reverse(b);
            return BitConverter.ToSingle(b, 0);
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

        public override Guid ComponentGuid
            => new Guid("A3B7C9D2-8E4F-4A5B-9C6D-7E8F9A0B1C2D");
    }
}
