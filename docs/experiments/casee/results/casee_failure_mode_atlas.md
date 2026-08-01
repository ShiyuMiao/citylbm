# Case E Failure-Mode Atlas

Generated: 2026-08-01T13:31:49.529626+00:00

## Verdict

- Formal v0.4.0 release allowed: False
- Official z=2 m MAE: 21.111408125 pp
- Official z=2 m R2: -2.006330362229977
- Official z=2 m Pearson: 0.11575649438573923
- Claim readiness: `limitations_ready_failure_mode_atlas`

## Failure Modes

| id | status | severity | quantitative signal | paper use |
|---|---|---|---|---|
| `FM001_official_metric_gate` | blocked | critical | official raw_trilinear z=2 m n=80; MAE=21.111 pp; R2=-2.006330; Pearson=0.115756 | Use as negative validation and release-boundary evidence. |
| `FM002_underprediction_bias` | active_limitation | critical | dx2 base bias=-31.233 pp and best gshift/nu diagnostic bias=-20.833 pp; z-center official bias=-16.409 pp | Use to explain systematic low-speed prediction at official pedestrian probes. |
| `FM003_probe_sampling_sensitivity` | diagnostic_only | major | raw MAE=21.111 pp, R2=-2.006330; vertical_valid_above MAE=16.041 pp, R2=-0.554717; z_plus_half MAE=18.761 pp, R2=-1.222132 | Use only as a probe-protocol sensitivity limitation. |
| `FM004_near_wall_solid_corner_risk` | active_limitation | critical | low-risk raw MAE=12.435 pp (n=47); high-risk raw MAE=34.589 pp (n=14); solid0 MAE=12.435 pp; solid4 MAE=35.845 pp | Use as the main limitations evidence for near-wall and solid-corner protocol risk. |
| `FM005_spatial_alignment_unlikely` | diagnostic_checked | moderate | identity Pearson=0.071789, R2=-2.311768; best available transform `flip_y` still has R2=-2.111059 | Use to narrow the error explanation away from a simple x/y convention mistake. |
| `FM006_runtime_preflight_blocked` | blocked | critical | official_followup_run_allowed=False; blocked=rhino_gha_load,gpu_runtime,vs_cpp_build_tools | Use to explain why no new long-run result was added in this release candidate. |

## Software Feedback

### FM001_official_metric_gate

- Primary evidence: `docs/experiments/casee/results/release_gate.json`
- Software feedback: Do not promote diagnostic settings to defaults until this gate improves on official raw_trilinear output.
- Default policy: No formal v0.4.0 default accuracy model.
- Next verification: casee_audit.py on a completed official z=2 m 80-probe CSV.
- Forbidden claim: Do not claim predictive accuracy or formal v0.4.0 readiness.

### FM002_underprediction_bias

- Primary evidence: `docs/experiments/casee/results/casee_ground_nu_diagnostic_comparison.csv`
- Software feedback: Prioritize near-ground velocity recovery, wall treatment, and inlet turbulence diagnostics.
- Default policy: Keep nu_lbm and z-origin changes default-off.
- Next verification: Repeat official raw_trilinear metrics after a physically justified wall/inlet change.
- Forbidden claim: Do not treat reduced bias alone as accuracy validation.

### FM003_probe_sampling_sensitivity

- Primary evidence: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`
- Software feedback: Expose sampling modes as diagnostics while preserving raw_trilinear as the formal metric.
- Default policy: Diagnostic modes remain non-default and non-formal.
- Next verification: Only raw_trilinear z=2 m can update release_gate.json.
- Forbidden claim: Do not substitute z_plus_half or vertical_valid_above for official z=2 m.

### FM004_near_wall_solid_corner_risk

- Primary evidence: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv`
- Software feedback: Add default-off wall/roughness/voxelization follow-up switches and retain per-probe risk metadata.
- Default policy: No promotion without official raw_trilinear improvement and Case A smoke regression.
- Next verification: Compare low/moderate/high risk residuals after the next completed official run.
- Forbidden claim: Do not claim the solver is validated for pedestrian-height corner probes.

### FM005_spatial_alignment_unlikely

- Primary evidence: `docs/experiments/casee/results/casee_spatial_alignment_diagnostic.csv`
- Software feedback: Keep wind-direction and lattice-convention audits in the Case E preset.
- Default policy: No coordinate transform becomes default from this diagnostic.
- Next verification: Rerun spatial audit only if coordinate mapping code changes.
- Forbidden claim: Do not claim all coordinate conventions are exhausted beyond the tested transforms.

### FM006_runtime_preflight_blocked

- Primary evidence: `docs/experiments/casee/results/casee_official_run_preflight.json`
- Software feedback: Keep launch preflight gates before scheduling long official runs.
- Default policy: Do not run or publish new official results while preflight is blocked.
- Next verification: Clear GPU, VS C++ and Rhino/GHA evidence, then rerun preflight.
- Forbidden claim: Do not describe the current environment as ready for more long native validation.

## Boundary

This atlas organizes existing negative-validation and diagnostic evidence. It does not add a new CFD run, does not change official z=2 m metrics, and does not allow formal v0.4.0.
