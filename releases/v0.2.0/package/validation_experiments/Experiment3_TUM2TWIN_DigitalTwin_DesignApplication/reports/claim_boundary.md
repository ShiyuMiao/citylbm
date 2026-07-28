# Claim Boundary

evidence_type: newly_run + preexisting_artifact + blocked

## Claims Supported By Current Evidence

- The TUM2TWIN official dataset pages and related source pages have been checked and recorded.
- The complete textured photogrammetry mesh matching the user's Rhino screenshot has been downloaded as OBJ/MTL/JPG and rendered locally for visual audit.
- The photogrammetry mesh is suitable for visual/Rhino reference, not for direct rigid CFD collision boundaries.
- The user-provided `converted.rar` package has been extracted and audited; its 3dm contains one photogrammetry mesh layer rather than separated semantic/CFD layers.
- The user-provided z0 photogrammetry STL has been run in FluidX3D as an exploratory pilot at dx = 2 m for 2000 steps; the voxel masks support the conclusion that it behaves as a fragmented visual shell rather than a robust closed building collision model.
- 27 LoD2 CityGML building files have been downloaded and converted into a full LoD2 collision STL.
- The full LoD2 STL has been QA-recorded with units, local z0 offset, bbox, triangle count, watertight status, boundary edges, non-manifold edges, degenerate triangles, and duplicate triangles.
- FluidX3D has been compiled and run locally on the Tesla P100 GPU.
- A full LoD2 8-direction coarse matrix has been run at dx = 4 m for 10000 steps per direction.
- A full LoD2 WD000 medium pilot has been run at dx = 2 m for 10000 steps.
- The main whole-block geometry has been corrected from the limited LoD2 subset to an OBJ-derived closed district prism collision model.
- A whole-block district prism 8-direction coarse matrix has been run at dx = 6 m.
- A whole-block district prism 8-direction medium matrix has been run at dx = 4 m.
- A coarse/medium grid-sensitivity comparison has been generated at common heights of 12, 24, and 48 m.
- A local photogrammetry-extent semantic closed prism geometry has been generated for pedestrian-height simulation.
- A local core-prism 8-direction matrix has been run at dx = 2 m for 10000 steps per direction, resolving a z~2 m pedestrian-height layer for preliminary VR and stagnation statistics.
- The local core-prism dx=2 m case has been upgraded with time sampling: 6000-step spin-up followed by three samples at steps 8000, 10000, and 12000 for each of 8 wind directions.
- Open-Meteo 2024 hourly 10 m wind speed/direction data have been downloaded as a wind-climate proxy and converted into 8 velocity-direction weights.
- A wind-climate-proxy weighted z~2 m VR map and metrics table have been generated from the local time-sampled FluidX3D results.
- Matplotlib audit figures and CSV metrics were generated directly from FluidX3D VTK outputs.
- A ParaView no-render pipeline state was generated with pvpython for manual GUI review.
- An S1 ventilation-relief design-sensitivity geometry has been generated, voxelized, simulated for 8 wind directions, and compared against S0 with the same dx=2 m time-sampled FluidX3D protocol.
- The S1 comparison supports a near-null/negative design-sensitivity conclusion: the tested single relief corridor does not materially improve global z~2 m VR or stagnation metrics.

## Claims Not Yet Supported

- The current results do not prove final pedestrian-level wind comfort or safety.
- The current results are not validated against field measurements or wind-tunnel data.
- The Open-Meteo weighted result is a climate-proxy sensitivity layer, not a site-measured wind rose or formal annual exceedance-probability comfort result.
- The current FluidX3D setup is not yet a fully Reynolds-scaled final study; it still uses a stable pilot viscosity.
- The full LoD2 collision STL is not perfectly watertight, although FluidX3D voxelization has succeeded.
- The whole-block prism model is a simplified closed block reconstruction from the LoD3 OBJ, not exact facade-resolved LoD3 geometry.
- The whole-block medium grid still does not resolve 1.5-2.0 m pedestrian height, although the local dx=2 m core-prism case resolves z~2 m and now has a short time-sampling window.
- ParaView headless screenshots are not available yet because RenderView creation fails without a working OpenGL/OSMesa path.
- 3DGS or photogrammetry mesh should not be claimed as a direct closed collision boundary.
- The user-provided photogrammetry FluidX3D pilot should not be used as a final wind comfort/safety result; it is evidence for geometry readiness limits only.
- The CityLBM-Grasshopper chain is optional and not executed; manuscript wording should be FluidX3D-native simulation with a CityLBM-compatible geometry package unless GH run evidence is added.
- GCRI has been scored as a paper-internal geometry-readiness metric, but it does not validate wind-result accuracy.
- S1 should not be written as a successful design optimization; it is a sensitivity result showing that the tested light corridor is insufficient in this morphology.
- GCBTE, pollutant dispersion, and additional S2-Sn design-intervention comparisons are not completed and must remain blocked/future-work items.

## Remaining Work Before Final SCI-Level Claims

1. Refine and document inflow/top/lateral boundary assumptions.
2. Complete Lawson/NEN/AIJ comfort/safety classification only after a site-appropriate wind rose, threshold velocities, and exceedance-probability method are fixed.
3. Consider a longer sampling window or dx=1 m local refinement if detailed 1.5 m pedestrian-height classification is required.
4. Add pollutant dispersion only after source terms and scalar transport setup are explicitly defined.
5. Develop S2-Sn network-scale porosity alternatives if the paper wants to make positive intervention-design claims rather than a negative S1 sensitivity claim.
6. Use ParaView GUI or install a software-rendering runtime for final publication screenshots.
7. If the paper title or method foregrounds CityLBM-GH, add Grasshopper definition files, plugin-run screenshots, solver logs, and output artifacts; otherwise keep the current FluidX3D-native positioning.
