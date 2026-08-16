# CityLBM Changelog

## v0.3.0

- Restored a compileable Rhino 7 / Grasshopper source baseline for the validation branch.
- Standardized plugin and assembly metadata to `0.3.0`.
- Added `Wind Profile = 3` (`CustomTable`) to `Create Scene`.
- Added CSV parsing for `z(m), U(m/s), k(m2/s2)` inflow profiles.
- Generated FluidX3D `setup.cpp` now emits `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]` and `profile_origin_z_m`.
- Added `case_metadata.json` and schema-tagged `domain_origin.json` for traceable post-processing.
- Added VTK reader metadata reporting to prevent SI/LBM velocity-unit ambiguity.
- Added validation metrics helpers for MAE, RMSE, bias, R2 and regression diagnostics.
- Added `Read VTK / Average Last N` to produce explicit multi-frame time-averaged fields for validation.
- Added protocol-risk metadata for boundary conditions, VTK frame count and validation-readiness status.
- Disabled the legacy bundled v0.5.0 fallback for controlled validation runs; users must provide an explicit external FluidX3D path.
- Added optional experimental `Run Simulation / Synthetic Inlet` inputs for CustomTable profiles with `k`.
- Generated FluidX3D cases can now use `k` for bounded STG-lite spectral inlet perturbations, with request/injection status and parameters recorded in `case_metadata.json`.
- Synthetic inlet runs now refresh inlet perturbations at `SyntheticTurbulenceUpdateInterval` instead of tying updates to the VTK save interval.
- Added generated `validation_protocol_audit.json/.md` so validation runs explicitly report inlet, boundary, averaging, coordinate, normalization and grid-resolution readiness.
- Added `scripts/validation_gate.py` to fail run packages that lack paper-grade evidence for averaging, inlet U/k preservation, native baseline linkage, probe mapping, coordinate normalization or bounded error metrics.
- Added `scripts/validation_metrics_from_probe_audit.py` to merge Data Probe audit rows with official AIJ measurements and output the standard validation metrics row.
- Time-averaging metrics now prefer real VTK audit frame counts and source time-step lists over requested CLI averaging windows, so short final-window runs cannot appear as longer paper-grade averages in validation tables.
- The paper-grade time-averaging gate now requires real archived `source_time_steps` and an explicit `time_averaging_gate=pass`; requested `AverageLastN` or `ExpectedVtkFrameCount` values are recorded only as diagnostic context.
- The time-averaging gate now independently parses `source_time_steps` and cross-checks count, first/last step, strict increase, uniform spacing and available-frame coverage; summary pass flags alone cannot hide an irregular or non-final VTK window.
- Native-run audits now record requested solver steps, VTK save interval/start step and expected VTK frame count; the final time-averaging gate fails configurations that were planned to save fewer than the minimum final-window frames.
- Native-run audits now record run-freshness evidence and fail the new `run_freshness` gate when selected VTK frames are older than the current setup/metadata artifacts.
- Native VTK probe extraction now writes VTK origin, spacing, dimensions, source time steps, source hashes and nearest-grid coordinates into the probe audit CSV for coordinate/projection traceability.
- Probe-derived metrics now record `probe_vtk_source_window_gate`, source time steps and hash-set counts; `validation_gate.py` fails `probe_source_window` when valid probes are not sampled from the same final-window VTK frames used by the averaging and inlet audits.
- The systematic-bias gate now infers under/overprediction directly from `U_bias_ratio` using the validation threshold, so a missing `systematic_bias_flag` cannot hide a `-34 pp` style low-bias run.
- The compared-component gate now requires `compared_component_consistency_gate=pass` and no missing per-probe component labels, preventing mixed or partially audited speed/streamwise comparisons from passing as paper-grade evidence.
- Added a `probe_projection_distance` gate that reads per-probe `nearest_distance` and `tolerance` from the Data Probe audit CSV and fails runs whose projection distance/tolerance is missing, exceeds tolerance or is too large relative to `dx`.
- Probe VTK sampling now records the physical grid extent and fails any official measurement point outside that extent before interpolation, preventing scale/domain-origin/coordinate errors from being hidden by boundary-clamped VTK samples.
- The coordinate/normalization gate now audits per-probe `Uref`, wind-vector and normalization flags from the Data Probe CSV; a correct summary metrics row alone cannot hide mixed or missing probe-level normalization evidence.
- The boundary gate now requires an explicit `boundary_protocol_audit.json` pass with `boundary_equivalence_supported=true`; AIJ-equivalence tokens in metadata/metrics are kept as diagnostic text and no longer pass the paper-grade boundary gate by themselves.
- Boundary evidence now also requires a supported `boundary_evidence_class` and at least one existing `boundary_evidence_files` artifact; token-only AIJ-equivalence text remains diagnostic and cannot satisfy the boundary gate by itself.
- Boundary support artifacts must now be non-empty and SHA256-hashed in `boundary_protocol_audit.json`; existence-only files cannot pass the paper-grade boundary gate.
- Boundary evidence now requires per-condition support booleans for inlet, outlet, lateral, top, ground-wall,
  roughness, blockage, fetch/clearance, outlet-reflection and side/top-boundary checks. Text values such as `unknown`,
  `unverified`, `not_checked` or `diagnostic_only` keep the boundary gate failing even if `boundary_evidence_gate=pass`
  is present.
- Added `scripts/audit_boundary_source.py`; validation packages must now archive `boundary_source_audit.json` with the generated `setup.cpp` hash and boundary implementation class. Simplified `TYPE_E` outlet/lateral/top source code now blocks paper-grade boundary promotion even when text evidence exists.
- The inlet length-scale gate now requires both `inlet_length_scale_gate=pass` and a supported AIJ/official, precursor/recycling, DFM/SEM, digital-filter or validated-model length-scale source; source tokens alone no longer pass.
- Inlet correlation audits now require finite temporal/spatial correlation coverage fractions, preventing sparse or degenerate inlet fluctuations from passing on correlation mean values alone.
- The inlet correlation gate now independently enforces the audited final-window source steps and numeric correlation thresholds, so RMS/k-preserving but uncorrelated or wrong-window inlet fluctuations cannot pass through a hand-filled `inlet_correlation_gate`.
- Inlet `U/k` preservation now requires real archived final-window source steps from `audit_inlet_profile_from_vtk.py`; `empty_tunnel_gate=pass` or bias values alone cannot satisfy the inlet evidence gate without the source-window audit.
- Added `scripts/audit_inlet_source.py`; validation packages must now archive `inlet_source_audit.json` with the generated `setup.cpp` hash, inlet implementation class and distribution-consistency evidence before turbulent-inlet claims are accepted.
- The paper-grade inlet-method gate now requires an explicit supported `inlet_method_class` plus distribution-consistent treatment; a protocol pass flag or method-name-only metadata can no longer pass the turbulent-inlet evidence gate.
- Added `scripts/audit_grid_sensitivity.py`; `validation_gate.py` now requires `grid_sensitivity_audit.json` with at
  least two matched dx levels, bounded finest-vs-coarser RMSE/bias change, and a finest dx matching the metrics row.
- Added `scripts/audit_native_citylbm_parity.py`; CityLBM validation rows now need paired native FluidX3D metrics with
  matched case, wind direction, dx, averaging, Uref, inlet/boundary and probe settings before inherited native accuracy
  can be claimed.
- Added a 2026-08-14 native Case A strict preflight record: fresh empty-tunnel and building configurations were generated from official AF/RS inputs, but FluidX3D was not launched because boundary-equivalence and roughness/precursor source gates remain open.
- Native FluidX3D metadata fields such as `TurbulenceMethod`, `InletUpdateInterval`, `SyntheticEddy`, `RecyclingRescaling` and `RoughnessLayout` are now mapped into the standard validation metrics row, so synthetic-eddy and digital-filter candidates remain diagnostic unless distribution-consistent inlet evidence, validated length-scale evidence and final-window correlation audits are archived.
- Added a separate `roughness_or_precursor` validation gate so AIJ Case A/E runs cannot pass paper-grade boundary checks through domain-clearance/blockage evidence alone when wind-tunnel roughness geometry, validated rough-wall treatment or precursor/recycling equivalence is missing.

### Known limits

- The STG-lite inlet is not a full digital-filter, precursor/recycling, or Reynolds-stress turbulent inflow and still requires native FluidX3D compile/run verification and sensitivity testing.
- Boundary conditions are still simplified and must be audited against the AIJ wind-tunnel setup.
- Case E has not been completed as a formal SCI-level validation run on this PC in this branch.
- Final publishable accuracy still requires native FluidX3D Case A baseline, grid sensitivity, time averaging and measured-data comparison.

## v0.2.1

- AIJ Case A workflow materials and validation helper scripts.
- FluidX3D integration and VTK visualization components.
- UI tab organization and component icon updates.

## v0.2.0

- Initial stable Grasshopper workflow with scene, simulation and result components.
