#!/usr/bin/env python3
"""Audit generated CustomProfile fidelity against the official AF CSV.

This is a cheap pre-CFD gate. It catches cases where a generated CityLBM or
native FluidX3D case only carries a simplified inlet profile while the
validation protocol expects the official AIJ AF z,U,k table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


PASS = "pass"
FAIL = "fail"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare case_metadata CustomProfile rows against an official AF CSV."
    )
    parser.add_argument("--metadata", required=True, help="case_metadata.json containing CustomProfile.")
    parser.add_argument("--af-csv", required=True, help="Official AF CSV with z,U and optional k/RMS columns.")
    parser.add_argument("--out-json", required=True, help="Output audit JSON.")
    parser.add_argument("--out-csv", help="Optional per-height comparison CSV.")
    parser.add_argument("--min-profile-rows", type=int, default=5)
    parser.add_argument("--min-overlap-af-rows", type=int, default=5)
    parser.add_argument("--max-u-mae-ratio", type=float, default=0.02)
    parser.add_argument("--max-k-mae-ratio", type=float, default=0.10)
    parser.add_argument("--max-k-rij-mae-ratio", type=float, default=0.10)
    parser.add_argument("--require-k", action="store_true")
    return parser.parse_args()


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_columns(columns: Sequence[str]) -> Dict[str, str]:
    return {"".join(ch for ch in column.lower() if ch.isalnum()): column for column in columns}


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def read_af_csv(path: Path) -> List[Dict[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"AF CSV has no rows: {path}")
    lookup = normalized_columns(list(rows[0].keys()))
    z_col = lookup.get("zm") or lookup.get("z")
    u_col = lookup.get("ums") or lookup.get("u") or lookup.get("velocity")
    k_col = lookup.get("km2s2") or lookup.get("k") or lookup.get("tke")
    urms_col = lookup.get("urmsms") or lookup.get("urms")
    vrms_col = lookup.get("vrmsms") or lookup.get("vrms")
    wrms_col = lookup.get("wrmsms") or lookup.get("wrms")
    if not z_col or not u_col:
        raise SystemExit("AF CSV must contain z and U columns.")
    samples: List[Dict[str, float]] = []
    for row in rows:
        z = as_float(row.get(z_col))
        u = as_float(row.get(u_col))
        if z is None or u is None:
            continue
        sample = {"z": z, "u": u}
        k = as_float(row.get(k_col)) if k_col else None
        if k is not None:
            sample["k"] = k
        urms = as_float(row.get(urms_col)) if urms_col else None
        vrms = as_float(row.get(vrms_col)) if vrms_col else None
        wrms = as_float(row.get(wrms_col)) if wrms_col else None
        if urms is not None and vrms is not None and wrms is not None:
            sample["k_from_rms"] = 0.5 * (urms * urms + vrms * vrms + wrms * wrms)
        samples.append(sample)
    samples.sort(key=lambda item: item["z"])
    if len(samples) < 2:
        raise SystemExit("AF CSV must contain at least two valid z/U samples.")
    return samples


def metadata_profile(metadata: Dict[str, Any]) -> List[Dict[str, float]]:
    raw = metadata.get("CustomProfile")
    if not isinstance(raw, list):
        return []
    profile: List[Dict[str, float]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        z = as_float(item.get("ZM") or item.get("z") or item.get("Z"))
        u = as_float(item.get("UMps") or item.get("U") or item.get("u"))
        if z is None or u is None:
            continue
        sample = {"z": z, "u": u}
        k = as_float(item.get("KM2s2") or item.get("K") or item.get("k"))
        if k is not None:
            sample["k"] = k
        r_values = [
            as_float(item.get("R11M2s2") or item.get("R11") or item.get("r11")),
            as_float(item.get("R22M2s2") or item.get("R22") or item.get("r22")),
            as_float(item.get("R33M2s2") or item.get("R33") or item.get("r33")),
        ]
        if all(value is not None for value in r_values):
            sample["k_from_rij"] = 0.5 * sum(float(value) for value in r_values)
        profile.append(sample)
    profile.sort(key=lambda row: row["z"])
    return profile


def interpolate(samples: Sequence[Dict[str, float]], key: str, z: float) -> Optional[float]:
    valid = [sample for sample in samples if key in sample]
    if not valid:
        return None
    if z <= valid[0]["z"]:
        return valid[0][key]
    if z >= valid[-1]["z"]:
        return valid[-1][key]
    for a, b in zip(valid, valid[1:]):
        if a["z"] <= z <= b["z"]:
            dz = b["z"] - a["z"]
            if abs(dz) <= 1.0e-12:
                return a[key]
            t = (z - a["z"]) / dz
            return a[key] + t * (b[key] - a[key])
    return None


def ratio_errors(rows: Sequence[Dict[str, float]], sim_key: str, ref_key: str) -> Dict[str, Any]:
    pairs = [(row[sim_key], row[ref_key]) for row in rows if sim_key in row and ref_key in row and row[ref_key] != 0.0]
    if not pairs:
        return {
            "count": 0,
            "mae_ratio": None,
            "rmse_ratio": None,
            "bias_ratio": None,
            "max_abs_ratio": None,
        }
    denom = sum(abs(ref) for _, ref in pairs) / len(pairs)
    if denom <= 1.0e-12:
        denom = 1.0
    diffs = [sim - ref for sim, ref in pairs]
    return {
        "count": len(pairs),
        "mae_ratio": sum(abs(diff) for diff in diffs) / len(diffs) / denom,
        "rmse_ratio": math.sqrt(sum(diff * diff for diff in diffs) / len(diffs)) / denom,
        "bias_ratio": sum(diffs) / len(diffs) / denom,
        "max_abs_ratio": max(abs(diff) for diff in diffs) / denom,
    }


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    columns = [
        "z",
        "custom_u",
        "af_u",
        "custom_k",
        "af_k",
        "custom_k_from_rij",
        "af_k_from_rms",
        "u_error",
        "k_error",
        "k_rij_error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def main() -> int:
    args = parse_args()
    metadata_path = Path(args.metadata)
    af_path = Path(args.af_csv)
    metadata = read_json(metadata_path)
    profile = metadata_profile(metadata)
    af_samples = read_af_csv(af_path)
    reasons: List[str] = []

    metadata_row_count = len(profile)
    metadata_declared_rows = as_int(metadata.get("CustomProfileRows"))
    af_row_count = len(af_samples)
    if metadata_row_count < 2:
        reasons.append("custom_profile_missing_or_too_few_rows")
    if metadata_declared_rows is not None and metadata_declared_rows != metadata_row_count:
        reasons.append("custom_profile_row_count_mismatch_metadata")
    if af_row_count >= args.min_profile_rows and metadata_row_count < args.min_profile_rows:
        reasons.append(
            f"custom_profile_rows_below_minimum:{metadata_row_count}<{args.min_profile_rows}"
        )

    overlap_rows: List[Dict[str, float]] = []
    if profile:
        z_min = min(row["z"] for row in profile)
        z_max = max(row["z"] for row in profile)
        for af in af_samples:
            z = af["z"]
            if z < z_min - 1.0e-12 or z > z_max + 1.0e-12:
                continue
            row: Dict[str, float] = {"z": z, "af_u": af["u"]}
            custom_u = interpolate(profile, "u", z)
            if custom_u is not None:
                row["custom_u"] = custom_u
                row["u_error"] = custom_u - af["u"]
            if "k" in af:
                row["af_k"] = af["k"]
            custom_k = interpolate(profile, "k", z)
            if custom_k is not None:
                row["custom_k"] = custom_k
                if "af_k" in row:
                    row["k_error"] = custom_k - row["af_k"]
            custom_k_from_rij = interpolate(profile, "k_from_rij", z)
            if custom_k_from_rij is not None:
                row["custom_k_from_rij"] = custom_k_from_rij
                if "custom_k" in row:
                    row["k_rij_error"] = custom_k_from_rij - row["custom_k"]
            if "k_from_rms" in af:
                row["af_k_from_rms"] = af["k_from_rms"]
            overlap_rows.append(row)
    else:
        z_min = None
        z_max = None

    if len(overlap_rows) < args.min_overlap_af_rows:
        reasons.append(f"overlap_af_rows_below_minimum:{len(overlap_rows)}<{args.min_overlap_af_rows}")

    u_metrics = ratio_errors(overlap_rows, "custom_u", "af_u")
    k_metrics = ratio_errors(overlap_rows, "custom_k", "af_k")
    k_rij_metrics = ratio_errors(overlap_rows, "custom_k_from_rij", "custom_k")

    if u_metrics["mae_ratio"] is None:
        reasons.append("u_profile_comparison_missing")
    elif u_metrics["mae_ratio"] > args.max_u_mae_ratio:
        reasons.append(
            f"u_mae_ratio_above_threshold:{u_metrics['mae_ratio']:.6g}>{args.max_u_mae_ratio:.6g}"
        )

    if args.require_k and k_metrics["mae_ratio"] is None:
        reasons.append("k_profile_comparison_missing")
    elif k_metrics["mae_ratio"] is not None and k_metrics["mae_ratio"] > args.max_k_mae_ratio:
        reasons.append(
            f"k_mae_ratio_above_threshold:{k_metrics['mae_ratio']:.6g}>{args.max_k_mae_ratio:.6g}"
        )

    if k_rij_metrics["mae_ratio"] is not None and k_rij_metrics["mae_ratio"] > args.max_k_rij_mae_ratio:
        reasons.append(
            "k_inconsistent_with_reynolds_stress_trace:"
            f"{k_rij_metrics['mae_ratio']:.6g}>{args.max_k_rij_mae_ratio:.6g}"
        )

    gate = PASS if not reasons else FAIL
    report = {
        "schema": "citylbm.custom_profile_af_fidelity.v1",
        "Gate": gate,
        "custom_profile_af_fidelity_gate": gate,
        "Reasons": reasons or ["custom_profile_matches_official_af_within_thresholds"],
        "MetadataPath": str(metadata_path.resolve()),
        "MetadataSha256": sha256_file(metadata_path),
        "AfCsvPath": str(af_path.resolve()),
        "AfCsvSha256": sha256_file(af_path),
        "CustomProfileRows": metadata_row_count,
        "CustomProfileRowsDeclared": metadata_declared_rows,
        "AfRows": af_row_count,
        "OverlapAfRows": len(overlap_rows),
        "CustomProfileZMin": z_min,
        "CustomProfileZMax": z_max,
        "AfZMin": min(row["z"] for row in af_samples),
        "AfZMax": max(row["z"] for row in af_samples),
        "Thresholds": {
            "min_profile_rows": args.min_profile_rows,
            "min_overlap_af_rows": args.min_overlap_af_rows,
            "max_u_mae_ratio": args.max_u_mae_ratio,
            "max_k_mae_ratio": args.max_k_mae_ratio,
            "max_k_rij_mae_ratio": args.max_k_rij_mae_ratio,
            "require_k": args.require_k,
        },
        "Metrics": {
            "U": u_metrics,
            "K": k_metrics,
            "KFromRijVsK": k_rij_metrics,
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.out_csv:
        write_csv(Path(args.out_csv), overlap_rows)
    return 0 if gate == PASS else 2


if __name__ == "__main__":
    sys.exit(main())
