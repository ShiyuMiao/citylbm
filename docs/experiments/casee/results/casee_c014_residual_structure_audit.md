# C014 Residual Structure Audit

Generated: 2026-08-11T03:02:03.359690+00:00

## Verdict

- Evidence type: `newly_run` audit over `preexisting_artifact` C014 solver output
- C014 MAE: 13.786 pp
- C014 R2: -0.229845
- C014 Pearson: 0.314966
- Post-hoc affine upper-bound R2: 0.099203
- Formal accuracy claim supported: False

## Residual Groups

| group | n | MAE pp | bias pp | R2 | Pearson | paper use |
|---|---:|---:|---:|---:|---:|---|
| `all` | 80 | 13.786 | -3.514 | -0.229845 | 0.314966 | Use as the C014 official-height negative-improvement summary. |
| `upstream_y_ge_0_inferred` | 42 | 12.655 | -2.894 | 0.048177 | 0.471442 | Use as residual-structure diagnostic evidence only. |
| `downstream_y_lt_0_inferred` | 38 | 15.035 | -4.199 | -0.566325 | 0.131206 | Use to identify the downstream half as a priority residual region. |
| `x_west_lt_0` | 43 | 13.576 | -4.330 | -0.258259 | 0.325223 | Use as residual-structure diagnostic evidence only. |
| `x_east_ge_0` | 37 | 14.030 | -2.566 | -0.200937 | 0.302834 | Use as residual-structure diagnostic evidence only. |
| `solid0_low_risk` | 54 | 12.123 | -5.008 | -0.028112 | 0.403415 | Use as near-wall and solid-corner limitation evidence. |
| `solid1_2_moderate_risk` | 12 | 15.681 | -12.883 | -0.557344 | 0.402262 | Use as near-wall and solid-corner limitation evidence. |
| `solid3_4_high_risk` | 14 | 18.576 | 10.279 | -0.580078 | 0.377384 | Use as near-wall and solid-corner limitation evidence. |
| `official_low_lt_0p3` | 17 | 13.933 | 12.724 | -11.487922 | 0.016371 | Use to explain overprediction in sheltered official low-speed probes. |
| `official_mid_0p3_0p6` | 52 | 12.052 | -5.123 | -1.603692 | 0.191352 | Use as residual-structure diagnostic evidence only. |
| `official_high_ge_0p6` | 11 | 21.755 | -21.002 | -13.313737 | 0.211752 | Use to explain that high-speed official probes remain under-recovered. |
| `pred_low_lt_0p3` | 19 | 12.387 | -9.353 | -0.937769 | -0.124043 | Use as residual-structure diagnostic evidence only. |
| `pred_mid_0p3_0p6` | 53 | 13.054 | -4.371 | -0.121093 | 0.181706 | Use as residual-structure diagnostic evidence only. |
| `pred_high_ge_0p6` | 8 | 21.952 | 16.028 | -1.160873 | -0.877421 | Use as residual-structure diagnostic evidence only. |

## Diagnostic Sampling Check

| mode | boundary | MAE pp | R2 | Pearson |
|---|---|---:|---:|---:|
| `raw_trilinear` | formal | 13.786 | -0.229845 | 0.314966 |
| `nearest_valid` | diagnostic_only | 17.797 | -1.055080 | 0.170335 |
| `fluid_weighted` | diagnostic_only | 15.856 | -0.601937 | 0.264100 |
| `vertical_valid_above` | diagnostic_only | 15.886 | -0.558624 | 0.285521 |
| `z_plus_half` | diagnostic_only | 12.939 | -0.110842 | 0.365416 |

## Largest Absolute Residuals

| No. | x | y | official | predicted | residual pp | solid | bin |
|---:|---:|---:|---:|---:|---:|---:|---|
| 46 | -121.0 | -56.5 | 0.180 | 0.761 | 58.07 | 4 | official_low_lt_0p3 |
| 79 | 81.5 | -69.5 | 0.320 | 0.767 | 44.75 | 4 | official_mid_0p3_0p6 |
| 60 | 88.5 | -6.0 | 0.730 | 0.359 | -37.06 | 0 | official_high_ge_0p6 |
| 56 | 38.0 | 5.5 | 0.670 | 0.320 | -35.03 | 2 | official_high_ge_0p6 |
| 24 | -56.0 | 33.0 | 0.460 | 0.123 | -33.69 | 0 | official_mid_0p3_0p6 |
| 62 | 39.5 | -20.0 | 0.690 | 0.356 | -33.37 | 2 | official_high_ge_0p6 |
| 78 | 45.5 | -86.5 | 0.280 | 0.588 | 30.80 | 4 | official_low_lt_0p3 |
| 2 | -93.0 | 33.0 | 0.590 | 0.288 | -30.15 | 0 | official_mid_0p3_0p6 |
| 28 | -39.5 | -4.0 | 0.710 | 0.415 | -29.51 | 2 | official_high_ge_0p6 |
| 13 | -97.0 | 19.0 | 0.590 | 0.306 | -28.37 | 0 | official_mid_0p3_0p6 |
| 71 | 66.5 | -24.5 | 0.500 | 0.222 | -27.82 | 0 | official_mid_0p3_0p6 |
| 38 | -26.0 | -10.0 | 0.610 | 0.352 | -25.75 | 0 | official_high_ge_0p6 |

## Boundary

This audit explains why the best C014 diagnostic candidate is still not paper-grade validation. It uses official z=2 m raw_trilinear C014 rows for residual analysis, but it does not add a new FluidX3D run, does not alter release_gate.json official metrics, and does not justify formal v0.4.0.
