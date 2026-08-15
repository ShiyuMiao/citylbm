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
- `k(m2/s2)` must be complete for all valid `z,U` rows. CityLBM v0.3.0 rejects partial `k` columns and duplicate
  profile heights because either condition can corrupt `profile_k_lbm[]` interpolation and make later inlet-turbulence
  errors untraceable.
- CityLBM setting: `Wind Profile = 3` (`CustomTable`)
- Wind vector: `(0,-1,0)` for N wind interpreted as north-to-south flow
- Uref metadata: `3.928296 m/s @ 15.9 m`
- Measurement file: `RS_caseE.csv`
- Validation subset: `case=ac`, `direction=N`, pedestrian height `z=2 m`

## Simulation settings

- First smoke run: `dx=5 m`, `steps=2000-5000`, `save interval=500 or 1000`
- Formal validation: `dx=2-3 m`, `steps>=10000`, save enough final VTK frames for time averaging. This dx is still
  not sufficient by itself: archive at least one matched coarser/finer metrics row and run
  `scripts\audit_grid_sensitivity.py` so `grid_sensitivity_audit.json` proves bounded finest-grid RMSE/bias change.
  The final gate reads grid convergence from this audit JSON, not from self-reported metrics fields.
- Use LES consistently and record `Cs`, viscosity, grid dimensions and GPU model.
- Archive LBM stability evidence for the exact native/CityLBM run: target maximum lattice velocity, estimated maximum
  Mach number, `tau`, `nu_lbm`, physical viscosity, Reynolds number, velocity set, LES/subgrid model and solver-log
  stability warnings. The v0.3.0 machine gate fails paper-grade promotion unless the runtime metrics row records a
  passing stability gate such as `lbm_stability_gate=solver_log_no_stability_warnings` and
  `solver_stability_warnings=none`.
  In v0.3.0, generated cases compute `nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx` and do not clamp `tau` upward to
  0.55. If `tau` is too close to 0.5, treat that as a stability/protocol issue to solve with grid, velocity-scale,
  LES/subgrid and solver-log evidence, not as a value to hide in case generation.
- For AF files with `k(m2/s2)`, enable `Run Simulation / Synthetic Inlet` only when testing the experimental STG-lite inlet.
  Record `STG Scale`/synthetic scale, `STG Corr Cells`/correlation cells, `STG Update`/pattern-update interval, `STG Max Frac`/amplitude cap,
  `STG Length Source`/correlation-length evidence source, and the generated `case_metadata.json` fields
  `SyntheticTurbulentInletRequested`, `SyntheticTurbulentInletInjected`,
  `SyntheticTurbulentInletLengthScaleSource` and `SyntheticTurbulentInletLengthScaleGate`.
  Leave `STG Length Source` empty unless the selected correlation length is backed by archived AIJ/official,
  precursor/recycling, DFM/SEM or validated synthetic-eddy length-scale evidence.
  The final gate reads inlet-source and inlet-correlation pass evidence from `inlet_source_audit.json` and
  `inlet_correlation_audit.json`; copying passing `inlet_source_*` or `inlet_correlation_*` fields into
  `validation_metrics.csv` is not accepted as turbulent-inlet evidence.
- Do not compare a single early VTK frame as a final result.
  The averaging gate requires at least 10 final-window frames, a final-window solver-step span of at least
  `--min-avg-step-span` (`1000` by default), and sampled VTK stability statistics; command-line or hand-entered
  mean/max speed standard-deviation ratios are diagnostic only.
- CityLBM v0.3.0 validation runs must use an explicit external FluidX3D source path in `Run Simulation / FX3D`.
  The legacy bundled v0.5.0 fallback is disabled for controlled validation because it is not the baseline.
  Mode 1/2/3 reject auto-detected paths for validation. The FX3D path must point to a deployable native source root
  containing `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`, plus `src/setup.cpp`, `src/defines.hpp`, `src/lbm.hpp` and
  `src/lbm.cpp`. Mode 0 may still generate a case without FX3D for offline preparation, but that is not a run.

## Required checks before accepting a run

- Generated `setup.cpp` contains `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]`, `profile_origin_z_m`, `profile_first_z_m` and `profile_last_z_m`.
- `case_metadata.json` records `CustomProfileRows`, `CustomProfileKRows`, `CustomProfileKComplete`, `KMinM2s2`,
  `KMaxM2s2`, `KMinLbm`, `KMaxLbm`, `ProfileFirstZM` and `ProfileLastZM`.
- If STG-lite is enabled, generated `setup.cpp` also contains `syntheticTurbulentInlet`, `applySyntheticTurbulentInlet`,
  `citylbm_stg_*` constants and the divergence-reduced transverse spectral-mode projection.
- The generated `validation_protocol_audit` must explicitly record `native_fluidx3d_baseline`, `boundary_conditions`,
  `lbm_stability_scaling`, `wind_direction_sign`, `probe_projection`, `normalization_basis` and `systematic_bias_gate`.
  Treat these items as paper-blocking until their run evidence is archived.
- `domain_origin.json` exists in both case root and output directory.
- `case_metadata.json` exists in both case root and output directory.
  Archive `BoundaryProtocolAudit` from this file: inlet/outlet/lateral/top faces, clearances in meters and H units,
  approximate frontal/plan blockage ratios, blockage gate, boundary protocol gate, and the simplified `TYPE_E`/`TYPE_S`
  boundary-type record. The blockage ratios are axis-aligned diagnostics from model/domain bounds; verify them against
  the official AIJ wind-tunnel blockage definition before making paper-grade claims.
- Archive an explicit AIJ boundary evidence JSON and generate `boundary_protocol_audit.json`. The evidence JSON must
  include `aij_case`, `wind_direction`, `boundary_equivalence_basis`, `inlet_boundary`, `outlet_boundary`,
  `lateral_boundary`, `top_boundary`, `ground_wall_treatment`, `roughness_treatment`, `floor_roughness_source`,
  `blockage_source`, `fetch_clearance_source`, `inlet_fetch_clearance_h`, `downstream_clearance_h`,
  `min_lateral_clearance_h`, `top_clearance_h`, `outlet_reflection_check`, `side_top_boundary_check`,
  `boundary_evidence_class`, at least one existing `boundary_evidence_files` support artifact and
  `boundary_evidence_gate=pass`. Each support artifact must be non-empty and recorded with SHA256 in
  `boundary_protocol_audit.json`. `boundary_equivalence_basis` must be backed by an archived tag such as
  `aij_verified`, `wind_tunnel_protocol_matched`, `empty_tunnel_passed`, `validated_boundary_model`,
  `precursor_boundary` or `recycling_boundary`. Domain clearance or token-only equivalence text is diagnostic and
  cannot pass the paper-grade boundary gate without a supported evidence class and archived support file.
  The final gate reads these boundary support booleans from `boundary_protocol_audit.json`; copying equivalent-looking
  `boundary_*_supported=true` fields into `validation_metrics.csv` is not accepted as AIJ boundary evidence. It also
  recomputes the SHA256 of every `boundary_evidence_files_sha256` entry from the current archived files, so an edited,
  missing or incompletely hashed support file invalidates the boundary evidence even if the JSON flag still says
  `boundary_evidence_files_all_hashed=true`.
- Audit the generated boundary source before accepting the boundary protocol. Run
  `scripts\audit_boundary_source.py --setup <case_dir>\src\setup.cpp --metadata <case_metadata.json> --out <case_dir>\boundary_source_audit.json`
  and archive `setup_cpp_sha256`, `boundary_source_method_class`, `boundary_source_simplified` and
  `boundary_source_wind_tunnel_equivalent`. A simplified `TYPE_E` outlet/lateral/top setup with `TYPE_S` no-slip
  floor/buildings remains diagnostic and cannot satisfy SCI-grade Case E boundary evidence by metadata alone.
  The audit accepts `TYPE_E`/`TYPE_S` assignments as generated-source evidence even when those constants are defined by
  included FluidX3D headers; this avoids a false missing-source failure while keeping the simplified-boundary paper gate
  failed.
  Advanced boundary tokens such as non-reflecting outlet, periodic side/top, rough-wall, precursor or recycling must
  come from comment-stripped generated C++ code. Archive `boundary_source_advanced_code_evidence=true` and
  `advanced_boundary_evidence_uses_comment_stripped_code=true` before treating the boundary source as AIJ-equivalent.
  For the current simplified/profile `TYPE_E` boundary source, also archive the structured velocity-initialization
  evidence from `boundary_source_audit.json`: `has_type_e_velocity_initialization=true`,
  `has_type_e_velocity_initialization_guard=true`, `has_type_e_velocity_initialization_coordinates=true`,
  `has_type_e_velocity_initialization_velocity_write=true` and, for CustomTable/profile inlet runs,
  `has_profile_type_e_velocity_initialization=true`.
  The validation gate treats boundary protocol, boundary-source and roughness/precursor claims as audit-only evidence:
  metrics CSV/JSON fields with the same names are recorded as ignored context and cannot substitute for
  `boundary_protocol_audit.json` or `boundary_source_audit.json`.
- `validation_protocol_audit.json` and `validation_protocol_audit.md` exist in both case root and output directory.
  Treat any `risk` or `fail` item as a blocker for paper-grade validation claims until resolved or explicitly justified.
- VTK files are newly generated for the current run directory, not copied from older experiments. The native audit must
  report `run_freshness_gate=pass`, with `latest_reference_mtime_utc` from the run-definition artifacts
  (`setup.cpp`, `defines.hpp`, `buildings.stl`, `domain_origin.json` and/or `case_metadata.json`) and
  `oldest_selected_vtk_mtime_utc` from the selected final-window VTK frames. A stale VTK frame that is older than the
  current setup/metadata keeps the run diagnostic even if the metrics are numerically acceptable.
  The final gate reads this evidence from `native_run_audit.json` or an archived Read VTK audit JSON, not from
  self-reported `validation_metrics.csv` fields.
  It also recomputes SHA256 for every runtime-selected VTK file path listed in that audit. Missing files, missing paths
  or declared hashes that do not match the current disk files fail `runtime_vtk_hash_traceability`, and the downstream
  probe/inlet source-window gates are not allowed to trust those runtime hashes.
  The final gate also recomputes the run-freshness mtime comparison from the archived paths in
  `freshness_reference_files` and `freshness_selected_vtk_files`. A copied audit JSON with
  `run_freshness_gate=pass` fails if the current VTK files are older than `setup.cpp`, `defines.hpp`, `buildings.stl`,
  `domain_origin.json` or `case_metadata.json`, or if any referenced file is missing.
- The AF inlet profile must be verified from real post-spinup VTK frames before probe accuracy is interpreted. Run
  `scripts\audit_inlet_profile_from_vtk.py` on the output VTK sequence, compare against `AF_caseE.csv`, and archive the
  resulting `inlet_profile_audit.json` and `.csv`. This audit checks that `Wind Profile=3` actually preserved both
  `U(z)` and the AF third-column `k(m2/s2)` statistics at the selected inlet/empty-tunnel plane.
  The final gate reads these pass/fail fields directly from `inlet_profile_audit.json`, not from self-reported
  `validation_metrics.csv` fields.
  It also records all available VTK steps, selected source steps, `selected_last_window`,
  `source_steps_strictly_increasing`, `source_step_spacing_uniform`, `time_averaging_gate_reasons`,
  `negative_streamwise_fraction`, and `inlet_streamwise_direction_gate`. Short, non-final or irregular inlet windows
  fail before probe accuracy is interpreted. The selected inlet-profile `source_time_steps` must also match the global
  runtime averaging audit exactly, and the selected VTK SHA256 hashes must match the runtime audit's selected VTK
  hashes. The inlet-profile audit's `af_csv_sha256` must also match `case_metadata.json` `WindProfileCsvSha256`;
  otherwise the run may have preserved a different AF table and remains diagnostic. A high
  reverse-streamwise fraction flags wind-vector or velocity component sign errors.
  The final gate recomputes hashes for the `selected_vtk_files` listed in `inlet_profile_audit.json`; an inlet profile
  audit without archived VTK paths, with missing files, or with mismatched file hashes is diagnostic even when the
  reported `source_time_steps` match the runtime window.
- The generated FluidX3D source must also be audited before interpreting the VTK result. Run
  `scripts\audit_inlet_source.py --setup <case_dir>\src\setup.cpp --metadata <case_metadata.json> --out <case_dir>\inlet_source_audit.json`
  and archive the resulting `setup_cpp_sha256`, `inlet_source_method_class`,
  `inlet_source_distribution_consistent` and `inlet_source_velocity_field_only` fields. A method name or metadata flag is
  not sufficient for SCI-grade Case E validation if the generated source only refreshes macroscopic velocity fields.
  The inlet-source audit classifies advanced inlet methods from comment-stripped generated C++ code. Archive
  `advanced_inlet_evidence_uses_comment_stripped_code=true` or `inlet_source_comment_stripped_code_audit=true`;
  otherwise the final gate treats the audit as stale or incomplete. Words such as `digital-filter`, `SEM`,
  `precursor` or `recycling` in comments are not implementation evidence.
  Generic distribution-function tokens are also not sufficient. `audit_inlet_source.py` records
  `has_distribution_function_write` and `distribution_function_write_count`, but a digital-filter or SEM/DFM inlet
  claim must additionally show `has_inlet_distribution_reconstruction=true` with a positive
  `inlet_distribution_reconstruction_count`, meaning the distribution reconstruction is tied to inlet/`TYPE_E` code.
  For STG-lite, the audit must also show the actual correlated-source features in generated code:
  `has_spectral_mode_evidence`, `has_taylor_advection_evidence`, `has_transverse_projection_evidence` and
  `has_length_scale_evidence`, plus the run-loop fields `has_synthetic_inlet_refresh_with_current_time`,
  `has_update_interval_run_control` and `has_segmented_stg_run_loop`. These fields separate correlated STG-lite from
  uncorrelated random perturbations and prove that `SyntheticTurbulenceUpdateInterval` controls the generated
  `lbm.run(steps_to_run)` refresh loop. `validation_gate.py` treats missing run-loop fields as stale or incomplete
  source-audit evidence for STG-like inlets, but a
  correlated velocity-field-only inlet remains diagnostic until distribution-function consistency or a validated
  precursor/DFM/SEM/recycling treatment is implemented.
- The turbulent-inlet correlation must be verified from the same real final-window VTK frames with
  `scripts\audit_inlet_correlation_from_vtk.py`. This audit records streamwise fluctuation variance, temporal lag-1
  signed correlation, temporal lag-1 absolute correlation for diagnosis, and adjacent spatial correlation. It is
  required because preserving AF `k` magnitude alone does not prove a digital-filter, SEM, precursor/recycling or
  otherwise correlated turbulent inlet. The audit must also pass temporal/spatial finite-correlation coverage fractions
  so a sparse subset of correlated non-degenerate samples cannot represent the full inlet plane.
  `validation_gate.py` independently checks that the correlation audit uses the same final averaged `source_time_steps`
  and VTK SHA256 hashes as the runtime audit, and that streamwise variance, temporal lag-1 correlation and spatial
  adjacent correlation exceed the configured thresholds. A hand-filled `inlet_correlation_gate=pass` is not sufficient
  when the source window, numeric correlation evidence or audit file is missing. The final gate accepts only the
  `inlet_correlation_audit.json`
  archived in the audited run package; a metrics-table `inlet_correlation_audit` path is ignored so old or external
  correlation JSON cannot be reused silently. The audit's listed VTK file paths and hashes are also recomputed from
  disk before the source-window comparison is trusted.
- The STG length-scale gate is not passed by choosing a convenient number of lattice cells. It passes only when
  `STG Length Source`/`SyntheticTurbulentInletLengthScaleSource` contains an archived evidence tag such as
  `aij_length_scale_verified`, `official_length_scale_verified`, `precursor_length_scale`,
  `digital_filter_length_scale`, `synthetic_eddy_length_scale`, `sem_length_scale`, `dfm_length_scale` or
  `validated_length_scale_model`; otherwise the run remains diagnostic.
  The final gate reads length-scale source and pass/fail status from `case_metadata.json` plus
  `validation_protocol_audit.json`, then cross-checks `inlet_source_audit.json` against the current `setup.cpp`.
  The source audit must detect length-scale code evidence and the generated metadata must carry a positive
  `SyntheticTurbulenceCorrelationLengthM`. `validation_metrics.csv` may summarize these fields, but self-reported
  `inlet_length_scale_source`, `inlet_length_scale_gate` or `synthetic_correlation_length_m` values cannot pass this
  gate without the generated metadata/protocol audit and current source-audit closure.
- Post-processing reads the final averaged velocity field, not an initial transient.
  In `Read VTK`, set `Average Last N > 0` and archive the `Averaging Audit` JSON output.
  This JSON records the actual averaged frame count, source time steps, mean speed, mean/max pointwise speed standard
  deviation, mean/max relative fluctuation, the available VTK frame count, whether the selected frames are the last
  available window, and whether source time steps are strictly increasing and uniformly spaced.
  A short window with large residual fluctuation is diagnostic only and must not be treated as paper-grade time averaging.
  For native FluidX3D runs outside Grasshopper, run `scripts\audit_native_run.py` on the run directory and pass its JSON
  to `validation_metrics_from_probe_audit.py --read-vtk-audit`. This records VTK frame hashes, selected final time steps,
  run-freshness evidence, solver-log stability warnings and LBM stability fields in the same schema used by the
  `Read VTK` audit output. `validation_gate.py` uses this runtime audit JSON as the authoritative source for
  run-freshness, solver-stability and time-averaging pass/fail decisions.
  When full-field statistics are not supplied manually, the script deterministically samples up to 20,000 points from
  the selected final VTK frames and computes `mean_speed_stddev_ratio` and `max_speed_stddev_ratio` from the real
  velocity time series.
  The metrics table may summarize the real audited `averaged_frame_count` and `source_time_steps`, but the final
  machine gate reads these fields from the runtime audit JSON, not from `validation_metrics.csv`. The requested
  `Average Last N` value is only a request field and is not sufficient for paper-grade evidence.
  If no Grasshopper `Read VTK` audit is available, `scripts\audit_inlet_profile_from_vtk.py` also computes these
  stationarity ratios from pointwise speed-magnitude time series on the same selected final-window inlet/profile plane,
  and the metrics builder can carry them into the standard validation row.
  The validation gate parses the archived `source_time_steps` list itself and fails duplicated, non-increasing,
  non-uniform, count-mismatched, too-short-span or non-final source windows even when summary fields say `pass`.
- Measurement interpolation uses the official `ac + N` points and records failed or out-of-domain probes.
- The probe audit table must contain official point number, original coordinate, interpolation distance,
  compared velocity component, compared value, wind-vector components, `wind_direction_valid`, `normalization_valid`,
  tolerance, out-of-tolerance flag, failure flag and `failure_reason`.
- In `Data Probe`, connect `Uref=3.928296`, `Wind Direction=(0,-1,0)`, `Probe IDs` from the official `RS_caseE.csv`
  point-number field, `Tolerance` from the run protocol, and `Compared Component`.
  Use `speed_ratio` when comparing with AIJ velocity-ratio magnitudes; use `streamwise_ratio` only if the validation
  table is explicitly defined as along-wind signed velocity. Archive the appended outputs `Speed Ratio`,
  `Streamwise Ratio`, `Nearest Distance`, `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`.
  These outputs are diagnostic only: `Uref` is used for validation ratios and must not be used to replace `AF_caseE.csv`.
  The metrics builder records `compared_component_consistency_gate`, `compared_component_unique_values` and
  `official_coordinate_delta_count`; the machine gate fails if valid probes mix components or if coordinate deltas are
  not available for every valid official probe. Native FluidX3D reruns outside Grasshopper must generate the same audit
  schema with `scripts\probe_vtk_points.py`, filtered to `case=ac` and `Wind_direction=N`, before building metrics.
  The metrics row must also carry `probe_mapping_table_sha256` and `official_measurement_sha256`; the final gate checks
  those against the current `--probe-audit` and `--official` files before any coordinate, component, Uref or bias metric
  is interpreted.
  The final gate reads official-coordinate delta coverage from the per-probe audit rows by default; copied
  `max_official_coordinate_delta_m` or `official_coordinate_delta_count` values in `validation_metrics.csv` are
  diagnostic summaries, not proof of coordinate closure.
  It also rechecks valid per-probe IDs against the current official RS table: IDs must be non-empty, unique among valid
  probe rows and present in the official file passed with `--official`. Duplicated, missing or unmatched point numbers
  keep the run diagnostic even when distance and coordinate-delta summaries look acceptable.
  The metrics builder and final gate use the same normalized probe-ID key, ignoring case, spaces and punctuation.
  Duplicate official IDs after this normalization must be corrected in `RS_caseE.csv` or the filtered official subset,
  not averaged or overwritten in post-processing.
  The reverse coverage is also mandatory: `official_measurement_count` must match `valid_n`,
  `official_probe_coverage_ratio` must be `1.0`, and `missing_official_probe_count` must be `0` for the filtered
  `case=ac`, `Wind_direction=N` official rows. A visually plausible subset of points is not acceptable for SCI-level
  Case E validation.
  Use structured-grid trilinear sampling for the velocity value; the nearest-node distance remains the coverage and
  tolerance evidence.
  Native VTK probe audit rows must include VTK origin, spacing, dimensions, source time steps, source step span, source
  file hashes and nearest-grid coordinates. These fields are required to separate coordinate-frame/projection mistakes
  from true velocity-field error before interpreting Case E bias.
  Run `scripts\audit_component_sensitivity.py` and archive `component_sensitivity_audit.json`; the final gate reads
  selected component, best component, component RMSE improvement and Uref best-fit scale from that audit file, not from
  self-reported fields in `validation_metrics.csv`. The audit must also record `probe_audit_sha256` matching the current
  `probe_audit.csv`, plus `official_sha256` matching the `--official` RS table supplied to the final gate; a stale
  sensitivity audit from another probe extraction or measurement table leaves the run diagnostic.
  The final gate accepts only the `component_sensitivity_audit.json` archived in the audited run package; a metrics-table
  `component_sensitivity_audit` path is ignored so old or external component/Uref sensitivity JSON cannot be reused
  silently.
  The `vtk_source_time_steps` and `vtk_source_sha256` values in every valid probe row must match the same final-window
  VTK frames used by `Read VTK`, `audit_native_run.py`, `audit_inlet_profile_from_vtk.py` and
  `audit_inlet_correlation_from_vtk.py`. `validation_gate.py` fails `probe_source_window` if probe extraction mixes
  windows, omits hashes, uses stale/copy-forward VTK evidence, or disagrees with the metrics `source_time_steps`.
  `vtk_source_step_span` and `minimum_validation_average_step_span` must also be present and meet the same
  `--min-avg-step-span` requirement as the runtime averaging audit.
  Every valid probe row must also include `vtk_source_files`; the final gate recomputes SHA256 from those archived VTK
  paths and compares the result with the row-level `vtk_source_sha256` and runtime final-window hashes.
- A paired native FluidX3D baseline must use the same `setup.cpp` physics choices, grid, VTK averaging window and probe
  extraction before any CityLBM-vs-AIJ error is attributed to the Grasshopper integration layer.
  The native manifest must point to one explicit complete FluidX3D source root. `validation_gate.py` verifies that the
  manifest source root exists, has a build file, and that the required native source records resolve to `src/setup.cpp`,
  `src/defines.hpp`, `src/lbm.hpp` and `src/lbm.cpp` under that same root with matching SHA256 hashes.
- Boundary-source evidence must come from comment-stripped generated `setup.cpp` code. `audit_boundary_source.py` treats
  TYPE_E/TYPE_S assignments, profile inlet, outlet/lateral/top checks, rough-wall evidence and precursor/recycling
  evidence in comments as diagnostics only; commented pseudo-code cannot make a simplified boundary setup paper-grade.
  The final validation gate recomputes the current run package `setup.cpp` SHA256 and requires both
  `inlet_source_audit.json` and `boundary_source_audit.json` to match it; source audits copied from an older generated
  case remain diagnostic.
  The same current-file rule applies to `boundary_protocol_audit.json` supporting files: the gate checks each archived
  support path, size and SHA256 before accepting AIJ-equivalent boundary evidence.
- For a CityLBM-driven Case E validation row, run `scripts\audit_native_citylbm_parity.py` or pass
  `--paired-native-metrics <native_validation_metrics.csv>` to the evidence chain. The resulting
  `native_citylbm_parity_audit.json` must show matched case, wind direction, `dx`, steps, VTK cadence, averaging window,
  `Uref`, inlet/boundary settings, compared component, probe table, source-audit gate states and evidence hashes before
  CityLBM accuracy is compared against native FluidX3D. The hash comparison must cover the AF/profile CSV, official
  measurement CSV, component-sensitivity official table and generated inlet/boundary `setup.cpp` source-audit files.
- `case_metadata.json` must be archived with the run. It records the boundary-condition summary, expected VTK frame count,
  time-averaging requirement, and known protocol risks.
- `native_fluidx3d_baseline_manifest.json` and `.md` must be archived. This manifest lists the exact generated
  `setup.cpp`, `defines.hpp`, `buildings.stl`, metadata files, shared run settings and paired evidence required for a
  native FluidX3D baseline, including SHA256 hashes for the generated source/metadata files. Treat the manifest gate
  `required_before_paper_grade_accuracy_claim` as blocking until the native baseline and CityLBM-driven run are compared
  with the same VTK averaging and probe audit table.
  The manifest also records whether the FluidX3D source path was explicitly supplied and whether the original native
  source tree passed the required-file check. If `NativeFluidX3DPathExplicitlyProvided=false` or source validation fails,
  the run cannot be used as the native baseline for paper claims. `validation_gate.py` and the native validation chain
  recompute SHA256 hashes from the manifest-listed source paths before accepting the baseline; stale or hand-filled
  manifest hashes are diagnostic only. The final gate recomputes `native_baseline` from this manifest and the
  `native_fluidx3d_baseline` protocol item; a metrics `native_baseline_gate=pass` field is only ignored context.
- Convert the `Data Probe` audit table and official `RS_caseE.csv` subset into a standard metrics row:

```powershell
python scripts\audit_inlet_profile_from_vtk.py <run_dir>\output --af-csv <official_data>\AF_caseE.csv --metadata <case_metadata.json> --wind-direction 0,-1,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_profile_audit.json --out-csv <run_dir>\inlet_profile_audit.csv

python scripts\audit_inlet_correlation_from_vtk.py <run_dir>\output --metadata <case_metadata.json> --wind-direction 0,-1,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_correlation_audit.json

python scripts\probe_vtk_points.py <run_dir>\output --official <official_data>\RS_caseE.csv --case ac --wind-direction-label N --wind-direction 0,-1,0 --u-ref 3.928296 --compared-component speed_ratio --interpolation trilinear --tolerance <probe_tolerance_m> --average-last-n 10 --min-avg-frames 10 --min-avg-step-span 1000 --out <probe_audit.csv>

python scripts\audit_component_sensitivity.py --probe-audit <probe_audit.csv> --official <official_data>\RS_caseE.csv --case ac --wind-direction N --selected-component speed_ratio --out-json <run_dir>\component_sensitivity_audit.json --out-csv <run_dir>\component_sensitivity_audit.csv

python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <official_data>\RS_caseE.csv --metadata <case_metadata.json> --read-vtk-audit <read_vtk_averaging_audit.json> --inlet-profile-audit <run_dir>\inlet_profile_audit.json --inlet-correlation-audit <run_dir>\inlet_correlation_audit.json --component-sensitivity-audit <run_dir>\component_sensitivity_audit.json --case ac --wind-direction N --u-ref 3.928296 --z-ref 15.9 --out <validation_metrics.csv> --comparison-out <probe_comparison.csv>
```

The final gate rechecks `component_sensitivity_audit.json` numerically. A run is diagnostic if another velocity
component materially lowers RMSE or if a best-fit scale far from `1.0` materially improves the selected component,
because that pattern can indicate a component, Uref or SI/LBM conversion error before inlet or boundary physics are
interpreted.

Generate the boundary protocol audit before the final gate:

```powershell
python scripts\audit_boundary_protocol.py <run_dir> --metadata <case_metadata.json> --evidence <boundary_evidence_casee_ac_N.json> --out <run_dir>\boundary_protocol_audit.json
```

- For a native FluidX3D or CityLBM run package with newly generated VTK frames, produce the complete post-run evidence
  package with one command:

```powershell
python scripts\run_native_validation_chain.py <run_dir> --official <official_data>\RS_caseE.csv --af-csv <official_data>\AF_caseE.csv --metadata <case_metadata.json> --boundary-evidence <boundary_evidence_casee_ac_N.json> --solver-log <solver.log> --case ac --wind-direction-label N --wind-vector 0,-1,0 --u-ref 3.928296 --z-ref 15.9 --software citylbm --average-last-n 10 --min-avg-frames 10 --min-avg-step-span 1000 --compared-component speed_ratio --interpolation trilinear --probe-tolerance <probe_tolerance_m> --dx <dx_m> --steps <steps> --save-interval <save_interval> --geometry-scale 250 --paired-native-metrics <native_validation_metrics.csv>
```

  The command creates `validation_chain_manifest.json`, `native_run_audit.json`, `inlet_source_audit.json`,
  `boundary_source_audit.json`, `inlet_profile_audit.json/.csv`, `inlet_correlation_audit.json`,
  `boundary_protocol_audit.json`, `probe_audit.csv`,
  `component_sensitivity_audit.json/.csv`, `validation_metrics.csv`, `probe_comparison.csv` and
  `validation_gate_report.json` under `<run_dir>\validation_chain`. It does not start a CFD simulation and must not be
  used to imply that Case E was rerun unless the VTK frames in `<run_dir>` were newly produced by the current Rhino 7/
  Grasshopper/CityLBM experiment.
  When `--paired-native-metrics` is supplied, it also writes `native_citylbm_parity_audit.json` and appends the parity
  fields to `validation_metrics.csv`.

- Run the machine gate after postprocessing:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseE --software citylbm --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --official <official_data>\RS_caseE.csv --expected-compared-component speed_ratio --expected-uref 3.928296 --expected-wind-vector 0,-1,0 --max-mean-speed-stddev-ratio 0.05 --max-point-speed-stddev-ratio 0.20 --out <run_dir>\validation_gate_report.json
```

  The gate must pass before Case E is described as paper-grade validation. A failed gate means the run remains
  diagnostic, even if Rhino/Grasshopper visualization and screenshots are complete.
  By default, the gate fails CityLBM's current velocity-field-only STG-lite inlet because it does not reconstruct
  FluidX3D distribution functions. The optional `--allow-velocity-only-inlet` flag is reserved for explicitly labelled
  diagnostic sensitivity runs after an empty-tunnel `U/k` preservation check; do not use it for SCI-grade Case E claims.
  A separate `paper_grade_inlet_method` gate remains failed under this override until the run uses a
  distribution-consistent digital-filter, SEM/DFM, precursor or recycling inlet with final-window U/k preservation.

## Metrics to report

- Valid point count and failed point count
- MAE and RMSE for normalized speed ratio
- Bias and bias ratio
- R2
- Regression slope and intercept
- Maximum absolute error
- Best-fit scale to official measurements, scaled RMSE and `bias_diagnosis` to separate Uref/unit/component errors from
  boundary/inlet physics errors.
- Component/Uref sensitivity audit: selected compared component, best RMSE component, selected/best RMSE, best-fit
  normalization scale, scaled-improvement ratio and `component_normalization_gate`. A failing audit means speed-ratio
  versus streamwise-ratio selection or Uref/SI conversion must be fixed before interpreting physical-model error.
  The audit's `probe_audit_sha256` and `official_sha256` must match the current probe audit CSV and official RS table
  used by the final gate.
- Metrics input-hash traceability: `validation_metrics.csv` must include `probe_mapping_table_sha256` and
  `official_measurement_sha256`, both matching the files passed to the final gate.
- Grid spacing, steps, averaging window and VTK frame list
- Grid-sensitivity audit: `grid_sensitivity_audit.json`, `grid_sensitivity_gate`,
  `grid_sensitivity_run_count`, `grid_sensitivity_finest_dx_m`,
  `grid_sensitivity_next_coarse_dx_m`, `grid_sensitivity_refinement_ratio`,
  `grid_sensitivity_rmse_change_ratio` and `grid_sensitivity_bias_change_ratio`. A single `dx=2-3 m` run remains
  diagnostic until these fields show bounded change from the next coarser/finer matched run.
- Native/CityLBM parity audit for CityLBM rows: `native_citylbm_parity_audit.json`,
  `native_citylbm_parity_gate`, `native_citylbm_parity_native_metrics`,
  `native_citylbm_parity_matched_field_count`, `native_citylbm_parity_mismatched_field_count` and
  `native_citylbm_parity_mismatched_fields`. The audit must also report non-zero gate/hash comparison coverage through
  `native_citylbm_parity_compared_gate_field_count` and `native_citylbm_parity_compared_hash_field_count`. A CityLBM row
  without this audit cannot be used to claim inherited native FluidX3D accuracy.
  The v0.3.0 machine gate requires at least 20 compared parity fields, at least 20 compared gate fields and all 5
  evidence-hash fields for CityLBM/native parity.
- Mean speed, mean/max pointwise speed standard deviation and mean/max relative fluctuation from the averaged VTK field
- `time_averaging` gate must use the final available VTK window, contain at least 10 frames, have strictly increasing
  uniformly spaced source steps, cover at least `--min-avg-step-span` solver steps (`1000` by default), and satisfy
  `mean_speed_stddev_ratio <= 0.05` and `max_speed_stddev_ratio <= 0.20` from the Read VTK audit or native-run audit
  unless a stricter case-specific stationarity criterion is documented.
  Self-reported `validation_metrics.csv` fields cannot pass this gate without the runtime audit artifact.
  Command-line speed-stability ratios in `audit_native_run.py` are diagnostic only; the native run audit passes
  `time_averaging_gate` only when the ratios are computed from deterministic sampled VTK frames.
- Probe source-window closure: `probe_vtk_source_time_steps`, `probe_vtk_source_step_span` and
  `probe_vtk_minimum_step_span` must match the runtime averaged VTK window and meet the same minimum solver-step span.
  This prevents a valid runtime average from being paired with a shorter or stale probe extraction.
- The native-run audit must also record `requested_time_steps`, `requested_vtk_save_interval`,
  `requested_vtk_save_start_step`, `requested_vtk_frame_count` and `requested_vtk_frame_gate=pass`. A Case E run
  planned to save fewer than 10 final-window VTK frames is diagnostic before accuracy metrics are interpreted.
  The final gate recomputes the requested VTK schedule from these fields and checks that `source_time_steps` are the
  final window of both the requested output schedule and `all_available_time_steps`; copied or manually edited
  `selected_last_window=true` / `requested_vtk_frame_gate=pass` flags are not enough.
- Inlet/outlet/lateral/top boundary faces and upstream/downstream/lateral/top clearances in building-height units
- Domain size, maximum building height, approximate frontal blockage ratio, approximate plan blockage ratio and blockage gate
- `boundary_protocol_audit.json`, `boundary_evidence_gate`, `boundary_missing_evidence_fields`,
  `boundary_equivalence_basis`, `boundary_equivalence_supported`, `boundary_evidence_class`,
  `boundary_evidence_class_supported`, `boundary_evidence_files_all_exist`,
  `boundary_evidence_files_all_hashed`, evidence-file SHA256 records, `clearance_numeric_gate` and
  `boundary_clearance_reasons`
- Boundary-condition support fields: `boundary_condition_fields_supported`,
  `boundary_condition_support_reasons`, `inlet_boundary_supported`, `outlet_boundary_supported`,
  `lateral_boundary_supported`, `top_boundary_supported`, `ground_wall_treatment_supported`,
  `roughness_treatment_supported`, `floor_roughness_source_supported`, `blockage_source_supported`,
  `fetch_clearance_source_supported`, `outlet_reflection_check_supported` and
  `side_top_boundary_check_supported`. A text-filled evidence JSON is not enough; unsupported values such as
  `unknown`, `unverified`, `not_checked`, `diagnostic_only` or `assumed_only` keep the run diagnostic.
- Run freshness: `run_freshness_gate`, `run_freshness_gate_reasons`, `latest_reference_mtime_utc` and
  `oldest_selected_vtk_mtime_utc`
- Mean probe distance and maximum probe distance
- Compared component consistency gate, unique compared components and official coordinate-delta coverage count from the
  per-probe audit rows, not only from the summary metrics table
- Valid probe-ID coverage: probe ID column, official ID column, unique valid probe count, duplicate/missing probe-ID
  count, unmatched official-ID count, official measurement count, official probe coverage ratio and missing official
  probe count
- Per-probe `Uref`, wind vector, `normalization_valid` and `wind_direction_valid` coverage from the Data Probe audit
  CSV. For paper-grade Case E, every valid probe must carry the same finite normalization basis and declared wind vector;
  a correct summary metrics row is diagnostic if the per-probe audit is missing or mixed.
- Probe source-window parity: `probe_vtk_source_window_gate`, `probe_vtk_source_window_reasons`,
  `probe_vtk_source_time_steps` and `probe_vtk_source_hash_set_count`. These fields must show that the official-point
  probe table was sampled from the same final averaged VTK window as the inlet and time-averaging audits.
  The final gate also compares each per-probe `vtk_source_sha256` list with the runtime audit's selected VTK frame
  hashes after those runtime hashes are recomputed from the archived VTK files, so a stale probe CSV copied from older
  VTK frames remains diagnostic even if the reported source time steps match.
- Native FluidX3D baseline run id or archive path
- Empty-tunnel `U/k` preservation gate, `empty_tunnel_U_bias_ratio`, `empty_tunnel_k_bias_ratio`
- Inlet profile preservation audit: selected plane, source VTK steps, `inlet_profile_gate`, `inlet_u_profile_gate`,
  `inlet_k_profile_gate`, `inlet_u_mae_ratio`, `inlet_u_rmse_ratio`, `inlet_k_mae_ratio`, and
  `inlet_k_rmse_ratio`. The source VTK steps must be identical to the runtime averaged `source_time_steps`, not merely
  another valid final-window subset, and must cover at least `--min-avg-step-span` solver steps.
- Inlet correlation audit: `inlet_correlation_gate`, signed temporal lag-1 correlation, temporal lag-1 absolute
  correlation, adjacent spatial correlation, temporal/spatial finite correlation fractions and streamwise fluctuation
  variance
  Correlation source-window fields must also be reported: `inlet_correlation_frame_count`,
  `inlet_correlation_source_time_steps`, `inlet_correlation_selected_last_window`,
  `inlet_correlation_source_steps_strictly_increasing`, `inlet_correlation_source_step_spacing_uniform` and
  `inlet_correlation_source_step_span`. The correlation audit must use the same final-window VTK steps as the runtime
  audit and meet the same minimum solver-step span.
- Inlet length-scale source audit closure: metadata/protocol pass status, positive
  `SyntheticTurbulenceCorrelationLengthM`, current `setup.cpp` source hash and source-audit-detected length-scale code
  evidence
- Paper-grade inlet method gate: `paper_grade_inlet_method` must pass. A velocity-field-only STG-lite run remains
  diagnostic even if `--allow-velocity-only-inlet` is used for sensitivity analysis. The metrics row must also record
  an explicit `inlet_method_class` and `inlet_method_class_supported=true`; a method name or protocol pass flag alone
  is not enough without a distribution-consistent treatment.
- Native baseline gate and `validation_gate_report.json`
- Protocol gate from `validation_protocol_audit.json`
- Systematic bias flag and `bias_diagnosis`. If mean bias remains around `-0.20` to `-0.35` speed-ratio units, do not
  tune parameters first. The validation gate also infers systematic bias directly from `U_bias_ratio` when the
  configured threshold is exceeded, even if the metrics row forgot to set `systematic_bias_flag`. If best-fit scaling
  removes much of the error, audit Uref, velocity-unit conversion, compared component and wind-direction sign. If
  scaled RMSE remains large, audit inlet turbulence, boundary treatment, roughness and probe projection.
- `validation_gate_report.json` `diagnostic_priority` ranks the next actions after a failed run. For SCI-grade Case E,
  do not skip lower-rank failures: coordinate/component/Uref/probe closure plus component/Uref sensitivity precedes time averaging; time averaging
  precedes inlet `U/k` preservation; inlet `U/k` preservation precedes turbulent-inlet method and length-scale claims;
  inlet correlation evidence precedes boundary/roughness/blockage evidence; boundary/roughness/blockage evidence
  precedes native baseline, native/CityLBM parity and grid-sensitivity evidence; only after those pass can a remaining
  `-34 pp` style low bias be interpreted as a solver/protocol physics problem.

## Current v0.3.0 limitation

CityLBM v0.3.0 reads, converts and records `k(m2/s2)`. It also provides an optional experimental STG-lite inlet that converts isotropic `k` to bounded deterministic spectral velocity perturbations using `sigma=sqrt(2k/3)`, with inlet refresh controlled by `SyntheticTurbulenceUpdateInterval`. The synthetic spectral-mode amplitudes are projected normal to their wave vectors to reduce non-physical divergent inlet fluctuations, and the spectral normalization targets the component RMS implied by isotropic `k` rather than the lower former diagnostic amplitude. This is a software-level improvement over the former metadata-only `k` chain and the earlier sparse-eddy diagnostic pattern, but it is not a full digital-filter, precursor/recycling, or Reynolds-stress turbulent inflow because the AF table does not provide Reynolds-stress tensors, turbulent length scales or a precursor field. The inlet correlation audit is therefore a necessary precondition that checks real VTK fluctuation correlation, not a replacement for a validated digital-filter/SEM/precursor inlet. The v0.3.0 machine gate treats velocity-field-only STG-lite as non-paper-grade by default; it can only be explicitly allowed for diagnostic sensitivity analysis with `--allow-velocity-only-inlet`. Any paper claim must state whether the validation used metadata-only inflow, STG-lite diagnostic inflow, or a later distribution-consistent turbulent inlet.

The current boundary conditions are also a simplified FluidX3D `TYPE_E` setup: velocity-profile inlet, pressure/free-outflow outlet approximation, lateral/top `TYPE_E`, and no-slip ground/buildings. CityLBM v0.3.0 initializes all `TYPE_E` boundary velocities from the mean wind profile before uploading flags/velocity fields, so outlet/lateral/top boundaries no longer start from zero velocity after their early boundary-return path. This removes one plausible software-side damping source, but it does not make the boundary protocol identical to the AIJ wind tunnel. CityLBM v0.3.0 records domain clearance and approximate frontal/plan blockage ratios in `BoundaryProtocolAudit`, and `validation_gate.py` fails the boundary gate when approximate frontal blockage exceeds the diagnostic threshold, the AIJ-equivalence basis is missing/unsupported, or upstream/downstream/lateral/top clearance evidence is below the configured H thresholds. These fields help detect protocol-scale errors, but they remain screening diagnostics until compared with the AIJ wind-tunnel boundary setup or replaced by a stronger inlet/outlet treatment.

The final gate now requires the TYPE_E velocity-initialization source evidence to come from `boundary_source_audit.json`
for simplified/profile boundary cases. For Case E CustomTable inflow, `has_profile_type_e_velocity_initialization=true`
is required so the archived `setup.cpp` proves boundary nodes are initialized from `windProfile(z)` rather than from a
stale zero field or a metrics-table claim.

The boundary evidence audit now also rejects vague per-condition descriptions. Each inlet, outlet, lateral, top,
ground-wall, roughness, blockage, fetch, outlet-reflection and side/top-boundary item must carry a supported evidence
tag such as `aij_verified`, `wind_tunnel_protocol_matched`, `empty_tunnel_passed`, `validated_boundary_model`,
`non_reflecting_checked`, `reflection_checked`, `roughness_layout_source`, `blockage_verified` or `fetch_verified`.
This is intentionally stricter than a normal smoke test because a remaining Case E bias cannot be interpreted as solver
accuracy until the wind-tunnel boundary protocol is independently supported.
