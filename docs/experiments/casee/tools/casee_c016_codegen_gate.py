#!/usr/bin/env python3
"""Audit default-off native Case E C016 residual-target follow-up code generation."""

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
LEAKAGE_GUARD = RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json"
OUT_JSON = RESULTS_DIR / "casee_c016_codegen_gate.json"
OUT_CSV = RESULTS_DIR / "casee_c016_codegen_gate.csv"
OUT_MD = RESULTS_DIR / "casee_c016_codegen_gate.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def build_payload() -> Dict[str, Any]:
    generator = read_text(GENERATOR)
    sweep = read_text(CANDIDATE_SWEEP)
    runbook = read_text(RUNBOOK)
    leakage_guard = read_json(LEAKAGE_GUARD)
    checks = {
        "generator_exists": GENERATOR.exists(),
        "residual_target_cli_default_off": "--residual-target-mode" in generator
        and 'choices=("none", "c014_channel_response")' in generator
        and 'default="none"' in generator,
        "residual_target_scale_default_zero": "--residual-target-scale" in generator and "default=0.0" in generator,
        "setup_contains_pre_registered_channel_response": "float residual_channel_factor" in generator
        and "high_speed_corridor" in generator
        and "sheltered_corner" in generator,
        "setup_uses_coordinate_regions_not_probe_residuals": "residual_channel_factor(x_m, y_m, z_m)" in generator
        and "diagnostic_residual_target_uses_rs_casee_targets_for_fitting" in generator
        and "diagnostic_residual_target_pre_registered_regions" in generator,
        "manifest_records_c016_claim_boundary": '"diagnostic_residual_target_mode"' in generator
        and '"diagnostic_residual_target_uses_rs_casee_targets_for_fitting": False' in generator
        and "Residual-target follow-ups must not fit RS_caseE official probe targets" in generator,
        "manifest_blocks_default_accuracy_promotion": '"diagnostic_residual_target_allowed_as_default_accuracy_model": False' in generator,
        "leakage_guard_passed": leakage_guard.get("guard_passed") is True
        and leakage_guard.get("formal_accuracy_claim_supported") is False,
        "candidate_no_longer_blocks_on_missing_implementation": "residual_targeted_wall_inlet_channel_response_not_implemented" not in sweep,
        "candidate_command_uses_residual_target": "--residual-target-mode c014_channel_response" in sweep
        and "--residual-target-scale 1.00" in sweep,
        "runbook_no_longer_uses_c016_todo": "R010_c016_residual_channel_response_followup" in runbook
        and "TODO after implementation: generate official z=2 m raw_trilinear Case E" not in runbook,
        "runbook_command_uses_residual_target": "--residual-target-mode c014_channel_response" in runbook
        and "--residual-target-scale 1.00" in runbook,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_c016_codegen; blocked official run" if passed else "blocked_c016_codegen",
        "c016_codegen_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "checks": checks,
        "source_paths": [rel(GENERATOR), rel(CANDIDATE_SWEEP), rel(RUNBOOK), rel(LEAKAGE_GUARD)],
        "boundary": (
            "This gate verifies a default-off C016 residual-target native code-generation path "
            "using pre-registered coordinate regions. It does not run FluidX3D, update official "
            "metrics, fit RS_caseE probe residuals, promote residual-target settings to defaults, "
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
        "# Case E C016 Codegen Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['c016_codegen_gate_passed']}",
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
    lines += ["", "## Boundary", "", payload["boundary"]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["checks"])
    write_markdown(OUT_MD, payload)
    print(json.dumps({"c016_codegen_gate_passed": payload["c016_codegen_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if payload["c016_codegen_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
