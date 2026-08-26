# AIJ Case A 300/150 Diagnostic Evidence

This folder contains lightweight evidence from the fresh native FluidX3D Case A diagnostic run used to package CityLBM v0.4.0.

The original VTK files are intentionally not included because they are large binary result files. The packaged files record the generated-case manifest, native-run manifest, validation metrics and gate report.

This run is diagnostic only. It confirms execution and traceability, but it does not satisfy publication-grade validation accuracy.

The later `AIJ_CaseA_300_150_vtk_start_100_canary` record in this package is a separate VTK scheduling proof. It confirms the new save-start/final-frame logic and should not be merged with the 186-probe diagnostic accuracy metrics below.

Key diagnostic metrics:

- `R2 = -2.8714`
- `Pearson r = 0.0163`
- `RMSE ratio = 3.4374`
- `MAE ratio = 2.9778`

Main remaining blockers:

- The 300-step run is too short for sufficient flow-through and stationary averaging.
- Runtime inlet `k` preservation is not yet acceptable.
- Boundary-runtime and native-precondition gates fail.
- AIJ Case E must not be promoted until Case A baseline evidence is improved.
