from pathlib import Path

from paraview.simple import *


ROOT = Path.cwd()
CASE = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

VTK = CASE / "output" / "matrix_core_prism_avg_wd000_dx2m_spin6k_s3_u_sample_2u-000012000.vtk"
STL = ROOT / "cfd_ready" / "core_photogrammetry_extent_prism_collision_z0.stl"
OUT = FIG / "paraview_core_wd000_vr_slice_z2m_quicklook.png"


def main():
    ResetSession()
    velocity = LegacyVTKReader(registrationName="wd000_velocity", FileNames=[str(VTK)])
    velocity.UpdatePipeline()
    calc = Calculator(registrationName="wd000_VR", Input=velocity)
    calc.AttributeType = "Point Data"
    calc.ResultArrayName = "VR"
    calc.Function = "mag(data)/5.0"
    calc.UpdatePipeline()
    slc = Slice(registrationName="wd000_VR_slice_z2m", Input=calc)
    slc.SliceType = "Plane"
    slc.SliceType.Origin = [0.0, 0.0, 2.0]
    slc.SliceType.Normal = [0.0, 0.0, 1.0]
    slc.UpdatePipeline()

    collision = STLReader(registrationName="core_collision", FileNames=[str(STL)])
    collision.UpdatePipeline()

    render_view = CreateView("RenderView")
    render_view.ViewSize = [1800, 1400]
    render_view.Background = [1.0, 1.0, 1.0]
    layout = CreateLayout(name="Quicklook")
    layout.AssignView(0, render_view)

    slc_display = Show(slc, render_view)
    slc_display.SetRepresentationType("Surface")
    ColorBy(slc_display, ("POINTS", "VR"))
    slc_display.RescaleTransferFunctionToDataRange(True)
    lut = GetColorTransferFunction("VR")
    lut.ApplyPreset("Viridis", True)
    bar = GetScalarBar(lut, render_view)
    bar.Title = "VR"
    bar.ComponentTitle = ""
    bar.Visibility = 1

    col_display = Show(collision, render_view)
    col_display.SetRepresentationType("Surface With Edges")
    col_display.DiffuseColor = [0.25, 0.25, 0.25]
    col_display.Opacity = 0.25

    bounds = slc.GetDataInformation().GetBounds()
    center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, 2.0]
    width = max(bounds[1] - bounds[0], bounds[3] - bounds[2])
    render_view.CameraPosition = [center[0], center[1], center[2] + 1.7 * width]
    render_view.CameraFocalPoint = center
    render_view.CameraViewUp = [0.0, 1.0, 0.0]
    ResetCamera(render_view)
    SaveScreenshot(str(OUT), render_view, ImageResolution=[1800, 1400], OverrideColorPalette="WhiteBackground")
    print(str(OUT))


if __name__ == "__main__":
    main()
