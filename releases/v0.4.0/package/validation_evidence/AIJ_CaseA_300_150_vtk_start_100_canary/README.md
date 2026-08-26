# AIJ Case A VTK Save-Start Canary

This folder records the short native FluidX3D canary used to verify CityLBM v0.4.0 VTK output scheduling after adding `VTK Save Start`.

Run conditions:

- Case: `CaseA`
- Wind direction: `W`
- Time steps: `300`
- VTK save interval: `150`
- VTK save start: `100`
- Expected source steps: `[100, 250, 300]`
- Actual VTK files: `u-000000100.vtk`, `u-000000250.vtk`, `u-000000300.vtk`
- Gate: `native_short_canary_gate=pass`

The VTK files are not packaged because each file is about 294 MB. The manifests record their names, sizes, source time steps and SHA256 hashes.

This is a scheduling and runtime-output integrity check only. It is not publication-grade AIJ accuracy validation.
