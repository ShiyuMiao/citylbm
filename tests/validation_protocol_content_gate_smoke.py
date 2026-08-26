#!/usr/bin/env python3
"""Smoke-test validation protocol content gating."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Optional


REPO = Path(__file__).resolve().parents[1]


def load_gate_module():
    path = REPO / "scripts" / "validation_gate.py"
    spec = importlib.util.spec_from_file_location("validation_gate", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protocol(module, status_overrides: Optional[dict] = None) -> dict:
    overrides = status_overrides or {}
    return {
        "Gate": "ready_for_validation_run",
        "Items": [
            {
                "Key": key,
                "Status": overrides.get(key, "pass"),
                "Evidence": "smoke",
            }
            for key in module.REQUIRED_PROTOCOL_ITEM_KEYS
        ],
    }


def main() -> int:
    module = load_gate_module()
    complete = module.audit_protocol_content(protocol(module))
    if not complete["ok"]:
        raise AssertionError(complete)
    if complete["risk_keys"] or complete["partial_keys"]:
        raise AssertionError(complete)

    empty = module.audit_protocol_content({"items": []})
    if empty["ok"]:
        raise AssertionError(empty)
    if "validation_protocol_audit_missing_or_empty" not in empty["reasons"]:
        raise AssertionError(empty)
    if "validation_protocol_item_missing:inlet_distribution_consistency" not in empty["reasons"]:
        raise AssertionError(empty)

    failed = module.audit_protocol_content(protocol(module, {"inlet_distribution_consistency": "fail"}))
    if failed["ok"]:
        raise AssertionError(failed)
    if "validation_protocol_item_fail:inlet_distribution_consistency" not in failed["reasons"]:
        raise AssertionError(failed)

    incomplete = module.audit_protocol_content(
        protocol(
            module,
            {
                "time_averaging": "partial",
                "boundary_conditions": "risk",
            },
        )
    )
    if incomplete["ok"]:
        raise AssertionError(incomplete)
    for expected in [
        "validation_protocol_item_partial:time_averaging",
        "validation_protocol_item_risk:boundary_conditions",
    ]:
        if expected not in incomplete["reasons"]:
            raise AssertionError((expected, incomplete))

    bad_gate = protocol(module)
    bad_gate["Gate"] = "diagnostic_only"
    bad_gate_result = module.audit_protocol_content(bad_gate)
    if bad_gate_result["ok"]:
        raise AssertionError(bad_gate_result)
    if "validation_protocol_audit_gate_not_paper_grade:diagnostic_only" not in bad_gate_result["reasons"]:
        raise AssertionError(bad_gate_result)

    missing_gate = protocol(module)
    missing_gate.pop("Gate")
    missing_gate_result = module.audit_protocol_content(missing_gate)
    if "validation_protocol_audit_gate_missing" not in missing_gate_result["reasons"]:
        raise AssertionError(missing_gate_result)

    gates = []
    module.add_gate(
        gates,
        "validation_protocol_content",
        module.FAIL,
        "validation_protocol_audit_missing_or_empty",
    )
    priorities = module.build_diagnostic_priority(gates, {})
    if priorities[0]["key"] != "validation_protocol_content":
        raise AssertionError(priorities)

    print("validation_protocol_content_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
