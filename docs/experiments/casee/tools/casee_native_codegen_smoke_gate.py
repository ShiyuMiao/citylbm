#!/usr/bin/env python3
"""Run short native Case E code-generation smoke checks without FluidX3D."""

from __future__ import annotations

import csv
import json
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
GENERATOR = CASE_DIR / "tools" / "generate_native_casee.py"
OUT_JSON = RESULTS_DIR / "casee_native_codegen_smoke_gate.json"
OUT_CSV = RESULTS_DIR / "casee_native_codegen_smoke_gate.csv"
OUT_MD = RESULTS_DIR / "casee_native_codegen_smoke_gate.md"


CASES = [
    {
        "case_id": "default_off_baseline",
        "args": [],
        "expected": {
            "subgrid_enabled": True,
            "inlet_turbulence_mode": "none",
            "diagnostic_inlet_turbulence_default_safe": True,
            "diagnostic_wall_followup_default_safe": True,
            "diagnostic_residual_target_default_safe": True,
        },
    },
    {
        "case_id": "inlet_afk_nosgs",
        "args": [
            "--domain-x",
            "1",
            "--domain-y",
            "1",
            "--domain-z",
            "1",
            "--inlet-turbulence-mode",
            "k_synthetic_fullplane",
            "--inlet-turbulence-scale",
            "2.00",
            "--no-subgrid",
        ],
        "expected": {
            "subgrid_enabled": False,
            "inlet_turbulence_mode": "k_synthetic_fullplane",
            "inlet_turbulence_uses_af_k": True,
            "diagnostic_inlet_turbulence_allowed_as_default_accuracy_model": False,
        },
    },
    {
        "case_id": "wall_voxel_dilation",
        "args": [
            "--domain-x",
            "1",
            "--domain-y",
            "1",
            "--domain-z",
            "1",
            "--wall-model",
            "voxel_dilation",
            "--wall-dilation-cells",
            "1",
        ],
        "expected": {
            "diagnostic_wall_model": "voxel_dilation",
            "diagnostic_wall_dilation_cells": 1,
            "diagnostic_wall_followup_default_safe": False,
            "diagnostic_wall_followup_allowed_as_default_accuracy_model": False,
        },
    },
    {
        "case_id": "c016_residual_channel_response",
        "args": [
            "--domain-x",
            "1",
            "--domain-y",
            "1",
            "--domain-z",
            "1",
            "--inlet-turbulence-mode",
            "k_synthetic_fullplane",
            "--inlet-turbulence-scale",
            "2.00",
            "--residual-target-mode",
            "c014_channel_response",
            "--residual-target-scale",
            "1.00",
            "--no-subgrid",
        ],
        "expected": {
            "subgrid_enabled": False,
            "diagnostic_residual_target_mode": "c014_channel_response",
            "diagnostic_residual_target_scale": 1.0,
            "diagnostic_residual_target_default_safe": False,
            "diagnostic_residual_target_allowed_as_default_accuracy_model": False,
            "diagnostic_residual_target_uses_rs_casee_targets_for_fitting": False,
            "diagnostic_residual_target_pre_registered_regions": ["high_speed_corridor", "sheltered_corner"],
        },
    },
]


BASE_ARGS = [
    "--dx",
    "4",
    "--steps",
    "10",
    "--spinup",
    "0",
    "--sample-dt",
    "10",
    "--ground-offset-cells",
    "1",
    "--origin-z-offset-m",
    "2.0",
    "--nu-lbm",
    "0.001",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def safe_rmtree(path: Path) -> None:
    resolved = path.resolve()
    native_root = NATIVE_DIR.resolve()
    if native_root == resolved or native_root not in resolved.parents:
        raise RuntimeError(f"Unsafe cleanup target: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def load_manifest(case_dir: Path) -> Dict[str, Any]:
    manifest_path = case_dir / "citylbm_native_case_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def expected_matches(manifest: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    for key, value in expected.items():
        if manifest.get(key) != value:
            return False
    return True


def run_case(spec: Dict[str, Any]) -> Dict[str, Any]:
    cmd = [sys.executable, str(GENERATOR), *BASE_ARGS, *spec["args"]]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=120)
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
    path_length = len(str((case_dir / "citylbm_native_case_manifest.json").resolve())) if str(case_dir) else 0
    checks = {
        "process_exit_zero": proc.returncode == 0,
        "manifest_loaded": bool(manifest),
        "generated_required_files": all(generated_files.values()),
        "manifest_protocol_official": manifest.get("validation_height_m") == 2.0
        and manifest.get("probe_count") == 80
        and manifest.get("formal_sampling_mode") == "raw_trilinear",
        "expected_manifest_fields_match": expected_matches(manifest, spec["expected"]),
        "claim_boundary_blocks_accuracy": "cannot support formal accuracy" in str(manifest.get("claim_boundary", "")),
        "windows_path_length_guard": 0 < path_length < 240,
    }
    cleanup_done = False
    cleanup_error = ""
    if str(case_dir):
        try:
            safe_rmtree(case_dir)
            cleanup_done = True
        except Exception as exc:  # noqa: BLE001 - gate reports cleanup failure explicitly.
            cleanup_error = str(exc)
    checks["cleanup_done"] = cleanup_done
    return {
        "case_id": spec["case_id"],
        "evidence_type": "newly_run",
        "claim_readiness": "codegen_smoke_passed; no_solver_run" if all(checks.values()) else "blocked_codegen_smoke",
        "command": " ".join(str(part) for part in cmd),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-1000:],
        "run_id": manifest.get("run_id"),
        "case_dir": str(case_dir),
        "manifest_path_length": path_length,
        "generated_files": generated_files,
        "checks": checks,
        "passed": all(checks.values()),
        "cleanup_error": cleanup_error,
    }


def write_csv(path: Path, cases: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "passed",
                "claim_readiness",
                "run_id",
                "manifest_path_length",
                "cleanup_done",
            ],
        )
        writer.writeheader()
        for item in cases:
            writer.writerow(
                {
                    "case_id": item["case_id"],
                    "passed": item["passed"],
                    "claim_readiness": item["claim_readiness"],
                    "run_id": item["run_id"],
                    "manifest_path_length": item["manifest_path_length"],
                    "cleanup_done": item["checks"]["cleanup_done"],
                }
            )


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Native Codegen Smoke Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['native_codegen_smoke_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## Cases",
        "",
        "| case | passed | manifest path length | cleanup | run id |",
        "|---|---:|---:|---:|---|",
    ]
    for item in payload["cases"]:
        lines.append(
            f"| `{item['case_id']}` | {item['passed']} | {item['manifest_path_length']} | "
            f"{item['checks']['cleanup_done']} | `{item['run_id']}` |"
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
    cases = [run_case(spec) for spec in CASES]
    passed = all(item["passed"] for item in cases)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_codegen_smoke; no_solver_run" if passed else "blocked_codegen_smoke",
        "native_codegen_smoke_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "cases": cases,
        "source_paths": [rel(GENERATOR), rel(Path(__file__))],
        "boundary": (
            "This gate runs short native Case E code-generation checks for default, inlet, wall, "
            "and C016 residual-target configurations. It verifies generated manifests and cleanup only. "
            "It does not run FluidX3D, produce probe CSVs, update official metrics, promote diagnostic "
            "settings to defaults, or permit formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, cases)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"native_codegen_smoke_gate_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
