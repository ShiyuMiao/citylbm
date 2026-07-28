# Morphology Stage-Transition Analysis

evidence_type: newly_run + blocked

## Purpose

This addendum deepens the building-form interpretation by separating the wind response into three analysis stages: the 0-20 m facade-adjacent band, the 20-50 m local-context band, and directional reactivity within the local-context band. The analysis uses the same 101 retained central components and the archived FluidX3D-derived morphology table; no new CFD simulation is claimed.

## Stage Statistics

- Components: `101`.
- Near-facade mean VR: `0.003182`; local-context mean VR: `0.005560`; mean recovery delta: `0.002378`.
- Median recovery delta: `0.000884`; P75 recovery delta: `0.003340`; P95 recovery delta: `0.010773`.
- Stage classes: `mixed_low_speed_context`=43; `near_to_context_recovery`=26; `persistent_shelter`=23; `directionally_reactive`=9.

## Top-Versus-Bottom Recovery Contrast

- Top-recovery and bottom-recovery quartiles each contain `26` components.
- Height/sqrt(area) is lower in the top-recovery quartile than in the bottom quartile: top mean `1.606`, bottom mean `2.476`, Cliff's delta `-0.577`, Mann-Whitney p `0.0003712`.
- Absolute mean height is also lower in the top-recovery quartile: top mean `20.433` m, bottom mean `23.203` m, Cliff's delta `-0.395`.
- Elongation shows a positive but weaker contrast: top mean `3.653`, bottom mean `2.875`, Cliff's delta `0.306`.
- Spearman rho between height/sqrt(area) and recovery delta is `-0.416` with p `1.485e-05`.

## Best Sample-Internal Rule

- Best retained subgroup rule: `mean_height_m_tertile=low + elongation_ratio_tertile=high + relative_enclosure_score_tertile=high`.
- Components in subgroup: `5`; mean recovery delta `0.006537`; top-recovery share `1.000`; bottom-recovery share `0.000`.

## Paper-Safe Interpretation

The additional stage-transition analysis supports a more precise conclusion than a direct `building height causes wind speed` statement. In this campus-core sample, the 0-20 m facade-adjacent band is a largely saturated sheltered zone, whereas the 20-50 m band exposes the differences between building-form contexts. The strongest recoveries are associated with lower relative vertical scale and selected plan-continuity conditions, while high relative vertical scale and compact isolated footprints tend to remain in persistent shelter. This is a digital-twin screening result and remains blocked from being written as a causal, field-validated or universally transferable design rule.

## Outputs

- `figures/morphology_stage_transition_summary.csv`
- `figures/morphology_stage_transition_feature_contrasts.csv`
- `figures/morphology_stage_transition_rule_table.csv`
- `figures/morphology_stage_transition_by_component.csv`
- `figures/morphology_stage_transition_panel.png`
- `paper_text/morphology_stage_transition_conclusion_zh.md`
- `paper_text/morphology_stage_transition_conclusion_en.md`
- `manifests/morphology_stage_transition_claims.csv`

## Boundaries

- No new FluidX3D case was run in this addendum.
- The rule table is sample-internal and exploratory.
- The result does not replace field validation, annual comfort assessment or pollutant dispersion modelling.
