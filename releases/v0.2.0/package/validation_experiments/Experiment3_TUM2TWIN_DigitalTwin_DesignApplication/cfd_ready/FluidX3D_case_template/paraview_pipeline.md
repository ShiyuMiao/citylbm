# ParaView visualization pipeline

1. Open FluidX3D exported `u-*.vtk`, `rho-*.vtk`, and `flags-*.vtk`.
2. Load `../building_collision_z0.stl` and `../ground_domain_z0.stl` as context geometry.
3. Apply `Slice` at z=1.5 m for pedestrian wind, plus z=10/20/40 m for low-altitude analysis.
4. Use `Calculator` for `sqrt(u_X*u_X+u_Y*u_Y+u_Z*u_Z)/5.0` as `VR`.
5. Use `Threshold`/`Contour` for acceleration, stagnation, and hotspot zones.
6. Export CSV slices for metric computation; do not save screenshots as evidence until VTK comes from a completed FluidX3D run.
