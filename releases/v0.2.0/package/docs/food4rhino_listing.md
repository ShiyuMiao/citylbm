# Food4Rhino Listing Draft - CityLBM v0.2.0

## Title

CityLBM - Urban Wind Simulation for Grasshopper

## Short Description

Grasshopper plugin for urban wind environment simulation. Generates FluidX3D LBM cases from Rhino geometry and provides VTK visualization, probes, slices, and AIJ validation examples.

## Long Description

CityLBM brings urban wind environment simulation into Rhino/Grasshopper. It helps users create wind scenes, add building geometry, define simulation domains, generate FluidX3D case files, and visualize VTK velocity results directly in the Rhino workflow.

CityLBM v0.2.0 is a stable Food4Rhino-oriented release. It focuses on a clean, repeatable workflow rather than bundling internal development experiments. The package includes 18 Grasshopper components for scene setup, case generation, and result postprocessing.

### Key Features

- Rhino/Grasshopper workflow for urban wind environment simulation.
- FluidX3D LBM case generation from Rhino building geometry.
- Uniform, power-law, logarithmic, and measured CSV wind profiles.
- Domain-origin metadata for physical VTK coordinate mapping.
- VTK result reading, velocity visualization, slices, streamlines, probes, and wind-speed grids.
- AIJ Case A and Case E example workflows.
- Packaged `validation_experiments` folder with Rhino, Grasshopper, Excel, screenshot, and checksum evidence for AIJ Case A and Case E.

### Requirements

- Windows 10/11
- Rhino 7 or Rhino 8
- Grasshopper
- .NET Framework 4.8
- External FluidX3D source tree for full solver execution

### Installation

Copy `CityLBM.gha`, `Newtonsoft.Json.dll`, and `NLog.dll` to `%APPDATA%\Grasshopper\Libraries\`, then restart Rhino and Grasshopper. If Windows blocks downloaded files, unblock them in file properties.

### FluidX3D Dependency

CityLBM v0.2.0 does not bundle FluidX3D. For full simulations, the `Run Simulation` component needs a FluidX3D source root containing `FluidX3D.sln` or `Makefile` and `src/setup.cpp`. Users can still generate case files with `Mode = 0` without compiling FluidX3D.

### Validation Examples

The package includes AIJ Case A and AIJ Case E example folders plus a `validation_experiments` evidence folder. Large VTK output files are excluded to keep the upload package small.

### References

- FluidX3D: https://github.com/ProjectPhysX/FluidX3D
- AIJ CFD Guidebook: https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm
- AIJ Case E dataset: https://zenodo.org/records/15429018

### License

MIT License for CityLBM. FluidX3D is an external dependency under its own license.
