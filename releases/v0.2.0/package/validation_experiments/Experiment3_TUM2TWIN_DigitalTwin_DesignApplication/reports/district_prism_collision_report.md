# District Prism Collision Report

evidence_type: newly_run

## Purpose

The direct district LoD3 OBJ surface was too sheet-like for robust FluidX3D collision use. This report records a corrected whole-block collision candidate reconstructed as closed footprint/height prisms from the official merged LoD3 OBJ high surfaces.

## Outputs

- Collision STL: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\district_prism_collision_z0.stl`
- QA JSON: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\geometry_qa_district_prism.json`
- Audit figure: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\district_prism_collision_audit.png`
- Grid estimate: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\FluidX3D_case_template\grid_memory_estimate_district_prism.csv`

## QA Summary

| Item | Value |
|---|---:|
| Selected high points | 3598730 |
| Raw occupied raster cells | 13008 |
| Final footprint cells | 21967 |
| Components | 217 |
| Exported triangles | 135122 |
| Height min / max / mean (m) | 6.00 / 58.00 / 20.86 |
| BBox X / Y / Z (m) | 1540.0 / 1375.0 / 58.0 |

## Evidence Boundary

This is a whole-block simplified collision model intended for LBM pilot simulation. It is more CFD-ready than the raw merged OBJ because it is closed and avoids sheet-like facade triangulation, but it is a generalized prism model and should be described as an OBJ-derived block reconstruction rather than exact LoD3 facade geometry.
