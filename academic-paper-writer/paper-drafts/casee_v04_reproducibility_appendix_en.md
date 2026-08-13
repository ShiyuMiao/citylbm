# AIJ Case E Reproducibility Appendix

Generated: 2026-08-13T13:55:51.673030+00:00

## Section Contract

Reader state before: the reader has seen the CityLBM workflow and needs enough detail to audit the Case E validation protocol.
Reader state after: the reader can identify the exact official protocol, the available evidence chain, the release boundary, and the remaining blockers.
Required moves: protocol definition, command provenance, artifact provenance, metric scope, software identity, and limitations boundary.
Evidence hooks: release gate JSON, reproducibility suite JSON, artifact index, claim matrix, plugin identity gate, and official Case E metric CSV.

## Protocol Scope

- Benchmark: AIJ Case E.
- Condition: `ac`.
- Wind direction: `N`; wind vector convention recorded as `(0, -1, 0)` in the Case E protocol.
- Geometry: official `BD_caseE.stl`, scale factor 250.
- Reference speed and height: Uref = 3.928296 m/s, zref = 15.9 m.
- Formal validation height: official z = 2 m.
- Formal probe set: 80 probes filtered from `RS_caseE.csv` by `case=ac` and `Wind_direction=N`.
- Formal sampling mode: `raw_trilinear` only.

## Current Official Metric

The current official z = 2 m Case E result is MAE = 21.111 percentage points, RMSE = 27.721 percentage points, bias = -16.409 percentage points, R2 = -2.006330, and Pearson = 0.115756 (newly_run; source: `docs/experiments/casee/results/release_gate.json`). Because the formal R2 remains negative and the release gate is closed, this is a negative-validation result, not an accuracy-success result.

## Reproducibility Chain

- Suite passed: True.
- Paper evidence gate passed: True.
- Plugin identity gate passed: True.
- Formal v0.4.0 release allowed: False.
- Recommended tag: `v0.4.0-rc94`.
- CityLBM build passed: True.
- Case A smoke regression passed: True.
- Rhino loaded new GHA: False.
- Official z = 2 m metric gate passed: False.

## Commands Used For Traceability

- `citylbm_release_build` (passed, returncode=0): `E:\citylbm_buildchain\dotnet\dotnet.exe build CityLBM/CityLBM.csproj -c Release`
- `casee_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe`
- `build_chain_audit` (passed, returncode=0): `python docs/experiments/casee/tools/build_chain_audit.py`
- `citylbm_build_hash_stability_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_build_hash_stability_gate.py`
- `citylbm_portable_toolchain_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_portable_toolchain_gate.py`
- `plugin_identity_gate` (passed, returncode=0): `python docs/experiments/casee/tools/plugin_identity_gate.py`
- `citylbm_plugin_identity_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_plugin_identity_component_gate.py`
- `citylbm_plugin_identity_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_plugin_identity_binary_gate.py`
- `citylbm_casee_postrun_audit_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_postrun_audit_component_gate.py`
- `citylbm_casee_postrun_audit_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_postrun_audit_binary_gate.py`
- `citylbm_casee_accuracy_action_plan_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_accuracy_action_plan_component_gate.py`
- `citylbm_casee_accuracy_action_plan_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_accuracy_action_plan_binary_gate.py`
- `citylbm_casee_paper_claim_card_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_paper_claim_card_component_gate.py`
- `citylbm_casee_paper_claim_card_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_paper_claim_card_binary_gate.py`
- `citylbm_casee_remediation_plan_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_remediation_plan_component_gate.py`
- `citylbm_casee_remediation_plan_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_remediation_plan_binary_gate.py`
- `citylbm_casee_official_metric_gate_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_metric_gate_component_gate.py`
- `citylbm_casee_official_metric_gate_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_metric_gate_binary_gate.py`
- `citylbm_casee_official_metrics_from_csv_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_metrics_from_csv_component_gate.py`
- `citylbm_casee_official_metrics_from_csv_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_metrics_from_csv_binary_gate.py`
- `rhino_gha_load_gate` (passed, returncode=0): `python docs/experiments/casee/tools/rhino_gha_load_gate.py`
- `citylbm_gha_install_audit` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_gha_install_audit.py`
- `casee_rhino_load_evidence_kit` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_rhino_load_evidence_kit.py`
- `rhino_gha_load_manifest_schema_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\rhino_gha_load_manifest_schema_gate.py`
- `casee_rhino_load_evidence_packet_gate` (passed, returncode=1): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_rhino_load_evidence_packet_gate.py`
- `manuscript_evidence_summary` (passed, returncode=0): `python docs/experiments/casee/tools/manuscript_evidence_summary.py`
- `vs_cpp_recovery_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\vs_cpp_recovery_gate.py`
- `vs_cpp_system_drive_space_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\vs_cpp_system_drive_space_gate.py`
- `vs_cpp_elevated_launcher_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\vs_cpp_elevated_launcher_gate.py`
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `citylbm_gpu_runtime_failfast_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_gpu_runtime_failfast_gate.py`
- `casee_dx1_readiness_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_dx1_readiness_audit.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_operational_recovery_dashboard` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_operational_recovery_dashboard.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_zcenter_rerun_consistency` (passed, returncode=0): `python docs/experiments/casee/tools/casee_zcenter_rerun_consistency.py`
- `casee_c002_longer_mean_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c002_longer_mean_audit.py`
- `casee_c003_zorigin_ablation_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c003_zorigin_ablation_audit.py`
- `casee_c004_dx3_low_cost_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c004_dx3_low_cost_audit.py`
- `casee_c005_decomposition_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c005_decomposition_audit.py`
- `casee_c008_c009_inlet_turbulence_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c008_c009_inlet_turbulence_audit.py`
- `casee_c014_residual_structure_audit` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_c014_residual_structure_audit.py`
- `casee_orphan_candidate_csv_audit` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_orphan_candidate_csv_audit.py`
- `casee_c016_residual_target_leakage_guard` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_c016_residual_target_leakage_guard.py`
- `casee_solver_run_provenance_ledger` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_solver_run_provenance_ledger.py`
- `casee_claim_support_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_claim_support_gate.py`
- `casee_research_accuracy_gap_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_research_accuracy_gap_gate.py`
- `casee_accuracy_action_plan_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_accuracy_action_plan_gate.py`
- `casee_candidate_sweep_plan` (passed, returncode=0): `python docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `casee_default_promotion_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_default_promotion_gate.py`
- `casee_wall_followup_codegen_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_wall_followup_codegen_gate.py`
- `casee_inlet_followup_codegen_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_inlet_followup_codegen_gate.py`
- `casee_c016_codegen_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_c016_codegen_gate.py`
- `casee_native_codegen_smoke_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_native_codegen_smoke_gate.py`
- `casee_runbook_codegen_preflight` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_runbook_codegen_preflight.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `citylbm_manifest_schema_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `casee_manuscript_section_pack` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `casee_paper_results_figure` (passed, returncode=0): `python docs/experiments/casee/tools/casee_paper_results_figure.py`
- `github_release_publication_gate_pre_release_assets` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate_pre_release_assets` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `artifact_index_pre_release_assets` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\artifact_index.py`
- `casee_release_asset_manifest` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `casee_release_bundle_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_release_bundle_gate.py`
- `github_release_publication_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `citylbm_software_feedback_matrix` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `casee_next_experiment_runbook` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_next_experiment_runbook.py`
- `casee_postrun_official_audit_handoff` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_postrun_official_audit_handoff.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `casee_release_asset_manifest_final` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `casee_release_bundle_gate_final` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_release_bundle_gate.py`
- `github_release_publication_gate_final` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate_final` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `casee_publication_readiness_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\casee_publication_readiness_gate.py`
- `artifact_index_final` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\artifact_index.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## Key Artifacts

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `bcb9670a5a5060187960a42fa3e1eb33e01107c89bfe39e802db066c48925c1a` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `d3d9d44b004ddbc148ab76e06b1b1660b9b28bce4335f757bba3168409971cae` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `871c5e0e84c3424fa6234e4c5778709c08e4385f22543622fa159a5c1335bc40` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `7fb9013e7f1fbeb4ecf2de1cae49918791c2f18b942efb150aa78380f887ae30` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `16e6f2d30698a60f0a9b7e9b1c4ddf0e49e24dcc49ca4de77c86584c4b293448` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `d8dffd6d1f2bf66235e675fac119adbe84c03ade83117c10d74a0a1707604f04` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `5362fe7ea6c59e815cd953fbdb988874ae97ac99f12f4582df3252065d238b3d` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `d3132d5cca8b4f97c06255ad11219f65e5a1e1aee1bae9018a22ee2ffeb49552` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `16ca8a266fcc5130108888114879358a2afa718ced67478267c05e7ead627187` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `234200411ae85f27923ca3e74f40c7dcb32673431bda7be7f8aa3301ac488aa2` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `25b2dea9bb2fd363725fb672b3c2415f8042ce6c19fcd09d3d5592a5ce0b2458` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `fe25bd13b95244124ed54bd51aa00841f427f29b5994f9b17020015566817623` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `e81ac9e872340bf988fc2267cd57cbc60a10e9d14e2afb1de47ac1c56374eb53` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `ed62262252f5eec7c40303ee575fb532e66471c043bc93db140fd8aa2ab9ceac` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `c9f046bcee7140f2f179646da344d94d5a7db73aef816079146c44c8e1a4ef35` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `3bb2e392f9215d84c3d5d7054e48bfaa83c759a8f29bbb9553ffa13e595f5963` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `35e1c7cd83c3351c26236cdeb33b2231dc6c96c130e2a94bed928dcc00085ee8` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `25d9a99a48943ad6eaa382adafeb1227e8b6750b44abbb1e7a079c4b9e61d291` |

## Claim Readiness Summary

- blocked: 1
- limitations_ready: 9
- paper_ready: 2
- weaken_claim: 2

## Manuscript-Allowed Claims

- The Case E official protocol and 80-probe filtering are reproducible from the archived inputs.
- The current CityLBM release-candidate build and tracked GHA are identifiable by hash.
- The official z = 2 m result is a transparent negative validation result.
- Near-wall, solid-corner, voxelization, and probe-sampling effects are supported as limitations diagnostics.

## Forbidden Claims

- CityLBM v0.4.0 has validated predictive accuracy for AIJ Case E.
- A diagnostic z-offset, `z_plus_half`, or `vertical_valid_above` result is the formal official z = 2 m result.
- The current evidence proves mesh independence or LES improvement.
- The current evidence proves that Rhino/Grasshopper has loaded the newly built GHA.

## Remaining Blockers

- Improve the official z = 2 m `raw_trilinear` metric until MAE is clearly below the previous near-20 pp level and R2/Pearson are positive.
- Independently verify that Rhino/Grasshopper loads the new GHA instead of an old plugin copy.
- Use the dx=1 readiness audit before any high-resolution long run; the current audit is limitations/planning evidence only.
- Complete the Visual Studio Build Tools 2022 C++ installation or continue with documented fallback build paths.

