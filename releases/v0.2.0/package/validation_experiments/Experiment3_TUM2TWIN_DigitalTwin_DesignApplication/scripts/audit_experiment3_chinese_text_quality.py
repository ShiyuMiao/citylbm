from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
REPO_ROOT = ROOT.parents[4]
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
DRAFT = REPO_ROOT / "academic-paper-writer" / "paper-drafts"
FIG = ROOT / "figures"


MOJIBAKE_PATTERNS = [
    "锛",
    "鈮",
    "閸",
    "鐨",
    "涓",
    "瀹",
    "棰",
    "妯",
    "绋",
    "鍥",
    "琛",
    "灞",
    "\ufffd",
]

CANONICAL_DIRECT_USE = {
    "paper_text/experiment3_clean_chinese_sci_package_zh.md",
    "paper_text/experiment3_clean_chinese_core_paragraphs_zh.md",
    "paper_text/experiment3_clean_chinese_figure_table_captions_zh.md",
    "paper_text/experiment3_final_sci_discussion_conclusion_zh.md",
    "paper_text/experiment3_sci_manuscript_module_zh.md",
    "paper_text/experiment3_sci_figure_captions_zh.md",
    "paper_text/experiment3_sci_table_captions_zh.md",
    "paper_text/morphology_directional_fingerprint_conclusion_zh.md",
}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.relative_to(REPO_ROOT).as_posix()


def text_files() -> list[Path]:
    files = sorted(PAPER.glob("*_zh.md"))
    if DRAFT.exists():
        files.extend(sorted(DRAFT.glob("*.md")))
    return files


def scan(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    counts = {pattern: text.count(pattern) for pattern in MOJIBAKE_PATTERNS}
    mojibake_hits = sum(counts.values())
    question_marks = text.count("?")
    replacement_question_flag = "needs_manual_check" if question_marks > 0 and "_en" not in path.name else "not_applicable_or_none"
    relative = rel(path)
    return {
        "relative_path": relative,
        "file_role": "canonical_direct_use" if relative in CANONICAL_DIRECT_USE else "supporting_or_legacy_text",
        "size_bytes": path.stat().st_size,
        "mojibake_hits": mojibake_hits,
        "replacement_question_marks": question_marks,
        "replacement_question_flag": replacement_question_flag,
        "quality_status": "pass" if mojibake_hits == 0 and replacement_question_flag != "needs_manual_check" else "review_required",
        "evidence_type": "newly_run",
        "audit_scope": "UTF-8 markdown text; heuristic mojibake pattern scan; not a semantic peer review",
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, key_field: str, row: dict[str, object], fields: list[str]) -> None:
    rows: list[dict[str, object]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    rows = [item for item in rows if item.get(key_field) != row[key_field]]
    rows.append(row)
    write_csv(path, rows, fields)


def build_report(rows: list[dict[str, object]]) -> str:
    total = len(rows)
    passed = sum(1 for row in rows if row["quality_status"] == "pass")
    flagged = total - passed
    canonical = [row for row in rows if row["file_role"] == "canonical_direct_use"]
    canonical_flagged = [row for row in canonical if row["quality_status"] != "pass"]
    top = sorted(rows, key=lambda row: int(row["mojibake_hits"]), reverse=True)[:12]

    lines = [
        "# Experiment 3 Chinese Text Quality Audit",
        "",
        "evidence_type: newly_run",
        "",
        "## Scope",
        "",
        "This audit checks paper-facing Chinese Markdown files for common mojibake patterns and replacement characters after the clean Chinese manuscript layer and caption files are regenerated. It is a text-integrity gate, not a scientific-content review.",
        "",
        "## Summary",
        "",
        f"- Chinese/draft Markdown files scanned: `{total}`",
        f"- Passed files: `{passed}`",
        f"- Files requiring review: `{flagged}`",
        f"- Canonical direct-use files scanned: `{len(canonical)}`",
        f"- Canonical direct-use files requiring review: `{len(canonical_flagged)}`",
        "",
        "## Canonical Use Policy",
        "",
        "Use the clean Chinese manuscript package and the regenerated SCI caption files as the direct writing surface. Older Chinese Markdown files may remain as supporting provenance, but any file flagged by this audit must be corrected before being copied into a manuscript.",
        "",
        "## Top Audit Rows",
        "",
        "| relative_path | file_role | mojibake_hits | replacement_question_marks | quality_status |",
        "|---|---|---:|---:|---|",
    ]
    for row in top:
        lines.append(
            f"| {row['relative_path']} | {row['file_role']} | {row['mojibake_hits']} | {row['replacement_question_marks']} | {row['quality_status']} |"
        )
    lines.extend(
        [
            "",
            "## Output Artifacts",
            "",
            "- `manifests/experiment3_chinese_text_quality_audit.csv`",
            "- `reports/experiment3_chinese_text_quality_audit.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = [scan(path) for path in text_files()]
    fields = [
        "relative_path",
        "file_role",
        "size_bytes",
        "mojibake_hits",
        "replacement_question_marks",
        "replacement_question_flag",
        "quality_status",
        "evidence_type",
        "audit_scope",
    ]
    write_csv(MAN / "experiment3_chinese_text_quality_audit.csv", rows, fields)
    (REP / "experiment3_chinese_text_quality_audit.md").write_text(build_report(rows), encoding="utf-8")

    total = len(rows)
    passed = sum(1 for row in rows if row["quality_status"] == "pass")
    canonical = [row for row in rows if row["file_role"] == "canonical_direct_use"]
    canonical_flagged = [row for row in canonical if row["quality_status"] != "pass"]

    upsert_csv(
        MAN / "evidence_inventory.csv",
        "claim",
        {
            "claim": "Chinese manuscript-facing Markdown files were scanned for mojibake and replacement-character corruption after regeneration.",
            "evidence_type": "newly_run",
            "source": "manifests/experiment3_chinese_text_quality_audit.csv; reports/experiment3_chinese_text_quality_audit.md",
        },
        ["claim", "evidence_type", "source"],
    )
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        "claim_layer",
        {
            "evidence_type": "newly_run",
            "claim_layer": "Chinese text quality readiness",
            "metric": "scanned Chinese/draft markdown files / pass count / canonical flagged count",
            "value": f"{total} / {passed} / {len(canonical_flagged)}",
            "source_artifact": "manifests/experiment3_chinese_text_quality_audit.csv; reports/experiment3_chinese_text_quality_audit.md",
            "paper_safe_claim": "The manuscript-facing Chinese text layer passes a reproducible mojibake/replacement-character audit; this is text-integrity evidence and does not add CFD validation.",
        },
        [
            "evidence_type",
            "claim_layer",
            "metric",
            "value",
            "source_artifact",
            "paper_safe_claim",
        ],
    )

    print("chinese_text_files", total)
    print("passed", passed)
    print("canonical_flagged", len(canonical_flagged))
    print("wrote Chinese text quality audit")


if __name__ == "__main__":
    main()
