#!/usr/bin/env python3
"""Smoke-test native probe/component gates through real audit input files."""

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


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(REPO),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require(condition: bool, data: object) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_probe_component_file_gate_") as tmp:
        root = Path(tmp)
        runtime_audit = root / "native_run_audit.json"
        official = root / "official.csv"
        probe = root / "probe_audit.csv"
        component = root / "component_sensitivity_audit.json"
        report = root / "native_preconditions_audit.json"

        runtime_hashes = ["a" * 64, "b" * 64, "c" * 64]
        write_json(
            runtime_audit,
            {
                "vtk_pattern": "u-*.vtk",
                "average_last_n_requested": 3,
                "selected_last_window": True,
                "source_time_steps": "1000,2000,3000",
                "source_step_span": 2000,
                "source_steps_strictly_increasing": True,
                "source_step_spacing_uniform": True,
                "source_vtk_sha256": ";".join(runtime_hashes),
            },
        )
        write_csv(
            official,
            [
                {
                    "case": "ac",
                    "wind_direction": "N",
                    "No.": "P1",
                    "x": "0",
                    "y": "0",
                    "z": "2",
                    "Velocity_Ratio": "1.0",
                },
                {
                    "case": "ac",
                    "wind_direction": "N",
                    "No.": "P2",
                    "x": "1",
                    "y": "0",
                    "z": "2",
                    "Velocity_Ratio": "0.8",
                },
            ],
        )
        write_csv(
            probe,
            [
                {
                    "probe_id": "P1",
                    "x": "9",
                    "y": "0",
                    "z": "2",
                    "failed": "false",
                    "normalization_valid": "true",
                    "wind_direction_valid": "true",
                    "u_ref": "1.0",
                    "nearest_distance": "3.0",
                    "tolerance": "2.6",
                    "out_of_tolerance": "false",
                    "compared_component": "speed_ratio",
                    "official_probe_set_row_count": "2",
                    "official_expected_row_count": "2",
                    "official_probe_ids_unique": "true",
                    "official_expected_z": "2",
                    "official_expected_z_tolerance": "0.001",
                    "official_z_match_count": "2",
                    "official_z_mismatch_count": "0",
                    "source_time_steps": "1000,2000",
                    "source_step_span": "1000",
                    "minimum_validation_average_step_span": "2000",
                    "source_vtk_sha256": ";".join(runtime_hashes[:2]),
                }
            ],
        )
        write_json(
            component,
            {
                "component_normalization_gate": "fail",
                "component_sensitivity_gate": "pass",
                "normalization_scale_gate": "fail",
                "streamwise_sign_gate": "fail",
                "streamwise_sign_gate_reasons": [],
                "normalization_scale_gate_reasons": [
                    "best_fit_scale_1.515152_suggests_uref_or_unit_error",
                    "scaled_rmse_improvement_0.420000_suggests_scale_like_error",
                ],
                "component_source_window_gate": "fail",
                "component_source_window_gate_reasons": ["source_window_mismatch"],
                "component_source_time_steps": "1000,2000",
                "component_source_step_span": 1000,
                "component_minimum_source_step_span": 2000,
                "component_source_sha256": ";".join(runtime_hashes[:2]),
                "probe_audit_sha256": "d" * 64,
                "official_sha256": "e" * 64,
            },
        )

        audit = run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_native_preconditions.py"),
                str(root),
                "--runtime-audit",
                str(runtime_audit),
                "--probe-audit",
                str(probe),
                "--component-sensitivity-audit",
                str(component),
                "--official",
                str(official),
                "--case",
                "ac",
                "--wind-direction-label",
                "N",
                "--u-ref",
                "3.928296",
                "--expected-compared-component",
                "abs_streamwise_ratio",
                "--average-last-n",
                "3",
                "--min-avg-frames",
                "3",
                "--min-avg-step-span",
                "2000",
                "--out",
                str(report),
            ]
        )
        require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
        data = json.loads(report.read_text(encoding="utf-8"))
        reasons = data.get("native_probe_component_equivalence_gate_reasons", [])
        gate_reasons = data.get("native_preconditions_gate_reasons", [])

        require(data.get("native_probe_component_equivalence_gate") == "fail", data)
        require(data.get("probe_component_fidelity_class") == "official_probe_coordinate_mismatch", data)
        require("native_probe_component_equivalence_gate_not_pass" in gate_reasons, data)
        for expected in [
            "probe_compared_component_speed_ratio_expected_abs_streamwise_ratio",
            "missing_official_probe_id_count_1",
            "probe_official_coordinate_delta_violation_count_1",
            "official_probe_coverage_ratio_not_one:0.5",
            "probe_uref_mismatch_count_1",
            "probe_source_time_steps_match_runtime_not_true:False",
            "probe_source_step_span_match_runtime_not_true:False",
            "probe_source_vtk_sha256_match_runtime_not_true:False",
            "probe_source_step_hash_pairs_match_runtime_not_true:False",
            "component_source_time_steps_match_runtime_not_true:False",
            "component_source_vtk_sha256_match_runtime_not_true:False",
            "component_source_step_hash_pairs_match_runtime_not_true:False",
            "component_sensitivity_probe_audit_sha256_matches_current_not_true:False",
            "component_sensitivity_official_sha256_matches_current_not_true:False",
            "component_source_step_span_1000_below_minimum_2000",
            "component_normalization_gate_not_pass:fail",
            "normalization_scale_gate_not_pass:fail",
            "streamwise_sign_gate_not_pass:fail",
            "normalization_scale_gate:best_fit_scale_1.515152_suggests_uref_or_unit_error",
            "normalization_scale_gate:scaled_rmse_improvement_0.420000_suggests_scale_like_error",
            "component_source_window_gate_not_pass:fail",
            "component_sensitivity_hash_traceability_gate_not_pass:fail",
        ]:
            require(expected in reasons, {"missing": expected, "reasons": reasons})
        require(data.get("component_sensitivity_hash_traceability_gate") == "fail", data)
        require(data.get("probe_max_official_coordinate_delta_m") == 9.0, data)
        require(data.get("probe_uref_mismatch_count") == 1, data)
        require(data.get("probe_source_time_steps_match_runtime") is False, data)
        require(data.get("component_source_vtk_sha256_match_runtime") is False, data)
        require(data.get("probe_audit_sha256") == sha256(probe), data)
        require(data.get("official_measurement_sha256") == sha256(official), data)

    print("native_preconditions_probe_component_file_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
