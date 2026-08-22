# AIJ Case A Native FluidX3D Baseline Protocol

This protocol is the promotion gate before CityLBM settings are copied into the Rhino/Grasshopper workflow and before
AIJ Case E is treated as a paper-grade validation experiment.

## Scope

- Case: AIJ Case A isolated building.
- Purpose: establish a native FluidX3D reference with controlled inlet, boundary, coordinate, averaging and probe
  extraction settings.
- Evidence status in this repository: protocol-ready with a newly generated strict preflight record; no new CFD solver
  result is archived.
- Required platform: native FluidX3D source tree with `FluidX3D.sln` or `makefile`, not the placeholder
  `src/Resources/FluidX3D/FluidX3D.source.zip`.
- For CityLBM v0.3.0 validation runs, the `Run Simulation / FX3D` input must be explicitly set. Mode 1/2/3 reject
  auto-detected paths. The path must contain `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`, plus `src/setup.cpp`,
  `src/defines.hpp`, `src/lbm.hpp` and `src/lbm.cpp`.

## 2026-08-14 Strict Preflight Evidence

Evidence type: `newly_run_preflight`, not a CFD result. The strict wrapper generated fresh native FluidX3D Case A
empty-tunnel and building cases from the official AF/RS inputs, then stopped before launching FluidX3D because
paper-grade protocol gates remain open.

Command:

```powershell
.\run_native_casea_strict_gate.ps1 -Dx 0.006 -Tau 0.5003333333333333 -EmptyTimeSteps 30000 -EmptySpinupSteps 5000 -BuildingTimeSteps 60000 -BuildingSpinupSteps 10000 -SampleInterval 100 -InletDiagnosticInterval 100 -VtkSaveInterval 1000 -VtkSaveStartStep 10000 -TurbulenceMethod synthetic-eddy -SyntheticEddyCount 384 -BoundaryMode side_periodic_top_profile_e -RunBuildingIfEmptyPass -PreflightOnly -CaseTagPrefix native_casea_strict_20260814_preflight
```

Generated cases:

- Empty tunnel:
  `F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casea_v020_rerun_20260716\native_cases\AIJ_CaseA_native_casea_strict_20260814_preflight_empty_20260814_20260814`
- Building:
  `F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casea_v020_rerun_20260716\native_cases\AIJ_CaseA_native_casea_strict_20260814_preflight_building_20260814_20260814`

Generated configuration evidence:

- Grid: `547 x 280 x 160 = 24,505,600` cells.
- Official probe count: `186`.
- Building geometry: generated ideal Case A block from the protocol script, not an external STL import.
- Target Reynolds number: `ReH=24000.000000026626`.
- `dx=0.006 m`, `tau=0.5003333333333333`, `UrefLbm=0.1`.
- Turbulence method: `synthetic-eddy`, `SyntheticEddyCount=384`.
- CityLBM STG-lite equivalent: set `Run Simulation / STG Modes=384` for the strict diagnostic baseline when runtime
  allows; values below 32 are smoke-test-only and fail the generated-source inlet audit.
- Averaging request: building `TimeSteps=60000`, `SpinupSteps=10000`, `SampleInterval=100`; estimated post-spinup
  probe samples `501`.
- VTK request: `VtkSaveInterval=1000`, `VtkSaveStartStep=10000`; estimated post-spinup frames `51`.

Passed preflight checks include correlated turbulent inlet selection, official AF turbulence-amplitude usage,
Reynolds-number matching, device-side synthetic-eddy update consistency, no direct velocity overwrite conditioning,
time-average length, same-run VTK evidence request, VTK temporal coverage, coordinate/normalization metadata and
explicit `+X` streamwise comparison protocol.

Blocking checks:

- `wind_tunnel_boundary_equivalence_source`: no archived source/evidence yet proves that the generated FluidX3D
  boundary conditions are equivalent to the AIJ wind-tunnel protocol.
- `wind_tunnel_roughness_or_precursor_source`: no archived roughness-block layout, rough-wall calibration, passing
  empty-tunnel gate, precursor or recycling-rescaling evidence is available.

Decision: do not launch or promote the building run as paper-grade evidence until the boundary-equivalence and
roughness/precursor gates are closed. A diagnostic override may be used for software debugging, but its metrics must not
be migrated into CityLBM or reported as native FluidX3D accuracy.

## Inputs

- Official inflow table: `AF_caseA.csv`.
- Official measurement table: `RS-caseA.csv`.
- Geometry: model-scale block, `B=0.08 m`, `H=0.16 m`, `D=0.08 m`.
- Coordinates: `+X` is streamwise wind direction, `Y=0` is the vertical center plane, `Z=0` is ground.
- Reference speed: use the official Case A reference velocity consistently in both native FluidX3D and CityLBM
  postprocessing. Do not change `Uref` to fit the error.
- If a metrics or gate command supplies `--case` or `--wind-direction`, the official measurement CSV must contain the
  corresponding case/condition or wind/direction column and the filtered subset must be non-empty. A missing filter
  column is a protocol failure, not permission to compare against the full RS table.
- Component/Uref sensitivity checks must use normalized probe IDs, matching the final metrics join. Official IDs that
  become duplicates after lowercase alphanumeric normalization are invalid because they make the component diagnosis
  ambiguous.

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
   The machine gate reports this separately as `roughness_or_precursor`. A passing boundary-clearance/blockage audit is
   not enough: the run must also archive source-driven AIJ roughness geometry, a validated rough-wall treatment, or a
   passing empty-tunnel precursor/recycling equivalence record.

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
   `outlet_reflection_check` and `side_top_boundary_check`, with `boundary_evidence_gate=pass`. It must also provide
   `boundary_evidence_class` and at least one `boundary_evidence_files` entry that resolves to an archived support
   file. The equivalence basis must use an archived tag such as `aij_verified`, `wind_tunnel_protocol_matched`,
   `empty_tunnel_passed`, `validated_boundary_model`, `precursor_boundary` or `recycling_boundary`. Missing fields,
   unsupported equivalence basis, unsupported evidence class, missing support files or clearance below the configured H
   thresholds keep the boundary gate diagnostic/fail. The validation gate requires a generated
   `boundary_protocol_audit.json` with `boundary_protocol_gate=pass`, `boundary_equivalence_supported=true`,
    `boundary_evidence_class_supported=true`, `boundary_evidence_files_all_exist=true` and
   `boundary_evidence_files_all_hashed=true`. It also requires `boundary_condition_fields_supported=true` plus
   individual support booleans for inlet, outlet, lateral, top, ground-wall treatment, roughness treatment, floor
   roughness source, blockage source, fetch/clearance source, outlet-reflection check and side/top-boundary check.
   Run `scripts/audit_boundary_source.py` on the generated `setup.cpp` and archive `boundary_source_audit.json`. The
   final gate fails paper-grade `boundary_protocol` when source code still shows a simplified `TYPE_E` outlet/lateral/top
   box with `TYPE_S` no-slip ground/buildings and no non-reflecting, precursor/recycling or rough-wall evidence.
   `TYPE_E`/`TYPE_S` may be defined in included FluidX3D headers; the audit therefore uses their generated-source
   assignments as source evidence, but that only proves boundary implementation traceability, not wind-tunnel equivalence.
   Advanced boundary-source claims must come from comment-stripped generated C++ code:
   `boundary_source_advanced_code_evidence=true` and
   `advanced_boundary_evidence_uses_comment_stripped_code=true`. Comments, metadata labels and C++ string literals alone
   are not accepted; `advanced_boundary_token_only=true` keeps the boundary source diagnostic/failing.
   For the current simplified/profile `TYPE_E` boundary source, the audit must also report
   `has_type_e_velocity_initialization=true`, `has_type_e_velocity_initialization_guard=true`,
   `has_type_e_velocity_initialization_coordinates=true` and
   `has_type_e_velocity_initialization_velocity_write=true`. Profile-inlet runs must additionally report
   `has_profile_type_e_velocity_initialization=true`, proving the outlet/lateral/top `TYPE_E` nodes are initialized from
   `windProfile(z)` instead of keeping zero velocity after the boundary-return path.
   Token-like text in metadata or metrics is diagnostic context only. `validation_gate.py` uses the boundary protocol,
   boundary-source and roughness/precursor audit files as the admissible evidence; metrics-table boundary fields are not
   allowed to repair missing or incomplete audit fields.

5. Inlet distribution-consistency gate.
   If the inlet turbulence is generated from `k`, archive whether the implementation reconstructs FluidX3D distribution
   functions or only refreshes macroscopic velocity fields. CityLBM v0.3.0 STG-lite is velocity-field-only; it is
   normalized to the isotropic component RMS target `sigma=sqrt(2k/3)`, but remains diagnostic by default. The machine
   gate only accepts it with the explicit `--allow-velocity-only-inlet` diagnostic override after an empty-tunnel run
   proves downstream `U/k` preservation. Paper-grade promotion should use a validated DFM/SEM/precursor/recycling inlet
   or another documented distribution-consistent treatment.
  The source audit separately records whether STG-lite actually contains correlated-source features: `citylbm_stg_corr_cells`,
  spectral modes, `citylbm_stg_mode_count`, Taylor frozen-turbulence advection and transverse wave-vector projection. Passing those source checks
  shows the inlet is stronger than uncorrelated random perturbations, but it still does not make the inlet
   distribution-consistent.
   The source audit must also show `has_synthetic_inlet_refresh_with_current_time`, `has_update_interval_run_control` and
   `has_segmented_stg_run_loop`. These fields prove that `SyntheticTurbulenceUpdateInterval` actually limits the
   generated `lbm.run(steps_to_run)` loop and that STG-lite refreshes from the current solver time rather than existing
   only as metadata or an unused constant. `validation_gate.py` rejects STG-like inlet source evidence from stale audit
   JSON files that do not contain these run-loop fields.
   Inlet-correlation values are accepted only from the archived `inlet_correlation_audit.json` generated from the
   current final-window VTK files. Metrics-table fields such as temporal lag-1 correlation, spatial adjacent correlation
   or streamwise fluctuation variance are ignored context and cannot prove correlated turbulent inflow.
   Run `scripts/audit_inlet_source.py` on the generated `setup.cpp` before interpreting any VTK result. Archive
   `inlet_source_audit.json` with `setup_cpp_sha256`, `inlet_source_method_class`,
   `inlet_source_distribution_consistent` and `inlet_source_velocity_field_only`; `validation_gate.py` fails
   `paper_grade_inlet_method` when metadata claims a distribution-consistent inlet but the generated source only shows
   macroscopic velocity-field forcing. Metrics-table `inlet_source_*` fields are ignored context and cannot repair a
   missing or incomplete source audit.
   Distribution consistency is source-context sensitive: `audit_inlet_source.py` records generic
   `has_distribution_function_write` / `distribution_function_write_count`, but digital-filter or SEM/DFM claims require
   `has_inlet_distribution_reconstruction=true` and a positive `inlet_distribution_reconstruction_count`. Distribution
   tokens outside an inlet/`TYPE_E` reconstruction context are diagnostic only. Method names that appear only in comments
   or C++ string literals set `advanced_inlet_method_token_only=true` and cannot pass `paper_grade_inlet_method`.
   In addition to RMS/k preservation, run `scripts/audit_inlet_correlation_from_vtk.py` on the same final-window VTK
   frames. The correlation audit records streamwise fluctuation variance, signed temporal lag-1 correlation, temporal
   lag-1 absolute correlation for diagnosis, and adjacent spatial correlation; a missing or failing audit means the
   inlet remains diagnostic even when the AF k magnitude is approximately preserved.
   The final gate independently checks this audit rather than trusting a summary flag: the correlation source time steps
   must match the global averaged `source_time_steps`, the window must be the final uniformly spaced window, and the
   default thresholds require streamwise variance `>1e-12`, temporal lag-1 correlation `>=0.10` and spatial adjacent
   correlation `>=0.05`. The default audit also requires at least 100 sampled inlet-plane points and 100 adjacent
   spatial pairs; smaller sparse samples remain diagnostic even if their finite-correlation fractions are high.
   The metrics CSV may summarize `inlet_source_*` and `inlet_correlation_*` fields, but it is not accepted as a substitute
   for the archived source-audit JSON and VTK correlation-audit JSON.
   The final gate also reads inlet `U(z)`, `k(z)`, streamwise-direction and inlet-window pass/fail fields directly from
   `inlet_profile_audit.json`; copied `inlet_profile_*` fields in `validation_metrics.csv` are not accepted as source evidence.
   The audit must also report finite temporal and spatial correlation coverage fractions; a high mean correlation from
   only a sparse subset of non-degenerate samples is not enough for a paper-grade turbulent-inlet claim.
   The inlet `U/k` preservation gate follows the same final-window evidence rule as the global time-average gate:
   `inlet_profile_source_time_steps` must be archived from real VTK frames, match `inlet_profile_frame_count`, represent
   the last available uniformly spaced window, match the global runtime audit `source_time_steps` exactly, and carry
   `inlet_profile_time_averaging_gate=pass`. An `empty_tunnel_gate` or small `U/k` bias value without that same-window
   evidence remains diagnostic.

6. Time-averaging gate.
   Do not report a single instantaneous VTK frame as validation. Archive post-spinup probe time means and, when VTK is
   used for visualization, at least 40 post-spinup VTK frames or an explicit averaged VTK field with the source frame
   list. For CityLBM post-processing, save the `Read VTK` `Averaging Audit` JSON output and pass it into the metrics
   builder. CityLBM v0.3.0 defaults to `TimeSteps=40000` and `SaveInterval=1000` so new cases produce about 40 VTK
   frames; shorter runs must be labelled smoke tests. The audit must show `selected_last_window=true`,
   `source_steps_strictly_increasing=true`, `source_step_spacing_uniform=true`, and
   `source_last_time_step=latest_available_time_step`. It must also record `source_step_span`; v0.3.0 rejects a
   paper-grade time average unless the final averaged window covers at least `--min-avg-step-span` solver steps
   (`20000` by default). The same gate also requires `mean_speed_stddev_ratio <= 0.05` and
   `max_speed_stddev_ratio <= 0.20` from the Read VTK averaging audit or native-run audit unless a stricter
   case-specific stationarity criterion is documented. The machine gate only counts the archived runtime audit as the
   authoritative time-averaging source: sampled VTK stability statistics (`mean_speed_statistics_source=sampled_vtk` or
   equivalent) and archived `source_time_steps` must come from real VTK/audit frames; command-line or hand-entered speed
   standard-deviation ratios, `AverageLastN`, `--average-last-n` and
   `ExpectedVtkFrameCount` are request or estimate fields and cannot pass the paper-grade time gate by themselves.
   The native-run audit must also record `requested_time_steps`, `requested_vtk_save_interval`,
   `requested_vtk_save_start_step`, `requested_vtk_frame_count`,
   `requested_vtk_expected_final_window_time_steps`, `requested_vtk_expected_final_window_step_span`,
   `requested_vtk_minimum_step_span` and `requested_vtk_frame_gate=pass`; a run configured to save fewer than the
   minimum final-window frames, or enough frames over too short a solver-step span, is rejected before interpreting
   accuracy.
   The gate independently parses `source_time_steps` and cross-checks the parsed count, first/last step, strict
   increase, uniform spacing and available-frame coverage. Do not rely on manually written `pass` flags when the source
   step list is missing, duplicated, irregular or not the final available window.

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
   component and must have an official coordinate-delta check. The machine gate recomputes coordinate-delta coverage
   from the Data Probe audit CSV rows; summary metrics are never accepted as paper-grade coordinate evidence. The
   explicit summary-only diagnostic override may only mark legacy traceability as diagnostic context. The metrics row
   must also close official-probe coverage:
   `official_measurement_count` must match `valid_n`,
   `official_probe_coverage_ratio` must be `1.0`, and `missing_official_probe_count` must be `0`.
   A subset of official probes is diagnostic only, because it can hide poor locations and understate MAE/RMSE.
   The metrics builder and final gate use the same normalized probe-ID key, ignoring case, spaces and punctuation.
   Duplicate official IDs after this normalization must be fixed in the source table instead of being silently
   overwritten.
   The Data Probe audit CSV must keep one consistent finite `Uref`, one consistent wind vector, and valid
   `normalization_valid`/`wind_direction_valid` flags for every
   valid probe; a correct summary metrics row alone is not sufficient. The machine gate requires
   `compared_component_consistency_gate=pass`; a single component label in a summary row is not enough if the per-probe
   component audit is missing or incomplete. Native FluidX3D runs that bypass Grasshopper must use
   `scripts/probe_vtk_points.py` to emit the same Data-Probe-compatible audit CSV before metrics are built. Use
   `--interpolation trilinear` for structured VTK validation and treat `nearest_distance` as a coverage/tolerance audit,
   not as the velocity sampling method.
   The probe audit must also record `vtk_source_step_span` and `minimum_validation_average_step_span`; the final gate
   rejects probe averages whose source VTK steps do not match the runtime averaging window or cover fewer than
   `--min-avg-step-span` solver steps.
   The machine gate now enforces `probe_projection_distance`: every valid probe must record `nearest_distance` and
   `tolerance`, the maximum distance must be within the recorded tolerance, and both maximum distance and tolerance must
   stay within the configured `dx` ratio. Increasing tolerance to rescue a missing slice point is diagnostic only.
   Component and Uref sensitivity must be archived as `component_sensitivity_audit.json`; final validation reads the
   selected component, best component, RMSE comparison and best-fit Uref scale from that audit file, not from
   self-reported fields in the metrics row. The audit must include `probe_audit_sha256`, and that hash must match the
   current `probe_audit.csv`; it must also include `official_sha256` matching the `--official` RS table supplied to the
   final gate. Otherwise a stale component/Uref sensitivity result cannot be used to interpret bias.
   The gate also enforces `probe_source_window`: every valid probe row must carry `vtk_source_time_steps` and
   `vtk_source_sha256`, the source steps must match the metrics/inlet final-window `source_time_steps`, and the hash
   count must match the averaged frame count. Probe rows sampled from stale, mixed or undocumented VTK frames are
   diagnostic even when the final metric row reports acceptable error values.

8. Grid-sensitivity gate.
   Archive at least two matched dx levels before interpreting a residual low-bias pattern as solver accuracy. Run
   `scripts/audit_grid_sensitivity.py` on the completed validation metrics rows and archive
   `grid_sensitivity_audit.json`. The finest-grid row must be the row passed to `validation_gate.py`, the refinement
   ratio must meet the configured threshold, and the finest-vs-next-coarse `U_RMSE_ratio` and `U_bias_ratio` changes
   must be bounded. The final gate reads these values from `grid_sensitivity_audit.json`, not from self-reported
   metrics fields. A single high-resolution Case A run is still diagnostic, even if it improves the result.

9. Native/CityLBM parity gate.
   For a CityLBM-driven Case A run, archive `native_citylbm_parity_audit.json` from
   `scripts/audit_native_citylbm_parity.py`. The audit must show that the CityLBM metrics row and the native FluidX3D
   metrics row use the same case, wind direction, `dx`, steps, VTK cadence, averaging window, `Uref`, inlet/boundary
   settings, probe component, probe table, source-audit gate states and evidence hashes. The required hashes include
   the AF/profile CSV, official measurement CSV, component-sensitivity official table and generated inlet/boundary
   `setup.cpp` source-audit files. Without this paired-condition audit, CityLBM-vs-native differences cannot
   be interpreted as software-integration error or inherited FluidX3D accuracy. Final validation reads matched and
   mismatched field counts from `native_citylbm_parity_audit.json`, not from the metrics row.

10. Promotion gate.
   CityLBM may inherit native FluidX3D settings only after native Case A has a passing or explicitly bounded diagnostic
   record. If native FluidX3D underpredicts mean speed or `k`, do not tune CityLBM to hide the discrepancy; fix or
   document the native physics first.

## Minimum Settings To Archive

- FluidX3D source path and source hash or commit.
- CityLBM `native_fluidx3d_baseline_manifest.json` with `NativeFluidX3DPathExplicitlyProvided=true` and a passing
  `NativeFluidX3DSourceValidation` record.
- `setup.cpp`, `defines.hpp`, `buildings.stl`, run log and postprocess script hashes.
- `dx`, lattice dimensions, `tau`, target Reynolds number, velocity set and LES/subgrid settings.
- `grid_sensitivity_audit.json`, including `grid_sensitivity_gate`, `grid_sensitivity_run_count`,
  `grid_sensitivity_finest_dx_m`, `grid_sensitivity_next_coarse_dx_m`,
  `grid_sensitivity_refinement_ratio`, `grid_sensitivity_rmse_change_ratio` and
  `grid_sensitivity_bias_change_ratio`. The final gate requires this audit in addition to the single-run `dx`.
- For CityLBM parity runs, `native_citylbm_parity_audit.json`, including `native_citylbm_parity_gate`,
  `native_citylbm_parity_native_metrics`, `native_citylbm_parity_matched_field_count`,
  `native_citylbm_parity_mismatched_field_count`, `native_citylbm_parity_mismatched_fields`,
  `native_citylbm_parity_compared_gate_field_count` and `native_citylbm_parity_compared_hash_field_count`.
  The machine gate now requires at least 20 compared parity fields, at least 20 compared gate fields and all 5
  evidence-hash fields before a CityLBM row can claim inherited native FluidX3D accuracy.
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
  `boundary_equivalence_supported`, `boundary_evidence_class`, `boundary_evidence_class_supported`,
  `boundary_evidence_files_all_exist`, `boundary_evidence_files_all_hashed`, evidence-file SHA256 records,
  `boundary_condition_fields_supported`, per-condition `*_supported` booleans, `clearance_numeric_gate` and
  `clearance_numeric_gate_reasons`; this file must be generated from metadata plus an
  explicit AIJ boundary evidence JSON before paper-grade promotion. A metadata-only, metrics-only or token-only
  boundary summary cannot pass the paper-grade boundary gate.
- `TYPE_E` boundary velocity initialization policy. CityLBM v0.3.0 generated cases initialize outlet, lateral and top
  `TYPE_E` nodes from the mean wind profile before device upload to avoid zero-speed boundary damping; archive the
  generated `setup.cpp` evidence for native and CityLBM parity runs. The machine gate reads this from
  `boundary_source_audit.json`, not from notes in the metrics CSV.
- Wall/roughness treatment: no-slip, rough-wall function, precursor/recycling, roughness blocks, or other documented
  approach.
- Inlet turbulence method: off, STG-lite, synthetic-eddy, digital-filter, recycling-rescaling or precursor.
- Inlet distribution treatment: macroscopic velocity only, equilibrium/distribution reconstruction, precursor field, or
  other archived method.
- STG correlation-length evidence source: record `STG Length Source`,
  `SyntheticTurbulentInletLengthScaleSource` and `SyntheticTurbulentInletLengthScaleGate`. Empty or user-selected
  lattice-cell values are diagnostic only; paper-grade promotion requires archived AIJ/official, precursor/recycling,
  digital-filter, synthetic-eddy, SEM/DFM or validated length-scale-model evidence. The machine gate requires both a
  supported source and `SyntheticTurbulentInletLengthScaleGate=pass`; source-like text alone is diagnostic context.
- Inlet `U` and `k` preservation metrics from the empty tunnel.
- Inlet/empty-tunnel profile-audit JSON and CSV from real post-spinup VTK frames, including the selected plane, all
  available VTK steps, selected source VTK steps, `selected_last_window`, `source_steps_strictly_increasing`,
  `source_step_spacing_uniform`, `time_averaging_gate_reasons`, `negative_streamwise_fraction`,
  `inlet_streamwise_direction_gate`, `U_MAE_ratio`, `U_RMSE_ratio`, `U_bias_ratio`, `k_MAE_ratio`, `k_RMSE_ratio`,
  `k_bias_ratio`, and the
  `inlet_profile_gate`.
- Inlet correlation-audit JSON from the same final-window VTK frames, including `inlet_correlation_gate`,
  `temporal_lag1_mean_correlation`, `temporal_lag1_abs_mean_correlation`, `spatial_adjacent_mean_correlation` and
  `mean_streamwise_fluctuation_variance`, plus `sample_count`, `adjacent_pair_count` and temporal/spatial finite
  correlation fractions.
  The metrics row must also carry `inlet_correlation_source_time_steps`, `inlet_correlation_frame_count`,
  `inlet_correlation_selected_last_window`, `inlet_correlation_source_steps_strictly_increasing` and
  `inlet_correlation_source_step_spacing_uniform`.
- Building probe metrics: `U_MAE_ratio`, `U_RMSE_ratio`, `U_bias_ratio`, `U_R2`, slope, intercept, max absolute error,
  `U_best_fit_scale_to_exp`, scaled RMSE and `bias_diagnosis`.
- Metrics input hashes: `validation_metrics.csv` must record `probe_mapping_table_sha256` matching the current
  `probe_audit.csv` and `official_measurement_sha256` matching the current official RS table passed to
  `validation_gate.py`.
- Component/Uref sensitivity audit hashes: `component_sensitivity_audit.json` must record `probe_audit_sha256` matching
  the current `probe_audit.csv` and `official_sha256` matching the official RS table passed to `validation_gate.py`.
- Probe mapping diagnostics: valid/failed count, mean/max probe distance, tolerance, compared-component consistency and
  coordinate-delta coverage across all valid probes.
- Probe source-window diagnostics: `probe_vtk_source_window_gate`, `probe_vtk_source_time_steps`,
  `probe_vtk_source_hash_set_count` and any `probe_vtk_source_window_reasons`, proving that probe extraction used the
  same final-window VTK frames as the averaging and inlet-profile audits.

## Machine Gate

After every native FluidX3D or CityLBM-driven Case A run, execute the repository gate before using metrics in a paper:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseA --software native-fluidx3d --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --expected-compared-component speed_ratio --expected-uref <Uref> --expected-wind-vector 1,0,0 --max-mean-speed-stddev-ratio 0.05 --max-point-speed-stddev-ratio 0.20 --out <run_dir>\validation_gate_report.json
```

If metrics are produced from Grasshopper `Data Probe`, build the metrics row first:

```powershell
python scripts\audit_native_run.py <run_dir> --metadata <case_metadata.json> --solver-log <solver.log> --average-last-n 40 --min-avg-frames 40 --min-avg-step-span 20000 --out <native_run_audit.json>

python scripts\audit_inlet_source.py --setup <run_dir>\src\setup.cpp --metadata <case_metadata.json> --out <run_dir>\inlet_source_audit.json

python scripts\audit_boundary_source.py --setup <run_dir>\src\setup.cpp --metadata <case_metadata.json> --out <run_dir>\boundary_source_audit.json

python scripts\audit_inlet_profile_from_vtk.py <run_dir>\output --af-csv <AF_caseA.csv> --metadata <case_metadata.json> --wind-direction 1,0,0 --plane-axis auto-inlet --average-last-n 40 --min-frames 40 --min-step-span 20000 --out-json <run_dir>\inlet_profile_audit.json --out-csv <run_dir>\inlet_profile_audit.csv

python scripts\audit_inlet_correlation_from_vtk.py <run_dir>\output --metadata <case_metadata.json> --wind-direction 1,0,0 --plane-axis auto-inlet --average-last-n 40 --min-frames 40 --min-step-span 20000 --out-json <run_dir>\inlet_correlation_audit.json

python scripts\probe_vtk_points.py <run_dir>\output --official <RS-caseA.csv> --case CaseA --wind-direction-label <direction> --wind-direction 1,0,0 --u-ref <Uref> --compared-component speed_ratio --interpolation trilinear --tolerance <probe_tolerance_m> --average-last-n 40 --min-avg-frames 40 --min-avg-step-span 20000 --out <probe_audit.csv>

python scripts\audit_component_sensitivity.py --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --case CaseA --wind-direction <direction> --selected-component speed_ratio --out-json <run_dir>\component_sensitivity_audit.json --out-csv <run_dir>\component_sensitivity_audit.csv

python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS-caseA.csv> --metadata <case_metadata.json> --read-vtk-audit <native_run_audit.json> --inlet-source-audit <run_dir>\inlet_source_audit.json --boundary-source-audit <run_dir>\boundary_source_audit.json --inlet-profile-audit <run_dir>\inlet_profile_audit.json --inlet-correlation-audit <run_dir>\inlet_correlation_audit.json --component-sensitivity-audit <run_dir>\component_sensitivity_audit.json --case CaseA --wind-direction <direction> --u-ref <Uref> --out <validation_metrics.csv>
```

Always pass `--selected-component` for paper-grade runs. If this argument is omitted, the audit may only infer the
selected component from valid, non-failed probe rows; missing or mixed per-probe `compared_component` values fail the
component/Uref sensitivity audit before residual bias is interpreted.

Before the final gate, archive the AIJ boundary evidence as JSON and audit it:

```powershell
python scripts\audit_boundary_protocol.py <run_dir> --metadata <case_metadata.json> --evidence <boundary_evidence.json> --out <run_dir>\boundary_protocol_audit.json
```

For a native FluidX3D run that bypasses Grasshopper, the same evidence chain can be generated with one command:

```powershell
python scripts\run_native_validation_chain.py <run_dir> --official <RS-caseA.csv> --af-csv <AF_caseA.csv> --metadata <case_metadata.json> --boundary-evidence <boundary_evidence.json> --solver-log <solver.log> --case CaseA --wind-direction-label <direction> --wind-vector 1,0,0 --u-ref <Uref> --software native-fluidx3d --average-last-n 40 --min-avg-frames 40 --min-avg-step-span 20000 --compared-component speed_ratio --interpolation trilinear --probe-tolerance <probe_tolerance_m>
```

The command writes `validation_chain_manifest.json`, `native_run_audit.json`, `inlet_profile_audit.json/.csv`,
`inlet_correlation_audit.json`, `boundary_protocol_audit.json`, `probe_audit.csv`,
`component_sensitivity_audit.json/.csv`, `validation_metrics.csv`, `probe_comparison.csv` and
`validation_gate_report.json` under
`<run_dir>\validation_chain`. It does not run FluidX3D; it only audits newly generated VTK frames and solver evidence
that already exist in the run directory. `native_run_audit.json` must report `run_freshness_gate=pass`, proving that the
selected final-window VTK frames are newer than the current run-definition artifacts such as `setup.cpp`, `defines.hpp`,
`buildings.stl`, `domain_origin.json` and/or `case_metadata.json`. Stale VTK frames copied from an older setup keep the
run diagnostic.

When `--mean-speed-stddev-ratio` and `--max-speed-stddev-ratio` are omitted, `audit_native_run.py` deterministically
samples up to 20,000 points from the selected final VTK frames and computes these stability ratios from the real
velocity time series. Explicit CLI mean-speed, standard-deviation or stability-ratio values are diagnostic-only; any
such override is recorded as `mean_speed_statistics_source=cli_override` and cannot satisfy the paper-grade
time-averaging gate. A stricter external full-field or probe-specific stationarity analysis may be archived as
supporting evidence, but the machine gate still requires sampled VTK statistics from the selected final-window frames.
The validation metrics row must use the actual audit `averaged_frame_count` and `source_time_steps`, not only the
requested `--average-last-n` value. A run with four real final VTK frames remains four-frame diagnostic evidence even if
the requested averaging window was ten frames. A run with no archived `source_time_steps` remains diagnostic even when
`ExpectedVtkFrameCount` or a CLI averaging request is greater than the minimum frame threshold.
The metrics row must also carry `run_freshness_gate`, `run_freshness_gate_reasons`, `latest_reference_mtime_utc` and
`oldest_selected_vtk_mtime_utc`; however, final `validation_gate.py` reads run freshness and solver-stability status
directly from `native_run_audit.json` or an archived Read VTK audit JSON. Summary metrics fields are ignored for this
gate, so stale or copy-forward VTK output cannot be promoted by editing `validation_metrics.csv`.

For a CityLBM-driven parity run, change `--software citylbm`, pass the already completed native metrics row with
`--paired-native-metrics <native_validation_metrics.csv>`, and keep the same metrics/probe schema. A passing paper-grade
record must archive `validation_gate_report.json`. The metrics row must include `empty_tunnel_gate=pass`,
`native_citylbm_parity_gate=pass`, `lbm_stability_gate=solver_log_no_stability_warnings`,
`solver_stability_warnings=none`, `normalization_valid=true`, `wind_direction_valid=true`, at least 10 averaged source frames,
`inlet_profile_gate=pass`, zero failed probes, bounded probe projection distance/tolerance, bounded mean-velocity bias/RMSE, and reported `k` bias/RMSE. If the gate returns `FAIL`, the run is
diagnostic only even if selected plots look reasonable.
`validation_gate.py` recomputes `native_baseline` from `native_fluidx3d_baseline_manifest.json`, required native source
hashes, BaselineId matching and the `native_fluidx3d_baseline` protocol item; metrics `native_baseline_gate=pass` is only
ignored context.
The JSON report also includes `diagnostic_priority`, which must be followed in order before changing physics parameters:
first close coordinate/component/Uref/probe issues and the component/Uref sensitivity audit, then final-window time
averaging, then AF `U/k` preservation, then turbulent-inlet method, length scale and correlation evidence, then
boundary/roughness/blockage, then the native FluidX3D baseline, native/CityLBM parity and grid sensitivity, and only then interpret the
remaining systematic bias as a physics/protocol problem.
The inlet `U/k` audit follows the same final-window rule as the VTK/probe average: short, non-final or irregular
source steps, or inlet-profile source steps that differ from the global averaged VTK window, fail before the result can
be interpreted as solver accuracy. The inlet-profile and inlet-correlation audits must also cover at least
`--min-avg-step-span` solver steps, not only the minimum frame count. The probe audit must carry the same
`vtk_source_step_span`; mismatched or missing per-probe step-span evidence fails before error statistics are interpreted.
When a native FluidX3D run has no Grasshopper Read VTK audit, `scripts/validation_metrics_from_probe_audit.py` uses the
inlet-profile audit as the authoritative source for `available_frame_count`, selected source time steps, last-window
selection, source-step monotonicity, uniform-spacing fields and selected-plane speed-stability ratios in the standard
metrics row.
It also fails when more than 5% of sampled inlet velocities project opposite to the declared wind vector, which catches
wind-sign and streamwise-component mistakes before AF/profile or probe errors are interpreted.
The gate also checks that `validation_metrics.csv` was built from the same `probe_audit.csv` and official RS table
passed on the command line by comparing `probe_mapping_table_sha256` and `official_measurement_sha256`.
The command intentionally omits `--allow-velocity-only-inlet`; add that flag only for explicitly labelled diagnostic
STG-lite sensitivity runs, not for the native FluidX3D baseline or a paper-grade CityLBM equivalence claim. Even when
that diagnostic override is used, `validation_gate.py` still fails the separate `paper_grade_inlet_method` gate until
the inlet treatment is distribution-consistent, digital-filter/SEM/DFM, precursor or recycling based and the final-window
U/k preservation evidence passes.
The validation gate infers `systematic_bias` directly from `U_bias_ratio` when its magnitude exceeds the configured
threshold, even if `systematic_bias_flag` is missing from the metrics row. If `bias_diagnosis` reports
`scale_like_error`, audit `Uref`, SI/LBM velocity conversion and compared component before changing inlet or boundary
parameters. If the scaled error remains large, prioritize boundary, roughness and inlet physics.

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
