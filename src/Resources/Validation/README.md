# AIJ Case A Validation — CityLBM v0.2.1

## Overview

AIJ Case A is the isolated building benchmark from the Architectural Institute of Japan (AIJ)
CFD Guidebook. This validation uses **real wind tunnel data** from Zenodo to compare
CityLBM simulation results against experimental measurements.

**Experimental data source:** Zenodo [10.5281/zenodo.15430018](https://zenodo.org/records/15430018) (CC BY 4.0)
Tominaga, Kikumoto, Okaze et al. — AIJ UWE Benchmark Dataset, Case I (CubeC)

## Quick Start

### Option A: One-Click .gh Generator
```
Double-click: create_casea_gh.bat
```
This launches Rhino, creates a complete `.gh` definition with all components pre-wired,
then closes automatically. Open the resulting `.gh` file — all components are connected.

### Option B: Manual 2-Component Setup
1. Add **GhPython** component → paste `AIJ_CaseA_OneClick.py`
2. Set outputs: `a=Mesh`, `b=Text`, `c=Curve`, `d=Point`
3. Connect to CityLBM: `Create Scene → Add Buildings → Grid Generator → Run Simulation`
4. Add second **GhPython** → paste `AIJ_CaseA_PostProcess.py`
5. Connect `Run Simulation` Case Dir → PostProcess `case_dir` input

## AIJ Case A Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Building | 0.10×0.10×0.10 m | Cube (1:1:1) |
| U_H | 1.7 m/s | Reference velocity at z=H |
| Wind direction | +X | Perpendicular to windward face |
| Cell size | 0.005 m | H/20 |
| Time steps | 10,000 | Statistical convergence |
| LES | Smagorinsky Cs=0.12 | Improves wake accuracy |

## Measurement Profiles

8 vertical profiles along the centerline (y=0) at:
x/H = -1.5, -0.5, 0.0, +0.65, +1.0, +2.0, +3.0, +5.0

Each profile samples velocity at 8 heights (z = 0.015 to 0.50 m).
Total: 64 experimental measurement points from wind tunnel LDA.

## Quality Assessment

| Avg Error | Grade |
|-----------|-------|
| < 15% | EXCELLENT |
| 15-25% | GOOD (typical LBM) |
| 25-35% | ACCEPTABLE |
| > 35% | NEEDS IMPROVEMENT |

## Files

| File | Purpose |
|------|---------|
| `AIJ_CaseA_OneClick.py` | Setup: cube geometry + Zenodo data + profiles |
| `AIJ_CaseA_PostProcess.py` | PostProcess: VTK reader + trilinear probe + error stats |
| `create_aij_gh.py` | Rhino Python: generates complete .gh definition |
| `create_casea_gh.bat` | One-click .gh generator |
| `AIJ_CaseA_Legacy.gh` | Legacy manual definition (reference only) |
| `zenodo_data/` | Raw Zenodo wind tunnel data (AF, RS-w, RS-c CSV) |

## References

- AIJ CFD Guidebook: https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm
- Zenodo dataset: https://zenodo.org/records/15430018
- CityLBM: https://github.com/ShiyuMiao/CityLBM