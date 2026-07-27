# TUM2TWIN manual model check

Check date: 2026-07-26

## User-provided screenshot

The screenshot shows a textured, photogrammetry-style TUM downtown campus block. It contains realistic roofs, roads, facade appearance, courtyard surfaces, and irregular torn edges typical of UAS/image-based reconstruction.

Interpretation: this is the UAS photogrammetry / textured mesh layer, suitable for visual reference, Rhino scene context, and paper figures. It should not be used directly as the final FluidX3D collision boundary because it is not guaranteed to be watertight, semantically separated, or cleanly manifold.

## Local file check

Local OBJ:

`D:\citylbm_tum2twin_heavy_store\raw\zenodo_14548134\TUM_Downtown_Photogrammetry_20241217_Mesh.obj`

Local offset:

`D:\citylbm_tum2twin_heavy_store\raw\zenodo_14548134\TUM_Downtown_Photogrammetry_20241217_Mesh_offset.xyz`

Offset values:

`690956.000 5336042.000 604.000`

OBJ statistics:

- vertices: `951285`
- texture coordinates: `951285`
- normals: `0`
- faces: `999999`
- local bbox min: `[-182.366, -205.826, -49.2653]`
- local bbox max: `[226.916, 336.833, -2.11812]`
- local size: `409.282 m x 542.659 m x 47.14718 m`

## Texture issue

The OBJ header references:

`mtllib TUM2TWIN-all-mesh.mtl`

The available local MTL file contains:

`map_Kd TUM2TWIN-all-mesh.jpg`

The earlier local Zenodo 14548134 copy did not contain the texture atlas. A second official Zenodo record was verified and downloaded:

`D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh`

This folder contains a mutually consistent OBJ/MTL/JPG set:

- `TUM_Downtown_Photogrammetry_20241217_Mesh.obj`
- `TUM_Downtown_Photogrammetry_20241217_Mesh.mtl`
- `TUM_Downtown_Photogrammetry_20241217_Mesh.jpg`

OBJ header:

`mtllib TUM_Downtown_Photogrammetry_20241217_Mesh.mtl`

MTL texture reference:

`map_Kd TUM_Downtown_Photogrammetry_20241217_Mesh.jpg`

A local top-down audit rendering was generated from OBJ UV coordinates and the JPG texture:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_textured_mesh_topdown_audit.png`

## Use in experiment

- Use the textured photogrammetry mesh as `UAS_Mesh` / visual reference layer.
- Use CityGML LoD2/LoD3 or CAD-derived solids for `CFD_Collision`.
- Use the manual textured model to visually audit whether the selected CFD collision buildings align with the real campus block.
- Do not claim that the photogrammetry mesh is a closed rigid FluidX3D wall boundary.
