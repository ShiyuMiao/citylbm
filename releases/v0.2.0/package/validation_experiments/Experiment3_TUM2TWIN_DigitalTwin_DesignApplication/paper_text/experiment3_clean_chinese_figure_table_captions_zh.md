# 实验3清洁中文图表说明

evidence_type: newly_run + preexisting_artifact + blocked

## Fig. E3-1

TUM Downtown 校园核心区行人高度 FluidX3D/VTK 风速比筛查图。该图来自 dx=2 m、八个来流方向、三个后 spin-up 样本的 core closed-prism collision 算例，用于人工审查低速区、方向一致性和建筑周边滞风格局。该图支持筛查级低通风解释，不支持年度舒适合规、现场验证或污染物扩散结论。

## Fig. E3-2

基础建筑形态参数与 20-50 m 局地背景风速响应的多变量稳健性分析。图中排序回归系数和置换重要性用于说明局地围合、平均高度和综合围合指标比单体占地面积、延展率或紧凑度更适合解释样本内风速差异。由于交叉验证解释力有限，该图应作为可解释筛查证据，而不是高精度预测模型。

## Fig. E3-3

S1/S2 设计敏感性场景在行人高度的方向性局部 trade-off。该图比较不同来流方向下 common open cells 的风速比变化。S2 的局部正响应略强于 S1，但改善单元稀疏，新开敞单元仍处于低速状态。因此该图是负向设计证据，说明几何孔隙面积本身不足以恢复校园核心区行人层通风。

## Fig. E3-4

0-20 m 近立面带到 20-50 m 局地背景带的风速恢复阈值规则筛查。分析在同一组 101 个建筑构件上比较近立面与局地背景响应，并提取样本内 tertile 组合规则。该图只能支持数字孪生样本内设计筛查，不能作为通用规范阈值或现场验证结论。

## Fig. E3-S5

20-50 m 局地背景带的建筑形态方向性指纹分析。该图将 101 个保留建筑构件的八风向 mean VR 范围、方向响应比、最佳响应风向与基础形态参数和阶段转化类型关联起来。persistent shelter 构件同时具有较低 mean VR 和较低方向范围，而 near-to-context recovery 与 directionally reactive 构件表现出更强的来流扇区响应。该图支持数字孪生设计筛查，不支持现场验证的因果阈值或年度风玫瑰合规评价。

## Table E3-1

实验3面向论文的一页式关键结果矩阵。该表整合 S0 基准、垂向恢复、Open-Meteo 代理权重、S1/S2 设计敏感性、方向性 trade-off、形态稳健性、阶段转化、方向性指纹和 GCRI，并逐行给出 evidence_type、来源文件和论文安全表述。

## Table E3-2

实验3完成度与论文可用性审计矩阵。该表区分已完成、筛查级完成、需弱化和阻塞的模块，明确标注现场数据、年度舒适合规、污染物扩散、GCBTE 和 CityLBM-Grasshopper 端到端执行的缺口。

## Table E3-3

Geometry-to-CFD Readiness Index 评分表。该表比较 photogrammetry visual mesh、core closed-prism collision 和 district prism collision 在水密性、非流形错误、语义层完整性、坐标/单位一致性、STL 导出和体素化成功等方面的就绪度，说明视觉真实与 CFD 碰撞边界可用性是不同属性。
