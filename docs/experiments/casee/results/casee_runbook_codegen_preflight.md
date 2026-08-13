# Case E Runbook Codegen Preflight

Generated: 2026-08-13T10:23:50.628143+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_runbook_codegen_preflight; no_solver_run`
- Formal accuracy claim supported: False

## Runbook Commands

| runbook id | passed | manifest path length | cleanup | run id |
|---|---:|---:|---:|---|
| `R005_official_dx2_zcenter_replicate` | True | 202 | True | `casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_pmodes_steps48000_spin12000_pf_R005` |
| `R006_wall_model_followup` | True | 232 | True | `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_wall_vd_dil1_damp0_pmodes_steps48000_spin12000_pf_R006` |
| `R007_inlet_turbulence_followup` | True | 228 | True | `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_afkfp_s2_pmodes_steps48000_spin12000_pf_R007` |
| `R008_dx1_feasibility_or_generation` | True | 204 | True | `casee_native_dx1_yn_sgs_gshift1_zoff0p5_nu0p001_pmodes_steps48000_spin12000_pf_R008` |
| `R010_c016_residual_channel_response_followup` | True | 239 | True | `casee_native_dx2_yn_nosgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_afkfp_s2_rt_c014_s1_pmodes_steps48000_spin12000_pf_R010` |

## Boundary

This gate executes only native case-generation commands from the next experiment runbook. It does not deploy to FluidX3D, does not run the solver, does not create probe CSVs, does not update official metrics, and does not permit formal v0.4.0.
