#!/usr/bin/env python3
"""Smoke-test strict native inlet traceability gates."""

from __future__ import annotations

import copy
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


def passing_native_audit():
    return {
        "inlet_profile_gate": "pass",
        "inlet_u_profile_gate": "pass",
        "inlet_k_profile_gate": "pass",
        "inlet_profile_time_averaging_gate": "pass",
        "inlet_correlation_gate": "pass",
        "inlet_k_variance_gate": "pass",
        "inlet_tke_gate": "pass",
        "inlet_streamwise_variance_target_from_k": 0.42,
        "inlet_streamwise_variance_to_k_ratio": 1.0,
        "inlet_profile_af_csv_sha256_matches_expected": True,
        "inlet_profile_source_time_steps_match_runtime": True,
        "inlet_profile_source_vtk_sha256_match_runtime": True,
        "inlet_profile_source_steps_strictly_increasing": True,
        "inlet_profile_source_step_spacing_uniform": True,
        "inlet_correlation_source_time_steps_match_runtime": True,
        "inlet_correlation_source_vtk_sha256_match_runtime": True,
        "inlet_correlation_source_steps_strictly_increasing": True,
        "inlet_correlation_source_step_spacing_uniform": True,
        "inlet_source_has_streamwise_clipping_control": True,
        "inlet_source_streamwise_clipping_enabled": False,
        "inlet_source_has_legacy_hardcoded_streamwise_clipping": False,
        "expected_uref_mps": 3.928296,
        "actual_uref_mps": 3.928296,
        "expected_zref_m": 15.9,
        "af_uref_at_zref_mps": 3.928296,
        "uref_af_profile_delta_mps": 0.0,
        "metadata_uref_af_profile_delta_mps": 0.0,
        "inlet_profile_source_step_span": 20000,
        "inlet_profile_minimum_step_span": 20000,
        "inlet_correlation_source_step_span": 20000,
        "inlet_correlation_minimum_step_span": 20000,
    }


def pass_gate(module, key):
    return {
        "key": key,
        "status": module.PASS,
        "evidence": "smoke pass",
        "required_next_action": "none",
    }


def main() -> int:
    module = load_gate_module()
    ok = module.native_inlet_precondition_traceability_status(
        passing_native_audit(),
        min_avg_step_span=20000,
    )
    if not ok["ok"]:
        raise AssertionError(ok)

    bad = copy.deepcopy(passing_native_audit())
    bad["inlet_profile_source_vtk_sha256_match_runtime"] = False
    bad["inlet_correlation_source_step_span"] = 3000
    failed = module.native_inlet_precondition_traceability_status(
        bad,
        min_avg_step_span=20000,
    )
    if failed["ok"]:
        raise AssertionError(failed)
    reasons = failed["reasons"]
    if "inlet_profile_source_vtk_sha256_match_runtime_not_true:False" not in reasons:
        raise AssertionError(reasons)
    if "inlet_correlation_source_step_span_below_20000" not in reasons:
        raise AssertionError(reasons)

    uref_bad = copy.deepcopy(passing_native_audit())
    uref_bad["metadata_uref_af_profile_delta_mps"] = 0.05
    uref_failed = module.native_inlet_precondition_traceability_status(
        uref_bad,
        min_avg_step_span=20000,
        uref_tolerance=1.0e-6,
    )
    if uref_failed["ok"]:
        raise AssertionError(uref_failed)
    if "metadata_uref_af_profile_delta_mps_above_tolerance:0.05" not in uref_failed["reasons"]:
        raise AssertionError(uref_failed["reasons"])

    missing_uref = copy.deepcopy(passing_native_audit())
    missing_uref.pop("af_uref_at_zref_mps")
    missing_failed = module.native_inlet_precondition_traceability_status(
        missing_uref,
        min_avg_step_span=20000,
    )
    if missing_failed["ok"]:
        raise AssertionError(missing_failed)
    if "af_uref_at_zref_mps_missing" not in missing_failed["reasons"]:
        raise AssertionError(missing_failed["reasons"])

    missing_k_variance = copy.deepcopy(passing_native_audit())
    missing_k_variance.pop("inlet_k_variance_gate")
    missing_k_failed = module.native_inlet_precondition_traceability_status(
        missing_k_variance,
        min_avg_step_span=20000,
    )
    if missing_k_failed["ok"]:
        raise AssertionError(missing_k_failed)
    if "inlet_k_variance_gate_not_pass:missing" not in missing_k_failed["reasons"]:
        raise AssertionError(missing_k_failed["reasons"])

    missing_tke = copy.deepcopy(passing_native_audit())
    missing_tke.pop("inlet_tke_gate")
    missing_tke_failed = module.native_inlet_precondition_traceability_status(
        missing_tke,
        min_avg_step_span=20000,
    )
    if missing_tke_failed["ok"]:
        raise AssertionError(missing_tke_failed)
    if "inlet_tke_gate_not_pass:missing" not in missing_tke_failed["reasons"]:
        raise AssertionError(missing_tke_failed["reasons"])

    clipping_bad = copy.deepcopy(passing_native_audit())
    clipping_bad["inlet_source_streamwise_clipping_enabled"] = True
    clipping_bad["inlet_source_has_legacy_hardcoded_streamwise_clipping"] = True
    clipping_failed = module.native_inlet_precondition_traceability_status(
        clipping_bad,
        min_avg_step_span=20000,
    )
    if clipping_failed["ok"]:
        raise AssertionError(clipping_failed)
    for reason in [
        "inlet_source_streamwise_clipping_enabled_not_false:True",
        "inlet_source_has_legacy_hardcoded_streamwise_clipping_not_false:True",
    ]:
        if reason not in clipping_failed["reasons"]:
            raise AssertionError(clipping_failed["reasons"])

    gates = [
        pass_gate(module, key)
        for key in [
            "validation_protocol_content",
            "inlet_source_evidence",
            "inlet_turbulence",
            "paper_grade_inlet_method",
            "inlet_length_scale",
            "inlet_correlation",
            "custom_k_profile",
            "inlet_profile_preservation",
            "inlet_profile_vtk_hash_traceability",
            "inlet_correlation_vtk_hash_traceability",
            "k_preservation_or_accuracy",
        ]
    ]
    gates.append(
        {
            "key": "native_inlet_precondition_traceability",
            "status": module.FAIL,
            "evidence": failed["reasons_csv"],
            "required_next_action": "Regenerate native inlet audits.",
        }
    )
    priorities = module.build_diagnostic_priority(gates, {})
    rank1 = next(
        item
        for item in priorities
        if item["key"] == "turbulent_inlet_method_and_u_k_preservation"
    )
    if rank1["rank"] != 1:
        raise AssertionError(rank1)
    if rank1["gate_status"] != module.FAIL:
        raise AssertionError(rank1)
    if "same final VTK window" not in rank1["next_action"]:
        raise AssertionError(rank1)

    print("validation_gate_native_inlet_traceability_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
