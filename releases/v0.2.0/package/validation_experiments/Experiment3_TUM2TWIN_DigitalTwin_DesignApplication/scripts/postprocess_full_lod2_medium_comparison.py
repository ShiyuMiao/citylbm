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

U_REF = 5.0
STEP = "000010000"
CASES = [
    {
        "label": "full_lod2_wd000_coarse4m_10k",
        "level": "coarse",
        "dx_m": 4.0,
        "z_by_height": {4: 1, 8: 2, 20: 5, 40: 10},
    },
    {
        "label": "full_lod2_wd000_medium2m_10k",
        "level": "medium",
        "dx_m": 2.0,
        "z_by_height": {4: 2, 8: 4, 20: 10, 40: 20},
    },
]


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


def metric_row(case, vr, flags, height, z_index):
    solid = (flags[z_index] & 1) > 0
    values = vr[z_index][~solid]
    return {
        "case": case["label"],
        "level": case["level"],
        "wind_deg": 0,
        "evidence_type": "newly_run",
        "dx_m": case["dx_m"],
        "height_m_approx": height,
        "z_index": z_index,
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
    loaded = []
    rows = []
    for case in CASES:
        u_path = OUT_DIR / f"matrix_{case['label']}_u_finalu-{STEP}.vtk"
        f_path = OUT_DIR / f"matrix_{case['label']}_flags_finalflags-{STEP}.vtk"
        meta, u = read_vtk(u_path)
        _, flags = read_vtk(f_path)
        speed = np.linalg.norm(u, axis=3)
        vr = speed / U_REF
        loaded.append({"case": case, "meta": meta, "vr": vr, "flags": flags, "extent": extent_xy(meta)})
        for height, z in case["z_by_height"].items():
            rows.append(metric_row(case, vr, flags, height, z))

    csv_path = CASE_FIG_DIR / "fluidx3d_full_lod2_wd000_coarse_vs_medium_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, axes = plt.subplots(2, 2, figsize=(13, 11), dpi=170, constrained_layout=True)
    views = [
        (loaded[0], 8, "coarse dx=4 m, z approx 8 m"),
        (loaded[1], 8, "medium dx=2 m, z approx 8 m"),
        (loaded[0], 20, "coarse dx=4 m, z approx 20 m"),
        (loaded[1], 20, "medium dx=2 m, z approx 20 m"),
    ]
    last_im = None
    for ax, (item, height, title) in zip(axes.ravel(), views):
        z = item["case"]["z_by_height"][height]
        solid = (item["flags"][z] & 1) > 0
        masked = np.ma.masked_where(solid, item["vr"][z])
        last_im = ax.imshow(masked, origin="lower", extent=item["extent"], cmap="turbo", vmin=0.0, vmax=1.6, interpolation="nearest")
        ax.contour(solid.astype(float), levels=[0.5], origin="lower", extent=item["extent"], colors="black", linewidths=0.22)
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
    cbar = fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.86)
    cbar.set_label("|U| / Uref")
    fig.suptitle("FluidX3D TUM2TWIN full LoD2 WD000 grid-sensitivity visual audit")
    panel_path = CASE_FIG_DIR / "fluidx3d_full_lod2_wd000_coarse_vs_medium_vr_audit.png"
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
