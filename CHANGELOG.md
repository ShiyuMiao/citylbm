# Changelog

## v0.4.0-rc4 - Case A smoke regression gate

- Added a reproducible AIJ Case A smoke-regression audit under `docs/experiments/casea/`.
- Generated and ran a native FluidX3D Case A smoke case with dx = 3.5 m and 2000 steps on this machine.
- Recorded the completed run log, compile log, generated case manifest, artifact hashes, and external VTK hashes without committing large VTK files.
- Wired the Case A smoke-regression status into the Case E release gate.

The release gate still blocks formal `v0.4.0`:

- Case A smoke regression now passes and can be used as a workflow non-regression guard.
- Best newly-run Case E official z=2 m result remains MAE = 23.972 pp, R2 = -2.311768, Pearson = 0.071789.
- Rhino/Grasshopper loading of the new GHA is still not independently verified.
- Case A smoke is not an accuracy-validation result and does not justify a formal predictive-accuracy claim.

## v0.4.0-rc3 - Probe-risk audit and nu diagnostic plugin switch

- Added automatic solid-corner metadata propagation in `casee_audit.py`; native probe CSVs with `solid_corner_neighbors_max` now produce probe residual risk labels and `casee_solid_corner_group_metrics.csv`.
- Updated `casee_validation_report.md` and XLSX output to include solid-corner group metrics.
- Fixed the release-gate recommendation so an existing HEAD rc tag, such as `v0.4.0-rc2`, is reported instead of always falling back to `v0.4.0-rc1`.
- Added the default-off Grasshopper `Diagnostic LBM Nu Override` input for reproducible `nu_lbm` sensitivity diagnostics without changing default solver behavior.

Case E remains below the formal accuracy gate:

- Best newly-run official z=2 m result remains MAE = 23.972 pp, R2 = -2.311768, Pearson = 0.071789.
- Solid-corner grouping shows 25 probes with zero solid interpolation neighbors have MAE = 12.932 pp and Pearson = 0.356584, while probes with 2 or 4 solid neighbors remain much worse.
- This supports a near-wall/probe-protocol limitation claim, not a predictive-accuracy claim.

## v0.4.0-rc1 - Native Case E diagnostic continuation

- Added a native FluidX3D Case E generator for official `ac+N`, scale factor 250, AF_caseE profile ingestion, binary STL conversion, and direct `casee_probe_time_mean.csv` output for the 80 official z=2 m probes.
- Completed newly-run native FluidX3D dx=3 m and dx=2 m Case E runs on this machine.
- Added diagnostic effective-ground offset and `nu_lbm` controls to the native Case E generator; these are not CityLBM defaults.
- Added a default-off Grasshopper input, `Diagnostic LBM Nu Override`, so native `nu_lbm` sensitivity can be reproduced from CityLBM case generation without changing generic defaults.
- Added MinGW/g++ fallback compilation in `FluidX3DInterface` so CityLBM can build FluidX3D when MSBuild is unavailable.
- Rebuilt CityLBM successfully with local .NET SDK 8.0.423; the generated GHA and build log are recorded in the Case E environment manifest. The build has 0 errors and existing nullable warnings.

Case E official z=2 m metrics remain below the formal accuracy gate:

- Best newly-run result so far: diagnostic dx=2 m, one effective-ground offset cell, `nu_lbm=0.001`, 48000 steps, spinup 12000, raw_trilinear, n=80.
- MAE = 23.972 percentage points, RMSE = 29.095 percentage points, bias = -20.833 percentage points.
- R2 = -2.311768 and Pearson = 0.071789.

Known blockers:

- Do not create the formal `v0.4.0` tag: the official z=2 m metric gate fails.
- Rhino/Grasshopper loading of the new GHA and Case A smoke regression are still not verified in this run.
- The dx=2 implementation currently reads full velocity fields for probe sampling; a true GPU-side probe-only reducer is needed before scaling to longer/high-resolution sweeps.
- Remaining accuracy risks are near-wall treatment, rough/effective ground modeling, inlet turbulence/digital-filter fidelity, LBM viscosity/Reynolds matching, voxelization alignment, and official probe sampling at solid corners.

## v0.3.0-rc1 - AIJ Case E accuracy diagnostic candidate

- Added source-level plugin optimization from Experiments 1-3: an explicit AIJ Case E preset input, Case E protocol policy, AF_caseE inlet-profile generation, lattice velocity cap scaling, and per-case run manifest output.
- Added an AIJ Case E `ac+N` preset for official z=2 m validation.
- Downloaded the official Zenodo Case E files into `docs/experiments/casee/official_data/` and recorded size, SHA256, Zenodo MD5, download time, and source URL in `docs/experiments/casee/data_manifest.csv`.
- Added the Case E protocol, native FluidX3D run matrix, and evidence inventory.
- Added `casee_audit.py` to generate official 80-probe filters, AF inlet-profile audits, residual tables, XLSX/PNG outputs, environment manifests, validation reports, and release-gate JSON.
- Added `release_gate.py`, which fails closed unless the formal v0.3.0 criteria pass.
- Added CityLBM config entries for Case E preset constants and diagnostic-only sampling/wall-ground switches.

Known blockers:

- The current machine has no .NET SDK/MSBuild command-line environment, so CityLBM source build is blocked.
- Native FluidX3D execution is blocked because `FluidX3D`, `nvidia-smi`, `nvcc`, and Visual Studio C++ build tools are not available from the command line.
- No formal v0.3.0 tag should be created until official z=2 m metrics are generated from native dx=3 m and dx=2 m runs and the full release gate passes.
