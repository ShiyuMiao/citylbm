#!/usr/bin/env python3
"""Audit velocity-component and Uref normalization sensitivity.

The script compares all component candidates already present in a Data
Probe/native probe audit CSV against official RS measurements. It is intended
to catch protocol mistakes such as using signed streamwise velocity when the
official table stores speed ratio, or a scale-like Uref/unit error that can
create a large systematic low bias.
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


COMPONENT_CANDIDATES = [
    "speed_ratio",
    "horizontal_speed_ratio",
    "streamwise_ratio",
    "abs_streamwise_ratio",
    "lateral_ratio",
    "u_ratio",
    "v_ratio",
    "w_ratio",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit whether component choice or Uref scaling explains validation bias."
    )
    parser.add_argument("--probe-audit", required=True, help="Data Probe/native probe audit CSV.")
    parser.add_argument("--official", required=True, help="Official RS/measurement CSV.")
    parser.add_argument("--out-json", required=True, help="Output component sensitivity JSON.")
    parser.add_argument("--out-csv", help="Optional per-component metrics CSV.")
    parser.add_argument("--case", default="", help="Optional official case filter.")
    parser.add_argument("--wind-direction", default="", help="Optional official wind-direction filter.")
    parser.add_argument("--official-id-column", default="")
    parser.add_argument("--official-value-column", default="")
    parser.add_argument("--probe-id-column", default="probe_id")
    parser.add_argument("--selected-component", default="", help="Expected/selected compared component.")
    parser.add_argument("--min-component-improvement-ratio", type=float, default=0.20)
    parser.add_argument("--max-best-scale-deviation", type=float, default=0.20)
    parser.add_argument("--min-scale-improvement-ratio", type=float, default=0.25)
    parser.add_argument("--min-bias-scale-improvement-ratio", type=float, default=0.25)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def norm_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def normalized_probe_id(value: Any) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def find_column(rows: Sequence[Dict[str, str]], candidates: Iterable[str]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    lookup = {norm_key(column): column for column in columns}
    for candidate in candidates:
        found = lookup.get(norm_key(candidate))
        if found:
            return found
    return ""


def get_value(row: Dict[str, str], key: str) -> str:
    if key in row:
        return str(row.get(key) or "")
    target = norm_key(key)
    for actual, value in row.items():
        if norm_key(actual) == target:
            return str(value or "")
    return ""


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


def as_bool(value: Any) -> Optional[bool]:
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "pass", "valid"}:
        return True
    if text in {"false", "0", "no", "fail", "invalid"}:
        return False
    return None


def filter_official(rows: Sequence[Dict[str, str]], case_name: str, wind_direction: str) -> List[Dict[str, str]]:
    selected = list(rows)
    if case_name:
        case_col = find_column(selected, ["case", "Case", "condition", "Condition"])
        if not case_col:
            raise SystemExit("Official CSV case filter requested, but no case column was detected.")
        target = case_name.strip().lower()
        selected = [row for row in selected if get_value(row, case_col).strip().lower() == target]
    if wind_direction:
        wind_col = find_column(selected, ["wind_direction", "Wind_direction", "direction", "Direction", "wind"])
        if not wind_col:
            raise SystemExit("Official CSV wind-direction filter requested, but no wind-direction column was detected.")
        target = wind_direction.strip().lower()
        selected = [row for row in selected if get_value(row, wind_col).strip().lower() == target]
    if not selected:
        raise SystemExit("Official CSV filter selected no rows.")
    return selected


def build_lookup(rows: Sequence[Dict[str, str]], id_col: str) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}
    for row in rows:
        raw_key = get_value(row, id_col).strip()
        key = normalized_probe_id(raw_key)
        if key:
            if key in result:
                raise SystemExit(f"Duplicate official probe ID after normalization: {raw_key}")
            result[key] = row
    return result


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def rmse(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return math.sqrt(sum(value * value for value in values) / len(values))


def r2_score(sim_values: Sequence[float], exp_values: Sequence[float]) -> Optional[float]:
    if len(sim_values) < 2 or len(sim_values) != len(exp_values):
        return None
    exp_mean = mean(exp_values)
    if exp_mean is None:
        return None
    ss_tot = sum((value - exp_mean) ** 2 for value in exp_values)
    if ss_tot <= 1.0e-30:
        return None
    ss_res = sum((sim - exp) ** 2 for sim, exp in zip(sim_values, exp_values))
    return 1.0 - ss_res / ss_tot


def regression(sim_values: Sequence[float], exp_values: Sequence[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(sim_values) < 2 or len(sim_values) != len(exp_values):
        return None, None
    x_mean = mean(exp_values)
    y_mean = mean(sim_values)
    if x_mean is None or y_mean is None:
        return None, None
    denom = sum((x - x_mean) ** 2 for x in exp_values)
    if denom <= 1.0e-30:
        return None, None
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(exp_values, sim_values)) / denom
    intercept = y_mean - slope * x_mean
    return slope, intercept


def best_scale_to_exp(sim_values: Sequence[float], exp_values: Sequence[float]) -> Optional[float]:
    denom = sum(value * value for value in sim_values)
    if denom <= 1.0e-30:
        return None
    return sum(sim * exp for sim, exp in zip(sim_values, exp_values)) / denom


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.10g}"
    return str(value)


def candidate_value(row: Dict[str, str], component: str) -> Optional[float]:
    if component == "abs_streamwise_ratio":
        value = as_float(get_value(row, "streamwise_ratio"))
        return abs(value) if value is not None else None
    if component in {"u_ratio", "v_ratio", "w_ratio"}:
        velocity = as_float(get_value(row, component[0]))
        uref = as_float(get_value(row, "Uref"))
        if velocity is None or uref is None or uref <= 0:
            return None
        return velocity / uref
    return as_float(get_value(row, component))


def probe_row_failed(row: Dict[str, str]) -> bool:
    return as_bool(get_value(row, "failed")) is True or as_bool(get_value(row, "out_of_tolerance")) is True


def probe_component_summary(probe_rows: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    components = set()
    valid_count = 0
    missing_count = 0
    for row in probe_rows:
        if probe_row_failed(row):
            continue
        valid_count += 1
        component = get_value(row, "compared_component").strip().lower()
        if component:
            components.add(component)
        else:
            missing_count += 1
    return {
        "valid_probe_row_count": valid_count,
        "valid_probe_compared_components": sorted(components),
        "valid_probe_compared_component_count": len(components),
        "valid_probe_missing_compared_component_count": missing_count,
    }


def select_component(
    probe_rows: Sequence[Dict[str, str]],
    explicit_component: str,
) -> Tuple[str, str, Dict[str, Any], List[str]]:
    summary = probe_component_summary(probe_rows)
    components = summary["valid_probe_compared_components"]
    missing_count = summary["valid_probe_missing_compared_component_count"]
    valid_count = summary["valid_probe_row_count"]
    reasons: List[str] = []

    explicit = explicit_component.strip().lower()
    if explicit:
        if components and explicit not in components:
            reasons.append("explicit_selected_component_conflicts_with_valid_probe_rows")
        if missing_count:
            reasons.append("valid_probe_rows_missing_compared_component")
        return explicit, "explicit_arg", summary, reasons

    if valid_count <= 0:
        reasons.append("no_valid_probe_rows_for_component_selection")
        return "", "valid_probe_rows", summary, reasons
    if missing_count:
        reasons.append("valid_probe_rows_missing_compared_component")
    if len(components) == 1:
        return components[0], "valid_probe_rows", summary, reasons
    if len(components) > 1:
        reasons.append("mixed_valid_probe_compared_components")
    else:
        reasons.append("no_valid_probe_compared_component")
    return "", "valid_probe_rows", summary, reasons


def component_metrics(
    component: str,
    probe_rows: Sequence[Dict[str, str]],
    official_lookup: Dict[str, Dict[str, str]],
    official_value_col: str,
    probe_id_col: str,
) -> Dict[str, Any]:
    sim_values: List[float] = []
    exp_values: List[float] = []
    failed = 0
    for row in probe_rows:
        failed_flag = as_bool(get_value(row, "failed"))
        out_of_tolerance = as_bool(get_value(row, "out_of_tolerance"))
        probe_id = normalized_probe_id(get_value(row, probe_id_col))
        official = official_lookup.get(probe_id)
        sim = candidate_value(row, component)
        exp = as_float(get_value(official, official_value_col)) if official else None
        if failed_flag is True or out_of_tolerance is True or sim is None or exp is None:
            failed += 1
            continue
        sim_values.append(sim)
        exp_values.append(exp)
    errors = [sim - exp for sim, exp in zip(sim_values, exp_values)]
    abs_errors = [abs(error) for error in errors]
    u_rmse = rmse(errors)
    bias = mean(errors)
    scale = best_scale_to_exp(sim_values, exp_values)
    scaled_errors = [scale * sim - exp for sim, exp in zip(sim_values, exp_values)] if scale is not None else []
    scaled_rmse = rmse(scaled_errors)
    scaled_bias = mean(scaled_errors)
    improvement = 1.0 - scaled_rmse / u_rmse if scaled_rmse is not None and u_rmse is not None and u_rmse > 1.0e-12 else None
    bias_reduction = (
        1.0 - abs(scaled_bias) / abs(bias)
        if scaled_bias is not None and bias is not None and abs(bias) > 1.0e-12
        else None
    )
    slope, intercept = regression(sim_values, exp_values)
    mean_sim_value = mean(sim_values)
    mean_exp_value = mean(exp_values)
    mean_sim_to_exp_ratio = (
        mean_sim_value / mean_exp_value
        if mean_sim_value is not None and mean_exp_value is not None and abs(mean_exp_value) > 1.0e-12
        else None
    )
    return {
        "component": component,
        "valid_n": len(sim_values),
        "failed_n": failed,
        "MAE": mean(abs_errors),
        "RMSE": u_rmse,
        "bias": bias,
        "R2": r2_score(sim_values, exp_values),
        "slope": slope,
        "intercept": intercept,
        "mean_sim": mean_sim_value,
        "mean_exp": mean_exp_value,
        "mean_sim_to_exp_ratio": mean_sim_to_exp_ratio,
        "best_fit_scale_to_exp": scale,
        "scaled_RMSE": scaled_rmse,
        "scaled_bias": scaled_bias,
        "scaled_improvement_ratio": improvement,
        "bias_abs_reduction_ratio": bias_reduction,
    }


def main() -> int:
    args = parse_args()
    probe_path = Path(args.probe_audit).resolve()
    official_path = Path(args.official).resolve()
    out_json = Path(args.out_json).resolve()
    out_csv = Path(args.out_csv).resolve() if args.out_csv else None
    probe_rows = read_csv(probe_path)
    official_rows = filter_official(read_csv(official_path), args.case, args.wind_direction)
    if not probe_rows:
        raise SystemExit("Probe audit CSV has no rows.")

    official_id_col = args.official_id_column or find_column(official_rows, ["No.", "No", "probe_id", "id", "point"])
    official_value_col = args.official_value_column or find_column(
        official_rows,
        ["Velocity_Ratio", "velocity_ratio", "V_exp_ratio", "U_exp_ratio", "U", "Velocity", "WindSpeed"],
    )
    if not official_id_col:
        raise SystemExit("Could not detect official probe ID column. Use --official-id-column.")
    if not official_value_col:
        raise SystemExit("Could not detect official measured value column. Use --official-value-column.")
    probe_id_col = args.probe_id_column or find_column(probe_rows, ["probe_id", "No.", "No", "id", "point"])
    if not probe_id_col:
        raise SystemExit("Could not detect probe ID column. Use --probe-id-column.")

    official_lookup = build_lookup(official_rows, official_id_col)
    valid_probe_ids = {
        normalized_probe_id(get_value(row, probe_id_col))
        for row in probe_rows
        if not probe_row_failed(row) and normalized_probe_id(get_value(row, probe_id_col))
    }
    matched_valid_probe_ids = sorted(probe_id for probe_id in valid_probe_ids if probe_id in official_lookup)
    unmatched_valid_probe_ids = sorted(probe_id for probe_id in valid_probe_ids if probe_id not in official_lookup)
    missing_official_probe_ids = sorted(probe_id for probe_id in official_lookup if probe_id not in valid_probe_ids)
    official_probe_coverage_ratio = (
        len(matched_valid_probe_ids) / float(len(official_lookup))
        if official_lookup
        else None
    )
    selected_component, selected_component_source, component_summary, selected_component_reasons = select_component(
        probe_rows,
        args.selected_component,
    )

    metrics = [
        component_metrics(component, probe_rows, official_lookup, official_value_col, probe_id_col)
        for component in COMPONENT_CANDIDATES
    ]
    valid_metrics = [row for row in metrics if row["valid_n"] > 0 and row["RMSE"] is not None]
    if not valid_metrics:
        raise SystemExit("No valid component sensitivity rows could be computed.")
    best = min(valid_metrics, key=lambda row: float(row["RMSE"]))
    selected = next((row for row in valid_metrics if row["component"] == selected_component), None)
    if selected is None:
        selected = component_metrics(selected_component, probe_rows, official_lookup, official_value_col, probe_id_col)
    selected_rmse = as_float(selected.get("RMSE"))
    best_rmse = as_float(best.get("RMSE"))
    component_improvement = (
        (selected_rmse - best_rmse) / selected_rmse
        if selected_rmse is not None and best_rmse is not None and selected_rmse > 1.0e-12
        else None
    )
    selected_scale = as_float(selected.get("best_fit_scale_to_exp"))
    selected_scaled_improvement = as_float(selected.get("scaled_improvement_ratio"))
    selected_bias = as_float(selected.get("bias"))
    selected_scaled_bias = as_float(selected.get("scaled_bias"))
    selected_bias_reduction = as_float(selected.get("bias_abs_reduction_ratio"))
    component_gate_reasons: List[str] = list(selected_component_reasons)
    if not selected_component:
        component_gate_reasons.append("selected_component_missing")
    if selected.get("valid_n", 0) <= 0 or selected_rmse is None:
        component_gate_reasons.append("selected_component_has_no_valid_rmse")
    if selected_component != best["component"] and component_improvement is not None and component_improvement >= args.min_component_improvement_ratio:
        component_gate_reasons.append(
            f"alternative_component_{best['component']}_improves_rmse_by_{component_improvement:.6g}"
        )
    if not official_lookup:
        component_gate_reasons.append("official_probe_id_lookup_empty")
    if len(valid_probe_ids) <= 0:
        component_gate_reasons.append("valid_probe_id_set_empty")
    if unmatched_valid_probe_ids:
        component_gate_reasons.append("valid_probe_ids_not_found_in_official")
    if missing_official_probe_ids:
        component_gate_reasons.append("official_probe_ids_missing_from_valid_probe_audit")
    if official_lookup and len(valid_probe_ids) != len(official_lookup):
        component_gate_reasons.append("valid_probe_id_count_does_not_match_official_id_count")
    if selected.get("valid_n", 0) != len(official_lookup):
        component_gate_reasons.append("selected_component_valid_n_does_not_match_official_id_count")
    if best.get("valid_n", 0) != len(official_lookup):
        component_gate_reasons.append("best_component_valid_n_does_not_match_official_id_count")
    normalization_gate_reasons: List[str] = []
    if selected_scale is not None and abs(selected_scale - 1.0) > args.max_best_scale_deviation:
        scale_explains_rmse = (
            selected_scaled_improvement is not None
            and selected_scaled_improvement >= args.min_scale_improvement_ratio
        )
        scale_explains_bias = (
            selected_bias_reduction is not None
            and selected_bias_reduction >= args.min_bias_scale_improvement_ratio
        )
        if scale_explains_rmse or scale_explains_bias:
            normalization_gate_reasons.append(
                f"best_fit_scale_{selected_scale:.6g}_suggests_uref_or_unit_error"
            )

    component_gate = "pass" if not component_gate_reasons else "fail"
    normalization_gate = "pass" if not normalization_gate_reasons else "fail"
    overall_gate = "pass" if component_gate == "pass" and normalization_gate == "pass" else "fail"
    report = {
        "schema": "citylbm.component_sensitivity_audit.v1",
        "generated_at_utc": utc_now(),
        "probe_audit": str(probe_path),
        "probe_audit_sha256": sha256_file(probe_path),
        "official": str(official_path),
        "official_sha256": sha256_file(official_path),
        "case": args.case,
        "wind_direction": args.wind_direction,
        "official_filtered_row_count": len(official_rows),
        "official_id_count": len(official_lookup),
        "probe_row_count": len(probe_rows),
        "valid_probe_id_count": len(valid_probe_ids),
        "matched_valid_probe_id_count": len(matched_valid_probe_ids),
        "unmatched_valid_probe_id_count": len(unmatched_valid_probe_ids),
        "missing_official_probe_id_count": len(missing_official_probe_ids),
        "official_probe_coverage_ratio": official_probe_coverage_ratio,
        "unmatched_valid_probe_ids_sample": unmatched_valid_probe_ids[:20],
        "missing_official_probe_ids_sample": missing_official_probe_ids[:20],
        "official_id_column": official_id_col,
        "official_value_column": official_value_col,
        "probe_id_column": probe_id_col,
        "probe_id_matching": "lowercase_alnum_normalized",
        "selected_component": selected_component,
        "selected_component_source": selected_component_source,
        **component_summary,
        "best_component_by_rmse": best["component"],
        "selected_component_rmse": selected.get("RMSE"),
        "selected_component_bias": selected_bias,
        "selected_component_scaled_bias": selected_scaled_bias,
        "selected_component_bias_abs_reduction_ratio": selected_bias_reduction,
        "selected_component_mean_sim": selected.get("mean_sim"),
        "selected_component_mean_exp": selected.get("mean_exp"),
        "selected_component_mean_sim_to_exp_ratio": selected.get("mean_sim_to_exp_ratio"),
        "best_component_rmse": best.get("RMSE"),
        "component_rmse_improvement_ratio": component_improvement,
        "selected_best_fit_scale_to_exp": selected_scale,
        "selected_scaled_improvement_ratio": selected_scaled_improvement,
        "component_sensitivity_gate": component_gate,
        "component_sensitivity_gate_reasons": component_gate_reasons or ["selected_component_not_worse_than_alternatives"],
        "normalization_scale_gate": normalization_gate,
        "normalization_scale_gate_reasons": normalization_gate_reasons or ["no_large_scale_like_uref_unit_error_detected"],
        "component_normalization_gate": overall_gate,
        "component_metrics": metrics,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if out_csv:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "component",
            "valid_n",
            "failed_n",
            "MAE",
            "RMSE",
            "bias",
            "R2",
            "slope",
            "intercept",
            "mean_sim",
            "mean_exp",
            "mean_sim_to_exp_ratio",
            "best_fit_scale_to_exp",
            "scaled_RMSE",
            "scaled_bias",
            "scaled_improvement_ratio",
            "bias_abs_reduction_ratio",
        ]
        with out_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in metrics:
                writer.writerow({field: fmt(row.get(field)) for field in fields})
    print(
        "component_normalization_gate={gate}; selected={selected}; best={best}; improvement={improvement}; scale={scale}; bias={bias}; scaled_bias={scaled_bias}".format(
            gate=overall_gate,
            selected=selected_component,
            best=best["component"],
            improvement=component_improvement,
            scale=selected_scale,
            bias=selected_bias,
            scaled_bias=selected_scaled_bias,
        )
    )
    return 0 if overall_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
