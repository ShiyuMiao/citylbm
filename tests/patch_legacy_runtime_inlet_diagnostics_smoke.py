#!/usr/bin/env python3
"""Smoke-test legacy runtime inlet diagnostics patching."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "patch_legacy_runtime_inlet_diagnostics.py"


LEGACY_SETUP = """#include "lbm.hpp"
#include <cmath>

void main_setup() {
    const float citylbm_dx_m = 3.000000f;
    const float citylbm_u_ref_si = 3.928296f;
    const float citylbm_u_ref_lbm = 0.100000f;
    const uint profile_count = 2u;
    const float profile_origin_z_m = 0.0f;
    const float profile_z_m[2] = { 2.0f, 10.0f };
    const float profile_u_lbm[2] = { 0.070000f, 0.090000f };
    const float profile_k_lbm[2] = { 0.000300f, 0.000360f };
    const float profile_u_rms_lbm[2] = { 0.010000f, 0.012000f };
    const float profile_v_rms_lbm[2] = { 0.010000f, 0.012000f };
    const float profile_w_rms_lbm[2] = { 0.010000f, 0.012000f };
    const float dir_x = 0.0f;
    const float dir_y = -1.0f;
    const float dir_z = 0.0f;
    const float lat_x = -dir_y;
    const float lat_y = dir_x;
    LBM lbm(SX, SY, SZ, 0.00016667f);
    const uint Nx = lbm.get_Nx(), Ny = lbm.get_Ny(), Nz = lbm.get_Nz();
    updateDigitalFilter(0u);
    while(lbm.get_t() < 40000u) {
        if(true) {
            const uint tnow = (uint)lbm.get_t();
            updateDigitalFilter(tnow);
            lbm.u.read_from_device();
            parallel_for(lbm.get_N(), [&](ulong n) {
                uint x=0u, y=0u, z=0u;
                lbm.coordinates(n, x, y, z);
                if(y == Ny-1u && z > 0u && (lbm.flags[n]&TYPE_S)!=TYPE_S) {
                    lbm.u.x[n] = 0.0f; lbm.u.y[n] = -0.1f; lbm.u.z[n] = 0.0f;
                }
            });
            lbm.u.write_to_device();
            #if defined(RECONSTRUCT_INLET_STRESS_DDF)
                lbm.reconstruct_inlet_stress_boundaries();
            #endif
        }
        lbm.run(1000u);
    }
}
"""


def run_patch(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_runtime_inlet_patch_") as raw:
        case_dir = Path(raw)
        setup = case_dir / "setup.cpp"
        setup.write_text(LEGACY_SETUP, encoding="utf-8")

        dry_manifest = case_dir / "dry.json"
        dry = run_patch("--case-dir", str(case_dir), "--out", str(dry_manifest), "--dry-run")
        if dry.returncode != 0:
            raise AssertionError((dry.returncode, dry.stdout, dry.stderr))
        dry_data = load(dry_manifest)
        if dry_data["Gate"] != "pass" or dry_data["WouldChange"] is not True or dry_data["Changed"] is not False:
            raise AssertionError(dry_data)
        if "citylbm_inlet_diagnostics_csv" in setup.read_text(encoding="utf-8"):
            raise AssertionError("dry-run edited setup.cpp")

        manifest = case_dir / "patch.json"
        result = run_patch("--case-dir", str(case_dir), "--out", str(manifest))
        if result.returncode != 0:
            raise AssertionError((result.returncode, result.stdout, result.stderr))
        data = load(manifest)
        if data["Gate"] != "pass" or data["Changed"] is not True or data["AlreadyPatched"] is not False:
            raise AssertionError(data)
        patched = setup.read_text(encoding="utf-8")
        for expected in [
            "#include <fstream>",
            "citylbm_inlet_diagnostics_csv",
            "writeSyntheticTurbulentInletDiagnostics",
            "writeSyntheticTurbulentInletDiagnostics(tnow);",
            "target_k_m2s2",
            "target_r11_m2s2",
            "target_r22_m2s2",
            "target_r33_m2s2",
            "target_r12_m2s2",
            "target_r13_m2s2",
            "target_r23_m2s2",
            "measured_r11_m2s2",
            "measured_r22_m2s2",
            "measured_r33_m2s2",
            "measured_r12_m2s2",
            "measured_r13_m2s2",
            "measured_r23_m2s2",
            "effective_sample_z_m",
            "profile_k_lbm[citylbm_pi]",
        ]:
            if expected not in patched:
                raise AssertionError((expected, patched))

        second = run_patch("--case-dir", str(case_dir), "--out", str(case_dir / "second.json"))
        if second.returncode != 0:
            raise AssertionError((second.returncode, second.stdout, second.stderr))
        second_data = load(case_dir / "second.json")
        if second_data["Gate"] != "pass" or second_data["AlreadyPatched"] is not True or second_data["Changed"] is not False:
            raise AssertionError(second_data)

    print("patch_legacy_runtime_inlet_diagnostics_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
