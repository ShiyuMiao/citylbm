#!/usr/bin/env python3
"""Audit the Grasshopper Case E Paper Claim Card component source."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "CaseEPaperClaimCardComponent.cs"
OUT_JSON = RESULTS_DIR / "citylbm_casee_paper_claim_card_component_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_casee_paper_claim_card_component_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_casee_paper_claim_card_component_gate.md"


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
        "component_class_present": "CaseEPaperClaimCardComponent" in text,
        "grasshopper_component_name_present": "Case E Paper Claim Card" in text,
        "outputs_paper_claim_sections": 'AddTextParameter("Paper Ready Claims"' in text
        and 'AddTextParameter("Limitations"' in text
        and 'AddTextParameter("Forbidden Claims"' in text
        and 'AddTextParameter("Evidence Paths"' in text,
        "formal_release_forced_false": 'AddBooleanParameter("Formal Release Allowed"' in text and "DA.SetData(5, false)" in text,
        "records_official_metric_values": "21.111408125" in text
        and "27.72103208243715" in text
        and "-2.006330362229977" in text
        and "0.11575649438573923" in text,
        "records_official_protocol": "case: ac" in text
        and "wind_direction: N" in text
        and "OfficialProbeCount = 80" in text
        and 'OfficialSamplingMode = "raw_trilinear"' in text
        and "OfficialHeightM = 2.0" in text,
        "records_paper_ready_negative_validation": "negative-validation result" in text
        and "traceable diagnostic workflow" in text
        and "pre-registered experimental switches" in text,
        "records_limitations": "official z=2 m R2 remains negative" in text
        and "MAE remains above the <15 pp" in text
        and "GPU runtime is currently blocked" in text,
        "blocks_forbidden_claims": "Do not claim predictive accuracy" in text
        and "Do not claim mesh independence" in text
        and "Do not claim LES improvement" in text
        and "Do not claim formal v0.4.0 release readiness" in text
        and "post-hoc affine calibration" in text,
        "records_evidence_paths": "release_gate.json" in text
        and "casee_reproducibility_suite.json" in text
        and "casee_paper_evidence_gate.json" in text
        and "citylbm_software_feedback_matrix.json" in text,
        "boundary_blocks_accuracy": "does not run CFD" in text
        and "update metrics" in text
        and "promote defaults" in text
        and "prove Rhino loaded the plugin" in text,
        "component_guid_present": "BA36730E-EEE4-4DB6-A360-61F889517DF1" in text,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_casee_paper_claim_card_component" if passed else "blocked_casee_paper_claim_card_component",
        "casee_paper_claim_card_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "component_source_path": rel(COMPONENT),
        "checks": checks,
        "boundary": (
            "This gate checks that CityLBM exposes paper-safe Case E claims and limitations inside Grasshopper. "
            "It is paper-writing support evidence only; it does not run CFD, change official metrics, "
            "promote defaults, or permit formal v0.4.0."
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
        "# CityLBM Case E Paper Claim Card Component Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['casee_paper_claim_card_component_gate_passed']}",
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
                "casee_paper_claim_card_component_gate_passed": payload["casee_paper_claim_card_component_gate_passed"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["casee_paper_claim_card_component_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
