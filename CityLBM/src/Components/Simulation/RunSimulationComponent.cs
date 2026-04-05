using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Text;
using System.Threading;
using Grasshopper.Kernel;
using CityLBM.Core;
using CityLBM.Solver;
using CityLBM.Utils;

namespace CityLBM.Components.Simulation
{
    /// <summary>
    /// 运行模拟组件（异步后台版）
    ///
    /// 工作模式：
    ///   Mode 0 — 仅生成 Case 文件（Generate Only）
    ///     输出 Case 目录路径和手动操作指南，用户自行编译运行 FluidX3D
    ///
    ///   Mode 1 — 自动部署 + 编译 + 运行（全自动，同步阻塞，适合短流程）
    ///     需要提供 FluidX3D 源码路径，自动完成全流程
    ///
    ///   Mode 2 — 仅部署到 FluidX3D 源码（不编译）
    ///
    ///   Mode 3 — 全自动后台运行（异步，不弹窗，GH 内实时进度）【推荐】
    ///     将编译和运行放到后台线程，GH 组件显示实时进度（0-100%）
    ///     不弹出任何窗口，完全在后台执行，可随时通过 Cancel 取消
    /// </summary>
    public class RunSimulationComponent : GH_Component
    {
        // ── 异步状态 ──────────────────────────────────────────────────────
        private CancellationTokenSource _cts;           // 当前运行的取消令牌
        private SolverResult _asyncResult;             // 最终结果
        private bool _asyncRunning;                    // 是否正在运行
        private int  _asyncProgress;                   // 进度 0-100
        private readonly List<string> _asyncLog = new List<string>();  // 实时日志
        private readonly object _logLock = new object();

        // ── 定时刷新（GH 组件不能直接跨线程刷新，需 ExpireSolution）─────
        private System.Timers.Timer _refreshTimer;

        // ── GH 加载保护 ───────────────────────────────────────────────────
        private DateTime _componentCreatedAt = DateTime.Now;  // 组件创建时间
        private static readonly TimeSpan GH_LOAD_GRACE_PERIOD = TimeSpan.FromSeconds(3);  // GH 加载宽限期

        public RunSimulationComponent()
            : base("Run Simulation", "Sim",
                   "生成 FluidX3D Case 文件 / 自动编译运行模拟\n" +
                   "Mode 3【推荐】：后台异步运行，GH 内实时显示进度，不弹窗",
                   "CityLBM", "Simulation")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            // 必填
            pManager.AddGenericParameter("Scene", "S", "CityLBM 场景对象", GH_ParamAccess.item);
            pManager.AddGenericParameter("Grid", "G", "笛卡尔网格", GH_ParamAccess.item);

            // 可选：FluidX3D 源码路径
            pManager.AddTextParameter("FluidX3D Path", "FX3D",
                "FluidX3D 源码根目录（包含 FluidX3D.sln 或 Makefile）\n" +
                "留空则自动检测常见安装位置。",
                GH_ParamAccess.item, "");

            // 模式
            pManager.AddIntegerParameter("Mode", "M",
                "运行模式：\n" +
                "  0 = 生成 Case 文件（若提供 FX3D 路径则自动部署 + 生成一键脚本）\n" +
                "  1 = 自动部署 + 编译 + 运行（同步，GH 界面暂时无响应）\n" +
                "  2 = 仅部署到 FluidX3D 源码（不编译）\n" +
                "  3 = 全自动后台运行【推荐】（异步，不弹窗，GH 内实时显示进度）",
                GH_ParamAccess.item, 3);

            // 物理参数
            pManager.AddNumberParameter("Wind Speed", "WS", "入口风速 (m/s)，0 = 使用 Scene 默认", GH_ParamAccess.item, 0.0);
            pManager.AddNumberParameter("Viscosity", "nu", "运动粘度 (m²/s)", GH_ParamAccess.item, 1.5e-5);
            pManager.AddIntegerParameter("Time Steps", "T", "总模拟步数（推荐 1000~3000，稳态风场不需要太多步）", GH_ParamAccess.item, 2000);
            pManager.AddIntegerParameter("Save Interval", "SI", "VTK 输出间隔（步数，增大可减少磁盘 IO）", GH_ParamAccess.item, 1000);

            // 触发 / 取消
            pManager.AddBooleanParameter("Run", "Run", "True = 开始；若已运行中则重新启动", GH_ParamAccess.item, false);
            pManager.AddBooleanParameter("Cancel", "Stop", "True = 取消当前后台运行", GH_ParamAccess.item, false);

            // 全部可选（除 Scene 和 Grid）
            for (int i = 2; i <= 9; i++) pManager[i].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Case Dir",    "Dir",      "Case 文件目录",         GH_ParamAccess.item);
            pManager.AddTextParameter("Output Dir",  "Out",      "VTK 输出目录",          GH_ParamAccess.item);
            pManager.AddBooleanParameter("Success",  "OK",       "操作是否成功",          GH_ParamAccess.item);
            pManager.AddTextParameter("Status",      "Status",   "当前状态信息",          GH_ParamAccess.item);
            pManager.AddIntegerParameter("Progress", "Pct",      "进度百分比（0-100）",   GH_ParamAccess.item);
            pManager.AddTextParameter("Log",         "Log",      "实时运行日志",          GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // ── 读取参数 ────────────────────────────────────────────────
            GH_Scene ghScene = null;
            GH_CartesianGrid ghGrid = null;
            string fluidX3DPath = "";
            int mode = 3;
            double windSpeedOverride = 0.0;
            double viscosity = 1.5e-5;
            int timeSteps = 5000;
            int saveInterval = 500;
            bool run = false;
            bool cancel = false;

            if (!DA.GetData(0, ref ghScene)) return;
            if (!DA.GetData(1, ref ghGrid)) return;
            DA.GetData(2, ref fluidX3DPath);
            DA.GetData(3, ref mode);
            DA.GetData(4, ref windSpeedOverride);
            DA.GetData(5, ref viscosity);
            DA.GetData(6, ref timeSteps);
            DA.GetData(7, ref saveInterval);
            DA.GetData(8, ref run);
            DA.GetData(9, ref cancel);

            // ── GH 加载期保护 ────────────────────────────────────────────
            // 使用宽限期策略：组件创建后 3 秒内认为 GH 可能还在加载
            // 这比检查 SolutionState 更可靠，因为后者在 GH 加载完成后仍可能返回 Process
            if (DateTime.Now - _componentCreatedAt < GH_LOAD_GRACE_PERIOD)
            {
                double waitSec = (GH_LOAD_GRACE_PERIOD - (DateTime.Now - _componentCreatedAt)).TotalSeconds;
                DA.SetData(0, "");           // Case Dir
                DA.SetData(1, "");           // Output Dir
                DA.SetData(2, false);        // Success
                DA.SetData(3, $"[加载中] GH 初始化中，请等待 {waitSec:F1} 秒后再运行...");
                DA.SetData(4, 0);            // Progress
                DA.SetData(5, "");           // Log
                // 触发一次刷新，让状态更新
                ScheduleRefresh(500);
                return;
            }

            // ── 取消操作 ─────────────────────────────────────────────────
            if (cancel && _asyncRunning)
            {
                _cts?.Cancel();
                // 注意：_asyncRunning 会在 completionCallback 中被重置为 false
                // 这里不能立即重置，否则 GH 刷新时可能进入 Mode3 启动逻辑
                DA.SetData(0, "");
                DA.SetData(1, "");
                DA.SetData(2, false);
                DA.SetData(3, "正在取消...");
                DA.SetData(4, _asyncProgress);
                DA.SetData(5, GetCurrentLog());
                return;
            }

            // ── 如果后台任务正在执行，无论 run 是否为 true，优先输出实时进度 ──
            // 这避免了 run=true 时反复进入 Mode3 启动逻辑的问题
            if (_asyncRunning)
            {
                string progressBar = GetProgressBar(_asyncProgress);
                string stage = GetProgressStage(_asyncProgress);
                string statusMsg = $"[{stage}]\n{progressBar} {_asyncProgress}%\n后台编译/运行中，请等待...";
                
                DA.SetData(0, "");
                DA.SetData(1, "");
                DA.SetData(2, false);
                DA.SetData(3, statusMsg);
                DA.SetData(4, _asyncProgress);
                DA.SetData(5, GetCurrentLog());
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"{stage} {_asyncProgress}%");
                return;
            }

            // ── 如果已有完成的异步结果且 run 仍为 true，保持输出结果 ──
            // 这防止模拟完成后 GH 重新计算导致结果丢失
            if (_asyncResult != null && _asyncResult.Success && run)
            {
                OutputAsyncResult(DA, _asyncResult);
                return;
            }

            // ── 未触发 ───────────────────────────────────────────────────
            if (!run)
            {
                if (_asyncResult != null)
                {
                    // 输出已完成的结果
                    OutputAsyncResult(DA, _asyncResult);
                }
                else
                {
                    DA.SetData(2, false);
                    DA.SetData(3, "将 Run 设为 True 以触发。Mode 3 = 后台运行（推荐，不弹窗）。");
                    DA.SetData(4, 0);
                }
                return;
            }

            // ── 验证输入 ─────────────────────────────────────────────────
            if (ghScene?.Value == null)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "场景对象无效");
                return;
            }
            if (ghGrid?.Value == null)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "网格对象无效");
                return;
            }

            Scene scene = ghScene.Value;
            CartesianGrid grid = ghGrid.Value;
            if (windSpeedOverride > 0.0) scene.WindSpeed = windSpeedOverride;

            var settings = new SimulationSettings
            {
                Viscosity = viscosity,
                TimeSteps = timeSteps,
                SaveInterval = saveInterval
            };
            settings.SetInletVelocity(scene.WindDirection, scene.WindSpeed);

            var solver = new FluidX3DInterface(fluidX3DPath);
            mode = Math.Max(0, Math.Min(3, mode));

            switch (mode)
            {
                case 0:
                    RunMode0_GenerateOnly(DA, solver, scene, grid, settings);
                    break;
                case 1:
                    RunMode1_FullAuto(DA, solver, scene, grid, settings);
                    break;
                case 2:
                    RunMode2_DeployOnly(DA, solver, scene, grid, settings);
                    break;
                case 3:
                    RunMode3_AsyncBackground(DA, solver, scene, grid, settings);
                    break;
            }
        }

        // ────────────────────────────────────────────────────────────────
        // Mode 0: 生成 Case 文件
        // ────────────────────────────────────────────────────────────────
        private void RunMode0_GenerateOnly(IGH_DataAccess DA,
            FluidX3DInterface solver, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            var result = solver.GenerateCaseOnly(scene, grid, settings);

            DA.SetData(0, result.CaseDirectory ?? "");
            DA.SetData(1, result.Success ? Path.Combine(result.CaseDirectory ?? "", "output") : "");
            DA.SetData(2, result.Success);
            DA.SetData(3, result.Success ? result.Instructions : $"生成失败：{result.ErrorMessage}");
            DA.SetData(4, result.Success ? 100 : 0);

            if (result.Success)
            {
                string tip = result.AutoDeployed
                    ? "[OK] Case 文件已生成并自动部署到 FluidX3D。双击 run_citylbm.bat 一键完成编译运行。"
                    : "[OK] Case 文件已生成，请按照输出说明手动部署到 FluidX3D。";
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, tip);
            }
            else
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, result.ErrorMessage);
            }
        }

        // ────────────────────────────────────────────────────────────────
        // Mode 1: 自动部署 + 编译 + 运行（同步，会阻塞 GH 界面）
        // ────────────────────────────────────────────────────────────────
        private void RunMode1_FullAuto(IGH_DataAccess DA,
            FluidX3DInterface solver, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            if (string.IsNullOrWhiteSpace(solver.FluidX3DPath))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "Mode 1 需要设置 FluidX3D 源码路径（FX3D 输入），或确保 FluidX3D 安装在常见位置以便自动检测。\n建议改用 Mode 3（后台异步，不阻塞界面）。");
                DA.SetData(2, false);
                DA.SetData(3, "错误：未找到 FluidX3D 路径。请设置 FX3D 输入或安装到默认位置。");
                return;
            }
            
            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"使用 FluidX3D 路径: {solver.FluidX3DPath}");

            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                "开始完整流程（同步模式）：生成 → 部署 → 编译 → 运行...\n提示：使用 Mode 3 可避免界面卡顿。");

            var result = solver.GenerateDeployBuildRun(scene, grid, settings);

            DA.SetData(0, result.CaseDirectory ?? "");
            DA.SetData(1, result.OutputDirectory ?? "");
            DA.SetData(2, result.Success);
            DA.SetData(4, result.Success ? 100 : 0);

            string summary = result.Success
                ? $"[OK] 模拟完成！耗时: {result.Duration.TotalMinutes:F1} 分钟\nVTK 输出: {result.OutputDirectory}"
                : $"[X] 失败: {result.ErrorMessage}";

            DA.SetData(3, summary);
            DA.SetData(5, result.Log);

            if (!result.Success)
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, result.ErrorMessage ?? "未知错误");
        }

        // ────────────────────────────────────────────────────────────────
        // Mode 2: 仅部署
        // ────────────────────────────────────────────────────────────────
        private void RunMode2_DeployOnly(IGH_DataAccess DA,
            FluidX3DInterface solver, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            if (string.IsNullOrWhiteSpace(solver.FluidX3DPath))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Mode 2 需要设置 FluidX3D 源码路径（FX3D 输入），或确保 FluidX3D 安装在常见位置以便自动检测。");
                DA.SetData(2, false);
                DA.SetData(3, "错误：未找到 FluidX3D 路径。请设置 FX3D 输入或安装到默认位置。");
                return;
            }
            
            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"使用 FluidX3D 路径: {solver.FluidX3DPath}");

            string caseDir;
            try { caseDir = solver.GenerateCase(scene, grid, settings); }
            catch (Exception ex)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, $"生成 Case 失败: {ex.Message}");
                DA.SetData(2, false); DA.SetData(3, $"生成 Case 失败: {ex.Message}");
                return;
            }

            var deployResult = solver.DeployToFluidX3D(caseDir);
            DA.SetData(0, caseDir);
            DA.SetData(1, Path.Combine(solver.FluidX3DPath, "output"));
            DA.SetData(2, deployResult.Success);
            DA.SetData(4, deployResult.Success ? 100 : 0);

            if (deployResult.Success)
            {
                string msg = deployResult.Message + "\n\n文件已部署，请手动编译并运行 FluidX3D：\n" +
                             "  Visual Studio: Build → Release x64\n" +
                             "  命令行: msbuild FluidX3D.sln /p:Configuration=Release /p:PlatformToolset=v143";
                DA.SetData(3, msg);
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, "[OK] 已部署到 FluidX3D 源码，请手动编译运行。");
            }
            else
            {
                DA.SetData(3, $"部署失败：{deployResult.ErrorMessage}");
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, deployResult.ErrorMessage);
            }
        }

        // ────────────────────────────────────────────────────────────────
        // Mode 3: 全自动后台异步运行【推荐】
        // 后台编译 + 后台运行，GH 内实时显示进度，不弹出任何窗口
        // ────────────────────────────────────────────────────────────────
        private void RunMode3_AsyncBackground(IGH_DataAccess DA,
            FluidX3DInterface solver, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            if (string.IsNullOrWhiteSpace(solver.FluidX3DPath))
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    "Mode 3 需要设置 FluidX3D 源码路径（FX3D 输入），或确保 FluidX3D 安装在常见位置以便自动检测。");
                DA.SetData(2, false);
                DA.SetData(3, "错误：未找到 FluidX3D 路径。请设置 FX3D 输入或安装到默认位置。");
                return;
            }
            
            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"使用 FluidX3D 路径: {solver.FluidX3DPath}");

            // 双重保险：正常不应该到这里（已在 SolveInstance 顶部提前 return）
            if (_asyncRunning)
            {
                string bar = GetProgressBar(_asyncProgress);
                string stg = GetProgressStage(_asyncProgress);
                DA.SetData(3, $"[{stg}]\n{bar} {_asyncProgress}%\n后台任务运行中...");
                DA.SetData(4, _asyncProgress);
                DA.SetData(5, GetCurrentLog());
                return;
            }

            // 重置状态
            _asyncResult = null;
            _asyncRunning = true;
            _asyncProgress = 0;
            lock (_logLock) { _asyncLog.Clear(); }
            StopRefreshTimer();

            // 启动定时刷新（每 2 秒刷新一次 GH 组件）
            StartRefreshTimer();

            // 启动后台任务
            _cts = solver.StartAsyncRun(
                scene, grid, settings,
                progressCallback: (msg, pct) =>
                {
                    lock (_logLock)
                    {
                        _asyncLog.Add(msg);
                        // 只保留最近 200 行日志，防止内存膨胀
                        if (_asyncLog.Count > 200) _asyncLog.RemoveAt(0);
                    }
                    if (pct >= 0) Interlocked.Exchange(ref _asyncProgress, pct);
                },
                completionCallback: result =>
                {
                    _asyncResult = result;
                    _asyncRunning = false;
                    StopRefreshTimer();
                    // 触发最后一次刷新以输出最终结果
                    TriggerGHRefresh();
                }
            );

            // 立即输出"已启动"状态
            DA.SetData(3, "[启动] 后台运行已启动，编译中...");
            DA.SetData(4, 0);
            DA.SetData(5, "正在初始化...");

            AddRuntimeMessage(GH_RuntimeMessageLevel.Remark,
                "[Mode 3] 后台运行已启动，GH 组件将每 2 秒自动刷新进度。\n" +
                "编译和求解完全在后台执行，不弹出任何窗口。\n" +
                "将 Cancel 设为 True 可随时中止运行。");
        }

        // ────────────────────────────────────────────────────────────────
        // 输出异步结果（后台任务完成后调用）
        // ────────────────────────────────────────────────────────────────
        private void OutputAsyncResult(IGH_DataAccess DA, SolverResult result)
        {
            DA.SetData(0, result.CaseDirectory ?? "");
            DA.SetData(1, result.OutputDirectory ?? "");
            DA.SetData(2, result.Success);
            DA.SetData(4, result.Success ? 100 : 0);

            string status = result.Success
                ? $"[OK] 模拟完成！耗时: {result.Duration.TotalMinutes:F1} 分钟\nVTK: {result.OutputDirectory}"
                : $"[X] 失败: {result.ErrorMessage}";

            DA.SetData(3, status);
            DA.SetData(5, GetCurrentLog());

            if (result.Success)
                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"[OK] 模拟完成！耗时 {result.Duration.TotalMinutes:F1} 分钟");
            else
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, result.ErrorMessage ?? "模拟失败");
        }

        // ────────────────────────────────────────────────────────────────
        // 辅助：日志 / 定时刷新
        // ────────────────────────────────────────────────────────────────
        private string GetCurrentLog()
        {
            lock (_logLock)
            {
                // 添加时间戳和行号，确保每次返回的字符串都是新的对象
                // 这样 Panel 会检测到变化并自动刷新
                var sb = new StringBuilder();
                for (int i = 0; i < _asyncLog.Count; i++)
                {
                    sb.AppendLine($"[{i + 1:D3}] {_asyncLog[i]}");
                }
                return sb.ToString();
            }
        }

        /// <summary>
        /// 生成可视化进度条字符串
        /// </summary>
        private string GetProgressBar(int progress)
        {
            const int barWidth = 20;
            int filled = (int)Math.Round(progress / 100.0 * barWidth);
            int empty = barWidth - filled;
            
            string bar = new string('█', filled) + new string('░', empty);
            return $"[{bar}]";
        }

        /// <summary>
        /// 根据进度百分比返回当前阶段描述
        /// </summary>
        private string GetProgressStage(int progress)
        {
            if (progress == 0) return "等待开始";
            if (progress < 10) return "准备文件";
            if (progress < 20) return "生成Case";
            if (progress < 30) return "部署文件";
            if (progress < 50) return "编译中...";
            if (progress < 60) return "编译完成";
            if (progress < 70) return "启动求解器";
            if (progress < 95) return "模拟运行中";
            if (progress < 100) return "收尾处理";
            return "完成";
        }

        private void StartRefreshTimer()
        {
            _refreshTimer = new System.Timers.Timer(2000);  // 每 2 秒刷新
            _refreshTimer.Elapsed += (s, e) => TriggerGHRefresh();
            _refreshTimer.AutoReset = true;
            _refreshTimer.Start();
        }

        private void StopRefreshTimer()
        {
            if (_refreshTimer != null)
            {
                _refreshTimer.Stop();
                _refreshTimer.Dispose();
                _refreshTimer = null;
            }
        }

        /// <summary>
        /// 延迟调度一次刷新（用于加载期保护等非定时场景）
        /// </summary>
        private void ScheduleRefresh(int delayMs)
        {
            var timer = new System.Timers.Timer(delayMs);
            timer.Elapsed += (s, e) =>
            {
                timer.Dispose();
                TriggerGHRefresh();
            };
            timer.AutoReset = false;
            timer.Start();
        }

        private void TriggerGHRefresh()
        {
            // 安全刷新：使用 InvokeOnUiThread 在 UI 线程标记组件过期
            // 宽限期保护已在 SolveInstance 中处理，这里不需要额外检查
            try
            {
                Rhino.RhinoApp.InvokeOnUiThread((Action)(() =>
                {
                    try
                    {
                        // 标记自身过期
                        ExpireSolution(false); // false = 非阻塞，仅标记过期
                        
                        // 强制刷新下游组件（包括 Panel）
                        // 这样连接 Log/Status 的 Panel 会自动更新，无需手动触发
                        var doc = OnPingDocument();
                        if (doc != null)
                        {
                            foreach (var param in Params.Output)
                            {
                                foreach (var recipient in param.Recipients)
                                {
                                    if (recipient.Attributes?.Parent is IGH_Component recipientComponent)
                                    {
                                        recipientComponent.ExpireSolution(false);
                                    }
                                    else if (recipient.Attributes?.Parent is IGH_Param recipientParam)
                                    {
                                        recipientParam.ExpireSolution(false);
                                    }
                                }
                            }
                        }
                    }
                    catch { /* 忽略所有边界情况 */ }
                }));
            }
            catch { /* 忽略所有边界情况 */ }
        }

        public override void RemovedFromDocument(GH_Document document)
        {
            // 组件从文档移除时停止定时器，防止泄漏
            StopRefreshTimer();
            _cts?.Cancel();
            base.RemovedFromDocument(document);
        }

        // ────────────────────────────────────────────────────────────────
        // 组件元信息
        // ────────────────────────────────────────────────────────────────
        protected override Bitmap Icon => null;

        public override Guid ComponentGuid
            => new Guid("F9A5B3E2-8C4D-4F7A-9B6E-2D5C7A8B9F1D");
    }
}
