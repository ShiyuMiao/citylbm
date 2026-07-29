# 实验 3 局限性与后续验证路线图段落

evidence_type: newly_run + preexisting_artifact + blocked

本研究的局限性不是实验失败，而是筛查型数字孪生风环境研究与工程合规评价之间的证据边界。当前 TUM2TWIN 实验已经完成数据层分离、CFD-ready 几何准备、FluidX3D 八风向筛查、ParaView/Rhino 审查资产、建筑形态机制解释和 S1/S2 设计敏感性测试，但尚未形成现场实测或风洞闭环。因此，本文只能主张校园核心区存在行人层低速与通风不足的筛查证据，不能主张实测验证后的预测精度。

第二个边界来自气候输入。Open-Meteo 2024 方向权重用于检验低速结论对代理风向权重的敏感性，但它不是校准后的场地风玫瑰，也不能支撑 Lawson、NEN 8100 或 AIJ 年度超越概率评价。若后续论文或工程报告需要转向正式舒适/安全合规，必须接入多年气象站或现场风观测，定义活动类型阈值，并计算行人高度受体点的年度超越概率。

第三个边界来自数值协议。dx = 2 m、八风向和三个后 spin-up 样本足以支持筛查级复现，但 residual history、完整网格无关性和更长时间统计尚未闭合。后续工作应保存监测点时间序列，补充 3 m/2 m/1 m 或等效分辨率敏感性，并报告网格收敛或不确定性范围。只有在这一步之后，数值方法部分才适合从“透明筛查协议”升级为“更强数值收敛证据”。

第四个边界与设计应用有关。S1/S2 给出的不是优化成功，而是有价值的负向敏感性证据：单通道 relief corridor 与 network porosity 均未改善全局行人层风速。这提示后续 S3-Sn 不应继续机械增加孔隙面积，而应围绕有效来流扇区、动量入口、压力交换路径和局地围合连续性设计风向耦合干预。若这些方案能够在同一 FluidX3D 协议下改善 mean VR 并降低低速比例，设计应用结论才可以从“筛除无效假设”升级为“提出有效干预策略”。

第五个边界是数字孪生模型本身。本文已经证明视觉真实与 CFD 碰撞就绪不同，但 GCBTE 尚未被计算，CityLBM-Grasshopper 端到端也尚未实跑。因此，当前最稳妥的论文定位仍是 FluidX3D-native digital-twin-to-CFD screening with CityLBM-compatible geometry preparation。若要进一步强化数字孪生创新性，需要从 3DGS 或影像重建结果中提取独立碰撞边界，并以 LoD3/闭合棱柱为 ground truth 计算 IoU、Chamfer/Hausdorff 和 voxel-mask agreement；若要强化 CityLBM 应用性，则需要补充 Grasshopper 文件、运行截图、输入输出日志和结果图像。
