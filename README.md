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
- Adds boundary-protocol diagnostics for domain clearance, boundary types and approximate frontal/plan blockage ratios.
- Adds `scripts/run_native_fluidx3d_case.py` to preflight a complete external FluidX3D source root, optionally install a
  CityLBM-generated case into it, and write a hash-traceable native baseline manifest before any native-vs-CityLBM
  accuracy claim.

## Important limitation

v0.3.0 reads and converts the `k(m2/s2)` column and can optionally use it for an experimental STG-lite inlet. This is not a full digital-filter, precursor/recycling, or Reynolds-stress-resolved turbulent inflow. The boundary audit records clearance and approximate blockage, but it is a screening diagnostic, not a substitute for the official AIJ wind-tunnel protocol. Final SCI-level Case A/Case E accuracy still requires strict native FluidX3D baseline comparison, empty-tunnel U/k preservation checks, longer time averaging, boundary-protocol justification and documented grid convergence.

## FluidX3D requirement

The Grasshopper plugin can be installed and the case-generation workflow can run directly in Rhino/Grasshopper. `Mode 0 = Generate Case` can be used without compiling or running FluidX3D. A controlled native or CityLBM-driven solver run still requires the user to set `Run Simulation / FluidX3D Path` explicitly; v0.3.0 does not treat auto-detected paths as paper-grade baseline evidence.

The `FluidX3D Path` input must point to a complete deployable FluidX3D source root containing `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`, plus `src/setup.cpp`, `src/defines.hpp`, `src/lbm.hpp` and `src/lbm.cpp`.

Use `Mode 0 = Generate Case` to check Grasshopper wiring without compiling or running FluidX3D.

On the experiment workstation, use the native runner before launching a strict FluidX3D baseline:

```powershell
python scripts\run_native_fluidx3d_case.py --case-dir <case_dir> --fluidx3d-source <FluidX3D_source_root> --out <case_dir>\native_fluidx3d_baseline_manifest.json --baseline-id <baseline_id> --expected-aij-case CaseA --expected-wind-direction N --time-steps 40000 --vtk-save-interval 1000 --expected-vtk-frame-count 40 --install
```

Add `--build` and `--run` only when the workstation is ready for the actual native solver run. The script does not run
CFD by default. The preflight manifest remains diagnostic-only when the planned VTK schedule is shorter than 40 frames
or spans fewer than 20000 solver steps in the final averaging window.

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
python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS_caseE.csv> --metadata <case_metadata.json> --case ac --wind-direction N --u-ref 3.928296 --z-ref 15.9 --out <validation_metrics.csv>
python scripts\validation_gate.py <run_dir> --case CaseE --software citylbm --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --out <run_dir>\validation_gate_report.json
```

## Build

```powershell
dotnet build -c Release
```

The Release build outputs `bin/Release/CityLBM.dll`. For Grasshopper installation, package or copy the release assembly as `CityLBM.gha` together with required dependencies.

## Author

Shiyu Miao, Dalian University of Technology`r`nmiaoshiyu@mail.dlut.edu.cn
