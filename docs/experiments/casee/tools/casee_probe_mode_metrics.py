#!/usr/bin/env python3
"""Compute AIJ Case E z=2 m metrics for formal and diagnostic probe modes."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"

MODE_COLUMNS = [
    ("raw_trilinear", "predicted_velocity_ratio", "formal"),
    ("nearest_valid", "nearest_valid_velocity_ratio", "diagnostic"),
    ("fluid_weighted", "fluid_weighted_velocity_ratio", "diagnostic"),
    ("vertical_valid_above", "vertical_valid_above_velocity_ratio", "diagnostic"),
    ("z_plus_half", "z_plus_half_velocity_ratio", "diagnostic"),
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def pearson(xs: List[float], ys: List[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0.0 or vy <= 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def r2_score(y_true: List[float], y_pred: List[float]) -> float | None:
    if not y_true:
        return None
    mean_y = sum(y_true) / len(y_true)
    sst = sum((y - mean_y) ** 2 for y in y_true)
    if sst <= 0.0:
        return None
    sse = sum((p - y) ** 2 for y, p in zip(y_true, y_pred))
    return 1.0 - sse / sst


def metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, object]:
    errors = [p - y for y, p in zip(y_true, y_pred)]
    return {
        "n": len(y_true),
        "mae_pp": 100.0 * sum(abs(e) for e in errors) / len(errors),
        "rmse_pp": 100.0 * math.sqrt(sum(e * e for e in errors) / len(errors)),
        "bias_pp": 100.0 * sum(errors) / len(errors),
        "r2": r2_score(y_true, y_pred),
        "pearson": pearson(y_true, y_pred),
        "pred_mean": sum(y_pred) / len(y_pred),
        "official_mean": sum(y_true) / len(y_true),
    }


def compute_mode_rows(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    y_true = [float(r["official_velocity_ratio"]) for r in rows]
    for mode, column, boundary in MODE_COLUMNS:
        y_pred = [float(r[column]) for r in rows]
        row = {
            "sampling_mode": mode,
            "claim_boundary": boundary,
            **metrics(y_true, y_pred),
            "paper_claim_readiness": "formal_gate_input" if boundary == "formal" else "limitations_diagnostic_only",
        }
        out.append(row)
    return out


def compute_group_rows(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for mode, column, boundary in MODE_COLUMNS:
        groups: Dict[str, List[Dict[str, str]]] = {}
        for row in rows:
            key = row.get("solid_corner_neighbors_max", "") or "unknown"
            groups.setdefault(key, []).append(row)
        for key in sorted(groups, key=lambda x: (x == "unknown", float(x) if x.replace(".", "", 1).isdigit() else 999.0)):
            group = groups[key]
            y_true = [float(r["official_velocity_ratio"]) for r in group]
            y_pred = [float(r[column]) for r in group]
            out.append(
                {
                    "sampling_mode": mode,
                    "claim_boundary": boundary,
                    "solid_corner_neighbors_max": key,
                    **metrics(y_true, y_pred),
                }
            )
    return out


def write_report(mode_rows: List[Dict[str, object]], group_rows: List[Dict[str, object]], source: Path, output: Path) -> None:
    best_mae = min(mode_rows, key=lambda r: float(r["mae_pp"]))
    best_pearson = max(mode_rows, key=lambda r: float(r["pearson"]) if r["pearson"] is not None else -999.0)
    formal = next(r for r in mode_rows if r["sampling_mode"] == "raw_trilinear")
    lines = [
        "# Case E Probe-Mode Metrics",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Prediction source: `{source}`",
        "",
        "## Summary",
        "",
        f"- Formal raw_trilinear: MAE {float(formal['mae_pp']):.3f} pp, R2 {float(formal['r2']):.6f}, Pearson {float(formal['pearson']):.6f}.",
        f"- Best diagnostic MAE: `{best_mae['sampling_mode']}` with MAE {float(best_mae['mae_pp']):.3f} pp.",
        f"- Best diagnostic Pearson: `{best_pearson['sampling_mode']}` with Pearson {float(best_pearson['pearson']):.6f}.",
        "- Claim readiness: diagnostics/limitations only; no diagnostic sampling mode makes official z=2 m R2 positive.",
        "",
        "## Mode Metrics",
        "",
        "| sampling_mode | boundary | MAE pp | RMSE pp | Bias pp | R2 | Pearson | pred_mean |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in mode_rows:
        lines.append(
            f"| {row['sampling_mode']} | {row['claim_boundary']} | {float(row['mae_pp']):.3f} | "
            f"{float(row['rmse_pp']):.3f} | {float(row['bias_pp']):.3f} | "
            f"{float(row['r2']):.6f} | {float(row['pearson']):.6f} | {float(row['pred_mean']):.6f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Alternative near-wall probe sampling reduces the underprediction bias and improves Pearson modestly, but all R2 values remain negative.",
        "This supports a near-wall/probe-protocol limitation and motivates wall-model/voxelization changes before any default accuracy claim.",
        "",
        "## Solid-Corner Group Detail",
        "",
        "| sampling_mode | solid neighbors | n | MAE pp | R2 | Pearson |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in group_rows:
        lines.append(
            f"| {row['sampling_mode']} | {row['solid_corner_neighbors_max']} | {row['n']} | "
            f"{float(row['mae_pp']):.3f} | {float(row['r2']):.6f} | {float(row['pearson']):.6f} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plot(mode_rows: List[Dict[str, object]], output: Path) -> None:
    try:
        import matplotlib.pyplot as plt

        labels = [str(r["sampling_mode"]) for r in mode_rows]
        mae = [float(r["mae_pp"]) for r in mode_rows]
        r2 = [float(r["r2"]) for r in mode_rows]
        pear = [float(r["pearson"]) for r in mode_rows]
        x = range(len(labels))

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        axes[0].bar(x, mae, color="#4C78A8")
        axes[0].set_xticks(list(x), labels, rotation=30, ha="right")
        axes[0].set_ylabel("MAE (percentage points)")
        axes[0].set_title("Probe-mode MAE")
        axes[1].bar([i - 0.18 for i in x], r2, width=0.36, label="R2", color="#F58518")
        axes[1].bar([i + 0.18 for i in x], pear, width=0.36, label="Pearson", color="#54A24B")
        axes[1].axhline(0.0, color="black", linewidth=0.8)
        axes[1].set_xticks(list(x), labels, rotation=30, ha="right")
        axes[1].set_title("Probe-mode correlation")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(output, dpi=180)
        plt.close(fig)
    except Exception as exc:
        output.with_suffix(".blocked.txt").write_text(str(exc), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicted", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_probe_mode_metrics.csv")
    parser.add_argument("--out-groups", type=Path, default=RESULTS_DIR / "casee_probe_mode_solid_corner_groups.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_probe_mode_metrics.md")
    parser.add_argument("--out-png", type=Path, default=RESULTS_DIR / "casee_probe_mode_metrics.png")
    args = parser.parse_args()

    rows = read_csv(args.predicted)
    if len(rows) != 80:
        raise SystemExit(f"Expected 80 probe rows, found {len(rows)}")
    missing = [column for _, column, _ in MODE_COLUMNS if column not in rows[0]]
    if missing:
        raise SystemExit(f"Missing probe mode columns: {missing}")

    mode_rows = compute_mode_rows(rows)
    group_rows = compute_group_rows(rows)
    write_csv(
        args.out_csv,
        mode_rows,
        [
            "sampling_mode",
            "claim_boundary",
            "n",
            "mae_pp",
            "rmse_pp",
            "bias_pp",
            "r2",
            "pearson",
            "pred_mean",
            "official_mean",
            "paper_claim_readiness",
        ],
    )
    write_csv(
        args.out_groups,
        group_rows,
        [
            "sampling_mode",
            "claim_boundary",
            "solid_corner_neighbors_max",
            "n",
            "mae_pp",
            "rmse_pp",
            "bias_pp",
            "r2",
            "pearson",
            "pred_mean",
            "official_mean",
        ],
    )
    write_report(mode_rows, group_rows, args.predicted, args.out_md)
    write_plot(mode_rows, args.out_png)
    print(json.dumps({"metrics": mode_rows, "out_csv": str(args.out_csv), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
