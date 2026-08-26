# =============================================================================
# AIJ Case A Post-Process — Simulation vs. Zenodo Wind Tunnel Data
# =============================================================================
# Reads FluidX3D VTK output, probes velocity at experimental measurement
# points, computes error statistics, and outputs comparison report.
#
# References:
#   Zenodo 10.5281/zenodo.15430018 (CC BY 4.0)
#   AIJ Guidebook for CFD Wind Environment around Buildings (2020)
#
# Input:  case_dir (Text)  — Run Simulation "Case Dir" output
# Output: a (Text)         — Comparison report
#         b (Point)        — Simulated velocity points
#         c (Point)        — Experimental data points
#         d (Curve)        — Error vectors
# =============================================================================

import os
import math

import clr
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# =============================================================================
# CONFIGURATION
# =============================================================================

H    = 0.10      # Building height (m)
U_REF = 1.7      # Reference wind speed U_H (m/s)

# Zenodo RS-w_caseI.csv experimental data: (x, y, z, U_exp) at y=0
EXP_DATA = [
    (-0.15, 0, 0.015, 0.976), (-0.15, 0, 0.05, 1.347),
    (-0.15, 0, 0.10, 1.592), (-0.15, 0, 0.15, 1.773),
    (-0.15, 0, 0.20, 1.890), (-0.15, 0, 0.30, 2.013),
    (-0.15, 0, 0.40, 2.088), (-0.15, 0, 0.50, 2.144),
    (-0.05, 0, 0.115, 1.676), (-0.05, 0, 0.15, 1.892),
    (-0.05, 0, 0.20, 1.965), (-0.05, 0, 0.30, 2.040),
    (-0.05, 0, 0.40, 2.099), (-0.05, 0, 0.50, 2.151),
    (0.00, 0, 0.115, 0.181), (0.00, 0, 0.15, 2.043),
    (0.00, 0, 0.20, 2.020), (0.00, 0, 0.30, 2.054),
    (0.00, 0, 0.40, 2.104), (0.00, 0, 0.50, 2.154),
    (0.065, 0, 0.015, -0.295), (0.065, 0, 0.05, -0.180),
    (0.065, 0, 0.10, 0.157), (0.065, 0, 0.15, 1.994),
    (0.065, 0, 0.20, 2.038), (0.065, 0, 0.30, 2.065),
    (0.065, 0, 0.40, 2.109), (0.065, 0, 0.50, 2.156),
    (0.10, 0, 0.015, -0.631), (0.10, 0, 0.05, 0.031),
    (0.10, 0, 0.10, 0.766), (0.10, 0, 0.15, 1.982),
    (0.10, 0, 0.20, 2.043), (0.10, 0, 0.30, 2.069),
    (0.10, 0, 0.40, 2.113), (0.10, 0, 0.50, 2.158),
    (0.20, 0, 0.015, -0.267), (0.20, 0, 0.05, 0.498),
    (0.20, 0, 0.10, 1.323), (0.20, 0, 0.15, 1.924),
    (0.20, 0, 0.20, 2.023), (0.20, 0, 0.30, 2.065),
    (0.20, 0, 0.40, 2.113), (0.20, 0, 0.50, 2.159),
    (0.30, 0, 0.015, 0.222), (0.30, 0, 0.05, 0.935),
    (0.30, 0, 0.10, 1.543), (0.30, 0, 0.15, 1.893),
    (0.30, 0, 0.20, 2.008), (0.30, 0, 0.30, 2.065),
    (0.30, 0, 0.40, 2.113), (0.30, 0, 0.50, 2.159),
    (0.50, 0, 0.015, 0.967), (0.50, 0, 0.05, 1.395),
    (0.50, 0, 0.10, 1.695), (0.50, 0, 0.15, 1.874),
    (0.50, 0, 0.20, 1.990), (0.50, 0, 0.30, 2.060),
    (0.50, 0, 0.40, 2.111), (0.50, 0, 0.50, 2.159),
]

# =============================================================================
# VTK Legacy ASCII Reader
# =============================================================================

def read_vtk(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    nx = ny = nz = 1
    ox = oy = oz = 0.0
    dx = dy = dz = 1.0
    velocities = []
    reading = False
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("DIMENSIONS"):
            p = line.split()
            nx, ny, nz = int(p[1]), int(p[2]), int(p[3])
        elif line.startswith("ORIGIN"):
            p = line.split()
            ox, oy, oz = float(p[1]), float(p[2]), float(p[3])
        elif line.startswith("SPACING"):
            p = line.split()
            dx, dy, dz = float(p[1]), float(p[2]), float(p[3])
        elif line.startswith("POINT_DATA"):
            reading = False
        elif line.startswith("VECTORS"):
            reading = True
            i += 1
        elif reading and line:
            p = line.split()
            if len(p) >= 3:
                try:
                    velocities.append((float(p[0]), float(p[1]), float(p[2])))
                except:
                    pass
        i += 1

    return nx, ny, nz, (ox, oy, oz), (dx, dy, dz), velocities


def trilinear(v, nx, ny, nz, oxyz, dxyz, px, py, pz):
    ox, oy, oz = oxyz
    dx, dy, dz = dxyz

    ix = (px - ox) / dx
    iy = (py - oy) / dy
    iz = (pz - oz) / dz

    ix = max(0, min(nx - 1.001, ix))
    iy = max(0, min(ny - 1.001, iy))
    iz = max(0, min(nz - 1.001, iz))

    i0, j0, k0 = int(ix), int(iy), int(iz)
    i1, j1, k1 = min(i0+1, nx-1), min(j0+1, ny-1), min(k0+1, nz-1)
    fx, fy, fz = ix - i0, iy - j0, iz - k0

    def idx(i, j, k):
        return k * ny * nx + j * nx + i

    def lerp(c000, c100, c010, c110, c001, c101, c011, c111):
        return (c000 * (1-fx)*(1-fy)*(1-fz) + c100 * fx*(1-fy)*(1-fz) +
                c010 * (1-fx)*fy*(1-fz) + c110 * fx*fy*(1-fz) +
                c001 * (1-fx)*(1-fy)*fz + c101 * fx*(1-fy)*fz +
                c011 * (1-fx)*fy*fz + c111 * fx*fy*fz)

    vx = lerp(v[idx(i0,j0,k0)][0], v[idx(i1,j0,k0)][0],
              v[idx(i0,j1,k0)][0], v[idx(i1,j1,k0)][0],
              v[idx(i0,j0,k1)][0], v[idx(i1,j0,k1)][0],
              v[idx(i0,j1,k1)][0], v[idx(i1,j1,k1)][0])
    vy = lerp(v[idx(i0,j0,k0)][1], v[idx(i1,j0,k0)][1],
              v[idx(i0,j1,k0)][1], v[idx(i1,j1,k0)][1],
              v[idx(i0,j0,k1)][1], v[idx(i1,j0,k1)][1],
              v[idx(i0,j1,k1)][1], v[idx(i1,j1,k1)][1])
    vz = lerp(v[idx(i0,j0,k0)][2], v[idx(i1,j0,k0)][2],
              v[idx(i0,j1,k0)][2], v[idx(i1,j1,k0)][2],
              v[idx(i0,j0,k1)][2], v[idx(i1,j0,k1)][2],
              v[idx(i0,j1,k1)][2], v[idx(i1,j1,k1)][2])

    return vx, vy, vz

# =============================================================================
# MAIN
# =============================================================================

case_dir_str = case_dir if isinstance(case_dir, str) else str(case_dir)
vtk_dir = os.path.join(case_dir_str, "output")

vtk_files = []
if os.path.isdir(vtk_dir):
    for f in os.listdir(vtk_dir):
        if f.endswith(".vtk"):
            vtk_files.append(os.path.join(vtk_dir, f))

if not vtk_files:
    for root, dirs, files in os.walk(case_dir_str):
        for f in files:
            if f.endswith(".vtk"):
                vtk_files.append(os.path.join(root, f))

if not vtk_files:
    print("[ERROR] No VTK files found.")
    a = "ERROR: No VTK output. Run simulation first."
    b, c, d = [], [], []
else:
    vtk_file = sorted(vtk_files)[-1]
    print("Reading: " + vtk_file)

    nx, ny, nz, origin, spacing, velocities = read_vtk(vtk_file)
    ncells = len(velocities)
    print("Grid: {}x{}x{} ({:.1f}M cells)".format(nx, ny, nz, ncells/1e6))
    print("Origin: ({:.3f},{:.3f},{:.3f})  Spacing: ({:.3f},{:.3f},{:.3f})".format(
        origin[0], origin[1], origin[2], spacing[0], spacing[1], spacing[2]))

    sim_pts = []
    exp_pts = []
    err_vecs = []

    report = []
    report.append("=" * 60)
    report.append("CityLBM v0.2.1 — AIJ Case A: CFD vs. Wind Tunnel")
    report.append("=" * 60)
    report.append("")
    report.append("VTK: {}".format(os.path.basename(vtk_file)))
    report.append("Grid: {}x{}x{} ({:.1f}M cells)".format(
        nx, ny, nz, ncells/1e6))
    report.append("Exp. data: Zenodo 10.5281/zenodo.15430018")
    report.append("Reference: U_H = {:.1f} m/s at H = {:.2f} m".format(U_REF, H))
    report.append("")
    report.append("{:>8s}  {:>8s}  {:>8s}  {:>10s}  {:>10s}  {:>8s}".format(
        "x/H", "z/H", "z(m)", "U_sim", "U_exp", "Err%"))
    report.append("-" * 60)

    errors = []
    n = 0
    failed_points = 0
    profile_positions = {}

    for x, y, z, u_exp in EXP_DATA:
        try:
            vx, vy, vz = trilinear(velocities, nx, ny, nz,
                                   origin, spacing, x, y, z)
        except Exception as exc:
            failed_points += 1
            xh = x / H
            zh = z / H
            report.append("{:+7.1f}  {:>8.3f}  {:>8.3f}  {:>10s}  {:>10.3f}  {:>8s}".format(
                xh, zh, z, "SKIP", u_exp, "FAILED"))
            continue

        u_sim = vx
        err = abs(u_sim - u_exp)
        err_pct = (err / (abs(u_exp) + 0.01)) * 100
        errors.append(err_pct)
        n += 1

        xh = x / H
        zh = z / H

        report.append("{:+7.1f}  {:>8.3f}  {:>8.3f}  {:>10.3f}  {:>10.3f}  {:>7.1f}%".format(
            xh, zh, z, u_sim, u_exp, err_pct))

        # Visualization points
        sim_pt = rg.Point3d(x, (u_sim / U_REF) * 0.5, z)
        sim_pts.append(sim_pt)
        exp_pt = rg.Point3d(x, (u_exp / U_REF) * 0.5, z)
        exp_pts.append(exp_pt)
        err_vecs.append(rg.LineCurve(
            rg.Line(sim_pt, exp_pt)))

    avg_err = sum(errors) / n if n > 0 else None
    rms_err = math.sqrt(sum(e*e for e in errors)/n) if n > 0 else None

    report.append("-" * 60)
    report.append("")
    report.append("VALID POINTS: {}".format(n))
    report.append("FAILED POINTS: {}".format(failed_points))
    if n > 0:
        report.append("AVERAGE ERROR: {:.1f}%".format(avg_err))
        report.append("RMS ERROR:    {:.1f}%".format(rms_err))
    else:
        report.append("AVERAGE ERROR: unavailable")
        report.append("RMS ERROR:    unavailable")
    report.append("")

    if n == 0:
        grade = "INVALID (no valid sampled probes)"
    elif avg_err < 15:
        grade = "EXCELLENT"
    elif avg_err < 25:
        grade = "GOOD (typical LBM result)"
    elif avg_err < 35:
        grade = "ACCEPTABLE"
    else:
        grade = "NEEDS IMPROVEMENT"

    report.append("QUALITY GRADE: {}".format(grade))
    report.append("")
    report.append("NOTES:")
    report.append("  - Probe sampling failures are skipped, not replaced with zero velocity")
    report.append("  - Wind tunnel used ABL profile; CityLBM uses uniform inflow")
    report.append("  - Smagorinsky LES improves wake region accuracy")
    report.append("  - Cube case: recirculation zone is most challenging region")
    report.append("  - Reference: AIJ CFD Guidebook (2020)")
    report.append("  - Data: Tominaga, Kikumoto, Okaze et al. (Zenodo)")
    report.append("=" * 60)

    a = "\n".join(report)
    b = sim_pts
    c = exp_pts
    d = err_vecs

    print("\n".join(report))
