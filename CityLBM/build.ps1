# CityLBM 编译脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CityLBM 编译" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "[1/3] 恢复 NuGet 包..." -ForegroundColor Yellow
dotnet restore
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 包恢复失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 包恢复完成" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] 编译项目 (Release)..." -ForegroundColor Yellow
dotnet build -c Release --no-restore 2>&1 | ForEach-Object {
    if ($_ -match "error") {
        Write-Host $_ -ForegroundColor Red
    } elseif ($_ -match "warning") {
        Write-Host $_ -ForegroundColor Yellow
    } elseif ($_ -match "成功|succeeded") {
        Write-Host $_ -ForegroundColor Green
    } else {
        Write-Host $_
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ 编译成功！" -ForegroundColor Green
    Write-Host ""
    
    # 检查输出文件
    $dllPath = "bin\Release\CityLBM.dll"
    if (Test-Path $dllPath) {
        $fileInfo = Get-Item $dllPath
        Write-Host "输出文件:" -ForegroundColor White
        Write-Host "  路径: $dllPath" -ForegroundColor Cyan
        Write-Host "  大小: $([math]::Round($fileInfo.Length / 1KB, 2)) KB" -ForegroundColor Cyan
        Write-Host "  时间: $($fileInfo.LastWriteTime)" -ForegroundColor Cyan
        Write-Host ""
        
        # 创建 .gha 文件
        $ghaDir = "bin\Release\CityLBM"
        if (-not (Test-Path $ghaDir)) {
            New-Item -ItemType Directory -Path $ghaDir -Force | Out-Null
        }
        
        Copy-Item $dllPath "$ghaDir\CityLBM.gha" -Force
        Write-Host "✓ 已创建: $ghaDir\CityLBM.gha" -ForegroundColor Green
        
        # 复制依赖
        Get-ChildItem "bin\Release\*.dll" | Where-Object { $_.Name -ne "CityLBM.dll" } | ForEach-Object {
            Copy-Item $_.FullName $ghaDir -Force
            Write-Host "  复制依赖: $($_.Name)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "编译成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "安装步骤:" -ForegroundColor White
        Write-Host "1. 打开 Rhino 7" -ForegroundColor Yellow
        Write-Host "2. 输入命令: Grasshopper" -ForegroundColor Yellow
        Write-Host "3. 菜单: File → Special Folders → Components Folder" -ForegroundColor Yellow
        Write-Host "4. 复制 CityLBM.gha 到打开的文件夹" -ForegroundColor Yellow
        Write-Host "5. 重启 Grasshopper" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 编译失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
