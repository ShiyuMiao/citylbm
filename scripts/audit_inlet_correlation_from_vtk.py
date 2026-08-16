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
    is_last_window,
    is_strictly_increasing,
    parse_vector,
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
    parser.add_argument("--average-last-n", type=int, default=10)
    parser.add_argument("--min-frames", type=int, default=10)
    parser.add_argument("--min-step-span", type=int, default=1000)
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
    parser.add_argument("--min-temporal-finite-fraction", type=float, default=0.80)
    parser.add_argument("--min-spatial-finite-fraction", type=float, default=0.80)
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
    selected_set = set(selected)
    nx, ny, _ = dims
    strides = [1, nx, nx * ny]
    normal = axis_index(normal_axis)
    pairs: List[Tuple[int, int]] = []
    for axis, stride in enumerate(strides):
        if axis == normal:
            continue
        for idx in selected:
            neighbor = idx + stride
            if neighbor in selected_set:
                # Avoid wrapping at x/y row boundaries.
                c0 = coordinate(idx, dims, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
                c1 = coordinate(neighbor, dims, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
                if abs(c1[axis] - c0[axis] - 1.0) <= 1.0e-9:
                    pairs.append((idx, neighbor))
    return pairs


def main() -> int:
    args = parse_args()
    vtk_path = Path(args.vtk_dir).resolve()
    out_json = Path(args.out_json).resolve()
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
    wind = parse_vector(args.wind_direction)

    all_files = discover_vtk_files(vtk_path, args.pattern)
    files = select_average_window(all_files, args.average_last_n)
    available_steps = [step_from_name(path) for path in all_files]
    source_steps = [step_from_name(path) for path in files]
    selected_vtk_files = [
        {"path": str(path), "time_step": step_from_name(path), "sha256": sha256_file(path)}
        for path in files
    ]
    source_vtk_hashes = [record["sha256"] for record in selected_vtk_files]
    selected_last_window = is_last_window(source_steps, available_steps)
    source_steps_increasing = is_strictly_increasing(source_steps)
    source_spacing_uniform = has_uniform_spacing(source_steps)
    source_step_span = source_steps[-1] - source_steps[0] if len(source_steps) >= 2 else None

    frames = [read_vtk_metadata(path) for path in files]
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            raise SystemExit("All VTK frames must have identical grid dimensions, origin and spacing.")

    axis = choose_axis(args, wind)
    plane_indices, plane_value, tolerance, plane_mode = select_plane_indices(first, axis, wind, args)
    selected = select_deterministic_subset(plane_indices, args.sample_limit)
    frame_vectors = [read_selected_vectors(frame, selected, args.velocity_scale) for frame in frames]

    streamwise_series: Dict[int, List[float]] = {}
    variances: List[float] = []
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
    temporal_corr = mean(temporal_corrs)
    temporal_abs_corr = mean(temporal_abs_corrs)
    spatial_corr = mean(spatial_corrs)
    temporal_finite_fraction = len(temporal_corrs) / float(len(selected)) if selected else None
    spatial_finite_fraction = len(spatial_corrs) / float(len(pairs)) if pairs else None

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
    if spatial_corr is None or spatial_corr < args.min_spatial_adjacent_correlation:
        reasons.append(
            f"spatial_adjacent_correlation_below_{args.min_spatial_adjacent_correlation:.6g}"
        )
    if spatial_finite_fraction is None or spatial_finite_fraction < args.min_spatial_finite_fraction:
        reasons.append(
            f"spatial_finite_fraction_below_{args.min_spatial_finite_fraction:.6g}"
        )

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
        "temporal_lag1_mean_correlation": temporal_corr,
        "temporal_lag1_abs_mean_correlation": temporal_abs_corr,
        "spatial_adjacent_mean_correlation": spatial_corr,
        "min_streamwise_variance": args.min_streamwise_variance,
        "min_temporal_lag1_correlation": args.min_temporal_lag1_correlation,
        "min_spatial_adjacent_correlation": args.min_spatial_adjacent_correlation,
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
        "inlet_correlation_gate={gate}; temporal_lag1={temporal}; temporal_lag1_abs={temporal_abs}; spatial={spatial}; reasons={reasons}".format(
            gate=gate,
            temporal=temporal_corr,
            temporal_abs=temporal_abs_corr,
            spatial=spatial_corr,
            reasons=";".join(report["inlet_correlation_gate_reasons"]),
        )
    )
    return 0 if gate == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
