#!/usr/bin/env python3
"""Audit runtime boundary-face velocity preservation from real VTK frames.

This script reads final-window `u-*.vtk` files and compares streamwise velocity
on inlet/outlet/lateral/top faces against the AF U(z) table. It is a diagnostic
boundary-contamination check for native FluidX3D/CityLBM validation packages;
it does not claim a simplified TYPE_E boundary is wind-tunnel equivalent.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from audit_inlet_profile_from_vtk import (
    axis_index,
    coordinate,
    discover_vtk_files,
    has_uniform_spacing,
    interpolate,
    is_last_window,
    is_strictly_increasing,
    mean,
    parse_vector,
    read_af_csv,
    read_selected_vectors,
    read_vtk_metadata,
    rmse,
    select_average_window,
    sha256_file,
    stddev,
    step_from_name,
)


PASS = "pass"
FAIL = "fail"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit boundary-face streamwise velocity preservation from VTK output."
    )
    parser.add_argument("vtk_dir", help="Directory containing u-*.vtk files, or one VTK file.")
    parser.add_argument("--af-csv", required=True, help="AF profile CSV with z,U and optional k columns.")
    parser.add_argument("--out-json", required=True, help="Output boundary_runtime_audit.json.")
    parser.add_argument("--out-csv", help="Optional per-face summary CSV.")
    parser.add_argument("--pattern", default="u-*.vtk")
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-frames", type=int, default=40)
    parser.add_argument("--min-step-span", type=int, default=20000)
    parser.add_argument("--wind-direction", default="1,0,0", help="Airflow vector, e.g. 0,-1,0.")
    parser.add_argument("--velocity-scale", type=float, default=1.0)
    parser.add_argument("--plane-tolerance", type=float, default=None)
    parser.add_argument("--max-inlet-u-mae-ratio", type=float, default=0.05)
    parser.add_argument("--max-side-top-u-mae-ratio", type=float, default=0.15)
    parser.add_argument("--max-outlet-u-mae-ratio", type=float, default=0.25)
    parser.add_argument("--max-negative-streamwise-fraction", type=float, default=0.05)
    parser.add_argument("--max-side-top-normal-velocity-ratio", type=float, default=0.10)
    return parser.parse_args()


def normalized_axis_name(axis_idx: int) -> str:
    return ["x", "y", "z"][axis_idx]


def face_indices(
    frame: Dict[str, Any],
    axis: str,
    side: str,
    tolerance: Optional[float],
) -> Tuple[List[int], float, float]:
    dims = frame["dimensions"]
    origin = frame["origin"]
    spacing = frame["spacing"]
    ax = axis_index(axis)
    n_axis = dims[ax]
    coords = [origin[ax] + i * spacing[ax] for i in range(n_axis)]
    value = min(coords) if side == "min" else max(coords)
    tol = tolerance
    if tol is None:
        tol = abs(spacing[ax]) * 0.51 if abs(spacing[ax]) > 1.0e-12 else 1.0e-9
    indices: List[int] = []
    for idx in range(dims[0] * dims[1] * dims[2]):
        coord = coordinate(idx, dims, origin, spacing)
        if abs(coord[ax] - value) <= tol:
            indices.append(idx)
    if not indices:
        raise SystemExit(f"No VTK points found on {axis}={value} within tolerance {tol}.")
    return indices, value, tol


def build_face_specs(wind: Tuple[float, float, float]) -> List[Dict[str, str]]:
    dominant_idx = max(range(3), key=lambda idx: abs(wind[idx]))
    dominant_axis = normalized_axis_name(dominant_idx)
    inlet_side = "min" if wind[dominant_idx] >= 0.0 else "max"
    outlet_side = "max" if inlet_side == "min" else "min"
    lateral_idx = 1 if dominant_axis == "x" else 0
    lateral_axis = normalized_axis_name(lateral_idx)
    return [
        {"name": "inlet", "axis": dominant_axis, "side": inlet_side},
        {"name": "outlet", "axis": dominant_axis, "side": outlet_side},
        {"name": "lateral_min", "axis": lateral_axis, "side": "min"},
        {"name": "lateral_max", "axis": lateral_axis, "side": "max"},
        {"name": "top", "axis": "z", "side": "max"},
    ]


def face_stats(
    name: str,
    axis: str,
    side: str,
    plane_value: float,
    tolerance: float,
    selected: Sequence[int],
    frame_vectors: Sequence[Dict[int, Tuple[float, float, float]]],
    frame: Dict[str, Any],
    wind: Tuple[float, float, float],
    af_samples: Sequence[Dict[str, float]],
) -> Dict[str, Any]:
    streamwise_means: List[float] = []
    expected_values: List[float] = []
    errors: List[float] = []
    speed_stddevs: List[float] = []
    normal_abs_values: List[float] = []
    negative_count = 0
    total_count = 0
    normal_idx = axis_index(axis)

    for idx in selected:
        coord = coordinate(idx, frame["dimensions"], frame["origin"], frame["spacing"])
        velocities = [vectors[idx] for vectors in frame_vectors]
        streamwise_values = [sum(v[i] * wind[i] for i in range(3)) for v in velocities]
        normal_abs_values.extend(abs(v[normal_idx]) for v in velocities)
        streamwise_mean = mean(streamwise_values)
        expected = interpolate(af_samples, "u", coord[2])
        if streamwise_mean is None or expected is None:
            continue
        streamwise_means.append(streamwise_mean)
        expected_values.append(abs(expected))
        errors.append(streamwise_mean - expected)
        speed_std = stddev([math.sqrt(sum(component * component for component in v)) for v in velocities])
        if speed_std is not None:
            speed_stddevs.append(speed_std)
        negative_count += sum(1 for value in streamwise_values if value < 0.0)
        total_count += len(streamwise_values)

    mae_value = sum(abs(value) for value in errors) / len(errors) if errors else None
    rmse_value = rmse(errors)
    bias_value = mean(errors)
    den = mean(expected_values)
    mean_streamwise = mean(streamwise_means)
    mean_abs_normal = mean(normal_abs_values)
    max_abs_normal = max(normal_abs_values) if normal_abs_values else None
    return {
        "name": name,
        "axis": axis,
        "side": side,
        "plane_value": plane_value,
        "plane_tolerance": tolerance,
        "sample_point_count": len(selected),
        "valid_sample_point_count": len(errors),
        "mean_streamwise_mps": mean_streamwise,
        "mean_af_u_mps": den,
        "u_mae_mps": mae_value,
        "u_rmse_mps": rmse_value,
        "u_bias_mps": bias_value,
        "u_mae_ratio": mae_value / den if mae_value is not None and den and den > 1.0e-12 else None,
        "u_rmse_ratio": rmse_value / den if rmse_value is not None and den and den > 1.0e-12 else None,
        "u_bias_ratio": bias_value / den if bias_value is not None and den and den > 1.0e-12 else None,
        "negative_streamwise_fraction": negative_count / total_count if total_count else None,
        "mean_abs_normal_velocity_mps": mean_abs_normal,
        "max_abs_normal_velocity_mps": max_abs_normal,
        "mean_abs_normal_velocity_ratio": (
            mean_abs_normal / den if mean_abs_normal is not None and den and den > 1.0e-12 else None
        ),
        "max_abs_normal_velocity_ratio": (
            max_abs_normal / den if max_abs_normal is not None and den and den > 1.0e-12 else None
        ),
        "mean_speed_stddev_mps": mean(speed_stddevs),
        "mean_speed_stddev_ratio": (
            (mean(speed_stddevs) or 0.0) / mean_streamwise
            if speed_stddevs and mean_streamwise and abs(mean_streamwise) > 1.0e-12
            else None
        ),
    }


def ratio_ok(value: Optional[float], maximum: float) -> bool:
    return value is not None and abs(value) <= maximum


def frac_ok(value: Optional[float], maximum: float) -> bool:
    return value is not None and value <= maximum


def main() -> int:
    args = parse_args()
    vtk_path = Path(args.vtk_dir).resolve()
    af_path = Path(args.af_csv).resolve()
    out_json = Path(args.out_json).resolve()
    out_csv = Path(args.out_csv).resolve() if args.out_csv else None
    wind = parse_vector(args.wind_direction)
    af_samples = read_af_csv(af_path)
    all_files = discover_vtk_files(vtk_path, args.pattern)
    files = select_average_window(all_files, args.average_last_n)
    available_steps = [step_from_name(path) for path in all_files]
    source_steps = [step_from_name(path) for path in files]
    selected_vtk_files = [
        {"path": str(path), "time_step": step_from_name(path), "sha256": sha256_file(path)}
        for path in files
    ]
    frames = [read_vtk_metadata(path) for path in files]
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            raise SystemExit("All VTK frames must have identical grid dimensions, origin and spacing.")

    face_reports: List[Dict[str, Any]] = []
    for spec in build_face_specs(wind):
        selected, plane_value, tolerance = face_indices(
            first, spec["axis"], spec["side"], args.plane_tolerance
        )
        vectors = [read_selected_vectors(frame, selected, args.velocity_scale) for frame in frames]
        face_reports.append(
            face_stats(
                spec["name"],
                spec["axis"],
                spec["side"],
                plane_value,
                tolerance,
                selected,
                vectors,
                first,
                wind,
                af_samples,
            )
        )

    by_name = {face["name"]: face for face in face_reports}
    inlet = by_name["inlet"]
    outlet = by_name["outlet"]
    side_top = [by_name["lateral_min"], by_name["lateral_max"], by_name["top"]]
    all_faces = [inlet, outlet] + side_top
    frame_count = len(files)
    source_step_span = source_steps[-1] - source_steps[0] if len(source_steps) >= 2 else None
    time_reasons: List[str] = []
    if frame_count < args.min_frames:
        time_reasons.append(f"averaged_frame_count_below_{args.min_frames}")
    if not is_last_window(source_steps, available_steps):
        time_reasons.append("not_last_available_window")
    if not is_strictly_increasing(source_steps):
        time_reasons.append("source_steps_not_strictly_increasing")
    if not has_uniform_spacing(source_steps):
        time_reasons.append("source_step_spacing_not_uniform")
    if source_step_span is None or source_step_span < args.min_step_span:
        time_reasons.append(f"source_step_span_below_{args.min_step_span}")

    traceability_gate = PASS if not time_reasons and all(face["valid_sample_point_count"] > 0 for face in all_faces) else FAIL
    inlet_reasons: List[str] = []
    if not ratio_ok(inlet.get("u_mae_ratio"), args.max_inlet_u_mae_ratio):
        inlet_reasons.append("inlet_u_mae_ratio_above_threshold")
    if not frac_ok(inlet.get("negative_streamwise_fraction"), args.max_negative_streamwise_fraction):
        inlet_reasons.append("inlet_negative_streamwise_fraction_above_threshold")
    inlet_gate = PASS if not inlet_reasons else FAIL

    side_top_reasons: List[str] = []
    for face in side_top:
        if not ratio_ok(face.get("u_mae_ratio"), args.max_side_top_u_mae_ratio):
            side_top_reasons.append(f"{face['name']}_u_mae_ratio_above_threshold")
        if not frac_ok(face.get("negative_streamwise_fraction"), args.max_negative_streamwise_fraction):
            side_top_reasons.append(f"{face['name']}_negative_streamwise_fraction_above_threshold")
    side_top_gate = PASS if not side_top_reasons else FAIL

    side_top_normal_reasons: List[str] = []
    for face in side_top:
        if not ratio_ok(face.get("max_abs_normal_velocity_ratio"), args.max_side_top_normal_velocity_ratio):
            side_top_normal_reasons.append(f"{face['name']}_normal_velocity_ratio_above_threshold")
    side_top_normal_gate = PASS if not side_top_normal_reasons else FAIL

    outlet_reasons: List[str] = []
    if not ratio_ok(outlet.get("u_mae_ratio"), args.max_outlet_u_mae_ratio):
        outlet_reasons.append("outlet_u_mae_ratio_above_threshold")
    if not frac_ok(outlet.get("negative_streamwise_fraction"), args.max_negative_streamwise_fraction):
        outlet_reasons.append("outlet_negative_streamwise_fraction_above_threshold")
    outlet_gate = PASS if not outlet_reasons else FAIL

    profile_gate = PASS if inlet_gate == PASS and side_top_gate == PASS and outlet_gate == PASS else FAIL
    runtime_reasons = []
    if traceability_gate != PASS:
        runtime_reasons.extend(time_reasons or ["boundary_face_sampling_incomplete"])
    runtime_reasons.extend(inlet_reasons)
    runtime_reasons.extend(side_top_reasons)
    runtime_reasons.extend(side_top_normal_reasons)
    runtime_reasons.extend(outlet_reasons)
    boundary_runtime_gate = PASS if traceability_gate == PASS and profile_gate == PASS and side_top_normal_gate == PASS else FAIL
    max_u_mae_ratio = max(
        [face.get("u_mae_ratio") for face in all_faces if face.get("u_mae_ratio") is not None],
        default=None,
    )
    max_negative_fraction = max(
        [face.get("negative_streamwise_fraction") for face in all_faces if face.get("negative_streamwise_fraction") is not None],
        default=None,
    )
    max_side_top_normal_velocity_ratio = max(
        [face.get("max_abs_normal_velocity_ratio") for face in side_top if face.get("max_abs_normal_velocity_ratio") is not None],
        default=None,
    )
    max_side_top_normal_abs_mps = max(
        [face.get("max_abs_normal_velocity_mps") for face in side_top if face.get("max_abs_normal_velocity_mps") is not None],
        default=None,
    )

    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_runtime_audit.v1",
        "vtk_dir": str(vtk_path),
        "af_csv": str(af_path),
        "af_csv_sha256": hashlib.sha256(af_path.read_bytes()).hexdigest(),
        "pattern": args.pattern,
        "average_last_n": args.average_last_n,
        "frame_count": frame_count,
        "source_time_steps": source_steps,
        "source_first_time_step": source_steps[0] if source_steps else None,
        "source_last_time_step": source_steps[-1] if source_steps else None,
        "source_step_span": source_step_span,
        "source_steps_strictly_increasing": is_strictly_increasing(source_steps),
        "source_step_spacing_uniform": has_uniform_spacing(source_steps),
        "selected_last_window": is_last_window(source_steps, available_steps),
        "selected_vtk_files": selected_vtk_files,
        "wind_direction": wind,
        "boundary_runtime_traceability_gate": traceability_gate,
        "boundary_runtime_traceability_gate_reasons": time_reasons or ["boundary_runtime_window_traceable"],
        "boundary_runtime_inlet_gate": inlet_gate,
        "boundary_runtime_inlet_gate_reasons": inlet_reasons or ["inlet_boundary_profile_preserved"],
        "boundary_runtime_side_top_gate": side_top_gate,
        "boundary_runtime_side_top_gate_reasons": side_top_reasons or ["side_top_boundary_profiles_preserved"],
        "boundary_runtime_side_top_normal_leakage_gate": side_top_normal_gate,
        "boundary_runtime_side_top_normal_leakage_gate_reasons": side_top_normal_reasons or ["side_top_normal_velocity_within_threshold"],
        "boundary_runtime_outlet_gate": outlet_gate,
        "boundary_runtime_outlet_gate_reasons": outlet_reasons or ["outlet_boundary_profile_preserved"],
        "boundary_runtime_profile_preservation_gate": profile_gate,
        "boundary_runtime_gate": boundary_runtime_gate,
        "boundary_runtime_gate_reasons": runtime_reasons or ["boundary_runtime_faces_preserve_af_profile"],
        "max_boundary_u_mae_ratio": max_u_mae_ratio,
        "max_boundary_negative_streamwise_fraction": max_negative_fraction,
        "max_side_top_normal_velocity_ratio": max_side_top_normal_velocity_ratio,
        "max_side_top_normal_abs_mps": max_side_top_normal_abs_mps,
        "inlet_u_mae_ratio": inlet.get("u_mae_ratio"),
        "outlet_u_mae_ratio": outlet.get("u_mae_ratio"),
        "side_top_max_u_mae_ratio": max(
            [face.get("u_mae_ratio") for face in side_top if face.get("u_mae_ratio") is not None],
            default=None,
        ),
        "faces": face_reports,
        "recommended_next_action": (
            "Use this audit on an empty-tunnel native baseline first. If inlet/side/top/outlet "
            "profile preservation fails, fix boundary treatment before interpreting AIJ probe errors."
        ),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if out_csv:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "name",
            "axis",
            "side",
            "plane_value",
            "sample_point_count",
            "valid_sample_point_count",
            "mean_streamwise_mps",
            "mean_af_u_mps",
            "u_mae_ratio",
            "u_bias_ratio",
            "negative_streamwise_fraction",
            "mean_abs_normal_velocity_ratio",
            "max_abs_normal_velocity_ratio",
            "max_abs_normal_velocity_mps",
        ]
        with out_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(face_reports)

    print(
        "boundary_runtime_gate="
        f"{boundary_runtime_gate}; inlet={inlet_gate}; side_top={side_top_gate}; "
        f"side_top_normal={side_top_normal_gate}; outlet={outlet_gate}; "
        f"max_u_mae_ratio={max_u_mae_ratio}; "
        f"max_side_top_normal_velocity_ratio={max_side_top_normal_velocity_ratio}"
    )
    return 0 if boundary_runtime_gate == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
