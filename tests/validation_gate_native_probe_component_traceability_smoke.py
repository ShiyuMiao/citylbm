#!/usr/bin/env python3
"""Smoke-test native probe/component/Uref traceability gates."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_gate_module():
    path = REPO / "scripts" / "validation_gate.py"
    spec = importlib.util.spec_from_file_location("validation_gate", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def passing_native_audit():
    zero_counts = {
        "probe_audit_failed_row_count": 0,
        "probe_missing_id_count": 0,
        "probe_duplicate_id_count": 0,
        "missing_official_probe_id_count": 0,
        "unmatched_probe_id_count": 0,
        "probe_missing_official_coordinate_delta_count": 0,
        "probe_official_coordinate_delta_violation_count": 0,
        "probe_normalization_missing_count": 0,
        "probe_normalization_invalid_count": 0,
        "probe_wind_direction_missing_count": 0,
        "probe_wind_direction_invalid_count": 0,
        "probe_uref_missing_count": 0,
        "probe_uref_mismatch_count": 0,
        "probe_nearest_distance_missing_count": 0,
        "probe_tolerance_missing_or_disabled_count": 0,
        "probe_out_of_tolerance_count": 0,
    }
    return {
        **zero_counts,
        "probe_audit_row_count": 80,
        "probe_audit_valid_row_count": 80,
        "official_probe_coverage_ratio": 1.0,
        "official_probe_set_gate": "pass",
        "official_probe_set_row_count": 80,
        "official_expected_row_count": 80,
        "official_probe_ids_unique": True,
        "official_expected_z_m": "2",
        "official_z_mismatch_count": 0,
        "probe_official_height_gate": "pass",
        "probe_official_height_gate_reasons_csv": "",
        "probe_source_time_steps_match_runtime": True,
        "probe_source_steps_strictly_increasing": True,
        "probe_source_step_spacing_uniform": True,
        "probe_source_step_span_match_runtime": True,
        "probe_source_vtk_sha256_match_runtime": True,
        "probe_source_step_hash_pairs_match_runtime": True,
        "component_source_time_steps_match_runtime": True,
        "component_source_steps_strictly_increasing": True,
        "component_source_step_spacing_uniform": True,
        "component_source_vtk_sha256_match_runtime": True,
        "component_source_step_hash_pairs_match_runtime": True,
        "probe_source_step_span": 20000,
        "probe_minimum_validation_average_step_span": 20000,
        "component_normalization_gate": "pass",
        "component_sensitivity_gate": "pass",
        "normalization_scale_gate": "pass",
        "streamwise_sign_gate": "pass",
        "component_source_window_gate": "pass",
        "component_source_time_steps": "20000,21000,22000,23000,24000,25000,26000,27000,28000,29000,30000,31000,32000,33000,34000,35000,36000,37000,38000,39000,40000",
        "component_source_step_span": 20000,
        "component_minimum_source_step_span": 20000,
        "component_source_sha256": "a" * 64,
        "probe_audit_sha256": "b" * 64,
        "official_measurement_sha256": "c" * 64,
        "component_sensitivity_probe_audit_sha256": "b" * 64,
        "component_sensitivity_official_sha256": "c" * 64,
        "component_sensitivity_probe_audit_sha256_matches_current": True,
        "component_sensitivity_official_sha256_matches_current": True,
        "component_sensitivity_hash_traceability_gate": "pass",
        "probe_component_fidelity_class": "paper_grade_probe_component_normalization",
    }


def pass_gate(module, key):
    return {
        "key": key,
        "status": module.PASS,
        "evidence": "smoke pass",
        "required_next_action": "none",
    }


def main() -> int:
    module = load_gate_module()
    ok = module.native_probe_component_traceability_status(
        passing_native_audit(),
        min_avg_step_span=20000,
    )
    if not ok["ok"]:
        raise AssertionError(ok)

    missing_official_set = copy.deepcopy(passing_native_audit())
    for key in [
        "official_expected_row_count",
        "official_expected_z_m",
        "official_probe_set_row_count",
        "official_probe_ids_unique",
        "official_z_mismatch_count",
    ]:
        missing_official_set.pop(key, None)
    missing_status = module.native_probe_component_traceability_status(
        missing_official_set,
        min_avg_step_span=20000,
    )
    if missing_status["ok"]:
        raise AssertionError(missing_status)
    for expected in [
        "official_expected_row_count_missing",
        "official_expected_z_m_missing",
        "official_probe_set_row_count_missing",
        "official_probe_ids_unique_not_true:missing",
        "official_z_mismatch_count_missing",
    ]:
        if expected not in missing_status["reasons"]:
            raise AssertionError(missing_status)

    bad = copy.deepcopy(passing_native_audit())
    bad["probe_out_of_tolerance_count"] = 2
    bad["probe_source_vtk_sha256_match_runtime"] = False
    bad["component_source_window_gate"] = "fail"
    bad["streamwise_sign_gate"] = "fail"
    bad["component_source_step_span"] = 3000
    bad["component_source_time_steps_match_runtime"] = False
    bad["component_source_vtk_sha256_match_runtime"] = False
    bad["component_source_step_hash_pairs_match_runtime"] = False
    bad["probe_source_step_hash_pairs_match_runtime"] = False
    bad["component_sensitivity_probe_audit_sha256_matches_current"] = False
    bad["component_sensitivity_hash_traceability_gate"] = "fail"
    bad["official_probe_set_gate"] = "fail"
    bad["official_z_mismatch_count"] = 1
    bad["probe_official_height_gate"] = "fail"
    bad["probe_official_height_gate_reasons_csv"] = "official_z_mismatch_count:1"
    bad["probe_component_fidelity_class"] = "probe_projection_mismatch"
    failed = module.native_probe_component_traceability_status(
        bad,
        min_avg_step_span=20000,
    )
    if failed["ok"]:
        raise AssertionError(failed)
    reasons = failed["reasons"]
    for expected in [
        "probe_out_of_tolerance_count_not_zero:2",
        "probe_source_vtk_sha256_match_runtime_not_true:False",
        "component_source_step_span_below_20000",
        "component_source_time_steps_match_runtime_not_true:False",
        "component_source_vtk_sha256_match_runtime_not_true:False",
        "component_source_step_hash_pairs_match_runtime_not_true:False",
        "probe_source_step_hash_pairs_match_runtime_not_true:False",
        "component_source_window_gate_not_pass:fail",
        "streamwise_sign_gate_not_pass:fail",
        "component_sensitivity_probe_audit_sha256_matches_current_not_true:False",
        "component_sensitivity_hash_traceability_gate_not_pass:fail",
        "probe_component_fidelity_class_not_paper_grade:probe_projection_mismatch",
        "official_probe_set_gate_not_pass:fail",
        "official_z_mismatch_count_not_zero:1",
        "probe_official_height_gate_not_pass:fail",
        "probe_official_height_gate:official_z_mismatch_count:1",
    ]:
        if expected not in reasons:
            raise AssertionError(reasons)

    gates = [
        pass_gate(module, key)
        for key in [
            "validation_protocol_content",
            "inlet_source_evidence",
            "inlet_turbulence",
            "paper_grade_inlet_method",
            "inlet_length_scale",
            "inlet_correlation",
            "custom_k_profile",
            "inlet_profile_preservation",
            "inlet_profile_vtk_hash_traceability",
            "inlet_correlation_vtk_hash_traceability",
            "native_inlet_precondition_traceability",
            "k_preservation_or_accuracy",
            "metrics_input_hash_traceability",
            "coordinate_normalization",
            "compared_component",
            "probe_projection_distance",
            "probe_grid_extent",
            "probe_source_window",
            "probe_mapping",
            "component_normalization_sensitivity",
        ]
    ]
    gates.append(
        {
            "key": "native_probe_component_traceability",
            "status": module.FAIL,
            "evidence": failed["reasons_csv"],
            "required_next_action": "Regenerate probe and component audits.",
        }
    )
    priorities = module.build_diagnostic_priority(gates, {})
    coordinate = next(
        item
        for item in priorities
        if item["key"] == "coordinate_component_normalization"
    )
    if coordinate["rank"] != 4:
        raise AssertionError(coordinate)
    if coordinate["gate_status"] != module.FAIL:
        raise AssertionError(coordinate)
    if "RS probe projection" not in coordinate["next_action"]:
        raise AssertionError(coordinate)

    print("validation_gate_native_probe_component_traceability_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
