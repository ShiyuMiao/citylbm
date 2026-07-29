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

DIRECTIONS = [0, 45, 90, 135, 180, 225, 270, 315]
DX = 6.0
U_REF = 5.0
STEP = "000010000"
Z_AUDIT = 2
Z_METRIC = [1, 2, 4, 8]


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


def metrics(case, wind_deg, vr, flags, z_index):
    solid = (flags[z_index] & 1) > 0
    values = vr[z_index][~solid]
    return {
        "case": case,
        "wind_deg": wind_deg,
        "evidence_type": "newly_run",
        "dx_m": DX,
        "z_index": z_index,
        "z_height_m_approx": z_index * DX,
        "open_cells": int((~solid).sum()),
        "solid_cells": int(solid.sum()),
        "solid_ratio": float(solid.mean()),
        "vr_mean": float(values.mean()),
        "vr_p50": float(np.percentile(values, 50)),
        "vr_p75": float(np.percentile(values, 75)),
        "vr_p90": float(np.percentile(values, 90)),
        "vr_p95": float(np.percentile(values, 95)),
        "vr_max": float(values.max()),
        "stagnation_ratio_vr_lt_0p2": float((values < 0.2).mean()),
        "accelerated_ratio_vr_gt_1p2": float((values > 1.2).mean()),
    }


def main():
    rows = []
    audit_maps = []
    equal_stack = []
    extent = None
    solid_ref = None

    for deg in DIRECTIONS:
        label = f"district_prism_wd{deg:03d}_coarse6m_10k"
        meta, u = read_vtk(OUT_DIR / f"matrix_{label}_u_finalu-{STEP}.vtk")
        _, flags = read_vtk(OUT_DIR / f"matrix_{label}_flags_finalflags-{STEP}.vtk")
        if extent is None:
            extent = extent_xy(meta)
            solid_ref = (flags[Z_AUDIT] & 1) > 0
        speed = np.linalg.norm(u, axis=3)
        vr = speed / U_REF
        for z in Z_METRIC:
            rows.append(metrics(label, deg, vr, flags, z))
        solid = (flags[Z_AUDIT] & 1) > 0
        audit_maps.append((deg, np.ma.masked_where(solid, vr[Z_AUDIT]), solid))
        equal_stack.append(np.where(solid, np.nan, vr[Z_AUDIT]))

    for z in Z_METRIC:
        layer_rows = [r for r in rows if int(r["z_index"]) == z]
        summary = {
            "case": f"district_prism_equal_weighted_8dir_coarse6m_10k_z{z}",
            "wind_deg": "equal_weighted",
            "evidence_type": "newly_run",
            "dx_m": DX,
            "z_index": z,
            "z_height_m_approx": z * DX,
            "open_cells": layer_rows[0]["open_cells"],
            "solid_cells": layer_rows[0]["solid_cells"],
            "solid_ratio": layer_rows[0]["solid_ratio"],
        }
        for key in ["vr_mean", "vr_p50", "vr_p75", "vr_p90", "vr_p95", "vr_max", "stagnation_ratio_vr_lt_0p2", "accelerated_ratio_vr_gt_1p2"]:
            summary[key] = float(np.mean([float(r[key]) for r in layer_rows]))
        rows.append(summary)

    csv_path = CASE_FIG_DIR / "fluidx3d_district_prism_8dir_coarse6m_10k_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(2, 4, figsize=(17, 8.5), dpi=170, constrained_layout=True)
    last_im = None
    for ax, (deg, masked_vr, solid) in zip(axes.ravel(), audit_maps):
        last_im = ax.imshow(masked_vr, origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
        ax.contour(solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.14)
        ax.set_title(f"WD{deg:03d}")
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    cbar = fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.86)
    cbar.set_label("|U| / Uref")
    fig.suptitle("FluidX3D TUM2TWIN district prism 8-direction coarse audit, z approx 12 m, dx=6 m, 10000 steps")
    panel_path = CASE_FIG_DIR / "fluidx3d_district_prism_8dir_coarse6m_10k_vr_panel_z12m.png"
    fig.savefig(panel_path)
    plt.close(fig)

    mean_map = np.nanmean(np.stack(equal_stack), axis=0)
    fig, ax = plt.subplots(figsize=(9, 8), dpi=180, constrained_layout=True)
    im = ax.imshow(np.ma.masked_invalid(mean_map), origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
    ax.contour(solid_ref.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.16)
    ax.set_title("District prism equal-weighted 8-direction VR mean, z approx 12 m")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    fig.colorbar(im, ax=ax, label="mean |U| / Uref")
    mean_path = CASE_FIG_DIR / "fluidx3d_district_prism_8dir_coarse6m_10k_equal_weighted_vr_z12m.png"
    fig.savefig(mean_path)
    plt.close(fig)

    copied = []
    for path in [csv_path, panel_path, mean_path]:
        target = PROJECT_FIG_DIR / path.name
        shutil.copyfile(path, target)
        copied.append(str(target))
    print("\n".join(copied))


if __name__ == "__main__":
    main()
