# C008/C009 Inlet Turbulence Audit

Generated: 2026-08-09T14:50:44.300801+00:00

## Verdict

- Status: `completed_inlet_turbulence_improved_but_negative_r2`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release`
- Formal release allowed: False
- Best candidate: `C009_inlet_k_synthetic_fullplane_s0p70`

## Best Official z=2 m Raw Metric

- MAE: 14.677544574999999 pp
- RMSE: 18.643675779275984 pp
- Bias: -4.5584198 pp
- R2: -0.3598186886134105
- Pearson: 0.2834105384611786
- Delta MAE vs z-center baseline: -6.4338635125 pp
- Delta R2 vs z-center baseline: 1.6465117686055901
- Delta Pearson vs z-center baseline: 0.16765405697638774
- Delta MAE vs C005: -5.048728375 pp
- Delta R2 vs C005: 1.24825645158085
- Delta Pearson vs C005: 0.18409524292211277

## Boundary

C008/C009 are completed official-height raw_trilinear candidate runs using a default-off synthetic full-plane inlet based on AF_caseE k. They improve MAE, R2, and Pearson, but R2 remains negative and the turbulence scale is a diagnostic sweep parameter. Use as inlet-turbulence evidence and software-feedback guidance only; do not claim formal v0.4.0, predictive accuracy, mesh independence, or LES improvement.
