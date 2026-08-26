#!/usr/bin/env python3
"""Bind explicit coordinate, probe and normalization protocol into metadata.

The script is intentionally no-CFD. It creates a derived metadata file used by
preflight gates so that long solver runs are not launched while the comparison
quantity, wind vector or probe subset is still ambiguous.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add AIJ coordinate/probe protocol fields to case_metadata.json.")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--case-dir", default="")
    parser.add_argument("--setup", default="")
    parser.add_argument("--case-label", default="")
    parser.add_argument("--wind-direction", default="")
    parser.add_argument("--wind-vector", default="")
    parser.add_argument("--probe-count", type=int, default=0)
    parser.add_argument("--probe-z-offset", type=float, default=0.0)
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--uref", type=float, default=None)
    parser.add_argument("--official-rs", default="")
    parser.add_argument("--official-af", default="")
    parser.add_argument(
        "--velocity-component-map",
        default="auto",
        choices=["auto", "magnitude", "wind-aligned", "ux"],
        help="Quantity compared against the official velocity ratio.",
    )
    parser.add_argument("--sampling-method", default="nearest-valid")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def sha256_file(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def nested(metadata: Dict[str, Any], *keys: str) -> Any:
    current: Any = metadata
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_text(metadata: Dict[str, Any], paths: List[List[str]]) -> str:
    for path in paths:
        value = nested(metadata, *path)
        if value not in (None, ""):
            return str(value)
    return ""


def first_float(metadata: Dict[str, Any], paths: List[List[str]]) -> Optional[float]:
    for path in paths:
        value = nested(metadata, *path)
        if value in (None, "") or isinstance(value, bool):
            continue
        try:
            return float(str(value))
        except ValueError:
            continue
    return None


def first_int(metadata: Dict[str, Any], paths: List[List[str]]) -> Optional[int]:
    value = first_float(metadata, paths)
    return int(value) if value is not None else None


def parse_vector(text: str) -> List[float]:
    parts = [part.strip() for part in str(text or "").replace(";", ",").split(",") if part.strip()]
    if len(parts) != 3:
        return []
    try:
        return [float(part) for part in parts]
    except ValueError:
        return []


def metadata_vector(value: Any) -> List[float]:
    if isinstance(value, list) and len(value) == 3:
        try:
            return [float(item) for item in value]
        except (TypeError, ValueError):
            return []
    if isinstance(value, dict):
        values = [value.get(key) for key in ("X", "Y", "Z")]
        if any(item is not None for item in values):
            try:
                return [float(item) for item in values]
            except (TypeError, ValueError):
                return []
        values = [value.get(key) for key in ("x", "y", "z")]
        try:
            return [float(item) for item in values]
        except (TypeError, ValueError):
            return []
    if isinstance(value, str):
        return parse_vector(value)
    return []


def resolve_path(text: str) -> str:
    if not text:
        return ""
    return str(Path(text).expanduser().resolve())


def setup_uses_magnitude(setup: Path) -> bool:
    if not setup.is_file():
        return False
    try:
        source = setup.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "sim_ratio = umag_mps/u_ref_si" in source or "sqrt(ux_mps*ux_mps" in source


def infer_setup_path(args: argparse.Namespace) -> Path:
    if args.setup:
        return Path(args.setup).expanduser().resolve()
    if args.case_dir:
        case_dir = Path(args.case_dir).expanduser().resolve()
        for name in ("src/setup.cpp", "setup.cpp"):
            candidate = case_dir / name
            if candidate.is_file():
                return candidate
    return Path("")


def velocity_mapping(args: argparse.Namespace, setup: Path) -> Dict[str, Any]:
    mode = args.velocity_component_map
    if mode == "auto":
        mode = "magnitude" if setup_uses_magnitude(setup) else "wind-aligned"
    if mode == "magnitude":
        return {
            "U": "speed magnitude compared with official Velocity_Ratio; FluidX3D umag = sqrt(u.x^2+u.y^2+u.z^2)",
            "OutputRatios": ["Umag_over_Uref", "Velocity_Ratio"],
            "Mode": "velocity_magnitude",
        }
    if mode == "wind-aligned":
        return {
            "U": "wind-aligned streamwise velocity dot(u, wind_direction_vector)",
            "OutputRatios": ["Ustream_over_Uref", "Uwind_over_Uref"],
            "Mode": "wind_aligned_streamwise",
        }
    return {
        "U": "streamwise velocity compared with FluidX3D u.x",
        "OutputRatios": ["Ux_over_Uref"],
        "Mode": "fluidx3d_u_x",
    }


def axes_for_wind(vector: List[float]) -> Dict[str, str]:
    if len(vector) != 3:
        return {
            "x": "streamwise/downstream direction must be declared by the case generator",
            "y": "lateral/spanwise direction must be declared by the case generator",
            "z": "vertical; ground at z=0 m",
        }
    dominant = max(range(3), key=lambda index: abs(vector[index]))
    axis_name = ["x", "y", "z"][dominant]
    sign = "positive" if vector[dominant] >= 0 else "negative"
    axes = {
        "x": "lateral/spanwise horizontal coordinate",
        "y": "lateral/spanwise horizontal coordinate",
        "z": "vertical; ground at z=0 m",
    }
    axes[axis_name] = f"streamwise/downstream horizontal coordinate; downstream follows {sign} {axis_name.upper()} for wind vector"
    return axes


def main() -> int:
    args = parse_args()
    metadata_path = Path(args.metadata).expanduser().resolve()
    metadata = read_json(metadata_path)
    if not metadata:
        print(f"metadata_missing_or_invalid:{metadata_path}")
        return 2

    setup = infer_setup_path(args)
    wind_vector = parse_vector(args.wind_vector) or metadata_vector(
        nested(metadata, "WindDirectionUnitVector")
        or nested(metadata, "WindVector")
        or nested(metadata, "WindDirectionVector")
        or nested(metadata, "inlet", "wind_vector")
    )
    case_label = args.case_label or first_text(metadata, [["AijCase"], ["AIJCase"], ["Case"], ["case"]])
    wind_direction = args.wind_direction or first_text(metadata, [["WindDirection"], ["WindDirectionLabel"], ["inlet", "wind_direction"]])
    probe_count = args.probe_count or first_int(metadata, [["ProbeCount"], ["target_rs_subset", "rows"], ["time_averaging", "official_probe_count"]]) or 0
    uref = args.uref if args.uref is not None else first_float(
        metadata,
        [["CoordinateProtocol", "Normalization", "Uref_mps"], ["Uref"], ["physics", "u_ref_mps_at_15p9m"]],
    )
    zref = args.z_ref if args.z_ref is not None else first_float(
        metadata,
        [["CoordinateProtocol", "Normalization", "Zref_m"], ["Zref"], ["physics", "z_ref_m"]],
    )
    official_rs = args.official_rs or first_text(
        metadata,
        [["OfficialRS"], ["OfficialRSCsv"], ["OfficialProbeCsv"], ["official_inputs", "RS_caseE.csv", "path"], ["official_inputs", "RS_caseA.csv", "path"]],
    )
    official_af = args.official_af or first_text(
        metadata,
        [["OfficialAF"], ["OfficialAFCsv"], ["InletProfileCsv"], ["official_inputs", "AF_caseE.csv", "path"], ["official_inputs", "AF_caseA.csv", "path"]],
    )
    official_rs_resolved = resolve_path(official_rs)
    official_af_resolved = resolve_path(official_af)
    component = velocity_mapping(args, setup)
    protocol = {
        "Axes": axes_for_wind(wind_vector),
        "StreamwiseAxis": "derived from WindDirectionUnitVector; downstream follows the inflow vector used by the generated FluidX3D case",
        "VelocityComponents": {
            "U": component["U"],
            "MappingMode": component["Mode"],
        },
        "Normalization": {
            "Uref_mps": uref,
            "Zref_m": zref,
            "OutputRatios": component["OutputRatios"],
        },
        "ProbeProjection": {
            "Formula": "grid_coordinate = (official_coordinate_m - domain_min_m) / dx_m; sample generated probe grid coordinates",
            "SamplingMethod": args.sampling_method,
            "ProbeVolumeRadiusCells": 1,
            "ProbeZOffsetM": args.probe_z_offset,
            "ProbeCellCenterCoordinates": False,
            "AvailableSamplingMethods": [
                "raw_trilinear",
                "fluid_weighted_trilinear",
                "nearest_valid",
                "vertical_valid_above",
            ],
        },
    }
    bound = dict(metadata)
    bound.update(
        {
            "AijCase": case_label,
            "WindDirection": wind_direction,
            "WindDirectionUnitVector": wind_vector,
            "ProbeCount": probe_count,
            "OfficialRS": official_rs_resolved,
            "OfficialRSSha256": sha256_file(official_rs_resolved),
            "OfficialProbeData": official_rs_resolved,
            "OfficialProbeDataSha256": sha256_file(official_rs_resolved),
            "OfficialAF": official_af_resolved,
            "OfficialAFSha256": sha256_file(official_af_resolved),
            "CoordinateProtocol": protocol,
            "CoordinateProbeProtocolBoundAtUtc": utc_now(),
            "CoordinateProbeProtocolBindingSource": {
                "metadata": str(metadata_path),
                "setup": str(setup) if str(setup) != "." else "",
                "velocity_component_map": args.velocity_component_map,
                "resolved_velocity_mapping_mode": component["Mode"],
            },
        }
    )
    out = Path(args.out).expanduser().resolve()
    write_json(out, bound)
    print(f"coordinate_probe_protocol_metadata_bound={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
