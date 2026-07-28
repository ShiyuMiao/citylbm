from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, rows_to_add: list[dict[str, str]], key: str, fieldnames: list[str]) -> None:
    rows = read_csv_rows(path)
    current = {row.get(key, ""): row for row in rows}
    for row in rows_to_add:
        current[row[key]] = row
    write_csv(path, list(current.values()), fieldnames)


def matrix_lookup(matrix: pd.DataFrame, claim_layer: str) -> pd.Series:
    row = matrix[matrix["claim_layer"] == claim_layer]
    if row.empty:
        raise ValueError(f"missing key-result claim layer: {claim_layer}")
    return row.iloc[0]


def build_paragraph_map(matrix: pd.DataFrame) -> list[dict[str, str]]:
    lookup = {row["claim_layer"]: row for _, row in matrix.iterrows()}
    rows = [
        {
            "paragraph_id": "D1",
            "section_role": "opening_positioning",
            "main_claim": "Experiment 3 should be framed as digital-twin-to-CFD wind screening rather than solver validation or compliance assessment.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "primary_sources": "reports/experiment3_final_completeness_and_gap_audit.md; reports/claim_boundary.md; reports/experiment3_reviewer_reproducibility_and_claim_audit.md",
            "key_numbers_or_terms": "FluidX3D-native; CityLBM-compatible geometry; blocked validation/compliance claims",
            "allowed_wording": "supports a reproducible screening workflow",
            "blocked_wording": "proves predictive accuracy; completes annual comfort compliance",
        },
        {
            "paragraph_id": "D2",
            "section_role": "digital_twin_data_model_performance",
            "main_claim": "The core digital-twin contribution is layer separation: visual photogrammetry supports scene audit, while closed semantic/CAD-derived geometry supports collision boundaries.",
            "evidence_type": "newly_run + preexisting_artifact",
            "primary_sources": lookup["Geometry-to-CFD readiness"]["source_artifact"],
            "key_numbers_or_terms": lookup["Geometry-to-CFD readiness"]["value"],
            "allowed_wording": "visual fidelity and CFD readiness are separable",
            "blocked_wording": "photogrammetry or 3DGS is directly CFD-ready",
        },
        {
            "paragraph_id": "D3",
            "section_role": "numerical_protocol_and_main_wind_result",
            "main_claim": "The archived FluidX3D protocol supports pedestrian-height low-speed screening and vertical-recovery interpretation.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "primary_sources": lookup["S0 baseline pedestrian screening"]["source_artifact"] + "; " + lookup["FluidX3D numerical protocol transparency"]["source_artifact"],
            "key_numbers_or_terms": lookup["S0 baseline pedestrian screening"]["value"] + "; " + lookup["Vertical recovery"]["value"],
            "allowed_wording": "low-speed screening; upper-layer recovery does not replace pedestrian assessment",
            "blocked_wording": "formal convergence; field validation; annual threshold exceedance",
        },
        {
            "paragraph_id": "D4",
            "section_role": "climate_proxy_boundary",
            "main_claim": "Open-Meteo weighting is a climate proxy sensitivity layer and should not be treated as a measured wind rose.",
            "evidence_type": "newly_run + preexisting_artifact",
            "primary_sources": lookup["Climate-proxy sensitivity"]["source_artifact"],
            "key_numbers_or_terms": lookup["Climate-proxy sensitivity"]["value"],
            "allowed_wording": "proxy-weighted low-speed conclusion is consistent with equal weighting",
            "blocked_wording": "annual Lawson/NEN/AIJ compliance",
        },
        {
            "paragraph_id": "D5",
            "section_role": "building_form_mechanism",
            "main_claim": "Building-form effects are best interpreted as staged near-facade saturation, 20-50 m local-context recovery and wind-sector reactivity.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "primary_sources": lookup["Building-form wind mechanism synthesis"]["source_artifact"],
            "key_numbers_or_terms": lookup["Building-form wind mechanism synthesis"]["value"],
            "allowed_wording": "sample-internal screening mechanism",
            "blocked_wording": "universal causal morphology law",
        },
        {
            "paragraph_id": "D6",
            "section_role": "design_application_negative_evidence",
            "main_claim": "S1/S2 show that porosity area alone is insufficient without wind-sector and momentum-entry coupling.",
            "evidence_type": "newly_run",
            "primary_sources": lookup["S1 design sensitivity"]["source_artifact"] + "; " + lookup["S2 design sensitivity"]["source_artifact"] + "; " + lookup["Directional local trade-off"]["source_artifact"],
            "key_numbers_or_terms": lookup["S1 design sensitivity"]["value"] + "; " + lookup["S2 design sensitivity"]["value"] + "; " + lookup["Directional local trade-off"]["value"],
            "allowed_wording": "negative design-sensitivity evidence",
            "blocked_wording": "successful design optimization",
        },
        {
            "paragraph_id": "D7",
            "section_role": "limitations_and_future_work",
            "main_claim": "The supported package remains bounded by missing field/wind-tunnel validation, annual compliance, pollutant dispersion, GCBTE and CityLBM-GH execution.",
            "evidence_type": "blocked",
            "primary_sources": "reports/claim_boundary.md; manifests/experiment3_final_requirement_coverage.csv; manifests/gcbte_status_table.csv",
            "key_numbers_or_terms": "blocked: validation, compliance, pollutant, GCBTE, CityLBM-GH",
            "allowed_wording": "remaining evidence required for stronger claims",
            "blocked_wording": "fully validated deployment-ready prediction",
        },
        {
            "paragraph_id": "C1",
            "section_role": "conclusion_takeaway",
            "main_claim": "Experiment 3 contributes an auditable real-campus digital-twin workflow and a building-form wind-screening interpretation.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "primary_sources": "figures/final_integrated_key_result_matrix.csv; reports/experiment3_completion_audit_and_paper_readiness.md",
            "key_numbers_or_terms": f"{len(matrix)} source key-result rows before final-discussion upsert",
            "allowed_wording": "auditable workflow and screening-level architectural mechanism",
            "blocked_wording": "final regulatory or field-validated design rule",
        },
    ]
    return rows


def write_discussion_text() -> None:
    zh = """# Experiment 3 最终 SCI 讨论与结论模块

evidence_type: newly_run + preexisting_artifact + blocked

## Discussion

本实验应被定位为真实城市数字孪生数据进入风环境模拟的应用转化研究，而不是求解器精度验证或法规级舒适度评价。AIJ Case A 和 Case E 已承担前序基准/验证支撑，Experiment 3 的核心问题则是：TUM2TWIN 这类真实校园数字孪生数据能否从视觉资产转化为 CFD-ready 几何，并进一步支持可审计的行人层风环境筛查和建筑形式解释。基于当前证据，最稳妥的表述是 FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation；不应写成实测验证、年度舒适安全合规或 CityLBM-Grasshopper 端到端验证。

数字孪生底层模型的表现说明，视觉真实并不等同于计算就绪。TUM2TWIN 的 photogrammetry/Rhino/3DGS-like 资产能够很好支持场景范围核验、贴图化视觉审查和人工一致性判断，但其非闭合、纹理化和语义不足的特征不适合作为最终刚性碰撞边界。相反，经过 LoD/OBJ/CAD-derived 数据重构的闭合棱柱碰撞几何在 GCRI 中显著优于 photogrammetry visual STL：后者 GCRI 为 0.455，而 core closed-prism collision 和 district prism collision 分别达到 0.925 和 0.918。因此，本实验对数字孪生风环境研究的直接贡献，是把“视觉孪生”拆分为视觉审查层、语义几何层和 CFD 碰撞层，而不是把三维外观模型直接送入求解器。

在数值协议层面，当前 FluidX3D case 已足以支撑筛查性结论。核心算例记录了 dx = 2 m、320 x 390 x 60 网格、Uref = 5 m/s、空气运动黏度 1.5e-5 m2/s、tau = 0.52999996、8 个来流方向以及 8000/10000/12000 steps 三个后 spin-up 样本。S0 基准显示，z~2 m 行人层 mean VR / 低速比例为 0.076 / 0.934，而 z~40 m 为 1.049 / 0.000。这说明研究区主要问题不是强风危险，而是行人高度持续低风速和通风不足；屋面以上流场恢复不能替代入口、院落、街道连通空间和步行路径的独立评价。

气候权重结果也应保守解释。Open-Meteo 2024 加权后的 z~2 m mean VR / 低速比例为 0.077 / 0.931，与八风向等权结果接近。这支持“低速格局对当前代理方向权重不敏感”的筛查结论，但 Open-Meteo 在本研究中只是气候方向权重代理，不是现场实测风玫瑰，更不能支持 Lawson、NEN 8100 或 AIJ 的年度超越概率舒适/安全合规判断。

建筑形式与风环境之间的关系应被写成分阶段机制，而非单变量规律。0-20 m 近立面带 mean VR 仅为 0.0032，滞风比例接近 1.0000，说明该区域几乎处于低速饱和状态，适合识别行人层遮蔽但不适合区分形态差异。20-50 m 局地上下文带 mean VR 提升至 0.0056，并出现平均 0.0024 的 near-to-context recovery delta，才开始显露建筑形式差异。在这一尺度，50 m 扇区围合度、平均高度和复合围合分数与局地 mean VR 和方向性 range 均呈稳定负相关；footprint、延展率和紧凑度不是可靠的独立预测器，但能在低相对竖向尺度、线性平面和特定围合组合中帮助识别恢复型子群。由此，本研究相对传统“围合削弱通风”的新认知在于：真实校园街区中的通风恢复不仅取决于开敞或孔隙面积，还取决于近立面遮蔽是否能过渡到 20-50 m 局地恢复，以及这种恢复是否具有风向扇区响应。

S1/S2 设计敏感性进一步把这一机制收束为负向设计证据。S1 single relief corridor 的 z~2 m mean VR / 低速比例变化为 -0.000213 / 0.000233，S2 network porosity 为 -0.000466 / 0.000633。即使 S2 在 315 deg 存在最强局部响应，新增开敞单元的最高 mean VR 也仅为 0.006646，且低速比例仍为 1.000。因此，S1/S2 不能写成成功优化方案；它们的价值在于证明，仅增加孔隙面积或廊道数量不足以恢复校园核心区通风。有效干预需要同时考虑风向扇区、动量入口、压力交换路径和局地围合连续性。

本实验仍有明确边界。当前证据不支持现场实测或风洞闭环验证，不支持正式年度舒适/安全合规，不支持污染物扩散结果，不支持 GCBTE 3DGS-to-collision 误差闭合，也不支持 CityLBM-Grasshopper 端到端实跑。后续若要将筛查结论升级为工程评价，需要补充校准风气候、实测或风洞验证、残差/统计收敛记录、网格无关性、污染物传输和至少一组与风向扇区耦合的正向设计干预。

## Conclusion

Experiment 3 证明，TUM2TWIN 真实校园数字孪生数据可以通过视觉审查、语义/LoD 几何重构、闭合碰撞边界生成、FluidX3D 八风向筛查和 ParaView/Rhino 人工审核，转化为可复现的城市风环境应用实验。其最重要的科学结论是：该校园核心区的行人层问题以低风速和通风不足为主，建筑形式影响呈现“近立面低速饱和 - 20-50 m 局地恢复 - 风向扇区响应”的分阶段机制；设计干预不能只追求孔隙面积，而应围绕有效动量入口和压力交换路径组织。该结论是数字孪生/FluidX3D 筛查证据，不是实测验证后的法规级评价。"""

    en = """# Experiment 3 Final SCI Discussion and Conclusion Module

evidence_type: newly_run + preexisting_artifact + blocked

## Discussion

Experiment 3 should be positioned as an application-transfer study for real urban digital-twin data, not as a solver-validation or regulatory comfort-compliance study. AIJ Cases A and E provide the preceding benchmark layer. The question in Experiment 3 is whether TUM2TWIN campus data can be converted from visual assets into CFD-ready geometry and then used for auditable pedestrian wind screening and architectural interpretation. The safest framing is FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation. The archive should not be described as field validation, annual comfort/safety compliance or completed CityLBM-Grasshopper end-to-end execution.

The digital-twin model performance shows that visual realism is not the same as computational readiness. TUM2TWIN photogrammetry, Rhino and 3DGS-like assets are valuable for scope checking, textured visual audit and manual consistency review, but their non-watertight, textured and weakly semantic nature makes them unsuitable as final rigid collision boundaries. Closed LoD/OBJ/CAD-derived prism geometries are much more CFD-ready: the photogrammetry visual STL has a GCRI of 0.455, whereas the core closed-prism and district-prism collision geometries reach 0.925 and 0.918. The direct contribution is therefore a layer-separated digital-twin workflow: visual audit layer, semantic geometry layer and CFD collision layer.

The archived FluidX3D protocol is sufficient for screening-level interpretation. The core case records dx = 2 m, a 320 x 390 x 60 lattice, Uref = 5 m/s, air kinematic viscosity of 1.5e-5 m2/s, tau = 0.52999996, eight inflow directions and three post-spin-up samples at 8000, 10000 and 12000 steps. In S0, the z~2 m pedestrian-layer mean VR / low-speed ratio is 0.076 / 0.934, whereas at z~40 m it is 1.049 / 0.000. The main campus-core issue is therefore persistent pedestrian-height low speed and insufficient ventilation, not strong-wind hazard. Above-roof recovery cannot replace separate assessment of entrances, courtyards, connected street spaces and walking paths.

The climate-weighted result must also be interpreted conservatively. Open-Meteo 2024 weighting gives a z~2 m mean VR / low-speed ratio of 0.077 / 0.931, close to the equal-weighted result. This supports the screening statement that the low-speed pattern is insensitive to the current proxy directional weighting. It does not constitute a measured wind rose or support annual Lawson, NEN 8100 or AIJ exceedance-probability comfort/safety classification.

The relationship between building form and wind environment is best written as a staged mechanism rather than a single-variable law. The 0-20 m facade-adjacent band has a mean VR of only 0.0032 and an almost complete low-speed ratio of 1.0000, so it identifies pedestrian sheltering but poorly separates morphology effects. The 20-50 m local-context band increases to a mean VR of 0.0056 and produces an average near-to-context recovery delta of 0.0024, exposing morphology-dependent recovery. At this scale, 50 m sector enclosure, mean height and combined enclosure are consistent suppressors of local mean VR and directional range. Footprint, elongation and compactness are not reliable standalone predictors, but they help identify recovery subgroups when combined with low relative vertical scale, linear plan form and specific enclosure states. The new insight beyond the traditional enclosure argument is that campus ventilation recovery depends not only on open area or porosity, but on whether near-facade sheltering transitions into 20-50 m contextual recovery and whether that recovery carries wind-sector response.

The S1/S2 sensitivity cases turn this mechanism into negative design evidence. S1 changes z~2 m mean VR / low-speed ratio by -0.000213 / 0.000233, and S2 changes them by -0.000466 / 0.000633. Even though S2 has its strongest local response at 315 deg, newly opened cells reach only a maximum mean VR of 0.006646 and remain fully low speed. Thus, S1/S2 are not successful optimization schemes. Their value is to show that adding porosity area or corridor count alone is insufficient; effective intervention must align wind sectors, momentum-entry paths, pressure exchange and local enclosure continuity.

The evidence boundary remains explicit. The archive does not support field or wind-tunnel validation, annual comfort/safety compliance, pollutant dispersion, GCBTE closure or CityLBM-Grasshopper end-to-end execution. Upgrading the screening result into an engineering assessment would require calibrated wind climate, field or wind-tunnel validation, residual/statistical convergence records, grid independence, pollutant transport and at least one wind-sector-coupled positive design intervention.

## Conclusion

Experiment 3 shows that TUM2TWIN real campus digital-twin data can be converted through visual audit, semantic/LoD geometry reconstruction, closed collision-boundary generation, FluidX3D eight-direction screening and ParaView/Rhino manual review into a reproducible urban wind-environment application experiment. Its main scientific finding is that the campus core is dominated by pedestrian-layer low speed and ventilation insufficiency, and that building-form influence follows a staged mechanism of near-facade low-speed saturation, 20-50 m local-context recovery and wind-sector response. Design intervention should therefore move beyond porosity area and target effective momentum-entry and pressure-exchange paths. This is digital-twin/FluidX3D screening evidence, not field-validated regulatory evaluation."""
    write_text(PAPER / "experiment3_final_sci_discussion_conclusion_zh.md", zh)
    write_text(PAPER / "experiment3_final_sci_discussion_conclusion_en.md", en)


def write_report(paragraph_rows: list[dict[str, str]]) -> None:
    table = pd.DataFrame(paragraph_rows).to_markdown(index=False)
    report = f"""# Experiment 3 Final SCI Discussion Evidence Map

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This package is the final discussion-level synthesis for Experiment 3. It does
not add CFD results; it maps each discussion/conclusion paragraph to verified
artifacts, allowed wording and blocked wording. Use it when integrating
Experiment 3 into the full SCI manuscript.

## Paragraph Evidence Map

{table}

## Use In Manuscript

- Use `paper_text/experiment3_final_sci_discussion_conclusion_zh.md` for the
  Chinese final discussion/conclusion module.
- Use `paper_text/experiment3_final_sci_discussion_conclusion_en.md` for the
  English final discussion/conclusion module.
- Keep all blocked wording out of the final paper unless new evidence is added.
"""
    write_text(REP / "experiment3_final_sci_discussion_evidence_map.md", report)


def upsert_manifests(matrix: pd.DataFrame) -> None:
    evidence_rows = [
        {
            "claim": "Final SCI discussion and conclusion module was synthesized from the key result matrix, mechanism synthesis, numerical protocol audit and claim boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_final_sci_discussion_conclusion_zh.md; paper_text/experiment3_final_sci_discussion_conclusion_en.md; reports/experiment3_final_sci_discussion_evidence_map.md",
        },
        {
            "claim": "Each final discussion paragraph was mapped to source artifacts, allowed wording and blocked wording.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_final_discussion_paragraph_evidence_map.csv",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Final SCI discussion synthesis",
        "metric": "paragraph evidence map / final bilingual discussion-conclusion module / blocked wording control",
        "value": f"8 mapped paragraphs / {len(matrix)} source key-result rows before final upsert / blocked validation-compliance-pollutant-GCBTE-CityLBM claims retained",
        "source_artifact": "manifests/experiment3_final_discussion_paragraph_evidence_map.csv; paper_text/experiment3_final_sci_discussion_conclusion_zh.md",
        "paper_safe_claim": "Experiment 3 is ready as a manuscript discussion module when framed as digital-twin-to-CFD wind screening with explicit evidence boundaries.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [key_row],
        "claim_layer",
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )

    if (DRAFT / "experiment3_claim_verification.csv").exists():
        rows = read_csv_rows(DRAFT / "experiment3_claim_verification.csv")
        fieldnames = list(rows[0].keys()) if rows else ["claim_layer", "evidence_type", "source", "value", "paper_safe_claim", "claim_readiness"]
        row = {
            "claim_layer": "module_claim_FINAL_DISCUSSION",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_final_discussion_paragraph_evidence_map.csv; reports/experiment3_final_sci_discussion_evidence_map.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Final discussion/conclusion paragraphs are mapped to evidence and retain blocked claim boundaries.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        rows = [item for item in rows if item.get("claim_layer") != "module_claim_FINAL_DISCUSSION"]
        rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(DRAFT / "experiment3_claim_verification.csv", rows, fieldnames)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    paragraph_rows = build_paragraph_map(matrix)
    write_csv(
        MAN / "experiment3_final_discussion_paragraph_evidence_map.csv",
        paragraph_rows,
        [
            "paragraph_id",
            "section_role",
            "main_claim",
            "evidence_type",
            "primary_sources",
            "key_numbers_or_terms",
            "allowed_wording",
            "blocked_wording",
        ],
    )
    write_discussion_text()
    write_report(paragraph_rows)
    upsert_manifests(matrix)
    print("final_discussion_paragraphs", len(paragraph_rows))
    print("key_result_rows_before_final_upsert", len(matrix))
    print("wrote final SCI discussion package")


if __name__ == "__main__":
    main()
