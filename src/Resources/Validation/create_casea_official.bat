@echo off
REM =============================================================================
REM CityLBM v0.2.1 ? AIJ Case A Official Validation .gh Generator
REM =============================================================================
REM Uses NATIVE GH Box component + CityLBM pipeline
REM AIJ official data: b=0.08m, H=0.16m, B=D=0.08m
REM =============================================================================
echo ============================================
echo CityLBM v0.2.1 ? AIJ Case A Official .gh
echo ============================================
echo.
echo Building: H=0.16m, B=0.08m, D=0.08m (AIJ b=0.08)
echo Inflow:   U_H=4.5 m/s, power-law alpha=0.25
echo.
set RHINO="C:\Program Files\Rhino 7\System\Rhino.exe"
set SCRIPT="%~dp0create_aij_official_gh.py"
if not exist %RHINO% (
    echo ERROR: Rhino 7 not found
    pause & exit /b 1
)
if not exist %SCRIPT% (
    echo ERROR: Script not found: %SCRIPT%
    pause & exit /b 1
)
echo [1/3] Closing Rhino...
taskkill /f /im Rhino.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [2/3] Generating .gh file...
%RHINO% /nosplash /runscript="_-RunPythonScript (Load %SCRIPT%)" /runscript="-_Exit"
timeout /t 3 /nobreak >nul
echo [3/3] Done!
if exist "%~dp0AIJ_CaseA_Official.gh" (
    echo   Created: %~dp0AIJ_CaseA_Official.gh
    echo   Open in Grasshopper, set component params, Run!
) else (
    echo   WARNING: .gh file not created. Check Rhino console.
)
pause