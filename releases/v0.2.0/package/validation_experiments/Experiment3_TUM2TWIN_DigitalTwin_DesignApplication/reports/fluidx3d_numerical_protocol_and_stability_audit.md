# FluidX3D Numerical Protocol and Stability Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This audit deepens the Experiment 3 evidence package by separating archived
FluidX3D protocol facts from numerical and validation claims that remain
unsupported. It adds no new CFD field and does not change the reported wind
maps. Its role is to make the dx=2 m, eight-direction, time-sampled screening
case reproducible enough for manuscript review while preventing overclaiming.

## Protocol Table

| protocol_item | status | value | evidence_type | paper_safe_use | claim_boundary |
|---|---|---|---|---|---|
| collision_geometry | recorded_complete_for_screening | core_photogrammetry_extent_prism_collision_z0.stl | newly_run | Use as the accepted S0 collision boundary for the core campus screening case. | Do not describe the textured photogrammetry shell as the collision boundary. |
| grid_and_domain | recorded_complete_for_screening | 320 x 390 x 60; dx=2.0; domain=640 x 780 x 120 | newly_run | Report as the core dx=2 m screening grid. | Not a grid-independent final engineering simulation. |
| physical_reference_values | recorded_complete_for_pilot_normalization | Uref=5.0; nu_air=1.5e-5; rho=1.225 | newly_run | Use to define the pilot velocity-ratio normalization and air-property conversion. | Uref is not a measured site wind profile and does not establish annual comfort exceedance probability. |
| lbm_conversion | recorded_with_boundary | dt=0.02; lbm_nu=0.01000; tau=0.52999996 | newly_run | Report as archived solver-conversion evidence for the completed FluidX3D pilot. | Tau is close to the low-relaxation stability side; this supports protocol transparency, not solver validation. |
| reynolds_reporting | recorded_with_boundary | Re_dx=666667; FluidX3D_reported_Re=< 29331 | newly_run | Use as a protocol descriptor, not as validation of Reynolds similarity. | No wind-tunnel or field Reynolds-scaling closure is established. |
| wind_direction_protocol | recorded_complete_for_screening | 0;45;90;135;180;225;270;315 | newly_run | Use for eight-direction screening and equal-weighted aggregation. | Open-Meteo weighting remains a climate proxy, not a formal measured wind rose. |
| sampling_protocol | recorded_complete_for_short_time_sampling | spinup=6000; run_steps=12000; samples=8000;10000;12000 | newly_run | Use to support the internal time-sampled screening claim. | This is not a long statistical averaging or residual-convergence proof. |
| output_planes_and_metrics | recorded_complete_for_screening | z~2,4,10,20,40 m; mean/P75/P90/P95/max VR; VR<0.2, VR>0.6, VR>1.0 | newly_run | Use for pedestrian-height and vertical-recovery interpretation. | Thresholds are screening bins, not Lawson/NEN/AIJ annual classes. |
| solid_and_open_boundary_semantics | recorded_with_boundary | buildings/ground as TYPE_S; directional pilot forcing/velocity setup | newly_run + blocked | Use to explain no-slip collision treatment and pilot inflow status. | A measured atmospheric boundary-layer inlet profile is not established in the archive. |
| temporal_stability | partial_screening_support | 3 post-spin-up samples per direction; effect-size intervals available | newly_run + blocked | Use to say the main low-speed and vertical-recovery patterns are stable within archived samples. | Do not call this formal convergence, stationarity or uncertainty quantification. |
| grid_sensitivity | partial_support_outside_core_final_case | district coarse/medium and full-LoD2 coarse/medium audit files exist | newly_run + blocked | Use only as a supporting sensitivity audit. | The core dx=2 m S0/S1/S2 results are not a full grid-independence study. |
| residual_or_solver_convergence | blocked_not_recorded | [RESULT_NEEDED: residual/convergence monitor] | blocked | State as a limitation and next rigor step. | Do not claim formal numerical convergence. |
| field_validation_and_compliance | blocked_not_available | [RESULT_NEEDED: measured wind, wind tunnel, annual exceedance probabilities] | blocked | Keep the experiment framed as digital-twin screening and design interpretation. | No field-validated prediction, annual Lawson/NEN/AIJ compliance or pollutant dispersion claim. |

## What This Adds to the Paper Conclusion

The strongest numerical conclusion is not that the simulation is a
field-validated prediction. The supported conclusion is narrower and more
useful for a digital-twin application paper: the TUM2TWIN core campus block can
be translated into an auditable FluidX3D-native screening case with recorded
geometry, grid, reference-speed, viscosity, LBM conversion, wind-direction and
sampling parameters. The resulting low pedestrian-layer VR pattern is stable
within the archived direction-sample evidence, while the same archive keeps
residual convergence, complete grid independence, field validation and annual
comfort compliance outside the claim boundary.

This strengthens the building-form discussion because it clarifies the scale of
the inference. The paper can interpret relative vertical massing, local
enclosure, plan continuity and wind-sector reactivity as screening descriptors
of a real campus block. It should not present these descriptors as universal
causal laws or code-compliance thresholds.

## Reviewer-Critical Boundaries

- The archived Uref and Open-Meteo weighting are protocol/proxy choices, not a
  measured site wind-climate closure.
- The tau/Re entries are transparent solver-conversion evidence, not a solver
  validation result.
- Three post-spin-up samples support internal pattern stability only.
- Coarse/medium comparisons support a sensitivity audit, not full grid
  independence of the core S0/S1/S2 conclusions.
- Residual convergence, field measurement, wind-tunnel closure, annual
  Lawson/NEN/AIJ compliance and pollutant dispersion remain blocked.
