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
- GCBTE, pollutant dispersion, and additional S3-Sn design-intervention comparisons are not completed and must remain blocked/future-work items.

## Remaining Work Before Final SCI-Level Claims

1. Refine and document inflow/top/lateral boundary assumptions.
2. Complete Lawson/NEN/AIJ comfort/safety classification only after a site-appropriate wind rose, threshold velocities, and exceedance-probability method are fixed.
3. Consider a longer sampling window or dx=1 m local refinement if detailed 1.5 m pedestrian-height classification is required.
4. Add pollutant dispersion only after source terms and scalar transport setup are explicitly defined.
5. Develop S3-Sn wind-sector-coupled gateway and enclosure-reduction alternatives if the paper wants to make positive intervention-design claims rather than the current negative S1/S2 sensitivity claims.
6. Use ParaView GUI or install a software-rendering runtime for final publication screenshots.
7. If the paper title or method foregrounds CityLBM-GH, add Grasshopper definition files, plugin-run screenshots, solver logs, and output artifacts; otherwise keep the current FluidX3D-native positioning.

## S2 Claim Boundary Addendum

- `newly_run`: S2 geometry was generated, voxelized, simulated in FluidX3D for eight wind directions, and compared with S0/S1 using the same postprocessing protocol.
- Supported claim: S2 does not produce meaningful global pedestrian-layer ventilation recovery under the current dx=2 m, 8-direction protocol.
- Unsupported claim: S2 proves that all porosity interventions fail, or that the tested geometry is a constructable campus design.
- Paper-safe interpretation: S1 and S2 jointly suggest that effective ventilation improvement in this campus core requires wind-sector-coupled porosity and momentum-entry positioning rather than simple geometric opening area.

## Directional Trade-Off Claim Boundary Addendum

- `newly_run`: S1/S2 directional trade-offs were computed from existing FluidX3D VTK outputs using the same three-sample averaging protocol.
- Supported claim: S2 creates slightly more localized common-open-cell response than S1, but the affected area is sparse and newly opened cells remain low-speed.
- Unsupported claim: the directional trade-off analysis proves a positive design solution or annual wind comfort improvement.
- Paper-safe interpretation: S3-Sn should be framed around wind-sector-coupled gateway placement and pressure-exchange continuity rather than arbitrary porosity area.

## Multivariate Morphology Robustness Claim Boundary Addendum

- `newly_run`: bootstrap Spearman, partial Spearman, and rank-regression robustness checks were computed from existing FluidX3D morphology-response CSVs.
- Supported claim: local enclosure and mean-height context are stronger ordered descriptors of the 20-50 m local-context mean VR than footprint area, elongation, or perimeter-area compactness.
- Unsupported claim: morphology parameters form a high-accuracy predictive model or establish causal design effects without additional intervention experiments and measured validation.
- Paper-safe interpretation: use the multivariate result as an interpretable campus wind-screening diagnosis with limited explanatory power (`R2 = 0.122 +/- 0.166`).

## Morphology Threshold Design-Rule Claim Boundary Addendum

- `newly_run`: near-to-context recovery and tertile-rule screening were computed from existing component-level morphology and FluidX3D wind-response CSVs.
- Supported claim: the 20-50 m local-context band reveals sample-internal morphology threshold signals that are hidden in the uniformly sheltered 0-20 m facade-adjacent band.
- Unsupported claim: the extracted rules are universal design thresholds, causal laws, or field-validated criteria for other campus blocks.
- Paper-safe interpretation: use the threshold result as a digital-twin screening layer for prioritizing candidate design mechanisms, with explicit single-case and no-field-validation boundaries.

## Final Integrated Paper-Readiness Claim Boundary Addendum

- `newly_run + preexisting_artifact + blocked`: final integrated paper-readiness files consolidate existing evidence and blockers without adding new CFD fields.
- Supported claim: the archive is manuscript-ready for a FluidX3D-native digital-twin-to-CFD screening workflow and morphology/design-sensitivity interpretation.
- Unsupported claim: the final integrated layer completes field validation, pollutant dispersion, annual comfort/safety compliance, GCBTE closure, successful design optimization, or CityLBM-GH end-to-end execution.
- Paper-safe interpretation: use `paper_text/final_integrated_results_discussion_zh.md` or `paper_text/final_integrated_results_discussion_en.md` as the highest-level Results/Discussion source.

## SCI Manuscript Module Claim Boundary Addendum

- `newly_run + preexisting_artifact + blocked`: the SCI manuscript module is a synthesis artifact generated from existing simulation outputs, verified references, audit matrices, and claim-boundary files.
- Supported claim: the module can be used as paper-facing text for Experiment 3 methods, results, discussion, limitations, and figure/table callouts.
- Unsupported claim: the existence of manuscript-ready prose does not add new CFD fields, field measurements, pollutant transport, annual comfort exceedance statistics, GCBTE results, or a completed CityLBM-GH plugin run.
- Paper-safe interpretation: use `paper_text/experiment3_sci_manuscript_module_zh.md`, `paper_text/experiment3_sci_manuscript_module_en.md`, and `paper_text/experiment3_figure_table_callouts_zh.md` as the current top-level writing layer, while preserving all blocker statements in `reports/experiment3_manuscript_module_audit.md` and `manifests/experiment3_manuscript_module_claims.csv`.

## SCI Section Paper Draft Claim Boundary Addendum

- `newly_run + preexisting_artifact + blocked`: the section paper draft is generated from archived Experiment 3 evidence, verified references, key result matrix, figure/table callouts, and blocker inventories.
- Supported claim: `academic-paper-writer/paper-drafts/paper_draft.md` and `paper_text/experiment3_sci_section_paper_draft_zh.md` are continuous section-level drafts suitable for integration into the broader SCI manuscript.
- Unsupported claim: the draft is not a venue-formatted final article, does not complete paper-level introduction/related-work framing, and does not close field validation, annual comfort compliance, pollutant dispersion, GCBTE, or CityLBM-GH execution.
- Paper-safe interpretation: treat the paper draft as the current Experiment 3 section manuscript, with target-journal formatting and optional CityLBM-GH foregrounding left as author-input decisions.
