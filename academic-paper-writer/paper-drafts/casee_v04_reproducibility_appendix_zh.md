# AIJ Case E 可复现性附录

生成时间: 2026-08-09T11:55:42.985575+00:00

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
- 推荐标签: `v0.4.0-rc33`。
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
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `555f96b38551f40ed68783fcf7544a8b8e4393e20e0d9e5c65ab1f0b7553fee6` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `a4e6c12999f17ebea9aaf02f91fbad48674b70f0306c294acc9ff17e184304bd` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `f5a8057998c61564f1e953fc930ce8354052cf1f755114142fe8a67575b1bea3` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `38ca54c97a7a03a107f3e9b0ede30e85e52984f947b4a1f2e7a48990c31d90d4` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `d8b49c9b8a86147015f415eaddbaef745afc46d22613c6b3f3305d6479f1ad38` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `07063479d98588420c3e550ff6a2fcd48d5d73db361c7cce1953e2d6879f92aa` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `016ad25450120caf1742bcefb0072c1a30704cc5a2e59f197699110239b6473c` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `039be851321c898aeb68abbcd16f5eadee6d84e64000fe3ca4d391abbcfa3e11` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `063fcf20777136d8996121dcf58499f7c90cf486ae65417f6830f2d134537fdf` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `9ca85047de2d818ff5ac98cdb6197b5f92c4d9dab0389f41fd778689c349edf0` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `cb8d1fc815c4d99a7abd899328652a15b2e33454a37f75fd5c8b5f9b9fbd16d2` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `dd6314a14a97a80f145ccd0ac717825f1ec9b5bcacffcc2ceeadfb8ac9bf3c58` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_official_run_preflight.json` | lightweight_release_asset | blocked_official_followup_preflight | `b1a27f11f5a943e4bd78453bd24040cfff49bb17054ce764824bce9932740c8e` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `f4fed5a5a28c441962d1c879e8e814c772f5718aa346efd0945265a7a68b5dc2` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | hash_record_only | paper_ready_figure_negative_validation | `ec5fead9978df0fc64bd8de61a508738f05f73170ed841fd4d9d0d320bc5f02a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | lightweight_release_asset | paper_ready_figure_negative_validation | `7777be3ae25b3e35fbff0cef020806c9c01818f928971f7df69fa2a904b5e451` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | lightweight_release_asset | paper_ready_figure_negative_validation | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |

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

