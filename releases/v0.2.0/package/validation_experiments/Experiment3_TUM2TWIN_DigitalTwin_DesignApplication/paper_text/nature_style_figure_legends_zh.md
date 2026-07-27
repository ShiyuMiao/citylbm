# Nature 风格图注草稿（中文）

**图 1 | TUM2TWIN 数字孪生数据到 CFD 风环境模拟的转译流程。**
a，TUM2TWIN photogrammetry/Rhino 视觉资产、LoD3 语义城市模型、闭合 CFD 碰撞边界、FluidX3D 工况和风环境指标之间的证据链。b，视觉 photogrammetry/Rhino 范围与核心 CFD-ready STL 范围对比，二者覆盖同一 TUM Downtown 核心街区尺度。c，密集视觉 photogrammetry mesh 与 LoD3-derived closed prism 之间的三角面数量差异。d，非 watertight 视觉 STL 与闭合语义棱柱碰撞体之间的边界可用性差异。e，photogrammetry/Rhino 与 LoD3-derived prism 在可视化参照、语义来源、闭合碰撞和 simulation-ready 方面的 geometry-to-CFD readiness 逻辑。Source data are provided as a Source Data file.

**图 2 | 核心 TUM Downtown 街区行人层方向稳健停滞特征。**
a，z≈2 m 行人高度 Open-Meteo 2024 风气候代理加权停滞概率分布，停滞定义为 VR<0.2，白色区域为固体碰撞单元。b，八个 FluidX3D 风向下 VR 的方向标准差，表示风向敏感性。c，z≈2 m 各风向平均 VR 与 VR<0.2 面积比例响应。d，等权八风向与 Open-Meteo 加权结果下的垂直 VR 恢复和停滞比例衰减。e，稳健性指标汇总，显示开放行人层单元中 91.5% 在至少 6/8 个风向下停滞，87.2% 在全部八个风向下停滞，而反复加速区域仅约 2.5%。FluidX3D 计算采用 dx=2 m、八风向和每风向三个 spin-up 后时间样本。Source data are provided as a Source Data file.
