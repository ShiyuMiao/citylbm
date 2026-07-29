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

LABEL_TEMPLATE = "core_prism_wd{wd:03d}_dx2m_10k"
STEP = "000010000"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
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


def stats(values):
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


def main():
    rows = []
    panel_data = []
    equal_sum = {z: None for z in Z_LEVELS}
    equal_count = {z: None for z in Z_LEVELS}
    panel_meta = None
    panel_solid = None

    for wd in WIND_DIRS:
        label = LABEL_TEMPLATE.format(wd=wd)
        u_path = OUT_DIR / f"matrix_{label}_u_finalu-{STEP}.vtk"
        f_path = OUT_DIR / f"matrix_{label}_flags_finalflags-{STEP}.vtk"
        meta, u = read_vtk(u_path)
        _, flags = read_vtk(f_path)
        speed = np.linalg.norm(u, axis=3)
        vr = speed / U_REF
        if panel_meta is None:
            panel_meta = meta
        for z in Z_LEVELS:
            solid = (flags[z] & 1) > 0
            vals = vr[z][~solid]
            row = {
                "case": label,
                "evidence_type": "newly_run",
                "geometry": "core_photogrammetry_extent_prism_collision_z0",
                "wind_deg": wd,
                "dx_m": DX,
                "z_index": z,
                "z_height_m_approx": z * DX,
                "solid_cells": int(solid.sum()),
                "open_cells": int((~solid).sum()),
                "solid_ratio": float(solid.mean()),
            }
            row.update(stats(vals))
            rows.append(row)

            arr = np.where(~solid, vr[z], np.nan).astype(np.float32)
            if equal_sum[z] is None:
                equal_sum[z] = np.nan_to_num(arr, nan=0.0)
                equal_count[z] = (~np.isnan(arr)).astype(np.float32)
            else:
                equal_sum[z] += np.nan_to_num(arr, nan=0.0)
                equal_count[z] += (~np.isnan(arr)).astype(np.float32)

        panel_solid = (flags[PANEL_Z] & 1) > 0
        panel_data.append((wd, np.ma.masked_where(panel_solid, vr[PANEL_Z])))

    fig, axes = plt.subplots(2, 4, figsize=(18, 9), dpi=170, constrained_layout=True)
    extent = extent_xy(panel_meta)
    for ax, (wd, masked_vr) in zip(axes.ravel(), panel_data):
        im = ax.imshow(masked_vr, origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
        ax.contour(panel_solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.12)
        ax.set_title(f"WD {wd:03d}, z~{PANEL_Z*DX:.0f} m")
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.9)
    cbar.set_label("VR = |U| / Uref")
    fig.suptitle("Core photogrammetry-extent semantic prism FluidX3D, 8 directions, dx=2 m, z~2 m")
    panel_png = CASE_FIG_DIR / "fluidx3d_core_prism_8dir_dx2m_10k_vr_panel_z2m.png"
    fig.savefig(panel_png)
    plt.close(fig)

    equal_rows = []
    for z in Z_LEVELS:
        avg = np.divide(equal_sum[z], equal_count[z], out=np.full_like(equal_sum[z], np.nan), where=equal_count[z] > 0)
        vals = avg[~np.isnan(avg)]
        row = {
            "case": "equal_weighted_8dir",
            "evidence_type": "newly_run",
            "geometry": "core_photogrammetry_extent_prism_collision_z0",
            "wind_deg": "equal_weighted",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "open_cells": int(vals.size),
        }
        row.update(stats(vals))
        equal_rows.append(row)
        rows.append(row)

    avg_z = np.divide(equal_sum[PANEL_Z], equal_count[PANEL_Z], out=np.full_like(equal_sum[PANEL_Z], np.nan), where=equal_count[PANEL_Z] > 0)
    fig, ax = plt.subplots(figsize=(8, 9), dpi=180, constrained_layout=True)
    im = ax.imshow(np.ma.masked_invalid(avg_z), origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
    ax.contour(panel_solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.15)
    ax.set_title("Equal-weighted 8-direction VR, core prism, z~2 m")
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(im, ax=ax, label="VR = |U| / Uref")
    equal_png = CASE_FIG_DIR / "fluidx3d_core_prism_8dir_dx2m_10k_equal_weighted_vr_z2m.png"
    fig.savefig(equal_png)
    plt.close(fig)

    metrics_csv = CASE_FIG_DIR / "fluidx3d_core_prism_8dir_dx2m_10k_metrics.csv"
    with metrics_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for path in [panel_png, equal_png, metrics_csv]:
        shutil.copyfile(path, PROJECT_FIG_DIR / path.name)
        print(PROJECT_FIG_DIR / path.name)


if __name__ == "__main__":
    main()
