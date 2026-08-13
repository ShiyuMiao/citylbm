#!/usr/bin/env python3
"""Audit the Grasshopper Case E Post-run Audit component source."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "CaseEPostRunAuditComponent.cs"
OUT_JSON = RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.md"


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
        "component_class_present": "CaseEPostRunAuditComponent" in text,
        "grasshopper_component_name_present": "Case E Post-run Audit" in text,
        "outputs_audit_command": 'AddTextParameter("Audit Command"' in text,
        "outputs_claim_readiness": 'AddTextParameter("Claim Readiness"' in text,
        "outputs_ready_gate": 'AddBooleanParameter("Ready For Official Audit"' in text,
        "outputs_formal_result_allowed_false": 'AddBooleanParameter("Formal Result Allowed Now"' in text
        and "DA.SetData(3, false)" in text,
        "outputs_candidate_sha256": 'AddTextParameter("Candidate SHA256"' in text and "SHA256.Create()" in text,
        "requires_official_case_ac_n": 'RequiredCase = "ac"' in text and 'RequiredWindDirection = "N"' in text,
        "requires_raw_trilinear": 'RequiredSamplingMode = "raw_trilinear"' in text,
        "requires_80_probes": "RequiredProbeCount = 80" in text,
        "requires_steps_and_spinup": "MinimumSteps = 48000" in text and "MinimumSpinup = 12000" in text,
        "requires_official_columns": "official_velocity_ratio" in text and "predicted_velocity_ratio" in text and "No." in text,
        "requires_manifest_and_complete_log": "No sidecar manifest JSON" in text and "No complete FluidX3D run log evidence" in text,
        "prints_casee_audit_command": "casee_audit.py" in text and "--release-target" in text and "--predicted" in text,
        "blocks_formal_claims": "does not compute R2" in text
        and "does not improve official AIJ Case E z=2 m metrics" in text
        and "does not permit formal v0.4.0" in text,
        "component_guid_present": "19B94D68-EB71-41C0-B4AB-35DAFECE4079" in text,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_casee_postrun_audit_component" if passed else "blocked_casee_postrun_audit_component",
        "casee_postrun_audit_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "component_source_path": rel(COMPONENT),
        "checks": checks,
        "boundary": (
            "This gate checks the plugin source for a fail-closed Case E post-run audit handoff component. "
            "It is software protocol-control evidence only; it does not run CFD, update official metrics, "
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
        "# CityLBM Case E Post-run Audit Component Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['casee_postrun_audit_component_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
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
    print(json.dumps({"casee_postrun_audit_component_gate_passed": payload["casee_postrun_audit_component_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if payload["casee_postrun_audit_component_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
