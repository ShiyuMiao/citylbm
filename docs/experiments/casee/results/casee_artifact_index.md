# Case E Artifact Index

Generated: 2026-08-01T12:53:31.651199+00:00

## Summary

- Artifact count: 124
- Total size bytes: 19711323
- Lightweight release assets: 92
- Optional log assets: 7
- Hash-only external references: 2

## Release Asset Roles

- external_reference_hash_only: 2
- hash_record_only: 23
- lightweight_release_asset: 92
- optional_log_asset: 7

## Claim Readiness

- blocked_followup_plan: 4
- blocked_followup_runbook: 4
- blocked_formal_release_gate: 1
- limitations_ready_diagnostic: 26
- limitations_ready_negative_validation: 2
- paper_ready_protocol_input: 6
- paper_ready_reproducibility: 68
- paper_ready_reproducibility_appendix: 4
- paper_ready_software_identity: 1
- paper_ready_traceability: 8

## Key Artifacts

| path | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `3702792b59e2251f4df12cb302d002d7dcef5f1baf1b1acc7ae20b12db621660` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | lightweight_release_asset | paper_ready_reproducibility_appendix | `00fb499e0cef820f2d70eb3590433d03479db49df05f5c4db43599b83daac87d` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | lightweight_release_asset | paper_ready_reproducibility_appendix | `649e8c0e899de168db76ce127c8957900d057c468ed12a88ee8a110244e4bebe` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `def89b6752b20e878719a39ce2d866159aca410141ed6deed06245988bbb68b1` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_next_experiment_runbook.json` | lightweight_release_asset | blocked_followup_runbook | `d44f61e496fc90d881cc2b4da473491eef70c2d08be30c7aceb30fc43b9d5c5c` |
| `docs/experiments/casee/results/casee_next_experiment_runbook.md` | lightweight_release_asset | blocked_followup_runbook | `fae158eabc7038a0a384f4e99c184d1f70ef2edcbcbcad80199aef227c383016` |
| `docs/experiments/casee/results/casee_paper_appendix_manifest.json` | lightweight_release_asset | paper_ready_reproducibility_appendix | `45fe1e5ce94b917f4165104accfd9941dabee0397a116c5dc8a8e8f017ac757e` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `17f532bb5826a313f7dd6ee09ea87ffc3bfb7a31fe6acc5c8ba6702e9998c863` |
| `docs/experiments/casee/results/casee_remaining_blockers.json` | lightweight_release_asset | blocked_followup_plan | `e19d44138428404c4958ec0ddce62b99fe56ea12a64c83b702794ff1f84decb9` |
| `docs/experiments/casee/results/casee_remaining_blockers.md` | lightweight_release_asset | blocked_followup_plan | `3433cdf85259e3e0c6a873656878101bc96f9b7ea5aa684812e210eb21443824` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | lightweight_release_asset | paper_ready_traceability | `54ab712e995028fe2619974d1ba37308badbe5e0ee356a58f7453d39ee4963fc` |
| `docs/experiments/casee/results/casee_validation_report.md` | lightweight_release_asset | limitations_ready_negative_validation | `c8a3ccdf5d33f9a4df166757d9320c378fc886390742c737688620dd7ee080c4` |
| `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` | lightweight_release_asset | limitations_ready_diagnostic | `58961ab3036c519f6d5665f17239c47007f2b2f34d86dc84aca139eb4bcc1a60` |
| `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv` | lightweight_release_asset | limitations_ready_diagnostic | `dcf90ab869ee70f4d01af830b6d28653632e0f1fd2e013b9ae0f74d1a1f3c993` |
| `docs/experiments/casee/results/plugin_identity_gate.json` | lightweight_release_asset | paper_ready_traceability | `5cbecf1e3d6f373ae56193f9cfa6ac1aecdc83c955b19662eb60ff9e158ff701` |
| `docs/experiments/casee/results/release_gate.json` | lightweight_release_asset | blocked_formal_release_gate | `5aebfc3c1ac6cca3759bbec67ef2d7aa0cc2340dd1b12a3b3632a62d73bf14a6` |
| `docs/releases/v0.4.0-rc18.md` | lightweight_release_asset | paper_ready_reproducibility | `7248ebfb69d8063d66c52244a52364a48c212f7b040e22ee40812b323daaeddd` |

## Boundary

This index supports reproducibility and manuscript traceability. It does not upgrade the formal AIJ Case E official z=2 m metric, which remains a negative validation result until the release gate passes.
