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
        if "source_velocity_field_only" not in spectral_report["paper_grade_inlet_source_gate_reasons"]:
            raise AssertionError(spectral_report["paper_grade_inlet_source_gate_reasons"])

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
