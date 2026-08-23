#!/usr/bin/env python3
"""Extract Data-Probe-compatible audit rows from native FluidX3D/CityLBM VTK.

This script lets a native FluidX3D run enter the same validation metrics/gate
path as Grasshopper `Data Probe`. It samples official RS probe coordinates from
a VTK velocity field, records coordinate, wind-vector, Uref and component
evidence, and writes the CSV columns expected by
validation_metrics_from_probe_audit.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe native FluidX3D/CityLBM VTK velocities at official RS coordinates."
    )
    parser.add_argument("vtk", help="VTK file, or directory containing VTK files.")
    parser.add_argument("--official", required=True, help="Official RS/probe CSV with ID and x/y/z columns.")
    parser.add_argument("--out", required=True, help="Output Data-Probe-compatible CSV.")
    parser.add_argument("--pattern", default="u-*.vtk", help="VTK glob when input is a directory.")
    parser.add_argument("--average-last-n", type=int, default=40, help="Average last N VTK frames before probing.")
    parser.add_argument(
        "--min-avg-frames",
        type=int,
        default=40,
        help="Minimum selected VTK frames required before writing a validation probe audit. Use 1 only for smoke tests.",
    )
    parser.add_argument(
        "--min-avg-step-span",
        type=int,
        default=20000,
        help="Minimum solver-step span covered by the selected VTK averaging window. Use 0 only for smoke tests.",
    )
    parser.add_argument("--probe-id-column", default="", help="Official probe ID column. Auto-detected when omitted.")
    parser.add_argument("--case", default="", help="Optional official CSV case filter, e.g. ac or CaseA.")
    parser.add_argument("--wind-direction-label", default="", help="Optional official CSV wind-direction filter, e.g. N.")
    parser.add_argument(
        "--expected-row-count",
        type=int,
        default=0,
        help="Expected official rows after case/wind filtering. 0 disables the count gate.",
    )
    parser.add_argument(
        "--expected-z",
        type=float,
        default=None,
        help="Expected official probe height after case/wind filtering, e.g. 2.0 for AIJ Case E pedestrian probes.",
    )
    parser.add_argument(
        "--expected-z-tolerance",
        type=float,
        default=1.0e-6,
        help="Absolute tolerance in meters for --expected-z.",
    )
    parser.add_argument("--x-column", default="x")
    parser.add_argument("--y-column", default="y")
    parser.add_argument("--z-column", default="z")
    parser.add_argument("--wind-direction", default="1,0,0", help="Airflow vector, e.g. 0,-1,0.")
    parser.add_argument("--u-ref", type=float, required=True, help="Reference velocity for speed/streamwise ratios.")
    parser.add_argument(
        "--compared-component",
        choices=[
            "speed_ratio",
            "horizontal_speed_ratio",
            "streamwise_ratio",
            "abs_streamwise_ratio",
            "lateral_ratio",
            "speed",
            "horizontal_speed",
            "streamwise_velocity",
            "abs_streamwise_velocity",
            "lateral_velocity",
            "u",
            "v",
            "w",
        ],
        default="speed_ratio",
    )
    parser.add_argument(
        "--interpolation",
        choices=["trilinear", "nearest"],
        default="trilinear",
        help="Velocity sampling method. Trilinear is recommended for structured VTK validation.",
    )
    parser.add_argument("--tolerance", type=float, default=0.0, help="Max nearest-node distance in meters. 0 disables failure by tolerance.")
    parser.add_argument("--velocity-scale", type=float, default=1.0)
    return parser.parse_args()


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
    values = [as_float(part) for part in text.strip().strip("()[]{}").replace(";", ",").split(",") if part.strip()]
    if len(values) != 3 or any(value is None for value in values):
        raise SystemExit(f"Invalid wind vector: {text}")
    length = math.sqrt(sum(float(value) * float(value) for value in values))
    if length <= 1.0e-12:
        raise SystemExit("Wind vector cannot be zero.")
    return tuple(float(value) / length for value in values)  # type: ignore[return-value]


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
    if column in row:
        return row[column]
    target = norm_key(column)
    for key, value in row.items():
        if norm_key(key) == target:
            return value
    return ""


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def filter_official_rows(
    rows: Sequence[Dict[str, str]],
    case_name: str,
    wind_direction: str,
) -> List[Dict[str, str]]:
    selected = list(rows)
    if case_name:
        case_col = find_column(selected, ["case", "condition", "bcac"])
        if not case_col:
            raise SystemExit("Official CSV case filter requested, but no case column was detected.")
        target = case_name.strip().lower()
        selected = [row for row in selected if get_value(row, case_col).strip().lower() == target]
    if wind_direction:
        wind_col = find_column(selected, ["Wind_direction", "wind_direction", "direction", "wind"])
        if not wind_col:
            raise SystemExit("Official CSV wind-direction filter requested, but no wind-direction column was detected.")
        target = wind_direction.strip().lower()
        selected = [row for row in selected if get_value(row, wind_col).strip().lower() == target]
    if not selected:
        raise SystemExit("Official CSV filter selected no rows.")
    return selected


def official_probe_set_summary(
    rows: Sequence[Dict[str, str]],
    probe_id_col: str,
    z_col: str,
    expected_row_count: int,
    expected_z: Optional[float],
    expected_z_tolerance: float,
) -> Dict[str, Any]:
    ids: List[str] = []
    missing_ids = 0
    for row in rows:
        probe_id = get_value(row, probe_id_col).strip()
        if not probe_id:
            missing_ids += 1
            continue
        ids.append(probe_id)
    duplicate_ids = sorted({probe_id for probe_id in ids if ids.count(probe_id) > 1})
    z_match_count = 0
    z_mismatch_count = 0
    if expected_z is not None:
        for row in rows:
            z_value = as_float(get_value(row, z_col))
            if z_value is not None and abs(z_value - expected_z) <= expected_z_tolerance:
                z_match_count += 1
            else:
                z_mismatch_count += 1
    summary = {
        "official_probe_set_row_count": len(rows),
        "official_expected_row_count": expected_row_count if expected_row_count > 0 else "",
        "official_probe_ids_unique": "true" if not duplicate_ids and missing_ids == 0 else "false",
        "official_missing_probe_id_count": missing_ids,
        "official_duplicate_probe_ids": ";".join(duplicate_ids),
        "official_expected_z": expected_z if expected_z is not None else "",
        "official_expected_z_tolerance": expected_z_tolerance if expected_z is not None else "",
        "official_z_match_count": z_match_count if expected_z is not None else "",
        "official_z_mismatch_count": z_mismatch_count if expected_z is not None else "",
    }
    reasons = []
    if expected_row_count > 0 and len(rows) != expected_row_count:
        reasons.append(f"official_row_count_{len(rows)}_does_not_match_expected_{expected_row_count}")
    if missing_ids:
        reasons.append(f"missing_probe_ids:{missing_ids}")
    if duplicate_ids:
        reasons.append(f"duplicate_probe_ids:{';'.join(duplicate_ids)}")
    if expected_z is not None and z_mismatch_count:
        reasons.append(f"official_z_mismatch_count_{z_mismatch_count}")
    if reasons:
        raise SystemExit("Official probe set validation failed: " + ", ".join(reasons))
    return summary


def vtk_files(path: Path, pattern: str, average_last_n: int) -> List[Path]:
    if path.is_file():
        return [path]
    files = sorted(path.glob(pattern), key=lambda item: step_from_name(item))
    if not files:
        output_dir = path / "output"
        if output_dir.exists():
            files = sorted(output_dir.glob(pattern), key=lambda item: step_from_name(item))
    if not files:
        raise SystemExit(f"No VTK files matched {pattern} in {path}")
    if average_last_n > 0:
        files = files[-average_last_n:]
    return files


def step_from_name(path: Path) -> int:
    matches = re.findall(r"(\d+)", path.stem)
    return int(matches[-1]) if matches else 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_header_line(text: str, name: str, count: int) -> Optional[Tuple[float, ...]]:
    match = re.search(rf"^{name}\s+(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    parts = match.group(1).strip().split()
    if len(parts) < count:
        return None
    values = [as_float(part) for part in parts[:count]]
    if any(value is None for value in values):
        return None
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def parse_ascii_vectors(text: str, expected_count: int) -> List[Tuple[float, float, float]]:
    values = [as_float(part) for part in text.replace("\r", "\n").split()]
    values = [value for value in values if value is not None]
    required = expected_count * 3
    if len(values) < required:
        raise SystemExit(f"ASCII VTK payload too short: {len(values)} < {required}")
    return [
        (float(values[i]), float(values[i + 1]), float(values[i + 2]))
        for i in range(0, required, 3)
    ]


def read_vtk_metadata(path: Path) -> Dict[str, Any]:
    with path.open("rb") as handle:
        data = handle.read(1024 * 1024)
    text = data.decode("latin-1", errors="ignore")
    if "DATASET STRUCTURED_POINTS" not in text.upper() and "DATASET IMAGE_DATA" not in text.upper():
        raise SystemExit(f"Only STRUCTURED_POINTS/IMAGE_DATA VTK is supported: {path}")
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
    vectors_match = re.search(rb"\nVECTORS\s+([^\s]+)\s+(float|double)\s*\r?\n", data, re.IGNORECASE)
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
        raise SystemExit(f"No VECTORS or SCALARS float/double 3 field found in first 1 MB: {path}")
    binary = any(line.strip().upper() == "BINARY" for line in text.splitlines()[2:10])
    ascii_vectors = None
    if not binary:
        ascii_vectors = parse_ascii_vectors(
            data[offset:].decode("latin-1", errors="ignore"),
            expected_count,
        )
    return {
        "path": str(path),
        "dimensions": (nx, ny, nz),
        "origin": tuple(float(value) for value in origin),
        "spacing": tuple(float(value) for value in spacing),
        "point_count": expected_count,
        "binary": binary,
        "dtype": dtype,
        "field_kind": field_kind,
        "data_offset": offset,
        "ascii_vectors": ascii_vectors,
    }


def dtype_size(dtype: str) -> int:
    return 8 if dtype.lower() == "double" else 4


def read_vector_at_index(meta: Dict[str, Any], index: int) -> Tuple[float, float, float]:
    if meta.get("ascii_vectors") is not None:
        return meta["ascii_vectors"][index]
    item_size = dtype_size(str(meta["dtype"]))
    code = "d" if item_size == 8 else "f"
    with Path(str(meta["path"])).open("rb") as handle:
        handle.seek(int(meta["data_offset"]) + index * 3 * item_size)
        payload = handle.read(3 * item_size)
    if len(payload) != 3 * item_size:
        raise SystemExit(f"VTK vector payload ended early: {meta['path']}")
    x, y, z = struct.unpack(">" + code * 3, payload)
    return float(x), float(y), float(z)


def nearest_index(
    point: Tuple[float, float, float],
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
) -> Tuple[int, Tuple[float, float, float], float]:
    ijk = []
    for axis in range(3):
        if abs(spacing[axis]) <= 1.0e-12:
            index = 0
        else:
            index = int(round((point[axis] - origin[axis]) / spacing[axis]))
        index = max(0, min(dims[axis] - 1, index))
        ijk.append(index)
    i, j, k = ijk
    idx = i + dims[0] * (j + dims[1] * k)
    coord = (
        origin[0] + i * spacing[0],
        origin[1] + j * spacing[1],
        origin[2] + k * spacing[2],
    )
    distance = math.sqrt(sum((coord[axis] - point[axis]) ** 2 for axis in range(3)))
    return idx, coord, distance


def grid_extent(
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    lower = []
    upper = []
    for axis in range(3):
        endpoint = origin[axis] + spacing[axis] * (dims[axis] - 1)
        lower.append(min(origin[axis], endpoint))
        upper.append(max(origin[axis], endpoint))
    return (lower[0], lower[1], lower[2]), (upper[0], upper[1], upper[2])


def point_grid_extent_status(
    point: Tuple[float, float, float],
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
    tolerance: float = 1.0e-9,
) -> Tuple[bool, str, Tuple[float, float, float], Tuple[float, float, float]]:
    lower, upper = grid_extent(dims, origin, spacing)
    outside_axes = []
    for axis, label in enumerate(("x", "y", "z")):
        if point[axis] < lower[axis] - tolerance or point[axis] > upper[axis] + tolerance:
            outside_axes.append(label)
    return not outside_axes, ",".join(outside_axes), lower, upper


def clamp_cell(value: float, max_index: int) -> Tuple[int, int, float]:
    if max_index <= 0:
        return 0, 0, 0.0
    lower = int(math.floor(value))
    if lower < 0:
        return 0, 0, 0.0
    if lower >= max_index:
        return max_index, max_index, 0.0
    upper = lower + 1
    fraction = value - lower
    return lower, upper, fraction


def trilinear_indices(
    point: Tuple[float, float, float],
    dims: Tuple[int, int, int],
    origin: Tuple[float, float, float],
    spacing: Tuple[float, float, float],
) -> List[Tuple[int, float]]:
    axes = []
    for axis in range(3):
        if abs(spacing[axis]) <= 1.0e-12:
            axes.append((0, 0, 0.0))
            continue
        coordinate = (point[axis] - origin[axis]) / spacing[axis]
        axes.append(clamp_cell(coordinate, dims[axis] - 1))
    (i0, i1, fx), (j0, j1, fy), (k0, k1, fz) = axes
    weights = []
    for k, wz in [(k0, 1.0 - fz), (k1, fz)]:
        for j, wy in [(j0, 1.0 - fy), (j1, fy)]:
            for i, wx in [(i0, 1.0 - fx), (i1, fx)]:
                weight = wx * wy * wz
                if weight <= 0.0:
                    continue
                idx = i + dims[0] * (j + dims[1] * k)
                weights.append((idx, weight))
    return weights


def sample_frame_velocity(
    frame: Dict[str, Any],
    point: Tuple[float, float, float],
    interpolation: str,
) -> Tuple[Tuple[float, float, float], int]:
    if interpolation == "nearest":
        vtk_index, _coord, _distance = nearest_index(point, frame["dimensions"], frame["origin"], frame["spacing"])
        return read_vector_at_index(frame, vtk_index), 1
    weighted_indices = trilinear_indices(point, frame["dimensions"], frame["origin"], frame["spacing"])
    velocity = [0.0, 0.0, 0.0]
    for idx, weight in weighted_indices:
        vector = read_vector_at_index(frame, idx)
        for axis in range(3):
            velocity[axis] += vector[axis] * weight
    return (velocity[0], velocity[1], velocity[2]), len(weighted_indices)


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.10g}"
    return str(value)


def compared_value(
    component: str,
    velocity: Tuple[float, float, float],
    wind: Tuple[float, float, float],
    u_ref: float,
) -> Dict[str, float]:
    speed = math.sqrt(sum(value * value for value in velocity))
    streamwise = sum(velocity[i] * wind[i] for i in range(3))
    abs_streamwise = abs(streamwise)
    horizontal_speed = math.sqrt(velocity[0] * velocity[0] + velocity[1] * velocity[1])
    lateral_sq = max(0.0, speed * speed - streamwise * streamwise)
    lateral = math.sqrt(lateral_sq)
    speed_ratio = speed / u_ref if u_ref > 0 else float("nan")
    horizontal_speed_ratio = horizontal_speed / u_ref if u_ref > 0 else float("nan")
    streamwise_ratio = streamwise / u_ref if u_ref > 0 else float("nan")
    abs_streamwise_ratio = abs_streamwise / u_ref if u_ref > 0 else float("nan")
    lateral_ratio = lateral / u_ref if u_ref > 0 else float("nan")
    u_ratio = velocity[0] / u_ref if u_ref > 0 else float("nan")
    v_ratio = velocity[1] / u_ref if u_ref > 0 else float("nan")
    w_ratio = velocity[2] / u_ref if u_ref > 0 else float("nan")
    mapping = {
        "speed_ratio": speed_ratio,
        "horizontal_speed_ratio": horizontal_speed_ratio,
        "streamwise_ratio": streamwise_ratio,
        "abs_streamwise_ratio": abs_streamwise_ratio,
        "lateral_ratio": lateral_ratio,
        "speed": speed,
        "horizontal_speed": horizontal_speed,
        "streamwise_velocity": streamwise,
        "abs_streamwise_velocity": abs_streamwise,
        "lateral_velocity": lateral,
        "u": velocity[0],
        "v": velocity[1],
        "w": velocity[2],
    }
    return {
        "compared_value": mapping[component],
        "speed": speed,
        "horizontal_speed": horizontal_speed,
        "streamwise_velocity": streamwise,
        "abs_streamwise_velocity": abs_streamwise,
        "lateral_velocity": lateral,
        "speed_ratio": speed_ratio,
        "horizontal_speed_ratio": horizontal_speed_ratio,
        "streamwise_ratio": streamwise_ratio,
        "abs_streamwise_ratio": abs_streamwise_ratio,
        "lateral_ratio": lateral_ratio,
        "u_ratio": u_ratio,
        "v_ratio": v_ratio,
        "w_ratio": w_ratio,
    }


def main() -> int:
    args = parse_args()
    vtk_paths = vtk_files(Path(args.vtk).resolve(), args.pattern, args.average_last_n)
    if args.min_avg_frames > 0 and len(vtk_paths) < args.min_avg_frames:
        raise SystemExit(
            f"Selected VTK frame count {len(vtk_paths)} is below --min-avg-frames {args.min_avg_frames}. "
            "Rerun with a longer final-window average, or explicitly lower --min-avg-frames for smoke tests."
        )
    source_steps = [step_from_name(path) for path in vtk_paths]
    source_step_span: Optional[int] = source_steps[-1] - source_steps[0] if len(source_steps) >= 2 else None
    if args.min_avg_step_span > 0 and (source_step_span is None or source_step_span < args.min_avg_step_span):
        raise SystemExit(
            f"Selected VTK solver-step span {source_step_span if source_step_span is not None else 'missing'} "
            f"is below --min-avg-step-span {args.min_avg_step_span}. "
            "Rerun with a longer final-window average, or explicitly lower --min-avg-step-span for smoke tests."
        )
    frames = [read_vtk_metadata(path) for path in vtk_paths]
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            raise SystemExit("Selected VTK frames must share dimensions, origin and spacing.")
    source_steps_csv = ",".join(str(step) for step in source_steps)
    source_files_csv = ";".join(str(path) for path in vtk_paths)
    source_hashes_csv = ";".join(sha256(path) for path in vtk_paths)
    dims = first["dimensions"]
    origin = first["origin"]
    spacing = first["spacing"]
    grid_min, grid_max = grid_extent(dims, origin, spacing)
    official_rows = filter_official_rows(
        read_csv(Path(args.official).resolve()),
        args.case,
        args.wind_direction_label,
    )
    if not official_rows:
        raise SystemExit("Official CSV has no rows.")
    probe_id_col = args.probe_id_column or find_column(official_rows, ["No.", "No", "probe_id", "id", "point"])
    x_col = find_column(official_rows, [args.x_column, "x", "X"])
    y_col = find_column(official_rows, [args.y_column, "y", "Y"])
    z_col = find_column(official_rows, [args.z_column, "z", "Z"])
    if not probe_id_col:
        raise SystemExit("Could not detect probe ID column. Use --probe-id-column.")
    if not x_col or not y_col or not z_col:
        raise SystemExit("Could not detect x/y/z columns.")
    official_summary = official_probe_set_summary(
        official_rows,
        probe_id_col,
        z_col,
        args.expected_row_count,
        args.expected_z,
        args.expected_z_tolerance,
    )
    wind = parse_vector(args.wind_direction)
    out_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(official_rows):
        probe_id = get_value(row, probe_id_col).strip()
        raw_point_values = [get_value(row, column).strip() for column in [x_col, y_col, z_col]]
        point_values = [as_float(value) for value in raw_point_values]
        if any(value is None for value in point_values):
            out_rows.append(
                {
                    "probe_id": probe_id,
                    "probe_index": index + 1,
                    "x": raw_point_values[0],
                    "y": raw_point_values[1],
                    "z": raw_point_values[2],
                    "official_x": raw_point_values[0],
                    "official_y": raw_point_values[1],
                    "official_z": raw_point_values[2],
                    "official_coordinate_delta": "",
                    **official_summary,
                    "u": "",
                    "v": "",
                    "w": "",
                    "speed": "",
                    "horizontal_speed": "",
                    "wind_x": wind[0],
                    "wind_y": wind[1],
                    "wind_z": wind[2],
                    "wind_direction_valid": "true",
                    "streamwise_velocity": "",
                    "abs_streamwise_velocity": "",
                    "lateral_velocity": "",
                    "Uref": args.u_ref,
                    "normalization_valid": "true" if args.u_ref > 0 and math.isfinite(args.u_ref) else "false",
                    "speed_ratio": "",
                    "horizontal_speed_ratio": "",
                    "streamwise_ratio": "",
                    "abs_streamwise_ratio": "",
                    "lateral_ratio": "",
                    "u_ratio": "",
                    "v_ratio": "",
                    "w_ratio": "",
                    "nearest_distance": "",
                    "nearest_grid_x": "",
                    "nearest_grid_y": "",
                    "nearest_grid_z": "",
                    "nearby_point_count": 0,
                    "method": f"{args.interpolation}_vtk_average_last_{len(frames)}",
                    "vtk_average_frame_count": len(frames),
                    "vtk_source_time_steps": source_steps_csv,
                    "vtk_source_step_span": source_step_span if source_step_span is not None else "",
                    "minimum_validation_average_step_span": args.min_avg_step_span,
                    "vtk_dimensions": f"{dims[0]},{dims[1]},{dims[2]}",
                    "vtk_origin_x": origin[0],
                    "vtk_origin_y": origin[1],
                    "vtk_origin_z": origin[2],
                    "vtk_spacing_x": spacing[0],
                    "vtk_spacing_y": spacing[1],
                    "vtk_spacing_z": spacing[2],
                    "vtk_grid_min_x": grid_min[0],
                    "vtk_grid_min_y": grid_min[1],
                    "vtk_grid_min_z": grid_min[2],
                    "vtk_grid_max_x": grid_max[0],
                    "vtk_grid_max_y": grid_max[1],
                    "vtk_grid_max_z": grid_max[2],
                    "inside_vtk_grid_extent": "false",
                    "outside_vtk_grid_axes": "invalid_coordinate",
                    "vtk_source_files": source_files_csv,
                    "vtk_source_sha256": source_hashes_csv,
                    "compared_component": args.compared_component,
                    "component_projection_basis": "speed_or_velocity_dot_airflow_unit_vector",
                    "compared_value": "",
                    "tolerance": args.tolerance,
                    "out_of_tolerance": "false",
                    "failed": "true",
                    "failure_reason": "invalid_probe_coordinate",
                }
            )
            continue
        official_point = tuple(float(value) for value in point_values)
        point = official_point
        official_coordinate_delta = 0.0
        _vtk_index, vtk_coord, distance = nearest_index(
            point,
            dims,
            origin,
            spacing,
        )
        inside_grid, outside_axes, point_grid_min, point_grid_max = point_grid_extent_status(
            point,
            dims,
            origin,
            spacing,
        )
        frame_samples = [sample_frame_velocity(frame, point, args.interpolation) for frame in frames]
        velocities = [sample[0] for sample in frame_samples]
        nearby_count = max(sample[1] for sample in frame_samples) if frame_samples else 0
        mean_velocity = tuple(
            sum(velocity[axis] for velocity in velocities) / len(velocities) * args.velocity_scale
            for axis in range(3)
        )
        component_values = compared_value(
            args.compared_component,
            mean_velocity,
            wind,
            args.u_ref,
        )
        value = component_values["compared_value"]
        normalization_valid = args.u_ref > 0 and math.isfinite(args.u_ref)
        wind_valid = all(math.isfinite(component) for component in wind)
        out_of_tolerance = args.tolerance > 0 and distance > args.tolerance
        failed = not inside_grid or out_of_tolerance or not math.isfinite(value)
        failure_reason = ""
        if not inside_grid:
            failure_reason = f"outside_vtk_grid_extent:{outside_axes}"
        elif out_of_tolerance:
            failure_reason = "out_of_tolerance"
        elif not math.isfinite(value):
            failure_reason = "invalid_compared_value"
        out_rows.append(
            {
                "probe_id": probe_id,
                "probe_index": index + 1,
                "x": point[0],
                "y": point[1],
                "z": point[2],
                "official_x": official_point[0],
                "official_y": official_point[1],
                "official_z": official_point[2],
                "official_coordinate_delta": official_coordinate_delta,
                **official_summary,
                "u": mean_velocity[0],
                "v": mean_velocity[1],
                "w": mean_velocity[2],
                "speed": component_values["speed"],
                "horizontal_speed": component_values["horizontal_speed"],
                "wind_x": wind[0],
                "wind_y": wind[1],
                "wind_z": wind[2],
                "wind_direction_valid": "true" if wind_valid else "false",
                "streamwise_velocity": component_values["streamwise_velocity"],
                "abs_streamwise_velocity": component_values["abs_streamwise_velocity"],
                "lateral_velocity": component_values["lateral_velocity"],
                "Uref": args.u_ref,
                "normalization_valid": "true" if normalization_valid else "false",
                "speed_ratio": component_values["speed_ratio"],
                "horizontal_speed_ratio": component_values["horizontal_speed_ratio"],
                "streamwise_ratio": component_values["streamwise_ratio"],
                "abs_streamwise_ratio": component_values["abs_streamwise_ratio"],
                "lateral_ratio": component_values["lateral_ratio"],
                "u_ratio": component_values["u_ratio"],
                "v_ratio": component_values["v_ratio"],
                "w_ratio": component_values["w_ratio"],
                "nearest_distance": distance,
                "nearest_grid_x": vtk_coord[0],
                "nearest_grid_y": vtk_coord[1],
                "nearest_grid_z": vtk_coord[2],
                "nearby_point_count": nearby_count,
                "method": f"{args.interpolation}_vtk_average_last_{len(frames)}",
                "vtk_average_frame_count": len(frames),
                "vtk_source_time_steps": source_steps_csv,
                "vtk_source_step_span": source_step_span if source_step_span is not None else "",
                "minimum_validation_average_step_span": args.min_avg_step_span,
                "vtk_dimensions": f"{dims[0]},{dims[1]},{dims[2]}",
                "vtk_origin_x": origin[0],
                "vtk_origin_y": origin[1],
                "vtk_origin_z": origin[2],
                "vtk_spacing_x": spacing[0],
                "vtk_spacing_y": spacing[1],
                "vtk_spacing_z": spacing[2],
                "vtk_grid_min_x": point_grid_min[0],
                "vtk_grid_min_y": point_grid_min[1],
                "vtk_grid_min_z": point_grid_min[2],
                "vtk_grid_max_x": point_grid_max[0],
                "vtk_grid_max_y": point_grid_max[1],
                "vtk_grid_max_z": point_grid_max[2],
                "inside_vtk_grid_extent": "true" if inside_grid else "false",
                "outside_vtk_grid_axes": outside_axes,
                "vtk_source_files": source_files_csv,
                "vtk_source_sha256": source_hashes_csv,
                "compared_component": args.compared_component,
                "component_projection_basis": "speed_or_velocity_dot_airflow_unit_vector",
                "compared_value": value,
                "tolerance": args.tolerance,
                "out_of_tolerance": "true" if out_of_tolerance else "false",
                "failed": "true" if failed else "false",
                "failure_reason": failure_reason,
            }
        )
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "probe_id",
        "probe_index",
        "x",
        "y",
        "z",
        "official_x",
        "official_y",
        "official_z",
        "official_coordinate_delta",
        "official_probe_set_row_count",
        "official_expected_row_count",
        "official_probe_ids_unique",
        "official_missing_probe_id_count",
        "official_duplicate_probe_ids",
        "official_expected_z",
        "official_expected_z_tolerance",
        "official_z_match_count",
        "official_z_mismatch_count",
        "u",
        "v",
        "w",
        "speed",
        "horizontal_speed",
        "wind_x",
        "wind_y",
        "wind_z",
        "wind_direction_valid",
        "streamwise_velocity",
        "abs_streamwise_velocity",
        "lateral_velocity",
        "Uref",
        "normalization_valid",
        "speed_ratio",
        "horizontal_speed_ratio",
        "streamwise_ratio",
        "abs_streamwise_ratio",
        "lateral_ratio",
        "u_ratio",
        "v_ratio",
        "w_ratio",
        "nearest_distance",
        "nearest_grid_x",
        "nearest_grid_y",
        "nearest_grid_z",
        "nearby_point_count",
        "method",
        "vtk_average_frame_count",
        "vtk_source_time_steps",
        "vtk_source_step_span",
        "minimum_validation_average_step_span",
        "vtk_dimensions",
        "vtk_origin_x",
        "vtk_origin_y",
        "vtk_origin_z",
        "vtk_spacing_x",
        "vtk_spacing_y",
        "vtk_spacing_z",
        "vtk_grid_min_x",
        "vtk_grid_min_y",
        "vtk_grid_min_z",
        "vtk_grid_max_x",
        "vtk_grid_max_y",
        "vtk_grid_max_z",
        "inside_vtk_grid_extent",
        "outside_vtk_grid_axes",
        "vtk_source_files",
        "vtk_source_sha256",
        "compared_component",
        "component_projection_basis",
        "compared_value",
        "tolerance",
        "out_of_tolerance",
        "failed",
        "failure_reason",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in out_rows:
            writer.writerow({field: fmt(row.get(field)) for field in fields})
    failed_count = sum(1 for row in out_rows if row["failed"] == "true")
    print(
        f"Wrote probe audit: {out_path}; probes={len(out_rows)}; failed={failed_count}; frames={len(frames)}"
    )
    return 2 if failed_count else 0


if __name__ == "__main__":
    sys.exit(main())
