#!/usr/bin/env python3
"""Smoke-test that velocity-only inlet overrides cannot pass paper-grade gates."""

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


def passing_kwargs() -> dict:
    return {
        "empty_tunnel_pass": True,
        "inlet_source_evidence_ok": True,
        "audit_paper_grade_inlet_source_gate": "pass",
        "audit_inlet_source_distribution_consistent": True,
        "audit_inlet_source_velocity_field_only": False,
        "audit_inlet_source_comment_stripped": True,
        "audit_has_uncorrelated_random_inlet": False,
        "audit_inlet_source_turbulent_inflow_fidelity_class": "distribution_consistent_digital_filter",
        "paper_method_class_ok": True,
        "treatment_distribution_consistent": True,
        "distribution_status": "pass",
        "treatment_velocity_only": False,
    }


def main() -> int:
    module = load_gate_module()
    if not module.paper_grade_inlet_method_pass(**passing_kwargs()):
        raise AssertionError("distribution-consistent inlet should pass the inlet-method gate")

    velocity_only = passing_kwargs()
    velocity_only.update(
        {
            "audit_inlet_source_distribution_consistent": False,
            "audit_inlet_source_velocity_field_only": True,
            "audit_inlet_source_turbulent_inflow_fidelity_class": "correlated_velocity_field_only",
            "treatment_velocity_only": True,
        }
    )
    if module.paper_grade_inlet_method_pass(**velocity_only):
        raise AssertionError("velocity-field-only STG-lite must not be paper-grade")

    uncorrelated = passing_kwargs()
    uncorrelated["audit_has_uncorrelated_random_inlet"] = True
    uncorrelated["audit_inlet_source_turbulent_inflow_fidelity_class"] = "uncorrelated_rms_velocity_field_only"
    if module.paper_grade_inlet_method_pass(**uncorrelated):
        raise AssertionError("uncorrelated RMS/k forcing must not be paper-grade")

    if not module.stg_three_component_evidence_pass(
        required=True,
        has_three_component_velocity_write=True,
        has_three_component_fluctuation_evidence=True,
        has_k_driven_three_component_stg=True,
    ):
        raise AssertionError("complete three-component STG evidence should pass the source-evidence helper")
    if module.stg_three_component_evidence_pass(
        required=True,
        has_three_component_velocity_write=True,
        has_three_component_fluctuation_evidence=True,
        has_k_driven_three_component_stg=None,
    ):
        raise AssertionError("stale STG audit without k-driven three-component evidence must fail")
    if not module.stg_three_component_evidence_pass(
        required=False,
        has_three_component_velocity_write=None,
        has_three_component_fluctuation_evidence=None,
        has_k_driven_three_component_stg=None,
    ):
        raise AssertionError("non-STG distribution-consistent inlets should not require STG fields")

    print("validation_gate_velocity_only_inlet_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
