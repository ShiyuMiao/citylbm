#!/usr/bin/env python3
"""Smoke-test audit recognition of legacy Case E digital-filter inlet code."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_inlet_source.py"
CREATE_LENGTH_SCALE = REPO / "scripts" / "create_turbulence_length_scale_evidence_template.py"
BIND_LENGTH_SCALE = REPO / "scripts" / "bind_turbulence_length_scale_metadata.py"


SETUP = """void main_setup() {
    const uint profile_count = 2u;
    const float profile_origin_z_m = 0f;
    const float profile_dx_m = 3f;
    const float profile_z_m[2] = { 1.5f, 4.5f };
    const float profile_u_lbm[2] = { 0.07f, 0.08f };
    const float profile_k_lbm[2] = { 0.0003f, 0.0004f };
    const float profile_u_rms_lbm[2] = { 0.01f, 0.011f };
    const float profile_v_rms_lbm[2] = { 0.01f, 0.011f };
    const float profile_w_rms_lbm[2] = { 0.01f, 0.011f };
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
    auto turbulentWind = [&](uint x, uint z_cell, uint t_step) -> float3 {
        const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;
        float mean_u = interpProfile(profile_u_lbm, z_m);
        float u_rms = interpProfile(profile_u_rms_lbm, z_m);
        float v_rms = interpProfile(profile_v_rms_lbm, z_m);
        float w_rms = interpProfile(profile_w_rms_lbm, z_m);
        const uint df_index = (x%digital_plane_width)*SZ + z_cell;
        return float3(mean_u + u_rms*df_ru[df_index], v_rms*df_rv[df_index], w_rms*df_rw[df_index]);
    };
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
    lbm.reconstruct_equilibrium_boundaries();
}
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        setup = temp / "setup.cpp"
        defines = temp / "defines.hpp"
        metadata = temp / "case_metadata.json"
        out = temp / "audit.json"
        setup.write_text(SETUP, encoding="utf-8")
        defines.write_text(
            "#define EQUILIBRIUM_BOUNDARIES\n#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n",
            encoding="utf-8",
        )
        metadata.write_text(
            json.dumps(
                {
                    "SyntheticTurbulentInletMethod": "digital-filter diagnostic inlet",
                    "SyntheticEddy": {"Enabled": True},
                    "WindDirectionUnitVector": [0.0, -1.0, 0.0],
                }
            ),
            encoding="utf-8",
        )
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
                str(out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 2:
            raise AssertionError((result.returncode, result.stdout, result.stderr))
        data = json.loads(out.read_text(encoding="utf-8"))
        if data["has_digital_filter_kernel_evidence"] is not True:
            raise AssertionError(data)
        if data["has_digital_filter_state_evidence"] is not True:
            raise AssertionError(data)
        if data["inlet_source_gate"] != "pass":
            raise AssertionError(data)
        reasons = ";".join(data["inlet_source_gate_reasons"])
        if "sem_source_missing" in reasons:
            raise AssertionError(data)
        if data["paper_grade_inlet_source_gate"] != "fail":
            raise AssertionError(data)
        if data["has_length_scale_parameter"] is not True:
            raise AssertionError(data)
        if data["has_bound_length_scale_evidence"] is not False:
            raise AssertionError(data)
        if data["setup_inlet_codegen_route"] != "legacy_runtime_diagnostic_patch_route":
            raise AssertionError(data)
        if data["has_current_citylbm_stg_codegen_route"] is not False:
            raise AssertionError(data)
        if data["has_legacy_runtime_diagnostic_patch_route"] is not True:
            raise AssertionError(data)
        if data["short_canary_allowed_by_codegen_route"] is not False:
            raise AssertionError(data)

        source = temp / "aij_length_scale_source.txt"
        source.write_text("paper-admissible AIJ length-scale source for smoke test\n", encoding="utf-8")
        evidence = temp / "turbulence_length_scale_evidence.json"
        bound_metadata = temp / "case_metadata.length_scale_bound.json"
        create_length = subprocess.run(
            [
                sys.executable,
                str(CREATE_LENGTH_SCALE),
                "--metadata",
                str(metadata),
                "--source-path",
                str(source),
                "--source-type",
                "official_aij",
                "--source-note",
                "Smoke-test official length-scale evidence.",
                "--paper-admissible",
                "--case",
                "CaseE",
                "--wind-direction",
                "N",
                "--out",
                str(evidence),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if create_length.returncode != 0:
            raise AssertionError((create_length.returncode, create_length.stdout, create_length.stderr))
        bind_length = subprocess.run(
            [
                sys.executable,
                str(BIND_LENGTH_SCALE),
                "--metadata",
                str(metadata),
                "--evidence-json",
                str(evidence),
                "--out",
                str(bound_metadata),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if bind_length.returncode != 0:
            raise AssertionError((bind_length.returncode, bind_length.stdout, bind_length.stderr))
        bound_out = temp / "audit.bound.json"
        bound_result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--setup",
                str(setup),
                "--defines",
                str(defines),
                "--metadata",
                str(bound_metadata),
                "--out",
                str(bound_out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if bound_result.returncode != 2:
            raise AssertionError((bound_result.returncode, bound_result.stdout, bound_result.stderr))
        bound_data = json.loads(bound_out.read_text(encoding="utf-8"))
        if bound_data["has_bound_length_scale_evidence"] is not True:
            raise AssertionError(bound_data)
        if bound_data["inlet_length_scale_evidence_basis"] != "bound_evidence_json_and_metadata_gate":
            raise AssertionError(bound_data)
        if "source_missing_turbulent_length_scale_evidence" in bound_data["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(bound_data)

    print("inlet_source_legacy_digital_filter_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
