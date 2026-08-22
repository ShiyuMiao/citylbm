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

    reasons = [
        "runtime_average_step_span_too_short",
        "probe_uref_mismatch",
        "paper_grade_boundary_source_gate_not_pass",
        "inlet_source_velocity_field_only",
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

    boundary_only = module.build_native_diagnostic_priority(
        ["boundary_source_simplified", "blockage_gate_not_pass"]
    )
    if boundary_only[0]["key"] != "boundary_roughness_blockage":
        raise AssertionError(boundary_only)

    print("native_preconditions_priority_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
