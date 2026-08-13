# Case E Official Run Preflight

Generated: 2026-08-13T05:32:13.352528+00:00

## Verdict

- Official follow-up run allowed now: False
- Formal v0.4.0 release allowed: False
- Claim readiness: `blocked_official_followup_preflight`

## Current Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923

## Gates

| gate | status | severity | required action |
|---|---:|---|---|
| `official_data_manifest` | pass | critical | Re-download and hash-check Zenodo Case E files if this fails. |
| `official_probe_protocol` | pass | critical | Keep formal validation locked to ac+N z=2 m with 80 raw_trilinear probes. |
| `citylbm_build` | pass | critical | Run reproducibility_suite.py or dotnet build until the Release build passes. |
| `plugin_identity` | pass | major | Regenerate plugin_identity_gate.py after rebuilding CityLBM.gha. |
| `rhino_gha_load` | blocked | major | Create a real Rhino/Grasshopper load manifest with version/hash screenshot or log evidence. |
| `dotnet_sdk` | pass | major | Restore the local .NET SDK path or install .NET SDK before rebuilding CityLBM. |
| `fluidx3d_binary` | pass | critical | Restore or rebuild FluidX3D.exe before scheduling native Case E. |
| `gpu_runtime` | blocked | critical | Recover/reboot the NVIDIA device until nvidia-smi returns 0 without GPU-lost errors. |
| `vs_cpp_build_tools` | blocked | major | Free C: space, approve UAC, and install Visual Studio Build Tools 2022 C++ workload. |
| `native_source_compile_path` | pass | critical | Provide either VS C++ Build Tools or the documented MinGW/g++ fallback before generating a new FluidX3D setup candidate. |
| `casea_smoke_regression` | pass | major | Rerun Case A smoke regression after any default solver change. |

## Boundary

This preflight controls whether another official native Case E follow-up can be scheduled. It is not solver-output evidence, does not change official z=2 m metrics, and does not allow formal v0.4.0.
