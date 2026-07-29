# FluidX3D Boundary Conditions, Numerics, and Convergence Boundary

evidence_type: newly_run + blocked

This note records the numerical setup that can be supported from the archived FluidX3D scripts and logs. It is intended to close the reproduction-package gap between the solver run reports and the paper method section.

## Reproducible Setup Table

The machine-readable table is stored at `manifests/fluidx3d_core_prism_boundary_condition_table.csv`.

| Item | Value | Evidence boundary |
|---|---:|---|
| Main case | `core_prism_avg_8dir_dx2m_spin6k_s3` | newly_run |
| Collision geometry | `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl` | newly_run |
| Grid | `320 x 390 x 60` cells | newly_run |
| Spatial resolution | `dx = 2.0 m` | newly_run |
| Domain size | `640 x 780 x 120 m` | newly_run, computed from grid and dx |
| Reference speed | `Uref = 5.0 m/s` | newly_run |
| Air kinematic viscosity | `1.5e-5 m2/s` | newly_run |
| Time conversion | `50 time steps/s` | newly_run |
| Time step | `0.02 s` | newly_run, computed |
| Total steps | `12,000` | newly_run |
| Physical duration | `240 s` | newly_run, computed |
| Spin-up | `6,000 steps = 120 s` | newly_run, computed |
| Samples | `8,000 / 10,000 / 12,000 steps` | newly_run |
| Wind directions | `0, 45, ..., 315 deg` velocity-to | newly_run |
| Reported physical `Re_dx` | `666,667` | newly_run, log-reported |
| LBM smoke viscosity | `0.01000` | newly_run, log-reported |
| Relaxation time | `0.52999996` | newly_run, log-reported |
| FluidX3D reported Re | `< 29331` | newly_run, log-reported |

## Boundary Interpretation

Buildings and ground were voxelized as solid collision regions and are interpreted as no-slip solid boundaries for the pedestrian wind-screening runs. Directional wind response is represented as eight independent velocity-to directions and then aggregated equally or with the Open-Meteo 2024 proxy weights.

The current archive does not establish a validated atmospheric boundary-layer inflow profile, field-calibrated roughness profile, residual convergence criterion, grid-independent annual comfort classification, wind-tunnel validation, or measured-campus wind closure. These remain `blocked` evidence items. Therefore, the paper should describe the results as digital-twin-to-FluidX3D screening and morphology interpretation, not as final compliance-level wind comfort certification.
