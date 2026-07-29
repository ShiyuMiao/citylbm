# Manual Review Checklist

evidence_type: newly_run

## 1. Rhino / Geometry Review

Open in Rhino:

- `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\rhino\TUM2TWIN_Downtown_district_CFD_layered_geometry.3dm`

Check:

- user 3dm matches screenshot visually;
- user 3dm is one photogrammetry layer, not a semantic CFD model;
- generated district 3dm contains `CFD_Collision_whole_district`;
- exact textured browsing should use OBJ/MTL/JPG, not 3dm.

## 2. CFD Geometry Review

Open or inspect:

- `figures/core_photogrammetry_extent_prism_collision_audit.png`
- `figures/district_prism_collision_audit.png`
- `reports/cfd_ready_geometry_qa.md`

Check:

- core local prism covers the screenshot/photogrammetry extent;
- district prism covers the broader campus/block context;
- user photogrammetry STL is not accepted as final collision because it is not watertight and voxelizes poorly.

## 3. Main Wind Result Review

Open:

- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`

Check:

- z~2 m pedestrian layer is shown;
- building masks are coherent closed-prism solids;
- time-mean maps are visually consistent across wind directions;
- Open-Meteo weighted map is interpreted as climate-proxy sensitivity, not measured annual comfort probability.

## 4. Metrics Review

Open:

- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv`
- `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`

Check key values:

- time-mean equal-weighted z~2 m: `VR_mean ≈ 0.076`, `VR_P95 ≈ 0.241`, `stagnation VR<0.2 ≈ 0.934`;
- Open-Meteo weighted z~2 m: `VR_mean ≈ 0.077`, `VR_P95 ≈ 0.246`, `stagnation VR<0.2 ≈ 0.931`;
- dominant proxy velocity-to sectors are 90°, 45°, 270°, and 0°.

## 5. ParaView Review

Open:

- `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\paraview.exe`

Load:

- `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm`
- `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_user_photogrammetry_dx2m_pilot_audit_pipeline.pvsm`

Check:

- `core_prism_collision_z0` loads;
- `core_prism_wd000_velocity_mag_slice_z2m` can be displayed;
- photogrammetry pilot shows fragmented/shell-like voxelization behavior.

## 6. Evidence Boundary Review

Read:

- `reports/claim_boundary.md`
- `reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md`
- `reports/wind_climate_weighted_core_prism_report.md`
- `paper_text/results_section_zh.md`
- `paper_text/discussion_limitations_zh.md`
- `paper_text/figure_table_index_zh.md`

Confirm that the paper does not claim:

- measured validation;
- final Lawson/NEN/AIJ exceedance comfort classes;
- pollutant dispersion;
- final Reynolds-scaled accuracy;
- photogrammetry/3DGS visual mesh as a closed collision boundary.
