from pathlib import Path

from paraview.simple import *


ROOT = Path.cwd()
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE / "paraview"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATE = OUT_DIR / "tum2twin_core_prism_dx2m_timesampled_8dir_vtk_review.pvsm"
COLLISION_STL = ROOT / "cfd_ready" / "core_photogrammetry_extent_prism_collision_z0.stl"
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
SLICE_HEIGHTS = [2.0, 10.0, 20.0, 40.0]


def main():
    ResetSession()

    collision = STLReader(
        registrationName="core_prism_collision_z0",
        FileNames=[str(COLLISION_STL)],
    )
    collision.UpdatePipeline()

    for wind_deg in WIND_DIRS:
        prefix = f"matrix_core_prism_avg_wd{wind_deg:03d}_dx2m_spin6k_s3"
        src = LegacyVTKReader(
            registrationName=f"wd{wind_deg:03d}_sample2_velocity_vtk",
            FileNames=[str(CASE / "output" / f"{prefix}_u_sample_2u-000012000.vtk")],
        )
        src.UpdatePipeline()

        calc = Calculator(registrationName=f"wd{wind_deg:03d}_VR_mag", Input=src)
        calc.AttributeType = "Point Data"
        calc.ResultArrayName = "VR"
        calc.Function = "mag(data)/5.0"
        calc.UpdatePipeline()

        for height in SLICE_HEIGHTS:
            slc = Slice(
                registrationName=f"wd{wind_deg:03d}_VR_slice_z{int(height)}m",
                Input=calc,
            )
            slc.SliceType = "Plane"
            slc.SliceType.Origin = [0.0, 0.0, height]
            slc.SliceType.Normal = [0.0, 0.0, 1.0]
            slc.UpdatePipeline()

    SaveState(str(STATE))
    print(str(STATE))


if __name__ == "__main__":
    main()
