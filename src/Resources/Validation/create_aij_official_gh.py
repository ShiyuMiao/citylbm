# =============================================================================
# create_aij_official_gh.py — Headless .gh Generator (Robust Version)
# =============================================================================
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System
import os
import time

# Ensure GH is open
rs.Command('_Grasshopper _Enter')
time.sleep(5)

import Grasshopper as gh
from Grasshopper.Kernel import GH_Document

canvas = gh.Instances.ActiveCanvas
if not canvas:
    raise Exception("Grasshopper canvas not available")

doc = canvas.Document
doc.DeselectAll()
for obj in list(doc.Objects):
    doc.RemoveObject(obj, False)

def find_proxy(guid_str):
    g = System.Guid(guid_str)
    for category in gh.Instances.ComponentServer.ObjectProxies:
        try:
            for proxy in category:
                try:
                    if proxy.Guid == g:
                        return proxy
                except: pass
        except: pass
    return None

def add_comp(guid_str, x, y, name):
    proxy = find_proxy(guid_str)
    if not proxy:
        raise Exception("Component not found: " + name + " (" + guid_str + ")")
    comp = proxy.CreateInstance()
    comp.Attributes.Pivot = System.Drawing.PointF(x, y)
    doc.AddObject(comp, False)
    return comp

print("Creating AIJ Case A Official .gh...")

# Read post-process code
base = os.path.dirname(os.path.abspath(__file__))
post_code_path = os.path.join(base, 'AIJ_CaseA_Official_PostProcess.py')
post_code = open(post_code_path, 'r', encoding='utf-8').read()

# 1. GhPython PostProcess
gh_post = add_comp('6d45f1cd-2b6c-4150-9633-7e7edf42f9a1', 1400, 100, 'GhPython PostProcess')
gh_post.Code = post_code
print("  + GhPython PostProcess")

# 2. CityLBM components
cs   = add_comp('C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A', 500, 100, 'Create Scene')
ab   = add_comp('D4E7F2A8-7C9B-5E8D-0B1A-3E5C6D9F8A2B', 740, 100, 'Add Buildings')
gg   = add_comp('E8F4A2D1-7B3C-4E8D-9A5F-3D6E7C8B9A1E', 980, 100, 'Grid Generator')
rsim = add_comp('F9A5B3E2-8C4D-4F7A-9B6E-2D5C7A8B9F1D', 1220, 100, 'Run Simulation')
print("  + CityLBM: CreateScene, AddBuildings, GridGenerator, RunSimulation")

# 3. Native GH Box (Center Box)
native_box = add_comp('722ccc01-0c7f-4030-ad33-c99bda4c90d9', 100, 100, 'Center Box')
print("  + GH Native Center Box")

# 4. Mesh Brep
mesh_brep = add_comp('0a29d78e-3c9f-47d7-b77a-d47259d27ad6', 260, 100, 'Mesh Brep')
print("  + GH Native Mesh Brep")

# 5. Panel
panel = add_comp('57DA99BD-ECEB-4743-AEB4-2CFC1B0C32FE', 1400, 300, 'Panel')
print("  + Panel")

# === WIRES ===
def wire(src, si, tgt, ti, desc):
    sp = src.Params.Output[si]
    tp = tgt.Params.Input[ti]
    doc.AddObject(Grasshopper.Kernel.GH_Assembly.CreateWire(sp, tp), False)
    print("  wire: " + desc)

wire(native_box, 0, mesh_brep, 0, 'Box -> MeshBrep')
wire(mesh_brep, 0, ab, 1, 'MeshBrep -> AddBuildings.B')
wire(cs, 0, ab, 0, 'CreateScene -> AddBuildings.S')
wire(ab, 0, gg, 0, 'AddBuildings -> GridGenerator')
wire(gg, 0, rsim, 0, 'GridGenerator -> RunSimulation')
wire(rsim, 0, gh_post, 0, 'RunSimulation -> PostProcess')
wire(gh_post, 0, panel, 0, 'PostProcess -> Panel')

# === SAVE ===
out = os.path.join(base, 'AIJ_CaseA_Official.gh')
from Grasshopper import IO
ghio = IO.GH_DocumentIO()
ghio.Document = doc
ghio.SaveAs(out)
print("\nSAVED: " + out)
print("SIZE: " + str(os.path.getsize(out)) + " bytes")
print("DONE")