# C003 dx=2 Z-Origin Ablation Audit

Generated: 2026-08-11T01:10:30.152065+00:00

## Verdict

- Status: `completed_ablation_supports_zorigin_sensitivity`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_zorigin_ablation; blocked formal accuracy release`
- 48000-step log complete: True
- Pass condition met: True
- Formal release allowed: False

## Official z=2 m raw_trilinear metric

- MAE: 23.125594087499998 pp
- R2: -2.221378753276796
- Pearson: 0.09921683588947784

## Delta vs current z-center baseline

- MAE delta: 2.0141859624999974 pp
- R2 delta: -0.21504839104681928
- Pearson delta: -0.016539658496261392

## Boundary

C003 is a completed official z=2 m raw_trilinear z-origin ablation. It supports treating z-center behavior as a protocol/near-wall sensitivity diagnostic, not as a validated default accuracy model. It does not support formal v0.4.0.
