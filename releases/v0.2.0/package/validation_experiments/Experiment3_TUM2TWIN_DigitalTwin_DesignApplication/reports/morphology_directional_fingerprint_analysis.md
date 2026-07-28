# Morphology Directional Fingerprint Analysis

evidence_type: newly_run + blocked

## Scope

This analysis reuses the archived FluidX3D-derived `basic_morphology_wind_response_by_component.csv` and the stage-transition component table. It does not run new CFD and does not claim field-validated directional causality. The target is a sample-internal design-screening descriptor for the 20-50 m local-context band.

## Component-Level Directionality

- Retained components: `101`
- Inflow directions: `8`
- Mean 20-50 m directional range of mean VR: `0.008655`
- Mean directional reactivity ratio, defined as `(max_direction_mean_VR - min_direction_mean_VR) / mean_direction_mean_VR`: `1.339`

## Morphology Correlations With Directional Range

| feature                     |   spearman_rho |     p_value |   n_components |
|:----------------------------|---------------:|------------:|---------------:|
| mean_height_m               |      -0.363049 | 0.000190467 |            101 |
| sector_enclosure_ratio_r50m |      -0.362088 | 0.000198653 |            101 |
| relative_enclosure_score    |      -0.327548 | 0.000827043 |            101 |

The strongest monotonic associations with directional range are negative for mean height and sector/local enclosure. This means the components that remain strongly enclosed or vertically massive tend to suppress not only the mean local-context VR, but also the directional spread that would otherwise reveal wind-sector access.

## Stage-Class Separation

| evidence_type       | stage_transition_class   |   n_components |   mean_local_context_vr |   median_local_context_vr |   mean_directional_range_vr |   median_directional_range_vr |   mean_directional_reactivity_ratio |   median_directional_reactivity_ratio |   mean_recovery_delta_vr |   median_recovery_delta_vr |
|:--------------------|:-------------------------|---------------:|------------------------:|--------------------------:|----------------------------:|------------------------------:|------------------------------------:|--------------------------------------:|-------------------------:|---------------------------:|
| newly_run + blocked | persistent_shelter       |             23 |              0.00138748 |                0.0010779  |                   0.0015793 |                    0.0009437  |                            0.943419 |                              0.840189 |             -0.000235416 |               -0.000137443 |
| newly_run + blocked | mixed_low_speed_context  |             43 |              0.00257018 |                0.00202121 |                   0.0035476 |                    0.00197202 |                            1.24122  |                              1.17332  |              0.00105647  |                0.000771581 |
| newly_run + blocked | near_to_context_recovery |             26 |              0.0123429  |                0.0103105  |                   0.0189411 |                    0.0173409  |                            1.62056  |                              1.60959  |              0.00725347  |                0.00649701  |
| newly_run + blocked | directionally_reactive   |              9 |              0.0109078  |                0.0101251  |                   0.0214211 |                    0.0209151  |                            1.99922  |                              2.1054   |              0.00128484  |                0.00102448  |

Kruskal-Wallis test for directional range across stage classes: statistic `72.907`, p-value `1.018e-15`.
Kruskal-Wallis test for directional reactivity ratio across stage classes: statistic `40.089`, p-value `1.02e-08`.

Persistent-shelter components have mean directional range `0.001579`, while near-to-context recovery components reach `0.018941` and directionally reactive components reach `0.021421`. This supports a more detailed interpretation: useful ventilation recovery in this digital-twin block appears when the local context is not only less sheltered on average, but also able to respond differently to inflow sectors.

## Best-Response Directions

| evidence_type       |   best_wind_deg |   component_count |   component_share |
|:--------------------|----------------:|------------------:|------------------:|
| newly_run + blocked |             135 |                20 |          0.19802  |
| newly_run + blocked |             180 |                18 |          0.178218 |
| newly_run + blocked |              45 |                17 |          0.168317 |
| newly_run + blocked |             315 |                17 |          0.168317 |

The best-response direction is not concentrated in a single inflow direction. This is consistent with a complex campus block where local recovery is controlled by local geometry and access paths rather than a single global canyon alignment.

## Claim Boundary

The result can be used to argue that directionality is an additional building-form screening layer beyond mean VR and recovery delta. It cannot be written as a universal design rule, wind-rose compliance result, field-validated causal mechanism, or proof that one morphology variable controls the wind field.

## Output Artifacts

- `figures/morphology_directional_fingerprint_by_component.csv`
- `figures/morphology_directional_fingerprint_feature_correlations.csv`
- `figures/morphology_directional_fingerprint_stage_summary.csv`
- `figures/morphology_directional_fingerprint_best_wind_summary.csv`
- `figures/morphology_directional_fingerprint_panel.png`
- `paper_text/morphology_directional_fingerprint_conclusion_zh.md`
- `paper_text/morphology_directional_fingerprint_conclusion_en.md`
- `manifests/morphology_directional_fingerprint_claims.csv`
