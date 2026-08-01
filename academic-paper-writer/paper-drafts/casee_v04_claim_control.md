# Case E Claim-Control Sheet for v0.4.0-rc

evidence_type: newly_run + blocked
scope: AIJ Case E, official z=2 m, ac+N, 80 probes

## Metric Snapshot

| metric | value | status |
|---|---:|---|
| n probes | 80 | official protocol |
| MAE | 21.111 pp | fails accuracy target |
| RMSE | 27.721 pp | diagnostic only |
| Bias | -16.409 pp | under-prediction remains |
| R2 | -2.006330 | fails gate |
| Pearson | 0.115756 | positive but weak |
| formal v0.4.0 allowed | false | rc only |

Source: `docs/experiments/casee/results/release_gate.json`

## Claim Levels

| level | claim | manuscript use |
|---|---|---|
| Paper-ready | The official Case E protocol was implemented and audited. | Methods / Reproducibility |
| Paper-ready | The CityLBM source builds and Case A smoke regression is preserved. | Reproducibility, not accuracy |
| Limitations-ready | Official z=2 m Case E does not pass the accuracy gate. | Results / Limitations |
| Limitations-ready | Error concentrates at near-wall and solid-corner probe-risk groups. | Discussion / Future work |
| Weakened diagnostic | Z-center alignment improves MAE and Pearson but keeps R2 negative. | Diagnostic result only |
| Blocked | Formal v0.4.0 predictive-accuracy release. | Do not claim |

## Default vs Experimental Software Implications

Settings that can remain in the default reproducibility path:

- Official Case E preset: `ac+N`, scale factor 250, Uref 3.928296 m/s, zref 15.9 m, official z=2 m probes.
- AF-based inlet profile ingestion and audit output.
- Run manifests, metric reports, residual tables, and probe-risk diagnostics.
- Case A smoke regression as a workflow non-regression guard.

Settings that must remain experimental or diagnostic:

- `DiagnosticZOriginOffsetM` / z-center alignment.
- `z_plus_half`, `vertical_valid_above`, `nearest_valid`, and `fluid_weighted` probe sampling.
- Rough-wall, effective-ground, near-wall, or boundary-mode switches that have not made official z=2 m R2 positive.

## Release Rule

Do not create a formal `v0.4.0` tag while any of the following is true:

- official z=2 m R2 is negative;
- MAE remains near the current 21 pp level;
- Pearson is only weakly positive;
- Rhino/Grasshopper loading of the newly built GHA is unverified;
- the native FluidX3D long-run chain is blocked by GPU or Visual Studio C++ setup.

Current recommended release state: `v0.4.0-rc`, accuracy diagnostic release candidate.
