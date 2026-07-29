$ErrorActionPreference = "Stop"

$caseRoot = "F:\citylbm_fluidx3d_workspace\tum2twin_case"
$fluidRoot = "F:\citylbm_fluidx3d_workspace\FluidX3D"
$exe = Join-Path $fluidRoot "bin\FluidX3D.exe"
$logDir = Join-Path $caseRoot "logs"
$outDir = Join-Path $caseRoot "output"

New-Item -ItemType Directory -Force -Path $logDir, $outDir | Out-Null

$env:Path = "F:\citylbm_fluidx3d_workspace\WinLibs\mingw64\bin;" +
    [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "Machine")

$env:TUM2TWIN_STL = "building_collision_full_lod2_z0.stl"
$env:TUM2TWIN_NX = "306"
$env:TUM2TWIN_NY = "306"
$env:TUM2TWIN_NZ = "64"
$env:TUM2TWIN_DX = "4.0"
$env:TUM2TWIN_RUN_STEPS = "10000"

$directions = @(0, 45, 90, 135, 180, 225, 270, 315)
$summary = @()

foreach ($deg in $directions) {
    $label = "full_lod2_wd{0:D3}_coarse4m_10k" -f $deg
    $log = Join-Path $logDir ("run_{0}.log" -f $label)
    $env:TUM2TWIN_WIND_DEG = [string]$deg
    $env:TUM2TWIN_RUN_LABEL = $label
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
    $finalU = Join-Path $outDir ("matrix_{0}_u_finalu-000010000.vtk" -f $label)
    $finalFlags = Join-Path $outDir ("matrix_{0}_flags_finalflags-000010000.vtk" -f $label)
    $status = if ($exit -eq 0 -and (Test-Path $finalU) -and (Test-Path $finalFlags)) { "ok" } else { "failed" }
    $row = [pscustomobject]@{
        label = $label
        wind_deg = $deg
        exit_code = $exit
        status = $status
        elapsed_s = [math]::Round(($end - $start).TotalSeconds, 2)
        log = $log
        final_u = $finalU
        final_flags = $finalFlags
    }
    $summary += $row
    Write-Host ("{0}: {1}, {2}s" -f $label, $status, $row.elapsed_s)
    if ($status -ne "ok") {
        throw "FluidX3D run failed for $label. See $log"
    }
}

$summaryPath = Join-Path $caseRoot "figures\fluidx3d_full_lod2_8dir_coarse4m_10k_run_summary.csv"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $summaryPath) | Out-Null
$summary | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $summaryPath
Write-Host "summary=$summaryPath"
