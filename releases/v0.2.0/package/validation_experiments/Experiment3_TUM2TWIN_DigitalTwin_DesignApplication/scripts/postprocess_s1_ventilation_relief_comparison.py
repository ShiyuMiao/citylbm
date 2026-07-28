from __future__ import annotations

import csv
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
CASE_FIG_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_FIG_DIR.mkdir(parents=True, exist_ok=True)

S0_TEMPLATE = "core_prism_avg_wd{wd:03d}_dx2m_spin6k_s3"
S1_TEMPLATE = "core_prism_s1_relief_avg_wd{wd:03d}_dx2m_spin6k_s3"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
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


def compute_scenario(scenario_id: str, label_template: str):
    rows = []
    panel_data = []
    equal_sum = {z: None for z in Z_LEVELS}
    equal_count = {z: None for z in Z_LEVELS}
    panel_meta = None
    panel_solid = None

    for wd in WIND_DIRS:
        label = label_template.format(wd=wd)
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
            time_avg = time_speed_sum[z] / float(len(SAMPLES))
            vals = time_avg[~solid]
            row = {
                "scenario": scenario_id,
                "case": label,
                "evidence_type": "newly_run",
                "averaging": "time_mean_3_samples",
                "wind_deg": wd,
                "dx_m": DX,
                "z_index": z,
                "z_height_m_approx": z * DX,
                "solid_ratio": float(solid.mean()),
                "open_cells": int((~solid).sum()),
            }
            row.update(stat_values(vals))
            rows.append(row)

            arr = np.where(~solid, time_avg, np.nan).astype(np.float32)
            if equal_sum[z] is None:
                equal_sum[z] = np.nan_to_num(arr, nan=0.0)
                equal_count[z] = (~np.isnan(arr)).astype(np.float32)
            else:
                equal_sum[z] += np.nan_to_num(arr, nan=0.0)
                equal_count[z] += (~np.isnan(arr)).astype(np.float32)

        panel_solid = solid_by_z[PANEL_Z]
        panel_data.append((wd, np.ma.masked_where(panel_solid, time_speed_sum[PANEL_Z] / float(len(SAMPLES)))))

    equal_maps = {}
    for z in Z_LEVELS:
        avg = np.divide(equal_sum[z], equal_count[z], out=np.full_like(equal_sum[z], np.nan), where=equal_count[z] > 0)
        vals = avg[~np.isnan(avg)]
        row = {
            "scenario": scenario_id,
            "case": f"{scenario_id}_equal_weighted_8dir",
            "evidence_type": "newly_run",
            "averaging": "time_mean_3_samples_then_direction_mean",
            "wind_deg": "equal_weighted",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "open_cells": int(vals.size),
        }
        row.update(stat_values(vals))
        rows.append(row)
        equal_maps[z] = avg

    return {
        "scenario": scenario_id,
        "meta": panel_meta,
        "rows": rows,
        "panel_data": panel_data,
        "panel_solid": panel_solid,
        "equal_maps": equal_maps,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_s1_panel(s1):
    extent = extent_xy(s1["meta"])
    fig, axes = plt.subplots(2, 4, figsize=(18, 9), dpi=170, constrained_layout=True)
    for ax, (wd, masked_vr) in zip(axes.ravel(), s1["panel_data"]):
        im = ax.imshow(masked_vr, origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
        ax.contour(s1["panel_solid"].astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.12)
        ax.set_title(f"S1 WD {wd:03d}, z~{PANEL_Z*DX:.0f} m")
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.9)
    cbar.set_label("VR = |U| / Uref")
    fig.suptitle("S1 ventilation-relief FluidX3D, time-mean of 3 samples, 8 directions, dx=2 m")
    path = CASE_FIG_DIR / "fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_vr_panel_z2m.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_comparison(s0, s1):
    extent = extent_xy(s0["meta"])
    z = PANEL_Z
    s0_map = s0["equal_maps"][z]
    s1_map = s1["equal_maps"][z]
    common = ~np.isnan(s0_map) & ~np.isnan(s1_map)
    delta = np.where(common, s1_map - s0_map, np.nan)
    fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=170, constrained_layout=True)
    im0 = axes[0].imshow(np.ma.masked_invalid(s0_map), origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
    axes[0].set_title("S0 equal-weighted VR, z~2 m")
    im1 = axes[1].imshow(np.ma.masked_invalid(s1_map), origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
    axes[1].set_title("S1 equal-weighted VR, z~2 m")
    im2 = axes[2].imshow(np.ma.masked_invalid(delta), origin="lower", extent=extent, cmap="coolwarm", vmin=-0.25, vmax=0.25, interpolation="nearest")
    axes[2].set_title("S1 - S0 VR delta, common open cells")
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
    fig.colorbar(im0, ax=axes[:2].tolist(), label="VR = |U| / Uref", shrink=0.86)
    fig.colorbar(im2, ax=axes[2], label="Delta VR", shrink=0.86)
    path = CASE_FIG_DIR / "fluidx3d_s0_s1_ventilation_relief_equal_weighted_vr_delta_z2m.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def comparison_rows(s0_rows, s1_rows):
    s0_equal = {
        int(r["z_index"]): r for r in s0_rows
        if r["wind_deg"] == "equal_weighted"
    }
    s1_equal = {
        int(r["z_index"]): r for r in s1_rows
        if r["wind_deg"] == "equal_weighted"
    }
    metric_names = [
        "vr_mean",
        "vr_p75",
        "vr_p90",
        "vr_p95",
        "vr_max",
        "stagnation_ratio_vr_lt_0p2",
        "accelerated_ratio_vr_gt_0p6",
        "high_ratio_vr_gt_1p0",
    ]
    rows = []
    for z in Z_LEVELS:
        row = {
            "evidence_type": "newly_run",
            "comparison": "S1_minus_S0",
            "averaging": "time_mean_3_samples_then_direction_mean",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "s0_open_cells": s0_equal[z]["open_cells"],
            "s1_open_cells": s1_equal[z]["open_cells"],
            "delta_open_cells": int(s1_equal[z]["open_cells"]) - int(s0_equal[z]["open_cells"]),
        }
        for m in metric_names:
            s0v = float(s0_equal[z][m])
            s1v = float(s1_equal[z][m])
            row[f"s0_{m}"] = s0v
            row[f"s1_{m}"] = s1v
            row[f"delta_{m}"] = s1v - s0v
            row[f"relative_delta_{m}"] = (s1v - s0v) / s0v if s0v != 0.0 else ""
        rows.append(row)
    return rows


def open_cell_delta_rows(s0, s1):
    rows = []
    for z in Z_LEVELS:
        s0_map = s0["equal_maps"][z]
        s1_map = s1["equal_maps"][z]
        s0_open = ~np.isnan(s0_map)
        s1_open = ~np.isnan(s1_map)
        common = s0_open & s1_open
        newly_open = ~s0_open & s1_open
        closed = s0_open & ~s1_open
        delta = s1_map - s0_map
        common_delta = delta[common]
        new_vals = s1_map[newly_open]
        row = {
            "evidence_type": "newly_run",
            "comparison": "S1_minus_S0_common_and_newly_open_cells",
            "averaging": "time_mean_3_samples_then_direction_mean",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "s0_open_cells": int(s0_open.sum()),
            "s1_open_cells": int(s1_open.sum()),
            "common_open_cells": int(common.sum()),
            "newly_open_cells": int(newly_open.sum()),
            "closed_cells": int(closed.sum()),
        }
        if common_delta.size:
            row.update({
                "common_delta_vr_mean": float(common_delta.mean()),
                "common_delta_vr_p05": float(np.percentile(common_delta, 5)),
                "common_delta_vr_p50": float(np.percentile(common_delta, 50)),
                "common_delta_vr_p95": float(np.percentile(common_delta, 95)),
                "common_delta_vr_min": float(common_delta.min()),
                "common_delta_vr_max": float(common_delta.max()),
                "common_ratio_delta_gt_0p02": float((common_delta > 0.02).mean()),
                "common_ratio_delta_lt_minus_0p02": float((common_delta < -0.02).mean()),
            })
        else:
            row.update({
                "common_delta_vr_mean": "",
                "common_delta_vr_p05": "",
                "common_delta_vr_p50": "",
                "common_delta_vr_p95": "",
                "common_delta_vr_min": "",
                "common_delta_vr_max": "",
                "common_ratio_delta_gt_0p02": "",
                "common_ratio_delta_lt_minus_0p02": "",
            })
        if new_vals.size:
            row.update({
                "newly_open_s1_vr_mean": float(new_vals.mean()),
                "newly_open_s1_vr_p95": float(np.percentile(new_vals, 95)),
                "newly_open_stagnation_ratio_vr_lt_0p2": float((new_vals < 0.2).mean()),
                "newly_open_acceleration_ratio_vr_gt_0p6": float((new_vals > 0.6).mean()),
            })
        else:
            row.update({
                "newly_open_s1_vr_mean": "",
                "newly_open_s1_vr_p95": "",
                "newly_open_stagnation_ratio_vr_lt_0p2": "",
                "newly_open_acceleration_ratio_vr_gt_0p6": "",
            })
        rows.append(row)
    return rows


def plot_height_summary(comp_rows):
    heights = [r["z_height_m_approx"] for r in comp_rows]
    s0_mean = [r["s0_vr_mean"] for r in comp_rows]
    s1_mean = [r["s1_vr_mean"] for r in comp_rows]
    s0_stag = [r["s0_stagnation_ratio_vr_lt_0p2"] for r in comp_rows]
    s1_stag = [r["s1_stagnation_ratio_vr_lt_0p2"] for r in comp_rows]
    x = np.arange(len(heights))
    width = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=170, constrained_layout=True)
    axes[0].bar(x - width/2, s0_mean, width, label="S0")
    axes[0].bar(x + width/2, s1_mean, width, label="S1")
    axes[0].set_xticks(x, [f"{h:g} m" for h in heights])
    axes[0].set_ylabel("Mean VR")
    axes[0].set_title("Mean VR by height")
    axes[0].legend()
    axes[1].bar(x - width/2, s0_stag, width, label="S0")
    axes[1].bar(x + width/2, s1_stag, width, label="S1")
    axes[1].set_xticks(x, [f"{h:g} m" for h in heights])
    axes[1].set_ylabel("VR<0.2 ratio")
    axes[1].set_title("Stagnation ratio by height")
    axes[1].legend()
    path = CASE_FIG_DIR / "fluidx3d_s0_s1_ventilation_relief_height_metric_comparison.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main():
    s0 = compute_scenario("S0", S0_TEMPLATE)
    s1 = compute_scenario("S1", S1_TEMPLATE)
    metrics_path = CASE_FIG_DIR / "fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_metrics.csv"
    write_csv(metrics_path, s1["rows"])

    comp = comparison_rows(s0["rows"], s1["rows"])
    comp_path = CASE_FIG_DIR / "fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv"
    write_csv(comp_path, comp)
    open_delta = open_cell_delta_rows(s0, s1)
    open_delta_path = CASE_FIG_DIR / "fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv"
    write_csv(open_delta_path, open_delta)

    panel = plot_s1_panel(s1)
    delta = plot_comparison(s0, s1)
    height_fig = plot_height_summary(comp)

    for path in [metrics_path, comp_path, open_delta_path, panel, delta, height_fig]:
        shutil.copyfile(path, PROJECT_FIG_DIR / path.name)
        print(PROJECT_FIG_DIR / path.name)


if __name__ == "__main__":
    main()
