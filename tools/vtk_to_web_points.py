#!/usr/bin/env python3
"""Export a compact, browser-ready vector sample from a legacy binary VTK field.

The resulting JSON deliberately keeps the VTK archive out of Git while retaining
enough spatial and vector information for an honest interactive preview.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Any


def read_legacy_vector_field(path: Path) -> tuple[dict[str, Any], array]:
    """Read the single three-component point field emitted by the archived case."""
    payload = path.read_bytes()
    stream = io.BytesIO(payload)
    header: dict[str, Any] = {"mode": "ASCII", "spacing": [1.0, 1.0, 1.0]}
    data_offset: int | None = None

    while stream.tell() < len(payload):
        line = stream.readline().decode("ascii", errors="ignore").strip()
        if not line:
            continue
        fields = line.split()
        upper = line.upper()
        if fields[0].upper() in {"ASCII", "BINARY"}:
            header["mode"] = fields[0].upper()
        elif upper.startswith("DIMENSIONS"):
            header["dimensions"] = [int(value) for value in fields[1:4]]
        elif upper.startswith("ORIGIN"):
            header["origin"] = [float(value) for value in fields[1:4]]
        elif upper.startswith("SPACING"):
            header["spacing"] = [float(value) for value in fields[1:4]]
        elif upper.startswith("POINT_DATA"):
            header["point_count"] = int(fields[1])
        elif upper.startswith("SCALARS"):
            header["field_name"] = fields[1]
            header["scalar_type"] = fields[2].lower()
            header["components"] = int(fields[3])
            lookup = stream.readline().decode("ascii", errors="ignore").strip()
            if not lookup.upper().startswith("LOOKUP_TABLE"):
                raise ValueError("Expected LOOKUP_TABLE after SCALARS.")
            data_offset = stream.tell()
            break
        elif upper.startswith("VECTORS"):
            header["field_name"] = fields[1]
            header["scalar_type"] = fields[2].lower()
            header["components"] = 3
            data_offset = stream.tell()
            break

    if data_offset is None or header.get("mode") != "BINARY":
        raise ValueError("This exporter expects a legacy binary VTK vector field.")
    if header.get("scalar_type") not in {"float", "float32"}:
        raise ValueError("Only float32 VTK vector fields are supported.")
    if header.get("components") != 3:
        raise ValueError("The VTK field must contain exactly three components.")

    nx, ny, nz = header["dimensions"]
    expected = nx * ny * nz * 3
    raw = payload[data_offset:data_offset + expected * 4]
    if len(raw) != expected * 4:
        raise ValueError("VTK vector payload is shorter than the declared dimensions.")
    vectors = array("f")
    vectors.frombytes(raw)
    if sys.byteorder == "little":
        vectors.byteswap()
    return header, vectors


def physical_position(
    i: int, j: int, k: int, header: dict[str, Any], domain: dict[str, float]
) -> list[float]:
    origin = header["origin"]
    spacing = header["spacing"]
    cell_size = float(domain["Dx"])
    return [
        float(domain["DomainMinX"]) + (origin[0] + i * spacing[0] - origin[0]) * cell_size,
        float(domain["DomainMinY"]) + (origin[1] + j * spacing[1] - origin[1]) * cell_size,
        float(domain["DomainMinZ"]) + (origin[2] + k * spacing[2] - origin[2]) * cell_size,
    ]


def export_points(vtk_path: Path, domain_path: Path, output_path: Path, stride: int) -> int:
    header, vectors = read_legacy_vector_field(vtk_path)
    domain = json.loads(domain_path.read_text(encoding="utf-8-sig"))
    nx, ny, nz = header["dimensions"]
    samples: list[list[float]] = []
    max_speed = 0.0

    for k in range(0, nz, stride):
        for j in range(0, ny, stride):
            for i in range(0, nx, stride):
                index = 3 * (k * ny * nx + j * nx + i)
                u, v, w = vectors[index:index + 3]
                speed = (u * u + v * v + w * w) ** 0.5
                if speed <= 1e-6:
                    continue
                x, y, z = physical_position(i, j, k, header, domain)
                samples.append([
                    round(x, 3), round(y, 3), round(z, 3),
                    round(float(u), 6), round(float(v), 6), round(float(w), 6),
                ])
                max_speed = max(max_speed, speed)

    output = {
        "format": "citylbm-vtk-vector-samples/v1",
        "source": vtk_path.name,
        "source_sha256": hashlib.sha256(vtk_path.read_bytes()).hexdigest(),
        "field": header["field_name"],
        "components": 3,
        "vtk_dimensions": header["dimensions"],
        "sample_stride": stride,
        "sample_count": len(samples),
        "max_speed_in_archive_scale": round(max_speed, 8),
        "velocity_units": "archive scale unresolved; not confirmed SI units",
        "domain": domain,
        "points": samples,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(samples)


def main() -> int:
    parser = argparse.ArgumentParser(description="Downsample a Case A VTK field for the static Three.js preview.")
    parser.add_argument("--vtk", type=Path, required=True)
    parser.add_argument("--domain", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=6)
    args = parser.parse_args()
    if args.stride < 1:
        parser.error("--stride must be at least 1")
    count = export_points(args.vtk, args.domain, args.output, args.stride)
    print(f"Wrote {count} vector samples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
