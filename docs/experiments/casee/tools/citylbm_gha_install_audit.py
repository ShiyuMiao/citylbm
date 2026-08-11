#!/usr/bin/env python3
"""Audit whether the tracked CityLBM GHA is staged for Grasshopper loading."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
PACKAGED_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM" / "CityLBM.gha"
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
RHINO_LOAD_GATE = RESULTS_DIR / "rhino_gha_load_gate.json"
OUT_JSON = RESULTS_DIR / "citylbm_gha_install_audit.json"
OUT_CSV = RESULTS_DIR / "citylbm_gha_install_audit.csv"
OUT_MD = RESULTS_DIR / "citylbm_gha_install_audit.md"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": rel(path), "sha256": "", "size_bytes": None, "mtime_utc": ""}
    return {
        "found": True,
        "path": rel(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_library_dirs() -> List[Path]:
    appdata = Path(os.environ.get("APPDATA", ""))
    localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
    userprofile = Path(os.environ.get("USERPROFILE", ""))
    raw = [
        appdata / "Grasshopper" / "Libraries",
        appdata / "McNeel" / "Rhinoceros" / "8.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        appdata / "McNeel" / "Rhinoceros" / "7.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        appdata / "McNeel" / "Rhinoceros" / "6.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        localappdata / "McNeel" / "Rhinoceros" / "8.0" / "Plug-ins" / "Grasshopper" / "Libraries",
        userprofile / "AppData" / "Roaming" / "Grasshopper" / "Libraries",
    ]
    seen: set[str] = set()
    dirs: List[Path] = []
    for path in raw:
        if not str(path):
            continue
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            dirs.append(path)
    return dirs


def installed_candidates(expected_sha: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for directory in candidate_library_dirs():
        if not directory.exists():
            rows.append(
                {
                    "library_dir": str(directory),
                    "library_dir_exists": False,
                    "path": "",
                    "found": False,
                    "sha256": "",
                    "matches_tracked_gha": False,
                    "size_bytes": None,
                    "mtime_utc": "",
                }
            )
            continue
        files = sorted(directory.glob("CityLBM*.gha"))
        if not files:
            rows.append(
                {
                    "library_dir": str(directory),
                    "library_dir_exists": True,
                    "path": "",
                    "found": False,
                    "sha256": "",
                    "matches_tracked_gha": False,
                    "size_bytes": None,
                    "mtime_utc": "",
                }
            )
            continue
        for path in files:
            digest = sha256(path)
            rows.append(
                {
                    "library_dir": str(directory),
                    "library_dir_exists": True,
                    "path": str(path),
                    "found": True,
                    "sha256": digest,
                    "matches_tracked_gha": bool(expected_sha) and digest.lower() == expected_sha.lower(),
                    "size_bytes": path.stat().st_size,
                    "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                }
            )
    return rows


def powershell_copy_command(target_dir: Path) -> str:
    source = str(TRACKED_GHA)
    target = str(target_dir / "CityLBM.gha")
    return (
        f"New-Item -ItemType Directory -Force -Path '{target_dir}' | Out-Null; "
        f"Copy-Item -LiteralPath '{source}' -Destination '{target}' -Force"
    )


def build_payload() -> Dict[str, Any]:
    plugin_gate = read_json(PLUGIN_IDENTITY_GATE)
    rhino_gate = read_json(RHINO_LOAD_GATE)
    expected_sha = str(plugin_gate.get("tracked_gha_sha256") or (sha256(TRACKED_GHA) if TRACKED_GHA.exists() else ""))
    candidates = installed_candidates(expected_sha)
    matching = [row for row in candidates if row["matches_tracked_gha"]]
    existing_dirs = [path for path in candidate_library_dirs() if path.exists()]
    recommended_dir = existing_dirs[0] if existing_dirs else candidate_library_dirs()[0]
    checks = {
        "plugin_identity_gate_passed": plugin_gate.get("plugin_identity_gate_passed") is True,
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "tracked_gha_hash_matches_identity_gate": bool(expected_sha)
        and TRACKED_GHA.exists()
        and sha256(TRACKED_GHA).lower() == expected_sha.lower(),
        "packaged_gha_exists": PACKAGED_GHA.exists(),
        "grasshopper_library_dir_detected_or_recommendable": recommended_dir is not None,
        "matching_gha_already_staged": bool(matching),
        "rhino_load_gate_still_fail_closed": rhino_gate.get("rhino_loaded_new_gha") is False
        and rhino_gate.get("claim_readiness") == "blocked_manual_rhino_load",
    }
    install_audit_passed = (
        checks["plugin_identity_gate_passed"]
        and checks["tracked_gha_exists"]
        and checks["tracked_gha_hash_matches_identity_gate"]
        and checks["grasshopper_library_dir_detected_or_recommendable"]
        and checks["rhino_load_gate_still_fail_closed"]
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "install_ready_pending_manual_rhino_load",
        "install_audit_passed": install_audit_passed,
        "matching_gha_already_staged": bool(matching),
        "rhino_loaded_new_gha": False,
        "expected_tracked_gha_sha256": expected_sha,
        "tracked_gha": file_status(TRACKED_GHA),
        "packaged_gha": file_status(PACKAGED_GHA),
        "candidate_library_dirs": [str(path) for path in candidate_library_dirs()],
        "recommended_library_dir": str(recommended_dir),
        "recommended_manual_copy_command": powershell_copy_command(recommended_dir),
        "installed_candidates": candidates,
        "checks": checks,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "boundary": (
            "This audit only checks whether the tracked CityLBM.gha is staged or stageable for Grasshopper. "
            "It does not copy files automatically, does not prove Rhino loaded the plugin, does not run CFD, "
            "and does not support formal accuracy claims."
        ),
    }


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    fieldnames = [
        "library_dir",
        "library_dir_exists",
        "path",
        "found",
        "sha256",
        "matches_tracked_gha",
        "size_bytes",
        "mtime_utc",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload["installed_candidates"]:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM GHA Install Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Install audit passed: {payload['install_audit_passed']}",
        f"- Matching GHA already staged: {payload['matching_gha_already_staged']}",
        f"- Rhino loaded new GHA: {payload['rhino_loaded_new_gha']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
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
        "## Recommended Manual Copy Command",
        "",
        "Run only when you want to stage the current tracked GHA for Grasshopper:",
        "",
        "```powershell",
        payload["recommended_manual_copy_command"],
        "```",
        "",
        "## Installed Candidates",
        "",
        "| library dir | found | matches tracked GHA | path | sha256 |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload["installed_candidates"]:
        lines.append(
            f"| `{row['library_dir']}` | {row['found']} | {row['matches_tracked_gha']} | "
            f"`{row['path']}` | `{row['sha256']}` |"
        )
    lines += ["", "## Boundary", "", payload["boundary"]]
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
                "install_audit_passed": payload["install_audit_passed"],
                "matching_gha_already_staged": payload["matching_gha_already_staged"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["install_audit_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
