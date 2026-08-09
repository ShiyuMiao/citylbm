# AIJ Case E 可复现性附录

生成时间: 2026-08-09T11:29:28.428224+00:00

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
- 推荐标签: `v0.4.0-rc31`。
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
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `21b0a2081c446dfffc1d49df0489825ad7e8cd3c4a936f28f9b22362801fac08` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `27ba7254c489b94c081614017a98d53090bd35ffe1949bdb92208450e3a776f2` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `64af31a7b0efc97d3246670430d1e6b867453fe162d5351223bb5e852a276985` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `bdade270bb4ef173280bf6b98409731bbe148ae193af03af36e92643e2c939bc` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `4bdd8198deff440e8e855ec7d622599cc317838d96b4bee09bf93b9d3561396c` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `c55bb6f177435d19217f56563e040a7a2af3c734b03ef74f586a8ed86d1a87cb` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `56927793e49db6c045799c5ff5a180bbbfa7c54d95383a9be2c9a7841c0409c6` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `5ff8612a7dd0b5a36e4515c175cb9cb2bab043648096219af6947efbf148e675` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `628cc584e7267391aca5e616f7847555684bbb0af45d4dcf48e9bf0292c99783` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_official_run_preflight.json` | lightweight_release_asset | blocked_official_followup_preflight | `8329e9529c0ac6d392422efb9771a5d7949794ce85c93535bfd9a7a3cfcc11a9` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `0dad9ccc1d0d96f72c3b75f25e733036c73528914e343158dd19d957344b1f03` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | hash_record_only | paper_ready_figure_negative_validation | `9abacc6d990c1e2ff06453642f6161e0d8ea44e17e94fcc90f96fd2a362bb75d` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | lightweight_release_asset | paper_ready_figure_negative_validation | `abdf36c26968e15532daee49091700f586aedf4a31a8a14355625df89e5fc989` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | lightweight_release_asset | paper_ready_figure_negative_validation | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | lightweight_release_asset | paper_ready_traceability | `527a29aa9227b7f69b5d26cdfbed3fe0531e0143b29b967f94696c0408012eed` |
| `docs/experiments/casee/results/casee_validation_report.md` | lightweight_release_asset | limitations_ready_negative_validation | `4b7b804a1657c90c9deda9c1c92b9a75ef50cc6447a9e1d57e78e63c16a917b4` |
| `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` | lightweight_release_asset | limitations_ready_diagnostic | `58961ab3036c519f6d5665f17239c47007f2b2f34d86dc84aca139eb4bcc1a60` |

## 论文章节可用性

- blocked: 2
- limitations_ready: 3
- paper_ready: 2
- weaken_claim: 1

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

