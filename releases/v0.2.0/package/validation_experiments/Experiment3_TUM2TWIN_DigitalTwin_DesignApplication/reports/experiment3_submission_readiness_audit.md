# Experiment 3 Submission Readiness Audit

evidence_type: newly_run + preexisting_artifact + blocked

Generated at: 2026-07-28

## Summary

- Figure/table assets checked: `8`
- Ready for manual review: `8`
- Missing assets: `0`
- Canonical paper position: FluidX3D-native simulation with a CityLBM-compatible geometry package.
- Claim strength: screening-level wind-environment application and morphology interpretation, not field-validated prediction.

## Asset-Level Status

| asset | type | exists | evidence_type | paper_safe_use | boundary |
|---|---|---|---|---|---|
| Fig. E3-1 | figure | yes | newly_run | baseline pedestrian-layer low-speed screening and manual visual audit | not annual Lawson/NEN/AIJ compliance; not field validation; not scalar dispersion |
| Fig. E3-2 | figure | yes | newly_run | morphology interpretation and variable ranking | not a deterministic surrogate model; not externally validated thresholds |
| Fig. E3-3 | figure | yes | newly_run | negative design-sensitivity evidence | not successful optimization; not final design recommendation |
| Fig. E3-4 | figure | yes | newly_run + blocked | sample-internal design-rule screening | not universal threshold; not field-validated design rule |
| Fig. E3-S1 | figure | yes | newly_run + blocked | supplementary uncertainty and effect-size audit | not measurement uncertainty; not grid convergence; not annual comfort exceedance probability |
| Table E3-1 | table | yes | newly_run + preexisting_artifact + blocked | main result table and evidence anchor | rows with blocked components must retain boundary wording |
| Table E3-2 | table | yes | newly_run + blocked | limitations table and claim boundary | blocked rows must not be converted into completed results |
| Table E3-3 | table | yes | newly_run | digital-twin geometry readiness metric | GCRI is a paper-internal readiness score, not an external standard |

## Remaining Blockers

- blocked: field or wind-tunnel validation.
- blocked: annual Lawson/NEN/AIJ comfort or safety compliance.
- blocked: pollutant scalar transport.
- blocked: GCBTE boundary-transfer computation.
- blocked: CityLBM-Grasshopper end-to-end execution.

## Submission Use

The current package is suitable for a design-application experiment section once the target journal, reference style and paper-level framing are fixed. The reviewer-facing figures and tables are present and traceable to CSV, manifest or report sources. The safest title wording remains: `FluidX3D-native simulation with CityLBM-compatible geometry package`.
