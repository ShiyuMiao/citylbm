from __future__ import annotations

import csv
import math
import re
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE_DIR / "output"
CASE_FIG_DIR = CASE_DIR / "figures"
PROJECT_FIG_DIR = ROOT / "figures"
CASE_FIG_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_FIG_DIR.mkdir(parents=True, exist_ok=True)

LABEL_TEMPLATE = "core_prism_avg_wd{wd:03d}_dx2m_spin6k_s3"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
SAMPLES = [(0, "000008000"), (1, "000010000"), (2, "000012000")]
Z_LEVELS = [1, 2, 5, 10, 20]
PANEL_Z = 1
DX = 2.0
U_REF = 5.0


def read_vtk(path: Path):
    raw = path.read_bytes()
    marker = b"LOOKUP_TABLE default\n"
    start = raw.index(marker) + len(marker)
    header = raw[:start].decode("ascii", errors="replace")
    dims = tuple(int(v) for v in re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", header).groups())
    origin = tuple(float(v) for v in re.search(r"ORIGIN\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    spacing = tuple(float(v) for v in re.search(r"SPACING\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    point_data = int(re.search(r"POINT_DATA\s+(\d+)", header).group(1))
    scalar_match = re.search(r"SCALARS\s+\S+\s+(\S+)(?:\s+(\d+))?", header)
    dtype_name = scalar_match.group(1)
    components = int(scalar_match.group(2) or "1")
    dtype = ">f4" if dtype_name == "float" else np.uint8
    arr = np.frombuffer(raw, dtype=dtype, count=point_data * components, offset=start).copy()
    if dtype_name == "float":
        arr = arr.astype(np.float32)
    if components > 1:
        arr = arr.reshape((dims[2], dims[1], dims[0], components))
    else:
        arr = arr.reshape((dims[2], dims[1], dims[0]))
    return {"dims": dims, "origin": origin, "spacing": spacing}, arr


def extent_xy(meta):
    nx, ny, _ = meta["dims"]
    ox, oy, _ = meta["origin"]
    sx, sy, _ = meta["spacing"]
    return [ox, ox + sx * (nx - 1), oy, oy + sy * (ny - 1)]


def stat_values(values: np.ndarray):
    return {
        "vr_mean": float(np.mean(values)),
        "vr_p75": float(np.percentile(values, 75)),
        "vr_p90": float(np.percentile(values, 90)),
        "vr_p95": float(np.percentile(values, 95)),
        "vr_max": float(np.max(values)),
        "stagnation_ratio_vr_lt_0p2": float(np.mean(values < 0.2)),
        "accelerated_ratio_vr_gt_0p6": float(np.mean(values > 0.6)),
        "high_ratio_vr_gt_1p0": float(np.mean(values > 1.0)),
    }


def load_wind_weights():
    path = ROOT / "manifests" / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv"
    weights = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            weights[int(row["simulated_velocity_direction_deg"])] = float(row["weight"])
    total = sum(weights.values())
    return {wd: weights.get(wd, 0.0) / total for wd in WIND_DIRS}


def copy_if_space(src: Path, dst_dir: Path) -> Path:
    dst = dst_dir / src.name
    try:
        free = shutil.disk_usage(dst_dir).free
        if free < src.stat().st_size + 5_000_000:
            print(f"SKIP_COPY_NO_SPACE {src} -> {dst}", file=sys.stderr)
            return src
        shutil.copyfile(src, dst)
        return dst
    except OSError as exc:
        print(f"SKIP_COPY_ERROR {src} -> {dst}: {exc}", file=sys.stderr)
        return src


def main():
    weights = load_wind_weights()
    meta0 = None
    solid_by_z = {}
    time_mean_by_wd_z: dict[int, dict[int, np.ndarray]] = {}
    rows = []

    for wd in WIND_DIRS:
        label = LABEL_TEMPLATE.format(wd=wd)
        flags_path = OUT_DIR / f"matrix_{label}_flags_sample_2flags-000012000.vtk"
        meta, flags = read_vtk(flags_path)
        if meta0 is None:
            meta0 = meta
        time_mean_by_wd_z[wd] = {}

        for z in Z_LEVELS:
            solid_by_z.setdefault(z, (flags[z] & 1) > 0)

        speed_sum = {z: None for z in Z_LEVELS}
        for sample_idx, step in SAMPLES:
            u_path = OUT_DIR / f"matrix_{label}_u_sample_{sample_idx}u-{step}.vtk"
            _, u = read_vtk(u_path)
            speed = np.linalg.norm(u, axis=3) / U_REF
            for z in Z_LEVELS:
                if speed_sum[z] is None:
                    speed_sum[z] = speed[z].astype(np.float32)
                else:
                    speed_sum[z] += speed[z].astype(np.float32)

        for z in Z_LEVELS:
            arr = speed_sum[z] / float(len(SAMPLES))
            solid = solid_by_z[z]
            vals = arr[~solid]
            row = {
                "case": "core_prism_deepened_directional",
                "evidence_type": "newly_run",
                "wind_deg": wd,
                "wind_climate_weight": weights[wd],
                "dx_m": DX,
                "z_index": z,
                "height_m": z * DX,
                "open_cells": int((~solid).sum()),
                "solid_ratio": float(solid.mean()),
            }
            row.update(stat_values(vals))
            rows.append(row)
            time_mean_by_wd_z[wd][z] = np.where(~solid, arr, np.nan).astype(np.float32)

    # Spatial robustness at pedestrian height.
    stack = np.stack([time_mean_by_wd_z[wd][PANEL_Z] for wd in WIND_DIRS], axis=0)
    valid = ~np.isnan(stack)
    common_open = np.any(valid, axis=0)
    mean_map = np.nanmean(stack, axis=0)
    std_map = np.nanstd(stack, axis=0)
    min_map = np.nanmin(stack, axis=0)
    max_map = np.nanmax(stack, axis=0)
    range_map = max_map - min_map
    stag_freq = np.nanmean(stack < 0.2, axis=0)
    accel_freq = np.nanmean(stack > 0.6, axis=0)
    weighted_stag = np.zeros_like(mean_map, dtype=np.float32)
    weighted_accel = np.zeros_like(mean_map, dtype=np.float32)
    weighted_mean = np.zeros_like(mean_map, dtype=np.float32)
    for wd in WIND_DIRS:
        weighted_mean += np.nan_to_num(time_mean_by_wd_z[wd][PANEL_Z], nan=0.0) * weights[wd]
        weighted_stag += np.nan_to_num((time_mean_by_wd_z[wd][PANEL_Z] < 0.2).astype(np.float32), nan=0.0) * weights[wd]
        weighted_accel += np.nan_to_num((time_mean_by_wd_z[wd][PANEL_Z] > 0.6).astype(np.float32), nan=0.0) * weights[wd]
    best_idx = np.nanargmax(np.where(valid, stack, -np.inf), axis=0)
    best_dir = np.take(np.array(WIND_DIRS, dtype=np.float32), best_idx)
    best_dir[~common_open] = np.nan

    open_mask = common_open
    robustness_rows = [
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "mean_directional_std_vr",
            "value": float(np.nanmean(std_map[open_mask])),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "p95_directional_std_vr",
            "value": float(np.nanpercentile(std_map[open_mask], 95)),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "mean_directional_range_vr",
            "value": float(np.nanmean(range_map[open_mask])),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "robust_stagnation_ratio_freq_ge_0p75",
            "value": float(np.nanmean(stag_freq[open_mask] >= 0.75)),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "all_direction_stagnation_ratio",
            "value": float(np.nanmean(stag_freq[open_mask] >= 1.0)),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "climate_weighted_stagnation_probability_mean",
            "value": float(np.nanmean(weighted_stag[open_mask])),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "climate_weighted_stag_prob_ge_0p75_area_ratio",
            "value": float(np.nanmean(weighted_stag[open_mask] >= 0.75)),
        },
        {
            "case": "core_prism_deepened_spatial_robustness_z2m",
            "evidence_type": "newly_run",
            "metric": "directionally_accelerated_ratio_freq_ge_0p25",
            "value": float(np.nanmean(accel_freq[open_mask] >= 0.25)),
        },
    ]

    extent = extent_xy(meta0)
    solid_panel = solid_by_z[PANEL_Z]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), dpi=180, constrained_layout=True)
    panels = [
        (mean_map, "mean VR, 8-dir", "turbo", 0, 1.2),
        (std_map, "directional std(VR)", "magma", 0, 0.35),
        (range_map, "directional range(VR)", "magma", 0, 1.0),
        (stag_freq, "stagnation frequency\nVR<0.2 across 8 dirs", "viridis", 0, 1.0),
        (weighted_stag, "Open-Meteo weighted\nstagnation probability", "viridis", 0, 1.0),
        (best_dir, "best ventilation direction\nargmax VR", "twilight", 0, 360),
    ]
    for ax, (arr, title, cmap, vmin, vmax) in zip(axes.ravel(), panels):
        masked = np.ma.masked_where(solid_panel | np.isnan(arr), arr)
        im = ax.imshow(masked, origin="lower", extent=extent, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
        ax.contour(solid_panel.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.12)
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.suptitle("Deepened pedestrian-layer robustness analysis, core prism, z~2 m")
    robustness_png = CASE_FIG_DIR / "fluidx3d_core_prism_deepened_directional_robustness_z2m.png"
    fig.savefig(robustness_png)
    plt.close(fig)

    # Direction response figure at z~2m.
    z2_rows = [r for r in rows if math.isclose(r["height_m"], 2.0)]
    wds = [r["wind_deg"] for r in z2_rows]
    vr_means = [r["vr_mean"] for r in z2_rows]
    stag_ratios = [r["stagnation_ratio_vr_lt_0p2"] for r in z2_rows]
    climate_weights = [r["wind_climate_weight"] for r in z2_rows]
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), dpi=180, sharex=True, constrained_layout=True)
    axes[0].bar(wds, vr_means, width=30, color="#4C78A8")
    axes[0].set_ylabel("mean VR")
    axes[0].set_title("Pedestrian-layer directional response, z~2 m")
    axes[1].bar(wds, stag_ratios, width=30, color="#C44E52")
    axes[1].set_ylabel("VR<0.2 ratio")
    axes[1].set_ylim(0, 1)
    axes[2].bar(wds, climate_weights, width=30, color="#55A868")
    axes[2].set_ylabel("2024 proxy weight")
    axes[2].set_xlabel("FluidX3D velocity direction (deg)")
    axes[2].set_xticks(WIND_DIRS)
    direction_png = CASE_FIG_DIR / "fluidx3d_core_prism_deepened_direction_response_z2m.png"
    fig.savefig(direction_png)
    plt.close(fig)

    # Vertical profile figure.
    equal_rows = []
    weighted_rows = []
    metrics_csv = PROJECT_FIG_DIR / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv"
    with metrics_csv.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["averaging"] == "time_mean_3_samples_then_direction_mean":
                equal_rows.append(row)
    weighted_csv = PROJECT_FIG_DIR / "fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv"
    with weighted_csv.open(newline="", encoding="utf-8-sig") as f:
        weighted_rows = list(csv.DictReader(f))
    equal_rows.sort(key=lambda r: float(r["z_height_m_approx"]))
    weighted_rows.sort(key=lambda r: float(r["z_height_m_approx"]))
    heights = [float(r["z_height_m_approx"]) for r in equal_rows]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), dpi=180, constrained_layout=True)
    for rows_in, label, color in [(equal_rows, "equal 8-dir", "#4C78A8"), (weighted_rows, "Open-Meteo weighted", "#55A868")]:
        axes[0].plot([float(r["vr_mean"]) for r in rows_in], heights, marker="o", label=label, color=color)
        axes[1].plot([float(r["vr_p95"]) for r in rows_in], heights, marker="o", label=label, color=color)
        axes[2].plot([float(r["stagnation_ratio_vr_lt_0p2"]) for r in rows_in], heights, marker="o", label=label, color=color)
    axes[0].set_xlabel("VR mean")
    axes[1].set_xlabel("VR P95")
    axes[2].set_xlabel("VR<0.2 ratio")
    for ax in axes:
        ax.set_ylabel("height (m)")
        ax.grid(True, alpha=0.25)
        ax.legend()
    fig.suptitle("Vertical wind-speed recovery metrics, core prism")
    vertical_png = CASE_FIG_DIR / "fluidx3d_core_prism_deepened_vertical_profile.png"
    fig.savefig(vertical_png)
    plt.close(fig)

    direction_csv = CASE_FIG_DIR / "fluidx3d_core_prism_deepened_directional_summary.csv"
    with direction_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    robustness_csv = CASE_FIG_DIR / "fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv"
    with robustness_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(robustness_rows[0].keys()))
        writer.writeheader()
        writer.writerows(robustness_rows)

    for path in [robustness_png, direction_png, vertical_png, direction_csv, robustness_csv]:
        print(copy_if_space(path, PROJECT_FIG_DIR))


if __name__ == "__main__":
    main()
