# AIJ Case E Manuscript Evidence Summary

Generated: 2026-08-09T12:18:27.805788+00:00

## Current Formal Metric

- Protocol: AIJ Case E `ac+N`, official z=2 m, 80 probes, formal `raw_trilinear` sampling.
- MAE: 21.111 pp.
- RMSE: 27.721 pp.
- Bias: -16.409 pp.
- R2: -2.006330.
- Pearson: 0.115756.
- Formal release allowed: False.
- Recommended tag: `v0.4.0-rc35`.

## Claim Matrix

| claim_id | readiness | section | allowed claim | evidence |
|---|---|---|---|---|
| C001 | paper_ready | Methods / Validation protocol | AIJ Case E validation uses the official ac+N, z=2 m, 80-probe protocol. | `docs/experiments/casee/results/casee_official_ac_N_probes.csv; docs/experiments/casee/casee_protocol.md` |
| C002 | limitations_ready | Results / Case E validation | The current formal official z=2 m Case E validation does not meet the release accuracy gate. | `docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/casee_metrics.csv` |
| C003 | weaken_claim | Results / Diagnostic improvement | Z-center lattice alignment improved the formal raw_trilinear diagnostic relative to the previous dx=2 probe-mode run, but R2 remained negative. | `docs/experiments/casee/results/casee_probe_mode_metrics.csv; docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` |
| C004 | limitations_ready | Discussion / Near-wall limitations | Error is concentrated at high protocol-risk probes near walls or solid interpolation corners. | `docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv; docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv` |
| C005 | limitations_ready | Discussion / Probe sampling diagnostics | Diagnostic sampling can reduce Case E MAE, but no diagnostic mode makes official z=2 m R2 positive. | `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` |
| C006 | paper_ready | Reproducibility / Build | The current CityLBM source builds in Release configuration on the available .NET SDK toolchain. | `docs/experiments/casee/results/citylbm_build_check.log; docs/experiments/casea/results/casea_smoke_regression.json` |
| C007 | blocked | Reproducibility / Build chain | Visual Studio Build Tools 2022 C++ and GPU runtime are not fully ready for additional long native validation. | `docs/experiments/casee/results/build_chain_manifest.json` |
| C008 | blocked | Release | Formal CityLBM v0.4.0 release is not allowed by the release gate. | `docs/experiments/casee/results/release_gate.json` |

## Results Paragraph Draft

AIJ Case E was evaluated under the official `ac+N` protocol using 80 pedestrian-height probes at z=2 m and formal raw-trilinear sampling. The latest z-center diagnostic run produced MAE = 21.111 percentage points, RMSE = 27.721 percentage points, bias = -16.409 percentage points, R2 = -2.006330, and Pearson = 0.115756 (newly_run; see `docs/experiments/casee/results/release_gate.json`). Because R2 remains negative and the release gate fails, this result should be reported as a transparent diagnostic/negative validation outcome rather than a predictive-accuracy result.

## Limitations Paragraph Draft

The dominant remaining limitation is near-wall and probe-protocol fidelity. Voxel/probe audits show substantially lower MAE for low-risk probes than for high-risk probes, while alternative diagnostic sampling modes reduce MAE but still do not make R2 positive. Therefore, the current evidence supports claims about workflow reproducibility, protocol transparency, and identified wall/voxelization/probe-sampling limitations, but it does not support formal mesh-independence, LES-improvement, or research-grade predictive-accuracy claims.

## Forbidden Claims

- CityLBM v0.4.0 has achieved validated predictive accuracy for AIJ Case E.
- z_plus_half, vertical_valid_above, or any z-offset diagnostic is the formal official z=2 m validation result.
- The current branch demonstrates mesh independence or LES improvement.
- The native Windows C++/GPU validation chain is fully ready for additional long runs.
