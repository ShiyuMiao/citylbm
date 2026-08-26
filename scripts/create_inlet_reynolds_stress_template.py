#!/usr/bin/env python3
"""Create draft inlet Reynolds-stress evidence templates.

This command does not create paper-grade evidence. It writes a full-tensor CSV
with the required columns and optional height rows from the AF profile, plus a
draft precursor JSON. Blank tensor components and draft precursor gates are
intentional so the audit cannot pass until traceable measured/precursor values
are provided.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


TENSOR_COLUMNS = ["z", "R11", "R22", "R33", "R12", "R13", "R23", "source_note"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create inlet Reynolds-stress template files.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json to bind this template to.")
    parser.add_argument("--af-csv", default="", help="Optional AF CSV used only to copy z rows.")
    parser.add_argument("--out-csv", required=True, help="Output measured/precursor tensor CSV template.")
    parser.add_argument("--out-precursor-json", default="", help="Optional output precursor evidence JSON template.")
    parser.add_argument("--case", default="", help="AIJ case label.")
    parser.add_argument("--wind-direction", default="", help="Wind-direction label.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
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


def normalize(value: str) -> str:
    return "".join(char for char in str(value).lower() if char.isalnum())


def pick_column(fieldnames: Sequence[str], candidates: Iterable[str]) -> str:
    lookup = {normalize(name): name for name in fieldnames}
    for candidate in candidates:
        match = lookup.get(normalize(candidate))
        if match:
            return match
    return ""


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed


def read_af_template_rows(path: Optional[Path]) -> List[Dict[str, str]]:
    if path is None or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
        u_rms_col = pick_column(fieldnames, ["u_rms", "u_rms(m/s)", "urms", "uprime_rms", "u_prime_rms"])
        v_rms_col = pick_column(fieldnames, ["v_rms", "v_rms(m/s)", "vrms", "vprime_rms", "v_prime_rms"])
        w_rms_col = pick_column(fieldnames, ["w_rms", "w_rms(m/s)", "wrms", "wprime_rms", "w_prime_rms"])
        if not z_col:
            return []
        has_rms = bool(u_rms_col and v_rms_col and w_rms_col)
        rows: List[Dict[str, str]] = []
        for row in reader:
            z = str(row.get(z_col, "")).strip()
            if z:
                template_row = {
                    "z": z,
                    "R11": "",
                    "R22": "",
                    "R33": "",
                    "R12": "",
                    "R13": "",
                    "R23": "",
                    "source_note": "TODO: replace blanks with measured or precursor-derived Reynolds stresses in m2/s2",
                }
                if has_rms:
                    u_rms = as_float(row.get(u_rms_col))
                    v_rms = as_float(row.get(v_rms_col))
                    w_rms = as_float(row.get(w_rms_col))
                    if u_rms is not None and v_rms is not None and w_rms is not None:
                        template_row.update(
                            {
                                "R11": f"{max(0.0, u_rms * u_rms):.12g}",
                                "R22": f"{max(0.0, v_rms * v_rms):.12g}",
                                "R33": f"{max(0.0, w_rms * w_rms):.12g}",
                                "source_note": "R11/R22/R33 prefilled from AF measured u_rms/v_rms/w_rms; TODO: provide R12/R13/R23 from measured, precursor, or equivalent-inlet evidence",
                            }
                        )
                rows.append(template_row)
        return rows


def resolve_path(raw: str) -> Optional[Path]:
    text = raw.strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def ensure_can_write(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"output exists, use --force to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


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
    metadata_path = Path(args.metadata).expanduser().resolve()
    if not metadata_path.exists():
        raise SystemExit(f"metadata does not exist: {metadata_path}")
    metadata = read_json(metadata_path)
    af_path = resolve_path(args.af_csv)
    out_csv = Path(args.out_csv).expanduser().resolve()
    out_precursor = resolve_path(args.out_precursor_json)
    ensure_can_write(out_csv, args.force)
    if out_precursor is not None:
        ensure_can_write(out_precursor, args.force)

    template_rows = read_af_template_rows(af_path)
    if not template_rows:
        template_rows = [
            {
                "z": "TODO",
                "R11": "",
                "R22": "",
                "R33": "",
                "R12": "",
                "R13": "",
                "R23": "",
                "source_note": "TODO: replace blanks with measured or precursor-derived Reynolds stresses in m2/s2",
            }
        ]
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TENSOR_COLUMNS)
        writer.writeheader()
        for row in template_rows:
            writer.writerow(row)

    if out_precursor is not None:
        payload = {
            "schema": "citylbm.equivalent_precursor_evidence.v1",
            "generated_at_utc": utc_now(),
            "Gate": "draft",
            "PaperAdmissible": False,
            "case": first_non_empty(args.case, metadata.get("AijCase"), metadata.get("Case"), "TODO"),
            "wind_direction": first_non_empty(args.wind_direction, metadata.get("WindDirection"), ""),
            "case_metadata_sha256": sha256_file(metadata_path),
            "case_metadata_path": str(metadata_path),
            "SourceVtkSha256": "",
            "SourceProfileMonitorJson": "",
            "SourceMetadataJson": "",
            "source_turbulence_method": "TODO: digital-filter, SEM, precursor, or recycling-rescaling evidence",
            "source_boundary_mode": "TODO: document source boundary protocol",
            "draft_next_steps": [
                "Run or cite a passing empty-tunnel/precursor chain.",
                "Fill SourceVtkSha256 or equivalent source hash evidence.",
                "Set Gate=pass and PaperAdmissible=true only after independent audit passes.",
            ],
        }
        out_precursor.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"wrote inlet tensor template: {out_csv}")
    if out_precursor is not None:
        print(f"wrote precursor evidence template: {out_precursor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
