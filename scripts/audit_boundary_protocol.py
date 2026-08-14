#!/usr/bin/env python3
"""Audit AIJ boundary-condition evidence for CityLBM/FluidX3D validation.

This script does not judge CFD accuracy. It checks whether a completed run has
enough traceable boundary, blockage, fetch and roughness evidence before the
numeric metrics can be treated as paper-grade AIJ validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


REQUIRED_EVIDENCE_FIELDS = [
    "aij_case",
    "wind_direction",
    "inlet_boundary",
    "outlet_boundary",
    "lateral_boundary",
    "top_boundary",
    "ground_wall_treatment",
    "roughness_treatment",
    "blockage_source",
    "fetch_clearance_source",
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

    missing = missing_fields(evidence, REQUIRED_EVIDENCE_FIELDS)
    explicit_gate = first_non_empty(
        evidence.get("boundary_evidence_gate"),
        evidence.get("BoundaryProtocolEvidenceGate"),
        evidence.get("gate"),
    ).lower()
    evidence_gate_pass = explicit_gate == "pass" and not missing
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
    if metadata_evidence_gate and metadata_evidence_gate != "pass" and not evidence_gate_pass:
        reasons.append(f"metadata_boundary_evidence_gate_{metadata_evidence_gate}")

    boundary_protocol_gate = "pass" if clearance_gate_pass and blockage_gate_pass and evidence_gate_pass else "fail"
    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_protocol_audit.v1",
        "generated_at_utc": utc_now(),
        "run_dir": str(run_dir),
        "metadata": str(metadata_path),
        "evidence_path": str(evidence_path) if evidence_path else "",
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
        "boundary_evidence_gate": "pass" if evidence_gate_pass else "fail",
        "boundary_evidence_source": first_non_empty(
            evidence.get("boundary_evidence_source"),
            evidence.get("source"),
            metadata_evidence_source,
        ),
        "boundary_protocol_gate": boundary_protocol_gate,
        "boundary_protocol_gate_reasons": reasons or ["boundary_protocol_evidence_complete"],
        "recommended_next_action": (
            "Archive an AIJ-equivalent boundary evidence JSON with inlet/outlet/lateral/top, "
            "ground roughness/no-slip treatment, blockage source and fetch/clearance source before "
            "claiming paper-grade validation."
        ),
    }

    for key in REQUIRED_EVIDENCE_FIELDS:
        report[key] = evidence.get(key, "")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"boundary_protocol_gate={boundary_protocol_gate}; reasons={';'.join(report['boundary_protocol_gate_reasons'])}")
    return 0 if boundary_protocol_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
