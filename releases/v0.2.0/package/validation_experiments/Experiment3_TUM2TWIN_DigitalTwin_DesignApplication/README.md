# Experiment 3: TUM2TWIN Digital-Twin Design Application

evidence_type: newly_run + preexisting_artifact

This folder archives the third experiment supporting the CityLBM urban wind-environment paper.

## Paper Logic

- Experiment 1: AIJ Case A, benchmark/validation support.
- Experiment 2: AIJ Case E, benchmark/validation support.
- Experiment 3: TUM2TWIN real urban digital-twin design-application experiment.

The first two AIJ cases support the solver/workflow validation layer. This experiment does not re-claim solver accuracy; it tests whether real digital-twin city data can be transformed into CFD-ready geometry, simulated with FluidX3D, inspected in ParaView/Rhino, and interpreted as an architectural wind screening and morphology-explanation application.

Current archive positioning: **FluidX3D-native simulation with a CityLBM-compatible geometry package**. The CityLBM/Grasshopper folder is retained as an interoperability template only and is not a completed end-to-end CityLBM plugin run.

## Research Object

The experiment uses the TUM2TWIN TUM Downtown / central campus digital-twin data. The user-provided Rhino/photogrammetry visual model is treated as the visual reference for the real block extent, while semantic/CAD-derived closed geometry is used for CFD collision boundaries.

Core distinction:

- UAS/photogrammetry mesh: visual reference and model-scope audit.
- CityGML/LoD3/CAD-derived geometry: preferred source for CFD collision preparation.
- User photogrammetry STL: tested as an exploratory counterexample; not accepted as the final collision boundary.
- FluidX3D VTK results: used for pedestrian-height wind-response screening.
- ParaView: used for VTK review-state preparation and manual visualization.

## Folder Contents

- `reports/`: experiment design, geometry QA, FluidX3D reports, ParaView audit, morphology analysis, evidence boundaries.
- `paper_text/`: Chinese manuscript-ready method, result, discussion, and conclusion paragraphs.
- `figures/`: manual-review PNG/SVG/PDF figures and postprocessed maps.
- `manifests/`: data, geometry, evidence, wind-climate proxy, and archive manifests.
- `scripts/`: reproducible postprocessing and analysis scripts.
- `cfd_ready/`: accepted and rejected/counterexample STL geometries used in the experiment.
- `rhino/`: Rhino files for visual checking and geometry management.
- `paraview_states/`: lightweight ParaView `.pvsm` state files for manual VTK inspection.
- `logs/`: selected FluidX3D/ParaView execution logs.
- `manifests/github_archive_manifest.csv`: file-level size and SHA256 checksums for the GitHub archive.

## Recommended Reading Order

1. `reports/final_experiment_package_index.md`
2. `reports/current_data_summary_and_conclusions.md`
3. `reports/model_result_object_consistency_audit.md`
4. `reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md`
5. `reports/paraview_vtk_core_wind_statistics_and_building_analysis.md`
6. `reports/basic_morphology_wind_response_analysis.md`
7. `reports/detailed_data_synthesis_for_paper_conclusions.md`
8. `paper_text/detailed_paper_conclusions_zh.md`
9. `paper_text/method_section_zh.md`
10. `paper_text/basic_morphology_wind_response_conclusion_zh.md`

## Current Main Conclusion

The most manuscript-ready interpretation no longer uses LCZ classification. It uses basic and transferable building-morphology parameters: footprint area, mean height, height/sqrt(area), perimeter-area compactness, elongation ratio, local built fraction, sector enclosure, and combined enclosure score.

The key new finding is that the immediate 0-20 m facade-adjacent band is uniformly sheltered, while the 20-50 m local-context band better reveals morphology-dependent wind recovery. In that band, 50 m sector enclosure is the clearest suppressor of mean VR, whereas footprint area, elongation ratio, and perimeter-area compactness are weak predictors in this screened campus core.

## Evidence Boundary

This archive supports a reproducible digital-twin-to-CFD design-application workflow and preliminary FluidX3D pedestrian-height wind-response screening. It does not provide field-validated prediction accuracy, formal annual comfort/safety compliance, pollutant-dispersion results, simulated S1-Sn design-intervention comparisons, 3DGS boundary-transfer error results, or a completed CityLBM-GH end-to-end run.

Large raw assets and full VTK outputs are not fully embedded in this GitHub archive. Their local paths and source boundaries are recorded in `EXTERNAL_ARTIFACTS.md` and `manifests/evidence_inventory.csv`.
