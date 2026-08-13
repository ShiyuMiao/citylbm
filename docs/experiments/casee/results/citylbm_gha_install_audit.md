# CityLBM GHA Install Audit

Generated: 2026-08-13T11:04:11.373929+00:00

## Verdict

- Install audit passed: True
- Matching GHA already staged: True
- Rhino loaded new GHA: False
- Claim readiness: `install_ready_pending_manual_rhino_load`
- Expected GHA SHA256: `e116a5c2d827aea5022de48ab2c2b9c48caad3326de5b2d1069ad448ca73171d`

## Checks

| check | passed |
|---|---:|
| `plugin_identity_gate_passed` | True |
| `tracked_gha_exists` | True |
| `tracked_gha_hash_matches_identity_gate` | True |
| `packaged_gha_exists` | True |
| `grasshopper_library_dir_detected_or_recommendable` | True |
| `matching_gha_already_staged` | True |
| `rhino_load_gate_still_fail_closed` | True |

## Recommended Manual Copy Command

Run only when you want to stage the current tracked GHA for Grasshopper:

```powershell
New-Item -ItemType Directory -Force -Path 'C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries' | Out-Null; Copy-Item -LiteralPath 'C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\CityLBM\bin\CityLBM.gha' -Destination 'C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries\CityLBM.gha' -Force
```

## Installed Candidates

| library dir | found | matches tracked GHA | path | sha256 |
|---|---:|---:|---|---|
| `C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries` | True | True | `C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries\CityLBM.gha` | `e116a5c2d827aea5022de48ab2c2b9c48caad3326de5b2d1069ad448ca73171d` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\7.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\6.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Local\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |

## Boundary

This audit only checks whether the tracked CityLBM.gha is staged or stageable for Grasshopper. It does not copy files automatically, does not prove Rhino loaded the plugin, does not run CFD, and does not support formal accuracy claims.
