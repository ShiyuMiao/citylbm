using System;
using System.IO;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Security.Cryptography;
using Rhino.Geometry;
using CityLBM.Core;
using Newtonsoft.Json;
using System.Globalization;

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
        private const int MinimumRecommendedAveragingFrames = 20;
        private const int PaperRecommendedAveragingFrames = 40;
        private const int PaperRecommendedAverageStepSpan = 20000;
        private const int PaperRecommendedStgRefreshes = 200;

        #region Properties

        /// <summary>FluidX3D 源码根目录（包含 FluidX3D.sln 或 Makefile）</summary>
        public string FluidX3DPath { get; set; }

        /// <summary>True when the user explicitly supplied FluidX3DPath instead of auto-detection.</summary>
        public bool HasExplicitFluidX3DPath { get; private set; }

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
            HasExplicitFluidX3DPath = !string.IsNullOrEmpty(FluidX3DPath);
            
            // 如果未提供路径，尝试自动检测
            if (string.IsNullOrEmpty(FluidX3DPath))
            {
                FluidX3DPath = AutoDetectFluidX3DPath();
            }
            
            WorkingDirectory = Path.Combine(Path.GetTempPath(), "CityLBM");

            if (!Directory.Exists(WorkingDirectory))
                Directory.CreateDirectory(WorkingDirectory);
        }

        #region v0.5.0 — Bundled Solver Mode

        private bool _bundlerInitAttempted;
        private bool _bundlerAvailable;

        public bool UseBundledSolver { get; set; }

        public bool IsBundlerAvailable
        {
            get
            {
                if (!_bundlerInitAttempted)
                {
                    _bundlerInitAttempted = true;
                    _bundlerAvailable = FluidX3DBundler.Instance.EnsureInitialized();
                }
                return _bundlerAvailable;
            }
        }

        public SolverResult RunWithBundledSolver(Scene scene, CartesianGrid grid, SimulationSettings settings,
                                                  Action<int, string> progressCallback = null,
                                                  CancellationToken cancellationToken = default)
        {
            var result = new SolverResult { StartTime = DateTime.Now };
            var log = new StringBuilder();

            log.AppendLine("=== CityLBM Bundled Solver v0.5.0 ===");
            log.AppendLine("Scene: " + (scene?.Name ?? "null"));
            log.AppendLine("Time: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            log.AppendLine();

            if (!IsBundlerAvailable)
            {
                result.Success = false;
                result.ErrorMessage = "FluidX3D Bundler init failed.\n" + FluidX3DBundler.Instance.GetInitLog();
                result.Log = log.ToString();
                result.EndTime = DateTime.Now;
                return result;
            }

            cancellationToken.ThrowIfCancellationRequested();

            log.AppendLine("[1/4] Generating case files...");
            string caseDir;
            try
            {
                caseDir = GenerateCase(scene, grid, settings, enableGraphics: false);
                log.AppendLine("      Case dir: " + caseDir);
                cancellationToken.ThrowIfCancellationRequested();
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = "Case generation failed: " + ex.Message;
                result.Log = log.ToString();
                result.EndTime = DateTime.Now;
                return result;
            }

            string definesPath = Path.Combine(caseDir, "defines.hpp");
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            string stlPath = Path.Combine(caseDir, "buildings.stl");

            if (!File.Exists(definesPath) || !File.Exists(setupPath))
            {
                result.Success = false;
                result.ErrorMessage = "Generated case files not found.";
                result.Log = log.ToString();
                result.EndTime = DateTime.Now;
                return result;
            }

            string definesContent = File.ReadAllText(definesPath, Encoding.UTF8);
            string setupContent = File.ReadAllText(setupPath, Encoding.UTF8);

            log.AppendLine("[2/4] Getting FluidX3D binary (bundled)...");
            string exePath = FluidX3DBundler.Instance.GetOrBuildExe(
                grid.Nx, grid.Ny, grid.Nz,
                definesContent, setupContent, stlPath,
                (pct, msg) => progressCallback?.Invoke(pct / 2, msg));

            if (string.IsNullOrEmpty(exePath))
            {
                result.Success = false;
                result.ErrorMessage = "Failed to get/build FluidX3D binary.";
                result.CaseDirectory = caseDir;
                result.Log = log.ToString();
                result.EndTime = DateTime.Now;
                return result;
            }
            log.AppendLine("      Binary: " + exePath);

            log.AppendLine("[3/4] Running simulation...");
            string buildDir = Path.GetDirectoryName(exePath);

            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = exePath,
                    WorkingDirectory = buildDir,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using (var process = new Process { StartInfo = psi })
                {
                    process.OutputDataReceived += (s, e) => { if (e.Data != null) log.AppendLine(e.Data); };
                    process.ErrorDataReceived += (s, e) => { if (e.Data != null) log.AppendLine("[ERR] " + e.Data); };
                    process.Start();
                    process.BeginOutputReadLine();
                    process.BeginErrorReadLine();
                    int dc = 0;
                    while (!process.HasExited)
                    {
                        if (cancellationToken.IsCancellationRequested)
                        {
                            try { process.Kill(); } catch { }
                            throw new OperationCanceledException();
                        }
                        process.WaitForExit(2000);
                        dc++;
                        progressCallback?.Invoke(Math.Min(50 + dc * 2, 95), "Simulating...");
                    }
                    result.ExitCode = process.ExitCode;
                    result.Success = process.ExitCode == 0;
                }
            }
            catch (OperationCanceledException)
            {
                result.Success = false;
                result.ErrorMessage = "用户取消了操作";
                result.CaseDirectory = caseDir;
                result.Log = log.ToString();
                result.EndTime = DateTime.Now;
                return result;
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.ErrorMessage = "Simulation failed: " + ex.Message;
                result.Log = log.ToString();
                result.CaseDirectory = caseDir;
                result.EndTime = DateTime.Now;
                return result;
            }

            log.AppendLine("[4/4] Collecting VTK results...");
            result.CaseDirectory = caseDir;
            string outputDir = Path.Combine(buildDir, "output");
            string caseOutputDir = Path.Combine(caseDir, "output");
            try
            {
                if (Directory.Exists(outputDir))
                {
                    Directory.CreateDirectory(caseOutputDir);
                    foreach (var f in Directory.GetFiles(outputDir, "*.vtk"))
                        File.Copy(f, Path.Combine(caseOutputDir, Path.GetFileName(f)), overwrite: true);
                    foreach (var f in Directory.GetFiles(outputDir, "*.vtu"))
                        File.Copy(f, Path.Combine(caseOutputDir, Path.GetFileName(f)), overwrite: true);
                }
                result.OutputDirectory = caseOutputDir;
            }
            catch { result.OutputDirectory = outputDir; }

            result.Log = log.ToString();
            result.EndTime = DateTime.Now;
            progressCallback?.Invoke(100, result.Success ? "Simulation complete!" : "Simulation failed.");
            return result;
        }

        #endregion
        
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
            return ValidateFluidX3DSourcePath(path, out _).IsValid;
        }

        public FluidX3DSourceValidation ValidateFluidX3DSourcePath(out string message)
        {
            var validation = ValidateFluidX3DSourcePath(FluidX3DPath, out message);
            return validation;
        }

        public static FluidX3DSourceValidation ValidateFluidX3DSourcePath(string path, out string message)
        {
            if (string.IsNullOrEmpty(path) || !Directory.Exists(path))
            {
                message = "FluidX3D source path is empty or does not exist.";
                return FluidX3DSourceValidation.Invalid(path, message);
            }
            
            bool hasSln = File.Exists(Path.Combine(path, "FluidX3D.sln"));
            bool hasMakefile = File.Exists(Path.Combine(path, "Makefile"));
            bool hasCMakeLists = File.Exists(Path.Combine(path, "CMakeLists.txt"));
            bool hasSrcDir = Directory.Exists(Path.Combine(path, "src"));
            bool hasSetupCpp = File.Exists(Path.Combine(path, "src", "setup.cpp"));
            bool hasDefinesHpp = File.Exists(Path.Combine(path, "src", "defines.hpp"));
            bool hasLbmHpp = File.Exists(Path.Combine(path, "src", "lbm.hpp"));
            bool hasLbmCpp = File.Exists(Path.Combine(path, "src", "lbm.cpp"));
            bool hasBuildFile = hasSln || hasMakefile || hasCMakeLists;
            
            var missing = new List<string>();
            if (!hasBuildFile) missing.Add("FluidX3D.sln/Makefile/CMakeLists.txt");
            if (!hasSrcDir) missing.Add("src/");
            if (!hasSetupCpp) missing.Add("src/setup.cpp");
            if (!hasDefinesHpp) missing.Add("src/defines.hpp");
            if (!hasLbmHpp) missing.Add("src/lbm.hpp");
            if (!hasLbmCpp) missing.Add("src/lbm.cpp");

            bool valid = missing.Count == 0;
            message = valid
                ? "FluidX3D source path is valid for controlled native-baseline deployment."
                : "FluidX3D source path is not a complete deployable source tree; missing: " + string.Join(", ", missing);

            return new FluidX3DSourceValidation
            {
                Path = path ?? "",
                IsValid = valid,
                Message = message,
                HasSolution = hasSln,
                HasMakefile = hasMakefile,
                HasCMakeLists = hasCMakeLists,
                HasSrcDirectory = hasSrcDir,
                HasSetupCpp = hasSetupCpp,
                HasDefinesHpp = hasDefinesHpp,
                HasLbmHpp = hasLbmHpp,
                HasLbmCpp = hasLbmCpp,
                MissingRequiredItems = missing
            };
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
            GenerateDefinesHpp(scene, grid, settings, definesPath, enableGraphics);

            // 3. 生成 setup.cpp（使用 FluidX3D 真实 API）
            // 注意：STL 和 VTK 路径使用相对路径，部署到 FluidX3D 后可正确运行
            string setupPath = Path.Combine(caseDir, "setup.cpp");
            GenerateSetupCpp(scene, grid, settings, setupPath, "buildings.stl", "output");

            // 4. 保存域原点信息（供后处理组件将 VTK 坐标映射回物理世界坐标）
            // FluidX3D VTK 输出以域中心为原点，CityLBM 使用物理世界坐标（Z 从地面=0 开始）
            SaveDomainOrigin(caseDir, grid.Origin, grid.DomainBounds, grid.Nx, grid.Ny, grid.Nz, grid.Dx);
            SaveCaseMetadata(caseDir, scene, grid, settings);
            SaveValidationProtocolAudit(caseDir, scene, grid, settings);
            SaveNativeFluidX3DBaselineManifest(caseDir, scene, grid, settings, setupPath, definesPath, stlPath);

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

            var sourceValidation = ValidateFluidX3DSourcePath(out string validationMessage);
            if (!sourceValidation.IsValid)
            {
                result.Success = false;
                result.ErrorMessage = $"FluidX3D source path is invalid for controlled validation: \"{FluidX3DPath}\"\n{validationMessage}";
                return result;
            }

            string fluidSrcDir = Path.Combine(FluidX3DPath, "src");

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

                // Only deploy automatically when the user explicitly supplied a validated source path.
                bool autoDeploy = HasExplicitFluidX3DPath && ValidateFluidX3DSourcePath(out _).IsValid;
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
        private void GenerateDefinesHpp(Scene scene, CartesianGrid grid, SimulationSettings settings, string definesPath, bool enableGraphics = true)
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

            // ── v0.2.0: Smagorinsky LES 亚格子模型（提升高 Re 精度）──
            if (settings.EnableSmagorinskyLES)
            {
                double cs = settings.SmagorinskyConstantCs;
                double prT = settings.TurbulentPrandtlNumber;
                
                sb.AppendLine("// ---- v0.2.0: Smagorinsky LES 亚格子模型 ----");
                sb.AppendLine("#define SMAGORINSKY    // 启用 Smagorinsky 亚格子湍流模型");
                sb.AppendLine();
                sb.AppendLine($"// Cs = {cs:F3} (Smagorinsky 常数，推荐范围 0.10~0.18)");
                sb.AppendLine($"// Pr_T = {prT:F2} (湍流 Prandtl 数)");
                sb.AppendLine("#define SMAGORINSKY_CS " + 
                    cs.ToString("F4", System.Globalization.CultureInfo.InvariantCulture) + "f  // Smagorinsky 常数");
                sb.AppendLine("#define SMAGORINSKY_PR_T " + 
                    prT.ToString("F2", System.Globalization.CultureInfo.InvariantCulture) + "f  // 湍流 Prandtl 数");
                sb.AppendLine();
                sb.AppendLine("// 启用 LES 后的说明：");
                sb.AppendLine("// - 高 Re 数流动精度显著提升");
                sb.AppendLine("- // 自动计算局部涡粘度: nu_t = (Cs * Delta)^2 * |S|");
                sb.AppendLine("// - 其中 |S| 为应变率张量模, Delta = 格子间距");
                sb.AppendLine("// - 注意：LES 模式下 TAU 由 BGK + Smagorinsky 耗散共同决定");
                sb.AppendLine();
            }
            else
            {
                sb.AppendLine("// ---- Smagorinsky LES（未启用，默认 BGK 模型）----");
                sb.AppendLine("// 如需高 Re 数模拟精度，请启用 EnableSmagorinskyLES 并设置 Cs");
                sb.AppendLine("// #define SMAGORINSKY");
                sb.AppendLine("// #define SMAGORINSKY_CS 0.12f");
                sb.AppendLine("// #define SMAGORINSKY_PR_T 0.5f");
                sb.AppendLine();
            }


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

            double dx = Math.Max(grid.Dx, 1.0e-9);
            double velocityScale = ComputeVelocityScaleMpsToLbm(scene);
            double nu_lbm = ComputeNuLbm(settings, grid, scene);
            double tau = ComputeTau(settings, grid, scene);

            sb.AppendLine("// ---- LBM viscosity scaling ----");
            sb.AppendLine($"// nu_physical = {settings.Viscosity:E3} m²/s");
            sb.AppendLine($"// velocity_scale_mps_to_lbm = {velocityScale:E8}");
            sb.AppendLine("// nu_lbm = nu_physical * velocity_scale_mps_to_lbm / dx");
            sb.AppendLine($"// dx = {dx:F4} m, nu_lbm = {nu_lbm:E8}, tau = {tau:F8}");
            sb.AppendLine("// CityLBM v0.3.0 does not silently clamp tau; validation gates and solver logs must prove stability.");
            sb.AppendLine($"#define TAU {tau.ToString("E8", System.Globalization.CultureInfo.InvariantCulture)}f");
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
            bool syntheticInletActive = IsSyntheticTurbulentInletActive(scene, settings);

            // 头部注释
            sb.AppendLine("// ====================================================");
            sb.AppendLine("// CityLBM 自动生成的 FluidX3D setup.cpp");
            sb.AppendLine($"// 场景: {scene.Name}");
            sb.AppendLine($"// 生成时间: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
            sb.AppendLine($"// 风廓线: {scene.WindProfile}");
            sb.AppendLine($"// 风速: {scene.WindSpeed:F2} m/s @ z_ref={scene.ReferenceHeight:F1}m");
            sb.AppendLine($"// 粗糙度: z0={scene.RoughnessLength:F2}m, alpha={scene.PowerLawAlpha:F2}");
            sb.AppendLine("// 风向: " + scene.WindDirection.ToString());
            sb.AppendLine("// ====================================================");
            sb.AppendLine();
            sb.AppendLine("#include \"lbm.hpp\"");  // 正确路径：src/ 已在 include 搜索路径中
            if (syntheticInletActive)
            {
                sb.AppendLine("#include <vector>");
            }
            sb.AppendLine();

            // 物理参数注释
            sb.AppendLine("// ---- 物理参数 ----");
            sb.AppendLine($"// 网格间距    dx = {grid.Dx:F3} m");
            sb.AppendLine($"// 域尺寸      {grid.Nx * grid.Dx:F1} m x {grid.Ny * grid.Dx:F1} m x {grid.Nz * grid.Dx:F1} m");
            sb.AppendLine($"// 参考风速    {scene.WindSpeed:F2} m/s @ z_ref={scene.ReferenceHeight:F1}m");
            sb.AppendLine($"// 风廓线      {scene.WindProfile}");
            sb.AppendLine($"// 粗糙度长度  z0 = {scene.RoughnessLength:F3} m");
            if (scene.WindProfile == WindProfileType.PowerLaw)
            {
                sb.AppendLine($"// 幂律指数    alpha = {scene.PowerLawAlpha:F2}");
                sb.AppendLine($"// 公式        U(z) = {scene.WindSpeed:F2} * (z/{scene.ReferenceHeight:F1})^{scene.PowerLawAlpha:F2}");
            }
            else if (scene.WindProfile == WindProfileType.Logarithmic)
            {
                double kappa = scene.VonKarmanConstant;
                double zRef = scene.ReferenceHeight;
                double z0 = scene.RoughnessLength;
                double uStar = scene.WindSpeed * kappa / Math.Log(zRef / z0);
                sb.AppendLine($"// von Karman   kappa = {kappa}");
                sb.AppendLine($"// 摩擦速度    u* = {uStar:F3} m/s");
                sb.AppendLine($"// 公式        U(z) = ({uStar:F3}/{kappa}) * ln(z/{z0:F3})");
            }
            sb.AppendLine($"// 运动粘度    {settings.Viscosity:E3} m2/s");
            double re = scene.WindSpeed * grid.Dx * grid.Nx / settings.Viscosity;
            sb.AppendLine($"// Re ~         {re:F0}");
            sb.AppendLine();

            // LBM 无量纲速度（格子单位）
            double uMax = TargetMaxProfileVelocityLbm; // LBM 稳定上限约 0.1c
            double uScale = ComputeVelocityScaleMpsToLbm(scene);
            var windDir = NormalizeWindDirection(scene.WindDirection);
            double ulbm_x = windDir.X * uMax;
            double ulbm_y = windDir.Y * uMax;
            double ulbm_z = Math.Max(0, windDir.Z * uMax);

            // LBM viscosity in lattice units. Do not clamp this value here; stability is audited from tau and solver logs.
            double nu_final = ComputeNuLbm(settings, grid, scene);
            double tau_val = ComputeTau(settings, grid, scene);

            sb.AppendLine("void main_setup() {");
            sb.AppendLine($"    // LBM 物理参数 (u_max = {uMax}, tau = {tau_val:F4}, nu = {nu_final:E4})");

            // 根据风廓线类型生成不同的 C++ 变量和函数
            if (scene.WindProfile == WindProfileType.Uniform)
            {
                sb.AppendLine($"    const float u_x = {ulbm_x.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float u_y = {ulbm_y.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float u_z = {ulbm_z.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
            }
            else if (scene.WindProfile == WindProfileType.PowerLaw)
            {
                double alpha = scene.PowerLawAlpha;
                double zRefCells = scene.ReferenceHeight / grid.Dx;
                sb.AppendLine("    // 幂律风廓线: U(z) = U_ref * (z / z_ref) ^ alpha");
                sb.AppendLine($"    const float U_ref = {uMax.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float z_ref = {zRefCells.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float alpha = {alpha.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_x = {windDir.X.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_y = {windDir.Y.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_z = {Math.Max(0, windDir.Z).ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine();
                sb.AppendLine("    // 风廓线速度计算函数 (C++ lambda)");
                sb.AppendLine("    auto windProfile = [&](uint z_cell) -> float3 {");
                sb.AppendLine("        float z = (float)(z_cell + 0.5f);");
                sb.AppendLine("        float u_mag = U_ref * powf(z / z_ref, alpha);");
                sb.AppendLine("        return float3(dir_x * u_mag, dir_y * u_mag, dir_z * u_mag);");
                sb.AppendLine("    };");
            }
            else if (scene.WindProfile == WindProfileType.Logarithmic)
            {
                double kappa = scene.VonKarmanConstant;
                double z0Cells = scene.RoughnessLength / grid.Dx;
                double zRefCells = scene.ReferenceHeight / grid.Dx;
                double uStarLBM = uMax * kappa / Math.Log(zRefCells / z0Cells);
                sb.AppendLine("    // 对数律风廓线: U(z) = (u* / kappa) * ln(z / z0)");
                sb.AppendLine($"    const float u_star = {uStarLBM.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float kappa = {kappa.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float z0 = {z0Cells.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_x = {windDir.X.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_y = {windDir.Y.ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine($"    const float dir_z = {Math.Max(0, windDir.Z).ToString("F6", System.Globalization.CultureInfo.InvariantCulture)}f;");
                sb.AppendLine();
                sb.AppendLine("    // 风廓线速度计算函数 (C++ lambda)");
                sb.AppendLine("    auto windProfile = [&](uint z_cell) -> float3 {");
                sb.AppendLine("        float z = (float)(z_cell + 0.5f);");
                sb.AppendLine("        if(z <= z0) return float3(0.0f, 0.0f, 0.0f);");
                sb.AppendLine("        float u_mag = (u_star / kappa) * logf(z / z0);");
                sb.AppendLine("        return float3(dir_x * u_mag, dir_y * u_mag, dir_z * u_mag);");
                sb.AppendLine("    };");
            }
            else if (scene.WindProfile == WindProfileType.CustomTable)
            {
                AppendCustomTableProfileCode(sb, scene, grid.Dx, grid.Origin.Z, uScale, windDir);
            }
            sb.AppendLine();

            // 正确：LBM 构造函数参数是 nu（LBM 运动粘度），不是 TAU
            sb.AppendLine("    // 初始化 LBM（参数：Nx, Ny, Nz, nu_lbm）");
            sb.AppendLine($"    // velocity_scale_mps_to_lbm = {uScale:E8}; nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx = {nu_final:E8}; tau = {tau_val:F8}");
            sb.AppendLine("    // CityLBM v0.3.0 no longer clamps tau to 0.55; validation gates and solver logs must prove stability.");
            sb.AppendLine($"    LBM lbm(SX, SY, SZ, {nu_final.ToString("E8", System.Globalization.CultureInfo.InvariantCulture)}f);");

            // ── v0.2.0: Smagorinsky LES 模型初始化 ──
            if (settings.EnableSmagorinskyLES)
            {
                double cs = settings.SmagorinskyConstantCs;
                double prT = settings.TurbulentPrandtlNumber;
                
                sb.AppendLine();
                sb.AppendLine("    // ── v0.2.0: Smagorinsky LES 亚格子模型初始化 ──");
                sb.AppendLine("#if defined(SMAGORINSKY)");
                sb.AppendLine($"    lbm.set_smagorinsky_cs({cs.ToString("F4", System.Globalization.CultureInfo.InvariantCulture)}f);  // Smagorinsky 常数 Cs={cs}");
                sb.AppendLine($"    lbm.set_turbulent_prandtl({prT.ToString("F2", System.Globalization.CultureInfo.InvariantCulture)}f);  // 湍流 Prandtl 数 Pr_T={prT}");
                sb.AppendLine("    // Smagorinsky 模型将自动计算局部涡粘度:");
                sb.AppendLine("    //   nu_t(x) = (Cs * Delta)^2 * |S(x)|");
                sb.AppendLine("    //   其中 |S| 为应变率张量模, Delta = 格子间距");
                sb.AppendLine("#endif // SMAGORINSKY");
                sb.AppendLine();
            }

            sb.AppendLine();

            // 边界条件（parallel_for 是 FluidX3D 推荐的并行初始化方式）
            sb.AppendLine("    // 初始化边界条件和速度场（parallel_for 并行）");
            sb.AppendLine("    const uint Nx = lbm.get_Nx(), Ny = lbm.get_Ny(), Nz = lbm.get_Nz();");
            if (syntheticInletActive)
            {
                AppendSyntheticTurbulentInletVelocityCode(sb, settings, grid.Dx);
                AppendSyntheticTurbulentInletApplyCode(sb, windDir);
            }
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

            GenerateInletOutletCode(sb, windDir, grid, scene, syntheticInletActive);
            sb.AppendLine();

            // 初始化速度场
            if (scene.WindProfile == WindProfileType.Uniform)
            {
                sb.AppendLine("        // 初始化速度场（均匀来流）");
                sb.AppendLine("        lbm.u.x[n] = u_x;");
                sb.AppendLine("        lbm.u.y[n] = u_y;");
                sb.AppendLine("        lbm.u.z[n] = u_z;");
            }
            else
            {
                sb.AppendLine("        // 初始化速度场（按风廓线）");
                sb.AppendLine("        float3 u_profile = windProfile(z);");
                sb.AppendLine("        lbm.u.x[n] = u_profile.x;");
                sb.AppendLine("        lbm.u.y[n] = u_profile.y;");
                sb.AppendLine("        lbm.u.z[n] = u_profile.z;");
            }
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
            AppendEquilibriumBoundaryVelocityInitialization(sb, scene.WindProfile);
            sb.AppendLine();
            sb.AppendLine("    lbm.flags.write_to_device();");
            sb.AppendLine("    lbm.u.write_to_device();");
            sb.AppendLine();

            // STL 体素化
            // 注意：STL 文件中的坐标是 Rhino 世界坐标系（物理单位：米）
            // 需要转换为 LBM 内部坐标系（格子单位）
            // LBM 内部坐标 = (Rhino 世界坐标 - DomainOrigin) / Dx
            // voxelize_stl 的 offset 参数是加到 STL 坐标上的偏移量
            // 所以我们需要传入 -DomainOrigin/Dx，这样 STL 坐标 + offset = (STL - DomainOrigin)/Dx
            sb.AppendLine("    // 导入建筑物 STL（体素化为固体壁面 TYPE_S）");
            sb.AppendLine($"    // 坐标变换：Rhino 世界坐标(m) → LBM 内部坐标(格子)");
            sb.AppendLine($"    // DomainOrigin: ({grid.Origin.X:F2}, {grid.Origin.Y:F2}, {grid.Origin.Z:F2}) m");
            sb.AppendLine($"    // Dx: {grid.Dx:F4} m/格子");
            sb.AppendLine($"    float3 stl_offset = float3({(-grid.Origin.X/grid.Dx):F4}f, {(-grid.Origin.Y/grid.Dx):F4}f, {(-grid.Origin.Z/grid.Dx):F4}f);  // -DomainOrigin/Dx");
            sb.AppendLine($"    lbm.voxelize_stl(\"{stlRelPath}\", stl_offset, float3x3(1.0f));");
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
            if (syntheticInletActive)
            {
                sb.AppendLine("    // CityLBM v0.3.0 validation fix: GRAPHICS mode uses the same STG refresh loop as batch mode.");
                sb.AppendLine($"    while(lbm.get_t() < {settings.TimeSteps}u) {{");
                sb.AppendLine($"        uint remaining = {settings.TimeSteps}u - (uint)lbm.get_t();");
                sb.AppendLine("        uint steps_to_run = remaining < citylbm_stg_update_interval ? remaining : citylbm_stg_update_interval;");
                sb.AppendLine("        applySyntheticTurbulentInlet((uint)lbm.get_t());");
                sb.AppendLine("        lbm.run(steps_to_run);");
                sb.AppendLine("    }");
            }
            else
            {
                sb.AppendLine($"    lbm.run({settings.TimeSteps}u);  // 持续模拟直到 TimeSteps");
            }
            sb.AppendLine("#else // 非 GRAPHICS 模式：手动循环 + VTK 输出");
            sb.AppendLine($"    lbm.run(0u);  // 初始化（0步）");
            sb.AppendLine();
            sb.AppendLine($"    while(lbm.get_t() < {settings.TimeSteps}u) {{");
            sb.AppendLine($"        uint remaining = {settings.TimeSteps}u - (uint)lbm.get_t();");
            sb.AppendLine($"        uint steps_to_run = remaining < {settings.SaveInterval}u ? remaining : {settings.SaveInterval}u;");
            if (syntheticInletActive)
            {
                sb.AppendLine($"        uint save_remainder = (uint)lbm.get_t() % {settings.SaveInterval}u;");
                sb.AppendLine($"        uint until_next_save = save_remainder == 0u ? {settings.SaveInterval}u : {settings.SaveInterval}u - save_remainder;");
                sb.AppendLine("        if(steps_to_run > until_next_save) steps_to_run = until_next_save;");
                sb.AppendLine("        if(steps_to_run > citylbm_stg_update_interval) steps_to_run = citylbm_stg_update_interval;");
            }
            if (syntheticInletActive)
            {
                sb.AppendLine("        applySyntheticTurbulentInlet((uint)lbm.get_t());");
            }
            sb.AppendLine("        lbm.run(steps_to_run);");
            sb.AppendLine();
            if (syntheticInletActive)
            {
                sb.AppendLine($"        if((uint)lbm.get_t() % {settings.SaveInterval}u == 0u || (uint)lbm.get_t() >= {settings.TimeSteps}u) {{");
            }
            sb.AppendLine("        // 输出 VTK（速度场）到指定目录");
            sb.AppendLine($"        // path 只传目录前缀，default_filename() 会自动拼接 name-timestep.vtk");
            sb.AppendLine($"        lbm.u.write_device_to_vtk(\"{outputRelDir}/\", true);  // true=自动转换为 SI 物理单位(m/s)");
            if (syntheticInletActive)
            {
                sb.AppendLine("        }");
            }
            sb.AppendLine();
            sb.AppendLine("        print_info(\"Step: \" + to_string(lbm.get_t()) +");
            sb.AppendLine($"                   \" / {settings.TimeSteps}\");");
            sb.AppendLine("    }");
            sb.AppendLine("#endif // GRAPHICS");
            sb.AppendLine("}");

            File.WriteAllText(setupPath, sb.ToString(), Encoding.UTF8);
        }

        private void GenerateInletOutletCode(StringBuilder sb, Vector3d windDir, CartesianGrid grid, Scene scene, bool syntheticInletActive)
        {
            bool xDominant = Math.Abs(windDir.X) >= Math.Abs(windDir.Y);

            if (scene.WindProfile == WindProfileType.Uniform)
            {
                // 均匀来流（向后兼容，使用 u_x/u_y/u_z 常量）
                if (xDominant)
                {
                    bool windFromMinX = windDir.X > 0;
                    sb.AppendLine("        // 入口/出口边界（X 方向主导风，均匀来流）");
                    if (windFromMinX)
                    {
                        sb.AppendLine("        if(x == 0u)  { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口");
                        sb.AppendLine("        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    else
                    {
                        sb.AppendLine("        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口");
                        sb.AppendLine("        if(x == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    sb.AppendLine("        // Y 方向侧面：自由滑移");
                    sb.AppendLine("        if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }");
                }
                else
                {
                    bool windFromMinY = windDir.Y > 0;
                    sb.AppendLine("        // 入口/出口边界（Y 方向主导风，均匀来流）");
                    if (windFromMinY)
                    {
                        sb.AppendLine("        if(y == 0u)  { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口");
                        sb.AppendLine("        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    else
                    {
                        sb.AppendLine("        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; lbm.u.x[n] = u_x; lbm.u.y[n] = u_y; lbm.u.z[n] = u_z; return; }  // 入口");
                        sb.AppendLine("        if(y == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    sb.AppendLine("        // X 方向侧面：自由滑移");
                    sb.AppendLine("        if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }");
                }
            }
            else
            {
                // 风廓线模式：入口速度随高度变化，使用 windProfile(z) 函数
                if (xDominant)
                {
                    bool windFromMinX = windDir.X > 0;
                    sb.AppendLine($"        // 入口/出口边界（X 方向主导风，{scene.WindProfile} 风廓线）");
                    if (windFromMinX)
                    {
                        sb.AppendLine("        if(x == 0u)  {  // 入口：按风廓线设置速度");
                        sb.AppendLine("            lbm.flags[n] = TYPE_E;");
                        sb.AppendLine(syntheticInletActive
                            ? "            float3 u_in = syntheticTurbulentInlet(x, y, z, 0u);"
                            : "            float3 u_in = windProfile(z);");
                        sb.AppendLine("            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;");
                        sb.AppendLine("            return;");
                        sb.AppendLine("        }");
                        sb.AppendLine("        if(x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    else
                    {
                        sb.AppendLine("        if(x == Nx-1u) {  // 入口：按风廓线设置速度");
                        sb.AppendLine("            lbm.flags[n] = TYPE_E;");
                        sb.AppendLine(syntheticInletActive
                            ? "            float3 u_in = syntheticTurbulentInlet(x, y, z, 0u);"
                            : "            float3 u_in = windProfile(z);");
                        sb.AppendLine("            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;");
                        sb.AppendLine("            return;");
                        sb.AppendLine("        }");
                        sb.AppendLine("        if(x == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    sb.AppendLine("        // Y 方向侧面：自由滑移");
                    sb.AppendLine("        if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }");
                }
                else
                {
                    bool windFromMinY = windDir.Y > 0;
                    sb.AppendLine($"        // 入口/出口边界（Y 方向主导风，{scene.WindProfile} 风廓线）");
                    if (windFromMinY)
                    {
                        sb.AppendLine("        if(y == 0u)  {  // 入口：按风廓线设置速度");
                        sb.AppendLine("            lbm.flags[n] = TYPE_E;");
                        sb.AppendLine(syntheticInletActive
                            ? "            float3 u_in = syntheticTurbulentInlet(x, y, z, 0u);"
                            : "            float3 u_in = windProfile(z);");
                        sb.AppendLine("            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;");
                        sb.AppendLine("            return;");
                        sb.AppendLine("        }");
                        sb.AppendLine("        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    else
                    {
                        sb.AppendLine("        if(y == Ny-1u) {  // 入口：按风廓线设置速度");
                        sb.AppendLine("            lbm.flags[n] = TYPE_E;");
                        sb.AppendLine(syntheticInletActive
                            ? "            float3 u_in = syntheticTurbulentInlet(x, y, z, 0u);"
                            : "            float3 u_in = windProfile(z);");
                        sb.AppendLine("            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;");
                        sb.AppendLine("            return;");
                        sb.AppendLine("        }");
                        sb.AppendLine("        if(y == 0u)  { lbm.flags[n] = TYPE_E; return; }  // 出口：自由出流");
                    }
                    sb.AppendLine("        // X 方向侧面：自由滑移");
                    sb.AppendLine("        if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }");
                }
            }
            sb.AppendLine("        // 顶面：自由出流");
            sb.AppendLine("        if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }");
        }

        private void AppendEquilibriumBoundaryVelocityInitialization(StringBuilder sb, WindProfileType windProfile)
        {
            sb.AppendLine("    // CityLBM v0.3.0 validation fix: initialize all TYPE_E boundary velocities.");
            sb.AppendLine("    // Without this pass, outlet/lateral/top TYPE_E nodes can keep zero velocity after the boundary return path,");
            sb.AppendLine("    // which may add artificial damping and contribute to systematic speed-ratio underprediction.");
            sb.AppendLine("    parallel_for(lbm.get_N(), [&](ulong n) {");
            sb.AppendLine("        if(lbm.flags[n] != TYPE_E) return;");
            sb.AppendLine("        uint x=0u, y=0u, z=0u;");
            sb.AppendLine("        lbm.coordinates(n, x, y, z);");
            if (windProfile == WindProfileType.Uniform)
            {
                sb.AppendLine("        lbm.u.x[n] = u_x;");
                sb.AppendLine("        lbm.u.y[n] = u_y;");
                sb.AppendLine("        lbm.u.z[n] = u_z;");
            }
            else
            {
                sb.AppendLine("        float3 u_e = windProfile(z);");
                sb.AppendLine("        lbm.u.x[n] = u_e.x;");
                sb.AppendLine("        lbm.u.y[n] = u_e.y;");
                sb.AppendLine("        lbm.u.z[n] = u_e.z;");
            }
            sb.AppendLine("    });");
        }

        #endregion

        #region Private — Helpers

        /// <summary>
        /// 保存物理域原点信息到 JSON 文件，供后处理组件将 VTK 坐标映射回物理世界坐标。
        /// FluidX3D VTK 输出以域中心为原点（ORIGIN 为负值），
        /// 而 CityLBM 使用物理世界坐标（Z 从地面=0 开始）。
        /// 后处理组件读取此文件后计算偏移量：offset = DomainOrigin - VTK.ORIGIN
        /// </summary>
        private const double TargetMaxProfileVelocityLbm = 0.1;

        private double GetProfileScaleSpeed(Scene scene)
        {
            if (scene.WindProfile == WindProfileType.CustomTable &&
                scene.CustomWindProfile != null &&
                scene.CustomWindProfile.Count > 0)
            {
                double maxU = scene.CustomWindProfile.Max(s => s.U);
                if (maxU > 0.0)
                    return maxU;
            }

            return scene.WindSpeed;
        }

        private double ComputeVelocityScaleMpsToLbm(Scene scene)
        {
            return TargetMaxProfileVelocityLbm / Math.Max(GetProfileScaleSpeed(scene), 0.001);
        }

        private double ComputeTau(SimulationSettings settings, CartesianGrid grid, Scene scene)
        {
            return 3.0 * ComputeNuLbm(settings, grid, scene) + 0.5;
        }

        private double ComputeNuLbm(SimulationSettings settings, CartesianGrid grid, Scene scene)
        {
            double dx = Math.Max(grid.Dx, 1.0e-9);
            return settings.Viscosity * ComputeVelocityScaleMpsToLbm(scene) / dx;
        }

        private double EstimateRunReynoldsNumber(Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            return GetProfileScaleSpeed(scene) * grid.Dx * Math.Max(1, grid.Nx) / settings.Viscosity;
        }

        private void AppendCustomTableProfileCode(StringBuilder sb, Scene scene, double dx, double originZ, double uScale, Vector3d windDir)
        {
            var samples = scene.CustomWindProfile ?? new List<WindProfileSample>();
            if (samples.Count < 2)
                throw new InvalidOperationException("CustomTable profile requires at least two z,U rows.");

            sb.AppendLine("    // CustomTable wind profile from CityLBM CSV. z is SI meters in the Rhino/world vertical datum; U is converted to LBM units.");
            sb.AppendLine($"    const int profile_count = {samples.Count};");
            sb.AppendLine($"    const float profile_origin_z_m = {originZ.ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float profile_first_z_m = {samples.First().Z.ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float profile_last_z_m = {samples.Last().Z.ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine("    const float profile_z_m[profile_count] = {" + JoinFloatArray(samples.Select(s => s.Z)) + "};");
            sb.AppendLine("    const float profile_z_lbm[profile_count] = {" + JoinFloatArray(samples.Select(s => s.Z / dx)) + "};");
            sb.AppendLine("    const float profile_u_lbm[profile_count] = {" + JoinFloatArray(samples.Select(s => s.U * uScale)) + "};");
            sb.AppendLine("    const float profile_k_m2s2[profile_count] = {" + JoinFloatArray(samples.Select(s => s.HasK ? Math.Max(0.0, s.K) : 0.0)) + "};");
            sb.AppendLine("    const float profile_k_lbm[profile_count] = {" + JoinFloatArray(samples.Select(s => s.HasK ? Math.Max(0.0, s.K) * uScale * uScale : 0.0)) + "};");
            sb.AppendLine($"    const float citylbm_velocity_scale_lbm_to_mps = {(1.0 / uScale).ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float dir_x = {windDir.X.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float dir_y = {windDir.Y.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float dir_z = {Math.Max(0.0, windDir.Z).ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine("    auto interpolate_profile_u = [&](float z_m) -> float {");
            sb.AppendLine("        if(z_m <= profile_z_m[0]) return profile_u_lbm[0];");
            sb.AppendLine("        if(z_m >= profile_z_m[profile_count-1]) return profile_u_lbm[profile_count-1];");
            sb.AppendLine("        for(int i=0; i<profile_count-1; i++) {");
            sb.AppendLine("            if(z_m >= profile_z_m[i] && z_m <= profile_z_m[i+1]) {");
            sb.AppendLine("                float dz = profile_z_m[i+1] - profile_z_m[i];");
            sb.AppendLine("                if(dz < 1.0e-6f) dz = 1.0e-6f;");
            sb.AppendLine("                float t = (z_m - profile_z_m[i]) / dz;");
            sb.AppendLine("                return profile_u_lbm[i] + t * (profile_u_lbm[i+1] - profile_u_lbm[i]);");
            sb.AppendLine("            }");
            sb.AppendLine("        }");
            sb.AppendLine("        return profile_u_lbm[profile_count-1];");
            sb.AppendLine("    };");
            sb.AppendLine("    auto interpolate_profile_k = [&](float z_m) -> float {");
            sb.AppendLine("        if(z_m <= profile_z_m[0]) return profile_k_lbm[0];");
            sb.AppendLine("        if(z_m >= profile_z_m[profile_count-1]) return profile_k_lbm[profile_count-1];");
            sb.AppendLine("        for(int i=0; i<profile_count-1; i++) {");
            sb.AppendLine("            if(z_m >= profile_z_m[i] && z_m <= profile_z_m[i+1]) {");
            sb.AppendLine("                float dz = profile_z_m[i+1] - profile_z_m[i];");
            sb.AppendLine("                if(dz < 1.0e-6f) dz = 1.0e-6f;");
            sb.AppendLine("                float t = (z_m - profile_z_m[i]) / dz;");
            sb.AppendLine("                return profile_k_lbm[i] + t * (profile_k_lbm[i+1] - profile_k_lbm[i]);");
            sb.AppendLine("            }");
            sb.AppendLine("        }");
            sb.AppendLine("        return profile_k_lbm[profile_count-1];");
            sb.AppendLine("    };");
            sb.AppendLine("    auto windProfile = [&](uint z_cell) -> float3 {");
            sb.AppendLine($"        float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * {dx.ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine("        float u_mag = interpolate_profile_u(z_m);");
            sb.AppendLine("        return float3(dir_x * u_mag, dir_y * u_mag, dir_z * u_mag);");
            sb.AppendLine("    };");
            sb.AppendLine("    // k arrays are emitted for validation metadata and optional STG-lite inlet forcing.");
        }

        private bool IsSyntheticTurbulentInletActive(Scene scene, SimulationSettings settings)
        {
            return settings.EnableSyntheticTurbulentInlet &&
                   scene.WindProfile == WindProfileType.CustomTable &&
                   HasCompleteCustomKProfile(scene);
        }

        private bool HasCompleteCustomKProfile(Scene scene)
        {
            return scene.CustomWindProfile != null &&
                   scene.CustomWindProfile.Count >= 2 &&
                   scene.CustomWindProfile.All(s => s.HasK);
        }

        private string GetSyntheticTurbulentInletBlockedReason(Scene scene, SimulationSettings settings)
        {
            if (!settings.EnableSyntheticTurbulentInlet)
                return "not_requested";

            if (scene.WindProfile != WindProfileType.CustomTable)
                return "wind_profile_is_not_custom_table";

            if (scene.CustomWindProfile == null || scene.CustomWindProfile.Count < 2)
                return "custom_profile_missing_or_too_short";

            if (!HasCompleteCustomKProfile(scene))
                return "custom_profile_k_column_incomplete";

            return "not_blocked";
        }

        private string GetSyntheticTurbulenceLengthScaleSource(Scene scene, SimulationSettings settings)
        {
            if (!IsSyntheticTurbulentInletActive(scene, settings))
                return "none";

            string source = (settings.SyntheticTurbulenceLengthScaleSource ?? "").Trim();
            return string.IsNullOrEmpty(source)
                ? "user_parameter_in_lattice_cells; not derived from AIJ length-scale data or a precursor field"
                : source;
        }

        private string GetSyntheticTurbulenceLengthScaleGate(Scene scene, SimulationSettings settings)
        {
            if (!IsSyntheticTurbulentInletActive(scene, settings))
                return "not_applicable";

            return HasSupportedSyntheticTurbulenceLengthScaleSource(settings.SyntheticTurbulenceLengthScaleSource)
                ? "pass"
                : "diagnostic_only_missing_official_or_precursor_length_scale";
        }

        private bool HasSupportedSyntheticTurbulenceLengthScaleSource(string source)
        {
            if (string.IsNullOrWhiteSpace(source))
                return false;

            string text = source.ToLowerInvariant();
            string[] tokens =
            {
                "aij_length_scale_verified",
                "official_length_scale_verified",
                "precursor_length_scale",
                "recycling_length_scale",
                "digital_filter_length_scale",
                "digital-filter_length_scale",
                "synthetic_eddy_length_scale",
                "synthetic-eddy_length_scale",
                "sem_length_scale",
                "dfm_length_scale",
                "validated_length_scale_model"
            };
            return tokens.Any(token => text.Contains(token));
        }

        private void AppendSyntheticTurbulentInletVelocityCode(StringBuilder sb, SimulationSettings settings, double dx)
        {
            double scale = Math.Max(0.0, Math.Min(2.0, settings.SyntheticTurbulenceIntensityScale));
            double corr = Math.Max(1.0, Math.Min(64.0, settings.SyntheticTurbulenceCorrelationCells));
            double maxFrac = Math.Max(0.05, Math.Min(0.80, settings.SyntheticTurbulenceMaxFractionOfMean));
            double minStreamwiseFrac = Math.Max(0.0, Math.Min(0.50, settings.SyntheticTurbulenceMinStreamwiseFraction));
            int updateInterval = Math.Max(1, settings.SyntheticTurbulenceUpdateInterval);
            int modeCount = Math.Max(4, Math.Min(1024, settings.SyntheticTurbulenceModeCount));
            double[] componentNorms = ComputeSyntheticTurbulenceComponentNorms(modeCount, corr);

            sb.AppendLine();
            sb.AppendLine("    // CityLBM STG-lite inlet: deterministic spectral synthetic fluctuations from isotropic k.");
            sb.AppendLine("    // Temporal evolution uses Taylor frozen-turbulence advection along the local mean wind.");
            sb.AppendLine("    // Per-mode fluctuation vectors are projected normal to their wave vector to reduce non-physical divergence.");
            sb.AppendLine("    // This is a diagnostic approximation, not a full digital-filter/SEM/precursor inlet with Reynolds-stress tensors.");
            sb.AppendLine("    // It updates macroscopic inlet velocity fields only; distribution functions are not reconstructed here.");
            sb.AppendLine("    // Each refresh subtracts the perturbation mean per inlet z_cell so finite-mode/capped fluctuations preserve the AF mean profile by height.");
            sb.AppendLine($"    const float citylbm_stg_scale = {scale.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float citylbm_stg_corr_cells = {corr.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float citylbm_stg_max_fraction = {maxFrac.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float citylbm_stg_min_streamwise_fraction = {minStreamwiseFrac.ToString("F6", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const uint citylbm_stg_update_interval = {updateInterval}u;");
            sb.AppendLine($"    const int citylbm_stg_mode_count = {modeCount};");
            sb.AppendLine("    // Target component RMS follows isotropic k: sigma=sqrt(2k/3).");
            sb.AppendLine("    // Per-component constants are precomputed from the deterministic projected modes so finite mode counts preserve the target RMS more closely than a single sqrt(6/M) approximation.");
            sb.AppendLine($"    const float citylbm_stg_norm_x = {componentNorms[0].ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float citylbm_stg_norm_y = {componentNorms[1].ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine($"    const float citylbm_stg_norm_z = {componentNorms[2].ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine("    auto citylbm_mode_phase = [&](int mode, int component) -> float {");
            sb.AppendLine("        return 0.17320508f * (float)((mode + 1) * (component * 13 + 7));");
            sb.AppendLine("    };");
            sb.AppendLine("    auto citylbm_mode_wave = [&](int mode, int axis) -> float {");
            sb.AppendLine("        int h = ((mode + 3) * (axis * 19 + 11)) % 7 + 1;");
            sb.AppendLine("        float direction = (((mode + axis) % 2) == 0) ? 1.0f : -1.0f;");
            sb.AppendLine("        return direction * (float)h / citylbm_stg_corr_cells;");
            sb.AppendLine("    };");
            sb.AppendLine("    auto citylbm_mode_amplitude = [&](int mode, int axis) -> float {");
            sb.AppendLine("        float raw = sinf(0.75487767f * (float)((mode + 1) * (axis * 17 + 5)));");
            sb.AppendLine("        return fabsf(raw) < 0.05f ? (raw < 0.0f ? -0.05f : 0.05f) : raw;");
            sb.AppendLine("    };");
            sb.AppendLine("    auto syntheticTurbulentInlet = [&](uint x, uint y, uint z_cell, uint t_step) -> float3 {");
            sb.AppendLine("        float3 mean = windProfile(z_cell);");
            sb.AppendLine($"        float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * {dx.ToString("F8", CultureInfo.InvariantCulture)}f;");
            sb.AppendLine("        float k_lbm = interpolate_profile_k(z_m);");
            sb.AppendLine("        if(k_lbm < 0.0f) k_lbm = 0.0f;");
            sb.AppendLine("        float sigma = sqrtf(0.6666667f * k_lbm) * citylbm_stg_scale;");
            sb.AppendLine("        float mean_mag = sqrtf(mean.x*mean.x + mean.y*mean.y + mean.z*mean.z);");
            sb.AppendLine("        float cap = citylbm_stg_max_fraction * (mean_mag > 1.0e-6f ? mean_mag : 1.0e-6f);");
            sb.AppendLine("        if(sigma > cap) sigma = cap;");
            sb.AppendLine("        float advected_x = (float)x - dir_x * mean_mag * (float)t_step;");
            sb.AppendLine("        float advected_y = (float)y - dir_y * mean_mag * (float)t_step;");
            sb.AppendLine("        float advected_z = (float)z_cell - dir_z * mean_mag * (float)t_step;");
            sb.AppendLine("        float fluct_x = 0.0f, fluct_y = 0.0f, fluct_z = 0.0f;");
            sb.AppendLine("        for(int m=0; m<citylbm_stg_mode_count; m++) {");
            sb.AppendLine("            float kx = citylbm_mode_wave(m, 0);");
            sb.AppendLine("            float ky = citylbm_mode_wave(m, 1);");
            sb.AppendLine("            float kz = citylbm_mode_wave(m, 2);");
            sb.AppendLine("            float ax = citylbm_mode_amplitude(m, 0);");
            sb.AppendLine("            float ay = citylbm_mode_amplitude(m, 1);");
            sb.AppendLine("            float az = citylbm_mode_amplitude(m, 2);");
            sb.AppendLine("            float kk = kx*kx + ky*ky + kz*kz;");
            sb.AppendLine("            float ak = ax*kx + ay*ky + az*kz;");
            sb.AppendLine("            if(kk > 1.0e-12f) { ax -= ak*kx/kk; ay -= ak*ky/kk; az -= ak*kz/kk; }");
            sb.AppendLine("            float aa = sqrtf(ax*ax + ay*ay + az*az);");
            sb.AppendLine("            if(aa > 1.0e-6f) { ax /= aa; ay /= aa; az /= aa; }");
            sb.AppendLine("            float phase = kx * advected_x + ky * advected_y + kz * advected_z;");
            sb.AppendLine("            float wave = sinf(phase + citylbm_mode_phase(m, 1));");
            sb.AppendLine("            fluct_x += ax * wave;");
            sb.AppendLine("            fluct_y += ay * wave;");
            sb.AppendLine("            fluct_z += az * wave;");
            sb.AppendLine("        }");
            sb.AppendLine("        fluct_x *= citylbm_stg_norm_x;");
            sb.AppendLine("        fluct_y *= citylbm_stg_norm_y;");
            sb.AppendLine("        fluct_z *= citylbm_stg_norm_z;");
            sb.AppendLine("        float3 u = float3(mean.x + sigma * fluct_x, mean.y + sigma * fluct_y, mean.z + sigma * fluct_z);");
            sb.AppendLine("        // Default is no streamwise clipping so k-derived fluctuations are not silently truncated.");
            sb.AppendLine("        if(citylbm_stg_min_streamwise_fraction > 0.0f) {");
            sb.AppendLine("            float streamwise = u.x*dir_x + u.y*dir_y + u.z*dir_z;");
            sb.AppendLine("            float min_streamwise = citylbm_stg_min_streamwise_fraction * (mean_mag > 1.0e-6f ? mean_mag : 1.0e-6f);");
            sb.AppendLine("            if(streamwise < min_streamwise) {");
            sb.AppendLine("                float correction = min_streamwise - streamwise;");
            sb.AppendLine("                u.x += correction * dir_x;");
            sb.AppendLine("                u.y += correction * dir_y;");
            sb.AppendLine("                u.z += correction * dir_z;");
            sb.AppendLine("            }");
            sb.AppendLine("        }");
            sb.AppendLine("        return u;");
            sb.AppendLine("    };");
        }

        private static double[] ComputeSyntheticTurbulenceComponentNorms(int modeCount, double corr)
        {
            int count = Math.Max(4, Math.Min(1024, modeCount));
            double safeCorr = Math.Max(1.0, Math.Min(64.0, corr));
            double sumX = 0.0;
            double sumY = 0.0;
            double sumZ = 0.0;

            for (int mode = 0; mode < count; mode++)
            {
                double kx = SyntheticModeWave(mode, 0, safeCorr);
                double ky = SyntheticModeWave(mode, 1, safeCorr);
                double kz = SyntheticModeWave(mode, 2, safeCorr);
                double ax = SyntheticModeAmplitude(mode, 0);
                double ay = SyntheticModeAmplitude(mode, 1);
                double az = SyntheticModeAmplitude(mode, 2);
                double kk = kx * kx + ky * ky + kz * kz;
                double ak = ax * kx + ay * ky + az * kz;
                if (kk > 1.0e-12)
                {
                    ax -= ak * kx / kk;
                    ay -= ak * ky / kk;
                    az -= ak * kz / kk;
                }

                double aa = Math.Sqrt(ax * ax + ay * ay + az * az);
                if (aa > 1.0e-6)
                {
                    ax /= aa;
                    ay /= aa;
                    az /= aa;
                }

                sumX += ax * ax;
                sumY += ay * ay;
                sumZ += az * az;
            }

            double fallback = Math.Sqrt(6.0 / count);
            return new[]
            {
                sumX > 1.0e-12 ? Math.Sqrt(2.0 / sumX) : fallback,
                sumY > 1.0e-12 ? Math.Sqrt(2.0 / sumY) : fallback,
                sumZ > 1.0e-12 ? Math.Sqrt(2.0 / sumZ) : fallback
            };
        }

        private static double SyntheticModeWave(int mode, int axis, double corr)
        {
            int h = ((mode + 3) * (axis * 19 + 11)) % 7 + 1;
            double direction = ((mode + axis) % 2) == 0 ? 1.0 : -1.0;
            return direction * h / corr;
        }

        private static double SyntheticModeAmplitude(int mode, int axis)
        {
            double raw = Math.Sin(0.75487767 * ((mode + 1) * (axis * 17 + 5)));
            if (Math.Abs(raw) < 0.05)
                return raw < 0.0 ? -0.05 : 0.05;

            return raw;
        }

        private void AppendSyntheticTurbulentInletApplyCode(StringBuilder sb, Vector3d windDir)
        {
            string inletCondition = GetInletFaceCondition(windDir);

            sb.AppendLine("    auto applySyntheticTurbulentInlet = [&](uint t_step) {");
            sb.AppendLine("        // Velocity-field-only refresh for diagnostic turbulent-inlet runs.");
            sb.AppendLine("        // Two-pass layer correction keeps the finite-mode STG-lite perturbation mean-preserving at every inlet z_cell.");
            sb.AppendLine("        // Refresh only TYPE_E inlet nodes so solid ground/building flags are not overwritten.");
            sb.AppendLine("        lbm.flags.read_from_device();");
            sb.AppendLine("        lbm.u.read_from_device();");
            sb.AppendLine("        std::vector<float> citylbm_stg_layer_mean_correction_x(Nz, 0.0f);");
            sb.AppendLine("        std::vector<float> citylbm_stg_layer_mean_correction_y(Nz, 0.0f);");
            sb.AppendLine("        std::vector<float> citylbm_stg_layer_mean_correction_z(Nz, 0.0f);");
            sb.AppendLine("        std::vector<ulong> citylbm_stg_layer_corrected_inlet_count(Nz, 0ull);");
            sb.AppendLine("        for(ulong n=0ull; n<lbm.get_N(); n++) {");
            sb.AppendLine("            uint x=0u, y=0u, z=0u;");
            sb.AppendLine("            lbm.coordinates(n, x, y, z);");
            sb.AppendLine($"            if(lbm.flags[n] == TYPE_E && {inletCondition}) {{");
            sb.AppendLine("                float3 mean = windProfile(z);");
            sb.AppendLine("                float3 u_in = syntheticTurbulentInlet(x, y, z, t_step);");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_x[z] += u_in.x - mean.x;");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_y[z] += u_in.y - mean.y;");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_z[z] += u_in.z - mean.z;");
            sb.AppendLine("                citylbm_stg_layer_corrected_inlet_count[z]++;");
            sb.AppendLine("            }");
            sb.AppendLine("        }");
            sb.AppendLine("        for(uint z_layer=0u; z_layer<Nz; z_layer++) {");
            sb.AppendLine("            if(citylbm_stg_layer_corrected_inlet_count[z_layer] > 0ull) {");
            sb.AppendLine("                float inv_count = 1.0f / (float)citylbm_stg_layer_corrected_inlet_count[z_layer];");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_x[z_layer] *= inv_count;");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_y[z_layer] *= inv_count;");
            sb.AppendLine("                citylbm_stg_layer_mean_correction_z[z_layer] *= inv_count;");
            sb.AppendLine("            }");
            sb.AppendLine("        }");
            sb.AppendLine("        parallel_for(lbm.get_N(), [&](ulong n) {");
            sb.AppendLine("            uint x=0u, y=0u, z=0u;");
            sb.AppendLine("            lbm.coordinates(n, x, y, z);");
            sb.AppendLine($"            if(lbm.flags[n] == TYPE_E && {inletCondition}) {{");
            sb.AppendLine("                float3 u_in = syntheticTurbulentInlet(x, y, z, t_step);");
            sb.AppendLine("                u_in.x -= citylbm_stg_layer_mean_correction_x[z];");
            sb.AppendLine("                u_in.y -= citylbm_stg_layer_mean_correction_y[z];");
            sb.AppendLine("                u_in.z -= citylbm_stg_layer_mean_correction_z[z];");
            sb.AppendLine("                float3 mean = windProfile(z);");
            sb.AppendLine("                float mean_mag = sqrtf(mean.x*mean.x + mean.y*mean.y + mean.z*mean.z);");
            sb.AppendLine("                if(citylbm_stg_min_streamwise_fraction > 0.0f) {");
            sb.AppendLine("                    float streamwise = u_in.x*dir_x + u_in.y*dir_y + u_in.z*dir_z;");
            sb.AppendLine("                    float min_streamwise = citylbm_stg_min_streamwise_fraction * (mean_mag > 1.0e-6f ? mean_mag : 1.0e-6f);");
            sb.AppendLine("                    if(streamwise < min_streamwise) {");
            sb.AppendLine("                        float correction = min_streamwise - streamwise;");
            sb.AppendLine("                        u_in.x += correction * dir_x;");
            sb.AppendLine("                        u_in.y += correction * dir_y;");
            sb.AppendLine("                        u_in.z += correction * dir_z;");
            sb.AppendLine("                    }");
            sb.AppendLine("                }");
            sb.AppendLine("                lbm.u.x[n] = u_in.x;");
            sb.AppendLine("                lbm.u.y[n] = u_in.y;");
            sb.AppendLine("                lbm.u.z[n] = u_in.z;");
            sb.AppendLine("            }");
            sb.AppendLine("        });");
            sb.AppendLine("        lbm.u.write_to_device();");
            sb.AppendLine("    };");
            sb.AppendLine();
        }

        private string GetInletFaceCondition(Vector3d windDir)
        {
            bool xDominant = Math.Abs(windDir.X) >= Math.Abs(windDir.Y);
            if (xDominant)
                return windDir.X > 0.0 ? "x == 0u" : "x == Nx-1u";

            return windDir.Y > 0.0 ? "y == 0u" : "y == Ny-1u";
        }

        private string JoinFloatArray(IEnumerable<double> values)
        {
            return string.Join(", ", values.Select(v => v.ToString("F8", CultureInfo.InvariantCulture) + "f"));
        }

        private void SaveCaseMetadata(string caseDir, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            try
            {
                double uScale = 0.1 / Math.Max(GetProfileScaleSpeed(scene), 0.001);
                bool hasK = scene.CustomWindProfile != null && scene.CustomWindProfile.Any(s => s.HasK);
                int customProfileRowCount = scene.CustomWindProfile == null ? 0 : scene.CustomWindProfile.Count;
                int customProfileKRowCount = scene.CustomWindProfile == null ? 0 : scene.CustomWindProfile.Count(s => s.HasK);
                bool customProfileKComplete = customProfileRowCount > 0 && customProfileKRowCount == customProfileRowCount;
                double minKM2s2 = hasK ? scene.CustomWindProfile.Where(s => s.HasK).Min(s => s.K) : 0.0;
                double maxKM2s2 = hasK ? scene.CustomWindProfile.Where(s => s.HasK).Max(s => s.K) : 0.0;
                bool syntheticActive = IsSyntheticTurbulentInletActive(scene, settings);
                var boundaryAudit = BuildBoundaryProtocolAudit(scene, grid);
                double metadataBuildingHeightM = boundaryAudit.BuildingBoundsM == null ? 0.0 : boundaryAudit.BuildingBoundsM.Height;
                double tau = ComputeTau(settings, grid, scene);
                double nuLbm = ComputeNuLbm(settings, grid, scene);
                double reynolds = EstimateRunReynoldsNumber(scene, grid, settings);
                string windProfileCsvSha256 = ComputeOptionalFileSha256(scene.WindProfileCsvPath);
                int expectedFrames = settings.SaveInterval > 0
                    ? (int)Math.Ceiling(settings.TimeSteps / (double)settings.SaveInterval)
                    : 0;
                int expectedPaperAverageStepSpan = ComputeExpectedFinalWindowStepSpan(settings, PaperRecommendedAveragingFrames);
                int expectedPaperAverageStgRefreshes = ComputeExpectedFinalWindowStgRefreshCount(settings, PaperRecommendedAveragingFrames);
                double[] syntheticComponentNorms = ComputeSyntheticTurbulenceComponentNorms(
                    settings.SyntheticTurbulenceModeCount,
                    settings.SyntheticTurbulenceCorrelationCells);
                string syntheticTemporalSamplingGate = syntheticActive
                    ? (expectedPaperAverageStgRefreshes >= PaperRecommendedStgRefreshes
                        ? "pass"
                        : "diagnostic_only_insufficient_stg_refreshes_in_average_window")
                    : "not_applicable";
                string inletReynoldsStressTreatment = syntheticActive
                    ? "isotropic_from_k_only_R11_R22_R33_2k_over_3_R12_R13_R23_0; no measured Reynolds-stress tensor in AF table"
                    : (hasK ? "metadata_only_isotropic_k_assumption_not_injected" : "none");
                bool inletReynoldsStressTensorAvailable = false;
                bool inletDistributionFunctionReconstruction = false;
                bool boundaryNonReflectingOutletImplemented = false;
                bool boundarySideTopWindTunnelEquivalentImplemented = false;
                bool boundaryRoughWallFunctionImplemented = false;
                bool boundaryPrecursorOrRecyclingImplemented = false;
                bool boundaryBlockageFetchEvidenceArchived = false;
                string[] missingPaperGradeInletEvidence = syntheticActive
                    ? new[]
                    {
                        "measured_or_precursor_reynolds_stress_tensor",
                        "inlet_distribution_function_reconstruction",
                        "empty_tunnel_U_k_correlation_preservation_gate"
                    }
                    : new[]
                    {
                        "active_correlated_turbulent_inlet",
                        "measured_or_precursor_reynolds_stress_tensor",
                        "inlet_distribution_function_reconstruction",
                        "empty_tunnel_U_k_correlation_preservation_gate"
                    };
                string[] missingPaperGradeBoundaryEvidence = new[]
                {
                    "non_reflecting_or_validated_outlet_state",
                    "side_top_boundary_pair_mapping_or_wind_tunnel_equivalence",
                    "rough_wall_or_wall_function_action",
                    "precursor_or_recycling_development_field",
                    "official_blockage_fetch_clearance_evidence"
                };
                var metadata = new
                {
                    SchemaVersion = 2,
                    CityLBMVersion = "0.3.0",
                    SceneName = scene.Name,
                    GeneratedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),
                    WindProfile = scene.WindProfile.ToString(),
                    WindProfileCsvPath = scene.WindProfileCsvPath ?? "",
                    WindProfileCsvSha256 = windProfileCsvSha256,
                    ReferenceWindSpeedMps = scene.WindSpeed,
                    ReferenceHeightM = scene.ReferenceHeight,
                    ProfileScaleSpeedMps = GetProfileScaleSpeed(scene),
                    VelocityScaleMpsToLbm = uScale,
                    VelocityScaleLbmToMps = 1.0 / uScale,
                    TargetMaxProfileVelocityLbm = FluidX3DInterface.TargetMaxProfileVelocityLbm,
                    EstimatedMaxProfileMach = FluidX3DInterface.TargetMaxProfileVelocityLbm / Math.Sqrt(1.0 / 3.0),
                    LbmStabilityGate = "requires_solver_log_and_runtime_statistics",
                    LbmTau = tau,
                    LbmNu = nuLbm,
                    LbmViscosityUnitConversion = "nu_lbm = nu_SI * VelocityScaleMpsToLbm / dx",
                    TauClampingPolicy = "not_clamped_in_case_generation; validation_gate_and_solver_log_must_prove_stability",
                    PhysicalViscosityM2s = settings.Viscosity,
                    EstimatedReynoldsNumber = reynolds,
                    VelocitySet = "D3Q19",
                    LesModel = settings.EnableSmagorinskyLES ? "Smagorinsky" : "BGK_no_LES",
                    SmagorinskyCs = settings.EnableSmagorinskyLES ? settings.SmagorinskyConstantCs : 0.0,
                    TurbulentPrandtlNumber = settings.EnableSmagorinskyLES ? settings.TurbulentPrandtlNumber : 0.0,
                    SolverStabilityWarnings = "not_available_until_solver_log_is_archived",
                    VelocityOutputUnits = "FluidX3D write_device_to_vtk true requested; reader treats metadata as the unit contract.",
                    VtkReaderShouldApplyVelocityScale = false,
                    GeometryPhysicalUnitAssumption = "Rhino_model_geometry_is_already_real_scale_meters_before_case_generation",
                    GeometryScaleEvidenceGate = scene.BuildingMeshes != null && scene.BuildingMeshes.Count > 0 && metadataBuildingHeightM > 1.0
                        ? "diagnostic_geometry_scale_plausible_verify_against_official_probe_coordinates"
                        : "risk_missing_or_model_scale_geometry_verify_units_and_stl_scale",
                    GeometryScaleExpectedCaseENote = "AIJ_CaseE_official_BD_caseE_stl_is_1_to_250_model_scale_and_must_be_scaled_by_250_before_Add_Buildings",
                    GeometryBuildingCount = scene.BuildingMeshes == null ? 0 : scene.BuildingMeshes.Count,
                    GeometryBuildingHeightM = metadataBuildingHeightM,
                    DxM = grid.Dx,
                    Nx = grid.Nx,
                    Ny = grid.Ny,
                    Nz = grid.Nz,
                    TimeSteps = settings.TimeSteps,
                    SaveInterval = settings.SaveInterval,
                    ExpectedVtkFrameCount = expectedFrames,
                    TimeAveragingRequiredForValidation = true,
                    MinimumRecommendedAveragingFrames = MinimumRecommendedAveragingFrames,
                    PaperRecommendedAveragingFrames = PaperRecommendedAveragingFrames,
                    PaperRecommendedAverageStepSpan = PaperRecommendedAverageStepSpan,
                    ExpectedPaperAverageStepSpan = expectedPaperAverageStepSpan,
                    TimeAveragingRunGate = expectedFrames >= MinimumRecommendedAveragingFrames
                        ? "pass_minimum_frame_count"
                        : "smoke_only_too_few_frames_for_validation",
                    TimeAveragingPaperGate = expectedFrames >= PaperRecommendedAveragingFrames && expectedPaperAverageStepSpan >= PaperRecommendedAverageStepSpan
                        ? "pass_paper_recommended_frame_count_and_step_span"
                        : "diagnostic_only_extend_time_steps_or_reduce_save_interval",
                    TimeAveragingRunGateRequiredForModes = "Mode 1/2/3 require ExpectedVtkFrameCount >= MinimumRecommendedAveragingFrames for a smoke/diagnostic workflow; paper-grade validation also requires PaperRecommendedAveragingFrames and PaperRecommendedAverageStepSpan.",
                    CustomProfileRows = customProfileRowCount,
                    CustomProfileHasK = hasK,
                    CustomProfileKRows = customProfileKRowCount,
                    CustomProfileKComplete = customProfileKComplete,
                    KColumnStatus = hasK
                        ? (customProfileKComplete ? "read_from_csv_and_converted_to_lbm_metadata" : "invalid_partial_k_column")
                        : "not_available",
                    KUnitConversion = "k_lbm = k_m2s2 * VelocityScaleMpsToLbm^2",
                    KMinM2s2 = minKM2s2,
                    KMaxM2s2 = maxKM2s2,
                    KMinLbm = minKM2s2 * uScale * uScale,
                    KMaxLbm = maxKM2s2 * uScale * uScale,
                    TurbulentInletLevel = syntheticActive
                        ? "Level 2.5 STG-lite spectral perturbation from isotropic k"
                        : (hasK ? "Level 2 metadata/diagnostic chain" : "none"),
                    SyntheticTurbulentInletRequested = settings.EnableSyntheticTurbulentInlet,
                    SyntheticTurbulentInletInjected = syntheticActive,
                    SyntheticTurbulentInletBlockedReason = syntheticActive
                        ? "not_blocked"
                        : GetSyntheticTurbulentInletBlockedReason(scene, settings),
                    SyntheticTurbulentInletMethod = syntheticActive
                        ? "STG-lite deterministic divergence-reduced spectral modes with isotropic k and Taylor frozen-turbulence advection; not digital-filter, precursor, or Reynolds-stress inflow"
                        : "none",
                    SyntheticTurbulentInletTemporalTreatment = syntheticActive
                        ? "Taylor frozen-turbulence phase advection by local mean LBM velocity along the wind vector"
                        : "none",
                    SyntheticTurbulentInletDivergenceTreatment = syntheticActive
                        ? "per-mode fluctuation amplitudes projected normal to synthetic wave vectors"
                        : "none",
                    SyntheticTurbulentInletEnergyNormalization = syntheticActive
                        ? "component RMS target sigma=sqrt(2k/3); per-component deterministic spectral normalization accounts for finite-mode projected-component energy"
                        : "none",
                    SyntheticTurbulentInletComponentRmsNormalization = syntheticActive
                        ? new
                        {
                            X = syntheticComponentNorms[0],
                            Y = syntheticComponentNorms[1],
                            Z = syntheticComponentNorms[2],
                            Basis = "sqrt(2/sum(projected_unit_mode_component^2)); sinusoidal variance is 1/2"
                        }
                        : null,
                    SyntheticTurbulentInletDistributionTreatment = syntheticActive
                        ? "velocity_field_only_no_distribution_function_reconstruction; refreshed on TYPE_E inlet nodes in batch and graphics modes"
                        : "none",
                    SyntheticTurbulentInletMeanPreservingCorrection = syntheticActive,
                    SyntheticTurbulentInletMeanPreservingScope = syntheticActive
                        ? "per_z_cell_inlet_layer"
                        : "none",
                    SyntheticTurbulentInletMeanPreservingTreatment = syntheticActive
                        ? "each refresh subtracts the TYPE_E inlet perturbation mean separately for every z_cell layer so finite-mode and capped STG-lite fluctuations preserve the CustomTable mean U(z) profile by height"
                        : "none",
                    InletDistributionFunctionReconstruction = inletDistributionFunctionReconstruction,
                    SyntheticTurbulentInletPaperGradeStatus = syntheticActive
                        ? "diagnostic_only_until_distribution_reconstruction_or_native_k_preservation_gate_passes"
                        : "not_applicable",
                    PaperGradeTurbulentInletPrerequisiteGate = "fail",
                    PaperGradeTurbulentInletMissingEvidence = missingPaperGradeInletEvidence,
                    SyntheticTurbulenceIntensityScale = settings.SyntheticTurbulenceIntensityScale,
                    SyntheticTurbulenceCorrelationCells = settings.SyntheticTurbulenceCorrelationCells,
                    SyntheticTurbulenceCorrelationLengthM = settings.SyntheticTurbulenceCorrelationCells * grid.Dx,
                    SyntheticTurbulenceModeCount = settings.SyntheticTurbulenceModeCount,
                    SyntheticTurbulentInletLengthScaleSource = GetSyntheticTurbulenceLengthScaleSource(scene, settings),
                    SyntheticTurbulentInletLengthScaleGate = GetSyntheticTurbulenceLengthScaleGate(scene, settings),
                    SyntheticTurbulenceUpdateInterval = settings.SyntheticTurbulenceUpdateInterval,
                    SyntheticTurbulenceMinimumRecommendedRefreshes = PaperRecommendedStgRefreshes,
                    SyntheticTurbulenceExpectedFinalWindowRefreshCount = expectedPaperAverageStgRefreshes,
                    SyntheticTurbulentInletTemporalSamplingGate = syntheticTemporalSamplingGate,
                    SyntheticTurbulenceMaxFractionOfMean = settings.SyntheticTurbulenceMaxFractionOfMean,
                    SyntheticTurbulenceMinStreamwiseFraction = settings.SyntheticTurbulenceMinStreamwiseFraction,
                    SyntheticTurbulenceStreamwiseClippingTreatment = settings.SyntheticTurbulenceMinStreamwiseFraction > 0.0
                        ? "diagnostic_streamwise_lower_bound_enabled"
                        : "disabled_no_streamwise_clipping_of_k_perturbations",
                    InletReynoldsStressTensorAvailable = inletReynoldsStressTensorAvailable,
                    InletReynoldsStressTreatment = inletReynoldsStressTreatment,
                    ReynoldsStressAssumption = hasK ? "isotropic k only; no Reynolds stress tensor is available from AF table" : "",
                    WallRoughnessTreatment = "ground/buildings are voxelized TYPE_S no-slip; RoughnessLength shapes analytic mean profiles but is not a FluidX3D rough-wall or wall-function boundary in v0.3.0",
                    WindDirectionUnitVector = new
                    {
                        X = scene.WindDirection.X,
                        Y = scene.WindDirection.Y,
                        Z = scene.WindDirection.Z
                    },
                    InletVelocityTreatment = scene.WindProfile == WindProfileType.CustomTable
                        ? (syntheticActive
                            ? "height-varying mean velocity plus bounded STG-lite spectral fluctuations from k"
                            : "height-varying mean velocity from CustomTable; no correlated fluctuations")
                        : "deterministic mean velocity boundary",
                    BoundaryConditionSummary = GetBoundaryConditionSummary(scene.WindDirection, scene.WindProfile),
                    BoundaryConditionMethodClass = "citylbm_type_e_box_simplified",
                    BoundaryConditionPaperGradeStatus = "diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass",
                    BoundaryTypeEVelocityInitializationApplied = true,
                    BoundaryTypeEVelocityInitializationTreatment = scene.WindProfile == WindProfileType.Uniform
                        ? "all_TYPE_E_boundaries_initialized_from_uniform_mean_velocity_before_device_upload"
                        : "all_TYPE_E_boundaries_initialized_from_height_varying_mean_profile_before_device_upload",
                    BoundaryTypeEVelocityInitializationProfileAware = scene.WindProfile != WindProfileType.Uniform,
                    BoundaryTypeEVelocityInitializationDeviceUploadOrder = "lbm.flags_and_lbm.u_written_to_device_after_initialization_before_stl_voxelization",
                    BoundaryVelocityInitializationPaperGradeStatus = "diagnostic_damping_mitigation_not_wind_tunnel_equivalent_boundary",
                    PaperGradeBoundaryPrerequisiteGate = "fail",
                    PaperGradeBoundaryMissingEvidence = missingPaperGradeBoundaryEvidence,
                    BoundaryNonReflectingOutletImplemented = boundaryNonReflectingOutletImplemented,
                    BoundarySideTopWindTunnelEquivalentImplemented = boundarySideTopWindTunnelEquivalentImplemented,
                    BoundaryRoughWallFunctionImplemented = boundaryRoughWallFunctionImplemented,
                    BoundaryPrecursorOrRecyclingImplemented = boundaryPrecursorOrRecyclingImplemented,
                    BoundaryBlockageFetchEvidenceArchived = boundaryBlockageFetchEvidenceArchived,
                    BoundaryProtocolAudit = boundaryAudit,
                    BoundaryProtocolEvidenceSource = boundaryAudit.ProtocolEvidenceSource,
                    BoundaryProtocolEvidenceGate = boundaryAudit.ProtocolEvidenceGate,
                    ValidationReadiness = "diagnostic_ready_not_paper_grade_until_native_baseline_grid_sensitivity_long_averaging_and_turbulent_inlet_are_verified",
                    KnownProtocolRisks = BuildProtocolRisks(scene, settings).ToList(),
                    ProfileOriginZM = grid.Origin.Z,
                    ProfileFirstZM = scene.CustomWindProfile == null || scene.CustomWindProfile.Count == 0 ? 0.0 : scene.CustomWindProfile.Min(s => s.Z),
                    ProfileLastZM = scene.CustomWindProfile == null || scene.CustomWindProfile.Count == 0 ? 0.0 : scene.CustomWindProfile.Max(s => s.Z),
                    CustomProfile = scene.CustomWindProfile == null ? null : scene.CustomWindProfile.Select(s => new
                    {
                        ZM = s.Z,
                        UMps = s.U,
                        HasK = s.HasK,
                        KM2s2 = s.HasK ? s.K : 0.0,
                        KLBM = s.HasK ? s.K * uScale * uScale : 0.0
                    }).ToList()
                };

                string json = JsonConvert.SerializeObject(metadata, Formatting.Indented);
                File.WriteAllText(Path.Combine(caseDir, "case_metadata.json"), json, Encoding.UTF8);
                File.WriteAllText(Path.Combine(caseDir, "output", "case_metadata.json"), json, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[CityLBM] Save case_metadata.json failed: {ex.Message}");
            }
        }

        private string GetBoundaryConditionSummary(Vector3d windDirection, WindProfileType windProfile)
        {
            var dir = NormalizeWindDirection(windDirection);

            bool xDominant = Math.Abs(dir.X) >= Math.Abs(dir.Y);
            string axis = xDominant ? "X" : "Y";
            string inletSide;
            string outletSide;
            string lateralSides;

            if (xDominant)
            {
                bool fromMin = dir.X > 0.0;
                inletSide = fromMin ? "X-" : "X+";
                outletSide = fromMin ? "X+" : "X-";
                lateralSides = "Y-/Y+";
            }
            else
            {
                bool fromMin = dir.Y > 0.0;
                inletSide = fromMin ? "Y-" : "Y+";
                outletSide = fromMin ? "Y+" : "Y-";
                lateralSides = "X-/X+";
            }

            return $"dominant_axis={axis}; inlet={inletSide} TYPE_E velocity profile ({windProfile}); " +
                   $"outlet={outletSide} TYPE_E pressure/free-outflow approximation; " +
                   $"lateral={lateralSides} TYPE_E slip/free approximation; top=TYPE_E; ground/buildings=TYPE_S no-slip";
        }

        internal static Vector3d NormalizeWindDirection(Vector3d direction)
        {
            if (!IsFinite(direction.X) || !IsFinite(direction.Y) || !IsFinite(direction.Z))
                return new Vector3d(1.0, 0.0, 0.0);

            double length = Math.Sqrt(
                direction.X * direction.X +
                direction.Y * direction.Y +
                direction.Z * direction.Z);

            if (length <= 1.0e-12)
                return new Vector3d(1.0, 0.0, 0.0);

            return new Vector3d(direction.X / length, direction.Y / length, direction.Z / length);
        }

        private static bool IsFinite(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }

        private BoundaryProtocolAudit BuildBoundaryProtocolAudit(Scene scene, CartesianGrid grid)
        {
            var dir = NormalizeWindDirection(scene.WindDirection);

            bool xDominant = Math.Abs(dir.X) >= Math.Abs(dir.Y);
            bool fromMin = xDominant ? dir.X > 0.0 : dir.Y > 0.0;
            string axis = xDominant ? "X" : "Y";
            string inletFace = xDominant
                ? (fromMin ? "X-" : "X+")
                : (fromMin ? "Y-" : "Y+");
            string outletFace = xDominant
                ? (fromMin ? "X+" : "X-")
                : (fromMin ? "Y+" : "Y-");
            string lateralFaces = xDominant ? "Y-/Y+" : "X-/X+";

            BoundingBox domain = grid.DomainBounds;
            BoundingBox buildings = scene.Bounds;
            bool hasBuildings = buildings.IsValid;
            double buildingHeight = hasBuildings ? Math.Max(0.0, buildings.Max.Z - buildings.Min.Z) : double.NaN;
            double referenceHeight = buildingHeight > 1.0e-9 ? buildingHeight : double.NaN;

            double upstreamDistance;
            double downstreamDistance;
            double lateralMinusDistance;
            double lateralPlusDistance;
            if (xDominant)
            {
                upstreamDistance = fromMin ? buildings.Min.X - domain.Min.X : domain.Max.X - buildings.Max.X;
                downstreamDistance = fromMin ? domain.Max.X - buildings.Max.X : buildings.Min.X - domain.Min.X;
                lateralMinusDistance = buildings.Min.Y - domain.Min.Y;
                lateralPlusDistance = domain.Max.Y - buildings.Max.Y;
            }
            else
            {
                upstreamDistance = fromMin ? buildings.Min.Y - domain.Min.Y : domain.Max.Y - buildings.Max.Y;
                downstreamDistance = fromMin ? domain.Max.Y - buildings.Max.Y : buildings.Min.Y - domain.Min.Y;
                lateralMinusDistance = buildings.Min.X - domain.Min.X;
                lateralPlusDistance = domain.Max.X - buildings.Max.X;
            }

            double topClearance = hasBuildings ? domain.Max.Z - buildings.Max.Z : double.NaN;
            double minLateralDistance = Math.Min(lateralMinusDistance, lateralPlusDistance);
            double upstreamRatio = SafeRatio(upstreamDistance, referenceHeight);
            double downstreamRatio = SafeRatio(downstreamDistance, referenceHeight);
            double lateralRatio = SafeRatio(minLateralDistance, referenceHeight);
            double topRatio = SafeRatio(topClearance, referenceHeight);
            double domainX = domain.Max.X - domain.Min.X;
            double domainY = domain.Max.Y - domain.Min.Y;
            double domainZ = domain.Max.Z - domain.Min.Z;
            double buildingX = hasBuildings ? Math.Max(0.0, buildings.Max.X - buildings.Min.X) : double.NaN;
            double buildingY = hasBuildings ? Math.Max(0.0, buildings.Max.Y - buildings.Min.Y) : double.NaN;
            double buildingPlanArea = hasBuildings ? buildingX * buildingY : double.NaN;
            double domainPlanArea = IsPositiveDimension(domainX) && IsPositiveDimension(domainY) ? domainX * domainY : double.NaN;
            double frontalWidth = xDominant ? buildingY : buildingX;
            double inletWidth = xDominant ? domainY : domainX;
            double buildingFrontalArea = hasBuildings ? frontalWidth * buildingHeight : double.NaN;
            double inletFaceArea = IsPositiveDimension(inletWidth) && IsPositiveDimension(domainZ) ? inletWidth * domainZ : double.NaN;
            double planBlockageRatio = SafeRatio(buildingPlanArea, domainPlanArea);
            double frontalBlockageRatio = SafeRatio(buildingFrontalArea, inletFaceArea);

            bool domainValid = IsPositiveDimension(domain.Max.X - domain.Min.X) &&
                               IsPositiveDimension(domain.Max.Y - domain.Min.Y) &&
                               IsPositiveDimension(domain.Max.Z - domain.Min.Z);
            bool hasReferenceHeight = !double.IsNaN(referenceHeight) && referenceHeight > 1.0e-9;
            bool domainContainsBuildings = hasBuildings && domainValid &&
                                           domain.Min.X <= buildings.Min.X &&
                                           domain.Min.Y <= buildings.Min.Y &&
                                           domain.Min.Z <= buildings.Min.Z &&
                                           domain.Max.X >= buildings.Max.X &&
                                           domain.Max.Y >= buildings.Max.Y &&
                                           domain.Max.Z >= buildings.Max.Z;
            bool upstreamOk = upstreamRatio >= 5.0;
            bool downstreamOk = downstreamRatio >= 10.0;
            bool lateralOk = lateralRatio >= 5.0;
            bool topOk = topRatio >= 5.0;
            bool blockageDiagnosticAvailable =
                !double.IsNaN(frontalBlockageRatio) &&
                !double.IsInfinity(frontalBlockageRatio) &&
                !double.IsNaN(planBlockageRatio) &&
                !double.IsInfinity(planBlockageRatio);
            bool frontalBlockageOk = blockageDiagnosticAvailable && frontalBlockageRatio <= 0.05;
            bool planBlockageOk = blockageDiagnosticAvailable && planBlockageRatio <= 0.25;

            bool meetsDiagnosticDomain =
                domainValid &&
                hasBuildings &&
                hasReferenceHeight &&
                domainContainsBuildings &&
                upstreamOk &&
                downstreamOk &&
                lateralOk &&
                topOk &&
                frontalBlockageOk;

            var gateReasons = new List<string>();
            if (!domainValid) gateReasons.Add("domain_bounds_invalid_or_non_positive");
            if (!hasBuildings) gateReasons.Add("building_bounds_missing_or_invalid");
            if (!hasReferenceHeight) gateReasons.Add("building_height_unavailable_for_H_scaling");
            if (hasBuildings && domainValid && !domainContainsBuildings) gateReasons.Add("domain_does_not_fully_contain_building_bounds");
            if (hasReferenceHeight && !upstreamOk) gateReasons.Add("upstream_clearance_below_5H");
            if (hasReferenceHeight && !downstreamOk) gateReasons.Add("downstream_clearance_below_10H");
            if (hasReferenceHeight && !lateralOk) gateReasons.Add("minimum_lateral_clearance_below_5H");
            if (hasReferenceHeight && !topOk) gateReasons.Add("top_clearance_below_5H");
            if (!blockageDiagnosticAvailable) gateReasons.Add("blockage_ratio_unavailable");
            if (blockageDiagnosticAvailable && !frontalBlockageOk) gateReasons.Add("approx_frontal_blockage_above_0.05");
            if (blockageDiagnosticAvailable && !planBlockageOk) gateReasons.Add("approx_plan_blockage_above_0.25_diagnostic");
            if (gateReasons.Count == 0) gateReasons.Add("diagnostic_clearance_thresholds_satisfied");

            return new BoundaryProtocolAudit
            {
                Purpose = "Structured audit of boundary faces and domain clearance; compare these values with the AIJ wind-tunnel protocol before paper-grade claims.",
                DominantAxis = axis,
                InletFace = inletFace,
                OutletFace = outletFace,
                LateralFaces = lateralFaces,
                TopFace = "Z+",
                GroundFace = "Z-",
                BoundaryTypes = new BoundaryTypesRecord
                {
                    Inlet = "TYPE_E velocity profile; boundary velocity initialized from mean profile",
                    Outlet = "TYPE_E pressure/free-outflow approximation; velocity initialized from mean profile to avoid zero-speed boundary damping",
                    Lateral = "TYPE_E slip/free approximation; velocity initialized from mean profile",
                    Top = "TYPE_E; velocity initialized from mean profile",
                    Ground = "TYPE_S no-slip; no rough-wall function",
                    Buildings = "TYPE_S no-slip"
                },
                DomainSizeM = new DimensionRecord
                {
                    X = Math.Round(domain.Max.X - domain.Min.X, 6),
                    Y = Math.Round(domain.Max.Y - domain.Min.Y, 6),
                    Z = Math.Round(domain.Max.Z - domain.Min.Z, 6)
                },
                BuildingBoundsM = hasBuildings ? new BoundsRecord
                {
                    MinX = Math.Round(buildings.Min.X, 6),
                    MinY = Math.Round(buildings.Min.Y, 6),
                    MinZ = Math.Round(buildings.Min.Z, 6),
                    MaxX = Math.Round(buildings.Max.X, 6),
                    MaxY = Math.Round(buildings.Max.Y, 6),
                    MaxZ = Math.Round(buildings.Max.Z, 6),
                    Height = Math.Round(buildingHeight, 6)
                } : null,
                ClearanceM = new ClearanceRecord
                {
                    Upstream = Math.Round(upstreamDistance, 6),
                    Downstream = Math.Round(downstreamDistance, 6),
                    LateralMinus = Math.Round(lateralMinusDistance, 6),
                    LateralPlus = Math.Round(lateralPlusDistance, 6),
                    MinLateral = Math.Round(minLateralDistance, 6),
                    Top = Math.Round(topClearance, 6)
                },
                ClearanceByBuildingHeight = new ClearanceRatioRecord
                {
                    Upstream = RoundOrNaN(upstreamRatio),
                    Downstream = RoundOrNaN(downstreamRatio),
                    MinLateral = RoundOrNaN(lateralRatio),
                    Top = RoundOrNaN(topRatio)
                },
                DiagnosticThresholdsByBuildingHeight = new BoundaryThresholdRecord
                {
                    Upstream = 5.0,
                    Downstream = 10.0,
                    MinLateral = 5.0,
                    Top = 5.0
                },
                BlockageDiagnostics = new BoundaryBlockageRecord
                {
                    Method = "axis-aligned building-bounds approximation; use only as a screening diagnostic and verify against official wind-tunnel blockage",
                    DomainPlanAreaM2 = RoundOrNaN(domainPlanArea),
                    BuildingPlanAreaM2 = RoundOrNaN(buildingPlanArea),
                    InletFaceAreaM2 = RoundOrNaN(inletFaceArea),
                    BuildingFrontalAreaM2 = RoundOrNaN(buildingFrontalArea),
                    ApproxPlanBlockageRatio = RoundOrNaN(planBlockageRatio),
                    ApproxFrontalBlockageRatio = RoundOrNaN(frontalBlockageRatio),
                    DiagnosticMaxFrontalBlockageRatio = 0.05,
                    DiagnosticMaxPlanBlockageRatio = 0.25,
                    FrontalBlockageOk = frontalBlockageOk,
                    PlanBlockageOk = planBlockageOk,
                    Gate = frontalBlockageOk ? "blockage_diagnostic_ok_verify_against_aij" : "blockage_protocol_risk"
                },
                ClearanceChecks = new BoundaryClearanceCheckRecord
                {
                    DomainValid = domainValid,
                    BuildingBoundsValid = hasBuildings,
                    BuildingHeightValid = hasReferenceHeight,
                    DomainContainsBuildings = domainContainsBuildings,
                    UpstreamOk = upstreamOk,
                    DownstreamOk = downstreamOk,
                    MinLateralOk = lateralOk,
                    TopOk = topOk,
                    ApproxFrontalBlockageOk = frontalBlockageOk,
                    ApproxPlanBlockageOk = planBlockageOk
                },
                MeetsDiagnosticDomain = meetsDiagnosticDomain,
                Gate = meetsDiagnosticDomain ? "diagnostic_clearance_ok_verify_against_aij" : "boundary_clearance_risk",
                ProtocolEvidenceSource = "diagnostic_clearance_and_blockage_only; not matched to official AIJ wind-tunnel boundary/fetch/roughness evidence",
                ProtocolEvidenceGate = "diagnostic_only_missing_aij_boundary_protocol_evidence",
                GateReasons = gateReasons,
                RequiredNextAction = "For AIJ validation, archive this object, report inlet/outlet/lateral/top clearances, approximate blockage ratios, and compare against the official wind-tunnel blockage and fetch protocol."
            };
        }

        private bool IsPositiveDimension(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value) && value > 0.0;
        }

        private double SafeRatio(double numerator, double denominator)
        {
            return !double.IsNaN(numerator) && !double.IsNaN(denominator) && Math.Abs(denominator) > 1.0e-12
                ? numerator / denominator
                : double.NaN;
        }

        private double RoundOrNaN(double value)
        {
            return double.IsNaN(value) || double.IsInfinity(value)
                ? double.NaN
                : Math.Round(value, 6);
        }

        private static int ComputeExpectedFinalWindowStepSpan(SimulationSettings settings, int averageFrameCount)
        {
            if (settings == null ||
                settings.SaveInterval <= 0 ||
                settings.TimeSteps <= 0 ||
                averageFrameCount <= 1)
            {
                return 0;
            }

            var savedSteps = new List<int>();
            for (int step = settings.SaveInterval; step <= settings.TimeSteps; step += settings.SaveInterval)
                savedSteps.Add(step);

            if (savedSteps.Count == 0 || savedSteps[savedSteps.Count - 1] != settings.TimeSteps)
                savedSteps.Add(settings.TimeSteps);

            int windowCount = Math.Min(averageFrameCount, savedSteps.Count);
            if (windowCount <= 1)
                return 0;

            return savedSteps[savedSteps.Count - 1] - savedSteps[savedSteps.Count - windowCount];
        }

        private static int ComputeExpectedFinalWindowStgRefreshCount(SimulationSettings settings, int averageFrameCount)
        {
            int span = ComputeExpectedFinalWindowStepSpan(settings, averageFrameCount);
            if (span <= 0 || settings.SyntheticTurbulenceUpdateInterval <= 0)
                return 0;

            return (int)Math.Floor(span / (double)settings.SyntheticTurbulenceUpdateInterval);
        }

        private IEnumerable<string> BuildProtocolRisks(Scene scene, SimulationSettings settings)
        {
            bool syntheticActive = IsSyntheticTurbulentInletActive(scene, settings);
            if (scene.WindProfile == WindProfileType.CustomTable &&
                scene.CustomWindProfile != null &&
                scene.CustomWindProfile.Any(s => s.HasK))
            {
                if (syntheticActive)
                {
                    yield return "AF k column drives an experimental STG-lite spectral inlet with Taylor frozen-turbulence temporal advection, but this is not a full digital-filter, precursor/recycling, or Reynolds-stress inflow.";
                    yield return "STG-lite inlet refreshes macroscopic lbm.u values on TYPE_E inlet nodes in both batch and graphics modes; distribution functions are not reconstructed, so k preservation must be proven by an empty-tunnel native baseline before paper-grade validation.";
                    if (!HasSupportedSyntheticTurbulenceLengthScaleSource(settings.SyntheticTurbulenceLengthScaleSource))
                        yield return "STG-lite correlation length is still a diagnostic user-selected value; provide AIJ/official/precursor/DFM/SEM length-scale evidence before paper-grade validation.";
                    int expectedStgRefreshes = ComputeExpectedFinalWindowStgRefreshCount(settings, PaperRecommendedAveragingFrames);
                    if (expectedStgRefreshes < PaperRecommendedStgRefreshes)
                        yield return $"STG-lite final averaging window is expected to contain only {expectedStgRefreshes} inlet refreshes; paper-grade use should sample at least {PaperRecommendedStgRefreshes} refreshes after stationarity.";
                }
                else
                {
                    yield return "AF k column is read and converted, but no digital-filter/synthetic-eddy turbulent inlet is injected. If synthetic inlet was requested, CityLBM requires k to be present on every CustomTable profile row before injection.";
                }
            }
            else if (settings.EnableSyntheticTurbulentInlet)
            {
                yield return "Synthetic inlet was requested but disabled because the scene is not CustomTable with a usable k column.";
            }

            yield return "Boundary conditions are simplified TYPE_E inlet/outlet/lateral/top approximations and must be checked against the AIJ wind-tunnel protocol.";
            yield return "CityLBM initializes all TYPE_E boundary velocities from the mean wind profile before device upload to avoid zero-speed outlet/lateral/top boundary damping.";
            yield return "BoundaryProtocolAudit records inlet/outlet/lateral/top faces and clearances, but its diagnostic thresholds are not a substitute for the official AIJ boundary/blockage protocol.";
            yield return "Ground is currently TYPE_S no-slip without a rough-wall or wall-function model; AF profile roughness is not the same as an aerodynamic rough-wall boundary.";

            int expectedFrames = settings.SaveInterval > 0
                ? (int)Math.Ceiling(settings.TimeSteps / (double)settings.SaveInterval)
                : 0;
            int expectedPaperAverageStepSpan = ComputeExpectedFinalWindowStepSpan(settings, PaperRecommendedAveragingFrames);
            int expectedPaperAverageStgRefreshes = ComputeExpectedFinalWindowStgRefreshCount(settings, PaperRecommendedAveragingFrames);
            if (expectedFrames < PaperRecommendedAveragingFrames || expectedPaperAverageStepSpan < PaperRecommendedAverageStepSpan)
            {
                yield return $"Only {expectedFrames} VTK frames and a final {PaperRecommendedAveragingFrames}-frame step span of {expectedPaperAverageStepSpan} are expected; formal validation should average at least {PaperRecommendedAveragingFrames} late frames spanning about {PaperRecommendedAverageStepSpan} solver steps after stationarity is checked.";
            }

            yield return "Coordinate transform, wind component sign, probe projection and normalization basis must be audited for each validation run.";
        }

        private void SaveValidationProtocolAudit(string caseDir, Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            try
            {
                var items = BuildValidationProtocolAuditItems(scene, grid, settings).ToList();
                var audit = new
                {
                    SchemaVersion = 1,
                    CityLBMVersion = "0.3.0",
                    SceneName = scene.Name,
                    GeneratedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),
                    Purpose = "Protocol-level audit for AIJ validation before interpreting error metrics.",
                    Gate = items.Any(i => i.Status == "fail" || i.Status == "risk")
                        ? "not_paper_grade"
                        : (items.Any(i => i.Status == "partial") ? "diagnostic_only" : "ready_for_validation_run"),
                    Items = items
                };

                string json = JsonConvert.SerializeObject(audit, Formatting.Indented);
                File.WriteAllText(Path.Combine(caseDir, "validation_protocol_audit.json"), json, Encoding.UTF8);
                File.WriteAllText(Path.Combine(caseDir, "output", "validation_protocol_audit.json"), json, Encoding.UTF8);

                string markdown = BuildValidationProtocolAuditMarkdown(audit.Gate, items);
                File.WriteAllText(Path.Combine(caseDir, "validation_protocol_audit.md"), markdown, Encoding.UTF8);
                File.WriteAllText(Path.Combine(caseDir, "output", "validation_protocol_audit.md"), markdown, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[CityLBM] Save validation_protocol_audit failed: {ex.Message}");
            }
        }

        private void SaveNativeFluidX3DBaselineManifest(
            string caseDir,
            Scene scene,
            CartesianGrid grid,
            SimulationSettings settings,
            string setupPath,
            string definesPath,
            string stlPath)
        {
            try
            {
                string domainOriginPath = Path.Combine(caseDir, "domain_origin.json");
                string caseMetadataPath = Path.Combine(caseDir, "case_metadata.json");
                string validationAuditPath = Path.Combine(caseDir, "validation_protocol_audit.json");
                var requiredSourceFiles = new[]
                {
                    BuildBaselineSourceFile("Native FluidX3D original setup", Path.Combine(FluidX3DPath ?? "", "src", "setup.cpp")),
                    BuildBaselineSourceFile("Native FluidX3D original defines", Path.Combine(FluidX3DPath ?? "", "src", "defines.hpp")),
                    BuildBaselineSourceFile("Native FluidX3D lbm.hpp", Path.Combine(FluidX3DPath ?? "", "src", "lbm.hpp")),
                    BuildBaselineSourceFile("Native FluidX3D lbm.cpp", Path.Combine(FluidX3DPath ?? "", "src", "lbm.cpp")),
                    BuildBaselineSourceFile("FluidX3D setup", setupPath),
                    BuildBaselineSourceFile("FluidX3D defines", definesPath),
                    BuildBaselineSourceFile("Building geometry", stlPath),
                    BuildBaselineSourceFile("Domain origin", domainOriginPath),
                    BuildBaselineSourceFile("Case metadata", caseMetadataPath),
                    BuildBaselineSourceFile("Validation protocol audit", validationAuditPath)
                };
                var boundaryAudit = BuildBoundaryProtocolAudit(scene, grid);
                double manifestBuildingHeightM = boundaryAudit.BuildingBoundsM == null ? 0.0 : boundaryAudit.BuildingBoundsM.Height;
                var sourceValidation = ValidateFluidX3DSourcePath(out string sourceValidationMessage);
                string baselineId = BuildNativeBaselineId(scene, requiredSourceFiles);
                string[] missingPaperGradeBoundaryEvidence = new[]
                {
                    "non_reflecting_or_validated_outlet_state",
                    "side_top_boundary_pair_mapping_or_wind_tunnel_equivalence",
                    "rough_wall_or_wall_function_action",
                    "precursor_or_recycling_development_field",
                    "official_blockage_fetch_clearance_evidence"
                };

                var manifest = new
                {
                    SchemaVersion = 1,
                    CityLBMVersion = "0.3.0",
                    BaselineId = baselineId,
                    SceneName = scene.Name,
                    GeneratedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),
                    Purpose = "Paired native FluidX3D baseline protocol for separating solver/protocol error from CityLBM integration error.",
                    Gate = "required_before_paper_grade_accuracy_claim",
                    CaseDirectory = caseDir,
                    NativeFluidX3DSourcePath = FluidX3DPath ?? "",
                    NativeFluidX3DPathExplicitlyProvided = HasExplicitFluidX3DPath,
                    NativeFluidX3DSourceValidation = sourceValidation,
                    NativeFluidX3DSourceValidationMessage = sourceValidationMessage,
                    RequiredSourceFiles = requiredSourceFiles,
                    SharedRunConditions = new
                    {
                        DxM = grid.Dx,
                        Nx = grid.Nx,
                        Ny = grid.Ny,
                        Nz = grid.Nz,
                        TimeSteps = settings.TimeSteps,
                        SaveInterval = settings.SaveInterval,
                        ExpectedVtkFrameCount = settings.SaveInterval > 0
                            ? (int)Math.Ceiling(settings.TimeSteps / (double)settings.SaveInterval)
                            : 0,
                        GeometryPhysicalUnitAssumption = "Rhino_model_geometry_is_already_real_scale_meters_before_case_generation",
                        GeometryScaleEvidenceGate = scene.BuildingMeshes != null && scene.BuildingMeshes.Count > 0 && manifestBuildingHeightM > 1.0
                            ? "diagnostic_geometry_scale_plausible_verify_against_official_probe_coordinates"
                            : "risk_missing_or_model_scale_geometry_verify_units_and_stl_scale",
                        GeometryScaleExpectedCaseENote = "AIJ_CaseE_official_BD_caseE_stl_is_1_to_250_model_scale_and_must_be_scaled_by_250_before_Add_Buildings",
                        GeometryBuildingCount = scene.BuildingMeshes == null ? 0 : scene.BuildingMeshes.Count,
                        GeometryBuildingHeightM = manifestBuildingHeightM,
                        MinimumRecommendedAveragingFrames = MinimumRecommendedAveragingFrames,
                        PaperRecommendedAveragingFrames = PaperRecommendedAveragingFrames,
                        PaperRecommendedAverageStepSpan = PaperRecommendedAverageStepSpan,
                        ExpectedPaperAverageStepSpan = ComputeExpectedFinalWindowStepSpan(settings, PaperRecommendedAveragingFrames),
                        WindProfile = scene.WindProfile.ToString(),
                        WindProfileCsvPath = scene.WindProfileCsvPath ?? "",
                        WindProfileCsvSha256 = ComputeOptionalFileSha256(scene.WindProfileCsvPath),
                        WindDirectionUnitVector = new
                        {
                            X = scene.WindDirection.X,
                            Y = scene.WindDirection.Y,
                            Z = scene.WindDirection.Z
                        },
                        ReferenceWindSpeedMps = scene.WindSpeed,
                        ReferenceHeightM = scene.ReferenceHeight,
                        TargetMaxProfileVelocityLbm = FluidX3DInterface.TargetMaxProfileVelocityLbm,
                        EstimatedMaxProfileMach = FluidX3DInterface.TargetMaxProfileVelocityLbm / Math.Sqrt(1.0 / 3.0),
                        LbmStabilityGate = "requires_solver_log_and_runtime_statistics",
                        LbmTau = ComputeTau(settings, grid, scene),
                        LbmNu = ComputeNuLbm(settings, grid, scene),
                        LbmViscosityUnitConversion = "nu_lbm = nu_SI * VelocityScaleMpsToLbm / dx",
                        TauClampingPolicy = "not_clamped_in_case_generation; validation_gate_and_solver_log_must_prove_stability",
                        PhysicalViscosityM2s = settings.Viscosity,
                        EstimatedReynoldsNumber = EstimateRunReynoldsNumber(scene, grid, settings),
                        VelocitySet = "D3Q19",
                        LesModel = settings.EnableSmagorinskyLES ? "Smagorinsky" : "BGK_no_LES",
                        SmagorinskyCs = settings.EnableSmagorinskyLES ? settings.SmagorinskyConstantCs : 0.0,
                        TurbulentPrandtlNumber = settings.EnableSmagorinskyLES ? settings.TurbulentPrandtlNumber : 0.0,
                        SolverStabilityWarnings = "not_available_until_solver_log_is_archived",
                        SyntheticTurbulentInletRequested = settings.EnableSyntheticTurbulentInlet,
                        SyntheticTurbulentInletInjected = IsSyntheticTurbulentInletActive(scene, settings),
                        SyntheticTurbulentInletBlockedReason = IsSyntheticTurbulentInletActive(scene, settings)
                            ? "not_blocked"
                            : GetSyntheticTurbulentInletBlockedReason(scene, settings),
                        SyntheticTurbulenceCorrelationCells = settings.SyntheticTurbulenceCorrelationCells,
                        SyntheticTurbulenceCorrelationLengthM = settings.SyntheticTurbulenceCorrelationCells * grid.Dx,
                        SyntheticTurbulenceModeCount = settings.SyntheticTurbulenceModeCount,
                        SyntheticTurbulentInletLengthScaleSource = GetSyntheticTurbulenceLengthScaleSource(scene, settings),
                        SyntheticTurbulentInletLengthScaleGate = GetSyntheticTurbulenceLengthScaleGate(scene, settings),
                        SyntheticTurbulenceMinStreamwiseFraction = settings.SyntheticTurbulenceMinStreamwiseFraction,
                        SyntheticTurbulenceStreamwiseClippingTreatment = settings.SyntheticTurbulenceMinStreamwiseFraction > 0.0
                            ? "diagnostic_streamwise_lower_bound_enabled"
                            : "disabled_no_streamwise_clipping_of_k_perturbations",
                        SyntheticTurbulentInletTemporalTreatment = IsSyntheticTurbulentInletActive(scene, settings)
                            ? "Taylor frozen-turbulence phase advection by local mean LBM velocity along the wind vector"
                            : "none",
                        InletDistributionTreatment = IsSyntheticTurbulentInletActive(scene, settings)
                            ? "velocity_field_only_no_distribution_function_reconstruction"
                            : "not_active",
                        WallRoughnessTreatment = "ground/buildings TYPE_S no-slip; no FluidX3D rough-wall or wall-function boundary in v0.3.0",
                        BoundaryConditionSummary = GetBoundaryConditionSummary(scene.WindDirection, scene.WindProfile),
                        BoundaryConditionMethodClass = "citylbm_type_e_box_simplified",
                        BoundaryConditionPaperGradeStatus = "diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass",
                        BoundaryTypeEVelocityInitializationApplied = true,
                        BoundaryTypeEVelocityInitializationTreatment = scene.WindProfile == WindProfileType.Uniform
                            ? "all_TYPE_E_boundaries_initialized_from_uniform_mean_velocity_before_device_upload"
                            : "all_TYPE_E_boundaries_initialized_from_height_varying_mean_profile_before_device_upload",
                        BoundaryTypeEVelocityInitializationProfileAware = scene.WindProfile != WindProfileType.Uniform,
                        BoundaryTypeEVelocityInitializationDeviceUploadOrder = "lbm.flags_and_lbm.u_written_to_device_after_initialization_before_stl_voxelization",
                        BoundaryVelocityInitializationPaperGradeStatus = "diagnostic_damping_mitigation_not_wind_tunnel_equivalent_boundary",
                        PaperGradeBoundaryPrerequisiteGate = "fail",
                        PaperGradeBoundaryMissingEvidence = missingPaperGradeBoundaryEvidence,
                        BoundaryNonReflectingOutletImplemented = false,
                        BoundarySideTopWindTunnelEquivalentImplemented = false,
                        BoundaryRoughWallFunctionImplemented = false,
                        BoundaryPrecursorOrRecyclingImplemented = false,
                        BoundaryBlockageFetchEvidenceArchived = false,
                        BoundaryProtocolAudit = boundaryAudit,
                        BoundaryProtocolEvidenceSource = boundaryAudit.ProtocolEvidenceSource,
                        BoundaryProtocolEvidenceGate = boundaryAudit.ProtocolEvidenceGate
                    },
                    RequiredPairedEvidence = new[]
                    {
                        "Native FluidX3D executable path and build log compiled from the archived setup.cpp/defines.hpp.",
                        "CityLBM-driven run log using the same setup.cpp physics choices, grid, time steps and save interval.",
                        "New VTK files from both runs; do not copy older u-*.vtk files into the archive.",
                        "Inlet distribution treatment and wall roughness treatment recorded in both native and CityLBM-driven runs.",
                        "Read VTK Average Last N setting and actual SourceTimeSteps used for every metric.",
                        "Data Probe Audit CSV with Uref, Wind Direction, speed ratio, streamwise ratio, nearest distance and nearby point count.",
                        "Official probe table with point numbers, coordinates, compared velocity component and failed/out-of-domain flag.",
                        "Metrics table containing MAE, RMSE, bias, R2, regression slope/intercept and systematic-bias flag."
                    },
                    AcceptanceBlocks = new[]
                    {
                        "Use an explicitly supplied FluidX3D source path; auto-detected paths are not sufficient evidence for a controlled baseline.",
                        "Do not claim CityLBM accuracy if native FluidX3D has not been run from the same archived case.",
                        "Do not tune parameters while mean speed-ratio bias remains about -0.20 to -0.35 without first auditing inlet turbulence, boundary treatment, wind-direction sign, probe projection and Uref normalization.",
                        "Do not use R2 alone as a reliability criterion.",
                        "Do not compare a single instantaneous or short-window VTK frame as a formal validation result."
                    },
                    KnownProtocolRisks = BuildProtocolRisks(scene, settings).ToList()
                };

                string json = JsonConvert.SerializeObject(manifest, Formatting.Indented);
                File.WriteAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.json"), json, Encoding.UTF8);
                File.WriteAllText(Path.Combine(caseDir, "output", "native_fluidx3d_baseline_manifest.json"), json, Encoding.UTF8);

                string markdown = BuildNativeFluidX3DBaselineManifestMarkdown(
                    manifest.BaselineId,
                    manifest.Gate,
                    requiredSourceFiles,
                    manifest.RequiredPairedEvidence,
                    manifest.AcceptanceBlocks);
                File.WriteAllText(Path.Combine(caseDir, "native_fluidx3d_baseline_manifest.md"), markdown, Encoding.UTF8);
                File.WriteAllText(Path.Combine(caseDir, "output", "native_fluidx3d_baseline_manifest.md"), markdown, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[CityLBM] Save native_fluidx3d_baseline_manifest failed: {ex.Message}");
            }
        }

        private string BuildNativeBaselineId(Scene scene, IEnumerable<BaselineSourceFileRecord> requiredSourceFiles)
        {
            var sb = new StringBuilder();
            sb.AppendLine("citylbm-native-baseline-v1");
            sb.AppendLine(scene?.Name ?? "");
            foreach (var file in requiredSourceFiles.OrderBy(f => f.Role, StringComparer.Ordinal))
                sb.AppendLine($"{file.Role}|{file.Exists}|{file.Sha256}");

            using (var sha = SHA256.Create())
            {
                byte[] bytes = Encoding.UTF8.GetBytes(sb.ToString());
                string digest = BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
                return $"citylbm-v0.3.0-{SanitizeName(scene?.Name ?? "case")}-{digest.Substring(0, 12)}";
            }
        }

        private BaselineSourceFileRecord BuildBaselineSourceFile(string role, string path)
        {
            bool exists = !string.IsNullOrWhiteSpace(path) && File.Exists(path);
            return new BaselineSourceFileRecord
            {
                Role = role,
                Path = path ?? "",
                Exists = exists,
                HashAlgorithm = "SHA256",
                Sha256 = exists ? ComputeFileSha256(path) : ""
            };
        }

        private string ComputeFileSha256(string path)
        {
            using (var stream = File.OpenRead(path))
            using (var sha = SHA256.Create())
            {
                byte[] hash = sha.ComputeHash(stream);
                return BitConverter.ToString(hash).Replace("-", "").ToUpperInvariant();
            }
        }

        private string ComputeOptionalFileSha256(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                return "";

            try
            {
                string fullPath = Path.GetFullPath(path);
                return File.Exists(fullPath) ? ComputeFileSha256(fullPath) : "";
            }
            catch
            {
                return "";
            }
        }

        private string BuildNativeFluidX3DBaselineManifestMarkdown(
            string baselineId,
            string gate,
            IEnumerable<BaselineSourceFileRecord> requiredSourceFiles,
            IEnumerable<string> requiredEvidence,
            IEnumerable<string> acceptanceBlocks)
        {
            var sb = new StringBuilder();
            sb.AppendLine("# Native FluidX3D baseline manifest");
            sb.AppendLine();
            sb.AppendLine($"BaselineId: `{baselineId}`");
            sb.AppendLine();
            sb.AppendLine($"Gate: `{gate}`");
            sb.AppendLine();
            sb.AppendLine("This file is a protocol manifest, not a simulation result. Use it to run the native FluidX3D baseline from the same generated case before judging CityLBM-vs-AIJ accuracy.");
            sb.AppendLine();
            sb.AppendLine("## Required source hashes");
            sb.AppendLine("| Role | Exists | SHA256 | Path |");
            sb.AppendLine("|---|---:|---|---|");
            foreach (var file in requiredSourceFiles)
            {
                sb.AppendLine($"| {EscapeMarkdownTable(file.Role)} | `{file.Exists}` | `{file.Sha256}` | {EscapeMarkdownTable(file.Path)} |");
            }
            sb.AppendLine();
            sb.AppendLine("## Required paired evidence");
            foreach (string item in requiredEvidence)
                sb.AppendLine($"- {item}");
            sb.AppendLine();
            sb.AppendLine("## Acceptance blocks");
            foreach (string item in acceptanceBlocks)
                sb.AppendLine($"- {item}");
            return sb.ToString();
        }

        private IEnumerable<ValidationProtocolAuditItem> BuildValidationProtocolAuditItems(Scene scene, CartesianGrid grid, SimulationSettings settings)
        {
            bool customTable = scene.WindProfile == WindProfileType.CustomTable;
            bool hasProfile = scene.CustomWindProfile != null && scene.CustomWindProfile.Count >= 2;
            bool hasK = scene.CustomWindProfile != null && scene.CustomWindProfile.Any(s => s.HasK);
            bool syntheticActive = IsSyntheticTurbulentInletActive(scene, settings);
            string lengthScaleSource = GetSyntheticTurbulenceLengthScaleSource(scene, settings);
            string lengthScaleGate = GetSyntheticTurbulenceLengthScaleGate(scene, settings);
            bool lengthScaleSupported = lengthScaleGate == "pass";
            double maxProfileVelocityLbm = TargetMaxProfileVelocityLbm;
            double estimatedMach = maxProfileVelocityLbm / Math.Sqrt(1.0 / 3.0);
            double tau = ComputeTau(settings, grid, scene);
            double nuLbm = ComputeNuLbm(settings, grid, scene);
            double reynolds = EstimateRunReynoldsNumber(scene, grid, settings);
            BoundaryProtocolAudit boundaryAudit = BuildBoundaryProtocolAudit(scene, grid);
            bool boundaryClearanceOk = boundaryAudit.MeetsDiagnosticDomain;
            int expectedFrames = settings.SaveInterval > 0
                ? (int)Math.Ceiling(settings.TimeSteps / (double)settings.SaveInterval)
                : 0;
            int expectedPaperAverageStepSpan = ComputeExpectedFinalWindowStepSpan(settings, PaperRecommendedAveragingFrames);
            int expectedPaperAverageStgRefreshes = ComputeExpectedFinalWindowStgRefreshCount(settings, PaperRecommendedAveragingFrames);

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_mean_profile",
                Status = customTable && hasProfile ? "pass" : "risk",
                Evidence = customTable && hasProfile
                    ? $"CustomTable with {scene.CustomWindProfile.Count} rows; setup.cpp will emit profile_z_m/profile_u_lbm arrays."
                    : $"WindProfile={scene.WindProfile}; AIJ AF validation should use CustomTable z,U,k.",
                Risk = customTable && hasProfile ? "" : "Mean inflow may not match the AIJ approach-flow profile.",
                RequiredNextAction = customTable && hasProfile ? "Archive setup.cpp and case_metadata.json with the run." : "Set Wind Profile=CustomTable and load the official AF CSV."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_turbulence_k",
                Status = syntheticActive ? "partial" : (hasK ? "risk" : "fail"),
                Evidence = syntheticActive
                    ? $"AF k column is present and STG-lite inlet is requested; setup.cpp will emit syntheticTurbulentInlet/applySyntheticTurbulentInlet with {settings.SyntheticTurbulenceModeCount} spectral modes, per-component RMS normalization from k, Taylor frozen-turbulence advection, TYPE_E inlet refreshes in batch/graphics modes and velocity-field-only treatment."
                    : (hasK ? "AF k column is present but only metadata/profile arrays are guaranteed." : "No usable k column found in CustomWindProfile."),
                Risk = syntheticActive
                    ? $"STG-lite is not a full digital-filter/precursor/Reynolds-stress inlet, assumes isotropic turbulence and frozen-turbulence advection, uses {settings.SyntheticTurbulenceModeCount} spectral modes and correlation length {settings.SyntheticTurbulenceCorrelationCells:F3} cells ({settings.SyntheticTurbulenceCorrelationCells * grid.Dx:F3} m) with source '{lengthScaleSource}', streamwise clipping fraction {settings.SyntheticTurbulenceMinStreamwiseFraction:F3}, and does not reconstruct distribution functions."
                    : "Missing or inactive turbulent inlet can cause systematic underprediction of pedestrian-level velocity ratios.",
                RequiredNextAction = syntheticActive
                    ? "Run empty-tunnel and building native FluidX3D baselines proving downstream U/k preservation and replace/user-justify the inlet length scale before paper claims."
                    : "Enable Synthetic Inlet for diagnostic runs or implement a full DFM/SEM/precursor inlet for formal validation."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_turbulence_length_scale",
                Status = syntheticActive ? (lengthScaleSupported ? "pass" : "risk") : "partial",
                Evidence = syntheticActive
                    ? $"STG-lite correlation length is SyntheticTurbulenceCorrelationCells={settings.SyntheticTurbulenceCorrelationCells:F3}, dx={grid.Dx:F6} m, length={settings.SyntheticTurbulenceCorrelationCells * grid.Dx:F6} m, source='{lengthScaleSource}', gate={lengthScaleGate}."
                    : "No synthetic turbulent inlet length scale is active.",
                Risk = syntheticActive
                    ? (lengthScaleSupported
                        ? "Length-scale source is traceable, but STG-lite still lacks Reynolds-stress tensors, distribution-function reconstruction and native U/k/correlation preservation evidence."
                        : "AF tables provide k but not turbulent length scales or Reynolds-stress tensors; a user-selected lattice correlation length can strongly affect Case A/E pedestrian-level speed ratios.")
                    : "If turbulent inflow is later enabled, its length-scale source must be archived and validated.",
                RequiredNextAction = "For paper-grade turbulent-inflow validation, use AIJ-documented length scales, a precursor/recycling field, or a calibrated DFM/SEM length-scale model and archive the evidence."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_reynolds_stress_tensor",
                Status = syntheticActive ? "risk" : (hasK ? "risk" : "fail"),
                Evidence = syntheticActive
                    ? "STG-lite derives sigma from isotropic k only: R11=R22=R33=2k/3 and R12=R13=R23=0 are assumptions, not measured AIJ Reynolds-stress tensors."
                    : (hasK ? "AF k column is available, but no Reynolds-stress tensor is injected at the inlet." : "No k or Reynolds-stress inlet evidence is active."),
                Risk = "A k-only isotropic inlet can match turbulence kinetic energy while missing anisotropy and shear stresses that control separation, recirculation and pedestrian-level speed ratios.",
                RequiredNextAction = "For paper-grade claims, archive a measured/precursor Reynolds-stress tensor, or prove with empty-tunnel and building baselines that the isotropic-k approximation preserves the target U/k/correlation envelope."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_temporal_sampling",
                Status = syntheticActive
                    ? (expectedPaperAverageStgRefreshes >= PaperRecommendedStgRefreshes ? "partial" : "risk")
                    : "partial",
                Evidence = syntheticActive
                    ? $"STG Update={settings.SyntheticTurbulenceUpdateInterval} steps; final {PaperRecommendedAveragingFrames}-frame average spans {expectedPaperAverageStepSpan} solver steps and is expected to sample {expectedPaperAverageStgRefreshes} inlet refreshes; recommended minimum={PaperRecommendedStgRefreshes}."
                    : "No synthetic turbulent inlet is active, so inlet temporal-refresh sampling is not applicable to this generated case.",
                Risk = syntheticActive && expectedPaperAverageStgRefreshes < PaperRecommendedStgRefreshes
                    ? "The saved-frame count can look sufficient while the inlet fluctuation pattern changes too few times, producing short-sample or pseudo-steady validation metrics."
                    : "Even with enough planned STG refreshes, stationarity and actual sampled VTK source steps must still be proven after the run.",
                RequiredNextAction = syntheticActive
                    ? "Use a smaller STG Update interval or longer final averaging window, then verify inlet temporal correlation from the selected VTK frames."
                    : "If a synthetic inlet is later enabled, archive the update interval, final-window refresh count and inlet-correlation audit."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "inlet_distribution_consistency",
                Status = syntheticActive ? "risk" : (hasK ? "risk" : "fail"),
                Evidence = syntheticActive
                    ? "Generated setup refreshes inlet lbm.u but does not reconstruct FluidX3D distribution functions for the imposed turbulent fluctuation."
                    : (hasK ? "AF k is available, but no turbulent fluctuation is injected into the inlet." : "No k-driven inlet path is active."),
                Risk = "A velocity-only turbulent inlet can dissipate or distort k near the boundary and may cause large Case A/Case E speed-ratio bias even when the GH workflow runs.",
                RequiredNextAction = "For SCI-grade validation, pass an empty-tunnel U/k preservation gate or replace STG-lite with a validated DFM/SEM/precursor/recycling inlet that includes distribution consistency."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "native_fluidx3d_baseline",
                Status = "risk",
                Evidence = "CityLBM can generate the FluidX3D setup.cpp, but this audit cannot prove a paired native FluidX3D run exists.",
                Risk = "If native FluidX3D is not run with the same geometry, inflow, averaging window and probes, software-integration error cannot be separated from solver/protocol error.",
                RequiredNextAction = "Run a native FluidX3D Case A/Case E baseline from the archived setup.cpp, then compare the same probe table against the CityLBM-driven run."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "boundary_conditions",
                Status = "risk",
                Evidence = GetBoundaryConditionSummary(scene.WindDirection, scene.WindProfile) +
                    $" BoundaryProtocolAudit.Gate={boundaryAudit.Gate}; BoundaryProtocolEvidenceGate={boundaryAudit.ProtocolEvidenceGate}.",
                Risk = boundaryClearanceOk
                    ? "Clearance satisfies diagnostic defaults, but TYPE_E inlet/outlet/lateral/top remains a simplified protocol without archived AIJ-equivalent boundary/fetch/roughness evidence."
                    : "Domain clearance or simplified TYPE_E boundary treatment can contaminate the validation field and contribute to systematic bias.",
                RequiredNextAction = "Archive AIJ boundary/fetch/roughness evidence or an empty-tunnel/native baseline boundary-preservation check, then set BoundaryProtocolEvidenceGate=pass only for that documented run."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "wall_roughness_model",
                Status = "risk",
                Evidence = $"RoughnessLength={scene.RoughnessLength:F6} m; ground/buildings are generated as TYPE_S no-slip. Analytic roughness affects mean-profile generation only.",
                Risk = "If the AIJ wind-tunnel floor roughness or approach-flow development is not represented as a boundary/precursor treatment, pedestrian-height speed ratios and k can be systematically biased.",
                RequiredNextAction = "Before paper-grade claims, document the wind-tunnel floor treatment and either validate no-slip against the empty-tunnel U/k gate or implement a rough-wall/precursor/recycling boundary strategy."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "lbm_stability_scaling",
                Status = (maxProfileVelocityLbm <= 0.1 && tau > 0.5 && tau <= 2.0) ? "partial" : "risk",
                Evidence = $"TargetMaxProfileVelocityLbm={maxProfileVelocityLbm:F3}; EstimatedMaxProfileMach={estimatedMach:F3}; LbmTau={tau:F6}; LbmNu={nuLbm:E6}; EstimatedRe={reynolds:F0}; VelocitySet=D3Q19; LesModel={(settings.EnableSmagorinskyLES ? "Smagorinsky" : "BGK_no_LES")}; ProfileScaleSpeed={GetProfileScaleSpeed(scene):F6} m/s.",
                Risk = "The generated setup uses a conservative lattice-velocity target, but actual stability and compressibility must be checked from solver logs and final velocity statistics.",
                RequiredNextAction = "Archive setup.cpp, solver log, viscosity/tau, maximum velocity and any FluidX3D stability warnings for each validation run."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "time_averaging",
                Status = expectedFrames >= PaperRecommendedAveragingFrames && expectedPaperAverageStepSpan >= PaperRecommendedAverageStepSpan ? "partial" : "risk",
                Evidence = $"TimeSteps={settings.TimeSteps}, SaveInterval={settings.SaveInterval}, ExpectedVtkFrameCount={expectedFrames}, PaperRecommendedAveragingFrames={PaperRecommendedAveragingFrames}, PaperRecommendedAverageStepSpan={PaperRecommendedAverageStepSpan}, ExpectedPaperAverageStepSpan={expectedPaperAverageStepSpan}.",
                Risk = expectedFrames >= PaperRecommendedAveragingFrames && expectedPaperAverageStepSpan >= PaperRecommendedAverageStepSpan
                    ? "The planned saved-frame count and final-window step span satisfy the paper-grade preflight, but stationarity still must be proven from actual VTK/logs."
                    : "Too few VTK frames for robust time averaging; a single or short-window field can bias validation metrics.",
                RequiredNextAction = $"Use Read VTK Average Last N={PaperRecommendedAveragingFrames} or higher, archive the actual SourceTimeSteps used for metrics, and verify stationarity before interpreting validation error."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "wind_direction_sign",
                Status = "partial",
                Evidence = $"WindDirection=({scene.WindDirection.X:F6},{scene.WindDirection.Y:F6},{scene.WindDirection.Z:F6}); {GetBoundaryConditionSummary(scene.WindDirection, scene.WindProfile)}.",
                Risk = "A sign or component convention error can create strong systematic bias even when the solver runs normally.",
                RequiredNextAction = "For AIJ Case E N wind, verify that the intended convention is north-to-south and that the generated inlet face and compared velocity component match the official RS table."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "coordinate_transform",
                Status = "partial",
                Evidence = $"domain_origin.json will be written with origin=({grid.Origin.X:F3},{grid.Origin.Y:F3},{grid.Origin.Z:F3}), dx={grid.Dx:F3}, grid={grid.Nx}x{grid.Ny}x{grid.Nz}; CustomTable ProfileOriginZM={grid.Origin.Z:F3} and setup.cpp samples U(z)/k(z) at ProfileOriginZM+(z_cell+0.5)*dx.",
                Risk = "Generated metadata supports coordinate recovery and origin-aware inlet-height sampling, but RS probe projection and wind component sign must be checked against official points.",
                RequiredNextAction = "Archive domain_origin.json, case_metadata.json and a probe-mapping table with nearest/interpolated point distances."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "probe_projection",
                Status = "risk",
                Evidence = "Generated case metadata records the CFD grid, but measured RS probe coordinates are not part of setup.cpp.",
                Risk = "Wrong STL scale, z=2 m height handling, probe tolerance or nearest-cell projection can appear as a large speed-ratio error.",
                RequiredNextAction = "Export a probe audit table with official No., x, y, z, interpolation cell, interpolation distance, failed flag and compared velocity component."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "normalization_basis",
                Status = customTable ? "partial" : "risk",
                Evidence = customTable
                    ? $"ReferenceWindSpeed={scene.WindSpeed:F6} m/s at z_ref={scene.ReferenceHeight:F3} m; ProfileScaleSpeed={GetProfileScaleSpeed(scene):F6} m/s."
                    : $"WindProfile={scene.WindProfile}; ReferenceWindSpeed={scene.WindSpeed:F6} m/s.",
                Risk = "AIJ velocity-ratio comparison must use the official Uref/probe convention, not only the LBM stability scaling speed.",
                RequiredNextAction = "Record Uref source, wind component used for ratio, and whether speed magnitude or streamwise velocity is compared."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "systematic_bias_gate",
                Status = "risk",
                Evidence = "Protocol audit is generated before post-processing, so it cannot verify measured-vs-simulated bias.",
                Risk = "A mean speed-ratio bias around -0.20 to -0.35 indicates a protocol/physics mismatch that should block paper-grade claims even if R2 is acceptable.",
                RequiredNextAction = "After post-processing, record mean bias, regression slope/intercept and a residual map; if bias remains about -34 pp, audit inlet turbulence, boundaries, direction/probes and Uref before tuning parameters."
            };

            yield return new ValidationProtocolAuditItem
            {
                Key = "grid_resolution",
                Status = grid.Dx <= 3.0 ? "partial" : "risk",
                Evidence = $"dx={grid.Dx:F3} m.",
                Risk = grid.Dx <= 3.0
                    ? "Resolution is in the planned formal range, but grid-sensitivity evidence is still required."
                    : "Resolution is smoke-test level and may under-resolve street canyons and pedestrian probes.",
                RequiredNextAction = "Run dx sensitivity, at minimum smoke dx plus formal dx=2-3 m, with the same postprocess protocol."
            };
        }

        private string BuildValidationProtocolAuditMarkdown(string gate, IList<ValidationProtocolAuditItem> items)
        {
            var sb = new StringBuilder();
            sb.AppendLine("# CityLBM validation protocol audit");
            sb.AppendLine();
            sb.AppendLine($"Gate: `{gate}`");
            sb.AppendLine();
            sb.AppendLine("| Item | Status | Evidence | Risk | Required next action |");
            sb.AppendLine("|---|---|---|---|---|");
            foreach (var item in items)
            {
                sb.AppendLine($"| {EscapeMarkdownTable(item.Key)} | `{item.Status}` | {EscapeMarkdownTable(item.Evidence)} | {EscapeMarkdownTable(item.Risk)} | {EscapeMarkdownTable(item.RequiredNextAction)} |");
            }
            sb.AppendLine();
            sb.AppendLine("Status meanings: `pass` = directly satisfied by generated case settings; `partial` = software support exists but run evidence is still required; `risk` = likely protocol risk for paper-grade validation; `fail` = missing required validation input.");
            return sb.ToString();
        }

        private string EscapeMarkdownTable(string value)
        {
            return (value ?? "").Replace("|", "\\|").Replace("\r", " ").Replace("\n", " ");
        }

        private void SaveDomainOrigin(string caseDir, Point3d origin, BoundingBox domainBounds,
                                       int nx, int ny, int nz, double dx)
        {
            try
            {
                // 同时保存到 case 目录和 output 目录（后处理组件从 output 目录旁查找）
                var info = new
                {
                    SchemaVersion = 2,
                    CityLBMVersion = "0.3.0",
                    DomainOriginX = Math.Round(origin.X, 6),
                    DomainOriginY = Math.Round(origin.Y, 6),
                    DomainOriginZ = Math.Round(origin.Z, 6),
                    DomainMinX = Math.Round(domainBounds.Min.X, 6),
                    DomainMinY = Math.Round(domainBounds.Min.Y, 6),
                    DomainMinZ = Math.Round(domainBounds.Min.Z, 6),
                    DomainMaxX = Math.Round(domainBounds.Max.X, 6),
                    DomainMaxY = Math.Round(domainBounds.Max.Y, 6),
                    DomainMaxZ = Math.Round(domainBounds.Max.Z, 6),
                    Nx = nx,
                    Ny = ny,
                    Nz = nz,
                    Dx = Math.Round(dx, 6),
                    DxUnits = "m",
                    VtkCoordinateContract = "VTK grid coordinates are converted to Rhino world meters through domain_origin.json.",
                    Description = "CityLBM domain origin for VTK coordinate mapping"
                };

                string json = JsonConvert.SerializeObject(info, Formatting.Indented);

                // 保存到 case 目录
                string caseJsonPath = Path.Combine(caseDir, "domain_origin.json");
                File.WriteAllText(caseJsonPath, json, Encoding.UTF8);

                // 也保存一份到 output 目录（后处理组件从 VTK 文件同目录查找）
                string outputJsonPath = Path.Combine(caseDir, "output", "domain_origin.json");
                File.WriteAllText(outputJsonPath, json, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[CityLBM] 保存 domain_origin.json 失败: {ex.Message}");
            }
        }

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

    public class ValidationProtocolAuditItem
    {
        public string Key { get; set; }
        public string Status { get; set; }
        public string Evidence { get; set; }
        public string Risk { get; set; }
        public string RequiredNextAction { get; set; }
    }

    internal class BaselineSourceFileRecord
    {
        public string Role { get; set; }
        public string Path { get; set; }
        public bool Exists { get; set; }
        public string HashAlgorithm { get; set; }
        public string Sha256 { get; set; }
    }

    public class FluidX3DSourceValidation
    {
        public string Path { get; set; }
        public bool IsValid { get; set; }
        public string Message { get; set; }
        public bool HasSolution { get; set; }
        public bool HasMakefile { get; set; }
        public bool HasCMakeLists { get; set; }
        public bool HasSrcDirectory { get; set; }
        public bool HasSetupCpp { get; set; }
        public bool HasDefinesHpp { get; set; }
        public bool HasLbmHpp { get; set; }
        public bool HasLbmCpp { get; set; }
        public IList<string> MissingRequiredItems { get; set; }

        public static FluidX3DSourceValidation Invalid(string path, string message)
        {
            return new FluidX3DSourceValidation
            {
                Path = path ?? "",
                IsValid = false,
                Message = message ?? "",
                MissingRequiredItems = new List<string>()
            };
        }
    }

    internal class BoundaryProtocolAudit
    {
        public string Purpose { get; set; }
        public string DominantAxis { get; set; }
        public string InletFace { get; set; }
        public string OutletFace { get; set; }
        public string LateralFaces { get; set; }
        public string TopFace { get; set; }
        public string GroundFace { get; set; }
        public BoundaryTypesRecord BoundaryTypes { get; set; }
        public DimensionRecord DomainSizeM { get; set; }
        public BoundsRecord BuildingBoundsM { get; set; }
        public ClearanceRecord ClearanceM { get; set; }
        public ClearanceRatioRecord ClearanceByBuildingHeight { get; set; }
        public BoundaryThresholdRecord DiagnosticThresholdsByBuildingHeight { get; set; }
        public BoundaryBlockageRecord BlockageDiagnostics { get; set; }
        public BoundaryClearanceCheckRecord ClearanceChecks { get; set; }
        public bool MeetsDiagnosticDomain { get; set; }
        public string Gate { get; set; }
        public string ProtocolEvidenceSource { get; set; }
        public string ProtocolEvidenceGate { get; set; }
        public List<string> GateReasons { get; set; }
        public string RequiredNextAction { get; set; }
    }

    internal class BoundaryTypesRecord
    {
        public string Inlet { get; set; }
        public string Outlet { get; set; }
        public string Lateral { get; set; }
        public string Top { get; set; }
        public string Ground { get; set; }
        public string Buildings { get; set; }
    }

    internal class DimensionRecord
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }
    }

    internal class BoundsRecord
    {
        public double MinX { get; set; }
        public double MinY { get; set; }
        public double MinZ { get; set; }
        public double MaxX { get; set; }
        public double MaxY { get; set; }
        public double MaxZ { get; set; }
        public double Height { get; set; }
    }

    internal class ClearanceRecord
    {
        public double Upstream { get; set; }
        public double Downstream { get; set; }
        public double LateralMinus { get; set; }
        public double LateralPlus { get; set; }
        public double MinLateral { get; set; }
        public double Top { get; set; }
    }

    internal class ClearanceRatioRecord
    {
        public double Upstream { get; set; }
        public double Downstream { get; set; }
        public double MinLateral { get; set; }
        public double Top { get; set; }
    }

    internal class BoundaryThresholdRecord
    {
        public double Upstream { get; set; }
        public double Downstream { get; set; }
        public double MinLateral { get; set; }
        public double Top { get; set; }
    }

    internal class BoundaryBlockageRecord
    {
        public string Method { get; set; }
        public double DomainPlanAreaM2 { get; set; }
        public double BuildingPlanAreaM2 { get; set; }
        public double InletFaceAreaM2 { get; set; }
        public double BuildingFrontalAreaM2 { get; set; }
        public double ApproxPlanBlockageRatio { get; set; }
        public double ApproxFrontalBlockageRatio { get; set; }
        public double DiagnosticMaxFrontalBlockageRatio { get; set; }
        public double DiagnosticMaxPlanBlockageRatio { get; set; }
        public bool FrontalBlockageOk { get; set; }
        public bool PlanBlockageOk { get; set; }
        public string Gate { get; set; }
    }

    internal class BoundaryClearanceCheckRecord
    {
        public bool DomainValid { get; set; }
        public bool BuildingBoundsValid { get; set; }
        public bool BuildingHeightValid { get; set; }
        public bool DomainContainsBuildings { get; set; }
        public bool UpstreamOk { get; set; }
        public bool DownstreamOk { get; set; }
        public bool MinLateralOk { get; set; }
        public bool TopOk { get; set; }
        public bool ApproxFrontalBlockageOk { get; set; }
        public bool ApproxPlanBlockageOk { get; set; }
    }

    /// <summary>模拟物理设置</summary>
    public class SimulationSettings
    {
        public double Viscosity { get; set; } = 1.5e-5;  // 空气运动粘度 (m²/s)
        public double Density { get; set; } = 1.225;     // 空气密度 (kg/m³)
        public int TimeSteps { get; set; } = 40000;      // validation-oriented default; lower values are smoke tests only
        public int SaveInterval { get; set; } = 1000;    // writes enough frames for paper-grade time averaging preflight

        public double InletVelocityX { get; set; }
        public double InletVelocityY { get; set; }
        public double InletVelocityZ { get; set; } = 0;

        // ── v0.2.0: Smagorinsky LES 亚格子模型 ──
        
        /// <summary>
        /// 是否启用 Smagorinsky LES 亚格子模型（v0.2.0 新增）
        /// 启用后可提升高 Reynolds 数流动的模拟精度
        /// 默认 false（向后兼容 BGK 单松弛时间模型）
        /// </summary>
        public bool EnableSmagorinskyLES { get; set; } = false;
        
        /// <summary>
        /// Smagorinsky 常数 Cs（默认 0.12，推荐范围 0.10~0.18）
        /// 较小的 Cs 值：更少耗散，但可能不稳定
        /// 较大的 Cs 值：更多耗散，更稳定但精度降低
        /// 典型值：Cs=0.12 (标准), Cs=0.17 (高湍流强度)
        /// </summary>
        public double SmagorinskyConstantCs { get; set; } = 0.12;

        /// <summary>
        /// 湍流 Prandtl 数（默认 0.5，仅 Smagorinsky 模式有效）
        /// 用于亚格子热通量计算
        /// </summary>
        public double TurbulentPrandtlNumber { get; set; } = 0.5;

        /// <summary>
        /// Enables an experimental STG-lite inlet for CustomTable profiles with k.
        /// This is a correlated, bounded spectral perturbation from isotropic k, not full DFM/SEM.
        /// </summary>
        public bool EnableSyntheticTurbulentInlet { get; set; } = false;

        /// <summary>Multiplier applied to sigma=sqrt(2k/3) from the AF table.</summary>
        public double SyntheticTurbulenceIntensityScale { get; set; } = 1.0;

        /// <summary>Approximate spatial correlation length in lattice cells.</summary>
        public double SyntheticTurbulenceCorrelationCells { get; set; } = 4.0;

        /// <summary>Number of deterministic spectral modes used by the STG-lite inlet.</summary>
        public int SyntheticTurbulenceModeCount { get; set; } = 64;

        /// <summary>
        /// Traceable evidence tag/source for the synthetic turbulence correlation length.
        /// Empty means a diagnostic user-selected lattice-cell length.
        /// </summary>
        public string SyntheticTurbulenceLengthScaleSource { get; set; } = "";

        /// <summary>How often the inlet perturbation pattern is advanced in LBM steps.</summary>
        public int SyntheticTurbulenceUpdateInterval { get; set; } = 25;

        /// <summary>Upper bound of perturbation sigma relative to local mean speed.</summary>
        public double SyntheticTurbulenceMaxFractionOfMean { get; set; } = 0.35;

        /// <summary>
        /// Optional diagnostic lower bound for streamwise velocity as a fraction of local mean speed.
        /// Default 0 disables clipping so k-derived perturbations are not silently truncated.
        /// </summary>
        public double SyntheticTurbulenceMinStreamwiseFraction { get; set; } = 0.0;

        public void SetInletVelocity(Vector3d direction, double speed)
        {
            direction = FluidX3DInterface.NormalizeWindDirection(direction);
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

        /// <summary>Number of VTK frames used when this result is a time-averaged field.</summary>
        public int AveragedFrameCount { get; set; }

        /// <summary>Mean speed magnitude of the averaged velocity field.</summary>
        public double MeanSpeed { get; set; } = double.NaN;

        /// <summary>Mean pointwise speed standard deviation across averaged frames.</summary>
        public double MeanSpeedStdDev { get; set; } = double.NaN;

        /// <summary>Maximum pointwise speed standard deviation across averaged frames.</summary>
        public double MaxSpeedStdDev { get; set; } = double.NaN;

        /// <summary>Mean speed standard deviation divided by mean speed.</summary>
        public double MeanSpeedStdDevRatio { get; set; } = double.NaN;

        /// <summary>Maximum speed standard deviation divided by mean speed.</summary>
        public double MaxSpeedStdDevRatio { get; set; } = double.NaN;

        /// <summary>Source time steps used when this result is a time-averaged field.</summary>
        public List<int> SourceTimeSteps { get; set; } = new List<int>();

        /// <summary>VTK 文件中的原始点总数（采样前）</summary>
        public int RawPointCount { get; set; }

        public int PointCount => Points?.Count ?? 0;
        public int VelocityCount => Velocities?.Count ?? 0;
    }
}
