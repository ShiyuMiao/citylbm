# Case E dx=1 m Readiness Audit

Generated: 2026-08-13T13:38:43.315173+00:00

## Verdict

- dx=1 readiness: `high_risk_blocked_until_dry_run`
- dx=1 memory headroom ok: False
- Run started: False
- Run allowed without user confirmation: False
- Formal accuracy claim supported: False

## Current Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923
- Formal release allowed: False

## dx=1 Command Under Audit

`python docs/experiments/casee/tools/generate_native_casee.py --dx 1 --steps 48000 --spinup 12000 --sample-dt 4000 --ground-offset-cells 1 --origin-z-offset-m 0.5 --nu-lbm 0.001`

## GPU And Memory Summary

- GPU count: 0
- Minimum free memory: 0.0 GiB
- Current generator moderate per-GPU requirement: 13.79 GiB
- Current generator moderate headroom: -1.0
- Current generator conservative per-GPU requirement: 27.58 GiB
- Conservative padding moderate per-GPU requirement: 68.408 GiB

## Memory Scenarios

| basis | scenario | cells | required/GPU GiB | min free GiB | headroom ok |
|---|---|---:|---:|---:|---:|
| current_generator_fixed_domain | optimistic_fp16s_core | 115680000 | 6.895 | 0.0 | False |
| current_generator_fixed_domain | moderate_fp16s_plus_overhead | 115680000 | 13.79 | 0.0 | False |
| current_generator_fixed_domain | conservative_runtime_overhead | 115680000 | 27.58 | 0.0 | False |
| conservative_stl_padding_estimate | optimistic_fp16s_core | 573851376 | 34.204 | 0.0 | False |
| conservative_stl_padding_estimate | moderate_fp16s_plus_overhead | 573851376 | 68.408 | 0.0 | False |
| conservative_stl_padding_estimate | conservative_runtime_overhead | 573851376 | 136.817 | 0.0 | False |

## Boundary

This audit is newly-run readiness evidence. It is not a FluidX3D solver run, not a Case E accuracy result, and not mesh-independence evidence.
