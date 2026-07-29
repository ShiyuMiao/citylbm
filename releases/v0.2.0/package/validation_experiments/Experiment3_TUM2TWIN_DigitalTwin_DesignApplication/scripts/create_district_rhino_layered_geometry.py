from pathlib import Path
import struct
import rhino3dm


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rhino" / "TUM2TWIN_Downtown_district_CFD_layered_geometry.3dm"
COLLISION_STL = ROOT / "cfd_ready" / "district_prism_collision_z0.stl"
GROUND_STL = ROOT / "cfd_ready" / "ground_domain_z0.stl"
VISUAL_STL = ROOT / "cfd_ready" / "visual_reference_uas_mesh_decimated.stl"


def read_binary_stl(path: Path) -> rhino3dm.Mesh:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL too small: {path}")
    ntri = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + ntri * 50
    if expected > len(data):
        raise ValueError(f"Only binary STL is supported here: {path}")

    mesh = rhino3dm.Mesh()
    vertex_index = {}

    def add_vertex(x, y, z):
        key = (round(x, 6), round(y, 6), round(z, 6))
        idx = vertex_index.get(key)
        if idx is None:
            idx = mesh.Vertices.Add(x, y, z)
            vertex_index[key] = idx
        return idx

    offset = 84
    for _ in range(ntri):
        offset += 12
        pts = []
        for _j in range(3):
            x, y, z = struct.unpack_from("<fff", data, offset)
            offset += 12
            pts.append(add_vertex(x, y, z))
        mesh.Faces.AddFace(pts[0], pts[1], pts[2])
        offset += 2

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


def add_layer(model, name, color):
    layer = rhino3dm.Layer()
    layer.Name = name
    layer.Color = color
    return model.Layers.Add(layer)


def add_mesh(model, mesh, layer_index, name):
    attrs = rhino3dm.ObjectAttributes()
    attrs.LayerIndex = layer_index
    attrs.Name = name
    model.Objects.AddMesh(mesh, attrs)


def main():
    model = rhino3dm.File3dm()
    model.Settings.ModelUnitSystem = rhino3dm.UnitSystem.Meters

    layers = {
        "UAS_Mesh_visual_reference_decimated": add_layer(model, "UAS_Mesh_visual_reference_decimated", (42, 127, 184, 255)),
        "LoD3_District_reference": add_layer(model, "LoD3_District_reference", (44, 160, 44, 255)),
        "Road_Ground": add_layer(model, "Road_Ground", (120, 120, 120, 255)),
        "CFD_Collision_whole_district": add_layer(model, "CFD_Collision_whole_district", (215, 48, 39, 255)),
        "Notes": add_layer(model, "Notes", (40, 40, 40, 255)),
    }

    collision = read_binary_stl(COLLISION_STL)
    add_mesh(model, collision, layers["CFD_Collision_whole_district"], "district_prism_collision_z0")
    add_mesh(model, collision.Duplicate(), layers["LoD3_District_reference"], "district_prism_reference_from_TUM_CentralCampus_OBJ")

    if GROUND_STL.exists():
        add_mesh(model, read_binary_stl(GROUND_STL), layers["Road_Ground"], "ground_domain_z0")

    if VISUAL_STL.exists():
        add_mesh(model, read_binary_stl(VISUAL_STL), layers["UAS_Mesh_visual_reference_decimated"], "visual_reference_uas_mesh_decimated")

    attrs = rhino3dm.ObjectAttributes()
    attrs.LayerIndex = layers["Notes"]
    attrs.Name = "geometry_usage_note"
    model.Objects.AddTextDot(
        "TUM2TWIN whole-district CFD layered geometry\n"
        "Use OBJ+MTL+JPG for exact textured photogrammetry browsing.\n"
        "Use CFD_Collision_whole_district for FluidX3D collision/domain management.\n"
        "The older TUM2TWIN_wind_pilot_layers.3dm collision layer covers only a few buildings.",
        rhino3dm.Point3d(-700, -700, 80),
        attrs,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not model.Write(str(OUT), 7):
        raise RuntimeError(f"Failed to write {OUT}")
    print(OUT.resolve())


if __name__ == "__main__":
    main()
