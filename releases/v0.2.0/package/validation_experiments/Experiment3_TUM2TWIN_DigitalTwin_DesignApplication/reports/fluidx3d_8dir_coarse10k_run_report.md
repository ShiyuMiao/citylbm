# FluidX3D 8-direction coarse10k run report

Run date: 2026-07-26

## Purpose

This run is the first 8-direction FluidX3D coarse pilot for the TUM2TWIN digital-twin wind workflow. It verifies that the case can be parameterized by wind direction, executed repeatedly, exported to VTK, and postprocessed into the SCI-level metric framework.

This is not the final paper-level converged result. The current grid is coarse (`dx = 2 m`) and uses a deliberately stable smoke-test viscosity (`lbm_nu = 0.01`). It is suitable for pipeline validation, wind-direction workflow testing, and identifying QA issues before medium/fine simulations.

## Case configuration

- Solver: FluidX3D 3.7
- Source path: `F:\citylbm_fluidx3d_workspace\FluidX3D`
- Case setup: `F:\citylbm_fluidx3d_workspace\FluidX3D\src\setup.cpp`
- GPU: NVIDIA Tesla P100-PCIE-16GB, device 0
- Grid: `133 x 115 x 72 = 1,101,240` cells
- dx: `2.0 m`
- Uref: `5.0 m/s`
- Wind convention: `0 deg = +Y`, `90 deg = +X`
- Directions: `0, 45, 90, 135, 180, 225, 270, 315 deg`
- Steps per direction: `10000`
- Collision STL: `F:\citylbm_fluidx3d_workspace\FluidX3D\stl\building_collision_z0.stl`
- Output directory: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output`

## Output evidence

- Batch script: `F:\citylbm_fluidx3d_workspace\tum2twin_case\scripts\run_fluidx3d_8dir_coarse.ps1`
- Postprocess script: `F:\citylbm_fluidx3d_workspace\tum2twin_case\scripts\postprocess_fluidx3d_8dir_matrix.py`
- Metrics CSV: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_8dir_coarse10k_metrics.csv`
- VR panel: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_8dir_coarse10k_vr_panel.png`
- Per-direction logs: `F:\citylbm_fluidx3d_workspace\tum2twin_case\logs\run_matrix_wd*_coarse10k.log`
- Final velocity VTK files: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_wd*_coarse10k_u_finalu-000010000.vtk`

## Near-pedestrian coarse metrics

The audit plane uses `z-index = 2`, approximately `4 m`, because the current `dx = 2 m` coarse grid places the first stable building solid voxels at this layer. The final paper run should use a finer grid or interpolation to report `1.5 m / 2.0 m` pedestrian height directly.

| case | VR mean | VR P90 | VR P95 | VR max | stagnation VR<0.2 | acceleration VR>1.2 |
|---|---:|---:|---:|---:|---:|---:|
| wd000 | 0.372 | 0.841 | 1.000 | 1.132 | 0.202 | 0.000 |
| wd045 | 0.374 | 0.790 | 1.000 | 1.082 | 0.232 | 0.000 |
| wd090 | 0.364 | 0.790 | 1.000 | 1.131 | 0.149 | 0.000 |
| wd135 | 0.378 | 0.790 | 1.000 | 1.083 | 0.217 | 0.000 |
| wd180 | 0.386 | 0.842 | 1.000 | 1.132 | 0.159 | 0.000 |
| wd225 | 0.373 | 0.790 | 1.000 | 1.082 | 0.221 | 0.000 |
| wd270 | 0.360 | 0.788 | 1.000 | 1.131 | 0.199 | 0.000 |
| wd315 | 0.363 | 0.790 | 1.000 | 1.082 | 0.257 | 0.000 |
| equal-weighted | 0.371 | 0.803 | 1.000 | 1.107 | 0.205 | 0.000 |

## QA interpretation

- All 8 directions produced VTK outputs and logs.
- The velocity fields are finite and not blank.
- The current coarse grid visibly reflects boundary/domain effects and low-resolution building voxelization.
- The result should be used to debug workflow and estimate metric scripts, not to support final urban wind claims.

## Next SCI-level steps

1. Increase collision geometry coverage from four-building pilot to a larger street-canyon/open-space subdomain.
2. Run medium and fine grids; target direct pedestrian height sampling.
3. Add time-window averaging after spin-up rather than single final snapshot metrics.
4. Introduce wind-rose weighting and optional pollutant scalar transport.
5. Use ParaView GUI or OSMesa-enabled pvpython for publication screenshots and manual audit.

## Evidence boundary

- `newly_run`: 8-direction FluidX3D coarse10k VTK, logs, metrics, panel image.
- `blocked`: final grid-sensitive SCI conclusions.
- `blocked`: measured wind-field validation or wind-tunnel closure for this site.
