# C005 dx=2 Domain-Decomposition Ablation Audit

Generated: 2026-08-09T15:41:10.985640+00:00

## Verdict

- Status: `completed_decomposition_sensitivity_warning`
- Evidence type: `newly_run`
- Claim readiness: `limitations_ready_runtime_decomposition_ablation; blocked formal accuracy release`
- 48000-step log complete: True
- Manifest protocol ok: True
- Pass condition met: False
- Formal release allowed: False

## Official z=2 m raw_trilinear metric

- MAE: 19.7262730375 pp
- R2: -1.608075055394031
- Pearson: 0.09931531110580517

## Delta vs current z-center baseline

- MAE delta: -1.3851350875000001 pp
- R2 delta: 0.3982553068359458
- Pearson delta: -0.01644118327993406

## Boundary

C005 is a completed dx=2 4x1x1 domain-decomposition ablation under the official z=2 m raw_trilinear protocol. It is runtime/reproducibility evidence only and cannot support formal v0.4.0, mesh independence, or a default accuracy upgrade.
