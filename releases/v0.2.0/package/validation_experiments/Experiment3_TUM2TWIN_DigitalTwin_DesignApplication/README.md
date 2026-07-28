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
8. `reports/sci_statistical_robustness_analysis.md`
9. `paper_text/sci_results_discussion_strengthened_zh.md`
10. `paper_text/sci_results_discussion_strengthened_en.md`
11. `paper_text/detailed_paper_conclusions_zh.md`
12. `paper_text/method_section_zh.md`
13. `paper_text/basic_morphology_wind_response_conclusion_zh.md`
14. `reports/basic_morphology_multivariate_robustness.md`
15. `paper_text/basic_morphology_multivariate_robustness_conclusion_zh.md`
16. `reports/experiment3_completion_audit_and_paper_readiness.md`
17. `paper_text/final_integrated_results_discussion_zh.md`
18. `paper_text/final_integrated_results_discussion_en.md`

## Current Main Conclusion

The most manuscript-ready interpretation no longer uses LCZ classification. It uses basic and transferable building-morphology parameters: footprint area, mean height, height/sqrt(area), perimeter-area compactness, elongation ratio, local built fraction, sector enclosure, and combined enclosure score.

The key new finding is that the immediate 0-20 m facade-adjacent band is uniformly sheltered, while the 20-50 m local-context band better reveals morphology-dependent wind recovery. In that band, 50 m sector enclosure is the clearest suppressor of mean VR, whereas footprint area, elongation ratio, and perimeter-area compactness are weak predictors in this screened campus core.

A multivariate robustness addendum strengthens this wording but also narrows it: the rank-transformed ridge model for 20-50 m mean VR has limited explanatory power (`R2 = 0.122 +/- 0.166`), so the morphology parameters should be used as interpretable screening variables rather than deterministic predictors. Sector enclosure, mean height, and combined enclosure remain the strongest ordered signals.

## Evidence Boundary

This archive supports a reproducible digital-twin-to-CFD design-application workflow, preliminary FluidX3D pedestrian-height wind-response screening, and two executed design-sensitivity comparisons (`S1` and `S2`). It does not provide field-validated prediction accuracy, formal annual comfort/safety compliance, pollutant-dispersion results, successful design optimization, S3-Sn design-intervention proof, 3DGS boundary-transfer error results, or a completed CityLBM-GH end-to-end run.

Large raw assets and full VTK outputs are not fully embedded in this GitHub archive. Their local paths and source boundaries are recorded in `EXTERNAL_ARTIFACTS.md` and `manifests/evidence_inventory.csv`.

## Latest Literature-Grounded Synthesis

The latest addendum links the FluidX3D/ParaView outputs to verified pedestrian-wind, campus-CFD, climate-context and digital-twin geometry literature. It adds:

- `reports/literature_grounded_sci_discussion.md`
- `manifests/verified_references_for_sci_discussion.csv`
- `manifests/citation_to_claim_map_sci_discussion.csv`
- `paper_text/literature_grounded_discussion_sci_zh.md`
- `paper_text/literature_grounded_discussion_sci_en.md`

Use these files when writing the final SCI discussion because they explicitly separate paper-ready claims from blocked claims.

## Executed S1 Design Sensitivity Scenario

The design-application layer now includes an executed S1 ventilation-relief sensitivity scenario. S1 was simulated with the same FluidX3D dx=2 m, 8-direction, three-sample protocol as S0. The result is a near-null/negative design sensitivity outcome rather than a successful optimization.

- `reports/s1_ventilation_relief_fluidx3d_comparison_report.md`
- `paper_text/design_intervention_s1_discussion_zh.md`
- `paper_text/design_intervention_s1_discussion_en.md`
- `manifests/s1_design_intervention_claims.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_equal_weighted_vr_delta_z2m.png`

## Executed S2 Network-Porosity Sensitivity Scenario

The design-application layer now includes a second executed sensitivity case, `S2_network_porosity`. S2 tests two east-west plus one north-south least-removal porosity corridors. It was simulated with the same FluidX3D dx=2 m, 8-direction, three-sample protocol as S0/S1. The result remains near-null/negative at the global pedestrian layer, refining the conclusion from "single corridor is insufficient" to "geometric porosity alone is insufficient unless coupled to effective wind-entry positions".

- `reports/s2_network_porosity_fluidx3d_comparison_report.md`
- `paper_text/design_intervention_s2_discussion_zh.md`
- `paper_text/design_intervention_s2_discussion_en.md`
- `manifests/s2_design_intervention_claims.csv`
- `figures/fluidx3d_s0_s2_network_porosity_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_s2_design_sensitivity_height_metric_comparison.png`

## Directional Design Trade-Off Addendum

The archive now includes a deterministic post-processing analysis of S1/S2 directional local trade-offs. It shows that S2 has more localized positive common-open-cell response than S1, but the response is sparse and newly opened cells remain fully low-speed at z~2 m.

- `reports/design_sensitivity_directional_tradeoff_analysis.md`
- `paper_text/design_sensitivity_directional_tradeoff_discussion_zh.md`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png`
- `figures/fluidx3d_s2_minus_s0_directional_delta_panel_z2m.png`

## Multivariate Morphology Robustness Addendum

The archive now includes a lightweight bootstrap/partial-correlation/rank-regression robustness check for the basic morphology interpretation. It confirms that the 20-50 m local-context band is better treated as a local enclosure and momentum-exchange diagnostic than as a single-building size or shape effect.

- `reports/basic_morphology_multivariate_robustness.md`
- `paper_text/basic_morphology_multivariate_robustness_conclusion_zh.md`
- `figures/basic_morphology_multivariate_robustness.csv`
- `figures/basic_morphology_rank_model_cv_summary.csv`
- `figures/basic_morphology_multivariate_rank_model_importance.png`

## Final Integrated Paper-Readiness Layer

The archive now includes a final integrated result matrix, completion audit, and manuscript-ready Chinese/English results-discussion sections. This layer binds the baseline, climate-proxy weighting, S1/S2 sensitivity, directional trade-off, morphology robustness, GCRI geometry readiness, and claim boundary into a single paper-facing package.

- `figures/final_integrated_key_result_matrix.csv`
- `figures/experiment3_completion_audit_matrix.csv`
- `reports/experiment3_completion_audit_and_paper_readiness.md`
- `paper_text/final_integrated_results_discussion_zh.md`
- `paper_text/final_integrated_results_discussion_en.md`
