# 实验3 SCI 论文模块：TUM2TWIN 数字孪生校园风环境应用

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题名

真实城市数字孪生数据到 CFD-ready 风环境筛查的应用转化：基于 TUM2TWIN 校园核心区的 FluidX3D 实验

## 研究定位

Case A 与 Case E 已承担求解器基准与前序验证角色；实验3不重新宣称求解器精度，而聚焦真实数字孪生城市数据如何进入风环境模拟与设计解释。本文将 TUM2TWIN 的 UAS/photogrammetry 视觉资产、LoD/OBJ 语义几何、Rhino/OBJ 管理模型和闭合 STL 碰撞边界分层使用，以避免把视觉真实误写为 CFD-ready。该定位与行人风环境 CFD 研究中对不确定性、舒适评价链条和校园尺度决策支持的要求一致 [R1,R5-R7]。

## 方法

本文首先对 TUM2TWIN 数据进行功能分层。UAS photogrammetry mesh 与纹理模型用于场景范围核验、真实外观对照和 Rhino/ParaView 手动审查；语义建筑数据和 LoD/CAD-derived 几何用于生成闭合刚性碰撞边界；用户 photogrammetry STL 作为视觉参考和几何可用性反例保留，不直接作为最终 LBM 碰撞体。几何就绪性通过 GCRI 记录，其中 photogrammetry visual STL / core closed-prism collision / district prism collision 的得分分别为 0.455 / 0.925 / 0.918。

FluidX3D 模拟采用 dx=2 m 的核心子域，包含 8 个来流方向，并在 spin-up 后抽取 8000、10000 和 12000 steps 三个样本。后处理先进行同风向时间平均，再输出八风向等权结果、Open-Meteo 2024 风向代理加权结果、不同高度层 VR 统计、建筑距离/形态关联和 S1/S2 设计敏感性比较。评价指标包括 mean VR、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 仅用于方向权重敏感性，不用于正式年度舒适概率评价。

## 实验设置

研究对象为 TUM Downtown photogrammetry 视觉范围对应的校园核心街区。S0 为 core closed-prism collision baseline；S1 为单条 light relief corridor；S2 为三通道 network porosity。S1/S2 与 S0 共享 dx=2 m、8 风向和三样本后处理协议，因此比较结果可解释为几何敏感性，而不是不同求解设置造成的差异。图表调用建议见 `manifests/experiment3_manuscript_figure_table_plan.csv`。

## 结果

S0 基准结果表明，行人高度的主导问题是通风不足而非强风危险。z≈2 m mean VR / 低速比例为 0.076 / 0.934；z≈40 m mean VR / 低速比例为 1.049 / 0.000。这一竖向差异说明屋面以上的流速恢复不能替代校园步行层、入口、院落与街道连通空间的独立评价。Open-Meteo 2024 方向代理加权后 z≈2 m mean VR / 低速比例为 0.077 / 0.931，与八风向等权平均接近，支持“低速结论对代理方向权重不敏感”的筛查性判断，但不支持年度 Lawson/NEN/AIJ 舒适安全合规结论 [R5,R8-R10]。

建筑形式分析显示，0-20 m 近立面带近乎整体滞风，20-50 m 局地环境带更能反映风速恢复差异。多变量稳健性结果为 0.122+/-0.166 / -0.147 / 0.083，说明基础形态参数的预测力有限，但变量排序仍有解释意义：局地扇区围合和平均高度比单体 footprint、elongation 或 perimeter-area compactness 更接近行人层风速恢复机制。本文由此将传统“高密度/围合削弱通风”的认识转化为可定位的校园尺度诊断：关键不只是建筑有多高或多大，而是 30-50 m 范围内是否存在连续围合、动量入口不足和院落-街道压力交换受阻 [R2-R4]。

S1/S2 设计敏感性实验进一步限定了设计结论。S1 在 z≈2 m 的 mean VR / 低速比例变化为 -0.000213 / 0.000233；S2 为 -0.000466 / 0.000633。方向性 trade-off 显示 S2 的局部响应为 315 deg / 0.002374 / 0.006646。因此，S1/S2 均不能被写成成功优化方案；它们的价值在于说明几何孔隙面积本身不足以恢复行人层通风，开口必须与有效来流扇区、动量入口和压力交换路径耦合。

## 讨论

相较传统理想街谷或简化建筑群研究，本实验的新增价值不在于声称更高预测精度，而在于将真实数字孪生数据的可视化层、语义层和碰撞层分离，并记录从视觉一致性到 CFD-ready 的证据链。TUM2TWIN 的 photogrammetry/3DGS-like 资产提供真实外观和场景审查价值，但最终碰撞边界必须由语义/LoD/CAD-derived 闭合几何生成 [R11,R12]。风环境结论也应从“是否形成强风区”转向“校园核心区是否存在稳定通风不足及其局地形态原因”。

## 局限性

本文不宣称实测风场验证、风洞闭环、正式年度舒适/安全合规、污染物扩散预测、S3-Sn 正向优化、GCBTE 误差闭合或 CityLBM-Grasshopper 端到端运行。Open-Meteo 方向权重是气候代理，不是现场风玫瑰；S1/S2 是负向设计敏感性证据，不是最终设计方案；形态统计是解释性筛查，不是可替代 CFD 的高精度预测模型。

## 可直接用于摘要的结论句

本实验表明，TUM2TWIN 数字孪生数据能够通过语义闭合几何转化为 FluidX3D 可用的真实校园街区风环境筛查流程；在当前核心区，模拟结果显示行人层持续低速、上部流场恢复和局地围合控制有限风速恢复，且 S1/S2 负向敏感性说明设计干预应从简单增加孔隙面积转向风向扇区耦合的动量入口和压力交换连续性。

## 参考文献键

[R1] Blocken; Stathopoulos; van Beeck (2016). Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment. Building and Environment, 100, 50-81. doi:10.1016/j.buildenv.2016.02.004.
[R2] Oke (1988). Street design and urban canopy layer climate. Energy and Buildings, 11, 103-113. doi:10.1016/0378-7788(88)90026-6.
[R3] Cheng; Liu; Leung (2009). On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number. Building Simulation, 2, 53-61. doi:10.1007/S12273-008-8332-4.
[R4] Tsang; Kwok; Hitchcock (2012). Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium. Building and Environment, 49, 167-181. doi:10.1016/j.buildenv.2011.08.014.
[R5] Janssen; Blocken; van Hooff (2013). Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study. Building and Environment, 59, 547-562. doi:10.1016/j.buildenv.2012.10.012.
[R6] Blocken; Janssen; van Hooff (2012). CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus. Environmental Modelling and Software, 30, 15-34. doi:10.1016/j.envsoft.2011.11.009.
[R7] Hagbo; Giljarhus (2022). Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions. Frontiers in Built Environment, 8. doi:10.3389/fbuil.2022.858067.
[R8] Peel; Finlayson; McMahon (2007). Updated world map of the Koppen-Geiger climate classification. Hydrology and Earth System Sciences, 11, 1633-1644. doi:10.5194/hess-11-1633-2007.
[R9] Beck et al. (2018). Present and future Koppen-Geiger climate classification maps at 1-km resolution. Scientific Data, 5. doi:10.1038/sdata.2018.214.
[R10] Fadl; Karadelis (2013). CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus. International Journal of Architecture, Engineering and Construction, 2, 131-143. doi:10.7492/IJAEC.2013.013.
[R11] TUM2TWIN project (2025). TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks. Official TUM2TWIN website.
[R12] Hagbo; Giljarhus; Hjertager (2020). Influence of geometry acquisition method on pedestrian wind simulations. arXiv:2010.12371.
