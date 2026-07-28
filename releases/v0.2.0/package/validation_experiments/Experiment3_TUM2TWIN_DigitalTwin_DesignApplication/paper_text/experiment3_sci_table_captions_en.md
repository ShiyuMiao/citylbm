# Experiment 3 SCI Table Captions

evidence_type: newly_run + preexisting_artifact + blocked

These captions are tied to archived source artifacts. They should be edited only for journal style, not for claim strength, unless new evidence is added.

## Table E3-1

Table E3-1. Paper-facing one-page key-result matrix for Experiment 3. The table consolidates S0 baseline, vertical recovery, Open-Meteo proxy sensitivity, S1/S2 design sensitivity, directional trade-off, morphology robustness, threshold screening, stage-transition analysis, morphology directional fingerprinting and GCRI into one evidence framework with evidence type, source artifact and paper-safe claim for each row.

- Asset: `figures/final_integrated_key_result_matrix.csv`
- Source data: `compiled from FluidX3D metrics, Open-Meteo proxy weights, morphology CSVs, design-sensitivity comparisons and GCRI`
- Evidence type: `newly_run + preexisting_artifact + blocked`
- Boundary: rows with blocked components must retain boundary wording

## Table E3-2

Table E3-2. Completion and paper-readiness audit matrix for Experiment 3. The table separates completed, screening-level, weakened and blocked modules, explicitly marking missing field data, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-Grasshopper end-to-end execution.

- Asset: `figures/experiment3_completion_audit_matrix.csv`
- Source data: `reports/experiment3_completion_audit_and_paper_readiness.md`
- Evidence type: `newly_run + blocked`
- Boundary: blocked rows must not be converted into completed results

## Table E3-3

Table E3-3. Geometry-to-CFD Readiness Index (GCRI) scoring table. The table compares photogrammetry visual mesh, core closed-prism collision geometry and district-prism collision geometry in watertightness, non-manifold error, semantic layer completeness, coordinate/unit consistency, STL export and voxelization success, showing that visual realism and CFD collision readiness are distinct model properties.

- Asset: `manifests/gcri_scoring_table.csv`
- Source data: `reports/geometry_to_cfd_readiness_index_results.md; reports/cfd_ready_geometry_qa.md`
- Evidence type: `newly_run`
- Boundary: GCRI is a paper-internal readiness score, not an external standard
