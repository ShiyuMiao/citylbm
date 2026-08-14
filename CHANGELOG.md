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
- Native VTK probe extraction now writes VTK origin, spacing, dimensions, source time steps, source hashes and nearest-grid coordinates into the probe audit CSV for coordinate/projection traceability.
- The compared-component gate now requires `compared_component_consistency_gate=pass` and no missing per-probe component labels, preventing mixed or partially audited speed/streamwise comparisons from passing as paper-grade evidence.
- Added a `probe_projection_distance` gate that reads per-probe `nearest_distance` and `tolerance` from the Data Probe audit CSV and fails runs whose projection distance/tolerance is missing, exceeds tolerance or is too large relative to `dx`.
- The boundary gate now requires an explicit `boundary_protocol_audit.json` pass with `boundary_equivalence_supported=true`; AIJ-equivalence tokens in metadata/metrics are kept as diagnostic text and no longer pass the paper-grade boundary gate by themselves.
- Boundary evidence now also requires a supported `boundary_evidence_class` and at least one existing `boundary_evidence_files` artifact; token-only AIJ-equivalence text remains diagnostic and cannot satisfy the boundary gate by itself.
- The inlet length-scale gate now requires both `inlet_length_scale_gate=pass` and a supported AIJ/official, precursor/recycling, DFM/SEM, digital-filter or validated-model length-scale source; source tokens alone no longer pass.
- Inlet correlation audits now require finite temporal/spatial correlation coverage fractions, preventing sparse or degenerate inlet fluctuations from passing on correlation mean values alone.
- Inlet `U/k` preservation now requires real archived final-window source steps from `audit_inlet_profile_from_vtk.py`; `empty_tunnel_gate=pass` or bias values alone cannot satisfy the inlet evidence gate without the source-window audit.
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
