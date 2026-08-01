# Case E Probe-Mode Metrics

Generated: 2026-08-01T11:30:28.665052+00:00
Prediction source: `docs\experiments\casee\results\casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv`

## Summary

- Formal raw_trilinear: MAE 21.111 pp, R2 -2.006330, Pearson 0.115756.
- Best diagnostic MAE: `vertical_valid_above` with MAE 16.041 pp.
- Best diagnostic Pearson: `vertical_valid_above` with Pearson 0.336940.
- Claim readiness: diagnostics/limitations only; no diagnostic sampling mode makes official z=2 m R2 positive.

## Mode Metrics

| sampling_mode | boundary | MAE pp | RMSE pp | Bias pp | R2 | Pearson | pred_mean |
|---|---|---:|---:|---:|---:|---:|---:|
| raw_trilinear | formal | 21.111 | 27.721 | -16.409 | -2.006330 | 0.115756 | 0.258408 |
| nearest_valid | diagnostic | 18.724 | 24.124 | -13.271 | -1.276686 | 0.176049 | 0.289794 |
| fluid_weighted | diagnostic | 19.430 | 25.695 | -14.665 | -1.582872 | 0.179157 | 0.275852 |
| vertical_valid_above | diagnostic | 16.041 | 19.935 | -10.535 | -0.554717 | 0.336940 | 0.317151 |
| z_plus_half | diagnostic | 18.761 | 23.833 | -13.813 | -1.222132 | 0.239523 | 0.284367 |

## Interpretation

Alternative near-wall probe sampling reduces the underprediction bias and improves Pearson modestly, but all R2 values remain negative.
This supports a near-wall/probe-protocol limitation and motivates wall-model/voxelization changes before any default accuracy claim.

## Solid-Corner Group Detail

| sampling_mode | solid neighbors | n | MAE pp | R2 | Pearson |
|---|---:|---:|---:|---:|---:|
| raw_trilinear | 0 | 47 | 12.435 | -0.281039 | 0.322599 |
| raw_trilinear | 2 | 20 | 31.925 | -2.746254 | -0.135504 |
| raw_trilinear | 4 | 13 | 35.845 | -4.513468 | -0.254465 |
| nearest_valid | 0 | 47 | 13.024 | -0.347328 | 0.309129 |
| nearest_valid | 2 | 20 | 25.853 | -1.632766 | 0.047556 |
| nearest_valid | 4 | 13 | 28.366 | -2.740724 | -0.009774 |
| fluid_weighted | 0 | 47 | 12.435 | -0.281039 | 0.322599 |
| fluid_weighted | 2 | 20 | 26.115 | -1.679367 | 0.173585 |
| fluid_weighted | 4 | 13 | 34.435 | -4.382993 | -0.281564 |
| vertical_valid_above | 0 | 47 | 13.024 | -0.347328 | 0.309129 |
| vertical_valid_above | 2 | 20 | 21.548 | -0.788384 | 0.333005 |
| vertical_valid_above | 4 | 13 | 18.474 | -0.633008 | 0.633125 |
| z_plus_half | 0 | 47 | 12.693 | -0.352093 | 0.283207 |
| z_plus_half | 2 | 20 | 26.738 | -1.687297 | 0.238395 |
| z_plus_half | 4 | 13 | 28.426 | -2.342070 | 0.609851 |
