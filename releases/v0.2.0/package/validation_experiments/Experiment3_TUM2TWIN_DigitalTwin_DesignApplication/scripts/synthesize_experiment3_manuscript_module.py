from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"


def write_text_lf(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def read_value(matrix: pd.DataFrame, claim_layer: str) -> str:
    row = matrix[matrix["claim_layer"] == claim_layer]
    if row.empty:
        raise ValueError(f"missing matrix claim layer: {claim_layer}")
    return str(row.iloc[0]["value"])


def main() -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    MAN.mkdir(parents=True, exist_ok=True)

    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    refs = pd.read_csv(MAN / "verified_references_for_sci_discussion.csv")
    cmap = pd.read_csv(MAN / "citation_to_claim_map_sci_discussion.csv")
    audit = pd.read_csv(FIG / "experiment3_completion_audit_matrix.csv")

    baseline = read_value(matrix, "S0 baseline pedestrian screening")
    vertical = read_value(matrix, "Vertical recovery")
    climate = read_value(matrix, "Climate-proxy sensitivity")
    s1 = read_value(matrix, "S1 design sensitivity")
    s2 = read_value(matrix, "S2 design sensitivity")
    trade = read_value(matrix, "Directional local trade-off")
    morph = read_value(matrix, "Morphology robustness")
    threshold = read_value(matrix, "Morphology threshold design rule")
    gcri = read_value(matrix, "Geometry-to-CFD readiness")

    claims = [
        {
            "claim_id": "M1",
            "section": "Method",
            "claim": "TUM2TWIN layers are separated into visual reference, semantic/collision geometry and CFD/LBM simulation inputs.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source": "reports/data_source_and_download_manifest.md; reports/cfd_ready_geometry_qa.md; manifests/gcri_scoring_table.csv",
            "claim_readiness": "paper_ready",
        },
        {
            "claim_id": "R1",
            "section": "Results",
            "claim": "S0 baseline pedestrian layer is dominated by low speed, while the upper layer recovers.",
            "evidence_type": "newly_run",
            "source": "figures/final_integrated_key_result_matrix.csv",
            "claim_readiness": "paper_ready_as_screening",
        },
        {
            "claim_id": "R2",
            "section": "Results",
            "claim": "Open-Meteo 2024 weighting is a climate-proxy sensitivity layer, not an annual comfort assessment.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source": "figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim_id": "R3",
            "section": "Results",
            "claim": "Basic morphology variables are interpretable screening descriptors; sector enclosure ranks above single-building footprint/elongation.",
            "evidence_type": "newly_run",
            "source": "figures/basic_morphology_multivariate_robustness.csv; reports/basic_morphology_multivariate_robustness.md",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim_id": "R3b",
            "section": "Results",
            "claim": "Near-to-context recovery analysis extracts sample-internal morphology threshold rules for design screening, not externally validated design thresholds.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_threshold_rule_screening.csv; reports/morphology_threshold_design_rule_analysis.md; paper_text/morphology_threshold_design_rule_conclusion_zh.md",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim_id": "R4",
            "section": "Results",
            "claim": "S1/S2 are negative design-sensitivity evidence rather than successful optimization.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "claim_readiness": "paper_ready_negative_result",
        },
        {
            "claim_id": "L1",
            "section": "Limitations",
            "claim": "Field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported.",
            "evidence_type": "blocked",
            "source": "reports/claim_boundary.md; reports/experiment3_completion_audit_and_paper_readiness.md",
            "claim_readiness": "must_state_as_boundary",
        },
    ]
    pd.DataFrame(claims).to_csv(MAN / "experiment3_manuscript_module_claims.csv", index=False, encoding="utf-8-sig", lineterminator="\n")

    reference_lines = []
    for _, row in refs.iterrows():
        doi = "" if pd.isna(row.get("doi")) or not str(row.get("doi")).strip() else f" doi:{row['doi']}."
        reference_lines.append(f"[{row['ref_id']}] {row['authors']} ({row['year']}). {row['title']}. {row['source']}.{doi}")

    figure_table_rows = [
        {
            "callout_id": "Fig. E3-1",
            "recommended_file": "figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png",
            "purpose": "Baseline pedestrian-layer spatial VR/stagnation pattern for manual review.",
        },
        {
            "callout_id": "Fig. E3-2",
            "recommended_file": "figures/basic_morphology_multivariate_rank_model_importance.png",
            "purpose": "Morphology ranking: rank-regression coefficients and permutation importance.",
        },
        {
            "callout_id": "Fig. E3-3",
            "recommended_file": "figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png",
            "purpose": "S1/S2 directional local trade-off summary.",
        },
        {
            "callout_id": "Fig. E3-4",
            "recommended_file": "figures/morphology_threshold_recovery_rule_summary.png",
            "purpose": f"Near-to-context morphology threshold design-rule screening: {threshold}.",
        },
        {
            "callout_id": "Table E3-1",
            "recommended_file": "figures/final_integrated_key_result_matrix.csv",
            "purpose": "One-page paper-facing result matrix with evidence sources.",
        },
        {
            "callout_id": "Table E3-2",
            "recommended_file": "figures/experiment3_completion_audit_matrix.csv",
            "purpose": "Paper-readiness and blocked-claim audit.",
        },
        {
            "callout_id": "Table E3-3",
            "recommended_file": "manifests/gcri_scoring_table.csv",
            "purpose": "Geometry-to-CFD readiness scoring for visual and collision geometries.",
        },
    ]
    figure_table = pd.DataFrame(figure_table_rows)
    figure_table.to_csv(MAN / "experiment3_manuscript_figure_table_plan.csv", index=False, encoding="utf-8-sig", lineterminator="\n")

    zh = f"""# 实验3 SCI 论文模块：TUM2TWIN 数字孪生校园风环境应用

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题名

真实城市数字孪生数据到 CFD-ready 风环境筛查的应用转化：基于 TUM2TWIN 校园核心区的 FluidX3D 实验

## 研究定位

Case A 与 Case E 已承担求解器基准与前序验证角色；实验3不重新宣称求解器精度，而聚焦真实数字孪生城市数据如何进入风环境模拟与设计解释。本文将 TUM2TWIN 的 UAS/photogrammetry 视觉资产、LoD/OBJ 语义几何、Rhino/OBJ 管理模型和闭合 STL 碰撞边界分层使用，以避免把视觉真实误写为 CFD-ready。该定位与行人风环境 CFD 研究中对不确定性、舒适评价链条和校园尺度决策支持的要求一致 [R1,R5-R7]。

## 方法

本文首先对 TUM2TWIN 数据进行功能分层。UAS photogrammetry mesh 与纹理模型用于场景范围核验、真实外观对照和 Rhino/ParaView 手动审查；语义建筑数据和 LoD/CAD-derived 几何用于生成闭合刚性碰撞边界；用户 photogrammetry STL 作为视觉参考和几何可用性反例保留，不直接作为最终 LBM 碰撞体。几何就绪性通过 GCRI 记录，其中 photogrammetry visual STL / core closed-prism collision / district prism collision 的得分分别为 {gcri}。

FluidX3D 模拟采用 dx=2 m 的核心子域，包含 8 个来流方向，并在 spin-up 后抽取 8000、10000 和 12000 steps 三个样本。后处理先进行同风向时间平均，再输出八风向等权结果、Open-Meteo 2024 风向代理加权结果、不同高度层 VR 统计、建筑距离/形态关联和 S1/S2 设计敏感性比较。评价指标包括 mean VR、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 仅用于方向权重敏感性，不用于正式年度舒适概率评价。

## 实验设置

研究对象为 TUM Downtown photogrammetry 视觉范围对应的校园核心街区。S0 为 core closed-prism collision baseline；S1 为单条 light relief corridor；S2 为三通道 network porosity。S1/S2 与 S0 共享 dx=2 m、8 风向和三样本后处理协议，因此比较结果可解释为几何敏感性，而不是不同求解设置造成的差异。图表调用建议见 `manifests/experiment3_manuscript_figure_table_plan.csv`。

## 结果

S0 基准结果表明，行人高度的主导问题是通风不足而非强风危险。z≈2 m mean VR / 低速比例为 {baseline}；z≈40 m mean VR / 低速比例为 {vertical}。这一竖向差异说明屋面以上的流速恢复不能替代校园步行层、入口、院落与街道连通空间的独立评价。Open-Meteo 2024 方向代理加权后 z≈2 m mean VR / 低速比例为 {climate}，与八风向等权平均接近，支持“低速结论对代理方向权重不敏感”的筛查性判断，但不支持年度 Lawson/NEN/AIJ 舒适安全合规结论 [R5,R8-R10]。

建筑形式分析显示，0-20 m 近立面带近乎整体滞风，20-50 m 局地环境带更能反映风速恢复差异。多变量稳健性结果为 {morph}，说明基础形态参数的预测力有限，但变量排序仍有解释意义：局地扇区围合和平均高度比单体 footprint、elongation 或 perimeter-area compactness 更接近行人层风速恢复机制。本文由此将传统“高密度/围合削弱通风”的认识转化为可定位的校园尺度诊断：关键不只是建筑有多高或多大，而是 30-50 m 范围内是否存在连续围合、动量入口不足和院落-街道压力交换受阻 [R2-R4]。

S1/S2 设计敏感性实验进一步限定了设计结论。S1 在 z≈2 m 的 mean VR / 低速比例变化为 {s1}；S2 为 {s2}。方向性 trade-off 显示 S2 的局部响应为 {trade}。因此，S1/S2 均不能被写成成功优化方案；它们的价值在于说明几何孔隙面积本身不足以恢复行人层通风，开口必须与有效来流扇区、动量入口和压力交换路径耦合。

## 讨论

相较传统理想街谷或简化建筑群研究，本实验的新增价值不在于声称更高预测精度，而在于将真实数字孪生数据的可视化层、语义层和碰撞层分离，并记录从视觉一致性到 CFD-ready 的证据链。TUM2TWIN 的 photogrammetry/3DGS-like 资产提供真实外观和场景审查价值，但最终碰撞边界必须由语义/LoD/CAD-derived 闭合几何生成 [R11,R12]。风环境结论也应从“是否形成强风区”转向“校园核心区是否存在稳定通风不足及其局地形态原因”。

## 局限性

本文不宣称实测风场验证、风洞闭环、正式年度舒适/安全合规、污染物扩散预测、S3-Sn 正向优化、GCBTE 误差闭合或 CityLBM-Grasshopper 端到端运行。Open-Meteo 方向权重是气候代理，不是现场风玫瑰；S1/S2 是负向设计敏感性证据，不是最终设计方案；形态统计是解释性筛查，不是可替代 CFD 的高精度预测模型。

## 可直接用于摘要的结论句

本实验表明，TUM2TWIN 数字孪生数据能够通过语义闭合几何转化为 FluidX3D 可用的真实校园街区风环境筛查流程；在当前核心区，模拟结果显示行人层持续低速、上部流场恢复和局地围合控制有限风速恢复，且 S1/S2 负向敏感性说明设计干预应从简单增加孔隙面积转向风向扇区耦合的动量入口和压力交换连续性。

## 参考文献键

{chr(10).join(reference_lines)}
"""
    write_text_lf(PAPER / "experiment3_sci_manuscript_module_zh.md", zh)

    en = f"""# Experiment 3 SCI Manuscript Module: TUM2TWIN Digital-Twin Campus Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Suggested Title

From real urban digital-twin data to CFD-ready wind screening: a FluidX3D experiment on the TUM2TWIN campus core

## Study Positioning

Cases A and E support the preceding solver benchmark layer. Experiment 3 does not re-claim solver accuracy; it tests whether a real urban digital twin can be converted into CFD-ready geometry, simulated in FluidX3D and interpreted as a campus wind-design screening case. The workflow separates UAS/photogrammetry visual assets, semantic LoD/OBJ geometry, Rhino/OBJ management models and closed STL collision boundaries. This positioning follows the evidence boundary required by pedestrian-wind CFD and campus decision-support studies [R1,R5-R7].

## Methods

TUM2TWIN data are divided by function. UAS photogrammetry and textured meshes support scene audit and visual consistency checks; semantic building data and LoD/CAD-derived geometry support closed collision-boundary construction; the user photogrammetry STL is retained as a visual reference and geometry-readiness counterexample rather than as the final LBM collision body. Geometry readiness is recorded by GCRI, with photogrammetry visual STL / core closed-prism collision / district prism collision scores of {gcri}.

The FluidX3D core-domain simulation uses dx=2 m, eight inflow directions and three post-spin-up samples at 8000, 10000 and 12000 steps. Post-processing first averages the three samples per direction, then computes equal-weighted eight-direction statistics, Open-Meteo 2024 proxy direction weighting, vertical VR profiles, morphology-response relations and S1/S2 design-sensitivity comparisons. Metrics include mean VR, P75/P90/P95, VR<0.2 low-speed ratio, VR>0.6 acceleration ratio and VR>1.0 high-speed ratio. The Open-Meteo layer is used only as proxy directional sensitivity, not formal annual comfort probability.

## Experimental Setup

The study object is the TUM Downtown campus core corresponding to the photogrammetry visual block. S0 is the core closed-prism collision baseline; S1 is a single light relief corridor; S2 is a three-corridor network-porosity case. S1/S2 share the dx=2 m, eight-direction and three-sample post-processing protocol with S0, so their comparison isolates geometry sensitivity within the present screening design.

## Results

The S0 baseline shows pedestrian-layer ventilation insufficiency rather than a strong-wind hazard. At z~2 m, mean VR / low-speed ratio is {baseline}; at z~40 m it becomes {vertical}. The vertical contrast shows that above-roof recovery cannot be used as a surrogate for campus pedestrian-space ventilation. Open-Meteo 2024 proxy weighting gives z~2 m mean VR / low-speed ratio of {climate}, close to the equal-weighted result. The low-speed conclusion is therefore stable under this proxy weighting, but this does not support annual Lawson/NEN/AIJ compliance [R5,R8-R10].

The morphology analysis translates traditional canyon/canopy reasoning into a local digital-twin diagnosis. The 0-20 m facade-adjacent band is almost uniformly sheltered, while the 20-50 m local-context band better distinguishes wind recovery. The multivariate robustness result is {morph}; thus morphology variables are useful as interpretable screening descriptors but not as a high-accuracy surrogate model. Sector enclosure and mean height rank above individual footprint, elongation and perimeter-area compactness, indicating that local enclosure, wind-entry opportunity and pressure-exchange continuity are more informative than isolated building shape [R2-R4].

The S1/S2 design-sensitivity sequence further narrows the design claim. S1 changes z~2 m mean VR / low-speed ratio by {s1}; S2 changes them by {s2}. Directional trade-off analysis gives {trade}. S1/S2 should therefore be interpreted as negative design evidence: geometric opening area alone does not recover pedestrian ventilation unless aligned with effective inflow sectors, momentum entry and pressure-exchange paths.

## Discussion

Compared with idealized canyon or simplified urban-block studies, the added value of this experiment is not a claim of higher predictive accuracy but a traceable digital-twin-to-CFD conversion pathway. Photogrammetry and 3DGS-like assets provide visual realism and scene audit capability, whereas final FluidX3D/CityLBM collision boundaries require semantic or LoD/CAD-derived closed geometry [R11,R12]. The wind-design interpretation also shifts from strong-wind danger toward persistent ventilation insufficiency and its local morphology controls.

## Limitations

The module does not claim field validation, wind-tunnel closure, formal annual comfort/safety compliance, pollutant dispersion, positive S3-Sn optimization, GCBTE closure or CityLBM-Grasshopper end-to-end execution. Open-Meteo is a climate proxy, not a measured site wind rose; S1/S2 are negative sensitivity tests, not final design proposals; and morphology statistics are explanatory screening evidence, not a replacement for CFD or measurement.

## Abstract-Ready Takeaway

The experiment demonstrates that TUM2TWIN digital-twin data can be transformed through semantic closed geometry into a FluidX3D-ready campus wind-screening workflow. The tested campus core shows persistent pedestrian-layer low-speed conditions, upper-layer flow recovery and local enclosure-controlled wind recovery, while the negative S1/S2 sensitivity results indicate that design intervention should move from simple porosity area toward wind-sector-coupled momentum entry and pressure-exchange continuity.

## Reference Key

{chr(10).join(reference_lines)}
"""
    write_text_lf(PAPER / "experiment3_sci_manuscript_module_en.md", en)

    callout_md = "# 实验3图表调用与论文嵌入计划\n\n"
    callout_md += "evidence_type: newly_run + preexisting_artifact\n\n"
    callout_md += figure_table.to_markdown(index=False)
    callout_md += "\n\n图表使用边界：这些图表支持筛查、形态解释和证据边界，不支持实测验证、年度舒适合规或污染物扩散结论。\n"
    write_text_lf(PAPER / "experiment3_figure_table_callouts_zh.md", callout_md)

    audit_md = "# Experiment 3 Manuscript Module Audit\n\n"
    audit_md += "evidence_type: newly_run + preexisting_artifact + blocked\n\n"
    audit_md += "## Claim Inventory\n\n"
    audit_md += pd.DataFrame(claims).to_markdown(index=False)
    audit_md += "\n\n## Upstream Citation-to-Claim Map\n\n"
    audit_md += cmap.to_markdown(index=False)
    audit_md += "\n\n## Completion Audit Summary\n\n"
    audit_md += audit.to_markdown(index=False)
    audit_md += "\n\nVerification: the module is suitable as an Experiment 3 manuscript section, but not as proof of field validation, annual comfort compliance, pollutant dispersion, GCBTE closure or CityLBM-GH end-to-end execution.\n"
    write_text_lf(REP / "experiment3_manuscript_module_audit.md", audit_md)

    print("wrote", PAPER / "experiment3_sci_manuscript_module_zh.md")
    print("wrote", PAPER / "experiment3_sci_manuscript_module_en.md")
    print("wrote", PAPER / "experiment3_figure_table_callouts_zh.md")
    print("wrote", REP / "experiment3_manuscript_module_audit.md")
    print("wrote", MAN / "experiment3_manuscript_module_claims.csv")
    print("wrote", MAN / "experiment3_manuscript_figure_table_plan.csv")


if __name__ == "__main__":
    main()
