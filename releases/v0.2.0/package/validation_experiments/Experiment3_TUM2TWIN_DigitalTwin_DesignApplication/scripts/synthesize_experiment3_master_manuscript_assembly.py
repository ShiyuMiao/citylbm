from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"

FIELDS = [
    "assembly_id",
    "manuscript_section",
    "recommended_position",
    "primary_source_text",
    "primary_evidence_artifacts",
    "figure_table_callouts",
    "paper_ready_claim",
    "deepened_conclusion_for_paper",
    "claim_boundary",
    "evidence_type",
    "open_debt_or_author_action",
]

KEY_FIELDS = [
    "evidence_type",
    "claim_layer",
    "metric",
    "value",
    "source_artifact",
    "paper_safe_claim",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, row: dict[str, object], fields: list[str], unique_field: str) -> None:
    rows = read_csv(path)
    rows = [item for item in rows if item.get(unique_field) != str(row[unique_field])]
    rows.append({field: row.get(field, "") for field in fields})
    write_csv(path, rows, fields)


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def find_value(rows: list[dict[str, str]], claim_layer: str) -> str:
    for row in rows:
        if row.get("claim_layer") == claim_layer:
            return row.get("value", "")
    return ""


def make_rows() -> list[dict[str, object]]:
    key = read_csv(FIG / "final_integrated_key_result_matrix.csv")
    deep = read_csv(MAN / "experiment3_deep_data_conclusion_matrix.csv")
    debts = read_csv(MAN / "experiment3_submission_debt_register.csv")

    debt_status = Counter(row.get("status", "") for row in debts)
    deep_count = len(deep)
    key_count = sum(1 for row in key if row.get("claim_layer") != "Master manuscript assembly map")

    baseline_value = find_value(key, "S0 baseline pedestrian screening")
    gcri_value = find_value(key, "Geometry-to-CFD readiness")
    s1_value = find_value(key, "S1 design sensitivity")
    s2_value = find_value(key, "S2 design sensitivity")
    deep_value = find_value(key, "Deep data conclusion synthesis")
    debt_value = find_value(key, "Submission debt register")

    return [
        {
            "assembly_id": "E3-M0",
            "manuscript_section": "Experiment positioning after AIJ Case A/E",
            "recommended_position": "Insert at the start of Experiment 3, after solver/workflow validation experiments.",
            "primary_source_text": "paper_text/experiment_design_paragraph_zh.md; paper_text/experiment3_sci_section_paper_draft_en.md",
            "primary_evidence_artifacts": "README.md; reports/claim_boundary.md; manifests/experiment3_final_requirement_coverage.csv",
            "figure_table_callouts": "Table E3-2",
            "paper_ready_claim": "Experiment 3 is a real-campus digital-twin design-application case rather than a new solver-validation case.",
            "deepened_conclusion_for_paper": "The defensible title logic is FluidX3D-native simulation with CityLBM-compatible geometry preparation, supported by AIJ Case A/E as the preceding validation layer.",
            "claim_boundary": "Do not state that Experiment 3 independently proves solver accuracy or CityLBM-Grasshopper end-to-end execution.",
            "evidence_type": "preexisting_artifact + newly_run + blocked",
            "open_debt_or_author_action": "Author must decide final paper title emphasis and target journal style.",
        },
        {
            "assembly_id": "E3-M1",
            "manuscript_section": "Digital-twin data layering and geometry workflow",
            "recommended_position": "Methods, before numerical setup.",
            "primary_source_text": "paper_text/method_section_zh.md; paper_text/fluidx3d_numerical_protocol_methods_en.md",
            "primary_evidence_artifacts": "reports/data_source_and_download_manifest.md; reports/rhino_geometry_conversion_report.md; reports/cfd_ready_geometry_qa.md; manifests/data_manifest.csv; manifests/geometry_manifest.csv",
            "figure_table_callouts": "Table E3-3",
            "paper_ready_claim": "UAS/photogrammetry assets support visual audit, while semantic or CAD-derived closed geometry supports CFD collision boundaries.",
            "deepened_conclusion_for_paper": "The digital-twin contribution is not the visual realism of 3DGS/photogrammetry itself, but the traceable reassignment of visual, semantic and collision functions across data layers.",
            "claim_boundary": "Do not describe textured photogrammetry or 3DGS primitives as directly accepted watertight rigid collision boundaries.",
            "evidence_type": "newly_run + preexisting_artifact",
            "open_debt_or_author_action": "None for screening-level manuscript use.",
        },
        {
            "assembly_id": "E3-M2",
            "manuscript_section": "Geometry-to-CFD readiness",
            "recommended_position": "Methods or first Results subsection.",
            "primary_source_text": "paper_text/experiment3_deep_data_conclusion_module_zh.md; paper_text/experiment3_deep_data_conclusion_module_en.md",
            "primary_evidence_artifacts": "manifests/gcri_scoring_table.csv; manifests/geometry_qa_core_photogrammetry_extent_prism.json; cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl",
            "figure_table_callouts": "Table E3-3",
            "paper_ready_claim": f"GCRI evidence separates CFD-ready collision geometry from visually faithful but CFD-fragile geometry ({gcri_value}).",
            "deepened_conclusion_for_paper": "A high-readiness collision model can be much less visually rich than the source digital twin; for wind simulation, semantic closure and voxelization success matter more than texture fidelity.",
            "claim_boundary": "GCBTE is proposed but not computed because no independent 3DGS-derived collision extraction was available.",
            "evidence_type": "newly_run + blocked",
            "open_debt_or_author_action": "Keep GCBTE as future validation unless a 3DGS collision extraction workflow is added.",
        },
        {
            "assembly_id": "E3-M3",
            "manuscript_section": "Baseline pedestrian wind field",
            "recommended_position": "Results subsection 1.",
            "primary_source_text": "paper_text/results_section_zh.md; paper_text/final_integrated_results_discussion_en.md",
            "primary_evidence_artifacts": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv; reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md; reports/paraview_vtk_core_wind_statistics_and_building_analysis.md",
            "figure_table_callouts": "Fig. E3-1; Table E3-1",
            "paper_ready_claim": f"The baseline FluidX3D run supports a screening-level low-speed pedestrian-layer finding ({baseline_value}).",
            "deepened_conclusion_for_paper": "The main physical pattern is not isolated corner acceleration; it is a campus-core ventilation deficit in which pedestrian-layer low-speed zones occupy most of the open-cell mask across wind sectors.",
            "claim_boundary": "Do not convert VR maps into formal Lawson/NEN/AIJ annual comfort or safety classes.",
            "evidence_type": "newly_run + blocked",
            "open_debt_or_author_action": "Measured wind climate or wind-tunnel validation is needed for compliance or prediction claims.",
        },
        {
            "assembly_id": "E3-M4",
            "manuscript_section": "Vertical recovery and directionality",
            "recommended_position": "Results subsection 2.",
            "primary_source_text": "paper_text/experiment3_directional_anisotropy_results_zh.md; paper_text/experiment3_effect_size_uncertainty_results_zh.md",
            "primary_evidence_artifacts": "figures/fluidx3d_core_prism_deepened_directional_summary.csv; figures/experiment3_effect_size_uncertainty_summary.csv; manifests/experiment3_deep_data_sentence_evidence_map.csv",
            "figure_table_callouts": "Fig. E3-S1; Fig. E3-S2",
            "paper_ready_claim": "Vertical layers and eight-direction summaries show quasi-omnidirectional sheltering near pedestrians and partial recovery aloft.",
            "deepened_conclusion_for_paper": "The useful design reading is a vertical and directional gradient: the campus block behaves as a sheltered ground layer with wind-sector-dependent recovery rather than a uniform roughness patch.",
            "claim_boundary": "Sampling remains screening-level and does not replace convergence, grid-independence or validation evidence.",
            "evidence_type": "newly_run + blocked",
            "open_debt_or_author_action": "Add stronger temporal convergence and grid sensitivity if the target journal demands predictive CFD validation.",
        },
        {
            "assembly_id": "E3-M5",
            "manuscript_section": "Building-form interpretation",
            "recommended_position": "Results subsection 3 and Discussion.",
            "primary_source_text": "paper_text/building_form_wind_mechanism_conclusion_zh.md; paper_text/morphology_stage_transition_conclusion_en.md; paper_text/morphology_directional_fingerprint_conclusion_en.md",
            "primary_evidence_artifacts": "reports/building_form_wind_mechanism_synthesis.md; figures/basic_morphology_parameter_correlations.csv; figures/morphology_stage_transition_stage_summary.csv; figures/morphology_directional_fingerprint_stage_summary.csv",
            "figure_table_callouts": "Fig. E3-2; Fig. E3-4; Fig. E3-S3; Fig. E3-S4; Fig. E3-S5",
            "paper_ready_claim": "At this campus-block scale, basic morphology parameters explain wind response better as local-context descriptors than as LCZ classes.",
            "deepened_conclusion_for_paper": "The most useful new reading is a near-to-context transition: the 0-20 m facade-adjacent band is largely saturated by sheltering, while the 20-50 m band reveals how enclosure, local built fraction, relative vertical massing and wind-sector alignment control recovery.",
            "claim_boundary": "Treat correlations, thresholds, archetypes and directional fingerprints as sample-internal screening evidence, not universal causal laws.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "open_debt_or_author_action": "External sites or measured datasets are needed before claiming universal morphology thresholds.",
        },
        {
            "assembly_id": "E3-M6",
            "manuscript_section": "Design sensitivity S1/S2",
            "recommended_position": "Results subsection 4 or design-application discussion.",
            "primary_source_text": "paper_text/design_intervention_s1_discussion_en.md; paper_text/design_intervention_s2_discussion_en.md; paper_text/design_sensitivity_directional_tradeoff_discussion_zh.md",
            "primary_evidence_artifacts": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv; figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv",
            "figure_table_callouts": "Fig. E3-3; Table E3-1",
            "paper_ready_claim": f"S1/S2 are negative or near-null design-sensitivity tests rather than successful optimization cases ({s1_value}; {s2_value}).",
            "deepened_conclusion_for_paper": "The design insight is that simply adding corridor-like porosity does not guarantee pedestrian ventilation recovery; wind-entry position, upstream approach sector and local cavity coupling are more decisive than porosity area alone.",
            "claim_boundary": "Do not claim optimized intervention performance or S3-Sn design proof.",
            "evidence_type": "newly_run + blocked",
            "open_debt_or_author_action": "A future optimization loop should add S3-Sn alternatives and objective functions before using the word optimized.",
        },
        {
            "assembly_id": "E3-M7",
            "manuscript_section": "Campus climate and application potential",
            "recommended_position": "Discussion after morphology/design sensitivity.",
            "primary_source_text": "paper_text/conclusion_climate_campus_digital_twin_wind_zh.md; paper_text/experiment3_research_question_answer_paragraphs_en.md",
            "primary_evidence_artifacts": "manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv; figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv; reports/experiment3_research_question_synthesis.md",
            "figure_table_callouts": "Table E3-1; Fig. E3-S2",
            "paper_ready_claim": "The campus application value lies in repeatable screening of ventilation-sensitive spaces and in prioritizing morphology-aware design review.",
            "deepened_conclusion_for_paper": "For a dense educational campus, digital-twin CFD is most useful as a management-scale diagnostic layer: it can mark persistent low-speed pockets, compare local interventions and guide where field sensors or wind-tunnel validation should be deployed next.",
            "claim_boundary": "Open-Meteo remains a climate proxy and cannot support formal annual comfort/safety exceedance claims.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "open_debt_or_author_action": "Use local measured wind records if the final manuscript claims climate-compliance relevance.",
        },
        {
            "assembly_id": "E3-M8",
            "manuscript_section": "Limitations and claim boundary",
            "recommended_position": "End of Discussion and Conclusion.",
            "primary_source_text": "paper_text/experiment3_limitations_future_validation_roadmap_en.md; paper_text/experiment3_submission_debt_closure_note_zh.md",
            "primary_evidence_artifacts": "manifests/experiment3_submission_debt_register.csv; reports/experiment3_submission_debt_register.md; reports/claim_boundary.md",
            "figure_table_callouts": "Table E3-2",
            "paper_ready_claim": f"The archive explicitly classifies remaining debts and blocked claim upgrades ({debt_value}).",
            "deepened_conclusion_for_paper": "The limitation section should be written as a boundary of evidence strength, not as an apology: the completed contribution is data translation plus screening; validation, compliance and pollutant exposure are the next evidence layers.",
            "claim_boundary": "Keep blocked items visible: field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE and CityLBM-GH execution.",
            "evidence_type": "newly_run + blocked",
            "open_debt_or_author_action": f"Open status counts: {dict(debt_status)}.",
        },
        {
            "assembly_id": "E3-M9",
            "manuscript_section": "Data, code and reproducibility statements",
            "recommended_position": "Declarations, Data availability, Code availability and supplementary archive notes.",
            "primary_source_text": "paper_text/experiment3_submission_statements_en.md; paper_text/experiment3_submission_statements_zh.md",
            "primary_evidence_artifacts": "manifests/github_archive_manifest.csv; reports/github_archive_manifest_validation.md; EXTERNAL_ARTIFACTS.md; manifests/evidence_inventory.csv",
            "figure_table_callouts": "None",
            "paper_ready_claim": "The GitHub archive contains a checkout-stable manifest and points to external large assets without embedding all raw/VTK files.",
            "deepened_conclusion_for_paper": "Reproducibility should be framed as file-level traceability of the public package plus documented external-artifact boundaries.",
            "claim_boundary": "Do not imply that every large raw dataset or full VTK dump is stored directly in GitHub.",
            "evidence_type": "newly_run + preexisting_artifact",
            "open_debt_or_author_action": "Author must fill funding, competing interests, acknowledgements and CRediT roles.",
        },
        {
            "assembly_id": "E3-M10",
            "manuscript_section": "Final conclusion paragraph",
            "recommended_position": "Last paragraph of Experiment 3 or paper Conclusion.",
            "primary_source_text": "paper_text/experiment3_final_contribution_and_conclusion_en.md; paper_text/experiment3_deep_data_conclusion_module_en.md; paper_text/experiment3_final_sci_discussion_conclusion_en.md",
            "primary_evidence_artifacts": "manifests/experiment3_deep_data_conclusion_matrix.csv; figures/final_integrated_key_result_matrix.csv; manifests/experiment3_deep_data_sentence_evidence_map.csv",
            "figure_table_callouts": "Table E3-1; Table E3-2",
            "paper_ready_claim": f"The final conclusion should synthesize geometry readiness, low-speed dominance, morphology-context interpretation and negative design sensitivity ({deep_count} deep findings; {key_count} key-result rows; {deep_value}).",
            "deepened_conclusion_for_paper": "Experiment 3 adds a design-application layer beyond AIJ validation: it shows how a real digital twin can become a wind-screening instrument, and it reframes building-form effects as context-dependent ventilation recovery rather than a single morphology or LCZ label.",
            "claim_boundary": "Retain screening-level wording unless the missing external validation and compliance evidence are added.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "open_debt_or_author_action": "Manual author review should choose whether this is a standalone Experiment 3 section or a merged Results/Discussion subsection.",
        },
    ]


def write_outputs(rows: list[dict[str, object]]) -> None:
    write_csv(MAN / "experiment3_master_manuscript_assembly_map.csv", rows, FIELDS)

    brief_fields = [
        "assembly_id",
        "manuscript_section",
        "figure_table_callouts",
        "paper_ready_claim",
        "claim_boundary",
        "open_debt_or_author_action",
    ]
    report = f"""# Experiment 3 Master Manuscript Assembly Map

evidence_type: newly_run + preexisting_artifact + blocked

This report converts the current Experiment 3 archive into a manuscript assembly map. It does not add new simulation outcomes. It tells the author where each result belongs, what artifact supports it, which figure or table should be cited, and how the claim must be bounded.

## Assembly Summary

- Assembly rows: `{len(rows)}`
- Main safe positioning: `FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation`.
- Strongest paper contribution: data-layer separation, CFD-ready geometry construction, campus-core low-speed screening, building-form/context interpretation, and negative S1/S2 design-sensitivity evidence.
- Claims still blocked: field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE closure, CityLBM-Grasshopper end-to-end execution, and optimized S3-Sn intervention proof.

## Manuscript Assembly Table

{md_table(rows, brief_fields)}

## Recommended Narrative Order

1. Position Experiment 3 after AIJ Case A/E as a real digital-twin application case.
2. Explain why visual photogrammetry and semantic collision geometry must be separated.
3. Report GCRI/geometry QA before wind results so the reader sees why the CFD boundary is legitimate.
4. Present S0 baseline low-speed and vertical/directional recovery.
5. Interpret wind response with basic morphology parameters rather than LCZ classification.
6. Use S1/S2 as negative design-sensitivity evidence to show why porosity must be coupled to wind-entry context.
7. Close with campus application potential and explicit evidence boundaries.
"""
    (REP / "experiment3_master_manuscript_assembly_map.md").write_text(report, encoding="utf-8")

    zh = """# 实验3主论文装配指南

evidence_type: newly_run + preexisting_artifact + blocked

## 可直接采用的论文主线

实验3应放在 AIJ Case A 与 Case E 之后，作为真实城市数字孪生风环境应用实验，而不是再次证明求解器精度。最稳妥的论文定位是：基于 TUM2TWIN 校园数字孪生数据，建立从视觉真实模型到 CFD-ready 碰撞边界的转化流程，并使用 FluidX3D-native 求解与 ParaView/统计后处理完成行人高度风环境筛查；CityLBM-Grasshopper 部分保留为兼容输入模板，除非补充端到端运行证据。

## 详细结论组织

第一层结论是数据层结论：UAS/摄影测量模型适合用于真实场景核验、Rhino 浏览和论文图像一致性审查，但不应直接承担 LBM 碰撞边界；语义或 CAD 派生的封闭几何才是本实验进入 CFD 的关键。这里的创新点不是“数字孪生模型越真实越适合模拟”，而是“数字孪生底层数据需要按视觉、语义和碰撞功能重新分层”。

第二层结论是风场分布结论：S0 八风向结果支持校园核心区行人高度存在大范围低风速与通风不足区。该结论不能写成正式舒适/安全合规评价，但可以写成面向设计管理的筛查结果：模型能够指出哪些开放空间、街巷和建筑间隙需要进一步现场测量、风洞验证或设计干预。

第三层结论是建筑形态结论：在本模型尺度下，不再使用 LCZ 分类，而采用更加基础的建筑形态参数。最有解释力的不是单栋建筑高度或占地面积本身，而是 0-20 m 近立面遮蔽饱和与 20-50 m 局地上下文恢复之间的差异。换言之，建筑形式对风环境的影响在这个校园街区中表现为“局地围合、相对竖向体量、平面连续性和来流扇区耦合”的共同结果。

第四层结论是设计应用结论：S1/S2 并没有证明简单开口或通廊一定改善行人层通风，反而提供了更有论文价值的负结果。它说明几何孔隙率不能单独作为优化目标；如果开口位置没有接入有效来流、或没有打通局地滞风腔体，增加孔隙可能只产生局部、方向性和近零甚至负向的响应。

第五层结论是应用潜力结论：在校园环境中，数字孪生风模拟最适合先作为“筛查-解释-布点-迭代设计”的工具。它可以帮助识别长期低风速风险区、组织建筑形态参数解释、决定传感器布点和后续风洞/实测验证位置，而不应在缺少实测闭环时直接替代正式风环境评价。

## 必须保留的边界

本文不能声称完成了实测验证、风洞验证、正式年度 Lawson/NEN/AIJ 舒适安全评价、污染物扩散预测、GCBTE 量化闭合、CityLBM-Grasshopper 端到端验证或成功优化设计。应把这些内容写成后续验证路径，而不是已完成结果。
"""
    (PAPER / "experiment3_master_manuscript_assembly_guide_zh.md").write_text(zh, encoding="utf-8")

    en = """# Experiment 3 Master Manuscript Assembly Guide

evidence_type: newly_run + preexisting_artifact + blocked

## Recommended Manuscript Line

Experiment 3 should be positioned after AIJ Case A and Case E as a real digital-twin application case, not as an additional solver-validation case. The safest framing is a FluidX3D-native digital-twin-to-CFD wind-screening experiment with a CityLBM-compatible geometry package.

## Detailed Conclusion Structure

The first conclusion concerns data layers: visual photogrammetry is useful for scene audit and Rhino review, whereas semantically repaired or CAD-derived closed geometry is required for LBM collision boundaries. The novelty is therefore not visual realism alone, but functional separation between visual, semantic and collision-ready representations.

The second conclusion concerns wind distribution: the S0 eight-direction results support a screening-level finding of extensive pedestrian-layer low-speed conditions in the campus core. This should be written as a design-screening result, not as formal annual comfort or safety compliance.

The third conclusion concerns building form: at this model scale, basic morphology parameters are more defensible than LCZ classification. The important pattern is a near-to-context transition: the 0-20 m facade-adjacent band is largely saturated by sheltering, while the 20-50 m context band exposes wind recovery controlled by local enclosure, relative vertical massing, plan continuity and wind-sector coupling.

The fourth conclusion concerns design application: S1/S2 are valuable negative sensitivity tests. They show that geometric porosity alone does not guarantee pedestrian ventilation improvement; wind-entry position and coupling to the local cavity system are more important than opening area by itself.

The fifth conclusion concerns campus application potential: digital-twin wind simulation is most useful as a screening, interpretation, sensor-placement and iterative-design tool before formal validation. It can prioritize spaces for measurement and design review, but it should not replace field validation or regulatory comfort assessment.

## Boundaries To Preserve

Do not claim field validation, wind-tunnel validation, formal Lawson/NEN/AIJ annual comfort or safety compliance, pollutant dispersion prediction, closed GCBTE quantification, CityLBM-Grasshopper end-to-end execution, or successful optimized S3-Sn intervention unless new evidence is added.
"""
    (PAPER / "experiment3_master_manuscript_assembly_guide_en.md").write_text(en, encoding="utf-8")

    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Master manuscript assembly map",
            "metric": "assembly rows / sections covered / paper-facing guides",
            "value": f"{len(rows)} / {len({row['manuscript_section'] for row in rows})} / 2",
            "source_artifact": "manifests/experiment3_master_manuscript_assembly_map.csv; reports/experiment3_master_manuscript_assembly_map.md; paper_text/experiment3_master_manuscript_assembly_guide_zh.md; paper_text/experiment3_master_manuscript_assembly_guide_en.md",
            "paper_safe_claim": "Experiment 3 now has a section-by-section manuscript assembly map linking each paper-ready conclusion to source text, evidence artifacts, figures/tables and claim boundaries.",
        },
        KEY_FIELDS,
        "claim_layer",
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        {
            "claim": "Experiment 3 master manuscript assembly map links each paper-facing conclusion to source text, evidence artifacts, figure/table callouts and claim boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_master_manuscript_assembly_map.csv; reports/experiment3_master_manuscript_assembly_map.md; paper_text/experiment3_master_manuscript_assembly_guide_zh.md; paper_text/experiment3_master_manuscript_assembly_guide_en.md",
        },
        ["claim", "evidence_type", "source"],
        "claim",
    )


def main() -> None:
    rows = make_rows()
    write_outputs(rows)
    print("master_manuscript_assembly_rows", len(rows))


if __name__ == "__main__":
    main()
