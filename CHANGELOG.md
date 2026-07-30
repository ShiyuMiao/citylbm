# Changelog

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
