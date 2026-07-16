# CityLBM v0.2.0

CityLBM is a Grasshopper plugin for urban wind environment simulation. It builds a Rhino/Grasshopper workflow around FluidX3D, using the Lattice Boltzmann Method (LBM) for wind-field case generation, execution, and VTK result visualization.

This v0.2.0 package is the stable Food4Rhino release line. It is intentionally smaller than the internal development folder and does not include v0.5.0 code, large VTK outputs, debug files, or temporary automation scripts.

## Requirements

- Windows 10/11
- Rhino 7 or Rhino 8 with Grasshopper
- .NET Framework 4.8
- FluidX3D source tree as an external dependency for full simulation runs

CityLBM does not bundle FluidX3D in this release. In the `Run Simulation` component, set `FluidX3D Path` to a FluidX3D source root that contains `FluidX3D.sln` or `Makefile` and `src/setup.cpp`.

Users can open the Grasshopper files, inspect the bundled AIJ validation
evidence, and generate case files immediately after installation. Re-running
the solver from Grasshopper requires the local FluidX3D path above.

## Components

CityLBM v0.2.0 contains 18 core Grasshopper components plus the `CityLBM.Lawson.gha` companion component:

- Scene setup: create wind scenes, add buildings, define domains, set wind conditions.
- Simulation: generate Cartesian grids and FluidX3D cases.
- Results: read VTK files, visualize velocity fields, extract slices, streamlines, point probes, and wind-speed grids.
- Comfort: `Lawson Comfort` classifies pedestrian-level wind speeds for Lawson-style comfort and safety checks.

## Basic Workflow

1. Create a `CityLBM` scene.
2. Add Rhino building geometry.
3. Define or confirm the simulation domain.
4. Generate a Cartesian grid.
5. Use `Run Simulation` in `Mode 0` to generate a FluidX3D case.
6. For full runs, provide a valid FluidX3D source path and use the automatic run modes.
7. Read `u-*.vtk` output and extract slices, probes, or wind-speed grids.

## Accuracy-Oriented Features

- `CustomTable` wind profile input through CSV files with `z(m), U(m/s)`.
- Domain-origin metadata for mapping VTK coordinates back to Rhino physical coordinates.
- AIJ Case A and Case E example folders for validation-oriented workflows.
- Probe and Excel-ready result extraction support.

## Examples

- `examples/AIJ_CaseA`: isolated-building validation workflow and proof screenshot.
- `examples/AIJ_CaseE`: Niigata urban district `ac + N` validation inputs and Grasshopper workflow.
- `validation_experiments`: packaged Case A and Case E validation evidence with Rhino files, Grasshopper files, Excel results, screenshots, and checksums.

Large VTK result files are intentionally excluded from this Food4Rhino package.

## References

- FluidX3D: https://github.com/ProjectPhysX/FluidX3D
- AIJ CFD Guidebook: https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm
- AIJ Case E Niigata dataset: https://zenodo.org/records/15429018

## License

CityLBM is distributed under the MIT License. FluidX3D is an external dependency and remains under its own license.
