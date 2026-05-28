# CityLBM v0.2.1

**GPU-accelerated Urban Wind Environment Simulation for Grasshopper**

CityLBM is a single-file Grasshopper plugin that brings high-performance urban wind simulation directly into Rhino. Powered by the Lattice Boltzmann Method (LBM) and GPU acceleration via FluidX3D, it enables architects and urban planners to analyze wind comfort, pedestrian-level wind, and building aerodynamics without leaving the design environment.

## Features

- **One-Click Installation** — Single `.gha` file, no dependencies, no C++ compiler required
- **GPU-Accelerated Simulation** — Leverages OpenCL for fast LBM computation
- **20 Grasshopper Components** organized into 3 intuitive groups:
  - `1 | Scene` — Scene creation, building import, domain setup, wind conditions
  - `2 | Simulation` — Grid generation and solver execution
  - `3 | Results` — VTK reading, velocity visualization, slices, streamlines, comfort maps
- **AIJ-Compliant Domain Setup** — Automatic calculation domain per AIJ guidelines
- **Wind Profile Support** — Uniform, Power Law (GB 50009), and Logarithmic profiles
- **LES Turbulence Model** — Smagorinsky subgrid-scale model for high-Re flows
- **Lawson Comfort Criteria** — Pedestrian wind comfort assessment

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 (64-bit) |
| Rhino | Rhino 6 SR18+ or Rhino 7 |
| Grasshopper | Built-in |
| GPU | OpenCL 1.2+ compatible (NVIDIA/AMD/Intel) |
| Disk | ~3 MB for plugin |

## Quick Start

1. **Install**: Copy `CityLBM.gha` to `%APPDATA%\Grasshopper\Libraries\`
2. **Launch**: Open Rhino → type `Grasshopper`
3. **Create Scene**: Drag `Create Scene` from `CityLBM → 1 | Scene`
4. **Add Buildings**: Connect building meshes via `Add Buildings`
5. **Setup Domain**: Use `Domain Setup` for AIJ-compliant domain
6. **Generate Grid**: Connect to `Generate Grid`
7. **Run Simulation**: Connect to `Run Simulation` (Mode 3 for background execution)
8. **Visualize**: Use Results tab components for analysis

## How It Works (No Compiler Needed!)

CityLBM bundles a **pre-compiled FluidX3D solver** inside the `.gha` file. On first run:
1. FluidX3D.exe is extracted to `%APPDATA%\CityLBM\`
2. Grid configuration is written at runtime via `grid_config.txt`
3. Buildings geometry is exported as STL
4. FluidX3D runs headlessly on your GPU
5. VTK results are read back into Grasshopper

**You never need to install Visual Studio, CUDA Toolkit, or compile any C++ code.**

## License

This project is provided for academic and research purposes. Contact the author for commercial use.

## Author

**Shiyu Miao**  
Dalian University of Technology  
Email: miaoshiyu@mail.dlut.edu.cn