# Case E Probe-Mode Metrics

Generated: 2026-08-01T11:09:37.643665+00:00
Prediction source: `docs\experiments\casee\results\casee_native_dx2_gshift1_nu001_pmodes_probe_time_mean.csv`

## Summary

- Formal raw_trilinear: MAE 23.972 pp, R2 -2.311768, Pearson 0.071789.
- Best diagnostic MAE: `z_plus_half` with MAE 21.217 pp.
- Best diagnostic Pearson: `z_plus_half` with Pearson 0.187068.
- Claim readiness: diagnostics/limitations only; no diagnostic sampling mode makes official z=2 m R2 positive.

## Mode Metrics

| sampling_mode | boundary | MAE pp | RMSE pp | Bias pp | R2 | Pearson | pred_mean |
|---|---|---:|---:|---:|---:|---:|---:|
| raw_trilinear | formal | 23.972 | 29.095 | -20.833 | -2.311768 | 0.071789 | 0.214166 |
| nearest_valid | diagnostic | 21.918 | 26.620 | -15.360 | -1.772209 | 0.057643 | 0.268898 |
| fluid_weighted | diagnostic | 21.728 | 26.667 | -17.191 | -1.781966 | 0.050744 | 0.250589 |
| vertical_valid_above | diagnostic | 21.356 | 25.963 | -15.922 | -1.637050 | 0.118127 | 0.263278 |
| z_plus_half | diagnostic | 21.217 | 25.910 | -17.529 | -1.626431 | 0.187068 | 0.247212 |

## Interpretation

Alternative near-wall probe sampling reduces the underprediction bias and improves Pearson modestly, but all R2 values remain negative.
This supports a near-wall/probe-protocol limitation and motivates wall-model/voxelization changes before any default accuracy claim.

## Solid-Corner Group Detail

| sampling_mode | solid neighbors | n | MAE pp | R2 | Pearson |
|---|---:|---:|---:|---:|---:|
| raw_trilinear | 0 | 25 | 12.932 | -0.176479 | 0.356584 |
| raw_trilinear | 2 | 37 | 27.110 | -3.232168 | -0.199618 |
| raw_trilinear | 3 | 2 | 13.338 | -17.017904 | -1.000000 |
| raw_trilinear | 4 | 16 | 35.294 | -3.349963 | 0.269639 |
| nearest_valid | 0 | 25 | 13.482 | -0.216507 | 0.304044 |
| nearest_valid | 2 | 37 | 25.423 | -2.777439 | -0.190921 |
| nearest_valid | 3 | 2 | 15.768 | -19.147916 | -1.000000 |
| nearest_valid | 4 | 16 | 27.764 | -2.065253 | 0.247152 |
| fluid_weighted | 0 | 25 | 12.932 | -0.176479 | 0.356584 |
| fluid_weighted | 2 | 37 | 24.653 | -2.663749 | -0.237272 |
| fluid_weighted | 3 | 2 | 16.655 | -19.297106 | -1.000000 |
| fluid_weighted | 4 | 16 | 29.344 | -2.298553 | 0.270219 |
| vertical_valid_above | 0 | 25 | 13.482 | -0.216507 | 0.304044 |
| vertical_valid_above | 2 | 37 | 24.208 | -2.448213 | -0.060168 |
| vertical_valid_above | 3 | 2 | 15.768 | -19.147916 | -1.000000 |
| vertical_valid_above | 4 | 16 | 27.764 | -2.065253 | 0.247152 |
| z_plus_half | 0 | 25 | 13.064 | -0.188765 | 0.315931 |
| z_plus_half | 2 | 37 | 23.366 | -2.241758 | 0.137588 |
| z_plus_half | 3 | 2 | 16.759 | -20.560880 | -1.000000 |
| z_plus_half | 4 | 16 | 29.543 | -2.342521 | 0.257614 |
