#!/usr/bin/env python3
"""Prepare fail-closed Rhino/Grasshopper load evidence collection for CityLBM."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
RHINO_LOAD_GATE = RESULTS_DIR / "rhino_gha_load_gate.json"
GHA_INSTALL_AUDIT = RESULTS_DIR / "citylbm_gha_install_audit.json"
OUT_JSON = RESULTS_DIR / "casee_rhino_load_evidence_kit.json"
OUT_CSV = RESULTS_DIR / "casee_rhino_load_evidence_kit.csv"
OUT_MD = RESULTS_DIR / "casee_rhino_load_evidence_kit.md"
OUT_TEMPLATE = RESULTS_DIR / "rhino_gha_load_manifest.template.json"


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
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def file_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": str(path), "sha256": "", "size_bytes": None, "mtime_utc": ""}
    return {
        "found": True,
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def rhino_candidates() -> List[Path]:
    raw = [
        Path(r"C:\Program Files\Rhino 8\System\Rhino.exe"),
        Path(r"C:\Program Files\Rhino 7\System\Rhino.exe"),
        Path(r"C:\Program Files\Rhino 6\System\Rhino.exe"),
        Path(r"C:\Program Files\McNeel\Rhino 8\System\Rhino.exe"),
        Path(r"C:\Program Files\McNeel\Rhino 7\System\Rhino.exe"),
    ]
    seen: set[str] = set()
    out: List[Path] = []
    for path in raw:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def grasshopper_library_dirs() -> List[Path]:
    appdata = Path(os.environ.get("APPDATA", ""))
    localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
    userprofile = Path(os.environ.get("USERPROFILE", ""))
    raw = [
        appdata / "Grasshopper" / "Libraries",
        appdata / "McNeel" / "Rhinoceros" / "8.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        appdata / "McNeel" / "Rhinoceros" / "7.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        localappdata / "McNeel" / "Rhinoceros" / "8.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        userprofile / "AppData" / "Roaming" / "Grasshopper" / "Libraries",
    ]
    seen: set[str] = set()
    out: List[Path] = []
    for path in raw:
        if not str(path):
            continue
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def staged_gha_rows(expected_sha: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for directory in grasshopper_library_dirs():
        if not directory.exists():
            rows.append(
                {
                    "kind": "grasshopper_library",
                    "path": str(directory),
                    "found": False,
                    "sha256": "",
                    "matches_expected": False,
                    "note": "library directory missing",
                }
            )
            continue
        files = sorted(directory.glob("CityLBM*.gha"))
        if not files:
            rows.append(
                {
                    "kind": "grasshopper_library",
                    "path": str(directory),
                    "found": True,
                    "sha256": "",
                    "matches_expected": False,
                    "note": "library directory exists but no CityLBM*.gha was found",
                }
            )
            continue
        for path in files:
            digest = sha256(path)
            rows.append(
                {
                    "kind": "staged_gha",
                    "path": str(path),
                    "found": True,
                    "sha256": digest,
                    "matches_expected": bool(expected_sha) and digest.lower() == expected_sha.lower(),
                    "note": "candidate staged GHA",
                }
            )
    return rows


def manual_manifest_template(expected_version: str, expected_sha: str) -> Dict[str, Any]:
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "operator": "manual-operator-name",
        "rhino_version": "paste Rhino About/SystemInfo version string",
        "grasshopper_version": "paste Grasshopper version string",
        "observed_plugin_version": expected_version,
        "observed_assembly_version": "0.4.0.0",
        "observed_gha_sha256": expected_sha,
        "evidence_artifacts": [
            "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png",
            "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt",
        ],
        "notes": (
            "Create docs/experiments/casee/results/rhino_gha_load_manifest.json only after a real "
            "Rhino/Grasshopper session shows CityLBM loaded from the staged GHA. Do not use this template as pass evidence."
        ),
    }


def build_payload() -> Dict[str, Any]:
    plugin_gate = read_json(PLUGIN_IDENTITY_GATE)
    rhino_gate = read_json(RHINO_LOAD_GATE)
    install_audit = read_json(GHA_INSTALL_AUDIT)
    expected_version = str(plugin_gate.get("plugin_public_version") or "0.4.0-rc")
    expected_sha = str(plugin_gate.get("tracked_gha_sha256") or sha256(TRACKED_GHA))
    rhinos = [file_status(path) for path in rhino_candidates()]
    staged = staged_gha_rows(expected_sha)
    template = manual_manifest_template(expected_version, expected_sha)
    checks = {
        "plugin_identity_gate_passed": plugin_gate.get("plugin_identity_gate_passed") is True,
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "tracked_gha_sha_available": bool(expected_sha),
        "rhino_executable_detected": any(row["found"] for row in rhinos),
        "matching_gha_staged": any(row["matches_expected"] for row in staged),
        "install_audit_passed": install_audit.get("install_audit_passed") is True,
        "rhino_load_gate_fail_closed": rhino_gate.get("rhino_loaded_new_gha") is False,
    }
    kit_ready = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "author_input_needed_manual_rhino_load" if kit_ready else "blocked_rhino_evidence_kit",
        "rhino_load_evidence_kit_ready": kit_ready,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "expected_plugin_public_version": expected_version,
        "expected_tracked_gha_sha256": expected_sha,
        "tracked_gha": file_status(TRACKED_GHA),
        "rhino_candidates": rhinos,
        "staged_gha_candidates": staged,
        "manual_manifest_template_path": rel(OUT_TEMPLATE),
        "manual_manifest_template": template,
        "checks": checks,
        "manual_steps": [
            "Open Rhino from one detected Rhino.exe path.",
            "Start Grasshopper and ensure the staged CityLBM GHA is loaded, not an older copy.",
            "Capture a screenshot or log showing CityLBM version/path/hash.",
            "Copy rhino_gha_load_manifest.template.json to rhino_gha_load_manifest.json and replace template fields with observed values.",
            "Run python docs/experiments/casee/tools/rhino_gha_load_gate.py and then python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0.",
        ],
        "boundary": (
            "This kit prepares manual evidence collection only. It does not prove Rhino loaded the plugin, "
            "does not run CFD, and does not improve official Case E z=2 m metrics."
        ),
    }


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = ["kind", "path", "found", "sha256", "matches_expected", "note"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Rhino/GHA Load Evidence Kit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Evidence kit ready: {payload['rhino_load_evidence_kit_ready']}",
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
    lines += [
        "",
        "## Manual Steps",
        "",
    ]
    for idx, step in enumerate(payload["manual_steps"], start=1):
        lines.append(f"{idx}. {step}")
    lines += [
        "",
        "## Template",
        "",
        f"- Template path: `{payload['manual_manifest_template_path']}`",
        "",
        "```json",
        json.dumps(payload["manual_manifest_template"], indent=2),
        "```",
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
    OUT_TEMPLATE.write_text(json.dumps(payload["manual_manifest_template"], indent=2), encoding="utf-8")
    rows = [
        {"kind": "tracked_gha", **payload["tracked_gha"], "matches_expected": True, "note": "tracked release asset"},
        *payload["rhino_candidates"],
        *payload["staged_gha_candidates"],
    ]
    normalized = []
    for row in rows:
        normalized.append(
            {
                "kind": row.get("kind", "rhino_executable"),
                "path": row.get("path", ""),
                "found": row.get("found", False),
                "sha256": row.get("sha256", ""),
                "matches_expected": row.get("matches_expected", False),
                "note": row.get("note", "candidate Rhino executable"),
            }
        )
    write_csv(OUT_CSV, normalized)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"rhino_load_evidence_kit_ready": payload["rhino_load_evidence_kit_ready"], "out_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
