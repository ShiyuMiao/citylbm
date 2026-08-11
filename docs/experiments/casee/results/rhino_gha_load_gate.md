# Rhino/GHA Load Gate

Generated: 2026-08-11T00:16:44.947265+00:00

## Verdict

- Rhino loaded new GHA: False
- Claim readiness: `blocked_manual_rhino_load`
- Expected plugin version: `0.4.0-rc`
- Expected GHA SHA256: `28e531a58d4045499a845c439823653a9b8232576acdc812f4a1d4684fa3a735`

## Checks

| check | passed |
|---|---:|
| `plugin_identity_gate_passed` | True |
| `tracked_gha_exists` | True |
| `manual_manifest_exists` | False |
| `manual_manifest_required_fields_present` | False |
| `observed_plugin_version_matches_expected` | False |
| `observed_gha_sha256_matches_tracked` | False |
| `evidence_artifacts_listed` | False |
| `evidence_artifacts_exist` | False |

Missing manifest fields:
- `checked_at`
- `operator`
- `rhino_version`
- `grasshopper_version`
- `observed_plugin_version`
- `observed_gha_sha256`
- `evidence_artifacts`

## Required Manual Manifest

`docs/experiments/casee/results/rhino_gha_load_manifest.json` must be created from a real Rhino/Grasshopper session before this gate can pass:

```json
{
  "checked_at": "YYYY-MM-DDTHH:MM:SS+08:00",
  "operator": "name",
  "rhino_version": "Rhino 7/8 version string",
  "grasshopper_version": "Grasshopper version string",
  "observed_plugin_version": "0.4.0-rc",
  "observed_assembly_version": "0.4.0.0",
  "observed_gha_sha256": "28e531a58d4045499a845c439823653a9b8232576acdc812f4a1d4684fa3a735",
  "evidence_artifacts": [
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png",
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt"
  ],
  "notes": "Evidence must show the loaded CityLBM GHA path/version/hash from the Rhino/Grasshopper session."
}
```

## Boundary

This gate proves only Rhino/Grasshopper loaded the tracked CityLBM GHA identity. It is not CFD accuracy evidence and must not change official z=2 m metrics.
