from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TRACKED_GHA = ROOT / "CityLBM/bin/CityLBM.gha"
RELEASE_GHA = ROOT / "CityLBM/bin/Release/CityLBM.gha"
COMPONENT_GATE = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_component_gate.json"
OUT_JSON = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_binary_gate.json"
OUT_CSV = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_binary_gate.csv"
OUT_MD = ROOT / "docs/experiments/casee/results/citylbm_casee_official_metrics_from_csv_binary_gate.md"


REQUIRED_MARKERS = [
    "CaseEOfficialMetricsFromCsvComponent",
    "Case E Official Metrics From CSV",
    "Metric Rows",
    "Gate Checks",
    "Official Metric Gate",
    "Formal Release Allowed",
    "official_velocity_ratio",
    "predicted_velocity_ratio",
    "MAE_pp=",
    "RMSE_pp=",
    "bias_pp=",
    "R2=",
    "Pearson=",
    "MAE threshold: < 15.0 pp",
    "R2 threshold: > 0.0",
    "Pearson threshold: > 0.0",
    "sampling_raw_trilinear_check=",
    "height_2m_check=",
    "probe_count_check=",
    "official_z2m_metric_gate=",
    "formal_release_allowed=false",
    "release_gate.json",
    "z_plus_half",
    "6189C8B7-3E79-4C0B-BC1D-4E85D7E90493",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contains_marker(binary: bytes, marker: str) -> bool:
    return marker.encode("utf-8") in binary or marker.encode("utf-16le") in binary


def main() -> int:
    tracked_exists = TRACKED_GHA.exists()
    release_exists = RELEASE_GHA.exists()
    tracked_sha = sha256(TRACKED_GHA) if tracked_exists else ""
    release_sha = sha256(RELEASE_GHA) if release_exists else ""
    binary = TRACKED_GHA.read_bytes() if tracked_exists else b""
    marker_checks = {marker: contains_marker(binary, marker) for marker in REQUIRED_MARKERS}
    component_gate_payload = json.loads(COMPONENT_GATE.read_text(encoding="utf-8")) if COMPONENT_GATE.exists() else {}
    checks = {
        "tracked_gha_exists": tracked_exists,
        "release_gha_exists": release_exists,
        "tracked_gha_matches_release_gha": tracked_exists and release_exists and tracked_sha == release_sha,
        "source_component_gate_passed": bool(component_gate_payload.get("casee_official_metrics_from_csv_component_gate_passed")),
        "all_required_markers_present_in_tracked_gha": all(marker_checks.values()),
    }
    passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_packaged_casee_official_metrics_from_csv_component",
        "casee_official_metrics_from_csv_binary_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "default_setting_allowed": False,
        "tracked_gha_path": str(TRACKED_GHA.relative_to(ROOT)),
        "release_gha_path": str(RELEASE_GHA.relative_to(ROOT)),
        "tracked_gha_sha256": tracked_sha,
        "release_gha_sha256": release_sha,
        "tracked_gha_size_bytes": TRACKED_GHA.stat().st_size if tracked_exists else 0,
        "required_markers": marker_checks,
        "checks": checks,
        "boundary": (
            "This gate checks that the packaged GHA contains the Case E Official Metrics From CSV "
            "component strings. It is packaging evidence for a metric calculator only; it does not "
            "prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["check", "passed"])
        writer.writeheader()
        for name, value in checks.items():
            writer.writerow({"check": name, "passed": value})
        for marker, value in marker_checks.items():
            writer.writerow({"check": f"marker::{marker}", "passed": value})
    OUT_MD.write_text(
        "# CityLBM Case E Official Metrics From CSV Binary Gate\n\n"
        f"- gate_passed: {str(passed).lower()}\n"
        f"- tracked_gha_sha256: {tracked_sha}\n"
        f"- release_gha_sha256: {release_sha}\n"
        "- formal_accuracy_claim_supported: false\n"
        "- formal_release_allowed: false\n"
        "- default_setting_allowed: false\n"
        "- boundary: packaged metric-calculator evidence only; no CFD run or metric improvement.\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
