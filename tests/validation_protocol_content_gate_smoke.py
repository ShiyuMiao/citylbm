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
        "Gate": "not_paper_grade",
        "Items": [
            {
                "Key": key,
                "Status": overrides.get(key, "risk" if key in {"boundary_conditions", "native_fluidx3d_baseline"} else "partial"),
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
    if "boundary_conditions" not in complete["risk_keys"]:
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
