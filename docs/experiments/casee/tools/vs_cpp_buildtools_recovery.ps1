param(
    [switch]$Install,
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
        $version = (& $Name 2>&1 | Select-Object -First 1) -join "`n"
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

function Get-VswhereVcPath {
    $vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path -LiteralPath $vswhere)) {
        return @{ found = $false; vswhere = (Get-FileStatus $vswhere); installation_path = "" }
    }
    $path = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null
    return @{ found = -not [string]::IsNullOrWhiteSpace($path); vswhere = (Get-FileStatus $vswhere); installation_path = ($path -join "").Trim() }
}

$systemDrive = if ($env:SystemDrive) { "$env:SystemDrive\" } else { "C:\" }
$driveInfo = Get-PSDrive -Name $systemDrive.Substring(0, 1)
$systemFreeGB = [math]::Round($driveInfo.Free / 1GB, 3)
$isAdmin = Test-IsAdmin
$vs = Get-VswhereVcPath
$vcvarsCandidates = @(
    (Join-Path $InstallPath "VC\Auxiliary\Build\vcvars64.bat"),
    "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)
$vcvarsStatus = @($vcvarsCandidates | ForEach-Object { Get-FileStatus $_ })
$winget = Get-CommandStatus "winget.exe"
$cl = Get-CommandStatus "cl.exe"
$msbuild = Get-CommandStatus "msbuild.exe"

$override = "--wait --quiet --norestart --installPath $InstallPath --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --add Microsoft.VisualStudio.Component.VC.CMake.Project --add Microsoft.VisualStudio.Component.Windows11SDK.26100"
$wingetArgs = @(
    "install",
    "--id", "Microsoft.VisualStudio.2022.BuildTools",
    "--source", "winget",
    "--accept-package-agreements",
    "--accept-source-agreements",
    "--silent",
    "--location", $InstallPath,
    "--override", $override
)
$commandLine = "winget " + (($wingetArgs | ForEach-Object { if ($_ -match "\s") { '"' + $_ + '"' } else { $_ } }) -join " ")

$blockers = New-Object System.Collections.Generic.List[string]
if (-not $vs.found) { $blockers.Add("vswhere does not find Microsoft.VisualStudio.Component.VC.Tools.x86.x64") }
if (-not $winget.found) { $blockers.Add("winget.exe is not available") }
if (-not $isAdmin) { $blockers.Add("current shell is not elevated; VS Build Tools install requires UAC approval") }
if ($systemFreeGB -lt $MinSystemDriveFreeGB) { $blockers.Add("system drive free space is below $MinSystemDriveFreeGB GB") }
if (-not $cl.found) { $blockers.Add("cl.exe is not on PATH") }
if (-not $msbuild.found) { $blockers.Add("msbuild.exe is not on PATH") }

$installExitCode = $null
$installStdout = ""
$installStderr = ""
if ($Install) {
    if (-not $winget.found) {
        $installExitCode = 127
        $installStderr = "winget.exe is not available"
    } elseif (-not $isAdmin) {
        $installExitCode = 10
        $installStderr = "Not elevated. Re-run PowerShell as Administrator or approve UAC."
    } elseif ($systemFreeGB -lt $MinSystemDriveFreeGB) {
        $installExitCode = 11
        $installStderr = "System drive free space is below $MinSystemDriveFreeGB GB."
    } else {
        $proc = Start-Process -FilePath $winget.path -ArgumentList $wingetArgs -Wait -PassThru -NoNewWindow
        $installExitCode = $proc.ExitCode
    }
}

$payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    evidence_type = "newly_run"
    install_requested = [bool]$Install
    install_attempted = [bool]($Install -and $winget.found -and $isAdmin -and $systemFreeGB -ge $MinSystemDriveFreeGB)
    vs_cpp_ready = [bool]$vs.found
    current_user_is_admin = [bool]$isAdmin
    system_drive_free_gb = $systemFreeGB
    min_system_drive_free_gb = $MinSystemDriveFreeGB
    install_path = $InstallPath
    recommended_command = $commandLine
    vswhere_vc = $vs
    vcvars64_candidates = $vcvarsStatus
    winget = $winget
    cl = $cl
    msbuild = $msbuild
    blockers = @($blockers)
    install_result = @{
        exit_code = $installExitCode
        stdout = $installStdout
        stderr = $installStderr
    }
    boundary = "Default mode is audit-only. The script installs Visual Studio Build Tools only when -Install is explicitly supplied; readiness is build-chain evidence only, not CFD accuracy evidence."
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
