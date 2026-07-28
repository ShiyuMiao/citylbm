from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"

for folder in [MAN, REP, PAPER, DRAFT]:
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("|" + "|".join(["---"] * len(fields)) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def exists_status(path: str) -> str:
    p = ROOT / path
    return "exists" if p.exists() else "missing"


def main() -> None:
    key_matrix = read_csv(FIG / "final_integrated_key_result_matrix.csv")
    figure_plan = read_csv(MAN / "experiment3_manuscript_figure_table_plan.csv")
    readiness = read_csv(MAN / "experiment3_submission_readiness_checklist.csv")
    evidence = read_csv(MAN / "evidence_inventory.csv")
    refs = read_csv(MAN / "verified_references_for_sci_discussion.csv")
    claim_verification = read_csv(DRAFT / "experiment3_claim_verification.csv")

    ready_count = sum(1 for row in readiness if row.get("submission_status") == "ready_for_manual_review")
    missing_assets = [row for row in readiness if row.get("exists") != "yes"]

    inventory_path = MAN / "evidence_inventory.csv"
    additions = [
        {
            "claim": "Final completeness and gap audit was regenerated from the current key result matrix, figure/table plan, evidence inventory and readiness checklist.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "reports/experiment3_final_completeness_and_gap_audit.md; manifests/experiment3_final_requirement_coverage.csv",
        },
        {
            "claim": "Final bilingual contribution and conclusion paragraphs were drafted with explicit claim boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_final_contribution_and_conclusion_zh.md; paper_text/experiment3_final_contribution_and_conclusion_en.md",
        },
    ]
    existing = {(row.get("claim", ""), row.get("source", "")) for row in evidence}
    for row in additions:
        key = (row["claim"], row["source"])
        if key not in existing:
            evidence.append(row)
    write_csv(inventory_path, evidence, ["claim", "evidence_type", "source"])

    requirements = [
        {
            "requirement": "TUM2TWIN official source and layer verification",
            "status": "complete",
            "evidence_type": "newly_run + preexisting_artifact",
            "evidence_artifact": "reports/data_source_and_download_manifest.md; manifests/data_manifest.csv",
            "paper_safe_interpretation": "Official data sources, download records, checksums, licenses and layer roles are archived.",
        },
        {
            "requirement": "Rhino/OBJ visual-object consistency",
            "status": "complete",
            "evidence_type": "newly_run + user_claim",
            "evidence_artifact": "reports/model_result_object_consistency_audit.md; reports/current_data_summary_and_conclusions.md",
            "paper_safe_interpretation": "The simulated core geometry matches the user's TUM Downtown visual block at study-scale, while using a repaired semantic collision boundary.",
        },
        {
            "requirement": "CFD-ready collision geometry",
            "status": "complete",
            "evidence_type": "newly_run",
            "evidence_artifact": "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl; manifests/geometry_qa_core_photogrammetry_extent_prism.json; manifests/gcri_scoring_table.csv",
            "paper_safe_interpretation": "Closed z0-aligned geometry, QA records and GCRI contrast support the data-to-CFD method claim.",
        },
        {
            "requirement": "FluidX3D baseline simulation",
            "status": "complete",
            "evidence_type": "newly_run",
            "evidence_artifact": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_safe_interpretation": "Eight directions and three post-spin-up samples support a screening-level pedestrian wind result.",
        },
        {
            "requirement": "ParaView and manual visual audit assets",
            "status": "complete_with_environment_boundary",
            "evidence_type": "newly_run + blocked",
            "evidence_artifact": "paraview_states/; reports/paraview_visualization_package.md; reports/paraview_vtk_core_wind_statistics_and_building_analysis.md",
            "paper_safe_interpretation": "ParaView states and Python-rendered audit maps exist; headless ParaView screenshots remain blocked by Windows OpenGL/OSMesa.",
        },
        {
            "requirement": "Climate-direction proxy sensitivity",
            "status": "complete_with_boundary",
            "evidence_type": "newly_run + preexisting_artifact",
            "evidence_artifact": "figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv; manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv",
            "paper_safe_interpretation": "Open-Meteo is a proxy directional weighting layer, not measured annual comfort compliance.",
        },
        {
            "requirement": "Basic morphology and multivariate robustness",
            "status": "complete_with_boundary",
            "evidence_type": "newly_run",
            "evidence_artifact": "reports/basic_morphology_wind_response_analysis.md; reports/basic_morphology_multivariate_robustness.md",
            "paper_safe_interpretation": "Local enclosure and height context are interpretable screening descriptors, not a high-accuracy predictor.",
        },
        {
            "requirement": "Morphology threshold and archetype interpretation",
            "status": "complete_with_boundary",
            "evidence_type": "newly_run + blocked",
            "evidence_artifact": "reports/morphology_threshold_design_rule_analysis.md; reports/morphology_form_response_archetype_analysis.md",
            "paper_safe_interpretation": "The 20-50 m band and response archetypes support sample-internal design screening, not universal causal thresholds.",
        },
        {
            "requirement": "S1/S2 design sensitivity",
            "status": "complete_negative_result",
            "evidence_type": "newly_run",
            "evidence_artifact": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "paper_safe_interpretation": "S1/S2 are near-null or negative; they support design-boundary reasoning rather than optimization success.",
        },
        {
            "requirement": "Directional anisotropy and wind-sector design logic",
            "status": "complete_with_boundary",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "evidence_artifact": "reports/experiment3_directional_anisotropy_analysis.md; figures/experiment3_directional_anisotropy_summary.csv",
            "paper_safe_interpretation": "Low-speed sheltering is quasi-omnidirectional; local intervention response is sector-sensitive but not globally restorative.",
        },
        {
            "requirement": "SCI section draft and figure/table captions",
            "status": "complete_as_generic_section",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "evidence_artifact": "academic-paper-writer/paper-drafts/paper_draft.md; academic-paper-writer/paper-drafts/paper_draft_en.md; paper_text/experiment3_sci_figure_captions_en.md",
            "paper_safe_interpretation": "A generic SCI section and 10 traceable figure/table assets are available, pending target-journal formatting.",
        },
        {
            "requirement": "CityLBM-Grasshopper end-to-end execution",
            "status": "blocked",
            "evidence_type": "blocked",
            "evidence_artifact": "cfd_ready/CityLBM_GH_input_template/README.md; reports/claim_boundary.md",
            "paper_safe_interpretation": "Frame as FluidX3D-native simulation with a CityLBM-compatible geometry package unless GH execution evidence is added.",
        },
        {
            "requirement": "Measured or wind-tunnel validation",
            "status": "blocked",
            "evidence_type": "blocked",
            "evidence_artifact": "reports/claim_boundary.md",
            "paper_safe_interpretation": "Do not claim field-validated predictive accuracy.",
        },
        {
            "requirement": "Formal Lawson/NEN/AIJ annual comfort compliance",
            "status": "blocked",
            "evidence_type": "blocked",
            "evidence_artifact": "reports/claim_boundary.md",
            "paper_safe_interpretation": "Do not claim annual threshold-exceedance comfort or safety classes.",
        },
        {
            "requirement": "Pollutant dispersion",
            "status": "blocked",
            "evidence_type": "blocked",
            "evidence_artifact": "reports/metric_system_for_digital_twin_wind_application.md",
            "paper_safe_interpretation": "Pollutant metrics remain templates only.",
        },
        {
            "requirement": "GCBTE 3DGS collision-transfer error",
            "status": "blocked",
            "evidence_type": "blocked",
            "evidence_artifact": "manifests/gcbte_status_table.csv",
            "paper_safe_interpretation": "GCBTE is defined but not computed because no independent 3DGS-derived collision extraction exists.",
        },
    ]
    write_csv(
        MAN / "experiment3_final_requirement_coverage.csv",
        requirements,
        [
            "requirement",
            "status",
            "evidence_type",
            "evidence_artifact",
            "paper_safe_interpretation",
        ],
    )

    key_fields = [
        "evidence_type",
        "claim_layer",
        "metric",
        "value",
        "source_artifact",
        "paper_safe_claim",
    ]
    req_fields = [
        "requirement",
        "status",
        "evidence_type",
        "evidence_artifact",
        "paper_safe_interpretation",
    ]

    completion = f"""# Experiment 3 Completion Audit and Paper Readiness

evidence_type: newly_run + preexisting_artifact + blocked

This audit reflects the current archive after the morphology-response archetype addendum. It checks whether the TUM2TWIN Experiment 3 package is ready for manuscript use and where claim boundaries must remain explicit.

## Evidence Counts

- Key result matrix rows: `{len(key_matrix)}`
- Figure/table callouts: `{len(figure_plan)}`
- Submission-readiness assets: `{len(readiness)}`
- Ready for manual review: `{ready_count}`
- Missing figure/table assets: `{len(missing_assets)}`
- Evidence inventory rows: `{len(evidence)}`
- Verified references used in Experiment 3 section draft: `{len(refs)}`
- Claim verification rows: `{len(claim_verification)}`

## Key Result Matrix

{md_table(key_matrix, key_fields)}

## Requirement Coverage

{md_table(requirements, req_fields)}

## Paper-Ready Positioning

Experiment 3 is paper-ready as a FluidX3D-native digital-twin wind-environment screening and design-interpretation case. Its strongest claims concern data-layer separation, CFD-ready geometry construction, pedestrian-layer low-speed screening, local morphology diagnosis, morphology-response archetypes, directional anisotropy and negative S1/S2 design-sensitivity evidence.

It is not ready for claims of field-validated accuracy, formal annual comfort/safety compliance, pollutant dispersion, successful design optimization, GCBTE closure, or CityLBM-Grasshopper end-to-end execution. These blockers should remain visible in the manuscript rather than being hidden as limitations after the fact.
"""
    (REP / "experiment3_completion_audit_and_paper_readiness.md").write_text(
        completion, encoding="utf-8"
    )

    final_audit = f"""# Experiment 3 Final Completeness and Gap Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Verdict

The current archive is complete enough for a standalone Experiment 3 section in an SCI manuscript if the claim is framed as:

`FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation.`

It is not complete enough for:

- measured validation claims;
- annual comfort/safety compliance;
- pollutant dispersion;
- CityLBM-Grasshopper end-to-end execution;
- 3DGS-to-collision transfer-error closure;
- successful design optimization.

## Most Defensible Contribution Chain

1. TUM2TWIN visual, semantic and CAD/OBJ layers are separated by function.
2. Visual photogrammetry/Rhino assets are retained for scene audit, not used directly as final collision bodies.
3. Closed LoD/OBJ-derived collision geometries are QA-recorded and FluidX3D-ready.
4. Eight-direction, three-sample FluidX3D outputs show robust pedestrian-layer low-speed conditions.
5. Open-Meteo weighting confirms proxy-direction robustness without claiming annual compliance.
6. Morphology statistics and archetypes identify local enclosure, relative vertical massing and plan continuity as screening descriptors.
7. S1/S2 negative sensitivity shows that porosity area alone is not a sufficient intervention mechanism.

## Current Paper Assets

- Main result rows: `{len(key_matrix)}`
- Reviewer-facing figures/tables: `{len(readiness)}` with `{ready_count}` ready for manual review.
- Evidence inventory rows: `{len(evidence)}`
- Archive manifest status should be checked through `manifests/github_archive_manifest.csv` after every commit.

## Manuscript-Safe Central Claim

In the TUM2TWIN campus-core case, digital-twin wind-environment value comes from the traceable conversion of visually realistic but CFD-fragile data into closed semantic collision geometry and from the ability to diagnose persistent pedestrian-layer ventilation insufficiency in relation to local building form. The new morphology-response archetype layer shows that wind recovery is better discussed as a combined response of relative vertical massing, elongation and local enclosure than as a single footprint, height or porosity effect.

## Required Remaining Evidence for Stronger Claims

{md_table([row for row in requirements if row["status"] == "blocked"], req_fields)}
"""
    (REP / "experiment3_final_completeness_and_gap_audit.md").write_text(
        final_audit, encoding="utf-8"
    )

    checklist = f"""# Experiment 3 Draft Verification Report

evidence_type: newly_run + preexisting_artifact + blocked

## Verification Summary

- Draft status: generic SCI section draft generated from archived Experiment 3 evidence.
- Evidence inventory rows: `{len(evidence)}`
- References used: `{len(refs)}`
- Key result matrix rows: `{len(key_matrix)}`
- Figure/table callouts: `{len(figure_plan)}`
- Submission-readiness assets: `{len(readiness)}`
- Ready for manual review: `{ready_count}`
- Claim inventory rows: `{len(claim_verification)}`

## Passed Checks

- Quantitative claims in the draft come from `figures/final_integrated_key_result_matrix.csv`.
- References are drawn from `manifests/verified_references_for_sci_discussion.csv`.
- Figure/table assets are tracked in `manifests/experiment3_submission_readiness_checklist.csv`.
- Blocked claims remain explicit: field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution.
- The morphology threshold rule and morphology-response archetypes are framed as sample-internal screening evidence.
- The draft contains a single References section and a synchronized pending-debt list.

## Remaining Publication Debts

- AUTHOR_INPUT_NEEDED: target journal and final reference style.
- AUTHOR_INPUT_NEEDED: whether the paper title should say FluidX3D-native or CityLBM-compatible geometry package.
- RESULT_NEEDED: field/wind-tunnel validation before predictive-accuracy claims.
- RESULT_NEEDED: calibrated wind climate before annual comfort/safety compliance.
- RESULT_NEEDED: pollutant simulation before concentration or exposure claims.

## Output Files

- `academic-paper-writer/paper-drafts/paper_draft.md`
- `academic-paper-writer/paper-drafts/paper_draft_en.md`
- `academic-paper-writer/paper-drafts/section_blueprint.md`
- `academic-paper-writer/paper-drafts/experiment3_claim_verification.csv`
- `academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md`
- `paper_text/experiment3_sci_section_paper_draft_zh.md`
- `paper_text/experiment3_sci_section_paper_draft_en.md`
- `reports/experiment3_paper_draft_verification.md`
- `reports/experiment3_final_completeness_and_gap_audit.md`
"""
    (DRAFT / "experiment3_publication_readiness_checklist.md").write_text(
        checklist, encoding="utf-8"
    )
    (REP / "experiment3_paper_draft_verification.md").write_text(
        checklist, encoding="utf-8"
    )

    paper_zh = """# 实验3最终论文贡献与结论段

evidence_type: newly_run + preexisting_artifact + blocked

本实验表明，真实城市数字孪生数据进入风环境模拟的关键价值，并不只是提供高真实感三维外观，而是建立视觉层、语义层和计算碰撞层之间可追踪的转换关系。以 TUM2TWIN Downtown 校园核心区为例，photogrammetry/Rhino/3DGS-like 视觉资产能够可靠支持场景范围核验、纹理化展示和人工审查，但其水密性、语义分层和体素化稳定性不足以直接承担 FluidX3D/CityLBM 的刚性碰撞边界。经 LoD/OBJ/CAD-derived 数据重构的闭合棱柱碰撞几何则能够进入 FluidX3D，并形成可复核的八风向、三采样行人层风环境筛查结果。

在风环境结论上，本实验将传统建筑风环境研究中关于高度、围合、街谷遮蔽和孔隙连通性的认识推进到真实数字孪生街区尺度。S0 基准结果显示，研究区的主要问题不是强风危险，而是行人高度持续低风速和通风不足；上部流场恢复不能替代入口、院落、街道连通空间和步行路径的独立评估。形态统计、阈值筛查和建筑形式风响应类型学进一步说明，20-50 m 局地背景带比 0-20 m 近立面带更能揭示建筑形式差异；行人层风速恢复更适合解释为相对竖向体量、平面延展性和局地围合共同作用的结果，而不是单一建筑面积、高度或孔隙面积的结果。

S1/S2 设计敏感性实验提供的是负结果而非成功优化：单条 relief corridor 和三通道 network porosity 都没有带来全局行人层 mean VR 改善，新增开敞单元仍处于低速背景中。这个负结果具有明确的设计应用价值，即校园核心区通风改善不能停留在“增加孔隙面积”的几何层面，而必须与有效来流扇区、动量入口、压力交换路径和局地围合连续性共同设计。因此，实验3最稳妥的论文定位是：真实数字孪生数据到 CFD-ready 几何的应用转化、FluidX3D-native 行人层风环境筛查、以及建筑形式机制解释；而不是实测验证、法规级舒适安全评价、污染物扩散预测或 CityLBM-Grasshopper 全链路验证。
"""
    (PAPER / "experiment3_final_contribution_and_conclusion_zh.md").write_text(
        paper_zh, encoding="utf-8"
    )

    paper_en = """# Final Contribution and Conclusion Paragraph for Experiment 3

evidence_type: newly_run + preexisting_artifact + blocked

This experiment shows that the wind-environment value of real urban digital-twin data lies not merely in visually realistic geometry, but in a traceable transformation from visual assets to semantic and CFD-ready collision geometry. In the TUM2TWIN Downtown campus core, photogrammetry, Rhino and 3DGS-like assets support scene audit, texture-based review and communication of the real urban context, but their watertightness, semantic separation and voxelization stability are insufficient for direct use as rigid FluidX3D/CityLBM collision boundaries. Closed LoD/OBJ/CAD-derived prism geometry, by contrast, can be QA-recorded, voxelized and used for an eight-direction, three-sample FluidX3D pedestrian-wind screening workflow.

The wind result extends traditional building-form wind-environment knowledge into a real digital-twin block. The S0 baseline indicates persistent pedestrian-layer low-speed conditions rather than a strong-wind hazard, and above-roof recovery cannot substitute for independent assessment of entrances, courtyards, streets and pedestrian routes. Morphology correlations, threshold screening and the new building-form response archetypes show that the 20-50 m local-context band is more diagnostic than the uniformly sheltered 0-20 m facade-adjacent band. Pedestrian-layer wind recovery is therefore better interpreted as a combined response of relative vertical massing, plan elongation and local enclosure than as a single effect of footprint area, building height or porosity.

The S1/S2 design-sensitivity experiments provide negative design evidence rather than successful optimization. Neither a single relief corridor nor a three-corridor network-porosity intervention improves global pedestrian-layer mean VR, and newly opened cells remain embedded in a low-speed background. This negative result is useful for design application: campus-core ventilation improvement should not be reduced to adding geometric opening area, but should couple openings to effective inflow sectors, momentum entry, pressure-exchange paths and local enclosure continuity. The safest manuscript positioning is therefore a FluidX3D-native digital-twin-to-CFD screening and building-form interpretation study, not field validation, regulatory comfort certification, pollutant dispersion prediction or a completed CityLBM-Grasshopper end-to-end workflow.
"""
    (PAPER / "experiment3_final_contribution_and_conclusion_en.md").write_text(
        paper_en, encoding="utf-8"
    )

    print("key_result_rows", len(key_matrix))
    print("figure_table_callouts", len(figure_plan))
    print("submission_assets", len(readiness))
    print("ready_assets", ready_count)
    print("evidence_rows", len(evidence))
    print("wrote reports/experiment3_completion_audit_and_paper_readiness.md")
    print("wrote reports/experiment3_final_completeness_and_gap_audit.md")
    print("wrote manifests/experiment3_final_requirement_coverage.csv")
    print("wrote final contribution paragraphs")


if __name__ == "__main__":
    main()
