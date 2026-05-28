@echo off
REM =============================================================================
REM CityLBM v0.2.1 ? AIJ Case A Validation .gh Generator
REM =============================================================================
REM This script runs Rhino 7 in background to generate a complete
REM AIJ Case A validation Grasshopper definition with all components pre-wired.
REM
REM Output: AIJ_CaseA_OneClick.gh (same folder as this batch file)
REM =============================================================================

echo ============================================
echo CityLBM v0.2.1 ? AIJ Case A .gh Generator
echo ============================================
echo.

set RHINO="C:\Program Files\Rhino 7\System\Rhino.exe"
set SCRIPT="%~dp0create_aij_gh.py"

if not exist %RHINO% (
    echo ERROR: Rhino 7 not found at %RHINO%
    echo Please install Rhino 7 first.
    pause
    exit /b 1
)

if not exist %SCRIPT% (
    echo ERROR: Generator script not found: %SCRIPT%
    pause
    exit /b 1
)

echo [1/3] Closing any running Rhino instances...
taskkill /f /im Rhino.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Launching Rhino with AIJ Case A generator...
echo        Rhino will open, create the .gh file, then close.
echo        This takes ~10-15 seconds...
echo.

%RHINO% /nosplash /runscript="_-RunPythonScript (Load %SCRIPT%)" /runscript="-_Exit"

timeout /t 3 /nobreak >nul

echo [3/3] Checking output...
if exist "%~dp0AIJ_CaseA_OneClick.gh" (
    echo.
    echo ============================================
    echo   SUCCESS! .gh file created:
    echo   %~dp0AIJ_CaseA_OneClick.gh
    echo ============================================
    echo.
    echo NEXT: Open this .gh file in Grasshopper,
    echo        all components are pre-wired.
    echo        Hit Run to start simulation.
) else (
    echo.
    echo WARNING: .gh file not found.
    echo Try running manually in Rhino:
    echo   _-RunPythonScript (Load "%SCRIPT%")
)

pause