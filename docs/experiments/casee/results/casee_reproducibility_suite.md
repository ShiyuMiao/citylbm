# Case E Reproducibility Suite

Generated: 2026-08-01T12:53:31.926242+00:00

## Verdict

- Suite passed: True
- Formal v0.4.0 allowed: False
- Recommended tag: `v0.4.0-rc18`

## Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923

## Artifact Index

- Artifact count: 124
- Lightweight release assets: 92
- Formal accuracy claim supported: False

## Commands

| step | returncode | passed |
|---|---:|---:|
| citylbm_release_build | 0 | True |
| sync_tracked_gha |  | True |
| casee_audit | 0 | True |
| manuscript_evidence_summary | 0 | True |
| plugin_identity_gate | 0 | True |
| artifact_index_pre_appendix | 0 | True |
| paper_appendix_generator | 0 | True |
| casee_blocker_remediation_plan | 0 | True |
| casee_next_experiment_runbook | 0 | True |
| artifact_index | 0 | True |
| paper_evidence_gate | 0 | True |
| formal_release_gate_expected_block | 1 | True |

## Boundary

This suite proves that the current rc evidence chain is reproducible and claim-safe. It intentionally treats the formal release gate as blocked while official z=2 m R2 remains negative.
