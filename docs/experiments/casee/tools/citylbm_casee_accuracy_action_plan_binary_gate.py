#!/usr/bin/env python3
"""Audit that the packaged CityLBM GHA contains the Case E Accuracy Action Plan component."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
RELEASE_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha"
SOURCE_GATE = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_component_gate.json"
OUT_JSON = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_binary_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_binary_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_binary_gate.md"


REQUIRED_MARKERS = [
    "CaseEAccuracyActionPlanComponent",
    "Case E Accuracy Action Plan",
    "MAE Gap pp",
    "R2 Gap",
    "Next Actions",
    "default_setting_allowed: false",
    "predictive accuracy",
    "mesh independence",
    "LES improvement",
    "formal v0.4.0",
    "post-hoc affine",
    "A001",
    "A004",
    "A005",
    "A006",
    "A008",
    "862C4BA3-B4EC-4E33-88CA-0F7345708B68",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def binary_contains(data: bytes, marker: str) -> bool:
    return marker.encode("utf-8") in data or marker.encode("utf-16le") in data


def build_payload() -> Dict[str, Any]:
    source_gate = read_json(SOURCE_GATE)
    data = TRACKED_GHA.read_bytes() if TRACKED_GHA.exists() else b""
    tracked_sha = sha256(TRACKED_GHA)
    release_sha = sha256(RELEASE_GHA)
    marker_checks = {marker: binary_contains(data, marker) for marker in REQUIRED_MARKERS}
    checks = {
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "release_gha_exists": RELEASE_GHA.exists(),
        "tracked_gha_matches_release_gha": bool(tracked_sha) and tracked_sha == release_sha,
        "source_component_gate_passed": source_gate.get("casee_accuracy_action_plan_component_gate_passed") is True,
        "all_required_markers_present_in_tracked_gha": all(marker_checks.values()),
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_packaged_casee_accuracy_action_plan_component" if passed else "blocked_packaged_casee_accuracy_action_plan_component",
        "casee_accuracy_action_plan_binary_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "tracked_gha_path": rel(TRACKED_GHA),
        "release_gha_path": rel(RELEASE_GHA),
        "tracked_gha_sha256": tracked_sha,
        "release_gha_sha256": release_sha,
        "tracked_gha_size_bytes": TRACKED_GHA.stat().st_size if TRACKED_GHA.exists() else None,
        "required_markers": marker_checks,
        "checks": checks,
        "boundary": (
            "This gate checks that the packaged GHA contains the Case E accuracy action-plan component strings. "
            "It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, "
            "improve official z=2 m metrics, or permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["kind", "name", "passed"])
        writer.writeheader()
        for key, value in payload["checks"].items():
            writer.writerow({"kind": "gate_check", "name": key, "passed": value})
        for key, value in payload["required_markers"].items():
            writer.writerow({"kind": "binary_marker", "name": key, "passed": value})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Case E Accuracy Action Plan Binary Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['casee_accuracy_action_plan_binary_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Default setting allowed: {payload['default_setting_allowed']}",
        f"- Tracked GHA: `{payload['tracked_gha_path']}`",
        f"- Tracked GHA SHA256: `{payload['tracked_gha_sha256']}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Required Binary Markers",
        "",
        "| marker | present |",
        "|---|---:|",
    ]
    for key, value in payload["required_markers"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload)
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "casee_accuracy_action_plan_binary_gate_passed": payload["casee_accuracy_action_plan_binary_gate_passed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["casee_accuracy_action_plan_binary_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
