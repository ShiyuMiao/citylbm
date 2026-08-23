#!/usr/bin/env python3
"""Audit whether a native FluidX3D run package is a strict baseline.

This script does not run CFD and does not judge AIJ accuracy. It checks that a
native FluidX3D baseline manifest is explicit, hash-traceable, and consistent
with the current run package and final-window VTK audit before the result is
used to diagnose CityLBM accuracy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REQUIRED_NATIVE_ROLES = [
    "Native FluidX3D original setup",
    "Native FluidX3D original defines",
    "Native FluidX3D lbm.hpp",
    "Native FluidX3D lbm.cpp",
]

REQUIRED_RUN_ROLES = [
    "FluidX3D setup",
    "FluidX3D defines",
    "Case metadata",
    "Domain origin",
    "Validation protocol audit",
]

REQUIRED_BOUNDARY_SUPPORT_FIELDS = [
    "inlet_boundary_supported",
    "outlet_boundary_supported",
    "lateral_boundary_supported",
    "top_boundary_supported",
    "ground_wall_treatment_supported",
    "roughness_treatment_supported",
    "floor_roughness_source_supported",
    "blockage_source_supported",
    "fetch_clearance_source_supported",
    "outlet_reflection_check_supported",
    "side_top_boundary_check_supported",
]

REQUIRED_PROTOCOL_ITEM_KEYS = [
    "inlet_mean_profile",
    "inlet_turbulence_k",
    "inlet_turbulence_length_scale",
    "inlet_reynolds_stress_tensor",
    "inlet_temporal_sampling",
    "inlet_distribution_consistency",
    "native_fluidx3d_baseline",
    "boundary_conditions",
    "wall_roughness_model",
    "lbm_stability_scaling",
    "time_averaging",
    "wind_direction_sign",
    "coordinate_transform",
    "probe_projection",
    "normalization_basis",
    "systematic_bias_gate",
    "grid_resolution",
]

PAPER_GRADE_PROTOCOL_AUDIT_GATES = {
    "pass",
    "paper_grade",
    "paper_grade_candidate",
    "ready_for_validation_run",
}


def reason_matches_token(reason: str, token: str) -> bool:
    reason_text = str(reason or "").lower()
    token_text = str(token or "").lower()
    if not token_text:
        return False
    if "_" in token_text:
        return token_text in reason_text
    return token_text in re.split(r"[^a-z0-9]+", reason_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit native FluidX3D strict-baseline preconditions.")
    parser.add_argument("run_dir", help="Run/case directory containing native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--manifest", help="Optional explicit native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--metadata", help="case_metadata.json used for the run.")
    parser.add_argument("--runtime-audit", help="native_run_audit.json/read_vtk_audit.json for the final VTK window.")
    parser.add_argument("--inlet-source-audit", help="inlet_source_audit.json from generated setup.cpp.")
    parser.add_argument("--inlet-profile-audit", help="inlet_profile_audit.json from final-window VTK.")
    parser.add_argument("--inlet-correlation-audit", help="inlet_correlation_audit.json from final-window VTK.")
    parser.add_argument("--boundary-source-audit", help="boundary_source_audit.json from generated setup.cpp.")
    parser.add_argument("--boundary-protocol-audit", help="boundary_protocol_audit.json with AIJ-equivalent evidence.")
    parser.add_argument("--boundary-runtime-audit", help="boundary_runtime_audit.json from final-window VTK boundary faces.")
    parser.add_argument("--probe-audit", help="probe_audit.csv used for metrics.")
    parser.add_argument("--component-sensitivity-audit", help="component_sensitivity_audit.json for component/Uref checks.")
    parser.add_argument("--official", help="Official RS/probe CSV used to recompute per-probe coordinate closure.")
    parser.add_argument("--af-csv", help="Official AF CSV used by the run.")
    parser.add_argument("--case", default="", help="Expected case label.")
    parser.add_argument("--wind-direction-label", default="", help="Official wind-direction label, e.g. N.")
    parser.add_argument("--software", default="", help="Expected software label.")
    parser.add_argument("--wind-vector", default="", help="Expected wind vector, e.g. 0,-1,0.")
    parser.add_argument("--u-ref", type=float, default=None, help="Expected reference wind speed in m/s.")
    parser.add_argument("--z-ref", type=float, default=None, help="Reference height used to derive Uref from the AF profile.")
    parser.add_argument("--expected-compared-component", default="", help="Expected probe comparison component.")
    parser.add_argument("--u-ref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--expected-vtk-pattern", default="u-*.vtk")
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-avg-frames", type=int, default=40)
    parser.add_argument("--min-avg-step-span", type=int, default=20000)
    parser.add_argument("--max-estimated-mach", type=float, default=0.20)
    parser.add_argument("--min-lbm-tau", type=float, default=0.500001)
    parser.add_argument("--max-lbm-tau", type=float, default=2.0)
    parser.add_argument("--out", required=True, help="Output audit JSON.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_native_diagnostic_priority(reasons: List[str]) -> List[Dict[str, Any]]:
    reason_set = set(reasons)

    groups = [
        (
            0,
            "validation_protocol_content",
            [
                "validation_protocol",
                "protocol_item",
                "protocol_audit",
            ],
            "The validation protocol audit must be complete before native baseline preconditions can support paper-grade evidence.",
            "Regenerate validation_protocol_audit.json from the current case and verify every required protocol item has an explicit non-fail status.",
        ),
        (
            1,
            "turbulent_inlet_method_and_u_k_preservation",
            [
                "inlet",
                "custom_profile",
                "profile_k",
                "profile_u",
                "af_csv",
                "paper_grade_inlet_source",
                "distribution_consistent",
                "velocity_field_only",
                "uncorrelated",
                "random",
                "rms",
                "method_class",
                "correlation",
                "synthetic",
                "stg",
                "refresh",
                "streamwise",
                "clipping",
            ],
            "The native baseline must first prove the AIJ AF U(z)/k(z) inlet and correlated turbulence source; RMS/k velocity perturbations alone remain diagnostic.",
            "Fix the native setup/inlet audits before interpreting probe error or comparing against CityLBM.",
        ),
        (
            2,
            "boundary_roughness_blockage",
            [
                "boundary",
                "roughness",
                "blockage",
                "clearance",
                "fetch",
                "outlet_reflection",
                "side_top",
                "ground_wall",
            ],
            "Boundary-condition evidence must show AIJ-equivalent inlet, outlet, lateral/top, floor and roughness treatment.",
            "Archive structured boundary evidence and non-empty hashed support files before promoting the baseline.",
        ),
        (
            3,
            "lbm_stability_scaling",
            [
                "lbm",
                "mach",
                "tau",
                "nu",
                "viscosity",
                "reynolds",
                "velocity_set",
                "les",
                "smagorinsky",
                "stability",
                "solver",
            ],
            "Native FluidX3D scaling must keep Mach, tau/nu, Reynolds, velocity set, LES model and solver stability logs inside interpretable ranges.",
            "Fix LBM scaling/runtime statistics before interpreting residual bias or grid effects.",
        ),
        (
            4,
            "time_averaging_stationarity",
            [
                "runtime",
                "strict_native",
                "strict_native_run",
                "time",
                "step_span",
                "step_spacing",
                "frame_count",
                "average",
                "actual_vtk",
                "vtk_output",
                "vtk_hash",
                "fresh",
                "freshness",
                "source_step",
            ],
            "The final VTK window must be fresh, hash-traceable and long enough for a stable mean-flow comparison.",
            "Rerun or re-audit with the required final-window frame count and solver-step span.",
        ),
        (
            5,
            "coordinate_component_normalization",
            [
                "probe",
                "component",
                "normalization",
                "wind_vector",
                "uref",
                "official",
                "coordinate",
                "compared",
            ],
            "Probe IDs, coordinates, wind sign, compared component and Uref must match the official RS table.",
            "Fix the probe audit and component/Uref sensitivity audit before interpreting residual bias.",
        ),
        (
            6,
            "systematic_bias_after_prerequisites",
            [
                "systematic",
                "bias",
                "r2",
                "slope",
                "intercept",
                "underprediction",
                "overprediction",
            ],
            "Systematic bias is interpretable only after the previous protocol gates are closed.",
            "Treat remaining bias as a physics/protocol issue and compare paired native FluidX3D and CityLBM runs.",
        ),
    ]
    priorities: List[Dict[str, Any]] = []
    matched: set[str] = set()
    for rank, key, tokens, diagnosis, action in groups:
        matching_reasons = sorted(
            reason for reason in reason_set if any(reason_matches_token(reason, token) for token in tokens)
        )
        matched.update(matching_reasons)
        if matching_reasons:
            priorities.append(
                {
                    "rank": rank,
                    "key": key,
                    "reason_count": len(matching_reasons),
                    "reasons": matching_reasons,
                    "diagnosis": diagnosis,
                    "next_action": action,
                }
            )
    unmatched = sorted(reason_set - matched)
    if unmatched:
        priorities.append(
            {
                "rank": 7,
                "key": "other_precondition_evidence",
                "reason_count": len(unmatched),
                "reasons": unmatched,
                "diagnosis": "Additional traceability or packaging preconditions remain open.",
                "next_action": "Close these residual audit reasons after the five primary CFD-validation risks are handled.",
            }
        )
    return priorities


def build_native_precondition_closure(reasons: List[str]) -> Dict[str, Any]:
    reason_set = set(reasons)
    stage_specs = [
        (
            0,
            "validation_protocol_content",
            [
                "validation_protocol",
                "protocol_item",
                "protocol_audit",
            ],
            "Complete validation protocol audit.",
        ),
        (
            1,
            "turbulent_inlet_method_and_u_k_preservation",
            [
                "inlet",
                "custom_profile",
                "profile_k",
                "profile_u",
                "af_csv",
                "paper_grade_inlet_source",
                "distribution_consistent",
                "velocity_field_only",
                "uncorrelated",
                "random",
                "rms",
                "method_class",
                "correlation",
                "synthetic",
                "stg",
                "refresh",
                "sampling",
                "streamwise",
                "clipping",
            ],
            "Prove AF U(z)/k(z), correlated turbulent inlet and distribution-consistent inlet treatment.",
        ),
        (
            2,
            "boundary_roughness_blockage",
            [
                "boundary",
                "roughness",
                "blockage",
                "clearance",
                "fetch",
                "outlet_reflection",
                "side_top",
                "ground_wall",
            ],
            "Prove AIJ-equivalent boundary, floor roughness, fetch, clearance and blockage treatment.",
        ),
        (
            3,
            "lbm_stability_scaling",
            [
                "lbm",
                "mach",
                "tau",
                "nu",
                "viscosity",
                "reynolds",
                "velocity_set",
                "les",
                "smagorinsky",
                "stability",
                "solver",
            ],
            "Prove LBM Mach/tau/nu/Re, velocity set, LES model and solver log stability.",
        ),
        (
            4,
            "time_averaging_stationarity",
            [
                "runtime",
                "strict_native",
                "strict_native_run",
                "time",
                "step_span",
                "step_spacing",
                "frame_count",
                "average",
                "actual_vtk",
                "vtk_output",
                "vtk_hash",
                "fresh",
                "freshness",
                "source_step",
            ],
            "Prove fresh final-window VTK hashes, frame count, uniform spacing and solver-step span.",
        ),
        (
            5,
            "coordinate_component_normalization",
            [
                "probe",
                "component",
                "normalization",
                "wind_vector",
                "uref",
                "official",
                "coordinate",
                "compared",
            ],
            "Prove RS probe IDs/coordinates, wind sign, compared component and Uref normalization.",
        ),
        (
            6,
            "grid_resolution_and_systematic_bias",
            [
                "grid",
                "resolution",
                "dx",
                "systematic",
                "bias",
                "r2",
                "slope",
                "intercept",
                "underprediction",
                "overprediction",
            ],
            "Only interpret grid sensitivity and systematic bias after protocol stages 0-4 are closed.",
        ),
    ]
    stages: List[Dict[str, Any]] = []
    for rank, key, tokens, required_evidence in stage_specs:
        stage_reasons = sorted(
            reason for reason in reason_set if any(reason_matches_token(reason, token) for token in tokens)
        )
        stages.append(
            {
                "rank": rank,
                "key": key,
                "status": "pass" if not stage_reasons else "fail",
                "reason_count": len(stage_reasons),
                "reasons": stage_reasons,
                "required_evidence": required_evidence,
            }
        )
    failed_stages = [stage for stage in stages if stage["status"] != "pass"]
    top_stage = failed_stages[0] if failed_stages else {}
    return {
        "gate": "pass" if not failed_stages else "fail",
        "stage_count": len(stages),
        "closed_stage_count": len(stages) - len(failed_stages),
        "failed_stage_count": len(failed_stages),
        "failed_stage_keys": [stage["key"] for stage in failed_stages],
        "failed_stage_keys_csv": ";".join(stage["key"] for stage in failed_stages),
        "top_blocking_stage_key": top_stage.get("key", ""),
        "top_blocking_stage_rank": top_stage.get("rank"),
        "top_blocking_stage_reason_count": top_stage.get("reason_count"),
        "top_blocking_stage_reasons": top_stage.get("reasons", []),
        "top_blocking_stage_reasons_csv": ";".join(
            str(reason) for reason in top_stage.get("reasons", [])
        ),
        "stages": stages,
    }


def build_native_rerun_prescription(
    priorities: List[Dict[str, Any]],
    closure: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
    average_last_n: int,
) -> Dict[str, Any]:
    top = priorities[0] if priorities else {}
    top_key = str(top.get("key") or "").strip()
    top_diagnosis = str(top.get("diagnosis") or "").strip()
    top_action = str(top.get("next_action") or "").strip()
    accuracy_allowed = not priorities and str(closure.get("gate") or "").lower() == "pass"

    prescriptions = {
        "validation_protocol_content": (
            "regenerate_protocol_audit_before_cfd",
            [
                "rerun_validation_protocol_audit_from_current_case",
                "record_non_fail_status_for_all_required_protocol_items",
                "hash_current_setup_metadata_domain_and_geometry",
            ],
        ),
        "turbulent_inlet_method_and_u_k_preservation": (
            "native_empty_tunnel_inlet_preservation_first",
            [
                "use_customtable_af_u_and_k_profile",
                "provide_distribution_consistent_dfm_sem_or_precursor_inlet_or_archive_explicit_velocity_only_diagnostic_label",
                "prove_final_window_inlet_u_profile_gate_pass",
                "prove_final_window_inlet_k_profile_gate_pass",
                "prove_inlet_correlation_and_tke_gates_pass",
                "prove_planned_synthetic_inlet_sampling_gate_pass",
                "archive_inlet_source_profile_correlation_audits_with_matching_setup_and_vtk_hashes",
            ],
        ),
        "boundary_roughness_blockage": (
            "native_boundary_equivalence_before_probe_accuracy",
            [
                "document_aij_equivalent_inlet_outlet_side_top_and_floor_treatments",
                "archive_non_empty_hashed_boundary_support_files",
                "prove_roughness_fetch_clearance_blockage_outlet_reflection_and_side_top_checks",
                "run_boundary_runtime_audit_on_the_same_final_vtk_window",
            ],
        ),
        "lbm_stability_scaling": (
            "native_lbm_stability_scaling_audit_first",
            [
                "keep_target_max_profile_velocity_lbm_at_or_below_0.1",
                "prove_estimated_max_profile_mach_below_threshold",
                "prove_lbm_tau_and_nu_are_valid",
                "record_physical_viscosity_and_estimated_reynolds_number",
                "record_velocity_set_and_les_or_subgrid_model",
                "archive_solver_log_with_no_stability_warnings",
            ],
        ),
        "time_averaging_stationarity": (
            "rerun_long_final_window_average",
            [
                f"save_at_least_{min_avg_frames}_final_window_vtk_frames",
                f"span_at_least_{min_avg_step_span}_solver_steps_in_final_window",
                f"set_average_last_n_to_{average_last_n}",
                "use_strictly_increasing_uniform_time_steps",
                "hash_every_selected_final_window_vtk_frame",
                "prove_final_window_stationarity_gate_pass",
            ],
        ),
        "coordinate_component_normalization": (
            "repair_probe_mapping_component_and_uref_audits",
            [
                "match_all_official_probe_ids_and_coordinates",
                "keep_probe_projection_distance_within_tolerance",
                "compare_the_declared_streamwise_or_speed_component_consistently",
                "verify_wind_vector_sign_and_uref_against_af_profile",
                "rerun_component_sensitivity_on_the_same_vtk_window",
            ],
        ),
        "systematic_bias_after_prerequisites": (
            "paired_native_citylbm_physics_diagnosis",
            [
                "compare_paired_native_fluidx3d_and_citylbm_runs_with_identical_inputs",
                "run_grid_sensitivity_with_matched_coarser_or_finer_dx",
                "treat_remaining_bias_as_physics_or_protocol_after_all_preconditions_pass",
            ],
        ),
        "other_precondition_evidence": (
            "close_residual_traceability_gaps",
            [
                "inspect_unmatched_native_precondition_reasons",
                "archive_missing_hashes_manifests_or_audit_files",
            ],
        ),
    }
    experiment, controls = prescriptions.get(
        top_key,
        (
            "accuracy_interpretation_ready" if accuracy_allowed else "inspect_native_precondition_audit",
            [] if accuracy_allowed else ["close_native_precondition_reasons_before_accuracy_interpretation"],
        ),
    )
    summary = (
        "All native precondition stages are closed; accuracy metrics can be interpreted against the configured gates."
        if accuracy_allowed
        else f"Do not interpret probe accuracy yet. Next experiment: {experiment}. {top_diagnosis or top_action}"
    )
    return {
        "gate": "pass" if accuracy_allowed else "fail",
        "top_key": top_key,
        "experiment": experiment,
        "required_controls": controls,
        "required_controls_csv": ";".join(controls),
        "minimum_final_window": (
            f"average_last_n={average_last_n};"
            f"min_avg_frames={min_avg_frames};"
            f"min_avg_step_span={min_avg_step_span}"
        ),
        "accuracy_interpretation_allowed": accuracy_allowed,
        "summary": summary,
    }


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def load_protocol_items(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["Items", "items", "ProtocolItems", "protocol_items"]:
        value = audit.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def audit_protocol_content(
    audit: Dict[str, Any],
    required_keys: Iterable[str] = REQUIRED_PROTOCOL_ITEM_KEYS,
) -> Dict[str, Any]:
    items = load_protocol_items(audit)
    statuses = {
        str(item.get("Key") or item.get("key") or "").strip(): str(
            item.get("Status") or item.get("status") or ""
        ).strip().lower()
        for item in items
        if str(item.get("Key") or item.get("key") or "").strip()
    }
    required = list(required_keys)
    audit_gate = str(audit.get("Gate") or audit.get("gate") or "").strip().lower()
    missing = [key for key in required if key not in statuses]
    missing_status = [key for key in required if key in statuses and not statuses[key]]
    failed = [key for key, status in statuses.items() if status == "fail"]
    risk = [key for key, status in statuses.items() if status == "risk"]
    partial = [key for key, status in statuses.items() if status == "partial"]
    reasons: List[str] = []
    if not audit or not items:
        reasons.append("validation_protocol_audit_missing_or_empty")
    reasons.extend(f"validation_protocol_item_missing:{key}" for key in missing)
    reasons.extend(f"validation_protocol_item_status_missing:{key}" for key in missing_status)
    reasons.extend(f"validation_protocol_item_fail:{key}" for key in failed)
    reasons.extend(f"validation_protocol_item_risk:{key}" for key in risk)
    reasons.extend(f"validation_protocol_item_partial:{key}" for key in partial)
    if not audit_gate:
        reasons.append("validation_protocol_audit_gate_missing")
    elif audit_gate not in PAPER_GRADE_PROTOCOL_AUDIT_GATES:
        reasons.append(f"validation_protocol_audit_gate_not_paper_grade:{audit_gate}")
    return {
        "gate": "pass" if not reasons else "fail",
        "item_count": len(items),
        "required_item_count": len(required),
        "audit_gate": audit_gate,
        "allowed_audit_gates": sorted(PAPER_GRADE_PROTOCOL_AUDIT_GATES),
        "missing_keys": missing,
        "missing_status_keys": missing_status,
        "failed_keys": failed,
        "risk_keys": risk,
        "partial_keys": partial,
        "statuses": statuses,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def first_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def protocol_item_status(protocol_content_audit: Dict[str, Any], key: str) -> str:
    statuses = protocol_content_audit.get("statuses")
    if isinstance(statuses, dict):
        return str(statuses.get(key) or "").strip().lower()
    return ""


def build_lbm_stability_reasons(
    *,
    target_velocity_lbm: Optional[float],
    estimated_mach: Optional[float],
    lbm_tau: Optional[float],
    lbm_nu: Optional[float],
    physical_viscosity: Optional[float],
    estimated_reynolds: Optional[float],
    velocity_set: str,
    les_model: str,
    solver_warnings: str,
    lbm_stability_gate: str,
    protocol_status: str,
    max_estimated_mach: float,
    min_lbm_tau: float,
    max_lbm_tau: float,
) -> List[str]:
    reasons: List[str] = []
    if target_velocity_lbm is None:
        reasons.append("target_max_profile_velocity_lbm_missing")
    elif target_velocity_lbm > 0.1:
        reasons.append(f"target_max_profile_velocity_lbm_above_0.1:{target_velocity_lbm}")
    if estimated_mach is None:
        reasons.append("estimated_max_profile_mach_missing")
    elif estimated_mach > max_estimated_mach:
        reasons.append(f"estimated_max_profile_mach_above_{max_estimated_mach}:{estimated_mach}")
    if lbm_tau is None:
        reasons.append("lbm_tau_missing")
    elif not (min_lbm_tau <= lbm_tau <= max_lbm_tau):
        reasons.append(f"lbm_tau_outside_{min_lbm_tau}_{max_lbm_tau}:{lbm_tau}")
    if lbm_nu is None:
        reasons.append("lbm_nu_missing")
    elif lbm_nu <= 0.0:
        reasons.append(f"lbm_nu_not_positive:{lbm_nu}")
    if physical_viscosity is None:
        reasons.append("physical_viscosity_m2s_missing")
    elif physical_viscosity <= 0.0:
        reasons.append(f"physical_viscosity_m2s_not_positive:{physical_viscosity}")
    if estimated_reynolds is None:
        reasons.append("estimated_reynolds_number_missing")
    elif estimated_reynolds <= 0.0:
        reasons.append(f"estimated_reynolds_number_not_positive:{estimated_reynolds}")
    if not str(velocity_set or "").strip():
        reasons.append("velocity_set_missing")
    if not str(les_model or "").strip():
        reasons.append("les_model_missing")

    normalized_warnings = str(solver_warnings or "").strip().lower()
    if normalized_warnings not in {
        "none",
        "no_warnings",
        "no_stability_warnings",
        "pass",
        "solver_log_no_stability_warnings",
    }:
        reasons.append(f"solver_stability_warnings_not_clear:{normalized_warnings or 'missing'}")

    normalized_gate = str(lbm_stability_gate or "").strip().lower()
    if normalized_gate not in {"pass", "solver_log_no_stability_warnings", "runtime_statistics_archived"}:
        reasons.append(f"runtime_lbm_stability_gate_not_pass:{normalized_gate or 'missing'}")

    if str(protocol_status or "").strip().lower() in {"", "fail"}:
        reasons.append(f"validation_protocol_lbm_stability_scaling_not_closed:{protocol_status or 'missing'}")
    return reasons


def read_csv_rows(path: Optional[Path]) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Optional[Path]) -> str:
    if not path or not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def component_sensitivity_input_hash_traceability(
    component_sensitivity_audit: Dict[str, Any],
    probe_audit_sha256: str,
    official_sha256: str,
) -> Dict[str, Any]:
    """Check that component sensitivity was generated from current probe/official inputs."""
    reasons: List[str] = []
    component_probe_sha = str(component_sensitivity_audit.get("probe_audit_sha256") or "").strip().lower()
    component_official_sha = str(component_sensitivity_audit.get("official_sha256") or "").strip().lower()
    probe_matches: Optional[bool] = None
    official_matches: Optional[bool] = None

    if component_sensitivity_audit and probe_audit_sha256:
        probe_matches = component_probe_sha == probe_audit_sha256
        if not component_probe_sha:
            reasons.append("component_sensitivity_probe_audit_hash_missing")
        elif not probe_matches:
            reasons.append("component_sensitivity_probe_audit_hash_mismatch")

    if component_sensitivity_audit and official_sha256:
        official_matches = component_official_sha == official_sha256
        if not component_official_sha:
            reasons.append("component_sensitivity_official_hash_missing")
        elif not official_matches:
            reasons.append("component_sensitivity_official_hash_mismatch")

    return {
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "probe_audit_sha256": probe_audit_sha256,
        "official_sha256": official_sha256,
        "component_probe_audit_sha256": component_probe_sha,
        "component_official_sha256": component_official_sha,
        "probe_audit_sha256_matches_current": probe_matches,
        "official_sha256_matches_current": official_matches,
    }


def find_first(base: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        for root in [base, base / "output", base / "src", base / "validation_chain"]:
            candidate = root / name
            if candidate.exists():
                return candidate.resolve()
    parent = base.parent
    if parent != base:
        for name in names:
            candidate = parent / name
            if candidate.exists():
                return candidate.resolve()
    return None


def as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "pass"}:
            return True
        if text in {"false", "0", "no", "fail"}:
            return False
    return None


def as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_vector(text: str) -> Optional[Tuple[float, float, float]]:
    cleaned = str(text or "").strip().strip("()[]")
    if not cleaned:
        return None
    parts = [part.strip() for part in cleaned.replace(";", ",").split(",") if part.strip()]
    if len(parts) != 3:
        parts = [part.strip() for part in cleaned.split() if part.strip()]
    if len(parts) != 3:
        return None
    values = [as_float(part) for part in parts]
    if any(value is None for value in values):
        return None
    return (values[0], values[1], values[2])  # type: ignore[index]


def unit_vector(vector: Optional[Tuple[float, float, float]]) -> Optional[Tuple[float, float, float]]:
    if vector is None:
        return None
    norm = math.sqrt(sum(component * component for component in vector))
    if norm <= 1.0e-12:
        return None
    return tuple(component / norm for component in vector)


def vector_delta(a: Optional[Tuple[float, float, float]], b: Optional[Tuple[float, float, float]]) -> Optional[float]:
    au = unit_vector(a)
    bu = unit_vector(b)
    if au is None or bu is None:
        return None
    return math.sqrt(sum((left - right) * (left - right) for left, right in zip(au, bu)))


def manifest_record(manifest: Dict[str, Any], role: str) -> Dict[str, Any]:
    records = manifest.get("RequiredSourceFiles", [])
    if not isinstance(records, list):
        return {}
    for record in records:
        if isinstance(record, dict) and str(record.get("Role") or "").strip() == role:
            return record
    return {}


def resolve_record_path(record: Dict[str, Any], manifest_path: Optional[Path]) -> Optional[Path]:
    raw_path = str(record.get("Path") or "").strip()
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and manifest_path is not None:
        path = manifest_path.parent / path
    return path.resolve()


def audit_role(manifest: Dict[str, Any], manifest_path: Optional[Path], role: str) -> Dict[str, Any]:
    record = manifest_record(manifest, role)
    declared_sha = str(record.get("Sha256") or "").strip().lower()
    declared_exists = as_bool(record.get("Exists"))
    declared_algorithm = str(record.get("HashAlgorithm") or "").strip().upper()
    path = resolve_record_path(record, manifest_path)
    actual_sha = sha256_file(path)
    reasons: List[str] = []
    if not record:
        reasons.append("record_missing")
    if declared_exists is not True:
        reasons.append("exists_not_true")
    if declared_algorithm != "SHA256":
        reasons.append("hash_algorithm_not_sha256")
    if not declared_sha:
        reasons.append("sha256_missing")
    if path is None or not path.exists():
        reasons.append("path_missing")
    if declared_sha and actual_sha and declared_sha != actual_sha:
        reasons.append("sha256_mismatch")
    return {
        "role": role,
        "path": str(path) if path else "",
        "declared_exists": declared_exists,
        "declared_sha256": declared_sha,
        "actual_sha256": actual_sha,
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
    }


def shared_wind_vector(shared: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    raw = shared.get("WindDirectionUnitVector")
    if isinstance(raw, dict):
        values = [as_float(raw.get(key)) for key in ["X", "Y", "Z"]]
        if all(value is not None for value in values):
            return (values[0], values[1], values[2])  # type: ignore[index]
    if isinstance(raw, str):
        return parse_vector(raw)
    return None


def expected_final_window_span(time_steps: Optional[int], save_interval: Optional[int], save_start_step: Optional[int], average_last_n: int) -> Optional[int]:
    if time_steps is None or save_interval is None or save_interval <= 0:
        return None
    first = save_start_step if save_start_step is not None else save_interval
    steps = list(range(first, time_steps + 1, save_interval))
    if not steps:
        return None
    final = steps[-max(1, average_last_n) :]
    if len(final) < 2:
        return 0
    return final[-1] - final[0]


def source_step_span_from_steps(steps: List[int]) -> Optional[int]:
    if len(steps) < 2:
        return None
    ordered = sorted(steps)
    return ordered[-1] - ordered[0]


def source_steps_strictly_increasing(steps: List[int]) -> bool:
    return len(steps) >= 2 and all(right > left for left, right in zip(steps, steps[1:]))


def source_steps_uniformly_spaced(steps: List[int]) -> bool:
    if len(steps) < 2:
        return False
    spacings = [right - left for left, right in zip(steps, steps[1:])]
    return all(spacing > 0 for spacing in spacings) and len(set(spacings)) == 1


def count_below_minimum_reason(label: str, value: Optional[int], minimum: int) -> str:
    if value is None:
        return f"{label}_missing"
    if value < minimum:
        return f"{label}_{value}_below_minimum_{minimum}"
    return ""


def reason_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    token = "".join(char if char.isascii() and (char.isalnum() or char in "._+-") else "_" for char in text)
    token = "_".join(part for part in token.split("_") if part)
    return token or "missing"


def count_reason(label: str, count: int) -> str:
    return f"{label}_{count}"


def build_probe_official_height_gate(
    official_expected_z: Any,
    official_z_match_count: Optional[int],
    official_z_mismatch_count: Optional[int],
    official_probe_set_row_count: Optional[int],
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not str(official_expected_z or "").strip():
        reasons.append("official_expected_z_missing")
    if official_z_match_count is None:
        reasons.append("official_z_match_count_missing")
    if official_z_mismatch_count is None:
        reasons.append("official_z_mismatch_count_missing")
    elif official_z_mismatch_count > 0:
        reasons.append(f"official_z_mismatch_count:{official_z_mismatch_count}")
    if (
        official_probe_set_row_count is not None
        and official_z_match_count is not None
        and official_z_match_count != official_probe_set_row_count
    ):
        reasons.append(
            f"official_z_match_count_{official_z_match_count}_does_not_match_official_row_count_{official_probe_set_row_count}"
        )
    return {
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def split_scalar_list(value: Any, separators: Tuple[str, ...] = (",", ";")) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    for separator in separators[1:]:
        text = text.replace(separator, separators[0])
    return [part.strip() for part in text.split(separators[0]) if part.strip()]


def parse_int_list(value: Any) -> List[int]:
    output: List[int] = []
    for item in split_scalar_list(value):
        parsed = as_int(item)
        if parsed is not None:
            output.append(parsed)
    return output


def parse_hash_list(value: Any) -> List[str]:
    return [item.lower() for item in split_scalar_list(value) if item]


def audit_source_steps(audit: Dict[str, Any]) -> List[int]:
    return parse_int_list(audit.get("source_time_steps") or audit.get("source_time_steps_csv"))


def audit_source_hashes(audit: Dict[str, Any]) -> List[str]:
    hashes = parse_hash_list(audit.get("source_vtk_sha256") or audit.get("source_vtk_sha256_csv"))
    if hashes:
        return hashes
    records = audit.get("selected_vtk_files")
    if isinstance(records, list):
        return [
            str(record.get("sha256") or "").strip().lower()
            for record in records
            if isinstance(record, dict) and str(record.get("sha256") or "").strip()
        ]
    return []


def step_hash_pairs_from_steps_hashes(steps: List[int], hashes: List[str]) -> List[Tuple[int, str]]:
    if not steps or not hashes or len(steps) != len(hashes):
        return []
    return [(step, digest) for step, digest in zip(steps, hashes)]


def audit_source_step_hash_pairs(audit: Dict[str, Any]) -> List[Tuple[int, str]]:
    for key in ["selected_vtk_files", "freshness_selected_vtk_files", "vtk_files"]:
        records = audit.get(key)
        if not isinstance(records, list):
            continue
        pairs: List[Tuple[int, str]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            step = as_int(
                record.get("time_step")
                or record.get("TimeStep")
                or record.get("timestep")
                or record.get("step")
            )
            digest = str(
                record.get("sha256")
                or record.get("Sha256")
                or record.get("SHA256")
                or record.get("hash")
                or ""
            ).strip().lower()
            if step is not None and digest:
                pairs.append((step, digest))
        if pairs:
            return sorted(pairs)
    return step_hash_pairs_from_steps_hashes(audit_source_steps(audit), audit_source_hashes(audit))


def runtime_source_hashes(runtime_audit: Dict[str, Any], runtime_steps: List[int]) -> List[str]:
    records = runtime_audit.get("freshness_selected_vtk_files")
    if isinstance(records, list) and records:
        return [
            str(record.get("sha256") or "").strip().lower()
            for record in records
            if isinstance(record, dict) and str(record.get("sha256") or "").strip()
        ]
    records = runtime_audit.get("vtk_files")
    if not isinstance(records, list):
        return []
    selected_steps = set(runtime_steps)
    output: List[Tuple[int, str]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        step = as_int(record.get("time_step"))
        digest = str(record.get("sha256") or "").strip().lower()
        if step is not None and step in selected_steps and digest:
            output.append((step, digest))
    return [digest for _, digest in sorted(output)]


def append_source_window_reasons(
    reasons: List[str],
    label: str,
    audit: Dict[str, Any],
    runtime_steps: List[int],
    runtime_hashes: List[str],
) -> Dict[str, Any]:
    audit_steps = audit_source_steps(audit)
    audit_hashes = audit_source_hashes(audit)
    audit_step_hash_pairs = audit_source_step_hash_pairs(audit)
    runtime_step_hash_pairs = step_hash_pairs_from_steps_hashes(runtime_steps, runtime_hashes)
    steps_match = bool(runtime_steps) and audit_steps == runtime_steps
    hashes_match = bool(runtime_hashes) and bool(audit_hashes) and set(audit_hashes) == set(runtime_hashes)
    step_hash_pairs_match = bool(runtime_step_hash_pairs) and audit_step_hash_pairs == runtime_step_hash_pairs
    if audit:
        if not runtime_steps:
            reasons.append(f"{label}_runtime_source_time_steps_missing")
        elif not audit_steps:
            reasons.append(f"{label}_source_time_steps_missing")
        elif not steps_match:
            reasons.append(f"{label}_source_time_steps_mismatch")
        if not runtime_hashes:
            reasons.append(f"{label}_runtime_source_vtk_hashes_missing")
        elif not audit_hashes:
            reasons.append(f"{label}_source_vtk_hashes_missing")
        elif not hashes_match:
            reasons.append(f"{label}_source_vtk_hashes_mismatch")
        if not step_hash_pairs_match:
            reasons.append(f"{label}_source_step_hash_pairs_mismatch")
    return {
        f"{label}_source_time_steps": audit_steps,
        f"{label}_source_time_steps_match_runtime": steps_match,
        f"{label}_source_vtk_sha256": audit_hashes,
        f"{label}_source_vtk_sha256_match_runtime": hashes_match,
        f"{label}_source_step_hash_pairs_match_runtime": step_hash_pairs_match,
    }


def append_source_step_span_reasons(
    reasons: List[str],
    label: str,
    audit: Dict[str, Any],
    min_step_span: int,
) -> Dict[str, Any]:
    audit_steps = audit_source_steps(audit)
    reported = as_int(audit.get("source_step_span"))
    computed = source_step_span_from_steps(audit_steps)
    effective = computed if computed is not None else reported
    matches_steps = reported is not None and computed is not None and reported == computed
    increasing = source_steps_strictly_increasing(audit_steps)
    uniform = source_steps_uniformly_spaced(audit_steps)
    reported_increasing = as_bool(audit.get("source_steps_strictly_increasing"))
    reported_uniform = as_bool(audit.get("source_step_spacing_uniform"))
    if audit:
        if reported is None:
            reasons.append(f"{label}_source_step_span_missing")
        if computed is None:
            reasons.append(f"{label}_source_time_steps_span_missing")
        elif reported is not None and reported != computed:
            reasons.append(f"{label}_source_step_span_mismatch_time_steps")
        if not increasing:
            reasons.append(f"{label}_source_steps_not_strictly_increasing")
        if not uniform:
            reasons.append(f"{label}_source_step_spacing_not_uniform")
        if reported_increasing is not None and reported_increasing != increasing:
            reasons.append(f"{label}_source_steps_increasing_flag_mismatch")
        if reported_uniform is not None and reported_uniform != uniform:
            reasons.append(f"{label}_source_step_spacing_flag_mismatch")
    if effective is None or effective < min_step_span:
        reasons.append(f"{label}_step_span_too_short")
    return {
        f"{label}_reported_source_step_span": reported,
        f"{label}_source_step_span_from_time_steps": computed,
        f"{label}_source_step_span": effective,
        f"{label}_source_step_span_matches_time_steps": matches_steps,
        f"{label}_source_steps_strictly_increasing": increasing,
        f"{label}_source_step_spacing_uniform": uniform,
        f"{label}_reported_source_steps_strictly_increasing": reported_increasing,
        f"{label}_reported_source_step_spacing_uniform": reported_uniform,
    }


def build_time_average_evidence_reasons(
    *,
    runtime_audit_present: bool,
    runtime_reported_time_average_gate: str,
    time_gate: str,
    requested_frame_gate: str,
    stationarity_gate: str,
    stationarity_reasons: List[str],
    planned_frame_shortfall_reason: Optional[str],
    runtime_average_shortfall_reason: Optional[str],
    planned_step_shortfall_reason: Optional[str],
    runtime_step_shortfall_reason: Optional[str],
    runtime_avg: Optional[int],
    required_average_last_n: int,
    runtime_selected_last_window: Optional[bool],
    runtime_step_span: Optional[int],
    runtime_step_span_reported: Optional[int],
    runtime_step_span_from_steps: Optional[int],
    runtime_steps: List[int],
    runtime_steps_increasing: bool,
    runtime_steps_uniform: bool,
    runtime_hashes: List[str],
    runtime_hash_count: int,
    runtime_hash_unique_count: int,
    min_avg_frames: int,
) -> List[str]:
    evidence_reasons: List[str] = []
    if not runtime_audit_present:
        evidence_reasons.append("runtime_audit_missing")
    if runtime_reported_time_average_gate != "pass":
        evidence_reasons.append(
            f"runtime_reported_time_averaging_gate_not_pass:{runtime_reported_time_average_gate}"
        )
    if time_gate != "pass":
        evidence_reasons.append(f"runtime_time_averaging_gate_not_pass:{time_gate or 'missing'}")
    if requested_frame_gate != "pass":
        evidence_reasons.append(
            f"runtime_requested_vtk_frame_gate_not_pass:{requested_frame_gate or 'missing'}"
        )
    if stationarity_gate != "pass":
        evidence_reasons.append(
            f"runtime_final_window_stationarity_gate_not_pass:{stationarity_gate or 'missing'}"
        )
    for reason in stationarity_reasons:
        evidence_reasons.append(f"runtime_final_window_stationarity_reason:{reason}")
    if planned_frame_shortfall_reason:
        evidence_reasons.append(f"planned_frame_shortfall:{planned_frame_shortfall_reason}")
    if runtime_average_shortfall_reason:
        evidence_reasons.append(f"runtime_average_window_shortfall:{runtime_average_shortfall_reason}")
    if planned_step_shortfall_reason:
        evidence_reasons.append(f"planned_step_span_shortfall:{planned_step_shortfall_reason}")
    if runtime_step_shortfall_reason:
        evidence_reasons.append(f"runtime_step_span_shortfall:{runtime_step_shortfall_reason}")
    if runtime_avg is None:
        evidence_reasons.append("runtime_average_window_missing")
    elif runtime_avg != required_average_last_n:
        evidence_reasons.append(
            f"runtime_average_window_{runtime_avg}_does_not_match_required_{required_average_last_n}"
        )
    if runtime_selected_last_window is not True:
        evidence_reasons.append(f"runtime_selected_last_window_not_true:{runtime_selected_last_window}")
    if runtime_step_span is None:
        evidence_reasons.append("runtime_source_step_span_missing")
    if (
        runtime_step_span_reported is not None
        and runtime_step_span_from_steps is not None
        and runtime_step_span_reported != runtime_step_span_from_steps
    ):
        evidence_reasons.append("runtime_source_step_span_mismatch_time_steps")
    if not runtime_steps:
        evidence_reasons.append("runtime_source_time_steps_missing")
    elif not runtime_steps_increasing:
        evidence_reasons.append("runtime_source_steps_not_strictly_increasing")
    if runtime_steps and not runtime_steps_uniform:
        evidence_reasons.append("runtime_source_step_spacing_not_uniform")
    if not runtime_hashes:
        evidence_reasons.append("runtime_source_vtk_hashes_missing")
    if runtime_hash_count != len(runtime_steps):
        evidence_reasons.append("runtime_source_vtk_hash_count_mismatch_time_steps")
    if runtime_hash_count < min_avg_frames:
        evidence_reasons.append(
            count_below_minimum_reason("runtime_source_vtk_hash_count", runtime_hash_count, min_avg_frames)
            or "runtime_source_vtk_hash_count_below_minimum"
        )
    if runtime_hash_unique_count != runtime_hash_count:
        evidence_reasons.append("runtime_source_vtk_hashes_not_unique")
    return evidence_reasons


def build_final_window_frame_count_gate(
    *,
    runtime_avg: Optional[int],
    runtime_source_frame_count: Optional[int],
    runtime_hash_count: int,
    runtime_hash_unique_count: int,
    runtime_selected_last_window: Optional[bool],
    min_avg_frames: int,
) -> Dict[str, Any]:
    reasons: List[str] = []
    for label, value in [
        ("runtime_average_window_frame_count", runtime_avg),
        ("runtime_source_frame_count", runtime_source_frame_count),
        ("runtime_source_vtk_sha256_count", runtime_hash_count),
    ]:
        if value is None:
            reasons.append(f"{label}_missing")
            continue
        shortfall = count_below_minimum_reason(label, value, min_avg_frames)
        if shortfall:
            reasons.append(shortfall)
    if runtime_hash_unique_count != runtime_hash_count:
        reasons.append("runtime_source_vtk_sha256_not_unique")
    if runtime_selected_last_window is not True:
        reasons.append(
            f"runtime_selected_last_window_not_true:{runtime_selected_last_window}"
        )
    return {
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def classify_time_averaging_fidelity(
    *,
    time_average_gate: str,
    runtime_final_window_frame_count_gate: str,
    stationarity_gate: str,
    runtime_selected_last_window: Optional[bool],
    runtime_average_shortfall_reason: str,
    runtime_step_shortfall_reason: str,
) -> str:
    if (
        time_average_gate == "pass"
        and runtime_final_window_frame_count_gate == "pass"
        and stationarity_gate == "pass"
        and runtime_selected_last_window is True
    ):
        return "paper_grade_final_window_average"
    if runtime_average_shortfall_reason or runtime_step_shortfall_reason:
        return "short_diagnostic_average_window"
    if runtime_selected_last_window is not True:
        return "stale_or_nonfinal_average_window"
    if stationarity_gate and stationarity_gate != "pass":
        return "nonstationary_final_window"
    return "incomplete_time_averaging_evidence"


def build_inlet_equivalence_evidence_reasons(
    *,
    inlet_source_audit: Dict[str, Any],
    inlet_source_hash_check: Dict[str, Any],
    inlet_profile_audit: Dict[str, Any],
    inlet_profile_af_hash_matches: bool,
    inlet_profile_window_check: Dict[str, Any],
    inlet_correlation_audit: Dict[str, Any],
    inlet_correlation_window_check: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
) -> List[str]:
    evidence_reasons: List[str] = []

    source_gate = str(inlet_source_audit.get("inlet_source_gate") or "").strip().lower()
    paper_source_gate = str(inlet_source_audit.get("paper_grade_inlet_source_gate") or "").strip().lower()
    source_distribution_consistent = as_bool(inlet_source_audit.get("inlet_source_distribution_consistent"))
    source_velocity_only = as_bool(inlet_source_audit.get("inlet_source_velocity_field_only"))
    source_comment_stripped = as_bool(inlet_source_audit.get("inlet_source_comment_stripped_code_audit"))
    source_uncorrelated_random = as_bool(inlet_source_audit.get("has_uncorrelated_random_inlet"))
    source_method_class = str(inlet_source_audit.get("inlet_source_method_class") or "").strip()
    source_fidelity_class = str(
        inlet_source_audit.get("inlet_source_turbulent_inflow_fidelity_class") or ""
    ).strip()
    source_correlated_velocity_only = as_bool(
        inlet_source_audit.get("inlet_source_has_correlated_velocity_field_only")
    )
    source_uncorrelated_rms_velocity_only = as_bool(
        inlet_source_audit.get("inlet_source_has_uncorrelated_rms_velocity_field_only")
    )
    source_correlation_model = str(inlet_source_audit.get("synthetic_inlet_correlation_model") or "").strip()
    source_distribution_route = str(inlet_source_audit.get("inlet_distribution_route") or "").strip()
    source_distribution_route_gate = str(inlet_source_audit.get("inlet_distribution_route_gate") or "").strip().lower()
    source_has_equilibrium_define = as_bool(inlet_source_audit.get("has_equilibrium_boundaries_define"))
    source_has_type_e_equilibrium_route = as_bool(
        inlet_source_audit.get("has_type_e_equilibrium_boundary_route")
    )
    source_has_length_scale = as_bool(inlet_source_audit.get("has_inlet_length_scale_evidence"))
    source_length_gate = str(inlet_source_audit.get("metadata_length_scale_gate") or "").strip().lower()
    source_has_reynolds_tensor = as_bool(inlet_source_audit.get("has_reynolds_stress_tensor_evidence"))
    source_reynolds_treatment = str(inlet_source_audit.get("reynolds_stress_treatment") or "").strip()
    source_has_three_component_write = as_bool(inlet_source_audit.get("has_three_component_velocity_write"))
    source_has_three_component_fluctuation = as_bool(
        inlet_source_audit.get("has_three_component_fluctuation_evidence")
    )
    source_has_k_driven_stg = as_bool(inlet_source_audit.get("has_k_driven_three_component_stg"))
    source_has_component_phase_decorrelation = as_bool(
        inlet_source_audit.get("has_component_phase_decorrelation")
    )
    source_has_temporal_filter_state = as_bool(inlet_source_audit.get("has_temporal_filter_state"))
    source_has_mean_correction = as_bool(inlet_source_audit.get("has_mean_preserving_inlet_correction"))
    source_has_layer_correction = as_bool(inlet_source_audit.get("has_layerwise_mean_preserving_inlet_correction"))
    source_has_streamwise_clipping_control = as_bool(inlet_source_audit.get("has_streamwise_clipping_control"))
    source_streamwise_clipping_enabled = as_bool(inlet_source_audit.get("streamwise_clipping_enabled"))
    source_has_legacy_clipping = as_bool(inlet_source_audit.get("has_legacy_hardcoded_streamwise_clipping"))
    source_hash_matches = as_bool(inlet_source_hash_check.get("inlet_source_setup_cpp_sha256_matches_current"))
    source_reasons = split_scalar_list(inlet_source_audit.get("inlet_source_gate_reasons"))
    paper_source_reasons = split_scalar_list(inlet_source_audit.get("paper_grade_inlet_source_gate_reasons"))
    if not inlet_source_audit:
        evidence_reasons.append("inlet_source_audit_missing")
    if source_gate != "pass":
        evidence_reasons.append(f"inlet_source_gate_not_pass:{source_gate or 'missing'}")
    if paper_source_gate != "pass":
        evidence_reasons.append(f"paper_grade_inlet_source_gate_not_pass:{paper_source_gate or 'missing'}")
    if source_distribution_consistent is not True:
        evidence_reasons.append(f"inlet_source_distribution_consistent_not_true:{source_distribution_consistent}")
    if source_velocity_only is not False:
        evidence_reasons.append(f"inlet_source_velocity_field_only_not_false:{source_velocity_only}")
    if source_comment_stripped is not True:
        evidence_reasons.append(f"inlet_source_comment_stripped_code_audit_not_true:{source_comment_stripped}")
    if source_uncorrelated_random is not False:
        evidence_reasons.append(f"inlet_source_has_uncorrelated_random_inlet_not_false:{source_uncorrelated_random}")
    if source_fidelity_class not in {
        "distribution_consistent_digital_filter",
        "distribution_consistent_synthetic_eddy",
        "distribution_consistent_precursor_or_recycling",
    }:
        evidence_reasons.append(
            f"inlet_source_turbulent_inflow_fidelity_class_not_paper_grade:{source_fidelity_class or 'missing'}"
        )
    if source_correlated_velocity_only is not False:
        evidence_reasons.append(
            f"inlet_source_has_correlated_velocity_field_only_not_false:{source_correlated_velocity_only}"
        )
    if source_uncorrelated_rms_velocity_only is not False:
        evidence_reasons.append(
            "inlet_source_has_uncorrelated_rms_velocity_field_only_not_false:"
            f"{source_uncorrelated_rms_velocity_only}"
        )
    if source_correlation_model in {"uncorrelated_random_rms_velocity_field_only", "velocity_field_only_without_correlation_evidence"}:
        evidence_reasons.append(f"inlet_synthetic_correlation_model_not_paper_grade:{source_correlation_model}")
    if source_distribution_route_gate != "pass":
        evidence_reasons.append(
            f"inlet_distribution_route_gate_not_pass:{source_distribution_route_gate or 'missing'}"
        )
    if source_distribution_route == "velocity_field_only_without_equilibrium_boundary_define":
        evidence_reasons.append("inlet_distribution_route_missing_equilibrium_boundaries_define")
    if source_has_equilibrium_define is False and source_distribution_route != "direct_setup_distribution_write":
        evidence_reasons.append("inlet_source_has_equilibrium_boundaries_define_not_true:False")
    if source_has_type_e_equilibrium_route is False and source_distribution_route != "direct_setup_distribution_write":
        evidence_reasons.append("inlet_source_has_type_e_equilibrium_boundary_route_not_true:False")
    if source_method_class in {
        "stg_lite_velocity_field_only",
        "stg_lite_correlated_velocity_field_only",
        "mean_profile_velocity_field_only",
        "named_method_without_distribution_evidence",
        "named_method_without_precursor_recycling_field_evidence",
        "precursor_or_recycling_velocity_field_only",
    }:
        evidence_reasons.append(f"inlet_source_method_class_not_paper_grade:{source_method_class}")
    if source_has_length_scale is not True:
        evidence_reasons.append(f"inlet_source_has_inlet_length_scale_evidence_not_true:{source_has_length_scale}")
    if source_length_gate != "pass":
        evidence_reasons.append(f"inlet_source_metadata_length_scale_gate_not_pass:{source_length_gate or 'missing'}")
    if source_has_reynolds_tensor is not True:
        evidence_reasons.append(f"inlet_source_has_reynolds_stress_tensor_evidence_not_true:{source_has_reynolds_tensor}")
    if source_reynolds_treatment != "full_tensor_or_precursor_evidence":
        evidence_reasons.append(f"inlet_source_reynolds_stress_treatment_not_full_tensor:{source_reynolds_treatment or 'missing'}")
    for key, value in [
        ("inlet_source_has_three_component_velocity_write", source_has_three_component_write),
        ("inlet_source_has_three_component_fluctuation_evidence", source_has_three_component_fluctuation),
        ("inlet_source_has_k_driven_three_component_stg", source_has_k_driven_stg),
        ("inlet_source_has_component_phase_decorrelation", source_has_component_phase_decorrelation),
        ("inlet_source_has_temporal_filter_state", source_has_temporal_filter_state),
        ("inlet_source_has_mean_preserving_inlet_correction", source_has_mean_correction),
        ("inlet_source_has_layerwise_mean_preserving_inlet_correction", source_has_layer_correction),
        ("inlet_source_has_streamwise_clipping_control", source_has_streamwise_clipping_control),
    ]:
        if value is not True:
            evidence_reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")
    if source_streamwise_clipping_enabled is not False:
        evidence_reasons.append(f"inlet_source_streamwise_clipping_enabled_not_false:{source_streamwise_clipping_enabled}")
    if source_has_legacy_clipping is not False:
        evidence_reasons.append(f"inlet_source_has_legacy_hardcoded_streamwise_clipping_not_false:{source_has_legacy_clipping}")
    if source_hash_matches is not True:
        evidence_reasons.append(f"inlet_source_setup_cpp_sha256_matches_current_not_true:{source_hash_matches}")
    for reason in source_reasons:
        if reason != "inlet_source_consistent_with_declared_metadata":
            evidence_reasons.append(f"inlet_source_reason:{reason}")
    for reason in paper_source_reasons:
        if reason != "source_distribution_consistent":
            evidence_reasons.append(f"paper_grade_inlet_source_reason:{reason}")

    profile_gate = str(inlet_profile_audit.get("inlet_profile_gate") or "").strip().upper()
    u_profile_gate = str(inlet_profile_audit.get("inlet_u_profile_gate") or "").strip().upper()
    k_profile_gate = str(inlet_profile_audit.get("inlet_k_profile_gate") or "").strip().upper()
    profile_time_gate = str(inlet_profile_audit.get("time_averaging_gate") or "").strip().upper()
    profile_frame_count = as_int(inlet_profile_audit.get("frame_count"))
    profile_step_span = source_step_span_from_steps(audit_source_steps(inlet_profile_audit))
    if profile_step_span is None:
        profile_step_span = as_int(inlet_profile_audit.get("source_step_span"))
    if not inlet_profile_audit:
        evidence_reasons.append("inlet_profile_audit_missing")
    for key, value in [
        ("inlet_profile_gate", profile_gate),
        ("inlet_u_profile_gate", u_profile_gate),
        ("inlet_k_profile_gate", k_profile_gate),
        ("inlet_profile_time_averaging_gate", profile_time_gate),
    ]:
        if value != "PASS":
            evidence_reasons.append(f"{key}_not_pass:{value.lower() or 'missing'}")
    if not inlet_profile_af_hash_matches:
        evidence_reasons.append("inlet_profile_af_csv_sha256_matches_expected_not_true")
    if profile_frame_count is None or profile_frame_count < min_avg_frames:
        evidence_reasons.append(
            count_below_minimum_reason("inlet_profile_frame_count", profile_frame_count, min_avg_frames)
            or "inlet_profile_frame_count_below_minimum"
        )
    if profile_step_span is None or profile_step_span < min_avg_step_span:
        evidence_reasons.append(
            count_below_minimum_reason("inlet_profile_source_step_span", profile_step_span, min_avg_step_span)
            or "inlet_profile_source_step_span_below_minimum"
        )
    for key in [
        "inlet_profile_source_time_steps_match_runtime",
        "inlet_profile_source_vtk_sha256_match_runtime",
        "inlet_profile_source_step_hash_pairs_match_runtime",
    ]:
        value = as_bool(inlet_profile_window_check.get(key))
        if value is not True:
            evidence_reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    correlation_gate = str(inlet_correlation_audit.get("inlet_correlation_gate") or "").strip().upper()
    k_variance_gate = str(inlet_correlation_audit.get("inlet_k_variance_gate") or "").strip().upper()
    tke_gate = str(inlet_correlation_audit.get("inlet_tke_gate") or "").strip().upper()
    correlation_frame_count = as_int(inlet_correlation_audit.get("frame_count"))
    correlation_step_span = source_step_span_from_steps(audit_source_steps(inlet_correlation_audit))
    if correlation_step_span is None:
        correlation_step_span = as_int(inlet_correlation_audit.get("source_step_span"))
    if not inlet_correlation_audit:
        evidence_reasons.append("inlet_correlation_audit_missing")
    for key, value in [
        ("inlet_correlation_gate", correlation_gate),
        ("inlet_k_variance_gate", k_variance_gate),
        ("inlet_tke_gate", tke_gate),
    ]:
        if value != "PASS":
            evidence_reasons.append(f"{key}_not_pass:{value.lower() or 'missing'}")
    if correlation_frame_count is None or correlation_frame_count < min_avg_frames:
        evidence_reasons.append(
            count_below_minimum_reason("inlet_correlation_frame_count", correlation_frame_count, min_avg_frames)
            or "inlet_correlation_frame_count_below_minimum"
        )
    if correlation_step_span is None or correlation_step_span < min_avg_step_span:
        evidence_reasons.append(
            count_below_minimum_reason("inlet_correlation_source_step_span", correlation_step_span, min_avg_step_span)
            or "inlet_correlation_source_step_span_below_minimum"
        )
    for key in [
        "inlet_correlation_source_time_steps_match_runtime",
        "inlet_correlation_source_vtk_sha256_match_runtime",
        "inlet_correlation_source_step_hash_pairs_match_runtime",
    ]:
        value = as_bool(inlet_correlation_window_check.get(key))
        if value is not True:
            evidence_reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")
    for reason in split_scalar_list(inlet_correlation_audit.get("inlet_correlation_gate_reasons")):
        if reason != "inlet_correlation_evidence_present":
            evidence_reasons.append(f"inlet_correlation_reason:{reason}")
    for reason in split_scalar_list(inlet_correlation_audit.get("inlet_k_variance_gate_reasons")):
        if reason != "k_variance_matches_af_profile":
            evidence_reasons.append(f"inlet_k_variance_reason:{reason}")
    for reason in split_scalar_list(inlet_correlation_audit.get("inlet_tke_gate_reasons")):
        if reason != "tke_matches_af_profile":
            evidence_reasons.append(f"inlet_tke_reason:{reason}")

    return evidence_reasons


def build_boundary_equivalence_evidence_reasons(
    *,
    boundary_source_audit: Dict[str, Any],
    boundary_source_hash_check: Dict[str, Any],
    boundary_protocol_audit: Dict[str, Any],
    boundary_runtime_audit: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
) -> List[str]:
    evidence_reasons: List[str] = []

    source_gate = str(boundary_source_audit.get("boundary_source_gate") or "").strip().lower()
    paper_source_gate = str(boundary_source_audit.get("paper_grade_boundary_source_gate") or "").strip().lower()
    source_equivalent = as_bool(boundary_source_audit.get("boundary_source_wind_tunnel_equivalent"))
    source_simplified = as_bool(boundary_source_audit.get("boundary_source_simplified"))
    source_fidelity_class = str(boundary_source_audit.get("boundary_source_fidelity_class") or "").strip()
    source_complete_evidence = as_bool(
        boundary_source_audit.get("boundary_source_has_complete_wind_tunnel_evidence")
    )
    source_stub_only = as_bool(boundary_source_audit.get("boundary_source_has_empty_advanced_method_stub_only"))
    source_advanced_code_evidence = as_bool(boundary_source_audit.get("boundary_source_advanced_code_evidence"))
    source_missing_paper_evidence = split_scalar_list(
        boundary_source_audit.get("missing_paper_grade_source_evidence")
    )
    source_hash_matches = as_bool(boundary_source_hash_check.get("boundary_source_setup_cpp_sha256_matches_current"))
    if not boundary_source_audit:
        evidence_reasons.append("boundary_source_audit_missing")
    if source_gate != "pass":
        evidence_reasons.append(f"boundary_source_gate_not_pass:{source_gate or 'missing'}")
    if paper_source_gate != "pass":
        evidence_reasons.append(f"paper_grade_boundary_source_gate_not_pass:{paper_source_gate or 'missing'}")
    if source_equivalent is not True:
        evidence_reasons.append(f"boundary_source_wind_tunnel_equivalent_not_true:{source_equivalent}")
    if source_simplified is not False:
        evidence_reasons.append(f"boundary_source_simplified_not_false:{source_simplified}")
    if source_fidelity_class != "wind_tunnel_equivalent_complete":
        evidence_reasons.append(
            f"boundary_source_fidelity_class_not_paper_grade:{source_fidelity_class or 'missing'}"
        )
    if source_complete_evidence is not True:
        evidence_reasons.append(
            f"boundary_source_has_complete_wind_tunnel_evidence_not_true:{source_complete_evidence}"
        )
    if source_stub_only is not False:
        evidence_reasons.append(
            f"boundary_source_has_empty_advanced_method_stub_only_not_false:{source_stub_only}"
        )
    if source_advanced_code_evidence is not True:
        evidence_reasons.append(f"boundary_source_advanced_code_evidence_not_true:{source_advanced_code_evidence}")
    for field in source_missing_paper_evidence:
        evidence_reasons.append(f"boundary_source_missing_paper_grade_evidence:{field}")
    if source_hash_matches is not True:
        evidence_reasons.append(f"boundary_source_setup_cpp_sha256_matches_current_not_true:{source_hash_matches}")

    protocol_gate = str(boundary_protocol_audit.get("boundary_protocol_gate") or "").strip().lower()
    evidence_gate = str(boundary_protocol_audit.get("boundary_evidence_gate") or "").strip().lower()
    run_identity_gate = str(boundary_protocol_audit.get("boundary_run_identity_gate") or "").strip().lower()
    metadata_hash_matches = as_bool(boundary_protocol_audit.get("evidence_metadata_sha256_matches_current"))
    evidence_hashed = as_bool(boundary_protocol_audit.get("boundary_evidence_files_all_hashed"))
    equivalence_supported = as_bool(boundary_protocol_audit.get("boundary_equivalence_supported"))
    evidence_class_supported = as_bool(boundary_protocol_audit.get("boundary_evidence_class_supported"))
    condition_fields_supported = as_bool(boundary_protocol_audit.get("boundary_condition_fields_supported"))
    clearance_gate = str(boundary_protocol_audit.get("clearance_numeric_gate") or "").strip().lower()
    blockage_gate = str(boundary_protocol_audit.get("blockage_gate") or "").strip().lower()
    missing_evidence_fields = split_scalar_list(boundary_protocol_audit.get("missing_evidence_fields"))
    unsupported_condition_fields = split_scalar_list(boundary_protocol_audit.get("unsupported_boundary_condition_fields"))
    condition_support_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_condition_support_reasons"))
    if not unsupported_condition_fields:
        prefix = "unsupported_boundary_condition_fields:"
        for support_reason in condition_support_reasons:
            if support_reason.startswith(prefix):
                unsupported_condition_fields = split_scalar_list(support_reason[len(prefix) :])
                break
    clearance_reasons = split_scalar_list(boundary_protocol_audit.get("clearance_numeric_gate_reasons"))
    protocol_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_protocol_gate_reasons"))
    run_identity_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_run_identity_gate_reasons"))
    missing_files = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_missing"))
    empty_files = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_empty"))
    unreadable_files = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_unreadable"))
    missing_or_false_support_fields = [
        field for field in REQUIRED_BOUNDARY_SUPPORT_FIELDS if as_bool(boundary_protocol_audit.get(field)) is not True
    ]
    if not boundary_protocol_audit:
        evidence_reasons.append("boundary_protocol_audit_missing")
    if protocol_gate != "pass":
        evidence_reasons.append(f"boundary_protocol_gate_not_pass:{protocol_gate or 'missing'}")
    if evidence_gate != "pass":
        evidence_reasons.append(f"boundary_evidence_gate_not_pass:{evidence_gate or 'missing'}")
    if run_identity_gate != "pass":
        evidence_reasons.append(f"boundary_run_identity_gate_not_pass:{run_identity_gate or 'missing'}")
    if metadata_hash_matches is not True:
        evidence_reasons.append(f"boundary_evidence_metadata_sha256_matches_current_not_true:{metadata_hash_matches}")
    if evidence_hashed is not True:
        evidence_reasons.append(f"boundary_evidence_files_all_hashed_not_true:{evidence_hashed}")
    if equivalence_supported is not True:
        evidence_reasons.append(f"boundary_equivalence_supported_not_true:{equivalence_supported}")
    if evidence_class_supported is not True:
        evidence_reasons.append(f"boundary_evidence_class_supported_not_true:{evidence_class_supported}")
    if condition_fields_supported is not True:
        evidence_reasons.append(f"boundary_condition_fields_supported_not_true:{condition_fields_supported}")
    if clearance_gate != "pass":
        evidence_reasons.append(f"boundary_clearance_numeric_gate_not_pass:{clearance_gate or 'missing'}")
    if blockage_gate != "pass":
        evidence_reasons.append(f"boundary_blockage_gate_not_pass:{blockage_gate or 'missing'}")
    for field in missing_evidence_fields:
        evidence_reasons.append(f"boundary_missing_evidence_field:{field}")
    for field in unsupported_condition_fields:
        evidence_reasons.append(f"boundary_unsupported_condition_field:{field}")
    for field in missing_or_false_support_fields:
        evidence_reasons.append(f"boundary_required_support_field_not_true:{field}")
    for reason in protocol_reasons:
        if reason != "boundary_protocol_pass":
            evidence_reasons.append(f"boundary_protocol_reason:{reason}")
    for reason in condition_support_reasons:
        if reason != "all_boundary_condition_fields_supported":
            evidence_reasons.append(f"boundary_condition_support_reason:{reason}")
    for reason in clearance_reasons:
        if reason != "clearance_numeric_evidence_complete":
            evidence_reasons.append(f"boundary_clearance_reason:{reason}")
    for reason in run_identity_reasons:
        if reason != "boundary_evidence_bound_to_current_run":
            evidence_reasons.append(f"boundary_run_identity_reason:{reason}")
    for path in missing_files:
        evidence_reasons.append(f"boundary_evidence_file_missing:{Path(path).name or 'unnamed'}")
    for path in empty_files:
        evidence_reasons.append(f"boundary_evidence_file_empty:{Path(path).name or 'unnamed'}")
    for path in unreadable_files:
        evidence_reasons.append(f"boundary_evidence_file_unreadable:{Path(path).name or 'unnamed'}")

    runtime_gate = str(boundary_runtime_audit.get("boundary_runtime_gate") or "").strip().lower()
    runtime_traceability_gate = str(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate") or ""
    ).strip().lower()
    runtime_profile_gate = str(
        boundary_runtime_audit.get("boundary_runtime_profile_preservation_gate") or ""
    ).strip().lower()
    runtime_inlet_gate = str(boundary_runtime_audit.get("boundary_runtime_inlet_gate") or "").strip().lower()
    runtime_side_top_gate = str(boundary_runtime_audit.get("boundary_runtime_side_top_gate") or "").strip().lower()
    runtime_side_top_normal_gate = str(
        boundary_runtime_audit.get("boundary_runtime_side_top_normal_leakage_gate") or ""
    ).strip().lower()
    runtime_outlet_gate = str(boundary_runtime_audit.get("boundary_runtime_outlet_gate") or "").strip().lower()
    runtime_reasons = split_scalar_list(boundary_runtime_audit.get("boundary_runtime_gate_reasons"))
    runtime_traceability_reasons = split_scalar_list(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate_reasons")
    )
    runtime_steps = audit_source_steps(boundary_runtime_audit)
    runtime_hashes = audit_source_hashes(boundary_runtime_audit)
    runtime_step_span = source_step_span_from_steps(runtime_steps)
    runtime_reported_step_span = as_int(boundary_runtime_audit.get("source_step_span"))
    if runtime_step_span is None:
        runtime_step_span = runtime_reported_step_span
    runtime_frame_count = as_int(boundary_runtime_audit.get("frame_count"))
    runtime_selected_last_window = as_bool(boundary_runtime_audit.get("selected_last_window"))
    runtime_steps_increasing = source_steps_strictly_increasing(runtime_steps)
    runtime_steps_uniform = source_steps_uniformly_spaced(runtime_steps)
    runtime_hash_count = len(runtime_hashes)
    runtime_hash_unique_count = len(set(runtime_hashes))
    if not boundary_runtime_audit:
        evidence_reasons.append("boundary_runtime_audit_missing")
    if runtime_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_gate_not_pass:{runtime_gate or 'missing'}")
    if runtime_traceability_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_traceability_gate_not_pass:{runtime_traceability_gate or 'missing'}")
    if runtime_profile_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_profile_preservation_gate_not_pass:{runtime_profile_gate or 'missing'}")
    if runtime_inlet_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_inlet_gate_not_pass:{runtime_inlet_gate or 'missing'}")
    if runtime_side_top_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_side_top_gate_not_pass:{runtime_side_top_gate or 'missing'}")
    if runtime_side_top_normal_gate != "pass":
        evidence_reasons.append(
            f"boundary_runtime_side_top_normal_leakage_gate_not_pass:{runtime_side_top_normal_gate or 'missing'}"
        )
    if runtime_outlet_gate != "pass":
        evidence_reasons.append(f"boundary_runtime_outlet_gate_not_pass:{runtime_outlet_gate or 'missing'}")
    if runtime_frame_count is None or runtime_frame_count < min_avg_frames:
        evidence_reasons.append(
            count_below_minimum_reason("boundary_runtime_frame_count", runtime_frame_count, min_avg_frames)
            or "boundary_runtime_frame_count_below_minimum"
        )
    if runtime_step_span is None or runtime_step_span < min_avg_step_span:
        evidence_reasons.append(
            count_below_minimum_reason("boundary_runtime_source_step_span", runtime_step_span, min_avg_step_span)
            or "boundary_runtime_source_step_span_below_minimum"
        )
    if runtime_selected_last_window is not True:
        evidence_reasons.append(f"boundary_runtime_selected_last_window_not_true:{runtime_selected_last_window}")
    if not runtime_steps:
        evidence_reasons.append("boundary_runtime_source_time_steps_missing")
    elif not runtime_steps_increasing:
        evidence_reasons.append("boundary_runtime_source_steps_not_strictly_increasing")
    if runtime_steps and not runtime_steps_uniform:
        evidence_reasons.append("boundary_runtime_source_step_spacing_not_uniform")
    if not runtime_hashes:
        evidence_reasons.append("boundary_runtime_source_vtk_hashes_missing")
    if runtime_hash_count != len(runtime_steps):
        evidence_reasons.append("boundary_runtime_source_vtk_hash_count_mismatch_time_steps")
    if runtime_hash_count < min_avg_frames:
        evidence_reasons.append(
            count_below_minimum_reason("boundary_runtime_source_vtk_hash_count", runtime_hash_count, min_avg_frames)
            or "boundary_runtime_source_vtk_hash_count_below_minimum"
        )
    if runtime_hash_unique_count != runtime_hash_count:
        evidence_reasons.append("boundary_runtime_source_vtk_hashes_not_unique")
    for reason in runtime_reasons:
        if reason != "boundary_runtime_faces_preserve_af_profile":
            evidence_reasons.append(f"boundary_runtime_reason:{reason}")
    for reason in runtime_traceability_reasons:
        if reason != "boundary_runtime_window_traceable":
            evidence_reasons.append(f"boundary_runtime_traceability_reason:{reason}")

    return evidence_reasons


def append_setup_hash_reason(reasons: List[str], label: str, audit: Dict[str, Any], setup_sha: str) -> Dict[str, Any]:
    audit_sha = str(audit.get("setup_cpp_sha256") or "").strip().lower()
    match = bool(audit_sha) and bool(setup_sha) and audit_sha == setup_sha
    if audit:
        if not audit_sha:
            reasons.append(f"{label}_setup_cpp_sha256_missing")
        elif not setup_sha:
            reasons.append(f"{label}_current_setup_cpp_missing")
        elif not match:
            reasons.append(f"{label}_setup_cpp_sha256_mismatch")
    return {
        f"{label}_setup_cpp_sha256": audit_sha,
        f"{label}_setup_cpp_sha256_matches_current": match,
    }


def probe_unique_values(rows: List[Dict[str, str]], *fields: str) -> List[str]:
    return sorted({row_value(row, *fields) for row in rows if row_value(row, *fields)})


def probe_unique_int_values(rows: List[Dict[str, str]], *fields: str) -> List[int]:
    values = []
    for row in rows:
        value = as_int(row_value(row, *fields))
        if value is not None:
            values.append(value)
    return sorted(set(values))


def row_value(row: Dict[str, str], *fields: str) -> str:
    lowered = {key.lower(): value for key, value in row.items()}
    for field in fields:
        if field in row:
            return str(row.get(field) or "").strip()
        value = lowered.get(field.lower())
        if value is not None:
            return str(value or "").strip()
    return ""


def normalized_column_key(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def find_csv_column(rows: List[Dict[str, str]], candidates: Iterable[str]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    normalized = {normalized_column_key(column): column for column in columns}
    for candidate in candidates:
        found = normalized.get(normalized_column_key(candidate))
        if found:
            return found
    return ""


def find_column_by_fieldnames(fieldnames: Iterable[str], candidates: Iterable[str]) -> str:
    normalized = {normalized_column_key(column): column for column in fieldnames}
    for candidate in candidates:
        found = normalized.get(normalized_column_key(candidate))
        if found:
            return found
    return ""


def af_u_at_reference_height(path: Optional[Path], z_ref: Optional[float]) -> Optional[float]:
    if path is None or z_ref is None or not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return None
        z_column = find_column_by_fieldnames(reader.fieldnames, ["z", "z(m)", "height", "height_m"])
        u_column = find_column_by_fieldnames(reader.fieldnames, ["U", "U(m/s)", "u_mps", "velocity", "velocity_mps"])
        if not z_column or not u_column:
            return None
        samples: List[Tuple[float, float]] = []
        for row in reader:
            z = as_float(row.get(z_column))
            u = as_float(row.get(u_column))
            if z is not None and u is not None:
                samples.append((z, u))
    if len(samples) < 2:
        return None
    samples.sort(key=lambda item: item[0])
    if z_ref <= samples[0][0]:
        return samples[0][1]
    if z_ref >= samples[-1][0]:
        return samples[-1][1]
    for (z0, u0), (z1, u1) in zip(samples, samples[1:]):
        if z0 <= z_ref <= z1:
            if abs(z1 - z0) <= 1.0e-12:
                return u0
            return u0 + (u1 - u0) * ((z_ref - z0) / (z1 - z0))
    return None


def filter_official_rows(
    rows: List[Dict[str, str]],
    case: str,
    wind_direction: str,
) -> Tuple[List[Dict[str, str]], Optional[str]]:
    filtered = rows
    case_text = str(case or "").strip().lower()
    wind_text = str(wind_direction or "").strip().lower()
    if case_text:
        case_col = find_csv_column(filtered, ["case", "Case", "condition", "Condition", "bcac"])
        if not case_col:
            return [], "official_case_filter_column_missing"
        filtered = [
            row
            for row in filtered
            if str(row.get(case_col) or "").strip().lower() == case_text
        ]
        if not filtered:
            return [], "official_case_filter_no_rows"
    if wind_text:
        wind_col = find_csv_column(
            filtered,
            ["Wind_direction", "wind_direction", "direction", "Direction", "wind", "Wind"],
        )
        if not wind_col:
            return [], "official_wind_direction_filter_column_missing"
        filtered = [
            row
            for row in filtered
            if str(row.get(wind_col) or "").strip().lower() == wind_text
        ]
        if not filtered:
            return [], "official_wind_direction_filter_no_rows"
    return filtered, None


def build_official_coordinate_lookup(
    official_path: Optional[Path],
    case: str,
    wind_direction: str,
) -> Tuple[Dict[str, Tuple[float, float, float]], Optional[str]]:
    rows = read_csv_rows(official_path)
    if not official_path:
        return {}, "official_csv_not_provided"
    if not rows:
        return {}, "official_csv_missing_or_empty"
    rows, filter_error = filter_official_rows(rows, case, wind_direction)
    if filter_error:
        return {}, filter_error
    id_column = find_csv_column(rows, ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"])
    x_column = find_csv_column(rows, ["x", "X", "x_m", "X_m", "X(m)", "x(m)"])
    y_column = find_csv_column(rows, ["y", "Y", "y_m", "Y_m", "Y(m)", "y(m)"])
    z_column = find_csv_column(rows, ["z", "Z", "z_m", "Z_m", "Z(m)", "z(m)"])
    if not id_column:
        return {}, "official_id_column_missing"
    if not x_column or not y_column or not z_column:
        return {}, "official_coordinate_columns_missing"

    lookup: Dict[str, Tuple[float, float, float]] = {}
    duplicate_ids = set()
    invalid_count = 0
    for row in rows:
        probe_id = normalized_column_key(str(row.get(id_column) or "").strip())
        if not probe_id:
            continue
        x = as_float(row.get(x_column))
        y = as_float(row.get(y_column))
        z = as_float(row.get(z_column))
        if x is None or y is None or z is None:
            invalid_count += 1
            continue
        if probe_id in lookup:
            duplicate_ids.add(probe_id)
        lookup[probe_id] = (x, y, z)
    if duplicate_ids:
        return {}, "official_duplicate_ids_after_normalization"
    if invalid_count:
        return {}, f"official_invalid_coordinate_count:{invalid_count}"
    if not lookup:
        return {}, "official_coordinate_lookup_empty"
    return lookup, None


def probe_official_coordinate_delta_summary(
    valid_probe_rows: List[Dict[str, str]],
    official_coordinates: Dict[str, Tuple[float, float, float]],
    probe_id_column: str,
) -> Dict[str, Any]:
    coordinate_deltas: List[float] = []
    recomputed_count = 0
    use_current_official = bool(official_coordinates and probe_id_column)
    for row in valid_probe_rows:
        coordinate_delta: Optional[float] = None
        if use_current_official:
            probe_id = normalized_column_key(str(row.get(probe_id_column) or "").strip())
            official_coordinate = official_coordinates.get(probe_id)
            if official_coordinate is not None:
                probe_x = as_float(row_value(row, "x", "X"))
                probe_y = as_float(row_value(row, "y", "Y"))
                probe_z = as_float(row_value(row, "z", "Z"))
                if probe_x is not None and probe_y is not None and probe_z is not None:
                    coordinate_delta = max(
                        abs(probe_x - official_coordinate[0]),
                        abs(probe_y - official_coordinate[1]),
                        abs(probe_z - official_coordinate[2]),
                    )
                    recomputed_count += 1
        else:
            coordinate_delta = as_float(row_value(row, "official_coordinate_delta", "OfficialCoordinateDelta"))
        if coordinate_delta is not None:
            coordinate_deltas.append(coordinate_delta)
    return {
        "deltas": coordinate_deltas,
        "recomputed_count": recomputed_count,
        "missing_count": len(valid_probe_rows) - len(coordinate_deltas),
        "source": "current_official_csv_recomputed" if use_current_official else "probe_audit_only",
        "requires_current_official_recompute": use_current_official,
    }


def probe_row_failed(row: Dict[str, str]) -> bool:
    failed = as_bool(row_value(row, "failed", "Failed"))
    out_of_tolerance = as_bool(row_value(row, "out_of_tolerance", "OutOfTolerance"))
    status = row_value(row, "validation_status", "ValidationStatus", "status", "Status").lower()
    return (
        failed is True
        or out_of_tolerance is True
        or any(token in status for token in ["fail", "invalid", "out_of_tolerance", "out-of-tolerance"])
    )


def classify_probe_component_fidelity(reasons: List[str]) -> str:
    if not reasons:
        return "paper_grade_probe_component_normalization"
    reason_text = ";".join(str(reason) for reason in reasons).lower()
    if "probe_audit_missing" in reason_text or "official_measurement_sha256_missing" in reason_text:
        return "missing_probe_or_official_evidence"
    if any(
        token in reason_text
        for token in [
            "official_probe",
            "official_coordinate",
            "coordinate_delta",
            "missing_official_probe_id",
            "unmatched_official",
            "probe_missing_id",
            "probe_duplicate_id",
            "official_z",
            "height_gate",
        ]
    ):
        return "official_probe_coordinate_mismatch"
    if any(
        token in reason_text
        for token in [
            "out_of_tolerance",
            "nearest_distance",
            "tolerance_missing",
            "probe_projection",
        ]
    ):
        return "probe_projection_mismatch"
    if any(token in reason_text for token in ["source_", "sha256", "time_steps", "step_span", "window"]):
        return "stale_or_untraceable_probe_component_window"
    if any(
        token in reason_text
        for token in [
            "component",
            "normalization",
            "streamwise",
            "uref",
            "wind_direction",
            "compared_component",
        ]
    ):
        return "component_or_normalization_mismatch"
    return "incomplete_probe_component_evidence"


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else find_first(run_dir, ["case_metadata.json"])
    runtime_audit_path = Path(args.runtime_audit).expanduser().resolve() if args.runtime_audit else find_first(run_dir, ["native_run_audit.json", "read_vtk_audit.json"])
    inlet_source_audit_path = Path(args.inlet_source_audit).expanduser().resolve() if args.inlet_source_audit else find_first(run_dir, ["inlet_source_audit.json"])
    inlet_profile_audit_path = Path(args.inlet_profile_audit).expanduser().resolve() if args.inlet_profile_audit else find_first(run_dir, ["inlet_profile_audit.json"])
    inlet_correlation_audit_path = Path(args.inlet_correlation_audit).expanduser().resolve() if args.inlet_correlation_audit else find_first(run_dir, ["inlet_correlation_audit.json"])
    boundary_source_audit_path = Path(args.boundary_source_audit).expanduser().resolve() if args.boundary_source_audit else find_first(run_dir, ["boundary_source_audit.json"])
    boundary_protocol_audit_path = Path(args.boundary_protocol_audit).expanduser().resolve() if args.boundary_protocol_audit else find_first(run_dir, ["boundary_protocol_audit.json"])
    boundary_runtime_audit_path = Path(args.boundary_runtime_audit).expanduser().resolve() if args.boundary_runtime_audit else find_first(run_dir, ["boundary_runtime_audit.json"])
    probe_audit_path = Path(args.probe_audit).expanduser().resolve() if args.probe_audit else find_first(run_dir, ["probe_audit.csv"])
    component_sensitivity_audit_path = Path(args.component_sensitivity_audit).expanduser().resolve() if args.component_sensitivity_audit else find_first(run_dir, ["component_sensitivity_audit.json"])
    official_path = Path(args.official).expanduser().resolve() if args.official else None
    setup_path = find_first(run_dir, ["setup.cpp"])
    defines_path = find_first(run_dir, ["defines.hpp"])
    domain_origin_path = find_first(run_dir, ["domain_origin.json"])
    protocol_audit_path = find_first(run_dir, ["validation_protocol_audit.json"])

    manifest = read_json(manifest_path)
    metadata = read_json(metadata_path)
    runtime_audit = read_json(runtime_audit_path)
    inlet_source_audit = read_json(inlet_source_audit_path)
    inlet_profile_audit = read_json(inlet_profile_audit_path)
    inlet_correlation_audit = read_json(inlet_correlation_audit_path)
    boundary_source_audit = read_json(boundary_source_audit_path)
    boundary_protocol_audit = read_json(boundary_protocol_audit_path)
    boundary_runtime_audit = read_json(boundary_runtime_audit_path)
    validation_protocol_audit = read_json(protocol_audit_path)
    protocol_content_audit = audit_protocol_content(validation_protocol_audit)
    probe_rows = read_csv_rows(probe_audit_path)
    component_sensitivity_audit = read_json(component_sensitivity_audit_path)
    probe_audit_sha = sha256_file(probe_audit_path)
    official_sha = sha256_file(official_path)
    component_hash_traceability = component_sensitivity_input_hash_traceability(
        component_sensitivity_audit,
        probe_audit_sha,
        official_sha,
    )
    reasons: List[str] = []

    if not manifest:
        reasons.append("native_manifest_missing_or_empty")
    if not str(manifest.get("BaselineId") or "").strip():
        reasons.append("baseline_id_missing")
    if str(manifest.get("Gate") or "").strip() != "required_before_paper_grade_accuracy_claim":
        reasons.append("manifest_gate_unexpected")
    if as_bool(manifest.get("NativeFluidX3DPathExplicitlyProvided")) is not True:
        reasons.append("native_fluidx3d_path_not_explicit")
    source_validation = manifest.get("NativeFluidX3DSourceValidation", {})
    if not isinstance(source_validation, dict) or as_bool(source_validation.get("IsValid")) is not True:
        reasons.append("native_fluidx3d_source_validation_failed")

    role_audits = [audit_role(manifest, manifest_path, role) for role in REQUIRED_NATIVE_ROLES + REQUIRED_RUN_ROLES]
    failed_roles = [item["role"] for item in role_audits if item["gate"] != "pass"]
    if failed_roles:
        reasons.append("required_source_file_hash_gate_failed:" + ";".join(failed_roles))

    setup_sha = sha256_file(setup_path)
    defines_sha = sha256_file(defines_path)
    metadata_sha = sha256_file(metadata_path)
    domain_origin_sha = sha256_file(domain_origin_path)
    protocol_audit_sha = sha256_file(protocol_audit_path)
    runtime_audit_sha = sha256_file(runtime_audit_path)
    run_hash_checks = {
        "FluidX3D setup": setup_sha,
        "FluidX3D defines": defines_sha,
        "Case metadata": metadata_sha,
        "Domain origin": domain_origin_sha,
        "Validation protocol audit": protocol_audit_sha,
    }
    for role, actual_sha in run_hash_checks.items():
        declared_sha = str(manifest_record(manifest, role).get("Sha256") or "").strip().lower()
        if not actual_sha:
            reasons.append(f"current_run_file_missing:{role}")
        elif not declared_sha or declared_sha != actual_sha:
            reasons.append(f"current_run_file_hash_mismatch:{role}")
    if protocol_content_audit["gate"] != "pass":
        reasons.extend(str(reason) for reason in protocol_content_audit["reasons"])

    shared = manifest.get("SharedRunConditions", {})
    if not isinstance(shared, dict):
        shared = {}
        reasons.append("shared_run_conditions_missing")

    target_velocity_lbm = as_float(
        first_value(
            runtime_audit.get("target_max_profile_velocity_lbm"),
            runtime_audit.get("TargetMaxProfileVelocityLbm"),
            metadata.get("TargetMaxProfileVelocityLbm"),
            shared.get("TargetMaxProfileVelocityLbm"),
        )
    )
    estimated_mach = as_float(
        first_value(
            runtime_audit.get("estimated_max_profile_mach"),
            runtime_audit.get("EstimatedMaxProfileMach"),
            metadata.get("EstimatedMaxProfileMach"),
            shared.get("EstimatedMaxProfileMach"),
        )
    )
    lbm_tau = as_float(
        first_value(
            runtime_audit.get("lbm_tau"),
            runtime_audit.get("LbmTau"),
            metadata.get("LbmTau"),
            shared.get("LbmTau"),
        )
    )
    lbm_nu = as_float(
        first_value(
            runtime_audit.get("lbm_nu"),
            runtime_audit.get("LbmNu"),
            metadata.get("LbmNu"),
            shared.get("LbmNu"),
        )
    )
    physical_viscosity = as_float(
        first_value(
            runtime_audit.get("physical_viscosity_m2s"),
            runtime_audit.get("PhysicalViscosityM2s"),
            metadata.get("PhysicalViscosityM2s"),
            shared.get("PhysicalViscosityM2s"),
        )
    )
    estimated_reynolds = as_float(
        first_value(
            runtime_audit.get("estimated_reynolds_number"),
            runtime_audit.get("EstimatedReynoldsNumber"),
            metadata.get("EstimatedReynoldsNumber"),
            shared.get("EstimatedReynoldsNumber"),
        )
    )
    velocity_set = str(
        first_value(
            runtime_audit.get("velocity_set"),
            runtime_audit.get("VelocitySet"),
            metadata.get("VelocitySet"),
            shared.get("VelocitySet"),
        )
        or ""
    ).strip()
    les_model = str(
        first_value(
            runtime_audit.get("les_model"),
            runtime_audit.get("LesModel"),
            metadata.get("LesModel"),
            shared.get("LesModel"),
        )
        or ""
    ).strip()
    solver_warnings = str(
        first_value(
            runtime_audit.get("solver_stability_warnings"),
            runtime_audit.get("SolverStabilityWarnings"),
            shared.get("SolverStabilityWarnings"),
        )
        or ""
    ).strip()
    lbm_runtime_gate = str(
        first_value(
            runtime_audit.get("lbm_stability_gate"),
            runtime_audit.get("LbmStabilityGate"),
            shared.get("LbmStabilityGate"),
        )
        or ""
    ).strip().lower()
    lbm_protocol_status = protocol_item_status(protocol_content_audit, "lbm_stability_scaling")
    lbm_stability_reasons = build_lbm_stability_reasons(
        target_velocity_lbm=target_velocity_lbm,
        estimated_mach=estimated_mach,
        lbm_tau=lbm_tau,
        lbm_nu=lbm_nu,
        physical_viscosity=physical_viscosity,
        estimated_reynolds=estimated_reynolds,
        velocity_set=velocity_set,
        les_model=les_model,
        solver_warnings=solver_warnings,
        lbm_stability_gate=lbm_runtime_gate,
        protocol_status=lbm_protocol_status,
        max_estimated_mach=args.max_estimated_mach,
        min_lbm_tau=args.min_lbm_tau,
        max_lbm_tau=args.max_lbm_tau,
    )
    lbm_stability_gate = "pass" if not lbm_stability_reasons else "fail"
    if lbm_stability_gate != "pass":
        reasons.append("lbm_stability_gate_not_pass")
        reasons.extend(f"lbm_stability_reason:{reason}" for reason in lbm_stability_reasons)

    metadata_steps = as_int(metadata.get("TimeSteps"))
    metadata_save_interval = as_int(metadata.get("SaveInterval"))
    shared_steps = as_int(shared.get("TimeSteps"))
    shared_save_interval = as_int(shared.get("SaveInterval"))
    if metadata_steps is not None and shared_steps is not None and metadata_steps != shared_steps:
        reasons.append("metadata_manifest_time_steps_mismatch")
    if metadata_save_interval is not None and shared_save_interval is not None and metadata_save_interval != shared_save_interval:
        reasons.append("metadata_manifest_save_interval_mismatch")

    shared_frame_count = as_int(shared.get("ExpectedVtkFrameCount"))
    metadata_frame_count = as_int(metadata.get("ExpectedVtkFrameCount"))
    requested_frame_count = as_int(runtime_audit.get("requested_vtk_frame_count"))
    frame_candidates = [value for value in [shared_frame_count, metadata_frame_count, requested_frame_count] if value is not None]
    planned_frame_count_min = min(frame_candidates) if frame_candidates else None
    planned_frame_shortfall_reason = count_below_minimum_reason(
        "planned_vtk_frame_count",
        planned_frame_count_min,
        args.min_avg_frames,
    )
    if planned_frame_shortfall_reason:
        reasons.append("planned_vtk_frame_count_below_minimum")
        reasons.append(planned_frame_shortfall_reason)

    native_runner_gate_record = manifest.get("RunnerGate", {})
    if not isinstance(native_runner_gate_record, dict):
        native_runner_gate_record = {}
    native_runner_gate = str(native_runner_gate_record.get("Gate") or "").strip().lower()
    native_runner_reasons = split_scalar_list(native_runner_gate_record.get("Reasons"))
    if not native_runner_reasons:
        native_runner_reasons = split_scalar_list(native_runner_gate_record.get("ReasonsCsv"))
    if manifest and native_runner_gate != "pass":
        reasons.append(f"native_runner_gate_not_pass:{native_runner_gate or 'missing'}")
        for reason in native_runner_reasons:
            reasons.append(f"native_runner_reason:{reason}")

    actual_vtk_output = manifest.get("ActualVtkOutputGate", {})
    if not isinstance(actual_vtk_output, dict):
        actual_vtk_output = {}
    actual_vtk_output_gate = str(actual_vtk_output.get("Gate") or "").strip().lower()
    actual_vtk_output_reasons = split_scalar_list(actual_vtk_output.get("Reasons"))
    if not actual_vtk_output_reasons:
        actual_vtk_output_reasons = split_scalar_list(actual_vtk_output.get("ReasonsCsv"))
    actual_vtk_frame_count = as_int(actual_vtk_output.get("ActualFrameCount"))
    actual_vtk_expected_frame_count = as_int(actual_vtk_output.get("ExpectedFrameCount"))
    actual_vtk_minimum_frame_count = as_int(actual_vtk_output.get("MinimumFrameCount"))
    actual_vtk_output_required = as_bool(actual_vtk_output.get("ActualOutputRequired"))
    if actual_vtk_output and actual_vtk_output_gate == "diagnostic_only":
        reasons.append("actual_vtk_output_gate_not_pass")
        for reason in actual_vtk_output_reasons:
            reasons.append(f"actual_vtk_output_reason:{reason}")

    synthetic_sampling = manifest.get("PlannedSyntheticInletSamplingGate", {})
    if not isinstance(synthetic_sampling, dict):
        synthetic_sampling = {}
    planned_synthetic_gate = str(synthetic_sampling.get("Gate") or "").strip().lower()
    planned_synthetic_reasons = split_scalar_list(synthetic_sampling.get("Reasons"))
    if not planned_synthetic_reasons:
        planned_synthetic_reasons = split_scalar_list(synthetic_sampling.get("ReasonsCsv"))
    planned_synthetic_requested = as_bool(synthetic_sampling.get("SyntheticInletRequested"))
    planned_synthetic_injected = as_bool(synthetic_sampling.get("SyntheticInletInjected"))
    planned_synthetic_active = as_bool(synthetic_sampling.get("SyntheticInletActive"))
    planned_synthetic_update_interval = as_int(synthetic_sampling.get("UpdateInterval"))
    planned_synthetic_final_window_span = as_int(synthetic_sampling.get("FinalWindowStepSpan"))
    planned_synthetic_refresh_count = as_int(synthetic_sampling.get("ComputedRefreshCount"))
    planned_synthetic_metadata_expected_refresh_count = as_int(
        synthetic_sampling.get("MetadataExpectedRefreshCount")
    )
    planned_synthetic_minimum_refresh_count = as_int(synthetic_sampling.get("MinimumRefreshCount"))
    metadata_synthetic_requested = as_bool(metadata.get("SyntheticTurbulentInletRequested"))
    metadata_synthetic_injected = as_bool(metadata.get("SyntheticTurbulentInletInjected"))
    metadata_synthetic_active = metadata_synthetic_requested is True or metadata_synthetic_injected is True
    if synthetic_sampling:
        if planned_synthetic_gate not in {"pass", "not_applicable"}:
            reasons.append(f"planned_synthetic_inlet_sampling_gate_not_pass:{planned_synthetic_gate or 'missing'}")
            for reason in planned_synthetic_reasons:
                reasons.append(f"planned_synthetic_inlet_sampling_reason:{reason}")
        if metadata_synthetic_active and planned_synthetic_gate == "not_applicable":
            reasons.append("planned_synthetic_inlet_sampling_not_applicable_for_active_metadata")
    elif metadata_synthetic_active:
        reasons.append("planned_synthetic_inlet_sampling_gate_missing")

    runtime_pattern = str(runtime_audit.get("vtk_pattern") or "").strip()
    if not runtime_audit:
        reasons.append("runtime_audit_missing")
    elif runtime_pattern != args.expected_vtk_pattern:
        reasons.append("runtime_vtk_pattern_mismatch")

    runtime_avg = as_int(runtime_audit.get("average_last_n_requested"))
    if runtime_avg is None:
        runtime_avg = as_int(runtime_audit.get("averaged_frame_count"))
    runtime_average_shortfall_reason = count_below_minimum_reason(
        "runtime_average_window_frame_count",
        runtime_avg,
        args.min_avg_frames,
    )
    if runtime_avg is None or runtime_avg < args.min_avg_frames or runtime_avg != args.average_last_n:
        reasons.append("runtime_average_window_mismatch_or_too_short")
        if runtime_average_shortfall_reason:
            reasons.append(runtime_average_shortfall_reason)
        if runtime_avg is not None and runtime_avg != args.average_last_n:
            reasons.append(f"runtime_average_window_{runtime_avg}_does_not_match_required_{args.average_last_n}")

    runtime_steps = audit_source_steps(runtime_audit)
    runtime_hashes = runtime_source_hashes(runtime_audit, runtime_steps)
    runtime_selected_last_window = as_bool(runtime_audit.get("selected_last_window"))
    runtime_source_frame_count = len(runtime_steps) if runtime_steps else None
    runtime_hash_count = len(runtime_hashes)
    runtime_hash_unique_count = len(set(runtime_hashes))
    runtime_step_span_reported = as_int(runtime_audit.get("source_step_span"))
    runtime_step_span_from_steps = source_step_span_from_steps(runtime_steps)
    runtime_step_span = runtime_step_span_from_steps if runtime_step_span_from_steps is not None else runtime_step_span_reported
    runtime_steps_increasing = source_steps_strictly_increasing(runtime_steps)
    runtime_steps_uniform = source_steps_uniformly_spaced(runtime_steps)
    runtime_reported_steps_increasing = as_bool(runtime_audit.get("source_steps_strictly_increasing"))
    runtime_reported_steps_uniform = as_bool(runtime_audit.get("source_step_spacing_uniform"))
    planned_span = expected_final_window_span(
        shared_steps or metadata_steps,
        shared_save_interval or metadata_save_interval,
        as_int(runtime_audit.get("requested_vtk_save_start_step")),
        args.average_last_n,
    )
    if runtime_audit:
        if runtime_step_span_reported is None:
            reasons.append("runtime_source_step_span_missing")
        if runtime_step_span_from_steps is None:
            reasons.append("runtime_source_time_steps_span_missing")
        elif runtime_step_span_reported is not None and runtime_step_span_reported != runtime_step_span_from_steps:
            reasons.append("runtime_source_step_span_mismatch_time_steps")
        if not runtime_steps_increasing:
            reasons.append("runtime_source_steps_not_strictly_increasing")
        if not runtime_steps_uniform:
            reasons.append("runtime_source_step_spacing_not_uniform")
        if runtime_reported_steps_increasing is not None and runtime_reported_steps_increasing != runtime_steps_increasing:
            reasons.append("runtime_source_steps_increasing_flag_mismatch")
        if runtime_reported_steps_uniform is not None and runtime_reported_steps_uniform != runtime_steps_uniform:
            reasons.append("runtime_source_step_spacing_flag_mismatch")
        if runtime_selected_last_window is not True:
            reasons.append("runtime_selected_last_window_not_true")
        if runtime_hash_count != len(runtime_steps):
            reasons.append("runtime_source_vtk_hash_count_mismatch_time_steps")
        if runtime_hash_count < args.min_avg_frames:
            reasons.append("runtime_source_vtk_hash_count_below_min_avg_frames")
        if runtime_hash_unique_count != runtime_hash_count:
            reasons.append("runtime_source_vtk_hashes_not_unique")
        if any(len(value) != 64 for value in runtime_hashes):
            reasons.append("runtime_source_vtk_hash_not_sha256")
    runtime_step_shortfall_reason = count_below_minimum_reason(
        "runtime_average_step_span",
        runtime_step_span,
        args.min_avg_step_span,
    )
    planned_step_shortfall_reason = count_below_minimum_reason(
        "planned_average_step_span",
        planned_span,
        args.min_avg_step_span,
    )
    if runtime_step_shortfall_reason:
        reasons.append("runtime_average_step_span_too_short")
        reasons.append(runtime_step_shortfall_reason)
    if planned_step_shortfall_reason:
        reasons.append("planned_average_step_span_too_short")
        reasons.append(planned_step_shortfall_reason)

    time_gate = str(runtime_audit.get("time_averaging_gate") or "").strip().lower()
    requested_frame_gate = str(runtime_audit.get("requested_vtk_frame_gate") or "").strip().lower()
    stationarity_gate = str(runtime_audit.get("final_window_stationarity_gate") or "").strip().lower()
    stationarity_reasons = split_scalar_list(runtime_audit.get("final_window_stationarity_gate_reasons"))
    strict_native_run_gate = str(runtime_audit.get("strict_native_run_gate") or "").strip().lower()
    strict_native_run_reasons = split_scalar_list(runtime_audit.get("strict_native_run_gate_reasons"))
    runtime_mean_speed_statistics_source = str(
        runtime_audit.get("mean_speed_statistics_source") or ""
    ).strip().lower()
    runtime_mean_speed_statistics_cli_override = as_bool(
        runtime_audit.get("mean_speed_statistics_cli_override")
    )
    runtime_mean_speed_statistics_cli_override_fields_csv = str(
        runtime_audit.get("mean_speed_statistics_cli_override_fields_csv") or ""
    )
    runtime_reported_time_average_gate = "pass" if time_gate == "pass" and requested_frame_gate == "pass" else "fail"
    if runtime_reported_time_average_gate != "pass":
        reasons.append("runtime_time_averaging_gate_not_pass")
    if runtime_audit and stationarity_gate != "pass":
        reasons.append("runtime_final_window_stationarity_gate_not_pass")
        for reason in stationarity_reasons:
            reasons.append(f"runtime_final_window_stationarity_{reason}")
    if runtime_audit and strict_native_run_gate != "pass":
        reasons.append(f"strict_native_run_gate_not_pass:{strict_native_run_gate or 'missing'}")
        for reason in strict_native_run_reasons:
            reasons.append(f"strict_native_run_reason:{reason}")
    if runtime_audit and runtime_mean_speed_statistics_source != "sampled_vtk":
        reasons.append(
            "runtime_mean_speed_statistics_source_not_sampled_vtk:"
            f"{runtime_mean_speed_statistics_source or 'missing'}"
        )
    if runtime_audit and runtime_mean_speed_statistics_cli_override is not False:
        reasons.append(
            "runtime_mean_speed_statistics_cli_override_not_false:"
            f"{runtime_mean_speed_statistics_cli_override if runtime_mean_speed_statistics_cli_override is not None else 'missing'}"
        )

    if runtime_audit:
        if not runtime_steps:
            reasons.append("runtime_source_time_steps_missing")
        if not runtime_hashes:
            reasons.append("runtime_source_vtk_hashes_missing")

    runtime_final_window_frame_count_gate = build_final_window_frame_count_gate(
        runtime_avg=runtime_avg,
        runtime_source_frame_count=runtime_source_frame_count,
        runtime_hash_count=runtime_hash_count,
        runtime_hash_unique_count=runtime_hash_unique_count,
        runtime_selected_last_window=runtime_selected_last_window,
        min_avg_frames=args.min_avg_frames,
    )
    if runtime_final_window_frame_count_gate["gate"] != "pass":
        reasons.append("runtime_final_window_frame_count_gate_not_pass")
        reasons.extend(
            f"runtime_final_window_frame_count_gate_reason:{reason}"
            for reason in runtime_final_window_frame_count_gate["reasons"]
        )

    time_average_evidence_reasons = build_time_average_evidence_reasons(
        runtime_audit_present=bool(runtime_audit),
        runtime_reported_time_average_gate=runtime_reported_time_average_gate,
        time_gate=time_gate,
        requested_frame_gate=requested_frame_gate,
        stationarity_gate=stationarity_gate,
        stationarity_reasons=stationarity_reasons,
        planned_frame_shortfall_reason=planned_frame_shortfall_reason,
        runtime_average_shortfall_reason=runtime_average_shortfall_reason,
        planned_step_shortfall_reason=planned_step_shortfall_reason,
        runtime_step_shortfall_reason=runtime_step_shortfall_reason,
        runtime_avg=runtime_avg,
        required_average_last_n=args.average_last_n,
        runtime_selected_last_window=runtime_selected_last_window,
        runtime_step_span=runtime_step_span,
        runtime_step_span_reported=runtime_step_span_reported,
        runtime_step_span_from_steps=runtime_step_span_from_steps,
        runtime_steps=runtime_steps,
        runtime_steps_increasing=runtime_steps_increasing,
        runtime_steps_uniform=runtime_steps_uniform,
        runtime_hashes=runtime_hashes,
        runtime_hash_count=runtime_hash_count,
        runtime_hash_unique_count=runtime_hash_unique_count,
        min_avg_frames=args.min_avg_frames,
    )
    time_average_gate = "pass" if not time_average_evidence_reasons else "fail"
    time_averaging_fidelity_class = classify_time_averaging_fidelity(
        time_average_gate=time_average_gate,
        runtime_final_window_frame_count_gate=runtime_final_window_frame_count_gate["gate"],
        stationarity_gate=stationarity_gate,
        runtime_selected_last_window=runtime_selected_last_window,
        runtime_average_shortfall_reason=runtime_average_shortfall_reason,
        runtime_step_shortfall_reason=runtime_step_shortfall_reason,
    )
    if time_average_gate != "pass":
        reasons.append("native_time_average_evidence_gate_not_pass")

    expected_vector = parse_vector(args.wind_vector)
    actual_vector = shared_wind_vector(shared)
    wind_delta = vector_delta(actual_vector, expected_vector) if expected_vector else None
    if expected_vector and (wind_delta is None or wind_delta > args.wind_vector_tolerance):
        reasons.append("wind_vector_mismatch")

    shared_u_ref = as_float(shared.get("ReferenceWindSpeedMps"))
    metadata_u_ref = as_float(metadata.get("ReferenceWindSpeedMps") or metadata.get("WindSpeed"))
    u_ref = shared_u_ref if shared_u_ref is not None else metadata_u_ref
    af_csv = Path(args.af_csv).expanduser().resolve() if args.af_csv else None
    u_ref_from_af = af_u_at_reference_height(af_csv, args.z_ref)
    if args.u_ref is not None and (u_ref is None or abs(u_ref - args.u_ref) > args.u_ref_tolerance):
        reasons.append("uref_mismatch")
    if (
        args.u_ref is not None
        and u_ref_from_af is not None
        and abs(args.u_ref - u_ref_from_af) > args.u_ref_tolerance
    ):
        reasons.append("uref_af_profile_mismatch")
        reasons.append(
            f"uref_af_profile_delta_{reason_token(f'{abs(args.u_ref - u_ref_from_af):.12g}')}"
        )
    if (
        u_ref is not None
        and u_ref_from_af is not None
        and abs(u_ref - u_ref_from_af) > args.u_ref_tolerance
    ):
        reasons.append("metadata_uref_af_profile_mismatch")

    af_sha = sha256_file(af_csv)
    manifest_af_sha = str(shared.get("WindProfileCsvSha256") or "").strip().lower()
    if af_csv:
        if not af_sha:
            reasons.append("af_csv_missing")
        elif manifest_af_sha and manifest_af_sha != af_sha:
            reasons.append("af_csv_hash_mismatch")
    if str(shared.get("WindProfile") or "").strip().lower() != "customtable":
        reasons.append("wind_profile_not_customtable")

    inlet_source_gate = str(inlet_source_audit.get("inlet_source_gate") or "").strip().lower()
    paper_inlet_source_gate = str(inlet_source_audit.get("paper_grade_inlet_source_gate") or "").strip().lower()
    inlet_distribution_consistent = as_bool(inlet_source_audit.get("inlet_source_distribution_consistent"))
    inlet_velocity_only = as_bool(inlet_source_audit.get("inlet_source_velocity_field_only"))
    inlet_source_method_class = str(inlet_source_audit.get("inlet_source_method_class") or "").strip()
    inlet_source_fidelity_class = str(
        inlet_source_audit.get("inlet_source_turbulent_inflow_fidelity_class") or ""
    ).strip()
    inlet_has_correlated_velocity_only = as_bool(
        inlet_source_audit.get("inlet_source_has_correlated_velocity_field_only")
    )
    inlet_has_uncorrelated_rms_velocity_only = as_bool(
        inlet_source_audit.get("inlet_source_has_uncorrelated_rms_velocity_field_only")
    )
    inlet_requires_distribution_reconstruction = as_bool(
        inlet_source_audit.get("inlet_source_requires_distribution_reconstruction")
    )
    inlet_correlation_model = str(inlet_source_audit.get("synthetic_inlet_correlation_model") or "").strip()
    inlet_distribution_route = str(inlet_source_audit.get("inlet_distribution_route") or "").strip()
    inlet_distribution_route_gate = str(inlet_source_audit.get("inlet_distribution_route_gate") or "").strip().lower()
    inlet_has_equilibrium_boundaries_define = as_bool(
        inlet_source_audit.get("has_equilibrium_boundaries_define")
    )
    inlet_has_type_e_equilibrium_boundary_route = as_bool(
        inlet_source_audit.get("has_type_e_equilibrium_boundary_route")
    )
    inlet_has_reynolds_metadata_claim = as_bool(
        inlet_source_audit.get("has_reynolds_stress_tensor_metadata_claim")
    )
    inlet_has_reynolds_diagonal_source = as_bool(
        inlet_source_audit.get("has_reynolds_stress_diagonal_source_evidence")
    )
    inlet_has_reynolds_offdiagonal_source = as_bool(
        inlet_source_audit.get("has_reynolds_stress_offdiagonal_source_evidence")
    )
    inlet_has_reynolds_full_tensor_source = as_bool(
        inlet_source_audit.get("has_reynolds_stress_full_tensor_source_evidence")
    )
    inlet_has_uncorrelated_random = as_bool(inlet_source_audit.get("has_uncorrelated_random_inlet"))
    inlet_uncorrelated_random_patterns = split_scalar_list(
        inlet_source_audit.get("uncorrelated_random_inlet_patterns")
    )
    inlet_recommended_next_action = str(inlet_source_audit.get("recommended_next_action") or "").strip()
    inlet_has_three_component_velocity_write = as_bool(
        inlet_source_audit.get("has_three_component_velocity_write")
    )
    inlet_has_three_component_fluctuation_evidence = as_bool(
        inlet_source_audit.get("has_three_component_fluctuation_evidence")
    )
    inlet_has_k_driven_three_component_stg = as_bool(
        inlet_source_audit.get("has_k_driven_three_component_stg")
    )
    inlet_has_component_phase_decorrelation = as_bool(
        inlet_source_audit.get("has_component_phase_decorrelation")
    )
    inlet_has_temporal_filter_state = as_bool(inlet_source_audit.get("has_temporal_filter_state"))
    inlet_has_mean_preserving_correction = as_bool(
        inlet_source_audit.get("has_mean_preserving_inlet_correction")
    )
    inlet_has_layerwise_mean_preserving_correction = as_bool(
        inlet_source_audit.get("has_layerwise_mean_preserving_inlet_correction")
    )
    inlet_has_streamwise_clipping_control = as_bool(
        inlet_source_audit.get("has_streamwise_clipping_control")
    )
    inlet_streamwise_min_fraction = as_float(inlet_source_audit.get("streamwise_min_fraction"))
    inlet_streamwise_clipping_enabled = as_bool(inlet_source_audit.get("streamwise_clipping_enabled"))
    inlet_has_legacy_hardcoded_streamwise_clipping = as_bool(
        inlet_source_audit.get("has_legacy_hardcoded_streamwise_clipping")
    )
    inlet_stg_evidence_required = (
        "stg" in inlet_source_method_class.lower()
        or "stg" in inlet_correlation_model.lower()
        or as_bool(inlet_source_audit.get("has_synthetic_inlet_function")) is True
    )
    inlet_source_reasons = split_scalar_list(inlet_source_audit.get("inlet_source_gate_reasons"))
    paper_inlet_source_reasons = split_scalar_list(inlet_source_audit.get("paper_grade_inlet_source_gate_reasons"))
    if not inlet_source_audit:
        reasons.append("inlet_source_audit_missing")
    if inlet_source_gate != "pass":
        reasons.append("inlet_source_gate_not_pass")
    if paper_inlet_source_gate != "pass":
        reasons.append("paper_grade_inlet_source_gate_not_pass")
    if inlet_distribution_consistent is not True:
        reasons.append("inlet_source_not_distribution_consistent")
    if inlet_velocity_only is True:
        reasons.append("inlet_source_velocity_field_only")
    if inlet_distribution_route_gate != "pass":
        reasons.append("inlet_distribution_route_gate_not_pass")
    if inlet_distribution_route == "velocity_field_only_without_equilibrium_boundary_define":
        reasons.append("inlet_distribution_route_missing_equilibrium_boundaries_define")
    if inlet_has_equilibrium_boundaries_define is False and inlet_distribution_route != "direct_setup_distribution_write":
        reasons.append("inlet_source_missing_equilibrium_boundaries_define")
    if inlet_has_type_e_equilibrium_boundary_route is False and inlet_distribution_route != "direct_setup_distribution_write":
        reasons.append("inlet_source_missing_type_e_equilibrium_boundary_route")
    if inlet_stg_evidence_required and inlet_has_three_component_velocity_write is not True:
        reasons.append("inlet_source_missing_three_component_velocity_write_evidence")
    if inlet_stg_evidence_required and inlet_has_three_component_fluctuation_evidence is not True:
        reasons.append("inlet_source_missing_three_component_fluctuation_evidence")
    if inlet_stg_evidence_required and inlet_has_k_driven_three_component_stg is not True:
        reasons.append("inlet_source_missing_k_driven_three_component_stg_evidence")
    if inlet_stg_evidence_required and inlet_has_component_phase_decorrelation is not True:
        reasons.append("inlet_source_missing_component_phase_decorrelation")
    if inlet_stg_evidence_required and inlet_has_temporal_filter_state is not True:
        reasons.append("inlet_source_missing_temporal_filter_state")
    if inlet_stg_evidence_required and inlet_has_mean_preserving_correction is not True:
        reasons.append("inlet_source_missing_mean_preserving_inlet_correction")
    if inlet_stg_evidence_required and inlet_has_layerwise_mean_preserving_correction is not True:
        reasons.append("inlet_source_missing_layerwise_mean_preserving_inlet_correction")
    if inlet_stg_evidence_required and inlet_has_streamwise_clipping_control is not True:
        reasons.append("inlet_source_missing_streamwise_clipping_control")
    if inlet_streamwise_clipping_enabled is True:
        reasons.append("inlet_source_streamwise_clipping_enabled")
    if (
        inlet_has_legacy_hardcoded_streamwise_clipping is True
        or "synthetic_inlet_uses_legacy_hardcoded_streamwise_clipping" in inlet_source_reasons
    ):
        reasons.append("inlet_source_uses_legacy_hardcoded_streamwise_clipping")
    if (
        inlet_has_uncorrelated_random is True
        or inlet_correlation_model == "uncorrelated_random_rms_velocity_field_only"
        or "synthetic_inlet_uses_uncorrelated_random_rms" in inlet_source_reasons
    ):
        reasons.append("inlet_source_uses_uncorrelated_random_rms")
    inlet_source_hash_check = append_setup_hash_reason(reasons, "inlet_source", inlet_source_audit, setup_sha)

    inlet_profile_gate = str(inlet_profile_audit.get("inlet_profile_gate") or "").strip().upper()
    inlet_u_profile_gate = str(inlet_profile_audit.get("inlet_u_profile_gate") or "").strip().upper()
    inlet_k_profile_gate = str(inlet_profile_audit.get("inlet_k_profile_gate") or "").strip().upper()
    inlet_profile_time_gate = str(inlet_profile_audit.get("time_averaging_gate") or "").strip().upper()
    inlet_profile_frame_count = as_int(inlet_profile_audit.get("frame_count"))
    if not inlet_profile_audit:
        reasons.append("inlet_profile_audit_missing")
    if inlet_profile_gate != "PASS":
        reasons.append("inlet_profile_gate_not_pass")
    if inlet_u_profile_gate != "PASS":
        reasons.append("inlet_u_profile_gate_not_pass")
    if inlet_k_profile_gate != "PASS":
        reasons.append("inlet_k_profile_gate_not_pass")
    if inlet_profile_time_gate != "PASS":
        reasons.append("inlet_profile_time_averaging_gate_not_pass")
    if inlet_profile_frame_count is None or inlet_profile_frame_count < args.min_avg_frames:
        reasons.append("inlet_profile_frame_count_below_minimum")
    inlet_profile_span_check = append_source_step_span_reasons(
        reasons,
        "inlet_profile",
        inlet_profile_audit,
        args.min_avg_step_span,
    )
    inlet_profile_window_check = append_source_window_reasons(
        reasons,
        "inlet_profile",
        inlet_profile_audit,
        runtime_steps,
        runtime_hashes,
    )
    inlet_profile_af_sha = str(inlet_profile_audit.get("af_csv_sha256") or "").strip().lower()
    inlet_profile_af_hash_matches = bool(inlet_profile_af_sha) and (
        (bool(af_sha) and inlet_profile_af_sha == af_sha)
        or (bool(manifest_af_sha) and inlet_profile_af_sha == manifest_af_sha)
    )
    if inlet_profile_audit:
        if not inlet_profile_af_sha:
            reasons.append("inlet_profile_af_csv_sha256_missing")
        elif not inlet_profile_af_hash_matches:
            reasons.append("inlet_profile_af_csv_sha256_mismatch")

    inlet_correlation_gate = str(inlet_correlation_audit.get("inlet_correlation_gate") or "").strip().upper()
    inlet_k_variance_gate = str(inlet_correlation_audit.get("inlet_k_variance_gate") or "").strip().upper()
    inlet_k_variance_ratio = as_float(inlet_correlation_audit.get("inlet_streamwise_variance_to_k_ratio"))
    inlet_k_variance_target = as_float(inlet_correlation_audit.get("inlet_streamwise_variance_target_from_k"))
    inlet_tke_gate = str(inlet_correlation_audit.get("inlet_tke_gate") or "").strip().upper()
    inlet_tke_target = as_float(inlet_correlation_audit.get("inlet_tke_target_from_af_k"))
    inlet_tke_ratio = as_float(inlet_correlation_audit.get("inlet_tke_to_k_ratio"))
    inlet_mean_tke = as_float(inlet_correlation_audit.get("mean_turbulent_kinetic_energy_from_components"))
    inlet_correlation_frame_count = as_int(inlet_correlation_audit.get("frame_count"))
    if not inlet_correlation_audit:
        reasons.append("inlet_correlation_audit_missing")
    if inlet_correlation_gate != "PASS":
        reasons.append("inlet_correlation_gate_not_pass")
    if inlet_k_variance_gate != "PASS":
        reasons.append("inlet_k_variance_gate_not_pass")
    if inlet_tke_gate != "PASS":
        reasons.append("inlet_tke_gate_not_pass")
    if inlet_correlation_frame_count is None or inlet_correlation_frame_count < args.min_avg_frames:
        reasons.append("inlet_correlation_frame_count_below_minimum")
    inlet_correlation_span_check = append_source_step_span_reasons(
        reasons,
        "inlet_correlation",
        inlet_correlation_audit,
        args.min_avg_step_span,
    )
    inlet_correlation_window_check = append_source_window_reasons(
        reasons,
        "inlet_correlation",
        inlet_correlation_audit,
        runtime_steps,
        runtime_hashes,
    )

    native_inlet_equivalence_reasons = build_inlet_equivalence_evidence_reasons(
        inlet_source_audit=inlet_source_audit,
        inlet_source_hash_check=inlet_source_hash_check,
        inlet_profile_audit=inlet_profile_audit,
        inlet_profile_af_hash_matches=inlet_profile_af_hash_matches,
        inlet_profile_window_check=inlet_profile_window_check,
        inlet_correlation_audit=inlet_correlation_audit,
        inlet_correlation_window_check=inlet_correlation_window_check,
        min_avg_frames=args.min_avg_frames,
        min_avg_step_span=args.min_avg_step_span,
    )
    native_inlet_equivalence_gate = "pass" if not native_inlet_equivalence_reasons else "fail"
    if native_inlet_equivalence_gate != "pass":
        reasons.append("native_inlet_equivalence_gate_not_pass")

    boundary_source_gate = str(boundary_source_audit.get("boundary_source_gate") or "").strip().lower()
    paper_boundary_source_gate = str(boundary_source_audit.get("paper_grade_boundary_source_gate") or "").strip().lower()
    boundary_source_equivalent = as_bool(boundary_source_audit.get("boundary_source_wind_tunnel_equivalent"))
    boundary_source_simplified = as_bool(boundary_source_audit.get("boundary_source_simplified"))
    boundary_source_method_class = str(boundary_source_audit.get("boundary_source_method_class") or "").strip()
    boundary_source_fidelity_class = str(boundary_source_audit.get("boundary_source_fidelity_class") or "").strip()
    boundary_source_has_complete_wind_tunnel_evidence = as_bool(
        boundary_source_audit.get("boundary_source_has_complete_wind_tunnel_evidence")
    )
    boundary_source_has_empty_advanced_method_stub_only = as_bool(
        boundary_source_audit.get("boundary_source_has_empty_advanced_method_stub_only")
    )
    boundary_source_advanced_code_evidence = as_bool(
        boundary_source_audit.get("boundary_source_advanced_code_evidence")
    )
    boundary_source_has_paper_grade_outlet = as_bool(boundary_source_audit.get("has_paper_grade_outlet_source"))
    boundary_source_has_paper_grade_side_top = as_bool(boundary_source_audit.get("has_paper_grade_side_top_source"))
    boundary_source_has_paper_grade_rough_wall = as_bool(boundary_source_audit.get("has_paper_grade_rough_wall_source"))
    boundary_source_has_paper_grade_development = as_bool(
        boundary_source_audit.get("has_paper_grade_development_source")
    )
    boundary_source_has_non_reflecting_outlet_method = as_bool(
        boundary_source_audit.get("has_non_reflecting_outlet_method")
    )
    boundary_source_has_non_reflecting_outlet_state = as_bool(
        boundary_source_audit.get("has_non_reflecting_outlet_state_evidence")
    )
    boundary_source_has_periodic_side_top_method = as_bool(
        boundary_source_audit.get("has_periodic_side_top_method")
    )
    boundary_source_has_periodic_pair_mapping = as_bool(
        boundary_source_audit.get("has_periodic_pair_mapping_evidence")
    )
    boundary_source_has_rough_wall_function_method = as_bool(
        boundary_source_audit.get("has_rough_wall_function_method")
    )
    boundary_source_has_rough_wall_parameter = as_bool(
        boundary_source_audit.get("has_rough_wall_parameter_evidence")
    )
    boundary_source_has_rough_wall_action = as_bool(
        boundary_source_audit.get("has_rough_wall_action_evidence")
    )
    boundary_source_has_precursor_recycling_method = as_bool(
        boundary_source_audit.get("has_precursor_or_recycling_boundary_method")
    )
    boundary_source_has_precursor_recycling_field = as_bool(
        boundary_source_audit.get("has_precursor_or_recycling_boundary_field_evidence")
    )
    boundary_source_missing_paper_evidence = split_scalar_list(
        boundary_source_audit.get("missing_paper_grade_source_evidence")
    )
    if not boundary_source_audit:
        reasons.append("boundary_source_audit_missing")
    if boundary_source_gate != "pass":
        reasons.append("boundary_source_gate_not_pass")
    if paper_boundary_source_gate != "pass":
        reasons.append("paper_grade_boundary_source_gate_not_pass")
    if boundary_source_equivalent is not True:
        reasons.append("boundary_source_not_wind_tunnel_equivalent")
    if boundary_source_simplified is True:
        reasons.append("boundary_source_simplified")
    if boundary_source_fidelity_class != "wind_tunnel_equivalent_complete":
        reasons.append(f"boundary_source_fidelity_class_not_paper_grade_{boundary_source_fidelity_class or 'missing'}")
    if boundary_source_has_complete_wind_tunnel_evidence is not True:
        reasons.append("boundary_source_has_complete_wind_tunnel_evidence_not_true")
    if boundary_source_has_empty_advanced_method_stub_only is True:
        reasons.append("boundary_source_has_empty_advanced_method_stub_only")
    if boundary_source_advanced_code_evidence is not True:
        reasons.append("boundary_source_advanced_code_evidence_not_true")
    for field in boundary_source_missing_paper_evidence:
        reasons.append(f"boundary_source_missing_paper_grade_evidence_{field}")
    boundary_source_hash_check = append_setup_hash_reason(reasons, "boundary_source", boundary_source_audit, setup_sha)

    boundary_protocol_gate = str(boundary_protocol_audit.get("boundary_protocol_gate") or "").strip().lower()
    boundary_evidence_gate = str(boundary_protocol_audit.get("boundary_evidence_gate") or "").strip().lower()
    boundary_run_identity_gate = str(boundary_protocol_audit.get("boundary_run_identity_gate") or "").strip().lower()
    boundary_run_identity_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_run_identity_gate_reasons"))
    boundary_evidence_metadata_hash_matches = as_bool(
        boundary_protocol_audit.get("evidence_metadata_sha256_matches_current")
    )
    boundary_evidence_hashed = as_bool(boundary_protocol_audit.get("boundary_evidence_files_all_hashed"))
    boundary_equivalence_supported = as_bool(boundary_protocol_audit.get("boundary_equivalence_supported"))
    boundary_evidence_class_supported = as_bool(boundary_protocol_audit.get("boundary_evidence_class_supported"))
    boundary_condition_fields_supported = as_bool(
        boundary_protocol_audit.get("boundary_condition_fields_supported")
    )
    boundary_clearance_numeric_gate = str(boundary_protocol_audit.get("clearance_numeric_gate") or "").strip().lower()
    boundary_blockage_gate = str(boundary_protocol_audit.get("blockage_gate") or "").strip().lower()
    boundary_protocol_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_protocol_gate_reasons"))
    boundary_condition_support_reasons = split_scalar_list(
        boundary_protocol_audit.get("boundary_condition_support_reasons")
    )
    boundary_clearance_reasons = split_scalar_list(
        boundary_protocol_audit.get("clearance_numeric_gate_reasons")
    )
    boundary_missing_evidence_fields = split_scalar_list(boundary_protocol_audit.get("missing_evidence_fields"))
    boundary_unsupported_condition_fields = split_scalar_list(
        boundary_protocol_audit.get("unsupported_boundary_condition_fields")
    )
    if not boundary_unsupported_condition_fields:
        prefix = "unsupported_boundary_condition_fields:"
        for support_reason in boundary_condition_support_reasons:
            if support_reason.startswith(prefix):
                boundary_unsupported_condition_fields = split_scalar_list(support_reason[len(prefix) :])
                break
    boundary_evidence_files_missing = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_missing"))
    boundary_evidence_files_empty = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_empty"))
    boundary_evidence_files_unreadable = split_scalar_list(
        boundary_protocol_audit.get("boundary_evidence_files_unreadable")
    )
    boundary_required_support_fields_missing_or_false = [
        field for field in REQUIRED_BOUNDARY_SUPPORT_FIELDS if as_bool(boundary_protocol_audit.get(field)) is not True
    ]
    if not boundary_protocol_audit:
        reasons.append("boundary_protocol_audit_missing")
    if boundary_protocol_gate != "pass":
        reasons.append("boundary_protocol_gate_not_pass")
    if boundary_evidence_gate != "pass":
        reasons.append("boundary_evidence_gate_not_pass")
    if boundary_run_identity_gate != "pass":
        reasons.append("boundary_run_identity_gate_not_pass")
    if boundary_evidence_metadata_hash_matches is not True:
        reasons.append("boundary_evidence_metadata_sha256_not_bound_to_current_run")
    if boundary_evidence_hashed is not True:
        reasons.append("boundary_evidence_files_not_hashed")
    if boundary_protocol_audit:
        if boundary_equivalence_supported is not True:
            reasons.append("boundary_equivalence_not_supported")
        if boundary_evidence_class_supported is not True:
            reasons.append("boundary_evidence_class_not_supported")
        if boundary_condition_fields_supported is not True:
            reasons.append("boundary_condition_fields_not_supported")
        if boundary_clearance_numeric_gate != "pass":
            reasons.append("boundary_clearance_numeric_gate_not_pass")
        if boundary_blockage_gate != "pass":
            reasons.append("boundary_blockage_gate_not_pass")
        if boundary_missing_evidence_fields:
            reasons.append("boundary_missing_evidence_fields_present")
            for field in boundary_missing_evidence_fields:
                reasons.append(f"boundary_missing_evidence_field_{field}")
        if boundary_unsupported_condition_fields:
            reasons.append("boundary_unsupported_condition_fields_present")
            for field in boundary_unsupported_condition_fields:
                reasons.append(f"boundary_condition_field_{field}_not_supported")
        if boundary_required_support_fields_missing_or_false:
            reasons.append("boundary_required_support_fields_missing_or_false")
            for field in boundary_required_support_fields_missing_or_false:
                reasons.append(f"boundary_required_support_field_{field}_not_supported")
        for clearance_reason in boundary_clearance_reasons:
            if clearance_reason != "clearance_numeric_evidence_complete":
                reasons.append(f"boundary_clearance_{clearance_reason}")
        for path in boundary_evidence_files_missing:
            reasons.append(f"boundary_evidence_file_missing_{Path(path).name or 'unnamed'}")
        for path in boundary_evidence_files_empty:
            reasons.append(f"boundary_evidence_file_empty_{Path(path).name or 'unnamed'}")
        for path in boundary_evidence_files_unreadable:
            reasons.append(f"boundary_evidence_file_unreadable_{Path(path).name or 'unnamed'}")
        for identity_reason in boundary_run_identity_reasons:
            if identity_reason != "boundary_evidence_bound_to_current_run":
                reasons.append(f"boundary_identity_{identity_reason}")

    boundary_runtime_gate = str(boundary_runtime_audit.get("boundary_runtime_gate") or "").strip().lower()
    boundary_runtime_traceability_gate = str(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate") or ""
    ).strip().lower()
    boundary_runtime_profile_gate = str(
        boundary_runtime_audit.get("boundary_runtime_profile_preservation_gate") or ""
    ).strip().lower()
    boundary_runtime_inlet_gate = str(boundary_runtime_audit.get("boundary_runtime_inlet_gate") or "").strip().lower()
    boundary_runtime_side_top_gate = str(boundary_runtime_audit.get("boundary_runtime_side_top_gate") or "").strip().lower()
    boundary_runtime_side_top_normal_gate = str(
        boundary_runtime_audit.get("boundary_runtime_side_top_normal_leakage_gate") or ""
    ).strip().lower()
    boundary_runtime_outlet_gate = str(boundary_runtime_audit.get("boundary_runtime_outlet_gate") or "").strip().lower()
    boundary_runtime_reasons = split_scalar_list(boundary_runtime_audit.get("boundary_runtime_gate_reasons"))
    boundary_runtime_traceability_reasons = split_scalar_list(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate_reasons")
    )
    boundary_runtime_steps = audit_source_steps(boundary_runtime_audit)
    boundary_runtime_hashes = audit_source_hashes(boundary_runtime_audit)
    boundary_runtime_source_step_span = source_step_span_from_steps(boundary_runtime_steps)
    boundary_runtime_reported_source_step_span = as_int(boundary_runtime_audit.get("source_step_span"))
    if boundary_runtime_source_step_span is None:
        boundary_runtime_source_step_span = boundary_runtime_reported_source_step_span
    boundary_runtime_frame_count = as_int(boundary_runtime_audit.get("frame_count"))
    boundary_runtime_selected_last_window = as_bool(boundary_runtime_audit.get("selected_last_window"))
    boundary_runtime_steps_increasing = source_steps_strictly_increasing(boundary_runtime_steps)
    boundary_runtime_steps_uniform = source_steps_uniformly_spaced(boundary_runtime_steps)
    boundary_runtime_hash_count = len(boundary_runtime_hashes)
    boundary_runtime_hash_unique_count = len(set(boundary_runtime_hashes))
    runtime_step_hash_pairs = step_hash_pairs_from_steps_hashes(runtime_steps, runtime_hashes)
    boundary_runtime_step_hash_pairs = audit_source_step_hash_pairs(boundary_runtime_audit)
    boundary_runtime_steps_match_runtime = bool(runtime_steps) and boundary_runtime_steps == runtime_steps
    boundary_runtime_hashes_match_runtime = (
        bool(runtime_hashes)
        and bool(boundary_runtime_hashes)
        and set(boundary_runtime_hashes) == set(runtime_hashes)
    )
    boundary_runtime_step_hash_pairs_match_runtime = (
        bool(runtime_step_hash_pairs)
        and bool(boundary_runtime_step_hash_pairs)
        and boundary_runtime_step_hash_pairs == runtime_step_hash_pairs
    )
    if not boundary_runtime_audit:
        reasons.append("boundary_runtime_audit_missing")
    else:
        if boundary_runtime_gate != "pass":
            reasons.append("boundary_runtime_gate_not_pass")
        if boundary_runtime_traceability_gate != "pass":
            reasons.append("boundary_runtime_traceability_gate_not_pass")
        if boundary_runtime_profile_gate != "pass":
            reasons.append("boundary_runtime_profile_preservation_gate_not_pass")
        if boundary_runtime_inlet_gate != "pass":
            reasons.append("boundary_runtime_inlet_gate_not_pass")
        if boundary_runtime_side_top_gate != "pass":
            reasons.append("boundary_runtime_side_top_gate_not_pass")
        if boundary_runtime_side_top_normal_gate != "pass":
            reasons.append("boundary_runtime_side_top_normal_leakage_gate_not_pass")
        if boundary_runtime_outlet_gate != "pass":
            reasons.append("boundary_runtime_outlet_gate_not_pass")
        if boundary_runtime_frame_count is None or boundary_runtime_frame_count < args.min_avg_frames:
            reasons.append("boundary_runtime_frame_count_below_minimum")
        if boundary_runtime_source_step_span is None or boundary_runtime_source_step_span < args.min_avg_step_span:
            reasons.append("boundary_runtime_source_step_span_below_minimum")
        if boundary_runtime_selected_last_window is not True:
            reasons.append("boundary_runtime_selected_last_window_not_true")
        if not boundary_runtime_steps:
            reasons.append("boundary_runtime_source_time_steps_missing")
        if not boundary_runtime_steps_match_runtime:
            reasons.append("boundary_runtime_source_time_steps_mismatch_runtime")
        if not boundary_runtime_steps_increasing:
            reasons.append("boundary_runtime_source_steps_not_strictly_increasing")
        if not boundary_runtime_steps_uniform:
            reasons.append("boundary_runtime_source_step_spacing_not_uniform")
        if not boundary_runtime_hashes_match_runtime:
            reasons.append("boundary_runtime_source_vtk_sha256_mismatch_runtime")
        if not boundary_runtime_step_hash_pairs_match_runtime:
            reasons.append("boundary_runtime_source_step_hash_pairs_mismatch_runtime")
        if boundary_runtime_hash_count != len(boundary_runtime_steps):
            reasons.append("boundary_runtime_source_vtk_sha256_count_mismatch_time_steps")
        if boundary_runtime_hash_count < args.min_avg_frames:
            reasons.append("boundary_runtime_source_vtk_sha256_count_below_minimum")
        if boundary_runtime_hash_unique_count != boundary_runtime_hash_count:
            reasons.append("boundary_runtime_source_vtk_sha256_not_unique")
        for reason in boundary_runtime_reasons:
            if reason != "boundary_runtime_faces_preserve_af_profile":
                reasons.append(f"boundary_runtime_{reason}")
        for reason in boundary_runtime_traceability_reasons:
            if reason != "boundary_runtime_window_traceable":
                reasons.append(f"boundary_runtime_traceability_{reason}")

    native_boundary_equivalence_reasons = build_boundary_equivalence_evidence_reasons(
        boundary_source_audit=boundary_source_audit,
        boundary_source_hash_check=boundary_source_hash_check,
        boundary_protocol_audit=boundary_protocol_audit,
        boundary_runtime_audit=boundary_runtime_audit,
        min_avg_frames=args.min_avg_frames,
        min_avg_step_span=args.min_avg_step_span,
    )
    native_boundary_equivalence_gate = "pass" if not native_boundary_equivalence_reasons else "fail"
    if native_boundary_equivalence_gate != "pass":
        reasons.append("native_boundary_equivalence_gate_not_pass")

    expected_component = str(args.expected_compared_component or "").strip()
    failed_probe_rows = [row for row in probe_rows if probe_row_failed(row)]
    valid_probe_rows = [row for row in probe_rows if not probe_row_failed(row)]
    official_probe_set_field_names = [
        "official_probe_set_row_count",
        "official_expected_row_count",
        "official_probe_ids_unique",
        "official_missing_probe_id_count",
        "official_duplicate_probe_ids",
        "official_expected_z",
        "official_expected_z_tolerance",
        "official_z_match_count",
        "official_z_mismatch_count",
    ]
    official_probe_set_unique_values = {
        field: sorted(
            {
                row_value(row, field)
                for row in probe_rows
                if row_value(row, field)
            }
        )
        for field in official_probe_set_field_names
    }
    official_probe_set_reasons: List[str] = []
    for field, values in official_probe_set_unique_values.items():
        if len(values) > 1:
            official_probe_set_reasons.append(f"mixed_{field}:{len(values)}")
    official_probe_set_row_count = as_int(next(iter(official_probe_set_unique_values["official_probe_set_row_count"]), ""))
    official_expected_row_count = as_int(next(iter(official_probe_set_unique_values["official_expected_row_count"]), ""))
    official_probe_ids_unique = as_bool(next(iter(official_probe_set_unique_values["official_probe_ids_unique"]), ""))
    official_missing_probe_id_count = as_int(next(iter(official_probe_set_unique_values["official_missing_probe_id_count"]), ""))
    official_duplicate_probe_ids = ";".join(official_probe_set_unique_values["official_duplicate_probe_ids"])
    official_expected_z = next(iter(official_probe_set_unique_values["official_expected_z"]), "")
    official_expected_z_tolerance = next(iter(official_probe_set_unique_values["official_expected_z_tolerance"]), "")
    official_z_match_count = as_int(next(iter(official_probe_set_unique_values["official_z_match_count"]), ""))
    official_z_mismatch_count = as_int(next(iter(official_probe_set_unique_values["official_z_mismatch_count"]), ""))
    if official_expected_row_count is None:
        official_probe_set_reasons.append("official_expected_row_count_missing")
    elif official_probe_set_row_count != official_expected_row_count:
        official_probe_set_reasons.append(
            f"official_row_count_{official_probe_set_row_count}_does_not_match_expected_{official_expected_row_count}"
        )
    if not str(official_expected_z or "").strip():
        official_probe_set_reasons.append("official_expected_z_missing")
    if official_probe_set_row_count is None:
        official_probe_set_reasons.append("official_probe_set_row_count_missing")
    if official_probe_ids_unique is None:
        official_probe_set_reasons.append("official_probe_ids_unique_missing")
    if official_probe_ids_unique is False:
        official_probe_set_reasons.append("official_probe_ids_not_unique")
    if official_missing_probe_id_count and official_missing_probe_id_count > 0:
        official_probe_set_reasons.append(f"official_missing_probe_id_count:{official_missing_probe_id_count}")
    if official_duplicate_probe_ids:
        official_probe_set_reasons.append(f"official_duplicate_probe_ids:{official_duplicate_probe_ids}")
    if official_z_mismatch_count and official_z_mismatch_count > 0:
        official_probe_set_reasons.append(f"official_z_mismatch_count:{official_z_mismatch_count}")
    official_probe_set_gate = "pass" if not official_probe_set_reasons else "fail"
    probe_official_height = build_probe_official_height_gate(
        official_expected_z,
        official_z_match_count,
        official_z_mismatch_count,
        official_probe_set_row_count,
    )
    probe_official_height_gate = probe_official_height["gate"]
    probe_official_height_reasons = probe_official_height["reasons"]
    compared_components = {
        row_value(row, "compared_component", "ComparedComponent")
        for row in valid_probe_rows
        if row_value(row, "compared_component", "ComparedComponent")
    }
    compared_component_values_csv = ";".join(sorted(compared_components))
    compared_component_mismatch_reason = ""
    if not probe_rows:
        reasons.append("probe_audit_missing_or_empty")
    if probe_rows and not valid_probe_rows:
        reasons.append("probe_audit_has_no_valid_rows")
    if failed_probe_rows:
        reasons.append("probe_audit_has_failed_rows")
    if official_probe_set_gate != "pass":
        reasons.append("official_probe_set_gate_not_pass")
        for reason in official_probe_set_reasons:
            reasons.append(f"official_probe_set_gate:{reason}")
    if probe_official_height_gate != "pass":
        reasons.append("probe_official_height_gate_not_pass")
        for reason in probe_official_height_reasons:
            reasons.append(f"probe_official_height_gate:{reason}")
    if expected_component and compared_components != {expected_component}:
        reasons.append("probe_compared_component_mismatch")
        compared_component_mismatch_reason = (
            f"probe_compared_component_{reason_token(compared_component_values_csv)}"
            f"_expected_{reason_token(expected_component)}"
        )
        reasons.append(compared_component_mismatch_reason)

    official_coordinates, official_coordinate_error = build_official_coordinate_lookup(
        official_path,
        args.case,
        args.wind_direction_label,
    )
    probe_id_column = find_csv_column(valid_probe_rows, ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"])
    official_probe_ids = set(official_coordinates.keys())
    probe_ids: List[str] = []
    seen_probe_ids = set()
    duplicate_probe_ids = set()
    missing_probe_id_count = 0
    if valid_probe_rows and not probe_id_column:
        reasons.append("probe_id_column_missing")
    for row in valid_probe_rows:
        probe_id = normalized_column_key(str(row.get(probe_id_column) or "").strip()) if probe_id_column else ""
        if not probe_id:
            missing_probe_id_count += 1
            continue
        if probe_id in seen_probe_ids:
            duplicate_probe_ids.add(probe_id)
        seen_probe_ids.add(probe_id)
        probe_ids.append(probe_id)
    unmatched_probe_ids = sorted(set(probe_ids) - official_probe_ids) if official_probe_ids else sorted(set(probe_ids))
    missing_official_probe_ids = sorted(official_probe_ids - set(probe_ids)) if official_probe_ids else []
    duplicate_probe_ids_sorted = sorted(duplicate_probe_ids)
    official_probe_coverage_ratio = (
        len(official_probe_ids & set(probe_ids)) / len(official_probe_ids)
        if official_probe_ids
        else None
    )
    official_probe_coverage_reason = ""
    if valid_probe_rows:
        if official_coordinate_error:
            reasons.append("probe_official_identity_error:" + official_coordinate_error)
        if missing_probe_id_count:
            reasons.append("probe_id_missing")
            reasons.append(count_reason("probe_id_missing_count", missing_probe_id_count))
        if duplicate_probe_ids:
            reasons.append("probe_id_duplicate")
            reasons.append(count_reason("probe_id_duplicate_count", len(duplicate_probe_ids)))
        if unmatched_probe_ids:
            reasons.append("probe_unmatched_official_ids")
            reasons.append(count_reason("probe_unmatched_official_id_count", len(unmatched_probe_ids)))
        if missing_official_probe_ids or official_probe_coverage_ratio != 1.0:
            reasons.append("probe_official_probe_coverage_incomplete")
            official_probe_coverage_reason = (
                f"probe_official_coverage_{len(official_probe_ids & set(probe_ids))}"
                f"_of_{len(official_probe_ids)}"
            )
            reasons.append(official_probe_coverage_reason)
    coordinate_summary = probe_official_coordinate_delta_summary(
        valid_probe_rows,
        official_coordinates,
        probe_id_column,
    )
    official_coordinate_deltas = coordinate_summary["deltas"]
    official_coordinate_recomputed_count = coordinate_summary["recomputed_count"]
    missing_official_coordinate_delta_count = coordinate_summary["missing_count"]
    official_coordinate_delta_source = coordinate_summary["source"]
    requires_current_official_recompute = coordinate_summary["requires_current_official_recompute"]
    max_official_coordinate_delta = max(official_coordinate_deltas) if official_coordinate_deltas else None
    official_coordinate_delta_violation_count = sum(
        1 for value in official_coordinate_deltas if abs(value) > args.max_official_coordinate_delta_m
    )
    probe_projection_issue_reason = ""
    probe_component_uref_issue_reason = compared_component_mismatch_reason
    normalization_missing_count = 0
    normalization_invalid_count = 0
    wind_missing_count = 0
    wind_invalid_count = 0
    uref_missing_count = 0
    uref_mismatch_count = 0
    nearest_distance_missing_count = 0
    tolerance_missing_or_disabled_count = 0
    probe_out_of_tolerance_count = 0
    for row in valid_probe_rows:
        normalized = as_bool(row_value(row, "normalization_valid", "NormalizationValid"))
        if normalized is None:
            normalization_missing_count += 1
        elif normalized is not True:
            normalization_invalid_count += 1
        wind_valid = as_bool(row_value(row, "wind_direction_valid", "WindDirectionValid"))
        if wind_valid is None:
            wind_missing_count += 1
        elif wind_valid is not True:
            wind_invalid_count += 1
        row_uref = as_float(row_value(row, "u_ref", "Uref", "U_ref"))
        if row_uref is None:
            uref_missing_count += 1
        elif args.u_ref is not None and abs(row_uref - args.u_ref) > args.u_ref_tolerance:
            uref_mismatch_count += 1
        if as_float(row_value(row, "nearest_distance", "NearestDistance")) is None:
            nearest_distance_missing_count += 1
        tolerance = as_float(row_value(row, "tolerance", "Tolerance"))
        if tolerance is None or tolerance <= 0.0:
            tolerance_missing_or_disabled_count += 1
        if as_bool(row_value(row, "out_of_tolerance", "OutOfTolerance")) is True:
            probe_out_of_tolerance_count += 1
    if valid_probe_rows:
        if missing_official_coordinate_delta_count:
            reasons.append("probe_official_coordinate_delta_missing")
            reasons.append(
                count_reason("probe_official_coordinate_delta_missing_count", missing_official_coordinate_delta_count)
            )
        if requires_current_official_recompute and official_coordinate_recomputed_count != len(valid_probe_rows):
            reasons.append("probe_official_coordinate_delta_current_official_recompute_incomplete")
            reasons.append(
                count_reason(
                    "probe_official_coordinate_delta_recomputed_count",
                    official_coordinate_recomputed_count,
                )
            )
        if official_coordinate_delta_violation_count:
            reasons.append("probe_official_coordinate_delta_exceeds_threshold")
            reasons.append(
                count_reason(
                    "probe_official_coordinate_delta_violation_count",
                    official_coordinate_delta_violation_count,
                )
            )
        if normalization_missing_count:
            reasons.append("probe_normalization_valid_missing")
            reasons.append(count_reason("probe_normalization_valid_missing_count", normalization_missing_count))
        if normalization_invalid_count:
            reasons.append("probe_normalization_invalid")
            reasons.append(count_reason("probe_normalization_invalid_count", normalization_invalid_count))
        if wind_missing_count:
            reasons.append("probe_wind_direction_valid_missing")
            reasons.append(count_reason("probe_wind_direction_valid_missing_count", wind_missing_count))
        if wind_invalid_count:
            reasons.append("probe_wind_direction_invalid")
            reasons.append(count_reason("probe_wind_direction_invalid_count", wind_invalid_count))
        if uref_missing_count:
            reasons.append("probe_uref_missing")
            reasons.append(count_reason("probe_uref_missing_count", uref_missing_count))
        if uref_mismatch_count:
            reasons.append("probe_uref_mismatch")
            uref_reason = count_reason("probe_uref_mismatch_count", uref_mismatch_count)
            reasons.append(uref_reason)
            probe_component_uref_issue_reason = ";".join(
                reason for reason in [probe_component_uref_issue_reason, uref_reason] if reason
            )
        if nearest_distance_missing_count:
            reasons.append("probe_nearest_distance_missing")
            reasons.append(count_reason("probe_nearest_distance_missing_count", nearest_distance_missing_count))
        if tolerance_missing_or_disabled_count:
            reasons.append("probe_tolerance_missing_or_disabled")
            tolerance_reason = count_reason("probe_tolerance_missing_or_disabled_count", tolerance_missing_or_disabled_count)
            reasons.append(tolerance_reason)
            probe_projection_issue_reason = ";".join(
                reason for reason in [probe_projection_issue_reason, tolerance_reason] if reason
            )
        if probe_out_of_tolerance_count:
            reasons.append("probe_out_of_tolerance")
            out_of_tolerance_reason = count_reason("probe_out_of_tolerance_count", probe_out_of_tolerance_count)
            reasons.append(out_of_tolerance_reason)
            probe_projection_issue_reason = ";".join(
                reason for reason in [probe_projection_issue_reason, out_of_tolerance_reason] if reason
            )
    probe_source_steps_values = probe_unique_values(
        probe_rows,
        "vtk_source_time_steps",
        "VtkSourceTimeSteps",
        "source_time_steps",
        "SourceTimeSteps",
    )
    probe_source_hash_values = probe_unique_values(
        probe_rows,
        "vtk_source_sha256",
        "VtkSourceSha256",
        "source_vtk_sha256",
        "SourceVtkSha256",
    )
    probe_source_step_span_values = probe_unique_int_values(
        probe_rows,
        "vtk_source_step_span",
        "VtkSourceStepSpan",
        "source_step_span",
        "SourceStepSpan",
    )
    probe_minimum_step_span_values = probe_unique_int_values(
        probe_rows,
        "minimum_validation_average_step_span",
        "MinimumValidationAverageStepSpan",
        "vtk_minimum_validation_average_step_span",
        "VtkMinimumValidationAverageStepSpan",
    )
    probe_source_steps = parse_int_list(probe_source_steps_values[0]) if len(probe_source_steps_values) == 1 else []
    probe_source_hashes = parse_hash_list(probe_source_hash_values[0]) if len(probe_source_hash_values) == 1 else []
    probe_source_step_span = probe_source_step_span_values[0] if len(probe_source_step_span_values) == 1 else None
    probe_minimum_step_span = probe_minimum_step_span_values[0] if len(probe_minimum_step_span_values) == 1 else None
    probe_source_steps_match = bool(runtime_steps) and probe_source_steps == runtime_steps
    probe_source_hashes_match = bool(runtime_hashes) and bool(probe_source_hashes) and probe_source_hashes == runtime_hashes
    probe_source_step_hash_pairs_match = (
        bool(runtime_steps)
        and bool(runtime_hashes)
        and probe_source_steps == runtime_steps
        and probe_source_hashes == runtime_hashes
        and len(probe_source_steps) == len(probe_source_hashes)
    )
    probe_source_steps_increasing = source_steps_strictly_increasing(probe_source_steps)
    probe_source_steps_uniform = source_steps_uniformly_spaced(probe_source_steps)
    probe_source_step_span_match = (
        runtime_step_span is not None
        and probe_source_step_span is not None
        and probe_source_step_span == runtime_step_span
    )
    if probe_rows:
        if len(probe_source_steps_values) != 1:
            reasons.append("probe_source_time_steps_inconsistent_or_missing")
        elif not probe_source_steps_match:
            reasons.append("probe_source_time_steps_mismatch")
        if not probe_source_steps_increasing:
            reasons.append("probe_source_steps_not_strictly_increasing")
        if not probe_source_steps_uniform:
            reasons.append("probe_source_step_spacing_not_uniform")
        if len(probe_source_hash_values) != 1:
            reasons.append("probe_source_vtk_hashes_inconsistent_or_missing")
        elif not probe_source_hashes_match:
            reasons.append("probe_source_vtk_hashes_mismatch")
        if len(probe_source_steps_values) == 1 and len(probe_source_hash_values) == 1:
            if not probe_source_step_hash_pairs_match:
                reasons.append("probe_source_step_hash_pairs_mismatch")
        if len(probe_source_step_span_values) != 1:
            reasons.append("probe_source_step_span_inconsistent_or_missing")
        else:
            if probe_source_step_span < args.min_avg_step_span:
                reasons.append("probe_source_step_span_too_short")
            if not probe_source_step_span_match:
                reasons.append("probe_source_step_span_mismatch")
        if len(probe_minimum_step_span_values) != 1:
            reasons.append("probe_minimum_step_span_inconsistent_or_missing")
        elif probe_minimum_step_span != args.min_avg_step_span:
            reasons.append("probe_minimum_step_span_mismatch")

    component_gate = str(component_sensitivity_audit.get("component_normalization_gate") or "").strip().lower()
    component_sensitivity_gate = str(component_sensitivity_audit.get("component_sensitivity_gate") or "").strip().lower()
    normalization_scale_gate = str(component_sensitivity_audit.get("normalization_scale_gate") or "").strip().lower()
    streamwise_sign_gate = str(component_sensitivity_audit.get("streamwise_sign_gate") or "").strip().lower()
    component_source_window_gate = str(component_sensitivity_audit.get("component_source_window_gate") or "").strip().lower()
    component_sensitivity_gate_reasons_csv = ";".join(
        str(reason)
        for reason in component_sensitivity_audit.get("component_sensitivity_gate_reasons", [])
        if str(reason).strip()
    )
    normalization_scale_gate_reasons_csv = ";".join(
        str(reason)
        for reason in component_sensitivity_audit.get("normalization_scale_gate_reasons", [])
        if str(reason).strip()
    )
    streamwise_sign_gate_reasons_csv = ";".join(
        str(reason)
        for reason in component_sensitivity_audit.get("streamwise_sign_gate_reasons", [])
        if str(reason).strip()
    )
    component_source_steps = parse_int_list(component_sensitivity_audit.get("component_source_time_steps"))
    component_source_hashes = parse_hash_list(component_sensitivity_audit.get("component_source_sha256"))
    component_source_steps_match_runtime = bool(runtime_steps) and component_source_steps == runtime_steps
    component_source_hashes_match_runtime = (
        bool(runtime_hashes)
        and bool(component_source_hashes)
        and component_source_hashes == runtime_hashes
    )
    component_source_step_hash_pairs_match_runtime = (
        bool(runtime_steps)
        and bool(runtime_hashes)
        and component_source_steps == runtime_steps
        and component_source_hashes == runtime_hashes
        and len(component_source_steps) == len(component_source_hashes)
    )
    component_source_steps_increasing = source_steps_strictly_increasing(component_source_steps)
    component_source_steps_uniform = source_steps_uniformly_spaced(component_source_steps)
    if not component_sensitivity_audit:
        reasons.append("component_sensitivity_audit_missing")
    reasons.extend(component_hash_traceability["reasons"])
    if component_gate != "pass":
        reasons.append("component_normalization_gate_not_pass")
    if component_sensitivity_gate != "pass":
        reasons.append("component_sensitivity_gate_not_pass")
    if normalization_scale_gate != "pass":
        reasons.append("normalization_scale_gate_not_pass")
    if streamwise_sign_gate != "pass":
        reasons.append("streamwise_sign_gate_not_pass")
    if component_source_window_gate != "pass":
        reasons.append("component_source_window_gate_not_pass")
    if not component_source_steps_match_runtime:
        reasons.append("component_source_time_steps_mismatch_runtime")
    if not component_source_hashes_match_runtime:
        reasons.append("component_source_vtk_hashes_mismatch_runtime")
    if not component_source_step_hash_pairs_match_runtime:
        reasons.append("component_source_step_hash_pairs_mismatch_runtime")

    native_probe_component_equivalence_reasons: List[str] = []
    if not probe_rows:
        native_probe_component_equivalence_reasons.append("probe_audit_missing_or_empty")
    if probe_rows and not valid_probe_rows:
        native_probe_component_equivalence_reasons.append("probe_audit_has_no_valid_rows")
    if failed_probe_rows:
        native_probe_component_equivalence_reasons.append(count_reason("probe_audit_failed_row_count", len(failed_probe_rows)))
    if expected_component and compared_components != {expected_component}:
        native_probe_component_equivalence_reasons.append(
            compared_component_mismatch_reason or "probe_compared_component_mismatch"
        )
    if valid_probe_rows and not probe_id_column:
        native_probe_component_equivalence_reasons.append("probe_id_column_missing")
    if valid_probe_rows and official_coordinate_error:
        native_probe_component_equivalence_reasons.append("probe_official_identity_error:" + official_coordinate_error)
    for key, value in [
        ("probe_missing_id_count", missing_probe_id_count),
        ("probe_duplicate_id_count", len(duplicate_probe_ids)),
        ("probe_unmatched_official_id_count", len(unmatched_probe_ids)),
        ("missing_official_probe_id_count", len(missing_official_probe_ids)),
        ("probe_missing_official_coordinate_delta_count", missing_official_coordinate_delta_count),
        ("probe_official_coordinate_delta_violation_count", official_coordinate_delta_violation_count),
        ("probe_normalization_valid_missing_count", normalization_missing_count),
        ("probe_normalization_invalid_count", normalization_invalid_count),
        ("probe_wind_direction_valid_missing_count", wind_missing_count),
        ("probe_wind_direction_invalid_count", wind_invalid_count),
        ("probe_uref_missing_count", uref_missing_count),
        ("probe_uref_mismatch_count", uref_mismatch_count),
        ("probe_nearest_distance_missing_count", nearest_distance_missing_count),
        ("probe_tolerance_missing_or_disabled_count", tolerance_missing_or_disabled_count),
        ("probe_out_of_tolerance_count", probe_out_of_tolerance_count),
    ]:
        if value:
            native_probe_component_equivalence_reasons.append(count_reason(key, value))
    if valid_probe_rows and requires_current_official_recompute and official_coordinate_recomputed_count != len(valid_probe_rows):
        native_probe_component_equivalence_reasons.append(
            count_reason("probe_official_coordinate_delta_recomputed_count", official_coordinate_recomputed_count)
        )
    if valid_probe_rows:
        if official_probe_coverage_ratio is None:
            native_probe_component_equivalence_reasons.append("official_probe_coverage_ratio_missing")
        elif abs(official_probe_coverage_ratio - 1.0) > 1.0e-12:
            native_probe_component_equivalence_reasons.append(
                f"official_probe_coverage_ratio_not_one:{official_probe_coverage_ratio}"
            )
    for key, value in [
        ("probe_source_time_steps_match_runtime", probe_source_steps_match),
        ("probe_source_steps_strictly_increasing", probe_source_steps_increasing),
        ("probe_source_step_spacing_uniform", probe_source_steps_uniform),
        ("probe_source_step_span_match_runtime", probe_source_step_span_match),
        ("probe_source_vtk_sha256_match_runtime", probe_source_hashes_match),
        ("probe_source_step_hash_pairs_match_runtime", probe_source_step_hash_pairs_match),
        ("component_source_time_steps_match_runtime", component_source_steps_match_runtime),
        ("component_source_steps_strictly_increasing", component_source_steps_increasing),
        ("component_source_step_spacing_uniform", component_source_steps_uniform),
        ("component_source_vtk_sha256_match_runtime", component_source_hashes_match_runtime),
        ("component_source_step_hash_pairs_match_runtime", component_source_step_hash_pairs_match_runtime),
        (
            "component_sensitivity_probe_audit_sha256_matches_current",
            component_hash_traceability["probe_audit_sha256_matches_current"],
        ),
        (
            "component_sensitivity_official_sha256_matches_current",
            component_hash_traceability["official_sha256_matches_current"],
        ),
    ]:
        if value is not True:
            native_probe_component_equivalence_reasons.append(
                f"{key}_not_true:{value if value is not None else 'missing'}"
            )
    for key, value in [
        ("probe_source_step_span", probe_source_step_span),
        ("probe_minimum_validation_average_step_span", probe_minimum_step_span),
        ("component_source_step_span", as_int(component_sensitivity_audit.get("component_source_step_span"))),
        ("component_minimum_source_step_span", as_int(component_sensitivity_audit.get("component_minimum_source_step_span"))),
    ]:
        if value is None:
            native_probe_component_equivalence_reasons.append(f"{key}_missing")
        elif value < args.min_avg_step_span:
            native_probe_component_equivalence_reasons.append(
                count_below_minimum_reason(key, value, args.min_avg_step_span) or f"{key}_below_minimum"
            )
    for key, value in [
        ("component_normalization_gate", component_gate),
        ("component_sensitivity_gate", component_sensitivity_gate),
        ("normalization_scale_gate", normalization_scale_gate),
        ("component_source_window_gate", component_source_window_gate),
        ("component_sensitivity_hash_traceability_gate", component_hash_traceability["gate"]),
    ]:
        if value != "pass":
            native_probe_component_equivalence_reasons.append(f"{key}_not_pass:{value or 'missing'}")
    for key, value in [
        ("component_source_time_steps", component_sensitivity_audit.get("component_source_time_steps")),
        ("component_source_sha256", component_sensitivity_audit.get("component_source_sha256")),
        ("probe_audit_sha256", probe_audit_sha),
        ("official_measurement_sha256", official_sha),
        ("component_sensitivity_probe_audit_sha256", component_hash_traceability["component_probe_audit_sha256"]),
        ("component_sensitivity_official_sha256", component_hash_traceability["component_official_sha256"]),
    ]:
        if not str(value or "").strip():
            native_probe_component_equivalence_reasons.append(f"{key}_missing")
    native_probe_component_equivalence_gate = (
        "pass" if not native_probe_component_equivalence_reasons else "fail"
    )
    probe_component_fidelity_class = classify_probe_component_fidelity(
        native_probe_component_equivalence_reasons
    )
    if native_probe_component_equivalence_gate != "pass":
        reasons.append("native_probe_component_equivalence_gate_not_pass")

    protocol_identity_gate = "pass" if not any(
        reason in reasons
        for reason in [
            "wind_vector_mismatch",
            "uref_mismatch",
            "uref_af_profile_mismatch",
            "metadata_uref_af_profile_mismatch",
            "af_csv_missing",
            "af_csv_hash_mismatch",
            "wind_profile_not_customtable",
            "metadata_manifest_time_steps_mismatch",
            "metadata_manifest_save_interval_mismatch",
        ]
    ) else "fail"

    native_diagnostic_priority = build_native_diagnostic_priority(reasons)
    native_top_priority = native_diagnostic_priority[0] if native_diagnostic_priority else {}
    native_precondition_closure = build_native_precondition_closure(reasons)
    native_rerun_prescription = build_native_rerun_prescription(
        native_diagnostic_priority,
        native_precondition_closure,
        args.min_avg_frames,
        args.min_avg_step_span,
        args.average_last_n,
    )

    result = {
        "generated_at_utc": utc_now(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path) if manifest_path else "",
        "metadata": str(metadata_path) if metadata_path else "",
        "runtime_audit": str(runtime_audit_path) if runtime_audit_path else "",
        "setup_cpp": str(setup_path) if setup_path else "",
        "defines_hpp": str(defines_path) if defines_path else "",
        "domain_origin": str(domain_origin_path) if domain_origin_path else "",
        "validation_protocol_audit": str(protocol_audit_path) if protocol_audit_path else "",
        "baseline_id": str(manifest.get("BaselineId") or "").strip(),
        "case": args.case,
        "software": args.software,
        "expected_wind_vector": args.wind_vector,
        "actual_wind_vector": actual_vector,
        "wind_vector_delta": wind_delta,
        "expected_uref_mps": args.u_ref,
        "actual_uref_mps": u_ref,
        "expected_zref_m": args.z_ref,
        "af_uref_at_zref_mps": u_ref_from_af,
        "uref_af_profile_delta_mps": (
            abs(args.u_ref - u_ref_from_af)
            if args.u_ref is not None and u_ref_from_af is not None
            else None
        ),
        "metadata_uref_af_profile_delta_mps": (
            abs(u_ref - u_ref_from_af)
            if u_ref is not None and u_ref_from_af is not None
            else None
        ),
        "expected_vtk_pattern": args.expected_vtk_pattern,
        "runtime_vtk_pattern": runtime_pattern,
        "average_last_n_required": args.average_last_n,
        "runtime_average_last_n": runtime_avg,
        "min_avg_frames": args.min_avg_frames,
        "min_avg_step_span": args.min_avg_step_span,
        "planned_frame_count_min": planned_frame_count_min,
        "planned_frame_count_shortfall_reason": planned_frame_shortfall_reason,
        "runtime_average_window_shortfall_reason": runtime_average_shortfall_reason,
        "planned_final_window_step_span": planned_span,
        "planned_average_step_span_shortfall_reason": planned_step_shortfall_reason,
        "runtime_source_step_span": runtime_step_span,
        "runtime_average_step_span_shortfall_reason": runtime_step_shortfall_reason,
        "runtime_reported_source_step_span": runtime_step_span_reported,
        "runtime_source_step_span_from_time_steps": runtime_step_span_from_steps,
        "runtime_source_step_span_matches_time_steps": (
            runtime_step_span_reported is not None
            and runtime_step_span_from_steps is not None
            and runtime_step_span_reported == runtime_step_span_from_steps
        ),
        "runtime_source_steps_strictly_increasing": runtime_steps_increasing,
        "runtime_source_step_spacing_uniform": runtime_steps_uniform,
        "runtime_reported_source_steps_strictly_increasing": runtime_reported_steps_increasing,
        "runtime_reported_source_step_spacing_uniform": runtime_reported_steps_uniform,
        "runtime_selected_last_window": runtime_selected_last_window,
        "runtime_source_frame_count": runtime_source_frame_count,
        "runtime_source_time_steps": runtime_steps,
        "runtime_source_vtk_sha256": runtime_hashes,
        "runtime_source_vtk_sha256_count": runtime_hash_count,
        "runtime_source_vtk_sha256_unique_count": runtime_hash_unique_count,
        "runtime_final_window_frame_count_gate": runtime_final_window_frame_count_gate["gate"],
        "runtime_final_window_frame_count_gate_reasons": runtime_final_window_frame_count_gate["reasons"],
        "runtime_final_window_frame_count_gate_reasons_csv": runtime_final_window_frame_count_gate["reasons_csv"],
        "runtime_reported_time_averaging_gate": runtime_reported_time_average_gate,
        "runtime_time_averaging_gate": time_gate,
        "runtime_final_window_stationarity_gate": stationarity_gate,
        "runtime_final_window_stationarity_gate_reasons": stationarity_reasons,
        "runtime_final_window_stationarity_gate_reasons_csv": ";".join(stationarity_reasons),
        "runtime_final_window_mean_speed_drift_ratio": runtime_audit.get("final_window_mean_speed_drift_ratio", ""),
        "runtime_max_final_window_mean_speed_drift_ratio": runtime_audit.get("max_final_window_mean_speed_drift_ratio", ""),
        "runtime_mean_speed_statistics_source": runtime_mean_speed_statistics_source,
        "runtime_mean_speed_statistics_cli_override": runtime_mean_speed_statistics_cli_override,
        "runtime_mean_speed_statistics_cli_override_fields_csv": runtime_mean_speed_statistics_cli_override_fields_csv,
        "runtime_requested_vtk_frame_gate": requested_frame_gate,
        "strict_native_run_gate": strict_native_run_gate,
        "strict_native_run_gate_reasons": strict_native_run_reasons,
        "strict_native_run_gate_reasons_csv": ";".join(strict_native_run_reasons),
        "native_preconditions_time_average_evidence_gate": time_average_gate,
        "time_averaging_fidelity_class": time_averaging_fidelity_class,
        "native_preconditions_time_average_evidence_gate_reasons": time_average_evidence_reasons,
        "native_preconditions_time_average_evidence_gate_reasons_csv": ";".join(time_average_evidence_reasons),
        "native_preconditions_lbm_stability_gate": lbm_stability_gate,
        "native_preconditions_lbm_stability_gate_reasons": lbm_stability_reasons,
        "native_preconditions_lbm_stability_gate_reasons_csv": ";".join(lbm_stability_reasons),
        "native_preconditions_target_max_profile_velocity_lbm": target_velocity_lbm,
        "native_preconditions_estimated_max_profile_mach": estimated_mach,
        "native_preconditions_max_estimated_mach_threshold": args.max_estimated_mach,
        "native_preconditions_lbm_tau": lbm_tau,
        "native_preconditions_min_lbm_tau_threshold": args.min_lbm_tau,
        "native_preconditions_max_lbm_tau_threshold": args.max_lbm_tau,
        "native_preconditions_lbm_nu": lbm_nu,
        "native_preconditions_physical_viscosity_m2s": physical_viscosity,
        "native_preconditions_estimated_reynolds_number": estimated_reynolds,
        "native_preconditions_velocity_set": velocity_set,
        "native_preconditions_les_model": les_model,
        "native_preconditions_solver_stability_warnings": solver_warnings,
        "native_preconditions_runtime_lbm_stability_gate": lbm_runtime_gate,
        "native_preconditions_protocol_lbm_stability_scaling_status": lbm_protocol_status,
        "native_runner_gate": native_runner_gate,
        "native_runner_gate_reasons": native_runner_reasons,
        "native_runner_gate_reasons_csv": ";".join(native_runner_reasons),
        "actual_vtk_output_gate": actual_vtk_output_gate,
        "actual_vtk_output_gate_reasons": actual_vtk_output_reasons,
        "actual_vtk_output_gate_reasons_csv": ";".join(actual_vtk_output_reasons),
        "actual_vtk_output_required": actual_vtk_output_required,
        "actual_vtk_frame_count": actual_vtk_frame_count,
        "actual_vtk_expected_frame_count": actual_vtk_expected_frame_count,
        "actual_vtk_minimum_frame_count": actual_vtk_minimum_frame_count,
        "planned_synthetic_inlet_sampling_gate": planned_synthetic_gate,
        "planned_synthetic_inlet_sampling_gate_reasons": planned_synthetic_reasons,
        "planned_synthetic_inlet_sampling_gate_reasons_csv": ";".join(planned_synthetic_reasons),
        "planned_synthetic_inlet_sampling_active": planned_synthetic_active,
        "planned_synthetic_inlet_sampling_requested": planned_synthetic_requested,
        "planned_synthetic_inlet_sampling_injected": planned_synthetic_injected,
        "planned_synthetic_inlet_update_interval": planned_synthetic_update_interval,
        "planned_synthetic_inlet_final_window_step_span": planned_synthetic_final_window_span,
        "planned_synthetic_inlet_refresh_count": planned_synthetic_refresh_count,
        "planned_synthetic_inlet_metadata_expected_refresh_count": planned_synthetic_metadata_expected_refresh_count,
        "planned_synthetic_inlet_minimum_refresh_count": planned_synthetic_minimum_refresh_count,
        "inlet_source_audit": str(inlet_source_audit_path) if inlet_source_audit_path else "",
        "inlet_profile_audit": str(inlet_profile_audit_path) if inlet_profile_audit_path else "",
        "inlet_correlation_audit": str(inlet_correlation_audit_path) if inlet_correlation_audit_path else "",
        "boundary_source_audit": str(boundary_source_audit_path) if boundary_source_audit_path else "",
        "boundary_protocol_audit": str(boundary_protocol_audit_path) if boundary_protocol_audit_path else "",
        "boundary_runtime_audit": str(boundary_runtime_audit_path) if boundary_runtime_audit_path else "",
        "probe_audit": str(probe_audit_path) if probe_audit_path else "",
        "component_sensitivity_audit": str(component_sensitivity_audit_path) if component_sensitivity_audit_path else "",
        "official_measurement_csv": str(official_path) if official_path else "",
        "probe_audit_sha256": probe_audit_sha,
        "official_measurement_sha256": official_sha,
        "component_sensitivity_probe_audit_sha256": component_hash_traceability["component_probe_audit_sha256"],
        "component_sensitivity_official_sha256": component_hash_traceability["component_official_sha256"],
        "component_sensitivity_probe_audit_sha256_matches_current": component_hash_traceability[
            "probe_audit_sha256_matches_current"
        ],
        "component_sensitivity_official_sha256_matches_current": component_hash_traceability[
            "official_sha256_matches_current"
        ],
        "component_sensitivity_hash_traceability_gate": component_hash_traceability["gate"],
        "component_sensitivity_hash_traceability_gate_reasons": component_hash_traceability["reasons"],
        "component_sensitivity_hash_traceability_gate_reasons_csv": component_hash_traceability["reasons_csv"],
        "component_normalization_gate": component_gate,
        "component_sensitivity_gate": component_sensitivity_gate,
        "component_sensitivity_gate_reasons": component_sensitivity_audit.get("component_sensitivity_gate_reasons", []),
        "component_sensitivity_gate_reasons_csv": component_sensitivity_gate_reasons_csv,
        "normalization_scale_gate": normalization_scale_gate,
        "normalization_scale_gate_reasons": component_sensitivity_audit.get("normalization_scale_gate_reasons", []),
        "normalization_scale_gate_reasons_csv": normalization_scale_gate_reasons_csv,
        "streamwise_sign_gate": streamwise_sign_gate,
        "streamwise_sign_gate_reasons": component_sensitivity_audit.get("streamwise_sign_gate_reasons", []),
        "streamwise_sign_gate_reasons_csv": streamwise_sign_gate_reasons_csv,
        "streamwise_negative_fraction": component_sensitivity_audit.get("streamwise_negative_fraction"),
        "streamwise_mean_ratio": component_sensitivity_audit.get("streamwise_mean_ratio"),
        "streamwise_sign_valid_n": component_sensitivity_audit.get("streamwise_sign_valid_n"),
        "streamwise_negative_count": component_sensitivity_audit.get("streamwise_negative_count"),
        "component_selected_component": component_sensitivity_audit.get("selected_component"),
        "component_selected_component_source": component_sensitivity_audit.get("selected_component_source"),
        "component_best_component_by_rmse": component_sensitivity_audit.get("best_component_by_rmse"),
        "component_official_probe_coverage_ratio": component_sensitivity_audit.get("official_probe_coverage_ratio"),
        "component_selected_component_rmse": component_sensitivity_audit.get("selected_component_rmse"),
        "component_selected_component_bias": component_sensitivity_audit.get("selected_component_bias"),
        "component_selected_component_scaled_bias": component_sensitivity_audit.get("selected_component_scaled_bias"),
        "component_selected_component_bias_abs_reduction_ratio": component_sensitivity_audit.get(
            "selected_component_bias_abs_reduction_ratio"
        ),
        "component_selected_component_mean_sim": component_sensitivity_audit.get("selected_component_mean_sim"),
        "component_selected_component_mean_exp": component_sensitivity_audit.get("selected_component_mean_exp"),
        "component_selected_component_mean_sim_to_exp_ratio": component_sensitivity_audit.get(
            "selected_component_mean_sim_to_exp_ratio"
        ),
        "component_best_component_rmse": component_sensitivity_audit.get("best_component_rmse"),
        "component_rmse_improvement_ratio": component_sensitivity_audit.get("component_rmse_improvement_ratio"),
        "component_normalization_best_fit_scale": component_sensitivity_audit.get("selected_best_fit_scale_to_exp"),
        "component_normalization_scaled_improvement_ratio": component_sensitivity_audit.get(
            "selected_scaled_improvement_ratio"
        ),
        "native_inlet_equivalence_gate": native_inlet_equivalence_gate,
        "native_inlet_equivalence_gate_reasons": native_inlet_equivalence_reasons,
        "native_inlet_equivalence_gate_reasons_csv": ";".join(native_inlet_equivalence_reasons),
        "native_probe_component_equivalence_gate": native_probe_component_equivalence_gate,
        "probe_component_fidelity_class": probe_component_fidelity_class,
        "native_probe_component_equivalence_gate_reasons": native_probe_component_equivalence_reasons,
        "native_probe_component_equivalence_gate_reasons_csv": ";".join(
            native_probe_component_equivalence_reasons
        ),
        "inlet_source_gate": inlet_source_gate,
        "paper_grade_inlet_source_gate": paper_inlet_source_gate,
        "inlet_source_distribution_consistent": inlet_distribution_consistent,
        "inlet_source_velocity_field_only": inlet_velocity_only,
        "inlet_source_method_class": inlet_source_method_class,
        "inlet_source_turbulent_inflow_fidelity_class": inlet_source_fidelity_class,
        "inlet_source_has_correlated_velocity_field_only": inlet_has_correlated_velocity_only,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": inlet_has_uncorrelated_rms_velocity_only,
        "inlet_source_requires_distribution_reconstruction": inlet_requires_distribution_reconstruction,
        "inlet_synthetic_correlation_model": inlet_correlation_model,
        "inlet_source_distribution_route": inlet_distribution_route,
        "inlet_source_distribution_route_gate": inlet_distribution_route_gate,
        "inlet_source_has_equilibrium_boundaries_define": inlet_has_equilibrium_boundaries_define,
        "inlet_source_has_type_e_equilibrium_boundary_route": inlet_has_type_e_equilibrium_boundary_route,
        "inlet_source_has_reynolds_stress_tensor_metadata_claim": inlet_has_reynolds_metadata_claim,
        "inlet_source_has_reynolds_stress_diagonal_source_evidence": inlet_has_reynolds_diagonal_source,
        "inlet_source_has_reynolds_stress_offdiagonal_source_evidence": inlet_has_reynolds_offdiagonal_source,
        "inlet_source_has_reynolds_stress_full_tensor_source_evidence": inlet_has_reynolds_full_tensor_source,
        "inlet_source_has_uncorrelated_random_inlet": inlet_has_uncorrelated_random,
        "inlet_source_uncorrelated_random_patterns": inlet_uncorrelated_random_patterns,
        "inlet_source_uncorrelated_random_patterns_csv": ";".join(inlet_uncorrelated_random_patterns),
        "inlet_source_recommended_next_action": inlet_recommended_next_action,
        "inlet_source_stg_evidence_required": inlet_stg_evidence_required,
        "inlet_source_has_three_component_velocity_write": inlet_has_three_component_velocity_write,
        "inlet_source_has_three_component_fluctuation_evidence": inlet_has_three_component_fluctuation_evidence,
        "inlet_source_has_k_driven_three_component_stg": inlet_has_k_driven_three_component_stg,
        "inlet_source_has_component_phase_decorrelation": inlet_has_component_phase_decorrelation,
        "inlet_source_has_temporal_filter_state": inlet_has_temporal_filter_state,
        "inlet_source_has_mean_preserving_inlet_correction": inlet_has_mean_preserving_correction,
        "inlet_source_has_layerwise_mean_preserving_inlet_correction": inlet_has_layerwise_mean_preserving_correction,
        "inlet_source_has_streamwise_clipping_control": inlet_has_streamwise_clipping_control,
        "inlet_source_streamwise_min_fraction": inlet_streamwise_min_fraction,
        "inlet_source_streamwise_clipping_enabled": inlet_streamwise_clipping_enabled,
        "inlet_source_has_legacy_hardcoded_streamwise_clipping": inlet_has_legacy_hardcoded_streamwise_clipping,
        "inlet_source_gate_reasons": inlet_source_reasons,
        "inlet_source_gate_reasons_csv": ";".join(inlet_source_reasons),
        "paper_grade_inlet_source_gate_reasons": paper_inlet_source_reasons,
        "paper_grade_inlet_source_gate_reasons_csv": ";".join(paper_inlet_source_reasons),
        **inlet_source_hash_check,
        "inlet_profile_gate": inlet_profile_gate,
        "inlet_u_profile_gate": inlet_u_profile_gate,
        "inlet_k_profile_gate": inlet_k_profile_gate,
        "inlet_profile_af_csv_sha256": inlet_profile_af_sha,
        "inlet_profile_af_csv_sha256_matches_expected": inlet_profile_af_hash_matches,
        **inlet_profile_span_check,
        **inlet_profile_window_check,
        "inlet_correlation_gate": inlet_correlation_gate,
        "inlet_k_variance_gate": inlet_k_variance_gate,
        "inlet_streamwise_variance_target_from_k": inlet_k_variance_target,
        "inlet_streamwise_variance_to_k_ratio": inlet_k_variance_ratio,
        "inlet_tke_gate": inlet_tke_gate,
        "inlet_tke_target_from_af_k": inlet_tke_target,
        "inlet_tke_to_k_ratio": inlet_tke_ratio,
        "inlet_mean_turbulent_kinetic_energy_from_components": inlet_mean_tke,
        **inlet_correlation_span_check,
        **inlet_correlation_window_check,
        "boundary_source_gate": boundary_source_gate,
        "paper_grade_boundary_source_gate": paper_boundary_source_gate,
        "boundary_source_method_class": boundary_source_method_class,
        "boundary_source_fidelity_class": boundary_source_fidelity_class,
        "boundary_source_has_complete_wind_tunnel_evidence": boundary_source_has_complete_wind_tunnel_evidence,
        "boundary_source_has_empty_advanced_method_stub_only": boundary_source_has_empty_advanced_method_stub_only,
        "boundary_source_advanced_code_evidence": boundary_source_advanced_code_evidence,
        "boundary_source_wind_tunnel_equivalent": boundary_source_equivalent,
        "boundary_source_simplified": boundary_source_simplified,
        "boundary_source_has_paper_grade_outlet_source": boundary_source_has_paper_grade_outlet,
        "boundary_source_has_paper_grade_side_top_source": boundary_source_has_paper_grade_side_top,
        "boundary_source_has_paper_grade_rough_wall_source": boundary_source_has_paper_grade_rough_wall,
        "boundary_source_has_paper_grade_development_source": boundary_source_has_paper_grade_development,
        "boundary_source_has_non_reflecting_outlet_method": boundary_source_has_non_reflecting_outlet_method,
        "boundary_source_has_non_reflecting_outlet_state_evidence": boundary_source_has_non_reflecting_outlet_state,
        "boundary_source_has_periodic_side_top_method": boundary_source_has_periodic_side_top_method,
        "boundary_source_has_periodic_pair_mapping_evidence": boundary_source_has_periodic_pair_mapping,
        "boundary_source_has_rough_wall_function_method": boundary_source_has_rough_wall_function_method,
        "boundary_source_has_rough_wall_parameter_evidence": boundary_source_has_rough_wall_parameter,
        "boundary_source_has_rough_wall_action_evidence": boundary_source_has_rough_wall_action,
        "boundary_source_has_precursor_or_recycling_boundary_method": boundary_source_has_precursor_recycling_method,
        "boundary_source_has_precursor_or_recycling_boundary_field_evidence": boundary_source_has_precursor_recycling_field,
        "boundary_source_missing_paper_grade_source_evidence": boundary_source_missing_paper_evidence,
        "boundary_source_missing_paper_grade_source_evidence_csv": ";".join(boundary_source_missing_paper_evidence),
        **boundary_source_hash_check,
        "native_boundary_equivalence_gate": native_boundary_equivalence_gate,
        "native_boundary_equivalence_gate_reasons": native_boundary_equivalence_reasons,
        "native_boundary_equivalence_gate_reasons_csv": ";".join(native_boundary_equivalence_reasons),
        "boundary_protocol_gate": boundary_protocol_gate,
        "boundary_evidence_gate": boundary_evidence_gate,
        "boundary_run_identity_gate": boundary_run_identity_gate,
        "boundary_run_identity_gate_reasons": boundary_run_identity_reasons,
        "boundary_run_identity_gate_reasons_csv": ";".join(boundary_run_identity_reasons),
        "boundary_evidence_metadata_sha256_matches_current": boundary_evidence_metadata_hash_matches,
        "boundary_evidence_aij_case": str(boundary_protocol_audit.get("evidence_aij_case") or ""),
        "boundary_evidence_wind_direction": str(boundary_protocol_audit.get("evidence_wind_direction") or ""),
        "boundary_evidence_files_all_hashed": boundary_evidence_hashed,
        "boundary_equivalence_supported": boundary_equivalence_supported,
        "boundary_evidence_class_supported": boundary_evidence_class_supported,
        "boundary_condition_fields_supported": boundary_condition_fields_supported,
        "boundary_clearance_numeric_gate": boundary_clearance_numeric_gate,
        "boundary_blockage_gate": boundary_blockage_gate,
        "boundary_protocol_gate_reasons": boundary_protocol_reasons,
        "boundary_protocol_gate_reasons_csv": ";".join(boundary_protocol_reasons),
        "boundary_missing_evidence_fields": boundary_missing_evidence_fields,
        "boundary_missing_evidence_fields_csv": ";".join(boundary_missing_evidence_fields),
        "boundary_unsupported_condition_fields": boundary_unsupported_condition_fields,
        "boundary_unsupported_condition_fields_csv": ";".join(boundary_unsupported_condition_fields),
        "boundary_condition_support_reasons": boundary_condition_support_reasons,
        "boundary_condition_support_reasons_csv": ";".join(boundary_condition_support_reasons),
        "boundary_clearance_numeric_gate_reasons": boundary_clearance_reasons,
        "boundary_clearance_numeric_gate_reasons_csv": ";".join(boundary_clearance_reasons),
        "boundary_evidence_files_missing": boundary_evidence_files_missing,
        "boundary_evidence_files_missing_csv": ";".join(boundary_evidence_files_missing),
        "boundary_evidence_files_empty": boundary_evidence_files_empty,
        "boundary_evidence_files_empty_csv": ";".join(boundary_evidence_files_empty),
        "boundary_evidence_files_unreadable": boundary_evidence_files_unreadable,
        "boundary_evidence_files_unreadable_csv": ";".join(boundary_evidence_files_unreadable),
        "boundary_required_support_fields_missing_or_false": boundary_required_support_fields_missing_or_false,
        "boundary_required_support_fields_missing_or_false_csv": ";".join(boundary_required_support_fields_missing_or_false),
        "boundary_runtime_gate": boundary_runtime_gate,
        "boundary_runtime_gate_reasons": boundary_runtime_reasons,
        "boundary_runtime_gate_reasons_csv": ";".join(boundary_runtime_reasons),
        "boundary_runtime_traceability_gate": boundary_runtime_traceability_gate,
        "boundary_runtime_traceability_gate_reasons": boundary_runtime_traceability_reasons,
        "boundary_runtime_traceability_gate_reasons_csv": ";".join(boundary_runtime_traceability_reasons),
        "boundary_runtime_profile_preservation_gate": boundary_runtime_profile_gate,
        "boundary_runtime_inlet_gate": boundary_runtime_inlet_gate,
        "boundary_runtime_side_top_gate": boundary_runtime_side_top_gate,
        "boundary_runtime_side_top_normal_leakage_gate": boundary_runtime_side_top_normal_gate,
        "boundary_runtime_outlet_gate": boundary_runtime_outlet_gate,
        "boundary_runtime_max_u_mae_ratio": boundary_runtime_audit.get("max_boundary_u_mae_ratio", ""),
        "boundary_runtime_inlet_u_mae_ratio": boundary_runtime_audit.get("inlet_u_mae_ratio", ""),
        "boundary_runtime_outlet_u_mae_ratio": boundary_runtime_audit.get("outlet_u_mae_ratio", ""),
        "boundary_runtime_side_top_max_u_mae_ratio": boundary_runtime_audit.get("side_top_max_u_mae_ratio", ""),
        "boundary_runtime_max_side_top_normal_velocity_ratio": boundary_runtime_audit.get("max_side_top_normal_velocity_ratio", ""),
        "boundary_runtime_max_side_top_normal_abs_mps": boundary_runtime_audit.get("max_side_top_normal_abs_mps", ""),
        "boundary_runtime_max_negative_streamwise_fraction": boundary_runtime_audit.get("max_boundary_negative_streamwise_fraction", ""),
        "boundary_runtime_source_time_steps": boundary_runtime_steps,
        "boundary_runtime_source_time_steps_csv": ";".join(str(step) for step in boundary_runtime_steps),
        "boundary_runtime_source_step_span": boundary_runtime_source_step_span,
        "boundary_runtime_reported_source_step_span": boundary_runtime_reported_source_step_span,
        "boundary_runtime_source_time_steps_match_runtime": boundary_runtime_steps_match_runtime,
        "boundary_runtime_source_steps_strictly_increasing": boundary_runtime_steps_increasing,
        "boundary_runtime_source_step_spacing_uniform": boundary_runtime_steps_uniform,
        "boundary_runtime_selected_last_window": boundary_runtime_selected_last_window,
        "boundary_runtime_source_vtk_sha256": boundary_runtime_hashes,
        "boundary_runtime_source_vtk_sha256_csv": ";".join(boundary_runtime_hashes),
        "boundary_runtime_source_vtk_sha256_match_runtime": boundary_runtime_hashes_match_runtime,
        "boundary_runtime_source_step_hash_pairs_match_runtime": boundary_runtime_step_hash_pairs_match_runtime,
        "boundary_runtime_source_vtk_sha256_count": boundary_runtime_hash_count,
        "boundary_runtime_source_vtk_sha256_unique_count": boundary_runtime_hash_unique_count,
        "boundary_runtime_frame_count": boundary_runtime_frame_count,
        "probe_audit_row_count": len(probe_rows),
        "probe_audit_valid_row_count": len(valid_probe_rows),
        "probe_audit_failed_row_count": len(failed_probe_rows),
        "probe_audit_compared_components": sorted(compared_components),
        "probe_audit_compared_components_csv": compared_component_values_csv,
        "expected_compared_component": expected_component,
        "probe_compared_component_mismatch_reason": compared_component_mismatch_reason,
        "probe_id_column": probe_id_column,
        "probe_missing_id_count": missing_probe_id_count,
        "probe_duplicate_id_count": len(duplicate_probe_ids),
        "probe_duplicate_ids_csv": ";".join(duplicate_probe_ids_sorted),
        "probe_unique_id_count": len(seen_probe_ids),
        "official_probe_id_count": len(official_probe_ids),
        "official_probe_set_gate": official_probe_set_gate,
        "official_probe_set_gate_reasons": official_probe_set_reasons,
        "probe_official_height_gate": probe_official_height_gate,
        "probe_official_height_gate_reasons": probe_official_height_reasons,
        "probe_official_height_gate_reasons_csv": ";".join(probe_official_height_reasons),
        "official_probe_set_row_count": official_probe_set_row_count,
        "official_expected_row_count": official_expected_row_count,
        "official_probe_ids_unique": official_probe_ids_unique,
        "official_missing_probe_id_count": official_missing_probe_id_count,
        "official_duplicate_probe_ids": official_duplicate_probe_ids,
        "official_expected_z_m": official_expected_z,
        "official_expected_z_tolerance_m": official_expected_z_tolerance,
        "official_z_match_count": official_z_match_count,
        "official_z_mismatch_count": official_z_mismatch_count,
        "matched_official_probe_id_count": len(official_probe_ids & set(probe_ids)),
        "missing_official_probe_id_count": len(missing_official_probe_ids),
        "missing_official_probe_ids_csv": ";".join(missing_official_probe_ids),
        "unmatched_probe_id_count": len(unmatched_probe_ids),
        "unmatched_probe_ids_csv": ";".join(unmatched_probe_ids),
        "official_probe_coverage_ratio": official_probe_coverage_ratio,
        "probe_official_coverage_reason": official_probe_coverage_reason,
        "probe_official_coordinate_delta_count": len(official_coordinate_deltas),
        "probe_official_coordinate_delta_source": official_coordinate_delta_source,
        "probe_official_coordinate_delta_recomputed_count": official_coordinate_recomputed_count,
        "probe_official_coordinate_delta_recompute_error": official_coordinate_error,
        "probe_missing_official_coordinate_delta_count": missing_official_coordinate_delta_count,
        "probe_max_official_coordinate_delta_m": max_official_coordinate_delta,
        "probe_official_coordinate_delta_violation_count": official_coordinate_delta_violation_count,
        "probe_max_official_coordinate_delta_threshold_m": args.max_official_coordinate_delta_m,
        "probe_normalization_missing_count": normalization_missing_count,
        "probe_normalization_invalid_count": normalization_invalid_count,
        "probe_wind_direction_missing_count": wind_missing_count,
        "probe_wind_direction_invalid_count": wind_invalid_count,
        "probe_uref_missing_count": uref_missing_count,
        "probe_uref_mismatch_count": uref_mismatch_count,
        "probe_nearest_distance_missing_count": nearest_distance_missing_count,
        "probe_tolerance_missing_or_disabled_count": tolerance_missing_or_disabled_count,
        "probe_out_of_tolerance_count": probe_out_of_tolerance_count,
        "probe_projection_issue_reason": probe_projection_issue_reason,
        "probe_component_uref_issue_reason": probe_component_uref_issue_reason,
        "probe_source_time_steps": probe_source_steps,
        "probe_source_time_steps_match_runtime": probe_source_steps_match,
        "probe_source_steps_strictly_increasing": probe_source_steps_increasing,
        "probe_source_step_spacing_uniform": probe_source_steps_uniform,
        "probe_source_step_span": probe_source_step_span,
        "probe_source_step_span_match_runtime": probe_source_step_span_match,
        "probe_minimum_validation_average_step_span": probe_minimum_step_span,
        "probe_source_vtk_sha256": probe_source_hashes,
        "probe_source_vtk_sha256_match_runtime": probe_source_hashes_match,
        "probe_source_step_hash_pairs_match_runtime": probe_source_step_hash_pairs_match,
        "component_normalization_gate": component_gate,
        "component_sensitivity_gate": component_sensitivity_gate,
        "normalization_scale_gate": normalization_scale_gate,
        "streamwise_sign_gate": streamwise_sign_gate,
        "component_source_window_gate": component_source_window_gate,
        "component_source_window_gate_reasons": component_sensitivity_audit.get(
            "component_source_window_gate_reasons", []
        ),
        "component_source_window_gate_reasons_csv": ";".join(
            str(reason) for reason in component_sensitivity_audit.get("component_source_window_gate_reasons", [])
        )
        if isinstance(component_sensitivity_audit.get("component_source_window_gate_reasons"), list)
        else str(component_sensitivity_audit.get("component_source_window_gate_reasons", "")),
        "component_source_time_steps": str(component_sensitivity_audit.get("component_source_time_steps") or ""),
        "component_source_time_steps_match_runtime": component_source_steps_match_runtime,
        "component_source_steps_strictly_increasing": component_source_steps_increasing,
        "component_source_step_spacing_uniform": component_source_steps_uniform,
        "component_source_step_span": component_sensitivity_audit.get("component_source_step_span"),
        "component_minimum_source_step_span": component_sensitivity_audit.get("component_minimum_source_step_span"),
        "component_source_sha256": str(component_sensitivity_audit.get("component_source_sha256") or ""),
        "component_source_vtk_sha256_match_runtime": component_source_hashes_match_runtime,
        "component_source_step_hash_pairs_match_runtime": component_source_step_hash_pairs_match_runtime,
        "native_preconditions_protocol_identity_gate": protocol_identity_gate,
        "native_preconditions_time_average_gate": time_average_gate,
        "native_preconditions_manifest_sha256": sha256_file(manifest_path),
        "native_preconditions_setup_sha256": setup_sha,
        "native_preconditions_defines_sha256": defines_sha,
        "native_preconditions_metadata_sha256": metadata_sha,
        "native_preconditions_runtime_audit_sha256": runtime_audit_sha,
        "native_preconditions_protocol_audit_sha256": protocol_audit_sha,
        "validation_protocol_content_gate": protocol_content_audit["gate"],
        "validation_protocol_content_gate_reasons": protocol_content_audit["reasons"],
        "validation_protocol_content_gate_reasons_csv": protocol_content_audit["reasons_csv"],
        "validation_protocol_content_item_count": protocol_content_audit["item_count"],
        "validation_protocol_content_required_item_count": protocol_content_audit["required_item_count"],
        "validation_protocol_content_audit_gate": protocol_content_audit["audit_gate"],
        "validation_protocol_content_missing_keys": protocol_content_audit["missing_keys"],
        "validation_protocol_content_missing_keys_csv": ";".join(protocol_content_audit["missing_keys"]),
        "validation_protocol_content_missing_status_keys": protocol_content_audit["missing_status_keys"],
        "validation_protocol_content_missing_status_keys_csv": ";".join(
            protocol_content_audit["missing_status_keys"]
        ),
        "validation_protocol_content_failed_keys": protocol_content_audit["failed_keys"],
        "validation_protocol_content_failed_keys_csv": ";".join(protocol_content_audit["failed_keys"]),
        "validation_protocol_content_risk_keys": protocol_content_audit["risk_keys"],
        "validation_protocol_content_risk_keys_csv": ";".join(protocol_content_audit["risk_keys"]),
        "validation_protocol_content_partial_keys": protocol_content_audit["partial_keys"],
        "validation_protocol_content_partial_keys_csv": ";".join(protocol_content_audit["partial_keys"]),
        "native_preconditions_af_csv_sha256": af_sha,
        "role_audits": role_audits,
        "native_preconditions_gate": "pass" if not reasons else "fail",
        "native_preconditions_gate_reasons": reasons,
        "native_preconditions_gate_reasons_csv": ";".join(reasons),
        "native_precondition_closure_gate": native_precondition_closure["gate"],
        "native_precondition_closed_stage_count": native_precondition_closure["closed_stage_count"],
        "native_precondition_failed_stage_count": native_precondition_closure["failed_stage_count"],
        "native_precondition_failed_stage_keys": native_precondition_closure["failed_stage_keys"],
        "native_precondition_failed_stage_keys_csv": native_precondition_closure["failed_stage_keys_csv"],
        "native_precondition_top_blocking_stage_key": native_precondition_closure["top_blocking_stage_key"],
        "native_precondition_top_blocking_stage_rank": native_precondition_closure["top_blocking_stage_rank"],
        "native_precondition_top_blocking_stage_reason_count": native_precondition_closure["top_blocking_stage_reason_count"],
        "native_precondition_top_blocking_stage_reasons": native_precondition_closure["top_blocking_stage_reasons"],
        "native_precondition_top_blocking_stage_reasons_csv": native_precondition_closure["top_blocking_stage_reasons_csv"],
        "native_precondition_closure": native_precondition_closure["stages"],
        "native_top_blocking_priority_rank": native_top_priority.get("rank"),
        "native_top_blocking_priority_key": native_top_priority.get("key", ""),
        "native_top_blocking_priority_reason_count": native_top_priority.get("reason_count"),
        "native_top_blocking_priority_reasons": native_top_priority.get("reasons", []),
        "native_top_blocking_priority_reasons_csv": ";".join(
            str(reason) for reason in native_top_priority.get("reasons", [])
        ),
        "native_top_blocking_priority_diagnosis": native_top_priority.get("diagnosis", ""),
        "native_top_blocking_priority_next_action": native_top_priority.get("next_action", ""),
        "native_rerun_prescription_gate": native_rerun_prescription["gate"],
        "native_rerun_prescription_top_key": native_rerun_prescription["top_key"],
        "native_rerun_prescription_experiment": native_rerun_prescription["experiment"],
        "native_rerun_prescription_required_controls": native_rerun_prescription["required_controls"],
        "native_rerun_prescription_required_controls_csv": native_rerun_prescription["required_controls_csv"],
        "native_rerun_prescription_minimum_final_window": native_rerun_prescription["minimum_final_window"],
        "native_rerun_prescription_accuracy_interpretation_allowed": native_rerun_prescription[
            "accuracy_interpretation_allowed"
        ],
        "native_rerun_prescription_summary": native_rerun_prescription["summary"],
        "native_diagnostic_priority_order": [
            "validation_protocol_content",
            "turbulent_inlet_method_and_u_k_preservation",
            "boundary_roughness_blockage",
            "lbm_stability_scaling",
            "time_averaging_stationarity",
            "coordinate_component_normalization",
            "systematic_bias_after_prerequisites",
        ],
        "native_diagnostic_priority": native_diagnostic_priority,
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0 if not reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
