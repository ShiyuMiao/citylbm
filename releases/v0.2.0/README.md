# CityLBM v0.2.0 Release

This directory preserves the CityLBM v0.2.0 package for GitHub version
management. Future releases should use separate sibling directories, for
example `releases/v0.2.1` or `releases/v0.3.0`, instead of replacing this
snapshot.

## Contents

- `package/`: Food4Rhino/Yak package source directory.
- `CityLBM_v0.2.0_Food4Rhino.zip`: uploadable package archive.

## Version

- Package version: `0.2.0`
- Assembly version: `0.2.0.0`
- Rhino/Grasshopper target: Windows Rhino 7/8 + Grasshopper

## Validation Evidence

The package includes `package/validation_experiments` with AIJ Case A and AIJ
Case E evidence:

- Rhino files
- Grasshopper workflows
- Excel result workbooks
- screenshots
- case metadata
- SHA256 checksums

The bundled validation evidence is based on existing CityLBM/FluidX3D VTK
outputs, but the raw VTK files are not included to keep the repository and
Food4Rhino upload package compact.

## Archive Hash

`CityLBM_v0.2.0_Food4Rhino.zip`

SHA256:

`4BF9EF2A1EF8A1CE347771C6851EF0AA236A45B51141A928274F9FFDB7404DB6`

## Known Boundary

The verified v0.2.0 binary exposes 18 Grasshopper components. `Lawson Comfort`
exists in the development source tree but is not compiled into this verified
binary; validation workflows keep it optional until a rebuilt binary includes
the component.
