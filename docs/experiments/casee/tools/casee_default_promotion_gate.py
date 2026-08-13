#!/usr/bin/env python3
"""Gate whether Case E diagnostic settings may be promoted to CityLBM defaults."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_default_promotion_gate.json"
OUT_CSV = RESULTS_DIR / "casee_default_promotion_gate.csv"
OUT_MD = RESULTS_DIR / "casee_default_promotion_gate.md"


FORMAL_REQUIRED = [
    "official_z2m_metric_gate",
    "casea_smoke_regression_passed",
    "rhino_loaded_new_gha",
    "official_raw_trilinear_only",
    "no_zplus_substitution",
    "no_rs_casee_target_fitting",
    "complete_command_log_csv_figure_trace",
]


DIAGNOSTIC_SETTINGS = [
    {
        "setting_id": "nu_lbm_override",
        "surface": "CityLBM Run Simulation / native generator",
        "control": "nuLBM / --nu-lbm",
        "current_status": "diagnostic_switch",
        "promotion_requires": ["official_z2m_metric_gate", "casea_smoke_regression_passed", "complete_command_log_csv_figure_trace"],
    },
    {
        "setting_id": "z_origin_offset",
        "surface": "CityLBM Run Simulation / native generator",
        "control": "zOff / --origin-z-offset-m",
        "current_status": "diagnostic_switch",
        "promotion_requires": ["official_z2m_metric_gate", "official_raw_trilinear_only", "no_zplus_substitution"],
    },
    {
        "setting_id": "wall_model",
        "surface": "CityLBM Run Simulation / native generator",
        "control": "wallModel / --wall-model",
        "current_status": "default_off_followup",
        "promotion_requires": FORMAL_REQUIRED,
    },
    {
        "setting_id": "roughness_length",
        "surface": "CityLBM Run Simulation",
        "control": "z0Wall",
        "current_status": "default_off_followup",
        "promotion_requires": FORMAL_REQUIRED,
    },
    {
        "setting_id": "inlet_turbulence",
        "surface": "CityLBM Run Simulation / native generator",
        "control": "inletT/inletS / --inlet-turbulence-mode/scale",
        "current_status": "default_off_followup",
        "promotion_requires": FORMAL_REQUIRED,
    },
    {
        "setting_id": "residual_target",
        "surface": "CityLBM Run Simulation / native generator",
        "control": "residT/residS / --residual-target-mode/scale",
        "current_status": "default_off_followup",
        "promotion_requires": FORMAL_REQUIRED,
    },
    {
        "setting_id": "diagnostic_probe_sampling",
        "surface": "Case E preset/native output",
        "control": "nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half",
        "current_status": "diagnostic_only",
        "never_promote": True,
        "promotion_requires": ["official_raw_trilinear_only", "no_zplus_substitution"],
    },
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def build_rows() -> List[Dict[str, Any]]:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    default_policy = read_json(RESULTS_DIR / "casee_default_policy_gate.json")
    c016_guard = read_json(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json")
    runbook_preflight = read_json(RESULTS_DIR / "casee_runbook_codegen_preflight.json")
    paper_gate = read_json(RESULTS_DIR / "casee_paper_evidence_gate.json")
    metrics = release_gate.get("metrics") or {}
    checks = release_gate.get("checks") or {}
    gate_state = {
        "official_z2m_metric_gate": checks.get("official_z2m_metric_gate") is True,
        "casea_smoke_regression_passed": checks.get("casea_smoke_regression_passed") is True,
        "rhino_loaded_new_gha": checks.get("rhino_loaded_new_gha") is True,
        "official_raw_trilinear_only": metrics.get("height_m") == 2.0 and metrics.get("sampling_mode") == "raw_trilinear",
        "no_zplus_substitution": default_policy.get("default_policy_gate_passed") is True,
        "no_rs_casee_target_fitting": c016_guard.get("guard_passed") is True,
        "complete_command_log_csv_figure_trace": paper_gate.get("paper_evidence_gate_passed") is True
        and runbook_preflight.get("runbook_codegen_preflight_passed") is True,
    }
    rows = []
    for item in DIAGNOSTIC_SETTINGS:
        required = list(item["promotion_requires"])
        missing = [key for key in required if gate_state.get(key) is not True]
        if item.get("never_promote") is True:
            missing = sorted(set(missing + ["diagnostic_sampling_never_formal_default"]))
        rows.append(
            {
                **item,
                "evidence_type": "newly_run",
                "promotion_allowed_now": False if missing else True,
                "promotion_blockers": missing,
                "required_gate_count": len(required),
                "passed_required_gate_count": len(required) - len(missing),
                "paper_use": "Use as default-promotion boundary for software implications and limitations.",
                "limitations": "No default promotion while any required gate is missing; generated cases and diagnostic metrics alone are insufficient.",
            }
        )
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "setting_id",
                "surface",
                "control",
                "current_status",
                "evidence_type",
                "promotion_requires",
                "promotion_allowed_now",
                "promotion_blockers",
                "required_gate_count",
                "passed_required_gate_count",
                "paper_use",
                "limitations",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["promotion_requires"] = "; ".join(row["promotion_requires"])
            out["promotion_blockers"] = "; ".join(row["promotion_blockers"])
            out.pop("never_promote", None)
            writer.writerow(out)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Default Promotion Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['default_promotion_gate_passed']}",
        f"- Any diagnostic default promotion allowed: {payload['any_diagnostic_default_promotion_allowed']}",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {payload['formal_release_allowed']}",
        "",
        "## Promotion Rows",
        "",
        "| setting | status | promotion allowed | blockers |",
        "|---|---|---:|---|",
    ]
    for row in payload["rows"]:
        blockers = "; ".join(row["promotion_blockers"])
        lines.append(f"| `{row['setting_id']}` | {row['current_status']} | {row['promotion_allowed_now']} | {blockers} |")
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    any_promotion = any(row["promotion_allowed_now"] for row in rows)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_default_promotion_boundary",
        "default_promotion_gate_passed": not any_promotion,
        "any_diagnostic_default_promotion_allowed": any_promotion,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "rows": rows,
        "source_paths": [
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "casee_default_policy_gate.json"),
            rel(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json"),
            rel(RESULTS_DIR / "casee_runbook_codegen_preflight.json"),
            rel(RESULTS_DIR / "casee_paper_evidence_gate.json"),
        ],
        "boundary": (
            "This gate is a promotion blocker: while official z=2 m accuracy, Case A regression, "
            "Rhino/GHA load, raw-trilinear protocol, no-fitting, and traceability gates are not all satisfied, "
            "diagnostic Case E settings must remain experimental switches. It does not run FluidX3D or update metrics."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"default_promotion_gate_passed": payload["default_promotion_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if payload["default_promotion_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
