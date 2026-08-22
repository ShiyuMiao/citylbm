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

    reasons = [
        "runtime_average_step_span_too_short",
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_average_step_span_3000_below_minimum_20000",
        "probe_uref_mismatch",
        "paper_grade_boundary_source_gate_not_pass",
        "boundary_missing_evidence_field_floor_roughness_source",
        "boundary_required_support_field_outlet_reflection_check_supported_not_supported",
        "inlet_source_velocity_field_only",
        "inlet_source_uses_uncorrelated_random_rms",
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

    time_priority = next(item for item in priorities if item["key"] == "time_averaging_stationarity")
    if "runtime_average_window_frame_count_4_below_minimum_40" not in time_priority["reasons"]:
        raise AssertionError(time_priority)
    if "runtime_average_step_span_3000_below_minimum_20000" not in time_priority["reasons"]:
        raise AssertionError(time_priority)

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
