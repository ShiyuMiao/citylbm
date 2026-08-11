# Case E Reproducibility Suite

Generated: 2026-08-11T02:06:39.754585+00:00

## Verdict

- Suite passed: True
- Formal v0.4.0 allowed: False
- Recommended tag: `v0.4.0-rc60`

## Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923

## Artifact Index

- Artifact count: 328
- Lightweight release assets: 256
- Formal accuracy claim supported: False

## Build Chain

- Build chain ready: False
- VS Build Tools C++: `blocked`
- GPU runtime: `blocked`
- dx=1 readiness: `high_risk_blocked_until_dry_run`
- dx=1 memory headroom ok: False

## Commands

| step | returncode | passed |
|---|---:|---:|
| citylbm_release_build | 0 | True |
| sync_tracked_gha |  | True |
| casee_audit | 0 | True |
| build_chain_audit | 0 | True |
| sync_tracked_gha |  | True |
| stage_tracked_gha_for_grasshopper |  | True |
| plugin_identity_gate | 0 | True |
| rhino_gha_load_gate | 0 | True |
| citylbm_gha_install_audit | 0 | True |
| casee_rhino_load_evidence_kit | 0 | True |
| manuscript_evidence_summary | 0 | True |
| vs_cpp_recovery_gate | 0 | True |
| casee_official_run_preflight | 0 | True |
| casee_dx1_readiness_audit | 0 | True |
| casee_environment_recovery_runbook | 0 | True |
| casee_failure_mode_atlas | 0 | True |
| casee_zcenter_rerun_consistency | 0 | True |
| casee_c002_longer_mean_audit | 0 | True |
| casee_c003_zorigin_ablation_audit | 0 | True |
| casee_c004_dx3_low_cost_audit | 0 | True |
| casee_c005_decomposition_audit | 0 | True |
| casee_c008_c009_inlet_turbulence_audit | 0 | True |
| casee_c014_residual_structure_audit | 0 | True |
| casee_c016_residual_target_leakage_guard | 0 | True |
| casee_solver_run_provenance_ledger | 0 | True |
| casee_claim_support_gate | 0 | True |
| casee_candidate_sweep_plan | 0 | True |
| casee_default_policy_gate | 0 | True |
| citylbm_paper_results_packet | 0 | True |
| citylbm_manifest_output_gate | 0 | True |
| citylbm_manifest_schema_gate | 0 | True |
| casee_manuscript_results_table | 0 | True |
| casee_manuscript_section_pack | 0 | True |
| casee_paper_results_figure | 0 | True |
| artifact_index_pre_release_assets | 0 | True |
| casee_release_asset_manifest | 0 | True |
| citylbm_software_feedback_matrix | 0 | True |
| artifact_index_pre_appendix | 0 | True |
| paper_appendix_generator | 0 | True |
| casee_blocker_remediation_plan | 0 | True |
| casee_next_experiment_runbook | 0 | True |
| artifact_index | 0 | True |
| casee_release_asset_manifest_final | 0 | True |
| paper_evidence_gate | 0 | True |
| casee_publication_readiness_gate | 0 | True |
| artifact_index_final | 0 | True |
| formal_release_gate_expected_block | 1 | True |

## Boundary

This suite proves that the current rc evidence chain is reproducible and claim-safe. It intentionally treats the formal release gate as blocked while official z=2 m R2 remains negative.
