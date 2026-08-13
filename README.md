# CityLBM v0.3.0

CityLBM is a Grasshopper workflow plugin for urban wind simulation with FluidX3D-backed case generation, execution, VTK reading and visualization.

## What v0.3.0 fixes

- Restores a compileable Rhino 7 / Grasshopper source baseline.
- Sets plugin, assembly and package metadata to `0.3.0`.
- Adds `Wind Profile = 3` (`CustomTable`) in `Create Scene`.
- Reads validation inflow CSV files with columns `z(m), U(m/s), k(m2/s2)`.
- Uses the CSV `U(z)` table for inlet velocity interpolation instead of replacing it with a single Uref value.
- Records turbulent kinetic energy `k` in SI units and converts it to LBM units in generated case metadata.
- Adds an optional experimental STG-lite inlet path that turns isotropic `k` into bounded deterministic spectral velocity perturbations.
- Writes `case_metadata.json` and schema-tagged `domain_origin.json` for post-processing traceability.
- Adds VTK reader metadata checks so velocity units are explicit in Grasshopper output.
- Adds reusable validation metrics utilities for MAE, RMSE, bias, R2 and regression slope/intercept.
- Adds `scripts/validation_gate.py` to prevent smoke/diagnostic runs from being reported as paper-grade AIJ validation.

## Important limitation

v0.3.0 reads and converts the `k(m2/s2)` column and can optionally use it for an experimental STG-lite inlet. This is not a full digital-filter, precursor/recycling, or Reynolds-stress-resolved turbulent inflow. Final SCI-level Case A/Case E accuracy still requires strict native FluidX3D baseline comparison, empty-tunnel U/k preservation checks, longer time averaging and documented grid convergence.

## FluidX3D requirement

The Grasshopper plugin can be installed and the case-generation workflow can run directly in Rhino/Grasshopper. A real solver run still needs a valid local FluidX3D path unless a verified bundled executable is present in the user's installation. In `Run Simulation`, set `FluidX3D Path` to a FluidX3D source root that contains `FluidX3D.sln` or `Makefile` and `src/setup.cpp`.

Use `Mode 0 = Generate Case` to check Grasshopper wiring without compiling or running FluidX3D.

## AIJ Case E essentials

- Geometry: `BD_caseE.stl`, model scale `1:250`; scale by `250` before comparison with field coordinates.
- Case: `ac`
- Wind direction: `N`, represented as `(0,-1,0)` in CityLBM vector input.
- Wind profile: `WP=3`
- Wind profile CSV: `official_data/AF_caseE.csv`
- Uref metadata: `3.928296 m/s @ 15.9 m`; do not use this single value to replace the AF table.
- Pedestrian validation height: `z=2 m`

See `docs/CaseE_run_protocol.md` for the strict validation procedure.

After postprocessing, run the machine gate before using AIJ metrics in a manuscript:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseE --software citylbm --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --out <run_dir>\validation_gate_report.json
```

## Build

```powershell
dotnet build -c Release
```

The Release build outputs `bin/Release/CityLBM.dll`. For Grasshopper installation, package or copy the release assembly as `CityLBM.gha` together with required dependencies.

## Author

Shiyu Miao, Dalian University of Technology`r`nmiaoshiyu@mail.dlut.edu.cn
