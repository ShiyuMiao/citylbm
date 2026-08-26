# AIJ Case A Official Validation — CityLBM v0.2.1

## Source

This validation uses the **official AIJ CFD Guidebook Case A** wind tunnel data
(Architectural Institute of Japan, "Guidebook for CFD Wind Environment around Buildings", 2020).

The experimental data was extracted from the official AIJ benchmark Excel file
(`CaseA(1_1_2).xls`) containing LDA measurements at 26+ probe points in the
vertical centerline plane (y=0).

## Building Geometry (AIJ Official)

| Parameter | Symbol | Value | Formula |
|-----------|--------|-------|---------|
| Scale unit | b | **0.08 m** | — |
| Building height | H | **0.16 m** | H = 2b |
| Building width | B | **0.08 m** | B = b |
| Building depth | D | **0.08 m** | D = b |
| Aspect ratio | H:B:D | **2:1:1** | AIJ standard |

**Coordinate system:**
- X: streamwise (+X = wind direction)
- Y: spanwise (building width)
- Z: vertical (building height, base at Z=0)
- Building centroid at (0, 0, H/2)
- Building footprint: X=[-D/2, D/2], Y=[-B/2, B/2], Z=[0, H]

## Wind Conditions (AIJ Official)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Inflow type | Power-law ABL | U(z) = U_H * (z/H)^alpha |
| alpha | 0.25 | Suburban terrain (AIJ Category III) |
| U_H | ~4.5 m/s | Reference velocity at z=H=0.16m |
| Wind direction | +X | Perpendicular to D face |
| Turbulence | Included in data | sigma_u, sigma_v, sigma_w, k |

## Grid Requirements (AIJ Recommended)

| Parameter | Value |
|-----------|-------|
| Cell size | 0.008 m (H/20) |
| Cells per building height | 20 |
| Upstream domain | >= 5H = 0.80 m |
| Downstream domain | >= 15H = 2.40 m |
| Lateral domain | >= 5H = 0.80 m (each side) |
| Vertical domain | >= 5H = 0.80 m above building |
| Blockage ratio | < 3% |

## Measurement Points (Vertical Section y=0)

26 probe points at the centerline plane, spanning:
- Streamwise: x/b = -0.75 to +0.50
- Vertical: z/b = 0.125 to 3.500

| x/b | Count | Region |
|-----|-------|--------|
| -0.75 | 10 | Upstream near-field approach flow |
| -0.50 | 4 | Windward edge shear layer |
| -0.25 | 4 | Above building front (separation) |
| 0.00 | 4 | Above building center (reattachment) |
| 0.50 | 4 | Leeward edge (recirculation zone) |

## CityLBM Component Settings

| Component | Parameter | Value |
|-----------|-----------|-------|
| **Center Box** | X domain | (-0.04, +0.04) |
| | Y domain | (-0.04, +0.04) |
| | Z domain | (0, +0.16) |
| **Mesh Brep** | — | Convert Box to Mesh |
| **Create Scene** | Wind Speed V | 4.5 |
| | Wind Direction D | (1, 0, 0) |
| | Domain Extension | 2.0 |
| **Add Buildings** | S (Scene) | <- Create Scene |
| | B (Buildings) | <- Mesh Brep |
| **Grid Generator** | Cell Size | 0.008 |
| **Run Simulation** | Mode | 3 (async) |
| | Time Steps | 10000 |
| | Save Interval | 500 |

## Expected Results

Based on AIJ benchmark quality criteria for LBM simulations:

| Avg Error | Grade | Expected for |
|-----------|-------|-------------|
| < 20% | EXCELLENT | High-resolution grid + ABL profile |
| 20-30% | GOOD | Uniform inflow LBM (CityLBM default) |
| 30-45% | ACCEPTABLE | Coarse grid or simple BCs |
| > 45% | NEEDS REVIEW | Check domain size / grid / BC |

**Key flow features to verify:**
1. Upstream (x/b=-0.75): U increases with z, approaching ~5.4 m/s at z/b=3.5
2. Windward edge (x/b=-0.5): strong vertical gradient at z/b~2 (building top)
3. Above building (x/b=-0.25 to 0): flow acceleration + separation bubble
4. Leeward (x/b=0.5): wake recovery begins, lower velocities than upstream

## Quick Start

### Generate the .gh file
```
Double-click: create_casea_official.bat
```
Or run manually in Rhino:
```
Rhino.exe /nosplash /runscript="_-RunPythonScript (Load create_aij_official_gh.py)"
```

### Open in Grasshopper
1. Open `AIJ_CaseA_Official.gh` in Grasshopper
2. Verify the native GH Box dimensions (X/Y domain, Z height)
3. Set Create Scene parameters (V=4.5, D=(1,0,0), Extension=2.0)
4. Set Grid Generator cell size = 0.008
5. Set Run Simulation: Mode=3, Steps=10000, Save=500
6. Click Run
7. Wait for FluidX3D compilation (~30-60s first time) + simulation
8. GhPython PostProcess automatically reads VTK and generates comparison report

## Files

| File | Purpose |
|------|---------|
| `create_aij_official_gh.py` | Rhino Python: generates .gh with native GH Box + CityLBM |
| `AIJ_CaseA_Official_PostProcess.py` | GhPython: VTK reader + AIJ data comparison |
| `AIJ_CaseA_Official.gh` | Output: complete Grasshopper definition |
| `create_casea_official.bat` | One-click .gh generator batch file |

## References

- AIJ (2020). *Guidebook for CFD Wind Environment around Buildings*. Architectural Institute of Japan.
- Tominaga et al. (2008). "AIJ guidelines for practical applications of CFD to pedestrian wind environment around buildings." *Journal of Wind Engineering and Industrial Aerodynamics*, 96(10-11), 1749-1761.
- Zenodo supplementary data: https://zenodo.org/records/15430018