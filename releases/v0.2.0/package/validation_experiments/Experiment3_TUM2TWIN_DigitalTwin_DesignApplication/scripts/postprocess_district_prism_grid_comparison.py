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
U_REF = 5.0
STEP = "000010000"
CASES = [
    {"level": "coarse6m", "dx": 6.0, "template": "district_prism_wd{deg:03d}_coarse6m_10k", "z_by_height": {12: 2, 24: 4, 48: 8}},
    {"level": "medium4m", "dx": 4.0, "template": "district_prism_wd{deg:03d}_medium4m_10k", "z_by_height": {12: 3, 24: 6, 48: 12}},
]


def read_vtk(path: Path):
    raw = path.read_bytes()
    marker = b"LOOKUP_TABLE default\n"
    start = raw.index(marker) + len(marker)
    header = raw[:start].decode("ascii", errors="replace")
    dims = tuple(int(v) for v in re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", header).groups())
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
    return arr


def row_for(level, dx, wind_deg, height, z, vr, flags):
    solid = (flags[z] & 1) > 0
    values = vr[z][~solid]
    return {
        "level": level,
        "wind_deg": wind_deg,
        "evidence_type": "newly_run",
        "dx_m": dx,
        "height_m_approx": height,
        "z_index": z,
        "open_cells": int((~solid).sum()),
        "solid_cells": int(solid.sum()),
        "solid_ratio": float(solid.mean()),
        "vr_mean": float(values.mean()),
        "vr_p75": float(np.percentile(values, 75)),
        "vr_p90": float(np.percentile(values, 90)),
        "vr_p95": float(np.percentile(values, 95)),
        "vr_max": float(values.max()),
        "stagnation_ratio_vr_lt_0p2": float((values < 0.2).mean()),
        "accelerated_ratio_vr_gt_1p2": float((values > 1.2).mean()),
    }


def main():
    rows = []
    summary_rows = []
    for case in CASES:
        case_rows = []
        for deg in DIRECTIONS:
            label = case["template"].format(deg=deg)
            u = read_vtk(OUT_DIR / f"matrix_{label}_u_finalu-{STEP}.vtk")
            flags = read_vtk(OUT_DIR / f"matrix_{label}_flags_finalflags-{STEP}.vtk")
            vr = np.linalg.norm(u, axis=3) / U_REF
            for height, z in case["z_by_height"].items():
                case_rows.append(row_for(case["level"], case["dx"], deg, height, z, vr, flags))
        rows.extend(case_rows)
        for height in case["z_by_height"]:
            layer = [r for r in case_rows if r["height_m_approx"] == height]
            summary = {
                "level": case["level"],
                "wind_deg": "equal_weighted",
                "evidence_type": "newly_run",
                "dx_m": case["dx"],
                "height_m_approx": height,
                "z_index": case["z_by_height"][height],
                "open_cells": layer[0]["open_cells"],
                "solid_cells": layer[0]["solid_cells"],
                "solid_ratio": layer[0]["solid_ratio"],
            }
            for key in ["vr_mean", "vr_p75", "vr_p90", "vr_p95", "vr_max", "stagnation_ratio_vr_lt_0p2", "accelerated_ratio_vr_gt_1p2"]:
                summary[key] = float(np.mean([float(r[key]) for r in layer]))
            summary_rows.append(summary)
            rows.append(summary)

    csv_path = CASE_FIG_DIR / "fluidx3d_district_prism_grid_comparison_common_heights.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    heights = [12, 24, 48]
    x = np.arange(len(heights))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), dpi=170, constrained_layout=True)
    for offset, level in [(-width / 2, "coarse6m"), (width / 2, "medium4m")]:
        vals = [next(r for r in summary_rows if r["level"] == level and r["height_m_approx"] == h)["vr_mean"] for h in heights]
        axes[0].bar(x + offset, vals, width=width, label=level)
        stag = [next(r for r in summary_rows if r["level"] == level and r["height_m_approx"] == h)["stagnation_ratio_vr_lt_0p2"] for h in heights]
        axes[1].bar(x + offset, stag, width=width, label=level)
    for ax, ylabel in [(axes[0], "VR mean"), (axes[1], "stagnation ratio VR<0.2")]:
        ax.set_xticks(x)
        ax.set_xticklabels([f"{h} m" for h in heights])
        ax.set_xlabel("common comparison height")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
    fig.suptitle("District prism grid-sensitivity comparison at common heights")
    fig_path = CASE_FIG_DIR / "fluidx3d_district_prism_grid_comparison_common_heights.png"
    fig.savefig(fig_path)
    plt.close(fig)

    copied = []
    for path in [csv_path, fig_path]:
        target = PROJECT_FIG_DIR / path.name
        shutil.copyfile(path, target)
        copied.append(str(target))
    print("\n".join(copied))


if __name__ == "__main__":
    main()
