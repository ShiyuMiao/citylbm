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
- `case_metadata.json` records protocol-risk fields: simplified boundary-condition summary, expected VTK frame count, required averaging, and validation-readiness status.
- `Run Simulation` no longer falls back to the legacy bundled v0.5.0 solver when no external FluidX3D path is provided; controlled validation must use an explicit external FluidX3D baseline.
- `Run Simulation` adds an optional experimental `Synthetic Inlet` control for CustomTable profiles with `k`.
- Generated FluidX3D `setup.cpp` can now use the AF `k` column to apply bounded SEM-lite synthetic-eddy inlet perturbations from `sigma=sqrt(2k/3)`.
- Synthetic inlet runs now limit each solver advance to `SyntheticTurbulenceUpdateInterval`, so inlet perturbations refresh independently from the VTK save interval.
- `case_metadata.json` records whether the synthetic inlet was requested and actually injected, plus synthetic scale, correlation length, update interval and amplitude cap.
- Each generated case now writes `validation_protocol_audit.json` and `.md` to flag inlet, boundary-condition, time-averaging, coordinate, normalization and grid-resolution readiness before metrics are interpreted.
- `case_metadata.json` and the native baseline manifest now include `BoundaryProtocolAudit`, a structured record of
  inlet/outlet/lateral/top faces, domain clearances in meters and building-height units, simplified boundary types and a
  diagnostic boundary-clearance gate.
- The validation audit now also records native FluidX3D baseline requirement, LBM stability scaling, wind-direction sign,
  probe-projection risk and systematic-bias gate so the known `-34 pp` underprediction pattern is treated as a protocol
  blocker rather than a tuning target.
- `docs/validation_metrics_template.csv` now includes run-evidence fields for source time steps, compared velocity component,
  averaged-field stability, boundary summary, synthetic inlet method, native baseline id, probe mapping distances and protocol gate.
- `Data Probe` now appends validation-audit outputs for `Uref`-based speed ratio, streamwise ratio, nearest VTK-sample
  distance and per-probe CSV rows without changing the existing first five outputs.
- `Data Probe` now accepts optional official probe IDs, a probe-to-VTK tolerance and an explicit compared component.
  Its audit CSV records the selected comparison value and flags probes with no VTK neighbor, invalid comparison value
  or out-of-tolerance mapping.
- Each generated case now also writes `native_fluidx3d_baseline_manifest.json` and `.md` so native FluidX3D and
  CityLBM-driven runs must archive the same `setup.cpp`, `defines.hpp`, geometry, metadata, averaging window and probe
  audit evidence before any paper-grade accuracy claim.
- The native baseline manifest now includes existence flags and SHA256 hashes for the generated source, geometry and
  metadata files so paired native/CityLBM runs can prove they used identical inputs.

## Remaining scientific work

- Native FluidX3D Case A strict baseline must be run with the same geometry, inflow, averaging window and measurement extraction.
- If native FluidX3D is significantly closer to AIJ measurements, the same settings must be ported into CityLBM.
- Case E should then be run with dx=2-3 m, long time averaging and the official AF/RS files.
- The SEM-lite inlet is not a full digital-filter, precursor/recycling, or Reynolds-stress method; it lacks Reynolds-stress tensors, turbulent length scales and validated precursor inflow.
- The boundary condition model remains simplified and must be audited against the AIJ wind-tunnel setup before making paper-grade accuracy claims.
- `BoundaryProtocolAudit` uses diagnostic clearance defaults and does not replace the official AIJ wind-tunnel boundary,
  fetch and blockage protocol.
- A high R2 alone is not sufficient. Mean bias, regression slope/intercept, probe mapping and native-vs-CityLBM parity must be acceptable before claiming publishable validation accuracy.
