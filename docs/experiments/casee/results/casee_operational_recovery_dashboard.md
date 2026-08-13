# Case E Operational Recovery Dashboard

Generated: 2026-08-13T13:06:00.453277+00:00

## Verdict

- Dashboard passed: True
- Claim readiness: `operational_recovery_ready; blocked official run and formal release`
- Blocking steps: 7
- Long FluidX3D run allowed: False
- Long-run blockers: OP001_system_drive_space, OP004_gpu_recovery, OP006_official_followup_preflight
- Formal v0.4.0 allowed: False
- Recommended tag: `v0.4.0-rc92`

## Ordered Recovery Path

| priority | step | status | blocks long run | next action | verification |
|---:|---|---|---:|---|---|
| 1 | `OP001_system_drive_space` | blocked | True | Free system-drive space manually until C: has at least 8 GB free. | `python docs/experiments/casee/tools/vs_cpp_system_drive_space_gate.py` |
| 2 | `OP002_vs_cpp_install` | blocked | False | After C: space is sufficient, launch the explicit UAC recovery script and verify vswhere/VC tools. | `python docs/experiments/casee/tools/vs_cpp_recovery_gate.py` |
| 3 | `OP003_uac_launcher` | blocked | False | Run the launcher with -Launch only after space blockers are resolved. | `powershell -NoProfile -ExecutionPolicy Bypass -File docs/experiments/casee/tools/vs_cpp_buildtools_elevated_launcher.ps1 -Launch -NoPause` |
| 4 | `OP004_gpu_recovery` | blocked | True | Reboot or recover the NVIDIA device, then rerun the GPU fail-fast gate. | `python docs/experiments/casee/tools/citylbm_gpu_runtime_failfast_gate.py` |
| 5 | `OP005_rhino_load_evidence` | blocked | False | Load the staged GHA in Rhino/Grasshopper and record the manual manifest plus screenshot/log evidence. | `python docs/experiments/casee/tools/rhino_gha_load_manifest_schema_gate.py` |
| 6 | `OP006_official_followup_preflight` | blocked | True | Rerun preflight after environment recovery before generating or launching another official long run. | `python docs/experiments/casee/tools/casee_official_run_preflight.py` |
| 7 | `OP007_formal_metric_gate` | blocked | False | Only a completed, logged official z=2 m raw_trilinear run can replace this metric gate. | `python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_casee_probe_time_mean.csv>` |

## Evidence Links

- `OP001_system_drive_space`: `docs/experiments/casee/results/vs_cpp_system_drive_space_gate.json`; C: free=0.0 GB; needed=8.0 GB; shortfall=8.0 GB
- `OP002_vs_cpp_install`: `docs/experiments/casee/results/vs_cpp_recovery_gate.json`; vs_cpp_ready=False; can_attempt_install_now=False; blockers=5
- `OP003_uac_launcher`: `docs/experiments/casee/results/vs_cpp_elevated_launcher_gate.json`; can_launch=False; launch_attempted=False; blockers=['system drive free space is below 8 GB']
- `OP004_gpu_recovery`: `docs/experiments/casee/results/citylbm_gpu_runtime_failfast_gate.json`; gpu_runtime_ready=False; gpu_lost_detected=True; long_run_allowed=False
- `OP005_rhino_load_evidence`: `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.json`; manual_manifest_present=False; manual_manifest_claim_ready=False; rhino_loaded_new_gha=False
- `OP006_official_followup_preflight`: `docs/experiments/casee/results/casee_official_run_preflight.json`; official_followup_run_allowed=False; blocked_gates=['official_data_manifest', 'rhino_gha_load', 'gpu_runtime', 'vs_cpp_build_tools']
- `OP007_formal_metric_gate`: `docs/experiments/casee/results/release_gate.json`; MAE=21.111408125 pp; R2=-2.006330362229977; Pearson=0.11575649438573923; formal_release_allowed=False

## Boundary

This dashboard aggregates existing recovery gates and commands only. It does not free disk space, install tools, recover GPU runtime, load Rhino, run FluidX3D, alter solver defaults, improve official metrics, or permit formal v0.4.0.
