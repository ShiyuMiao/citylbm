#!/usr/bin/env python3
"""Audit coordinate, probe and normalization protocol before CFD runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


PASS_STATUSES = {"pass", "ready_for_validation_run", "paper_grade", "paper_grade_candidate"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check AIJ coordinate axes, probe projection, Uref and official probe-table identity."
    )
    parser.add_argument("run_dir", help="Case root directory.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json generated with the case.")
    parser.add_argument("--official", default="", help="Official RS/probe CSV used for probe comparison.")
    parser.add_argument("--af-csv", default="", help="Official AF inlet-profile CSV used for Uref cross-check.")
    parser.add_argument("--domain-origin", default="", help="domain_origin.json used to map official metre coordinates to VTK lattice coordinates.")
    parser.add_argument("--out", required=True, help="Output coordinate_probe_protocol_audit.json.")
    parser.add_argument("--expected-aij-case", default="")
    parser.add_argument("--expected-wind-direction", default="")
    parser.add_argument("--expected-wind-vector", default="")
    parser.add_argument("--expected-probe-row-count", type=int, default=0)
    parser.add_argument("--expected-probe-z", type=float, default=None)
    parser.add_argument("--expected-probe-z-min", type=float, default=None)
    parser.add_argument("--expected-probe-z-max", type=float, default=None)
    parser.add_argument("--official-condition-filter", default="", help="Optional official RS condition/state filter, e.g. ac.")
    parser.add_argument("--official-wind-filter", default="", help="Optional official RS wind-direction filter, e.g. N.")
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--expected-uref", type=float, default=None)
    parser.add_argument("--uref-tolerance", type=float, default=1.0e-4)
    parser.add_argument("--probe-z-tolerance", type=float, default=1.0e-6)
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_value(metadata: Dict[str, Any], candidates: Sequence[Sequence[str]]) -> Any:
    for path in candidates:
        value = nested(metadata, *path)
        if value not in (None, ""):
            return value
    return None


def resolve_path(
    explicit: str,
    metadata: Dict[str, Any],
    metadata_path: Path,
    candidates: Sequence[Sequence[str]],
) -> Dict[str, Any]:
    explicit_text = explicit.strip()
    if explicit_text:
        raw: Any = explicit_text
        source = "argument"
        path = Path(explicit_text).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
    else:
        raw = first_value(metadata, candidates)
        source = "metadata" if raw not in (None, "") else "missing"
        path = Path(str(raw)).expanduser() if raw not in (None, "") else None
        if path is not None and not path.is_absolute():
            path = metadata_path.parent / path
    resolved = path.resolve() if path is not None else None
    return {
        "source": source,
        "raw": str(raw) if raw not in (None, "") else "",
        "path": str(resolved) if resolved else "",
        "exists": bool(resolved and resolved.is_file()),
        "sha256": sha256(resolved) if resolved and resolved.is_file() else "",
    }


def resolve_domain_origin_path(
    explicit: str,
    metadata: Dict[str, Any],
    metadata_path: Path,
    run_dir: Path,
    probe_projection: Dict[str, Any],
) -> Dict[str, Any]:
    candidates = []
    explicit_text = explicit.strip()
    if explicit_text:
        candidates.append(("argument", explicit_text))
    for key in ["DomainOriginPath", "DomainOriginJson", "DomainOriginFile"]:
        value = probe_projection.get(key)
        if value not in (None, ""):
            candidates.append(("metadata_probe_projection", str(value)))
    for paths in [
        [("DomainOriginPath",), ("DomainOriginJson",), ("DomainOriginFile",)],
        [("Validation", "DomainOriginPath"), ("Validation", "DomainOriginJson")],
    ]:
        for path_keys in paths:
            value = nested(metadata, *path_keys)
            if value not in (None, ""):
                candidates.append(("metadata", str(value)))
    candidates.extend(
        [
            ("run_dir", str(run_dir / "domain_origin.json")),
            ("metadata_dir", str(metadata_path.parent / "domain_origin.json")),
        ]
    )
    for source, raw in candidates:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (metadata_path.parent if source.startswith("metadata") else Path.cwd()) / path
        resolved = path.resolve()
        if resolved.is_file():
            return {
                "source": source,
                "raw": raw,
                "path": str(resolved),
                "exists": True,
                "sha256": sha256(resolved),
            }
    source, raw = candidates[0] if candidates else ("missing", "")
    path = Path(raw).expanduser() if raw else None
    if path is not None and not path.is_absolute():
        path = (metadata_path.parent if source.startswith("metadata") else Path.cwd()) / path
    resolved = path.resolve() if path is not None else None
    return {
        "source": source,
        "raw": raw,
        "path": str(resolved) if resolved else "",
        "exists": False,
        "sha256": "",
    }


def vector3_from_mapping(value: Any) -> List[float]:
    if isinstance(value, list) and len(value) >= 3:
        parsed = [as_float(item) for item in value[:3]]
        return [item for item in parsed if item is not None]
    if isinstance(value, dict):
        parsed = [as_float(value.get(key)) for key in ("X", "Y", "Z")]
        if all(item is not None for item in parsed):
            return [item for item in parsed if item is not None]
        parsed = [as_float(value.get(key)) for key in ("x", "y", "z")]
        if all(item is not None for item in parsed):
            return [item for item in parsed if item is not None]
    return []


def domain_origin_summary(path_info: Dict[str, Any]) -> Dict[str, Any]:
    if not path_info.get("exists"):
        return {
            "dx_m": None,
            "domain_min_m": [],
            "domain_min_source": "",
            "valid": False,
        }
    path = Path(str(path_info.get("path")))
    data = read_json(path)
    dx = None
    for key in ["Dx", "dx", "DxM", "dx_m", "GridSpacingM", "grid_spacing_m"]:
        dx = as_float(data.get(key))
        if dx is not None:
            break
    domain_min_source = ""
    domain_min = vector3_from_mapping(data.get("DomainMin"))
    if len(domain_min) == 3:
        domain_min_source = "DomainMin"
    if len(domain_min) != 3:
        domain_min = vector3_from_mapping(data.get("DomainOrigin"))
        if len(domain_min) == 3:
            domain_min_source = "DomainOrigin"
    if len(domain_min) != 3:
        domain_min = vector3_from_mapping(data.get("Origin"))
        if len(domain_min) == 3:
            domain_min_source = "Origin"
    if len(domain_min) != 3:
        parsed = [as_float(data.get(f"DomainMin{axis}")) for axis in ["X", "Y", "Z"]]
        if all(value is not None for value in parsed):
            domain_min = [value for value in parsed if value is not None]
            domain_min_source = "DomainMinXYZ"
    if len(domain_min) != 3:
        parsed = [as_float(data.get(f"DomainOrigin{axis}")) for axis in ["X", "Y", "Z"]]
        if all(value is not None for value in parsed):
            domain_min = [value for value in parsed if value is not None]
            domain_min_source = "DomainOriginXYZ"
    return {
        "dx_m": dx,
        "domain_min_m": domain_min,
        "domain_min_source": domain_min_source,
        "valid": dx is not None and dx > 0.0 and len(domain_min) == 3,
    }


def as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def normalize_name(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def pick_column(fieldnames: Sequence[str], candidates: Iterable[str]) -> str:
    lookup = {normalize_name(name): name for name in fieldnames}
    for candidate in candidates:
        match = lookup.get(normalize_name(candidate))
        if match:
            return match
    return ""


def load_csv_rows(path_info: Dict[str, Any]) -> List[Dict[str, str]]:
    path_text = path_info.get("path")
    path = Path(path_text) if path_text else None
    if path is None or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def filter_official_rows(
    rows: List[Dict[str, str]],
    condition_filter: str,
    wind_filter: str,
) -> Dict[str, Any]:
    if not rows:
        return {
            "input_row_count": 0,
            "row_count": 0,
            "condition_filter": condition_filter,
            "wind_filter": wind_filter,
            "condition_column": "",
            "wind_column": "",
            "rows": [],
        }
    fieldnames = list(rows[0].keys())
    condition_col = pick_column(fieldnames, ["case", "condition", "state", "construction", "phase"])
    wind_col = pick_column(fieldnames, ["Wind_direction", "wind_direction", "wind", "direction", "WD"])
    condition_norm = normalize_name(condition_filter)
    wind_norm = normalize_name(wind_filter)
    filtered: List[Dict[str, str]] = []
    for row in rows:
        condition_ok = True
        wind_ok = True
        if condition_norm:
            condition_ok = bool(condition_col) and normalize_name(row.get(condition_col, "")) == condition_norm
        if wind_norm:
            wind_ok = bool(wind_col) and normalize_name(row.get(wind_col, "")) == wind_norm
        if condition_ok and wind_ok:
            filtered.append(row)
    return {
        "input_row_count": len(rows),
        "row_count": len(filtered),
        "condition_filter": condition_filter,
        "wind_filter": wind_filter,
        "condition_column": condition_col,
        "wind_column": wind_col,
        "rows": filtered,
    }


def parse_vector(text: str) -> List[float]:
    parts = [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    values = [as_float(part) for part in parts]
    return [value for value in values if value is not None]


def metadata_vector(value: Any) -> List[float]:
    if isinstance(value, list):
        parsed = [as_float(item) for item in value]
        return [item for item in parsed if item is not None]
    if isinstance(value, dict):
        parsed = [as_float(value.get(key)) for key in ("X", "Y", "Z")]
        if any(item is not None for item in parsed):
            return [item for item in parsed if item is not None]
        parsed = [as_float(value.get(key)) for key in ("x", "y", "z")]
        return [item for item in parsed if item is not None]
    if isinstance(value, str):
        return parse_vector(value)
    return []


def vector_close(actual: Sequence[float], expected: Sequence[float], tolerance: float = 1.0e-6) -> bool:
    return len(actual) == len(expected) == 3 and all(abs(a - b) <= tolerance for a, b in zip(actual, expected))


def close(actual: Optional[float], expected: Optional[float], tolerance: float) -> bool:
    if actual is None or expected is None:
        return False
    return abs(actual - expected) <= tolerance


def interpolate_af_u(rows: List[Dict[str, str]], z_ref: Optional[float]) -> Optional[float]:
    if z_ref is None or not rows:
        return None
    fieldnames = list(rows[0].keys())
    z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
    u_col = pick_column(fieldnames, ["u", "u_mps", "u(m/s)", "U(m/s)", "velocity", "velocity_mps"])
    if not z_col or not u_col:
        return None
    samples: List[tuple[float, float]] = []
    for row in rows:
        z = as_float(row.get(z_col))
        u = as_float(row.get(u_col))
        if z is not None and u is not None:
            samples.append((z, u))
    if not samples:
        return None
    samples.sort()
    if z_ref <= samples[0][0]:
        return samples[0][1]
    if z_ref >= samples[-1][0]:
        return samples[-1][1]
    for (z0, u0), (z1, u1) in zip(samples, samples[1:]):
        if z0 <= z_ref <= z1 and z1 != z0:
            t = (z_ref - z0) / (z1 - z0)
            return u0 + t * (u1 - u0)
    return None


def probe_csv_summary(
    rows: List[Dict[str, str]],
    expected_z: Optional[float],
    expected_z_min: Optional[float],
    expected_z_max: Optional[float],
    z_tolerance: float,
) -> Dict[str, Any]:
    if not rows:
        return {
            "row_count": 0,
            "z_column": "",
            "z_valid_count": 0,
            "z_mismatch_count": 0,
            "z_range_mismatch_count": 0,
            "z_below_min_count": 0,
            "z_above_max_count": 0,
        }
    fieldnames = list(rows[0].keys())
    z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
    z_values = [as_float(row.get(z_col)) for row in rows] if z_col else []
    z_numeric = [value for value in z_values if value is not None]
    mismatch_count = 0
    if expected_z is not None and z_col:
        mismatch_count = sum(1 for value in z_numeric if not close(value, expected_z, z_tolerance))
    below_min_count = 0
    above_max_count = 0
    if expected_z_min is not None and z_col:
        below_min_count = sum(1 for value in z_numeric if value < expected_z_min - z_tolerance)
    if expected_z_max is not None and z_col:
        above_max_count = sum(1 for value in z_numeric if value > expected_z_max + z_tolerance)
    return {
        "row_count": len(rows),
        "columns": fieldnames,
        "z_column": z_col,
        "z_valid_count": len(z_numeric),
        "z_min": min(z_numeric) if z_numeric else None,
        "z_max": max(z_numeric) if z_numeric else None,
        "z_mismatch_count": mismatch_count,
        "z_range_mismatch_count": below_min_count + above_max_count,
        "z_below_min_count": below_min_count,
        "z_above_max_count": above_max_count,
        "expected_z": expected_z,
        "expected_z_min": expected_z_min,
        "expected_z_max": expected_z_max,
    }


def official_probe_identity_summary(rows: List[Dict[str, str]], uref_mps: Optional[float]) -> Dict[str, Any]:
    if not rows:
        return {
            "row_count": 0,
            "id_column": "",
            "x_column": "",
            "y_column": "",
            "z_column": "",
            "value_column": "",
            "value_source": "",
            "value_requires_uref": False,
            "missing_id_count": 0,
            "duplicate_ids": [],
            "invalid_coordinate_count": 0,
            "invalid_value_count": 0,
            "unique_id_count": 0,
        }
    fieldnames = list(rows[0].keys())
    id_col = pick_column(fieldnames, ["No.", "No", "probe_id", "ProbeId", "ProbeID", "id", "ID", "point", "point_id"])
    x_col = pick_column(fieldnames, ["x", "X", "x_m", "X_m", "x(m)", "X(m)"])
    y_col = pick_column(fieldnames, ["y", "Y", "y_m", "Y_m", "y(m)", "Y(m)"])
    z_col = pick_column(fieldnames, ["z", "Z", "z_m", "Z_m", "z(m)", "Z(m)", "height", "height_m"])
    ratio_col = pick_column(
        fieldnames,
        ["Velocity_Ratio", "velocity_ratio", "V_exp_ratio", "U_exp_ratio"],
    )
    velocity_col = ""
    value_source = "velocity_ratio_column"
    value_requires_uref = False
    if ratio_col:
        value_col = ratio_col
    else:
        value_col = pick_column(
            fieldnames,
            ["U(m/s)", "U_mps", "U", "V(m/s)", "V_mps", "V", "Velocity(m/s)", "Velocity", "WindSpeed"],
        )
        if value_col:
            velocity_col = value_col
            value_source = "computed_from_velocity_mps_over_Uref"
            value_requires_uref = True
    seen = set()
    duplicates = set()
    missing_id_count = 0
    invalid_coordinate_count = 0
    invalid_value_count = 0
    for row in rows:
        raw_id = str(row.get(id_col, "")).strip() if id_col else ""
        normalized_id = normalize_name(raw_id)
        if not normalized_id:
            missing_id_count += 1
        elif normalized_id in seen:
            duplicates.add(raw_id or normalized_id)
        else:
            seen.add(normalized_id)

        coords = [as_float(row.get(col)) if col else None for col in [x_col, y_col, z_col]]
        if any(value is None for value in coords):
            invalid_coordinate_count += 1
        value = as_float(row.get(value_col)) if value_col else None
        if value is not None and velocity_col:
            if uref_mps is None or uref_mps <= 0.0:
                value = None
            else:
                value = value / uref_mps
        if value is None:
            invalid_value_count += 1

    return {
        "row_count": len(rows),
        "id_column": id_col,
        "x_column": x_col,
        "y_column": y_col,
        "z_column": z_col,
        "value_column": value_col,
        "velocity_column": velocity_col,
        "value_source": value_source if value_col else "",
        "value_requires_uref": value_requires_uref,
        "value_uref_mps": uref_mps if value_requires_uref else None,
        "missing_id_count": missing_id_count,
        "duplicate_ids": sorted(duplicates),
        "invalid_coordinate_count": invalid_coordinate_count,
        "invalid_value_count": invalid_value_count,
        "unique_id_count": len(seen),
    }


def text_contains(value: Any, *tokens: str) -> bool:
    text = str(value or "").lower()
    return all(token.lower() in text for token in tokens)


def list_text(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def ratio_names(normalization: Dict[str, Any]) -> List[str]:
    return [normalize_name(item) for item in list_text(normalization.get("OutputRatios"))]


def streamwise_axis_declared(axes: Dict[str, Any], protocol: Dict[str, Any]) -> bool:
    values = list(axes.values())
    values.append(protocol.get("StreamwiseAxis"))
    return any(
        text_contains(value, "streamwise") and (text_contains(value, "downstream") or text_contains(value, "wind"))
        for value in values
    )


def velocity_ratio_mapping_status(
    velocity_components: Dict[str, Any],
    normalization: Dict[str, Any],
) -> Dict[str, Any]:
    u_text = str(velocity_components.get("U") or velocity_components.get("VelocityRatio") or "")
    u_norm = normalize_name(u_text)
    ratios = ratio_names(normalization)
    accepts_magnitude = any(
        token in u_norm
        for token in ["umag", "magnitude", "speedmagnitude", "velocitymagnitude", "sqrtux2uy2uz2"]
    )
    accepts_streamwise = any(token in u_norm for token in ["streamwise", "windaligned", "dotu"])
    accepts_ux = "ux" in u_norm or "fluidx3dux" in u_norm
    magnitude_ratio = any(
        item in ratios
        for item in ["umagoveruref", "velocitymagnitudeoveruref", "speedmagnitudeoveruref", "velocityratio"]
    )
    streamwise_ratio = any(
        item in ratios
        for item in ["ustreamoveruref", "uwindoveruref", "windaligneduoveruref", "streamwiseuoveruref"]
    )
    ux_ratio = "uxoveruref" in ratios
    if accepts_magnitude and magnitude_ratio:
        return {"ok": True, "mode": "velocity_magnitude", "required_ratio": "Umag_over_Uref"}
    if accepts_streamwise and streamwise_ratio:
        return {"ok": True, "mode": "wind_aligned_streamwise", "required_ratio": "Ustream_over_Uref"}
    if accepts_ux and ux_ratio:
        return {"ok": True, "mode": "fluidx3d_u_x", "required_ratio": "Ux_over_Uref"}
    return {
        "ok": False,
        "mode": "",
        "required_ratio": "",
        "mapping_text": u_text,
        "output_ratios": list_text(normalization.get("OutputRatios")),
    }


def canonical_label(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def label_matches(actual: str, expected: str) -> bool:
    actual_norm = canonical_label(actual)
    expected_norm = canonical_label(expected)
    return bool(actual_norm and expected_norm and (actual_norm == expected_norm or expected_norm in actual_norm))


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()
    metadata = read_json(metadata_path)
    reasons: List[str] = []
    warnings: List[str] = []

    if not run_dir.exists():
        reasons.append("run_dir_missing")
    if not metadata:
        reasons.append("metadata_missing_or_invalid")

    protocol = metadata.get("CoordinateProtocol") if isinstance(metadata.get("CoordinateProtocol"), dict) else {}
    axes = protocol.get("Axes") if isinstance(protocol.get("Axes"), dict) else {}
    velocity_components = protocol.get("VelocityComponents") if isinstance(protocol.get("VelocityComponents"), dict) else {}
    normalization = protocol.get("Normalization") if isinstance(protocol.get("Normalization"), dict) else {}
    probe_projection = protocol.get("ProbeProjection") if isinstance(protocol.get("ProbeProjection"), dict) else {}

    expected_vector = parse_vector(args.expected_wind_vector) if args.expected_wind_vector else []

    if not protocol:
        reasons.append("coordinate_protocol_missing")
    if not streamwise_axis_declared(axes, protocol):
        reasons.append("coordinate_streamwise_axis_not_declared")
    if not text_contains(axes.get("z"), "vertical"):
        reasons.append("coordinate_axis_z_not_declared_vertical")
    velocity_mapping = velocity_ratio_mapping_status(velocity_components, normalization)
    if not velocity_mapping["ok"]:
        reasons.append("velocity_component_U_not_mapped_to_official_velocity_ratio")

    output_ratios = normalization.get("OutputRatios")
    if not isinstance(output_ratios, list) or not ratio_names(normalization):
        reasons.append("normalization_output_ratio_missing")

    metadata_case = str(first_value(metadata, [("AijCase",), ("AIJCase",), ("Case",), ("CaseLabel",)]) or "")
    if args.expected_aij_case and metadata_case and not label_matches(metadata_case, args.expected_aij_case):
        reasons.append(f"case_mismatch:{metadata_case}!={args.expected_aij_case}")
    if args.expected_aij_case and not metadata_case:
        reasons.append("case_label_missing")

    metadata_wind = str(first_value(metadata, [("WindDirection",), ("WindDirectionLabel",), ("WindDirectionName",)]) or "")
    if args.expected_wind_direction and metadata_wind and metadata_wind.lower() != args.expected_wind_direction.lower():
        reasons.append(f"wind_direction_mismatch:{metadata_wind}!={args.expected_wind_direction}")
    if args.expected_wind_direction and not metadata_wind:
        reasons.append("wind_direction_label_missing")

    actual_vector = metadata_vector(first_value(metadata, [("WindDirectionUnitVector",), ("WindVector",), ("WindDirectionVector",)]))
    if expected_vector and not vector_close(actual_vector, expected_vector):
        reasons.append(
            "wind_vector_mismatch:"
            + ",".join(str(value) for value in actual_vector)
            + "!="
            + ",".join(str(value) for value in expected_vector)
        )

    uref = as_float(normalization.get("Uref_mps"))
    if uref is None:
        uref = as_float(metadata.get("Uref"))
    zref = as_float(normalization.get("Zref_m"))
    if zref is None:
        zref = as_float(metadata.get("Zref"))
    if args.expected_uref is not None and not close(uref, args.expected_uref, args.uref_tolerance):
        reasons.append(f"uref_mismatch:{uref}!={args.expected_uref}")

    required_probe_projection = [
        "Formula",
        "SamplingMethod",
        "ProbeVolumeRadiusCells",
        "ProbeZOffsetM",
        "ProbeCellCenterCoordinates",
    ]
    missing_probe_projection = [key for key in required_probe_projection if key not in probe_projection]
    if missing_probe_projection:
        reasons.append("probe_projection_fields_missing:" + ",".join(missing_probe_projection))
    projection_formula = str(probe_projection.get("Formula") or "")
    if not text_contains(projection_formula, "dx") or not (
        text_contains(projection_formula, "domain")
        or text_contains(projection_formula, "origin")
        or text_contains(projection_formula, "min")
    ):
        reasons.append("probe_projection_formula_missing_domain_origin_or_dx_mapping")
    if str(probe_projection.get("SamplingMethod") or metadata.get("ProbeSampling") or "").lower() not in {
        "nearest-valid",
        "nearest_valid",
        "volume-average",
        "volume_average",
        "trilinear",
    }:
        reasons.append("probe_sampling_method_missing_or_unknown")
    probe_radius = as_float(probe_projection.get("ProbeVolumeRadiusCells"))
    if probe_radius is None or probe_radius < 0.0:
        reasons.append("probe_volume_radius_cells_missing_or_invalid")
    if as_float(probe_projection.get("ProbeZOffsetM")) is None:
        reasons.append("probe_z_offset_m_missing_or_invalid")
    if not isinstance(probe_projection.get("ProbeCellCenterCoordinates"), bool):
        reasons.append("probe_cell_center_coordinates_not_boolean")

    domain_origin_info = resolve_domain_origin_path(
        args.domain_origin,
        metadata,
        metadata_path,
        run_dir,
        probe_projection,
    )
    domain_origin = domain_origin_summary(domain_origin_info)
    if not domain_origin_info["exists"]:
        reasons.append("domain_origin_json_missing")
    if domain_origin["dx_m"] is None or domain_origin["dx_m"] <= 0.0:
        reasons.append("domain_origin_dx_m_missing_or_invalid")
    if len(domain_origin["domain_min_m"]) != 3:
        reasons.append("domain_origin_domain_min_m_missing_or_invalid")
    projection_dx = as_float(probe_projection.get("DxM"))
    if projection_dx is not None and domain_origin["dx_m"] is not None and not close(
        projection_dx,
        domain_origin["dx_m"],
        1.0e-9,
    ):
        reasons.append(f"probe_projection_dx_m_mismatch_domain_origin:{projection_dx}!={domain_origin['dx_m']}")
    projection_min = vector3_from_mapping(probe_projection.get("DomainMinM"))
    if projection_min and len(domain_origin["domain_min_m"]) == 3 and not vector_close(
        projection_min,
        domain_origin["domain_min_m"],
        1.0e-9,
    ):
        reasons.append("probe_projection_domain_min_m_mismatch_domain_origin")

    probe_count = as_float(metadata.get("ProbeCount"))
    if args.expected_probe_row_count > 0 and probe_count is not None and int(probe_count) != args.expected_probe_row_count:
        reasons.append(f"metadata_probe_count_mismatch:{int(probe_count)}!={args.expected_probe_row_count}")

    official_info = resolve_path(
        args.official,
        metadata,
        metadata_path,
        [("OfficialRS",), ("OfficialProbeCsv",), ("OfficialProbeCSV",), ("Validation", "OfficialRS")],
    )
    af_info = resolve_path(
        args.af_csv,
        metadata,
        metadata_path,
        [("OfficialAF",), ("OfficialAFCsv",), ("OfficialAFCSV",), ("Validation", "OfficialAF")],
    )

    official_rows_raw = load_csv_rows(official_info)
    official_filter = filter_official_rows(
        official_rows_raw,
        args.official_condition_filter,
        args.official_wind_filter,
    )
    official_rows = official_filter["rows"]
    if (
        args.expected_probe_z is not None
        and (args.expected_probe_z_min is not None or args.expected_probe_z_max is not None)
    ):
        reasons.append("expected_probe_z_single_and_range_both_set")
    if (
        args.expected_probe_z_min is not None
        and args.expected_probe_z_max is not None
        and args.expected_probe_z_min > args.expected_probe_z_max
    ):
        reasons.append(f"expected_probe_z_range_invalid:{args.expected_probe_z_min}>{args.expected_probe_z_max}")

    official_summary = probe_csv_summary(
        official_rows,
        args.expected_probe_z,
        args.expected_probe_z_min,
        args.expected_probe_z_max,
        args.probe_z_tolerance,
    )
    official_identity = official_probe_identity_summary(official_rows, uref)
    if (args.official or official_info["source"] == "metadata") and not official_info["exists"]:
        reasons.append("official_probe_csv_missing")
    if official_rows:
        if not official_identity["id_column"]:
            reasons.append("official_probe_id_column_missing")
        if official_identity["missing_id_count"]:
            reasons.append(f"official_probe_missing_id_count:{official_identity['missing_id_count']}")
        if official_identity["duplicate_ids"]:
            reasons.append("official_probe_duplicate_ids:" + ";".join(official_identity["duplicate_ids"]))
        if not official_identity["x_column"] or not official_identity["y_column"] or not official_identity["z_column"]:
            reasons.append("official_probe_coordinate_columns_missing")
        if official_identity["invalid_coordinate_count"]:
            reasons.append(f"official_probe_invalid_coordinate_count:{official_identity['invalid_coordinate_count']}")
        if not official_identity["value_column"]:
            reasons.append("official_probe_velocity_ratio_column_missing")
        if official_identity["invalid_value_count"]:
            reasons.append(f"official_probe_invalid_velocity_ratio_count:{official_identity['invalid_value_count']}")
    if args.expected_probe_row_count > 0:
        if official_summary["row_count"] != args.expected_probe_row_count:
            reasons.append(f"official_probe_row_count_mismatch:{official_summary['row_count']}!={args.expected_probe_row_count}")
        if probe_count is None:
            warnings.append("metadata_probe_count_missing")
    if args.expected_probe_z is not None:
        if official_summary["row_count"] > 0 and not official_summary["z_column"]:
            reasons.append("official_probe_z_column_missing")
        elif official_summary["z_mismatch_count"]:
            reasons.append(f"official_probe_z_mismatch_count:{official_summary['z_mismatch_count']}")
    if args.expected_probe_z_min is not None or args.expected_probe_z_max is not None:
        if official_summary["row_count"] > 0 and not official_summary["z_column"]:
            reasons.append("official_probe_z_column_missing")
        elif official_summary["z_range_mismatch_count"]:
            reasons.append(f"official_probe_z_range_mismatch_count:{official_summary['z_range_mismatch_count']}")

    af_rows = load_csv_rows(af_info)
    af_uref = interpolate_af_u(af_rows, args.z_ref if args.z_ref is not None else zref)
    if args.af_csv and not af_info["exists"]:
        reasons.append("af_csv_missing")
    if args.expected_uref is not None and af_rows and af_uref is not None and not close(
        af_uref, args.expected_uref, max(args.uref_tolerance, 1.0e-3)
    ):
        reasons.append(f"af_uref_at_zref_mismatch:{af_uref}!={args.expected_uref}")

    gate = "pass" if not reasons else "fail"
    if gate == "pass":
        development_stage = "eligible_for_short_native_canary"
        development_duration = "short_cfd"
        development_runs_cfd_next = True
        development_next_cfd_scope = "short_native_canary_only"
        development_reason = "Coordinate axes, wind vector, probe subset and Uref identity pass the pre-CFD protocol gate."
    elif any("coordinate_axis" in reason or "velocity_component" in reason for reason in reasons):
        development_stage = "fix_coordinate_axis_component_mapping_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_coordinate_component_gate_passes"
        development_reason = "Coordinate axes or streamwise velocity-component mapping is ambiguous or inconsistent."
    elif any("uref" in reason.lower() or "normalization" in reason.lower() for reason in reasons):
        development_stage = "fix_uref_normalization_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_uref_normalization_gate_passes"
        development_reason = "Uref, zref or output-ratio normalization does not match the official AF/profile protocol."
    elif any(
        "probe" in reason.lower() or "domain_origin" in reason.lower()
        for reason in reasons
    ):
        development_stage = "fix_probe_subset_projection_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_probe_subset_projection_gate_passes"
        development_reason = "Official probe count, probe height/range or probe projection protocol is inconsistent."
    else:
        development_stage = "fix_coordinate_probe_protocol_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_coordinate_probe_gate_passes"
        development_reason = "Coordinate/probe protocol audit reports unresolved blockers."

    report = {
        "Schema": "citylbm.coordinate_probe_protocol_audit.v1",
        "GeneratedAtUtc": utc_now(),
        "RunDir": str(run_dir),
        "Metadata": {
            "path": str(metadata_path),
            "exists": metadata_path.is_file(),
            "sha256": sha256(metadata_path) if metadata_path.is_file() else "",
        },
        "Gate": gate,
        "coordinate_probe_protocol_gate": gate,
        "Reasons": reasons,
        "Warnings": warnings,
        "Case": {"metadata": metadata_case, "expected": args.expected_aij_case},
        "WindDirection": {"metadata": metadata_wind, "expected": args.expected_wind_direction},
        "WindVector": {"metadata": actual_vector, "expected": expected_vector},
        "CoordinateProtocol": {
            "present": bool(protocol),
            "Axes": axes,
            "VelocityComponents": velocity_components,
            "VelocityRatioMapping": velocity_mapping,
            "Normalization": normalization,
            "ProbeProjection": probe_projection,
            "DomainOrigin": {
                "path": domain_origin_info.get("path", ""),
                "source": domain_origin_info.get("source", ""),
                "exists": domain_origin_info.get("exists", False),
                "sha256": domain_origin_info.get("sha256", ""),
                "dx_m": domain_origin.get("dx_m"),
                "domain_min_m": domain_origin.get("domain_min_m"),
                "domain_min_source": domain_origin.get("domain_min_source"),
                "valid": domain_origin.get("valid", False),
                "projection_dx_m": projection_dx,
                "projection_domain_min_m": projection_min,
            },
        },
        "Uref": {
            "metadata_mps": uref,
            "metadata_zref_m": zref,
            "expected_mps": args.expected_uref,
            "af_u_at_zref_mps": af_uref,
            "zref_checked_m": args.z_ref if args.z_ref is not None else zref,
        },
        "OfficialProbeCsv": official_info,
        "OfficialProbeSummary": official_summary,
        "OfficialProbeIdentity": official_identity,
        "OfficialProbeFilter": {key: value for key, value in official_filter.items() if key != "rows"},
        "AFCsv": af_info,
        "development_acceleration_stage": development_stage,
        "development_acceleration_duration_class": development_duration,
        "development_acceleration_runs_cfd_next": development_runs_cfd_next,
        "development_acceleration_next_cfd_scope": development_next_cfd_scope,
        "development_acceleration_reason": development_reason,
        "long_cfd_allowed_by_coordinate_probe_protocol": gate == "pass",
        "RequiredBeforeLongCfd": [
            "coordinate_probe_protocol_gate=pass",
            "official probe IDs are present and unique in the selected RS subset",
            "official x/y/z coordinates and measured velocity-ratio values are numeric",
            "simulated velocity ratio maps explicitly to the official measured quantity",
            "Uref and zref match the official AF profile",
            "probe count and probe z or z-range match the selected AIJ RS subset",
            "domain_origin.json exists and provides Dx plus three-axis DomainMin/DomainOrigin for reproducible probe mapping",
        ],
    }
    write_json(Path(args.out).expanduser().resolve(), report)
    print(f"coordinate_probe_protocol_gate={gate}; out={Path(args.out).expanduser().resolve()}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate in PASS_STATUSES else 2


if __name__ == "__main__":
    raise SystemExit(main())
