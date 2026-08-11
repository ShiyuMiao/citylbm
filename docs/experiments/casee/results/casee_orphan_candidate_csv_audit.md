# Case E Orphan Candidate CSV Audit

Generated: 2026-08-11T03:33:04.519062+00:00

## Verdict

- Audit passed: True
- Candidate CSVs: 4
- Formal raw candidates with complete logs: 0
- Any formal result allowed: False
- Best raw run: `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s2_pmodes_steps48000_spin12000`
- Best raw MAE: 13.7856467875 pp
- Best raw R2: -0.22984501828340775

## Formal Raw Rows

| run | tracked? | logs | MAE pp | R2 | Pearson | readiness |
|---|---:|---:|---:|---:|---:|---|
| `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s1p5_pmodes_steps48000_spin12000` | False | 0 | 14.172 | -0.2911 | 0.2897 | `blocked_missing_complete_run_log` |
| `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s2_pmodes_steps48000_spin12000` | False | 0 | 13.786 | -0.2298 | 0.3150 | `blocked_missing_complete_run_log` |
| `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s2p5_pmodes_steps48000_spin12000` | False | 0 | 13.911 | -0.2541 | 0.2937 | `blocked_missing_complete_run_log` |
| `casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s2_pmodes_steps48000_spin12000` | False | 0 | 14.386 | -0.3307 | 0.2801 | `blocked_missing_complete_run_log` |

## Boundary

This audit inventories local untracked/preexisting candidate CSVs only. It does not commit the raw CSVs, does not prove FluidX3D completed without complete run logs, does not update release_gate.json, and does not permit formal v0.4.0 or official z=2 m accuracy claims.
