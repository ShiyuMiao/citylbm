# FluidX3D Core Prism Time-Sampled 8-Direction dx=2 m Report

evidence_type: newly_run

## Purpose

This report upgrades the local core-prism pedestrian-height result from a single final snapshot to a time-sampled pilot. For each of eight wind directions, FluidX3D was run with a spin-up period followed by three velocity samples. The post-processing first averages the three samples for each wind direction and then computes an equal-weighted 8-direction map.

This is the current strongest wind-environment simulation evidence in the experiment package.

## Geometry

- Collision geometry: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- Source: official TUM2TWIN `TUM_CentralCampus.obj`, cropped to the user-provided photogrammetry/Rhino visual extent
- Collision type: semantic closed heightfield prism, not the photogrammetry shell
- Bbox: approximately `420 x 555 x 32.43 m`
- QA: `manifests/geometry_qa_core_photogrammetry_extent_prism.json`

## FluidX3D Sampling Setup

- Solver: FluidX3D local build, modified to support environment-controlled time sampling
- GPU: NVIDIA Tesla P100-PCIE-16GB
- Grid: `320 x 390 x 60`
- dx: `2.0 m`
- Wind directions: `0, 45, 90, 135, 180, 225, 270, 315 deg`
- Spin-up: `6000 steps`
- Samples: `3`
- Sample steps: `8000, 10000, 12000`
- Sample interval: `2000 steps`
- Runtime per direction: about `21-25 s`
- Total runtime: about `180 s`
- Run script: `scripts/run_fluidx3d_core_prism_timesampled_8dir_dx2m.ps1`
- Postprocess script: `scripts/postprocess_core_prism_timesampled_8dir_dx2m.py`

## Visual Outputs

- Time-mean 8-direction panel at z~2 m: `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`
- Time-mean + equal-weighted map at z~2 m: `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`
- Full metrics CSV: `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`
- Run summary: `F:\citylbm_fluidx3d_workspace\tum2twin_case\figures\fluidx3d_core_prism_timesampled_8dir_dx2m_run_summary.csv`

## Time-Mean Equal-Weighted Metrics

| Approx. height (m) | VR mean | VR P75 | VR P90 | VR P95 | VR max | Stagnation VR<0.2 | VR>0.6 | VR>1.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.076 | 0.080 | 0.155 | 0.241 | 1.000 | 0.934 | 0.013 | 0.000 |
| 4 | 0.187 | 0.237 | 0.412 | 0.635 | 1.048 | 0.665 | 0.053 | 0.000 |
| 10 | 0.404 | 0.625 | 0.831 | 0.915 | 1.041 | 0.314 | 0.276 | 0.004 |
| 20 | 0.602 | 0.936 | 1.002 | 1.021 | 1.068 | 0.245 | 0.594 | 0.104 |
| 40 | 1.049 | 1.123 | 1.139 | 1.147 | 1.182 | 0.000 | 1.000 | 0.734 |

## Interpretation

The time-sampled metrics are nearly identical to the previous final-snapshot dx=2 m metrics, which indicates that the current short sampling window is internally stable. At z~2 m, the equal-weighted VR remains low across most open cells, with a stagnation ratio of approximately 0.934 for `VR < 0.2`.

This supports a preliminary conclusion that the dense core subdomain is dominated by low pedestrian-height ventilation under the present pilot boundary conditions.

## Evidence Boundary

Supported:

- local pedestrian-height VR screening at z~2 m;
- stagnation-area statistics;
- comparison of time-mean values across 8 wind directions;
- demonstration that semantic closed collision geometry supports a more coherent CFD workflow than direct photogrammetry-shell voxelization.

Not yet supported:

- final Lawson/NEN/AIJ exceedance-probability comfort/safety classification;
- validation against field or wind-tunnel measurements;
- final Reynolds-scaled prediction accuracy;
- pollutant dispersion results.

The next rigor step is to connect wind-climate probabilities and, if comfort/safety classification is required, run a longer statistically averaged case or a finer local grid.
