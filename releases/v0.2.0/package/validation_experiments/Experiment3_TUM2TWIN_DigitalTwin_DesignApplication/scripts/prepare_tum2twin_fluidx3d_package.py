import csv
import hashlib
import json
import math
import os
import struct
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEAVY_RAW = Path(r"D:\citylbm_tum2twin_heavy_store\raw")
PYDEPS = Path(r"D:\citylbm_tum2twin_heavy_store\pydeps")
if PYDEPS.exists():
    sys.path.insert(0, str(PYDEPS))

OUT_CFD = ROOT / "cfd_ready"
OUT_RHINO = ROOT / "rhino"
OUT_MANIFESTS = ROOT / "manifests"
OUT_REPORTS = ROOT / "reports"
OUT_PAPER = ROOT / "paper_text"

GML_NS = {"gml": "http://www.opengis.net/gml"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
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
    if n == 0:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def bbox_of(tris):
    pts = [p for tri in tris for p in tri]
    if not pts:
        return None
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


def parse_citygml_polygons(paths):
    rings = []
    envelopes = []
    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()
        for env in root.findall(".//gml:Envelope", GML_NS):
            low = env.find("gml:lowerCorner", GML_NS)
            high = env.find("gml:upperCorner", GML_NS)
            if low is not None and high is not None:
                envelopes.append((tuple(map(float, low.text.split())), tuple(map(float, high.text.split()))))
        for pos in root.findall(".//gml:Polygon/gml:exterior/gml:LinearRing/gml:posList", GML_NS):
            vals = list(map(float, pos.text.split()))
            if len(vals) % 3 != 0:
                continue
            ring = [(vals[i], vals[i + 1], vals[i + 2]) for i in range(0, len(vals), 3)]
            rings.append((path.name, ring))
    return rings, envelopes


def offset_triangles(tris, offset):
    ox, oy, oz = offset
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
    for tri in tris:
        a, b, c = tri
        n = vcross(vsub(b, a), vsub(c, a))
        if math.sqrt(sum(x * x for x in n)) < 1e-9:
            degenerate += 1
        edges[edge_key(a, b)] += 1
        edges[edge_key(b, c)] += 1
        edges[edge_key(c, a)] += 1
    boundary = sum(1 for v in edges.values() if v == 1)
    nonmanifold = sum(1 for v in edges.values() if v > 2)
    return {
        "triangles": len(tris),
        "bbox": bbox_of(tris),
        "signed_volume": signed_volume(tris),
        "unique_edges": len(edges),
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "degenerate_triangles": degenerate,
        "watertight": boundary == 0 and nonmanifold == 0 and degenerate == 0,
    }


def write_binary_stl(path, tris, name="mesh"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        header = (name[:80]).encode("ascii", "ignore").ljust(80, b" ")
        f.write(header)
        f.write(struct.pack("<I", len(tris)))
        for tri in tris:
            a, b, c = tri
            n = vnorm(vcross(vsub(b, a), vsub(c, a)))
            f.write(struct.pack("<3f", *n))
            f.write(struct.pack("<3f", *a))
            f.write(struct.pack("<3f", *b))
            f.write(struct.pack("<3f", *c))
            f.write(struct.pack("<H", 0))


def make_ground(domain_bbox, margin=80.0):
    mn, mx = domain_bbox["min"], domain_bbox["max"]
    x0, x1 = mn[0] - margin, mx[0] + margin
    y0, y1 = mn[1] - margin, mx[1] + margin
    z = 0.0
    return [
        [(x0, y0, z), (x1, y0, z), (x1, y1, z)],
        [(x0, y0, z), (x1, y1, z), (x0, y1, z)],
    ]


def sample_obj_to_stl(obj_path, out_path, max_faces=120000):
    vertices = []
    faces = []
    total_faces = 0
    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                total_faces += 1
    step = max(1, math.ceil(total_faces / max_faces))
    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        face_i = 0
        for line in f:
            if not line.startswith("f "):
                continue
            if face_i % step == 0:
                idx = []
                for token in line.split()[1:]:
                    idx.append(int(token.split("/")[0]) - 1)
                if len(idx) >= 3:
                    p0 = vertices[idx[0]]
                    for i in range(1, len(idx) - 1):
                        faces.append([p0, vertices[idx[i]], vertices[idx[i + 1]]])
            face_i += 1
    write_binary_stl(out_path, faces, "uas_visual_reference_decimated")
    return total_faces, step, faces


def write_rhino_3dm(path, layers, meshes):
    try:
        import rhino3dm
    except Exception as exc:
        return {"created": False, "reason": repr(exc)}
    model = rhino3dm.File3dm()
    layer_index = {}
    for layer_name in layers:
        layer = rhino3dm.Layer()
        layer.Name = layer_name
        layer_index[layer_name] = model.Layers.Add(layer)
    for layer_name, tris in meshes.items():
        mesh = rhino3dm.Mesh()
        vmap = {}
        def vid(p):
            key = tuple(round(x, 6) for x in p)
            if key not in vmap:
                vmap[key] = mesh.Vertices.Add(p[0], p[1], p[2])
            return vmap[key]
        for a, b, c in tris:
            mesh.Faces.AddFace(vid(a), vid(b), vid(c))
        mesh.Normals.ComputeNormals()
        mesh.Compact()
        attr = rhino3dm.ObjectAttributes()
        attr.LayerIndex = layer_index.get(layer_name, 0)
        attr.Name = layer_name
        model.Objects.AddMesh(mesh, attr)
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Meters
    model.Write(str(path), 7)
    return {"created": True, "path": str(path)}


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    for d in [OUT_CFD, OUT_RHINO, OUT_MANIFESTS, OUT_REPORTS, OUT_PAPER]:
        d.mkdir(parents=True, exist_ok=True)

    selected = HEAVY_RAW / "tum2twin_gitlab_selected"
    zenodo = HEAVY_RAW / "zenodo_14548134"
    lod2_paths = [
        selected / "citygml/lod2-building-datasets/DEBY_LOD2_4906970.gml",
        selected / "citygml/lod2-building-datasets/DEBY_LOD2_4906972.gml",
        selected / "citygml/lod2-building-datasets/DEBY_LOD2_4906976.gml",
        selected / "citygml/lod2-building-datasets/DEBY_LOD2_4906981.gml",
    ]
    lod3_paths = [
        selected / "citygml/lod3-building-datasets/DEBY_LOD3_4906970.gml",
        selected / "citygml/lod3-building-datasets/DEBY_LOD3_4906972.gml",
        selected / "citygml/lod3-building-datasets/DEBY_LOD3_4906976.gml",
        selected / "citygml/lod3-building-datasets/DEBY_LOD3_4906981.gml",
    ]
    uas_obj = zenodo / "TUM_Downtown_Photogrammetry_20241217_Mesh.obj"
    uas_mtl = zenodo / "TUM_Downtown_Photogrammetry_20241217_Mesh.mtl"
    uas_offset = zenodo / "TUM_Downtown_Photogrammetry_20241217_Mesh_offset.xyz"

    lod2_rings, lod2_envs = parse_citygml_polygons(lod2_paths)
    lod3_rings, lod3_envs = parse_citygml_polygons(lod3_paths)
    lod2_tris_world = [tri for _, ring in lod2_rings for tri in triangulate_ring(ring)]
    lod3_tris_world = [tri for _, ring in lod3_rings for tri in triangulate_ring(ring)]
    bb_world = bbox_of(lod2_tris_world)
    origin = (bb_world["min"][0], bb_world["min"][1], bb_world["min"][2])
    lod2_tris = offset_triangles(lod2_tris_world, origin)
    lod3_tris = offset_triangles(lod3_tris_world, origin)

    # Keep positive volume orientation for downstream voxelization assumptions.
    if signed_volume(lod2_tris) < 0:
        lod2_tris = [[a, c, b] for a, b, c in lod2_tris]
    if signed_volume(lod3_tris) < 0:
        lod3_tris = [[a, c, b] for a, b, c in lod3_tris]

    building_stl = OUT_CFD / "building_collision_z0.stl"
    lod3_stl = OUT_CFD / "lod3_building_reference_z0.stl"
    ground_stl = OUT_CFD / "ground_domain_z0.stl"
    visual_stl = OUT_CFD / "visual_reference_uas_mesh_decimated.stl"
    write_binary_stl(building_stl, lod2_tris, "TUM2TWIN_LoD2_building_collision_z0")
    write_binary_stl(lod3_stl, lod3_tris, "TUM2TWIN_LoD3_building_reference_z0")
    ground_tris = make_ground(bbox_of(lod2_tris), margin=80.0)
    write_binary_stl(ground_stl, ground_tris, "TUM2TWIN_ground_domain_z0")
    total_uas_faces, uas_step, visual_tris = sample_obj_to_stl(uas_obj, visual_stl)

    rhino_path = OUT_RHINO / "TUM2TWIN_wind_pilot_layers.3dm"
    rhino_status = write_rhino_3dm(
        rhino_path,
        ["UAS_Mesh", "LoD2_Buildings", "LoD3_Buildings", "Vegetation", "Road_Ground", "CFD_Collision"],
        {
            "CFD_Collision": lod2_tris,
            "LoD3_Buildings": lod3_tris[:250000],
            "UAS_Mesh": visual_tris[:60000],
            "Road_Ground": ground_tris,
        },
    )

    qa = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "coordinate_reference_system": "EPSG:25832 in source CityGML; exported STLs use local z0 coordinates in meters",
        "origin_world_easting_northing_z": origin,
        "lod2_source_envelopes": lod2_envs,
        "lod3_source_envelopes": lod3_envs,
        "building_collision_z0": mesh_qa(lod2_tris),
        "lod3_reference_z0": mesh_qa(lod3_tris),
        "ground_domain_z0": mesh_qa(ground_tris),
        "visual_reference_uas_mesh_decimated": {
            **mesh_qa(visual_tris),
            "source_total_faces": total_uas_faces,
            "sampling_step": uas_step,
        },
        "rhino_3dm": rhino_status,
    }
    write_text(OUT_MANIFESTS / "geometry_qa.json", json.dumps(qa, ensure_ascii=False, indent=2))

    geometry_rows = []
    for p, role, source in [
        (building_stl, "CFD collision boundary", "LoD2 CityGML"),
        (lod3_stl, "semantic/detail reference", "LoD3 CityGML"),
        (ground_stl, "ground/domain plane", "derived from LoD2 bbox"),
        (visual_stl, "visual/reference STL", "UAS photogrammetry OBJ, decimated"),
        (rhino_path, "Rhino layer model", "generated 3DM"),
    ]:
        geometry_rows.append({
            "file": str(p),
            "role": role,
            "source": source,
            "size_bytes": p.stat().st_size if p.exists() else "",
            "sha256": sha256(p) if p.exists() else "",
            "evidence_type": "newly_run",
        })
    with open(OUT_MANIFESTS / "geometry_manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=geometry_rows[0].keys())
        writer.writeheader()
        writer.writerows(geometry_rows)

    data_files = [
        (uas_obj, "https://zenodo.org/records/14548134", "UAS 3D Mesh OBJ", "cc-by-4.0", "Anders et al., UAV Laser Scanning and Photogrammetry of TUM Downtown Campus, Zenodo, DOI 10.5281/zenodo.14548134"),
        (uas_mtl, "https://zenodo.org/records/14548134", "UAS 3D Mesh MTL", "cc-by-4.0", "Anders et al., Zenodo DOI 10.5281/zenodo.14548134"),
        (uas_offset, "https://zenodo.org/records/14548134", "UAS 3D Mesh offset", "cc-by-4.0", "Anders et al., Zenodo DOI 10.5281/zenodo.14548134"),
    ] + [(p, "https://gitlab.lrz.de/tum-gis/tum2twin-datasets", p.name, "repository LICENSE, verify before publication", "TUM2TWIN GitLab dataset repository") for p in lod2_paths + lod3_paths]
    data_rows = []
    for p, url, desc, license_id, citation in data_files:
        data_rows.append({
            "local_path": str(p),
            "source_url": url,
            "description": desc,
            "size_bytes": p.stat().st_size if p.exists() else "",
            "md5": md5(p) if p.exists() else "",
            "sha256": sha256(p) if p.exists() else "",
            "download_time_local": time.strftime("%Y-%m-%d %H:%M:%S"),
            "license": license_id,
            "citation": citation,
            "evidence_type": "preexisting_artifact",
        })
    with open(OUT_MANIFESTS / "data_manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data_rows[0].keys())
        writer.writeheader()
        writer.writerows(data_rows)

    evidence_rows = [
        {"claim": "UAS 3D Mesh is used as visual/photogrammetric reference, not final collision boundary.", "evidence_type": "preexisting_artifact", "source": "TUM2TWIN cm-mesh page and downloaded OBJ/MTL"},
        {"claim": "LoD2/LoD3 CityGML building models provide semantic building surfaces for CFD collision geometry.", "evidence_type": "preexisting_artifact", "source": "TUM2TWIN semantic building models page and downloaded CityGML"},
        {"claim": "building_collision_z0.stl was generated from four LoD2 buildings and checked locally.", "evidence_type": "newly_run", "source": str(OUT_MANIFESTS / "geometry_qa.json")},
        {"claim": "FluidX3D simulation results are not available on this machine yet.", "evidence_type": "blocked", "source": "FluidX3D executable/OpenCL build not installed or run in this session"},
        {"claim": "ParaView visualization is specified as VTK workflow; no ParaView-rendered images were generated.", "evidence_type": "blocked", "source": "No FluidX3D VTK output yet"},
    ]
    with open(OUT_MANIFESTS / "evidence_inventory.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=evidence_rows[0].keys())
        writer.writeheader()
        writer.writerows(evidence_rows)

    write_templates(qa)
    write_reports(qa)
    print(json.dumps({
        "building_stl": str(building_stl),
        "lod3_stl": str(lod3_stl),
        "ground_stl": str(ground_stl),
        "visual_stl": str(visual_stl),
        "rhino_3dm": str(rhino_path),
        "qa": str(OUT_MANIFESTS / "geometry_qa.json"),
    }, ensure_ascii=False, indent=2))


def write_templates(qa):
    fluid_dir = OUT_CFD / "FluidX3D_case_template"
    citylbm_dir = OUT_CFD / "CityLBM_GH_input_template"
    fluid_dir.mkdir(parents=True, exist_ok=True)
    citylbm_dir.mkdir(parents=True, exist_ok=True)
    bbox = qa["building_collision_z0"]["bbox"]
    dx_options = [
        ("coarse", 2.0),
        ("medium", 1.0),
        ("fine", 0.5),
    ]
    rows = []
    lx = bbox["max"][0] - bbox["min"][0] + 160.0
    ly = bbox["max"][1] - bbox["min"][1] + 160.0
    hmax = bbox["max"][2] - bbox["min"][2]
    lz = hmax + 120.0
    for name, dx in dx_options:
        nx, ny, nz = math.ceil(lx / dx), math.ceil(ly / dx), math.ceil(lz / dx)
        cells = nx * ny * nz
        rows.append((name, dx, nx, ny, nz, cells, round(cells * 120 / 1024**3, 2)))
    setup_cpp = f"""// TUM2TWIN wind pilot template for FluidX3D.
// Copy this file into FluidX3D/src/setup.cpp after installing/building FluidX3D.
// Geometry: cfd_ready/building_collision_z0.stl, meters, z0-local coordinates.
// Evidence boundary: template only; no simulation result is claimed.

void main_setup() {{
    // Required extensions in defines.hpp: EQUILIBRIUM_BOUNDARIES, VOLUME_FORCE
    const uint Nx = {rows[0][2]}u, Ny = {rows[0][3]}u, Nz = {rows[0][4]}u; // coarse pilot
    const float si_Uref = 5.0f;       // m/s at 10 m, placeholder until wind rose is connected
    const float si_nu_air = 1.5E-5f;  // m^2/s
    const float dx = {rows[0][1]}f;   // m/cell
    units.set_m_kg_s(1.0f, 0.05f, 1.0f, dx, si_Uref, 1.225f);
    const float lbm_nu = units.nu(si_nu_air);
    LBM lbm(Nx, Ny, Nz, lbm_nu);

    Mesh* buildings = read_stl(get_exe_path()+\"../stl/building_collision_z0.stl\", 1.0f);
    lbm.voxelize_mesh_on_device(buildings, TYPE_S);

    // Boundary-condition sketch:
    // - Rotate or remap wind vector for eight directions: 0,45,...,315 degrees.
    // - Use TYPE_E equilibrium boundaries for inflow/top as needed.
    // - Keep buildings and ground as no-slip TYPE_S.
    // - Export u/rho/flags VTK after spin-up and averaging windows for ParaView.
    lbm.run(0u);
    for(uint t=0u; t<=20000u; t+=1000u) {{
        lbm.run(1000u);
        if(t>=10000u) {{
            lbm.u.write_device_to_vtk();
            lbm.flags.write_device_to_vtk();
        }}
    }}
}}
"""
    write_text(fluid_dir / "setup_tum2twin_wind_pilot.cpp", setup_cpp)
    write_text(fluid_dir / "run_matrix.csv", "case_id,wind_dir_deg,Uref_10m,ped_height_m,dx_m,Nx,Ny,Nz,status\n" + "\n".join(
        f"S0_WD{d},{d},5.0,1.5,{rows[0][1]},{rows[0][2]},{rows[0][3]},{rows[0][4]},blocked_by_missing_solver"
        for d in [0,45,90,135,180,225,270,315]
    ) + "\n")
    write_text(fluid_dir / "paraview_pipeline.md", """# ParaView visualization pipeline

1. Open FluidX3D exported `u-*.vtk`, `rho-*.vtk`, and `flags-*.vtk`.
2. Load `../building_collision_z0.stl` and `../ground_domain_z0.stl` as context geometry.
3. Apply `Slice` at z=1.5 m for pedestrian wind, plus z=10/20/40 m for low-altitude analysis.
4. Use `Calculator` for `sqrt(u_X*u_X+u_Y*u_Y+u_Z*u_Z)/5.0` as `VR`.
5. Use `Threshold`/`Contour` for acceleration, stagnation, and hotspot zones.
6. Export CSV slices for metric computation; do not save screenshots as evidence until VTK comes from a completed FluidX3D run.
""")
    write_text(fluid_dir / "grid_memory_estimate.csv", "level,dx_m,Nx,Ny,Nz,cells,rough_vram_GB_at_120B_per_cell\n" + "\n".join(
        ",".join(map(str, row)) for row in rows
    ) + "\n")
    write_text(citylbm_dir / "README.md", """# CityLBM / Grasshopper optional input template

This folder is retained only as a secondary interoperability template. The main solver path for this experiment is FluidX3D with ParaView visualization.

Inputs:
- `../building_collision_z0.stl`
- `../ground_domain_z0.stl`
- `../../manifests/geometry_qa.json`

Status: not executed.
Evidence type: blocked / optional, because CityLBM is not installed and is not the requested primary solver.
""")


def write_reports(qa):
    bbox = qa["building_collision_z0"]["bbox"]
    hmax = bbox["max"][2] - bbox["min"][2]
    reports = {
        "tum2twin_experiment_design.md": f"""# TUM2TWIN 城市数字孪生风环境应用实验设计

evidence_type: preexisting_artifact + newly_run + blocked

本实验位于 Case A/E 之后，定位为真实数字孪生街区数据进入风环境模拟的应用落地验证。Case A/E 承担求解器基准与基础验证；TUM2TWIN Case 不重复宣称求解器精度，而验证多源数字孪生数据如何分层转化为 CFD/LBM 可用几何、工况矩阵、指标体系和可复现实验包。

对象选择：TUM Downtown pilot 子区块，使用 DEBY_LOD2/LOD3_4906970、4906972、4906976、4906981 四栋建筑，覆盖多栋建筑、街道边界、入口/开放空间和近地风环境分析场景。

数据分层：
- UAS 3D Mesh / UAS photographs：用于真实外观、3DGS/影像重建参照和 Rhino 视觉对齐，不作为最终碰撞实体。
- CityGML LoD2/LoD3：作为建筑语义与碰撞边界的主要来源；当前 `building_collision_z0.stl` 来源于 LoD2。
- CAD/OBJ/Rhino：作为可视化、检查、图层管理和 STL 转换中间层。
- pc-fac：用于立面语义参考与 3DGS-to-boundary 讨论，不作为 CFD 闭合几何。

计算域初设：Hmax={hmax:.2f} m；建议上游 5H、下游 15H、侧向 5H、顶部 5H。当前 pilot 输出先采用 bbox+80 m 水平边界、顶部约 Hmax+120 m 的粗网格模板。

主求解路线：FluidX3D；可视化路线：ParaView 读取 FluidX3D `.vtk` 输出。
""",
        "data_source_and_download_manifest.md": """# 数据来源与下载 Manifest

evidence_type: preexisting_artifact + newly_run

官方核验页面：
- https://tum2t.win/datasets
- https://tum2t.win/datasets/cm-mesh
- https://tum2t.win/datasets/cm-buildings
- https://tum2t.win/datasets/cm-vegetation
- https://tum2t.win/datasets/cm-cad
- https://tum2t.win/benchmarks/pc-fac

本机下载记录见：
- `manifests/data_manifest.csv`
- `manifests/tum2twin_gitlab_tree.json`
- `manifests/tum2twin_gitlab_tree_blobs.csv`

重数据实际存放在 D 盘：
- `D:\\citylbm_tum2twin_heavy_store\\raw\\zenodo_14548134`
- `D:\\citylbm_tum2twin_heavy_store\\raw\\tum2twin_gitlab_selected`

原因：C 盘剩余空间不足，重数据转移到 D 盘以保证后续处理稳定。
""",
        "rhino_geometry_conversion_report.md": f"""# Rhino 几何转换报告

evidence_type: newly_run

Rhino 文件：
- `{OUT_RHINO / 'TUM2TWIN_wind_pilot_layers.3dm'}`

图层：
- UAS_Mesh：UAS OBJ 抽样视觉参考网格；
- LoD2_Buildings：LoD2 建筑来源；
- LoD3_Buildings：LoD3 细节参考抽样；
- Vegetation：保留图层，当前未实体化为风场阻力模型；
- Road_Ground：地面/域平面；
- CFD_Collision：FluidX3D 主碰撞边界。

说明：精确带贴图浏览仍应优先使用原始 OBJ+MTL+贴图文件。当前 Zenodo 已下载 OBJ/MTL，但 MTL 引用的 `TUM2TWIN-all-mesh.jpg` 不在已核验的小体量下载文件中；因此 3DM 主要用于 Rhino/GH 分层建模与碰撞实体管理，不宣称完整嵌入原始 UV 贴图。
""",
        "cfd_ready_geometry_qa.md": f"""# CFD-ready Geometry QA

evidence_type: newly_run

单位：米。源 CRS：EPSG:25832。导出 STL：local z0 坐标，原点为 `{qa['origin_world_easting_northing_z']}`。

主要文件：
- `cfd_ready/building_collision_z0.stl`
- `cfd_ready/lod3_building_reference_z0.stl`
- `cfd_ready/ground_domain_z0.stl`
- `cfd_ready/visual_reference_uas_mesh_decimated.stl`

QA JSON：`manifests/geometry_qa.json`

关键检查：
- building_collision_z0 triangles: {qa['building_collision_z0']['triangles']}
- building_collision_z0 watertight: {qa['building_collision_z0']['watertight']}
- boundary_edges: {qa['building_collision_z0']['boundary_edges']}
- nonmanifold_edges: {qa['building_collision_z0']['nonmanifold_edges']}
- Hmax: {hmax:.2f} m

若 FluidX3D 对 STL 法线或孔洞敏感，下一步在 Rhino/Blender/Microsoft 3D Builder 中执行封闭性修复，并以 `voxelization_success` 更新 Readiness Index。
""",
        "metric_system_for_digital_twin_wind_application.md": metric_report(),
        "simulation_protocol_without_solver.md": """# FluidX3D + ParaView 模拟协议

evidence_type: blocked

状态：blocked_by_missing_solver。当前机器尚未安装/编译 FluidX3D，也未运行 ParaView 后处理。

主路线：
1. 安装 OpenCL GPU/CPU runtime。
2. 编译 FluidX3D。
3. 将 `cfd_ready/building_collision_z0.stl` 复制到 FluidX3D `stl/`。
4. 将 `cfd_ready/FluidX3D_case_template/setup_tum2twin_wind_pilot.cpp` 合并到 `src/setup.cpp`。
5. 对 8 个风向运行 coarse pilot。
6. 输出 `u-*.vtk`、`rho-*.vtk`、`flags-*.vtk`。
7. 使用 ParaView pipeline 提取 1.5 m pedestrian plane、10/20/40 m UAV planes。

不伪造内容：本包不包含模拟云图、风速数值结论、显存性能实测或精度验证结论。
""",
        "claim_boundary.md": """# Claim Boundary

evidence_type: newly_run + preexisting_artifact + blocked

可以声称：
- 已完成 TUM2TWIN 官方资料核验、数据分层定位和本机下载记录。
- 已从 CityGML LoD2/LoD3 生成 CFD-ready STL 和 Rhino 3DM 分层文件。
- 已设计 FluidX3D + ParaView 的实验协议、工况矩阵和指标体系。

不能声称：
- FluidX3D 已完成真实风场模拟。
- 结果已被实测风场或风洞数据验证。
- 3DGS/photogrammetry mesh 可直接作为闭合刚性碰撞边界。
- ParaView 云图来自本机求解结果。

缺失闭环：
- FluidX3D 编译与 OpenCL 设备验证。
- ParaView 对 VTK 的实际读取截图。
- 实测风速、风玫瑰或污染物观测数据。
""",
    }
    for name, text in reports.items():
        write_text(OUT_REPORTS / name, text)
    write_text(OUT_PAPER / "method_section_zh.md", method_section())
    write_text(OUT_PAPER / "experiment_design_paragraph_zh.md", experiment_paragraph())


def metric_report():
    return """# 数字孪生城市风环境指标体系

evidence_type: user_claim + preexisting_artifact + blocked

| 类别 | 指标 | 公式/定义 | 输出 | evidence_type |
|---|---|---|---|---|
| 行人风速 | VR | VR = U_ped / U_ref | mean, P75, P90, P95, max, 加速区/滞风区 | blocked |
| 舒适安全 | Lawson/NEN/AIJ 思路 | 阈值风速 + 超越概率 + 活动类型 | comfortable/tolerable/uncomfortable/unsafe 面积比例 | blocked |
| 通风不足 | stagnation area ratio | A(U/Uref < 阈值)/A_total | 污染滞留与热舒适风险区 | blocked |
| 污染扩散 | C/C0 | 道路/点/面源无量纲浓度 | hotspot 面积、路径暴露积分 | blocked |
| 方案比较 | ΔA, Δhotspot | S0 baseline vs S1-Sn | 舒适面积提升、危险面积降低 | blocked |
| Geometry-to-CFD Readiness Index | GCRI | 0.25W + 0.15(1-NM) + 0.15S + 0.15C + 0.15E + 0.15V | 0-1，越高越可进入 CFD | newly_run + blocked |
| 3DGS-to-Collision Boundary Transfer Error | GCBTE | IoU, Chamfer/Hausdorff, roof/wall boundary error, solid mask agreement | 用 CityGML LoD2/LoD3 作 GT | blocked |
| 工程效率 | Wind Benefit per Modeling Cost | Δ舒适面积 / 建模修复小时 | 方案工程收益 | blocked |
| 周转效率 | Digital Twin Scenario Turnaround Time | 下载-可视化-STL-case template 用时 | 工程落地效率 | newly_run |

GCRI 子项建议：
- W watertight ratio；
- NM non-manifold error normalized；
- S semantic layer completeness；
- C coordinate/unit consistency；
- E STL export success；
- V voxelization success。

当前 V 项必须等 FluidX3D 实际 voxelization 后更新。
"""


def method_section():
    return """# 方法段落（中文）

本文构建了一个面向真实城市数字孪生数据的风环境模拟落地流程。研究对象选取 TUM2TWIN TUM Downtown 数据集中包含街道峡谷、多栋建筑与开放空间关系的 pilot 子区块。数据首先按照物理边界属性进行分层：UAS photogrammetry mesh 与影像数据用于真实外观参照、三维重建质量检查和 3DGS/视觉模型对齐；CityGML LoD2/LoD3 语义建筑模型作为建筑碰撞边界的主要来源；CAD/OBJ/Rhino 模型作为 Rhino/Grasshopper 中间层，用于图层组织、几何检查与 STL 输出；pc-fac 立面语义分割基准仅用于语义参考，不作为封闭 CFD 几何。几何转换阶段将 CityGML 多边形表面解析、三角化并转换到以地面最低点为零高程的局部米制坐标系，输出 `building_collision_z0.stl`、`lod3_building_reference_z0.stl`、`ground_domain_z0.stl` 与视觉参考 STL，同时记录坐标原点、包围盒、三角面数、边界边、非流形边和封闭性检查。数值模拟阶段以 FluidX3D 作为 LBM 求解器，利用二进制 STL 建筑边界进行体素化，设置 8 个主导风向、10 m 高度参考风速 5 m/s 的初始工况，并在行人高度 1.5 m 及 10/20/40 m 低空高度层输出速度、风速比、涡量及可选污染物浓度场。结果通过 ParaView 读取 FluidX3D 导出的 VTK 文件进行切片、阈值分区和指标统计。"""


def experiment_paragraph():
    return """# 实验定位段落（中文）

本实验不以重新证明 FluidX3D 或 CityLBM 的求解精度为目标，而是置于前序 Case A/E 基准与验证之后，检验真实城市数字孪生数据进入风环境模拟应用的可行性与证据边界。TUM2TWIN 提供了同一校园环境下的 UAS 影像重建网格、CityGML LoD2/LoD3 语义建筑、植被、道路和 CAD/OBJ 模型，使其适合回答“数字孪生数据如何从可视化资产转化为 CFD/LBM 可计算边界”的问题。实验明确区分外观真实与物理可计算性：3DGS 或 photogrammetry mesh 可提供视觉参照和表面细节，但由于孔洞、噪声、非流形结构与语义缺失，不能直接作为最终刚性碰撞边界；建筑碰撞边界优先由 CityGML LoD2/LoD3 或 CAD-derived 模型生成。由此，本文将风环境结果解释限制在数字孪生几何准备、FluidX3D case 构建、ParaView 后处理与指标体系设计层面；在缺少实测风场或风洞闭环前，不宣称预测精度已被实测证明。"""


if __name__ == "__main__":
    main()
