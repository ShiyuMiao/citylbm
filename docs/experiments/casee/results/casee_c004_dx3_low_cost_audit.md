# C004 dx=3 Low-Cost Direction Check Audit

Generated: 2026-08-13T06:08:10.398939+00:00

## Verdict

- Status: `completed_low_cost_positive_correlation`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_dx3_low_cost_regression; blocked formal accuracy release`
- 48000-step log complete: True
- Manifest protocol ok: True
- Pass condition met: True
- Formal release allowed: False

## Official z=2 m raw_trilinear metric

- MAE: 24.48456695 pp
- R2: -2.5282993702661267
- Pearson: 0.10934876905648619

## Delta vs current z-center baseline

- MAE delta: 3.373158825000001 pp
- R2 delta: -0.5219690080361499
- Pearson delta: -0.0064077253292530445

## Boundary

C004 is a completed dx=3 low-cost official z=2 m raw_trilinear control run. It checks direction/protocol consistency and coarse-grid behavior only. It does not support formal v0.4.0, mesh independence, or a default accuracy upgrade.
