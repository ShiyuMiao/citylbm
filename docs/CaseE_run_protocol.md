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
- For AF files with `k(m2/s2)`, enable `Run Simulation / Synthetic Inlet` only when testing the experimental SEM-lite inlet.
  Record `STG Scale`/synthetic scale, `STG Corr Cells`/correlation cells, and the generated `case_metadata.json` fields `SyntheticTurbulentInletRequested`
  and `SyntheticTurbulentInletInjected`.
- Do not compare a single early VTK frame as a final result.
- CityLBM v0.3.0 validation runs must use an explicit external FluidX3D source path in `Run Simulation / FX3D`.
  The legacy bundled v0.5.0 fallback is disabled for controlled validation because it is not the baseline.

## Required checks before accepting a run

- Generated `setup.cpp` contains `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]` and `profile_origin_z_m`.
- If SEM-lite is enabled, generated `setup.cpp` also contains `syntheticTurbulentInlet`, `applySyntheticTurbulentInlet`
  and `citylbm_stg_*` constants.
- The generated `validation_protocol_audit` must explicitly record `native_fluidx3d_baseline`, `boundary_conditions`,
  `lbm_stability_scaling`, `wind_direction_sign`, `probe_projection`, `normalization_basis` and `systematic_bias_gate`.
  Treat these items as paper-blocking until their run evidence is archived.
- `domain_origin.json` exists in both case root and output directory.
- `case_metadata.json` exists in both case root and output directory.
- `validation_protocol_audit.json` and `validation_protocol_audit.md` exist in both case root and output directory.
  Treat any `risk` or `fail` item as a blocker for paper-grade validation claims until resolved or explicitly justified.
- VTK files are newly generated for the current run directory, not copied from older experiments.
- Post-processing reads the final averaged velocity field, not an initial transient.
  In `Read VTK`, set `Average Last N > 0` and record the actual averaged source time steps printed in the Info output.
- Measurement interpolation uses the official `ac + N` points and records failed or out-of-domain probes.
- The probe audit table must contain official point number, original coordinate, CFD interpolation cell, interpolation
  distance, compared velocity component and failure flag.
- In `Data Probe`, connect `Uref=3.928296` and `Wind Direction=(0,-1,0)`, then archive the appended outputs
  `Speed Ratio`, `Streamwise Ratio`, `Nearest Distance` and `Audit CSV`. These outputs are diagnostic only:
  `Uref` is used for validation ratios and must not be used to replace `AF_caseE.csv`.
- A paired native FluidX3D baseline must use the same `setup.cpp` physics choices, grid, VTK averaging window and probe
  extraction before any CityLBM-vs-AIJ error is attributed to the Grasshopper integration layer.
- `case_metadata.json` must be archived with the run. It records the boundary-condition summary, expected VTK frame count,
  time-averaging requirement, and known protocol risks.
- `native_fluidx3d_baseline_manifest.json` and `.md` must be archived. This manifest lists the exact generated
  `setup.cpp`, `defines.hpp`, `buildings.stl`, metadata files, shared run settings and paired evidence required for a
  native FluidX3D baseline, including SHA256 hashes for the generated source/metadata files. Treat the manifest gate
  `required_before_paper_grade_accuracy_claim` as blocking until the native baseline and CityLBM-driven run are compared
  with the same VTK averaging and probe audit table.

## Metrics to report

- Valid point count and failed point count
- MAE and RMSE for normalized speed ratio
- Bias and bias ratio
- R2
- Regression slope and intercept
- Maximum absolute error
- Grid spacing, steps, averaging window and VTK frame list
- Mean probe distance and maximum probe distance
- Native FluidX3D baseline run id or archive path
- Protocol gate from `validation_protocol_audit.json`
- Systematic bias flag. If mean bias remains around `-0.20` to `-0.35` speed-ratio units, do not tune parameters first;
  audit inlet turbulence, boundary treatment, wind-direction sign, probe projection and Uref normalization.

## Current v0.3.0 limitation

CityLBM v0.3.0 reads, converts and records `k(m2/s2)`. It also provides an optional experimental SEM-lite inlet that converts isotropic `k` to bounded synthetic-eddy velocity perturbations using `sigma=sqrt(2k/3)`, with inlet refresh controlled by `SyntheticTurbulenceUpdateInterval`. This is a software-level improvement over the former metadata-only `k` chain, but it is not a full digital-filter, precursor/recycling, or Reynolds-stress turbulent inflow because the AF table does not provide Reynolds-stress tensors, turbulent length scales or a precursor field. Any paper claim must state whether the validation used metadata-only inflow or SEM-lite inflow.

The current boundary conditions are also a simplified FluidX3D `TYPE_E` setup: velocity-profile inlet, pressure/free-outflow outlet approximation, lateral/top `TYPE_E`, and no-slip ground/buildings. This must be treated as a protocol risk until compared with the AIJ wind-tunnel boundary setup or replaced by a stronger inlet/outlet treatment.
