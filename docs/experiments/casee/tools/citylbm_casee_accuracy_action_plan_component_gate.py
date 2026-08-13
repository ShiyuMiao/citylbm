#!/usr/bin/env python3
"""Audit the Grasshopper Case E Accuracy Action Plan component source."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "CaseEAccuracyActionPlanComponent.cs"
OUT_JSON = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_component_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_component_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_casee_accuracy_action_plan_component_gate.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def build_payload() -> Dict[str, Any]:
    text = read_text(COMPONENT)
    checks = {
        "component_source_exists": COMPONENT.exists(),
        "component_class_present": "CaseEAccuracyActionPlanComponent" in text,
        "grasshopper_component_name_present": "Case E Accuracy Action Plan" in text,
        "outputs_claim_readiness": 'AddTextParameter("Claim Readiness"' in text,
        "outputs_formal_release_allowed": 'AddBooleanParameter("Formal Release Allowed"' in text and "DA.SetData(2, false)" in text,
        "outputs_metric_gaps": 'AddNumberParameter("MAE Gap pp"' in text and 'AddNumberParameter("R2 Gap"' in text,
        "outputs_next_actions_and_boundary": 'AddTextParameter("Next Actions"' in text and 'AddTextParameter("Boundary"' in text,
        "records_official_protocol": "case: ac" in text and "wind_direction: N" in text and "OfficialProbeCount = 80" in text,
        "records_official_sampling_height": 'OfficialSamplingMode = "raw_trilinear"' in text and "OfficialHeightM = 2.0" in text,
        "records_current_official_metrics": "21.111408125" in text and "-2.006330362229977" in text and "0.11575649438573923" in text,
        "records_metric_thresholds": "MaeThresholdPp = 15.0" in text and "R2Threshold = 0.0" in text and "PearsonThreshold = 0.0" in text,
        "records_ordered_action_ids": all(action_id in text for action_id in ["A001", "A002", "A003", "A004", "A005", "A006", "A007", "A008"]),
        "records_official_followup_actions": "wall-model official follow-up" in text
        and "AF-k/no-SGS inlet official follow-up" in text
        and "C016 channel-response follow-up" in text,
        "records_postrun_audit_policy": "casee_audit.py" in text and "case=ac, Wind_direction=N, z=2 m, 80 probes, raw_trilinear" in text,
        "blocks_forbidden_claims": "predictive accuracy" in text
        and "mesh independence" in text
        and "LES improvement" in text
        and "formal v0.4.0" in text
        and "post-hoc affine" in text,
        "blocks_default_promotion": "default_setting_allowed: false" in text,
        "component_guid_present": "862C4BA3-B4EC-4E33-88CA-0F7345708B68" in text,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_casee_accuracy_action_plan_component" if passed else "blocked_casee_accuracy_action_plan_component",
        "casee_accuracy_action_plan_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "component_source_path": rel(COMPONENT),
        "checks": checks,
        "boundary": (
            "This gate checks that CityLBM exposes the current Case E accuracy gap and ordered next actions "
            "inside Grasshopper while keeping formal v0.4.0 and default promotion blocked. It is software "
            "workflow evidence only; it does not run CFD or improve official z=2 m metrics."
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
        "# CityLBM Case E Accuracy Action Plan Component Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['casee_accuracy_action_plan_component_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Default setting allowed: {payload['default_setting_allowed']}",
        f"- Component source: `{payload['component_source_path']}`",
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
                "casee_accuracy_action_plan_component_gate_passed": payload["casee_accuracy_action_plan_component_gate_passed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["casee_accuracy_action_plan_component_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
