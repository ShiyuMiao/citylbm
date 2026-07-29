# FluidX3D coarse smoke test run report

Run date: 2026-07-26

## Status

This is a newly_run coarse smoke test for the TUM2TWIN digital-twin wind workflow. It verifies the local path from CFD-ready STL to FluidX3D voxelization, GPU execution, VTK export, and quicklook image generation. It is not a final physics-calibrated urban wind result.

## Storage

- Heavy workspace: `F:\citylbm_fluidx3d_workspace`
- TUM2TWIN raw heavy store: `D:\citylbm_tum2twin_heavy_store`
- Project reports and figures: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究`

## FluidX3D

- Source: `F:\citylbm_fluidx3d_workspace\FluidX3D`
- Commit: `8986874e626e0aebd317ab16c420b39e30dfa273`
- Executable: `F:\citylbm_fluidx3d_workspace\FluidX3D\bin\FluidX3D.exe`
- Case setup: `F:\citylbm_fluidx3d_workspace\FluidX3D\src\setup.cpp`
- Compile runtime: WinLibs MinGW in `F:\citylbm_fluidx3d_workspace\WinLibs`
- GPU used: NVIDIA Tesla P100-PCIE-16GB, device 0
- OpenCL: NVIDIA OpenCL C 3.0

## Coarse case

- Geometry: `F:\citylbm_fluidx3d_workspace\FluidX3D\stl\building_collision_z0.stl`
- Grid: `133 x 115 x 72 = 1,101,240` cells
- dx: `2.0 m`
- Wind direction: `+Y`
- Reference speed: `5.0 m/s`
- Output steps: `0`, `1000`, `2000`
- Smoke-test viscosity: `lbm_nu = 0.01`, `tau = 0.53`
- Evidence note: the viscosity is deliberately raised for numerical smoke-test stability and is not a final Reynolds-similarity claim.

## Outputs

- Log: `F:\citylbm_fluidx3d_workspace\tum2twin_case\logs\run_coarse_smoke_stable_wd000.log`
- Velocity VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\stable_u_002000u-000002000.vtk`
- Flags VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\stable_flags_002000flags-000002000.vtk`
- Status: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\stable_status_002000status-000002000.txt`
- Quicklook script: `F:\citylbm_fluidx3d_workspace\tum2twin_case\scripts\render_fluidx3d_vtk_quicklook.py`
- ParaView state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_fluidx3d_quicklook_state.pvsm`

## Quicklook statistics

The quicklook near-pedestrian plane uses z-index 2 because the coarse 2 m grid places the first building solid voxels at that level. Treat this as a low-altitude audit plane, not a precise 1.5 m pedestrian result.

- VR mean: `0.377`
- VR P75: `0.450`
- VR P90: `0.841`
- VR P95: `1.000`
- VR max: `1.132`
- Stagnation ratio, VR < 0.2: `0.196`
- Accelerated ratio, VR > 1.2: `0.000`

## ParaView

ParaView 6.1.1 ZIP was downloaded and extracted to `F:\citylbm_fluidx3d_workspace\ParaView_zip`. The MSI installer failed because C drive has insufficient space and Windows Installer still writes to `C:\Windows\Installer`.

Headless screenshot generation with `pvpython` is blocked by the current OpenGL context: `failed to get valid pixel format` and missing `OSMesa`. A `.pvsm` state file was generated for manual GUI review.

## Evidence boundary

- `newly_run`: FluidX3D compile, GPU run, VTK outputs, Python quicklook PNGs, ParaView portable extraction, ParaView state file.
- `blocked`: ParaView headless screenshot through `pvpython` in the current desktop environment.
- `blocked`: final 8-wind-direction, grid-sensitive, statistically converged SCI result has not yet been run.
