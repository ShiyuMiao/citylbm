#!/usr/bin/env python3
"""Fail-closed audit for Rhino/Grasshopper loading the tracked CityLBM GHA."""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
MANUAL_MANIFEST = RESULTS_DIR / "rhino_gha_load_manifest.json"
OUT_JSON = RESULTS_DIR / "rhino_gha_load_gate.json"
OUT_MD = RESULTS_DIR / "rhino_gha_load_gate.md"

REQUIRED_MANIFEST_FIELDS = [
    "checked_at",
    "operator",
    "rhino_version",
    "grasshopper_version",
    "observed_plugin_version",
    "observed_gha_sha256",
    "evidence_artifacts",
]


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def resolve_evidence(path_value: str) -> Path:
    p = Path(path_value)
    return p if p.is_absolute() else ROOT / p


def manual_template(expected_version: str, expected_sha: str) -> Dict[str, Any]:
    return {
        "checked_at": "YYYY-MM-DDTHH:MM:SS+08:00",
        "operator": "name",
        "rhino_version": "Rhino 7/8 version string",
        "grasshopper_version": "Grasshopper version string",
        "observed_plugin_version": expected_version,
        "observed_assembly_version": "0.4.0.0",
        "observed_gha_sha256": expected_sha,
        "evidence_artifacts": [
            "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png",
            "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt",
        ],
        "notes": "Evidence must show the loaded CityLBM GHA path/version/hash from the Rhino/Grasshopper session.",
    }


def build_payload() -> Dict[str, Any]:
    plugin_gate = read_json(PLUGIN_IDENTITY_GATE)
    manifest = read_json(MANUAL_MANIFEST)
    expected_version = str(plugin_gate.get("plugin_public_version") or "")
    expected_sha = str(plugin_gate.get("tracked_gha_sha256") or sha256(TRACKED_GHA))

    missing_fields = [field for field in REQUIRED_MANIFEST_FIELDS if not manifest.get(field)]
    evidence_values = manifest.get("evidence_artifacts") if isinstance(manifest.get("evidence_artifacts"), list) else []
    evidence_paths = [resolve_evidence(str(item)) for item in evidence_values]
    missing_evidence = [rel(path) if path.is_absolute() and str(path).startswith(str(ROOT)) else str(path) for path in evidence_paths if not path.exists()]

    checks = {
        "plugin_identity_gate_passed": bool(plugin_gate.get("plugin_identity_gate_passed")),
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "manual_manifest_exists": MANUAL_MANIFEST.exists(),
        "manual_manifest_required_fields_present": not missing_fields,
        "observed_plugin_version_matches_expected": bool(expected_version)
        and manifest.get("observed_plugin_version") == expected_version,
        "observed_gha_sha256_matches_tracked": bool(expected_sha)
        and str(manifest.get("observed_gha_sha256", "")).lower() == expected_sha.lower(),
        "evidence_artifacts_listed": len(evidence_values) > 0,
        "evidence_artifacts_exist": len(evidence_values) > 0 and not missing_evidence,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "rhino_loaded_new_gha": passed,
        "claim_readiness": "paper_ready_software_load_identity" if passed else "blocked_manual_rhino_load",
        "expected_plugin_public_version": expected_version,
        "expected_tracked_gha_sha256": expected_sha,
        "tracked_gha_path": rel(TRACKED_GHA),
        "plugin_identity_gate_path": rel(PLUGIN_IDENTITY_GATE),
        "manual_manifest_path": rel(MANUAL_MANIFEST),
        "manual_manifest_present": MANUAL_MANIFEST.exists(),
        "missing_required_fields": missing_fields,
        "missing_evidence_artifacts": missing_evidence,
        "checks": checks,
        "manual_manifest_template": manual_template(expected_version, expected_sha),
        "boundary": (
            "This gate proves only Rhino/Grasshopper loaded the tracked CityLBM GHA identity. "
            "It is not CFD accuracy evidence and must not change official z=2 m metrics."
        ),
    }


def write_markdown(payload: Dict[str, Any]) -> None:
    lines: List[str] = [
        "# Rhino/GHA Load Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Rhino loaded new GHA: {payload['rhino_loaded_new_gha']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Expected plugin version: `{payload['expected_plugin_public_version']}`",
        f"- Expected GHA SHA256: `{payload['expected_tracked_gha_sha256']}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    if payload["missing_required_fields"]:
        lines += ["", "Missing manifest fields:"]
        for item in payload["missing_required_fields"]:
            lines.append(f"- `{item}`")
    if payload["missing_evidence_artifacts"]:
        lines += ["", "Missing evidence artifacts:"]
        for item in payload["missing_evidence_artifacts"]:
            lines.append(f"- `{item}`")
    lines += [
        "",
        "## Required Manual Manifest",
        "",
        f"`{payload['manual_manifest_path']}` must be created from a real Rhino/Grasshopper session before this gate can pass:",
        "",
        "```json",
        json.dumps(payload["manual_manifest_template"], indent=2),
        "```",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(json.dumps({"rhino_loaded_new_gha": payload["rhino_loaded_new_gha"], "out_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
