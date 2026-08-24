# CityLBM v0.3.0 Validation Optimization Notes

v0.3.0 is a validation-readiness branch. It fixes software issues that can create large AIJ validation errors, but it does not claim final Case A or Case E publication-grade accuracy by itself.

## Main fixes relative to earlier versions

- `Create Scene` now accepts `WP=3` for CustomTable profiles.
- `AF_caseE.csv` style input is parsed as `z(m), U(m/s), k(m2/s2)`.
- CustomTable `k` parsing is now strict all-or-none: if any valid CSV row provides `k(m2/s2)`, every valid row must
  provide it, and duplicate `z` heights are rejected before case generation. This prevents missing turbulence rows from
  being silently converted to `profile_k_lbm=0` and corrupting the inlet-energy profile.
- The generated FluidX3D case uses the full `U(z)` table for inlet interpolation.
- CustomTable inlet interpolation is now domain-origin aware: generated `setup.cpp` samples `U(z)` and `k(z)` at
  `profile_origin_z_m + (z_cell + 0.5) * dx`, and metadata records the same `ProfileOriginZM`. Shifted CFD domains can
  no longer silently apply the AF profile at the wrong physical height.
- `Uref` is retained as metadata for normalization instead of replacing the inflow table.
- `scripts/run_native_validation_chain.py` and `scripts/audit_native_preconditions.py` now bind `--u-ref` to the AF CSV
  interpolation at `--z-ref` when a reference height is provided. A mismatched normalization velocity fails before VTK
  probing or remains an explicit native-precondition blocker, preventing scale-like speed-ratio bias from entering the
  Case A/E evidence chain.
- `validation_metrics_from_probe_audit.py` and `docs/validation_metrics_template.csv` now carry native AF-reference
  fields (`expected_uref_mps`, `actual_uref_mps`, `expected_zref_m`, interpolated AF `U(zref)`, and both Uref-vs-AF
  deltas), so downstream Case A/E summary rows expose normalization/profile inconsistencies instead of hiding them in
  separate precondition JSON files.
- `validation_gate.py` now treats those native AF-reference fields as hard inlet-precondition evidence: missing
  `AF U(zref)` data or Uref-vs-AF deltas above `--uref-tolerance` fail the native inlet traceability gate before a
  FluidX3D baseline can be used for CityLBM accuracy interpretation.
- `audit_boundary_source.py` now rejects empty advanced-boundary method stubs such as `void non_reflecting_outlet(...) {}`
  as paper-grade source evidence. Boundary-source metrics now expose the empty-stub flag and count, preventing a named
  non-reflecting/periodic/rough-wall/precursor function from being mistaken for implemented AIJ-equivalent boundaries.
- The `k` column is preserved, converted to LBM units and stored in metadata.
- `case_metadata.json` now records CustomTable row count, `k` row count, all-row `k` consistency, SI/LBM `k` ranges,
  profile origin and the first/last profile heights, so AIJ run packages can audit the inlet profile without reopening
  the CSV.
- `domain_origin.json` now includes schema and version fields.
- `case_metadata.json` records wind profile, velocity scaling, k status, grid and run settings.
- `Read VTK` reports whether metadata-driven velocity scaling was applied.
- `Read VTK` adds `Average Last N` so validation workflows can output an explicit multi-frame time-averaged velocity field instead of a single instantaneous VTK frame.
- `Read VTK` now sorts VTK files by parsed numeric time step instead of lexicographic filename order, preventing
  `u-10000.vtk` style outputs from being selected before shorter time-step names during latest-frame and averaging workflows.
- `Read VTK` now reports averaged-field stability diagnostics: mean speed, mean/max pointwise speed standard deviation,
  and mean/max relative fluctuation across the averaged VTK frames.
- `scripts/probe_vtk_points.py` now writes explicit velocity-projection diagnostics for VTK probe extraction:
  `horizontal_speed(_ratio)`, `abs_streamwise(_ratio)`, `lateral(_ratio)`, signed axis ratios and a
  `component_projection_basis`. `scripts/audit_component_sensitivity.py` includes the new candidates, making wind-sign,
  speed-vs-streamwise and Uref mistakes easier to detect before interpreting systematic bias.
- `docs/validation_metrics_template.csv` is synchronized with the metrics writer fields, including boundary-audit
  hash provenance and selected-component bias/mean diagnostics. A smoke test now fails if future metrics outputs and
  the user-facing template diverge.
- `Read VTK` now emits an explicit `time_averaging_gate` and GH warning when the selected VTK window is unaveraged,
  shorter than 40 frames, does not span at least 20000 solver steps, is not the last available window, non-uniform, or above the stability thresholds.
- `Run Simulation` and `SimulationSettings` now default to `TimeSteps=40000` and `SaveInterval=1000`, producing about
  40 VTK frames for a paper-grade preflight averaging workflow instead of short demo-only output.
- `Run Simulation` now blocks Mode 1/2/3 when the planned `TimeSteps / SaveInterval` window would produce fewer than
  40 VTK frames or fewer than 20000 solver steps. Mode 0 can still generate smoke-test cases, but the metadata marks them as non-validation runs.
- Native/CityLBM run audits now also compute the planned final VTK averaging-window solver-step span from
  `TimeSteps`, `SaveInterval`, `SaveStartStep` and `AverageLastN`; validation fails if the requested final window has
  enough frames but does not cover the minimum solver-step span.
- Native FluidX3D precondition and validation gates now require the runtime VTK source window to be the last available
  window and to include one unique SHA256-traceable VTK file per averaged frame. A long-looking step list without fresh,
  complete final-window file evidence remains diagnostic-only.
- Native time-averaging traceability now carries and rechecks the runtime mean-speed statistics source. CLI or hand
  entered stability statistics cannot pass the native final-window gate unless the archived evidence shows `sampled_vtk`
  statistics with no override.
- `validation_gate.py` now requires `validation_metrics.csv` to come from the same final-window VTK steps recorded in
  the runtime/read-VTK audit; stale metrics or four-frame diagnostic averages are blocked before any paper-grade
  accuracy claim.
- The final time-averaging consistency gate now also requires archived evidence that selected VTK frames are the last
  available window, have strictly increasing time steps and use uniform spacing. A copied `time_averaging_gate=pass`
  label is not enough without those window facts.
- `validation_gate.py` now has a dedicated `validation_protocol_content` gate. Empty
  `validation_protocol_audit.json` files, missing required protocol items, missing statuses or explicit failed protocol
  items block paper-grade evidence before inlet, boundary, time-averaging or bias metrics are interpreted.
- `audit_native_preconditions.py` now applies the same validation-protocol content gate to native FluidX3D baselines,
  preserving missing/failed protocol items in `native_preconditions_gate_reasons` and making incomplete protocol audits
  the first native diagnostic priority.
- `audit_native_preconditions.py` now records numeric time-window shortfall reasons, such as
  `runtime_average_window_frame_count_4_below_minimum_40` or
  `runtime_average_step_span_3000_below_minimum_20000`, so short four-frame baselines remain traceable in downstream
  metrics and diagnostic priorities.
- Native precondition audits and validation metrics now carry the matched uncorrelated-random inlet patterns and the
  recommended next action from `inlet_source_audit.json`, so RMS/k random velocity-field perturbations remain visible as
  a validation blocker in final Case A/E evidence rows.
- Native precondition audits now emit a machine-readable rerun prescription (`native_rerun_prescription_*`) that maps the
  top blocker to the next strict native FluidX3D experiment: inlet U/k preservation, boundary-equivalence evidence,
  longer final-window averaging, probe/component/Uref repair or paired native-vs-CityLBM physics diagnosis.
- `validation_gate.py` now adds `native_inlet_precondition_traceability`, requiring native FluidX3D U/k profile,
  correlation, AF CSV hash, VTK hash and final-window step-span evidence before a native baseline or systematic-bias
  interpretation can pass. Legacy summary-only native audits remain diagnostic.
- Native inlet traceability now also requires source-method evidence that the inlet is paper-grade and distribution
  consistent. A native run can no longer pass this gate with only preserved U/k profiles if the inlet remains STG-lite,
  uncorrelated random forcing or any other macroscopic velocity-field-only route.
- `audit_inlet_source.py` now fails the base inlet-source gate when a setup only names an advanced digital-filter,
  SEM, precursor or recycling method but lacks distribution-function reconstruction, filter state, eddy population or
  recycled-field evidence. This prevents old diagnostic setups from being misread as valid turbulent-inlet sources.
- `validation_gate.py` now adds `native_probe_component_traceability`, requiring native FluidX3D probe IDs, official
  coordinates, projection tolerance, Uref, wind vector, compared component and component-sensitivity source window to
  match the same final averaged VTK window before residual bias can be interpreted.
- Native probe/component traceability now also requires ordered `time_step -> VTK SHA256` pair equality against the
  runtime final window. Matching only the time-step list plus an unordered hash set is no longer enough for probe or
  component-sensitivity evidence.
- `validation_gate.py` now adds `native_boundary_traceability`, requiring native FluidX3D boundary-source code,
  AIJ-equivalent boundary evidence, current metadata hash, boundary evidence file hashes, supported outlet/side/top/
  floor/roughness/fetch fields and case/wind identity before boundary-sensitive bias can be interpreted.
- Native boundary traceability now directly rechecks the generated-source method class and the four required paper-grade
  boundary-source evidence booleans: outlet, side/top, rough-wall and precursor/recycling development-field evidence.
  A wrongly promoted simplified `TYPE_E` box can no longer pass by carrying only a copied `paper_grade_boundary_source_gate=pass`.
- Native validation now includes `boundary_runtime_audit.json`, a final-window VTK boundary-face check for inlet,
  outlet, lateral and top streamwise velocity preservation against the AF profile. This is runtime evidence for
  boundary contamination, not a substitute for wind-tunnel-equivalent outlet/side/top/floor/roughness source evidence.
- Native boundary runtime traceability now also checks that the boundary-runtime audit uses the same final-window
  `source_time_steps` and VTK SHA256 set as the main runtime audit, preventing stale boundary-preservation evidence
  from supporting Case A/E bias interpretation.
- Native inlet profile, inlet correlation and boundary-runtime traceability now require `time_step -> VTK SHA256` pair
  equality against the main runtime final window. Matching only the time-step list and the unordered hash set is no
  longer sufficient for paper-grade native FluidX3D evidence.
- `validation_gate.py` now adds `native_time_averaging_traceability`, requiring native FluidX3D planned and runtime
  final-window frame counts, solver-step span, increasing/uniform source steps and empty shortfall reasons before a
  native baseline or systematic-bias interpretation can pass.
- `case_metadata.json` records protocol-risk fields: simplified boundary-condition summary, expected VTK frame count, required averaging, and validation-readiness status.
- `Run Simulation` no longer falls back to the legacy bundled v0.5.0 solver when no external FluidX3D path is provided; controlled validation must use an explicit external FluidX3D baseline.
- Mode 3 now follows the same explicit FluidX3D source-path rule as Mode 1/2. The legacy bundled solver code path is
  retained for source compatibility but is no longer selected by v0.3.0 validation runs when `FluidX3D Path` is empty.
- `Run Simulation` adds an optional experimental `Synthetic Inlet` control for CustomTable profiles with `k`.
- Generated FluidX3D `setup.cpp` can now use the AF `k` column to apply bounded STG-lite spectral inlet perturbations from `sigma=sqrt(2k/3)`.
- `Run Simulation` now exposes `STG Modes`, and generated `setup.cpp` writes the same value to
  `citylbm_stg_mode_count` instead of hard-coding 12 spectral modes. Strict Case A/E diagnostic baselines can use
  128-384 modes while smoke tests may keep lower values.
- The STG-lite inlet now uses deterministic multi-mode spectral fluctuations, avoiding the earlier sparse-eddy pattern where many inlet cells could receive near-zero perturbation.
- STG-lite spectral modes are now projected normal to their synthetic wave vectors before summation, reducing non-physical divergent inlet fluctuations while keeping the method deterministic and auditable.
- STG-lite temporal evolution now uses Taylor frozen-turbulence phase advection along the local mean wind instead of an arbitrary discrete phase increment, improving time correlation while remaining a diagnostic velocity-field inlet.
- STG-lite now precomputes separate x/y/z component RMS normalization constants for its deterministic projected modes
  and records them in `case_metadata.json`, reducing finite-mode `k -> sigma` drift compared with the earlier single
  `sqrt(6/mode_count)` approximation.
- Synthetic inlet runs now limit each solver advance to `SyntheticTurbulenceUpdateInterval`, so inlet perturbations refresh independently from the VTK save interval.
- `Run Simulation`, `case_metadata.json` and `validation_protocol_audit` now track the expected number of STG-lite inlet
  refreshes inside the final averaging window. Mode 1/2/3 validation runs are blocked when STG-lite is active but the
  averaged window samples fewer than 200 inlet-pattern refreshes; Mode 0 still generates the case as diagnostic-only.
- Interactive `GRAPHICS` runs now use the same STG-lite refresh loop as batch runs, and inlet perturbations are applied only
  to `TYPE_E` inlet nodes so solid ground/building flags are not touched by the diagnostic inlet refresh.
- `setup.cpp`, `case_metadata.json` and `validation_protocol_audit` now explicitly record that STG-lite refreshes macroscopic `lbm.u` only and does not reconstruct FluidX3D distribution functions.
- `case_metadata.json` records whether the synthetic inlet was requested and actually injected, plus synthetic scale, correlation length, update interval and amplitude cap.
- STG-lite injection now requires `k` on every CustomTable profile row. Partial `k` columns remain available for metadata diagnostics but are blocked from turbulent-inlet injection, with `SyntheticTurbulentInletBlockedReason=custom_profile_k_column_incomplete`.
- `Run Simulation` now emits explicit Grasshopper warnings when a complete CustomTable `k` column is present but `Synthetic Inlet` is off, or when STG-lite is enabled but remains a velocity-field-only diagnostic inlet. This prevents validation runs from mistaking metadata-only `k` handling for true turbulent inflow.
- `case_metadata.json`, the native baseline manifest, metrics template and `validation_gate.py` now track the synthetic
  inlet correlation length and its evidence source. A user-selected STG correlation length is treated as diagnostic-only
  until it is replaced or justified by AIJ length-scale data, a precursor/recycling field or a validated DFM/SEM model.
- `audit_inlet_correlation_from_vtk.py`, the metrics template and `validation_gate.py` now report temporal/spatial
  integral positive-lag counts. Inlet fluctuations must retain at least a short multi-lag correlation footprint, so
  lag-1-only or near-white-noise RMS/k perturbations remain diagnostic rather than paper-grade turbulent inflow evidence.
- `validation_gate.py` now treats inlet length-scale evidence as metadata/protocol-audit evidence only. Metrics-table
  `inlet_length_scale_source`, `inlet_length_scale_gate` and `synthetic_correlation_length_m` fields are reported as
  ignored context and cannot pass the length-scale gate by themselves.
- The inlet length-scale gate now also requires `inlet_source_audit.json` evidence from the current `setup.cpp`,
  including detected length-scale source code and a positive synthetic correlation length. Metadata/protocol tags alone
  are not enough for SCI-grade inlet claims.
- `Run Simulation` adds `STG Length Source`, an optional text evidence tag for the STG correlation-length source. Empty
  values preserve the diagnostic-only behavior; accepted evidence tags such as `aij_length_scale_verified`,
  `official_length_scale_verified`, `precursor_length_scale`, `digital_filter_length_scale`,
  `synthetic_eddy_length_scale`, `sem_length_scale`, `dfm_length_scale` or `validated_length_scale_model` are recorded
  in `case_metadata.json`, the native manifest and the validation audit.
- Each generated case now writes `validation_protocol_audit.json` and `.md` to flag inlet, boundary-condition, time-averaging, coordinate, normalization and grid-resolution readiness before metrics are interpreted.
- `probe_vtk_points.py` now records the VTK physical grid extent for every sampled probe and hard-fails probes outside
  that extent before nearest/trilinear interpolation, so incorrect STL scale, `domain_origin` or RS coordinate
  transforms cannot be hidden by clamping samples to the VTK boundary.
- `probe_vtk_points.py` now supports official probe-set gates (`--expected-row-count`, `--expected-z`) and
  `validation_metrics_from_probe_audit.py` carries the resulting `official_probe_set_*` evidence. AIJ Case E `ac + N`
  post-processing can now fail before metrics if the filtered official subset is not exactly the 80 pedestrian-height
  `z=2.0 m` probes, preventing partial, wrong-condition or wrong-height RS comparisons from being interpreted as
  validation accuracy.
- `case_metadata.json`, the native baseline manifest and validation metrics now record the geometry-unit assumption,
  building count/height and a geometry-scale evidence gate. The metadata explicitly states that CityLBM expects real-scale
  meter geometry and that the official AIJ Case E `BD_caseE.stl` model-scale geometry must be scaled by 250 before
  adding buildings.
- `case_metadata.json` and the native baseline manifest now include `BoundaryProtocolAudit`, a structured record of
  inlet/outlet/lateral/top faces, domain clearances in meters and building-height units, simplified boundary types and a
  diagnostic boundary-clearance gate.
- `BoundaryProtocolAudit` now also records per-condition clearance booleans and gate reasons, so undersized or misplaced
  domains fail explicitly instead of only reporting aggregate clearance ratios.
- `case_metadata.json`, the native baseline manifest, metrics template and `validation_gate.py` now separate diagnostic
  boundary clearance/blockage from AIJ-equivalent boundary evidence. Clearances alone no longer pass the boundary gate
  unless the run also archives an official AIJ/empty-tunnel/validated-boundary evidence source.
- Added `scripts/audit_boundary_protocol.py` and wired it into `scripts/run_native_validation_chain.py`. Each post-run
  evidence chain now writes `boundary_protocol_audit.json`; without an explicit AIJ boundary/fetch/roughness evidence
  JSON the boundary gate remains diagnostic/failing instead of treating domain clearance as a paper-grade match.
- `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py` now carry
  `boundary_protocol_audit` and `boundary_missing_evidence_fields`, making missing inlet/outlet/lateral/top, roughness,
  blockage-source and fetch-clearance evidence visible in the metrics row and final gate report.
- `audit_boundary_protocol.py` now requires structured AIJ-equivalence evidence, not only `boundary_evidence_gate=pass`.
  The external evidence or generated metadata must expose `boundary_equivalence_basis`, upstream/downstream/lateral/top
  clearance in building-height units, floor roughness source, outlet reflection check and side/top boundary check. The
  final validation gate now reports `boundary_equivalence_supported`, `clearance_numeric_gate` and clearance reasons.
- `audit_native_preconditions.py` and the metrics CSV now preserve native boundary-protocol details, including missing
  AIJ evidence fields, unsupported boundary-condition fields, required support booleans, clearance reasons and evidence
  file hash failures. A native baseline with simplified or undocumented boundary/fetch/roughness assumptions now points
  to the exact missing evidence instead of only reporting a generic boundary failure.
- Boundary support files are now read and SHA256-hashed by `audit_boundary_protocol.py`. Empty, unreadable or
  existence-only files keep `boundary_evidence_files_all_hashed=false`, and the final validation gate fails until the
  evidence artifacts are non-empty and traceable in the run archive.
- `validation_gate.py` now requires boundary-equivalence support, evidence-file hashes, supported boundary-condition
  fields and clearance checks to come from the archived `boundary_protocol_audit.json` itself. Metrics CSV fields can
  no longer self-report those boundary evidence booleans in place of the external audit file.
- `audit_native_preconditions.py` now independently requires the archived boundary protocol audit to expose
  boundary-equivalence support, supported evidence class, supported boundary-condition fields, blockage/clearance gates
  and all inlet/outlet/lateral/top/roughness/reflection support booleans before a native FluidX3D Case A/E run can be
  used as the strict baseline for CityLBM error diagnosis.
- `audit_boundary_source.py`, `case_metadata.json`, the native baseline manifest, metrics template and
  `validation_gate.py` now require concrete boundary-source evidence for a paper-grade AIJ boundary claim: a
  non-reflecting or validated outlet state, side/top pair mapping or wind-tunnel-equivalent treatment, rough-wall or
  wall-function action, precursor/recycling development-field evidence and official blockage/fetch/clearance evidence.
  The current TYPE_E/TYPE_S box boundary is therefore explicitly classified as diagnostic-only instead of being allowed
  to support SCI-grade accuracy claims.
- `audit_native_preconditions.py` and the metrics CSV now report the top blocking diagnostic priority and next action,
  so a failing Case A/E package points first to inlet U/k turbulence evidence, then boundary evidence, time averaging,
  coordinate/component/Uref closure and residual systematic bias.
- `audit_native_preconditions.py`, `validation_gate.py` and the metrics CSV now also emit a structured
  `native_precondition_closure` stage matrix. Native FluidX3D baselines must close validation protocol content, turbulent
  inlet U/k/correlation, boundary/roughness/blockage, final-window averaging, coordinate/component/Uref normalization and
  residual grid/bias interpretation in order before any CityLBM accuracy claim can pass.
- The metrics CSV now also carries native-baseline inlet-profile and inlet-correlation gates from
  `native_preconditions_audit.json`, including AF CSV hash match, U/k profile preservation, source-window/runtime hash
  matching and minimum step-span fields. A native FluidX3D row can therefore show exactly whether the AF `U/k` inlet and
  correlated turbulence evidence were proven before CityLBM parity or residual bias are interpreted.
- `audit_native_preconditions.py` now promotes uncorrelated RMS/k random inlet forcing from the inlet-source audit into
  the native baseline precondition reasons, preserving the exact blocker instead of collapsing it into a generic inlet
  failure.
- `validation_gate.py` now propagates the native-preconditions top blocker into the final `diagnostic_priority`, so the
  final gate report preserves the same first-action diagnosis instead of only reporting a generic native-baseline
  failure.
- `audit_boundary_protocol.py`, the metrics template and `validation_gate.py` now require independent support booleans
  for inlet, outlet, lateral, top, ground-wall treatment, roughness treatment, floor roughness source, blockage source,
  fetch/clearance source, outlet-reflection check and side/top-boundary check. A text-filled evidence JSON with values
  such as `unknown`, `unverified`, `not_checked`, `diagnostic_only` or `assumed_only` remains diagnostic even when
  `boundary_evidence_gate=pass` is present.
- `case_metadata.json` and `validation_protocol_audit` now separate analytic inflow roughness from actual wall treatment:
  ground/buildings remain `TYPE_S` no-slip in v0.3.0, with no FluidX3D rough-wall or wall-function boundary.
- The validation audit now also records native FluidX3D baseline requirement, LBM stability scaling, wind-direction sign,
  probe-projection risk and systematic-bias gate so the known `-34 pp` underprediction pattern is treated as a protocol
  blocker rather than a tuning target.
- `validation_gate.py` and `audit_native_preconditions.py` now report diagnostic priority in the CFD-validation order:
  turbulent inlet U/k/correlation first, boundary/roughness/blockage second, final-window time averaging third,
  coordinate/component/Uref/probe mapping fourth, and residual systematic bias only after those prerequisites.
- `docs/validation_metrics_template.csv` now includes run-evidence fields for source time steps, CustomTable `k`
  completeness/ranges, compared velocity component, averaged-field stability, boundary summary, synthetic inlet method,
  inlet distribution treatment, wall roughness treatment, native baseline id, probe mapping distances and protocol gate.
- `validation_metrics_from_probe_audit.py` now writes SHA256 hashes for the probe audit table and official measurement
  table, and `validation_gate.py` requires those hashes to match the current `--probe-audit` and `--official` inputs.
  A copied metrics row can no longer pass coordinate/component/Uref diagnostics for a different probe extraction or RS
  table.
- Official measurement filtering is now strict in both `validation_metrics_from_probe_audit.py` and
  `validation_gate.py`: when `--case` or `--wind-direction` is requested, the official RS table must expose a matching
  case/condition or wind/direction column and the filtered subset must be non-empty. This prevents Case E `bc/ac` rows
  or other wind directions from silently entering the reported error statistics and final gate.
- `validation_metrics_from_probe_audit.py` now records `probe_uref_expected_mps`, `probe_uref_values` and
  `probe_uref_mismatch_count`; when the command-level Uref differs from the per-probe audit Uref, the metrics
  `protocol_gate` fails with `fail_probe_uref_mismatch`. `validation_gate.py` now includes a `metrics_protocol` gate so
  these internal coordinate/component/Uref protocol failures cannot be ignored by later accuracy checks.
- `audit_component_sensitivity.py` now uses the same lowercase alphanumeric probe-ID normalization as the main metrics
  and gate scripts, and rejects duplicate official IDs after normalization. Component/Uref sensitivity checks therefore
  compare the same official points as the final metrics join.
- `validation_gate.py` now reads inlet-correlation pass/fail, temporal lag-1 correlation, spatial adjacent correlation,
  streamwise fluctuation variance and finite-correlation coverage only from `inlet_correlation_audit.json`. Metrics CSV
  fields with the same names are ignored context, so turbulent-inlet evidence must come from the archived VTK audit.
- `Data Probe` now appends validation-audit outputs for `Uref`-based speed ratio, streamwise ratio, nearest VTK-sample
  distance and per-probe CSV rows without changing the existing first five outputs.
- `Data Probe` now accepts optional official probe IDs, a probe-to-VTK tolerance and an explicit compared component.
  Its audit CSV records the selected comparison value and flags probes with no VTK neighbor, invalid comparison value
  or out-of-tolerance mapping.
- `Data Probe` audit CSV now records the wind-vector components, `wind_direction_valid` and `normalization_valid`, so
  speed-ratio and streamwise-ratio comparisons can be traced instead of inferred from the GH canvas.
- `Data Probe` spatial hashing now uses floor-based cell indices for negative coordinates and applies the configured
  search radius as a real distance filter. This fixes probe-neighbor ambiguity for AIJ domains with negative `x/y`
  coordinates and makes the nearest-distance/tolerance audit meaningful.
- Each generated case now also writes `native_fluidx3d_baseline_manifest.json` and `.md` so native FluidX3D and
  CityLBM-driven runs must archive the same `setup.cpp`, `defines.hpp`, geometry, metadata, averaging window and probe
  audit evidence before any paper-grade accuracy claim.
- Added `scripts/run_native_fluidx3d_case.py` as the pre-run native FluidX3D preparation entry point. It validates an
  explicitly supplied FluidX3D source root, can install a CityLBM-generated `setup.cpp`/`defines.hpp` into that source
  tree with backups, optionally builds/runs the executable, and writes the hash-traceable native baseline manifest. The
  default mode is dry-run preflight and does not start CFD.
- `scripts/run_native_fluidx3d_case.py` now also fails fast to diagnostic-only when the generated case lacks
  `validation_protocol_audit.json`, when expected case/wind identity is missing or mismatched, or when the planned VTK
  schedule cannot provide the default 40-frame / 20000-step final averaging window.
- `scripts/run_native_fluidx3d_case.py` now audits the content of `validation_protocol_audit.json`. Empty audit files,
  missing protocol items, missing item statuses or explicit failed protocol items are diagnostic-only, so a native
  FluidX3D baseline cannot pass merely because the audit file exists.
- The native baseline manifest now includes existence flags and SHA256 hashes for the generated source, geometry and
  metadata files so paired native/CityLBM runs can prove they used identical inputs.
- The native baseline manifest now includes a stable `BaselineId`, derived from the scene name and required source hashes,
  so metrics and `validation_gate.py` can trace a completed native FluidX3D baseline without relying on manual labels.
- `docs/CaseA_native_baseline_protocol.md` defines the native FluidX3D Case A promotion gate: empty-tunnel `U/k`
  preservation, inlet distribution-consistency treatment, post-spinup averaging, official probe IDs, tolerance-based
  probe mapping and CityLBM-vs-native equivalence must be archived before Case E is promoted as SCI-grade validation.
- `scripts/validation_gate.py` now audits completed run packages and fails diagnostic-only evidence that lacks metrics,
  empty-tunnel `U/k` preservation, native baseline linkage, valid wind/normalization flags, probe mapping, time averaging
  or bounded mean/k errors.
- `scripts/validation_gate.py` now requires the native baseline manifest to prove an explicitly supplied FluidX3D source
  path, a passing source-tree validation record and SHA256 hashes for the native `setup.cpp`, `defines.hpp`, `lbm.hpp`
  and `lbm.cpp`; a metrics row can no longer self-report `native_baseline_gate=pass` without this evidence.
- `scripts/validation_gate.py` now also requires `native_fluidx3d_baseline_id` in the metrics row to match the manifest
  `BaselineId`, preventing copied or manually mistyped native-baseline labels from passing the evidence gate.
- `scripts/validation_gate.py` now requires the per-probe `Data Probe` audit CSV for coordinate, normalization and
  compared-component traceability. Summary-only metrics are allowed only through an explicit diagnostic override and
  should not be used for paper-grade validation claims.
- `--allow-summary-only-probe-metrics` is now diagnostic-only in the machine gate. It may downgrade missing legacy
  probe-audit traceability to a warning, but it can no longer make `coordinate_normalization`, `compared_component` or
  `probe_mapping` pass from summary metrics.
- `scripts/validation_gate.py` now computes official-coordinate delta coverage from the per-probe audit rows by default.
  `max_official_coordinate_delta_m` and `official_coordinate_delta_count` in `validation_metrics.csv` are summaries only
  and cannot replace `probe_audit.csv` for paper-grade coordinate closure.
- `scripts/validation_gate.py` now recomputes per-probe official-coordinate deltas from the current official
  RS/measurement CSV when the Grasshopper Data Probe audit does not already contain `official_coordinate_delta`. This
  keeps coordinate closure tied to the archived official table and avoids requiring GH users to hand-author derived
  coordinate-delta columns.
- `scripts/audit_native_preconditions.py` and `scripts/run_native_validation_chain.py` now use the same official
  RS/measurement CSV fallback for native-baseline probe coordinate closure, so the native precondition gate and final
  validation gate no longer disagree about Grasshopper-exported probe audits that omit derived coordinate-delta fields.
- `scripts/audit_native_preconditions.py` now also requires one-to-one official probe coverage for the selected
  case/wind subset: missing probe IDs, duplicate probe IDs, extra probe IDs or omitted official measurement points keep
  the native baseline diagnostic instead of allowing a partial matched subset to support accuracy claims.
- `scripts/audit_native_preconditions.py` now treats `OutOfTolerance=true` and failing/invalid validation-status fields
  as failed probe rows, and accepts common PascalCase VTK source-window column names. Native baselines therefore cannot
  pass by exporting a probe audit with nonstandard status or source-hash headers.
- `scripts/audit_native_preconditions.py` now requires the per-probe audit table to carry a unique VTK source-window
  step span and minimum validation step-span field. The probe table must match the runtime-selected VTK window and meet
  the minimum averaging span before a native FluidX3D baseline can be promoted beyond diagnostic evidence.
- Native preconditions now recompute the runtime VTK source-window step span from the archived `source_time_steps` and
  require it to match the reported runtime `source_step_span`. A hand-entered or stale span value can no longer hide a
  short final averaging window.
- Native preconditions now apply the same source-step-span closure to `inlet_profile_audit.json` and
  `inlet_correlation_audit.json`. Inlet `U/k` preservation and turbulence-correlation evidence must therefore prove
  their own averaging-window span from archived source time steps, not only from a copied summary field.
- Grasshopper runtime and result-reading thresholds are now aligned with the final validation gate: `Run Simulation`
  blocks Mode 1/2/3 validation runs below 40 saved VTK frames or a 20000-step final averaging span, and `Read VTK`
  records `source_step_span`, `source_step_span_shortfall` and `minimum_validation_average_step_span` in `AvgAudit`.
  Four-frame late-window outputs are therefore preserved as smoke/diagnostic evidence rather than paper-grade averages.
- The STG-lite inlet refresh now applies a two-pass inlet-face mean correction before writing TYPE_E velocities, so finite
  spectral-mode and amplitude-capped fluctuations preserve the CustomTable mean `U(z)` profile instead of injecting a
  bulk velocity drift. `audit_inlet_source.py`, native preconditions and the metrics CSV expose
  `has_mean_preserving_inlet_correction`; STG-lite remains velocity-field-only and diagnostic until distribution-function
  reconstruction or native inlet-preservation evidence closes.
- Native preconditions now recompute strict monotonicity and uniform spacing for runtime, inlet-profile,
  inlet-correlation and probe source time steps. Non-final, reordered, duplicated or uneven VTK windows remain
  diagnostic even if an audit JSON reports `time_averaging_gate=pass`.
- `scripts/validation_gate.py` now rechecks valid per-probe IDs against the current official RS/measurement table:
  every valid probe row must have a non-empty unique ID, and each ID must exist in the official table before
  coordinate/Uref/compared-component diagnostics can pass.
- `validation_metrics_from_probe_audit.py`, `validation_metrics_template.csv` and `validation_gate.py` now close the
  reverse probe-coverage check: every official probe ID for the selected case/wind must be represented exactly once by
  a valid probe row. Missing official probes now set `fail_incomplete_official_probe_coverage` and keep the run
  diagnostic, even if the remaining matched subset has good error statistics.
  The final gate also cross-checks the metrics-row coverage fields against the per-probe audit recomputation.
- `validation_metrics_from_probe_audit.py` now uses the same normalized probe-ID matching rule as `validation_gate.py`
  when joining probe rows to official RS measurements, and rejects duplicate official IDs after normalization. Metrics
  construction and final gate coverage can no longer silently disagree because of case, spacing or punctuation in AIJ
  point labels.
- `audit_component_sensitivity.py`, `validation_metrics_from_probe_audit.py`, the metrics template and
  `validation_gate.py` now bind component/Uref sensitivity evidence to the same case and wind-direction subset as the
  audited run. The final gate fails component audits reused from another AIJ condition or wind direction even when the
  probe CSV and official measurement file hashes match.
- `validation_gate.py` now handles zero-RMSE or otherwise undefined scale-improvement component audits without treating
  them as evidence of a Uref/unit problem when the best-fit scale is already near unity.
- `scripts/validation_gate.py` now requires component/Uref sensitivity values to come from archived
  `component_sensitivity_audit.json`; metrics rows may point to that audit, but can no longer self-report
  component-normalization pass fields, best component, RMSE comparison or best-fit Uref scale.
- `validation_gate.py` now requires `component_sensitivity_audit.json` to be physically archived in the audited run
  package. A metrics-table `component_sensitivity_audit` path is reported as ignored context and can no longer point the
  gate to an external or stale component/Uref sensitivity JSON.
- `audit_boundary_source.py` now evaluates TYPE_E/TYPE_S assignments, profile inlet, outlet/lateral/top boundaries and
  rough-wall/precursor evidence from comment-stripped `setup.cpp` code. Boundary keywords or pseudo-code in comments are
  retained only as diagnostics and can no longer support a boundary-source gate.
- `audit_inlet_source.py` and `audit_boundary_source.py` now strip C++ string/character literals before classifying
  advanced inlet or boundary implementations. Labels such as `"digital_filter"`, `"SEM"`, `"non_reflecting"` or
  `"rough_wall"` are reported as token-only diagnostics unless the generated `setup.cpp` also contains call/array/field
  code evidence for the claimed method.
- `audit_boundary_source.py` now also applies string-literal stripping to advanced boundary token diagnostics themselves,
  so UI labels, log strings or explanatory constants cannot trigger `advanced_boundary_token_only` without real outlet,
  side/top, rough-wall or precursor/recycling implementation code.
- `audit_inlet_source.py` now checks CustomTable code for `profile_origin_z_m` and origin-aware physical-height
  sampling. A generated inlet that falls back to a hard-coded zero vertical datum is rejected by the source audit.
- `audit_boundary_source.py` now separates advanced boundary method names from concrete implementation evidence. A
  named `non_reflecting`, `periodic`, `rough_wall`, `precursor` or `recycling` function is no longer enough: the audit
  also looks for sponge/convective/radiation outlet state, periodic pair mapping, rough-wall parameter plus wall-action
  code, or recycled/precursor field evidence before the boundary source can be promoted.
- `audit_boundary_source.py`, `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py`
  now explicitly audit the CityLBM TYPE_E boundary-velocity initialization pass. Simplified/profile TYPE_E boundary
  cases must show the generated guard on `lbm.flags[n]`, coordinate recovery and three-component `lbm.u` writes; profile
  inlet cases must also show that outlet/lateral/top TYPE_E nodes are initialized from `windProfile(z)`. This prevents a
  run package from passing source traceability while retaining the older zero-speed outlet/lateral/top damping risk.
- `case_metadata.json`, the native baseline manifest and validation metrics now also preserve the TYPE_E boundary-velocity
  initialization treatment, profile-awareness, device-upload ordering and diagnostic-only paper-grade status. This makes
  the damping mitigation visible in archived Case A/E packages without treating it as wind-tunnel-equivalent boundary
  physics.
- `audit_boundary_source.py` now treats coherent `TYPE_E`/`TYPE_S` assignments in generated `setup.cpp` as source
  evidence even when `EQUILIBRIUM_BOUNDARIES` is defined in `defines.hpp`, and it no longer interprets negative metadata
  statements such as `no rough-wall function` as advanced-boundary claims. The correct current classification is
  source-traceable simplified boundary (`boundary_source_gate=pass`) but non-paper-grade boundary
  (`paper_grade_boundary_source_gate=fail`).
- Native FluidX3D baseline gating now recomputes SHA256 hashes for the manifest-listed `setup.cpp`, `defines.hpp`,
  `lbm.hpp` and `lbm.cpp` paths. A manifest can no longer pass by declaring `Exists=true` with a non-empty hash if the
  local source file is missing or has changed.
- `validation_gate.py` now binds `inlet_source_audit.json` and `boundary_source_audit.json` to the current run's
  `setup.cpp` SHA256. Source audits copied from an older generated case fail even if their internal gate fields say
  `pass`.
- `validation_gate.py` now recomputes SHA256 for every file listed in `boundary_protocol_audit.json`
  `boundary_evidence_files_sha256`. Boundary support files copied, edited, removed or incompletely hashed after the
  protocol audit keep the run diagnostic even if the audit JSON still says `boundary_evidence_files_all_hashed=true`.
- `case_metadata.json`, the native baseline manifest, metrics template and `validation_gate.py` now track LBM stability
  evidence: target lattice velocity, estimated Mach number, `tau`, `nu_lbm`, physical viscosity, Reynolds number,
  velocity set, LES/subgrid model and solver-log stability warnings. A generated case is not enough; the machine gate
  requires runtime stability evidence before treating native FluidX3D or CityLBM results as paper-grade.
- Generated `setup.cpp` and `defines.hpp` now compute lattice viscosity from the same velocity-scale contract used for
  the inlet profile: `nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx`. CityLBM no longer silently clamps `tau` to
  `0.55`, because that changes the physical Reynolds number and can create artificial diffusion and systematic
  underprediction. Runs with `tau` too close to 0.5 must be handled by the stability gate, solver logs, grid/scale
  choices and LES evidence rather than by hidden viscosity inflation.
- Added `scripts/audit_native_run.py` to turn a native FluidX3D run directory into a reusable audit JSON containing VTK
  frame hashes, selected final time steps, time-averaging gate fields, solver-log stability warning status and LBM
  stability metadata for downstream metrics/gate checks.
- `scripts/audit_native_run.py` now writes `strict_native_run_gate` and supports `--strict`; diagnostic audits still
  produce JSON, but a native run with stale VTK, too few averaging frames, insufficient final-window span, stationarity
  failure or missing/dirty solver log returns a non-zero code when strict checking is requested.
- `strict_native_run_gate` is now propagated into `audit_native_preconditions.py`,
  `validation_metrics_from_probe_audit.py`, `docs/validation_metrics_template.csv` and `validation_gate.py`. A native
  baseline with failed freshness, requested-frame, final-window, stationarity or solver-log evidence is blocked in the
  final metrics/gate package, not only at the standalone command-line audit.
- `scripts/audit_native_run.py` now computes time-stability ratios directly from real VTK velocity time series when the
  ratios are not supplied on the command line. It deterministically samples up to 20,000 points across the selected final
  frames, records the sampling method, and feeds `mean_speed_stddev_ratio` / `max_speed_stddev_ratio` into the same
  time-averaging gate used by Grasshopper `Read VTK`.
- `scripts/audit_native_run.py`, `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py`
  now carry `run_freshness_gate`, `latest_reference_mtime_utc` and `oldest_selected_vtk_mtime_utc`, so stale VTK frames
  copied from older setups cannot be promoted as newly generated Case A/E evidence.
- `validation_gate.py` now reads run-freshness and solver-stability pass/fail evidence from archived
  `native_run_audit.json` or Read VTK audit JSON. Metrics rows may summarize these fields, but can no longer self-report
  fresh VTK output or clean solver stability without the runtime audit artifact.
- `validation_gate.py` now also reads the paper-grade `time_averaging` gate from the runtime audit artifact only:
  averaged frame count, source time steps, final-window selection, requested VTK frame preflight and sampled stability
  ratios cannot be self-reported from `validation_metrics.csv`.
- `validation_gate.py` now independently recomputes the requested VTK output steps from archived
  `requested_time_steps`, `requested_vtk_save_interval` and `requested_vtk_save_start_step`, and rechecks that
  `source_time_steps` are the final window of both the requested output schedule and `all_available_time_steps`.
- `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py` now carry
  `probe_vtk_source_window_gate`, probe source time steps and probe VTK hash-set counts. Valid probe rows must use the
  same final-window VTK frames as the averaging and inlet-profile/correlation audits, or the new `probe_source_window`
  gate keeps the run diagnostic.
- `validation_gate.py` now reads grid-sensitivity and native/CityLBM parity pass evidence from
  `grid_sensitivity_audit.json` and `native_citylbm_parity_audit.json` only. Metrics rows can summarize those audits,
  but cannot self-report grid convergence or native/CityLBM condition matching.
- `scripts/audit_native_citylbm_parity.py` now compares paper-critical gate states and evidence hashes in addition to
  nominal case settings. Native/CityLBM rows must match AF profile SHA256, official measurement SHA256, component
  sensitivity official SHA256, inlet/boundary `setup.cpp` source-audit hashes and key inlet/boundary/probe/time gates
  before CityLBM accuracy is interpreted against native FluidX3D.
- `validation_metrics_from_probe_audit.py` now records native/CityLBM parity comparison coverage counts, and
  `validation_gate.py` fails CityLBM paper-grade promotion unless the archived parity audit includes enough gate-field
  coverage and all required evidence-hash comparisons.
- `scripts/audit_native_citylbm_parity.py` and `validation_gate.py` now require explicit critical parity fields, not
  just aggregate match counts. Case/wind, dx, VTK cadence, averaging, Uref, inlet/boundary/probe gates and AF/official/
  source-audit hashes must all be present and matched before CityLBM accuracy can be interpreted against native
  FluidX3D.
- Added `scripts/audit_native_citylbm_accuracy_delta.py` and a `native_citylbm_accuracy_delta` validation gate to
  quantify whether CityLBM adds RMSE, bias, R2, regression-slope or intercept error beyond a paired native FluidX3D
  run. If CityLBM matches a poor native baseline, the result remains a native protocol/physics limitation; if CityLBM
  is worse than the paired native run, the gate points back to parameter transfer, `setup.cpp`, VTK scaling and probe
  postprocessing.
- Added `scripts/audit_inlet_profile_from_vtk.py` to read real post-spinup `u-*.vtk` frames, sample an inlet or
  empty-tunnel cross-plane, reconstruct time-mean streamwise `U(z)` and temporal-variance `k(z)`, and compare both
  against the official AF table. This replaces hand-filled empty-tunnel `U/k` evidence with an archived JSON/CSV audit.
- `validation_gate.py` now requires `inlet_profile_audit.json` and reads inlet `U/k` preservation, streamwise-direction
  and inlet-window pass/fail evidence from that audit JSON only. Metrics rows can summarize inlet profile results, but
  cannot self-report AF profile preservation.
- `scripts/audit_inlet_profile_from_vtk.py` now records all available VTK steps and fails the inlet `U/k` gate when the
  selected average is not an explicit final window with strictly increasing, uniformly spaced time steps. This prevents
  short or non-final inlet samples from being interpreted as solver accuracy evidence.
- `validation_gate.py` now requires the inlet `U/k` preservation audit to use exactly the same `source_time_steps` as the
  global runtime averaging audit. A separate final-window inlet profile sample can no longer be combined with probe or
  correlation evidence from a different VTK window.
- `scripts/audit_inlet_profile_from_vtk.py`, `validation_metrics_from_probe_audit.py`, the metrics template and
  `validation_gate.py` now carry an inlet streamwise-direction gate. If more than 5% of sampled inlet velocities project
  opposite to the declared wind vector, the inlet profile gate fails before wind-sign or compared-component mistakes can
  be mistaken for solver accuracy error.
- Added `scripts/audit_inlet_correlation_from_vtk.py` and wired it into the native validation chain, metrics builder
  and final gate. This checks real final-window inlet VTK frames for streamwise fluctuation variance, temporal lag-1
  correlation and adjacent spatial correlation, so a run cannot rely on RMS/k preservation alone to claim correlated
  turbulent inflow.
- The final `inlet_correlation` gate now independently checks correlation source-window parity and numeric thresholds:
  source time steps must match the global averaged VTK window, the audit must use a final uniformly spaced window, and
  streamwise variance, temporal lag-1 correlation and spatial adjacent correlation must exceed configured minima.
- The inlet correlation audit now gates on signed positive temporal lag-1 correlation, not only absolute lag-1
  correlation. This prevents alternating or white-noise-like RMS/k perturbations from passing as physically correlated
  turbulent inflow evidence.
- `audit_inlet_correlation_from_vtk.py` and `validation_gate.py` now require a minimum inlet-plane sample count and
  adjacent spatial-pair count in addition to finite temporal/spatial correlation fractions. Sparse final-window samples
  can no longer pass the turbulent-inlet correlation gate by reporting high fractions over too few points.
- `audit_inlet_correlation_from_vtk.py` now writes a structured failing audit JSON when VTK discovery, metadata reading,
  inlet-plane selection or vector extraction fails, so missing or unreadable inlet-correlation evidence remains archived
  as an explicit protocol failure instead of disappearing as a missing file.
- `validation_gate.py` now requires inlet-source and inlet-correlation pass evidence to come from the archived
  `inlet_source_audit.json` and `inlet_correlation_audit.json` values themselves. Metrics CSV fields can summarize
  those audits, but cannot replace the generated-source hash or final-window VTK correlation audit.
- `validation_gate.py` now requires `inlet_correlation_audit.json` to be physically archived in the audited run package.
  A metrics-table `inlet_correlation_audit` path is reported as ignored context and can no longer point the gate to an
  external or stale correlation JSON.
- `scripts/validation_metrics_from_probe_audit.py` converts Grasshopper `Data Probe` audit rows plus official RS tables
  into the standard metrics CSV, including matched probe count, coordinate deltas, selected component, normalization flags,
  regression diagnostics and systematic low-bias detection.
- `scripts/validation_metrics_from_probe_audit.py` can now ingest the inlet-profile audit JSON and write
  `inlet_profile_gate`, `inlet_u_profile_gate`, `inlet_k_profile_gate`, `inlet_u_mae_ratio`, `inlet_u_rmse_ratio`,
  `inlet_k_mae_ratio` and `inlet_k_rmse_ratio`
  into the standard metrics row.
- Inlet-profile audits now compute `U_RMSE` and `k_RMSE` from the real post-spinup VTK frame window. The standard
  metrics row carries `k_RMSE_m2s2` and `k_RMSE_ratio`, and `validation_gate.py` requires the k RMSE ratio in addition
  to k bias so local turbulent-energy errors cannot be hidden by cancellation.
- For native FluidX3D baselines, `scripts/validation_metrics_from_probe_audit.py` now falls back to
  `audit_inlet_profile_from_vtk.py` time-window evidence when a Grasshopper Read VTK audit is not present. The standard
  metrics row can therefore carry `available_frame_count`, `source_first_time_step`, `source_last_time_step`,
  `latest_available_time_step`, `selected_last_window`, source-step monotonicity and spacing from the same real VTK
  inlet-profile audit used for `U/k` preservation.
- Time-averaging stability metrics now carry `mean_speed_statistics_source`; `validation_gate.py` only accepts sampled
  VTK/audit-derived stability statistics, so command-line or hand-entered standard-deviation ratios cannot satisfy the
  paper-grade averaging gate.
- `audit_native_run.py`, `validation_metrics_from_probe_audit.py`, `validation_gate.py` and
  `run_native_validation_chain.py` now record and enforce the final-window solver-step span. A run can no longer pass
  paper-grade time averaging solely by saving many closely spaced VTK frames; the default minimum span is `20000` solver
  steps via `--min-avg-step-span`.
- Inlet U/k preservation and inlet-correlation audits now use the same minimum final-window step-span rule. The
  validation gate rejects inlet-profile or inlet-correlation evidence when its archived source VTK window is too short,
  even if it has the minimum number of frames.
- `scripts/audit_inlet_profile_from_vtk.py` now also computes `mean_speed_stddev_ratio` and
  `max_speed_stddev_ratio` from pointwise speed-magnitude time series on the selected final-window plane. Native
  baseline metrics can inherit these stationarity fields from the inlet-profile audit when no Grasshopper `Read VTK`
  audit exists.
- `scripts/validation_gate.py` now has a separate `inlet_profile_preservation` gate. Paper-grade validation fails when
  real VTK frames do not prove that the requested AF `U(z)` and `k(z)` are preserved at the inlet/empty-tunnel audit
  plane.
- `validation_gate.py` now adds a separate `paper_grade_inlet_method` gate. The diagnostic
  `--allow-velocity-only-inlet` override can no longer make a velocity-field-only STG-lite run paper-grade; formal
  validation still requires a distribution-consistent digital-filter, SEM/DFM, precursor or recycling inlet plus
  final-window U/k preservation evidence.
- Added `scripts/audit_inlet_source.py` and wired `inlet_source_audit.json` into the metrics template, native validation
  chain and final gate. The audit hashes the generated `setup.cpp`, classifies the actual inlet implementation and fails
  paper-grade promotion when a method is only velocity-field forcing or when metadata claims distribution consistency
  without matching source evidence.
- `scripts/audit_inlet_source.py` now distinguishes correlated STG-lite source evidence from uncorrelated velocity-only
  perturbations. It recognizes `citylbm_stg_corr_cells`, spectral modes, Taylor frozen-turbulence advection and transverse
  wave-vector projection, while still marking the method as velocity-field-only and non-paper-grade until the inlet is
  distribution-consistent.
- `scripts/audit_inlet_source.py` now reads `citylbm_stg_mode_count` from generated `setup.cpp` and fails the inlet
  source gate when a synthetic inlet uses fewer than 32 spectral modes, preventing a stale low-mode diagnostic setup
  from being mistaken for the documented strict STG-lite baseline.
- `scripts/audit_inlet_source.py` now also checks that `SyntheticTurbulenceUpdateInterval` is wired into the generated
  solver loop: STG-lite must refresh with the current `lbm.get_t()` and the refresh must be coupled to a segmented
  `lbm.run(steps_to_run)` advance. A token-only `citylbm_stg_update_interval` constant no longer passes the source audit.
- `scripts/audit_inlet_source.py` now removes C/C++ comments before classifying advanced inlet methods. Method names
  that appear only in comments, such as "not a full digital-filter/SEM/precursor inlet", no longer count as
  distribution-consistent source evidence.
- `scripts/audit_inlet_source.py`, the metrics template and `validation_gate.py` now distinguish generic distribution
  function tokens from inlet-context distribution reconstruction. Digital-filter or SEM/DFM source claims require
  `has_inlet_distribution_reconstruction=true`; stray `lbm.f`, `feq` or `stress_ddf` code outside an inlet/`TYPE_E`
  reconstruction context is recorded as diagnostic evidence but cannot make the inlet paper-grade.
- `scripts/audit_inlet_source.py` now requires method-specific advanced-inlet evidence before classifying an inlet as
  distribution-consistent: digital-filter/DFM claims must expose a filter kernel and spatiotemporal filter state, SEM
  claims must expose an eddy-population state, and precursor/recycling claims must expose recycled or precursor field
  evidence. A method function name alone is reported as named-method-only evidence and fails paper-grade inlet source
  promotion.
- `validation_gate.py`, `validation_metrics_from_probe_audit.py` and `docs/validation_metrics_template.csv` now carry the
  same STG run-loop evidence fields. A stale `inlet_source_audit.json` without those fields no longer satisfies
  `inlet_source_evidence` for STG-like inlets.
- Added `scripts/audit_boundary_source.py` and wired `boundary_source_audit.json` into the metrics template, native
  validation chain and final gate. The audit hashes the generated `setup.cpp`, classifies the actual boundary source
  implementation, and keeps simplified `TYPE_E` outlet/lateral/top plus no-slip-only floor/buildings from satisfying
  paper-grade boundary protocol claims.
- `scripts/audit_boundary_source.py` now treats `TYPE_E`/`TYPE_S` symbol usage in generated `setup.cpp` as boundary-source
  evidence even when the constants are defined in included FluidX3D headers. This prevents coherent simplified boundary
  setups from being misreported as missing source, while still failing the paper-grade wind-tunnel-equivalence gate.
- `scripts/audit_boundary_source.py` now strips C++ comments before accepting advanced boundary evidence such as
  non-reflecting outlet, periodic side/top, rough-wall, precursor or recycling tokens. `validation_gate.py` requires this
  comment-stripped code evidence for paper-grade boundary-source promotion, so explanatory comments cannot make a
  simplified `TYPE_E` box look AIJ-equivalent.
- `scripts/validation_gate.py` now treats boundary protocol, boundary-source and roughness/precursor claims as audit-only
  evidence. It reads the real `blockage_gate` emitted by `audit_boundary_protocol.py`; metrics-table fields such as
  `boundary_source_gate`, `boundary_evidence_gate` or roughness tokens are reported as ignored context and cannot make a
  run pass without `boundary_protocol_audit.json` and `boundary_source_audit.json`.
- `native_baseline` gating no longer trusts `native_baseline_gate` from metrics. It recomputes the gate from
  `native_fluidx3d_baseline_manifest.json`, required native FluidX3D source hashes, BaselineId matching and the
  `native_fluidx3d_baseline` protocol item.
- `inlet_source_evidence` reporting is now audit-only. Metrics-table `inlet_source_gate`,
  `paper_grade_inlet_source_gate` and `inlet_source_method_class` fields are reported as ignored context and cannot make
  a run pass without a complete `inlet_source_audit.json`.
- The final gate now requires inlet-source advanced-method evidence to come from comment-stripped generated code. Older
  `inlet_source_audit.json` files without `advanced_inlet_evidence_uses_comment_stripped_code=true` or
  `inlet_source_comment_stripped_code_audit=true` remain diagnostic and must be regenerated.
- Added `scripts/probe_vtk_points.py` to sample native FluidX3D/CityLBM VTK frames at official RS probe points and emit
  the same Data-Probe-compatible audit CSV used by Grasshopper, including official coordinates, nearest-node distance,
  Uref, wind-vector evidence, compared component, time-averaged value and per-probe failure flags.
- Native VTK probe extraction now records unparsable official probe coordinates as explicit failed rows with
  `failure_reason=invalid_probe_coordinate` instead of silently dropping those probes from `failed_n`.
- Native VTK probe extraction now defaults to a 40-frame final-window average and refuses to write a validation probe
  audit when the selected VTK window is shorter than `--min-avg-frames`; one-frame extraction must be explicitly marked
  as smoke-test behavior by lowering that threshold.
- Native VTK probe extraction now also records `vtk_source_step_span` and
  `minimum_validation_average_step_span`, and refuses validation probe audits whose selected final-window VTK files
  cover fewer than `--min-avg-step-span` solver steps (`20000` by default). The metrics table and final gate now require
  the per-probe source-step span to match the runtime averaging window, preventing short-window probe averages from
  passing as paper-grade time averaging evidence.
- Native VTK probe extraction now defaults to structured-grid trilinear velocity sampling instead of nearest-node
  sampling, while keeping nearest-node distance as a separate coverage/tolerance audit field. This reduces avoidable
  RS probe projection error at `dx=2-3 m` without hiding out-of-domain probes.
- Native VTK probe extraction now writes the official RS coordinates and per-row `official_coordinate_delta` directly
  into `probe_audit.csv`, so the final gate can audit coordinate closure from the sampled probe rows instead of trusting
  summary-only metrics fields.
- `audit_native_preconditions.py` now independently audits per-probe official-coordinate deltas, normalization flags,
  wind-direction flags, `Uref`, nearest VTK distance and nonzero probe tolerance before a native FluidX3D baseline can
  pass paper-grade preconditions.
- The Grasshopper `Run Simulation` component now blocks Mode 1/2/3 validation runs unless the planned VTK output provides
  at least 40 saved frames and the final averaging window spans at least 20000 solver steps. Mode 0 still generates cases,
  but flags shorter schedules as smoke/diagnostic only.
- Added `scripts/audit_component_sensitivity.py` and wired it into the native validation chain, metrics builder and
  final gate. It compares `speed_ratio`, signed/absolute streamwise ratio and component ratios against official RS
  values, then flags whether a different component or a scale-like Uref/SI conversion factor can explain the bias before
  inlet or boundary physics are tuned.
- `audit_component_sensitivity.py` now derives the selected comparison component from valid, non-failed probe rows when
  `--selected-component` is not supplied, and fails the audit for missing or mixed per-probe `compared_component`
  evidence. A failed or stale first row in `probe_audit.csv` can no longer make the component/Uref sensitivity check
  report the wrong selected component.
- Probe-derived metrics now preserve the actual `Uref` used by `Data Probe` and read `WindDirectionUnitVector` from
  `case_metadata.json`, so wind/normalization evidence is not lost during validation-gate reporting.
- Added `scripts/run_native_validation_chain.py` as a one-command post-run evidence chain for native FluidX3D/CityLBM
  VTK packages. It runs the native run audit, generated `setup.cpp` inlet-source and boundary-source audits, inlet `U/k` profile audit, trilinear probe extraction, metrics builder and
  validation gate, then writes `validation_chain_manifest.json` so Case A/Case E reruns cannot skip required evidence
  while being mistaken for fresh CFD simulations.
- `scripts/run_native_fluidx3d_case.py` and `scripts/run_native_validation_chain.py` now split the native workflow into
  two auditable phases: prepare/install/build/run the real FluidX3D case first, then audit the newly generated VTK
  frames. The post-run chain still does not run CFD and must not be used to rebrand old VTK output as a fresh
  experiment.
- `validation_gate.py` now writes `diagnostic_priority` to the JSON report and console output. Failed runs are triaged
  in the required order: inlet `U/k` preservation, generated-source inlet evidence, turbulent inlet method, length scale
  and correlation evidence, generated-source boundary evidence, boundary/roughness/blockage, final-window time averaging,
  coordinate/component/Uref/probe evidence plus component/Uref sensitivity, native FluidX3D baseline, native/CityLBM
  parity, grid sensitivity, then residual systematic-bias root cause.
- `validation_gate.py` now independently rechecks component/Uref sensitivity numbers instead of trusting a copied
  `component_normalization_gate=pass`: if another velocity component materially reduces RMSE, or a best-fit scale far
  from 1.0 materially improves the selected component, the run remains diagnostic until component choice and Uref/SI
  scaling are resolved.
- `audit_component_sensitivity.py` now records SHA256 hashes for the probe audit CSV and official RS table, and
  `validation_gate.py` requires the component/Uref sensitivity audit probe hash to match the current `--probe-audit`
  and the official-table hash to match the current `--official`. Stale component-sensitivity JSON files can no longer
  explain away systematic bias for a different probe extraction or official measurement table.
- Added `scripts/audit_grid_sensitivity.py` and wired its output into the metrics template, validation chain and final
  gate. Paper-grade runs now require `grid_sensitivity_audit.json` with at least two matched dx levels, a finest dx that
  matches the reported metrics row, sufficient refinement ratio, and bounded finest-vs-next-coarse `U_RMSE_ratio` and
  `U_bias_ratio` changes. This makes a single improved high-resolution run diagnostic rather than publishable evidence.
- Added `scripts/audit_native_citylbm_parity.py` and wired its output into the metrics template, validation chain and
  final gate. A CityLBM validation row now requires `native_citylbm_parity_audit.json` proving that the paired native
  FluidX3D row used the same case, wind direction, grid, VTK cadence, averaging, Uref, inlet/boundary setup and probe
  component before CityLBM accuracy is interpreted as inherited from native FluidX3D.
- `validation_gate.py` now binds the per-probe VTK source-window audit to the runtime-selected VTK SHA256 hashes from
  `native_run_audit.json` or the Read VTK audit. A copied probe CSV from older VTK frames fails even when its reported
  source time steps match the current averaging window.
- `audit_inlet_profile_from_vtk.py` and `audit_inlet_correlation_from_vtk.py` now write SHA256 hashes for the selected
  final-window VTK frames, and `validation_gate.py` requires those hashes to match the runtime-selected window. Stale
  inlet U/k or turbulence-correlation audits can no longer pass by repeating only the same source time-step numbers.
- Generated `case_metadata.json` now records `WindProfileCsvSha256`; the inlet-profile audit records `af_csv_sha256`,
  and `validation_gate.py` requires the two hashes to match before accepting inlet `U/k` preservation. This prevents a
  run from proving preservation against the wrong AF table.
- `validation_gate.py` now recomputes SHA256 hashes for the runtime-selected VTK files listed in
  `native_run_audit.json` or a Read VTK audit. The selected files must exist in the archived run package and match the
  audit-declared hashes before probe, inlet-profile or inlet-correlation source-window evidence is trusted.
- `validation_gate.py` now also recomputes the selected VTK file hashes listed inside `inlet_profile_audit.json` and
  `inlet_correlation_audit.json`. Inlet `U/k` preservation and turbulence-correlation evidence must therefore come
  from current archived VTK files, not from copied audit JSON with matching time-step labels.
- `validation_gate.py` now recomputes run-freshness mtimes from archived runtime-audit file paths. The final gate no
  longer accepts `run_freshness_gate=pass` unless the referenced setup/metadata/building/domain files exist and every
  selected VTK frame is newer than the latest run-definition artifact on disk.
- `validation_gate.py` now recomputes per-probe `vtk_source_files` hashes from the probe audit CSV. Probe extraction
  evidence must list the archived VTK source paths, and those files must hash to the same final-window SHA256 set used
  by the runtime, inlet-profile and inlet-correlation audits.
- `validation_gate.py` now recomputes official coordinate deltas from the current official RS CSV and probe `x/y/z`
  values, then requires every valid probe to have recomputed coordinate evidence. A stale or hand-written
  `official_coordinate_delta=0` value in a copied probe CSV can no longer hide scale, `domain_origin` or RS projection
  mistakes.
- `audit_native_preconditions.py` now applies the same current-official-coordinate rule to native FluidX3D baseline
  preconditions. When an official RS/probe CSV is provided, native baseline evidence must recompute every valid probe
  coordinate delta from that file instead of trusting stale `official_coordinate_delta` values copied in a probe audit.
- `validation_metrics_from_probe_audit.py` and `docs/validation_metrics_template.csv` now carry the native baseline
  coordinate-delta source, recomputed count, recompute error and missing-delta count so exported metrics expose whether
  native probe evidence came from the current official table.
- `validation_gate.py` now verifies that native FluidX3D baseline source hashes come from one explicit complete source
  root. The manifest must prove a build file plus `src/setup.cpp`, `src/defines.hpp`, `src/lbm.hpp` and `src/lbm.cpp`
  under the declared `NativeFluidX3DSourcePath`, not merely provide four matching hashes from arbitrary paths.
- `scripts/audit_inlet_source.py` now recognizes the native strict-baseline synthetic-eddy implementation
  (`synthetic_eddy_count`, `updateSyntheticEddyPlane`, `turbulentWind`, `applyInlet(current)` and segmented
  `lbm.run(...)`) as correlated velocity-field inlet evidence instead of misclassifying dormant helper code as missing
  DFM/SEM proof. It still fails the paper-grade inlet gate because this path is velocity-field-only and does not
  reconstruct inlet distribution functions.
- `scripts/audit_inlet_source.py` now applies STG-lite-specific spectral-mode, Taylor-advection, update-interval and
  amplitude-cap checks only to velocity-field-only STG-lite sources. Distribution-consistent SEM/DFM/precursor evidence
  is no longer failed by CityLBM STG-lite diagnostics, while uncorrelated RMS/k random inlet forcing is explicitly tested
  to remain non-paper-grade.
- `audit_native_preconditions.py`, the metrics writer and the validation metrics template now carry
  `inlet_distribution_route`, `inlet_distribution_route_gate`, `has_equilibrium_boundaries_define` and
  `has_type_e_equilibrium_boundary_route` into the native baseline gate. A native setup that writes only macroscopic
  velocity fields without `EQUILIBRIUM_BOUNDARIES`/`TYPE_E` equilibrium-boundary evidence is now reported as a first-order
  inlet-source blocker instead of being hidden behind a generic method label.
- Native probe/component equivalence now also checks that the component/Uref sensitivity audit uses the same final-window
  `source_time_steps` and VTK SHA256 set as the runtime audit. A component-sensitivity report from a stale or different
  VTK window can no longer explain away systematic bias in Case A/E validation.
- `scripts/audit_inlet_source.py`, the metrics writer and the validation metrics template now expose whether a synthetic
  inlet has three-component velocity writes, three-component fluctuation evidence and `k`-driven three-component STG
  evidence. A velocity-field STG source that cannot prove all three components are perturbed from `k` fails the inlet
  source audit instead of being treated as a reliable turbulent inlet.
- `validation_gate.py`, `audit_native_preconditions.py` and the metrics template now require those three-component STG
  evidence fields for STG-like source audits. Older `inlet_source_audit.json` files without the new fields remain
  diagnostic and native baselines report the missing STG evidence as a first-priority turbulent-inlet blocker.
- `audit_native_run.py` no longer lets command-line speed-stability values pass the native `time_averaging_gate`.
  Paper-grade time averaging must use deterministic sampled-VTK statistics from the selected final-window frames. Any
  CLI override of mean speed, standard deviation or stability ratio is recorded as `mean_speed_statistics_source=cli_override`
  and remains diagnostic context only.
- `audit_native_run.py`, the metrics writer and `docs/validation_metrics_template.csv` now report final-window averaging
  shortfalls as explicit numbers: missing requested VTK frames, missing averaged frames and missing solver-step span.
  A four-frame diagnostic window now carries a directly auditable 36-frame shortfall and step-span shortfall instead of
  only a generic time-averaging failure string.
- `validation_gate.py` now adds a `systematic_bias_interpretation` gate. Large underprediction/overprediction cannot be
  interpreted as native FluidX3D or CityLBM solver accuracy while inlet U/k, turbulent-inlet evidence, boundary evidence,
  fresh VTK, time averaging, coordinate/component/Uref, native baseline, CityLBM parity or grid-sensitivity gates are
  still open.
- The final `diagnostic_priority` now expands failed systematic-bias prerequisites and the native FluidX3D top blocker,
  so a large residual bias points to the exact open evidence gates before any solver-accuracy interpretation.
- `audit_native_preconditions.py` now uses the same native-root-cause order requested for Case A debugging: turbulent
  inlet first, AIJ-equivalent boundary/roughness second, real final-window time averaging third,
  coordinate/component/Uref/probe closure fourth, LBM stability evidence fifth, and residual systematic bias only after
  those prerequisites.
- `validation_gate.py` now writes a structured `systematic_bias_diagnostic` block to the JSON report, including bias
  percentage points, threshold percentage points, best-fit scale, scaled-RMSE improvement and the exact open prerequisite
  blockers. This keeps large Case A/Case E underprediction from being interpreted through R2 alone.
- `audit_native_preconditions.py` now preserves concrete probe mapping and normalization blocker details, including the
  compared component values, missing/unmatched/duplicate probe IDs, official-coordinate coverage, coordinate-delta
  violation counts, Uref mismatch counts and VTK projection tolerance failures. The metrics CSV carries these native
  probe fields forward so residual bias cannot be explained without first proving RS probe identity, wind component,
  Uref normalization and sampling coordinates.
- The inlet-source evidence gate now requires more than a k-driven STG-lite label before accepting paper-grade turbulent
  inflow. `case_metadata.json`, `validation_protocol_audit.json`, `audit_inlet_source.py` and the metrics template now
  expose whether the inlet has turbulent length-scale evidence, Reynolds-stress tensor evidence and distribution-function
  reconstruction. The current CityLBM STG-lite path remains explicitly marked as `velocity_field_only` with an isotropic
  k assumption until a measured/precursor Reynolds-stress tensor and distribution-consistent inlet are implemented or
  proven by native empty-tunnel U/k/correlation preservation tests.
- `validation_gate.py` now has a direct smoke-tested paper-grade inlet-method predicate: `--allow-velocity-only-inlet`
  can relax only the general diagnostic inlet gate and cannot promote STG-lite or uncorrelated RMS/k forcing to
  paper-grade turbulent-inlet evidence.
- `audit_inlet_source.py` now also detects C++ STL random generators such as `std::mt19937`,
  `std::normal_distribution` and `std::uniform_real_distribution` in inlet context, so RMS/k velocity perturbations
  built from those sources are classified as uncorrelated diagnostic inlet forcing.
- `scripts/run_native_fluidx3d_case.py` now evaluates validation-protocol, metadata, planned VTK-window and synthetic
  inlet refresh gates before any native install/build/run action. If that `PreExecutionGate` is diagnostic-only, the
  runner blocks execution by default; `--allow-diagnostic-execution` is recorded as a debugging override and is not
  paper-grade evidence.
- `scripts/run_native_fluidx3d_case.py` and `validation_gate.py` now treat missing paper-grade case-metadata
  prerequisite fields as blockers instead of silently accepting absent evidence. Native Case A/E metadata must explicitly
  record turbulent-inlet readiness, boundary readiness, inlet route, and boundary implementation/evidence booleans before
  install/build/run or final validation gates can move beyond diagnostic status.
- `scripts/run_native_validation_chain.py` no longer promotes a native manifest to `native_baseline_gate=pass` unless
  the manifest also proves `PreExecutionGate=pass`, `Run.Requested=true`, `Run.Gate=pass` and
  `ActualVtkOutputGate=pass`. Dry-run/preflight manifests therefore cannot stand in for a real native FluidX3D baseline.
- 2026-08-24 native Case A empty-tunnel diagnostic `native_casea_strict_20260824_reconstruct_inlet_stress_novtk`
  tested the experimental inlet-stress/DDF reconstruction route without writing large VTK files. The strict empty-tunnel
  monitor rejected the run: `U_MAE/Uref=683.013%`, `k_MAE/target_mean=100.000%`, `k_bias/target_mean=-100.000%`.
  This route is therefore explicitly not promoted into CityLBM v0.3.0 and must be treated as a failed diagnostic, not
  as a native FluidX3D baseline or a solver-accuracy result.

## Remaining scientific work

- Native FluidX3D Case A strict baseline must be run with the same geometry, inflow, averaging window and measurement extraction.
- The inlet-profile audit must be run on newly generated native and CityLBM VTK sequences; without this JSON, high probe
  R2 is not enough to diagnose whether the solver preserved the official AF `U/k` inlet.
- If native FluidX3D is significantly closer to AIJ measurements, the same settings must be ported into CityLBM and
  verified with `native_citylbm_parity_audit.json` rather than by manual label matching.
- Case E should then be run with dx=2-3 m, long time averaging, at least one matched grid-sensitivity companion run, and
  the official AF/RS files.
- The new default `40000/1000` run is a validation preflight workflow, not final stationarity proof; paper runs must
  archive actual averaged source frames, stability diagnostics and solver logs.
- The STG-lite inlet is not a full digital-filter, precursor/recycling, or Reynolds-stress method; it lacks Reynolds-stress tensors, turbulent length scales and validated precursor inflow.
- The STG-lite inlet is velocity-field-only in v0.3.0. It remains diagnostic until empty-tunnel tests prove downstream
  `U/k` preservation or the inlet is replaced by a distribution-consistent DFM/SEM/precursor/recycling implementation.
- The inlet correlation audit is a precondition, not a complete turbulence-model validation: passing it proves measurable
  time/space correlation in sampled VTK frames, but not Reynolds-stress tensors, digital-filter correctness, precursor
  consistency or distribution-function reconstruction.
- The boundary condition model remains simplified and must be audited against the AIJ wind-tunnel setup before making paper-grade accuracy claims.
- Ground roughness is not yet represented by a rough-wall/wall-function boundary; the AF mean profile alone does not prove
  correct near-ground turbulence or speed-ratio behavior.
- `BoundaryProtocolAudit` uses configurable diagnostic clearance defaults and does not replace the official AIJ wind-tunnel
  boundary, fetch and blockage protocol; the external evidence JSON must still identify the AIJ-equivalence basis and
  outlet/side/top/floor roughness checks.
- A run without `boundary_protocol_audit.json` and a passing external AIJ boundary evidence JSON is not paper-grade,
  even if probe R2, screenshots or speed-ratio plots look acceptable.
- A high R2 alone is not sufficient. Mean bias, regression slope/intercept, probe mapping and native-vs-CityLBM parity must be acceptable before claiming publishable validation accuracy.
