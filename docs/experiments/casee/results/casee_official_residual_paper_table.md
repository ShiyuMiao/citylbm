# Case E Official Residual Paper Table

Generated: 2026-08-13T14:14:23.163153+00:00

## Verdict

- Table passed: True
- Claim readiness: `limitations_ready_official_residual_paper_table`
- Formal accuracy claim supported: False
- Formal release allowed: False

## Official Metric Context

- n: 80
- MAE: 21.111408 pp
- RMSE: 27.721032 pp
- Bias: -16.409216 pp
- R2: -2.006330
- Pearson: 0.115756

## Protocol Checks

- input_exists: True
- probe_count_80: True
- ids_1_to_80: True
- case_ac: True
- wind_direction_n: True
- height_z2m: True
- raw_trilinear: True
- formal_metric_gate_failed: True

## Top Residual Probes

| rank | probe | official | predicted | residual pp | abs error pp | sse share |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 58 | 0.850 | 0.035 | -81.454 | 81.454 | 0.108 |
| 2 | 30 | 0.690 | 0.000 | -69.000 | 69.000 | 0.077 |
| 3 | 38 | 0.610 | 0.000 | -61.000 | 61.000 | 0.061 |
| 4 | 29 | 0.610 | 0.013 | -59.670 | 59.670 | 0.058 |
| 5 | 62 | 0.690 | 0.135 | -55.520 | 55.520 | 0.050 |
| 6 | 32 | 0.540 | 0.000 | -54.000 | 54.000 | 0.047 |
| 7 | 61 | 0.540 | 0.000 | -54.000 | 54.000 | 0.047 |
| 8 | 28 | 0.710 | 0.181 | -52.910 | 52.910 | 0.046 |
| 9 | 67 | 0.500 | 0.000 | -50.000 | 50.000 | 0.041 |
| 10 | 27 | 0.480 | 0.000 | -48.000 | 48.000 | 0.037 |

## Group Summary

| axis | group | n | official mean | predicted mean | MAE pp | bias pp | under fraction |
|---|---|---:|---:|---:|---:|---:|---:|
| official_speed_bin | high_official_ge_0p6 | 11 | 0.683 | 0.216 | 46.693 | -46.693 | 1.000 |
| official_speed_bin | low_official_lt_0p3 | 17 | 0.214 | 0.188 | 13.409 | -2.575 | 0.529 |
| official_speed_bin | mid_official_0p3_0p6 | 52 | 0.436 | 0.290 | 18.218 | -14.526 | 0.712 |
| solid_corner_risk | solid0_low_risk | 47 | 0.429 | 0.376 | 12.435 | -5.379 | 0.574 |
| solid_corner_risk | solid1_2_moderate_risk | 20 | 0.429 | 0.132 | 31.925 | -29.698 | 0.850 |
| solid_corner_risk | solid3plus_high_risk | 13 | 0.388 | 0.029 | 35.845 | -35.845 | 1.000 |
| windward_leeward_proxy | downstream_y_lt_0 | 38 | 0.443 | 0.246 | 22.486 | -19.774 | 0.816 |
| windward_leeward_proxy | upstream_y_ge_0 | 42 | 0.404 | 0.270 | 19.868 | -13.365 | 0.619 |

## Boundary

This table is derived from the official z=2 m residual CSV for manuscript diagnostics. It does not run FluidX3D, improve official metrics, support calibration-as-validation, or permit formal v0.4.0.
