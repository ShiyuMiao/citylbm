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

## Fig. E3-S1

图 E3-S1. 实验3效应量与不确定性补充森林图。图中汇总 S0 行人层与上层风速比、40 m-2 m 竖向恢复、S1/S2 行人层全局变化以及建筑形态近立面到局地环境的恢复增量。该图用于说明核心低速、竖向脱耦和 S1/S2 负结果在方向-采样或方向范围内保持一致，但它只表示已归档模拟输出的统计不确定性，不代表实测不确定性、网格收敛证明或年度舒适度超越概率。

- Asset: `figures/experiment3_effect_size_uncertainty_forest.png`
- Source data: `figures/experiment3_effect_size_uncertainty_summary.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not measurement uncertainty; not grid convergence; not annual comfort exceedance probability

## Fig. E3-S2

图 E3-S2. 实验3八风向各向异性与设计扇区响应补充图。图中比较 S0 行人层 mean VR、行人层滞风比例、40 m-2 m 竖向恢复以及 S2 common-open-cell 局地响应。结果显示行人层低速和高滞风在八个来流方向中近似全向存在，而 S2 的局部响应具有方向性，最强响应出现在 315 deg；但S1/S2全局行人层 mean-VR delta 在全部方向上仍为负。该图支持风扇区耦合的设计解释，不支持年度风玫瑰合规或成功优化宣称。

- Asset: `figures/experiment3_directional_anisotropy_panel.png`
- Source data: `figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv`
- Evidence type: `newly_run + preexisting_artifact + blocked`
- Boundary: not measured wind rose; not annual comfort compliance; not successful optimization

## Fig. E3-S3

图 E3-S3. 101 个保留中心区建筑构件的建筑形式风响应类型学补充图。左图在 50 m 扇区围合度和相对高度空间中显示形态聚类，点大小表示建筑足迹面积；右图比较不同类型的 20-50 m 平均恢复量。类型间恢复量差异显著（Kruskal-Wallis p=0.0001682），支持筛查层结论：本校园核心区的行人层风速恢复更适合解释为相对竖向体量、平面延展性和局地围合共同作用的结果，而不是单一建筑形态变量的结果。

- Asset: `figures/morphology_form_response_archetype_panel.png`
- Source data: `figures/morphology_form_response_archetype_summary.csv; figures/morphology_form_response_archetype_by_component.csv`
- Evidence type: `newly_run + blocked`
- Boundary: not causal typology; not field validation; not universal design class
