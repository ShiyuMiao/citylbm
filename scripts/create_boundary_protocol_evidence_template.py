#!/usr/bin/env python3
"""Create a run-bound boundary protocol evidence template.

The template is intentionally not a passing evidence file. It binds the draft
to the current case_metadata.json hash and lists every field required by
audit_boundary_protocol.py, so the remaining work is to replace the TODO values
with traceable AIJ/empty-tunnel/precursor evidence instead of hand-writing the
schema from memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a boundary protocol evidence JSON template.")
    parser.add_argument("run_dir", help="Case root directory.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json to bind this template to.")
    parser.add_argument("--out", required=True, help="Output boundary evidence template JSON.")
    parser.add_argument("--case", default="", help="AIJ case label, for example CaseA or CaseE.")
    parser.add_argument("--wind-direction", default="standard", help="Wind-direction label. Use N for Case E ac+N.")
    parser.add_argument(
        "--supporting-file",
        action="append",
        default=[],
        help="Traceable support file path to list in boundary_evidence_files. Repeat as needed.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def supporting_file_record(raw_path: str) -> Dict[str, Any]:
    path = Path(raw_path).expanduser().resolve()
    record: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": 0,
        "sha256": "",
    }
    if path.exists() and path.is_file():
        content = path.read_bytes()
        record["size_bytes"] = len(content)
        record["sha256"] = hashlib.sha256(content).hexdigest()
    return record


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def numeric_first(*values: Any) -> Optional[float]:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def format_float(value: Optional[float]) -> Any:
    return "" if value is None else value


def metadata_boundary_text(metadata: Dict[str, Any], boundary: str) -> str:
    treatment = nested(metadata, "BoundaryProtocol", "Treatment", boundary)
    if treatment:
        return f"TODO: verify source for metadata treatment: {treatment}"
    return "TODO: document AIJ-equivalent boundary treatment with source and hash"


def clearance_value(metadata: Dict[str, Any], *paths: Iterable[str]) -> Optional[float]:
    for path in paths:
        value = numeric_first(nested(metadata, *path))
        if value is not None:
            return value
    return None


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    if not metadata_path.exists():
        raise SystemExit(f"metadata does not exist: {metadata_path}")
    if out_path.exists() and not args.force:
        raise SystemExit(f"output exists, use --force to overwrite: {out_path}")

    metadata = read_json(metadata_path)
    boundary_audit = metadata.get("BoundaryProtocolAudit") if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    case_label = first_non_empty(args.case, metadata.get("Case"), metadata.get("AIJCase"), "TODO")
    wind_direction = first_non_empty(args.wind_direction, metadata.get("WindDirection"), "standard")
    upstream = clearance_value(
        metadata,
        ("BoundaryProtocolAudit", "ClearanceByBuildingHeight", "Upstream"),
        ("BoundaryProtocol", "DomainExtensionsInH", "upstream"),
    )
    downstream = clearance_value(
        metadata,
        ("BoundaryProtocolAudit", "ClearanceByBuildingHeight", "Downstream"),
        ("BoundaryProtocol", "DomainExtensionsInH", "downstream"),
    )
    lateral = clearance_value(
        metadata,
        ("BoundaryProtocolAudit", "ClearanceByBuildingHeight", "MinLateral"),
        ("BoundaryProtocol", "DomainExtensionsInH", "lateral_each_side"),
    )
    top = clearance_value(
        metadata,
        ("BoundaryProtocolAudit", "ClearanceByBuildingHeight", "Top"),
        ("BoundaryProtocol", "DomainExtensionsInH", "top_above_model"),
    )
    blockage = numeric_first(
        nested(boundary_audit, "BlockageDiagnostics", "ApproxFrontalBlockageRatio"),
        nested(metadata, "BoundaryProtocol", "BlockageEstimate", "ratio"),
    )

    payload: Dict[str, Any] = {
        "schema": "citylbm.boundary_protocol_evidence.v1",
        "generated_at_utc": utc_now(),
        "template_status": "draft_not_validated",
        "boundary_evidence_gate": "draft",
        "boundary_evidence_class": "TODO: one of official_aij_documentation, wind_tunnel_protocol_matched, empty_tunnel_boundary_preservation, precursor_boundary, recycling_boundary, validated_boundary_model",
        "boundary_evidence_source": "TODO: cite official AIJ document, empty-tunnel report, precursor report, or validated boundary model",
        "boundary_evidence_files": [str(item) for item in args.supporting_file],
        "boundary_evidence_file_records": [supporting_file_record(item) for item in args.supporting_file],
        "case_metadata_sha256": sha256_file(metadata_path),
        "case_metadata_path": str(metadata_path),
        "aij_case": case_label,
        "wind_direction": wind_direction,
        "boundary_equivalence_basis": "TODO: use a supported basis such as wind_tunnel_protocol_matched, empty_tunnel_passed, precursor_boundary, recycling_boundary, or validated_boundary_model",
        "inlet_boundary": metadata_boundary_text(metadata, "inlet"),
        "outlet_boundary": metadata_boundary_text(metadata, "outlet"),
        "lateral_boundary": metadata_boundary_text(metadata, "sides"),
        "top_boundary": metadata_boundary_text(metadata, "top"),
        "ground_wall_treatment": "TODO: document no-slip, rough-wall, roughness blocks, wall function, or validated surrogate with source",
        "roughness_treatment": "TODO: document AIJ roughness/spire/fence/precursor treatment; do not use assumed_only",
        "floor_roughness_source": "TODO: source path/hash for roughness layout or explicit source saying not applicable",
        "blockage_source": f"TODO: verify blockage against source; metadata_estimate={blockage}" if blockage is not None else "TODO: provide blockage source",
        "fetch_clearance_source": "TODO: source for upstream/downstream/lateral/top clearance and wind-tunnel equivalence",
        "inlet_fetch_clearance_h": format_float(upstream),
        "downstream_clearance_h": format_float(downstream),
        "min_lateral_clearance_h": format_float(lateral),
        "top_clearance_h": format_float(top),
        "outlet_reflection_check": "TODO: provide non_reflecting_checked or reflection_checked evidence with source/hash",
        "side_top_boundary_check": "TODO: provide side/top boundary equivalence or reflection check evidence with source/hash",
        "draft_next_steps": [
            "Replace every TODO with a source-backed statement containing supported audit tokens.",
            "Add every cited source file to boundary_evidence_files.",
            "Run audit_boundary_protocol.py with this evidence file; paper use requires boundary_protocol_gate=pass.",
            "Do not treat this template as validation evidence while boundary_evidence_gate is draft.",
        ],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"wrote boundary evidence template: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
