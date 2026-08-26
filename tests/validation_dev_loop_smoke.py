#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def load_module():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "run_validation_dev_loop.py"
    spec = importlib.util.spec_from_file_location("run_validation_dev_loop", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_validation_dev_loop.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def value_after(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def main() -> int:
    module = load_module()
    repo = Path(__file__).resolve().parents[1]
    repo_default, repo_meta = module.default_out_dir(repo, "casea", "STAMP", min_free_bytes=0)
    if repo_default != repo / "validation_runs" / "casea_dev_loop_STAMP":
        raise AssertionError((repo_default, repo_meta))
    temp_default, temp_meta = module.default_out_dir(repo, "casea", "STAMP", min_free_bytes=10**20)
    if "CityLBM_validation_runs" not in str(temp_default) or temp_meta["Mode"] != "temp_due_to_low_repo_disk_free":
        raise AssertionError((temp_default, temp_meta))

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "run_validation_dev_loop.py",
            "--case",
            "casea",
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--startup-canary",
        ]
        startup_args = module.parse_args()
    finally:
        sys.argv = old_argv
    if startup_args.runtime_default_mode != "startup_canary":
        raise AssertionError(startup_args.runtime_default_mode)
    if (
        startup_args.time_steps,
        startup_args.vtk_save_interval,
        startup_args.expected_vtk_frame_count,
        startup_args.average_last_n,
        startup_args.min_vtk_frames,
        startup_args.min_vtk_step_span,
    ) != (100, 100, 1, 1, 1, 0):
        raise AssertionError(startup_args)

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "run_validation_dev_loop.py",
            "--case",
            "casea",
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--correlation-canary",
        ]
        correlation_args = module.parse_args()
    finally:
        sys.argv = old_argv
    if correlation_args.runtime_default_mode != "correlation_canary":
        raise AssertionError(correlation_args.runtime_default_mode)
    if (
        correlation_args.time_steps,
        correlation_args.vtk_save_interval,
        correlation_args.expected_vtk_frame_count,
        correlation_args.average_last_n,
        correlation_args.min_vtk_frames,
        correlation_args.min_vtk_step_span,
        correlation_args.diagnostic_canary_stg_update_interval,
    ) != (500, 100, 5, 5, 5, 400, 5):
        raise AssertionError(correlation_args)
    if correlation_args.diagnostic_canary_stg_intensity_scale is not None:
        raise AssertionError(correlation_args.diagnostic_canary_stg_intensity_scale)

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "run_validation_dev_loop.py",
            "--case",
            "casea",
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--correlation-canary",
            "--diagnostic-canary-stg-intensity-scale",
            "1.414214",
            "--diagnostic-canary-stg-temporal-step-scale",
            "0.100000",
        ]
        correlation_scale_args = module.parse_args()
    finally:
        sys.argv = old_argv
    if correlation_scale_args.diagnostic_canary_stg_intensity_scale != 1.414214:
        raise AssertionError(correlation_scale_args.diagnostic_canary_stg_intensity_scale)
    if correlation_scale_args.diagnostic_canary_stg_temporal_step_scale != 0.1:
        raise AssertionError(correlation_scale_args.diagnostic_canary_stg_temporal_step_scale)

    old_argv = sys.argv[:]
    try:
        sys.argv = [
            "run_validation_dev_loop.py",
            "--case",
            "casea",
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--startup-canary",
            "--correlation-canary",
        ]
        try:
            module.parse_args()
        except SystemExit as exc:
            if exc.code == 0:
                raise AssertionError("mutually exclusive runtime modes should fail")
        else:
            raise AssertionError("mutually exclusive runtime modes should fail")
    finally:
        sys.argv = old_argv

    with tempfile.TemporaryDirectory(prefix="citylbm_dev_loop_smoke_") as raw:
        root = Path(raw)
        out_dir = root / "out"
        case_dir = root / "case"
        source = root / "FluidX3D"
        case_dir.mkdir()
        source.mkdir()
        length_source = root / "casea_length_scale_source.json"
        length_source.write_text('{"gate":"pass"}\n', encoding="utf-8")
        captured: list[tuple[str, list[str]]] = []

        def fake_run_step(name, cmd, cwd):
            command = list(cmd)
            captured.append((name, command))
            if name == "codegen_preflight_canary":
                manifest_path = Path(value_after(command, "--manifest-out"))
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    json.dumps(
                        {
                            "CaseName": "stg_full_reynolds_stress_tensor",
                            "CaseDir": str(root / "case"),
                            "FluidX3DSource": str(source),
                            "OutDir": str(out_dir),
                            "ExpectedAijCase": value_after(command, "--expected-aij-case"),
                            "ExpectedWindDirection": value_after(command, "--expected-wind-direction"),
                            "ExpectedWindVector": value_after(command, "--expected-wind-vector"),
                            "DiagnosticCanaryGate": {"Gate": "pass", "Reasons": []},
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            return {"Name": name, "Command": command, "ReturnCode": 0, "Stdout": "", "Stderr": ""}

        old_argv = sys.argv[:]
        old_run_step = module.run_step
        try:
            module.run_step = fake_run_step
            sys.argv = [
                "run_validation_dev_loop.py",
                "--case",
                "casea",
                "--fluidx3d-source",
                str(source),
                "--out-dir",
                str(out_dir),
                "--case-dir",
                str(case_dir),
                "--length-scale-source",
                str(length_source),
                "--length-scale-source-type",
                "precursor",
                "--length-scale-source-note",
                "smoke length-scale source",
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
                "--diagnostic-canary-stg-intensity-scale",
                "1.414214",
                "--diagnostic-canary-stg-temporal-step-scale",
                "0.100000",
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        names = [name for name, _ in captured]
        if names != ["codegen_preflight_canary", "native_short_canary_plan_or_execute"]:
            raise AssertionError(names)
        codegen_cmd = captured[0][1]
        if value_after(codegen_cmd, "--expected-wind-vector") != "1,0,0":
            raise AssertionError(codegen_cmd)
        if "--official" not in codegen_cmd or not value_after(codegen_cmd, "--official").endswith("RS-caseA.csv"):
            raise AssertionError(codegen_cmd)
        if "--af-csv" not in codegen_cmd or not value_after(codegen_cmd, "--af-csv").endswith("AF_caseA.csv"):
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--expected-probe-row-count") != "186":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--expected-uref") != "4.491":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--length-scale-source") != str(length_source):
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--length-scale-source-type") != "precursor":
            raise AssertionError(codegen_cmd)
        if "--length-scale-paper-admissible" not in codegen_cmd:
            raise AssertionError(codegen_cmd)
        if "--require-actual-geometry" not in codegen_cmd:
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--case-dir") != str(case_dir):
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--time-steps") != "60000":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--vtk-save-interval") != "500":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--vtk-save-start-step") != "10000":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--average-last-n") != "80":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--diagnostic-canary-stg-intensity-scale") != "1.414214":
            raise AssertionError(codegen_cmd)
        if value_after(codegen_cmd, "--diagnostic-canary-stg-temporal-step-scale") != "0.1":
            raise AssertionError(codegen_cmd)
        loop = json.loads((out_dir / "validation_dev_loop_manifest.json").read_text(encoding="utf-8-sig"))
        if loop["Gate"] != "pass" or loop["DiagnosticCanaryReady"] is not True:
            raise AssertionError(loop)
        if loop["StrictOfficialInputs"] is not True:
            raise AssertionError(loop)
        if loop["RequireActualGeometry"] is not True:
            raise AssertionError(loop)
        if loop["OfficialInputResolution"]["OfficialSource"] != "auto_candidate":
            raise AssertionError(loop)
        if loop["OfficialInputResolution"]["AfCsvSource"] != "auto_candidate":
            raise AssertionError(loop)
        if loop["OutputPlacement"]["Mode"] != "explicit_out_dir":
            raise AssertionError(loop["OutputPlacement"])
        if loop["LengthScaleEvidencePlan"]["SourceType"] != "precursor":
            raise AssertionError(loop["LengthScaleEvidencePlan"])
        if loop["TimeAveragingPlan"]["TimeSteps"] != 60000:
            raise AssertionError(loop["TimeAveragingPlan"])
        if loop["DiagnosticCanaryPlan"]["SyntheticTurbulenceIntensityScale"] != 1.414214:
            raise AssertionError(loop["DiagnosticCanaryPlan"])
        if loop["DiagnosticCanaryPlan"]["SyntheticTurbulenceTemporalStepScale"] != 0.1:
            raise AssertionError(loop["DiagnosticCanaryPlan"])
        if loop["NextOptimizationTarget"]["Key"] != "preflight_next_target_missing":
            raise AssertionError(loop["NextOptimizationTarget"])

        post_target = module.build_loop_next_optimization_target(
            {
                "NextOptimizationTarget": {
                    "Key": "turbulent_inlet_method_and_u_k_preservation",
                    "Diagnosis": "inlet evidence first",
                    "NextAction": "fix inlet",
                    "RequiredExperiment": "native_empty_tunnel_inlet_preservation_first",
                }
            },
            [
                {"Name": "audit_runtime_inlet_diagnostics_after_canary", "Gate": "pass"},
                {"Name": "audit_inlet_correlation_after_canary", "Gate": "pass"},
            ],
        )
        if post_target["Key"] != "turbulent_inlet_method_and_u_k_preservation":
            raise AssertionError(post_target)
        if post_target["ShortRuntimeCanaryEvidenceGate"]["Gate"] != "pass":
            raise AssertionError(post_target)
        if post_target["RequiredExperiment"] != "paper_length_empty_tunnel_inlet_preservation_with_bound_inlet_evidence":
            raise AssertionError(post_target)

        geometry_target = module.build_loop_next_optimization_target(
            {
                "NextOptimizationTarget": {
                    "Key": "turbulent_inlet_method_and_u_k_preservation",
                    "Diagnosis": "inlet evidence first",
                    "NextAction": "fix inlet",
                }
            },
            [],
            {
                "ActualValidationGeometryGate": {
                    "Gate": "diagnostic_only",
                    "Required": True,
                    "Reasons": ["geometry_building_count_not_positive:0"],
                }
            },
        )
        if geometry_target["Key"] != "actual_validation_geometry_missing":
            raise AssertionError(geometry_target)
        if geometry_target["ShortDiagnosticCanaryAllowed"] is not False:
            raise AssertionError(geometry_target)

        route_target = module.build_loop_next_optimization_target(
            {},
            [],
            {
                "ShortCanaryRouteCheckGate": "fail",
                "ActualValidationGeometryGate": {
                    "Gate": "pass",
                    "Required": True,
                    "CaseAStandardBoxGeometry": True,
                },
                "Reasons": [
                    "short_canary_route_check:runtime_inlet_diagnostics_source_gate_not_pass:fail",
                    "short_canary_route_check:setup_codegen_route_not_current_citylbm:legacy_runtime_diagnostic_patch_route",
                ],
            },
        )
        if route_target["Key"] != "current_codegen_route_required":
            raise AssertionError(route_target)
        if route_target["ShortDiagnosticCanaryAllowed"] is not False:
            raise AssertionError(route_target)

        captured.clear()
        fast_out_dir = root / "fast_out"
        try:
            module.run_step = fake_run_step
            sys.argv = [
                "run_validation_dev_loop.py",
                "--case",
                "casee",
                "--fluidx3d-source",
                str(source),
                "--out-dir",
                str(fast_out_dir),
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        fast_codegen_cmd = captured[0][1]
        if value_after(fast_codegen_cmd, "--time-steps") != "2000":
            raise AssertionError(fast_codegen_cmd)
        if value_after(fast_codegen_cmd, "--vtk-save-interval") != "100":
            raise AssertionError(fast_codegen_cmd)
        if value_after(fast_codegen_cmd, "--vtk-save-start-step") != "100":
            raise AssertionError(fast_codegen_cmd)
        if value_after(fast_codegen_cmd, "--average-last-n") != "10":
            raise AssertionError(fast_codegen_cmd)
        fast_loop = json.loads((fast_out_dir / "validation_dev_loop_manifest.json").read_text(encoding="utf-8-sig"))
        if fast_loop["RuntimeDefaultMode"] != "development_canary":
            raise AssertionError(fast_loop)
        if fast_loop["TimeAveragingPlan"]["MinimumStepSpan"] != 900:
            raise AssertionError(fast_loop["TimeAveragingPlan"])

        captured.clear()
        paper_out_dir = root / "paper_out"
        try:
            module.run_step = fake_run_step
            sys.argv = [
                "run_validation_dev_loop.py",
                "--case",
                "casee",
                "--fluidx3d-source",
                str(source),
                "--out-dir",
                str(paper_out_dir),
                "--paper-defaults",
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        paper_codegen_cmd = captured[0][1]
        if value_after(paper_codegen_cmd, "--time-steps") != "40000":
            raise AssertionError(paper_codegen_cmd)
        if value_after(paper_codegen_cmd, "--average-last-n") != "40":
            raise AssertionError(paper_codegen_cmd)
        paper_loop = json.loads((paper_out_dir / "validation_dev_loop_manifest.json").read_text(encoding="utf-8-sig"))
        if paper_loop["RuntimeDefaultMode"] != "paper_candidate":
            raise AssertionError(paper_loop)

        captured.clear()
        correlation_out_dir = root / "correlation_out"
        try:
            module.run_step = fake_run_step
            sys.argv = [
                "run_validation_dev_loop.py",
                "--case",
                "casea",
                "--fluidx3d-source",
                str(source),
                "--out-dir",
                str(correlation_out_dir),
                "--correlation-canary",
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        correlation_codegen_cmd = captured[0][1]
        if value_after(correlation_codegen_cmd, "--time-steps") != "500":
            raise AssertionError(correlation_codegen_cmd)
        if value_after(correlation_codegen_cmd, "--expected-vtk-frame-count") != "5":
            raise AssertionError(correlation_codegen_cmd)
        if value_after(correlation_codegen_cmd, "--average-last-n") != "5":
            raise AssertionError(correlation_codegen_cmd)
        if value_after(correlation_codegen_cmd, "--diagnostic-canary-stg-update-interval") != "5":
            raise AssertionError(correlation_codegen_cmd)
        correlation_loop = json.loads((correlation_out_dir / "validation_dev_loop_manifest.json").read_text(encoding="utf-8-sig"))
        if correlation_loop["RuntimeDefaultMode"] != "correlation_canary":
            raise AssertionError(correlation_loop)
        if correlation_loop["TimeAveragingPlan"]["MinimumStepSpan"] != 400:
            raise AssertionError(correlation_loop["TimeAveragingPlan"])
        if correlation_loop["DiagnosticCanaryPlan"]["SyntheticTurbulenceUpdateInterval"] != 5:
            raise AssertionError(correlation_loop["DiagnosticCanaryPlan"])
        if correlation_loop["DiagnosticCanaryPlan"]["ExpectedFinalWindowRefreshCount"] != 80:
            raise AssertionError(correlation_loop["DiagnosticCanaryPlan"])

        post_fail_out_dir = root / "post_fail_out"

        def fake_run_step_with_failed_post_audit(name, cmd, cwd):
            command = list(cmd)
            captured.append((name, command))
            if name == "codegen_preflight_canary":
                manifest_path = Path(value_after(command, "--manifest-out"))
                preflight_pack = manifest_path.parent / "native_preflight_pack_manifest.json"
                runtime_audit = manifest_path.parent / "runtime_inlet_diagnostics_csv_audit.json"
                correlation_audit = manifest_path.parent / "inlet_correlation_audit.json"
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                preflight_pack.write_text(
                    json.dumps(
                        {
                            "DevelopmentTriage": {
                                "SuggestedCommands": [
                                    {
                                        "Name": "audit_runtime_inlet_diagnostics_after_canary",
                                        "Command": [
                                            sys.executable,
                                            "audit_inlet_diagnostics_csv.py",
                                            "--out-json",
                                            str(runtime_audit),
                                        ],
                                    },
                                    {
                                        "Name": "audit_inlet_correlation_after_canary",
                                        "Command": [
                                            sys.executable,
                                            "audit_inlet_correlation_from_vtk.py",
                                            "--out-json",
                                            str(correlation_audit),
                                        ],
                                    },
                                ]
                            }
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                manifest_path.write_text(
                    json.dumps(
                        {
                            "CaseName": "casea_full_reynolds_stress_tensor",
                            "CaseDir": str(root / "case"),
                            "FluidX3DSource": str(source),
                            "OutDir": str(post_fail_out_dir),
                            "NativePreflightPackManifest": str(preflight_pack),
                            "DiagnosticCanaryGate": {"Gate": "pass", "Reasons": []},
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            elif name == "native_short_canary_plan_or_execute":
                manifest_path = Path(value_after(command, "--manifest-out"))
                manifest_path.write_text('{"Gate":"pass","Reasons":[]}\n', encoding="utf-8")
            elif name == "audit_runtime_inlet_diagnostics_after_canary":
                Path(value_after(command, "--out-json")).write_text('{"Gate":"pass","Reasons":[]}\n', encoding="utf-8")
            elif name == "audit_inlet_correlation_after_canary":
                Path(value_after(command, "--out-json")).write_text(
                    '{"inlet_correlation_gate":"fail","inlet_correlation_gate_reasons":["k_variance_ratio_below_0.5"]}\n',
                    encoding="utf-8",
                )
                return {"Name": name, "Command": command, "ReturnCode": 2, "Stdout": "", "Stderr": ""}
            return {"Name": name, "Command": command, "ReturnCode": 0, "Stdout": "", "Stderr": ""}

        captured.clear()
        try:
            module.run_step = fake_run_step_with_failed_post_audit
            sys.argv = [
                "run_validation_dev_loop.py",
                "--case",
                "casea",
                "--fluidx3d-source",
                str(source),
                "--out-dir",
                str(post_fail_out_dir),
                "--correlation-canary",
                "--execute-canary",
                "--allow-diagnostic",
            ]
            code = module.main()
        finally:
            module.run_step = old_run_step
            sys.argv = old_argv

        if code != 0:
            raise AssertionError(code)
        post_fail_loop = json.loads((post_fail_out_dir / "validation_dev_loop_manifest.json").read_text(encoding="utf-8-sig"))
        if post_fail_loop["Gate"] != "diagnostic_only":
            raise AssertionError(post_fail_loop)
        if "post_canary_runtime_evidence_not_pass:fail" not in post_fail_loop["Reasons"]:
            raise AssertionError(post_fail_loop["Reasons"])

    print("validation_dev_loop_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
