# S2 Network-Porosity Geometry Report

evidence_type: newly_run + superseded_by_simulation

S2 is a stronger network-scale sensitivity scenario following the near-null S1 result. It is not a final architectural proposal. It tests whether multiple connected porosity releases are needed before the TUM Downtown campus-core flow field responds at pedestrian height.

## Geometry Protocol

- Baseline: `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl`
- S2 STL: `cfd_ready/core_prism_s2_network_porosity_collision_z0.stl`
- Selection method: three Dijkstra least-removal paths through the S0 5 m heightfield: two east-west context paths and one north-south central link.
- Corridor radius: `2` cells.
- Nominal corridor width: `25.0 m`.
- Removed cells: `201`.
- Removed area: `5025.0 m2`.
- Removed fraction of baseline footprint: `8.50%`.
- Removed height min/max/mean: `12.38 / 32.43 / 21.71 m`.
- S2 triangles: `14612`.
- Audit figure: `figures/core_prism_s2_network_porosity_geometry_audit.png`.

## Evidence Boundary

This geometry-only report records how S2 was constructed. It has been superseded for solver status by `reports/s2_network_porosity_fluidx3d_comparison_report.md`, where the S2 FluidX3D run is documented. S2 remains a numerical morphology sensitivity case for testing network porosity. It does not represent constructability, ownership, heritage, cost, or formal campus planning feasibility.
