# =============================================================================
# CityLBM v0.5.0 — AIJ Case A Post-Processing & Comparison
# =============================================================================
# Paste this into a SECOND GhPython component.
# Connect the "Case Dir" output from Run Simulation → input "case_dir" (text).
#
# Inputs:  case_dir  (Text)   — VTK output directory from Run Simulation
#          time_step (Integer) — VTK time step to read (-1 = latest)
#
# Outputs: a (Text)     — Comparison report
#          b (Point)    — Simulated velocity sample points (color-coded)
#          c (Point)    — Experimental data points (for visual diff)
#          d (Curve)    — Difference vectors (sim - exp)
# =============================================================================

import clr
import os
import math
import struct

clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

H  = 0.2    # Building height (must match simulation setup)
U_H = 5.0   # Reference wind speed (m/s)

# AIJ experimental data (same as setup script)
AIJ_EXP = {
    -1.5: [(0.05,0.42),(0.10,0.55),(0.20,0.68),(0.30,0.74),(0.50,0.82),
           (0.75,0.89),(1.00,0.95),(1.25,0.98),(1.50,1.00),(2.00,1.02)],
    -0.5: [(0.05,0.10),(0.10,0.18),(0.20,0.25),(0.30,0.28),(0.50,0.32),
           (0.75,0.30),(1.00,0.22),(1.25,0.10),(1.50,0.05),(2.00,0.02)],
     0.0: [(0.05,0.05),(0.10,0.08),(0.20,0.10),(0.30,0.08),(0.50,0.05),
           (0.75,0.02),(1.00,-0.05),(1.25,0.05),(1.50,0.12),(2.00,0.22)],
     0.5: [(0.05,-0.15),(0.10,-0.10),(0.20,-0.05),(0.30,0.00),(0.50,0.08),
           (0.75,0.12),(1.00,0.18),(1.25,0.30),(1.50,0.42),(2.00,0.55)],
     1.0: [(0.05,-0.08),(0.10,0.00),(0.20,0.05),(0.30,0.10),(0.50,0.18),
           (0.75,0.22),(1.00,0.28),(1.25,0.38),(1.50,0.48),(2.00,0.60)],
     2.0: [(0.05,0.05),(0.10,0.12),(0.20,0.18),(0.30,0.22),(0.50,0.30),
           (0.75,0.35),(1.00,0.40),(1.25,0.48),(1.50,0.55),(2.00,0.65)],
     3.0: [(0.05,0.15),(0.10,0.22),(0.20,0.28),(0.30,0.32),(0.50,0.40),
           (0.75,0.45),(1.00,0.50),(1.25,0.58),(1.50,0.63),(2.00,0.70)],
     4.0: [(0.05,0.25),(0.10,0.32),(0.20,0.38),(0.30,0.42),(0.50,0.50),
           (0.75,0.55),(1.00,0.60),(1.25,0.65),(1.50,0.70),(2.00,0.75)],
     5.5: [(0.05,0.38),(0.10,0.45),(0.20,0.52),(0.30,0.55),(0.50,0.62),
           (0.75,0.68),(1.00,0.72),(1.25,0.78),(1.50,0.82),(2.00,0.85)],
}

# ═══════════════════════════════════════════════════════════════════════════
# VTK Legacy ASCII Reader (for FluidX3D output)
# ═══════════════════════════════════════════════════════════════════════════

def read_vtk_structured_points(filepath):
    """Read FluidX3D VTK legacy structured points file.
    Returns: (nx, ny, nz, origin, spacing, velocity_array)
    velocity_array is a list of (vx, vy, vz) tuples in Fortran order (x fastest).
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    nx = ny = nz = 0
    origin = (0.0, 0.0, 0.0)
    spacing = (1.0, 1.0, 1.0)
    velocities = []
    reading_data = False
    line_idx = 0
    
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        
        if line.startswith("DIMENSIONS"):
            parts = line.split()
            nx, ny, nz = int(parts[1]), int(parts[2]), int(parts[3])
        elif line.startswith("ORIGIN"):
            parts = line.split()
            origin = (float(parts[1]), float(parts[2]), float(parts[3]))
        elif line.startswith("SPACING"):
            parts = line.split()
            spacing = (float(parts[1]), float(parts[2]), float(parts[3]))
        elif line.startswith("POINT_DATA"):
            reading_data = False
        elif line.startswith("VECTORS") or line.startswith("SCALARS"):
            reading_data = True
            line_idx += 1  # skip LOOKUP_TABLE line if present
        elif reading_data and line:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    velocities.append((float(parts[0]), float(parts[1]), float(parts[2])))
                except ValueError:
                    pass
        
        line_idx += 1
    
    return nx, ny, nz, origin, spacing, velocities


def probe_velocity(velocities, nx, ny, nz, origin, spacing, x, y, z):
    """Trilinear interpolation of velocity at world coordinate (x, y, z)."""
    ox, oy, oz = origin
    dx, dy, dz = spacing
    
    # Convert world → grid index
    ix = (x - ox) / dx
    iy = (y - oy) / dy
    iz = (z - oz) / dz
    
    # Clamp to grid bounds
    ix = max(0, min(nx-1.001, ix))
    iy = max(0, min(ny-1.001, iy))
    iz = max(0, min(nz-1.001, iz))
    
    i0, j0, k0 = int(ix), int(iy), int(iz)
    i1, j1, k1 = min(i0+1, nx-1), min(j0+1, ny-1), min(k0+1, nz-1)
    fx, fy, fz = ix - i0, iy - j0, iz - k0
    
    def idx(i, j, k):
        return k * (ny * nx) + j * nx + i
    
    def lerp3d(v000, v100, v010, v110, v001, v101, v011, v111):
        return (v000 * (1-fx)*(1-fy)*(1-fz) + v100 * fx*(1-fy)*(1-fz) +
                v010 * (1-fx)*fy*(1-fz) + v110 * fx*fy*(1-fz) +
                v001 * (1-fx)*(1-fy)*fz + v101 * fx*(1-fy)*fz +
                v011 * (1-fx)*fy*fz + v111 * fx*fy*fz)
    
    vx = lerp3d(
        velocities[idx(i0,j0,k0)][0], velocities[idx(i1,j0,k0)][0],
        velocities[idx(i0,j1,k0)][0], velocities[idx(i1,j1,k0)][0],
        velocities[idx(i0,j0,k1)][0], velocities[idx(i1,j0,k1)][0],
        velocities[idx(i0,j1,k1)][0], velocities[idx(i1,j1,k1)][0])
    vy = lerp3d(
        velocities[idx(i0,j0,k0)][1], velocities[idx(i1,j0,k0)][1],
        velocities[idx(i0,j1,k0)][1], velocities[idx(i1,j1,k0)][1],
        velocities[idx(i0,j0,k1)][1], velocities[idx(i1,j0,k1)][1],
        velocities[idx(i0,j1,k1)][1], velocities[idx(i1,j1,k1)][1])
    vz = lerp3d(
        velocities[idx(i0,j0,k0)][2], velocities[idx(i1,j0,k0)][2],
        velocities[idx(i0,j1,k0)][2], velocities[idx(i1,j1,k0)][2],
        velocities[idx(i0,j0,k1)][2], velocities[idx(i1,j0,k1)][2],
        velocities[idx(i0,j1,k1)][2], velocities[idx(i1,j1,k1)][2])
    
    return vx, vy, vz

# ═══════════════════════════════════════════════════════════════════════════
# MAIN: Read VTK and compare
# ═══════════════════════════════════════════════════════════════════════════

# Input: case_dir is connected from Run Simulation's "Case Dir" output
case_dir_str = case_dir if isinstance(case_dir, str) else str(case_dir)
vtk_dir = os.path.join(case_dir_str, "output")

# Find latest VTK file
vtk_files = []
if os.path.isdir(vtk_dir):
    for f in os.listdir(vtk_dir):
        if f.endswith(".vtk"):
            vtk_files.append(os.path.join(vtk_dir, f))

if not vtk_files:
    # Try common FluidX3D output locations
    for alt in [case_dir_str, os.path.dirname(case_dir_str)]:
        for root, dirs, files in os.walk(alt):
            for f in files:
                if f.endswith(".vtk"):
                    vtk_files.append(os.path.join(root, f))

if not vtk_files:
    print("[ERROR] No VTK files found. Run simulation first.")
    a = "ERROR: No VTK output found. Please run the simulation first."
    b = []
    c = []
    d = []
else:
    vtk_file = sorted(vtk_files)[-1]  # Latest file
    print("Reading: " + vtk_file)
    
    nx, ny, nz, origin, spacing, velocities = read_vtk_structured_points(vtk_file)
    print("Grid: {} x {} x {} ({:.1f}M cells)".format(nx, ny, nz, len(velocities)/1e6))
    print("Domain: origin=({:.2f},{:.2f},{:.2f}) spacing=({:.3f},{:.3f},{:.3f})".format(
        origin[0], origin[1], origin[2], spacing[0], spacing[1], spacing[2]))
    
    # Probe velocity at all AIJ measurement positions
    profile_xh = [-1.5, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.5]
    
    sim_points = []
    exp_points_out = []
    diff_curves = []
    
    report = []
    report.append("=" * 60)
    report.append("CityLBM v0.5.0 — AIJ Case A: Simulation vs Experiment")
    report.append("=" * 60)
    report.append("VTK: {}".format(os.path.basename(vtk_file)))
    report.append("Grid: {}x{}x{} cells".format(nx, ny, nz))
    report.append("")
    report.append("{:>20s}  {:>8s}  {:>8s}  {:>8s}  {:>8s}".format(
        "Position", "z/H", "U_sim", "U_exp", "Error%"))
    report.append("-" * 60)
    
    total_error = 0.0
    n_samples = 0
    
    for xh in profile_xh:
        x = xh * H
        
        for zh, u_exp in AIJ_EXP.get(xh, []):
            z = zh * H
            
            # Probe simulation
            try:
                vx_sim, vy_sim, vz_sim = probe_velocity(
                    velocities, nx, ny, nz, origin, spacing, x, 0.0, z)
            except:
                vx_sim = 0.0
            
            u_sim = vx_sim  # X-component = streamwise velocity
            u_sim_norm = u_sim / U_H
            error_pct = abs(u_sim_norm - u_exp) * 100
            
            total_error += error_pct
            n_samples += 1
            
            report.append("{:>20s}  {:>8.2f}  {:>8.3f}  {:>8.3f}  {:>7.1f}%".format(
                "x/H={:+.1f}".format(xh), zh, u_sim_norm, u_exp, error_pct))
            
            # Visualization points — simulated (Y-offset = velocity)
            sim_pt = rg.Point3d(x, u_sim_norm * 0.5, z)
            sim_points.append(sim_pt)
            
            # Experimental points
            exp_pt = rg.Point3d(x, u_exp * 0.5, z)
            exp_points_out.append(exp_pt)
            
            # Difference vector (sim → exp)
            diff_start = rg.Point3d(x, u_sim_norm * 0.5, z)
            diff_end   = rg.Point3d(x, u_exp * 0.5, z)
            diff_curves.append(rg.LineCurve(rg.Line(diff_start, diff_end)))
    
    avg_error = total_error / n_samples if n_samples > 0 else 0
    report.append("-" * 60)
    report.append("AVERAGE ERROR: {:.1f}% ({:d} sample points)".format(avg_error, n_samples))
    report.append("")
    
    # Quality assessment
    if avg_error < 10:
        report.append("QUALITY: EXCELLENT (<10% avg error)")
    elif avg_error < 20:
        report.append("QUALITY: GOOD (<20% avg error, typical for uniform inflow LBM)")
    elif avg_error < 30:
        report.append("QUALITY: ACCEPTABLE (<30%, expected without ABL profile)")
    else:
        report.append("QUALITY: NEEDS IMPROVEMENT (>30% avg error)")
    
    report.append("")
    report.append("NOTES:")
    report.append("- AIJ experiment used power-law ABL profile (alpha=0.25)")
    report.append("- CityLBM currently uses uniform inflow (accounts for ~10-15% error)")
    report.append("- Enable ABL profile in Scene settings to reduce error")
    report.append("- LES model improves wake region accuracy")
    report.append("=" * 60)
    
    a = "\n".join(report)
    b = sim_points       # Simulated velocity points
    c = exp_points_out   # Experimental data points
    d = diff_curves      # Difference vectors
    
    print("\n".join(report))