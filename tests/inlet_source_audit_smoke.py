#!/usr/bin/env python3
"""Smoke-test inlet source audit paper-grade classification."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_audit(setup: Path, metadata: Path, out_json: Path) -> tuple[int, dict]:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_inlet_source.py"),
            "--setup",
            str(setup),
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
        raise AssertionError(
            f"audit did not write {out_json}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed.returncode, json.loads(out_json.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_inlet_source_") as tmp:
        root = Path(tmp)
        metadata = root / "case_metadata.json"
        write_text(
            metadata,
            json.dumps(
                {
                    "SyntheticTurbulentInletMethod": "STG-lite",
                    "SyntheticTurbulentInletDistributionTreatment": "velocity_field_only",
                    "SyntheticEddy": {"Enabled": True},
                },
                indent=2,
            ),
        )

        random_setup = root / "random_setup.cpp"
        random_out = root / "random_audit.json"
        write_text(
            random_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
float windProfile(uint z_cell) {
    const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * 1.0f;
    return profile_u_lbm[0] + z_m * 0.0f;
}
void applySyntheticTurbulentInlet(uint t_step) {
    const float sigma = sqrt(2.0f * profile_k_lbm[0] / 3.0f);
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            const float white_noise = 2.0f * random() - 1.0f;
            lbm.u.x[n] = windProfile(n) + sigma * white_noise;
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
for(uint remaining=100u; remaining>0u; ) {
    uint steps_to_run = remaining > citylbm_stg_update_interval ? citylbm_stg_update_interval : remaining;
    applySyntheticTurbulentInlet((uint)lbm.get_t());
    lbm.run(steps_to_run);
    remaining -= steps_to_run;
}
""",
        )
        random_code, random_report = run_audit(random_setup, metadata, random_out)
        if random_code == 0:
            raise AssertionError("uncorrelated random inlet unexpectedly passed")
        if random_report["paper_grade_inlet_source_gate"] != "fail":
            raise AssertionError(random_report["paper_grade_inlet_source_gate"])
        if random_report["synthetic_inlet_correlation_model"] != "uncorrelated_random_rms_velocity_field_only":
            raise AssertionError(random_report["synthetic_inlet_correlation_model"])
        if "synthetic_inlet_uses_uncorrelated_random_rms" not in random_report["inlet_source_gate_reasons"]:
            raise AssertionError(random_report["inlet_source_gate_reasons"])
        if "Do not describe" not in random_report["recommended_next_action"]:
            raise AssertionError(random_report["recommended_next_action"])
        if "source_missing_reynolds_stress_tensor_evidence" not in random_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(random_report["paper_grade_inlet_source_gate_reasons"])
        if random_report["has_three_component_fluctuation_evidence"]:
            raise AssertionError(random_report)
        if random_report["has_k_driven_three_component_stg"]:
            raise AssertionError(random_report)

        stl_random_setup = root / "stl_random_setup.cpp"
        stl_random_out = root / "stl_random_audit.json"
        write_text(
            stl_random_setup,
            """
#include <random>
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
std::mt19937 rng(1234u);
std::normal_distribution<float> gaussian_noise(0.0f, 1.0f);
void applySyntheticTurbulentInlet(uint t_step) {
    const float sigma = sqrt(2.0f * profile_k_lbm[0] / 3.0f);
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            lbm.u.x[n] = profile_u_lbm[0] + sigma * gaussian_noise(rng);
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
for(uint remaining=100u; remaining>0u; ) {
    uint steps_to_run = remaining > citylbm_stg_update_interval ? citylbm_stg_update_interval : remaining;
    applySyntheticTurbulentInlet((uint)lbm.get_t());
    lbm.run(steps_to_run);
    remaining -= steps_to_run;
}
""",
        )
        stl_random_code, stl_random_report = run_audit(stl_random_setup, metadata, stl_random_out)
        if stl_random_code == 0:
            raise AssertionError("STL random inlet unexpectedly passed")
        if stl_random_report["synthetic_inlet_correlation_model"] != "uncorrelated_random_rms_velocity_field_only":
            raise AssertionError(stl_random_report["synthetic_inlet_correlation_model"])
        if "synthetic_inlet_uses_uncorrelated_random_rms" not in stl_random_report["inlet_source_gate_reasons"]:
            raise AssertionError(stl_random_report["inlet_source_gate_reasons"])
        random_patterns = ";".join(stl_random_report["uncorrelated_random_inlet_patterns"])
        if "mt19937" not in random_patterns or "normal_distribution" not in random_patterns:
            raise AssertionError(random_patterns)
        if "distribution-consistent inlet" not in stl_random_report["recommended_next_action"]:
            raise AssertionError(stl_random_report["recommended_next_action"])

        dfm_metadata = root / "dfm_case_metadata.json"
        write_text(
            dfm_metadata,
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

        comment_only_dfm_setup = root / "comment_only_dfm_setup.cpp"
        comment_only_dfm_out = root / "comment_only_dfm_audit.json"
        write_text(
            comment_only_dfm_setup,
            """
// This comment claims a digital_filter / DFM / SEM inlet, but the code below
// is only a mean-profile velocity assignment.
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
void applyMeanInletOnly() {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            lbm.u.x[n] = profile_u_lbm[0];
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
""",
        )
        comment_dfm_code, comment_dfm_report = run_audit(
            comment_only_dfm_setup,
            dfm_metadata,
            comment_only_dfm_out,
        )
        if comment_dfm_code == 0:
            raise AssertionError("comment-only DFM/SEM claims unexpectedly passed")
        if comment_dfm_report["has_digital_filter_token"]:
            raise AssertionError(comment_dfm_report)
        if comment_dfm_report["has_sem_token"]:
            raise AssertionError(comment_dfm_report)
        if comment_dfm_report["inlet_source_comment_stripped_code_audit"] is not True:
            raise AssertionError(comment_dfm_report)
        if "metadata_requests_turbulent_inlet_but_source_has_no_inlet_method" not in comment_dfm_report["inlet_source_gate_reasons"]:
            raise AssertionError(comment_dfm_report["inlet_source_gate_reasons"])
        if "source_not_distribution_consistent" not in comment_dfm_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(comment_dfm_report["paper_grade_inlet_source_gate_reasons"])

        token_only_dfm_setup = root / "token_only_dfm_setup.cpp"
        token_only_dfm_out = root / "token_only_dfm_audit.json"
        write_text(
            token_only_dfm_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
const int citylbm_digital_filter_mode = 1;
void applyMeanInletOnly() {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            lbm.u.x[n] = profile_u_lbm[0];
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
""",
        )
        token_dfm_code, token_dfm_report = run_audit(
            token_only_dfm_setup,
            dfm_metadata,
            token_only_dfm_out,
        )
        if token_dfm_code == 0:
            raise AssertionError("token-only digital-filter source unexpectedly passed")
        if token_dfm_report["advanced_inlet_method_token_only"] is not True:
            raise AssertionError(token_dfm_report)
        if "advanced_inlet_method_tokens_without_code_evidence" not in token_dfm_report["inlet_source_gate_reasons"]:
            raise AssertionError(token_dfm_report["inlet_source_gate_reasons"])
        if "source_not_distribution_consistent" not in token_dfm_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(token_dfm_report["paper_grade_inlet_source_gate_reasons"])

        named_dfm_setup = root / "named_dfm_setup.cpp"
        named_dfm_out = root / "named_dfm_audit.json"
        write_text(
            named_dfm_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
void digital_filter_inlet(uint t_step) {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            lbm.u.x[n] = profile_u_lbm[0];
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
""",
        )
        named_dfm_code, named_dfm_report = run_audit(
            named_dfm_setup,
            dfm_metadata,
            named_dfm_out,
        )
        if named_dfm_code == 0:
            raise AssertionError("named DFM without kernel/state/distribution unexpectedly passed")
        if named_dfm_report["inlet_source_method_class"] != "named_method_without_distribution_evidence":
            raise AssertionError(named_dfm_report["inlet_source_method_class"])
        for expected_reason in [
            "digital_filter_source_missing_filter_kernel",
            "digital_filter_source_missing_spatiotemporal_filter_state",
            "advanced_inlet_method_missing_distribution_evidence",
        ]:
            if expected_reason not in named_dfm_report["inlet_source_gate_reasons"]:
                raise AssertionError(named_dfm_report["inlet_source_gate_reasons"])

        spectral_setup = root / "spectral_setup.cpp"
        spectral_out = root / "spectral_audit.json"
        write_text(
            spectral_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
const int citylbm_stg_mode_count = 64;
const float citylbm_stg_corr_cells = 8.0f;
const uint citylbm_stg_update_interval = 5u;
const float citylbm_stg_max_fraction = 0.5f;
const float citylbm_stg_min_streamwise_fraction = 0.0f;
const uint Nz = 16u;
const float dir_x = 1.0f, dir_y = 0.0f, dir_z = 0.0f;
float citylbm_mode_wave(int mode, int axis) { return (1.0f + mode + axis) / citylbm_stg_corr_cells; }
float citylbm_mode_amplitude(int mode, int axis) { return 0.1f + mode + axis; }
float3 windProfile(uint z_cell) {
    const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * 1.0f;
    return float3(profile_u_lbm[0] + z_m * 0.0f, 0.0f, 0.0f);
}
float interpolate_profile_k(float z_m) { return profile_k_lbm[0]; }
float3 syntheticTurbulentInlet(uint x, uint y, uint z_cell, uint t_step) {
    float3 mean = windProfile(z_cell);
    float k_lbm = interpolate_profile_k(profile_origin_z_m + ((float)z_cell + 0.5f) * 1.0f);
    float sigma = sqrtf(0.6666667f * k_lbm);
    float mean_mag = sqrtf(mean.x*mean.x + mean.y*mean.y + mean.z*mean.z);
    float advected_x = (float)x - dir_x * mean_mag * (float)t_step;
    float advected_y = (float)y - dir_y * mean_mag * (float)t_step;
    float advected_z = (float)z_cell - dir_z * mean_mag * (float)t_step;
    float fluct_x = 0.0f, fluct_y = 0.0f, fluct_z = 0.0f;
    for(int m=0; m<citylbm_stg_mode_count; m++) {
        float kx = citylbm_mode_wave(m, 0);
        float ky = citylbm_mode_wave(m, 1);
        float kz = citylbm_mode_wave(m, 2);
        float ax = citylbm_mode_amplitude(m, 0);
        float ay = citylbm_mode_amplitude(m, 1);
        float az = citylbm_mode_amplitude(m, 2);
        float kk = kx*kx + ky*ky + kz*kz;
        float ak = ax*kx + ay*ky + az*kz;
        if(kk > 1.0e-12f) { ax -= ak*kx/kk; ay -= ak*ky/kk; az -= ak*kz/kk; }
        float wave = sinf(kx * advected_x + ky * advected_y + kz * advected_z);
        fluct_x += ax * wave;
        fluct_y += ay * wave;
        fluct_z += az * wave;
    }
    return float3(mean.x + sigma * fluct_x, mean.y + sigma * fluct_y, mean.z + sigma * fluct_z);
}
void applySyntheticTurbulentInlet(uint t_step) {
    std::vector<float> citylbm_stg_layer_mean_correction_x(Nz, 0.0f);
    std::vector<float> citylbm_stg_layer_mean_correction_y(Nz, 0.0f);
    std::vector<float> citylbm_stg_layer_mean_correction_z(Nz, 0.0f);
    std::vector<ulong> citylbm_stg_layer_corrected_inlet_count(Nz, 0ull);
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            uint z = n;
            float3 mean = windProfile(n);
            float3 u_in = syntheticTurbulentInlet(0u, 0u, z, t_step);
            citylbm_stg_layer_mean_correction_x[z] += u_in.x - mean.x;
            citylbm_stg_layer_mean_correction_y[z] += u_in.y - mean.y;
            citylbm_stg_layer_mean_correction_z[z] += u_in.z - mean.z;
            citylbm_stg_layer_corrected_inlet_count[z]++;
        }
    }
    for(uint z_layer=0u; z_layer<Nz; z_layer++) {
        if(citylbm_stg_layer_corrected_inlet_count[z_layer] > 0ull) {
            float inv_count = 1.0f / (float)citylbm_stg_layer_corrected_inlet_count[z_layer];
            citylbm_stg_layer_mean_correction_x[z_layer] *= inv_count;
            citylbm_stg_layer_mean_correction_y[z_layer] *= inv_count;
            citylbm_stg_layer_mean_correction_z[z_layer] *= inv_count;
        }
    }
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            uint z = n;
            float3 u_in = syntheticTurbulentInlet(0u, 0u, z, t_step);
            u_in.x -= citylbm_stg_layer_mean_correction_x[z];
            u_in.y -= citylbm_stg_layer_mean_correction_y[z];
            u_in.z -= citylbm_stg_layer_mean_correction_z[z];
            lbm.u.x[n] = u_in.x;
            lbm.u.y[n] = u_in.y;
            lbm.u.z[n] = u_in.z;
        }
    }
}
for(uint remaining=100u; remaining>0u; ) {
    uint steps_to_run = remaining > citylbm_stg_update_interval ? citylbm_stg_update_interval : remaining;
    applySyntheticTurbulentInlet((uint)lbm.get_t());
    lbm.run(steps_to_run);
    remaining -= steps_to_run;
}
""",
        )
        spectral_code, spectral_report = run_audit(spectral_setup, metadata, spectral_out)
        if spectral_code == 0:
            raise AssertionError("velocity-field-only spectral STG unexpectedly passed paper gate")
        if spectral_report["inlet_source_gate"] != "pass":
            raise AssertionError(spectral_report)
        if spectral_report["paper_grade_inlet_source_gate"] != "fail":
            raise AssertionError(spectral_report)
        if spectral_report["synthetic_inlet_correlation_model"] != "spectral_taylor_projected_velocity_field_only":
            raise AssertionError(spectral_report["synthetic_inlet_correlation_model"])
        if not spectral_report["has_three_component_velocity_write"]:
            raise AssertionError(spectral_report)
        if not spectral_report["has_three_component_fluctuation_evidence"]:
            raise AssertionError(spectral_report)
        if not spectral_report["has_k_driven_three_component_stg"]:
            raise AssertionError(spectral_report)
        if not spectral_report["has_mean_preserving_inlet_correction"]:
            raise AssertionError(spectral_report)
        if not spectral_report["has_layerwise_mean_preserving_inlet_correction"]:
            raise AssertionError(spectral_report)
        if "source_velocity_field_only" not in spectral_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(spectral_report["paper_grade_inlet_source_gate_reasons"])
        if spectral_report["has_streamwise_clipping_control"] is not True:
            raise AssertionError(spectral_report)
        if abs(float(spectral_report["streamwise_min_fraction"]) - 0.0) > 1.0e-12:
            raise AssertionError(spectral_report)
        if spectral_report["streamwise_clipping_enabled"] is not False:
            raise AssertionError(spectral_report)
        if spectral_report["has_legacy_hardcoded_streamwise_clipping"] is not False:
            raise AssertionError(spectral_report)

        legacy_clip_setup = root / "legacy_clip_setup.cpp"
        legacy_clip_out = root / "legacy_clip_audit.json"
        write_text(
            legacy_clip_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
const int citylbm_stg_mode_count = 64;
const float citylbm_stg_corr_cells = 8.0f;
const uint citylbm_stg_update_interval = 5u;
const float citylbm_stg_max_fraction = 0.5f;
float3 windProfile(uint z_cell) { return float3(profile_u_lbm[0], 0.0f, 0.0f); }
float3 syntheticTurbulentInlet(uint x, uint y, uint z_cell, uint t_step) {
    float3 mean = windProfile(z_cell);
    float mean_mag = sqrtf(mean.x*mean.x + mean.y*mean.y + mean.z*mean.z);
    float min_streamwise = 0.05f * (mean_mag > 1.0e-12f ? mean_mag : 1.0f);
    return float3(min_streamwise, 0.0f, 0.0f);
}
void applySyntheticTurbulentInlet(uint t_step) {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            float3 u_in = syntheticTurbulentInlet(0u, 0u, n, t_step);
            lbm.u.x[n] = u_in.x;
            lbm.u.y[n] = u_in.y;
            lbm.u.z[n] = u_in.z;
        }
    }
}
for(uint remaining=100u; remaining>0u; ) {
    uint steps_to_run = remaining > citylbm_stg_update_interval ? citylbm_stg_update_interval : remaining;
    applySyntheticTurbulentInlet((uint)lbm.get_t());
    lbm.run(steps_to_run);
    remaining -= steps_to_run;
}
""",
        )
        legacy_clip_code, legacy_clip_report = run_audit(legacy_clip_setup, metadata, legacy_clip_out)
        if legacy_clip_code == 0:
            raise AssertionError("legacy streamwise clipping unexpectedly passed")
        if legacy_clip_report["has_legacy_hardcoded_streamwise_clipping"] is not True:
            raise AssertionError(legacy_clip_report)
        if "synthetic_inlet_uses_legacy_hardcoded_streamwise_clipping" not in legacy_clip_report["inlet_source_gate_reasons"]:
            raise AssertionError(legacy_clip_report["inlet_source_gate_reasons"])

        face_mean_setup = root / "face_mean_setup.cpp"
        face_mean_out = root / "face_mean_audit.json"
        write_text(
            face_mean_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
const int citylbm_stg_mode_count = 64;
const float citylbm_stg_corr_cells = 8.0f;
const uint citylbm_stg_update_interval = 5u;
const float citylbm_stg_max_fraction = 0.5f;
const float dir_x = 1.0f, dir_y = 0.0f, dir_z = 0.0f;
float citylbm_mode_wave(int mode, int axis) { return (1.0f + mode + axis) / citylbm_stg_corr_cells; }
float citylbm_mode_amplitude(int mode, int axis) { return 0.1f + mode + axis; }
float3 windProfile(uint z_cell) { return float3(profile_u_lbm[0], 0.0f, 0.0f); }
float interpolate_profile_k(float z_m) { return profile_k_lbm[0]; }
float3 syntheticTurbulentInlet(uint x, uint y, uint z_cell, uint t_step) {
    float3 mean = windProfile(z_cell);
    float k_lbm = interpolate_profile_k(profile_origin_z_m + ((float)z_cell + 0.5f) * 1.0f);
    float sigma = sqrtf(0.6666667f * k_lbm);
    float mean_mag = sqrtf(mean.x*mean.x + mean.y*mean.y + mean.z*mean.z);
    float advected_x = (float)x - dir_x * mean_mag * (float)t_step;
    float advected_y = (float)y - dir_y * mean_mag * (float)t_step;
    float advected_z = (float)z_cell - dir_z * mean_mag * (float)t_step;
    float fluct_x = 0.0f, fluct_y = 0.0f, fluct_z = 0.0f;
    for(int m=0; m<citylbm_stg_mode_count; m++) {
        float kx = citylbm_mode_wave(m, 0);
        float ky = citylbm_mode_wave(m, 1);
        float kz = citylbm_mode_wave(m, 2);
        float ax = citylbm_mode_amplitude(m, 0);
        float ay = citylbm_mode_amplitude(m, 1);
        float az = citylbm_mode_amplitude(m, 2);
        float kk = kx*kx + ky*ky + kz*kz;
        float ak = ax*kx + ay*ky + az*kz;
        if(kk > 1.0e-12f) { ax -= ak*kx/kk; ay -= ak*ky/kk; az -= ak*kz/kk; }
        float wave = sinf(kx * advected_x + ky * advected_y + kz * advected_z);
        fluct_x += ax * wave;
        fluct_y += ay * wave;
        fluct_z += az * wave;
    }
    return float3(mean.x + sigma * fluct_x, mean.y + sigma * fluct_y, mean.z + sigma * fluct_z);
}
void applySyntheticTurbulentInlet(uint t_step) {
    float3 citylbm_stg_mean_correction = float3(0.0f, 0.0f, 0.0f);
    ulong citylbm_stg_corrected_inlet_count = 0ull;
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            float3 mean = windProfile(n);
            float3 u_in = syntheticTurbulentInlet(0u, 0u, n, t_step);
            citylbm_stg_mean_correction.x += u_in.x - mean.x;
            citylbm_stg_mean_correction.y += u_in.y - mean.y;
            citylbm_stg_mean_correction.z += u_in.z - mean.z;
            citylbm_stg_corrected_inlet_count++;
        }
    }
    if(citylbm_stg_corrected_inlet_count > 0ull) {
        float inv_count = 1.0f / (float)citylbm_stg_corrected_inlet_count;
        citylbm_stg_mean_correction.x *= inv_count;
        citylbm_stg_mean_correction.y *= inv_count;
        citylbm_stg_mean_correction.z *= inv_count;
    }
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            float3 u_in = syntheticTurbulentInlet(0u, 0u, n, t_step);
            u_in.x -= citylbm_stg_mean_correction.x;
            u_in.y -= citylbm_stg_mean_correction.y;
            u_in.z -= citylbm_stg_mean_correction.z;
            lbm.u.x[n] = u_in.x;
            lbm.u.y[n] = u_in.y;
            lbm.u.z[n] = u_in.z;
        }
    }
}
for(uint remaining=100u; remaining>0u; ) {
    uint steps_to_run = remaining > citylbm_stg_update_interval ? citylbm_stg_update_interval : remaining;
    applySyntheticTurbulentInlet((uint)lbm.get_t());
    lbm.run(steps_to_run);
    remaining -= steps_to_run;
}
""",
        )
        face_mean_code, face_mean_report = run_audit(face_mean_setup, metadata, face_mean_out)
        if face_mean_code == 0:
            raise AssertionError("face-mean STG unexpectedly passed inlet source gate")
        if face_mean_report["has_mean_preserving_inlet_correction"] is not True:
            raise AssertionError(face_mean_report)
        if face_mean_report["has_layerwise_mean_preserving_inlet_correction"] is not False:
            raise AssertionError(face_mean_report)
        if "synthetic_inlet_missing_layerwise_mean_preserving_inlet_correction" not in face_mean_report["inlet_source_gate_reasons"]:
            raise AssertionError(face_mean_report["inlet_source_gate_reasons"])

        named_recycling_setup = root / "named_recycling_setup.cpp"
        named_recycling_out = root / "named_recycling_audit.json"
        write_text(
            named_recycling_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
void recycling_rescaling_inlet(uint t_step) {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            lbm.u.x[n] = profile_u_lbm[0];
            lbm.u.y[n] = 0.0f;
            lbm.u.z[n] = 0.0f;
        }
    }
}
""",
        )
        named_recycling_code, named_recycling_report = run_audit(
            named_recycling_setup,
            metadata,
            named_recycling_out,
        )
        if named_recycling_code == 0:
            raise AssertionError("named recycling inlet without recycled field unexpectedly passed")
        if named_recycling_report["inlet_source_gate"] != "fail":
            raise AssertionError(named_recycling_report)
        if named_recycling_report["inlet_source_method_class"] != "named_method_without_precursor_recycling_field_evidence":
            raise AssertionError(named_recycling_report["inlet_source_method_class"])
        if "precursor_recycling_method_missing_recycled_field_evidence" not in named_recycling_report["inlet_source_gate_reasons"]:
            raise AssertionError(named_recycling_report["inlet_source_gate_reasons"])

        precursor_velocity_setup = root / "precursor_velocity_setup.cpp"
        precursor_velocity_out = root / "precursor_velocity_audit.json"
        write_text(
            precursor_velocity_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_origin_z_m = 0.0f;
float3 recycling_buffer[16];
void recycling_rescaling_inlet(uint t_step) {
    for(uint n=0u; n<10u; n++) {
        if(flags[n]==TYPE_E) {
            float3 u_in = recycling_buffer[n];
            lbm.u.x[n] = u_in.x;
            lbm.u.y[n] = u_in.y;
            lbm.u.z[n] = u_in.z;
        }
    }
}
""",
        )
        precursor_velocity_code, precursor_velocity_report = run_audit(
            precursor_velocity_setup,
            metadata,
            precursor_velocity_out,
        )
        if precursor_velocity_code == 0:
            raise AssertionError("precursor/recycling velocity-only inlet unexpectedly passed")
        if precursor_velocity_report["inlet_source_method_class"] != "precursor_or_recycling_velocity_field_only":
            raise AssertionError(precursor_velocity_report["inlet_source_method_class"])
        if "precursor_recycling_source_missing_inlet_distribution_reconstruction" not in precursor_velocity_report["inlet_source_gate_reasons"]:
            raise AssertionError(precursor_velocity_report["inlet_source_gate_reasons"])
        if "source_velocity_field_only" not in precursor_velocity_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(precursor_velocity_report["paper_grade_inlet_source_gate_reasons"])

        sem_setup = root / "sem_setup.cpp"
        sem_out = root / "sem_audit.json"
        write_text(
            sem_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
const float profile_r11_lbm[] = {0.000066f, 0.000133f};
const float profile_r22_lbm[] = {0.000066f, 0.000133f};
const float profile_r33_lbm[] = {0.000066f, 0.000133f};
const float synthetic_eddy_length_scale = 4.0f;
const float profile_origin_z_m = 0.0f;
struct SemEddy { float eddy_center; float eddy_radius; float eddy_strength; float eddy_lifetime; };
SemEddy sem_eddy[64];
void sem_distribution(uint t_step) {}
float calculate_f_eq(uint q, float rho, float ux, float uy, float uz) { return rho + ux + uy + uz + q; }
void reconstructSyntheticEddyInletDistributions(uint n) {
    if(flags[n]==TYPE_E) {
        const uint z_cell = n;
        const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * 1.0f;
        const float ux = profile_u_lbm[0] + z_m * 0.0f;
        lbm.u.x[n] = ux;
        for(uint q=0u; q<19u; q++) {
            lbm.f[n*19u+q] = calculate_f_eq(q, 1.0f, ux, 0.0f, 0.0f);
        }
    }
}
void applySyntheticTurbulentInlet(uint t_step) {
    sem_distribution(t_step);
    reconstructSyntheticEddyInletDistributions(0u);
}
""",
        )
        sem_code, sem_report = run_audit(sem_setup, metadata, sem_out)
        if sem_code != 0:
            raise AssertionError(sem_report)
        if sem_report["paper_grade_inlet_source_gate"] != "pass":
            raise AssertionError(sem_report["paper_grade_inlet_source_gate"])
        if sem_report["inlet_source_method_class"] != "synthetic_eddy_distribution_consistent":
            raise AssertionError(sem_report["inlet_source_method_class"])
        if sem_report["distribution_consistency_basis"] != "sem_eddy_population_distribution_reconstruction":
            raise AssertionError(sem_report["distribution_consistency_basis"])
        if sem_report["reynolds_stress_treatment"] != "full_tensor_or_precursor_evidence":
            raise AssertionError(sem_report["reynolds_stress_treatment"])
        if not sem_report["has_inlet_length_scale_evidence"]:
            raise AssertionError(sem_report)

    print("inlet_source_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
