from paraview.simple import *
from pathlib import Path


CASE_DIR = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE_DIR / "output"
PV_DIR = CASE_DIR / "paraview"
PV_DIR.mkdir(parents=True, exist_ok=True)

LABEL = "full_lod2_wd000_coarse4m_10k"
STEP = "000010000"
U_VTK = OUT_DIR / f"matrix_{LABEL}_u_finalu-{STEP}.vtk"
FLAGS_VTK = OUT_DIR / f"matrix_{LABEL}_flags_finalflags-{STEP}.vtk"
BUILDING_STL = Path(r"F:\citylbm_fluidx3d_workspace\FluidX3D\stl\building_collision_full_lod2_z0.stl")
STATE = PV_DIR / "tum2twin_full_lod2_wd000_coarse4m_10k_vr_slice_state.pvsm"


def main():
    u = LegacyVTKReader(FileNames=[str(U_VTK)])
    flags = LegacyVTKReader(FileNames=[str(FLAGS_VTK)])
    buildings = STLReader(FileNames=[str(BUILDING_STL)])

    calc = Calculator(Input=u)
    calc.ResultArrayName = "VR"
    calc.Function = "mag(data)/5.0"
    calc.UpdatePipeline()

    bounds = calc.GetDataInformation().GetBounds()
    z_slice = bounds[4] + 2 * 4.0
    slice_filter = Slice(Input=calc)
    slice_filter.SliceType = "Plane"
    slice_filter.SliceType.Origin = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, z_slice]
    slice_filter.SliceType.Normal = [0.0, 0.0, 1.0]
    slice_filter.UpdatePipeline()

    view = CreateView("RenderView")
    view.ViewSize = [1920, 1080]
    view.Background = [1.0, 1.0, 1.0]
    layout = CreateLayout(name="TUM2TWIN_Full_LoD2_WD000")
    layout.AssignView(0, view)

    slice_display = Show(slice_filter, view)
    slice_display.Representation = "Surface"
    ColorBy(slice_display, ("POINTS", "VR"))
    lut = GetColorTransferFunction("VR")
    lut.RGBPoints = [0.0, 0.18995, 0.07176, 0.23217, 0.8, 0.20803, 0.7187, 0.47287, 1.6, 0.99325, 0.90616, 0.14394]
    lut.RescaleTransferFunction(0.0, 1.6)
    slice_display.LookupTable = lut

    building_display = Show(buildings, view)
    building_display.Representation = "Surface With Edges"
    building_display.DiffuseColor = [0.82, 0.82, 0.82]
    building_display.Opacity = 0.45

    Hide(flags, view)
    ResetCamera(view)
    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
