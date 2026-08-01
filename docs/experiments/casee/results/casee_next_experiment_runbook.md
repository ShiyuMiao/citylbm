# Case E Next Experiment Runbook

Generated: 2026-08-01T13:31:51.005050+00:00

## Current Official Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923
- Formal release allowed: False
- Recommended tag: `v0.4.0-rc23`

## Command Matrix

| id | stage | enabled now | purpose | command |
|---|---|---:|---|---|
| `R001_preflight_release_chain` | preflight | True | Rebuild CityLBM and regenerate fail-closed release evidence before scheduling more CFD. | `python docs/experiments/casee/tools/reproducibility_suite.py` |
| `R002_gpu_recovery_check` | preflight | True | Verify whether long native FluidX3D runs can be attempted. | `nvidia-smi` |
| `R003_build_chain_refresh` | preflight | True | Refresh .NET, FluidX3D, VS C++ and disk-space evidence. | `python docs/experiments/casee/tools/build_chain_audit.py` |
| `R004_rhino_gha_load_check` | manual_validation | False | Close the Rhino/Grasshopper new-GHA release gate. | `Manual: capture Rhino/Grasshopper screenshot/log showing CityLBM Version=0.4.0-rc and GHA SHA256.` |
| `R005_official_dx2_zcenter_replicate` | native_case_generation | False | Replicate the current best official raw_trilinear diagnostic before changing physics. | `python docs/experiments/casee/tools/generate_native_casee.py --dx 2 --steps 48000 --spinup 12000 --sample-dt 2000 --ground-offset-cells 1 --origin-z-offset-m 1.0 --nu-lbm 0.001` |
| `R006_wall_model_followup_placeholder` | implementation_then_native_run | False | Test a wall/roughness/voxelization change aimed at near-wall official z=2 m errors. | `TODO after implementation: generate native Case E with the new wall/voxelization option and audit raw_trilinear output.` |
| `R007_inlet_turbulence_followup_placeholder` | implementation_then_native_run | False | Test a full-plane digital-filter inlet turbulence change based on AF_caseE z,U,k. | `TODO after implementation: generate native Case E with revised full-plane inlet turbulence and audit raw_trilinear output.` |
| `R008_dx1_feasibility_or_generation` | high_resolution_followup | False | Prepare a dx=1 m official follow-up only if memory/runtime evidence is acceptable. | `python docs/experiments/casee/tools/generate_native_casee.py --dx 1 --steps 48000 --spinup 12000 --sample-dt 4000 --ground-offset-cells 1 --origin-z-offset-m 0.5 --nu-lbm 0.001` |
| `R009_postrun_official_audit` | postrun_audit | False | Audit any newly completed official z=2 m probe CSV against the release gate. | `python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_casee_probe_time_mean.csv>` |

## Formal Result Policy

### R001_preflight_release_chain

- Trigger: Any time the branch changes.
- Expected artifact: `docs/experiments/casee/results/casee_reproducibility_suite.json`
- Formal result policy: Reproducibility evidence only.
- Pass condition: suite_passed=true and formal_release_allowed=false until official metrics pass.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone.

### R002_gpu_recovery_check

- Trigger: After rebooting or recovering the NVIDIA device.
- Expected artifact: `docs/experiments/casee/results/build_chain_manifest.json after build_chain_audit.py rerun`
- Formal result policy: Environment readiness only.
- Pass condition: returncode=0 and no GPU-lost message.
- Forbidden claim: Do not claim a new CFD result from GPU readiness.

### R003_build_chain_refresh

- Trigger: After freeing C: space, installing VS Build Tools C++, or changing FluidX3D binaries.
- Expected artifact: `docs/experiments/casee/results/build_chain_manifest.json`
- Formal result policy: Build-chain evidence only.
- Pass condition: dotnet ready; FluidX3D binary found; GPU ready for long runs; VS C++ status recorded.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone.

### R004_rhino_gha_load_check

- Trigger: After copying/loading tracked CityLBM/bin/CityLBM.gha into Rhino/Grasshopper.
- Expected artifact: `docs/experiments/casee/results/rhino_gha_load_manifest.json`
- Formal result policy: Software identity/load evidence only.
- Pass condition: Manifest proves Rhino loaded the tracked GHA hash, not an old installed copy.
- Forbidden claim: Do not mark rhino_loaded_new_gha=true without an artifact.

### R005_official_dx2_zcenter_replicate

- Trigger: GPU ready; need a clean baseline for comparison.
- Expected artifact: `docs/experiments/casee/native_cases/<run_id>/citylbm_native_case_manifest.json`
- Formal result policy: Only the eventual raw_trilinear 80-probe CSV can be audited as formal official z=2 m.
- Pass condition: Generated case then completed FluidX3D run with casee_probe_time_mean.csv and complete log.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone.

### R006_wall_model_followup_placeholder

- Trigger: A code change exists that is justified by wall/probe diagnostics and remains default-off until validated.
- Expected artifact: `docs/experiments/casee/results/<wall_followup_probe_time_mean.csv>`
- Formal result policy: May inform defaults only if official raw_trilinear metrics improve and Case A smoke regression passes.
- Pass condition: MAE clearly below prior near-20 pp level, R2>0, Pearson>0, n=80 official probes.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone.

### R007_inlet_turbulence_followup_placeholder

- Trigger: A documented inlet turbulence implementation change exists.
- Expected artifact: `docs/experiments/casee/results/<inlet_followup_probe_time_mean.csv>`
- Formal result policy: Experimental switch unless official metric improvement is stable.
- Pass condition: Official raw_trilinear metric improves without relying on diagnostic sampling or z-offset substitution.
- Forbidden claim: Do not claim predictive accuracy, mesh independence, or formal v0.4.0 readiness from this command alone.

### R008_dx1_feasibility_or_generation

- Trigger: GPU ready and dx1 feasibility estimate accepted.
- Expected artifact: `docs/experiments/casee/native_cases/<dx1_run_id>/citylbm_native_case_manifest.json`
- Formal result policy: No mesh-independence claim until completed dx1 metrics support the trend.
- Pass condition: Completed dx=1 official z=2 m raw_trilinear run with all 80 probes and complete log.
- Forbidden claim: Do not claim mesh independence from generated case files or dx=2/3 diagnostics.

### R009_postrun_official_audit

- Trigger: After a complete FluidX3D run writes a new casee_probe_time_mean.csv.
- Expected artifact: `docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/casee_validation_report.md`
- Formal result policy: This is the only path that can update official z=2 m metrics.
- Pass condition: release_gate official_z2m_metric_gate=true and all other release checks true before formal tag.
- Forbidden claim: Do not cite an unaudited probe CSV as a paper result.

## Boundary

This runbook is a command and policy matrix for future work. It does not add a new solver run, does not change the official z=2 m metric, and does not allow a formal v0.4.0 tag.
