# Experiment 3 Submission Debt Register

evidence_type: newly_run + preexisting_artifact + blocked

This register scans the paper-facing Markdown layer for explicit placeholders and consolidates the remaining claim-upgrade debts. It does not add CFD results; it prevents unresolved author-input or external-validation requirements from being accidentally written as completed evidence.

## Summary

- Debt rows: `7`
- Status counts: `{'open_author_input': 1, 'blocked': 4, 'open_conditional': 1, 'closed_or_not_detected': 1}`
- Debt-type counts: `{'author_input_needed': 1, 'blocked_external_validation': 2, 'blocked_missing_simulation': 1, 'conditional_method_claim': 1, 'blocked_missing_metric': 1, 'citation_and_figure_hygiene': 1}`
- Placeholder source counts: `{'AUTHOR_INPUT_NEEDED': 6, 'RESULT_NEEDED': 4}`

## Register

| debt_id | debt_type | status | affected_claim | required_evidence_to_close | current_safe_action |
|---|---|---|---|---|---|
| SDR1 | author_input_needed | open_author_input | Target journal, final reference style, final title emphasis and author-administrative statements. | Author decision on target journal, citation format, paper title wording, funding, competing interests, acknowledgements, CRediT roles and final license wording. | Keep as author-input placeholders; do not invent venue requirements or administrative statements. |
| SDR2 | blocked_external_validation | blocked | Field-validated predictive accuracy and measured wind-environment validation. | On-site wind measurements or wind-tunnel data with documented sensor/scale setup, matched boundary conditions, comparison metrics and uncertainty. | State as missing validation; keep current results as FluidX3D-native screening and morphology interpretation. |
| SDR3 | blocked_external_validation | blocked | Lawson, NEN 8100 or AIJ annual comfort/safety compliance. | Calibrated measured or official wind rose, velocity-threshold exceedance calculation, activity-class thresholds and documented aggregation period. | Use VR, stagnation and climate-proxy sensitivity only; do not label areas as compliant/non-compliant. |
| SDR4 | blocked_missing_simulation | blocked | Pollutant concentration, exposure, scalar hot spots and C/C0 predictions. | FluidX3D or equivalent scalar-transport setup, source terms, boundary conditions, timestep/sample records and postprocessed C/C0 fields. | Keep pollutant metrics as templates only. |
| SDR5 | conditional_method_claim | open_conditional | CityLBM-Grasshopper plugin end-to-end execution. | Grasshopper file, CityLBM plugin run screenshot/log, input/output artifacts and generated wind/geometry output trace. | Frame the current experiment as FluidX3D-native simulation with a CityLBM-compatible geometry package. |
| SDR6 | blocked_missing_metric | blocked | 3DGS-to-collision-boundary transfer error. | Independent 3DGS-derived collision extraction, CityGML/LoD2/LoD3 ground truth, IoU/Chamfer/Hausdorff/roof-wall error computation and solid-mask agreement. | Keep GCBTE as a proposed metric and future validation path. |
| SDR7 | citation_and_figure_hygiene | closed_or_not_detected | Unresolved citation, figure or table placeholders in paper-facing Markdown. | Verified references or figure/table source artifacts if new placeholders are introduced. | Current scan found no REF_NEEDED, FIGURE_NEEDED or TABLE_NEEDED placeholders in the scanned paper-facing Markdown. |

## Paper-Safe Closeout

Experiment 3 is ready for a journal-neutral SCI section when it is framed as FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation. The remaining open items are not packaging failures. They are either author-input fields or claim-upgrade evidence that would be required only if the manuscript wants to claim field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE, CityLBM-Grasshopper end-to-end execution or successful optimization.
