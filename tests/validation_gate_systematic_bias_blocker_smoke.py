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

    critical_evidence = (
        "systematic bias is present, but prerequisite gates are not closed: "
        "native-CityLBM paired accuracy delta=FAIL; grid sensitivity=FAIL. "
        "Treat the current result as protocol/physics debugging evidence, not solver-accuracy validation."
    )
    critical_blockers = module.extract_systematic_prerequisite_blocker_list(critical_evidence)
    if critical_blockers != [
        "native-CityLBM paired accuracy delta=FAIL",
        "grid sensitivity=FAIL",
    ]:
        raise AssertionError(critical_blockers)
    critical_priorities = module.build_diagnostic_priority(
        [
            {
                "key": "systematic_bias_interpretation",
                "status": module.FAIL,
                "evidence": critical_evidence,
                "required_next_action": "Close all prerequisite evidence gates.",
            }
        ],
        {},
    )
    critical_item = next(
        priority
        for priority in critical_priorities
        if priority["key"] == "systematic_bias_interpretation"
    )
    if "native-CityLBM paired accuracy delta=FAIL" not in critical_item["reason"]:
        raise AssertionError(critical_item)
    if "grid sensitivity=FAIL" not in critical_item["reason"]:
        raise AssertionError(critical_item)
    if "grid-sensitivity gates" not in critical_item["next_action"]:
        raise AssertionError(critical_item)

    if not module.allow_systematic_root_cause_interpretation(True, []):
        raise AssertionError("Closed prerequisites should allow root-cause interpretation.")
    if module.allow_solver_accuracy_interpretation(True, True, []):
        raise AssertionError(
            "Systematic bias must block solver-accuracy interpretation even after prerequisites close."
        )
    if module.allow_solver_accuracy_interpretation(False, False, []):
        raise AssertionError("Failed mean-velocity accuracy must block solver-accuracy interpretation.")
    blockers = module.solver_accuracy_interpretation_blockers(True, False, ["grid sensitivity=FAIL"])
    if blockers != [
        "systematic_bias_present",
        "mean_velocity_accuracy_failed",
        "prerequisite_gates_open",
    ]:
        raise AssertionError(blockers)

    reasons = module.systematic_bias_failure_reasons(
        systematic_bias_present=True,
        inferred_systematic_bias=True,
        inferred_systematic_direction="underprediction",
        u_bias=-0.34,
        max_u_bias_ratio=0.05,
        best_scale=1.6,
        max_best_scale_deviation=0.2,
        scaled_improvement=0.45,
        min_scaled_improvement_ratio=0.25,
        failed_prerequisites=[
            "time averaging and stationarity=FAIL",
            "native FluidX3D baseline=FAIL",
        ],
        accuracy_failure_reasons=["U_R2_below_0.6:-0.2"],
        prerequisites_closed=False,
        root_cause_interpretation_allowed=False,
        solver_accuracy_allowed=False,
        solver_accuracy_blockers=[
            "systematic_bias_present",
            "mean_velocity_accuracy_failed",
            "prerequisite_gates_open",
        ],
    )
    expected_fragments = [
        "systematic_bias_present",
        "systematic_underprediction",
        "U_bias_ratio_abs_above_0.05:-0.34",
        "best_fit_scale_suggests_normalization_or_physics_gap:1.6;limit=0.2",
        "scaled_improvement_suggests_scale_like_bias:0.45;limit=0.25",
        "prerequisite_gates_open:time averaging and stationarity=FAIL;native FluidX3D baseline=FAIL",
        "prerequisite_gate_open:time averaging and stationarity=FAIL",
        "mean_velocity_accuracy_failed:U_R2_below_0.6:-0.2",
        "solver_accuracy_interpretation_blocked:systematic_bias_present;mean_velocity_accuracy_failed;prerequisite_gates_open",
        "root_cause_interpretation_blocked_until_prerequisites_close",
    ]
    for fragment in expected_fragments:
        if fragment not in reasons:
            raise AssertionError((fragment, reasons))

    residual_reasons = module.systematic_bias_failure_reasons(
        systematic_bias_present=True,
        inferred_systematic_bias=True,
        inferred_systematic_direction="underprediction",
        u_bias=-0.12,
        max_u_bias_ratio=0.05,
        best_scale=1.0,
        max_best_scale_deviation=0.2,
        scaled_improvement=0.0,
        min_scaled_improvement_ratio=0.25,
        failed_prerequisites=[],
        accuracy_failure_reasons=[],
        prerequisites_closed=True,
        root_cause_interpretation_allowed=True,
        solver_accuracy_allowed=False,
        solver_accuracy_blockers=["systematic_bias_present"],
    )
    if "residual_physics_or_protocol_bias_after_prerequisites_closed" not in residual_reasons:
        raise AssertionError(residual_reasons)
    if "prerequisite_gates_open:" in "|".join(residual_reasons):
        raise AssertionError(residual_reasons)

    clean_reasons = module.systematic_bias_failure_reasons(
        systematic_bias_present=False,
        inferred_systematic_bias=False,
        inferred_systematic_direction="",
        u_bias=0.01,
        max_u_bias_ratio=0.05,
        best_scale=None,
        max_best_scale_deviation=0.2,
        scaled_improvement=None,
        min_scaled_improvement_ratio=0.25,
        failed_prerequisites=[],
        accuracy_failure_reasons=[],
        prerequisites_closed=True,
        root_cause_interpretation_allowed=False,
        solver_accuracy_allowed=True,
        solver_accuracy_blockers=[],
    )
    if clean_reasons:
        raise AssertionError(clean_reasons)

    print("validation_gate_systematic_bias_blocker_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
