# AIJ Case E Example

This folder contains the CityLBM v0.2.0 validation-oriented setup for AIJ Case E, focusing on `ac + N`.

## Files

- `grasshopper/AIJ_CaseE_ac_N_validation.gh`: Grasshopper workflow.
- `official_data/AF_caseE.csv`: inlet wind profile, first numeric columns are `z(m), U(m/s)`.
- `official_data/RS_caseE.csv`: measurement-point reference data.
- `official_data/BD_caseE.stl`: Niigata building geometry.
- `official_data/MP_caseE.png`: measurement-point reference image.
- `../../screenshots/AIJ_CaseE_Rhino_GH_proof.png`: Rhino/GH proof screenshot.

## Input Conditions

- Case: `ac`
- Wind direction: `N`
- Direction vector convention: from north to south, `(0, -1, 0)`
- Geometry scale: STL is 1:250 model scale; scale by 250 in Rhino/GH for real-scale comparison.
- Reference height: `15.9 m`
- Pedestrian validation height: `2 m`
- First smoke test: `dx = 5 m`, `steps = 2000`, `save interval = 500 or 1000`
- Formal validation run: `dx = 2-3 m`, `steps = 10000+`, depending on hardware

## Data Source

Official AIJ Case E Niigata data source:

https://zenodo.org/records/15429018

Large VTK outputs are not included in this Food4Rhino package.
