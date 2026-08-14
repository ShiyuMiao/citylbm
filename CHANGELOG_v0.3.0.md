# CityLBM v0.3.0 Validation Optimization Notes

v0.3.0 is a validation-readiness branch. It fixes software issues that can create large AIJ validation errors, but it does not claim final Case A or Case E publication-grade accuracy by itself.

## Main fixes relative to earlier versions

- `Create Scene` now accepts `WP=3` for CustomTable profiles.
- `AF_caseE.csv` style input is parsed as `z(m), U(m/s), k(m2/s2)`.
- The generated FluidX3D case uses the full `U(z)` table for inlet interpolation.
- `Uref` is retained as metadata for normalization instead of replacing the inflow table.
- The `k` column is preserved, converted to LBM units and stored in metadata.
- `domain_origin.json` now includes schema and version fields.
- `case_metadata.json` records wind profile, velocity scaling, k status, grid and run settings.
- `Read VTK` reports whether metadata-driven velocity scaling was applied.
- `Read VTK` adds `Average Last N` so validation workflows can output an explicit multi-frame time-averaged velocity field instead of a single instantaneous VTK frame.
- `Read VTK` now reports averaged-field stability diagnostics: mean speed, mean/max pointwise speed standard deviation,
  and mean/max relative fluctuation across the averaged VTK frames.
- `Read VTK` now emits an explicit `time_averaging_gate` and GH warning when the selected VTK window is unaveraged,
  shorter than 10 frames, not the last available window, non-uniform, or above the stability thresholds.
- `Run Simulation` and `SimulationSettings` now default to `TimeSteps=10000` and `SaveInterval=500`, producing about
  20 VTK frames for a minimum validation averaging workflow instead of short demo-only output.
- `Run Simulation` now blocks Mode 1/2/3 when the planned `TimeSteps / SaveInterval` window would produce fewer than
  10 VTK frames. Mode 0 can still generate smoke-test cases, but the metadata marks them as non-validation runs.
- `case_metadata.json` records protocol-risk fields: simplified boundary-condition summary, expected VTK frame count, required averaging, and validation-readiness status.
- `Run Simulation` no longer falls back to the legacy bundled v0.5.0 solver when no external FluidX3D path is provided; controlled validation must use an explicit external FluidX3D baseline.
- `Run Simulation` adds an optional experimental `Synthetic Inlet` control for CustomTable profiles with `k`.
- Generated FluidX3D `setup.cpp` can now use the AF `k` column to apply bounded STG-lite spectral inlet perturbations from `sigma=sqrt(2k/3)`.
- The STG-lite inlet now uses deterministic multi-mode spectral fluctuations, avoiding the earlier sparse-eddy pattern where many inlet cells could receive near-zero perturbation.
- STG-lite spectral modes are now projected normal to their synthetic wave vectors before summation, reducing non-physical divergent inlet fluctuations while keeping the method deterministic and auditable.
- STG-lite temporal evolution now uses Taylor frozen-turbulence phase advection along the local mean wind instead of an arbitrary discrete phase increment, improving time correlation while remaining a diagnostic velocity-field inlet.
- Synthetic inlet runs now limit each solver advance to `SyntheticTurbulenceUpdateInterval`, so inlet perturbations refresh independently from the VTK save interval.
- Interactive `GRAPHICS` runs now use the same STG-lite refresh loop as batch runs, and inlet perturbations are applied only
  to `TYPE_E` inlet nodes so solid ground/building flags are not touched by the diagnostic inlet refresh.
- `setup.cpp`, `case_metadata.json` and `validation_protocol_audit` now explicitly record that STG-lite refreshes macroscopic `lbm.u` only and does not reconstruct FluidX3D distribution functions.
- `case_metadata.json` records whether the synthetic inlet was requested and actually injected, plus synthetic scale, correlation length, update interval and amplitude cap.
- `case_metadata.json`, the native baseline manifest, metrics template and `validation_gate.py` now track the synthetic
  inlet correlation length and its evidence source. A user-selected STG correlation length is treated as diagnostic-only
  until it is replaced or justified by AIJ length-scale data, a precursor/recycling field or a validated DFM/SEM model.
- `Run Simulation` adds `STG Length Source`, an optional text evidence tag for the STG correlation-length source. Empty
  values preserve the diagnostic-only behavior; accepted evidence tags such as `aij_length_scale_verified`,
  `official_length_scale_verified`, `precursor_length_scale`, `digital_filter_length_scale`,
  `synthetic_eddy_length_scale`, `sem_length_scale`, `dfm_length_scale` or `validated_length_scale_model` are recorded
  in `case_metadata.json`, the native manifest and the validation audit.
- Each generated case now writes `validation_protocol_audit.json` and `.md` to flag inlet, boundary-condition, time-averaging, coordinate, normalization and grid-resolution readiness before metrics are interpreted.
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
- Boundary support files are now read and SHA256-hashed by `audit_boundary_protocol.py`. Empty, unreadable or
  existence-only files keep `boundary_evidence_files_all_hashed=false`, and the final validation gate fails until the
  evidence artifacts are non-empty and traceable in the run archive.
- `validation_gate.py` now requires boundary-equivalence support, evidence-file hashes, supported boundary-condition
  fields and clearance checks to come from the archived `boundary_protocol_audit.json` itself. Metrics CSV fields can
  no longer self-report those boundary evidence booleans in place of the external audit file.
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
- `docs/validation_metrics_template.csv` now includes run-evidence fields for source time steps, compared velocity component,
  averaged-field stability, boundary summary, synthetic inlet method, inlet distribution treatment, wall roughness
  treatment, native baseline id, probe mapping distances and protocol gate.
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
- `scripts/audit_native_run.py` now computes time-stability ratios directly from real VTK velocity time series when the
  ratios are not supplied on the command line. It deterministically samples up to 20,000 points across the selected final
  frames, records the sampling method, and feeds `mean_speed_stddev_ratio` / `max_speed_stddev_ratio` into the same
  time-averaging gate used by Grasshopper `Read VTK`.
- `scripts/audit_native_run.py`, `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py`
  now carry `run_freshness_gate`, `latest_reference_mtime_utc` and `oldest_selected_vtk_mtime_utc`, so stale VTK frames
  copied from older setups cannot be promoted as newly generated Case A/E evidence.
- `validation_metrics_from_probe_audit.py`, the metrics template and `validation_gate.py` now carry
  `probe_vtk_source_window_gate`, probe source time steps and probe VTK hash-set counts. Valid probe rows must use the
  same final-window VTK frames as the averaging and inlet-profile/correlation audits, or the new `probe_source_window`
  gate keeps the run diagnostic.
- Added `scripts/audit_inlet_profile_from_vtk.py` to read real post-spinup `u-*.vtk` frames, sample an inlet or
  empty-tunnel cross-plane, reconstruct time-mean streamwise `U(z)` and temporal-variance `k(z)`, and compare both
  against the official AF table. This replaces hand-filled empty-tunnel `U/k` evidence with an archived JSON/CSV audit.
- `scripts/audit_inlet_profile_from_vtk.py` now records all available VTK steps and fails the inlet `U/k` gate when the
  selected average is not an explicit final window with strictly increasing, uniformly spaced time steps. This prevents
  short or non-final inlet samples from being interpreted as solver accuracy evidence.
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
- `validation_gate.py` now requires inlet-source and inlet-correlation pass evidence to come from the archived
  `inlet_source_audit.json` and `inlet_correlation_audit.json` values themselves. Metrics CSV fields can summarize
  those audits, but cannot replace the generated-source hash or final-window VTK correlation audit.
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
- Added `scripts/audit_boundary_source.py` and wired `boundary_source_audit.json` into the metrics template, native
  validation chain and final gate. The audit hashes the generated `setup.cpp`, classifies the actual boundary source
  implementation, and keeps simplified `TYPE_E` outlet/lateral/top plus no-slip-only floor/buildings from satisfying
  paper-grade boundary protocol claims.
- Added `scripts/probe_vtk_points.py` to sample native FluidX3D/CityLBM VTK frames at official RS probe points and emit
  the same Data-Probe-compatible audit CSV used by Grasshopper, including official coordinates, nearest-node distance,
  Uref, wind-vector evidence, compared component, time-averaged value and per-probe failure flags.
- Native VTK probe extraction now records unparsable official probe coordinates as explicit failed rows with
  `failure_reason=invalid_probe_coordinate` instead of silently dropping those probes from `failed_n`.
- Native VTK probe extraction now defaults to a 10-frame final-window average and refuses to write a validation probe
  audit when the selected VTK window is shorter than `--min-avg-frames`; one-frame extraction must be explicitly marked
  as smoke-test behavior by lowering that threshold.
- Native VTK probe extraction now defaults to structured-grid trilinear velocity sampling instead of nearest-node
  sampling, while keeping nearest-node distance as a separate coverage/tolerance audit field. This reduces avoidable
  RS probe projection error at `dx=2-3 m` without hiding out-of-domain probes.
- Added `scripts/audit_component_sensitivity.py` and wired it into the native validation chain, metrics builder and
  final gate. It compares `speed_ratio`, signed/absolute streamwise ratio and component ratios against official RS
  values, then flags whether a different component or a scale-like Uref/SI conversion factor can explain the bias before
  inlet or boundary physics are tuned.
- Probe-derived metrics now preserve the actual `Uref` used by `Data Probe` and read `WindDirectionUnitVector` from
  `case_metadata.json`, so wind/normalization evidence is not lost during validation-gate reporting.
- Added `scripts/run_native_validation_chain.py` as a one-command post-run evidence chain for native FluidX3D/CityLBM
  VTK packages. It runs the native run audit, generated `setup.cpp` inlet-source and boundary-source audits, inlet `U/k` profile audit, trilinear probe extraction, metrics builder and
  validation gate, then writes `validation_chain_manifest.json` so Case A/Case E reruns cannot skip required evidence
  while being mistaken for fresh CFD simulations.
- `validation_gate.py` now writes `diagnostic_priority` to the JSON report and console output. Failed runs are triaged
  in the required order: coordinate/component/Uref/probe evidence plus component/Uref sensitivity, time averaging, inlet
  `U/k` preservation, generated-source inlet evidence, turbulent inlet method, length scale and correlation evidence, generated-source boundary evidence, boundary/roughness/blockage, native
  FluidX3D baseline, native/CityLBM parity, grid sensitivity, then residual systematic-bias root cause.
- `validation_gate.py` now independently rechecks component/Uref sensitivity numbers instead of trusting a copied
  `component_normalization_gate=pass`: if another velocity component materially reduces RMSE, or a best-fit scale far
  from 1.0 materially improves the selected component, the run remains diagnostic until component choice and Uref/SI
  scaling are resolved.
- Added `scripts/audit_grid_sensitivity.py` and wired its output into the metrics template, validation chain and final
  gate. Paper-grade runs now require `grid_sensitivity_audit.json` with at least two matched dx levels, a finest dx that
  matches the reported metrics row, sufficient refinement ratio, and bounded finest-vs-next-coarse `U_RMSE_ratio` and
  `U_bias_ratio` changes. This makes a single improved high-resolution run diagnostic rather than publishable evidence.
- Added `scripts/audit_native_citylbm_parity.py` and wired its output into the metrics template, validation chain and
  final gate. A CityLBM validation row now requires `native_citylbm_parity_audit.json` proving that the paired native
  FluidX3D row used the same case, wind direction, grid, VTK cadence, averaging, Uref, inlet/boundary setup and probe
  component before CityLBM accuracy is interpreted as inherited from native FluidX3D.

## Remaining scientific work

- Native FluidX3D Case A strict baseline must be run with the same geometry, inflow, averaging window and measurement extraction.
- The inlet-profile audit must be run on newly generated native and CityLBM VTK sequences; without this JSON, high probe
  R2 is not enough to diagnose whether the solver preserved the official AF `U/k` inlet.
- If native FluidX3D is significantly closer to AIJ measurements, the same settings must be ported into CityLBM and
  verified with `native_citylbm_parity_audit.json` rather than by manual label matching.
- Case E should then be run with dx=2-3 m, long time averaging, at least one matched grid-sensitivity companion run, and
  the official AF/RS files.
- The new default `10000/500` run is still a minimum validation workflow, not final stationarity proof; paper runs must
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
