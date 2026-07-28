# Multivariate Robustness of Basic Morphology-Wind Relations

evidence_type: newly_run

## Purpose

This supplementary analysis tests whether the basic morphology conclusion is robust beyond single-parameter Spearman correlations. It uses the same retained central components and FluidX3D-derived wind-response table as the basic morphology analysis, with no solver rerun.

## Protocol

- Inputs: `figures/basic_morphology_per_component_near_facade_0_20m.csv` and `figures/basic_morphology_per_component_local_context_20_50m.csv`.
- Sample unit: retained building component (`n=101`).
- Predictors: footprint area, mean height, height/sqrt(area), perimeter^2/area, elongation ratio, local built fraction within 30 m, sector enclosure within 50 m and combined enclosure score.
- Responses: eight-direction averaged mean VR, P95 VR and directional range of mean VR.
- Robustness checks: bootstrap Spearman intervals (`n=300`), partial Spearman after controlling for the remaining predictors, and repeated 5-fold cross-validated ridge regression (`8` repeats) on rank-transformed variables.

## Main Result

For the 20-50 m local-context band, the rank-regression model for mean VR has cross-validated R2 `0.122 +/- 0.166`. This should be interpreted as limited but useful explanatory power, not as a predictive urban wind model. The useful outcome is the ordering of morphological signals rather than high deterministic prediction accuracy.

## Strongest Multivariate Signals for 20-50 m Mean VR

### Permutation Importance

| feature_label            |   spearman_rho |   bootstrap_spearman_ci95_low |   bootstrap_spearman_ci95_high |   partial_spearman |   ridge_standardized_coef |   permutation_r2_drop |
|:-------------------------|---------------:|------------------------------:|-------------------------------:|-------------------:|--------------------------:|----------------------:|
| sector enclosure r50m    |        -0.3956 |                       -0.5607 |                        -0.1749 |            -0.0228 |                   -0.1467 |                0.0828 |
| mean height              |        -0.3507 |                       -0.5304 |                        -0.1241 |            -0.1344 |                   -0.1388 |                0.0559 |
| combined enclosure score |        -0.3019 |                       -0.4833 |                        -0.1084 |            -0.1505 |                   -0.1051 |                0.0368 |
| height/sqrt(area)        |        -0.2083 |                       -0.3853 |                        -0.0408 |            -0.0348 |                   -0.0831 |                0.0203 |

### Partial Spearman Ranking

| feature_label             |   spearman_rho |   partial_spearman |   partial_spearman_p |   ridge_standardized_coef |   permutation_r2_drop |
|:--------------------------|---------------:|-------------------:|---------------------:|--------------------------:|----------------------:|
| combined enclosure score  |        -0.3019 |            -0.1505 |               0.1478 |                   -0.1051 |                0.0368 |
| mean height               |        -0.3507 |            -0.1344 |               0.1966 |                   -0.1388 |                0.0559 |
| local built fraction r30m |        -0.2260 |             0.1112 |               0.2861 |                   -0.0681 |                0.0170 |
| perimeter^2/area          |         0.0509 |            -0.0861 |               0.4092 |                    0.0015 |               -0.0034 |

## Interpretation

The multivariate check supports the earlier morphology conclusion with a narrower claim. The explanatory pattern is not reducible to a single footprint-size or height effect. Enclosure-related variables remain important, but they are statistically entangled because `relative_enclosure_score` combines local built fraction and sector enclosure. Therefore, the paper should write the result as a local-context morphology diagnosis: pedestrian-layer wind recovery depends on whether the 30-50 m surroundings permit pressure and momentum exchange, while individual building height or footprint area alone is insufficient.

## Claim Boundary

This is a post-processing statistical robustness analysis. It does not validate the CFD model against measurements, prove causal design effects, or replace additional S3-Sn intervention experiments.
