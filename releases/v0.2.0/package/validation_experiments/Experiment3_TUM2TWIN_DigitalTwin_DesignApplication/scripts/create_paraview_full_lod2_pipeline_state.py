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
STATE = PV_DIR / "tum2twin_full_lod2_wd000_coarse4m_10k_pipeline_no_render.pvsm"


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

    RenameSource("WD000 velocity VTK", u)
    RenameSource("WD000 flags VTK", flags)
    RenameSource("full LoD2 building STL", buildings)
    RenameSource("VR = mag(data)/5", calc)
    RenameSource("VR slice z-index 2", slice_filter)
    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
