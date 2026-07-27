# FluidX3D + ParaView Case Template

evidence_type: blocked

This folder is a simulation-ready template, not a completed CFD run.

## Required Software

- FluidX3D source/build environment.
- OpenCL runtime for the target GPU or CPU.
- A C++ compiler supported by the selected FluidX3D build route.
- ParaView or `pvpython` for VTK visualization.

## Inputs

- `../building_collision_z0.stl`: primary LoD2-derived solid building collision boundary.
- `../ground_domain_z0.stl`: flat z0 ground/domain reference plane.
- `../lod3_building_reference_z0.stl`: detailed semantic reference, not the first collision choice.
- `../../manifests/geometry_qa.json`: geometry QA and coordinate transform.

## Files

- `setup_tum2twin_wind_pilot.cpp`: FluidX3D setup template.
- `run_matrix.csv`: eight wind directions with `blocked_by_missing_solver` status.
- `grid_memory_estimate.csv`: coarse/medium/fine grid-size estimate.
- `paraview_pipeline.md`: VTK post-processing workflow.

## Boundary

No FluidX3D executable was found on this machine during package preparation. No VTK fields, wind maps, comfort maps, or GPU performance numbers are claimed.
