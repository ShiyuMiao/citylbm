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

SCENARIO_ID = "S1_ventilation_relief"
OUT_STL = OUT_CFD / "core_prism_s1_ventilation_relief_collision_z0.stl"
OUT_QA = OUT_MANIFESTS / "geometry_qa_core_prism_s1_ventilation_relief.json"
OUT_AUDIT = OUT_FIGURES / "core_prism_s1_ventilation_relief_geometry_audit.png"
OUT_REPORT = OUT_REPORTS / "s1_ventilation_relief_geometry_report.md"

CORRIDOR_RADIUS_CELLS = 2
CENTRAL_BAND_FRACTION = 0.62


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dijkstra_relief_path(mask: np.ndarray, heights: np.ndarray) -> list[tuple[int, int]]:
    ny, nx = mask.shape
    y_mid = 0.5 * (ny - 1)
    band_half = 0.5 * CENTRAL_BAND_FRACTION * ny
    y_min = max(0, int(math.floor(y_mid - band_half)))
    y_max = min(ny - 1, int(math.ceil(y_mid + band_half)))
    start_nodes = [(j, 0) for j in range(y_min, y_max + 1)]
    target_x = nx - 1

    dist = np.full((ny, nx), np.inf, dtype=np.float64)
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    heap: list[tuple[float, int, int]] = []

    def step_cost(j: int, i: int) -> float:
        central_penalty = 0.025 * ((j - y_mid) / max(1.0, band_half)) ** 2
        length_penalty = 0.03
        if not mask[j, i]:
            return length_penalty + central_penalty
        height_penalty = min(1.0, float(heights[j, i]) / 35.0)
        return 1.0 + height_penalty + central_penalty

    for j, i in start_nodes:
        c = step_cost(j, i)
        dist[j, i] = c
        heapq.heappush(heap, (c, j, i))

    end = None
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while heap:
        d, j, i = heapq.heappop(heap)
        if d != dist[j, i]:
            continue
        if i == target_x:
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
        raise RuntimeError("No relief path found")

    path = [end]
    cur = end
    while cur in prev:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path


def corridor_cells(mask: np.ndarray, path: list[tuple[int, int]], radius: int) -> np.ndarray:
    ny, nx = mask.shape
    seed = np.zeros_like(mask, dtype=bool)
    for j, i in path:
        seed[j, i] = True
    distance = ndimage.distance_transform_edt(~seed)
    corridor = distance <= float(radius)
    return corridor & mask


def write_audit_figure(mask, heights, remove, s1_mask, path):
    path_layer = np.zeros_like(mask, dtype=float)
    for j, i in path:
        path_layer[j, i] = 1.0

    fig, axes = plt.subplots(1, 3, figsize=(18, 7), dpi=170, constrained_layout=True)
    axes[0].imshow(mask, origin="lower", cmap="gray_r", interpolation="nearest")
    axes[0].contour(path_layer, levels=[0.5], origin="lower", colors="red", linewidths=1.0)
    axes[0].set_title("S0 closed-prism footprint + selected relief path")
    axes[1].imshow(np.ma.masked_where(~mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[1].imshow(np.ma.masked_where(~remove, remove), origin="lower", cmap="autumn", interpolation="nearest", alpha=0.65)
    axes[1].set_title("cells removed for S1 ventilation relief")
    axes[2].imshow(np.ma.masked_where(~s1_mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[2].set_title("S1 collision footprint after relief")
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
    path = dijkstra_relief_path(mask, heights)
    remove = corridor_cells(mask, path, CORRIDOR_RADIUS_CELLS)
    s1_mask = mask & ~remove
    s1_heights = heights.copy()
    s1_heights[remove] = 0.0

    s1_tris = base.build_heightfield_mesh(s1_mask, s1_heights)
    s1_bbox = base.bbox_of(s1_tris)
    base.write_binary_stl(OUT_STL, s1_tris, "core_prism_s1_ventilation_relief_collision_z0")
    write_audit_figure(mask, heights, remove, s1_mask, path)

    removed_heights = heights[remove]
    qa = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenario_id": SCENARIO_ID,
        "evidence_type": "newly_run",
        "purpose": "design-sensitivity geometry that opens a least-removal east-west ventilation relief corridor through the accepted core prism collision field",
        "baseline_geometry": "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl",
        "source_obj": str(base.OBJ_PATH),
        "selection_method": "Dijkstra path over the baseline 5 m heightfield; open cells have low traversal cost and solid cells have height-weighted removal cost; a two-cell corridor is removed around the selected path",
        "parameters": {
            "baseline_raster_resolution_m": base.RESOLUTION_M,
            "corridor_radius_cells": CORRIDOR_RADIUS_CELLS,
            "corridor_nominal_width_m": (2 * CORRIDOR_RADIUS_CELLS + 1) * base.RESOLUTION_M,
            "central_band_fraction": CENTRAL_BAND_FRACTION,
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
        "path_length_cells": len(path),
        "s1_footprint_cells": int(s1_mask.sum()),
        "s1_triangles": len(s1_tris),
        "s1_bbox": s1_bbox,
        "stl_path": str(OUT_STL),
        "stl_size_bytes": OUT_STL.stat().st_size,
        "stl_sha256": sha256(OUT_STL),
        "audit_figure": str(OUT_AUDIT),
        "claim_boundary": "S1 is a morphology sensitivity scenario, not a confirmed architectural proposal or constructability assessment.",
    }
    OUT_QA.write_text(json.dumps(qa, indent=2), encoding="utf-8", newline="\n")

    append_or_replace_csv(
        OUT_MANIFESTS / "design_scenario_manifest.csv",
        "scenario_id",
        {
            "scenario_id": "S1",
            "description": "ventilation-relief morphology sensitivity scenario",
            "geometry_change": f"removed {qa['removed_cells']} heightfield collision cells ({qa['removed_area_m2']:.1f} m2, {100.0*qa['removed_fraction_of_baseline_footprint']:.2f}% of baseline footprint) along a least-removal east-west corridor",
            "simulation_status": "geometry_committed_not_yet_simulated",
            "evidence_type": "newly_run + blocked",
            "paper_use": "geometry-ready design sensitivity scenario; no wind improvement value until FluidX3D postprocessing is completed",
        },
    )

    stl_rel = OUT_STL.relative_to(ROOT).as_posix()
    audit_rel = OUT_AUDIT.relative_to(ROOT).as_posix()
    OUT_REPORT.write_text(
        f"""# S1 Ventilation-Relief Geometry Report

evidence_type: newly_run + blocked

This file commits an explicit S1 geometry for the design-application layer of Experiment 3. S1 is not a final architectural proposal. It is a morphology sensitivity scenario that removes a minimal east-west relief corridor from the accepted S0 closed-prism collision field.

## Geometry Protocol

- Baseline: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- S1 STL: `{stl_rel}`
- Selection method: Dijkstra least-removal path through the S0 5 m heightfield. Open cells have low traversal cost; solid cells have height-weighted removal cost.
- Corridor radius: `{CORRIDOR_RADIUS_CELLS}` cells.
- Nominal corridor width: `{qa['parameters']['corridor_nominal_width_m']:.1f} m`.
- Removed cells: `{qa['removed_cells']}`.
- Removed area: `{qa['removed_area_m2']:.1f} m2`.
- Removed fraction of baseline footprint: `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%`.
- Removed height min/max/mean: `{qa['removed_height_min_max_mean_m'][0]:.2f} / {qa['removed_height_min_max_mean_m'][1]:.2f} / {qa['removed_height_min_max_mean_m'][2]:.2f} m`.
- S1 triangles: `{len(s1_tris)}`.
- Audit figure: `{audit_rel}`.

## Evidence Boundary

At this stage the S1 collision geometry is committed and QA-recorded, but wind-field improvement is not yet claimed. Any S1-S0 comfort, stagnation or VR improvement statement must wait until S1 is voxelized, simulated and post-processed with the same FluidX3D protocol as S0.
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
