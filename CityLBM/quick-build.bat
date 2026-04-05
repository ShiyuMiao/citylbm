@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在编译...
dotnet build -c Release
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 编译成功！
    echo ========================================
    if not exist "bin\Release\CityLBM" mkdir "bin\Release\CityLBM"
    copy /Y "bin\Release\CityLBM.dll" "bin\Release\CityLBM\CityLBM.gha"
    echo 已创建: bin\Release\CityLBM\CityLBM.gha
) else (
    echo.
    echo ========================================
    echo 编译失败
    echo ========================================
)
