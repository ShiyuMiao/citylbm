# FluidX3D Download And Next Run Plan

evidence_type: newly_run + blocked

## Disk Decision

C drive had less than 1 GB free during preparation, so it is not suitable for solver source, build output, VTK export, or ParaView post-processing files.

Selected working drive:

- `F:\citylbm_fluidx3d_workspace`

Reason:

- F drive has the largest available capacity.
- FluidX3D source, case STL files, logs, and future VTK outputs can grow without filling the system drive.
- Current preparation keeps C drive only for the lightweight project reports and manifests.

## Downloaded Solver

FluidX3D was downloaded from the official GitHub repository:

- https://github.com/ProjectPhysX/FluidX3D

Local path:

- `F:\citylbm_fluidx3d_workspace\FluidX3D`

Downloaded commit:

- `8986874e626e0aebd317ab16c420b39e30dfa273`

## Local Preparation Status

Prepared case directory:

- `F:\citylbm_fluidx3d_workspace\tum2twin_case`

Expected subfolders:

- `stl\`: CFD-ready geometry for FluidX3D voxelization.
- `setup_overlay\`: TUM2TWIN setup template to merge into FluidX3D `src/setup.cpp`.
- `paraview\`: ParaView VTK visualization workflow.
- `manifests\`: geometry and evidence manifests.
- `output\`: reserved for future FluidX3D VTK files.
- `logs\`: reserved for build and run logs.

## Not Run Yet

No compilation, no OpenCL device test, no FluidX3D simulation, and no ParaView rendering were run in this preparation step.

Next status:

- `ready_for_solver_setup`
- `blocked_by_missing_build_toolchain_or_unconfirmed_compile`

## Next Session Checklist

1. Confirm whether to compile FluidX3D locally.
2. Verify Visual Studio C++ toolchain or select another supported compiler route.
3. Verify OpenCL device availability.
4. Apply `tum2twin_case\setup_overlay\setup_tum2twin_wind_pilot.cpp` into `FluidX3D\src\setup.cpp`.
5. Build FluidX3D.
6. Run a minimal OpenCL/device smoke test.
7. Run the coarse TUM2TWIN pilot for one wind direction.
8. Export VTK.
9. Open VTK in ParaView and validate the pedestrian plane workflow.
