# TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry audit

evidence_type: newly_run + preexisting_artifact

## Object checked

User-named object:

- `TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry`

Exact local file with this name was not found in the project folder, `D:\citylbm_tum2twin_heavy_store`, common user download folders, or selected F-drive experiment folders.

Official Zenodo record 14899378 was queried through the Zenodo API. The official record contains OBJ/MTL/JPG, LAZ, DSM, orthophoto, images, OPF, trajectory, and documentation files. It does not list a Rhino `.3dm` or `rhino_layered_geometry` file. Therefore, this name is treated as a derived Rhino-layered model name rather than an official raw dataset filename.

Official visual source already downloaded:

- `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.obj`
- `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.mtl`
- `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.jpg`

Existing local Rhino-layered file checked:

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\rhino\TUM2TWIN_wind_pilot_layers.3dm`

## Current 3dm layer audit

The checked 3dm contains 6 layers and 4 mesh objects:

| Layer | Object count | Bbox XY size | Bbox Z size | Interpretation |
|---|---:|---:|---:|---|
| `UAS_Mesh` | 1 | 409.06 m x 542.54 m | 46.89 m | Visual photogrammetry reference extent |
| `LoD3_Buildings` | 1 | 107.24 m x 71.26 m | 23.05 m | Too small for whole-block CFD |
| `CFD_Collision` | 1 | 105.48 m x 68.01 m | 23.05 m | Only a few-building collision layer |
| `Road_Ground` | 1 | 265.48 m x 228.01 m | 0.00 m | Simple ground/reference plane |
| `LoD2_Buildings` | 0 | n/a | n/a | Empty in checked 3dm |
| `Vegetation` | 0 | n/a | n/a | Empty in checked 3dm |

## Scope conclusion

The existing 3dm is useful for Rhino/GH layer management and visual reference, but it is not sufficient as a whole-block CFD collision model. Its `UAS_Mesh` visual layer covers the photogrammetry scene, while the actual building/collision layers cover only a small subset. This matches the user concern that the current simulation object contains only several buildings.

For whole-block FluidX3D simulation, the current CFD mainline should remain:

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\district_prism_collision_z0.stl`

This STL was reconstructed from the official TUM2TWIN LoD3 city OBJ:

- `D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected\obj\lod3_merged_city_model\TUM_CentralCampus.obj`

The LoD3 OBJ bbox is approximately 1541.22 m x 1375.07 m x 63.11 m. It is the appropriate whole-district geometry reference for the current FluidX3D application experiment. The direct OBJ surface was not used as the final collision boundary because voxelization produced sheet-like artifacts; the closed prism reconstruction is the current CFD-ready collision layer.

## Audit artifacts

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\tum2twin_rhino_layered_geometry_scope_audit.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_rhino_layered_geometry_scope_audit.png`

## Evidence boundary

- `newly_run`: local 3dm layer/object/bbox audit with `rhino3dm`; bbox comparison figure and CSV generated locally.
- `preexisting_artifact`: official Zenodo 14899378 file list and downloaded official OBJ/MTL/JPG; official TUM2TWIN GitLab LoD3 OBJ.
- `blocked`: exact user-named `.3dm` or archive cannot be checked unless the actual file is copied into the project/F-drive workspace or attached in the session.
