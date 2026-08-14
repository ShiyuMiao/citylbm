#!/usr/bin/env python3
"""Build a CityLBM validation metrics row from Data Probe audit output.

Inputs:
  - Data Probe audit CSV from Grasshopper.
  - Official measurement CSV, e.g. AIJ Case E RS_caseE.csv.

The output follows docs/validation_metrics_template.csv and is designed to feed
scripts/validation_gate.py. It focuses on traceable probe matching, selected
velocity component, Uref normalization, and systematic-bias detection.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


TEMPLATE_FIELDS = [
    "case",
    "wind_direction",
    "software",
    "version",
    "dx_m",
    "steps",
    "save_interval",
    "averaging_window",
    "available_frame_count",
    "source_time_steps",
    "source_first_time_step",
    "source_last_time_step",
    "latest_available_time_step",
    "selected_last_window",
    "source_steps_strictly_increasing",
    "source_step_spacing_uniform",
    "time_averaging_gate",
    "time_averaging_gate_reasons",
    "mean_speed_mps",
    "mean_speed_stddev_mps",
    "max_speed_stddev_mps",
    "mean_speed_stddev_ratio",
    "max_speed_stddev_ratio",
    "profile_csv",
    "geometry_scale",
    "Uref_mps",
    "Zref_m",
    "target_max_profile_velocity_lbm",
    "estimated_max_profile_mach",
    "lbm_tau",
    "lbm_nu",
    "physical_viscosity_m2s",
    "estimated_reynolds_number",
    "velocity_set",
    "les_model",
    "smagorinsky_cs",
    "solver_stability_warnings",
    "lbm_stability_gate",
    "normalization_valid",
    "velocity_component",
    "compared_component_consistency_gate",
    "compared_component_unique_values",
    "wind_vector",
    "wind_direction_valid",
    "inlet_face",
    "outlet_face",
    "lateral_faces",
    "domain_size_x_m",
    "domain_size_y_m",
    "domain_size_z_m",
    "max_building_height_m",
    "upstream_clearance_h",
    "downstream_clearance_h",
    "min_lateral_clearance_h",
    "top_clearance_h",
    "approx_frontal_blockage_ratio",
    "approx_plan_blockage_ratio",
    "blockage_protocol_gate",
    "boundary_protocol_gate",
    "boundary_evidence_source",
    "boundary_evidence_gate",
    "boundary_protocol_audit",
    "boundary_missing_evidence_fields",
    "boundary_equivalence_basis",
    "boundary_equivalence_supported",
    "boundary_evidence_class",
    "boundary_evidence_class_supported",
    "boundary_evidence_files_all_exist",
    "clearance_numeric_gate",
    "boundary_clearance_reasons",
    "boundary_summary",
    "synthetic_inlet_method",
    "inlet_distribution_treatment",
    "wall_roughness_treatment",
    "synthetic_update_interval",
    "synthetic_max_fraction",
    "synthetic_correlation_length_m",
    "inlet_length_scale_source",
    "inlet_length_scale_gate",
    "inlet_correlation_audit",
    "inlet_correlation_gate",
    "inlet_temporal_lag1_correlation",
    "inlet_temporal_lag1_abs_correlation",
    "inlet_spatial_adjacent_correlation",
    "inlet_streamwise_fluctuation_variance",
    "inlet_temporal_finite_correlation_fraction",
    "inlet_spatial_finite_correlation_fraction",
    "inlet_profile_audit",
    "inlet_profile_available_frame_count",
    "inlet_profile_frame_count",
    "inlet_profile_source_time_steps",
    "inlet_profile_source_first_time_step",
    "inlet_profile_source_last_time_step",
    "inlet_profile_latest_available_time_step",
    "inlet_profile_selected_last_window",
    "inlet_profile_source_steps_strictly_increasing",
    "inlet_profile_source_step_spacing_uniform",
    "inlet_profile_time_averaging_gate",
    "inlet_profile_time_averaging_gate_reasons",
    "inlet_negative_streamwise_fraction",
    "inlet_streamwise_direction_gate",
    "inlet_profile_gate",
    "inlet_u_profile_gate",
    "inlet_u_mae_ratio",
    "inlet_u_rmse_ratio",
    "inlet_k_profile_gate",
    "inlet_k_mae_ratio",
    "inlet_k_rmse_ratio",
    "empty_tunnel_gate",
    "empty_tunnel_U_bias_ratio",
    "empty_tunnel_k_bias_ratio",
    "native_fluidx3d_baseline_id",
    "native_baseline_gate",
    "probe_mapping_table",
    "probe_id_field",
    "probe_tolerance_m",
    "compared_component",
    "component_sensitivity_audit",
    "component_normalization_gate",
    "component_sensitivity_gate",
    "normalization_scale_gate",
    "best_component_by_rmse",
    "selected_component_rmse_ratio",
    "best_component_rmse_ratio",
    "component_rmse_improvement_ratio",
    "normalization_best_fit_scale",
    "normalization_scaled_improvement_ratio",
    "failed_probe_count_by_tolerance",
    "valid_n",
    "failed_n",
    "mean_probe_distance_m",
    "max_probe_distance_m",
    "max_official_coordinate_delta_m",
    "official_coordinate_delta_count",
    "U_MAE_ratio",
    "U_RMSE_ratio",
    "U_bias_ratio",
    "U_R2",
    "U_regression_slope",
    "U_regression_intercept",
    "U_max_abs_error",
    "U_mean_sim",
    "U_mean_exp",
    "U_mean_ratio_sim_to_exp",
    "U_best_fit_scale_to_exp",
    "U_scaled_MAE_ratio",
    "U_scaled_RMSE_ratio",
    "U_scaled_improvement_ratio",
    "bias_diagnosis",
    "k_MAE_m2s2",
    "k_RMSE_m2s2",
    "k_RMSE_ratio",
    "k_bias_m2s2",
    "k_bias_ratio",
    "systematic_bias_flag",
    "protocol_gate",
    "validation_gate_report",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge Data Probe audit rows with official AIJ measurements and compute validation metrics."
    )
    parser.add_argument("--probe-audit", required=True, help="Data Probe audit CSV.")
    parser.add_argument("--official", required=True, help="Official RS/measurement CSV.")
    parser.add_argument("--out", required=True, help="Output metrics CSV path.")
    parser.add_argument("--comparison-out", help="Optional per-probe comparison CSV.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--read-vtk-audit", help="Optional Read VTK Averaging Audit JSON.")
    parser.add_argument("--inlet-profile-audit", help="Optional inlet/empty-tunnel profile audit JSON from audit_inlet_profile_from_vtk.py.")
    parser.add_argument("--inlet-correlation-audit", help="Optional inlet correlation audit JSON from audit_inlet_correlation_from_vtk.py.")
    parser.add_argument("--boundary-protocol-audit", help="Optional boundary_protocol_audit.json from audit_boundary_protocol.py.")
    parser.add_argument("--component-sensitivity-audit", help="Optional component/Uref sensitivity JSON from audit_component_sensitivity.py.")
    parser.add_argument("--case", default="", help="Case label to write and optionally filter official rows.")
    parser.add_argument("--wind-direction", default="", help="Wind direction label to write and optionally filter official rows.")
    parser.add_argument("--software", default="citylbm")
    parser.add_argument("--version", default="0.3.0")
    parser.add_argument("--official-id-column", default="", help="Official probe ID column. Auto-detected when omitted.")
    parser.add_argument("--official-value-column", default="", help="Official measured value column. Auto-detected when omitted.")
    parser.add_argument("--probe-id-column", default="probe_id")
    parser.add_argument("--sim-value-column", default="compared_value")
    parser.add_argument("--u-ref", type=float, default=None, help="Reference velocity, used only for metadata checks.")
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--dx", type=float, default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--save-interval", type=int, default=None)
    parser.add_argument("--averaging-window", type=int, default=None)
    parser.add_argument("--source-time-steps", default="")
    parser.add_argument("--mean-speed", type=float, default=None)
    parser.add_argument("--mean-speed-stddev", type=float, default=None)
    parser.add_argument("--max-speed-stddev", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--max-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--profile-csv", default="")
    parser.add_argument("--geometry-scale", default="")
    parser.add_argument("--empty-tunnel-gate", default="")
    parser.add_argument("--empty-tunnel-u-bias-ratio", default="")
    parser.add_argument("--empty-tunnel-k-bias-ratio", default="")
    parser.add_argument("--native-baseline-id", default="")
    parser.add_argument("--native-baseline-gate", default="")
    parser.add_argument(
        "--lbm-stability-gate",
        default="",
        help="Runtime LBM stability evidence gate, e.g. solver_log_no_stability_warnings.",
    )
    parser.add_argument(
        "--solver-stability-warnings",
        default="",
        help="Solver log stability warning summary, e.g. none or no_stability_warnings.",
    )
    parser.add_argument("--k-mae", default="")
    parser.add_argument("--k-rmse", default="")
    parser.add_argument("--k-bias", default="")
    parser.add_argument("--k-bias-ratio", default="")
    parser.add_argument("--systematic-bias-threshold", type=float, default=0.20)
    parser.add_argument("--append", action="store_true", help="Append to metrics CSV if it exists.")
    return parser.parse_args()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def norm_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def find_column(rows: Sequence[Dict[str, str]], candidates: Iterable[str]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    normalized = {norm_key(column): column for column in columns}
    for candidate in candidates:
        found = normalized.get(norm_key(candidate))
        if found:
            return found
    for column in columns:
        ncol = norm_key(column)
        for candidate in candidates:
            if norm_key(candidate) in ncol:
                return column
    return ""


def get_value(row: Dict[str, str], column: str) -> str:
    if not column:
        return ""
    if column in row:
        return row[column]
    target = norm_key(column)
    for key, value in row.items():
        if norm_key(key) == target:
            return value
    return ""


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def as_bool(value: Any) -> Optional[bool]:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "ok", "pass"}:
        return True
    if text in {"false", "0", "no", "n", "fail"}:
        return False
    return None


def csv_bool(value: Optional[bool]) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.10g}"
    return str(value)


def filter_official(rows: List[Dict[str, str]], case: str, wind_direction: str) -> List[Dict[str, str]]:
    if not rows:
        return rows
    case_col = find_column(rows, ["case"])
    wind_col = find_column(rows, ["Wind_direction", "wind_direction", "direction", "wind"])
    filtered = rows
    if case and case_col:
        filtered = [row for row in filtered if get_value(row, case_col).strip().lower() == case.lower()]
    if wind_direction and wind_col:
        filtered = [
            row
            for row in filtered
            if get_value(row, wind_col).strip().lower() == wind_direction.lower()
        ]
    return filtered


def build_official_lookup(rows: List[Dict[str, str]], id_column: str) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in rows:
        probe_id = get_value(row, id_column).strip()
        if probe_id:
            lookup[probe_id] = row
    return lookup


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def rmse(errors: Sequence[float]) -> Optional[float]:
    if not errors:
        return None
    return math.sqrt(sum(error * error for error in errors) / len(errors))


def r2(sim: Sequence[float], exp: Sequence[float]) -> Optional[float]:
    if len(sim) < 2 or len(sim) != len(exp):
        return None
    exp_mean = sum(exp) / len(exp)
    ss_tot = sum((value - exp_mean) ** 2 for value in exp)
    if ss_tot <= 1.0e-15:
        return None
    ss_res = sum((s - e) ** 2 for s, e in zip(sim, exp))
    return 1.0 - ss_res / ss_tot


def regression(sim: Sequence[float], exp: Sequence[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(sim) < 2 or len(sim) != len(exp):
        return None, None
    x_mean = sum(exp) / len(exp)
    y_mean = sum(sim) / len(sim)
    denom = sum((x - x_mean) ** 2 for x in exp)
    if denom <= 1.0e-15:
        return None, None
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(exp, sim)) / denom
    intercept = y_mean - slope * x_mean
    return slope, intercept


def best_scale_to_exp(sim: Sequence[float], exp: Sequence[float]) -> Optional[float]:
    if len(sim) == 0 or len(sim) != len(exp):
        return None
    denom = sum(s * s for s in sim)
    if denom <= 1.0e-15:
        return None
    return sum(s * e for s, e in zip(sim, exp)) / denom


def diagnose_bias(
    u_bias: Optional[float],
    u_rmse: Optional[float],
    scaled_rmse: Optional[float],
    scale: Optional[float],
    slope: Optional[float],
    systematic_threshold: float,
) -> str:
    if u_bias is None or abs(u_bias) < systematic_threshold:
        return ""
    direction = "systematic_underprediction" if u_bias < 0 else "systematic_overprediction"
    scale_text = "" if scale is None else f"best_scale={scale:.6g}"
    if u_rmse is not None and scaled_rmse is not None and u_rmse > 1.0e-12:
        improvement = 1.0 - scaled_rmse / u_rmse
        if improvement >= 0.50 and scale is not None and (scale < 0.80 or scale > 1.20):
            return f"{direction}; scale_like_error; {scale_text}; audit_Uref_units_velocity_component"
        if improvement >= 0.25:
            return f"{direction}; mixed_scale_and_protocol_error; {scale_text}; audit_normalization_then_boundary_inlet"
    if slope is not None and (slope < 0.70 or slope > 1.30):
        return f"{direction}; regression_slope_out_of_range; {scale_text}; audit_component_probe_mapping_boundary"
    return f"{direction}; protocol_or_physics_error_likely; {scale_text}; audit_inlet_boundary_roughness_time_average"


def metadata_field(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def vector_field(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, dict):
            x = value.get("X")
            y = value.get("Y")
            z = value.get("Z")
            if x is not None and y is not None and z is not None:
                return f"({x},{y},{z})"
        if value not in (None, ""):
            return str(value)
    return ""


def nested(metadata: Dict[str, Any], parent: str, key: str) -> str:
    value = metadata.get(parent)
    if isinstance(value, dict):
        child = value.get(key)
        if child not in (None, ""):
            return str(child)
    return ""


def infer_synthetic_inlet_method(metadata: Dict[str, Any]) -> str:
    method = metadata_field(metadata, "SyntheticTurbulentInletMethod", "TurbulenceMethod")
    if method:
        return method
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True:
        return "synthetic-eddy"
    if as_bool(nested(metadata, "RecyclingRescaling", "Enabled")) is True:
        return "recycling-rescaling"
    return ""


def infer_inlet_distribution_treatment(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletDistributionTreatment")
    if explicit:
        return explicit
    method = infer_synthetic_inlet_method(metadata).lower()
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True or "synthetic" in method:
        if as_bool(nested(metadata, "SyntheticEddy", "DeviceSemStressDdf")) is True:
            return "synthetic_eddy_stress_ddf_diagnostic_unverified"
        if as_bool(nested(metadata, "SyntheticEddy", "DeviceSideInlet")) is True:
            return "synthetic_eddy_velocity_field_only"
        return "synthetic_eddy_host_velocity_field_only"
    if "digital" in method:
        return "digital_filter_velocity_field_only_unless_distribution_evidence_archived"
    if "recycling" in method:
        return "recycling_rescaling_velocity_field_only_unless_precursor_evidence_archived"
    if "hash" in method or "random" in method:
        return "uncorrelated_rms_k_velocity_field_only"
    return ""


def infer_synthetic_update_interval(metadata: Dict[str, Any]) -> str:
    return metadata_field(metadata, "SyntheticTurbulenceUpdateInterval", "InletUpdateInterval")


def infer_synthetic_correlation_length_m(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulenceCorrelationLengthM")
    if explicit:
        return explicit
    dx = as_float(metadata.get("Dx"))
    lx_cells = as_float(nested(metadata, "SyntheticEddy", "LxCells"))
    if dx is not None and lx_cells is not None:
        return fmt(dx * lx_cells)
    return ""


def infer_inlet_length_scale_source(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletLengthScaleSource")
    if explicit:
        return explicit
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True:
        return "synthetic_eddy_case_parameter_no_external_length_scale_source"
    if "digital" in infer_synthetic_inlet_method(metadata).lower():
        return "digital_filter_case_parameter_no_external_length_scale_source"
    return ""


def infer_inlet_length_scale_gate(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletLengthScaleGate")
    if explicit:
        return explicit
    source = infer_inlet_length_scale_source(metadata)
    if source:
        return "diagnostic_missing_validated_length_scale_source"
    return ""


def infer_wall_roughness_treatment(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "WallRoughnessTreatment")
    if explicit:
        return explicit
    if as_bool(nested(metadata, "RoughnessLayout", "Enabled")) is False:
        return "roughness_layout_disabled_no_wind_tunnel_source"
    rough_wall = metadata.get("RoughWallDrag") if isinstance(metadata.get("RoughWallDrag"), dict) else {}
    if as_bool(rough_wall.get("VolumeForceEnabled")) is True:
        return "equivalent_rough_wall_drag_diagnostic"
    return ""


def audit_float(audit: Dict[str, Any], key: str) -> Optional[float]:
    return as_float(audit.get(key))


def audit_int(audit: Dict[str, Any], key: str) -> Optional[int]:
    value = audit.get(key)
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def audit_source_steps(audit: Dict[str, Any]) -> str:
    csv_value = audit.get("source_time_steps_csv")
    if csv_value not in (None, ""):
        return str(csv_value)
    steps = audit.get("source_time_steps")
    if isinstance(steps, list):
        return ",".join(str(step) for step in steps)
    return ""


def audit_field(audit: Dict[str, Any], key: str) -> str:
    value = audit.get(key)
    if value not in (None, ""):
        return str(value)
    return ""


def audit_gate(audit: Dict[str, Any], key: str) -> str:
    value = audit.get(key)
    return str(value).strip().lower() if value not in (None, "") else ""


def first_int(*values: Optional[int]) -> Optional[int]:
    for value in values:
        if value is not None:
            return value
    return None


def first_float(*values: Optional[float]) -> Optional[float]:
    for value in values:
        if value is not None:
            return value
    return None


def first_text(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def first_bool_text(*values: Any) -> str:
    for value in values:
        parsed = as_bool(value)
        if parsed is not None:
            return csv_bool(parsed)
    return ""


def main() -> int:
    args = parse_args()
    probe_path = Path(args.probe_audit).resolve()
    official_path = Path(args.official).resolve()
    out_path = Path(args.out).resolve()
    comparison_path = Path(args.comparison_out).resolve() if args.comparison_out else None
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
    read_vtk_audit = read_json(Path(args.read_vtk_audit).resolve() if args.read_vtk_audit else None)
    inlet_profile_audit = read_json(Path(args.inlet_profile_audit).resolve() if args.inlet_profile_audit else None)
    inlet_correlation_audit = read_json(Path(args.inlet_correlation_audit).resolve() if args.inlet_correlation_audit else None)
    boundary_protocol_audit = read_json(Path(args.boundary_protocol_audit).resolve() if args.boundary_protocol_audit else None)
    component_sensitivity_audit = read_json(Path(args.component_sensitivity_audit).resolve() if args.component_sensitivity_audit else None)

    probe_rows = read_csv(probe_path)
    official_rows = filter_official(read_csv(official_path), args.case, args.wind_direction)
    if not probe_rows:
        raise SystemExit("Probe audit CSV has no rows.")
    if not official_rows:
        raise SystemExit("Official measurement CSV has no matching rows.")

    official_id_col = args.official_id_column or find_column(official_rows, ["No.", "No", "probe_id", "id", "point"])
    official_value_col = args.official_value_column or find_column(
        official_rows,
        ["Velocity_Ratio", "velocity_ratio", "V_exp_ratio", "U_exp_ratio", "U", "Velocity", "WindSpeed"],
    )
    if not official_id_col:
        raise SystemExit("Could not detect official probe ID column. Use --official-id-column.")
    if not official_value_col:
        raise SystemExit("Could not detect official measured value column. Use --official-value-column.")

    official = build_official_lookup(official_rows, official_id_col)
    sim_values: List[float] = []
    exp_values: List[float] = []
    errors: List[float] = []
    abs_errors: List[float] = []
    distances: List[float] = []
    official_coordinate_deltas: List[float] = []
    comparison_rows: List[Dict[str, Any]] = []
    failed = 0
    normalization_values: List[bool] = []
    wind_values: List[bool] = []
    probe_urefs: List[float] = []
    compared_component = ""
    compared_components: List[str] = []
    tolerance = ""

    for row in probe_rows:
        probe_id = get_value(row, args.probe_id_column).strip()
        official_row = official.get(probe_id)
        status = get_value(row, "failed").strip().lower()
        validation_status = get_value(row, "validation_status").strip().lower()
        if not official_row:
            failed += 1
            continue
        sim = as_float(get_value(row, args.sim_value_column))
        exp = as_float(get_value(official_row, official_value_col))
        failed_flag = as_bool(status)
        if failed_flag is True or "fail" in validation_status or sim is None or exp is None:
            failed += 1
            continue
        sim_values.append(sim)
        exp_values.append(exp)
        error = sim - exp
        errors.append(error)
        abs_errors.append(abs(error))
        distance = as_float(get_value(row, "nearest_distance"))
        if distance is not None:
            distances.append(distance)
        coord_deltas = []
        for coord in ["x", "y", "z"]:
            sim_coord = as_float(get_value(row, coord))
            official_coord = as_float(get_value(official_row, coord))
            if sim_coord is not None and official_coord is not None:
                coord_deltas.append(abs(sim_coord - official_coord))
        coordinate_delta = max(coord_deltas) if coord_deltas else None
        if coordinate_delta is not None:
            official_coordinate_deltas.append(coordinate_delta)
        normalized = as_bool(get_value(row, "normalization_valid"))
        wind_valid = as_bool(get_value(row, "wind_direction_valid"))
        if normalized is not None:
            normalization_values.append(normalized)
        if wind_valid is not None:
            wind_values.append(wind_valid)
        row_uref = as_float(get_value(row, "Uref"))
        if row_uref is not None:
            probe_urefs.append(row_uref)
        if not compared_component:
            compared_component = get_value(row, "compared_component")
        row_compared_component = get_value(row, "compared_component").strip().lower()
        if row_compared_component:
            compared_components.append(row_compared_component)
        if not tolerance:
            tolerance = get_value(row, "tolerance")
        comparison_rows.append(
            {
                "probe_id": probe_id,
                "sim_value": sim,
                "official_value": exp,
                "error": error,
                "abs_error": abs(error),
                "nearest_distance": distance,
                "official_coordinate_delta": coordinate_delta,
                "compared_component": get_value(row, "compared_component"),
                "normalization_valid": get_value(row, "normalization_valid"),
                "wind_direction_valid": get_value(row, "wind_direction_valid"),
            }
        )

    valid_n = len(sim_values)
    if valid_n == 0:
        raise SystemExit("No valid matched probes after filtering failed rows.")

    u_mae = mean(abs_errors)
    u_rmse = rmse(errors)
    u_bias = mean(errors)
    u_r2 = r2(sim_values, exp_values)
    slope, intercept = regression(sim_values, exp_values)
    max_abs = max(abs_errors) if abs_errors else None
    mean_sim = mean(sim_values)
    mean_exp = mean(exp_values)
    mean_ratio = mean_sim / mean_exp if mean_sim is not None and mean_exp is not None and abs(mean_exp) > 1.0e-15 else None
    best_scale = best_scale_to_exp(sim_values, exp_values)
    scaled_errors = [best_scale * s - e for s, e in zip(sim_values, exp_values)] if best_scale is not None else []
    scaled_abs_errors = [abs(error) for error in scaled_errors]
    scaled_mae = mean(scaled_abs_errors)
    scaled_rmse = rmse(scaled_errors)
    scaled_improvement = (
        1.0 - scaled_rmse / u_rmse
        if scaled_rmse is not None and u_rmse is not None and u_rmse > 1.0e-12
        else None
    )
    bias_diagnosis = diagnose_bias(u_bias, u_rmse, scaled_rmse, best_scale, slope, args.systematic_bias_threshold)
    systematic_flag = ""
    if u_bias is not None and abs(u_bias) >= args.systematic_bias_threshold:
        systematic_flag = "underprediction" if u_bias < 0 else "overprediction"
    unique_compared_components = sorted(set(compared_components))
    component_consistency_gate = (
        "pass"
        if len(unique_compared_components) == 1 and bool(unique_compared_components[0])
        else "fail_mixed_or_missing_compared_component"
    )
    normalization_gate_value = all(normalization_values) if normalization_values else None
    wind_gate_value = all(wind_values) if wind_values else None
    unique_probe_urefs = sorted({round(value, 12) for value in probe_urefs})
    inferred_uref = args.u_ref
    if inferred_uref is None:
        if len(unique_probe_urefs) == 1:
            inferred_uref = probe_urefs[0]
        else:
            inferred_uref = as_float(
                metadata_field(metadata, "ReferenceWindSpeedMps", "ReferenceWindSpeed", "UrefMps", "Uref")
            )
    inferred_zref = args.z_ref
    if inferred_zref is None:
        inferred_zref = as_float(metadata_field(metadata, "ReferenceHeightM", "ZrefM", "ReferenceHeight"))
    coordinate_delta_count = len(official_coordinate_deltas)
    max_coordinate_delta = max(official_coordinate_deltas) if official_coordinate_deltas else None
    protocol_failures: List[str] = []
    if args.u_ref is None and len(unique_probe_urefs) > 1:
        protocol_failures.append("fail_mixed_probe_uref")
    if component_consistency_gate != "pass":
        protocol_failures.append(component_consistency_gate)
    if normalization_gate_value is not True:
        protocol_failures.append("fail_missing_or_invalid_uref_normalization")
    if wind_gate_value is not True:
        protocol_failures.append("fail_missing_or_invalid_wind_direction")
    if coordinate_delta_count != valid_n:
        protocol_failures.append("fail_incomplete_official_coordinate_audit")
    elif max_coordinate_delta is None or max_coordinate_delta > 1.0e-6:
        protocol_failures.append("fail_probe_coordinate_mismatch")
    if failed > 0:
        protocol_failures.append("fail_unmatched_or_failed_probes")
    metrics_protocol_gate = (
        "metrics_ready_for_validation_gate"
        if not protocol_failures
        else ";".join(protocol_failures)
    )

    boundary_audit = metadata.get("BoundaryProtocolAudit") if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    blockage_audit = boundary_audit.get("BlockageDiagnostics") if isinstance(boundary_audit.get("BlockageDiagnostics"), dict) else {}
    boundary_missing_fields = boundary_protocol_audit.get("missing_evidence_fields")
    if isinstance(boundary_missing_fields, list):
        boundary_missing_fields_text = ";".join(str(field) for field in boundary_missing_fields)
    else:
        boundary_missing_fields_text = str(boundary_missing_fields or "")
    averaging_window = first_int(
        audit_int(read_vtk_audit, "averaged_frame_count"),
        audit_int(inlet_profile_audit, "frame_count"),
        args.averaging_window,
    )
    source_time_steps = audit_source_steps(read_vtk_audit)
    if not source_time_steps:
        source_time_steps = audit_source_steps(inlet_profile_audit)
    if not source_time_steps:
        source_time_steps = args.source_time_steps
    available_frame_count = first_int(
        audit_int(read_vtk_audit, "available_frame_count"),
        audit_int(inlet_profile_audit, "available_frame_count"),
    )
    source_first_time_step = first_int(
        audit_int(read_vtk_audit, "source_first_time_step"),
        audit_int(inlet_profile_audit, "source_first_time_step"),
    )
    source_last_time_step = first_int(
        audit_int(read_vtk_audit, "source_last_time_step"),
        audit_int(inlet_profile_audit, "source_last_time_step"),
    )
    latest_available_time_step = first_int(
        audit_int(read_vtk_audit, "latest_available_time_step"),
        audit_int(inlet_profile_audit, "latest_available_time_step"),
    )
    selected_last_window = first_bool_text(
        read_vtk_audit.get("selected_last_window"),
        inlet_profile_audit.get("selected_last_window"),
    )
    source_steps_strictly_increasing = first_bool_text(
        read_vtk_audit.get("source_steps_strictly_increasing"),
        inlet_profile_audit.get("source_steps_strictly_increasing"),
    )
    source_step_spacing_uniform = first_bool_text(
        read_vtk_audit.get("source_step_spacing_uniform"),
        inlet_profile_audit.get("source_step_spacing_uniform"),
    )
    time_averaging_gate = first_text(
        read_vtk_audit.get("time_averaging_gate"),
        inlet_profile_audit.get("time_averaging_gate"),
    )
    time_averaging_gate_reasons = first_text(
        read_vtk_audit.get("time_averaging_gate_reasons_csv"),
        inlet_profile_audit.get("time_averaging_gate_reasons_csv"),
    )
    mean_speed = args.mean_speed if args.mean_speed is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_mps"),
        audit_float(inlet_profile_audit, "mean_speed_mps"),
    )
    mean_speed_stddev = args.mean_speed_stddev if args.mean_speed_stddev is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_stddev_mps"),
        audit_float(inlet_profile_audit, "mean_speed_stddev_mps"),
    )
    max_speed_stddev = args.max_speed_stddev if args.max_speed_stddev is not None else first_float(
        audit_float(read_vtk_audit, "max_speed_stddev_mps"),
        audit_float(inlet_profile_audit, "max_speed_stddev_mps"),
    )
    mean_speed_stddev_ratio = args.mean_speed_stddev_ratio if args.mean_speed_stddev_ratio is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_stddev_ratio"),
        audit_float(inlet_profile_audit, "mean_speed_stddev_ratio"),
    )
    max_speed_stddev_ratio = args.max_speed_stddev_ratio if args.max_speed_stddev_ratio is not None else first_float(
        audit_float(read_vtk_audit, "max_speed_stddev_ratio"),
        audit_float(inlet_profile_audit, "max_speed_stddev_ratio"),
    )
    inlet_profile_gate = audit_gate(inlet_profile_audit, "inlet_profile_gate")
    inlet_u_profile_gate = audit_gate(inlet_profile_audit, "inlet_u_profile_gate")
    inlet_k_profile_gate = audit_gate(inlet_profile_audit, "inlet_k_profile_gate")
    inlet_streamwise_direction_gate = audit_gate(inlet_profile_audit, "inlet_streamwise_direction_gate")
    inlet_negative_streamwise_fraction = audit_float(inlet_profile_audit, "negative_streamwise_fraction")
    inlet_u_mae_ratio = audit_float(inlet_profile_audit, "U_MAE_ratio")
    inlet_u_rmse_ratio = audit_float(inlet_profile_audit, "U_RMSE_ratio")
    inlet_k_mae_ratio = audit_float(inlet_profile_audit, "k_MAE_ratio")
    inlet_k_rmse_ratio = audit_float(inlet_profile_audit, "k_RMSE_ratio")
    inlet_u_bias_ratio = audit_float(inlet_profile_audit, "U_bias_ratio")
    inlet_k_bias_ratio = audit_float(inlet_profile_audit, "k_bias_ratio")
    inlet_k_mae = audit_float(inlet_profile_audit, "k_MAE_m2s2")
    inlet_k_rmse = audit_float(inlet_profile_audit, "k_RMSE_m2s2")
    inlet_k_bias = audit_float(inlet_profile_audit, "k_bias_m2s2")
    metrics = {field: "" for field in TEMPLATE_FIELDS}
    metrics.update(
        {
            "case": args.case,
            "wind_direction": args.wind_direction,
            "software": args.software,
            "version": args.version,
            "dx_m": fmt(args.dx),
            "steps": fmt(args.steps),
            "save_interval": fmt(args.save_interval),
            "averaging_window": fmt(averaging_window),
            "available_frame_count": fmt(available_frame_count),
            "source_time_steps": source_time_steps,
            "source_first_time_step": fmt(source_first_time_step),
            "source_last_time_step": fmt(source_last_time_step),
            "latest_available_time_step": fmt(latest_available_time_step),
            "selected_last_window": selected_last_window,
            "source_steps_strictly_increasing": source_steps_strictly_increasing,
            "source_step_spacing_uniform": source_step_spacing_uniform,
            "time_averaging_gate": time_averaging_gate,
            "time_averaging_gate_reasons": time_averaging_gate_reasons,
            "mean_speed_mps": fmt(mean_speed),
            "mean_speed_stddev_mps": fmt(mean_speed_stddev),
            "max_speed_stddev_mps": fmt(max_speed_stddev),
            "mean_speed_stddev_ratio": fmt(mean_speed_stddev_ratio),
            "max_speed_stddev_ratio": fmt(max_speed_stddev_ratio),
            "profile_csv": args.profile_csv,
            "geometry_scale": args.geometry_scale,
            "Uref_mps": fmt(inferred_uref),
            "Zref_m": fmt(inferred_zref),
            "target_max_profile_velocity_lbm": metadata_field(metadata, "TargetMaxProfileVelocityLbm"),
            "estimated_max_profile_mach": metadata_field(metadata, "EstimatedMaxProfileMach"),
            "lbm_tau": metadata_field(metadata, "LbmTau"),
            "lbm_nu": metadata_field(metadata, "LbmNu"),
            "physical_viscosity_m2s": metadata_field(metadata, "PhysicalViscosityM2s"),
            "estimated_reynolds_number": metadata_field(metadata, "EstimatedReynoldsNumber"),
            "velocity_set": metadata_field(metadata, "VelocitySet"),
            "les_model": metadata_field(metadata, "LesModel"),
            "smagorinsky_cs": metadata_field(metadata, "SmagorinskyCs"),
            "solver_stability_warnings": args.solver_stability_warnings or audit_field(read_vtk_audit, "solver_stability_warnings") or metadata_field(metadata, "SolverStabilityWarnings"),
            "lbm_stability_gate": args.lbm_stability_gate or audit_field(read_vtk_audit, "lbm_stability_gate") or metadata_field(metadata, "LbmStabilityGate"),
            "normalization_valid": csv_bool(normalization_gate_value),
            "velocity_component": compared_component,
            "compared_component_consistency_gate": component_consistency_gate,
            "compared_component_unique_values": ";".join(unique_compared_components),
            "wind_vector": vector_field(metadata, "WindDirectionUnitVector", "WindDirection", "wind_vector"),
            "wind_direction_valid": csv_bool(wind_gate_value),
            "inlet_face": nested(metadata, "BoundaryProtocolAudit", "InletFace"),
            "outlet_face": nested(metadata, "BoundaryProtocolAudit", "OutletFace"),
            "lateral_faces": nested(metadata, "BoundaryProtocolAudit", "LateralFaces"),
            "domain_size_x_m": nested(boundary_audit, "DomainSizeM", "X"),
            "domain_size_y_m": nested(boundary_audit, "DomainSizeM", "Y"),
            "domain_size_z_m": nested(boundary_audit, "DomainSizeM", "Z"),
            "max_building_height_m": nested(boundary_audit, "BuildingBoundsM", "Height"),
            "upstream_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Upstream"),
            "downstream_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Downstream"),
            "min_lateral_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "MinLateral"),
            "top_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Top"),
            "approx_frontal_blockage_ratio": blockage_audit.get("ApproxFrontalBlockageRatio", ""),
            "approx_plan_blockage_ratio": blockage_audit.get("ApproxPlanBlockageRatio", ""),
            "blockage_protocol_gate": blockage_audit.get("Gate", ""),
            "boundary_protocol_gate": str(boundary_protocol_audit.get("boundary_protocol_gate", "")) or str(boundary_audit.get("Gate", "")),
            "boundary_evidence_source": str(boundary_protocol_audit.get("boundary_evidence_source", "")) or metadata_field(metadata, "BoundaryProtocolEvidenceSource") or boundary_audit.get("ProtocolEvidenceSource", ""),
            "boundary_evidence_gate": str(boundary_protocol_audit.get("boundary_evidence_gate", "")) or metadata_field(metadata, "BoundaryProtocolEvidenceGate") or boundary_audit.get("ProtocolEvidenceGate", ""),
            "boundary_protocol_audit": str(Path(args.boundary_protocol_audit).resolve()) if args.boundary_protocol_audit else "",
            "boundary_missing_evidence_fields": boundary_missing_fields_text,
            "boundary_equivalence_basis": str(boundary_protocol_audit.get("boundary_equivalence_basis", "")),
            "boundary_equivalence_supported": csv_bool(boundary_protocol_audit.get("boundary_equivalence_supported")),
            "boundary_evidence_class": str(boundary_protocol_audit.get("boundary_evidence_class", "")),
            "boundary_evidence_class_supported": csv_bool(boundary_protocol_audit.get("boundary_evidence_class_supported")),
            "boundary_evidence_files_all_exist": csv_bool(boundary_protocol_audit.get("boundary_evidence_files_all_exist")),
            "clearance_numeric_gate": str(boundary_protocol_audit.get("clearance_numeric_gate", "")),
            "boundary_clearance_reasons": ";".join(
                str(reason) for reason in boundary_protocol_audit.get("clearance_numeric_gate_reasons", [])
            )
            if isinstance(boundary_protocol_audit.get("clearance_numeric_gate_reasons"), list)
            else str(boundary_protocol_audit.get("clearance_numeric_gate_reasons", "")),
            "boundary_summary": metadata_field(metadata, "BoundaryConditionSummary"),
            "synthetic_inlet_method": infer_synthetic_inlet_method(metadata),
            "inlet_distribution_treatment": infer_inlet_distribution_treatment(metadata),
            "wall_roughness_treatment": infer_wall_roughness_treatment(metadata),
            "synthetic_update_interval": infer_synthetic_update_interval(metadata),
            "synthetic_max_fraction": metadata_field(metadata, "SyntheticTurbulenceMaxFractionOfMean"),
            "synthetic_correlation_length_m": infer_synthetic_correlation_length_m(metadata),
            "inlet_length_scale_source": infer_inlet_length_scale_source(metadata),
            "inlet_length_scale_gate": infer_inlet_length_scale_gate(metadata),
            "inlet_correlation_audit": str(Path(args.inlet_correlation_audit).resolve()) if args.inlet_correlation_audit else "",
            "inlet_correlation_gate": audit_gate(inlet_correlation_audit, "inlet_correlation_gate"),
            "inlet_temporal_lag1_correlation": fmt(audit_float(inlet_correlation_audit, "temporal_lag1_mean_correlation")),
            "inlet_temporal_lag1_abs_correlation": fmt(audit_float(inlet_correlation_audit, "temporal_lag1_abs_mean_correlation")),
            "inlet_spatial_adjacent_correlation": fmt(audit_float(inlet_correlation_audit, "spatial_adjacent_mean_correlation")),
            "inlet_streamwise_fluctuation_variance": fmt(audit_float(inlet_correlation_audit, "mean_streamwise_fluctuation_variance")),
            "inlet_temporal_finite_correlation_fraction": fmt(audit_float(inlet_correlation_audit, "temporal_finite_correlation_fraction")),
            "inlet_spatial_finite_correlation_fraction": fmt(audit_float(inlet_correlation_audit, "spatial_finite_correlation_fraction")),
            "inlet_profile_audit": str(Path(args.inlet_profile_audit).resolve()) if args.inlet_profile_audit else "",
            "inlet_profile_available_frame_count": fmt(audit_int(inlet_profile_audit, "available_frame_count")),
            "inlet_profile_frame_count": fmt(audit_int(inlet_profile_audit, "frame_count")),
            "inlet_profile_source_time_steps": audit_source_steps(inlet_profile_audit),
            "inlet_profile_source_first_time_step": fmt(audit_int(inlet_profile_audit, "source_first_time_step")),
            "inlet_profile_source_last_time_step": fmt(audit_int(inlet_profile_audit, "source_last_time_step")),
            "inlet_profile_latest_available_time_step": fmt(audit_int(inlet_profile_audit, "latest_available_time_step")),
            "inlet_profile_selected_last_window": first_bool_text(inlet_profile_audit.get("selected_last_window")),
            "inlet_profile_source_steps_strictly_increasing": first_bool_text(inlet_profile_audit.get("source_steps_strictly_increasing")),
            "inlet_profile_source_step_spacing_uniform": first_bool_text(inlet_profile_audit.get("source_step_spacing_uniform")),
            "inlet_profile_time_averaging_gate": audit_gate(inlet_profile_audit, "time_averaging_gate"),
            "inlet_profile_time_averaging_gate_reasons": ";".join(
                str(reason) for reason in inlet_profile_audit.get("time_averaging_gate_reasons", [])
            )
            if isinstance(inlet_profile_audit.get("time_averaging_gate_reasons"), list)
            else str(inlet_profile_audit.get("time_averaging_gate_reasons", "")),
            "inlet_negative_streamwise_fraction": fmt(inlet_negative_streamwise_fraction),
            "inlet_streamwise_direction_gate": inlet_streamwise_direction_gate,
            "inlet_profile_gate": inlet_profile_gate,
            "inlet_u_profile_gate": inlet_u_profile_gate,
            "inlet_u_mae_ratio": fmt(inlet_u_mae_ratio),
            "inlet_u_rmse_ratio": fmt(inlet_u_rmse_ratio),
            "inlet_k_profile_gate": inlet_k_profile_gate,
            "inlet_k_mae_ratio": fmt(inlet_k_mae_ratio),
            "inlet_k_rmse_ratio": fmt(inlet_k_rmse_ratio),
            "empty_tunnel_gate": args.empty_tunnel_gate or inlet_profile_gate,
            "empty_tunnel_U_bias_ratio": args.empty_tunnel_u_bias_ratio or fmt(inlet_u_bias_ratio),
            "empty_tunnel_k_bias_ratio": args.empty_tunnel_k_bias_ratio or fmt(inlet_k_bias_ratio),
            "native_fluidx3d_baseline_id": args.native_baseline_id,
            "native_baseline_gate": args.native_baseline_gate,
            "probe_mapping_table": str(probe_path),
            "probe_id_field": args.probe_id_column,
            "probe_tolerance_m": tolerance,
            "compared_component": compared_component,
            "component_sensitivity_audit": str(Path(args.component_sensitivity_audit).resolve()) if args.component_sensitivity_audit else "",
            "component_normalization_gate": audit_gate(component_sensitivity_audit, "component_normalization_gate"),
            "component_sensitivity_gate": audit_gate(component_sensitivity_audit, "component_sensitivity_gate"),
            "normalization_scale_gate": audit_gate(component_sensitivity_audit, "normalization_scale_gate"),
            "best_component_by_rmse": audit_field(component_sensitivity_audit, "best_component_by_rmse"),
            "selected_component_rmse_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_rmse")),
            "best_component_rmse_ratio": fmt(audit_float(component_sensitivity_audit, "best_component_rmse")),
            "component_rmse_improvement_ratio": fmt(audit_float(component_sensitivity_audit, "component_rmse_improvement_ratio")),
            "normalization_best_fit_scale": fmt(audit_float(component_sensitivity_audit, "selected_best_fit_scale_to_exp")),
            "normalization_scaled_improvement_ratio": fmt(audit_float(component_sensitivity_audit, "selected_scaled_improvement_ratio")),
            "failed_probe_count_by_tolerance": failed,
            "valid_n": valid_n,
            "failed_n": failed,
            "mean_probe_distance_m": fmt(mean(distances)),
            "max_probe_distance_m": fmt(max(distances) if distances else None),
            "max_official_coordinate_delta_m": fmt(max_coordinate_delta),
            "official_coordinate_delta_count": coordinate_delta_count,
            "U_MAE_ratio": fmt(u_mae),
            "U_RMSE_ratio": fmt(u_rmse),
            "U_bias_ratio": fmt(u_bias),
            "U_R2": fmt(u_r2),
            "U_regression_slope": fmt(slope),
            "U_regression_intercept": fmt(intercept),
            "U_max_abs_error": fmt(max_abs),
            "U_mean_sim": fmt(mean_sim),
            "U_mean_exp": fmt(mean_exp),
            "U_mean_ratio_sim_to_exp": fmt(mean_ratio),
            "U_best_fit_scale_to_exp": fmt(best_scale),
            "U_scaled_MAE_ratio": fmt(scaled_mae),
            "U_scaled_RMSE_ratio": fmt(scaled_rmse),
            "U_scaled_improvement_ratio": fmt(scaled_improvement),
            "bias_diagnosis": bias_diagnosis,
            "k_MAE_m2s2": args.k_mae or fmt(inlet_k_mae),
            "k_RMSE_m2s2": args.k_rmse or fmt(inlet_k_rmse),
            "k_RMSE_ratio": fmt(inlet_k_rmse_ratio),
            "k_bias_m2s2": args.k_bias or fmt(inlet_k_bias),
            "k_bias_ratio": args.k_bias_ratio or fmt(inlet_k_bias_ratio),
            "systematic_bias_flag": systematic_flag,
            "protocol_gate": metrics_protocol_gate,
            "notes": (
                f"official_id_column={official_id_col}; official_value_column={official_value_col}; "
                f"matched={valid_n}; official_filtered={len(official_rows)}; "
                f"probe_uref_values={';'.join(fmt(value) for value in unique_probe_urefs) or 'none'}; "
                f"metrics_protocol_failures={';'.join(protocol_failures) or 'none'}"
            ),
        }
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not args.append or not out_path.exists()
    with out_path.open("a" if args.append else "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(metrics)

    if comparison_path:
        comparison_path.parent.mkdir(parents=True, exist_ok=True)
        with comparison_path.open("w", encoding="utf-8", newline="") as handle:
            fields = [
                "probe_id",
                "sim_value",
                "official_value",
                "error",
                "abs_error",
                "nearest_distance",
                "official_coordinate_delta",
                "compared_component",
                "normalization_valid",
                "wind_direction_valid",
            ]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in comparison_rows:
                writer.writerow(row)

    print(f"Wrote metrics: {out_path}")
    print(f"valid_n={valid_n}; failed_n={failed}; U_bias_ratio={fmt(u_bias)}; U_R2={fmt(u_r2)}; systematic_bias_flag={systematic_flag or 'false'}; bias_diagnosis={bias_diagnosis or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
