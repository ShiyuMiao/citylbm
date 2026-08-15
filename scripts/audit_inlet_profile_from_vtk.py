#!/usr/bin/env python3
"""Audit inlet/empty-tunnel U(z) and k(z) preservation from real VTK frames.

The script reads newly generated FluidX3D/CityLBM `u-*.vtk` files, samples one
cross-plane or inlet face, computes a time-mean streamwise profile and turbulent
kinetic energy from temporal velocity fluctuations, then compares both profiles
with an AIJ AF table. It is an evidence generator for validation_gate.py, not a
CFD runner and not a visualization shortcut.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PASS = "pass"
FAIL = "fail"
DIAGNOSTIC = "diagnostic"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare VTK-derived inlet/empty-tunnel U(z), k(z) against an AF CSV profile."
    )
    parser.add_argument("vtk_dir", help="Directory containing u-*.vtk files, or one VTK file.")
    parser.add_argument("--af-csv", required=True, help="AF profile CSV with z,U and optional k columns.")
    parser.add_argument("--out-json", required=True, help="Output audit JSON.")
    parser.add_argument("--out-csv", help="Optional per-height profile comparison CSV.")
    parser.add_argument("--metadata", help="Optional case_metadata.json for traceability.")
    parser.add_argument("--pattern", default="u-*.vtk", help="VTK glob when vtk_dir is a directory.")
    parser.add_argument("--average-last-n", type=int, default=10, help="Use last N frames.")
    parser.add_argument("--min-frames", type=int, default=10)
    parser.add_argument("--wind-direction", default="1,0,0", help="Airflow vector, e.g. 0,-1,0.")
    parser.add_argument(
        "--plane-axis",
        default="auto-inlet",
        choices=["auto-inlet", "x", "y", "z"],
        help="Plane normal axis. auto-inlet chooses dominant wind-axis inlet face.",
    )
    parser.add_argument(
        "--plane-value",
        type=float,
        default=None,
        help="Physical coordinate of the plane. Omit to use inlet face for auto-inlet.",
    )
    parser.add_argument(
        "--plane-index",
        default="nearest",
        choices=["nearest", "min", "max", "inlet", "outlet"],
        help="Plane selection when plane-value is omitted.",
    )
    parser.add_argument(
        "--plane-tolerance",
        type=float,
        default=None,
        help="Physical tolerance around plane-value. Defaults to 0.51 grid spacing along the plane axis.",
    )
    parser.add_argument("--z-bin-m", type=float, default=0.0, help="Optional fixed vertical bin height.")
    parser.add_argument("--max-u-mae-ratio", type=float, default=0.05)
    parser.add_argument("--max-k-mae-ratio", type=float, default=0.25)
    parser.add_argument(
        "--max-negative-streamwise-fraction",
        type=float,
        default=0.05,
        help="Fail when this fraction of sampled inlet velocities projects opposite to --wind-direction.",
    )
    parser.add_argument("--velocity-scale", type=float, default=1.0, help="Multiply VTK velocities by this scale.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def parse_vector(text: str) -> Tuple[float, float, float]:
    parts = [part.strip() for part in text.strip().strip("()[]{}").replace(";", ",").split(",")]
    values = [as_float(part) for part in parts if part]
    if len(values) != 3 or any(value is None for value in values):
        raise SystemExit(f"Invalid --wind-direction vector: {text}")
    length = math.sqrt(sum(float(value) * float(value) for value in values))
    if length <= 1.0e-12:
        raise SystemExit("--wind-direction cannot be zero.")
    return tuple(float(value) / length for value in values)  # type: ignore[return-value]


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def read_af_csv(path: Path) -> List[Dict[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"AF CSV has no rows: {path}")
    columns = list(rows[0].keys())
    lookup = {"".join(ch for ch in col.lower() if ch.isalnum()): col for col in columns}
    z_col = lookup.get("zm") or lookup.get("z")
    u_col = lookup.get("ums") or lookup.get("u") or lookup.get("velocity")
    k_col = lookup.get("km2s2") or lookup.get("k") or lookup.get("tke")
    if not z_col or not u_col:
        raise SystemExit("AF CSV must contain z and U columns.")
    samples: List[Dict[str, float]] = []
    for row in rows:
        z = as_float(row.get(z_col))
        u = as_float(row.get(u_col))
        k = as_float(row.get(k_col)) if k_col else None
        if z is None or u is None:
            continue
        sample = {"z": z, "u": u}
        if k is not None:
            sample["k"] = k
        samples.append(sample)
    if len(samples) < 2:
        raise SystemExit("AF CSV must contain at least two valid z/U samples.")
    samples.sort(key=lambda item: item["z"])
    return samples


def interpolate(samples: Sequence[Dict[str, float]], key: str, z: float) -> Optional[float]:
    valid = [sample for sample in samples if key in sample]
    if not valid:
        return None
    if z <= valid[0]["z"]:
        return valid[0][key]
    if z >= valid[-1]["z"]:
        return valid[-1][key]
    for a, b in zip(valid, valid[1:]):
        if a["z"] <= z <= b["z"]:
            dz = b["z"] - a["z"]
            if abs(dz) <= 1.0e-12:
                return a[key]
            t = (z - a["z"]) / dz
            return a[key] + t * (b[key] - a[key])
    return None


def discover_vtk_files(path: Path, pattern: str) -> List[Path]:
    if path.is_file():
        return [path]
    files = sorted(path.glob(pattern), key=lambda item: step_from_name(item))
    if not files:
        raise SystemExit(f"No VTK files matched {pattern} in {path}")
    return files


def select_average_window(files: Sequence[Path], average_last_n: int) -> List[Path]:
    if average_last_n > 0:
        return list(files[-average_last_n:])
    return list(files)


def step_from_name(path: Path) -> int:
    matches = re.findall(r"(\d+)", path.stem)
    return int(matches[-1]) if matches else 0


def is_strictly_increasing(values: Sequence[int]) -> bool:
    return bool(values) and all(values[i] > values[i - 1] for i in range(1, len(values)))


def has_uniform_spacing(values: Sequence[int]) -> bool:
    if not values:
        return False
    if len(values) < 3:
        return True
    spacing = values[1] - values[0]
    return spacing > 0 and all(values[i] - values[i - 1] == spacing for i in range(2, len(values)))


def is_last_window(selected_steps: Sequence[int], available_steps: Sequence[int]) -> bool:
    if not selected_steps:
        return False
    return list(selected_steps) == list(available_steps[-len(selected_steps):])


def parse_header_line(text: str, name: str, count: int) -> Optional[Tuple[float, ...]]:
    pattern = re.compile(rf"^{name}\s+(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    parts = match.group(1).strip().split()
    if len(parts) < count:
        return None
    values = [as_float(part) for part in parts[:count]]
    if any(value is None for value in values):
        return None
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def parse_ascii_vectors(after_line: str, expected_count: int) -> List[Tuple[float, float, float]]:
    parts = after_line.replace("\r", "\n").split()
    values = [as_float(part) for part in parts]
    values = [value for value in values if value is not None]
    required = expected_count * 3
    if len(values) < required:
        raise SystemExit(f"ASCII VTK vector payload too short: {len(values)} < {required}")
    return [
        (float(values[i]), float(values[i + 1]), float(values[i + 2]))
        for i in range(0, required, 3)
    ]


def parse_binary_vector_payload(payload: bytes, count: int, dtype: str) -> List[Tuple[float, float, float]]:
    item_size = 8 if dtype.lower() == "double" else 4
    required = count * 3 * item_size
    if len(payload) < required:
        raise SystemExit(f"Binary VTK vector payload too short: {len(payload)} < {required}")
    fmt = ">" + ("d" if item_size == 8 else "f") * count * 3
    values = struct.unpack(fmt, payload[:required])
    return [
        (float(values[i]), float(values[i + 1]), float(values[i + 2]))
        for i in range(0, len(values), 3)
    ]


def read_vtk_metadata(path: Path) -> Dict[str, Any]:
    with path.open("rb") as handle:
        data = handle.read(1024 * 1024)
    text = data.decode("latin1", errors="ignore")
    if "DATASET STRUCTURED_POINTS" not in text.upper() and "DATASET IMAGE_DATA" not in text.upper():
        raise SystemExit(f"Only STRUCTURED_POINTS/IMAGE_DATA VTK is supported by this audit: {path}")
    dims = parse_header_line(text, "DIMENSIONS", 3)
    origin = parse_header_line(text, "ORIGIN", 3) or (0.0, 0.0, 0.0)
    spacing = parse_header_line(text, "SPACING", 3) or (1.0, 1.0, 1.0)
    point_data = parse_header_line(text, "POINT_DATA", 1)
    if not dims:
        raise SystemExit(f"VTK DIMENSIONS missing: {path}")
    nx, ny, nz = [int(round(value)) for value in dims]
    expected_count = nx * ny * nz
    if point_data and int(round(point_data[0])) != expected_count:
        raise SystemExit(f"POINT_DATA count does not match DIMENSIONS in {path}")
    vectors_match = re.search(
        rb"\nVECTORS\s+([^\s]+)\s+(float|double)\s*\r?\n", data, re.IGNORECASE
    )
    scalars_match = re.search(
        rb"\nSCALARS\s+([^\s]+)\s+(float|double)\s+3\s*\r?\nLOOKUP_TABLE\s+[^\s]+\s*\r?\n",
        data,
        re.IGNORECASE,
    )
    if vectors_match:
        dtype = vectors_match.group(2).decode("ascii", errors="ignore")
        offset = vectors_match.end()
        field_kind = "VECTORS"
    elif scalars_match:
        dtype = scalars_match.group(2).decode("ascii", errors="ignore")
        offset = scalars_match.end()
        field_kind = "SCALARS_3"
    else:
        raise SystemExit(f"No VECTORS field or SCALARS float/double 3 field found in first 1 MB of {path}")
    binary = any(line.strip().upper() == "BINARY" for line in text.splitlines()[2:10])
    ascii_vectors = None
    if not binary:
        ascii_vectors = parse_ascii_vectors(data[offset:].decode("latin1", errors="ignore"), expected_count)
    return {
        "path": str(path),
        "dimensions": (nx, ny, nz),
        "origin": tuple(float(value) for value in origin),
        "spacing": tuple(float(value) for value in spacing),
        "binary": binary,
        "dtype": dtype,
        "field_kind": field_kind,
        "data_offset": offset,
        "ascii_vectors": ascii_vectors,
    }


def dtype_size(dtype: str) -> int:
    return 8 if dtype.lower() == "double" else 4


def read_selected_vectors(frame: Dict[str, Any], selected: Sequence[int], velocity_scale: float) -> Dict[int, Tuple[float, float, float]]:
    if frame.get("ascii_vectors") is not None:
        vectors = frame["ascii_vectors"]
        return {
            idx: tuple(component * velocity_scale for component in vectors[idx])
            for idx in selected
        }
    item_size = dtype_size(str(frame["dtype"]))
    result: Dict[int, Tuple[float, float, float]] = {}
    with Path(frame["path"]).open("rb") as handle:
        for idx in sorted(selected):
            handle.seek(int(frame["data_offset"]) + idx * 3 * item_size)
            payload = handle.read(3 * item_size)
            values = parse_binary_vector_payload(payload, 1, str(frame["dtype"]))[0]
            result[idx] = tuple(component * velocity_scale for component in values)
    return result


def axis_index(axis: str) -> int:
    return {"x": 0, "y": 1, "z": 2}[axis]


def coordinate(index: int, dims: Tuple[int, int, int], origin: Tuple[float, float, float], spacing: Tuple[float, float, float]) -> Tuple[float, float, float]:
    nx, ny, _ = dims
    i = index % nx
    j = (index // nx) % ny
    k = index // (nx * ny)
    return (
        origin[0] + i * spacing[0],
        origin[1] + j * spacing[1],
        origin[2] + k * spacing[2],
    )


def choose_axis(args: argparse.Namespace, wind: Tuple[float, float, float]) -> str:
    if args.plane_axis != "auto-inlet":
        return args.plane_axis
    dominant = max(range(3), key=lambda idx: abs(wind[idx]))
    return ["x", "y", "z"][dominant]


def select_plane_indices(
    frame: Dict[str, Any],
    axis: str,
    wind: Tuple[float, float, float],
    args: argparse.Namespace,
) -> Tuple[List[int], float, float, str]:
    dims = frame["dimensions"]
    origin = frame["origin"]
    spacing = frame["spacing"]
    ax = axis_index(axis)
    n_axis = dims[ax]
    coords = [origin[ax] + i * spacing[ax] for i in range(n_axis)]
    if args.plane_value is not None:
        value = args.plane_value
        mode = "nearest_value"
    else:
        mode = args.plane_index
        if mode == "nearest":
            mode = "inlet"
        if mode == "inlet":
            value = min(coords) if wind[ax] >= 0.0 else max(coords)
        elif mode == "outlet":
            value = max(coords) if wind[ax] >= 0.0 else min(coords)
        elif mode == "min":
            value = min(coords)
        elif mode == "max":
            value = max(coords)
        else:
            value = coords[0]
    tolerance = args.plane_tolerance
    if tolerance is None:
        tolerance = abs(spacing[ax]) * 0.51 if abs(spacing[ax]) > 1.0e-12 else 1.0e-9
    indices: List[int] = []
    for idx in range(dims[0] * dims[1] * dims[2]):
        coord = coordinate(idx, dims, origin, spacing)
        if abs(coord[ax] - value) <= tolerance:
            indices.append(idx)
    if not indices:
        raise SystemExit(
            f"No VTK points found on {axis}={value} within tolerance {tolerance}."
        )
    return indices, value, tolerance, mode


def bin_key(z: float, af_samples: Sequence[Dict[str, float]], z_bin_m: float) -> float:
    if z_bin_m > 0:
        return round(round(z / z_bin_m) * z_bin_m, 10)
    return min((sample["z"] for sample in af_samples), key=lambda value: abs(value - z))


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def mae(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(abs(value) for value in values) / len(values)


def rmse(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return math.sqrt(sum(value * value for value in values) / len(values))


def stddev(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    center = mean(values)
    if center is None:
        return None
    return math.sqrt(sum((value - center) ** 2 for value in values) / len(values))


def main() -> int:
    args = parse_args()
    vtk_path = Path(args.vtk_dir).resolve()
    af_path = Path(args.af_csv).resolve()
    out_json = Path(args.out_json).resolve()
    out_csv = Path(args.out_csv).resolve() if args.out_csv else None
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
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
    source_vtk_hashes = [record["sha256"] for record in selected_vtk_files]
    selected_last_window = is_last_window(source_steps, available_steps)
    source_steps_increasing = is_strictly_increasing(source_steps)
    source_spacing_uniform = has_uniform_spacing(source_steps)
    frames = [read_vtk_metadata(path) for path in files]
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            raise SystemExit("All VTK frames must have identical grid dimensions, origin and spacing.")

    axis = choose_axis(args, wind)
    selected, plane_value, tolerance, plane_mode = select_plane_indices(first, axis, wind, args)
    bins: Dict[float, Dict[str, Any]] = {}
    negative_streamwise = 0
    total_samples = 0
    frame_vectors = [read_selected_vectors(frame, selected, args.velocity_scale) for frame in frames]
    point_mean_speeds: List[float] = []
    point_speed_stddevs: List[float] = []
    for idx in selected:
        coord = coordinate(idx, first["dimensions"], first["origin"], first["spacing"])
        velocities = [vectors[idx] for vectors in frame_vectors]
        speed_values = [math.sqrt(sum(component * component for component in v)) for v in velocities]
        point_mean_speed = mean(speed_values)
        point_speed_stddev = stddev(speed_values)
        if point_mean_speed is not None:
            point_mean_speeds.append(point_mean_speed)
        if point_speed_stddev is not None:
            point_speed_stddevs.append(point_speed_stddev)
        streamwise_values = [sum(v[i] * wind[i] for i in range(3)) for v in velocities]
        negative_streamwise += sum(1 for value in streamwise_values if value < 0.0)
        total_samples += len(streamwise_values)
        mean_vec = tuple(mean([v[i] for v in velocities]) or 0.0 for i in range(3))
        variances = []
        for component in range(3):
            component_values = [v[component] for v in velocities]
            component_mean = mean_vec[component]
            variances.append(mean([(value - component_mean) ** 2 for value in component_values]) or 0.0)
        k_tke = 0.5 * sum(variances)
        streamwise_mean = mean(streamwise_values)
        if streamwise_mean is None:
            continue
        key = bin_key(coord[2], af_samples, args.z_bin_m)
        bucket = bins.setdefault(key, {"z_values": [], "u_values": [], "k_values": [], "count": 0})
        bucket["z_values"].append(coord[2])
        bucket["u_values"].append(streamwise_mean)
        bucket["k_values"].append(k_tke)
        bucket["count"] += 1

    rows: List[Dict[str, Any]] = []
    u_errors: List[float] = []
    k_errors: List[float] = []
    af_u_values: List[float] = []
    af_k_values: List[float] = []
    for key in sorted(bins.keys()):
        bucket = bins[key]
        z_mean = mean(bucket["z_values"])
        u_mean = mean(bucket["u_values"])
        k_mean = mean(bucket["k_values"])
        if z_mean is None or u_mean is None:
            continue
        af_u = interpolate(af_samples, "u", z_mean)
        af_k = interpolate(af_samples, "k", z_mean)
        u_error = u_mean - af_u if af_u is not None else None
        k_error = k_mean - af_k if k_mean is not None and af_k is not None else None
        if u_error is not None and af_u is not None:
            u_errors.append(u_error)
            af_u_values.append(abs(af_u))
        if k_error is not None and af_k is not None:
            k_errors.append(k_error)
            af_k_values.append(abs(af_k))
        rows.append(
            {
                "z_m": z_mean,
                "sample_count": bucket["count"],
                "U_streamwise_mean_mps": u_mean,
                "U_af_mps": af_u,
                "U_error_mps": u_error,
                "k_tke_from_time_variance_m2s2": k_mean,
                "k_af_m2s2": af_k,
                "k_error_m2s2": k_error,
            }
        )

    u_mae = mae(u_errors)
    u_rmse = rmse(u_errors)
    u_bias = mean(u_errors)
    u_den = mean(af_u_values)
    u_mae_ratio = u_mae / u_den if u_mae is not None and u_den and u_den > 1.0e-12 else None
    u_rmse_ratio = u_rmse / u_den if u_rmse is not None and u_den and u_den > 1.0e-12 else None
    u_bias_ratio = u_bias / u_den if u_bias is not None and u_den and u_den > 1.0e-12 else None
    k_mae = mae(k_errors)
    k_rmse = rmse(k_errors)
    k_bias = mean(k_errors)
    k_den = mean(af_k_values)
    k_mae_ratio = k_mae / k_den if k_mae is not None and k_den and k_den > 1.0e-12 else None
    k_rmse_ratio = k_rmse / k_den if k_rmse is not None and k_den and k_den > 1.0e-12 else None
    k_bias_ratio = k_bias / k_den if k_bias is not None and k_den and k_den > 1.0e-12 else None
    frame_count = len(frames)
    mean_speed_mps = mean(point_mean_speeds)
    mean_speed_stddev_mps = mean(point_speed_stddevs)
    max_speed_stddev_mps = max(point_speed_stddevs) if point_speed_stddevs else None
    mean_speed_stddev_ratio = (
        mean_speed_stddev_mps / mean_speed_mps
        if mean_speed_mps is not None
        and mean_speed_mps > 1.0e-12
        and mean_speed_stddev_mps is not None
        else None
    )
    max_speed_stddev_ratio = (
        max_speed_stddev_mps / mean_speed_mps
        if mean_speed_mps is not None
        and mean_speed_mps > 1.0e-12
        and max_speed_stddev_mps is not None
        else None
    )
    time_gate_reasons: List[str] = []
    if args.average_last_n <= 0:
        time_gate_reasons.append("averaging_window_not_explicit")
    if frame_count < args.min_frames:
        time_gate_reasons.append(f"averaged_frame_count_below_{args.min_frames}")
    if not selected_last_window:
        time_gate_reasons.append("not_last_available_window")
    if not source_steps_increasing:
        time_gate_reasons.append("source_steps_not_strictly_increasing")
    if not source_spacing_uniform:
        time_gate_reasons.append("source_step_spacing_not_uniform")
    time_gate = PASS if not time_gate_reasons else FAIL
    negative_streamwise_fraction = negative_streamwise / total_samples if total_samples else None
    direction_gate_reasons: List[str] = []
    if negative_streamwise_fraction is None:
        direction_gate_reasons.append("missing_negative_streamwise_fraction")
    elif negative_streamwise_fraction > args.max_negative_streamwise_fraction:
        direction_gate_reasons.append(
            f"negative_streamwise_fraction_above_{args.max_negative_streamwise_fraction:.6g}"
        )
    direction_gate = PASS if not direction_gate_reasons else FAIL
    u_gate = PASS if u_mae_ratio is not None and u_mae_ratio <= args.max_u_mae_ratio else FAIL
    k_gate = PASS if k_mae_ratio is not None and k_mae_ratio <= args.max_k_mae_ratio else FAIL
    overall = PASS if time_gate == PASS and direction_gate == PASS and u_gate == PASS and k_gate == PASS else FAIL
    if k_mae_ratio is None:
        overall = DIAGNOSTIC if time_gate == PASS and direction_gate == PASS and u_gate == PASS else FAIL

    report = {
        "schema": "citylbm.inlet_profile_audit.v1",
        "vtk_dir": str(vtk_path),
        "af_csv": str(af_path),
        "metadata": str(Path(args.metadata).resolve()) if args.metadata else "",
        "metadata_case_name": metadata.get("Name") or metadata.get("CaseName") or "",
        "vtk_files": [str(path) for path in files],
        "selected_vtk_files": selected_vtk_files,
        "source_vtk_sha256": source_vtk_hashes,
        "source_vtk_sha256_csv": ";".join(source_vtk_hashes),
        "available_frame_count": len(all_files),
        "all_available_time_steps": available_steps,
        "all_available_time_steps_csv": ",".join(str(step) for step in available_steps),
        "source_time_steps": source_steps,
        "source_time_steps_csv": ",".join(str(step) for step in source_steps),
        "source_first_time_step": source_steps[0] if source_steps else None,
        "source_last_time_step": source_steps[-1] if source_steps else None,
        "latest_available_time_step": available_steps[-1] if available_steps else None,
        "frame_count": frame_count,
        "min_frames": args.min_frames,
        "average_last_n_requested": args.average_last_n,
        "selected_last_window": selected_last_window,
        "source_steps_strictly_increasing": source_steps_increasing,
        "source_step_spacing_uniform": source_spacing_uniform,
        "wind_direction": wind,
        "plane_axis": axis,
        "plane_mode": plane_mode,
        "plane_value": plane_value,
        "plane_tolerance": tolerance,
        "selected_point_count": len(selected),
        "height_bin_count": len(rows),
        "velocity_scale": args.velocity_scale,
        "mean_speed_mps": mean_speed_mps,
        "mean_speed_stddev_mps": mean_speed_stddev_mps,
        "max_speed_stddev_mps": max_speed_stddev_mps,
        "mean_speed_stddev_ratio": mean_speed_stddev_ratio,
        "max_speed_stddev_ratio": max_speed_stddev_ratio,
        "mean_speed_statistics_source": "sampled_vtk",
        "speed_stability_point_count": len(point_speed_stddevs),
        "speed_stability_source": "selected_plane_point_speed_magnitude_final_window",
        "negative_streamwise_fraction": negative_streamwise_fraction,
        "max_negative_streamwise_fraction": args.max_negative_streamwise_fraction,
        "inlet_streamwise_direction_gate": direction_gate,
        "inlet_streamwise_direction_gate_reasons": direction_gate_reasons,
        "inlet_streamwise_direction_gate_reasons_csv": ";".join(direction_gate_reasons),
        "time_averaging_gate": time_gate,
        "time_averaging_gate_reasons": time_gate_reasons,
        "time_averaging_gate_reasons_csv": ";".join(time_gate_reasons),
        "inlet_u_profile_gate": u_gate,
        "inlet_k_profile_gate": k_gate,
        "inlet_profile_gate": overall,
        "U_MAE_mps": u_mae,
        "U_RMSE_mps": u_rmse,
        "U_bias_mps": u_bias,
        "U_MAE_ratio": u_mae_ratio,
        "U_RMSE_ratio": u_rmse_ratio,
        "U_bias_ratio": u_bias_ratio,
        "k_MAE_m2s2": k_mae,
        "k_RMSE_m2s2": k_rmse,
        "k_bias_m2s2": k_bias,
        "k_MAE_ratio": k_mae_ratio,
        "k_RMSE_ratio": k_rmse_ratio,
        "k_bias_ratio": k_bias_ratio,
        "thresholds": {
            "max_u_mae_ratio": args.max_u_mae_ratio,
            "max_k_mae_ratio": args.max_k_mae_ratio,
            "max_negative_streamwise_fraction": args.max_negative_streamwise_fraction,
        },
        "notes": (
            "k is estimated from temporal velocity variance on the selected VTK plane; "
            "this is reliable only when frames are post-spinup and uniformly spaced. "
            "Time stability ratios are computed from pointwise speed-magnitude standard deviations "
            "on the same selected final-window plane."
        ),
        "profile_rows": rows,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if out_csv:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "z_m",
            "sample_count",
            "U_streamwise_mean_mps",
            "U_af_mps",
            "U_error_mps",
            "k_tke_from_time_variance_m2s2",
            "k_af_m2s2",
            "k_error_m2s2",
        ]
        with out_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    print(
        "inlet_profile_gate={gate}; frames={frames}; points={points}; negative_streamwise_fraction={neg}; mean_speed_stddev_ratio={mean_std}; max_speed_stddev_ratio={max_std}; U_MAE_ratio={u}; U_RMSE_ratio={u_rmse}; k_MAE_ratio={k}; k_RMSE_ratio={k_rmse}".format(
            gate=overall,
            frames=frame_count,
            points=len(selected),
            neg="" if negative_streamwise_fraction is None else f"{negative_streamwise_fraction:.6g}",
            mean_std="" if mean_speed_stddev_ratio is None else f"{mean_speed_stddev_ratio:.6g}",
            max_std="" if max_speed_stddev_ratio is None else f"{max_speed_stddev_ratio:.6g}",
            u="" if u_mae_ratio is None else f"{u_mae_ratio:.6g}",
            u_rmse="" if u_rmse_ratio is None else f"{u_rmse_ratio:.6g}",
            k="" if k_mae_ratio is None else f"{k_mae_ratio:.6g}",
            k_rmse="" if k_rmse_ratio is None else f"{k_rmse_ratio:.6g}",
        )
    )
    return 0 if overall == PASS else 2


if __name__ == "__main__":
    sys.exit(main())
