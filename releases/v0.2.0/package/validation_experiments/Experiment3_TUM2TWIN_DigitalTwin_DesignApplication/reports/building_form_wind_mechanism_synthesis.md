# Building-Form Wind-Environment Mechanism Synthesis

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This synthesis turns the existing morphology, FluidX3D and directional-fingerprint
outputs into a paper-facing architectural mechanism model. It does not add a
new CFD run. It integrates the same 101 retained building components and asks
which basic morphology descriptors are useful for explaining the screened
campus wind response.

## Mechanism Layers

- stage_saturation: near_facade_0_20m_mean_vr / stagnation = 0.0032 / 1.0000 (the immediate facade-adjacent band is almost fully low-speed and is a weak discriminator of form differences)
- local_context_recovery: local_context_20_50m_mean_vr / local_minus_near_delta = 0.0056 / 0.0024 (the 20-50 m band exposes morphology-differentiated recovery that is hidden near the facade)
- directional_reactivity: persistent/recovery/reactive local-context directional range = 0.0016 / 0.0189 / 0.0214 (useful recovery includes wind-sector response, not only higher mean VR)
- archetype_contrast: best/worst archetype recovery delta = R1_A1_linear_low_relative_height_recovery 0.0080 / R4_A5_open_or_mixed_low_response 0.0007 (combined morphology groups explain wind response better than single size or shape variables)

## Strongest Suppression Descriptors

- sector enclosure r50m: rho_mean=-0.396, rho_range=-0.362, role=primary_shelter_suppressor
- mean height: rho_mean=-0.351, rho_range=-0.363, role=primary_shelter_suppressor
- combined enclosure score: rho_mean=-0.302, rho_range=-0.328, role=primary_shelter_suppressor
- local built fraction r30m: rho_mean=-0.226, rho_range=-0.263, role=secondary_shelter_suppressor

## Conditional Form Descriptors

- footprint area: recovery rho=0.304, local mean rho=0.081
- perimeter^2/area: recovery rho=0.247, local mean rho=0.051
- elongation ratio: recovery rho=0.234, local mean rho=0.083

## Paper-Ready New Understanding

The main new understanding is a scale-dependent mechanism rather than a single
parameter law. The 0-20 m facade-adjacent band is nearly saturated by low speed,
so it is useful for identifying pedestrian sheltering but weak for separating
building types. The 20-50 m local-context band reveals whether the local
configuration recovers wind speed and whether that recovery has a wind-sector
fingerprint. In this band, mean height, sector enclosure and combined enclosure
are the most consistent suppressors of mean VR and directional range. Footprint
area, elongation and perimeter-area compactness are weak direct predictors, but
they become useful when read as conditional descriptors of low-relative-height,
elongated or articulated recovery subgroups.

## Claim Boundary

Supported: sample-internal digital-twin screening interpretation of building
form, local enclosure and directional response for the TUM Downtown core campus
block.

Not supported: universal morphology thresholds, field-validated causal laws,
annual wind-comfort compliance, pollutant dispersion or transferable design
optimization rules without additional cases and measurements.
