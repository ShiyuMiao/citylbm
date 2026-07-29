from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage


ROOT = Path.cwd()
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT = CASE / "output"
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
FIG.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)
PAPER.mkdir(parents=True, exist_ok=True)

WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
DX = 2.0
U_REF = 5.0
Z_INDEX_PED = 1
MODEL_HEIGHT_M = Z_INDEX_PED * DX
EDGE_BUFFER_M = 20.0
NEAR_BUILDING_RING_M = 20.0
ANALYSIS_ZONES = [
    ("near_facade_0_20m", 0.0, 20.0),
    ("local_context_20_50m", 20.0, 50.0),
]
ENCLOSURE_RADIUS_M = 50.0
LOCAL_DENSITY_RADIUS_M = 30.0
MIN_COMPONENT_CELLS = 8


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
    return arr, {
        "dims_xyz": dims,
        "origin": origin,
        "spacing": spacing,
        "array_name": name,
        "vtk_type": vtk_type,
        "n_components": ncomp,
    }


def summarize(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {
            "mean_vr": math.nan,
            "p75_vr": math.nan,
            "p90_vr": math.nan,
            "p95_vr": math.nan,
            "max_vr": math.nan,
            "stagnation_ratio_vr_lt_0p2": math.nan,
            "acceleration_ratio_vr_gt_0p6": math.nan,
        }
    return {
        "mean_vr": float(values.mean()),
        "p75_vr": float(np.percentile(values, 75)),
        "p90_vr": float(np.percentile(values, 90)),
        "p95_vr": float(np.percentile(values, 95)),
        "max_vr": float(values.max()),
        "stagnation_ratio_vr_lt_0p2": float((values < 0.2).mean()),
        "acceleration_ratio_vr_gt_0p6": float((values > 0.6).mean()),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def component_perimeter_cells(mask: np.ndarray) -> int:
    exposed = np.zeros_like(mask, dtype=bool)
    for shift in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nb = np.roll(mask, shift=shift, axis=(0, 1))
        if shift[0] == -1:
            nb[-1, :] = False
        elif shift[0] == 1:
            nb[0, :] = False
        elif shift[1] == -1:
            nb[:, -1] = False
        elif shift[1] == 1:
            nb[:, 0] = False
        exposed |= mask & ~nb
    return int(exposed.sum())


def sector_enclosure(label_mask: np.ndarray, solid_mask: np.ndarray, cy: float, cx: float) -> float:
    radius_cells = ENCLOSURE_RADIUS_M / DX
    yy, xx = np.indices(solid_mask.shape)
    dy = yy - cy
    dx = xx - cx
    rr = np.sqrt(dx * dx + dy * dy)
    around = solid_mask & ~label_mask & (rr > 0) & (rr <= radius_cells)
    if not around.any():
        return 0.0
    angles = (np.degrees(np.arctan2(dy[around], dx[around])) + 360.0) % 360.0
    sectors = np.floor(angles / 45.0).astype(int)
    return float(np.unique(sectors).size / 8.0)


def local_built_fraction(solid_mask: np.ndarray, cy: float, cx: float) -> float:
    radius_cells = LOCAL_DENSITY_RADIUS_M / DX
    yy, xx = np.indices(solid_mask.shape)
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    area = rr <= radius_cells
    return float(solid_mask[area].mean())


def classify_enclosure(sector_ratio: float, built_fraction: float) -> str:
    if sector_ratio >= 0.625 or built_fraction >= 0.30:
        return "high_enclosure"
    if sector_ratio >= 0.375 or built_fraction >= 0.18:
        return "medium_enclosure"
    return "low_enclosure"


def classify_lcz_like(mean_height: float, footprint_area: float, enclosure: str, built_fraction: float) -> str:
    compact = enclosure == "high_enclosure" or built_fraction >= 0.25
    open_form = enclosure == "low_enclosure" and built_fraction < 0.18
    if mean_height >= 25.0:
        return "LCZ1_compact_highrise_like" if compact else "LCZ4_open_highrise_like"
    if mean_height >= 10.0:
        return "LCZ2_compact_midrise_like" if compact else "LCZ5_open_midrise_like"
    if footprint_area >= 1200.0 and open_form:
        return "LCZ8_large_lowrise_like"
    return "LCZ3_compact_lowrise_like" if compact else "LCZ6_open_lowrise_like"


def relative_enclosure_class(score: float, q33: float, q66: float) -> str:
    if score <= q33:
        return "low_enclosure"
    if score <= q66:
        return "medium_enclosure"
    return "high_enclosure"


def weighted_group_stats(rows: list[dict[str, object]], group_keys: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    out = []
    for keys, g in df.groupby(group_keys, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        cells = g["sample_open_cells"].astype(float).to_numpy()
        cells = np.where(np.isfinite(cells), cells, 0.0)
        total = cells.sum()
        record = dict(zip(group_keys, keys))
        record["component_count"] = int(g["component_id"].nunique())
        record["sample_open_cells"] = int(total)
        for col in ["mean_vr", "p95_vr", "stagnation_ratio_vr_lt_0p2", "acceleration_ratio_vr_gt_0p6"]:
            vals = g[col].astype(float).to_numpy()
            valid = np.isfinite(vals) & (cells > 0)
            record[col] = float(np.average(vals[valid], weights=cells[valid])) if valid.any() else math.nan
        out.append(record)
    return pd.DataFrame(out)


def main() -> None:
    flags, meta = read_structured_vtk_binary(
        OUT / "matrix_core_prism_avg_wd000_dx2m_spin6k_s3_flags_sample_2flags-000012000.vtk"
    )
    solid_2d = flags[Z_INDEX_PED] == 1
    open_2d = flags[Z_INDEX_PED] == 0
    labels, n_labels = ndimage.label(solid_2d, structure=np.ones((3, 3), dtype=int))
    solid_positions = np.argwhere(solid_2d)
    global_ymin, global_xmin = solid_positions.min(axis=0)
    global_ymax, global_xmax = solid_positions.max(axis=0)
    edge_buffer_cells = int(round(EDGE_BUFFER_M / DX))

    height_index = np.zeros_like(solid_2d, dtype=np.int16)
    for z in range(1, flags.shape[0]):
        height_index[flags[z] == 1] = z
    height_m = height_index.astype(float) * DX

    component_rows: list[dict[str, object]] = []
    retained_ids: list[int] = []
    label_to_class: dict[int, str] = {}
    label_to_lcz: dict[int, str] = {}

    for comp_id in range(1, n_labels + 1):
        comp = labels == comp_id
        cells = int(comp.sum())
        if cells < MIN_COMPONENT_CELLS:
            status = "excluded_small_fragment"
        else:
            yy, xx = np.where(comp)
            ymin, ymax = int(yy.min()), int(yy.max())
            xmin, xmax = int(xx.min()), int(xx.max())
            edge = (
                xmin <= global_xmin + edge_buffer_cells
                or xmax >= global_xmax - edge_buffer_cells
                or ymin <= global_ymin + edge_buffer_cells
                or ymax >= global_ymax - edge_buffer_cells
            )
            status = "excluded_edge_incomplete" if edge else "retained_central"

        yy, xx = np.where(comp)
        cy, cx = float(yy.mean()), float(xx.mean())
        footprint_area = cells * DX * DX
        perimeter_m = component_perimeter_cells(comp) * DX
        compactness = float((perimeter_m * perimeter_m) / max(footprint_area, 1.0))
        heights = height_m[comp & (height_m > 0)]
        mean_height = float(heights.mean()) if heights.size else 0.0
        max_height = float(heights.max()) if heights.size else 0.0
        built_fraction = local_built_fraction(solid_2d, cy, cx)
        sector_ratio = sector_enclosure(comp, solid_2d, cy, cx)
        enclosure_score = 0.70 * built_fraction + 0.30 * sector_ratio
        enclosure = classify_enclosure(sector_ratio, built_fraction)
        lcz_like = classify_lcz_like(mean_height, footprint_area, enclosure, built_fraction)
        label_to_class[comp_id] = enclosure
        label_to_lcz[comp_id] = lcz_like
        if status == "retained_central":
            retained_ids.append(comp_id)

        component_rows.append(
            {
                "component_id": comp_id,
                "evidence_type": "newly_run",
                "status": status,
                "footprint_cells": cells,
                "footprint_area_m2": footprint_area,
                "perimeter_m": perimeter_m,
                "compactness_p2_over_a": compactness,
                "mean_height_m": mean_height,
                "max_height_m": max_height,
                "centroid_x_index": cx,
                "centroid_y_index": cy,
                "bbox_xmin_index": int(xx.min()),
                "bbox_xmax_index": int(xx.max()),
                "bbox_ymin_index": int(yy.min()),
                "bbox_ymax_index": int(yy.max()),
                "local_built_fraction_r30m": built_fraction,
                "sector_enclosure_ratio_r50m": sector_ratio,
                "relative_enclosure_score": enclosure_score,
                "enclosure_class": enclosure,
                "lcz_like_class": lcz_like,
                "edge_filter_buffer_m": EDGE_BUFFER_M,
            }
        )

    retained_scores = np.array(
        [r["relative_enclosure_score"] for r in component_rows if r["status"] == "retained_central"],
        dtype=float,
    )
    q33, q66 = np.percentile(retained_scores, [33.333, 66.667]) if retained_scores.size else (math.nan, math.nan)
    for row in component_rows:
        if row["status"] != "retained_central":
            continue
        row["enclosure_class_absolute_check"] = row["enclosure_class"]
        row["relative_enclosure_q33"] = q33
        row["relative_enclosure_q66"] = q66
        row["enclosure_class"] = relative_enclosure_class(row["relative_enclosure_score"], q33, q66)
        row["lcz_like_class"] = classify_lcz_like(
            row["mean_height_m"],
            row["footprint_area_m2"],
            row["enclosure_class"],
            row["local_built_fraction_r30m"],
        )

    response_rows: list[dict[str, object]] = []
    component_masks = {cid: labels == cid for cid in retained_ids}
    component_distance = {
        cid: ndimage.distance_transform_edt(~mask) * DX for cid, mask in component_masks.items()
    }

    for wind_deg in WIND_DIRS:
        prefix = f"matrix_core_prism_avg_wd{wind_deg:03d}_dx2m_spin6k_s3"
        velocity, _ = read_structured_vtk_binary(OUT / f"{prefix}_u_sample_2u-000012000.vtk")
        wind_flags, _ = read_structured_vtk_binary(OUT / f"{prefix}_flags_sample_2flags-000012000.vtk")
        vr = np.linalg.norm(velocity[Z_INDEX_PED], axis=-1) / U_REF
        wind_open = wind_flags[Z_INDEX_PED] == 0

        for cid in retained_ids:
            comp = component_masks[cid]
            dist = component_distance[cid]
            comp_row = next(r for r in component_rows if r["component_id"] == cid)
            for zone_name, dmin, dmax in ANALYSIS_ZONES:
                zone_open = wind_open & (dist > dmin) & (dist <= dmax)
                values = vr[zone_open]
                row = {
                    "component_id": cid,
                    "evidence_type": "newly_run",
                    "wind_deg": wind_deg,
                    "model_height_m": MODEL_HEIGHT_M,
                    "analysis_zone": zone_name,
                    "distance_min_m": dmin,
                    "distance_max_m": dmax,
                    "sample_open_cells": int(zone_open.sum()),
                    "enclosure_class": comp_row["enclosure_class"],
                    "lcz_like_class": comp_row["lcz_like_class"],
                    "footprint_area_m2": comp_row["footprint_area_m2"],
                    "mean_height_m": comp_row["mean_height_m"],
                    "sector_enclosure_ratio_r50m": comp_row["sector_enclosure_ratio_r50m"],
                    "local_built_fraction_r30m": comp_row["local_built_fraction_r30m"],
                }
                row.update(summarize(values))
                response_rows.append(row)

    write_csv(FIG / "morphology_lcz_component_manifest.csv", component_rows)
    write_csv(FIG / "morphology_lcz_wind_response_by_component.csv", response_rows)

    by_enclosure_wind = weighted_group_stats(response_rows, ["analysis_zone", "enclosure_class", "wind_deg"])
    by_lcz_wind = weighted_group_stats(response_rows, ["analysis_zone", "lcz_like_class", "wind_deg"])
    by_enclosure_lcz = weighted_group_stats(response_rows, ["analysis_zone", "enclosure_class", "lcz_like_class"])
    by_enclosure_wind.to_csv(FIG / "morphology_wind_response_by_enclosure_and_wind.csv", index=False, encoding="utf-8-sig")
    by_lcz_wind.to_csv(FIG / "morphology_wind_response_by_lcz_and_wind.csv", index=False, encoding="utf-8-sig")
    by_enclosure_lcz.to_csv(FIG / "morphology_wind_response_by_enclosure_lcz_summary.csv", index=False, encoding="utf-8-sig")

    # Classification map.
    class_order = [
        "excluded_edge_incomplete",
        "excluded_small_fragment",
        "low_enclosure",
        "medium_enclosure",
        "high_enclosure",
    ]
    colors = {
        "excluded_edge_incomplete": "#d0d0d0",
        "excluded_small_fragment": "#f0f0f0",
        "low_enclosure": "#4daf4a",
        "medium_enclosure": "#377eb8",
        "high_enclosure": "#e41a1c",
    }
    rgba = np.zeros((*solid_2d.shape, 4), dtype=float)
    status_by_id = {r["component_id"]: r["status"] for r in component_rows}
    for cid in range(1, n_labels + 1):
        row = next(r for r in component_rows if r["component_id"] == cid)
        key = row["status"] if row["status"] != "retained_central" else row["enclosure_class"]
        hex_color = colors[key]
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
        rgba[labels == cid, :3] = rgb
        rgba[labels == cid, 3] = 1.0

    fig, ax = plt.subplots(figsize=(8, 9), constrained_layout=True)
    ax.imshow(rgba, origin="lower")
    ax.set_title("Central morphology classification after edge-building removal")
    ax.set_xticks([])
    ax.set_yticks([])
    handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=colors[k], label=k, markersize=10)
        for k in class_order
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True, fontsize=8)
    fig.savefig(FIG / "morphology_lcz_central_building_classification_map.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.0), constrained_layout=True)
    for zone, ax in zip(["near_facade_0_20m", "local_context_20_50m"], axes):
        zone_df = by_enclosure_wind[by_enclosure_wind["analysis_zone"] == zone]
        for enc, g in zone_df.groupby("enclosure_class"):
            axes_idx = ax
            axes_idx.plot(g["wind_deg"], g["mean_vr"], marker="o", label=enc)
        ax.set_title(zone.replace("_", " "))
        ax.set_xlabel("Wind direction (deg)")
        ax.set_ylabel("mean VR")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Morphology-classified wind response under 8 incoming wind directions", fontsize=13)
    fig.savefig(FIG / "morphology_lcz_wind_response_summary.png", dpi=220)
    plt.close(fig)

    context_summary = by_enclosure_lcz[by_enclosure_lcz["analysis_zone"] == "local_context_20_50m"].sort_values(
        ["enclosure_class", "lcz_like_class"]
    )
    fig, ax = plt.subplots(figsize=(12, 4.8), constrained_layout=True)
    x = np.arange(len(context_summary))
    ax.bar(x - 0.2, context_summary["mean_vr"], width=0.4, label="mean VR", color="#4daf4a")
    ax.bar(x + 0.2, context_summary["stagnation_ratio_vr_lt_0p2"], width=0.4, label="VR<0.2 ratio", color="#377eb8")
    labels_txt = [
        f"{r.enclosure_class}\n{r.lcz_like_class.replace('_like','')}" for r in context_summary.itertuples()
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels_txt, rotation=35, ha="right", fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_title("Local context wind response, 20-50 m from classified buildings")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(FIG / "morphology_lcz_context_zone_response.png", dpi=220)
    plt.close(fig)

    counts = pd.DataFrame(component_rows).groupby(["status", "enclosure_class", "lcz_like_class"], dropna=False).size().reset_index(name="component_count")
    retained = pd.DataFrame(component_rows)
    retained = retained[retained["status"] == "retained_central"]

    md = []
    md.append("# Morphology and LCZ-like Wind-Response Classification\n\n")
    md.append("evidence_type: newly_run + preexisting_artifact\n\n")
    md.append("## Method\n\n")
    md.append("- Edge-removal rule: components in the z~2 m building/solid mask are first labelled; components within 20 m of the outer solid-envelope boundary are marked `excluded_edge_incomplete` and removed from morphology-response statistics.\n")
    md.append("- Enclosure rule: retained central components are scored by local built fraction within 30 m and 8-sector surrounding-building occupancy within 50 m; low/medium/high enclosure classes are internal tertiles of this score after edge removal.\n")
    md.append("- LCZ rule: classes are LCZ-like morphology labels inferred from height, compactness/enclosure and footprint size. They are not official WUDAPT LCZ map labels.\n")
    md.append("- Wind-response rule: for each retained component and each of eight incoming wind directions, VR is sampled in two open-cell zones: 0-20 m facade-adjacent band and 20-50 m local-context band.\n\n")
    md.append("## Data\n\n")
    md.append(f"- VTK directory: `{OUT}`\n")
    md.append(f"- Grid metadata: `{meta}`\n")
    md.append(f"- Pedestrian layer used for morphology response: z~{MODEL_HEIGHT_M:.1f} m / index {Z_INDEX_PED}\n")
    md.append(f"- Total labelled solid components: {n_labels}\n")
    md.append(f"- Retained central components: {len(retained_ids)}\n\n")
    md.append("## Component Counts\n\n")
    md.append(counts.to_markdown(index=False))
    md.append("\n\n## Retained Morphology-Wind Summary\n\n")
    md.append(by_enclosure_lcz.to_markdown(index=False, floatfmt=".4f"))
    md.append("\n\n## Interpretation\n\n")
    md.append("1. Removing edge-incomplete buildings prevents truncated peripheral fragments from dominating the morphology interpretation. The remaining components represent the central campus block more consistently.\n")
    md.append("2. The retained central morphology is interpreted primarily as compact/open low- to mid-rise LCZ-like campus fabric rather than an official LCZ product. This is suitable for intra-site wind interpretation but should not be reported as a city-scale LCZ map.\n")
    md.append("3. The facade-adjacent band remains extremely low-speed for almost all classes; the 20-50 m local-context band is more informative for comparing low, medium and high enclosure responses under different incoming wind directions.\n")
    md.append("4. The eight-direction grouping supports discussion of incoming-wind sensitivity, but the present results remain CFD screening evidence, not field-validated comfort compliance.\n\n")
    md.append("## Outputs\n\n")
    for name in [
        "morphology_lcz_component_manifest.csv",
        "morphology_lcz_wind_response_by_component.csv",
        "morphology_wind_response_by_enclosure_and_wind.csv",
        "morphology_wind_response_by_lcz_and_wind.csv",
        "morphology_wind_response_by_enclosure_lcz_summary.csv",
        "morphology_lcz_central_building_classification_map.png",
        "morphology_lcz_wind_response_summary.png",
        "morphology_lcz_context_zone_response.png",
    ]:
        md.append(f"- `{FIG / name}`\n")
    md.append("\n## Literature Boundary\n\n")
    md.append("- LCZ classes follow the Stewart and Oke/WUDAPT idea that urban sites can be grouped by building height, packing and surface cover at local scale. Source: https://www.wudapt.org/lcz/\n")
    md.append("- WUDAPT describes LCZs as a globally consistent morphology-relevant layer for climate, weather, environment and planning models. Source: https://www.wudapt.org/\n")
    md.append("- Because this project classifies a small campus core from CFD-ready geometry, the label used here is `LCZ-like`, not an official LCZ map.\n")
    (REP / "morphology_lcz_wind_response_analysis.md").write_text("".join(md), encoding="utf-8")

    zh = """# 按形态与 LCZ-like 类型深化的风环境结论

evidence_type: newly_run + preexisting_artifact

在进一步解释数值结果时，本研究首先从模型层面对建筑对象进行了筛选：基于 z≈2 m 的 FluidX3D flags 文件识别建筑/固体组件，并将位于外层实体包络边界 20 m 范围内的组件标记为边缘不完整建筑，不纳入形态-风场响应统计。这样处理的目的不是删除真实校园边界，而是避免由研究范围裁切造成的截断建筑影响围合度和通风指标解释。

在保留的中心建筑中，本文采用围合度与 LCZ-like 类型共同描述建筑形态。围合度由 30 m 局部建成比例和 50 m 八方向扇区遮挡共同确定，分为低、中、高围合；LCZ-like 类型则根据建筑高度、紧凑程度和足迹尺度，将组件解释为 compact/open low-rise 或 compact/open midrise 等局地气候区相似形态。需要强调的是，这里的 LCZ-like 分类是基于校园核心区 CFD-ready 几何的形态解释，不是官方 WUDAPT LCZ 图斑。

形态分组后的风场响应进一步表明，TUM 中心校园核心区的低通风并非均匀背景噪声，而与建筑围合和局部紧凑程度有关。贴近建筑 0-20 m 的开放单元在各类形态中几乎均保持极低 VR，说明建筑界面附近的风速恢复非常有限；相比之下，20-50 m 局地环境带更能体现不同围合等级和 LCZ-like 类型之间的差异。高围合或 compact LCZ-like 组件周边更容易维持低 VR，而相对低围合、open midrise/open highrise-like 组件在部分风向下出现有限恢复。这一结果使论文结论可以从“校园核心区整体低风速”推进到“不同建筑形态在不同前置风向和距离建筑的空间带中表现出可分类的通风差异”。

因此，本研究的设计启示应从单一高度或单一风向判断转向形态组合判断：对于中欧温和湿润气候下的城市型校园，优先需要关注高围合院落、连续建筑翼、弱连通通道和贴近建筑界面的长期低通风区；设计干预可围绕打开近地通风路径、优化院落与街道之间的风道连通、减少连续封闭边界和评估不同季节主导风向下的路径舒适性展开。该结论仍属于 CFD 筛查和数字孪生应用层面的证据，尚不等同于实测验证或正式风舒适合规评价。
"""
    (PAPER / "morphology_lcz_wind_response_conclusion_zh.md").write_text(zh, encoding="utf-8")


if __name__ == "__main__":
    main()
