#!/usr/bin/env python3
"""Smoke-test native precondition diagnostic priority ordering."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_audit_module():
    path = REPO / "scripts" / "audit_native_preconditions.py"
    spec = importlib.util.spec_from_file_location("audit_native_preconditions", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_audit_module()
    if module.count_below_minimum_reason("runtime_average_window_frame_count", 4, 40) != (
        "runtime_average_window_frame_count_4_below_minimum_40"
    ):
        raise AssertionError("frame shortfall reason did not preserve the actual count")
    if module.count_below_minimum_reason("runtime_average_step_span", 3000, 20000) != (
        "runtime_average_step_span_3000_below_minimum_20000"
    ):
        raise AssertionError("step-span shortfall reason did not preserve the actual span")
    if module.reason_token("abs streamwise ratio; speed") != "abs_streamwise_ratio_speed":
        raise AssertionError("reason token did not normalize component labels")
    if module.count_reason("probe_uref_mismatch_count", 80) != "probe_uref_mismatch_count_80":
        raise AssertionError("count reason did not preserve the failing row count")

    passing_time_reasons = module.build_time_average_evidence_reasons(
        runtime_audit_present=True,
        runtime_reported_time_average_gate="pass",
        time_gate="pass",
        requested_frame_gate="pass",
        stationarity_gate="pass",
        stationarity_reasons=[],
        planned_frame_shortfall_reason=None,
        runtime_average_shortfall_reason=None,
        planned_step_shortfall_reason=None,
        runtime_step_shortfall_reason=None,
        runtime_avg=40,
        required_average_last_n=40,
        runtime_selected_last_window=True,
        runtime_step_span=39000,
        runtime_step_span_reported=39000,
        runtime_step_span_from_steps=39000,
        runtime_steps=list(range(1000, 41000, 1000)),
        runtime_steps_increasing=True,
        runtime_steps_uniform=True,
        runtime_hashes=[f"{idx:064x}" for idx in range(40)],
        runtime_hash_count=40,
        runtime_hash_unique_count=40,
        min_avg_frames=40,
    )
    if passing_time_reasons:
        raise AssertionError(passing_time_reasons)

    short_time_reasons = module.build_time_average_evidence_reasons(
        runtime_audit_present=True,
        runtime_reported_time_average_gate="fail",
        time_gate="pass",
        requested_frame_gate="fail",
        stationarity_gate="diagnostic_only",
        stationarity_reasons=["final_window_mean_speed_drift_ratio_above_threshold"],
        planned_frame_shortfall_reason="planned_vtk_frame_count_4_below_minimum_40",
        runtime_average_shortfall_reason="runtime_average_window_frame_count_4_below_minimum_40",
        planned_step_shortfall_reason="planned_average_step_span_3000_below_minimum_20000",
        runtime_step_shortfall_reason="runtime_average_step_span_3000_below_minimum_20000",
        runtime_avg=4,
        required_average_last_n=40,
        runtime_selected_last_window=False,
        runtime_step_span=3000,
        runtime_step_span_reported=3000,
        runtime_step_span_from_steps=3000,
        runtime_steps=[1000, 2000, 3000, 4000],
        runtime_steps_increasing=True,
        runtime_steps_uniform=True,
        runtime_hashes=[f"{idx:064x}" for idx in range(4)],
        runtime_hash_count=4,
        runtime_hash_unique_count=4,
        min_avg_frames=40,
    )
    for expected_reason in [
        "runtime_reported_time_averaging_gate_not_pass:fail",
        "runtime_requested_vtk_frame_gate_not_pass:fail",
        "runtime_final_window_stationarity_gate_not_pass:diagnostic_only",
        "runtime_average_window_shortfall:runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_step_span_shortfall:runtime_average_step_span_3000_below_minimum_20000",
        "runtime_average_window_4_does_not_match_required_40",
        "runtime_selected_last_window_not_true:False",
        "runtime_source_vtk_hash_count_4_below_minimum_40",
    ]:
        if expected_reason not in short_time_reasons:
            raise AssertionError((expected_reason, short_time_reasons))

    reasons = [
        "runtime_average_step_span_too_short",
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_average_step_span_3000_below_minimum_20000",
        "probe_uref_mismatch",
        "probe_uref_mismatch_count_80",
        "probe_out_of_tolerance_count_12",
        "probe_compared_component_speed_expected_abs_streamwise_ratio",
        "probe_official_coverage_72_of_80",
        "paper_grade_boundary_source_gate_not_pass",
        "boundary_missing_evidence_field_floor_roughness_source",
        "boundary_required_support_field_outlet_reflection_check_supported_not_supported",
        "inlet_source_velocity_field_only",
        "inlet_source_uses_uncorrelated_random_rms",
        "inlet_source_missing_three_component_fluctuation_evidence",
        "inlet_source_missing_k_driven_three_component_stg_evidence",
        "systematic_bias_after_prerequisites",
    ]
    priorities = module.build_native_diagnostic_priority(reasons)
    keys = [item["key"] for item in priorities]
    expected = [
        "turbulent_inlet_method_and_u_k_preservation",
        "boundary_roughness_blockage",
        "time_averaging_stationarity",
        "coordinate_component_normalization",
        "systematic_bias_after_prerequisites",
    ]
    if keys[:5] != expected:
        raise AssertionError(keys)

    top = priorities[0]
    if top["rank"] != 1:
        raise AssertionError(top)
    if top["key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(top)
    if "RMS/k velocity perturbations alone remain diagnostic" not in top["diagnosis"]:
        raise AssertionError(top["diagnosis"])
    if "inlet_source_uses_uncorrelated_random_rms" not in top["reasons"]:
        raise AssertionError(top)
    if "inlet_source_missing_k_driven_three_component_stg_evidence" not in top["reasons"]:
        raise AssertionError(top)

    closure = module.build_native_precondition_closure(reasons)
    expected_closure_keys = [
        "turbulent_inlet_method_and_u_k_preservation",
        "boundary_roughness_blockage",
        "time_averaging_stationarity",
        "coordinate_component_normalization",
        "grid_resolution_and_systematic_bias",
    ]
    if closure["gate"] != "fail":
        raise AssertionError(closure)
    if closure["failed_stage_keys"] != expected_closure_keys:
        raise AssertionError(closure["failed_stage_keys"])
    if closure["top_blocking_stage_key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(closure)
    if closure["top_blocking_stage_reason_count"] <= 0:
        raise AssertionError(closure)

    empty_closure = module.build_native_precondition_closure([])
    if empty_closure["gate"] != "pass":
        raise AssertionError(empty_closure)
    if empty_closure["failed_stage_count"] != 0:
        raise AssertionError(empty_closure)
    if empty_closure["closed_stage_count"] != empty_closure["stage_count"]:
        raise AssertionError(empty_closure)

    time_priority = next(item for item in priorities if item["key"] == "time_averaging_stationarity")
    if "runtime_average_window_frame_count_4_below_minimum_40" not in time_priority["reasons"]:
        raise AssertionError(time_priority)
    if "runtime_average_step_span_3000_below_minimum_20000" not in time_priority["reasons"]:
        raise AssertionError(time_priority)

    coordinate_priority = next(item for item in priorities if item["key"] == "coordinate_component_normalization")
    for reason in [
        "probe_uref_mismatch_count_80",
        "probe_out_of_tolerance_count_12",
        "probe_compared_component_speed_expected_abs_streamwise_ratio",
        "probe_official_coverage_72_of_80",
    ]:
        if reason not in coordinate_priority["reasons"]:
            raise AssertionError(coordinate_priority)

    boundary_only = module.build_native_diagnostic_priority(
        [
            "boundary_source_simplified",
            "blockage_gate_not_pass",
            "boundary_missing_evidence_field_floor_roughness_source",
        ]
    )
    if boundary_only[0]["key"] != "boundary_roughness_blockage":
        raise AssertionError(boundary_only)
    if "boundary_missing_evidence_field_floor_roughness_source" not in boundary_only[0]["reasons"]:
        raise AssertionError(boundary_only)

    print("native_preconditions_priority_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
