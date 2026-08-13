from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs/experiments/casee/results"
INPUT_CSV = RESULTS_DIR / "casee_probe_residuals.csv"
OUT_JSON = RESULTS_DIR / "casee_official_residual_paper_table.json"
OUT_CSV = RESULTS_DIR / "casee_official_residual_paper_table.csv"
OUT_MD = RESULTS_DIR / "casee_official_residual_paper_table.md"

REQUIRED_N = 80
REQUIRED_CASE = "ac"
REQUIRED_WIND_DIRECTION = "N"
REQUIRED_HEIGHT_M = 2.0
REQUIRED_SAMPLING = "raw_trilinear"


def read_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            row = dict(raw)
            for key in [
                "No.",
                "x_m",
                "y_m",
                "z_m",
                "official_velocity_ratio",
                "predicted_velocity_ratio",
                "residual",
                "abs_error_pp",
                "solid_corner_neighbors_max",
                "samples",
            ]:
                if key in row and row[key] != "":
                    row[key] = float(row[key])
            row["No."] = int(row["No."])
            rows.append(row)
    return rows


def metric_summary(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    residuals = [float(row["predicted_velocity_ratio"]) - float(row["official_velocity_ratio"]) for row in rows]
    official = [float(row["official_velocity_ratio"]) for row in rows]
    predicted = [float(row["predicted_velocity_ratio"]) for row in rows]
    mae = mean(abs(value) for value in residuals) * 100.0
    rmse = math.sqrt(mean(value * value for value in residuals)) * 100.0
    bias = mean(residuals) * 100.0
    observed_mean = mean(official)
    ss_res = sum((p - o) ** 2 for p, o in zip(predicted, official))
    ss_tot = sum((o - observed_mean) ** 2 for o in official)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    pearson = pearson_corr(official, predicted)
    return {
        "n": len(rows),
        "mae_pp": mae,
        "rmse_pp": rmse,
        "bias_pp": bias,
        "r2": r2,
        "pearson": pearson,
    }


def pearson_corr(xs: List[float], ys: List[float]) -> float:
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    denominator = math.sqrt(x_var * y_var)
    return numerator / denominator if denominator > 0 else float("nan")


def official_bin(value: float) -> str:
    if value < 0.3:
        return "low_official_lt_0p3"
    if value < 0.6:
        return "mid_official_0p3_0p6"
    return "high_official_ge_0p6"


def solid_group(value: float) -> str:
    if value <= 0:
        return "solid0_low_risk"
    if value <= 2:
        return "solid1_2_moderate_risk"
    return "solid3plus_high_risk"


def spatial_group(row: Dict[str, Any]) -> str:
    return "downstream_y_lt_0" if float(row["y_m"]) < 0 else "upstream_y_ge_0"


def group_summary(rows: List[Dict[str, Any]], label: str, group_name: str) -> Dict[str, Any]:
    residuals = [float(row["residual"]) for row in rows]
    abs_errors = [abs(float(row["residual"])) * 100.0 for row in rows]
    official = [float(row["official_velocity_ratio"]) for row in rows]
    predicted = [float(row["predicted_velocity_ratio"]) for row in rows]
    under_fraction = sum(1 for value in residuals if value < 0) / len(residuals) if residuals else 0.0
    return {
        "table": "group_summary",
        "row_id": f"{label}:{group_name}",
        "group_axis": label,
        "group": group_name,
        "n": len(rows),
        "official_mean": mean(official) if official else float("nan"),
        "predicted_mean": mean(predicted) if predicted else float("nan"),
        "mae_pp": mean(abs_errors) if abs_errors else float("nan"),
        "bias_pp": mean(residuals) * 100.0 if residuals else float("nan"),
        "under_fraction": under_fraction,
        "paper_use": "Use as residual-structure evidence for limitations and next-model targeting.",
        "limitations": "Group diagnostics do not improve official metrics and cannot support formal v0.4.0.",
    }


def build_group_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    specs = [
        ("official_speed_bin", official_bin),
        ("solid_corner_risk", lambda row: solid_group(float(row["solid_corner_neighbors_max"]))),
        ("windward_leeward_proxy", spatial_group),
    ]
    out: List[Dict[str, Any]] = []
    for label, key_fn in specs:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            key = key_fn(row if label != "official_speed_bin" else float(row["official_velocity_ratio"]))
            groups.setdefault(key, []).append(row)
        for key in sorted(groups):
            out.append(group_summary(groups[key], label, key))
    return out


def build_top_rows(rows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    total_sse = sum((float(row["residual"]) ** 2) for row in rows)
    out: List[Dict[str, Any]] = []
    for rank, row in enumerate(sorted(rows, key=lambda item: float(item["abs_error_pp"]), reverse=True)[:top_n], start=1):
        residual_pp = float(row["residual"]) * 100.0
        out.append(
            {
                "table": "top_residual_probe",
                "row_id": f"top_{rank:02d}",
                "rank": rank,
                "probe_id": int(row["No."]),
                "x_m": float(row["x_m"]),
                "y_m": float(row["y_m"]),
                "official_velocity_ratio": float(row["official_velocity_ratio"]),
                "predicted_velocity_ratio": float(row["predicted_velocity_ratio"]),
                "residual_pp": residual_pp,
                "abs_error_pp": abs(residual_pp),
                "sse_share": (float(row["residual"]) ** 2) / total_sse if total_sse > 0 else float("nan"),
                "solid_corner_neighbors_max": int(float(row["solid_corner_neighbors_max"])),
                "official_speed_bin": official_bin(float(row["official_velocity_ratio"])),
                "paper_use": "Use to identify localized residual drivers in the official negative validation.",
                "limitations": "Top-probe diagnostics are post-run interpretation only, not calibration or formal validation.",
            }
        )
    return out


def protocol_checks(rows: List[Dict[str, Any]], metrics: Dict[str, float]) -> Dict[str, bool]:
    return {
        "input_exists": INPUT_CSV.exists(),
        "probe_count_80": len(rows) == REQUIRED_N,
        "ids_1_to_80": sorted(int(row["No."]) for row in rows) == list(range(1, REQUIRED_N + 1)),
        "case_ac": all(str(row.get("case")) == REQUIRED_CASE for row in rows),
        "wind_direction_n": all(str(row.get("Wind_direction")) == REQUIRED_WIND_DIRECTION for row in rows),
        "height_z2m": all(abs(float(row.get("z_m", -999.0)) - REQUIRED_HEIGHT_M) < 1e-9 for row in rows),
        "raw_trilinear": all(str(row.get("sampling_mode")) == REQUIRED_SAMPLING for row in rows),
        "formal_metric_gate_failed": metrics["r2"] < 0.0 or metrics["mae_pp"] >= 15.0,
    }


def write_csv(rows: Iterable[Dict[str, Any]]) -> None:
    fieldnames = [
        "table",
        "row_id",
        "rank",
        "probe_id",
        "group_axis",
        "group",
        "n",
        "x_m",
        "y_m",
        "official_velocity_ratio",
        "predicted_velocity_ratio",
        "official_mean",
        "predicted_mean",
        "residual_pp",
        "abs_error_pp",
        "mae_pp",
        "bias_pp",
        "under_fraction",
        "sse_share",
        "solid_corner_neighbors_max",
        "official_speed_bin",
        "paper_use",
        "limitations",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(payload: Dict[str, Any]) -> None:
    metrics = payload["metrics"]
    checks = payload["checks"]
    lines = [
        "# Case E Official Residual Paper Table",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Table passed: {payload['official_residual_paper_table_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        "",
        "## Official Metric Context",
        "",
        f"- n: {metrics['n']}",
        f"- MAE: {metrics['mae_pp']:.6f} pp",
        f"- RMSE: {metrics['rmse_pp']:.6f} pp",
        f"- Bias: {metrics['bias_pp']:.6f} pp",
        f"- R2: {metrics['r2']:.6f}",
        f"- Pearson: {metrics['pearson']:.6f}",
        "",
        "## Protocol Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## Top Residual Probes",
        "",
        "| rank | probe | official | predicted | residual pp | abs error pp | sse share |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["top_residual_rows"]:
        lines.append(
            f"| {row['rank']} | {row['probe_id']} | {row['official_velocity_ratio']:.3f} | "
            f"{row['predicted_velocity_ratio']:.3f} | {row['residual_pp']:.3f} | "
            f"{row['abs_error_pp']:.3f} | {row['sse_share']:.3f} |"
        )
    lines += [
        "",
        "## Group Summary",
        "",
        "| axis | group | n | official mean | predicted mean | MAE pp | bias pp | under fraction |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["group_rows"]:
        lines.append(
            f"| {row['group_axis']} | {row['group']} | {row['n']} | {row['official_mean']:.3f} | "
            f"{row['predicted_mean']:.3f} | {row['mae_pp']:.3f} | {row['bias_pp']:.3f} | "
            f"{row['under_fraction']:.3f} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = read_rows(INPUT_CSV)
    metrics = metric_summary(rows)
    checks = protocol_checks(rows, metrics)
    top_rows = build_top_rows(rows)
    group_rows = build_group_rows(rows)
    passed = all(checks.values()) and checks["formal_metric_gate_failed"]
    combined_rows = top_rows + group_rows
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "limitations_ready_official_residual_paper_table",
        "official_residual_paper_table_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "input_csv": str(INPUT_CSV.relative_to(ROOT)),
        "metrics": metrics,
        "checks": checks,
        "top_residual_rows": top_rows,
        "group_rows": group_rows,
        "boundary": (
            "This table is derived from the official z=2 m residual CSV for manuscript diagnostics. "
            "It does not run FluidX3D, improve official metrics, support calibration-as-validation, "
            "or permit formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(combined_rows)
    write_markdown(payload)
    print(json.dumps({"official_residual_paper_table_passed": passed, "out_json": str(OUT_JSON.relative_to(ROOT))}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
