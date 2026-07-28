# 实验3论文正文草稿：TUM2TWIN 数字孪生校园风环境应用

evidence_type: newly_run + preexisting_artifact + blocked

## 研究目的与定位

在前序 AIJ Case A 与 Case E 已用于求解器基准和工作流验证的前提下，实验3的目标不是再次证明求解器精度，而是检验真实城市数字孪生数据能否被可靠转化为风环境模拟和设计解释所需的 CFD-ready 输入。TUM2TWIN 数据包含 UAS 影像/摄影测量网格、纹理化三维模型、语义建筑数据、CAD/OBJ/Rhino 几何以及立面语义基准等多类资产；这些资产在风环境研究中的功能并不相同。摄影测量或 3DGS-like 资产具有真实外观和场景一致性审查价值，但不应直接等同于封闭刚性碰撞边界；真正进入 FluidX3D/CityLBM 的固体边界需要由语义 LoD 或 CAD-derived 闭合几何生成。这一定位与行人风环境 CFD 研究对不确定性、舒适评价链条和校园尺度决策支持的要求一致 [1,5,6]。

## 数据分层与 CFD-ready 几何构建

本研究将 TUM2TWIN 数据按照“视觉参照、语义/几何管理、碰撞边界、求解输入”四个层次组织。UAS photogrammetry mesh 与纹理化 OBJ/MTL/JPG 用于核验研究范围和真实外观；用户提供的 Rhino photogrammetry 模型用于确认分析对象与 TUM Downtown 校园街区视觉范围一致；LoD/OBJ/CAD-derived 几何用于构建 z0 对齐的闭合 STL 碰撞体；FluidX3D 输入则使用经过 QA 的 core closed-prism collision。几何就绪性通过 GCRI 记录，photogrammetry visual STL、core closed-prism collision 与 district prism collision 的得分分别为 `0.455 / 0.925 / 0.918`。这说明数字孪生底层模型的主要方法贡献不是简单提供“更漂亮”的模型，而是揭示视觉真实性与 CFD-ready 刚性边界之间的差异，并提供从真实场景到可计算几何的证据链 [11,12]。

## FluidX3D 模拟与后处理协议

核心子域采用 dx=2 m 的 FluidX3D 设置，包含 8 个来流方向。每个方向在 spin-up 后抽取 8000、10000 和 12000 steps 三个样本，后处理先进行同风向时间平均，再计算八风向等权平均、Open-Meteo 2024 方向代理加权、竖向 VR 剖面、建筑形态响应和 S1/S2 设计敏感性。主要指标包括 mean VR、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 2024 仅作为方向权重敏感性层，不作为现场实测风玫瑰，也不用于正式年度舒适/安全合规评价 [5,7,8,9]。

## 基准风环境结果

S0 基准结果显示，该校园核心区的主导问题不是强风危险，而是稳定的近地通风不足。z≈2 m 行人层 mean VR / 低速比例为 `0.076 / 0.934`，而 z≈40 m mean VR / 低速比例为 `1.049 / 0.000`。这一竖向差异说明，屋面以上流场恢复不能替代入口、院落、街道连通空间和行人路径的独立评价。Open-Meteo 2024 方向代理加权后，z≈2 m mean VR / 低速比例为 `0.077 / 0.931`，与八风向等权结果非常接近。因此，本文可以写成“低速格局对该代理方向权重不敏感”，但不能写成年度 Lawson/NEN/AIJ 舒适或安全合规结论 [5,7,10]。

## 建筑形态与风速恢复机制

建筑形态分析将传统“围合街谷削弱通风”的认识推进到可定位的校园尺度诊断 [2,3,4]。0-20 m 近立面带几乎普遍滞风，难以区分不同建筑形式的影响；20-50 m 局地环境带更能反映风速恢复差异。多变量稳健性结果为 `0.122+/-0.166 / -0.147 / 0.083`，说明基础形态参数具有解释价值，但不能被写成高精度预测模型。进一步的阈值规则分析将同一批 101 个建筑单元的 0-20 m 与 20-50 m 响应配对，结果为 `mean_height_m=low_tertile + elongation_ratio=high_tertile / 0.0057 / 0.857 / -0.416`。因此，本实验在传统结论基础上提供的新认知是：在校园型连续街区中，风环境改善不宜只看单体建筑面积、伸长率或孔隙面积，而应在 20-50 m 尺度上同时识别局地暴露度、相对竖向尺度、平面连续性和外部动量进入条件。该规则是样本内数字孪生筛查证据，不是可直接外推的通用设计阈值。

## S1/S2 设计敏感性与负结果价值

为检验“增加孔隙是否能缓解低速”的设计假设，本研究构建了 S1 single light relief corridor 和 S2 three-corridor network porosity 两个几何敏感性场景，并使用与 S0 相同的 dx=2 m、8 风向、三样本后处理协议。S1 在 z≈2 m 的 mean VR / 低速比例变化为 `-0.000213 / 0.000233`，S2 为 `-0.000466 / 0.000633`。方向性 trade-off 进一步显示 `315 deg / 0.002374 / 0.006646`。这些结果说明，S1/S2 不能作为成功优化方案；其论文价值在于提供负向设计证据，即几何孔隙面积如果没有与有效来流扇区、动量入口和压力交换路径耦合，就可能只是在低速背景中增加开敞空间，而不能恢复行人层通风。

## 讨论与应用意义

实验3的关键贡献在于建立了真实数字孪生数据到 CFD-ready 风环境筛查的落地链条，并把校园风环境问题从“是否出现强风区”转向“是否存在稳定通风不足及其形态原因”。相较理想街谷或简化建筑群模型，TUM2TWIN 案例保留了真实校园街区的复杂围合、入口、院落和街道连通关系，使风环境分析能够服务于前期筛查、问题定位和设计假设排除。S1/S2 的负结果并不削弱实验价值，反而说明数字孪生工作流可用于在投入更精细 CFD、风洞或现场监测前筛掉低效干预，并将后续设计聚焦到风向扇区耦合的入口廊道、围合解除和压力交换连续性。

## 局限性与证据边界

本文不宣称 TUM Downtown 实测风场验证、风洞闭环、正式年度舒适/安全合规、污染物扩散预测、S3-Sn 正向优化、GCBTE 误差闭合或 CityLBM-Grasshopper 端到端运行。Open-Meteo 2024 是方向权重代理，不是现场风玫瑰；S1/S2 是负向设计敏感性证据，不是最终设计方案；形态统计是解释性筛查，不是可替代 CFD 或现场测量的预测模型。后续若要进入合规评价，需要补充校准风玫瑰、阈值超越概率、网格/时间敏感性、实测或风洞闭环以及必要的污染物或热舒适耦合模拟。

## References

[1] Blocken; Stathopoulos; van Beeck (2016). Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment. Building and Environment, 100, 50-81. doi:10.1016/j.buildenv.2016.02.004. https://doi.org/10.1016/j.buildenv.2016.02.004
[2] Oke (1988). Street design and urban canopy layer climate. Energy and Buildings, 11, 103-113. doi:10.1016/0378-7788(88)90026-6. https://doi.org/10.1016/0378-7788(88)90026-6
[3] Cheng; Liu; Leung (2009). On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number. Building Simulation, 2, 53-61. doi:10.1007/S12273-008-8332-4. https://doi.org/10.1007/s12273-008-8332-4
[4] Tsang; Kwok; Hitchcock (2012). Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium. Building and Environment, 49, 167-181. doi:10.1016/j.buildenv.2011.08.014. https://doi.org/10.1016/j.buildenv.2011.08.014
[5] Janssen; Blocken; van Hooff (2013). Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study. Building and Environment, 59, 547-562. doi:10.1016/j.buildenv.2012.10.012. https://doi.org/10.1016/j.buildenv.2012.10.012
[6] Blocken; Janssen; van Hooff (2012). CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus. Environmental Modelling and Software, 30, 15-34. doi:10.1016/j.envsoft.2011.11.009. https://doi.org/10.1016/j.envsoft.2011.11.009
[7] Hagbo; Giljarhus (2022). Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions. Frontiers in Built Environment, 8. doi:10.3389/fbuil.2022.858067. https://doi.org/10.3389/fbuil.2022.858067
[8] Peel; Finlayson; McMahon (2007). Updated world map of the Koppen-Geiger climate classification. Hydrology and Earth System Sciences, 11, 1633-1644. doi:10.5194/hess-11-1633-2007. https://doi.org/10.5194/hess-11-1633-2007
[9] Beck et al. (2018). Present and future Koppen-Geiger climate classification maps at 1-km resolution. Scientific Data, 5. doi:10.1038/sdata.2018.214. https://doi.org/10.1038/sdata.2018.214
[10] Fadl; Karadelis (2013). CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus. International Journal of Architecture, Engineering and Construction, 2, 131-143. doi:10.7492/IJAEC.2013.013. https://doi.org/10.7492/ijaec.2013.013
[11] TUM2TWIN project (2025). TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks. Official TUM2TWIN website. https://tum2t.win/datasets
[12] Hagbo; Giljarhus; Hjertager (2020). Influence of geometry acquisition method on pedestrian wind simulations. arXiv:2010.12371. https://arxiv.org/abs/2010.12371

## 待补充清单

- AUTHOR_INPUT_NEEDED: target journal and formatting/citation style.
- RESULT_NEEDED: onsite or wind-tunnel validation if field-validated accuracy is claimed.
- RESULT_NEEDED: annual comfort/safety exceedance calculation with calibrated wind climate if Lawson/NEN/AIJ compliance is claimed.
- RESULT_NEEDED: pollutant scalar transport if exposure or concentration hotspots are claimed.
- RESULT_NEEDED: CityLBM-Grasshopper end-to-end screenshot/logs if the final method title foregrounds CityLBM-GH rather than FluidX3D-native simulation.
