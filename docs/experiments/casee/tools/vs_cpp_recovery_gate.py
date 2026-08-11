#!/usr/bin/env python3
"""Audit the Visual Studio Build Tools C++ recovery path for Case E."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
SCRIPT = CASE_DIR / "tools" / "vs_cpp_buildtools_recovery.ps1"
PROBE_JSON = RESULTS_DIR / "vs_cpp_buildtools_recovery_probe.json"
OUT_JSON = RESULTS_DIR / "vs_cpp_recovery_gate.json"
OUT_CSV = RESULTS_DIR / "vs_cpp_recovery_gate.csv"
OUT_MD = RESULTS_DIR / "vs_cpp_recovery_gate.md"


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


def run_powershell_probe() -> Dict[str, Any]:
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
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=60, encoding="utf-8", errors="replace")
        return {
            "command": " ".join(command),
            "found": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": " ".join(command), "found": True, "returncode": None, "stdout": "", "stderr": str(exc)}


def script_contract_status() -> Dict[str, Any]:
    text = SCRIPT.read_text(encoding="utf-8", errors="replace") if SCRIPT.exists() else ""
    return {
        "script_found": SCRIPT.exists(),
        "requires_explicit_install_switch": "[switch]$Install" in text and "if ($Install)" in text,
        "has_admin_check": "Test-IsAdmin" in text and "Administrator" in text,
        "has_system_drive_space_check": "MinSystemDriveFreeGB" in text and "system_drive_free_gb" in text,
        "has_vc_workload": "Microsoft.VisualStudio.Workload.VCTools" in text,
        "has_windows_sdk_component": "Microsoft.VisualStudio.Component.Windows11SDK.26100" in text,
        "has_cmake_component": "Microsoft.VisualStudio.Component.VC.CMake.Project" in text,
        "writes_json_probe": "OutJson" in text and "ConvertTo-Json" in text,
        "noninteractive_mode": "NoPause" in text,
    }


def summarize(probe: Dict[str, Any], script_contract: Dict[str, Any], ps_result: Dict[str, Any]) -> Dict[str, Any]:
    blockers = list(probe.get("blockers") or [])
    vs_ready = bool(probe.get("vs_cpp_ready"))
    recovery_script_ready = all(bool(value) for value in script_contract.values())
    can_attempt_install_now = bool(
        probe.get("winget", {}).get("found")
        and probe.get("current_user_is_admin")
        and float(probe.get("system_drive_free_gb") or 0) >= float(probe.get("min_system_drive_free_gb") or 8.0)
    )
    checks = {
        "powershell_probe_ran": ps_result.get("returncode") == 0 and PROBE_JSON.exists(),
        "recovery_script_ready": recovery_script_ready,
        "default_mode_audit_only": script_contract.get("requires_explicit_install_switch") is True,
        "admin_and_space_guards_present": script_contract.get("has_admin_check") is True
        and script_contract.get("has_system_drive_space_check") is True,
        "vs_components_specified": script_contract.get("has_vc_workload") is True
        and script_contract.get("has_windows_sdk_component") is True
        and script_contract.get("has_cmake_component") is True,
        "claim_boundary_safe": vs_ready is False or probe.get("install_attempted") in {False, None},
    }
    gate_passed = all(bool(value) for value in checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "blocked_vs_cpp_recovery_ready_for_manual_install" if not vs_ready else "build_chain_vs_cpp_ready",
        "vs_cpp_recovery_gate_passed": gate_passed,
        "vs_cpp_ready": vs_ready,
        "can_attempt_install_now": can_attempt_install_now,
        "recommended_command": probe.get("recommended_command", ""),
        "blockers": blockers,
        "checks": checks,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "boundary": (
            "This gate verifies the VS C++ recovery path and current machine blockers. It does not install tools unless "
            "the PowerShell script is explicitly run with -Install, does not recover GPU runtime, does not add CFD output, "
            "and does not permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, summary: Dict[str, Any], probe: Dict[str, Any], script_contract: Dict[str, Any]) -> None:
    rows: List[Dict[str, Any]] = []
    for key, value in summary["checks"].items():
        rows.append({"item": key, "status": value, "evidence": "summary.checks", "limitation": ""})
    for key, value in script_contract.items():
        rows.append({"item": key, "status": value, "evidence": rel(SCRIPT), "limitation": ""})
    for blocker in summary["blockers"]:
        rows.append({"item": "blocker", "status": "blocked", "evidence": "PowerShell probe", "limitation": blocker})
    rows.append(
        {
            "item": "recommended_command",
            "status": "manual_action_required",
            "evidence": probe.get("recommended_command", ""),
            "limitation": "Run only from an elevated shell after C: space/UAC blockers are resolved.",
        }
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item", "status", "evidence", "limitation"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, summary: Dict[str, Any], probe: Dict[str, Any], ps_result: Dict[str, Any]) -> None:
    lines = [
        "# VS C++ Build Tools Recovery Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['vs_cpp_recovery_gate_passed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        f"- VS C++ ready: {summary['vs_cpp_ready']}",
        f"- Can attempt install now: {summary['can_attempt_install_now']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        "",
        "## Current Machine Probe",
        "",
        f"- PowerShell return code: {ps_result.get('returncode')}",
        f"- Current user is admin: {probe.get('current_user_is_admin')}",
        f"- System drive free GB: {probe.get('system_drive_free_gb')}",
        f"- Minimum system drive free GB: {probe.get('min_system_drive_free_gb')}",
        f"- Install path: `{probe.get('install_path')}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in summary["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## Blockers", ""]
    for blocker in summary["blockers"] or ["None"]:
        lines.append(f"- {blocker}")
    lines += [
        "",
        "## Manual Recovery Command",
        "",
        "Run only from an elevated PowerShell after resolving the listed blockers:",
        "",
        "```powershell",
        f"powershell -NoProfile -ExecutionPolicy Bypass -File {rel(SCRIPT)} -Install -NoPause",
        "```",
        "",
        "The underlying winget command recorded by the probe is:",
        "",
        "```powershell",
        str(summary["recommended_command"]),
        "```",
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ps_result = run_powershell_probe()
    probe = read_json(PROBE_JSON)
    script_contract = script_contract_status()
    summary = summarize(probe, script_contract, ps_result)
    payload = {
        "summary": summary,
        "script": file_status(SCRIPT),
        "probe_artifact": file_status(PROBE_JSON),
        "powershell_probe": ps_result,
        "script_contract": script_contract,
        "probe": probe,
        "source_artifacts": [rel(SCRIPT), rel(PROBE_JSON)],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, summary, probe, script_contract)
    write_markdown(OUT_MD, summary, probe, ps_result)
    print(json.dumps({"vs_cpp_recovery_gate_passed": summary["vs_cpp_recovery_gate_passed"], "vs_cpp_ready": summary["vs_cpp_ready"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["vs_cpp_recovery_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
