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
    parser.add_argument("--max-k-rmse-ratio", type=float, default=0.50)
    parser.add_argument("--max-empty-tunnel-u-bias-ratio", type=float, default=0.05)
    parser.add_argument("--max-empty-tunnel-k-bias-ratio", type=float, default=0.15)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--max-probe-failure-fraction", type=float, default=0.0)
    parser.add_argument("--max-probe-distance-dx-ratio", type=float, default=1.0)
    parser.add_argument("--max-probe-tolerance-dx-ratio", type=float, default=1.0)
    parser.add_argument("--min-inlet-temporal-finite-fraction", type=float, default=0.80)
    parser.add_argument("--min-inlet-spatial-finite-fraction", type=float, default=0.80)
    parser.add_argument("--max-frontal-blockage-ratio", type=float, default=0.05)
    parser.add_argument("--max-estimated-mach", type=float, default=0.20)
    parser.add_argument("--min-lbm-tau", type=float, default=0.500001)
    parser.add_argument("--max-lbm-tau", type=float, default=2.0)
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
        "--allow-summary-only-probe-metrics",
        action="store_true",
        help=(
            "Diagnostic override only: allow coordinate, normalization and compared-component "
            "checks to rely on a summary metrics row when the per-probe Data Probe audit CSV "
            "is missing. Paper-grade validation should not use this flag."
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


def build_diagnostic_priority(gates: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    by_key = gate_by_key(gates)
    priorities: List[Dict[str, Any]] = []

    coordinate_gate = by_key.get("coordinate_normalization")
    compared_gate = by_key.get("compared_component")
    projection_gate = by_key.get("probe_projection_distance")
    probe_gate = by_key.get("probe_mapping")
    sensitivity_gate = by_key.get("component_normalization_sensitivity")
    if any(gate is None or gate.get("status") != PASS for gate in [coordinate_gate, compared_gate, projection_gate, probe_gate, sensitivity_gate]):
        coordinate_priority_gate = next(
            (
                gate for gate in [coordinate_gate, compared_gate, projection_gate, probe_gate, sensitivity_gate]
                if gate is None or gate.get("status") != PASS
            ),
            coordinate_gate,
        )
        add_priority(
            priorities,
            1,
            "coordinate_component_normalization",
            coordinate_priority_gate,
            "Probe coordinates, wind sign, compared component and Uref must be closed before interpreting bias.",
            "Fix RS probe projection, wind vector, compared_component and Uref/SI velocity conversion first; rerun component/Uref sensitivity before interpreting bias.",
        )

    time_gate = by_key.get("time_averaging")
    if time_gate is None or time_gate.get("status") != PASS:
        add_priority(
            priorities,
            2,
            "time_averaging_stationarity",
            time_gate,
            "A short or unstable final VTK window can create apparent systematic velocity bias.",
            "Rerun or postprocess with at least the required final-window frames and stable mean/max speed stddev ratios.",
        )

    inlet_profile_gate = by_key.get("inlet_profile_preservation")
    k_gate = by_key.get("k_preservation_or_accuracy")
    if any(gate is None or gate.get("status") != PASS for gate in [inlet_profile_gate, k_gate]):
        add_priority(
            priorities,
            3,
            "inlet_profile_u_k_preservation",
            inlet_profile_gate,
            "The AF U(z)/k(z) table must be preserved in real VTK frames before probe accuracy is meaningful.",
            "Run an empty-tunnel or inlet-plane VTK audit and fix profile conversion, k scaling or inlet application.",
        )

    inlet_gate = by_key.get("inlet_turbulence")
    paper_inlet_gate = by_key.get("paper_grade_inlet_method")
    length_gate = by_key.get("inlet_length_scale")
    correlation_gate = by_key.get("inlet_correlation")
    if any(gate is None or gate.get("status") != PASS for gate in [inlet_gate, paper_inlet_gate, length_gate, correlation_gate]):
        inlet_priority_gate = next(
            (
                gate for gate in [inlet_gate, paper_inlet_gate, length_gate, correlation_gate]
                if gate is None or gate.get("status") != PASS
            ),
            inlet_gate,
        )
        add_priority(
            priorities,
            4,
            "turbulent_inlet_method",
            inlet_priority_gate,
            "Velocity-field-only, length-scale-free or correlation-unverified STG-lite cannot establish paper-grade AIJ turbulent inflow.",
            "Use a distribution-consistent DFM/SEM/precursor/recycling inlet or archive validated turbulence length-scale and inlet correlation evidence.",
        )

    boundary_gate = by_key.get("boundary_protocol")
    roughness_gate = by_key.get("roughness_or_precursor")
    if any(gate is None or gate.get("status") != PASS for gate in [boundary_gate, roughness_gate]):
        boundary_priority_gate = next(
            (gate for gate in [boundary_gate, roughness_gate] if gate is None or gate.get("status") != PASS),
            boundary_gate,
        )
        add_priority(
            priorities,
            5,
            "boundary_roughness_blockage",
            boundary_priority_gate,
            "Simplified TYPE_E boundaries, missing rough-wall treatment or excessive blockage can drive systematic underprediction.",
            "Audit AIJ-equivalent inlet/outlet/lateral/top/floor conditions, roughness treatment, fetch and blockage.",
        )

    native_gate = by_key.get("native_baseline")
    if native_gate is None or native_gate.get("status") != PASS:
        add_priority(
            priorities,
            6,
            "native_fluidx3d_baseline",
            native_gate,
            "CityLBM accuracy cannot be separated from native FluidX3D/protocol error without a paired native baseline.",
            "Run native FluidX3D with the same setup, grid, averaging and probes, then compare before changing CityLBM.",
        )

    systematic_gate = by_key.get("systematic_bias")
    mean_gate = by_key.get("mean_velocity_accuracy")
    systematic_flag = str(get_any(metrics, ["systematic_bias_flag"]) or "").strip().lower()
    bias_diagnosis = str(get_any(metrics, ["bias_diagnosis"]) or "").strip()
    if systematic_gate is not None and systematic_gate.get("status") != PASS:
        add_priority(
            priorities,
            7,
            "systematic_bias_root_cause",
            systematic_gate,
            f"Metrics report systematic bias: {systematic_flag or 'flagged'}; {bias_diagnosis or 'no diagnosis string'}.",
            "After ranks 1-6 pass, treat remaining bias as a physics/protocol issue and test inlet, boundary, roughness and grid sensitivity.",
        )
    elif mean_gate is not None and mean_gate.get("status") != PASS:
        add_priority(
            priorities,
            7,
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


def source_frame_details(metrics: Dict[str, Any]) -> Tuple[Optional[int], str, bool]:
    source_steps = get_any(metrics, ["source_time_steps", "SourceTimeSteps", "source_steps"])
    if source_steps:
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
    inlet_correlation_audit_path = find_first(run_dir, ["inlet_correlation_audit.json"])
    boundary_audit_path = find_first(run_dir, ["boundary_protocol_audit.json"])
    component_sensitivity_audit_path = find_first(run_dir, ["component_sensitivity_audit.json"])
    manifest_path = find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metrics_path = Path(args.metrics).resolve() if args.metrics else find_metrics(run_dir)
    probe_path = Path(args.probe_audit).resolve() if args.probe_audit else None

    metadata = read_json(metadata_path)
    audit = read_json(audit_path)
    inlet_correlation_audit = read_json(inlet_correlation_audit_path)
    external_boundary_audit = read_json(boundary_audit_path)
    component_sensitivity_audit = read_json(component_sensitivity_audit_path)
    manifest = read_json(manifest_path)
    metrics, metrics_path = read_metrics(metrics_path)
    items = load_protocol_items(audit)
    gates: List[Dict[str, Any]] = []

    add_gate(
        gates,
        "artifact_presence",
        PASS if metadata_path and audit_path and metrics_path and metrics else FAIL,
        (
            f"metadata={metadata_path or 'missing'}; audit={audit_path or 'missing'}; "
            f"boundary_audit={boundary_audit_path or 'missing'}; metrics={metrics_path or 'missing'}"
        ),
        "Archive case_metadata.json, validation_protocol_audit.json, boundary_protocol_audit.json and metrics CSV/JSON for every run.",
    )

    frame_count, source_step_text, has_real_source_steps = source_frame_details(metrics)
    requested_avg_window = as_int(get_any(metrics, ["averaging_window", "AverageLastN", "average_last_n"]))
    expected_vtk_frame_count = as_int(metadata.get("ExpectedVtkFrameCount"))
    if has_real_source_steps:
        frame_source = "metrics real source_time_steps"
    else:
        frame_source = "missing real source_time_steps"
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
        has_real_source_steps
        and frame_count is not None
        and frame_count >= args.min_avg_frames
        and selected_last_window is True
        and source_steps_increasing is True
        and source_spacing_uniform is True
        and source_last_step is not None
        and latest_available_step is not None
        and source_last_step == latest_available_step
        and metrics_time_gate == "pass"
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
            f"requested_averaging_window={requested_avg_window}; "
            f"expected_vtk_frame_count={expected_vtk_frame_count}; "
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
        get_any(metrics, ["solver_stability_warnings", "SolverStabilityWarnings"])
        or metadata.get("SolverStabilityWarnings")
        or get_any(manifest.get("SharedRunConditions", {}), ["SolverStabilityWarnings"])
        or ""
    ).strip().lower()
    lbm_stability_gate = str(
        get_any(metrics, ["lbm_stability_gate", "LbmStabilityGate"])
        or metadata.get("LbmStabilityGate")
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
            f"protocol_status={stability_protocol_status or 'missing'}"
        ),
        "Archive solver log/runtime statistics proving no FluidX3D stability warnings, bounded Mach, valid tau/nu, Reynolds number, velocity set and LES/subgrid model before interpreting validation metrics.",
    )

    boundary_gate = str(
        get_any(external_boundary_audit, ["metadata_boundary_protocol_gate"])
        or get_any(metrics, ["boundary_protocol_gate", "BoundaryProtocolGate"])
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
    boundary_evidence_source = str(
        get_any(external_boundary_audit, ["boundary_evidence_source"])
        or get_any(metrics, ["boundary_evidence_source", "BoundaryProtocolEvidenceSource"])
        or get_any(boundary_audit, ["ProtocolEvidenceSource"])
        or metadata.get("BoundaryProtocolEvidenceSource")
        or ""
    )
    boundary_evidence_gate = str(
        get_any(external_boundary_audit, ["boundary_evidence_gate"])
        or get_any(metrics, ["boundary_evidence_gate", "BoundaryProtocolEvidenceGate"])
        or get_any(boundary_audit, ["ProtocolEvidenceGate"])
        or metadata.get("BoundaryProtocolEvidenceGate")
        or ""
    ).strip().lower()
    boundary_equivalence_basis = str(
        get_any(external_boundary_audit, ["boundary_equivalence_basis"])
        or get_any(metrics, ["boundary_equivalence_basis", "BoundaryEquivalenceBasis"])
        or get_any(boundary_audit, ["BoundaryEquivalenceBasis"])
        or metadata.get("BoundaryEquivalenceBasis")
        or ""
    )
    external_boundary_equivalence_supported = as_bool(
        get_any(external_boundary_audit, ["boundary_equivalence_supported"])
        or get_any(metrics, ["boundary_equivalence_supported", "BoundaryEquivalenceSupported"])
    )
    clearance_numeric_gate = str(
        get_any(external_boundary_audit, ["clearance_numeric_gate"])
        or get_any(metrics, ["clearance_numeric_gate", "BoundaryClearanceNumericGate"])
        or ""
    ).strip().lower()
    clearance_numeric_reasons = str(
        get_any(external_boundary_audit, ["clearance_numeric_gate_reasons"])
        or get_any(metrics, ["boundary_clearance_reasons", "BoundaryClearanceReasons"])
        or ""
    )
    external_boundary_protocol_gate = str(
        get_any(external_boundary_audit, ["boundary_protocol_gate"]) or ""
    ).strip().lower()
    external_boundary_missing_fields = external_boundary_audit.get("missing_evidence_fields")
    if isinstance(external_boundary_missing_fields, list):
        external_boundary_missing_fields_text = ",".join(str(field) for field in external_boundary_missing_fields)
    else:
        external_boundary_missing_fields_text = str(external_boundary_missing_fields or "")
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
    boundary_evidence_ok = boundary_evidence_gate == "pass" and boundary_evidence_supported and boundary_clearance_ok
    add_gate(
        gates,
        "boundary_protocol",
        PASS
        if boundary_diagnostic_ok
        and boundary_evidence_ok
        and boundary_external_ok
        else FAIL,
        (
            f"boundary_protocol_gate={boundary_gate or 'missing'}; "
            f"external_boundary_protocol_gate={external_boundary_protocol_gate or 'missing'}; "
            f"approx_frontal_blockage_ratio={frontal_blockage}; "
            f"blockage_protocol_gate={blockage_gate or 'missing'}; "
            f"required frontal <= {args.max_frontal_blockage_ratio}; "
            f"boundary_evidence_gate={boundary_evidence_gate or 'missing'}; "
            f"boundary_evidence_source={boundary_evidence_source or 'missing'}; "
            f"boundary_equivalence_basis={boundary_equivalence_basis or 'missing'}; "
            f"boundary_evidence_supported={boundary_evidence_supported}; "
            f"boundary_equivalence_token_inferred={boundary_evidence_supported_by_token}; "
            f"clearance_numeric_gate={clearance_numeric_gate or 'missing'}; "
            f"clearance_numeric_gate_reasons={clearance_numeric_reasons or 'none'}; "
            f"missing_boundary_evidence_fields={external_boundary_missing_fields_text or 'none'}"
        ),
        "Fix domain extents/model placement, reduce blockage, and archive AIJ-equivalent boundary/fetch/roughness evidence or an empty-tunnel/native boundary-preservation check.",
    )

    roughness_layout = metadata.get("RoughnessLayout") if isinstance(metadata.get("RoughnessLayout"), dict) else {}
    equivalent_precursor = metadata.get("EquivalentPrecursor") if isinstance(metadata.get("EquivalentPrecursor"), dict) else {}
    wall_roughness_treatment = str(
        get_any(metrics, ["wall_roughness_treatment", "WallRoughnessTreatment"])
        or metadata.get("WallRoughnessTreatment")
        or ""
    ).strip()
    external_roughness_treatment = str(get_any(external_boundary_audit, ["roughness_treatment"]) or "").strip()
    floor_roughness_source = str(
        get_any(external_boundary_audit, ["floor_roughness_source"])
        or get_any(metrics, ["floor_roughness_source", "FloorRoughnessSource"])
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
        boundary_evidence_gate == "pass"
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
            f"boundary_evidence_gate={boundary_evidence_gate or 'missing'}"
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
    inlet_profile_gate = str(get_any(metrics, ["inlet_profile_gate"]) or "").strip().lower()
    inlet_u_profile_gate = str(get_any(metrics, ["inlet_u_profile_gate"]) or "").strip().lower()
    inlet_k_profile_gate = str(get_any(metrics, ["inlet_k_profile_gate"]) or "").strip().lower()
    inlet_streamwise_direction_gate = str(get_any(metrics, ["inlet_streamwise_direction_gate"]) or "").strip().lower()
    inlet_negative_streamwise_fraction = as_float(get_any(metrics, ["inlet_negative_streamwise_fraction"]))
    inlet_profile_available_frame_count = as_int(get_any(metrics, ["inlet_profile_available_frame_count"]))
    inlet_profile_frame_count = as_int(get_any(metrics, ["inlet_profile_frame_count"]))
    inlet_profile_source_steps = str(get_any(metrics, ["inlet_profile_source_time_steps"]) or "").strip()
    inlet_profile_source_frame_count, inlet_profile_source_step_text, inlet_profile_has_source_steps = source_frame_details(
        {"source_time_steps": inlet_profile_source_steps}
    )
    inlet_profile_source_first_step = as_int(get_any(metrics, ["inlet_profile_source_first_time_step"]))
    inlet_profile_source_last_step = as_int(get_any(metrics, ["inlet_profile_source_last_time_step"]))
    inlet_profile_latest_available_step = as_int(get_any(metrics, ["inlet_profile_latest_available_time_step"]))
    inlet_profile_selected_last_window = as_bool(get_any(metrics, ["inlet_profile_selected_last_window"]))
    inlet_profile_steps_increasing = as_bool(get_any(metrics, ["inlet_profile_source_steps_strictly_increasing"]))
    inlet_profile_spacing_uniform = as_bool(get_any(metrics, ["inlet_profile_source_step_spacing_uniform"]))
    inlet_profile_time_gate = str(get_any(metrics, ["inlet_profile_time_averaging_gate"]) or "").strip().lower()
    inlet_profile_time_gate_reasons = str(get_any(metrics, ["inlet_profile_time_averaging_gate_reasons"]) or "").strip()
    inlet_u_mae_ratio = as_float(get_any(metrics, ["inlet_u_mae_ratio"]))
    inlet_u_rmse_ratio = as_float(get_any(metrics, ["inlet_u_rmse_ratio"]))
    inlet_k_mae_ratio = as_float(get_any(metrics, ["inlet_k_mae_ratio"]))
    inlet_k_rmse_ratio = as_float(get_any(metrics, ["inlet_k_rmse_ratio"]))
    empty_u_bias = as_float(get_any(metrics, ["empty_tunnel_U_bias_ratio", "empty_tunnel_u_bias_ratio"]))
    empty_k_bias = as_float(get_any(metrics, ["empty_tunnel_k_bias_ratio", "empty_tunnel_K_bias_ratio"]))
    empty_gate = str(get_any(metrics, ["empty_tunnel_gate", "inlet_k_preservation_gate"]) or "").strip().lower()
    inlet_profile_window_ok = (
        inlet_profile_has_source_steps
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
            f"inlet_profile_source_time_steps={inlet_profile_source_step_text or 'missing'}; "
            f"inlet_profile_source_first_step={inlet_profile_source_first_step}; "
            f"inlet_profile_source_last_step={inlet_profile_source_last_step}; "
            f"inlet_profile_latest_available_step={inlet_profile_latest_available_step}; "
            f"inlet_profile_selected_last_window={inlet_profile_selected_last_window}; "
            f"inlet_profile_source_steps_strictly_increasing={inlet_profile_steps_increasing}; "
            f"inlet_profile_source_step_spacing_uniform={inlet_profile_spacing_uniform}; "
            f"inlet_profile_time_averaging_gate={inlet_profile_time_gate or 'missing'}; "
            f"inlet_profile_time_averaging_gate_reasons={inlet_profile_time_gate_reasons or 'none'}; "
            f"inlet_u_mae_ratio={inlet_u_mae_ratio}; inlet_u_rmse_ratio={inlet_u_rmse_ratio}; "
            f"inlet_k_mae_ratio={inlet_k_mae_ratio}; inlet_k_rmse_ratio={inlet_k_rmse_ratio}"
        ),
        "Run scripts/audit_inlet_profile_from_vtk.py on real post-spinup VTK frames and pass U(z)/k(z) preservation before paper-grade validation.",
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

    paper_grade_inlet_pass = (
        empty_tunnel_pass
        and (
            treatment_distribution_consistent
            or distribution_status == "pass"
        )
        and not treatment_velocity_only
    )
    add_gate(
        gates,
        "paper_grade_inlet_method",
        PASS if paper_grade_inlet_pass else FAIL,
        (
            f"method={synthetic_inlet_method or 'missing'}; "
            f"treatment={inlet_treatment or 'missing'}; "
            f"inlet_distribution_consistency={distribution_status or 'missing'}; "
            f"velocity_field_only={treatment_velocity_only}; "
            f"method_name_only={method_name_only}; "
            f"distribution_consistent={treatment_distribution_consistent}; "
            f"empty_tunnel_or_inlet_profile_pass={empty_tunnel_pass}; "
            f"allow_velocity_only_inlet={args.allow_velocity_only_inlet}"
        ),
        (
            "For paper-grade validation, use a distribution-consistent digital-filter, SEM/DFM, precursor or "
            "recycling inlet. The --allow-velocity-only-inlet override is diagnostic only and cannot satisfy "
            "this paper-grade inlet-method gate."
        ),
    )

    inlet_correlation_gate = str(
        get_any(metrics, ["inlet_correlation_gate", "InletCorrelationGate"])
        or get_any(inlet_correlation_audit, ["inlet_correlation_gate"])
        or ""
    ).strip().lower()
    inlet_temporal_lag1 = as_float(
        get_any(metrics, ["inlet_temporal_lag1_correlation", "InletTemporalLag1Correlation"])
        or get_any(inlet_correlation_audit, ["temporal_lag1_mean_correlation"])
    )
    inlet_temporal_lag1_abs = as_float(
        get_any(metrics, ["inlet_temporal_lag1_abs_correlation", "InletTemporalLag1AbsCorrelation"])
        or get_any(inlet_correlation_audit, ["temporal_lag1_abs_mean_correlation"])
    )
    inlet_spatial_adjacent = as_float(
        get_any(metrics, ["inlet_spatial_adjacent_correlation", "InletSpatialAdjacentCorrelation"])
        or get_any(inlet_correlation_audit, ["spatial_adjacent_mean_correlation"])
    )
    inlet_streamwise_variance = as_float(
        get_any(metrics, ["inlet_streamwise_fluctuation_variance", "InletStreamwiseFluctuationVariance"])
        or get_any(inlet_correlation_audit, ["mean_streamwise_fluctuation_variance"])
    )
    inlet_temporal_finite_fraction = as_float(
        get_first_available(
            get_any(metrics, ["inlet_temporal_finite_correlation_fraction", "InletTemporalFiniteCorrelationFraction"]),
            get_any(inlet_correlation_audit, ["temporal_finite_correlation_fraction"]),
        )
    )
    inlet_spatial_finite_fraction = as_float(
        get_first_available(
            get_any(metrics, ["inlet_spatial_finite_correlation_fraction", "InletSpatialFiniteCorrelationFraction"]),
            get_any(inlet_correlation_audit, ["spatial_finite_correlation_fraction"]),
        )
    )
    metric_inlet_correlation_audit = str(
        get_any(metrics, ["inlet_correlation_audit", "InletCorrelationAudit"]) or ""
    ).strip()
    metric_inlet_correlation_audit_exists = False
    if metric_inlet_correlation_audit:
        try:
            metric_inlet_correlation_audit_exists = Path(metric_inlet_correlation_audit).expanduser().exists()
        except OSError:
            metric_inlet_correlation_audit_exists = False
    inlet_correlation_audit_exists = bool(inlet_correlation_audit_path and inlet_correlation_audit_path.exists()) or metric_inlet_correlation_audit_exists
    inlet_correlation_coverage_ok = (
        inlet_temporal_finite_fraction is not None
        and inlet_temporal_finite_fraction >= args.min_inlet_temporal_finite_fraction
        and inlet_spatial_finite_fraction is not None
        and inlet_spatial_finite_fraction >= args.min_inlet_spatial_finite_fraction
    )
    add_gate(
        gates,
        "inlet_correlation",
        PASS if inlet_correlation_gate == "pass" and inlet_correlation_audit_exists and inlet_correlation_coverage_ok else FAIL,
        (
            f"inlet_correlation_gate={inlet_correlation_gate or 'missing'}; "
            f"temporal_lag1_mean_correlation={inlet_temporal_lag1}; "
            f"temporal_lag1_abs_mean_correlation={inlet_temporal_lag1_abs}; "
            f"spatial_adjacent_mean_correlation={inlet_spatial_adjacent}; "
            f"mean_streamwise_fluctuation_variance={inlet_streamwise_variance}; "
            f"temporal_finite_correlation_fraction={inlet_temporal_finite_fraction}; "
            f"required >= {args.min_inlet_temporal_finite_fraction}; "
            f"spatial_finite_correlation_fraction={inlet_spatial_finite_fraction}; "
            f"required >= {args.min_inlet_spatial_finite_fraction}; "
            f"audit={inlet_correlation_audit_path or metric_inlet_correlation_audit or 'missing'}; "
            f"audit_exists={inlet_correlation_audit_exists}"
        ),
        "Run scripts/audit_inlet_correlation_from_vtk.py on real final-window inlet VTK frames; RMS/k alone is not enough to prove correlated turbulent inflow.",
    )

    inlet_length_status = protocol_status(items, "inlet_turbulence_length_scale")
    inlet_length_source = str(
        get_any(metrics, ["inlet_length_scale_source", "SyntheticTurbulentInletLengthScaleSource"])
        or metadata.get("SyntheticTurbulentInletLengthScaleSource")
        or ""
    )
    inlet_length_gate = str(
        get_any(metrics, ["inlet_length_scale_gate", "SyntheticTurbulentInletLengthScaleGate"])
        or metadata.get("SyntheticTurbulentInletLengthScaleGate")
        or ""
    ).strip().lower()
    synthetic_corr_length_m = as_float(
        get_any(metrics, ["synthetic_correlation_length_m", "SyntheticTurbulenceCorrelationLengthM"])
        or metadata.get("SyntheticTurbulenceCorrelationLengthM")
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
    length_gate_pass = inlet_length_gate == "pass" and length_scale_supported
    add_gate(
        gates,
        "inlet_length_scale",
        PASS if length_gate_pass else FAIL,
        (
            f"protocol_status={inlet_length_status or 'missing'}; "
            f"source={inlet_length_source or 'missing'}; "
            f"gate={inlet_length_gate or 'missing'}; "
            f"synthetic_correlation_length_m={synthetic_corr_length_m}; "
            f"length_scale_source_supported={length_scale_supported}"
        ),
        "Use AIJ-documented turbulence length scales, a precursor/recycling field, or a validated DFM/SEM length-scale model; a user-selected STG correlation length is diagnostic only.",
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
    detailed_probe_audit_ok = probe_audit_traceable or probe_summary_override
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
        if detailed_probe_audit_ok
        and normalization_valid is True
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
            f"official_coordinate_delta_count={coord_delta_count}; valid_n={valid_metric_count}; "
            f"probe_audit_traceable={probe_audit_traceable}; "
            f"allow_summary_only_probe_metrics={probe_summary_override}"
        ),
        "Audit Uref/Zref, wind sign, compared component and RS probe coordinate transform.",
    )

    component_gate = str(get_any(metrics, ["compared_component_consistency_gate", "ComparedComponentConsistencyGate"]) or "").strip().lower()
    metric_component = str(get_any(metrics, ["compared_component", "velocity_component", "ComparedComponent"]) or "").strip().lower()
    probe_valid_component_count, probe_components, probe_missing_component_count, probe_component_error = read_probe_component_audit(probe_path)
    expected_component = args.expected_compared_component.strip().lower()
    if probe_components:
        unique_components = probe_components
    else:
        unique_components = [c for c in metric_component.split(";") if c] if ";" in metric_component else ([metric_component] if metric_component else [])
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
    metric_component_sensitivity_audit_exists = False
    if metric_component_sensitivity_audit:
        try:
            metric_component_sensitivity_path = Path(metric_component_sensitivity_audit).expanduser()
            metric_component_sensitivity_audit_exists = metric_component_sensitivity_path.exists()
            if metric_component_sensitivity_audit_exists and not component_sensitivity_audit:
                component_sensitivity_audit = read_json(metric_component_sensitivity_path)
        except OSError:
            metric_component_sensitivity_audit_exists = False

    component_normalization_gate = str(
        get_any(metrics, ["component_normalization_gate", "ComponentNormalizationGate"])
        or component_sensitivity_audit.get("component_normalization_gate")
        or ""
    ).strip().lower()
    component_sensitivity_gate = str(
        get_any(metrics, ["component_sensitivity_gate", "ComponentSensitivityGate"])
        or component_sensitivity_audit.get("component_sensitivity_gate")
        or ""
    ).strip().lower()
    normalization_scale_gate = str(
        get_any(metrics, ["normalization_scale_gate", "NormalizationScaleGate"])
        or component_sensitivity_audit.get("normalization_scale_gate")
        or ""
    ).strip().lower()
    selected_component = str(
        component_sensitivity_audit.get("selected_component")
        or get_any(metrics, ["compared_component", "velocity_component", "ComparedComponent"])
        or ""
    ).strip().lower()
    best_component = str(
        get_any(metrics, ["best_component_by_rmse", "BestComponentByRmse"])
        or component_sensitivity_audit.get("best_component_by_rmse")
        or ""
    ).strip().lower()
    selected_component_rmse = as_float(
        get_any(metrics, ["selected_component_rmse_ratio", "SelectedComponentRmseRatio"])
        or component_sensitivity_audit.get("selected_component_rmse")
    )
    best_component_rmse = as_float(
        get_any(metrics, ["best_component_rmse_ratio", "BestComponentRmseRatio"])
        or component_sensitivity_audit.get("best_component_rmse")
    )
    component_rmse_improvement = as_float(
        get_any(metrics, ["component_rmse_improvement_ratio", "ComponentRmseImprovementRatio"])
        or component_sensitivity_audit.get("component_rmse_improvement_ratio")
    )
    normalization_best_scale = as_float(
        get_any(metrics, ["normalization_best_fit_scale", "NormalizationBestFitScale"])
        or component_sensitivity_audit.get("selected_best_fit_scale_to_exp")
    )
    normalization_scaled_improvement = as_float(
        get_any(metrics, ["normalization_scaled_improvement_ratio", "NormalizationScaledImprovementRatio"])
        or component_sensitivity_audit.get("selected_scaled_improvement_ratio")
    )
    component_sensitivity_audit_exists = (
        bool(component_sensitivity_audit_path and component_sensitivity_audit_path.exists())
        or metric_component_sensitivity_audit_exists
    )
    add_gate(
        gates,
        "component_normalization_sensitivity",
        PASS if component_normalization_gate == "pass" and component_sensitivity_audit_exists else FAIL,
        (
            f"component_normalization_gate={component_normalization_gate or 'missing'}; "
            f"component_sensitivity_gate={component_sensitivity_gate or 'missing'}; "
            f"normalization_scale_gate={normalization_scale_gate or 'missing'}; "
            f"selected_component={selected_component or 'missing'}; "
            f"best_component_by_rmse={best_component or 'missing'}; "
            f"selected_component_rmse={selected_component_rmse}; "
            f"best_component_rmse={best_component_rmse}; "
            f"component_rmse_improvement_ratio={component_rmse_improvement}; "
            f"normalization_best_fit_scale={normalization_best_scale}; "
            f"normalization_scaled_improvement_ratio={normalization_scaled_improvement}; "
            f"audit={component_sensitivity_audit_path or metric_component_sensitivity_audit or 'missing'}; "
            f"audit_exists={component_sensitivity_audit_exists}"
        ),
        "Run scripts/audit_component_sensitivity.py and fix speed_ratio/streamwise_ratio/component selection or Uref/SI conversion before interpreting systematic bias.",
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
            "min_inlet_temporal_finite_fraction": args.min_inlet_temporal_finite_fraction,
            "min_inlet_spatial_finite_fraction": args.min_inlet_spatial_finite_fraction,
            "max_frontal_blockage_ratio": args.max_frontal_blockage_ratio,
            "max_estimated_mach": args.max_estimated_mach,
            "min_lbm_tau": args.min_lbm_tau,
            "max_lbm_tau": args.max_lbm_tau,
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
            "inlet_correlation_audit": str(inlet_correlation_audit_path) if inlet_correlation_audit_path else "",
            "boundary_protocol_audit": str(boundary_audit_path) if boundary_audit_path else "",
            "component_sensitivity_audit": str(component_sensitivity_audit_path) if component_sensitivity_audit_path else "",
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
