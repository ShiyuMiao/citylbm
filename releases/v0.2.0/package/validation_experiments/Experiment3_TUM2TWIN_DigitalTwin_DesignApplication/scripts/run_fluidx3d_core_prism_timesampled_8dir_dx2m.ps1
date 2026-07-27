$ErrorActionPreference = "Stop"

$caseRoot = "F:\citylbm_fluidx3d_workspace\tum2twin_case"
$fluidRoot = "F:\citylbm_fluidx3d_workspace\FluidX3D"
$exe = Join-Path $fluidRoot "bin\FluidX3D.exe"
$stlDir = Join-Path $fluidRoot "stl"
$logDir = Join-Path $caseRoot "logs"
$outDir = Join-Path $caseRoot "output"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

New-Item -ItemType Directory -Force -Path $stlDir, $logDir, $outDir | Out-Null

$srcStl = Join-Path $projectRoot "cfd_ready\core_photogrammetry_extent_prism_collision_z0.stl"
$dstName = "core_photogrammetry_extent_prism_collision_z0.stl"
$dstStl = Join-Path $stlDir $dstName
Copy-Item -LiteralPath $srcStl -Destination $dstStl -Force

$env:Path = "F:\citylbm_fluidx3d_workspace\WinLibs\mingw64\bin;" +
    [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "Machine")

$env:TUM2TWIN_STL = $dstName
$env:TUM2TWIN_NX = "320"
$env:TUM2TWIN_NY = "390"
$env:TUM2TWIN_NZ = "60"
$env:TUM2TWIN_DX = "2.0"
$env:TUM2TWIN_RUN_STEPS = "12000"
$env:TUM2TWIN_SAMPLE_SPINUP = "6000"
$env:TUM2TWIN_SAMPLE_INTERVAL = "2000"
$env:TUM2TWIN_SAMPLE_COUNT = "3"

$directions = @(0, 45, 90, 135, 180, 225, 270, 315)
$summary = @()

foreach ($deg in $directions) {
    $label = "core_prism_avg_wd{0:D3}_dx2m_spin6k_s3" -f $deg
    $log = Join-Path $logDir ("run_{0}.log" -f $label)
    $sample2 = Join-Path $outDir ("matrix_{0}_u_sample_2u-000012000.vtk" -f $label)
    $flags2 = Join-Path $outDir ("matrix_{0}_flags_sample_2flags-000012000.vtk" -f $label)

    if ((Test-Path $sample2) -and (Test-Path $flags2)) {
        $summary += [pscustomobject]@{
            label = $label
            wind_deg = $deg
            status = "skipped_existing"
            elapsed_s = 0
            log = $log
            final_sample_u = $sample2
            final_sample_flags = $flags2
        }
        Write-Host ("{0}: skipped_existing" -f $label)
        continue
    }

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
    $elapsed = [math]::Round(($end - $start).TotalSeconds, 2)
    $status = if ($exit -eq 0 -and (Test-Path $sample2) -and (Test-Path $flags2)) { "ok" } else { "failed" }
    $summary += [pscustomobject]@{
        label = $label
        wind_deg = $deg
        status = $status
        elapsed_s = $elapsed
        log = $log
        final_sample_u = $sample2
        final_sample_flags = $flags2
    }
    Write-Host ("{0}: {1}, {2}s" -f $label, $status, $elapsed)
    if ($status -ne "ok") {
        throw "FluidX3D time-sampled core prism run failed for $label. See $log"
    }
}

$summaryPath = Join-Path $caseRoot "figures\fluidx3d_core_prism_timesampled_8dir_dx2m_run_summary.csv"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $summaryPath) | Out-Null
$summary | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $summaryPath
Write-Host "summary=$summaryPath"
