#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import struct
import sys
import tempfile
from pathlib import Path


def load_module():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "run_codegen_preflight_canary.py"
    spec = importlib.util.spec_from_file_location("run_codegen_preflight_canary", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_codegen_preflight_canary.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def value_after(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def write_casea_standard_box_stl(path: Path) -> None:
    vertices = [
        (-0.04, -0.04, 0.0),
        (0.04, -0.04, 0.0),
        (0.04, 0.04, 0.0),
        (-0.04, 0.04, 0.0),
        (-0.04, -0.04, 0.16),
        (0.04, -0.04, 0.16),
        (0.04, 0.04, 0.16),
        (-0.04, 0.04, 0.16),
    ]
    triangles = [
        (0, 1, 2), (0, 2, 3),
        (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1),
        (1, 5, 6), (1, 6, 2),
        (2, 6, 7), (2, 7, 3),
        (3, 7, 4), (3, 4, 0),
    ]
    with path.open("wb") as handle:
        handle.write(b"AIJ Case A 1:1:2 box".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            handle.write(struct.pack("<fff", 0.0, 0.0, 0.0))
            for index in tri:
                handle.write(struct.pack("<fff", *vertices[index]))
            handle.write(struct.pack("<H", 0))


def main() -> int:
    module = load_module()
    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "run_codegen_preflight_canary.py",
            "--case-name",
            "stg_full_reynolds_stress_tensor",
            "--case-dir",
            "F:\\generated\\AIJ_CaseA_case",
            "--expected-aij-case",
            "CaseA",
            "--expected-wind-direction",
            "N",
            "--expected-wind-vector",
            "1,0,0",
            "--expected-probe-row-count",
            "186",
            "--expected-probe-z-min",
            "0.01",
            "--expected-probe-z-max",
            "0.28",
            "--z-ref",
            "0.16",
            "--expected-uref",
            "4.491",
            "--length-scale-source",
            "F:\\casea_length_scale_source.json",
            "--length-scale-source-type",
            "precursor",
            "--length-scale-source-note",
            "smoke length-scale note",
            "--length-scale-paper-admissible",
            "--time-steps",
            "60000",
            "--vtk-save-interval",
            "500",
            "--vtk-save-start-step",
            "10000",
            "--expected-vtk-frame-count",
            "100",
            "--average-last-n",
            "80",
            "--min-vtk-frames",
            "60",
            "--min-vtk-step-span",
            "30000",
            "--diagnostic-canary-stg-update-interval",
            "2",
            "--diagnostic-canary-stg-intensity-scale",
            "1.414214",
            "--diagnostic-canary-stg-temporal-step-scale",
            "0.100000",
            "--require-actual-geometry",
            "--quick",
        ]
        args = module.parse_args()
    finally:
        sys.argv = old_argv

    if args.expected_probe_z_min != 0.01:
        raise AssertionError(args.expected_probe_z_min)
    if args.expected_probe_z_max != 0.28:
        raise AssertionError(args.expected_probe_z_max)
    if args.case_dir != "F:\\generated\\AIJ_CaseA_case":
        raise AssertionError(args.case_dir)
    if args.expected_wind_vector != "1,0,0":
        raise AssertionError(args.expected_wind_vector)
    if args.length_scale_source_type != "precursor":
        raise AssertionError(args.length_scale_source_type)
    if args.length_scale_paper_admissible is not True:
        raise AssertionError(args.length_scale_paper_admissible)
    if args.require_actual_geometry is not True:
        raise AssertionError(args.require_actual_geometry)
    if args.time_steps != 60000 or args.average_last_n != 80:
        raise AssertionError(args)
    if args.diagnostic_canary_stg_update_interval != 2:
        raise AssertionError(args.diagnostic_canary_stg_update_interval)
    if args.diagnostic_canary_stg_intensity_scale != 1.414214:
        raise AssertionError(args.diagnostic_canary_stg_intensity_scale)
    if args.diagnostic_canary_stg_temporal_step_scale != 0.1:
        raise AssertionError(args.diagnostic_canary_stg_temporal_step_scale)

    with tempfile.TemporaryDirectory(prefix="citylbm_actual_geometry_gate_smoke_") as raw:
        case_dir = Path(raw)
        (case_dir / "buildings.stl").write_bytes(b"solid smoke\nendsolid smoke\n")
        (case_dir / "case_metadata.json").write_text(
            json.dumps(
                {
                    "SceneName": "casea_smoke",
                    "WindProfileCsvPath": "AF_caseA_full_tensor_smoke.csv",
                    "GeometryBuildingCount": 0,
                    "Nx": 16,
                    "Ny": 16,
                    "Nz": 16,
                }
            ),
            encoding="utf-8",
        )
        gate = module.actual_validation_geometry_gate(case_dir, True)
        if gate["Gate"] != "diagnostic_only":
            raise AssertionError(gate)
        expected_reasons = set(gate["Reasons"])
        if not any(reason.startswith("buildings_stl_too_small_for_actual_validation") for reason in expected_reasons):
            raise AssertionError(gate)
        if "geometry_building_count_not_positive:0" not in expected_reasons:
            raise AssertionError(gate)
        if "metadata_names_indicate_smoke_case" not in expected_reasons:
            raise AssertionError(gate)

        warning_gate = module.actual_validation_geometry_gate(case_dir, False)
        if warning_gate["Gate"] != "pass" or not warning_gate["Warnings"]:
            raise AssertionError(warning_gate)

    with tempfile.TemporaryDirectory(prefix="citylbm_casea_standard_box_gate_") as raw:
        case_dir = Path(raw)
        write_casea_standard_box_stl(case_dir / "buildings.stl")
        (case_dir / "case_metadata.json").write_text(
            json.dumps(
                {
                    "AijCase": "CaseA",
                    "GeneratedCaseName": "AIJ_CaseA_native_strict_building",
                    "Nx": 547,
                    "Ny": 280,
                    "Nz": 160,
                }
            ),
            encoding="utf-8",
        )
        casea_gate = module.actual_validation_geometry_gate(case_dir, True, "CaseA")
        if casea_gate["Gate"] != "pass":
            raise AssertionError(casea_gate)
        if casea_gate["CaseAStandardBoxGeometry"] is not True:
            raise AssertionError(casea_gate)
        if "legacy_metadata_missing_geometry_building_count_but_casea_standard_box_stl_verified" not in casea_gate["Warnings"]:
            raise AssertionError(casea_gate)

    with tempfile.TemporaryDirectory(prefix="citylbm_codegen_canary_smoke_") as raw:
        root = Path(raw)
        temp_citylbm = root / "CityLBM"
        case_dir = temp_citylbm / "stg_full_reynolds_stress_tensor"
        external_case_dir = root / "external_case"
        source = temp_citylbm / "fake_fluidx3d_source_full_reynolds_tensor"
        out_dir = root / "out"
        af_csv = root / "AF_caseA.csv"
        case_dir.mkdir(parents=True)
        external_case_dir.mkdir(parents=True)
        source.mkdir(parents=True)
        af_csv.write_text("z(m),U(m/s),k(m2/s2)\n0.01,2.9,0.4\n0.16,4.491,0.652\n", encoding="utf-8")
        captured: list[tuple[str, list[str]]] = []

        def fake_gettempdir() -> str:
            return str(root)

        def fake_run_step(name, cmd, cwd, extra_env=None):
            command = list(cmd)
            captured.append((name, command))
            if name == "audit_custom_profile_against_af":
                audit_path = Path(value_after(command, "--out-json"))
                audit_path.parent.mkdir(parents=True, exist_ok=True)
                audit_path.write_text(
                    json.dumps({"Gate": "pass", "Reasons": ["custom_profile_matches_official_af_within_thresholds"]}),
                    encoding="utf-8",
                )
            if name == "check_short_canary_route":
                route_path = Path(value_after(command, "--out"))
                route_path.parent.mkdir(parents=True, exist_ok=True)
                route_path.write_text(json.dumps({"Gate": "pass"}), encoding="utf-8")
            if name == "run_native_preflight_pack":
                manifest_path = Path(value_after(command, "--out-dir")) / "native_preflight_pack_manifest.json"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    json.dumps({"Gate": "pass", "Reasons": [], "DiagnosticCanaryGate": {"Gate": "pass"}}),
                    encoding="utf-8",
                )
            return {"Name": name, "Command": command, "ReturnCode": 0, "Stdout": "", "Stderr": ""}

        old_argv = sys.argv[:]
        old_run_step = module.run_step
        old_gettempdir = module.tempfile.gettempdir
        try:
            module.run_step = fake_run_step
            module.tempfile.gettempdir = fake_gettempdir
            sys.argv = [
                "run_codegen_preflight_canary.py",
                "--case-name",
                "stg_full_reynolds_stress_tensor",
                "--out-dir",
                str(out_dir),
                "--case-dir",
                str(external_case_dir),
                "--af-csv",
                str(af_csv),
                "--time-steps",
                "500",
                "--vtk-save-interval",
                "25",
                "--vtk-save-start-step",
                "25",
                "--expected-vtk-frame-count",
                "20",
                "--average-last-n",
                "8",
                "--min-vtk-frames",
                "8",
                "--min-vtk-step-span",
                "175",
                "--diagnostic-canary-stg-update-interval",
                "2",
                "--diagnostic-canary-stg-intensity-scale",
                "1.414214",
                "--diagnostic-canary-stg-temporal-step-scale",
                "0.100000",
                "--quick",
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            module.tempfile.gettempdir = old_gettempdir
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        manifest = json.loads((out_dir / "codegen_preflight_canary_manifest.json").read_text(encoding="utf-8-sig"))
        if manifest["CaseDir"] != str(external_case_dir.resolve()) or manifest["ExternalCaseDir"] is not True:
            raise AssertionError(manifest)
        if manifest["SkippedBuild"] is not True or manifest["SkippedCodegen"] is not True:
            raise AssertionError(manifest)
        if manifest["CustomProfileAfFidelityGate"] != "pass":
            raise AssertionError(manifest)
        audit_cmd = next(command for name, command in captured if name == "audit_custom_profile_against_af")
        if value_after(audit_cmd, "--af-csv") != str(af_csv.resolve()):
            raise AssertionError(audit_cmd)
        preflight_cmd = next(command for name, command in captured if name == "run_native_preflight_pack")
        if value_after(preflight_cmd, "--diagnostic-canary-time-steps") != "500":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-vtk-save-interval") != "25":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-spinup-steps") != "25":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-average-last-n") != "8":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-min-vtk-frames") != "8":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-min-step-span") != "175":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-stg-update-interval") != "2":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-stg-intensity-scale") != "1.414214":
            raise AssertionError(preflight_cmd)
        if value_after(preflight_cmd, "--diagnostic-canary-stg-temporal-step-scale") != "0.1":
            raise AssertionError(preflight_cmd)

    print("codegen_preflight_canary_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
