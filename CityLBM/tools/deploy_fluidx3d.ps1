<#
.SYNOPSIS
    CityLBM → FluidX3D 自动化部署脚本
    
.DESCRIPTION
    将 CityLBM 生成的 Case 文件自动部署到 FluidX3D，编译并运行模拟。
    支持三种模式：
      - Mode 0: 仅复制文件（部署）
      - Mode 1: 部署 + 编译
      - Mode 2: 部署 + 编译 + 运行
    
.PARAMETER CaseDir
    CityLBM 生成的 Case 目录路径（包含 setup.cpp, defines.hpp, buildings.stl）

.PARAMETER FluidX3DPath
    FluidX3D 源码根目录（包含 FluidX3D.sln）

.PARAMETER Mode
    运行模式：
      0 = 仅部署文件（默认）
      1 = 部署 + 编译
      2 = 部署 + 编译 + 运行

.EXAMPLE
    .\deploy_fluidx3d.ps1 -CaseDir "C:\Users\MSY\AppData\Local\Temp\CityLBM\MyScene" -FluidX3DPath "D:\FluidX3D" -Mode 2

.NOTES
    Author: CityLBM Team
    Version: 1.0
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="CityLBM Case 目录路径")]
    [string]$CaseDir,
    
    [Parameter(Mandatory=$true, HelpMessage="FluidX3D 源码根目录")]
    [string]$FluidX3DPath,
    
    [Parameter(Mandatory=$false, HelpMessage="运行模式: 0=仅部署, 1=部署+编译, 2=全流程")]
    [ValidateSet(0, 1, 2)]
    [int]$Mode = 0
)

# =====================================================
# 配置
# =====================================================
$ErrorActionPreference = "Stop"
$StartTime = Get-Date

# 颜色输出函数
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error2 { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Warning2 { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }

# =====================================================
# 步骤 1: 验证输入
# =====================================================
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  CityLBM → FluidX3D 自动化部署" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""

Write-Info "验证输入..."

# 检查 Case 目录
if (-not (Test-Path $CaseDir)) {
    Write-Error2 "Case 目录不存在: $CaseDir"
    exit 1
}

$caseFiles = @("setup.cpp", "defines.hpp", "buildings.stl")
$missingFiles = @()
foreach ($file in $caseFiles) {
    if (-not (Test-Path (Join-Path $CaseDir $file))) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Error2 "Case 目录缺少文件: $($missingFiles -join ', ')"
    exit 1
}
Write-Success "Case 目录验证通过"

# 检查 FluidX3D 目录
if (-not (Test-Path $FluidX3DPath)) {
    Write-Error2 "FluidX3D 目录不存在: $FluidX3DPath"
    Write-Info "请下载 FluidX3D: https://github.com/ProjectPhysX/FluidX3D"
    exit 1
}

$fluidSrcDir = Join-Path $FluidX3DPath "src"
if (-not (Test-Path $fluidSrcDir)) {
    Write-Error2 "找不到 FluidX3D/src 目录"
    exit 1
}

$slnFile = Join-Path $FluidX3DPath "FluidX3D.sln"
$hasSolution = Test-Path $slnFile

Write-Success "FluidX3D 目录验证通过"
Write-Host ""

# =====================================================
# 步骤 2: 备份原始文件
# =====================================================
Write-Info "备份原始文件..."

$backupDir = Join-Path $FluidX3DPath ".citylbm_backup"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

$backupFiles = @(
    @{ Src = Join-Path $fluidSrcDir "setup.cpp"; Dst = Join-Path $backupDir "setup.cpp.original" },
    @{ Src = Join-Path $fluidSrcDir "defines.hpp"; Dst = Join-Path $backupDir "defines.hpp.original" }
)

foreach ($bf in $backupFiles) {
    if ((Test-Path $bf.Src) -and -not (Test-Path $bf.Dst)) {
        Copy-Item $bf.Src $bf.Dst -Force
        Write-Success "备份: $(Split-Path $bf.Src -Leaf)"
    }
}

Write-Host ""

# =====================================================
# 步骤 3: 部署文件
# =====================================================
Write-Info "部署 Case 文件..."

# 复制 setup.cpp
Copy-Item (Join-Path $CaseDir "setup.cpp") (Join-Path $fluidSrcDir "setup.cpp") -Force
Write-Success "setup.cpp → FluidX3D/src/"

# 复制 defines.hpp
Copy-Item (Join-Path $CaseDir "defines.hpp") (Join-Path $fluidSrcDir "defines.hpp") -Force
Write-Success "defines.hpp → FluidX3D/src/"

# 复制 buildings.stl
Copy-Item (Join-Path $CaseDir "buildings.stl") (Join-Path $FluidX3DPath "buildings.stl") -Force
Write-Success "buildings.stl → FluidX3D/"

# 创建输出目录
$outputDir = Join-Path $FluidX3DPath "output"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Success "创建 output/ 目录"
}

Write-Host ""

if ($Mode -eq 0) {
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Yellow
    Write-Host "  Mode 0: 仅部署完成" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "下一步："
    Write-Host "  1. 打开 Visual Studio"
    Write-Host "  2. 加载 $slnFile"
    Write-Host "  3. Build → Release x64"
    Write-Host "  4. 运行 FluidX3D.exe"
    Write-Host ""
    Write-Host "或使用命令行："
    Write-Host "  msbuild `"$slnFile`" /p:Configuration=Release /p:Platform=x64"
    Write-Host ""
    
    $EndTime = Get-Date
    Write-Host "完成时间: $($EndTime - $StartTime)" -ForegroundColor Gray
    exit 0
}

# =====================================================
# 步骤 4: 查找 MSBuild
# =====================================================
Write-Info "查找 MSBuild..."

$msbuildPaths = @(
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
)

$msbuild = $null
foreach ($path in $msbuildPaths) {
    if (Test-Path $path) {
        $msbuild = $path
        break
    }
}

if (-not $msbuild) {
    # 尝试 where 命令
    try {
        $msbuild = (Get-Command MSBuild.exe -ErrorAction Stop).Source
    } catch {
        Write-Error2 "找不到 MSBuild。请安装 Visual Studio 或 Build Tools。"
        Write-Info "下载地址: https://visualstudio.microsoft.com/downloads/"
        exit 1
    }
}

Write-Success "MSBuild: $msbuild"
Write-Host ""

if (-not $hasSolution) {
    Write-Error2 "找不到 FluidX3D.sln，无法编译"
    exit 1
}

# =====================================================
# 步骤 5: 编译
# =====================================================
Write-Info "编译 FluidX3D..."
Write-Host ""

$buildArgs = @(
    "`"$slnFile`"",
    "/t:Build",
    "/p:Configuration=Release",
    "/p:Platform=x64",
    "/m",
    "/nologo",
    "/verbosity:minimal"
)

$buildOutput = & $msbuild $buildArgs 2>&1
$buildExitCode = $LASTEXITCODE

Write-Host $buildOutput -ForegroundColor $(if ($buildExitCode -eq 0) { "Gray" } else { "Red" })
Write-Host ""

if ($buildExitCode -ne 0) {
    Write-Error2 "编译失败 (Exit Code: $buildExitCode)"
    Write-Info "检查错误信息并修复后重试"
    exit 1
}

Write-Success "编译成功！"
Write-Host ""

if ($Mode -eq 1) {
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Yellow
    Write-Host "  Mode 1: 部署 + 编译完成" -ForegroundColor Yellow
    Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "下一步："
    Write-Host "  双击运行 FluidX3D.exe"
    Write-Host "  或在命令行执行: .\FluidX3D.exe"
    Write-Host ""
    
    $EndTime = Get-Date
    Write-Host "完成时间: $($EndTime - $StartTime)" -ForegroundColor Gray
    exit 0
}

# =====================================================
# 步骤 6: 运行
# =====================================================
Write-Info "运行 FluidX3D..."
Write-Host ""

# 查找可执行文件
$exeCandidates = @(
    Join-Path $FluidX3DPath "bin\Release\x64\FluidX3D.exe",
    Join-Path $FluidX3DPath "bin\Release\FluidX3D.exe",
    Join-Path $FluidX3DPath "x64\Release\FluidX3D.exe",
    Join-Path $FluidX3DPath "FluidX3D.exe"
)

$exePath = $null
foreach ($candidate in $exeCandidates) {
    if (Test-Path $candidate) {
        $exePath = $candidate
        break
    }
}

if (-not $exePath) {
    Write-Error2 "找不到 FluidX3D.exe"
    Write-Info "请检查编译输出目录"
    exit 1
}

Write-Success "可执行文件: $exePath"
Write-Host ""

# 运行
Push-Location $FluidX3DPath
try {
    $runStart = Get-Date
    & $exePath
    $runExitCode = $LASTEXITCODE
    $runEnd = Get-Date
} catch {
    Write-Error2 "运行出错: $_"
    Pop-Location
    exit 1
}
Pop-Location

Write-Host ""
Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Green
Write-Host "  Mode 2: 完整流程执行完成！" -ForegroundColor Green
Write-Host "───────────────────────────────────────────────────────" -ForegroundColor Green
Write-Host ""

# =====================================================
# 步骤 7: 收集结果
# =====================================================
Write-Info "检查输出文件..."

$outputDir = Join-Path $FluidX3DPath "output"
if (Test-Path $outputDir) {
    $vtkFiles = Get-ChildItem $outputDir -Filter "*.vtk" -ErrorAction SilentlyContinue
    if ($vtkFiles.Count -gt 0) {
        Write-Success "生成 $($vtkFiles.Count) 个 VTK 文件"
        
        # 复制 VTK 回 Case 目录
        $caseOutputDir = Join-Path $CaseDir "output"
        if (-not (Test-Path $caseOutputDir)) {
            New-Item -ItemType Directory -Path $caseOutputDir -Force | Out-Null
        }
        
        Copy-Item (Join-Path $outputDir "*.vtk") $caseOutputDir -Force
        Write-Success "VTK 文件已复制到: $caseOutputDir"
        
        Write-Host ""
        Write-Host "在 Grasshopper 中使用 Read VTK 组件读取:" -ForegroundColor Cyan
        Write-Host "  $caseOutputDir" -ForegroundColor White
    } else {
        Write-Warning2 "未找到 VTK 输出文件"
    }
}

Write-Host ""
$EndTime = Get-Date
$TotalDuration = $EndTime - $StartTime
Write-Host "总耗时: $($TotalDuration.TotalMinutes:F1) 分钟" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
