# No Pre-Compilation Required — Install & Run

## FluidX3D Pre-Compilation Mechanism

CityLBM embeds a **pre-compiled FluidX3D.exe** solver inside the `.gha` file.

### User Experience
- Install plugin → drag components → click Run → get results
- **No C++ compiler, CUDA Toolkit, or Visual Studio installation needed**

### How It Works

```
CityLBM.gha (2.5 MB)
  ├── CityLBM plugin code
  ├── Newtonsoft.Json (merged via ILRepack)
  ├── NLog (merged via ILRepack)
  ├── Icon resources (22 PNGs)
  ├── Validation files (AIJ Case A)
  └── FluidX3D.exe ← pre-compiled GPU solver
```

On first run:
1. Plugin automatically extracts `FluidX3D.exe` to `%APPDATA%\CityLBM\`
2. Generates `grid_config.txt` from Grasshopper grid parameters
3. Exports building geometry as `buildings.stl`
4. Invokes `FluidX3D.exe` in headless mode (pure GPU compute, no window)
5. Reads VTK output files back into Grasshopper for visualization

### Comparison: Traditional CFD vs. CityLBM

| | Traditional CFD | CityLBM |
|---|---|---|
| Install steps | Install VS + CUDA + compile | Copy 1 file |
| Solver config | Manually edit C++ headers | Grasshopper parameter panel |
| Recompilation | Every grid change | Never (runtime config) |
| Learning curve | C++ / CMake knowledge | Grasshopper basics |

### Modifying the Solver (Advanced)

For advanced users who need to modify FluidX3D algorithms:
1. Edit `FluidX3D/src/setup.cpp` and `defines.hpp`
2. Compile new `FluidX3D.exe` with Make or Visual Studio
3. Replace `src/Resources/FluidX3D/FluidX3D.exe`
4. Rebuild CityLBM.gha via patcher

For 99% of use cases, the default pre-compiled solver works perfectly.