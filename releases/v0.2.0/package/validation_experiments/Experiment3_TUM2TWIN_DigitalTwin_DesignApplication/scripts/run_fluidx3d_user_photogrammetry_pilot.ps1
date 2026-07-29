$ErrorActionPreference = "Stop"

$caseRoot = "F:\citylbm_fluidx3d_workspace\tum2twin_case"
$fluidRoot = "F:\citylbm_fluidx3d_workspace\FluidX3D"
$exe = Join-Path $fluidRoot "bin\FluidX3D.exe"
$stlDir = Join-Path $fluidRoot "stl"
$logDir = Join-Path $caseRoot "logs"
$outDir = Join-Path $caseRoot "output"

New-Item -ItemType Directory -Force -Path $stlDir, $logDir, $outDir | Out-Null

$srcStl = "D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl"
$dstName = "TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl"
$dstStl = Join-Path $stlDir $dstName
if (-not (Test-Path $dstStl)) {
    Copy-Item -LiteralPath $srcStl -Destination $dstStl
}

$env:Path = "F:\citylbm_fluidx3d_workspace\WinLibs\mingw64\bin;" +
    [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "Machine")

$label = "user_photo_wd000_dx2m_2k"
$env:TUM2TWIN_STL = $dstName
$env:TUM2TWIN_NX = "360"
$env:TUM2TWIN_NY = "430"
$env:TUM2TWIN_NZ = "80"
$env:TUM2TWIN_DX = "2.0"
$env:TUM2TWIN_RUN_STEPS = "2000"
$env:TUM2TWIN_WIND_DEG = "0"
$env:TUM2TWIN_RUN_LABEL = $label

$log = Join-Path $logDir ("run_{0}.log" -f $label)
$finalU = Join-Path $outDir ("matrix_{0}_u_finalu-000002000.vtk" -f $label)
$finalFlags = Join-Path $outDir ("matrix_{0}_flags_finalflags-000002000.vtk" -f $label)

if ((Test-Path $finalU) -and (Test-Path $finalFlags)) {
    Write-Host ("{0}: skipped_existing" -f $label)
} else {
    $start = Get-Date
    Push-Location $fluidRoot
    try {
        & $exe *> $log
        $exit = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    $end = Get-Date
    $elapsed = [math]::Round(($end - $start).TotalSeconds, 2)
    $status = if ($exit -eq 0 -and (Test-Path $finalU) -and (Test-Path $finalFlags)) { "ok" } else { "failed" }
    Write-Host ("{0}: {1}, {2}s" -f $label, $status, $elapsed)
    if ($status -ne "ok") {
        throw "FluidX3D user photogrammetry pilot failed. See $log"
    }
}

[pscustomobject]@{
    label = $label
    status = "completed_or_existing"
    stl = $dstStl
    grid = "360x430x80"
    dx_m = 2.0
    steps = 2000
    log = $log
    final_u = $finalU
    final_flags = $finalFlags
} | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $caseRoot "figures\fluidx3d_user_photogrammetry_pilot_summary.csv")
