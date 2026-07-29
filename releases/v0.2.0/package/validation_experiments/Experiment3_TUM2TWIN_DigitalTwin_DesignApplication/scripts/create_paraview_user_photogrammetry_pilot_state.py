from pathlib import Path
from paraview.simple import *


CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE / "paraview"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATE = OUT_DIR / "tum2twin_user_photogrammetry_dx2m_pilot_audit_pipeline.pvsm"
LABEL = "user_photo_wd000_dx2m_2k"
U_VTK = CASE / "output" / f"matrix_{LABEL}_u_finalu-000002000.vtk"
FLAGS_VTK = CASE / "output" / f"matrix_{LABEL}_flags_finalflags-000002000.vtk"
VOXELIZED_STL = CASE / "output" / f"matrix_{LABEL}_building_collision_voxelized_reference.stl"


def main():
    ResetSession()
    u = LegacyVTKReader(registrationName="user_photo_u_final_dx2m_2k", FileNames=[str(U_VTK)])
    u.UpdatePipeline()
    flags = LegacyVTKReader(registrationName="user_photo_flags_final_dx2m_2k", FileNames=[str(FLAGS_VTK)])
    flags.UpdatePipeline()

    calc = Calculator(registrationName="user_photo_velocity_magnitude", Input=u)
    calc.AttributeType = "Point Data"
    calc.ResultArrayName = "velocity_mag"
    calc.Function = "mag(data)"
    calc.UpdatePipeline()

    for z in [2.0, 4.0, 10.0, 20.0, 40.0]:
        slc = Slice(registrationName=f"user_photo_velocity_mag_slice_z{int(z)}m", Input=calc)
        slc.SliceType = "Plane"
        slc.SliceType.Origin = [0.0, 0.0, z]
        slc.SliceType.Normal = [0.0, 0.0, 1.0]
        slc.UpdatePipeline()

    if VOXELIZED_STL.exists():
        voxel = STLReader(registrationName="user_photo_voxelized_reference_stl", FileNames=[str(VOXELIZED_STL)])
        voxel.UpdatePipeline()

    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
