# Experiment 3 Deep Data Conclusion Package

evidence_type: newly_run + preexisting_artifact + blocked

This file reorganizes the archived Experiment 3 data into paper-facing conclusions. It does not create new CFD results; it derives conclusion support from existing FluidX3D, ParaView, morphology, design-sensitivity, GCRI and Open-Meteo-proxy tables.

## Conclusion Matrix

| conclusion_id | conclusion_layer | main_finding_zh | key_numbers | evidence_type | claim_boundary |
|---|---|---|---|---|---|
| DC1 | baseline_vertical_structure | 校园核心区行人高度风速比处于强遮蔽状态，而上部流场在20-40 m高度恢复。 | 2 m mean VR=0.076, VR<0.2=93.4%; 20 m mean VR=0.602; 40 m mean VR=1.049, VR<0.2=0.0% | newly_run | 筛查级FluidX3D结果；非实测验证或正式舒适合规评价。 |
| DC2 | directional_robustness | 2 m低风速格局不是单一风向造成，而是在八个风向下均较稳定。 | 2 m mean VR range=0.0060; stagnation range=1.74%; all-direction stagnation=87.2% | newly_run | 八风向筛查，不等于年度超越概率。 |
| DC3 | building_distance_gradient | 风速恢复并不局限于离开立面几米后立即发生，低风速从近立面扩展到街区步行网络。 | 0-4 m mean VR=0.0021, VR<0.2=100.0%; >20 m mean VR=0.0951, VR<0.2=90.8% | newly_run | 基于当前碰撞几何与VTK统计；未包含树冠、热浮力或实测行人路径。 |
| DC4 | morphology_parameters | 局地围合度和局地建成比例比单体尺度面积、细长度或紧凑度更能解释风响应差异。 | strongest rho=-0.534 for combined enclosure score vs directional_mean_vr; 20-50 m enclosure high-low mean VR change=-53.7% | newly_run | 样本内部相关与分组差异；不写成普适因果阈值。 |
| DC5 | stage_and_archetype | 建筑响应可分为持续遮蔽、低速混合、近-远恢复和方向敏感几类，而不是单一线性梯度。 | persistent shelter n=23; near-to-context recovery n=26; recovery-stage mean delta=0.0073; persistent-stage mean delta=-0.0002 | newly_run + blocked | 聚类和阶段分类为样本内部解释工具；需要更多街区外推验证。 |
| DC6 | design_sensitivity | S1/S2增加开放网格或局部孔隙并未改善全局行人层mean VR，反而出现近零或轻微负响应。 | S1 z2 delta mean VR=-0.000213, delta stagnation=0.000233; S2 z2 delta mean VR=-0.000466, delta stagnation=0.000633 | newly_run | 仅S1/S2两个方案；不能写成设计优化成功。 |
| DC7 | climate_proxy_and_uncertainty | Open-Meteo代理风向加权没有改变低风速主结论，但只能作为气候敏感性而非正式风玫瑰验证。 | top3 proxy directions=90,45,270; top3 weight=60.5%; z2 mean VR bootstrap CI=[0.076,0.077]; z2 stagnation CI=[0.926,0.932] | newly_run + preexisting_artifact + blocked | Open-Meteo为代理数据；非现场测风、非正式年度超越概率。 |
| DC8 | digital_twin_model_performance | 数字孪生底层模型的视觉真实性与CFD碰撞可用性明显分离。 | photogrammetry GCRI=0.455; core prism GCRI=0.925; district prism GCRI=0.918 | newly_run + preexisting_artifact | GCRI为本研究定义的应用就绪指标；GCBTE尚未完成。 |

## Paper-Level Interpretation

The data support a more detailed architectural reading than a generic "dense blocks reduce wind" statement. The strongest result is a three-level structure:

1. At pedestrian height, the whole campus core is strongly sheltered and the result is stable across eight wind directions.
2. At intermediate height and at distances beyond the immediate facade band, some recovery appears, but it remains controlled by local enclosure and built fraction.
3. Simple local porosity interventions did not improve the global pedestrian metric, so the design implication is to test connected block-scale ventilation paths instead of assuming that any local opening improves ventilation.

## Evidence Boundary

- Supported: digital-twin-to-CFD transformation, FluidX3D-native screening, ParaView/statistical review, vertical recovery, direction robustness, distance-to-building gradient, morphology-response interpretation, S1/S2 negative sensitivity, GCRI model-role separation.
- Not supported: measured validation, wind-tunnel validation, annual Lawson/NEN/AIJ compliance, pollutant dispersion, GCBTE, CityLBM-Grasshopper end-to-end execution, successful design optimization.
