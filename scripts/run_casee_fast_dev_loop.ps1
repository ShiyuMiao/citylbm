param(
    [string]$FluidX3DSource = "",
    [string]$PythonExe = "",
    [string]$OutDir = "",
    [int]$TimeSteps = 2000,
[int]$VtkSaveInterval = 100,
[int]$VtkSaveStartStep = 100,
[int]$ExpectedVtkFrameCount = 20,
[int]$AverageLastN = 10,
[int]$MinVtkFrames = 10,
[int]$MinVtkStepSpan = 900,
    [switch]$NoSolver,
    [switch]$ReuseTempCase,
    [switch]$SkipCodegenSmoke
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$workspace = Split-Path $repo -Parent
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

if ([string]::IsNullOrWhiteSpace($FluidX3DSource)) {
    $FluidX3DSource = Join-Path $workspace "citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master"
}

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $env:TEMP ("citylbm_casee_fast_dev_loop_" + $stamp)
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $pythonCandidates = @(
        "C:\Program Files\ladybug_tools\python\python.exe",
        "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe",
        "python"
    )
    foreach ($candidate in $pythonCandidates) {
        if ($candidate -eq "python") {
            $resolved = Get-Command python -ErrorAction SilentlyContinue
            if ($null -ne $resolved) {
                $PythonExe = $resolved.Source
                break
            }
        } elseif (Test-Path -LiteralPath $candidate) {
            $PythonExe = $candidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    throw "No usable Python executable found. Pass -PythonExe explicitly."
}

$fDrive = Get-PSDrive -Name F -ErrorAction SilentlyContinue
if ($null -ne $fDrive -and $fDrive.Free -lt 536870912) {
    Write-Warning ("F: free space is low ({0} bytes). Fast outputs will be written to {1}." -f $fDrive.Free, $OutDir)
}

$env:PYTHONDONTWRITEBYTECODE = "1"

if (-not $SkipCodegenSmoke) {
    dotnet run --project (Join-Path $repo "tests\CodegenSmoke\CodegenSmoke.csproj") -c Release
}

$argsList = @(
    (Join-Path $repo "scripts\run_validation_dev_loop.py"),
    "--case", "casee",
    "--fluidx3d-source", $FluidX3DSource,
    "--out-dir", $OutDir,
    "--time-steps", "$TimeSteps",
    "--vtk-save-interval", "$VtkSaveInterval",
    "--vtk-save-start-step", "$VtkSaveStartStep",
    "--expected-vtk-frame-count", "$ExpectedVtkFrameCount",
    "--average-last-n", "$AverageLastN",
    "--min-vtk-frames", "$MinVtkFrames",
    "--min-vtk-step-span", "$MinVtkStepSpan",
    "--allow-diagnostic"
)

if ($ReuseTempCase) {
    $argsList += "--quick"
}

if (-not $NoSolver) {
    $argsList += "--execute-canary"
}

& $PythonExe @argsList

Write-Host ""
Write-Host ("Manifest: " + (Join-Path $OutDir "validation_dev_loop_manifest.json"))
Write-Host ("VTK output: " + (Join-Path $OutDir "diagnostic_solver_cwd\output"))
