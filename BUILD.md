# Build Guide

## How the Release Binary is Produced

The v0.2.1 release binary (`bin/CityLBM.gha`) is built from v0.2.0 source using the following pipeline:

1. **Build**: `dotnet publish CityLBM.csproj -c Release`
2. **Merge**: ILRepack merges `Newtonsoft.Json.dll` + `NLog.dll` into the DLL
3. **Patch**: Mono.Cecil patches tab name strings (`"Scene"` → `"1 | Scene"`, etc.)
4. **Rename**: `CityLBM.dll` → `CityLBM.gha`

## Why This Process?

The Grasshopper plugin loader is sensitive to how the .NET assembly is structured. After extensive testing, we found:
- `dotnet build` produces assemblies that Grasshopper doesn't fully recognize
- `dotnet publish` + ILRepack matches the working v0.2.0 binary structure
- Tab names must be patched via Cecil to avoid changing component abbreviations

## FluidX3D Pre-Compilation

**Users DO NOT need a C++ compiler.** The FluidX3D solver is pre-compiled into a standalone executable that is embedded as a resource in CityLBM.gha. At runtime:

1. `FluidX3DBundler` extracts `FluidX3D.exe` to `%APPDATA%\CityLBM\`
2. Grid parameters are written to `grid_config.txt`
3. Building geometry is exported as `buildings.stl`
4. `FluidX3D.exe` runs headlessly with GPU acceleration
5. VTK output files are read back into Grasshopper

### Modifying the Solver

If you need to modify FluidX3D (e.g., change grid dimensions, boundary conditions):
1. Edit `src/setup.cpp` and `src/defines.hpp` in the FluidX3D project
2. Compile with `make` or Visual Studio (OpenCL SDK required)
3. Replace `src/Resources/FluidX3D/FluidX3D.exe`
4. Rebuild CityLBM

The default FluidX3D build uses:
- D3Q19 lattice, FP32 precision
- Smagorinsky LES (Cs = 0.12)
- Headless mode (no graphics)
- Grid dimensions read from `grid_config.txt` at runtime

## .csproj Key Settings

```xml
<TargetFramework>net472</TargetFramework>
<CopyLocalLockFileAssemblies>true</CopyLocalLockFileAssemblies>
```

References:
- RhinoCommon.dll (Rhino 6/7 System directory)
- Grasshopper.dll (Rhino 6/7 Plug-ins)
- Newtonsoft.Json 13.0.3
- NLog 5.2.0