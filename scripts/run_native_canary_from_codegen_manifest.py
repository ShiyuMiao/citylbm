#!/usr/bin/env python3
"""Plan or execute a short native FluidX3D canary from a fresh-codegen manifest.

This script is intentionally separated from paper-grade validation. It only
starts a short native run when DiagnosticCanaryGate already passes, and records
that the result is a runtime/VTK-output canary, not an accuracy claim.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence

DEFAULT_AVERAGE_LAST_N = 1
DEFAULT_MIN_VTK_FRAMES = 1
DEFAULT_MIN_VTK_STEP_SPAN = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a short native FluidX3D canary from a codegen preflight manifest.")
    parser.add_argument("--codegen-manifest", required=True, help="codegen_preflight_canary_manifest.json.")
    parser.add_argument("--out-dir", default="", help="Canary output directory. Defaults to <codegen out>/native_canary.")
    parser.add_argument("--manifest-out", default="", help="Canary wrapper manifest path.")
    parser.add_argument("--solver-cwd", default="", help="Working directory for FluidX3D.exe. Defaults to <out-dir>/solver_cwd.")
    parser.add_argument("--exe", default="", help="Optional explicit FluidX3D.exe path.")
    parser.add_argument("--msbuild", default="", help="Optional explicit MSBuild path.")
    parser.add_argument("--configuration", default="Release")
    parser.add_argument("--platform", default="x64")
    parser.add_argument("--time-steps", type=int, default=None, help="Override generated case time steps.")
    parser.add_argument("--vtk-save-interval", type=int, default=None, help="Override generated case VTK save interval.")
    parser.add_argument("--vtk-save-start-step", type=int, default=None, help="Override first VTK output step after spin-up.")
    parser.add_argument("--expected-vtk-frame-count", type=int, default=None, help="Override generated case frame count.")
    parser.add_argument("--average-last-n", type=int, default=DEFAULT_AVERAGE_LAST_N)
    parser.add_argument("--min-vtk-frames", type=int, default=DEFAULT_MIN_VTK_FRAMES)
    parser.add_argument("--min-vtk-step-span", type=int, default=DEFAULT_MIN_VTK_STEP_SPAN)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--max-generated-time-steps-for-short-canary", type=int, default=5000)
    parser.add_argument("--allow-long-generated-case", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Actually install/build/run native FluidX3D.")
    parser.add_argument(
        "--keep-graphics",
        action="store_true",
        help="Do not disable FluidX3D GRAPHICS macros before a short VTK canary run.",
    )
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="With --execute, install case files into FluidX3D source but do not build or run.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_step(name: str, cmd: Sequence[str], cwd: Path) -> Dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "Name": name,
        "Command": list(cmd),
        "ReturnCode": completed.returncode,
        "ElapsedSeconds": round(time.time() - started, 3),
        "Stdout": completed.stdout,
        "Stderr": completed.stderr,
    }


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def gate_value(mapping: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = nested(mapping, *key.split("."))
        if isinstance(value, dict):
            nested_gate = value.get("Gate") or value.get("gate")
            if nested_gate is not None:
                return str(nested_gate).strip().lower()
        if value is not None:
            return str(value).strip().lower()
    return ""


def optional(cmd: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value)
    if text == "":
        return
    cmd.extend([flag, text])


def command_option(cmd: Sequence[str], flag: str) -> str:
    try:
        index = list(cmd).index(flag)
    except ValueError:
        return ""
    if index + 1 >= len(cmd):
        return ""
    return str(cmd[index + 1]).strip()


def set_option(cmd: Sequence[str], flag: str, value: Any) -> List[str]:
    result = list(cmd)
    text = str(value) if value is not None else ""
    try:
        index = result.index(flag)
    except ValueError:
        if text:
            result.extend([flag, text])
        return result
    if index + 1 < len(result):
        result[index + 1] = text
    elif text:
        result.append(text)
    return result


def append_flag_once(cmd: Sequence[str], flag: str) -> List[str]:
    result = list(cmd)
    if flag not in result:
        result.append(flag)
    return result


def remove_flags(cmd: Sequence[str], flags: Sequence[str]) -> List[str]:
    flag_set = set(flags)
    return [item for item in cmd if item not in flag_set]


def suggested_command(preflight_pack: Dict[str, Any], name: str) -> List[str]:
    triage = preflight_pack.get("DevelopmentTriage") if isinstance(preflight_pack.get("DevelopmentTriage"), dict) else {}
    commands = triage.get("SuggestedCommands") if isinstance(triage.get("SuggestedCommands"), list) else []
    for item in commands:
        if not isinstance(item, dict) or item.get("Name") != name:
            continue
        command = item.get("Command")
        if isinstance(command, list) and all(isinstance(part, str) for part in command):
            return list(command)
    return []


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        try:
            as_float = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if not as_float.is_integer():
            return None
        parsed = int(as_float)
    return parsed


def first_int_match(source: str, patterns: Sequence[str]) -> Optional[int]:
    for pattern in patterns:
        match = re.search(pattern, source)
        if match:
            return as_int(match.group(1))
    return None


def computed_frame_count(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int] = None,
) -> Optional[int]:
    if time_steps is None or save_interval is None or time_steps <= 0 or save_interval <= 0:
        return None
    if save_start_step is not None and save_start_step < 0:
        return None
    first_step = save_interval if save_start_step is None or save_start_step <= 0 else save_start_step
    if first_step > time_steps:
        return 0
    count = ((time_steps - first_step) // save_interval) + 1
    if first_step + (count - 1) * save_interval != time_steps:
        count += 1
    return count


def generated_case_schedule(case_dir: Path) -> Dict[str, Any]:
    metadata = read_json(case_dir / "case_metadata.json")
    metadata_time_steps = as_int(metadata.get("TimeSteps") or metadata.get("SimulationTimeSteps"))
    metadata_save_interval = as_int(metadata.get("SaveInterval") or metadata.get("VtkSaveInterval"))
    metadata_save_start_step = as_int(metadata.get("VtkSaveStartStep") or metadata.get("SaveStartStep"))
    vtk_output = metadata.get("VtkOutput") if isinstance(metadata.get("VtkOutput"), dict) else {}
    if metadata_save_start_step is None and isinstance(vtk_output, dict):
        metadata_save_start_step = as_int(vtk_output.get("SaveStartStep") or vtk_output.get("VtkSaveStartStep"))
    metadata_expected_frames = as_int(metadata.get("ExpectedVtkFrameCount"))
    setup_path = next((path for path in [case_dir / "src" / "setup.cpp", case_dir / "setup.cpp"] if path.is_file()), None)
    source = ""
    if setup_path is not None:
        source = setup_path.read_text(encoding="utf-8", errors="replace")
    setup_time_steps = first_int_match(
        source,
        [
            r"\bconst\s+uint\s+total_steps\s*=\s*(\d+)u?\s*;",
            r"\blbm\.get_t\s*\(\s*\)\s*<\s*(\d+)u?\b",
            r"\bremaining\s*=\s*(\d+)u?\s*-",
        ],
    )
    setup_save_interval = first_int_match(
        source,
        [
            r"\bconst\s+uint\s+vtk_save_interval\s*=\s*(\d+)u?\s*;",
            r"\bconst\s+uint\s+citylbm_save_interval\s*=\s*(\d+)u?\s*;",
        ],
    )
    setup_save_start_step = first_int_match(
        source,
        [
            r"\bconst\s+uint\s+citylbm_vtk_save_start_step\s*=\s*(\d+)u?\s*;",
            r"\bconst\s+uint\s+vtk_save_start_step\s*=\s*(\d+)u?\s*;",
        ],
    )
    time_steps = metadata_time_steps or setup_time_steps
    save_interval = metadata_save_interval or setup_save_interval
    save_start_step = metadata_save_start_step if metadata_save_start_step is not None else setup_save_start_step
    expected_frames = metadata_expected_frames or computed_frame_count(time_steps, save_interval, save_start_step)
    return {
        "MetadataPath": str((case_dir / "case_metadata.json").resolve()) if (case_dir / "case_metadata.json").is_file() else "",
        "SetupPath": str(setup_path.resolve()) if setup_path is not None else "",
        "MetadataTimeSteps": metadata_time_steps,
        "MetadataSaveInterval": metadata_save_interval,
        "MetadataVtkSaveStartStep": metadata_save_start_step,
        "MetadataExpectedVtkFrameCount": metadata_expected_frames,
        "SetupTimeSteps": setup_time_steps,
        "SetupSaveInterval": setup_save_interval,
        "SetupVtkSaveStartStep": setup_save_start_step,
        "TimeSteps": time_steps,
        "SaveInterval": save_interval,
        "VtkSaveStartStep": save_start_step,
        "ExpectedVtkFrameCount": expected_frames,
    }


def manifest_text(codegen: Dict[str, Any], key: str, default: str = "") -> str:
    value = codegen.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    codegen_manifest_path = Path(args.codegen_manifest).expanduser().resolve()
    codegen = read_json(codegen_manifest_path)
    codegen_out_dir = Path(str(codegen.get("OutDir") or codegen_manifest_path.parent)).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else codegen_out_dir / "native_canary"
    solver_cwd = Path(args.solver_cwd).expanduser().resolve() if args.solver_cwd else out_dir / "solver_cwd"
    manifest_out = (
        Path(args.manifest_out).expanduser().resolve()
        if args.manifest_out
        else out_dir / "native_canary_manifest.json"
    )
    native_manifest_out = out_dir / "native_fluidx3d_canary_run_manifest.json"
    output_dir = solver_cwd / "output"

    case_dir = Path(str(codegen.get("CaseDir") or "")).expanduser()
    source_root = Path(str(codegen.get("FluidX3DSource") or "")).expanduser()
    expected_aij_case = manifest_text(codegen, "ExpectedAijCase", "CaseA")
    expected_wind_direction = manifest_text(codegen, "ExpectedWindDirection", "N")
    expected_wind_vector = manifest_text(codegen, "ExpectedWindVector", "1,0,0")
    preflight_pack = read_json(Path(str(codegen.get("NativePreflightPackManifest") or "")))
    artifacts = preflight_pack.get("Artifacts") if isinstance(preflight_pack.get("Artifacts"), dict) else {}
    suggested_native_cmd = suggested_command(preflight_pack, "run_native_diagnostic_canary")
    suggested_time_steps: Optional[int] = None
    suggested_save_interval: Optional[int] = None
    suggested_save_start_step: Optional[int] = None
    suggested_expected_frames: Optional[int] = None
    suggested_average_last_n: Optional[int] = None
    suggested_min_vtk_frames: Optional[int] = None
    suggested_min_vtk_step_span: Optional[int] = None
    if args.execute and suggested_native_cmd:
        suggested_case_dir = command_option(suggested_native_cmd, "--case-dir")
        suggested_source_root = command_option(suggested_native_cmd, "--fluidx3d-source")
        suggested_solver_cwd = command_option(suggested_native_cmd, "--solver-cwd")
        suggested_output_dir = command_option(suggested_native_cmd, "--output-dir")
        suggested_time_steps = as_int(command_option(suggested_native_cmd, "--time-steps"))
        suggested_save_interval = as_int(command_option(suggested_native_cmd, "--vtk-save-interval"))
        suggested_save_start_step = as_int(command_option(suggested_native_cmd, "--vtk-save-start-step"))
        suggested_expected_frames = as_int(command_option(suggested_native_cmd, "--expected-vtk-frame-count"))
        suggested_average_last_n = as_int(command_option(suggested_native_cmd, "--average-last-n"))
        suggested_min_vtk_frames = as_int(command_option(suggested_native_cmd, "--min-vtk-frames"))
        suggested_min_vtk_step_span = as_int(command_option(suggested_native_cmd, "--min-vtk-step-span"))
        if suggested_case_dir:
            case_dir = Path(suggested_case_dir).expanduser()
        if suggested_source_root:
            source_root = Path(suggested_source_root).expanduser()
        if suggested_solver_cwd and not args.solver_cwd and not args.out_dir:
            solver_cwd = Path(suggested_solver_cwd).expanduser().resolve()
            output_dir = solver_cwd / "output"
        if suggested_output_dir and not args.solver_cwd and not args.out_dir:
            output_dir = Path(suggested_output_dir).expanduser().resolve()
    validation_protocol = str(artifacts.get("ValidationProtocolAudit") or "")
    inlet_source_audit = str(artifacts.get("InletSourceAudit") or "")

    reasons: List[str] = []
    if not codegen:
        reasons.append("codegen_manifest_missing_or_invalid")
    if gate_value(codegen, "DiagnosticCanaryGate") != "pass":
        reasons.append(f"diagnostic_canary_gate_not_pass:{gate_value(codegen, 'DiagnosticCanaryGate') or 'missing'}")
    if not case_dir.is_dir():
        reasons.append("case_dir_missing")
    if not source_root.is_dir():
        reasons.append("fluidx3d_source_missing")
    if validation_protocol and not Path(validation_protocol).is_file():
        reasons.append("validation_protocol_audit_missing")
    if inlet_source_audit and not Path(inlet_source_audit).is_file():
        reasons.append("inlet_source_audit_missing")

    schedule = generated_case_schedule(case_dir) if case_dir.is_dir() else {}
    generated_time_steps = as_int(schedule.get("TimeSteps"))
    generated_save_interval = as_int(schedule.get("SaveInterval"))
    generated_save_start_step = as_int(schedule.get("VtkSaveStartStep"))
    generated_expected_frames = as_int(schedule.get("ExpectedVtkFrameCount"))
    effective_time_steps = args.time_steps if args.time_steps is not None else suggested_time_steps or generated_time_steps
    effective_save_interval = (
        args.vtk_save_interval if args.vtk_save_interval is not None else suggested_save_interval or generated_save_interval
    )
    effective_save_start_step = (
        args.vtk_save_start_step
        if args.vtk_save_start_step is not None
        else suggested_save_start_step if suggested_save_start_step is not None else generated_save_start_step
    )
    computed_effective_expected_frames = computed_frame_count(
        effective_time_steps,
        effective_save_interval,
        effective_save_start_step,
    )
    effective_expected_frames = (
        args.expected_vtk_frame_count
        if args.expected_vtk_frame_count is not None
        else (
            computed_effective_expected_frames
            if computed_effective_expected_frames is not None
            else suggested_expected_frames if suggested_expected_frames is not None else generated_expected_frames
        )
    )
    effective_average_last_n = (
        suggested_average_last_n
        if args.execute
        and suggested_native_cmd
        and args.average_last_n == DEFAULT_AVERAGE_LAST_N
        and suggested_average_last_n is not None
        else args.average_last_n
    )
    effective_min_vtk_frames = (
        suggested_min_vtk_frames
        if args.execute
        and suggested_native_cmd
        and args.min_vtk_frames == DEFAULT_MIN_VTK_FRAMES
        and suggested_min_vtk_frames is not None
        else args.min_vtk_frames
    )
    effective_min_vtk_step_span = (
        suggested_min_vtk_step_span
        if args.execute
        and suggested_native_cmd
        and args.min_vtk_step_span == DEFAULT_MIN_VTK_STEP_SPAN
        and suggested_min_vtk_step_span is not None
        else args.min_vtk_step_span
    )
    if args.execute:
        if effective_time_steps is None or effective_save_interval is None:
            reasons.append("generated_case_schedule_missing")
        if (
            args.time_steps is not None
            and generated_time_steps is not None
            and args.time_steps != generated_time_steps
        ):
            reasons.append(f"requested_time_steps_{args.time_steps}_does_not_match_generated_case_time_steps_{generated_time_steps}")
        if (
            args.vtk_save_interval is not None
            and generated_save_interval is not None
            and args.vtk_save_interval != generated_save_interval
        ):
            reasons.append(
                f"requested_vtk_save_interval_{args.vtk_save_interval}_does_not_match_generated_case_save_interval_{generated_save_interval}"
            )
        if (
            effective_time_steps is not None
            and effective_time_steps > args.max_generated_time_steps_for_short_canary
            and not args.allow_long_generated_case
        ):
            reasons.append(
                f"generated_case_time_steps_{effective_time_steps}_exceeds_short_canary_limit_{args.max_generated_time_steps_for_short_canary}"
            )

    fallback_native_cmd = [
        sys.executable,
        str(repo / "scripts" / "run_native_fluidx3d_case.py"),
        "--case-dir",
        str(case_dir.resolve()) if case_dir else "",
        "--fluidx3d-source",
        str(source_root.resolve()) if source_root else "",
        "--out",
        str(native_manifest_out),
        "--baseline-id",
        f"short-native-canary-{codegen.get('CaseName') or 'case'}-{utc_now()}",
        "--expected-aij-case",
        expected_aij_case,
        "--expected-wind-direction",
        expected_wind_direction,
        "--expected-wind-vector",
        expected_wind_vector,
        "--time-steps",
        str(effective_time_steps or ""),
        "--vtk-save-interval",
        str(effective_save_interval or ""),
        "--vtk-save-start-step",
        str(effective_save_start_step or ""),
        "--expected-vtk-frame-count",
        str(effective_expected_frames or ""),
        "--average-last-n",
        str(effective_average_last_n),
        "--min-vtk-frames",
        str(effective_min_vtk_frames),
        "--min-vtk-step-span",
        str(effective_min_vtk_step_span),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--solver-cwd",
        str(solver_cwd),
        "--output-dir",
        str(output_dir),
        "--allow-diagnostic-execution",
    ]
    optional(fallback_native_cmd, "--validation-protocol-audit", validation_protocol)
    optional(fallback_native_cmd, "--inlet-source-audit", inlet_source_audit)
    optional(fallback_native_cmd, "--exe", args.exe)
    optional(fallback_native_cmd, "--msbuild", args.msbuild)
    optional(fallback_native_cmd, "--configuration", args.configuration)
    optional(fallback_native_cmd, "--platform", args.platform)
    native_cmd = list(suggested_native_cmd) if args.execute and suggested_native_cmd else fallback_native_cmd
    native_cmd = set_option(native_cmd, "--case-dir", str(case_dir.resolve()) if case_dir else "")
    native_cmd = set_option(native_cmd, "--fluidx3d-source", str(source_root.resolve()) if source_root else "")
    native_cmd = set_option(native_cmd, "--out", str(native_manifest_out))
    native_cmd = set_option(native_cmd, "--time-steps", str(effective_time_steps or ""))
    native_cmd = set_option(native_cmd, "--vtk-save-interval", str(effective_save_interval or ""))
    native_cmd = set_option(native_cmd, "--vtk-save-start-step", str(effective_save_start_step or ""))
    native_cmd = set_option(native_cmd, "--expected-vtk-frame-count", str(effective_expected_frames or ""))
    native_cmd = set_option(native_cmd, "--average-last-n", str(effective_average_last_n))
    native_cmd = set_option(native_cmd, "--min-vtk-frames", str(effective_min_vtk_frames))
    native_cmd = set_option(native_cmd, "--min-vtk-step-span", str(effective_min_vtk_step_span))
    native_cmd = set_option(native_cmd, "--timeout-seconds", str(args.timeout_seconds))
    native_cmd = set_option(native_cmd, "--solver-cwd", str(solver_cwd))
    native_cmd = set_option(native_cmd, "--output-dir", str(output_dir))
    if args.exe:
        native_cmd = set_option(native_cmd, "--exe", args.exe)
    if args.msbuild:
        native_cmd = set_option(native_cmd, "--msbuild", args.msbuild)
    if args.configuration:
        native_cmd = set_option(native_cmd, "--configuration", args.configuration)
    if args.platform:
        native_cmd = set_option(native_cmd, "--platform", args.platform)
    if args.execute:
        native_cmd = append_flag_once(native_cmd, "--install")
        if not args.install_only:
            native_cmd = append_flag_once(native_cmd, "--build")
            native_cmd = append_flag_once(native_cmd, "--run")
            if not args.keep_graphics:
                native_cmd = append_flag_once(native_cmd, "--disable-graphics-for-run")
        else:
            native_cmd = remove_flags(native_cmd, ["--build", "--run", "--disable-graphics-for-run"])

    steps: List[Dict[str, Any]] = []
    if args.execute and not reasons:
        steps.append(run_step("run_native_fluidx3d_short_canary", native_cmd, repo))
    elif args.execute and reasons:
        steps.append(
            {
                "Name": "run_native_fluidx3d_short_canary",
                "Command": native_cmd,
                "ReturnCode": 2,
                "ElapsedSeconds": 0.0,
                "Stdout": "",
                "Stderr": "blocked_by_wrapper_preconditions",
            }
        )

    native_manifest = read_json(native_manifest_out)
    if args.execute and native_manifest:
        run_gate = gate_value(native_manifest, "Run")
        actual_vtk_gate = gate_value(native_manifest, "ActualVtkOutputGate")
        if run_gate != "pass":
            reasons.append(f"native_run_gate_not_pass:{run_gate or 'missing'}")
        if actual_vtk_gate != "pass":
            reasons.append(f"actual_vtk_output_gate_not_pass:{actual_vtk_gate or 'missing'}")
        if steps and steps[-1]["ReturnCode"] != 0 and run_gate == "pass" and actual_vtk_gate == "pass":
            steps[-1]["DiagnosticReturnCodeAccepted"] = True
            steps[-1]["DiagnosticReturnCodeReason"] = (
                "native runner returned nonzero because paper-grade evidence gates are diagnostic-only, "
                "but the short runtime and VTK-output canary passed"
            )
        elif steps and steps[-1]["ReturnCode"] != 0:
            reasons.append(f"native_canary_runner_failed:{steps[-1]['ReturnCode']}")
    elif steps and steps[-1]["ReturnCode"] != 0:
        reasons.append(f"native_canary_runner_failed:{steps[-1]['ReturnCode']}")

    if reasons:
        gate = "fail"
    else:
        gate = "pass" if args.execute else "planned"
    wrapper = {
        "Schema": "citylbm.native_short_canary.wrapper.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "short_runtime_and_vtk_output_canary_only_not_paper_grade_validation",
        "CodegenManifest": str(codegen_manifest_path),
        "NativeRunnerManifest": str(native_manifest_out),
        "CaseDir": str(case_dir.resolve()) if case_dir else "",
        "FluidX3DSource": str(source_root.resolve()) if source_root else "",
        "SolverCwd": str(solver_cwd),
        "OutputDir": str(output_dir),
        "Execute": args.execute,
        "Gate": gate,
        "Reasons": list(dict.fromkeys(reasons)),
        "ReasonsCsv": ";".join(dict.fromkeys(reasons)),
        "PaperUsePolicy": "never_use_short_canary_for_accuracy_or_paper_metrics",
        "GeneratedCaseSchedule": schedule,
        "ShortCanaryRunConditions": {
            "TimeSteps": effective_time_steps,
            "SaveInterval": effective_save_interval,
            "VtkSaveStartStep": effective_save_start_step,
            "ExpectedVtkFrameCount": effective_expected_frames,
            "AverageLastN": effective_average_last_n,
            "MinVtkFrames": effective_min_vtk_frames,
            "MinVtkStepSpan": effective_min_vtk_step_span,
        },
        "Command": native_cmd,
        "Steps": steps,
        "NextAction": (
            "Short native canary completed; inspect NativeRunnerManifest for VTK hashes before any longer run."
            if gate == "pass" and args.execute
            else (
                "Plan is ready. Re-run with --execute to install/build/run the short native canary."
                if gate == "pass" or gate == "planned"
                else "Do not execute; fix wrapper reasons first."
            )
        ),
    }
    write_json(manifest_out, wrapper)
    print(f"native_short_canary_gate={gate}; manifest={manifest_out}")
    if wrapper["Reasons"]:
        print("reasons=" + wrapper["ReasonsCsv"])
    return 0 if gate in {"pass", "planned"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
