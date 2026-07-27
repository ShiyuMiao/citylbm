# FluidX3D Core Prism 8-Direction dx=2 m Report

evidence_type: newly_run

## Purpose

This run provides a local high-resolution wind-environment pilot for the TUM Downtown core area matching the user-provided photogrammetry/Rhino visual extent. Unlike the user-provided photogrammetry STL pilot, this case uses a semantic closed prism collision geometry reconstructed from the official TUM2TWIN LoD3 OBJ high surfaces.

This is the strongest current evidence layer for pedestrian-height statistics in the experiment package.

## Geometry

- Collision STL: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- Geometry source: official `TUM_CentralCampus.obj`
- Crop source XY: `x=-190..235 m`, `y=-215..345 m`
- Geometry bbox: approximately `420 x 555 x 32.43 m`
- Triangles: `15,964`
- Reconstruction method: high-surface footprint extraction and closed heightfield prism extrusion
- QA file: `manifests/geometry_qa_core_photogrammetry_extent_prism.json`
- Audit figure: `figures/core_photogrammetry_extent_prism_collision_audit.png`

## FluidX3D Run

- Solver: FluidX3D local build
- Device: NVIDIA Tesla P100-PCIE-16GB
- Wind directions: `0, 45, 90, 135, 180, 225, 270, 315 deg`
- Grid: `320 x 390 x 60`
- dx: `2.0 m`
- Steps per direction: `10000`
- Runtime per direction: about `17-19 s`
- Total runtime: about `144 s`
- Run script: `scripts/run_fluidx3d_core_prism_8dir_dx2m.ps1`
- Postprocess script: `scripts/postprocess_core_prism_8dir_dx2m.py`

## Visual Outputs

- 8-direction z~2 m panel: `figures/fluidx3d_core_prism_8dir_dx2m_10k_vr_panel_z2m.png`
- Equal-weighted z~2 m map: `figures/fluidx3d_core_prism_8dir_dx2m_10k_equal_weighted_vr_z2m.png`
- Metrics CSV: `figures/fluidx3d_core_prism_8dir_dx2m_10k_metrics.csv`

## Equal-Weighted Metrics

| Approx. height (m) | VR mean | VR P75 | VR P90 | VR P95 | VR max | Stagnation VR<0.2 | VR>0.6 | VR>1.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.076 | 0.080 | 0.155 | 0.241 | 1.000 | 0.934 | 0.013 | 0.000 |
| 4 | 0.187 | 0.237 | 0.412 | 0.635 | 1.048 | 0.666 | 0.053 | 0.000 |
| 10 | 0.404 | 0.625 | 0.831 | 0.915 | 1.041 | 0.314 | 0.276 | 0.004 |
| 20 | 0.602 | 0.936 | 1.002 | 1.021 | 1.068 | 0.245 | 0.594 | 0.104 |
| 40 | 1.048 | 1.122 | 1.139 | 1.147 | 1.182 | 0.000 | 1.000 | 0.733 |

## Interpretation Boundary

The dx=2 m local grid resolves a 2 m pedestrian-height layer and is suitable for preliminary wind-speed-ratio and stagnation-area statistics. However, the current setup still uses a stable pilot viscosity and short-duration final snapshots rather than statistically converged time averages. Therefore:

- supported: geometry-to-CFD workflow, local pedestrian-height VR screening, stagnation ratio, direction matrix comparison;
- not yet supported: final Lawson/NEN/AIJ comfort classification, safety exceedance probabilities, measured validation, or final Reynolds-scaled prediction accuracy.

This local closed-prism result should be used as the current main pedestrian-height simulation evidence, while the photogrammetry STL pilot should be used only as a geometry-readiness counterexample.
