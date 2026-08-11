#!/usr/bin/env python3
"""Audit the explicit UAC launcher for VS C++ Build Tools recovery."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
SCRIPT = CASE_DIR / "tools" / "vs_cpp_buildtools_elevated_launcher.ps1"
RECOVERY_SCRIPT = CASE_DIR / "tools" / "vs_cpp_buildtools_recovery.ps1"
PROBE_JSON = RESULTS_DIR / "vs_cpp_buildtools_elevated_launcher_probe.json"
OUT_JSON = RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json"
OUT_CSV = RESULTS_DIR / "vs_cpp_elevated_launcher_gate.csv"
OUT_MD = RESULTS_DIR / "vs_cpp_elevated_launcher_gate.md"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": rel(path), "sha256": "", "size_bytes": None}
    return {"found": True, "path": rel(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_launcher_probe() -> Dict[str, Any]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-OutJson",
        str(PROBE_JSON),
        "-NoPause",
    ]
    if not SCRIPT.exists():
        return {"command": " ".join(command), "found": False, "returncode": None, "stdout": "", "stderr": "script missing"}
    proc = subprocess.run(command, text=True, capture_output=True, timeout=60, encoding="utf-8", errors="replace")
    return {
        "command": " ".join(command),
        "found": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def script_contract_status() -> Dict[str, Any]:
    text = SCRIPT.read_text(encoding="utf-8", errors="replace") if SCRIPT.exists() else ""
    return {
        "script_found": SCRIPT.exists(),
        "recovery_script_found": RECOVERY_SCRIPT.exists(),
        "default_mode_audit_only": "[switch]$Launch" in text and "if ($Launch)" in text,
        "uses_uac_elevation": "-Verb RunAs" in text and "Start-Process" in text,
        "delegates_to_recovery_install": "vs_cpp_buildtools_recovery.ps1" in text and "-Install" in text,
        "has_system_drive_space_guard": "MinSystemDriveFreeGB" in text and "system_drive_free_gb" in text,
        "writes_json_probe": "OutJson" in text and "ConvertTo-Json" in text,
        "records_post_install_verifier": "vs_cpp_recovery_gate.py" in text,
        "has_claim_boundary": "formal v0.4.0" in text and "improve Case E metrics" in text,
    }


def summarize(probe: Dict[str, Any], contract: Dict[str, Any], ps_result: Dict[str, Any]) -> Dict[str, Any]:
    blockers = list(probe.get("blockers") or [])
    checks = {
        "powershell_probe_ran": ps_result.get("returncode") == 0 and PROBE_JSON.exists(),
        "launcher_script_ready": all(bool(value) for value in contract.values()),
        "audit_mode_did_not_launch": probe.get("launch_requested") is False and probe.get("launch_attempted") is False,
        "preflight_blockers_recorded": isinstance(blockers, list),
        "post_install_verifier_recorded": bool(probe.get("post_install_verification")),
        "claim_boundary_safe": "improve Case E metrics" in str(probe.get("boundary", "")),
    }
    gate_passed = all(bool(value) for value in checks.values())
    can_launch = bool(probe.get("can_launch_elevated_install_now"))
    if can_launch:
        readiness = "elevated_launcher_ready_for_manual_uac_install"
    else:
        readiness = "elevated_launcher_ready_but_preflight_blocked"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": readiness,
        "vs_cpp_elevated_launcher_gate_passed": gate_passed,
        "can_launch_elevated_install_now": can_launch,
        "launch_attempted": bool(probe.get("launch_attempted")),
        "blockers": blockers,
        "recovery_command": probe.get("recovery_command", ""),
        "post_install_verification": probe.get("post_install_verification", ""),
        "checks": checks,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "boundary": (
            "This gate verifies an explicit UAC launcher for VS Build Tools recovery. It does not launch installation "
            "during the suite, does not recover GPU runtime, does not add CFD output, and does not permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, summary: Dict[str, Any], contract: Dict[str, Any]) -> None:
    rows: List[Dict[str, Any]] = []
    for key, value in summary["checks"].items():
        rows.append({"item": key, "status": value, "evidence": "summary.checks", "limitation": ""})
    for key, value in contract.items():
        rows.append({"item": key, "status": value, "evidence": rel(SCRIPT), "limitation": ""})
    for blocker in summary["blockers"]:
        rows.append({"item": "blocker", "status": "blocked", "evidence": rel(PROBE_JSON), "limitation": blocker})
    rows.append(
        {
            "item": "manual_uac_command",
            "status": "manual_action_required",
            "evidence": summary["recovery_command"],
            "limitation": "Use the launcher with -Launch only after preflight blockers are resolved.",
        }
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item", "status", "evidence", "limitation"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: Dict[str, Any], probe: Dict[str, Any]) -> None:
    lines = [
        "# VS C++ Elevated Launcher Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['vs_cpp_elevated_launcher_gate_passed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        f"- Can launch elevated install now: {summary['can_launch_elevated_install_now']}",
        f"- Launch attempted by this gate: {summary['launch_attempted']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in summary["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## Current Preflight", ""]
    lines.append(f"- System drive free GB: {probe.get('system_drive_free_gb')}")
    lines.append(f"- Minimum system drive free GB: {probe.get('min_system_drive_free_gb')}")
    lines.append(f"- Current user is admin: {probe.get('current_user_is_admin')}")
    lines.append(f"- Install path: `{probe.get('install_path')}`")
    lines += ["", "## Blockers", ""]
    for blocker in summary["blockers"] or ["None"]:
        lines.append(f"- {blocker}")
    lines += [
        "",
        "## Manual Launch",
        "",
        "After resolving blockers, run:",
        "",
        "```powershell",
        f"powershell -NoProfile -ExecutionPolicy Bypass -File {rel(SCRIPT)} -Launch -NoPause",
        "```",
        "",
        "Then verify the installation with:",
        "",
        "```powershell",
        summary["post_install_verification"],
        "```",
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ps_result = run_launcher_probe()
    probe = read_json(PROBE_JSON)
    contract = script_contract_status()
    summary = summarize(probe, contract, ps_result)
    payload = {
        "summary": summary,
        "script": file_status(SCRIPT),
        "recovery_script": file_status(RECOVERY_SCRIPT),
        "probe_artifact": file_status(PROBE_JSON),
        "powershell_probe": ps_result,
        "script_contract": contract,
        "probe": probe,
        "source_artifacts": [rel(SCRIPT), rel(RECOVERY_SCRIPT), rel(PROBE_JSON)],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, summary, contract)
    write_markdown(OUT_MD, summary, probe)
    print(
        json.dumps(
            {
                "vs_cpp_elevated_launcher_gate_passed": summary["vs_cpp_elevated_launcher_gate_passed"],
                "can_launch_elevated_install_now": summary["can_launch_elevated_install_now"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if summary["vs_cpp_elevated_launcher_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
