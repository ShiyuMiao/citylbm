param(
  [string]$FluidX3DPath = "F:\citylbm_fluidx3d_workspace\FluidX3D",
  [string]$CasePath = "F:\citylbm_fluidx3d_workspace\tum2twin_case"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $FluidX3DPath)) {
  throw "FluidX3D path not found: $FluidX3DPath"
}
if (-not (Test-Path $CasePath)) {
  throw "Case path not found: $CasePath"
}

$srcSetup = Join-Path $FluidX3DPath "src\setup.cpp"
$overlaySetup = Join-Path $CasePath "setup_overlay\setup_tum2twin_wind_pilot.cpp"
$stlSrc = Join-Path $CasePath "stl"
$stlDest = Join-Path $FluidX3DPath "stl"
$backup = Join-Path $FluidX3DPath ("src\setup.cpp.backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

if (-not (Test-Path $srcSetup)) {
  throw "FluidX3D setup.cpp not found: $srcSetup"
}
if (-not (Test-Path $overlaySetup)) {
  throw "TUM2TWIN setup overlay not found: $overlaySetup"
}

Copy-Item -LiteralPath $srcSetup -Destination $backup -Force
Copy-Item -LiteralPath $overlaySetup -Destination $srcSetup -Force
New-Item -ItemType Directory -Force -Path $stlDest | Out-Null
Copy-Item -LiteralPath (Join-Path $stlSrc "*.stl") -Destination $stlDest -Force

[PSCustomObject]@{
  FluidX3DPath = $FluidX3DPath
  CasePath = $CasePath
  SetupBackup = $backup
  SetupApplied = $srcSetup
  StlDestination = $stlDest
}
