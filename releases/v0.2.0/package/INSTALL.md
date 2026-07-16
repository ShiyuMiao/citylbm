# Installation

## Rhino 7/8 Grasshopper Install

1. Close Rhino.
2. Copy these files into `%APPDATA%\Grasshopper\Libraries\`:
   - `CityLBM.gha`
   - `Newtonsoft.Json.dll`
   - `NLog.dll`
3. If Windows marks downloaded files as blocked, right-click each file, open `Properties`, and choose `Unblock`.
4. Start Rhino 7 or Rhino 8.
5. Open Grasshopper and confirm the `CityLBM` tab is visible.

## FluidX3D Setup

CityLBM v0.2.0 does not bundle FluidX3D. For full simulations, download or clone FluidX3D separately and set the `FluidX3D Path` input in `Run Simulation`.

The selected folder must contain:

- `FluidX3D.sln` or `Makefile`
- `src/setup.cpp`

If you only want to verify the Grasshopper workflow, use `Run Simulation` with `Mode = 0`. This generates the FluidX3D case files without compiling or running the solver.

## Quick Check

Open `examples/AIJ_CaseA/grasshopper/AIJ_CaseA_validation.gh` and confirm the basic component chain is visible:

`Create Scene -> Add Buildings -> Generate Grid -> Run Simulation`.

Set `Run Simulation` to `Mode = 0` first. A successful check produces a case directory containing `setup.cpp`, `defines.hpp`, `buildings.stl`, and `domain_origin.json`.
