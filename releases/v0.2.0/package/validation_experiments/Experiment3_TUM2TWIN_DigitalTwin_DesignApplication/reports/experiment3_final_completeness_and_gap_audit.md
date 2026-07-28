# Experiment 3 Final Completeness and Gap Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Verdict

The current archive is complete enough for a standalone Experiment 3 section in an SCI manuscript if the claim is framed as:

`FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation.`

It is not complete enough for:

- measured validation claims;
- annual comfort/safety compliance;
- pollutant dispersion;
- CityLBM-Grasshopper end-to-end execution;
- 3DGS-to-collision transfer-error closure;
- successful design optimization.

## Most Defensible Contribution Chain

1. TUM2TWIN visual, semantic and CAD/OBJ layers are separated by function.
2. Visual photogrammetry/Rhino assets are retained for scene audit, not used directly as final collision bodies.
3. Closed LoD/OBJ-derived collision geometries are QA-recorded and FluidX3D-ready.
4. Eight-direction, three-sample FluidX3D outputs show robust pedestrian-layer low-speed conditions.
5. Open-Meteo weighting confirms proxy-direction robustness without claiming annual compliance.
6. Morphology statistics, archetypes, stage-transition and directional-fingerprint analysis identify local enclosure, relative vertical massing, plan continuity, near-to-context recovery and wind-sector reactivity as screening descriptors.
7. S1/S2 negative sensitivity shows that porosity area alone is not a sufficient intervention mechanism.

## Current Paper Assets

- Main result rows: `19`
- Reviewer-facing figures/tables: `12` with `12` ready for manual review.
- Evidence inventory rows: `125`
- Archive manifest status should be checked through `manifests/github_archive_manifest.csv` after every commit.

## Manuscript-Safe Central Claim

In the TUM2TWIN campus-core case, digital-twin wind-environment value comes from the traceable conversion of visually realistic but CFD-fragile data into closed semantic collision geometry and from the ability to diagnose persistent pedestrian-layer ventilation insufficiency in relation to local building form. The morphology-response archetype, stage-transition and directional-fingerprint layers show that wind recovery is better discussed as a near-to-context response of relative vertical massing, elongation, plan continuity, local enclosure and wind-sector reactivity than as a single footprint, height or porosity effect.

## Required Remaining Evidence for Stronger Claims

| requirement | status | evidence_type | evidence_artifact | paper_safe_interpretation |
|---|---|---|---|---|
| CityLBM-Grasshopper end-to-end execution | blocked | blocked | cfd_ready/CityLBM_GH_input_template/README.md; reports/claim_boundary.md | Frame as FluidX3D-native simulation with a CityLBM-compatible geometry package unless GH execution evidence is added. |
| Measured or wind-tunnel validation | blocked | blocked | reports/claim_boundary.md | Do not claim field-validated predictive accuracy. |
| Formal Lawson/NEN/AIJ annual comfort compliance | blocked | blocked | reports/claim_boundary.md | Do not claim annual threshold-exceedance comfort or safety classes. |
| Pollutant dispersion | blocked | blocked | reports/metric_system_for_digital_twin_wind_application.md | Pollutant metrics remain templates only. |
| GCBTE 3DGS collision-transfer error | blocked | blocked | manifests/gcbte_status_table.csv | GCBTE is defined but not computed because no independent 3DGS-derived collision extraction exists. |
