#!/usr/bin/env python3
"""Audit that the packaged CityLBM GHA contains the Plugin Identity component."""

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
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
SOURCE_GATE = RESULTS_DIR / "citylbm_plugin_identity_component_gate.json"
OUT_JSON = RESULTS_DIR / "citylbm_plugin_identity_binary_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_plugin_identity_binary_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_plugin_identity_binary_gate.md"


REQUIRED_ASCII_MARKERS = [
    "PluginIdentityComponent",
    "Plugin Identity",
    "GHA SHA256",
    "Manifest Template",
    "CityLBM Plugin Identity",
    "observed_gha_sha256",
    "not CFD accuracy evidence",
    "7B5126DD-4C5F-4C27-8E4C-142792314E55",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def binary_contains(data: bytes, marker: str) -> bool:
    ascii_marker = marker.encode("utf-8")
    utf16_marker = marker.encode("utf-16le")
    return ascii_marker in data or utf16_marker in data


def build_payload() -> Dict[str, Any]:
    plugin_gate = read_json(PLUGIN_IDENTITY_GATE)
    source_gate = read_json(SOURCE_GATE)
    data = TRACKED_GHA.read_bytes() if TRACKED_GHA.exists() else b""
    tracked_sha = sha256(TRACKED_GHA)
    release_sha = sha256(RELEASE_GHA)
    marker_checks = {marker: binary_contains(data, marker) for marker in REQUIRED_ASCII_MARKERS}
    checks = {
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "release_gha_exists": RELEASE_GHA.exists(),
        "tracked_gha_matches_release_gha": bool(tracked_sha) and tracked_sha == release_sha,
        "tracked_gha_matches_plugin_identity_gate": bool(tracked_sha)
        and tracked_sha == str(plugin_gate.get("tracked_gha_sha256", "")),
        "source_component_gate_passed": source_gate.get("plugin_identity_component_gate_passed") is True,
        "all_required_markers_present_in_tracked_gha": all(marker_checks.values()),
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_packaged_gha_identity_component" if passed else "blocked_packaged_gha_identity_component",
        "plugin_identity_binary_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "tracked_gha_path": rel(TRACKED_GHA),
        "release_gha_path": rel(RELEASE_GHA),
        "tracked_gha_sha256": tracked_sha,
        "release_gha_sha256": release_sha,
        "tracked_gha_size_bytes": TRACKED_GHA.stat().st_size if TRACKED_GHA.exists() else None,
        "required_markers": marker_checks,
        "checks": checks,
        "boundary": (
            "This gate checks that the packaged GHA contains the Plugin Identity component strings. "
            "It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, "
            "or improve official Case E z=2 m metrics."
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
        "# CityLBM Plugin Identity Binary Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['plugin_identity_binary_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
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
    print(json.dumps({"plugin_identity_binary_gate_passed": payload["plugin_identity_binary_gate_passed"], "out_json": str(OUT_JSON)}, indent=2))
    return 0 if payload["plugin_identity_binary_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
