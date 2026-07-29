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

## Sentence-Level Evidence Map

| sentence_id | language | manuscript_use | sentence_text | evidence_type | blocked_wording_to_avoid |
|---|---|---|---|---|---|
| DC1_EN | en | Results: vertical wind structure | The TUM Downtown campus core is strongly sheltered at pedestrian height: the z=2 m plane has a mean velocity ratio of 0.076 and 93.4% of open cells below VR=0.2, whereas the mean velocity ratio increases to 0.602 at 20 m and 1.049 at 40 m. | newly_run | field-validated pedestrian comfort; annual exceedance; full grid-independence proof |
| DC1_ZH | zh | Results: vertical wind structure | 结果表明，TUM Downtown校园核心区在2 m行人高度呈现强遮蔽状态，mean VR仅为0.076，VR<0.2区域约占93.4%；但20 m和40 m高度的mean VR分别升至0.602和1.049，说明该街区存在明显的行人层-上部流场脱耦。 | newly_run | field-validated pedestrian comfort; annual exceedance; full grid-independence proof |
| DC2_EN | en | Results: directional robustness | The low-speed pedestrian layer is not a single-wind-direction artefact: across the eight simulated wind directions, the z=2 m mean velocity ratio varies by only 0.0060, the stagnation-area ratio varies by 1.74 percentage points, and 87.2% of open pedestrian cells remain stagnant for all directions. | newly_run | measured dominant-wind validation; formal wind-climate exceedance probability |
| DC2_ZH | zh | Results: directional robustness | 八风向结果显示，2 m高度mean VR的风向范围仅为0.0060，VR<0.2面积比例的范围约1.74个百分点，且87.2%的行人层开放网格在所有风向下均保持低风速状态，说明该校园核心区的低通风问题具有明显方向鲁棒性。 | newly_run | measured dominant-wind validation; formal wind-climate exceedance probability |
| DC3_EN | en | Results: building-distance gradient | The distance-to-building analysis shows that low ventilation extends beyond the immediate facade band: the 0-4 m band has a mean VR of 0.0021, and even cells more than 20 m from buildings retain a mean VR of only 0.095 with 90.8% of cells below VR=0.2. | newly_run | tree-canopy effects; buoyancy; observed pedestrian-route exposure |
| DC3_ZH | zh | Results: building-distance gradient | 按至建筑距离分组后，0-4 m近立面带mean VR仅为0.0021，4-10 m和10-20 m仍几乎全部低于VR=0.2；即使在>20 m区域，mean VR也仅为0.095，约90.8%的开放网格仍低于VR=0.2。这表明低通风并非单纯的近墙边界层，而是被街区围合扩展为步行网络尺度的问题。 | newly_run | tree-canopy effects; buoyancy; observed pedestrian-route exposure |
| DC4_EN | en | Discussion: morphology explanation | Component-level morphology statistics indicate that local enclosure and local built fraction are more informative screening descriptors than isolated footprint size or elongation, with the strongest observed correlation being between the near-facade combined enclosure score and directional mean VR (Spearman rho=-0.534). | newly_run | universal causal threshold; transferable predictor without external blocks |
| DC4_ZH | zh | Discussion: morphology explanation | 形态统计显示，近立面0-20 m带内combined enclosure score与directional mean VR的Spearman相关为-0.534，local built fraction的相关为-0.464；20-50 m带内sector enclosure仍为最清晰的抑制因子。高combined enclosure组相对低组的20-50 m mean VR降低约53.7%，提示局地围合度是比单体面积或细长度更有解释力的设计筛查参数。 | newly_run | universal causal threshold; transferable predictor without external blocks |
| DC5_EN | en | Discussion: response archetypes | The building-component response is better described as a set of local-context regimes than as a monotonic distance gradient: 23 components fall into persistent shelter, 26 into near-to-context recovery, and 9 into directionally reactive behaviour. | newly_run + blocked | universal archetype taxonomy; causal typology beyond the sampled campus core |
| DC5_ZH | zh | Discussion: response archetypes | 组件级阶段分析显示，23个建筑组件属于persistent shelter，26个属于near-to-context recovery，9个表现出directionally reactive特征。恢复型组件的局地恢复增量均值为0.0073，而持续遮蔽型为-0.0002，说明真实校园街区中的风环境响应更接近形态上下文驱动的多类型谱系，而非简单的随距离单调恢复。 | newly_run + blocked | universal archetype taxonomy; causal typology beyond the sampled campus core |
| DC6_EN | en | Discussion: design sensitivity | The two design-sensitivity tests provide a useful negative result: S1 and S2 slightly increase the number of open cells but do not improve the global z=2 m mean VR, which changes by -0.000213 for S1 and -0.000466 for S2. | newly_run | successful optimization; general claim that porosity never improves wind conditions |
| DC6_ZH | zh | Discussion: design sensitivity | 两个设计敏感性方案均未带来全局行人层改善：S1在2 m高度的mean VR变化为-0.000213，S2为-0.000466，且VR<0.2比例分别增加0.000233和0.000633。该负结果提示，在强围合校园核心中，设计干预需要围绕街区尺度通风路径和压力连通组织，而不是仅增加局部空隙。 | newly_run | successful optimization; general claim that porosity never improves wind conditions |
| DC7_EN | en | Limitations: climate proxy and uncertainty | Open-Meteo weighting is retained only as a climate-proxy sensitivity layer: the three largest proxy direction sectors account for 60.5% of the weight, but this does not replace measured wind-rose data or annual comfort assessment. | newly_run + preexisting_artifact + blocked | formal Lawson/NEN/AIJ annual compliance; measured local wind climate |
| DC7_ZH | zh | Limitations: climate proxy and uncertainty | Open-Meteo 2024代理风向加权显示前三个模拟风向合计权重约为60.5%，但2 m低速结论在方向样本bootstrap区间内保持稳定：mean VR为0.076，95%区间为0.076-0.077，VR<0.2比例为0.929，95%区间为0.926-0.932。因此，气候代理可用于情景权重敏感性讨论，但不能替代正式测风或年度舒适评价。 | newly_run + preexisting_artifact + blocked | formal Lawson/NEN/AIJ annual compliance; measured local wind climate |
| DC8_EN | en | Methods/Discussion: digital-twin model performance | The GCRI results demonstrate the modelling gap between visual digital-twin assets and CFD collision geometry: the photogrammetry STL scores 0.455, whereas the repaired core and district prism collision geometries score 0.925 and 0.918. | newly_run + preexisting_artifact | 3DGS boundary-transfer accuracy; direct use of visual meshes as final collision boundaries |
| DC8_ZH | zh | Methods/Discussion: digital-twin model performance | GCRI结果显示，用户摄影测量STL的就绪度仅为0.455，而经闭合、z0对齐并成功体素化的核心和街区棱柱碰撞几何分别达到0.925和0.918。这说明数字孪生底层模型在风环境应用中不能按视觉真实性直接等同于CFD边界质量，而应区分视觉参照、语义建筑层和碰撞几何层。 | newly_run + preexisting_artifact | 3DGS boundary-transfer accuracy; direct use of visual meshes as final collision boundaries |

## Paper-Level Interpretation

The data support a more detailed architectural reading than a generic "dense blocks reduce wind" statement. The strongest result is a three-level structure:

1. At pedestrian height, the whole campus core is strongly sheltered and the result is stable across eight wind directions.
2. At intermediate height and at distances beyond the immediate facade band, some recovery appears, but it remains controlled by local enclosure and built fraction.
3. Simple local porosity interventions did not improve the global pedestrian metric, so the design implication is to test connected block-scale ventilation paths instead of assuming that any local opening improves ventilation.

## Evidence Boundary

- Supported: digital-twin-to-CFD transformation, FluidX3D-native screening, ParaView/statistical review, vertical recovery, direction robustness, distance-to-building gradient, morphology-response interpretation, S1/S2 negative sensitivity, GCRI model-role separation.
- Not supported: measured validation, wind-tunnel validation, annual Lawson/NEN/AIJ compliance, pollutant dispersion, GCBTE, CityLBM-Grasshopper end-to-end execution, successful design optimization.
