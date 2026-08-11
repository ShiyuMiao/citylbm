param(
    [switch]$Launch,
    [string]$InstallPath = "E:\citylbm_buildchain\VSBuildTools",
    [double]$MinSystemDriveFreeGB = 8.0,
    [string]$OutJson = "",
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-CommandStatus {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        return @{ found = $false; path = ""; version = "" }
    }
    $version = ""
    try {
        $version = (& $Name --version 2>&1 | Select-Object -First 1) -join "`n"
    } catch {
        $version = $_.Exception.Message
    }
    return @{ found = $true; path = $cmd.Source; version = $version }
}

function Get-FileStatus {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return @{ found = $false; path = $Path; sha256 = ""; size_bytes = $null }
    }
    $item = Get-Item -LiteralPath $Path
    $hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return @{ found = $true; path = $item.FullName; sha256 = $hash.Hash.ToLowerInvariant(); size_bytes = $item.Length }
}

$scriptDir = Split-Path -Parent $PSCommandPath
$recoveryScript = Join-Path $scriptDir "vs_cpp_buildtools_recovery.ps1"
$systemDrive = if ($env:SystemDrive) { "$env:SystemDrive\" } else { "C:\" }
$driveInfo = Get-PSDrive -Name $systemDrive.Substring(0, 1)
$systemFreeGB = [math]::Round($driveInfo.Free / 1GB, 3)
$winget = Get-CommandStatus "winget.exe"
$isAdmin = Test-IsAdmin
$recoveryStatus = Get-FileStatus $recoveryScript

$recoveryArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $recoveryScript,
    "-Install",
    "-InstallPath", $InstallPath,
    "-MinSystemDriveFreeGB", ([string]$MinSystemDriveFreeGB),
    "-NoPause"
)
$recoveryCommand = "powershell " + (($recoveryArgs | ForEach-Object { if ($_ -match "\s") { '"' + $_ + '"' } else { $_ } }) -join " ")

$blockers = New-Object System.Collections.Generic.List[string]
if (-not $recoveryStatus.found) { $blockers.Add("vs_cpp_buildtools_recovery.ps1 is missing") }
if (-not $winget.found) { $blockers.Add("winget.exe is not available") }
if ($systemFreeGB -lt $MinSystemDriveFreeGB) { $blockers.Add("system drive free space is below $MinSystemDriveFreeGB GB") }

$canLaunchElevatedInstallNow = [bool]($recoveryStatus.found -and $winget.found -and $systemFreeGB -ge $MinSystemDriveFreeGB)
$launchAttempted = $false
$launchResult = @{
    exit_code = $null
    message = ""
}

if ($Launch) {
    if (-not $canLaunchElevatedInstallNow) {
        $launchResult.exit_code = 20
        $launchResult.message = "Elevated install was requested but preflight blockers are present."
    } else {
        $launchAttempted = $true
        $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $recoveryArgs -Verb RunAs -PassThru
        $launchResult.exit_code = 0
        $launchResult.message = "Elevated VS Build Tools recovery process launched; approve UAC and rerun vs_cpp_recovery_gate.py after it exits."
        $launchResult.process_id = $proc.Id
    }
}

$payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    evidence_type = "newly_run"
    launch_requested = [bool]$Launch
    launch_attempted = [bool]$launchAttempted
    current_user_is_admin = [bool]$isAdmin
    system_drive_free_gb = $systemFreeGB
    min_system_drive_free_gb = $MinSystemDriveFreeGB
    install_path = $InstallPath
    recovery_script = $recoveryStatus
    winget = $winget
    can_launch_elevated_install_now = $canLaunchElevatedInstallNow
    recovery_command = $recoveryCommand
    blockers = @($blockers)
    launch_result = $launchResult
    post_install_verification = "python docs/experiments/casee/tools/vs_cpp_recovery_gate.py"
    boundary = "Default mode is audit-only. Use -Launch only to open a UAC-elevated VS Build Tools recovery process; this does not run CFD, recover GPU runtime, improve Case E metrics, or support formal v0.4.0."
}

$json = $payload | ConvertTo-Json -Depth 8
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
