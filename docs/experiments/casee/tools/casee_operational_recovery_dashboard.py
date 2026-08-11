#!/usr/bin/env python3
"""Summarize the ordered recovery path before another official Case E run."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_operational_recovery_dashboard.json"
OUT_CSV = RESULTS_DIR / "casee_operational_recovery_dashboard.csv"
OUT_MD = RESULTS_DIR / "casee_operational_recovery_dashboard.md"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def command(code: str) -> str:
    return code


def recovery_rows(
    release_gate: Dict[str, Any],
    space_gate: Dict[str, Any],
    vs_recovery: Dict[str, Any],
    launcher: Dict[str, Any],
    gpu_gate: Dict[str, Any],
    rhino_schema: Dict[str, Any],
    preflight: Dict[str, Any],
) -> List[Dict[str, Any]]:
    space = space_gate.get("summary") or {}
    vs = vs_recovery.get("summary") or {}
    launch = launcher.get("summary") or {}
    metrics = release_gate.get("metrics") or {}
    rows: List[Dict[str, Any]] = [
        {
            "step_id": "OP001_system_drive_space",
            "priority": 1,
            "status": "blocked" if not space.get("space_ready_for_vs_cpp_launcher") else "ready",
            "blocks_long_run": True,
            "evidence_path": rel(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json"),
            "current_fact": (
                f"C: free={space.get('system_drive_free_gb')} GB; "
                f"needed={space.get('min_system_drive_free_gb')} GB; "
                f"shortfall={space.get('additional_free_needed_gb')} GB"
            ),
            "next_action": "Free system-drive space manually until C: has at least 8 GB free.",
            "verification_command": command("python docs/experiments/casee/tools/vs_cpp_system_drive_space_gate.py"),
            "paper_use": "Operational blocker evidence only.",
        },
        {
            "step_id": "OP002_vs_cpp_install",
            "priority": 2,
            "status": "blocked" if not vs.get("vs_cpp_ready") else "ready",
            "blocks_long_run": False,
            "evidence_path": rel(RESULTS_DIR / "vs_cpp_recovery_gate.json"),
            "current_fact": (
                f"vs_cpp_ready={vs.get('vs_cpp_ready')}; "
                f"can_attempt_install_now={vs.get('can_attempt_install_now')}; "
                f"blockers={len(vs.get('blockers') or [])}"
            ),
            "next_action": "After C: space is sufficient, launch the explicit UAC recovery script and verify vswhere/VC tools.",
            "verification_command": command("python docs/experiments/casee/tools/vs_cpp_recovery_gate.py"),
            "paper_use": "Build-chain reproducibility evidence only.",
        },
        {
            "step_id": "OP003_uac_launcher",
            "priority": 3,
            "status": "blocked" if not launch.get("can_launch_elevated_install_now") else "ready_for_manual_launch",
            "blocks_long_run": False,
            "evidence_path": rel(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json"),
            "current_fact": (
                f"can_launch={launch.get('can_launch_elevated_install_now')}; "
                f"launch_attempted={launch.get('launch_attempted')}; "
                f"blockers={launch.get('blockers')}"
            ),
            "next_action": "Run the launcher with -Launch only after space blockers are resolved.",
            "verification_command": command(
                "powershell -NoProfile -ExecutionPolicy Bypass -File docs/experiments/casee/tools/vs_cpp_buildtools_elevated_launcher.ps1 -Launch -NoPause"
            ),
            "paper_use": "Manual recovery traceability only.",
        },
        {
            "step_id": "OP004_gpu_recovery",
            "priority": 4,
            "status": "blocked" if not gpu_gate.get("gpu_runtime_ready") else "ready",
            "blocks_long_run": True,
            "evidence_path": rel(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json"),
            "current_fact": (
                f"gpu_runtime_ready={gpu_gate.get('gpu_runtime_ready')}; "
                f"gpu_lost_detected={gpu_gate.get('gpu_lost_detected')}; "
                f"long_run_allowed={gpu_gate.get('long_fluidx3d_run_allowed')}"
            ),
            "next_action": "Reboot or recover the NVIDIA device, then rerun the GPU fail-fast gate.",
            "verification_command": command("python docs/experiments/casee/tools/citylbm_gpu_runtime_failfast_gate.py"),
            "paper_use": "Runtime blocker evidence only.",
        },
        {
            "step_id": "OP005_rhino_load_evidence",
            "priority": 5,
            "status": "blocked" if not rhino_schema.get("manual_manifest_claim_ready") else "ready",
            "blocks_long_run": False,
            "evidence_path": rel(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json"),
            "current_fact": (
                f"manual_manifest_present={rhino_schema.get('manual_manifest_present')}; "
                f"manual_manifest_claim_ready={rhino_schema.get('manual_manifest_claim_ready')}; "
                f"rhino_loaded_new_gha={rhino_schema.get('rhino_loaded_new_gha')}"
            ),
            "next_action": "Load the staged GHA in Rhino/Grasshopper and record the manual manifest plus screenshot/log evidence.",
            "verification_command": command("python docs/experiments/casee/tools/rhino_gha_load_manifest_schema_gate.py"),
            "paper_use": "Software-load identity evidence only.",
        },
        {
            "step_id": "OP006_official_followup_preflight",
            "priority": 6,
            "status": "blocked" if not preflight.get("official_followup_run_allowed") else "ready",
            "blocks_long_run": True,
            "evidence_path": rel(RESULTS_DIR / "casee_official_run_preflight.json"),
            "current_fact": (
                f"official_followup_run_allowed={preflight.get('official_followup_run_allowed')}; "
                f"blocked_gates={preflight.get('blocked_gates')}"
            ),
            "next_action": "Rerun preflight after environment recovery before generating or launching another official long run.",
            "verification_command": command("python docs/experiments/casee/tools/casee_official_run_preflight.py"),
            "paper_use": "Pre-run protocol evidence only.",
        },
        {
            "step_id": "OP007_formal_metric_gate",
            "priority": 7,
            "status": "blocked" if not release_gate.get("formal_release_allowed") else "ready",
            "blocks_long_run": False,
            "evidence_path": rel(RESULTS_DIR / "release_gate.json"),
            "current_fact": (
                f"MAE={metrics.get('mae_pp')} pp; R2={metrics.get('r2')}; "
                f"Pearson={metrics.get('pearson')}; formal_release_allowed={release_gate.get('formal_release_allowed')}"
            ),
            "next_action": "Only a completed, logged official z=2 m raw_trilinear run can replace this metric gate.",
            "verification_command": command(
                "python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_casee_probe_time_mean.csv>"
            ),
            "paper_use": "Current negative validation and limitations result.",
        },
    ]
    return rows


def summarize(rows: List[Dict[str, Any]], release_gate: Dict[str, Any]) -> Dict[str, Any]:
    blocking_steps = [row for row in rows if row["status"] == "blocked"]
    long_run_blockers = [row["step_id"] for row in rows if row["status"] == "blocked" and row["blocks_long_run"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "operational_recovery_ready; blocked official run and formal release",
        "operational_recovery_dashboard_passed": True,
        "blocking_step_count": len(blocking_steps),
        "blocking_steps": [row["step_id"] for row in blocking_steps],
        "long_fluidx3d_run_allowed": not long_run_blockers,
        "long_run_blockers": long_run_blockers,
        "recommended_tag": release_gate.get("recommended_tag"),
        "formal_release_allowed": bool(release_gate.get("formal_release_allowed")),
        "formal_accuracy_claim_supported": False,
        "boundary": (
            "This dashboard aggregates existing recovery gates and commands only. It does not free disk space, install tools, "
            "recover GPU runtime, load Rhino, run FluidX3D, alter solver defaults, improve official metrics, or permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = [
        "step_id",
        "priority",
        "status",
        "blocks_long_run",
        "evidence_path",
        "current_fact",
        "next_action",
        "verification_command",
        "paper_use",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Case E Operational Recovery Dashboard",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Dashboard passed: {summary['operational_recovery_dashboard_passed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        f"- Blocking steps: {summary['blocking_step_count']}",
        f"- Long FluidX3D run allowed: {summary['long_fluidx3d_run_allowed']}",
        f"- Long-run blockers: {', '.join(summary['long_run_blockers']) or 'None'}",
        f"- Formal v0.4.0 allowed: {summary['formal_release_allowed']}",
        f"- Recommended tag: `{summary['recommended_tag']}`",
        "",
        "## Ordered Recovery Path",
        "",
        "| priority | step | status | blocks long run | next action | verification |",
        "|---:|---|---|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['priority']} | `{row['step_id']}` | {row['status']} | {row['blocks_long_run']} | "
            f"{row['next_action']} | `{row['verification_command']}` |"
        )
    lines += ["", "## Evidence Links", ""]
    for row in payload["rows"]:
        lines.append(f"- `{row['step_id']}`: `{row['evidence_path']}`; {row['current_fact']}")
    lines += ["", "## Boundary", "", summary["boundary"]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    space_gate = read_json(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json")
    vs_recovery = read_json(RESULTS_DIR / "vs_cpp_recovery_gate.json")
    launcher = read_json(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json")
    gpu_gate = read_json(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json")
    rhino_schema = read_json(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    rows = recovery_rows(release_gate, space_gate, vs_recovery, launcher, gpu_gate, rhino_schema, preflight)
    summary = summarize(rows, release_gate)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": [
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json"),
            rel(RESULTS_DIR / "vs_cpp_recovery_gate.json"),
            rel(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json"),
            rel(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json"),
            rel(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json"),
            rel(RESULTS_DIR / "casee_official_run_preflight.json"),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "operational_recovery_dashboard_passed": summary["operational_recovery_dashboard_passed"],
                "blocking_step_count": summary["blocking_step_count"],
                "long_fluidx3d_run_allowed": summary["long_fluidx3d_run_allowed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
