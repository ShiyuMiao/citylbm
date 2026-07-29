# ParaView Visualization Package

evidence_type: newly_run + blocked

## Available ParaView Artifacts

- Portable ParaView executable: `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\paraview.exe`
- pvpython executable: `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\pvpython.exe`
- Whole-district medium audit state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_district_prism_medium4m_8dir_audit_pipeline.pvsm`
- Whole-district state-generation script: `scripts/create_paraview_district_prism_medium_state.py`
- State contents verified: `district_prism_collision_z0`, `wd000_velocity_mag_slice_z8m`, `wd000_velocity_mag_slice_z20m`, `wd000_velocity_mag_slice_z40m`, and 8 medium-grid wind-direction VTK sources.
- Local core-prism dx=2 m audit state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm`
- Local core-prism state-generation script: `scripts/create_paraview_core_prism_dx2m_state.py`
- Current strongest Matplotlib review figures: `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png` and `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`
- User photogrammetry pilot audit state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_user_photogrammetry_dx2m_pilot_audit_pipeline.pvsm`
- User photogrammetry state-generation script: `scripts/create_paraview_user_photogrammetry_pilot_state.py`
- WD000 no-render pipeline state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_full_lod2_wd000_coarse4m_10k_pipeline_no_render.pvsm`
- State-generation script: `scripts/create_paraview_full_lod2_pipeline_state.py`
- RenderView state attempt script: `scripts/create_paraview_full_lod2_state.py`
- OpenGL failure log: `F:\citylbm_fluidx3d_workspace\tum2twin_case\logs\paraview_create_full_lod2_state.log`

## Manual Review Procedure

1. Open `paraview.exe`.
2. Load `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_district_prism_medium4m_8dir_audit_pipeline.pvsm`.
3. In the Pipeline Browser, enable `district_prism_collision_z0` and one of `wd000_velocity_mag_slice_z8m`, `wd000_velocity_mag_slice_z20m`, or `wd000_velocity_mag_slice_z40m`.
4. Color the active slice by `velocity_mag`, rescale to the visible data range, and use a top-down camera for comparison with `figures/fluidx3d_district_prism_8dir_medium4m_10k_vr_panel_z8m.png`.
5. Use the hidden wind-direction sources `wd045...wd315...` to create additional `Calculator` and `Slice` filters manually if a direction-specific ParaView audit is needed.

## Local Pedestrian-Height Review

1. Open `paraview.exe`.
2. Load `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm`.
3. Enable `core_prism_collision_z0` and `core_prism_wd000_velocity_mag_slice_z2m`.
4. Color the slice by `velocity_mag` and compare with `figures/fluidx3d_core_prism_8dir_dx2m_10k_vr_panel_z2m.png`.
5. Use the `core_prism_wd045...wd315...` VTK sources to create the same calculator/slice filters for other wind directions if needed.

Note: the ParaView state currently exposes final-snapshot VTK sources. The time-sampled VTK files are available in `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\` with labels `core_prism_avg_wdXXX_dx2m_spin6k_s3`. The publication-review figures should use the time-sampled Matplotlib outputs unless a ParaView GUI review is specifically needed.

## Time-Sampled Core VTK Review State

evidence_type: newly_run

- ParaView version checked by pvpython: `6.1`.
- Non-C installation used: `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\`.
- New time-sampled state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_timesampled_8dir_vtk_review.pvsm`.
- State-generation script: `scripts/create_paraview_core_timesampled_vtk_state.py`.
- State contents: `core_prism_collision_z0`, 8 wind-direction VTK velocity sources, `VR=mag(data)/5.0` calculators, and z=2/10/20/40 m slices for every direction.

Manual review:

1. Open `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\paraview.exe`.
2. Load `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_timesampled_8dir_vtk_review.pvsm`.
3. Toggle one `wdXXX_VR_slice_z2m` layer at a time and keep `core_prism_collision_z0` visible.
4. Color by `VR`; use the same color range when comparing wind directions.
5. Compare against `figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png` and `figures/paraview_vtk_core_dx2m_direction_vertical_building_stats.png`.

## VTK Statistical Audit Before Architectural Interpretation

evidence_type: newly_run

- Report: `reports/paraview_vtk_core_wind_statistics_and_building_analysis.md`.
- Direction statistics: `figures/paraview_vtk_core_dx2m_pedestrian_stats_by_direction.csv`.
- Vertical profile: `figures/paraview_vtk_core_dx2m_vertical_profile_stats.csv`.
- Building-distance groups: `figures/paraview_vtk_core_dx2m_building_distance_stats.csv`.
- Robustness metrics: `figures/paraview_vtk_core_dx2m_robustness_stats.csv`.
- Manual audit maps: `figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png`.
- Manual audit summary: `figures/paraview_vtk_core_dx2m_direction_vertical_building_stats.png`.

## Photogrammetry STL Pilot Review

1. Open `paraview.exe`.
2. Load `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_user_photogrammetry_dx2m_pilot_audit_pipeline.pvsm`.
3. Enable `user_photo_velocity_mag_slice_z2m`, `z4m`, `z10m`, `z20m`, and `z40m` one at a time.
4. Compare with `figures/fluidx3d_user_photo_wd000_dx2m_2k_voxel_vr_audit.png`.
5. Use this only as a geometry-readiness/voxelization audit. It is not the final wind comfort result.

## Blocked Item

Headless ParaView screenshots are blocked on this Windows environment because `pvpython` cannot create a valid OpenGL pixel format and reports missing `osmesa.dll`. This does not block FluidX3D solving or Matplotlib audit-image generation, but it does block automated ParaView screenshots until an OSMesa/Mesa software rendering runtime is installed or the ParaView GUI is used interactively.
