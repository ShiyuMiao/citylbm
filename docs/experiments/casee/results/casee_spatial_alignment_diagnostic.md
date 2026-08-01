# Case E Spatial Alignment Diagnostic

Generated: 2026-08-01T10:59:54.082128+00:00
Prediction source: `docs\experiments\casee\results\casee_native_dx2_gshift1_nu001_probe_time_mean.csv`

## Purpose

This diagnostic checks whether poor official z=2 m correlation could be explained by a simple x/y coordinate convention drift.
It reassigns each official probe to the nearest predicted probe after candidate coordinate transforms, then recomputes the official metrics.

## Summary

- Identity Pearson: 0.071789; R2: -2.311768; MAE: 23.972 pp.
- Best Pearson transform: `identity` with Pearson 0.071789.
- Best R2 transform: `flip_y` with R2 -2.111059.
- Claim readiness: limitations only. This is a coordinate-audit diagnostic, not an accuracy validation.

## Transform Metrics

| transform | MAE pp | R2 | Pearson | mean nearest m | unique matched |
|---|---:|---:|---:|---:|---:|
| identity | 23.972 | -2.311768 | 0.071789 | 0.00 | 80 |
| flip_x | 25.120 | -2.664853 | 0.029985 | 12.31 | 55 |
| flip_y | 23.124 | -2.111059 | 0.069213 | 12.37 | 49 |
| flip_x_and_y | 26.729 | -2.887267 | -0.096767 | 9.97 | 55 |
| swap_xy | 27.110 | -3.107001 | -0.007625 | 14.07 | 44 |
| swap_xy_flip_new_x | 26.185 | -2.808519 | -0.084309 | 17.34 | 42 |
| swap_xy_flip_new_y | 25.943 | -2.998036 | -0.121681 | 17.46 | 35 |
| swap_xy_flip_both | 26.681 | -3.048680 | -0.263069 | 14.74 | 46 |

## Interpretation

No tested x/y flip, swap, or 90-degree rotation makes the official z=2 m R2 positive.
The current evidence therefore points away from a simple coordinate-convention error and toward near-wall sampling, wall modeling, inlet turbulence, voxelization, or probe-location protocol fidelity.
