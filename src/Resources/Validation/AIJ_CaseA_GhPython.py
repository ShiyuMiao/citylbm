# =============================================================================
# AIJ Case A Validation — Single GhPython (Setup + PostProcess)
# =============================================================================
# AIJ CFD Guidebook Case A: Isolated building benchmark
# Official wind tunnel data, building scale b=0.08m
# =============================================================================
# Paste into GhPython component. Set inputs/outputs:
#   Input:  case_dir (Text)      — optional, from Run Simulation "Case Dir"
#   Output: a (Mesh)             — building geometry (connect to Add Buildings)
#   Output: b (Text)             — setup guide / comparison report
# =============================================================================
# TWO MODES:
#   Phase 1: case_dir empty → generates building mesh + setup instructions
#   Phase 2: case_dir has VTK  → reads results + compares with wind tunnel data
# =============================================================================

import os, math
import clr
clr.AddReference("Grasshopper")
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# =====================================================================
# AIJ OFFICIAL SPECIFICATION (from AIJ CFD Guidebook Case A Excel data)
# =====================================================================
B_SCALE = 0.08    # Scale unit b [m]
H = 2 * B_SCALE    # Building height = 0.16 m
B = B_SCALE         # Building width  = 0.08 m
D = B_SCALE         # Building depth  = 0.08 m
U_REF = 4.5        # U_H at z=H [m/s]

AIJ_EXP_DATA = [
    # x/b, z/b, U_exp [m/s]  — vertical centerline (y=0) LDA measurements
    (-0.75, 0.125, 0.208), (-0.75, 0.500, 1.267), (-0.75, 1.000, 1.409),
    (-0.75, 1.500, 1.701), (-0.75, 1.750, 2.067), (-0.75, 2.000, 3.044),
    (-0.75, 2.125, 3.654), (-0.75, 2.375, 4.539), (-0.75, 2.750, 4.962),
    (-0.75, 3.500, 5.351),
    (-0.50, 2.125, 4.281), (-0.50, 2.375, 4.937),
    (-0.50, 2.750, 5.138), (-0.50, 3.500, 5.402),
    (-0.25, 2.125, 1.681), (-0.25, 2.375, 5.568),
    (-0.25, 2.750, 5.268), (-0.25, 3.500, 5.416),
    ( 0.00, 2.125, 1.250), ( 0.00, 2.375, 5.461),
    ( 0.00, 2.750, 5.307), ( 0.00, 3.500, 5.402),
    ( 0.50, 2.125, 2.743), ( 0.50, 2.375, 4.824),
    ( 0.50, 2.750, 5.212), ( 0.50, 3.500, 5.392),
]

# =====================================================================
# STEP 1: Generate AIJ Building Geometry (always)
# =====================================================================
box = rg.Box(
    rg.Plane.WorldXY,
    rg.Interval(-D/2, D/2),
    rg.Interval(-B/2, B/2),
    rg.Interval(0, H),
)
mp = rg.MeshingParameters()
mp.MinimumEdgeLength = 0.002
mp.MaximumEdgeLength = 0.004
building_mesh = rg.Mesh.CreateFromBrep(box.ToBrep(), mp)[0]
building_mesh.Weld(0.001)
building_mesh.Compact()

# =====================================================================
# STEP 2: Check if we're in Setup or PostProcess mode
# =====================================================================
case_dir_str = ""

# Check if case_dir input is connected and has a value
try:
    if case_dir is not None:
        if isinstance(case_dir, str):
            case_dir_str = case_dir
        else:
            case_dir_str = str(case_dir)
except NameError:
    pass  # case_dir not connected — setup mode

vtk_files = []
if case_dir_str:
    vtk_dir = os.path.join(case_dir_str, "output")
    if os.path.isdir(vtk_dir):
        for f in os.listdir(vtk_dir):
            if f.endswith(".vtk"):
                vtk_files.append(os.path.join(vtk_dir, f))
    if not vtk_files:
        for root, dirs, files in os.walk(case_dir_str):
            for f in files:
                if f.endswith(".vtk"):
                    vtk_files.append(os.path.join(root, f))

if vtk_files:
    # =================================================================
    # POSTPROCESS MODE — VTK found, run comparison
    # =================================================================
    vtk_file = sorted(vtk_files)[-1]

    # VTK reader
    with open(vtk_file, 'r') as f:
        lines = f.readlines()
    nx = ny = nz = 1
    ox, oy, oz = 0.0, 0.0, 0.0
    dx, dy, dz = 1.0, 1.0, 1.0
    velocities = []
    reading = False
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("DIMENSIONS"):
            p = ln.split(); nx, ny, nz = int(p[1]), int(p[2]), int(p[3])
        elif ln.startswith("ORIGIN"):
            p = ln.split(); ox, oy, oz = float(p[1]), float(p[2]), float(p[3])
        elif ln.startswith("SPACING"):
            p = ln.split(); dx, dy, dz = float(p[1]), float(p[2]), float(p[3])
        elif ln.startswith("POINT_DATA"): reading = False
        elif ln.startswith("VECTORS"): reading = True; i += 1
        elif reading and ln:
            p = ln.split()
            if len(p) >= 3:
                try: velocities.append((float(p[0]), float(p[1]), float(p[2])))
                except: pass
        i += 1

    # Trilinear interpolation
    def probe(px, py, pz):
        ix = max(0, min(nx-1.001, (px-ox)/dx))
        iy = max(0, min(ny-1.001, (py-oy)/dy))
        iz = max(0, min(nz-1.001, (pz-oz)/dz))
        i0, j0, k0 = int(ix), int(iy), int(iz)
        i1, j1, k1 = min(i0+1,nx-1), min(j0+1,ny-1), min(k0+1,nz-1)
        fx, fy, fz = ix-i0, iy-j0, iz-k0
        def idx(ii, jj, kk): return kk*ny*nx + jj*nx + ii
        def l(c000,c100,c010,c110,c001,c101,c011,c111):
            return (c000*(1-fx)*(1-fy)*(1-fz)+c100*fx*(1-fy)*(1-fz)+
                    c010*(1-fx)*fy*(1-fz)+c110*fx*fy*(1-fz)+
                    c001*(1-fx)*(1-fy)*fz+c101*fx*(1-fy)*fz+
                    c011*(1-fx)*fy*fz+c111*fx*fy*fz)
        return l(velocities[idx(i0,j0,k0)][0], velocities[idx(i1,j0,k0)][0],
                 velocities[idx(i0,j1,k0)][0], velocities[idx(i1,j1,k0)][0],
                 velocities[idx(i0,j0,k1)][0], velocities[idx(i1,j0,k1)][0],
                 velocities[idx(i0,j1,k1)][0], velocities[idx(i1,j1,k1)][0])

    # Run comparison
    errors = []
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("CityLBM — AIJ Case A: Simulation vs Wind Tunnel")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append("BUILDING: H={:.3f}m  B={:.3f}m  D={:.3f}m (b={:.3f}m)".format(H,B,D,B_SCALE))
    report_lines.append("INFLOW:   U_H={:.1f} m/s, power-law alpha=0.25".format(U_REF))
    report_lines.append("VTK:      {} (grid {}x{}x{})".format(os.path.basename(vtk_file), nx, ny, nz))
    report_lines.append("DATA:     AIJ CFD Guidebook Case A (LDA, {} points)".format(len(AIJ_EXP_DATA)))
    report_lines.append("")
    report_lines.append("{:>8s} {:>8s} {:>8s} {:>8s} {:>8s} {:>10s} {:>10s} {:>8s}".format(
        "x/b", "z/b", "x(m)", "z(m)", "U_sim", "U_exp", "U_norm", "Err%"))
    report_lines.append("-" * 70)

    for xb, zb, u_exp in AIJ_EXP_DATA:
        px, pz = xb * B_SCALE, zb * B_SCALE
        try: u_sim = probe(px, 0.0, pz)
        except: u_sim = 0.0
        err = abs(u_sim - u_exp) / max(abs(u_exp), 0.01) * 100
        errors.append(err)
        report_lines.append("{:+7.2f} {:>8.3f} {:>8.3f} {:>8.3f} {:>8.3f} {:>10.3f} {:>10.3f} {:>7.1f}%".format(
            xb, zb, px, pz, u_sim, u_exp, u_exp/U_REF, err))

    report_lines.append("-" * 70)
    avg_err = sum(errors)/len(errors)
    rms_err = math.sqrt(sum(e*e for e in errors)/len(errors))
    report_lines.append("AVG ERROR: {:.1f}%   RMS: {:.1f}%   MAX: {:.1f}%".format(avg_err, rms_err, max(errors)))
    report_lines.append("GRADE: " + ("EXCELLENT" if avg_err<20 else "GOOD" if avg_err<30 else "ACCEPTABLE" if avg_err<45 else "NEEDS IMPROVEMENT"))
    report_lines.append("=" * 70)

    a = building_mesh
    b = "\n".join(report_lines)

else:
    # =================================================================
    # SETUP MODE — no VTK yet, output building + instructions
    # =================================================================
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("CityLBM — AIJ Case A Validation Setup")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append("BUILDING: H={:.3f}m  B={:.3f}m  D={:.3f}m  (b={:.3f}m)".format(H,B,D,B_SCALE))
    report_lines.append("ASPECT:   H:B:D = 2:1:1  (AIJ standard)")
    report_lines.append("WIND:     U_H = {:.1f} m/s, +X direction".format(U_REF))
    report_lines.append("PROFILE:  Power-law ABL, alpha = 0.25 (suburban)")
    report_lines.append("EXP DATA: {} LDA points from AIJ CFD Guidebook Case A".format(len(AIJ_EXP_DATA)))
    report_lines.append("")
    report_lines.append("=== CITYLBM COMPONENT SETTINGS ===")
    report_lines.append("")
    report_lines.append("Create Scene:")
    report_lines.append("  Wind Speed (V):      {:.1f}".format(U_REF))
    report_lines.append("  Wind Direction (D):  (1, 0, 0)")
    report_lines.append("  Domain Extension:    2.0")
    report_lines.append("")
    report_lines.append("Grid Generator:")
    report_lines.append("  Cell Size:           0.008  (H/20)")
    report_lines.append("")
    report_lines.append("Run Simulation:")
    report_lines.append("  Mode:                3 (async background)")
    report_lines.append("  Time Steps:          10000")
    report_lines.append("  Save Interval:       500")
    report_lines.append("")
    report_lines.append("=== WIRING ===")
    report_lines.append("  Output a (Mesh)  ->  Add Buildings (B)")
    report_lines.append("  Create Scene     ->  Add Buildings (S)")
    report_lines.append("  Add Buildings    ->  Grid Generator")
    report_lines.append("  Grid Generator   ->  Run Simulation")
    report_lines.append("  Run Sim Case Dir ->  THIS GhPython (case_dir)")
    report_lines.append("")
    report_lines.append("After simulation completes, reconnect Case Dir")
    report_lines.append("to this GhPython and Run again for comparison.")
    report_lines.append("=" * 70)

    a = building_mesh
    b = "\n".join(report_lines)

print(b)