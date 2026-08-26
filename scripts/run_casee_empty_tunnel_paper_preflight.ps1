param(
    [string]$CaseDir = "",
    [string]$OutDir = "",
    [string]$SolverCwd = "",
    [string]$FluidX3DSource = "",
    [string]$OfficialConditionFilter = "ac",
    [string]$OfficialWindFilter = "N",
    [string]$PythonExe = "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe",
    [switch]$SkipPreflight,
    [switch]$AllowLongRun
)

$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$workspace = Split-Path $repo -Parent

if ([string]::IsNullOrWhiteSpace($CaseDir)) {
    $CaseDir = Join-Path $env:LOCALAPPDATA "Temp\CityLBM\stg_full_reynolds_stress_tensor"
}

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutDir = Join-Path $env:LOCALAPPDATA "Temp\citylbm_casee_empty_tunnel_paper_$stamp"
}

if ([string]::IsNullOrWhiteSpace($SolverCwd)) {
    $SolverCwd = Join-Path $env:LOCALAPPDATA ("Temp\" + (Split-Path $OutDir -Leaf) + "_solver")
}

if ([string]::IsNullOrWhiteSpace($FluidX3DSource)) {
    $FluidX3DSource = Join-Path $workspace "citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master"
}

$official = Join-Path $repo "releases\v0.2.0\package\examples\AIJ_CaseE\official_data\RS_caseE.csv"
$afCsv = Join-Path $repo "releases\v0.2.0\package\examples\AIJ_CaseE\official_data\AF_caseE.csv"
$manifest = Join-Path $OutDir "empty_tunnel_manifest.json"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python not found: $PythonExe"
}
if (-not (Test-Path -LiteralPath $CaseDir)) {
    throw "CityLBM generated case directory not found: $CaseDir"
}
if (-not (Test-Path -LiteralPath $official)) {
    throw "Official RS_caseE.csv not found: $official"
}
if (-not (Test-Path -LiteralPath $afCsv)) {
    throw "Official AF_caseE.csv not found: $afCsv"
}

$drive = Get-PSDrive -Name C
if ($drive.Free -lt 20GB) {
    Write-Warning ("C drive free space is below 20 GB: {0:N2} GB" -f ($drive.Free / 1GB))
}

$prepareArgs = @(
    (Join-Path $repo "scripts\prepare_native_empty_tunnel_case.py"),
    "--case-dir", $CaseDir,
    "--out-dir", $OutDir,
    "--fluidx3d-source", $FluidX3DSource,
    "--solver-cwd", $SolverCwd,
    "--manifest-out", $manifest,
    "--baseline-id", "casee-empty-tunnel-paper-inlet",
    "--expected-aij-case", "CaseE",
    "--expected-wind-direction", "N",
    "--expected-wind-vector", "0,-1,0",
    "--official", $official,
    "--official-condition-filter", $OfficialConditionFilter,
    "--official-wind-filter", $OfficialWindFilter,
    "--af-csv", $afCsv,
    "--expected-probe-row-count", "80",
    "--expected-probe-z", "2.0",
    "--z-ref", "15.9",
    "--expected-uref", "3.928296",
    "--time-steps", "60000",
    "--vtk-save-interval", "1000",
    "--vtk-save-start-step", "10000",
    "--expected-vtk-frame-count", "51",
    "--average-last-n", "40",
    "--min-vtk-frames", "40",
    "--min-vtk-step-span", "20000",
    "--require-af-k"
)

Write-Host "Preparing Case E empty-tunnel inlet-preservation package..."
& $PythonExe @prepareArgs

if (-not $SkipPreflight) {
    Write-Host "Running no-CFD preflight..."
    & $PythonExe (Join-Path $repo "scripts\run_native_empty_tunnel_workflow.py") `
        --manifest $manifest `
        --stage preflight `
        --execute
}

if ($AllowLongRun) {
    Write-Host "Starting long native FluidX3D run..."
    & $PythonExe (Join-Path $repo "scripts\run_native_empty_tunnel_workflow.py") `
        --manifest $manifest `
        --stage run `
        --execute `
        --allow-long-run
}

Write-Host "empty_tunnel_manifest=$manifest"
