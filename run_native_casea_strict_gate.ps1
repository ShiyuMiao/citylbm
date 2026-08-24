param(
    [Parameter(Mandatory = $true)]
    [string]$CaseDir,

    [Parameter(Mandatory = $true)]
    [string]$FluidX3DSource,

    [string]$OutDir = "",
    [string]$VtkOutputDir = "",
    [string]$BaselineId = "",
    [string]$ExpectedWindDirection = "N",
    [int]$TimeSteps = 60000,
    [int]$VtkSaveInterval = 1000,
    [int]$VtkSaveStartStep = 10000,
    [int]$ExpectedVtkFrameCount = 51,
    [int]$AverageLastN = 40,
    [int]$MinVtkFrames = 40,
    [int]$MinVtkStepSpan = 20000,
    [int]$MinStgRefreshes = 200,
    [string]$MSBuild = "",
    [string]$Exe = "",
    [int]$TimeoutSeconds = 0,
    [switch]$Install,
    [switch]$Build,
    [switch]$Run,
    [switch]$AllowDiagnosticExecution
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repo "scripts\run_native_fluidx3d_case.py"
if (-not (Test-Path -LiteralPath $runner)) {
    throw "Native runner not found: $runner"
}

$resolvedCaseDir = (Resolve-Path -LiteralPath $CaseDir).Path
$resolvedFluidX3DSource = (Resolve-Path -LiteralPath $FluidX3DSource).Path

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $resolvedCaseDir "native_baseline"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$manifest = Join-Path $OutDir "native_fluidx3d_baseline_manifest.json"

if ([string]::IsNullOrWhiteSpace($BaselineId)) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BaselineId = "native-fluidx3d-casea-$ExpectedWindDirection-$stamp"
}

$python = $env:PYTHON
if ([string]::IsNullOrWhiteSpace($python)) {
    $python = "python"
}

$args = @(
    $runner,
    "--case-dir", $resolvedCaseDir,
    "--fluidx3d-source", $resolvedFluidX3DSource,
    "--out", $manifest,
    "--baseline-id", $BaselineId,
    "--expected-aij-case", "CaseA",
    "--expected-wind-direction", $ExpectedWindDirection,
    "--time-steps", $TimeSteps,
    "--vtk-save-interval", $VtkSaveInterval,
    "--vtk-save-start-step", $VtkSaveStartStep,
    "--expected-vtk-frame-count", $ExpectedVtkFrameCount,
    "--average-last-n", $AverageLastN,
    "--min-vtk-frames", $MinVtkFrames,
    "--min-vtk-step-span", $MinVtkStepSpan,
    "--min-stg-refreshes", $MinStgRefreshes
)

if (-not [string]::IsNullOrWhiteSpace($MSBuild)) {
    $args += @("--msbuild", $MSBuild)
}
if (-not [string]::IsNullOrWhiteSpace($Exe)) {
    $args += @("--exe", $Exe)
}
if ($TimeoutSeconds -gt 0) {
    $args += @("--timeout-seconds", $TimeoutSeconds)
}
if ($Install) {
    $args += "--install"
}
if ($Build) {
    $args += "--build"
}
if ($Run) {
    $args += "--run"
}
if (-not [string]::IsNullOrWhiteSpace($VtkOutputDir)) {
    $resolvedVtkOutputDir = (Resolve-Path -LiteralPath $VtkOutputDir).Path
    $args += @("--output-dir", $resolvedVtkOutputDir)
}
if ($AllowDiagnosticExecution) {
    $args += "--allow-diagnostic-execution"
}

Write-Host "CityLBM native Case A strict gate"
Write-Host "CaseDir: $resolvedCaseDir"
Write-Host "FluidX3DSource: $resolvedFluidX3DSource"
Write-Host "Manifest: $manifest"
Write-Host "Execution switches: Install=$Install Build=$Build Run=$Run"

& $python @args
exit $LASTEXITCODE
