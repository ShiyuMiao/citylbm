# AIJ Case E strict validation protocol

This document defines the strict rerun protocol for CityLBM v0.3.0. It is not a result file.

## Scope

- Case: AIJ Case E, construction-after condition `ac`
- Wind direction: `N`
- Software platform: Rhino 7 + Grasshopper + CityLBM v0.3.0
- Solver backend: FluidX3D through CityLBM generated `setup.cpp`

## Inputs

- Geometry: `BD_caseE.stl`
- Geometry scale: STL is `1:250`; scale by `250` before simulation or ensure generated STL is in full-scale meters.
- Inflow profile: `AF_caseE.csv`
- Required profile columns: `z(m), U(m/s), k(m2/s2)`
- CityLBM setting: `Wind Profile = 3` (`CustomTable`)
- Wind vector: `(0,-1,0)` for N wind interpreted as north-to-south flow
- Uref metadata: `3.928296 m/s @ 15.9 m`
- Measurement file: `RS_caseE.csv`
- Validation subset: `case=ac`, `direction=N`, pedestrian height `z=2 m`

## Simulation settings

- First smoke run: `dx=5 m`, `steps=2000-5000`, `save interval=500 or 1000`
- Formal validation: `dx=2-3 m`, `steps>=10000`, save enough final VTK frames for time averaging
- Use LES consistently and record `Cs`, viscosity, grid dimensions and GPU model.
- Do not compare a single early VTK frame as a final result.

## Required checks before accepting a run

- Generated `setup.cpp` contains `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]` and `profile_origin_z_m`.
- `domain_origin.json` exists in both case root and output directory.
- `case_metadata.json` exists in both case root and output directory.
- VTK files are newly generated for the current run directory, not copied from older experiments.
- Post-processing reads the final averaged velocity field, not an initial transient.
- Measurement interpolation uses the official `ac + N` points and records failed or out-of-domain probes.

## Metrics to report

- Valid point count and failed point count
- MAE and RMSE for normalized speed ratio
- Bias and bias ratio
- R2
- Regression slope and intercept
- Maximum absolute error
- Grid spacing, steps, averaging window and VTK frame list

## Current v0.3.0 limitation

CityLBM v0.3.0 reads, converts and records `k(m2/s2)`, but it does not inject synthetic turbulent inlet fluctuations. Any paper claim must state whether the validation used this v0.3.0 metadata-only k chain or a later turbulent inflow implementation.
