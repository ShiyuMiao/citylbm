#!/usr/bin/env python3
"""Smoke-test validation_gate loads component audit paths recorded in metrics."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def gate_by_key(report: dict, key: str) -> dict:
    for gate in report.get("gates", []):
        if gate.get("key") == key:
            return gate
    raise AssertionError(f"Missing gate: {key}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_validation_gate_component_path_") as tmp:
        root = Path(tmp)
        run_dir = root / "run"
        artifact_dir = root / "artifacts"
        metrics = root / "metrics.csv"
        probe = root / "probe_audit.csv"
        official = root / "official.csv"
        component = artifact_dir / "component_sensitivity_audit.json"
        report_path = root / "report.json"

        run_dir.mkdir(parents=True)
        write_csv(
            official,
            [
                {"No.": "P1", "case": "CaseA", "wind_direction": "W", "U(m/s)": "1.0"},
                {"No.": "P2", "case": "CaseA", "wind_direction": "W", "U(m/s)": "0.8"},
            ],
        )
        write_csv(
            probe,
            [
                {
                    "probe_id": "P1",
                    "failed": "false",
                    "out_of_tolerance": "false",
                    "compared_component": "speed_ratio",
                    "speed_ratio": "0.66",
                    "streamwise_ratio": "0.66",
                },
                {
                    "probe_id": "P2",
                    "failed": "false",
                    "out_of_tolerance": "false",
                    "compared_component": "speed_ratio",
                    "speed_ratio": "0.528",
                    "streamwise_ratio": "0.528",
                },
            ],
        )
        write_json(
            component,
            {
                "case": "CaseA",
                "wind_direction": "W",
                "component_normalization_gate": "fail",
                "component_sensitivity_gate": "pass",
                "normalization_scale_gate": "fail",
                "normalization_scale_gate_reasons": [
                    "mean_sim_to_exp_ratio_0.66_below_0.8_suggests_systematic_underprediction"
                ],
                "streamwise_sign_gate": "pass",
                "streamwise_sign_gate_reasons": ["streamwise_ratio_direction_sign_consistent"],
                "component_source_window_gate": "pass",
                "component_source_window_gate_reasons": ["source_window_consistent_and_hashed"],
                "component_source_time_steps": "1000,2000",
                "component_source_step_span": 1000,
                "component_minimum_source_step_span": 1000,
                "component_source_sha256": "a" * 64,
                "component_source_hash_set_unique_count": 2,
                "probe_audit_sha256": sha256(probe),
                "official_sha256": sha256(official),
                "official_filtered_row_count": 2,
                "official_id_count": 2,
                "probe_row_count": 2,
                "valid_probe_id_count": 2,
                "matched_valid_probe_id_count": 2,
                "unmatched_valid_probe_id_count": 0,
                "missing_official_probe_id_count": 0,
                "official_probe_coverage_ratio": 1.0,
                "valid_probe_compared_components": ["speed_ratio"],
                "valid_probe_compared_component_count": 2,
                "valid_probe_missing_compared_component_count": 0,
                "selected_component": "speed_ratio",
                "selected_component_source": "explicit",
                "best_component_by_rmse": "speed_ratio",
                "selected_component_rmse": 0.27,
                "best_component_rmse": 0.27,
                "component_rmse_improvement_ratio": 0.0,
                "selected_component_mean_sim": 0.594,
                "selected_component_mean_exp": 0.9,
                "selected_component_mean_sim_to_exp_ratio": 0.66,
                "selected_best_fit_scale_to_exp": 1.5151515151515151,
                "selected_scaled_improvement_ratio": 0.0,
            },
        )
        write_csv(
            metrics,
            [
                {
                    "case": "CaseA",
                    "wind_direction": "W",
                    "component_sensitivity_audit": str(component.relative_to(root)),
                    "compared_component": "speed_ratio",
                    "compared_component_consistency_gate": "pass",
                    "component_normalization_gate": "fail",
                    "component_sensitivity_gate": "pass",
                    "normalization_scale_gate": "fail",
                    "streamwise_sign_gate": "pass",
                }
            ],
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_gate.py"),
                str(run_dir),
                "--metrics",
                str(metrics),
                "--probe-audit",
                str(probe),
                "--official",
                str(official),
                "--case",
                "CaseA",
                "--expected-compared-component",
                "speed_ratio",
                "--out",
                str(report_path),
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 2:
            raise AssertionError(
                f"Expected validation failure, got {completed.returncode}\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        gate = gate_by_key(report, "component_normalization_sensitivity")
        evidence = str(gate.get("evidence") or "")
        if "audit_exists=True" not in evidence:
            raise AssertionError(evidence)
        if "component_normalization_gate=fail" not in evidence:
            raise AssertionError(evidence)
        if "normalization_scale_gate=fail" not in evidence:
            raise AssertionError(evidence)
        if "selected_component_mean_sim_to_exp_ratio=0.66" not in evidence:
            raise AssertionError(evidence)
        if "mean_sim_to_exp_ratio_0.66_below_0.8_suggests_systematic_underprediction" not in evidence:
            raise AssertionError(evidence)

    print("validation_gate_component_audit_metrics_path_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
