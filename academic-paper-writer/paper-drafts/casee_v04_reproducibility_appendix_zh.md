# AIJ Case E 可复现性附录

生成时间: 2026-08-13T05:32:35.046018+00:00

## 章节契约

读者进入本附录前应已了解 CityLBM 的总体工作流；读完后应能够审计 Case E 的官方协议、命令来源、产物哈希、版本边界和剩余阻塞项。
本附录只使用已有门控与产物索引，不引入新的 CFD 精度结论。

## 协议范围

- 基准案例: AIJ Case E。
- 工况: `ac`。
- 风向: `N`；风向量约定在协议中记录为 `(0, -1, 0)`。
- 几何: 官方 `BD_caseE.stl`，比例因子 250。
- 参考风速和高度: Uref = 3.928296 m/s，zref = 15.9 m。
- 正式验证高度: 官方 z = 2 m。
- 正式测点: `RS_caseE.csv` 中 `case=ac` 且 `Wind_direction=N` 的 80 个测点。
- 正式采样: 仅 `raw_trilinear`。

## 当前官方指标

当前 official z = 2 m Case E 结果为 MAE = 21.111 个百分点，RMSE = 27.721 个百分点，bias = -16.409 个百分点，R2 = -2.006330，Pearson = 0.115756 （newly_run；来源: `docs/experiments/casee/results/release_gate.json`）。由于正式 R2 仍为负且 release gate 关闭，该结果只能写成负向验证或局限性结果，不能写成精度验证成功。

## 可复现链

- 一键复现套件通过: True。
- 论文证据门控通过: True。
- 插件身份门控通过: True。
- 正式 v0.4.0 是否允许发布: False。
- 推荐标签: `v0.4.0-rc77`。
- CityLBM 构建通过: True。
- Case A smoke regression 通过: True。
- Rhino 是否已加载新 GHA: False。
- official z = 2 m 指标门槛是否通过: False。

## 可追溯命令

- `casee_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe`
- `build_chain_audit` (passed, returncode=0): `python docs/experiments/casee/tools/build_chain_audit.py`
- `citylbm_build_hash_stability_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_build_hash_stability_gate.py`
- `citylbm_portable_toolchain_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_portable_toolchain_gate.py`
- `plugin_identity_gate` (passed, returncode=0): `python docs/experiments/casee/tools/plugin_identity_gate.py`
- `citylbm_plugin_identity_component_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_plugin_identity_component_gate.py`
- `citylbm_plugin_identity_binary_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_plugin_identity_binary_gate.py`
- `rhino_gha_load_gate` (passed, returncode=0): `python docs/experiments/casee/tools/rhino_gha_load_gate.py`
- `citylbm_gha_install_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_gha_install_audit.py`
- `casee_rhino_load_evidence_kit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_rhino_load_evidence_kit.py`
- `rhino_gha_load_manifest_schema_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\rhino_gha_load_manifest_schema_gate.py`
- `manuscript_evidence_summary` (passed, returncode=0): `python docs/experiments/casee/tools/manuscript_evidence_summary.py`
- `vs_cpp_recovery_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\vs_cpp_recovery_gate.py`
- `vs_cpp_system_drive_space_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\vs_cpp_system_drive_space_gate.py`
- `vs_cpp_elevated_launcher_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\vs_cpp_elevated_launcher_gate.py`
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `citylbm_gpu_runtime_failfast_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_gpu_runtime_failfast_gate.py`
- `casee_dx1_readiness_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_dx1_readiness_audit.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_operational_recovery_dashboard` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_operational_recovery_dashboard.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_zcenter_rerun_consistency` (passed, returncode=0): `python docs/experiments/casee/tools/casee_zcenter_rerun_consistency.py`
- `casee_c002_longer_mean_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c002_longer_mean_audit.py`
- `casee_c003_zorigin_ablation_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c003_zorigin_ablation_audit.py`
- `casee_c004_dx3_low_cost_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c004_dx3_low_cost_audit.py`
- `casee_c005_decomposition_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c005_decomposition_audit.py`
- `casee_c008_c009_inlet_turbulence_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c008_c009_inlet_turbulence_audit.py`
- `casee_c014_residual_structure_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c014_residual_structure_audit.py`
- `casee_orphan_candidate_csv_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_orphan_candidate_csv_audit.py`
- `casee_c016_residual_target_leakage_guard` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c016_residual_target_leakage_guard.py`
- `casee_solver_run_provenance_ledger` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_solver_run_provenance_ledger.py`
- `casee_claim_support_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_claim_support_gate.py`
- `casee_candidate_sweep_plan` (passed, returncode=0): `python docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `citylbm_manifest_schema_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `casee_manuscript_section_pack` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `casee_paper_results_figure` (passed, returncode=0): `python docs/experiments/casee/tools/casee_paper_results_figure.py`
- `github_release_publication_gate_pre_release_assets` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate_pre_release_assets` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `artifact_index_pre_release_assets` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\artifact_index.py`
- `casee_release_asset_manifest` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `casee_release_bundle_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_bundle_gate.py`
- `github_release_publication_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `citylbm_software_feedback_matrix` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `casee_next_experiment_runbook` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_next_experiment_runbook.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `casee_release_asset_manifest_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `casee_release_bundle_gate_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_bundle_gate.py`
- `github_release_publication_gate_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\github_release_publication_gate.py`
- `casee_workspace_hygiene_gate_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_workspace_hygiene_gate.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `casee_publication_readiness_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_publication_readiness_gate.py`
- `artifact_index_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\artifact_index.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## 关键产物

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `504acb274423b6ac48fb81262e0e004558cd59143b34965ded932595560dfa39` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `5fc78d1fa20d56737f10f24e6269d5528b5f4c18cbfa70cc2f42661fbfe45de0` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `2a152dc87b7dff480822d5e273eab8b34ceb5438e576ffeff1554c3e2858aba6` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `2f071cf1fddf8ad446cef737753ef0e5480ee8870b10a13587d713f3861d70e7` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `99bfc6175c8cf034f04e9e7f0d3de5e6b95e2bbcdfa8987c1db8b6be8a7f1946` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `6b21318396a838c1ee111ff4c2b46a85b0bcf667d9318267fc4e8739059267b2` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `18e3fd42772d8726c72ea15340618cecac81ea18353ed35a315151bbe3673e67` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `dedb157a2b76c4b579df78e041c08d52f391086f1036d54fa7f494c518d4c0b6` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `2fde7ce62a5edce1350504e1890b658d028b33cd98080a00dd46eca0028d7672` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `5904d25c360ce6e7a475a94afc67ea3e56b92cbc6dbaaeabbc61970b7e3b0678` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `39eabbe901fa49ca4c9d5db23471dd14e489c07f30cad4d7d64edfa708cb78f3` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `c2c30d5256398bfacb27757ec61609be3088fdedbcc16928a0f02acce6c34447` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `14fdce2695717f45c50757cf16d6f01505031ae8892171615ee84dd8062bda50` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `52d7bee554d9444e648183ef79a9237268c6600a25a350495750767307c0279b` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `7448a73e98e3d869a5b37f1bc5d9dcfdf2caa87508b6108d79185067343831ba` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `40b2175a815623bb389569b59e8564353bb62dbb17c4d3a59a0d5ea4aae80cba` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `5e577e285224e92db6deb0a4e89dfdaf3f4eb881376afd819aefabd1d61d8bb4` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `906407ae034bdd1ca465b417b766667af2ce768bf207e6c9fc4635eebaf0653a` |

## 论文章节可用性

- blocked: 1
- limitations_ready: 9
- paper_ready: 2
- weaken_claim: 2

## 允许写入论文的表述

- Case E 官方协议和 80 测点过滤过程可由归档输入复现。
- 当前 CityLBM release-candidate 构建和跟踪版 GHA 可由哈希识别。
- official z = 2 m 结果是透明的负向验证结果。
- near-wall、solid-corner、voxelization 和 probe-sampling 影响可作为局限性诊断讨论。

## 禁止写入论文的表述

- CityLBM v0.4.0 已完成 AIJ Case E 预测精度验证。
- 诊断性 z-offset、`z_plus_half` 或 `vertical_valid_above` 是正式 official z = 2 m 结果。
- 当前证据证明网格无关性或 LES 改善。
- 当前证据证明 Rhino/Grasshopper 已加载新构建的 GHA。

## 剩余阻塞

- official z = 2 m `raw_trilinear` 指标仍需进一步改善，至少要使 MAE 明显低于既有接近 20 pp 的水平，并使 R2 和 Pearson 为正。
- 需要独立验证 Rhino/Grasshopper 加载的是新 GHA，而不是旧插件副本。
- 继续长时间 native FluidX3D 前需要恢复 GPU runtime；最新 `nvidia-smi` 证据显示 GPU lost。
- 需要完成 Visual Studio Build Tools 2022 C++ 安装，或继续记录可复现的 fallback 构建路径。

