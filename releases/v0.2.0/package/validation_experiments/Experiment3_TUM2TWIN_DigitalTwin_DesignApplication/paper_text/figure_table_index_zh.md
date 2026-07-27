# 图表索引与论文插图建议（中文）

## 建议图件

**图 1：TUM2TWIN photogrammetry 视觉模型与研究区范围。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_textured_mesh_topdown_audit.png`，说明 UAS photogrammetry mesh 主要承担真实外观核验和场景定位功能。若需展示用户手动下载的 Rhino 包，可补充 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_rhino_layered_geometry_scope_audit.png`。

**图 2：核心街区 CFD-ready 闭合碰撞几何 QA。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\core_photogrammetry_extent_prism_collision_audit.png`。图注应强调该几何由官方 LoD3 OBJ 衍生，覆盖截图对应的核心街区，作为 dx=2 m 行人高度模拟的主要碰撞边界。

**图 3：整街区 closed-prism 几何筛查。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\district_prism_collision_audit.png`，或结合 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_district_prism_8dir_medium4m_10k_vr_panel_z8m.png` 展示全街区可计算性和中等分辨率筛查结果。

**图 4：photogrammetry STL 作为碰撞边界的反例。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_user_photo_wd000_dx2m_2k_voxel_vr_audit.png`。图注应明确该结果不是正式风环境结论，而是证明视觉网格在体素化中会产生非封闭、片状或碎片化固体掩膜。

**图 5：核心街区八风向行人高度风速比。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`。这是当前最强的本机新运行风场证据，包含 dx=2 m、八风向、三时间样本平均结果。

**图 6：等权重平均行人高度风速比。**
建议使用 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`，用于展示行人高度整体低风速区与局部加速路径。

**图 7：Open-Meteo 2024 风气候代理权重与加权风速比分布。**
建议组合 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\open_meteo_tum_city_campus_2024_windrose_8dir_velocity_to.png` 与 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`。图注中应写明该风玫瑰为气候代理，不是现场实测。

**图 8：ParaView 人工审核管线。**
建议在本机打开 `F:\citylbm_fluidx3d_workspace\tum2twin_case\paraview\tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm` 后手动截图，展示 STL、VTK 和 z=2 m 切片同屏审核。若不手动截图，论文中可仅将 ParaView 作为可复现审核工具写入方法或补充材料。

## 建议表格

**表 1：TUM2TWIN 数据层与 CFD 用途映射。**
数据源包括 UAS photographs、UAS photogrammetry mesh、CityGML/LoD3 building models、CAD/OBJ/Rhino 模型和 pc-fac benchmark。字段建议包含 source、main use、CFD role、evidence_type、limitation。

**表 2：几何 QA 与 CFD readiness。**
数据来自 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\geometry_manifest.csv`、`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\geometry_qa_core_photogrammetry_extent_prism.json` 和 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\reports\cfd_ready_geometry_qa.md`。建议列出 bbox、triangle count、watertight 状态、boundary edges、用途和证据类型。

**表 3：核心街区八风向 FluidX3D 工况。**
数据来自 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\reports\fluidx3d_core_prism_timesampled_8dir_dx2m_report.md`。字段建议包含 dx、domain resolution、wind direction、spinup steps、sample steps、sample count、runtime、output VTK。

**表 4：行人高度风速比统计。**
数据来自 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv` 和 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv`。核心列包括 height、VR_mean、VR_P75、VR_P90、VR_P95、VR_max、stagnation area ratio。

**表 5：证据边界清单。**
数据来自 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\evidence_inventory.csv` 与 `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\reports\claim_boundary.md`。建议将每条论文主张标注为 newly_run、preexisting_artifact、user_claim 或 blocked。
