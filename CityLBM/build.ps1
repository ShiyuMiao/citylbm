param(
    [string]$DotNetPath = "",
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CityLBM build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

function Resolve-CityLBMDotNet {
    param([string]$RequestedPath)

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        $candidates += $RequestedPath
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CITYLBM_DOTNET)) {
        $candidates += $env:CITYLBM_DOTNET
    }
    $candidates += "E:\citylbm_buildchain\dotnet\dotnet.exe"
    $candidates += "dotnet"

    foreach ($candidate in $candidates) {
        if ($candidate -eq "dotnet") {
            $cmd = Get-Command dotnet -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
            continue
        }
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "No .NET SDK found. Set -DotNetPath or CITYLBM_DOTNET, or install .NET SDK."
}

try {
    $dotnet = Resolve-CityLBMDotNet -RequestedPath $DotNetPath
    Write-Host "Using .NET SDK: $dotnet" -ForegroundColor Cyan
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Restoring NuGet packages..." -ForegroundColor Yellow
& $dotnet restore
if ($LASTEXITCODE -ne 0) {
    Write-Host "Restore failed." -ForegroundColor Red
    exit 1
}
Write-Host "Restore completed." -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Building Release..." -ForegroundColor Yellow
& $dotnet build -c Release --no-restore 2>&1 | ForEach-Object {
    if ($_ -match "error") {
        Write-Host $_ -ForegroundColor Red
    } elseif ($_ -match "warning") {
        Write-Host $_ -ForegroundColor Yellow
    } elseif ($_ -match "succeeded|Build succeeded") {
        Write-Host $_ -ForegroundColor Green
    } else {
        Write-Host $_
    }
}
$buildExitCode = $LASTEXITCODE

if ($buildExitCode -ne 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Build failed." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    if (-not $NoPause) {
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    exit $buildExitCode
}

Write-Host ""
Write-Host "Build completed." -ForegroundColor Green
Write-Host ""

$ghaSourcePath = "bin\Release\CityLBM.gha"
if (-not (Test-Path -LiteralPath $ghaSourcePath)) {
    Write-Host "Missing merged GHA: $ghaSourcePath" -ForegroundColor Red
    exit 1
}

$fileInfo = Get-Item -LiteralPath $ghaSourcePath
Write-Host "[3/3] Packaging Grasshopper output..." -ForegroundColor Yellow
Write-Host "Output GHA: $ghaSourcePath" -ForegroundColor Cyan
Write-Host "Size KB: $([math]::Round($fileInfo.Length / 1KB, 2))" -ForegroundColor Cyan
Write-Host "Updated: $($fileInfo.LastWriteTime)" -ForegroundColor Cyan

$trackedGhaPath = "bin\CityLBM.gha"
Copy-Item -LiteralPath $ghaSourcePath -Destination $trackedGhaPath -Force
Write-Host "Updated distributable: $trackedGhaPath" -ForegroundColor Green

$ghaDir = "bin\Release\CityLBM"
if (-not (Test-Path -LiteralPath $ghaDir)) {
    New-Item -ItemType Directory -Path $ghaDir -Force | Out-Null
}

Copy-Item -LiteralPath $ghaSourcePath -Destination "$ghaDir\CityLBM.gha" -Force
Write-Host "Created: $ghaDir\CityLBM.gha" -ForegroundColor Green

Get-ChildItem "bin\Release\*.dll" | Where-Object { $_.Name -ne "CityLBM.dll" } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $ghaDir -Force
    Write-Host "Copied dependency: $($_.Name)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "CityLBM build succeeded." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Install: copy bin\CityLBM.gha to the Grasshopper Libraries folder, then restart Grasshopper." -ForegroundColor Yellow

if (-not $NoPause) {
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
