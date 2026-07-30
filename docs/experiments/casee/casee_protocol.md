# AIJ Case E Protocol for CityLBM v0.3.0 Gate

This protocol freezes the validation target for CityLBM Experiment 2.

## Fixed Setup

- Case: AIJ Case E.
- Condition: `ac`.
- Wind direction: `N`.
- Solver wind vector: `(0, -1, 0)`, subject to a recorded coordinate transform if the solver convention differs.
- Geometry: `BD_caseE.stl`.
- Scale factor: `250`.
- Reference velocity: `Uref = 3.928296 m/s`.
- Reference height: `zref = 15.9 m`.
- Formal validation height: official `z = 2 m`.
- Probe set: `RS_caseE.csv` filtered by `case=ac` and `Wind_direction=N`; expected count is 80.

## Evidence Semantics

- `newly_run`: generated in the current session by a recorded command.
- `preexisting_artifact`: already present in the repository or release package and inspected in this session.
- `user_claim`: stated by the user or older notes but not independently verified in this session.

Only `newly_run` and documented `preexisting_artifact` entries may support manuscript claims. `user_claim` entries are investigation context only.

## Prohibitions

- Do not use `z+4.5 m`, `z_plus_half`, or any other offset height as the formal z=2 m validation result.
- Do not describe a smoke run as accuracy validation.
- Do not migrate diagnostic settings into CityLBM defaults unless the native FluidX3D run improves official z=2 m metrics.
- Do not create the formal `v0.3.0` tag unless the release gate passes.

## Required Native FluidX3D Runs

The official accuracy gate requires at least:

- `dx=3 m`, `steps >= 48000`, `spinup >= 12000`.
- `dx=2 m`, `steps >= 48000`, `spinup >= 12000`.
- Probe-only time mean written to `casee_probe_time_mean.csv`.
- Full-plane digital-filter inlet using `AF_caseE.csv` `z,U,k`.
- Completed logs and postprocessed residuals for all 80 official probes.

## CityLBM v0.2.1-v0.2.5 Feedback Scope

- v0.2.1: Case E preset, official probe filtering, case manifest generation.
- v0.2.2: AF profile ingestion and full-plane inlet audit outputs.
- v0.2.3: probe sampling modes and per-probe residual/risk reporting.
- v0.2.4: near-wall, rough-wall, and effective-ground switches as experimental controls only.
- v0.2.5: automated Case E report, evidence inventory, run manifest, and release-gate output.

Default behavior may change only after native FluidX3D evidence shows stable improvement at official z=2 m.

