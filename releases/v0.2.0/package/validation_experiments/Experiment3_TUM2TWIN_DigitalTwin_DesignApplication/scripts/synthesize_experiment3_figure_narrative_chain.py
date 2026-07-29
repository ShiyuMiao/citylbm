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


def readiness_lookup(readiness: pd.DataFrame) -> dict[str, pd.Series]:
    return {str(row["asset_id"]): row for _, row in readiness.iterrows()}


def build_rows(plan: pd.DataFrame, readiness: pd.DataFrame) -> list[dict[str, str]]:
    assets = readiness_lookup(readiness)
    narrative = {
        "Fig. E3-1": {
            "manuscript_position": "Main Figure 1 / Results opening",
            "result_question": "What is the baseline pedestrian wind problem in the real campus block?",
            "primary_claim": "The baseline is a low-speed and insufficient-ventilation problem at pedestrian height.",
            "narrative_role": "establishes the core wind-environment phenomenon before morphology and design interpretation",
            "boundary": "not annual comfort compliance, field validation or pollutant dispersion",
            "manual_review_action": "verify spatial alignment between low-speed/stagnation maps and the TUM Downtown block before submission",
        },
        "Fig. E3-2": {
            "manuscript_position": "Main Figure 2 / Building-form explanation",
            "result_question": "Which basic morphology descriptors explain the 20-50 m local-context response?",
            "primary_claim": "Sector enclosure, mean height and combined enclosure are interpretable screening descriptors, while model power remains limited.",
            "narrative_role": "translates traditional building-form wind logic into quantitative digital-twin descriptors",
            "boundary": "not a high-accuracy surrogate model or externally validated threshold",
            "manual_review_action": "check axis labels, coefficient signs and whether the caption keeps the screening-only language",
        },
        "Fig. E3-3": {
            "manuscript_position": "Main Figure 3 / Design sensitivity",
            "result_question": "Do S1/S2 porosity interventions improve pedestrian ventilation?",
            "primary_claim": "S1/S2 are negative sensitivity evidence; porosity alone does not restore the global pedestrian-layer speed field.",
            "narrative_role": "turns the baseline diagnosis into design-application evidence by rejecting insufficient intervention logic",
            "boundary": "not successful optimization or final design recommendation",
            "manual_review_action": "verify that positive local cells are not visually overstated relative to sparse global response",
        },
        "Fig. E3-4": {
            "manuscript_position": "Main Figure 4 / Mechanism synthesis",
            "result_question": "Where does the building-form signal become visible?",
            "primary_claim": "The 20-50 m local-context band reveals recovery hidden by near-facade low-speed saturation.",
            "narrative_role": "provides the main architectural mechanism: near-facade shelter, contextual recovery and conditional morphology signals",
            "boundary": "not a universal or field-validated morphology threshold",
            "manual_review_action": "check whether the rule is labelled as sample-internal and not a code-like design criterion",
        },
        "Fig. E3-S1": {
            "manuscript_position": "Supplementary Figure S1 / Robustness",
            "result_question": "Are core numerical patterns stable within the archived direction-sample layer?",
            "primary_claim": "Low-speed baseline, vertical recovery and S1/S2 negative results are stable within archived samples.",
            "narrative_role": "supports uncertainty language for the main result figures",
            "boundary": "not measurement uncertainty, grid convergence or annual exceedance probability",
            "manual_review_action": "check that confidence/range wording is tied to archived samples only",
        },
        "Fig. E3-S2": {
            "manuscript_position": "Supplementary Figure S2 / Directionality",
            "result_question": "Is the low-speed result controlled by one inflow direction?",
            "primary_claim": "Pedestrian low-speed sheltering is quasi-omnidirectional, while local design response is sector-sensitive.",
            "narrative_role": "supports wind-sector-coupled design reasoning",
            "boundary": "not measured wind rose, annual compliance or successful optimization",
            "manual_review_action": "check that the 315 deg local response is described as local and sparse",
        },
        "Fig. E3-S3": {
            "manuscript_position": "Supplementary Figure S3 / Morphology archetypes",
            "result_question": "Do combined morphology groups reveal wind-response differences?",
            "primary_claim": "Recovery differs across combined morphology archetypes involving relative massing, elongation and enclosure.",
            "narrative_role": "adds typological interpretation behind the main morphology figure",
            "boundary": "not causal taxonomy or universal design class",
            "manual_review_action": "check cluster names and avoid implying external typology validation",
        },
        "Fig. E3-S4": {
            "manuscript_position": "Supplementary Figure S4 / Stage transition",
            "result_question": "How does wind response change from facade-adjacent shelter to local-context recovery?",
            "primary_claim": "The same 101 components move from saturated near-facade shelter to differentiated 20-50 m recovery.",
            "narrative_role": "supports the staged mechanism used in the main discussion",
            "boundary": "not field validation, annual comfort compliance or universal morphology threshold",
            "manual_review_action": "check that component count, bands and stage labels are legible",
        },
        "Fig. E3-S5": {
            "manuscript_position": "Supplementary Figure S5 / Directional fingerprint",
            "result_question": "Does useful recovery require wind-sector response as well as mean VR recovery?",
            "primary_claim": "Recovery/reactive components show stronger local wind-sector fingerprints than persistent-shelter components.",
            "narrative_role": "supports the argument that design should target sector-coupled momentum exchange",
            "boundary": "not field-validated directional threshold or annual wind-rose compliance",
            "manual_review_action": "check that directional range is not presented as a universal metric",
        },
        "Table E3-1": {
            "manuscript_position": "Main Table 1 / Result matrix",
            "result_question": "Which quantitative results support the paper claims?",
            "primary_claim": "The paper-facing claims are traceable to evidence type, metric value, source artifact and safe wording.",
            "narrative_role": "acts as the one-page evidence backbone for Results and Discussion",
            "boundary": "not a substitute for raw data or solver logs",
            "manual_review_action": "verify all numbers quoted in text match this table before submission",
        },
        "Table E3-2": {
            "manuscript_position": "Supplementary Table 1 / Paper-readiness audit",
            "result_question": "Which claims are complete and which remain blocked?",
            "primary_claim": "Experiment 3 is complete as screening/design interpretation and incomplete for validation/compliance/pollutant/GCBTE/CityLBM-GH claims.",
            "narrative_role": "keeps claim strength explicit for reviewers",
            "boundary": "not evidence that blocked items are completed",
            "manual_review_action": "check that manuscript wording follows the blocked-claim rows",
        },
        "Table E3-3": {
            "manuscript_position": "Main or Supplementary Table / Geometry method",
            "result_question": "Why is photogrammetry not used as the final collision geometry?",
            "primary_claim": "GCRI separates visual reference from closed collision-boundary readiness.",
            "narrative_role": "supports the digital-twin-to-CFD methodological contribution",
            "boundary": "GCRI is a study-defined readiness index, not an external universal standard",
            "manual_review_action": "check weight definitions and make clear that visual STL is a counterexample/reference layer",
        },
    }

    rows: list[dict[str, str]] = []
    for _, item in plan.iterrows():
        asset_id = str(item["callout_id"])
        ready = assets.get(asset_id)
        spec = narrative[asset_id]
        rows.append(
            {
                "asset_id": asset_id,
                "asset_type": str(ready["asset_type"]) if ready is not None else "",
                "relative_path": str(ready["relative_path"]) if ready is not None else str(item["recommended_file"]),
                "exists": str(ready["exists"]) if ready is not None else "unknown",
                "evidence_type": str(ready["evidence_type"]) if ready is not None else "",
                "manuscript_position": spec["manuscript_position"],
                "result_question": spec["result_question"],
                "primary_claim": spec["primary_claim"],
                "narrative_role": spec["narrative_role"],
                "boundary": spec["boundary"],
                "manual_review_action": spec["manual_review_action"],
            }
        )
    return rows


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    escaped = [
        {field: str(row.get(field, "")).replace("|", "\\|") for field in fields}
        for row in rows
    ]
    return pd.DataFrame(escaped)[fields].to_markdown(index=False)


def write_reports(rows: list[dict[str, str]]) -> None:
    fields = [
        "asset_id",
        "manuscript_position",
        "result_question",
        "primary_claim",
        "boundary",
        "manual_review_action",
    ]
    report = f"""# Experiment 3 Figure and Table Narrative Chain

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This file maps each planned Experiment 3 figure and table to its role in the
SCI manuscript argument. It does not create new results. It prevents figures
from being used to support stronger claims than their evidence type allows.

## Figure/Table Narrative Matrix

{md_table(rows, fields)}

## Recommended Manuscript Sequence

Use Fig. E3-1 to open the Results section with the real campus pedestrian
low-speed problem. Use Table E3-3 and/or Table E3-1 to establish the
digital-twin-to-CFD method evidence. Then use Fig. E3-2, Fig. E3-4 and the
morphology supplementary figures to develop the building-form mechanism. Use
Fig. E3-3 and Fig. E3-S2 for the design-sensitivity and wind-sector discussion.
Close the Results/Discussion boundary with Table E3-2 and the limitations
roadmap rather than implying validation, compliance or optimization success.
"""
    write_text(REP / "experiment3_figure_table_narrative_chain.md", report)

    zh = """# 实验 3 图表叙事链段落

evidence_type: newly_run + preexisting_artifact + blocked

本文图表顺序应服务于一条清晰的证据链，而不是简单罗列后处理结果。建议首先使用 Fig. E3-1 呈现 TUM Downtown 核心区的行人层低速与滞风分布，把论文问题明确为“通风不足筛查”而不是强风危险或舒适合规评价。随后使用 Table E3-3 和 Table E3-1 说明数字孪生底层模型如何从视觉审查层转化为 CFD-ready 碰撞边界，并把 GCRI、FluidX3D 协议、核心指标和证据类型统一到一个可审计表格中。

建筑形式分析可由 Fig. E3-2 和 Fig. E3-4 作为主文图支撑。Fig. E3-2 强调基础形态参数的解释性而非预测精度，Fig. E3-4 则把 0-20 m 近立面低速饱和与 20-50 m 局地恢复连接起来。补充图 Fig. E3-S3、E3-S4 和 E3-S5 分别承担形态响应类型、阶段转化和风向指纹的解释任务，用来支撑“建筑形式影响是分阶段、局地上下文和风向扇区共同作用”的结论。

设计应用部分应使用 Fig. E3-3 和 Fig. E3-S2，而不是把 S1/S2 写成优化成功。图表叙事应明确：S1/S2 的价值在于提供负向敏感性证据，说明单纯增加孔隙面积或通道数量不能恢复全局行人层通风。最后，Table E3-2 与局限性路线图应放在 Discussion 末尾，用于说明本实验已完成筛查与设计解释，但仍未完成实测验证、年度舒适安全合规、污染物扩散、GCBTE 和 CityLBM-Grasshopper 端到端证据。
"""
    write_text(PAPER / "experiment3_figure_table_narrative_chain_zh.md", zh)

    en = """# Experiment 3 Figure and Table Narrative Paragraphs

evidence_type: newly_run + preexisting_artifact + blocked

The figures and tables should follow a claim-building sequence rather than a simple list of post-processing outputs. Fig. E3-1 should open the Results section by showing the pedestrian-layer low-speed and stagnation pattern in the TUM Downtown core, thereby framing the problem as ventilation-insufficiency screening rather than strong-wind hazard or compliance assessment. Table E3-3 and Table E3-1 should then establish how the digital-twin source data are transferred from visual audit layers to CFD-ready collision geometry and how the main GCRI, FluidX3D protocol, result metrics and evidence types are made auditable.

The building-form analysis should be supported by Fig. E3-2 and Fig. E3-4 in the main text. Fig. E3-2 emphasizes the interpretability of basic morphology descriptors rather than predictive accuracy, while Fig. E3-4 connects 0-20 m facade-adjacent low-speed saturation with 20-50 m local-context recovery. Supplementary Figs. E3-S3, E3-S4 and E3-S5 then provide the detailed morphology-response archetype, stage-transition and directional-fingerprint evidence behind the conclusion that building-form influence is staged, contextual and wind-sector dependent.

The design-application section should use Fig. E3-3 and Fig. E3-S2 without presenting S1/S2 as successful optimizations. Their role is to show negative sensitivity evidence: increasing porosity area or corridor count alone does not restore global pedestrian-layer ventilation. Finally, Table E3-2 and the limitations roadmap should close the Discussion by clarifying that Experiment 3 supports screening and design interpretation, but not field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE closure or CityLBM-Grasshopper end-to-end execution.
"""
    write_text(PAPER / "experiment3_figure_table_narrative_chain_en.md", en)


def upsert_outputs(rows: list[dict[str, str]], key_count: int) -> None:
    write_csv(
        MAN / "experiment3_figure_table_narrative_chain.csv",
        rows,
        [
            "asset_id",
            "asset_type",
            "relative_path",
            "exists",
            "evidence_type",
            "manuscript_position",
            "result_question",
            "primary_claim",
            "narrative_role",
            "boundary",
            "manual_review_action",
        ],
    )

    evidence_rows = [
        {
            "claim": "Experiment 3 figure/table narrative chain was generated from the current figure plan and submission-readiness checklist.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_figure_table_narrative_chain.csv; reports/experiment3_figure_table_narrative_chain.md",
        },
        {
            "claim": "Bilingual figure/table narrative paragraphs were drafted to connect figures and tables to Results/Discussion claims without overclaiming.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_figure_table_narrative_chain_zh.md; paper_text/experiment3_figure_table_narrative_chain_en.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Figure-table narrative readiness",
        "metric": "figure/table narrative matrix / bilingual figure-order paragraphs / manual-review actions",
        "value": f"{len(rows)} figure-table assets / {key_count} source key-result rows before figure-narrative upsert",
        "source_artifact": "manifests/experiment3_figure_table_narrative_chain.csv; reports/experiment3_figure_table_narrative_chain.md",
        "paper_safe_claim": "Experiment 3 has a figure/table narrative chain that ties each visual asset to a specific manuscript claim and boundary.",
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
            "claim_layer": "module_claim_FIGURE_TABLE_NARRATIVE",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_figure_table_narrative_chain.csv; reports/experiment3_figure_table_narrative_chain.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Figure/table narrative order is evidence-mapped and preserves claim boundaries.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        claim_rows = [item for item in claim_rows if item.get("claim_layer") != "module_claim_FIGURE_TABLE_NARRATIVE"]
        claim_rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(claim_path, claim_rows, fieldnames)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    plan = pd.read_csv(MAN / "experiment3_manuscript_figure_table_plan.csv")
    readiness = pd.read_csv(MAN / "experiment3_submission_readiness_checklist.csv")
    key_count = len(pd.read_csv(FIG / "final_integrated_key_result_matrix.csv"))
    rows = build_rows(plan, readiness)
    write_reports(rows)
    upsert_outputs(rows, key_count)
    print("figure_table_assets", len(rows))
    print("key_result_rows_before_figure_narrative_upsert", key_count)
    print("wrote figure/table narrative chain")


if __name__ == "__main__":
    main()
