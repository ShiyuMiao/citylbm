import csv
import hashlib
import json
import math
import struct
import time
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OBJ_PATH = Path(r"D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected\obj\lod3_merged_city_model\TUM_CentralCampus.obj")
OUT_CFD = ROOT / "cfd_ready"
OUT_FIGURES = ROOT / "figures"
OUT_MANIFESTS = ROOT / "manifests"
OUT_REPORTS = ROOT / "reports"

BUILDING_MATERIALS = {"defaultMat"}
MIN_TRIANGLE_ZMAX = 2.0


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


def edge_key(a, b):
    ar = tuple(round(x, 4) for x in a)
    br = tuple(round(x, 4) for x in b)
    return tuple(sorted((ar, br)))


def signed_volume(tris):
    vol = 0.0
    for a, b, c in tris:
        vol += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
    return vol


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
        duplicate_triangles[tuple(sorted(tuple(round(v, 4) for v in p) for p in tri))] += 1
    return {
        "triangles": len(tris),
        "bbox": bbox_of(tris),
        "signed_volume_m3": signed_volume(tris),
        "unique_edges": len(edges),
        "boundary_edges": sum(1 for count in edges.values() if count == 1),
        "nonmanifold_edges": sum(1 for count in edges.values() if count > 2),
        "degenerate_triangles": degenerate,
        "duplicate_triangles": sum(count - 1 for count in duplicate_triangles.values() if count > 1),
    }


def parse_face_indices(line, vertex_count):
    out = []
    for token in line.split()[1:]:
        first = token.split("/")[0]
        if not first:
            continue
        idx = int(first)
        out.append(idx - 1 if idx > 0 else vertex_count + idx)
    return out


def read_obj_building_tris(path):
    vertices = []
    tris = []
    material_counts = Counter()
    selected_faces = 0
    total_faces = 0
    current_material = None
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("usemtl "):
                current_material = line.strip()[7:] or None
            elif line.startswith("f "):
                total_faces += 1
                material_counts[current_material or "(none)"] += 1
                if current_material not in BUILDING_MATERIALS:
                    continue
                idx = parse_face_indices(line, len(vertices))
                if len(idx) < 3:
                    continue
                pts = [vertices[i] for i in idx if 0 <= i < len(vertices)]
                if len(pts) < 3:
                    continue
                if max(p[2] for p in pts) < MIN_TRIANGLE_ZMAX:
                    continue
                selected_faces += 1
                p0 = pts[0]
                for i in range(1, len(pts) - 1):
                    tris.append([p0, pts[i], pts[i + 1]])
    return tris, {
        "obj_vertices": len(vertices),
        "obj_total_faces": total_faces,
        "selected_source_faces": selected_faces,
        "material_face_counts": dict(material_counts),
        "selected_materials": sorted(BUILDING_MATERIALS),
        "min_triangle_zmax_m": MIN_TRIANGLE_ZMAX,
    }


def offset_xy_only(tris, origin_xy):
    ox, oy = origin_xy
    return [[(p[0] - ox, p[1] - oy, p[2]) for p in tri] for tri in tris]


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


def write_footprint(path, tris, bbox):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    polys = []
    colors = []
    for tri in tris:
        zmax = max(p[2] for p in tri)
        if zmax < MIN_TRIANGLE_ZMAX:
            continue
        polys.append([(p[0], p[1]) for p in tri])
        colors.append(min(zmax, 60.0))
    fig, ax = plt.subplots(figsize=(11, 10), dpi=170)
    coll = PolyCollection(polys, array=colors, cmap="viridis", linewidth=0.0, alpha=0.95)
    ax.add_collection(coll)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(bbox["min"][0] - 20, bbox["max"][0] + 20)
    ax.set_ylim(bbox["min"][1] - 20, bbox["max"][1] + 20)
    ax.set_xlabel("local x (m)")
    ax.set_ylabel("local y (m)")
    ax.set_title("TUM2TWIN district-scale LoD3 OBJ-derived collision audit")
    fig.colorbar(coll, ax=ax, label="triangle zmax (m)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def estimate_grid(bbox, dx_values):
    sx = bbox["max"][0] - bbox["min"][0]
    sy = bbox["max"][1] - bbox["min"][1]
    hmax = bbox["max"][2] - min(0.0, bbox["min"][2])
    rows = []
    # Use reduced urban-domain buffers for district-scale pilot; final wind-direction
    # domains can be cropped/rotated around the target street block.
    lx = sx + 12.0 * hmax
    ly = sy + 12.0 * hmax
    lz = 5.0 * hmax
    for label, dx in dx_values:
        nx, ny, nz = math.ceil(lx / dx), math.ceil(ly / dx), math.ceil(lz / dx)
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


def update_geometry_manifest(stl_path, qa):
    manifest = OUT_MANIFESTS / "geometry_manifest.csv"
    rows = []
    if manifest.exists():
        with manifest.open("r", newline="", encoding="utf-8-sig") as f:
            rows = [r for r in csv.DictReader(f) if "district_lod3_obj" not in r.get("file", "")]
    rows.append({
        "file": str(stl_path),
        "role": "district-scale CFD collision boundary candidate",
        "source": "TUM_CentralCampus.obj defaultMat, zmax>=2m",
        "size_bytes": stl_path.stat().st_size,
        "sha256": qa["stl_sha256"],
        "evidence_type": "newly_run",
    })
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "role", "source", "size_bytes", "sha256", "evidence_type"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    tris_world, source = read_obj_building_tris(OBJ_PATH)
    if not tris_world:
        raise SystemExit("No building candidate triangles selected from OBJ.")
    world_bbox = bbox_of(tris_world)
    origin_xy = (world_bbox["min"][0], world_bbox["min"][1])
    tris = offset_xy_only(tris_world, origin_xy)
    qa = mesh_qa(tris)
    qa.update(source)
    qa["created_at_local"] = time.strftime("%Y-%m-%d %H:%M:%S")
    qa["source_obj"] = str(OBJ_PATH)
    qa["source_obj_size_bytes"] = OBJ_PATH.stat().st_size
    qa["source_coordinate_note"] = "OBJ local coordinates; exported STL subtracts x/y minima only and keeps z in OBJ local meters."
    qa["origin_obj_xy"] = list(origin_xy)
    qa["grid_estimates"] = estimate_grid(qa["bbox"], [("district_coarse", 6.0), ("district_medium", 4.0), ("district_fine_candidate", 2.0)])

    stl_path = OUT_CFD / "district_lod3_obj_collision_z0.stl"
    qa_path = OUT_MANIFESTS / "geometry_qa_district_lod3_obj.json"
    fig_path = OUT_FIGURES / "district_lod3_obj_collision_footprint_audit.png"
    grid_path = OUT_CFD / "FluidX3D_case_template" / "grid_memory_estimate_district_lod3_obj.csv"
    report_path = OUT_REPORTS / "district_scale_geometry_correction_report.md"

    write_binary_stl(stl_path, tris, "tum2twin_district_lod3_obj_collision")
    qa["stl_path"] = str(stl_path)
    qa["stl_size_bytes"] = stl_path.stat().st_size
    qa["stl_sha256"] = sha256(stl_path)
    write_footprint(fig_path, tris, qa["bbox"])
    qa["footprint_audit_figure"] = str(fig_path)

    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    with grid_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(qa["grid_estimates"][0].keys()))
        writer.writeheader()
        writer.writerows(qa["grid_estimates"])
    update_geometry_manifest(stl_path, qa)

    bbox = qa["bbox"]
    report = f"""# District-Scale Geometry Correction Report

evidence_type: newly_run

## Reason For Correction

The previous `building_collision_full_lod2_z0.stl` uses all 27 available LoD2 CityGML building files, but its footprint still reads as a limited campus-core set of buildings. For the user's requested whole-block wind simulation, the collision geometry has been expanded using the official merged LoD3 city OBJ model.

## New District-Scale Candidate

- Source: `{OBJ_PATH}`
- Selected material: `defaultMat`
- Selection rule: keep faces from selected material with triangle zmax >= {MIN_TRIANGLE_ZMAX} m
- Output STL: `{stl_path}`
- QA JSON: `{qa_path}`
- Audit figure: `{fig_path}`

## QA

| Item | Value |
|---|---:|
| OBJ vertices | {qa['obj_vertices']} |
| OBJ total faces | {qa['obj_total_faces']} |
| Selected source faces | {qa['selected_source_faces']} |
| Exported triangles | {qa['triangles']} |
| Boundary edges | {qa['boundary_edges']} |
| Non-manifold edges | {qa['nonmanifold_edges']} |
| Degenerate triangles | {qa['degenerate_triangles']} |
| Duplicate triangles | {qa['duplicate_triangles']} |
| BBox X (m) | {bbox['max'][0] - bbox['min'][0]:.3f} |
| BBox Y (m) | {bbox['max'][1] - bbox['min'][1]:.3f} |
| BBox Z (m) | {bbox['max'][2] - bbox['min'][2]:.3f} |

## Evidence Boundary

This is a district-scale collision candidate derived from the official merged LoD3 OBJ, not from the textured photogrammetry mesh. Because the OBJ is a merged visual/semantic city model rather than a guaranteed closed CFD solid, it must be voxelization-tested in FluidX3D before being used for final wind metrics. The previous LoD2 FluidX3D results are now treated as solver-pipeline evidence only, not as the final whole-block experiment.
"""
    report_path.write_text(report, encoding="utf-8")

    print(json.dumps({
        "stl": str(stl_path),
        "qa": str(qa_path),
        "figure": str(fig_path),
        "triangles": qa["triangles"],
        "bbox": qa["bbox"],
        "grid_estimates": qa["grid_estimates"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
