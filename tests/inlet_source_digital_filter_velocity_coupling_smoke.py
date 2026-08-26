#!/usr/bin/env python3
"""Smoke-test that digital-filter evidence must couple filtered fields into inlet velocity."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_inlet_source.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_audit(setup: Path, defines: Path, metadata: Path, out_json: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--setup",
            str(setup),
            "--defines",
            str(defines),
            "--metadata",
            str(metadata),
            "--out",
            str(out_json),
        ],
        cwd=str(REPO),
        text=True,
        capture_output=True,
    )
    if not out_json.exists():
        raise AssertionError((result.returncode, result.stdout, result.stderr))
    return result.returncode, json.loads(out_json.read_text(encoding="utf-8"))


SETUP_PREFIX = """
const uint profile_count = 2u;
const float profile_origin_z_m = 0.0f;
const float profile_dx_m = 3.0f;
const float profile_z_m[2] = {1.5f, 4.5f};
const float profile_u_lbm[2] = {0.07f, 0.08f};
const float profile_k_lbm[2] = {0.0003f, 0.0004f};
const float profile_u_rms_lbm[2] = {0.01f, 0.011f};
const float profile_v_rms_lbm[2] = {0.01f, 0.011f};
const float profile_w_rms_lbm[2] = {0.01f, 0.011f};
const uint turbulence_method = 3u;
const float digital_filter_alpha = 0.86f;
const float digital_filter_time_alpha = 0.93f;
const float digital_filter_time_beta = 0.36f;
const int digital_filter_radius = 4;
const uint digital_plane_width = 16u;
const uint digital_plane_count = digital_plane_width*SZ;
std::vector<float> df_ru(digital_plane_count, 0.0f);
std::vector<float> df_rv(digital_plane_count, 0.0f);
std::vector<float> df_rw(digital_plane_count, 0.0f);
std::vector<float> df_next_u(digital_plane_count, 0.0f);
std::vector<float> df_next_v(digital_plane_count, 0.0f);
std::vector<float> df_next_w(digital_plane_count, 0.0f);
bool df_initialized = false;
auto smoothPlane = [&](const std::vector<float>& raw, std::vector<float>& tmp, std::vector<float>& out) {
    for(uint a=0u; a<digital_plane_width; a++) {
        for(uint z=0u; z<SZ; z++) {
            float acc = 0.0f;
            float weight_sum = 0.0f;
            for(int da=-digital_filter_radius; da<=digital_filter_radius; ++da) {
                const float w = pow(digital_filter_alpha, (float)abs(da));
                acc += w*raw[a*SZ + z];
                weight_sum += w;
            }
            tmp[a*SZ + z] = acc / weight_sum;
        }
    }
    out = tmp;
};
auto updateDigitalFilter = [&](uint t_step) {
    std::vector<float> raw_u(digital_plane_count, 0.0f), raw_v(digital_plane_count, 0.0f), raw_w(digital_plane_count, 0.0f);
    std::vector<float> tmp(digital_plane_count, 0.0f);
    smoothPlane(raw_u, tmp, df_next_u);
    smoothPlane(raw_v, tmp, df_next_v);
    smoothPlane(raw_w, tmp, df_next_w);
    if(!df_initialized) { df_ru = df_next_u; df_rv = df_next_v; df_rw = df_next_w; df_initialized = true; return; }
    for(uint i=0u; i<digital_plane_count; i++) {
        df_ru[i] = digital_filter_time_alpha*df_ru[i] + digital_filter_time_beta*df_next_u[i];
        df_rv[i] = digital_filter_time_alpha*df_rv[i] + digital_filter_time_beta*df_next_v[i];
        df_rw[i] = digital_filter_time_alpha*df_rw[i] + digital_filter_time_beta*df_next_w[i];
    }
};
auto interpProfile = [&](const float* values, float z_m) -> float { return values[0]; };
"""


SETUP_SUFFIX = """
updateDigitalFilter(0u);
parallel_for(lbm.get_N(), [&](ulong n) {
    uint x=0u, y=0u, z=1u;
    lbm.flags[n] = TYPE_E;
    float3 u_in = turbulentWind(x, z, 0u);
    lbm.u.x[n] = u_in.x;
    lbm.u.y[n] = u_in.y;
    lbm.u.z[n] = u_in.z;
});
lbm.flags.write_to_device();
lbm.u.write_to_device();
lbm.reconstruct_inlet_stress_boundaries();
"""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_dfm_coupling_") as raw:
        root = Path(raw)
        metadata = root / "case_metadata.json"
        defines = root / "defines.hpp"
        bad_setup = root / "dfm_without_velocity_coupling.cpp"
        local_setup = root / "dfm_local_velocity_coupling.cpp"
        good_setup = root / "dfm_with_velocity_coupling.cpp"
        bad_out = root / "bad_audit.json"
        local_out = root / "local_audit.json"
        good_out = root / "good_audit.json"

        write_text(
            metadata,
            json.dumps(
                {
                    "SyntheticTurbulentInletMethod": "digital-filter",
                    "SyntheticTurbulentInletDistributionTreatment": "digital_filter_distribution_consistent",
                    "PaperGradeInletMethodClass": "digital_filter_distribution_consistent",
                    "SyntheticEddy": {"Enabled": True},
                },
                indent=2,
            ),
        )
        write_text(defines, "#define RECONSTRUCT_INLET_STRESS_DDF\n")
        write_text(
            bad_setup,
            SETUP_PREFIX
            + """
auto turbulentWind = [&](uint x, uint z_cell, uint t_step) -> float3 {
    const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;
    float mean_u = interpProfile(profile_u_lbm, z_m);
    return float3(mean_u, 0.0f, 0.0f);
};
"""
            + SETUP_SUFFIX,
        )
        write_text(
            local_setup,
            SETUP_PREFIX
            + """
auto turbulentWind = [&](uint x, uint z_cell, uint t_step) -> float3 {
    const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;
    float mean_u = interpProfile(profile_u_lbm, z_m);
    float u_rms = interpProfile(profile_u_rms_lbm, z_m);
    float v_rms = interpProfile(profile_v_rms_lbm, z_m);
    float w_rms = interpProfile(profile_w_rms_lbm, z_m);
    const uint df_index = (x%digital_plane_width)*SZ + z_cell;
    return float3(mean_u + u_rms*df_ru[df_index], v_rms*df_rv[df_index], w_rms*df_rw[df_index]);
};
"""
            + SETUP_SUFFIX,
        )
        write_text(
            good_setup,
            SETUP_PREFIX.replace(
                "acc += w*raw[a*SZ + z];",
                "const uint aa = (uint)((int(a) + int(digital_plane_width) + da) % int(digital_plane_width));\n"
                "                acc += w*raw[aa*SZ + z];",
            )
            + """
auto turbulentWind = [&](uint x, uint z_cell, uint t_step) -> float3 {
    const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;
    float mean_u = interpProfile(profile_u_lbm, z_m);
    float u_rms = interpProfile(profile_u_rms_lbm, z_m);
    float v_rms = interpProfile(profile_v_rms_lbm, z_m);
    float w_rms = interpProfile(profile_w_rms_lbm, z_m);
    const uint df_index = (x%digital_plane_width)*SZ + z_cell;
    return float3(mean_u + u_rms*df_ru[df_index], v_rms*df_rv[df_index], w_rms*df_rw[df_index]);
};
"""
            + SETUP_SUFFIX,
        )

        bad_code, bad_report = run_audit(bad_setup, defines, metadata, bad_out)
        if bad_code == 0:
            raise AssertionError("digital-filter source without velocity coupling unexpectedly passed")
        if bad_report["has_digital_filter_kernel_evidence"] is not True:
            raise AssertionError(bad_report)
        if bad_report["has_digital_filter_state_evidence"] is not True:
            raise AssertionError(bad_report)
        if bad_report["has_digital_filter_spatial_stencil_evidence"] is not False:
            raise AssertionError(bad_report)
        if bad_report["has_digital_filter_velocity_coupling_evidence"] is not False:
            raise AssertionError(bad_report)
        if "digital_filter_source_missing_spatial_neighbor_stencil" not in bad_report["inlet_source_gate_reasons"]:
            raise AssertionError(bad_report["inlet_source_gate_reasons"])
        if "digital_filter_source_missing_filtered_velocity_coupling" not in bad_report["inlet_source_gate_reasons"]:
            raise AssertionError(bad_report["inlet_source_gate_reasons"])
        if bad_report["inlet_source_method_class"] == "digital_filter_distribution_consistent":
            raise AssertionError(bad_report["inlet_source_method_class"])

        local_code, local_report = run_audit(local_setup, defines, metadata, local_out)
        if local_code == 0:
            raise AssertionError("local single-cell digital-filter source unexpectedly passed")
        if local_report["has_digital_filter_velocity_coupling_evidence"] is not True:
            raise AssertionError(local_report)
        if local_report["has_digital_filter_spatial_stencil_evidence"] is not False:
            raise AssertionError(local_report)
        if "digital_filter_source_missing_spatial_neighbor_stencil" not in local_report["inlet_source_gate_reasons"]:
            raise AssertionError(local_report["inlet_source_gate_reasons"])
        if local_report["inlet_source_method_class"] == "digital_filter_distribution_consistent":
            raise AssertionError(local_report["inlet_source_method_class"])

        good_code, good_report = run_audit(good_setup, defines, metadata, good_out)
        if good_code != 2:
            raise AssertionError((good_code, good_report))
        if good_report["has_digital_filter_spatial_stencil_evidence"] is not True:
            raise AssertionError(good_report)
        if good_report["has_digital_filter_velocity_coupling_evidence"] is not True:
            raise AssertionError(good_report)
        if good_report["inlet_source_method_class"] != "digital_filter_distribution_consistent":
            raise AssertionError(good_report["inlet_source_method_class"])
        if good_report["inlet_source_gate"] != "pass":
            raise AssertionError(good_report["inlet_source_gate_reasons"])
        if good_report["paper_grade_inlet_source_gate"] != "fail":
            raise AssertionError(good_report)

    print("inlet_source_digital_filter_velocity_coupling_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
