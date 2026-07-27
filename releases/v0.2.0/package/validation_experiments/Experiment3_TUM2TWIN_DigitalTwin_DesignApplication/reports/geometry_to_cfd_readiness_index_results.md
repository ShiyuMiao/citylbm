# Geometry-to-CFD Readiness Index Results

evidence_type: newly_run + preexisting_artifact

The GCRI table converts the qualitative geometry QA into an explicit 0-1 readiness score. The scoring is a paper-internal, reproducible screening index rather than an external standard.

Machine-readable table: `manifests/gcri_scoring_table.csv`.

## Formula

`GCRI = 0.20 W + 0.15 M + 0.15 S + 0.15 C + 0.15 E + 0.20 V`

where `W` is watertightness, `M` manifoldness, `S` semantic completeness, `C` coordinate/unit consistency, `E` export success, and `V` voxelization success.

## Current Scores

| Geometry | Role | GCRI | Main interpretation |
|---|---:|---:|---|
| User photogrammetry full-resolution STL | visual reference / counterexample | `0.455` | useful for visual scope review, not reliable as final collision |
| Core photogrammetry-extent prism collision | accepted core collision | `0.925` | strongest local CFD-ready geometry in the archive |
| Whole-district prism collision | accepted district collision | `0.918` | suitable for district-scale coarse/medium screening |
| LoD3 direct OBJ collision candidate | semantic detail reference / repair candidate | `0.528` | semantically valuable but needs closure/repair before collision use |
| LoD2/LoD3-derived closed prism target | recommended future production collision | `0.955` | target-state criterion, not a new solver result |

## Paper Claim Boundary

The score supports the claim that a visual digital-twin mesh and a CFD collision boundary are different artifacts. The photogrammetry mesh preserves appearance and study-object extent, while the prism/semantic collision geometries provide the closed, voxelizable solids needed by FluidX3D. The GCRI does not prove wind-result accuracy; it only measures readiness of a digital-twin geometry for CFD/LBM ingestion.
