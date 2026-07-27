from __future__ import annotations

import csv
import hashlib
import json
import math
import struct
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = Path(r"D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected\obj\lod3_merged_city_model\TUM_CentralCampus.obj")
OUT_CFD = ROOT / "cfd_ready"
OUT_FIGURES = ROOT / "figures"
OUT_MANIFESTS = ROOT / "manifests"
OUT_REPORTS = ROOT / "reports"

MATERIAL = "defaultMat"
RESOLUTION_M = 5.0
VERTEX_Z_THRESHOLD_M = 1.5
FACE_ZMAX_THRESHOLD_M = 3.0
MIN_COMPONENT_CELLS = 4
MIN_HEIGHT_M = 6.0

# User-provided photogrammetry/Rhino visual mesh bbox, expanded slightly for robust overlap.
CROP_SOURCE_XY = {
    "xmin": -190.0,
    "xmax": 235.0,
    "ymin": -215.0,
    "ymax": 345.0,
}


def sha256(path: Path) -> str:
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


def write_binary_stl(path: Path, tris, name: str):
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


def parse_face_indices(line: str, vertex_count: int):
    out = []
    for tok in line.split()[1:]:
        raw = int(tok.split("/")[0])
        out.append(raw - 1 if raw > 0 else vertex_count + raw)
    return out


def collect_crop_high_points():
    vertices = []
    points = []
    current_material = None
    total_faces = 0
    selected_faces = 0
    crop_faces = 0
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
                idx = parse_face_indices(line, len(vertices))
                pts = [vertices[i] for i in idx if 0 <= i < len(vertices)]
                if not pts or max(p[2] for p in pts) < FACE_ZMAX_THRESHOLD_M:
                    continue
                selected_faces += 1
                if not any(
                    CROP_SOURCE_XY["xmin"] <= p[0] <= CROP_SOURCE_XY["xmax"]
                    and CROP_SOURCE_XY["ymin"] <= p[1] <= CROP_SOURCE_XY["ymax"]
                    for p in pts
                ):
                    continue
                crop_faces += 1
                for p in pts:
                    if (
                        p[2] >= VERTEX_Z_THRESHOLD_M
                        and CROP_SOURCE_XY["xmin"] <= p[0] <= CROP_SOURCE_XY["xmax"]
                        and CROP_SOURCE_XY["ymin"] <= p[1] <= CROP_SOURCE_XY["ymax"]
                    ):
                        points.append(p)
    return np.array(points, dtype=np.float32), {
        "obj_vertices": len(vertices),
        "obj_total_faces": total_faces,
        "selected_defaultmat_faces": selected_faces,
        "crop_intersecting_faces": crop_faces,
        "selected_crop_high_points": len(points),
    }


def build_crop_mask(points):
    x0 = CROP_SOURCE_XY["xmin"]
    y0 = CROP_SOURCE_XY["ymin"]
    nx = int(math.ceil((CROP_SOURCE_XY["xmax"] - x0) / RESOLUTION_M)) + 1
    ny = int(math.ceil((CROP_SOURCE_XY["ymax"] - y0) / RESOLUTION_M)) + 1
    ix = ((points[:, 0] - x0) / RESOLUTION_M).astype(np.int32)
    iy = ((points[:, 1] - y0) / RESOLUTION_M).astype(np.int32)
    valid = (0 <= ix) & (ix < nx) & (0 <= iy) & (iy < ny)
    ix, iy, zs = ix[valid], iy[valid], points[:, 2][valid]

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

    heights = ndimage.maximum_filter(hmax, size=5).astype(np.float32)
    labels, nlab = ndimage.label(keep)
    for label in range(1, nlab + 1):
        comp = labels == label
        vals = hmax[comp & (hmax > 0)]
        fallback = float(np.percentile(vals, 75)) if vals.size else MIN_HEIGHT_M
        heights[comp & (heights <= 0)] = fallback
    heights[keep] = np.maximum(heights[keep], MIN_HEIGHT_M)
    heights[~keep] = 0.0

    return keep, heights, {
        "crop_source_xy": CROP_SOURCE_XY,
        "local_origin_source_xy": [x0, y0],
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
            add_quad(tris, (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))
            add_quad(tris, (x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1))
            for di, dj, side in [(-1, 0, "west"), (1, 0, "east"), (0, -1, "south"), (0, 1, "north")]:
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


def bbox_of(tris):
    pts = [p for tri in tris for p in tri]
    return {
        "min": [min(p[i] for p in pts) for i in range(3)],
        "max": [max(p[i] for p in pts) for i in range(3)],
    }


def write_audit_figure(path, mask, heights):
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=160, constrained_layout=True)
    axes[0].imshow(mask, origin="lower", cmap="gray_r", interpolation="nearest")
    axes[0].set_title("core photogrammetry-extent closed prism footprint")
    axes[0].set_xticks([])
    axes[0].set_yticks([])
    im = axes[1].imshow(np.ma.masked_where(~mask, heights), origin="lower", cmap="viridis", interpolation="nearest")
    axes[1].set_title("assigned semantic-prism height (m)")
    axes[1].set_xticks([])
    axes[1].set_yticks([])
    fig.colorbar(im, ax=axes[1], label="height (m)")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def estimate_grids(bbox):
    sx = bbox["max"][0] - bbox["min"][0]
    sy = bbox["max"][1] - bbox["min"][1]
    h = bbox["max"][2] - bbox["min"][2]
    rows = []
    for label, dx in [("core_dx2m", 2.0), ("core_dx1m_candidate", 1.0)]:
        nx = math.ceil((sx + 6.0 * h) / dx)
        ny = math.ceil((sy + 6.0 * h) / dx)
        nz = math.ceil((3.0 * h) / dx)
        cells = nx * ny * nz
        rows.append({
            "level": label,
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
    points, source_stats = collect_crop_high_points()
    if len(points) == 0:
        raise RuntimeError("No high points found in crop")
    mask, heights, raster_stats = build_crop_mask(points)
    tris = build_heightfield_mesh(mask, heights)
    bbox = bbox_of(tris)

    out_stl = OUT_CFD / "core_photogrammetry_extent_prism_collision_z0.stl"
    write_binary_stl(out_stl, tris, "core_photogrammetry_extent_prism_collision_z0")
    audit_png = OUT_FIGURES / "core_photogrammetry_extent_prism_collision_audit.png"
    write_audit_figure(audit_png, mask, heights)

    qa = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "purpose": "high-resolution pedestrian subdomain matching the user-provided photogrammetry visual extent, using semantic closed prism collision geometry",
        "source_obj": str(OBJ_PATH),
        "source_material": MATERIAL,
        "parameters": {
            "raster_resolution_m": RESOLUTION_M,
            "vertex_z_threshold_m": VERTEX_Z_THRESHOLD_M,
            "face_zmax_threshold_m": FACE_ZMAX_THRESHOLD_M,
            "min_component_cells": MIN_COMPONENT_CELLS,
            "min_height_m": MIN_HEIGHT_M,
            "crop_source_xy": CROP_SOURCE_XY,
        },
        **source_stats,
        **raster_stats,
        "triangles": len(tris),
        "bbox": bbox,
        "height_min_max_mean_m": [
            float(heights[mask].min()),
            float(heights[mask].max()),
            float(heights[mask].mean()),
        ],
        "grid_estimates": estimate_grids(bbox),
        "stl_path": str(out_stl),
        "stl_size_bytes": out_stl.stat().st_size,
        "stl_sha256": sha256(out_stl),
        "audit_figure": str(audit_png),
    }
    qa_path = OUT_MANIFESTS / "geometry_qa_core_photogrammetry_extent_prism.json"
    qa_path.write_text(json.dumps(qa, indent=2), encoding="utf-8")

    report = OUT_REPORTS / "core_photogrammetry_extent_prism_collision_report.md"
    report.write_text(
        "# Core Photogrammetry-Extent Prism Collision Report\n\n"
        "evidence_type: newly_run\n\n"
        "This geometry is a local high-resolution CFD collision candidate. It follows the user-provided photogrammetry/Rhino visual extent, but the collision geometry is reconstructed from semantic LoD3 OBJ high surfaces as closed heightfield prisms.\n\n"
        f"- STL: `{out_stl}`\n"
        f"- Triangles: `{len(tris)}`\n"
        f"- Bbox size: `{bbox['max'][0]-bbox['min'][0]:.1f} x {bbox['max'][1]-bbox['min'][1]:.1f} x {bbox['max'][2]-bbox['min'][2]:.1f} m`\n"
        f"- Footprint cells: `{raster_stats['footprint_cells']}`\n"
        f"- Components: `{raster_stats['component_count']}`\n"
        f"- Audit figure: `{audit_png}`\n\n"
        "This is the preferred local pedestrian-resolution geometry, while the user-provided photogrammetry STL remains a visual/reference and geometry-readiness counterexample.\n",
        encoding="utf-8",
    )
    print(out_stl)
    print(audit_png)
    print(qa_path)
    print(report)


if __name__ == "__main__":
    main()
