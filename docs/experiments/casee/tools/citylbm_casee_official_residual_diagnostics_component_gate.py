from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "CityLBM/src/Components/Results/CaseEOfficialResidualDiagnosticsComponent.cs"
OUT_JSON = ROOT / "docs/experiments/casee/results/citylbm_casee_official_residual_diagnostics_component_gate.json"
OUT_CSV = ROOT / "docs/experiments/casee/results/citylbm_casee_official_residual_diagnostics_component_gate.csv"
OUT_MD = ROOT / "docs/experiments/casee/results/citylbm_casee_official_residual_diagnostics_component_gate.md"


REQUIRED_MARKERS = {
    "component_class": "CaseEOfficialResidualDiagnosticsComponent",
    "component_name": "Case E Official Residual Diagnostics",
    "official_height": "OfficialHeightM = 2.0",
    "probe_count": "RequiredProbeCount = 80",
    "case_ac": 'RequiredCase = "ac"',
    "wind_direction_n": 'RequiredWindDirection = "N"',
    "raw_trilinear": 'RequiredSamplingMode = "raw_trilinear"',
    "official_column": "official_velocity_ratio",
    "predicted_column": "predicted_velocity_ratio",
    "top_residual_rows": "Top Residual Rows",
    "group_rows": "Group Rows",
    "risk_rows": "Risk Rows",
    "low_group": "low_official_speed",
    "mid_group": "mid_official_speed",
    "high_group": "high_official_speed",
    "under_fraction": "under_fraction",
    "formal_false": "formal_release_allowed: false",
    "no_metric_improvement": "residual_diagnostics_do_not_improve_metrics=true",
    "no_calibration": "posthoc_calibration_not_validation=true",
    "no_diagnostic_sampling_formal": "diagnostic_sampling_not_formal=true",
    "release_boundary": "permit formal v0.4.0",
    "guid": "9BAEAB1F-6F24-4679-B940-D4E97DE0D54B",
}


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8") if SOURCE.exists() else ""
    marker_checks = {name: marker in text for name, marker in REQUIRED_MARKERS.items()}
    output_checks = {
        "has_report_output": 'AddTextParameter("Report"' in text,
        "has_top_output": 'AddTextParameter("Top Residual Rows"' in text,
        "has_group_output": 'AddTextParameter("Group Rows"' in text,
        "has_risk_output": 'AddTextParameter("Risk Rows"' in text,
        "has_formal_diagnostic_ready_output": 'AddBooleanParameter("Formal Diagnostic Ready"' in text,
        "has_claim_readiness_output": 'AddTextParameter("Claim Readiness"' in text,
    }
    protocol_checks = {
        "checks_ac_case": "official_case_check=\" + officialCase" in text,
        "checks_n_direction": "wind_direction_check=\" + officialWindDirection" in text,
        "checks_z2m": "height_2m_check=\" + officialHeight" in text,
        "checks_raw_trilinear": "sampling_raw_trilinear_check=\" + officialSampling" in text,
        "checks_probe_ids": "probe_id_check=\" + idsOneToEighty" in text,
        "requires_80_rows": "Expected 80 official ac+N probe rows" in text,
    }
    checks = {
        "source_exists": SOURCE.exists(),
        **{f"marker_{name}": value for name, value in marker_checks.items()},
        **output_checks,
        **protocol_checks,
    }
    passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_software_residual_diagnostics_with_release_boundary",
        "casee_official_residual_diagnostics_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "source_path": str(SOURCE.relative_to(ROOT)),
        "checks": checks,
        "boundary": (
            "This gate audits a Grasshopper residual-diagnostics component. It checks official "
            "protocol constants, top residual rows, group summaries, and claim boundaries only; "
            "it does not run CFD, improve Case E official z=2 m metrics, prove Rhino loaded the GHA, "
            "or permit formal v0.4.0."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["check", "passed"])
        writer.writeheader()
        for name, value in checks.items():
            writer.writerow({"check": name, "passed": value})
    OUT_MD.write_text(
        "# CityLBM Case E Official Residual Diagnostics Component Gate\n\n"
        f"- gate_passed: {str(passed).lower()}\n"
        "- evidence_type: newly_run\n"
        "- formal_accuracy_claim_supported: false\n"
        "- formal_release_allowed: false\n"
        "- default_setting_allowed: false\n"
        "- boundary: software residual-diagnostics evidence only; no CFD run or metric improvement.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
