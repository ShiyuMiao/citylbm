# Morphology Threshold Design-Rule Paragraph

evidence_type: newly_run

在进一步的形态阈值分析中，本研究将同一批 101 个中心区建筑构件的近立面带（0-20 m）与局地背景带（20-50 m）进行配对比较，并定义 `context_recovery_delta_vr = mean_VR_20-50m - mean_VR_0-20m`。结果显示，近立面带平均 VR 仅为 `0.0032`，而 20-50 m 局地背景带平均 VR 上升至 `0.0056`，说明本案例中建筑形态对风环境的可解释性主要出现在脱离贴壁遮蔽后的局地交换范围，而不是直接贴近立面的 0-20 m 范围。基于基础形态参数的 tertile 规则筛选进一步表明，最佳简单组合规则为 `mean_height_m=low_tertile + elongation_ratio=high_tertile`，其平均恢复量为 `0.0057`，top-recovery 构件占比为 `0.857`；同时，恢复量与 `height_to_sqrt_area` 的单调相关最强且为负，说明较高的相对竖向尺度会抑制局地风速恢复。由此，本实验在传统“围合削弱行人层风速”的认识上补充了一个数字孪生应用层面的判断：对校园型连续街区而言，通风潜力不宜仅依据单体建筑面积、伸长率或孔隙开口面积来判断，而应在 20-50 m 尺度上同时识别局地暴露度、竖向体量和外部动量进入条件。该结论是 FluidX3D 模拟和统计筛查结果，不等同于经实测验证的通用阈值或法规级舒适性判定；其中 `mean_height_m=low_tertile + elongation_ratio=high_tertile` 仅代表本样本内的小规模高恢复子集，而不是可直接外推的设计规范。
