from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "CityLBM/src/Components/Results/CaseEOfficialMetricsFromCsvComponent.cs"
OUT_JSON = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_component_gate.json"
OUT_CSV = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_component_gate.csv"
OUT_MD = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_component_gate.md"


REQUIRED_MARKERS = {
    "component_class": "CaseEOfficialMetricsFromCsvComponent",
    "component_name": "Case E Official Metrics From CSV",
    "official_height": "OfficialHeightM = 2.0",
    "probe_count": "RequiredProbeCount = 80",
    "case_ac": 'RequiredCase = "ac"',
    "wind_direction_n": 'RequiredWindDirection = "N"',
    "case_input": 'AddTextParameter(\n                "Case"',
    "wind_direction_input": 'AddTextParameter(\n                "Wind Direction"',
    "raw_trilinear": 'RequiredSamplingMode = "raw_trilinear"',
    "mae_threshold": "MaeThresholdPp = 15.0",
    "r2_threshold": "R2Threshold = 0.0",
    "pearson_threshold": "PearsonThreshold = 0.0",
    "official_column": "official_velocity_ratio",
    "predicted_column": "predicted_velocity_ratio",
    "mae_formula": "mae * 100.0",
    "rmse_formula": "Math.Sqrt",
    "bias_formula": "bias * 100.0",
    "r2_formula": "1.0 - ssRes / ssTot",
    "pearson_formula": "ComputePearson",
    "gate_false_until_release": "Formal Release Allowed",
    "formal_false": "formal_release_allowed=false",
    "diagnostic_forbidden": "z_plus_half",
    "guid": "6189C8B7-3E79-4C0B-BC1D-4E85D7E90493",
}


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8") if SOURCE.exists() else ""
    marker_checks = {name: marker in text for name, marker in REQUIRED_MARKERS.items()}
    output_checks = {
        "has_report_output": 'AddTextParameter("Report"' in text,
        "has_metric_rows_output": 'AddTextParameter("Metric Rows"' in text,
        "has_gate_checks_output": 'AddTextParameter("Gate Checks"' in text,
        "has_official_metric_gate_output": 'AddBooleanParameter("Official Metric Gate"' in text,
        "has_formal_release_allowed_output": 'AddBooleanParameter("Formal Release Allowed"' in text,
        "has_claim_readiness_output": 'AddTextParameter("Claim Readiness"' in text,
    }
    safety_checks = {
        "does_not_set_formal_true": "DA.SetData(4, false)" in text,
        "requires_release_gate_boundary": "release_gate.json" in text,
        "blocks_non_raw_trilinear": "sampling_raw_trilinear_check" in text,
        "blocks_non_z2m": "height_2m_check" in text,
        "blocks_non_ac_case": "official_case_check=\" + officialCase" in text,
        "blocks_non_n_direction": "wind_direction_check=\" + officialWindDirection" in text,
        "blocks_bad_probe_count": "probe_count_check" in text,
        "keeps_claim_readiness_boundary": "metric_gate_passed_release_gate_still_required" in text,
    }
    checks = {
        "source_exists": SOURCE.exists(),
        **{f"marker_{name}": value for name, value in marker_checks.items()},
        **output_checks,
        **safety_checks,
    }
    passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_software_metric_calculator_with_release_boundary",
        "casee_official_metrics_from_csv_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "source_path": str(SOURCE.relative_to(ROOT)),
        "checks": checks,
        "boundary": (
            "This gate audits a Grasshopper CSV metric-calculator component. It checks official "
            "protocol constants, metric formulas, and claim boundaries only; it does not run CFD, "
            "improve Case E official z=2 m metrics, prove Rhino loaded the GHA, or permit formal v0.4.0."
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
        "# CityLBM Case E Official Metrics From CSV Component Gate\n\n"
        f"- gate_passed: {str(passed).lower()}\n"
        "- evidence_type: newly_run\n"
        "- formal_accuracy_claim_supported: false\n"
        "- formal_release_allowed: false\n"
        "- default_setting_allowed: false\n"
        "- boundary: software metric-calculator evidence only; no CFD run or metric improvement.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
