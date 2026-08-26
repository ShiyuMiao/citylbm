#!/usr/bin/env python3
"""Audit CityLBM/FluidX3D inlet diagnostic CSV without waiting for VTK parsing.

The generated setup.cpp writes `*_inlet_turbulence_stats.csv` during a native
FluidX3D run. This audit checks whether the runtime inlet plane preserved the
target CustomTable mean velocity and turbulence levels. It is a fast feedback
gate for short canary runs; the VTK profile/correlation audits remain the
stronger post-run evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PASS = "pass"
FAIL = "fail"
REYNOLDS_STRESS_COMPONENTS = ("r11", "r22", "r33", "r12", "r13", "r23")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit runtime inlet U/k/RMS preservation from *_inlet_turbulence_stats.csv."
    )
    parser.add_argument("csv_path", help="Path to *_inlet_turbulence_stats.csv.")
    parser.add_argument("--out-json", required=True, help="Output audit JSON.")
    parser.add_argument("--out-csv", default="", help="Optional per-profile summary CSV.")
    parser.add_argument("--min-steps", type=int, default=3)
    parser.add_argument("--average-last-n-steps", type=int, default=3)
    parser.add_argument("--min-profiles", type=int, default=2)
    parser.add_argument("--min-samples-y", type=int, default=1)
    parser.add_argument("--max-mean-u-rel-error", type=float, default=0.10)
    parser.add_argument("--max-k-rel-error", type=float, default=0.35)
    parser.add_argument("--max-rms-rel-error", type=float, default=0.35)
    parser.add_argument("--max-reynolds-stress-rel-error", type=float, default=0.50)
    parser.add_argument("--max-reynolds-stress-abs-error", type=float, default=0.02)
    parser.add_argument("--max-crossflow-ratio", type=float, default=0.20)
    parser.add_argument("--require-k", action="store_true")
    parser.add_argument("--require-rms", action="store_true")
    parser.add_argument("--require-reynolds-stress", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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
    parsed = as_float(value)
    if parsed is None:
        return None
    rounded = int(round(parsed))
    if abs(parsed - rounded) > 1.0e-9:
        return None
    return rounded


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def rel_error(actual: Optional[float], target: Optional[float]) -> Optional[float]:
    if actual is None or target is None:
        return None
    denom = max(abs(target), 1.0e-12)
    return abs(actual - target) / denom


def rms_active_k(
    target_ur: Optional[float],
    target_vr: Optional[float],
    target_wr: Optional[float],
    r12: Optional[float],
    r13: Optional[float],
    r23: Optional[float],
) -> Optional[float]:
    """Return the runtime k target when a full tensor target is active.

    The generated diagnostics report both the raw AF/table k and component RMS
    targets. For full-tensor canaries, componentwise RMS rescaling makes the
    RMS-derived energy the active runtime target while off-diagonal covariance
    is still diagnostic.
    """
    offdiag = [value for value in (r12, r13, r23) if value is not None]
    if not offdiag or max(abs(value) for value in offdiag) <= 1.0e-12:
        return None
    if target_ur is None or target_vr is None or target_wr is None:
        return None
    return 0.5 * (target_ur * target_ur + target_vr * target_vr + target_wr * target_wr)


def linear_interpolate(points: Sequence[Tuple[float, Optional[float]]], z: Optional[float]) -> Optional[float]:
    if z is None:
        return None
    finite = sorted((pz, value) for pz, value in points if value is not None)
    if not finite:
        return None
    if z <= finite[0][0]:
        return finite[0][1]
    if z >= finite[-1][0]:
        return finite[-1][1]
    for (z0, v0), (z1, v1) in zip(finite, finite[1:]):
        if z0 <= z <= z1:
            span = z1 - z0
            if abs(span) < 1.0e-12:
                return v0
            t = (z - z0) / span
            return v0 + t * (v1 - v0)
    return finite[-1][1]


def finite_values(rows: Iterable[Dict[str, Any]], key: str) -> List[float]:
    values: List[float] = []
    for row in rows:
        value = as_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def required_columns() -> List[str]:
    return [
        "step",
        "profile_index",
        "target_U_mps",
        "target_u_rms_mps",
        "target_v_rms_mps",
        "target_w_rms_mps",
        "target_k_m2s2",
        "mean_U_mps",
        "mean_V_mps",
        "mean_W_mps",
        "u_rms_mps",
        "v_rms_mps",
        "w_rms_mps",
        "k_m2s2",
        "samples_y",
    ]


def reynolds_stress_columns() -> List[str]:
    columns: List[str] = []
    for component in REYNOLDS_STRESS_COMPONENTS:
        columns.append(f"target_{component}_m2s2")
    for component in REYNOLDS_STRESS_COMPONENTS:
        columns.append(f"measured_{component}_m2s2")
    return columns


def read_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return rows, fields


def canonicalize_columns(rows: List[Dict[str, str]], fields: List[str]) -> Tuple[List[Dict[str, str]], List[str], Dict[str, str]]:
    fields_by_lower = {field.lower(): field for field in fields}
    canonical_fields = list(fields)
    aliases: Dict[str, str] = {}
    for canonical in required_columns() + reynolds_stress_columns():
        if canonical in fields:
            continue
        actual = fields_by_lower.get(canonical.lower())
        if actual is None:
            continue
        aliases[canonical] = actual
        if canonical not in canonical_fields:
            canonical_fields.append(canonical)
        for row in rows:
            row[canonical] = row.get(actual, "")
    return rows, canonical_fields, aliases


def select_steps(rows: Sequence[Dict[str, str]], average_last_n_steps: int) -> Tuple[List[int], List[Dict[str, str]]]:
    steps = sorted({step for step in (as_int(row.get("step")) for row in rows) if step is not None})
    if average_last_n_steps > 0:
        selected_steps = steps[-average_last_n_steps:]
    else:
        selected_steps = steps
    selected = [row for row in rows if as_int(row.get("step")) in set(selected_steps)]
    return selected_steps, selected


def profile_summary(rows: Sequence[Dict[str, str]]) -> List[Dict[str, Any]]:
    profile_ids = sorted({idx for idx in (as_int(row.get("profile_index")) for row in rows) if idx is not None})
    profile_targets: Dict[int, Dict[str, Optional[float]]] = {}
    for profile_id in profile_ids:
        profile_rows = [row for row in rows if as_int(row.get("profile_index")) == profile_id]
        profile_targets[profile_id] = {
            "z_m": mean(finite_values(profile_rows, "z_m")),
            "target_U_mps": mean(finite_values(profile_rows, "target_U_mps")),
            "target_k_m2s2": mean(finite_values(profile_rows, "target_k_m2s2")),
            "target_u_rms_mps": mean(finite_values(profile_rows, "target_u_rms_mps")),
            "target_v_rms_mps": mean(finite_values(profile_rows, "target_v_rms_mps")),
            "target_w_rms_mps": mean(finite_values(profile_rows, "target_w_rms_mps")),
        }
        target = profile_targets[profile_id]
        target["active_target_k_m2s2"] = (
            rms_active_k(
                target.get("target_u_rms_mps"),
                target.get("target_v_rms_mps"),
                target.get("target_w_rms_mps"),
                mean(finite_values(profile_rows, "target_r12_m2s2")),
                mean(finite_values(profile_rows, "target_r13_m2s2")),
                mean(finite_values(profile_rows, "target_r23_m2s2")),
            )
            or target.get("target_k_m2s2")
        )
    target_series = {
        key: [(target.get("z_m") or 0.0, target.get(key)) for target in profile_targets.values() if target.get("z_m") is not None]
        for key in (
            "target_U_mps",
            "target_k_m2s2",
            "active_target_k_m2s2",
            "target_u_rms_mps",
            "target_v_rms_mps",
            "target_w_rms_mps",
        )
    }
    summaries: List[Dict[str, Any]] = []
    for profile_id in profile_ids:
        profile_rows = [row for row in rows if as_int(row.get("profile_index")) == profile_id]
        profile_z = mean(finite_values(profile_rows, "z_m"))
        effective_z = mean(finite_values(profile_rows, "effective_sample_z_m"))
        target_u = mean(finite_values(profile_rows, "target_U_mps"))
        mean_u = mean(finite_values(profile_rows, "mean_U_mps"))
        target_k = mean(finite_values(profile_rows, "target_k_m2s2"))
        k_sim = mean(finite_values(profile_rows, "k_m2s2"))
        target_ur = mean(finite_values(profile_rows, "target_u_rms_mps"))
        target_vr = mean(finite_values(profile_rows, "target_v_rms_mps"))
        target_wr = mean(finite_values(profile_rows, "target_w_rms_mps"))
        active_target_k = (
            rms_active_k(
                target_ur,
                target_vr,
                target_wr,
                mean(finite_values(profile_rows, "target_r12_m2s2")),
                mean(finite_values(profile_rows, "target_r13_m2s2")),
                mean(finite_values(profile_rows, "target_r23_m2s2")),
            )
            or target_k
        )
        ur = mean(finite_values(profile_rows, "u_rms_mps"))
        vr = mean(finite_values(profile_rows, "v_rms_mps"))
        wr = mean(finite_values(profile_rows, "w_rms_mps"))
        mean_v = mean(finite_values(profile_rows, "mean_V_mps"))
        mean_w = mean(finite_values(profile_rows, "mean_W_mps"))
        samples_y = [as_int(row.get("samples_y")) for row in profile_rows]
        sample_values = [value for value in samples_y if value is not None]
        crossflow = None
        if mean_u is not None:
            transverse = math.sqrt((mean_v or 0.0) ** 2 + (mean_w or 0.0) ** 2)
            crossflow = transverse / max(abs(mean_u), 1.0e-12)
        target_u_effective = linear_interpolate(target_series["target_U_mps"], effective_z)
        target_k_effective = linear_interpolate(target_series["target_k_m2s2"], effective_z)
        active_target_k_effective = linear_interpolate(target_series["active_target_k_m2s2"], effective_z)
        target_ur_effective = linear_interpolate(target_series["target_u_rms_mps"], effective_z)
        target_vr_effective = linear_interpolate(target_series["target_v_rms_mps"], effective_z)
        target_wr_effective = linear_interpolate(target_series["target_w_rms_mps"], effective_z)
        z_offset = None if profile_z is None or effective_z is None else effective_z - profile_z
        summaries.append(
            {
                "profile_index": profile_id,
                "row_count": len(profile_rows),
                "min_samples_y": min(sample_values) if sample_values else None,
                "profile_z_m": profile_z,
                "effective_sample_z_m": effective_z,
                "sample_z_offset_m": z_offset,
                "target_U_mps": target_u,
                "mean_U_mps": mean_u,
                "mean_U_rel_error": rel_error(mean_u, target_u),
                "target_U_effective_mps": target_u_effective,
                "mean_U_rel_error_effective": rel_error(mean_u, target_u_effective),
                "target_k_m2s2": target_k,
                "k_m2s2": k_sim,
                "k_rel_error": rel_error(k_sim, target_k),
                "target_k_effective_m2s2": target_k_effective,
                "k_rel_error_effective": rel_error(k_sim, target_k_effective),
                "active_target_k_m2s2": active_target_k,
                "active_k_rel_error": rel_error(k_sim, active_target_k),
                "active_target_k_effective_m2s2": active_target_k_effective,
                "active_k_rel_error_effective": rel_error(k_sim, active_target_k_effective),
                "target_u_rms_mps": target_ur,
                "u_rms_mps": ur,
                "u_rms_rel_error": rel_error(ur, target_ur),
                "target_u_rms_effective_mps": target_ur_effective,
                "u_rms_rel_error_effective": rel_error(ur, target_ur_effective),
                "target_v_rms_mps": target_vr,
                "v_rms_mps": vr,
                "v_rms_rel_error": rel_error(vr, target_vr),
                "target_v_rms_effective_mps": target_vr_effective,
                "v_rms_rel_error_effective": rel_error(vr, target_vr_effective),
                "target_w_rms_mps": target_wr,
                "w_rms_mps": wr,
                "w_rms_rel_error": rel_error(wr, target_wr),
                "target_w_rms_effective_mps": target_wr_effective,
                "w_rms_rel_error_effective": rel_error(wr, target_wr_effective),
                "mean_crossflow_ratio": crossflow,
            }
        )
        for component in REYNOLDS_STRESS_COMPONENTS:
            target_key = f"target_{component}_m2s2"
            measured_key = f"measured_{component}_m2s2"
            target = mean(finite_values(profile_rows, target_key))
            measured = mean(finite_values(profile_rows, measured_key))
            abs_err = None if target is None or measured is None else abs(measured - target)
            summaries[-1][target_key] = target
            summaries[-1][measured_key] = measured
            summaries[-1][f"{component}_abs_error_m2s2"] = abs_err
            summaries[-1][f"{component}_rel_error"] = rel_error(measured, target)
    return summaries


def max_optional(values: Iterable[Optional[float]]) -> Optional[float]:
    finite = [value for value in values if value is not None]
    return max(finite) if finite else None


def write_summary_csv(path: Path, summaries: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "profile_index",
        "row_count",
        "min_samples_y",
        "profile_z_m",
        "effective_sample_z_m",
        "sample_z_offset_m",
        "target_U_mps",
        "mean_U_mps",
        "mean_U_rel_error",
        "target_U_effective_mps",
        "mean_U_rel_error_effective",
        "target_k_m2s2",
        "k_m2s2",
        "k_rel_error",
        "target_k_effective_m2s2",
        "k_rel_error_effective",
        "active_target_k_m2s2",
        "active_k_rel_error",
        "active_target_k_effective_m2s2",
        "active_k_rel_error_effective",
        "target_u_rms_mps",
        "u_rms_mps",
        "u_rms_rel_error",
        "target_u_rms_effective_mps",
        "u_rms_rel_error_effective",
        "target_v_rms_mps",
        "v_rms_mps",
        "v_rms_rel_error",
        "target_v_rms_effective_mps",
        "v_rms_rel_error_effective",
        "target_w_rms_mps",
        "w_rms_mps",
        "w_rms_rel_error",
        "target_w_rms_effective_mps",
        "w_rms_rel_error_effective",
        "mean_crossflow_ratio",
    ]
    for component in REYNOLDS_STRESS_COMPONENTS:
        fields.extend(
            [
                f"target_{component}_m2s2",
                f"measured_{component}_m2s2",
                f"{component}_abs_error_m2s2",
                f"{component}_rel_error",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in summaries:
            writer.writerow({field: row.get(field) for field in fields})


def build_audit(args: argparse.Namespace) -> Dict[str, Any]:
    path = Path(args.csv_path).expanduser().resolve()
    reasons: List[str] = []
    if not path.is_file():
        return {
            "Schema": "citylbm.inlet_diagnostics_csv_audit.v1",
            "GeneratedAtUtc": utc_now(),
            "Gate": FAIL,
            "Reasons": ["inlet_diagnostics_csv_missing"],
            "CsvPath": str(path),
        }

    rows, fields = read_rows(path)
    rows, fields, column_aliases = canonicalize_columns(rows, fields)
    missing = [column for column in required_columns() if column not in fields]
    if missing:
        reasons.extend(f"missing_column:{column}" for column in missing)
    missing_reynolds_stress_columns = [column for column in reynolds_stress_columns() if column not in fields]
    reynolds_stress_columns_present = not missing_reynolds_stress_columns
    if args.require_reynolds_stress and missing_reynolds_stress_columns:
        reasons.extend(f"missing_reynolds_stress_column:{column}" for column in missing_reynolds_stress_columns)
    if not rows:
        reasons.append("csv_has_no_rows")

    steps, selected = select_steps(rows, args.average_last_n_steps)
    all_steps = sorted({step for step in (as_int(row.get("step")) for row in rows) if step is not None})
    if len(all_steps) < args.min_steps:
        reasons.append(f"step_count_below_{args.min_steps}")
    if not selected:
        reasons.append("no_rows_in_selected_step_window")

    summaries = profile_summary(selected)
    if len(summaries) < args.min_profiles:
        reasons.append(f"profile_count_below_{args.min_profiles}")
    if any((row.get("min_samples_y") or 0) < args.min_samples_y for row in summaries):
        reasons.append(f"samples_y_below_{args.min_samples_y}")

    max_u = max_optional(row.get("mean_U_rel_error") for row in summaries)
    max_u_effective = max_optional(row.get("mean_U_rel_error_effective") for row in summaries)
    max_k = max_optional(row.get("k_rel_error") for row in summaries)
    max_k_effective = max_optional(row.get("k_rel_error_effective") for row in summaries)
    max_active_k = max_optional(row.get("active_k_rel_error") for row in summaries)
    max_active_k_effective = max_optional(row.get("active_k_rel_error_effective") for row in summaries)
    max_ur = max_optional(row.get("u_rms_rel_error") for row in summaries)
    max_vr = max_optional(row.get("v_rms_rel_error") for row in summaries)
    max_wr = max_optional(row.get("w_rms_rel_error") for row in summaries)
    max_rms = max_optional([max_ur, max_vr, max_wr])
    max_ur_effective = max_optional(row.get("u_rms_rel_error_effective") for row in summaries)
    max_vr_effective = max_optional(row.get("v_rms_rel_error_effective") for row in summaries)
    max_wr_effective = max_optional(row.get("w_rms_rel_error_effective") for row in summaries)
    max_rms_effective = max_optional([max_ur_effective, max_vr_effective, max_wr_effective])
    max_sample_z_offset = max_optional(
        abs(value)
        for value in (row.get("sample_z_offset_m") for row in summaries)
        if value is not None
    )
    max_crossflow = max_optional(row.get("mean_crossflow_ratio") for row in summaries)
    max_reynolds_stress_abs = max_optional(
        row.get(f"{component}_abs_error_m2s2")
        for row in summaries
        for component in REYNOLDS_STRESS_COMPONENTS
    )
    max_reynolds_stress_rel = max_optional(
        row.get(f"{component}_rel_error")
        for row in summaries
        for component in REYNOLDS_STRESS_COMPONENTS
    )
    reynolds_stress_error_exceeds_threshold = (
        max_reynolds_stress_abs is not None
        and max_reynolds_stress_abs > args.max_reynolds_stress_abs_error
        and (max_reynolds_stress_rel is None or max_reynolds_stress_rel > args.max_reynolds_stress_rel_error)
    )
    if not reynolds_stress_columns_present:
        reynolds_stress_gate = "missing"
    elif max_reynolds_stress_abs is None:
        reynolds_stress_gate = "unavailable"
    elif reynolds_stress_error_exceeds_threshold:
        reynolds_stress_gate = FAIL
    else:
        reynolds_stress_gate = PASS

    max_u_for_gate = max_u_effective if max_u_effective is not None else max_u
    max_k_for_gate = max_active_k_effective if max_active_k_effective is not None else max_active_k
    max_rms_for_gate = max_rms_effective if max_rms_effective is not None else max_rms

    if max_u_for_gate is None:
        reasons.append("mean_u_error_unavailable")
    elif max_u_for_gate > args.max_mean_u_rel_error:
        reasons.append(f"mean_u_rel_error_above_{args.max_mean_u_rel_error:.6g}")

    if args.require_k:
        if max_k_for_gate is None:
            reasons.append("k_error_unavailable")
        elif max_k_for_gate > args.max_k_rel_error:
            reasons.append(f"k_rel_error_above_{args.max_k_rel_error:.6g}")

    if args.require_rms:
        if max_rms_for_gate is None:
            reasons.append("rms_error_unavailable")
        elif max_rms_for_gate > args.max_rms_rel_error:
            reasons.append(f"rms_rel_error_above_{args.max_rms_rel_error:.6g}")

    if args.require_reynolds_stress and reynolds_stress_columns_present:
        if max_reynolds_stress_abs is None:
            reasons.append("reynolds_stress_error_unavailable")
        elif reynolds_stress_error_exceeds_threshold:
            reasons.append(
                "reynolds_stress_error_above_"
                f"abs_{args.max_reynolds_stress_abs_error:.6g}_or_rel_{args.max_reynolds_stress_rel_error:.6g}"
            )

    if max_crossflow is not None and max_crossflow > args.max_crossflow_ratio:
        reasons.append(f"crossflow_ratio_above_{args.max_crossflow_ratio:.6g}")

    return {
        "Schema": "citylbm.inlet_diagnostics_csv_audit.v1",
        "GeneratedAtUtc": utc_now(),
        "Gate": PASS if not reasons else FAIL,
        "Reasons": reasons or ["inlet_diagnostics_preserved_within_tolerance"],
        "CsvPath": str(path),
        "CsvSha256": sha256(path),
        "Rows": len(rows),
        "Columns": fields,
        "ColumnAliases": column_aliases,
        "AllSteps": all_steps,
        "SelectedSteps": steps,
        "ProfileCount": len(summaries),
        "Thresholds": {
            "MinSteps": args.min_steps,
            "AverageLastNSteps": args.average_last_n_steps,
            "MinProfiles": args.min_profiles,
            "MinSamplesY": args.min_samples_y,
            "MaxMeanURelError": args.max_mean_u_rel_error,
            "MaxKRelError": args.max_k_rel_error,
            "MaxRmsRelError": args.max_rms_rel_error,
            "MaxReynoldsStressRelError": args.max_reynolds_stress_rel_error,
            "MaxReynoldsStressAbsErrorM2s2": args.max_reynolds_stress_abs_error,
            "MaxCrossflowRatio": args.max_crossflow_ratio,
            "RequireK": bool(args.require_k),
            "RequireRms": bool(args.require_rms),
            "RequireReynoldsStress": bool(args.require_reynolds_stress),
        },
        "Metrics": {
            "MaxMeanURelError": max_u,
            "MaxMeanURelErrorEffectiveSampleZ": max_u_effective,
            "MaxKRelError": max_k,
            "MaxKRelErrorEffectiveSampleZ": max_k_effective,
            "MaxActiveKRelError": max_active_k,
            "MaxActiveKRelErrorEffectiveSampleZ": max_active_k_effective,
            "MaxRmsRelError": max_rms,
            "MaxRmsRelErrorEffectiveSampleZ": max_rms_effective,
            "MaxSampleZOffsetM": max_sample_z_offset,
            "MeanUGateComparison": "effective_sample_z" if max_u_effective is not None else "profile_z",
            "KGateComparison": "effective_sample_z_active_target" if max_active_k_effective is not None else "profile_z_active_target",
            "RmsGateComparison": "effective_sample_z" if max_rms_effective is not None else "profile_z",
            "ReynoldsStressGate": reynolds_stress_gate,
            "ReynoldsStressColumnsPresent": reynolds_stress_columns_present,
            "MissingReynoldsStressColumns": missing_reynolds_stress_columns,
            "MaxReynoldsStressAbsErrorM2s2": max_reynolds_stress_abs,
            "MaxReynoldsStressRelError": max_reynolds_stress_rel,
            "MaxCrossflowRatio": max_crossflow,
        },
        "Profiles": summaries,
    }


def main() -> int:
    args = parse_args()
    audit = build_audit(args)
    out_json = Path(args.out_json).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(audit, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if args.out_csv and audit.get("Profiles"):
        write_summary_csv(Path(args.out_csv).expanduser().resolve(), audit["Profiles"])
    print(f"inlet_diagnostics_csv_gate={audit['Gate']}; out={out_json}")
    if audit["Gate"] != PASS:
        print("reasons=" + ";".join(str(reason) for reason in audit.get("Reasons", [])))
    return 0 if audit["Gate"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
