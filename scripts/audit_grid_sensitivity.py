#!/usr/bin/env python3
"""Audit grid-sensitivity evidence for CityLBM/FluidX3D validation.

This script does not run CFD. It reads two or more existing validation metrics
rows and checks whether the finest archived grid is plausibly grid-insensitive
before a Case A/E result is promoted as paper-grade evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit grid-sensitivity metrics from completed runs.")
    parser.add_argument(
        "--metrics",
        action="append",
        required=True,
        help="Validation metrics CSV/JSON. Repeat for multiple grid levels; CSV files may contain multiple rows.",
    )
    parser.add_argument("--out", required=True, help="Output grid_sensitivity_audit.json.")
    parser.add_argument("--case", default="", help="Optional case filter.")
    parser.add_argument("--wind-direction", default="", help="Optional wind-direction filter.")
    parser.add_argument("--software", default="", help="Optional software filter.")
    parser.add_argument("--max-paper-dx-m", type=float, default=3.0)
    parser.add_argument("--min-grid-sensitivity-run-count", type=int, default=2)
    parser.add_argument("--min-grid-refinement-ratio", type=float, default=1.25)
    parser.add_argument("--max-grid-rmse-change-ratio", type=float, default=0.10)
    parser.add_argument("--max-grid-bias-change-ratio", type=float, default=0.05)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def get_any(row: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def read_metrics(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        return [data] if isinstance(data, dict) else []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def text_matches(row_value: Any, expected: str) -> bool:
    if not expected:
        return True
    return str(row_value or "").strip().lower() == expected.strip().lower()


def row_key(row: Dict[str, Any]) -> Tuple[str, str, str, float]:
    return (
        str(get_any(row, ["case", "Case"]) or "").strip(),
        str(get_any(row, ["wind_direction", "WindDirection"]) or "").strip(),
        str(get_any(row, ["software", "Software"]) or "").strip(),
        as_float(get_any(row, ["dx_m", "dx", "DxM", "Dx"])) or math.inf,
    )


def normalize_row(row: Dict[str, Any], source: Path, index: int) -> Optional[Dict[str, Any]]:
    dx = as_float(get_any(row, ["dx_m", "dx", "DxM", "Dx"]))
    rmse = as_float(get_any(row, ["U_RMSE_ratio", "U_RMSE_Uref", "U_RMSE"]))
    bias = as_float(get_any(row, ["U_bias_ratio", "U_bias_Uref", "U_bias"]))
    r2 = as_float(get_any(row, ["U_R2", "R2"]))
    if dx is None or dx <= 0.0:
        return None
    return {
        "case": str(get_any(row, ["case", "Case"]) or "").strip(),
        "wind_direction": str(get_any(row, ["wind_direction", "WindDirection"]) or "").strip(),
        "software": str(get_any(row, ["software", "Software"]) or "").strip(),
        "dx_m": dx,
        "U_RMSE_ratio": rmse,
        "U_bias_ratio": bias,
        "U_R2": r2,
        "source": str(source.resolve()),
        "source_row_index": index,
    }


def latest_by_dx(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_dx: Dict[float, Dict[str, Any]] = {}
    for row in rows:
        by_dx[row["dx_m"]] = row
    return sorted(by_dx.values(), key=lambda item: item["dx_m"])


def main() -> int:
    args = parse_args()
    metric_paths = [Path(item).expanduser().resolve() for item in args.metrics]
    out_path = Path(args.out).expanduser().resolve()

    raw_rows: List[Dict[str, Any]] = []
    unreadable: List[str] = []
    for path in metric_paths:
        if not path.exists():
            unreadable.append(str(path))
            continue
        try:
            rows = read_metrics(path)
        except (OSError, json.JSONDecodeError, csv.Error):
            unreadable.append(str(path))
            continue
        for index, row in enumerate(rows):
            normalized = normalize_row(row, path, index)
            if normalized is None:
                continue
            if not text_matches(normalized["case"], args.case):
                continue
            if not text_matches(normalized["wind_direction"], args.wind_direction):
                continue
            if not text_matches(normalized["software"], args.software):
                continue
            raw_rows.append(normalized)

    rows = latest_by_dx(raw_rows)
    finest = rows[0] if rows else None
    next_coarse = rows[1] if len(rows) > 1 else None
    run_count = len(rows)
    fine_dx = finest["dx_m"] if finest else None
    coarse_dx = next_coarse["dx_m"] if next_coarse else None
    refinement_ratio = coarse_dx / fine_dx if fine_dx and coarse_dx else None
    fine_rmse = finest.get("U_RMSE_ratio") if finest else None
    coarse_rmse = next_coarse.get("U_RMSE_ratio") if next_coarse else None
    fine_bias = finest.get("U_bias_ratio") if finest else None
    coarse_bias = next_coarse.get("U_bias_ratio") if next_coarse else None
    rmse_change = (
        abs(float(fine_rmse) - float(coarse_rmse))
        if fine_rmse is not None and coarse_rmse is not None
        else None
    )
    bias_change = (
        abs(float(fine_bias) - float(coarse_bias))
        if fine_bias is not None and coarse_bias is not None
        else None
    )

    reasons: List[str] = []
    if unreadable:
        reasons.append("metrics_unreadable:" + ",".join(unreadable))
    if run_count < args.min_grid_sensitivity_run_count:
        reasons.append(f"grid_sensitivity_run_count_below_{args.min_grid_sensitivity_run_count}")
    if fine_dx is None:
        reasons.append("fine_dx_missing")
    elif fine_dx > args.max_paper_dx_m:
        reasons.append(f"fine_dx_above_{args.max_paper_dx_m:g}")
    if refinement_ratio is None:
        reasons.append("grid_refinement_ratio_missing")
    elif refinement_ratio < args.min_grid_refinement_ratio:
        reasons.append(f"grid_refinement_ratio_below_{args.min_grid_refinement_ratio:g}")
    if rmse_change is None:
        reasons.append("grid_rmse_change_missing")
    elif rmse_change > args.max_grid_rmse_change_ratio:
        reasons.append(f"grid_rmse_change_above_{args.max_grid_rmse_change_ratio:g}")
    if bias_change is None:
        reasons.append("grid_bias_change_missing")
    elif bias_change > args.max_grid_bias_change_ratio:
        reasons.append(f"grid_bias_change_above_{args.max_grid_bias_change_ratio:g}")

    gate = "pass" if not reasons else "fail"
    report: Dict[str, Any] = {
        "schema": "citylbm.grid_sensitivity_audit.v1",
        "generated_at_utc": utc_now(),
        "metrics": [str(path) for path in metric_paths],
        "case_filter": args.case,
        "wind_direction_filter": args.wind_direction,
        "software_filter": args.software,
        "grid_sensitivity_gate": gate,
        "grid_sensitivity_gate_reasons": reasons or ["grid_sensitivity_evidence_complete"],
        "grid_sensitivity_run_count": run_count,
        "grid_sensitivity_dx_values_m": [row["dx_m"] for row in rows],
        "grid_sensitivity_finest_dx_m": fine_dx,
        "grid_sensitivity_next_coarse_dx_m": coarse_dx,
        "grid_sensitivity_refinement_ratio": refinement_ratio,
        "grid_sensitivity_rmse_change_ratio": rmse_change,
        "grid_sensitivity_bias_change_ratio": bias_change,
        "grid_sensitivity_finest_U_RMSE_ratio": fine_rmse,
        "grid_sensitivity_next_coarse_U_RMSE_ratio": coarse_rmse,
        "grid_sensitivity_finest_U_bias_ratio": fine_bias,
        "grid_sensitivity_next_coarse_U_bias_ratio": coarse_bias,
        "max_paper_dx_m": args.max_paper_dx_m,
        "min_grid_sensitivity_run_count": args.min_grid_sensitivity_run_count,
        "min_grid_refinement_ratio": args.min_grid_refinement_ratio,
        "max_grid_rmse_change_ratio": args.max_grid_rmse_change_ratio,
        "max_grid_bias_change_ratio": args.max_grid_bias_change_ratio,
        "selected_rows": rows,
        "recommended_next_action": (
            "Run at least two matched grid levels with the same inflow, boundary, averaging and probe extraction; "
            "do not interpret a remaining systematic bias as solver accuracy until the finest-grid change is bounded."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"grid_sensitivity_gate={gate}; reasons={';'.join(report['grid_sensitivity_gate_reasons'])}")
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
