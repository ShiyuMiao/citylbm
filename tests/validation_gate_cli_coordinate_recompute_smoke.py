#!/usr/bin/env python3
"""Smoke-test that validation_gate CLI recomputes probe coordinates from official CSV."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_gate_cli_coord_") as tmp:
        root = Path(tmp)
        official = root / "official.csv"
        probe = root / "probe_audit.csv"
        metrics = root / "validation_metrics.csv"
        report = root / "validation_gate_report.json"

        write_text(
            official,
            """No.,case,wind_direction,x,y,z,Velocity_Ratio
P1,ac,N,0,0,2,0.50
""",
        )
        write_csv(
            probe,
            {
                "probe_id": "P1",
                "x": 9.0,
                "y": 0.0,
                "z": 2.0,
                "failed": "false",
                "validation_status": "pass",
                "inside_vtk_grid_extent": "true",
                "normalization_valid": "true",
                "wind_direction_valid": "true",
                "Uref": 3.928296,
                "wind_x": 0.0,
                "wind_y": -1.0,
                "wind_z": 0.0,
                "compared_component": "speed_ratio",
                "nearest_distance": 0.0,
                "tolerance": 1.0,
                "official_coordinate_delta": 0.0,
                "vtk_source_time_steps": "1000;2000",
                "vtk_source_step_span": 1000,
                "minimum_validation_average_step_span": 1000,
                "vtk_source_sha256": "a" * 64,
                "vtk_source_files": "u-000001000.vtk;u-000002000.vtk",
            },
        )
        write_csv(
            metrics,
            {
                "case": "ac",
                "wind_direction": "N",
                "software": "citylbm",
                "version": "0.3.0",
                "dx_m": 1.0,
                "Uref_mps": 3.928296,
                "Zref_m": 15.9,
                "wind_vector": "0,-1,0",
                "compared_component": "speed_ratio",
                "compared_component_consistency_gate": "pass",
                "probe_component_fidelity_class": "paper_grade_probe_component_normalization",
                "component_sensitivity_audit": "pass",
                "component_normalization_gate": "pass",
                "valid_n": 1,
                "failed_n": 0,
                "U_MAE_Uref": 0.0,
                "U_RMSE_Uref": 0.0,
                "U_bias_Uref": 0.0,
                "U_R2": 1.0,
                "slope": 1.0,
                "intercept": 0.0,
                "protocol_gate": "metrics_ready_for_validation_gate",
                "normalization_valid": "true",
                "wind_direction_valid": "true",
                "probe_uref_expected_mps": 3.928296,
                "probe_uref_values": "3.928296",
                "probe_uref_mismatch_count": 0,
                "max_official_coordinate_delta_m": 0.0,
                "official_coordinate_delta_count": 1,
                "official_measurement_count": 1,
                "official_probe_coverage_ratio": 1.0,
                "missing_official_probe_count": 0,
            },
        )

        command = [
            sys.executable,
            str(REPO / "scripts" / "validation_gate.py"),
            str(root),
            "--metrics",
            str(metrics),
            "--probe-audit",
            str(probe),
            "--official",
            str(official),
            "--case",
            "ac",
            "--software",
            "citylbm",
            "--expected-compared-component",
            "speed_ratio",
            "--expected-uref",
            "3.928296",
            "--expected-wind-vector",
            "0,-1,0",
            "--out",
            str(report),
        ]
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
        if result.returncode != 2:
            raise AssertionError(
                f"Expected validation gate failure from recomputed coordinate mismatch, got {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        data = json.loads(report.read_text(encoding="utf-8"))
        gates = {gate["key"]: gate for gate in data["gates"]}
        coordinate_gate = gates.get("coordinate_normalization")
        if not coordinate_gate or coordinate_gate["status"] != "FAIL":
            raise AssertionError(data)
        evidence = coordinate_gate["evidence"]
        required_fragments = [
            "coordinate_source=current_official_csv_recomputed",
            "max_official_coordinate_delta_m=9.0",
            "metrics_max_official_coordinate_delta_m=0.0",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in evidence]
        if missing:
            raise AssertionError(f"Missing evidence fragments {missing} in {evidence}")

    print("validation_gate_cli_coordinate_recompute_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
