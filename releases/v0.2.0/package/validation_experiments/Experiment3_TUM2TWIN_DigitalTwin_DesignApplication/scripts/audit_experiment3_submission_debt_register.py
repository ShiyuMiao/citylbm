from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path.cwd()
REPO = ROOT.parents[4]
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
FIG = ROOT / "figures"
DRAFT = REPO / "academic-paper-writer" / "paper-drafts"

FIELDS = [
    "debt_id",
    "debt_type",
    "status",
    "detected_phrase",
    "affected_claim",
    "source_files",
    "required_evidence_to_close",
    "current_safe_action",
    "paper_safe_wording",
    "risk_if_ignored",
]

KEY_FIELDS = [
    "evidence_type",
    "claim_layer",
    "metric",
    "value",
    "source_artifact",
    "paper_safe_claim",
]

PLACEHOLDERS = [
    "AUTHOR_INPUT_NEEDED",
    "RESULT_NEEDED",
    "REF_NEEDED",
    "FIGURE_NEEDED",
    "TABLE_NEEDED",
    "METHOD_DETAIL_NEEDED",
    "RESULT_UNVERIFIED",
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


def scan_placeholder_sources() -> dict[str, list[str]]:
    hits: dict[str, list[str]] = defaultdict(list)
    for folder in [DRAFT, PAPER]:
        for path in folder.glob("*.md"):
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            rel = path.relative_to(REPO).as_posix()
            for placeholder in PLACEHOLDERS:
                if placeholder in text:
                    hits[placeholder].append(rel)
    return {key: sorted(set(value)) for key, value in hits.items()}


def make_rows(hits: dict[str, list[str]]) -> list[dict[str, object]]:
    author_sources = "; ".join(hits.get("AUTHOR_INPUT_NEEDED", [])) or "academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md"
    result_sources = "; ".join(hits.get("RESULT_NEEDED", [])) or "academic-paper-writer/paper-drafts/paper_draft.md; academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md"
    ref_sources = "; ".join(hits.get("REF_NEEDED", []))
    figure_sources = "; ".join(hits.get("FIGURE_NEEDED", []) + hits.get("TABLE_NEEDED", []))

    rows = [
        {
            "debt_id": "SDR1",
            "debt_type": "author_input_needed",
            "status": "open_author_input",
            "detected_phrase": "AUTHOR_INPUT_NEEDED",
            "affected_claim": "Target journal, final reference style, final title emphasis and author-administrative statements.",
            "source_files": author_sources,
            "required_evidence_to_close": "Author decision on target journal, citation format, paper title wording, funding, competing interests, acknowledgements, CRediT roles and final license wording.",
            "current_safe_action": "Keep as author-input placeholders; do not invent venue requirements or administrative statements.",
            "paper_safe_wording": "The Experiment 3 section is journal-neutral and ready for integration after target-journal and author-administrative fields are fixed.",
            "risk_if_ignored": "Invented venue style or author declarations would create submission-integrity risk.",
        },
        {
            "debt_id": "SDR2",
            "debt_type": "blocked_external_validation",
            "status": "blocked",
            "detected_phrase": "RESULT_NEEDED: onsite or wind-tunnel validation",
            "affected_claim": "Field-validated predictive accuracy and measured wind-environment validation.",
            "source_files": result_sources,
            "required_evidence_to_close": "On-site wind measurements or wind-tunnel data with documented sensor/scale setup, matched boundary conditions, comparison metrics and uncertainty.",
            "current_safe_action": "State as missing validation; keep current results as FluidX3D-native screening and morphology interpretation.",
            "paper_safe_wording": "The study does not claim field-validated prediction accuracy.",
            "risk_if_ignored": "Screening-level CFD could be overstated as validated prediction.",
        },
        {
            "debt_id": "SDR3",
            "debt_type": "blocked_external_validation",
            "status": "blocked",
            "detected_phrase": "RESULT_NEEDED: annual comfort/safety exceedance",
            "affected_claim": "Lawson, NEN 8100 or AIJ annual comfort/safety compliance.",
            "source_files": result_sources,
            "required_evidence_to_close": "Calibrated measured or official wind rose, velocity-threshold exceedance calculation, activity-class thresholds and documented aggregation period.",
            "current_safe_action": "Use VR, stagnation and climate-proxy sensitivity only; do not label areas as compliant/non-compliant.",
            "paper_safe_wording": "Open-Meteo is used only as a climate-proxy sensitivity layer, not annual comfort compliance.",
            "risk_if_ignored": "Proxy wind weighting could be mistaken for formal comfort/safety assessment.",
        },
        {
            "debt_id": "SDR4",
            "debt_type": "blocked_missing_simulation",
            "status": "blocked",
            "detected_phrase": "RESULT_NEEDED: pollutant scalar transport",
            "affected_claim": "Pollutant concentration, exposure, scalar hot spots and C/C0 predictions.",
            "source_files": result_sources,
            "required_evidence_to_close": "FluidX3D or equivalent scalar-transport setup, source terms, boundary conditions, timestep/sample records and postprocessed C/C0 fields.",
            "current_safe_action": "Keep pollutant metrics as templates only.",
            "paper_safe_wording": "Pollutant dispersion is defined as a future metric but not reported as a result.",
            "risk_if_ignored": "The manuscript would fabricate concentration or exposure evidence.",
        },
        {
            "debt_id": "SDR5",
            "debt_type": "conditional_method_claim",
            "status": "open_conditional",
            "detected_phrase": "RESULT_NEEDED: CityLBM-Grasshopper end-to-end",
            "affected_claim": "CityLBM-Grasshopper plugin end-to-end execution.",
            "source_files": result_sources,
            "required_evidence_to_close": "Grasshopper file, CityLBM plugin run screenshot/log, input/output artifacts and generated wind/geometry output trace.",
            "current_safe_action": "Frame the current experiment as FluidX3D-native simulation with a CityLBM-compatible geometry package.",
            "paper_safe_wording": "The CityLBM-Grasshopper package remains an interoperability template unless new GH execution evidence is added.",
            "risk_if_ignored": "The method title could overclaim a workflow that was not executed end to end.",
        },
        {
            "debt_id": "SDR6",
            "debt_type": "blocked_missing_metric",
            "status": "blocked",
            "detected_phrase": "GCBTE not computed",
            "affected_claim": "3DGS-to-collision-boundary transfer error.",
            "source_files": "manifests/gcbte_status_table.csv; reports/design_scenario_and_unfinished_metric_boundary.md",
            "required_evidence_to_close": "Independent 3DGS-derived collision extraction, CityGML/LoD2/LoD3 ground truth, IoU/Chamfer/Hausdorff/roof-wall error computation and solid-mask agreement.",
            "current_safe_action": "Keep GCBTE as a proposed metric and future validation path.",
            "paper_safe_wording": "GCBTE is defined but not computed in the current archive.",
            "risk_if_ignored": "A proposed metric could be misread as an executed quantitative result.",
        },
        {
            "debt_id": "SDR7",
            "debt_type": "citation_and_figure_hygiene",
            "status": "closed_or_not_detected" if not ref_sources and not figure_sources else "open_review",
            "detected_phrase": "REF_NEEDED / FIGURE_NEEDED / TABLE_NEEDED",
            "affected_claim": "Unresolved citation, figure or table placeholders in paper-facing Markdown.",
            "source_files": "; ".join(item for item in [ref_sources, figure_sources] if item) or "none detected in scanned paper-facing Markdown",
            "required_evidence_to_close": "Verified references or figure/table source artifacts if new placeholders are introduced.",
            "current_safe_action": "Current scan found no REF_NEEDED, FIGURE_NEEDED or TABLE_NEEDED placeholders in the scanned paper-facing Markdown.",
            "paper_safe_wording": "No additional citation/figure placeholder debt is detected by this register; literature claims still rely on existing verified-reference maps.",
            "risk_if_ignored": "New placeholders could be carried into the manuscript if this audit is not rerun after edits.",
        },
    ]
    return rows


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def write_outputs(rows: list[dict[str, object]], hits: dict[str, list[str]]) -> None:
    write_csv(MAN / "experiment3_submission_debt_register.csv", rows, FIELDS)

    status_counts = Counter(str(row["status"]) for row in rows)
    type_counts = Counter(str(row["debt_type"]) for row in rows)
    placeholder_counts = {placeholder: len(files) for placeholder, files in hits.items()}
    report = f"""# Experiment 3 Submission Debt Register

evidence_type: newly_run + preexisting_artifact + blocked

This register scans the paper-facing Markdown layer for explicit placeholders and consolidates the remaining claim-upgrade debts. It does not add CFD results; it prevents unresolved author-input or external-validation requirements from being accidentally written as completed evidence.

## Summary

- Debt rows: `{len(rows)}`
- Status counts: `{dict(status_counts)}`
- Debt-type counts: `{dict(type_counts)}`
- Placeholder source counts: `{placeholder_counts}`

## Register

{md_table(rows, ["debt_id", "debt_type", "status", "affected_claim", "required_evidence_to_close", "current_safe_action"])}

## Paper-Safe Closeout

Experiment 3 is ready for a journal-neutral SCI section when it is framed as FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation. The remaining open items are not packaging failures. They are either author-input fields or claim-upgrade evidence that would be required only if the manuscript wants to claim field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE, CityLBM-Grasshopper end-to-end execution or successful optimization.
"""
    (REP / "experiment3_submission_debt_register.md").write_text(report, encoding="utf-8")

    note = """# 实验3投稿债务关闭说明

evidence_type: newly_run + preexisting_artifact + blocked

本轮审计把论文草稿中的 AUTHOR_INPUT_NEEDED 与 RESULT_NEEDED 占位符整理为投稿债务登记表。当前可以关闭的不是实测验证或法规评价，而是“哪些内容不能写成已完成结果”的边界问题：目标期刊、引用格式、题名措辞、基金与作者贡献等属于作者输入；实测或风洞验证、年度舒适安全超越概率、污染物扩散、GCBTE 与 CityLBM-Grasshopper 端到端执行属于外部证据或后续实验。

因此，实验3当前最稳妥的论文定位仍是：真实数字孪生城市数据到 CFD-ready 几何的转化、FluidX3D-native 风环境筛查、ParaView/统计复核、建筑形态解释和 S1/S2 负向设计敏感性。若论文题名或方法强调 CityLBM-Grasshopper 全链路、正式舒适安全合规或污染物暴露预测，则必须先补充相应证据，不能仅靠当前归档支撑。
"""
    (PAPER / "experiment3_submission_debt_closure_note_zh.md").write_text(note, encoding="utf-8")

    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Submission debt register",
            "metric": "submission debt rows / author-input rows / blocked claim-upgrade rows / citation-figure placeholder status",
            "value": f"{len(rows)} / {status_counts.get('open_author_input', 0)} / {status_counts.get('blocked', 0)} / {status_counts.get('closed_or_not_detected', 0)}",
            "source_artifact": "manifests/experiment3_submission_debt_register.csv; reports/experiment3_submission_debt_register.md; paper_text/experiment3_submission_debt_closure_note_zh.md",
            "paper_safe_claim": "The remaining Experiment 3 debts are author-input or claim-upgrade requirements; no unresolved citation, figure or table placeholder is detected in the scanned paper-facing Markdown.",
        },
        KEY_FIELDS,
        "claim_layer",
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        {
            "claim": "Experiment 3 submission debt register classifies author-input and claim-upgrade placeholders and preserves blocked evidence boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_submission_debt_register.csv; reports/experiment3_submission_debt_register.md; paper_text/experiment3_submission_debt_closure_note_zh.md",
        },
        ["claim", "evidence_type", "source"],
        "claim",
    )


def main() -> None:
    hits = scan_placeholder_sources()
    rows = make_rows(hits)
    write_outputs(rows, hits)
    print("submission_debt_rows", len(rows))
    print("placeholder_types_detected", sorted(hits.keys()))


if __name__ == "__main__":
    main()
