# AIJ Case E 结果与局限性草稿（中文）

evidence_type: newly_run
status: v0.4.0-rc evidence only
generated_from:
- docs/experiments/casee/results/release_gate.json
- docs/experiments/casee/results/casee_manuscript_claim_matrix.csv
- docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv
- docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv

## 可直接写入 Results 的版本

本研究按照 AIJ Case E 的官方 `ac+N` 工况复核 CityLBM/FluidX3D 工作流，正式验证高度限定为行人高度 `z=2 m`，测点为 `RS_caseE.csv` 中 `case=ac` 且 `Wind_direction=N` 的 80 个官方探针。正式统计仅采用 `raw_trilinear` 采样，不使用 `z_plus_half`、`vertical_valid_above` 或任何上移高度作为替代结果。最新 z-center 诊断运行得到 MAE = 21.111 percentage points，RMSE = 27.721 percentage points，Bias = -16.409 percentage points，R2 = -2.006330，Pearson = 0.115756（newly_run；source: `docs/experiments/casee/results/release_gate.json`）。因此，当前结果不能写成精度验证通过，也不能支撑 CityLBM v0.4.0 正式发布；它应作为严格协议下的负验证结果和误差诊断证据呈现。

与上一组 dx=2 m probe-mode 结果相比，z-center 格点对齐使正式 `raw_trilinear` 的 MAE 从 23.972 percentage points 降至 21.111 percentage points，R2 从 -2.311768 改善至 -2.006330，Pearson 从 0.071789 提升至 0.115756（newly_run；source: `docs/experiments/casee/results/casee_probe_mode_metrics.csv` and `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`）。该改善说明垂向格点布置会影响 AIJ Case E 行人高度测点误差，但改善幅度仍不足以达到论文中“预测精度已验证”的要求。

误差审计进一步显示，误差主要集中在近壁面、实体角点插值风险较高的探针。z-center 审计中，低风险测点的正式 `raw_trilinear` MAE 为 12.435 percentage points，而中风险和高风险测点分别为 32.644 和 34.589 percentage points（newly_run；source: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv`）。这表明当前瓶颈更接近近壁面采样、体素化边界和壁面模型问题，而不是单纯的后处理表格误差。

## 可直接写入 Discussion / Limitations 的版本

当前 Case E 证据支持三个有限结论。第一，CityLBM v0.4.0-rc 已经把官方 Case E 前置条件、80 测点筛选、入口剖面和多种探针采样诊断纳入可追溯流程。第二，z-center 格点对齐和探针风险审计能够降低部分误差并定位误差来源。第三，正式 `z=2 m` 验证仍未通过，R2 仍为负值，因此该版本只能作为 accuracy diagnostic release，而不能作为 predictive-accuracy release。

诊断采样模式具有方法学价值，但不能替代官方结果。在 z-center 运行中，`vertical_valid_above` 的 MAE 可降至 16.041 percentage points，R2 改善到 -0.554717，Pearson 为 0.336940（newly_run；source: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`）。然而该模式改变了官方 z=2 m 探针协议，只能用于说明近壁面/实体角点采样敏感性，不能作为正式验证指标。

因此，论文中关于 CityLBM 的精度表述应保持克制：可以写“该工具链已形成可复现的 AIJ Case E 诊断流程，并揭示了行人高度近壁面误差集中机制”；不应写“CityLBM 已在 AIJ Case E 达到科研级预测精度”。后续若要进入正式 v0.4.0，需要至少使 official z=2 m 的 R2 转正、Pearson 稳定为正相关、MAE 明显低于当前约 21 pp，并完成 Rhino/Grasshopper 新 GHA 加载确认、Case A smoke regression 和完整构建链复核。

## 论文中可以保留的句子

- CityLBM/FluidX3D 工作流在 AIJ Case E 中完成了官方 `ac+N`、`z=2 m`、80 测点协议的可追溯复核。
- 当前 official z=2 m 结果为 MAE = 21.111 percentage points、R2 = -2.006330、Pearson = 0.115756，因此不满足正式精度发布门槛。
- z-center 格点诊断降低了 MAE 并提高了 Pearson，但未使 R2 转正。
- 高风险近壁面/实体角点测点贡献了主要误差，提示后续优化应聚焦壁面模型、体素化边界和官方探针采样协议。

## 论文中不能写的句子

- CityLBM v0.4.0 已通过 AIJ Case E 精度验证。
- z_plus_half 或 vertical_valid_above 是官方 z=2 m 验证结果。
- 当前结果证明了 LES 改善或网格无关性。
- 只要使用 z-center 格点对齐，就可以默认提高所有城市风环境案例的预测精度。
