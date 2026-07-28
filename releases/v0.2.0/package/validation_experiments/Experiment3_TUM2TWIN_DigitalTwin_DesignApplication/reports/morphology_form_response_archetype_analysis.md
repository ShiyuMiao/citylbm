# Building-Form Wind-Response Archetype Analysis

evidence_type: newly_run

## Purpose

This addendum converts the component-level morphology table into a compact building-form response typology. The aim is to support a more detailed paper conclusion about how basic building-form parameters relate to pedestrian-layer wind recovery in the TUM2TWIN campus core.

## Protocol

- Input: `figures/morphology_near_to_context_recovery_by_component.csv`
- Unit of analysis: retained central building component.
- Sample size after numeric cleaning: `101` components.
- Clustering input: footprint area, mean height, height/sqrt(area), compactness, elongation, local built fraction within 30 m, sector enclosure within 50 m, and combined enclosure score.
- Clustering method: deterministic k-means on standardized morphology variables, `k=4`.
- Response variables used only for interpretation: near-facade mean VR, 20-50 m local-context mean VR, near-to-context recovery delta, local-context P95 VR, and directional range.

## Main Typology Result

| archetype | n | mean height | H/sqrt(A) | elongation | enclosure score | mean VR 20-50 m | recovery delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| R1_A1_linear_low_relative_height_recovery | 4 | 25.73 | 1.294 | 5.34 | 0.343 | 0.0237 | 0.0080 |
| R2_A3_enclosed_linear_moderate_recovery | 19 | 22.33 | 1.117 | 6.81 | 0.674 | 0.0047 | 0.0028 |
| R3_A2_enclosed_vertical_persistent_stagnation | 49 | 21.01 | 1.729 | 3.25 | 0.519 | 0.0051 | 0.0028 |
| R4_A5_open_or_mixed_low_response | 29 | 24.53 | 3.085 | 2.14 | 0.468 | 0.0043 | 0.0007 |

## Statistical Separation

The archetype groups differ in near-to-context recovery delta with Kruskal-Wallis statistic `20.019` and p-value `0.0001682`. This is a sample-internal separation test, not an external validation test.

## Paper-Safe Interpretation

The strongest recovery archetype is `R1_A1_linear_low_relative_height_recovery`, with mean 20-50 m VR `0.0237` and recovery delta `0.0080`. The weakest recovery archetype is `R4_A5_open_or_mixed_low_response`, with mean 20-50 m VR `0.0043` and recovery delta `0.0007`.

This supports a more detailed conclusion than a single correlation table: in the screened campus core, pedestrian wind recovery is associated with combinations of relative vertical massing, elongation and local enclosure. The result does not show that an isolated geometric variable controls wind environment by itself. Instead, it shows that the digital-twin-to-CFD workflow can identify building-form response archetypes that are useful for campus-scale design screening.

## Evidence Boundary

The typology is derived from FluidX3D post-processing and building-component morphology metrics. It does not prove causal design performance, field-predictive accuracy, official comfort compliance or pollutant exposure. It should be presented as a digital-twin screening and interpretation layer.

## Outputs

- `figures/morphology_form_response_archetype_by_component.csv`
- `figures/morphology_form_response_archetype_summary.csv`
- `figures/morphology_form_response_archetype_panel.png`
