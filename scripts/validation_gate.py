#!/usr/bin/env python3
"""Audit CityLBM/FluidX3D validation run artifacts before paper claims.

This script does not run CFD. It checks whether an existing run package has the
minimum evidence needed before AIJ Case A/E metrics can be treated as validation
evidence rather than a smoke or diagnostic run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

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

NATIVE_CITYLBM_PARITY_CRITICAL_FIELDS = [
    "case",
    "wind_direction",
    "dx_m",
    "steps",
    "save_interval",
    "averaging_window",
    "requested_time_steps",
    "requested_vtk_save_interval",
    "requested_vtk_frame_count",
    "time_averaging_fidelity_class",
    "Uref_mps",
    "Zref_m",
    "compared_component",
    "probe_component_fidelity_class",
    "wind_vector",
    "inlet_face",
    "outlet_face",
    "lateral_faces",
    "velocity_set",
    "les_model",
    "synthetic_inlet_method",
    "inlet_distribution_treatment",
    "inlet_method_class",
    "inlet_source_method_class",
    "inlet_source_turbulent_inflow_fidelity_class",
    "inlet_source_correlation_model",
    "inlet_source_distribution_route",
    "inlet_source_reynolds_stress_treatment",
    "inlet_source_has_three_component_velocity_write",
    "inlet_source_has_three_component_fluctuation_evidence",
    "inlet_source_has_k_driven_three_component_stg",
    "inlet_source_has_component_phase_decorrelation",
    "inlet_source_has_temporal_filter_state",
    "inlet_source_has_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_mean_preserving_inlet_correction",
    "inlet_source_has_streamwise_clipping_control",
    "inlet_source_streamwise_clipping_enabled",
    "inlet_source_has_legacy_hardcoded_streamwise_clipping",
    "inlet_source_has_uncorrelated_random_inlet",
    "inlet_source_has_correlated_velocity_field_only",
    "inlet_source_has_uncorrelated_rms_velocity_field_only",
    "wall_roughness_treatment",
    "boundary_evidence_class",
    "boundary_source_method_class",
    "boundary_source_fidelity_class",
    "boundary_source_has_complete_wind_tunnel_evidence",
    "boundary_source_has_empty_advanced_method_stub_only",
    "native_preconditions_strict_native_run_gate",
    "requested_vtk_frame_gate",
    "run_freshness_gate",
    "time_averaging_gate",
    "lbm_stability_gate",
    "normalization_valid",
    "compared_component_consistency_gate",
    "wind_direction_valid",
    "blockage_protocol_gate",
    "boundary_protocol_gate",
    "boundary_evidence_gate",
    "boundary_source_gate",
    "paper_grade_boundary_source_gate",
    "boundary_runtime_gate",
    "boundary_runtime_traceability_gate",
    "boundary_runtime_profile_preservation_gate",
    "boundary_runtime_inlet_gate",
    "boundary_runtime_side_top_gate",
    "boundary_runtime_side_top_normal_leakage_gate",
    "boundary_runtime_outlet_gate",
    "inlet_source_gate",
    "paper_grade_inlet_source_gate",
    "inlet_source_distribution_route_gate",
    "inlet_method_class_supported",
    "inlet_length_scale_gate",
    "inlet_correlation_gate",
    "inlet_profile_time_averaging_gate",
    "inlet_streamwise_direction_gate",
    "inlet_profile_gate",
    "inlet_u_profile_gate",
    "inlet_k_profile_gate",
    "probe_vtk_source_window_gate",
    "component_normalization_gate",
    "component_sensitivity_gate",
    "normalization_scale_gate",
    "streamwise_sign_gate",
    "synthetic_temporal_sampling_gate",
    "synthetic_mode_count",
    "synthetic_update_interval",
    "synthetic_minimum_recommended_refresh_count",
    "synthetic_expected_final_window_refresh_count",
    "synthetic_component_norm_x",
    "synthetic_component_norm_y",
    "synthetic_component_norm_z",
    "synthetic_correlation_length_m",
    "boundary_runtime_frame_count",
    "boundary_runtime_source_step_span",
    "boundary_runtime_max_u_mae_ratio",
    "boundary_runtime_max_side_top_normal_velocity_ratio",
    "profile_csv_sha256",
    "official_measurement_sha256",
    "component_sensitivity_official_sha256",
    "inlet_source_setup_sha256",
    "boundary_source_setup_sha256",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate a CityLBM/FluidX3D AIJ validation run package."
    )
    parser.add_argument("run_dir", help="Case root or output directory to audit.")
    parser.add_argument(
        "--metrics",
        help="Validation metrics CSV/JSON. Defaults to the newest matching file in run_dir.",
    )
    parser.add_argument(
        "--probe-audit",
        help="Optional probe audit CSV from Data Probe.",
    )
    parser.add_argument(
        "--official",
        help="Official RS/measurement CSV used to build the probe metrics and component sensitivity audit.",
    )
    parser.add_argument("--case", default="", help="Expected case label, e.g. CaseA or CaseE.")
    parser.add_argument("--software", default="", help="Expected software label, e.g. native-fluidx3d or citylbm.")
    parser.add_argument("--min-avg-frames", type=int, default=40)
    parser.add_argument("--min-avg-step-span", type=int, default=20000)
    parser.add_argument("--max-mean-speed-stddev-ratio", type=float, default=0.05)
    parser.add_argument("--max-point-speed-stddev-ratio", type=float, default=0.20)
    parser.add_argument("--max-u-bias-ratio", type=float, default=0.15)
    parser.add_argument("--max-u-rmse-ratio", type=float, default=0.30)
    parser.add_argument("--min-u-r2", type=float, default=0.70)
    parser.add_argument("--min-slope", type=float, default=0.70)
    parser.add_argument("--max-slope", type=float, default=1.30)
    parser.add_argument("--max-intercept-abs", type=float, default=0.20)
    parser.add_argument("--max-k-bias-ratio", type=float, default=0.30)
    parser.add_argument("--max-k-rmse-ratio", type=float, default=0.50)
    parser.add_argument("--max-empty-tunnel-u-bias-ratio", type=float, default=0.05)
    parser.add_argument("--max-empty-tunnel-k-bias-ratio", type=float, default=0.15)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--max-probe-failure-fraction", type=float, default=0.0)
    parser.add_argument("--max-probe-distance-dx-ratio", type=float, default=1.0)
    parser.add_argument("--max-probe-tolerance-dx-ratio", type=float, default=1.0)
    parser.add_argument("--max-component-rmse-improvement-ratio", type=float, default=0.20)
    parser.add_argument("--max-normalization-best-scale-deviation", type=float, default=0.20)
    parser.add_argument("--min-normalization-scaled-improvement-ratio", type=float, default=0.25)
    parser.add_argument("--min-inlet-temporal-finite-fraction", type=float, default=0.80)
    parser.add_argument("--min-inlet-spatial-finite-fraction", type=float, default=0.80)
    parser.add_argument("--min-inlet-correlation-sample-count", type=int, default=100)
    parser.add_argument("--min-inlet-correlation-adjacent-pair-count", type=int, default=100)
    parser.add_argument("--min-inlet-streamwise-variance", type=float, default=1.0e-12)
    parser.add_argument("--min-inlet-temporal-lag1-correlation", type=float, default=0.10)
    parser.add_argument("--min-inlet-spatial-adjacent-correlation", type=float, default=0.05)
    parser.add_argument("--min-inlet-temporal-integral-lag-count", type=int, default=2)
    parser.add_argument("--min-inlet-spatial-integral-lag-count", type=int, default=2)
    parser.add_argument("--max-frontal-blockage-ratio", type=float, default=0.05)
    parser.add_argument("--max-estimated-mach", type=float, default=0.20)
    parser.add_argument("--min-lbm-tau", type=float, default=0.500001)
    parser.add_argument("--max-lbm-tau", type=float, default=2.0)
    parser.add_argument("--max-paper-dx-m", type=float, default=3.0)
    parser.add_argument("--min-grid-sensitivity-run-count", type=int, default=2)
    parser.add_argument("--min-grid-refinement-ratio", type=float, default=1.25)
    parser.add_argument("--max-grid-rmse-change-ratio", type=float, default=0.10)
    parser.add_argument("--max-grid-bias-change-ratio", type=float, default=0.05)
    parser.add_argument("--grid-dx-tolerance", type=float, default=1.0e-9)
    parser.add_argument("--min-native-citylbm-parity-field-count", type=int, default=20)
    parser.add_argument("--min-native-citylbm-parity-gate-field-count", type=int, default=20)
    parser.add_argument("--min-native-citylbm-parity-hash-field-count", type=int, default=5)
    parser.add_argument("--max-native-citylbm-rmse-delta", type=float, default=0.03)
    parser.add_argument("--max-native-citylbm-abs-bias-delta", type=float, default=0.03)
    parser.add_argument("--max-native-citylbm-r2-drop", type=float, default=0.05)
    parser.add_argument("--max-native-citylbm-slope-delta", type=float, default=0.10)
    parser.add_argument("--max-native-citylbm-intercept-delta", type=float, default=0.05)
    parser.add_argument("--expected-compared-component", default="", help="Require a specific Data Probe compared_component, e.g. speed_ratio or streamwise_ratio.")
    parser.add_argument("--expected-uref", type=float, default=None, help="Require the metrics/Data Probe Uref to match this value.")
    parser.add_argument("--uref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--expected-wind-vector", default="", help="Require wind_vector to match x,y,z or (x,y,z), e.g. 0,-1,0.")
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--expected-vtk-pattern", default="u-*.vtk", help="Require the runtime VTK audit to use this velocity-field glob.")
    parser.add_argument(
        "--allow-velocity-only-inlet",
        action="store_true",
        help=(
            "Diagnostic override only: allow CityLBM STG-lite velocity-field-only "
            "inlet to pass the general inlet-turbulence diagnostic gate when "
            "empty-tunnel U/k preservation passes. This flag cannot satisfy the "
            "paper-grade turbulent-inlet-method gate."
        ),
    )
    parser.add_argument(
        "--allow-summary-only-probe-metrics",
        action="store_true",
        help=(
            "Diagnostic override only: downgrade missing probe-audit traceability to WARN for legacy "
            "summaries. It cannot satisfy paper-grade coordinate, component or probe-mapping gates."
        ),
    )
    parser.add_argument(
        "--allow-diagnostic",
        action="store_true",
        help="Return exit code 0 for diagnostic-only packages while still reporting FAIL gates.",
    )
    parser.add_argument("--out", help="Optional JSON report path.")
    return parser.parse_args()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256_file(path: Optional[Path]) -> str:
    if not path or not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_metrics(path: Optional[Path]) -> Tuple[Dict[str, Any], Optional[Path]]:
    if not path or not path.exists():
        return {}, path
    if path.suffix.lower() == ".json":
        data = read_json(path)
        if isinstance(data, dict):
            return data, path
        return {}, path
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}, path
    return rows[-1], path


def find_first(base: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        candidate = base / name
        if candidate.exists():
            return candidate
        nested_candidate = base / "validation_chain" / name
        if nested_candidate.exists():
            return nested_candidate
    parent = base.parent
    if parent != base:
        for name in names:
            candidate = parent / name
            if candidate.exists():
                return candidate
            nested_candidate = parent / "validation_chain" / name
            if nested_candidate.exists():
                return nested_candidate
    return None


def find_metrics(base: Path) -> Optional[Path]:
    patterns = [
        "*validation_metrics*.csv",
        "*metrics*.csv",
        "*validation*.csv",
        "*validation_metrics*.json",
        "*metrics*.json",
    ]
    candidates: List[Path] = []
    for root in [base, base.parent]:
        if root.exists():
            for pattern in patterns:
                candidates.extend(root.glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def as_int(value: Any) -> Optional[int]:
    number = as_float(value)
    if number is None:
        return None
    return int(round(number))


def as_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "pass", "valid"}:
        return True
    if text in {"false", "0", "no", "n", "fail", "invalid"}:
        return False
    return None


def get_any(mapping: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def get_first_available(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def as_string_list(value: Any) -> List[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(";") if part.strip()]


def declared_paper_averaging_status(
    source: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
    *,
    require_gate: bool,
) -> Dict[str, Any]:
    expected_frames = as_int(get_any(source, ["ExpectedVtkFrameCount", "expected_vtk_frame_count"]))
    recommended_frames = as_int(get_any(source, ["PaperRecommendedAveragingFrames", "paper_recommended_averaging_frames"]))
    recommended_span = as_int(get_any(source, ["PaperRecommendedAverageStepSpan", "paper_recommended_average_step_span"]))
    expected_span = as_int(get_any(source, ["ExpectedPaperAverageStepSpan", "expected_paper_average_step_span"]))
    paper_gate = str(get_any(source, ["TimeAveragingPaperGate", "time_averaging_paper_gate"]) or "").strip().lower()

    required_frames = max(min_avg_frames, recommended_frames or 0)
    required_span = max(min_avg_step_span, recommended_span or 0)
    reasons: List[str] = []
    if expected_frames is None:
        reasons.append("expected_vtk_frame_count_missing")
    elif expected_frames < required_frames:
        reasons.append(f"expected_vtk_frame_count_below_{required_frames}")

    if recommended_frames is None:
        reasons.append("paper_recommended_averaging_frames_missing")
    if recommended_span is None:
        reasons.append("paper_recommended_average_step_span_missing")

    if expected_span is None:
        reasons.append("expected_paper_average_step_span_missing")
    elif expected_span < required_span:
        reasons.append(f"expected_paper_average_step_span_below_{required_span}")

    if require_gate:
        if not paper_gate:
            reasons.append("time_averaging_paper_gate_missing")
        elif paper_gate != "pass_paper_recommended_frame_count_and_step_span":
            reasons.append(f"time_averaging_paper_gate_not_pass:{paper_gate}")

    return {
        "ok": not reasons,
        "expected_vtk_frame_count": expected_frames,
        "paper_recommended_averaging_frames": recommended_frames,
        "paper_recommended_average_step_span": recommended_span,
        "expected_paper_average_step_span": expected_span,
        "required_frames": required_frames,
        "required_span": required_span,
        "time_averaging_paper_gate": paper_gate,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


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
    candidate_keys = [normalized_column_key(candidate) for candidate in candidates]
    for column in columns:
        normalized_column = normalized_column_key(column)
        if any(candidate and candidate in normalized_column for candidate in candidate_keys):
            return column
    return ""


def parse_vector(value: Any) -> Optional[Tuple[float, float, float]]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.strip("()[]{}")
    parts = [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    if len(parts) != 3:
        return None
    values = [as_float(part) for part in parts]
    if any(v is None for v in values):
        return None
    return values[0], values[1], values[2]


def normalize_vector(vector: Optional[Tuple[float, float, float]]) -> Optional[Tuple[float, float, float]]:
    if vector is None:
        return None
    length = math.sqrt(sum(component * component for component in vector))
    if length <= 1.0e-12:
        return None
    return tuple(component / length for component in vector)


def vector_delta(
    actual: Optional[Tuple[float, float, float]],
    expected: Optional[Tuple[float, float, float]],
) -> Optional[float]:
    actual_unit = normalize_vector(actual)
    expected_unit = normalize_vector(expected)
    if actual_unit is None or expected_unit is None:
        return None
    return math.sqrt(sum((a - e) * (a - e) for a, e in zip(actual_unit, expected_unit)))


def add_gate(gates: List[Dict[str, Any]], key: str, status: str, evidence: str, required: str = "") -> None:
    gates.append(
        {
            "key": key,
            "status": status,
            "evidence": evidence,
            "required_next_action": required,
        }
    )


def gate_by_key(gates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(gate.get("key") or ""): gate for gate in gates}


def add_priority(
    priorities: List[Dict[str, Any]],
    rank: int,
    key: str,
    gate: Optional[Dict[str, Any]],
    reason: str,
    action: str,
) -> None:
    priorities.append(
        {
            "rank": rank,
            "key": key,
            "gate_status": str(gate.get("status") or "MISSING") if gate else "MISSING",
            "reason": reason,
            "next_action": action,
        }
    )


def extract_systematic_prerequisite_blockers(evidence: str) -> str:
    text = str(evidence or "")
    marker = "prerequisite gates are not closed: "
    if marker not in text:
        return ""
    blockers = text.split(marker, 1)[1]
    for suffix in [". Treat ", "."]:
        if suffix in blockers:
            blockers = blockers.split(suffix, 1)[0]
            break
    return blockers.strip()


def extract_systematic_prerequisite_blocker_list(evidence: str) -> List[str]:
    blockers = extract_systematic_prerequisite_blockers(evidence)
    if not blockers:
        return []
    return [part.strip() for part in blockers.split(";") if part.strip()]


def allow_systematic_root_cause_interpretation(
    systematic_bias_present: bool, failed_prerequisites: List[str]
) -> bool:
    return bool(systematic_bias_present) and not failed_prerequisites


def allow_solver_accuracy_interpretation(
    systematic_bias_present: bool,
    accuracy_pass: bool,
    failed_prerequisites: List[str],
) -> bool:
    return bool(accuracy_pass) and not systematic_bias_present and not failed_prerequisites


def solver_accuracy_interpretation_blockers(
    systematic_bias_present: bool,
    accuracy_pass: bool,
    failed_prerequisites: List[str],
) -> List[str]:
    blockers: List[str] = []
    if systematic_bias_present:
        blockers.append("systematic_bias_present")
    if not accuracy_pass:
        blockers.append("mean_velocity_accuracy_failed")
    if failed_prerequisites:
        blockers.append("prerequisite_gates_open")
    return blockers


def mean_velocity_accuracy_failure_reasons(
    *,
    u_bias: Optional[float],
    u_rmse: Optional[float],
    u_r2: Optional[float],
    slope: Optional[float],
    intercept: Optional[float],
    max_u_bias_ratio: float,
    max_u_rmse_ratio: float,
    min_u_r2: float,
    min_slope: float,
    max_slope: float,
    max_intercept_abs: float,
) -> List[str]:
    reasons: List[str] = []
    if u_bias is None:
        reasons.append("U_bias_ratio_missing")
    elif abs(u_bias) > max_u_bias_ratio:
        reasons.append(f"U_bias_ratio_abs_above_{max_u_bias_ratio:g}:{u_bias:g}")
    if u_rmse is None:
        reasons.append("U_RMSE_ratio_missing")
    elif u_rmse > max_u_rmse_ratio:
        reasons.append(f"U_RMSE_ratio_above_{max_u_rmse_ratio:g}:{u_rmse:g}")
    if u_r2 is None:
        reasons.append("U_R2_missing")
    elif u_r2 < min_u_r2:
        reasons.append(f"U_R2_below_{min_u_r2:g}:{u_r2:g}")
    if slope is None:
        reasons.append("U_regression_slope_missing")
    elif slope < min_slope or slope > max_slope:
        reasons.append(f"U_regression_slope_outside_{min_slope:g}_{max_slope:g}:{slope:g}")
    if intercept is None:
        reasons.append("U_regression_intercept_missing")
    elif abs(intercept) > max_intercept_abs:
        reasons.append(f"U_regression_intercept_abs_above_{max_intercept_abs:g}:{intercept:g}")
    return reasons


def build_diagnostic_priority(gates: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    by_key = gate_by_key(gates)
    priorities: List[Dict[str, Any]] = []

    protocol_gate = by_key.get("validation_protocol_content")
    if protocol_gate is None or protocol_gate.get("status") != PASS:
        add_priority(
            priorities,
            0,
            "validation_protocol_content",
            protocol_gate,
            "The validation protocol audit is missing, empty or incomplete, so later inlet, boundary, averaging and bias diagnostics cannot be treated as a complete paper-grade evidence chain.",
            "Regenerate validation_protocol_audit.json from the current case and verify all required protocol items before interpreting CFD error metrics.",
        )

    source_gate = by_key.get("inlet_source_evidence")
    inlet_gate = by_key.get("inlet_turbulence")
    paper_inlet_gate = by_key.get("paper_grade_inlet_method")
    length_gate = by_key.get("inlet_length_scale")
    correlation_gate = by_key.get("inlet_correlation")
    inlet_profile_gate = by_key.get("inlet_profile_preservation")
    inlet_profile_hash_gate = by_key.get("inlet_profile_vtk_hash_traceability")
    inlet_correlation_hash_gate = by_key.get("inlet_correlation_vtk_hash_traceability")
    native_inlet_traceability_gate = by_key.get("native_inlet_precondition_traceability")
    k_gate = by_key.get("k_preservation_or_accuracy")
    custom_k_gate = by_key.get("custom_k_profile")
    inlet_gates = [
        source_gate,
        inlet_gate,
        paper_inlet_gate,
        length_gate,
        correlation_gate,
        custom_k_gate,
        inlet_profile_gate,
        inlet_profile_hash_gate,
        inlet_correlation_hash_gate,
        native_inlet_traceability_gate,
        k_gate,
    ]
    if any(gate is None or gate.get("status") != PASS for gate in inlet_gates):
        inlet_priority_gate = next(
            (
                gate for gate in inlet_gates
                if gate is None or gate.get("status") != PASS
            ),
            paper_inlet_gate,
        )
        add_priority(
            priorities,
            1,
            "turbulent_inlet_method_and_u_k_preservation",
            inlet_priority_gate,
            "The first reliability gate is the AIJ inflow: AF U(z)/k(z) must be preserved, and turbulence cannot be RMS/k random velocity perturbations only.",
            "Verify inlet-source code, U/k profile preservation and inlet correlation on the same final VTK window; replace velocity-field-only STG-lite with distribution-consistent DFM/SEM/precursor/recycling evidence before paper claims.",
        )

    boundary_source_gate = by_key.get("boundary_source_evidence")
    boundary_gate = by_key.get("boundary_protocol")
    boundary_runtime_gate = by_key.get("boundary_runtime")
    roughness_gate = by_key.get("roughness_or_precursor")
    native_boundary_traceability_gate = by_key.get("native_boundary_traceability")
    if any(
        gate is None or gate.get("status") != PASS
        for gate in [
            boundary_source_gate,
            boundary_gate,
            boundary_runtime_gate,
            roughness_gate,
            native_boundary_traceability_gate,
        ]
    ):
        boundary_priority_gate = next(
            (
                gate
                for gate in [
                    boundary_source_gate,
                    boundary_gate,
                    boundary_runtime_gate,
                    roughness_gate,
                    native_boundary_traceability_gate,
                ]
                if gate is None or gate.get("status") != PASS
            ),
            boundary_gate,
        )
        add_priority(
            priorities,
            2,
            "boundary_roughness_blockage",
            boundary_priority_gate,
            "Simplified inlet/outlet/lateral/top/floor conditions, missing rough-wall treatment or excessive blockage can dominate AIJ validation error.",
            "Audit AIJ-equivalent boundary conditions, roughness treatment, fetch/development length, lateral/top clearance and blockage before tuning solver parameters.",
        )

    freshness_gate = by_key.get("run_freshness")
    vtk_hash_gate = by_key.get("runtime_vtk_hash_traceability")
    time_gate = by_key.get("time_averaging")
    metrics_time_gate = by_key.get("metrics_time_averaging_consistency")
    native_time_traceability_gate = by_key.get("native_time_averaging_traceability")
    time_gates = [
        freshness_gate,
        vtk_hash_gate,
        time_gate,
        metrics_time_gate,
        native_time_traceability_gate,
    ]
    if any(gate is None or gate.get("status") != PASS for gate in time_gates):
        time_priority_gate = next(
            (
                gate for gate in time_gates
                if gate is None or gate.get("status") != PASS
            ),
            time_gate,
        )
        add_priority(
            priorities,
            3,
            "time_averaging_stationarity",
            time_priority_gate,
            "A short or stale final VTK window, such as only a few late frames, cannot support stable mean-flow validation.",
            "Regenerate VTK from the current setup and postprocess a sufficiently long final-window average with archived hashes and stationarity statistics.",
        )

    coordinate_gate = by_key.get("coordinate_normalization")
    metrics_hash_gate = by_key.get("metrics_input_hash_traceability")
    compared_gate = by_key.get("compared_component")
    projection_gate = by_key.get("probe_projection_distance")
    grid_extent_gate = by_key.get("probe_grid_extent")
    probe_source_gate = by_key.get("probe_source_window")
    probe_gate = by_key.get("probe_mapping")
    sensitivity_gate = by_key.get("component_normalization_sensitivity")
    native_probe_traceability_gate = by_key.get("native_probe_component_traceability")
    coordinate_gates = [
        metrics_hash_gate,
        coordinate_gate,
        compared_gate,
        projection_gate,
        grid_extent_gate,
        probe_source_gate,
        probe_gate,
        sensitivity_gate,
        native_probe_traceability_gate,
    ]
    if any(gate is None or gate.get("status") != PASS for gate in coordinate_gates):
        coordinate_priority_gate = next(
            (
                gate for gate in coordinate_gates
                if gate is None or gate.get("status") != PASS
            ),
            coordinate_gate,
        )
        add_priority(
            priorities,
            4,
            "coordinate_component_normalization",
            coordinate_priority_gate,
            "Probe coordinates, wind sign, compared component and Uref must be closed before interpreting bias.",
            "Fix RS probe projection, wind vector, compared_component and Uref/SI velocity conversion first; rerun component/Uref sensitivity before interpreting bias.",
        )

    native_preconditions_full_gate = by_key.get("native_preconditions_full_evidence")
    native_gate = by_key.get("native_baseline")
    if any(
        gate is None or gate.get("status") != PASS
        for gate in [native_inlet_traceability_gate, native_preconditions_full_gate, native_gate]
    ):
        if native_inlet_traceability_gate is None or native_inlet_traceability_gate.get("status") != PASS:
            native_priority_gate = native_inlet_traceability_gate
        elif native_preconditions_full_gate is None or native_preconditions_full_gate.get("status") != PASS:
            native_priority_gate = native_preconditions_full_gate
        else:
            native_priority_gate = native_gate
        native_top_key = str(get_any(metrics, ["native_top_blocking_priority_key"]) or "").strip()
        native_top_diagnosis = str(
            get_any(metrics, ["native_top_blocking_priority_diagnosis"]) or ""
        ).strip()
        native_top_action = str(
            get_any(metrics, ["native_top_blocking_priority_next_action"]) or ""
        ).strip()
        native_top_reason_text = str(
            get_any(metrics, ["native_top_blocking_priority_reasons"]) or ""
        ).strip()
        native_reason = (
            f"Native FluidX3D preconditions report top blocker '{native_top_key}': "
            f"{native_top_diagnosis or 'no diagnosis text'}"
            + (f" Reasons: {native_top_reason_text}." if native_top_reason_text else "")
            if native_top_key
            else "CityLBM accuracy cannot be separated from native FluidX3D/protocol error without a paired native baseline."
        )
        native_action = (
            native_top_action
            if native_top_action
            else "Run native FluidX3D with the same setup, grid, averaging and probes, and archive full inlet, boundary, probe and component-normalization precondition evidence before changing CityLBM."
        )
        add_priority(
            priorities,
            5,
            "native_fluidx3d_baseline",
            native_priority_gate,
            native_reason,
            native_action,
        )

    parity_gate = by_key.get("native_citylbm_parity")
    if parity_gate is None or parity_gate.get("status") != PASS:
        add_priority(
            priorities,
            6,
            "native_citylbm_parity",
            parity_gate,
            "CityLBM accuracy cannot be compared with native FluidX3D unless the paired runs use the same protocol.",
            "Archive native_citylbm_parity_audit.json proving matched case, wind, dx, averaging, Uref, inlet, boundary and probe settings.",
        )

    accuracy_delta_gate = by_key.get("native_citylbm_accuracy_delta")
    if accuracy_delta_gate is None or accuracy_delta_gate.get("status") != PASS:
        add_priority(
            priorities,
            7,
            "native_citylbm_accuracy_delta",
            accuracy_delta_gate,
            "After protocol parity, CityLBM must not add RMSE, bias, R2 or regression error beyond the paired native FluidX3D run.",
            "Archive native_citylbm_accuracy_delta_audit.json; if CityLBM adds error, inspect parameter transfer, setup.cpp generation, VTK scaling and probe postprocessing before attributing residual bias to FluidX3D physics.",
        )

    grid_gate = by_key.get("grid_sensitivity")
    if grid_gate is None or grid_gate.get("status") != PASS:
        add_priority(
            priorities,
            8,
            "grid_sensitivity",
            grid_gate,
            "A single high-resolution run cannot prove that residual bias is independent of dx.",
            "Run at least two matched grid levels and bound the finest-grid RMSE/bias change before interpreting solver accuracy.",
        )

    systematic_gate = by_key.get("systematic_bias")
    systematic_interpretation_gate = by_key.get("systematic_bias_interpretation")
    mean_gate = by_key.get("mean_velocity_accuracy")
    systematic_flag = str(get_any(metrics, ["systematic_bias_flag"]) or "").strip().lower()
    bias_diagnosis = str(get_any(metrics, ["bias_diagnosis"]) or "").strip()
    if systematic_interpretation_gate is not None and systematic_interpretation_gate.get("status") != PASS:
        failed_prereq_text = extract_systematic_prerequisite_blockers(
            str(systematic_interpretation_gate.get("evidence") or "")
        )
        native_top_key = str(get_any(metrics, ["native_top_blocking_priority_key"]) or "").strip()
        native_top_diagnosis = str(
            get_any(metrics, ["native_top_blocking_priority_diagnosis"]) or ""
        ).strip()
        native_top_action = str(
            get_any(metrics, ["native_top_blocking_priority_next_action"]) or ""
        ).strip()
        blocker_detail = (
            f" Open prerequisites: {failed_prereq_text}."
            if failed_prereq_text
            else ""
        )
        native_detail = (
            f" Native top blocker '{native_top_key}': {native_top_diagnosis or 'no diagnosis text'}."
            if native_top_key
            else ""
        )
        systematic_action = (
            f"{native_top_action} Then close all listed prerequisite gates before interpreting residual bias."
            if native_top_action
            else "Close inlet turbulence, boundary, averaging, coordinate/component/Uref, native baseline, parity and grid-sensitivity gates before interpreting residual bias."
        )
        add_priority(
            priorities,
            9,
            "systematic_bias_interpretation",
            systematic_interpretation_gate,
            (
                "Large bias is present while prerequisite evidence gates remain open, so the result cannot support a solver-accuracy claim."
                + blocker_detail
                + native_detail
            ),
            systematic_action,
        )
    if systematic_gate is not None and systematic_gate.get("status") != PASS:
        add_priority(
            priorities,
            10,
            "systematic_bias_root_cause",
            systematic_gate,
            f"Metrics report systematic bias: {systematic_flag or 'flagged'}; {bias_diagnosis or 'no diagnosis string'}.",
            "After ranks 1-8 pass, treat remaining bias as a physics/protocol issue rather than a CityLBM precision claim.",
        )
    elif mean_gate is not None and mean_gate.get("status") != PASS:
        add_priority(
            priorities,
            10,
            "mean_velocity_accuracy",
            mean_gate,
            "Mean-flow metrics still fail after prerequisite evidence gates.",
            "Use the regression slope/intercept, RMSE and bias fields to design the next native-vs-CityLBM sensitivity run.",
        )

    return priorities


def load_protocol_items(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not audit:
        return []
    if isinstance(audit.get("Items"), list):
        return audit["Items"]
    if isinstance(audit.get("items"), list):
        return audit["items"]
    if isinstance(audit, list):
        return audit
    return []


def protocol_status(items: List[Dict[str, Any]], key: str) -> Optional[str]:
    for item in items:
        if str(item.get("Key") or item.get("key") or "") == key:
            return str(item.get("Status") or item.get("status") or "").lower()
    return None


def audit_protocol_content(
    audit: Dict[str, Any],
    required_keys: Iterable[str] = REQUIRED_PROTOCOL_ITEM_KEYS,
) -> Dict[str, Any]:
    items = [item for item in load_protocol_items(audit) if isinstance(item, dict)]
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
        "ok": not reasons,
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


def paper_grade_inlet_method_pass(
    *,
    empty_tunnel_pass: bool,
    inlet_source_evidence_ok: bool,
    audit_paper_grade_inlet_source_gate: str,
    audit_inlet_source_distribution_consistent: Optional[bool],
    audit_inlet_source_velocity_field_only: Optional[bool],
    audit_inlet_source_comment_stripped: Optional[bool],
    audit_has_uncorrelated_random_inlet: Optional[bool],
    audit_inlet_source_turbulent_inflow_fidelity_class: str,
    paper_method_class_ok: bool,
    treatment_distribution_consistent: bool,
    distribution_status: str,
    treatment_velocity_only: bool,
) -> bool:
    return (
        empty_tunnel_pass
        and inlet_source_evidence_ok
        and audit_paper_grade_inlet_source_gate == "pass"
        and audit_inlet_source_distribution_consistent is True
        and audit_inlet_source_velocity_field_only is not True
        and audit_inlet_source_comment_stripped is True
        and audit_has_uncorrelated_random_inlet is not True
        and (
            audit_inlet_source_turbulent_inflow_fidelity_class
            in {
                "distribution_consistent_digital_filter",
                "distribution_consistent_synthetic_eddy",
                "distribution_consistent_precursor_or_recycling",
            }
        )
        and paper_method_class_ok
        and treatment_distribution_consistent
        and distribution_status == "pass"
        and not treatment_velocity_only
    )


def stg_three_component_evidence_pass(
    *,
    required: bool,
    has_three_component_velocity_write: Optional[bool],
    has_three_component_fluctuation_evidence: Optional[bool],
    has_k_driven_three_component_stg: Optional[bool],
) -> bool:
    return (
        not required
        or (
            has_three_component_velocity_write is True
            and has_three_component_fluctuation_evidence is True
            and has_k_driven_three_component_stg is True
        )
    )


def read_probe_counts(path: Optional[Path]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    if not path or not path.exists():
        return None, None, "probe audit CSV not found"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0, 0, "probe audit CSV has no rows"
    failed = 0
    for row in rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            failed += 1
    return len(rows), failed, None


def read_probe_identity_audit(
    probe_path: Optional[Path],
    official_path: Optional[Path],
    case: str = "",
    wind_direction: str = "",
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "valid_count": None,
        "probe_id_column": "",
        "official_id_column": "",
        "missing_probe_id_count": 0,
        "duplicate_probe_id_count": 0,
        "unique_probe_id_count": None,
        "official_row_count": None,
        "official_id_count": None,
        "matched_official_id_count": 0,
        "missing_official_probe_id_count": 0,
        "official_probe_coverage_ratio": None,
        "unmatched_official_id_count": 0,
        "error": None,
    }
    if not probe_path or not probe_path.exists():
        result["error"] = "probe audit CSV not found"
        return result
    with probe_path.open("r", encoding="utf-8-sig", newline="") as handle:
        probe_rows = list(csv.DictReader(handle))
    if not probe_rows:
        result["valid_count"] = 0
        result["error"] = "probe audit CSV has no rows"
        return result

    id_candidates = ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"]
    probe_id_column = find_csv_column(probe_rows, id_candidates)
    result["probe_id_column"] = probe_id_column
    if not probe_id_column:
        result["error"] = "probe_id_column_missing"
        return result

    probe_ids: List[str] = []
    seen = set()
    duplicate_ids = set()
    valid_count = 0
    for row in probe_rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1
        probe_id = str(row.get(probe_id_column) or "").strip()
        if not probe_id:
            result["missing_probe_id_count"] += 1
            continue
        probe_ids.append(probe_id)
        normalized_id = normalized_column_key(probe_id)
        if normalized_id in seen:
            duplicate_ids.add(normalized_id)
        seen.add(normalized_id)

    result["valid_count"] = valid_count
    result["unique_probe_id_count"] = len(seen)
    result["duplicate_probe_id_count"] = len(duplicate_ids)
    if not official_path or not official_path.exists():
        result["error"] = "official measurement CSV not found"
        return result
    with official_path.open("r", encoding="utf-8-sig", newline="") as handle:
        official_rows = list(csv.DictReader(handle))
    if not official_rows:
        result["error"] = "official measurement CSV has no rows"
        return result
    official_rows, official_filter_error = filter_official_identity_rows(official_rows, case, wind_direction)
    result["official_row_count"] = len(official_rows)
    if official_filter_error:
        result["error"] = official_filter_error
        return result
    if not official_rows:
        result["error"] = "official measurement CSV has no matching case/wind rows"
        return result
    official_id_column = find_csv_column(official_rows, id_candidates)
    result["official_id_column"] = official_id_column
    if not official_id_column:
        result["error"] = "official_id_column_missing"
        return result
    official_ids = {
        normalized_column_key(str(row.get(official_id_column) or "").strip())
        for row in official_rows
        if str(row.get(official_id_column) or "").strip()
    }
    result["official_id_count"] = len(official_ids)
    if not official_ids:
        result["error"] = "official_ids_empty"
        return result
    probe_id_set = {normalized_column_key(probe_id) for probe_id in probe_ids}
    matched_official_ids = official_ids & probe_id_set
    result["matched_official_id_count"] = len(matched_official_ids)
    result["missing_official_probe_id_count"] = len(official_ids - probe_id_set)
    result["official_probe_coverage_ratio"] = (
        len(matched_official_ids) / len(official_ids)
        if official_ids
        else None
    )
    result["unmatched_official_id_count"] = sum(
        1
        for probe_id in probe_ids
        if normalized_column_key(probe_id) not in official_ids
    )
    return result


def filter_official_identity_rows(
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
    case: str = "",
    wind_direction: str = "",
) -> Tuple[Dict[str, Tuple[float, float, float]], Optional[str]]:
    if not official_path or not official_path.exists():
        return {}, "official measurement CSV not found"
    with official_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}, "official measurement CSV has no rows"
    rows, filter_error = filter_official_identity_rows(rows, case, wind_direction)
    if filter_error:
        return {}, filter_error
    if not rows:
        return {}, "official measurement CSV has no matching case/wind rows"

    id_candidates = ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"]
    id_column = find_csv_column(rows, id_candidates)
    x_column = find_csv_column(rows, ["x", "X", "x_m", "X_m", "X(m)", "x(m)"])
    y_column = find_csv_column(rows, ["y", "Y", "y_m", "Y_m", "Y(m)", "y(m)"])
    z_column = find_csv_column(rows, ["z", "Z", "z_m", "Z_m", "Z(m)", "z(m)"])
    if not id_column:
        return {}, "official_id_column_missing"
    if not x_column or not y_column or not z_column:
        return {}, "official_coordinate_columns_missing"

    coordinates: Dict[str, Tuple[float, float, float]] = {}
    duplicate_ids = set()
    invalid_coordinate_count = 0
    for row in rows:
        probe_id = normalized_column_key(str(row.get(id_column) or "").strip())
        if not probe_id:
            continue
        x = as_float(row.get(x_column))
        y = as_float(row.get(y_column))
        z = as_float(row.get(z_column))
        if x is None or y is None or z is None:
            invalid_coordinate_count += 1
            continue
        if probe_id in coordinates:
            duplicate_ids.add(probe_id)
        coordinates[probe_id] = (x, y, z)
    if duplicate_ids:
        return {}, "official_duplicate_ids_after_normalization"
    if invalid_coordinate_count:
        return {}, f"official_invalid_coordinate_count:{invalid_coordinate_count}"
    if not coordinates:
        return {}, "official_coordinate_lookup_empty"
    return coordinates, None


def read_probe_component_audit(path: Optional[Path]) -> Tuple[Optional[int], List[str], Optional[int], Optional[str]]:
    if not path or not path.exists():
        return None, [], None, "probe audit CSV not found"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0, [], 0, "probe audit CSV has no rows"
    components = set()
    valid_count = 0
    missing_component_count = 0
    for row in rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1
        component = str(get_any(row, ["compared_component", "ComparedComponent"]) or "").strip().lower()
        if component:
            components.add(component)
        else:
            missing_component_count += 1
    return valid_count, sorted(components), missing_component_count, None


def read_probe_projection_audit(
    path: Optional[Path],
) -> Tuple[Optional[int], Optional[float], Optional[float], int, int, Optional[str]]:
    if not path or not path.exists():
        return None, None, None, 0, 0, "probe audit CSV not found"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0, None, None, 0, 0, "probe audit CSV has no rows"
    valid_count = 0
    distances: List[float] = []
    tolerances: List[float] = []
    missing_distance_count = 0
    missing_tolerance_count = 0
    for row in rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1
        distance = as_float(get_any(row, ["nearest_distance", "NearestDistance", "probe_distance_m", "ProbeDistanceM"]))
        tolerance = as_float(get_any(row, ["tolerance", "Tolerance", "probe_tolerance_m", "ProbeToleranceM"]))
        if distance is None:
            missing_distance_count += 1
        else:
            distances.append(distance)
        if tolerance is None:
            missing_tolerance_count += 1
        else:
            tolerances.append(tolerance)
    return (
        valid_count,
        max(distances) if distances else None,
        max(tolerances) if tolerances else None,
        missing_distance_count,
        missing_tolerance_count,
        None,
    )


def read_probe_coordinate_normalization_audit(
    path: Optional[Path],
    expected_uref: Optional[float],
    uref_tolerance: float,
    expected_wind_vector: Optional[Tuple[float, float, float]],
    wind_vector_tolerance: float,
    official_path: Optional[Path] = None,
    case: str = "",
    wind_direction: str = "",
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "valid_count": None,
        "missing_normalization_count": 0,
        "invalid_normalization_count": 0,
        "missing_wind_direction_count": 0,
        "invalid_wind_direction_count": 0,
        "missing_uref_count": 0,
        "uref_mismatch_count": 0,
        "unique_uref_count": None,
        "max_official_coordinate_delta_m": None,
        "official_coordinate_delta_count": 0,
        "missing_official_coordinate_delta_count": 0,
        "missing_wind_vector_count": 0,
        "wind_vector_mismatch_count": 0,
        "unique_wind_vector_count": None,
        "missing_vtk_grid_extent_count": 0,
        "outside_vtk_grid_extent_count": 0,
        "official_coordinate_recomputed_count": 0,
        "official_coordinate_source": "",
        "official_coordinate_error": None,
        "error": None,
    }
    if not path or not path.exists():
        result["error"] = "probe audit CSV not found"
        return result
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        result["valid_count"] = 0
        result["error"] = "probe audit CSV has no rows"
        return result

    official_coordinates, official_coordinate_error = build_official_coordinate_lookup(
        official_path,
        case,
        wind_direction,
    )
    result["official_coordinate_error"] = official_coordinate_error
    result["official_coordinate_source"] = (
        "current_official_csv_recomputed"
        if official_coordinates
        else "probe_audit_only"
    )

    id_candidates = ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"]
    probe_id_column = find_csv_column(rows, id_candidates)
    valid_count = 0
    urefs: List[float] = []
    wind_vectors: List[Tuple[float, float, float]] = []
    coordinate_deltas: List[float] = []
    for row in rows:
        inside_grid = as_bool(get_any(row, ["inside_vtk_grid_extent", "InsideVtkGridExtent"]))
        if inside_grid is None:
            result["missing_vtk_grid_extent_count"] += 1
        elif inside_grid is False:
            result["outside_vtk_grid_extent_count"] += 1

        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1

        normalization = as_bool(get_any(row, ["normalization_valid", "NormalizationValid"]))
        if normalization is None:
            result["missing_normalization_count"] += 1
        elif normalization is False:
            result["invalid_normalization_count"] += 1

        wind_valid = as_bool(get_any(row, ["wind_direction_valid", "WindDirectionValid"]))
        if wind_valid is None:
            result["missing_wind_direction_count"] += 1
        elif wind_valid is False:
            result["invalid_wind_direction_count"] += 1

        row_uref = as_float(get_any(row, ["Uref", "Uref_mps", "U_ref", "ReferenceWindSpeedMps"]))
        if row_uref is None:
            result["missing_uref_count"] += 1
        else:
            urefs.append(row_uref)
            if expected_uref is not None and abs(row_uref - expected_uref) > uref_tolerance:
                result["uref_mismatch_count"] += 1

        probe_reported_coordinate_delta = as_float(
            get_any(
                row,
                [
                    "official_coordinate_delta",
                    "OfficialCoordinateDelta",
                    "official_coordinate_delta_m",
                    "OfficialCoordinateDeltaM",
                ],
            )
        )
        coordinate_delta = None
        if official_coordinates and probe_id_column:
            probe_id = normalized_column_key(str(row.get(probe_id_column) or "").strip())
            official_coordinate = official_coordinates.get(probe_id)
            if official_coordinate is not None:
                probe_x = as_float(get_any(row, ["x", "X"]))
                probe_y = as_float(get_any(row, ["y", "Y"]))
                probe_z = as_float(get_any(row, ["z", "Z"]))
                if probe_x is not None and probe_y is not None and probe_z is not None:
                    coordinate_delta = max(
                        abs(probe_x - official_coordinate[0]),
                        abs(probe_y - official_coordinate[1]),
                        abs(probe_z - official_coordinate[2]),
                    )
                    result["official_coordinate_recomputed_count"] += 1
        if coordinate_delta is None:
            coordinate_delta = probe_reported_coordinate_delta
        if coordinate_delta is None:
            result["missing_official_coordinate_delta_count"] += 1
        else:
            coordinate_deltas.append(coordinate_delta)

        row_wind = parse_vector(get_any(row, ["wind_vector", "WindVector"]))
        if row_wind is None:
            wx = as_float(get_any(row, ["wind_x", "WindX"]))
            wy = as_float(get_any(row, ["wind_y", "WindY"]))
            wz = as_float(get_any(row, ["wind_z", "WindZ"]))
            if wx is not None and wy is not None and wz is not None:
                row_wind = (wx, wy, wz)
        if row_wind is None:
            result["missing_wind_vector_count"] += 1
        else:
            wind_vectors.append(row_wind)
            delta = vector_delta(row_wind, expected_wind_vector)
            if expected_wind_vector is not None and (delta is None or delta > wind_vector_tolerance):
                result["wind_vector_mismatch_count"] += 1

    result["valid_count"] = valid_count
    result["unique_uref_count"] = len({round(value, 12) for value in urefs})
    result["max_official_coordinate_delta_m"] = max(coordinate_deltas) if coordinate_deltas else None
    result["official_coordinate_delta_count"] = len(coordinate_deltas)
    normalized_winds = [normalize_vector(vector) for vector in wind_vectors]
    result["unique_wind_vector_count"] = len(
        {
            tuple(round(component, 12) for component in vector)
            for vector in normalized_winds
            if vector is not None
        }
    )
    return result


def normalized_hash_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        hashes: List[str] = []
        for item in value:
            hashes.extend(normalized_hash_list(item))
        return hashes
    text = str(value).strip()
    if not text:
        return []
    parts = text.replace(",", ";").replace(" ", ";").split(";")
    return [part.strip().lower() for part in parts if part.strip()]


def runtime_selected_vtk_hashes(
    runtime_audit: Dict[str, Any],
    expected_source_steps_text: str,
) -> Tuple[List[str], str]:
    status = runtime_selected_vtk_hash_status(runtime_audit, None, expected_source_steps_text)
    declared_hashes = status["declared_hashes"]
    return declared_hashes, ";".join(declared_hashes)


def runtime_selected_vtk_hash_status(
    runtime_audit: Dict[str, Any],
    runtime_audit_path: Optional[Path],
    expected_source_steps_text: str,
) -> Dict[str, Any]:
    expected_steps, expected_error = parsed_source_steps(expected_source_steps_text)
    result: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "expected_step_count": len(expected_steps),
        "selected_file_count": 0,
        "path_missing_count": 0,
        "missing_file_count": 0,
        "hash_mismatch_count": 0,
        "declared_hashes": [],
        "declared_hash_text": "",
        "actual_hashes": [],
        "actual_hash_text": "",
        "actual_paths": [],
    }
    if expected_error:
        result["error"] = expected_error
        return result
    records = get_any(
        runtime_audit,
        [
            "freshness_selected_vtk_files",
            "FreshnessSelectedVtkFiles",
            "selected_vtk_files",
            "SelectedVtkFiles",
        ],
    )
    if isinstance(records, list):
        selected: List[Dict[str, Any]] = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            step = as_int(get_any(record, ["time_step", "TimeStep", "step", "Step"]))
            hashes = normalized_hash_list(get_any(record, ["sha256", "Sha256", "SHA256", "hash", "Hash"]))
            declared_path = str(
                get_any(record, ["path", "Path", "file", "File", "filename", "FileName"]) or ""
            ).strip()
            if hashes or declared_path:
                selected.append(
                    {
                        "step": step,
                        "declared_hash": hashes[0] if hashes else "",
                        "index": index,
                        "path": declared_path,
                    }
                )
        if selected:
            expected_step_set = set(expected_steps)
            if expected_step_set and any(item["step"] is not None for item in selected):
                selected = [item for item in selected if item["step"] in expected_step_set]
            if selected and all(item["step"] is not None for item in selected):
                selected = sorted(selected, key=lambda item: int(item["step"]))
            else:
                selected = sorted(selected, key=lambda item: item["index"])
            result["selected_file_count"] = len(selected)
            declared_hashes: List[str] = []
            actual_hashes: List[str] = []
            actual_paths: List[str] = []
            base_dir = runtime_audit_path.parent if runtime_audit_path is not None else None
            for item in selected:
                declared_hash = str(item["declared_hash"]).strip().lower()
                declared_hashes.append(declared_hash)
                declared_path = str(item["path"]).strip()
                if not declared_path:
                    result["path_missing_count"] += 1
                    actual_hashes.append("")
                    actual_paths.append("")
                    continue
                vtk_path = Path(declared_path).expanduser()
                if not vtk_path.is_absolute() and base_dir is not None:
                    vtk_path = base_dir / vtk_path
                vtk_path = vtk_path.resolve()
                if not vtk_path.exists():
                    result["missing_file_count"] += 1
                    actual_hashes.append("")
                    actual_paths.append(str(vtk_path))
                    continue
                actual_hash = sha256_file(vtk_path).lower()
                actual_hashes.append(actual_hash)
                actual_paths.append(str(vtk_path))
                if declared_hash and actual_hash and declared_hash != actual_hash:
                    result["hash_mismatch_count"] += 1
            result["declared_hashes"] = declared_hashes
            result["declared_hash_text"] = ";".join([value for value in declared_hashes if value])
            result["actual_hashes"] = actual_hashes
            result["actual_hash_text"] = ";".join([value for value in actual_hashes if value])
            result["actual_paths"] = actual_paths
            if not selected:
                result["error"] = "runtime_selected_vtk_files_empty_after_step_filter"
            elif not all(declared_hashes):
                result["error"] = "runtime_selected_vtk_sha256_missing"
            elif not all(actual_hashes):
                result["error"] = "runtime_selected_vtk_actual_sha256_missing"
            elif expected_steps and len(declared_hashes) != len(expected_steps):
                result["error"] = "runtime_selected_vtk_count_mismatch"
            elif declared_hashes != actual_hashes:
                result["error"] = "runtime_selected_vtk_sha256_mismatch"
            elif (
                result["path_missing_count"] == 0
                and result["missing_file_count"] == 0
                and result["hash_mismatch_count"] == 0
                and bool(expected_steps)
            ):
                result["ok"] = True
            return result
    fallback_hashes = normalized_hash_list(
        get_any(
            runtime_audit,
            [
                "source_vtk_sha256",
                "SourceVtkSha256",
                "vtk_source_sha256",
                "VtkSourceSha256",
                "selected_vtk_sha256",
                "SelectedVtkSha256",
            ],
        )
    )
    result["declared_hashes"] = fallback_hashes
    result["declared_hash_text"] = ";".join(fallback_hashes)
    result["error"] = "runtime_selected_vtk_files_missing"
    return result


def resolve_audit_path(raw_path: str, audit_path: Optional[Path]) -> Path:
    path = Path(str(raw_path).strip()).expanduser()
    if not path.is_absolute() and audit_path is not None:
        path = audit_path.parent / path
    return path.resolve()


def boundary_evidence_file_hash_status(
    boundary_audit: Dict[str, Any],
    boundary_audit_path: Optional[Path],
) -> Dict[str, Any]:
    raw_files = get_any(
        boundary_audit,
        ["boundary_evidence_files", "BoundaryEvidenceFiles"],
    )
    if isinstance(raw_files, list):
        declared_file_count = len([item for item in raw_files if str(item).strip()])
    else:
        declared_file_text = str(raw_files or "").strip()
        declared_file_count = (
            len([part for part in declared_file_text.replace(";", ",").split(",") if part.strip()])
            if declared_file_text
            else 0
        )

    records = get_any(
        boundary_audit,
        [
            "boundary_evidence_files_sha256",
            "BoundaryEvidenceFilesSha256",
            "boundary_evidence_file_hashes",
            "BoundaryEvidenceFileHashes",
        ],
    )
    result: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "declared_file_count": declared_file_count,
        "hash_record_count": 0,
        "path_missing_count": 0,
        "missing_file_count": 0,
        "declared_hash_missing_count": 0,
        "actual_hash_missing_count": 0,
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "declared_hashes": [],
        "actual_hashes": [],
        "actual_paths": [],
    }
    if not isinstance(records, list) or not records:
        result["error"] = "boundary_evidence_hash_records_missing"
        return result

    result["hash_record_count"] = len(records)
    declared_hashes: List[str] = []
    actual_hashes: List[str] = []
    actual_paths: List[str] = []
    for record in records:
        if not isinstance(record, dict):
            result["path_missing_count"] += 1
            declared_hashes.append("")
            actual_hashes.append("")
            actual_paths.append("")
            continue
        raw_path = str(get_any(record, ["path", "Path", "file", "File"]) or "").strip()
        declared_hash_list = normalized_hash_list(
            get_any(record, ["sha256", "Sha256", "SHA256", "hash", "Hash"])
        )
        declared_hash = declared_hash_list[0] if declared_hash_list else ""
        declared_hashes.append(declared_hash)
        if not declared_hash:
            result["declared_hash_missing_count"] += 1
        if not raw_path:
            result["path_missing_count"] += 1
            actual_hashes.append("")
            actual_paths.append("")
            continue

        evidence_path = resolve_audit_path(raw_path, boundary_audit_path)
        actual_paths.append(str(evidence_path))
        if not evidence_path.exists():
            result["missing_file_count"] += 1
            actual_hashes.append("")
            continue
        actual_hash = sha256_file(evidence_path).lower()
        actual_hashes.append(actual_hash)
        if not actual_hash:
            result["actual_hash_missing_count"] += 1
        elif declared_hash and declared_hash != actual_hash:
            result["hash_mismatch_count"] += 1

        declared_size = as_int(get_any(record, ["size_bytes", "SizeBytes", "bytes", "Bytes"]))
        if declared_size is not None:
            try:
                actual_size = evidence_path.stat().st_size
            except OSError:
                actual_size = None
            if actual_size is None or declared_size != actual_size:
                result["size_mismatch_count"] += 1

    result["declared_hashes"] = declared_hashes
    result["actual_hashes"] = actual_hashes
    result["actual_paths"] = actual_paths
    if declared_file_count and declared_file_count != len(records):
        result["error"] = "boundary_evidence_hash_record_count_mismatch"
    elif result["path_missing_count"]:
        result["error"] = "boundary_evidence_hash_record_path_missing"
    elif result["missing_file_count"]:
        result["error"] = "boundary_evidence_hash_record_file_missing"
    elif result["declared_hash_missing_count"]:
        result["error"] = "boundary_evidence_sha256_missing"
    elif result["actual_hash_missing_count"]:
        result["error"] = "boundary_evidence_actual_sha256_missing"
    elif result["hash_mismatch_count"]:
        result["error"] = "boundary_evidence_sha256_mismatch"
    elif result["size_mismatch_count"]:
        result["error"] = "boundary_evidence_size_mismatch"
    else:
        result["ok"] = True
    return result


def runtime_run_freshness_status(
    runtime_audit: Dict[str, Any],
    runtime_audit_path: Optional[Path],
    runtime_vtk_hash_status: Dict[str, Any],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "reference_file_count": 0,
        "selected_file_count": 0,
        "missing_reference_file_count": 0,
        "missing_selected_file_count": 0,
        "latest_reference_mtime_utc": "",
        "oldest_selected_vtk_mtime_utc": "",
        "stale_selected_vtk_count": 0,
    }
    reference_records = get_any(
        runtime_audit,
        ["freshness_reference_files", "FreshnessReferenceFiles", "reference_files", "ReferenceFiles"],
    )
    reference_paths: List[Path] = []
    if isinstance(reference_records, list):
        for record in reference_records:
            if not isinstance(record, dict):
                continue
            raw_path = str(get_any(record, ["path", "Path", "file", "File"]) or "").strip()
            if raw_path:
                reference_paths.append(resolve_audit_path(raw_path, runtime_audit_path))
    result["reference_file_count"] = len(reference_paths)
    reference_mtimes: List[float] = []
    for path in reference_paths:
        if not path.exists():
            result["missing_reference_file_count"] += 1
            continue
        reference_mtimes.append(path.stat().st_mtime)

    selected_paths = [
        Path(path)
        for path in runtime_vtk_hash_status.get("actual_paths", [])
        if str(path).strip()
    ]
    result["selected_file_count"] = len(selected_paths)
    selected_mtimes: List[float] = []
    for path in selected_paths:
        if not path.exists():
            result["missing_selected_file_count"] += 1
            continue
        selected_mtimes.append(path.stat().st_mtime)

    if reference_mtimes:
        latest_reference = max(reference_mtimes)
        result["latest_reference_mtime_utc"] = datetime.fromtimestamp(latest_reference, timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        latest_reference = None
    if selected_mtimes:
        oldest_selected = min(selected_mtimes)
        result["oldest_selected_vtk_mtime_utc"] = datetime.fromtimestamp(oldest_selected, timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        oldest_selected = None
    if latest_reference is not None and selected_mtimes:
        result["stale_selected_vtk_count"] = sum(1 for mtime in selected_mtimes if mtime < latest_reference)

    if not reference_paths:
        result["error"] = "freshness_reference_files_missing"
    elif not selected_paths:
        result["error"] = "freshness_selected_vtk_files_missing"
    elif result["missing_reference_file_count"]:
        result["error"] = "freshness_reference_file_missing"
    elif result["missing_selected_file_count"]:
        result["error"] = "freshness_selected_vtk_file_missing"
    elif latest_reference is None:
        result["error"] = "freshness_reference_mtime_missing"
    elif oldest_selected is None:
        result["error"] = "freshness_selected_vtk_mtime_missing"
    elif result["stale_selected_vtk_count"]:
        result["error"] = "selected_vtk_older_than_latest_reference"
    else:
        result["ok"] = True
    return result


def normalized_path_list(value: Any) -> List[str]:
    text = str(value or "").strip()
    if not text:
        return []
    if ";" in text:
        return [part.strip() for part in text.split(";") if part.strip()]
    return [text]


def read_probe_source_window_audit(
    path: Optional[Path],
    expected_source_steps_text: str,
    expected_source_hashes: Optional[List[str]] = None,
    min_source_step_span: int = 0,
) -> Dict[str, Any]:
    normalized_expected_hashes = [str(value).strip().lower() for value in (expected_source_hashes or []) if str(value).strip()]
    result: Dict[str, Any] = {
        "valid_count": None,
        "expected_source_steps": expected_source_steps_text,
        "expected_source_hashes": ";".join(normalized_expected_hashes),
        "expected_source_step_span": None,
        "missing_source_steps_count": 0,
        "source_steps_mismatch_count": 0,
        "unique_source_steps_count": None,
        "missing_source_step_span_count": 0,
        "source_step_span_mismatch_count": 0,
        "source_step_span_short_count": 0,
        "missing_minimum_step_span_count": 0,
        "minimum_step_span_mismatch_count": 0,
        "unique_source_step_span_count": None,
        "missing_source_hash_count": 0,
        "source_hash_count_mismatch_count": 0,
        "source_hash_mismatch_count": 0,
        "unique_source_hash_set_count": None,
        "missing_source_files_count": 0,
        "source_file_count_mismatch_count": 0,
        "source_file_missing_count": 0,
        "source_file_hash_mismatch_count": 0,
        "source_file_expected_hash_mismatch_count": 0,
        "unique_source_file_set_count": None,
        "error": None,
    }
    expected_steps, expected_error = parsed_source_steps(expected_source_steps_text)
    if expected_error:
        result["error"] = expected_error
        return result
    expected_source_step_span = expected_steps[-1] - expected_steps[0] if len(expected_steps) >= 2 else None
    result["expected_source_step_span"] = expected_source_step_span
    if not path or not path.exists():
        result["error"] = "probe audit CSV not found"
        return result
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        result["valid_count"] = 0
        result["error"] = "probe audit CSV has no rows"
        return result

    valid_count = 0
    source_step_sets = set()
    source_step_spans = set()
    source_hash_sets = set()
    source_file_sets = set()
    base_dir = path.parent
    for row in rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1
        step_text = str(get_any(row, ["vtk_source_time_steps", "VtkSourceTimeSteps"]) or "").strip()
        if not step_text:
            result["missing_source_steps_count"] += 1
        else:
            row_steps, row_error = parsed_source_steps(step_text)
            if row_error or row_steps != expected_steps:
                result["source_steps_mismatch_count"] += 1
            source_step_sets.add(",".join(str(step) for step in row_steps))
        row_step_span = as_int(get_any(row, ["vtk_source_step_span", "VtkSourceStepSpan"]))
        if row_step_span is None:
            result["missing_source_step_span_count"] += 1
        else:
            source_step_spans.add(row_step_span)
            if expected_source_step_span is not None and row_step_span != expected_source_step_span:
                result["source_step_span_mismatch_count"] += 1
            if min_source_step_span > 0 and row_step_span < min_source_step_span:
                result["source_step_span_short_count"] += 1
        row_min_step_span = as_int(
            get_any(
                row,
                [
                    "minimum_validation_average_step_span",
                    "MinimumValidationAverageStepSpan",
                    "vtk_minimum_validation_average_step_span",
                ],
            )
        )
        if row_min_step_span is None:
            result["missing_minimum_step_span_count"] += 1
        elif min_source_step_span > 0 and row_min_step_span != min_source_step_span:
            result["minimum_step_span_mismatch_count"] += 1

        hash_text = str(get_any(row, ["vtk_source_sha256", "VtkSourceSha256"]) or "").strip()
        hashes = normalized_hash_list(hash_text)
        if not hashes:
            result["missing_source_hash_count"] += 1
        elif step_text and len(hashes) != len(expected_steps):
            result["source_hash_count_mismatch_count"] += 1
        if hashes and normalized_expected_hashes and hashes != normalized_expected_hashes:
            result["source_hash_mismatch_count"] += 1
        if hashes:
            source_hash_sets.add(";".join(hashes))

        source_files = normalized_path_list(get_any(row, ["vtk_source_files", "VtkSourceFiles"]))
        if not source_files:
            result["missing_source_files_count"] += 1
            continue
        if len(source_files) != len(expected_steps):
            result["source_file_count_mismatch_count"] += 1
        resolved_paths: List[Path] = []
        actual_hashes: List[str] = []
        missing_file = False
        for raw_file in source_files:
            source_file = Path(raw_file).expanduser()
            if not source_file.is_absolute():
                source_file = base_dir / source_file
            source_file = source_file.resolve()
            resolved_paths.append(source_file)
            if not source_file.exists():
                result["source_file_missing_count"] += 1
                missing_file = True
                continue
            actual_hashes.append(sha256_file(source_file).lower())
        source_file_sets.add(";".join(str(item) for item in resolved_paths))
        if missing_file:
            continue
        if hashes and actual_hashes != hashes:
            result["source_file_hash_mismatch_count"] += 1
        if normalized_expected_hashes and actual_hashes != normalized_expected_hashes:
            result["source_file_expected_hash_mismatch_count"] += 1

    result["valid_count"] = valid_count
    result["unique_source_steps_count"] = len(source_step_sets)
    result["unique_source_step_span_count"] = len(source_step_spans)
    result["unique_source_hash_set_count"] = len(source_hash_sets)
    result["unique_source_file_set_count"] = len(source_file_sets)
    return result


def source_frame_details(metrics: Dict[str, Any]) -> Tuple[Optional[int], str, bool]:
    source_steps = get_any(metrics, ["source_time_steps", "SourceTimeSteps", "source_steps"])
    if source_steps:
        if isinstance(source_steps, list):
            text = ",".join(str(step) for step in source_steps)
        else:
            text = str(source_steps).strip()
        if not text:
            return None, "", False
        separators = [",", ";", " "]
        parts = [text]
        for sep in separators:
            if sep in text:
                parts = [p for p in text.replace(";", ",").replace(" ", ",").split(",") if p.strip()]
                break
        return len(parts), text, True
    requested = as_int(get_any(metrics, ["averaging_window", "AverageLastN", "average_last_n"]))
    if requested:
        return None, "", False
    return None, "", False


def parsed_source_steps(text: str) -> Tuple[List[int], Optional[str]]:
    if not text.strip():
        return [], "source_time_steps_missing"
    parts = [part for part in text.replace(";", ",").replace(" ", ",").split(",") if part.strip()]
    steps: List[int] = []
    for part in parts:
        value = as_int(part)
        if value is None:
            return [], f"source_time_steps_unparseable:{part}"
        steps.append(value)
    return steps, None


def parsed_step_list_value(value: Any, missing_reason: str) -> Tuple[List[int], Optional[str]]:
    if value is None:
        return [], missing_reason
    if isinstance(value, list):
        text = ",".join(str(item) for item in value)
    else:
        text = str(value).strip()
    if not text:
        return [], missing_reason
    return parsed_source_steps(text)


def requested_vtk_steps_status(
    requested_time_steps: Optional[int],
    requested_vtk_save_interval: Optional[int],
    requested_vtk_save_start_step: Optional[int],
    requested_vtk_frame_count: Optional[int],
    requested_average_last_n: Optional[int],
    selected_source_steps: List[int],
    min_avg_frames: int,
    min_avg_step_span: int,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "recomputed_steps": [],
        "recomputed_steps_csv": "",
        "recomputed_frame_count": None,
        "recomputed_final_window_steps": [],
        "recomputed_final_window_steps_csv": "",
        "recomputed_final_window_step_span": None,
        "declared_frame_count_matches": False,
        "selected_source_matches_final_requested_window": False,
        "selected_source_matches_requested_averaging_window": False,
    }
    reasons: List[str] = []
    if requested_time_steps is None:
        reasons.append("requested_time_steps_missing")
    if requested_vtk_save_interval is None:
        reasons.append("requested_vtk_save_interval_missing")
    elif requested_vtk_save_interval <= 0:
        reasons.append("requested_vtk_save_interval_non_positive")
    if reasons:
        result["error"] = ";".join(reasons)
        return result

    start_step = requested_vtk_save_start_step
    if start_step is None:
        start_step = requested_vtk_save_interval
    if start_step is None:
        reasons.append("requested_vtk_save_start_step_missing")
    elif start_step < 0:
        reasons.append("requested_vtk_save_start_step_negative")
    elif requested_time_steps is not None and start_step > requested_time_steps:
        reasons.append("requested_vtk_save_start_after_time_steps")
    if reasons:
        result["error"] = ";".join(reasons)
        return result

    assert requested_time_steps is not None
    assert requested_vtk_save_interval is not None
    assert start_step is not None
    recomputed_steps = list(range(start_step, requested_time_steps + 1, requested_vtk_save_interval))
    recomputed_count = len(recomputed_steps)
    result["recomputed_steps"] = recomputed_steps
    result["recomputed_steps_csv"] = ",".join(str(step) for step in recomputed_steps)
    result["recomputed_frame_count"] = recomputed_count
    result["declared_frame_count_matches"] = (
        requested_vtk_frame_count is not None and requested_vtk_frame_count == recomputed_count
    )
    final_window_steps: List[int] = []
    if requested_average_last_n is not None and requested_average_last_n > 0:
        final_window_steps = recomputed_steps[-requested_average_last_n:]
    final_window_span = (
        final_window_steps[-1] - final_window_steps[0]
        if len(final_window_steps) >= 2
        else None
    )
    result["recomputed_final_window_steps"] = final_window_steps
    result["recomputed_final_window_steps_csv"] = ",".join(str(step) for step in final_window_steps)
    result["recomputed_final_window_step_span"] = final_window_span
    result["selected_source_matches_final_requested_window"] = (
        bool(selected_source_steps)
        and len(selected_source_steps) <= recomputed_count
        and selected_source_steps == recomputed_steps[-len(selected_source_steps) :]
    )
    result["selected_source_matches_requested_averaging_window"] = (
        bool(selected_source_steps)
        and bool(final_window_steps)
        and selected_source_steps == final_window_steps
    )
    if recomputed_count < min_avg_frames:
        reasons.append(f"recomputed_requested_vtk_frame_count_below_{min_avg_frames}")
    if requested_average_last_n is None:
        reasons.append("requested_averaging_window_missing")
    elif requested_average_last_n <= 0:
        reasons.append("requested_averaging_window_non_positive")
    elif requested_average_last_n < min_avg_frames:
        reasons.append(f"requested_averaging_window_below_{min_avg_frames}")
    if min_avg_step_span > 0:
        if final_window_span is None:
            reasons.append("recomputed_requested_vtk_final_window_step_span_missing")
        elif final_window_span < min_avg_step_span:
            reasons.append(f"recomputed_requested_vtk_final_window_step_span_below_{min_avg_step_span}")
    if not result["declared_frame_count_matches"]:
        reasons.append("requested_vtk_frame_count_mismatch")
    if not result["selected_source_matches_final_requested_window"]:
        reasons.append("selected_source_steps_not_final_requested_window")
    if not result["selected_source_matches_requested_averaging_window"]:
        reasons.append("selected_source_steps_not_requested_averaging_window")
    result["error"] = ";".join(reasons) if reasons else None
    result["ok"] = not reasons
    return result


def strictly_increasing(values: List[int]) -> bool:
    return all(b > a for a, b in zip(values, values[1:]))


def uniformly_spaced(values: List[int]) -> bool:
    if len(values) <= 2:
        return True
    spacing = values[1] - values[0]
    return spacing > 0 and all((b - a) == spacing for a, b in zip(values, values[1:]))


def metrics_time_averaging_consistency_status(
    metrics: Dict[str, Any],
    runtime_audit: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
) -> Dict[str, Any]:
    runtime_frame_count, runtime_source_text, runtime_has_steps = source_frame_details(runtime_audit)
    runtime_steps, runtime_steps_error = parsed_source_steps(runtime_source_text)
    runtime_span = as_int(get_any(runtime_audit, ["source_step_span", "SourceStepSpan"]))
    if runtime_span is None and len(runtime_steps) >= 2:
        runtime_span = runtime_steps[-1] - runtime_steps[0]
    runtime_available_count = as_int(get_any(runtime_audit, ["available_frame_count", "AvailableFrameCount"]))
    runtime_min_step_span = as_int(
        get_any(runtime_audit, ["minimum_validation_average_step_span", "MinimumValidationAverageStepSpan"])
    )
    runtime_time_gate = str(
        get_any(runtime_audit, ["time_averaging_gate", "TimeAveragingGate"]) or ""
    ).strip().lower()
    runtime_selected_last_window = as_bool(
        get_any(runtime_audit, ["selected_last_window", "SelectedLastWindow"])
    )
    runtime_steps_increasing = as_bool(
        get_any(runtime_audit, ["source_steps_strictly_increasing", "SourceStepsStrictlyIncreasing"])
    )
    runtime_spacing_uniform = as_bool(
        get_any(runtime_audit, ["source_step_spacing_uniform", "SourceStepSpacingUniform"])
    )

    metrics_frame_count, metrics_source_text, metrics_has_steps = source_frame_details(metrics)
    metrics_steps, metrics_steps_error = parsed_source_steps(metrics_source_text)
    metrics_averaged_count = as_int(get_any(metrics, ["averaged_frame_count", "AveragedFrameCount"]))
    metrics_available_count = as_int(get_any(metrics, ["available_frame_count", "AvailableFrameCount"]))
    metrics_span = as_int(get_any(metrics, ["source_step_span", "SourceStepSpan"]))
    metrics_min_step_span = as_int(
        get_any(metrics, ["minimum_validation_average_step_span", "MinimumValidationAverageStepSpan"])
    )
    metrics_time_gate = str(
        get_any(metrics, ["time_averaging_gate", "TimeAveragingGate"]) or ""
    ).strip().lower()
    metrics_selected_last_window = as_bool(
        get_any(metrics, ["selected_last_window", "SelectedLastWindow"])
    )
    metrics_steps_increasing = as_bool(
        get_any(metrics, ["source_steps_strictly_increasing", "SourceStepsStrictlyIncreasing"])
    )
    metrics_spacing_uniform = as_bool(
        get_any(metrics, ["source_step_spacing_uniform", "SourceStepSpacingUniform"])
    )

    reasons: List[str] = []
    if not runtime_has_steps:
        reasons.append("runtime_source_time_steps_missing")
    if runtime_steps_error:
        reasons.append(f"runtime_source_time_steps_error:{runtime_steps_error}")
    if runtime_time_gate != "pass":
        reasons.append(f"runtime_time_averaging_gate_not_pass:{runtime_time_gate or 'missing'}")
    if runtime_frame_count is None:
        reasons.append("runtime_frame_count_missing")
    elif runtime_frame_count < min_avg_frames:
        reasons.append(f"runtime_frame_count_below_{min_avg_frames}")
    if runtime_span is None:
        reasons.append("runtime_source_step_span_missing")
    elif runtime_span < min_avg_step_span:
        reasons.append(f"runtime_source_step_span_below_{min_avg_step_span}")
    if runtime_selected_last_window is not True:
        reasons.append(
            "runtime_selected_last_window_missing"
            if runtime_selected_last_window is None
            else "runtime_selected_last_window_not_true"
        )
    if runtime_steps_increasing is not True:
        reasons.append(
            "runtime_source_steps_strictly_increasing_missing"
            if runtime_steps_increasing is None
            else "runtime_source_steps_not_strictly_increasing"
        )
    if runtime_spacing_uniform is not True:
        reasons.append(
            "runtime_source_step_spacing_uniform_missing"
            if runtime_spacing_uniform is None
            else "runtime_source_step_spacing_not_uniform"
        )

    if not metrics_has_steps:
        reasons.append("metrics_source_time_steps_missing")
    if metrics_steps_error:
        reasons.append(f"metrics_source_time_steps_error:{metrics_steps_error}")
    if metrics_time_gate != "pass":
        reasons.append(f"metrics_time_averaging_gate_not_pass:{metrics_time_gate or 'missing'}")
    if metrics_averaged_count is None:
        reasons.append("metrics_averaged_frame_count_missing")
    elif metrics_averaged_count < min_avg_frames:
        reasons.append(f"metrics_averaged_frame_count_below_{min_avg_frames}")
    if metrics_span is None:
        reasons.append("metrics_source_step_span_missing")
    elif metrics_span < min_avg_step_span:
        reasons.append(f"metrics_source_step_span_below_{min_avg_step_span}")
    if metrics_min_step_span is None:
        reasons.append("metrics_minimum_validation_average_step_span_missing")
    elif metrics_min_step_span != min_avg_step_span:
        reasons.append("metrics_minimum_validation_average_step_span_mismatch")
    if metrics_selected_last_window is not True:
        reasons.append(
            "metrics_selected_last_window_missing"
            if metrics_selected_last_window is None
            else "metrics_selected_last_window_not_true"
        )
    if metrics_steps_increasing is not True:
        reasons.append(
            "metrics_source_steps_strictly_increasing_missing"
            if metrics_steps_increasing is None
            else "metrics_source_steps_not_strictly_increasing"
        )
    if metrics_spacing_uniform is not True:
        reasons.append(
            "metrics_source_step_spacing_uniform_missing"
            if metrics_spacing_uniform is None
            else "metrics_source_step_spacing_not_uniform"
        )
    if runtime_min_step_span is not None and metrics_min_step_span is not None and runtime_min_step_span != metrics_min_step_span:
        reasons.append("metrics_runtime_minimum_step_span_mismatch")

    if runtime_steps and metrics_steps and runtime_steps != metrics_steps:
        reasons.append("metrics_source_time_steps_do_not_match_runtime_audit")
    if (
        runtime_frame_count is not None
        and metrics_frame_count is not None
        and metrics_frame_count != runtime_frame_count
    ):
        reasons.append("metrics_source_step_count_does_not_match_runtime_audit")
    if (
        runtime_frame_count is not None
        and metrics_averaged_count is not None
        and metrics_averaged_count != runtime_frame_count
    ):
        reasons.append("metrics_averaged_frame_count_does_not_match_runtime_audit")
    if (
        runtime_available_count is not None
        and metrics_available_count is not None
        and metrics_available_count != runtime_available_count
    ):
        reasons.append("metrics_available_frame_count_does_not_match_runtime_audit")
    if runtime_available_count is not None and metrics_available_count is None:
        reasons.append("metrics_available_frame_count_missing")
    if runtime_span is not None and metrics_span is not None and metrics_span != runtime_span:
        reasons.append("metrics_source_step_span_does_not_match_runtime_audit")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "runtime_frame_count": runtime_frame_count,
        "runtime_available_frame_count": runtime_available_count,
        "runtime_source_time_steps": runtime_source_text,
        "runtime_source_step_span": runtime_span,
        "runtime_minimum_step_span": runtime_min_step_span,
        "runtime_time_averaging_gate": runtime_time_gate,
        "runtime_selected_last_window": runtime_selected_last_window,
        "runtime_source_steps_strictly_increasing": runtime_steps_increasing,
        "runtime_source_step_spacing_uniform": runtime_spacing_uniform,
        "metrics_frame_count": metrics_frame_count,
        "metrics_averaged_frame_count": metrics_averaged_count,
        "metrics_available_frame_count": metrics_available_count,
        "metrics_source_time_steps": metrics_source_text,
        "metrics_source_step_span": metrics_span,
        "metrics_minimum_step_span": metrics_min_step_span,
        "metrics_time_averaging_gate": metrics_time_gate,
        "metrics_selected_last_window": metrics_selected_last_window,
        "metrics_source_steps_strictly_increasing": metrics_steps_increasing,
        "metrics_source_step_spacing_uniform": metrics_spacing_uniform,
    }


def native_inlet_precondition_traceability_status(
    native_preconditions_audit: Dict[str, Any],
    min_avg_step_span: int,
    uref_tolerance: float = 1.0e-6,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_preconditions_audit:
        reasons.append("native_preconditions_audit_missing")

    for key in [
        "inlet_profile_gate",
        "inlet_u_profile_gate",
        "inlet_k_profile_gate",
        "inlet_profile_time_averaging_gate",
        "inlet_correlation_gate",
        "inlet_k_variance_gate",
        "inlet_tke_gate",
    ]:
        value = str(get_any(native_preconditions_audit, [key]) or "").strip().lower()
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")

    for key in [
        "inlet_profile_af_csv_sha256_matches_expected",
        "inlet_profile_source_time_steps_match_runtime",
        "inlet_profile_source_vtk_sha256_match_runtime",
        "inlet_profile_source_step_hash_pairs_match_runtime",
        "inlet_profile_source_steps_strictly_increasing",
        "inlet_profile_source_step_spacing_uniform",
        "inlet_correlation_source_time_steps_match_runtime",
        "inlet_correlation_source_vtk_sha256_match_runtime",
        "inlet_correlation_source_step_hash_pairs_match_runtime",
        "inlet_correlation_source_steps_strictly_increasing",
        "inlet_correlation_source_step_spacing_uniform",
        "inlet_source_has_component_phase_decorrelation",
        "inlet_source_has_temporal_filter_state",
        "inlet_source_has_streamwise_clipping_control",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    for key in [
        "inlet_source_streamwise_clipping_enabled",
        "inlet_source_has_legacy_hardcoded_streamwise_clipping",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not False:
            reasons.append(f"{key}_not_false:{value if value is not None else 'missing'}")

    for key in [
        "paper_grade_inlet_source_gate",
        "inlet_source_distribution_route_gate",
    ]:
        value = str(get_any(native_preconditions_audit, [key]) or "").strip().lower()
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")

    for key in [
        "inlet_source_distribution_consistent",
        "inlet_source_has_distribution_function_write",
        "inlet_source_has_inlet_distribution_reconstruction",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    for key in [
        "inlet_source_velocity_field_only",
        "inlet_source_has_uncorrelated_random_inlet",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not False:
            reasons.append(f"{key}_not_false:{value if value is not None else 'missing'}")

    source_method_class = str(
        get_any(native_preconditions_audit, ["inlet_source_method_class"]) or ""
    ).strip().lower()
    source_fidelity_class = str(
        get_any(native_preconditions_audit, ["inlet_source_turbulent_inflow_fidelity_class"]) or ""
    ).strip().lower()
    source_correlated_velocity_only = as_bool(
        get_any(native_preconditions_audit, ["inlet_source_has_correlated_velocity_field_only"])
    )
    source_uncorrelated_rms_velocity_only = as_bool(
        get_any(native_preconditions_audit, ["inlet_source_has_uncorrelated_rms_velocity_field_only"])
    )
    supported_source_method = any(
        token in source_method_class
        for token in [
            "digital_filter",
            "dfm",
            "sem",
            "synthetic_eddy_distribution_consistent",
            "precursor",
            "recycling_rescaling",
        ]
    ) and not any(
        token in source_method_class
        for token in [
            "diagnostic",
            "velocity_field_only",
            "macroscopic_velocity",
            "stg_lite",
            "stg-lite",
            "uncorrelated",
        ]
    )
    if not source_method_class:
        reasons.append("inlet_source_method_class_missing")
    elif not supported_source_method:
        reasons.append(f"inlet_source_method_class_not_paper_grade:{source_method_class}")
    if source_fidelity_class not in {
        "distribution_consistent_digital_filter",
        "distribution_consistent_synthetic_eddy",
        "distribution_consistent_precursor_or_recycling",
    }:
        reasons.append(
            f"inlet_source_turbulent_inflow_fidelity_class_not_paper_grade:{source_fidelity_class or 'missing'}"
        )
    if source_correlated_velocity_only is not False:
        reasons.append(
            f"inlet_source_has_correlated_velocity_field_only_not_false:"
            f"{source_correlated_velocity_only if source_correlated_velocity_only is not None else 'missing'}"
        )
    if source_uncorrelated_rms_velocity_only is not False:
        reasons.append(
            "inlet_source_has_uncorrelated_rms_velocity_field_only_not_false:"
            f"{source_uncorrelated_rms_velocity_only if source_uncorrelated_rms_velocity_only is not None else 'missing'}"
        )

    inlet_method_text = " ".join(
        str(native_preconditions_audit.get(key) or "").lower()
        for key in [
            "inlet_source_method_class",
            "inlet_synthetic_correlation_model",
            "inlet_source_correlation_model",
            "synthetic_inlet_method",
            "inlet_method_class",
        ]
    )
    planned_synthetic_active = as_bool(
        get_any(native_preconditions_audit, ["planned_synthetic_inlet_sampling_active"])
    )
    planned_synthetic_requested = as_bool(
        get_any(native_preconditions_audit, ["planned_synthetic_inlet_sampling_requested"])
    )
    planned_synthetic_injected = as_bool(
        get_any(native_preconditions_audit, ["planned_synthetic_inlet_sampling_injected"])
    )
    synthetic_sampling_required = (
        "stg" in inlet_method_text
        or "synthetic" in inlet_method_text
        or planned_synthetic_active is True
        or planned_synthetic_requested is True
        or planned_synthetic_injected is True
    )
    if synthetic_sampling_required:
        planned_synthetic_gate = str(
            get_any(native_preconditions_audit, ["planned_synthetic_inlet_sampling_gate"]) or ""
        ).strip().lower()
        if planned_synthetic_gate != "pass":
            reasons.append(
                "planned_synthetic_inlet_sampling_gate_not_pass:"
                f"{planned_synthetic_gate or 'missing'}"
            )
        if planned_synthetic_active is not True:
            reasons.append(
                "planned_synthetic_inlet_sampling_active_not_true:"
                f"{planned_synthetic_active if planned_synthetic_active is not None else 'missing'}"
            )
        refresh_count = as_int(
            get_any(native_preconditions_audit, ["planned_synthetic_inlet_refresh_count"])
        )
        expected_refresh_count = as_int(
            get_any(
                native_preconditions_audit,
                ["planned_synthetic_inlet_metadata_expected_refresh_count"],
            )
        )
        minimum_refresh_count = as_int(
            get_any(native_preconditions_audit, ["planned_synthetic_inlet_minimum_refresh_count"])
        )
        if refresh_count is None:
            reasons.append("planned_synthetic_inlet_refresh_count_missing")
        if minimum_refresh_count is None:
            reasons.append("planned_synthetic_inlet_minimum_refresh_count_missing")
        elif refresh_count is not None and refresh_count < minimum_refresh_count:
            reasons.append(
                "planned_synthetic_inlet_refresh_count_below_minimum:"
                f"{refresh_count}_of_{minimum_refresh_count}"
            )
        if (
            expected_refresh_count is not None
            and refresh_count is not None
            and expected_refresh_count != refresh_count
        ):
            reasons.append(
                "planned_synthetic_inlet_expected_refresh_count_mismatch:"
                f"{expected_refresh_count}!={refresh_count}"
            )

    expected_uref = as_float(get_any(native_preconditions_audit, ["expected_uref_mps"]))
    actual_uref = as_float(get_any(native_preconditions_audit, ["actual_uref_mps"]))
    expected_zref = as_float(get_any(native_preconditions_audit, ["expected_zref_m"]))
    af_uref = as_float(get_any(native_preconditions_audit, ["af_uref_at_zref_mps"]))
    uref_af_delta = as_float(get_any(native_preconditions_audit, ["uref_af_profile_delta_mps"]))
    metadata_uref_af_delta = as_float(
        get_any(native_preconditions_audit, ["metadata_uref_af_profile_delta_mps"])
    )
    for key, value in [
        ("expected_uref_mps", expected_uref),
        ("actual_uref_mps", actual_uref),
        ("expected_zref_m", expected_zref),
        ("af_uref_at_zref_mps", af_uref),
        ("uref_af_profile_delta_mps", uref_af_delta),
        ("metadata_uref_af_profile_delta_mps", metadata_uref_af_delta),
    ]:
        if value is None:
            reasons.append(f"{key}_missing")
    for key, value in [
        ("uref_af_profile_delta_mps", uref_af_delta),
        ("metadata_uref_af_profile_delta_mps", metadata_uref_af_delta),
    ]:
        if value is not None and value > uref_tolerance:
            reasons.append(f"{key}_above_tolerance:{value}")

    for label, span_key, minimum_key in [
        ("inlet_profile", "inlet_profile_source_step_span", "inlet_profile_minimum_step_span"),
        ("inlet_correlation", "inlet_correlation_source_step_span", "inlet_correlation_minimum_step_span"),
    ]:
        span = as_int(get_any(native_preconditions_audit, [span_key]))
        minimum = as_int(get_any(native_preconditions_audit, [minimum_key]))
        if span is None:
            reasons.append(f"{label}_source_step_span_missing")
        elif span < min_avg_step_span:
            reasons.append(f"{label}_source_step_span_below_{min_avg_step_span}")
        if minimum is None:
            reasons.append(f"{label}_minimum_step_span_missing")
        elif minimum < min_avg_step_span:
            reasons.append(f"{label}_minimum_step_span_below_{min_avg_step_span}")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def native_probe_component_traceability_status(
    native_preconditions_audit: Dict[str, Any],
    min_avg_step_span: int,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_preconditions_audit:
        reasons.append("native_preconditions_audit_missing")

    expected_zero_counts = [
        "probe_audit_failed_row_count",
        "probe_missing_id_count",
        "probe_duplicate_id_count",
        "missing_official_probe_id_count",
        "unmatched_probe_id_count",
        "probe_missing_official_coordinate_delta_count",
        "probe_official_coordinate_delta_violation_count",
        "probe_normalization_missing_count",
        "probe_normalization_invalid_count",
        "probe_wind_direction_missing_count",
        "probe_wind_direction_invalid_count",
        "probe_uref_missing_count",
        "probe_uref_mismatch_count",
        "probe_nearest_distance_missing_count",
        "probe_tolerance_missing_or_disabled_count",
        "probe_out_of_tolerance_count",
    ]
    for key in expected_zero_counts:
        value = as_int(get_any(native_preconditions_audit, [key]))
        if value is None:
            reasons.append(f"{key}_missing")
        elif value != 0:
            reasons.append(f"{key}_not_zero:{value}")

    row_count = as_int(get_any(native_preconditions_audit, ["probe_audit_row_count"]))
    valid_row_count = as_int(get_any(native_preconditions_audit, ["probe_audit_valid_row_count"]))
    if row_count is None or row_count <= 0:
        reasons.append("probe_audit_row_count_missing_or_zero")
    if valid_row_count is None or valid_row_count <= 0:
        reasons.append("probe_audit_valid_row_count_missing_or_zero")
    elif row_count is not None and valid_row_count != row_count:
        reasons.append(f"probe_audit_valid_row_count_mismatch:{valid_row_count}_of_{row_count}")

    coverage = as_float(get_any(native_preconditions_audit, ["official_probe_coverage_ratio"]))
    if coverage is None:
        reasons.append("official_probe_coverage_ratio_missing")
    elif abs(coverage - 1.0) > 1.0e-12:
        reasons.append(f"official_probe_coverage_ratio_not_one:{coverage}")
    official_expected_row_count = as_int(get_any(native_preconditions_audit, ["official_expected_row_count"]))
    official_expected_z = str(get_any(native_preconditions_audit, ["official_expected_z_m"]) or "").strip()
    if official_expected_row_count is None:
        reasons.append("official_expected_row_count_missing")
    if not official_expected_z:
        reasons.append("official_expected_z_m_missing")
    official_probe_set_gate = str(get_any(native_preconditions_audit, ["official_probe_set_gate"]) or "").strip().lower()
    if official_probe_set_gate != "pass":
        reasons.append(f"official_probe_set_gate_not_pass:{official_probe_set_gate or 'missing'}")
    probe_official_height_gate = str(
        get_any(native_preconditions_audit, ["probe_official_height_gate"]) or ""
    ).strip().lower()
    if probe_official_height_gate != "pass":
        reasons.append(f"probe_official_height_gate_not_pass:{probe_official_height_gate or 'missing'}")
        for reason in as_string_list(
            get_any(
                native_preconditions_audit,
                ["probe_official_height_gate_reasons", "probe_official_height_gate_reasons_csv"],
            )
        ):
            reasons.append(f"probe_official_height_gate:{reason}")
    official_probe_set_row_count = as_int(get_any(native_preconditions_audit, ["official_probe_set_row_count"]))
    if official_probe_set_row_count is None:
        reasons.append("official_probe_set_row_count_missing")
    elif official_expected_row_count is not None and official_probe_set_row_count != official_expected_row_count:
        reasons.append(
            f"official_probe_set_row_count_mismatch:{official_probe_set_row_count}_of_{official_expected_row_count}"
        )
    official_probe_ids_unique = as_bool(get_any(native_preconditions_audit, ["official_probe_ids_unique"]))
    if official_probe_ids_unique is not True:
        reasons.append(f"official_probe_ids_unique_not_true:{official_probe_ids_unique if official_probe_ids_unique is not None else 'missing'}")
    official_z_mismatch_count = as_int(get_any(native_preconditions_audit, ["official_z_mismatch_count"]))
    if official_z_mismatch_count is None:
        reasons.append("official_z_mismatch_count_missing")
    elif official_z_mismatch_count != 0:
        reasons.append(f"official_z_mismatch_count_not_zero:{official_z_mismatch_count}")
    expected_coordinate_count = None
    for candidate_count in [official_probe_set_row_count, official_expected_row_count, valid_row_count]:
        if candidate_count is not None:
            expected_coordinate_count = candidate_count
            break
    coordinate_delta_count = as_int(
        get_any(native_preconditions_audit, ["probe_official_coordinate_delta_count"])
    )
    coordinate_recomputed_count = as_int(
        get_any(native_preconditions_audit, ["probe_official_coordinate_delta_recomputed_count"])
    )
    coordinate_delta_source = str(
        get_any(native_preconditions_audit, ["probe_official_coordinate_delta_source"]) or ""
    ).strip().lower()
    coordinate_recompute_error = str(
        get_any(native_preconditions_audit, ["probe_official_coordinate_delta_recompute_error"]) or ""
    ).strip()
    max_coordinate_delta = as_float(
        get_any(native_preconditions_audit, ["probe_max_official_coordinate_delta_m"])
    )
    max_coordinate_delta_threshold = as_float(
        get_any(native_preconditions_audit, ["probe_max_official_coordinate_delta_threshold_m"])
    )
    if coordinate_delta_count is None:
        reasons.append("probe_official_coordinate_delta_count_missing")
    elif expected_coordinate_count is not None and coordinate_delta_count != expected_coordinate_count:
        reasons.append(
            "probe_official_coordinate_delta_count_mismatch:"
            f"{coordinate_delta_count}_of_{expected_coordinate_count}"
        )
    if coordinate_delta_source != "current_official_csv_recomputed":
        reasons.append(
            "probe_official_coordinate_delta_source_not_current_official_csv_recomputed:"
            f"{coordinate_delta_source or 'missing'}"
        )
    if coordinate_recomputed_count is None:
        reasons.append("probe_official_coordinate_delta_recomputed_count_missing")
    elif expected_coordinate_count is not None and coordinate_recomputed_count != expected_coordinate_count:
        reasons.append(
            "probe_official_coordinate_delta_recomputed_count_mismatch:"
            f"{coordinate_recomputed_count}_of_{expected_coordinate_count}"
        )
    if coordinate_recompute_error:
        reasons.append(f"probe_official_coordinate_delta_recompute_error_present:{coordinate_recompute_error}")
    if max_coordinate_delta is None:
        reasons.append("probe_max_official_coordinate_delta_m_missing")
    if max_coordinate_delta_threshold is None:
        reasons.append("probe_max_official_coordinate_delta_threshold_m_missing")
    if (
        max_coordinate_delta is not None
        and max_coordinate_delta_threshold is not None
        and max_coordinate_delta > max_coordinate_delta_threshold
    ):
        reasons.append(
            "probe_max_official_coordinate_delta_above_threshold:"
            f"{max_coordinate_delta}>{max_coordinate_delta_threshold}"
        )

    for key in [
        "probe_source_time_steps_match_runtime",
        "probe_source_steps_strictly_increasing",
        "probe_source_step_spacing_uniform",
        "probe_source_step_span_match_runtime",
        "probe_source_vtk_sha256_match_runtime",
        "probe_source_step_hash_pairs_match_runtime",
        "component_source_time_steps_match_runtime",
        "component_source_steps_strictly_increasing",
        "component_source_step_spacing_uniform",
        "component_source_vtk_sha256_match_runtime",
        "component_source_step_hash_pairs_match_runtime",
        "component_sensitivity_probe_audit_sha256_matches_current",
        "component_sensitivity_official_sha256_matches_current",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    for label, key in [
        ("probe", "probe_source_step_span"),
        ("probe_minimum", "probe_minimum_validation_average_step_span"),
        ("component", "component_source_step_span"),
        ("component_minimum", "component_minimum_source_step_span"),
    ]:
        value = as_int(get_any(native_preconditions_audit, [key]))
        if value is None:
            reasons.append(f"{label}_source_step_span_missing")
        elif value < min_avg_step_span:
            reasons.append(f"{label}_source_step_span_below_{min_avg_step_span}")

    for key in [
        "component_normalization_gate",
        "component_sensitivity_gate",
        "normalization_scale_gate",
        "streamwise_sign_gate",
        "component_source_window_gate",
        "component_sensitivity_hash_traceability_gate",
    ]:
        value = str(get_any(native_preconditions_audit, [key]) or "").strip().lower()
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")

    for key in [
        "component_source_time_steps",
        "component_source_sha256",
        "probe_audit_sha256",
        "official_measurement_sha256",
        "component_sensitivity_probe_audit_sha256",
        "component_sensitivity_official_sha256",
    ]:
        value = str(get_any(native_preconditions_audit, [key]) or "").strip()
        if not value:
            reasons.append(f"{key}_missing")

    probe_component_fidelity_class = str(
        get_any(native_preconditions_audit, ["probe_component_fidelity_class"]) or ""
    ).strip().lower()
    if probe_component_fidelity_class != "paper_grade_probe_component_normalization":
        reasons.append(
            "probe_component_fidelity_class_not_paper_grade:"
            f"{probe_component_fidelity_class or 'missing'}"
        )

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "probe_component_fidelity_class": probe_component_fidelity_class,
    }


def native_boundary_traceability_status(
    native_preconditions_audit: Dict[str, Any],
    expected_case: str = "",
    expected_wind_direction: str = "",
    min_avg_frames: int = 40,
    min_avg_step_span: int = 20000,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_preconditions_audit:
        reasons.append("native_preconditions_audit_missing")

    for key in [
        "boundary_source_gate",
        "paper_grade_boundary_source_gate",
        "boundary_protocol_gate",
        "boundary_evidence_gate",
        "boundary_run_identity_gate",
        "boundary_clearance_numeric_gate",
        "boundary_blockage_gate",
        "boundary_runtime_gate",
        "boundary_runtime_traceability_gate",
        "boundary_runtime_profile_preservation_gate",
        "boundary_runtime_inlet_gate",
        "boundary_runtime_side_top_gate",
        "boundary_runtime_side_top_normal_leakage_gate",
        "boundary_runtime_outlet_gate",
    ]:
        value = str(get_any(native_preconditions_audit, [key]) or "").strip().lower()
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")

    for key in [
        "boundary_source_wind_tunnel_equivalent",
        "boundary_source_has_complete_wind_tunnel_evidence",
        "boundary_source_advanced_code_evidence",
        "boundary_source_setup_cpp_sha256_matches_current",
        "boundary_evidence_metadata_sha256_matches_current",
        "boundary_evidence_files_all_hashed",
        "boundary_equivalence_supported",
        "boundary_evidence_class_supported",
        "boundary_condition_fields_supported",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    simplified = as_bool(get_any(native_preconditions_audit, ["boundary_source_simplified"]))
    if simplified is not False:
        reasons.append(
            f"boundary_source_simplified_not_false:{simplified if simplified is not None else 'missing'}"
        )

    source_method_class = str(
        get_any(native_preconditions_audit, ["boundary_source_method_class"]) or ""
    ).strip().lower()
    if source_method_class != "wind_tunnel_equivalent_boundary_source":
        reasons.append(
            f"boundary_source_method_class_not_wind_tunnel_equivalent:{source_method_class or 'missing'}"
        )

    source_fidelity_class = str(
        get_any(native_preconditions_audit, ["boundary_source_fidelity_class"]) or ""
    ).strip().lower()
    if source_fidelity_class != "wind_tunnel_equivalent_complete":
        reasons.append(
            f"boundary_source_fidelity_class_not_paper_grade:{source_fidelity_class or 'missing'}"
        )

    stub_only = as_bool(get_any(native_preconditions_audit, ["boundary_source_has_empty_advanced_method_stub_only"]))
    if stub_only is not False:
        reasons.append(
            f"boundary_source_has_empty_advanced_method_stub_only_not_false:{stub_only if stub_only is not None else 'missing'}"
        )

    for key in [
        "boundary_source_has_paper_grade_outlet_source",
        "boundary_source_has_paper_grade_side_top_source",
        "boundary_source_has_paper_grade_rough_wall_source",
        "boundary_source_has_paper_grade_development_source",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    boundary_runtime_steps, boundary_runtime_steps_error = parsed_step_list_value(
        get_any(native_preconditions_audit, ["boundary_runtime_source_time_steps", "boundary_runtime_source_time_steps_csv"]),
        "boundary_runtime_source_time_steps_missing",
    )
    boundary_runtime_hashes = normalized_hash_list(
        get_any(native_preconditions_audit, ["boundary_runtime_source_vtk_sha256", "boundary_runtime_source_vtk_sha256_csv"])
    )
    boundary_runtime_hash_count = as_int(
        get_any(native_preconditions_audit, ["boundary_runtime_source_vtk_sha256_count"])
    )
    if boundary_runtime_hash_count is None:
        boundary_runtime_hash_count = len(boundary_runtime_hashes) if boundary_runtime_hashes else None
    boundary_runtime_hash_unique_count = as_int(
        get_any(native_preconditions_audit, ["boundary_runtime_source_vtk_sha256_unique_count"])
    )
    if boundary_runtime_hash_unique_count is None:
        boundary_runtime_hash_unique_count = len(set(boundary_runtime_hashes)) if boundary_runtime_hashes else None
    boundary_runtime_frame_count = as_int(get_any(native_preconditions_audit, ["boundary_runtime_frame_count"]))
    boundary_runtime_span = as_int(get_any(native_preconditions_audit, ["boundary_runtime_source_step_span"]))
    boundary_runtime_reported_span = as_int(
        get_any(native_preconditions_audit, ["boundary_runtime_reported_source_step_span"])
    )
    boundary_runtime_selected_last_window = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_selected_last_window"])
    )
    boundary_runtime_steps_increasing = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_source_steps_strictly_increasing"])
    )
    boundary_runtime_steps_uniform = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_source_step_spacing_uniform"])
    )
    boundary_runtime_steps_match_runtime = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_source_time_steps_match_runtime"])
    )
    boundary_runtime_hashes_match_runtime = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_source_vtk_sha256_match_runtime"])
    )
    boundary_runtime_step_hash_pairs_match_runtime = as_bool(
        get_any(native_preconditions_audit, ["boundary_runtime_source_step_hash_pairs_match_runtime"])
    )
    span_from_steps = None
    if boundary_runtime_steps and len(boundary_runtime_steps) >= 2:
        span_from_steps = boundary_runtime_steps[-1] - boundary_runtime_steps[0]
    if boundary_runtime_steps_error:
        reasons.append(f"boundary_runtime_source_time_steps_error:{boundary_runtime_steps_error}")
    if not boundary_runtime_steps:
        reasons.append("boundary_runtime_source_time_steps_missing")
    if boundary_runtime_frame_count is None:
        reasons.append("boundary_runtime_frame_count_missing")
    elif boundary_runtime_frame_count < min_avg_frames:
        reasons.append(f"boundary_runtime_frame_count_below_{min_avg_frames}")
    if boundary_runtime_span is None:
        reasons.append("boundary_runtime_source_step_span_missing")
    elif boundary_runtime_span < min_avg_step_span:
        reasons.append(f"boundary_runtime_source_step_span_below_{min_avg_step_span}")
    if span_from_steps is None:
        reasons.append("boundary_runtime_source_time_steps_span_missing")
    else:
        if boundary_runtime_span is not None and boundary_runtime_span != span_from_steps:
            reasons.append("boundary_runtime_source_step_span_mismatch_time_steps")
        if boundary_runtime_reported_span is not None and boundary_runtime_reported_span != span_from_steps:
            reasons.append("boundary_runtime_reported_source_step_span_mismatch_time_steps")
    if boundary_runtime_selected_last_window is not True:
        reasons.append(
            f"boundary_runtime_selected_last_window_not_true:{boundary_runtime_selected_last_window if boundary_runtime_selected_last_window is not None else 'missing'}"
        )
    if boundary_runtime_steps_increasing is not True:
        reasons.append(
            f"boundary_runtime_source_steps_strictly_increasing_not_true:{boundary_runtime_steps_increasing if boundary_runtime_steps_increasing is not None else 'missing'}"
        )
    if boundary_runtime_steps_uniform is not True:
        reasons.append(
            f"boundary_runtime_source_step_spacing_uniform_not_true:{boundary_runtime_steps_uniform if boundary_runtime_steps_uniform is not None else 'missing'}"
        )
    if boundary_runtime_steps_match_runtime is not True:
        reasons.append(
            f"boundary_runtime_source_time_steps_match_runtime_not_true:{boundary_runtime_steps_match_runtime if boundary_runtime_steps_match_runtime is not None else 'missing'}"
        )
    if boundary_runtime_hashes_match_runtime is not True:
        reasons.append(
            f"boundary_runtime_source_vtk_sha256_match_runtime_not_true:{boundary_runtime_hashes_match_runtime if boundary_runtime_hashes_match_runtime is not None else 'missing'}"
        )
    if boundary_runtime_step_hash_pairs_match_runtime is not True:
        reasons.append(
            f"boundary_runtime_source_step_hash_pairs_match_runtime_not_true:{boundary_runtime_step_hash_pairs_match_runtime if boundary_runtime_step_hash_pairs_match_runtime is not None else 'missing'}"
        )
    if boundary_runtime_hash_count is None:
        reasons.append("boundary_runtime_source_vtk_sha256_count_missing")
    else:
        if boundary_runtime_hash_count < min_avg_frames:
            reasons.append(f"boundary_runtime_source_vtk_sha256_count_below_{min_avg_frames}")
        if boundary_runtime_steps and boundary_runtime_hash_count != len(boundary_runtime_steps):
            reasons.append("boundary_runtime_source_vtk_sha256_count_mismatch_time_steps")
    if boundary_runtime_hash_unique_count is None:
        reasons.append("boundary_runtime_source_vtk_sha256_unique_count_missing")
    elif boundary_runtime_hash_count is not None and boundary_runtime_hash_unique_count != boundary_runtime_hash_count:
        reasons.append("boundary_runtime_source_vtk_sha256_not_unique")
    if boundary_runtime_frame_count is not None and boundary_runtime_steps and boundary_runtime_frame_count != len(boundary_runtime_steps):
        reasons.append("boundary_runtime_frame_count_mismatch_time_steps")

    for key in [
        "boundary_source_missing_paper_grade_source_evidence",
        "boundary_missing_evidence_fields",
        "boundary_unsupported_condition_fields",
        "boundary_evidence_files_missing",
        "boundary_evidence_files_empty",
        "boundary_evidence_files_unreadable",
        "boundary_required_support_fields_missing_or_false",
    ]:
        values = as_string_list(get_any(native_preconditions_audit, [key]))
        if values:
            reasons.append(f"{key}_not_empty:{','.join(values)}")

    evidence_case = str(get_any(native_preconditions_audit, ["boundary_evidence_aij_case"]) or "").strip()
    evidence_wind = str(
        get_any(native_preconditions_audit, ["boundary_evidence_wind_direction"]) or ""
    ).strip()
    if not evidence_case:
        reasons.append("boundary_evidence_aij_case_missing")
    elif expected_case and evidence_case.lower() != expected_case.strip().lower():
        reasons.append(f"boundary_evidence_aij_case_mismatch:{evidence_case}!={expected_case}")
    if not evidence_wind:
        reasons.append("boundary_evidence_wind_direction_missing")
    elif expected_wind_direction and evidence_wind.lower() != expected_wind_direction.strip().lower():
        reasons.append(
            f"boundary_evidence_wind_direction_mismatch:{evidence_wind}!={expected_wind_direction}"
        )

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def native_time_averaging_traceability_status(
    native_preconditions_audit: Dict[str, Any],
    min_avg_frames: int,
    min_avg_step_span: int,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_preconditions_audit:
        reasons.append("native_preconditions_audit_missing")

    time_gate = str(
        get_any(native_preconditions_audit, ["native_preconditions_time_average_gate"]) or ""
    ).strip().lower()
    if time_gate != "pass":
        reasons.append(f"native_preconditions_time_average_gate_not_pass:{time_gate or 'missing'}")
    time_evidence_gate = str(
        get_any(native_preconditions_audit, ["native_preconditions_time_average_evidence_gate"]) or ""
    ).strip().lower()
    runtime_reported_time_gate = str(
        get_any(native_preconditions_audit, ["runtime_reported_time_averaging_gate"]) or ""
    ).strip().lower()
    runtime_time_gate = str(
        get_any(native_preconditions_audit, ["runtime_time_averaging_gate"]) or ""
    ).strip().lower()
    runtime_requested_vtk_frame_gate = str(
        get_any(native_preconditions_audit, ["runtime_requested_vtk_frame_gate"]) or ""
    ).strip().lower()
    runtime_final_window_frame_count_gate = str(
        get_any(native_preconditions_audit, ["runtime_final_window_frame_count_gate"]) or ""
    ).strip().lower()
    for key, value in [
        ("native_preconditions_time_average_evidence_gate", time_evidence_gate),
        ("runtime_reported_time_averaging_gate", runtime_reported_time_gate),
        ("runtime_time_averaging_gate", runtime_time_gate),
        ("runtime_requested_vtk_frame_gate", runtime_requested_vtk_frame_gate),
        ("runtime_final_window_frame_count_gate", runtime_final_window_frame_count_gate),
    ]:
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")
    strict_native_run_gate = str(
        get_any(
            native_preconditions_audit,
            ["strict_native_run_gate", "native_preconditions_strict_native_run_gate"],
        )
        or ""
    ).strip().lower()
    strict_native_run_reasons = as_string_list(
        get_any(
            native_preconditions_audit,
            ["strict_native_run_gate_reasons", "native_preconditions_strict_native_run_gate_reasons"],
        )
    )
    if strict_native_run_gate != "pass":
        reasons.append(f"strict_native_run_gate_not_pass:{strict_native_run_gate or 'missing'}")
    for reason in strict_native_run_reasons:
        if reason and reason != "native_run_artifacts_pass_strict_evidence_gates":
            reasons.append(f"strict_native_run_gate_reason_present:{reason}")

    planned_frame_count = as_int(
        get_any(native_preconditions_audit, ["planned_frame_count_min"])
    )
    runtime_average_last_n = as_int(
        get_any(native_preconditions_audit, ["runtime_average_last_n"])
    )
    runtime_steps_value = get_any(native_preconditions_audit, ["runtime_source_time_steps"])
    runtime_steps, runtime_steps_error = parsed_step_list_value(
        runtime_steps_value,
        "runtime_source_time_steps_missing",
    )
    runtime_frame_count = len(runtime_steps) if runtime_steps else None
    runtime_hashes = normalized_hash_list(
        get_any(
            native_preconditions_audit,
            ["runtime_source_vtk_sha256", "runtime_source_vtk_sha256_csv"],
        )
    )
    runtime_hash_count = as_int(
        get_any(
            native_preconditions_audit,
            ["runtime_source_vtk_sha256_count", "runtime_source_vtk_hash_count"],
        )
    )
    if runtime_hash_count is None:
        runtime_hash_count = len(runtime_hashes) if runtime_hashes else None
    runtime_hash_unique_count = as_int(
        get_any(
            native_preconditions_audit,
            [
                "runtime_source_vtk_sha256_unique_count",
                "runtime_source_vtk_hash_unique_count",
            ],
        )
    )
    if runtime_hash_unique_count is None:
        runtime_hash_unique_count = len(set(runtime_hashes)) if runtime_hashes else None
    runtime_selected_last_window = as_bool(
        get_any(native_preconditions_audit, ["runtime_selected_last_window"])
    )
    runtime_span = as_int(
        get_any(native_preconditions_audit, ["runtime_source_step_span"])
    )
    runtime_span_from_steps = as_int(
        get_any(native_preconditions_audit, ["runtime_source_step_span_from_time_steps"])
    )
    if runtime_span is None and runtime_span_from_steps is not None:
        runtime_span = runtime_span_from_steps
    planned_span = as_int(
        get_any(native_preconditions_audit, ["planned_final_window_step_span"])
    )
    runtime_stationarity_gate = str(
        get_any(native_preconditions_audit, ["runtime_final_window_stationarity_gate"]) or ""
    ).strip().lower()
    time_averaging_fidelity_class = str(
        get_any(native_preconditions_audit, ["time_averaging_fidelity_class"]) or ""
    ).strip().lower()
    runtime_mean_speed_statistics_source = str(
        get_any(
            native_preconditions_audit,
            ["runtime_mean_speed_statistics_source", "mean_speed_statistics_source"],
        )
        or ""
    ).strip().lower()
    runtime_mean_speed_statistics_cli_override = as_bool(
        get_any(
            native_preconditions_audit,
            [
                "runtime_mean_speed_statistics_cli_override",
                "mean_speed_statistics_cli_override",
            ],
        )
    )

    if planned_frame_count is None:
        reasons.append("planned_frame_count_min_missing")
    elif planned_frame_count < min_avg_frames:
        reasons.append(f"planned_frame_count_min_below_{min_avg_frames}")
    if runtime_average_last_n is None:
        reasons.append("runtime_average_last_n_missing")
    elif runtime_average_last_n < min_avg_frames:
        reasons.append(f"runtime_average_last_n_below_{min_avg_frames}")
    if runtime_steps_error:
        reasons.append(f"runtime_source_time_steps_error:{runtime_steps_error}")
    if runtime_frame_count is None:
        reasons.append("runtime_source_frame_count_missing")
    elif runtime_frame_count < min_avg_frames:
        reasons.append(f"runtime_source_frame_count_below_{min_avg_frames}")
    if runtime_selected_last_window is not True:
        reasons.append(
            f"runtime_selected_last_window_not_true:{runtime_selected_last_window if runtime_selected_last_window is not None else 'missing'}"
        )
    if not runtime_hashes:
        reasons.append("runtime_source_vtk_sha256_missing")
    if runtime_hash_count is None:
        reasons.append("runtime_source_vtk_sha256_count_missing")
    else:
        if runtime_hash_count < min_avg_frames:
            reasons.append(f"runtime_source_vtk_sha256_count_below_{min_avg_frames}")
        if runtime_frame_count is not None and runtime_hash_count != runtime_frame_count:
            reasons.append("runtime_source_vtk_sha256_count_mismatch_frame_count")
        if runtime_hashes and runtime_hash_count != len(runtime_hashes):
            reasons.append("runtime_source_vtk_sha256_count_mismatch_hash_list")
    if runtime_hash_unique_count is None:
        reasons.append("runtime_source_vtk_sha256_unique_count_missing")
    elif runtime_hash_count is not None and runtime_hash_unique_count != runtime_hash_count:
        reasons.append("runtime_source_vtk_sha256_unique_count_mismatch_hash_count")
    if runtime_hashes and any(len(value) != 64 for value in runtime_hashes):
        reasons.append("runtime_source_vtk_sha256_not_sha256_length")
    if runtime_span is None:
        reasons.append("runtime_source_step_span_missing")
    elif runtime_span < min_avg_step_span:
        reasons.append(f"runtime_source_step_span_below_{min_avg_step_span}")
    if runtime_span_from_steps is None:
        reasons.append("runtime_source_step_span_from_time_steps_missing")
    elif runtime_span_from_steps < min_avg_step_span:
        reasons.append(f"runtime_source_step_span_from_time_steps_below_{min_avg_step_span}")
    if planned_span is None:
        reasons.append("planned_final_window_step_span_missing")
    elif planned_span < min_avg_step_span:
        reasons.append(f"planned_final_window_step_span_below_{min_avg_step_span}")

    for key in [
        "runtime_source_step_span_matches_time_steps",
        "runtime_source_steps_strictly_increasing",
        "runtime_source_step_spacing_uniform",
    ]:
        value = as_bool(get_any(native_preconditions_audit, [key]))
        if value is not True:
            reasons.append(f"{key}_not_true:{value if value is not None else 'missing'}")

    for key in [
        "planned_frame_count_shortfall_reason",
        "runtime_average_window_shortfall_reason",
        "planned_average_step_span_shortfall_reason",
        "runtime_average_step_span_shortfall_reason",
        "runtime_final_window_stationarity_gate_reasons",
    ]:
        values = as_string_list(get_any(native_preconditions_audit, [key]))
        if values:
            reasons.append(f"{key}_present:{','.join(values)}")
    if runtime_stationarity_gate != "pass":
        reasons.append(f"runtime_final_window_stationarity_gate_not_pass:{runtime_stationarity_gate or 'missing'}")
    if time_averaging_fidelity_class != "paper_grade_final_window_average":
        reasons.append(
            f"time_averaging_fidelity_class_not_paper_grade:{time_averaging_fidelity_class or 'missing'}"
        )
    if runtime_mean_speed_statistics_source != "sampled_vtk":
        reasons.append(
            "runtime_mean_speed_statistics_source_not_sampled_vtk:"
            f"{runtime_mean_speed_statistics_source or 'missing'}"
        )
    if runtime_mean_speed_statistics_cli_override is not False:
        reasons.append(
            "runtime_mean_speed_statistics_cli_override_not_false:"
            f"{runtime_mean_speed_statistics_cli_override if runtime_mean_speed_statistics_cli_override is not None else 'missing'}"
        )

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "planned_frame_count_min": planned_frame_count,
        "runtime_average_last_n": runtime_average_last_n,
        "runtime_source_frame_count": runtime_frame_count,
        "runtime_selected_last_window": runtime_selected_last_window,
        "runtime_source_vtk_sha256_count": runtime_hash_count,
        "runtime_source_vtk_sha256_unique_count": runtime_hash_unique_count,
        "runtime_source_step_span": runtime_span,
        "runtime_source_step_span_from_time_steps": runtime_span_from_steps,
        "runtime_final_window_stationarity_gate": runtime_stationarity_gate,
        "time_averaging_fidelity_class": time_averaging_fidelity_class,
        "native_preconditions_time_average_evidence_gate": time_evidence_gate,
        "runtime_reported_time_averaging_gate": runtime_reported_time_gate,
        "runtime_time_averaging_gate": runtime_time_gate,
        "runtime_requested_vtk_frame_gate": runtime_requested_vtk_frame_gate,
        "runtime_final_window_frame_count_gate": runtime_final_window_frame_count_gate,
        "strict_native_run_gate": strict_native_run_gate,
        "runtime_mean_speed_statistics_source": runtime_mean_speed_statistics_source,
        "runtime_mean_speed_statistics_cli_override": runtime_mean_speed_statistics_cli_override,
        "runtime_final_window_mean_speed_drift_ratio": as_float(
            get_any(native_preconditions_audit, ["runtime_final_window_mean_speed_drift_ratio"])
        ),
        "planned_final_window_step_span": planned_span,
    }


def native_citylbm_parity_critical_status(
    native_citylbm_parity_audit: Dict[str, Any],
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_citylbm_parity_audit:
        reasons.append("native_citylbm_parity_audit_missing")

    declared_gate = str(
        get_any(native_citylbm_parity_audit, ["critical_parity_field_gate"]) or ""
    ).strip().lower()
    if declared_gate != "pass":
        reasons.append(f"critical_parity_field_gate_not_pass:{declared_gate or 'missing'}")

    declared_required_fields = as_string_list(
        get_any(native_citylbm_parity_audit, ["required_critical_fields"])
    )
    if not declared_required_fields:
        reasons.append("required_critical_fields_missing")
    omitted_current_fields = [
        field
        for field in NATIVE_CITYLBM_PARITY_CRITICAL_FIELDS
        if field not in declared_required_fields
    ]
    if omitted_current_fields and declared_required_fields:
        reasons.append(
            "required_critical_fields_omit_current:"
            + ",".join(omitted_current_fields)
        )
    required_fields = list(
        dict.fromkeys(declared_required_fields + list(NATIVE_CITYLBM_PARITY_CRITICAL_FIELDS))
    )
    missing_declared = as_string_list(
        get_any(native_citylbm_parity_audit, ["missing_critical_fields"])
    )
    if missing_declared:
        reasons.append("missing_critical_fields_declared:" + ",".join(missing_declared))

    comparisons = get_any(native_citylbm_parity_audit, ["comparisons"])
    comparison_by_field: Dict[str, Dict[str, Any]] = {}
    if isinstance(comparisons, list):
        for item in comparisons:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "").strip()
            if field:
                comparison_by_field[field] = item
    else:
        reasons.append("comparisons_missing_or_not_list")

    missing_recomputed = [
        field
        for field in required_fields
        if not comparison_by_field.get(field)
        or as_bool(comparison_by_field[field].get("match")) is not True
    ]
    if missing_recomputed:
        reasons.append("missing_critical_fields_recomputed:" + ",".join(missing_recomputed))

    matched_count = as_int(
        get_any(native_citylbm_parity_audit, ["matched_critical_field_count"])
    )
    required_count = as_int(
        get_any(native_citylbm_parity_audit, ["required_critical_field_count"])
    )
    if required_count is None:
        reasons.append("required_critical_field_count_missing")
        required_count = len(required_fields)
    if matched_count is None:
        reasons.append("matched_critical_field_count_missing")
    elif matched_count < required_count:
        reasons.append(f"matched_critical_field_count_below_required:{matched_count}_of_{required_count}")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "required_fields": required_fields,
        "required_field_count": required_count,
        "matched_field_count": matched_count,
        "missing_declared": missing_declared,
        "missing_recomputed": missing_recomputed,
    }


def native_citylbm_accuracy_delta_status(
    native_citylbm_accuracy_delta_audit: Dict[str, Any],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not native_citylbm_accuracy_delta_audit:
        reasons.append("native_citylbm_accuracy_delta_audit_missing")

    declared_gate = str(
        get_any(native_citylbm_accuracy_delta_audit, ["native_citylbm_accuracy_delta_gate"]) or ""
    ).strip().lower()
    if declared_gate != "pass":
        reasons.append(f"native_citylbm_accuracy_delta_gate_not_pass:{declared_gate or 'missing'}")

    additional_error = as_bool(
        get_any(native_citylbm_accuracy_delta_audit, ["citylbm_additional_error_flag"])
    )
    if additional_error is not False:
        reasons.append(
            "citylbm_additional_error_flag_not_false:"
            + ("missing" if additional_error is None else str(additional_error))
        )

    native_accuracy_gate = str(
        get_any(native_citylbm_accuracy_delta_audit, ["native_accuracy_gate"]) or ""
    ).strip().lower()
    if native_accuracy_gate != "pass":
        reasons.append(f"native_accuracy_gate_not_pass:{native_accuracy_gate or 'missing'}")
        for reason in as_string_list(
            get_any(native_citylbm_accuracy_delta_audit, ["native_accuracy_gate_reasons"])
        ):
            if reason and reason != "native_accuracy_metrics_within_thresholds":
                reasons.append(f"native_accuracy_gate_reason:{reason}")

    interpretation = str(
        get_any(native_citylbm_accuracy_delta_audit, ["accuracy_interpretation"]) or ""
    ).strip()
    if not interpretation:
        reasons.append("accuracy_interpretation_missing")

    deltas = {
        "U_RMSE_delta_city_minus_native": as_float(
            get_any(native_citylbm_accuracy_delta_audit, ["U_RMSE_delta_city_minus_native"])
        ),
        "U_abs_bias_delta_city_minus_native": as_float(
            get_any(native_citylbm_accuracy_delta_audit, ["U_abs_bias_delta_city_minus_native"])
        ),
        "U_R2_drop_native_minus_city": as_float(
            get_any(native_citylbm_accuracy_delta_audit, ["U_R2_drop_native_minus_city"])
        ),
        "U_slope_abs_delta": as_float(
            get_any(native_citylbm_accuracy_delta_audit, ["U_slope_abs_delta"])
        ),
        "U_intercept_abs_delta": as_float(
            get_any(native_citylbm_accuracy_delta_audit, ["U_intercept_abs_delta"])
        ),
    }
    thresholds = {
        "U_RMSE_delta_city_minus_native": args.max_native_citylbm_rmse_delta,
        "U_abs_bias_delta_city_minus_native": args.max_native_citylbm_abs_bias_delta,
        "U_R2_drop_native_minus_city": args.max_native_citylbm_r2_drop,
        "U_slope_abs_delta": args.max_native_citylbm_slope_delta,
        "U_intercept_abs_delta": args.max_native_citylbm_intercept_delta,
    }
    reason_names = {
        "U_RMSE_delta_city_minus_native": "citylbm_rmse_regression_delta_above_threshold",
        "U_abs_bias_delta_city_minus_native": "citylbm_abs_bias_regression_delta_above_threshold",
        "U_R2_drop_native_minus_city": "citylbm_r2_drop_above_threshold",
        "U_slope_abs_delta": "citylbm_slope_delta_above_threshold",
        "U_intercept_abs_delta": "citylbm_intercept_delta_above_threshold",
    }
    for field, value in deltas.items():
        if value is None:
            reasons.append(f"{field}_missing")
            continue
        if value > thresholds[field]:
            reasons.append(f"{reason_names[field]}:{value}>{thresholds[field]}")

    return {
        "ok": not reasons,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "declared_gate": declared_gate,
        "native_accuracy_gate": native_accuracy_gate,
        "interpretation": interpretation,
        "citylbm_additional_error_flag": additional_error,
        "deltas": deltas,
        "thresholds": thresholds,
    }


def get_manifest_source_record(manifest: Dict[str, Any], role: str) -> Dict[str, Any]:
    records = manifest.get("RequiredSourceFiles")
    if not isinstance(records, list):
        return {}
    target = role.strip().lower()
    for record in records:
        if not isinstance(record, dict):
            continue
        if str(record.get("Role") or "").strip().lower() == target:
            return record
    return {}


def manifest_source_hash_status(
    manifest: Dict[str, Any],
    role: str,
    manifest_path: Optional[Path],
) -> Dict[str, Any]:
    record = get_manifest_source_record(manifest, role)
    declared_path = str(record.get("Path") or "").strip()
    declared_sha = str(record.get("Sha256") or "").strip().lower()
    hash_algorithm = str(record.get("HashAlgorithm") or "").strip().upper()
    exists_declared = as_bool(record.get("Exists")) is True
    if not record:
        return {
            "role": role,
            "ok": False,
            "reason": "record_missing",
            "declared_path": "",
            "declared_sha256": "",
            "actual_sha256": "",
        }
    if not declared_path:
        return {
            "role": role,
            "ok": False,
            "reason": "path_missing",
            "declared_path": "",
            "declared_sha256": declared_sha,
            "actual_sha256": "",
        }
    source_path = Path(declared_path).expanduser()
    if not source_path.is_absolute() and manifest_path is not None:
        source_path = manifest_path.parent / source_path
    source_path = source_path.resolve()
    actual_sha = sha256_file(source_path).lower()
    ok = (
        exists_declared
        and hash_algorithm == "SHA256"
        and bool(declared_sha)
        and bool(actual_sha)
        and declared_sha == actual_sha
    )
    reasons: List[str] = []
    if not exists_declared:
        reasons.append("manifest_exists_false")
    if hash_algorithm != "SHA256":
        reasons.append("hash_algorithm_not_sha256")
    if not declared_sha:
        reasons.append("declared_sha256_missing")
    if not source_path.exists():
        reasons.append("source_path_missing")
    elif not actual_sha:
        reasons.append("actual_sha256_unavailable")
    elif declared_sha and declared_sha != actual_sha:
        reasons.append("sha256_mismatch")
    return {
        "role": role,
        "ok": ok,
        "reason": "pass" if ok else ",".join(reasons or ["unknown"]),
        "declared_path": str(source_path),
        "declared_sha256": declared_sha,
        "actual_sha256": actual_sha,
    }


def native_manifest_source_root_status(
    manifest: Dict[str, Any],
    manifest_path: Optional[Path],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ok": False,
        "reason": "",
        "source_path": "",
        "source_path_exists": False,
        "has_build_file": False,
        "required_role_path_mismatch_count": 0,
        "missing_required_item_count": 0,
    }
    reasons: List[str] = []
    if not manifest:
        reasons.append("manifest_missing")
        result["reason"] = ";".join(reasons)
        return result

    source_root_text = str(manifest.get("NativeFluidX3DSourcePath") or "").strip()
    if not source_root_text:
        reasons.append("native_source_root_missing")
        result["reason"] = ";".join(reasons)
        return result
    source_root = Path(source_root_text).expanduser()
    if not source_root.is_absolute() and manifest_path is not None:
        source_root = manifest_path.parent / source_root
    source_root = source_root.resolve()
    result["source_path"] = str(source_root)
    result["source_path_exists"] = source_root.exists() and source_root.is_dir()
    if not result["source_path_exists"]:
        reasons.append("native_source_root_not_found")

    source_validation = manifest.get("NativeFluidX3DSourceValidation", {})
    if not isinstance(source_validation, dict):
        source_validation = {}
        reasons.append("native_source_validation_missing")
    if as_bool(source_validation.get("IsValid")) is not True:
        reasons.append("native_source_validation_not_valid")

    has_build_file = any(
        as_bool(source_validation.get(key)) is True
        for key in ["HasSolution", "HasMakefile", "HasCMakeLists"]
    )
    result["has_build_file"] = has_build_file
    if not has_build_file:
        reasons.append("native_source_build_file_missing")

    required_validation_flags = [
        "HasSrcDirectory",
        "HasSetupCpp",
        "HasDefinesHpp",
        "HasLbmHpp",
        "HasLbmCpp",
    ]
    for key in required_validation_flags:
        if as_bool(source_validation.get(key)) is not True:
            reasons.append(f"native_source_validation_flag_false:{key}")

    missing_items = source_validation.get("MissingRequiredItems")
    missing_count = len(missing_items) if isinstance(missing_items, list) else 0
    result["missing_required_item_count"] = missing_count
    if missing_count:
        reasons.append("native_source_validation_missing_items:" + ",".join(str(item) for item in missing_items))

    expected_paths = {
        "Native FluidX3D original setup": source_root / "src" / "setup.cpp",
        "Native FluidX3D original defines": source_root / "src" / "defines.hpp",
        "Native FluidX3D lbm.hpp": source_root / "src" / "lbm.hpp",
        "Native FluidX3D lbm.cpp": source_root / "src" / "lbm.cpp",
    }
    mismatch_count = 0
    for role, expected_path in expected_paths.items():
        record = get_manifest_source_record(manifest, role)
        declared_path_text = str(record.get("Path") or "").strip()
        if not declared_path_text:
            mismatch_count += 1
            reasons.append(f"native_source_role_path_missing:{role}")
            continue
        declared_path = Path(declared_path_text).expanduser()
        if not declared_path.is_absolute() and manifest_path is not None:
            declared_path = manifest_path.parent / declared_path
        declared_path = declared_path.resolve()
        if declared_path != expected_path.resolve():
            mismatch_count += 1
            reasons.append(f"native_source_role_not_under_declared_root:{role}")
    result["required_role_path_mismatch_count"] = mismatch_count
    result["ok"] = not reasons
    result["reason"] = "pass" if result["ok"] else ";".join(reasons)
    return result


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    metadata_path = find_first(run_dir, ["case_metadata.json"])
    audit_path = find_first(run_dir, ["validation_protocol_audit.json"])
    inlet_correlation_audit_path = find_first(run_dir, ["inlet_correlation_audit.json"])
    inlet_profile_audit_path = find_first(run_dir, ["inlet_profile_audit.json"])
    inlet_source_audit_path = find_first(run_dir, ["inlet_source_audit.json"])
    boundary_source_audit_path = find_first(run_dir, ["boundary_source_audit.json"])
    boundary_audit_path = find_first(run_dir, ["boundary_protocol_audit.json"])
    boundary_runtime_audit_path = find_first(run_dir, ["boundary_runtime_audit.json"])
    component_sensitivity_audit_path = find_first(run_dir, ["component_sensitivity_audit.json"])
    grid_sensitivity_audit_path = find_first(run_dir, ["grid_sensitivity_audit.json"])
    native_preconditions_audit_path = find_first(run_dir, ["native_preconditions_audit.json"])
    native_citylbm_parity_audit_path = find_first(run_dir, ["native_citylbm_parity_audit.json"])
    native_citylbm_accuracy_delta_audit_path = find_first(run_dir, ["native_citylbm_accuracy_delta_audit.json"])
    setup_cpp_path = find_first(run_dir, ["setup.cpp"])
    runtime_audit_path = find_first(
        run_dir,
        [
            "native_run_audit.json",
            "read_vtk_audit.json",
            "read_vtk_averaging_audit.json",
            "averaging_audit.json",
            "ReadVTK_AveragingAudit.json",
        ],
    )
    manifest_path = find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metrics_path = Path(args.metrics).resolve() if args.metrics else find_metrics(run_dir)
    probe_path = Path(args.probe_audit).resolve() if args.probe_audit else None
    official_path = Path(args.official).resolve() if args.official else None

    metadata = read_json(metadata_path)
    audit = read_json(audit_path)
    inlet_correlation_audit = read_json(inlet_correlation_audit_path)
    inlet_profile_audit = read_json(inlet_profile_audit_path)
    inlet_source_audit = read_json(inlet_source_audit_path)
    boundary_source_audit = read_json(boundary_source_audit_path)
    external_boundary_audit = read_json(boundary_audit_path)
    boundary_runtime_audit = read_json(boundary_runtime_audit_path)
    component_sensitivity_audit = read_json(component_sensitivity_audit_path)
    grid_sensitivity_audit = read_json(grid_sensitivity_audit_path)
    native_preconditions_audit = read_json(native_preconditions_audit_path)
    native_citylbm_parity_audit = read_json(native_citylbm_parity_audit_path)
    native_citylbm_accuracy_delta_audit = read_json(native_citylbm_accuracy_delta_audit_path)
    runtime_audit = read_json(runtime_audit_path)
    manifest = read_json(manifest_path)
    metrics, metrics_path = read_metrics(metrics_path)
    items = load_protocol_items(audit)
    protocol_content = audit_protocol_content(audit)
    shared_run_conditions = manifest.get("SharedRunConditions", {})
    if not isinstance(shared_run_conditions, dict):
        shared_run_conditions = {}
    software_label = str(args.software or get_any(metrics, ["software", "Software"]) or "").strip().lower()
    citylbm_result = "citylbm" in software_label and "native" not in software_label
    gates: List[Dict[str, Any]] = []
    current_setup_cpp_sha256 = sha256_file(setup_cpp_path).lower()
    current_probe_audit_sha256 = sha256_file(probe_path)
    current_official_sha256 = sha256_file(official_path)

    add_gate(
        gates,
        "artifact_presence",
        PASS
        if metadata_path
        and audit_path
        and inlet_profile_audit_path
        and inlet_correlation_audit_path
        and inlet_source_audit_path
        and boundary_source_audit_path
        and boundary_audit_path
        and boundary_runtime_audit_path
        and runtime_audit_path
        and grid_sensitivity_audit_path
        and native_preconditions_audit_path
        and (native_citylbm_parity_audit_path or not citylbm_result)
        and (native_citylbm_accuracy_delta_audit_path or not citylbm_result)
        and metrics_path
        and metrics
        else FAIL,
        (
            f"metadata={metadata_path or 'missing'}; audit={audit_path or 'missing'}; "
            f"inlet_profile_audit={inlet_profile_audit_path or 'missing'}; "
            f"inlet_correlation_audit={inlet_correlation_audit_path or 'missing'}; "
            f"inlet_source_audit={inlet_source_audit_path or 'missing'}; "
            f"boundary_source_audit={boundary_source_audit_path or 'missing'}; "
            f"boundary_audit={boundary_audit_path or 'missing'}; "
            f"boundary_runtime_audit={boundary_runtime_audit_path or 'missing'}; "
            f"runtime_audit={runtime_audit_path or 'missing'}; "
            f"grid_sensitivity_audit={grid_sensitivity_audit_path or 'missing'}; "
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"native_citylbm_parity_audit={native_citylbm_parity_audit_path or ('missing' if citylbm_result else ('not_required_for_' + (software_label or 'unknown')))}; "
            f"native_citylbm_accuracy_delta_audit={native_citylbm_accuracy_delta_audit_path or ('missing' if citylbm_result else ('not_required_for_' + (software_label or 'unknown')))}; "
            f"metrics={metrics_path or 'missing'}"
        ),
        "Archive case_metadata.json, validation_protocol_audit.json, inlet_profile_audit.json, inlet_correlation_audit.json, inlet_source_audit.json, boundary_source_audit.json, boundary_protocol_audit.json, boundary_runtime_audit.json, native_run_audit/read_vtk_audit JSON, native_preconditions_audit.json, grid_sensitivity_audit.json and metrics CSV/JSON for every run; CityLBM accuracy claims also require native_citylbm_parity_audit.json and native_citylbm_accuracy_delta_audit.json.",
    )
    add_gate(
        gates,
        "validation_protocol_content",
        PASS if protocol_content["ok"] else FAIL,
        (
            f"audit={audit_path or 'missing'}; "
            f"audit_gate={protocol_content['audit_gate'] or 'missing'}; "
            f"item_count={protocol_content['item_count']}; "
            f"required_item_count={protocol_content['required_item_count']}; "
            f"missing_keys={';'.join(protocol_content['missing_keys']) or 'none'}; "
            f"missing_status_keys={';'.join(protocol_content['missing_status_keys']) or 'none'}; "
            f"failed_keys={';'.join(protocol_content['failed_keys']) or 'none'}; "
            f"risk_keys={';'.join(protocol_content['risk_keys']) or 'none'}; "
            f"partial_keys={';'.join(protocol_content['partial_keys']) or 'none'}"
        ),
        "Regenerate validation_protocol_audit.json from the current case until all required protocol items are present with explicit statuses and no item is marked fail.",
    )

    metrics_probe_audit_sha256 = str(
        get_any(metrics, ["probe_mapping_table_sha256", "ProbeMappingTableSha256"]) or ""
    ).strip().lower()
    metrics_official_sha256 = str(
        get_any(metrics, ["official_measurement_sha256", "OfficialMeasurementSha256"]) or ""
    ).strip().lower()
    metrics_probe_hash_matches = (
        bool(current_probe_audit_sha256)
        and bool(metrics_probe_audit_sha256)
        and metrics_probe_audit_sha256 == current_probe_audit_sha256.lower()
    )
    metrics_official_hash_matches = (
        bool(current_official_sha256)
        and bool(metrics_official_sha256)
        and metrics_official_sha256 == current_official_sha256.lower()
    )
    add_gate(
        gates,
        "metrics_input_hash_traceability",
        PASS if metrics_probe_hash_matches and metrics_official_hash_matches else FAIL,
        (
            f"metrics_probe_mapping_table_sha256={metrics_probe_audit_sha256 or 'missing'}; "
            f"current_probe_audit_sha256={current_probe_audit_sha256 or 'missing'}; "
            f"metrics_probe_hash_matches={metrics_probe_hash_matches}; "
            f"metrics_official_measurement_sha256={metrics_official_sha256 or 'missing'}; "
            f"current_official_sha256={current_official_sha256 or 'missing'}; "
            f"metrics_official_hash_matches={metrics_official_hash_matches}"
        ),
        "Rebuild validation_metrics.csv from the current probe_audit.csv and official RS/measurement CSV before interpreting coordinate, component, Uref or bias diagnostics.",
    )

    frame_count, source_step_text, has_real_source_steps = source_frame_details(runtime_audit)
    runtime_vtk_hash_status = runtime_selected_vtk_hash_status(runtime_audit, runtime_audit_path, source_step_text)
    runtime_freshness_status = runtime_run_freshness_status(
        runtime_audit,
        runtime_audit_path,
        runtime_vtk_hash_status,
    )
    run_freshness_gate = str(
        get_any(runtime_audit, ["run_freshness_gate", "RunFreshnessGate"]) or ""
    ).strip().lower()
    run_freshness_reasons = str(
        get_any(runtime_audit, ["run_freshness_gate_reasons_csv", "RunFreshnessGateReasonsCsv"])
        or get_any(runtime_audit, ["run_freshness_gate_reasons", "RunFreshnessGateReasons"])
        or ""
    ).strip()
    latest_reference_mtime = str(
        get_any(runtime_audit, ["latest_reference_mtime_utc", "LatestReferenceMtimeUtc"]) or ""
    ).strip()
    oldest_selected_vtk_mtime = str(
        get_any(runtime_audit, ["oldest_selected_vtk_mtime_utc", "OldestSelectedVtkMtimeUtc"]) or ""
    ).strip()
    run_freshness_ok = (
        run_freshness_gate == "pass"
        and bool(latest_reference_mtime)
        and bool(oldest_selected_vtk_mtime)
        and runtime_freshness_status["ok"]
    )
    add_gate(
        gates,
        "run_freshness",
        PASS if run_freshness_ok else FAIL,
        (
            f"run_freshness_gate={run_freshness_gate or 'missing'}; "
            f"latest_reference_mtime_utc={latest_reference_mtime or 'missing'}; "
            f"oldest_selected_vtk_mtime_utc={oldest_selected_vtk_mtime or 'missing'}; "
            f"actual_latest_reference_mtime_utc={runtime_freshness_status['latest_reference_mtime_utc'] or 'missing'}; "
            f"actual_oldest_selected_vtk_mtime_utc={runtime_freshness_status['oldest_selected_vtk_mtime_utc'] or 'missing'}; "
            f"freshness_reference_file_count={runtime_freshness_status['reference_file_count']}; "
            f"freshness_selected_file_count={runtime_freshness_status['selected_file_count']}; "
            f"missing_reference_file_count={runtime_freshness_status['missing_reference_file_count']}; "
            f"missing_selected_file_count={runtime_freshness_status['missing_selected_file_count']}; "
            f"stale_selected_vtk_count={runtime_freshness_status['stale_selected_vtk_count']}; "
            f"freshness_recompute_error={runtime_freshness_status['error'] or 'none'}; "
            f"run_freshness_gate_reasons={run_freshness_reasons or 'none'}; "
            f"metrics_run_freshness_gate={get_any(metrics, ['run_freshness_gate', 'RunFreshnessGate']) or 'ignored'}; "
            f"runtime_audit={runtime_audit_path or 'missing'}"
        ),
        "Regenerate VTK after the current setup.cpp/defines/buildings/metadata inputs and archive the native run audit proving selected VTK frames are newer than the run-definition artifacts.",
    )

    frame_count, source_step_text, has_real_source_steps = source_frame_details(runtime_audit)
    requested_avg_window = as_int(
        get_any(runtime_audit, ["average_last_n_requested", "AverageLastNRequested", "averaging_window", "AverageLastN", "average_last_n"])
    )
    expected_vtk_frame_count = as_int(metadata.get("ExpectedVtkFrameCount"))
    requested_time_steps = as_int(get_any(runtime_audit, ["requested_time_steps", "RequestedTimeSteps"]))
    requested_vtk_save_interval = as_int(get_any(runtime_audit, ["requested_vtk_save_interval", "RequestedVtkSaveInterval"]))
    requested_vtk_save_start_step = as_int(get_any(runtime_audit, ["requested_vtk_save_start_step", "RequestedVtkSaveStartStep"]))
    requested_vtk_frame_count = as_int(get_any(runtime_audit, ["requested_vtk_frame_count", "RequestedVtkFrameCount"]))
    requested_vtk_frame_gate = str(get_any(runtime_audit, ["requested_vtk_frame_gate", "RequestedVtkFrameGate"]) or "").strip().lower()
    requested_vtk_frame_gate_reasons = str(get_any(runtime_audit, ["requested_vtk_frame_gate_reasons_csv", "RequestedVtkFrameGateReasonsCsv", "requested_vtk_frame_gate_reasons", "RequestedVtkFrameGateReasons"]) or "").strip()
    if has_real_source_steps:
        frame_source = "runtime_audit real source_time_steps"
    else:
        frame_source = "missing runtime_audit real source_time_steps"
    available_frame_count = as_int(get_any(runtime_audit, ["available_frame_count", "AvailableFrameCount"]))
    runtime_vtk_pattern = str(get_any(runtime_audit, ["vtk_pattern", "VtkPattern"]) or "").strip()
    expected_vtk_pattern = str(args.expected_vtk_pattern or "").strip()
    vtk_pattern_ok = bool(runtime_vtk_pattern) and (
        not expected_vtk_pattern or runtime_vtk_pattern == expected_vtk_pattern
    )
    source_first_step = as_int(get_any(runtime_audit, ["source_first_time_step", "SourceFirstTimeStep"]))
    source_last_step = as_int(get_any(runtime_audit, ["source_last_time_step", "SourceLastTimeStep"]))
    declared_source_step_span = as_int(get_any(runtime_audit, ["source_step_span", "SourceStepSpan"]))
    latest_available_step = as_int(get_any(runtime_audit, ["latest_available_time_step", "LatestAvailableTimeStep"]))
    selected_last_window = as_bool(get_any(runtime_audit, ["selected_last_window", "SelectedLastWindow"]))
    source_steps_increasing = as_bool(get_any(runtime_audit, ["source_steps_strictly_increasing", "SourceStepsStrictlyIncreasing"]))
    source_spacing_uniform = as_bool(get_any(runtime_audit, ["source_step_spacing_uniform", "SourceStepSpacingUniform"]))
    parsed_steps, parsed_steps_error = parsed_source_steps(source_step_text)
    parsed_frame_count = len(parsed_steps) if parsed_steps else None
    parsed_first_step = parsed_steps[0] if parsed_steps else None
    parsed_last_step = parsed_steps[-1] if parsed_steps else None
    parsed_steps_increasing = strictly_increasing(parsed_steps) if parsed_steps else False
    parsed_spacing_uniform = uniformly_spaced(parsed_steps) if parsed_steps else False
    all_available_steps_value = get_first_available(
        get_any(runtime_audit, ["all_available_time_steps_csv", "AllAvailableTimeStepsCsv"]),
        get_any(runtime_audit, ["all_available_time_steps", "AllAvailableTimeSteps"]),
    )
    all_available_steps, all_available_steps_error = parsed_step_list_value(
        all_available_steps_value,
        "all_available_time_steps_missing",
    )
    all_available_steps_increasing = strictly_increasing(all_available_steps) if all_available_steps else False
    all_available_steps_uniform = uniformly_spaced(all_available_steps) if all_available_steps else False
    recomputed_available_count_matches = (
        available_frame_count is not None
        and bool(all_available_steps)
        and available_frame_count == len(all_available_steps)
    )
    recomputed_selected_last_window = (
        bool(parsed_steps)
        and bool(all_available_steps)
        and len(parsed_steps) <= len(all_available_steps)
        and parsed_steps == all_available_steps[-len(parsed_steps) :]
    )
    requested_vtk_step_status = requested_vtk_steps_status(
        requested_time_steps,
        requested_vtk_save_interval,
        requested_vtk_save_start_step,
        requested_vtk_frame_count,
        requested_avg_window,
        parsed_steps,
        args.min_avg_frames,
        args.min_avg_step_span,
    )
    metadata_paper_averaging_status = declared_paper_averaging_status(
        metadata,
        args.min_avg_frames,
        args.min_avg_step_span,
        require_gate=True,
    )
    manifest_paper_averaging_status = declared_paper_averaging_status(
        shared_run_conditions,
        args.min_avg_frames,
        args.min_avg_step_span,
        require_gate=False,
    )
    runtime_vtk_hash_status = runtime_selected_vtk_hash_status(runtime_audit, runtime_audit_path, source_step_text)
    expected_source_hashes = (
        runtime_vtk_hash_status["actual_hashes"] if runtime_vtk_hash_status["ok"] else []
    )
    expected_source_hash_text = runtime_vtk_hash_status["actual_hash_text"]
    add_gate(
        gates,
        "runtime_vtk_hash_traceability",
        PASS if runtime_vtk_hash_status["ok"] else FAIL,
        (
            f"selected_file_count={runtime_vtk_hash_status['selected_file_count']}; "
            f"expected_step_count={runtime_vtk_hash_status['expected_step_count']}; "
            f"path_missing_count={runtime_vtk_hash_status['path_missing_count']}; "
            f"missing_file_count={runtime_vtk_hash_status['missing_file_count']}; "
            f"hash_mismatch_count={runtime_vtk_hash_status['hash_mismatch_count']}; "
            f"declared_hashes={runtime_vtk_hash_status['declared_hash_text'] or 'missing'}; "
            f"actual_hashes={runtime_vtk_hash_status['actual_hash_text'] or 'missing'}; "
            f"error={runtime_vtk_hash_status['error'] or 'none'}; "
            f"runtime_audit={runtime_audit_path or 'missing'}"
        ),
        "Regenerate the runtime audit from current selected VTK files and keep those files in the archived run package; JSON-declared VTK hashes alone are not accepted.",
    )
    source_step_count_matches = parsed_frame_count is not None and frame_count == parsed_frame_count
    source_first_matches = source_first_step is None or source_first_step == parsed_first_step
    source_last_matches = source_last_step is None or source_last_step == parsed_last_step
    computed_source_step_span = (
        parsed_last_step - parsed_first_step
        if parsed_first_step is not None and parsed_last_step is not None
        else None
    )
    source_step_span_matches = (
        declared_source_step_span is not None
        and computed_source_step_span is not None
        and declared_source_step_span == computed_source_step_span
    )
    source_step_span_long_enough = (
        computed_source_step_span is not None
        and computed_source_step_span >= args.min_avg_step_span
    )
    available_covers_source_window = (
        available_frame_count is not None
        and parsed_frame_count is not None
        and available_frame_count >= parsed_frame_count
    )
    runtime_time_gate = str(get_any(runtime_audit, ["time_averaging_gate", "TimeAveragingGate"]) or "").strip().lower()
    runtime_time_gate_reasons = str(get_any(runtime_audit, ["time_averaging_gate_reasons_csv", "TimeAveragingGateReasonsCsv", "time_averaging_gate_reasons", "TimeAveragingGateReasons"]) or "").strip()
    mean_speed_stddev_ratio = as_float(get_any(runtime_audit, ["mean_speed_stddev_ratio", "MeanSpeedStdDevRatio"]))
    max_speed_stddev_ratio = as_float(get_any(runtime_audit, ["max_speed_stddev_ratio", "MaxSpeedStdDevRatio"]))
    mean_speed_statistics_source = str(
        get_any(runtime_audit, ["mean_speed_statistics_source", "MeanSpeedStatisticsSource"]) or ""
    ).strip().lower()
    speed_statistics_source_ok = mean_speed_statistics_source in {
        "sampled_vtk",
        "vtk_sampled",
        "read_vtk_audit",
        "native_run_audit",
        "inlet_profile_audit",
    }
    mean_speed_stable = (
        mean_speed_stddev_ratio is not None
        and mean_speed_stddev_ratio <= args.max_mean_speed_stddev_ratio
    )
    point_speed_stable = (
        max_speed_stddev_ratio is not None
        and max_speed_stddev_ratio <= args.max_point_speed_stddev_ratio
    )
    time_window_ok = (
        has_real_source_steps
        and frame_count is not None
        and frame_count >= args.min_avg_frames
        and parsed_steps_error is None
        and source_step_count_matches
        and parsed_steps_increasing
        and parsed_spacing_uniform
        and source_first_matches
        and source_last_matches
        and source_step_span_matches
        and source_step_span_long_enough
        and available_covers_source_window
        and all_available_steps_error is None
        and all_available_steps_increasing
        and all_available_steps_uniform
        and recomputed_available_count_matches
        and recomputed_selected_last_window
        and selected_last_window is True
        and source_steps_increasing is True
        and source_spacing_uniform is True
        and source_last_step is not None
        and latest_available_step is not None
        and source_last_step == latest_available_step
        and runtime_time_gate == "pass"
        and requested_vtk_frame_gate == "pass"
        and requested_vtk_frame_count is not None
        and requested_vtk_frame_count >= args.min_avg_frames
        and requested_vtk_step_status["ok"]
        and metadata_paper_averaging_status["ok"]
        and manifest_paper_averaging_status["ok"]
        and vtk_pattern_ok
        and speed_statistics_source_ok
        and mean_speed_stable
        and point_speed_stable
    )
    add_gate(
        gates,
        "time_averaging",
        PASS if time_window_ok else FAIL,
        (
            f"{frame_source}: {frame_count}; required >= {args.min_avg_frames}; "
            f"real_source_time_steps_present={has_real_source_steps}; "
            f"source_time_steps={source_step_text or 'missing'}; "
            f"parsed_source_step_count={parsed_frame_count}; source_step_count_matches={source_step_count_matches}; "
            f"parsed_first_step={parsed_first_step}; parsed_last_step={parsed_last_step}; "
            f"source_first_matches={source_first_matches}; source_last_matches={source_last_matches}; "
            f"declared_source_step_span={declared_source_step_span}; computed_source_step_span={computed_source_step_span}; "
            f"source_step_span_matches={source_step_span_matches}; "
            f"source_step_span_long_enough={source_step_span_long_enough}; required >= {args.min_avg_step_span}; "
            f"parsed_steps_strictly_increasing={parsed_steps_increasing}; "
            f"parsed_step_spacing_uniform={parsed_spacing_uniform}; "
            f"available_covers_source_window={available_covers_source_window}; "
            f"parsed_source_steps_error={parsed_steps_error or 'none'}; "
            f"all_available_time_steps={str(all_available_steps_value or '').strip() or 'missing'}; "
            f"all_available_time_steps_error={all_available_steps_error or 'none'}; "
            f"all_available_steps_strictly_increasing={all_available_steps_increasing}; "
            f"all_available_steps_uniform={all_available_steps_uniform}; "
            f"recomputed_available_count_matches={recomputed_available_count_matches}; "
            f"recomputed_selected_last_window={recomputed_selected_last_window}; "
            f"requested_averaging_window={requested_avg_window}; "
            f"requested_time_steps={requested_time_steps}; "
            f"requested_vtk_save_interval={requested_vtk_save_interval}; "
            f"requested_vtk_save_start_step={requested_vtk_save_start_step}; "
            f"requested_vtk_frame_count={requested_vtk_frame_count}; required >= {args.min_avg_frames}; "
            f"recomputed_requested_vtk_frame_count={requested_vtk_step_status['recomputed_frame_count']}; "
            f"recomputed_requested_vtk_final_window_steps={requested_vtk_step_status['recomputed_final_window_steps_csv'] or 'missing'}; "
            f"recomputed_requested_vtk_final_window_step_span={requested_vtk_step_status['recomputed_final_window_step_span']}; "
            f"requested_vtk_final_window_step_span_required >= {args.min_avg_step_span}; "
            f"requested_vtk_declared_frame_count_matches={requested_vtk_step_status['declared_frame_count_matches']}; "
            f"requested_vtk_selected_source_matches_final_window={requested_vtk_step_status['selected_source_matches_final_requested_window']}; "
            f"requested_vtk_selected_source_matches_requested_averaging_window={requested_vtk_step_status['selected_source_matches_requested_averaging_window']}; "
            f"requested_vtk_recompute_error={requested_vtk_step_status['error'] or 'none'}; "
            f"metadata_expected_vtk_frame_count={metadata_paper_averaging_status['expected_vtk_frame_count']}; "
            f"metadata_paper_recommended_averaging_frames={metadata_paper_averaging_status['paper_recommended_averaging_frames']}; "
            f"metadata_paper_recommended_average_step_span={metadata_paper_averaging_status['paper_recommended_average_step_span']}; "
            f"metadata_expected_paper_average_step_span={metadata_paper_averaging_status['expected_paper_average_step_span']}; "
            f"metadata_time_averaging_paper_gate={metadata_paper_averaging_status['time_averaging_paper_gate'] or 'missing'}; "
            f"metadata_paper_averaging_ok={metadata_paper_averaging_status['ok']}; "
            f"metadata_paper_averaging_reasons={metadata_paper_averaging_status['reasons_csv'] or 'none'}; "
            f"manifest_expected_vtk_frame_count={manifest_paper_averaging_status['expected_vtk_frame_count']}; "
            f"manifest_paper_recommended_averaging_frames={manifest_paper_averaging_status['paper_recommended_averaging_frames']}; "
            f"manifest_paper_recommended_average_step_span={manifest_paper_averaging_status['paper_recommended_average_step_span']}; "
            f"manifest_expected_paper_average_step_span={manifest_paper_averaging_status['expected_paper_average_step_span']}; "
            f"manifest_paper_averaging_ok={manifest_paper_averaging_status['ok']}; "
            f"manifest_paper_averaging_reasons={manifest_paper_averaging_status['reasons_csv'] or 'none'}; "
            f"requested_vtk_frame_gate={requested_vtk_frame_gate or 'missing'}; "
            f"requested_vtk_frame_gate_reasons={requested_vtk_frame_gate_reasons or 'none'}; "
            f"expected_vtk_frame_count={expected_vtk_frame_count}; "
            f"available_frame_count={available_frame_count}; source_first_step={source_first_step}; "
            f"runtime_vtk_pattern={runtime_vtk_pattern or 'missing'}; "
            f"expected_vtk_pattern={expected_vtk_pattern or 'not enforced'}; "
            f"vtk_pattern_ok={vtk_pattern_ok}; "
            f"source_last_step={source_last_step}; latest_available_step={latest_available_step}; "
            f"selected_last_window={selected_last_window}; source_steps_strictly_increasing={source_steps_increasing}; "
            f"source_step_spacing_uniform={source_spacing_uniform}; "
            f"runtime_time_averaging_gate={runtime_time_gate or 'missing'}; "
            f"runtime_time_averaging_gate_reasons={runtime_time_gate_reasons or 'none'}; "
            f"metrics_time_averaging_gate={get_any(metrics, ['time_averaging_gate', 'TimeAveragingGate']) or 'ignored'}; "
            f"metrics_averaged_frame_count={get_any(metrics, ['averaged_frame_count', 'AveragedFrameCount']) or 'ignored'}; "
            f"mean_speed_statistics_source={mean_speed_statistics_source or 'missing'}; "
            f"speed_statistics_source_ok={speed_statistics_source_ok}; "
            f"mean_speed_stddev_ratio={mean_speed_stddev_ratio}; required <= {args.max_mean_speed_stddev_ratio}; "
            f"max_speed_stddev_ratio={max_speed_stddev_ratio}; required <= {args.max_point_speed_stddev_ratio}; "
            f"runtime_audit={runtime_audit_path or 'missing'}"
        ),
        "Rerun or postprocess with a longer statistically stable final-window average whose source steps are the last available, increasing and uniformly spaced.",
    )
    metrics_time_status = metrics_time_averaging_consistency_status(
        metrics,
        runtime_audit,
        args.min_avg_frames,
        args.min_avg_step_span,
    )
    add_gate(
        gates,
        "metrics_time_averaging_consistency",
        PASS if metrics_time_status["ok"] else FAIL,
        (
            f"runtime_time_averaging_gate={metrics_time_status['runtime_time_averaging_gate'] or 'missing'}; "
            f"metrics_time_averaging_gate={metrics_time_status['metrics_time_averaging_gate'] or 'missing'}; "
            f"runtime_source_time_steps={metrics_time_status['runtime_source_time_steps'] or 'missing'}; "
            f"metrics_source_time_steps={metrics_time_status['metrics_source_time_steps'] or 'missing'}; "
            f"runtime_frame_count={metrics_time_status['runtime_frame_count']}; "
            f"metrics_source_step_count={metrics_time_status['metrics_frame_count']}; "
            f"metrics_averaged_frame_count={metrics_time_status['metrics_averaged_frame_count']}; "
            f"required_frames>={args.min_avg_frames}; "
            f"runtime_available_frame_count={metrics_time_status['runtime_available_frame_count']}; "
            f"metrics_available_frame_count={metrics_time_status['metrics_available_frame_count']}; "
            f"runtime_source_step_span={metrics_time_status['runtime_source_step_span']}; "
            f"metrics_source_step_span={metrics_time_status['metrics_source_step_span']}; "
            f"required_step_span>={args.min_avg_step_span}; "
            f"runtime_minimum_step_span={metrics_time_status['runtime_minimum_step_span']}; "
            f"metrics_minimum_step_span={metrics_time_status['metrics_minimum_step_span']}; "
            f"reasons={metrics_time_status['reasons_csv'] or 'none'}"
        ),
        "Rebuild validation_metrics.csv from the same final-window VTK files recorded in read_vtk_audit/native_run_audit; stale or short-window metrics cannot support validation.",
    )

    target_velocity_lbm = as_float(
        get_any(metrics, ["target_max_profile_velocity_lbm", "TargetMaxProfileVelocityLbm"])
        or metadata.get("TargetMaxProfileVelocityLbm")
        or get_any(manifest.get("SharedRunConditions", {}), ["TargetMaxProfileVelocityLbm"])
    )
    estimated_mach = as_float(
        get_any(metrics, ["estimated_max_profile_mach", "EstimatedMaxProfileMach"])
        or metadata.get("EstimatedMaxProfileMach")
        or get_any(manifest.get("SharedRunConditions", {}), ["EstimatedMaxProfileMach"])
    )
    lbm_tau = as_float(
        get_any(metrics, ["lbm_tau", "LbmTau"])
        or metadata.get("LbmTau")
        or get_any(manifest.get("SharedRunConditions", {}), ["LbmTau"])
    )
    lbm_nu = as_float(
        get_any(metrics, ["lbm_nu", "LbmNu"])
        or metadata.get("LbmNu")
        or get_any(manifest.get("SharedRunConditions", {}), ["LbmNu"])
    )
    physical_viscosity = as_float(
        get_any(metrics, ["physical_viscosity_m2s", "PhysicalViscosityM2s"])
        or metadata.get("PhysicalViscosityM2s")
        or get_any(manifest.get("SharedRunConditions", {}), ["PhysicalViscosityM2s"])
    )
    estimated_re = as_float(
        get_any(metrics, ["estimated_reynolds_number", "EstimatedReynoldsNumber"])
        or metadata.get("EstimatedReynoldsNumber")
        or get_any(manifest.get("SharedRunConditions", {}), ["EstimatedReynoldsNumber"])
    )
    velocity_set = str(
        get_any(metrics, ["velocity_set", "VelocitySet"])
        or metadata.get("VelocitySet")
        or get_any(manifest.get("SharedRunConditions", {}), ["VelocitySet"])
        or ""
    ).strip()
    les_model = str(
        get_any(metrics, ["les_model", "LesModel"])
        or metadata.get("LesModel")
        or get_any(manifest.get("SharedRunConditions", {}), ["LesModel"])
        or ""
    ).strip()
    solver_warnings = str(
        get_any(runtime_audit, ["solver_stability_warnings", "SolverStabilityWarnings"])
        or get_any(manifest.get("SharedRunConditions", {}), ["SolverStabilityWarnings"])
        or ""
    ).strip().lower()
    lbm_stability_gate = str(
        get_any(runtime_audit, ["lbm_stability_gate", "LbmStabilityGate"])
        or get_any(manifest.get("SharedRunConditions", {}), ["LbmStabilityGate"])
        or ""
    ).strip().lower()
    stability_protocol_status = protocol_status(items, "lbm_stability_scaling")
    solver_warning_ok = solver_warnings in {
        "none",
        "no_warnings",
        "no_stability_warnings",
        "pass",
        "solver_log_no_stability_warnings",
    }
    lbm_stability_ok = (
        target_velocity_lbm is not None
        and target_velocity_lbm <= 0.1
        and estimated_mach is not None
        and estimated_mach <= args.max_estimated_mach
        and lbm_tau is not None
        and args.min_lbm_tau <= lbm_tau <= args.max_lbm_tau
        and lbm_nu is not None
        and lbm_nu > 0.0
        and physical_viscosity is not None
        and physical_viscosity > 0.0
        and estimated_re is not None
        and estimated_re > 0.0
        and bool(velocity_set)
        and bool(les_model)
        and solver_warning_ok
        and lbm_stability_gate in {"pass", "solver_log_no_stability_warnings", "runtime_statistics_archived"}
    )
    add_gate(
        gates,
        "lbm_stability",
        PASS if lbm_stability_ok else FAIL,
        (
            f"target_max_profile_velocity_lbm={target_velocity_lbm}; required <= 0.1; "
            f"estimated_max_profile_mach={estimated_mach}; required <= {args.max_estimated_mach}; "
            f"lbm_tau={lbm_tau}; required {args.min_lbm_tau}..{args.max_lbm_tau}; "
            f"lbm_nu={lbm_nu}; physical_viscosity_m2s={physical_viscosity}; "
            f"estimated_reynolds_number={estimated_re}; velocity_set={velocity_set or 'missing'}; "
            f"les_model={les_model or 'missing'}; solver_stability_warnings={solver_warnings or 'missing'}; "
            f"lbm_stability_gate={lbm_stability_gate or 'missing'}; "
            f"metrics_lbm_stability_gate={get_any(metrics, ['lbm_stability_gate', 'LbmStabilityGate']) or 'ignored'}; "
            f"metrics_solver_stability_warnings={get_any(metrics, ['solver_stability_warnings', 'SolverStabilityWarnings']) or 'ignored'}; "
            f"runtime_audit={runtime_audit_path or 'missing'}; "
            f"protocol_status={stability_protocol_status or 'missing'}"
        ),
        "Archive solver log/runtime statistics proving no FluidX3D stability warnings, bounded Mach, valid tau/nu, Reynolds number, velocity set and LES/subgrid model before interpreting validation metrics.",
    )

    boundary_gate = str(
        get_any(external_boundary_audit, ["metadata_boundary_protocol_gate"])
        or ""
    )
    boundary_audit = metadata.get("BoundaryProtocolAudit", {}) if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    blockage_audit = boundary_audit.get("BlockageDiagnostics", {}) if isinstance(boundary_audit.get("BlockageDiagnostics"), dict) else {}
    frontal_blockage = as_float(
        get_any(external_boundary_audit, ["approx_frontal_blockage_ratio", "ApproxFrontalBlockageRatio"])
        or get_any(blockage_audit, ["ApproxFrontalBlockageRatio"])
    )
    blockage_gate = str(
        get_any(external_boundary_audit, ["blockage_gate", "blockage_protocol_gate", "BlockageProtocolGate"])
        or get_any(blockage_audit, ["Gate"])
        or ""
    )
    boundary_evidence_source = str(
        get_any(external_boundary_audit, ["boundary_evidence_source"])
        or ""
    )
    boundary_evidence_gate = str(
        get_any(external_boundary_audit, ["boundary_evidence_gate"])
        or ""
    ).strip().lower()
    boundary_equivalence_basis = str(
        get_any(external_boundary_audit, ["boundary_equivalence_basis"])
        or ""
    )
    boundary_evidence_class = str(
        get_any(external_boundary_audit, ["boundary_evidence_class"])
        or ""
    ).strip().lower()
    boundary_evidence_class_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_class_supported"])
    )
    boundary_evidence_files_all_exist = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_files_all_exist"])
    )
    boundary_evidence_files_all_hashed = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_files_all_hashed"])
    )
    boundary_condition_fields_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_condition_fields_supported"])
    )
    boundary_condition_support_reasons = str(
        get_any(external_boundary_audit, ["boundary_condition_support_reasons"])
        or ""
    )
    boundary_condition_support_keys = [
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
    boundary_condition_support_values = {
        key: as_bool(get_any(external_boundary_audit, [key]))
        for key in boundary_condition_support_keys
    }
    external_boundary_condition_support_values = {
        key: as_bool(get_any(external_boundary_audit, [key]))
        for key in boundary_condition_support_keys
    }
    external_boundary_equivalence_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_equivalence_supported"])
    )
    external_boundary_equivalence_supported_from_audit = as_bool(
        get_any(external_boundary_audit, ["boundary_equivalence_supported"])
    )
    external_boundary_evidence_gate = str(
        get_any(external_boundary_audit, ["boundary_evidence_gate"]) or ""
    ).strip().lower()
    external_boundary_evidence_class_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_class_supported"])
    )
    external_boundary_evidence_files_all_exist = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_files_all_exist"])
    )
    external_boundary_evidence_files_all_hashed = as_bool(
        get_any(external_boundary_audit, ["boundary_evidence_files_all_hashed"])
    )
    external_boundary_condition_fields_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_condition_fields_supported"])
    )
    clearance_numeric_gate = str(
        get_any(external_boundary_audit, ["clearance_numeric_gate"])
        or ""
    ).strip().lower()
    external_clearance_numeric_gate = str(
        get_any(external_boundary_audit, ["clearance_numeric_gate"]) or ""
    ).strip().lower()
    clearance_numeric_reasons = str(
        get_any(external_boundary_audit, ["clearance_numeric_gate_reasons"])
        or ""
    )
    external_boundary_protocol_gate = str(
        get_any(external_boundary_audit, ["boundary_protocol_gate"]) or ""
    ).strip().lower()
    boundary_evidence_file_hash_check = boundary_evidence_file_hash_status(
        external_boundary_audit,
        boundary_audit_path,
    )
    boundary_evidence_file_hashes_match_current = boundary_evidence_file_hash_check["ok"] is True
    boundary_evidence_file_hash_error = str(boundary_evidence_file_hash_check.get("error") or "")
    boundary_run_identity_gate = str(
        get_any(external_boundary_audit, ["boundary_run_identity_gate"])
        or get_any(metrics, ["boundary_run_identity_gate", "BoundaryRunIdentityGate"])
        or ""
    ).strip().lower()
    boundary_run_identity_reasons = str(
        get_any(external_boundary_audit, ["boundary_run_identity_gate_reasons"])
        or get_any(metrics, ["boundary_run_identity_gate_reasons", "BoundaryRunIdentityGateReasons"])
        or ""
    )
    boundary_evidence_metadata_hash_matches = as_bool(
        get_first_available(
            get_any(external_boundary_audit, ["evidence_metadata_sha256_matches_current"]),
            get_any(metrics, ["boundary_evidence_metadata_sha256_matches_current", "BoundaryEvidenceMetadataSha256MatchesCurrent"]),
        )
    )
    boundary_evidence_aij_case = str(
        get_any(external_boundary_audit, ["evidence_aij_case"])
        or get_any(metrics, ["boundary_evidence_aij_case", "BoundaryEvidenceAijCase"])
        or ""
    )
    boundary_evidence_wind_direction = str(
        get_any(external_boundary_audit, ["evidence_wind_direction"])
        or get_any(metrics, ["boundary_evidence_wind_direction", "BoundaryEvidenceWindDirection"])
        or ""
    )
    external_boundary_missing_fields = external_boundary_audit.get("missing_evidence_fields")
    if isinstance(external_boundary_missing_fields, list):
        external_boundary_missing_fields_text = ",".join(str(field) for field in external_boundary_missing_fields)
    else:
        external_boundary_missing_fields_text = str(external_boundary_missing_fields or "")
    boundary_source_gate = str(get_any(boundary_source_audit, ["boundary_source_gate"]) or "").strip().lower()
    boundary_source_reasons = str(
        get_first_available(
            get_any(boundary_source_audit, ["boundary_source_gate_reasons_csv"]),
            get_any(boundary_source_audit, ["boundary_source_gate_reasons"]),
        )
        or ""
    )
    paper_grade_boundary_source_gate = str(
        get_any(boundary_source_audit, ["paper_grade_boundary_source_gate"]) or ""
    ).strip().lower()
    paper_grade_boundary_source_reasons = str(
        get_first_available(
            get_any(boundary_source_audit, ["paper_grade_boundary_source_gate_reasons_csv"]),
            get_any(boundary_source_audit, ["paper_grade_boundary_source_gate_reasons"]),
        )
        or ""
    )
    boundary_source_method_class = str(
        get_any(boundary_source_audit, ["boundary_source_method_class"]) or ""
    ).strip()
    boundary_source_fidelity_class = str(
        get_any(boundary_source_audit, ["boundary_source_fidelity_class"]) or ""
    ).strip()
    boundary_source_complete_wind_tunnel_evidence = as_bool(
        get_any(boundary_source_audit, ["boundary_source_has_complete_wind_tunnel_evidence"])
    )
    boundary_source_empty_stub_only = as_bool(
        get_any(boundary_source_audit, ["boundary_source_has_empty_advanced_method_stub_only"])
    )
    boundary_source_coherent = as_bool(
        get_any(boundary_source_audit, ["boundary_source_coherent"])
    )
    boundary_source_simplified = as_bool(
        get_any(boundary_source_audit, ["boundary_source_simplified"])
    )
    boundary_source_wind_tunnel_equivalent = as_bool(
        get_any(boundary_source_audit, ["boundary_source_wind_tunnel_equivalent"])
    )
    boundary_source_advanced_code_evidence = as_bool(
        get_any(boundary_source_audit, ["boundary_source_advanced_code_evidence"])
    )
    boundary_source_comment_stripped_code_audit = as_bool(
        get_any(boundary_source_audit, ["advanced_boundary_evidence_uses_comment_stripped_code"])
    )
    boundary_has_non_reflecting_method = as_bool(
        get_any(boundary_source_audit, ["has_non_reflecting_outlet_method"])
    )
    boundary_has_non_reflecting_state = as_bool(
        get_any(boundary_source_audit, ["has_non_reflecting_outlet_state_evidence"])
    )
    boundary_has_periodic_method = as_bool(
        get_any(boundary_source_audit, ["has_periodic_side_top_method"])
    )
    boundary_has_periodic_mapping = as_bool(
        get_any(boundary_source_audit, ["has_periodic_pair_mapping_evidence"])
    )
    boundary_has_rough_wall_method = as_bool(
        get_any(boundary_source_audit, ["has_rough_wall_function_method"])
    )
    boundary_has_rough_wall_parameter = as_bool(
        get_any(boundary_source_audit, ["has_rough_wall_parameter_evidence"])
    )
    boundary_has_rough_wall_action = as_bool(
        get_any(boundary_source_audit, ["has_rough_wall_action_evidence"])
    )
    boundary_has_precursor_recycling_method = as_bool(
        get_any(boundary_source_audit, ["has_precursor_or_recycling_boundary_method"])
    )
    boundary_has_precursor_recycling_field = as_bool(
        get_any(boundary_source_audit, ["has_precursor_or_recycling_boundary_field_evidence"])
    )
    boundary_has_paper_grade_outlet_source = as_bool(
        get_any(boundary_source_audit, ["has_paper_grade_outlet_source"])
    )
    boundary_has_paper_grade_side_top_source = as_bool(
        get_any(boundary_source_audit, ["has_paper_grade_side_top_source"])
    )
    boundary_has_paper_grade_rough_wall_source = as_bool(
        get_any(boundary_source_audit, ["has_paper_grade_rough_wall_source"])
    )
    boundary_has_paper_grade_development_source = as_bool(
        get_any(boundary_source_audit, ["has_paper_grade_development_source"])
    )
    boundary_source_missing_paper_grade_evidence = str(
        get_first_available(
            get_any(boundary_source_audit, ["missing_paper_grade_source_evidence"]),
            get_any(metrics, ["boundary_source_missing_paper_grade_source_evidence"]),
        )
        or ""
    )
    boundary_type_e_velocity_initialization = as_bool(
        get_any(boundary_source_audit, ["has_type_e_velocity_initialization"])
    )
    boundary_type_e_velocity_initialization_guard = as_bool(
        get_any(boundary_source_audit, ["has_type_e_velocity_initialization_guard"])
    )
    boundary_type_e_velocity_initialization_coordinates = as_bool(
        get_any(boundary_source_audit, ["has_type_e_velocity_initialization_coordinates"])
    )
    boundary_type_e_velocity_initialization_velocity_write = as_bool(
        get_any(boundary_source_audit, ["has_type_e_velocity_initialization_velocity_write"])
    )
    boundary_profile_type_e_velocity_initialization = as_bool(
        get_any(boundary_source_audit, ["has_profile_type_e_velocity_initialization"])
    )
    boundary_has_profile_inlet = as_bool(get_any(boundary_source_audit, ["has_profile_inlet"]))
    boundary_source_setup_sha256 = str(
        get_any(boundary_source_audit, ["setup_cpp_sha256"]) or ""
    ).strip().lower()
    boundary_source_setup_hash_matches = (
        bool(current_setup_cpp_sha256)
        and bool(boundary_source_setup_sha256)
        and boundary_source_setup_sha256 == current_setup_cpp_sha256
    )
    boundary_type_e_velocity_initialization_required = (
        boundary_source_method_class in {"simplified_type_e_box", "partial_type_e_boundary_source"}
        or boundary_has_profile_inlet is True
    )
    boundary_type_e_velocity_initialization_ok = (
        not boundary_type_e_velocity_initialization_required
        or (
            boundary_type_e_velocity_initialization is True
            and boundary_type_e_velocity_initialization_guard is True
            and boundary_type_e_velocity_initialization_coordinates is True
            and boundary_type_e_velocity_initialization_velocity_write is True
            and (boundary_has_profile_inlet is not True or boundary_profile_type_e_velocity_initialization is True)
        )
    )
    boundary_evidence_supported_by_token = any(
        token in (boundary_evidence_source + " " + boundary_equivalence_basis).lower()
        for token in [
            "aij_verified",
            "empty_tunnel_passed",
            "validated_boundary_model",
            "precursor_boundary",
            "recycling_boundary",
            "wind_tunnel_protocol_matched",
        ]
    )
    boundary_evidence_supported = external_boundary_equivalence_supported is True
    boundary_diagnostic_ok = (
        boundary_gate == "diagnostic_clearance_ok_verify_against_aij"
        and frontal_blockage is not None
        and frontal_blockage <= args.max_frontal_blockage_ratio
    )
    boundary_external_ok = external_boundary_protocol_gate == "pass"
    boundary_clearance_ok = clearance_numeric_gate in {"", "pass"}
    external_boundary_audit_evidence_complete = (
        boundary_audit_path is not None
        and boundary_external_ok
        and external_boundary_evidence_gate == "pass"
        and external_boundary_equivalence_supported_from_audit is True
        and external_boundary_evidence_class_supported is True
        and external_boundary_evidence_files_all_exist is True
        and external_boundary_evidence_files_all_hashed is True
        and boundary_evidence_file_hashes_match_current
        and boundary_run_identity_gate == "pass"
        and boundary_evidence_metadata_hash_matches is True
        and external_boundary_condition_fields_supported is True
        and all(value is True for value in external_boundary_condition_support_values.values())
        and external_clearance_numeric_gate == "pass"
        and not external_boundary_missing_fields_text
    )
    boundary_evidence_ok = (
        boundary_evidence_gate == "pass"
        and external_boundary_audit_evidence_complete
        and boundary_evidence_supported
        and boundary_evidence_class_supported is True
        and boundary_evidence_files_all_exist is True
        and boundary_evidence_files_all_hashed is True
        and boundary_evidence_file_hashes_match_current
        and boundary_run_identity_gate == "pass"
        and boundary_evidence_metadata_hash_matches is True
        and boundary_condition_fields_supported is True
        and all(value is True for value in boundary_condition_support_values.values())
        and boundary_clearance_ok
    )
    boundary_source_evidence_ok = (
        boundary_source_audit_path is not None
        and boundary_source_gate == "pass"
        and boundary_source_coherent is True
        and boundary_type_e_velocity_initialization_ok
        and bool(boundary_source_method_class)
        and bool(boundary_source_setup_sha256)
        and boundary_source_setup_hash_matches
    )
    paper_grade_boundary_source_ok = (
        boundary_source_evidence_ok
        and paper_grade_boundary_source_gate == "pass"
        and boundary_source_wind_tunnel_equivalent is True
        and boundary_source_fidelity_class == "wind_tunnel_equivalent_complete"
        and boundary_source_complete_wind_tunnel_evidence is True
        and boundary_source_empty_stub_only is False
        and boundary_source_simplified is not True
        and boundary_source_advanced_code_evidence is True
        and boundary_source_comment_stripped_code_audit is True
        and boundary_has_paper_grade_outlet_source is True
        and boundary_has_paper_grade_side_top_source is True
        and boundary_has_paper_grade_rough_wall_source is True
        and boundary_has_paper_grade_development_source is True
        and not boundary_source_missing_paper_grade_evidence
    )
    add_gate(
        gates,
        "boundary_source_evidence",
        PASS if paper_grade_boundary_source_ok else FAIL,
        (
            f"boundary_source_audit={boundary_source_audit_path or 'missing'}; "
            f"boundary_source_gate={boundary_source_gate or 'missing'}; "
            f"paper_grade_boundary_source_gate={paper_grade_boundary_source_gate or 'missing'}; "
            f"boundary_source_evidence_ok={boundary_source_evidence_ok}; "
            f"paper_grade_boundary_source_ok={paper_grade_boundary_source_ok}; "
            f"source_method_class={boundary_source_method_class or 'missing'}; "
            f"source_fidelity_class={boundary_source_fidelity_class or 'missing'}; "
            f"source_complete_wind_tunnel_evidence={boundary_source_complete_wind_tunnel_evidence}; "
            f"source_empty_stub_only={boundary_source_empty_stub_only}; "
            f"source_coherent={boundary_source_coherent}; "
            f"source_simplified={boundary_source_simplified}; "
            f"source_wind_tunnel_equivalent={boundary_source_wind_tunnel_equivalent}; "
            f"source_advanced_code_evidence={boundary_source_advanced_code_evidence}; "
            f"comment_stripped_code_audit={boundary_source_comment_stripped_code_audit}; "
            f"non_reflecting_method={boundary_has_non_reflecting_method}; "
            f"non_reflecting_state_evidence={boundary_has_non_reflecting_state}; "
            f"periodic_method={boundary_has_periodic_method}; "
            f"periodic_pair_mapping_evidence={boundary_has_periodic_mapping}; "
            f"rough_wall_method={boundary_has_rough_wall_method}; "
            f"rough_wall_parameter_evidence={boundary_has_rough_wall_parameter}; "
            f"rough_wall_action_evidence={boundary_has_rough_wall_action}; "
            f"precursor_recycling_method={boundary_has_precursor_recycling_method}; "
            f"precursor_recycling_field_evidence={boundary_has_precursor_recycling_field}; "
            f"paper_grade_outlet_source={boundary_has_paper_grade_outlet_source}; "
            f"paper_grade_side_top_source={boundary_has_paper_grade_side_top_source}; "
            f"paper_grade_rough_wall_source={boundary_has_paper_grade_rough_wall_source}; "
            f"paper_grade_development_source={boundary_has_paper_grade_development_source}; "
            f"missing_paper_grade_source_evidence={boundary_source_missing_paper_grade_evidence or 'none'}; "
            f"type_e_velocity_initialization={boundary_type_e_velocity_initialization}; "
            f"type_e_velocity_initialization_guard={boundary_type_e_velocity_initialization_guard}; "
            f"type_e_velocity_initialization_coordinates={boundary_type_e_velocity_initialization_coordinates}; "
            f"type_e_velocity_initialization_velocity_write={boundary_type_e_velocity_initialization_velocity_write}; "
            f"profile_type_e_velocity_initialization={boundary_profile_type_e_velocity_initialization}; "
            f"has_profile_inlet={boundary_has_profile_inlet}; "
            f"type_e_velocity_initialization_required={boundary_type_e_velocity_initialization_required}; "
            f"type_e_velocity_initialization_ok={boundary_type_e_velocity_initialization_ok}; "
            f"setup_cpp_sha256={boundary_source_setup_sha256 or 'missing'}; "
            f"current_setup_cpp={setup_cpp_path or 'missing'}; "
            f"current_setup_cpp_sha256={current_setup_cpp_sha256 or 'missing'}; "
            f"setup_hash_matches_current={boundary_source_setup_hash_matches}; "
            f"boundary_source_gate_reasons={boundary_source_reasons or 'none'}; "
            f"metrics_boundary_source_gate={get_any(metrics, ['boundary_source_gate', 'BoundarySourceGate']) or 'ignored'}; "
            f"metrics_paper_grade_boundary_source_gate={get_any(metrics, ['paper_grade_boundary_source_gate', 'PaperGradeBoundarySourceGate']) or 'ignored'}; "
            f"metrics_boundary_source_method_class={get_any(metrics, ['boundary_source_method_class', 'BoundarySourceMethodClass']) or 'ignored'}"
        ),
        "Run scripts/audit_boundary_source.py on the generated setup.cpp and archive the source hash and boundary implementation class before interpreting boundary-sensitive validation metrics.",
    )
    add_gate(
        gates,
        "boundary_protocol",
        PASS
        if boundary_diagnostic_ok
        and paper_grade_boundary_source_ok
        and boundary_evidence_ok
        and boundary_external_ok
        else FAIL,
        (
            f"boundary_protocol_gate={boundary_gate or 'missing'}; "
            f"boundary_source_gate={boundary_source_gate or 'missing'}; "
            f"paper_grade_boundary_source_gate={paper_grade_boundary_source_gate or 'missing'}; "
            f"source_method_class={boundary_source_method_class or 'missing'}; "
            f"source_simplified={boundary_source_simplified}; "
            f"source_wind_tunnel_equivalent={boundary_source_wind_tunnel_equivalent}; "
            f"source_advanced_code_evidence={boundary_source_advanced_code_evidence}; "
            f"comment_stripped_code_audit={boundary_source_comment_stripped_code_audit}; "
            f"non_reflecting_method={boundary_has_non_reflecting_method}; "
            f"non_reflecting_state_evidence={boundary_has_non_reflecting_state}; "
            f"periodic_method={boundary_has_periodic_method}; "
            f"periodic_pair_mapping_evidence={boundary_has_periodic_mapping}; "
            f"rough_wall_method={boundary_has_rough_wall_method}; "
            f"rough_wall_parameter_evidence={boundary_has_rough_wall_parameter}; "
            f"rough_wall_action_evidence={boundary_has_rough_wall_action}; "
            f"precursor_recycling_method={boundary_has_precursor_recycling_method}; "
            f"precursor_recycling_field_evidence={boundary_has_precursor_recycling_field}; "
            f"type_e_velocity_initialization={boundary_type_e_velocity_initialization}; "
            f"profile_type_e_velocity_initialization={boundary_profile_type_e_velocity_initialization}; "
            f"type_e_velocity_initialization_required={boundary_type_e_velocity_initialization_required}; "
            f"type_e_velocity_initialization_ok={boundary_type_e_velocity_initialization_ok}; "
            f"external_boundary_protocol_gate={external_boundary_protocol_gate or 'missing'}; "
            f"approx_frontal_blockage_ratio={frontal_blockage}; "
            f"blockage_protocol_gate={blockage_gate or 'missing'}; "
            f"required frontal <= {args.max_frontal_blockage_ratio}; "
            f"boundary_evidence_gate={boundary_evidence_gate or 'missing'}; "
            f"boundary_evidence_source={boundary_evidence_source or 'missing'}; "
            f"boundary_equivalence_basis={boundary_equivalence_basis or 'missing'}; "
            f"boundary_evidence_supported={boundary_evidence_supported}; "
            f"external_boundary_equivalence_supported_from_audit={external_boundary_equivalence_supported_from_audit}; "
            f"external_boundary_audit_evidence_complete={external_boundary_audit_evidence_complete}; "
            f"external_boundary_evidence_gate={external_boundary_evidence_gate or 'missing'}; "
            f"external_boundary_evidence_class_supported={external_boundary_evidence_class_supported}; "
            f"external_boundary_evidence_files_all_exist={external_boundary_evidence_files_all_exist}; "
            f"external_boundary_evidence_files_all_hashed={external_boundary_evidence_files_all_hashed}; "
            f"boundary_evidence_file_hashes_match_current={boundary_evidence_file_hashes_match_current}; "
            f"boundary_evidence_file_hash_error={boundary_evidence_file_hash_error or 'none'}; "
            f"boundary_evidence_hash_record_count={boundary_evidence_file_hash_check['hash_record_count']}; "
            f"boundary_evidence_hash_declared_file_count={boundary_evidence_file_hash_check['declared_file_count']}; "
            f"boundary_evidence_hash_mismatch_count={boundary_evidence_file_hash_check['hash_mismatch_count']}; "
            f"boundary_run_identity_gate={boundary_run_identity_gate or 'missing'}; "
            f"boundary_run_identity_reasons={boundary_run_identity_reasons or 'none'}; "
            f"boundary_evidence_metadata_hash_matches_current={boundary_evidence_metadata_hash_matches}; "
            f"boundary_evidence_aij_case={boundary_evidence_aij_case or 'missing'}; "
            f"boundary_evidence_wind_direction={boundary_evidence_wind_direction or 'missing'}; "
            f"external_boundary_condition_fields_supported={external_boundary_condition_fields_supported}; "
            f"external_boundary_condition_support_values={external_boundary_condition_support_values}; "
            f"boundary_evidence_class={boundary_evidence_class or 'missing'}; "
            f"boundary_evidence_class_supported={boundary_evidence_class_supported}; "
            f"boundary_evidence_files_all_exist={boundary_evidence_files_all_exist}; "
            f"boundary_evidence_files_all_hashed={boundary_evidence_files_all_hashed}; "
            f"boundary_condition_fields_supported={boundary_condition_fields_supported}; "
            f"boundary_condition_support_values={boundary_condition_support_values}; "
            f"boundary_condition_support_reasons={boundary_condition_support_reasons or 'none'}; "
            f"boundary_equivalence_token_inferred={boundary_evidence_supported_by_token}; "
            f"clearance_numeric_gate={clearance_numeric_gate or 'missing'}; "
            f"external_clearance_numeric_gate={external_clearance_numeric_gate or 'missing'}; "
            f"clearance_numeric_gate_reasons={clearance_numeric_reasons or 'none'}; "
            f"paper_grade_boundary_source_gate_reasons={paper_grade_boundary_source_reasons or 'none'}; "
            f"missing_boundary_evidence_fields={external_boundary_missing_fields_text or 'none'}; "
            f"metrics_boundary_protocol_gate={get_any(metrics, ['boundary_protocol_gate', 'BoundaryProtocolGate']) or 'ignored'}; "
            f"metrics_boundary_evidence_gate={get_any(metrics, ['boundary_evidence_gate', 'BoundaryProtocolEvidenceGate']) or 'ignored'}; "
            f"metrics_blockage_protocol_gate={get_any(metrics, ['blockage_protocol_gate', 'BlockageProtocolGate']) or 'ignored'}"
        ),
        "Fix domain extents/model placement, reduce blockage, archive setup.cpp boundary-source evidence, and replace/justify simplified TYPE_E boundaries with AIJ-equivalent boundary/fetch/roughness evidence or an empty-tunnel/native boundary-preservation check.",
    )

    boundary_runtime_gate_value = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_gate"]),
            get_any(metrics, ["boundary_runtime_gate", "BoundaryRuntimeGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_traceability_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_traceability_gate"]),
            get_any(metrics, ["boundary_runtime_traceability_gate", "BoundaryRuntimeTraceabilityGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_profile_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_profile_preservation_gate"]),
            get_any(metrics, ["boundary_runtime_profile_preservation_gate", "BoundaryRuntimeProfilePreservationGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_inlet_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_inlet_gate"]),
            get_any(metrics, ["boundary_runtime_inlet_gate", "BoundaryRuntimeInletGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_side_top_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_side_top_gate"]),
            get_any(metrics, ["boundary_runtime_side_top_gate", "BoundaryRuntimeSideTopGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_side_top_normal_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_side_top_normal_leakage_gate"]),
            get_any(metrics, ["boundary_runtime_side_top_normal_leakage_gate", "BoundaryRuntimeSideTopNormalLeakageGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_outlet_gate = str(
        get_first_available(
            get_any(boundary_runtime_audit, ["boundary_runtime_outlet_gate"]),
            get_any(metrics, ["boundary_runtime_outlet_gate", "BoundaryRuntimeOutletGate"]),
        )
        or ""
    ).strip().lower()
    boundary_runtime_reason_values = get_first_available(
        get_any(boundary_runtime_audit, ["boundary_runtime_gate_reasons"]),
        get_any(metrics, ["boundary_runtime_gate_reasons", "BoundaryRuntimeGateReasons"]),
    )
    boundary_runtime_reasons = (
        ";".join(as_string_list(boundary_runtime_reason_values))
        if isinstance(boundary_runtime_reason_values, list)
        else str(boundary_runtime_reason_values or "")
    )
    boundary_runtime_max_u_mae_ratio = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["max_boundary_u_mae_ratio"]),
            get_any(metrics, ["boundary_runtime_max_u_mae_ratio", "BoundaryRuntimeMaxUMaeRatio"]),
        )
    )
    boundary_runtime_inlet_u_mae_ratio = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["inlet_u_mae_ratio"]),
            get_any(metrics, ["boundary_runtime_inlet_u_mae_ratio", "BoundaryRuntimeInletUMaeRatio"]),
        )
    )
    boundary_runtime_outlet_u_mae_ratio = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["outlet_u_mae_ratio"]),
            get_any(metrics, ["boundary_runtime_outlet_u_mae_ratio", "BoundaryRuntimeOutletUMaeRatio"]),
        )
    )
    boundary_runtime_side_top_max_u_mae_ratio = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["side_top_max_u_mae_ratio"]),
            get_any(metrics, ["boundary_runtime_side_top_max_u_mae_ratio", "BoundaryRuntimeSideTopMaxUMaeRatio"]),
        )
    )
    boundary_runtime_max_side_top_normal_velocity_ratio = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["max_side_top_normal_velocity_ratio"]),
            get_any(metrics, ["boundary_runtime_max_side_top_normal_velocity_ratio", "BoundaryRuntimeMaxSideTopNormalVelocityRatio"]),
        )
    )
    boundary_runtime_max_side_top_normal_abs_mps = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["max_side_top_normal_abs_mps"]),
            get_any(metrics, ["boundary_runtime_max_side_top_normal_abs_mps", "BoundaryRuntimeMaxSideTopNormalAbsMps"]),
        )
    )
    boundary_runtime_max_negative_fraction = as_float(
        get_first_available(
            get_any(boundary_runtime_audit, ["max_boundary_negative_streamwise_fraction"]),
            get_any(metrics, ["boundary_runtime_max_negative_streamwise_fraction", "BoundaryRuntimeMaxNegativeStreamwiseFraction"]),
        )
    )
    boundary_runtime_source_step_span = as_int(
        get_first_available(
            get_any(boundary_runtime_audit, ["source_step_span"]),
            get_any(metrics, ["boundary_runtime_source_step_span", "BoundaryRuntimeSourceStepSpan"]),
        )
    )
    boundary_runtime_frame_count = as_int(
        get_first_available(
            get_any(boundary_runtime_audit, ["frame_count"]),
            get_any(metrics, ["boundary_runtime_frame_count", "BoundaryRuntimeFrameCount"]),
        )
    )
    boundary_runtime_ok = (
        boundary_runtime_audit_path is not None
        and boundary_runtime_gate_value == "pass"
        and boundary_runtime_traceability_gate == "pass"
        and boundary_runtime_profile_gate == "pass"
        and boundary_runtime_inlet_gate == "pass"
        and boundary_runtime_side_top_gate == "pass"
        and boundary_runtime_side_top_normal_gate == "pass"
        and boundary_runtime_outlet_gate == "pass"
    )
    add_gate(
        gates,
        "boundary_runtime",
        PASS if boundary_runtime_ok else FAIL,
        (
            f"boundary_runtime_audit={boundary_runtime_audit_path or 'missing'}; "
            f"boundary_runtime_gate={boundary_runtime_gate_value or 'missing'}; "
            f"boundary_runtime_traceability_gate={boundary_runtime_traceability_gate or 'missing'}; "
            f"boundary_runtime_profile_preservation_gate={boundary_runtime_profile_gate or 'missing'}; "
            f"boundary_runtime_inlet_gate={boundary_runtime_inlet_gate or 'missing'}; "
            f"boundary_runtime_side_top_gate={boundary_runtime_side_top_gate or 'missing'}; "
            f"boundary_runtime_side_top_normal_leakage_gate={boundary_runtime_side_top_normal_gate or 'missing'}; "
            f"boundary_runtime_outlet_gate={boundary_runtime_outlet_gate or 'missing'}; "
            f"max_boundary_u_mae_ratio={boundary_runtime_max_u_mae_ratio}; "
            f"inlet_u_mae_ratio={boundary_runtime_inlet_u_mae_ratio}; "
            f"side_top_max_u_mae_ratio={boundary_runtime_side_top_max_u_mae_ratio}; "
            f"max_side_top_normal_velocity_ratio={boundary_runtime_max_side_top_normal_velocity_ratio}; "
            f"max_side_top_normal_abs_mps={boundary_runtime_max_side_top_normal_abs_mps}; "
            f"outlet_u_mae_ratio={boundary_runtime_outlet_u_mae_ratio}; "
            f"max_negative_streamwise_fraction={boundary_runtime_max_negative_fraction}; "
            f"frame_count={boundary_runtime_frame_count}; "
            f"source_step_span={boundary_runtime_source_step_span}; "
            f"reasons={boundary_runtime_reasons or 'none'}"
        ),
        "Run scripts/audit_boundary_runtime_from_vtk.py on the same final VTK averaging window and fix inlet/outlet/lateral/top boundary treatment until boundary-face U(z), side/top no-penetration and reverse-flow checks pass.",
    )

    roughness_layout = metadata.get("RoughnessLayout") if isinstance(metadata.get("RoughnessLayout"), dict) else {}
    equivalent_precursor = metadata.get("EquivalentPrecursor") if isinstance(metadata.get("EquivalentPrecursor"), dict) else {}
    wall_roughness_treatment = str(
        get_any(external_boundary_audit, ["wall_roughness_treatment", "WallRoughnessTreatment"])
        or metadata.get("WallRoughnessTreatment")
        or ""
    ).strip()
    external_roughness_treatment = str(get_any(external_boundary_audit, ["roughness_treatment"]) or "").strip()
    floor_roughness_source = str(
        get_any(external_boundary_audit, ["floor_roughness_source"])
        or get_any(roughness_layout, ["SourceReferences"])
        or ""
    ).strip()
    roughness_layout_enabled = as_bool(roughness_layout.get("Enabled"))
    roughness_layout_paper = as_bool(roughness_layout.get("PaperSourceAdmissible"))
    roughness_voxel_count = as_int(roughness_layout.get("VoxelizedBoxCount"))
    precursor_enabled = as_bool(equivalent_precursor.get("Enabled"))
    precursor_empty_gate = as_bool(equivalent_precursor.get("EmptyTunnelGatePass"))
    precursor_paper = as_bool(equivalent_precursor.get("PaperAdmissible"))
    precursor_method_class = str(equivalent_precursor.get("MethodClass") or "").strip()
    roughness_text = " ".join(
        [
            wall_roughness_treatment,
            external_roughness_treatment,
            floor_roughness_source,
            precursor_method_class,
        ]
    ).lower()
    roughness_source_supported = any(
        token in roughness_text
        for token in [
            "aij_verified",
            "official",
            "wind_tunnel_protocol_matched",
            "roughness_layout_source",
            "validated_rough_wall",
            "empty_tunnel_passed",
            "precursor",
            "recycling",
        ]
    )
    roughness_layout_ok = (
        roughness_layout_enabled is True
        and roughness_layout_paper is True
        and roughness_voxel_count is not None
        and roughness_voxel_count > 0
    )
    precursor_ok = precursor_enabled is True and precursor_empty_gate is True and precursor_paper is True
    external_roughness_ok = (
        boundary_evidence_ok
        and external_boundary_audit_evidence_complete
        and bool(external_roughness_treatment)
        and bool(floor_roughness_source)
        and roughness_source_supported
    )
    roughness_or_precursor_ok = roughness_layout_ok or precursor_ok or external_roughness_ok
    add_gate(
        gates,
        "roughness_or_precursor",
        PASS if roughness_or_precursor_ok else FAIL,
        (
            f"wall_roughness_treatment={wall_roughness_treatment or 'missing'}; "
            f"external_roughness_treatment={external_roughness_treatment or 'missing'}; "
            f"floor_roughness_source={floor_roughness_source or 'missing'}; "
            f"roughness_layout_enabled={roughness_layout_enabled}; "
            f"roughness_layout_paper_admissible={roughness_layout_paper}; "
            f"roughness_voxel_count={roughness_voxel_count}; "
            f"equivalent_precursor_enabled={precursor_enabled}; "
            f"equivalent_precursor_empty_gate={precursor_empty_gate}; "
            f"equivalent_precursor_paper_admissible={precursor_paper}; "
            f"precursor_method_class={precursor_method_class or 'missing'}; "
            f"roughness_source_supported={roughness_source_supported}; "
            f"boundary_evidence_gate={boundary_evidence_gate or 'missing'}; "
            f"boundary_evidence_ok={boundary_evidence_ok}; "
            f"external_boundary_audit_evidence_complete={external_boundary_audit_evidence_complete}; "
            f"external_roughness_ok={external_roughness_ok}; "
            f"metrics_wall_roughness_treatment={get_any(metrics, ['wall_roughness_treatment', 'WallRoughnessTreatment']) or 'ignored'}; "
            f"metrics_floor_roughness_source={get_any(metrics, ['floor_roughness_source', 'FloorRoughnessSource']) or 'ignored'}"
        ),
        (
            "Archive source-driven AIJ roughness geometry, a validated rough-wall treatment, or a passing "
            "empty-tunnel precursor/recycling equivalence record before promoting Case A/E validation."
        ),
    )

    inlet_status = protocol_status(items, "inlet_turbulence_k")
    distribution_status = protocol_status(items, "inlet_distribution_consistency")
    inlet_treatment = str(
        get_any(metrics, ["inlet_distribution_treatment"])
        or metadata.get("SyntheticTurbulentInletDistributionTreatment")
        or ""
    )
    synthetic_inlet_method = str(
        get_any(metrics, ["synthetic_inlet_method", "SyntheticInletMethod"])
        or metadata.get("SyntheticTurbulentInletMethod")
        or metadata.get("TurbulenceMethod")
        or ""
    ).strip()
    inlet_method_class = str(
        get_any(metrics, ["inlet_method_class", "paper_grade_inlet_method_class", "InletMethodClass"])
        or metadata.get("PaperGradeInletMethodClass")
        or metadata.get("InletMethodClass")
        or ""
    ).strip()
    inlet_method_class_supported = as_bool(
        get_any(
            metrics,
            [
                "inlet_method_class_supported",
                "paper_grade_inlet_method_class_supported",
                "InletMethodClassSupported",
            ],
        )
        or metadata.get("PaperGradeInletMethodClassSupported")
        or metadata.get("InletMethodClassSupported")
    )
    inlet_source_gate = str(
        get_any(inlet_source_audit, ["inlet_source_gate"]) or ""
    ).strip().lower()
    inlet_source_reasons = str(
        get_first_available(
            get_any(inlet_source_audit, ["inlet_source_gate_reasons_csv"]),
            get_any(inlet_source_audit, ["inlet_source_gate_reasons"]),
        )
        or ""
    )
    paper_grade_inlet_source_gate = str(
        get_any(inlet_source_audit, ["paper_grade_inlet_source_gate"]) or ""
    ).strip().lower()
    paper_grade_inlet_source_reasons = str(
        get_first_available(
            get_any(inlet_source_audit, ["paper_grade_inlet_source_gate_reasons_csv"]),
            get_any(inlet_source_audit, ["paper_grade_inlet_source_gate_reasons"]),
        )
        or ""
    )
    inlet_source_method_class = str(
        get_any(inlet_source_audit, ["inlet_source_method_class"]) or ""
    ).strip()
    inlet_source_fidelity_class = str(
        get_any(inlet_source_audit, ["inlet_source_turbulent_inflow_fidelity_class"]) or ""
    ).strip()
    inlet_source_distribution_consistent = as_bool(
        get_any(inlet_source_audit, ["inlet_source_distribution_consistent"])
    )
    inlet_source_velocity_field_only = as_bool(
        get_any(inlet_source_audit, ["inlet_source_velocity_field_only"])
    )
    inlet_source_setup_sha256 = str(
        get_any(inlet_source_audit, ["setup_cpp_sha256"]) or ""
    ).strip().lower()
    audit_inlet_source_gate = str(get_any(inlet_source_audit, ["inlet_source_gate"]) or "").strip().lower()
    audit_paper_grade_inlet_source_gate = str(
        get_any(inlet_source_audit, ["paper_grade_inlet_source_gate"]) or ""
    ).strip().lower()
    audit_inlet_source_method_class = str(
        get_any(inlet_source_audit, ["inlet_source_method_class"]) or ""
    ).strip()
    audit_inlet_source_fidelity_class = str(
        get_any(inlet_source_audit, ["inlet_source_turbulent_inflow_fidelity_class"]) or ""
    ).strip()
    audit_inlet_source_distribution_consistent = as_bool(
        get_any(inlet_source_audit, ["inlet_source_distribution_consistent"])
    )
    audit_inlet_source_velocity_field_only = as_bool(
        get_any(inlet_source_audit, ["inlet_source_velocity_field_only"])
    )
    audit_has_distribution_function_write = as_bool(
        get_any(inlet_source_audit, ["has_distribution_function_write"])
    )
    audit_distribution_function_write_count = as_int(
        get_any(inlet_source_audit, ["distribution_function_write_count"])
    )
    audit_has_inlet_distribution_reconstruction = as_bool(
        get_any(inlet_source_audit, ["has_inlet_distribution_reconstruction"])
    )
    audit_inlet_distribution_reconstruction_count = as_int(
        get_any(inlet_source_audit, ["inlet_distribution_reconstruction_count"])
    )
    audit_has_digital_filter_kernel = as_bool(
        get_any(inlet_source_audit, ["has_digital_filter_kernel_evidence"])
    )
    audit_has_digital_filter_state = as_bool(
        get_any(inlet_source_audit, ["has_digital_filter_state_evidence"])
    )
    audit_has_sem_eddy_population = as_bool(
        get_any(inlet_source_audit, ["has_sem_eddy_population_evidence"])
    )
    audit_has_precursor_recycling_field = as_bool(
        get_any(inlet_source_audit, ["has_precursor_recycling_field_evidence"])
    )
    audit_distribution_consistency_basis = str(
        get_any(inlet_source_audit, ["distribution_consistency_basis"]) or ""
    ).strip().lower()
    audit_inlet_source_setup_sha256 = str(
        get_any(inlet_source_audit, ["setup_cpp_sha256"]) or ""
    ).strip().lower()
    inlet_source_setup_hash_matches = (
        bool(current_setup_cpp_sha256)
        and bool(audit_inlet_source_setup_sha256)
        and audit_inlet_source_setup_sha256 == current_setup_cpp_sha256
    )
    audit_inlet_source_comment_stripped = as_bool(
        get_any(
            inlet_source_audit,
            [
                "advanced_inlet_evidence_uses_comment_stripped_code",
                "inlet_source_comment_stripped_code_audit",
            ],
        )
    )
    audit_synthetic_inlet_requested = as_bool(
        get_any(inlet_source_audit, ["synthetic_inlet_requested"])
    )
    audit_has_synthetic_inlet_function = as_bool(
        get_any(inlet_source_audit, ["has_synthetic_inlet_function"])
    )
    audit_has_three_component_velocity_write = as_bool(
        get_any(inlet_source_audit, ["has_three_component_velocity_write"])
    )
    audit_has_three_component_fluctuation_evidence = as_bool(
        get_any(inlet_source_audit, ["has_three_component_fluctuation_evidence"])
    )
    audit_has_k_driven_three_component_stg = as_bool(
        get_any(inlet_source_audit, ["has_k_driven_three_component_stg"])
    )
    audit_has_stg_refresh_with_current_time = as_bool(
        get_any(inlet_source_audit, ["has_synthetic_inlet_refresh_with_current_time"])
    )
    audit_has_update_interval_run_control = as_bool(
        get_any(inlet_source_audit, ["has_update_interval_run_control"])
    )
    audit_has_segmented_stg_run_loop = as_bool(
        get_any(inlet_source_audit, ["has_segmented_stg_run_loop"])
    )
    audit_has_uncorrelated_random_inlet = as_bool(
        get_any(inlet_source_audit, ["has_uncorrelated_random_inlet"])
    )
    audit_has_correlated_velocity_field_only = as_bool(
        get_any(inlet_source_audit, ["inlet_source_has_correlated_velocity_field_only"])
    )
    audit_has_uncorrelated_rms_velocity_field_only = as_bool(
        get_any(inlet_source_audit, ["inlet_source_has_uncorrelated_rms_velocity_field_only"])
    )
    audit_inlet_correlation_model = str(
        get_any(inlet_source_audit, ["synthetic_inlet_correlation_model"]) or ""
    ).strip()
    audit_has_inlet_length_scale_evidence = as_bool(
        get_any(inlet_source_audit, ["has_length_scale_evidence"])
    )
    wind_profile_text = str(
        get_first_available(
            get_any(metadata, ["WindProfile", "wind_profile"]),
            get_any(metrics, ["wind_profile", "WindProfile"]),
            get_any(shared_run_conditions, ["WindProfile", "wind_profile"]),
        )
        or ""
    ).strip()
    custom_profile_rows = as_int(
        get_first_available(
            get_any(metadata, ["CustomProfileRows", "custom_profile_rows"]),
            get_any(metrics, ["custom_profile_rows", "CustomProfileRows"]),
            get_any(shared_run_conditions, ["CustomProfileRows", "custom_profile_rows"]),
        )
    )
    custom_profile_has_k = as_bool(
        get_first_available(
            get_any(metadata, ["CustomProfileHasK", "custom_profile_has_k"]),
            get_any(metrics, ["custom_profile_has_k", "CustomProfileHasK"]),
            get_any(shared_run_conditions, ["CustomProfileHasK", "custom_profile_has_k"]),
        )
    )
    custom_profile_k_rows = as_int(
        get_first_available(
            get_any(metadata, ["CustomProfileKRows", "custom_profile_k_rows"]),
            get_any(metrics, ["custom_profile_k_rows", "CustomProfileKRows"]),
            get_any(shared_run_conditions, ["CustomProfileKRows", "custom_profile_k_rows"]),
        )
    )
    custom_profile_k_complete = as_bool(
        get_first_available(
            get_any(metadata, ["CustomProfileKComplete", "custom_profile_k_complete"]),
            get_any(metrics, ["custom_profile_k_complete", "CustomProfileKComplete"]),
            get_any(shared_run_conditions, ["CustomProfileKComplete", "custom_profile_k_complete"]),
        )
    )
    k_column_status = str(
        get_first_available(
            get_any(metadata, ["KColumnStatus", "k_column_status"]),
            get_any(metrics, ["k_column_status", "KColumnStatus"]),
            get_any(shared_run_conditions, ["KColumnStatus", "k_column_status"]),
        )
        or ""
    ).strip().lower()
    synthetic_inlet_requested = as_bool(
        get_first_available(
            get_any(metadata, ["SyntheticTurbulentInletRequested", "synthetic_turbulent_inlet_requested"]),
            get_any(metrics, ["synthetic_turbulent_inlet_requested", "SyntheticTurbulentInletRequested"]),
            get_any(shared_run_conditions, ["SyntheticTurbulentInletRequested", "synthetic_turbulent_inlet_requested"]),
        )
    )
    synthetic_inlet_injected = as_bool(
        get_first_available(
            get_any(metadata, ["SyntheticTurbulentInletInjected", "synthetic_turbulent_inlet_injected"]),
            get_any(metrics, ["synthetic_turbulent_inlet_injected", "SyntheticTurbulentInletInjected"]),
            get_any(shared_run_conditions, ["SyntheticTurbulentInletInjected", "synthetic_turbulent_inlet_injected"]),
        )
    )
    synthetic_inlet_blocked_reason = str(
        get_first_available(
            get_any(metadata, ["SyntheticTurbulentInletBlockedReason", "synthetic_turbulent_inlet_blocked_reason"]),
            get_any(metrics, ["synthetic_turbulent_inlet_blocked_reason", "SyntheticTurbulentInletBlockedReason"]),
            get_any(shared_run_conditions, ["SyntheticTurbulentInletBlockedReason", "synthetic_turbulent_inlet_blocked_reason"]),
        )
        or ""
    ).strip().lower()
    custom_profile_present = (
        wind_profile_text.lower() == "customtable"
        or (custom_profile_rows is not None and custom_profile_rows >= 2)
    )
    k_rows_match_profile_rows = (
        custom_profile_rows is not None
        and custom_profile_k_rows is not None
        and custom_profile_rows > 0
        and custom_profile_k_rows == custom_profile_rows
    )
    k_complete = custom_profile_k_complete is True or k_rows_match_profile_rows
    k_has_any = custom_profile_has_k is True or (custom_profile_k_rows is not None and custom_profile_k_rows > 0)
    custom_k_reasons: List[str] = []
    if custom_profile_present:
        if custom_profile_rows is None or custom_profile_rows < 2:
            custom_k_reasons.append("custom_profile_rows_missing_or_too_short")
        if not k_has_any:
            custom_k_reasons.append("custom_profile_k_missing")
        elif not k_complete:
            custom_k_reasons.append("custom_profile_k_column_incomplete")
        if k_column_status in {"invalid_partial_k_column", "not_available"}:
            custom_k_reasons.append(f"k_column_status:{k_column_status}")
        elif not k_column_status:
            custom_k_reasons.append("k_column_status_missing")
    if (
        synthetic_inlet_requested is True
        and synthetic_inlet_injected is not True
        and synthetic_inlet_blocked_reason == "custom_profile_k_column_incomplete"
    ):
        custom_k_reasons.append("synthetic_inlet_blocked_by_custom_profile_k_column")
    add_gate(
        gates,
        "custom_k_profile",
        PASS if not custom_k_reasons else FAIL,
        (
            f"wind_profile={wind_profile_text or 'missing'}; "
            f"custom_profile_present={custom_profile_present}; "
            f"custom_profile_rows={custom_profile_rows}; "
            f"custom_profile_has_k={custom_profile_has_k}; "
            f"custom_profile_k_rows={custom_profile_k_rows}; "
            f"custom_profile_k_complete={custom_profile_k_complete}; "
            f"k_rows_match_profile_rows={k_rows_match_profile_rows}; "
            f"k_column_status={k_column_status or 'missing'}; "
            f"synthetic_inlet_requested={synthetic_inlet_requested}; "
            f"synthetic_inlet_injected={synthetic_inlet_injected}; "
            f"synthetic_inlet_blocked_reason={synthetic_inlet_blocked_reason or 'missing'}; "
            f"reasons={';'.join(custom_k_reasons) if custom_k_reasons else 'none'}"
        ),
        "For AIJ CustomTable validation, read a complete z,U,k AF table, keep one k value per profile row, archive k conversion metadata and regenerate the case before using inlet turbulence evidence.",
    )
    inlet_profile_gate = str(get_any(inlet_profile_audit, ["inlet_profile_gate"]) or "").strip().lower()
    inlet_u_profile_gate = str(get_any(inlet_profile_audit, ["inlet_u_profile_gate"]) or "").strip().lower()
    inlet_k_profile_gate = str(get_any(inlet_profile_audit, ["inlet_k_profile_gate"]) or "").strip().lower()
    inlet_streamwise_direction_gate = str(
        get_any(inlet_profile_audit, ["inlet_streamwise_direction_gate"]) or ""
    ).strip().lower()
    inlet_negative_streamwise_fraction = as_float(get_any(inlet_profile_audit, ["negative_streamwise_fraction"]))
    inlet_profile_available_frame_count = as_int(get_any(inlet_profile_audit, ["available_frame_count"]))
    inlet_profile_frame_count = as_int(get_any(inlet_profile_audit, ["frame_count"]))
    inlet_profile_source_steps = get_first_available(
        get_any(inlet_profile_audit, ["source_time_steps_csv"]),
        get_any(inlet_profile_audit, ["source_time_steps"]),
    )
    inlet_profile_source_frame_count, inlet_profile_source_step_text, inlet_profile_has_source_steps = source_frame_details(
        {"source_time_steps": inlet_profile_source_steps}
    )
    inlet_profile_parsed_steps, inlet_profile_steps_error = parsed_source_steps(
        inlet_profile_source_step_text
    )
    inlet_profile_source_matches = (
        has_real_source_steps
        and parsed_steps_error is None
        and inlet_profile_steps_error is None
        and inlet_profile_parsed_steps == parsed_steps
    )
    inlet_profile_vtk_hash_status = runtime_selected_vtk_hash_status(
        inlet_profile_audit,
        inlet_profile_audit_path,
        inlet_profile_source_step_text,
    )
    inlet_profile_source_hashes = inlet_profile_vtk_hash_status["actual_hashes"]
    inlet_profile_source_hash_text = inlet_profile_vtk_hash_status["actual_hash_text"]
    inlet_profile_source_hash_matches = (
        inlet_profile_vtk_hash_status["ok"]
        and bool(expected_source_hashes)
        and bool(inlet_profile_source_hashes)
        and inlet_profile_source_hashes == expected_source_hashes
    )
    add_gate(
        gates,
        "inlet_profile_vtk_hash_traceability",
        PASS if inlet_profile_source_hash_matches else FAIL,
        (
            f"selected_file_count={inlet_profile_vtk_hash_status['selected_file_count']}; "
            f"expected_step_count={inlet_profile_vtk_hash_status['expected_step_count']}; "
            f"path_missing_count={inlet_profile_vtk_hash_status['path_missing_count']}; "
            f"missing_file_count={inlet_profile_vtk_hash_status['missing_file_count']}; "
            f"hash_mismatch_count={inlet_profile_vtk_hash_status['hash_mismatch_count']}; "
            f"declared_hashes={inlet_profile_vtk_hash_status['declared_hash_text'] or 'missing'}; "
            f"actual_hashes={inlet_profile_vtk_hash_status['actual_hash_text'] or 'missing'}; "
            f"runtime_expected_hashes={expected_source_hash_text or 'missing'}; "
            f"source_hash_matches_runtime={inlet_profile_source_hash_matches}; "
            f"error={inlet_profile_vtk_hash_status['error'] or 'none'}; "
            f"inlet_profile_audit={inlet_profile_audit_path or 'missing'}"
        ),
        "Regenerate the inlet-profile audit from the current final-window VTK files; source_time_steps or copied hashes alone are not accepted.",
    )
    metadata_profile_csv_sha256 = str(get_any(metadata, ["WindProfileCsvSha256"]) or "").strip().lower()
    inlet_profile_af_csv_sha256 = str(get_any(inlet_profile_audit, ["af_csv_sha256", "AfCsvSha256"]) or "").strip().lower()
    inlet_profile_af_csv_hash_matches = (
        bool(metadata_profile_csv_sha256)
        and bool(inlet_profile_af_csv_sha256)
        and metadata_profile_csv_sha256 == inlet_profile_af_csv_sha256
    )
    inlet_profile_source_first_step = as_int(get_any(inlet_profile_audit, ["source_first_time_step"]))
    inlet_profile_source_last_step = as_int(get_any(inlet_profile_audit, ["source_last_time_step"]))
    inlet_profile_declared_step_span = as_int(get_any(inlet_profile_audit, ["source_step_span"]))
    inlet_profile_latest_available_step = as_int(get_any(inlet_profile_audit, ["latest_available_time_step"]))
    inlet_profile_selected_last_window = as_bool(get_any(inlet_profile_audit, ["selected_last_window"]))
    inlet_profile_steps_increasing = as_bool(get_any(inlet_profile_audit, ["source_steps_strictly_increasing"]))
    inlet_profile_spacing_uniform = as_bool(get_any(inlet_profile_audit, ["source_step_spacing_uniform"]))
    inlet_profile_time_gate = str(get_any(inlet_profile_audit, ["time_averaging_gate"]) or "").strip().lower()
    inlet_profile_time_gate_reasons = str(
        get_any(inlet_profile_audit, ["time_averaging_gate_reasons_csv"])
        or get_any(inlet_profile_audit, ["time_averaging_gate_reasons"])
        or ""
    ).strip()
    inlet_u_mae_ratio = as_float(get_any(inlet_profile_audit, ["U_MAE_ratio"]))
    inlet_u_rmse_ratio = as_float(get_any(inlet_profile_audit, ["U_RMSE_ratio"]))
    inlet_k_mae_ratio = as_float(get_any(inlet_profile_audit, ["k_MAE_ratio"]))
    inlet_k_rmse_ratio = as_float(get_any(inlet_profile_audit, ["k_RMSE_ratio"]))
    inlet_profile_computed_step_span = (
        inlet_profile_parsed_steps[-1] - inlet_profile_parsed_steps[0]
        if len(inlet_profile_parsed_steps) >= 2
        else None
    )
    inlet_profile_step_span_matches = (
        inlet_profile_declared_step_span is not None
        and inlet_profile_computed_step_span is not None
        and inlet_profile_declared_step_span == inlet_profile_computed_step_span
    )
    inlet_profile_step_span_long_enough = (
        inlet_profile_computed_step_span is not None
        and inlet_profile_computed_step_span >= args.min_avg_step_span
    )
    empty_u_bias = as_float(get_any(inlet_profile_audit, ["U_bias_ratio"]))
    empty_k_bias = as_float(get_any(inlet_profile_audit, ["k_bias_ratio"]))
    empty_gate = inlet_profile_gate
    inlet_profile_window_ok = (
        inlet_profile_has_source_steps
        and inlet_profile_source_matches
        and inlet_profile_source_hash_matches
        and inlet_profile_af_csv_hash_matches
        and inlet_profile_frame_count is not None
        and inlet_profile_source_frame_count is not None
        and inlet_profile_frame_count == inlet_profile_source_frame_count
        and inlet_profile_frame_count >= args.min_avg_frames
        and inlet_profile_selected_last_window is True
        and inlet_profile_steps_increasing is True
        and inlet_profile_spacing_uniform is True
        and inlet_profile_source_last_step is not None
        and inlet_profile_latest_available_step is not None
        and inlet_profile_source_last_step == inlet_profile_latest_available_step
        and inlet_profile_step_span_matches
        and inlet_profile_step_span_long_enough
        and inlet_profile_time_gate == "pass"
    )
    inlet_profile_pass = (
        inlet_profile_gate == "pass"
        and inlet_u_profile_gate == "pass"
        and inlet_k_profile_gate == "pass"
        and inlet_streamwise_direction_gate == "pass"
        and inlet_profile_window_ok
    )
    empty_tunnel_pass = (
        inlet_profile_pass
        or (
            inlet_profile_window_ok
            and empty_gate == "pass"
        )
        or (
            inlet_profile_window_ok
            and empty_u_bias is not None
            and abs(empty_u_bias) <= args.max_empty_tunnel_u_bias_ratio
            and empty_k_bias is not None
            and abs(empty_k_bias) <= args.max_empty_tunnel_k_bias_ratio
        )
    )
    treatment_text = inlet_treatment.lower()
    method_text = synthetic_inlet_method.lower()
    method_class_text = inlet_method_class.lower()
    treatment_distribution_consistent = any(
        token in treatment_text
        for token in [
            "distribution_consistent",
            "precursor",
            "validated_recycling",
            "recycling_distribution_consistent",
            "digital_filter_distribution",
            "digital-filter_distribution",
            "sem_distribution",
            "dfm_distribution",
        ]
    )
    treatment_velocity_only = any(
        token in treatment_text
        for token in [
            "velocity_field_only",
            "macroscopic_velocity",
            "diagnostic_unverified",
            "uncorrelated_rms",
            "unless_distribution_evidence_archived",
        ]
    )
    method_name_only = bool(method_text) and not inlet_treatment.strip()
    inferred_method_class_supported = any(
        token in method_class_text
        for token in [
            "digital_filter",
            "dfm",
            "sem",
            "synthetic_eddy_distribution_consistent",
            "precursor",
            "recycling_rescaling",
        ]
    ) and not any(token in method_class_text for token in ["diagnostic", "velocity_field_only", "stg_lite", "stg-lite"])
    paper_method_class_ok = (
        bool(method_class_text)
        and (inlet_method_class_supported is True or inferred_method_class_supported)
        and not method_name_only
    )
    audit_method_class_text = audit_inlet_source_method_class.lower()
    audit_stg_run_loop_required = (
        audit_has_synthetic_inlet_function is True
        or "stg" in audit_method_class_text
        or "stg" in method_text
        or "stg" in method_class_text
    )
    audit_stg_run_loop_ok = (
        not audit_stg_run_loop_required
        or (
            audit_has_stg_refresh_with_current_time is True
            and audit_has_update_interval_run_control is True
            and audit_has_segmented_stg_run_loop is True
        )
    )
    audit_stg_three_component_evidence_ok = stg_three_component_evidence_pass(
        required=audit_stg_run_loop_required,
        has_three_component_velocity_write=audit_has_three_component_velocity_write,
        has_three_component_fluctuation_evidence=audit_has_three_component_fluctuation_evidence,
        has_k_driven_three_component_stg=audit_has_k_driven_three_component_stg,
    )
    inlet_gate_status = PASS
    if inlet_status == "fail" or distribution_status == "fail":
        inlet_gate_status = FAIL
    elif treatment_velocity_only:
        inlet_gate_status = PASS if args.allow_velocity_only_inlet and empty_tunnel_pass else FAIL
    elif treatment_distribution_consistent or distribution_status == "pass":
        inlet_gate_status = PASS if empty_tunnel_pass else FAIL
    else:
        inlet_gate_status = FAIL
    add_gate(
        gates,
        "inlet_profile_preservation",
        PASS if inlet_profile_pass else FAIL,
        (
            f"inlet_profile_gate={inlet_profile_gate or 'missing'}; "
            f"inlet_u_profile_gate={inlet_u_profile_gate or 'missing'}; "
            f"inlet_k_profile_gate={inlet_k_profile_gate or 'missing'}; "
            f"inlet_streamwise_direction_gate={inlet_streamwise_direction_gate or 'missing'}; "
            f"inlet_negative_streamwise_fraction={inlet_negative_streamwise_fraction}; "
            f"inlet_profile_frame_count={inlet_profile_frame_count}; required >= {args.min_avg_frames}; "
            f"inlet_profile_available_frame_count={inlet_profile_available_frame_count}; "
            f"inlet_profile_source_frame_count={inlet_profile_source_frame_count}; "
            f"inlet_profile_real_source_time_steps_present={inlet_profile_has_source_steps}; "
            f"expected_source_time_steps={source_step_text or 'missing'}; "
            f"expected_source_hashes={expected_source_hash_text or 'missing'}; "
            f"inlet_profile_source_time_steps={inlet_profile_source_step_text or 'missing'}; "
            f"inlet_profile_source_matches={inlet_profile_source_matches}; "
            f"inlet_profile_source_hashes={inlet_profile_source_hash_text or 'missing'}; "
            f"inlet_profile_source_hash_matches={inlet_profile_source_hash_matches}; "
            f"metadata_profile_csv_sha256={metadata_profile_csv_sha256 or 'missing'}; "
            f"inlet_profile_af_csv_sha256={inlet_profile_af_csv_sha256 or 'missing'}; "
            f"inlet_profile_af_csv_hash_matches={inlet_profile_af_csv_hash_matches}; "
            f"inlet_profile_source_steps_error={inlet_profile_steps_error or 'none'}; "
            f"inlet_profile_source_first_step={inlet_profile_source_first_step}; "
            f"inlet_profile_source_last_step={inlet_profile_source_last_step}; "
            f"inlet_profile_declared_step_span={inlet_profile_declared_step_span}; "
            f"inlet_profile_computed_step_span={inlet_profile_computed_step_span}; "
            f"inlet_profile_step_span_matches={inlet_profile_step_span_matches}; "
            f"inlet_profile_step_span_long_enough={inlet_profile_step_span_long_enough}; "
            f"required_step_span >= {args.min_avg_step_span}; "
            f"inlet_profile_latest_available_step={inlet_profile_latest_available_step}; "
            f"inlet_profile_selected_last_window={inlet_profile_selected_last_window}; "
            f"inlet_profile_source_steps_strictly_increasing={inlet_profile_steps_increasing}; "
            f"inlet_profile_source_step_spacing_uniform={inlet_profile_spacing_uniform}; "
            f"inlet_profile_time_averaging_gate={inlet_profile_time_gate or 'missing'}; "
            f"inlet_profile_time_averaging_gate_reasons={inlet_profile_time_gate_reasons or 'none'}; "
            f"inlet_u_mae_ratio={inlet_u_mae_ratio}; inlet_u_rmse_ratio={inlet_u_rmse_ratio}; "
            f"inlet_k_mae_ratio={inlet_k_mae_ratio}; inlet_k_rmse_ratio={inlet_k_rmse_ratio}; "
            f"metrics_inlet_profile_gate={get_any(metrics, ['inlet_profile_gate']) or 'ignored'}; "
            f"inlet_profile_audit={inlet_profile_audit_path or 'missing'}"
        ),
        "Run scripts/audit_inlet_profile_from_vtk.py on real post-spinup VTK frames and pass U(z)/k(z) preservation before paper-grade validation.",
    )

    inlet_source_evidence_ok = (
        inlet_source_audit_path is not None
        and audit_inlet_source_gate == "pass"
        and bool(audit_inlet_source_method_class)
        and bool(audit_inlet_source_setup_sha256)
        and inlet_source_setup_hash_matches
        and audit_inlet_source_comment_stripped is True
        and audit_stg_run_loop_ok
        and audit_stg_three_component_evidence_ok
        and audit_has_uncorrelated_random_inlet is not True
        and audit_has_correlated_velocity_field_only is not True
        and audit_has_uncorrelated_rms_velocity_field_only is not True
    )
    add_gate(
        gates,
        "inlet_source_evidence",
        PASS if inlet_source_evidence_ok else FAIL,
        (
            f"inlet_source_audit={inlet_source_audit_path or 'missing'}; "
            f"inlet_source_gate={inlet_source_gate or 'missing'}; "
            f"paper_grade_inlet_source_gate={paper_grade_inlet_source_gate or 'missing'}; "
            f"source_method_class={inlet_source_method_class or 'missing'}; "
            f"source_turbulent_inflow_fidelity_class={inlet_source_fidelity_class or 'missing'}; "
            f"source_distribution_consistent={inlet_source_distribution_consistent}; "
            f"source_velocity_field_only={inlet_source_velocity_field_only}; "
            f"setup_cpp_sha256={inlet_source_setup_sha256 or 'missing'}; "
            f"current_setup_cpp={setup_cpp_path or 'missing'}; "
            f"current_setup_cpp_sha256={current_setup_cpp_sha256 or 'missing'}; "
            f"setup_hash_matches_current={inlet_source_setup_hash_matches}; "
            f"audit_only_inlet_source_gate={audit_inlet_source_gate or 'missing'}; "
            f"audit_only_paper_grade_inlet_source_gate={audit_paper_grade_inlet_source_gate or 'missing'}; "
            f"audit_only_source_method_class={audit_inlet_source_method_class or 'missing'}; "
            f"audit_only_source_turbulent_inflow_fidelity_class={audit_inlet_source_fidelity_class or 'missing'}; "
            f"audit_only_source_distribution_consistent={audit_inlet_source_distribution_consistent}; "
            f"audit_only_source_velocity_field_only={audit_inlet_source_velocity_field_only}; "
            f"audit_has_distribution_function_write={audit_has_distribution_function_write}; "
            f"audit_distribution_function_write_count={audit_distribution_function_write_count}; "
            f"audit_has_inlet_distribution_reconstruction={audit_has_inlet_distribution_reconstruction}; "
            f"audit_inlet_distribution_reconstruction_count={audit_inlet_distribution_reconstruction_count}; "
            f"audit_has_digital_filter_kernel={audit_has_digital_filter_kernel}; "
            f"audit_has_digital_filter_state={audit_has_digital_filter_state}; "
            f"audit_has_sem_eddy_population={audit_has_sem_eddy_population}; "
            f"audit_has_precursor_recycling_field={audit_has_precursor_recycling_field}; "
            f"audit_distribution_consistency_basis={audit_distribution_consistency_basis or 'missing'}; "
            f"audit_only_setup_cpp_sha256={audit_inlet_source_setup_sha256 or 'missing'}; "
            f"audit_comment_stripped_code_audit={audit_inlet_source_comment_stripped}; "
            f"audit_synthetic_inlet_requested={audit_synthetic_inlet_requested}; "
            f"audit_has_synthetic_inlet_function={audit_has_synthetic_inlet_function}; "
            f"audit_has_three_component_velocity_write={audit_has_three_component_velocity_write}; "
            f"audit_has_three_component_fluctuation_evidence={audit_has_three_component_fluctuation_evidence}; "
            f"audit_has_k_driven_three_component_stg={audit_has_k_driven_three_component_stg}; "
            f"audit_stg_run_loop_required={audit_stg_run_loop_required}; "
            f"audit_has_synthetic_inlet_refresh_with_current_time={audit_has_stg_refresh_with_current_time}; "
            f"audit_has_update_interval_run_control={audit_has_update_interval_run_control}; "
            f"audit_has_segmented_stg_run_loop={audit_has_segmented_stg_run_loop}; "
            f"audit_stg_run_loop_ok={audit_stg_run_loop_ok}; "
            f"audit_stg_three_component_evidence_ok={audit_stg_three_component_evidence_ok}; "
            f"audit_has_uncorrelated_random_inlet={audit_has_uncorrelated_random_inlet}; "
            f"audit_has_correlated_velocity_field_only={audit_has_correlated_velocity_field_only}; "
            f"audit_has_uncorrelated_rms_velocity_field_only={audit_has_uncorrelated_rms_velocity_field_only}; "
            f"audit_inlet_correlation_model={audit_inlet_correlation_model or 'missing'}; "
            f"inlet_source_gate_reasons={inlet_source_reasons or 'none'}; "
            f"metrics_inlet_source_gate={get_any(metrics, ['inlet_source_gate', 'InletSourceGate']) or 'ignored'}; "
            f"metrics_paper_grade_inlet_source_gate={get_any(metrics, ['paper_grade_inlet_source_gate', 'PaperGradeInletSourceGate']) or 'ignored'}; "
            f"metrics_inlet_source_method_class={get_any(metrics, ['inlet_source_method_class', 'InletSourceMethodClass']) or 'ignored'}"
        ),
        "Run scripts/audit_inlet_source.py on the generated setup.cpp and archive the source hash, inlet implementation class and STG run-loop evidence before interpreting probe accuracy.",
    )

    add_gate(
        gates,
        "inlet_turbulence",
        inlet_gate_status,
        (
            f"inlet_turbulence_k={inlet_status}; inlet_distribution_consistency={distribution_status}; "
            f"method={synthetic_inlet_method or 'missing'}; treatment={inlet_treatment or 'missing'}; "
            f"method_name_only={method_name_only}; inlet_profile_gate={inlet_profile_gate or 'missing'}; "
            f"empty_tunnel_gate={empty_gate or 'missing'}; "
            f"empty_tunnel_U_bias_ratio={empty_u_bias}; empty_tunnel_k_bias_ratio={empty_k_bias}; "
            f"allow_velocity_only_inlet={args.allow_velocity_only_inlet}"
        ),
        "Use a distribution-consistent DFM/SEM/precursor/recycling inlet and pass empty-tunnel U/k preservation; velocity-only STG-lite is diagnostic unless explicitly allowed.",
    )

    paper_grade_inlet_pass = paper_grade_inlet_method_pass(
        empty_tunnel_pass=empty_tunnel_pass,
        inlet_source_evidence_ok=inlet_source_evidence_ok,
        audit_paper_grade_inlet_source_gate=audit_paper_grade_inlet_source_gate,
        audit_inlet_source_distribution_consistent=audit_inlet_source_distribution_consistent,
        audit_inlet_source_velocity_field_only=audit_inlet_source_velocity_field_only,
        audit_inlet_source_comment_stripped=audit_inlet_source_comment_stripped,
        audit_has_uncorrelated_random_inlet=audit_has_uncorrelated_random_inlet,
        audit_inlet_source_turbulent_inflow_fidelity_class=audit_inlet_source_fidelity_class,
        paper_method_class_ok=paper_method_class_ok,
        treatment_distribution_consistent=treatment_distribution_consistent,
        distribution_status=distribution_status,
        treatment_velocity_only=treatment_velocity_only,
    )
    add_gate(
        gates,
        "paper_grade_inlet_method",
        PASS if paper_grade_inlet_pass else FAIL,
        (
            f"method={synthetic_inlet_method or 'missing'}; "
            f"method_class={inlet_method_class or 'missing'}; "
            f"method_class_supported={inlet_method_class_supported}; "
            f"inferred_method_class_supported={inferred_method_class_supported}; "
            f"source_method_class={inlet_source_method_class or 'missing'}; "
            f"source_turbulent_inflow_fidelity_class={inlet_source_fidelity_class or 'missing'}; "
            f"inlet_source_gate={inlet_source_gate or 'missing'}; "
            f"paper_grade_inlet_source_gate={paper_grade_inlet_source_gate or 'missing'}; "
            f"source_distribution_consistent={inlet_source_distribution_consistent}; "
            f"source_velocity_field_only={inlet_source_velocity_field_only}; "
            f"audit_only_paper_grade_inlet_source_gate={audit_paper_grade_inlet_source_gate or 'missing'}; "
            f"audit_only_source_turbulent_inflow_fidelity_class={audit_inlet_source_fidelity_class or 'missing'}; "
            f"audit_only_source_distribution_consistent={audit_inlet_source_distribution_consistent}; "
            f"audit_only_source_velocity_field_only={audit_inlet_source_velocity_field_only}; "
            f"audit_comment_stripped_code_audit={audit_inlet_source_comment_stripped}; "
            f"audit_distribution_consistency_basis={audit_distribution_consistency_basis or 'missing'}; "
            f"audit_has_digital_filter_kernel={audit_has_digital_filter_kernel}; "
            f"audit_has_digital_filter_state={audit_has_digital_filter_state}; "
            f"audit_has_sem_eddy_population={audit_has_sem_eddy_population}; "
            f"audit_has_precursor_recycling_field={audit_has_precursor_recycling_field}; "
            f"audit_has_uncorrelated_random_inlet={audit_has_uncorrelated_random_inlet}; "
            f"audit_has_correlated_velocity_field_only={audit_has_correlated_velocity_field_only}; "
            f"audit_has_uncorrelated_rms_velocity_field_only={audit_has_uncorrelated_rms_velocity_field_only}; "
            f"audit_inlet_correlation_model={audit_inlet_correlation_model or 'missing'}; "
            f"treatment={inlet_treatment or 'missing'}; "
            f"inlet_distribution_consistency={distribution_status or 'missing'}; "
            f"velocity_field_only={treatment_velocity_only}; "
            f"method_name_only={method_name_only}; "
            f"paper_method_class_ok={paper_method_class_ok}; "
            f"distribution_consistent={treatment_distribution_consistent}; "
            f"empty_tunnel_or_inlet_profile_pass={empty_tunnel_pass}; "
            f"paper_grade_inlet_source_gate_reasons={paper_grade_inlet_source_reasons or 'none'}; "
            f"allow_velocity_only_inlet={args.allow_velocity_only_inlet}"
        ),
        (
            "For paper-grade validation, use a distribution-consistent digital-filter, SEM/DFM, precursor or "
            "recycling inlet proven from comment-stripped generated source code. The --allow-velocity-only-inlet "
            "override is diagnostic only and cannot satisfy this paper-grade inlet-method gate."
        ),
    )

    inlet_correlation_gate = str(
        get_any(inlet_correlation_audit, ["inlet_correlation_gate"]) or ""
    ).strip().lower()
    inlet_temporal_lag1 = as_float(
        get_any(inlet_correlation_audit, ["temporal_lag1_mean_correlation"])
    )
    inlet_temporal_lag1_abs = as_float(
        get_any(inlet_correlation_audit, ["temporal_lag1_abs_mean_correlation"])
    )
    inlet_spatial_adjacent = as_float(
        get_any(inlet_correlation_audit, ["spatial_adjacent_mean_correlation"])
    )
    inlet_temporal_integral_lag_count = as_int(
        get_any(inlet_correlation_audit, ["temporal_integral_positive_lag_count"])
    )
    inlet_temporal_integral_time_steps = as_int(
        get_any(inlet_correlation_audit, ["temporal_integral_time_steps"])
    )
    inlet_spatial_integral_lag_count = as_int(
        get_any(inlet_correlation_audit, ["spatial_integral_positive_lag_count"])
    )
    inlet_spatial_integral_length_m = as_float(
        get_any(inlet_correlation_audit, ["spatial_integral_length_m"])
    )
    inlet_streamwise_variance = as_float(
        get_any(inlet_correlation_audit, ["mean_streamwise_fluctuation_variance"])
    )
    inlet_k_variance_gate = str(
        get_any(inlet_correlation_audit, ["inlet_k_variance_gate"]) or ""
    ).strip().lower()
    inlet_streamwise_variance_target = as_float(
        get_any(inlet_correlation_audit, ["inlet_streamwise_variance_target_from_k"])
    )
    inlet_streamwise_variance_to_k_ratio = as_float(
        get_any(inlet_correlation_audit, ["inlet_streamwise_variance_to_k_ratio"])
    )
    inlet_temporal_finite_fraction = as_float(
        get_any(inlet_correlation_audit, ["temporal_finite_correlation_fraction"])
    )
    inlet_spatial_finite_fraction = as_float(
        get_any(inlet_correlation_audit, ["spatial_finite_correlation_fraction"])
    )
    inlet_correlation_sample_count = as_int(
        get_any(inlet_correlation_audit, ["sample_count"])
    )
    inlet_correlation_adjacent_pair_count = as_int(
        get_any(inlet_correlation_audit, ["adjacent_pair_count"])
    )
    metric_inlet_correlation_audit = str(
        get_any(metrics, ["inlet_correlation_audit", "InletCorrelationAudit"]) or ""
    ).strip()
    inlet_correlation_gate = str(
        get_any(inlet_correlation_audit, ["inlet_correlation_gate"])
        or ""
    ).strip().lower()
    inlet_temporal_lag1 = as_float(
        get_any(inlet_correlation_audit, ["temporal_lag1_mean_correlation"])
    )
    inlet_temporal_lag1_abs = as_float(
        get_any(inlet_correlation_audit, ["temporal_lag1_abs_mean_correlation"])
    )
    inlet_spatial_adjacent = as_float(
        get_any(inlet_correlation_audit, ["spatial_adjacent_mean_correlation"])
    )
    inlet_streamwise_variance = as_float(
        get_any(inlet_correlation_audit, ["mean_streamwise_fluctuation_variance"])
    )
    inlet_temporal_finite_fraction = as_float(
        get_any(inlet_correlation_audit, ["temporal_finite_correlation_fraction"])
    )
    inlet_spatial_finite_fraction = as_float(
        get_any(inlet_correlation_audit, ["spatial_finite_correlation_fraction"])
    )
    inlet_correlation_sample_count = as_int(
        get_any(inlet_correlation_audit, ["sample_count"])
    )
    inlet_correlation_adjacent_pair_count = as_int(
        get_any(inlet_correlation_audit, ["adjacent_pair_count"])
    )
    inlet_correlation_audit_exists = bool(inlet_correlation_audit_path and inlet_correlation_audit_path.exists())
    inlet_correlation_source_steps = get_first_available(
        get_any(inlet_correlation_audit, ["source_time_steps_csv", "source_time_steps"]),
    )
    inlet_correlation_source_count, inlet_correlation_source_step_text, inlet_correlation_has_source_steps = source_frame_details(
        {"source_time_steps": inlet_correlation_source_steps}
    )
    inlet_correlation_frame_count = as_int(
        get_any(inlet_correlation_audit, ["frame_count"])
    )
    inlet_correlation_declared_step_span = as_int(
        get_any(inlet_correlation_audit, ["source_step_span"])
    )
    inlet_correlation_selected_last_window = as_bool(
        get_any(inlet_correlation_audit, ["selected_last_window"])
    )
    inlet_correlation_steps_increasing = as_bool(
        get_any(inlet_correlation_audit, ["source_steps_strictly_increasing"])
    )
    inlet_correlation_spacing_uniform = as_bool(
        get_any(inlet_correlation_audit, ["source_step_spacing_uniform"])
    )
    inlet_correlation_steps, inlet_correlation_steps_error = parsed_source_steps(inlet_correlation_source_step_text)
    inlet_correlation_computed_step_span = (
        inlet_correlation_steps[-1] - inlet_correlation_steps[0]
        if len(inlet_correlation_steps) >= 2
        else None
    )
    inlet_correlation_step_span_matches = (
        inlet_correlation_declared_step_span is not None
        and inlet_correlation_computed_step_span is not None
        and inlet_correlation_declared_step_span == inlet_correlation_computed_step_span
    )
    inlet_correlation_step_span_long_enough = (
        inlet_correlation_computed_step_span is not None
        and inlet_correlation_computed_step_span >= args.min_avg_step_span
    )
    inlet_correlation_source_matches = (
        has_real_source_steps
        and parsed_steps_error is None
        and inlet_correlation_steps_error is None
        and inlet_correlation_steps == parsed_steps
    )
    inlet_correlation_vtk_hash_status = runtime_selected_vtk_hash_status(
        inlet_correlation_audit,
        inlet_correlation_audit_path,
        inlet_correlation_source_step_text,
    )
    inlet_correlation_source_hashes = inlet_correlation_vtk_hash_status["actual_hashes"]
    inlet_correlation_source_hash_text = inlet_correlation_vtk_hash_status["actual_hash_text"]
    inlet_correlation_source_hash_matches = (
        inlet_correlation_vtk_hash_status["ok"]
        and bool(expected_source_hashes)
        and bool(inlet_correlation_source_hashes)
        and inlet_correlation_source_hashes == expected_source_hashes
    )
    add_gate(
        gates,
        "inlet_correlation_vtk_hash_traceability",
        PASS if inlet_correlation_source_hash_matches else FAIL,
        (
            f"selected_file_count={inlet_correlation_vtk_hash_status['selected_file_count']}; "
            f"expected_step_count={inlet_correlation_vtk_hash_status['expected_step_count']}; "
            f"path_missing_count={inlet_correlation_vtk_hash_status['path_missing_count']}; "
            f"missing_file_count={inlet_correlation_vtk_hash_status['missing_file_count']}; "
            f"hash_mismatch_count={inlet_correlation_vtk_hash_status['hash_mismatch_count']}; "
            f"declared_hashes={inlet_correlation_vtk_hash_status['declared_hash_text'] or 'missing'}; "
            f"actual_hashes={inlet_correlation_vtk_hash_status['actual_hash_text'] or 'missing'}; "
            f"runtime_expected_hashes={expected_source_hash_text or 'missing'}; "
            f"source_hash_matches_runtime={inlet_correlation_source_hash_matches}; "
            f"error={inlet_correlation_vtk_hash_status['error'] or 'none'}; "
            f"inlet_correlation_audit={inlet_correlation_audit_path or 'missing'}"
        ),
        "Regenerate the inlet-correlation audit from the current final-window VTK files; copied correlation JSON cannot provide turbulent-inlet evidence.",
    )
    inlet_correlation_window_ok = (
        inlet_correlation_has_source_steps
        and inlet_correlation_source_matches
        and inlet_correlation_source_hash_matches
        and inlet_correlation_frame_count is not None
        and inlet_correlation_source_count is not None
        and inlet_correlation_frame_count == inlet_correlation_source_count
        and inlet_correlation_frame_count >= args.min_avg_frames
        and inlet_correlation_selected_last_window is True
        and inlet_correlation_steps_increasing is True
        and inlet_correlation_spacing_uniform is True
        and inlet_correlation_step_span_matches
        and inlet_correlation_step_span_long_enough
    )
    inlet_correlation_coverage_ok = (
        inlet_temporal_finite_fraction is not None
        and inlet_temporal_finite_fraction >= args.min_inlet_temporal_finite_fraction
        and inlet_spatial_finite_fraction is not None
        and inlet_spatial_finite_fraction >= args.min_inlet_spatial_finite_fraction
        and inlet_correlation_sample_count is not None
        and inlet_correlation_sample_count >= args.min_inlet_correlation_sample_count
        and inlet_correlation_adjacent_pair_count is not None
        and inlet_correlation_adjacent_pair_count >= args.min_inlet_correlation_adjacent_pair_count
    )
    inlet_correlation_values_ok = (
        inlet_streamwise_variance is not None
        and inlet_streamwise_variance > args.min_inlet_streamwise_variance
        and inlet_temporal_lag1 is not None
        and inlet_temporal_lag1 >= args.min_inlet_temporal_lag1_correlation
        and inlet_spatial_adjacent is not None
        and inlet_spatial_adjacent >= args.min_inlet_spatial_adjacent_correlation
        and inlet_temporal_integral_lag_count is not None
        and inlet_temporal_integral_lag_count >= args.min_inlet_temporal_integral_lag_count
        and inlet_spatial_integral_lag_count is not None
        and inlet_spatial_integral_lag_count >= args.min_inlet_spatial_integral_lag_count
        and inlet_k_variance_gate == "pass"
    )
    add_gate(
        gates,
        "inlet_correlation",
        PASS
        if inlet_correlation_gate == "pass"
        and inlet_correlation_audit_exists
        and inlet_correlation_window_ok
        and inlet_correlation_coverage_ok
        and inlet_correlation_values_ok
        else FAIL,
        (
            f"inlet_correlation_gate={inlet_correlation_gate or 'missing'}; "
            f"temporal_lag1_mean_correlation={inlet_temporal_lag1}; "
            f"required >= {args.min_inlet_temporal_lag1_correlation}; "
            f"temporal_lag1_abs_mean_correlation={inlet_temporal_lag1_abs}; "
            f"spatial_adjacent_mean_correlation={inlet_spatial_adjacent}; "
            f"required >= {args.min_inlet_spatial_adjacent_correlation}; "
            f"temporal_integral_positive_lag_count={inlet_temporal_integral_lag_count}; "
            f"required >= {args.min_inlet_temporal_integral_lag_count}; "
            f"temporal_integral_time_steps={inlet_temporal_integral_time_steps}; "
            f"spatial_integral_positive_lag_count={inlet_spatial_integral_lag_count}; "
            f"required >= {args.min_inlet_spatial_integral_lag_count}; "
            f"spatial_integral_length_m={inlet_spatial_integral_length_m}; "
            f"mean_streamwise_fluctuation_variance={inlet_streamwise_variance}; "
            f"required > {args.min_inlet_streamwise_variance}; "
            f"inlet_k_variance_gate={inlet_k_variance_gate or 'missing'}; "
            f"inlet_streamwise_variance_target_from_k={inlet_streamwise_variance_target}; "
            f"inlet_streamwise_variance_to_k_ratio={inlet_streamwise_variance_to_k_ratio}; "
            f"temporal_finite_correlation_fraction={inlet_temporal_finite_fraction}; "
            f"required >= {args.min_inlet_temporal_finite_fraction}; "
            f"spatial_finite_correlation_fraction={inlet_spatial_finite_fraction}; "
            f"required >= {args.min_inlet_spatial_finite_fraction}; "
            f"inlet_correlation_sample_count={inlet_correlation_sample_count}; "
            f"required >= {args.min_inlet_correlation_sample_count}; "
            f"inlet_correlation_adjacent_pair_count={inlet_correlation_adjacent_pair_count}; "
            f"required >= {args.min_inlet_correlation_adjacent_pair_count}; "
            f"inlet_correlation_source_time_steps={inlet_correlation_source_step_text or 'missing'}; "
            f"expected_source_time_steps={source_step_text or 'missing'}; "
            f"expected_source_hashes={expected_source_hash_text or 'missing'}; "
            f"inlet_correlation_source_matches={inlet_correlation_source_matches}; "
            f"inlet_correlation_source_hashes={inlet_correlation_source_hash_text or 'missing'}; "
            f"inlet_correlation_source_hash_matches={inlet_correlation_source_hash_matches}; "
            f"inlet_correlation_frame_count={inlet_correlation_frame_count}; required >= {args.min_avg_frames}; "
            f"inlet_correlation_source_count={inlet_correlation_source_count}; "
            f"inlet_correlation_declared_step_span={inlet_correlation_declared_step_span}; "
            f"inlet_correlation_computed_step_span={inlet_correlation_computed_step_span}; "
            f"inlet_correlation_step_span_matches={inlet_correlation_step_span_matches}; "
            f"inlet_correlation_step_span_long_enough={inlet_correlation_step_span_long_enough}; "
            f"required_step_span >= {args.min_avg_step_span}; "
            f"inlet_correlation_selected_last_window={inlet_correlation_selected_last_window}; "
            f"inlet_correlation_source_steps_strictly_increasing={inlet_correlation_steps_increasing}; "
            f"inlet_correlation_source_step_spacing_uniform={inlet_correlation_spacing_uniform}; "
            f"inlet_correlation_source_steps_error={inlet_correlation_steps_error or 'none'}; "
            f"correlation_values_source=audit_json_only; "
            f"audit={inlet_correlation_audit_path or 'missing'}; "
            f"audit_exists={inlet_correlation_audit_exists}; "
            f"metrics_inlet_correlation_audit={metric_inlet_correlation_audit or 'ignored'}; "
            f"metrics_temporal_integral_lag_count={get_any(metrics, ['inlet_temporal_integral_positive_lag_count']) or 'ignored'}; "
            f"metrics_spatial_integral_lag_count={get_any(metrics, ['inlet_spatial_integral_positive_lag_count']) or 'ignored'}"
        ),
        "Run scripts/audit_inlet_correlation_from_vtk.py on real final-window inlet VTK frames; RMS/k alone is not enough to prove correlated turbulent inflow.",
    )

    inlet_length_status = protocol_status(items, "inlet_turbulence_length_scale")
    metadata_inlet_length_source = str(metadata.get("SyntheticTurbulentInletLengthScaleSource") or "")
    metadata_inlet_length_gate = str(metadata.get("SyntheticTurbulentInletLengthScaleGate") or "").strip().lower()
    inlet_length_source = metadata_inlet_length_source
    inlet_length_gate = metadata_inlet_length_gate
    synthetic_corr_length_m = as_float(
        metadata.get("SyntheticTurbulenceCorrelationLengthM")
    )
    length_scale_supported = any(
        token in inlet_length_source.lower()
        for token in [
            "aij_length_scale_verified",
            "official_length_scale_verified",
            "precursor_length_scale",
            "recycling_length_scale",
            "digital_filter_length_scale",
            "digital-filter_length_scale",
            "synthetic_eddy_length_scale",
            "synthetic-eddy_length_scale",
            "sem_length_scale",
            "dfm_length_scale",
            "validated_length_scale_model",
        ]
    )
    length_gate_pass = (
        inlet_length_status == "pass"
        and inlet_length_gate == "pass"
        and length_scale_supported
        and inlet_source_evidence_ok
        and audit_has_inlet_length_scale_evidence is True
        and synthetic_corr_length_m is not None
        and synthetic_corr_length_m > 0.0
    )
    add_gate(
        gates,
        "inlet_length_scale",
        PASS if length_gate_pass else FAIL,
        (
            f"protocol_status={inlet_length_status or 'missing'}; "
            f"metadata_source={inlet_length_source or 'missing'}; "
            f"metadata_gate={inlet_length_gate or 'missing'}; "
            f"synthetic_correlation_length_m={synthetic_corr_length_m}; "
            f"length_scale_source_supported={length_scale_supported}; "
            f"inlet_source_evidence_ok={inlet_source_evidence_ok}; "
            f"audit_has_length_scale_evidence={audit_has_inlet_length_scale_evidence}; "
            f"inlet_source_audit={inlet_source_audit_path or 'missing'}; "
            f"metrics_inlet_length_scale_source={get_any(metrics, ['inlet_length_scale_source', 'SyntheticTurbulentInletLengthScaleSource']) or 'ignored'}; "
            f"metrics_inlet_length_scale_gate={get_any(metrics, ['inlet_length_scale_gate', 'SyntheticTurbulentInletLengthScaleGate']) or 'ignored'}; "
            f"metrics_synthetic_correlation_length_m={get_any(metrics, ['synthetic_correlation_length_m', 'SyntheticTurbulenceCorrelationLengthM']) or 'ignored'}"
        ),
        "Use AIJ-documented turbulence length scales, a precursor/recycling field, or a validated DFM/SEM length-scale model backed by current setup.cpp source-audit evidence; a user-selected STG correlation length is diagnostic only.",
    )

    synthetic_injected = as_bool(
        get_any(metadata, ["SyntheticTurbulentInletInjected", "SyntheticInletInjected"])
    )
    metadata_temporal_sampling_gate = str(
        get_any(metadata, ["SyntheticTurbulentInletTemporalSamplingGate"]) or ""
    ).strip().lower()
    metrics_temporal_sampling_gate = str(
        get_any(metrics, ["synthetic_temporal_sampling_gate", "SyntheticTurbulentInletTemporalSamplingGate"]) or ""
    ).strip().lower()
    metadata_stg_refresh_count = as_int(
        get_any(metadata, ["SyntheticTurbulenceExpectedFinalWindowRefreshCount"])
    )
    metrics_stg_refresh_count = as_int(
        get_any(metrics, ["synthetic_expected_final_window_refresh_count", "SyntheticTurbulenceExpectedFinalWindowRefreshCount"])
    )
    metadata_stg_refresh_minimum = as_int(
        get_any(metadata, ["SyntheticTurbulenceMinimumRecommendedRefreshes"])
    )
    metrics_stg_refresh_minimum = as_int(
        get_any(metrics, ["synthetic_minimum_recommended_refresh_count", "SyntheticTurbulenceMinimumRecommendedRefreshes"])
    )
    temporal_sampling_not_applicable = synthetic_injected is not True
    temporal_sampling_pass = (
        temporal_sampling_not_applicable
        or (
            metadata_temporal_sampling_gate == "pass"
            and metrics_temporal_sampling_gate == "pass"
            and metadata_stg_refresh_count is not None
            and metadata_stg_refresh_minimum is not None
            and metadata_stg_refresh_count >= metadata_stg_refresh_minimum
            and metrics_stg_refresh_count == metadata_stg_refresh_count
            and metrics_stg_refresh_minimum == metadata_stg_refresh_minimum
        )
    )
    add_gate(
        gates,
        "inlet_temporal_sampling",
        PASS if temporal_sampling_pass else FAIL,
        (
            f"synthetic_injected={synthetic_injected}; "
            f"metadata_temporal_sampling_gate={metadata_temporal_sampling_gate or 'missing'}; "
            f"metrics_temporal_sampling_gate={metrics_temporal_sampling_gate or 'missing'}; "
            f"metadata_stg_refresh_count={metadata_stg_refresh_count}; "
            f"metadata_stg_refresh_minimum={metadata_stg_refresh_minimum}; "
            f"metrics_stg_refresh_count={metrics_stg_refresh_count}; "
            f"metrics_stg_refresh_minimum={metrics_stg_refresh_minimum}; "
            f"not_applicable={temporal_sampling_not_applicable}"
        ),
        "For STG-lite validation, the final averaged VTK window must sample enough inlet-pattern refreshes; otherwise increase TimeSteps, reduce STG Update, or keep the run diagnostic-only.",
    )

    metrics_native_id = str(get_any(metrics, ["native_fluidx3d_baseline_id"]) or "").strip()
    manifest_native_id = str(manifest.get("BaselineId") or "").strip()
    native_id = metrics_native_id or manifest_native_id
    native_id_matches_manifest = (
        bool(metrics_native_id)
        and bool(manifest_native_id)
        and metrics_native_id == manifest_native_id
    )
    native_status = protocol_status(items, "native_fluidx3d_baseline")
    native_path_explicit = as_bool(manifest.get("NativeFluidX3DPathExplicitlyProvided"))
    native_source_validation = manifest.get("NativeFluidX3DSourceValidation", {})
    if not isinstance(native_source_validation, dict):
        native_source_validation = {}
    native_source_valid = as_bool(native_source_validation.get("IsValid"))
    native_source_hash_roles = [
        "Native FluidX3D original setup",
        "Native FluidX3D original defines",
        "Native FluidX3D lbm.hpp",
        "Native FluidX3D lbm.cpp",
    ]
    native_source_hash_statuses = [
        manifest_source_hash_status(manifest, role, manifest_path) for role in native_source_hash_roles
    ]
    native_source_root_status = native_manifest_source_root_status(manifest, manifest_path)
    native_source_hashes_ok = all(
        as_bool(status.get("ok")) is True for status in native_source_hash_statuses
    )
    native_source_hash_failure_reasons = [
        f"{status.get('role')}:{status.get('reason')}"
        for status in native_source_hash_statuses
        if as_bool(status.get("ok")) is not True
    ]
    native_preconditions_gate = str(
        get_any(native_preconditions_audit, ["native_preconditions_gate"]) or ""
    ).strip().lower()
    native_preconditions_reasons = str(
        get_any(native_preconditions_audit, ["native_preconditions_gate_reasons_csv", "native_preconditions_gate_reasons"]) or ""
    )
    native_preconditions_protocol_gate = str(
        get_any(native_preconditions_audit, ["native_preconditions_protocol_identity_gate"]) or ""
    ).strip().lower()
    native_preconditions_time_gate = str(
        get_any(native_preconditions_audit, ["native_preconditions_time_average_gate"]) or ""
    ).strip().lower()
    native_top_blocking_priority_key = str(
        get_any(native_preconditions_audit, ["native_top_blocking_priority_key"]) or ""
    ).strip()
    native_top_blocking_priority_diagnosis = str(
        get_any(native_preconditions_audit, ["native_top_blocking_priority_diagnosis"]) or ""
    ).strip()
    native_top_blocking_priority_next_action = str(
        get_any(native_preconditions_audit, ["native_top_blocking_priority_next_action"]) or ""
    ).strip()
    native_precondition_closure_gate = str(
        get_any(native_preconditions_audit, ["native_precondition_closure_gate"]) or ""
    ).strip().lower()
    native_precondition_failed_stage_count = as_int(
        get_any(native_preconditions_audit, ["native_precondition_failed_stage_count"])
    )
    native_precondition_failed_stage_keys = str(
        get_any(
            native_preconditions_audit,
            ["native_precondition_failed_stage_keys_csv", "native_precondition_failed_stage_keys"],
        )
        or ""
    ).strip()
    native_precondition_top_blocking_stage_key = str(
        get_any(native_preconditions_audit, ["native_precondition_top_blocking_stage_key"]) or ""
    ).strip()
    native_preconditions_inlet_source_gate = str(
        get_any(native_preconditions_audit, ["inlet_source_gate"]) or ""
    ).strip().lower()
    native_preconditions_paper_inlet_gate = str(
        get_any(native_preconditions_audit, ["paper_grade_inlet_source_gate"]) or ""
    ).strip().lower()
    native_preconditions_inlet_distribution_consistent = as_bool(
        get_any(native_preconditions_audit, ["inlet_source_distribution_consistent"])
    )
    native_preconditions_inlet_velocity_only = as_bool(
        get_any(native_preconditions_audit, ["inlet_source_velocity_field_only"])
    )
    native_preconditions_inlet_profile_gate = str(
        get_any(native_preconditions_audit, ["inlet_profile_gate"]) or ""
    ).strip().lower()
    native_preconditions_inlet_u_profile_gate = str(
        get_any(native_preconditions_audit, ["inlet_u_profile_gate"]) or ""
    ).strip().lower()
    native_preconditions_inlet_k_profile_gate = str(
        get_any(native_preconditions_audit, ["inlet_k_profile_gate"]) or ""
    ).strip().lower()
    native_preconditions_inlet_correlation_gate = str(
        get_any(native_preconditions_audit, ["inlet_correlation_gate"]) or ""
    ).strip().lower()
    native_preconditions_inlet_k_variance_gate = str(
        get_any(native_preconditions_audit, ["inlet_k_variance_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_source_gate = str(
        get_any(native_preconditions_audit, ["boundary_source_gate"]) or ""
    ).strip().lower()
    native_preconditions_paper_boundary_gate = str(
        get_any(native_preconditions_audit, ["paper_grade_boundary_source_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_equivalent = as_bool(
        get_any(native_preconditions_audit, ["boundary_source_wind_tunnel_equivalent"])
    )
    native_preconditions_boundary_fidelity_class = str(
        get_any(native_preconditions_audit, ["boundary_source_fidelity_class"]) or ""
    ).strip()
    native_preconditions_boundary_complete_evidence = as_bool(
        get_any(native_preconditions_audit, ["boundary_source_has_complete_wind_tunnel_evidence"])
    )
    native_preconditions_boundary_empty_stub_only = as_bool(
        get_any(native_preconditions_audit, ["boundary_source_has_empty_advanced_method_stub_only"])
    )
    native_preconditions_boundary_simplified = as_bool(
        get_any(native_preconditions_audit, ["boundary_source_simplified"])
    )
    native_preconditions_boundary_protocol_gate = str(
        get_any(native_preconditions_audit, ["boundary_protocol_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_evidence_gate = str(
        get_any(native_preconditions_audit, ["boundary_evidence_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_traceability_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_traceability_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_profile_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_profile_preservation_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_inlet_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_inlet_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_side_top_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_side_top_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_side_top_normal_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_side_top_normal_leakage_gate"]) or ""
    ).strip().lower()
    native_preconditions_boundary_runtime_outlet_gate = str(
        get_any(native_preconditions_audit, ["boundary_runtime_outlet_gate"]) or ""
    ).strip().lower()
    native_boundary_expected_case = str(args.case or "").strip()
    native_boundary_expected_wind_direction = str(
        get_any(metrics, ["wind_direction", "WindDirection", "Wind_direction"]) or ""
    ).strip()
    native_preconditions_probe_row_count = as_int(
        get_any(native_preconditions_audit, ["probe_audit_row_count"])
    )
    native_preconditions_probe_failed_count = as_int(
        get_any(native_preconditions_audit, ["probe_audit_failed_row_count"])
    )
    native_preconditions_probe_components = {
        component.strip().lower()
        for component in as_string_list(
            get_any(native_preconditions_audit, ["probe_audit_compared_components"])
        )
        if component.strip()
    }
    native_preconditions_expected_component = str(
        get_any(native_preconditions_audit, ["expected_compared_component"]) or ""
    ).strip().lower()
    required_compared_component = str(
        args.expected_compared_component or native_preconditions_expected_component or ""
    ).strip().lower()
    native_preconditions_component_gate = str(
        get_any(native_preconditions_audit, ["component_normalization_gate"]) or ""
    ).strip().lower()
    native_preconditions_component_sensitivity_gate = str(
        get_any(native_preconditions_audit, ["component_sensitivity_gate"]) or ""
    ).strip().lower()
    native_preconditions_normalization_scale_gate = str(
        get_any(native_preconditions_audit, ["normalization_scale_gate"]) or ""
    ).strip().lower()
    native_preconditions_streamwise_sign_gate = str(
        get_any(native_preconditions_audit, ["streamwise_sign_gate"]) or ""
    ).strip().lower()
    native_preconditions_id = str(
        get_any(native_preconditions_audit, ["baseline_id", "BaselineId"]) or ""
    ).strip()
    current_manifest_sha256 = sha256_file(manifest_path).lower()
    native_preconditions_manifest_sha256 = str(
        get_any(native_preconditions_audit, ["native_preconditions_manifest_sha256"]) or ""
    ).strip().lower()
    native_preconditions_manifest_hash_matches = (
        bool(current_manifest_sha256)
        and bool(native_preconditions_manifest_sha256)
        and current_manifest_sha256 == native_preconditions_manifest_sha256
    )
    native_preconditions_id_matches = (
        bool(manifest_native_id)
        and bool(native_preconditions_id)
        and manifest_native_id == native_preconditions_id
    )
    native_inlet_traceability = native_inlet_precondition_traceability_status(
        native_preconditions_audit,
        args.min_avg_step_span,
        args.uref_tolerance,
    )
    add_gate(
        gates,
        "native_inlet_precondition_traceability",
        PASS if native_inlet_traceability["ok"] else FAIL,
        (
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"reasons={native_inlet_traceability['reasons_csv'] or 'none'}; "
            f"inlet_profile_gate={native_preconditions_inlet_profile_gate or 'missing'}; "
            f"inlet_u_profile_gate={native_preconditions_inlet_u_profile_gate or 'missing'}; "
            f"inlet_k_profile_gate={native_preconditions_inlet_k_profile_gate or 'missing'}; "
            f"inlet_profile_time_averaging_gate={get_any(native_preconditions_audit, ['inlet_profile_time_averaging_gate']) or 'missing'}; "
            f"expected_uref_mps={get_any(native_preconditions_audit, ['expected_uref_mps'])}; "
            f"actual_uref_mps={get_any(native_preconditions_audit, ['actual_uref_mps'])}; "
            f"expected_zref_m={get_any(native_preconditions_audit, ['expected_zref_m'])}; "
            f"af_uref_at_zref_mps={get_any(native_preconditions_audit, ['af_uref_at_zref_mps'])}; "
            f"uref_af_profile_delta_mps={get_any(native_preconditions_audit, ['uref_af_profile_delta_mps'])}; "
            f"metadata_uref_af_profile_delta_mps={get_any(native_preconditions_audit, ['metadata_uref_af_profile_delta_mps'])}; "
            f"uref_tolerance={args.uref_tolerance}; "
            f"inlet_profile_af_csv_sha256_matches_expected={get_any(native_preconditions_audit, ['inlet_profile_af_csv_sha256_matches_expected'])}; "
            f"inlet_profile_source_time_steps_match_runtime={get_any(native_preconditions_audit, ['inlet_profile_source_time_steps_match_runtime'])}; "
            f"inlet_profile_source_vtk_sha256_match_runtime={get_any(native_preconditions_audit, ['inlet_profile_source_vtk_sha256_match_runtime'])}; "
            f"inlet_profile_source_step_span={get_any(native_preconditions_audit, ['inlet_profile_source_step_span'])}; "
            f"inlet_correlation_gate={native_preconditions_inlet_correlation_gate or 'missing'}; "
            f"inlet_k_variance_gate={native_preconditions_inlet_k_variance_gate or 'missing'}; "
            f"inlet_streamwise_variance_target_from_k={get_any(native_preconditions_audit, ['inlet_streamwise_variance_target_from_k'])}; "
            f"inlet_streamwise_variance_to_k_ratio={get_any(native_preconditions_audit, ['inlet_streamwise_variance_to_k_ratio'])}; "
            f"inlet_correlation_source_time_steps_match_runtime={get_any(native_preconditions_audit, ['inlet_correlation_source_time_steps_match_runtime'])}; "
            f"inlet_correlation_source_vtk_sha256_match_runtime={get_any(native_preconditions_audit, ['inlet_correlation_source_vtk_sha256_match_runtime'])}; "
            f"inlet_correlation_source_step_span={get_any(native_preconditions_audit, ['inlet_correlation_source_step_span'])}; "
            f"required_min_avg_step_span={args.min_avg_step_span}"
        ),
        "Regenerate native inlet profile and inlet correlation audits from the same runtime-selected final VTK window, with matching AF CSV hash, VTK hashes, increasing/uniform source steps and sufficient solver-step span.",
    )
    native_probe_traceability = native_probe_component_traceability_status(
        native_preconditions_audit,
        args.min_avg_step_span,
    )
    add_gate(
        gates,
        "native_probe_component_traceability",
        PASS if native_probe_traceability["ok"] else FAIL,
        (
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"probe_component_fidelity_class={native_probe_traceability['probe_component_fidelity_class'] or 'missing'}; "
            f"reasons={native_probe_traceability['reasons_csv'] or 'none'}; "
            f"probe_audit_row_count={native_preconditions_probe_row_count}; "
            f"probe_audit_failed_row_count={native_preconditions_probe_failed_count}; "
            f"official_probe_coverage_ratio={get_any(native_preconditions_audit, ['official_probe_coverage_ratio'])}; "
            f"probe_max_official_coordinate_delta_m={get_any(native_preconditions_audit, ['probe_max_official_coordinate_delta_m'])}; "
            f"probe_official_coordinate_delta_violation_count={get_any(native_preconditions_audit, ['probe_official_coordinate_delta_violation_count'])}; "
            f"probe_source_time_steps_match_runtime={get_any(native_preconditions_audit, ['probe_source_time_steps_match_runtime'])}; "
            f"probe_source_vtk_sha256_match_runtime={get_any(native_preconditions_audit, ['probe_source_vtk_sha256_match_runtime'])}; "
            f"probe_source_step_span={get_any(native_preconditions_audit, ['probe_source_step_span'])}; "
            f"component_normalization_gate={native_preconditions_component_gate or 'missing'}; "
            f"component_sensitivity_gate={native_preconditions_component_sensitivity_gate or 'missing'}; "
            f"normalization_scale_gate={native_preconditions_normalization_scale_gate or 'missing'}; "
            f"streamwise_sign_gate={native_preconditions_streamwise_sign_gate or 'missing'}; "
            f"component_source_window_gate={get_any(native_preconditions_audit, ['component_source_window_gate']) or 'missing'}; "
            f"component_sensitivity_hash_traceability_gate={get_any(native_preconditions_audit, ['component_sensitivity_hash_traceability_gate']) or 'missing'}; "
            f"component_sensitivity_probe_audit_sha256_matches_current={get_any(native_preconditions_audit, ['component_sensitivity_probe_audit_sha256_matches_current'])}; "
            f"component_sensitivity_official_sha256_matches_current={get_any(native_preconditions_audit, ['component_sensitivity_official_sha256_matches_current'])}; "
            f"component_source_step_span={get_any(native_preconditions_audit, ['component_source_step_span'])}; "
            f"required_min_avg_step_span={args.min_avg_step_span}"
        ),
        "Regenerate probe_audit.csv and component_sensitivity_audit.json from the same final VTK window, with official probe IDs, official coordinates, Uref, wind vector, compared component, tolerance and source hashes closed.",
    )
    native_boundary_traceability = native_boundary_traceability_status(
        native_preconditions_audit,
        expected_case=native_boundary_expected_case,
        expected_wind_direction=native_boundary_expected_wind_direction,
        min_avg_frames=args.min_avg_frames,
        min_avg_step_span=args.min_avg_step_span,
    )
    add_gate(
        gates,
        "native_boundary_traceability",
        PASS if native_boundary_traceability["ok"] else FAIL,
        (
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"reasons={native_boundary_traceability['reasons_csv'] or 'none'}; "
            f"boundary_source_gate={native_preconditions_boundary_source_gate or 'missing'}; "
            f"paper_grade_boundary_source_gate={native_preconditions_paper_boundary_gate or 'missing'}; "
            f"boundary_source_wind_tunnel_equivalent={native_preconditions_boundary_equivalent}; "
            f"boundary_source_fidelity_class={native_preconditions_boundary_fidelity_class or 'missing'}; "
            f"boundary_source_has_complete_wind_tunnel_evidence={native_preconditions_boundary_complete_evidence}; "
            f"boundary_source_has_empty_advanced_method_stub_only={native_preconditions_boundary_empty_stub_only}; "
            f"boundary_source_simplified={native_preconditions_boundary_simplified}; "
            f"boundary_source_setup_cpp_sha256_matches_current={get_any(native_preconditions_audit, ['boundary_source_setup_cpp_sha256_matches_current'])}; "
            f"boundary_protocol_gate={native_preconditions_boundary_protocol_gate or 'missing'}; "
            f"boundary_evidence_gate={native_preconditions_boundary_evidence_gate or 'missing'}; "
            f"boundary_runtime_gate={native_preconditions_boundary_runtime_gate or 'missing'}; "
            f"boundary_runtime_traceability_gate={native_preconditions_boundary_runtime_traceability_gate or 'missing'}; "
            f"boundary_runtime_profile_preservation_gate={native_preconditions_boundary_runtime_profile_gate or 'missing'}; "
            f"boundary_runtime_inlet_gate={native_preconditions_boundary_runtime_inlet_gate or 'missing'}; "
            f"boundary_runtime_side_top_gate={native_preconditions_boundary_runtime_side_top_gate or 'missing'}; "
            f"boundary_runtime_side_top_normal_leakage_gate={native_preconditions_boundary_runtime_side_top_normal_gate or 'missing'}; "
            f"boundary_runtime_outlet_gate={native_preconditions_boundary_runtime_outlet_gate or 'missing'}; "
            f"boundary_runtime_max_u_mae_ratio={get_any(native_preconditions_audit, ['boundary_runtime_max_u_mae_ratio'])}; "
            f"boundary_runtime_max_side_top_normal_velocity_ratio={get_any(native_preconditions_audit, ['boundary_runtime_max_side_top_normal_velocity_ratio'])}; "
            f"boundary_runtime_frame_count={get_any(native_preconditions_audit, ['boundary_runtime_frame_count'])}; "
            f"boundary_runtime_source_step_span={get_any(native_preconditions_audit, ['boundary_runtime_source_step_span'])}; "
            f"boundary_runtime_selected_last_window={get_any(native_preconditions_audit, ['boundary_runtime_selected_last_window'])}; "
            f"boundary_runtime_source_vtk_sha256_count={get_any(native_preconditions_audit, ['boundary_runtime_source_vtk_sha256_count'])}; "
            f"boundary_runtime_source_vtk_sha256_unique_count={get_any(native_preconditions_audit, ['boundary_runtime_source_vtk_sha256_unique_count'])}; "
            f"boundary_run_identity_gate={get_any(native_preconditions_audit, ['boundary_run_identity_gate']) or 'missing'}; "
            f"boundary_evidence_metadata_sha256_matches_current={get_any(native_preconditions_audit, ['boundary_evidence_metadata_sha256_matches_current'])}; "
            f"boundary_evidence_files_all_hashed={get_any(native_preconditions_audit, ['boundary_evidence_files_all_hashed'])}; "
            f"boundary_equivalence_supported={get_any(native_preconditions_audit, ['boundary_equivalence_supported'])}; "
            f"boundary_evidence_class_supported={get_any(native_preconditions_audit, ['boundary_evidence_class_supported'])}; "
            f"boundary_condition_fields_supported={get_any(native_preconditions_audit, ['boundary_condition_fields_supported'])}; "
            f"boundary_required_support_fields_missing_or_false={get_any(native_preconditions_audit, ['boundary_required_support_fields_missing_or_false_csv']) or 'none'}; "
            f"boundary_evidence_aij_case={get_any(native_preconditions_audit, ['boundary_evidence_aij_case']) or 'missing'}; "
            f"expected_case={native_boundary_expected_case or 'not_set'}; "
            f"boundary_evidence_wind_direction={get_any(native_preconditions_audit, ['boundary_evidence_wind_direction']) or 'missing'}; "
            f"expected_wind_direction={native_boundary_expected_wind_direction or 'not_set'}"
        ),
        "Regenerate boundary_source_audit.json and boundary_protocol_audit.json from the current native setup, with AIJ-equivalent outlet/side/top/floor/roughness/fetch evidence, current metadata hash and hashed support files.",
    )
    native_time_traceability = native_time_averaging_traceability_status(
        native_preconditions_audit,
        args.min_avg_frames,
        args.min_avg_step_span,
    )
    add_gate(
        gates,
        "native_time_averaging_traceability",
        PASS if native_time_traceability["ok"] else FAIL,
        (
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"reasons={native_time_traceability['reasons_csv'] or 'none'}; "
            f"native_preconditions_time_average_gate={native_preconditions_time_gate or 'missing'}; "
            f"native_preconditions_time_average_evidence_gate={native_time_traceability['native_preconditions_time_average_evidence_gate'] or 'missing'}; "
            f"runtime_reported_time_averaging_gate={native_time_traceability['runtime_reported_time_averaging_gate'] or 'missing'}; "
            f"runtime_time_averaging_gate={native_time_traceability['runtime_time_averaging_gate'] or 'missing'}; "
            f"runtime_requested_vtk_frame_gate={native_time_traceability['runtime_requested_vtk_frame_gate'] or 'missing'}; "
            f"runtime_final_window_frame_count_gate={native_time_traceability['runtime_final_window_frame_count_gate'] or 'missing'}; "
            f"planned_frame_count_min={native_time_traceability['planned_frame_count_min']}; "
            f"runtime_average_last_n={native_time_traceability['runtime_average_last_n']}; "
            f"runtime_source_frame_count={native_time_traceability['runtime_source_frame_count']}; "
            f"runtime_source_step_span={native_time_traceability['runtime_source_step_span']}; "
            f"runtime_source_step_span_from_time_steps={native_time_traceability['runtime_source_step_span_from_time_steps']}; "
            f"runtime_source_step_span_matches_time_steps={get_any(native_preconditions_audit, ['runtime_source_step_span_matches_time_steps'])}; "
            f"runtime_source_steps_strictly_increasing={get_any(native_preconditions_audit, ['runtime_source_steps_strictly_increasing'])}; "
            f"runtime_source_step_spacing_uniform={get_any(native_preconditions_audit, ['runtime_source_step_spacing_uniform'])}; "
            f"runtime_selected_last_window={native_time_traceability['runtime_selected_last_window']}; "
            f"runtime_source_vtk_sha256_count={native_time_traceability['runtime_source_vtk_sha256_count']}; "
            f"runtime_source_vtk_sha256_unique_count={native_time_traceability['runtime_source_vtk_sha256_unique_count']}; "
            f"planned_final_window_step_span={native_time_traceability['planned_final_window_step_span']}; "
            f"runtime_final_window_stationarity_gate={native_time_traceability['runtime_final_window_stationarity_gate'] or 'missing'}; "
            f"time_averaging_fidelity_class={native_time_traceability['time_averaging_fidelity_class'] or 'missing'}; "
            f"runtime_final_window_mean_speed_drift_ratio={native_time_traceability['runtime_final_window_mean_speed_drift_ratio']}; "
            f"runtime_max_final_window_mean_speed_drift_ratio={get_any(native_preconditions_audit, ['runtime_max_final_window_mean_speed_drift_ratio'])}; "
            f"required_min_avg_frames={args.min_avg_frames}; "
            f"required_min_avg_step_span={args.min_avg_step_span}"
        ),
        "Regenerate native runtime and precondition audits from a sufficiently long final VTK averaging window; four-frame or stale diagnostic windows cannot support paper-grade baseline evidence.",
    )
    native_preconditions_full_evidence_ok = (
        native_preconditions_audit_path is not None
        and native_inlet_traceability["ok"]
        and native_probe_traceability["ok"]
        and native_boundary_traceability["ok"]
        and native_time_traceability["ok"]
        and native_preconditions_inlet_source_gate == "pass"
        and native_preconditions_paper_inlet_gate == "pass"
        and native_preconditions_inlet_distribution_consistent is True
        and native_preconditions_inlet_velocity_only is False
        and native_preconditions_inlet_profile_gate == "pass"
        and native_preconditions_inlet_u_profile_gate == "pass"
        and native_preconditions_inlet_k_profile_gate == "pass"
        and native_preconditions_inlet_correlation_gate == "pass"
        and native_preconditions_inlet_k_variance_gate == "pass"
        and native_preconditions_boundary_source_gate == "pass"
        and native_preconditions_paper_boundary_gate == "pass"
        and native_preconditions_boundary_equivalent is True
        and native_preconditions_boundary_fidelity_class == "wind_tunnel_equivalent_complete"
        and native_preconditions_boundary_complete_evidence is True
        and native_preconditions_boundary_empty_stub_only is False
        and native_preconditions_boundary_simplified is False
        and native_preconditions_boundary_protocol_gate == "pass"
        and native_preconditions_boundary_evidence_gate == "pass"
        and native_preconditions_boundary_runtime_gate == "pass"
        and native_preconditions_boundary_runtime_traceability_gate == "pass"
        and native_preconditions_boundary_runtime_profile_gate == "pass"
        and native_preconditions_boundary_runtime_inlet_gate == "pass"
        and native_preconditions_boundary_runtime_side_top_gate == "pass"
        and native_preconditions_boundary_runtime_side_top_normal_gate == "pass"
        and native_preconditions_boundary_runtime_outlet_gate == "pass"
        and native_preconditions_probe_row_count is not None
        and native_preconditions_probe_row_count > 0
        and native_preconditions_probe_failed_count == 0
        and (
            not required_compared_component
            or required_compared_component in native_preconditions_probe_components
        )
        and native_preconditions_component_gate == "pass"
        and native_preconditions_component_sensitivity_gate == "pass"
        and native_preconditions_normalization_scale_gate == "pass"
        and native_preconditions_streamwise_sign_gate == "pass"
        and native_precondition_closure_gate == "pass"
        and native_precondition_failed_stage_count == 0
    )
    add_gate(
        gates,
        "native_preconditions_full_evidence",
        PASS if native_preconditions_full_evidence_ok else FAIL,
        (
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"inlet_source_gate={native_preconditions_inlet_source_gate or 'missing'}; "
            f"paper_grade_inlet_source_gate={native_preconditions_paper_inlet_gate or 'missing'}; "
            f"inlet_source_distribution_consistent={native_preconditions_inlet_distribution_consistent}; "
            f"inlet_source_velocity_field_only={native_preconditions_inlet_velocity_only}; "
            f"inlet_profile_gate={native_preconditions_inlet_profile_gate or 'missing'}; "
            f"inlet_u_profile_gate={native_preconditions_inlet_u_profile_gate or 'missing'}; "
            f"inlet_k_profile_gate={native_preconditions_inlet_k_profile_gate or 'missing'}; "
            f"inlet_correlation_gate={native_preconditions_inlet_correlation_gate or 'missing'}; "
            f"inlet_k_variance_gate={native_preconditions_inlet_k_variance_gate or 'missing'}; "
            f"native_inlet_traceability_ok={native_inlet_traceability['ok']}; "
            f"native_inlet_traceability_reasons={native_inlet_traceability['reasons_csv'] or 'none'}; "
            f"native_probe_traceability_ok={native_probe_traceability['ok']}; "
            f"native_probe_traceability_reasons={native_probe_traceability['reasons_csv'] or 'none'}; "
            f"native_boundary_traceability_ok={native_boundary_traceability['ok']}; "
            f"native_boundary_traceability_reasons={native_boundary_traceability['reasons_csv'] or 'none'}; "
            f"native_time_traceability_ok={native_time_traceability['ok']}; "
            f"native_time_traceability_reasons={native_time_traceability['reasons_csv'] or 'none'}; "
            f"boundary_source_gate={native_preconditions_boundary_source_gate or 'missing'}; "
            f"paper_grade_boundary_source_gate={native_preconditions_paper_boundary_gate or 'missing'}; "
            f"boundary_source_wind_tunnel_equivalent={native_preconditions_boundary_equivalent}; "
            f"boundary_source_fidelity_class={native_preconditions_boundary_fidelity_class or 'missing'}; "
            f"boundary_source_has_complete_wind_tunnel_evidence={native_preconditions_boundary_complete_evidence}; "
            f"boundary_source_has_empty_advanced_method_stub_only={native_preconditions_boundary_empty_stub_only}; "
            f"boundary_source_simplified={native_preconditions_boundary_simplified}; "
            f"boundary_protocol_gate={native_preconditions_boundary_protocol_gate or 'missing'}; "
            f"boundary_evidence_gate={native_preconditions_boundary_evidence_gate or 'missing'}; "
            f"boundary_runtime_gate={native_preconditions_boundary_runtime_gate or 'missing'}; "
            f"boundary_runtime_traceability_gate={native_preconditions_boundary_runtime_traceability_gate or 'missing'}; "
            f"boundary_runtime_profile_preservation_gate={native_preconditions_boundary_runtime_profile_gate or 'missing'}; "
            f"boundary_runtime_inlet_gate={native_preconditions_boundary_runtime_inlet_gate or 'missing'}; "
            f"boundary_runtime_side_top_gate={native_preconditions_boundary_runtime_side_top_gate or 'missing'}; "
            f"boundary_runtime_side_top_normal_leakage_gate={native_preconditions_boundary_runtime_side_top_normal_gate or 'missing'}; "
            f"boundary_runtime_outlet_gate={native_preconditions_boundary_runtime_outlet_gate or 'missing'}; "
            f"probe_audit_row_count={native_preconditions_probe_row_count}; "
            f"probe_audit_failed_row_count={native_preconditions_probe_failed_count}; "
            f"probe_audit_compared_components={';'.join(sorted(native_preconditions_probe_components)) or 'missing'}; "
            f"required_compared_component={required_compared_component or 'not_required'}; "
            f"component_normalization_gate={native_preconditions_component_gate or 'missing'}; "
            f"component_sensitivity_gate={native_preconditions_component_sensitivity_gate or 'missing'}; "
            f"normalization_scale_gate={native_preconditions_normalization_scale_gate or 'missing'}; "
            f"streamwise_sign_gate={native_preconditions_streamwise_sign_gate or 'missing'}; "
            f"native_precondition_closure_gate={native_precondition_closure_gate or 'missing'}; "
            f"native_precondition_failed_stage_count={native_precondition_failed_stage_count}; "
            f"native_precondition_failed_stage_keys={native_precondition_failed_stage_keys or 'none'}; "
            f"native_precondition_top_blocking_stage_key={native_precondition_top_blocking_stage_key or 'missing'}"
        ),
        "Regenerate native_preconditions_audit.json after inlet-source, inlet-profile/correlation, boundary, probe and component-normalization audits all pass; legacy summary-only native preconditions are not enough for paper-grade validation.",
    )
    native_preconditions_ok = (
        native_preconditions_audit_path is not None
        and native_preconditions_gate == "pass"
        and native_preconditions_protocol_gate == "pass"
        and native_preconditions_time_gate == "pass"
        and native_preconditions_id_matches
        and native_preconditions_manifest_hash_matches
        and native_preconditions_full_evidence_ok
    )
    native_manifest_ok = (
        native_path_explicit is True
        and native_source_valid is True
        and native_source_root_status["ok"]
        and native_source_hashes_ok
        and native_preconditions_ok
    )
    native_gate = "pass" if manifest_path is not None and native_manifest_ok else "fail"
    add_gate(
        gates,
        "native_baseline",
        PASS if native_id_matches_manifest and native_status == "pass" and native_gate == "pass" else FAIL,
        (
            f"native_fluidx3d_baseline_id={metrics_native_id or 'missing'}; "
            f"manifest_baseline_id={manifest_native_id or 'missing'}; "
            f"native_id_matches_manifest={native_id_matches_manifest}; "
            f"protocol_status={native_status or 'missing'}; native_baseline_gate={native_gate or 'missing'}; "
            f"NativeFluidX3DPathExplicitlyProvided={native_path_explicit}; "
            f"NativeFluidX3DSourceValidation.IsValid={native_source_valid}; "
            f"native_source_root={native_source_root_status['source_path'] or 'missing'}; "
            f"native_source_root_exists={native_source_root_status['source_path_exists']}; "
            f"native_source_root_has_build_file={native_source_root_status['has_build_file']}; "
            f"native_source_root_role_path_mismatch_count={native_source_root_status['required_role_path_mismatch_count']}; "
            f"native_source_root_missing_required_item_count={native_source_root_status['missing_required_item_count']}; "
            f"native_source_root_reasons={native_source_root_status['reason'] or 'none'}; "
            f"native_source_hashes_ok={native_source_hashes_ok}; "
            f"native_source_hash_failure_reasons={';'.join(native_source_hash_failure_reasons) or 'none'}; "
            f"native_preconditions_audit={native_preconditions_audit_path or 'missing'}; "
            f"native_preconditions_gate={native_preconditions_gate or 'missing'}; "
            f"native_preconditions_protocol_identity_gate={native_preconditions_protocol_gate or 'missing'}; "
            f"native_preconditions_time_average_gate={native_preconditions_time_gate or 'missing'}; "
            f"native_time_traceability_ok={native_time_traceability['ok']}; "
            f"native_time_traceability_reasons={native_time_traceability['reasons_csv'] or 'none'}; "
            f"native_top_blocking_priority_key={native_top_blocking_priority_key or 'missing'}; "
            f"native_top_blocking_priority_diagnosis={native_top_blocking_priority_diagnosis or 'missing'}; "
            f"native_top_blocking_priority_next_action={native_top_blocking_priority_next_action or 'missing'}; "
            f"native_precondition_closure_gate={native_precondition_closure_gate or 'missing'}; "
            f"native_precondition_failed_stage_count={native_precondition_failed_stage_count}; "
            f"native_precondition_failed_stage_keys={native_precondition_failed_stage_keys or 'none'}; "
            f"native_precondition_top_blocking_stage_key={native_precondition_top_blocking_stage_key or 'missing'}; "
            f"native_preconditions_full_evidence_ok={native_preconditions_full_evidence_ok}; "
            f"native_preconditions_inlet_source_gate={native_preconditions_inlet_source_gate or 'missing'}; "
            f"native_preconditions_paper_grade_inlet_source_gate={native_preconditions_paper_inlet_gate or 'missing'}; "
            f"native_preconditions_inlet_source_distribution_consistent={native_preconditions_inlet_distribution_consistent}; "
            f"native_preconditions_inlet_source_velocity_field_only={native_preconditions_inlet_velocity_only}; "
            f"native_preconditions_inlet_profile_gate={native_preconditions_inlet_profile_gate or 'missing'}; "
            f"native_preconditions_inlet_u_profile_gate={native_preconditions_inlet_u_profile_gate or 'missing'}; "
            f"native_preconditions_inlet_k_profile_gate={native_preconditions_inlet_k_profile_gate or 'missing'}; "
            f"native_preconditions_inlet_correlation_gate={native_preconditions_inlet_correlation_gate or 'missing'}; "
            f"native_preconditions_boundary_source_gate={native_preconditions_boundary_source_gate or 'missing'}; "
            f"native_preconditions_paper_grade_boundary_source_gate={native_preconditions_paper_boundary_gate or 'missing'}; "
            f"native_preconditions_boundary_source_wind_tunnel_equivalent={native_preconditions_boundary_equivalent}; "
            f"native_preconditions_boundary_source_fidelity_class={native_preconditions_boundary_fidelity_class or 'missing'}; "
            f"native_preconditions_boundary_source_has_complete_wind_tunnel_evidence={native_preconditions_boundary_complete_evidence}; "
            f"native_preconditions_boundary_source_has_empty_advanced_method_stub_only={native_preconditions_boundary_empty_stub_only}; "
            f"native_preconditions_boundary_source_simplified={native_preconditions_boundary_simplified}; "
            f"native_preconditions_boundary_protocol_gate={native_preconditions_boundary_protocol_gate or 'missing'}; "
            f"native_preconditions_boundary_evidence_gate={native_preconditions_boundary_evidence_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_gate={native_preconditions_boundary_runtime_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_traceability_gate={native_preconditions_boundary_runtime_traceability_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_profile_preservation_gate={native_preconditions_boundary_runtime_profile_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_inlet_gate={native_preconditions_boundary_runtime_inlet_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_side_top_gate={native_preconditions_boundary_runtime_side_top_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_side_top_normal_leakage_gate={native_preconditions_boundary_runtime_side_top_normal_gate or 'missing'}; "
            f"native_preconditions_boundary_runtime_outlet_gate={native_preconditions_boundary_runtime_outlet_gate or 'missing'}; "
            f"native_preconditions_probe_audit_row_count={native_preconditions_probe_row_count}; "
            f"native_preconditions_probe_audit_failed_row_count={native_preconditions_probe_failed_count}; "
            f"native_preconditions_probe_audit_compared_components={';'.join(sorted(native_preconditions_probe_components)) or 'missing'}; "
            f"native_preconditions_expected_compared_component={native_preconditions_expected_component or 'missing'}; "
            f"required_compared_component={required_compared_component or 'not_required'}; "
            f"native_preconditions_component_normalization_gate={native_preconditions_component_gate or 'missing'}; "
            f"native_preconditions_component_sensitivity_gate={native_preconditions_component_sensitivity_gate or 'missing'}; "
            f"native_preconditions_normalization_scale_gate={native_preconditions_normalization_scale_gate or 'missing'}; "
            f"native_preconditions_streamwise_sign_gate={native_preconditions_streamwise_sign_gate or 'missing'}; "
            f"native_preconditions_id={native_preconditions_id or 'missing'}; "
            f"native_preconditions_id_matches={native_preconditions_id_matches}; "
            f"native_preconditions_manifest_sha256={native_preconditions_manifest_sha256 or 'missing'}; "
            f"current_manifest_sha256={current_manifest_sha256 or 'missing'}; "
            f"native_preconditions_manifest_hash_matches={native_preconditions_manifest_hash_matches}; "
            f"native_preconditions_reasons={native_preconditions_reasons or 'none'}; "
            f"manifest={manifest_path or 'missing'}; "
            f"metrics_native_baseline_gate={get_any(metrics, ['native_baseline_gate', 'native_fluidx3d_baseline_gate']) or 'ignored'}; "
            f"metrics_native_preconditions_gate={get_any(metrics, ['native_preconditions_gate']) or 'ignored'}"
        ),
        "Run and archive a paired native FluidX3D baseline using an explicit complete source tree with setup/defines/lbm source hashes, then keep native_preconditions_audit.json proving manifest, setup, metadata, VTK pattern, averaging window, wind vector and Uref match the current package.",
    )

    parity_gate = str(
        get_any(native_citylbm_parity_audit, ["native_citylbm_parity_gate"]) or ""
    ).strip().lower()
    parity_reasons = str(
        get_any(native_citylbm_parity_audit, ["native_citylbm_parity_gate_reasons"]) or ""
    )
    parity_native_metrics = str(
        get_any(native_citylbm_parity_audit, ["native_metrics"]) or ""
    ).strip()
    parity_matched_count = as_int(
        get_any(native_citylbm_parity_audit, ["matched_field_count"])
    )
    parity_mismatched_count = as_int(
        get_any(native_citylbm_parity_audit, ["mismatched_field_count"])
    )
    parity_mismatched_fields = str(
        get_any(native_citylbm_parity_audit, ["mismatched_fields"]) or ""
    )
    parity_compared_gate_count = as_int(
        get_any(native_citylbm_parity_audit, ["compared_gate_field_count"])
    )
    parity_compared_hash_count = as_int(
        get_any(native_citylbm_parity_audit, ["compared_hash_field_count"])
    )
    parity_critical_status = native_citylbm_parity_critical_status(
        native_citylbm_parity_audit
    )
    parity_ok = (
        not citylbm_result
        or (
            native_citylbm_parity_audit_path is not None
            and parity_gate == "pass"
            and parity_critical_status["ok"]
            and parity_native_metrics
            and parity_matched_count is not None
            and parity_matched_count >= args.min_native_citylbm_parity_field_count
            and parity_compared_gate_count is not None
            and parity_compared_gate_count >= args.min_native_citylbm_parity_gate_field_count
            and parity_compared_hash_count is not None
            and parity_compared_hash_count >= args.min_native_citylbm_parity_hash_field_count
            and parity_mismatched_count == 0
        )
    )
    add_gate(
        gates,
        "native_citylbm_parity",
        PASS if parity_ok else FAIL,
        (
            f"software={software_label or 'missing'}; citylbm_result={citylbm_result}; "
            f"native_citylbm_parity_audit={native_citylbm_parity_audit_path or 'missing'}; "
            f"native_citylbm_parity_gate={parity_gate or 'missing'}; "
            f"native_metrics={parity_native_metrics or 'missing'}; "
            f"matched_field_count={parity_matched_count}; required >= {args.min_native_citylbm_parity_field_count}; "
            f"compared_gate_field_count={parity_compared_gate_count}; "
            f"required_gate_fields >= {args.min_native_citylbm_parity_gate_field_count}; "
            f"compared_hash_field_count={parity_compared_hash_count}; "
            f"required_hash_fields >= {args.min_native_citylbm_parity_hash_field_count}; "
            f"critical_parity_ok={parity_critical_status['ok']}; "
            f"critical_parity_reasons={parity_critical_status['reasons_csv'] or 'none'}; "
            f"matched_critical_field_count={parity_critical_status['matched_field_count']}; "
            f"required_critical_field_count={parity_critical_status['required_field_count']}; "
            f"missing_critical_fields={','.join(parity_critical_status['missing_recomputed']) or 'none'}; "
            f"mismatched_field_count={parity_mismatched_count}; mismatched_fields={parity_mismatched_fields or 'none'}; "
            f"native_citylbm_parity_gate_reasons={parity_reasons or 'none'}; "
            f"metrics_native_citylbm_parity_gate={get_any(metrics, ['native_citylbm_parity_gate', 'NativeCitylbmParityGate']) or 'ignored'}"
        ),
        "Before using native FluidX3D as the accuracy baseline for CityLBM, archive a parity audit proving the same case, wind, dx, averaging, Uref, inlet, boundary, source-audit hashes and probe settings.",
    )

    accuracy_delta_status = native_citylbm_accuracy_delta_status(
        native_citylbm_accuracy_delta_audit,
        args,
    )
    accuracy_delta_ok = (
        not citylbm_result
        or (
            native_citylbm_accuracy_delta_audit_path is not None
            and accuracy_delta_status["ok"]
        )
    )
    accuracy_deltas = accuracy_delta_status["deltas"]
    add_gate(
        gates,
        "native_citylbm_accuracy_delta",
        PASS if accuracy_delta_ok else FAIL,
        (
            f"software={software_label or 'missing'}; citylbm_result={citylbm_result}; "
            f"native_citylbm_accuracy_delta_audit={native_citylbm_accuracy_delta_audit_path or 'missing'}; "
            f"native_citylbm_accuracy_delta_gate={accuracy_delta_status['declared_gate'] or 'missing'}; "
            f"native_accuracy_gate={accuracy_delta_status['native_accuracy_gate'] or 'missing'}; "
            f"accuracy_interpretation={accuracy_delta_status['interpretation'] or 'missing'}; "
            f"citylbm_additional_error_flag={accuracy_delta_status['citylbm_additional_error_flag']}; "
            f"U_RMSE_delta_city_minus_native={accuracy_deltas['U_RMSE_delta_city_minus_native']}; "
            f"threshold <= {args.max_native_citylbm_rmse_delta}; "
            f"U_abs_bias_delta_city_minus_native={accuracy_deltas['U_abs_bias_delta_city_minus_native']}; "
            f"threshold <= {args.max_native_citylbm_abs_bias_delta}; "
            f"U_R2_drop_native_minus_city={accuracy_deltas['U_R2_drop_native_minus_city']}; "
            f"threshold <= {args.max_native_citylbm_r2_drop}; "
            f"U_slope_abs_delta={accuracy_deltas['U_slope_abs_delta']}; "
            f"threshold <= {args.max_native_citylbm_slope_delta}; "
            f"U_intercept_abs_delta={accuracy_deltas['U_intercept_abs_delta']}; "
            f"threshold <= {args.max_native_citylbm_intercept_delta}; "
            f"native_citylbm_accuracy_delta_reasons={accuracy_delta_status['reasons_csv'] or 'none'}; "
            f"metrics_native_citylbm_accuracy_delta_gate={get_any(metrics, ['native_citylbm_accuracy_delta_gate']) or 'ignored'}"
        ),
        "Archive native_citylbm_accuracy_delta_audit.json comparing paired CityLBM and native FluidX3D metrics. If CityLBM adds error, inspect parameter transfer, setup.cpp generation, VTK scaling and probe postprocessing; if CityLBM matches a poor native baseline, improve native inlet, boundary, averaging and grid protocol first.",
    )

    grid_gate = str(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_gate"]) or ""
    ).strip().lower()
    grid_reasons = str(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_gate_reasons"]) or ""
    )
    grid_run_count = as_int(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_run_count"])
    )
    grid_fine_dx = as_float(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_finest_dx_m"])
    )
    grid_next_coarse_dx = as_float(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_next_coarse_dx_m"])
    )
    grid_refinement_ratio = as_float(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_refinement_ratio"])
    )
    grid_rmse_change = as_float(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_rmse_change_ratio"])
    )
    grid_bias_change = as_float(
        get_any(grid_sensitivity_audit, ["grid_sensitivity_bias_change_ratio"])
    )
    current_dx_for_grid = as_float(get_any(metrics, ["dx_m", "dx", "DxM", "Dx"]))
    grid_fine_matches_current = (
        grid_fine_dx is not None
        and current_dx_for_grid is not None
        and abs(grid_fine_dx - current_dx_for_grid) <= args.grid_dx_tolerance
    )
    grid_sensitivity_ok = (
        grid_sensitivity_audit_path is not None
        and grid_gate == "pass"
        and grid_run_count is not None
        and grid_run_count >= args.min_grid_sensitivity_run_count
        and grid_fine_dx is not None
        and grid_fine_dx <= args.max_paper_dx_m
        and grid_fine_matches_current
        and grid_refinement_ratio is not None
        and grid_refinement_ratio >= args.min_grid_refinement_ratio
        and grid_rmse_change is not None
        and grid_rmse_change <= args.max_grid_rmse_change_ratio
        and grid_bias_change is not None
        and grid_bias_change <= args.max_grid_bias_change_ratio
    )
    add_gate(
        gates,
        "grid_sensitivity",
        PASS if grid_sensitivity_ok else FAIL,
        (
            f"grid_sensitivity_audit={grid_sensitivity_audit_path or 'missing'}; "
            f"grid_sensitivity_gate={grid_gate or 'missing'}; "
            f"grid_sensitivity_run_count={grid_run_count}; required >= {args.min_grid_sensitivity_run_count}; "
            f"current_dx_m={current_dx_for_grid}; finest_dx_m={grid_fine_dx}; required <= {args.max_paper_dx_m}; "
            f"finest_dx_matches_current={grid_fine_matches_current}; "
            f"next_coarse_dx_m={grid_next_coarse_dx}; refinement_ratio={grid_refinement_ratio}; "
            f"required >= {args.min_grid_refinement_ratio}; "
            f"rmse_change_ratio={grid_rmse_change}; required <= {args.max_grid_rmse_change_ratio}; "
            f"bias_change_ratio={grid_bias_change}; required <= {args.max_grid_bias_change_ratio}; "
            f"grid_sensitivity_gate_reasons={grid_reasons or 'none'}; "
            f"metrics_grid_sensitivity_gate={get_any(metrics, ['grid_sensitivity_gate', 'GridSensitivityGate']) or 'ignored'}"
        ),
        "Archive at least two matched grid levels and show the finest-grid U_RMSE/U_bias changes are bounded before interpreting residual systematic bias.",
    )

    probe_total, probe_failed, probe_error = read_probe_counts(probe_path)
    probe_audit_traceable = probe_total is not None and probe_total > 0
    probe_summary_override = args.allow_summary_only_probe_metrics
    probe_traceability_status = (
        PASS
        if probe_audit_traceable
        else (WARN if probe_summary_override else FAIL)
    )
    add_gate(
        gates,
        "probe_audit_traceability",
        probe_traceability_status,
        (
            f"probe_audit={probe_path or 'missing'}; probe_total={probe_total}; "
            f"probe_failed={probe_failed}; allow_summary_only_probe_metrics={probe_summary_override}; "
            f"{probe_error or ''}"
        ).strip(),
        "Export the Data Probe audit CSV with official probe IDs, x/y/z, Uref, wind vector, compared_component, nearest_distance and tolerance.",
    )
    detailed_probe_audit_ok = probe_audit_traceable
    probe_source = read_probe_source_window_audit(
        probe_path,
        source_step_text,
        expected_source_hashes,
        args.min_avg_step_span,
    )
    probe_source_window_ok = (
        probe_audit_traceable
        and has_real_source_steps
        and bool(expected_source_hashes)
        and probe_source["valid_count"] is not None
        and probe_source["valid_count"] > 0
        and probe_source["missing_source_steps_count"] == 0
        and probe_source["source_steps_mismatch_count"] == 0
        and probe_source["unique_source_steps_count"] == 1
        and probe_source["missing_source_step_span_count"] == 0
        and probe_source["source_step_span_mismatch_count"] == 0
        and probe_source["source_step_span_short_count"] == 0
        and probe_source["missing_minimum_step_span_count"] == 0
        and probe_source["minimum_step_span_mismatch_count"] == 0
        and probe_source["unique_source_step_span_count"] == 1
        and probe_source["missing_source_hash_count"] == 0
        and probe_source["source_hash_count_mismatch_count"] == 0
        and probe_source["source_hash_mismatch_count"] == 0
        and probe_source["unique_source_hash_set_count"] == 1
        and probe_source["missing_source_files_count"] == 0
        and probe_source["source_file_count_mismatch_count"] == 0
        and probe_source["source_file_missing_count"] == 0
        and probe_source["source_file_hash_mismatch_count"] == 0
        and probe_source["source_file_expected_hash_mismatch_count"] == 0
        and probe_source["unique_source_file_set_count"] == 1
        and not probe_source["error"]
    )
    add_gate(
        gates,
        "probe_source_window",
        PASS if probe_source_window_ok else FAIL,
        (
            f"expected_source_time_steps={source_step_text or 'missing'}; "
            f"expected_source_hashes={expected_source_hash_text or 'missing'}; "
            f"real_source_time_steps_present={has_real_source_steps}; "
            f"probe_valid_count={probe_source['valid_count']}; "
            f"missing_probe_source_steps={probe_source['missing_source_steps_count']}; "
            f"probe_source_steps_mismatch={probe_source['source_steps_mismatch_count']}; "
            f"unique_probe_source_steps={probe_source['unique_source_steps_count']}; "
            f"expected_probe_source_step_span={probe_source['expected_source_step_span']}; "
            f"required_probe_source_step_span>={args.min_avg_step_span}; "
            f"missing_probe_source_step_span={probe_source['missing_source_step_span_count']}; "
            f"probe_source_step_span_mismatch={probe_source['source_step_span_mismatch_count']}; "
            f"probe_source_step_span_short={probe_source['source_step_span_short_count']}; "
            f"missing_probe_minimum_step_span={probe_source['missing_minimum_step_span_count']}; "
            f"probe_minimum_step_span_mismatch={probe_source['minimum_step_span_mismatch_count']}; "
            f"unique_probe_source_step_spans={probe_source['unique_source_step_span_count']}; "
            f"missing_probe_source_hashes={probe_source['missing_source_hash_count']}; "
            f"probe_source_hash_count_mismatch={probe_source['source_hash_count_mismatch_count']}; "
            f"probe_source_hash_mismatch={probe_source['source_hash_mismatch_count']}; "
            f"unique_probe_source_hash_sets={probe_source['unique_source_hash_set_count']}; "
            f"missing_probe_source_files={probe_source['missing_source_files_count']}; "
            f"probe_source_file_count_mismatch={probe_source['source_file_count_mismatch_count']}; "
            f"probe_source_file_missing={probe_source['source_file_missing_count']}; "
            f"probe_source_file_hash_mismatch={probe_source['source_file_hash_mismatch_count']}; "
            f"probe_source_file_expected_hash_mismatch={probe_source['source_file_expected_hash_mismatch_count']}; "
            f"unique_probe_source_file_sets={probe_source['unique_source_file_set_count']}; "
            f"probe_audit_traceable={probe_audit_traceable}; "
            f"error={probe_source['error'] or 'none'}"
        ),
        "Use the same final-window VTK frames for time averaging, inlet/profile audits and RS probe extraction, and archive per-probe VTK source paths, hashes and solver-step span.",
    )
    (
        projection_valid_count,
        max_probe_distance,
        max_probe_tolerance,
        missing_probe_distance_count,
        missing_probe_tolerance_count,
        probe_projection_error,
    ) = read_probe_projection_audit(probe_path)
    dx_m = as_float(get_any(metrics, ["dx_m", "dx", "DxM", "Dx"]))
    distance_within_tolerance = (
        max_probe_distance is not None
        and max_probe_tolerance is not None
        and max_probe_distance <= max_probe_tolerance + 1.0e-9
    )
    distance_dx_ratio = (
        max_probe_distance / dx_m
        if max_probe_distance is not None and dx_m is not None and dx_m > 0.0
        else None
    )
    tolerance_dx_ratio = (
        max_probe_tolerance / dx_m
        if max_probe_tolerance is not None and dx_m is not None and dx_m > 0.0
        else None
    )
    distance_dx_ok = (
        distance_dx_ratio is not None
        and distance_dx_ratio <= args.max_probe_distance_dx_ratio
    )
    tolerance_dx_ok = (
        tolerance_dx_ratio is not None
        and tolerance_dx_ratio <= args.max_probe_tolerance_dx_ratio
    )
    projection_complete = (
        projection_valid_count is not None
        and projection_valid_count > 0
        and missing_probe_distance_count == 0
        and missing_probe_tolerance_count == 0
    )
    add_gate(
        gates,
        "probe_projection_distance",
        PASS
        if probe_audit_traceable
        and projection_complete
        and distance_within_tolerance
        and distance_dx_ok
        and tolerance_dx_ok
        else FAIL,
        (
            f"probe_valid_count={projection_valid_count}; dx_m={dx_m}; "
            f"max_probe_distance_m={max_probe_distance}; max_probe_tolerance_m={max_probe_tolerance}; "
            f"missing_distance_count={missing_probe_distance_count}; "
            f"missing_tolerance_count={missing_probe_tolerance_count}; "
            f"distance_within_tolerance={distance_within_tolerance}; "
            f"distance_dx_ratio={distance_dx_ratio}; required <= {args.max_probe_distance_dx_ratio}; "
            f"tolerance_dx_ratio={tolerance_dx_ratio}; required <= {args.max_probe_tolerance_dx_ratio}; "
            f"probe_audit_traceable={probe_audit_traceable}; {probe_projection_error or ''}"
        ).strip(),
        "Keep RS probe interpolation/projection distances traceable and bounded by dx; do not rescue missing slice points with an overly large tolerance.",
    )

    metrics_grid_extent_gate = str(
        get_any(metrics, ["probe_grid_extent_gate", "ProbeGridExtentGate"]) or ""
    ).strip().lower()
    metrics_outside_grid_count = as_int(
        get_any(metrics, ["probe_outside_vtk_grid_extent_count", "ProbeOutsideVtkGridExtentCount"])
    )
    metrics_missing_grid_count = as_int(
        get_any(metrics, ["probe_missing_vtk_grid_extent_count", "ProbeMissingVtkGridExtentCount"])
    )
    probe_grid_extent_ok = (
        probe_audit_traceable
        and metrics_grid_extent_gate == "pass"
        and metrics_outside_grid_count == 0
        and metrics_missing_grid_count == 0
    )
    add_gate(
        gates,
        "probe_grid_extent",
        PASS if probe_grid_extent_ok else FAIL,
        (
            f"metrics_probe_grid_extent_gate={metrics_grid_extent_gate or 'missing'}; "
            f"metrics_outside_vtk_grid_extent_count={metrics_outside_grid_count}; "
            f"metrics_missing_vtk_grid_extent_count={metrics_missing_grid_count}; "
            f"probe_audit_traceable={probe_audit_traceable}"
        ),
        "Require every official probe to lie inside the physical VTK grid before interpolation; fix scale, domain_origin or RS coordinate transforms before comparing errors.",
    )

    metrics_protocol_gate = str(
        get_any(metrics, ["protocol_gate", "ProtocolGate", "metrics_protocol_gate"])
        or ""
    ).strip()
    metrics_probe_uref_expected = as_float(
        get_any(metrics, ["probe_uref_expected_mps", "ProbeUrefExpectedMps"])
    )
    metrics_probe_uref_values = str(
        get_any(metrics, ["probe_uref_values", "ProbeUrefValues"]) or ""
    ).strip()
    metrics_probe_uref_mismatch_count = as_int(
        get_any(metrics, ["probe_uref_mismatch_count", "ProbeUrefMismatchCount"])
    )
    metrics_protocol_ok = (
        metrics_protocol_gate == "metrics_ready_for_validation_gate"
        and (metrics_probe_uref_mismatch_count in {None, 0})
    )
    add_gate(
        gates,
        "metrics_protocol",
        PASS if metrics_protocol_ok else FAIL,
        (
            f"metrics_protocol_gate={metrics_protocol_gate or 'missing'}; "
            f"probe_uref_expected_mps={metrics_probe_uref_expected if metrics_probe_uref_expected is not None else 'not_set'}; "
            f"probe_uref_values={metrics_probe_uref_values or 'missing'}; "
            f"probe_uref_mismatch_count={metrics_probe_uref_mismatch_count if metrics_probe_uref_mismatch_count is not None else 'missing'}"
        ),
        "Rebuild validation_metrics.csv from the current probe audit and official table until its internal protocol_gate is metrics_ready_for_validation_gate.",
    )

    normalization_valid = as_bool(get_any(metrics, ["normalization_valid", "NormalizationValid"]))
    wind_valid = as_bool(get_any(metrics, ["wind_direction_valid", "WindDirectionValid"]))
    uref = as_float(get_any(metrics, ["Uref_mps", "Uref", "U_ref"]))
    uref_ok = args.expected_uref is None or (
        uref is not None and abs(uref - args.expected_uref) <= args.uref_tolerance
    )
    metric_wind_vector = parse_vector(get_any(metrics, ["wind_vector", "WindVector"]))
    expected_wind_vector = parse_vector(args.expected_wind_vector) if args.expected_wind_vector else None
    wind_delta = vector_delta(metric_wind_vector, expected_wind_vector)
    wind_vector_ok = expected_wind_vector is None or (
        wind_delta is not None and wind_delta <= args.wind_vector_tolerance
    )
    metrics_coord_delta = as_float(get_any(metrics, ["max_official_coordinate_delta_m", "MaxOfficialCoordinateDeltaM"]))
    metrics_coord_delta_count = as_int(get_any(metrics, ["official_coordinate_delta_count", "OfficialCoordinateDeltaCount"]))
    valid_metric_count = as_int(get_any(metrics, ["valid_n", "ValidN"]))
    metrics_official_measurement_count = as_int(
        get_any(metrics, ["official_measurement_count", "OfficialMeasurementCount"])
    )
    metrics_missing_official_probe_count = as_int(
        get_any(metrics, ["missing_official_probe_count", "MissingOfficialProbeCount"])
    )
    metrics_official_probe_coverage_ratio = as_float(
        get_any(metrics, ["official_probe_coverage_ratio", "OfficialProbeCoverageRatio"])
    )
    identity_case = str(get_any(metrics, ["case", "Case"]) or args.case or "").strip()
    identity_wind_direction = str(
        get_any(metrics, ["wind_direction", "WindDirection", "Wind_direction"]) or ""
    ).strip()
    probe_coord_norm = read_probe_coordinate_normalization_audit(
        probe_path,
        args.expected_uref,
        args.uref_tolerance,
        expected_wind_vector,
        args.wind_vector_tolerance,
        official_path,
        identity_case,
        identity_wind_direction,
    )
    probe_identity = read_probe_identity_audit(
        probe_path,
        official_path,
        identity_case,
        identity_wind_direction,
    )
    coord_delta = as_float(probe_coord_norm["max_official_coordinate_delta_m"])
    coord_delta_count = as_int(probe_coord_norm["official_coordinate_delta_count"])
    coord_valid_count = as_int(probe_coord_norm["valid_count"])
    coord_source = str(probe_coord_norm["official_coordinate_source"] or "missing")
    coord_ok = coord_delta is not None and coord_delta <= args.max_official_coordinate_delta_m
    coord_coverage_ok = (
        coord_delta_count is not None
        and coord_valid_count is not None
        and coord_valid_count > 0
        and coord_delta_count == coord_valid_count
        and probe_coord_norm["missing_official_coordinate_delta_count"] == 0
    )
    probe_identity_valid_count = as_int(probe_identity["valid_count"])
    probe_identity_ok = (
        probe_audit_traceable
        and probe_identity_valid_count is not None
        and probe_identity_valid_count > 0
        and bool(probe_identity["probe_id_column"])
        and bool(probe_identity["official_id_column"])
        and probe_identity["missing_probe_id_count"] == 0
        and probe_identity["duplicate_probe_id_count"] == 0
        and probe_identity["unique_probe_id_count"] == probe_identity_valid_count
        and probe_identity["official_id_count"] is not None
        and probe_identity["official_id_count"] > 0
        and probe_identity["matched_official_id_count"] == probe_identity["official_id_count"]
        and probe_identity["missing_official_probe_id_count"] == 0
        and probe_identity["official_probe_coverage_ratio"] == 1.0
        and probe_identity["unmatched_official_id_count"] == 0
        and probe_identity["error"] is None
        and coord_valid_count == probe_identity_valid_count
        and probe_identity_valid_count == probe_identity["official_id_count"]
        and (valid_metric_count is None or valid_metric_count == probe_identity_valid_count)
        and (
            metrics_official_measurement_count is None
            or metrics_official_measurement_count == probe_identity["official_id_count"]
        )
        and (
            metrics_missing_official_probe_count is None
            or metrics_missing_official_probe_count == probe_identity["missing_official_probe_id_count"]
        )
        and (
            metrics_official_probe_coverage_ratio is None
            or abs(metrics_official_probe_coverage_ratio - probe_identity["official_probe_coverage_ratio"]) <= 1.0e-12
        )
    )
    probe_coord_norm_ok = (
        probe_audit_traceable
        and probe_coord_norm["valid_count"] is not None
        and probe_coord_norm["valid_count"] > 0
        and probe_coord_norm["missing_normalization_count"] == 0
        and probe_coord_norm["invalid_normalization_count"] == 0
        and probe_coord_norm["missing_wind_direction_count"] == 0
        and probe_coord_norm["invalid_wind_direction_count"] == 0
        and probe_coord_norm["missing_uref_count"] == 0
        and probe_coord_norm["uref_mismatch_count"] == 0
        and probe_coord_norm["unique_uref_count"] == 1
        and probe_coord_norm["missing_wind_vector_count"] == 0
        and probe_coord_norm["wind_vector_mismatch_count"] == 0
        and probe_coord_norm["unique_wind_vector_count"] == 1
        and probe_coord_norm["missing_vtk_grid_extent_count"] == 0
        and probe_coord_norm["outside_vtk_grid_extent_count"] == 0
        and probe_coord_norm["official_coordinate_error"] is None
        and probe_coord_norm["official_coordinate_recomputed_count"] == probe_coord_norm["valid_count"]
    )
    add_gate(
        gates,
        "coordinate_normalization",
        PASS
        if detailed_probe_audit_ok
        and normalization_valid is True
        and wind_valid is True
        and uref_ok
        and wind_vector_ok
        and coord_ok
        and coord_coverage_ok
        and probe_identity_ok
        and probe_coord_norm_ok
        else FAIL,
        (
            f"normalization_valid={normalization_valid}; wind_direction_valid={wind_valid}; "
            f"Uref_mps={uref}; expected_uref={args.expected_uref}; uref_tolerance={args.uref_tolerance}; "
            f"wind_vector={metric_wind_vector}; expected_wind_vector={expected_wind_vector}; "
            f"wind_vector_unit_delta={wind_delta}; wind_vector_tolerance={args.wind_vector_tolerance}; "
            f"coordinate_source={coord_source}; "
            f"max_official_coordinate_delta_m={coord_delta}; required <= {args.max_official_coordinate_delta_m}; "
            f"official_coordinate_delta_count={coord_delta_count}; coordinate_valid_count={coord_valid_count}; "
            f"probe_identity_valid_count={probe_identity_valid_count}; "
            f"probe_identity_probe_id_column={probe_identity['probe_id_column'] or 'missing'}; "
            f"probe_identity_official_id_column={probe_identity['official_id_column'] or 'missing'}; "
            f"probe_identity_unique_probe_id_count={probe_identity['unique_probe_id_count']}; "
            f"probe_identity_missing_probe_id_count={probe_identity['missing_probe_id_count']}; "
            f"probe_identity_duplicate_probe_id_count={probe_identity['duplicate_probe_id_count']}; "
            f"probe_identity_official_row_count={probe_identity['official_row_count']}; "
            f"probe_identity_official_id_count={probe_identity['official_id_count']}; "
            f"probe_identity_matched_official_id_count={probe_identity['matched_official_id_count']}; "
            f"probe_identity_missing_official_probe_id_count={probe_identity['missing_official_probe_id_count']}; "
            f"probe_identity_official_probe_coverage_ratio={probe_identity['official_probe_coverage_ratio']}; "
            f"probe_identity_unmatched_official_id_count={probe_identity['unmatched_official_id_count']}; "
            f"probe_identity_filter_case={identity_case or 'none'}; "
            f"probe_identity_filter_wind_direction={identity_wind_direction or 'none'}; "
            f"metrics_official_measurement_count={metrics_official_measurement_count if metrics_official_measurement_count is not None else 'ignored'}; "
            f"metrics_missing_official_probe_count={metrics_missing_official_probe_count if metrics_missing_official_probe_count is not None else 'ignored'}; "
            f"metrics_official_probe_coverage_ratio={metrics_official_probe_coverage_ratio if metrics_official_probe_coverage_ratio is not None else 'ignored'}; "
            f"probe_identity_ok={probe_identity_ok}; "
            f"probe_identity_error={probe_identity['error'] or 'none'}; "
            f"metrics_max_official_coordinate_delta_m={metrics_coord_delta if metrics_coord_delta is not None else 'ignored'}; "
            f"metrics_official_coordinate_delta_count={metrics_coord_delta_count if metrics_coord_delta_count is not None else 'ignored'}; "
            f"probe_norm_valid_count={probe_coord_norm['valid_count']}; "
            f"probe_official_coordinate_source={probe_coord_norm['official_coordinate_source']}; "
            f"probe_official_coordinate_recomputed_count={probe_coord_norm['official_coordinate_recomputed_count']}; "
            f"probe_official_coordinate_error={probe_coord_norm['official_coordinate_error'] or 'none'}; "
            f"probe_missing_official_coordinate_delta_count={probe_coord_norm['missing_official_coordinate_delta_count']}; "
            f"probe_missing_normalization_count={probe_coord_norm['missing_normalization_count']}; "
            f"probe_invalid_normalization_count={probe_coord_norm['invalid_normalization_count']}; "
            f"probe_missing_wind_direction_count={probe_coord_norm['missing_wind_direction_count']}; "
            f"probe_invalid_wind_direction_count={probe_coord_norm['invalid_wind_direction_count']}; "
            f"probe_missing_uref_count={probe_coord_norm['missing_uref_count']}; "
            f"probe_uref_mismatch_count={probe_coord_norm['uref_mismatch_count']}; "
            f"probe_unique_uref_count={probe_coord_norm['unique_uref_count']}; "
            f"probe_missing_wind_vector_count={probe_coord_norm['missing_wind_vector_count']}; "
            f"probe_wind_vector_mismatch_count={probe_coord_norm['wind_vector_mismatch_count']}; "
            f"probe_unique_wind_vector_count={probe_coord_norm['unique_wind_vector_count']}; "
            f"probe_missing_vtk_grid_extent_count={probe_coord_norm['missing_vtk_grid_extent_count']}; "
            f"probe_outside_vtk_grid_extent_count={probe_coord_norm['outside_vtk_grid_extent_count']}; "
            f"probe_audit_traceable={probe_audit_traceable}; "
            f"allow_summary_only_probe_metrics={probe_summary_override}; "
            f"{probe_coord_norm['error'] or ''}"
        ),
        "Audit Uref/Zref, wind sign, compared component and RS probe coordinate transform.",
    )

    component_gate = str(get_any(metrics, ["compared_component_consistency_gate", "ComparedComponentConsistencyGate"]) or "").strip().lower()
    metric_component = str(get_any(metrics, ["compared_component", "velocity_component", "ComparedComponent"]) or "").strip().lower()
    probe_valid_component_count, probe_components, probe_missing_component_count, probe_component_error = read_probe_component_audit(probe_path)
    expected_component = args.expected_compared_component.strip().lower()
    unique_components = probe_components
    component_consistent = (
        detailed_probe_audit_ok
        and component_gate == "pass"
        and len(unique_components) == 1
        and bool(unique_components[0])
        and (probe_missing_component_count in {None, 0})
        and (not expected_component or unique_components[0] == expected_component)
    )
    add_gate(
        gates,
        "compared_component",
        PASS if component_consistent else FAIL,
        (
            f"metrics_component={metric_component or 'missing'}; "
            f"metrics_component_gate={component_gate or 'missing'}; "
            f"probe_components={';'.join(unique_components) or 'missing'}; "
            f"expected={expected_component or 'not_set'}; "
            f"probe_valid_component_count={probe_valid_component_count}; "
            f"probe_missing_component_count={probe_missing_component_count}; "
            f"probe_audit_traceable={probe_audit_traceable}; "
            f"allow_summary_only_probe_metrics={probe_summary_override}; "
            f"{probe_component_error or ''}"
        ).strip(),
        "Use one explicit Data Probe Compared Component for all official probes and match it to the AIJ table definition.",
    )

    metric_component_sensitivity_audit = str(
        get_any(metrics, ["component_sensitivity_audit", "ComponentSensitivityAudit"]) or ""
    ).strip()

    component_normalization_gate = str(
        component_sensitivity_audit.get("component_normalization_gate") or ""
    ).strip().lower()
    component_sensitivity_gate = str(
        component_sensitivity_audit.get("component_sensitivity_gate") or ""
    ).strip().lower()
    normalization_scale_gate = str(
        component_sensitivity_audit.get("normalization_scale_gate") or ""
    ).strip().lower()
    streamwise_sign_gate = str(
        component_sensitivity_audit.get("streamwise_sign_gate") or ""
    ).strip().lower()
    streamwise_sign_reasons_raw = component_sensitivity_audit.get("streamwise_sign_gate_reasons")
    streamwise_sign_reasons = (
        [str(value) for value in streamwise_sign_reasons_raw]
        if isinstance(streamwise_sign_reasons_raw, list)
        else [str(streamwise_sign_reasons_raw)]
        if streamwise_sign_reasons_raw
        else []
    )
    streamwise_negative_fraction = as_float(
        component_sensitivity_audit.get("streamwise_negative_fraction")
    )
    streamwise_mean_ratio = as_float(component_sensitivity_audit.get("streamwise_mean_ratio"))
    streamwise_sign_valid_n = as_int(component_sensitivity_audit.get("streamwise_sign_valid_n"))
    selected_component = str(
        component_sensitivity_audit.get("selected_component")
        or ""
    ).strip().lower()
    selected_component_source = str(
        component_sensitivity_audit.get("selected_component_source")
        or ""
    ).strip().lower()
    component_audit_case = str(component_sensitivity_audit.get("case") or "").strip()
    component_audit_wind_direction = str(component_sensitivity_audit.get("wind_direction") or "").strip()
    component_scope_case_ok = (
        not identity_case
        or component_audit_case.lower() == identity_case.lower()
    )
    component_scope_wind_ok = (
        not identity_wind_direction
        or component_audit_wind_direction.lower() == identity_wind_direction.lower()
    )
    component_official_filtered_row_count = as_int(
        component_sensitivity_audit.get("official_filtered_row_count")
    )
    component_official_id_count = as_int(component_sensitivity_audit.get("official_id_count"))
    component_probe_row_count = as_int(component_sensitivity_audit.get("probe_row_count"))
    component_valid_probe_id_count = as_int(component_sensitivity_audit.get("valid_probe_id_count"))
    component_matched_valid_probe_id_count = as_int(
        component_sensitivity_audit.get("matched_valid_probe_id_count")
    )
    component_unmatched_valid_probe_id_count = as_int(
        component_sensitivity_audit.get("unmatched_valid_probe_id_count")
    )
    component_missing_official_probe_id_count = as_int(
        component_sensitivity_audit.get("missing_official_probe_id_count")
    )
    component_official_probe_coverage_ratio = as_float(
        component_sensitivity_audit.get("official_probe_coverage_ratio")
    )
    component_scope_ok = (
        component_scope_case_ok
        and component_scope_wind_ok
        and component_official_filtered_row_count is not None
        and component_official_filtered_row_count > 0
        and component_official_id_count is not None
        and component_official_id_count > 0
        and component_valid_probe_id_count is not None
        and component_valid_probe_id_count > 0
        and component_matched_valid_probe_id_count is not None
        and component_matched_valid_probe_id_count == component_valid_probe_id_count
        and component_matched_valid_probe_id_count == component_official_id_count
        and component_valid_probe_id_count == component_official_id_count
        and component_unmatched_valid_probe_id_count == 0
        and component_missing_official_probe_id_count == 0
        and component_official_probe_coverage_ratio is not None
        and abs(component_official_probe_coverage_ratio - 1.0) <= 1.0e-12
    )
    valid_probe_components_raw = component_sensitivity_audit.get("valid_probe_compared_components")
    valid_probe_components = (
        [str(value).strip().lower() for value in valid_probe_components_raw]
        if isinstance(valid_probe_components_raw, list)
        else []
    )
    valid_probe_component_count = as_int(
        component_sensitivity_audit.get("valid_probe_compared_component_count")
    )
    valid_probe_missing_component_count = as_int(
        component_sensitivity_audit.get("valid_probe_missing_compared_component_count")
    )
    best_component = str(
        component_sensitivity_audit.get("best_component_by_rmse")
        or ""
    ).strip().lower()
    selected_component_rmse = as_float(
        component_sensitivity_audit.get("selected_component_rmse")
    )
    best_component_rmse = as_float(
        component_sensitivity_audit.get("best_component_rmse")
    )
    component_rmse_improvement = as_float(
        component_sensitivity_audit.get("component_rmse_improvement_ratio")
    )
    selected_component_bias = as_float(
        component_sensitivity_audit.get("selected_component_bias")
    )
    selected_component_scaled_bias = as_float(
        component_sensitivity_audit.get("selected_component_scaled_bias")
    )
    selected_component_bias_reduction = as_float(
        component_sensitivity_audit.get("selected_component_bias_abs_reduction_ratio")
    )
    selected_component_mean_sim = as_float(
        component_sensitivity_audit.get("selected_component_mean_sim")
    )
    selected_component_mean_exp = as_float(
        component_sensitivity_audit.get("selected_component_mean_exp")
    )
    selected_component_mean_ratio = as_float(
        component_sensitivity_audit.get("selected_component_mean_sim_to_exp_ratio")
    )
    normalization_best_scale = as_float(
        component_sensitivity_audit.get("selected_best_fit_scale_to_exp")
    )
    normalization_scaled_improvement = as_float(
        component_sensitivity_audit.get("selected_scaled_improvement_ratio")
    )
    component_source_window_gate = str(
        component_sensitivity_audit.get("component_source_window_gate") or ""
    ).strip().lower()
    component_source_window_reasons_raw = component_sensitivity_audit.get("component_source_window_gate_reasons")
    component_source_window_reasons = (
        [str(value) for value in component_source_window_reasons_raw]
        if isinstance(component_source_window_reasons_raw, list)
        else [str(component_source_window_reasons_raw)]
        if component_source_window_reasons_raw
        else []
    )
    component_probe_audit_sha256 = str(
        get_any(component_sensitivity_audit, ["probe_audit_sha256", "ProbeAuditSha256"]) or ""
    ).strip().lower()
    component_official_sha256 = str(
        get_any(component_sensitivity_audit, ["official_sha256", "OfficialSha256"]) or ""
    ).strip().lower()
    component_probe_hash_matches = (
        bool(current_probe_audit_sha256)
        and bool(component_probe_audit_sha256)
        and component_probe_audit_sha256 == current_probe_audit_sha256.lower()
    )
    component_official_hash_matches = (
        bool(current_official_sha256)
        and bool(component_official_sha256)
        and component_official_sha256 == current_official_sha256.lower()
    )
    component_sensitivity_audit_exists = (
        bool(component_sensitivity_audit_path and component_sensitivity_audit_path.exists())
    )
    component_choice_not_explained = (
        bool(selected_component)
        and bool(best_component)
        and selected_component_rmse is not None
        and best_component_rmse is not None
        and (
            selected_component == best_component
            or (
                component_rmse_improvement is not None
                and component_rmse_improvement < args.max_component_rmse_improvement_ratio
            )
        )
    )
    normalization_scale_not_explained = (
        normalization_best_scale is not None
        and (
            abs(normalization_best_scale - 1.0) <= args.max_normalization_best_scale_deviation
            or normalization_scaled_improvement is None
            or normalization_scaled_improvement < args.min_normalization_scaled_improvement_ratio
        )
    )
    component_normalization_pass = (
        component_sensitivity_audit_exists
        and component_normalization_gate == "pass"
        and component_sensitivity_gate == "pass"
        and normalization_scale_gate == "pass"
        and streamwise_sign_gate == "pass"
        and component_source_window_gate == "pass"
        and component_probe_hash_matches
        and component_official_hash_matches
        and component_scope_ok
        and component_choice_not_explained
        and normalization_scale_not_explained
    )
    add_gate(
        gates,
        "component_normalization_sensitivity",
        PASS if component_normalization_pass else FAIL,
        (
            f"component_normalization_gate={component_normalization_gate or 'missing'}; "
            f"component_sensitivity_gate={component_sensitivity_gate or 'missing'}; "
            f"normalization_scale_gate={normalization_scale_gate or 'missing'}; "
            f"streamwise_sign_gate={streamwise_sign_gate or 'missing'}; "
            f"streamwise_sign_reasons={';'.join(streamwise_sign_reasons) or 'missing'}; "
            f"streamwise_negative_fraction={streamwise_negative_fraction}; "
            f"streamwise_mean_ratio={streamwise_mean_ratio}; "
            f"streamwise_sign_valid_n={streamwise_sign_valid_n}; "
            f"component_source_window_gate={component_source_window_gate or 'missing'}; "
            f"component_source_window_reasons={';'.join(component_source_window_reasons) or 'missing'}; "
            f"component_source_time_steps={component_sensitivity_audit.get('component_source_time_steps') or 'missing'}; "
            f"component_source_step_span={component_sensitivity_audit.get('component_source_step_span')}; "
            f"component_minimum_source_step_span={component_sensitivity_audit.get('component_minimum_source_step_span')}; "
            f"component_source_hash_set_unique_count={component_sensitivity_audit.get('component_source_hash_set_unique_count')}; "
            f"component_audit_case={component_audit_case or 'missing'}; "
            f"expected_case={identity_case or 'not_set'}; "
            f"component_scope_case_ok={component_scope_case_ok}; "
            f"component_audit_wind_direction={component_audit_wind_direction or 'missing'}; "
            f"expected_wind_direction={identity_wind_direction or 'not_set'}; "
            f"component_scope_wind_ok={component_scope_wind_ok}; "
            f"component_official_filtered_row_count={component_official_filtered_row_count}; "
            f"component_official_id_count={component_official_id_count}; "
            f"component_probe_row_count={component_probe_row_count}; "
            f"component_valid_probe_id_count={component_valid_probe_id_count}; "
            f"component_matched_valid_probe_id_count={component_matched_valid_probe_id_count}; "
            f"component_unmatched_valid_probe_id_count={component_unmatched_valid_probe_id_count}; "
            f"component_missing_official_probe_id_count={component_missing_official_probe_id_count}; "
            f"component_official_probe_coverage_ratio={component_official_probe_coverage_ratio}; "
            f"component_scope_ok={component_scope_ok}; "
            f"selected_component={selected_component or 'missing'}; "
            f"selected_component_source={selected_component_source or 'missing'}; "
            f"valid_probe_compared_components={';'.join(valid_probe_components) or 'missing'}; "
            f"valid_probe_compared_component_count={valid_probe_component_count}; "
            f"valid_probe_missing_compared_component_count={valid_probe_missing_component_count}; "
            f"best_component_by_rmse={best_component or 'missing'}; "
            f"selected_component_rmse={selected_component_rmse}; "
            f"selected_component_bias={selected_component_bias}; "
            f"selected_component_scaled_bias={selected_component_scaled_bias}; "
            f"selected_component_bias_abs_reduction_ratio={selected_component_bias_reduction}; "
            f"selected_component_mean_sim={selected_component_mean_sim}; "
            f"selected_component_mean_exp={selected_component_mean_exp}; "
            f"selected_component_mean_sim_to_exp_ratio={selected_component_mean_ratio}; "
            f"best_component_rmse={best_component_rmse}; "
            f"component_rmse_improvement_ratio={component_rmse_improvement}; "
            f"component_choice_not_explained={component_choice_not_explained}; "
            f"max_component_rmse_improvement_ratio={args.max_component_rmse_improvement_ratio}; "
            f"normalization_best_fit_scale={normalization_best_scale}; "
            f"normalization_scaled_improvement_ratio={normalization_scaled_improvement}; "
            f"normalization_scale_not_explained={normalization_scale_not_explained}; "
            f"component_probe_audit_sha256={component_probe_audit_sha256 or 'missing'}; "
            f"current_probe_audit_sha256={current_probe_audit_sha256 or 'missing'}; "
            f"component_probe_hash_matches={component_probe_hash_matches}; "
            f"component_official_sha256={component_official_sha256 or 'missing'}; "
            f"current_official_sha256={current_official_sha256 or 'missing'}; "
            f"component_official_hash_matches={component_official_hash_matches}; "
            f"max_normalization_best_scale_deviation={args.max_normalization_best_scale_deviation}; "
            f"min_normalization_scaled_improvement_ratio={args.min_normalization_scaled_improvement_ratio}; "
            f"metrics_component_normalization_gate={get_any(metrics, ['component_normalization_gate', 'ComponentNormalizationGate']) or 'ignored'}; "
            f"metrics_component_sensitivity_gate={get_any(metrics, ['component_sensitivity_gate', 'ComponentSensitivityGate']) or 'ignored'}; "
            f"metrics_normalization_scale_gate={get_any(metrics, ['normalization_scale_gate', 'NormalizationScaleGate']) or 'ignored'}; "
            f"metrics_streamwise_sign_gate={get_any(metrics, ['streamwise_sign_gate', 'StreamwiseSignGate']) or 'ignored'}; "
            f"audit={component_sensitivity_audit_path or 'missing'}; "
            f"audit_exists={component_sensitivity_audit_exists}; "
            f"metrics_component_sensitivity_audit={metric_component_sensitivity_audit or 'ignored'}"
        ),
        "Run scripts/audit_component_sensitivity.py and fix speed_ratio/streamwise_ratio/component selection, wind-vector sign or Uref/SI conversion before interpreting systematic bias.",
    )

    valid_n = as_int(get_any(metrics, ["valid_n", "ValidN"]))
    failed_n = as_int(get_any(metrics, ["failed_n", "FailedN"]))
    if probe_total is not None:
        valid_n = probe_total - (probe_failed or 0)
        failed_n = probe_failed
    failure_fraction = None
    if valid_n is not None and failed_n is not None and valid_n + failed_n > 0:
        failure_fraction = failed_n / float(valid_n + failed_n)
    add_gate(
        gates,
        "probe_mapping",
        PASS
        if detailed_probe_audit_ok
        and failure_fraction is not None
        and failure_fraction <= args.max_probe_failure_fraction
        else FAIL,
        (
            f"valid_n={valid_n}; failed_n={failed_n}; failure_fraction={failure_fraction}; "
            f"probe_audit_traceable={probe_audit_traceable}; "
            f"allow_summary_only_probe_metrics={probe_summary_override}; "
            f"{probe_error or ''}"
        ).strip(),
        "Export Data Probe audit CSV and fix tolerance/projection until official probes map reliably.",
    )

    u_bias = as_float(get_any(metrics, ["U_bias_ratio", "U_bias_Uref", "U_bias"]))
    u_rmse = as_float(get_any(metrics, ["U_RMSE_ratio", "U_RMSE_Uref", "U_RMSE"]))
    u_r2 = as_float(get_any(metrics, ["U_R2", "R2"]))
    slope = as_float(get_any(metrics, ["U_regression_slope", "slope"]))
    intercept = as_float(get_any(metrics, ["U_regression_intercept", "intercept"]))
    accuracy_failure_reasons = mean_velocity_accuracy_failure_reasons(
        u_bias=u_bias,
        u_rmse=u_rmse,
        u_r2=u_r2,
        slope=slope,
        intercept=intercept,
        max_u_bias_ratio=args.max_u_bias_ratio,
        max_u_rmse_ratio=args.max_u_rmse_ratio,
        min_u_r2=args.min_u_r2,
        min_slope=args.min_slope,
        max_slope=args.max_slope,
        max_intercept_abs=args.max_intercept_abs,
    )
    accuracy_pass = not accuracy_failure_reasons
    add_gate(
        gates,
        "mean_velocity_accuracy",
        PASS if accuracy_pass else FAIL,
        (
            f"U_bias_ratio={u_bias}; U_RMSE_ratio={u_rmse}; U_R2={u_r2}; "
            f"slope={slope}; intercept={intercept}; "
            f"failure_reasons={';'.join(accuracy_failure_reasons) or 'none'}"
        ),
        "Do not promote to paper-grade validation until bias, RMSE, R2, slope and intercept all meet thresholds.",
    )

    k_bias_ratio = as_float(get_any(metrics, ["k_bias_ratio", "K_bias_ratio"]))
    k_rmse_ratio = as_float(get_any(metrics, ["k_RMSE_ratio", "K_RMSE_ratio", "inlet_k_rmse_ratio"]))
    if k_bias_ratio is None or k_rmse_ratio is None:
        k_status = FAIL
        missing = []
        if k_bias_ratio is None:
            missing.append("k_bias_ratio")
        if k_rmse_ratio is None:
            missing.append("k_RMSE_ratio")
        k_evidence = "missing " + ",".join(missing)
    else:
        k_status = (
            PASS
            if abs(k_bias_ratio) <= args.max_k_bias_ratio and k_rmse_ratio <= args.max_k_rmse_ratio
            else FAIL
        )
        k_evidence = (
            f"k_bias_ratio={k_bias_ratio}; required abs <= {args.max_k_bias_ratio}; "
            f"k_RMSE_ratio={k_rmse_ratio}; required <= {args.max_k_rmse_ratio}"
        )
    add_gate(
        gates,
        "k_preservation_or_accuracy",
        k_status,
        k_evidence,
        "For turbulent-inflow validation, report k metrics from empty-tunnel and building probes.",
    )

    systematic_flag = str(get_any(metrics, ["systematic_bias_flag"]) or "").strip().lower()
    bias_diagnosis = str(get_any(metrics, ["bias_diagnosis"]) or "").strip()
    best_scale = as_float(get_any(metrics, ["U_best_fit_scale_to_exp"]))
    scaled_rmse = as_float(get_any(metrics, ["U_scaled_RMSE_ratio"]))
    scaled_improvement = as_float(get_any(metrics, ["U_scaled_improvement_ratio"]))
    systematic_tokens = {"true", "1", "yes", "fail", "risk", "underprediction", "overprediction"}
    inferred_systematic_bias = u_bias is not None and abs(u_bias) > args.max_u_bias_ratio
    inferred_systematic_direction = (
        "underprediction"
        if inferred_systematic_bias and u_bias is not None and u_bias < 0
        else ("overprediction" if inferred_systematic_bias and u_bias is not None and u_bias > 0 else "")
    )
    systematic_bias_present = systematic_flag in systematic_tokens or inferred_systematic_bias
    u_bias_percentage_points = u_bias * 100.0 if u_bias is not None else None
    max_u_bias_percentage_points = args.max_u_bias_ratio * 100.0
    add_gate(
        gates,
        "systematic_bias",
        FAIL if systematic_bias_present else PASS,
        (
            f"systematic_bias_flag={systematic_flag or 'missing/false'}; "
            f"inferred_from_U_bias={inferred_systematic_bias}; "
            f"inferred_direction={inferred_systematic_direction or 'none'}; "
            f"U_bias_ratio={u_bias}; U_bias_percentage_points={u_bias_percentage_points}; "
            f"threshold={args.max_u_bias_ratio}; threshold_percentage_points={max_u_bias_percentage_points}; "
            f"best_scale={best_scale}; scaled_RMSE={scaled_rmse}; "
            f"scaled_improvement={scaled_improvement}; diagnosis={bias_diagnosis or 'missing'}"
        ),
        "Investigate Uref/component/probe mapping first, then inlet, boundary, roughness and time averaging before tuning if systematic bias is present.",
    )

    prerequisite_labels = {
        "validation_protocol_content": "validation protocol content",
        "metrics_input_hash_traceability": "metrics hash traceability",
        "run_freshness": "fresh VTK inputs",
        "runtime_vtk_hash_traceability": "runtime VTK hash traceability",
        "time_averaging": "time averaging and stationarity",
        "native_time_averaging_traceability": "native FluidX3D final-window time averaging traceability",
        "custom_k_profile": "CustomTable U/k profile",
        "inlet_profile_preservation": "inlet U/k preservation",
        "inlet_profile_vtk_hash_traceability": "inlet profile VTK hash traceability",
        "k_preservation_or_accuracy": "k preservation or accuracy",
        "inlet_source_evidence": "inlet source evidence",
        "inlet_turbulence": "inlet turbulence evidence",
        "paper_grade_inlet_method": "paper-grade turbulent inlet method",
        "inlet_correlation": "inlet correlation evidence",
        "inlet_length_scale": "inlet length-scale evidence",
        "native_inlet_precondition_traceability": "native FluidX3D inlet U/k and correlation traceability",
        "boundary_source_evidence": "boundary source evidence",
        "boundary_protocol": "boundary protocol",
        "boundary_runtime": "boundary runtime face preservation",
        "native_boundary_traceability": "native FluidX3D AIJ boundary traceability",
        "roughness_or_precursor": "roughness or precursor evidence",
        "native_preconditions_full_evidence": "native FluidX3D preconditions",
        "native_probe_component_traceability": "native FluidX3D probe/component/Uref traceability",
        "native_baseline": "native FluidX3D baseline",
        "native_citylbm_parity": "native-CityLBM parity",
        "native_citylbm_accuracy_delta": "native-CityLBM paired accuracy delta",
        "grid_sensitivity": "grid sensitivity",
        "probe_audit_traceability": "probe audit traceability",
        "probe_source_window": "probe source window",
        "probe_projection_distance": "probe projection distance",
        "probe_grid_extent": "probe grid extent",
        "coordinate_normalization": "coordinate normalization",
        "compared_component": "compared velocity component",
        "component_normalization_sensitivity": "component/Uref sensitivity",
        "probe_mapping": "probe mapping",
    }
    by_key = gate_by_key(gates)
    failed_prerequisites = [
        f"{label}={str(by_key.get(key, {}).get('status') or 'MISSING')}"
        for key, label in prerequisite_labels.items()
        if by_key.get(key, {}).get("status") != PASS
    ]
    if not systematic_bias_present:
        interpretation_status = PASS
        interpretation_evidence = "no systematic bias detected by flag or U_bias threshold"
    elif failed_prerequisites:
        interpretation_status = FAIL
        interpretation_evidence = (
            "systematic bias is present, but prerequisite gates are not closed: "
            + "; ".join(failed_prerequisites)
            + ". Treat the current result as protocol/physics debugging evidence, not solver-accuracy validation."
        )
    else:
        interpretation_status = PASS
        interpretation_evidence = (
            "systematic bias is present, and prerequisite gates are closed; residual bias may be interpreted as "
            "a remaining physics/protocol issue rather than a coordinate, stale-output, inlet-transfer or postprocess artifact. "
            "This does not permit a solver-accuracy claim until mean_velocity_accuracy and systematic_bias both pass."
        )
    add_gate(
        gates,
        "systematic_bias_interpretation",
        interpretation_status,
        interpretation_evidence,
        "Close all prerequisite evidence gates before using systematic bias, R2 or regression metrics as paper-grade solver-accuracy evidence.",
    )
    prerequisites_closed = not failed_prerequisites
    root_cause_interpretation_allowed = allow_systematic_root_cause_interpretation(
        systematic_bias_present, failed_prerequisites
    )
    solver_accuracy_allowed = allow_solver_accuracy_interpretation(
        systematic_bias_present, accuracy_pass, failed_prerequisites
    )
    solver_accuracy_blockers = solver_accuracy_interpretation_blockers(
        systematic_bias_present, accuracy_pass, failed_prerequisites
    )
    systematic_bias_diagnostic = {
        "present": systematic_bias_present,
        "flag": systematic_flag,
        "inferred_from_U_bias": inferred_systematic_bias,
        "direction": inferred_systematic_direction,
        "U_bias_ratio": u_bias,
        "U_bias_percentage_points": u_bias_percentage_points,
        "threshold_ratio": args.max_u_bias_ratio,
        "threshold_percentage_points": max_u_bias_percentage_points,
        "best_fit_scale_to_exp": best_scale,
        "scaled_RMSE_ratio": scaled_rmse,
        "scaled_improvement_ratio": scaled_improvement,
        "bias_diagnosis": bias_diagnosis,
        "prerequisite_blockers": failed_prerequisites if systematic_bias_present else [],
        "prerequisite_blocker_count": len(failed_prerequisites) if systematic_bias_present else 0,
        "prerequisite_evidence_closed": prerequisites_closed,
        "root_cause_interpretation_allowed": root_cause_interpretation_allowed,
        "solver_accuracy_interpretation_allowed": solver_accuracy_allowed,
        "solver_accuracy_interpretation_blockers": solver_accuracy_blockers,
        "mean_velocity_accuracy_pass": accuracy_pass,
        "mean_velocity_accuracy_failure_reasons": accuracy_failure_reasons,
        "interpretation_gate": interpretation_status,
        "interpretation_evidence": interpretation_evidence,
    }

    failing = [gate for gate in gates if gate["status"] == FAIL]
    warnings = [gate for gate in gates if gate["status"] == WARN]
    verdict = FAIL if failing else (WARN if warnings else PASS)
    diagnostic_priority = build_diagnostic_priority(gates, metrics)
    return {
        "schema": "citylbm.validation_gate.v1",
        "run_dir": str(run_dir),
        "case": args.case,
        "software": args.software,
        "verdict": verdict,
        "paper_grade": verdict == PASS,
        "gates": gates,
        "diagnostic_priority": diagnostic_priority,
        "systematic_bias_diagnostic": systematic_bias_diagnostic,
        "thresholds": {
            "min_avg_frames": args.min_avg_frames,
            "max_mean_speed_stddev_ratio": args.max_mean_speed_stddev_ratio,
            "max_point_speed_stddev_ratio": args.max_point_speed_stddev_ratio,
            "max_u_bias_ratio": args.max_u_bias_ratio,
            "max_u_rmse_ratio": args.max_u_rmse_ratio,
            "min_u_r2": args.min_u_r2,
            "min_slope": args.min_slope,
            "max_slope": args.max_slope,
            "max_intercept_abs": args.max_intercept_abs,
            "max_k_bias_ratio": args.max_k_bias_ratio,
            "max_k_rmse_ratio": args.max_k_rmse_ratio,
            "max_empty_tunnel_u_bias_ratio": args.max_empty_tunnel_u_bias_ratio,
            "max_empty_tunnel_k_bias_ratio": args.max_empty_tunnel_k_bias_ratio,
            "max_official_coordinate_delta_m": args.max_official_coordinate_delta_m,
            "max_probe_failure_fraction": args.max_probe_failure_fraction,
            "max_probe_distance_dx_ratio": args.max_probe_distance_dx_ratio,
            "max_probe_tolerance_dx_ratio": args.max_probe_tolerance_dx_ratio,
            "max_component_rmse_improvement_ratio": args.max_component_rmse_improvement_ratio,
            "max_normalization_best_scale_deviation": args.max_normalization_best_scale_deviation,
            "min_normalization_scaled_improvement_ratio": args.min_normalization_scaled_improvement_ratio,
            "min_inlet_temporal_finite_fraction": args.min_inlet_temporal_finite_fraction,
            "min_inlet_spatial_finite_fraction": args.min_inlet_spatial_finite_fraction,
            "min_inlet_temporal_integral_lag_count": args.min_inlet_temporal_integral_lag_count,
            "min_inlet_spatial_integral_lag_count": args.min_inlet_spatial_integral_lag_count,
            "min_inlet_correlation_sample_count": args.min_inlet_correlation_sample_count,
            "min_inlet_correlation_adjacent_pair_count": args.min_inlet_correlation_adjacent_pair_count,
            "max_frontal_blockage_ratio": args.max_frontal_blockage_ratio,
            "max_estimated_mach": args.max_estimated_mach,
            "min_lbm_tau": args.min_lbm_tau,
            "max_lbm_tau": args.max_lbm_tau,
            "max_paper_dx_m": args.max_paper_dx_m,
            "min_grid_sensitivity_run_count": args.min_grid_sensitivity_run_count,
            "min_grid_refinement_ratio": args.min_grid_refinement_ratio,
            "max_grid_rmse_change_ratio": args.max_grid_rmse_change_ratio,
            "max_grid_bias_change_ratio": args.max_grid_bias_change_ratio,
            "grid_dx_tolerance": args.grid_dx_tolerance,
            "min_native_citylbm_parity_field_count": args.min_native_citylbm_parity_field_count,
            "min_native_citylbm_parity_gate_field_count": args.min_native_citylbm_parity_gate_field_count,
            "min_native_citylbm_parity_hash_field_count": args.min_native_citylbm_parity_hash_field_count,
            "max_native_citylbm_rmse_delta": args.max_native_citylbm_rmse_delta,
            "max_native_citylbm_abs_bias_delta": args.max_native_citylbm_abs_bias_delta,
            "max_native_citylbm_r2_drop": args.max_native_citylbm_r2_drop,
            "max_native_citylbm_slope_delta": args.max_native_citylbm_slope_delta,
            "max_native_citylbm_intercept_delta": args.max_native_citylbm_intercept_delta,
            "expected_compared_component": args.expected_compared_component,
            "expected_uref": args.expected_uref,
            "uref_tolerance": args.uref_tolerance,
            "expected_wind_vector": args.expected_wind_vector,
            "wind_vector_tolerance": args.wind_vector_tolerance,
            "allow_velocity_only_inlet": args.allow_velocity_only_inlet,
            "allow_summary_only_probe_metrics": args.allow_summary_only_probe_metrics,
        },
        "artifacts": {
            "case_metadata": str(metadata_path) if metadata_path else "",
            "validation_protocol_audit": str(audit_path) if audit_path else "",
            "inlet_source_audit": str(inlet_source_audit_path) if inlet_source_audit_path else "",
            "boundary_source_audit": str(boundary_source_audit_path) if boundary_source_audit_path else "",
            "inlet_correlation_audit": str(inlet_correlation_audit_path) if inlet_correlation_audit_path else "",
            "boundary_protocol_audit": str(boundary_audit_path) if boundary_audit_path else "",
            "boundary_runtime_audit": str(boundary_runtime_audit_path) if boundary_runtime_audit_path else "",
            "component_sensitivity_audit": str(component_sensitivity_audit_path) if component_sensitivity_audit_path else "",
            "grid_sensitivity_audit": str(grid_sensitivity_audit_path) if grid_sensitivity_audit_path else "",
            "native_preconditions_audit": str(native_preconditions_audit_path) if native_preconditions_audit_path else "",
            "native_citylbm_parity_audit": str(native_citylbm_parity_audit_path) if native_citylbm_parity_audit_path else "",
            "native_citylbm_accuracy_delta_audit": str(native_citylbm_accuracy_delta_audit_path) if native_citylbm_accuracy_delta_audit_path else "",
            "native_fluidx3d_baseline_manifest": str(manifest_path) if manifest_path else "",
            "metrics": str(metrics_path) if metrics_path else "",
            "probe_audit": str(probe_path) if probe_path else "",
            "official": str(official_path) if official_path else "",
        },
    }


def print_report(report: Dict[str, Any]) -> None:
    print(f"Validation gate verdict: {report['verdict']}")
    print(f"Paper-grade evidence: {report['paper_grade']}")
    for gate in report["gates"]:
        print(f"- [{gate['status']}] {gate['key']}: {gate['evidence']}")
        if gate["status"] != PASS and gate["required_next_action"]:
            print(f"  next: {gate['required_next_action']}")
    priorities = report.get("diagnostic_priority", [])
    if priorities:
        print("Diagnostic priority:")
        for item in priorities:
            print(
                "- rank {rank}: {key} [{status}] - {action}".format(
                    rank=item.get("rank"),
                    key=item.get("key"),
                    status=item.get("gate_status"),
                    action=item.get("next_action"),
                )
            )


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print_report(report)
    if report["verdict"] == PASS or args.allow_diagnostic:
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
