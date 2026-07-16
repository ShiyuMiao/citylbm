# CityLBM v0.2.0 Validation Experiments

This folder contains the lightweight validation evidence bundled with the
CityLBM v0.2.0 package. It is organized for thesis screenshots and repeatable
inspection rather than for storing every large raw VTK file.

## Included Cases

### AIJ Case A

- Rhino file: `AIJ_CaseA/rhino/AIJ_CaseA_validation.3dm`
- Grasshopper file: `AIJ_CaseA/grasshopper/AIJ_CaseA_validation.gh`
- Excel result: `AIJ_CaseA/excel/AIJ_CaseA_validation_from_existing_vtk.xlsx`
- Screenshot: `AIJ_CaseA/screenshots/rhino_proof_AIJCASEA.png`
- Case metadata: `AIJ_CaseA/case/domain_origin.json`, `AIJ_CaseA/case/setup.cpp`

The Excel result is generated from the existing CityLBM/FluidX3D VTK validation
run `u-000002000.vtk`. The raw VTK file is intentionally not bundled in this
package to keep the GitHub and user package size manageable.

### AIJ Case E

- Rhino file: `AIJ_CaseE/rhino/AIJCASEE_ac_N_citylbm_no_arrow_vtk_points.3dm`
- Grasshopper file: `AIJ_CaseE/grasshopper/AIJ_CaseE_ac_N_citylbm_full_workflow.gh`
- Excel result: `AIJ_CaseE/excel/AIJCASEE_ac_N_citylbm_measure_points.xlsx`
- Screenshot: `AIJ_CaseE/screenshots/rhino_casee_citylbm_no_arrow_vtk_points.png`
- Case metadata: `AIJ_CaseE/case/domain_origin.json`, `AIJ_CaseE/case/setup.cpp`

The Case E result is based on the CityLBM-generated FluidX3D VTK file
`u-000002000.vtk`, sampled at the official `ac + N` measurement points.
The Rhino view shows the AIJ Case E model with VTK-derived speed samples, not
manual arrows or synthetic placeholder data.

## Current Accuracy Boundary

These files prove the end-to-end workflow:

`Grasshopper setup -> CityLBM/FluidX3D run -> VTK output -> Rhino visualization -> Excel point comparison`

They do not yet represent the final publication-grade accuracy run. The Case E
Excel workbook records the current smoke-run status (`dx=5m`, `2000` steps) and
its error statistics.

## Component Note

The current v0.2.0 package binary exposes 18 Grasshopper components. The
`Lawson Comfort` source exists in the development tree, but the verified
v0.2.0 binary inspected during this cleanup does not contain that compiled
component. The Case E full workflow therefore treats Lawson post-processing as
optional until a rebuilt binary includes it.
