#!/usr/bin/env python3
"""Audit system-drive free space before VS Build Tools C++ recovery."""

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "vs_cpp_system_drive_space_gate.json"
OUT_CSV = RESULTS_DIR / "vs_cpp_system_drive_space_gate.csv"
OUT_MD = RESULTS_DIR / "vs_cpp_system_drive_space_gate.md"
MIN_SYSTEM_DRIVE_FREE_GB = 8.0


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except Exception:
        return str(path)


def gb(value: int) -> float:
    return round(value / (1024**3), 3)


def dir_size(path: Path, *, max_files: int = 250_000) -> Dict[str, Any]:
    if not path.exists():
        return {
            "found": False,
            "path": str(path),
            "size_bytes": 0,
            "size_gb": 0.0,
            "file_count": 0,
            "dir_count": 0,
            "errors": [],
            "truncated": False,
        }
    total = 0
    files = 0
    dirs = 0
    errors: List[str] = []
    truncated = False
    for current, dirnames, filenames in os.walk(path, topdown=True, onerror=lambda exc: errors.append(str(exc))):
        dirs += len(dirnames)
        for filename in filenames:
            files += 1
            if files > max_files:
                truncated = True
                dirnames[:] = []
                break
            fpath = Path(current) / filename
            try:
                total += fpath.stat().st_size
            except OSError as exc:
                errors.append(f"{fpath}: {exc}")
        if truncated:
            break
    return {
        "found": True,
        "path": str(path),
        "size_bytes": total,
        "size_gb": gb(total),
        "file_count": files,
        "dir_count": dirs,
        "errors": errors[:25],
        "truncated": truncated,
    }


def existing_env_path(name: str) -> Optional[Path]:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value)


def unique_candidates(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    rows = []
    for item in items:
        path = Path(str(item["path"]))
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(item)
    return rows


def candidate_specs(system_drive: str) -> List[Dict[str, Any]]:
    userprofile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    localappdata = Path(os.environ.get("LOCALAPPDATA", userprofile / "AppData" / "Local"))
    temp_paths = [p for p in [existing_env_path("TEMP"), existing_env_path("TMP")] if p is not None]
    croot = Path(system_drive + "\\")
    specs = [
        {
            "id": "user_temp",
            "path": temp_paths[0] if temp_paths else localappdata / "Temp",
            "risk": "low",
            "cleanup_owner": "user",
            "manual_action": "Close running installers/apps, then remove stale files from the user temp folder or use Windows Storage cleanup.",
        },
        {
            "id": "winget_temp_cache",
            "path": localappdata / "Temp" / "WinGet",
            "risk": "low",
            "cleanup_owner": "user",
            "manual_action": "Remove stale WinGet installer cache after confirming no winget install is running.",
        },
        {
            "id": "pip_cache",
            "path": localappdata / "pip" / "Cache",
            "risk": "low",
            "cleanup_owner": "user",
            "manual_action": "Run `python -m pip cache purge` if Python package downloads can be re-fetched.",
        },
        {
            "id": "nuget_cache",
            "path": userprofile / ".nuget" / "packages",
            "risk": "medium",
            "cleanup_owner": "developer",
            "manual_action": "Run `dotnet nuget locals all --clear` only if package re-download is acceptable.",
        },
        {
            "id": "windows_update_download",
            "path": croot / "Windows" / "SoftwareDistribution" / "Download",
            "risk": "medium",
            "cleanup_owner": "administrator",
            "manual_action": "Use Windows Settings > System > Storage > Temporary files or Disk Cleanup as Administrator.",
        },
        {
            "id": "delivery_optimization_cache",
            "path": croot / "ProgramData" / "Microsoft" / "Windows" / "DeliveryOptimization" / "Cache",
            "risk": "medium",
            "cleanup_owner": "administrator",
            "manual_action": "Use Windows Delivery Optimization cleanup through system Storage settings.",
        },
        {
            "id": "recycle_bin",
            "path": croot / "$Recycle.Bin",
            "risk": "medium",
            "cleanup_owner": "user",
            "manual_action": "Review Recycle Bin contents manually before emptying.",
        },
    ]
    return unique_candidates(specs)


def audit_candidates(system_drive: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for spec in candidate_specs(system_drive):
        status = dir_size(Path(str(spec["path"])))
        row = {**spec, **status}
        row["candidate_for_manual_cleanup"] = bool(row["found"] and row["size_bytes"] > 0)
        rows.append(row)
    rows.sort(key=lambda item: int(item.get("size_bytes") or 0), reverse=True)
    return rows


def summarize(rows: List[Dict[str, Any]], system_drive: str) -> Dict[str, Any]:
    usage = shutil.disk_usage(system_drive + "\\")
    free_gb = gb(usage.free)
    shortfall_gb = round(max(0.0, MIN_SYSTEM_DRIVE_FREE_GB - free_gb), 3)
    low_risk_bytes = sum(int(row["size_bytes"]) for row in rows if row.get("risk") == "low")
    total_candidate_bytes = sum(int(row["size_bytes"]) for row in rows)
    enough_now = free_gb >= MIN_SYSTEM_DRIVE_FREE_GB
    low_risk_could_cover = free_gb + gb(low_risk_bytes) >= MIN_SYSTEM_DRIVE_FREE_GB
    any_errors = any(bool(row.get("errors")) for row in rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "space_preflight_ready" if enough_now else "space_preflight_blocked_manual_cleanup_needed",
        "vs_cpp_system_drive_space_gate_passed": True,
        "system_drive": system_drive,
        "system_drive_total_gb": gb(usage.total),
        "system_drive_free_gb": free_gb,
        "min_system_drive_free_gb": MIN_SYSTEM_DRIVE_FREE_GB,
        "additional_free_needed_gb": shortfall_gb,
        "space_ready_for_vs_cpp_launcher": enough_now,
        "low_risk_candidate_total_gb": gb(low_risk_bytes),
        "all_candidate_total_gb": gb(total_candidate_bytes),
        "low_risk_cleanup_could_cover_shortfall": low_risk_could_cover,
        "candidate_count": len(rows),
        "candidate_count_found": sum(1 for row in rows if row.get("found")),
        "scan_errors_present": any_errors,
        "deletion_attempted": False,
        "post_cleanup_verification": "python docs/experiments/casee/tools/vs_cpp_elevated_launcher_gate.py",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "boundary": (
            "This gate measures system-drive free space and manual cleanup candidates only. It does not delete files, "
            "install Visual Studio Build Tools, recover GPU runtime, run FluidX3D, improve Case E metrics, or permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "id",
        "path",
        "found",
        "risk",
        "cleanup_owner",
        "size_gb",
        "file_count",
        "dir_count",
        "truncated",
        "candidate_for_manual_cleanup",
        "manual_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# VS C++ System Drive Space Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['vs_cpp_system_drive_space_gate_passed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        f"- System drive: `{summary['system_drive']}`",
        f"- Free space: {summary['system_drive_free_gb']} GB",
        f"- Required free space: {summary['min_system_drive_free_gb']} GB",
        f"- Additional free space needed: {summary['additional_free_needed_gb']} GB",
        f"- Ready for VS C++ elevated launcher: {summary['space_ready_for_vs_cpp_launcher']}",
        f"- Low-risk candidate total: {summary['low_risk_candidate_total_gb']} GB",
        f"- Low-risk cleanup could cover shortfall: {summary['low_risk_cleanup_could_cover_shortfall']}",
        f"- Deletion attempted: {summary['deletion_attempted']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        "",
        "## Candidate Inventory",
        "",
        "| id | risk | owner | found | size GB | manual action |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['id']}` | {row['risk']} | {row['cleanup_owner']} | {row['found']} | "
            f"{row['size_gb']} | {row['manual_action']} |"
        )
    lines += [
        "",
        "## Next Verification",
        "",
        "After manual cleanup, rerun:",
        "",
        "```powershell",
        summary["post_cleanup_verification"],
        "```",
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    system_drive = (os.environ.get("SystemDrive") or "C:").rstrip("\\/")
    rows = audit_candidates(system_drive)
    summary = summarize(rows, system_drive)
    payload = {
        "summary": summary,
        "candidates": rows,
        "source_artifacts": [rel(Path(__file__))],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, summary, rows)
    print(
        json.dumps(
            {
                "vs_cpp_system_drive_space_gate_passed": summary["vs_cpp_system_drive_space_gate_passed"],
                "system_drive_free_gb": summary["system_drive_free_gb"],
                "additional_free_needed_gb": summary["additional_free_needed_gb"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
