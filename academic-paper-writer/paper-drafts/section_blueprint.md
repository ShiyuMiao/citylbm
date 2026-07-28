# Section Blueprint: Experiment 3 TUM2TWIN Digital-Twin Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Section Contract

- Reader state before section: the reader has seen AIJ Case A and Case E as benchmark/validation support and now needs to understand why a real digital-twin case is needed.
- Required move 1: distinguish visual digital-twin assets from CFD collision geometry.
- Required move 2: state FluidX3D setup, aggregation level, directions, samples and metrics before reporting values.
- Required move 3: report baseline low-speed pattern, vertical recovery and climate-proxy sensitivity without claiming annual comfort compliance.
- Required move 4: connect building form to wind response using basic morphology descriptors, the near-to-context threshold rule and the stage-transition addendum.
- Required move 5: interpret S1/S2 as negative design-sensitivity evidence, not successful optimization.
- Required move 6: close with digital-twin application value and explicit blockers.

## Evidence Hooks

- Baseline: `0.076 / 0.934`
- Vertical recovery: `1.049 / 0.000`
- Climate proxy: `0.077 / 0.931`
- Morphology robustness: `0.122+/-0.166 / -0.147 / 0.083`
- Threshold screening: `mean_height_m=low_tertile + elongation_ratio=high_tertile / 0.0057 / 0.857 / -0.416`
- Building-form response archetypes: `R1_A1_linear_low_relative_height_recovery / R4_A5_open_or_mixed_low_response / 0.0001682 / 0.0080 vs 0.0007`
- Stage transition: `near/local/recovery mean VR 0.003182 / 0.005560 / 0.002378; best rule mean_height_m_tertile=low + elongation_ratio_tertile=high + relative_enclosure_score_tertile=high / n=5 / mean recovery 0.0065 / top share 1.000; height/sqrt(area) Cliff delta -0.577`
- Directional fingerprint: `range mean 0.008655; stage ranges persistent/recovery/reactive 0.001579 / 0.018941 / 0.021421; stage Kruskal p 1.02e-15; rho mean_height -0.363, sector_enclosure -0.362`
- S1/S2: `-0.000213 / 0.000233`; `-0.000466 / 0.000633`; `315 deg / 0.002374 / 0.006646`
- GCRI: `0.455 / 0.925 / 0.918`

## Figure and Table Callouts

| callout_id   | recommended_file                                                         | purpose                                                                                                                                             |
|:-------------|:-------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------|
| Fig. E3-1    | figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png                  | Baseline pedestrian-layer spatial VR/stagnation pattern for manual review.                                                                          |
| Fig. E3-2    | figures/basic_morphology_multivariate_rank_model_importance.png          | Morphology ranking: rank-regression coefficients and permutation importance.                                                                        |
| Fig. E3-3    | figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png | S1/S2 directional local trade-off summary.                                                                                                          |
| Fig. E3-4    | figures/morphology_threshold_recovery_rule_summary.png                   | Near-to-context morphology threshold design-rule screening: mean_height_m=low_tertile + elongation_ratio=high_tertile / 0.0057 / 0.857 / -0.416.    |
| Fig. E3-S1   | figures/experiment3_effect_size_uncertainty_forest.png                   | Supplementary effect-size and uncertainty audit for S0 low-speed baseline, vertical recovery, S1/S2 negative sensitivity and morphology recovery.   |
| Fig. E3-S2   | figures/experiment3_directional_anisotropy_panel.png                     | Supplementary eight-direction anisotropy and design-sector response for S0 baseline, vertical recovery and S1/S2 design sensitivity.                |
| Fig. E3-S3   | figures/morphology_form_response_archetype_panel.png                     | Supplementary building-form response archetype analysis for 101 retained components and 20-50 m recovery contrast.                                  |
| Fig. E3-S4   | figures/morphology_stage_transition_panel.png                            | Supplementary near-to-context morphology stage-transition analysis separating facade-adjacent shelter, 20-50 m recovery and directional reactivity. |
| Fig. E3-S5   | figures/morphology_directional_fingerprint_panel.png                     | Supplementary morphology directional fingerprint analysis linking 20-50 m wind-sector response to enclosure, height and stage-transition class.     |
| Table E3-1   | figures/final_integrated_key_result_matrix.csv                           | One-page paper-facing result matrix with evidence sources.                                                                                          |
| Table E3-2   | figures/experiment3_completion_audit_matrix.csv                          | Paper-readiness and blocked-claim audit.                                                                                                            |
| Table E3-3   | manifests/gcri_scoring_table.csv                                         | Geometry-to-CFD readiness scoring for visual and collision geometries.                                                                              |

## Failure Checks

- Do not write field validation, wind-tunnel closure, annual Lawson/NEN/AIJ compliance, pollutant dispersion, GCBTE closure or CityLBM-GH end-to-end execution as completed.
- Do not write the morphology threshold, stage-transition or directional-fingerprint subgroup rules as universal design thresholds.
- Do not use Open-Meteo 2024 as a measured site wind rose.
