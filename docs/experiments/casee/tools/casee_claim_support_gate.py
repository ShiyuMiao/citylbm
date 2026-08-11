#!/usr/bin/env python3
"""Gate manuscript claim support for Case E without upgrading accuracy claims."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"

CLAIM_MATRIX = RESULTS_DIR / "casee_manuscript_claim_matrix.csv"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
SOLVER_LEDGER = RESULTS_DIR / "casee_solver_run_provenance_ledger.json"

OUT_JSON = RESULTS_DIR / "casee_claim_support_gate.json"
OUT_CSV = RESULTS_DIR / "casee_claim_support_gate.csv"
OUT_MD = RESULTS_DIR / "casee_claim_support_gate.md"

FIELDNAMES = [
    "claim_id",
    "support_class",
    "claim_readiness",
    "section",
    "evidence_type",
    "source_paths_exist",
    "claim_supported_for_paper",
    "formal_accuracy_claim_supported",
    "paper_use",
    "limitations",
]

FORMAL_PROTOCOL_IDS = {"C001"}
FORMAL_NEGATIVE_IDS = {"C002"}
DIAGNOSTIC_LIMITATION_IDS = {"C003", "C004", "C005", "C009", "C010", "C011", "C012", "C013", "C014"}
REPRODUCIBILITY_IDS = {"C006", "C007"}
FORMAL_RELEASE_BLOCK_IDS = {"C008"}
REQUIRED_IDS = FORMAL_PROTOCOL_IDS | FORMAL_NEGATIVE_IDS | DIAGNOSTIC_LIMITATION_IDS | REPRODUCIBILITY_IDS | FORMAL_RELEASE_BLOCK_IDS

FORBIDDEN_SUCCESS_PATTERNS = [
    "predictive accuracy",
    "mesh independence",
    "LES improvement",
    "formal v0.4.0 readiness",
    "validated default model",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def split_paths(value: str) -> List[str]:
    return [item.strip().replace("\\", "/") for item in value.split(";") if item.strip()]


def path_exists(path_text: str) -> bool:
    path = Path(path_text)
    if path.is_absolute():
        return path.exists()
    return (ROOT / path_text).exists()


def all_source_paths_exist(row: Dict[str, str]) -> bool:
    paths = split_paths(row.get("source_paths", ""))
    return bool(paths) and all(path_exists(path) for path in paths)


def classify_claim(row: Dict[str, str]) -> Tuple[str, bool, bool, str, str]:
    claim_id = row.get("claim_id", "")
    readiness = row.get("claim_readiness", "")
    forbidden_use = row.get("forbidden_use", "")
    allowed_use = row.get("allowed_use", "")

    if claim_id in FORMAL_PROTOCOL_IDS:
        return (
            "paper_methods_protocol",
            readiness == "paper_ready",
            False,
            allowed_use,
            "Protocol setup does not imply accuracy success.",
        )
    if claim_id in FORMAL_NEGATIVE_IDS:
        return (
            "paper_results_negative_validation",
            readiness == "limitations_ready",
            False,
            allowed_use,
            forbidden_use,
        )
    if claim_id in DIAGNOSTIC_LIMITATION_IDS:
        return (
            "limitations_only_diagnostic",
            readiness in {"limitations_ready", "weaken_claim"},
            False,
            allowed_use,
            forbidden_use,
        )
    if claim_id in REPRODUCIBILITY_IDS:
        return (
            "paper_reproducibility_context",
            readiness in {"paper_ready", "weaken_claim"},
            False,
            allowed_use,
            forbidden_use,
        )
    if claim_id in FORMAL_RELEASE_BLOCK_IDS:
        return (
            "blocked_formal_release",
            readiness == "blocked",
            False,
            allowed_use,
            forbidden_use,
        )
    return (
        "unclassified",
        False,
        False,
        "Do not use until the claim is classified.",
        "Missing claim-support classification.",
    )


def forbidden_patterns_are_blocked(rows: Iterable[Dict[str, str]]) -> Tuple[bool, List[Dict[str, str]]]:
    violations: List[Dict[str, str]] = []
    for row in rows:
        text = " ".join(
            [
                row.get("claim", ""),
                row.get("allowed_use", ""),
                row.get("forbidden_use", ""),
                row.get("protocol_risks", ""),
            ]
        )
        lower = text.lower()
        if not any(pattern.lower() in lower for pattern in FORBIDDEN_SUCCESS_PATTERNS):
            continue
        readiness = row.get("claim_readiness", "")
        forbidden_use = row.get("forbidden_use", "").lower()
        if readiness in {"blocked", "limitations_ready", "weaken_claim"} and any(
            marker in forbidden_use
            for marker in ["do not", "cannot", "not claim", "not describe", "not use"]
        ):
            continue
        violations.append(
            {
                "claim_id": row.get("claim_id", ""),
                "claim_readiness": readiness,
                "matched_text": text,
            }
        )
    return not violations, violations


def build_rows(claim_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in claim_rows:
        support_class, supported, formal_supported, paper_use, limitations = classify_claim(row)
        out.append(
            {
                "claim_id": row.get("claim_id", ""),
                "support_class": support_class,
                "claim_readiness": row.get("claim_readiness", ""),
                "section": row.get("section", ""),
                "evidence_type": row.get("evidence_type", ""),
                "source_paths_exist": all_source_paths_exist(row),
                "claim_supported_for_paper": supported,
                "formal_accuracy_claim_supported": formal_supported,
                "paper_use": paper_use,
                "limitations": limitations,
            }
        )
    return out


def summarize(rows: List[Dict[str, Any]], claim_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    release_gate = read_json(RELEASE_GATE)
    ledger = read_json(SOLVER_LEDGER)
    found_ids = {str(row["claim_id"]) for row in rows}
    class_counts: Dict[str, int] = {}
    for row in rows:
        key = str(row["support_class"])
        class_counts[key] = class_counts.get(key, 0) + 1

    forbidden_ok, forbidden_violations = forbidden_patterns_are_blocked(claim_rows)
    metrics = release_gate.get("metrics") or {}
    official_r2 = metrics.get("r2")
    official_r2_negative = official_r2 is not None and float(official_r2) < 0.0
    all_paths_exist = all(bool(row["source_paths_exist"]) for row in rows)
    no_formal_accuracy_claims = not any(bool(row["formal_accuracy_claim_supported"]) for row in rows)
    no_unclassified = not any(row["support_class"] == "unclassified" for row in rows)
    required_ids_present = REQUIRED_IDS.issubset(found_ids)

    gate_passed = (
        required_ids_present
        and all_paths_exist
        and no_unclassified
        and no_formal_accuracy_claims
        and forbidden_ok
        and release_gate.get("formal_release_allowed") is False
        and official_r2_negative
        and ledger.get("ledger_passed") is True
        and ledger.get("formal_accuracy_claim_supported") is False
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_support_gate_passed": gate_passed,
        "evidence_type": "newly_run",
        "claim_count": len(rows),
        "support_class_counts": class_counts,
        "required_ids_present": required_ids_present,
        "missing_required_ids": sorted(REQUIRED_IDS - found_ids),
        "all_source_paths_exist": all_paths_exist,
        "no_unclassified_claims": no_unclassified,
        "no_formal_accuracy_claims": no_formal_accuracy_claims,
        "forbidden_success_patterns_blocked": forbidden_ok,
        "forbidden_success_pattern_violations": forbidden_violations,
        "official_r2": official_r2,
        "official_r2_negative": official_r2_negative,
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "recommended_tag": release_gate.get("recommended_tag"),
        "ledger_passed": ledger.get("ledger_passed"),
        "claim_readiness": "paper_ready_claim_support_gate; blocked formal accuracy release",
        "boundary": (
            "This gate supports manuscript claim triage only. It does not add CFD output, "
            "improve official z=2 m metrics, or permit a formal v0.4.0 release."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in FIELDNAMES})


def write_markdown(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines = [
        "# Case E Claim Support Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['claim_support_gate_passed']}",
        f"- Formal release allowed: {summary['formal_release_allowed']}",
        f"- Recommended tag: `{summary['recommended_tag']}`",
        f"- Official R2: {summary['official_r2']}",
        f"- No formal accuracy claims: {summary['no_formal_accuracy_claims']}",
        f"- Forbidden success patterns blocked: {summary['forbidden_success_patterns_blocked']}",
        "",
        "## Support Classes",
        "",
    ]
    for key in sorted(summary["support_class_counts"]):
        lines.append(f"- {key}: {summary['support_class_counts'][key]}")
    lines += [
        "",
        "## Claim Triage",
        "",
        "| claim | class | readiness | supported | formal accuracy? | limitations |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['claim_id']}` | {row['support_class']} | {row['claim_readiness']} | "
            f"{row['claim_supported_for_paper']} | {row['formal_accuracy_claim_supported']} | {row['limitations']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    claim_rows = read_csv(CLAIM_MATRIX)
    rows = build_rows(claim_rows)
    summary = summarize(rows, claim_rows)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": [
            rel(CLAIM_MATRIX),
            rel(RELEASE_GATE),
            rel(SOLVER_LEDGER),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"claim_support_gate_passed": summary["claim_support_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["claim_support_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
