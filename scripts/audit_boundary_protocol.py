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
    "missing",
    "none",
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
    evidence_path = Path(args.evidence).expanduser().resolve() if args.evidence else None
    out_path = Path(args.out).expanduser().resolve()

    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    if not metadata_path.exists():
        raise SystemExit(f"metadata does not exist: {metadata_path}")
    if evidence_path is not None and not evidence_path.exists():
        raise SystemExit(f"evidence does not exist: {evidence_path}")

    metadata = read_json(metadata_path)
    evidence = read_json(evidence_path)
    boundary_audit = metadata.get("BoundaryProtocolAudit") if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    blockage_audit = nested(boundary_audit, "BlockageDiagnostics") or {}
    frontal_blockage = as_float(nested(blockage_audit, "ApproxFrontalBlockageRatio"))
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
    )
    blockage_gate_pass = frontal_blockage is not None and frontal_blockage <= args.max_frontal_blockage_ratio
    clearance_gate_pass = metadata_gate == "diagnostic_clearance_ok_verify_against_aij"

    reasons: List[str] = []
    if not metadata_gate:
        reasons.append("metadata_boundary_protocol_gate_missing")
    elif not clearance_gate_pass:
        reasons.append(f"metadata_boundary_protocol_gate_{metadata_gate}")
    if frontal_blockage is None:
        reasons.append("approx_frontal_blockage_ratio_missing")
    elif not blockage_gate_pass:
        reasons.append(f"approx_frontal_blockage_above_{args.max_frontal_blockage_ratio}")
    if not evidence_path:
        reasons.append("external_boundary_evidence_json_missing")
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
    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_protocol_audit.v1",
        "generated_at_utc": utc_now(),
        "run_dir": str(run_dir),
        "metadata": str(metadata_path),
        "metadata_sha256": sha256_file(metadata_path),
        "evidence_path": str(evidence_path) if evidence_path else "",
        "boundary_evidence_json_sha256": sha256_file(evidence_path),
        "metadata_boundary_protocol_gate": metadata_gate,
        "metadata_boundary_evidence_gate": metadata_evidence_gate,
        "metadata_boundary_evidence_source": metadata_evidence_source,
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
