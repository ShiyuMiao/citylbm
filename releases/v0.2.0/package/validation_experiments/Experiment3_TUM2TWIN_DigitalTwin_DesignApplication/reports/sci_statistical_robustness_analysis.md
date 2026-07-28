# SCI Statistical Robustness Analysis

evidence_type: newly_run + blocked

This report adds statistical robustness checks to the existing morphology-wind-response conclusion. It does not add new CFD fields; it reuses component-level morphology and wind-response CSVs generated from the FluidX3D/ParaView post-processing pipeline.

## Inputs and Protocol

- Inputs: `figures/basic_morphology_per_component_near_facade_0_20m.csv` and `figures/basic_morphology_per_component_local_context_20_50m.csv`.
- Unit of analysis: retained building components, `n=101` for each zone.
- Response: component-level `directional_mean_vr`.
- Predictors: footprint area, mean height, height/sqrt(area), perimeter²/area, elongation, local built fraction within 30 m, sector enclosure within 50 m, and combined enclosure score.
- Robustness checks: 2,000 bootstrap resamples for Spearman correlations and high-vs-low tertile effects; 200 repeated 5-fold cross-validation runs for OLS model comparison.

## Bootstrap Correlations

The local-context band preserves the main negative association between enclosure and pedestrian wind recovery:

| parameter | rho | 95% CI | n |
| --- | --- | --- | --- |
| sector enclosure, r=50 m | -0.396 | [-0.574, -0.158] | 101 |
| mean height | -0.351 | [-0.532, -0.147] | 101 |
| combined enclosure score | -0.302 | [-0.483, -0.097] | 101 |
| local built fraction, r=30 m | -0.226 | [-0.411, -0.039] | 101 |
| height / sqrt(area) | -0.208 | [-0.376, -0.025] | 101 |

The combined enclosure score has Spearman rho `-0.302` with a 95% bootstrap interval of `[-0.483, -0.097]`. Sector enclosure and mean height also remain mostly negative in the resampling distribution. This supports the claim that wind recovery is linked to local morphological context rather than to a single extreme component.

## Tertile Effect Robustness

| zone | parameter | low mean VR | high mean VR | delta | 95% CI |
| --- | --- | --- | --- | --- | --- |
| local_context_20_50m | combined enclosure score | 0.0086 | 0.0042 | -0.0043 | [-0.0076, -0.0014] |
| near_facade_0_20m | combined enclosure score | 0.0060 | 0.0017 | -0.0043 | [-0.0066, -0.0024] |
| near_facade_0_20m | local built fraction, r=30 m | 0.0057 | 0.0017 | -0.0039 | [-0.0062, -0.0020] |
| local_context_20_50m | local built fraction, r=30 m | 0.0082 | 0.0043 | -0.0039 | [-0.0072, -0.0009] |
| local_context_20_50m | mean height | 0.0079 | 0.0048 | -0.0032 | [-0.0060, 0.0002] |
| local_context_20_50m | sector enclosure, r=50 m | 0.0056 | 0.0040 | -0.0015 | [-0.0032, -0.0002] |
| local_context_20_50m | height / sqrt(area) | 0.0064 | 0.0051 | -0.0013 | [-0.0039, 0.0017] |
| near_facade_0_20m | footprint area | 0.0043 | 0.0031 | -0.0011 | [-0.0034, 0.0011] |

High combined enclosure in the 20-50 m band reduces mean VR by `-0.0043` compared with the low-enclosure group, with a bootstrap 95% CI of `[-0.0076, -0.0014]`. High local built fraction produces a comparable effect of `-0.0039` with a 95% CI of `[-0.0072, -0.0009]`.

## Cross-Validated Model Comparison

| zone | model | CV R2 mean | CV R2 SD | RMSE |
| --- | --- | --- | --- | --- |
| local_context_20_50m | all_with_composite | 0.383 | 0.262 | 0.0050 |
| local_context_20_50m | all_without_composite | 0.373 | 0.146 | 0.0051 |
| local_context_20_50m | context_only | 0.325 | 0.072 | 0.0053 |
| local_context_20_50m | context_plus_height | 0.309 | 0.098 | 0.0053 |
| local_context_20_50m | size_height_shape | -0.130 | 0.185 | 0.0068 |
| near_facade_0_20m | all_without_composite | 0.459 | 0.213 | 0.0031 |
| near_facade_0_20m | context_only | 0.446 | 0.066 | 0.0032 |
| near_facade_0_20m | all_with_composite | 0.433 | 0.274 | 0.0032 |
| near_facade_0_20m | context_plus_height | 0.433 | 0.082 | 0.0032 |
| near_facade_0_20m | size_height_shape | -0.148 | 0.163 | 0.0046 |

For the 20-50 m local-context band, the context-only model reaches mean cross-validated R² `0.325`, while the size-height-shape model reaches `-0.130`. The best local-context model is `all_with_composite` with mean cross-validated R² `0.383`. These values should be interpreted as modest predictive performance, but they are useful for paper argumentation because they show that contextual enclosure variables carry more transferable explanatory signal than object-size descriptors alone.

## SCI-Level Interpretation

The strengthened result is not merely that the campus core is slow at pedestrian height. The more specific conclusion is that local-context geometry controls the limited wind recovery within an already sheltered pedestrian field. In other words, the morphology variables do not transform the site from stagnant to ventilated; instead, they explain where small but design-relevant recovery occurs inside a generally low-speed campus core.

## Claim Boundary

This is a component-level statistical robustness analysis derived from simulation outputs. It is not causal identification, field validation, annual comfort/safety compliance, pollutant dispersion, or a simulated S1 intervention comparison.

## Output Tables

- `figures/sci_stat_bootstrap_spearman_ci.csv`
- `figures/sci_stat_tertile_effect_bootstrap_ci.csv`
- `figures/sci_stat_model_comparison_cv.csv`
- `figures/sci_stat_model_standardized_coefficients.csv`
- `manifests/sci_statistical_robustness_claims.csv`
