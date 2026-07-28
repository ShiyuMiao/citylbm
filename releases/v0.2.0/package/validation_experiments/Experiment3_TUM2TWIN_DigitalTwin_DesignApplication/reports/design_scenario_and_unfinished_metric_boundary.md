# Design Scenario and Unfinished Metric Boundary

evidence_type: newly_run + blocked

This archive now contains an executed baseline screening case (`S0`) and an executed S1 design-sensitivity case (`S1_ventilation_relief`). The S1 result should be interpreted as a near-null/negative sensitivity test, not as a successful optimization.

Machine-readable tables:

- `manifests/design_scenario_manifest.csv`
- `manifests/s1_design_intervention_claims.csv`
- `manifests/gcbte_status_table.csv`

## Scenario Status

| Scenario | Status | Paper use |
|---|---|---|
| `S0 baseline` | executed FluidX3D dx=2 m, eight directions, three time samples after spin-up | primary wind-screening and morphology-response interpretation |
| `S1 ventilation-relief` | executed FluidX3D dx=2 m, eight directions, three time samples after spin-up | design-sensitivity comparison; report as near-null/negative outcome |

## S1 Main Result

S1 removes `66` collision cells (`1650.0 m2`, `2.79%` of S0 footprint) along a least-removal east-west relief corridor. At z~2 m, S1 changes equal-weighted mean VR by only `-0.000213` and changes VR<0.2 stagnation ratio by `0.000233`. Newly opened cells remain low-speed, with S1 mean VR `0.002697` and stagnation ratio `1.000`.

## Remaining Blocked Metrics

The 3DGS/photogrammetry-to-collision transfer metrics are still not numerically computed because no independent 3DGS-derived building collision extraction exists in this archive. Pollutant dispersion has not been run. Lawson/NEN/AIJ-style comfort and safety classification also remains blocked because the archive lacks measured wind statistics or a formal annual exceedance-probability wind rose. Open-Meteo is used only as a climate proxy for directional weighting and should not be written as site validation.
