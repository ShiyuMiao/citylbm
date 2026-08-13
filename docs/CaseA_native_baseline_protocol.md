# AIJ Case A Native FluidX3D Baseline Protocol

This protocol is the promotion gate before CityLBM settings are copied into the Rhino/Grasshopper workflow and before
AIJ Case E is treated as a paper-grade validation experiment.

## Scope

- Case: AIJ Case A isolated building.
- Purpose: establish a native FluidX3D reference with controlled inlet, boundary, coordinate, averaging and probe
  extraction settings.
- Evidence status in this repository: protocol-ready, not newly run.
- Required platform: native FluidX3D source tree with `FluidX3D.sln` or `makefile`, not the placeholder
  `src/Resources/FluidX3D/FluidX3D.source.zip`.
- For CityLBM v0.3.0 validation runs, the `Run Simulation / FX3D` input must be explicitly set. Mode 1/2/3 reject
  auto-detected paths. The path must contain `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`, plus `src/setup.cpp`,
  `src/defines.hpp`, `src/lbm.hpp` and `src/lbm.cpp`.

## Inputs

- Official inflow table: `AF_caseA.csv`.
- Official measurement table: `RS-caseA.csv`.
- Geometry: model-scale block, `B=0.08 m`, `H=0.16 m`, `D=0.08 m`.
- Coordinates: `+X` is streamwise wind direction, `Y=0` is the vertical center plane, `Z=0` is ground.
- Reference speed: use the official Case A reference velocity consistently in both native FluidX3D and CityLBM
  postprocessing. Do not change `Uref` to fit the error.

## Native Baseline Gates

1. Empty-tunnel gate.
   The empty-tunnel run must preserve both mean velocity and turbulent kinetic energy before any building run is
   promoted. Record `U_MAE`, `U_RMSE`, `U_bias`, `k_MAE`, `k_RMSE`, `k_bias`, the post-spinup sample count and the
   inlet-turbulence method. Generate these fields from real `u-*.vtk` frames with
   `scripts/audit_inlet_profile_from_vtk.py`; do not hand-enter them without an archived profile-audit JSON.

2. Building Case A gate.
   Run the building case only after the empty-tunnel gate passes or after the protocol is explicitly marked as
   diagnostic. Use the same FluidX3D source commit, `setup.cpp`, `defines.hpp`, grid spacing, boundary mode,
   turbulence method and averaging rules.

3. Wall and roughness gate.
   Archive whether the wind-tunnel floor and roughness blocks are represented as no-slip voxels, rough-wall functions,
   precursor/recycling development, or another documented treatment. In CityLBM v0.3.0 `RoughnessLength` shapes analytic
   mean-profile generation only; ground/buildings remain `TYPE_S` no-slip, so this gate must be closed by empty-tunnel
   `U/k` preservation before Case A/Case E is promoted.

4. Boundary blockage gate.
   Archive domain dimensions, maximum building height, upstream/downstream/lateral/top clearance in `H`, approximate
   frontal blockage ratio and approximate plan blockage ratio. CityLBM v0.3.0 writes these fields in
   `BoundaryProtocolAudit`. The ratios are axis-aligned screening diagnostics; compare them with the official AIJ
   wind-tunnel blockage protocol before paper-grade promotion.

5. Inlet distribution-consistency gate.
   If the inlet turbulence is generated from `k`, archive whether the implementation reconstructs FluidX3D distribution
   functions or only refreshes macroscopic velocity fields. CityLBM v0.3.0 STG-lite is velocity-field-only; it is
   normalized to the isotropic component RMS target `sigma=sqrt(2k/3)`, but remains diagnostic by default. The machine
   gate only accepts it with the explicit `--allow-velocity-only-inlet` diagnostic override after an empty-tunnel run
   proves downstream `U/k` preservation. Paper-grade promotion should use a validated DFM/SEM/precursor/recycling inlet
   or another documented distribution-consistent treatment.

6. Time-averaging gate.
   Do not report a single instantaneous VTK frame as validation. Archive post-spinup probe time means and, when VTK is
   used for visualization, at least 10 post-spinup VTK frames or an explicit averaged VTK field with the source frame
   list. For CityLBM post-processing, save the `Read VTK` `Averaging Audit` JSON output and pass it into the metrics
   builder. CityLBM v0.3.0 defaults to `TimeSteps=10000` and `SaveInterval=500` so new cases produce about 20 VTK
   frames; shorter runs must be labelled smoke tests. The audit must show `selected_last_window=true`,
   `source_steps_strictly_increasing=true`, `source_step_spacing_uniform=true`, and
   `source_last_time_step=latest_available_time_step`. The same gate also requires `mean_speed_stddev_ratio <= 0.05`
   and `max_speed_stddev_ratio <= 0.20` from the Read VTK averaging audit unless a stricter case-specific stationarity
   criterion is documented.

7. Probe audit gate.
   Probe extraction must record official point IDs, coordinates, selected velocity component, `Uref`, nearest VTK/probe
   distance, tolerance, failure status, valid count and failed count. In CityLBM this is produced by `Data Probe`
   outputs `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`. The `Search Radius` input must be
   archived because v0.3.0 applies it as the actual interpolation-neighbor distance filter. The audit CSV must also
   record wind-vector components, `wind_direction_valid` and `normalization_valid` so speed-ratio and streamwise-ratio
   comparisons remain traceable. The validation metrics must record `compared_component_consistency_gate`,
   `compared_component_unique_values` and `official_coordinate_delta_count`; every valid probe must use one explicit
   component and must have an official coordinate-delta check.

8. Promotion gate.
   CityLBM may inherit native FluidX3D settings only after native Case A has a passing or explicitly bounded diagnostic
   record. If native FluidX3D underpredicts mean speed or `k`, do not tune CityLBM to hide the discrepancy; fix or
   document the native physics first.

## Minimum Settings To Archive

- FluidX3D source path and source hash or commit.
- CityLBM `native_fluidx3d_baseline_manifest.json` with `NativeFluidX3DPathExplicitlyProvided=true` and a passing
  `NativeFluidX3DSourceValidation` record.
- `setup.cpp`, `defines.hpp`, `buildings.stl`, run log and postprocess script hashes.
- `dx`, lattice dimensions, `tau`, target Reynolds number, velocity set and LES/subgrid settings.
- LBM stability evidence: target maximum lattice velocity, estimated maximum Mach number, `tau`, `nu_lbm`, physical
  viscosity, Reynolds number, velocity set, LES/subgrid model and solver-log stability warning status. The machine
  gate now fails this block unless the runtime metrics row records a passing stability gate such as
  `solver_log_no_stability_warnings`.
- Domain extents in `H`: upstream, downstream, lateral and top clearance.
- Approximate frontal blockage ratio, approximate plan blockage ratio and blockage gate.
- Boundary mode and boundary-source justification.
- `TYPE_E` boundary velocity initialization policy. CityLBM v0.3.0 generated cases initialize outlet, lateral and top
  `TYPE_E` nodes from the mean wind profile before device upload to avoid zero-speed boundary damping; archive the
  generated `setup.cpp` evidence for native and CityLBM parity runs.
- Wall/roughness treatment: no-slip, rough-wall function, precursor/recycling, roughness blocks, or other documented
  approach.
- Inlet turbulence method: off, STG-lite, synthetic-eddy, digital-filter, recycling-rescaling or precursor.
- Inlet distribution treatment: macroscopic velocity only, equilibrium/distribution reconstruction, precursor field, or
  other archived method.
- Inlet `U` and `k` preservation metrics from the empty tunnel.
- Inlet/empty-tunnel profile-audit JSON and CSV from real post-spinup VTK frames, including the selected plane, source
  VTK steps, `U_MAE_ratio`, `U_bias_ratio`, `k_MAE_ratio`, `k_bias_ratio`, and the `inlet_profile_gate`.
- Building probe metrics: `U_MAE_ratio`, `U_RMSE_ratio`, `U_bias_ratio`, `U_R2`, slope, intercept, max absolute error,
  `U_best_fit_scale_to_exp`, scaled RMSE and `bias_diagnosis`.
- Probe mapping diagnostics: valid/failed count, mean/max probe distance, tolerance, compared-component consistency and
  coordinate-delta coverage across all valid probes.

## Machine Gate

After every native FluidX3D or CityLBM-driven Case A run, execute the repository gate before using metrics in a paper:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseA --software native-fluidx3d --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --expected-compared-component speed_ratio --expected-uref <Uref> --expected-wind-vector 1,0,0 --max-mean-speed-stddev-ratio 0.05 --max-point-speed-stddev-ratio 0.20 --out <run_dir>\validation_gate_report.json
```

If metrics are produced from Grasshopper `Data Probe`, build the metrics row first:

```powershell
python scripts\audit_native_run.py <run_dir> --metadata <case_metadata.json> --solver-log <solver.log> --average-last-n 10 --mean-speed-stddev-ratio <ratio> --max-speed-stddev-ratio <ratio> --out <native_run_audit.json>

python scripts\audit_inlet_profile_from_vtk.py <run_dir>\output --af-csv <AF_caseA.csv> --metadata <case_metadata.json> --wind-direction 1,0,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_profile_audit.json --out-csv <run_dir>\inlet_profile_audit.csv

python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --metadata <case_metadata.json> --read-vtk-audit <native_run_audit.json> --inlet-profile-audit <run_dir>\inlet_profile_audit.json --case CaseA --wind-direction <direction> --u-ref <Uref> --out <validation_metrics.csv>
```

For a CityLBM-driven parity run, change `--software citylbm` and keep the same metrics/probe schema. A passing paper-grade
record must archive `validation_gate_report.json` and the metrics row must include `empty_tunnel_gate=pass`,
`native_baseline_gate=pass`, `lbm_stability_gate=solver_log_no_stability_warnings`,
`solver_stability_warnings=none`, `normalization_valid=true`, `wind_direction_valid=true`, at least 10 averaged source frames,
`inlet_profile_gate=pass`, zero failed probes, bounded mean-velocity bias/RMSE, and reported `k` bias. If the gate returns `FAIL`, the run is
diagnostic only even if selected plots look reasonable.
The command intentionally omits `--allow-velocity-only-inlet`; add that flag only for explicitly labelled diagnostic
STG-lite sensitivity runs, not for the native FluidX3D baseline or a paper-grade CityLBM equivalence claim.
If `bias_diagnosis` reports `scale_like_error`, audit `Uref`, SI/LBM velocity conversion and compared component before
changing inlet or boundary parameters. If the scaled error remains large, prioritize boundary, roughness and inlet
physics.

## Current Blockers

- The repository-embedded `src/Resources/FluidX3D/FluidX3D.source.zip` is a placeholder and cannot establish a native
  source baseline.
- The executable `bin/FluidX3D.exe` can run on the local GPU, but its banner identifies it as a CityLBM runtime solver.
  Use it only as a smoke-test executable unless its source, `setup.cpp` and build recipe are archived.
- Historical Case A experiments in the old portable validation folder are useful diagnostic evidence, but they are not
  new v0.3.0 runs and must not be presented as fresh Case A or Case E results.

## Case E Dependency

Case E starts only after Case A closes the native-vs-CityLBM equivalence gate. The Case E SCI chain must then reuse the
same source-control discipline: official AF/RS tables, `WP=3` CustomTable, `k` audit, post-spinup averaging, official
probe IDs and `Data Probe` validation status.
