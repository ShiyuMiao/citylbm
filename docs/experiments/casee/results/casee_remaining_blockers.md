# Case E Remaining Blockers And Remediation Plan

Generated: 2026-08-11T01:31:25.242999+00:00

## Verdict

- Formal v0.4.0 allowed: False
- Recommended tag: `v0.4.0-rc57`
- Official z=2 m MAE: 21.111408125 pp
- Official z=2 m R2: -2.006330362229977
- Official z=2 m Pearson: 0.11575649438573923

## Blockers

| id | status | severity | release gate | pass condition |
|---|---|---|---|---|
| `B001_official_z2m_metric_gate` | blocked | critical | official_z2m_metric_gate | n=80, height=2 m, sampling=raw_trilinear, MAE clearly below prior near-20 pp level, R2>0, Pearson>0. |
| `B002_rhino_new_gha_load` | blocked | critical | rhino_loaded_new_gha | Rhino/Grasshopper session demonstrably loads the new tracked GHA, not an old installed copy. |
| `B003_gpu_runtime` | blocked | critical | native_fluidx3d_followup_capacity | nvidia-smi returns 0 and reports the target GPU without GPU-lost errors. |
| `B004_vs_cpp_build_tools` | blocked | major | native_fluidx3d_build_capacity | vswhere returns a VC tools installation path and vcvars64.bat/cl.exe are available. |
| `B005_dx1_high_resolution_run` | not_started | major | mesh_resolution_followup | Completed official z=2 m dx=1 m run with all 80 raw_trilinear probe predictions and complete log. |

## Required Actions

### B001_official_z2m_metric_gate

- Current evidence: official z=2 m raw_trilinear n=80; MAE=21.111 pp; R2=-2.006330; Pearson=0.115756
- Required action: Run a new official z=2 m raw_trilinear Case E experiment only after a physically defensible change to wall treatment, inlet turbulence, voxelization, or probe protocol implementation is made.
- Verification: `python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_official_casee_probe_time_mean.csv>`
- Paper use: Use current value only as negative validation and limitations evidence.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or LES improvement.

### B002_rhino_new_gha_load

- Current evidence: rhino_loaded_new_gha=False
- Required action: Load the tracked CityLBM/bin/CityLBM.gha in Rhino/Grasshopper and capture plugin version/hash evidence.
- Verification: `Manual Rhino/Grasshopper load check plus screenshot/log showing CityLBM Version=0.4.0-rc and matching GHA SHA256.`
- Paper use: Use only after an independently recorded artifact exists.
- Forbidden claim: Do not state the new plugin was loaded in Rhino until this artifact exists.

### B003_gpu_runtime

- Current evidence: nvidia-smi returncode=15; stdout=Unable to determine the device handle for GPU0000:C3:00.0: GPU is lost.  Reboot the system to recover this GPU
- Required action: Recover the NVIDIA device/driver before any additional long native FluidX3D validation run.
- Verification: `nvidia-smi`
- Paper use: Use as an environment blocker statement.
- Forbidden claim: Do not describe the native validation chain as currently ready for new long runs.

### B004_vs_cpp_build_tools

- Current evidence: VS C++ status=blocked; C: free=4.969 GB
- Required action: Free enough space on C: or redirect installer cache, approve UAC, and install Visual Studio Build Tools 2022 C++ workload.
- Verification: `"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`
- Paper use: Use as build-chain limitation until ready.
- Forbidden claim: Do not claim the Windows native C++ build chain is complete.

### B005_dx1_high_resolution_run

- Current evidence: dx1_readiness=high_risk_blocked_until_dry_run; memory_headroom_ok=False; moderate_required_per_gpu_gib=13.79; gpu_min_free_gib=0.0; run_started=False
- Required action: Run a user-confirmed dx=1 dry allocation test or adjust domain/decomposition before scheduling a full 48000-step dx=1 official run.
- Verification: `docs/experiments/casee/results/<dx1_run_log>; docs/experiments/casee/results/<dx1_probe_time_mean.csv>`
- Paper use: Use current state only as future-work planning.
- Forbidden claim: Do not claim mesh independence from dx=2/3 diagnostics.

## Next Experiment Queue

| priority | experiment | trigger | formal output | default policy |
|---:|---|---|---|---|
| 1 | `casee_wall_model_followup` | GPU recovered and a physically defensible wall/roughness/voxelization implementation change exists. | official z=2 m raw_trilinear 80-probe CSV | Promote to CityLBM default only if official raw_trilinear metric improves and survives Case A smoke regression. |
| 2 | `casee_inlet_turbulence_followup` | Full-plane digital-filter inlet parameters are changed from documented AF_caseE z,U,k evidence. | official z=2 m raw_trilinear 80-probe CSV | Keep as experimental switch unless official metric improvement is stable. |
| 3 | `casee_dx1_feasibility_or_run` | GPU runtime ready and memory/runtime estimate is acceptable. | dx=1 m official z=2 m raw_trilinear run if feasible | Do not claim mesh independence until the metric trend supports it. |

## Boundary

This plan is operational evidence for remaining work. It does not add a new CFD run, does not improve the official z=2 m metric, and does not allow a formal v0.4.0 tag.
