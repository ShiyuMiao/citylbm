# Case E z-center Rerun Consistency

Generated: 2026-08-13T09:47:14.960154+00:00

## Verdict

- Status: `passed_reproduced_failed_metric`
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_reproducibility; blocked formal accuracy release`
- 48000-step log complete: True
- CSV SHA256 equal to baseline: True

## Official z=2 m raw_trilinear rerun metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923

## Artifacts

- Baseline CSV: `docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv`
- Rerun CSV: `docs/experiments/casee/results/casee_native_dx2_zcenter_rerun_20260809_203439_probe_time_mean.csv`
- Rerun log: `docs/experiments/casee/results/fluidx3d_dx2_zcenter_rerun_20260809_203439.log`
- Rerun stderr log: `docs/experiments/casee/results/fluidx3d_dx2_zcenter_rerun_20260809_203439.err.log`

## Boundary

This audit shows the current compiled z-center diagnostic reproduces the same official z=2 m raw_trilinear failure metric. It supports reproducibility and limitations claims only; it does not improve accuracy, does not support mesh independence, and does not allow formal v0.4.0.
