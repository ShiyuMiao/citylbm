# Case E Paper Evidence Gate

Generated: 2026-08-11T00:23:39.101374+00:00

## Verdict

- Paper evidence gate passed: True
- Formal v0.4.0 release allowed: False
- Recommended tag: `v0.4.0-rc49`

## Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923
- Negative validation status: True

## Claim Matrix

- Claims: 14
- Readiness counts: `{'paper_ready': 2, 'limitations_ready': 9, 'weaken_claim': 2, 'blocked': 1}`
- Blocked release claim present: True
- Negative validation claim present: True
- Recommended tag present: True
- No overstated paper-ready claims: True

## Draft Scan

- Checked files: 6
- Checked nonblank lines: 324
- Draft claim boundary passed: True

## Artifact Index

- Artifact index found: True
- Artifact count: 287
- Lightweight release assets: 215
- Required artifacts present: True
- Formal accuracy claim supported by index: False

## Rhino/GHA Load Gate

- Gate found: True
- Rhino loaded new GHA: False
- Claim readiness: `blocked_manual_rhino_load`
- Claim boundary safe: True

## Build Chain Manifest

- Manifest found: True
- Build chain ready: False
- Claim readiness: `blocked_build_chain_diagnostic`
- VS Build Tools C++: `blocked`
- MinGW/g++ fallback: `ready`
- Native source compile ready: True
- Native source compile path: `mingw_gpp_fallback`
- .NET SDK: `ready`
- FluidX3D: `ready_for_existing_binary`
- GPU runtime: `blocked`
- UAC/1602 blocker recorded: True
- Claim boundary safe: True

## Official Run Preflight

- Preflight found: True
- Official follow-up run allowed: False
- Formal release allowed: False
- Claim readiness: `blocked_official_followup_preflight`
- Claim boundary safe: True

## dx=1 Readiness Audit

- Audit found: True
- Audit passed: True
- dx=1 readiness: `high_risk_blocked_until_dry_run`
- Memory headroom ok: False
- Run started: False
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Environment Recovery Runbook

- Recovery runbook found: True
- Formal release allowed: False
- Claim readiness: `blocked_environment_recovery_runbook`
- Recovery steps: 7
- Claim boundary safe: True

## Failure-Mode Atlas

- Atlas found: True
- Failure modes: 7
- Claim readiness: `limitations_ready_failure_mode_atlas`
- Claim boundary safe: True

## z-center Rerun Consistency

- Rerun found: True
- Status: `passed_reproduced_failed_metric`
- 48000-step log complete: True
- CSV SHA256 equal: True
- R2: -2.006330362229977
- Claim readiness: `paper_ready_reproducibility; blocked formal accuracy release`
- Claim boundary safe: True

## C002 Longer Time-Mean Audit

- Audit found: True
- Status: `completed_no_improvement`
- 96000-step log complete: True
- Pass condition met: False
- R2: -2.1851358653077058
- R2 delta vs baseline: -0.1788055030777289
- Claim readiness: `limitations_ready_candidate_result; blocked formal accuracy release`
- Claim boundary safe: True

## C003 Z-Origin Ablation Audit

- Audit found: True
- Status: `completed_ablation_supports_zorigin_sensitivity`
- 48000-step log complete: True
- Pass condition met: True
- Consistent with preexisting no-zcenter artifact: True
- R2: -2.221378753276796
- R2 delta vs z-center baseline: -0.21504839104681928
- Claim readiness: `limitations_ready_zorigin_ablation; blocked formal accuracy release`
- Claim boundary safe: True

## C004 dx=3 Low-Cost Direction Check

- Audit found: True
- Status: `completed_low_cost_positive_correlation`
- 48000-step log complete: True
- Manifest protocol ok: True
- Pearson positive: True
- Pass condition met: True
- R2: -2.5282993702661267
- R2 delta vs z-center baseline: -0.5219690080361499
- Claim readiness: `limitations_ready_dx3_low_cost_regression; blocked formal accuracy release`
- Claim boundary safe: True

## Candidate Sweep Plan

- Plan found: True
- Plan generated: True
- Candidate count: 9
- Executable-now count: 0
- Claim readiness: `paper_ready_followup_plan; blocked formal accuracy release`
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Default Policy Gate

- Gate found: True
- Default policy gate passed: True
- Checks: 26
- Claim readiness: `paper_ready_default_policy_boundary`
- Claim boundary safe: True

## Cross-Experiment Paper Results Packet

- Packet found: True
- Packet passed: True
- Result rows: 26
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False
- Claim boundary safe: True

## Manifest Output Gate

- Gate found: True
- Gate passed: True
- Checks: 17
- Claim readiness: `paper_ready_manifest_traceability`
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Manifest Schema Gate

- Gate found: True
- Gate passed: True
- Contract version: `casee_manifest_contract_v1`
- Checks: 11
- Claim readiness: `paper_ready_manifest_schema_boundary`
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Manuscript Results Table

- Table found: True
- Table passed: True
- Rows: 6
- Claim readiness: `paper_ready_manuscript_results_table`
- Diagnostic rows not formal: True
- Formal R2 negative: True
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Manuscript Section Pack

- Pack found: True
- Pack passed: True
- Checks: 9
- Claim readiness: `paper_ready_negative_validation_and_limitations`
- Formal release allowed: False
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Paper Results Figure

- Figure found: True
- Figure gate passed: True
- Claim readiness: `paper_ready_figure_for_negative_validation_and_limitations`
- Export bundle complete: True
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Software Feedback Matrix

- Matrix found: True
- Matrix passed: True
- Feedback rows: 28
- All source paths exist: True
- No forbidden default promotion: True
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False
- Claim boundary safe: True

No forbidden success-claim violations were found outside negated or forbidden-claim sections.
