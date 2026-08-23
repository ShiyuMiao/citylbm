#!/usr/bin/env python3
"""Audit whether CityLBM adds error beyond a paired native FluidX3D run.

The script does not run CFD. It compares already archived validation metrics
for matched CityLBM and native FluidX3D rows after parity has established that
the protocol is comparable.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


METRIC_FIELDS = [
    "U_MAE_ratio",
    "U_RMSE_ratio",
    "U_bias_ratio",
    "U_R2",
    "U_regression_slope",
    "U_regression_intercept",
    "U_mean_ratio_sim_to_exp",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit CityLBM-vs-native FluidX3D accuracy deltas."
    )
    parser.add_argument("--citylbm-metrics", required=True, help="CityLBM validation metrics CSV/JSON.")
    parser.add_argument("--native-metrics", required=True, help="Native FluidX3D validation metrics CSV/JSON.")
    parser.add_argument("--out", required=True, help="Output native_citylbm_accuracy_delta_audit.json.")
    parser.add_argument("--case", default="", help="Optional case filter.")
    parser.add_argument("--wind-direction", default="", help="Optional wind-direction filter.")
    parser.add_argument("--citylbm-software", default="citylbm")
    parser.add_argument("--native-software", default="native-fluidx3d")
    parser.add_argument(
        "--native-preconditions-audit",
        help="native_preconditions_audit.json proving native FluidX3D protocol closure before interpreting accuracy.",
    )
    parser.add_argument("--max-rmse-regression-delta", type=float, default=0.03)
    parser.add_argument("--max-abs-bias-regression-delta", type=float, default=0.03)
    parser.add_argument("--max-r2-drop", type=float, default=0.05)
    parser.add_argument("--max-slope-delta", type=float, default=0.10)
    parser.add_argument("--max-intercept-delta", type=float, default=0.05)
    parser.add_argument("--native-max-u-rmse-ratio", type=float, default=0.30)
    parser.add_argument("--native-max-u-bias-ratio", type=float, default=0.15)
    parser.add_argument("--native-min-u-r2", type=float, default=0.70)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("\\", "/").split())


def text_matches(value: Any, expected: str) -> bool:
    return not expected or normalize_text(value) == normalize_text(expected)


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
        return None if math.isnan(parsed) or math.isinf(parsed) else parsed
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return None if math.isnan(parsed) or math.isinf(parsed) else parsed


def read_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        return [data] if isinstance(data, dict) else []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def text_field(row: Dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def int_field(row: Dict[str, Any], key: str) -> Optional[int]:
    value = row.get(key)
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def native_preconditions_status(audit: Dict[str, Any], audit_path: Optional[Path]) -> Dict[str, Any]:
    reasons: List[str] = []
    if audit_path is None:
        reasons.append("native_preconditions_audit_not_provided")
    elif not audit:
        reasons.append("native_preconditions_audit_missing_or_unreadable")

    required_pass_gates = [
        "native_preconditions_gate",
        "native_precondition_closure_gate",
        "native_preconditions_protocol_identity_gate",
        "native_preconditions_time_average_evidence_gate",
        "native_inlet_equivalence_gate",
        "native_boundary_equivalence_gate",
        "native_probe_component_equivalence_gate",
    ]
    for key in required_pass_gates:
        value = text_field(audit, key).lower()
        if value != "pass":
            reasons.append(f"{key}_not_pass:{value or 'missing'}")

    failed_stage_count = int_field(audit, "native_precondition_failed_stage_count")
    if failed_stage_count is None:
        reasons.append("native_precondition_failed_stage_count_missing")
    elif failed_stage_count != 0:
        reasons.append(f"native_precondition_failed_stage_count_not_zero:{failed_stage_count}")

    return {
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons or ["native_preconditions_closed"],
        "audit": str(audit_path) if audit_path else "",
        "native_preconditions_gate": text_field(audit, "native_preconditions_gate"),
        "native_precondition_closure_gate": text_field(audit, "native_precondition_closure_gate"),
        "native_preconditions_protocol_identity_gate": text_field(
            audit, "native_preconditions_protocol_identity_gate"
        ),
        "native_preconditions_time_average_evidence_gate": text_field(
            audit, "native_preconditions_time_average_evidence_gate"
        ),
        "native_inlet_equivalence_gate": text_field(audit, "native_inlet_equivalence_gate"),
        "native_boundary_equivalence_gate": text_field(audit, "native_boundary_equivalence_gate"),
        "native_probe_component_equivalence_gate": text_field(
            audit, "native_probe_component_equivalence_gate"
        ),
        "native_precondition_failed_stage_count": failed_stage_count,
        "native_precondition_top_blocking_stage_key": text_field(
            audit, "native_precondition_top_blocking_stage_key"
        ),
    }


def select_row(
    rows: List[Dict[str, Any]],
    software: str,
    case: str,
    wind_direction: str,
) -> Tuple[Optional[Dict[str, Any]], str]:
    candidates: List[Dict[str, Any]] = []
    for row in rows:
        if not text_matches(row.get("software"), software):
            continue
        if not text_matches(row.get("case"), case):
            continue
        if not text_matches(row.get("wind_direction"), wind_direction):
            continue
        candidates.append(row)
    if not candidates:
        return None, "no_matching_row"
    if len(candidates) > 1:
        return candidates[-1], f"multiple_matching_rows_selected_last:{len(candidates)}"
    return candidates[0], ""


def metric_pair(city: Dict[str, Any], native: Dict[str, Any], field: str) -> Dict[str, Any]:
    city_value = as_float(city.get(field))
    native_value = as_float(native.get(field))
    return {
        "field": field,
        "citylbm": city_value,
        "native": native_value,
        "delta_city_minus_native": (
            city_value - native_value if city_value is not None and native_value is not None else None
        ),
        "present": city_value is not None and native_value is not None,
    }


def main() -> int:
    args = parse_args()
    city_path = Path(args.citylbm_metrics).expanduser().resolve()
    native_path = Path(args.native_metrics).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    native_preconditions_path = (
        Path(args.native_preconditions_audit).expanduser().resolve()
        if args.native_preconditions_audit
        else None
    )

    reasons: List[str] = []
    citylbm_delta_reasons: List[str] = []
    native_preconditions = read_json(native_preconditions_path)
    native_preconditions_gate = native_preconditions_status(native_preconditions, native_preconditions_path)
    if native_preconditions_gate["gate"] != "pass":
        reasons.append("native_preconditions_not_closed")
        reasons.extend(
            f"native_precondition_reason:{reason}"
            for reason in native_preconditions_gate["reasons"]
        )
    try:
        city_rows = read_rows(city_path)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        city_rows = []
        reasons.append(f"citylbm_metrics_unreadable:{exc}")
    try:
        native_rows = read_rows(native_path)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        native_rows = []
        reasons.append(f"native_metrics_unreadable:{exc}")

    city_row, city_select_reason = select_row(
        city_rows, args.citylbm_software, args.case, args.wind_direction
    )
    native_row, native_select_reason = select_row(
        native_rows, args.native_software, args.case, args.wind_direction
    )
    if city_select_reason and not city_select_reason.startswith("multiple_matching"):
        reasons.append("citylbm_" + city_select_reason)
    if native_select_reason and not native_select_reason.startswith("multiple_matching"):
        reasons.append("native_" + native_select_reason)

    metric_pairs: Dict[str, Dict[str, Any]] = {}
    if city_row is not None and native_row is not None:
        metric_pairs = {
            field: metric_pair(city_row, native_row, field)
            for field in METRIC_FIELDS
        }
        missing_metric_fields = [
            field for field, item in metric_pairs.items() if item["present"] is not True
        ]
        if missing_metric_fields:
            reasons.append("paired_accuracy_metric_missing:" + ",".join(missing_metric_fields))

    city_rmse = metric_pairs.get("U_RMSE_ratio", {}).get("citylbm")
    native_rmse = metric_pairs.get("U_RMSE_ratio", {}).get("native")
    city_bias = metric_pairs.get("U_bias_ratio", {}).get("citylbm")
    native_bias = metric_pairs.get("U_bias_ratio", {}).get("native")
    city_r2 = metric_pairs.get("U_R2", {}).get("citylbm")
    native_r2 = metric_pairs.get("U_R2", {}).get("native")
    city_slope = metric_pairs.get("U_regression_slope", {}).get("citylbm")
    native_slope = metric_pairs.get("U_regression_slope", {}).get("native")
    city_intercept = metric_pairs.get("U_regression_intercept", {}).get("citylbm")
    native_intercept = metric_pairs.get("U_regression_intercept", {}).get("native")

    rmse_regression_delta = (
        city_rmse - native_rmse if city_rmse is not None and native_rmse is not None else None
    )
    abs_bias_regression_delta = (
        abs(city_bias) - abs(native_bias) if city_bias is not None and native_bias is not None else None
    )
    r2_drop = native_r2 - city_r2 if city_r2 is not None and native_r2 is not None else None
    slope_delta = (
        abs(city_slope - native_slope)
        if city_slope is not None and native_slope is not None
        else None
    )
    intercept_delta = (
        abs(city_intercept - native_intercept)
        if city_intercept is not None and native_intercept is not None
        else None
    )

    if rmse_regression_delta is not None and rmse_regression_delta > args.max_rmse_regression_delta:
        reason = f"citylbm_rmse_regression_delta_above_{args.max_rmse_regression_delta}"
        reasons.append(reason)
        citylbm_delta_reasons.append(reason)
    if (
        abs_bias_regression_delta is not None
        and abs_bias_regression_delta > args.max_abs_bias_regression_delta
    ):
        reason = f"citylbm_abs_bias_regression_delta_above_{args.max_abs_bias_regression_delta}"
        reasons.append(reason)
        citylbm_delta_reasons.append(reason)
    if r2_drop is not None and r2_drop > args.max_r2_drop:
        reason = f"citylbm_r2_drop_above_{args.max_r2_drop}"
        reasons.append(reason)
        citylbm_delta_reasons.append(reason)
    if slope_delta is not None and slope_delta > args.max_slope_delta:
        reason = f"citylbm_slope_delta_above_{args.max_slope_delta}"
        reasons.append(reason)
        citylbm_delta_reasons.append(reason)
    if intercept_delta is not None and intercept_delta > args.max_intercept_delta:
        reason = f"citylbm_intercept_delta_above_{args.max_intercept_delta}"
        reasons.append(reason)
        citylbm_delta_reasons.append(reason)

    native_accuracy_gate = "pass"
    native_accuracy_reasons: List[str] = []
    if native_rmse is None or native_rmse > args.native_max_u_rmse_ratio:
        native_accuracy_gate = "fail"
        native_accuracy_reasons.append("native_u_rmse_not_publishable")
    if native_bias is None or abs(native_bias) > args.native_max_u_bias_ratio:
        native_accuracy_gate = "fail"
        native_accuracy_reasons.append("native_u_bias_not_publishable")
    if native_r2 is None or native_r2 < args.native_min_u_r2:
        native_accuracy_gate = "fail"
        native_accuracy_reasons.append("native_u_r2_not_publishable")

    if native_accuracy_gate != "pass":
        reasons.append(f"native_accuracy_gate_not_pass:{native_accuracy_gate}")
        reasons.extend(
            f"native_accuracy_gate_reason:{reason}"
            for reason in native_accuracy_reasons
        )

    delta_gate = "pass" if not reasons else "fail"
    citylbm_additional_error = bool(citylbm_delta_reasons)
    if citylbm_additional_error:
        interpretation = "citylbm_regression_or_transfer_error"
    elif native_preconditions_gate["gate"] != "pass":
        interpretation = "native_preconditions_not_closed"
    elif native_accuracy_gate == "pass":
        interpretation = "citylbm_matches_publishable_native_baseline"
    else:
        interpretation = "citylbm_matches_native_but_native_protocol_or_physics_limited"

    report = {
        "schema": "citylbm.native_citylbm_accuracy_delta_audit.v1",
        "generated_at_utc": utc_now(),
        "native_citylbm_accuracy_delta_gate": delta_gate,
        "native_citylbm_accuracy_delta_gate_reasons": reasons or ["citylbm_accuracy_matches_native_within_delta_thresholds"],
        "accuracy_interpretation": interpretation,
        "citylbm_additional_error_flag": citylbm_additional_error,
        "citylbm_additional_error_reasons": citylbm_delta_reasons,
        "native_preconditions_audit": native_preconditions_gate["audit"],
        "native_preconditions_accuracy_gate": native_preconditions_gate["gate"],
        "native_preconditions_accuracy_gate_reasons": native_preconditions_gate["reasons"],
        "native_preconditions_gate": native_preconditions_gate["native_preconditions_gate"],
        "native_precondition_closure_gate": native_preconditions_gate["native_precondition_closure_gate"],
        "native_preconditions_protocol_identity_gate": native_preconditions_gate[
            "native_preconditions_protocol_identity_gate"
        ],
        "native_preconditions_time_average_evidence_gate": native_preconditions_gate[
            "native_preconditions_time_average_evidence_gate"
        ],
        "native_inlet_equivalence_gate": native_preconditions_gate["native_inlet_equivalence_gate"],
        "native_boundary_equivalence_gate": native_preconditions_gate["native_boundary_equivalence_gate"],
        "native_probe_component_equivalence_gate": native_preconditions_gate[
            "native_probe_component_equivalence_gate"
        ],
        "native_precondition_failed_stage_count": native_preconditions_gate[
            "native_precondition_failed_stage_count"
        ],
        "native_precondition_top_blocking_stage_key": native_preconditions_gate[
            "native_precondition_top_blocking_stage_key"
        ],
        "native_accuracy_gate": native_accuracy_gate,
        "native_accuracy_gate_reasons": native_accuracy_reasons or ["native_accuracy_metrics_within_thresholds"],
        "citylbm_metrics": str(city_path),
        "native_metrics": str(native_path),
        "case_filter": args.case,
        "wind_direction_filter": args.wind_direction,
        "citylbm_row_selection_warning": city_select_reason,
        "native_row_selection_warning": native_select_reason,
        "metric_pairs": list(metric_pairs.values()),
        "U_RMSE_delta_city_minus_native": rmse_regression_delta,
        "U_abs_bias_delta_city_minus_native": abs_bias_regression_delta,
        "U_R2_drop_native_minus_city": r2_drop,
        "U_slope_abs_delta": slope_delta,
        "U_intercept_abs_delta": intercept_delta,
        "thresholds": {
            "max_rmse_regression_delta": args.max_rmse_regression_delta,
            "max_abs_bias_regression_delta": args.max_abs_bias_regression_delta,
            "max_r2_drop": args.max_r2_drop,
            "max_slope_delta": args.max_slope_delta,
            "max_intercept_delta": args.max_intercept_delta,
            "native_max_u_rmse_ratio": args.native_max_u_rmse_ratio,
            "native_max_u_bias_ratio": args.native_max_u_bias_ratio,
            "native_min_u_r2": args.native_min_u_r2,
        },
        "recommended_next_action": (
            "If CityLBM adds error beyond the paired native run, inspect parameter transfer, setup.cpp generation, "
            "VTK scaling and probe postprocessing. If CityLBM matches native but native is not publishable, improve "
            "the native inlet, boundary, averaging or grid protocol before changing CityLBM."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "native_citylbm_accuracy_delta_gate="
        f"{delta_gate}; interpretation={interpretation}; reasons={';'.join(report['native_citylbm_accuracy_delta_gate_reasons'])}"
    )
    return 0 if delta_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
