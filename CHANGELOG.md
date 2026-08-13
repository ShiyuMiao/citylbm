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

### Known limits

- The `k` column is read, converted and recorded, but v0.3.0 does not yet inject synthetic turbulent fluctuations at the inlet.
- Case E has not been completed as a formal SCI-level validation run on this PC in this branch.
- Final publishable accuracy still requires native FluidX3D Case A baseline, grid sensitivity, time averaging and measured-data comparison.

## v0.2.1

- AIJ Case A workflow materials and validation helper scripts.
- FluidX3D integration and VTK visualization components.
- UI tab organization and component icon updates.

## v0.2.0

- Initial stable Grasshopper workflow with scene, simulation and result components.
