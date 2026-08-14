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
   Run `scripts/audit_boundary_protocol.py` or the full chain with `--boundary-evidence <boundary_evidence.json>`.
   The evidence JSON must explicitly document `aij_case`, `wind_direction`, `boundary_equivalence_basis`,
   `inlet_boundary`, `outlet_boundary`, `lateral_boundary`, `top_boundary`, `ground_wall_treatment`,
   `roughness_treatment`, `floor_roughness_source`, `blockage_source`, `fetch_clearance_source`,
   `inlet_fetch_clearance_h`, `downstream_clearance_h`, `min_lateral_clearance_h`, `top_clearance_h`,
   `outlet_reflection_check` and `side_top_boundary_check`, with `boundary_evidence_gate=pass`. The equivalence basis
   must use an archived tag such as `aij_verified`, `wind_tunnel_protocol_matched`, `empty_tunnel_passed`,
   `validated_boundary_model`, `precursor_boundary` or `recycling_boundary`. Missing fields, unsupported equivalence
   basis or clearance below the configured H thresholds keep the boundary gate diagnostic/fail.

5. Inlet distribution-consistency gate.
   If the inlet turbulence is generated from `k`, archive whether the implementation reconstructs FluidX3D distribution
   functions or only refreshes macroscopic velocity fields. CityLBM v0.3.0 STG-lite is velocity-field-only; it is
   normalized to the isotropic component RMS target `sigma=sqrt(2k/3)`, but remains diagnostic by default. The machine
   gate only accepts it with the explicit `--allow-velocity-only-inlet` diagnostic override after an empty-tunnel run
   proves downstream `U/k` preservation. Paper-grade promotion should use a validated DFM/SEM/precursor/recycling inlet
   or another documented distribution-consistent treatment.
   In addition to RMS/k preservation, run `scripts/audit_inlet_correlation_from_vtk.py` on the same final-window VTK
   frames. The correlation audit records streamwise fluctuation variance, signed temporal lag-1 correlation, temporal
   lag-1 absolute correlation for diagnosis, and adjacent spatial correlation; a missing or failing audit means the
   inlet remains diagnostic even when the AF k magnitude is approximately preserved.

6. Time-averaging gate.
   Do not report a single instantaneous VTK frame as validation. Archive post-spinup probe time means and, when VTK is
   used for visualization, at least 10 post-spinup VTK frames or an explicit averaged VTK field with the source frame
   list. For CityLBM post-processing, save the `Read VTK` `Averaging Audit` JSON output and pass it into the metrics
   builder. CityLBM v0.3.0 defaults to `TimeSteps=10000` and `SaveInterval=500` so new cases produce about 20 VTK
   frames; shorter runs must be labelled smoke tests. The audit must show `selected_last_window=true`,
   `source_steps_strictly_increasing=true`, `source_step_spacing_uniform=true`, and
   `source_last_time_step=latest_available_time_step`. The same gate also requires `mean_speed_stddev_ratio <= 0.05`
   and `max_speed_stddev_ratio <= 0.20` from the Read VTK averaging audit, native-run audit, or inlet-profile audit
   unless a stricter case-specific stationarity criterion is documented.

7. Probe audit gate.
   Probe extraction must record official point IDs, coordinates, selected velocity component, `Uref`, nearest VTK/probe
   distance, tolerance, failure status, valid count and failed count. In CityLBM this is produced by `Data Probe`
   outputs `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`. The `Search Radius` input must be
  archived because v0.3.0 applies it as the actual interpolation-neighbor distance filter. The audit CSV must also
  record wind-vector components, `wind_direction_valid` and `normalization_valid` so speed-ratio and streamwise-ratio
  comparisons remain traceable. Native VTK probe extraction must also record VTK origin, spacing, dimensions, source
  time steps, source file hashes and nearest-grid coordinates so coordinate-frame and projection errors can be audited
  from the same table. The validation metrics must record `compared_component_consistency_gate`,
   `compared_component_unique_values` and `official_coordinate_delta_count`; every valid probe must use one explicit
   component and must have an official coordinate-delta check. Native FluidX3D runs that bypass Grasshopper must use
   `scripts/probe_vtk_points.py` to emit the same Data-Probe-compatible audit CSV before metrics are built. Use
   `--interpolation trilinear` for structured VTK validation and treat `nearest_distance` as a coverage/tolerance audit,
   not as the velocity sampling method.

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
  CityLBM v0.3.0 generates `nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx` and does not silently clamp `tau` to 0.55.
  A near-0.5 `tau` is a stability risk to document and resolve with solver evidence, not a reason to inflate viscosity
  inside the generator.
- Domain extents in `H`: upstream, downstream, lateral and top clearance.
- Approximate frontal blockage ratio, approximate plan blockage ratio and blockage gate.
- Boundary mode and boundary-source justification.
- `boundary_protocol_audit.json`, including `boundary_missing_evidence_fields`, `boundary_equivalence_basis`,
  `boundary_equivalence_supported`, `clearance_numeric_gate` and `clearance_numeric_gate_reasons`; this file must be
  generated from metadata plus an explicit AIJ boundary evidence JSON before paper-grade promotion.
- `TYPE_E` boundary velocity initialization policy. CityLBM v0.3.0 generated cases initialize outlet, lateral and top
  `TYPE_E` nodes from the mean wind profile before device upload to avoid zero-speed boundary damping; archive the
  generated `setup.cpp` evidence for native and CityLBM parity runs.
- Wall/roughness treatment: no-slip, rough-wall function, precursor/recycling, roughness blocks, or other documented
  approach.
- Inlet turbulence method: off, STG-lite, synthetic-eddy, digital-filter, recycling-rescaling or precursor.
- Inlet distribution treatment: macroscopic velocity only, equilibrium/distribution reconstruction, precursor field, or
  other archived method.
- STG correlation-length evidence source: record `STG Length Source`,
  `SyntheticTurbulentInletLengthScaleSource` and `SyntheticTurbulentInletLengthScaleGate`. Empty or user-selected
  lattice-cell values are diagnostic only; paper-grade promotion requires archived AIJ/official, precursor/recycling,
  digital-filter, synthetic-eddy, SEM/DFM or validated length-scale-model evidence.
- Inlet `U` and `k` preservation metrics from the empty tunnel.
- Inlet/empty-tunnel profile-audit JSON and CSV from real post-spinup VTK frames, including the selected plane, all
  available VTK steps, selected source VTK steps, `selected_last_window`, `source_steps_strictly_increasing`,
  `source_step_spacing_uniform`, `time_averaging_gate_reasons`, `negative_streamwise_fraction`,
  `inlet_streamwise_direction_gate`, `U_MAE_ratio`, `U_RMSE_ratio`, `U_bias_ratio`, `k_MAE_ratio`, `k_RMSE_ratio`,
  `k_bias_ratio`, and the
  `inlet_profile_gate`.
- Inlet correlation-audit JSON from the same final-window VTK frames, including `inlet_correlation_gate`,
  `temporal_lag1_mean_correlation`, `temporal_lag1_abs_mean_correlation`, `spatial_adjacent_mean_correlation` and
  `mean_streamwise_fluctuation_variance`.
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
python scripts\audit_native_run.py <run_dir> --metadata <case_metadata.json> --solver-log <solver.log> --average-last-n 10 --out <native_run_audit.json>

python scripts\audit_inlet_profile_from_vtk.py <run_dir>\output --af-csv <AF_caseA.csv> --metadata <case_metadata.json> --wind-direction 1,0,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_profile_audit.json --out-csv <run_dir>\inlet_profile_audit.csv

python scripts\audit_inlet_correlation_from_vtk.py <run_dir>\output --metadata <case_metadata.json> --wind-direction 1,0,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_correlation_audit.json

python scripts\probe_vtk_points.py <run_dir>\output --official <RS-caseA.csv> --case CaseA --wind-direction-label <direction> --wind-direction 1,0,0 --u-ref <Uref> --compared-component speed_ratio --interpolation trilinear --tolerance <probe_tolerance_m> --average-last-n 10 --out <probe_audit.csv>

python scripts\audit_component_sensitivity.py --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --case CaseA --wind-direction <direction> --selected-component speed_ratio --out-json <run_dir>\component_sensitivity_audit.json --out-csv <run_dir>\component_sensitivity_audit.csv

python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --metadata <case_metadata.json> --read-vtk-audit <native_run_audit.json> --inlet-profile-audit <run_dir>\inlet_profile_audit.json --inlet-correlation-audit <run_dir>\inlet_correlation_audit.json --component-sensitivity-audit <run_dir>\component_sensitivity_audit.json --case CaseA --wind-direction <direction> --u-ref <Uref> --out <validation_metrics.csv>
```

Before the final gate, archive the AIJ boundary evidence as JSON and audit it:

```powershell
python scripts\audit_boundary_protocol.py <run_dir> --metadata <case_metadata.json> --evidence <boundary_evidence.json> --out <run_dir>\boundary_protocol_audit.json
```

For a native FluidX3D run that bypasses Grasshopper, the same evidence chain can be generated with one command:

```powershell
python scripts\run_native_validation_chain.py <run_dir> --official <RS-caseA.csv> --af-csv <AF_caseA.csv> --metadata <case_metadata.json> --boundary-evidence <boundary_evidence.json> --solver-log <solver.log> --case CaseA --wind-direction-label <direction> --wind-vector 1,0,0 --u-ref <Uref> --software native-fluidx3d --average-last-n 10 --min-avg-frames 10 --compared-component speed_ratio --interpolation trilinear --probe-tolerance <probe_tolerance_m>
```

The command writes `validation_chain_manifest.json`, `native_run_audit.json`, `inlet_profile_audit.json/.csv`,
`inlet_correlation_audit.json`, `boundary_protocol_audit.json`, `probe_audit.csv`,
`component_sensitivity_audit.json/.csv`, `validation_metrics.csv`, `probe_comparison.csv` and
`validation_gate_report.json` under
`<run_dir>\validation_chain`. It does not run FluidX3D; it only audits newly generated VTK frames and solver evidence
that already exist in the run directory.

When `--mean-speed-stddev-ratio` and `--max-speed-stddev-ratio` are omitted, `audit_native_run.py` deterministically
samples up to 20,000 points from the selected final VTK frames and computes these stability ratios from the real
velocity time series. Explicit CLI ratios can still be used when a stricter full-field or probe-specific averaging
analysis has already been archived.
The validation metrics row must use the actual audit `averaged_frame_count` and `source_time_steps`, not only the
requested `--average-last-n` value. A run with four real final VTK frames remains four-frame diagnostic evidence even if
the requested averaging window was ten frames.

For a CityLBM-driven parity run, change `--software citylbm` and keep the same metrics/probe schema. A passing paper-grade
record must archive `validation_gate_report.json` and the metrics row must include `empty_tunnel_gate=pass`,
`native_baseline_gate=pass`, `lbm_stability_gate=solver_log_no_stability_warnings`,
`solver_stability_warnings=none`, `normalization_valid=true`, `wind_direction_valid=true`, at least 10 averaged source frames,
`inlet_profile_gate=pass`, zero failed probes, bounded mean-velocity bias/RMSE, and reported `k` bias/RMSE. If the gate returns `FAIL`, the run is
diagnostic only even if selected plots look reasonable.
The JSON report also includes `diagnostic_priority`, which must be followed in order before changing physics parameters:
first close coordinate/component/Uref/probe issues and the component/Uref sensitivity audit, then final-window time
averaging, then AF `U/k` preservation, then turbulent-inlet method, length scale and correlation evidence, then
boundary/roughness/blockage, and only then interpret the remaining systematic bias as a physics/protocol problem.
The inlet `U/k` audit follows the same final-window rule as the VTK/probe average: short, non-final or irregular
source steps fail before the result can be interpreted as solver accuracy.
When a native FluidX3D run has no Grasshopper Read VTK audit, `scripts/validation_metrics_from_probe_audit.py` uses the
inlet-profile audit as the authoritative source for `available_frame_count`, selected source time steps, last-window
selection, source-step monotonicity, uniform-spacing fields and selected-plane speed-stability ratios in the standard
metrics row.
It also fails when more than 5% of sampled inlet velocities project opposite to the declared wind vector, which catches
wind-sign and streamwise-component mistakes before AF/profile or probe errors are interpreted.
The command intentionally omits `--allow-velocity-only-inlet`; add that flag only for explicitly labelled diagnostic
STG-lite sensitivity runs, not for the native FluidX3D baseline or a paper-grade CityLBM equivalence claim. Even when
that diagnostic override is used, `validation_gate.py` still fails the separate `paper_grade_inlet_method` gate until
the inlet treatment is distribution-consistent, digital-filter/SEM/DFM, precursor or recycling based and the final-window
U/k preservation evidence passes.
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
