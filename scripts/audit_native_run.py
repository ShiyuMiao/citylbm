#!/usr/bin/env python3
"""Create a machine-readable audit for a native FluidX3D validation run.

The script does not run CFD and does not judge AIJ accuracy. It inspects a run
directory after the solver has produced files and emits a JSON record that can
be passed to validation_metrics_from_probe_audit.py as --read-vtk-audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


RISK_PATTERNS = [
    ("nan", re.compile(r"\bnan\b", re.IGNORECASE)),
    ("inf", re.compile(r"\binf(?:inity)?\b", re.IGNORECASE)),
    ("diverg", re.compile(r"diverg", re.IGNORECASE)),
    ("unstable", re.compile(r"unstable", re.IGNORECASE)),
    ("instability", re.compile(r"instability", re.IGNORECASE)),
    ("blow up", re.compile(r"blow\s+up", re.IGNORECASE)),
    ("blow-up", re.compile(r"blow-up", re.IGNORECASE)),
    ("overflow", re.compile(r"overflow", re.IGNORECASE)),
    ("cuda error", re.compile(r"cuda\s+error", re.IGNORECASE)),
    ("opencl error", re.compile(r"opencl\s+error", re.IGNORECASE)),
    ("segmentation fault", re.compile(r"segmentation\s+fault", re.IGNORECASE)),
    ("exception", re.compile(r"exception", re.IGNORECASE)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit native FluidX3D VTK frames and solver log evidence."
    )
    parser.add_argument("run_dir", help="Native FluidX3D case/output directory.")
    parser.add_argument("--metadata", help="Optional case_metadata.json to copy stability settings from.")
    parser.add_argument("--solver-log", help="Optional solver stdout/stderr log path.")
    parser.add_argument("--out", required=True, help="Output audit JSON path.")
    parser.add_argument("--average-last-n", type=int, default=10)
    parser.add_argument("--min-avg-frames", type=int, default=10)
    parser.add_argument("--time-steps", type=int, default=None, help="Planned solver time steps for run-configuration frame-count preflight.")
    parser.add_argument("--vtk-save-interval", type=int, default=None, help="Planned VTK save interval for run-configuration frame-count preflight.")
    parser.add_argument("--vtk-save-start-step", type=int, default=None, help="First planned VTK save step. Defaults to save interval when omitted.")
    parser.add_argument("--max-mean-speed-stddev-ratio", type=float, default=0.05)
    parser.add_argument("--max-point-speed-stddev-ratio", type=float, default=0.20)
    parser.add_argument("--mean-speed-mps", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-mps", type=float, default=None)
    parser.add_argument("--max-speed-stddev-mps", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--max-speed-stddev-ratio", type=float, default=None)
    parser.add_argument(
        "--vtk-stability-sample-limit",
        type=int,
        default=20000,
        help="Maximum deterministic VTK points sampled for automatic time-stability statistics. Set 0 to disable.",
    )
    return parser.parse_args()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def extract_time_step(path: Path) -> Optional[int]:
    matches = re.findall(r"\d+", path.stem)
    if not matches:
        return None
    return int(matches[-1])


def find_vtk_files(run_dir: Path) -> List[Path]:
    candidates = list(run_dir.glob("*.vtk"))
    output_dir = run_dir / "output"
    if output_dir.exists():
        candidates.extend(output_dir.glob("*.vtk"))
    unique = {str(path.resolve()).lower(): path for path in candidates}
    return sorted(unique.values(), key=lambda p: (extract_time_step(p) is None, extract_time_step(p) or 0, p.name))


def find_reference_file(run_dir: Path, name: str) -> Optional[Path]:
    candidates = [
        run_dir / name,
        run_dir / "src" / name,
        run_dir / "input" / name,
        run_dir / "output" / name,
    ]
    return next((path.resolve() for path in candidates if path.exists()), None)


def run_freshness_audit(
    run_dir: Path,
    metadata_path: Optional[Path],
    selected_vtk_files: Sequence[Path],
) -> Dict[str, Any]:
    references: Dict[str, Path] = {}
    if metadata_path and metadata_path.exists():
        references["case_metadata.json"] = metadata_path.resolve()
    for name in ["setup.cpp", "defines.hpp", "buildings.stl", "domain_origin.json"]:
        found = find_reference_file(run_dir, name)
        if found is not None:
            references[name] = found

    reference_records = [
        {
            "role": role,
            "path": str(path),
            "mtime_utc": mtime_utc(path),
            "sha256": sha256(path),
        }
        for role, path in sorted(references.items())
    ]
    vtk_records = [
        {
            "path": str(path.resolve()),
            "time_step": extract_time_step(path),
            "mtime_utc": mtime_utc(path),
            "sha256": sha256(path),
        }
        for path in selected_vtk_files
    ]
    reference_mtimes = [path.stat().st_mtime for path in references.values()]
    vtk_mtimes = [path.stat().st_mtime for path in selected_vtk_files]
    reasons: List[str] = []
    if not selected_vtk_files:
        reasons.append("selected_vtk_files_missing")
    if not references:
        reasons.append("freshness_reference_artifacts_missing")
    if reference_mtimes and vtk_mtimes:
        latest_reference_mtime = max(reference_mtimes)
        stale = [
            str(path.resolve())
            for path in selected_vtk_files
            if path.stat().st_mtime < latest_reference_mtime
        ]
        if stale:
            reasons.append("selected_vtk_older_than_latest_reference:" + ";".join(stale))
    return {
        "run_freshness_gate": "pass" if not reasons else "diagnostic_only",
        "run_freshness_gate_reasons": reasons,
        "run_freshness_gate_reasons_csv": ";".join(reasons),
        "freshness_reference_files": reference_records,
        "freshness_selected_vtk_files": vtk_records,
        "latest_reference_mtime_utc": max((record["mtime_utc"] for record in reference_records), default=""),
        "oldest_selected_vtk_mtime_utc": min((record["mtime_utc"] for record in vtk_records), default=""),
    }


def is_strictly_increasing(values: List[int]) -> bool:
    return bool(values) and all(values[i] > values[i - 1] for i in range(1, len(values)))


def has_uniform_spacing(values: List[int]) -> bool:
    if not values:
        return False
    if len(values) < 3:
        return True
    spacing = values[1] - values[0]
    return spacing > 0 and all(values[i] - values[i - 1] == spacing for i in range(2, len(values)))


def parse_header_line(text: str, name: str, count: int) -> Optional[Tuple[float, ...]]:
    pattern = re.compile(rf"^{name}\s+(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    parts = match.group(1).strip().split()
    if len(parts) < count:
        return None
    values: List[float] = []
    for part in parts[:count]:
        try:
            values.append(float(part))
        except ValueError:
            return None
    return tuple(values)


def parse_vtk_metadata(path: Path) -> Dict[str, Any]:
    with path.open("rb") as handle:
        data = handle.read(1024 * 1024)
    text = data.decode("latin-1", errors="ignore")
    dims = parse_header_line(text, "DIMENSIONS", 3)
    point_data = parse_header_line(text, "POINT_DATA", 1)
    if not dims:
        raise ValueError(f"VTK DIMENSIONS missing: {path}")
    nx, ny, nz = [int(round(value)) for value in dims]
    count = nx * ny * nz
    if point_data and int(round(point_data[0])) != count:
        raise ValueError(f"POINT_DATA count does not match DIMENSIONS: {path}")
    vectors_match = re.search(
        rb"\nVECTORS\s+([^\s]+)\s+(float|double)\s*\r?\n",
        data,
        re.IGNORECASE,
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
        raise ValueError(f"No VECTORS or SCALARS float/double 3 field found: {path}")
    binary = any(line.strip().upper() == "BINARY" for line in text.splitlines()[2:10])
    return {
        "path": str(path),
        "dimensions": [nx, ny, nz],
        "point_count": count,
        "binary": binary,
        "dtype": dtype,
        "field_kind": field_kind,
        "data_offset": offset,
    }


def dtype_size(dtype: str) -> int:
    return 8 if dtype.lower() == "double" else 4


def selected_sample_indices(point_count: int, sample_limit: int) -> List[int]:
    if point_count <= 0 or sample_limit <= 0:
        return []
    if point_count <= sample_limit:
        return list(range(point_count))
    if sample_limit == 1:
        return [point_count // 2]
    return sorted({round(i * (point_count - 1) / (sample_limit - 1)) for i in range(sample_limit)})


def parse_ascii_vectors(text: str, expected_count: int) -> List[Tuple[float, float, float]]:
    parts = text.replace("\r", "\n").split()
    values: List[float] = []
    for part in parts:
        try:
            values.append(float(part))
        except ValueError:
            continue
    required = expected_count * 3
    if len(values) < required:
        raise ValueError(f"ASCII VTK vector payload too short: {len(values)} < {required}")
    return [
        (values[i], values[i + 1], values[i + 2])
        for i in range(0, required, 3)
    ]


def read_vectors_at_indices(meta: Dict[str, Any], indices: Sequence[int]) -> List[Tuple[float, float, float]]:
    path = Path(str(meta["path"]))
    if not bool(meta["binary"]):
        data = path.read_bytes()
        vectors = parse_ascii_vectors(
            data[int(meta["data_offset"]) :].decode("latin-1", errors="ignore"),
            int(meta["point_count"]),
        )
        return [vectors[index] for index in indices]
    item_size = dtype_size(str(meta["dtype"]))
    unpack_code = "d" if item_size == 8 else "f"
    vectors: List[Tuple[float, float, float]] = []
    with path.open("rb") as handle:
        for index in indices:
            handle.seek(int(meta["data_offset"]) + index * 3 * item_size)
            payload = handle.read(3 * item_size)
            if len(payload) != 3 * item_size:
                raise ValueError(f"VTK vector payload ended early: {path}")
            x, y, z = struct.unpack(">" + unpack_code * 3, payload)
            vectors.append((float(x), float(y), float(z)))
    return vectors


def compute_sampled_vtk_stability(
    selected_paths: Sequence[Path],
    sample_limit: int,
) -> Dict[str, Any]:
    if sample_limit <= 0:
        return {"vtk_stability_sampling_enabled": False}
    if len(selected_paths) < 2:
        return {
            "vtk_stability_sampling_enabled": True,
            "vtk_stability_sampling_gate": "insufficient_frames",
            "vtk_stability_sampling_error": "at least two frames are required",
        }
    try:
        metas = [parse_vtk_metadata(path) for path in selected_paths]
        first = metas[0]
        for meta in metas[1:]:
            if meta["dimensions"] != first["dimensions"] or meta["point_count"] != first["point_count"]:
                raise ValueError("selected VTK frames do not share dimensions/point count")
        indices = selected_sample_indices(int(first["point_count"]), sample_limit)
        frame_vectors = [read_vectors_at_indices(meta, indices) for meta in metas]
        point_stddevs: List[float] = []
        point_means: List[float] = []
        for point_index in range(len(indices)):
            speeds = [
                math.sqrt(
                    frame[point_index][0] * frame[point_index][0]
                    + frame[point_index][1] * frame[point_index][1]
                    + frame[point_index][2] * frame[point_index][2]
                )
                for frame in frame_vectors
            ]
            mean_speed = sum(speeds) / len(speeds)
            variance = sum((speed - mean_speed) ** 2 for speed in speeds) / len(speeds)
            point_means.append(mean_speed)
            point_stddevs.append(math.sqrt(variance))
        mean_speed_mps = sum(point_means) / len(point_means) if point_means else None
        mean_speed_stddev_mps = sum(point_stddevs) / len(point_stddevs) if point_stddevs else None
        max_speed_stddev_mps = max(point_stddevs) if point_stddevs else None
        mean_ratio = (
            mean_speed_stddev_mps / mean_speed_mps
            if mean_speed_mps and mean_speed_mps > 1.0e-12 and mean_speed_stddev_mps is not None
            else None
        )
        max_ratio = (
            max_speed_stddev_mps / mean_speed_mps
            if mean_speed_mps and mean_speed_mps > 1.0e-12 and max_speed_stddev_mps is not None
            else None
        )
        return {
            "vtk_stability_sampling_enabled": True,
            "vtk_stability_sampling_gate": "sampled",
            "vtk_stability_sample_limit": sample_limit,
            "vtk_stability_sample_count": len(indices),
            "vtk_stability_field_kind": first["field_kind"],
            "vtk_stability_dtype": first["dtype"],
            "mean_speed_mps": mean_speed_mps,
            "mean_speed_stddev_mps": mean_speed_stddev_mps,
            "max_speed_stddev_mps": max_speed_stddev_mps,
            "mean_speed_stddev_ratio": mean_ratio,
            "max_speed_stddev_ratio": max_ratio,
        }
    except Exception as exc:
        return {
            "vtk_stability_sampling_enabled": True,
            "vtk_stability_sampling_gate": "failed",
            "vtk_stability_sampling_error": str(exc),
        }


def read_text_lossy(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def audit_solver_log(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {
            "solver_log_found": False,
            "solver_stability_warnings": "missing_solver_log",
            "lbm_stability_gate": "missing_solver_log",
            "solver_warning_matches": [],
        }
    text = read_text_lossy(path)
    matches = [label for label, pattern in RISK_PATTERNS if pattern.search(text)]
    return {
        "solver_log_found": True,
        "solver_log_path": str(path),
        "solver_log_sha256": sha256(path),
        "solver_stability_warnings": "none" if not matches else ";".join(matches),
        "lbm_stability_gate": "solver_log_no_stability_warnings" if not matches else "solver_log_stability_warnings",
        "solver_warning_matches": matches,
    }


def finite(value: Optional[float]) -> bool:
    return value is not None and not math.isnan(value) and not math.isinf(value)


def metadata_value(metadata: Dict[str, Any], key: str) -> Any:
    value = metadata.get(key)
    return "" if value is None else value


def metadata_int(metadata: Dict[str, Any], *keys: str) -> Optional[int]:
    for key in keys:
        value = metadata.get(key)
        if value in (None, ""):
            continue
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            continue
    return None


def expected_vtk_frame_preflight(
    metadata: Dict[str, Any],
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int],
    min_avg_frames: int,
) -> Dict[str, Any]:
    requested_time_steps = (
        time_steps
        if time_steps is not None
        else metadata_int(metadata, "TimeSteps", "Steps", "SimulationTimeSteps")
    )
    requested_save_interval = (
        save_interval
        if save_interval is not None
        else metadata_int(metadata, "VtkSaveInterval", "SaveInterval", "VTKSaveInterval")
    )
    requested_save_start = (
        save_start_step
        if save_start_step is not None
        else metadata_int(metadata, "VtkSaveStartStep", "VtkSaveStart", "VTKSaveStartStep")
    )
    metadata_expected = metadata_int(metadata, "ExpectedVtkFrameCount", "ExpectedFinalVtkFrameCount")
    reasons: List[str] = []
    expected_steps: List[int] = []
    if requested_time_steps is None:
        reasons.append("requested_time_steps_missing")
    if requested_save_interval is None:
        reasons.append("requested_vtk_save_interval_missing")
    elif requested_save_interval <= 0:
        reasons.append("requested_vtk_save_interval_non_positive")
    if requested_time_steps is not None and requested_save_interval is not None and requested_save_interval > 0:
        start = requested_save_start if requested_save_start is not None else requested_save_interval
        if start < 0:
            reasons.append("requested_vtk_save_start_step_negative")
        elif start > requested_time_steps:
            reasons.append("requested_vtk_save_start_after_time_steps")
        else:
            expected_steps = list(range(start, requested_time_steps + 1, requested_save_interval))
    expected_count = len(expected_steps) if expected_steps else metadata_expected
    if expected_count is None:
        reasons.append("requested_vtk_frame_count_unavailable")
    elif expected_count < min_avg_frames:
        reasons.append(f"requested_vtk_frame_count_below_{min_avg_frames}")
    return {
        "requested_time_steps": requested_time_steps,
        "requested_vtk_save_interval": requested_save_interval,
        "requested_vtk_save_start_step": requested_save_start,
        "requested_vtk_frame_count": expected_count,
        "requested_vtk_expected_time_steps": expected_steps,
        "requested_vtk_expected_time_steps_csv": ",".join(str(step) for step in expected_steps),
        "metadata_expected_vtk_frame_count": metadata_expected,
        "requested_vtk_frame_gate": "pass" if not reasons else "diagnostic_only",
        "requested_vtk_frame_gate_reasons": reasons,
        "requested_vtk_frame_gate_reasons_csv": ";".join(reasons),
    }


def build_audit(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    metadata_path = Path(args.metadata).resolve() if args.metadata else None
    metadata = read_json(metadata_path)
    vtk_files = find_vtk_files(run_dir)
    steps = [extract_time_step(path) for path in vtk_files]
    known_steps = sorted(step for step in steps if step is not None)
    selected_steps = known_steps[-args.average_last_n :] if args.average_last_n > 0 else []
    selected_last_window = bool(selected_steps) and selected_steps == known_steps[-len(selected_steps) :]
    increasing = is_strictly_increasing(selected_steps)
    uniform = has_uniform_spacing(selected_steps)
    selected_step_set = set(selected_steps)
    selected_vtk_files = [
        path
        for path in vtk_files
        if extract_time_step(path) in selected_step_set
    ]
    sampled_stability = compute_sampled_vtk_stability(
        selected_vtk_files,
        args.vtk_stability_sample_limit,
    )
    freshness_audit = run_freshness_audit(run_dir, metadata_path, selected_vtk_files)
    mean_speed_mps = (
        args.mean_speed_mps
        if args.mean_speed_mps is not None
        else sampled_stability.get("mean_speed_mps")
    )
    mean_speed_stddev_mps = (
        args.mean_speed_stddev_mps
        if args.mean_speed_stddev_mps is not None
        else sampled_stability.get("mean_speed_stddev_mps")
    )
    max_speed_stddev_mps = (
        args.max_speed_stddev_mps
        if args.max_speed_stddev_mps is not None
        else sampled_stability.get("max_speed_stddev_mps")
    )
    mean_speed_stddev_ratio = (
        args.mean_speed_stddev_ratio
        if args.mean_speed_stddev_ratio is not None
        else sampled_stability.get("mean_speed_stddev_ratio")
    )
    max_speed_stddev_ratio = (
        args.max_speed_stddev_ratio
        if args.max_speed_stddev_ratio is not None
        else sampled_stability.get("max_speed_stddev_ratio")
    )
    mean_speed_statistics_source = (
        "cli"
        if args.mean_speed_stddev_ratio is not None and args.max_speed_stddev_ratio is not None
        else "sampled_vtk"
    )

    reasons: List[str] = []
    if args.average_last_n <= 0:
        reasons.append("averaging_disabled")
    if len(selected_steps) < args.min_avg_frames:
        reasons.append(f"averaged_frame_count_below_{args.min_avg_frames}")
    if not selected_last_window:
        reasons.append("not_last_available_window")
    if not increasing:
        reasons.append("source_steps_not_strictly_increasing")
    if not uniform:
        reasons.append("source_step_spacing_not_uniform")
    if not finite(mean_speed_stddev_ratio):
        reasons.append("missing_mean_speed_stddev_ratio")
    elif float(mean_speed_stddev_ratio) > args.max_mean_speed_stddev_ratio:
        reasons.append("mean_speed_stddev_ratio_above_0.05")
    if not finite(max_speed_stddev_ratio):
        reasons.append("missing_max_speed_stddev_ratio")
    elif float(max_speed_stddev_ratio) > args.max_point_speed_stddev_ratio:
        reasons.append("max_speed_stddev_ratio_above_0.20")
    if sampled_stability.get("vtk_stability_sampling_gate") == "failed":
        reasons.append("vtk_stability_sampling_failed")
    if mean_speed_statistics_source != "sampled_vtk":
        reasons.append("mean_speed_statistics_not_from_sampled_vtk")

    requested_frame_preflight = expected_vtk_frame_preflight(
        metadata,
        args.time_steps,
        args.vtk_save_interval,
        args.vtk_save_start_step,
        args.min_avg_frames,
    )
    if requested_frame_preflight["requested_vtk_frame_gate"] != "pass":
        reasons.append("requested_vtk_frame_preflight_not_pass")

    log_audit = audit_solver_log(Path(args.solver_log).resolve() if args.solver_log else None)
    audit: Dict[str, Any] = {
        "schema_version": 1,
        "component": "Native FluidX3D run audit",
        "run_dir": str(run_dir),
        "average_last_n_requested": args.average_last_n,
        "averaging_enabled": args.average_last_n > 0,
        "averaged_frame_count": len(selected_steps),
        "available_frame_count": len(known_steps),
        "requested_time_steps": requested_frame_preflight["requested_time_steps"],
        "requested_vtk_save_interval": requested_frame_preflight["requested_vtk_save_interval"],
        "requested_vtk_save_start_step": requested_frame_preflight["requested_vtk_save_start_step"],
        "requested_vtk_frame_count": requested_frame_preflight["requested_vtk_frame_count"],
        "requested_vtk_expected_time_steps": requested_frame_preflight["requested_vtk_expected_time_steps"],
        "requested_vtk_expected_time_steps_csv": requested_frame_preflight["requested_vtk_expected_time_steps_csv"],
        "metadata_expected_vtk_frame_count": requested_frame_preflight["metadata_expected_vtk_frame_count"],
        "requested_vtk_frame_gate": requested_frame_preflight["requested_vtk_frame_gate"],
        "requested_vtk_frame_gate_reasons": requested_frame_preflight["requested_vtk_frame_gate_reasons"],
        "requested_vtk_frame_gate_reasons_csv": requested_frame_preflight["requested_vtk_frame_gate_reasons_csv"],
        "all_available_time_steps": known_steps,
        "all_available_time_steps_csv": ",".join(str(step) for step in known_steps),
        "source_time_steps": selected_steps,
        "source_time_steps_csv": ",".join(str(step) for step in selected_steps),
        "source_first_time_step": selected_steps[0] if selected_steps else None,
        "source_last_time_step": selected_steps[-1] if selected_steps else None,
        "latest_available_time_step": known_steps[-1] if known_steps else None,
        "selected_last_window": selected_last_window,
        "source_steps_strictly_increasing": increasing,
        "source_step_spacing_uniform": uniform,
        "mean_speed_mps": mean_speed_mps,
        "mean_speed_stddev_mps": mean_speed_stddev_mps,
        "max_speed_stddev_mps": max_speed_stddev_mps,
        "mean_speed_stddev_ratio": mean_speed_stddev_ratio,
        "max_speed_stddev_ratio": max_speed_stddev_ratio,
        "mean_speed_statistics_source": mean_speed_statistics_source,
        "minimum_validation_average_frames": args.min_avg_frames,
        "max_mean_speed_stddev_ratio": args.max_mean_speed_stddev_ratio,
        "max_point_speed_stddev_ratio": args.max_point_speed_stddev_ratio,
        "time_averaging_gate": "pass" if not reasons else "diagnostic_only",
        "time_averaging_gate_reasons": reasons,
        "time_averaging_gate_reasons_csv": ";".join(reasons),
        "run_freshness_gate": freshness_audit["run_freshness_gate"],
        "run_freshness_gate_reasons": freshness_audit["run_freshness_gate_reasons"],
        "run_freshness_gate_reasons_csv": freshness_audit["run_freshness_gate_reasons_csv"],
        "freshness_reference_files": freshness_audit["freshness_reference_files"],
        "freshness_selected_vtk_files": freshness_audit["freshness_selected_vtk_files"],
        "latest_reference_mtime_utc": freshness_audit["latest_reference_mtime_utc"],
        "oldest_selected_vtk_mtime_utc": freshness_audit["oldest_selected_vtk_mtime_utc"],
        "vtk_files": [
            {
                "path": str(path),
                "time_step": extract_time_step(path),
                "sha256": sha256(path),
            }
            for path in vtk_files
        ],
        "target_max_profile_velocity_lbm": metadata_value(metadata, "TargetMaxProfileVelocityLbm"),
        "estimated_max_profile_mach": metadata_value(metadata, "EstimatedMaxProfileMach"),
        "lbm_tau": metadata_value(metadata, "LbmTau"),
        "lbm_nu": metadata_value(metadata, "LbmNu"),
        "physical_viscosity_m2s": metadata_value(metadata, "PhysicalViscosityM2s"),
        "estimated_reynolds_number": metadata_value(metadata, "EstimatedReynoldsNumber"),
        "velocity_set": metadata_value(metadata, "VelocitySet"),
        "les_model": metadata_value(metadata, "LesModel"),
        "smagorinsky_cs": metadata_value(metadata, "SmagorinskyCs"),
    }
    for key, value in sampled_stability.items():
        if key not in {
            "mean_speed_mps",
            "mean_speed_stddev_mps",
            "max_speed_stddev_mps",
            "mean_speed_stddev_ratio",
            "max_speed_stddev_ratio",
        }:
            audit[key] = value
    audit.update(log_audit)
    return audit


def main() -> int:
    args = parse_args()
    audit = build_audit(args)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote native run audit: {out_path}")
    print(
        "frames={}; selected={}; time_gate={}; lbm_stability_gate={}; solver_warnings={}".format(
            audit["available_frame_count"],
            audit["source_time_steps_csv"],
            audit["time_averaging_gate"],
            audit["lbm_stability_gate"],
            audit["solver_stability_warnings"],
        )
    )
    print(
        "freshness_gate={}; freshness_reasons={}".format(
            audit["run_freshness_gate"],
            audit["run_freshness_gate_reasons_csv"] or "none",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
