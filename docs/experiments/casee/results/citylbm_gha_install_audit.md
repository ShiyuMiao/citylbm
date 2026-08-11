# CityLBM GHA Install Audit

Generated: 2026-08-11T03:01:54.709199+00:00

## Verdict

- Install audit passed: True
- Matching GHA already staged: True
- Rhino loaded new GHA: False
- Claim readiness: `install_ready_pending_manual_rhino_load`
- Expected GHA SHA256: `944f471b171e7e00e8ee09867b60324669f6f08014039461ba467dca95d9895b`

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
| `C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries` | True | True | `C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries\CityLBM.gha` | `944f471b171e7e00e8ee09867b60324669f6f08014039461ba467dca95d9895b` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\7.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\6.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Local\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |

## Boundary

This audit only checks whether the tracked CityLBM.gha is staged or stageable for Grasshopper. It does not copy files automatically, does not prove Rhino loaded the plugin, does not run CFD, and does not support formal accuracy claims.
