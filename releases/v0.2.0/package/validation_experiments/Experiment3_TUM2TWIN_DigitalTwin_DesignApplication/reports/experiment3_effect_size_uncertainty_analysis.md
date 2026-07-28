# Experiment 3 Effect-Size and Uncertainty Analysis

evidence_type: newly_run + blocked

## Protocol

This addendum recomputes paper-facing effect sizes from archived Experiment 3 CSV outputs. It does not run a new CFD solver case. The S0 baseline uncertainty uses the `individual_sample` rows of `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`, giving 8 wind directions x 3 post-spin-up samples = 24 direction-sample units per height. Vertical recovery uses paired direction-sample differences between z~40 m and z~2 m. S1/S2 design sensitivity uses the 8-direction min-max range at z~2 m from `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`. Morphology recovery uses the 101 retained building components in `figures/morphology_near_to_context_recovery_by_component.csv`.

## Key Effect Sizes

- S0 z~2 m mean VR: `0.076338` with bootstrap 95% CI `0.075529` to `0.077110`.
- S0 z~2 m VR<0.2 ratio: `0.929184` with bootstrap 95% CI `0.926430` to `0.932069`.
- Paired z~40 m minus z~2 m mean VR: `0.972170` with bootstrap 95% CI `0.967413` to `0.977473`.
- S1 z~2 m global mean-VR delta: `-0.000213` with 8-direction range `-0.000264` to `-0.000148`.
- S2 z~2 m global mean-VR delta: `-0.000466` with 8-direction range `-0.000532` to `-0.000336`.
- Mean near-to-context morphology recovery delta: `0.002378` with bootstrap 95% CI `0.001742` to `0.003062`.

## Paper-Safe Interpretation

The added uncertainty layer strengthens three conservative conclusions. First, the pedestrian-height low-speed state is not a single-sample artifact: the z~2 m mean VR remains low and the VR<0.2 ratio remains high across direction-sample bootstrap resampling. Second, the vertical contrast is large and consistently positive for mean VR, confirming that above-roof flow recovery cannot be substituted for pedestrian-layer assessment. Third, S1/S2 remain near-null or negative in global z~2 m metrics across the eight tested directions, so their role is negative design-sensitivity evidence rather than successful optimization.

For morphology, the 20-50 m local-context band shows a small positive recovery relative to the 0-20 m near-facade band, and the top-versus-bottom recovery quartile contrast is descriptive evidence for sample-internal design screening. These results remain bounded: they are not field measurement uncertainty, not grid-convergence proof, not annual comfort/safety exceedance probabilities, and not causal design thresholds.

## Output Artifacts

- `figures/experiment3_effect_size_uncertainty_summary.csv`
- `figures/experiment3_effect_size_uncertainty_forest.png`
- `reports/experiment3_effect_size_uncertainty_analysis.md`
- `paper_text/experiment3_effect_size_uncertainty_results_zh.md`
- `manifests/experiment3_effect_size_uncertainty_claims.csv`
