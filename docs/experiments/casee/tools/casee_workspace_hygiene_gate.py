#!/usr/bin/env python3
"""Fail closed if local Case E artifacts could be mistaken for release evidence."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
OUT_JSON = RESULTS_DIR / "casee_workspace_hygiene_gate.json"
OUT_CSV = RESULTS_DIR / "casee_workspace_hygiene_gate.csv"
OUT_MD = RESULTS_DIR / "casee_workspace_hygiene_gate.md"

ALLOWED_UNTRACKED_PREFIXES = (
    ".workbuddy/",
    "CityLBM/NuGet/",
    "CityLBM/bin/Release/",
    "CityLBM/obj/",
    "NuGet/",
    "docs/experiments/casee/native_cases/",
    "docs/experiments/casee/results/",
    "tools/",
)

ALLOWED_UNTRACKED_RESULT_PATTERNS = (
    ".log",
    ".err.log",
    "casee_c006_",
)

EXPECTED_UNTRACKED_EVIDENCE = {
    "docs/experiments/casee/tools/casee_workspace_hygiene_gate.py",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.json",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.csv",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.md",
    "docs/experiments/casee/tools/casee_postrun_official_audit_handoff.py",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.json",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.md",
    "CityLBM/src/Components/Results/CaseEAccuracyActionPlanComponent.cs",
    "docs/experiments/casee/tools/citylbm_casee_accuracy_action_plan_component_gate.py",
    "docs/experiments/casee/tools/citylbm_casee_accuracy_action_plan_binary_gate.py",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.json",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.md",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.json",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.md",
    "CityLBM/src/Components/Results/CaseEPaperClaimCardComponent.cs",
    "docs/experiments/casee/tools/citylbm_casee_paper_claim_card_component_gate.py",
    "docs/experiments/casee/tools/citylbm_casee_paper_claim_card_binary_gate.py",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.json",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.md",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.json",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.md",
    "CityLBM/src/Components/Results/CaseERemediationPlanComponent.cs",
    "docs/experiments/casee/tools/citylbm_casee_remediation_plan_component_gate.py",
    "docs/experiments/casee/tools/citylbm_casee_remediation_plan_binary_gate.py",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_component_gate.json",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_component_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_component_gate.md",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_binary_gate.json",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_binary_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_remediation_plan_binary_gate.md",
    "CityLBM/src/Components/Results/CaseEOfficialMetricGateComponent.cs",
    "docs/experiments/casee/tools/citylbm_casee_official_metric_gate_component_gate.py",
    "docs/experiments/casee/tools/citylbm_casee_official_metric_gate_binary_gate.py",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_component_gate.json",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_component_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_component_gate.md",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_binary_gate.json",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_binary_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_official_metric_gate_binary_gate.md",
    "docs/releases/v0.4.0-rc76.md",
    "docs/releases/v0.4.0-rc77.md",
    "docs/releases/v0.4.0-rc78.md",
    "docs/releases/v0.4.0-rc89.md",
    "docs/releases/v0.4.0-rc90.md",
    "docs/releases/v0.4.0-rc91.md",
    "docs/releases/v0.4.0-rc92.md",
}

FORBIDDEN_TRACKED_SUFFIXES = (".vtk", ".vtu", ".vti", ".vtp", ".stl", ".3dm")
FORBIDDEN_TRACKED_PARTS = (
    "/bin/Release/",
    "/obj/",
    "/NuGet/",
)

TRACKED_HEAVY_SCOPE_PREFIXES = (
    "CityLBM/bin/Release/",
    "CityLBM/obj/",
    "CityLBM/NuGet/",
    "NuGet/",
    "docs/experiments/casee/native_cases/",
    "docs/experiments/casee/results/",
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_git(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        encoding="utf-8",
        errors="replace",
    )


def status_rows() -> List[Dict[str, Any]]:
    proc = run_git(["status", "--short", "--ignored"])
    rows: List[Dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].replace("\\", "/")
        rows.append(
            {
                "status_code": code,
                "path": path,
                "classification": classify_status(code, path),
                "release_risk": release_risk(code, path),
            }
        )
    return rows


def classify_status(code: str, path: str) -> str:
    if code == "!!":
        return "ignored_local_artifact"
    if code == "??":
        if path in EXPECTED_UNTRACKED_EVIDENCE:
            return "expected_untracked_evidence_pending_commit"
        if any(path.startswith(prefix) for prefix in ALLOWED_UNTRACKED_PREFIXES):
            if path.startswith("docs/experiments/casee/results/"):
                name = Path(path).name
                if any(name.endswith(item) or name.startswith(item) for item in ALLOWED_UNTRACKED_RESULT_PATTERNS):
                    return "allowed_untracked_local_artifact"
                return "unexpected_untracked_casee_result"
            return "allowed_untracked_local_artifact"
        return "unexpected_untracked_file"
    return "tracked_or_staged_change"


def release_risk(code: str, path: str) -> str:
    lower = path.lower()
    if code == "??":
        return "manual_review_required"
    if lower.endswith(FORBIDDEN_TRACKED_SUFFIXES):
        if lower.endswith("citylbm/bin/citylbm.gha"):
            return "allowed_compiled_plugin"
        return "forbidden_tracked_heavy_or_raw"
    if any(part.lower() in lower for part in FORBIDDEN_TRACKED_PARTS):
        return "forbidden_tracked_build_cache"
    return "controlled"


def tracked_forbidden_rows() -> List[Dict[str, Any]]:
    proc = run_git(["ls-files"])
    rows: List[Dict[str, Any]] = []
    for path in proc.stdout.splitlines():
        if not any(path.startswith(prefix) for prefix in TRACKED_HEAVY_SCOPE_PREFIXES):
            continue
        lower = path.lower()
        if lower.endswith("citylbm/bin/citylbm.gha"):
            continue
        if lower.endswith(FORBIDDEN_TRACKED_SUFFIXES) or any(part.lower() in lower for part in FORBIDDEN_TRACKED_PARTS):
            rows.append(
                {
                    "status_code": "tracked",
                    "path": path,
                    "classification": "tracked_forbidden_artifact",
                    "release_risk": release_risk("tracked", path),
                }
            )
    return rows


def write_csv(rows: List[Dict[str, Any]]) -> None:
    fields = ["status_code", "path", "classification", "release_risk"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_md(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# Case E Workspace Hygiene Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['workspace_hygiene_gate_passed']}",
        f"- Ignored local artifacts: {summary['ignored_local_artifact_count']}",
        f"- Allowed untracked local artifacts: {summary['allowed_untracked_local_artifact_count']}",
        f"- Unexpected untracked files: {summary['unexpected_untracked_count']}",
        f"- Tracked forbidden artifacts: {summary['tracked_forbidden_count']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        "",
        "## Non-Controlled Rows",
        "",
        "| status | path | classification | risk |",
        "|---|---|---|---|",
    ]
    for row in rows:
        if row["classification"] in {"ignored_local_artifact", "tracked_or_staged_change"}:
            continue
        lines.append(f"| `{row['status_code']}` | `{row['path']}` | `{row['classification']}` | `{row['release_risk']}` |")
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = status_rows() + tracked_forbidden_rows()
    unexpected = [row for row in rows if row["classification"].startswith("unexpected")]
    tracked_forbidden = [row for row in rows if row["classification"] == "tracked_forbidden_artifact"]
    passed = not unexpected and not tracked_forbidden
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "workspace_hygiene_gate_passed": passed,
        "ignored_local_artifact_count": sum(1 for row in rows if row["classification"] == "ignored_local_artifact"),
        "allowed_untracked_local_artifact_count": sum(1 for row in rows if row["classification"] == "allowed_untracked_local_artifact"),
        "expected_untracked_evidence_pending_commit_count": sum(1 for row in rows if row["classification"] == "expected_untracked_evidence_pending_commit"),
        "unexpected_untracked_count": len(unexpected),
        "tracked_forbidden_count": len(tracked_forbidden),
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "claim_readiness": "paper_ready_workspace_hygiene; not CFD accuracy evidence" if passed else "blocked_workspace_hygiene",
        "boundary": (
            "This gate audits workspace hygiene for Case E release evidence. It records ignored local caches, "
            "logs, native candidate CSVs, and visualization scratch files so they cannot be mistaken for "
            "paper-ready official results. It does not delete files, run CFD, improve metrics, or permit formal v0.4.0."
        ),
    }
    payload = {"summary": summary, "rows": rows}
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(rows)
    write_md(payload, rows)
    print(json.dumps({"workspace_hygiene_gate_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
