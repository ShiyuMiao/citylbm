# C008-C015 Inlet Turbulence and SGS Sweep Audit

Generated: 2026-08-11T00:16:48.741216+00:00

## Verdict

- Status: `completed_inlet_turbulence_improved_but_negative_r2`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release`
- Formal release allowed: False
- Best candidate: `C014_inlet_k_synthetic_fullplane_s2p00_no_sgs`

## Best Official z=2 m Raw Metric

- MAE: 13.7856467875 pp
- RMSE: 17.730306046944502 pp
- Bias: -3.5140317875 pp
- R2: -0.22984501828340775
- Pearson: 0.31496559664177526
- Delta MAE vs z-center baseline: -7.3257613 pp
- Delta R2 vs z-center baseline: 1.7764854389355929
- Delta Pearson vs z-center baseline: 0.19920911515698442
- Delta MAE vs C005: -5.940626162499999 pp
- Delta R2 vs C005: 1.3782301219108528
- Delta Pearson vs C005: 0.21565030110270944

## Boundary

C008-C015 are completed official-height raw_trilinear candidate runs using a default-off synthetic full-plane inlet based on AF_caseE k. C013-C015 add a no-SGS ablation; C014 is the strongest current diagnostic candidate, but R2 remains negative. The turbulence scale and no-SGS setting are diagnostic sweep parameters. Use as inlet-turbulence evidence and software-feedback guidance only; do not claim formal v0.4.0, predictive accuracy, mesh independence, or LES improvement.
