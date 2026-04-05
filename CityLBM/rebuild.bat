@echo off
chcp 65001 >nul
echo ========================================
echo CityLBM 重新编译
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 清理旧文件...
if exist "bin\Release\CityLBM\*.gha" del /q "bin\Release\CityLBM\*.gha"
if exist "bin\Release\CityLBM\*.dll" del /q "bin\Release\CityLBM\*.dll"
echo   √ 清理完成
echo.

echo [2/2] 编译项目 (Release配置)...
dotnet build -c Release --no-incremental

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo × 编译失败
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo √ 编译成功！
echo ========================================
echo.
echo 输出文件: bin\Release\CityLBM\CityLBM.gha
echo.

:: 自动复制到Grasshopper库
set GH_LIB=%APPDATA%\Grasshopper\Libraries
if not exist "%GH_LIB%" mkdir "%GH_LIB%"
copy /y "bin\Release\CityLBM\CityLBM.gha" "%GH_LIB%\CityLBM.gha" >nul
echo 已复制到: %GH_LIB%\CityLBM.gha
echo.

echo 请重启 Rhino 和 Grasshopper 以加载插件。
pause
