#!/usr/bin/env python3
"""Smoke-test the native FluidX3D runner manifest and install path."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
PROTOCOL_STATUSES = {
    "inlet_mean_profile": "pass",
    "inlet_turbulence_k": "pass",
    "inlet_turbulence_length_scale": "pass",
    "inlet_reynolds_stress_tensor": "pass",
    "inlet_temporal_sampling": "pass",
    "inlet_distribution_consistency": "pass",
    "native_fluidx3d_baseline": "pass",
    "boundary_conditions": "pass",
    "wall_roughness_model": "pass",
    "lbm_stability_scaling": "pass",
    "time_averaging": "pass",
    "wind_direction_sign": "pass",
    "coordinate_transform": "pass",
    "probe_projection": "pass",
    "normalization_basis": "pass",
    "systematic_bias_gate": "pass",
    "grid_resolution": "pass",
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(args: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def create_source(root: Path) -> None:
    write(root / "FluidX3D.sln", "Microsoft Visual Studio Solution File\n")
    write(root / "src" / "setup.cpp", "// original native setup\n")
    write(root / "src" / "defines.hpp", "// original native defines\n")
    write(root / "src" / "lbm.hpp", "// lbm header\n")
    write(root / "src" / "lbm.cpp", "// lbm source\n")


def validation_protocol_audit(status_overrides: dict | None = None) -> dict:
    status_overrides = status_overrides or {}
    return {
        "SchemaVersion": 1,
        "Gate": "ready_for_validation_run",
        "Items": [
            {"Key": key, "Status": status_overrides.get(key, status), "Evidence": "smoke"}
            for key, status in PROTOCOL_STATUSES.items()
        ],
    }


def create_case(root: Path, *, citylbm_root_layout: bool = False) -> None:
    setup_path = root / "setup.cpp" if citylbm_root_layout else root / "src" / "setup.cpp"
    defines_path = root / "defines.hpp" if citylbm_root_layout else root / "src" / "defines.hpp"
    write(setup_path, "// case setup\n")
    write(defines_path, "// case defines\n")
    metadata = {
        "AijCase": "CaseA",
        "WindDirection": "N",
        "SyntheticTurbulentInletRequested": True,
        "SyntheticTurbulentInletInjected": True,
        "SyntheticTurbulenceUpdateInterval": 100,
        "SyntheticTurbulenceMinimumRecommendedRefreshes": 200,
        "SyntheticTurbulenceExpectedFinalWindowRefreshCount": 390,
    }
    write(root / "case_metadata.json", json.dumps(metadata, indent=2))
    write(root / "domain_origin.json", json.dumps({"origin": [0, 0, 0]}, indent=2))
    write(root / "validation_protocol_audit.json", json.dumps(validation_protocol_audit(), indent=2))
    write(root / "buildings.stl", "solid smoke\nendsolid smoke\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        dry_manifest = temp / "dry" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(dry_manifest),
                "--baseline-id",
                "smoke-casea-native",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ]
        )
        dry = load_json(dry_manifest)
        if dry["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(dry["RunnerGate"])
        if dry["NativeFluidX3DPathExplicitlyProvided"] is not True:
            raise AssertionError("native path was not marked explicit")
        if dry["NativeFluidX3DSourceValidation"]["IsValid"] is not True:
            raise AssertionError(dry["NativeFluidX3DSourceValidation"])
        if dry["ValidationProtocolAuditGate"]["Gate"] != "pass":
            raise AssertionError(dry["ValidationProtocolAuditGate"])
        if dry["ValidationProtocolAuditGate"]["Statuses"]["inlet_distribution_consistency"] != "pass":
            raise AssertionError(dry["ValidationProtocolAuditGate"])
        if dry["PlannedSyntheticInletSamplingGate"]["Gate"] != "pass":
            raise AssertionError(dry["PlannedSyntheticInletSamplingGate"])
        if dry["PlannedSyntheticInletSamplingGate"]["ComputedRefreshCount"] != 390:
            raise AssertionError(dry["PlannedSyntheticInletSamplingGate"])
        if dry["ActualVtkOutputGate"]["Gate"] != "not_applicable":
            raise AssertionError(dry["ActualVtkOutputGate"])
        if dry["Install"]["Performed"] is not False:
            raise AssertionError(dry["Install"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// original native setup\n":
            raise AssertionError("dry-run modified source setup.cpp")
        roles = {record["Role"] for record in dry["RequiredSourceFiles"]}
        for role in [
            "Native FluidX3D original setup",
            "Native FluidX3D original defines",
            "Native FluidX3D lbm.hpp",
            "Native FluidX3D lbm.cpp",
            "FluidX3D setup",
            "FluidX3D defines",
            "Case metadata",
            "Domain origin",
            "Validation protocol audit",
        ]:
            if role not in roles:
                raise AssertionError(f"missing manifest role: {role}")

        install_manifest = temp / "install" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(install_manifest),
                "--baseline-id",
                "smoke-casea-native-install",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--install",
            ]
        )
        installed = load_json(install_manifest)
        if installed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(installed["RunnerGate"])
        if installed["Install"]["Performed"] is not True:
            raise AssertionError(installed["Install"])
        if len(installed["Install"]["Backups"]) != 2:
            raise AssertionError(installed["Install"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// case setup\n":
            raise AssertionError("install did not replace setup.cpp")
        if not (install_manifest.parent / "native_source_backups").exists():
            raise AssertionError("backup directory was not created")

        citylbm_layout_source = temp / "FluidX3D_citylbm_layout"
        citylbm_layout_case = temp / "citylbm_layout_case"
        create_source(citylbm_layout_source)
        create_case(citylbm_layout_case, citylbm_root_layout=True)

        citylbm_layout_manifest = temp / "citylbm_layout" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(citylbm_layout_case),
                "--fluidx3d-source",
                str(citylbm_layout_source),
                "--out",
                str(citylbm_layout_manifest),
                "--baseline-id",
                "smoke-casea-native-citylbm-layout",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--install",
            ]
        )
        citylbm_layout = load_json(citylbm_layout_manifest)
        if citylbm_layout["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(citylbm_layout["RunnerGate"])
        by_role = {record["Role"]: record for record in citylbm_layout["RequiredSourceFiles"]}
        if by_role["FluidX3D setup"]["SelectedRelativePath"] != "setup.cpp":
            raise AssertionError(by_role["FluidX3D setup"])
        if by_role["FluidX3D defines"]["SelectedRelativePath"] != "defines.hpp":
            raise AssertionError(by_role["FluidX3D defines"])
        if citylbm_layout["Install"]["Performed"] is not True:
            raise AssertionError(citylbm_layout["Install"])
        if (citylbm_layout_source / "src" / "setup.cpp").read_text(encoding="utf-8") != "// case setup\n":
            raise AssertionError("CityLBM root-layout setup.cpp was not installed into native src/setup.cpp")
        if (citylbm_layout_source / "src" / "defines.hpp").read_text(encoding="utf-8") != "// case defines\n":
            raise AssertionError("CityLBM root-layout defines.hpp was not installed into native src/defines.hpp")

        short_manifest = temp / "short" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(short_manifest),
                "--baseline-id",
                "smoke-casea-native-short",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "5000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "5",
            ],
            expected_returncode=2,
        )
        short = load_json(short_manifest)
        if short["RunnerGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(short["RunnerGate"])
        if "planned_vtk_frame_count_5_below_minimum_40" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "planned_final_window_step_span_4000_below_minimum_20000" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "planned_stg_refresh_count_40_below_minimum_200" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "metadata_stg_refresh_count_390_does_not_match_computed_40" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])

        incomplete_protocol_case = temp / "incomplete_protocol_case"
        create_case(incomplete_protocol_case)
        write(
            incomplete_protocol_case / "validation_protocol_audit.json",
            json.dumps(
                validation_protocol_audit(
                    {
                        "inlet_turbulence_k": "partial",
                        "boundary_conditions": "risk",
                    }
                ),
                indent=2,
            ),
        )
        incomplete_protocol_manifest = temp / "incomplete_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(incomplete_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(incomplete_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-incomplete-protocol",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        incomplete_protocol = load_json(incomplete_protocol_manifest)
        for reason in [
            "validation_protocol_item_partial:inlet_turbulence_k",
            "validation_protocol_item_risk:boundary_conditions",
        ]:
            if reason not in incomplete_protocol["RunnerGate"]["Reasons"]:
                raise AssertionError(incomplete_protocol["RunnerGate"])

        bad_gate_case = temp / "bad_gate_case"
        create_case(bad_gate_case)
        bad_gate_audit = validation_protocol_audit()
        bad_gate_audit["Gate"] = "not_paper_grade"
        write(bad_gate_case / "validation_protocol_audit.json", json.dumps(bad_gate_audit, indent=2))
        bad_gate_manifest = temp / "bad_gate" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(bad_gate_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(bad_gate_manifest),
                "--baseline-id",
                "smoke-casea-native-bad-protocol-gate",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        bad_gate = load_json(bad_gate_manifest)
        if "validation_protocol_audit_gate_not_paper_grade:not_paper_grade" not in bad_gate["RunnerGate"]["Reasons"]:
            raise AssertionError(bad_gate["RunnerGate"])

        slow_refresh_case = temp / "slow_refresh_case"
        create_case(slow_refresh_case)
        slow_metadata_path = slow_refresh_case / "case_metadata.json"
        slow_metadata = load_json(slow_metadata_path)
        slow_metadata["SyntheticTurbulenceUpdateInterval"] = 500
        slow_metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] = 78
        write(slow_metadata_path, json.dumps(slow_metadata, indent=2))
        slow_refresh_manifest = temp / "slow_refresh" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(slow_refresh_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(slow_refresh_manifest),
                "--baseline-id",
                "smoke-casea-native-slow-stg-refresh",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        slow_refresh = load_json(slow_refresh_manifest)
        if slow_refresh["PlannedVtkScheduleGate"]["Gate"] != "pass":
            raise AssertionError(slow_refresh["PlannedVtkScheduleGate"])
        if slow_refresh["PlannedSyntheticInletSamplingGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(slow_refresh["PlannedSyntheticInletSamplingGate"])
        if "planned_stg_refresh_count_78_below_minimum_200" not in slow_refresh["RunnerGate"]["Reasons"]:
            raise AssertionError(slow_refresh["RunnerGate"])

        partial_output = temp / "partial_output"
        write(partial_output / "u-000001000.vtk", "# vtk DataFile Version 3.0\nsmoke\n")
        partial_output_manifest = temp / "partial_output_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(partial_output_manifest),
                "--baseline-id",
                "smoke-casea-native-partial-output",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--output-dir",
                str(partial_output),
            ],
            expected_returncode=2,
        )
        partial_output_result = load_json(partial_output_manifest)
        if partial_output_result["ActualVtkOutputGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(partial_output_result["ActualVtkOutputGate"])
        if "actual_vtk_frame_count_1_below_minimum_40" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])
        if "actual_vtk_frame_count_1_does_not_match_expected_40" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])

        missing_protocol_case = temp / "missing_protocol_case"
        create_case(missing_protocol_case)
        (missing_protocol_case / "validation_protocol_audit.json").unlink()
        missing_protocol_manifest = temp / "missing_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(missing_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(missing_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-missing-protocol",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        missing_protocol = load_json(missing_protocol_manifest)
        if "case_required_file_missing:Validation protocol audit" not in missing_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_protocol["RunnerGate"])

        empty_protocol_case = temp / "empty_protocol_case"
        create_case(empty_protocol_case)
        write(empty_protocol_case / "validation_protocol_audit.json", json.dumps({"items": []}, indent=2))
        empty_protocol_manifest = temp / "empty_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(empty_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(empty_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-empty-protocol",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        empty_protocol = load_json(empty_protocol_manifest)
        if "validation_protocol_audit_missing_or_empty" not in empty_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(empty_protocol["RunnerGate"])
        if "validation_protocol_item_missing:inlet_distribution_consistency" not in empty_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(empty_protocol["RunnerGate"])

    print("native_fluidx3d_runner_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
