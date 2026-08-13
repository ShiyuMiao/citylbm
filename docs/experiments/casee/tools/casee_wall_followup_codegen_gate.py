#!/usr/bin/env python3
"""Audit default-off native Case E wall/ground follow-up code generation."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
GENERATOR = CASE_DIR / "tools" / "generate_native_casee.py"
CANDIDATE_SWEEP = CASE_DIR / "tools" / "casee_candidate_sweep_plan.py"
RUNBOOK = CASE_DIR / "tools" / "casee_next_experiment_runbook.py"
OUT_JSON = RESULTS_DIR / "casee_wall_followup_codegen_gate.json"
OUT_CSV = RESULTS_DIR / "casee_wall_followup_codegen_gate.csv"
OUT_MD = RESULTS_DIR / "casee_wall_followup_codegen_gate.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def build_payload() -> Dict[str, Any]:
    generator = read_text(GENERATOR)
    sweep = read_text(CANDIDATE_SWEEP)
    runbook = read_text(RUNBOOK)
    checks = {
        "generator_exists": GENERATOR.exists(),
        "wall_model_cli_default_off": '--wall-model' in generator
        and 'choices=("none", "voxel_dilation", "ground_damping")' in generator
        and 'default="none"' in generator,
        "wall_dilation_default_zero": '--wall-dilation-cells' in generator and 'default=0' in generator,
        "wall_damping_default_zero": '--wall-damping-factor' in generator and 'default=0.0' in generator,
        "setup_contains_wall_followup_function": "void apply_casee_wall_followup" in generator,
        "setup_supports_voxel_dilation": "CASEE_DIAGNOSTIC_WALL_MODEL==1" in generator
        and "CASEE_WALL_DILATION_CELLS" in generator,
        "setup_supports_ground_damping": "CASEE_DIAGNOSTIC_WALL_MODEL==2" in generator
        and "CASEE_WALL_DAMPING_FACTOR" in generator,
        "setup_calls_wall_followup_after_voxelization": "lbm.voxelize_mesh_on_device(mesh, TYPE_S);" in generator
        and "apply_casee_wall_followup(lbm, Nx, Ny, Nz);" in generator,
        "manifest_records_default_safety": "diagnostic_wall_followup_default_safe" in generator,
        "manifest_blocks_default_accuracy_promotion": "diagnostic_wall_followup_allowed_as_default_accuracy_model" in generator
        and "False" in generator,
        "claim_boundary_blocks_accuracy_claim": "cannot support formal accuracy or default-promotion claims" in generator,
        "candidate_no_longer_blocks_on_missing_implementation": "physical_wall_model_not_implemented" not in sweep,
        "candidate_command_uses_wall_model": "--wall-model voxel_dilation" in sweep
        or "--wall-model ground_damping" in sweep,
        "runbook_no_longer_uses_wall_placeholder_todo": "R006_wall_model_followup" in runbook
        and "R006_wall_model_followup_placeholder" not in runbook
        and "generate native Case E with the new wall/voxelization option" not in runbook,
        "runbook_command_uses_wall_model": "--wall-model voxel_dilation" in runbook
        or "--wall-model ground_damping" in runbook,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_wall_followup_codegen; blocked official run" if passed else "blocked_wall_followup_codegen",
        "wall_followup_codegen_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "checks": checks,
        "source_paths": [rel(GENERATOR), rel(CANDIDATE_SWEEP), rel(RUNBOOK)],
        "boundary": (
            "This gate verifies a default-off native wall/ground follow-up code-generation path. "
            "It does not run FluidX3D, update official metrics, promote wall settings to defaults, "
            "or permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, checks: Dict[str, bool]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed"])
        writer.writeheader()
        for key, value in checks.items():
            writer.writerow({"check": key, "passed": value})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Wall Follow-up Codegen Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['wall_followup_codegen_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
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
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["checks"])
    write_markdown(OUT_MD, payload)
    print(json.dumps({"wall_followup_codegen_gate_passed": payload["wall_followup_codegen_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if payload["wall_followup_codegen_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
