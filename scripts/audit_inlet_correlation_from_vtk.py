#!/usr/bin/env python3
"""Audit turbulent-inlet temporal/spatial correlation from real VTK frames.

This script complements audit_inlet_profile_from_vtk.py. The profile audit
checks whether U(z) and k(z) are preserved; this audit checks whether the inlet
fluctuation field contains measurable time/space correlation instead of only
uncorrelated RMS/k noise. It does not run CFD and does not certify a full
digital-filter, SEM, precursor or Reynolds-stress inlet by itself.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from audit_inlet_profile_from_vtk import (
    choose_axis,
    coordinate,
    discover_vtk_files,
    has_uniform_spacing,
    interpolate,
    is_last_window,
    is_strictly_increasing,
    parse_vector,
    read_af_csv,
    read_json,
    read_selected_vectors,
    read_vtk_metadata,
    select_average_window,
    select_plane_indices,
    sha256_file,
    step_from_name,
)


PASS = "pass"
FAIL = "fail"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit inlet fluctuation correlation from post-spinup VTK frames."
    )
    parser.add_argument("vtk_dir", help="Directory containing u-*.vtk files, or one VTK file.")
    parser.add_argument("--out-json", required=True, help="Output inlet correlation audit JSON.")
    parser.add_argument("--metadata", help="Optional case_metadata.json for traceability.")
    parser.add_argument("--pattern", default="u-*.vtk")
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-frames", type=int, default=40)
    parser.add_argument("--min-step-span", type=int, default=20000)
    parser.add_argument("--wind-direction", default="1,0,0")
    parser.add_argument(
        "--plane-axis",
        default="auto-inlet",
        choices=["auto-inlet", "x", "y", "z"],
        help="Plane normal axis. auto-inlet chooses dominant wind-axis inlet face.",
    )
    parser.add_argument("--plane-value", type=float, default=None)
    parser.add_argument(
        "--plane-index",
        default="nearest",
        choices=["nearest", "min", "max", "inlet", "outlet"],
    )
    parser.add_argument("--plane-tolerance", type=float, default=None)
    parser.add_argument("--velocity-scale", type=float, default=1.0)
    parser.add_argument("--sample-limit", type=int, default=20000)
    parser.add_argument("--min-sample-count", type=int, default=100)
    parser.add_argument("--min-adjacent-pair-count", type=int, default=100)
    parser.add_argument("--min-streamwise-variance", type=float, default=1.0e-12)
    parser.add_argument("--min-temporal-lag1-correlation", type=float, default=0.10)
    parser.add_argument("--min-spatial-adjacent-correlation", type=float, default=0.05)
    parser.add_argument("--max-temporal-lag-count", type=int, default=8)
    parser.add_argument("--max-spatial-lag-cells", type=int, default=8)
    parser.add_argument("--min-temporal-integral-lag-count", type=int, default=2)
    parser.add_argument("--min-spatial-integral-lag-count", type=int, default=2)
    parser.add_argument("--min-temporal-finite-fraction", type=float, default=0.80)
    parser.add_argument("--min-spatial-finite-fraction", type=float, default=0.80)
    parser.add_argument("--af-csv", help="Optional AF CSV containing z,U,k for k-variance traceability.")
    parser.add_argument(
        "--require-k-variance-check",
        action="store_true",
        help="Fail when --af-csv is absent instead of leaving the k-variance check untested.",
    )
    parser.add_argument("--min-k-variance-ratio", type=float, default=0.50)
    parser.add_argument("--max-k-variance-ratio", type=float, default=1.50)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    avg = mean(values)
    if avg is None:
        return None
    return sum((value - avg) ** 2 for value in values) / len(values)


def correlation(a_values: Sequence[float], b_values: Sequence[float]) -> Optional[float]:
    if len(a_values) != len(b_values) or len(a_values) < 2:
        return None
    a_mean = mean(a_values)
    b_mean = mean(b_values)
    if a_mean is None or b_mean is None:
        return None
    a = [value - a_mean for value in a_values]
    b = [value - b_mean for value in b_values]
    numerator = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    if denom <= 1.0e-30:
        return None
    return numerator / denom


def select_deterministic_subset(indices: Sequence[int], limit: int) -> List[int]:
    values = list(indices)
    if limit <= 0 or len(values) <= limit:
        return values
    stride = max(1, int(math.ceil(len(values) / float(limit))))
    return values[::stride][:limit]


def axis_index(axis: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[axis]


def adjacent_pairs(selected: Sequence[int], dims: Tuple[int, int, int], normal_axis: str) -> List[Tuple[int, int]]:
    return lagged_pairs(selected, dims, normal_axis, 1)


def lagged_pairs(selected: Sequence[int], dims: Tuple[int, int, int], normal_axis: str, lag_cells: int) -> List[Tuple[int, int]]:
    if lag_cells <= 0:
        return []
    selected_set = set(selected)
    nx, ny, _ = dims
    strides = [1, nx, nx * ny]
    normal = axis_index(normal_axis)
    pairs: List[Tuple[int, int]] = []
    for axis, stride in enumerate(strides):
        if axis == normal:
            continue
        offset = stride * lag_cells
        for idx in selected:
            neighbor = idx + offset
            if neighbor in selected_set:
                # Avoid wrapping at x/y row boundaries.
                c0 = coordinate(idx, dims, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
                c1 = coordinate(neighbor, dims, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
                if abs(c1[axis] - c0[axis] - float(lag_cells)) <= 1.0e-9:
                    pairs.append((idx, neighbor))
    return pairs


def positive_integral_lag_count(correlations: Sequence[Optional[float]]) -> int:
    count = 0
    for value in correlations:
        if value is None or value <= 0.0:
            break
        count += 1
    return count


def streamwise_variance_target_from_af_k(
    samples: Sequence[Dict[str, float]],
    selected: Sequence[int],
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
) -> Tuple[Optional[float], int]:
    targets: List[float] = []
    for idx in selected:
        z = coordinate(idx, dims, origin, spacing)[2]
        k = interpolate(samples, "k", z)
        if k is None or k < 0.0:
            continue
        # Isotropic fallback: k = 0.5 * (u'^2 + v'^2 + w'^2), so each
        # component variance target is 2k/3.
        targets.append(2.0 * k / 3.0)
    return mean(targets), len(targets)


def tke_target_from_af_k(
    samples: Sequence[Dict[str, float]],
    selected: Sequence[int],
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
) -> Tuple[Optional[float], int]:
    targets: List[float] = []
    for idx in selected:
        z = coordinate(idx, dims, origin, spacing)[2]
        k = interpolate(samples, "k", z)
        if k is None or k < 0.0:
            continue
        targets.append(k)
    return mean(targets), len(targets)


def k_variance_gate(
    actual_variance: Optional[float],
    target_variance: Optional[float],
    min_ratio: float,
    max_ratio: float,
    require_check: bool,
    af_csv_supplied: bool,
) -> Tuple[str, List[str], Optional[float]]:
    if not af_csv_supplied:
        if require_check:
            return FAIL, ["af_csv_missing_for_k_variance_check"], None
        return "not_checked", ["af_csv_not_supplied"], None
    if target_variance is None or target_variance <= 0.0:
        return FAIL, ["k_variance_target_missing_or_nonpositive"], None
    if actual_variance is None or actual_variance <= 0.0:
        return FAIL, ["streamwise_fluctuation_variance_missing_or_nonpositive"], None
    ratio = actual_variance / target_variance
    gate_reasons: List[str] = []
    if ratio < min_ratio:
        gate_reasons.append(f"k_variance_ratio_below_{min_ratio:.6g}")
    if ratio > max_ratio:
        gate_reasons.append(f"k_variance_ratio_above_{max_ratio:.6g}")
    return PASS if not gate_reasons else FAIL, gate_reasons or ["k_variance_evidence_present"], ratio


def tke_gate(
    actual_tke: Optional[float],
    target_k: Optional[float],
    min_ratio: float,
    max_ratio: float,
    require_check: bool,
    af_csv_supplied: bool,
) -> Tuple[str, List[str], Optional[float]]:
    if not af_csv_supplied:
        if require_check:
            return FAIL, ["af_csv_missing_for_tke_check"], None
        return "not_checked", ["af_csv_not_supplied"], None
    if target_k is None or target_k <= 0.0:
        return FAIL, ["tke_target_k_missing_or_nonpositive"], None
    if actual_tke is None or actual_tke <= 0.0:
        return FAIL, ["tke_missing_or_nonpositive"], None
    ratio = actual_tke / target_k
    gate_reasons: List[str] = []
    if ratio < min_ratio:
        gate_reasons.append(f"tke_to_k_ratio_below_{min_ratio:.6g}")
    if ratio > max_ratio:
        gate_reasons.append(f"tke_to_k_ratio_above_{max_ratio:.6g}")
    return PASS if not gate_reasons else FAIL, gate_reasons or ["tke_evidence_present"], ratio


def temporal_lag_correlations(
    streamwise_series: Dict[int, List[float]],
    max_lag_count: int,
) -> List[Optional[float]]:
    lag_count = max(0, max_lag_count)
    correlations: List[Optional[float]] = []
    for lag in range(1, lag_count + 1):
        lag_values: List[float] = []
        for series in streamwise_series.values():
            if len(series) <= lag:
                continue
            corr = correlation(series[:-lag], series[lag:])
            if corr is not None:
                lag_values.append(corr)
        correlations.append(mean(lag_values))
    return correlations


def spatial_lag_correlations(
    streamwise_series: Dict[int, List[float]],
    selected: Sequence[int],
    dims: Tuple[int, int, int],
    normal_axis: str,
    max_lag_cells: int,
) -> Tuple[List[Optional[float]], List[int]]:
    lag_count = max(0, max_lag_cells)
    correlations: List[Optional[float]] = []
    pair_counts: List[int] = []
    for lag in range(1, lag_count + 1):
        pairs = lagged_pairs(selected, dims, normal_axis, lag)
        pair_counts.append(len(pairs))
        values: List[float] = []
        for a_idx, b_idx in pairs:
            corr = correlation(streamwise_series[a_idx], streamwise_series[b_idx])
            if corr is not None:
                values.append(corr)
        correlations.append(mean(values))
    return correlations, pair_counts


def selected_vtk_records(files: Sequence[Path]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in files:
        record: Dict[str, Any] = {
            "path": str(path),
            "time_step": step_from_name(path),
        }
        try:
            record["sha256"] = sha256_file(path)
        except Exception as exc:  # pragma: no cover - defensive audit trace
            record["sha256"] = ""
            record["sha256_error"] = str(exc)
        records.append(record)
    return records


def write_failure_report(
    args: argparse.Namespace,
    vtk_path: Path,
    out_json: Path,
    metadata: Dict[str, Any],
    wind: Tuple[float, float, float],
    reasons: Sequence[str],
    error: str,
    all_files: Optional[Sequence[Path]] = None,
    files: Optional[Sequence[Path]] = None,
) -> int:
    available = list(all_files or [])
    selected = list(files or [])
    available_steps = [step_from_name(path) for path in available]
    source_steps = [step_from_name(path) for path in selected]
    selected_records = selected_vtk_records(selected)
    source_step_span = source_steps[-1] - source_steps[0] if len(source_steps) >= 2 else None
    selected_last_window = is_last_window(source_steps, available_steps)
    report: Dict[str, Any] = {
        "schema": "citylbm.inlet_correlation_audit.v1",
        "generated_at_utc": utc_now(),
        "vtk_dir": str(vtk_path),
        "metadata": str(Path(args.metadata).resolve()) if args.metadata else "",
        "citylbm_version": metadata.get("CityLBMVersion", metadata.get("Version", "")),
        "wind_direction": list(wind),
        "plane_axis": "",
        "plane_mode": "",
        "plane_value": None,
        "plane_tolerance": None,
        "available_frame_count": len(available),
        "frame_count": len(selected),
        "source_time_steps": source_steps,
        "source_time_steps_csv": ",".join(str(step) for step in source_steps),
        "source_step_span": source_step_span,
        "minimum_validation_average_step_span": args.min_step_span,
        "selected_vtk_files": selected_records,
        "source_vtk_sha256": [str(record.get("sha256", "")) for record in selected_records],
        "source_vtk_sha256_csv": ";".join(str(record.get("sha256", "")) for record in selected_records),
        "selected_last_window": selected_last_window,
        "source_steps_strictly_increasing": is_strictly_increasing(source_steps),
        "source_step_spacing_uniform": has_uniform_spacing(source_steps),
        "plane_point_count": 0,
        "sample_count": 0,
        "sample_limit": args.sample_limit,
        "min_sample_count": args.min_sample_count,
        "adjacent_pair_count": 0,
        "min_adjacent_pair_count": args.min_adjacent_pair_count,
        "finite_temporal_correlation_count": 0,
        "finite_spatial_correlation_count": 0,
        "temporal_finite_correlation_fraction": None,
        "spatial_finite_correlation_fraction": None,
        "mean_streamwise_fluctuation_variance": None,
        "mean_component_fluctuation_variance_x": None,
        "mean_component_fluctuation_variance_y": None,
        "mean_component_fluctuation_variance_z": None,
        "mean_turbulent_kinetic_energy_from_components": None,
        "af_csv": str(Path(args.af_csv).resolve()) if args.af_csv else "",
        "af_csv_sha256": "",
        "inlet_k_variance_gate": FAIL if args.require_k_variance_check else "not_checked",
        "inlet_k_variance_gate_reasons": (
            ["af_csv_missing_for_k_variance_check"]
            if args.require_k_variance_check
            else ["k_variance_not_evaluated_after_audit_failure"]
        ),
        "inlet_streamwise_variance_target_from_k": None,
        "inlet_streamwise_variance_to_k_ratio": None,
        "inlet_k_variance_target_sample_count": 0,
        "inlet_tke_gate": FAIL if args.require_k_variance_check else "not_checked",
        "inlet_tke_gate_reasons": (
            ["af_csv_missing_for_tke_check"]
            if args.require_k_variance_check
            else ["tke_not_evaluated_after_audit_failure"]
        ),
        "inlet_tke_target_from_af_k": None,
        "inlet_tke_to_k_ratio": None,
        "inlet_tke_target_sample_count": 0,
        "min_k_variance_ratio": args.min_k_variance_ratio,
        "max_k_variance_ratio": args.max_k_variance_ratio,
        "temporal_lag1_mean_correlation": None,
        "temporal_lag1_abs_mean_correlation": None,
        "temporal_lag_correlations": [],
        "temporal_integral_positive_lag_count": 0,
        "temporal_integral_time_steps": 0,
        "spatial_adjacent_mean_correlation": None,
        "spatial_lag_correlations": [],
        "spatial_lag_pair_counts": [],
        "spatial_integral_positive_lag_count": 0,
        "spatial_integral_length_cells": 0,
        "spatial_integral_length_m": 0.0,
        "min_streamwise_variance": args.min_streamwise_variance,
        "min_temporal_lag1_correlation": args.min_temporal_lag1_correlation,
        "min_spatial_adjacent_correlation": args.min_spatial_adjacent_correlation,
        "max_temporal_lag_count": args.max_temporal_lag_count,
        "max_spatial_lag_cells": args.max_spatial_lag_cells,
        "min_temporal_integral_lag_count": args.min_temporal_integral_lag_count,
        "min_spatial_integral_lag_count": args.min_spatial_integral_lag_count,
        "min_temporal_finite_fraction": args.min_temporal_finite_fraction,
        "min_spatial_finite_fraction": args.min_spatial_finite_fraction,
        "audit_error": error,
        "inlet_correlation_gate": FAIL,
        "inlet_correlation_gate_reasons": list(reasons) or ["inlet_correlation_audit_failed"],
        "paper_grade_note": (
            "A failed correlation audit is archived as evidence that the run is not paper-grade for turbulent-inlet "
            "claims. Re-run after producing enough post-spinup VTK frames and verifying the inlet plane selection."
        ),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "inlet_correlation_gate=fail; temporal_lag1=None; temporal_lag1_abs=None; spatial=None; reasons={reasons}".format(
            reasons=";".join(report["inlet_correlation_gate_reasons"]),
        )
    )
    return 2


def main() -> int:
    args = parse_args()
    vtk_path = Path(args.vtk_dir).resolve()
    out_json = Path(args.out_json).resolve()
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
    wind = parse_vector(args.wind_direction)

    try:
        all_files = discover_vtk_files(vtk_path, args.pattern)
    except SystemExit as exc:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["vtk_files_missing"],
            str(exc),
        )
    files = select_average_window(all_files, args.average_last_n)
    if not files:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["selected_vtk_window_empty"],
            "No VTK frames were selected for inlet correlation auditing.",
            all_files,
            files,
        )
    available_steps = [step_from_name(path) for path in all_files]
    source_steps = [step_from_name(path) for path in files]
    selected_vtk_files = selected_vtk_records(files)
    source_vtk_hashes = [record["sha256"] for record in selected_vtk_files]
    selected_last_window = is_last_window(source_steps, available_steps)
    source_steps_increasing = is_strictly_increasing(source_steps)
    source_spacing_uniform = has_uniform_spacing(source_steps)
    source_step_span = source_steps[-1] - source_steps[0] if len(source_steps) >= 2 else None

    try:
        frames = [read_vtk_metadata(path) for path in files]
    except Exception as exc:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["vtk_metadata_read_failed"],
            str(exc),
            all_files,
            files,
        )
    if not frames:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["vtk_metadata_frames_empty"],
            "No VTK metadata frames were available after reading selected files.",
            all_files,
            files,
        )
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            return write_failure_report(
                args,
                vtk_path,
                out_json,
                metadata,
                wind,
                ["vtk_grid_mismatch"],
                "All VTK frames must have identical grid dimensions, origin and spacing.",
                all_files,
                files,
            )

    axis = choose_axis(args, wind)
    try:
        plane_indices, plane_value, tolerance, plane_mode = select_plane_indices(first, axis, wind, args)
    except Exception as exc:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["inlet_plane_selection_failed"],
            str(exc),
            all_files,
            files,
        )
    selected = select_deterministic_subset(plane_indices, args.sample_limit)
    try:
        frame_vectors = [read_selected_vectors(frame, selected, args.velocity_scale) for frame in frames]
    except Exception as exc:
        return write_failure_report(
            args,
            vtk_path,
            out_json,
            metadata,
            wind,
            ["vtk_vector_read_failed"],
            str(exc),
            all_files,
            files,
        )

    streamwise_series: Dict[int, List[float]] = {}
    variances: List[float] = []
    component_variances: List[List[float]] = [[], [], []]
    tke_values: List[float] = []
    temporal_corrs: List[float] = []
    temporal_abs_corrs: List[float] = []
    for idx in selected:
        series = [
            sum(vectors[idx][component] * wind[component] for component in range(3))
            for vectors in frame_vectors
        ]
        streamwise_series[idx] = series
        var = variance(series)
        if var is not None:
            variances.append(var)
        point_component_variances: List[float] = []
        for component in range(3):
            component_series = [vectors[idx][component] for vectors in frame_vectors]
            component_var = variance(component_series)
            if component_var is None:
                point_component_variances = []
                break
            component_variances[component].append(component_var)
            point_component_variances.append(component_var)
        if len(point_component_variances) == 3:
            tke_values.append(0.5 * sum(point_component_variances))
        corr = correlation(series[:-1], series[1:])
        if corr is not None:
            temporal_corrs.append(corr)
            temporal_abs_corrs.append(abs(corr))

    pairs = adjacent_pairs(selected, first["dimensions"], axis)
    spatial_corrs: List[float] = []
    for a_idx, b_idx in pairs:
        corr = correlation(streamwise_series[a_idx], streamwise_series[b_idx])
        if corr is not None:
            spatial_corrs.append(corr)

    mean_variance = mean(variances)
    mean_component_variances = [mean(values) for values in component_variances]
    mean_tke = mean(tke_values)
    temporal_corr = mean(temporal_corrs)
    temporal_abs_corr = mean(temporal_abs_corrs)
    spatial_corr = mean(spatial_corrs)
    temporal_lag_values = temporal_lag_correlations(
        streamwise_series,
        args.max_temporal_lag_count,
    )
    temporal_integral_lag_count = positive_integral_lag_count(temporal_lag_values)
    source_step_interval = (
        source_steps[1] - source_steps[0]
        if len(source_steps) >= 2 and source_spacing_uniform
        else None
    )
    temporal_integral_time_steps = (
        temporal_integral_lag_count * source_step_interval
        if source_step_interval is not None
        else None
    )
    spatial_lag_values, spatial_lag_pair_counts = spatial_lag_correlations(
        streamwise_series,
        selected,
        first["dimensions"],
        axis,
        args.max_spatial_lag_cells,
    )
    spatial_integral_lag_count = positive_integral_lag_count(spatial_lag_values)
    normal_index = axis_index(axis)
    tangential_spacing = [
        abs(float(first["spacing"][idx]))
        for idx in range(3)
        if idx != normal_index
    ]
    mean_tangential_spacing = mean(tangential_spacing)
    spatial_integral_length_m = (
        spatial_integral_lag_count * mean_tangential_spacing
        if mean_tangential_spacing is not None
        else None
    )
    temporal_finite_fraction = len(temporal_corrs) / float(len(selected)) if selected else None
    spatial_finite_fraction = len(spatial_corrs) / float(len(pairs)) if pairs else None

    af_csv_sha = ""
    af_csv_samples: List[Dict[str, float]] = []
    k_variance_target: Optional[float] = None
    k_variance_target_count = 0
    tke_target: Optional[float] = None
    tke_target_count = 0
    k_variance_gate_reasons: List[str] = []
    af_csv_supplied = bool(args.af_csv)
    if args.af_csv:
        af_path = Path(args.af_csv).resolve()
        try:
            af_csv_sha = sha256_file(af_path)
            af_csv_samples = read_af_csv(af_path)
            k_variance_target, k_variance_target_count = streamwise_variance_target_from_af_k(
                af_csv_samples,
                selected,
                first["dimensions"],
                first["origin"],
                first["spacing"],
            )
            tke_target, tke_target_count = tke_target_from_af_k(
                af_csv_samples,
                selected,
                first["dimensions"],
                first["origin"],
                first["spacing"],
            )
        except Exception as exc:
            k_variance_gate_reasons.append(f"af_csv_k_variance_read_failed:{exc}")

    k_gate, k_reasons, k_variance_ratio = k_variance_gate(
        mean_variance,
        k_variance_target,
        args.min_k_variance_ratio,
        args.max_k_variance_ratio,
        args.require_k_variance_check,
        af_csv_supplied,
    )
    tke_check_gate, tke_reasons, tke_ratio = tke_gate(
        mean_tke,
        tke_target,
        args.min_k_variance_ratio,
        args.max_k_variance_ratio,
        args.require_k_variance_check,
        af_csv_supplied,
    )
    if k_variance_gate_reasons:
        k_gate = FAIL
        k_reasons = k_variance_gate_reasons
        tke_check_gate = FAIL
        tke_reasons = k_variance_gate_reasons

    reasons: List[str] = []
    if args.average_last_n <= 0:
        reasons.append("averaging_window_not_explicit")
    if len(frames) < args.min_frames:
        reasons.append(f"averaged_frame_count_below_{args.min_frames}")
    if not selected_last_window:
        reasons.append("not_last_available_window")
    if not source_steps_increasing:
        reasons.append("source_steps_not_strictly_increasing")
    if not source_spacing_uniform:
        reasons.append("source_step_spacing_not_uniform")
    if source_step_span is None:
        reasons.append("source_step_span_missing")
    elif source_step_span < args.min_step_span:
        reasons.append(f"source_step_span_below_{args.min_step_span}")
    if mean_variance is None or mean_variance <= args.min_streamwise_variance:
        reasons.append("streamwise_fluctuation_variance_missing_or_too_small")
    if len(selected) < args.min_sample_count:
        reasons.append(f"sample_count_below_{args.min_sample_count}")
    if len(pairs) < args.min_adjacent_pair_count:
        reasons.append(f"adjacent_pair_count_below_{args.min_adjacent_pair_count}")
    if temporal_corr is None or temporal_corr < args.min_temporal_lag1_correlation:
        reasons.append(
            f"temporal_lag1_correlation_below_{args.min_temporal_lag1_correlation:.6g}"
        )
    if temporal_finite_fraction is None or temporal_finite_fraction < args.min_temporal_finite_fraction:
        reasons.append(
            f"temporal_finite_fraction_below_{args.min_temporal_finite_fraction:.6g}"
        )
    if temporal_integral_lag_count < args.min_temporal_integral_lag_count:
        reasons.append(
            f"temporal_integral_lag_count_below_{args.min_temporal_integral_lag_count}"
        )
    if spatial_corr is None or spatial_corr < args.min_spatial_adjacent_correlation:
        reasons.append(
            f"spatial_adjacent_correlation_below_{args.min_spatial_adjacent_correlation:.6g}"
        )
    if spatial_finite_fraction is None or spatial_finite_fraction < args.min_spatial_finite_fraction:
        reasons.append(
            f"spatial_finite_fraction_below_{args.min_spatial_finite_fraction:.6g}"
        )
    if spatial_integral_lag_count < args.min_spatial_integral_lag_count:
        reasons.append(
            f"spatial_integral_lag_count_below_{args.min_spatial_integral_lag_count}"
        )
    if k_gate == FAIL:
        reasons.extend(k_reasons)
    if tke_check_gate == FAIL:
        reasons.extend(tke_reasons)

    gate = PASS if not reasons else FAIL
    report: Dict[str, Any] = {
        "schema": "citylbm.inlet_correlation_audit.v1",
        "generated_at_utc": utc_now(),
        "vtk_dir": str(vtk_path),
        "metadata": str(Path(args.metadata).resolve()) if args.metadata else "",
        "citylbm_version": metadata.get("CityLBMVersion", metadata.get("Version", "")),
        "wind_direction": list(wind),
        "plane_axis": axis,
        "plane_mode": plane_mode,
        "plane_value": plane_value,
        "plane_tolerance": tolerance,
        "available_frame_count": len(all_files),
        "frame_count": len(frames),
        "source_time_steps": source_steps,
        "source_time_steps_csv": ",".join(str(step) for step in source_steps),
        "source_step_span": source_step_span,
        "minimum_validation_average_step_span": args.min_step_span,
        "selected_vtk_files": selected_vtk_files,
        "source_vtk_sha256": source_vtk_hashes,
        "source_vtk_sha256_csv": ";".join(source_vtk_hashes),
        "selected_last_window": selected_last_window,
        "source_steps_strictly_increasing": source_steps_increasing,
        "source_step_spacing_uniform": source_spacing_uniform,
        "plane_point_count": len(plane_indices),
        "sample_count": len(selected),
        "sample_limit": args.sample_limit,
        "min_sample_count": args.min_sample_count,
        "adjacent_pair_count": len(pairs),
        "min_adjacent_pair_count": args.min_adjacent_pair_count,
        "finite_temporal_correlation_count": len(temporal_corrs),
        "finite_spatial_correlation_count": len(spatial_corrs),
        "temporal_finite_correlation_fraction": temporal_finite_fraction,
        "spatial_finite_correlation_fraction": spatial_finite_fraction,
        "mean_streamwise_fluctuation_variance": mean_variance,
        "mean_component_fluctuation_variance_x": mean_component_variances[0],
        "mean_component_fluctuation_variance_y": mean_component_variances[1],
        "mean_component_fluctuation_variance_z": mean_component_variances[2],
        "mean_turbulent_kinetic_energy_from_components": mean_tke,
        "af_csv": str(Path(args.af_csv).resolve()) if args.af_csv else "",
        "af_csv_sha256": af_csv_sha,
        "inlet_k_variance_gate": k_gate,
        "inlet_k_variance_gate_reasons": k_reasons,
        "inlet_streamwise_variance_target_from_k": k_variance_target,
        "inlet_streamwise_variance_to_k_ratio": k_variance_ratio,
        "inlet_k_variance_target_sample_count": k_variance_target_count,
        "inlet_tke_gate": tke_check_gate,
        "inlet_tke_gate_reasons": tke_reasons,
        "inlet_tke_target_from_af_k": tke_target,
        "inlet_tke_to_k_ratio": tke_ratio,
        "inlet_tke_target_sample_count": tke_target_count,
        "min_k_variance_ratio": args.min_k_variance_ratio,
        "max_k_variance_ratio": args.max_k_variance_ratio,
        "temporal_lag1_mean_correlation": temporal_corr,
        "temporal_lag1_abs_mean_correlation": temporal_abs_corr,
        "temporal_lag_correlations": temporal_lag_values,
        "temporal_integral_positive_lag_count": temporal_integral_lag_count,
        "temporal_integral_time_steps": temporal_integral_time_steps,
        "spatial_adjacent_mean_correlation": spatial_corr,
        "spatial_lag_correlations": spatial_lag_values,
        "spatial_lag_pair_counts": spatial_lag_pair_counts,
        "spatial_integral_positive_lag_count": spatial_integral_lag_count,
        "spatial_integral_length_cells": spatial_integral_lag_count,
        "spatial_integral_length_m": spatial_integral_length_m,
        "min_streamwise_variance": args.min_streamwise_variance,
        "min_temporal_lag1_correlation": args.min_temporal_lag1_correlation,
        "min_spatial_adjacent_correlation": args.min_spatial_adjacent_correlation,
        "max_temporal_lag_count": args.max_temporal_lag_count,
        "max_spatial_lag_cells": args.max_spatial_lag_cells,
        "min_temporal_integral_lag_count": args.min_temporal_integral_lag_count,
        "min_spatial_integral_lag_count": args.min_spatial_integral_lag_count,
        "min_temporal_finite_fraction": args.min_temporal_finite_fraction,
        "min_spatial_finite_fraction": args.min_spatial_finite_fraction,
        "inlet_correlation_gate": gate,
        "inlet_correlation_gate_reasons": reasons or ["inlet_correlation_evidence_present"],
        "paper_grade_note": (
            "A passing correlation audit proves only measurable inlet time/space correlation in the sampled VTK frames. "
            "It does not by itself prove a full digital-filter, SEM, precursor/recycling, Reynolds-stress or "
            "distribution-consistent inlet."
        ),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "inlet_correlation_gate={gate}; temporal_lag1={temporal}; temporal_lag1_abs={temporal_abs}; temporal_integral_lags={temporal_integral}; spatial={spatial}; spatial_integral_lags={spatial_integral}; reasons={reasons}".format(
            gate=gate,
            temporal=temporal_corr,
            temporal_abs=temporal_abs_corr,
            temporal_integral=temporal_integral_lag_count,
            spatial=spatial_corr,
            spatial_integral=spatial_integral_lag_count,
            reasons=";".join(report["inlet_correlation_gate_reasons"]),
        )
    )
    return 0 if gate == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
