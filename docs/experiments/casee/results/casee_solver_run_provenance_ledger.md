# Case E Solver Run Provenance Ledger

Generated: 2026-08-13T11:04:37.324088+00:00

## Verdict

- Ledger passed: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_provenance_ledger`
- Formal accuracy claim supported: False
- Solver run rows: 13
- Diagnostic/protocol rows: 3

## Rows

| run | kind | evidence | MAE pp | R2 | Pearson | csv | log | claim |
|---|---|---|---:|---:|---:|---|---|---|
| `release_gate_current_official_z2m` | metric_recompute | newly_run / preexisting_artifact | 21.111408125 | -2.006330362229977 | 0.11575649438573923 | `docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv` | `` | limitations_ready_negative_validation |
| `C001_dx2_zcenter_replicate_best_known` | solver_run | newly_run / newly_run | 21.111408125 | -2.006330362229977 | 0.11575649438573923 | `docs/experiments/casee/results/casee_native_dx2_zcenter_rerun_20260809_203439_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_dx2_zcenter_rerun_20260809_203439.log` | paper_ready_reproducibility; blocked formal accuracy release |
| `C002_dx2_longer_mean_stability` | solver_run | newly_run / newly_run | 22.015022499999997 | -2.1851358653077058 | -0.0089370077112125 | `docs/experiments/casee/results/casee_c002_dx2_longer_mean_20260809_205343_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c002_dx2_longer_mean_run_20260809_205343.log` | limitations_ready_candidate_result; blocked formal accuracy release |
| `C003_dx2_no_zcenter_ablation` | solver_run | newly_run / newly_run | 23.125594087499998 | -2.221378753276796 | 0.09921683588947784 | `docs/experiments/casee/results/casee_c003_dx2_no_zcenter_20260809_212601_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c003_dx2_no_zcenter_run_20260809_212601.log` | limitations_ready_zorigin_ablation; blocked formal accuracy release |
| `C004_dx3_low_cost_direction_check` | solver_run | newly_run / newly_run | 24.48456695 | -2.5282993702661267 | 0.10934876905648619 | `docs/experiments/casee/results/casee_c004_dx3_low_cost_20260809_214302_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c004_dx3_low_cost_run_20260809_214302.log` | limitations_ready_dx3_low_cost_regression; blocked formal accuracy release |
| `C005_dx2_domain_decomposition_ablation` | solver_run | newly_run / newly_run | 19.7262730375 | -1.608075055394031 | 0.09931531110580517 | `docs/experiments/casee/results/casee_c005_dx2_decomp4x1x1_20260809_215600_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c005_dx2_decomp4x1x1_run_20260809_215600.log` | limitations_ready_runtime_decomposition_ablation; blocked formal accuracy release |
| `C008_inlet_k_synthetic_fullplane_s0p35` | solver_run | newly_run / newly_run | 14.76899495 | -0.3738588496510471 | 0.28160955502614543 | `docs/experiments/casee/results/casee_c008_inlet_k_synthetic_20260809_221958_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c008_inlet_k_synthetic_run_20260809_221958.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C009_inlet_k_synthetic_fullplane_s0p70` | solver_run | newly_run / newly_run | 14.677544574999999 | -0.3598186886134105 | 0.2834105384611786 | `docs/experiments/casee/results/casee_c009_inlet_k_synthetic_s0p7_20260809_223022_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c009_inlet_k_synthetic_s0p7_run_20260809_223022.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C010_inlet_k_synthetic_fullplane_s1p00` | solver_run | newly_run / newly_run | 14.447778762499999 | -0.3365050257235407 | 0.2869083408749314 | `docs/experiments/casee/results/casee_c010_inlet_k_synthetic_s1p0_20260809_225516_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c010_inlet_k_synthetic_s1p0_run_20260809_225516.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C011_inlet_k_synthetic_fullplane_s1p50` | solver_run | newly_run / newly_run | 14.3750643375 | -0.32680378704255153 | 0.2856641275815884 | `docs/experiments/casee/results/casee_c011_inlet_k_synthetic_s1p5_20260809_230150_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c011_inlet_k_synthetic_s1p5_run_20260809_230150.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C012_inlet_k_synthetic_fullplane_s2p00` | solver_run | newly_run / newly_run | 14.3858118625 | -0.33071101307031925 | 0.28009027913979595 | `docs/experiments/casee/results/casee_c012_inlet_k_synthetic_s2p0_20260809_233100_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c012_inlet_k_synthetic_s2p0_run_20260809_233100.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C013_inlet_k_synthetic_fullplane_s1p50_no_sgs` | solver_run | newly_run / newly_run | 14.171929962500002 | -0.2910782045991698 | 0.289718251551298 | `docs/experiments/casee/results/casee_c013_inlet_k_synthetic_s1p5_nosgs_20260809_234500_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c013_inlet_k_synthetic_s1p5_nosgs_run_20260809_234500.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C014_inlet_k_synthetic_fullplane_s2p00_no_sgs` | solver_run | newly_run / newly_run | 13.7856467875 | -0.22984501828340775 | 0.31496559664177526 | `docs/experiments/casee/results/casee_c014_inlet_k_synthetic_s2p0_nosgs_20260809_235100_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c014_inlet_k_synthetic_s2p0_nosgs_run_20260809_235100.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C015_inlet_k_synthetic_fullplane_s2p50_no_sgs` | solver_run | newly_run / newly_run | 13.911236162500002 | -0.2540964291683978 | 0.29367767575075826 | `docs/experiments/casee/results/casee_c015_inlet_k_synthetic_s2p5_nosgs_20260810_000000_probe_time_mean.csv` | `docs/experiments/casee/results/fluidx3d_c015_inlet_k_synthetic_s2p5_nosgs_run_20260810_000000.log` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release |
| `C014_residual_structure_audit` | diagnostic_audit | newly_run / preexisting_artifact | 13.7856467875 | -0.22984501828340775 | 0.31496559664177526 | `docs/experiments/casee/results/casee_c014_inlet_k_synthetic_s2p0_nosgs_20260809_235100_probe_time_mean.csv` | `` | limitations_ready_residual_structure; blocked formal accuracy release |
| `C016_residual_target_leakage_guard` | protocol_guard | newly_run / not_a_solver_run |  |  |  | `` | `` | paper_ready_protocol_risk_guard |

## Protocol Risks

- Official validation remains z = 2 m, 80 probes, raw_trilinear sampling.
- Rows without solver logs are diagnostic/protocol artifacts, not CFD runs.
- C014 residual and C016 guard rows cannot be used as formal accuracy metrics.
- Formal v0.4.0 remains blocked until release_gate.json passes.

## Boundary

This ledger consolidates provenance for existing Case E metrics. It does not create new CFD output, does not alter metrics, and does not support formal v0.4.0 while the official release gate is blocked.
