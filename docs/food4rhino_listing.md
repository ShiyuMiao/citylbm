# CityLBM v0.3.0 Food4Rhino Listing Draft

## Title
CityLBM - Grasshopper workflow for FluidX3D urban wind simulation

## Short Description
Grasshopper components for preparing FluidX3D urban wind cases, reading VTK output, visualizing wind fields, and auditing AIJ validation evidence.

## Long Description

CityLBM connects Rhino/Grasshopper geometry workflows with FluidX3D-based LBM case generation and post-processing. The v0.3.0 branch is focused on validation readiness: it records the inflow profile, grid, domain origin, VTK averaging window, probe mapping and protocol gates so AIJ-style validation runs can be audited instead of treated as screenshots only.

### Key Features
- Scene, domain and building setup components for Rhino/Grasshopper.
- CustomTable inflow support for `z(m), U(m/s), k(m2/s2)` profiles.
- Generated FluidX3D `setup.cpp` with traceable profile arrays and metadata.
- VTK reading, multi-frame averaging, slicing, probe extraction and visualization.
- Validation metrics for MAE, RMSE, bias, R2, regression slope/intercept and probe coverage.
- Case A native-baseline and Case E run protocols for reproducible AIJ validation packages.

### What's New in v0.3.0
- Standardized plugin and assembly metadata to `0.3.0`.
- Uses the full CustomTable `U(z)` inlet profile; `Uref` is kept only as metadata/normalization context.
- Samples CustomTable `U(z)`/`k(z)` using the CFD domain origin and records `ProfileOriginZM` for coordinate audits.
- Reads, converts and records `k(m2/s2)` in SI and LBM units.
- Optional STG-lite diagnostic inlet from isotropic `k`; it is blocked unless every CustomTable row has a valid `k`.
- Records `SyntheticTurbulentInletRequested`, `SyntheticTurbulentInletInjected` and `SyntheticTurbulentInletBlockedReason`.
- Adds validation gates for time averaging, boundary evidence, inlet U/k preservation, native FluidX3D parity, probe mapping and coordinate/normalization checks.

### FluidX3D Requirement
The plugin can be installed and `Mode 0 = Generate Case` can run without launching FluidX3D. A real solver run still requires the user to provide an explicit `FluidX3D Path` in the `Run Simulation` component.

For controlled validation, the path must point to a complete FluidX3D source root containing a build file (`FluidX3D.sln`, `Makefile` or `CMakeLists.txt`) and `src/setup.cpp`, `src/defines.hpp`, `src/lbm.hpp`, `src/lbm.cpp`. Auto-detected paths are not accepted as paper-grade baseline evidence.

### Validation Status
v0.3.0 is validation-ready, not a completed benchmark claim. Case A and Case E must be rerun on the user's experimental machine with explicit FluidX3D source evidence, newly generated VTK files, at least 40 final-window frames spanning at least 20000 solver steps, inlet U/k preservation checks, boundary-protocol evidence and grid sensitivity before SCI-level accuracy claims are made.

### System Requirements
- Windows 10/11
- Rhino 7 with Grasshopper
- .NET Framework 4.8
- GPU/OpenCL environment suitable for FluidX3D
- Local FluidX3D source/build environment for Mode 1/2/3 solver runs

### Installation
1. Copy `CityLBM.gha`, `Newtonsoft.Json.dll` and `NLog.dll` to `%APPDATA%\Grasshopper\Libraries\`.
2. Unblock downloaded files in Windows file properties if needed.
3. Restart Rhino 7 and Grasshopper.
4. For case generation only, use `Run Simulation / Mode 0`.
5. For solver execution or validation, set `Run Simulation / FluidX3D Path` to the explicit local FluidX3D source root.

### References
- AIJ CFD Guidebook: https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm
- FluidX3D: https://github.com/ProjectPhysX/FluidX3D
- GitHub: https://github.com/ShiyuMiao/citylbm

### License
MIT License
