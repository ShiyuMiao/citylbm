#!/usr/bin/env python3
"""Audit whether Case E evidence and manuscript drafts stay within claim bounds."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PAPER_DRAFTS_DIR = ROOT / "academic-paper-writer" / "paper-drafts"

REQUIRED_ARTIFACTS = [
    "CityLBM/bin/CityLBM.gha",
    "docs/experiments/casee/results/release_gate.json",
    "docs/experiments/casee/results/casee_metrics.csv",
    "docs/experiments/casee/results/casee_validation_report.md",
    "docs/experiments/casee/results/casee_manuscript_claim_matrix.csv",
    "docs/experiments/casee/results/casee_paper_evidence_gate.json",
    "docs/experiments/casee/results/plugin_identity_gate.json",
    "docs/releases/v0.4.0-rc15.md",
]

FORBIDDEN_SUCCESS_PATTERNS = [
    "has passed AIJ Case E accuracy validation",
    "validated predictive accuracy",
    "research-grade predictive accuracy",
    "LES improvement",
    "mesh independence",
    "official z=2 m validation result",
    "精度验证通过",
    "科研级预测精度",
    "已通过 AIJ Case E",
    "网格无关性",
]

NEGATION_MARKERS = [
    "not ",
    "cannot ",
    "should not ",
    "does not ",
    "do not ",
    "rather than ",
    "不能",
    "不应",
    "不可",
    "未",
    "不得",
    "不能写",
    "不满足",
]

FORBIDDEN_SECTION_MARKERS = [
    "## Forbidden",
    "## 论文中不能写",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def metric_gate_status(gate: Dict[str, Any]) -> Dict[str, Any]:
    metrics = gate.get("metrics") or {}
    r2 = metrics.get("r2")
    mae = metrics.get("mae_pp")
    pearson = metrics.get("pearson")
    formal_allowed = bool(gate.get("formal_release_allowed", False))
    return {
        "formal_release_allowed": formal_allowed,
        "recommended_tag": gate.get("recommended_tag", ""),
        "official_z2m_r2": r2,
        "official_z2m_mae_pp": mae,
        "official_z2m_pearson": pearson,
        "formal_metric_is_negative_validation": bool(r2 is not None and float(r2) < 0.0),
    }


def claim_matrix_status(rows: List[Dict[str, str]], recommended_tag: str) -> Dict[str, Any]:
    readiness_counts: Dict[str, int] = {}
    for row in rows:
        readiness = row.get("claim_readiness", "unknown")
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1

    joined = "\n".join(" ".join(row.values()) for row in rows)
    overstated_paper_ready: List[str] = []
    for row in rows:
        readiness = row.get("claim_readiness", "")
        text = " ".join(row.values()).lower()
        if readiness == "paper_ready" and any(p.lower() in text for p in FORBIDDEN_SUCCESS_PATTERNS):
            overstated_paper_ready.append(row.get("claim_id", "unknown"))

    return {
        "claim_count": len(rows),
        "readiness_counts": readiness_counts,
        "blocked_release_claim_present": "Formal CityLBM v0.4.0 release is not allowed" in joined,
        "negative_validation_claim_present": "does not meet the release accuracy gate" in joined,
        "recommended_tag_present": recommended_tag in joined if recommended_tag else False,
        "no_overstated_paper_ready_claims": not overstated_paper_ready,
        "overstated_paper_ready_claim_ids": overstated_paper_ready,
    }


def in_forbidden_section(line: str, current_forbidden: bool) -> bool:
    stripped = line.strip()
    if stripped.startswith("## "):
        return any(stripped.startswith(marker) for marker in FORBIDDEN_SECTION_MARKERS)
    return current_forbidden


def line_is_negated(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in NEGATION_MARKERS)


def scan_draft(path: Path) -> Tuple[List[Dict[str, Any]], int]:
    violations: List[Dict[str, Any]] = []
    forbidden_section = False
    checked_lines = 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        forbidden_section = in_forbidden_section(line, forbidden_section)
        if not line.strip():
            continue
        checked_lines += 1
        lower = line.lower()
        for pattern in FORBIDDEN_SUCCESS_PATTERNS:
            if pattern.lower() not in lower:
                continue
            if forbidden_section or line_is_negated(line):
                continue
            violations.append(
                {
                    "path": display_path(path),
                    "line": lineno,
                    "pattern": pattern,
                    "text": line.strip(),
                }
            )
    return violations, checked_lines


def draft_status(paths: Iterable[Path]) -> Dict[str, Any]:
    all_violations: List[Dict[str, Any]] = []
    checked_files: List[str] = []
    checked_lines = 0
    for path in paths:
        if not path.exists():
            continue
        violations, n_lines = scan_draft(path)
        checked_files.append(display_path(path))
        checked_lines += n_lines
        all_violations.extend(violations)
    return {
        "checked_files": checked_files,
        "checked_nonblank_lines": checked_lines,
        "forbidden_success_claim_violations": all_violations,
        "draft_claim_boundary_passed": not all_violations and bool(checked_files),
    }


def artifact_index_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "artifact_index_found": False,
            "artifact_count": 0,
            "lightweight_release_asset_count": 0,
            "formal_accuracy_claim_supported": None,
            "required_artifacts_present": False,
            "missing_required_artifacts": REQUIRED_ARTIFACTS,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    artifacts = data.get("artifacts", [])
    paths = {str(row.get("path", "")) for row in artifacts}
    missing = [item for item in REQUIRED_ARTIFACTS if item not in paths]
    summary = data.get("summary", {})
    return {
        "artifact_index_found": True,
        "artifact_count": summary.get("artifact_count", len(artifacts)),
        "lightweight_release_asset_count": summary.get("lightweight_release_asset_count", 0),
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "required_artifacts_present": not missing,
        "missing_required_artifacts": missing,
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metric = payload["metric_gate"]
    claim = payload["claim_matrix"]
    draft = payload["draft_scan"]
    artifact = payload["artifact_index"]
    lines = [
        "# Case E Paper Evidence Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Paper evidence gate passed: {payload['paper_evidence_gate_passed']}",
        f"- Formal v0.4.0 release allowed: {metric['formal_release_allowed']}",
        f"- Recommended tag: `{metric['recommended_tag']}`",
        "",
        "## Official z=2 m Metric",
        "",
        f"- MAE: {metric['official_z2m_mae_pp']} pp",
        f"- R2: {metric['official_z2m_r2']}",
        f"- Pearson: {metric['official_z2m_pearson']}",
        f"- Negative validation status: {metric['formal_metric_is_negative_validation']}",
        "",
        "## Claim Matrix",
        "",
        f"- Claims: {claim['claim_count']}",
        f"- Readiness counts: `{claim['readiness_counts']}`",
        f"- Blocked release claim present: {claim['blocked_release_claim_present']}",
        f"- Negative validation claim present: {claim['negative_validation_claim_present']}",
        f"- Recommended tag present: {claim['recommended_tag_present']}",
        f"- No overstated paper-ready claims: {claim['no_overstated_paper_ready_claims']}",
        "",
        "## Draft Scan",
        "",
        f"- Checked files: {len(draft['checked_files'])}",
        f"- Checked nonblank lines: {draft['checked_nonblank_lines']}",
        f"- Draft claim boundary passed: {draft['draft_claim_boundary_passed']}",
        "",
        "## Artifact Index",
        "",
        f"- Artifact index found: {artifact['artifact_index_found']}",
        f"- Artifact count: {artifact['artifact_count']}",
        f"- Lightweight release assets: {artifact['lightweight_release_asset_count']}",
        f"- Required artifacts present: {artifact['required_artifacts_present']}",
        f"- Formal accuracy claim supported by index: {artifact['formal_accuracy_claim_supported']}",
    ]
    if artifact["missing_required_artifacts"]:
        lines += ["", "Missing required artifacts:"]
        for item in artifact["missing_required_artifacts"]:
            lines.append(f"- `{item}`")
    if draft["forbidden_success_claim_violations"]:
        lines += ["", "## Violations", ""]
        for item in draft["forbidden_success_claim_violations"]:
            lines.append(f"- `{item['path']}:{item['line']}` matched `{item['pattern']}`: {item['text']}")
    else:
        lines += ["", "No forbidden success-claim violations were found outside negated or forbidden-claim sections."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--claim-matrix", type=Path, default=RESULTS_DIR / "casee_manuscript_claim_matrix.csv")
    parser.add_argument("--artifact-index", type=Path, default=RESULTS_DIR / "casee_artifact_index.json")
    parser.add_argument("--draft-glob", default="casee_v04_*.md")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_paper_evidence_gate.json")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_paper_evidence_gate.md")
    args = parser.parse_args()

    gate = json.loads(args.release_gate.read_text(encoding="utf-8"))
    metric = metric_gate_status(gate)
    claim = claim_matrix_status(read_csv(args.claim_matrix), str(metric["recommended_tag"]))
    draft = draft_status(sorted(PAPER_DRAFTS_DIR.glob(args.draft_glob)))
    artifact = artifact_index_status(args.artifact_index)
    passed = (
        metric["formal_metric_is_negative_validation"]
        and claim["blocked_release_claim_present"]
        and claim["negative_validation_claim_present"]
        and claim["recommended_tag_present"]
        and claim["no_overstated_paper_ready_claims"]
        and draft["draft_claim_boundary_passed"]
        and artifact["artifact_index_found"]
        and artifact["required_artifacts_present"]
        and artifact["formal_accuracy_claim_supported"] is False
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_evidence_gate_passed": passed,
        "metric_gate": metric,
        "claim_matrix": claim,
        "draft_scan": draft,
        "artifact_index": artifact,
    }
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"paper_evidence_gate_passed": passed, "out_json": str(args.out_json)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
