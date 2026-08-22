#!/usr/bin/env python3
"""Smoke-test systematic-bias diagnostics list prerequisite blockers."""

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
    evidence = (
        "systematic bias is present, but prerequisite gates are not closed: "
        "time averaging and stationarity=FAIL; native FluidX3D baseline=FAIL. "
        "Treat the current result as protocol/physics debugging evidence, not solver-accuracy validation."
    )
    gates = [
        {
            "key": "systematic_bias_interpretation",
            "status": module.FAIL,
            "evidence": evidence,
            "required_next_action": "Close all prerequisite evidence gates.",
        }
    ]
    metrics = {
        "native_top_blocking_priority_key": "turbulent_inlet_method_and_u_k_preservation",
        "native_top_blocking_priority_diagnosis": "Native inlet is not distribution-consistent.",
        "native_top_blocking_priority_next_action": "Replace STG-lite or prove inlet equivalence.",
    }

    priorities = module.build_diagnostic_priority(gates, metrics)
    item = next(
        priority for priority in priorities if priority["key"] == "systematic_bias_interpretation"
    )
    blockers = module.extract_systematic_prerequisite_blocker_list(evidence)
    if blockers != [
        "time averaging and stationarity=FAIL",
        "native FluidX3D baseline=FAIL",
    ]:
        raise AssertionError(blockers)
    if "time averaging and stationarity=FAIL" not in item["reason"]:
        raise AssertionError(item)
    if "native FluidX3D baseline=FAIL" not in item["reason"]:
        raise AssertionError(item)
    if "turbulent_inlet_method_and_u_k_preservation" not in item["reason"]:
        raise AssertionError(item)
    if "Replace STG-lite or prove inlet equivalence" not in item["next_action"]:
        raise AssertionError(item)

    print("validation_gate_systematic_bias_blocker_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
