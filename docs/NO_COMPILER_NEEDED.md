# CityLBM v0.3.0 FluidX3D Path Policy

This file replaces the older "no compiler needed" draft. That draft described a bundled pre-compiled `FluidX3D.exe` workflow. It is not the validation policy for CityLBM v0.3.0.

## What Runs Directly

After installing the Grasshopper plugin, users can directly:

- open the CityLBM Grasshopper components;
- build a scene, domain and grid;
- import building geometry;
- use `Run Simulation / Mode 0 = Generate Case`;
- generate `setup.cpp`, `defines.hpp`, `domain_origin.json`, `case_metadata.json` and validation audit files;
- inspect or share the generated case package.

This workflow does not require launching FluidX3D.

## What Still Requires FluidX3D

Any real CFD solve requires `Run Simulation / FluidX3D Path` to point to an explicit local FluidX3D source/build root.

For v0.3.0 validation, the path should contain:

- `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`;
- `src/setup.cpp`;
- `src/defines.hpp`;
- `src/lbm.hpp`;
- `src/lbm.cpp`.

CityLBM records this path and source validation in the native baseline manifest. Auto-detected paths or copied executables are not sufficient evidence for paper-grade Case A or Case E validation.

## Why This Is Stricter

The goal of v0.3.0 is not a demo-only one-click package. It is a validation-ready research branch. For AIJ validation, the run package must prove which FluidX3D source, generated `setup.cpp`, grid, time steps, VTK frames, inlet treatment, boundary treatment and post-processing metrics produced the result.

Bundling an opaque executable may be convenient for demonstrations, but it is weak evidence for SCI-level validation because the solver source, compile settings and boundary/inlet implementation cannot be audited.

## Practical User Guidance

- Use `Mode 0` when checking Grasshopper wiring or preparing a case.
- Use `Mode 1/2/3` only after setting an explicit `FluidX3D Path`.
- Archive the generated case directory, solver log, VTK files, `case_metadata.json`, `domain_origin.json`, `validation_protocol_audit.json` and metrics outputs.
- Do not describe a run as paper-grade unless `validation_gate.py` passes with native FluidX3D baseline, time averaging, inlet U/k preservation, boundary evidence, probe mapping and grid-sensitivity evidence.
