@echo off
echo ============================================
echo   CityLBM v0.2.1 - One-Click Installer
echo ============================================
echo.

set "GH_LIB=%APPDATA%\Grasshopper\Libraries"
set "CITYLBM_DATA=%APPDATA%\CityLBM"

:: Create folders
if not exist "%GH_LIB%" mkdir "%GH_LIB%"
if not exist "%CITYLBM_DATA%" mkdir "%CITYLBM_DATA%"

:: Install plugin
echo [1/2] Installing CityLBM plugin...
copy /Y "%~dp0bin\CityLBM.gha" "%GH_LIB%\CityLBM.gha"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy plugin. Close Rhino and try again.
    pause
    exit /b 1
)

:: Install pre-compiled solver
echo [2/2] Installing FluidX3D solver (pre-compiled, no C++ needed)...
copy /Y "%~dp0bin\FluidX3D.exe" "%CITYLBM_DATA%\FluidX3D.exe"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Solver copy failed. You may need to run as administrator.
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo   Plugin: %GH_LIB%\CityLBM.gha
echo   Solver: %CITYLBM_DATA%\FluidX3D.exe
echo.
echo   Next steps:
echo   1. Restart Rhino
echo   2. Type 'Grasshopper' in Rhino command line
echo   3. Find 'CityLBM' tab with 20 components
echo.
pause