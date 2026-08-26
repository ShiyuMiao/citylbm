# =============================================================================
# AIJ Case A Official Post-Process — Simulation vs AIJ Wind Tunnel Data
# =============================================================================
# Official data from: AIJ CFD Guidebook Case A (Building scale b=0.08m)
# Building: H=2b=0.16m, B=b=0.08m, D=b=0.08m
# Inflow: power-law profile U(z) = U_H * (z/H)^0.25, U_H ~ 4.5 m/s
# =============================================================================
# Input:  case_dir (Text) — Run Simulation "Case Dir" output
# Output: a (Text)  — Comparison report
#         b (Point) — Simulated velocity points
#         c (Point) — Experimental data points
#         d (Curve) — Error vectors
# =============================================================================

import os, math, re
import clr
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# =============================================================================
# AIJ OFFICIAL EXPERIMENTAL DATA — Vertical Section at y=0
# =============================================================================
# Source: AIJ CFD Guidebook, Case A wind tunnel measurements
# Format: (x/b, y/b, z/b, U [m/s])
# Building scale: b = 0.08m, H = 2b = 0.16m
# Reference velocity: U_H ~ 4.5 m/s at z = H = 2b

B_SCALE = 0.08    # Scale unit b [m]
H = 2 * B_SCALE    # Building height = 0.16 m
B = B_SCALE         # Building width  = 0.08 m
D = B_SCALE         # Building depth  = 0.08 m
U_REF = 4.5        # Reference velocity at z=H [m/s]

# Vertical section data (y/b=0 centerline plane)
AIJ_DATA = [
    # x/b=-0.75 (upstream near-field)
    (-0.75, 0.0, 0.125, 0.208),
    (-0.75, 0.0, 0.500, 1.267),
    (-0.75, 0.0, 1.000, 1.409),
    (-0.75, 0.0, 1.500, 1.701),
    (-0.75, 0.0, 1.750, 2.067),
    (-0.75, 0.0, 2.000, 3.044),
    (-0.75, 0.0, 2.125, 3.654),
    (-0.75, 0.0, 2.375, 4.539),
    (-0.75, 0.0, 2.750, 4.962),
    (-0.75, 0.0, 3.500, 5.351),
    # x/b=-0.5 (building windward edge)
    (-0.50, 0.0, 2.125, 4.281),
    (-0.50, 0.0, 2.375, 4.937),
    (-0.50, 0.0, 2.750, 5.138),
    (-0.50, 0.0, 3.500, 5.402),
    # x/b=-0.25 (above building front)
    (-0.25, 0.0, 2.125, 1.681),
    (-0.25, 0.0, 2.375, 5.568),
    (-0.25, 0.0, 2.750, 5.268),
    (-0.25, 0.0, 3.500, 5.416),
    # x/b=0.0 (building center)
    (0.00, 0.0, 2.125, 1.250),
    (0.00, 0.0, 2.375, 5.461),
    (0.00, 0.0, 2.750, 5.307),
    (0.00, 0.0, 3.500, 5.402),
    # x/b=0.5 (leeward edge)
    (0.50, 0.0, 2.125, 2.743),
    (0.50, 0.0, 2.375, 4.824),
    (0.50, 0.0, 2.750, 5.212),
    (0.50, 0.0, 3.500, 5.392),
]

# =============================================================================
# VTK READER
# =============================================================================

def read_vtk(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    nx = ny = nz = 1
    ox, oy, oz = 0.0, 0.0, 0.0
    dx, dy, dz = 1.0, 1.0, 1.0
    point_data_count = None
    velocities = []
    reading = False
    warnings = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if line.startswith("DIMENSIONS"):
            p = line.split()
            if len(p) >= 4:
                nx, ny, nz = int(p[1]), int(p[2]), int(p[3])
            i += 1
            continue

        if line.startswith("ORIGIN"):
            p = line.split()
            if len(p) >= 4:
                ox, oy, oz = float(p[1]), float(p[2]), float(p[3])
            i += 1
            continue

        if line.startswith("SPACING"):
            p = line.split()
            if len(p) >= 4:
                dx, dy, dz = float(p[1]), float(p[2]), float(p[3])
            i += 1
            continue

        if line.startswith("POINT_DATA"):
            p = line.split()
            if len(p) >= 2:
                try:
                    point_data_count = int(p[1])
                except:
                    point_data_count = None
            reading = False
            i += 1
            continue

        if line.startswith("VECTORS"):
            reading = True
            i += 1
            continue

        if line.startswith((
            "CELL_DATA", "SCALARS", "LOOKUP_TABLE",
            "TENSORS", "NORMALS", "FIELD", "TEXTURE_COORDINATES"
        )):
            reading = False
            i += 1
            continue

        if reading:
            p = line.split()
            if len(p) >= 3:
                try:
                    velocities.append((float(p[0]), float(p[1]), float(p[2])))
                except:
                    reading = False
            else:
                reading = False

        i += 1

    if point_data_count is None:
        point_data_count = nx * ny * nz
    expected_count = nx * ny * nz
    if point_data_count != expected_count:
        warnings.append(
            "POINT_DATA count does not match grid points: POINT_DATA={}, grid={}".format(
                point_data_count, expected_count
            )
        )

    expected = min(point_data_count, expected_count)
    if expected > len(velocities):
        warnings.append(
            "Incomplete vector list: got {} points, expected {} (using {} point(s))".format(
                len(velocities), expected, len(velocities)
            )
        )
    elif expected < len(velocities):
        velocities = velocities[:expected]

    return nx, ny, nz, (ox, oy, oz), (dx, dy, dz), velocities, warnings


def trilinear(v, nx, ny, nz, oxyz, dxyz, px, py, pz):
    ox, oy, oz = oxyz
    dx, dy, dz = dxyz
    ix = max(0, min(nx-1.001, (px-ox)/dx))
    iy = max(0, min(ny-1.001, (py-oy)/dy))
    iz = max(0, min(nz-1.001, (pz-oz)/dz))
    i0, j0, k0 = int(ix), int(iy), int(iz)
    i1, j1, k1 = min(i0+1,nx-1), min(j0+1,ny-1), min(k0+1,nz-1)
    fx, fy, fz = ix-i0, iy-j0, iz-k0

    def idx(i, j, k): return k*ny*nx + j*nx + i

    max_index = len(v) - 1
    if max_index < 0:
        raise IndexError("No vectors parsed from VTK.")

    for ii in (i0, i1):
        for jj in (j0, j1):
            for kk in (k0, k1):
                if idx(ii, jj, kk) > max_index:
                    raise IndexError("VTK sample index out of range.")

    def lerp(c000,c100,c010,c110,c001,c101,c011,c111):
        return (c000*(1-fx)*(1-fy)*(1-fz)+c100*fx*(1-fy)*(1-fz)+
                c010*(1-fx)*fy*(1-fz)+c110*fx*fy*(1-fz)+
                c001*(1-fx)*(1-fy)*fz+c101*fx*(1-fy)*fz+
                c011*(1-fx)*fy*fz+c111*fx*fy*fz)

    vx = lerp(v[idx(i0,j0,k0)][0],v[idx(i1,j0,k0)][0],
              v[idx(i0,j1,k0)][0],v[idx(i1,j1,k0)][0],
              v[idx(i0,j0,k1)][0],v[idx(i1,j0,k1)][0],
              v[idx(i0,j1,k1)][0],v[idx(i1,j1,k1)][0])
    return vx, 0.0, 0.0


VTK_STEP_RE = re.compile(r"u-(\d+)\.vtk$", re.IGNORECASE)


def find_latest_vtk(case_dir):
    """Find latest velocity VTK file for AIJ Case A post-process.

    Prefer solver naming pattern u-<step>.vtk and fallback to latest vtk.
    """
    if not case_dir:
        return None, None

    candidates = []
    seen = set()

    search_roots = [
        case_dir,
        os.path.join(case_dir, "output"),
        os.path.join(case_dir, "result", "output")
    ]

    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            if name.lower().endswith(".vtk"):
                full = os.path.join(root, name)
                if full not in seen:
                    candidates.append(full)
                    seen.add(full)

    if not candidates:
        for root, _, files in os.walk(case_dir):
            for name in files:
                if name.lower().endswith(".vtk"):
                    full = os.path.join(root, name)
                    if full not in seen:
                        candidates.append(full)
                        seen.add(full)

    if not candidates:
        return None, None

    step_candidates = []
    for path in candidates:
        m = VTK_STEP_RE.match(os.path.basename(path))
        if m:
            step_candidates.append((int(m.group(1)), path))

    if step_candidates:
        step, path = max(step_candidates, key=lambda item: item[0])
        return path, "u-step:{}".format(step)

    return sorted(candidates)[-1], "fallback"


# =============================================================================
# MAIN
# =============================================================================

case_dir_str = case_dir if isinstance(case_dir, str) else str(case_dir)
vtk_file, vtk_source = find_latest_vtk(case_dir_str)

if not vtk_file:
    print("[ERROR] No VTK files found.")
    a = "ERROR: No VTK output. Run simulation first."
    b, c, d = [], [], []
else:
    print("Reading: {} [{}]".format(vtk_file, vtk_source))
    nx, ny, nz, origin, spacing, velocities, vtk_warnings = read_vtk(vtk_file)
    ncells = len(velocities)
    print("Grid: {}x{}x{} ({:.1f}M cells)".format(nx, ny, nz, ncells/1e6))
    for warning in vtk_warnings:
        print("[WARN] {}".format(warning))

    sim_pts, exp_pts, err_vecs = [], [], []
    report = []
    report.append("=" * 70)
    report.append("CityLBM v0.2.1 — AIJ Case A Official Validation")
    report.append("=" * 70)
    report.append("")
    report.append("BUILDING: H={:.2f}m, B={:.2f}m, D={:.2f}m (b={:.3f}m)".format(H,B,D,B_SCALE))
    report.append("INFLOW:   U_H={:.1f} m/s, power-law alpha=0.25".format(U_REF))
    report.append("VTK:      {}".format(os.path.basename(vtk_file)))
    report.append("GRID:     {}x{}x{} ({:.1f}M cells)".format(nx,ny,nz,ncells/1e6))
    report.append("")
    report.append("DATA SOURCE: AIJ CFD Guidebook Case A Wind Tunnel")
    report.append("  Vertical section at y/b=0 (centerline plane)")
    report.append("  {} measurement points, LDA sampling".format(len(AIJ_DATA)))
    report.append("")
    report.append("{:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>10s} {:>10s} {:>8s}".format(
        "x/b", "y/b", "z/b", "z(m)", "x(m)", "U_sim", "U_exp", "Err%"))
    report.append("-" * 70)

    errors = []
    failed_points = 0
    for xb, yb, zb, u_exp in AIJ_DATA:
        px = xb * B_SCALE
        py = yb * B_SCALE
        pz = zb * B_SCALE
        try:
            vx, _, _ = trilinear(velocities, nx, ny, nz, origin, spacing, px, py, pz)
        except:
            vx = 0.0
            failed_points += 1
        u_sim = vx
        err = abs(u_sim - u_exp) / max(abs(u_exp), 0.01) * 100
        errors.append(err)
        report.append("{:+7.2f} {:>8.3f} {:>8.3f} {:>8.3f} {:>8.3f} {:>10.3f} {:>10.3f} {:>7.1f}%".format(
            xb, yb, zb, pz, px, u_sim, u_exp, err))
        sim_pts.append(rg.Point3d(px, u_sim/U_REF*0.5, pz))
        exp_pts.append(rg.Point3d(px, u_exp/U_REF*0.5, pz))
        err_vecs.append(rg.LineCurve(rg.Line(
            rg.Point3d(px, u_sim/U_REF*0.5, pz),
            rg.Point3d(px, u_exp/U_REF*0.5, pz))))

    avg_err = sum(errors) / len(errors)
    rms_err = math.sqrt(sum(e*e for e in errors) / len(errors))

    report.append("-" * 70)
    if failed_points > 0:
        report.append("WARNINGS: {} probe point(s) used fallback 0.0 due VTK sampling issue.".format(failed_points))
        report.append("  Recommend re-checking VTK parse consistency and POINT_DATA/GRID metadata.")
    report.append("")
    report.append("POINTS:       {}".format(len(AIJ_DATA)))
    report.append("AVG ERROR:    {:.1f}%".format(avg_err))
    report.append("RMS ERROR:    {:.1f}%".format(rms_err))
    report.append("MAX ERROR:    {:.1f}%".format(max(errors)))
    report.append("")

    if avg_err < 20:
        grade = "EXCELLENT — CFD matches wind tunnel closely"
    elif avg_err < 30:
        grade = "GOOD — acceptable for engineering applications"
    elif avg_err < 45:
        grade = "ACCEPTABLE — within typical LBM error bounds"
    else:
        grade = "NEEDS IMPROVEMENT — check grid resolution / BCs"

    report.append("GRADE: {}".format(grade))
    report.append("")
    report.append("NOTES:")
    report.append("  - AIJ experiment uses ABL power-law profile (alpha=0.25)")
    report.append("  - CityLBM uniform inflow contributes systematic error")
    report.append("  - Recirculation zone (x/b=0.5, z/b<2) is most challenging")
    report.append("  - Windward edge (x/b=-0.25, z/b=2.125) shows strong shear")
    report.append("  - Grid resolution H/20 recommended per AIJ guidelines")
    report.append("")
    report.append("PRECONDITIONS CHECK:")
    report.append("  [ ] Building: H=0.16m, B=0.08m, D=0.08m (b=0.08m)")
    report.append("  [ ] Building centered at origin, base at Z=0")
    report.append("  [ ] Wind: U_H=4.5m/s, +X direction")
    report.append("  [ ] Cell size: 0.008m (H/20)")
    report.append("  [ ] Domain: upstream >=5H, downstream >=15H")
    report.append("  [ ] LES: Smagorinsky Cs=0.12")
    report.append("  [ ] Time steps: >=10000 for convergence")
    report.append("=" * 70)

    a = "\n".join(report)
    b = sim_pts
    c = exp_pts
    d = err_vecs
    print("\n".join(report))
