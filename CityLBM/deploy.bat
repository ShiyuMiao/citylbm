@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo CityLBM 一键编译部署
echo ========================================
echo.

cd /d "%~dp0"

:: 清理旧文件
echo [1/3] 清理旧文件...
if exist "bin\Release\*.gha" del /q "bin\Release\*.gha" 2>nul
if exist "bin\Release\*.dll" del /q "bin\Release\*.dll" 2>nul
echo   √ 清理完成
echo.

:: 编译
echo [2/3] 编译项目 (Release 配置)...
dotnet build -c Release --no-incremental
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo × 编译失败！
    echo ========================================
    pause
    exit /b 1
)
echo   √ 编译成功
echo.

:: 部署
echo [3/3] 部署到 Grasshopper...
set "GH_LIB=%APPDATA%\Grasshopper\Libraries"
if not exist "%GH_LIB%" mkdir "%GH_LIB%"
copy /y "bin\Release\CityLBM.gha" "%GH_LIB%\CityLBM.gha" >nul
if %errorlevel% neq 0 (
    echo   × 复制失败
    pause
    exit /b 1
)
echo   √ 已部署到: %GH_LIB%\CityLBM.gha
echo.

:: 显示文件信息
echo ========================================
echo √ 编译部署成功！
echo ========================================
echo.
echo 插件路径: %GH_LIB%\CityLBM.gha
echo 文件大小:
for %%A in ("%GH_LIB%\CityLBM.gha") do echo   %%~zA 字节
echo.
echo 请执行以下步骤加载插件:
echo   1. 关闭 Grasshopper 和 Rhino (如果正在运行)
echo   2. 重新打开 Rhino 7
echo   3. 输入命令: Grasshopper
echo   4. 在组件面板中找到 "CityLBM" 标签页
echo.
pause
