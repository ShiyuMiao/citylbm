# S1 Ventilation-Relief Geometry Report

evidence_type: newly_run + blocked

This file commits an explicit S1 geometry for the design-application layer of Experiment 3. S1 is not a final architectural proposal. It is a morphology sensitivity scenario that removes a minimal east-west relief corridor from the accepted S0 closed-prism collision field.

## Geometry Protocol

- Baseline: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- S1 STL: `cfd_ready/core_prism_s1_ventilation_relief_collision_z0.stl`
- Selection method: Dijkstra least-removal path through the S0 5 m heightfield. Open cells have low traversal cost; solid cells have height-weighted removal cost.
- Corridor radius: `2` cells.
- Nominal corridor width: `25.0 m`.
- Removed cells: `66`.
- Removed area: `1650.0 m2`.
- Removed fraction of baseline footprint: `2.79%`.
- Removed height min/max/mean: `12.72 / 23.45 / 18.67 m`.
- S1 triangles: `15498`.
- Audit figure: `figures/core_prism_s1_ventilation_relief_geometry_audit.png`.

## Evidence Boundary

At this stage the S1 collision geometry is committed and QA-recorded, but wind-field improvement is not yet claimed. Any S1-S0 comfort, stagnation or VR improvement statement must wait until S1 is voxelized, simulated and post-processed with the same FluidX3D protocol as S0.
