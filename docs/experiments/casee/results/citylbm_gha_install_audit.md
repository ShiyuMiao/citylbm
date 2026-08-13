# CityLBM GHA Install Audit

Generated: 2026-08-13T12:33:14.893740+00:00

## Verdict

- Install audit passed: True
- Matching GHA already staged: False
- Rhino loaded new GHA: False
- Claim readiness: `install_audited_staging_blocked_by_disk_space`
- Expected GHA SHA256: `f89944de26daa6c54b6791cdbeec6bac1c3b0d3463f70de2fe253bfd475bdcfc`

## Checks

| check | passed |
|---|---:|
| `plugin_identity_gate_passed` | True |
| `tracked_gha_exists` | True |
| `tracked_gha_hash_matches_identity_gate` | True |
| `packaged_gha_exists` | True |
| `grasshopper_library_dir_detected_or_recommendable` | True |
| `tracked_gha_stageable_or_already_staged` | False |
| `matching_gha_already_staged` | False |
| `rhino_load_gate_still_fail_closed` | True |

## Recommended Manual Copy Command

Run only when you want to stage the current tracked GHA for Grasshopper:

```powershell
New-Item -ItemType Directory -Force -Path 'C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries' | Out-Null; Copy-Item -LiteralPath 'E:\citylbm_rc89_work\CityLBM\bin\CityLBM.gha' -Destination 'C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries\CityLBM.gha' -Force
```

## Installed Candidates

| library dir | found | matches tracked GHA | path | sha256 |
|---|---:|---:|---|---|
| `C:\Users\miaoshiyu\AppData\Roaming\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\7.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Roaming\McNeel\Rhinoceros\6.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |
| `C:\Users\miaoshiyu\AppData\Local\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries` | False | False | `` | `` |

## Boundary

This audit only checks whether the tracked CityLBM.gha is staged or stageable for Grasshopper. It does not copy files automatically, does not prove Rhino loaded the plugin, does not run CFD, and does not support formal accuracy claims.
