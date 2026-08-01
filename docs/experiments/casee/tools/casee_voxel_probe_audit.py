#!/usr/bin/env python3
"""Audit AIJ Case E official probes against STL geometry and voxel sampling."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
DATA_DIR = CASE_DIR / "official_data"
RESULTS_DIR = CASE_DIR / "results"

SCALE_FACTOR = 250.0
DOMAIN = {
    "origin_x": -300.0,
    "origin_y": -500.0,
    "origin_z": 0.0,
    "size_x": 600.0,
    "size_y": 800.0,
    "size_z": 240.0,
}

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]
Triangle = Tuple[Point3, Point3, Point3]


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


def parse_ascii_stl(path: Path, scale: float) -> List[Triangle]:
    triangles: List[Triangle] = []
    vertices: List[Point3] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.strip().split()
        if not parts:
            continue
        if parts[0] == "vertex" and len(parts) >= 4:
            vertices.append((float(parts[1]) * scale, float(parts[2]) * scale, float(parts[3]) * scale))
        elif parts[0] == "endfacet":
            if len(vertices) >= 3:
                triangles.append((vertices[-3], vertices[-2], vertices[-1]))
    if not triangles:
        raise SystemExit(f"No triangles parsed from {path}")
    return triangles


def mesh_bbox(triangles: Sequence[Triangle]) -> Dict[str, float]:
    xs = [p[0] for tri in triangles for p in tri]
    ys = [p[1] for tri in triangles for p in tri]
    zs = [p[2] for tri in triangles for p in tri]
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }


def point_segment_distance_2d(p: Point2, a: Point2, b: Point2) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay
    denom = vx * vx + vy * vy
    if denom <= 1e-24:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    qx = ax + t * vx
    qy = ay + t * vy
    return math.hypot(px - qx, py - qy)


def point_in_triangle_2d(p: Point2, a: Point2, b: Point2, c: Point2) -> bool:
    px, py = p
    ax, ay = a
    bx, by = b
    cx, cy = c
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) <= 1e-18:
        return False
    w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
    w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
    w3 = 1.0 - w1 - w2
    eps = -1e-9
    return w1 >= eps and w2 >= eps and w3 >= eps


def point_triangle_projection_distance_2d(p: Point2, tri: Triangle) -> float:
    a = (tri[0][0], tri[0][1])
    b = (tri[1][0], tri[1][1])
    c = (tri[2][0], tri[2][1])
    if point_in_triangle_2d(p, a, b, c):
        return 0.0
    return min(
        point_segment_distance_2d(p, a, b),
        point_segment_distance_2d(p, b, c),
        point_segment_distance_2d(p, c, a),
    )


def corr(xs: List[float], ys: List[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0.0 or vy <= 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def load_probe_predictions(path: Path) -> Dict[int, Dict[str, float]]:
    out: Dict[int, Dict[str, float]] = {}
    for row in read_csv(path):
        no = int(float(row.get("No.") or row.get("No") or row.get("probe_id")))
        out[no] = {
            "official": float(row["official_velocity_ratio"]),
            "raw": float(row["predicted_velocity_ratio"]),
            "z_plus_half": float(row.get("z_plus_half_velocity_ratio", row["predicted_velocity_ratio"])),
            "vertical_valid_above": float(row.get("vertical_valid_above_velocity_ratio", row["predicted_velocity_ratio"])),
            "solid_neighbors": float(row.get("solid_corner_neighbors_max", 0.0)),
        }
    return out


def voxel_info(x: float, y: float, z: float, dx: float, ground_offset_cells: int) -> Dict[str, object]:
    origin_z = DOMAIN["origin_z"] - ground_offset_cells * dx
    gx = (x - DOMAIN["origin_x"]) / dx - 0.5
    gy = (y - DOMAIN["origin_y"]) / dx - 0.5
    gz = (z - origin_z) / dx - 0.5
    x0 = math.floor(gx)
    y0 = math.floor(gy)
    z0 = math.floor(gz)
    tx = gx - x0
    ty = gy - y0
    tz = gz - z0
    return {
        "dx_m": dx,
        "ground_offset_cells": ground_offset_cells,
        "grid_x_float": gx,
        "grid_y_float": gy,
        "grid_z_float": gz,
        "grid_x0": x0,
        "grid_y0": y0,
        "grid_z0": z0,
        "grid_tx": tx,
        "grid_ty": ty,
        "grid_tz": tz,
        "lower_z_center_m": origin_z + (z0 + 0.5) * dx,
        "upper_z_center_m": origin_z + (z0 + 1.5) * dx,
        "straddles_two_z_layers": 0.0 < tz < 1.0,
    }


def classify_protocol_risk(distance_wall: float, distance_footprint: float, solid_neighbors: float, dx: float) -> str:
    if solid_neighbors >= 4 or distance_wall <= 0.25 * dx or distance_footprint <= 0.25 * dx:
        return "high"
    if solid_neighbors >= 2 or distance_wall <= 0.75 * dx or distance_footprint <= 0.75 * dx:
        return "moderate"
    return "low"


def audit(triangles: Sequence[Triangle], predictions: Dict[int, Dict[str, float]], dx: float, ground_offset_cells: int) -> List[Dict[str, object]]:
    probes = []
    for row in read_csv(DATA_DIR / "RS_caseE.csv"):
        if row["case"] == "ac" and row["Wind_direction"] == "N" and abs(float(row["z(m)"]) - 2.0) < 1e-9:
            probes.append(
                {
                    "no": int(row["No."]),
                    "x": float(row["x(m)"]),
                    "y": float(row["y(m)"]),
                    "z": float(row["z(m)"]),
                    "official": float(row["Velocity_Ratio"]),
                }
            )
    probes.sort(key=lambda p: int(p["no"]))
    if len(probes) != 80:
        raise SystemExit(f"Expected 80 official probes, found {len(probes)}")

    footprint_triangles = [tri for tri in triangles if max(p[2] for p in tri) >= 2.0]
    wall_triangles = [
        tri
        for tri in triangles
        if min(p[2] for p in tri) <= 2.0 <= max(p[2] for p in tri) and (max(p[2] for p in tri) - min(p[2] for p in tri)) >= 0.5
    ]

    out: List[Dict[str, object]] = []
    for probe in probes:
        point = (probe["x"], probe["y"])
        footprint_dist = min(point_triangle_projection_distance_2d(point, tri) for tri in footprint_triangles)
        wall_dist = min(point_triangle_projection_distance_2d(point, tri) for tri in wall_triangles)
        pred = predictions.get(int(probe["no"]), {})
        official = float(pred.get("official", probe["official"]))
        raw = float(pred.get("raw", float("nan")))
        zph = float(pred.get("z_plus_half", raw))
        vva = float(pred.get("vertical_valid_above", raw))
        solid_neighbors = float(pred.get("solid_neighbors", 0.0))
        info = voxel_info(probe["x"], probe["y"], probe["z"], dx, ground_offset_cells)
        out.append(
            {
                "No.": int(probe["no"]),
                "x_m": probe["x"],
                "y_m": probe["y"],
                "z_m": probe["z"],
                "official_velocity_ratio": official,
                "raw_trilinear_velocity_ratio": raw,
                "raw_abs_error_pp": abs(raw - official) * 100.0,
                "z_plus_half_velocity_ratio": zph,
                "z_plus_half_abs_error_pp": abs(zph - official) * 100.0,
                "vertical_valid_above_velocity_ratio": vva,
                "vertical_valid_above_abs_error_pp": abs(vva - official) * 100.0,
                "z_plus_half_improvement_pp": (abs(raw - official) - abs(zph - official)) * 100.0,
                "nearest_footprint_distance_m": footprint_dist,
                "nearest_wall_crossing_distance_m": wall_dist,
                "solid_corner_neighbors_max": int(solid_neighbors),
                "protocol_risk": classify_protocol_risk(wall_dist, footprint_dist, solid_neighbors, dx),
                **info,
            }
        )
    return out


def group_summary(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        groups.setdefault(str(row["protocol_risk"]), []).append(row)
    groups.setdefault("all", rows)
    out = []
    for key in ["low", "moderate", "high", "all"]:
        group = groups.get(key, [])
        if not group:
            continue
        out.append(
            {
                "group": key,
                "n": len(group),
                "raw_mae_pp": sum(float(r["raw_abs_error_pp"]) for r in group) / len(group),
                "z_plus_half_mae_pp": sum(float(r["z_plus_half_abs_error_pp"]) for r in group) / len(group),
                "vertical_valid_above_mae_pp": sum(float(r["vertical_valid_above_abs_error_pp"]) for r in group) / len(group),
                "mean_wall_distance_m": sum(float(r["nearest_wall_crossing_distance_m"]) for r in group) / len(group),
                "mean_footprint_distance_m": sum(float(r["nearest_footprint_distance_m"]) for r in group) / len(group),
                "mean_solid_neighbors": sum(float(r["solid_corner_neighbors_max"]) for r in group) / len(group),
            }
        )
    return out


def write_report(rows: List[Dict[str, object]], groups: List[Dict[str, object]], bbox: Dict[str, float], output: Path, prediction_path: Path) -> None:
    high = [r for r in rows if r["protocol_risk"] == "high"]
    low = [r for r in rows if r["protocol_risk"] == "low"]
    raw_errors = [float(r["raw_abs_error_pp"]) for r in rows]
    wall_distances = [float(r["nearest_wall_crossing_distance_m"]) for r in rows]
    footprint_distances = [float(r["nearest_footprint_distance_m"]) for r in rows]
    solid_neighbors = [float(r["solid_corner_neighbors_max"]) for r in rows]
    zph_improvements = [float(r["z_plus_half_improvement_pp"]) for r in rows]
    lines = [
        "# Case E Voxel/Probe Protocol Audit",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Prediction source: `{display_path(prediction_path)}`",
        "",
        "## Mesh and Grid",
        "",
        f"- STL scale factor: {SCALE_FACTOR:g}",
        f"- Physical mesh bbox: x [{bbox['min_x']:.3f}, {bbox['max_x']:.3f}], y [{bbox['min_y']:.3f}, {bbox['max_y']:.3f}], z [{bbox['min_z']:.3f}, {bbox['max_z']:.3f}] m.",
        "- Audited grid: dx = 2 m with one effective-ground offset cell.",
        "- Official z = 2 m lies halfway between the z = 1 m and z = 3 m lattice centers in this diagnostic setup.",
        "",
        "## Summary",
        "",
        f"- High protocol-risk probes: {len(high)} / {len(rows)}.",
        f"- Low protocol-risk probes: {len(low)} / {len(rows)}.",
        f"- Pearson(raw absolute error, wall distance): {corr(raw_errors, wall_distances):.6f}.",
        f"- Pearson(raw absolute error, footprint distance): {corr(raw_errors, footprint_distances):.6f}.",
        f"- Pearson(raw absolute error, solid-neighbor count): {corr(raw_errors, solid_neighbors):.6f}.",
        f"- Pearson(z_plus_half improvement, solid-neighbor count): {corr(zph_improvements, solid_neighbors):.6f}.",
        "- Claim readiness: limitations/protocol-risk evidence only.",
        "",
        "## Risk Groups",
        "",
        "| group | n | raw MAE pp | z_plus_half MAE pp | vertical_valid_above MAE pp | mean wall distance m | mean solid neighbors |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in groups:
        lines.append(
            f"| {row['group']} | {row['n']} | {float(row['raw_mae_pp']):.3f} | {float(row['z_plus_half_mae_pp']):.3f} | "
            f"{float(row['vertical_valid_above_mae_pp']):.3f} | {float(row['mean_wall_distance_m']):.3f} | {float(row['mean_solid_neighbors']):.3f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The official pedestrian-height probes are voxel-sensitive because z = 2 m is not a lattice-center height in the best dx = 2 m effective-ground diagnostic.",
        "The association between solid-neighbor count and diagnostic sampling improvement supports treating near-wall/probe protocol as a primary limitation.",
        "This audit does not validate predictive accuracy; it narrows the next software work toward explicit wall-distance-aware probe reporting and wall/voxelization model changes.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_plot(rows: List[Dict[str, object]], output: Path) -> None:
    try:
        import matplotlib.pyplot as plt

        colors = {"low": "#4C78A8", "moderate": "#F58518", "high": "#E45756"}
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
        for risk, color in colors.items():
            group = [r for r in rows if r["protocol_risk"] == risk]
            if not group:
                continue
            axes[0].scatter(
                [float(r["nearest_wall_crossing_distance_m"]) for r in group],
                [float(r["raw_abs_error_pp"]) for r in group],
                s=34,
                label=risk,
                color=color,
                alpha=0.85,
            )
            axes[1].scatter(
                [float(r["solid_corner_neighbors_max"]) for r in group],
                [float(r["z_plus_half_improvement_pp"]) for r in group],
                s=34,
                label=risk,
                color=color,
                alpha=0.85,
            )
        axes[0].set_xlabel("nearest wall-crossing distance (m)")
        axes[0].set_ylabel("raw abs error (pp)")
        axes[0].set_title("Probe error vs wall proximity")
        axes[1].axhline(0.0, color="black", linewidth=0.8)
        axes[1].set_xlabel("solid interpolation neighbors")
        axes[1].set_ylabel("z_plus_half improvement (pp)")
        axes[1].set_title("Sampling improvement vs solid-corner risk")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(output, dpi=180)
        plt.close(fig)
    except Exception as exc:
        output.with_suffix(".blocked.txt").write_text(str(exc), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stl", type=Path, default=DATA_DIR / "BD_caseE.stl")
    parser.add_argument("--predicted", type=Path, required=True)
    parser.add_argument("--dx", type=float, default=2.0)
    parser.add_argument("--ground-offset-cells", type=int, default=1)
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_voxel_probe_audit.csv")
    parser.add_argument("--out-groups", type=Path, default=RESULTS_DIR / "casee_voxel_probe_audit_groups.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_voxel_probe_audit.md")
    parser.add_argument("--out-png", type=Path, default=RESULTS_DIR / "casee_voxel_probe_audit.png")
    args = parser.parse_args()

    triangles = parse_ascii_stl(args.stl, SCALE_FACTOR)
    bbox = mesh_bbox(triangles)
    predictions = load_probe_predictions(args.predicted)
    rows = audit(triangles, predictions, args.dx, args.ground_offset_cells)
    groups = group_summary(rows)
    write_csv(
        args.out_csv,
        rows,
        [
            "No.",
            "x_m",
            "y_m",
            "z_m",
            "official_velocity_ratio",
            "raw_trilinear_velocity_ratio",
            "raw_abs_error_pp",
            "z_plus_half_velocity_ratio",
            "z_plus_half_abs_error_pp",
            "vertical_valid_above_velocity_ratio",
            "vertical_valid_above_abs_error_pp",
            "z_plus_half_improvement_pp",
            "nearest_footprint_distance_m",
            "nearest_wall_crossing_distance_m",
            "solid_corner_neighbors_max",
            "protocol_risk",
            "dx_m",
            "ground_offset_cells",
            "grid_x_float",
            "grid_y_float",
            "grid_z_float",
            "grid_x0",
            "grid_y0",
            "grid_z0",
            "grid_tx",
            "grid_ty",
            "grid_tz",
            "lower_z_center_m",
            "upper_z_center_m",
            "straddles_two_z_layers",
        ],
    )
    write_csv(
        args.out_groups,
        groups,
        [
            "group",
            "n",
            "raw_mae_pp",
            "z_plus_half_mae_pp",
            "vertical_valid_above_mae_pp",
            "mean_wall_distance_m",
            "mean_footprint_distance_m",
            "mean_solid_neighbors",
        ],
    )
    write_report(rows, groups, bbox, args.out_md, args.predicted)
    write_plot(rows, args.out_png)
    print(json.dumps({"triangles": len(triangles), "bbox": bbox, "groups": groups, "out_csv": str(args.out_csv)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
