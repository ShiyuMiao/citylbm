#!/usr/bin/env python3
"""Smoke-test diagnostic canary case cloning and schedule shortening."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prepare_native_diagnostic_canary_case.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_diag_canary_case_") as raw:
        temp = Path(raw)
        source = temp / "source_case"
        target = temp / "canary_case"
        manifest = temp / "canary_manifest.json"
        write(
            source / "setup.cpp",
            """
void main_setup() {
    const char* citylbm_inlet_diagnostics_csv = "casee_scene_inlet_turbulence_stats.csv";
    const float profile_origin_z_m = 0f;
    const float profile_dx_m = 3f;
    const float epsilon = 1.0e-6f;
    const float citylbm_stg_scale = 1.000000f;
    const float citylbm_stg_temporal_step_scale = 0.500000f;
    const uint citylbm_stg_update_interval = 25u;
    lbm.run(48000u);
    lbm.run(0u);
    const uint citylbm_total_steps = 48000u;
    const uint citylbm_spinup_steps = 12000u;
    const uint citylbm_save_interval = 1000u;
    sampleProbes();
    print_info("Step: " + to_string(lbm.get_t()) + " / 48000");
}
""",
        )
        write(source / "defines.hpp", "#define FP16S\n")
        write(source / "domain_origin.json", "{}\n")
        write(source / "buildings.stl", "solid test\nendsolid test\n")
        write(source / "output" / "u-000001000.vtk", "large output should not be copied\n")
        write(
            source / "case_metadata.json",
            json.dumps(
                {
                    "time_averaging": {
                        "time_steps": 48000,
                        "spinup_steps": 12000,
                        "save_interval": 1000,
                    },
                    "SyntheticTurbulenceUpdateInterval": 25,
                    "SyntheticTurbulenceExpectedFinalWindowRefreshCount": 1440,
                    "outputs": {"case_dir": str(source), "probe_csv": "casee_probe_time_mean.csv"},
                },
                indent=2,
            ),
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-case-dir",
                str(source),
                "--out-case-dir",
                str(target),
                "--manifest-out",
                str(manifest),
                "--time-steps",
                "2000",
                "--spinup-steps",
                "500",
                "--vtk-save-interval",
                "500",
                "--synthetic-turbulence-update-interval",
                "2",
                "--synthetic-turbulence-intensity-scale",
                "1.414214",
                "--synthetic-turbulence-temporal-step-scale",
                "0.100000",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        data = load_json(manifest)
        if data["Gate"] != "pass":
            raise AssertionError(data)
        setup = (target / "setup.cpp").read_text(encoding="utf-8")
        for expected in [
            "lbm.run(2000u);",
            "lbm.run(0u);",
            "const float profile_origin_z_m = 0.000000f;",
            "const float profile_dx_m = 3.000000f;",
            "const float epsilon = 1.0e-6f;",
            "const float citylbm_stg_scale = 1.414214f;",
            "const float citylbm_stg_temporal_step_scale = 0.100000f;",
            "const uint citylbm_stg_update_interval = 2u;",
            "const uint citylbm_total_steps = 2000u;",
            "const uint citylbm_spinup_steps = 500u;",
            "const uint citylbm_save_interval = 500u;",
            "lbm.u.write_device_to_vtk(\"output/\", true);",
            "print_info(\"Step: \" + to_string(lbm.get_t()) + \" / 2000\");",
        ]:
            if expected not in setup:
                raise AssertionError(setup)
        if (target / "output" / "u-000001000.vtk").exists():
            raise AssertionError("VTK output was copied into diagnostic canary case")
        if " 0f" in setup or " 3f" in setup:
            raise AssertionError(setup)
        metadata = load_json(target / "case_metadata.json")
        if metadata["TimeSteps"] != 2000:
            raise AssertionError(metadata)
        if metadata["SaveInterval"] != 500 or metadata["VtkSaveInterval"] != 500:
            raise AssertionError(metadata)
        if metadata["SaveStartStep"] != 500 or metadata["ExpectedVtkFrameCount"] != 4:
            raise AssertionError(metadata)
        if metadata["SyntheticTurbulenceUpdateInterval"] != 2:
            raise AssertionError(metadata)
        if metadata["SyntheticTurbulenceIntensityScale"] != 1.414214:
            raise AssertionError(metadata)
        if metadata["SyntheticTurbulenceTemporalStepScale"] != 0.1:
            raise AssertionError(metadata)
        if metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] != 750:
            raise AssertionError(metadata)
        if metadata["DiagnosticCanary"]["SyntheticTurbulenceUpdateIntervalOverride"] != 2:
            raise AssertionError(metadata["DiagnosticCanary"])
        if metadata["DiagnosticCanary"]["SyntheticTurbulenceIntensityScaleOverride"] != 1.414214:
            raise AssertionError(metadata["DiagnosticCanary"])
        if metadata["DiagnosticCanary"]["SyntheticTurbulenceTemporalStepScaleOverride"] != 0.1:
            raise AssertionError(metadata["DiagnosticCanary"])
        if metadata["time_averaging"]["expected_post_spinup_frames"] != 4:
            raise AssertionError(metadata["time_averaging"])
        if metadata["RuntimeInletDiagnosticsCsv"] != "casee_scene_inlet_turbulence_stats.csv":
            raise AssertionError(metadata)
        if metadata["DiagnosticCanary"]["SourceCaseDir"] != str(source.resolve()):
            raise AssertionError(metadata["DiagnosticCanary"])

        loop_source = temp / "loop_source_case"
        loop_target = temp / "loop_canary_case"
        loop_manifest = temp / "loop_canary_manifest.json"
        write(
            loop_source / "setup.cpp",
            """
void main_setup() {
    const uint citylbm_stg_update_interval = 25u;
    while(lbm.get_t() < 60000u) {
        uint remaining = 60000u - (uint)lbm.get_t();
        uint steps_to_run = remaining < 1000u ? remaining : 1000u;
        uint save_remainder = (uint)lbm.get_t() % 1000u;
        uint until_next_save = save_remainder == 0u ? 1000u : 1000u - save_remainder;
        if(steps_to_run > until_next_save) steps_to_run = until_next_save;
        if(steps_to_run > citylbm_stg_update_interval) steps_to_run = citylbm_stg_update_interval;
        applySyntheticTurbulentInlet((uint)lbm.get_t());
        lbm.run(steps_to_run);
        if(((uint)lbm.get_t() >= 10000u && (uint)lbm.get_t() % 1000u == 0u) || (uint)lbm.get_t() >= 60000u) {
            lbm.u.write_device_to_vtk("output/", true);
        }
    }
}
""",
        )
        write(loop_source / "defines.hpp", "#define FP16S\n")
        write(loop_source / "domain_origin.json", "{}\n")
        write(loop_source / "buildings.stl", "solid test\nendsolid test\n")
        write(
            loop_source / "case_metadata.json",
            json.dumps(
                {
                    "SyntheticTurbulenceUpdateInterval": 25,
                    "SyntheticTurbulenceExpectedFinalWindowRefreshCount": 1560,
                },
                indent=2,
            ),
        )
        loop_completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-case-dir",
                str(loop_source),
                "--out-case-dir",
                str(loop_target),
                "--manifest-out",
                str(loop_manifest),
                "--time-steps",
                "2000",
                "--spinup-steps",
                "500",
                "--vtk-save-interval",
                "500",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if loop_completed.returncode != 0:
            raise AssertionError((loop_completed.returncode, loop_completed.stdout, loop_completed.stderr))
        loop_data = load_json(loop_manifest)
        if loop_data["Gate"] != "pass":
            raise AssertionError(loop_data)
        if loop_data["MetadataPatch"]["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] != 60:
            raise AssertionError(loop_data["MetadataPatch"])
        loop_setup = (loop_target / "setup.cpp").read_text(encoding="utf-8")
        for expected in [
            "while(lbm.get_t() < 2000u)",
            "uint remaining = 2000u - (uint)lbm.get_t();",
            "uint steps_to_run = remaining < 500u ? remaining : 500u;",
            "uint save_remainder = (uint)lbm.get_t() % 500u;",
            "uint until_next_save = save_remainder == 0u ? 500u : 500u - save_remainder;",
            "if(((uint)lbm.get_t() >= 500u && (uint)lbm.get_t() % 500u == 0u) || (uint)lbm.get_t() >= 2000u)",
        ]:
            if expected not in loop_setup:
                raise AssertionError(loop_setup)

        nested_source = temp / "nested_source_case"
        nested_target = nested_source / "preflight_custom" / "diagnostic_canary_case"
        nested_manifest = temp / "nested_canary_manifest.json"
        write(
            nested_source / "setup.cpp",
            """
void main_setup() {
    const float profile_origin_z_m = 0f;
    const uint citylbm_total_steps = 1000u;
    const uint citylbm_spinup_steps = 100u;
    const uint citylbm_save_interval = 100u;
    lbm.run(1000u);
}
""",
        )
        write(nested_source / "defines.hpp", "#define GRAPHICS\n")
        write(nested_source / "case_metadata.json", json.dumps({"TimeSteps": 1000}, indent=2))
        nested_completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source-case-dir",
                str(nested_source),
                "--out-case-dir",
                str(nested_target),
                "--manifest-out",
                str(nested_manifest),
                "--time-steps",
                "200",
                "--spinup-steps",
                "25",
                "--vtk-save-interval",
                "25",
                "--allow-existing",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if nested_completed.returncode != 0:
            raise AssertionError((nested_completed.returncode, nested_completed.stdout, nested_completed.stderr))
        nested_data = load_json(nested_manifest)
        if nested_data["Gate"] != "pass":
            raise AssertionError(nested_data)
        if not (nested_target / "setup.cpp").is_file():
            raise AssertionError("nested target was not populated")
        if (nested_target / "preflight_custom").exists():
            raise AssertionError("nested target copied itself recursively")

    print("prepare_native_diagnostic_canary_case_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
