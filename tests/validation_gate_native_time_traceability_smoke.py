#!/usr/bin/env python3
"""Smoke-test native FluidX3D final-window time traceability gates."""

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
    steps = list(range(1000, 41000, 1000))
    hashes = [f"{index:064x}" for index in range(1, len(steps) + 1)]
    return {
        "native_preconditions_time_average_gate": "pass",
        "time_averaging_fidelity_class": "paper_grade_final_window_average",
        "strict_native_run_gate": "pass",
        "strict_native_run_gate_reasons": ["native_run_artifacts_pass_strict_evidence_gates"],
        "planned_frame_count_min": 40,
        "runtime_average_last_n": 40,
        "runtime_source_time_steps": steps,
        "runtime_selected_last_window": True,
        "runtime_source_vtk_sha256": hashes,
        "runtime_source_vtk_sha256_count": 40,
        "runtime_source_vtk_sha256_unique_count": 40,
        "runtime_source_step_span": 39000,
        "runtime_source_step_span_from_time_steps": 39000,
        "runtime_source_step_span_matches_time_steps": True,
        "runtime_source_steps_strictly_increasing": True,
        "runtime_source_step_spacing_uniform": True,
        "runtime_final_window_stationarity_gate": "pass",
        "runtime_final_window_mean_speed_drift_ratio": 0.01,
        "runtime_max_final_window_mean_speed_drift_ratio": 0.03,
        "runtime_mean_speed_statistics_source": "sampled_vtk",
        "runtime_mean_speed_statistics_cli_override": False,
        "runtime_mean_speed_statistics_cli_override_fields_csv": "",
        "planned_final_window_step_span": 39000,
        "planned_frame_count_shortfall_reason": "",
        "runtime_average_window_shortfall_reason": "",
        "planned_average_step_span_shortfall_reason": "",
        "runtime_average_step_span_shortfall_reason": "",
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
    ok = module.native_time_averaging_traceability_status(
        passing_native_audit(),
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if not ok["ok"]:
        raise AssertionError(ok)

    bad = copy.deepcopy(passing_native_audit())
    bad.update(
        {
            "runtime_average_last_n": 4,
            "runtime_source_time_steps": [37000, 38000, 39000, 40000],
            "runtime_source_vtk_sha256": [f"{index:064x}" for index in range(1, 5)],
            "runtime_source_vtk_sha256_count": 4,
            "runtime_source_vtk_sha256_unique_count": 4,
            "runtime_source_step_span": 3000,
            "runtime_source_step_span_from_time_steps": 3000,
            "runtime_average_window_shortfall_reason": (
                "runtime_average_window_frame_count_4_below_minimum_40"
            ),
            "runtime_average_step_span_shortfall_reason": (
                "runtime_average_step_span_3000_below_minimum_20000"
            ),
            "time_averaging_fidelity_class": "short_diagnostic_average_window",
        }
    )
    failed = module.native_time_averaging_traceability_status(
        bad,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if failed["ok"]:
        raise AssertionError(failed)
    reasons = failed["reasons_csv"]
    for expected in (
        "runtime_average_last_n_below_40",
        "runtime_source_frame_count_below_40",
        "runtime_source_step_span_below_20000",
        "runtime_average_window_shortfall_reason_present:runtime_average_window_frame_count_4_below_minimum_40",
        "time_averaging_fidelity_class_not_paper_grade:short_diagnostic_average_window",
    ):
        if expected not in reasons:
            raise AssertionError((expected, reasons))

    drifting = copy.deepcopy(passing_native_audit())
    drifting.update(
        {
            "native_preconditions_time_average_gate": "fail",
            "strict_native_run_gate": "fail",
            "strict_native_run_gate_reasons": [
                "time_averaging_gate_not_pass:diagnostic_only",
                "final_window_stationarity_gate_not_pass:diagnostic_only",
            ],
            "runtime_final_window_stationarity_gate": "diagnostic_only",
            "time_averaging_fidelity_class": "nonstationary_final_window",
            "runtime_final_window_mean_speed_drift_ratio": 0.08,
            "runtime_final_window_stationarity_gate_reasons": [
                "final_window_mean_speed_drift_ratio_above_threshold"
            ],
        }
    )
    drifting_failed = module.native_time_averaging_traceability_status(
        drifting,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if drifting_failed["ok"]:
        raise AssertionError(drifting_failed)
    drifting_reasons = drifting_failed["reasons_csv"]
    for expected in (
        "native_preconditions_time_average_gate_not_pass:fail",
        "strict_native_run_gate_not_pass:fail",
        "strict_native_run_gate_reason_present:time_averaging_gate_not_pass:diagnostic_only",
        "runtime_final_window_stationarity_gate_not_pass:diagnostic_only",
        "time_averaging_fidelity_class_not_paper_grade:nonstationary_final_window",
        "runtime_final_window_stationarity_gate_reasons_present:final_window_mean_speed_drift_ratio_above_threshold",
    ):
        if expected not in drifting_reasons:
            raise AssertionError((expected, drifting_reasons))

    stale = copy.deepcopy(passing_native_audit())
    stale.update(
        {
            "runtime_selected_last_window": False,
            "runtime_source_vtk_sha256": [f"{index:064x}" for index in range(1, 39)],
            "runtime_source_vtk_sha256_count": 38,
            "runtime_source_vtk_sha256_unique_count": 37,
            "time_averaging_fidelity_class": "stale_or_nonfinal_average_window",
        }
    )
    stale_failed = module.native_time_averaging_traceability_status(
        stale,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if stale_failed["ok"]:
        raise AssertionError(stale_failed)
    stale_reasons = stale_failed["reasons_csv"]
    for expected in (
        "runtime_selected_last_window_not_true:False",
        "runtime_source_vtk_sha256_count_below_40",
        "time_averaging_fidelity_class_not_paper_grade:stale_or_nonfinal_average_window",
        "runtime_source_vtk_sha256_count_mismatch_frame_count",
        "runtime_source_vtk_sha256_unique_count_mismatch_hash_count",
    ):
        if expected not in stale_reasons:
            raise AssertionError((expected, stale_reasons))

    cli_stats = copy.deepcopy(passing_native_audit())
    cli_stats.update(
        {
            "runtime_mean_speed_statistics_source": "cli_override",
            "runtime_mean_speed_statistics_cli_override": True,
            "runtime_mean_speed_statistics_cli_override_fields_csv": (
                "mean_speed_mps,mean_speed_stddev_mps"
            ),
        }
    )
    cli_failed = module.native_time_averaging_traceability_status(
        cli_stats,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if cli_failed["ok"]:
        raise AssertionError(cli_failed)
    cli_reasons = cli_failed["reasons_csv"]
    for expected in (
        "runtime_mean_speed_statistics_source_not_sampled_vtk:cli_override",
        "runtime_mean_speed_statistics_cli_override_not_false:True",
    ):
        if expected not in cli_reasons:
            raise AssertionError((expected, cli_reasons))

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
            "native_inlet_precondition_traceability",
            "k_preservation_or_accuracy",
            "boundary_source_evidence",
            "boundary_protocol",
            "roughness_or_precursor",
            "native_boundary_traceability",
            "run_freshness",
            "runtime_vtk_hash_traceability",
            "time_averaging",
            "metrics_time_averaging_consistency",
        ]
    ]
    gates.append(
        {
            "key": "native_time_averaging_traceability",
            "status": module.FAIL,
            "evidence": failed["reasons_csv"],
            "required_next_action": "Regenerate native final-window averaging evidence.",
        }
    )
    priorities = module.build_diagnostic_priority(gates, {})
    time_priority = next(
        item
        for item in priorities
        if item["key"] == "time_averaging_stationarity"
    )
    if time_priority["rank"] != 3:
        raise AssertionError(time_priority)
    if time_priority["gate_status"] != module.FAIL:
        raise AssertionError(time_priority)
    if "sufficiently long final-window average" not in time_priority["next_action"]:
        raise AssertionError(time_priority)

    print("validation_gate_native_time_traceability_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
