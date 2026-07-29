# TUM2TWIN Experiment Design

evidence_type: newly_run + preexisting_artifact + user_claim + blocked

## Research Position

This experiment is positioned after Case A/E benchmark or validation cases. It does not attempt to re-prove the intrinsic accuracy of FluidX3D/CityLBM. Instead, it tests how a real urban digital twin dataset can be converted into a wind-environment simulation workflow with clear evidence boundaries.

Core research question:

How can TUM2TWIN visual, semantic, CAD/OBJ/Rhino, and benchmark data be layered so that a real urban scene becomes CFD/LBM-ready without falsely treating photogrammetry or 3DGS-like visual meshes as closed rigid collision boundaries?

## Data Layering Strategy

| Data type | Use in this experiment | CFD collision role |
|---|---|---|
| UAS photogrammetry mesh / images | visual audit, screenshot matching, Rhino inspection, 3DGS/visual reference | not final collision |
| User-provided Rhino/photogrammetry package | confirms screenshot scene and provides a photogrammetry-shell counterexample | exploratory only |
| CityGML LoD2/LoD3 | semantic building evidence and geometry source | collision source candidate |
| TUM_CentralCampus OBJ | district-scale semantic geometry source | primary source for closed prism collision |
| CAD/OBJ/Rhino intermediate models | layer management and manual QA | intermediate |
| pc-fac benchmark | facade semantic reference | not CFD geometry |

## Simulation Geometry Levels

1. `building_collision_z0.stl`: early 4-building smoke-test geometry; retained only as pipeline evidence.
2. `building_collision_full_lod2_z0.stl`: expanded LoD2 geometry; retained as semantic conversion evidence.
3. `district_prism_collision_z0.stl`: whole-district closed-prism geometry reconstructed from `TUM_CentralCampus.obj`; used for coarse/medium district screening.
4. `core_photogrammetry_extent_prism_collision_z0.stl`: local closed semantic-prism geometry matching the user screenshot/photogrammetry extent; current main pedestrian-height simulation geometry.
5. `TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl`: user-provided photogrammetry STL; run only as an exploratory counterexample because it is not watertight and voxelizes as a fragmented visual shell.

## FluidX3D Simulation Hierarchy

| Case | Purpose | Grid / dx | Status |
|---|---|---|---|
| Full LoD2 pilot | solver pipeline proof | dx=4/2 m variants | newly_run, not main |
| District prism coarse | whole-district screening | dx=6 m, 8 directions | newly_run |
| District prism medium | stronger whole-district screening | dx=4 m, 8 directions | newly_run |
| User photogrammetry STL pilot | show why visual mesh is not collision geometry | dx=2 m, WD000, 2000 steps | newly_run counterexample |
| Core prism final snapshot | local pedestrian-height matrix | dx=2 m, 8 directions, 10000 steps | newly_run |
| Core prism time-sampled | current strongest result | dx=2 m, 8 directions, spin-up 6000 + samples at 8000/10000/12000 | newly_run |
| Open-Meteo weighted core result | wind-climate proxy weighting | time-mean results weighted by 2024 proxy wind rose | newly_run + preexisting_artifact |

## Current Main Evidence

Current strongest simulation result:

- `reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`
- `reports/wind_climate_weighted_core_prism_report.md`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`

At z≈2 m, the time-mean equal-weighted result gives:

- `VR_mean ≈ 0.076`
- `VR_P95 ≈ 0.241`
- `stagnation ratio VR<0.2 ≈ 0.934`

Open-Meteo 2024 proxy weighting gives:

- `VR_mean ≈ 0.077`
- `VR_P95 ≈ 0.246`
- `stagnation ratio VR<0.2 ≈ 0.931`

## Evidence Boundary

Supported:

- data download and source verification;
- Rhino/OBJ/STL geometry audit;
- digital-twin-to-CFD geometry workflow;
- FluidX3D execution on local GPU;
- local pedestrian-height VR and stagnation screening;
- Open-Meteo wind-climate proxy weighting.

Not supported yet:

- formal Lawson/NEN/AIJ annual exceedance comfort classes;
- field or wind-tunnel validation;
- pollutant dispersion;
- final Reynolds-scaled prediction accuracy;
- direct use of photogrammetry/3DGS mesh as final collision geometry.
