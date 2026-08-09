#!/usr/bin/env python3
"""Generate the next-run command matrix for AIJ Case E official z=2 m follow-up."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
NATIVE_DIR = CASE_DIR / "native_cases"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fieldnames = [
        "runbook_id",
        "stage",
        "enabled_now",
        "evidence_type",
        "purpose",
        "trigger_condition",
        "command",
        "expected_artifact",
        "formal_result_policy",
        "pass_condition",
        "forbidden_claim",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def command_rows(release_gate: Dict[str, Any], blockers: Dict[str, Any], dx1_readiness: Dict[str, Any]) -> List[Dict[str, Any]]:
    gpu_blocked = any(
        b.get("blocker_id") == "B003_gpu_runtime" and b.get("status") == "blocked"
        for b in blockers.get("blockers", [])
    )
    rhino_blocked = any(
        b.get("blocker_id") == "B002_rhino_new_gha_load" and b.get("status") == "blocked"
        for b in blockers.get("blockers", [])
    )
    metric_blocked = not bool(release_gate.get("checks", {}).get("official_z2m_metric_gate"))
    dx1_summary = dx1_readiness.get("summary") or {}
    dx1_headroom_ok = dx1_summary.get("dx1_memory_headroom_ok") is True
    common_forbidden = "Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone."
    rows: List[Dict[str, Any]] = [
        {
            "runbook_id": "R001_preflight_release_chain",
            "stage": "preflight",
            "enabled_now": True,
            "evidence_type": "newly_run",
            "purpose": "Rebuild CityLBM and regenerate fail-closed release evidence before scheduling more CFD.",
            "trigger_condition": "Any time the branch changes.",
            "command": "python docs/experiments/casee/tools/reproducibility_suite.py",
            "expected_artifact": "docs/experiments/casee/results/casee_reproducibility_suite.json",
            "formal_result_policy": "Reproducibility evidence only.",
            "pass_condition": "suite_passed=true and formal_release_allowed=false until official metrics pass.",
            "forbidden_claim": common_forbidden,
        },
        {
            "runbook_id": "R002_gpu_recovery_check",
            "stage": "preflight",
            "enabled_now": True,
            "evidence_type": "newly_run",
            "purpose": "Verify whether long native FluidX3D runs can be attempted.",
            "trigger_condition": "After rebooting or recovering the NVIDIA device.",
            "command": "nvidia-smi",
            "expected_artifact": "docs/experiments/casee/results/build_chain_manifest.json after build_chain_audit.py rerun",
            "formal_result_policy": "Environment readiness only.",
            "pass_condition": "returncode=0 and no GPU-lost message.",
            "forbidden_claim": "Do not claim a new CFD result from GPU readiness.",
        },
        {
            "runbook_id": "R003_build_chain_refresh",
            "stage": "preflight",
            "enabled_now": True,
            "evidence_type": "newly_run",
            "purpose": "Refresh .NET, FluidX3D, VS C++ and disk-space evidence.",
            "trigger_condition": "After freeing C: space, installing VS Build Tools C++, or changing FluidX3D binaries.",
            "command": "python docs/experiments/casee/tools/build_chain_audit.py",
            "expected_artifact": "docs/experiments/casee/results/build_chain_manifest.json",
            "formal_result_policy": "Build-chain evidence only.",
            "pass_condition": "dotnet ready; FluidX3D binary found; GPU ready for long runs; VS C++ status recorded.",
            "forbidden_claim": common_forbidden,
        },
        {
            "runbook_id": "R004_rhino_gha_load_check",
            "stage": "manual_validation",
            "enabled_now": not rhino_blocked,
            "evidence_type": "author_input_needed",
            "purpose": "Close the Rhino/Grasshopper new-GHA release gate.",
            "trigger_condition": "After copying/loading tracked CityLBM/bin/CityLBM.gha into Rhino/Grasshopper.",
            "command": "Manual: capture Rhino/Grasshopper screenshot/log showing CityLBM Version=0.4.0-rc and GHA SHA256.",
            "expected_artifact": "docs/experiments/casee/results/rhino_gha_load_manifest.json",
            "formal_result_policy": "Software identity/load evidence only.",
            "pass_condition": "Manifest proves Rhino loaded the tracked GHA hash, not an old installed copy.",
            "forbidden_claim": "Do not mark rhino_loaded_new_gha=true without an artifact.",
        },
        {
            "runbook_id": "R005_official_dx2_zcenter_replicate",
            "stage": "native_case_generation",
            "enabled_now": not gpu_blocked,
            "evidence_type": "blocked_until_gpu_ready" if gpu_blocked else "newly_run_when_executed",
            "purpose": "Replicate the current best official raw_trilinear diagnostic before changing physics.",
            "trigger_condition": "GPU ready; need a clean baseline for comparison.",
            "command": "python docs/experiments/casee/tools/generate_native_casee.py --dx 2 --steps 48000 --spinup 12000 --sample-dt 2000 --ground-offset-cells 1 --origin-z-offset-m 1.0 --nu-lbm 0.001",
            "expected_artifact": "docs/experiments/casee/native_cases/<run_id>/citylbm_native_case_manifest.json",
            "formal_result_policy": "Only the eventual raw_trilinear 80-probe CSV can be audited as formal official z=2 m.",
            "pass_condition": "Generated case then completed FluidX3D run with casee_probe_time_mean.csv and complete log.",
            "forbidden_claim": common_forbidden,
        },
        {
            "runbook_id": "R006_wall_model_followup_placeholder",
            "stage": "implementation_then_native_run",
            "enabled_now": False,
            "evidence_type": "blocked_until_physical_change_exists",
            "purpose": "Test a wall/roughness/voxelization change aimed at near-wall official z=2 m errors.",
            "trigger_condition": "A code change exists that is justified by wall/probe diagnostics and remains default-off until validated.",
            "command": "TODO after implementation: generate native Case E with the new wall/voxelization option and audit raw_trilinear output.",
            "expected_artifact": "docs/experiments/casee/results/<wall_followup_probe_time_mean.csv>",
            "formal_result_policy": "May inform defaults only if official raw_trilinear metrics improve and Case A smoke regression passes.",
            "pass_condition": "MAE clearly below prior near-20 pp level, R2>0, Pearson>0, n=80 official probes.",
            "forbidden_claim": common_forbidden,
        },
        {
            "runbook_id": "R007_inlet_turbulence_followup_placeholder",
            "stage": "implementation_then_native_run",
            "enabled_now": False,
            "evidence_type": "blocked_until_physical_change_exists",
            "purpose": "Test a full-plane digital-filter inlet turbulence change based on AF_caseE z,U,k.",
            "trigger_condition": "A documented inlet turbulence implementation change exists.",
            "command": "TODO after implementation: generate native Case E with revised full-plane inlet turbulence and audit raw_trilinear output.",
            "expected_artifact": "docs/experiments/casee/results/<inlet_followup_probe_time_mean.csv>",
            "formal_result_policy": "Experimental switch unless official metric improvement is stable.",
            "pass_condition": "Official raw_trilinear metric improves without relying on diagnostic sampling or z-offset substitution.",
            "forbidden_claim": common_forbidden,
        },
        {
            "runbook_id": "R008_dx1_feasibility_or_generation",
            "stage": "high_resolution_followup",
            "enabled_now": (not gpu_blocked) and dx1_headroom_ok,
            "evidence_type": "blocked_until_dx1_readiness_passes" if not dx1_headroom_ok else "newly_run_when_executed",
            "purpose": "Prepare a dx=1 m official follow-up only if memory/runtime evidence is acceptable.",
            "trigger_condition": "GPU ready, dx1 readiness audit memory_headroom_ok=true, and user confirms a dry allocation/full run.",
            "command": "python docs/experiments/casee/tools/generate_native_casee.py --dx 1 --steps 48000 --spinup 12000 --sample-dt 4000 --ground-offset-cells 1 --origin-z-offset-m 0.5 --nu-lbm 0.001",
            "expected_artifact": "docs/experiments/casee/native_cases/<dx1_run_id>/citylbm_native_case_manifest.json",
            "formal_result_policy": "No mesh-independence claim until completed dx1 metrics support the trend.",
            "pass_condition": "Readiness audit passes, then completed dx=1 official z=2 m raw_trilinear run with all 80 probes and complete log.",
            "forbidden_claim": "Do not claim mesh independence from generated case files or dx=2/3 diagnostics.",
        },
        {
            "runbook_id": "R009_postrun_official_audit",
            "stage": "postrun_audit",
            "enabled_now": not metric_blocked,
            "evidence_type": "newly_run_when_executed",
            "purpose": "Audit any newly completed official z=2 m probe CSV against the release gate.",
            "trigger_condition": "After a complete FluidX3D run writes a new casee_probe_time_mean.csv.",
            "command": "python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_casee_probe_time_mean.csv>",
            "expected_artifact": "docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/casee_validation_report.md",
            "formal_result_policy": "This is the only path that can update official z=2 m metrics.",
            "pass_condition": "release_gate official_z2m_metric_gate=true and all other release checks true before formal tag.",
            "forbidden_claim": "Do not cite an unaudited probe CSV as a paper result.",
        },
    ]
    return rows


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metrics = payload["release_gate_summary"]["metrics"]
    lines = [
        "# Case E Next Experiment Runbook",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Current Official Metric",
        "",
        f"- MAE: {metrics.get('mae_pp')} pp",
        f"- R2: {metrics.get('r2')}",
        f"- Pearson: {metrics.get('pearson')}",
        f"- Formal release allowed: {payload['release_gate_summary']['formal_release_allowed']}",
        f"- Recommended tag: `{payload['release_gate_summary']['recommended_tag']}`",
        "",
        "## Command Matrix",
        "",
        "| id | stage | enabled now | purpose | command |",
        "|---|---|---:|---|---|",
    ]
    for row in payload["commands"]:
        lines.append(
            f"| `{row['runbook_id']}` | {row['stage']} | {row['enabled_now']} | "
            f"{row['purpose']} | `{row['command']}` |"
        )
    lines += [
        "",
        "## Formal Result Policy",
        "",
    ]
    for row in payload["commands"]:
        lines += [
            f"### {row['runbook_id']}",
            "",
            f"- Trigger: {row['trigger_condition']}",
            f"- Expected artifact: `{row['expected_artifact']}`",
            f"- Formal result policy: {row['formal_result_policy']}",
            f"- Pass condition: {row['pass_condition']}",
            f"- Forbidden claim: {row['forbidden_claim']}",
            "",
        ]
    lines += [
        "## Boundary",
        "",
        "This runbook is a command and policy matrix for future work. It does not add a new solver run, does not change the official z=2 m metric, and does not allow a formal v0.4.0 tag.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--blockers", type=Path, default=RESULTS_DIR / "casee_remaining_blockers.json")
    parser.add_argument("--dx1-readiness", type=Path, default=RESULTS_DIR / "casee_dx1_readiness_audit.json")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_next_experiment_runbook.json")
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_next_experiment_runbook.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_next_experiment_runbook.md")
    args = parser.parse_args()

    release_gate = read_json(args.release_gate)
    blockers = read_json(args.blockers)
    dx1_readiness = read_json(args.dx1_readiness)
    rows = command_rows(release_gate, blockers, dx1_readiness)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "blocked_followup_runbook; not_accuracy_evidence",
        "release_gate_summary": {
            "formal_release_allowed": release_gate.get("formal_release_allowed"),
            "recommended_tag": release_gate.get("recommended_tag"),
            "metrics": release_gate.get("metrics", {}),
            "checks": release_gate.get("checks", {}),
        },
        "commands": rows,
        "blocked_command_count": sum(1 for row in rows if not bool(row["enabled_now"])),
        "boundary": "Future-run command matrix only; no new CFD accuracy evidence.",
    }
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, payload)
    print(json.dumps({"commands": len(rows), "blocked_command_count": payload["blocked_command_count"], "out_json": str(args.out_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
