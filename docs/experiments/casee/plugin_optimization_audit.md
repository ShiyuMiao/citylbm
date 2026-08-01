# CityLBM Plugin Optimization Audit from Experiments 1-3

Generated in the `codex/experiment-2-aij-casee-citylbm-v0.3.0-rc` branch.

## Original Plugin Behavior Reviewed

- `RunSimulationComponent` exposed generic wind speed, viscosity, timestep, and save interval controls, but had no explicit AIJ Case E validation preset.
- `SimulationSettings` defaulted to short smoke-run scale settings (`TimeSteps=2000`, `SaveInterval=1000`) and did not record spin-up, Uref, zref, probe protocol, or evidence boundaries.
- `FluidX3DInterface.GenerateSetupCpp()` initialized a uniform inlet velocity field and used the same constant velocity on inlet boundary cells.
- Generated case folders did not include a machine-readable run manifest tying the FluidX3D case to the experiment protocol.

## Experiment-Derived Changes

### Experiment 1 / Case A Boundary

Case A remains a smoke-regression guard. No accuracy-model default was changed from Case A alone. The current-machine smoke regression passed with a 2000-step FluidX3D run log and timestep-2000 VTK output recorded by hash. This satisfies the workflow non-regression guard for the release gate, but it is not an accuracy-validation result.

### Experiment 2 / AIJ Case E

Implemented in source:

- Added an explicit `AIJ Case E Preset` input to `Run Simulation`.
- Added `SimulationProtocolPolicy.Apply()` for the official Case E `ac+N` protocol.
- When the preset is enabled, the plugin forces:
  - wind vector `(0, -1, 0)`;
  - `Uref = 3.928296 m/s`;
  - `zref = 15.9 m`;
  - formal validation height `z = 2 m`;
  - `TimeSteps >= 48000`;
  - `SpinupSteps >= 12000`;
  - `ExpectedProbeCount = 80`;
  - formal sampling mode `raw_trilinear`.
- Added `AF_caseE.csv` ingestion for the generated FluidX3D inlet profile.
- Added profile-aware lattice velocity scaling so the highest AF velocity does not exceed the configured lattice velocity cap.
- Added `citylbm_run_manifest.json` generation in every case folder.
- Applied the Case E wind override to a generation-only `Scene` clone, so Grasshopper input scenes are not silently mutated.
- Kept the generic CityLBM lattice velocity default at 0.1; the 0.08 cap is Case E preset-only.
- Added a default-off `Diagnostic LBM Nu Override` Grasshopper input and run-manifest field. It exists to reproduce native `nu_lbm` sensitivity diagnostics and is not a default solver accuracy model.
- Added a MinGW/g++ fallback path for FluidX3D builds when MSBuild is unavailable or fails. This is a build-chain reliability improvement, not a solver accuracy model.

### Experiment 3 / TUM2TWIN

Experiment 3 supports workflow traceability and screening-level urban digital-twin use. The code change from Experiment 3 is not a new default accuracy model; it is manifest and protocol traceability, so real urban runs can be reviewed without confusing screening outputs with benchmark validation.

## What Is Default vs Experimental

Default-safe:

- Run manifest output.
- Explicit protocol metadata.
- Fail-closed evidence boundary.

Preset-only:

- AIJ Case E official wind speed, direction, inlet profile, long-run settings, and z=2 m probe protocol.

Experimental only:

- `nearest_valid`, `fluid_weighted`, `vertical_valid_above`, `z_plus_half`.
- near-wall, rough-wall, and effective-ground switches.
- `nu_lbm` sweeps below the generic stable default.
- claims about full-plane digital-filter turbulence improvement until native FluidX3D logs and z=2 m metrics prove it.

## Current Verification Status

- Source was edited, rebuilt, and inspected.
- Official data and 80-probe filtering are verified.
- AIJ Case A smoke regression passed on this machine; the generated case, logs, artifact hashes, and external VTK hashes are recorded under `docs/experiments/casea/`.
- CityLBM builds on the local .NET SDK 8.0.423 toolchain with 0 errors and existing nullable warnings; the generated GHA is recorded in `docs/experiments/casee/results/environment_manifest.json`.
- Native FluidX3D dx=3 m and dx=2 m runs completed at official z=2 m, but the metrics remain below the release threshold.
- Effective-ground plus lower `nu_lbm` diagnostics improved the best newly-run official z=2 m result to MAE 23.972 pp, R2 -2.311768, Pearson 0.071789. This is directional improvement only; R2 remains negative and the release gate still fails.
- Error grouping for the best diagnostic run shows MAE 12.932 pp at probes with zero solid interpolation neighbors, but 35.294 pp at probes with four solid neighbors. An affine calibration of the predictions still gives only R2 0.005154, so the main blocker is spatial/protocol fidelity near walls and solid corners, not just a global velocity scale.
- `casee_audit.py` now propagates `solid_corner_neighbors_max` from native probe CSVs into residuals, XLSX output, validation reports, and `casee_solid_corner_group_metrics.csv`; this makes the near-wall/probe-protocol risk reproducible rather than hand-entered.
- A spatial-alignment diagnostic found no simple x/y flip, swap, or 90-degree transform that makes official z=2 m R2 positive. This weakens the coordinate-convention hypothesis and shifts the next optimization focus toward near-wall sampling, wall modeling, inlet turbulence, voxelization, and probe protocol fidelity.
- The native Case E generator now has a completed probe-mode diagnostic runner that writes formal `raw_trilinear` plus `nearest_valid`, `fluid_weighted`, `vertical_valid_above`, and `z_plus_half` diagnostic columns. The best diagnostic mode (`z_plus_half`) reduced MAE to 21.217 pp and raised Pearson to 0.187068, but R2 remained negative at -1.626431; this is limitations evidence, not a formal accuracy result.
- The voxel/probe protocol audit shows a strong risk split: low-risk probes have raw MAE 12.932 pp, while high-risk probes have raw MAE 32.454 pp. CityLBM now writes Case E probe protocol-risk metadata into `citylbm_run_manifest.json`, including lattice z-layer placement and the rule that `z_plus_half` cannot be used as a formal substitute.
- Because effective-ground shifting depends on native Case E's explicit STL physical-origin mapping and CityLBM's generic generator currently voxelizes around `lbm.center()`, the effective-ground switch was not migrated into the plugin defaults or GH UI in this continuation.
- Therefore, this is still an accuracy-diagnostic optimization, not a validated accuracy success.
