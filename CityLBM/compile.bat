@echo off
chcp 65001 >nul
echo ========================================
echo CityLBM 快速编译脚本
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 清理旧的编译文件...
if exist "bin\Release\CityLBM.dll" del "bin\Release\CityLBM.dll"
if exist "bin\Release\CityLBM.gha" del "bin\Release\CityLBM.gha"
echo   ✓ 清理完成
echo.

echo [2/2] 编译项目 (Release 配置)...
dotnet build -c Release

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ 编译成功！
    echo ========================================
    echo.
    
    REM 检查是否需要复制到 Grasshopper 库目录
    set GH_LIB=%APPDATA%\Grasshopper\Libraries
    
    echo 正在准备 Grasshopper 插件文件...
    
    REM 创建输出目录
    if not exist "bin\Release\CityLBM" mkdir "bin\Release\CityLBM"
    
    REM 复制主DLL并重命名为.gha
    copy /Y "bin\Release\CityLBM.dll" "bin\Release\CityLBM\CityLBM.gha" >nul
    
    REM 复制依赖的DLL
    copy /Y "bin\Release\Newtonsoft.Json.dll" "bin\Release\CityLBM\" >nul 2>&1
    copy /Y "bin\Release\NLog.dll" "bin\Release\CityLBM\" >nul 2>&1
    
    echo.
    echo 输出文件位置:
    echo   %CD%\bin\Release\CityLBM\CityLBM.gha
    echo.
    echo 下一步操作:
    echo   1. 打开 Rhino 7
    echo   2. 输入命令: Grasshopper
    echo   3. 在 Grasshopper 中，菜单 File ^> Special Folders ^> Components Folder
    echo   4. 将 CityLBM.gha 文件复制到打开的文件夹中
    echo   5. 重启 Grasshopper，组件将出现在 CityLBM 标签页下
    echo.
) else (
    echo.
    echo ========================================
    echo ✗ 编译失败
    echo ========================================
    echo.
    echo 请检查上面的错误信息
    echo.
)

echo 按任意键退出...
pause >nul
