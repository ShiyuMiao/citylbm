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
- `case_metadata.json` records protocol-risk fields: simplified boundary-condition summary, expected VTK frame count, required averaging, and validation-readiness status.
- `Run Simulation` no longer falls back to the legacy bundled v0.5.0 solver when no external FluidX3D path is provided; controlled validation must use an explicit external FluidX3D baseline.
- `Run Simulation` adds an optional experimental `Synthetic Inlet` control for CustomTable profiles with `k`.
- Generated FluidX3D `setup.cpp` can now use the AF `k` column to apply bounded STG-lite inlet perturbations from `sigma=sqrt(2k/3)`.
- `case_metadata.json` records whether the synthetic inlet was requested and actually injected, plus STG scale, correlation length, update interval and amplitude cap.

## Remaining scientific work

- Native FluidX3D Case A strict baseline must be run with the same geometry, inflow, averaging window and measurement extraction.
- If native FluidX3D is significantly closer to AIJ measurements, the same settings must be ported into CityLBM.
- Case E should then be run with dx=2-3 m, long time averaging and the official AF/RS files.
- The STG-lite inlet is not a full digital-filter or synthetic-eddy method; it lacks Reynolds-stress tensors, turbulent length scales and precursor/recycling inflow.
- The boundary condition model remains simplified and must be audited against the AIJ wind-tunnel setup before making paper-grade accuracy claims.
