import struct
from pathlib import Path

import rhino3dm as r3d


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "citylbm_v0.2.0_portable" / "validation" / "【验证】AIJCASEA_u-000002000"
STL = SOURCE / "case" / "buildings.stl"
OUT = ROOT / "CityLBM_v0.2.0_Food4Rhino" / "package" / "validation_experiments" / "AIJ_CaseA" / "rhino" / "AIJ_CaseA_validation.3dm"


def read_binary_stl(path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL is too small: {path}")

    tri_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + tri_count * 50
    if len(data) < expected:
        raise ValueError(f"STL is truncated: expected {expected} bytes, got {len(data)}")

    triangles = []
    offset = 84
    for _ in range(tri_count):
        offset += 12
        pts = []
        for _ in range(3):
            pts.append(struct.unpack_from("<fff", data, offset))
            offset += 12
        triangles.append(pts)
        offset += 2
    return triangles


def add_layer(model, name, color):
    layer = r3d.Layer()
    layer.Name = name
    layer.Color = color
    return model.Layers.Add(layer)


def main():
    triangles = read_binary_stl(STL)
    model = r3d.File3dm()
    model.Settings.ModelUnitSystem = r3d.UnitSystem.Meters

    building_layer = add_layer(model, "AIJ_CASEA_BUILDING", (130, 130, 130, 255))
    annotation_layer = add_layer(model, "VALIDATION_ANNOTATION", (20, 80, 220, 255))

    mesh = r3d.Mesh()
    for tri in triangles:
        face = []
        for x, y, z in tri:
            face.append(mesh.Vertices.Add(x, y, z))
        mesh.Faces.AddFace(face[0], face[1], face[2])
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    attrs = r3d.ObjectAttributes()
    attrs.Name = "AIJ Case A building STL from CityLBM validation run"
    attrs.LayerIndex = building_layer
    model.Objects.AddMesh(mesh, attrs)

    bbox = mesh.GetBoundingBox()
    min_pt = bbox.Min
    max_pt = bbox.Max
    y_mid = (min_pt.Y + max_pt.Y) / 2.0
    z_top = max_pt.Z

    line_attrs = r3d.ObjectAttributes()
    line_attrs.Name = "Reference wind direction marker"
    line_attrs.LayerIndex = annotation_layer
    model.Objects.AddLine(
        r3d.Point3d(min_pt.X - 2.0, y_mid, z_top + 1.0),
        r3d.Point3d(max_pt.X + 2.0, y_mid, z_top + 1.0),
        line_attrs,
    )

    dot_attrs = r3d.ObjectAttributes()
    dot_attrs.Name = "Validation note"
    dot_attrs.LayerIndex = annotation_layer
    model.Objects.AddTextDot(
        "AIJ Case A validation scene\nCityLBM v0.2.0\nSource: u-000002000.vtk",
        r3d.Point3d(min_pt.X, min_pt.Y, z_top + 2.0),
        dot_attrs,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not model.Write(str(OUT), 7):
        raise RuntimeError(f"Failed to write {OUT}")
    print(OUT)


if __name__ == "__main__":
    main()
