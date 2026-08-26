# =============================================================================
# CityLBM AIJ Case A — ONE-CLICK VALIDATION (All-in-One GhPython)
# =============================================================================
# Paste into GhPython component. Outputs:
#   a (Text) — Report (setup → simulation → comparison)
#   b (Mesh) — Building geometry
# =============================================================================
# AIJ CFD Guidebook Case A official data:
#   Building: H=2b=0.16m, B=D=b=0.08m
#   Inflow: U_H=4.5 m/s, power-law alpha=0.25
#   Experimental: 26 LDA points at y=0 centerline
# =============================================================================

import os, math, time, re
import clr

# Load CityLBM assembly
gh_libs = os.path.expandvars(r"%APPDATA%\Grasshopper\Libraries")
gha_path = os.path.join(gh_libs, "CityLBM.gha")
if not os.path.exists(gha_path):
    raise Exception("CityLBM.gha not found at: " + gh_libs)
clr.AddReferenceToFileAndPath(gha_path)

clr.AddReference("Grasshopper")
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg
from Rhino.Geometry import Vector3d

# Import CityLBM types
from CityLBM.Core import Scene, GridGenerator, WindProfileType, RoughnessCategory
from CityLBM.Solver import FluidX3DInterface, SimulationSettings

# =============================================================================
# AIJ OFFICIAL SPECIFICATION
# =============================================================================
B_SCALE = 0.08      # Scale unit [m]
H = 2 * B_SCALE      # Building height = 0.16 m
B = B_SCALE           # Width = 0.08 m
D = B_SCALE           # Depth = 0.08 m
U_REF = 4.5           # Reference wind speed at z=H [m/s]
CELL_SIZE = 0.008     # H/20 = 0.008m
TIME_STEPS = 10000    # Production baseline for AIJ official comparison
SAVE_INTERVAL = 500   # VTK save interval

# AIJ experimental wind tunnel data (LDA, y=0 centerline)
AIJ_DATA = [
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

VTK_STEP_RE = re.compile(r"u-(\d+)\.vtk$", re.IGNORECASE)


def find_latest_vtk(case_dir, fallback_output_dir=None):
    """Find latest VTK file for the completed official Case A run."""
    if not case_dir:
        return None, None

    candidates = []
    seen = set()
    search_roots = [case_dir]
    if fallback_output_dir:
        search_roots.append(fallback_output_dir)
    search_roots.extend([
        os.path.join(case_dir, "output"),
        os.path.join(case_dir, "result", "output")
    ])

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
        step, selected = max(step_candidates, key=lambda item: item[0])
        return selected, "u-step:{}".format(step)

    return sorted(candidates)[-1], "fallback"

# =============================================================================
# STEP 1: Generate Building Mesh
# =============================================================================
print("=" * 70)
print("CityLBM AIJ Case A — One-Click Validation")
print("=" * 70)
print("Building: H={:.3f}  B={:.3f}  D={:.3f} (b={:.3f})".format(H, B, D, B_SCALE))
print("Wind: U_H={:.1f} m/s, +X direction".format(U_REF))
print("Grid: dx={:.3f}m (H/{:.0f})".format(CELL_SIZE, H/CELL_SIZE))
print("Steps: {}  Save: {}".format(TIME_STEPS, SAVE_INTERVAL))
print("")

box = rg.Box(rg.Plane.WorldXY,
             rg.Interval(-D/2, D/2),
             rg.Interval(-B/2, B/2),
             rg.Interval(0, H))
mp = rg.MeshingParameters()
mp.MinimumEdgeLength = CELL_SIZE/4
mp.MaximumEdgeLength = CELL_SIZE/2
building_mesh = rg.Mesh.CreateFromBrep(box.ToBrep(), mp)[0]
building_mesh.Weld(0.001)
building_mesh.Compact()
print("Mesh: {} faces".format(building_mesh.Faces.Count))

# =============================================================================
# STEP 2: Create Scene
# =============================================================================
scene = Scene()
scene.Name = "AIJ_CaseA_OneClick"
scene.WindSpeed = U_REF
scene.WindDirection = Vector3d(1.0, 0.0, 0.0)
scene.WindProfile = WindProfileType.PowerLaw
scene.PowerLawAlpha = 0.25
scene.ReferenceHeight = H
scene.RoughnessCategory = RoughnessCategory.C
scene.DomainExtensionRatio = 2.0
scene.GroundHeight = 0.0
scene.AddBuilding(building_mesh)
print("Scene: '{}' created, {} building(s)".format(scene.Name, scene.BuildingCount))

# =============================================================================
# STEP 3: Generate Grid
# =============================================================================
generator = GridGenerator(CELL_SIZE)
grid = generator.Generate(scene)
n_total = grid.Nx * grid.Ny * grid.Nz
print("Grid: {}x{}x{} = {:.1f}M cells".format(
    grid.Nx, grid.Ny, grid.Nz, n_total/1e6))

# =============================================================================
# STEP 4: Simulation Settings
# =============================================================================
settings = SimulationSettings()
settings.Viscosity = 1.5e-5
settings.Density = 1.225
settings.TimeSteps = TIME_STEPS
settings.SaveInterval = SAVE_INTERVAL
settings.EnableSmagorinskyLES = True
settings.SmagorinskyConstantCs = 0.12
settings.SetInletVelocity(Vector3d(1.0, 0.0, 0.0), U_REF)
print("Settings: LES=ON (Cs=0.12), nu={:.1e}, {} steps".format(
    settings.Viscosity, settings.TimeSteps))

# =============================================================================
# STEP 5: Run Simulation
# =============================================================================
print("")
print("=" * 70)
print("RUNNING SIMULATION (this may take 5-30 minutes)...")
print("=" * 70)

interface = FluidX3DInterface()
interface.UseBundledSolver = True

t0 = time.time()
result = interface.RunWithBundledSolver(scene, grid, settings)
elapsed = time.time() - t0

if not result.Success:
    print("SIMULATION FAILED: " + (result.ErrorMessage or "Unknown error"))
    print(result.Log or "")
    a = "SIMULATION FAILED:\n" + (result.ErrorMessage or "Unknown error")
    b = building_mesh
else:
    print("Simulation completed in {:.1f} minutes.".format(elapsed/60))
    print("Case dir: " + (result.CaseDirectory or ""))
    print("Output dir: " + (result.OutputDirectory or ""))

    # =====================================================================
    # STEP 6: Read VTK and Compare
    # =====================================================================
    output_dir = result.OutputDirectory or os.path.join(
        result.CaseDirectory or "", "output")
    vtk_file, vtk_source = find_latest_vtk(result.CaseDirectory or ".", output_dir)
    if not vtk_file:
        a = "Simulation completed but no VTK files found.\nOutput: " + str(output_dir)
        b = building_mesh
    else:
        print("Reading: " + vtk_file + " [" + str(vtk_source) + "]")

        # Read VTK
        with open(vtk_file, 'r') as f:
            lines = f.readlines()
        nx = ny = nz = 1
        ox, oy, oz = 0.0, 0.0, 0.0
        dx, dy, dz = 1.0, 1.0, 1.0
        velocities = []
        point_data_count = None
        reading = False
        vtk_warnings = []
        i = 0
        while i < len(lines):
            ln = lines[i].strip()
            if ln.startswith("DIMENSIONS"):
                p = ln.split(); nx, ny, nz = int(p[1]), int(p[2]), int(p[3])
            elif ln.startswith("ORIGIN"):
                p = ln.split(); ox, oy, oz = float(p[1]), float(p[2]), float(p[3])
            elif ln.startswith("SPACING"):
                p = ln.split(); dx, dy, dz = float(p[1]), float(p[2]), float(p[3])
            elif ln.startswith("POINT_DATA"):
                p = ln.split()
                if len(p) >= 2:
                    try:
                        point_data_count = int(p[1])
                    except:
                        point_data_count = None
                reading = False
            elif ln.startswith("VECTORS"): reading = True; i += 1; continue
            elif ln.startswith(("CELL_DATA", "SCALARS", "LOOKUP_TABLE", "TENSORS", "NORMALS", "FIELD", "TEXTURE_COORDINATES")):
                reading = False
                i += 1
                continue
            elif reading and ln:
                p = ln.split()
                if len(p) >= 3:
                    try: velocities.append((float(p[0]), float(p[1]), float(p[2])))
                    except: pass
            i += 1

        expected_count = nx * ny * nz
        if point_data_count is None:
            point_data_count = expected_count
        if point_data_count != expected_count:
            vtk_warnings.append(
                "POINT_DATA count does not match grid points: POINT_DATA={}, grid={}".format(
                    point_data_count, expected_count
                )
            )
        expected_points = min(point_data_count, expected_count)
        if len(velocities) < expected_points:
            vtk_warnings.append(
                "Incomplete vector list: got {} points, expected {} (using {})".format(
                    len(velocities), expected_points, len(velocities)
                )
            )
        else:
            velocities = velocities[:expected_points]

        # Trilinear probe
        def probe(px, py, pz):
            ix = max(0, min(nx-1.001, (px-ox)/dx))
            iy = max(0, min(ny-1.001, (py-oy)/dy))
            iz = max(0, min(nz-1.001, (pz-oz)/dz))
            i0, j0, k0 = int(ix), int(iy), int(iz)
            i1, j1, k1 = min(i0+1,nx-1), min(j0+1,ny-1), min(k0+1,nz-1)
            fx, fy, fz = ix-i0, iy-j0, iz-k0
            def idx(ii, jj, kk): return kk*ny*nx + jj*nx + ii
            max_index = len(velocities) - 1
            if max_index < 0:
                raise IndexError("No vectors parsed from VTK.")
            for ii in (i0, i1):
                for jj in (j0, j1):
                    for kk in (k0, k1):
                        if idx(ii, jj, kk) > max_index:
                            raise IndexError("VTK sample index out of range.")
            def l(c000,c100,c010,c110,c001,c101,c011,c111):
                return (c000*(1-fx)*(1-fy)*(1-fz)+c100*fx*(1-fy)*(1-fz)+
                        c010*(1-fx)*fy*(1-fz)+c110*fx*fy*(1-fz)+
                        c001*(1-fx)*(1-fy)*fz+c101*fx*(1-fy)*fz+
                        c011*(1-fx)*fy*fz+c111*fx*fy*fz)
            return l(velocities[idx(i0,j0,k0)][0], velocities[idx(i1,j0,k0)][0],
                     velocities[idx(i0,j1,k0)][0], velocities[idx(i1,j1,k0)][0],
                     velocities[idx(i0,j0,k1)][0], velocities[idx(i1,j0,k1)][0],
                     velocities[idx(i0,j1,k1)][0], velocities[idx(i1,j1,k1)][0])

        # Comparison
        errors = []
        report = []
        for warning in vtk_warnings:
            report.append("WARN: " + warning)
        report.append("=" * 70)
        report.append("CityLBM AIJ Case A — Simulation vs Wind Tunnel")
        report.append("=" * 70)
        report.append("")
        report.append("BUILDING: H={:.3f}m  B={:.3f}m  D={:.3f}m  (b={:.3f}m)".format(H,B,D,B_SCALE))
        report.append("GRID:     {}x{}x{} ({:.1f}M cells)".format(nx,ny,nz,len(velocities)/1e6))
        report.append("TIME:     {:.0f}s ({:.1f} min)".format(elapsed, elapsed/60))
        report.append("DATA:     AIJ CFD Guidebook Case A ({} LDA points)".format(len(AIJ_DATA)))
        report.append("")
        report.append("{:>8s} {:>8s} {:>8s} {:>8s} {:>10s} {:>10s} {:>8s}".format(
            "x/b", "z/b", "x(m)", "z(m)", "U_sim", "U_exp", "Err%"))
        report.append("-" * 70)

        failed_points = 0
        for xb, zb, u_exp in AIJ_DATA:
            px, pz = xb * B_SCALE, zb * B_SCALE
            try:
                u_sim = probe(px, 0.0, pz)
            except:
                u_sim = 0.0
                failed_points += 1
            err = abs(u_sim - u_exp) / max(abs(u_exp), 0.01) * 100
            errors.append(err)
            report.append("{:+7.2f} {:>8.3f} {:>8.3f} {:>8.3f} {:>10.3f} {:>10.3f} {:>7.1f}%".format(
                xb, zb, px, pz, u_sim, u_exp, err))

        report.append("-" * 70)
        if failed_points > 0:
            report.append(
                "WARN: {} probe point(s) used fallback 0.0 due VTK sampling issue.".format(
                    failed_points
                )
            )
        avg = sum(errors)/len(errors)
        rms = math.sqrt(sum(e*e for e in errors)/len(errors))
        grade = "EXCELLENT" if avg<20 else "GOOD" if avg<30 else "ACCEPTABLE" if avg<45 else "NEEDS IMPROVEMENT"
        report.append("AVG: {:.1f}% | RMS: {:.1f}% | MAX: {:.1f}% | GRADE: {}".format(
            avg, rms, max(errors), grade))
        report.append("=" * 70)

        a = "\n".join(report)
        b = building_mesh
        print(a)

print("")
print("DONE — see output 'a' for full report")
