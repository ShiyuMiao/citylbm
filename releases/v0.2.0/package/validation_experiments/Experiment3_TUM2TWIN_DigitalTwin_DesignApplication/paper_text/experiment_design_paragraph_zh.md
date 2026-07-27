# 实验定位段落（中文）

本实验位于前序 Case A/E 基准验证之后，研究目标不是重新证明 FluidX3D 或 CityLBM 的求解精度，而是评估真实城市数字孪生数据进入风环境模拟应用的可行路径、关键阻碍和证据边界。TUM2TWIN 同时提供 UAS 影像/photogrammetry mesh、纹理化外观、语义城市模型、OBJ/CAD/Rhino 中间模型和立面语义参考，为“数字孪生资产如何从可视化资源转化为 CFD/LBM 可计算边界”提供了合适案例。本文将 photogrammetry/Rhino 视觉模型用于真实场景核验和三维可视化，将官方 LoD3 OBJ 衍生的闭合语义棱柱几何作为 FluidX3D 主要碰撞边界，并通过用户提供的 full-resolution photogrammetry STL pilot 证明视觉网格即使能够进入求解器，也会在体素化中表现为非封闭、片状或高度错位的固体掩膜，因此不能直接作为最终刚性碰撞体。

实验采用三级证据结构：第一，整街区 closed-prism 几何用于验证 TUM2TWIN 城市级数字孪生数据能够进入 FluidX3D 并完成 8 风向筛查；第二，截图对应的核心子域采用 dx=2 m 局部模拟，在 z≈2 m 行人高度层进行时间平均风速比和滞风比例统计；第三，引入 Open-Meteo 2024 小时级 10 m 风向/风速作为风气候代理，形成 8 风向加权结果，用于展示从等权方向矩阵到气候权重解释的工程落地步骤。所有结果均按照 `newly_run`、`preexisting_artifact`、`user_claim` 和 `blocked` 标注证据来源。当前结果支持数字孪生几何准备、CFD-ready 转换、FluidX3D 求解、ParaView/Matplotlib 后处理和行人高度 VR 筛查，但在缺少现场风场、风洞数据、正式年超越概率和污染物源项的条件下，不宣称已完成最终舒适安全分类或预测精度验证。
