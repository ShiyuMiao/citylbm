# Experiment 3 Claim-Verification Hygiene Audit

evidence_type: newly_run + preexisting_artifact

## Summary

- Claim-verification rows after normalization: `44`
- Blank `claim_or_asset` rows after normalization: `0`
- Rows normalized from blank claim names: `7`

## Interpretation

This audit does not add CFD results. It removes a table-hygiene problem in the paper-facing claim inventory by assigning stable module-level identifiers to synthesis rows that previously had evidence sources but no `claim_or_asset` name.

## Audit Rows

| row_index | old_claim_or_asset | new_claim_or_asset | status | source |
|---|---|---|---|---|
| 1 | S0 baseline pedestrian screening | S0 baseline pedestrian screening | unchanged | figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv |
| 2 | Vertical recovery | Vertical recovery | unchanged | figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv |
| 3 | Climate-proxy sensitivity | Climate-proxy sensitivity | unchanged | figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv |
| 4 | S1 design sensitivity | S1 design sensitivity | unchanged | figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv |
| 5 | S2 design sensitivity | S2 design sensitivity | unchanged | figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv |
| 6 | Directional local trade-off | Directional local trade-off | unchanged | figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv |
| 7 | Morphology robustness | Morphology robustness | unchanged | figures/basic_morphology_rank_model_cv_summary.csv; figures/basic_morphology_multivariate_robustness.csv |
| 8 | Morphology threshold design rule | Morphology threshold design rule | unchanged | figures/morphology_threshold_rule_screening.csv; figures/morphology_recovery_top_bottom_contrast.csv |
| 9 | Geometry-to-CFD readiness | Geometry-to-CFD readiness | unchanged | manifests/gcri_scoring_table.csv |
| 10 | Effect-size uncertainty | Effect-size uncertainty | unchanged | figures/experiment3_effect_size_uncertainty_summary.csv |
| 11 | Directional anisotropy | Directional anisotropy | unchanged | figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv |
| 12 | Building-form response archetypes | Building-form response archetypes | unchanged | figures/morphology_form_response_archetype_summary.csv; reports/morphology_form_response_archetype_analysis.md |
| 13 | Morphology stage transition | Morphology stage transition | unchanged | figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_rule_table.csv; figures/morphology_stage_transition_feature_contrasts.csv |
| 14 | Morphology directional fingerprint | Morphology directional fingerprint | unchanged | figures/morphology_directional_fingerprint_by_component.csv; figures/morphology_directional_fingerprint_feature_correlations.csv; figures/morphology_directional_fingerprint_stage_summary.csv |
| 15 | module_claim_M1 | module_claim_M1 | unchanged | reports/data_source_and_download_manifest.md; reports/cfd_ready_geometry_qa.md; manifests/gcri_scoring_table.csv |
| 16 | module_claim_R1 | module_claim_R1 | unchanged | figures/final_integrated_key_result_matrix.csv |
| 17 | module_claim_R2 | module_claim_R2 | unchanged | figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv |
| 18 | module_claim_R3 | module_claim_R3 | unchanged | figures/basic_morphology_multivariate_robustness.csv; reports/basic_morphology_multivariate_robustness.md |
| 19 | module_claim_R3b | module_claim_R3b | unchanged | figures/morphology_threshold_rule_screening.csv; reports/morphology_threshold_design_rule_analysis.md; paper_text/morphology_threshold_design_rule_conclusion_zh.md |
| 20 | module_claim_R3c | module_claim_R3c | unchanged | figures/morphology_form_response_archetype_summary.csv; figures/morphology_form_response_archetype_by_component.csv; reports/morphology_form_response_archetype_analysis.md; paper_text/morphology_form_response_archetype_conclusion_zh.md |
| 21 | module_claim_R3d | module_claim_R3d | unchanged | figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_feature_contrasts.csv; reports/morphology_stage_transition_analysis.md; paper_text/morphology_stage_transition_conclusion_zh.md |
| 22 | module_claim_R3e | module_claim_R3e | unchanged | figures/morphology_directional_fingerprint_by_component.csv; figures/morphology_directional_fingerprint_feature_correlations.csv; figures/morphology_directional_fingerprint_stage_summary.csv; reports/morphology_directional_fingerprint_analysis.md |
| 23 | module_claim_R4 | module_claim_R4 | unchanged | figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv |
| 24 | module_claim_L1 | module_claim_L1 | unchanged | reports/claim_boundary.md; reports/experiment3_completion_audit_and_paper_readiness.md |
| 25 | Fig. E3-1 | Fig. E3-1 | unchanged | figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png |
| 26 | Fig. E3-2 | Fig. E3-2 | unchanged | figures/basic_morphology_multivariate_rank_model_importance.png |
| 27 | Fig. E3-3 | Fig. E3-3 | unchanged | figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png |
| 28 | Fig. E3-4 | Fig. E3-4 | unchanged | figures/morphology_threshold_recovery_rule_summary.png |
| 29 | Fig. E3-S1 | Fig. E3-S1 | unchanged | figures/experiment3_effect_size_uncertainty_forest.png |
| 30 | Fig. E3-S2 | Fig. E3-S2 | unchanged | figures/experiment3_directional_anisotropy_panel.png |
| 31 | Fig. E3-S3 | Fig. E3-S3 | unchanged | figures/morphology_form_response_archetype_panel.png |
| 32 | Fig. E3-S4 | Fig. E3-S4 | unchanged | figures/morphology_stage_transition_panel.png |
| 33 | Fig. E3-S5 | Fig. E3-S5 | unchanged | figures/morphology_directional_fingerprint_panel.png |
| 34 | Table E3-1 | Table E3-1 | unchanged | figures/final_integrated_key_result_matrix.csv |
| 35 | Table E3-2 | Table E3-2 | unchanged | figures/experiment3_completion_audit_matrix.csv |
| 36 | Table E3-3 | Table E3-3 | unchanged | manifests/gcri_scoring_table.csv |
| 37 |  | module_claim_NUMERICAL_PROTOCOL | blank_name_normalized | manifests/fluidx3d_numerical_protocol_audit.csv; reports/fluidx3d_numerical_protocol_and_stability_audit.md |
| 38 |  | module_claim_BUILDING_FORM_MECHANISM | blank_name_normalized | figures/building_form_wind_mechanism_parameter_matrix.csv; reports/building_form_wind_mechanism_synthesis.md |
| 39 |  | module_claim_FINAL_DISCUSSION | blank_name_normalized | manifests/experiment3_final_discussion_paragraph_evidence_map.csv; reports/experiment3_final_sci_discussion_evidence_map.md |
| 40 |  | module_claim_ABSTRACT | blank_name_normalized | manifests/experiment3_abstract_highlights_evidence_map.csv; reports/experiment3_sci_abstract_highlights_audit.md |
| 41 |  | module_claim_RQ_SYNTHESIS | blank_name_normalized | manifests/experiment3_research_question_evidence_matrix.csv; reports/experiment3_research_question_synthesis.md |
| 42 |  | module_claim_LIMITATIONS_ROADMAP | blank_name_normalized | manifests/experiment3_limitations_future_validation_roadmap.csv; reports/experiment3_limitations_future_validation_roadmap.md |
| 43 |  | module_claim_FIGURE_TABLE_NARRATIVE | blank_name_normalized | manifests/experiment3_figure_table_narrative_chain.csv; reports/experiment3_figure_table_narrative_chain.md |
| 44 | module_claim_SUBMISSION_STATEMENTS | module_claim_SUBMISSION_STATEMENTS | unchanged | manifests/experiment3_submission_statement_evidence_map.csv; reports/experiment3_submission_statement_package.md |
