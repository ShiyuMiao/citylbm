# CityLBM 开发环境配置脚本
# 运行此脚本以配置编译环境

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CityLBM 开发环境配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[警告] 建议以管理员身份运行此脚本" -ForegroundColor Yellow
    Write-Host ""
}

# 1. 检查 Rhino 7
Write-Host "[1/4] 检查 Rhino 7..." -ForegroundColor Green
$rhinoPath = "C:\Program Files\Rhino 7\System\RhinoCommon.dll"
$ghPath = "C:\Program Files\Rhino 7\Plug-ins\Grasshopper\Grasshopper.dll"

if (Test-Path $rhinoPath) {
    Write-Host "  ✓ RhinoCommon.dll 已找到" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 RhinoCommon.dll" -ForegroundColor Red
    Write-Host "    请安装 Rhino 7: https://www.rhino3d.com/download/" -ForegroundColor Yellow
    exit 1
}

if (Test-Path $ghPath) {
    Write-Host "  ✓ Grasshopper.dll 已找到" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 Grasshopper.dll" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. 检查 .NET SDK
Write-Host "[2/4] 检查 .NET SDK..." -ForegroundColor Green
$dotnetSDKs = dotnet --list-sdks 2>$null
if ($dotnetSDKs -match "6\.") {
    Write-Host "  ✓ .NET 6 SDK 已安装" -ForegroundColor Green
    Write-Host "    版本: $dotnetSDKs" -ForegroundColor Gray
} else {
    Write-Host "  ✗ 未安装 .NET 6 SDK" -ForegroundColor Red
    Write-Host ""
    Write-Host "  正在下载 .NET 6 SDK 安装程序..." -ForegroundColor Yellow
    
    $downloadUrl = "https://dotnetcli.azureedge.net/dotnet/Sdk/6.0.419/dotnet-sdk-6.0.419-win-x64.exe"
    $installerPath = "$env:TEMP\dotnet-sdk-6.0.419-win-x64.exe"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "  ✓ 下载完成" -ForegroundColor Green
        Write-Host ""
        Write-Host "  正在启动安装程序..." -ForegroundColor Yellow
        Write-Host "  请按照安装向导完成安装，然后重新运行此脚本" -ForegroundColor Yellow
        Start-Process $installerPath -Wait
        exit 0
    } catch {
        Write-Host "  ✗ 下载失败: $_" -ForegroundColor Red
        Write-Host "  请手动下载安装: https://dotnet.microsoft.com/download/dotnet/6.0" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""

# 3. 检查 Visual Studio
Write-Host "[3/4] 检查 Visual Studio..." -ForegroundColor Green
$vsWherePath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vsWherePath) {
    $vsPath = & $vsWherePath -latest -property installationPath 2>$null
    if ($vsPath) {
        Write-Host "  ✓ Visual Studio 已安装" -ForegroundColor Green
        Write-Host "    路径: $vsPath" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Visual Studio 可能未正确安装" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ 未检测到 Visual Studio Installer" -ForegroundColor Yellow
    Write-Host "    建议安装 VS 2022 Community (免费): https://visualstudio.microsoft.com/downloads/" -ForegroundColor Yellow
    Write-Host "    或者使用 VS Code + C# 扩展" -ForegroundColor Yellow
}
Write-Host ""

# 4. 编译项目
Write-Host "[4/4] 尝试编译项目..." -ForegroundColor Green
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectPath

Write-Host "  执行: dotnet build -c Release" -ForegroundColor Gray
dotnet build -c Release

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "✓ 编译成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "输出文件位置:" -ForegroundColor White
    Write-Host "  bin\Release\CityLBM.dll" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor White
    Write-Host "  1. 将 CityLBM.dll 重命名为 CityLBM.gha" -ForegroundColor Yellow
    Write-Host "  2. 复制到 Grasshopper 组件目录" -ForegroundColor Yellow
    Write-Host "     C:\Users\$env:USERNAME\AppData\Roaming\Grasshopper\Libraries\" -ForegroundColor Yellow
    Write-Host "  3. 在 Rhino 中输入 Grasshopper 命令加载" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 编译失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查错误信息并修复问题后重试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
