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

        sem_setup = root / "sem_setup.cpp"
        sem_out = root / "sem_audit.json"
        write_text(
            sem_setup,
            """
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
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

    print("inlet_source_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
