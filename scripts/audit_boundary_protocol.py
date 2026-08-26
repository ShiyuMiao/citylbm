#!/usr/bin/env python3
"""Audit AIJ boundary-condition evidence for CityLBM/FluidX3D validation.

This script does not judge CFD accuracy. It checks whether a completed run has
enough traceable boundary, blockage, fetch and roughness evidence before the
numeric metrics can be treated as paper-grade AIJ validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


REQUIRED_EVIDENCE_FIELDS = [
    "boundary_evidence_class",
    "boundary_evidence_files",
    "aij_case",
    "wind_direction",
    "boundary_equivalence_basis",
    "inlet_boundary",
    "outlet_boundary",
    "lateral_boundary",
    "top_boundary",
    "ground_wall_treatment",
    "roughness_treatment",
    "floor_roughness_source",
    "blockage_source",
    "fetch_clearance_source",
    "inlet_fetch_clearance_h",
    "downstream_clearance_h",
    "min_lateral_clearance_h",
    "top_clearance_h",
    "outlet_reflection_check",
    "side_top_boundary_check",
]

BOUNDARY_EQUIVALENCE_TOKENS = [
    "aij_verified",
    "empty_tunnel_passed",
    "validated_boundary_model",
    "precursor_boundary",
    "recycling_boundary",
    "wind_tunnel_protocol_matched",
]

SUPPORTED_EVIDENCE_CLASSES = {
    "official_aij_documentation",
    "wind_tunnel_protocol_matched",
    "empty_tunnel_boundary_preservation",
    "precursor_boundary",
    "recycling_boundary",
    "validated_boundary_model",
}

SUPPORTED_CONDITION_TOKENS = [
    "aij_verified",
    "empty_tunnel_passed",
    "validated_boundary_model",
    "precursor_boundary",
    "recycling_boundary",
    "wind_tunnel_protocol_matched",
    "official",
    "measured",
    "sha256",
    "source_documented",
    "non_reflecting_checked",
    "reflection_checked",
    "profile_preserved",
    "roughness_layout_source",
    "validated_rough_wall",
    "blockage_verified",
    "fetch_verified",
]

UNSUPPORTED_CONDITION_TOKENS = [
    "unknown",
    "unverified",
    "not_checked",
    "not check",
    "todo",
    "placeholder",
    "diagnostic_only",
    "assumed_only",
    "approximate",
    "approximation",
    "box boundary",
    "missing",
    "none",
    "free outflow",
    "free-outflow",
    "free approximation",
    "open boundary",
    "open outlet",
    "simple_box",
    "simplified",
    "slip/free",
    "slip approximation",
    "type e",
    "type_e",
]

CONDITION_SUPPORT_FIELDS = [
    "inlet_boundary",
    "outlet_boundary",
    "lateral_boundary",
    "top_boundary",
    "ground_wall_treatment",
    "roughness_treatment",
    "floor_roughness_source",
    "blockage_source",
    "fetch_clearance_source",
    "outlet_reflection_check",
    "side_top_boundary_check",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit boundary-condition evidence for an AIJ validation run."
    )
    parser.add_argument("run_dir", help="Case root directory.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json generated with the run.")
    parser.add_argument(
        "--evidence",
        default="",
        help="Optional JSON file documenting AIJ-equivalent boundary/fetch/roughness evidence.",
    )
    parser.add_argument("--out", required=True, help="Output boundary_protocol_audit.json.")
    parser.add_argument("--max-frontal-blockage-ratio", type=float, default=0.05)
    parser.add_argument("--min-upstream-clearance-h", type=float, default=5.0)
    parser.add_argument("--min-downstream-clearance-h", type=float, default=10.0)
    parser.add_argument("--min-lateral-clearance-h", type=float, default=5.0)
    parser.add_argument("--min-top-clearance-h", type=float, default=5.0)
    parser.add_argument("--expected-aij-case", default="", help="Optional expected AIJ case label for the evidence JSON.")
    parser.add_argument("--expected-wind-direction", default="", help="Optional expected wind-direction label for the evidence JSON.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        value = float(value)
        return None if math.isnan(value) or math.isinf(value) else value
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return None if math.isnan(parsed) or math.isinf(parsed) else parsed


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_metadata_value(metadata: Dict[str, Any], candidates: Iterable[Iterable[str]]) -> Any:
    for path in candidates:
        value = nested(metadata, *path)
        if value not in (None, ""):
            return value
    return None


def resolve_optional_path(raw: Any, base_path: Optional[Path]) -> Optional[Path]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute() and base_path is not None:
        path = base_path.parent / path
    return path.resolve()


def discover_evidence_path(explicit: str, metadata: Dict[str, Any], metadata_path: Path) -> Dict[str, Any]:
    explicit_text = explicit.strip()
    if explicit_text:
        raw: Any = explicit_text
        source = "argument"
        path = Path(explicit_text).expanduser().resolve()
    else:
        raw = first_metadata_value(
            metadata,
            [
                ("BoundaryProtocol", "SourceEvidenceFile"),
                ("BoundaryProtocol", "SourceEvidenceJson"),
                ("BoundaryProtocol", "EvidenceJson"),
                ("BoundaryProtocol", "source_evidence_file"),
                ("BoundaryProtocol", "source_evidence_json"),
                ("BoundaryEvidenceJson",),
                ("BoundaryProtocolEvidenceJson",),
            ],
        )
        source = "metadata" if raw not in (None, "") else "missing"
        path = resolve_optional_path(raw, metadata_path)
    return {
        "source": source,
        "raw": str(raw) if raw not in (None, "") else "",
        "path": str(path) if path else "",
        "exists": bool(path and path.exists()),
    }


def non_empty(mapping: Dict[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def missing_fields(mapping: Dict[str, Any], fields: Iterable[str]) -> List[str]:
    return [field for field in fields if not non_empty(mapping, field)]


def first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def evidence_float(
    evidence: Dict[str, Any],
    key: str,
    metadata: Dict[str, Any],
    *metadata_keys: str,
) -> Optional[float]:
    parsed = as_float(evidence.get(key))
    if parsed is not None:
        return parsed
    return as_float(nested(metadata, *metadata_keys))


def binary_stl_bounds(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "is_binary_stl": False, "triangle_count": 0, "bounds": None, "extents": None}
    data = path.read_bytes()
    if len(data) < 84:
        return {"exists": True, "is_binary_stl": False, "triangle_count": 0, "bounds": None, "extents": None}
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    if triangle_count <= 0 or expected_size != len(data):
        return {"exists": True, "is_binary_stl": False, "triangle_count": triangle_count, "bounds": None, "extents": None}
    mins = [math.inf, math.inf, math.inf]
    maxs = [-math.inf, -math.inf, -math.inf]
    offset = 84
    for _ in range(triangle_count):
        offset += 12
        for _vertex in range(3):
            x, y, z = struct.unpack_from("<fff", data, offset)
            offset += 12
            for axis, value in enumerate((x, y, z)):
                mins[axis] = min(mins[axis], float(value))
                maxs[axis] = max(maxs[axis], float(value))
        offset += 2
    if not all(math.isfinite(value) for value in mins + maxs):
        return {"exists": True, "is_binary_stl": True, "triangle_count": triangle_count, "bounds": None, "extents": None}
    extents = {axis: maxs[index] - mins[index] for index, axis in enumerate(("X", "Y", "Z"))}
    bounds = {
        "MinX": mins[0],
        "MinY": mins[1],
        "MinZ": mins[2],
        "MaxX": maxs[0],
        "MaxY": maxs[1],
        "MaxZ": maxs[2],
    }
    return {
        "exists": True,
        "is_binary_stl": True,
        "triangle_count": triangle_count,
        "bounds": bounds,
        "extents": extents,
        "height": extents["Z"],
    }


def boundary_audit_with_stl_fallback(run_dir: Path, boundary_audit: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    stl = binary_stl_bounds(run_dir / "buildings.stl")
    updated = dict(boundary_audit)
    fallback: Dict[str, Any] = {
        "used": False,
        "source": "buildings.stl",
        "stl": stl,
        "computed_clearance_by_h": {},
        "computed_frontal_blockage_ratio": None,
    }
    extents = stl.get("extents") if isinstance(stl.get("extents"), dict) else {}
    height = as_float(stl.get("height"))
    clearance_m = boundary_audit.get("ClearanceM") if isinstance(boundary_audit.get("ClearanceM"), dict) else {}
    if height is not None and height > 0.0 and clearance_m:
        clearance_by_h = dict(boundary_audit.get("ClearanceByBuildingHeight") or {})
        mappings = {
            "Upstream": "Upstream",
            "Downstream": "Downstream",
            "MinLateral": "MinLateral",
            "Top": "Top",
        }
        for out_key, clearance_key in mappings.items():
            current = as_float(clearance_by_h.get(out_key))
            clearance_value = as_float(clearance_m.get(clearance_key))
            if current is None and clearance_value is not None:
                clearance_by_h[out_key] = clearance_value / height
                fallback["computed_clearance_by_h"][out_key] = clearance_by_h[out_key]
        if fallback["computed_clearance_by_h"]:
            updated["ClearanceByBuildingHeight"] = clearance_by_h
            fallback["used"] = True

    domain_size = boundary_audit.get("DomainSizeM") if isinstance(boundary_audit.get("DomainSizeM"), dict) else {}
    blockage = dict(boundary_audit.get("BlockageDiagnostics") or {})
    frontal_current = as_float(blockage.get("ApproxFrontalBlockageRatio"))
    dominant_axis = str(boundary_audit.get("DominantAxis") or "X").strip().upper()
    if extents and domain_size and (frontal_current is None or frontal_current <= 0.0):
        if dominant_axis == "X":
            building_a = as_float(extents.get("Y"))
            building_b = as_float(extents.get("Z"))
            inlet_a = as_float(domain_size.get("Y"))
            inlet_b = as_float(domain_size.get("Z"))
        elif dominant_axis == "Y":
            building_a = as_float(extents.get("X"))
            building_b = as_float(extents.get("Z"))
            inlet_a = as_float(domain_size.get("X"))
            inlet_b = as_float(domain_size.get("Z"))
        else:
            building_a = as_float(extents.get("X"))
            building_b = as_float(extents.get("Y"))
            inlet_a = as_float(domain_size.get("X"))
            inlet_b = as_float(domain_size.get("Y"))
        building_frontal = building_a * building_b if building_a is not None and building_b is not None else None
        inlet_area = inlet_a * inlet_b if inlet_a is not None and inlet_b is not None else None
        if building_frontal is not None and inlet_area is not None and inlet_area > 0.0:
            blockage["BuildingFrontalAreaM2"] = building_frontal
            blockage["InletFaceAreaM2"] = inlet_area
            blockage["ApproxFrontalBlockageRatio"] = building_frontal / inlet_area
            updated["BlockageDiagnostics"] = blockage
            fallback["computed_frontal_blockage_ratio"] = blockage["ApproxFrontalBlockageRatio"]
            fallback["used"] = True

    return updated, fallback


def combined_evidence(
    evidence: Dict[str, Any],
    boundary_audit: Dict[str, Any],
) -> Dict[str, Any]:
    combined = dict(evidence)
    fallback_pairs = {
        "inlet_fetch_clearance_h": ("ClearanceByBuildingHeight", "Upstream"),
        "downstream_clearance_h": ("ClearanceByBuildingHeight", "Downstream"),
        "min_lateral_clearance_h": ("ClearanceByBuildingHeight", "MinLateral"),
        "top_clearance_h": ("ClearanceByBuildingHeight", "Top"),
    }
    for key, metadata_keys in fallback_pairs.items():
        if not non_empty(combined, key):
            value = nested(boundary_audit, *metadata_keys)
            if value is not None:
                combined[key] = value
    return combined


def equivalence_supported(*values: Any) -> bool:
    text = " ".join(str(value or "").lower() for value in values)
    return any(token in text for token in BOUNDARY_EQUIVALENCE_TOKENS)


def condition_supported(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    if any(token in text for token in UNSUPPORTED_CONDITION_TOKENS):
        return False
    return any(token in text for token in SUPPORTED_CONDITION_TOKENS)


def condition_support_map(evidence: Dict[str, Any]) -> Dict[str, bool]:
    return {field: condition_supported(evidence.get(field)) for field in CONDITION_SUPPORT_FIELDS}


def identity_token(value: Any) -> str:
    return "".join(char.lower() for char in str(value or "").strip() if char.isalnum())


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]


def resolve_evidence_files(paths: List[str], evidence_path: Optional[Path], run_dir: Path) -> Dict[str, Any]:
    base_dirs: List[Path] = []
    if evidence_path is not None:
        base_dirs.append(evidence_path.parent)
    base_dirs.append(run_dir)

    resolved: List[str] = []
    missing: List[str] = []
    hashed: List[Dict[str, Any]] = []
    unreadable: List[str] = []
    empty: List[str] = []
    for raw_path in paths:
        candidate = Path(raw_path).expanduser()
        candidates = [candidate] if candidate.is_absolute() else [base / candidate for base in base_dirs]
        existing = next((path for path in candidates if path.exists()), None)
        if existing is None:
            missing.append(raw_path)
        else:
            resolved_path = existing.resolve()
            resolved_text = str(resolved_path)
            resolved.append(resolved_text)
            try:
                content = resolved_path.read_bytes()
            except OSError:
                unreadable.append(resolved_text)
                continue
            size = len(content)
            if size <= 0:
                empty.append(resolved_text)
            hashed.append(
                {
                    "path": resolved_text,
                    "size_bytes": size,
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    all_hashed = bool(paths) and not missing and not unreadable and not empty and len(hashed) == len(paths)
    return {
        "resolved": resolved,
        "missing": missing,
        "unreadable": unreadable,
        "empty": empty,
        "sha256": hashed,
        "all_exist": bool(paths) and not missing,
        "all_hashed": all_hashed,
    }


def sha256_file(path: Optional[Path]) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    if not metadata_path.exists():
        raise SystemExit(f"metadata does not exist: {metadata_path}")

    metadata = read_json(metadata_path)
    evidence_discovery = discover_evidence_path(args.evidence, metadata, metadata_path)
    evidence_path = Path(evidence_discovery["path"]) if evidence_discovery["path"] else None
    if args.evidence and evidence_path is not None and not evidence_path.exists():
        raise SystemExit(f"evidence does not exist: {evidence_path}")
    evidence = read_json(evidence_path)
    metadata_sha = sha256_file(metadata_path)
    raw_boundary_audit = metadata.get("BoundaryProtocolAudit") if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    boundary_audit, stl_boundary_fallback = boundary_audit_with_stl_fallback(run_dir, raw_boundary_audit)
    blockage_audit = nested(boundary_audit, "BlockageDiagnostics") or {}
    frontal_blockage = as_float(nested(blockage_audit, "ApproxFrontalBlockageRatio"))
    if frontal_blockage is None:
        frontal_blockage = as_float(nested(metadata, "BoundaryProtocol", "BlockageEstimate", "ratio"))
    metadata_gate = first_non_empty(boundary_audit.get("Gate"), metadata.get("BoundaryProtocolGate"))
    metadata_evidence_gate = first_non_empty(
        boundary_audit.get("ProtocolEvidenceGate"),
        metadata.get("BoundaryProtocolEvidenceGate"),
    ).lower()
    metadata_evidence_source = first_non_empty(
        boundary_audit.get("ProtocolEvidenceSource"),
        metadata.get("BoundaryProtocolEvidenceSource"),
    )

    combined = combined_evidence(evidence, boundary_audit)
    missing = missing_fields(combined, REQUIRED_EVIDENCE_FIELDS)
    evidence_aij_case = first_non_empty(combined.get("aij_case"), evidence.get("case"))
    evidence_wind_direction = first_non_empty(combined.get("wind_direction"), evidence.get("wind_direction_label"))
    evidence_metadata_sha = first_non_empty(
        evidence.get("case_metadata_sha256"),
        evidence.get("metadata_sha256"),
        evidence.get("BoundaryProtocolMetadataSha256"),
    ).lower()
    metadata_sha_matches_current = bool(evidence_metadata_sha) and evidence_metadata_sha == metadata_sha.lower()
    expected_case = str(args.expected_aij_case or "").strip()
    expected_wind_direction = str(args.expected_wind_direction or "").strip()
    identity_reasons: List[str] = []
    if not evidence_metadata_sha:
        identity_reasons.append("case_metadata_sha256_missing")
    elif not metadata_sha_matches_current:
        identity_reasons.append("case_metadata_sha256_mismatch")
    if expected_case and identity_token(evidence_aij_case) != identity_token(expected_case):
        identity_reasons.append("aij_case_mismatch")
    if expected_wind_direction and identity_token(evidence_wind_direction) != identity_token(expected_wind_direction):
        identity_reasons.append("wind_direction_mismatch")
    run_identity_gate_pass = not identity_reasons
    explicit_gate = first_non_empty(
        evidence.get("boundary_evidence_gate"),
        evidence.get("BoundaryProtocolEvidenceGate"),
        evidence.get("gate"),
    ).lower()
    boundary_evidence_source = first_non_empty(
        evidence.get("boundary_evidence_source"),
        evidence.get("source"),
        metadata_evidence_source,
    )
    boundary_evidence_class = first_non_empty(
        evidence.get("boundary_evidence_class"),
        evidence.get("evidence_class"),
        evidence.get("boundary_evidence_type"),
    ).lower()
    evidence_files = as_list(
        evidence.get("boundary_evidence_files")
        or evidence.get("evidence_files")
        or evidence.get("supporting_files")
    )
    evidence_file_status = resolve_evidence_files(evidence_files, evidence_path, run_dir)
    boundary_equivalence_basis = first_non_empty(
        evidence.get("boundary_equivalence_basis"),
        metadata.get("BoundaryEquivalenceBasis"),
        boundary_audit.get("BoundaryEquivalenceBasis"),
    )
    boundary_equivalence_supported = equivalence_supported(boundary_equivalence_basis, boundary_evidence_source)
    boundary_evidence_class_supported = boundary_evidence_class in SUPPORTED_EVIDENCE_CLASSES
    condition_support = condition_support_map(combined)
    unsupported_conditions = [field for field, supported in condition_support.items() if not supported]
    boundary_condition_fields_supported = not unsupported_conditions
    upstream_clearance_h = evidence_float(
        evidence, "inlet_fetch_clearance_h", boundary_audit, "ClearanceByBuildingHeight", "Upstream"
    )
    downstream_clearance_h = evidence_float(
        evidence, "downstream_clearance_h", boundary_audit, "ClearanceByBuildingHeight", "Downstream"
    )
    lateral_clearance_h = evidence_float(
        evidence, "min_lateral_clearance_h", boundary_audit, "ClearanceByBuildingHeight", "MinLateral"
    )
    top_clearance_h = evidence_float(
        evidence, "top_clearance_h", boundary_audit, "ClearanceByBuildingHeight", "Top"
    )
    clearance_reasons: List[str] = []
    clearance_checks = [
        ("upstream_clearance_h", upstream_clearance_h, args.min_upstream_clearance_h),
        ("downstream_clearance_h", downstream_clearance_h, args.min_downstream_clearance_h),
        ("min_lateral_clearance_h", lateral_clearance_h, args.min_lateral_clearance_h),
        ("top_clearance_h", top_clearance_h, args.min_top_clearance_h),
    ]
    for name, value, minimum in clearance_checks:
        if value is None:
            clearance_reasons.append(f"{name}_missing")
        elif value < minimum:
            clearance_reasons.append(f"{name}_below_{minimum:g}")
    clearance_numeric_gate_pass = not clearance_reasons
    evidence_gate_pass = (
        explicit_gate == "pass"
        and not missing
        and boundary_equivalence_supported
        and boundary_evidence_class_supported
        and boundary_condition_fields_supported
        and evidence_file_status["all_hashed"]
        and clearance_numeric_gate_pass
        and run_identity_gate_pass
    )
    blockage_gate_pass = frontal_blockage is not None and frontal_blockage <= args.max_frontal_blockage_ratio
    clearance_gate_pass = metadata_gate == "diagnostic_clearance_ok_verify_against_aij" or clearance_numeric_gate_pass

    reasons: List[str] = []
    if not clearance_gate_pass and not metadata_gate:
        reasons.append("metadata_boundary_protocol_gate_missing")
    elif not clearance_gate_pass:
        reasons.append(f"metadata_boundary_protocol_gate_{metadata_gate}")
    if frontal_blockage is None:
        reasons.append("approx_frontal_blockage_ratio_missing")
    elif not blockage_gate_pass:
        reasons.append(f"approx_frontal_blockage_above_{args.max_frontal_blockage_ratio}")
    if not evidence_path:
        reasons.append("external_boundary_evidence_json_missing")
    elif not evidence_path.exists():
        reasons.append("external_boundary_evidence_json_not_found")
    if missing:
        reasons.append("missing_evidence_fields:" + ",".join(missing))
    if explicit_gate != "pass":
        reasons.append(f"boundary_evidence_gate_{explicit_gate or 'missing'}")
    if not boundary_equivalence_supported:
        reasons.append("boundary_equivalence_basis_missing_or_unsupported")
    if not boundary_evidence_class_supported:
        reasons.append(f"boundary_evidence_class_{boundary_evidence_class or 'missing'}_unsupported")
    if unsupported_conditions:
        reasons.append("unsupported_boundary_condition_fields:" + ",".join(unsupported_conditions))
    reasons.extend(identity_reasons)
    if not evidence_file_status["all_exist"]:
        if not evidence_files:
            reasons.append("boundary_evidence_files_missing")
        else:
            reasons.append("boundary_evidence_files_not_found:" + ",".join(evidence_file_status["missing"]))
    elif not evidence_file_status["all_hashed"]:
        if evidence_file_status["unreadable"]:
            reasons.append("boundary_evidence_files_unreadable:" + ",".join(evidence_file_status["unreadable"]))
        if evidence_file_status["empty"]:
            reasons.append("boundary_evidence_files_empty:" + ",".join(evidence_file_status["empty"]))
    reasons.extend(clearance_reasons)
    if metadata_evidence_gate and metadata_evidence_gate != "pass" and not evidence_gate_pass:
        reasons.append(f"metadata_boundary_evidence_gate_{metadata_evidence_gate}")

    boundary_protocol_gate = "pass" if clearance_gate_pass and blockage_gate_pass and evidence_gate_pass else "fail"
    if boundary_protocol_gate == "pass":
        development_stage = "eligible_for_short_native_canary"
        development_duration = "short_cfd"
        development_reason = "Boundary protocol evidence is bound to this run and passes AIJ-equivalent checks."
        development_runs_cfd_next = True
        development_next_cfd_scope = "short_native_canary_only"
    elif not run_identity_gate_pass:
        development_stage = "fix_boundary_protocol_identity_before_cfd"
        development_duration = "minutes"
        development_reason = "Boundary evidence is not bound to the current case metadata, AIJ case, or wind direction."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_boundary_protocol_identity_passes"
    elif not blockage_gate_pass or not clearance_gate_pass:
        development_stage = "fix_boundary_clearance_or_blockage_before_cfd"
        development_duration = "minutes"
        development_reason = "Domain clearance or blockage evidence is missing or outside the configured AIJ-equivalent threshold."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_clearance_and_blockage_pass"
    elif (
        explicit_gate != "pass"
        or missing
        or not boundary_equivalence_supported
        or not boundary_evidence_class_supported
        or not evidence_file_status["all_exist"]
        or not evidence_file_status["all_hashed"]
    ):
        development_stage = "resolve_boundary_protocol_evidence_before_cfd"
        development_duration = "minutes"
        development_reason = "Boundary evidence JSON is missing, draft, incomplete, unsupported, or lacks hashed support files."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_boundary_protocol_gate_passes"
    elif unsupported_conditions:
        development_stage = "replace_simplified_boundary_protocol_before_cfd"
        development_duration = "minutes"
        development_reason = "Boundary protocol evidence still contains simplified/free/slip/open labels that are not paper-grade."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_boundary_protocol_conditions_supported"
    else:
        development_stage = "resolve_boundary_protocol_evidence_before_cfd"
        development_duration = "minutes"
        development_reason = "Boundary evidence JSON is missing, draft, incomplete, unsupported, or lacks hashed support files."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_boundary_protocol_gate_passes"

    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_protocol_audit.v1",
        "generated_at_utc": utc_now(),
        "run_dir": str(run_dir),
        "metadata": str(metadata_path),
        "metadata_sha256": metadata_sha,
        "evidence_discovery": evidence_discovery,
        "evidence_path": str(evidence_path) if evidence_path else "",
        "boundary_evidence_json_sha256": sha256_file(evidence_path),
        "boundary_run_identity_gate": "pass" if run_identity_gate_pass else "fail",
        "boundary_run_identity_gate_reasons": identity_reasons or ["boundary_evidence_bound_to_current_run"],
        "expected_aij_case": expected_case,
        "expected_wind_direction": expected_wind_direction,
        "evidence_aij_case": evidence_aij_case,
        "evidence_wind_direction": evidence_wind_direction,
        "evidence_case_metadata_sha256": evidence_metadata_sha,
        "evidence_metadata_sha256_matches_current": metadata_sha_matches_current,
        "metadata_boundary_protocol_gate": metadata_gate,
        "metadata_boundary_evidence_gate": metadata_evidence_gate,
        "metadata_boundary_evidence_source": metadata_evidence_source,
        "stl_boundary_fallback": stl_boundary_fallback,
        "inlet_face": boundary_audit.get("InletFace", ""),
        "outlet_face": boundary_audit.get("OutletFace", ""),
        "lateral_faces": boundary_audit.get("LateralFaces", ""),
        "top_face": boundary_audit.get("TopFace", ""),
        "ground_face": boundary_audit.get("GroundFace", ""),
        "approx_frontal_blockage_ratio": frontal_blockage,
        "max_frontal_blockage_ratio": args.max_frontal_blockage_ratio,
        "blockage_gate": "pass" if blockage_gate_pass else "fail",
        "evidence_required_fields": REQUIRED_EVIDENCE_FIELDS,
        "missing_evidence_fields": missing,
        "boundary_equivalence_basis": boundary_equivalence_basis,
        "boundary_equivalence_supported": boundary_equivalence_supported,
        "boundary_evidence_class": boundary_evidence_class,
        "boundary_evidence_class_supported": boundary_evidence_class_supported,
        "supported_boundary_evidence_classes": sorted(SUPPORTED_EVIDENCE_CLASSES),
        "supported_boundary_condition_tokens": SUPPORTED_CONDITION_TOKENS,
        "unsupported_boundary_condition_tokens": UNSUPPORTED_CONDITION_TOKENS,
        "boundary_condition_fields_supported": boundary_condition_fields_supported,
        "boundary_condition_support_reasons": (
            ["boundary_condition_fields_supported"]
            if boundary_condition_fields_supported
            else ["unsupported_boundary_condition_fields:" + ",".join(unsupported_conditions)]
        ),
        "boundary_evidence_files": evidence_files,
        "boundary_evidence_files_resolved": evidence_file_status["resolved"],
        "boundary_evidence_files_missing": evidence_file_status["missing"],
        "boundary_evidence_files_unreadable": evidence_file_status["unreadable"],
        "boundary_evidence_files_empty": evidence_file_status["empty"],
        "boundary_evidence_files_sha256": evidence_file_status["sha256"],
        "boundary_evidence_files_all_exist": evidence_file_status["all_exist"],
        "boundary_evidence_files_all_hashed": evidence_file_status["all_hashed"],
        "inlet_fetch_clearance_h": upstream_clearance_h,
        "downstream_clearance_h": downstream_clearance_h,
        "min_lateral_clearance_h": lateral_clearance_h,
        "top_clearance_h": top_clearance_h,
        "min_required_upstream_clearance_h": args.min_upstream_clearance_h,
        "min_required_downstream_clearance_h": args.min_downstream_clearance_h,
        "min_required_lateral_clearance_h": args.min_lateral_clearance_h,
        "min_required_top_clearance_h": args.min_top_clearance_h,
        "clearance_numeric_gate": "pass" if clearance_numeric_gate_pass else "fail",
        "clearance_numeric_gate_reasons": clearance_reasons or ["clearance_numeric_evidence_complete"],
        "outlet_reflection_check": evidence.get("outlet_reflection_check", ""),
        "outlet_reflection_check_supported": condition_support["outlet_reflection_check"],
        "side_top_boundary_check": evidence.get("side_top_boundary_check", ""),
        "side_top_boundary_check_supported": condition_support["side_top_boundary_check"],
        "floor_roughness_source": evidence.get("floor_roughness_source", ""),
        "floor_roughness_source_supported": condition_support["floor_roughness_source"],
        "boundary_evidence_gate": "pass" if evidence_gate_pass else "fail",
        "boundary_evidence_source": boundary_evidence_source,
        "boundary_protocol_gate": boundary_protocol_gate,
        "boundary_protocol_gate_reasons": reasons or ["boundary_protocol_evidence_complete"],
        "development_acceleration_stage": development_stage,
        "development_acceleration_duration_class": development_duration,
        "development_acceleration_runs_cfd_next": development_runs_cfd_next,
        "development_acceleration_next_cfd_scope": development_next_cfd_scope,
        "development_acceleration_reason": development_reason,
        "long_cfd_allowed_by_boundary_protocol_audit": boundary_protocol_gate == "pass",
        "recommended_next_action": (
            "Archive an AIJ-equivalent boundary evidence JSON with inlet/outlet/lateral/top, "
            "ground roughness/no-slip treatment, blockage source and fetch/clearance source before "
            "claiming paper-grade validation."
        ),
    }

    for key in REQUIRED_EVIDENCE_FIELDS:
        report[key] = combined.get(key, "")
    for key in CONDITION_SUPPORT_FIELDS:
        report[f"{key}_supported"] = condition_support[key]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"boundary_protocol_gate={boundary_protocol_gate}; reasons={';'.join(report['boundary_protocol_gate_reasons'])}")
    return 0 if boundary_protocol_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
