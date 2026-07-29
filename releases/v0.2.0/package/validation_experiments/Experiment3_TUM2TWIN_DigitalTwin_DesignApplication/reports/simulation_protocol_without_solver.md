# FluidX3D / ParaView Simulation Protocol

evidence_type: newly_run + blocked

Note: this file keeps the original requested filename, but the local machine now has a working FluidX3D build and completed simulations. The remaining blocked items are not solver installation, but measured validation, formal comfort probability, pollutant dispersion, and automated headless ParaView screenshots.

## Solver Environment

- FluidX3D repo: `F:\citylbm_fluidx3d_workspace\FluidX3D`
- executable: `F:\citylbm_fluidx3d_workspace\FluidX3D\bin\FluidX3D.exe`
- GPU used: NVIDIA Tesla P100-PCIE-16GB
- setup file: `F:\citylbm_fluidx3d_workspace\FluidX3D\src\setup.cpp`
- output root: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output`

`setup.cpp` supports environment-controlled runs:

- `TUM2TWIN_STL`
- `TUM2TWIN_NX`, `TUM2TWIN_NY`, `TUM2TWIN_NZ`
- `TUM2TWIN_DX`
- `TUM2TWIN_WIND_DEG`
- `TUM2TWIN_RUN_LABEL`
- `TUM2TWIN_RUN_STEPS`
- `TUM2TWIN_SAMPLE_SPINUP`
- `TUM2TWIN_SAMPLE_INTERVAL`
- `TUM2TWIN_SAMPLE_COUNT`

## Current Main Simulation Protocol

Geometry:

- `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`

Grid:

- `320 x 390 x 60`
- `dx = 2.0 m`

Wind directions:

- `0, 45, 90, 135, 180, 225, 270, 315 deg`

Sampling:

- spin-up: `6000 steps`
- samples: `8000, 10000, 12000 steps`
- sample count: `3`
- aggregation: time mean per direction, then 8-direction equal weighting or Open-Meteo 2024 proxy weighting

Scripts:

- run: `scripts/run_fluidx3d_core_prism_timesampled_8dir_dx2m.ps1`
- postprocess: `scripts/postprocess_core_prism_timesampled_8dir_dx2m.py`
- wind-climate weighting: `scripts/postprocess_windrose_weighted_core_prism.py`

## Visualization Protocol

Matplotlib audit figures are the current reliable publication-review figures:

- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`

ParaView is available for manual GUI review:

- `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\paraview.exe`
- main state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm`
- photogrammetry counterexample state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_user_photogrammetry_dx2m_pilot_audit_pipeline.pvsm`
- district screening state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_district_prism_medium4m_8dir_audit_pipeline.pvsm`

Headless ParaView RenderView screenshots are blocked because this Windows environment cannot create a valid OpenGL pixel format and reports missing `osmesa.dll`. This does not affect FluidX3D runs or Matplotlib VTK post-processing.

## Remaining Protocol Limits

Current results support local VR/stagnation screening. They do not yet support:

- final Lawson/NEN/AIJ exceedance comfort classes;
- field or wind-tunnel validation;
- pollutant dispersion;
- final Reynolds-scaled accuracy claims;
- automated ParaView screenshots without GUI or OSMesa/Mesa runtime.
