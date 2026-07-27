# ParaView VTK Core Wind Field Statistical Analysis
evidence_type: newly_run
## Data and Tooling
- ParaView/pvpython path: `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\pvpython.exe`
- ParaView state opened/saved from VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_timesampled_8dir_vtk_review.pvsm`
- VTK source directory: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output`
- Wind directions: 0, 45, 90, 135, 180, 225, 270, 315 deg
- Grid metadata: `{'dims_xyz': (320, 390, 60), 'origin': (-318.999982, -388.999984, -59.0000008), 'spacing': (2.0, 2.0, 2.0), 'array_name': 'data', 'vtk_type': 'float', 'n_components': 3}`
- Speed ratio definition: `VR = |U| / 5.0 m/s`; statistics use `flags==0` open cells only. `flags==1` is solid/building and `flags==2` is boundary.
## Core Pedestrian-Layer Robustness
- valid_open_cells_all_8_dirs_flag0: 109520
- all_direction_stagnation_ratio_vr_lt_0p2: 0.8837929145361578
- robust_stagnation_ratio_freq_ge_6_of_8: 0.9267531044558072
- directionally_accelerated_ratio_freq_ge_2_of_8: 0.012856099342585829
- mean_directional_std_vr: 0.024149881675839424
- p95_directional_range_vr: 0.1999014988541603
## Direction-Level Pedestrian Statistics, z~2 m
| wind_deg | mean VR | P95 VR | max VR | VR<0.2 ratio | VR>0.6 ratio |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0648 | 0.1990 | 0.7007 | 0.9522 | 0.0058 |
| 45 | 0.0673 | 0.2155 | 0.7242 | 0.9348 | 0.0065 |
| 90 | 0.0631 | 0.2200 | 0.7024 | 0.9432 | 0.0071 |
| 135 | 0.0616 | 0.2123 | 0.7243 | 0.9347 | 0.0065 |
| 180 | 0.0611 | 0.1972 | 0.7005 | 0.9522 | 0.0058 |
| 225 | 0.0654 | 0.2138 | 0.7241 | 0.9348 | 0.0065 |
| 270 | 0.0656 | 0.2212 | 0.7025 | 0.9426 | 0.0071 |
| 315 | 0.0659 | 0.2162 | 0.7242 | 0.9354 | 0.0065 |
## Vertical Recovery
| model height | mean VR across directions | mean P95 VR | mean VR<0.2 ratio |
|---:|---:|---:|---:|
| 2.0 m | 0.0644 | 0.2119 | 0.9412 |
| 4.0 m | 0.1759 | 0.5818 | 0.6581 |
| 10.0 m | 0.3960 | 1.0087 | 0.3813 |
| 20.0 m | 0.5963 | 1.0977 | 0.2914 |
| 40.0 m | 1.0486 | 1.2629 | 0.0000 |
## Building-Related Stepwise Interpretation
1. Solid/open separation: use `flags==1` as building collision cells and exclude `flags==2` boundary cells from pedestrian statistics.
2. Near-building zone: group open cells by 2D distance to the nearest solid cell at z~2 m: 0-4 m, 4-10 m, 10-20 m, and >20 m.
3. Morphology interpretation: compare VR and stagnation ratios across distance bins to distinguish facade-adjacent shelter, channelized passages, and open-space recovery.
4. Claim boundary: these are CFD-derived aerodynamic diagnostics, not field-validated wind comfort classes.
## ParaView Rendering Boundary
- The VTK files were successfully loaded by `pvpython` and saved into the `.pvsm` review state above.
- Automated headless screenshots remain blocked on this Windows environment because ParaView cannot initialize a valid OpenGL pixel format and reports missing `osmesa.dll`.
- The PNG audit figures in this report are generated directly from the same VTK arrays and flags with Python/Matplotlib for immediate manual review; they are statistical audit maps, not ParaView-rendered screenshots.
## Outputs
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_pedestrian_stats_by_direction.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_vertical_profile_stats.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_building_distance_stats.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_robustness_stats.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_statistical_maps_z2m.png`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\paraview_vtk_core_dx2m_direction_vertical_building_stats.png`
