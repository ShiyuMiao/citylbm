#!/usr/bin/env python3
"""Audit the Grasshopper Case E Remediation Plan component source."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "CaseERemediationPlanComponent.cs"
OUT_JSON = RESULTS_DIR / "citylbm_casee_remediation_plan_component_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_casee_remediation_plan_component_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_casee_remediation_plan_component_gate.md"


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
        "component_class_present": "CaseERemediationPlanComponent" in text,
        "grasshopper_component_name_present": "Case E Remediation Plan" in text,
        "outputs_remediation_sections": 'AddTextParameter("Blockers"' in text
        and 'AddTextParameter("Required Actions"' in text
        and 'AddTextParameter("Verification"' in text
        and 'AddTextParameter("Pass Conditions"' in text
        and 'AddTextParameter("Forbidden Claims"' in text
        and 'AddTextParameter("Next Experiments"' in text,
        "formal_release_forced_false": 'AddBooleanParameter("Formal Release Allowed"' in text and "DA.SetData(7, false)" in text,
        "records_official_metric_values": "21.111408125" in text
        and "27.72103208243715" in text
        and "-16.409216" in text
        and "-2.006330362229977" in text
        and "0.11575649438573923" in text,
        "records_official_protocol": "case: ac" in text
        and "wind_direction: N" in text
        and "OfficialProbeCount = 80" in text
        and 'OfficialSamplingMode = "raw_trilinear"' in text
        and "OfficialHeightM = 2.0" in text,
        "records_current_blockers": "B001 official_z2m_metric_gate" in text
        and "B002 rhino_new_gha_load" in text
        and "B003 gpu_runtime" in text
        and "B004 vs_cpp_build_tools" in text
        and "B005 dx1_high_resolution_run" in text,
        "records_verification_commands": "casee_audit.py --release-target v0.4.0" in text
        and "nvidia-smi must return 0" in text
        and "vswhere must find" in text
        and "manual Rhino/Grasshopper manifest" in text,
        "records_pass_conditions": "R2>0" in text
        and "Pearson>0" in text
        and "new tracked GHA" in text
        and "dx=1 m result exists" in text,
        "blocks_forbidden_claims": "Do not claim predictive accuracy" in text
        and "Do not claim mesh independence" in text
        and "Do not claim LES improvement" in text
        and "Do not claim formal v0.4.0 release readiness" in text
        and "post-hoc affine calibration" in text,
        "records_next_experiments": "casee_wall_model_followup" in text
        and "casee_inlet_turbulence_followup" in text
        and "casee_dx1_feasibility_or_run" in text,
        "boundary_blocks_accuracy": "does not run CFD" in text
        and "update metrics" in text
        and "promote defaults" in text
        and "prove Rhino loaded the plugin" in text,
        "component_guid_present": "3F46B886-F94E-492D-9D4F-FA6F170BF1D2" in text,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_casee_remediation_plan_component" if passed else "blocked_casee_remediation_plan_component",
        "casee_remediation_plan_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "component_source_path": rel(COMPONENT),
        "checks": checks,
        "boundary": (
            "This gate checks that CityLBM exposes the current Case E blockers, remediation actions, "
            "verification commands, and forbidden claims inside Grasshopper. It is operational planning "
            "and paper-limitations support only; it does not run CFD, change official metrics, promote "
            "defaults, or permit formal v0.4.0."
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
        "# CityLBM Case E Remediation Plan Component Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['casee_remediation_plan_component_gate_passed']}",
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
                "casee_remediation_plan_component_gate_passed": payload["casee_remediation_plan_component_gate_passed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["casee_remediation_plan_component_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
