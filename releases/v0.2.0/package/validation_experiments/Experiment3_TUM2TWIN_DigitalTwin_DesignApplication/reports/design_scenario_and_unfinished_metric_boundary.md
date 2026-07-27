# Design Scenario and Unfinished Metric Boundary

evidence_type: newly_run + blocked

This archive contains an executed baseline screening case (`S0`) and a documented but not executed design-intervention placeholder (`S1`). The file exists to prevent the manuscript from overstating unrun scenario comparisons.

Machine-readable tables:

- `manifests/design_scenario_manifest.csv`
- `manifests/gcbte_status_table.csv`

## Scenario Status

| Scenario | Status | Paper use |
|---|---|---|
| `S0 baseline` | executed FluidX3D dx=2 m, eight directions, three time samples after spin-up | report wind-screening and morphology-response interpretation |
| `S1 ventilation-relief candidate` | not simulated | protocol placeholder only; no improvement value or figure should be reported |

Until `S1` is geometrically committed, voxelized, simulated, and post-processed with the same metrics as `S0`, this experiment should be written as **real digital-twin wind screening and morphology interpretation**, not as a completed intervention-comparison study.

## GCBTE Status

The 3DGS/photogrammetry-to-collision transfer metrics are defined but not numerically computed because no independent 3DGS-derived building collision extraction exists in this archive. The current evidence only supports a qualitative counterexample: the raw photogrammetry STL is visually consistent with the campus block but is not accepted as a robust closed collision boundary.

## Pollutant and Comfort Boundary

Pollutant dispersion has not been run. Lawson/NEN/AIJ-style comfort and safety classification also remains blocked because the archive lacks measured wind statistics or a formal annual exceedance-probability wind rose. Open-Meteo is used only as a climate proxy for directional weighting and should not be written as site validation.
