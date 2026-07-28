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


def lookup(matrix: pd.DataFrame, claim_layer: str) -> pd.Series:
    row = matrix[matrix["claim_layer"] == claim_layer]
    if row.empty:
        raise ValueError(f"missing claim layer: {claim_layer}")
    return row.iloc[0]


def join_values(matrix: pd.DataFrame, claim_layers: list[str]) -> str:
    return " | ".join(f"{layer}: {lookup(matrix, layer)['value']}" for layer in claim_layers)


def join_sources(matrix: pd.DataFrame, claim_layers: list[str]) -> str:
    sources: list[str] = []
    for layer in claim_layers:
        sources.extend(str(lookup(matrix, layer)["source_artifact"]).split("; "))
    return "; ".join(dict.fromkeys(source.strip() for source in sources if source.strip()))


def build_rq_rows(matrix: pd.DataFrame) -> list[dict[str, str]]:
    return [
        {
            "research_question": "RQ1",
            "question": "How can visually realistic TUM2TWIN digital-twin data be converted into CFD-ready wind-simulation geometry?",
            "evidence_type": "newly_run + preexisting_artifact",
            "source_artifact": join_sources(matrix, ["Geometry-to-CFD readiness"]),
            "key_result": join_values(matrix, ["Geometry-to-CFD readiness"]),
            "paper_answer": "The digital-twin model must be separated into visual audit, semantic geometry and collision-boundary layers; closed LoD/OBJ/CAD-derived prisms are CFD-ready, while photogrammetry is mainly a visual audit layer.",
            "new_insight": "Digital-twin value is not exhausted by visual realism; its wind-environment value depends on the traceability of layer transfer from scene representation to computable boundary.",
            "blocked_claim": "Photogrammetry or 3DGS-like visual geometry directly provides a final rigid CFD collision boundary.",
        },
        {
            "research_question": "RQ2",
            "question": "What is the dominant pedestrian-height wind-environment pattern in the TUM Downtown campus core?",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": join_sources(
                matrix,
                [
                    "S0 baseline pedestrian screening",
                    "Vertical recovery",
                    "Climate-proxy sensitivity",
                    "Effect-size uncertainty",
                    "Directional anisotropy",
                ],
            ),
            "key_result": join_values(
                matrix,
                [
                    "S0 baseline pedestrian screening",
                    "Vertical recovery",
                    "Climate-proxy sensitivity",
                    "Directional anisotropy",
                ],
            ),
            "paper_answer": "The campus core is dominated by persistent pedestrian-layer low-speed and ventilation insufficiency, while the upper layer recovers and the low-speed pattern is not controlled by one exceptional inflow direction.",
            "new_insight": "For this real campus block, the design concern should be framed as insufficient pedestrian ventilation and stagnant sheltered space rather than strong-wind hazard.",
            "blocked_claim": "The result is a field-validated or annual Lawson/NEN/AIJ comfort/safety classification.",
        },
        {
            "research_question": "RQ3",
            "question": "Which basic building-form parameters explain the wind-response pattern at this block scale?",
            "evidence_type": "newly_run + blocked",
            "source_artifact": join_sources(
                matrix,
                [
                    "Morphology robustness",
                    "Morphology threshold design rule",
                    "Building-form response archetypes",
                    "Morphology stage transition",
                    "Morphology directional fingerprint",
                    "Building-form wind mechanism synthesis",
                ],
            ),
            "key_result": join_values(
                matrix,
                [
                    "Morphology robustness",
                    "Morphology stage transition",
                    "Morphology directional fingerprint",
                    "Building-form wind mechanism synthesis",
                ],
            ),
            "paper_answer": "Building-form effects are best interpreted as a staged mechanism: near-facade low-speed saturation, 20-50 m local-context recovery, and wind-sector directional reactivity. Sector enclosure, mean height, relative vertical scale, elongation and combined enclosure are interpretable descriptors.",
            "new_insight": "The useful morphology signal emerges in the 20-50 m context band, not in the uniformly sheltered 0-20 m facade-adjacent band; recovery is a contextual and directional response rather than a single footprint, height or porosity effect.",
            "blocked_claim": "The morphology rules are universal, causal, field-validated thresholds or a high-accuracy predictive surrogate.",
        },
        {
            "research_question": "RQ4",
            "question": "Do simple porosity-based interventions improve the pedestrian wind field?",
            "evidence_type": "newly_run",
            "source_artifact": join_sources(
                matrix,
                ["S1 design sensitivity", "S2 design sensitivity", "Directional local trade-off"],
            ),
            "key_result": join_values(
                matrix,
                ["S1 design sensitivity", "S2 design sensitivity", "Directional local trade-off"],
            ),
            "paper_answer": "S1 and S2 are negative design-sensitivity evidence: neither a single relief corridor nor a stronger network-porosity intervention improves the global pedestrian-layer speed field.",
            "new_insight": "Campus ventilation improvement should not be reduced to adding porosity area; openings need to be aligned with effective wind sectors, momentum-entry paths, pressure exchange and local enclosure continuity.",
            "blocked_claim": "S1/S2 are successful optimized design proposals.",
        },
        {
            "research_question": "RQ5",
            "question": "What is the engineering application potential of a real campus digital twin for wind-environment work?",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": join_sources(
                matrix,
                [
                    "FluidX3D numerical protocol transparency",
                    "Final SCI discussion synthesis",
                    "SCI abstract and highlights readiness",
                ],
            )
            + "; reports/paraview_visualization_package.md; reports/github_archive_manifest_validation.md",
            "key_result": join_values(
                matrix,
                [
                    "FluidX3D numerical protocol transparency",
                    "Final SCI discussion synthesis",
                    "SCI abstract and highlights readiness",
                ],
            ),
            "paper_answer": "The application value is a reproducible screening workflow that links data provenance, geometry QA, FluidX3D simulation, ParaView/Rhino review assets, morphology interpretation and claim-controlled manuscript text.",
            "new_insight": "For campus renewal, the digital twin works as an evidence-management and scenario-screening platform before field-calibrated compliance studies are available.",
            "blocked_claim": "The package is a completed regulatory assessment or a CityLBM-Grasshopper end-to-end application.",
        },
        {
            "research_question": "RQ6",
            "question": "Where must the claim boundary remain explicit before paper submission?",
            "evidence_type": "blocked",
            "source_artifact": "reports/claim_boundary.md; manifests/experiment3_final_requirement_coverage.csv; reports/experiment3_final_completeness_and_gap_audit.md",
            "key_result": "blocked: measured validation; annual comfort/safety compliance; pollutant dispersion; CityLBM-GH execution; GCBTE closure; successful optimization",
            "paper_answer": "Experiment 3 should be submitted as a FluidX3D-native digital-twin-to-CFD screening and building-form interpretation case with CityLBM-compatible geometry preparation.",
            "new_insight": "Making the negative and blocked evidence explicit improves the credibility of the design-application claim because it separates actionable screening knowledge from unsupported engineering certification.",
            "blocked_claim": "All solver validation, compliance, pollutant, GCBTE and CityLBM-GH claims are completed.",
        },
    ]


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    escaped_rows = []
    for row in rows:
        escaped_rows.append(
            {
                field: str(row.get(field, "")).replace("|", "\\|")
                for field in fields
            }
        )
    df = pd.DataFrame(escaped_rows)
    return df[fields].to_markdown(index=False)


def write_reports(rows: list[dict[str, str]]) -> None:
    report = f"""# Experiment 3 Research-Question-to-Evidence Synthesis

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This synthesis converts the completed Experiment 3 archive into explicit
research-question answers for SCI manuscript writing. It does not add new CFD
results. It organizes existing data, morphology analysis, design-sensitivity
tests, protocol evidence and blocked boundaries into a paper-facing argument.

## RQ-to-Evidence Matrix

{md_table(rows, ["research_question", "question", "evidence_type", "key_result", "paper_answer", "blocked_claim"])}

## Paper-Safe Contribution Logic

The experiment answers a sequence of application questions: first, how a
visual digital twin becomes a CFD-ready collision model; second, what wind
problem appears in the real campus block; third, which building-form
descriptors help explain that problem; fourth, why simple porosity
interventions are insufficient; and fifth, how the resulting workflow can be
used as a campus-scale screening tool. The final answer remains bounded by
missing field validation, annual comfort compliance, pollutant modelling,
GCBTE closure and CityLBM-Grasshopper end-to-end evidence.
"""
    write_text(REP / "experiment3_research_question_synthesis.md", report)

    zh = """# 实验 3 研究问题回答段落

evidence_type: newly_run + preexisting_artifact + blocked

本文的第一个研究问题是：真实数字孪生数据如何进入可计算的城市风环境模拟。TUM2TWIN Downtown 案例表明，数字孪生模型不能被视为单一几何对象，而应被拆分为视觉审查层、语义几何层和 CFD 碰撞边界层。photogrammetry visual STL 的 GCRI 为 0.455，而 core closed-prism 与 district-prism collision 几何分别达到 0.925 和 0.918，说明视觉真实度与碰撞边界就绪度是两个不同属性。由此，本文将摄影测量/Rhino/3DGS-like 模型用于真实街区范围和外观一致性审查，将 LoD/OBJ/CAD-derived 闭合几何用于 FluidX3D 碰撞边界。这个结论的意义在于，数字孪生在风环境研究中的价值不是“直接拿来模拟”，而是提供可追踪的数据层转换路径。

第二个研究问题是：TUM Downtown 校园核心区的主导风环境问题是什么。FluidX3D 八风向筛查显示，z~2 m 行人层 mean VR / 低速比例为 0.076 / 0.934，而 z~40 m 为 1.049 / 0.000；Open-Meteo 代理方向权重下 z~2 m 结果为 0.077 / 0.931。结合方向各向异性分析，低速遮蔽不是由单一异常来流方向造成的，而是校园核心区的准全向行人层通风不足。因此，本实验的风环境结论不应被写成强风危险评估，而应写成行人高度低风速、滞风和通风不足筛查。

第三个研究问题是：建筑形式如何解释这种风环境分布。当前结果支持一种分阶段机制，而不是单变量规律。0-20 m 近立面带几乎处于低速饱和状态，能够识别遮蔽但难以区分形态差异；20-50 m 局地上下文带开始显露恢复差异，并与扇区围合度、平均高度、相对竖向体量、平面延展和复合围合状态相关。建筑形式影响因此更适合被解释为“近立面低速饱和 - 局地上下文恢复 - 风向扇区响应”的连续过程，而不是简单归因于面积、高度或孔隙率。

第四个研究问题是：简单孔隙化干预是否足以改善行人层风环境。S1 单通道 relief corridor 与 S2 network porosity 都给出负向或近零结果，z~2 m mean VR 分别变化 -0.000213 和 -0.000466，低速比例反而略增。S2 在 315 deg 出现局部响应，但新增开敞单元仍保持极低风速。这说明校园通风改善不能停留在“增加孔隙面积”，而必须将开口位置与有效来流扇区、动量入口、压力交换路径和局地围合连续性耦合。

第五个研究问题是：数字孪生校园模型的工程应用潜力在哪里。本文最稳妥的应用定位是筛查和设计解释，而不是法规合规认证。该流程把数据来源、几何 QA、FluidX3D 数值协议、ParaView/Rhino 可视化审查、建筑形态统计和证据边界整合为一个可复现包，适合在校园更新早期识别低通风热点、筛除无效干预假设并组织后续高成本实测或风洞验证。当前仍不能宣称实测验证、年度舒适/安全合规、污染物扩散预测、GCBTE 闭环或 CityLBM-Grasshopper 全链路完成。
"""
    write_text(PAPER / "experiment3_research_question_answer_paragraphs_zh.md", zh)

    en = """# Experiment 3 Research-Question Answer Paragraphs

evidence_type: newly_run + preexisting_artifact + blocked

The first research question asks how real digital-twin data can enter computable urban wind simulation. The TUM2TWIN Downtown case shows that the digital twin cannot be treated as a single geometry object; it must be separated into a visual audit layer, a semantic geometry layer and a CFD collision-boundary layer. The photogrammetry visual STL has a GCRI of 0.455, whereas the core closed-prism and district-prism collision geometries reach 0.925 and 0.918. Visual realism and collision-boundary readiness are therefore different properties. In this study, photogrammetry/Rhino/3DGS-like assets support real-block extent and visual-consistency review, while closed LoD/OBJ/CAD-derived geometry is used as the FluidX3D collision boundary. The implication is that the value of the digital twin is not direct simulation from visual geometry, but a traceable data-layer transfer route.

The second research question asks what the dominant wind-environment issue is in the TUM Downtown campus core. The eight-direction FluidX3D screening gives a z~2 m pedestrian-layer mean VR / low-speed ratio of 0.076 / 0.934, whereas the z~40 m values are 1.049 / 0.000. The Open-Meteo proxy-weighted z~2 m result is 0.077 / 0.931. Together with the directional-anisotropy analysis, this indicates that pedestrian low-speed sheltering is not caused by one exceptional inflow direction, but is a quasi-omnidirectional ventilation-insufficiency condition in the campus core. The wind result should therefore be written as pedestrian-height low-speed and stagnation screening, not as a strong-wind hazard assessment.

The third research question asks how building form explains the wind distribution. The current evidence supports a staged mechanism rather than a single-variable rule. The 0-20 m facade-adjacent band is nearly low-speed saturated and can identify sheltering but poorly differentiates morphology. The 20-50 m local-context band begins to reveal recovery differences, which are associated with sector enclosure, mean height, relative vertical scale, plan elongation and combined enclosure states. Building-form influence is therefore better interpreted as a sequence of near-facade low-speed saturation, local-context recovery and wind-sector response, rather than as an isolated effect of footprint area, height or porosity.

The fourth research question asks whether simple porosity interventions are sufficient to improve pedestrian wind. The S1 relief corridor and S2 network-porosity tests both produce negative or near-null global results: z~2 m mean VR changes by -0.000213 and -0.000466, respectively, while the low-speed ratio slightly increases. S2 shows local response under the 315 deg sector, but newly opened cells remain very low speed. This indicates that campus ventilation improvement cannot be reduced to increasing opening area. Openings must be coupled with effective inflow sectors, momentum-entry paths, pressure-exchange routes and local enclosure continuity.

The fifth research question asks where the engineering application potential of the campus digital twin lies. The safest application claim is screening and design interpretation, not regulatory certification. The workflow integrates data provenance, geometry QA, FluidX3D numerical protocol, ParaView/Rhino visual review, building-form statistics and claim boundaries into a reproducible package. It can support early campus-renewal decisions by identifying low-ventilation hotspots, rejecting ineffective intervention hypotheses and organizing later field or wind-tunnel validation. It still cannot claim field validation, annual comfort/safety compliance, pollutant-dispersion prediction, GCBTE closure or completed CityLBM-Grasshopper end-to-end execution.
"""
    write_text(PAPER / "experiment3_research_question_answer_paragraphs_en.md", en)


def upsert_manifests(rows: list[dict[str, str]], matrix: pd.DataFrame) -> None:
    evidence_rows = [
        {
            "claim": "Research-question-to-evidence synthesis was generated from the current Experiment 3 key matrix and claim boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_research_question_evidence_matrix.csv; reports/experiment3_research_question_synthesis.md",
        },
        {
            "claim": "Bilingual research-question answer paragraphs were drafted for SCI Results/Discussion integration with explicit blocked claims.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_research_question_answer_paragraphs_zh.md; paper_text/experiment3_research_question_answer_paragraphs_en.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Research-question synthesis readiness",
        "metric": "RQ-to-evidence matrix / bilingual RQ answer paragraphs / blocked-claim control",
        "value": f"{len(rows)} research questions / {len(matrix)} source key-result rows before RQ upsert",
        "source_artifact": "manifests/experiment3_research_question_evidence_matrix.csv; paper_text/experiment3_research_question_answer_paragraphs_en.md",
        "paper_safe_claim": "Experiment 3 has a research-question-level synthesis that converts the evidence archive into manuscript-ready answers without overclaiming.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [key_row],
        "claim_layer",
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )

    claim_path = DRAFT / "experiment3_claim_verification.csv"
    if claim_path.exists():
        claim_rows = read_csv_rows(claim_path)
        fieldnames = list(claim_rows[0].keys()) if claim_rows else [
            "claim_layer",
            "evidence_type",
            "source",
            "value",
            "paper_safe_claim",
            "claim_readiness",
        ]
        row = {
            "claim_layer": "module_claim_RQ_SYNTHESIS",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_research_question_evidence_matrix.csv; reports/experiment3_research_question_synthesis.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Research-question answers are evidence-mapped and keep blocked claims visible.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        claim_rows = [item for item in claim_rows if item.get("claim_layer") != "module_claim_RQ_SYNTHESIS"]
        claim_rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(claim_path, claim_rows, fieldnames)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    rows = build_rq_rows(matrix)
    write_csv(
        MAN / "experiment3_research_question_evidence_matrix.csv",
        rows,
        [
            "research_question",
            "question",
            "evidence_type",
            "source_artifact",
            "key_result",
            "paper_answer",
            "new_insight",
            "blocked_claim",
        ],
    )
    write_reports(rows)
    upsert_manifests(rows, matrix)
    print("research_questions", len(rows))
    print("key_result_rows_before_rq_upsert", len(matrix))
    print("wrote research-question synthesis")


if __name__ == "__main__":
    main()
