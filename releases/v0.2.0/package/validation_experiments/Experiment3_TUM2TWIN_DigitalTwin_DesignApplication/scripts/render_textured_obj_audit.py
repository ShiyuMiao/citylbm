from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


OBJ = Path(r"D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.obj")
TEX = Path(r"D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.jpg")
OUT = Path(r"C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\tum2twin_textured_mesh_topdown_audit.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

FACE_STRIDE = 2
CANVAS_W = 1800
CANVAS_H = 2400


def parse_obj_sample(path: Path, stride: int):
    vertices: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    polys: list[list[tuple[float, float, float]]] = []
    uvs: list[list[tuple[float, float]]] = []
    face_count = 0

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                _tag, x, y, z = line.split()[:4]
                vertices.append((float(x), float(y), float(z)))
            elif line.startswith("vt "):
                parts = line.split()
                texcoords.append((float(parts[1]), float(parts[2])))
            elif line.startswith("f "):
                face_count += 1
                if face_count % stride != 0:
                    continue
                xy: list[tuple[float, float]] = []
                uv: list[tuple[float, float]] = []
                for token in line.split()[1:4]:
                    fields = token.split("/")
                    vi = int(fields[0]) - 1
                    ti = int(fields[1]) - 1 if len(fields) > 1 and fields[1] else vi
                    x, y, _z = vertices[vi]
                    u, v = texcoords[ti]
                    xy.append((x, y, _z))
                    uv.append((u, v))
                polys.append(xy)
                uvs.append(uv)
    return np.asarray(polys, dtype=np.float32), np.asarray(uvs, dtype=np.float32), len(vertices), len(texcoords), face_count


def main() -> None:
    polys, uvs, vertex_count, texcoord_count, face_count = parse_obj_sample(OBJ, FACE_STRIDE)
    image = Image.open(TEX).convert("RGB")
    tex = np.asarray(image)
    h, w = tex.shape[:2]

    uv_centers = uvs.mean(axis=1)
    px = np.clip((uv_centers[:, 0] * (w - 1)).astype(int), 0, w - 1)
    py = np.clip(((1.0 - uv_centers[:, 1]) * (h - 1)).astype(int), 0, h - 1)
    colors = tex[py, px]

    xy = polys[:, :, :2]
    z = polys[:, :, 2].mean(axis=1)
    min_xy = xy.reshape(-1, 2).min(axis=0)
    max_xy = xy.reshape(-1, 2).max(axis=0)
    scale = min((CANVAS_W - 80) / (max_xy[0] - min_xy[0]), (CANVAS_H - 80) / (max_xy[1] - min_xy[1]))
    offset = np.array([40.0, 40.0], dtype=np.float32)
    pts = (xy - min_xy) * scale + offset
    pts[:, :, 1] = CANVAS_H - pts[:, :, 1]

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), "white")
    draw = ImageDraw.Draw(canvas)
    order = np.argsort(z)  # draw ground/low points first, roofs later
    for i in order:
        tri = [tuple(p) for p in pts[i]]
        color = tuple(int(c) for c in colors[i])
        draw.polygon(tri, fill=color)

    header = Image.new("RGB", (CANVAS_W, 150), "white")
    hdraw = ImageDraw.Draw(header)
    hdraw.text((30, 20), "TUM2TWIN textured photogrammetry mesh audit", fill=(0, 0, 0))
    hdraw.text((30, 55), f"sampled {len(polys):,}/{face_count:,} faces; vertices {vertex_count:,}; texcoords {texcoord_count:,}", fill=(0, 0, 0))
    hdraw.text((30, 90), f"source: {OBJ}", fill=(0, 0, 0))
    combined = Image.new("RGB", (CANVAS_W, CANVAS_H + 150), "white")
    combined.paste(header, (0, 0))
    combined.paste(canvas, (0, 150))
    combined.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
