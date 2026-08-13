# AIJ Case A Native FluidX3D Baseline Protocol

This protocol is the promotion gate before CityLBM settings are copied into the Rhino/Grasshopper workflow and before
AIJ Case E is treated as a paper-grade validation experiment.

## Scope

- Case: AIJ Case A isolated building.
- Purpose: establish a native FluidX3D reference with controlled inlet, boundary, coordinate, averaging and probe
  extraction settings.
- Evidence status in this repository: protocol-ready, not newly run.
- Required platform: native FluidX3D source tree with `FluidX3D.sln` or `makefile`, not the placeholder
  `src/Resources/FluidX3D/FluidX3D.source.zip`.

## Inputs

- Official inflow table: `AF_caseA.csv`.
- Official measurement table: `RS-caseA.csv`.
- Geometry: model-scale block, `B=0.08 m`, `H=0.16 m`, `D=0.08 m`.
- Coordinates: `+X` is streamwise wind direction, `Y=0` is the vertical center plane, `Z=0` is ground.
- Reference speed: use the official Case A reference velocity consistently in both native FluidX3D and CityLBM
  postprocessing. Do not change `Uref` to fit the error.

## Native Baseline Gates

1. Empty-tunnel gate.
   The empty-tunnel run must preserve both mean velocity and turbulent kinetic energy before any building run is
   promoted. Record `U_MAE`, `U_RMSE`, `U_bias`, `k_MAE`, `k_RMSE`, `k_bias`, the post-spinup sample count and the
   inlet-turbulence method.

2. Building Case A gate.
   Run the building case only after the empty-tunnel gate passes or after the protocol is explicitly marked as
   diagnostic. Use the same FluidX3D source commit, `setup.cpp`, `defines.hpp`, grid spacing, boundary mode,
   turbulence method and averaging rules.

3. Time-averaging gate.
   Do not report a single instantaneous VTK frame as validation. Archive post-spinup probe time means and, when VTK is
   used for visualization, at least 10 post-spinup VTK frames or an explicit averaged VTK field with the source frame
   list.

4. Probe audit gate.
   Probe extraction must record official point IDs, coordinates, selected velocity component, `Uref`, nearest VTK/probe
   distance, tolerance, failure status, valid count and failed count. In CityLBM this is produced by `Data Probe`
   outputs `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`.

5. Promotion gate.
   CityLBM may inherit native FluidX3D settings only after native Case A has a passing or explicitly bounded diagnostic
   record. If native FluidX3D underpredicts mean speed or `k`, do not tune CityLBM to hide the discrepancy; fix or
   document the native physics first.

## Minimum Settings To Archive

- FluidX3D source path and source hash or commit.
- `setup.cpp`, `defines.hpp`, `buildings.stl`, run log and postprocess script hashes.
- `dx`, lattice dimensions, `tau`, target Reynolds number, velocity set and LES/subgrid settings.
- Domain extents in `H`: upstream, downstream, lateral and top clearance.
- Boundary mode and boundary-source justification.
- Inlet turbulence method: off, SEM-lite, synthetic-eddy, digital-filter, recycling-rescaling or precursor.
- Inlet `U` and `k` preservation metrics from the empty tunnel.
- Building probe metrics: `U_MAE_ratio`, `U_RMSE_ratio`, `U_bias_ratio`, `U_R2`, slope, intercept and max absolute
  error.
- Probe mapping diagnostics: valid/failed count, mean/max probe distance, tolerance and compared component.

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
