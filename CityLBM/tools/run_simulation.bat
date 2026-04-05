@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =====================================================
:: CityLBM → FluidX3D 自动化部署批处理
:: =====================================================

echo ═══════════════════════════════════════════════════════
echo   CityLBM ^> FluidX3D 自动化部署
echo ═══════════════════════════════════════════════════════
echo.

:: 设置路径（用户需要修改）
set "CASE_DIR=C:\Users\MSY\AppData\Local\Temp\CityLBM\CityLBM Scene"
set "FLUIDX3D_PATH=D:\FluidX3D"

:: 检查路径是否存在
if not exist "%CASE_DIR%" (
    echo [错误] Case 目录不存在: %CASE_DIR%
    echo 请修改脚本中的 CASE_DIR 变量
    pause
    exit /b 1
)

if not exist "%FLUIDX3D_PATH%" (
    echo [错误] FluidX3D 目录不存在: %FLUIDX3D_PATH%
    echo 请修改脚本中的 FLUIDX3D_PATH 变量
    echo.
    echo 下载 FluidX3D: https://github.com/ProjectPhysX/FluidX3D
    pause
    exit /b 1
)

:: 调用 PowerShell 脚本
powershell -ExecutionPolicy Bypass -File "%~dp0deploy_fluidx3d.ps1" ^
    -CaseDir "%CASE_DIR%" ^
    -FluidX3DPath "%FLUIDX3D_PATH%" ^
    -Mode 2

echo.
pause
