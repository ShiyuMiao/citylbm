# Case E Candidate Sweep Plan

Generated: 2026-08-11T00:52:36.953119+00:00

## Verdict

- Plan generated: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_followup_plan; blocked formal accuracy release`
- Formal accuracy claim supported: False
- Formal release allowed: False
- Candidate count: 9
- Executable-now count: 0

## Current Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923
- Sampling mode: `raw_trilinear`

## Candidates

| priority | candidate | executable now | class | blocking gates | pass condition |
|---:|---|---:|---|---|---|
| 1 | `C001_dx2_zcenter_replicate_best_known` | False | current_compiled_binary_rerun | `gpu_runtime; gpu_runtime; official_followup_preflight; current_deployed_binary_not_matching_baseline` | Reproduces n=80 raw_trilinear official z=2 m metrics within audit tolerance. |
| 2 | `C002_dx2_longer_mean_stability` | False | time_mean_stability | `gpu_runtime; gpu_runtime; official_followup_preflight` | Pearson remains positive and R2 moves toward zero without diagnostic sampling substitution. |
| 3 | `C003_dx2_no_zcenter_ablation` | False | protocol_ablation | `gpu_runtime; gpu_runtime; official_followup_preflight` | Shows whether z-origin sensitivity is a diagnostic limitation rather than a stable accuracy fix. |
| 4 | `C004_dx3_low_cost_direction_check` | False | low_cost_regression | `gpu_runtime; gpu_runtime; official_followup_preflight` | No reversal of Pearson sign and no protocol mismatch in manifest/logs. |
| 5 | `C005_dx2_domain_decomposition_ablation` | False | runtime_ablation | `gpu_runtime; gpu_runtime; official_followup_preflight` | Raw_trilinear metrics remain consistent with C001 within expected numerical variability. |
| 6 | `C006_dx1_dry_allocation_then_short_smoke` | False | high_resolution_preflight | `user_confirmation_required; dx1_memory_headroom; gpu_memory_headroom_lt_25pct` | Only proceed after dry allocation confirms memory headroom and the user approves a long run. |
| 7 | `C007_default_off_wall_physics_implementation` | False | requires_implementation | `physical_wall_model_not_implemented` | MAE clearly below the current near-20 pp level, R2>0, Pearson>0, Case A smoke regression passes. |
| 8 | `C008_C015_full_plane_inlet_turbulence_sgs_sweep` | False | requires_implementation | `gpu_runtime; gpu_runtime; official_followup_preflight` | Official raw_trilinear metric improves without relying on non-raw sampling or z-height substitution. |
| 9 | `C016_residual_targeted_wall_inlet_channel_response` | False | requires_implementation | `gpu_runtime; residual_targeted_wall_inlet_channel_response_not_implemented; official_followup_preflight` | Official raw_trilinear z=2 m R2 becomes positive, Pearson remains positive, MAE stays below C014, and Case A smoke regression passes. |

## Boundary

This plan ranks future official z=2 m follow-up candidates and records their commands, blockers, and pass conditions. It does not start FluidX3D, does not add solver-output evidence, and does not support formal v0.4.0 or predictive-accuracy claims.
