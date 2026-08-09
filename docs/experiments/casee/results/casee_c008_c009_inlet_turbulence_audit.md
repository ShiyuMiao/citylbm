# C008-C011 Inlet Turbulence Sweep Audit

Generated: 2026-08-09T15:13:20.267933+00:00

## Verdict

- Status: `completed_inlet_turbulence_improved_but_negative_r2`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release`
- Formal release allowed: False
- Best candidate: `C011_inlet_k_synthetic_fullplane_s1p50`

## Best Official z=2 m Raw Metric

- MAE: 14.3750643375 pp
- RMSE: 18.41596115408416 pp
- Bias: -4.6872345375 pp
- R2: -0.32680378704255153
- Pearson: 0.2856641275815884
- Delta MAE vs z-center baseline: -6.73634375 pp
- Delta R2 vs z-center baseline: 1.679526670176449
- Delta Pearson vs z-center baseline: 0.16990764609679754
- Delta MAE vs C005: -5.351208612499999 pp
- Delta R2 vs C005: 1.281271353151709
- Delta Pearson vs C005: 0.18634883204252256

## Boundary

C008-C011 are completed official-height raw_trilinear candidate runs using a default-off synthetic full-plane inlet based on AF_caseE k. They improve MAE, R2, and Pearson, but R2 remains negative and the turbulence scale is a diagnostic sweep parameter. Use as inlet-turbulence evidence and software-feedback guidance only; do not claim formal v0.4.0, predictive accuracy, mesh independence, or LES improvement.
