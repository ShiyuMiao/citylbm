# User Converted Rhino Layered Package Audit

evidence_type: newly_run + user_claim

## Package Location

User-provided archive found at:

- `C:\Users\miaoshiyu\Downloads\converted.rar`

Because the C drive has less than 3 GB free space, the archive was extracted to D drive:

- `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\`

Archive metadata:

| Item | Value |
|---|---|
| Archive size | 84,731,151 bytes |
| Archive type | RAR5 |
| Encrypted | No |
| Total extracted size | 144,509,238 bytes |
| SHA256 | `F60472D879609AFB5D5A0FE93F5DE00E7DEB1B363A2D5DCFF098A4AB6992A063` |
| MD5 | `08E87B475DCDC902011D3066965A9BEC` |

## Extracted Files

| File | Size | Role |
|---|---:|---|
| `TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm` | 44,509,170 bytes | Rhino-readable visual photogrammetry mesh |
| `TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` | 50,000,034 bytes | z0-shifted full-resolution photogrammetry STL |
| `TUM_Downtown_Photogrammetry_20241217_visual_local_fullres.stl` | 50,000,034 bytes | original-local-Z visual full-resolution photogrammetry STL |

## Rhino 3dm Audit

The 3dm was read locally with `rhino3dm`.

| Field | Value |
|---|---|
| Model unit metadata | `UnitSystem.Millimeters` |
| Layer count | 1 |
| Object count | 1 |
| Layer name | `TUM2TWIN::UAS_Photogrammetry_Mesh::material` |
| Object name | `TUM_Downtown_Photogrammetry_20241217_fullres_mesh` |
| Mesh faces | 999,999 |
| Bbox min | `[-182.366, -205.826, -49.265]` |
| Bbox size | `[409.282, 542.659, 47.147]` |

Important interpretation: despite the filename containing `rhino_layered_geometry`, this checked file is not a multi-layer Rhino/GH modeling file. It contains one visual photogrammetry mesh layer. It is useful for manual Rhino visual checking and scene selection, but it does not contain separate LoD2, LoD3, vegetation, road/ground, or CFD collision layers.

## STL QA

Both STL files contain the same photogrammetry topology.

| File | Triangles | Unique vertices, rounded 1e-5 | Boundary edges | Non-manifold edges >2 | Degenerate faces | Watertight by edge count |
|---|---:|---:|---:|---:|---:|---|
| `TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` | 999,999 | 494,113 | 2,245 | 0 | 0 | false |
| `TUM_Downtown_Photogrammetry_20241217_visual_local_fullres.stl` | 999,999 | 494,113 | 2,245 | 0 | 0 | false |

The `fluidx3d_z0_fullres.stl` file is shifted so that the photogrammetry Z range starts at 0. Its bbox size is approximately:

- `409.282 m x 542.659 m x 47.147 m`

The `visual_local_fullres.stl` keeps the original local Z range:

- min Z approximately `-49.265 m`
- max Z approximately `-2.118 m`

## CFD Use Decision

This package is valuable and should be retained as the user-confirmed visual model matching the Rhino screenshot.

However, it should not replace the current CFD collision mainline for rigorous paper claims, because:

1. It is a photogrammetry mesh, not a semantic LoD2/LoD3 building model.
2. It is not watertight by edge-count QA.
3. It has no separated building, vegetation, road, ground, and collision layers in the checked 3dm.
4. Its unit metadata is millimeters while the coordinate magnitudes and original TUM2TWIN OBJ/STL pipeline are treated as meters, so unit interpretation must be stated explicitly before any solver use.

Recommended use:

- `visual_reference`: yes
- `Rhino manual scene audit`: yes
- `FluidX3D exploratory voxelization test`: possible, with evidence boundary
- `final rigid building collision boundary`: no, unless repaired/segmented and re-QA confirms watertight collision geometry

The current rigorous whole-district CFD mainline remains:

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\district_prism_collision_z0.stl`

The user-provided photogrammetry package should be used to support the paper's core argument that photogrammetry/3DGS-like visual meshes require conversion or semantic supplementation before becoming reliable CFD collision boundaries.
