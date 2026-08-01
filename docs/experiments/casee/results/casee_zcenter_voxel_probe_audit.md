# Case E Voxel/Probe Protocol Audit

Generated: 2026-08-01T11:30:58.383104+00:00
Prediction source: `docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv`

## Mesh and Grid

- STL scale factor: 250
- Physical mesh bbox: x [-197.929, 197.387], y [-196.925, 198.226], z [-0.000, 60.000] m.
- Audited grid: dx = 2 m, ground offset cells = 1, origin z offset = 1 m.
- Official z = 2 m lies on a lattice-center height in this diagnostic setup.

## Summary

- High protocol-risk probes: 14 / 80.
- Low protocol-risk probes: 47 / 80.
- Pearson(raw absolute error, wall distance): -0.109184.
- Pearson(raw absolute error, footprint distance): -0.108643.
- Pearson(raw absolute error, solid-neighbor count): 0.552638.
- Pearson(z_plus_half improvement, solid-neighbor count): 0.540488.
- Claim readiness: limitations/protocol-risk evidence only.

## Risk Groups

| group | n | raw MAE pp | z_plus_half MAE pp | vertical_valid_above MAE pp | mean wall distance m | mean solid neighbors |
|---|---:|---:|---:|---:|---:|---:|
| low | 47 | 12.435 | 12.693 | 13.024 | 5.843 | 0.000 |
| moderate | 19 | 32.644 | 27.054 | 21.863 | 4.311 | 2.000 |
| high | 14 | 34.589 | 27.877 | 18.265 | 3.034 | 3.857 |
| all | 80 | 21.111 | 18.761 | 16.041 | 4.988 | 1.150 |

## Interpretation

This diagnostic removes vertical two-layer interpolation at official z = 2 m, so any remaining error is less attributable to height straddling alone.
The association between solid-neighbor count and diagnostic sampling improvement supports treating near-wall/probe protocol as a primary limitation.
This audit does not validate predictive accuracy; it narrows the next software work toward explicit wall-distance-aware probe reporting and wall/voxelization model changes.
