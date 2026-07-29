import csv
import hashlib
import json
import math
import struct
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOD2_DIR = Path(r"D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_full_lod2\citygml\lod2-building-datasets")
OUT_CFD = ROOT / "cfd_ready"
OUT_MANIFESTS = ROOT / "manifests"
OUT_FIGURES = ROOT / "figures"
OUT_REPORTS = ROOT / "reports"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
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


def triangulate_ring(points):
    if len(points) >= 2 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 3:
        return []
    p0 = points[0]
    return [(p0, points[i], points[i + 1]) for i in range(1, len(points) - 1)]


def parse_poslist(text):
    values = [float(x) for x in text.split()]
    if len(values) % 3 != 0:
        return []
    return [(values[i], values[i + 1], values[i + 2]) for i in range(0, len(values), 3)]


def parse_citygml(paths):
    rings = []
    envelopes = []
    building_ids = set()
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for elem in root.iter():
            tag = elem.tag.split("}", 1)[-1]
            if tag == "Envelope":
                low = None
                high = None
                for child in elem:
                    child_tag = child.tag.split("}", 1)[-1]
                    if child_tag == "lowerCorner":
                        low = child.text
                    elif child_tag == "upperCorner":
                        high = child.text
                if low and high:
                    envelopes.append((tuple(map(float, low.split())), tuple(map(float, high.split()))))
            elif tag == "Building":
                gid = elem.attrib.get("{http://www.opengis.net/gml}id") or elem.attrib.get("id")
                if gid:
                    building_ids.add(gid)
            elif tag == "posList" and elem.text:
                ring = parse_poslist(elem.text)
                if ring:
                    rings.append({"file": path.name, "ring": ring})
    return rings, envelopes, building_ids


def offset_triangles(tris, origin):
    ox, oy, oz = origin
    return [[(p[0] - ox, p[1] - oy, p[2] - oz) for p in tri] for tri in tris]


def signed_volume(tris):
    vol = 0.0
    for a, b, c in tris:
        vol += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    return vol


def edge_key(a, b):
    ar = tuple(round(x, 5) for x in a)
    br = tuple(round(x, 5) for x in b)
    return tuple(sorted((ar, br)))


def mesh_qa(tris):
    edges = Counter()
    degenerate = 0
    duplicate_triangles = Counter()
    for tri in tris:
        a, b, c = tri
        n = vcross(vsub(b, a), vsub(c, a))
        if math.sqrt(sum(x * x for x in n)) < 1e-9:
            degenerate += 1
        edges[edge_key(a, b)] += 1
        edges[edge_key(b, c)] += 1
        edges[edge_key(c, a)] += 1
        duplicate_triangles[tuple(sorted(tuple(round(v, 5) for v in p) for p in tri))] += 1
    boundary = sum(1 for count in edges.values() if count == 1)
    nonmanifold = sum(1 for count in edges.values() if count > 2)
    duplicates = sum(count - 1 for count in duplicate_triangles.values() if count > 1)
    return {
        "triangles": len(tris),
        "bbox": bbox_of(tris),
        "signed_volume_m3": signed_volume(tris),
        "unique_edges": len(edges),
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "degenerate_triangles": degenerate,
        "duplicate_triangles": duplicates,
        "watertight": boundary == 0 and nonmanifold == 0 and degenerate == 0,
    }


def write_binary_stl(path, tris, name):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
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


def make_ground(bbox, margin):
    mn, mx = bbox["min"], bbox["max"]
    x0, x1 = mn[0] - margin, mx[0] + margin
    y0, y1 = mn[1] - margin, mx[1] + margin
    return [
        [(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0)],
        [(x0, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)],
    ]


def estimate_grid(bbox, dx_values):
    mn, mx = bbox["min"], bbox["max"]
    lx = mx[0] - mn[0]
    ly = mx[1] - mn[1]
    hmax = mx[2] - mn[2]
    rows = []
    # Conservative 8-direction pilot box: 5H side/upstream, 15H downstream can be
    # rotated per wind direction later; here we reserve the longest horizontal span.
    horizontal = max(lx, ly) + 20.0 * hmax
    vertical = 6.0 * hmax
    for label, dx in dx_values:
        nx = math.ceil(horizontal / dx)
        ny = math.ceil(horizontal / dx)
        nz = math.ceil(vertical / dx)
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


def write_footprint_png(path, tris, bbox):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
    except Exception as exc:
        return {"created": False, "reason": repr(exc)}

    polys = []
    colors = []
    for tri in tris:
        zmean = sum(p[2] for p in tri) / 3.0
        if zmean < 0.2:
            continue
        polys.append([(p[0], p[1]) for p in tri])
        colors.append(zmean)
    fig, ax = plt.subplots(figsize=(10, 8), dpi=180)
    coll = PolyCollection(polys, array=colors, cmap="viridis", linewidth=0.05, edgecolor=(0, 0, 0, 0.12))
    ax.add_collection(coll)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(bbox["min"][0] - 10.0, bbox["max"][0] + 10.0)
    ax.set_ylim(bbox["min"][1] - 10.0, bbox["max"][1] + 10.0)
    ax.set_title("TUM2TWIN full LoD2 collision mesh audit (height colored)")
    ax.set_xlabel("local x (m)")
    ax.set_ylabel("local y (m)")
    fig.colorbar(coll, ax=ax, label="z above local ground (m)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return {"created": True, "path": str(path)}


def main():
    paths = sorted(LOD2_DIR.glob("*.gml"))
    if not paths:
        raise SystemExit(f"No LoD2 GML files found in {LOD2_DIR}")

    rings, envelopes, building_ids = parse_citygml(paths)
    world_tris = []
    rings_by_file = Counter()
    for item in rings:
        tris = triangulate_ring(item["ring"])
        world_tris.extend(tris)
        rings_by_file[item["file"]] += 1
    if not world_tris:
        raise SystemExit("No polygon rings parsed from LoD2 files.")

    world_bbox = bbox_of(world_tris)
    origin = (world_bbox["min"][0], world_bbox["min"][1], world_bbox["min"][2])
    tris = offset_triangles(world_tris, origin)
    qa = mesh_qa(tris)
    qa["source_gml_count"] = len(paths)
    qa["source_ring_count"] = len(rings)
    qa["source_building_id_count"] = len(building_ids)
    qa["origin_world_easting_northing_z"] = list(origin)
    qa["coordinate_reference_system"] = "EPSG:25832 in source CityGML; exported STLs use local z0 meters"
    qa["source_files"] = [{"name": p.name, "size_bytes": p.stat().st_size, "rings": rings_by_file[p.name]} for p in paths]
    qa["created_at_local"] = time.strftime("%Y-%m-%d %H:%M:%S")
    qa["grid_estimates"] = estimate_grid(qa["bbox"], [("coarse_full", 4.0), ("medium_full", 2.0), ("fine_full", 1.0)])

    stl_path = OUT_CFD / "building_collision_full_lod2_z0.stl"
    ground_path = OUT_CFD / "ground_domain_full_lod2_z0.stl"
    qa_path = OUT_MANIFESTS / "geometry_qa_full_lod2.json"
    grid_path = OUT_CFD / "FluidX3D_case_template" / "grid_memory_estimate_full_lod2.csv"
    png_path = OUT_FIGURES / "full_lod2_collision_footprint_audit.png"
    report_path = OUT_REPORTS / "full_lod2_geometry_expansion_report.md"

    hmax = qa["bbox"]["max"][2] - qa["bbox"]["min"][2]
    ground = make_ground(qa["bbox"], margin=max(80.0, 5.0 * hmax))
    ground_qa = mesh_qa(ground)
    write_binary_stl(stl_path, tris, "tum2twin_full_lod2_collision_z0")
    write_binary_stl(ground_path, ground, "tum2twin_full_lod2_ground_z0")
    qa["stl_path"] = str(stl_path)
    qa["stl_size_bytes"] = stl_path.stat().st_size
    qa["stl_sha256"] = sha256(stl_path)
    qa["ground_stl_path"] = str(ground_path)
    qa["ground_qa"] = ground_qa
    qa["ground_stl_sha256"] = sha256(ground_path)
    figure_result = write_footprint_png(png_path, tris, qa["bbox"])
    qa["footprint_audit_figure"] = figure_result

    qa_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    grid_path.parent.mkdir(parents=True, exist_ok=True)
    with open(grid_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(qa["grid_estimates"][0].keys()))
        writer.writeheader()
        writer.writerows(qa["grid_estimates"])

    geom_manifest = OUT_MANIFESTS / "geometry_manifest.csv"
    existing = []
    if geom_manifest.exists():
        with open(geom_manifest, "r", newline="", encoding="utf-8-sig") as f:
            existing = list(csv.DictReader(f))
    keep = [row for row in existing if "full_lod2" not in row.get("file", "")]
    keep.extend([
        {
            "file": str(stl_path),
            "role": "expanded CFD collision boundary",
            "source": "27 LoD2 CityGML files",
            "size_bytes": stl_path.stat().st_size,
            "sha256": qa["stl_sha256"],
            "evidence_type": "newly_run",
        },
        {
            "file": str(ground_path),
            "role": "expanded ground/domain plane",
            "source": "derived from full LoD2 bbox",
            "size_bytes": ground_path.stat().st_size,
            "sha256": qa["ground_stl_sha256"],
            "evidence_type": "newly_run",
        },
    ])
    with open(geom_manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "role", "source", "size_bytes", "sha256", "evidence_type"])
        writer.writeheader()
        writer.writerows(keep)

    report = f"""# Full LoD2 Geometry Expansion Report

evidence_type: newly_run

## Purpose

The earlier FluidX3D smoke test used a small four-building LoD2 collision mesh. This expanded geometry uses all locally downloaded TUM2TWIN LoD2 building GML files so the next experiment can move from pipeline validation toward a real-district application case.

## Outputs

- Full building collision STL: `{stl_path}`
- Full ground/domain STL: `{ground_path}`
- QA JSON: `{qa_path}`
- Grid estimate CSV: `{grid_path}`
- Footprint audit figure: `{png_path}`

## Geometry QA

| Item | Value |
|---|---:|
| Source GML files | {qa["source_gml_count"]} |
| Parsed polygon rings | {qa["source_ring_count"]} |
| CityGML building ids | {qa["source_building_id_count"]} |
| Triangles | {qa["triangles"]} |
| Watertight | {qa["watertight"]} |
| Boundary edges | {qa["boundary_edges"]} |
| Non-manifold edges | {qa["nonmanifold_edges"]} |
| Degenerate triangles | {qa["degenerate_triangles"]} |
| Duplicate triangles | {qa["duplicate_triangles"]} |
| Hmax (m) | {hmax:.3f} |

## BBox

- Local min: `{qa["bbox"]["min"]}`
- Local max: `{qa["bbox"]["max"]}`
- Source origin EPSG:25832/z: `{qa["origin_world_easting_northing_z"]}`

## Evidence Boundary

This mesh is CFD-ready in the sense of semantic source selection, unit consistency, local z0 conversion, STL export, and QA recording. It is not yet a final SCI wind result until FluidX3D voxelization, grid/time sensitivity, and ParaView post-processing are completed on this expanded geometry.
"""
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps({
        "gml_files": len(paths),
        "rings": len(rings),
        "triangles": qa["triangles"],
        "watertight": qa["watertight"],
        "stl": str(stl_path),
        "qa": str(qa_path),
        "figure": figure_result,
        "grid_estimate": str(grid_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
