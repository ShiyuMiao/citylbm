# 实验3 SCI 图题说明

evidence_type: newly_run + preexisting_artifact + blocked

These captions are tied to archived source artifacts. They should be edited only for journal style, not for claim strength, unless new evidence is added.

## Fig. E3-1

图 E3-1. TUM Downtown 核心校园街区在行人高度的 FluidX3D/VTK 风速比筛查图。图中结果来自 dx=2 m、8 个来流方向、三时刻采样后的核心闭合棱柱碰撞几何，用于人工审核低风速区、方向一致性和建筑周边滞风格局。该图支持“行人层以低速和通风不足为主”的筛查性结论，但不支持年度舒适度合规、实测验证或污染物扩散结论。

- Asset: `figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png`
- Source data: `figures/paraview_vtk_core_dx2m_robustness_stats.csv; figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`
- Evidence type: `newly_run`
- Boundary: not annual Lawson/NEN/AIJ compliance; not field validation; not scalar dispersion

## Fig. E3-2

图 E3-2. 基础建筑形态参数与 20-50 m 局地环境风速响应的多变量稳健性分析。图中排序回归系数和置换重要度显示，局地围合度、平均高度和综合围合指标比单体占地面积、平面伸长率或紧凑度更能解释样本内风速差异。由于交叉验证解释力有限，该图应写成可解释筛查证据，而不是高精度预测模型。

- Asset: `figures/basic_morphology_multivariate_rank_model_importance.png`
- Source data: `figures/basic_morphology_multivariate_robustness.csv; figures/basic_morphology_rank_model_cv_summary.csv`
- Evidence type: `newly_run`
- Boundary: not a deterministic surrogate model; not externally validated thresholds

## Fig. E3-3

图 E3-3. S1/S2 设计敏感性场景在行人高度的方向性局地 trade-off。热图比较不同来流方向下共同开放单元的风速比变化，显示 S2 的局地正响应略强于 S1，但改善单元稀疏且新增开放单元仍处低速状态。因此该图的论文价值是负结果证据，即几何孔隙率本身不足以恢复校园核心区行人层通风。

- Asset: `figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png`
- Source data: `figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv; figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`
- Evidence type: `newly_run`
- Boundary: not successful optimization; not final design recommendation

## Fig. E3-4

图 E3-4. 0-20 m 近立面带到 20-50 m 局地环境带的风速恢复阈值规则筛查。分析在同一组 101 个保留建筑单元上比较近立面与局地环境响应，提取样本内 tertile 组合规则。最佳简单规则提示较低相对竖向尺度和特定平面形态组合更易出现局地恢复，但该阈值仅用于数字孪生样本内设计筛查，不能外推为通用规范或实测验证结论。

- Asset: `figures/morphology_threshold_recovery_rule_summary.png`
- Source data: `figures/morphology_threshold_rule_screening.csv; figures/morphology_recovery_top_bottom_contrast.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not universal threshold; not field-validated design rule
