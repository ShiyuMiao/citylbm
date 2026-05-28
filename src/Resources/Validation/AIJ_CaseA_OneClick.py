# =============================================================================
# CityLBM v0.5.0 — AIJ Case A One-Click Validation
# =============================================================================
# Paste this into a GhPython component in Grasshopper.
#
# Outputs:
#   a (Mesh)   — AIJ Case A building mesh
#   b (Text)   — Validation report
#   c (Curve)  — Vertical measurement profile lines (9 positions)
#   d (Point)  — Experimental data comparison points
#
# After running: connect "a" → Add Buildings → Grid Generator → Run Simulation
# Then use a second GhPython with AIJ_CaseA_PostProcess.py to compare results.
# =============================================================================

import clr
import sys
import os
import math
from collections import OrderedDict

# ── Load CityLBM assembly ──────────────────────────────────────────────────
gh_libs = os.path.expandvars(r"%APPDATA%\Grasshopper\Libraries")
gha_path = os.path.join(gh_libs, "CityLBM.gha")
if os.path.exists(gha_path):
    clr.AddReferenceToFileAndPath(gha_path)
else:
    print("[WARN] CityLBM.gha not found at: " + gh_libs)

clr.AddReference("Grasshopper")
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Edit these values for different test scenarios
# ═══════════════════════════════════════════════════════════════════════════

H  = 0.2    # Building height (m) — H:B:D = 2:1:1 (AIJ standard)
B  = 0.1    # Building width  (m, Y-direction)
D  = 0.1    # Building depth  (m, X-direction, along wind)

WIND_SPEED      = 5.0
WIND_DIR_X      = 1.0
WIND_DIR_Y      = 0.0
WIND_DIR_Z      = 0.0

CELL_SIZE       = 0.01     # H/20 = 20 cells/building-height
TIME_STEPS      = 10000
SAVE_INTERVAL   = 500
ENABLE_LES      = True
SMAGORINSKY_CS  = 0.12

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Generate Building Geometry
# ═══════════════════════════════════════════════════════════════════════════

box = rg.Box(
    rg.Plane.WorldXY,
    rg.Interval(-D/2, D/2),
    rg.Interval(-B/2, B/2),
    rg.Interval(0, H)
)

mp = rg.MeshingParameters()
mp.MinimumEdgeLength = CELL_SIZE / 2
mp.MaximumEdgeLength = CELL_SIZE
building_mesh = rg.Mesh.CreateFromBrep(box.ToBrep(), mp)[0]
building_mesh.Weld(0.001)
building_mesh.Compact()

print("=" * 60)
print("CityLBM v0.5.0 — AIJ Case A Validation Setup")
print("=" * 60)
print("Building: {:.2f}x{:.2f}x{:.2f} m  |  Faces: {}".format(
    H, B, D, building_mesh.Faces.Count))
print("Wind: {:.0f} m/s from +X  |  Grid: {:.3f} m (H/{:.0f})".format(
    WIND_SPEED, CELL_SIZE, H/CELL_SIZE))
print("LES: {} (Cs={:.2f})  |  Steps: {} (save/{})".format(
    "ON" if ENABLE_LES else "OFF", SMAGORINSKY_CS, TIME_STEPS, SAVE_INTERVAL))

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Vertical Measurement Profiles (AIJ standard positions)
# ═══════════════════════════════════════════════════════════════════════════

profile_positions = OrderedDict([
    ("-1.5H upstream",     -1.5),
    ("-0.5H windward",     -0.5),
    (" 0.0H above bldg",    0.0),
    (" 0.5H leeward",       0.5),
    (" 1.0H near wake",     1.0),
    (" 2.0H near wake",     2.0),
    (" 3.0H mid wake",      3.0),
    (" 4.0H far wake",      4.0),
    (" 5.5H far wake",      5.5),
])

profile_curves = []
for name, xh in profile_positions.items():
    x = xh * H
    pts = [rg.Point3d(x, 0, zh * H) for zh in [i*0.1 for i in range(21)]]
    profile_curves.append(rg.PolylineCurve(pts))
    print("  Profile {}: x={:.2f}m".format(name, x))

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Experimental Data Points (AIJ CFD Guidebook Case A)
# ═══════════════════════════════════════════════════════════════════════════

aij_data = {
    # x/H : [(z/H, U/U_H), ...]
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

exp_points = []
for xh, measurements in aij_data.items():
    x = xh * H
    for zh, u_uh in measurements:
        pt = rg.Point3d(x, u_uh * 0.5, zh * H)  # Y-offset = velocity
        exp_points.append(pt)

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Generate Report
# ═══════════════════════════════════════════════════════════════════════════

report = []
report.append("=" * 60)
report.append("CityLBM v0.5.0 — AIJ Case A Validation Setup")
report.append("=" * 60)
report.append("")
report.append("BUILDING: {:.3f} x {:.3f} x {:.3f} m (H:B:D = 2:1:1)".format(H, B, D))
report.append("WIND:    {:.0f} m/s from +X (Uniform inflow)".format(WIND_SPEED))
report.append("GRID:    {:.3f} m cell size (H/{:.0f})".format(CELL_SIZE, H/CELL_SIZE))
report.append("STEPS:   {} steps, save every {}".format(TIME_STEPS, SAVE_INTERVAL))
report.append("LES:     {} (Cs={:.2f})".format("ON" if ENABLE_LES else "OFF", SMAGORINSKY_CS))
report.append("")
report.append("NEXT STEPS:")
report.append("  1. Connect output 'a' (Mesh) to 'Add Buildings'")
report.append("  2. Create Scene → Add Buildings → Grid Generator → Run Simulation")
report.append("  3. Run Simulation Mode 3 (async), wait for completion")
report.append("  4. Use AIJ_CaseA_PostProcess.py in a new GhPython to compare")
report.append("")
report.append("MEASUREMENT PROFILES: 9 vertical lines at x/H = -1.5 to 5.5")
report.append("EXPERIMENTAL DATA: AIJ CFD Guidebook Case A (wind tunnel)")
report.append("")
report.append("EXPECTED RESULTS (AIJ benchmark):")
report.append("  Windward:    U/U_H < 0.3 at x/H = -0.5")
report.append("  Above bldg:  flow acceleration + separation bubble")
report.append("  Leeward:     recirculation (U < 0 at x/H = 0.5)")
report.append("  Far wake:    70% recovery at x/H = 5.5")
report.append("=" * 60)

# ═══════════════════════════════════════════════════════════════════════════
# OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════

a = building_mesh       # → Add Buildings (B input)
b = "\n".join(report)   # → Panel
c = profile_curves       # → Curve param (visualize in Rhino)
d = exp_points           # → Point param