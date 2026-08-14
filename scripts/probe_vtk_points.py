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
    parser.add_argument("--average-last-n", type=int, default=1, help="Average last N VTK frames before probing.")
    parser.add_argument("--probe-id-column", default="", help="Official probe ID column. Auto-detected when omitted.")
    parser.add_argument("--case", default="", help="Optional official CSV case filter, e.g. ac or CaseA.")
    parser.add_argument("--wind-direction-label", default="", help="Optional official CSV wind-direction filter, e.g. N.")
    parser.add_argument("--x-column", default="x")
    parser.add_argument("--y-column", default="y")
    parser.add_argument("--z-column", default="z")
    parser.add_argument("--wind-direction", default="1,0,0", help="Airflow vector, e.g. 0,-1,0.")
    parser.add_argument("--u-ref", type=float, required=True, help="Reference velocity for speed/streamwise ratios.")
    parser.add_argument(
        "--compared-component",
        choices=["speed_ratio", "streamwise_ratio", "speed", "streamwise_velocity", "u", "v", "w"],
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
) -> Tuple[float, float, float, float]:
    speed = math.sqrt(sum(value * value for value in velocity))
    streamwise = sum(velocity[i] * wind[i] for i in range(3))
    speed_ratio = speed / u_ref if u_ref > 0 else float("nan")
    streamwise_ratio = streamwise / u_ref if u_ref > 0 else float("nan")
    mapping = {
        "speed_ratio": speed_ratio,
        "streamwise_ratio": streamwise_ratio,
        "speed": speed,
        "streamwise_velocity": streamwise,
        "u": velocity[0],
        "v": velocity[1],
        "w": velocity[2],
    }
    return mapping[component], speed, streamwise, speed_ratio


def main() -> int:
    args = parse_args()
    vtk_paths = vtk_files(Path(args.vtk).resolve(), args.pattern, args.average_last_n)
    frames = [read_vtk_metadata(path) for path in vtk_paths]
    first = frames[0]
    for frame in frames[1:]:
        if frame["dimensions"] != first["dimensions"] or frame["origin"] != first["origin"] or frame["spacing"] != first["spacing"]:
            raise SystemExit("Selected VTK frames must share dimensions, origin and spacing.")
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
    wind = parse_vector(args.wind_direction)
    out_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(official_rows):
        probe_id = get_value(row, probe_id_col).strip()
        point_values = [as_float(get_value(row, column)) for column in [x_col, y_col, z_col]]
        if any(value is None for value in point_values):
            continue
        point = tuple(float(value) for value in point_values)  # type: ignore[assignment]
        _vtk_index, _vtk_coord, distance = nearest_index(
            point,
            first["dimensions"],
            first["origin"],
            first["spacing"],
        )
        frame_samples = [sample_frame_velocity(frame, point, args.interpolation) for frame in frames]
        velocities = [sample[0] for sample in frame_samples]
        nearby_count = max(sample[1] for sample in frame_samples) if frame_samples else 0
        mean_velocity = tuple(
            sum(velocity[axis] for velocity in velocities) / len(velocities) * args.velocity_scale
            for axis in range(3)
        )
        value, speed, streamwise, speed_ratio = compared_value(
            args.compared_component,
            mean_velocity,
            wind,
            args.u_ref,
        )
        streamwise_ratio = streamwise / args.u_ref if args.u_ref > 0 else float("nan")
        normalization_valid = args.u_ref > 0 and math.isfinite(args.u_ref)
        wind_valid = all(math.isfinite(component) for component in wind)
        out_of_tolerance = args.tolerance > 0 and distance > args.tolerance
        failed = out_of_tolerance or not math.isfinite(value)
        out_rows.append(
            {
                "probe_id": probe_id,
                "probe_index": index + 1,
                "x": point[0],
                "y": point[1],
                "z": point[2],
                "u": mean_velocity[0],
                "v": mean_velocity[1],
                "w": mean_velocity[2],
                "speed": speed,
                "wind_x": wind[0],
                "wind_y": wind[1],
                "wind_z": wind[2],
                "wind_direction_valid": "true" if wind_valid else "false",
                "streamwise_velocity": streamwise,
                "Uref": args.u_ref,
                "normalization_valid": "true" if normalization_valid else "false",
                "speed_ratio": speed_ratio,
                "streamwise_ratio": streamwise_ratio,
                "nearest_distance": distance,
                "nearby_point_count": nearby_count,
                "method": f"{args.interpolation}_vtk_average_last_{len(frames)}",
                "compared_component": args.compared_component,
                "compared_value": value,
                "tolerance": args.tolerance,
                "out_of_tolerance": "true" if out_of_tolerance else "false",
                "failed": "true" if failed else "false",
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
        "u",
        "v",
        "w",
        "speed",
        "wind_x",
        "wind_y",
        "wind_z",
        "wind_direction_valid",
        "streamwise_velocity",
        "Uref",
        "normalization_valid",
        "speed_ratio",
        "streamwise_ratio",
        "nearest_distance",
        "nearby_point_count",
        "method",
        "compared_component",
        "compared_value",
        "tolerance",
        "out_of_tolerance",
        "failed",
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
