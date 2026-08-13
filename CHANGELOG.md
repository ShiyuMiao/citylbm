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
