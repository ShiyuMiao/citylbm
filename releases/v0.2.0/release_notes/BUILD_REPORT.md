# CityLBM v0.2.0 Food4Rhino Build Report

Date: 2026-06-04

## Release paths

- Package source: `F:\Grade2master2\CITYLBM开发文件\CityLBM_v0.2.0_Food4Rhino\package`
- Upload ZIP: `F:\Grade2master2\CITYLBM开发文件\CityLBM_v0.2.0_Food4Rhino\CityLBM_v0.2.0_Food4Rhino.zip`

## Build

- Source baseline: `F:\0_PhD second year\第5篇：城市风环境LBM二次开发\CityLBM0.1.0WIP`
- Target framework: `.NET Framework 4.8`
- Rhino reference: Rhino 7
- Build command: `dotnet build CityLBM.sln -c Release`
- Build status: success
- Errors: 0
- Warnings: 2 pre-existing unused-field warnings:
  - `ProbeConduit._lineWidth`
  - `WindCompassConduit._followViewport`

## Version checks

- `CityLBM.gha` assembly version: `0.2.0.0`
- `manifest.yml` version: `0.2.0`
- Installed local Grasshopper copy: `%APPDATA%\Grasshopper\Libraries\CityLBM.gha`
- Installed local Grasshopper copy version: `0.2.0.0`

## Package checks

- ZIP root contains `manifest.yml`: pass
- `.pdb` files included: 0
- `obj` directories included: 0
- `Debug` directories included: 0
- `.vtk` files included: 0
- `src_v0.5.0` included: 0
- Yak CLI: not found on this machine, so `yak build` was not run.

## Rhino/GH checks

- Rhino 7 is installed on this machine and was used for build references.
- Rhino 8 is not installed on this machine, so Rhino 8 loading was not locally tested.
- Automated Rhino/GH UI loading was not run in this packaging pass; manual check should open `examples\AIJ_CaseA\grasshopper\AIJ_CaseA_validation.gh` and confirm the CityLBM tab/components load.

## Notes

- FluidX3D is kept as an external dependency for v0.2.0.
- AIJ Case A and Case E examples are included without large VTK output files.
- The Case E official geometry `BD_caseE.stl` is included because the example is intended to be runnable after the user configures FluidX3D.

## Accuracy Hotfix - 2026-06-06

- Rebuilt `package/CityLBM.gha` after adding FluidX3D unit-system setup to generated `setup.cpp`.
- Generated cases now call `units.set_m_kg_s(...)` before VTK export so `write_device_to_vtk(..., true)` can output velocity in m/s consistently.
- `domain_origin.json` now records `ReferenceWindSpeedSi`, `ReferenceVelocityLbm`, `VelocityScaleSiPerLbm`, and `VTKVelocityUnits`.
- AIJ Case A and Case E postprocess scripts now support `--velocity-scale` for auditing old VTK files generated before this fix.
- Updated package hash: `A971EC46E3EB1EDA57187D20DCD055D98113B2FAEE4688C5A3B51F90508B69F6`.
- Updated ZIP hash: `980DC531C96EFC32CB8DE454A53F487F8013643C830704D52A211E6019AF66B0`.
- Local Grasshopper library copy could not be overwritten during this pass because Rhino was still running and locking `%APPDATA%\Grasshopper\Libraries\CityLBM.gha`.

## Lawson Component Hotfix - 2026-07-16

- Added `package/CityLBM.Lawson.gha` as a companion Grasshopper assembly for the missing `Lawson Comfort` component.
- Verified `CityLBM.Lawson.gha` by reflection: assembly version `0.2.0.0`; component name `Lawson Comfort`; nickname `Lawson`; category `CityLBM`; subcategory `3 | Results`; GUID `c4e8f2a1-7b3d-4c5e-9f1a-2d3e4f5a6b7c`.
- Installed local Grasshopper library copy: `%APPDATA%\Grasshopper\Libraries\CityLBM.Lawson.gha`.
- Rebuilt upload ZIP and confirmed root contains `manifest.yml`, `CityLBM.gha`, and `CityLBM.Lawson.gha` with no `.vtk`, `.pdb`, `obj`, `Debug`, backup, or `src_v0.5.0` files.
- Updated package docs so installation instructions include both `CityLBM.gha` and `CityLBM.Lawson.gha`.
- Current ZIP hash: `D08F8DD2F0B68259070AEE7E4F1525EDD8697625BF16AA63B101747851183BCC`.
- Current Lawson assembly hash: `E9ACA7FB5CF89D4C5079622417863BAEE7896653F9847F3538DCF3E7331A9BE3`.
- Full `v0.2.1\src` rebuild is still blocked by widespread encoding-damaged C# source files; the verified v0.2.0 install artifacts remain the package binaries.

## Grasshopper Icon Hotfix - 2026-07-16

- Patched embedded PNG resources in `package/CityLBM.gha` from 200x200 to 24x24 without changing component logic.
- Verified by reflection that all 18 `CityLBM.gha` components return `Icon_24x24` as 24x24; `BadIconCount=0`.
- Updated local Grasshopper library copy `%APPDATA%\Grasshopper\Libraries\CityLBM.gha` after closing Rhino, so the next Rhino/GH launch loads the fixed toolbar icons.
- The original pre-iconfix `CityLBM.gha` is retained only in `release_notes\CityLBM.gha.pre_iconfix_backup` for audit history and is not included in the upload ZIP.
- Current ZIP hash: `64F4086576F5287E964B477E58BE82F2DD7758353AD9AF2C1327C4C8A5300887`.
- Current `CityLBM.gha` hash: `A0A75EB3E57CCDA9E54A5F5BC25ABD17E70D51C4A18E2144C0AB67F56C069623`.
