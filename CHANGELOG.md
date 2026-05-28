# CityLBM Changelog

## v0.2.1 (Current Release)

### What's New
- **AIJ Case A One-Click Validation**: Run `create_casea_gh.bat` to generate a complete
  Grasshopper definition with all 20 CityLBM components pre-wired for the AIJ Case A
  benchmark. Includes two GhPython scripts (Setup + PostProcess) with automatic
  building geometry, 9 measurement profiles, 90-point experimental comparison,
  and quality assessment report.
- **5 New/Replaced Icons**: AbsoluteDomain, Isosurface, Lawson, VerticalSlice, and
  validation icons regenerated at 200x200 RGBA in blue (#1A6FC4) matching IconPark style.
  All 22 icons are now unique (duplicate validation.png fixed).
- **FluidX3D Bundled**: Pre-compiled FluidX3D.exe (477 KB) embedded in the .gha.
  No C++ compiler or manual FluidX3D installation needed.
- **Tab Organization**: Tabs renamed to `1 | Scene`, `2 | Simulation`, `3 | Results`
  following Eddy3D naming convention to prevent alphabetical reordering.

### Components (20 total)
**1 | Scene (7)**: CreateScene, AddBuildings, SceneInfo, DomainDesigner,
AbsoluteDomain, DomainSetup, WindCondition

**2 | Simulation (2)**: GridGenerator, RunSimulation

**3 | Results (11)**: ReadVTK, VelocityVisualization, SliceVisualization,
VerticalSlice, SimulationStats, VTKCloudVisualization, Probe,
WindSpeedGrid, Streamline, Isosurface, LawsonComfort

### Installation
1. Run `install.bat` (or manually copy `bin\CityLBM.gha` to `%APPDATA%\Grasshopper\Libraries\`)
2. Copy `bin\FluidX3D.exe` to `%APPDATA%\CityLBM\`
3. Restart Rhino + Grasshopper

### Known Limitations
- Requires Rhino 7 + Grasshopper
- FluidX3D requires Windows (uses pre-compiled .exe)
- Uniform inflow used by default (AIJ uses power-law ABL; ~10-15% systematic error)
- First run compiles FluidX3D solver from embedded source (~30-60s, cached afterward)

## v0.2.0
- Initial release with 20 components
- FluidX3D LBM solver integration
- VTK read/write, visualization components
- Basic wind comfort assessment (Lawson criteria)