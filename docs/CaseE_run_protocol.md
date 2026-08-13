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
- For AF files with `k(m2/s2)`, enable `Run Simulation / Synthetic Inlet` only when testing the experimental STG-lite inlet.
  Record `STG Scale`/synthetic scale, `STG Corr Cells`/correlation cells, `STG Update`/pattern-update interval, `STG Max Frac`/amplitude cap,
  and the generated `case_metadata.json` fields `SyntheticTurbulentInletRequested` and `SyntheticTurbulentInletInjected`.
- Do not compare a single early VTK frame as a final result.
- CityLBM v0.3.0 validation runs must use an explicit external FluidX3D source path in `Run Simulation / FX3D`.
  The legacy bundled v0.5.0 fallback is disabled for controlled validation because it is not the baseline.

## Required checks before accepting a run

- Generated `setup.cpp` contains `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]` and `profile_origin_z_m`.
- If STG-lite is enabled, generated `setup.cpp` also contains `syntheticTurbulentInlet`, `applySyntheticTurbulentInlet`
  and `citylbm_stg_*` constants.
- The generated `validation_protocol_audit` must explicitly record `native_fluidx3d_baseline`, `boundary_conditions`,
  `lbm_stability_scaling`, `wind_direction_sign`, `probe_projection`, `normalization_basis` and `systematic_bias_gate`.
  Treat these items as paper-blocking until their run evidence is archived.
- `domain_origin.json` exists in both case root and output directory.
- `case_metadata.json` exists in both case root and output directory.
  Archive `BoundaryProtocolAudit` from this file: inlet/outlet/lateral/top faces, clearances in meters and H units,
  boundary protocol gate, and the simplified `TYPE_E`/`TYPE_S` boundary-type record.
- `validation_protocol_audit.json` and `validation_protocol_audit.md` exist in both case root and output directory.
  Treat any `risk` or `fail` item as a blocker for paper-grade validation claims until resolved or explicitly justified.
- VTK files are newly generated for the current run directory, not copied from older experiments.
- Post-processing reads the final averaged velocity field, not an initial transient.
  In `Read VTK`, set `Average Last N > 0` and archive the `Averaging Audit` JSON output.
  This JSON records the actual averaged frame count, source time steps, mean speed, mean/max pointwise speed standard
  deviation and mean/max relative fluctuation.
  A short window with large residual fluctuation is diagnostic only and must not be treated as paper-grade time averaging.
- Measurement interpolation uses the official `ac + N` points and records failed or out-of-domain probes.
- The probe audit table must contain official point number, original coordinate, interpolation distance,
  compared velocity component, compared value, wind-vector components, `wind_direction_valid`, `normalization_valid`,
  tolerance, out-of-tolerance flag and failure flag.
- In `Data Probe`, connect `Uref=3.928296`, `Wind Direction=(0,-1,0)`, `Probe IDs` from the official `RS_caseE.csv`
  point-number field, `Tolerance` from the run protocol, and `Compared Component`.
  Use `speed_ratio` when comparing with AIJ velocity-ratio magnitudes; use `streamwise_ratio` only if the validation
  table is explicitly defined as along-wind signed velocity. Archive the appended outputs `Speed Ratio`,
  `Streamwise Ratio`, `Nearest Distance`, `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`.
  These outputs are diagnostic only: `Uref` is used for validation ratios and must not be used to replace `AF_caseE.csv`.
- A paired native FluidX3D baseline must use the same `setup.cpp` physics choices, grid, VTK averaging window and probe
  extraction before any CityLBM-vs-AIJ error is attributed to the Grasshopper integration layer.
- `case_metadata.json` must be archived with the run. It records the boundary-condition summary, expected VTK frame count,
  time-averaging requirement, and known protocol risks.
- `native_fluidx3d_baseline_manifest.json` and `.md` must be archived. This manifest lists the exact generated
  `setup.cpp`, `defines.hpp`, `buildings.stl`, metadata files, shared run settings and paired evidence required for a
  native FluidX3D baseline, including SHA256 hashes for the generated source/metadata files. Treat the manifest gate
  `required_before_paper_grade_accuracy_claim` as blocking until the native baseline and CityLBM-driven run are compared
  with the same VTK averaging and probe audit table.
- Convert the `Data Probe` audit table and official `RS_caseE.csv` subset into a standard metrics row:

```powershell
python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS_caseE.csv> --metadata <case_metadata.json> --read-vtk-audit <read_vtk_averaging_audit.json> --case ac --wind-direction N --u-ref 3.928296 --z-ref 15.9 --out <validation_metrics.csv> --comparison-out <probe_comparison.csv>
```

- Run the machine gate after postprocessing:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseE --software citylbm --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --out <run_dir>\validation_gate_report.json
```

  The gate must pass before Case E is described as paper-grade validation. A failed gate means the run remains
  diagnostic, even if Rhino/Grasshopper visualization and screenshots are complete.

## Metrics to report

- Valid point count and failed point count
- MAE and RMSE for normalized speed ratio
- Bias and bias ratio
- R2
- Regression slope and intercept
- Maximum absolute error
- Grid spacing, steps, averaging window and VTK frame list
- Mean speed, mean/max pointwise speed standard deviation and mean/max relative fluctuation from the averaged VTK field
- Inlet/outlet/lateral/top boundary faces and upstream/downstream/lateral/top clearances in building-height units
- Mean probe distance and maximum probe distance
- Native FluidX3D baseline run id or archive path
- Empty-tunnel `U/k` preservation gate, `empty_tunnel_U_bias_ratio`, `empty_tunnel_k_bias_ratio`
- Native baseline gate and `validation_gate_report.json`
- Protocol gate from `validation_protocol_audit.json`
- Systematic bias flag. If mean bias remains around `-0.20` to `-0.35` speed-ratio units, do not tune parameters first;
  audit inlet turbulence, boundary treatment, wind-direction sign, probe projection and Uref normalization.

## Current v0.3.0 limitation

CityLBM v0.3.0 reads, converts and records `k(m2/s2)`. It also provides an optional experimental STG-lite inlet that converts isotropic `k` to bounded deterministic spectral velocity perturbations using `sigma=sqrt(2k/3)`, with inlet refresh controlled by `SyntheticTurbulenceUpdateInterval`. This is a software-level improvement over the former metadata-only `k` chain and the earlier sparse-eddy diagnostic pattern, but it is not a full digital-filter, precursor/recycling, or Reynolds-stress turbulent inflow because the AF table does not provide Reynolds-stress tensors, turbulent length scales or a precursor field. Any paper claim must state whether the validation used metadata-only inflow or STG-lite inflow.

The current boundary conditions are also a simplified FluidX3D `TYPE_E` setup: velocity-profile inlet, pressure/free-outflow outlet approximation, lateral/top `TYPE_E`, and no-slip ground/buildings. This must be treated as a protocol risk until compared with the AIJ wind-tunnel boundary setup or replaced by a stronger inlet/outlet treatment.
