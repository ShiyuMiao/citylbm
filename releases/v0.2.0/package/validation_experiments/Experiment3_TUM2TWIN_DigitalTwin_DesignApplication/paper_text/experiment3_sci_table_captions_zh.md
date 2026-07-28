# 实验3 SCI 表题说明

evidence_type: newly_run + preexisting_artifact + blocked

These captions are tied to archived source artifacts. They should be edited only for journal style, not for claim strength, unless new evidence is added.

## Table E3-1

表 E3-1. 实验3面向论文的一页式关键结果矩阵。表格把 S0 基准、竖向恢复、Open-Meteo 方向代理敏感性、S1/S2 设计敏感性、方向性 trade-off、形态稳健性、阈值筛查和 GCRI 几何就绪度整合到同一证据框架，并逐行给出 evidence_type、来源文件和论文安全表述。

- Asset: `figures/final_integrated_key_result_matrix.csv`
- Source data: `compiled from FluidX3D metrics, Open-Meteo proxy weights, morphology CSVs, design-sensitivity comparisons and GCRI`
- Evidence type: `newly_run + preexisting_artifact + blocked`
- Boundary: rows with blocked components must retain boundary wording

## Table E3-2

表 E3-2. 实验3完成度与论文可用性审计矩阵。表格区分已完成、可写为筛查结论、需要弱化和仍受阻的模块，尤其标注实测风场、年度舒适度合规、污染物扩散、GCBTE 和 CityLBM-Grasshopper 端到端运行的缺口。

- Asset: `figures/experiment3_completion_audit_matrix.csv`
- Source data: `reports/experiment3_completion_audit_and_paper_readiness.md`
- Evidence type: `newly_run + blocked`
- Boundary: blocked rows must not be converted into completed results

## Table E3-3

表 E3-3. Geometry-to-CFD Readiness Index (GCRI) 评分表。表格比较摄影测量视觉网格、核心闭合棱柱碰撞几何和街区棱柱碰撞几何在水密性、非流形错误、语义层完整性、坐标/单位一致性、STL 导出和体素化成功等子项上的 0-1 就绪度，说明视觉真实度与 CFD 碰撞边界可用性是不同属性。

- Asset: `manifests/gcri_scoring_table.csv`
- Source data: `reports/geometry_to_cfd_readiness_index_results.md; reports/cfd_ready_geometry_qa.md`
- Evidence type: `newly_run`
- Boundary: GCRI is a paper-internal readiness score, not an external standard
