# Case E Publication Readiness Gate

Generated: 2026-08-13T04:27:41.279203+00:00

## Verdict

- Publication readiness gate passed: True
- Claim readiness: `paper_ready_publication_packet; blocked formal accuracy release`
- Formal release allowed: False
- Recommended tag: `v0.4.0-rc73`
- Official MAE: 21.111408125 pp
- Official R2: -2.006330362229977
- Official Pearson: 0.11575649438573923

## Reviewer Audit

| id | reviewer question | status | paper location | allowed statement | must not claim |
|---|---|---|---|---|---|
| `PR001` | Is the official AIJ Case E validation protocol explicit and reproducible? | paper_ready_protocol | Methods / Validation protocol | Case E is evaluated under the official ac+N, z=2 m, 80-probe, raw_trilinear protocol. | Do not infer accuracy success from protocol setup alone. |
| `PR002` | What is the formal official z=2 m result? | limitations_ready_negative_validation | Results / Validation | The formal official z=2 m result remains negative: MAE=21.111408125 pp, R2=-2.006330362229977, Pearson=0.11575649438573923. | Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness. |
| `PR003` | Are diagnostic improvements separated from formal validation? | paper_ready_claim_boundary | Results / Diagnostics and Discussion | C014 is the strongest diagnostic candidate, but it remains limitations-only because formal R2 is negative. | Do not report diagnostic sampling, inlet tuning, no-SGS, affine calibration, or residual subsets as official validation. |
| `PR004` | Can a reviewer trace every reported metric to commands, logs, and CSV files? | paper_ready_provenance | Reproducibility appendix | The solver-run ledger maps Case E metrics to run commands/configs, logs, CSV outputs, hashes, and claim boundaries. | Do not use provenance completeness as evidence of accuracy success. |
| `PR005` | Are paper figures source-backed and claim-safe? | paper_ready_figure | Figure / Results | The figure can show negative validation and limitations-only diagnostic improvements. | Do not visually imply that diagnostic bars are formal accuracy validation. |
| `PR006` | Is the reproducibility appendix generated from current evidence? | paper_ready_appendix | Supplementary / Reproducibility appendix | The appendix can document commands, artifacts, release boundary, and environment limitations. | Do not describe the appendix as resolving the official accuracy failure. |
| `PR007` | Has the software feedback been constrained to validated defaults, diagnostic switches, and manifest-level publication dependencies? | paper_ready_software_boundary | Software implications / Limitations | CityLBM converts evidence into formal defaults, diagnostic-only switches, manifest-level publication dependencies, a Run Simulation Publication Gate output, GHA staging audit, and release blockers. | Do not promote benchmark-tuned diagnostics or manifest publication readiness to default accuracy models. |
| `PR008` | What still blocks a formal accuracy-oriented release? | blocked_formal_release | Limitations / Future work | Formal release remains blocked by the official z=2 m metric gate, missing Rhino/GHA load evidence, current GHA staging status, current GPU/runtime recovery needs, and unresolved VS C++ Build Tools recovery blockers. | Do not create a formal v0.4.0 tag or state that the optimized plugin satisfies research-grade accuracy. |
| `PR009` | Is the entire publication packet reproducible from scripts? | paper_ready_scripted_packet | Reproducibility statement | The current publication packet is script-generated and passes the paper evidence and claim-support gates. | Do not treat a passing publication gate as a passing CFD accuracy gate. |
| `PR010` | Are release assets lightweight and traceable? | paper_ready_release_assets | Data and code availability | The artifact index records 385 artifacts and 313 lightweight release assets; the curated release manifest selects 72 upload assets and keeps 20 raw/large assets excluded or hash-only. | Do not commit large VTK/raw geometry duplicates as manuscript evidence. |

## Boundary

This gate audits whether the current Case E material is publication-ready as a negative-validation and limitations package. It does not add CFD output, improve official metrics, or permit a formal release.
