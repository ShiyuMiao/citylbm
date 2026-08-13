# Case E Environment Recovery Runbook

Generated: 2026-08-13T04:35:53.213192+00:00

## Verdict

- Official follow-up run allowed now: False
- Formal v0.4.0 release allowed: False
- Claim readiness: `blocked_environment_recovery_runbook`

## Workspace Cleanup Candidates

| path | exists | files | size MB |
|---|---:|---:|---:|
| `CityLBM/NuGet` | True | 1 | 0.0 |
| `CityLBM/bin/Release` | True | 5 | 3.809 |
| `CityLBM/obj` | True | 14 | 0.288 |
| `NuGet` | True | 1 | 0.0 |

## Recovery Steps

| step | enabled | priority | gate | verification |
|---|---:|---:|---|---|
| `REC001_gpu_recovery` | True | 1 | gpu_runtime | `nvidia-smi` |
| `REC002_free_c_drive` | True | 2 | vs_cpp_build_tools | `Get-PSDrive C` |
| `REC003_install_vs_cpp` | True | 3 | vs_cpp_build_tools | `winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget --accept-package-agreements --accept-source-agreements --silent --location E:\citylbm_buildchain\VSBuildTools --override "--wait --quiet --norestart --installPath E:\citylbm_buildchain\VSBuildTools --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --add Microsoft.VisualStudio.Component.VC.CMake.Project --add Microsoft.VisualStudio.Component.Windows11SDK.26100"` |
| `REC004_refresh_build_chain` | True | 4 | build_chain_manifest | `python docs/experiments/casee/tools/build_chain_audit.py` |
| `REC005_rhino_manifest` | True | 5 | rhino_gha_load | `python docs/experiments/casee/tools/rhino_gha_load_gate.py` |
| `REC006_preflight_rerun` | True | 6 | official_followup_preflight | `python docs/experiments/casee/tools/casee_official_run_preflight.py` |
| `REC007_reproducibility_suite` | True | 7 | evidence_chain | `python docs/experiments/casee/tools/reproducibility_suite.py` |

## Details

### REC001_gpu_recovery

- Action: Reboot or recover the NVIDIA driver/device before any long native FluidX3D run.
- Pass condition: returncode=0 and no GPU-lost message.
- Risk boundary: GPU readiness is environment evidence only, not solver accuracy.

### REC002_free_c_drive

- Action: Free C: drive space to at least 8 GB before retrying VS Build Tools C++; current free space is 1.515 GB. Workspace build-cache candidates total only 4.097 MB.
- Pass condition: C: free space >= 8 GB; workspace cache cleanup alone is not enough if the current value remains near 0.5 GB.
- Risk boundary: Do not delete user data; record any cleanup outside the repo separately.

### REC003_install_vs_cpp

- Action: After freeing disk space and approving UAC, install Visual Studio Build Tools 2022 C++ workload.
- Pass condition: Installer exits 0 and vswhere finds Microsoft.VisualStudio.Component.VC.Tools.x86.x64.
- Risk boundary: Installation readiness is build-chain evidence only.

### REC004_refresh_build_chain

- Action: Refresh the build-chain manifest after GPU, disk, or VS changes.
- Pass condition: build_chain_manifest.json records the updated GPU, disk, .NET, FluidX3D and VS C++ status.
- Risk boundary: This does not create a new CFD result.

### REC005_rhino_manifest

- Action: Load the tracked CityLBM/bin/CityLBM.gha in Rhino/Grasshopper and create the manual load manifest plus screenshot/log evidence.
- Pass condition: rhino_gha_load_gate.json reports rhino_loaded_new_gha=true from real manifest evidence.
- Risk boundary: Software-load identity only; not CFD accuracy.

### REC006_preflight_rerun

- Action: Rerun official follow-up preflight before scheduling another long Case E native run.
- Pass condition: official_followup_run_allowed=true before launching another official long follow-up.
- Risk boundary: Preflight readiness is not solver-output evidence.

### REC007_reproducibility_suite

- Action: Run the full lightweight evidence suite after any recovery or code change.
- Pass condition: suite_passed=true; formal_release_allowed remains false until official z=2 m metrics pass.
- Risk boundary: Claim-safety evidence only unless a new audited official probe CSV is supplied.

## Boundary

This runbook records recovery actions for environment and build-chain blockers. It does not delete files, install tools, run CFD, improve official z=2 m metrics, or allow formal v0.4.0.
