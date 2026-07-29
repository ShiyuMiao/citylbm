from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
MAN = ROOT / "manifests"
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    rows = pd.read_csv(path).to_dict("records")
    additions = [
        {
            "claim": "Reviewer-facing reproducibility and claim-risk audit was generated from the current Experiment 3 matrix, figure/table readiness checklist and requirement coverage table.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "reports/experiment3_reviewer_reproducibility_and_claim_audit.md; manifests/experiment3_reviewer_claim_risk_matrix.csv",
        },
        {
            "claim": "Reviewer-response paragraphs were drafted to separate paper-ready screening claims from blocked validation, compliance and CityLBM-GH claims.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_reviewer_response_paragraphs_en.md; paper_text/experiment3_reviewer_response_paragraphs_zh.md",
        },
    ]
    for item in additions:
        matched = False
        for row in rows:
            if row["claim"] == item["claim"]:
                row.update(item)
                matched = True
                break
        if not matched:
            rows.append(item)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def classify_claim(row: pd.Series) -> tuple[str, str, str]:
    evidence_type = str(row.get("evidence_type", ""))
    claim_layer = str(row.get("claim_layer", ""))
    safe = str(row.get("paper_safe_claim", ""))
    blocked_words = ["field", "annual", "compliance", "pollutant", "CityLBM", "GCBTE", "universal", "causal"]
    if "blocked" in evidence_type:
        readiness = "paper_ready_with_boundary"
        risk = "medium"
    else:
        readiness = "paper_ready_as_screening"
        risk = "low"
    if any(word.lower() in (claim_layer + " " + safe).lower() for word in blocked_words):
        risk = "medium"
    reviewer_question = {
        "S0 baseline pedestrian screening": "Is the main wind problem strong wind or insufficient pedestrian ventilation?",
        "Vertical recovery": "Does upper-layer recovery justify omitting pedestrian-height assessment?",
        "Climate-proxy sensitivity": "Is the Open-Meteo layer a measured wind rose or only a proxy sensitivity test?",
        "S1 design sensitivity": "Do the design openings improve the pedestrian wind field?",
        "S2 design sensitivity": "Does stronger porosity solve the low-speed condition?",
        "Directional local trade-off": "Are design effects global or only local and directional?",
        "Morphology robustness": "Can morphology variables be used as a predictive surrogate?",
        "Morphology threshold design rule": "Are the threshold rules universal design criteria?",
        "Geometry-to-CFD readiness": "Why not use photogrammetry/3DGS-like mesh directly as the collision boundary?",
        "Effect-size uncertainty": "Are the numerical patterns stable across archived directions/samples?",
        "Directional anisotropy": "Is the result controlled by one exceptional inflow direction?",
        "Building-form response archetypes": "Do morphology groups support design interpretation beyond single variables?",
        "Morphology stage transition": "Where does the building-form signal become visible?",
        "Morphology directional fingerprint": "Does useful recovery require wind-sector response as well as mean VR recovery?",
        "FluidX3D numerical protocol transparency": "Are the boundary conditions, viscosity, Reynolds descriptors, sampling and convergence limits recorded?",
        "Building-form wind mechanism synthesis": "What is the architectural mechanism linking building form and the wind-environment pattern?",
        "Final SCI discussion synthesis": "Can each final discussion paragraph be traced to evidence and blocked wording?",
        "SCI abstract and highlights readiness": "Does the abstract remain no stronger than the verified discussion evidence?",
        "Research-question synthesis readiness": "Do the research-question answers convert evidence into claims without expanding beyond the archive?",
        "Limitations and validation roadmap readiness": "Does the limitations section define evidence needed for stronger claims without implying those claims are completed?",
        "Figure-table narrative readiness": "Does each figure or table support only the manuscript claim it is allowed to support?",
        "Submission statements readiness": "Do the data, code and reproducibility statements distinguish archived files, external assets and blocked claims?",
    }.get(claim_layer, "What evidence supports this claim and where is the boundary?")
    required_wording = (
        "Frame as screening-level FluidX3D/digital-twin evidence; keep source artifact and blocked boundary visible."
        if readiness.endswith("boundary")
        else "Frame as a completed screening result under the archived FluidX3D protocol."
    )
    return readiness, risk, reviewer_question + " " + required_wording


def build_risk_matrix(matrix: pd.DataFrame, requirements: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in matrix.iterrows():
        readiness, risk, reviewer_note = classify_claim(row)
        rows.append(
            {
                "item_type": "claim_layer",
                "item": row["claim_layer"],
                "evidence_type": row["evidence_type"],
                "source_artifact": row["source_artifact"],
                "claim_readiness": readiness,
                "reviewer_risk": risk,
                "reviewer_question_or_response": reviewer_note,
            }
        )
    for _, row in requirements.iterrows():
        if str(row.get("status")) != "blocked":
            continue
        rows.append(
            {
                "item_type": "blocked_requirement",
                "item": row["requirement"],
                "evidence_type": row["evidence_type"],
                "source_artifact": row["evidence_artifact"],
                "claim_readiness": "blocked_do_not_claim",
                "reviewer_risk": "high_if_overclaimed",
                "reviewer_question_or_response": row["paper_safe_interpretation"],
            }
        )
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_No rows._"
    return df[cols].to_markdown(index=False)


def main() -> None:
    for folder in [MAN, REP, PAPER]:
        folder.mkdir(parents=True, exist_ok=True)

    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    readiness = pd.read_csv(MAN / "experiment3_submission_readiness_checklist.csv")
    requirements = pd.read_csv(MAN / "experiment3_final_requirement_coverage.csv")
    evidence = pd.read_csv(MAN / "evidence_inventory.csv")
    risk = build_risk_matrix(matrix, requirements)
    risk_path = MAN / "experiment3_reviewer_claim_risk_matrix.csv"
    risk.to_csv(risk_path, index=False, encoding="utf-8", lineterminator="\n")

    ready_count = int((readiness["submission_status"] == "ready_for_manual_review").sum())
    blocked = risk[risk["claim_readiness"] == "blocked_do_not_claim"]
    bounded = risk[risk["claim_readiness"] == "paper_ready_with_boundary"]

    report = f"""# Experiment 3 Reviewer Reproducibility and Claim-Risk Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This reviewer-facing audit turns the Experiment 3 archive into an explicit
claim-control layer. It is intended for paper revision, reviewer response, and
manual pre-submission checks. It does not add CFD results; it verifies that
each paper-facing claim has an evidence type, source artifact and boundary.

## Reproducibility Anchor

- Canonical rebuild command from the release package root: `& .\\scripts\\rebuild_experiment3_paper_assets.ps1`
- Key result matrix rows: `{len(matrix)}`
- Reviewer-facing figure/table assets: `{len(readiness)}`
- Ready-for-manual-review assets: `{ready_count}`
- Evidence inventory rows before this audit upsert: `{len(evidence)}`
- GitHub archive manifest refresh: performed at the end of `rebuild_experiment3_paper_assets.ps1`

## Paper-Ready Claim Layers

{md_table(risk[risk["item_type"] == "claim_layer"], ["item", "evidence_type", "claim_readiness", "reviewer_risk", "reviewer_question_or_response"])}

## Blocked Claims That Must Not Be Overstated

{md_table(blocked, ["item", "evidence_type", "claim_readiness", "reviewer_risk", "reviewer_question_or_response"])}

## Claims Requiring Boundary Language

{md_table(bounded, ["item", "evidence_type", "source_artifact", "reviewer_question_or_response"])}

## Reviewer-Safe Summary

The archive is internally reproducible for a FluidX3D-native digital-twin wind
screening experiment with CityLBM-compatible geometry preparation. Its strongest
claims are data-layer separation, geometry-to-CFD readiness, eight-direction
pedestrian low-speed screening, upper-layer recovery, morphology-based local
context interpretation, negative S1/S2 design sensitivity and wind-sector
directional fingerprints. Claims about field validation, annual comfort or
safety compliance, pollutant dispersion, GCBTE closure and CityLBM-Grasshopper
end-to-end execution remain blocked.
"""
    write_text(REP / "experiment3_reviewer_reproducibility_and_claim_audit.md", report)

    en = """# Reviewer-Ready Response Paragraphs for Experiment 3

evidence_type: newly_run + preexisting_artifact + blocked

If a reviewer asks whether Experiment 3 validates FluidX3D or CityLBM accuracy, the safe response is that Cases A and E provide the preceding benchmark layer, whereas Experiment 3 evaluates real digital-twin application transfer. The completed evidence concerns TUM2TWIN data-layer separation, CFD-ready collision-geometry preparation, FluidX3D-native eight-direction screening, ParaView/manual visual audit assets and morphology-based interpretation. The archive does not claim field-measured accuracy, wind-tunnel closure or CityLBM-Grasshopper end-to-end execution.

If a reviewer asks whether the wind-environment conclusion is a comfort-code result, the safe response is no. The reported metrics are velocity-ratio screening metrics under an archived FluidX3D protocol. Open-Meteo 2024 is used only as a proxy directional weighting layer. Formal Lawson/NEN/AIJ annual comfort or safety classification would require calibrated wind climate, threshold exceedance probabilities and additional validation evidence.

If a reviewer asks what is new beyond traditional canyon/enclosure knowledge, the safe response is that the digital-twin workflow localizes the traditional insight inside a real campus block and separates three morphology-response layers. The 0-20 m facade-adjacent band is nearly saturated by sheltering; the 20-50 m local-context band exposes mean recovery; and the directional-fingerprint addendum shows whether local recovery is coupled to wind-sector response. This moves the design interpretation from single morphology variables or LCZ labels toward relative vertical massing, plan continuity, local enclosure, momentum-exchange paths and wind-sector reactivity.

If a reviewer asks why S1/S2 matter despite being negative, the safe response is that they are design-sensitivity tests rather than optimized proposals. Their near-null or negative global pedestrian-layer results show that added porosity alone is insufficient when not aligned with effective inflow sectors and pressure-exchange paths. This negative evidence narrows the design hypothesis for future interventions.
"""
    zh = """# 实验3审稿回应备用段落

evidence_type: newly_run + preexisting_artifact + blocked

如果审稿人质疑实验3是否在验证 FluidX3D 或 CityLBM 精度，安全回应是：AIJ Case A 和 Case E 承担前序基准/验证层，实验3的目标是检验真实数字孪生数据如何转化为可模拟、可审查、可解释的风环境应用流程。当前完成的证据包括 TUM2TWIN 数据层分离、CFD-ready 碰撞几何准备、FluidX3D-native 八风向筛查、ParaView/人工视觉审查资产和建筑形态解释；不宣称现场实测验证、风洞闭环或 CityLBM-Grasshopper 端到端执行。

如果审稿人质疑是否已经完成舒适度规范评价，安全回应是否定的。本文报告的是归档 FluidX3D 协议下的风速比筛查指标，Open-Meteo 2024 仅作为方向权重代理层。正式 Lawson/NEN/AIJ 年度舒适或安全分类还需要校准风气候、阈值超越概率和额外验证证据。

如果审稿人质疑相对传统街谷/围合研究的新意，安全回应是：本实验把传统认识定位到真实校园数字孪生街区中，并区分了三个形态响应层。0-20 m 近立面带几乎被遮蔽饱和，20-50 m 局地环境带揭示平均恢复，而方向性指纹进一步判断局地恢复是否与来流扇区响应耦合。由此，设计解释从单一形态变量或 LCZ 标签转向相对竖向体量、平面连续性、局地围合、动量交换路径和风向扇区响应。

如果审稿人质疑 S1/S2 负结果的意义，安全回应是：S1/S2 是设计敏感性测试，不是优化方案。其全局行人层近零或负向结果说明，单纯增加孔隙面积不足以恢复通风；孔隙必须与有效来流扇区、动量入口和压力交换路径耦合。这个负结果帮助收窄后续设计干预假设。
"""
    write_text(PAPER / "experiment3_reviewer_response_paragraphs_en.md", en)
    write_text(PAPER / "experiment3_reviewer_response_paragraphs_zh.md", zh)

    upsert_evidence_inventory()

    print("reviewer_claim_rows", len(risk))
    print("blocked_rows", len(blocked))
    print("bounded_rows", len(bounded))
    print("wrote reviewer reproducibility pack")


if __name__ == "__main__":
    main()
