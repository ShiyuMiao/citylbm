#!/usr/bin/env python3
"""Generate native FluidX3D AIJ Case E probe-mean cases.

The generated setup is a validation runner, not a claim of validated accuracy.
It writes casee_probe_time_mean.csv directly from official z=2 m probes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
DATA_DIR = CASE_DIR / "official_data"
NATIVE_DIR = CASE_DIR / "native_cases"

DOMAIN = {
    "origin_x": -300.0,
    "origin_y": -500.0,
    "origin_z": 0.0,
    "size_x": 600.0,
    "size_y": 800.0,
    "size_z": 240.0,
}
UREF = 3.928296
SCALE_FACTOR = 250.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def official_probes() -> list[dict[str, float]]:
    rows = []
    for r in read_csv(DATA_DIR / "RS_caseE.csv"):
        if r["case"] == "ac" and r["Wind_direction"] == "N" and abs(float(r["z(m)"]) - 2.0) < 1e-9:
            rows.append(
                {
                    "No.": int(r["No."]),
                    "x": float(r["x(m)"]),
                    "y": float(r["y(m)"]),
                    "z": float(r["z(m)"]),
                    "vr": float(r["Velocity_Ratio"]),
                }
            )
    rows.sort(key=lambda r: int(r["No."]))
    if len(rows) != 80:
        raise SystemExit(f"Expected 80 official ac+N z=2 m probes, found {len(rows)}")
    return rows


def approach_flow() -> list[dict[str, float]]:
    return [{"z": float(r["z(m)"]), "u": float(r["U(m/s)"]), "k": float(r["k(m2/s2)"])} for r in read_csv(DATA_DIR / "AF_caseE.csv")]


def c_array(name: str, values: list[float], suffix: str = "f") -> str:
    def fmt(v: float) -> str:
        s = f"{v:.8g}"
        if "e" not in s.lower() and "." not in s:
            s += ".0"
        return f"{s}{suffix}"

    body = ", ".join(fmt(v) for v in values)
    return f"static const float {name}[] = {{ {body} }};"


def c_int_array(name: str, values: list[int]) -> str:
    body = ", ".join(str(v) for v in values)
    return f"static const int {name}[] = {{ {body} }};"


def generate_defines(use_subgrid: bool) -> str:
    subgrid = "#define SUBGRID\n" if use_subgrid else ""
    return f"""#pragma once

#define D3Q19
#define SRT
#define FP16S
#define EQUILIBRIUM_BOUNDARIES
{subgrid}

#define TYPE_S 0b00000001
#define TYPE_E 0b00000010
#define TYPE_T 0b00000100
#define TYPE_F 0b00001000
#define TYPE_I 0b00010000
#define TYPE_G 0b00100000
#define TYPE_X 0b01000000
#define TYPE_Y 0b10000000

#if defined(FP16S) || defined(FP16C)
#define fpxx ushort
#else
#define fpxx float
#endif
"""


def convert_ascii_stl_to_binary(src: Path, dst: Path) -> int:
    triangles: list[tuple[tuple[float, float, float], list[tuple[float, float, float]]]] = []
    normal = (0.0, 0.0, 0.0)
    vertices: list[tuple[float, float, float]] = []
    for raw in src.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = raw.strip().split()
        if not parts:
            continue
        if parts[0] == "facet" and len(parts) >= 5 and parts[1] == "normal":
            normal = (float(parts[2]), float(parts[3]), float(parts[4]))
            vertices = []
        elif parts[0] == "vertex" and len(parts) >= 4:
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "endfacet":
            if len(vertices) == 3:
                triangles.append((normal, vertices))
    with dst.open("wb") as f:
        header = b"CityLBM AIJ Case E binary STL".ljust(80, b" ")
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for n, vs in triangles:
            f.write(struct.pack("<12fH", n[0], n[1], n[2], vs[0][0], vs[0][1], vs[0][2], vs[1][0], vs[1][1], vs[1][2], vs[2][0], vs[2][1], vs[2][2], 0))
    return len(triangles)


def generate_setup(
    dx: float,
    steps: int,
    spinup: int,
    sample_dt: int,
    lattice_umax: float,
    wind_y: float,
    ground_offset_cells: int,
    origin_z_offset_m: float,
    domain_decomp: tuple[int, int, int],
    nu_lbm: float,
    inlet_turbulence_mode: str,
    inlet_turbulence_scale: float,
    wall_model: str,
    wall_dilation_cells: int,
    wall_damping_factor: float,
    residual_target_mode: str,
    residual_target_scale: float,
) -> str:
    probes = official_probes()
    af = approach_flow()
    origin_z = DOMAIN["origin_z"] - ground_offset_cells * dx + origin_z_offset_m
    nx = math.ceil(DOMAIN["size_x"] / dx)
    ny = math.ceil(DOMAIN["size_y"] / dx)
    nz = math.ceil((DOMAIN["size_z"] - origin_z) / dx)
    max_ratio = max(p["u"] / UREF for p in af)
    uref_lbm = lattice_umax / max_ratio
    wall_model_code = {"none": 0, "voxel_dilation": 1, "ground_damping": 2}[wall_model]
    wall_dilation_cells = max(0, int(wall_dilation_cells))
    wall_damping_factor = max(0.0, min(1.0, float(wall_damping_factor)))
    residual_target_code = {"none": 0, "c014_channel_response": 1}[residual_target_mode]
    residual_target_scale = max(0.0, min(1.0, float(residual_target_scale)))

    lines = [
        "// Generated by docs/experiments/casee/tools/generate_native_casee.py",
        "// AIJ Case E ac+N official z=2 m probe-only time-mean validation runner.",
        '#include "lbm.hpp"',
        "",
        f"static const uint CASEE_NX = {nx}u;",
        f"static const uint CASEE_NY = {ny}u;",
        f"static const uint CASEE_NZ = {nz}u;",
        f"static const float CASEE_DX = {dx:.8f}f;",
        f"static const float CASEE_ORIGIN_X = {DOMAIN['origin_x']:.8f}f;",
        f"static const float CASEE_ORIGIN_Y = {DOMAIN['origin_y']:.8f}f;",
        f"static const float CASEE_ORIGIN_Z = {origin_z:.8f}f;",
        f"static const int CASEE_GROUND_OFFSET_CELLS = {ground_offset_cells};",
        f"static const float CASEE_ORIGIN_Z_OFFSET_M = {origin_z_offset_m:.8f}f;",
        f"static const uint CASEE_DX_DOMAINS = {domain_decomp[0]}u;",
        f"static const uint CASEE_DY_DOMAINS = {domain_decomp[1]}u;",
        f"static const uint CASEE_DZ_DOMAINS = {domain_decomp[2]}u;",
        f"static const float CASEE_NU_LBM = {nu_lbm:.10f}f;",
        f"static const uint CASEE_STEPS = {steps}u;",
        f"static const uint CASEE_SPINUP = {spinup}u;",
        f"static const uint CASEE_SAMPLE_DT = {sample_dt}u;",
        f"static const float CASEE_UREF_LBM = {uref_lbm:.10f}f;",
        f"static const float CASEE_WIND_Y = {wind_y:.1f}f;",
        f"static const int CASEE_INLET_TURBULENCE_MODE = {1 if inlet_turbulence_mode == 'k_synthetic_fullplane' else 0};",
        f"static const float CASEE_INLET_TURBULENCE_SCALE = {inlet_turbulence_scale:.8f}f;",
        f"static const int CASEE_DIAGNOSTIC_WALL_MODEL = {wall_model_code};",
        f"static const int CASEE_WALL_DILATION_CELLS = {wall_dilation_cells};",
        f"static const float CASEE_WALL_DAMPING_FACTOR = {wall_damping_factor:.8f}f;",
        "static const bool CASEE_WALL_FOLLOWUP_DEFAULT_SAFE = CASEE_DIAGNOSTIC_WALL_MODEL==0 && CASEE_WALL_DILATION_CELLS==0 && CASEE_WALL_DAMPING_FACTOR<=0.0f;",
        f"static const int CASEE_DIAGNOSTIC_RESIDUAL_TARGET_MODE = {residual_target_code};",
        f"static const float CASEE_RESIDUAL_TARGET_SCALE = {residual_target_scale:.8f}f;",
        "static const bool CASEE_RESIDUAL_TARGET_DEFAULT_SAFE = CASEE_DIAGNOSTIC_RESIDUAL_TARGET_MODE==0 && CASEE_RESIDUAL_TARGET_SCALE<=0.0f;",
        "static const int CASEE_PROBE_N = 80;",
        c_int_array("PROBE_NO", [int(p["No."]) for p in probes]),
        c_array("PROBE_X", [p["x"] for p in probes]),
        c_array("PROBE_Y", [p["y"] for p in probes]),
        c_array("PROBE_Z", [p["z"] for p in probes]),
        c_array("PROBE_OFFICIAL", [p["vr"] for p in probes]),
        f"static const int AF_N = {len(af)};",
        c_array("AF_Z", [p["z"] for p in af]),
        c_array("AF_U_RATIO", [p["u"] / UREF for p in af]),
        c_array("AF_SIGMA_RATIO", [math.sqrt(max(0.0, 2.0 * p["k"] / 3.0)) / UREF for p in af]),
        "",
        "float clampf_casee(const float v, const float lo, const float hi) { return v<lo ? lo : (v>hi ? hi : v); }",
        "",
        "float inlet_ratio(const float z_m) {",
        "    if(z_m<=AF_Z[0]) return AF_U_RATIO[0];",
        "    for(int i=0; i<AF_N-1; i++) {",
        "        if(z_m<=AF_Z[i+1]) {",
        "            const float t = (z_m-AF_Z[i])/(AF_Z[i+1]-AF_Z[i]);",
        "            return AF_U_RATIO[i]*(1.0f-t)+AF_U_RATIO[i+1]*t;",
        "        }",
        "    }",
        "    return AF_U_RATIO[AF_N-1];",
        "}",
        "",
        "float inlet_sigma_ratio(const float z_m) {",
        "    if(z_m<=AF_Z[0]) return AF_SIGMA_RATIO[0];",
        "    for(int i=0; i<AF_N-1; i++) {",
        "        if(z_m<=AF_Z[i+1]) {",
        "            const float t = (z_m-AF_Z[i])/(AF_Z[i+1]-AF_Z[i]);",
        "            return AF_SIGMA_RATIO[i]*(1.0f-t)+AF_SIGMA_RATIO[i+1]*t;",
        "        }",
        "    }",
        "    return AF_SIGMA_RATIO[AF_N-1];",
        "}",
        "",
        "float inlet_synthetic_signal(const uint x, const uint z, const uint step) {",
        "    const float xf = (float)x;",
        "    const float zf = (float)z;",
        "    const float tf = (float)step;",
        "    const float a = sinf(0.173f*xf + 0.071f*zf + 0.0031f*tf);",
        "    const float b = sinf(0.047f*xf - 0.131f*zf + 0.0053f*tf + 1.7f);",
        "    const float c = sinf(0.109f*xf + 0.037f*zf - 0.0047f*tf + 3.1f);",
        "    return clampf_casee(0.50f*a + 0.30f*b + 0.20f*c, -1.0f, 1.0f);",
        "}",
        "",
        "float inlet_velocity_lbm(const float z_m, const uint x, const uint z, const uint step) {",
        "    const float base = CASEE_UREF_LBM*inlet_ratio(z_m);",
        "    if(CASEE_INLET_TURBULENCE_MODE==0 || CASEE_INLET_TURBULENCE_SCALE<=0.0f) return base;",
        "    const float sigma = CASEE_UREF_LBM*inlet_sigma_ratio(z_m);",
        "    const float perturbed = base + CASEE_INLET_TURBULENCE_SCALE*sigma*inlet_synthetic_signal(x, z, step);",
        "    return clampf_casee(perturbed, 0.0f, 0.095f);",
        "}",
        "",
        "float residual_channel_factor(const float x_m, const float y_m, const float z_m) {",
        "    if(CASEE_DIAGNOSTIC_RESIDUAL_TARGET_MODE==0 || CASEE_RESIDUAL_TARGET_SCALE<=0.0f) return 1.0f;",
        "    if(CASEE_DIAGNOSTIC_RESIDUAL_TARGET_MODE==1) {",
        "        const bool high_speed_corridor = (x_m>-120.0f && x_m<130.0f && y_m>-70.0f && y_m<45.0f && z_m<=8.0f);",
        "        const bool sheltered_corner = ((x_m<-80.0f || x_m>80.0f) && y_m<-45.0f && z_m<=8.0f);",
        "        if(high_speed_corridor) return 1.0f+0.20f*CASEE_RESIDUAL_TARGET_SCALE;",
        "        if(sheltered_corner) return 1.0f-0.15f*CASEE_RESIDUAL_TARGET_SCALE;",
        "    }",
        "    return 1.0f;",
        "}",
        "",
        "void apply_casee_inlet(LBM& lbm, const uint Nx, const uint Ny, const uint Nz, const uint step) {",
        "    (void)Nx;",
        "    if(CASEE_INLET_TURBULENCE_MODE==0 || CASEE_INLET_TURBULENCE_SCALE<=0.0f) return;",
        "    parallel_for(lbm.get_N(), [&](ulong n) {",
        "        uint x=0u, y=0u, z=0u;",
        "        lbm.coordinates(n, x, y, z);",
        "        const bool inlet_cell = CASEE_WIND_Y<0.0f ? y==Ny-1u : y==0u;",
        "        if(!inlet_cell) return;",
        "        const float z_m = CASEE_ORIGIN_Z+((float)z+0.5f)*CASEE_DX;",
        "        const float x_m = CASEE_ORIGIN_X+((float)x+0.5f)*CASEE_DX;",
        "        const float y_m = CASEE_ORIGIN_Y+((float)y+0.5f)*CASEE_DX;",
        "        const float u = inlet_velocity_lbm(z_m, x, z, step)*residual_channel_factor(x_m, y_m, z_m);",
        "        lbm.u.x[n] = 0.0f;",
        "        lbm.u.y[n] = CASEE_WIND_Y*u;",
        "        lbm.u.z[n] = 0.0f;",
        "    });",
        "    lbm.u.write_to_device();",
        "}",
        "",
        "float3 sample_u_raw_trilinear(LBM& lbm, const float x_m, const float y_m, const float z_m, int& solid_neighbors) {",
        "    const float gx = (x_m-CASEE_ORIGIN_X)/CASEE_DX-0.5f;",
        "    const float gy = (y_m-CASEE_ORIGIN_Y)/CASEE_DX-0.5f;",
        "    const float gz = (z_m-CASEE_ORIGIN_Z)/CASEE_DX-0.5f;",
        "    int x0 = (int)floor(gx), y0 = (int)floor(gy), z0 = (int)floor(gz);",
        "    const float tx = clampf_casee(gx-(float)x0, 0.0f, 1.0f);",
        "    const float ty = clampf_casee(gy-(float)y0, 0.0f, 1.0f);",
        "    const float tz = clampf_casee(gz-(float)z0, 0.0f, 1.0f);",
        "    x0 = max(0, min((int)lbm.get_Nx()-2, x0));",
        "    y0 = max(0, min((int)lbm.get_Ny()-2, y0));",
        "    z0 = max(0, min((int)lbm.get_Nz()-2, z0));",
        "    float3 acc = float3(0.0f);",
        "    solid_neighbors = 0;",
        "    for(int dz=0; dz<=1; dz++) for(int dy=0; dy<=1; dy++) for(int dx=0; dx<=1; dx++) {",
        "        const uint xi=(uint)(x0+dx), yi=(uint)(y0+dy), zi=(uint)(z0+dz);",
        "        const float wx = dx ? tx : 1.0f-tx;",
        "        const float wy = dy ? ty : 1.0f-ty;",
        "        const float wz = dz ? tz : 1.0f-tz;",
        "        const float w = wx*wy*wz;",
        "        const ulong n = lbm.index(xi, yi, zi);",
        "        if((lbm.flags[n]&TYPE_S)!=0u) solid_neighbors++;",
        "        acc.x += w*lbm.u.x[n];",
        "        acc.y += w*lbm.u.y[n];",
        "        acc.z += w*lbm.u.z[n];",
        "    }",
        "    return acc;",
        "}",
        "",
        "float3 sample_u_fluid_weighted(LBM& lbm, const float x_m, const float y_m, const float z_m, int& solid_neighbors, float& fluid_weight_sum) {",
        "    const float gx = (x_m-CASEE_ORIGIN_X)/CASEE_DX-0.5f;",
        "    const float gy = (y_m-CASEE_ORIGIN_Y)/CASEE_DX-0.5f;",
        "    const float gz = (z_m-CASEE_ORIGIN_Z)/CASEE_DX-0.5f;",
        "    int x0 = (int)floor(gx), y0 = (int)floor(gy), z0 = (int)floor(gz);",
        "    const float tx = clampf_casee(gx-(float)x0, 0.0f, 1.0f);",
        "    const float ty = clampf_casee(gy-(float)y0, 0.0f, 1.0f);",
        "    const float tz = clampf_casee(gz-(float)z0, 0.0f, 1.0f);",
        "    x0 = max(0, min((int)lbm.get_Nx()-2, x0));",
        "    y0 = max(0, min((int)lbm.get_Ny()-2, y0));",
        "    z0 = max(0, min((int)lbm.get_Nz()-2, z0));",
        "    float3 acc = float3(0.0f);",
        "    solid_neighbors = 0;",
        "    fluid_weight_sum = 0.0f;",
        "    for(int dz=0; dz<=1; dz++) for(int dy=0; dy<=1; dy++) for(int dx=0; dx<=1; dx++) {",
        "        const uint xi=(uint)(x0+dx), yi=(uint)(y0+dy), zi=(uint)(z0+dz);",
        "        const float wx = dx ? tx : 1.0f-tx;",
        "        const float wy = dy ? ty : 1.0f-ty;",
        "        const float wz = dz ? tz : 1.0f-tz;",
        "        const float w = wx*wy*wz;",
        "        const ulong n = lbm.index(xi, yi, zi);",
        "        if((lbm.flags[n]&TYPE_S)!=0u) { solid_neighbors++; continue; }",
        "        acc.x += w*lbm.u.x[n];",
        "        acc.y += w*lbm.u.y[n];",
        "        acc.z += w*lbm.u.z[n];",
        "        fluid_weight_sum += w;",
        "    }",
        "    if(fluid_weight_sum>0.0f) {",
        "        acc.x /= fluid_weight_sum;",
        "        acc.y /= fluid_weight_sum;",
        "        acc.z /= fluid_weight_sum;",
        "    } else {",
        "        int raw_solid_neighbors = 0;",
        "        acc = sample_u_raw_trilinear(lbm, x_m, y_m, z_m, raw_solid_neighbors);",
        "    }",
        "    return acc;",
        "}",
        "",
        "float3 sample_u_nearest_valid(LBM& lbm, const float x_m, const float y_m, const float z_m, int& search_radius_used) {",
        "    const float gx = (x_m-CASEE_ORIGIN_X)/CASEE_DX-0.5f;",
        "    const float gy = (y_m-CASEE_ORIGIN_Y)/CASEE_DX-0.5f;",
        "    const float gz = (z_m-CASEE_ORIGIN_Z)/CASEE_DX-0.5f;",
        "    const int cx = max(0, min((int)lbm.get_Nx()-1, (int)round(gx)));",
        "    const int cy = max(0, min((int)lbm.get_Ny()-1, (int)round(gy)));",
        "    const int cz = max(0, min((int)lbm.get_Nz()-1, (int)round(gz)));",
        "    float best_d2 = 1.0e30f;",
        "    ulong best_n = lbm.index((uint)cx, (uint)cy, (uint)cz);",
        "    bool found = false;",
        "    search_radius_used = -1;",
        "    for(int r=0; r<=3 && !found; r++) {",
        "        for(int dz=-r; dz<=r; dz++) for(int dy=-r; dy<=r; dy++) for(int dx=-r; dx<=r; dx++) {",
        "            const int xi = cx+dx, yi = cy+dy, zi = cz+dz;",
        "            if(xi<0 || yi<0 || zi<0 || xi>=(int)lbm.get_Nx() || yi>=(int)lbm.get_Ny() || zi>=(int)lbm.get_Nz()) continue;",
        "            const ulong n = lbm.index((uint)xi, (uint)yi, (uint)zi);",
        "            if((lbm.flags[n]&TYPE_S)!=0u) continue;",
        "            const float d2 = ((float)xi-gx)*((float)xi-gx)+((float)yi-gy)*((float)yi-gy)+((float)zi-gz)*((float)zi-gz);",
        "            if(d2<best_d2) { best_d2=d2; best_n=n; found=true; search_radius_used=r; }",
        "        }",
        "    }",
        "    return float3(lbm.u.x[best_n], lbm.u.y[best_n], lbm.u.z[best_n]);",
        "}",
        "",
        "float3 sample_u_vertical_valid_above(LBM& lbm, const float x_m, const float y_m, const float z_m, int& dz_used) {",
        "    const float gx = (x_m-CASEE_ORIGIN_X)/CASEE_DX-0.5f;",
        "    const float gy = (y_m-CASEE_ORIGIN_Y)/CASEE_DX-0.5f;",
        "    const float gz = (z_m-CASEE_ORIGIN_Z)/CASEE_DX-0.5f;",
        "    const int xi = max(0, min((int)lbm.get_Nx()-1, (int)round(gx)));",
        "    const int yi = max(0, min((int)lbm.get_Ny()-1, (int)round(gy)));",
        "    const int zi0 = max(0, min((int)lbm.get_Nz()-1, (int)round(gz)));",
        "    dz_used = -1;",
        "    for(int dz=0; dz<=6; dz++) {",
        "        const int zi = zi0+dz;",
        "        if(zi>=(int)lbm.get_Nz()) break;",
        "        const ulong n = lbm.index((uint)xi, (uint)yi, (uint)zi);",
        "        if((lbm.flags[n]&TYPE_S)==0u) { dz_used=dz; return float3(lbm.u.x[n], lbm.u.y[n], lbm.u.z[n]); }",
        "    }",
        "    int nearest_radius = -1;",
        "    return sample_u_nearest_valid(lbm, x_m, y_m, z_m, nearest_radius);",
        "}",
        "",
        "void apply_casee_wall_followup(LBM& lbm, const uint Nx, const uint Ny, const uint Nz) {",
        "    if(CASEE_DIAGNOSTIC_WALL_MODEL==0) return;",
        "    if(CASEE_DIAGNOSTIC_WALL_MODEL==1 && CASEE_WALL_DILATION_CELLS>0) {",
        "        for(int pass=0; pass<CASEE_WALL_DILATION_CELLS; pass++) {",
        "            lbm.flags.read_from_device();",
        "            parallel_for(lbm.get_N(), [&](ulong n) {",
        "                uint x=0u, y=0u, z=0u;",
        "                lbm.coordinates(n, x, y, z);",
        "                if(z==0u || x==0u || y==0u || x>=Nx-1u || y>=Ny-1u || z>=Nz-1u) return;",
        "                if((lbm.flags[n]&TYPE_S)!=0u) return;",
        "                bool near_solid = false;",
        "                for(int dz=-1; dz<=1 && !near_solid; dz++) for(int dy=-1; dy<=1 && !near_solid; dy++) for(int dx=-1; dx<=1; dx++) {",
        "                    if(dx==0 && dy==0 && dz==0) continue;",
        "                    const int xi=(int)x+dx, yi=(int)y+dy, zi=(int)z+dz;",
        "                    if(xi<0 || yi<0 || zi<0 || xi>=(int)Nx || yi>=(int)Ny || zi>=(int)Nz) continue;",
        "                    const ulong nn=lbm.index((uint)xi, (uint)yi, (uint)zi);",
        "                    if((lbm.flags[nn]&TYPE_S)!=0u) { near_solid=true; break; }",
        "                }",
        "                if(near_solid) lbm.flags[n]=TYPE_S;",
        "            });",
        "            lbm.flags.write_to_device();",
        "        }",
        "    }",
        "    if(CASEE_DIAGNOSTIC_WALL_MODEL==2 && CASEE_WALL_DAMPING_FACTOR>0.0f) {",
        "        parallel_for(lbm.get_N(), [&](ulong n) {",
        "            uint x=0u, y=0u, z=0u;",
        "            lbm.coordinates(n, x, y, z);",
        "            if(z>3u) return;",
        "            if((lbm.flags[n]&TYPE_S)!=0u) return;",
        "            const float layer = (float)z/3.0f;",
        "            const float damp = 1.0f-CASEE_WALL_DAMPING_FACTOR*(1.0f-layer);",
        "            lbm.u.x[n] *= damp;",
        "            lbm.u.y[n] *= damp;",
        "            lbm.u.z[n] *= damp;",
        "        });",
        "        lbm.u.write_to_device();",
        "    }",
        "}",
        "",
        "void main_setup() {",
        "    LBM lbm(CASEE_NX, CASEE_NY, CASEE_NZ, CASEE_DX_DOMAINS, CASEE_DY_DOMAINS, CASEE_DZ_DOMAINS, CASEE_NU_LBM);",
        "    const uint Nx=lbm.get_Nx(), Ny=lbm.get_Ny(), Nz=lbm.get_Nz();",
        "    parallel_for(lbm.get_N(), [&](ulong n) {",
        "        uint x=0u, y=0u, z=0u;",
        "        lbm.coordinates(n, x, y, z);",
        "        if(z==0u) { lbm.flags[n]=TYPE_S; return; }",
        "        const float z_m = CASEE_ORIGIN_Z+((float)z+0.5f)*CASEE_DX;",
        "        const float x_m = CASEE_ORIGIN_X+((float)x+0.5f)*CASEE_DX;",
        "        const float y_m = CASEE_ORIGIN_Y+((float)y+0.5f)*CASEE_DX;",
        "        const float u = inlet_velocity_lbm(z_m, x, z, 0u)*residual_channel_factor(x_m, y_m, z_m);",
        "        const bool inlet_cell = CASEE_WIND_Y<0.0f ? y==Ny-1u : y==0u;",
        "        const bool outlet_cell = CASEE_WIND_Y<0.0f ? y==0u : y==Ny-1u;",
        "        if(inlet_cell) { lbm.flags[n]=TYPE_E; lbm.u.y[n] = CASEE_WIND_Y*u; return; }",
        "        if(outlet_cell || x==0u || x==Nx-1u || z==Nz-1u) { lbm.flags[n]=TYPE_E; return; }",
        "        lbm.u.y[n] = CASEE_WIND_Y*u;",
        "    });",
        "    lbm.flags.write_to_device();",
        "    lbm.u.write_to_device();",
        "    const float3 stl_offset = float3(-CASEE_ORIGIN_X/CASEE_DX, -CASEE_ORIGIN_Y/CASEE_DX, -CASEE_ORIGIN_Z/CASEE_DX);",
        f"    const Mesh* mesh = read_stl(\"buildings.stl\", {SCALE_FACTOR:.8f}f/CASEE_DX, float3x3(1.0f), stl_offset);",
        "    lbm.voxelize_mesh_on_device(mesh, TYPE_S);",
        "    delete mesh;",
        "    apply_casee_wall_followup(lbm, Nx, Ny, Nz);",
        "    lbm.flags.read_from_device();",
        "    double sum_speed[80] = {0.0};",
        "    double sum_speed_nearest_valid[80] = {0.0};",
        "    double sum_speed_fluid_weighted[80] = {0.0};",
        "    double sum_speed_vertical_valid_above[80] = {0.0};",
        "    double sum_speed_z_plus_half[80] = {0.0};",
        "    int solid_risk[80] = {0};",
        "    int fluid_weight_solid_risk[80] = {0};",
        "    int nearest_valid_search_radius[80] = {0};",
        "    int vertical_valid_above_dz[80] = {0};",
        "    uint samples = 0u;",
        "    lbm.run(0u);",
        "    while(lbm.get_t()<CASEE_STEPS) {",
        "        const uint remaining = CASEE_STEPS-(uint)lbm.get_t();",
        "        const uint dt = remaining<CASEE_SAMPLE_DT ? remaining : CASEE_SAMPLE_DT;",
        "        apply_casee_inlet(lbm, Nx, Ny, Nz, (uint)lbm.get_t());",
        "        lbm.run(dt);",
        "        if(lbm.get_t()>=CASEE_SPINUP) {",
        "            lbm.u.read_from_device();",
        "            for(int i=0; i<CASEE_PROBE_N; i++) {",
        "                int solid_neighbors = 0;",
        "                const float3 up = sample_u_raw_trilinear(lbm, PROBE_X[i], PROBE_Y[i], PROBE_Z[i], solid_neighbors);",
        "                sum_speed[i] += (double)sqrtf(up.x*up.x+up.y*up.y+up.z*up.z);",
        "                if(solid_neighbors>solid_risk[i]) solid_risk[i] = solid_neighbors;",
        "                int fluid_solid_neighbors = 0;",
        "                float fluid_weight_sum = 0.0f;",
        "                const float3 uf = sample_u_fluid_weighted(lbm, PROBE_X[i], PROBE_Y[i], PROBE_Z[i], fluid_solid_neighbors, fluid_weight_sum);",
        "                sum_speed_fluid_weighted[i] += (double)sqrtf(uf.x*uf.x+uf.y*uf.y+uf.z*uf.z);",
        "                if(fluid_solid_neighbors>fluid_weight_solid_risk[i]) fluid_weight_solid_risk[i] = fluid_solid_neighbors;",
        "                int nearest_radius = -1;",
        "                const float3 un = sample_u_nearest_valid(lbm, PROBE_X[i], PROBE_Y[i], PROBE_Z[i], nearest_radius);",
        "                sum_speed_nearest_valid[i] += (double)sqrtf(un.x*un.x+un.y*un.y+un.z*un.z);",
        "                if(nearest_radius>nearest_valid_search_radius[i]) nearest_valid_search_radius[i] = nearest_radius;",
        "                int vertical_dz = -1;",
        "                const float3 uv = sample_u_vertical_valid_above(lbm, PROBE_X[i], PROBE_Y[i], PROBE_Z[i], vertical_dz);",
        "                sum_speed_vertical_valid_above[i] += (double)sqrtf(uv.x*uv.x+uv.y*uv.y+uv.z*uv.z);",
        "                if(vertical_dz>vertical_valid_above_dz[i]) vertical_valid_above_dz[i] = vertical_dz;",
        "                int zph_solid_neighbors = 0;",
        "                const float3 uz = sample_u_raw_trilinear(lbm, PROBE_X[i], PROBE_Y[i], PROBE_Z[i]+0.5f*CASEE_DX, zph_solid_neighbors);",
        "                sum_speed_z_plus_half[i] += (double)sqrtf(uz.x*uz.x+uz.y*uz.y+uz.z*uz.z);",
        "            }",
        "            samples++;",
        "        }",
        '        print_info("CaseE step "+to_string(lbm.get_t())+" / "+to_string(CASEE_STEPS));',
        "    }",
        '    string csv = "No.,x_m,y_m,z_m,official_velocity_ratio,predicted_velocity_ratio,speed_lbm,solid_corner_neighbors_max,nearest_valid_velocity_ratio,fluid_weighted_velocity_ratio,vertical_valid_above_velocity_ratio,z_plus_half_velocity_ratio,fluid_weighted_solid_neighbors_max,nearest_valid_search_radius_max,vertical_valid_above_dz_max,samples\\n";',
        "    for(int i=0; i<CASEE_PROBE_N; i++) {",
        "        const double mean_speed = samples>0u ? sum_speed[i]/(double)samples : 0.0;",
        "        const double pred_ratio = mean_speed/(double)CASEE_UREF_LBM;",
        "        const double nearest_valid_ratio = (samples>0u ? sum_speed_nearest_valid[i]/(double)samples : 0.0)/(double)CASEE_UREF_LBM;",
        "        const double fluid_weighted_ratio = (samples>0u ? sum_speed_fluid_weighted[i]/(double)samples : 0.0)/(double)CASEE_UREF_LBM;",
        "        const double vertical_valid_above_ratio = (samples>0u ? sum_speed_vertical_valid_above[i]/(double)samples : 0.0)/(double)CASEE_UREF_LBM;",
        "        const double z_plus_half_ratio = (samples>0u ? sum_speed_z_plus_half[i]/(double)samples : 0.0)/(double)CASEE_UREF_LBM;",
        "        csv += to_string(PROBE_NO[i])+\",\"+to_string(PROBE_X[i], 6u)+\",\"+to_string(PROBE_Y[i], 6u)+\",\"+to_string(PROBE_Z[i], 6u)+\",\";",
        "        csv += to_string(PROBE_OFFICIAL[i], 8u)+\",\"+to_string(pred_ratio, 8u)+\",\"+to_string(mean_speed, 8u)+\",\"+to_string(solid_risk[i])+\",\";",
        "        csv += to_string(nearest_valid_ratio, 8u)+\",\"+to_string(fluid_weighted_ratio, 8u)+\",\"+to_string(vertical_valid_above_ratio, 8u)+\",\"+to_string(z_plus_half_ratio, 8u)+\",\";",
        "        csv += to_string(fluid_weight_solid_risk[i])+\",\"+to_string(nearest_valid_search_radius[i])+\",\"+to_string(vertical_valid_above_dz[i])+\",\"+to_string(samples)+\"\\n\";",
        "    }",
        '    write_file("casee_probe_time_mean.csv", csv);',
        "}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dx", type=float, required=True)
    parser.add_argument("--steps", type=int, default=48000)
    parser.add_argument("--spinup", type=int, default=12000)
    parser.add_argument("--sample-dt", type=int, default=200)
    parser.add_argument("--lattice-umax", type=float, default=0.08)
    parser.add_argument("--wind-y", type=float, choices=(-1.0, 1.0), default=-1.0)
    parser.add_argument("--no-subgrid", action="store_true")
    parser.add_argument(
        "--ground-offset-cells",
        type=int,
        default=0,
        help="Diagnostic effective-ground shift. 1 adds one sub-ground solid layer so z=0 falls at the solid-fluid interface.",
    )
    parser.add_argument(
        "--origin-z-offset-m",
        type=float,
        default=0.0,
        help="Diagnostic vertical origin offset after ground-offset is applied. Use 1.0 with dx=2 and ground-offset-cells=1 to center z=2 m on a lattice layer.",
    )
    parser.add_argument("--domain-x", type=int, default=2)
    parser.add_argument("--domain-y", type=int, default=2)
    parser.add_argument("--domain-z", type=int, default=1)
    parser.add_argument("--nu-lbm", type=float, default=0.01666667)
    parser.add_argument("--inlet-turbulence-mode", choices=("none", "k_synthetic_fullplane"), default="none")
    parser.add_argument("--inlet-turbulence-scale", type=float, default=0.0)
    parser.add_argument(
        "--wall-model",
        choices=("none", "voxel_dilation", "ground_damping"),
        default="none",
        help="Default-off diagnostic wall/ground follow-up. Not a formal accuracy model unless an audited official run later passes.",
    )
    parser.add_argument(
        "--wall-dilation-cells",
        type=int,
        default=0,
        help="For --wall-model voxel_dilation, dilate solid cells by this many neighbor passes. Default 0 is off.",
    )
    parser.add_argument(
        "--wall-damping-factor",
        type=float,
        default=0.0,
        help="For --wall-model ground_damping, damp near-ground fluid velocities by this factor in setup initialization. Default 0 is off.",
    )
    parser.add_argument(
        "--residual-target-mode",
        choices=("none", "c014_channel_response"),
        default="none",
        help="Default-off C016 residual-target follow-up. Uses pre-registered coordinate regions only; never fits RS_caseE probe residuals.",
    )
    parser.add_argument(
        "--residual-target-scale",
        type=float,
        default=0.0,
        help="For --residual-target-mode c014_channel_response, scale the pre-registered channel response in [0,1]. Default 0 is off.",
    )
    parser.add_argument("--fluidx3d-root", type=Path)
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()

    wind_label = "yn" if args.wind_y < 0 else "yp"
    sgs_label = "nosgs" if args.no_subgrid else "sgs"
    ground_label = f"gshift{args.ground_offset_cells}"
    zoff_label = f"zoff{args.origin_z_offset_m:g}".replace(".", "p").replace("-", "m")
    nu_label = f"nu{args.nu_lbm:g}".replace(".", "p")
    domain_decomp = (args.domain_x, args.domain_y, args.domain_z)
    domain_label = "" if domain_decomp == (2, 2, 1) else f"_dom{args.domain_x}x{args.domain_y}x{args.domain_z}"
    inlet_label = ""
    if args.inlet_turbulence_mode != "none" or abs(args.inlet_turbulence_scale) > 1e-12:
        scale_label = f"{args.inlet_turbulence_scale:g}".replace(".", "p").replace("-", "m")
        inlet_label = f"_inlet_{args.inlet_turbulence_mode}_s{scale_label}"
    wall_label = ""
    if args.wall_model != "none" or args.wall_dilation_cells > 0 or abs(args.wall_damping_factor) > 1e-12:
        damping_label = f"{args.wall_damping_factor:g}".replace(".", "p").replace("-", "m")
        wall_label = f"_wall_{args.wall_model}_dil{args.wall_dilation_cells}_damp{damping_label}"
    residual_label = ""
    if args.residual_target_mode != "none" or abs(args.residual_target_scale) > 1e-12:
        residual_scale_label = f"{args.residual_target_scale:g}".replace(".", "p").replace("-", "m")
        residual_mode_label = {
            "c014_channel_response": "c014cr",
        }.get(args.residual_target_mode, args.residual_target_mode)
        residual_label = f"_resid_{residual_mode_label}_s{residual_scale_label}"
    run_id = f"casee_native_dx{args.dx:g}_{wind_label}_{sgs_label}_{ground_label}_{zoff_label}_{nu_label}{domain_label}{inlet_label}{wall_label}{residual_label}_pmodes_steps{args.steps}_spin{args.spinup}"
    case_dir = NATIVE_DIR / run_id
    case_dir.mkdir(parents=True, exist_ok=True)
    setup = generate_setup(
        args.dx,
        args.steps,
        args.spinup,
        args.sample_dt,
        args.lattice_umax,
        args.wind_y,
        args.ground_offset_cells,
        args.origin_z_offset_m,
        domain_decomp,
        args.nu_lbm,
        args.inlet_turbulence_mode,
        args.inlet_turbulence_scale,
        args.wall_model,
        args.wall_dilation_cells,
        args.wall_damping_factor,
        args.residual_target_mode,
        args.residual_target_scale,
    )
    defines = generate_defines(not args.no_subgrid)
    (case_dir / "setup.cpp").write_text(setup, encoding="utf-8")
    (case_dir / "defines.hpp").write_text(defines, encoding="utf-8")
    triangle_count = convert_ascii_stl_to_binary(DATA_DIR / "BD_caseE.stl", case_dir / "buildings.stl")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "dx_m": args.dx,
        "steps": args.steps,
        "spinup": args.spinup,
        "sample_dt": args.sample_dt,
        "condition": "ac",
        "wind_direction": "N",
        "solver_wind_y": args.wind_y,
        "subgrid_enabled": not args.no_subgrid,
        "ground_offset_cells": args.ground_offset_cells,
        "origin_z_offset_m": args.origin_z_offset_m,
        "domain_decomposition": list(domain_decomp),
        "nu_lbm": args.nu_lbm,
        "inlet_turbulence_mode": args.inlet_turbulence_mode,
        "inlet_turbulence_scale": args.inlet_turbulence_scale,
        "inlet_turbulence_uses_af_k": bool(args.inlet_turbulence_mode == "k_synthetic_fullplane" and args.inlet_turbulence_scale > 0.0),
        "diagnostic_inlet_turbulence_default_safe": bool(args.inlet_turbulence_mode == "none" and abs(args.inlet_turbulence_scale) <= 1e-12),
        "diagnostic_inlet_turbulence_allowed_as_default_accuracy_model": False,
        "diagnostic_wall_model": args.wall_model,
        "diagnostic_wall_dilation_cells": args.wall_dilation_cells,
        "diagnostic_wall_damping_factor": args.wall_damping_factor,
        "diagnostic_wall_followup_default_safe": bool(
            args.wall_model == "none" and args.wall_dilation_cells == 0 and abs(args.wall_damping_factor) <= 1e-12
        ),
        "diagnostic_wall_followup_allowed_as_default_accuracy_model": False,
        "diagnostic_residual_target_mode": args.residual_target_mode,
        "diagnostic_residual_target_scale": args.residual_target_scale,
        "diagnostic_residual_target_default_safe": bool(args.residual_target_mode == "none" and abs(args.residual_target_scale) <= 1e-12),
        "diagnostic_residual_target_allowed_as_default_accuracy_model": False,
        "diagnostic_residual_target_uses_rs_casee_targets_for_fitting": False,
        "diagnostic_residual_target_pre_registered_regions": (
            ["high_speed_corridor", "sheltered_corner"] if args.residual_target_mode == "c014_channel_response" else []
        ),
        "validation_height_m": 2.0,
        "probe_count": 80,
        "formal_sampling_mode": "raw_trilinear",
        "diagnostic_sampling_modes": [
            "nearest_valid",
            "fluid_weighted",
            "vertical_valid_above",
            "z_plus_half",
        ],
        "geometry_scale_factor": SCALE_FACTOR,
        "binary_stl_triangles": triangle_count,
        "output": "casee_probe_time_mean.csv",
        "evidence_boundary": "generated case only until FluidX3D run completes",
        "claim_boundary": "Inlet-turbulence, wall/ground, and residual-target follow-up options are default-off diagnostics and cannot support formal accuracy or default-promotion claims without a completed official z=2 m release-gate pass. Residual-target follow-ups must not fit RS_caseE official probe targets.",
    }
    (case_dir / "citylbm_native_case_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if args.deploy:
        if args.fluidx3d_root is None:
            raise SystemExit("--deploy requires --fluidx3d-root")
        src = args.fluidx3d_root / "src"
        if not src.exists():
            raise SystemExit(f"Missing FluidX3D src directory: {src}")
        shutil.copy2(case_dir / "setup.cpp", src / "setup.cpp")
        shutil.copy2(case_dir / "defines.hpp", src / "defines.hpp")
        shutil.copy2(case_dir / "buildings.stl", args.fluidx3d_root / "buildings.stl")

    print(json.dumps({"case_dir": str(case_dir), "deployed": bool(args.deploy), **manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
