using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Rhino.Geometry;
using CityLBM.Core;

namespace CityLBM.Solver
{
    /// <summary>
    /// FluidX3D 求解器接口（正确集成版本）
    ///
    /// FluidX3D 工作原理：
    ///   它不是配置文件驱动的求解器，而是一个需要重新编译的 C++ 程序。
    ///   正确流程：修改 src/setup.cpp 和 src/defines.hpp → 重新编译 → 运行 FluidX3D.exe
    ///
    /// 集成流程：
    ///   1. GenerateCase()  — 在临时目录生成 setup.cpp / defines.hpp / buildings.stl
    ///   2. DeployToFluidX3D() — 将生成文件覆盖到 FluidX3D/src/ 目录
    ///   3. Build()         — 调用 MSBuild / make 编译 FluidX3D
    ///   4. RunSolver()     — 运行编译好的可执行文件
    ///   5. ReadResults()   — 读取 VTK 输出
    /// </summary>
    public class FluidX3DInterface
    {
        #region Properties

        /// <summary>FluidX3D 源码根目录（包含 FluidX3D.sln 或 Makefile）</summary>
        public string FluidX3DPath { get; set; }

        /// <summary>临时工作目录（存放生成的 Case 文件）</summary>
        public string WorkingDirectory { get; set; }

        /// <summary>最近一次部署的 Case 目录</summary>
        public string LastCaseDirectory { get; private set; }

        /// <summary>编译日志</summary>
        public string BuildLog { get; private set; }

        #endregion

        #region Constructor

        public FluidX3DInterface(string fluidX3DPath = "")
        {
            FluidX3DPath = fluidX3DPath?.Trim().TrimEnd('\\', '/') ?? "";
            
            // 如果未提供路径，尝试自动检测
            if (string.IsNullOrEmpty(FluidX3DPath))
            {
                FluidX3DPath = AutoDetectFluidX3DPath();
            }
            
            WorkingDirectory = Path.Combine(Path.GetTempPath(), "CityLBM");

            if (!Directory.Exists(WorkingDirectory))
                Directory.CreateDirectory(WorkingDirectory);
        }
        
        /// <summary>
        /// 自动检测 FluidX3D 安装路径
        /// 搜索常见位置：用户文档、下载文件夹、桌面等
        /// </summary>
        private string AutoDetectFluidX3DPath()
        {
            // 常见的 FluidX3D 安装位置（按优先级排序）
            var searchPaths = new List<string>
            {
                // 用户明确配置的环境变量
                Environment.GetEnvironmentVariable("FLUIDX3D_PATH") ?? "",
                
                // 常见手动下载位置
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "FluidX3D"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "FluidX3D-master"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads", "FluidX3D"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads", "FluidX3D-master"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "FluidX3D"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "FluidX3D-master"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "FluidX3D"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "FluidX3D-master"),
                
                // 其他常见位置
                @"C:\FluidX3D",
                @"C:\FluidX3D-master",
                @"D:\FluidX3D",
                @"D:\FluidX3D-master",
            };
            
            // 搜索包含 FluidX3D.sln 或 src/setup.cpp 的有效目录
            foreach (var basePath in searchPaths)
            {
                if (string.IsNullOrEmpty(basePath)) continue;
                
                // 直接检查该路径
                if (IsValidFluidX3DPath(basePath))
                    return basePath;
                
                // 检查子目录（解压后的文件夹结构）
                try
                {
                    if (Directory.Exists(basePath))
                    {
                        var subdirs = Directory.GetDirectories(basePath, "FluidX3D*", SearchOption.TopDirectoryOnly);
                        foreach (var subdir in subdirs)
                        {
                            if (IsValidFluidX3DPath(subdir))
                                return subdir;
                        }
                    }
                }
                catch { /* 忽略访问错误 */ }
            }
            
            // 在 C: 和 D: 盘搜索（仅限一级深度，避免太慢）
            foreach (var drive in new[] { @"C:\", @"D:\", @"E:\", @"F:\" })
            {
                try
                {
                    if (!Directory.Exists(drive)) continue;
                    
                    var dirs = Directory.GetDirectories(drive, "*FluidX3D*", SearchOption.TopDirectoryOnly)
                        .Concat(Directory.GetDirectories(drive, "*fluidx3d*", SearchOption.TopDirectoryOnly));
                    
                    foreach (var dir in dirs)
                    {
                        if (IsValidFluidX3DPath(dir))
                            return dir;
                        
                        // 再检查一级子目录
                        try
                        {
                            var subdirs = Directory.GetDirectories(dir, "FluidX3D*", SearchOption.TopDirectoryOnly);
                            foreach (var subdir in subdirs)
                            {
                                if (IsValidFluidX3DPath(subdir))
                                    return subdir;
                            }
                        }
                        catch { }
                    }
                }
                catch { /* 忽略访问错误 */ }
            }
            
            return ""; // 未找到
        }
        
        /// <summary>
        /// 验证路径是否为有效的 FluidX3D 源码目录
        /// </summary>
        private bool IsValidFluidX3DPath(string path)
        {
            if (string.IsNullOrEmpty(path) || !Directory.Exists(path))
                return false;
            
            // 检查关键文件/目录
            bool hasSln = File.Exists(Path.Combine(path, "FluidX3D.sln"));
            bool hasMakefile = File.Exists(Path.Combine(path, "Makefile"));
            bool hasSrcDir = Directory.Exists(Path.Combine(path, "src"));
            bool hasSetupCpp = File.Exists(Path.Combine(path, "src", "setup.cpp"));
            
            // 有效的 FluidX3D 目录应该包含解决方案文件或 Makefile，以及 src 目录
            return (hasSln || hasMakefile) && hasSrcDir;
        }

        #endregion

        #region Public Methods — Case Generation

        /// <summary>
        /// 清理指定场景目录下的旧输出文件（VTK 结果）
        /// 防止读取到上一次模拟的旧结果
        /// </summary>
        /// <param name="sceneName">场景名称</param>
        /// <returns>清理的文件数量</returns>
        public int ClearOutputFiles(string sceneName)
        {
            string caseDir = Path.Combine(WorkingDirectory, SanitizeName(sceneName));
            string outputDir = Path.Combine(caseDir, "output");
            int cleared = 0;

            // 清理 Case/output/ 下的旧 VTK 文件
            if (Directory.Exists(outputDir))
            {
                foreach (var f in Directory.GetFiles(outputDir, "*.vtk"))
                {
                    try { File.Delete(f); cleared++; } catch { }
                }
                foreach (var f in Directory.GetFiles(outputDir, "*.vtu"))
                {
                    try { File.Delete(f); cleared++; } catch { }
                }
            }

            // 清理 FluidX3D 部署目录下的旧 output（如果存在）
            if (!string.IsNullOrEmpty(FluidX3DPath))
            {
                string[] fluidOutputDirs = new[]
                {
                    Path.Combine(FluidX3DPath, "output"),
                    Path.Combine(FluidX3DPath, "bin", "export"),
                    Path.Combine(FluidX3DPath, "export"),
                };
                foreach (var dir in fluidOutputDirs)
                {
                    if (Directory.Exists(dir))
                    {
                        foreach (var f in Directory.GetFiles(dir, "*.vtk"))
                        {
                            try { File.Delete(f); cleared++; } catch { }
                        }
                    }
                }
            }

            return cleared;
        }

        /// <summary>
        /// 第一步：为场景生成 Case 文件（写入临时目录）
        /// 返回 Case 目录路径
        /// 每次生成前自动清理旧的 VTK 输出文件
        /// </summary>
        /// <param name="enableGraphics">是否在 defines.hpp 中启用 GRAPHICS（后台运行传 false）</param>
        public string GenerateCase(Scene scene, CartesianGrid grid, SimulationSettings settings, bool enableGraphics = true)
        {
            // 自动清理旧输出（防止读取到上次模拟的旧 VTK）
            int cleared = ClearOutputFiles(scene.Name);
            if (cleared > 0)
                Debug.WriteLine($"[CityLBM] 已清理 {cleared} 个旧 VTK 输出文件（场景: {scene.Name}）");

            // 使用场景名作为文件夹名
            string caseDir = Path.Combine(WorkingDirectory, SanitizeName(scene.Name));
            Directory.CreateDirectory(caseDir);

            string outputDir = Path.Combine(caseDir, "output");
            Directory.CreateDirectory(outputDir);

            // 1. 导出建筑物为 STL 文件
            string stlPath = Path.Combine(caseDir, "buildings.stl");
            ExportBuildingsToSTL(scene.BuildingMeshes, stlPath);

            // 2. 生成 defines.hpp
            string definesPath = Path.Combine(caseDir, "defines.hpp");
            GenerateDefinesHpp(grid, settings, definesPath, enableGraphics);

            // 3. 生成 setup.cpp（使用 FluidX3D 真实 API）
            // 注意：STL 和 VTK 路径使用相对路径，部署到 FluidX3D 后可正确运行
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            GenerateSetupCpp(scene, grid, settings, setupPath, "buildings.stl", "output");

            LastCaseDirectory = caseDir;
            return caseDir;
        }

        #endregion

        #region Public Methods — Deploy & Build

        /// <summary>
        /// 第二步：将 Case 文件部署到 FluidX3D 源码目录
        /// 覆盖 FluidX3D/src/setup.cpp 和 FluidX3D/src/defines.hpp
        /// </summary>
        public DeployResult DeployToFluidX3D(string caseDir)
        {
            var result = new DeployResult { CaseDirectory = caseDir };

            if (string.IsNullOrEmpty(FluidX3DPath) || !Directory.Exists(FluidX3DPath))
            {
                result.Success = false;
                result.ErrorMessage = $"FluidX3D 路径无效或不存在：\"{FluidX3DPath}\"\n请确保已设置正确的 FluidX3D 源码目录。";
                return result;
            }

            string fluidSrcDir = Path.Combine(FluidX3DPath, "src");
            if (!Directory.Exists(fluidSrcDir))
            {
                result.Success = false;
                result.ErrorMessage = $"找不到 FluidX3D/src 目录：\"{fluidSrcDir}\"\n请确认这是正确的 FluidX3D 源码根目录。";
                return result;
            }

            try
            {
                // 备份原始文件
                BackupOriginalFiles(fluidSrcDir);

                // 覆盖 setup.cpp
                string srcSetup = Path.Combine(caseDir, "setup.cpp");
                string dstSetup = Path.Combine(fluidSrcDir, "setup.cpp");
                File.Copy(srcSetup, dstSetup, overwrite: true);
                result.DeployedFiles.Add(dstSetup);

                // 覆盖 defines.hpp
                string srcDefines = Path.Combine(caseDir, "defines.hpp");
                string dstDefines = Path.Combine(fluidSrcDir, "defines.hpp");
                File.Copy(srcDefines, dstDefines, overwrite: true);
                result.DeployedFiles.Add(dstDefines);

                // 复制 buildings.stl 到 FluidX3D 目录（运行时路径）
                string srcStl = Path.Combine(caseDir, "buildings.stl");
                string dstStl = Path.Combine(FluidX3DPath, "buildings.stl");
                File.Copy(srcStl, dstStl, overwrite: true);
                result.DeployedFiles.Add(dstStl);

                result.Success = true;
                result.Message = $"已成功部署到 FluidX3D 源码目录：\n{fluidSrcDir}\n\n部署的文件：\n" +
                                 string.Join("\n", result.DeployedFiles.Select(f => "  - " + Path.GetFileName(f)));
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"部署失败：{ex.Message}";
            }

            return result;
        }

        /// <summary>
        /// 第三步：编译 FluidX3D
        /// 支持 Windows（MSBuild）和 Linux/Mac（make）
        /// </summary>
        public BuildResult Build(Action<string> progressCallback = null)
        {
            var result = new BuildResult { StartTime = DateTime.Now };

            if (string.IsNullOrEmpty(FluidX3DPath) || !Directory.Exists(FluidX3DPath))
            {
                result.Success = false;
                result.ErrorMessage = "FluidX3D 路径未设置或不存在。";
                return result;
            }

            // 检测编译方式
            string slnFile = Path.Combine(FluidX3DPath, "FluidX3D.sln");
            string makeFile = Path.Combine(FluidX3DPath, "Makefile");
            string cmakeLists = Path.Combine(FluidX3DPath, "CMakeLists.txt");

            try
            {
                if (File.Exists(slnFile))
                {
                    result = BuildWithMSBuild(slnFile, progressCallback);
                }
                else if (File.Exists(makeFile))
                {
                    result = BuildWithMake(FluidX3DPath, progressCallback);
                }
                else if (File.Exists(cmakeLists))
                {
                    result = BuildWithCMake(FluidX3DPath);
                }
                else
                {
                    result.Success = false;
                    result.ErrorMessage = "找不到编译文件（FluidX3D.sln / Makefile / CMakeLists.txt）。\n请确认这是正确的 FluidX3D 源码目录。";
                }
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"编译过程发生异常：{ex.Message}";
            }

            BuildLog = result.Log;
            result.EndTime = DateTime.Now;
            return result;
        }

        /// <summary>
        /// 第四步：运行编译好的 FluidX3D 可执行文件
        /// 启用了 GRAPHICS 模式时会弹出 FluidX3D 渲染窗口
        /// </summary>
        public SolverResult RunSolver(string outputDir = null)
        {
            var result = new SolverResult { StartTime = DateTime.Now };

            if (string.IsNullOrEmpty(FluidX3DPath))
            {
                result.Success = false;
                result.ErrorMessage = "FluidX3D 路径未设置。";
                return result;
            }

            // 找可执行文件
            string exePath = FindExecutable(FluidX3DPath);
            if (string.IsNullOrEmpty(exePath))
            {
                result.Success = false;
                result.ErrorMessage = "找不到 FluidX3D 可执行文件。请先编译。";
                return result;
            }

            // 输出目录
            string resolvedOutputDir = outputDir ?? Path.Combine(FluidX3DPath, "output");
            Directory.CreateDirectory(resolvedOutputDir);

            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = exePath,
                    WorkingDirectory = FluidX3DPath,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = false   // 弹出 FluidX3D 渲染窗口（GRAPHICS 模式需要）
                };

                var sb = new StringBuilder();
                using (var process = new Process { StartInfo = startInfo })
                {
                    process.OutputDataReceived += (s, e) => { if (e.Data != null) sb.AppendLine(e.Data); };
                    process.ErrorDataReceived += (s, e) => { if (e.Data != null) sb.AppendLine("[ERR] " + e.Data); };

                    process.Start();
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();
                    process.WaitForExit();

                    result.ExitCode = process.ExitCode;
                    result.Success = process.ExitCode == 0;
                    result.Log = sb.ToString();
                }
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"运行 FluidX3D 失败：{ex.Message}";
            }

            result.EndTime = DateTime.Now;
            result.CaseDirectory = FluidX3DPath;
            return result;
        }

        /// <summary>
        /// 一键完整流程：GenerateCase → Deploy → Build → Run
        /// </summary>
        public SolverResult GenerateDeployBuildRun(Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            var result = new SolverResult { StartTime = DateTime.Now };
            var log = new StringBuilder();

            log.AppendLine("=== CityLBM → FluidX3D 完整流程 ===");
            log.AppendLine($"场景: {scene.Name}");
            log.AppendLine($"时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
            log.AppendLine();

            // Step 1: Generate Case
            log.AppendLine("[1/4] 生成 Case 文件...");
            string caseDir;
            try
            {
                caseDir = GenerateCase(scene, grid, settings);
                log.AppendLine($"      ✓ Case 目录: {caseDir}");
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"生成 Case 失败: {ex.Message}";
                result.Log = log.ToString();
                return result;
            }

            // Step 2: Deploy
            log.AppendLine("[2/4] 部署到 FluidX3D 源码...");
            var deployResult = DeployToFluidX3D(caseDir);
            if (!deployResult.Success)
            {
                result.Success = false;
                result.ErrorMessage = deployResult.ErrorMessage;
                result.CaseDirectory = caseDir;
                result.Log = log.ToString() + deployResult.ErrorMessage;
                return result;
            }
            log.AppendLine($"      ✓ {deployResult.Message.Split('\n')[0]}");

            // Step 3: Build
            log.AppendLine("[3/4] 编译 FluidX3D...");
            var buildResult = Build();
            log.AppendLine(buildResult.Success ? "      ✓ 编译成功" : $"      ✗ 编译失败: {buildResult.ErrorMessage}");
            if (!string.IsNullOrEmpty(buildResult.Log))
                log.AppendLine(buildResult.Log);

            if (!buildResult.Success)
            {
                result.Success = false;
                result.ErrorMessage = buildResult.ErrorMessage;
                result.CaseDirectory = caseDir;
                result.Log = log.ToString();
                return result;
            }

            // Step 4: Run
            log.AppendLine("[4/4] 运行 FluidX3D 求解器...");
            string outputDir = Path.Combine(FluidX3DPath, "output");
            var runResult = RunSolver(outputDir);
            log.AppendLine(runResult.Success ? "      ✓ 模拟完成" : $"      ✗ 运行失败: {runResult.ErrorMessage}");

            // Step 5: 复制 VTK 结果回 Case 目录
            if (runResult.Success)
            {
                log.AppendLine("[5/5] 收集 VTK 结果...");
                try
                {
                    CopyVTKResultsToCaseDir(outputDir, caseDir);
                    log.AppendLine($"      ✓ VTK 文件已复制到: {Path.Combine(caseDir, "output")}");
                }
                catch (Exception ex)
                {
                    log.AppendLine($"      ⚠ 复制 VTK 失败: {ex.Message}");
                }
            }

            result.Success = runResult.Success;
            result.ExitCode = runResult.ExitCode;
            result.ErrorMessage = runResult.ErrorMessage;
            result.CaseDirectory = caseDir;
            result.OutputDirectory = Path.Combine(caseDir, "output");  // 指向 Case 目录下的 output
            result.EndTime = DateTime.Now;
            result.Log = log.ToString();

            return result;
        }

        /// <summary>
        /// 异步后台执行完整流程（Generate → Deploy → Build → Run）。
        /// 不阻塞调用线程，进度通过 progressCallback 实时回调，完成后调用 completionCallback。
        /// 返回 CancellationTokenSource，可随时取消。
        /// </summary>
        public CancellationTokenSource StartAsyncRun(
            Scene scene,
            CartesianGrid grid,
            SimulationSettings settings,
            Action<string, int> progressCallback,   // (message, progressPercent 0-100)
            Action<SolverResult> completionCallback)
        {
            var cts = new CancellationTokenSource();
            var token = cts.Token;

            Task.Run(() =>
            {
                var result = new SolverResult { StartTime = DateTime.Now };
                var log = new StringBuilder();

                void Report(string msg, int pct = -1)
                {
                    log.AppendLine(msg);
                    progressCallback?.Invoke(msg, pct);
                }

                try
                {
                    token.ThrowIfCancellationRequested();

                    // Step 1: Generate Case（Mode 3 不启用 GRAPHICS，避免与后台运行冲突）
                    Report("[1/4] 生成 Case 文件（无图形模式）...", 5);
                    Report($"      [调试] FluidX3DPath = {FluidX3DPath}", 5);
                    string caseDir = GenerateCase(scene, grid, settings, enableGraphics: false);
                    Report($"      [OK] Case 目录: {caseDir}", 15);

                    token.ThrowIfCancellationRequested();

                    // Step 2: Deploy
                    Report("[2/4] 部署到 FluidX3D 源码...", 20);
                    var deployResult = DeployToFluidX3D(caseDir);
                    if (!deployResult.Success)
                    {
                        result.Success = false;
                        result.ErrorMessage = deployResult.ErrorMessage;
                        result.CaseDirectory = caseDir;
                        result.Log = log.ToString();
                        completionCallback?.Invoke(result);
                        return;
                    }
                    Report($"      [OK] 部署成功", 25);

                    token.ThrowIfCancellationRequested();

                    // Step 3: Build（带进度回调，编译阶段 30→60%）
                    Report("[3/4] 编译 FluidX3D（可能需要 2-10 分钟）...", 30);
                    int buildLineCount = 0;
                    var buildResult = Build(msg => {
                        if (!string.IsNullOrWhiteSpace(msg))
                        {
                            buildLineCount++;
                            // 根据输出行数在 30-58% 之间插值（MSBuild 典型输出 50-200 行）
                            int buildPct = Math.Min(58, 30 + buildLineCount / 3);
                            Report("  " + msg, buildPct);
                        }
                    });

                    if (!buildResult.Success)
                    {
                        result.Success = false;
                        result.ErrorMessage = buildResult.ErrorMessage;
                        result.CaseDirectory = caseDir;
                        result.Log = log.ToString() + "\n\n--- Build Log ---\n" + buildResult.Log;
                        completionCallback?.Invoke(result);
                        return;
                    }
                    Report($"      [OK] 编译成功", 60);

                    token.ThrowIfCancellationRequested();

                    // Step 4: Run Solver（带进度回调，模拟阶段 65→88%）
                    Report("[4/4] 运行 FluidX3D 求解器...", 65);
                    Report($"      [调试] FluidX3DPath = {FluidX3DPath}", 65);
                    string outputDir = Path.Combine(FluidX3DPath, "output");
                    Report($"      [调试] OutputDir = {outputDir}", 65);

                    int solverLineCount = 0;
                    Report($"      [调试] 即将调用 RunSolverWithCallback...", 65);
                    var runResult = RunSolverWithCallback(outputDir, msg => {
                        if (!string.IsNullOrWhiteSpace(msg))
                        {
                            solverLineCount++;
                            // 根据输出行数在 65-88% 之间插值（每 10 行推进约 1%）
                            int runPct = Math.Min(88, 65 + solverLineCount / 10);
                            Report("  " + msg, runPct);
                        }
                    }, token);

                    Report($"      [调试] RunSolverWithCallback 返回，Success={runResult.Success}, ExitCode={runResult.ExitCode}", 88);
                    if (!string.IsNullOrEmpty(runResult.ErrorMessage))
                        Report($"      [调试] ErrorMessage: {runResult.ErrorMessage}", 88);

                    if (!runResult.Success)
                    {
                        result.Success = false;
                        result.ErrorMessage = runResult.ErrorMessage;
                        result.CaseDirectory = caseDir;
                        result.Log = log.ToString();
                        completionCallback?.Invoke(result);
                        return;
                    }
                    Report($"      [OK] 模拟完成", 90);

                    // Step 5: Collect VTK
                    Report("[5/5] 收集 VTK 结果...", 92);
                    try
                    {
                        CopyVTKResultsToCaseDir(outputDir, caseDir);
                        Report($"      [OK] VTK 文件已复制到: {Path.Combine(caseDir, "output")}", 98);
                    }
                    catch (Exception ex)
                    {
                        Report($"      [!] 复制 VTK 失败: {ex.Message}");
                    }

                    result.Success = true;
                    result.CaseDirectory = caseDir;
                    result.OutputDirectory = Path.Combine(caseDir, "output");
                    result.EndTime = DateTime.Now;
                    result.Log = log.ToString();
                    Report($"=== 全流程完成，耗时 {result.Duration.TotalMinutes:F1} 分钟 ===", 100);
                }
                catch (OperationCanceledException)
                {
                    result.Success = false;
                    result.ErrorMessage = "用户取消了操作";
                    result.Log = log.ToString();
                }
                catch (Exception ex)
                {
                    result.Success = false;
                    result.ErrorMessage = ex.Message;
                    result.Log = log.ToString();
                }

                completionCallback?.Invoke(result);

            }, token);

            return cts;
        }

        /// <summary>
        /// RunSolver 的带回调版本（内部使用）
        /// </summary>
        private SolverResult RunSolverWithCallback(string outputDir, Action<string> progressCallback, CancellationToken token = default)
        {
            var result = new SolverResult { StartTime = DateTime.Now };

            if (string.IsNullOrEmpty(FluidX3DPath))
            {
                result.Success = false;
                result.ErrorMessage = "FluidX3D 路径未设置。";
                progressCallback?.Invoke("[错误] FluidX3D 路径未设置");
                return result;
            }

            progressCallback?.Invoke($"[调试] FluidX3D 路径: {FluidX3DPath}");
            string exePath = FindExecutable(FluidX3DPath);
            progressCallback?.Invoke($"[调试] 查找 exe 结果: {exePath ?? "未找到"}");
            
            if (string.IsNullOrEmpty(exePath))
            {
                result.Success = false;
                result.ErrorMessage = "找不到 FluidX3D 可执行文件。请先编译。";
                progressCallback?.Invoke("[错误] 找不到 FluidX3D.exe，查找位置:");
                progressCallback?.Invoke($"  - {Path.Combine(FluidX3DPath, "bin", "Release", "x64", "FluidX3D.exe")}");
                progressCallback?.Invoke($"  - {Path.Combine(FluidX3DPath, "x64", "Release", "FluidX3D.exe")}");
                progressCallback?.Invoke($"  - {Path.Combine(FluidX3DPath, "FluidX3D.exe")}");
                return result;
            }
            
            progressCallback?.Invoke($"[调试] 找到 exe: {exePath}");

            Directory.CreateDirectory(outputDir);

            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = exePath,
                    WorkingDirectory = FluidX3DPath,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true  // Mode 3 无图形后台运行，不弹窗
                };

                var sb = new StringBuilder();
                progressCallback?.Invoke($"[调试] 启动进程: {exePath}");
                progressCallback?.Invoke($"[调试] 工作目录: {FluidX3DPath}");
                
                using (var process = new Process { StartInfo = startInfo })
                {
                    process.OutputDataReceived += (s, e) => {
                        if (e.Data != null) {
                            sb.AppendLine(e.Data);
                            progressCallback?.Invoke(e.Data);
                        }
                    };
                    process.ErrorDataReceived += (s, e) => {
                        if (e.Data != null) {
                            sb.AppendLine("[ERR] " + e.Data);
                            progressCallback?.Invoke("[ERR] " + e.Data);
                        }
                    };

                    bool started = process.Start();
                    progressCallback?.Invoke($"[调试] 进程启动结果: {started}, PID: {process.Id}");
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();

                    // 支持取消：轮询检查 token
                    while (!process.WaitForExit(500))
                    {
                        if (token.IsCancellationRequested)
                        {
                            try { process.Kill(); } catch { }
                            token.ThrowIfCancellationRequested();
                        }
                    }

                    result.ExitCode = process.ExitCode;
                    result.Success = process.ExitCode == 0;
                    result.Log = sb.ToString();
                }
            }
            catch (OperationCanceledException) { throw; }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = $"运行 FluidX3D 失败：{ex.Message}";
            }

            result.EndTime = DateTime.Now;
            result.CaseDirectory = FluidX3DPath;
            return result;
        }

        /// <summary>
        /// 生成 Case 文件，并在提供 FluidX3D 路径时自动完成文件部署（步骤 1-4）。
        /// 同时在 Case 目录生成一键编译运行脚本 run_fluidx3d.bat / run_fluidx3d.sh。
        /// </summary>
        public CaseGenerationResult GenerateCaseOnly(Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            var result = new CaseGenerationResult { StartTime = DateTime.Now };
            try
            {
                string caseDir = GenerateCase(scene, grid, settings);
                result.Success = true;
                result.CaseDirectory = caseDir;

                // 若提供了 FluidX3D 路径，自动部署文件（步骤 1-4）
                bool autoDeploy = !string.IsNullOrWhiteSpace(FluidX3DPath) && Directory.Exists(FluidX3DPath);
                if (autoDeploy)
                {
                    var deployResult = DeployToFluidX3D(caseDir);
                    result.AutoDeployed = deployResult.Success;
                    result.DeployMessage = deployResult.Success
                        ? deployResult.Message
                        : $"自动部署失败：{deployResult.ErrorMessage}";

                    if (deployResult.Success)
                    {
                        // 生成一键脚本（放在 FluidX3D 根目录和 Case 目录各一份）
                        GenerateBuildRunScript(caseDir, FluidX3DPath);
                    }
                }

                // 生成输出说明（根据是否自动部署显示不同内容）
                result.Instructions = GenerateInstructions(caseDir, autoDeploy && result.AutoDeployed);
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = ex.Message;
            }
            return result;
        }

        /// <summary>
        /// 在 FluidX3D 根目录生成一键编译运行脚本（Windows .bat）
        /// </summary>
        private void GenerateBuildRunScript(string caseDir, string fluidX3DPath)
        {
            string caseOutputDir = Path.Combine(caseDir, "output");
            string fluidOutputDir = Path.Combine(fluidX3DPath, "output");

            // ---- Windows .bat 脚本 ----
            var bat = new StringBuilder();
            bat.AppendLine("@echo off");
            bat.AppendLine("chcp 65001 >nul 2>&1");
            bat.AppendLine("echo =========================================");
            bat.AppendLine("echo   CityLBM - 一键编译运行 FluidX3D");
            bat.AppendLine("echo =========================================");
            bat.AppendLine("echo.");
            bat.AppendLine($"cd /d \"{fluidX3DPath}\"");
            bat.AppendLine();

            // 创建 output 目录
            bat.AppendLine("echo [步骤 1/3] 创建输出目录...");
            bat.AppendLine($"if not exist \"{fluidOutputDir}\" mkdir \"{fluidOutputDir}\"");
            bat.AppendLine("echo   [OK] 输出目录就绪");
            bat.AppendLine();

            // 查找并调用 MSBuild 编译
            bat.AppendLine("echo [步骤 2/3] 编译 FluidX3D...");
            bat.AppendLine("set MSBUILD=");

            // 按顺序尝试常见 MSBuild 路径
            string[] msbuildPaths = new[]
            {
                @"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
            };
            foreach (string mb in msbuildPaths)
                bat.AppendLine($"if exist \"{mb}\" set MSBUILD={mb}");

            bat.AppendLine();
            bat.AppendLine("if \"%MSBUILD%\"==\"\" (");
            bat.AppendLine("    echo   [!] 未找到预设 MSBuild 路径，尝试自动查找...");
            bat.AppendLine("    for /f \"delims=\" %%i in ('where msbuild 2^>nul') do set MSBUILD=%%i");
            bat.AppendLine(")");
            bat.AppendLine("if \"%MSBUILD%\"==\"\" (");
            bat.AppendLine("    echo   X 找不到 MSBuild，请手动编译 FluidX3D.sln");
            bat.AppendLine("    echo   提示: 安装 Visual Studio 2019/2022 或 Build Tools");
            bat.AppendLine("    pause");
            bat.AppendLine("    exit /b 1");
            bat.AppendLine(")");
            bat.AppendLine("echo   MSBuild: %MSBUILD%");
            bat.AppendLine();
            // 自动检测本机已安装的平台工具集版本（v143=VS2022, v142=VS2019, v141=VS2017）
            bat.AppendLine("set TOOLSET=v143");
            bat.AppendLine("if not exist \"C:\\Program Files\\Microsoft Visual Studio\\2022\" set TOOLSET=v142");
            bat.AppendLine("if not exist \"C:\\Program Files\\Microsoft Visual Studio\\2019\" if \"%TOOLSET%\"==\"v142\" set TOOLSET=v141");
            bat.AppendLine("echo   工具集: %TOOLSET%");
            bat.AppendLine();
            bat.AppendLine($"\"%MSBUILD%\" \"{Path.Combine(fluidX3DPath, "FluidX3D.sln")}\" /t:Build /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset=%TOOLSET% /m /nologo");
            bat.AppendLine("if %ERRORLEVEL% neq 0 (");
            bat.AppendLine("    echo.");
            bat.AppendLine("    echo   X 编译失败！常见原因：");
            bat.AppendLine("    echo     1. CUDA 版本不匹配 - 检查 defines.hpp 中的 GPU 设置");
            bat.AppendLine("    echo     2. 缺少 Windows SDK - 在 VS Installer 中安装");
            bat.AppendLine("    echo     3. 工具集不匹配 - 尝试在 VS 中右键解决方案 \"重定解决方案目标\"");
            bat.AppendLine("    pause");
            bat.AppendLine("    exit /b 1");
            bat.AppendLine(")");
            bat.AppendLine("echo   V 编译成功");
            bat.AppendLine();

            // 运行求解器
            bat.AppendLine("echo [步骤 3/3] 运行 FluidX3D...");
            bat.AppendLine("set EXE=");
            string[] exePaths = new[]
            {
                Path.Combine(fluidX3DPath, "bin", "Release", "x64", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "bin", "Release", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "x64", "Release", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "FluidX3D.exe"),
            };
            foreach (string ep in exePaths)
                bat.AppendLine($"if exist \"{ep}\" set EXE={ep}");

            bat.AppendLine();
            bat.AppendLine("if \"%EXE%\"==\"\" (");
            bat.AppendLine("    echo   [!] 找不到 FluidX3D.exe，尝试在输出目录查找...");
            bat.AppendLine($"    for /r \"{fluidX3DPath}\" %%f in (FluidX3D.exe) do set EXE=%%f");
            bat.AppendLine(")");
            bat.AppendLine("if \"%EXE%\"==\"\" (");
            bat.AppendLine("    echo   [X] 找不到 FluidX3D.exe，请先编译");
            bat.AppendLine("    pause");
            bat.AppendLine("    exit /b 1");
            bat.AppendLine(")");
            bat.AppendLine("echo   EXE: %EXE%");
            bat.AppendLine();
            bat.AppendLine($"\"%EXE%\"");
            bat.AppendLine("if %ERRORLEVEL% neq 0 (");
            bat.AppendLine("    echo   [X] FluidX3D 运行失败");
            bat.AppendLine("    pause");
            bat.AppendLine("    exit /b 1");
            bat.AppendLine(")");
            bat.AppendLine("echo   [OK] FluidX3D 运行完成");
            bat.AppendLine();

            // 复制 VTK 结果回 Case 目录
            bat.AppendLine("echo [后处理] 复制 VTK 结果回 Case 目录...");
            bat.AppendLine($"if not exist \"{caseOutputDir}\" mkdir \"{caseOutputDir}\"");
            bat.AppendLine($"xcopy /Y /Q \"{fluidOutputDir}\\*.vtk\" \"{caseOutputDir}\\\" 2>nul");
            bat.AppendLine($"xcopy /Y /Q \"{fluidOutputDir}\\*.vtu\" \"{caseOutputDir}\\\" 2>nul");
            bat.AppendLine("echo   [OK] VTK 文件已复制到：");
            bat.AppendLine($"echo     {caseOutputDir}");
            bat.AppendLine();
            bat.AppendLine("echo =========================================");
            bat.AppendLine("echo   模拟完成！在 Grasshopper 中使用");
            bat.AppendLine("echo   Read VTK 组件读取以下目录：");
            bat.AppendLine($"echo   {caseOutputDir}");
            bat.AppendLine("echo =========================================");
            bat.AppendLine("pause");

            // 同时写到 FluidX3D 根目录和 Case 目录（UTF-8 with BOM，bat + chcp 65001 兼容）
            var utf8bom = new UTF8Encoding(encoderShouldEmitUTF8Identifier: true);
            string batInFluidX3D = Path.Combine(fluidX3DPath, "run_citylbm.bat");
            string batInCase = Path.Combine(caseDir, "run_citylbm.bat");
            File.WriteAllText(batInFluidX3D, bat.ToString(), utf8bom);
            File.WriteAllText(batInCase, bat.ToString(), utf8bom);
        }

        /// <summary>
        /// 读取 VTK 结果文件
        /// </summary>
        public List<VTKResult> ReadVTKResults(string directory)
        {
            var results = new List<VTKResult>();
            if (!Directory.Exists(directory)) return results;

            var vtkFiles = Directory.GetFiles(directory, "*.vtk")
                                    .OrderBy(f => ExtractTimeStepFromFilename(f))
                                    .ToArray();

            foreach (string vtkFile in vtkFiles)
            {
                try
                {
                    results.Add(ParseVTKFile(vtkFile));
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"解析 VTK 文件失败 {vtkFile}: {ex.Message}");
                }
            }

            return results;
        }

        /// <summary>
        /// 还原备份（恢复 FluidX3D 原始文件）
        /// </summary>
        public bool RestoreBackup()
        {
            if (string.IsNullOrEmpty(FluidX3DPath)) return false;
            string fluidSrcDir = Path.Combine(FluidX3DPath, "src");
            string backupDir = Path.Combine(FluidX3DPath, ".citylbm_backup");

            if (!Directory.Exists(backupDir)) return false;

            try
            {
                foreach (string bakFile in Directory.GetFiles(backupDir))
                {
                    string dstFile = Path.Combine(fluidSrcDir, Path.GetFileName(bakFile));
                    File.Copy(bakFile, dstFile, overwrite: true);
                }
                return true;
            }
            catch { return false; }
        }

        /// <summary>
        /// 将 FluidX3D 输出的 VTK 文件复制回 Case 目录
        /// FluidX3D 默认输出到 bin/export/，但也可能输出到 output/
        /// </summary>
        private void CopyVTKResultsToCaseDir(string fluidX3DOutputDir, string caseDir)
        {
            string caseOutputDir = Path.Combine(caseDir, "output");
            Directory.CreateDirectory(caseOutputDir);

            // FluidX3D 默认输出目录列表（按优先级）
            string[] possibleDirs = new[]
            {
                fluidX3DOutputDir,                                    // 指定的 output 目录
                Path.Combine(Path.GetDirectoryName(fluidX3DOutputDir), "export"),  // bin/export/
                Path.Combine(FluidX3DPath, "bin", "export"),         // FluidX3DPath/bin/export/
                Path.Combine(FluidX3DPath, "export"),                // FluidX3DPath/export/
            };

            int copiedCount = 0;
            foreach (string dir in possibleDirs)
            {
                if (!Directory.Exists(dir)) continue;
                
                foreach (string vtkFile in Directory.GetFiles(dir, "*.vtk"))
                {
                    string destFile = Path.Combine(caseOutputDir, Path.GetFileName(vtkFile));
                    File.Copy(vtkFile, destFile, overwrite: true);
                    copiedCount++;
                }
            }

            if (copiedCount == 0)
            {
                throw new FileNotFoundException($"未找到 VTK 文件。请检查以下目录是否存在 .vtk 文件:\n" +
                    string.Join("\n", possibleDirs.Select(d => $"  - {d}")));
            }
        }

        #endregion

        #region Private — Build Methods

        private BuildResult BuildWithMSBuild(string slnFile, Action<string> progressCallback = null)
        {
            var result = new BuildResult { StartTime = DateTime.Now };

            // 查找 MSBuild
            string msBuildPath = FindMSBuild();
            if (string.IsNullOrEmpty(msBuildPath))
            {
                result.Success = false;
                result.ErrorMessage = "找不到 MSBuild。请安装 Visual Studio 或 Build Tools。";
                return result;
            }

            // 自动检测本机已安装的平台工具集（v143=VS2022, v142=VS2019, v141=VS2017）
            string toolset = DetectPlatformToolset();
            progressCallback?.Invoke($"[编译] 使用工具集: {toolset}，MSBuild: {msBuildPath}");

            var sb = new StringBuilder();
            var startInfo = new ProcessStartInfo
            {
                FileName = msBuildPath,
                Arguments = $"\"{slnFile}\" /t:Rebuild /p:Configuration=Release /p:Platform=x64 /p:PlatformToolset={toolset} /m /nologo /v:minimal",
                WorkingDirectory = Path.GetDirectoryName(slnFile),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                StandardErrorEncoding = System.Text.Encoding.UTF8
            };

            using (var process = new Process { StartInfo = startInfo })
            {
                process.OutputDataReceived += (s, e) => {
                    if (e.Data != null) {
                        sb.AppendLine(e.Data);
                        progressCallback?.Invoke(e.Data);
                    }
                };
                process.ErrorDataReceived += (s, e) => {
                    if (e.Data != null) {
                        sb.AppendLine("[ERR] " + e.Data);
                        progressCallback?.Invoke("[ERR] " + e.Data);
                    }
                };
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                process.WaitForExit();

                result.ExitCode = process.ExitCode;
                result.Success = process.ExitCode == 0;
            }

            result.Log = sb.ToString();
            
            // 检查日志中是否包含关键错误（即使退出码为0）
            string logLower = result.Log.ToLower();
            bool hasCriticalError = logLower.Contains("error") || 
                                    logLower.Contains("msb4018") || 
                                    logLower.Contains("任务意外失败");
            
            if (result.Success && hasCriticalError)
            {
                result.Success = false;
                result.ErrorMessage = $"编译过程中检测到错误（可能是文件被占用或工具集问题）。请关闭其他占用 FluidX3D 文件的程序后重试。";
                progressCallback?.Invoke("[错误] 编译日志中包含错误信息，视为失败");
            }
            
            // 检查 exe 是否生成
            progressCallback?.Invoke($"[调试] 编译结束，退出码: {result.ExitCode}, Success: {result.Success}");
            if (result.Success)
            {
                string exePath = FindExecutable(Path.GetDirectoryName(slnFile));
                progressCallback?.Invoke($"[调试] 查找 exe 结果: {exePath ?? "未找到"}");
                if (string.IsNullOrEmpty(exePath))
                {
                    result.Success = false;
                    result.ErrorMessage = $"编译成功但未找到 FluidX3D.exe。请检查输出路径。查找位置:\n" +
                        $"  - {Path.Combine(Path.GetDirectoryName(slnFile), "x64", "Release", "FluidX3D.exe")}\n" +
                        $"  - {Path.Combine(Path.GetDirectoryName(slnFile), "bin", "Release", "x64", "FluidX3D.exe")}";
                    progressCallback?.Invoke("[错误] 编译成功但未找到 exe 文件");
                }
                else
                {
                    progressCallback?.Invoke($"[OK] 找到编译输出: {exePath}");
                }
            }
            else if (!hasCriticalError)
            {
                result.ErrorMessage = $"MSBuild 编译失败（工具集 {toolset}，退出码 {result.ExitCode}）。查看 Log 获取详情。";
            }

            return result;
        }

        private BuildResult BuildWithMake(string sourceDir, Action<string> progressCallback = null)
        {
            var result = new BuildResult { StartTime = DateTime.Now };
            var sb = new StringBuilder();

            var startInfo = new ProcessStartInfo
            {
                FileName = "make",
                Arguments = "-j4",
                WorkingDirectory = sourceDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var process = new Process { StartInfo = startInfo })
            {
                process.OutputDataReceived += (s, e) => {
                    if (e.Data != null) {
                        sb.AppendLine(e.Data);
                        progressCallback?.Invoke(e.Data);
                    }
                };
                process.ErrorDataReceived += (s, e) => {
                    if (e.Data != null) {
                        sb.AppendLine("[ERR] " + e.Data);
                        progressCallback?.Invoke("[ERR] " + e.Data);
                    }
                };
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                process.WaitForExit();

                result.ExitCode = process.ExitCode;
                result.Success = process.ExitCode == 0;
            }

            result.Log = sb.ToString();
            if (!result.Success)
                result.ErrorMessage = "make 编译失败。";

            return result;
        }

        private BuildResult BuildWithCMake(string sourceDir)
        {
            var result = new BuildResult { StartTime = DateTime.Now };
            var sb = new StringBuilder();
            string buildDir = Path.Combine(sourceDir, "build");
            Directory.CreateDirectory(buildDir);

            // cmake configure
            RunProcess("cmake", $"-S \"{sourceDir}\" -B \"{buildDir}\" -DCMAKE_BUILD_TYPE=Release", sourceDir, sb);
            // cmake build
            RunProcess("cmake", $"--build \"{buildDir}\" --config Release -- -j4", sourceDir, sb);

            result.Log = sb.ToString();
            result.Success = !result.Log.Contains("[ERR]");
            if (!result.Success)
                result.ErrorMessage = "CMake 编译失败。";

            return result;
        }

        private void RunProcess(string fileName, string args, string workDir, StringBuilder output)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = args,
                WorkingDirectory = workDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var p = new Process { StartInfo = startInfo })
            {
                p.OutputDataReceived += (s, e) => { if (e.Data != null) output.AppendLine(e.Data); };
                p.ErrorDataReceived += (s, e) => { if (e.Data != null) output.AppendLine("[ERR] " + e.Data); };
                p.Start();
                p.BeginOutputReadLine();
                p.BeginErrorReadLine();
                p.WaitForExit();
            }
        }

        /// <summary>
        /// 自动检测本机已安装的 Visual Studio C++ 平台工具集版本
        /// v143 = VS2022, v142 = VS2019, v141 = VS2017
        /// </summary>
        private string DetectPlatformToolset()
        {
            // 检查 VS2022
            if (Directory.Exists(@"C:\Program Files\Microsoft Visual Studio\2022"))
                return "v143";
            // 检查 VS2019
            if (Directory.Exists(@"C:\Program Files (x86)\Microsoft Visual Studio\2019") ||
                Directory.Exists(@"C:\Program Files\Microsoft Visual Studio\2019"))
                return "v142";
            // 检查 VS2017
            if (Directory.Exists(@"C:\Program Files (x86)\Microsoft Visual Studio\2017") ||
                Directory.Exists(@"C:\Program Files\Microsoft Visual Studio\2017"))
                return "v141";
            // 默认最新
            return "v143";
        }

        private string FindMSBuild()
        {
            // 常见 MSBuild 路径
            string[] candidates = new[]
            {
                @"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
                @"C:\Program Files\dotnet\dotnet.exe"
            };

            foreach (string candidate in candidates)
            {
                if (File.Exists(candidate)) return candidate;
            }

            // 尝试 PATH 中查找
            try
            {
                var startInfo = new ProcessStartInfo("where", "MSBuild.exe")
                {
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };
                using (var p = Process.Start(startInfo))
                {
                    string output = p.StandardOutput.ReadLine();
                    p.WaitForExit();
                    if (!string.IsNullOrEmpty(output) && File.Exists(output))
                        return output;
                }
            }
            catch { }

            return null;
        }

        private string FindExecutable(string fluidX3DPath)
        {
            string[] candidates = new[]
            {
                // MSBuild 默认输出路径（根据 .vcxproj 配置）
                Path.Combine(fluidX3DPath, "bin", "FluidX3D.exe"),
                // 其他常见路径
                Path.Combine(fluidX3DPath, "bin", "Release", "x64", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "bin", "Release", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "x64", "Release", "FluidX3D.exe"),
                Path.Combine(fluidX3DPath, "build", "FluidX3D"),
                Path.Combine(fluidX3DPath, "FluidX3D"),
                Path.Combine(fluidX3DPath, "FluidX3D.exe"),
            };

            foreach (string c in candidates)
            {
                if (File.Exists(c)) return c;
            }
            return null;
        }

        #endregion

        #region Private — Case File Generators

        private void ExportBuildingsToSTL(List<Mesh> meshes, string stlPath)
        {
            if (meshes == null || meshes.Count == 0)
            {
                // 写一个空的 STL（占位）
                File.WriteAllText(stlPath, "solid empty\nendsolid empty\n");
                return;
            }

            using (BinaryWriter writer = new BinaryWriter(File.Open(stlPath, FileMode.Create)))
            {
                byte[] header = new byte[80];
                Encoding.ASCII.GetBytes("CityLBM Building Meshes").CopyTo(header, 0);
                writer.Write(header);

                int totalTriangles = meshes.Sum(m => m.Faces.Sum(f => f.IsQuad ? 2 : 1));
                writer.Write(totalTriangles);

                foreach (var mesh in meshes)
                {
                    foreach (var face in mesh.Faces)
                    {
                        var v0 = mesh.Vertices[face.A];
                        var v1 = mesh.Vertices[face.B];
                        var v2 = mesh.Vertices[face.C];
                        var n = ComputeNormal(v0, v1, v2);
                        WriteTriangle(writer, n, v0, v1, v2);

                        if (face.IsQuad)
                        {
                            var v3 = mesh.Vertices[face.D];
                            WriteTriangle(writer, n, v2, v3, v0);
                        }
                    }
                }
            }
        }

        private Vector3f ComputeNormal(Point3f v0, Point3f v1, Point3f v2)
        {
            Vector3f e1 = v1 - v0;
            Vector3f e2 = v2 - v0;
            Vector3f n = Vector3f.CrossProduct(e1, e2);
            n.Unitize();
            return n;
        }

        private void WriteTriangle(BinaryWriter w, Vector3f n, Point3f v0, Point3f v1, Point3f v2)
        {
            w.Write(n.X); w.Write(n.Y); w.Write(n.Z);
            w.Write(v0.X); w.Write(v0.Y); w.Write(v0.Z);
            w.Write(v1.X); w.Write(v1.Y); w.Write(v1.Z);
            w.Write(v2.X); w.Write(v2.Y); w.Write(v2.Z);
            w.Write((ushort)0);
        }

        /// <summary>
        /// 生成 defines.hpp（覆盖 FluidX3D/src/defines.hpp）
        /// 只设置 CityLBM 需要的宏；其他宏保留 FluidX3D 默认值
        /// </summary>
        /// <param name="enableGraphics">是否启用实时渲染窗口（Mode 3 后台运行时应传 false）</param>
        private void GenerateDefinesHpp(CartesianGrid grid, SimulationSettings settings, string definesPath, bool enableGraphics = true)
        {
            var sb = new StringBuilder();
            sb.AppendLine("// ====================================================");
            sb.AppendLine("// CityLBM 自动生成 — 请勿手动修改");
            sb.AppendLine($"// 生成时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
            sb.AppendLine("// ====================================================");
            sb.AppendLine("#pragma once");
            sb.AppendLine();

            // 网格分辨率（FluidX3D 核心参数）
            sb.AppendLine("// ---- 网格尺寸 ----");
            sb.AppendLine($"#define SX {grid.Nx}u  // X 方向格子数");
            sb.AppendLine($"#define SY {grid.Ny}u  // Y 方向格子数");
            sb.AppendLine($"#define SZ {grid.Nz}u  // Z 方向格子数");
            sb.AppendLine();

            // D3Q19 碰撞模型（城市风环境推荐）
            sb.AppendLine("// ---- LBM 模型 ----");
            sb.AppendLine("#define D3Q19    // 推荐城市风环境");
            sb.AppendLine("// #define D3Q27 // 更精确但更慢");
            sb.AppendLine();

            // 松弛方案
            sb.AppendLine("// ---- 松弛方案 ----");
            sb.AppendLine("#define SRT      // 单松弛时间 (BGK)");
            sb.AppendLine("// #define TRT");
            sb.AppendLine();

            // 扩展功能
            sb.AppendLine("// ---- 扩展功能 ----");
            sb.AppendLine("#define FORCE_FIELD              // 允许体力");
            sb.AppendLine("#define EQUILIBRIUM_BOUNDARIES   // 平衡边界（TYPE_E，入口/出口需要）");
            sb.AppendLine("// #define TEMPERATURE            // 温度场（可选）");
            sb.AppendLine("// #define PARTICLES              // 粒子追踪（可选）");
            sb.AppendLine("// #define MOVING_BOUNDARIES");
            sb.AppendLine("// #define SURFACE");
            sb.AppendLine("// #define VOLUME_FORCE");
            sb.AppendLine();

            // 浮点精度（默认使用 FP32 确保最大兼容性）
            sb.AppendLine("// ---- 浮点精度 ----");
            sb.AppendLine("// 注意：FP16S 可提升 2 倍速度并减少 50% 显存占用，但需要显卡支持硬件 FP16");
            sb.AppendLine("// RTX 20/30/40 系列支持 FP16，旧显卡或出现数据异常时请使用 FP32");
            sb.AppendLine("// #define FP16S  // 半精度 IEEE-754（速度最快，显存最少，RTX 显卡推荐）");
            sb.AppendLine("// #define FP16C  // 半精度自定义（略慢但精度稍高）");
            sb.AppendLine("// 默认使用 float 单精度（最大兼容性，CPU 模式或旧显卡推荐）");
            sb.AppendLine("// 如需启用 FP16S，请取消上面 FP16S 的注释，并注释掉下面的 fpxx float 定义");
            sb.AppendLine();

            // fpxx C++ 类型别名（必须在此处定义！lbm.hpp/lbm.cpp 中 Memory<fpxx> 等代码在编译时需要这个类型）
            sb.AppendLine("// ---- fpxx C++ 类型别名（编译时必须，供 lbm.hpp/lbm.cpp 使用）----");
            sb.AppendLine("// 注意：此定义必须与上面的浮点精度设置保持一致");
            sb.AppendLine("#if defined(FP16S) || defined(FP16C)");
            sb.AppendLine("#define fpxx ushort  // 半精度模式");
            sb.AppendLine("#else // 默认 FP32");
            sb.AppendLine("#define fpxx float   // 单精度模式（默认，最大兼容性）");
            sb.AppendLine("#endif");
            sb.AppendLine();

            // 单元类型标志（必须在此处定义！lbm.cpp 第 816 行等 C++ 代码直接使用这些宏）
            sb.AppendLine("// ---- 单元类型标志（编译时必须，供 lbm.cpp 等 C++ 代码使用）----");
            sb.AppendLine("#define TYPE_S 0x01  // 0b00000001  固体边界（静止或移动）");
            sb.AppendLine("#define TYPE_E 0x02  // 0b00000010  平衡边界（流入/流出）");
            sb.AppendLine("#define TYPE_T 0x04  // 0b00000100  温度边界");
            sb.AppendLine("#define TYPE_F 0x08  // 0b00001000  流体");
            sb.AppendLine("#define TYPE_I 0x10  // 0b00010000  界面");
            sb.AppendLine("#define TYPE_G 0x20  // 0b00100000  气体");
            sb.AppendLine("#define TYPE_X 0x40  // 0b01000000  保留类型 X");
            sb.AppendLine("#define TYPE_Y 0x80  // 0b10000000  保留类型 Y");
            sb.AppendLine();

            // 可视化标志（VIS_* 宏）
            sb.AppendLine("// ---- 可视化标志 ----");
            sb.AppendLine("#define VIS_FLAG_LATTICE  0x01");
            sb.AppendLine("#define VIS_FLAG_SURFACE  0x02");
            sb.AppendLine("#define VIS_FIELD         0x04");
            sb.AppendLine("#define VIS_STREAMLINES   0x08");
            sb.AppendLine("#define VIS_Q_CRITERION   0x10");
            sb.AppendLine("#define VIS_PHI_RASTERIZE 0x20");
            sb.AppendLine("#define VIS_PHI_RAYTRACE  0x40");
            sb.AppendLine("#define VIS_PARTICLES     0x80");
            sb.AppendLine();

            // 图形输出（Mode 3 后台运行时禁用，避免与 RedirectStandardOutput 冲突）
            sb.AppendLine("// ---- 图形输出 ----");
            if (enableGraphics)
            {
                sb.AppendLine("// 启用实时渲染窗口（FluidX3D 全屏显示模拟过程）");
                sb.AppendLine("// 按键控制：P=暂停/继续, H=帮助, Esc=退出");
                sb.AppendLine("#define GRAPHICS");
                sb.AppendLine("#define INTERACTIVE_GRAPHICS");
                sb.AppendLine();
                // GRAPHICS_* 宏（启用 GRAPHICS 时必须定义）
                sb.AppendLine("#define GRAPHICS_FRAME_WIDTH     1920u");
                sb.AppendLine("#define GRAPHICS_FRAME_HEIGHT    1080u");
                sb.AppendLine("#define GRAPHICS_BACKGROUND_COLOR 0x000000");
                sb.AppendLine("#define GRAPHICS_U_MAX           0.3f");
                sb.AppendLine("#define GRAPHICS_RHO_DELTA       0.001f");
                sb.AppendLine("#define GRAPHICS_T_DELTA         1.0f");
                sb.AppendLine("#define GRAPHICS_F_MAX           0.002f");
                sb.AppendLine("#define GRAPHICS_Q_CRITERION     0.0001f");
                sb.AppendLine("#define GRAPHICS_STREAMLINE_SPARSE 4u");
                sb.AppendLine("#define GRAPHICS_STREAMLINE_LENGTH 128u");
                sb.AppendLine("#define GRAPHICS_RAYTRACING_TRANSMITTANCE 0.25f");
                sb.AppendLine("#define GRAPHICS_RAYTRACING_COLOR  0x005050");
            }
            else
            {
                sb.AppendLine("// GRAPHICS 已禁用（Mode 3 后台运行模式，输出 VTK 文件）");
                sb.AppendLine("// #define GRAPHICS");
                sb.AppendLine("// #define INTERACTIVE_GRAPHICS");
            }
            sb.AppendLine();

            // 松弛时间（由粘度和网格间距推算）
            double dx = grid.Dx;                // 格子物理尺寸（m，对应 CartesianGrid.Dx）
            double dt = dx / 1.0;               // 时间步长（使用格子单位，u_max≈0.1c）
            double nu_lbm = settings.Viscosity * dt / (dx * dx); // LBM 无量纲粘度
            double tau = 3.0 * nu_lbm + 0.5;   // 松弛时间
            tau = Math.Max(0.55, Math.Min(tau, 2.0)); // 限定在稳定范围

            sb.AppendLine("// ---- 松弛时间（由粘度自动计算）----");
            sb.AppendLine($"// nu_physical = {settings.Viscosity:E3} m²/s");
            sb.AppendLine($"// dx = {dx:F4} m, tau = {tau:F4}");
            sb.AppendLine($"#define TAU {tau.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f");
            sb.AppendLine();

            File.WriteAllText(definesPath, sb.ToString(), Encoding.UTF8);
        }

        /// <summary>
        /// 生成 setup.cpp（使用 FluidX3D 真实 API）
        /// main_setup() 函数包含完整的场景初始化逻辑
        /// 
        /// 注意：stlPath 和 outputDir 应使用相对路径（如 "buildings.stl" 和 "output"），
        /// 这样部署到 FluidX3D 目录后可正确运行。
        /// </summary>
        private void GenerateSetupCpp(Scene scene, CartesianGrid grid, SimulationSettings settings,
                                       string setupPath, string stlRelPath, string outputRelDir)
        {
            var sb = new StringBuilder();

            // 头部注释
            sb.AppendLine("// ====================================================");
            sb.AppendLine("// CityLBM 自动生成的 FluidX3D setup.cpp");
            sb.AppendLine($"// 场景: {scene.Name}");
            sb.AppendLine($"// 生成时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
            sb.AppendLine("// 风速: " + scene.WindSpeed.ToString("F2") + " m/s");
            sb.AppendLine("// 风向: " + scene.WindDirection.ToString());
            sb.AppendLine("// ====================================================");
            sb.AppendLine();
            sb.AppendLine("#include \"lbm.hpp\"");  // 正确路径：src/ 已在 include 搜索路径中
            sb.AppendLine();

            // 物理参数注释
            sb.AppendLine("// ---- 物理参数 ----");
            sb.AppendLine($"// 网格间距    dx = {grid.Dx:F3} m");
            sb.AppendLine($"// 域尺寸      {grid.Nx * grid.Dx:F1} m × {grid.Ny * grid.Dx:F1} m × {grid.Nz * grid.Dx:F1} m");
            sb.AppendLine($"// 入口风速    {scene.WindSpeed:F2} m/s");
            sb.AppendLine($"// 运动粘度    {settings.Viscosity:E3} m²/s");
            double re = scene.WindSpeed * grid.Dx * grid.Nx / settings.Viscosity;
            sb.AppendLine($"// Re ≈        {re:F0}");
            sb.AppendLine();

            // LBM 无量纲速度（格子单位）
            double uMax = 0.1; // LBM 稳定上限约 0.1c
            double uScale = uMax / Math.Max(scene.WindSpeed, 0.001);
            var windDir = scene.WindDirection;
            windDir.Unitize();
            double ulbm_x = windDir.X * uMax;
            double ulbm_y = windDir.Y * uMax;
            double ulbm_z = Math.Max(0, windDir.Z * uMax);

            // LBM 运动粘度（格子单位）：从 TAU 反算，nu = (TAU-0.5)/3
            // 实际上 defines.hpp 已经定义了 TAU，这里只是注释用
            double nu_lbm_val = (3.0 * settings.Viscosity * 1.0 / (grid.Dx * grid.Dx));
            double tau_val = 3.0 * nu_lbm_val + 0.5;
            tau_val = Math.Max(0.55, Math.Min(tau_val, 2.0));
            double nu_final = (tau_val - 0.5) / 3.0;

            sb.AppendLine("void main_setup() {");
            sb.AppendLine($"    // LBM 物理参数 (u_max = {uMax}, tau = {tau_val:F4}, nu = {nu_final:E4})");
            sb.AppendLine($"    const float u_x = {ulbm_x.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float u_y = {ulbm_y.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float u_z = {ulbm_z.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
            sb.AppendLine();

            // 正确：LBM 构造函数参数是 nu（LBM 运动粘度），不是 TAU
            sb.AppendLine("    // 初始化 LBM（参数：Nx, Ny, Nz, nu_lbm）");
            sb.AppendLine($"    // nu_lbm = (TAU-0.5)/3 = ({tau_val:F4}-0.5)/3 = {nu_final:F6}");
            sb.AppendLine($"    LBM lbm(SX, SY, SZ, {nu_final.ToString("F8", System.Globalization.CultureInfo.InvariantCulture)}f);");
            sb.AppendLine();

            // 边界条件（parallel_for 是 FluidX3D 推荐的并行初始化方式）
            sb.AppendLine("    // 初始化边界条件和速度场（parallel_for 并行）");
            sb.AppendLine("    const uint Nx = lbm.get_Nx(), Ny = lbm.get_Ny(), Nz = lbm.get_Nz();");
            sb.AppendLine("    parallel_for(lbm.get_N(), [&](ulong n) {");
            sb.AppendLine("        uint x=0u, y=0u, z=0u;");
            sb.AppendLine("        lbm.coordinates(n, x, y, z);");
            sb.AppendLine();
            sb.AppendLine("        // 地面（z=0）：无滑移壁面");
            sb.AppendLine("        if(z == 0u) {");
            sb.AppendLine("            lbm.flags[n] = TYPE_S;");
            sb.AppendLine("            return;  // parallel_for lambda 用 return 代替 continue");
            sb.AppendLine("        }");
            sb.AppendLine();
            GenerateInletOutletCode(sb, windDir, grid);
            sb.AppendLine();
            sb.AppendLine("        // 初始化速度场（均匀来流）");
            sb.AppendLine("        lbm.u.x[n] = u_x;");
            sb.AppendLine("        lbm.u.y[n] = u_y;");
            sb.AppendLine("        lbm.u.z[n] = u_z;");
            sb.AppendLine("    });");
            sb.AppendLine();

            // [FIX] 必须在 voxelize_stl 之前 write_to_device！
            // 原因：FluidX3D 的 voxelize_mesh_on_device() 内部在 !initialized 时
            // 会调用 u.read_from_device()，把 GPU 端的 u（此时还是 reset(0) 的零值）
            // 覆盖到 CPU 端，导致之前 parallel_for 设置的速度全部丢失！
            sb.AppendLine("    // [FIX] 必须在 voxelize_stl 之前 write_to_device！");
            sb.AppendLine("    // 原因：FluidX3D 的 voxelize_mesh_on_device() 内部在 !initialized 时");
            sb.AppendLine("    // 会调用 u.read_from_device()，把 GPU 端的 u（此时还是 reset(0) 的零值）");
            sb.AppendLine("    // 覆盖到 CPU 端，导致之前 parallel_for 设置的速度全部丢失！");
            sb.AppendLine("    lbm.flags.write_to_device();");
            sb.AppendLine("    lbm.u.write_to_device();");
            sb.AppendLine();

            // STL 体素化
            sb.AppendLine("    // 导入建筑物 STL（体素化为固体壁面 TYPE_S）");
            sb.AppendLine($"    lbm.voxelize_stl(\"{stlRelPath}\", lbm.center(), float3x3(1.0f));");
            sb.AppendLine();

            // 输出目录（相对路径，部署后在 FluidX3D 根目录下）
            sb.AppendLine($"    // VTK 输出目录: {outputRelDir}/");
            sb.AppendLine();

            // 主模拟循环
            // GRAPHICS 模式：使用 lbm.run() 自动管理渲染循环（内部集成图形刷新）
            // 非 GRAPHICS 模式：手动 while 循环 + VTK 输出
            sb.AppendLine("    // ── 主模拟循环 ──");
            sb.AppendLine("#if defined(GRAPHICS) && defined(INTERACTIVE_GRAPHICS)");
            sb.AppendLine("    // 交互式图形模式：lbm.run() 内部自动渲染每一帧");
            sb.AppendLine("    // 按键：P=暂停/继续, Esc=退出");
            sb.AppendLine("    lbm.graphics.visualization_modes = VIS_FLAG_SURFACE|VIS_Q_CRITERION;");
            sb.AppendLine($"    lbm.run({settings.TimeSteps}u);  // 持续模拟直到 TimeSteps");
            sb.AppendLine("#else // 非 GRAPHICS 模式：手动循环 + VTK 输出");
            sb.AppendLine($"    lbm.run(0u);  // 初始化（0步）");
            sb.AppendLine();
            sb.AppendLine($"    while(lbm.get_t() < {settings.TimeSteps}u) {{");
            sb.AppendLine($"        uint remaining = {settings.TimeSteps}u - (uint)lbm.get_t();");
            sb.AppendLine($"        uint steps_to_run = remaining < {settings.SaveInterval}u ? remaining : {settings.SaveInterval}u;");
            sb.AppendLine("        lbm.run(steps_to_run);");
            sb.AppendLine();
            sb.AppendLine("        // 输出 VTK（速度场）到指定目录");
            sb.AppendLine($"        // path 只传目录前缀，default_filename() 会自动拼接 name-timestep.vtk");
            sb.AppendLine($"        lbm.u.write_device_to_vtk(\"{outputRelDir}/\", true);  // true=自动转换为 SI 物理单位(m/s)");
            sb.AppendLine();
            sb.AppendLine("        print_info(\"Step: \" + to_string(lbm.get_t()) +");
            sb.AppendLine($"                   \" / {settings.TimeSteps}\");");
            sb.AppendLine("    }");
            sb.AppendLine("#endif // GRAPHICS");
            sb.AppendLine("}");

            File.WriteAllText(setupPath, sb.ToString(), Encoding.UTF8);
        }

        private void GenerateInletOutletCode(StringBuilder sb, Vector3d windDir, CartesianGrid grid)
        {
            bool xDominant = Math.Abs(windDir.X) >= Math.Abs(windDir.Y);

            if (xDominant)
            {
                bool windFromMinX = windDir.X > 0;
                sb.AppendLine("        // 入口/出口边界（X 方向主导风）");
                if (windFromMinX)
                {
                    sb.AppendLine("        if(x == 0u)  { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口：设置来流速度");
                    sb.AppendLine("        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                }
                else
                {
                    sb.AppendLine("        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口：设置来流速度");
                    sb.AppendLine("        if(x == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                }
                sb.AppendLine("        // Y 方向侧面：自由滑移");
                sb.AppendLine("        if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }");
            }
            else
            {
                bool windFromMinY = windDir.Y > 0;
                sb.AppendLine("        // 入口/出口边界（Y 方向主导风）");
                if (windFromMinY)
                {
                    sb.AppendLine("        if(y == 0u)  { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口：设置来流速度");
                    sb.AppendLine("        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                }
                else
                {
                    sb.AppendLine("        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口：设置来流速度");
                    sb.AppendLine("        if(y == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                }
                sb.AppendLine("        // X 方向侧面：自由滑移");
                sb.AppendLine("        if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }");
            }
            sb.AppendLine("        // 顶面：自由出流");
            sb.AppendLine("        if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }");
        }

        #endregion

        #region Private — Helpers

        private void BackupOriginalFiles(string fluidSrcDir)
        {
            string backupDir = Path.Combine(Path.GetDirectoryName(fluidSrcDir), ".citylbm_backup");
            Directory.CreateDirectory(backupDir);

            string[] filesToBackup = { "setup.cpp", "defines.hpp" };
            foreach (string file in filesToBackup)
            {
                string srcFile = Path.Combine(fluidSrcDir, file);
                string dstFile = Path.Combine(backupDir, file + ".original");
                if (File.Exists(srcFile) && !File.Exists(dstFile))
                {
                    File.Copy(srcFile, dstFile);
                }
            }
        }

        private string GenerateInstructions(string caseDir, bool autoDeploy)
        {
            var sb = new StringBuilder();

            if (autoDeploy)
            {
                // 已自动部署：只需告诉用户双击运行
                sb.AppendLine("═══════════════════════════════════════════════════════");
                sb.AppendLine("  CityLBM — 文件已自动部署 ✓");
                sb.AppendLine("═══════════════════════════════════════════════════════");
                sb.AppendLine();
                sb.AppendLine("✅ 已完成的步骤：");
                sb.AppendLine($"  ✓ setup.cpp  → {FluidX3DPath}\\src\\setup.cpp");
                sb.AppendLine($"  ✓ defines.hpp → {FluidX3DPath}\\src\\defines.hpp");
                sb.AppendLine($"  ✓ buildings.stl → {FluidX3DPath}\\buildings.stl");
                sb.AppendLine($"  ✓ output/ 目录已创建");
                sb.AppendLine($"  ✓ 一键脚本 → {FluidX3DPath}\\run_citylbm.bat");
                sb.AppendLine();
                sb.AppendLine("▶  下一步（二选一）：");
                sb.AppendLine();
                sb.AppendLine("  方法 A — 一键脚本（推荐）：");
                sb.AppendLine($"    双击运行：{FluidX3DPath}\\run_citylbm.bat");
                sb.AppendLine("    脚本将自动：编译 → 运行 → 收集结果");
                sb.AppendLine();
                sb.AppendLine("  方法 B — 手动：");
                sb.AppendLine("    1. 打开 Visual Studio → FluidX3D.sln → Build → Release x64");
                sb.AppendLine("    2. 运行 FluidX3D.exe");
                sb.AppendLine();
                sb.AppendLine("📂 结果读取路径（供 Read VTK 组件使用）：");
                sb.AppendLine($"   {Path.Combine(caseDir, "output")}");
                sb.AppendLine("   （运行完成后脚本会自动将 VTK 结果复制到此）");
                sb.AppendLine("═══════════════════════════════════════════════════════");
            }
            else
            {
                // 未自动部署：显示完整手动步骤
                sb.AppendLine("═══════════════════════════════════════════════════════");
                sb.AppendLine("  CityLBM — 手动集成 FluidX3D 步骤");
                sb.AppendLine("═══════════════════════════════════════════════════════");
                sb.AppendLine();
                sb.AppendLine("📁 Case 文件已生成到：");
                sb.AppendLine($"   {caseDir}");
                sb.AppendLine();
                sb.AppendLine("💡 提示：在 FX3D 输入端填写 FluidX3D 源码路径可跳过步骤 1-4。");
                sb.AppendLine();
                sb.AppendLine("📋 手动步骤：");
                sb.AppendLine();
                sb.AppendLine("  步骤 1 — 复制 setup.cpp");
                sb.AppendLine($"    从: {Path.Combine(caseDir, "setup.cpp")}");
                sb.AppendLine("    到: <FluidX3D根目录>/src/setup.cpp");
                sb.AppendLine();
                sb.AppendLine("  步骤 2 — 复制 defines.hpp");
                sb.AppendLine($"    从: {Path.Combine(caseDir, "defines.hpp")}");
                sb.AppendLine("    到: <FluidX3D根目录>/src/defines.hpp");
                sb.AppendLine();
                sb.AppendLine("  步骤 3 — 复制 buildings.stl");
                sb.AppendLine($"    从: {Path.Combine(caseDir, "buildings.stl")}");
                sb.AppendLine("    到: <FluidX3D根目录>/buildings.stl");
                sb.AppendLine();
                sb.AppendLine("  步骤 4 — 创建输出目录");
                sb.AppendLine("    在 FluidX3D 根目录下创建 output/ 文件夹");
                sb.AppendLine();
                sb.AppendLine("  步骤 5 — 编译 FluidX3D");
                sb.AppendLine("    Visual Studio: 打开 FluidX3D.sln → Build → Release x64");
                sb.AppendLine("    或命令行: msbuild FluidX3D.sln /p:Configuration=Release");
                sb.AppendLine();
                sb.AppendLine("  步骤 6 — 运行");
                sb.AppendLine("    双击 FluidX3D.exe，或在命令行运行");
                sb.AppendLine();
                sb.AppendLine("  步骤 7 — 读取结果");
                sb.AppendLine("    VTK 文件输出到: <FluidX3D根目录>/output/");
                sb.AppendLine("    将 VTK 文件复制回 Case 目录的 output/ 子文件夹");
                sb.AppendLine($"    在 Grasshopper 中使用 Read VTK 组件读取: {Path.Combine(caseDir, "output")}");
                sb.AppendLine();
                sb.AppendLine("───────────────────────────────────────────────────────");
                sb.AppendLine("💡 Case 目录结构：");
                sb.AppendLine($"   {caseDir}/");
                sb.AppendLine("   ├── setup.cpp      (FluidX3D 主程序)");
                sb.AppendLine("   ├── defines.hpp    (宏定义)");
                sb.AppendLine("   ├── buildings.stl  (建筑几何体)");
                sb.AppendLine("   └── output/        (VTK 结果文件)");
                sb.AppendLine("═══════════════════════════════════════════════════════");
            }

            return sb.ToString();
        }

        private VTKResult ParseVTKFile(string vtkPath)
        {
            var result = new VTKResult
            {
                FilePath = vtkPath,
                TimeStep = ExtractTimeStepFromFilename(vtkPath)
            };

            using (StreamReader reader = new StreamReader(vtkPath))
            {
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    line = line.Trim();

                    if (line.StartsWith("POINTS", StringComparison.OrdinalIgnoreCase))
                    {
                        string[] parts = line.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        int numPoints = int.Parse(parts[1]);
                        result.Points = new List<Point3d>(numPoints);

                        for (int i = 0; i < numPoints; i++)
                        {
                            string ptLine = reader.ReadLine()?.Trim();
                            if (ptLine == null) break;
                            var p = ptLine.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 3)
                            {
                                result.Points.Add(new Point3d(
                                    double.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture),
                                    double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture),
                                    double.Parse(p[2], System.Globalization.CultureInfo.InvariantCulture)));
                            }
                        }
                    }
                    else if (line.StartsWith("VECTORS", StringComparison.OrdinalIgnoreCase))
                    {
                        result.Velocities = new List<Vector3d>();
                        string vLine;
                        while ((vLine = reader.ReadLine()) != null)
                        {
                            vLine = vLine.Trim();
                            if (string.IsNullOrEmpty(vLine)) continue;
                            if (vLine.StartsWith("SCALARS", StringComparison.OrdinalIgnoreCase) ||
                                vLine.StartsWith("VECTORS", StringComparison.OrdinalIgnoreCase) ||
                                vLine.StartsWith("POINT_DATA", StringComparison.OrdinalIgnoreCase)) break;

                            var p = vLine.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                            if (p.Length >= 3)
                            {
                                result.Velocities.Add(new Vector3d(
                                    double.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture),
                                    double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture),
                                    double.Parse(p[2], System.Globalization.CultureInfo.InvariantCulture)));
                            }
                        }
                    }
                    else if (line.StartsWith("SCALARS", StringComparison.OrdinalIgnoreCase))
                    {
                        string[] parts = line.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                        string scalarName = parts.Length > 1 ? parts[1] : "unknown";

                        // 跳过 LOOKUP_TABLE 行
                        string nextLine = reader.ReadLine();
                        if (nextLine != null && !nextLine.Trim().StartsWith("LOOKUP_TABLE", StringComparison.OrdinalIgnoreCase))
                        {
                            // 如果不是 LOOKUP_TABLE，可能直接是数据
                        }

                        var values = new List<double>();
                        string sLine;
                        while ((sLine = reader.ReadLine()) != null)
                        {
                            sLine = sLine.Trim();
                            if (string.IsNullOrEmpty(sLine)) continue;
                            if (sLine.StartsWith("SCALARS", StringComparison.OrdinalIgnoreCase) ||
                                sLine.StartsWith("VECTORS", StringComparison.OrdinalIgnoreCase) ||
                                sLine.StartsWith("POINT_DATA", StringComparison.OrdinalIgnoreCase)) break;

                            if (double.TryParse(sLine, System.Globalization.NumberStyles.Float,
                                                System.Globalization.CultureInfo.InvariantCulture, out double val))
                            {
                                values.Add(val);
                            }
                        }
                        result.Scalars[scalarName] = values;
                    }
                }
            }

            return result;
        }

        private int ExtractTimeStepFromFilename(string filename)
        {
            string name = Path.GetFileNameWithoutExtension(filename);
            string[] parts = name.Split('_');
            if (parts.Length > 1 && int.TryParse(parts[parts.Length - 1], out int t))
                return t;
            return 0;
        }

        private string SanitizeName(string name)
        {
            foreach (char c in Path.GetInvalidFileNameChars())
                name = name.Replace(c, '_');
            return name;
        }

        #endregion
    }

    // ====================================================
    // 数据类
    // ====================================================

    /// <summary>模拟物理设置</summary>
    public class SimulationSettings
    {
        public double Viscosity { get; set; } = 1.5e-5;  // 空气运动粘度 (m²/s)
        public double Density { get; set; } = 1.225;     // 空气密度 (kg/m³)
        public int TimeSteps { get; set; } = 2000;       // 总模拟步数（默认 2000，稳态风场足够）
        public int SaveInterval { get; set; } = 1000;    // VTK 输出间隔（默认 1000，减少磁盘 IO）

        public double InletVelocityX { get; set; }
        public double InletVelocityY { get; set; }
        public double InletVelocityZ { get; set; } = 0;

        public void SetInletVelocity(Vector3d direction, double speed)
        {
            direction.Unitize();
            InletVelocityX = direction.X * speed;
            InletVelocityY = direction.Y * speed;
            InletVelocityZ = direction.Z * speed;
        }
    }

    /// <summary>部署结果</summary>
    public class DeployResult
    {
        public bool Success { get; set; }
        public string CaseDirectory { get; set; }
        public string Message { get; set; }
        public string ErrorMessage { get; set; }
        public List<string> DeployedFiles { get; set; } = new List<string>();
    }

    /// <summary>编译结果</summary>
    public class BuildResult
    {
        public bool Success { get; set; }
        public int ExitCode { get; set; }
        public string Log { get; set; }
        public string ErrorMessage { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public TimeSpan Duration => EndTime - StartTime;
    }

    /// <summary>Case 文件生成结果</summary>
    public class CaseGenerationResult
    {
        public bool Success { get; set; }
        public string CaseDirectory { get; set; }
        public string Instructions { get; set; }
        public string ErrorMessage { get; set; }
        public DateTime StartTime { get; set; }

        /// <summary>是否已自动部署到 FluidX3D 目录</summary>
        public bool AutoDeployed { get; set; }

        /// <summary>自动部署的消息（成功或失败原因）</summary>
        public string DeployMessage { get; set; }
    }

    /// <summary>求解器运行结果</summary>
    public class SolverResult
    {
        public bool Success { get; set; }
        public string CaseDirectory { get; set; }
        public string OutputDirectory { get; set; }
        public int ExitCode { get; set; }
        public string ErrorMessage { get; set; }
        public string Log { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public TimeSpan Duration => EndTime - StartTime;
    }

    /// <summary>VTK 结果数据</summary>
    public class VTKResult
    {
        public string FilePath { get; set; }
        public int TimeStep { get; set; }
        public List<Point3d> Points { get; set; }
        public List<Vector3d> Velocities { get; set; }
        public Dictionary<string, List<double>> Scalars { get; set; } = new Dictionary<string, List<double>>();

        /// <summary>VTK 文件中的原始点总数（采样前）</summary>
        public int RawPointCount { get; set; }

        public int PointCount => Points?.Count ?? 0;
        public int VelocityCount => Velocities?.Count ?? 0;
    }
}
