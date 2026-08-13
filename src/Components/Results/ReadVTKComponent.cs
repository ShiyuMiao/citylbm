using System;
using System.Drawing;
using System.Collections.Generic;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Linq;
using System.Threading.Tasks;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Solver;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// VTK 结果读取组件（含 Subsample 采样）
    /// 读取 FluidX3D 输出的 VTK 文件，基于物理间距进行降采样后输出 GH 数据
    /// </summary>
    public class ReadVTKComponent : GH_Component
    {
        // ── 后台加载状态（P0 性能优化：触发-轮询模式，解决 GH 假死）──
        private Task<List<VTKResult>> _loadTask;
        private List<VTKResult>       _cachedResults;
        private string  _cachedKey;          // vtkPath + step + timeStep 的组合键
        private double  _cachedSpacing;      // 上次检测到的网格间距
        private string  _cachedInfo;         // 上次的 Info 输出
        
        // 场景追踪：检测场景变化以自动更新 VTK 路径
        private string  _lastSceneName;      // 上次处理的场景名称
        private string  _lastCaseDir;        // 上次使用的 Case 目录
        private DateTime _lastVtkWriteTime;  // 上次 VTK 文件修改时间

        public ReadVTKComponent()
            : base("Read VTK", "VTK",
                   "读取 FluidX3D 输出的 VTK 结果文件（支持按物理间距降采样）",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddGenericParameter("Scene", "S",
                "CityLBM 场景（可选）。\n" +
                "连接后自动使用该场景的 Case 目录查找 VTK 文件。\n" +
                "优先级：VTK Path > Scene > 自动搜索最新",
                GH_ParamAccess.item);

            pManager.AddTextParameter("VTK Path", "P",
                "VTK 文件路径或包含 VTK 文件的目录。\n" +
                "留空且未连接 Scene 时，自动搜索 %TEMP%\\CityLBM 下最新模拟的 output 目录。",
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

            // VTK Path 和 Scene 均可选
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
                
            pManager.AddTextParameter("Log", "Log",
                "详细执行日志（用于调试和问题诊断）",
                GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            var logger = new ComponentLogger("ReadVTK");
            
            string vtkPath = "";
            int timeStep  = -1;
            double subsampleSpacing = 5.0;
            int manualStep = -1;

            // S 端口：安全提取场景对象（用于物理坐标偏移）
            Core.Scene physicalScene = null;
            string sceneName = null;
            IGH_Goo goo0 = null;
            if (DA.GetData(0, ref goo0))
            {
                if (goo0 is GH_Scene ghScene && ghScene.Value != null)
                {
                    physicalScene = ghScene.Value;
                    sceneName = ghScene.Value.Name;
                    logger.Info($"输入场景: {sceneName}");
                }
                else
                {
                    string str = null;
                    if (DA.GetData(0, ref str))
                        sceneName = str;
                }
            }

            DA.GetData(1, ref vtkPath);  // VTK Path 可选，留空自动搜索
            DA.GetData(2, ref timeStep);
            DA.GetData(3, ref subsampleSpacing);
            DA.GetData(4, ref manualStep);
            
            logger.Config("TimeStep", timeStep);
            logger.Config("SubsampleSpacing", $"{subsampleSpacing:F2} m");
            logger.Config("ManualStep", manualStep);

            // ── VTK Path 为空时，优先用 Scene 推算路径，再全局搜索 ──
            // 检测场景变化：如果场景名称或 Case 目录改变，强制重新搜索路径
            bool sceneChanged = (sceneName != _lastSceneName);
            
            if (string.IsNullOrEmpty(vtkPath) || sceneChanged)
            {
                // 优先级 1：通过 Scene 名称推算 Case 目录
                if (!string.IsNullOrEmpty(sceneName))
                {
                    string caseDir = GetCaseOutputDir(sceneName);
                    if (caseDir != null)
                    {
                        // 检测 Case 目录是否变化
                        if (caseDir != _lastCaseDir)
                        {
                            vtkPath = caseDir;
                            _lastCaseDir = caseDir;
                            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                                $"通过场景 \"{sceneName}\" 找到输出目录: {vtkPath}");
                            // 场景变化时清除缓存，强制重新读取
                            _cachedResults = null;
                            _cachedKey = null;
                        }
                        else
                        {
                            // Case 目录相同，但检查是否有新 VTK 文件
                            vtkPath = caseDir;
                            CheckForNewVtkFiles(vtkPath);
                        }
                    }
                }

                // 优先级 2：全局搜索最新有 VTK 的 output 目录
                if (string.IsNullOrEmpty(vtkPath))
                {
                    string latestDir = FindLatestOutputDir();
                    if (!string.IsNullOrEmpty(latestDir) && latestDir != _lastCaseDir)
                    {
                        vtkPath = latestDir;
                        _lastCaseDir = latestDir;
                        AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"自动找到输出目录: {vtkPath}");
                        // 新目录时清除缓存
                        _cachedResults = null;
                        _cachedKey = null;
                    }
                    else if (!string.IsNullOrEmpty(latestDir))
                    {
                        vtkPath = latestDir;
                        CheckForNewVtkFiles(vtkPath);
                    }
                }
                
                _lastSceneName = sceneName;
            }

            if (string.IsNullOrEmpty(vtkPath))
            {
                logger.Error("未找到 VTK 输出目录");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "未找到 VTK 输出目录。\n" +
                    "请先运行模拟，或将 Run Simulation 的 Output Dir 输出端连接到 VTK Path 输入端。");
                DA.SetData(5, logger.GetLog());
                return;
            }
            
            logger.FileOperation("VTK路径", vtkPath);

            // ── 收集 VTK 文件 ──────────────────────────────────────
            List<string> vtkFiles = new List<string>();
            if (Directory.Exists(vtkPath))
            {
                string[] files = Directory.GetFiles(vtkPath, "*.vtk");
                Array.Sort(files); // 按名称排序，使时间步有序
                vtkFiles.AddRange(files);
                logger.FileOperation("扫描目录", vtkPath, null);
                logger.Statistics("发现VTK文件", files.Length);
            }
            else if (File.Exists(vtkPath))
            {
                vtkFiles.Add(vtkPath);
                var fileInfo = new FileInfo(vtkPath);
                logger.FileOperation("加载单个文件", vtkPath, fileInfo.Length);
            }
            else
            {
                logger.Error($"路径不存在: {vtkPath}");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, $"路径不存在: {vtkPath}");
                DA.SetData(5, logger.GetLog());
                return;
            }

            if (vtkFiles.Count == 0)
            {
                logger.Warning("目录中未找到 .vtk 文件");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "目录中未找到 .vtk 文件");
                DA.SetData(5, logger.GetLog());
                return;
            }

            // ── 第一步：先读第一个文件探测网格间距 ───────────────────
            logger.StepStart("探测网格信息");
            double detectedSpacing = 0.0;
            VTKGridInfo gridInfo = default;
            try
            {
                gridInfo = ProbeGridSpacing(vtkFiles[0]);
                detectedSpacing = gridInfo.MinSpacing;
                
                logger.Info($"VTK文件: {Path.GetFileName(vtkFiles[0])}");
                logger.DataSummary("网格维度", new Dictionary<string, object> {
                    ["Dimensions"] = $"{gridInfo.Dimensions[0]} x {gridInfo.Dimensions[1]} x {gridInfo.Dimensions[2]}",
                    ["总点数"] = gridInfo.Dimensions[0] * gridInfo.Dimensions[1] * gridInfo.Dimensions[2]
                });
                logger.Info($"检测到的最小间距: {detectedSpacing:F4}");
            }
            catch (Exception ex)
            {
                logger.Warning($"探测网格信息失败: {ex.Message}");
                // 探测失败则维持 0
            }
            logger.StepEnd("探测网格信息");

            // ── 第二步：计算最终 step ──────────────────────────────
            logger.StepStart("计算采样步长");
            int step;
            int maxStep = 1000; // 采样步长上限，防止 step 过大导致无输出点
            if (manualStep > 0)
            {
                // 用户手动指定
                step = Math.Min(manualStep, maxStep);
                logger.Info($"使用手动指定步长: {step}");
            }
            else if (subsampleSpacing > 0 && detectedSpacing > 1e-10)
            {
                // 自动：物理间距 / 格点间距，至少 1
                step = Math.Max(1, (int)Math.Round(subsampleSpacing / detectedSpacing));
                step = Math.Min(step, maxStep);
                logger.Info($"自动计算步长: {step} (目标间距 {subsampleSpacing:F2}m / 检测间距 {detectedSpacing:F4}m)");
            }
            else
            {
                // 不采样
                step = 1;
                logger.Info("不采样，步长=1");
            }
            logger.StepEnd("计算采样步长", $"最终步长={step}");

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

            // ── 第四步：缓存键检查 ─────────────────────────────────
            // 缓存键包含：路径、步长、时间步、场景名、最后修改时间
            string cacheKey = $"{vtkPath}|{step}|{timeStep}|{sceneName}|{_lastVtkWriteTime:yyyyMMddHHmmss}";
            if (_cachedResults != null && _cachedKey == cacheKey)
            {
                // 缓存命中，直接输出（包括上次的 Info）
                OutputCachedResults(DA, _cachedResults, _cachedSpacing, _cachedInfo, physicalScene, logger);
                return;
            }

            // ── 第五步：后台加载或等待 ─────────────────────────────
            // P0 性能优化：触发-轮询模式，避免 GH 假死
            if (_loadTask == null || _loadTask.IsCompleted == false)
            {
                if (_loadTask == null)
                {
                    // 首次触发：启动后台读取
                    _cachedKey = cacheKey;
                    var filesToLoad = new List<string>(vtkFiles);
                    int tsFilter = timeStep;

                    _loadTask = Task.Run(() =>
                    {
                        var results = new List<VTKResult>();
                        foreach (string file in filesToLoad)
                        {
                            try
                            {
                                VTKResult result = ParseVTKFile(file, step);
                                if (tsFilter == -2 || tsFilter == -1 || result.TimeStep == tsFilter)
                                    results.Add(result);
                            }
                            catch (Exception ex)
                            {
                                // 后台任务中无法 AddRuntimeMessage，记录到 result 或忽略
                                System.Diagnostics.Debug.WriteLine($"ParseVTKFile failed: {ex.Message}");
                            }
                        }
                        return results;
                    });

                    // 设置回调：完成后触发 GH 重算
                    _loadTask.ContinueWith(t =>
                    {
                        if (!t.IsFaulted)
                        {
                            Rhino.RhinoApp.InvokeOnUiThread((Action)(() =>
                            {
                                ExpireSolution(true);
                            }));
                        }
                    });

                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, "⏳ 正在后台读取 VTK 文件...");
                }
                else
                {
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, "⏳ 读取中，请稍候...");
                }
                return;  // 本次 Solve 提前返回，不阻塞 GH
            }

            // ── 后台任务已完成 ─────────────────────────────────────
            if (_loadTask.IsFaulted)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    _loadTask.Exception?.InnerException?.Message ?? "读取失败");
                _loadTask = null;
                return;
            }

            _cachedResults = _loadTask.Result;
            _cachedSpacing = detectedSpacing;
            _loadTask = null;

            // 构建 Info 并缓存
            _cachedInfo = BuildInfoText(_cachedResults, detectedSpacing, subsampleSpacing, manualStep, step);

            OutputCachedResults(DA, _cachedResults, detectedSpacing, _cachedInfo, physicalScene, logger);
        }

        // ══════════════════════════════════════════════════════════════
        // 输出缓存结果（提取为独立方法，避免重复代码）
        // ══════════════════════════════════════════════════════════════
        private void OutputCachedResults(IGH_DataAccess DA, List<VTKResult> results,
            double detectedSpacing, string infoText, Core.Scene physicalScene, ComponentLogger logger)
        {
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

            // 坐标偏移变换（VTK 内部坐标 → 物理世界坐标）
            logger.StepStart("坐标变换");
            string vtkPath = results.Count > 0 ? results[0].FilePath : "";
            string transformLog = ApplyCoordinateOffset(allPoints, vtkPath, physicalScene);
            string velocityUnitLog = ApplyVelocityMetadata(allVelocities, vtkPath);
            logger.StepEnd("坐标变换");

            DA.SetDataList(0, allPoints);
            DA.SetDataList(1, allVelocities);
            DA.SetDataList(2, allPressures);
            DA.SetDataList(3, allTimeSteps);

            // 追加风廓线诊断和速度统计到 Info
            string fullInfo = infoText;
            if (physicalScene != null && allPoints.Count > 0)
                fullInfo += AppendWindProfileInfo(physicalScene, allPoints);
            if (allVelocities.Count > 0)
                fullInfo += AppendVelocityStats(allVelocities);
            
            // 添加坐标变换日志
            fullInfo += "\n\n=== 坐标变换日志 ===\n" + transformLog;

            fullInfo += "\n\n=== Velocity unit metadata ===\n" + velocityUnitLog;

            DA.SetData(4, fullInfo);
            DA.SetData(5, detectedSpacing);
            
            // 输出详细日志
            logger.Finish();
            DA.SetData(6, logger.GetLog());
        }

        private string BuildInfoText(List<VTKResult> results, double detectedSpacing,
            double subsampleSpacing, int manualStep, int step)
        {
            int totalRaw = results.Sum(r => r.RawPointCount);
            int totalOut = results.Sum(r => r.Points?.Count ?? 0);
            double samplingRate = totalRaw > 0 ? 100.0 * totalOut / totalRaw : 100.0;

            string spacingStr = detectedSpacing > 0 ? $"{detectedSpacing:F3} m" : "未知";
            string stepDesc = manualStep > 0
                ? $"手动 Step={step}"
                : (subsampleSpacing > 0
                    ? $"自动 Step={step}（{subsampleSpacing:F1} m ÷ {spacingStr}）"
                    : "不采样");

            return $"读取了 {results.Count} 个 VTK 文件\n" +
                   $"原始点数:   {totalRaw:N0}\n" +
                   $"输出点数:   {totalOut:N0}  ({samplingRate:F1}%)\n" +
                   $"速度向量数: {results.Sum(r => r.Velocities?.Count ?? 0):N0}\n" +
                   $"网格间距:   {spacingStr}\n" +
                   $"采样策略:   {stepDesc}\n" +
                   $"时间步范围: {results.Min(r => r.TimeStep)} → {results.Max(r => r.TimeStep)}";
        }

        private string AppendWindProfileInfo(Core.Scene physicalScene, List<Point3d> allPoints)
        {
            string wpType = physicalScene.WindProfile.ToString();
            double wSpeed = physicalScene.WindSpeed;
            double zRef = physicalScene.ReferenceHeight;
            double z0 = physicalScene.RoughnessLength;
            double alpha = physicalScene.PowerLawAlpha;

            double zMin = allPoints.Min(p => p.Z);
            double zMax = allPoints.Max(p => p.Z);
            double uAtZmin = physicalScene.GetWindSpeedAtHeight(zMin);
            double uAtZmax = physicalScene.GetWindSpeedAtHeight(zMax);

            return $"\n风廓线设置: {wpType}\n" +
                   $"  参考风速: {wSpeed:F2} m/s @ {zRef:F1}m\n" +
                   $"  粗糙度:   z₀={z0:F2}m, α={alpha:F2}\n" +
                   $"  理论范围: {uAtZmin:F2} ~ {uAtZmax:F2} m/s\n" +
                   $"  (Z={zMin:F1}m ~ {zMax:F1}m)";
        }

        private string AppendVelocityStats(List<Vector3d> allVelocities)
        {
            double vMin = double.MaxValue, vMax = double.MinValue;
            double wMin = double.MaxValue, wMax = double.MinValue;
            double hMin = double.MaxValue, hMax = double.MinValue;

            foreach (var v in allVelocities)
            {
                double spd = v.Length;
                double hSpd = Math.Sqrt(v.X * v.X + v.Y * v.Y);
                if (spd < vMin) vMin = spd;
                if (spd > vMax) vMax = spd;
                if (v.Z < wMin) wMin = v.Z;
                if (v.Z > wMax) wMax = v.Z;
                if (hSpd < hMin) hMin = hSpd;
                if (hSpd > hMax) hMax = hSpd;
            }

            return $"\n速度统计:\n" +
                   $"  合速度:   {vMin:F4} ~ {vMax:F4} m/s\n" +
                   $"  水平风速: {hMin:F4} ~ {hMax:F4} m/s\n" +
                   $"  竖直风速: {wMin:F4} ~ {wMax:F4} m/s";
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
                // 添加详细日志，调试用
                System.Diagnostics.Debug.WriteLine($"[DEBUG] GenerateStructuredPoints: dimensions=({dimensions[0]},{dimensions[1]},{dimensions[2]}), origin=({origin[0]},{origin[1]},{origin[2]}), spacing=({spacing[0]},{spacing[1]},{spacing[2]}), step={step}");
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
                    long sectionBytes = (long)pointCount * bytesPerPoint;

                    // ── 3 分量 SCALARS（如 FluidX3D 的 SCALARS data float 3）视为向量 ──
                    bool treatAsVector = (section.Type == "SCALARS" && section.Components == 3);
                    if (!treatAsVector && section.Type == "SCALARS")
                    {
                        string nameLower = (section.Name ?? "").ToLowerInvariant();
                        if (nameLower == "velocity" || nameLower == "u" || nameLower == "data")
                            treatAsVector = true;
                    }

                    if (section.Type == "VECTORS" || treatAsVector)
                    {
                        // P0/P3 性能优化：一次性块读取替代逐点 Seek，速度提升 10-50 倍
                        // 典型场景：400 万点 × 12 字节 ≈ 48 MB，一次性顺序 IO
                        // P3 前瞻性优化：超过 1GB 使用 MemoryMappedFile 避免 2GB 内存墙
                        result.Velocities = new List<Vector3d>();

                        if (sampledIndices != null && result.Points != null)
                        {
                            // 结构化网格：一次性读取整个数据块，内存中按索引提取
                            // P3: 超过 1GB 使用内存映射文件
                            const long MEMORY_MAP_THRESHOLD = 1024L * 1024L * 1024L; // 1GB

                            if (sectionBytes > MEMORY_MAP_THRESHOLD)
                            {
                                // 使用 MemoryMappedFile 读取超大文件
                                result.Velocities = ReadLargeVectorSectionWithMemoryMap(
                                    vtkPath, filePos, sectionBytes, bytesPerPoint,
                                    section.DataType, sampledIndices);
                            }
                            else
                            {
                                // 标准 byte[] 读取（适用于大多数情况）
                                byte[] rawBlock = new byte[sectionBytes];
                                fs.Seek(filePos, SeekOrigin.Begin);
                                ReadFully(fs, rawBlock, 0, (int)sectionBytes);

                                result.Velocities = new List<Vector3d>(sampledIndices.Count);
                                foreach (int idx in sampledIndices)
                                {
                                    int byteOffset = idx * bytesPerPoint;
                                    double vx, vy, vz;
                                    if (section.DataType == "double")
                                    {
                                        vx = ReadBigEndianDouble(rawBlock, byteOffset);
                                        vy = ReadBigEndianDouble(rawBlock, byteOffset + 8);
                                        vz = ReadBigEndianDouble(rawBlock, byteOffset + 16);
                                    }
                                    else
                                    {
                                        vx = ReadBigEndianFloat(rawBlock, byteOffset);
                                        vy = ReadBigEndianFloat(rawBlock, byteOffset + 4);
                                        vz = ReadBigEndianFloat(rawBlock, byteOffset + 8);
                                    }
                                    result.Velocities.Add(new Vector3d(vx, vy, vz));
                                }
                            }
                        }
                        else
                        {
                            // 非结构化：线性步进采样，流式读取
                            // 对于大文件，也使用块读取策略
                            result.Velocities = new List<Vector3d>(pointCount / step + 1);
                            int pointsPerChunk = Math.Max(1024, 64 * 1024 / bytesPerPoint); // 约 64KB 每块
                            byte[] chunkBuffer = new byte[pointsPerChunk * bytesPerPoint];

                            for (int rawIdx = 0; rawIdx < pointCount; rawIdx += step)
                            {
                                long offset = filePos + (long)rawIdx * bytesPerPoint;
                                fs.Seek(offset, SeekOrigin.Begin);
                                int read = fs.Read(chunkBuffer, 0, bytesPerPoint);
                                if (read >= bytesPerPoint)
                                {
                                    double vx, vy, vz;
                                    if (section.DataType == "double")
                                    {
                                        vx = ReadBigEndianDouble(chunkBuffer, 0);
                                        vy = ReadBigEndianDouble(chunkBuffer, 8);
                                        vz = ReadBigEndianDouble(chunkBuffer, 16);
                                    }
                                    else
                                    {
                                        vx = ReadBigEndianFloat(chunkBuffer, 0);
                                        vy = ReadBigEndianFloat(chunkBuffer, 4);
                                        vz = ReadBigEndianFloat(chunkBuffer, 8);
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
                        // P0 性能优化：SCALARS 同样使用块读取策略
                        var values = new List<double>();

                        if (sampledIndices != null)
                        {
                            // 结构化网格：一次性读取整个数据块
                            byte[] rawBlock = new byte[sectionBytes];
                            fs.Seek(filePos, SeekOrigin.Begin);
                            ReadFully(fs, rawBlock, 0, (int)sectionBytes);

                            values = new List<double>(sampledIndices.Count);
                            foreach (int idx in sampledIndices)
                            {
                                int byteOffset = idx * bytesPerValue;
                                double val = section.DataType == "double"
                                    ? ReadBigEndianDouble(rawBlock, byteOffset)
                                    : ReadBigEndianFloat(rawBlock, byteOffset);
                                values.Add(val);
                            }
                        }
                        else
                        {
                            // 非结构化：线性步进采样
                            values = new List<double>(pointCount / step + 1);
                            byte[] buffer = new byte[bytesPerValue];
                            for (int rawIdx = 0; rawIdx < pointCount; rawIdx += step)
                            {
                                long offset = filePos + (long)rawIdx * bytesPerValue;
                                fs.Seek(offset, SeekOrigin.Begin);
                                int read = fs.Read(buffer, 0, bytesPerValue);
                                if (read >= bytesPerValue)
                                {
                                    double val = section.DataType == "double"
                                        ? ReadBigEndianDouble(buffer, 0)
                                        : ReadBigEndianFloat(buffer, 0);
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

        #region P3 前瞻性优化：MemoryMappedFile 读取超大文件（突破 2GB 内存墙）

        /// <summary>
        /// 使用 MemoryMappedFile 读取超大向量数据段（超过 1GB）
        /// </summary>
        private List<Vector3d> ReadLargeVectorSectionWithMemoryMap(
            string filePath,
            long fileOffset,
            long sectionBytes,
            int bytesPerPoint,
            string dataType,
            List<int> sampledIndices)
        {
            var velocities = new List<Vector3d>(sampledIndices.Count);
            bool isDouble = dataType == "double";
            int bytesPerValue = isDouble ? 8 : 4;

            using (var mmf = MemoryMappedFile.CreateFromFile(
                filePath, FileMode.Open, null, 0, MemoryMappedFileAccess.Read))
            using (var accessor = mmf.CreateViewAccessor(fileOffset, sectionBytes, MemoryMappedFileAccess.Read))
            {
                byte[] buffer = new byte[bytesPerPoint]; // 12 bytes for float3, 24 for double3

                foreach (int idx in sampledIndices)
                {
                    long byteOffset = (long)idx * bytesPerPoint;
                    accessor.ReadArray(byteOffset, buffer, 0, bytesPerPoint);

                    double vx, vy, vz;
                    if (isDouble)
                    {
                        vx = ReadBigEndianDouble(buffer, 0);
                        vy = ReadBigEndianDouble(buffer, 8);
                        vz = ReadBigEndianDouble(buffer, 16);
                    }
                    else
                    {
                        vx = ReadBigEndianFloat(buffer, 0);
                        vy = ReadBigEndianFloat(buffer, 4);
                        vz = ReadBigEndianFloat(buffer, 8);
                    }
                    velocities.Add(new Vector3d(vx, vy, vz));
                }
            }

            return velocities;
        }

        /// <summary>
        /// 使用 MemoryMappedFile 读取超大标量数据段（超过 1GB）
        /// </summary>
        private List<double> ReadLargeScalarSectionWithMemoryMap(
            string filePath,
            long fileOffset,
            long sectionBytes,
            int bytesPerValue,
            string dataType,
            List<int> sampledIndices)
        {
            var values = new List<double>(sampledIndices.Count);
            bool isDouble = dataType == "double";

            using (var mmf = MemoryMappedFile.CreateFromFile(
                filePath, FileMode.Open, null, 0, MemoryMappedFileAccess.Read))
            using (var accessor = mmf.CreateViewAccessor(fileOffset, sectionBytes, MemoryMappedFileAccess.Read))
            {
                byte[] buffer = new byte[bytesPerValue];

                foreach (int idx in sampledIndices)
                {
                    long byteOffset = (long)idx * bytesPerValue;
                    accessor.ReadArray(byteOffset, buffer, 0, bytesPerValue);

                    double val = isDouble
                        ? ReadBigEndianDouble(buffer, 0)
                        : ReadBigEndianFloat(buffer, 0);
                    values.Add(val);
                }
            }

            return values;
        }

        #endregion

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
        /// 根据 Scene 名称推算 Case 的 output 目录路径。
        /// 路径规则与 FluidX3DInterface.GenerateCase() 一致：
        ///   %TEMP%\CityLBM\{SanitizeName(sceneName)}\output
        /// </summary>
        private string GetCaseOutputDir(string sceneName)
        {
            if (string.IsNullOrEmpty(sceneName)) return null;

            // 与 FluidX3DInterface.SanitizeName 相同的逻辑
            string safeName = sceneName;
            foreach (char c in Path.GetInvalidFileNameChars())
                safeName = safeName.Replace(c, '_');

            string outputDir = Path.Combine(Path.GetTempPath(), "CityLBM", safeName, "output");
            if (Directory.Exists(outputDir) && Directory.GetFiles(outputDir, "*.vtk").Length > 0)
                return outputDir;

            return null;
        }

        /// <summary>
        /// 检查 VTK 输出目录是否有新文件或更新
        /// 如果有更新的文件，清除缓存强制重新读取
        /// </summary>
        private void CheckForNewVtkFiles(string outputDir)
        {
            if (!Directory.Exists(outputDir)) return;
            
            try
            {
                var vtkFiles = Directory.GetFiles(outputDir, "*.vtk");
                if (vtkFiles.Length == 0) return;
                
                // 找到最新的文件修改时间
                DateTime latestTime = DateTime.MinValue;
                foreach (var f in vtkFiles)
                {
                    DateTime writeTime = File.GetLastWriteTime(f);
                    if (writeTime > latestTime)
                        latestTime = writeTime;
                }
                
                // 如果比上次记录的时间新，清除缓存
                if (latestTime > _lastVtkWriteTime)
                {
                    _cachedResults = null;
                    _cachedKey = null;
                    AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, 
                        $"检测到新 VTK 数据 ({latestTime:HH:mm:ss})，重新读取...");
                }
                
                _lastVtkWriteTime = latestTime;
            }
            catch { }
        }

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

        /// <summary>
        /// 保证从 Stream 中读取足量的字节（处理部分读取的情况）
        /// </summary>
        private static void ReadFully(Stream s, byte[] buf, int off, int count)
        {
            while (count > 0)
            {
                int n = s.Read(buf, off, count);
                if (n <= 0) throw new EndOfStreamException("Unexpected end of stream");
                off += n;
                count -= n;
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
            // 支持 "u-000000500" 或 "result_500" 两种分隔符
            char[] separators = { '_', '-' };
            string[] parts = name.Split(separators);
            if (parts.Length > 1 && int.TryParse(parts[parts.Length - 1], out int ts))
                return ts;
            return 0;
        }

        private class CaseMetadataInfo
        {
            public int SchemaVersion { get; set; }
            public string CityLBMVersion { get; set; }
            public string WindProfile { get; set; }
            public double VelocityScaleLbmToMps { get; set; }
            public bool VtkReaderShouldApplyVelocityScale { get; set; }
            public bool CustomProfileHasK { get; set; }
            public string KColumnStatus { get; set; }
            public bool SyntheticTurbulentInletInjected { get; set; }
        }

        private string ApplyVelocityMetadata(List<Vector3d> velocities, string vtkPathOrDir)
        {
            CaseMetadataInfo metadata = LoadCaseMetadata(vtkPathOrDir);
            if (metadata == null)
                return "case_metadata.json not found. Velocity units are reported as parsed from VTK.";

            if (metadata.VtkReaderShouldApplyVelocityScale && velocities.Count > 0)
            {
                double scale = metadata.VelocityScaleLbmToMps;
                if (scale > 0.0 && !double.IsNaN(scale) && !double.IsInfinity(scale))
                {
                    for (int i = 0; i < velocities.Count; i++)
                        velocities[i] = velocities[i] * scale;
                    return $"Applied VelocityScaleLbmToMps={scale:F8} from case_metadata.json. " +
                           $"CityLBM={metadata.CityLBMVersion}, profile={metadata.WindProfile}, k={metadata.KColumnStatus}, " +
                           $"synthetic_turbulent_inlet={metadata.SyntheticTurbulentInletInjected}.";
                }
            }

            return $"No additional velocity scaling applied. CityLBM={metadata.CityLBMVersion}, " +
                   $"schema={metadata.SchemaVersion}, profile={metadata.WindProfile}, " +
                   $"k={metadata.KColumnStatus}, synthetic_turbulent_inlet={metadata.SyntheticTurbulentInletInjected}.";
        }

        private CaseMetadataInfo LoadCaseMetadata(string vtkPathOrDir)
        {
            string parent = string.IsNullOrEmpty(vtkPathOrDir) ? null : Path.GetDirectoryName(vtkPathOrDir);
            string grandParent = string.IsNullOrEmpty(parent) ? null : Path.GetDirectoryName(parent);
            string[] searchPaths = new[] { vtkPathOrDir, parent, grandParent };

            foreach (string dir in searchPaths)
            {
                if (string.IsNullOrEmpty(dir)) continue;
                string jsonFile = Path.Combine(dir, "case_metadata.json");
                if (!File.Exists(jsonFile)) continue;
                try
                {
                    string json = File.ReadAllText(jsonFile, System.Text.Encoding.UTF8);
                    return Newtonsoft.Json.JsonConvert.DeserializeObject<CaseMetadataInfo>(json);
                }
                catch { }
            }

            return null;
        }

        #region 坐标偏移变换

        /// <summary>
        /// domain_origin.json 中存储的物理域信息
        /// </summary>
        private class DomainOriginInfo
        {
            public double DomainOriginX { get; set; }
            public double DomainOriginY { get; set; }
            public double DomainOriginZ { get; set; }
            public double DomainMinX { get; set; }
            public double DomainMinY { get; set; }
            public double DomainMinZ { get; set; }
            public double DomainMaxX { get; set; }
            public double DomainMaxY { get; set; }
            public double DomainMaxZ { get; set; }
            public double Dx { get; set; }  // 物理网格间距（米/格子）
            public int Nx { get; set; }     // X方向格子数
            public int Ny { get; set; }     // Y方向格子数
            public int Nz { get; set; }     // Z方向格子数
        }

        /// <summary>
        /// 从 VTK 输出目录或 case 目录加载 domain_origin.json
        /// </summary>
        private DomainOriginInfo LoadDomainOrigin(string vtkPathOrDir)
        {
            string[] searchPaths = new[]
            {
                vtkPathOrDir,
                Path.GetDirectoryName(vtkPathOrDir),
            };

            foreach (string dir in searchPaths)
            {
                if (string.IsNullOrEmpty(dir)) continue;
                string jsonFile = Path.Combine(dir, "domain_origin.json");
                if (File.Exists(jsonFile))
                {
                    try
                    {
                        string json = File.ReadAllText(jsonFile, System.Text.Encoding.UTF8);
                        return Newtonsoft.Json.JsonConvert.DeserializeObject<DomainOriginInfo>(json);
                    }
                    catch { }
                }
            }
            return null;
        }

        /// <summary>
        /// 从 VTK 头部提取 ORIGIN 坐标
        /// </summary>
        private double[] ExtractVTKOrigin(string vtkPath)
        {
            try
            {
                byte[] buf = new byte[2048];
                int n;
                using (FileStream fs = new FileStream(vtkPath, FileMode.Open, FileAccess.Read))
                    n = fs.Read(buf, 0, buf.Length);

                string header = System.Text.Encoding.ASCII.GetString(buf, 0, n);
                string[] lines = header.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

                foreach (string line in lines)
                {
                    string t = line.Trim();
                    if (t.StartsWith("ORIGIN"))
                    {
                        string[] p = t.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        if (p.Length >= 4)
                        {
                            float ox, oy, oz;
                            if (float.TryParse(p[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out ox)
                                && float.TryParse(p[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out oy)
                                && float.TryParse(p[3], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out oz))
                            {
                                return new double[] { ox, oy, oz };
                            }
                        }
                    }
                }
            }
            catch { }
            return null;
        }

        /// <summary>
        /// 将 VTK 坐标映射回物理世界坐标（米）。
        /// 
        /// 注意：FluidX3D 的 write_device_to_vtk 输出的是格子坐标（索引），
        /// 需要乘以 Dx 转换为物理坐标，再加上物理域偏移。
        /// 
        /// 变换：物理坐标 = VTK格子坐标 × Dx + 物理域Min
        /// </summary>
        private string ApplyCoordinateOffset(List<Point3d> points, string vtkPathOrDir, Core.Scene physicalScene)
        {
            var logger = new ComponentLogger("CoordinateTransform");
            
            if (points.Count == 0) 
            {
                logger.Warning("没有点需要变换");
                return logger.GetLog();
            }

            // 提取 VTK ORIGIN（格子索引偏移）
            double[] vtkOrigin = ExtractVTKOrigin(vtkPathOrDir);
            if (vtkOrigin == null) 
            {
                logger.Error("无法从 VTK 文件提取 ORIGIN");
                return logger.GetLog();
            }
            
            // 添加详细日志，调试用
            System.Diagnostics.Debug.WriteLine($"[DEBUG] ApplyCoordinateOffset: vtkOrigin=({vtkOrigin[0]},{vtkOrigin[1]},{vtkOrigin[2]})");
            logger.Info($"[DEBUG] vtkOrigin=({vtkOrigin[0]:F1},{vtkOrigin[1]:F1},{vtkOrigin[2]:F1})");

            double physMinX = 0, physMinY = 0, physMinZ = 0;
            double dx = 1.0;
            bool hasPhysOrigin = false;
            string originSource = "未知";

            // 优先级 1：从 domain_origin.json 读取
            DomainOriginInfo domInfo = LoadDomainOrigin(vtkPathOrDir);
            if (domInfo != null)
            {
                physMinX = domInfo.DomainMinX;
                physMinY = domInfo.DomainMinY;
                physMinZ = domInfo.DomainMinZ;
                dx = domInfo.Dx;
                hasPhysOrigin = true;
                originSource = "domain_origin.json";
                
                logger.Info("从 domain_origin.json 读取物理域信息");
                logger.DataSummary("物理域范围", new Dictionary<string, object> {
                    ["Min"] = $"({domInfo.DomainMinX:F2}, {domInfo.DomainMinY:F2}, {domInfo.DomainMinZ:F2})",
                    ["Max"] = $"({domInfo.DomainMaxX:F2}, {domInfo.DomainMaxY:F2}, {domInfo.DomainMaxZ:F2})",
                    ["Dx"] = domInfo.Dx,
                    ["Nx/Ny/Nz"] = $"{domInfo.Nx}/{domInfo.Ny}/{domInfo.Nz}"
                });
            }
            else
            {
                logger.Warning("未找到 domain_origin.json，尝试从 Scene 获取");
                // 调试：输出搜索路径
                string[] searchPaths = new[] { vtkPathOrDir, System.IO.Path.GetDirectoryName(vtkPathOrDir) };
                foreach (var path in searchPaths)
                {
                    if (!string.IsNullOrEmpty(path))
                    {
                        string jsonFile = System.IO.Path.Combine(path, "domain_origin.json");
                        logger.Info($"搜索路径: {jsonFile}, 存在: {System.IO.File.Exists(jsonFile)}");
                    }
                }
            }

            // 优先级 2：从 Scene 对象获取
            if (!hasPhysOrigin && physicalScene != null)
            {
                try
                {
                    BoundingBox physDomain = physicalScene.GetSimulationDomain();
                    physMinX = physDomain.Min.X;
                    physMinY = physDomain.Min.Y;
                    physMinZ = physDomain.Min.Z;
                    
                    // Scene 对象不提供 Dx，使用 domain_origin.json 中的值
                    // dx 已经在前面从 domInfo 获取
                    
                    hasPhysOrigin = true;
                    originSource = "Scene对象";
                    
                    logger.Info("从 Scene 对象获取物理域信息");
                    logger.Geometry("物理域", physDomain);
                }
                catch (Exception ex)
                {
                    logger.Warning($"从 Scene 获取域信息失败: {ex.Message}");
                }
            }

            if (!hasPhysOrigin) 
            {
                logger.Error("无法获取物理域原点信息");
                return logger.GetLog();
            }

            // 计算物理域最大值
            double physMaxX = physMinX + dx * (domInfo?.Nx ?? 100);
            double physMaxY = physMinY + dx * (domInfo?.Ny ?? 100);
            double physMaxZ = physMinZ + dx * (domInfo?.Nz ?? 100);

            // 判断 VTK 输出的是物理坐标还是格子坐标
            // 方法：检查 VTK 数据范围是否与物理域范围匹配
            // 先计算 VTK 数据的实际范围
            double vtkMinX = double.MaxValue, vtkMaxX = double.MinValue;
            double vtkMinY = double.MaxValue, vtkMaxY = double.MinValue;
            double vtkMinZ = double.MaxValue, vtkMaxZ = double.MinValue;
            foreach (var pt in points)
            {
                if (pt.X < vtkMinX) vtkMinX = pt.X;
                if (pt.X > vtkMaxX) vtkMaxX = pt.X;
                if (pt.Y < vtkMinY) vtkMinY = pt.Y;
                if (pt.Y > vtkMaxY) vtkMaxY = pt.Y;
                if (pt.Z < vtkMinZ) vtkMinZ = pt.Z;
                if (pt.Z > vtkMaxZ) vtkMaxZ = pt.Z;
            }
            double vtkRangeX = vtkMaxX - vtkMinX;
            double vtkRangeY = vtkMaxY - vtkMinY;
            double vtkRangeZ = vtkMaxZ - vtkMinZ;
            double physRangeX = physMaxX - physMinX;
            double physRangeY = physMaxY - physMinY;
            double physRangeZ = physMaxZ - physMinZ;
            
            // 如果 VTK 数据范围与物理域范围接近（误差在 20% 以内），则认为是物理坐标
            // 否则认为是格子坐标
            bool vtkOutputsPhysicalCoords = 
                (Math.Abs(vtkRangeX - physRangeX) / physRangeX < 0.2) &&
                (Math.Abs(vtkRangeY - physRangeY) / physRangeY < 0.2) &&
                (Math.Abs(vtkRangeZ - physRangeZ) / physRangeZ < 0.2);
            
            logger.Info($"VTK坐标类型检测: VTK范围=({vtkRangeX:F1},{vtkRangeY:F1},{vtkRangeZ:F1}), 物理域范围=({physRangeX:F1},{physRangeY:F1},{physRangeZ:F1}), 是物理坐标={vtkOutputsPhysicalCoords}");
            
            if (vtkOutputsPhysicalCoords)
            {
                // VTK 已输出物理坐标，只需要平移到正确的物理域原点
                // 偏移量 = 物理域Min - VTK原点
                double offsetX = physMinX - vtkOrigin[0];
                double offsetY = physMinY - vtkOrigin[1];
                double offsetZ = physMinZ - vtkOrigin[2];
                
                logger.DataSummary("坐标变换参数", new Dictionary<string, object> {
                    ["变换类型"] = "仅平移（VTK已输出物理坐标）",
                    ["Domain Dx"] = dx,
                    ["偏移X"] = offsetX,
                    ["偏移Y"] = offsetY,
                    ["偏移Z"] = offsetZ,
                    ["VTK原点"] = $"({vtkOrigin[0]:F2}, {vtkOrigin[1]:F2}, {vtkOrigin[2]:F2})",
                    ["物理域Min"] = $"({physMinX:F2}, {physMinY:F2}, {physMinZ:F2})",
                    ["数据来源"] = originSource
                });

                // 记录变换前的范围
                double minX = double.MaxValue, maxX = double.MinValue;
                double minY = double.MaxValue, maxY = double.MinValue;
                double minZ = double.MaxValue, maxZ = double.MinValue;
                foreach (var pt in points)
                {
                    if (pt.X < minX) minX = pt.X;
                    if (pt.X > maxX) maxX = pt.X;
                    if (pt.Y < minY) minY = pt.Y;
                    if (pt.Y > maxY) maxY = pt.Y;
                    if (pt.Z < minZ) minZ = pt.Z;
                    if (pt.Z > maxZ) maxZ = pt.Z;
                }
                logger.Info($"变换前范围(物理坐标): X[{minX:F2}, {maxX:F2}], Y[{minY:F2}, {maxY:F2}], Z[{minZ:F2}, {maxZ:F2}]");

                // 仅应用平移变换
                for (int i = 0; i < points.Count; i++)
                {
                    points[i] = new Point3d(
                        points[i].X + offsetX,
                        points[i].Y + offsetY,
                        points[i].Z + offsetZ);
                }
            }
            else
            {
                // VTK 输出的是格子坐标，需要缩放+平移
                // 物理坐标 = VTK格子坐标 × Dx + (物理域Min - VTK_ORIGIN × Dx)
                double offsetX = physMinX - vtkOrigin[0] * dx;
                double offsetY = physMinY - vtkOrigin[1] * dx;
                double offsetZ = physMinZ - vtkOrigin[2] * dx;
                
                logger.DataSummary("坐标变换参数", new Dictionary<string, object> {
                    ["变换类型"] = "缩放+平移（VTK输出格子坐标）",
                    ["Dx"] = dx,
                    ["VTK原点(格子索引)"] = $"({vtkOrigin[0]:F2}, {vtkOrigin[1]:F2}, {vtkOrigin[2]:F2})",
                    ["物理域Min"] = $"({physMinX:F2}, {physMinY:F2}, {physMinZ:F2})",
                    ["偏移量"] = $"({offsetX:F2}, {offsetY:F2}, {offsetZ:F2})",
                    ["数据来源"] = originSource
                });

                // 记录变换前的范围
                double minX = double.MaxValue, maxX = double.MinValue;
                double minY = double.MaxValue, maxY = double.MinValue;
                double minZ = double.MaxValue, maxZ = double.MinValue;
                foreach (var pt in points)
                {
                    if (pt.X < minX) minX = pt.X;
                    if (pt.X > maxX) maxX = pt.X;
                    if (pt.Y < minY) minY = pt.Y;
                    if (pt.Y > maxY) maxY = pt.Y;
                    if (pt.Z < minZ) minZ = pt.Z;
                    if (pt.Z > maxZ) maxZ = pt.Z;
                }
                logger.Info($"变换前范围(格子坐标): X[{minX:F2}, {maxX:F2}], Y[{minY:F2}, {maxY:F2}], Z[{minZ:F2}, {maxZ:F2}]");

                // 应用缩放和平移变换（VTK 格子坐标 → 物理坐标）
                for (int i = 0; i < points.Count; i++)
                {
                    points[i] = new Point3d(
                        points[i].X * dx + offsetX,
                        points[i].Y * dx + offsetY,
                        points[i].Z * dx + offsetZ);
                }
            }

            // 记录变换后的范围
            double finalMinX = double.MaxValue, finalMaxX = double.MinValue;
            double finalMinY = double.MaxValue, finalMaxY = double.MinValue;
            double finalMinZ = double.MaxValue, finalMaxZ = double.MinValue;
            foreach (var pt in points)
            {
                if (pt.X < finalMinX) finalMinX = pt.X;
                if (pt.X > finalMaxX) finalMaxX = pt.X;
                if (pt.Y < finalMinY) finalMinY = pt.Y;
                if (pt.Y > finalMaxY) finalMaxY = pt.Y;
                if (pt.Z < finalMinZ) finalMinZ = pt.Z;
                if (pt.Z > finalMaxZ) finalMaxZ = pt.Z;
            }
            logger.Info($"变换后范围(物理坐标): X[{finalMinX:F2}, {finalMaxX:F2}], Y[{finalMinY:F2}, {finalMaxY:F2}], Z[{finalMinZ:F2}, {finalMaxZ:F2}]");
            logger.Range("X范围", finalMinX, finalMaxX);
            logger.Range("Y范围", finalMinY, finalMaxY);
            logger.Range("Z范围", finalMinZ, finalMaxZ);

            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                $"坐标变换完成，数据范围: X[{finalMinX:F1},{finalMaxX:F1}], Y[{finalMinY:F1},{finalMaxY:F1}], Z[{finalMinZ:F1},{finalMaxZ:F1}]");
            
            logger.Finish();
            return logger.GetLog();
        }

        #endregion

        protected override Bitmap Icon => IconLoader.Load("ReadVTK.png");

        public override Guid ComponentGuid
            => new Guid("A3B7C9D2-8E4F-4A5B-9C6D-7E8F9A0B1C2D");
    }
}
