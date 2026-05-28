# AIJ UWE Benchmark Dataset – Case I (CubeC): Wind Tunnel Experiment for Flow and Dispersion around a Cubic Building Model

## Investigators

### Data Collector

- Hiroaki Kondo (National Institute of Advanced Industrial Science and Technology, Japan)
- Katsuhiko Mutou (National Institute of Advanced Industrial Science and Technology, Japan)
- Akihiro Hori (National Institute of Environmental Studies, Japan)

### Dataset Editors and Distributors

- Yoshihide Tominaga (Niigata Institute of Technology, Japan)  
- Hideki Kikumoto (The University of Tokyo, Japan)  
- Tsubasa Okaze (Institute of Science Tokyo, Japan)

### Contact for Questions

Yoshihide Tominaga  
Email: tominaga@abe.niit.ac.jp

---

## Overview

This dataset provides wind tunnel measurement results of wind velocity and gas concentration around an isolated cubic building model. The data were collected by AIST to validate the DiMCFD (Diffusion Model with CFD) model and includes high-resolution spatial measurements on multiple planes.

---

## Dataset Contents

### File List

- **AF_caseI.csv**  
  Vertical profile of the approaching flow.  
  **Columns:**  
  
  - `z` (m): Height  
  - `U` (m/s): Mean streamwise velocity  
  - `k` (m2/s2): Turbulent kinetic energy

- **RS-w_caseI.csv**  
  Wind velocity data at various locations.  
  **Columns:**  
  
  - `x`, `y`, `z` (m): Coordinates  
  - `U`, `V`, `W` (m/s): Mean wind velocity components in x, y, z directions  
  - `k` (m2/s2): Turbulent kinetic energy

- **RS-c_caseI.csv**  
  Concentration data of tracer gas (ethane).  
  **Columns:**  
  
  - `x`, `y`, `z` (m): Coordinates  
  - `C` (ppm): Mean gas concentration

- **MP-y-w_caseI.png**  
  Measurement points of wind velocity at `y/H = 0`

- **MP-z-w_caseI.png**  
  Measurement points of wind velocity at `z/H = 0.5`

- **MP-y-c_caseI.png**  
  Measurement points of concentration at `y/H = 0`

- **MP-z-c_caseI.png**  
  Measurement points of concentration at `z/H = 0`

- **LF_caseI.xlsx**  
  Legacy Excel version of the measurement dataset, provided as per the AIJ guidelines. Also available via: [Guidebook for CFD Predictions of Urban Wind Environment](https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm)

---

## Methodological Information

### Experimental Setup

- Model: Cube, 0.1 m per side (= H)  
- Release: Circular outlet (6 mm diameter) at the center of the cube’s roof  
- Gas: 10% ethane, released at 400 cc/min  
- Release momentum ratio: M = V<sub>e</sub> / U<sub>H</sub> = 0.14  (V<sub>e</sub>: Gas emission velocity, U<sub>H</sub>: Mean wind speed of appoach flow at H)
- Reynolds number: appro. 11,000 (based on H and U_H = 1.7 m/s)  

### Instrumentation

- **Wind velocity**:  
  
  - Instrument: Laser Doppler Anemometer (Dantec, BSA F60)  
  - Sampling rate: 200 Hz  
  - Averaging duration: 240 s

- **Gas concentration**:  
  
  - Instrument: Hydrocarbon Analyzer (Kimoto, HADA-01)  
  - Sampling rate: 1 Hz  
  - Averaging duration: 120 s

---

## Metadata

- **Units:**  
  - Length: meters (m)  
  - Wind speed: meters per second (m/s)  
  - Concentration: parts per million (ppm)  
- **File creation date:** 21 April, 2025  
- **Format:** CSV, PNG, XLSX  
- **Missing values:** None  
- **License:** CC BY 4.0  
- **Version:** 1.0  
- **Citation requested:** Japan Society for Atmospheric Environment (2013). *Guidelines for Atmospheric Environment Assessment Methods Using CFD Models (DiMCFD)*. Japan Society for Atmospheric Environment (in Japanese).
---

## Data Accessibility

- **Repository name:** Zenodo  
- **DOI:** 10.5281/zenodo.15430018
- **URL:** https://zenodo.org/records/15430018

---

## Related Articles

- Japan Society for Atmospheric Environment (2013). *Guidelines for Atmospheric Environment Assessment Methods Using CFD Models (DiMCFD)*. Japan Society for Atmospheric Environment (in Japanese).

---

*Note: This benchmark case is designed for validating CFD-based urban gas dispersion models as DiMCFD by Japan Society for Atmospheric Environment.*
