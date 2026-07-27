# FluidX3D District Prism 8-Direction Medium Report

evidence_type: newly_run

## Purpose

This report upgrades the whole-block TUM2TWIN prism experiment from a coarse screening layer (`dx=6 m`) to a medium grid (`dx=4 m`) for the same eight wind directions. The medium matrix is now the stronger evidence layer for the whole-block application experiment, while the coarse matrix remains a screening and comparison layer.

## Geometry

- Collision STL: `cfd_ready/district_prism_collision_z0.stl`
- Geometry source: official merged LoD3 OBJ, `TUM_CentralCampus.obj`
- Reconstruction method: high-surface footprint extraction and closed prism extrusion
- Approximate model bbox: 1540 m x 1375 m x 58 m

## FluidX3D Run

- Solver: FluidX3D 3.7, local GitHub build
- Device: NVIDIA Tesla P100-PCIE-16GB
- Wind directions: 0, 45, 90, 135, 180, 225, 270, 315 deg
- Grid: 560 x 518 x 73
- dx: 4.0 m
- Steps per direction: 10000
- Total runtime: about 490 s
- Per-direction runtime: 49-68 s
- Run script: `scripts/run_fluidx3d_district_prism_8dir_medium.ps1`
- Run summary: `F:\citylbm_fluidx3d_workspace\tum2twin_case\figures\fluidx3d_district_prism_8dir_medium4m_10k_run_summary.csv`

## Visual Outputs

- 8-direction medium panel: `figures/fluidx3d_district_prism_8dir_medium4m_10k_vr_panel_z8m.png`
- Equal-weighted medium map: `figures/fluidx3d_district_prism_8dir_medium4m_10k_equal_weighted_vr_z8m.png`
- Medium metrics CSV: `figures/fluidx3d_district_prism_8dir_medium4m_10k_metrics.csv`
- Coarse/medium comparison CSV: `figures/fluidx3d_district_prism_grid_comparison_common_heights.csv`
- Coarse/medium comparison figure: `figures/fluidx3d_district_prism_grid_comparison_common_heights.png`

## Medium Equal-Weighted Metrics

| Approx. height (m) | VR mean | VR P75 | VR P90 | VR P95 | VR max | Stagnation VR<0.2 |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0.068 | 0.066 | 0.119 | 0.194 | 1.000 | 0.952 |
| 8 | 0.172 | 0.194 | 0.336 | 0.518 | 1.105 | 0.763 |
| 20 | 0.405 | 0.527 | 0.800 | 0.987 | 1.125 | 0.227 |
| 40 | 0.675 | 0.880 | 1.030 | 1.074 | 1.130 | 0.006 |

## Common-Height Grid Sensitivity

| Height (m) | Coarse VR mean | Medium VR mean | Coarse stagnation | Medium stagnation |
|---:|---:|---:|---:|---:|
| 12 | 0.217 | 0.260 | 0.617 | 0.407 |
| 24 | 0.406 | 0.457 | 0.226 | 0.218 |
| 48 | 0.705 | 0.780 | 0.001 | 0.001 |

## Interpretation Boundary

The medium grid improves the whole-block evidence base and shows consistent flow organization with the coarse matrix, but it still does not resolve 1.5-2.0 m pedestrian height. The current results support a digital-twin-to-CFD workflow and whole-block wind-field screening at low-altitude layers. Formal pedestrian comfort/safety classification still requires either a cropped higher-resolution subdomain or a nested/local refinement strategy, plus time-averaging after spin-up.
