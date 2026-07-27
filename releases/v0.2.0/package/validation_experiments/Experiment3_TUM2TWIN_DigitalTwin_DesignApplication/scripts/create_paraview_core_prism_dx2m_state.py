from pathlib import Path
from paraview.simple import *


ROOT = Path(r"C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究")
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE / "paraview"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATE = OUT_DIR / "tum2twin_core_prism_dx2m_8dir_audit_pipeline.pvsm"
COLLISION_STL = ROOT / "cfd_ready" / "core_photogrammetry_extent_prism_collision_z0.stl"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]


def main():
    ResetSession()

    collision = STLReader(registrationName="core_prism_collision_z0", FileNames=[str(COLLISION_STL)])
    collision.UpdatePipeline()

    first = None
    for wd in WIND_DIRS:
        label = f"core_prism_wd{wd:03d}_dx2m_10k"
        src = LegacyVTKReader(
            registrationName=f"{label}_u_final",
            FileNames=[str(CASE / "output" / f"matrix_{label}_u_finalu-000010000.vtk")],
        )
        src.UpdatePipeline()
        if wd == 0:
            first = src

    calc = Calculator(registrationName="core_prism_wd000_velocity_magnitude", Input=first)
    calc.AttributeType = "Point Data"
    calc.ResultArrayName = "velocity_mag"
    calc.Function = "mag(data)"
    calc.UpdatePipeline()

    for z in [2.0, 4.0, 10.0, 20.0, 40.0]:
        slc = Slice(registrationName=f"core_prism_wd000_velocity_mag_slice_z{int(z)}m", Input=calc)
        slc.SliceType = "Plane"
        slc.SliceType.Origin = [0.0, 0.0, z]
        slc.SliceType.Normal = [0.0, 0.0, 1.0]
        slc.UpdatePipeline()

    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
