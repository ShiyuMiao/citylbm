#!/usr/bin/env python3
"""Preflight runbook native case-generation commands without running FluidX3D."""

from __future__ import annotations

import csv
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
NATIVE_DIR = CASE_DIR / "native_cases"
RUNBOOK = RESULTS_DIR / "casee_next_experiment_runbook.json"
GENERATOR = CASE_DIR / "tools" / "generate_native_casee.py"
OUT_JSON = RESULTS_DIR / "casee_runbook_codegen_preflight.json"
OUT_CSV = RESULTS_DIR / "casee_runbook_codegen_preflight.csv"
OUT_MD = RESULTS_DIR / "casee_runbook_codegen_preflight.md"

TARGET_RUNBOOK_IDS = {
    "R005_official_dx2_zcenter_replicate",
    "R006_wall_model_followup",
    "R007_inlet_turbulence_followup",
    "R008_dx1_feasibility_or_generation",
    "R010_c016_residual_channel_response_followup",
}

RUNBOOK_SUFFIXES = {
    "R005_official_dx2_zcenter_replicate": "pf_R005",
    "R006_wall_model_followup": "pf_R006",
    "R007_inlet_turbulence_followup": "pf_R007",
    "R008_dx1_feasibility_or_generation": "pf_R008",
    "R010_c016_residual_channel_response_followup": "pf_R010",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rmtree(path: Path, expected_suffix: str) -> None:
    resolved = path.resolve()
    native_root = NATIVE_DIR.resolve()
    if native_root == resolved or native_root not in resolved.parents:
        raise RuntimeError(f"Unsafe cleanup target: {resolved}")
    if not resolved.name.endswith(expected_suffix):
        raise RuntimeError(f"Refusing cleanup without expected preflight suffix {expected_suffix}: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def parse_generator_args(command: str) -> List[str]:
    parts = shlex.split(command, posix=False)
    try:
        generator_index = next(i for i, part in enumerate(parts) if part.endswith("generate_native_casee.py"))
    except StopIteration as exc:
        raise ValueError(f"Not a generate_native_casee.py command: {command}") from exc
    args = parts[generator_index + 1 :]
    forbidden = {"--deploy", "--fluidx3d-root"}
    if any(part in forbidden for part in args):
        raise ValueError(f"Runbook preflight refuses deploy-capable command: {command}")
    return args


def load_manifest(case_dir: Path) -> Dict[str, Any]:
    manifest_path = case_dir / "citylbm_native_case_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def manifest_expectations(runbook_id: str, manifest: Dict[str, Any]) -> Dict[str, bool]:
    common = {
        "official_protocol": manifest.get("validation_height_m") == 2.0
        and manifest.get("probe_count") == 80
        and manifest.get("formal_sampling_mode") == "raw_trilinear",
        "claim_boundary_blocks_accuracy": "cannot support formal accuracy" in str(manifest.get("claim_boundary", "")),
        "no_default_promoted_diagnostics": manifest.get("diagnostic_inlet_turbulence_allowed_as_default_accuracy_model") is False
        and manifest.get("diagnostic_wall_followup_allowed_as_default_accuracy_model") is False
        and manifest.get("diagnostic_residual_target_allowed_as_default_accuracy_model") is False,
    }
    if runbook_id == "R005_official_dx2_zcenter_replicate":
        common.update(
            {
                "dx2_zcenter": manifest.get("dx_m") == 2.0 and manifest.get("origin_z_offset_m") == 1.0,
                "baseline_diagnostics_off": manifest.get("inlet_turbulence_mode") == "none"
                and manifest.get("diagnostic_wall_model") == "none"
                and manifest.get("diagnostic_residual_target_mode") == "none",
            }
        )
    elif runbook_id == "R006_wall_model_followup":
        common.update(
            {
                "wall_voxel_dilation": manifest.get("diagnostic_wall_model") == "voxel_dilation"
                and manifest.get("diagnostic_wall_dilation_cells") == 1,
                "wall_not_default_safe": manifest.get("diagnostic_wall_followup_default_safe") is False,
            }
        )
    elif runbook_id == "R007_inlet_turbulence_followup":
        common.update(
            {
                "afk_inlet_nosgs": manifest.get("inlet_turbulence_mode") == "k_synthetic_fullplane"
                and manifest.get("inlet_turbulence_scale") == 2.0
                and manifest.get("subgrid_enabled") is False,
                "inlet_not_default_safe": manifest.get("diagnostic_inlet_turbulence_default_safe") is False,
            }
        )
    elif runbook_id == "R008_dx1_feasibility_or_generation":
        common.update(
            {
                "dx1_manifest": manifest.get("dx_m") == 1.0
                and manifest.get("origin_z_offset_m") == 0.5,
                "mesh_independence_not_claimed": manifest.get("evidence_boundary") == "generated case only until FluidX3D run completes",
            }
        )
    elif runbook_id == "R010_c016_residual_channel_response_followup":
        common.update(
            {
                "c016_residual_target": manifest.get("diagnostic_residual_target_mode") == "c014_channel_response"
                and manifest.get("diagnostic_residual_target_scale") == 1.0
                and manifest.get("diagnostic_residual_target_uses_rs_casee_targets_for_fitting") is False,
                "c016_regions_registered": manifest.get("diagnostic_residual_target_pre_registered_regions")
                == ["high_speed_corridor", "sheltered_corner"],
            }
        )
    return common


def run_preflight(row: Dict[str, Any]) -> Dict[str, Any]:
    runbook_id = str(row.get("runbook_id", ""))
    command = str(row.get("command", ""))
    try:
        args = parse_generator_args(command)
    except ValueError as exc:
        return {
            "runbook_id": runbook_id,
            "passed": False,
            "claim_readiness": "blocked_runbook_codegen_preflight",
            "command": command,
            "error": str(exc),
            "checks": {"command_is_native_codegen": False},
        }
    suffix = RUNBOOK_SUFFIXES.get(runbook_id, "pf_" + "".join(ch if ch.isalnum() else "_" for ch in runbook_id).strip("_")[:12])
    cmd = [sys.executable, str(GENERATOR), *args, "--run-id-suffix", suffix]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
    stdout_payload: Dict[str, Any] = {}
    case_dir = Path()
    if proc.stdout.strip():
        try:
            stdout_payload = json.loads(proc.stdout)
            case_dir = Path(stdout_payload.get("case_dir", ""))
        except json.JSONDecodeError:
            stdout_payload = {}
    manifest = load_manifest(case_dir) if str(case_dir) else {}
    generated_files = {
        "setup_cpp": bool((case_dir / "setup.cpp").exists()) if str(case_dir) else False,
        "defines_hpp": bool((case_dir / "defines.hpp").exists()) if str(case_dir) else False,
        "buildings_stl": bool((case_dir / "buildings.stl").exists()) if str(case_dir) else False,
        "manifest": bool(manifest),
    }
    manifest_path_length = len(str((case_dir / "citylbm_native_case_manifest.json").resolve())) if str(case_dir) else 0
    checks = {
        "command_is_native_codegen": True,
        "process_exit_zero": proc.returncode == 0,
        "manifest_loaded": bool(manifest),
        "generated_required_files": all(generated_files.values()),
        "no_solver_csv_written": not bool((case_dir / "casee_probe_time_mean.csv").exists()) if str(case_dir) else False,
        "windows_path_length_guard": 0 < manifest_path_length < 240,
    }
    checks.update(manifest_expectations(runbook_id, manifest))
    cleanup_done = False
    cleanup_error = ""
    if str(case_dir):
        try:
            safe_rmtree(case_dir, suffix)
            cleanup_done = True
        except Exception as exc:  # noqa: BLE001 - gate reports cleanup failure explicitly.
            cleanup_error = str(exc)
    checks["cleanup_done"] = cleanup_done
    passed = all(checks.values())
    return {
        "runbook_id": runbook_id,
        "evidence_type": "newly_run",
        "claim_readiness": "runbook_codegen_preflight_passed; no_solver_run" if passed else "blocked_runbook_codegen_preflight",
        "command": command,
        "executed_command": " ".join(str(part) for part in cmd),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-1000:],
        "run_id": manifest.get("run_id"),
        "case_dir": str(case_dir),
        "manifest_path_length": manifest_path_length,
        "generated_files": generated_files,
        "checks": checks,
        "passed": passed,
        "cleanup_error": cleanup_error,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "runbook_id",
                "passed",
                "claim_readiness",
                "run_id",
                "manifest_path_length",
                "cleanup_done",
            ],
        )
        writer.writeheader()
        for item in rows:
            writer.writerow(
                {
                    "runbook_id": item["runbook_id"],
                    "passed": item["passed"],
                    "claim_readiness": item["claim_readiness"],
                    "run_id": item.get("run_id", ""),
                    "manifest_path_length": item.get("manifest_path_length", 0),
                    "cleanup_done": (item.get("checks") or {}).get("cleanup_done", False),
                }
            )


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Runbook Codegen Preflight",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['runbook_codegen_preflight_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## Runbook Commands",
        "",
        "| runbook id | passed | manifest path length | cleanup | run id |",
        "|---|---:|---:|---:|---|",
    ]
    for item in payload["rows"]:
        lines.append(
            f"| `{item['runbook_id']}` | {item['passed']} | {item.get('manifest_path_length', 0)} | "
            f"{(item.get('checks') or {}).get('cleanup_done', False)} | `{item.get('run_id', '')}` |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    runbook = read_json(RUNBOOK)
    commands = [
        row
        for row in runbook.get("commands", [])
        if row.get("runbook_id") in TARGET_RUNBOOK_IDS and "generate_native_casee.py" in str(row.get("command", ""))
    ]
    rows = [run_preflight(row) for row in commands]
    covered_ids = {row.get("runbook_id") for row in rows}
    required_ids_present = TARGET_RUNBOOK_IDS.issubset(covered_ids)
    passed = required_ids_present and all(row.get("passed") is True for row in rows)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_runbook_codegen_preflight; no_solver_run" if passed else "blocked_runbook_codegen_preflight",
        "runbook_codegen_preflight_passed": passed,
        "required_runbook_ids_present": required_ids_present,
        "target_runbook_ids": sorted(TARGET_RUNBOOK_IDS),
        "covered_runbook_ids": sorted(covered_ids),
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "rows": rows,
        "source_paths": [rel(RUNBOOK), rel(GENERATOR), rel(Path(__file__))],
        "boundary": (
            "This gate executes only native case-generation commands from the next experiment runbook. "
            "It does not deploy to FluidX3D, does not run the solver, does not create probe CSVs, "
            "does not update official metrics, and does not permit formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"runbook_codegen_preflight_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
