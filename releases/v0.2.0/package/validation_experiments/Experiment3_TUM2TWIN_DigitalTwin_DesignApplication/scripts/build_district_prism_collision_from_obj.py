import csv
import hashlib
import json
import math
import struct
import time
from pathlib import Path

import numpy as np
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = Path(r"D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected\obj\lod3_merged_city_model\TUM_CentralCampus.obj")
OUT_CFD = ROOT / "cfd_ready"
OUT_FIGURES = ROOT / "figures"
OUT_MANIFESTS = ROOT / "manifests"
OUT_REPORTS = ROOT / "reports"

RESOLUTION_M = 5.0
VERTEX_Z_THRESHOLD_M = 1.5
FACE_ZMAX_THRESHOLD_M = 3.0
MIN_COMPONENT_CELLS = 4
MIN_HEIGHT_M = 6.0
MATERIAL = "defaultMat"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vnorm(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n == 0.0:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def bbox_of(tris):
    pts = [p for tri in tris for p in tri]
    return {
        "min": [min(p[i] for p in pts) for i in range(3)],
        "max": [max(p[i] for p in pts) for i in range(3)],
    }


def write_binary_stl(path, tris, name):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(name[:80].encode("ascii", "ignore").ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for tri in tris:
            a, b, c = tri
            n = vnorm(vcross(vsub(b, a), vsub(c, a)))
            f.write(struct.pack("<3f", *n))
            f.write(struct.pack("<3f", *a))
            f.write(struct.pack("<3f", *b))
            f.write(struct.pack("<3f", *c))
            f.write(struct.pack("<H", 0))


def parse_face_indices(line, vertex_count):
    idx = []
    for tok in line.split()[1:]:
        first = tok.split("/")[0]
        if not first:
            continue
        raw = int(first)
        idx.append(raw - 1 if raw > 0 else vertex_count + raw)
    return idx


def collect_defaultmat_high_points():
    vertices = []
    points = []
    current_material = None
    total_faces = 0
    selected_faces = 0
    with OBJ_PATH.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                vertices.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("usemtl "):
                current_material = line.strip()[7:]
            elif line.startswith("f "):
                total_faces += 1
                if current_material != MATERIAL:
                    continue
                indices = parse_face_indices(line, len(vertices))
                pts = [vertices[i] for i in indices if 0 <= i < len(vertices)]
                if not pts or max(p[2] for p in pts) < FACE_ZMAX_THRESHOLD_M:
                    continue
                selected_faces += 1
                for p in pts:
                    if p[2] >= VERTEX_Z_THRESHOLD_M:
                        points.append(p)
    return np.array(points, dtype=np.float32), {
        "obj_vertices": len(vertices),
        "obj_total_faces": total_faces,
        "selected_defaultmat_faces": selected_faces,
        "selected_high_points": len(points),
    }


def build_mask_and_heights(points):
    xs, ys, zs = points[:, 0], points[:, 1], points[:, 2]
    x0 = float(xs.min())
    y0 = float(ys.min())
    nx = int(np.ceil((float(xs.max()) - x0) / RESOLUTION_M)) + 1
    ny = int(np.ceil((float(ys.max()) - y0) / RESOLUTION_M)) + 1
    ix = ((xs - x0) / RESOLUTION_M).astype(np.int32)
    iy = ((ys - y0) / RESOLUTION_M).astype(np.int32)
    count = np.zeros((ny, nx), dtype=np.uint16)
    hmax = np.zeros((ny, nx), dtype=np.float32)
    np.add.at(count, (iy, ix), 1)
    np.maximum.at(hmax, (iy, ix), zs)

    base = count > 0
    mask = ndimage.binary_closing(base, iterations=1)
    mask = ndimage.binary_fill_holes(mask)
    labels, nlab = ndimage.label(mask)
    sizes = np.bincount(labels.ravel())
    keep = np.zeros_like(mask, dtype=bool)
    for label, size in enumerate(sizes):
        if label != 0 and size >= MIN_COMPONENT_CELLS:
            keep |= labels == label

    height_seed = ndimage.maximum_filter(hmax, size=5)
    heights = np.where(height_seed > 0, height_seed, 0.0).astype(np.float32)
    labels, nlab = ndimage.label(keep)
    for label in range(1, nlab + 1):
        comp = labels == label
        vals = hmax[comp & (hmax > 0)]
        fallback = float(np.percentile(vals, 75)) if vals.size else MIN_HEIGHT_M
        heights[comp & (heights <= 0)] = fallback
    heights[keep] = np.maximum(heights[keep], MIN_HEIGHT_M)
    heights[~keep] = 0.0
    return keep, heights, {
        "origin_obj_xy": [x0, y0],
        "raster_resolution_m": RESOLUTION_M,
        "raster_shape_ny_nx": [int(ny), int(nx)],
        "raw_occupied_cells": int(base.sum()),
        "footprint_cells": int(keep.sum()),
        "component_count": int(nlab),
    }


def add_quad(tris, a, b, c, d):
    tris.append([a, b, c])
    tris.append([a, c, d])


def build_heightfield_mesh(mask, heights):
    ny, nx = mask.shape
    tris = []
    for j in range(ny):
        for i in range(nx):
            if not mask[j, i]:
                continue
            h = float(heights[j, i])
            x0, x1 = i * RESOLUTION_M, (i + 1) * RESOLUTION_M
            y0, y1 = j * RESOLUTION_M, (j + 1) * RESOLUTION_M
            z0, z1 = 0.0, h
            # Bottom and top.
            add_quad(tris, (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))
            add_quad(tris, (x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1))

            neighbors = [
                (-1, 0, "west"),
                (1, 0, "east"),
                (0, -1, "south"),
                (0, 1, "north"),
            ]
            for di, dj, side in neighbors:
                ni, nj = i + di, j + dj
                nh = float(heights[nj, ni]) if (0 <= ni < nx and 0 <= nj < ny and mask[nj, ni]) else 0.0
                if nh >= h:
                    continue
                zl, zh = nh, h
                if side == "west":
                    add_quad(tris, (x0, y0, zl), (x0, y1, zl), (x0, y1, zh), (x0, y0, zh))
                elif side == "east":
                    add_quad(tris, (x1, y1, zl), (x1, y0, zl), (x1, y0, zh), (x1, y1, zh))
                elif side == "south":
                    add_quad(tris, (x1, y0, zl), (x0, y0, zl), (x0, y0, zh), (x1, y0, zh))
                elif side == "north":
                    add_quad(tris, (x0, y1, zl), (x1, y1, zl), (x1, y1, zh), (x0, y1, zh))
    return tris


def write_audit_figure(path, mask, heights):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(15, 7), dpi=160, constrained_layout=True)
    axes[0].imshow(mask, origin="lower", cmap="gray_r", interpolation="nearest")
    axes[0].set_title("district prism footprint mask")
    axes[0].set_xticks([])
    axes[0].set_yticks([])
    im = axes[1].imshow(np.ma.masked_where(~mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[1].set_title("assigned prism height (m)")
    axes[1].set_xticks([])
    axes[1].set_yticks([])
    fig.colorbar(im, ax=axes[1], label="height (m)")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def estimate_grid(bbox):
    sx = bbox["max"][0] - bbox["min"][0]
    sy = bbox["max"][1] - bbox["min"][1]
    h = bbox["max"][2] - bbox["min"][2]
    rows = []
    for level, dx in [("district_prism_coarse", 6.0), ("district_prism_medium", 4.0), ("district_prism_fine_candidate", 2.0)]:
        nx = math.ceil((sx + 12.0 * h) / dx)
        ny = math.ceil((sy + 12.0 * h) / dx)
        nz = math.ceil((5.0 * h) / dx)
        cells = nx * ny * nz
        rows.append({
            "level": level,
            "dx_m": dx,
            "Nx": nx,
            "Ny": ny,
            "Nz": nz,
            "cells": cells,
            "rough_vram_GB_120B_cell": round(cells * 120.0 / 1024**3, 2),
            "rough_vram_GB_200B_cell": round(cells * 200.0 / 1024**3, 2),
        })
    return rows


def main():
    points, source_stats = collect_defaultmat_high_points()
    mask, heights, raster_stats = build_mask_and_heights(points)
    tris = build_heightfield_mesh(mask, heights)
    bbox = bbox_of(tris)
    qa = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_obj": str(OBJ_PATH),
        "source_material": MATERIAL,
        "face_zmax_threshold_m": FACE_ZMAX_THRESHOLD_M,
        "vertex_z_threshold_m": VERTEX_Z_THRESHOLD_M,
        "min_component_cells": MIN_COMPONENT_CELLS,
        "min_height_m": MIN_HEIGHT_M,
        "triangles": len(tris),
        "bbox": bbox,
        "height_min_max_mean_m": [float(heights[mask].min()), float(heights[mask].max()), float(heights[mask].mean())],
        **source_stats,
        **raster_stats,
        "grid_estimates": estimate_grid(bbox),
    }

    stl_path = OUT_CFD / "district_prism_collision_z0.stl"
    qa_path = OUT_MANIFESTS / "geometry_qa_district_prism.json"
    fig_path = OUT_FIGURES / "district_prism_collision_audit.png"
    grid_path = OUT_CFD / "FluidX3D_case_template" / "grid_memory_estimate_district_prism.csv"
    report_path = OUT_REPORTS / "district_prism_collision_report.md"

    write_binary_stl(stl_path, tris, "tum2twin_district_prism_collision")
    qa["stl_path"] = str(stl_path)
    qa["stl_size_bytes"] = stl_path.stat().st_size
    qa["stl_sha256"] = sha256(stl_path)
    write_audit_figure(fig_path, mask, heights)
    qa["audit_figure"] = str(fig_path)
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    with grid_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(qa["grid_estimates"][0].keys()))
        writer.writeheader()
        writer.writerows(qa["grid_estimates"])

    report = f"""# District Prism Collision Report

evidence_type: newly_run

## Purpose

The direct district LoD3 OBJ surface was too sheet-like for robust FluidX3D collision use. This report records a corrected whole-block collision candidate reconstructed as closed footprint/height prisms from the official merged LoD3 OBJ high surfaces.

## Outputs

- Collision STL: `{stl_path}`
- QA JSON: `{qa_path}`
- Audit figure: `{fig_path}`
- Grid estimate: `{grid_path}`

## QA Summary

| Item | Value |
|---|---:|
| Selected high points | {qa['selected_high_points']} |
| Raw occupied raster cells | {qa['raw_occupied_cells']} |
| Final footprint cells | {qa['footprint_cells']} |
| Components | {qa['component_count']} |
| Exported triangles | {qa['triangles']} |
| Height min / max / mean (m) | {qa['height_min_max_mean_m'][0]:.2f} / {qa['height_min_max_mean_m'][1]:.2f} / {qa['height_min_max_mean_m'][2]:.2f} |
| BBox X / Y / Z (m) | {bbox['max'][0]-bbox['min'][0]:.1f} / {bbox['max'][1]-bbox['min'][1]:.1f} / {bbox['max'][2]-bbox['min'][2]:.1f} |

## Evidence Boundary

This is a whole-block simplified collision model intended for LBM pilot simulation. It is more CFD-ready than the raw merged OBJ because it is closed and avoids sheet-like facade triangulation, but it is a generalized prism model and should be described as an OBJ-derived block reconstruction rather than exact LoD3 facade geometry.
"""
    report_path.write_text(report, encoding="utf-8")

    manifest = OUT_MANIFESTS / "geometry_manifest.csv"
    rows = []
    if manifest.exists():
        with manifest.open("r", newline="", encoding="utf-8-sig") as f:
            rows = [row for row in csv.DictReader(f) if "district_prism_collision" not in row.get("file", "")]
    rows.append({
        "file": str(stl_path),
        "role": "whole-block prism CFD collision boundary",
        "source": "TUM_CentralCampus.obj defaultMat high-surface raster",
        "size_bytes": stl_path.stat().st_size,
        "sha256": qa["stl_sha256"],
        "evidence_type": "newly_run",
    })
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "role", "source", "size_bytes", "sha256", "evidence_type"])
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({
        "stl": str(stl_path),
        "qa": str(qa_path),
        "figure": str(fig_path),
        "triangles": len(tris),
        "bbox": bbox,
        "grid_estimates": qa["grid_estimates"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
