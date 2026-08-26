#!/usr/bin/env python3
"""Smoke-test legacy CustomTable profile-origin patching."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "patch_legacy_customtable_profile_origin.py"


LEGACY_SETUP = """void main_setup() {
    const uint profile_count = 3u;
    const float profile_z_m[3] = { 1.250000f, 2.500000f, 5.000000f };
    const float profile_z_cells[3] = { 0.416667f, 0.833333f, 1.666667f };
    const float profile_u_lbm[3] = { 0.070000f, 0.080000f, 0.090000f };
    const float profile_k_lbm[3] = { 0.000300f, 0.000350f, 0.000360f };
    const float profile_u_rms_lbm[3] = { 0.010000f, 0.011000f, 0.012000f };
    const float profile_v_rms_lbm[3] = { 0.010000f, 0.011000f, 0.012000f };
    const float profile_w_rms_lbm[3] = { 0.010000f, 0.011000f, 0.012000f };
    auto interpProfile = [&](const float* values, float z_cell) -> float {
        if(z_cell <= profile_z_cells[0]) return values[0];
        if(z_cell >= profile_z_cells[profile_count-1]) return values[profile_count-1];
        for(int i=0; i<(int)profile_count-1; ++i) {
            if(z_cell <= profile_z_cells[i+1]) {
                const float dz = fmax(profile_z_cells[i+1] - profile_z_cells[i], 1.0e-6f);
                const float t = (z_cell - profile_z_cells[i]) / dz;
                return values[i]*(1.0f-t) + values[i+1]*t;
            }
        }
        return values[profile_count-1];
    };
    auto windProfile = [&](uint z_cell) -> float3 {
        const float z = (float)z_cell + 0.5f;
        const float u_mag = interpProfile(profile_u_lbm, z);
        return float3(u_mag, 0.0f, 0.0f);
    };
    auto turbulentWind = [&](uint a_cell, uint z_cell, uint t_step) -> float3 {
        const float z = (float)z_cell + 0.5f;
        const float mean_u = interpProfile(profile_u_lbm, z);
        const float u_rms = turbulence_scale*interpProfile(profile_u_rms_lbm, z);
        const float v_rms = turbulence_scale*interpProfile(profile_v_rms_lbm, z);
        const float w_rms = turbulence_scale*interpProfile(profile_w_rms_lbm, z);
        const float k = interpProfile(profile_k_lbm, z);
        return float3(mean_u + u_rms + k, v_rms, w_rms);
    };
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
    with tempfile.TemporaryDirectory() as raw:
        case_dir = Path(raw)
        setup = case_dir / "setup.cpp"
        setup.write_text(LEGACY_SETUP, encoding="utf-8")
        (case_dir / "domain_origin.json").write_text(
            json.dumps({"DomainMin": [-300.0, -500.0, 0.0], "Dx": 3.0}, indent=2),
            encoding="utf-8",
        )

        dry_manifest = case_dir / "dry.json"
        dry = run_patch("--case-dir", str(case_dir), "--out", str(dry_manifest), "--dry-run")
        if dry.returncode != 0:
            raise AssertionError((dry.returncode, dry.stdout, dry.stderr))
        dry_data = load(dry_manifest)
        if dry_data["Gate"] != "pass" or dry_data["WouldChange"] is not True or dry_data["Changed"] is not False:
            raise AssertionError(dry_data)
        if "profile_origin_z_m" in setup.read_text(encoding="utf-8"):
            raise AssertionError("dry-run edited setup.cpp")

        manifest = case_dir / "patch.json"
        result = run_patch("--case-dir", str(case_dir), "--out", str(manifest))
        if result.returncode != 0:
            raise AssertionError((result.returncode, result.stdout, result.stderr))
        data = load(manifest)
        if data["Gate"] != "pass" or data["Changed"] is not True:
            raise AssertionError(data)
        patched = setup.read_text(encoding="utf-8")
        for expected in [
            "const float profile_origin_z_m = 0f;",
            "const float profile_dx_m = 3f;",
            "auto interpProfile = [&](const float* values, float z_m) -> float {",
            "z_m <= profile_z_m[0]",
            "profile_z_m[i+1] - profile_z_m[i]",
            "interpProfile(profile_k_lbm, z_m)",
        ]:
            if expected not in patched:
                raise AssertionError((expected, patched))
        if not re.search(r"z_m\s*=\s*profile_origin_z_m\s*\+\s*\(\s*\(?\s*float\s*\)?\s*z_cell\s*\+\s*0\.5f\s*\)\s*\*", patched):
            raise AssertionError(patched)

        second = run_patch("--case-dir", str(case_dir), "--out", str(case_dir / "second.json"))
        if second.returncode != 2:
            raise AssertionError((second.returncode, second.stdout, second.stderr))
        second_data = load(case_dir / "second.json")
        if "no_legacy_customtable_origin_patch_applied" not in second_data["Reasons"]:
            raise AssertionError(second_data)

    print("patch_legacy_customtable_profile_origin_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
