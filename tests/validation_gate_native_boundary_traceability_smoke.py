#!/usr/bin/env python3
"""Smoke-test native boundary traceability gates."""

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
    steps = [1000 * index for index in range(1, 41)]
    hashes = [f"{index:064x}" for index in range(1, 41)]
    return {
        "boundary_source_gate": "pass",
        "paper_grade_boundary_source_gate": "pass",
        "boundary_protocol_gate": "pass",
        "boundary_evidence_gate": "pass",
        "boundary_run_identity_gate": "pass",
        "boundary_clearance_numeric_gate": "pass",
        "boundary_blockage_gate": "pass",
        "boundary_runtime_gate": "pass",
        "boundary_runtime_traceability_gate": "pass",
        "boundary_runtime_profile_preservation_gate": "pass",
        "boundary_runtime_inlet_gate": "pass",
        "boundary_runtime_side_top_gate": "pass",
        "boundary_runtime_side_top_normal_leakage_gate": "pass",
        "boundary_runtime_outlet_gate": "pass",
        "boundary_source_wind_tunnel_equivalent": True,
        "boundary_source_simplified": False,
        "boundary_source_setup_cpp_sha256_matches_current": True,
        "boundary_evidence_metadata_sha256_matches_current": True,
        "boundary_evidence_files_all_hashed": True,
        "boundary_equivalence_supported": True,
        "boundary_evidence_class_supported": True,
        "boundary_condition_fields_supported": True,
        "boundary_source_method_class": "wind_tunnel_equivalent_boundary_source",
        "boundary_source_has_paper_grade_outlet_source": True,
        "boundary_source_has_paper_grade_side_top_source": True,
        "boundary_source_has_paper_grade_rough_wall_source": True,
        "boundary_source_has_paper_grade_development_source": True,
        "boundary_source_missing_paper_grade_source_evidence": "",
        "boundary_missing_evidence_fields": "",
        "boundary_unsupported_condition_fields": "",
        "boundary_evidence_files_missing": "",
        "boundary_evidence_files_empty": "",
        "boundary_evidence_files_unreadable": "",
        "boundary_required_support_fields_missing_or_false": "",
        "boundary_evidence_aij_case": "CaseE",
        "boundary_evidence_wind_direction": "N",
        "boundary_runtime_source_time_steps": steps,
        "boundary_runtime_source_time_steps_csv": ";".join(str(step) for step in steps),
        "boundary_runtime_source_step_span": 39000,
        "boundary_runtime_reported_source_step_span": 39000,
        "boundary_runtime_source_time_steps_match_runtime": True,
        "boundary_runtime_source_steps_strictly_increasing": True,
        "boundary_runtime_source_step_spacing_uniform": True,
        "boundary_runtime_selected_last_window": True,
        "boundary_runtime_source_vtk_sha256": hashes,
        "boundary_runtime_source_vtk_sha256_csv": ";".join(hashes),
        "boundary_runtime_source_vtk_sha256_match_runtime": True,
        "boundary_runtime_source_step_hash_pairs_match_runtime": True,
        "boundary_runtime_source_vtk_sha256_count": 40,
        "boundary_runtime_source_vtk_sha256_unique_count": 40,
        "boundary_runtime_frame_count": 40,
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
    ok = module.native_boundary_traceability_status(
        passing_native_audit(),
        expected_case="CaseE",
        expected_wind_direction="N",
    )
    if not ok["ok"]:
        raise AssertionError(ok)

    bad = copy.deepcopy(passing_native_audit())
    bad["boundary_source_simplified"] = True
    bad["boundary_source_method_class"] = "simplified_type_e_box"
    bad["boundary_source_has_paper_grade_outlet_source"] = False
    bad["boundary_source_has_paper_grade_side_top_source"] = False
    bad["boundary_source_has_paper_grade_rough_wall_source"] = False
    bad["boundary_source_has_paper_grade_development_source"] = False
    bad["boundary_evidence_metadata_sha256_matches_current"] = False
    bad["boundary_required_support_fields_missing_or_false"] = "roughness_treatment_supported"
    bad["boundary_evidence_wind_direction"] = "S"
    failed = module.native_boundary_traceability_status(
        bad,
        expected_case="CaseE",
        expected_wind_direction="N",
    )
    if failed["ok"]:
        raise AssertionError(failed)
    for expected in [
        "boundary_source_simplified_not_false:True",
        "boundary_source_method_class_not_wind_tunnel_equivalent:simplified_type_e_box",
        "boundary_source_has_paper_grade_outlet_source_not_true:False",
        "boundary_source_has_paper_grade_side_top_source_not_true:False",
        "boundary_source_has_paper_grade_rough_wall_source_not_true:False",
        "boundary_source_has_paper_grade_development_source_not_true:False",
        "boundary_evidence_metadata_sha256_matches_current_not_true:False",
        "boundary_required_support_fields_missing_or_false_not_empty:roughness_treatment_supported",
        "boundary_evidence_wind_direction_mismatch:S!=N",
    ]:
        if expected not in failed["reasons"]:
            raise AssertionError(failed["reasons"])

    bad_normal = copy.deepcopy(passing_native_audit())
    bad_normal["boundary_runtime_side_top_normal_leakage_gate"] = "fail"
    normal_failed = module.native_boundary_traceability_status(
        bad_normal,
        expected_case="CaseE",
        expected_wind_direction="N",
    )
    if normal_failed["ok"]:
        raise AssertionError(normal_failed)
    if "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail" not in normal_failed["reasons"]:
        raise AssertionError(normal_failed["reasons"])

    missing_normal = copy.deepcopy(passing_native_audit())
    del missing_normal["boundary_runtime_side_top_normal_leakage_gate"]
    missing_failed = module.native_boundary_traceability_status(
        missing_normal,
        expected_case="CaseE",
        expected_wind_direction="N",
    )
    if missing_failed["ok"]:
        raise AssertionError(missing_failed)
    if "boundary_runtime_side_top_normal_leakage_gate_not_pass:missing" not in missing_failed["reasons"]:
        raise AssertionError(missing_failed["reasons"])

    short_window = copy.deepcopy(passing_native_audit())
    short_window["boundary_runtime_source_time_steps"] = [1000, 2000, 3000, 4000]
    short_window["boundary_runtime_source_time_steps_csv"] = "1000;2000;3000;4000"
    short_window["boundary_runtime_source_step_span"] = 3000
    short_window["boundary_runtime_reported_source_step_span"] = 3000
    short_window["boundary_runtime_source_vtk_sha256"] = [f"{index:064x}" for index in range(1, 5)]
    short_window["boundary_runtime_source_vtk_sha256_csv"] = ";".join(
        short_window["boundary_runtime_source_vtk_sha256"]
    )
    short_window["boundary_runtime_source_vtk_sha256_count"] = 4
    short_window["boundary_runtime_source_vtk_sha256_unique_count"] = 4
    short_window["boundary_runtime_frame_count"] = 4
    short_window["boundary_runtime_selected_last_window"] = False
    short_window["boundary_runtime_source_time_steps_match_runtime"] = False
    short_window["boundary_runtime_source_vtk_sha256_match_runtime"] = False
    short_window["boundary_runtime_source_step_hash_pairs_match_runtime"] = False
    short_failed = module.native_boundary_traceability_status(
        short_window,
        expected_case="CaseE",
        expected_wind_direction="N",
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if short_failed["ok"]:
        raise AssertionError(short_failed)
    for expected in [
        "boundary_runtime_frame_count_below_40",
        "boundary_runtime_source_step_span_below_20000",
        "boundary_runtime_selected_last_window_not_true:False",
        "boundary_runtime_source_time_steps_match_runtime_not_true:False",
        "boundary_runtime_source_vtk_sha256_match_runtime_not_true:False",
        "boundary_runtime_source_step_hash_pairs_match_runtime_not_true:False",
        "boundary_runtime_source_vtk_sha256_count_below_40",
    ]:
        if expected not in short_failed["reasons"]:
            raise AssertionError(short_failed["reasons"])

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
            "boundary_source_evidence",
            "boundary_protocol",
            "boundary_runtime",
            "roughness_or_precursor",
        ]
    ]
    gates.append(
        {
            "key": "native_boundary_traceability",
            "status": module.FAIL,
            "evidence": failed["reasons_csv"],
            "required_next_action": "Regenerate boundary audits.",
        }
    )
    priorities = module.build_diagnostic_priority(gates, {})
    boundary = next(
        item
        for item in priorities
        if item["key"] == "boundary_roughness_blockage"
    )
    if boundary["rank"] != 2:
        raise AssertionError(boundary)
    if boundary["gate_status"] != module.FAIL:
        raise AssertionError(boundary)
    if "AIJ-equivalent" not in boundary["next_action"]:
        raise AssertionError(boundary)

    print("validation_gate_native_boundary_traceability_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
