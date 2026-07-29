# FluidX3D Full LoD2 Coarse Pilot Report

evidence_type: newly_run

## Run

- Geometry: `cfd_ready/building_collision_full_lod2_z0.stl`
- Source geometry: 27 TUM2TWIN LoD2 CityGML building files
- Solver: FluidX3D 3.7, local build from GitHub
- GPU: NVIDIA Tesla P100-PCIE-16GB
- Wind direction: WD000, 0 deg = +Y
- Grid: 306 x 306 x 64
- dx: 4.0 m
- Steps: 4000
- Run log: `F:\citylbm_fluidx3d_workspace\tum2twin_case\logs\run_full_lod2_wd000_coarse4m_4k.log`
- Final velocity VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_full_lod2_wd000_coarse4m_4k_u_finalu-000004000.vtk`
- Final flags VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_full_lod2_wd000_coarse4m_4k_flags_finalflags-000004000.vtk`

## Visual Outputs

- VR audit figure: `figures/fluidx3d_full_lod2_wd000_coarse4m_4k_vr_audit.png`
- Slice metrics: `figures/fluidx3d_full_lod2_wd000_coarse4m_4k_metrics.csv`
- Geometry footprint audit: `figures/full_lod2_collision_footprint_audit.png`

## Slice Metrics

| z approx (m) | VR mean | VR P90 | VR P95 | VR max | Stagnation VR<0.2 |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.097 | 0.151 | 0.269 | 1.000 | 0.929 |
| 8 | 0.246 | 0.447 | 0.699 | 1.129 | 0.612 |
| 20 | 0.576 | 0.943 | 1.020 | 1.123 | 0.039 |
| 40 | 0.898 | 1.085 | 1.113 | 1.126 | 0.002 |

## Interpretation Boundary

This is a full-district geometry and solver-chain audit, not a final pedestrian wind conclusion. The 4 m grid cannot resolve 1.5 m pedestrian-height flow, the run has not been time-averaged, and only one wind direction has been executed for this expanded geometry. The image is suitable for manual checking of geometry placement, voxelization, wake direction, and ParaView/post-processing readiness before running the 8-direction matrix.

## Next Runtime Estimate

Based on this run, a full LoD2 `dx=4 m` 8-direction pilot should take minutes rather than hours on the local Tesla P100, with VTK writing and post-processing likely dominating the wall time. A `dx=2 m` medium grid is estimated at about 47.8 million cells and 5.34-8.90 GB rough VRAM, so it is feasible to test on the 16 GB GPU but should be launched after the coarse images are manually accepted.
