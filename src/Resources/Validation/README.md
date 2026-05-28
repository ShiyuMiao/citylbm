# AIJ Case A Validation — CityLBM v0.2.1

AIJ (Architectural Institute of Japan) CFD Guidebook Case A:
isolated building wind tunnel benchmark.

## One-Click Setup (Recommended)

### Option 1: Generate .gh file automatically
```batch
# Double-click this file:
create_casea_gh.bat
```
This launches Rhino, creates `AIJ_CaseA_OneClick.gh` with all components pre-wired,
then closes. Open the resulting `.gh` file in Grasshopper → hit Run.

### Option 2: Manual 2-component setup
1. Open Grasshopper, add **GhPython** component
2. Paste `AIJ_CaseA_OneClick.py` contents
3. Set output types: `a=Mesh`, `b=Text`, `c=Curve`, `d=Point`
4. Connect outputs to CityLBM components:
   - `a` (Mesh) → **Add Buildings** (B input)
   - **Create Scene** → **Add Buildings** → **Grid Generator** → **Run Simulation**
5. Run Simulation in **Mode 3** (async background)
6. Add a **second** GhPython, paste `AIJ_CaseA_PostProcess.py`
7. Connect **Run Simulation** "Case Dir" → GhPython `case_dir` input
8. Click Run → comparison report + visualization

## AIJ Case A Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Building (H:B:D) | 0.2 : 0.1 : 0.1 m | 2:1:1 ratio |
| Wind speed U_H | 5.0 m/s | Uniform inflow |
| Wind direction | +X | Perpendicular to D face |
| Cell size | 0.01 m | H/20 = 20 cells/bldg-height |
| Time steps | 10,000 | Statistical convergence |
| Save interval | 500 | VTK output |
| LES | Smagorinsky (Cs=0.12) | Improves wake accuracy |
| Domain extension | 3.0 | Satisfies AIJ domain reqs |

## Measurement Profiles (9 vertical lines, y=0 plane)

| x/H | x (m) | Description | Expected U/U_H |
|-----|-------|-------------|----------------|
| -1.5 | -0.30 | Upstream far-field | 0.95 ~ 1.02 |
| -0.5 | -0.10 | Windward deceleration | 0.02 ~ 0.32 |
| 0.0 | 0.00 | Above building center | -0.05 ~ 0.10 |
| +0.5 | 0.10 | Leeward recirculation | -0.15 ~ 0.55 |
| +1.0 | 0.20 | Near-wake recovery | -0.08 ~ 0.60 |
| +2.0 | 0.40 | Mid-wake recovery | 0.05 ~ 0.65 |
| +3.0 | 0.60 | Mid-far wake | 0.15 ~ 0.70 |
| +4.0 | 0.80 | Far wake | 0.25 ~ 0.75 |
| +5.5 | 1.10 | Wake end | 0.38 ~ 0.85 |

## Quality Assessment

| Avg Error | Grade | Notes |
|-----------|-------|-------|
| < 10% | EXCELLENT | Best-case with ABL profile |
| 10-20% | GOOD | Typical for uniform inflow LBM |
| 20-30% | ACCEPTABLE | Without ABL profile |
| > 30% | NEEDS IMPROVEMENT | Check setup |

## Files

| File | Purpose |
|------|---------|
| `AIJ_CaseA_OneClick.py` | GhPython Setup: geometry + config + profiles |
| `AIJ_CaseA_PostProcess.py` | GhPython PostProcess: VTK reader + comparison |
| `create_aij_gh.py` | Rhino Python: generates complete .gh definition |
| `create_casea_gh.bat` | One-click .gh generator (run this!) |
| `AIJ_CaseA_OneClick.gh` | Output: complete Grasshopper definition |
| `AIJ_CaseA_Legacy.gh` | Legacy manual definition |

## References

- AIJ CFD Guidebook: https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm
- Experimental data: https://zenodo.org/records/15430019
- CityLBM: https://github.com/ShiyuMiao/CityLBM