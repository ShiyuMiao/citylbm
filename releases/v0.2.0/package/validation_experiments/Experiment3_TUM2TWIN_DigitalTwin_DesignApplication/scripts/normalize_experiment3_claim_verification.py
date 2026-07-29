from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
REPO_ROOT = ROOT.parents[4]
DRAFT = REPO_ROOT / "academic-paper-writer" / "paper-drafts"
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"


FIELDNAMES = [
    "claim_or_asset",
    "evidence_type",
    "source",
    "value_or_status",
    "paper_use",
    "verification_status",
]


SOURCE_RULES = [
    (
        "fluidx3d_numerical_protocol",
        "module_claim_NUMERICAL_PROTOCOL",
        "paper_ready_with_boundary",
        "FluidX3D numerical parameters are archived for screening-level reproduction; residual convergence, field validation and annual compliance are not claimed.",
    ),
    (
        "building_form_wind_mechanism",
        "module_claim_BUILDING_FORM_MECHANISM",
        "paper_ready_with_boundary",
        "Building-form effects are framed as a staged screening mechanism across near-facade sheltering, local-context recovery and wind-sector reactivity.",
    ),
    (
        "experiment3_final_discussion",
        "module_claim_FINAL_DISCUSSION",
        "paper_ready_with_boundary",
        "Final discussion and conclusion paragraphs are mapped to evidence and retain blocked claim boundaries.",
    ),
    (
        "experiment3_abstract_highlights",
        "module_claim_ABSTRACT",
        "paper_ready_with_boundary",
        "Abstract and highlights are mapped to evidence and preserve blocked claim boundaries.",
    ),
    (
        "experiment3_research_question",
        "module_claim_RQ_SYNTHESIS",
        "paper_ready_with_boundary",
        "Research-question answers are evidence-mapped and keep blocked claims visible.",
    ),
    (
        "experiment3_limitations_future_validation",
        "module_claim_LIMITATIONS_ROADMAP",
        "paper_ready_with_boundary",
        "Limitations and validation roadmap preserve blocked claims and define evidence needed for claim upgrades.",
    ),
    (
        "experiment3_figure_table_narrative",
        "module_claim_FIGURE_TABLE_NARRATIVE",
        "paper_ready_with_boundary",
        "Figure/table narrative order is evidence-mapped and preserves claim boundaries.",
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def map_blank_row(row: dict[str, str]) -> tuple[str, str, str] | None:
    source = row.get("source", "")
    lowered = source.lower()
    for needle, claim_id, status, paper_use in SOURCE_RULES:
        if needle in lowered:
            return claim_id, status, paper_use
    return None


def normalize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    normalized: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        item = {field: row.get(field, "") for field in FIELDNAMES}
        old_name = item["claim_or_asset"]
        status = "unchanged"
        if not item["claim_or_asset"].strip():
            mapped = map_blank_row(item)
            if mapped is None:
                item["claim_or_asset"] = f"module_claim_UNMAPPED_ROW_{index}"
                item["value_or_status"] = item["value_or_status"] or "author_review_needed"
                item["paper_use"] = item["paper_use"] or "AUTHOR_INPUT_NEEDED: review unmapped claim-verification row."
                item["verification_status"] = item["verification_status"] or "author_review_needed"
                status = "mapped_to_review_needed"
            else:
                claim_id, value_status, paper_use = mapped
                item["claim_or_asset"] = claim_id
                item["value_or_status"] = item["value_or_status"] or value_status
                item["paper_use"] = item["paper_use"] or paper_use
                item["verification_status"] = item["verification_status"] or value_status
                status = "blank_name_normalized"
        if item["claim_or_asset"] in seen:
            status = "duplicate_removed"
            audit.append(
                {
                    "row_index": str(index),
                    "old_claim_or_asset": old_name,
                    "new_claim_or_asset": item["claim_or_asset"],
                    "source": item["source"],
                    "status": status,
                }
            )
            continue
        seen.add(item["claim_or_asset"])
        normalized.append(item)
        audit.append(
            {
                "row_index": str(index),
                "old_claim_or_asset": old_name,
                "new_claim_or_asset": item["claim_or_asset"],
                "source": item["source"],
                "status": status,
            }
        )
    return normalized, audit


def upsert_csv(path: Path, key_field: str, item: dict[str, str], fieldnames: list[str]) -> None:
    rows = read_csv(path) if path.exists() else []
    updated = False
    for row in rows:
        if row.get(key_field) == item[key_field]:
            row.update(item)
            updated = True
            break
    if not updated:
        rows.append(item)
    write_csv(path, rows, fieldnames)


def update_integrated_evidence(normalized_count: int, fixed_count: int) -> None:
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        "claim_layer",
        {
            "evidence_type": "newly_run + preexisting_artifact",
            "claim_layer": "Claim-verification hygiene",
            "metric": "claim verification rows / blank claim rows after normalization",
            "value": f"{normalized_count} rows / 0 blank claim_or_asset rows / {fixed_count} rows normalized",
            "source_artifact": "academic-paper-writer/paper-drafts/experiment3_claim_verification.csv; manifests/experiment3_claim_verification_hygiene.csv",
            "paper_safe_claim": "The Experiment 3 claim-verification table has named claim or asset identifiers for every row, so reviewer-facing evidence checks no longer contain blank claim entries.",
        },
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        "claim",
        {
            "claim": "Experiment 3 claim-verification table was normalized so every reviewer-facing row has a named claim or asset identifier.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source": "academic-paper-writer/paper-drafts/experiment3_claim_verification.csv; manifests/experiment3_claim_verification_hygiene.csv; reports/experiment3_claim_verification_hygiene.md",
        },
        ["claim", "evidence_type", "source"],
    )


def write_report(audit: list[dict[str, str]], normalized_count: int, fixed_count: int) -> None:
    lines = [
        "# Experiment 3 Claim-Verification Hygiene Audit",
        "",
        "evidence_type: newly_run + preexisting_artifact",
        "",
        "## Summary",
        "",
        f"- Claim-verification rows after normalization: `{normalized_count}`",
        "- Blank `claim_or_asset` rows after normalization: `0`",
        f"- Rows normalized from blank claim names: `{fixed_count}`",
        "",
        "## Interpretation",
        "",
        "This audit does not add CFD results. It removes a table-hygiene problem in the paper-facing claim inventory by assigning stable module-level identifiers to synthesis rows that previously had evidence sources but no `claim_or_asset` name.",
        "",
        "## Audit Rows",
        "",
        "| row_index | old_claim_or_asset | new_claim_or_asset | status | source |",
        "|---|---|---|---|---|",
    ]
    for row in audit:
        lines.append(
            f"| {row['row_index']} | {row['old_claim_or_asset']} | {row['new_claim_or_asset']} | {row['status']} | {row['source']} |"
        )
    write_text(REP / "experiment3_claim_verification_hygiene.md", "\n".join(lines) + "\n")


def main() -> None:
    claim_path = DRAFT / "experiment3_claim_verification.csv"
    rows = read_csv(claim_path)
    normalized, audit = normalize_rows(rows)
    blank_after = [row for row in normalized if not row.get("claim_or_asset", "").strip()]
    if blank_after:
        raise RuntimeError(f"blank claim_or_asset rows remain: {len(blank_after)}")
    fixed_count = sum(1 for row in audit if row["status"] == "blank_name_normalized")
    write_csv(claim_path, normalized, FIELDNAMES)
    write_csv(
        MAN / "experiment3_claim_verification_hygiene.csv",
        audit,
        ["row_index", "old_claim_or_asset", "new_claim_or_asset", "source", "status"],
    )
    write_report(audit, len(normalized), fixed_count)
    update_integrated_evidence(len(normalized), fixed_count)
    print("claim_verification_rows", len(normalized))
    print("blank_claim_rows", 0)
    print("normalized_blank_rows", fixed_count)
    print("wrote manifests/experiment3_claim_verification_hygiene.csv")
    print("wrote reports/experiment3_claim_verification_hygiene.md")


if __name__ == "__main__":
    main()
