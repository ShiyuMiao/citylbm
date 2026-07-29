# Experiment 3 Limitations and Future Validation Roadmap

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This roadmap turns the remaining Experiment 3 claim boundaries into a
reviewer-facing validation plan. It does not add new CFD, field, wind-tunnel,
pollutant or CityLBM-Grasshopper results. It specifies what evidence would be
needed to upgrade the current screening study into stronger engineering or
regulatory claims.

## Limitation-to-Validation Matrix

| limitation_id   | limitation                                                                                         | claim_boundary                                                                                             | required_next_evidence                                                                                                                                                                            | upgrade_path                                                                | priority                                  |
|:----------------|:---------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------|:------------------------------------------|
| L1              | No field or wind-tunnel validation for the TUM2TWIN campus case.                                   | Do not claim field-validated predictive accuracy for Experiment 3.                                         | Install temporary anemometers or use wind-tunnel/PIV testing for selected pedestrian points; compare U/Uref, directionality and uncertainty against FluidX3D outputs.                             | screening-level result -> measured or wind-tunnel-supported validation case | high_for_prediction_claims                |
| L2              | Open-Meteo 2024 is a proxy directional weighting layer, not a calibrated site wind climate.        | Do not claim annual Lawson/NEN/AIJ comfort or safety compliance.                                           | Acquire calibrated multi-year wind rose or local station data, define exceedance thresholds by activity category, and compute annual threshold probabilities at pedestrian receptors.             | directional screening -> formal annual comfort/safety assessment            | high_for_compliance_claims                |
| L3              | Residual convergence and complete grid-independence evidence are not available.                    | Do not frame the FluidX3D result as final numerical convergence proof.                                     | Run dx sensitivity such as 3 m/2 m/1 m where feasible, store residual or monitor-point histories, and report grid-convergence index or uncertainty bands.                                         | screening protocol transparency -> numerically stronger CFD protocol        | medium_high_for_method_review             |
| L4              | CityLBM-Grasshopper end-to-end execution has not been completed.                                   | Use 'FluidX3D-native simulation with CityLBM-compatible geometry preparation' unless GH evidence is added. | Open Rhino/Grasshopper, load CityLBM template, run a small end-to-end case, archive GH file, screenshots, exported inputs, logs and output fields.                                                | CityLBM-compatible package -> CityLBM-GH executed workflow                  | medium_if_title_mentions_CityLBM          |
| L5              | Pollutant dispersion was not simulated.                                                            | Do not claim C/C0, exposure integral or pollutant hotspot results.                                         | Add scalar transport or passive tracer simulation with road/point/area source definitions, validate source normalization, and postprocess C/C0 and path exposure at pedestrian height.            | ventilation screening -> pollutant-dispersion application case              | medium_for_environmental_health_extension |
| L6              | GCBTE is defined but not computed because no independent 3DGS-derived collision extraction exists. | Do not claim completed 3DGS-to-collision transfer accuracy.                                                | Generate an independent 3DGS-derived solid mask or boundary extraction, compare against CityGML/LoD3 or closed-prism ground truth using IoU, Chamfer/Hausdorff distance and voxel-mask agreement. | conceptual boundary-transfer metric -> quantified GCBTE validation          | medium_for_digital_twin_novelty           |
| L7              | S1/S2 are negative sensitivity tests, not optimized design proposals.                              | Do not write S1/S2 as successful interventions.                                                            | Design S3-Sn wind-sector-coupled interventions using inlet-sector alignment, pressure-exchange paths and local enclosure continuity; rerun the same FluidX3D protocol and compare S0/S1/S2/Sn.    | negative design sensitivity -> positive design optimization evidence        | high_for_design_application_claims        |
| L8              | Morphology rules are sample-internal screening descriptors.                                        | Do not present morphology thresholds as universal causal laws.                                             | Replicate the same morphology pipeline across additional campus blocks, seasons, grid levels and design variants; test out-of-sample performance and robustness.                                  | sample-internal descriptor -> transferable morphology rule                  | medium_for_generalization_claims          |

## Manuscript Positioning

The current manuscript can confidently state a FluidX3D-native
digital-twin-to-CFD screening workflow and a staged building-form
interpretation for the TUM2TWIN campus core. The next experimental stage should
prioritize field/wind-tunnel validation and calibrated wind-climate coupling if
the target claim is predictive accuracy or comfort compliance. If the target
claim is design application, the highest-yield next experiment is not another
simple porosity opening but an S3-Sn set of wind-sector-coupled interventions.
