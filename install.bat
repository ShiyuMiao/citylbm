@echo off
echo ============================================
echo   CityLBM v0.2.1 - One-Click Installer
echo ============================================
echo.

set "GH_LIB=%APPDATA%\Grasshopper\Libraries"
set "CITYLBM_DATA=%APPDATA%\CityLBM"

:: Create folders
if not exist "%GH_LIB%" mkdir "%GH_LIB%"
if not exist "%GH_LIB%\Icons" mkdir "%GH_LIB%\Icons"
if not exist "%CITYLBM_DATA%" mkdir "%CITYLBM_DATA%"

:: Install plugin + dependencies
echo [1/4] Installing CityLBM plugin...
copy /Y "%~dp0bin\CityLBM.gha" "%GH_LIB%\CityLBM.gha"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy plugin. Close Rhino and try again.
    pause
    exit /b 1
)
copy /Y "%~dp0bin\Newtonsoft.Json.dll" "%GH_LIB%\Newtonsoft.Json.dll"
copy /Y "%~dp0bin\NLog.dll" "%GH_LIB%\NLog.dll"

:: Install icons (24x24, Grasshopper standard)
echo [2/4] Installing component icons...
xcopy /Y /Q "%~dp0bin\Icons\*.png" "%GH_LIB%\Icons\"

:: Install pre-compiled solver
echo [3/4] Installing FluidX3D solver (pre-compiled)...
copy /Y "%~dp0bin\FluidX3D.exe" "%CITYLBM_DATA%\FluidX3D.exe"

echo [4/4] Done!
echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo   Plugin: %GH_LIB%\CityLBM.gha
echo   Deps:   %GH_LIB%\Newtonsoft.Json.dll
echo   Deps:   %GH_LIB%\NLog.dll
echo   Icons:  %GH_LIB%\Icons\ (22 icons, 24x24px)
echo   Solver: %CITYLBM_DATA%\FluidX3D.exe
echo.
echo   Next steps:
echo   1. Restart Rhino
echo   2. Type 'Grasshopper' in Rhino command line
echo   3. Find 'CityLBM' tab with 20 components
echo.
pause
