from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
REPO_ROOT = ROOT.parents[4]
PAPER = ROOT / "paper_text"
REPORTS = ROOT / "reports"
MAN = ROOT / "manifests"
FIG = ROOT / "figures"
DRAFT_DIR = REPO_ROOT / "academic-paper-writer" / "paper-drafts"


FIGURE_CAPTIONS = [
    {
        "id": "Fig. E3-1",
        "path": "figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png",
        "evidence_type": "newly_run",
        "source_data": "figures/paraview_vtk_core_dx2m_robustness_stats.csv; figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
        "caption_zh": "图 E3-1. TUM Downtown 核心校园街区在行人高度的 FluidX3D/VTK 风速比筛查图。图中结果来自 dx=2 m、8 个来流方向、三时刻采样后的核心闭合棱柱碰撞几何，用于人工审核低风速区、方向一致性和建筑周边滞风格局。该图支持“行人层以低速和通风不足为主”的筛查性结论，但不支持年度舒适度合规、实测验证或污染物扩散结论。",
        "caption_en": "Fig. E3-1. Pedestrian-height FluidX3D/VTK velocity-ratio screening map for the TUM Downtown core campus block. The panel is derived from the dx=2 m, eight-direction, three-sample core closed-prism collision setup and is intended for manual review of low-speed regions, directional consistency and building-adjacent stagnation. It supports a screening-level low-ventilation interpretation, not annual comfort compliance, field validation or pollutant dispersion.",
        "paper_safe_use": "baseline pedestrian-layer low-speed screening and manual visual audit",
        "boundary": "not annual Lawson/NEN/AIJ compliance; not field validation; not scalar dispersion",
    },
    {
        "id": "Fig. E3-2",
        "path": "figures/basic_morphology_multivariate_rank_model_importance.png",
        "evidence_type": "newly_run",
        "source_data": "figures/basic_morphology_multivariate_robustness.csv; figures/basic_morphology_rank_model_cv_summary.csv",
        "caption_zh": "图 E3-2. 基础建筑形态参数与 20-50 m 局地环境风速响应的多变量稳健性分析。图中排序回归系数和置换重要度显示，局地围合度、平均高度和综合围合指标比单体占地面积、平面伸长率或紧凑度更能解释样本内风速差异。由于交叉验证解释力有限，该图应写成可解释筛查证据，而不是高精度预测模型。",
        "caption_en": "Fig. E3-2. Multivariate robustness analysis linking basic building-form parameters to wind response in the 20-50 m local-context band. Rank-regression coefficients and permutation importance indicate that local enclosure, mean height and combined enclosure are more informative than footprint area, elongation or compactness in this screened sample. Because cross-validated explanatory power is limited, the figure should be used as interpretable screening evidence rather than as a high-accuracy predictor.",
        "paper_safe_use": "morphology interpretation and variable ranking",
        "boundary": "not a deterministic surrogate model; not externally validated thresholds",
    },
    {
        "id": "Fig. E3-3",
        "path": "figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png",
        "evidence_type": "newly_run",
        "source_data": "figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv; figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv",
        "caption_zh": "图 E3-3. S1/S2 设计敏感性场景在行人高度的方向性局地 trade-off。热图比较不同来流方向下共同开放单元的风速比变化，显示 S2 的局地正响应略强于 S1，但改善单元稀疏且新增开放单元仍处低速状态。因此该图的论文价值是负结果证据，即几何孔隙率本身不足以恢复校园核心区行人层通风。",
        "caption_en": "Fig. E3-3. Directional local trade-off of S1/S2 design-sensitivity scenarios at pedestrian height. The heatmap compares velocity-ratio changes in common open cells across inflow directions. S2 produces slightly stronger local positive response than S1, but improved cells remain sparse and newly opened cells stay low-speed. The figure is therefore negative design evidence: geometric porosity alone is insufficient to recover pedestrian-layer ventilation in this campus core.",
        "paper_safe_use": "negative design-sensitivity evidence",
        "boundary": "not successful optimization; not final design recommendation",
    },
    {
        "id": "Fig. E3-4",
        "path": "figures/morphology_threshold_recovery_rule_summary.png",
        "evidence_type": "newly_run + blocked",
        "source_data": "figures/morphology_threshold_rule_screening.csv; figures/morphology_recovery_top_bottom_contrast.csv",
        "caption_zh": "图 E3-4. 0-20 m 近立面带到 20-50 m 局地环境带的风速恢复阈值规则筛查。分析在同一组 101 个保留建筑单元上比较近立面与局地环境响应，提取样本内 tertile 组合规则。最佳简单规则提示较低相对竖向尺度和特定平面形态组合更易出现局地恢复，但该阈值仅用于数字孪生样本内设计筛查，不能外推为通用规范或实测验证结论。",
        "caption_en": "Fig. E3-4. Threshold-rule screening for wind-speed recovery from the 0-20 m facade-adjacent band to the 20-50 m local-context band. The analysis pairs the same 101 retained building components and extracts sample-internal tertile rules. The best simple rule suggests that lower relative vertical scale combined with selected plan-form conditions is associated with higher local recovery, but the threshold is only a digital-twin screening rule, not a universal or field-validated design criterion.",
        "paper_safe_use": "sample-internal design-rule screening",
        "boundary": "not universal threshold; not field-validated design rule",
    },
    {
        "id": "Fig. E3-S1",
        "path": "figures/experiment3_effect_size_uncertainty_forest.png",
        "evidence_type": "newly_run + blocked",
        "source_data": "figures/experiment3_effect_size_uncertainty_summary.csv",
        "caption_zh": "图 E3-S1. 实验3效应量与不确定性补充森林图。图中汇总 S0 行人层与上层风速比、40 m-2 m 竖向恢复、S1/S2 行人层全局变化以及建筑形态近立面到局地环境的恢复增量。该图用于说明核心低速、竖向脱耦和 S1/S2 负结果在方向-采样或方向范围内保持一致，但它只表示已归档模拟输出的统计不确定性，不代表实测不确定性、网格收敛证明或年度舒适度超越概率。",
        "caption_en": "Fig. E3-S1. Supplementary forest plot of Experiment 3 effect sizes and uncertainty. The figure summarizes S0 pedestrian and upper-layer velocity ratios, 40 m minus 2 m vertical recovery, S1/S2 pedestrian-layer global changes and morphology near-to-context recovery. It shows that the low-speed baseline, vertical decoupling and S1/S2 negative results are stable within the available direction-sample or directional ranges, but it represents uncertainty in archived simulation outputs only, not measurement uncertainty, grid-convergence proof or annual comfort exceedance probability.",
        "paper_safe_use": "supplementary uncertainty and effect-size audit",
        "boundary": "not measurement uncertainty; not grid convergence; not annual comfort exceedance probability",
    },
    {
        "id": "Fig. E3-S2",
        "path": "figures/experiment3_directional_anisotropy_panel.png",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source_data": "figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv",
        "caption_zh": "图 E3-S2. 实验3八风向各向异性与设计扇区响应补充图。图中比较 S0 行人层 mean VR、行人层滞风比例、40 m-2 m 竖向恢复以及 S2 common-open-cell 局地响应。结果显示行人层低速和高滞风在八个来流方向中近似全向存在，而 S2 的局部响应具有方向性，最强响应出现在 315 deg；但S1/S2全局行人层 mean-VR delta 在全部方向上仍为负。该图支持风扇区耦合的设计解释，不支持年度风玫瑰合规或成功优化宣称。",
        "caption_en": "Fig. E3-S2. Supplementary eight-direction anisotropy and design-sector response for Experiment 3. The panel compares S0 pedestrian-layer mean VR, pedestrian-layer stagnation ratio, 40 m minus 2 m vertical recovery and S2 common-open-cell local response. The low-speed and high-stagnation state is quasi-omnidirectional across the eight inflow directions, whereas S2 local response is directional and strongest at 315 deg; nevertheless, S1/S2 global pedestrian-layer mean-VR deltas remain negative in all directions. The figure supports wind-sector-coupled design interpretation, not annual wind-rose compliance or successful optimization claims.",
        "paper_safe_use": "directional mechanism and wind-sector design interpretation",
        "boundary": "not measured wind rose; not annual comfort compliance; not successful optimization",
    },
]


TABLE_CAPTIONS = [
    {
        "id": "Table E3-1",
        "path": "figures/final_integrated_key_result_matrix.csv",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source_data": "compiled from FluidX3D metrics, Open-Meteo proxy weights, morphology CSVs, design-sensitivity comparisons and GCRI",
        "caption_zh": "表 E3-1. 实验3面向论文的一页式关键结果矩阵。表格把 S0 基准、竖向恢复、Open-Meteo 方向代理敏感性、S1/S2 设计敏感性、方向性 trade-off、形态稳健性、阈值筛查和 GCRI 几何就绪度整合到同一证据框架，并逐行给出 evidence_type、来源文件和论文安全表述。",
        "caption_en": "Table E3-1. Paper-facing one-page key-result matrix for Experiment 3. The table consolidates S0 baseline, vertical recovery, Open-Meteo proxy sensitivity, S1/S2 design sensitivity, directional trade-off, morphology robustness, threshold screening and GCRI into one evidence framework with evidence type, source artifact and paper-safe claim for each row.",
        "paper_safe_use": "main result table and evidence anchor",
        "boundary": "rows with blocked components must retain boundary wording",
    },
    {
        "id": "Table E3-2",
        "path": "figures/experiment3_completion_audit_matrix.csv",
        "evidence_type": "newly_run + blocked",
        "source_data": "reports/experiment3_completion_audit_and_paper_readiness.md",
        "caption_zh": "表 E3-2. 实验3完成度与论文可用性审计矩阵。表格区分已完成、可写为筛查结论、需要弱化和仍受阻的模块，尤其标注实测风场、年度舒适度合规、污染物扩散、GCBTE 和 CityLBM-Grasshopper 端到端运行的缺口。",
        "caption_en": "Table E3-2. Completion and paper-readiness audit matrix for Experiment 3. The table separates completed, screening-level, weakened and blocked modules, explicitly marking missing field data, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-Grasshopper end-to-end execution.",
        "paper_safe_use": "limitations table and claim boundary",
        "boundary": "blocked rows must not be converted into completed results",
    },
    {
        "id": "Table E3-3",
        "path": "manifests/gcri_scoring_table.csv",
        "evidence_type": "newly_run",
        "source_data": "reports/geometry_to_cfd_readiness_index_results.md; reports/cfd_ready_geometry_qa.md",
        "caption_zh": "表 E3-3. Geometry-to-CFD Readiness Index (GCRI) 评分表。表格比较摄影测量视觉网格、核心闭合棱柱碰撞几何和街区棱柱碰撞几何在水密性、非流形错误、语义层完整性、坐标/单位一致性、STL 导出和体素化成功等子项上的 0-1 就绪度，说明视觉真实度与 CFD 碰撞边界可用性是不同属性。",
        "caption_en": "Table E3-3. Geometry-to-CFD Readiness Index (GCRI) scoring table. The table compares photogrammetry visual mesh, core closed-prism collision geometry and district-prism collision geometry in watertightness, non-manifold error, semantic layer completeness, coordinate/unit consistency, STL export and voxelization success, showing that visual realism and CFD collision readiness are distinct model properties.",
        "paper_safe_use": "digital-twin geometry readiness metric",
        "boundary": "GCRI is a paper-internal readiness score, not an external standard",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def asset_status(row: dict[str, str]) -> dict[str, str]:
    rel = Path(row["path"])
    full = ROOT / rel
    exists = full.exists()
    size = full.stat().st_size if exists else 0
    return {
        "asset_id": row["id"],
        "asset_type": "figure" if row["id"].startswith("Fig.") else "table",
        "relative_path": row["path"],
        "exists": "yes" if exists else "no",
        "size_bytes": str(size),
        "evidence_type": row["evidence_type"],
        "source_data": row["source_data"],
        "paper_safe_use": row["paper_safe_use"],
        "boundary": row["boundary"],
        "submission_status": "ready_for_manual_review" if exists else "missing_asset",
    }


def build_caption_doc(title: str, items: list[dict[str, str]], key: str) -> str:
    lines = [
        f"# {title}",
        "",
        "evidence_type: newly_run + preexisting_artifact + blocked",
        "",
        "These captions are tied to archived source artifacts. They should be edited only for journal style, not for claim strength, unless new evidence is added.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## {item['id']}",
                "",
                item[key],
                "",
                f"- Asset: `{item['path']}`",
                f"- Source data: `{item['source_data']}`",
                f"- Evidence type: `{item['evidence_type']}`",
                f"- Boundary: {item['boundary']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_combined_draft_caption_doc() -> str:
    lines = [
        "# Experiment 3 Figure and Table Captions",
        "",
        "evidence_type: newly_run + preexisting_artifact + blocked",
        "",
        "Use these captions with the section draft after final journal style is fixed. The wording keeps screening results separate from blocked validation and compliance claims.",
        "",
        "## Figures",
        "",
    ]
    for item in FIGURE_CAPTIONS:
        lines.extend([f"### {item['id']}", "", item["caption_en"], "", item["caption_zh"], ""])
    lines.extend(["## Tables", ""])
    for item in TABLE_CAPTIONS:
        lines.extend([f"### {item['id']}", "", item["caption_en"], "", item["caption_zh"], ""])
    return "\n".join(lines).strip() + "\n"


def build_audit_doc(rows: list[dict[str, str]]) -> str:
    missing = [row for row in rows if row["exists"] != "yes"]
    ready = [row for row in rows if row["submission_status"] == "ready_for_manual_review"]
    blocked_topics = [
        "field or wind-tunnel validation",
        "annual Lawson/NEN/AIJ comfort or safety compliance",
        "pollutant scalar transport",
        "GCBTE boundary-transfer computation",
        "CityLBM-Grasshopper end-to-end execution",
    ]
    lines = [
        "# Experiment 3 Submission Readiness Audit",
        "",
        "evidence_type: newly_run + preexisting_artifact + blocked",
        "",
        "Generated at: 2026-07-28",
        "",
        "## Summary",
        "",
        f"- Figure/table assets checked: `{len(rows)}`",
        f"- Ready for manual review: `{len(ready)}`",
        f"- Missing assets: `{len(missing)}`",
        "- Canonical paper position: FluidX3D-native simulation with a CityLBM-compatible geometry package.",
        "- Claim strength: screening-level wind-environment application and morphology interpretation, not field-validated prediction.",
        "",
        "## Asset-Level Status",
        "",
        "| asset | type | exists | evidence_type | paper_safe_use | boundary |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['asset_id']} | {row['asset_type']} | {row['exists']} | {row['evidence_type']} | {row['paper_safe_use']} | {row['boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    for topic in blocked_topics:
        lines.append(f"- blocked: {topic}.")
    lines.extend(
        [
            "",
            "## Submission Use",
            "",
            "The current package is suitable for a design-application experiment section once the target journal, reference style and paper-level framing are fixed. The reviewer-facing figures and tables are present and traceable to CSV, manifest or report sources. The safest title wording remains: `FluidX3D-native simulation with CityLBM-compatible geometry package`.",
            "",
        ]
    )
    return "\n".join(lines)


def append_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    rows = read_csv(path)
    claim = "SCI figure/table captions and submission-readiness audit were generated from the verified Experiment 3 figure plan, result matrix, GCRI table and claim inventory."
    if any(row.get("claim") == claim for row in rows):
        return
    rows.append(
        {
            "claim": claim,
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_sci_figure_captions_zh.md; paper_text/experiment3_sci_table_captions_zh.md; reports/experiment3_submission_readiness_audit.md; manifests/experiment3_submission_readiness_checklist.csv",
        }
    )
    write_csv(path, rows, ["claim", "evidence_type", "source"])


def main() -> None:
    matrix = read_csv(FIG / "final_integrated_key_result_matrix.csv")
    figure_plan = read_csv(MAN / "experiment3_manuscript_figure_table_plan.csv")
    expected_assets = {row["recommended_file"] for row in figure_plan}
    caption_assets = {row["path"] for row in FIGURE_CAPTIONS + TABLE_CAPTIONS}
    if expected_assets != caption_assets:
        missing = expected_assets - caption_assets
        extra = caption_assets - expected_assets
        raise RuntimeError(f"caption asset mismatch; missing={missing}; extra={extra}")
    if len(matrix) < 9:
        raise RuntimeError("final integrated key result matrix is unexpectedly short")

    status_rows = [asset_status(row) for row in FIGURE_CAPTIONS + TABLE_CAPTIONS]
    fields = [
        "asset_id",
        "asset_type",
        "relative_path",
        "exists",
        "size_bytes",
        "evidence_type",
        "source_data",
        "paper_safe_use",
        "boundary",
        "submission_status",
    ]
    write_csv(MAN / "experiment3_submission_readiness_checklist.csv", status_rows, fields)

    write_text(
        PAPER / "experiment3_sci_figure_captions_zh.md",
        build_caption_doc("实验3 SCI 图题说明", FIGURE_CAPTIONS, "caption_zh"),
    )
    write_text(
        PAPER / "experiment3_sci_figure_captions_en.md",
        build_caption_doc("Experiment 3 SCI Figure Captions", FIGURE_CAPTIONS, "caption_en"),
    )
    write_text(
        PAPER / "experiment3_sci_table_captions_zh.md",
        build_caption_doc("实验3 SCI 表题说明", TABLE_CAPTIONS, "caption_zh"),
    )
    write_text(
        PAPER / "experiment3_sci_table_captions_en.md",
        build_caption_doc("Experiment 3 SCI Table Captions", TABLE_CAPTIONS, "caption_en"),
    )
    write_text(DRAFT_DIR / "figure_table_captions.md", build_combined_draft_caption_doc())
    write_text(REPORTS / "experiment3_submission_readiness_audit.md", build_audit_doc(status_rows))
    append_evidence_inventory()

    print("wrote paper_text/experiment3_sci_figure_captions_zh.md")
    print("wrote paper_text/experiment3_sci_figure_captions_en.md")
    print("wrote paper_text/experiment3_sci_table_captions_zh.md")
    print("wrote paper_text/experiment3_sci_table_captions_en.md")
    print("wrote academic-paper-writer/paper-drafts/figure_table_captions.md")
    print("wrote reports/experiment3_submission_readiness_audit.md")
    print("wrote manifests/experiment3_submission_readiness_checklist.csv")
    print("updated manifests/evidence_inventory.csv")


if __name__ == "__main__":
    main()
