# Experiment 3 SCI Figure Captions

evidence_type: newly_run + preexisting_artifact + blocked

These captions are tied to archived source artifacts. They should be edited only for journal style, not for claim strength, unless new evidence is added.

## Fig. E3-1

Fig. E3-1. Pedestrian-height FluidX3D/VTK velocity-ratio screening map for the TUM Downtown core campus block. The panel is derived from the dx=2 m, eight-direction, three-sample core closed-prism collision setup and is intended for manual review of low-speed regions, directional consistency and building-adjacent stagnation. It supports a screening-level low-ventilation interpretation, not annual comfort compliance, field validation or pollutant dispersion.

- Asset: `figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png`
- Source data: `figures/paraview_vtk_core_dx2m_robustness_stats.csv; figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`
- Evidence type: `newly_run`
- Boundary: not annual Lawson/NEN/AIJ compliance; not field validation; not scalar dispersion

## Fig. E3-2

Fig. E3-2. Multivariate robustness analysis linking basic building-form parameters to wind response in the 20-50 m local-context band. Rank-regression coefficients and permutation importance indicate that local enclosure, mean height and combined enclosure are more informative than footprint area, elongation or compactness in this screened sample. Because cross-validated explanatory power is limited, the figure should be used as interpretable screening evidence rather than as a high-accuracy predictor.

- Asset: `figures/basic_morphology_multivariate_rank_model_importance.png`
- Source data: `figures/basic_morphology_multivariate_robustness.csv; figures/basic_morphology_rank_model_cv_summary.csv`
- Evidence type: `newly_run`
- Boundary: not a deterministic surrogate model; not externally validated thresholds

## Fig. E3-3

Fig. E3-3. Directional local trade-off of S1/S2 design-sensitivity scenarios at pedestrian height. The heatmap compares velocity-ratio changes in common open cells across inflow directions. S2 produces slightly stronger local positive response than S1, but improved cells remain sparse and newly opened cells stay low-speed. The figure is therefore negative design evidence: geometric porosity alone is insufficient to recover pedestrian-layer ventilation in this campus core.

- Asset: `figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png`
- Source data: `figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv; figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`
- Evidence type: `newly_run`
- Boundary: not successful optimization; not final design recommendation

## Fig. E3-4

Fig. E3-4. Threshold-rule screening for wind-speed recovery from the 0-20 m facade-adjacent band to the 20-50 m local-context band. The analysis pairs the same 101 retained building components and extracts sample-internal tertile rules. The best simple rule suggests that lower relative vertical scale combined with selected plan-form conditions is associated with higher local recovery, but the threshold is only a digital-twin screening rule, not a universal or field-validated design criterion.

- Asset: `figures/morphology_threshold_recovery_rule_summary.png`
- Source data: `figures/morphology_threshold_rule_screening.csv; figures/morphology_recovery_top_bottom_contrast.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not universal threshold; not field-validated design rule

## Fig. E3-S1

Fig. E3-S1. Supplementary forest plot of Experiment 3 effect sizes and uncertainty. The figure summarizes S0 pedestrian and upper-layer velocity ratios, 40 m minus 2 m vertical recovery, S1/S2 pedestrian-layer global changes and morphology near-to-context recovery. It shows that the low-speed baseline, vertical decoupling and S1/S2 negative results are stable within the available direction-sample or directional ranges, but it represents uncertainty in archived simulation outputs only, not measurement uncertainty, grid-convergence proof or annual comfort exceedance probability.

- Asset: `figures/experiment3_effect_size_uncertainty_forest.png`
- Source data: `figures/experiment3_effect_size_uncertainty_summary.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not measurement uncertainty; not grid convergence; not annual comfort exceedance probability

## Fig. E3-S2

Fig. E3-S2. Supplementary eight-direction anisotropy and design-sector response for Experiment 3. The panel compares S0 pedestrian-layer mean VR, pedestrian-layer stagnation ratio, 40 m minus 2 m vertical recovery and S2 common-open-cell local response. The low-speed and high-stagnation state is quasi-omnidirectional across the eight inflow directions, whereas S2 local response is directional and strongest at 315 deg; nevertheless, S1/S2 global pedestrian-layer mean-VR deltas remain negative in all directions. The figure supports wind-sector-coupled design interpretation, not annual wind-rose compliance or successful optimization claims.

- Asset: `figures/experiment3_directional_anisotropy_panel.png`
- Source data: `figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv`
- Evidence type: `newly_run + preexisting_artifact + blocked`
- Boundary: not measured wind rose; not annual comfort compliance; not successful optimization

## Fig. E3-S3

Fig. E3-S3. Supplementary building-form wind-response archetype analysis for the 101 retained central components. The left panel maps morphology clusters in sector-enclosure and relative-height space, with point size proportional to footprint area; the right panel compares the mean 20-50 m recovery delta by archetype. The groups differ significantly in recovery delta (Kruskal-Wallis p=0.0001682), supporting a screening-level conclusion that wind recovery is associated with combinations of relative vertical massing, elongation and local enclosure rather than any single building-form variable.

- Asset: `figures/morphology_form_response_archetype_panel.png`
- Source data: `figures/morphology_form_response_archetype_summary.csv; figures/morphology_form_response_archetype_by_component.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not causal typology; not field validation; not universal design class

## Fig. E3-S4

Fig. E3-S4. Supplementary morphology stage-transition analysis. The panel decomposes the wind response of the 101 retained building components into the 0-20 m facade-adjacent sheltered stage, the 20-50 m local-context recovery stage and directional reactivity. The facade-adjacent band is nearly saturated by low-speed conditions, whereas the 20-50 m band reveals recovery contrasts linked to relative vertical scale, plan elongation and local enclosure. The figure is intended for digital-twin design screening, not for a field-validated causal threshold or universal design code.

- Asset: `figures/morphology_stage_transition_panel.png`
- Source data: `figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_feature_contrasts.csv; figures/morphology_stage_transition_rule_table.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not field validation; not universal morphology threshold; not annual comfort compliance
