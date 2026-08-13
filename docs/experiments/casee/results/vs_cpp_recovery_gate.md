# VS C++ Build Tools Recovery Gate

Generated: 2026-08-13T04:51:51.257039+00:00

## Verdict

- Gate passed: True
- Claim readiness: `blocked_vs_cpp_recovery_ready_for_manual_install`
- VS C++ ready: False
- Can attempt install now: False
- Formal accuracy claim supported: False

## Current Machine Probe

- PowerShell return code: 0
- Current user is admin: False
- System drive free GB: 1.51
- Minimum system drive free GB: 8
- Install path: `E:\citylbm_buildchain\VSBuildTools`

## Checks

| check | passed |
|---|---:|
| `powershell_probe_ran` | True |
| `recovery_script_ready` | True |
| `default_mode_audit_only` | True |
| `admin_and_space_guards_present` | True |
| `vs_components_specified` | True |
| `claim_boundary_safe` | True |

## Blockers

- vswhere does not find Microsoft.VisualStudio.Component.VC.Tools.x86.x64
- current shell is not elevated; VS Build Tools install requires UAC approval
- system drive free space is below 8 GB
- cl.exe is not on PATH
- msbuild.exe is not on PATH

## Manual Recovery Command

Run only from an elevated PowerShell after resolving the listed blockers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File docs/experiments/casee/tools/vs_cpp_buildtools_recovery.ps1 -Install -NoPause
```

The underlying winget command recorded by the probe is:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget --accept-package-agreements --accept-source-agreements --silent --location E:\citylbm_buildchain\VSBuildTools --override "--wait --quiet --norestart --installPath E:\citylbm_buildchain\VSBuildTools --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --add Microsoft.VisualStudio.Component.VC.CMake.Project --add Microsoft.VisualStudio.Component.Windows11SDK.26100"
```

## Boundary

This gate verifies the VS C++ recovery path and current machine blockers. It does not install tools unless the PowerShell script is explicitly run with -Install, does not recover GPU runtime, does not add CFD output, and does not permit formal v0.4.0.
