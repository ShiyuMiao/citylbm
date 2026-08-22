#!/usr/bin/env python3
"""Smoke-test native inlet precondition field propagation into metrics CSV."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_native_inlet_metrics_") as tmp:
        work = Path(tmp)
        official = work / "official.csv"
        probe = work / "probe.csv"
        inlet_source_audit = work / "inlet_source_audit.json"
        native_audit = work / "native_preconditions_audit.json"
        metrics = work / "metrics.csv"

        write_csv(
            official,
            [
                {
                    "case": "AIJ_CaseA",
                    "wind_direction": "N",
                    "No.": "1",
                    "Velocity_Ratio": "1.0",
                    "x": "0.0",
                    "y": "0.0",
                    "z": "2.0",
                }
            ],
        )
        write_csv(
            probe,
            [
                {
                    "probe_id": "1",
                    "compared_value": "0.9",
                    "failed": "false",
                    "validation_status": "pass",
                    "inside_vtk_grid_extent": "true",
                    "x": "0.0",
                    "y": "0.0",
                    "z": "2.0",
                    "nearest_distance": "0.1",
                    "normalization_valid": "true",
                    "wind_direction_valid": "true",
                    "Uref": "1.0",
                    "compared_component": "speed_ratio",
                    "tolerance": "0.5",
                    "vtk_source_time_steps": "1000;2000;3000",
                    "vtk_source_step_span": "2000",
                    "minimum_validation_average_step_span": "2000",
                    "vtk_source_sha256": "a;b;c",
                }
            ],
        )
        inlet_source_audit.write_text(
            json.dumps(
                {
                    "inlet_source_gate": "pass",
                    "inlet_source_gate_reasons": [
                        "inlet_source_consistent_with_declared_metadata",
                    ],
                    "paper_grade_inlet_source_gate": "fail",
                    "paper_grade_inlet_source_gate_reasons": [
                        "source_velocity_field_only",
                    ],
                    "inlet_source_method_class": "stg_lite_correlated_velocity_field_only",
                    "inlet_source_distribution_consistent": False,
                    "inlet_source_velocity_field_only": True,
                    "has_streamwise_clipping_control": True,
                    "streamwise_min_fraction": 0.0,
                    "streamwise_clipping_enabled": False,
                    "has_legacy_hardcoded_streamwise_clipping": False,
                    "recommended_next_action": "Use source evidence plus final-window VTK inlet profile/correlation audits.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        native_audit.write_text(
            json.dumps(
                {
                    "native_preconditions_gate": "fail",
                    "native_preconditions_time_average_gate": "fail",
                    "native_preconditions_time_average_evidence_gate": "fail",
                    "native_preconditions_time_average_evidence_gate_reasons_csv": (
                        "runtime_average_window_frame_count_4_below_minimum_40;"
                        "runtime_final_window_stationarity_gate_not_pass:diagnostic_only"
                    ),
                    "native_boundary_equivalence_gate": "fail",
                    "native_boundary_equivalence_gate_reasons_csv": (
                        "boundary_source_simplified_not_false:True;"
                        "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail"
                    ),
                    "native_inlet_equivalence_gate": "fail",
                    "native_inlet_equivalence_gate_reasons_csv": (
                        "inlet_source_velocity_field_only_not_false:True;"
                        "inlet_tke_gate_not_pass:fail"
                    ),
                    "expected_uref_mps": 3.93,
                    "actual_uref_mps": 3.90,
                    "expected_zref_m": 15.9,
                    "af_uref_at_zref_mps": 3.928296,
                    "uref_af_profile_delta_mps": 0.001704,
                    "metadata_uref_af_profile_delta_mps": 0.028296,
                    "inlet_profile_audit": "run/inlet_profile_audit.json",
                    "inlet_profile_gate": "FAIL",
                    "inlet_u_profile_gate": "PASS",
                    "inlet_k_profile_gate": "FAIL",
                    "inlet_profile_time_averaging_gate": "FAIL",
                    "inlet_profile_af_csv_sha256_matches_expected": False,
                    "inlet_profile_source_time_steps_match_runtime": True,
                    "inlet_profile_source_vtk_sha256_match_runtime": False,
                    "inlet_profile_source_step_span": 2000,
                    "inlet_profile_minimum_step_span": 20000,
                    "inlet_correlation_audit": "run/inlet_correlation_audit.json",
                    "inlet_correlation_gate": "FAIL",
                    "inlet_k_variance_gate": "FAIL",
                    "inlet_streamwise_variance_target_from_k": 0.42,
                    "inlet_streamwise_variance_to_k_ratio": 0.31,
                    "inlet_tke_gate": "FAIL",
                    "inlet_tke_target_from_af_k": 0.63,
                    "inlet_tke_to_k_ratio": 0.22,
                    "inlet_mean_turbulent_kinetic_energy_from_components": 0.14,
                    "inlet_correlation_source_time_steps_match_runtime": True,
                    "inlet_correlation_source_vtk_sha256_match_runtime": False,
                    "inlet_correlation_source_step_span": 2000,
                    "inlet_correlation_minimum_step_span": 20000,
                    "native_precondition_closure_gate": "fail",
                    "native_precondition_closed_stage_count": 2,
                    "native_precondition_failed_stage_count": 4,
                    "native_precondition_failed_stage_keys": [
                        "turbulent_inlet_method_and_u_k_preservation",
                        "time_averaging_stationarity",
                    ],
                    "native_precondition_top_blocking_stage_key": "turbulent_inlet_method_and_u_k_preservation",
                    "native_precondition_top_blocking_stage_rank": 1,
                    "native_precondition_top_blocking_stage_reason_count": 2,
                    "native_precondition_top_blocking_stage_reasons": [
                        "inlet_k_profile_gate_not_pass",
                        "inlet_correlation_gate_not_pass",
                    ],
                    "inlet_source_has_mean_preserving_inlet_correction": True,
                    "inlet_source_has_layerwise_mean_preserving_inlet_correction": True,
                    "inlet_source_has_streamwise_clipping_control": True,
                    "inlet_source_streamwise_min_fraction": 0.0,
                    "inlet_source_streamwise_clipping_enabled": False,
                    "inlet_source_has_legacy_hardcoded_streamwise_clipping": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        command = [
            sys.executable,
            str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
            "--probe-audit",
            str(probe),
            "--official",
            str(official),
            "--out",
            str(metrics),
            "--case",
            "AIJ_CaseA",
            "--wind-direction",
            "N",
            "--source-time-steps",
            "1000;2000;3000",
            "--inlet-source-audit",
            str(inlet_source_audit),
            "--native-preconditions-audit",
            str(native_audit),
        ]
        subprocess.run(command, cwd=str(REPO), check=True)

        with metrics.open("r", encoding="utf-8", newline="") as handle:
            row = next(csv.DictReader(handle))

    expected = {
        "native_inlet_profile_audit": "run/inlet_profile_audit.json",
        "native_inlet_profile_gate": "fail",
        "native_inlet_u_profile_gate": "pass",
        "native_inlet_k_profile_gate": "fail",
        "native_inlet_profile_time_averaging_gate": "fail",
        "native_inlet_profile_af_csv_sha256_matches_expected": "false",
        "native_inlet_profile_source_time_steps_match_runtime": "true",
        "native_inlet_profile_source_vtk_sha256_match_runtime": "false",
        "native_inlet_profile_source_step_span": "2000",
        "native_inlet_profile_minimum_step_span": "20000",
        "native_inlet_correlation_audit": "run/inlet_correlation_audit.json",
        "native_inlet_correlation_gate": "fail",
        "native_inlet_k_variance_gate": "fail",
        "native_inlet_streamwise_variance_target_from_k": "0.42",
        "native_inlet_streamwise_variance_to_k_ratio": "0.31",
        "native_inlet_tke_gate": "fail",
        "native_inlet_tke_target_from_af_k": "0.63",
        "native_inlet_tke_to_k_ratio": "0.22",
        "native_inlet_mean_turbulent_kinetic_energy_from_components": "0.14",
        "native_inlet_correlation_source_time_steps_match_runtime": "true",
        "native_inlet_correlation_source_vtk_sha256_match_runtime": "false",
        "native_inlet_correlation_source_step_span": "2000",
        "native_inlet_correlation_minimum_step_span": "20000",
        "native_preconditions_time_average_evidence_gate": "fail",
        "native_preconditions_time_average_evidence_gate_reasons": (
            "runtime_average_window_frame_count_4_below_minimum_40;"
            "runtime_final_window_stationarity_gate_not_pass:diagnostic_only"
        ),
        "native_boundary_equivalence_gate": "fail",
        "native_boundary_equivalence_gate_reasons": (
            "boundary_source_simplified_not_false:True;"
            "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail"
        ),
        "native_inlet_equivalence_gate": "fail",
        "native_inlet_equivalence_gate_reasons": (
            "inlet_source_velocity_field_only_not_false:True;"
            "inlet_tke_gate_not_pass:fail"
        ),
        "native_preconditions_expected_uref_mps": "3.93",
        "native_preconditions_actual_uref_mps": "3.9",
        "native_preconditions_expected_zref_m": "15.9",
        "native_preconditions_af_uref_at_zref_mps": "3.928296",
        "native_preconditions_uref_af_profile_delta_mps": "0.001704",
        "native_preconditions_metadata_uref_af_profile_delta_mps": "0.028296",
        "native_precondition_closure_gate": "fail",
        "native_precondition_closed_stage_count": "2",
        "native_precondition_failed_stage_count": "4",
        "native_precondition_failed_stage_keys": "turbulent_inlet_method_and_u_k_preservation;time_averaging_stationarity",
        "native_precondition_top_blocking_stage_key": "turbulent_inlet_method_and_u_k_preservation",
        "native_precondition_top_blocking_stage_rank": "1",
        "native_precondition_top_blocking_stage_reason_count": "2",
        "native_precondition_top_blocking_stage_reasons": "inlet_k_profile_gate_not_pass;inlet_correlation_gate_not_pass",
        "native_inlet_source_has_mean_preserving_inlet_correction": "true",
        "native_inlet_source_has_layerwise_mean_preserving_inlet_correction": "true",
        "native_inlet_source_has_streamwise_clipping_control": "true",
        "native_inlet_source_streamwise_min_fraction": "0.0",
        "native_inlet_source_streamwise_clipping_enabled": "false",
        "native_inlet_source_has_legacy_hardcoded_streamwise_clipping": "false",
        "inlet_source_has_streamwise_clipping_control": "true",
        "inlet_source_streamwise_min_fraction": "0.0",
        "inlet_source_streamwise_clipping_enabled": "false",
        "inlet_source_has_legacy_hardcoded_streamwise_clipping": "false",
        "synthetic_min_streamwise_fraction": "0.0",
        "synthetic_streamwise_clipping_enabled": "false",
        "synthetic_legacy_hardcoded_streamwise_clipping": "false",
    }
    for field, value in expected.items():
        if row.get(field) != value:
            raise AssertionError(f"{field}: expected {value!r}, got {row.get(field)!r}")

    print("native_inlet_metrics_fields_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
