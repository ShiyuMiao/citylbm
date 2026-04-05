# .NET 6 SDK 安装脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ".NET 6 SDK 安装程序" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 下载 .NET 6 SDK
$downloadUrl = "https://dotnetcli.azureedge.net/dotnet/Sdk/6.0.419/dotnet-sdk-6.0.419-win-x64.exe"
$installerPath = "$env:TEMP\dotnet-sdk-6.0.419-win-x64.exe"

Write-Host "正在下载 .NET 6 SDK..." -ForegroundColor Yellow
Write-Host "下载地址: $downloadUrl" -ForegroundColor Gray

try {
    # 使用 WebClient 下载
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $installerPath)
    
    Write-Host "✓ 下载完成" -ForegroundColor Green
    Write-Host "文件位置: $installerPath" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "正在启动安装程序..." -ForegroundColor Yellow
    Write-Host "请在弹出的安装窗口中完成安装" -ForegroundColor Yellow
    Write-Host ""
    
    # 启动安装程序（交互式安装）
    Start-Process $installerPath -Wait
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "安装程序已完成" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 刷新环境变量
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # 验证安装
    Write-Host "验证安装..." -ForegroundColor Yellow
    $dotnetVersion = dotnet --version 2>$null
    if ($dotnetVersion) {
        Write-Host "  ✓ .NET SDK 版本: $dotnetVersion" -ForegroundColor Green
        Write-Host ""
        Write-Host "下一步:" -ForegroundColor White
        Write-Host "  运行 .\compile.bat 编译项目" -ForegroundColor Yellow
    } else {
        Write-Host "  请重启 PowerShell 后再运行 compile.bat" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ 下载失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载安装 .NET 6 SDK:" -ForegroundColor Yellow
    Write-Host "  https://dotnet.microsoft.com/download/dotnet/6.0" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
