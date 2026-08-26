# Installation Guide

## Method 1: One-Click Installer (Recommended)

Run `install.bat` as administrator:
```
install.bat
```

## Method 2: Manual Installation

1. **Locate Grasshopper Libraries folder**:
   - Press `Win + R`, type `%APPDATA%\Grasshopper\Libraries`, press Enter
   - If the folder doesn't exist, create it

2. **Copy the plugin**:
   - Copy `bin\CityLBM.gha` into the Libraries folder

3. **Restart Rhino and Grasshopper**:
   - Close Rhino completely
   - Reopen Rhino
   - Type `Grasshopper` in the command line

4. **Verify installation**:
   - In Grasshopper, you should see a new `CityLBM` tab with three sub-tabs:
     - `1 | Scene` (7 components)
     - `2 | Simulation` (2 components)
     - `3 | Results` (11 components)

## Uninstalling

Delete `CityLBM.gha` from `%APPDATA%\Grasshopper\Libraries\` and restart Rhino.

## Troubleshooting

### Plugin doesn't appear in Grasshopper
- Ensure Rhino is **completely closed** before copying the .gha file
- Check that the file is in the correct folder: `%APPDATA%\Grasshopper\Libraries\`
- Right-click the .gha file → Properties → check "Unblock" if present
- Restart Rhino after installation

### "FluidX3D.exe not found" or solver path error
- v0.4.0 installs the Grasshopper plugin and can generate FluidX3D case files directly.
- Real simulation runs still require a valid local FluidX3D source tree or executable environment.
- In `Run Simulation`, set the FluidX3D path to your local solver location before running Mode 1/2/3.
- If you only need to check the Grasshopper workflow, use Mode 0 to generate the case without launching the solver.

### Simulation fails or is very slow
- Ensure your GPU supports OpenCL 1.2+
- Update GPU drivers to the latest version
- Reduce grid resolution (increase cell size dx)
- Close other GPU-intensive applications

### Component shows as orange/error
- Check that all required inputs are connected
- Hover over the component to see error details
- Ensure building meshes are closed and manifold
