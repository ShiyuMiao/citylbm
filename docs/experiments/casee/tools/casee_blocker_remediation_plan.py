#!/usr/bin/env python3
"""Generate a machine-readable remediation plan for blocked Case E release gates."""

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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fieldnames = [
        "blocker_id",
        "status",
        "severity",
        "release_gate_check",
        "evidence_type",
        "source_paths",
        "current_evidence",
        "required_action",
        "verification_command_or_artifact",
        "pass_condition",
        "paper_use",
        "forbidden_claim",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def compact(value: Any, max_len: int = 240) -> str:
    text = str(value or "")
    one_line = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(one_line) > max_len:
        return one_line[: max_len - 3] + "..."
    return one_line


def run_exists(rows: List[Dict[str, str]], run_id: str) -> bool:
    return any(row.get("run_id") == run_id and row.get("status", "").startswith("completed") for row in rows)


def build_blockers(gate: Dict[str, Any], build_chain: Dict[str, Any], matrix: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    checks = gate.get("checks", {})
    metrics = gate.get("metrics", {})
    vs_cpp = build_chain.get("visual_studio_build_tools_2022_cpp", {})
    gpu = build_chain.get("gpu_runtime", {}).get("nvidia_smi", {})
    disk_rows = build_chain.get("disk", [])
    c_free = next((row.get("free_gb") for row in disk_rows if row.get("drive") == "C:\\"), "NA")

    blockers: List[Dict[str, Any]] = [
        {
            "blocker_id": "B001_official_z2m_metric_gate",
            "status": "blocked" if not checks.get("official_z2m_metric_gate") else "ready",
            "severity": "critical",
            "release_gate_check": "official_z2m_metric_gate",
            "evidence_type": "newly_run",
            "source_paths": "docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/casee_metrics.csv",
            "current_evidence": (
                f"official z=2 m raw_trilinear n={metrics.get('n')}; "
                f"MAE={fmt(metrics.get('mae_pp'))} pp; R2={fmt(metrics.get('r2'), 6)}; Pearson={fmt(metrics.get('pearson'), 6)}"
            ),
            "required_action": (
                "Run a new official z=2 m raw_trilinear Case E experiment only after a physically defensible change "
                "to wall treatment, inlet turbulence, voxelization, or probe protocol implementation is made."
            ),
            "verification_command_or_artifact": (
                "python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 "
                "--predicted <new_official_casee_probe_time_mean.csv>"
            ),
            "pass_condition": "n=80, height=2 m, sampling=raw_trilinear, MAE clearly below prior near-20 pp level, R2>0, Pearson>0.",
            "paper_use": "Use current value only as negative validation and limitations evidence.",
            "forbidden_claim": "Do not claim predictive accuracy, mesh independence, or LES improvement.",
        },
        {
            "blocker_id": "B002_rhino_new_gha_load",
            "status": "blocked" if not checks.get("rhino_loaded_new_gha") else "ready",
            "severity": "critical",
            "release_gate_check": "rhino_loaded_new_gha",
            "evidence_type": "newly_run",
            "source_paths": "docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/plugin_identity_gate.json",
            "current_evidence": f"rhino_loaded_new_gha={checks.get('rhino_loaded_new_gha')}",
            "required_action": "Load the tracked CityLBM/bin/CityLBM.gha in Rhino/Grasshopper and capture plugin version/hash evidence.",
            "verification_command_or_artifact": (
                "Manual Rhino/Grasshopper load check plus screenshot/log showing CityLBM Version=0.4.0-rc "
                "and matching GHA SHA256."
            ),
            "pass_condition": "Rhino/Grasshopper session demonstrably loads the new tracked GHA, not an old installed copy.",
            "paper_use": "Use only after an independently recorded artifact exists.",
            "forbidden_claim": "Do not state the new plugin was loaded in Rhino until this artifact exists.",
        },
        {
            "blocker_id": "B003_gpu_runtime",
            "status": "blocked" if gpu.get("returncode") not in (0, "0") else "ready",
            "severity": "critical",
            "release_gate_check": "native_fluidx3d_followup_capacity",
            "evidence_type": "newly_run",
            "source_paths": "docs/experiments/casee/results/build_chain_manifest.json; docs/experiments/casee/results/release_gate.json",
            "current_evidence": f"nvidia-smi returncode={gpu.get('returncode')}; stdout={compact(gpu.get('stdout'))}",
            "required_action": "Recover the NVIDIA device/driver before any additional long native FluidX3D validation run.",
            "verification_command_or_artifact": "nvidia-smi",
            "pass_condition": "nvidia-smi returns 0 and reports the target GPU without GPU-lost errors.",
            "paper_use": "Use as an environment blocker statement.",
            "forbidden_claim": "Do not describe the native validation chain as currently ready for new long runs.",
        },
        {
            "blocker_id": "B004_vs_cpp_build_tools",
            "status": str(vs_cpp.get("status", "unknown")),
            "severity": "major",
            "release_gate_check": "native_fluidx3d_build_capacity",
            "evidence_type": "newly_run",
            "source_paths": "docs/experiments/casee/results/build_chain_manifest.json",
            "current_evidence": f"VS C++ status={vs_cpp.get('status')}; C: free={c_free} GB",
            "required_action": "Free enough space on C: or redirect installer cache, approve UAC, and install Visual Studio Build Tools 2022 C++ workload.",
            "verification_command_or_artifact": (
                r'"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * '
                r'-requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath'
            ),
            "pass_condition": "vswhere returns a VC tools installation path and vcvars64.bat/cl.exe are available.",
            "paper_use": "Use as build-chain limitation until ready.",
            "forbidden_claim": "Do not claim the Windows native C++ build chain is complete.",
        },
        {
            "blocker_id": "B005_dx1_high_resolution_run",
            "status": "not_started" if not run_exists(matrix, "casee_native_dx1_official") else "ready",
            "severity": "major",
            "release_gate_check": "mesh_resolution_followup",
            "evidence_type": "preexisting_artifact",
            "source_paths": "docs/experiments/casee/native_fluidx3d_run_matrix.csv; docs/experiments/casee/results/dx1_feasibility_estimate.md",
            "current_evidence": "Only dx=1 m feasibility exists; no official dx=1 m FluidX3D run is recorded.",
            "required_action": "After GPU recovery, decide whether dx=1 m is feasible and schedule only if memory/runtime estimates are acceptable.",
            "verification_command_or_artifact": "docs/experiments/casee/results/<dx1_run_log>; docs/experiments/casee/results/<dx1_probe_time_mean.csv>",
            "pass_condition": "Completed official z=2 m dx=1 m run with all 80 raw_trilinear probe predictions and complete log.",
            "paper_use": "Use current state only as future-work planning.",
            "forbidden_claim": "Do not claim mesh independence from dx=2/3 diagnostics.",
        },
    ]
    return blockers


def next_experiments() -> List[Dict[str, Any]]:
    return [
        {
            "priority": 1,
            "experiment_id": "casee_wall_model_followup",
            "trigger_condition": "GPU recovered and a physically defensible wall/roughness/voxelization implementation change exists.",
            "formal_output": "official z=2 m raw_trilinear 80-probe CSV",
            "diagnostic_outputs": "near-wall risk groups, probe-mode comparison, residual plots",
            "default_policy": "Promote to CityLBM default only if official raw_trilinear metric improves and survives Case A smoke regression.",
        },
        {
            "priority": 2,
            "experiment_id": "casee_inlet_turbulence_followup",
            "trigger_condition": "Full-plane digital-filter inlet parameters are changed from documented AF_caseE z,U,k evidence.",
            "formal_output": "official z=2 m raw_trilinear 80-probe CSV",
            "diagnostic_outputs": "inlet profile audit, turbulence audit, residual stratification",
            "default_policy": "Keep as experimental switch unless official metric improvement is stable.",
        },
        {
            "priority": 3,
            "experiment_id": "casee_dx1_feasibility_or_run",
            "trigger_condition": "GPU runtime ready and memory/runtime estimate is acceptable.",
            "formal_output": "dx=1 m official z=2 m raw_trilinear run if feasible",
            "diagnostic_outputs": "runtime, memory, probe risk, metric comparison against dx=2/3",
            "default_policy": "Do not claim mesh independence until the metric trend supports it.",
        },
    ]


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    gate = payload["release_gate_summary"]
    metrics = gate["metrics"]
    lines = [
        "# Case E Remaining Blockers And Remediation Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Formal v0.4.0 allowed: {gate['formal_release_allowed']}",
        f"- Recommended tag: `{gate['recommended_tag']}`",
        f"- Official z=2 m MAE: {metrics.get('mae_pp')} pp",
        f"- Official z=2 m R2: {metrics.get('r2')}",
        f"- Official z=2 m Pearson: {metrics.get('pearson')}",
        "",
        "## Blockers",
        "",
        "| id | status | severity | release gate | pass condition |",
        "|---|---|---|---|---|",
    ]
    for row in payload["blockers"]:
        lines.append(
            f"| `{row['blocker_id']}` | {row['status']} | {row['severity']} | "
            f"{row['release_gate_check']} | {row['pass_condition']} |"
        )
    lines += [
        "",
        "## Required Actions",
        "",
    ]
    for row in payload["blockers"]:
        lines += [
            f"### {row['blocker_id']}",
            "",
            f"- Current evidence: {row['current_evidence']}",
            f"- Required action: {row['required_action']}",
            f"- Verification: `{row['verification_command_or_artifact']}`",
            f"- Paper use: {row['paper_use']}",
            f"- Forbidden claim: {row['forbidden_claim']}",
            "",
        ]
    lines += [
        "## Next Experiment Queue",
        "",
        "| priority | experiment | trigger | formal output | default policy |",
        "|---:|---|---|---|---|",
    ]
    for row in payload["next_experiments"]:
        lines.append(
            f"| {row['priority']} | `{row['experiment_id']}` | {row['trigger_condition']} | "
            f"{row['formal_output']} | {row['default_policy']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This plan is operational evidence for remaining work. It does not add a new CFD run, does not improve the official z=2 m metric, and does not allow a formal v0.4.0 tag.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--build-chain", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    parser.add_argument("--run-matrix", type=Path, default=CASE_DIR / "native_fluidx3d_run_matrix.csv")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_remaining_blockers.json")
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_remaining_blockers.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_remaining_blockers.md")
    args = parser.parse_args()

    gate = read_json(args.release_gate)
    build_chain = read_json(args.build_chain)
    matrix = read_csv(args.run_matrix)
    blockers = build_blockers(gate, build_chain, matrix)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "blocked_followup_plan; paper_ready_limitations_support",
        "release_gate_summary": {
            "formal_release_allowed": gate.get("formal_release_allowed"),
            "recommended_tag": gate.get("recommended_tag"),
            "metrics": gate.get("metrics", {}),
            "checks": gate.get("checks", {}),
        },
        "blockers": blockers,
        "next_experiments": next_experiments(),
        "boundary": "Operational remediation plan only; not accuracy evidence.",
    }
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.out_csv, blockers)
    write_markdown(args.out_md, payload)
    print(json.dumps({"blockers": len(blockers), "out_json": str(args.out_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
