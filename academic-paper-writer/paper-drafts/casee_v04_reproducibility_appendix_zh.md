# AIJ Case E 可复现性附录

生成时间: 2026-08-11T00:41:57.689691+00:00

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
- 推荐标签: `v0.4.0-rc51`。
- CityLBM 构建通过: True。
- Case A smoke regression 通过: True。
- Rhino 是否已加载新 GHA: False。
- official z = 2 m 指标门槛是否通过: False。

## 可追溯命令

- `citylbm_release_build` (passed, returncode=0): `E:\citylbm_buildchain\dotnet\dotnet.exe build CityLBM/CityLBM.csproj -c Release`
- `casee_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe`
- `manuscript_evidence_summary` (passed, returncode=0): `python docs/experiments/casee/tools/manuscript_evidence_summary.py`
- `plugin_identity_gate` (passed, returncode=0): `python docs/experiments/casee/tools/plugin_identity_gate.py`
- `rhino_gha_load_gate` (passed, returncode=0): `python docs/experiments/casee/tools/rhino_gha_load_gate.py`
- `build_chain_audit` (passed, returncode=0): `python docs/experiments/casee/tools/build_chain_audit.py`
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `casee_dx1_readiness_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_dx1_readiness_audit.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_zcenter_rerun_consistency` (passed, returncode=0): `python docs/experiments/casee/tools/casee_zcenter_rerun_consistency.py`
- `casee_c002_longer_mean_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c002_longer_mean_audit.py`
- `casee_c003_zorigin_ablation_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c003_zorigin_ablation_audit.py`
- `casee_c004_dx3_low_cost_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c004_dx3_low_cost_audit.py`
- `casee_c005_decomposition_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c005_decomposition_audit.py`
- `casee_c008_c009_inlet_turbulence_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c008_c009_inlet_turbulence_audit.py`
- `casee_c014_residual_structure_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c014_residual_structure_audit.py`
- `casee_c016_residual_target_leakage_guard` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c016_residual_target_leakage_guard.py`
- `casee_solver_run_provenance_ledger` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_solver_run_provenance_ledger.py`
- `casee_candidate_sweep_plan` (passed, returncode=0): `python docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `citylbm_manifest_schema_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `casee_manuscript_section_pack` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `casee_paper_results_figure` (passed, returncode=0): `python docs/experiments/casee/tools/casee_paper_results_figure.py`
- `citylbm_software_feedback_matrix` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `casee_next_experiment_runbook` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_next_experiment_runbook.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## 关键产物

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `52137c07edc5c6c31386239761404ae1a5972d36c65b9048093f0ce4af1e1be0` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `dc6ad3fed9f0d840cd37dd1ec4b08bf6a320604fb8780ccdfed8a6cf498d4309` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `ef52a02951253261730a7ca308f1a97b1ec2bfa92023c1b96e513f4a30c5d0c0` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `dd3642be67d1f65540340c9a7e272d594eb912fa36c2d5c31f665596dc3ba241` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `f1cd384abbbe47b9aae857dd405f047e1a18d6fb7fb696bac212c9e9dd1758c3` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `176f88ceda2497c7375e8cb6e39f08c9f163875db9db0cb2bf279f6aede760b6` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `ba68ac987771a0e23537326db3f8e559e1e481098caff0420b6dc8b94b770bb6` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `7084f4f0a1c30614fba26371255538add6e1a8c0367ec471daee8a3549f05e23` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `0eed7f87785225166c7fb8ab8e2e5ea9f5a34e0fbbce8fb6d5a06955966d4050` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `e71c535ec315598bf4ee00324a1bb9c8a8b4adc74a45b79088af7ce8d1aa5dda` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `507b2a4c2111f1fcb741d84b28278ede0e1b17d0bd65364c2c662fb3088623b2` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `996d41c2c8a94ca1a817dea19a1dab1086489cd51c985a702c685e3c5bab2b94` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `2668894311e27377d411c34a3f2f75f264b3189474eb4d957bb3d8a4086b01b3` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `c6674f65fbcdfca7795bed751976871c3ab78555c6a6092e067f22a68024ecce` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `15db27d5174430c6c3727363a43420f477a86e26fc2bac658e25baf51c53a8ed` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `30a5220bb888010c76924da2ba7feb01b2acf27fca20da15fa82184fdfaf9268` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `2ebd4a75ef841bad5dabbaa8ade41ab68425d474f2978e57ee62c4dae3918aae` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `4405bf655937220a025b81bf89747cec3cbc049fcb745c7dcd08d0e068b456cd` |

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

