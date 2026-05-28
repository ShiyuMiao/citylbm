# =============================================================================
# create_aij_casea_gh.py - AIJ Case A One-Click .gh Generator
# =============================================================================
# Run inside Rhino 7:
#   Rhino.exe /nosplash /runscript="_-RunPythonScript (Load THIS_FILE)"
# =============================================================================

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System
import os

rs.Command('_Grasshopper _Enter')
System.Threading.Thread.Sleep(3000)

import Grasshopper as gh
from Grasshopper.Kernel import GH_Document

canvas = gh.Instances.ActiveCanvas
if not canvas:
    print('ERROR: Grasshopper not open')
    exit(1)

doc = canvas.Document

# Clear existing
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
                except:
                    pass
        except:
            pass
    return None

def add_comp(guid_str, x, y, name):
    proxy = find_proxy(guid_str)
    if not proxy:
        print('  MISSING: ' + name)
        return None
    comp = proxy.CreateInstance()
    comp.Attributes.Pivot = System.Drawing.PointF(x, y)
    doc.AddObject(comp, False)
    print('  OK: ' + name)
    return comp

base = os.path.dirname(os.path.abspath(__file__))
setup_code = open(os.path.join(base, 'AIJ_CaseA_OneClick.py'), 'r', encoding='utf-8').read()
post_code  = open(os.path.join(base, 'AIJ_CaseA_PostProcess.py'), 'r', encoding='utf-8').read()

print('=== Creating AIJ Case A .gh Definition ===')

# GhPython Setup
gh_setup = add_comp('6d45f1cd-2b6c-4150-9633-7e7edf42f9a1', 100, 100, 'GhPython Setup')
if gh_setup:
    gh_setup.Code = setup_code

# CityLBM components
cs   = add_comp('C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A', 400, 300, 'Create Scene')
ab   = add_comp('D4E7F2A8-7C9B-5E8D-0B1A-3E5C6D9F8A2B', 550, 100, 'Add Buildings')
gg   = add_comp('E8F4A2D1-7B3C-4E8D-9A5F-3D6E7C8B9A1E', 700, 100, 'Grid Generator')
rsim = add_comp('F9A5B3E2-8C4D-4F7A-9B6E-2D5C7A8B9F1D', 1000, 100, 'Run Simulation')

# GhPython PostProcess
gh_post = add_comp('6d45f1cd-2b6c-4150-9633-7e7edf42f9a1', 1300, 100, 'GhPython PostProcess')
if gh_post:
    gh_post.Code = post_code

# Panel for report text
panel = add_comp('57DA99BD-ECEB-4743-AEB4-2CFC1B0C32FE', 100, 300, 'Panel')

print('=== Connecting wires ===')

def wire(src, si, tgt, ti, desc):
    try:
        sp = src.Params.Output[si]
        tp = tgt.Params.Input[ti]
        doc.AddObject(Grasshopper.Kernel.GH_Assembly.CreateWire(sp, tp), False)
        print('  ' + desc)
    except Exception as e:
        print('  FAIL ' + desc + ': ' + str(e))

if gh_setup and ab: wire(gh_setup, 0, ab, 1, 'Setup.a -> AddBuildings.B')
if cs and ab:       wire(cs, 0, ab, 0, 'CreateScene -> AddBuildings.S')
if ab and gg:       wire(ab, 0, gg, 0, 'AddBuildings -> GridGenerator')
if gg and rsim:     wire(gg, 0, rsim, 0, 'GridGenerator -> RunSimulation')
if rsim and gh_post:wire(rsim, 0, gh_post, 0, 'RunSimulation -> PostProcess')
if gh_setup and panel: wire(gh_setup, 1, panel, 0, 'Setup.b -> Panel')

# Save .gh file
out = os.path.join(base, 'AIJ_CaseA_OneClick.gh')
print('=== Saving: ' + out + ' ===')
try:
    from Grasshopper import IO
    ghio = IO.GH_DocumentIO()
    ghio.Document = doc
    ghio.SaveAs(out)
    print('OK: ' + str(os.path.getsize(out)) + ' bytes')
except Exception as e:
    print('IO save error: ' + str(e))
    try:
        canvas.SaveDocument(out)
        print('OK (fallback): ' + str(os.path.getsize(out)) + ' bytes')
    except Exception as e2:
        print('Fallback error: ' + str(e2))

print('=== DONE ===')