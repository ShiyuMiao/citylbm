// TUM2TWIN wind pilot template for FluidX3D.
// Copy this file into FluidX3D/src/setup.cpp after installing/building FluidX3D.
// Geometry: cfd_ready/building_collision_z0.stl, meters, z0-local coordinates.
// Evidence boundary: template only; no simulation result is claimed.

void main_setup() {
    // Required extensions in defines.hpp: EQUILIBRIUM_BOUNDARIES, VOLUME_FORCE
    const uint Nx = 133u, Ny = 115u, Nz = 72u; // coarse pilot
    const float si_Uref = 5.0f;       // m/s at 10 m, placeholder until wind rose is connected
    const float si_nu_air = 1.5E-5f;  // m^2/s
    const float dx = 2.0f;   // m/cell
    units.set_m_kg_s(1.0f, 0.05f, 1.0f, dx, si_Uref, 1.225f);
    const float lbm_nu = units.nu(si_nu_air);
    LBM lbm(Nx, Ny, Nz, lbm_nu);

    Mesh* buildings = read_stl(get_exe_path()+"../stl/building_collision_z0.stl", 1.0f);
    lbm.voxelize_mesh_on_device(buildings, TYPE_S);

    // Boundary-condition sketch:
    // - Rotate or remap wind vector for eight directions: 0,45,...,315 degrees.
    // - Use TYPE_E equilibrium boundaries for inflow/top as needed.
    // - Keep buildings and ground as no-slip TYPE_S.
    // - Export u/rho/flags VTK after spin-up and averaging windows for ParaView.
    lbm.run(0u);
    for(uint t=0u; t<=20000u; t+=1000u) {
        lbm.run(1000u);
        if(t>=10000u) {
            lbm.u.write_device_to_vtk();
            lbm.flags.write_device_to_vtk();
        }
    }
}
