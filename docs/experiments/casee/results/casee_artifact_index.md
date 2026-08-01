# Case E Artifact Index

Generated: 2026-08-01T13:02:15.846313+00:00

## Summary

- Artifact count: 127
- Total size bytes: 19732495
- Lightweight release assets: 95
- Optional log assets: 7
- Hash-only external references: 2

## Release Asset Roles

- external_reference_hash_only: 2
- hash_record_only: 23
- lightweight_release_asset: 95
- optional_log_asset: 7

## Claim Readiness

- blocked_followup_plan: 4
- blocked_followup_runbook: 4
- blocked_formal_release_gate: 1
- blocked_manual_rhino_load: 3
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `c9ea0ec3411cf21ef1e9497dfbed1ad256ea91aa334bcf1431bdd57a87f15708` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md` | lightweight_release_asset | paper_ready_reproducibility_appendix | `25fa349b2e5f379715e923de2a6fb49656529adeea3557de118e633e0bcfcd48` |
| `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md` | lightweight_release_asset | paper_ready_reproducibility_appendix | `b26f63cae4885ec0b47131051e31d8b500ed3a60e5f78e3fbb9f5ad0d5aeea16` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `ad79da932e40093af5177de3790e4ccd5e7b2515391364bd484cd1fe3e9d536f` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_next_experiment_runbook.json` | lightweight_release_asset | blocked_followup_runbook | `7b4e21d049d2c6d72b23760754d3d928a4985c421142d32c4a5d845b06940772` |
| `docs/experiments/casee/results/casee_next_experiment_runbook.md` | lightweight_release_asset | blocked_followup_runbook | `252e3de6ce848c76975492abdba25a9558aca2b0cb3c12d9a89b395ddb3f5113` |
| `docs/experiments/casee/results/casee_paper_appendix_manifest.json` | lightweight_release_asset | paper_ready_reproducibility_appendix | `5727a8ac8ae7e89363193ebaa6f1353489958444e32439b87b0edef18e8fbded` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `a0b38a10c62190c90dfdba2f26e24aa7f50850a0c363e76dc5b97e900a526ed7` |
| `docs/experiments/casee/results/casee_remaining_blockers.json` | lightweight_release_asset | blocked_followup_plan | `2a7e99f1c32b18de858dc5a801e480dff50dc94d8fa5cac81e1734d5c45074b3` |
| `docs/experiments/casee/results/casee_remaining_blockers.md` | lightweight_release_asset | blocked_followup_plan | `e6d79b1dacf18d54bccc22bfb5e7645b2773d450b8046b681bbf6d17380b580a` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | lightweight_release_asset | paper_ready_traceability | `6a2195f9c944ec3ddf2f17851e10b927e1bcdef84ded5258561b2bcceb1fe735` |
| `docs/experiments/casee/results/casee_validation_report.md` | lightweight_release_asset | limitations_ready_negative_validation | `207a0fe78420ef6e067e4de76620e6d837741bb6bd2af077acfbc14874694bc5` |
| `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` | lightweight_release_asset | limitations_ready_diagnostic | `58961ab3036c519f6d5665f17239c47007f2b2f34d86dc84aca139eb4bcc1a60` |
| `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv` | lightweight_release_asset | limitations_ready_diagnostic | `dcf90ab869ee70f4d01af830b6d28653632e0f1fd2e013b9ae0f74d1a1f3c993` |
| `docs/experiments/casee/results/plugin_identity_gate.json` | lightweight_release_asset | paper_ready_traceability | `e68f1c3a66aff3fc5dc361a6f6b978d2deac36250964b8cdff5e09d36b95b92c` |
| `docs/experiments/casee/results/release_gate.json` | lightweight_release_asset | blocked_formal_release_gate | `5f91edb3baa8c56ee677a1def8eb9cea660f4e3a4230dd60c4789cfbc4043282` |
| `docs/experiments/casee/results/rhino_gha_load_gate.json` | lightweight_release_asset | blocked_manual_rhino_load | `2d9fb6c94b6a3d3f70201c50c108eaabbdf354612ea6cd8063cedf50c53532ed` |
| `docs/experiments/casee/results/rhino_gha_load_gate.md` | lightweight_release_asset | blocked_manual_rhino_load | `2ecabedae64105b4c50a2c760c971c55b9c2e489978e1c4dc0294f0feddb56f9` |
| `docs/releases/v0.4.0-rc19.md` | lightweight_release_asset | paper_ready_reproducibility | `97921252a31ee5498a9b4b3b5e394d938be7263541173fd8a46b42a001d6f60c` |

## Boundary

This index supports reproducibility and manuscript traceability. It does not upgrade the formal AIJ Case E official z=2 m metric, which remains a negative validation result until the release gate passes.
