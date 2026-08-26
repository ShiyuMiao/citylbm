#!/usr/bin/env python3
"""Bind turbulence length-scale evidence identity into case_metadata.json."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bind turbulence length-scale evidence into case metadata.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json to update.")
    parser.add_argument("--evidence-json", required=True, help="turbulence_length_scale_evidence.json.")
    parser.add_argument(
        "--quality",
        default="diagnostic_template_not_paper_grade",
        help="Evidence quality label. Use paper_grade only after the evidence JSON gate passes.",
    )
    parser.add_argument("--source-note", default="", help="Short provenance note stored in metadata.")
    parser.add_argument("--out", default="", help="Write updated metadata to this path instead of modifying in place.")
    parser.add_argument("--in-place", action="store_true", help="Modify the metadata file in place.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, label: str) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to read {label} JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} root must be a JSON object: {path}")
    return data


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def output_path(args: argparse.Namespace, metadata_path: Path) -> Path:
    if args.out:
        return Path(args.out).expanduser().resolve()
    if args.in_place:
        return metadata_path
    raise SystemExit("refusing to modify metadata without --in-place or --out")


def evidence_is_paper_grade(evidence: Dict[str, Any]) -> bool:
    gate = str(evidence.get("gate") or "").strip().lower()
    paper_gate = str(evidence.get("paper_grade_gate") or "").strip().lower()
    return gate == "pass" and paper_gate == "pass" and bool(str(evidence.get("source_sha256") or "").strip())


def main() -> int:
    args = parse_args()
    metadata_path = Path(args.metadata).expanduser().resolve()
    evidence_json = Path(args.evidence_json).expanduser().resolve()
    if not metadata_path.is_file():
        raise SystemExit(f"metadata not found: {metadata_path}")
    if not evidence_json.is_file():
        raise SystemExit(f"evidence JSON not found: {evidence_json}")
    out_path = output_path(args, metadata_path)

    metadata = read_json(metadata_path, "metadata")
    evidence = read_json(evidence_json, "length-scale evidence")
    evidence_hash = sha256_file(evidence_json)
    paper_grade = evidence_is_paper_grade(evidence)
    quality = str(args.quality).strip() or "diagnostic_template_not_paper_grade"
    if paper_grade and quality == "diagnostic_template_not_paper_grade":
        quality = "paper_grade"
    source_tag = str(
        (evidence.get("suggested_citylbm_metadata_patch") or {}).get("SyntheticTurbulenceLengthScaleSource")
        or evidence.get("source_type")
        or ""
    ).strip()
    gate = "pass" if paper_grade and quality in {"paper_grade", "ready_for_validation_run"} else "diagnostic_only"

    metadata.setdefault("TurbulenceLengthScale", {})
    if not isinstance(metadata["TurbulenceLengthScale"], dict):
        raise SystemExit("metadata TurbulenceLengthScale exists but is not an object")
    metadata["TurbulenceLengthScale"].update(
        {
            "EvidenceJsonPath": str(evidence_json),
            "EvidenceJsonSha256": evidence_hash,
            "EvidenceQuality": quality,
            "EvidenceGate": gate,
            "EvidenceBoundAtUtc": utc_now(),
            "SourceTag": source_tag,
            "SourceNote": str(args.source_note or "").strip()
            or "Identity binding only; paper-grade status requires a passing length-scale evidence JSON.",
        }
    )
    metadata["TurbulenceLengthScaleEvidenceJson"] = str(evidence_json)
    metadata["TurbulenceLengthScaleEvidenceSha256"] = evidence_hash
    metadata["SyntheticTurbulenceLengthScaleSource"] = source_tag
    metadata["SyntheticTurbulentInletLengthScaleSource"] = source_tag
    metadata["SyntheticTurbulentInletLengthScaleGate"] = "pass" if gate == "pass" else "diagnostic_only"

    write_json(out_path, metadata)
    print(f"metadata_turbulence_length_scale_bound={out_path}")
    print(f"evidence_json_sha256={evidence_hash}")
    print(f"evidence_gate={gate}")
    print(f"evidence_quality={quality}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
