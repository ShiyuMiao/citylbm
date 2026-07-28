# Experiment 3 SCI 摘要、Highlights 与关键词

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题目

真实校园数字孪生数据到 CFD-ready 风环境筛查：TUM2TWIN、FluidX3D 与建筑形式机制解释

## 摘要

真实城市数字孪生数据为建筑风环境研究提供了高真实感三维场景，但视觉真实并不等同于 CFD 碰撞边界就绪。本文以 TUM2TWIN Downtown 校园核心区为对象，构建了从 photogrammetry/Rhino/3DGS-like 视觉审查层、LoD/OBJ/CAD-derived 语义几何层到 FluidX3D 碰撞边界层的应用转化流程。结果显示，photogrammetry visual STL 的 Geometry-to-CFD Readiness Index 为 0.455，而 core closed-prism collision 与 district prism collision 分别达到 0.925 和 0.918，说明数字孪生底层模型需要按可视化、语义和计算边界功能分层使用。基于 dx = 2 m、8 个风向和 3 个后 spin-up 样本的 FluidX3D 筛查结果表明，研究区 z~2 m 行人层 mean VR / 低速比例为 0.076 / 0.934，而 z~40 m 为 1.049 / 0.000，主要问题是行人层通风不足而非强风危险。建筑形式分析进一步揭示，0-20 m 近立面带处于低速饱和状态，20-50 m 局地上下文带才显露形态恢复差异；50 m 扇区围合度、平均高度和复合围合分数是主要抑制性描述符。S1/S2 设计敏感性结果显示，单纯增加 relief corridor 或 network porosity 未改善全局行人层风速，说明孔隙面积必须与有效来流扇区、动量入口和压力交换路径耦合。本文贡献在于提出并验证了一条真实数字孪生街区到 CFD-ready 风环境筛查的可审计路径，以及一种面向校园更新的建筑形式-风环境分阶段解释框架。当前结论属于 FluidX3D/数字孪生筛查证据，不构成实测验证、年度舒适安全合规或污染物扩散预测。

## Highlights

- 区分 TUM2TWIN 视觉模型、语义几何和 CFD 碰撞边界三类功能层。
- FluidX3D 筛查显示校园核心区主要问题是行人层低风速与通风不足。
- 建筑形式影响表现为近立面低速饱和、20-50 m 局地恢复和风向响应。
- S1/S2 负向设计敏感性说明，孔隙面积 alone 不足以恢复通风。

## 关键词

数字孪生；城市风环境；FluidX3D；TUM2TWIN；CFD-ready 几何；行人层通风；建筑形态参数；校园微气候

## 图文摘要说明

建议图文摘要采用三段式流程图：左侧为 TUM2TWIN photogrammetry/Rhino/LoD 数据分层，中间为 closed-prism collision geometry 与 FluidX3D 八风向筛查，右侧为行人层低速结果、20-50 m 建筑形式恢复机制和 S1/S2 负向设计证据。图文摘要应避免使用 “validated prediction” 或 “comfort compliance” 等字样，除非后续加入外部验证证据。
