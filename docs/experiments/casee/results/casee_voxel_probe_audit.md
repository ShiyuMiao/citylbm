# Case E Voxel/Probe Protocol Audit

Generated: 2026-08-01T11:19:41.061098+00:00
Prediction source: `docs/experiments/casee/results/casee_native_dx2_gshift1_nu001_pmodes_probe_time_mean.csv`

## Mesh and Grid

- STL scale factor: 250
- Physical mesh bbox: x [-197.929, 197.387], y [-196.925, 198.226], z [-0.000, 60.000] m.
- Audited grid: dx = 2 m with one effective-ground offset cell.
- Official z = 2 m lies halfway between the z = 1 m and z = 3 m lattice centers in this diagnostic setup.

## Summary

- High protocol-risk probes: 19 / 80.
- Low protocol-risk probes: 25 / 80.
- Pearson(raw absolute error, wall distance): -0.132711.
- Pearson(raw absolute error, footprint distance): -0.132633.
- Pearson(raw absolute error, solid-neighbor count): 0.474583.
- Pearson(z_plus_half improvement, solid-neighbor count): 0.397877.
- Claim readiness: limitations/protocol-risk evidence only.

## Risk Groups

| group | n | raw MAE pp | z_plus_half MAE pp | vertical_valid_above MAE pp | mean wall distance m | mean solid neighbors |
|---|---:|---:|---:|---:|---:|---:|
| low | 25 | 12.932 | 13.064 | 13.482 | 6.940 | 0.000 |
| moderate | 36 | 27.162 | 23.316 | 24.152 | 4.842 | 2.028 |
| high | 19 | 32.454 | 27.967 | 26.421 | 2.694 | 3.737 |
| all | 80 | 23.972 | 21.217 | 21.356 | 4.988 | 1.800 |

## Interpretation

The official pedestrian-height probes are voxel-sensitive because z = 2 m is not a lattice-center height in the best dx = 2 m effective-ground diagnostic.
The association between solid-neighbor count and diagnostic sampling improvement supports treating near-wall/probe protocol as a primary limitation.
This audit does not validate predictive accuracy; it narrows the next software work toward explicit wall-distance-aware probe reporting and wall/voxelization model changes.
