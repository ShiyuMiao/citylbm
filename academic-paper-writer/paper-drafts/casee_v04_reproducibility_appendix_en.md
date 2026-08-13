# AIJ Case E Reproducibility Appendix

Generated: 2026-08-13T14:14:49.103725+00:00

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
- Recommended tag: `v0.4.0-rc95`.
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
- `citylbm_casee_official_residual_diagnostics_component_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_residual_diagnostics_component_gate.py`
- `citylbm_casee_official_residual_diagnostics_binary_gate` (passed, returncode=0): `python E:\citylbm_rc89_work\docs\experiments\casee\tools\citylbm_casee_official_residual_diagnostics_binary_gate.py`
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `5dd119b4c86fcc2fb36ef5e1bbc8f09b3fc403ce42bcf52542588bca7b997af0` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `4b91589919d81620d7be6fce7aaba7b3ba94dbf441f168aaf135ec9c75af6961` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `ea3d7baf2f84ee202f51ecab69e72698acdbc78249446b8601649d7667fe0ebb` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `07abbc3c9c27ff9db2147cd61bc8c029cde290c2421373d591d07491df25b0fb` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `786c9d7d049556fba6547ea3585dead976ad3812ea7817b7e66a70017410b515` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `afee8d437338f20baeab445fe48a3627b0174f2db6a05deffb70c07142f07216` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `8a654b1f3f332dab72c2d6e1bf4be41b5267c7c2d9e372ac51a4b9e743b635b0` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `1c81d18b43ece28ef765413dfdfa89b1523f2c7f0e94af2e8b3788004bb96986` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `cfa18ce137608efb55c2012de691ab3e64fcef2561838f1ec7b6460f4220483b` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `533f3c40cde78c7a9412773e7486c8a1be800b823c49474c8b599126f13a8a6b` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `b61addf7d8b7b6c6fb7b93e37efda9695947b91577fdb5351117743d348f9229` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `25bf7874019389bcb81d4bc8eeec9fa5deca6a5a0c7207aac33c21d30e1bbc9b` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `d5e99b5eedf99200822b793ea49ca2f99a417df6363701423c69c77ebe13f4ae` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `42cf2a5c798e967647f047d2fe24ca0abb2ac9434bec149b0a768fce39f897ea` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `4b08e9ca9b0c7a692839d118a3971e7e0324242669648956b62fb0149266695b` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `00f783e64504bd782684bb7ace4307e3dadb772170959cb5bc4ec1c11d4952b4` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `c80eef5a35754722b2a9d4501c237e1aaab4b0db88b0b27a4227921702d65628` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `6fa35ccf0ed76bc143b90d2063252def56839a83a7e613e14d3b3d8245316daa` |

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

