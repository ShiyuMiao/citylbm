# CityLBM Plugin Optimization Audit from Experiments 1-3

Generated in the `codex/experiment-2-aij-casee-citylbm-v0.3.0-rc` branch.

## Original Plugin Behavior Reviewed

- `RunSimulationComponent` exposed generic wind speed, viscosity, timestep, and save interval controls, but had no explicit AIJ Case E validation preset.
- `SimulationSettings` defaulted to short smoke-run scale settings (`TimeSteps=2000`, `SaveInterval=1000`) and did not record spin-up, Uref, zref, probe protocol, or evidence boundaries.
- `FluidX3DInterface.GenerateSetupCpp()` initialized a uniform inlet velocity field and used the same constant velocity on inlet boundary cells.
- Generated case folders did not include a machine-readable run manifest tying the FluidX3D case to the experiment protocol.

## Experiment-Derived Changes

### Experiment 1 / Case A Boundary

Case A remains a smoke-regression guard. No accuracy-model default was changed from Case A alone. The release gate still requires a Case A smoke regression before any formal v0.3.0 release.

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
- claims about full-plane digital-filter turbulence improvement until native FluidX3D logs and z=2 m metrics prove it.

## Current Verification Status

- Source was edited and statically inspected.
- Official data and 80-probe filtering are verified.
- Formal CityLBM build remains blocked because no .NET SDK/MSBuild is installed.
- Native FluidX3D validation remains blocked because FluidX3D/GPU runtime is unavailable.
- Therefore, this is an accuracy-oriented plugin optimization, not a validated accuracy success.
