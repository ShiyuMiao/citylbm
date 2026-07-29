# FluidX3D User Photogrammetry STL Exploratory Pilot

evidence_type: newly_run

## Purpose

This pilot tests the user-provided `TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` in FluidX3D. It is intentionally treated as an exploratory geometry-to-solver test, not as the final wind-environment result. The purpose is to provide direct experimental evidence for the paper argument that a photogrammetry/3DGS-like visual mesh can be opened and voxelized, but should not be accepted as a rigorous closed collision boundary without repair and semantic supplementation.

## Input Geometry

- Source archive: `C:\Users\miaoshiyu\Downloads\converted.rar`
- Extracted STL: `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl`
- Copied solver STL: `F:\citylbm_fluidx3d_workspace\FluidX3D\stl\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl`
- STL triangles: 999,999
- Bbox size: approximately `409.282 m x 542.659 m x 47.147 m`
- Watertight QA: false, with 2,245 boundary edges

## FluidX3D Setup

- Solver: FluidX3D local build
- GPU: NVIDIA Tesla P100-PCIE-16GB
- Case label: `user_photo_wd000_dx2m_2k`
- Wind direction: 0 deg
- Grid: `360 x 430 x 80`
- dx: `2.0 m`
- Steps: `2000`
- Runtime: about `11.94 s`
- Script: `scripts/run_fluidx3d_user_photogrammetry_pilot.ps1`
- Postprocess script: `scripts/postprocess_user_photogrammetry_pilot.py`

## Output Artifacts

- Audit figure: `figures/fluidx3d_user_photo_wd000_dx2m_2k_voxel_vr_audit.png`
- Metrics CSV: `figures/fluidx3d_user_photo_wd000_dx2m_2k_metrics.csv`
- Solver output folder: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\`

## Pilot Metrics

| Approx. height (m) | Solid ratio | VR mean | VR P90 | VR P95 | VR max | Stagnation VR<0.2 |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.0000 | 0.085 | 0.130 | 0.200 | 1.000 | 0.950 |
| 4 | 0.0010 | 0.219 | 0.366 | 0.563 | 1.125 | 0.325 |
| 10 | 0.0971 | 0.560 | 0.887 | 1.001 | 1.119 | 0.147 |
| 20 | 0.0896 | 0.830 | 1.069 | 1.098 | 1.122 | 0.125 |
| 40 | 0.0001 | 1.024 | 1.124 | 1.136 | 1.215 | 0.004 |

## Interpretation

The pilot confirms that the user-provided full-resolution photogrammetry STL can be passed to FluidX3D and produce VTK outputs. However, the voxelized solid masks show that the geometry behaves like a visual surface shell rather than a closed rigid building volume:

- at 2-4 m height, almost no solid building mask appears;
- at 10-20 m height, the solid mask appears as fragmented roof/facade strips;
- at 40 m height, almost no solid mask remains.

Therefore, this pilot supports the evidence boundary used in the experiment: the photogrammetry/Rhino visual mesh is suitable for scene inspection and visual reference, but it should not be used as the final collision geometry for rigorous pedestrian wind-environment claims.

## Decision

Accepted use:

- visual reference;
- Rhino manual model audit;
- evidence for geometry-to-CFD readiness limitations;
- exploratory FluidX3D voxelization illustration.

Rejected use without further repair:

- final watertight CFD collision boundary;
- formal Lawson/NEN/AIJ pedestrian comfort result;
- measured or validated wind prediction claim.

The rigorous whole-district mainline remains:

- `cfd_ready/district_prism_collision_z0.stl`
