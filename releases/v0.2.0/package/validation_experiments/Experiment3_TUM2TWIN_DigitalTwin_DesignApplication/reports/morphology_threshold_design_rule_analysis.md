# Morphology Threshold Design-Rule Analysis

evidence_type: newly_run

## Purpose

This addendum converts the existing component-level morphology and FluidX3D wind-response data into a design-rule screening layer. It does not run new CFD fields. Instead, it compares the facade-adjacent band (`0-20 m`) with the local-context band (`20-50 m`) for the same 101 retained central building components.

## Protocol

- Input: `figures/basic_morphology_per_component_near_facade_0_20m.csv`
- Input: `figures/basic_morphology_per_component_local_context_20_50m.csv`
- Components: `101`
- Response: `context_recovery_delta_vr = mean_VR_20_50m - mean_VR_0_20m`
- Rule search: single, two-part, and three-part tertile conditions using basic morphology variables only.
- Evidence boundary: the rules are diagnostic screening rules, not causal design laws or externally validated thresholds.

## Key Results

- Mean near-facade VR: `0.0032`.
- Mean local-context VR: `0.0056`.
- Mean near-to-context recovery delta: `0.0024`.
- Top recovery quartile threshold: `delta VR >= 0.0033`.
- Bottom recovery quartile threshold: `delta VR <= 0.0002`.
- Strongest negative monotonic descriptor of recovery delta: `height/sqrt(area)` with Spearman rho `-0.416`.
- Strongest positive monotonic descriptor of recovery delta: `footprint area` with Spearman rho `0.304`.
- Best simple rule: `mean_height_m=low_tertile + elongation_ratio=high_tertile`; `n=7`, mean recovery delta `0.0057`, top-recovery share `0.857`.

## Top-vs-Bottom Recovery Interpretation

The top recovery quartile has mean local-context VR `0.0123` and mean recovery delta `0.0073`. The bottom quartile has mean local-context VR `0.0024` and mean recovery delta `-0.0003`. This confirms that the 20-50 m band is the more informative layer for morphology-sensitive screening: the 0-20 m band is uniformly sheltered, while the outer local-context band reveals where flow begins to recover.

## Paper-Safe Conclusion

The new result supports a more design-oriented conclusion: in this campus block, wind recovery is not explained by a single building-size variable or by opening area alone. The strongest monotonic signal is the negative association with height normalized by footprint scale, while the best small subgroup combines lower mean height with higher elongation. This suggests that pedestrian-layer recovery depends on local exposure, vertical massing, and plan continuity rather than on a single footprint metric. The rule is useful for digital-twin screening, but it remains sample-internal because the thresholds are derived from one modeled TUM2TWIN case and have not been field-validated.

## Output Artifacts

- `figures/morphology_near_to_context_recovery_by_component.csv`
- `figures/morphology_recovery_top_bottom_contrast.csv`
- `figures/morphology_threshold_rule_screening.csv`
- `figures/morphology_threshold_recovery_rule_summary.png`
