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
