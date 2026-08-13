# Case E Native Codegen Smoke Gate

Generated: 2026-08-13T11:04:42.750891+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_codegen_smoke; no_solver_run`
- Formal accuracy claim supported: False

## Cases

| case | passed | manifest path length | cleanup | run id |
|---|---:|---:|---:|---|
| `default_off_baseline` | True | 187 | True | `casee_native_dx4_yn_sgs_gshift1_zoff2_nu0p001_pmodes_steps10_spin0` |
| `inlet_afk_nosgs` | True | 213 | True | `casee_native_dx4_yn_nosgs_gshift1_zoff2_nu0p001_dom1x1x1_inlet_afkfp_s2_pmodes_steps10_spin0` |
| `wall_voxel_dilation` | True | 215 | True | `casee_native_dx4_yn_sgs_gshift1_zoff2_nu0p001_dom1x1x1_wall_vd_dil1_damp0_pmodes_steps10_spin0` |
| `c016_residual_channel_response` | True | 224 | True | `casee_native_dx4_yn_nosgs_gshift1_zoff2_nu0p001_dom1x1x1_inlet_afkfp_s2_rt_c014_s1_pmodes_steps10_spin0` |

## Boundary

This gate runs short native Case E code-generation checks for default, inlet, wall, and C016 residual-target configurations. It verifies generated manifests and cleanup only. It does not run FluidX3D, produce probe CSVs, update official metrics, promote diagnostic settings to defaults, or permit formal v0.4.0.
