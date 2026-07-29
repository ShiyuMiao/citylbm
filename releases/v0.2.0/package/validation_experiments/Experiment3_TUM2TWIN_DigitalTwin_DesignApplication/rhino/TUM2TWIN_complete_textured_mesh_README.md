# TUM2TWIN complete textured mesh for Rhino

Use this official complete textured OBJ set for Rhino visual audit:

`D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.obj`

The OBJ, MTL, and JPG are in the same folder and reference each other correctly:

- OBJ: `TUM_Downtown_Photogrammetry_20241217_Mesh.obj`
- MTL: `TUM_Downtown_Photogrammetry_20241217_Mesh.mtl`
- JPG: `TUM_Downtown_Photogrammetry_20241217_Mesh.jpg`
- Offset: `TUM_Downtown_Photogrammetry_20241217_Mesh_offset.xyz`

Recommended Rhino workflow:

1. Open Rhino.
2. Import the OBJ above.
3. Keep the imported layer named `UAS_Mesh_VisualReference`.
4. Do not use this layer directly as `CFD_Collision`.
5. Load or reference `TUM2TWIN_wind_pilot_layers.3dm` for structured layers:
   - `UAS_Mesh`
   - `LoD2_Buildings`
   - `LoD3_Buildings`
   - `Vegetation`
   - `Road/Ground`
   - `CFD_Collision`

CFD collision geometry remains:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\building_collision_z0.stl`

Local audit image proving OBJ/UV/JPG consistency:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_textured_mesh_topdown_audit.png`

Evidence boundary:

- The OBJ+MTL+JPG textured model is for visualization and manual alignment.
- CityGML/CAD-derived STL is for FluidX3D rigid collision.
- Photogrammetry mesh is not assumed watertight or manifold.
