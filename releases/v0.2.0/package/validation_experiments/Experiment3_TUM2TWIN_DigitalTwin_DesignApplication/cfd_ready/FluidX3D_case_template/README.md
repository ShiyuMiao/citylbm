# FluidX3D + ParaView Case Template

evidence_type: newly_run + blocked

This folder began as a simulation-ready template before FluidX3D was available. It is now superseded by the executed FluidX3D-native runs recorded in `../../reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md` and the ParaView/statistical post-processing reports. The files here remain as reusable setup examples and input documentation, not as the sole evidence of the completed experiment.

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
- `run_matrix.csv`: original eight-direction pre-solver template retained for provenance; superseded by the executed FluidX3D run scripts and logs under `../../scripts/` and `../../logs/`.
- `grid_memory_estimate.csv`: coarse/medium/fine grid-size estimate.
- `paraview_pipeline.md`: VTK post-processing workflow.

## Boundary

FluidX3D was later downloaded, built, and used for the main dx=2 m core-prism screening experiment. This template alone should therefore not be cited as a missing-solver artifact. Cite the executed run reports for wind-field results.

Remaining limitations are still active: no field-measured validation, no wind-tunnel validation, no formal annual comfort/safety exceedance assessment, no pollutant transport run, and no completed CityLBM-Grasshopper end-to-end run are claimed.
