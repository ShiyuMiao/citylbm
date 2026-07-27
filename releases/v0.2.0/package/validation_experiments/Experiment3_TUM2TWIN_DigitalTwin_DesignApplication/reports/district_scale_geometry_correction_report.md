# District-Scale Geometry Correction Report

evidence_type: newly_run

## Reason For Correction

The previous `building_collision_full_lod2_z0.stl` uses all 27 available LoD2 CityGML building files, but its footprint still reads as a limited campus-core set of buildings. For the user's requested whole-block wind simulation, the collision geometry has been expanded using the official merged LoD3 city OBJ model.

## New District-Scale Candidate

- Source: `D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected\obj\lod3_merged_city_model\TUM_CentralCampus.obj`
- Selected material: `defaultMat`
- Selection rule: keep faces from selected material with triangle zmax >= 2.0 m
- Output STL: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\district_lod3_obj_collision_z0.stl`
- QA JSON: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\geometry_qa_district_lod3_obj.json`
- Audit figure: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\district_lod3_obj_collision_footprint_audit.png`

## QA

| Item | Value |
|---|---:|
| OBJ vertices | 776439 |
| OBJ total faces | 1664042 |
| Selected source faces | 1283256 |
| Exported triangles | 1283256 |
| Boundary edges | 65898 |
| Non-manifold edges | 169854 |
| Degenerate triangles | 2582 |
| Duplicate triangles | 6920 |
| BBox X (m) | 1541.221 |
| BBox Y (m) | 1375.073 |
| BBox Z (m) | 63.110 |

## Evidence Boundary

This is a district-scale collision candidate derived from the official merged LoD3 OBJ, not from the textured photogrammetry mesh. Because the OBJ is a merged visual/semantic city model rather than a guaranteed closed CFD solid, it must be voxelization-tested in FluidX3D before being used for final wind metrics. The previous LoD2 FluidX3D results are now treated as solver-pipeline evidence only, not as the final whole-block experiment.
