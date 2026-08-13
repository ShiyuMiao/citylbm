#!/usr/bin/env python3
"""Audit default-off native Case E inlet-turbulence follow-up code generation."""

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
OUT_JSON = RESULTS_DIR / "casee_inlet_followup_codegen_gate.json"
OUT_CSV = RESULTS_DIR / "casee_inlet_followup_codegen_gate.csv"
OUT_MD = RESULTS_DIR / "casee_inlet_followup_codegen_gate.md"


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
        "inlet_mode_cli_default_off": "--inlet-turbulence-mode" in generator
        and 'choices=("none", "k_synthetic_fullplane")' in generator
        and 'default="none"' in generator,
        "inlet_scale_default_zero": "--inlet-turbulence-scale" in generator and "default=0.0" in generator,
        "setup_reads_af_u_and_k": "AF_U_RATIO" in generator
        and "AF_SIGMA_RATIO" in generator
        and "math.sqrt(max(0.0, 2.0 * p[\"k\"] / 3.0)) / UREF" in generator,
        "setup_contains_fullplane_inlet_reapplication": "void apply_casee_inlet" in generator
        and "parallel_for(lbm.get_N()" in generator
        and "lbm.u.write_to_device();" in generator,
        "setup_reapplies_inlet_each_sample_window": "apply_casee_inlet(lbm, Nx, Ny, Nz, (uint)lbm.get_t());" in generator
        and "while(lbm.get_t()<CASEE_STEPS)" in generator,
        "setup_uses_official_raw_probe_csv": "casee_probe_time_mean.csv" in generator
        and "official_velocity_ratio,predicted_velocity_ratio" in generator,
        "manifest_records_inlet_mode": '"inlet_turbulence_mode"' in generator
        and '"inlet_turbulence_scale"' in generator
        and '"inlet_turbulence_uses_af_k"' in generator,
        "manifest_blocks_formal_claim": "diagnostic_inlet_turbulence" in generator
        and "formal accuracy or default-promotion claims" in generator,
        "candidate_no_longer_requires_inlet_implementation": "C008_C015_full_plane_inlet_turbulence_sgs_sweep" in sweep
        and "candidate_class=\"default_off_inlet_followup_codegen\"" in sweep,
        "candidate_command_uses_inlet_followup": "--inlet-turbulence-mode k_synthetic_fullplane" in sweep
        and "--inlet-turbulence-scale 2.00" in sweep
        and "--no-subgrid" in sweep,
        "runbook_no_longer_uses_inlet_placeholder_todo": "R007_inlet_turbulence_followup" in runbook
        and "R007_inlet_turbulence_followup_placeholder" not in runbook
        and "TODO after implementation: generate native Case E with revised full-plane inlet turbulence" not in runbook,
        "runbook_command_uses_inlet_followup": "--inlet-turbulence-mode k_synthetic_fullplane" in runbook
        and "--inlet-turbulence-scale 2.00" in runbook
        and "--no-subgrid" in runbook,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_inlet_followup_codegen; blocked official run" if passed else "blocked_inlet_followup_codegen",
        "inlet_followup_codegen_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "checks": checks,
        "source_paths": [rel(GENERATOR), rel(CANDIDATE_SWEEP), rel(RUNBOOK)],
        "boundary": (
            "This gate verifies the default-off native AF_caseE-k full-plane inlet-turbulence "
            "follow-up generation path. It does not run FluidX3D, update official metrics, "
            "promote inlet/SGS settings to defaults, or permit formal v0.4.0."
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
        "# Case E Inlet Follow-up Codegen Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['inlet_followup_codegen_gate_passed']}",
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
    print(
        json.dumps(
            {
                "inlet_followup_codegen_gate_passed": payload["inlet_followup_codegen_gate_passed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["inlet_followup_codegen_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
