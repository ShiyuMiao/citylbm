from __future__ import annotations

import csv
import json
import math
import re
import shutil
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
MANIFESTS = ROOT / "manifests"
REPORTS = ROOT / "reports"
RAW_WIND = Path(r"D:\citylbm_tum2twin_heavy_store\raw\wind_climate_open_meteo\open_meteo_tum_city_campus_2024_hourly_wind_10m.json")

LABEL_TEMPLATE = "core_prism_avg_wd{wd:03d}_dx2m_spin6k_s3"
WIND_DIRS = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=int)
SAMPLES = [(0, "000008000"), (1, "000010000"), (2, "000012000")]
DX = 2.0
U_REF = 5.0
Z_LEVELS = [1, 2, 5, 10, 20]
PANEL_Z = 1


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


def nearest_45(angle):
    return int((round(angle / 45.0) * 45) % 360)


def load_wind_weights():
    data = json.loads(RAW_WIND.read_text(encoding="utf-8"))
    hourly = data["hourly"]
    speeds = np.array(hourly["wind_speed_10m"], dtype=float)
    met_from = np.array(hourly["wind_direction_10m"], dtype=float)
    valid = np.isfinite(speeds) & np.isfinite(met_from)
    speeds = speeds[valid]
    met_from = met_from[valid]
    flow_to = (met_from + 180.0) % 360.0
    bins = np.array([nearest_45(a) for a in flow_to], dtype=int)

    rows = []
    weights = {}
    for wd in WIND_DIRS:
        mask = bins == wd
        count = int(mask.sum())
        weights[int(wd)] = count / float(len(bins))
        vals = speeds[mask]
        rows.append({
            "simulated_velocity_direction_deg": int(wd),
            "hours": count,
            "weight": weights[int(wd)],
            "mean_wind_speed_10m_ms": float(vals.mean()) if vals.size else 0.0,
            "p50_wind_speed_10m_ms": float(np.percentile(vals, 50)) if vals.size else 0.0,
            "p90_wind_speed_10m_ms": float(np.percentile(vals, 90)) if vals.size else 0.0,
        })
    return data, speeds, met_from, flow_to, bins, rows, weights


def stat_values(values):
    return {
        "vr_mean": float(values.mean()),
        "vr_p75": float(np.percentile(values, 75)),
        "vr_p90": float(np.percentile(values, 90)),
        "vr_p95": float(np.percentile(values, 95)),
        "vr_max": float(values.max()),
        "stagnation_ratio_vr_lt_0p2": float((values < 0.2).mean()),
        "accelerated_ratio_vr_gt_0p6": float((values > 0.6).mean()),
        "high_ratio_vr_gt_1p0": float((values > 1.0).mean()),
    }


def write_windrose_figure(rows):
    theta = np.deg2rad([r["simulated_velocity_direction_deg"] for r in rows])
    radii = np.array([r["weight"] for r in rows])
    width = np.deg2rad(45)
    fig = plt.figure(figsize=(8, 8), dpi=180)
    ax = fig.add_subplot(111, projection="polar")
    ax.bar(theta, radii, width=width, bottom=0.0, color="#2c7fb8", edgecolor="white", linewidth=1.0, align="center")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title("Open-Meteo 2024 wind climate proxy\nvelocity-to sectors after meteorological from-direction conversion")
    ax.set_rlabel_position(225)
    fig.tight_layout()
    out = PROJECT_FIG_DIR / "open_meteo_tum_city_campus_2024_windrose_8dir_velocity_to.png"
    fig.savefig(out)
    plt.close(fig)
    shutil.copyfile(out, CASE_FIG_DIR / out.name)
    return out


def main():
    data, speeds, met_from, flow_to, bins, wind_rows, weights = load_wind_weights()
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    weights_csv = MANIFESTS / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv"
    with weights_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(wind_rows[0]))
        writer.writeheader()
        writer.writerows(wind_rows)
    rose_png = write_windrose_figure(wind_rows)

    rows = []
    weighted_sum = {z: None for z in Z_LEVELS}
    weighted_count = {z: None for z in Z_LEVELS}
    panel_meta = None
    panel_solid = None

    for wd in WIND_DIRS:
        label = LABEL_TEMPLATE.format(wd=int(wd))
        flags_path = OUT_DIR / f"matrix_{label}_flags_sample_2flags-000012000.vtk"
        meta, flags = read_vtk(flags_path)
        if panel_meta is None:
            panel_meta = meta
        solid_by_z = {z: (flags[z] & 1) > 0 for z in Z_LEVELS}
        time_speed_sum = {z: None for z in Z_LEVELS}
        for sample_idx, step in SAMPLES:
            u_path = OUT_DIR / f"matrix_{label}_u_sample_{sample_idx}u-{step}.vtk"
            _, u = read_vtk(u_path)
            speed = np.linalg.norm(u, axis=3) / U_REF
            for z in Z_LEVELS:
                if time_speed_sum[z] is None:
                    time_speed_sum[z] = speed[z].astype(np.float32)
                else:
                    time_speed_sum[z] += speed[z].astype(np.float32)
        for z in Z_LEVELS:
            solid = solid_by_z[z]
            avg = time_speed_sum[z] / float(len(SAMPLES))
            arr = np.where(~solid, avg, np.nan).astype(np.float32)
            w = weights[int(wd)]
            if weighted_sum[z] is None:
                weighted_sum[z] = np.nan_to_num(arr, nan=0.0) * w
                weighted_count[z] = (~np.isnan(arr)).astype(np.float32) * w
            else:
                weighted_sum[z] += np.nan_to_num(arr, nan=0.0) * w
                weighted_count[z] += (~np.isnan(arr)).astype(np.float32) * w
        panel_solid = solid_by_z[PANEL_Z]

    for z in Z_LEVELS:
        weighted = np.divide(weighted_sum[z], weighted_count[z], out=np.full_like(weighted_sum[z], np.nan), where=weighted_count[z] > 0)
        vals = weighted[~np.isnan(weighted)]
        row = {
            "case": "open_meteo_2024_weighted_8dir",
            "evidence_type": "newly_run + preexisting_artifact",
            "wind_climate_source": str(RAW_WIND),
            "averaging": "time_mean_3_samples_then_open_meteo_2024_direction_weight",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "open_cells": int(vals.size),
        }
        row.update(stat_values(vals))
        rows.append(row)

    extent = extent_xy(panel_meta)
    weighted_z = np.divide(weighted_sum[PANEL_Z], weighted_count[PANEL_Z], out=np.full_like(weighted_sum[PANEL_Z], np.nan), where=weighted_count[PANEL_Z] > 0)
    fig, ax = plt.subplots(figsize=(8, 9), dpi=180, constrained_layout=True)
    im = ax.imshow(np.ma.masked_invalid(weighted_z), origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
    ax.contour(panel_solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.15)
    ax.set_title("Open-Meteo 2024 direction-weighted VR, core prism, z~2 m")
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=ax, label="VR = |U| / Uref")
    weighted_png = PROJECT_FIG_DIR / "fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png"
    fig.savefig(weighted_png)
    plt.close(fig)
    shutil.copyfile(weighted_png, CASE_FIG_DIR / weighted_png.name)

    metrics_csv = PROJECT_FIG_DIR / "fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv"
    with metrics_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    shutil.copyfile(metrics_csv, CASE_FIG_DIR / metrics_csv.name)

    report = REPORTS / "wind_climate_weighted_core_prism_report.md"
    report.write_text(
        "# Wind-Climate Weighted Core Prism Report\n\n"
        "evidence_type: newly_run + preexisting_artifact\n\n"
        "Open-Meteo Historical Weather API hourly wind speed/direction data for 2024 was used as a wind-climate proxy for the TUM City Campus location (`48.148, 11.568`). The API documentation states that historical weather data are based on reanalysis datasets and include hourly wind speed/direction variables.\n\n"
        "Direction convention: Open-Meteo wind direction is treated as meteorological from-direction. It was converted to a velocity-to direction by adding 180 degrees, then assigned to the nearest 45-degree FluidX3D simulated velocity-direction sector. This assumes no additional local model rotation; therefore the weighted result is a climate-proxy sensitivity layer, not a final measured exceedance-probability comfort assessment.\n\n"
        f"- Raw data: `{RAW_WIND}`\n"
        f"- Weights CSV: `{weights_csv}`\n"
        f"- Wind rose figure: `{rose_png}`\n"
        f"- Weighted VR figure: `{weighted_png}`\n"
        f"- Weighted metrics CSV: `{metrics_csv}`\n\n"
        "## 2024 Direction Weights\n\n"
        "| Velocity-to sector (deg) | Hours | Weight | Mean wind speed 10m (m/s) |\n"
        "|---:|---:|---:|---:|\n"
        + "\n".join(
            f"| {r['simulated_velocity_direction_deg']} | {r['hours']} | {r['weight']:.3f} | {r['mean_wind_speed_10m_ms']:.2f} |"
            for r in wind_rows
        )
        + "\n\n## Weighted Metrics\n\n"
        "| Height (m) | VR mean | VR P95 | Stagnation VR<0.2 |\n"
        "|---:|---:|---:|---:|\n"
        + "\n".join(
            f"| {r['z_height_m_approx']:.0f} | {r['vr_mean']:.3f} | {r['vr_p95']:.3f} | {r['stagnation_ratio_vr_lt_0p2']:.3f} |"
            for r in rows
        )
        + "\n",
        encoding="utf-8",
    )

    print(weights_csv)
    print(rose_png)
    print(weighted_png)
    print(metrics_csv)
    print(report)


if __name__ == "__main__":
    main()
