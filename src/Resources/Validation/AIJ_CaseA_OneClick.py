# =============================================================================
# AIJ Case A Validation — CityLBM v0.2.1
# One-Click Building Geometry + Experimental Data Setup
# =============================================================================
# Based on: AIJ CFD Guidebook Case A (Isolated Building Benchmark)
# Experimental data: Zenodo 10.5281/zenodo.15430018 (CC BY 4.0)
#   Tominaga, Kikumoto, Okaze et al. — AIJ UWE Benchmark Dataset
# =============================================================================
# Paste into GhPython component (outputs: Mesh, Text, Curve, Point)
#  a (Mesh)  -> Add Buildings (B input)
#  b (Text)  -> Panel (report)
#  c (Curve) -> Measurement profile lines (visualize in Rhino)
#  d (Point) -> Experimental data points (Y-offset = velocity)
# =============================================================================

import os
import math

import clr
clr.AddReference("Grasshopper")
clr.AddReference("RhinoCommon")
import Rhino.Geometry as rg

# =============================================================================
# CONFIGURATION — AIJ Case A (Cube Building)
# =============================================================================
# Reference: AIJ Guidebook for CFD Wind Environment around Buildings (2020)
# Building:   H = B = D = 0.10 m  (cube)
# Inflow:     U_H = 1.7 m/s at z=H
# =============================================================================

H   = 0.10    # Building height (m)
B   = 0.10    # Building width  (m, Y-direction)
D   = 0.10    # Building depth  (m, X-direction, along wind)

U_REF       = 1.7       # Reference wind speed U_H (m/s)

CELL_SIZE   = 0.005     # H/20 = 0.005m (20 cells per cube height)
TIME_STEPS  = 10000     # Total simulation steps
SAVE_INTVL  = 500       # VTK output interval
SMAG_CS     = 0.12      # Smagorinsky constant for LES
DOM_EXT     = 2.0       # Domain extension (>=2.0 for AIJ compliance)

# =============================================================================
# STEP 1: Building Geometry (Cube 0.1 x 0.1 x 0.1 m)
# =============================================================================

box = rg.Box(
    rg.Plane.WorldXY,
    rg.Interval(-D/2, D/2),    # X: streamwise
    rg.Interval(-B/2, B/2),    # Y: spanwise
    rg.Interval(0, H),         # Z: base at ground
)

mp = rg.MeshingParameters()
mp.MinimumEdgeLength = CELL_SIZE / 2
mp.MaximumEdgeLength = CELL_SIZE
building_mesh = rg.Mesh.CreateFromBrep(box.ToBrep(), mp)[0]
building_mesh.Weld(0.001)
building_mesh.Compact()

print("=" * 60)
print("CityLBM v0.2.1 — AIJ Case A Validation (Cube)")
print("=" * 60)
print("Building: {:.2f} x {:.2f} x {:.2f} m (cube)".format(H, B, D))
print("Wind: U_H = {:.1f} m/s from +X".format(U_REF))
print("Grid: {:.3f} m cell size (H/{:.0f})".format(CELL_SIZE, H/CELL_SIZE))
print("LES: ON (Smagorinsky Cs={:.2f})".format(SMAG_CS))
print("Steps: {}  |  Save: {}  |  Domain Ext: {}".format(
    TIME_STEPS, SAVE_INTVL, DOM_EXT))
print("")

# =============================================================================
# STEP 2: Experimental Data from Zenodo (RS-w_caseI.csv)
# =============================================================================
# AIJ wind tunnel measurements at y=0 centerline plane
# Format: (x, y, z, U, V, W, k) — all in SI units

exp_data = [
    # x=-0.15 (x/H=-1.5, upstream)
    (-0.15, 0, 0.015, 0.976), (-0.15, 0, 0.05, 1.347),
    (-0.15, 0, 0.10, 1.592), (-0.15, 0, 0.15, 1.773),
    (-0.15, 0, 0.20, 1.890), (-0.15, 0, 0.30, 2.013),
    (-0.15, 0, 0.40, 2.088), (-0.15, 0, 0.50, 2.144),
    # x=-0.05 (x/H=-0.5, windward face)
    (-0.05, 0, 0.115, 1.676), (-0.05, 0, 0.15, 1.892),
    (-0.05, 0, 0.20, 1.965), (-0.05, 0, 0.30, 2.040),
    (-0.05, 0, 0.40, 2.099), (-0.05, 0, 0.50, 2.151),
    # x=0.0 (above cube center)
    (0.00, 0, 0.115, 0.181), (0.00, 0, 0.15, 2.043),
    (0.00, 0, 0.20, 2.020), (0.00, 0, 0.30, 2.054),
    (0.00, 0, 0.40, 2.104), (0.00, 0, 0.50, 2.154),
    # x=0.065 (x/H=0.65, leeward recirculation)
    (0.065, 0, 0.015, -0.295), (0.065, 0, 0.05, -0.180),
    (0.065, 0, 0.10, 0.157), (0.065, 0, 0.15, 1.994),
    (0.065, 0, 0.20, 2.038), (0.065, 0, 0.30, 2.065),
    (0.065, 0, 0.40, 2.109), (0.065, 0, 0.50, 2.156),
    # x=0.10 (x/H=1.0, near wake)
    (0.10, 0, 0.015, -0.631), (0.10, 0, 0.05, 0.031),
    (0.10, 0, 0.10, 0.766), (0.10, 0, 0.15, 1.982),
    (0.10, 0, 0.20, 2.043), (0.10, 0, 0.30, 2.069),
    (0.10, 0, 0.40, 2.113), (0.10, 0, 0.50, 2.158),
    # x=0.20 (x/H=2.0, mid wake)
    (0.20, 0, 0.015, -0.267), (0.20, 0, 0.05, 0.498),
    (0.20, 0, 0.10, 1.323), (0.20, 0, 0.15, 1.924),
    (0.20, 0, 0.20, 2.023), (0.20, 0, 0.30, 2.065),
    (0.20, 0, 0.40, 2.113), (0.20, 0, 0.50, 2.159),
    # x=0.30 (x/H=3.0, far wake)
    (0.30, 0, 0.015, 0.222), (0.30, 0, 0.05, 0.935),
    (0.30, 0, 0.10, 1.543), (0.30, 0, 0.15, 1.893),
    (0.30, 0, 0.20, 2.008), (0.30, 0, 0.30, 2.065),
    (0.30, 0, 0.40, 2.113), (0.30, 0, 0.50, 2.159),
    # x=0.50 (x/H=5.0, far downstream)
    (0.50, 0, 0.015, 0.967), (0.50, 0, 0.05, 1.395),
    (0.50, 0, 0.10, 1.695), (0.50, 0, 0.15, 1.874),
    (0.50, 0, 0.20, 1.990), (0.50, 0, 0.30, 2.060),
    (0.50, 0, 0.40, 2.111), (0.50, 0, 0.50, 2.159),
]

# =============================================================================
# STEP 3: Measurement Profile Curves (Rhino visualization)
# =============================================================================

profile_x = sorted(set(p[0] for p in exp_data))
profile_curves = []
for x in profile_x:
    pts = [rg.Point3d(x, 0, z*0.01) for z in range(61)]
    profile_curves.append(rg.PolylineCurve(pts))
    print("  Profile x={:+.2f}m (x/H={:+.1f})".format(x, x/H))

# =============================================================================
# STEP 4: Experimental Data Points (for visual comparison)
# =============================================================================

exp_pts = []
for x, y, z, u in exp_data:
    pt = rg.Point3d(x, (u/U_REF) * 0.5, z)
    exp_pts.append(pt)

total_pts = len(exp_data)
print("")
print("Total measurement points: {}".format(total_pts))
print("Data: {} profiles, {} heights each".format(
    len(profile_x), total_pts // len(profile_x)))

# =============================================================================
# STEP 5: Report
# =============================================================================

report = []
report.append("=" * 60)
report.append("CityLBM v0.2.1 — AIJ Case A Validation (Cube)")
report.append("=" * 60)
report.append("")
report.append("BUILDING: {:.3f} x {:.3f} x {:.3f} m (cube)".format(H, B, D))
report.append("WIND:    U_H = {:.1f} m/s from +X".format(U_REF))
report.append("GRID:    dx = {:.3f} m (H/{:.0f})".format(CELL_SIZE, H/CELL_SIZE))
report.append("LES:     Smagorinsky Cs={:.2f}".format(SMAG_CS))
report.append("STEPS:   {} (save every {})".format(TIME_STEPS, SAVE_INTVL))
report.append("")
report.append("EXPERIMENTAL DATA:")
report.append("  Source:  Zenodo 10.5281/zenodo.15430018")
report.append("  Authors: Tominaga, Kikumoto, Okaze et al.")
report.append("  License: CC BY 4.0")
report.append("  Points:  {} ({} profiles)".format(total_pts, len(profile_x)))
report.append("")
report.append("NEXT STEPS:")
report.append("  1. Connect a (Mesh) -> Add Buildings (B)")
report.append("  2. Create Scene: V={}, D=(1,0,0), Ext={}".format(U_REF, DOM_EXT))
report.append("  3. Add Buildings -> Grid Generator -> Run Simulation")
report.append("  4. Run in Mode 3 (async), {} steps".format(TIME_STEPS))
report.append("  5. Connect Case Dir -> PostProcess GhPython")
report.append("=" * 60)

# =============================================================================
# OUTPUTS
# =============================================================================

a = building_mesh       # -> Add Buildings (B input)
b = "\n".join(report)   # -> Panel
c = profile_curves      # -> Curve param (Rhino visualization)
d = exp_pts             # -> Point param
