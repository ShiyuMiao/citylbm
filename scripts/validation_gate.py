#!/usr/bin/env python3
"""Audit CityLBM/FluidX3D validation run artifacts before paper claims.

This script does not run CFD. It checks whether an existing run package has the
minimum evidence needed before AIJ Case A/E metrics can be treated as validation
evidence rather than a smoke or diagnostic run.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


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
    parser.add_argument("--case", default="", help="Expected case label, e.g. CaseA or CaseE.")
    parser.add_argument("--software", default="", help="Expected software label, e.g. native-fluidx3d or citylbm.")
    parser.add_argument("--min-avg-frames", type=int, default=10)
    parser.add_argument("--max-mean-speed-stddev-ratio", type=float, default=0.05)
    parser.add_argument("--max-point-speed-stddev-ratio", type=float, default=0.20)
    parser.add_argument("--max-u-bias-ratio", type=float, default=0.15)
    parser.add_argument("--max-u-rmse-ratio", type=float, default=0.30)
    parser.add_argument("--min-u-r2", type=float, default=0.70)
    parser.add_argument("--min-slope", type=float, default=0.70)
    parser.add_argument("--max-slope", type=float, default=1.30)
    parser.add_argument("--max-intercept-abs", type=float, default=0.20)
    parser.add_argument("--max-k-bias-ratio", type=float, default=0.30)
    parser.add_argument("--max-empty-tunnel-u-bias-ratio", type=float, default=0.05)
    parser.add_argument("--max-empty-tunnel-k-bias-ratio", type=float, default=0.15)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--max-probe-failure-fraction", type=float, default=0.0)
    parser.add_argument("--max-frontal-blockage-ratio", type=float, default=0.05)
    parser.add_argument("--expected-compared-component", default="", help="Require a specific Data Probe compared_component, e.g. speed_ratio or streamwise_ratio.")
    parser.add_argument("--expected-uref", type=float, default=None, help="Require the metrics/Data Probe Uref to match this value.")
    parser.add_argument("--uref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--expected-wind-vector", default="", help="Require wind_vector to match x,y,z or (x,y,z), e.g. 0,-1,0.")
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument(
        "--allow-velocity-only-inlet",
        action="store_true",
        help=(
            "Allow CityLBM STG-lite velocity-field-only inlet to pass the inlet gate "
            "when empty-tunnel U/k preservation passes. Without this explicit "
            "diagnostic override, paper-grade validation requires a distribution-"
            "consistent, precursor, digital-filter or recycling inlet."
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
    parent = base.parent
    if parent != base:
        for name in names:
            candidate = parent / name
            if candidate.exists():
                return candidate
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


def read_probe_component_audit(path: Optional[Path]) -> Tuple[Optional[int], List[str], Optional[str]]:
    if not path or not path.exists():
        return None, [], "probe audit CSV not found"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0, [], "probe audit CSV has no rows"
    components = set()
    valid_count = 0
    for row in rows:
        failed_flag = as_bool(get_any(row, ["failed", "Failed", "out_of_tolerance", "OutOfTolerance"]))
        status = str(get_any(row, ["status", "Status", "validation_status", "ValidationStatus"]) or "").lower()
        if failed_flag is True or "fail" in status or "out" in status:
            continue
        valid_count += 1
        component = str(get_any(row, ["compared_component", "ComparedComponent"]) or "").strip().lower()
        if component:
            components.add(component)
    return valid_count, sorted(components), None


def source_frame_count(metrics: Dict[str, Any]) -> Optional[int]:
    direct = as_int(get_any(metrics, ["averaging_window", "AverageLastN", "average_last_n"]))
    if direct:
        return direct
    source_steps = get_any(metrics, ["source_time_steps", "SourceTimeSteps", "source_steps"])
    if source_steps:
        text = str(source_steps).strip()
        if not text:
            return None
        separators = [",", ";", " "]
        parts = [text]
        for sep in separators:
            if sep in text:
                parts = [p for p in text.replace(";", ",").replace(" ", ",").split(",") if p.strip()]
                break
        return len(parts)
    return None


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


def manifest_source_hash_ok(manifest: Dict[str, Any], role: str) -> bool:
    record = get_manifest_source_record(manifest, role)
    return (
        as_bool(record.get("Exists")) is True
        and str(record.get("HashAlgorithm") or "").strip().upper() == "SHA256"
        and bool(str(record.get("Sha256") or "").strip())
    )


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    metadata_path = find_first(run_dir, ["case_metadata.json"])
    audit_path = find_first(run_dir, ["validation_protocol_audit.json"])
    manifest_path = find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metrics_path = Path(args.metrics).resolve() if args.metrics else find_metrics(run_dir)
    probe_path = Path(args.probe_audit).resolve() if args.probe_audit else None

    metadata = read_json(metadata_path)
    audit = read_json(audit_path)
    manifest = read_json(manifest_path)
    metrics, metrics_path = read_metrics(metrics_path)
    items = load_protocol_items(audit)
    gates: List[Dict[str, Any]] = []

    add_gate(
        gates,
        "artifact_presence",
        PASS if metadata_path and audit_path and metrics_path and metrics else FAIL,
        f"metadata={metadata_path or 'missing'}; audit={audit_path or 'missing'}; metrics={metrics_path or 'missing'}",
        "Archive case_metadata.json, validation_protocol_audit.json and metrics CSV/JSON for every run.",
    )

    frame_count = source_frame_count(metrics)
    if frame_count is None:
        expected = as_int(metadata.get("ExpectedVtkFrameCount"))
        frame_count = expected
        frame_source = "case_metadata expected frame count"
    else:
        frame_source = "metrics source_time_steps/averaging_window"
    available_frame_count = as_int(get_any(metrics, ["available_frame_count", "AvailableFrameCount"]))
    source_first_step = as_int(get_any(metrics, ["source_first_time_step", "SourceFirstTimeStep"]))
    source_last_step = as_int(get_any(metrics, ["source_last_time_step", "SourceLastTimeStep"]))
    latest_available_step = as_int(get_any(metrics, ["latest_available_time_step", "LatestAvailableTimeStep"]))
    selected_last_window = as_bool(get_any(metrics, ["selected_last_window", "SelectedLastWindow"]))
    source_steps_increasing = as_bool(get_any(metrics, ["source_steps_strictly_increasing", "SourceStepsStrictlyIncreasing"]))
    source_spacing_uniform = as_bool(get_any(metrics, ["source_step_spacing_uniform", "SourceStepSpacingUniform"]))
    metrics_time_gate = str(get_any(metrics, ["time_averaging_gate", "TimeAveragingGate"]) or "").strip().lower()
    metrics_time_gate_reasons = str(get_any(metrics, ["time_averaging_gate_reasons", "TimeAveragingGateReasons"]) or "").strip()
    mean_speed_stddev_ratio = as_float(get_any(metrics, ["mean_speed_stddev_ratio", "MeanSpeedStdDevRatio"]))
    max_speed_stddev_ratio = as_float(get_any(metrics, ["max_speed_stddev_ratio", "MaxSpeedStdDevRatio"]))
    mean_speed_stable = (
        mean_speed_stddev_ratio is not None
        and mean_speed_stddev_ratio <= args.max_mean_speed_stddev_ratio
    )
    point_speed_stable = (
        max_speed_stddev_ratio is not None
        and max_speed_stddev_ratio <= args.max_point_speed_stddev_ratio
    )
    time_window_ok = (
        frame_count is not None
        and frame_count >= args.min_avg_frames
        and selected_last_window is True
        and source_steps_increasing is True
        and source_spacing_uniform is True
        and source_last_step is not None
        and latest_available_step is not None
        and source_last_step == latest_available_step
        and metrics_time_gate in {"", "pass"}
        and mean_speed_stable
        and point_speed_stable
    )
    add_gate(
        gates,
        "time_averaging",
        PASS if time_window_ok else FAIL,
        (
            f"{frame_source}: {frame_count}; required >= {args.min_avg_frames}; "
            f"available_frame_count={available_frame_count}; source_first_step={source_first_step}; "
            f"source_last_step={source_last_step}; latest_available_step={latest_available_step}; "
            f"selected_last_window={selected_last_window}; source_steps_strictly_increasing={source_steps_increasing}; "
            f"source_step_spacing_uniform={source_spacing_uniform}; "
            f"metrics_time_averaging_gate={metrics_time_gate or 'missing'}; "
            f"metrics_time_averaging_gate_reasons={metrics_time_gate_reasons or 'none'}; "
            f"mean_speed_stddev_ratio={mean_speed_stddev_ratio}; required <= {args.max_mean_speed_stddev_ratio}; "
            f"max_speed_stddev_ratio={max_speed_stddev_ratio}; required <= {args.max_point_speed_stddev_ratio}"
        ),
        "Rerun or postprocess with a longer statistically stable final-window average whose source steps are the last available, increasing and uniformly spaced.",
    )

    boundary_gate = str(
        get_any(metrics, ["boundary_protocol_gate", "BoundaryProtocolGate"])
        or get_any(metadata.get("BoundaryProtocolAudit", {}), ["Gate"])
        or ""
    )
    boundary_audit = metadata.get("BoundaryProtocolAudit", {}) if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    blockage_audit = boundary_audit.get("BlockageDiagnostics", {}) if isinstance(boundary_audit.get("BlockageDiagnostics"), dict) else {}
    frontal_blockage = as_float(
        get_any(metrics, ["approx_frontal_blockage_ratio", "ApproxFrontalBlockageRatio"])
        or get_any(blockage_audit, ["ApproxFrontalBlockageRatio"])
    )
    blockage_gate = str(
        get_any(metrics, ["blockage_protocol_gate", "BlockageProtocolGate"])
        or get_any(blockage_audit, ["Gate"])
        or ""
    )
    add_gate(
        gates,
        "boundary_protocol",
        PASS
        if boundary_gate == "diagnostic_clearance_ok_verify_against_aij"
        and frontal_blockage is not None
        and frontal_blockage <= args.max_frontal_blockage_ratio
        else FAIL,
        (
            f"boundary_protocol_gate={boundary_gate or 'missing'}; "
            f"approx_frontal_blockage_ratio={frontal_blockage}; "
            f"blockage_protocol_gate={blockage_gate or 'missing'}; "
            f"required frontal <= {args.max_frontal_blockage_ratio}"
        ),
        "Fix domain extents/model placement, reduce blockage, or archive a justified AIJ-equivalent boundary protocol.",
    )

    inlet_status = protocol_status(items, "inlet_turbulence_k")
    distribution_status = protocol_status(items, "inlet_distribution_consistency")
    inlet_treatment = str(
        get_any(metrics, ["inlet_distribution_treatment"])
        or metadata.get("SyntheticTurbulentInletDistributionTreatment")
        or ""
    )
    empty_u_bias = as_float(get_any(metrics, ["empty_tunnel_U_bias_ratio", "empty_tunnel_u_bias_ratio"]))
    empty_k_bias = as_float(get_any(metrics, ["empty_tunnel_k_bias_ratio", "empty_tunnel_K_bias_ratio"]))
    empty_gate = str(get_any(metrics, ["empty_tunnel_gate", "inlet_k_preservation_gate"]) or "").strip().lower()
    empty_tunnel_pass = (
        empty_gate == "pass"
        or (
            empty_u_bias is not None
            and abs(empty_u_bias) <= args.max_empty_tunnel_u_bias_ratio
            and empty_k_bias is not None
            and abs(empty_k_bias) <= args.max_empty_tunnel_k_bias_ratio
        )
    )
    treatment_distribution_consistent = any(
        token in inlet_treatment.lower()
        for token in ["distribution_consistent", "precursor", "digital-filter", "digital_filter", "recycling"]
    )
    treatment_velocity_only = "velocity_field_only" in inlet_treatment.lower()
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
        "inlet_turbulence",
        inlet_gate_status,
        (
            f"inlet_turbulence_k={inlet_status}; inlet_distribution_consistency={distribution_status}; "
            f"treatment={inlet_treatment or 'missing'}; empty_tunnel_gate={empty_gate or 'missing'}; "
            f"empty_tunnel_U_bias_ratio={empty_u_bias}; empty_tunnel_k_bias_ratio={empty_k_bias}; "
            f"allow_velocity_only_inlet={args.allow_velocity_only_inlet}"
        ),
        "Use a distribution-consistent DFM/SEM/precursor/recycling inlet and pass empty-tunnel U/k preservation; velocity-only STG-lite is diagnostic unless explicitly allowed.",
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
    native_gate = str(get_any(metrics, ["native_baseline_gate", "native_fluidx3d_baseline_gate"]) or "").strip().lower()
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
    native_source_hashes_ok = all(
        manifest_source_hash_ok(manifest, role) for role in native_source_hash_roles
    )
    native_manifest_ok = (
        native_path_explicit is True
        and native_source_valid is True
        and native_source_hashes_ok
    )
    add_gate(
        gates,
        "native_baseline",
        PASS if native_id_matches_manifest and native_gate == "pass" and native_manifest_ok else FAIL,
        (
            f"native_fluidx3d_baseline_id={metrics_native_id or 'missing'}; "
            f"manifest_baseline_id={manifest_native_id or 'missing'}; "
            f"native_id_matches_manifest={native_id_matches_manifest}; "
            f"protocol_status={native_status or 'missing'}; native_baseline_gate={native_gate or 'missing'}; "
            f"NativeFluidX3DPathExplicitlyProvided={native_path_explicit}; "
            f"NativeFluidX3DSourceValidation.IsValid={native_source_valid}; "
            f"native_source_hashes_ok={native_source_hashes_ok}; "
            f"manifest={manifest_path or 'missing'}"
        ),
        "Run and archive a paired native FluidX3D baseline using an explicit complete source tree with setup/defines/lbm source hashes, then compare the same setup, grid, averaging and probes.",
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
    coord_delta = as_float(get_any(metrics, ["max_official_coordinate_delta_m", "MaxOfficialCoordinateDeltaM"]))
    coord_delta_count = as_int(get_any(metrics, ["official_coordinate_delta_count", "OfficialCoordinateDeltaCount"]))
    valid_metric_count = as_int(get_any(metrics, ["valid_n", "ValidN"]))
    coord_ok = coord_delta is not None and coord_delta <= args.max_official_coordinate_delta_m
    coord_coverage_ok = (
        coord_delta_count is not None
        and valid_metric_count is not None
        and valid_metric_count > 0
        and coord_delta_count == valid_metric_count
    )
    add_gate(
        gates,
        "coordinate_normalization",
        PASS
        if normalization_valid is True
        and wind_valid is True
        and uref_ok
        and wind_vector_ok
        and coord_ok
        and coord_coverage_ok
        else FAIL,
        (
            f"normalization_valid={normalization_valid}; wind_direction_valid={wind_valid}; "
            f"Uref_mps={uref}; expected_uref={args.expected_uref}; uref_tolerance={args.uref_tolerance}; "
            f"wind_vector={metric_wind_vector}; expected_wind_vector={expected_wind_vector}; "
            f"wind_vector_unit_delta={wind_delta}; wind_vector_tolerance={args.wind_vector_tolerance}; "
            f"max_official_coordinate_delta_m={coord_delta}; required <= {args.max_official_coordinate_delta_m}; "
            f"official_coordinate_delta_count={coord_delta_count}; valid_n={valid_metric_count}"
        ),
        "Audit Uref/Zref, wind sign, compared component and RS probe coordinate transform.",
    )

    component_gate = str(get_any(metrics, ["compared_component_consistency_gate", "ComparedComponentConsistencyGate"]) or "").strip().lower()
    metric_component = str(get_any(metrics, ["compared_component", "velocity_component", "ComparedComponent"]) or "").strip().lower()
    probe_valid_component_count, probe_components, probe_component_error = read_probe_component_audit(probe_path)
    expected_component = args.expected_compared_component.strip().lower()
    if probe_components:
        unique_components = probe_components
    else:
        unique_components = [c for c in metric_component.split(";") if c] if ";" in metric_component else ([metric_component] if metric_component else [])
    component_consistent = (
        (component_gate == "pass" or component_gate == "")
        and len(unique_components) == 1
        and bool(unique_components[0])
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
            f"probe_valid_component_count={probe_valid_component_count}; {probe_component_error or ''}"
        ).strip(),
        "Use one explicit Data Probe Compared Component for all official probes and match it to the AIJ table definition.",
    )

    valid_n = as_int(get_any(metrics, ["valid_n", "ValidN"]))
    failed_n = as_int(get_any(metrics, ["failed_n", "FailedN"]))
    probe_total, probe_failed, probe_error = read_probe_counts(probe_path)
    if probe_total is not None:
        valid_n = probe_total - (probe_failed or 0)
        failed_n = probe_failed
    failure_fraction = None
    if valid_n is not None and failed_n is not None and valid_n + failed_n > 0:
        failure_fraction = failed_n / float(valid_n + failed_n)
    add_gate(
        gates,
        "probe_mapping",
        PASS if failure_fraction is not None and failure_fraction <= args.max_probe_failure_fraction else FAIL,
        f"valid_n={valid_n}; failed_n={failed_n}; failure_fraction={failure_fraction}; {probe_error or ''}".strip(),
        "Export Data Probe audit CSV and fix tolerance/projection until official probes map reliably.",
    )

    u_bias = as_float(get_any(metrics, ["U_bias_ratio", "U_bias_Uref", "U_bias"]))
    u_rmse = as_float(get_any(metrics, ["U_RMSE_ratio", "U_RMSE_Uref", "U_RMSE"]))
    u_r2 = as_float(get_any(metrics, ["U_R2", "R2"]))
    slope = as_float(get_any(metrics, ["U_regression_slope", "slope"]))
    intercept = as_float(get_any(metrics, ["U_regression_intercept", "intercept"]))
    accuracy_pass = (
        u_bias is not None
        and abs(u_bias) <= args.max_u_bias_ratio
        and u_rmse is not None
        and u_rmse <= args.max_u_rmse_ratio
        and u_r2 is not None
        and u_r2 >= args.min_u_r2
        and slope is not None
        and args.min_slope <= slope <= args.max_slope
        and intercept is not None
        and abs(intercept) <= args.max_intercept_abs
    )
    add_gate(
        gates,
        "mean_velocity_accuracy",
        PASS if accuracy_pass else FAIL,
        (
            f"U_bias_ratio={u_bias}; U_RMSE_ratio={u_rmse}; U_R2={u_r2}; "
            f"slope={slope}; intercept={intercept}"
        ),
        "Do not promote to paper-grade validation until bias, RMSE, R2, slope and intercept all meet thresholds.",
    )

    k_bias_ratio = as_float(get_any(metrics, ["k_bias_ratio", "K_bias_ratio"]))
    if k_bias_ratio is None:
        k_status = FAIL
        k_evidence = "k_bias_ratio=missing"
    else:
        k_status = PASS if abs(k_bias_ratio) <= args.max_k_bias_ratio else FAIL
        k_evidence = f"k_bias_ratio={k_bias_ratio}; required abs <= {args.max_k_bias_ratio}"
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
    add_gate(
        gates,
        "systematic_bias",
        FAIL if systematic_flag in {"true", "1", "yes", "fail", "risk", "underprediction"} else PASS,
        (
            f"systematic_bias_flag={systematic_flag or 'missing/false'}; "
            f"best_scale={best_scale}; scaled_RMSE={scaled_rmse}; "
            f"scaled_improvement={scaled_improvement}; diagnosis={bias_diagnosis or 'missing'}"
        ),
        "Investigate protocol/physics setup before tuning if a systematic low-bias flag is present.",
    )

    failing = [gate for gate in gates if gate["status"] == FAIL]
    warnings = [gate for gate in gates if gate["status"] == WARN]
    verdict = FAIL if failing else (WARN if warnings else PASS)
    return {
        "schema": "citylbm.validation_gate.v1",
        "run_dir": str(run_dir),
        "case": args.case,
        "software": args.software,
        "verdict": verdict,
        "paper_grade": verdict == PASS,
        "gates": gates,
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
            "max_empty_tunnel_u_bias_ratio": args.max_empty_tunnel_u_bias_ratio,
            "max_empty_tunnel_k_bias_ratio": args.max_empty_tunnel_k_bias_ratio,
            "max_official_coordinate_delta_m": args.max_official_coordinate_delta_m,
            "max_probe_failure_fraction": args.max_probe_failure_fraction,
            "max_frontal_blockage_ratio": args.max_frontal_blockage_ratio,
            "expected_compared_component": args.expected_compared_component,
            "expected_uref": args.expected_uref,
            "uref_tolerance": args.uref_tolerance,
            "expected_wind_vector": args.expected_wind_vector,
            "wind_vector_tolerance": args.wind_vector_tolerance,
            "allow_velocity_only_inlet": args.allow_velocity_only_inlet,
        },
        "artifacts": {
            "case_metadata": str(metadata_path) if metadata_path else "",
            "validation_protocol_audit": str(audit_path) if audit_path else "",
            "native_fluidx3d_baseline_manifest": str(manifest_path) if manifest_path else "",
            "metrics": str(metrics_path) if metrics_path else "",
            "probe_audit": str(probe_path) if probe_path else "",
        },
    }


def print_report(report: Dict[str, Any]) -> None:
    print(f"Validation gate verdict: {report['verdict']}")
    print(f"Paper-grade evidence: {report['paper_grade']}")
    for gate in report["gates"]:
        print(f"- [{gate['status']}] {gate['key']}: {gate['evidence']}")
        if gate["status"] != PASS and gate["required_next_action"]:
            print(f"  next: {gate['required_next_action']}")


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
