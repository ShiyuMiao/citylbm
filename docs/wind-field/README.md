# AIJ Case A Interactive Wind-Field Preview

`index.html` is a static Three.js view of a compact sample of the archived `u-000002000.vtk` velocity field. Run it through a local web server or static host; opening it directly from `file://` prevents the browser from fetching the JSON data.

Regenerate the data from the local archive:

```powershell
python .\tools\vtk_to_web_points.py `
  --vtk 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\【验证】AIJCASEA_u-000002000\case\output\u-000002000.vtk' `
  --domain 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\【验证】AIJCASEA_u-000002000\case\domain_origin.json' `
  --output .\docs\wind-field\data\aij-case-a-u-000002000-sampled.json `
  --stride 6
```

This is a presentation and inspection asset. Its archive velocity scale has not been confirmed as SI units, and a single snapshot does not establish a converged or time-averaged result.
