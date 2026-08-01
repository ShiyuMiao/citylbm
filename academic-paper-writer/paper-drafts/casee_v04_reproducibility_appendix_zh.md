# AIJ Case E 可复现性附录

生成时间: 2026-08-01T12:53:30.647940+00:00

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
- 推荐标签: `v0.4.0-rc18`。
- CityLBM 构建通过: True。
- Case A smoke regression 通过: True。
- Rhino 是否已加载新 GHA: False。
- official z = 2 m 指标门槛是否通过: False。

## 可追溯命令

- `citylbm_release_build` (passed, returncode=0): `E:\citylbm_buildchain\dotnet\dotnet.exe build CityLBM/CityLBM.csproj -c Release`
- `casee_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe`
- `manuscript_evidence_summary` (passed, returncode=0): `python docs/experiments/casee/tools/manuscript_evidence_summary.py`
- `plugin_identity_gate` (passed, returncode=0): `python docs/experiments/casee/tools/plugin_identity_gate.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## 关键产物

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `3702792b59e2251f4df12cb302d002d7dcef5f1baf1b1acc7ae20b12db621660` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `64af31a7b0efc97d3246670430d1e6b867453fe162d5351223bb5e852a276985` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `def89b6752b20e878719a39ce2d866159aca410141ed6deed06245988bbb68b1` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `17f532bb5826a313f7dd6ee09ea87ffc3bfb7a31fe6acc5c8ba6702e9998c863` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | lightweight_release_asset | paper_ready_traceability | `54ab712e995028fe2619974d1ba37308badbe5e0ee356a58f7453d39ee4963fc` |
| `docs/experiments/casee/results/casee_validation_report.md` | lightweight_release_asset | limitations_ready_negative_validation | `c8a3ccdf5d33f9a4df166757d9320c378fc886390742c737688620dd7ee080c4` |
| `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` | lightweight_release_asset | limitations_ready_diagnostic | `58961ab3036c519f6d5665f17239c47007f2b2f34d86dc84aca139eb4bcc1a60` |
| `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv` | lightweight_release_asset | limitations_ready_diagnostic | `dcf90ab869ee70f4d01af830b6d28653632e0f1fd2e013b9ae0f74d1a1f3c993` |
| `docs/experiments/casee/results/plugin_identity_gate.json` | lightweight_release_asset | paper_ready_traceability | `5cbecf1e3d6f373ae56193f9cfa6ac1aecdc83c955b19662eb60ff9e158ff701` |
| `docs/experiments/casee/results/release_gate.json` | lightweight_release_asset | blocked_formal_release_gate | `5aebfc3c1ac6cca3759bbec67ef2d7aa0cc2340dd1b12a3b3632a62d73bf14a6` |
| `CHANGELOG.md` | lightweight_release_asset | paper_ready_reproducibility | `cc6f9e91f5110d8346f74b64d9c271ac8c9ffd28db729838005740b335f4a61f` |
| `CityLBM/README.md` | lightweight_release_asset | paper_ready_reproducibility | `c7626d90345153e7fce1bcd3cf39baef96763cb48566d073979d273145c65c81` |
| `README.md` | lightweight_release_asset | paper_ready_reproducibility | `64a8bb5557b4f9cd9c659bfe67e2239c0ef509d4dccb451c3748993e493d7ade` |

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

