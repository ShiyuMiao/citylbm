# CFD-Ready Geometry QA

evidence_type: newly_run

## Current Geometry Hierarchy

| Geometry | File | Role | Current Status |
|---|---|---|---|
| Early 4-building collision | `cfd_ready/building_collision_z0.stl` | smoke-test only | deprecated for main claims |
| Expanded full LoD2 collision | `cfd_ready/building_collision_full_lod2_z0.stl` | semantic conversion evidence | not main |
| Direct district LoD3 OBJ candidate | `cfd_ready/district_lod3_obj_collision_z0.stl` | failed/limited candidate | voxelization showed sheet-like artifacts |
| Whole-district closed prism | `cfd_ready/district_prism_collision_z0.stl` | district screening | accepted for whole-district application screening |
| Core photogrammetry-extent closed prism | `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl` | local pedestrian-height simulation | current main local CFD geometry |
| User photogrammetry STL | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` | visual shell counterexample | not accepted as final collision |

## Whole-District Prism QA

- source: official `TUM_CentralCampus.obj`
- method: high-surface point extraction, footprint rasterization, hole filling, closed heightfield prism extrusion
- bbox: approximately `1540 x 1375 x 58 m`
- triangles: `135,122`
- footprint cells: `21,967`
- components: `217`
- QA file: `manifests/geometry_qa_district_prism.json`
- audit figure: `figures/district_prism_collision_audit.png`

## Core Local Prism QA

- source: official `TUM_CentralCampus.obj`
- crop: user photogrammetry/Rhino visual extent, approximately `x=-190..235 m`, `y=-215..345 m`
- bbox: approximately `420 x 555 x 32.43 m`
- triangles: `15,964`
- footprint cells: `2,365`
- components: `46`
- QA file: `manifests/geometry_qa_core_photogrammetry_extent_prism.json`
- audit figure: `figures/core_photogrammetry_extent_prism_collision_audit.png`
- current main local STL: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`

## User Photogrammetry STL QA

The user-provided full-resolution photogrammetry STL has:

- triangles: `999,999`
- bbox: approximately `409.282 x 542.659 x 47.147 m`
- boundary edges: `2,245`
- non-manifold edges >2: `0`
- degenerate faces: `0`
- watertight by edge count: `false`

FluidX3D exploratory voxelization confirmed that the geometry behaves as a fragmented visual surface shell rather than a coherent closed building collision body. It is therefore useful as a geometry-readiness counterexample, not as final collision geometry.

## QA Decision

Accepted main geometries:

- local pedestrian-height simulation: `core_photogrammetry_extent_prism_collision_z0.stl`
- whole-district application screening: `district_prism_collision_z0.stl`

Rejected for final collision:

- raw/textured photogrammetry mesh;
- user-provided photogrammetry STL;
- direct district LoD3 OBJ surface candidate without prism reconstruction.
