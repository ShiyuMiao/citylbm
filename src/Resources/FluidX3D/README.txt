FluidX3D.source.zip
====================
Place the FluidX3D source code as a ZIP archive here.
This file will be embedded into CityLBM.gha as an EmbeddedResource.

To create:
  1. Download FluidX3D from https://github.com/ProjectPhysX/FluidX3D
  2. Zip the entire FluidX3D directory (including src/, FluidX3D.sln, etc.)
  3. Name it "FluidX3D.source.zip"
  4. Place it in this directory

The zip should contain at minimum:
  - FluidX3D.sln (or Makefile / CMakeLists.txt)
  - src/
  - src/setup.cpp
  - src/defines.hpp
  - src/lbm.hpp
  - (all other FluidX3D source files)

v0.3.0 — CityLBM Bundled Solver