#!/usr/bin/env python3
"""Audit whether poor Case E z=2 m correlation is caused by x/y convention drift."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"


Point = Dict[str, float]
Transform = Tuple[str, Callable[[float, float], Tuple[float, float]]]


TRANSFORMS: List[Transform] = [
    ("identity", lambda x, y: (x, y)),
    ("flip_x", lambda x, y: (-x, y)),
    ("flip_y", lambda x, y: (x, -y)),
    ("flip_x_and_y", lambda x, y: (-x, -y)),
    ("swap_xy", lambda x, y: (y, x)),
    ("swap_xy_flip_new_x", lambda x, y: (-y, x)),
    ("swap_xy_flip_new_y", lambda x, y: (y, -x)),
    ("swap_xy_flip_both", lambda x, y: (-y, -x)),
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


def metric_summary(y_true: List[float], y_pred: List[float]) -> Dict[str, float | int | None]:
    errors = [p - y for y, p in zip(y_true, y_pred)]
    return {
        "n": len(y_true),
        "mae_pp": 100.0 * sum(abs(e) for e in errors) / len(errors),
        "rmse_pp": 100.0 * math.sqrt(sum(e * e for e in errors) / len(errors)),
        "bias_pp": 100.0 * sum(errors) / len(errors),
        "r2": r2_score(y_true, y_pred),
        "pearson": pearson(y_true, y_pred),
    }


def load_points(path: Path, prediction_column: str) -> List[Point]:
    rows = []
    for row in read_csv(path):
        rows.append(
            {
                "no": float(row.get("No.") or row.get("No") or row.get("probe_id")),
                "x": float(row["x_m"]),
                "y": float(row["y_m"]),
                "official": float(row["official_velocity_ratio"]),
                "predicted": float(row[prediction_column]),
            }
        )
    if len(rows) != 80:
        raise SystemExit(f"Expected 80 probe rows, found {len(rows)} in {path}")
    return rows


def evaluate_transform(points: List[Point], transform: Transform) -> Dict[str, object]:
    name, fn = transform
    prediction_cloud = [(p["x"], p["y"], p["predicted"], p["no"]) for p in points]
    y_true: List[float] = []
    y_pred: List[float] = []
    distances: List[float] = []
    matched_ids: List[int] = []
    for p in points:
        tx, ty = fn(p["x"], p["y"])
        match = min(prediction_cloud, key=lambda q: (q[0] - tx) ** 2 + (q[1] - ty) ** 2)
        distances.append(math.hypot(match[0] - tx, match[1] - ty))
        matched_ids.append(int(match[3]))
        y_true.append(p["official"])
        y_pred.append(match[2])
    metrics = metric_summary(y_true, y_pred)
    return {
        "transform": name,
        **metrics,
        "mean_nearest_distance_m": sum(distances) / len(distances),
        "max_nearest_distance_m": max(distances),
        "unique_matched_predictions": len(set(matched_ids)),
    }


def write_report(rows: List[Dict[str, object]], prediction_path: Path, output: Path) -> None:
    best_pearson = max(rows, key=lambda r: float(r["pearson"]) if r["pearson"] is not None else -999.0)
    best_r2 = max(rows, key=lambda r: float(r["r2"]) if r["r2"] is not None else -999.0)
    identity = next(r for r in rows if r["transform"] == "identity")
    lines = [
        "# Case E Spatial Alignment Diagnostic",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Prediction source: `{prediction_path}`",
        "",
        "## Purpose",
        "",
        "This diagnostic checks whether poor official z=2 m correlation could be explained by a simple x/y coordinate convention drift.",
        "It reassigns each official probe to the nearest predicted probe after candidate coordinate transforms, then recomputes the official metrics.",
        "",
        "## Summary",
        "",
        f"- Identity Pearson: {float(identity['pearson']):.6f}; R2: {float(identity['r2']):.6f}; MAE: {float(identity['mae_pp']):.3f} pp.",
        f"- Best Pearson transform: `{best_pearson['transform']}` with Pearson {float(best_pearson['pearson']):.6f}.",
        f"- Best R2 transform: `{best_r2['transform']}` with R2 {float(best_r2['r2']):.6f}.",
        "- Claim readiness: limitations only. This is a coordinate-audit diagnostic, not an accuracy validation.",
        "",
        "## Transform Metrics",
        "",
        "| transform | MAE pp | R2 | Pearson | mean nearest m | unique matched |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['transform']} | {float(row['mae_pp']):.3f} | {float(row['r2']):.6f} | "
            f"{float(row['pearson']):.6f} | {float(row['mean_nearest_distance_m']):.2f} | {row['unique_matched_predictions']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "No tested x/y flip, swap, or 90-degree rotation makes the official z=2 m R2 positive.",
        "The current evidence therefore points away from a simple coordinate-convention error and toward near-wall sampling, wall modeling, inlet turbulence, voxelization, or probe-location protocol fidelity.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plot(rows: List[Dict[str, object]], output: Path) -> None:
    try:
        import matplotlib.pyplot as plt

        labels = [str(r["transform"]) for r in rows]
        pearsons = [float(r["pearson"]) for r in rows]
        r2s = [float(r["r2"]) for r in rows]
        x = range(len(rows))
        plt.figure(figsize=(10, 4.8))
        plt.bar([i - 0.18 for i in x], pearsons, width=0.36, label="Pearson")
        plt.bar([i + 0.18 for i in x], r2s, width=0.36, label="R2")
        plt.axhline(0.0, color="black", linewidth=0.8)
        plt.xticks(list(x), labels, rotation=35, ha="right")
        plt.ylabel("Metric value")
        plt.title("AIJ Case E z=2 m coordinate-transform diagnostic")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output, dpi=180)
        plt.close()
    except Exception as exc:
        output.with_suffix(".blocked.txt").write_text(str(exc), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicted", type=Path, required=True)
    parser.add_argument("--prediction-column", default="predicted_velocity_ratio")
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_spatial_alignment_diagnostic.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_spatial_alignment_diagnostic.md")
    parser.add_argument("--out-png", type=Path, default=RESULTS_DIR / "casee_spatial_alignment_diagnostic.png")
    args = parser.parse_args()

    points = load_points(args.predicted, args.prediction_column)
    rows = [evaluate_transform(points, transform) for transform in TRANSFORMS]
    write_csv(
        args.out_csv,
        rows,
        [
            "transform",
            "n",
            "mae_pp",
            "rmse_pp",
            "bias_pp",
            "r2",
            "pearson",
            "mean_nearest_distance_m",
            "max_nearest_distance_m",
            "unique_matched_predictions",
        ],
    )
    write_report(rows, args.predicted, args.out_md)
    write_plot(rows, args.out_png)
    print(json.dumps({"rows": rows, "out_csv": str(args.out_csv), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
