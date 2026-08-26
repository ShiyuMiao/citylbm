#!/usr/bin/env python3
"""Bind inlet Reynolds-stress evidence files to case_metadata.json.

This command is intentionally narrow: it records file identity and provenance
so preflight audits can distinguish "not bound to this case" from "bound but
not yet paper-grade". It does not promote template data to validation evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bind Reynolds-stress evidence identity into case metadata.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json to update.")
    parser.add_argument("--stress-csv", required=True, help="Reynolds-stress tensor CSV evidence or template.")
    parser.add_argument(
        "--quality",
        default="diagnostic_template_not_paper_grade",
        help="Evidence quality label to write. Use paper_grade only for independently audited full-tensor evidence.",
    )
    parser.add_argument("--source-note", default="", help="Short provenance note stored in metadata.")
    parser.add_argument("--out", default="", help="Write updated metadata to this path instead of modifying in place.")
    parser.add_argument("--in-place", action="store_true", help="Modify the metadata file in place.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to read metadata JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"metadata root must be a JSON object: {path}")
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


def main() -> int:
    args = parse_args()
    metadata_path = Path(args.metadata).expanduser().resolve()
    stress_csv = Path(args.stress_csv).expanduser().resolve()
    if not metadata_path.is_file():
        raise SystemExit(f"metadata not found: {metadata_path}")
    if not stress_csv.is_file():
        raise SystemExit(f"stress CSV not found: {stress_csv}")
    out_path = output_path(args, metadata_path)

    metadata = read_json(metadata_path)
    metadata.setdefault("InletReynoldsStress", {})
    if not isinstance(metadata["InletReynoldsStress"], dict):
        raise SystemExit("metadata InletReynoldsStress exists but is not an object")

    metadata["InletReynoldsStress"].update(
        {
            "TensorCsvPath": str(stress_csv),
            "TensorCsvSha256": sha256_file(stress_csv),
            "EvidenceQuality": str(args.quality).strip() or "diagnostic_template_not_paper_grade",
            "EvidenceBoundAtUtc": utc_now(),
            "SourceNote": str(args.source_note or "").strip()
            or "Identity binding only; paper-grade status still requires full tensor or precursor audit.",
        }
    )
    metadata["InletReynoldsStressTensorCsvSha256"] = metadata["InletReynoldsStress"]["TensorCsvSha256"]
    write_json(out_path, metadata)
    print(f"metadata_reynolds_stress_bound={out_path}")
    print(f"tensor_csv_sha256={metadata['InletReynoldsStress']['TensorCsvSha256']}")
    print(f"evidence_quality={metadata['InletReynoldsStress']['EvidenceQuality']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
