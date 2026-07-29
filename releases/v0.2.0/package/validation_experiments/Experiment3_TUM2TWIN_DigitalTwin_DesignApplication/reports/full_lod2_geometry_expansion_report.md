# Full LoD2 Geometry Expansion Report

evidence_type: newly_run

## Purpose

The earlier FluidX3D smoke test used a small four-building LoD2 collision mesh. This expanded geometry uses all locally downloaded TUM2TWIN LoD2 building GML files so the next experiment can move from pipeline validation toward a real-district application case.

## Outputs

- Full building collision STL: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\building_collision_full_lod2_z0.stl`
- Full ground/domain STL: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\ground_domain_full_lod2_z0.stl`
- QA JSON: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\geometry_qa_full_lod2.json`
- Grid estimate CSV: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\FluidX3D_case_template\grid_memory_estimate_full_lod2.csv`
- Footprint audit figure: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\full_lod2_collision_footprint_audit.png`

## Geometry QA

| Item | Value |
|---|---:|
| Source GML files | 27 |
| Parsed polygon rings | 905 |
| CityGML building ids | 27 |
| Triangles | 3833 |
| Watertight | False |
| Boundary edges | 19 |
| Non-manifold edges | 6 |
| Degenerate triangles | 11 |
| Duplicate triangles | 5 |
| Hmax (m) | 42.390 |

## BBox

- Local min: `[0.0, 0.0, 0.0]`
- Local max: `[273.62899999995716, 373.50499999988824, 42.38999999999993]`
- Source origin EPSG:25832/z: `[690815.103, 5335874.965, 509.79]`

## Evidence Boundary

This mesh is CFD-ready in the sense of semantic source selection, unit consistency, local z0 conversion, STL export, and QA recording. It is not yet a final SCI wind result until FluidX3D voxelization, grid/time sensitivity, and ParaView post-processing are completed on this expanded geometry.
