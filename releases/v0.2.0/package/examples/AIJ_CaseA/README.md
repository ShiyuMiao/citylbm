# AIJ Case A Example

This folder contains a validation-oriented Grasshopper example for AIJ Case A.

## Files

- `grasshopper/AIJ_CaseA_validation.gh`: Grasshopper workflow.
- `geometry/buildings.stl`: building geometry used by the example.
- `results/AIJ_CaseA_validation_summary.xlsx`: pre-existing postprocessed summary from the internal validation folder.
- `../../screenshots/AIJ_CaseA_Rhino_proof.png`: Rhino proof screenshot.

## Recommended First Run

1. Open the GH file in Rhino 7/8 Grasshopper.
2. Confirm the component chain is visible.
3. Use `Run Simulation` with `Mode = 0`.
4. Confirm the generated case directory contains:
   - `setup.cpp`
   - `defines.hpp`
   - `buildings.stl`
   - `domain_origin.json`

Full solver execution requires a valid external FluidX3D source path.
