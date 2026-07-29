from pathlib import Path
from paraview.simple import *


ROOT = Path(r"C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究")
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE / "paraview"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATE = OUT_DIR / "tum2twin_district_prism_medium4m_8dir_audit_pipeline.pvsm"
COLLISION_STL = ROOT / "cfd_ready" / "district_prism_collision_z0.stl"

WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
VTK_FILES = {
    wd: CASE / "output" / f"matrix_district_prism_wd{wd:03d}_medium4m_10k_u_finalu-000010000.vtk"
    for wd in WIND_DIRS
}


def main():
    ResetSession()

    collision = STLReader(registrationName="district_prism_collision_z0", FileNames=[str(COLLISION_STL)])
    collision.UpdatePipeline()

    first = LegacyVTKReader(
        registrationName="wd000_medium4m_10k_u_final",
        FileNames=[str(VTK_FILES[0])],
    )
    first.UpdatePipeline()

    calc = Calculator(registrationName="wd000_velocity_magnitude_VR_proxy", Input=first)
    calc.AttributeType = "Point Data"
    calc.ResultArrayName = "velocity_mag"
    calc.Function = "mag(data)"
    calc.UpdatePipeline()

    # ParaView audit slices. With dx=4 m, these are low-altitude and roof/low-UAV review planes,
    # not formal 1.5-2.0 m pedestrian comfort planes.
    for z in [8.0, 20.0, 40.0]:
        slc = Slice(registrationName=f"wd000_velocity_mag_slice_z{int(z)}m", Input=calc)
        slc.SliceType = "Plane"
        slc.SliceType.Origin = [0.0, 0.0, z]
        slc.SliceType.Normal = [0.0, 0.0, 1.0]
        slc.UpdatePipeline()

    for wd in WIND_DIRS[1:]:
        src = LegacyVTKReader(
            registrationName=f"wd{wd:03d}_medium4m_10k_u_final_hidden",
            FileNames=[str(VTK_FILES[wd])],
        )
        src.UpdatePipeline()

    # No RenderView is created here. The Windows headless OpenGL path on this machine is unreliable
    # without OSMesa, but ParaView can still save a data-pipeline state for manual GUI review.
    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
