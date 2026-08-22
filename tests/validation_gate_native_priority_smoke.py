#!/usr/bin/env python3
"""Smoke-test final validation gate propagation of native precondition priority."""

from __future__ import annotations

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


def main() -> int:
    module = load_gate_module()
    gates = [
        {
            "key": "native_preconditions_full_evidence",
            "status": module.FAIL,
            "evidence": "native_preconditions_gate=fail",
            "required_next_action": "Regenerate native_preconditions_audit.json.",
        },
        {
            "key": "native_baseline",
            "status": module.FAIL,
            "evidence": "native_baseline_gate=fail",
            "required_next_action": "Run native baseline.",
        },
    ]
    metrics = {
        "native_top_blocking_priority_key": "turbulent_inlet_method_and_u_k_preservation",
        "native_top_blocking_priority_reasons": "inlet_source_velocity_field_only;inlet_k_profile_gate_not_pass",
        "native_top_blocking_priority_diagnosis": (
            "The native baseline must first prove the AIJ AF U(z)/k(z) inlet."
        ),
        "native_top_blocking_priority_next_action": (
            "Fix the native setup/inlet audits before interpreting probe error."
        ),
    }

    priorities = module.build_diagnostic_priority(gates, metrics)
    native = next(
        item for item in priorities if item["key"] == "native_fluidx3d_baseline"
    )
    if "turbulent_inlet_method_and_u_k_preservation" not in native["reason"]:
        raise AssertionError(native)
    if "inlet_source_velocity_field_only" not in native["reason"]:
        raise AssertionError(native)
    if native["next_action"] != metrics["native_top_blocking_priority_next_action"]:
        raise AssertionError(native)

    print("validation_gate_native_priority_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
