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

LABEL = "full_lod2_wd000_coarse4m_4k"
STEP = "000004000"
U_REF = 5.0
DX = 4.0


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


def metrics_for_slice(vr, flags, z_index):
    solid = (flags[z_index] & 1) > 0
    values = vr[z_index][~solid]
    return {
        "case": LABEL,
        "wind_deg": 0,
        "evidence_type": "newly_run",
        "dx_m": DX,
        "z_index": z_index,
        "z_height_m_approx": z_index * DX,
        "open_cells": int((~solid).sum()),
        "solid_cells": int(solid.sum()),
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
    u_path = OUT_DIR / f"matrix_{LABEL}_u_finalu-{STEP}.vtk"
    f_path = OUT_DIR / f"matrix_{LABEL}_flags_finalflags-{STEP}.vtk"
    meta, u = read_vtk(u_path)
    _, flags = read_vtk(f_path)
    speed = np.linalg.norm(u, axis=3)
    vr = speed / U_REF
    extent = extent_xy(meta)

    z_indices = [1, 2, 5, 10]
    rows = [metrics_for_slice(vr, flags, z) for z in z_indices]
    csv_path = CASE_FIG_DIR / "fluidx3d_full_lod2_wd000_coarse4m_4k_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(2, 2, figsize=(13, 10), dpi=170, constrained_layout=True)
    plot_specs = [
        (2, "near-ground audit plane, z approx 8 m"),
        (5, "low-altitude plane, z approx 20 m"),
        (10, "low-altitude plane, z approx 40 m"),
    ]
    last_im = None
    for ax, (z, title) in zip(axes.ravel()[:3], plot_specs):
        solid = (flags[z] & 1) > 0
        ped = np.ma.masked_where(solid, vr[z])
        last_im = ax.imshow(ped, origin="lower", extent=extent, cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
        ax.contour(solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.25)
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

    ax = axes.ravel()[3]
    z = 2
    step = 10
    x0, x1, y0, y1 = extent
    xs = np.linspace(x0, x1, u.shape[2])
    ys = np.linspace(y0, y1, u.shape[1])
    xx, yy = np.meshgrid(xs[::step], ys[::step])
    solid = (flags[z] & 1) > 0
    background = np.ma.masked_where(solid, vr[z])
    ax.imshow(background, origin="lower", extent=extent, cmap="Greys", vmin=0.0, vmax=1.6, interpolation="nearest", alpha=0.55)
    ax.quiver(
        xx,
        yy,
        u[z, ::step, ::step, 0],
        u[z, ::step, ::step, 1],
        color="tab:red",
        angles="xy",
        scale_units="xy",
        scale=0.035,
        width=0.002,
    )
    ax.contour(solid.astype(float), levels=[0.5], origin="lower", extent=extent, colors="black", linewidths=0.25)
    ax.set_title("horizontal velocity vectors, z approx 8 m")
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")

    cbar = fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.88)
    cbar.set_label("|U| / Uref")
    fig.suptitle(
        "FluidX3D TUM2TWIN full LoD2 coarse pilot, WD000, dx=4 m, 4000 steps\n"
        "Evidence boundary: visual QA only; not grid/time converged, not pedestrian-height resolved"
    )
    panel_path = CASE_FIG_DIR / "fluidx3d_full_lod2_wd000_coarse4m_4k_vr_audit.png"
    fig.savefig(panel_path)
    plt.close(fig)

    copied = []
    for path in [csv_path, panel_path]:
        target = PROJECT_FIG_DIR / path.name
        shutil.copyfile(path, target)
        copied.append(str(target))
    print("\n".join(copied))


if __name__ == "__main__":
    main()
