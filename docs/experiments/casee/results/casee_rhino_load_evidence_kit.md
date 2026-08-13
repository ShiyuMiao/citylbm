# Case E Rhino/GHA Load Evidence Kit

Generated: 2026-08-13T10:00:48.310553+00:00

## Verdict

- Evidence kit ready: True
- Claim readiness: `author_input_needed_manual_rhino_load`
- Expected plugin version: `0.4.0-rc`
- Expected GHA SHA256: `6ded1fad358edb75a4179a410dac570df5c5125a6f17abb8c36893a394f04f2b`

## Checks

| check | passed |
|---|---:|
| `plugin_identity_gate_passed` | True |
| `tracked_gha_exists` | True |
| `tracked_gha_sha_available` | True |
| `rhino_executable_detected` | True |
| `matching_gha_staged` | True |
| `install_audit_passed` | True |
| `rhino_load_gate_fail_closed` | True |

## Manual Steps

1. Open Rhino from one detected Rhino.exe path.
2. Start Grasshopper and ensure the staged CityLBM GHA is loaded, not an older copy.
3. Place the CityLBM Plugin Identity component and connect its Report, GHA Path, GHA SHA256, and Manifest Template outputs to panels.
4. Capture a screenshot or log showing the Plugin Identity component outputs from the Rhino/Grasshopper session.
5. Copy rhino_gha_load_manifest.template.json to rhino_gha_load_manifest.json and replace template fields with the observed Plugin Identity component values.
6. Run python docs/experiments/casee/tools/rhino_gha_load_gate.py and then python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0.

## Template

- Template path: `docs/experiments/casee/results/rhino_gha_load_manifest.template.json`

```json
{
  "checked_at": "2026-08-13T10:00:48.310474+00:00",
  "operator": "manual-operator-name",
  "rhino_version": "paste Rhino About/SystemInfo version string",
  "grasshopper_version": "paste Grasshopper version string",
  "observed_plugin_version": "0.4.0-rc",
  "observed_assembly_version": "0.4.0.0",
  "observed_gha_sha256": "6ded1fad358edb75a4179a410dac570df5c5125a6f17abb8c36893a394f04f2b",
  "evidence_artifacts": [
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png",
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt"
  ],
  "notes": "Create docs/experiments/casee/results/rhino_gha_load_manifest.json only after a real Rhino/Grasshopper session shows CityLBM loaded from the staged GHA. Do not use this template as pass evidence."
}
```

## Boundary

This kit prepares manual evidence collection only. It does not prove Rhino loaded the plugin, does not run CFD, and does not improve official Case E z=2 m metrics.
