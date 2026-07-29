# Model-Result Object Consistency Audit

evidence_type: newly_run

## Audit Question

Check whether the FluidX3D simulation results analyze the same object as the user-provided model screenshot:

- screenshot / user Rhino visual model: TUM Downtown photogrammetry block;
- main simulation result: `fluidx3d_core_prism_timesampled_8dir_dx2m_*`;
- CFD-ready geometry: `core_photogrammetry_extent_prism_collision_z0.stl`.

## Verdict

The main FluidX3D result is consistent with the screenshot at the study-area level, but not identical at the mesh-representation level.

The simulation does **not** use the raw textured photogrammetry mesh as the final collision boundary. Instead, it uses a closed semantic-prism collision geometry reconstructed from the official TUM2TWIN LoD3 OBJ within the same photogrammetry/Rhino visual extent. This is the correct interpretation for the paper: the screenshot/model and simulation refer to the same TUM Downtown block, while the computational boundary is a CFD-ready semantic reconstruction rather than the visual shell mesh.

Claim readiness: `paper_ready`, with this wording constraint:

> The analysis object is the TUM Downtown photogrammetry/Rhino visual extent. The FluidX3D collision boundary is a LoD3-derived closed prism approximation of that same extent, not the raw photogrammetry mesh.

## Evidence Table

| Layer | Evidence type | Path / source | Scope / bbox | Consistency judgement |
|---|---|---|---|---|
| User screenshot | user_claim + visual input | `C:\Users\MIAOSH~1\AppData\Local\Temp\codex-clipboard-343f614c-f3f8-49ce-b283-ddbbcf6ca52e.png` | Oblique view of TUM Downtown photogrammetry block | Reference image for manual object identity |
| User Rhino visual model | newly_run | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm` | bbox size about `409.1 x 542.5 x 46.9 m` | Matches screenshot scale and visual object, but is one photogrammetry mesh layer |
| User photogrammetry STL | newly_run | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` | bbox size about `409.3 x 542.7 x 47.1 m`; 999,999 triangles | Same visual extent, but not accepted as final collision because it is not watertight |
| Core CFD-ready collision geometry | newly_run | `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\core_photogrammetry_extent_prism_collision_z0.stl` | bbox size about `420.0 x 555.0 x 32.4 m`; 15,964 triangles; 46 components | Same study extent after semantic-prism reconstruction; main FluidX3D collision boundary |
| Main FluidX3D result | newly_run | `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png` | grid `320 x 390 x 60`, dx `2 m`, z about `2 m` | Uses the core CFD-ready collision geometry, therefore consistent with the intended study area |
| Whole-district prism result | newly_run | `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\cfd_ready\district_prism_collision_z0.stl` | bbox size about `1540 x 1375 x 58 m` | Broader district screening, not the exact screenshot-only core result |
| Earlier small Rhino collision layer | newly_run | `manifests\tum2twin_rhino_layered_geometry_scope_audit.csv` | about `105 x 68 m` | Too small; should not be described as the current main analysis object |

## Detailed Consistency Check

### 1. Plan-Extent Consistency

The user visual model audit reports a visual photogrammetry extent of about `409 x 543 m`. The current core CFD-ready geometry reports about `420 x 555 m`. This difference is expected because the CFD geometry is rasterized and padded from the LoD3 OBJ crop. Therefore, the main simulation object is not limited to a few isolated buildings; it covers the same downtown block scale as the screenshot.

### 2. Geometry-Representation Consistency

The screenshot and user Rhino file show a textured photogrammetry mesh. The main FluidX3D result uses a LoD3-derived closed semantic-prism model. These are intentionally different representations:

- photogrammetry mesh: visual reference, 3DGS/appearance reference, manual object confirmation;
- semantic-prism STL: closed collision boundary for FluidX3D voxelization.

This representation change should be explicitly stated in the manuscript to avoid the false claim that the visual mesh was directly used as a rigorous collision boundary.

### 3. Simulation-Figure Consistency

The white solid mask in `fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png` corresponds to the footprint in `core_photogrammetry_extent_prism_collision_audit.png`. The result figure is a horizontal z~2 m velocity-ratio slice with surrounding inflow/outflow buffer. Therefore, it will not visually resemble the oblique Rhino screenshot with roof textures. This is not a mismatch; it is a projection and data-layer difference.

### 4. Results That Should Not Be Used As Main Object Evidence

- `fluidx3d_user_photo_wd000_dx2m_2k_voxel_vr_audit.png` is a counterexample showing poor voxelization of the photogrammetry STL. It should not be used as the final wind-environment result.
- Whole-district coarse/medium prism results are useful for context and scalability, but they cover a broader district than the screenshot core.
- Old four-building or small Rhino-layer tests are superseded by the current core-prism and district-prism results.

## Protocol Risks

| Risk | Severity | Treatment |
|---|---|---|
| Raw photogrammetry mesh may be mistaken for final collision geometry | High | State explicitly that FluidX3D uses the LoD3-derived closed prism boundary |
| Oblique screenshot cannot be visually overlaid directly with z=2 m CFD slice | Medium | Compare bbox, source extent, and footprint audit rather than texture appearance |
| Semantic-prism geometry simplifies roofs/facades and omits fine facade roughness | Medium | Claim workflow-level application validation and preliminary wind screening, not final field-validated prediction |
| Whole-district and core results may be confused | Medium | Use core-prism figures for screenshot-matched analysis; use district-prism figures only for broader screening |
