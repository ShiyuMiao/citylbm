param(
    [string]$DotNetPath = "E:\citylbm_buildchain\dotnet\dotnet.exe",
    [string]$FluidX3DExe = "E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe",
    [string]$MingwBin = "F:\citylbm_fluidx3d_workspace\WinLibs\mingw64\bin",
    [string]$OutJson = "",
    [switch]$PersistUserPath,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

function Get-FileStatus {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return @{ found = $false; path = $Path; sha256 = ""; size_bytes = $null }
    }
    $item = Get-Item -LiteralPath $Path
    $hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return @{ found = $true; path = $item.FullName; sha256 = $hash.Hash.ToLowerInvariant(); size_bytes = $item.Length }
}

function Invoke-Captured {
    param([string]$FilePath, [string[]]$Arguments = @())
    if ([string]::IsNullOrWhiteSpace($FilePath)) {
        return @{ command = ""; found = $false; returncode = $null; stdout = ""; stderr = "empty command" }
    }
    $cmd = $FilePath
    if (-not (Test-Path -LiteralPath $FilePath)) {
        $resolved = Get-Command $FilePath -ErrorAction SilentlyContinue
        if ($null -eq $resolved) {
            return @{ command = (($FilePath, $Arguments) -join " "); found = $false; returncode = $null; stdout = ""; stderr = "not found" }
        }
        $cmd = $resolved.Source
    }
    $output = ""
    $code = $null
    try {
        $output = (& $cmd @Arguments 2>&1) -join "`n"
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
    } catch {
        $output = $_.Exception.Message
        $code = 1
    }
    return @{ command = (($cmd, $Arguments) -join " "); found = $true; returncode = $code; stdout = $output; stderr = "" }
}

function Add-ProcessPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return $false
    }
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $parts = @($env:PATH -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($parts -notcontains $resolved) {
        $env:PATH = $resolved + ";" + $env:PATH
    }
    return $true
}

$fluidx3dBin = ""
if (Test-Path -LiteralPath $FluidX3DExe) {
    $fluidx3dBin = Split-Path -Parent (Resolve-Path -LiteralPath $FluidX3DExe).Path
}
$dotnetDir = ""
if (Test-Path -LiteralPath $DotNetPath) {
    $dotnetDir = Split-Path -Parent (Resolve-Path -LiteralPath $DotNetPath).Path
    $env:CITYLBM_DOTNET = (Resolve-Path -LiteralPath $DotNetPath).Path
}
if (Test-Path -LiteralPath $FluidX3DExe) {
    $env:CITYLBM_FLUIDX3D_EXE = (Resolve-Path -LiteralPath $FluidX3DExe).Path
}

$added = @()
if (Add-ProcessPath $dotnetDir) { $added += $dotnetDir }
if (Add-ProcessPath $fluidx3dBin) { $added += $fluidx3dBin }
if (Add-ProcessPath $MingwBin) { $added += (Resolve-Path -LiteralPath $MingwBin).Path }

$dotnetStatus = Get-FileStatus $DotNetPath
$fluidxStatus = Get-FileStatus $FluidX3DExe
$gppPath = Join-Path $MingwBin "g++.exe"
$gppStatus = Get-FileStatus $gppPath
$clStatus = Invoke-Captured "cl.exe"
$msbuildStatus = Invoke-Captured "msbuild.exe"
$nvidiaStatus = Invoke-Captured "nvidia-smi"

$dotnetInfo = if ($dotnetStatus.found) { Invoke-Captured $DotNetPath @("--info") } else { Invoke-Captured "dotnet" @("--info") }
$gppVersion = if ($gppStatus.found) { Invoke-Captured $gppPath @("--version") } else { Invoke-Captured "g++.exe" @("--version") }

$dotnetReady = [bool]($dotnetStatus.found -and $dotnetInfo.returncode -eq 0)
$fluidxReady = [bool]$fluidxStatus.found
$gppReady = [bool]($gppStatus.found -and $gppVersion.returncode -eq 0)
$vsCppReady = [bool]($clStatus.found -and $msbuildStatus.found)
$gpuReady = [bool]($nvidiaStatus.returncode -eq 0 -and $nvidiaStatus.stdout -notmatch "GPU is lost")
$portableReady = [bool]($dotnetReady -and $fluidxReady -and $gppReady)

if ($PersistUserPath) {
    $currentUserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    $userParts = @($currentUserPath -split ";" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    foreach ($p in $added) {
        if ($userParts -notcontains $p) { $userParts += $p }
    }
    [Environment]::SetEnvironmentVariable("PATH", ($userParts -join ";"), "User")
}

$payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    evidence_type = "newly_run"
    install_attempted = $false
    persist_user_path_requested = [bool]$PersistUserPath
    portable_toolchain_ready = $portableReady
    process_path_entries_added = $added
    dotnet = @{
        ready = $dotnetReady
        executable = $dotnetStatus
        info = $dotnetInfo
        env_CITYLBM_DOTNET = $env:CITYLBM_DOTNET
    }
    fluidx3d = @{
        ready_for_existing_binary = $fluidxReady
        executable = $fluidxStatus
        env_CITYLBM_FLUIDX3D_EXE = $env:CITYLBM_FLUIDX3D_EXE
        bin_added_to_process_path = $added -contains $fluidx3dBin
    }
    mingw_gpp = @{
        ready = $gppReady
        executable = $gppStatus
        version = $gppVersion
        bin_added_to_process_path = $added -contains $MingwBin
    }
    visual_studio_cpp = @{
        ready = $vsCppReady
        cl = $clStatus
        msbuild = $msbuildStatus
    }
    gpu_runtime = @{
        ready = $gpuReady
        nvidia_smi = $nvidiaStatus
    }
    claim_readiness = if ($portableReady) { "portable_toolchain_ready_with_vs_gpu_boundaries" } else { "portable_toolchain_blocked" }
    formal_accuracy_claim_supported = $false
    boundary = "This script activates and audits portable local tool paths only. It does not install Visual Studio Build Tools, recover the GPU, run FluidX3D, improve Case E metrics, or support formal v0.4.0."
}

$json = $payload | ConvertTo-Json -Depth 10
if (-not [string]::IsNullOrWhiteSpace($OutJson)) {
    $outDir = Split-Path -Parent $OutJson
    if (-not [string]::IsNullOrWhiteSpace($outDir)) {
        New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    }
    $json | Set-Content -LiteralPath $OutJson -Encoding UTF8
}
$json

if (-not $NoPause -and -not $env:CI) {
    Read-Host "Press Enter to exit"
}

exit 0
