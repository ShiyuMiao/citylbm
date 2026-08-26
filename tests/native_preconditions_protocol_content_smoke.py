#!/usr/bin/env python3
"""Smoke-test native preconditions validation-protocol content gating."""

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


def protocol(module, overrides=None) -> dict:
    overrides = overrides or {}
    return {
        "Gate": "ready_for_validation_run",
        "Items": [
            {
                "Key": key,
                "Status": overrides.get(key, "pass"),
            }
            for key in module.REQUIRED_PROTOCOL_ITEM_KEYS
        ],
    }


def main() -> int:
    module = load_audit_module()

    complete = module.audit_protocol_content(protocol(module))
    if complete["gate"] != "pass":
        raise AssertionError(complete)

    empty = module.audit_protocol_content({"items": []})
    if empty["gate"] != "fail":
        raise AssertionError(empty)
    for expected in [
        "validation_protocol_audit_missing_or_empty",
        "validation_protocol_item_missing:inlet_distribution_consistency",
    ]:
        if expected not in empty["reasons"]:
            raise AssertionError((expected, empty))

    failed = module.audit_protocol_content(protocol(module, {"time_averaging": "fail"}))
    if failed["gate"] != "fail":
        raise AssertionError(failed)
    if "validation_protocol_item_fail:time_averaging" not in failed["reasons"]:
        raise AssertionError(failed)

    incomplete = module.audit_protocol_content(
        protocol(
            module,
            {
                "inlet_turbulence_k": "partial",
                "boundary_conditions": "risk",
            },
        )
    )
    if incomplete["gate"] != "fail":
        raise AssertionError(incomplete)
    for expected in [
        "validation_protocol_item_partial:inlet_turbulence_k",
        "validation_protocol_item_risk:boundary_conditions",
    ]:
        if expected not in incomplete["reasons"]:
            raise AssertionError((expected, incomplete))

    bad_gate = protocol(module)
    bad_gate["Gate"] = "not_paper_grade"
    bad_gate_audit = module.audit_protocol_content(bad_gate)
    if bad_gate_audit["gate"] != "fail":
        raise AssertionError(bad_gate_audit)
    if "validation_protocol_audit_gate_not_paper_grade:not_paper_grade" not in bad_gate_audit["reasons"]:
        raise AssertionError(bad_gate_audit)

    missing_gate = protocol(module)
    missing_gate.pop("Gate")
    missing_gate_audit = module.audit_protocol_content(missing_gate)
    if "validation_protocol_audit_gate_missing" not in missing_gate_audit["reasons"]:
        raise AssertionError(missing_gate_audit)

    priorities = module.build_native_diagnostic_priority(
        [
            "validation_protocol_item_missing:inlet_distribution_consistency",
            "inlet_source_velocity_field_only",
            "runtime_average_window_frame_count_4_below_minimum_40",
        ]
    )
    if priorities[0]["key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(priorities)
    if priorities[0]["rank"] != 0:
        raise AssertionError(priorities[0])
    protocol_priority = next(
        item for item in priorities if item["key"] == "validation_protocol_content"
    )
    if protocol_priority["rank"] != 6:
        raise AssertionError(protocol_priority)

    print("native_preconditions_protocol_content_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
