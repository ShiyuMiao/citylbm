from __future__ import annotations

import csv
import hashlib
import heapq
import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

import build_core_photogrammetry_extent_prism_collision as base


ROOT = Path(__file__).resolve().parents[1]
OUT_CFD = ROOT / "cfd_ready"
OUT_FIGURES = ROOT / "figures"
OUT_MANIFESTS = ROOT / "manifests"
OUT_REPORTS = ROOT / "reports"

SCENARIO_ID = "S2_network_porosity"
OUT_STL = OUT_CFD / "core_prism_s2_network_porosity_collision_z0.stl"
OUT_QA = OUT_MANIFESTS / "geometry_qa_core_prism_s2_network_porosity.json"
OUT_AUDIT = OUT_FIGURES / "core_prism_s2_network_porosity_geometry_audit.png"
OUT_REPORT = OUT_REPORTS / "s2_network_porosity_geometry_report.md"

CORRIDOR_RADIUS_CELLS = 2
PATH_SPECS = [
    {"name": "east_west_south_context", "axis": "ew", "fraction": 0.38},
    {"name": "east_west_north_context", "axis": "ew", "fraction": 0.62},
    {"name": "north_south_central_link", "axis": "ns", "fraction": 0.50},
]
BAND_HALF_FRACTION = 0.12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dijkstra_path(mask: np.ndarray, heights: np.ndarray, axis: str, fraction: float) -> list[tuple[int, int]]:
    ny, nx = mask.shape
    if axis == "ew":
        center = fraction * (ny - 1)
        band_half = max(2.0, BAND_HALF_FRACTION * ny)
        start_nodes = [(j, 0) for j in range(max(0, int(center - band_half)), min(ny - 1, int(center + band_half)) + 1)]
        is_target = lambda j, i: i == nx - 1
        coordinate_penalty = lambda j, i: ((j - center) / band_half) ** 2
    elif axis == "ns":
        center = fraction * (nx - 1)
        band_half = max(2.0, BAND_HALF_FRACTION * nx)
        start_nodes = [(0, i) for i in range(max(0, int(center - band_half)), min(nx - 1, int(center + band_half)) + 1)]
        is_target = lambda j, i: j == ny - 1
        coordinate_penalty = lambda j, i: ((i - center) / band_half) ** 2
    else:
        raise ValueError(axis)

    def step_cost(j: int, i: int) -> float:
        path_penalty = 0.05 * coordinate_penalty(j, i)
        length_penalty = 0.03
        if not mask[j, i]:
            return length_penalty + path_penalty
        height_penalty = min(1.25, float(heights[j, i]) / 32.0)
        return 1.0 + height_penalty + path_penalty

    dist = np.full((ny, nx), np.inf, dtype=np.float64)
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    heap: list[tuple[float, int, int]] = []
    for j, i in start_nodes:
        c = step_cost(j, i)
        dist[j, i] = c
        heapq.heappush(heap, (c, j, i))

    moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    end = None
    while heap:
        d, j, i = heapq.heappop(heap)
        if d != dist[j, i]:
            continue
        if is_target(j, i):
            end = (j, i)
            break
        for dj, di in moves:
            nj, ni = j + dj, i + di
            if not (0 <= nj < ny and 0 <= ni < nx):
                continue
            nd = d + step_cost(nj, ni) * (1.4142 if dj and di else 1.0)
            if nd < dist[nj, ni]:
                dist[nj, ni] = nd
                prev[(nj, ni)] = (j, i)
                heapq.heappush(heap, (nd, nj, ni))

    if end is None:
        raise RuntimeError(f"No path found for {axis} fraction {fraction}")

    path = [end]
    cur = end
    while cur in prev:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path


def cells_around_paths(mask: np.ndarray, paths: list[list[tuple[int, int]]]) -> np.ndarray:
    seed = np.zeros_like(mask, dtype=bool)
    for path in paths:
        for j, i in path:
            seed[j, i] = True
    distance = ndimage.distance_transform_edt(~seed)
    return (distance <= float(CORRIDOR_RADIUS_CELLS)) & mask


def write_audit_figure(mask, heights, remove, s2_mask, paths):
    path_layer = np.zeros_like(mask, dtype=float)
    for idx, path in enumerate(paths, start=1):
        for j, i in path:
            path_layer[j, i] = idx

    fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=170, constrained_layout=True)
    axes[0].imshow(mask, origin="lower", cmap="gray_r", interpolation="nearest")
    axes[0].imshow(np.ma.masked_where(path_layer <= 0, path_layer), origin="lower", cmap="tab10", interpolation="nearest", alpha=0.85)
    axes[0].set_title("S0 footprint + S2 network paths")
    axes[1].imshow(np.ma.masked_where(~mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[1].imshow(np.ma.masked_where(~remove, remove), origin="lower", cmap="autumn", interpolation="nearest", alpha=0.65)
    axes[1].set_title("cells removed for S2 network porosity")
    axes[2].imshow(np.ma.masked_where(~s2_mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[2].set_title("S2 collision footprint after network release")
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_AUDIT)
    plt.close(fig)


def append_or_replace_csv(path: Path, key_field: str, row: dict[str, str]) -> None:
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    rows = [r for r in rows if r.get(key_field) != row[key_field]]
    rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    points, source_stats = base.collect_crop_high_points()
    mask, heights, raster_stats = base.build_crop_mask(points)
    paths = [dijkstra_path(mask, heights, spec["axis"], spec["fraction"]) for spec in PATH_SPECS]
    remove = cells_around_paths(mask, paths)
    s2_mask = mask & ~remove
    s2_heights = heights.copy()
    s2_heights[remove] = 0.0

    s2_tris = base.build_heightfield_mesh(s2_mask, s2_heights)
    s2_bbox = base.bbox_of(s2_tris)
    base.write_binary_stl(OUT_STL, s2_tris, "core_prism_s2_network_porosity_collision_z0")
    write_audit_figure(mask, heights, remove, s2_mask, paths)

    removed_heights = heights[remove]
    qa = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenario_id": SCENARIO_ID,
        "evidence_type": "newly_run",
        "purpose": "network-scale morphology sensitivity geometry that opens multiple least-removal porosity corridors through the accepted core prism collision field",
        "baseline_geometry": "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl",
        "source_obj": str(base.OBJ_PATH),
        "selection_method": "three Dijkstra least-removal paths over the baseline 5 m heightfield: two east-west context links and one north-south central link; solid cells have height-weighted removal cost; a two-cell corridor is removed around the path union",
        "parameters": {
            "baseline_raster_resolution_m": base.RESOLUTION_M,
            "corridor_radius_cells": CORRIDOR_RADIUS_CELLS,
            "corridor_nominal_width_m": (2 * CORRIDOR_RADIUS_CELLS + 1) * base.RESOLUTION_M,
            "band_half_fraction": BAND_HALF_FRACTION,
            "path_specs": PATH_SPECS,
        },
        **source_stats,
        **raster_stats,
        "baseline_footprint_cells": int(mask.sum()),
        "removed_cells": int(remove.sum()),
        "removed_area_m2": float(remove.sum() * base.RESOLUTION_M * base.RESOLUTION_M),
        "removed_fraction_of_baseline_footprint": float(remove.sum() / max(1, mask.sum())),
        "removed_height_min_max_mean_m": [
            float(removed_heights.min()) if removed_heights.size else 0.0,
            float(removed_heights.max()) if removed_heights.size else 0.0,
            float(removed_heights.mean()) if removed_heights.size else 0.0,
        ],
        "path_lengths_cells": [len(p) for p in paths],
        "s2_footprint_cells": int(s2_mask.sum()),
        "s2_triangles": len(s2_tris),
        "s2_bbox": s2_bbox,
        "stl_path": str(OUT_STL),
        "stl_size_bytes": OUT_STL.stat().st_size,
        "stl_sha256": sha256(OUT_STL),
        "audit_figure": str(OUT_AUDIT),
        "claim_boundary": "S2 is a morphology sensitivity scenario, not a constructability-verified architectural proposal or optimized design.",
    }
    OUT_QA.write_text(json.dumps(qa, indent=2), encoding="utf-8", newline="\n")

    append_or_replace_csv(
        OUT_MANIFESTS / "design_scenario_manifest.csv",
        "scenario_id",
        {
            "scenario_id": "S2",
            "description": "network-porosity morphology sensitivity scenario",
            "geometry_change": f"removed {qa['removed_cells']} heightfield collision cells ({qa['removed_area_m2']:.1f} m2, {100.0*qa['removed_fraction_of_baseline_footprint']:.2f}% of baseline footprint) along two east-west and one north-south least-removal corridors",
            "simulation_status": "geometry_committed_not_yet_simulated",
            "evidence_type": "newly_run + blocked",
            "paper_use": "geometry-ready network-scale design sensitivity scenario; no wind improvement value until FluidX3D postprocessing is completed",
        },
    )

    OUT_REPORT.write_text(
        f"""# S2 Network-Porosity Geometry Report

evidence_type: newly_run + blocked

S2 is a stronger network-scale sensitivity scenario following the near-null S1 result. It is not a final architectural proposal. It tests whether multiple connected porosity releases are needed before the TUM Downtown campus-core flow field responds at pedestrian height.

## Geometry Protocol

- Baseline: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- S2 STL: `cfd_ready/core_prism_s2_network_porosity_collision_z0.stl`
- Selection method: three Dijkstra least-removal paths through the S0 5 m heightfield: two east-west context paths and one north-south central link.
- Corridor radius: `{CORRIDOR_RADIUS_CELLS}` cells.
- Nominal corridor width: `{qa['parameters']['corridor_nominal_width_m']:.1f} m`.
- Removed cells: `{qa['removed_cells']}`.
- Removed area: `{qa['removed_area_m2']:.1f} m2`.
- Removed fraction of baseline footprint: `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%`.
- Removed height min/max/mean: `{qa['removed_height_min_max_mean_m'][0]:.2f} / {qa['removed_height_min_max_mean_m'][1]:.2f} / {qa['removed_height_min_max_mean_m'][2]:.2f} m`.
- S2 triangles: `{len(s2_tris)}`.
- Audit figure: `figures/core_prism_s2_network_porosity_geometry_audit.png`.

## Evidence Boundary

At this stage the S2 collision geometry is committed and QA-recorded, but wind-field improvement is not yet claimed. S2 is a numerical morphology sensitivity case for testing network porosity. It does not represent constructability, ownership, heritage, cost, or formal campus planning feasibility.
""",
        encoding="utf-8",
        newline="\n",
    )

    print(OUT_STL)
    print(OUT_QA)
    print(OUT_AUDIT)
    print(OUT_REPORT)


if __name__ == "__main__":
    main()
