# FluidX3D Full LoD2 8-Direction Coarse Matrix Report

evidence_type: newly_run

## Run Matrix

- Geometry: `cfd_ready/building_collision_full_lod2_z0.stl`
- Solver: FluidX3D 3.7, local GitHub build
- Device: NVIDIA Tesla P100-PCIE-16GB
- Domain/grid: 306 x 306 x 64
- Grid spacing: dx = 4.0 m
- Directions: 0, 45, 90, 135, 180, 225, 270, 315 deg
- Steps per direction: 10000
- Wall time: 116.7 s total, about 14-15 s per direction
- Run script: `scripts/run_fluidx3d_full_lod2_8dir_coarse.ps1`
- Run summary: `F:\citylbm_fluidx3d_workspace\tum2twin_case\figures\fluidx3d_full_lod2_8dir_coarse4m_10k_run_summary.csv`

## Visual Audit Outputs

- 8-direction VR panel: `figures/fluidx3d_full_lod2_8dir_coarse4m_10k_vr_panel_z8m.png`
- Equal-weighted VR mean: `figures/fluidx3d_full_lod2_8dir_coarse4m_10k_equal_weighted_vr_z8m.png`
- Metrics CSV: `figures/fluidx3d_full_lod2_8dir_coarse4m_10k_metrics.csv`
- ParaView no-render pipeline state: `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_full_lod2_wd000_coarse4m_10k_pipeline_no_render.pvsm`

## Equal-Weighted 8-Direction Metrics

| Approx. height above lattice ground (m) | VR mean | VR P75 | VR P90 | VR P95 | VR max | Stagnation VR<0.2 | Acceleration VR>1.2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0.095 | 0.087 | 0.158 | 0.264 | 1.000 | 0.924 | 0.000 |
| 8 | 0.238 | 0.254 | 0.449 | 0.692 | 1.106 | 0.615 | 0.000 |
| 20 | 0.552 | 0.672 | 0.942 | 1.015 | 1.123 | 0.051 | 0.000 |
| 40 | 0.862 | 1.006 | 1.076 | 1.094 | 1.134 | 0.004 | 0.000 |

## Evidence Boundary

This matrix proves that the complete LoD2 collision workflow can be voxelized and run through FluidX3D for eight wind directions on the local GPU. It is not yet a final pedestrian wind comfort result because dx = 4 m does not resolve 1.5-2.0 m pedestrian height, no medium/fine grid sensitivity has been completed, and the setup still uses a stable smoke-test viscosity rather than a final Reynolds-scaled study design.

The current figures are therefore suitable for manual geometry/flow-direction audit and for selecting the next medium-grid case, not for final Lawson/NEN/AIJ comfort classification.
