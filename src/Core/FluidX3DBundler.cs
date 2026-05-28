using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace CityLBM.Solver
{
    public class FluidX3DBundler
    {
        public static readonly string DataRoot =
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "CityLBM");
        public static readonly string SourceDir = Path.Combine(DataRoot, "FluidX3D");
        public static readonly string BuildCacheDir = Path.Combine(DataRoot, "BuildCache");
        private const string RESOURCE_PREFIX = "CityLBM.Resources.FluidX3D.";
        private const string RESOURCE_SOURCE_ZIP = "FluidX3D.source.zip";

        public bool IsInitialized { get; private set; }
        public string InitLog { get; private set; }
        public string DetectedCompiler { get; private set; }
        public bool IsCompilerAvailable => !string.IsNullOrEmpty(DetectedCompiler);

        private static readonly Lazy<FluidX3DBundler> _instance =
            new Lazy<FluidX3DBundler>(() => new FluidX3DBundler());
        public static FluidX3DBundler Instance => _instance.Value;

        private FluidX3DBundler()
        {
            Directory.CreateDirectory(DataRoot);
            Directory.CreateDirectory(BuildCacheDir);
        }

        public bool EnsureInitialized()
        {
            if (IsInitialized && IsCompilerAvailable) return true;
            var log = new StringBuilder();
            log.AppendLine("=== CityLBM FluidX3D Bundler ===");
            log.AppendLine("Time: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            if (!IsInitialized)
            {
                log.AppendLine("[1/2] Extracting FluidX3D source...");
                if (!ExtractSourceIfNeeded(log))
                {
                    log.AppendLine("[FAIL] Source extraction failed.");
                    InitLog = log.ToString();
                    return false;
                }
                IsInitialized = true;
            }
            log.AppendLine("[2/2] Detecting C++ compiler...");
            DetectedCompiler = DetectCompiler(log);
            log.AppendLine("Compiler: " + (IsCompilerAvailable ? DetectedCompiler : "NOT FOUND"));
            InitLog = log.ToString();
            SaveInitLog();
            return true;
        }

        public string GetOrBuildExe(int nx, int ny, int nz,
                                     string definesContent, string setupContent,
                                     string stlPath,
                                     Action<int, string> progressCallback = null)
        {
            if (!IsCompilerAvailable)
            {
                progressCallback?.Invoke(0, "No C++ compiler found. Install VS Build Tools or MinGW.");
                return null;
            }
            string configHash = ComputeConfigHash(nx, ny, nz, definesContent, setupContent);
            string cacheDir = Path.Combine(BuildCacheDir, configHash);
            string cachedExe = Path.Combine(cacheDir, "FluidX3D.exe");
            if (File.Exists(cachedExe))
            {
                progressCallback?.Invoke(100, "Hit cache: " + configHash.Substring(0, 8));
                return cachedExe;
            }
            progressCallback?.Invoke(0, "Building FluidX3D (grid=" + nx + "x" + ny + "x" + nz + ")...");
            Directory.CreateDirectory(cacheDir);
            string srcDir = Path.Combine(cacheDir, "src");
            Directory.CreateDirectory(srcDir);
            File.WriteAllText(Path.Combine(srcDir, "defines.hpp"), definesContent, Encoding.UTF8);
            File.WriteAllText(Path.Combine(srcDir, "setup.cpp"), setupContent, Encoding.UTF8);
            CopySourceTreeExcluding(SourceDir, cacheDir, new[] { "src\\setup.cpp", "src\\defines.hpp" });
            string dstStl = Path.Combine(cacheDir, "buildings.stl");
            File.Copy(stlPath, dstStl, overwrite: true);
            progressCallback?.Invoke(10, "Compiling...");
            bool ok = BuildFluidX3D(cacheDir, progressCallback);
            if (ok && File.Exists(cachedExe))
            {
                progressCallback?.Invoke(100, "Build cached: " + configHash.Substring(0, 8));
                return cachedExe;
            }
            progressCallback?.Invoke(0, "Build failed.");
            try { Directory.Delete(cacheDir, true); } catch { }
            return null;
        }

        public string GetInitLog()
        {
            if (string.IsNullOrEmpty(InitLog)) EnsureInitialized();
            return InitLog ?? "Not initialized";
        }

        public void ClearCache()
        {
            if (Directory.Exists(BuildCacheDir))
            {
                Directory.Delete(BuildCacheDir, true);
                Directory.CreateDirectory(BuildCacheDir);
            }
        }

        public void SaveInitLog()
        {
            if (!string.IsNullOrEmpty(InitLog))
                File.WriteAllText(Path.Combine(DataRoot, "init.log"), InitLog, Encoding.UTF8);
        }

        private bool ExtractSourceIfNeeded(StringBuilder log)
        {
            bool exists = Directory.Exists(SourceDir) &&
                          Directory.Exists(Path.Combine(SourceDir, "src")) &&
                          (File.Exists(Path.Combine(SourceDir, "FluidX3D.sln")) ||
                           File.Exists(Path.Combine(SourceDir, "Makefile")) ||
                           File.Exists(Path.Combine(SourceDir, "CMakeLists.txt")));
            if (exists) { log.AppendLine("  Source already extracted."); return true; }
            try
            {
                var asm = Assembly.GetExecutingAssembly();
                string rn = RESOURCE_PREFIX + RESOURCE_SOURCE_ZIP;
                using (var s = asm.GetManifestResourceStream(rn))
                {
                    if (s == null) { log.AppendLine("  Resource not found: " + rn); return false; }
                    if (Directory.Exists(SourceDir)) Directory.Delete(SourceDir, true);
                    using (var za = new ZipArchive(s, ZipArchiveMode.Read))
                        za.ExtractToDirectory(SourceDir);
                    log.AppendLine("  Extracted to: " + SourceDir);
                    return true;
                }
            }
            catch (Exception ex) { log.AppendLine("  Error: " + ex.Message); return false; }
        }

        private void CopySourceTreeExcluding(string srcRoot, string dstRoot, string[] excludes)
        {
            var exSet = new HashSet<string>(excludes.Select(p => p.Replace('/', '\\').TrimStart('\\')), StringComparer.OrdinalIgnoreCase);
            foreach (string fp in Directory.GetFiles(srcRoot, "*", SearchOption.AllDirectories))
            {
                string rel = fp.Substring(srcRoot.Length).TrimStart('\\', '/');
                if (exSet.Contains(rel)) continue;
                string dp = Path.Combine(dstRoot, rel);
                Directory.CreateDirectory(Path.GetDirectoryName(dp));
                File.Copy(fp, dp, true);
            }
        }

        private string DetectCompiler(StringBuilder log)
        {
            string msbuild = FindMSBuild();
            if (!string.IsNullOrEmpty(msbuild)) { log.AppendLine("  MSBuild: " + msbuild); return "MSBuild"; }
            if (FindInPath("clang-cl.exe")) { log.AppendLine("  clang-cl"); return "clang-cl"; }
            if (FindInPath("g++.exe")) { log.AppendLine("  MinGW g++"); return "MinGW"; }
            if (FindInPath("cl.exe")) { log.AppendLine("  MSVC cl.exe"); return "MSVC"; }
            log.AppendLine("  No compiler found");
            return null;
        }

        private string FindMSBuild()
        {
            string vs2022 = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"Microsoft Visual Studio\2022");
            if (Directory.Exists(vs2022))
            {
                foreach (var ed in new[] { "Enterprise", "Professional", "Community", "BuildTools" })
                {
                    string mb = Path.Combine(vs2022, ed, @"MSBuild\Current\Bin\MSBuild.exe");
                    if (File.Exists(mb)) return mb;
                }
            }
            string vs2019 = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Microsoft Visual Studio\2019");
            if (Directory.Exists(vs2019))
            {
                foreach (var ed in new[] { "Enterprise", "Professional", "Community", "BuildTools" })
                {
                    string mb = Path.Combine(vs2019, ed, @"MSBuild\Current\Bin\MSBuild.exe");
                    if (File.Exists(mb)) return mb;
                }
            }
            string vswhere = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"Microsoft Visual Studio\Installer\vswhere.exe");
            if (File.Exists(vswhere))
            {
                try
                {
                    var psi = new ProcessStartInfo(vswhere, "-latest -requires Microsoft.Component.MSBuild -find MSBuild\\**\\Bin\\MSBuild.exe")
                    { RedirectStandardOutput = true, UseShellExecute = false, CreateNoWindow = true };
                    using (var p = Process.Start(psi)) { string o = p.StandardOutput.ReadToEnd().Trim(); p.WaitForExit(); if (!string.IsNullOrEmpty(o) && File.Exists(o)) return o; }
                }
                catch { }
            }
            return null;
        }

        private bool FindInPath(string exeName)
        {
            try
            {
                string pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
                foreach (string dir in pathEnv.Split(';'))
                    if (File.Exists(Path.Combine(dir.Trim(), exeName))) return true;
            }
            catch { }
            return false;
        }

        private bool BuildFluidX3D(string buildDir, Action<int, string> progressCallback)
        {
            string sln = Path.Combine(buildDir, "FluidX3D.sln");
            if (File.Exists(sln) && DetectedCompiler == "MSBuild")
                return BuildWithMSBuild(buildDir, sln, progressCallback);
            string mf = Path.Combine(buildDir, "Makefile");
            if (File.Exists(mf) && (DetectedCompiler == "MinGW" || DetectedCompiler == "clang-cl"))
                return BuildWithMake(buildDir, progressCallback);
            string msbuild = FindMSBuild();
            if (!string.IsNullOrEmpty(msbuild) && File.Exists(sln))
                return BuildWithMSBuild(buildDir, sln, progressCallback);
            progressCallback?.Invoke(0, "Unsupported build configuration.");
            return false;
        }

        private bool BuildWithMSBuild(string buildDir, string slnFile, Action<int, string> progressCallback)
        {
            string msbuild = FindMSBuild();
            if (string.IsNullOrEmpty(msbuild)) { progressCallback?.Invoke(0, "MSBuild not found"); return false; }
            progressCallback?.Invoke(20, "MSBuild compiling...");
            var psi = new ProcessStartInfo(msbuild, "\"" + slnFile + "\" /p:Configuration=Release /p:Platform=x64 /m /v:minimal")
            { WorkingDirectory = buildDir, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
            using (var p = new Process { StartInfo = psi })
            {
                p.Start();
                int dc = 0;
                while (!p.HasExited) { p.WaitForExit(2000); dc++; progressCallback?.Invoke(Math.Min(20 + dc * 3, 80), "Compiling..."); }
                progressCallback?.Invoke(90, "Checking output...");
                if (p.ExitCode != 0) { progressCallback?.Invoke(0, "MSBuild exit code: " + p.ExitCode); return false; }
            }
            string exe = Path.Combine(buildDir, "bin", "FluidX3D.exe");
            if (!File.Exists(exe)) exe = Path.Combine(buildDir, "FluidX3D.exe");
            if (File.Exists(exe)) { string dest = Path.Combine(buildDir, "FluidX3D.exe"); if (exe != dest) File.Copy(exe, dest, true); return true; }
            progressCallback?.Invoke(0, "FluidX3D.exe not found");
            return false;
        }

        private bool BuildWithMake(string buildDir, Action<int, string> progressCallback)
        {
            string makeCmd = DetectedCompiler == "MinGW" ? "mingw32-make" : "make";
            progressCallback?.Invoke(20, "Make compiling...");
            var psi = new ProcessStartInfo(makeCmd, "-j4") { WorkingDirectory = buildDir, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
            using (var p = new Process { StartInfo = psi })
            {
                p.Start();
                int dc = 0;
                while (!p.HasExited) { p.WaitForExit(2000); dc++; progressCallback?.Invoke(Math.Min(20 + dc * 5, 80), "Compiling..."); }
                if (p.ExitCode != 0) { progressCallback?.Invoke(0, "Make exit code: " + p.ExitCode); return false; }
            }
            string exe = Path.Combine(buildDir, "bin", "FluidX3D.exe");
            if (!File.Exists(exe)) exe = Path.Combine(buildDir, "FluidX3D.exe");
            return File.Exists(exe);
        }

        private string ComputeConfigHash(int nx, int ny, int nz, string defines, string setup)
        {
            using (var sha = SHA256.Create())
            {
                string input = nx + "x" + ny + "x" + nz + "|" + defines + "|" + setup;
                byte[] hash = sha.ComputeHash(Encoding.UTF8.GetBytes(input));
                return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
            }
        }

        public List<string> ListCachedConfigs()
        {
            var configs = new List<string>();
            if (!Directory.Exists(BuildCacheDir)) return configs;
            foreach (var dir in Directory.GetDirectories(BuildCacheDir))
            {
                string exe = Path.Combine(dir, "FluidX3D.exe");
                if (File.Exists(exe))
                {
                    string hash = Path.GetFileName(dir);
                    string size = new FileInfo(exe).Length / 1024 / 1024 + " MB";
                    configs.Add(hash.Substring(0, 8) + "... (" + size + ")");
                }
            }
            return configs;
        }
    }
}