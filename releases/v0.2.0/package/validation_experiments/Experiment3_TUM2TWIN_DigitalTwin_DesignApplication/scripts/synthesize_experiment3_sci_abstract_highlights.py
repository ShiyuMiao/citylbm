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


def build_evidence_map(matrix: pd.DataFrame) -> list[dict[str, str]]:
    return [
        {
            "text_unit": "abstract_sentence_1",
            "claim": "Real digital-twin city data require a layer-separated route before wind simulation.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source_artifact": "reports/data_source_and_download_manifest.md; reports/model_result_object_consistency_audit.md",
            "safe_wording": "require layer-separated conversion",
            "blocked_wording": "photogrammetry/3DGS directly supplies CFD collision boundaries",
        },
        {
            "text_unit": "abstract_sentence_2",
            "claim": "Visual realism and CFD collision readiness are separable; GCRI distinguishes photogrammetry from closed collision geometry.",
            "evidence_type": "newly_run",
            "source_artifact": lookup(matrix, "Geometry-to-CFD readiness")["source_artifact"],
            "safe_wording": lookup(matrix, "Geometry-to-CFD readiness")["value"],
            "blocked_wording": "GCRI is an external universal standard",
        },
        {
            "text_unit": "abstract_sentence_3",
            "claim": "FluidX3D screening identifies pedestrian-layer low speed and upper-layer recovery.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": lookup(matrix, "S0 baseline pedestrian screening")["source_artifact"]
            + "; "
            + lookup(matrix, "FluidX3D numerical protocol transparency")["source_artifact"],
            "safe_wording": lookup(matrix, "S0 baseline pedestrian screening")["value"]
            + "; "
            + lookup(matrix, "Vertical recovery")["value"],
            "blocked_wording": "field-validated prediction or annual comfort compliance",
        },
        {
            "text_unit": "abstract_sentence_4",
            "claim": "Building-form effects follow a staged mechanism across near-facade saturation, local-context recovery and directional reactivity.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": lookup(matrix, "Building-form wind mechanism synthesis")["source_artifact"],
            "safe_wording": lookup(matrix, "Building-form wind mechanism synthesis")["value"],
            "blocked_wording": "universal morphology law",
        },
        {
            "text_unit": "abstract_sentence_5",
            "claim": "S1/S2 negative sensitivity shows that porosity alone is insufficient.",
            "evidence_type": "newly_run",
            "source_artifact": lookup(matrix, "S1 design sensitivity")["source_artifact"]
            + "; "
            + lookup(matrix, "S2 design sensitivity")["source_artifact"],
            "safe_wording": lookup(matrix, "S1 design sensitivity")["value"]
            + "; "
            + lookup(matrix, "S2 design sensitivity")["value"],
            "blocked_wording": "successful optimization",
        },
        {
            "text_unit": "abstract_sentence_6",
            "claim": "The study is a screening workflow with explicit boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": "reports/experiment3_final_sci_discussion_evidence_map.md; reports/claim_boundary.md",
            "safe_wording": "screening-level evidence with blocked validation/compliance/pollutant/GCBTE/CityLBM-GH claims retained",
            "blocked_wording": "deployment-ready regulatory evaluation",
        },
        {
            "text_unit": "highlight_1",
            "claim": "TUM2TWIN visual, semantic and collision layers are separated for wind simulation.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source_artifact": "reports/data_source_and_download_manifest.md; manifests/gcri_scoring_table.csv",
            "safe_wording": "layer-separated digital-twin-to-CFD workflow",
            "blocked_wording": "direct 3DGS collision boundary",
        },
        {
            "text_unit": "highlight_2",
            "claim": "The campus core is dominated by pedestrian-layer low-speed ventilation insufficiency.",
            "evidence_type": "newly_run",
            "source_artifact": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "safe_wording": "z~2 m mean VR / low-speed ratio = 0.076 / 0.934",
            "blocked_wording": "measured annual comfort class",
        },
        {
            "text_unit": "highlight_3",
            "claim": "Building-form response is best interpreted as staged local-context recovery and directional reactivity.",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/building_form_wind_mechanism_parameter_matrix.csv; figures/building_form_wind_mechanism_synthesis_panel.png",
            "safe_wording": "near-facade saturation; 20-50 m recovery; wind-sector response",
            "blocked_wording": "universal threshold",
        },
        {
            "text_unit": "highlight_4",
            "claim": "S1/S2 porosity interventions are negative sensitivity evidence.",
            "evidence_type": "newly_run",
            "source_artifact": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "safe_wording": "porosity alone is insufficient",
            "blocked_wording": "successful design optimization",
        },
    ]


def write_abstract_files() -> None:
    zh = """# Experiment 3 SCI 摘要、Highlights 与关键词

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题目

真实校园数字孪生数据到 CFD-ready 风环境筛查：TUM2TWIN、FluidX3D 与建筑形式机制解释

## 摘要

真实城市数字孪生数据为建筑风环境研究提供了高真实感三维场景，但视觉真实并不等同于 CFD 碰撞边界就绪。本文以 TUM2TWIN Downtown 校园核心区为对象，构建了从 photogrammetry/Rhino/3DGS-like 视觉审查层、LoD/OBJ/CAD-derived 语义几何层到 FluidX3D 碰撞边界层的应用转化流程。结果显示，photogrammetry visual STL 的 Geometry-to-CFD Readiness Index 为 0.455，而 core closed-prism collision 与 district prism collision 分别达到 0.925 和 0.918，说明数字孪生底层模型需要按可视化、语义和计算边界功能分层使用。基于 dx = 2 m、8 个风向和 3 个后 spin-up 样本的 FluidX3D 筛查结果表明，研究区 z~2 m 行人层 mean VR / 低速比例为 0.076 / 0.934，而 z~40 m 为 1.049 / 0.000，主要问题是行人层通风不足而非强风危险。建筑形式分析进一步揭示，0-20 m 近立面带处于低速饱和状态，20-50 m 局地上下文带才显露形态恢复差异；50 m 扇区围合度、平均高度和复合围合分数是主要抑制性描述符。S1/S2 设计敏感性结果显示，单纯增加 relief corridor 或 network porosity 未改善全局行人层风速，说明孔隙面积必须与有效来流扇区、动量入口和压力交换路径耦合。本文贡献在于提出并验证了一条真实数字孪生街区到 CFD-ready 风环境筛查的可审计路径，以及一种面向校园更新的建筑形式-风环境分阶段解释框架。当前结论属于 FluidX3D/数字孪生筛查证据，不构成实测验证、年度舒适安全合规或污染物扩散预测。

## Highlights

- 区分 TUM2TWIN 视觉模型、语义几何和 CFD 碰撞边界三类功能层。
- FluidX3D 筛查显示校园核心区主要问题是行人层低风速与通风不足。
- 建筑形式影响表现为近立面低速饱和、20-50 m 局地恢复和风向响应。
- S1/S2 负向设计敏感性说明，孔隙面积 alone 不足以恢复通风。

## 关键词

数字孪生；城市风环境；FluidX3D；TUM2TWIN；CFD-ready 几何；行人层通风；建筑形态参数；校园微气候

## 图文摘要说明

建议图文摘要采用三段式流程图：左侧为 TUM2TWIN photogrammetry/Rhino/LoD 数据分层，中间为 closed-prism collision geometry 与 FluidX3D 八风向筛查，右侧为行人层低速结果、20-50 m 建筑形式恢复机制和 S1/S2 负向设计证据。图文摘要应避免使用 “validated prediction” 或 “comfort compliance” 等字样，除非后续加入外部验证证据。
"""

    en = """# Experiment 3 SCI Abstract, Highlights and Keywords

evidence_type: newly_run + preexisting_artifact + blocked

## Suggested Title

From Real Campus Digital Twins to CFD-Ready Wind Screening: TUM2TWIN, FluidX3D and Building-Form Mechanism Interpretation

## Abstract

Real urban digital twins provide visually realistic three-dimensional scenes for architectural wind-environment research, but visual realism is not equivalent to CFD collision-boundary readiness. Using the TUM2TWIN Downtown campus core as a case, this study develops an application-transfer workflow from photogrammetry/Rhino/3DGS-like visual audit layers, through LoD/OBJ/CAD-derived semantic geometry, to FluidX3D collision boundaries. The photogrammetry visual STL obtains a Geometry-to-CFD Readiness Index of 0.455, whereas the core closed-prism and district-prism collision geometries reach 0.925 and 0.918, showing that digital-twin source models must be separated by visualization, semantic and computational-boundary functions. Under a dx = 2 m, eight-direction and three post-spin-up-sample FluidX3D screening protocol, the z~2 m pedestrian-layer mean velocity ratio / low-speed ratio is 0.076 / 0.934, whereas the z~40 m values are 1.049 / 0.000. The main wind-environment issue is therefore pedestrian-layer ventilation insufficiency rather than strong-wind hazard. Building-form analysis further shows that the 0-20 m facade-adjacent band is low-speed saturated, while the 20-50 m local-context band exposes morphology-dependent recovery. The strongest suppressive descriptors are 50 m sector enclosure, mean height and combined enclosure. S1/S2 sensitivity tests show that adding a relief corridor or network porosity does not improve the global pedestrian-layer speed field, indicating that porosity must be coupled with effective inflow sectors, momentum-entry paths and pressure exchange. The contribution is an auditable real-digital-twin-to-CFD wind-screening workflow and a staged building-form interpretation framework for campus renewal. The evidence remains FluidX3D/digital-twin screening evidence, not field validation, annual comfort/safety compliance or pollutant-dispersion prediction.

## Highlights

- TUM2TWIN visual, semantic and CFD collision-boundary layers are separated.
- FluidX3D screening identifies pedestrian-layer low-speed ventilation insufficiency.
- Building-form effects follow near-facade saturation, 20-50 m recovery and wind-sector response.
- S1/S2 negative sensitivity shows that porosity area alone is insufficient.

## Keywords

Digital twin; Urban wind environment; FluidX3D; TUM2TWIN; CFD-ready geometry; Pedestrian ventilation; Building morphology; Campus microclimate

## Graphical Abstract Caption

The graphical abstract should show a three-stage workflow: TUM2TWIN photogrammetry/Rhino/LoD data separation, closed-prism collision geometry and FluidX3D eight-direction screening, and the final interpretation layer combining pedestrian low-speed maps, 20-50 m building-form recovery and S1/S2 negative design evidence. Avoid the wording "validated prediction" or "comfort compliance" unless new external validation evidence is added.
"""

    write_text(PAPER / "experiment3_sci_abstract_highlights_keywords_zh.md", zh)
    write_text(PAPER / "experiment3_sci_abstract_highlights_keywords_en.md", en)


def write_audit(rows: list[dict[str, str]]) -> None:
    table = pd.DataFrame(rows).to_markdown(index=False)
    report = f"""# Experiment 3 SCI Abstract and Highlights Evidence Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This audit maps every abstract sentence and highlight to source artifacts and
blocked wording. It is intended to prevent the abstract from becoming stronger
than the verified Experiment 3 evidence.

## Sentence and Highlight Evidence Map

{table}

## Abstract Claim Boundary

The abstract may claim an auditable digital-twin-to-CFD wind-screening workflow,
pedestrian-layer low-speed screening, staged building-form interpretation and
negative porosity-sensitivity evidence. It must not claim field validation,
annual comfort/safety compliance, pollutant dispersion, GCBTE closure,
CityLBM-Grasshopper end-to-end execution or successful optimization.
"""
    write_text(REP / "experiment3_sci_abstract_highlights_audit.md", report)


def upsert_manifests(matrix: pd.DataFrame) -> None:
    evidence_rows = [
        {
            "claim": "SCI abstract, highlights, keywords and graphical-abstract caption were drafted with sentence-level evidence mapping.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_sci_abstract_highlights_keywords_zh.md; paper_text/experiment3_sci_abstract_highlights_keywords_en.md; manifests/experiment3_abstract_highlights_evidence_map.csv",
        },
        {
            "claim": "Abstract wording was audited to exclude field validation, annual comfort compliance, pollutant dispersion, GCBTE, CityLBM-GH and successful-optimization claims.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "reports/experiment3_sci_abstract_highlights_audit.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "SCI abstract and highlights readiness",
        "metric": "abstract evidence map / bilingual abstract-highlights-keywords / graphical abstract caption",
        "value": f"10 mapped abstract-highlight units / {len(matrix)} source key-result rows before abstract upsert",
        "source_artifact": "manifests/experiment3_abstract_highlights_evidence_map.csv; paper_text/experiment3_sci_abstract_highlights_keywords_en.md",
        "paper_safe_claim": "Experiment 3 has a claim-controlled abstract/highlights package for manuscript submission.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [key_row],
        "claim_layer",
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )

    if (DRAFT / "experiment3_claim_verification.csv").exists():
        rows = read_csv_rows(DRAFT / "experiment3_claim_verification.csv")
        fieldnames = list(rows[0].keys()) if rows else [
            "claim_layer",
            "evidence_type",
            "source",
            "value",
            "paper_safe_claim",
            "claim_readiness",
        ]
        row = {
            "claim_layer": "module_claim_ABSTRACT",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_abstract_highlights_evidence_map.csv; reports/experiment3_sci_abstract_highlights_audit.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Abstract and highlights are mapped to evidence and preserve blocked claim boundaries.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        rows = [item for item in rows if item.get("claim_layer") != "module_claim_ABSTRACT"]
        rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(DRAFT / "experiment3_claim_verification.csv", rows, fieldnames)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    rows = build_evidence_map(matrix)
    write_csv(
        MAN / "experiment3_abstract_highlights_evidence_map.csv",
        rows,
        ["text_unit", "claim", "evidence_type", "source_artifact", "safe_wording", "blocked_wording"],
    )
    write_abstract_files()
    write_audit(rows)
    upsert_manifests(matrix)
    print("abstract_highlight_units", len(rows))
    print("key_result_rows_before_abstract_upsert", len(matrix))
    print("wrote SCI abstract/highlights package")


if __name__ == "__main__":
    main()
