#!/usr/bin/env python3
"""Generate a recovery runbook for blocked Case E runtime/build prerequisites."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_environment_recovery_runbook.json"
OUT_CSV = RESULTS_DIR / "casee_environment_recovery_runbook.csv"
OUT_MD = RESULTS_DIR / "casee_environment_recovery_runbook.md"

WORKSPACE_CLEANUP_CANDIDATES = [
    "CityLBM/NuGet",
    "CityLBM/bin/Release",
    "CityLBM/obj",
    "NuGet",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dir_size(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"path": path.as_posix(), "exists": False, "file_count": 0, "size_bytes": 0, "size_mb": 0.0}
    file_count = 0
    size = 0
    for item in path.rglob("*"):
        if item.is_file():
            file_count += 1
            size += item.stat().st_size
    return {
        "path": path.resolve().relative_to(ROOT).as_posix(),
        "exists": True,
        "file_count": file_count,
        "size_bytes": size,
        "size_mb": round(size / (1024**2), 3),
    }


def disk_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for drive in ["C:\\", "D:\\", "E:\\", "F:\\", "G:\\"]:
        if not Path(drive).exists():
            continue
        usage = shutil.disk_usage(drive)
        rows.append(
            {
                "drive": drive,
                "free_gb": round(usage.free / (1024**3), 3),
                "total_gb": round(usage.total / (1024**3), 3),
            }
        )
    return rows


def action_rows(preflight: Dict[str, Any], build_chain: Dict[str, Any], cleanup: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocked = set(preflight.get("blocked_gates", []))
    c_free = next((row.get("free_gb") for row in disk_rows() if row.get("drive") == "C:\\"), None)
    cleanup_mb = sum(float(row.get("size_mb", 0.0)) for row in cleanup)
    vs = build_chain.get("visual_studio_build_tools_2022_cpp", {})
    install_command = (vs.get("install_attempt") or {}).get("command") or (
        'winget install --id Microsoft.VisualStudio.2022.BuildTools --accept-package-agreements '
        '--accept-source-agreements --silent --override "--wait --quiet --norestart '
        '--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"'
    )
    return [
        {
            "step_id": "REC001_gpu_recovery",
            "enabled": "gpu_runtime" in blocked,
            "priority": 1,
            "blocking_gate": "gpu_runtime",
            "action": "Reboot or recover the NVIDIA driver/device before any long native FluidX3D run.",
            "verification_command": "nvidia-smi",
            "pass_condition": "returncode=0 and no GPU-lost message.",
            "risk_boundary": "GPU readiness is environment evidence only, not solver accuracy.",
        },
        {
            "step_id": "REC002_free_c_drive",
            "enabled": "vs_cpp_build_tools" in blocked,
            "priority": 2,
            "blocking_gate": "vs_cpp_build_tools",
            "action": (
                f"Free C: drive space to at least 8 GB before retrying VS Build Tools C++; "
                f"current free space is {c_free} GB. Workspace build-cache candidates total only {cleanup_mb:.3f} MB."
            ),
            "verification_command": "Get-PSDrive C",
            "pass_condition": "C: free space >= 8 GB; workspace cache cleanup alone is not enough if the current value remains near 0.5 GB.",
            "risk_boundary": "Do not delete user data; record any cleanup outside the repo separately.",
        },
        {
            "step_id": "REC003_install_vs_cpp",
            "enabled": "vs_cpp_build_tools" in blocked,
            "priority": 3,
            "blocking_gate": "vs_cpp_build_tools",
            "action": "After freeing disk space and approving UAC, install Visual Studio Build Tools 2022 C++ workload.",
            "verification_command": install_command,
            "pass_condition": "Installer exits 0 and vswhere finds Microsoft.VisualStudio.Component.VC.Tools.x86.x64.",
            "risk_boundary": "Installation readiness is build-chain evidence only.",
        },
        {
            "step_id": "REC004_refresh_build_chain",
            "enabled": True,
            "priority": 4,
            "blocking_gate": "build_chain_manifest",
            "action": "Refresh the build-chain manifest after GPU, disk, or VS changes.",
            "verification_command": "python docs/experiments/casee/tools/build_chain_audit.py",
            "pass_condition": "build_chain_manifest.json records the updated GPU, disk, .NET, FluidX3D and VS C++ status.",
            "risk_boundary": "This does not create a new CFD result.",
        },
        {
            "step_id": "REC005_rhino_manifest",
            "enabled": "rhino_gha_load" in blocked,
            "priority": 5,
            "blocking_gate": "rhino_gha_load",
            "action": "Load the tracked CityLBM/bin/CityLBM.gha in Rhino/Grasshopper and create the manual load manifest plus screenshot/log evidence.",
            "verification_command": "python docs/experiments/casee/tools/rhino_gha_load_gate.py",
            "pass_condition": "rhino_gha_load_gate.json reports rhino_loaded_new_gha=true from real manifest evidence.",
            "risk_boundary": "Software-load identity only; not CFD accuracy.",
        },
        {
            "step_id": "REC006_preflight_rerun",
            "enabled": True,
            "priority": 6,
            "blocking_gate": "official_followup_preflight",
            "action": "Rerun official follow-up preflight before scheduling another long Case E native run.",
            "verification_command": "python docs/experiments/casee/tools/casee_official_run_preflight.py",
            "pass_condition": "official_followup_run_allowed=true before launching another official long follow-up.",
            "risk_boundary": "Preflight readiness is not solver-output evidence.",
        },
        {
            "step_id": "REC007_reproducibility_suite",
            "enabled": True,
            "priority": 7,
            "blocking_gate": "evidence_chain",
            "action": "Run the full lightweight evidence suite after any recovery or code change.",
            "verification_command": "python docs/experiments/casee/tools/reproducibility_suite.py",
            "pass_condition": "suite_passed=true; formal_release_allowed remains false until official z=2 m metrics pass.",
            "risk_boundary": "Claim-safety evidence only unless a new audited official probe CSV is supplied.",
        },
    ]


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = ["step_id", "enabled", "priority", "blocking_gate", "action", "verification_command", "pass_condition", "risk_boundary"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Environment Recovery Runbook",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Official follow-up run allowed now: {payload['official_followup_run_allowed']}",
        f"- Formal v0.4.0 release allowed: {payload['formal_release_allowed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        "",
        "## Workspace Cleanup Candidates",
        "",
        "| path | exists | files | size MB |",
        "|---|---:|---:|---:|",
    ]
    for row in payload["workspace_cleanup_candidates"]:
        lines.append(f"| `{row['path']}` | {row['exists']} | {row['file_count']} | {row['size_mb']} |")
    lines += [
        "",
        "## Recovery Steps",
        "",
        "| step | enabled | priority | gate | verification |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload["steps"]:
        lines.append(
            f"| `{row['step_id']}` | {row['enabled']} | {row['priority']} | "
            f"{row['blocking_gate']} | `{row['verification_command']}` |"
        )
    lines += [
        "",
        "## Details",
        "",
    ]
    for row in payload["steps"]:
        lines += [
            f"### {row['step_id']}",
            "",
            f"- Action: {row['action']}",
            f"- Pass condition: {row['pass_condition']}",
            f"- Risk boundary: {row['risk_boundary']}",
            "",
        ]
    lines += [
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    build_chain = read_json(RESULTS_DIR / "build_chain_manifest.json")
    cleanup = [dir_size(ROOT / item) for item in WORKSPACE_CLEANUP_CANDIDATES]
    rows = action_rows(preflight, build_chain, cleanup)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "blocked_environment_recovery_runbook",
        "official_followup_run_allowed": bool(preflight.get("official_followup_run_allowed")),
        "formal_release_allowed": bool(preflight.get("formal_release_allowed")),
        "blocked_gates": preflight.get("blocked_gates", []),
        "disk": disk_rows(),
        "workspace_cleanup_candidates": cleanup,
        "steps": rows,
        "boundary": (
            "This runbook records recovery actions for environment and build-chain blockers. "
            "It does not delete files, install tools, run CFD, improve official z=2 m metrics, or allow formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"steps": len(rows), "blocked_gates": payload["blocked_gates"], "out_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
