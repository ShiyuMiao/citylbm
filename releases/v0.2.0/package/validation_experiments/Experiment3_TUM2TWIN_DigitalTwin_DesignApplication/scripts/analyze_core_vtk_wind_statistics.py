from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt


ROOT = Path.cwd()
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT = CASE / "output"
FIG = ROOT / "figures"
REP = ROOT / "reports"
FIG.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)

WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
DX = 2.0
U_REF = 5.0
MODEL_HEIGHT_LAYERS = {1: 2.0, 2: 4.0, 5: 10.0, 10: 20.0, 20: 40.0}
DISTANCE_BINS = [
    ("0-4m", 0.0, 4.0),
    ("4-10m", 4.0, 10.0),
    ("10-20m", 10.0, 20.0),
    (">20m", 20.0, np.inf),
]


def read_structured_vtk_binary(path: Path) -> tuple[np.ndarray, dict[str, object]]:
    raw = path.read_bytes()
    marker = b"LOOKUP_TABLE default\n"
    start = raw.index(marker) + len(marker)
    header = raw[:start].decode("ascii", errors="replace")

    dims = tuple(
        int(x)
        for x in re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", header).groups()
    )
    origin = tuple(
        float(x)
        for x in re.search(
            r"ORIGIN\s+([+\-\d.Ee]+)\s+([+\-\d.Ee]+)\s+([+\-\d.Ee]+)", header
        ).groups()
    )
    spacing = tuple(
        float(x)
        for x in re.search(
            r"SPACING\s+([+\-\d.Ee]+)\s+([+\-\d.Ee]+)\s+([+\-\d.Ee]+)", header
        ).groups()
    )
    scalar = re.search(r"SCALARS\s+(\S+)\s+(\S+)\s+(\d+)", header)
    name, vtk_type, ncomp = scalar.group(1), scalar.group(2), int(scalar.group(3))
    dtype = {"float": ">f4", "unsigned_char": "u1"}[vtk_type]
    count = int(np.prod(dims) * ncomp)
    arr = np.frombuffer(raw, dtype=np.dtype(dtype), count=count, offset=start)
    if ncomp == 1:
        arr = arr.reshape((dims[2], dims[1], dims[0]))
    else:
        arr = arr.reshape((dims[2], dims[1], dims[0], ncomp))
    meta = {
        "dims_xyz": dims,
        "origin": origin,
        "spacing": spacing,
        "array_name": name,
        "vtk_type": vtk_type,
        "n_components": ncomp,
    }
    return arr, meta


def pct(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q)) if values.size else float("nan")


def summarize(values: np.ndarray) -> dict[str, float]:
    return {
        "mean_vr": float(values.mean()),
        "p50_vr": pct(values, 50),
        "p75_vr": pct(values, 75),
        "p90_vr": pct(values, 90),
        "p95_vr": pct(values, 95),
        "max_vr": float(values.max()),
        "stagnation_ratio_vr_lt_0p2": float((values < 0.2).mean()),
        "acceleration_ratio_vr_gt_0p6": float((values > 0.6).mean()),
        "strong_acceleration_ratio_vr_gt_1p0": float((values > 1.0).mean()),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    direction_rows: list[dict[str, object]] = []
    vertical_rows: list[dict[str, object]] = []
    distance_rows: list[dict[str, object]] = []
    robustness_rows: list[dict[str, object]] = []

    all_ped_vr = []
    first_meta = None
    ped_open_mask_reference = None
    ped_distance_to_solid = None

    for wind_deg in WIND_DIRS:
        prefix = f"matrix_core_prism_avg_wd{wind_deg:03d}_dx2m_spin6k_s3"
        u_path = OUT / f"{prefix}_u_sample_2u-000012000.vtk"
        flag_path = OUT / f"{prefix}_flags_sample_2flags-000012000.vtk"
        velocity, meta = read_structured_vtk_binary(u_path)
        flags, _ = read_structured_vtk_binary(flag_path)
        if first_meta is None:
            first_meta = meta

        mag = np.linalg.norm(velocity, axis=-1)
        vr = mag / U_REF

        for z_index, model_height_m in MODEL_HEIGHT_LAYERS.items():
            open_mask = flags[z_index] == 0
            values = vr[z_index][open_mask]
            row = {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "wind_deg": wind_deg,
                "z_index": z_index,
                "model_height_m": model_height_m,
                "open_cells_flag0": int(open_mask.sum()),
                "solid_cells_flag1": int((flags[z_index] == 1).sum()),
                "boundary_cells_flag2": int((flags[z_index] == 2).sum()),
            }
            row.update(summarize(values))
            vertical_rows.append(row)
            if z_index == 1:
                direction_rows.append(row.copy())

        ped_open = flags[1] == 0
        ped_solid = flags[1] == 1
        ped_vr = vr[1]
        all_ped_vr.append(np.where(ped_open, ped_vr, np.nan))

        if ped_open_mask_reference is None:
            ped_open_mask_reference = ped_open
            ped_distance_to_solid = distance_transform_edt(~ped_solid) * DX

        for label, lo, hi in DISTANCE_BINS:
            bin_mask = ped_open & (ped_distance_to_solid > lo) & (ped_distance_to_solid <= hi)
            values = ped_vr[bin_mask]
            row = {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "wind_deg": wind_deg,
                "model_height_m": 2.0,
                "distance_to_building_bin": label,
                "open_cells": int(bin_mask.sum()),
            }
            row.update(summarize(values))
            distance_rows.append(row)

    stack = np.stack(all_ped_vr, axis=0)
    valid = np.isfinite(stack).all(axis=0)
    vals = stack[:, valid]
    stagnation_frequency = (vals < 0.2).mean(axis=0)
    acceleration_frequency = (vals > 0.6).mean(axis=0)
    directional_range = vals.max(axis=0) - vals.min(axis=0)
    directional_std = vals.std(axis=0)
    robustness_rows.extend(
        [
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "valid_open_cells_all_8_dirs_flag0",
                "value": int(valid.sum()),
            },
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "all_direction_stagnation_ratio_vr_lt_0p2",
                "value": float((stagnation_frequency == 1.0).mean()),
            },
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "robust_stagnation_ratio_freq_ge_6_of_8",
                "value": float((stagnation_frequency >= 0.75).mean()),
            },
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "directionally_accelerated_ratio_freq_ge_2_of_8",
                "value": float((acceleration_frequency >= 0.25).mean()),
            },
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "mean_directional_std_vr",
                "value": float(directional_std.mean()),
            },
            {
                "case": "core_prism_avg_8dir_dx2m_sample2_vtk",
                "evidence_type": "newly_run",
                "metric": "p95_directional_range_vr",
                "value": float(np.percentile(directional_range, 95)),
            },
        ]
    )

    write_csv(FIG / "paraview_vtk_core_dx2m_pedestrian_stats_by_direction.csv", direction_rows)
    write_csv(FIG / "paraview_vtk_core_dx2m_vertical_profile_stats.csv", vertical_rows)
    write_csv(FIG / "paraview_vtk_core_dx2m_building_distance_stats.csv", distance_rows)
    write_csv(FIG / "paraview_vtk_core_dx2m_robustness_stats.csv", robustness_rows)

    mean_vr_map = np.nanmean(stack, axis=0)
    stagnation_frequency_map = np.nanmean(stack < 0.2, axis=0)
    directional_std_map = np.nanstd(stack, axis=0)
    solid_mask_map = ~ped_open_mask_reference
    mean_vr_map[solid_mask_map] = np.nan
    stagnation_frequency_map[solid_mask_map] = np.nan
    directional_std_map[solid_mask_map] = np.nan

    fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    panels = [
        (mean_vr_map, "Mean VR across 8 directions", "VR", 0.0, 1.2),
        (stagnation_frequency_map, "Stagnation frequency (VR<0.2)", "frequency", 0.0, 1.0),
        (directional_std_map, "Directional std of VR", "std(VR)", 0.0, np.nanpercentile(directional_std_map, 99)),
        (np.where(ped_open_mask_reference, ped_distance_to_solid, np.nan), "Distance to nearest building cell", "m", 0.0, 40.0),
    ]
    for ax, (arr, title, label, vmin, vmax) in zip(axes.ravel(), panels):
        im = ax.imshow(arr, origin="lower", cmap="viridis", vmin=vmin, vmax=vmax)
        ax.imshow(np.where(solid_mask_map, 1.0, np.nan), origin="lower", cmap="gray", alpha=0.55)
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cbar.set_label(label)
    fig.suptitle("TUM2TWIN core VTK statistical audit at z~2 m", fontsize=14)
    fig.savefig(FIG / "paraview_vtk_core_dx2m_statistical_maps_z2m.png", dpi=220)
    plt.close(fig)

    dir_df = pd.DataFrame(direction_rows)
    vert_df = pd.DataFrame(vertical_rows)
    dist_df = pd.DataFrame(distance_rows)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)
    axes[0].plot(dir_df["wind_deg"], dir_df["mean_vr"], marker="o", label="mean")
    axes[0].plot(dir_df["wind_deg"], dir_df["p95_vr"], marker="s", label="P95")
    axes[0].set_xlabel("Wind direction (deg)")
    axes[0].set_ylabel("VR at z~2 m")
    axes[0].set_title("Directional response")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.3)

    vgrp = vert_df.groupby("model_height_m", as_index=False).agg(
        mean_vr=("mean_vr", "mean"),
        stagnation=("stagnation_ratio_vr_lt_0p2", "mean"),
    )
    axes[1].plot(vgrp["model_height_m"], vgrp["mean_vr"], marker="o", label="mean VR")
    axes[1].plot(vgrp["model_height_m"], vgrp["stagnation"], marker="s", label="VR<0.2 ratio")
    axes[1].set_xlabel("Model-relative height (m)")
    axes[1].set_title("Vertical recovery")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.3)

    dgrp = dist_df.groupby("distance_to_building_bin", as_index=False).agg(
        mean_vr=("mean_vr", "mean"),
        stagnation=("stagnation_ratio_vr_lt_0p2", "mean"),
    )
    order = [x[0] for x in DISTANCE_BINS]
    dgrp["distance_to_building_bin"] = pd.Categorical(
        dgrp["distance_to_building_bin"], categories=order, ordered=True
    )
    dgrp = dgrp.sort_values("distance_to_building_bin")
    x = np.arange(len(dgrp))
    axes[2].bar(x - 0.18, dgrp["mean_vr"], width=0.36, label="mean VR")
    axes[2].bar(x + 0.18, dgrp["stagnation"], width=0.36, label="VR<0.2 ratio")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([str(v) for v in dgrp["distance_to_building_bin"]])
    axes[2].set_xlabel("Distance to building")
    axes[2].set_title("Building-neighbour response")
    axes[2].legend(frameon=False)
    axes[2].grid(axis="y", alpha=0.3)
    fig.suptitle("Core VTK statistical summary before architectural interpretation", fontsize=14)
    fig.savefig(FIG / "paraview_vtk_core_dx2m_direction_vertical_building_stats.png", dpi=220)
    plt.close(fig)

    # Compact markdown report.
    mean_by_height = {}
    for h in sorted({r["model_height_m"] for r in vertical_rows}):
        rows = [r for r in vertical_rows if r["model_height_m"] == h]
        mean_by_height[h] = {
            "mean_vr": float(np.mean([r["mean_vr"] for r in rows])),
            "stagnation": float(np.mean([r["stagnation_ratio_vr_lt_0p2"] for r in rows])),
            "p95": float(np.mean([r["p95_vr"] for r in rows])),
        }

    md = []
    md.append("# ParaView VTK Core Wind Field Statistical Analysis\n")
    md.append("evidence_type: newly_run\n")
    md.append("## Data and Tooling\n")
    md.append(f"- ParaView/pvpython path: `F:\\citylbm_fluidx3d_workspace\\ParaView_zip\\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\\bin\\pvpython.exe`\n")
    md.append(f"- VTK source directory: `{OUT}`\n")
    md.append(f"- Wind directions: {', '.join(map(str, WIND_DIRS))} deg\n")
    md.append(f"- Grid metadata: `{first_meta}`\n")
    md.append("- Speed ratio definition: `VR = |U| / 5.0 m/s`; statistics use `flags==0` open cells only. `flags==1` is solid/building and `flags==2` is boundary.\n")
    md.append("## Core Pedestrian-Layer Robustness\n")
    for r in robustness_rows:
        md.append(f"- {r['metric']}: {r['value']}\n")
    md.append("## Direction-Level Pedestrian Statistics, z~2 m\n")
    md.append("| wind_deg | mean VR | P95 VR | max VR | VR<0.2 ratio | VR>0.6 ratio |\n")
    md.append("|---:|---:|---:|---:|---:|---:|\n")
    for r in direction_rows:
        md.append(
            f"| {r['wind_deg']} | {r['mean_vr']:.4f} | {r['p95_vr']:.4f} | {r['max_vr']:.4f} | "
            f"{r['stagnation_ratio_vr_lt_0p2']:.4f} | {r['acceleration_ratio_vr_gt_0p6']:.4f} |\n"
        )
    md.append("## Vertical Recovery\n")
    md.append("| model height | mean VR across directions | mean P95 VR | mean VR<0.2 ratio |\n")
    md.append("|---:|---:|---:|---:|\n")
    for h, row in mean_by_height.items():
        md.append(f"| {h:.1f} m | {row['mean_vr']:.4f} | {row['p95']:.4f} | {row['stagnation']:.4f} |\n")
    md.append("## Building-Related Stepwise Interpretation\n")
    md.append("1. Solid/open separation: use `flags==1` as building collision cells and exclude `flags==2` boundary cells from pedestrian statistics.\n")
    md.append("2. Near-building zone: group open cells by 2D distance to the nearest solid cell at z~2 m: 0-4 m, 4-10 m, 10-20 m, and >20 m.\n")
    md.append("3. Morphology interpretation: compare VR and stagnation ratios across distance bins to distinguish facade-adjacent shelter, channelized passages, and open-space recovery.\n")
    md.append("4. Claim boundary: these are CFD-derived aerodynamic diagnostics, not field-validated wind comfort classes.\n")
    md.append("## Outputs\n")
    for name in [
        "paraview_vtk_core_dx2m_pedestrian_stats_by_direction.csv",
        "paraview_vtk_core_dx2m_vertical_profile_stats.csv",
        "paraview_vtk_core_dx2m_building_distance_stats.csv",
        "paraview_vtk_core_dx2m_robustness_stats.csv",
        "paraview_vtk_core_dx2m_statistical_maps_z2m.png",
        "paraview_vtk_core_dx2m_direction_vertical_building_stats.png",
    ]:
        md.append(f"- `{FIG / name}`\n")
    (REP / "paraview_vtk_core_wind_statistics_and_building_analysis.md").write_text(
        "".join(md), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
