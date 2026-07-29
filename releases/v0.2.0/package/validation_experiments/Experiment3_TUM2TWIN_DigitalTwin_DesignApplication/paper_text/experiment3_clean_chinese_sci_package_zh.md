# 实验3清洁中文 SCI 文本包

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题名

真实城市数字孪生数据到 CFD-ready 风环境筛查的应用转化：基于 TUM2TWIN 校园街区的 FluidX3D 实验

## 中文摘要

本文面向真实城市数字孪生数据在城市风环境模拟中的应用落地问题，构建了一个基于 TUM2TWIN Downtown 校园街区的 FluidX3D-native 风环境筛查实验。与前序 AIJ Case A 和 Case E 的基准/验证定位不同，本实验不重新宣称求解器精度，而是评估视觉真实的数字孪生数据如何转化为可体素化、可复现、可审计的 CFD-ready 几何。研究将 UAS/photogrammetry/Rhino 资产用于场景范围、贴图外观和人工一致性审查，将 LoD/OBJ/CAD-derived 闭合几何用于刚性碰撞边界，并通过 Geometry-to-CFD Readiness Index 记录视觉模型与碰撞边界之间的可计算性差异。核心结果显示，研究区行人高度的主要问题是低风速和通风不足，而不是强风风险：S0 基准在 z~2 m 的 mean VR / 低风速比例为 0.076 / 0.934，z~40 m 则为 1.049 / 0.000。Open-Meteo 2024 方向代理加权后的 z~2 m 结果为 0.077 / 0.931，支持方向权重敏感性讨论，但不构成年度舒适/安全合规评价。建筑形态分析进一步表明，风速恢复应被解释为“近立面低速饱和 - 20-50 m 局地恢复 - 风向扇区响应”的分阶段机制，而不是单一高度、占地面积或孔隙率变量的结果。S1/S2 设计敏感性结果为近零或负向，说明几何孔隙面积本身不足以恢复行人层通风，干预应与有效来流扇区、动量入口和压力交换路径耦合。本文贡献在于建立了真实数字孪生数据到 FluidX3D 风环境筛查的证据链，并将校园街区风环境问题转化为可解释的建筑形态诊断；当前证据不支持现场验证、年度规范合规、污染物扩散、GCBTE 闭环或 CityLBM-Grasshopper 端到端运行声明。

## 关键词

城市风环境；数字孪生；TUM2TWIN；FluidX3D；CFD-ready 几何；行人层通风；建筑形态参数

# 实验3清洁中文 SCI 正文段落

evidence_type: newly_run + preexisting_artifact + blocked

## 研究定位

本实验位于 AIJ Case A 和 Case E 之后，其任务不是再次证明求解器精度，而是检验真实城市数字孪生数据能否被转化为风环境模拟和设计解释可使用的实验对象。TUM2TWIN Downtown 数据同时包含 photogrammetry/Rhino/OBJ 视觉资产、语义或 LoD 建筑几何、CAD-derived 模型和立面语义参考。本文将这些数据按功能分层：视觉资产用于真实场景核验和模型范围审查，语义/LoD/CAD-derived 闭合几何用于 CFD/LBM 刚性碰撞边界，FluidX3D 输出用于行人层风速比和形态响应筛查。这一分层是本文的方法核心，因为视觉真实并不等价于可计算、闭合、可体素化的碰撞边界。

## 数据到 CFD-ready 几何

几何准备结果显示，数字孪生底层模型存在明显的“视觉一致性 - CFD 就绪性”差异。GCRI 对 photogrammetry visual STL、core closed-prism collision 和 district prism collision 的评分为 0.455 / 0.925 / 0.918。这说明 photogrammetry 或 3DGS-like 资产适合用于场景真实性、贴图外观和分析对象一致性审查，但不应直接作为最终刚性碰撞边界。相反，经过 z0 对齐、闭合修复、语义分层和 STL/体素化检查的 LoD/OBJ/CAD-derived 几何更适合作为 FluidX3D 输入。由此，数字孪生在风环境研究中的价值不只是“更真实的可视化”，而是提供了可追溯的数据分层和几何转换路径。

## 数值协议

核心算例采用 FluidX3D 筛查协议，数值设定记录为 2 m / 320x390x60 / 5 m s-1 / 1.5e-5 m2 s-1 / 0.52999996 / 8000-10000-12000 / residual not recorded。该协议足以支持筛查级复现和审稿核查，但不能替代残差收敛、完整网格无关性、现场验证或年度舒适概率评估。本文所有速度结果均以 VR = U/Uref 组织，并输出 mean、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 2024 仅作为方向权重代理，用于判断主要低速结论是否对方向权重敏感，不能写成正式风玫瑰或规范合规依据。

## 基准风环境结果

S0 基准结果表明，TUM Downtown 校园核心区的主要行人风环境问题是持续低速和通风不足，而不是强风危险。z~2 m 行人层 mean VR / 低速比例为 0.076 / 0.934，而 z~40 m 为 1.049 / 0.000。这说明上部流场已经恢复，但近地层仍被建筑围合、院落边界和街道连接关系强烈遮蔽。换言之，屋顶以上风速恢复不能被用来替代入口、院落、街道转角和步行路径的独立行人层评估。

## 气候代理权重

Open-Meteo 2024 方向代理加权后的 z~2 m mean VR / 低速比例为 0.077 / 0.931，与八风向等权结果接近。这个结果可支持“当前低速格局对代理方向权重不敏感”的筛查级判断，但不能支持 Lawson、NEN 8100 或 AIJ 年度舒适/安全超越概率评价。若论文需要正式舒适分区，仍需接入校准风气候、阈值超越概率和现场或风洞验证。

## 建筑形态与风环境机制

建筑形态分析表明，该校园街区的风速恢复不宜用 LCZ 标签或单一形态变量概括，而应使用更基础、可迁移的建筑形态参数描述。当前证据支持的机制为 0.0032/0.0056; rho sector=-0.396, height=-0.351; persistent/recovery/reactive range=0.0016/0.0189/0.0214; best rule n=5 recovery=0.0065。更具体地说，near/local/recovery mean VR 0.003182 / 0.005560 / 0.002378; best rule mean_height_m_tertile=low + elongation_ratio_tertile=high + relative_enclosure_score_tertile=high / n=5 / mean recovery 0.0065 / top share 1.000; height/sqrt(area) Cliff delta -0.577；同时，range mean 0.008655; stage ranges persistent/recovery/reactive 0.001579 / 0.018941 / 0.021421; stage Kruskal p 1.02e-15; rho mean_height -0.363, sector_enclosure -0.362。这意味着 0-20 m 近立面带主要反映低速饱和，20-50 m 局地背景带才更能暴露建筑形态造成的恢复差异。有效通风恢复不仅表现为更高的局地 mean VR，还应表现为对不同来流扇区的响应能力。因而，建筑高度、平面延展、局地建成比例和 50 m 扇区围合度需要组合解释，而不能被简化为单一高度或孔隙率效应。

## 设计敏感性

S1/S2 干预结果提供的是负向设计证据，而不是优化成功。S1 的 z~2 m mean VR / 低速比例变化为 -0.000213 / 0.000233，S2 为 -0.000466 / 0.000633，方向性局部 trade-off 为 315 deg / 0.002374 / 0.006646。这说明单条 relief corridor 或三通道 network porosity 均未恢复全局行人层通风；即使局部单元出现方向性响应，新开敞单元仍嵌在低速背景中。由此得到的设计认识是：校园核心区的通风改善不能停留在增加孔隙面积或通道数量，而应将开口布置、有效来流扇区、动量入口、压力交换路径和局地围合连续性共同设计。

## 结论

本实验证明，TUM2TWIN 真实校园数字孪生数据可以通过视觉审查、语义/LoD 几何重构、闭合碰撞体生成、FluidX3D 八风向筛查和 ParaView/Rhino 人工审核，形成可复现的城市风环境应用实验。最稳妥的论文定位是：FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation。当前证据支持数字孪生数据转换路径、行人层低速筛查、建筑形态机制解释和 S1/S2 负向设计敏感性结论；不支持现场验证、风洞闭环、年度舒适/安全合规、污染物扩散预测、GCBTE 误差闭合、CityLBM-Grasshopper 端到端执行或成功设计优化声明。
