#!/usr/bin/env python3
"""Create a traceable turbulence length-scale evidence template.

This helper is intentionally no-CFD. It turns the current synthetic-inlet
length-scale setting into an auditable evidence record and keeps diagnostic
user parameters separate from paper-grade official, precursor or calibrated
sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


SUPPORTED_SOURCE_TYPES = {
    "official_aij": "aij_length_scale_verified",
    "wind_tunnel_document": "official_length_scale_verified",
    "precursor": "precursor_length_scale",
    "recycling": "recycling_length_scale",
    "digital_filter_calibration": "digital_filter_length_scale",
    "synthetic_eddy_calibration": "synthetic_eddy_length_scale",
    "sem_calibration": "sem_length_scale",
    "literature": "validated_length_scale_model",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create turbulence_length_scale_evidence.json.")
    parser.add_argument("--metadata", default="", help="Current case_metadata.json.")
    parser.add_argument("--source-path", default="", help="Official, precursor or calibrated source file.")
    parser.add_argument(
        "--source-type",
        choices=sorted(SUPPORTED_SOURCE_TYPES),
        default="official_aij",
        help="Traceable basis for the length-scale evidence.",
    )
    parser.add_argument("--source-note", default="", help="Short note describing the source and extraction method.")
    parser.add_argument("--case", default="", help="Expected case label, e.g. CaseE.")
    parser.add_argument("--wind-direction", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument(
        "--paper-admissible",
        action="store_true",
        help="Mark the provided source as reviewed/admissible for paper-grade validation.",
    )
    parser.add_argument("--out", required=True, help="Output turbulence_length_scale_evidence.json.")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it exists.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def get_nested(data: Dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_value(metadata: Dict[str, Any], candidates: Sequence[Sequence[str]]) -> Any:
    for path in candidates:
        value = get_nested(metadata, *path)
        if value not in (None, ""):
            return value
    return None


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


def identity_token(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def metadata_case_text(metadata: Dict[str, Any]) -> str:
    return str(
        first_value(
            metadata,
            [
                ("AijCase",),
                ("AIJCase",),
                ("Case",),
                ("case",),
                ("CaseLabel",),
                ("case_label",),
            ],
        )
        or ""
    )


def metadata_wind_text(metadata: Dict[str, Any]) -> str:
    return str(
        first_value(
            metadata,
            [
                ("WindDirection",),
                ("WindDirectionLabel",),
                ("wind_direction",),
                ("wind_label",),
                ("inlet", "wind_label"),
                ("inlet", "wind_direction"),
            ],
        )
        or ""
    )


def resolve_path(raw: str) -> Optional[Path]:
    text = str(raw or "").strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def length_settings(metadata: Dict[str, Any]) -> Dict[str, Any]:
    corr_cells = as_float(
        first_value(
            metadata,
            [
                ("SyntheticTurbulenceCorrelationCells",),
                ("SyntheticTurbulentInlet", "CorrelationCells"),
                ("synthetic_turbulence", "correlation_cells"),
                ("inlet", "correlation_cells"),
            ],
        )
    )
    corr_m = as_float(
        first_value(
            metadata,
            [
                ("SyntheticTurbulenceCorrelationLengthM",),
                ("SyntheticTurbulentInlet", "CorrelationLengthM"),
                ("synthetic_turbulence", "correlation_length_m"),
                ("inlet", "correlation_length_m"),
            ],
        )
    )
    dx_m = as_float(
        first_value(
            metadata,
            [
                ("Dx",),
                ("DxM",),
                ("Grid", "Dx"),
                ("Grid", "DxM"),
                ("grid", "dx"),
                ("grid", "dx_m"),
            ],
        )
    )
    if corr_m is None and corr_cells is not None and dx_m is not None:
        corr_m = corr_cells * dx_m
    return {
        "correlation_cells": corr_cells,
        "dx_m": dx_m,
        "correlation_length_m": corr_m,
        "legacy_inlet_turbulence_length_h": as_float(get_nested(metadata, "inlet", "turbulence_length_h")),
        "digital_filter_radius_cells": as_float(get_nested(metadata, "inlet", "digital_filter_radius")),
        "digital_filter_alpha": as_float(get_nested(metadata, "inlet", "digital_filter_alpha")),
        "metadata_length_scale_source": str(
            first_value(
                metadata,
                [
                    ("SyntheticTurbulentInletLengthScaleSource",),
                    ("SyntheticTurbulenceLengthScaleSource",),
                    ("synthetic_turbulence", "length_scale_source"),
                    ("inlet", "length_scale_source"),
                ],
            )
            or ""
        ),
        "metadata_length_scale_gate": str(
            first_value(
                metadata,
                [
                    ("SyntheticTurbulentInletLengthScaleGate",),
                    ("SyntheticTurbulenceLengthScaleGate",),
                    ("synthetic_turbulence", "length_scale_gate"),
                    ("inlet", "length_scale_gate"),
                ],
            )
            or ""
        ),
    }


def build_evidence(args: argparse.Namespace) -> Dict[str, Any]:
    metadata_path = resolve_path(args.metadata)
    metadata = read_json(metadata_path)
    source_path = resolve_path(args.source_path)
    source_exists = bool(source_path and source_path.is_file())
    expected_case = identity_token(args.case)
    found_case = identity_token(metadata_case_text(metadata))
    expected_wind = identity_token(args.wind_direction)
    found_wind = identity_token(metadata_wind_text(metadata))
    settings = length_settings(metadata)

    reasons: List[str] = []
    warnings: List[str] = []
    if metadata_path and not metadata_path.is_file():
        reasons.append("metadata_file_missing")
    if expected_case and found_case and expected_case not in found_case:
        reasons.append("case_label_mismatch")
    if expected_wind and found_wind and expected_wind != found_wind:
        reasons.append("wind_direction_label_mismatch")
    if (
        settings["correlation_cells"] is None
        and settings["correlation_length_m"] is None
        and settings["legacy_inlet_turbulence_length_h"] is None
        and settings["digital_filter_radius_cells"] is None
    ):
        warnings.append("current_length_scale_parameter_not_found_in_metadata")
    if not source_path:
        reasons.append("length_scale_source_file_missing")
    elif not source_exists:
        reasons.append("length_scale_source_file_not_found")
    if not args.source_note.strip():
        warnings.append("source_note_missing")
    if not args.paper_admissible:
        reasons.append("paper_admissible_review_flag_missing")

    gate = "pass" if not reasons else "draft"
    source_tag = SUPPORTED_SOURCE_TYPES[args.source_type]
    return {
        "schema": "citylbm.turbulence_length_scale_evidence.v1",
        "generated_at": utc_now(),
        "gate": gate,
        "paper_grade_gate": "pass" if gate == "pass" else "fail",
        "reasons": reasons,
        "warnings": warnings,
        "source_type": args.source_type,
        "source_path": str(source_path) if source_path else "",
        "source_exists": source_exists,
        "source_sha256": sha256(source_path) if source_exists and source_path else "",
        "source_note": args.source_note.strip(),
        "case_expected": args.case,
        "case_from_metadata": metadata_case_text(metadata),
        "wind_direction_expected": args.wind_direction,
        "wind_direction_from_metadata": metadata_wind_text(metadata),
        "metadata_path": str(metadata_path) if metadata_path else "",
        "metadata_exists": bool(metadata_path and metadata_path.is_file()),
        "metadata_sha256": sha256(metadata_path) if metadata_path and metadata_path.is_file() else "",
        "current_length_scale_settings": settings,
        "suggested_citylbm_metadata_patch": {
            "SyntheticTurbulenceLengthScaleSource": source_tag,
            "SyntheticTurbulentInletLengthScaleSource": source_tag,
            "SyntheticTurbulentInletLengthScaleGate": "pass" if gate == "pass" else "diagnostic_only_missing_official_or_precursor_length_scale",
            "TurbulenceLengthScaleEvidenceJson": str(Path(args.out).expanduser().resolve()),
        },
        "instructions": [
            "Keep this file with the case preflight evidence.",
            "For paper-grade runs, bind the suggested CityLBM metadata patch only after the source file is official, precursor-based or calibrated and paper_admissible is true.",
            "Do not treat a user-selected lattice-cell correlation length as publication evidence without this traceable source.",
        ],
    }


def main() -> int:
    args = parse_args()
    out = Path(args.out).expanduser().resolve()
    if out.exists() and not args.force:
        raise SystemExit(f"Output exists; use --force to overwrite: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_evidence(args), indent=2), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
