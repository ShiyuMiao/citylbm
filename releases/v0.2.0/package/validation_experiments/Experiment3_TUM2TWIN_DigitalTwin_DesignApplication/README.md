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
16. `reports/morphology_threshold_design_rule_analysis.md`
17. `paper_text/morphology_threshold_design_rule_conclusion_zh.md`
18. `reports/experiment3_completion_audit_and_paper_readiness.md`
19. `paper_text/final_integrated_results_discussion_zh.md`
20. `paper_text/final_integrated_results_discussion_en.md`
21. `paper_text/experiment3_sci_manuscript_module_zh.md`
22. `paper_text/experiment3_sci_manuscript_module_en.md`
23. `paper_text/experiment3_figure_table_callouts_zh.md`
24. `paper_text/experiment3_sci_section_paper_draft_zh.md`
25. `paper_text/experiment3_sci_section_paper_draft_en.md`
26. `reports/experiment3_paper_draft_verification.md`
27. `paper_text/experiment3_sci_figure_captions_zh.md`
28. `paper_text/experiment3_sci_table_captions_zh.md`
29. `reports/experiment3_submission_readiness_audit.md`
30. `reports/experiment3_effect_size_uncertainty_analysis.md`
31. `paper_text/experiment3_effect_size_uncertainty_results_zh.md`
32. `reports/experiment3_directional_anisotropy_analysis.md`
33. `paper_text/experiment3_directional_anisotropy_results_zh.md`
34. `reports/fluidx3d_numerical_protocol_and_stability_audit.md`
35. `paper_text/fluidx3d_numerical_protocol_methods_zh.md`

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

## Morphology Threshold Design-Rule Addendum

The archive now includes a near-to-context recovery analysis that compares the same 101 retained building components in the 0-20 m facade-adjacent band and the 20-50 m local-context band. It extracts sample-internal morphology threshold rules for design screening.

- `reports/morphology_threshold_design_rule_analysis.md`
- `paper_text/morphology_threshold_design_rule_conclusion_zh.md`
- `figures/morphology_near_to_context_recovery_by_component.csv`
- `figures/morphology_recovery_top_bottom_contrast.csv`
- `figures/morphology_threshold_rule_screening.csv`
- `figures/morphology_threshold_recovery_rule_summary.png`
- `manifests/morphology_threshold_design_rule_claims.csv`

Paper-safe interpretation: the 20-50 m band exposes morphology-sensitive wind recovery that is hidden in the uniformly sheltered 0-20 m facade-adjacent band. The best simple subgroup rule is sample-internal and should not be written as a universal or field-validated design threshold.

## Final Integrated Paper-Readiness Layer

The archive now includes a final integrated result matrix, completion audit, and manuscript-ready Chinese/English results-discussion sections. This layer binds the baseline, climate-proxy weighting, S1/S2 sensitivity, directional trade-off, morphology robustness, morphology threshold screening, GCRI geometry readiness, and claim boundary into a single paper-facing package.

- `figures/final_integrated_key_result_matrix.csv`
- `figures/experiment3_completion_audit_matrix.csv`
- `reports/experiment3_completion_audit_and_paper_readiness.md`
- `paper_text/final_integrated_results_discussion_zh.md`
- `paper_text/final_integrated_results_discussion_en.md`

## SCI Manuscript Module

The archive now includes a section-level SCI manuscript module. It consolidates the method positioning, experimental setup, result interpretation, design-application discussion, limitations, figure/table callouts, and claim inventory into paper-facing Chinese and English text.

- `paper_text/experiment3_sci_manuscript_module_zh.md`
- `paper_text/experiment3_sci_manuscript_module_en.md`
- `paper_text/experiment3_figure_table_callouts_zh.md`
- `reports/experiment3_manuscript_module_audit.md`
- `manifests/experiment3_manuscript_module_claims.csv`
- `manifests/experiment3_manuscript_figure_table_plan.csv`

Paper-safe interpretation: this is the highest-level writing layer for Experiment 3. It strengthens the conclusion that the digital-twin model is most valuable as a geometry-to-CFD translation and campus wind-screening workflow, while explicitly preserving the evidence boundary around field validation, formal annual comfort compliance, pollutant dispersion, GCBTE, and CityLBM-GH execution.

## SCI Section Paper Draft Package

The archive now includes a continuous section-level paper draft generated from the verified Experiment 3 evidence. The canonical working copy is under `academic-paper-writer/paper-drafts/`, with release copies kept in `paper_text/`.

- `academic-paper-writer/paper-drafts/paper_draft.md`
- `academic-paper-writer/paper-drafts/paper_draft_en.md`
- `academic-paper-writer/paper-drafts/section_blueprint.md`
- `academic-paper-writer/paper-drafts/experiment3_claim_verification.csv`
- `academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md`
- `paper_text/experiment3_sci_section_paper_draft_zh.md`
- `paper_text/experiment3_sci_section_paper_draft_en.md`
- `reports/experiment3_paper_draft_verification.md`

Paper-safe interpretation: this is a generic SCI section draft, not a venue-formatted final manuscript. It is ready for integration into the wider paper after the target journal, final citation style, and paper-level introduction/related-work framing are fixed.

## SCI Figure/Table Caption and Submission-Readiness Layer

The archive now includes bilingual SCI-style captions for four main figures, five supplementary figures and three recommended tables, plus an asset-level submission-readiness audit. This layer does not add new CFD results; it binds each reviewer-facing figure/table to its evidence type, source data, safe paper use, and claim boundary.

- `academic-paper-writer/paper-drafts/figure_table_captions.md`
- `paper_text/experiment3_sci_figure_captions_zh.md`
- `paper_text/experiment3_sci_figure_captions_en.md`
- `paper_text/experiment3_sci_table_captions_zh.md`
- `paper_text/experiment3_sci_table_captions_en.md`
- `reports/experiment3_submission_readiness_audit.md`
- `manifests/experiment3_submission_readiness_checklist.csv`

Audit result: all twelve planned figure/table assets exist and are ready for manual review. Remaining blockers are unchanged: field/wind-tunnel validation, annual comfort/safety compliance, pollutant transport, GCBTE computation, and CityLBM-Grasshopper end-to-end execution.

## Effect-Size and Uncertainty Addendum

The archive now includes a supplementary statistical layer that recomputes effect sizes and uncertainty intervals from existing archived CSV outputs. It uses S0's 8 directions x 3 post-spin-up samples, paired z~40 m minus z~2 m vertical differences, S1/S2 eight-direction z~2 m ranges, and the 101-component morphology recovery table.

- `scripts/analyze_experiment3_effect_size_uncertainty.py`
- `figures/experiment3_effect_size_uncertainty_summary.csv`
- `figures/experiment3_effect_size_uncertainty_forest.png`
- `reports/experiment3_effect_size_uncertainty_analysis.md`
- `paper_text/experiment3_effect_size_uncertainty_results_zh.md`
- `manifests/experiment3_effect_size_uncertainty_claims.csv`

Paper-safe interpretation: the pedestrian-layer low-speed result, the z~40 m versus z~2 m vertical recovery, and the S1/S2 near-null or negative global effects are stable within the archived direction-sample or directional uncertainty layer. This is not measurement uncertainty, grid-convergence proof, annual comfort exceedance probability, or a universal morphology threshold.

## Directional Anisotropy and Design-Sector Addendum

The archive now includes an eight-direction mechanism analysis that distinguishes quasi-omnidirectional campus sheltering from directionally localized design response.

- `scripts/analyze_experiment3_directional_anisotropy.py`
- `figures/experiment3_directional_response_by_wind.csv`
- `figures/experiment3_directional_anisotropy_summary.csv`
- `figures/experiment3_directional_anisotropy_panel.png`
- `reports/experiment3_directional_anisotropy_analysis.md`
- `paper_text/experiment3_directional_anisotropy_results_zh.md`
- `manifests/experiment3_directional_anisotropy_claims.csv`

Paper-safe interpretation: pedestrian-layer mean VR remains low and stagnation remains high across all eight simulated directions, so the main problem is not a single exceptional inflow direction. S2 has a localized directional response, strongest at 315 deg, but S1/S2 global pedestrian-layer mean-VR deltas remain negative in every tested direction. This supports wind-sector-coupled design reasoning, not annual wind-climate compliance or successful optimization.

## Building-Form Wind-Response Archetype Addendum

The archive now includes a compact morphology-response typology for the 101 retained central building components. The clustering uses only basic building-form parameters, then interprets each group using FluidX3D-derived near-facade and 20-50 m local-context wind metrics.

- `scripts/analyze_morphology_form_response_archetypes.py`
- `figures/morphology_form_response_archetype_by_component.csv`
- `figures/morphology_form_response_archetype_summary.csv`
- `figures/morphology_form_response_archetype_panel.png`
- `reports/morphology_form_response_archetype_analysis.md`
- `paper_text/morphology_form_response_archetype_conclusion_zh.md`
- `manifests/morphology_form_response_archetype_claims.csv`

Paper-safe interpretation: the type separation supports a more detailed building-form conclusion for Experiment 3. Pedestrian-layer recovery is associated with combinations of relative vertical massing, elongation and local enclosure, not with a single footprint, height or porosity variable alone. The typology is a FluidX3D/digital-twin screening result, not a field-validated causal taxonomy.

## Morphology Stage-Transition Addendum

The archive now includes a stage-transition analysis that separates the 0-20 m
facade-adjacent sheltered band, the 20-50 m local-context recovery band, and
directional reactivity for the same 101 retained central components.

- `scripts/analyze_morphology_stage_transition.py`
- `figures/morphology_stage_transition_summary.csv`
- `figures/morphology_stage_transition_feature_contrasts.csv`
- `figures/morphology_stage_transition_rule_table.csv`
- `figures/morphology_stage_transition_by_component.csv`
- `figures/morphology_stage_transition_panel.png`
- `reports/morphology_stage_transition_analysis.md`
- `paper_text/morphology_stage_transition_conclusion_zh.md`
- `paper_text/morphology_stage_transition_conclusion_en.md`
- `manifests/morphology_stage_transition_claims.csv`

Paper-safe interpretation: the 0-20 m facade-adjacent band is a low-speed
saturated stage, while the 20-50 m local-context band reveals
morphology-differentiated recovery. Top-recovery components have lower
relative vertical scale than bottom-recovery components, and the strongest
sample-internal subgroup combines low height, high elongation, and high
relative enclosure. This remains a digital-twin screening result, not a
field-validated or universal design threshold.

## Morphology Directional Fingerprint Addendum

The archive now includes a directional-fingerprint analysis that links the
eight-direction 20-50 m local-context response of the same 101 retained
components to basic morphology descriptors and stage-transition classes.

- `scripts/analyze_morphology_directional_fingerprint.py`
- `figures/morphology_directional_fingerprint_by_component.csv`
- `figures/morphology_directional_fingerprint_feature_correlations.csv`
- `figures/morphology_directional_fingerprint_stage_summary.csv`
- `figures/morphology_directional_fingerprint_best_wind_summary.csv`
- `figures/morphology_directional_fingerprint_panel.png`
- `reports/morphology_directional_fingerprint_analysis.md`
- `paper_text/morphology_directional_fingerprint_conclusion_zh.md`
- `paper_text/morphology_directional_fingerprint_conclusion_en.md`
- `manifests/morphology_directional_fingerprint_claims.csv`

Paper-safe interpretation: useful campus-scale ventilation recovery appears
not only as a higher 20-50 m mean VR, but also as stronger wind-sector
directional response. Persistent-shelter components suppress both mean VR and
directional range, while recovery/reactive components show stronger local
wind-sector fingerprints. This remains sample-internal digital-twin screening
evidence, not field validation, annual wind-rose compliance or a universal
directional morphology threshold.

## FluidX3D Numerical Protocol and Stability Boundary Layer

The archive now includes a numerical-protocol audit that binds the core
FluidX3D case setup to claim boundaries. It records grid/domain dimensions,
reference speed, air viscosity, LBM conversion, tau/Re descriptors, wind
directions, sampling steps, output planes, temporal-stability support, partial
grid-sensitivity evidence, and blocked convergence/compliance items.

- `scripts/synthesize_fluidx3d_numerical_protocol_audit.py`
- `manifests/fluidx3d_numerical_protocol_audit.csv`
- `reports/fluidx3d_numerical_protocol_and_stability_audit.md`
- `paper_text/fluidx3d_numerical_protocol_methods_zh.md`
- `paper_text/fluidx3d_numerical_protocol_methods_en.md`

Paper-safe interpretation: the FluidX3D case is transparent enough for
screening-level reproduction and manuscript review, while residual
convergence, complete grid independence, field validation and annual
comfort/safety compliance remain outside the supported claim boundary.

## Reviewer Reproducibility and Claim-Risk Layer

The archive now includes a reviewer-facing reproducibility and claim-risk audit
that maps each paper-facing claim to evidence type, source artifact, likely
reviewer question, and required boundary language.

- `scripts/synthesize_experiment3_reviewer_reproducibility_pack.py`
- `reports/experiment3_reviewer_reproducibility_and_claim_audit.md`
- `manifests/experiment3_reviewer_claim_risk_matrix.csv`
- `paper_text/experiment3_reviewer_response_paragraphs_en.md`
- `paper_text/experiment3_reviewer_response_paragraphs_zh.md`

Paper-safe interpretation: this layer is for pre-submission checking and
reviewer response. It does not add new CFD results; it prevents overclaiming by
separating paper-ready screening claims from blocked validation, compliance,
pollutant, GCBTE and CityLBM-GH claims.

## Final Completeness and Gap Audit Layer

The archive now includes a final reconciliation layer that checks whether the
paper-facing result matrix, figure/table assets, evidence inventory, claim
verification, and remaining blockers are mutually consistent.

- `scripts/synthesize_experiment3_final_completeness_audit.py`
- `manifests/experiment3_final_requirement_coverage.csv`
- `reports/experiment3_final_completeness_and_gap_audit.md`
- `reports/experiment3_completion_audit_and_paper_readiness.md`
- `reports/experiment3_paper_draft_verification.md`
- `paper_text/experiment3_final_contribution_and_conclusion_zh.md`
- `paper_text/experiment3_final_contribution_and_conclusion_en.md`
- `academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md`

Audit result: the final archive currently contains 15 key result rows, 12
reviewer-facing figure/table callouts, 12 ready submission assets, and 116
evidence-inventory entries. It is complete for a standalone Experiment 3
section if framed as FluidX3D-native digital-twin-to-CFD wind screening with
CityLBM-compatible geometry preparation. It remains incomplete for field
validation, annual comfort/safety compliance, pollutant dispersion, GCBTE,
CityLBM-Grasshopper end-to-end execution, and successful design optimization
claims.
