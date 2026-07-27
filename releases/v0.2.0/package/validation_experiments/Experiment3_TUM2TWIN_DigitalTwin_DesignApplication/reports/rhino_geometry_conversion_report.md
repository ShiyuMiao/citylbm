# Rhino Geometry Conversion Report

evidence_type: newly_run + user_claim

## Rhino / Visual Files

| File | Role | Status |
|---|---|---|
| `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.obj` | exact textured photogrammetry browsing with OBJ/MTL/JPG | official visual baseline |
| `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm` | user-provided Rhino-readable photogrammetry mesh matching screenshot | audited; 1 layer, 1 mesh |
| `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\rhino\TUM2TWIN_Downtown_district_CFD_layered_geometry.3dm` | generated Rhino management file with whole-district CFD collision layer | audited; 5 layers |
| `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\rhino\TUM2TWIN_wind_pilot_layers.3dm` | early local pilot 3dm | retained only as early pipeline evidence |

## User-Provided Rhino Package Audit

The user-provided `TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm` was extracted from `converted.rar` and read locally with `rhino3dm`.

- model unit metadata: `UnitSystem.Millimeters`
- layer count: `1`
- object count: `1`
- layer: `TUM2TWIN::UAS_Photogrammetry_Mesh::material`
- mesh faces: `999,999`
- bbox size: approximately `409.282 x 542.659 x 47.147`

Despite the filename containing `rhino_layered_geometry`, the checked file is not a multi-layer semantic CFD modeling file. It is a Rhino-readable photogrammetry visual mesh.

## Generated Rhino Management File

The generated file `TUM2TWIN_Downtown_district_CFD_layered_geometry.3dm` contains:

- `UAS_Mesh_visual_reference_decimated`
- `LoD3_District_reference`
- `Road_Ground`
- `CFD_Collision_whole_district`
- `Notes`

The `CFD_Collision_whole_district` layer has bbox approximately `1540 x 1375 x 58 m`, matching the district-scale closed prism geometry.

## Use Decision

- For exact textured visual browsing: use OBJ + MTL + JPG.
- For Rhino manual inspection of the screenshot scene: use the user-provided `.3dm`.
- For Rhino/GH collision-geometry management: use the generated district `.3dm`.
- For FluidX3D final collision: use `core_photogrammetry_extent_prism_collision_z0.stl` for local pedestrian-height results and `district_prism_collision_z0.stl` for whole-district screening.
- Do not use the photogrammetry `.3dm` or photogrammetry STL as final collision geometry without repair and QA.
