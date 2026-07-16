# Changelog

## v0.2.0 - Food4Rhino release

- Prepared a clean Food4Rhino user package for Rhino 7/8 Grasshopper.
- Set plugin and assembly version to `0.2.0.0`.
- Kept 18 stable CityLBM components for scene setup, simulation case generation, and VTK result visualization.
- Added `CustomTable` inlet wind profile support for measured CSV profiles.
- Corrected custom-profile height sampling with domain-origin offset.
- Kept FluidX3D as an external dependency instead of bundling solver source or executable files.
- Added AIJ Case A and AIJ Case E example folders.
- Added `validation_experiments/` with Case A and Case E Rhino files, Grasshopper workflows, Excel result workbooks, screenshots, metadata, and SHA256 checksums.
- Added Food4Rhino/Yak `manifest.yml`.
- Excluded internal development files, v0.5.0 experiments, debug builds, backup plugins, and large VTK output files.

## Known limitations

- Full simulation runs require a local FluidX3D source tree and build environment.
- The `Lawson Comfort` source exists in the development tree but is not compiled into the verified v0.2.0 package binary; validation workflows treat it as optional until the binary is rebuilt with that component.
- Rhino 7 was available for local build targeting; Rhino 8 compatibility is the release target but should be checked on a Rhino 8 machine before public submission.
- The examples are provided as validation-oriented workflows; numerical results depend on the user's FluidX3D build, GPU/CPU environment, grid size, and timestep settings.
