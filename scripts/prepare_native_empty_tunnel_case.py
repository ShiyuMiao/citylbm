#!/usr/bin/env python3
"""Prepare an empty-tunnel variant of a native FluidX3D validation case.

The script does not launch FluidX3D. It copies one explicit case directory,
switches the copied setup.cpp to `empty_tunnel = true`, and writes a manifest
with hashes and runnable command templates for the inlet-preservation run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


EMPTY_TUNNEL_PATTERN = re.compile(r"\bconst\s+bool\s+empty_tunnel\s*=\s*(false|true)\s*;")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a native validation case and enable its empty_tunnel switch for inlet-preservation testing."
    )
    parser.add_argument("--case-dir", required=True, help="Source native FluidX3D case directory.")
    parser.add_argument("--out-dir", required=True, help="Destination empty-tunnel case directory. Must not already exist.")
    parser.add_argument("--fluidx3d-source", default="", help="Optional native FluidX3D source root for command templates.")
    parser.add_argument(
        "--solver-cwd",
        default="",
        help="Optional FluidX3D run working directory. Its output/ directory is used for VTK files.",
    )
    parser.add_argument(
        "--manifest-out",
        default="",
        help="Output manifest path. Defaults to <out-dir>/empty_tunnel_manifest.json.",
    )
    parser.add_argument("--baseline-id", default="", help="Stable baseline id for the empty-tunnel experiment.")
    parser.add_argument("--expected-aij-case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--expected-wind-direction", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument("--expected-wind-vector", default="", help="Expected airflow vector, e.g. 1,0,0.")
    parser.add_argument("--official", default="", help="Optional official probe CSV for later validation-chain command.")
    parser.add_argument("--official-condition-filter", default="", help="Optional official RS condition/state filter, e.g. ac.")
    parser.add_argument("--official-wind-filter", default="", help="Optional official RS wind-direction filter, e.g. N.")
    parser.add_argument("--af-csv", default="", help="Optional AF inlet profile CSV with z,U,k columns.")
    parser.add_argument("--expected-probe-row-count", type=int, default=0)
    parser.add_argument("--expected-probe-z", type=float, default=None)
    parser.add_argument("--expected-probe-z-min", type=float, default=None)
    parser.add_argument("--expected-probe-z-max", type=float, default=None)
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--expected-uref", type=float, default=None)
    parser.add_argument("--time-steps", type=int, default=0, help="Planned solver steps. Defaults to metadata/setup.cpp.")
    parser.add_argument("--vtk-save-interval", type=int, default=0, help="VTK save interval. Defaults to metadata/setup.cpp.")
    parser.add_argument("--vtk-save-start-step", type=int, default=0, help="First VTK save step. Defaults to metadata/setup.cpp.")
    parser.add_argument("--expected-vtk-frame-count", type=int, default=0, help="Expected VTK frames. Defaults to computed plan.")
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-vtk-step-span", type=int, default=20000)
    parser.add_argument("--min-vtk-frames", type=int, default=0, help="Minimum VTK frames. Defaults to expected frame count.")
    parser.add_argument(
        "--velocity-scale",
        default="",
        help="VTK velocity multiplier. Defaults to case_metadata VelocityScaleLbmToMps when available.",
    )
    parser.add_argument("--vtk-pattern", default="u-*.vtk")
    parser.add_argument("--require-af-k", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_or_empty(path: Optional[Path]) -> str:
    if path is None or not path.is_file():
        return ""
    return sha256(path)


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


def first_existing(base: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        path = base / name
        if path.is_file():
            return path.resolve()
    return None


def add_optional(cmd: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value)
    if text == "":
        return
    cmd.extend([flag, text])


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        try:
            float_value = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if not float_value.is_integer():
            return None
        parsed = int(float_value)
    return parsed


def as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        try:
            number = float(str(value).strip().rstrip("fFuU"))
        except (TypeError, ValueError):
            return None
    if not math.isfinite(number):
        return None
    return number


def nested_value(data: Dict[str, Any], keys: Sequence[str]) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def setup_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError:
        return ""


def setup_const_number(text: str, name: str) -> Optional[float]:
    match = re.search(
        rf"\bconst\s+(?:uint|int|float|double)\s+{re.escape(name)}\s*=\s*([0-9.+\-Ee]+)f?u?\s*;",
        text,
    )
    return as_float(match.group(1)) if match else None


def setup_float_array(text: str, name: str) -> List[float]:
    match = re.search(rf"\b{re.escape(name)}\s*\[[^\]]*\]\s*=\s*\{{([^}}]+)\}}", text, re.DOTALL)
    if not match:
        return []
    values: List[float] = []
    for raw in match.group(1).split(","):
        parsed = as_float(raw.strip())
        if parsed is not None:
            values.append(parsed)
    return values


def infer_z_ref_m(text: str) -> Optional[float]:
    dx = setup_const_number(text, "citylbm_dx_m")
    u_ref_lbm = setup_const_number(text, "citylbm_u_ref_lbm")
    z_cells = setup_float_array(text, "profile_z_cells")
    u_values = setup_float_array(text, "profile_u_lbm")
    if dx is None or u_ref_lbm is None or not z_cells or len(z_cells) != len(u_values):
        return None
    index = min(range(len(u_values)), key=lambda item: abs(u_values[item] - u_ref_lbm))
    return z_cells[index] * dx


def planned_vtk_frame_count(time_steps: int, save_interval: int, save_start_step: int) -> int:
    if time_steps <= 0 or save_interval <= 0 or save_start_step < 0 or time_steps < save_start_step:
        return 0
    return ((time_steps - save_start_step) // save_interval) + 1


def planned_vtk_steps(time_steps: int, save_interval: int, save_start_step: int) -> List[int]:
    if time_steps <= 0 or save_interval <= 0 or save_start_step < 0 or time_steps < save_start_step:
        return []
    steps = list(range(save_start_step, time_steps + 1, save_interval))
    if not steps or steps[-1] != time_steps:
        steps.append(time_steps)
    return steps


def final_window_step_span(time_steps: int, save_interval: int, save_start_step: int, average_last_n: int) -> int:
    steps = planned_vtk_steps(time_steps, save_interval, save_start_step)
    if len(steps) <= 1:
        return 0
    selected = min(len(steps), max(average_last_n, 1))
    if selected <= 1:
        return 0
    return steps[-1] - steps[-selected]


def required_average_frames_for_step_span(save_interval: int, min_frames: int, min_step_span: int) -> int:
    if save_interval <= 0 or min_step_span <= 0:
        return max(1, min_frames)
    return max(min_frames, int(math.ceil(min_step_span / float(save_interval))) + 1)


def replace_counted(pattern: str, repl: str, text: str) -> Tuple[str, int]:
    return re.subn(pattern, repl, text)


def patch_setup_run_plan(setup: Path, time_steps: int, save_interval: int, save_start_step: int) -> Dict[str, Any]:
    text = setup.read_text(encoding="utf-8-sig")
    original = text
    changes: Dict[str, int] = {}

    def apply(name: str, pattern: str, repl: str) -> None:
        nonlocal text
        text, count = replace_counted(pattern, repl, text)
        changes[name] = count

    if time_steps > 0:
        apply(
            "total_steps_const",
            r"\bconst\s+uint\s+total_steps\s*=\s*\d+u\s*;",
            f"const uint total_steps = {time_steps}u;",
        )
        apply(
            "while_time_steps",
            r"while\(lbm\.get_t\(\)\s*<\s*\d+u\)",
            f"while(lbm.get_t() < {time_steps}u)",
        )
        apply(
            "remaining_time_steps",
            r"uint\s+remaining\s*=\s*\d+u\s*-\s*\(uint\)lbm\.get_t\(\)\s*;",
            f"uint remaining = {time_steps}u - (uint)lbm.get_t();",
        )

    if save_interval > 0:
        apply(
            "vtk_save_interval_const",
            r"\bconst\s+uint\s+vtk_save_interval\s*=\s*\d+u\s*;",
            f"const uint vtk_save_interval = {save_interval}u;",
        )
        apply(
            "steps_to_save_interval",
            r"uint\s+steps_to_run\s*=\s*remaining\s*<\s*\d+u\s*\?\s*remaining\s*:\s*\d+u\s*;",
            f"uint steps_to_run = remaining < {save_interval}u ? remaining : {save_interval}u;",
        )
        apply(
            "save_remainder_interval",
            r"uint\s+save_remainder\s*=\s*\(uint\)lbm\.get_t\(\)\s*%\s*\d+u\s*;",
            f"uint save_remainder = (uint)lbm.get_t() % {save_interval}u;",
        )
        apply(
            "until_next_save_interval",
            r"uint\s+until_next_save\s*=\s*save_remainder\s*==\s*0u\s*\?\s*\d+u\s*:\s*\d+u\s*-\s*save_remainder\s*;",
            f"uint until_next_save = save_remainder == 0u ? {save_interval}u : {save_interval}u - save_remainder;",
        )

    if save_interval > 0 and time_steps > 0:
        save_condition = (
            f"if(((uint)lbm.get_t() >= {save_start_step}u && "
            f"(uint)lbm.get_t() % {save_interval}u == 0u) || "
            f"(uint)lbm.get_t() >= {time_steps}u) {{"
        )
        apply(
            "vtk_save_condition",
            r"if\(\(uint\)lbm\.get_t\(\)\s*%\s*\d+u\s*==\s*0u\s*\|\|\s*\(uint\)lbm\.get_t\(\)\s*>=\s*\d+u\)\s*\{",
            save_condition,
        )

    if save_start_step > 0:
        if re.search(r"\bconst\s+uint\s+vtk_save_start_step\s*=", text):
            apply(
                "vtk_save_start_step_const",
                r"\bconst\s+uint\s+vtk_save_start_step\s*=\s*\d+u\s*;",
                f"const uint vtk_save_start_step = {save_start_step}u;",
            )
        elif "const uint vtk_save_interval" in text:
            text = re.sub(
                r"(\bconst\s+uint\s+vtk_save_interval\s*=\s*\d+u\s*;\s*)",
                rf"\1    const uint vtk_save_start_step = {save_start_step}u;\n",
                text,
                count=1,
            )
            changes["vtk_save_start_step_const_inserted"] = 1

    if text != original:
        setup.write_text(text, encoding="utf-8")
    return {
        "Applied": text != original,
        "RequestedTimeSteps": time_steps,
        "RequestedVtkSaveInterval": save_interval,
        "RequestedVtkSaveStartStep": save_start_step,
        "Changes": changes,
    }


def update_metadata_run_plan(metadata: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if args.time_steps <= 0 or args.vtk_save_interval <= 0:
        return {"Applied": False, "Reason": "time_steps_or_save_interval_unavailable"}

    save_start_step = max(args.vtk_save_start_step, 0)
    expected_frames = planned_vtk_frame_count(args.time_steps, args.vtk_save_interval, save_start_step)
    paper_frames = int(metadata.get("PaperRecommendedAveragingFrames") or args.average_last_n or 40)
    min_step_span = args.min_vtk_step_span if args.min_vtk_step_span > 0 else int(metadata.get("PaperRecommendedAverageStepSpan") or 20000)
    adaptive_frames = required_average_frames_for_step_span(args.vtk_save_interval, paper_frames, min_step_span)
    fixed_span = final_window_step_span(args.time_steps, args.vtk_save_interval, save_start_step, paper_frames)
    adaptive_span = final_window_step_span(args.time_steps, args.vtk_save_interval, save_start_step, adaptive_frames)
    update_interval = as_int(metadata.get("SyntheticTurbulenceUpdateInterval"))
    expected_refreshes = adaptive_span // update_interval if update_interval and update_interval > 0 else 0
    minimum_refreshes = int(metadata.get("SyntheticTurbulenceMinimumRecommendedRefreshes") or 200)

    metadata["TimeSteps"] = args.time_steps
    metadata["SaveInterval"] = args.vtk_save_interval
    metadata["ExpectedVtkFrameCount"] = expected_frames
    metadata["ExpectedPaperAverageStepSpan"] = fixed_span
    metadata["PaperRecommendedAdaptiveAveragingFrames"] = adaptive_frames
    metadata["ExpectedAdaptivePaperAverageStepSpan"] = adaptive_span
    metadata["TimeAveragingRunGate"] = (
        "pass_minimum_frame_count" if expected_frames >= 20 else "smoke_only_too_few_frames_for_validation"
    )
    metadata["TimeAveragingPaperGate"] = (
        "pass_adaptive_paper_recommended_frame_count_and_step_span"
        if expected_frames >= adaptive_frames and adaptive_span >= min_step_span
        else "diagnostic_only_extend_time_steps_or_reduce_save_interval"
    )
    vtk_output = metadata.setdefault("VtkOutput", {})
    if isinstance(vtk_output, dict):
        vtk_output["SaveIntervalSteps"] = args.vtk_save_interval
        vtk_output["SaveStartStep"] = save_start_step
        vtk_output["EstimatedPostSpinupFrameCount"] = expected_frames
    if update_interval and update_interval > 0:
        metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] = expected_refreshes
        metadata["SyntheticTurbulentInletTemporalSamplingGate"] = (
            "pass"
            if expected_refreshes >= minimum_refreshes
            else "diagnostic_only_insufficient_stg_refreshes_in_average_window"
        )
    metadata["RunPlanOverride"] = {
        "AppliedBy": "prepare_native_empty_tunnel_case.py",
        "AppliedAtUtc": utc_now(),
        "TimeSteps": args.time_steps,
        "VtkSaveInterval": args.vtk_save_interval,
        "VtkSaveStartStep": save_start_step,
        "ExpectedVtkFrameCount": expected_frames,
        "AverageLastN": args.average_last_n,
        "ExpectedFinalWindowStepSpan": adaptive_span,
        "SyntheticTurbulenceExpectedFinalWindowRefreshCount": expected_refreshes,
        "Purpose": "keep copied setup.cpp, metadata and native preflight schedule consistent",
    }
    return metadata["RunPlanOverride"]


def fill_inferred_args(args: argparse.Namespace, metadata: Dict[str, Any], setup: Path) -> Dict[str, Any]:
    text = setup_text(setup)
    inferred: Dict[str, Any] = {}
    metadata_time_steps = as_int(metadata.get("TimeSteps"))
    metadata_save_interval = as_int(nested_value(metadata, ["VtkOutput", "SaveIntervalSteps"]))
    metadata_save_start = as_int(nested_value(metadata, ["VtkOutput", "SaveStartStep"]))
    metadata_frame_count = as_int(nested_value(metadata, ["VtkOutput", "EstimatedPostSpinupFrameCount"]))

    if args.time_steps <= 0:
        args.time_steps = metadata_time_steps or int(setup_const_number(text, "total_steps") or 0)
        inferred["TimeSteps"] = args.time_steps
    if args.vtk_save_interval <= 0:
        args.vtk_save_interval = metadata_save_interval or int(setup_const_number(text, "vtk_save_interval") or 0)
        inferred["VtkSaveInterval"] = args.vtk_save_interval
    if args.vtk_save_start_step <= 0:
        args.vtk_save_start_step = metadata_save_start or int(setup_const_number(text, "vtk_save_start_step") or 0)
        inferred["VtkSaveStartStep"] = args.vtk_save_start_step
    if args.expected_vtk_frame_count <= 0:
        computed = planned_vtk_frame_count(args.time_steps, args.vtk_save_interval, args.vtk_save_start_step)
        args.expected_vtk_frame_count = computed or metadata_frame_count or 0
        inferred["ExpectedVtkFrameCount"] = args.expected_vtk_frame_count
    if args.min_vtk_frames <= 0:
        args.min_vtk_frames = min(args.expected_vtk_frame_count or 40, max(args.average_last_n, 1))
        inferred["MinVtkFrames"] = args.min_vtk_frames
    if args.expected_uref is None:
        args.expected_uref = setup_const_number(text, "citylbm_u_ref_si")
        inferred["ExpectedUref"] = args.expected_uref
    if args.z_ref is None:
        args.z_ref = infer_z_ref_m(text)
        inferred["ZRef"] = args.z_ref
    return {key: value for key, value in inferred.items() if value not in (None, "", 0)}


def validate_probe_z_args(args: argparse.Namespace) -> None:
    has_exact = args.expected_probe_z is not None
    has_range = args.expected_probe_z_min is not None or args.expected_probe_z_max is not None
    if has_exact and has_range:
        raise SystemExit("--expected-probe-z cannot be combined with --expected-probe-z-min/max")
    if has_range and (args.expected_probe_z_min is None or args.expected_probe_z_max is None):
        raise SystemExit("--expected-probe-z-min and --expected-probe-z-max must be supplied together")
    if (
        args.expected_probe_z_min is not None
        and args.expected_probe_z_max is not None
        and args.expected_probe_z_min > args.expected_probe_z_max
    ):
        raise SystemExit("--expected-probe-z-min cannot be greater than --expected-probe-z-max")


def resolve_velocity_scale(args: argparse.Namespace, metadata: Dict[str, Any]) -> str:
    explicit = str(args.velocity_scale).strip()
    if explicit:
        return explicit
    for key in ["VelocityScaleLbmToMps", "VelocityScale"]:
        value = as_float(metadata.get(key))
        if value is not None and value > 0:
            return f"{value:.12g}"
    return "1.0"


def patch_empty_tunnel_flag(setup: Path) -> str:
    text = setup.read_text(encoding="utf-8-sig")
    matches = list(EMPTY_TUNNEL_PATTERN.finditer(text))
    if not matches:
        return inject_empty_tunnel_flag_for_legacy_setup(setup, text)
    if len(matches) > 1:
        raise SystemExit(f"multiple empty_tunnel flags found in setup.cpp: {setup}")
    match = matches[0]
    current = match.group(1)
    if current == "true":
        return "already_true"
    patched = text[: match.start()] + "const bool empty_tunnel = true;" + text[match.end() :]
    setup.write_text(patched, encoding="utf-8")
    return "changed_false_to_true"


def inject_empty_tunnel_flag_for_legacy_setup(setup: Path, text: str) -> str:
    lines = text.splitlines(keepends=True)
    voxel_lines = [idx for idx, line in enumerate(lines) if "lbm.voxelize_stl(" in line]
    if len(voxel_lines) != 1:
        raise SystemExit(f"empty_tunnel flag not found and unique lbm.voxelize_stl call not found in setup.cpp: {setup}")

    voxel_idx = voxel_lines[0]
    offset_idx = None
    for idx in range(voxel_idx - 1, max(-1, voxel_idx - 12), -1):
        if "float3 stl_offset" in lines[idx]:
            offset_idx = idx
            break
    if offset_idx is None:
        raise SystemExit(f"empty_tunnel flag not found and stl_offset line not found before voxelize_stl in setup.cpp: {setup}")

    indent_match = re.match(r"^(\s*)", lines[voxel_idx])
    indent = indent_match.group(1) if indent_match else ""
    voxel_call = lines[voxel_idx].strip()
    newline = "\r\n" if lines[voxel_idx].endswith("\r\n") else "\n"

    lines.insert(offset_idx, f"{indent}const bool empty_tunnel = true;  // Injected by CityLBM empty-tunnel validation pack.{newline}")
    voxel_idx += 1
    lines[voxel_idx] = (
        f"{indent}if(!empty_tunnel) {{{newline}"
        f"{indent}    {voxel_call}{newline}"
        f"{indent}}}{newline}"
    )
    setup.write_text("".join(lines), encoding="utf-8")
    return "injected_true_and_guarded_voxelize_stl"


def command_text(cmd: List[str]) -> str:
    return " ".join(f'"{part}"' if (" " in part or "\t" in part) else part for part in cmd)


def build_commands(args: argparse.Namespace, repo: Path, out_dir: Path, manifest_out: Path) -> Dict[str, Any]:
    py = sys.executable
    scripts = repo / "scripts"
    native_manifest = out_dir / "native_fluidx3d_baseline_manifest.json"
    preflight_dir = out_dir / "preflight"
    fluidx3d_source = Path(args.fluidx3d_source).expanduser().resolve() if args.fluidx3d_source else None
    solver_cwd = Path(args.solver_cwd).expanduser().resolve() if args.solver_cwd else None
    vtk_dir = (solver_cwd / "output") if solver_cwd else ((fluidx3d_source / "output") if fluidx3d_source else (out_dir / "output"))
    inlet_profile_json = out_dir / "inlet_profile_from_vtk.json"
    inlet_profile_csv = out_dir / "inlet_profile_from_vtk.csv"
    inlet_correlation_json = out_dir / "inlet_correlation_from_vtk.json"
    case_slug = (args.expected_aij_case or out_dir.name).lower().replace(" ", "")
    inlet_diagnostics_dir = solver_cwd or fluidx3d_source or out_dir
    inlet_diagnostics_csv = inlet_diagnostics_dir / f"{case_slug}_inlet_turbulence_stats.csv"
    inlet_diagnostics_json = out_dir / "inlet_diagnostics_csv_audit.json"
    inlet_diagnostics_summary_csv = out_dir / "inlet_diagnostics_csv_summary.csv"

    runner_cmd = [
        py,
        str(scripts / "run_native_fluidx3d_case.py"),
        "--case-dir",
        str(out_dir),
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()) if args.fluidx3d_source else "<FluidX3D_source_root>",
        "--out",
        str(native_manifest),
        "--baseline-id",
        args.baseline_id or f"native-empty-tunnel-{out_dir.name}",
        "--time-steps",
        str(args.time_steps),
        "--vtk-save-interval",
        str(args.vtk_save_interval),
        "--expected-vtk-frame-count",
        str(args.expected_vtk_frame_count),
        "--average-last-n",
        str(args.average_last_n),
        "--min-vtk-frames",
        str(args.min_vtk_frames),
        "--min-vtk-step-span",
        str(args.min_vtk_step_span),
    ]
    add_optional(runner_cmd, "--expected-aij-case", args.expected_aij_case)
    add_optional(runner_cmd, "--expected-wind-direction", args.expected_wind_direction)
    add_optional(runner_cmd, "--expected-wind-vector", args.expected_wind_vector)
    add_optional(runner_cmd, "--official", args.official)
    add_optional(runner_cmd, "--official-condition-filter", args.official_condition_filter)
    add_optional(runner_cmd, "--official-wind-filter", args.official_wind_filter)
    add_optional(runner_cmd, "--af-csv", args.af_csv)
    add_optional(runner_cmd, "--expected-probe-row-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
    add_optional(runner_cmd, "--expected-probe-z", args.expected_probe_z)
    add_optional(runner_cmd, "--expected-probe-z-min", args.expected_probe_z_min)
    add_optional(runner_cmd, "--expected-probe-z-max", args.expected_probe_z_max)
    add_optional(runner_cmd, "--z-ref", args.z_ref)
    add_optional(runner_cmd, "--expected-uref", args.expected_uref)
    add_optional(runner_cmd, "--vtk-save-start-step", args.vtk_save_start_step if args.vtk_save_start_step else None)
    add_optional(runner_cmd, "--solver-cwd", str(solver_cwd) if solver_cwd else "")
    if args.require_af_k:
        runner_cmd.append("--require-af-k")

    run_cmd = list(runner_cmd) + [
        "--install",
        "--build",
        "--run",
        "--disable-graphics-for-run",
        "--allow-diagnostic-execution",
        "--output-dir",
        str(vtk_dir),
    ]

    preflight_cmd = [
        py,
        str(scripts / "run_native_preflight_pack.py"),
        "--case-dir",
        str(out_dir),
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()) if args.fluidx3d_source else "<FluidX3D_source_root>",
        "--out-dir",
        str(preflight_dir),
        "--manifest-out",
        str(native_manifest),
        "--time-steps",
        str(args.time_steps),
        "--vtk-save-interval",
        str(args.vtk_save_interval),
        "--expected-vtk-frame-count",
        str(args.expected_vtk_frame_count),
        "--average-last-n",
        str(args.average_last_n),
        "--min-vtk-step-span",
        str(args.min_vtk_step_span),
        "--allow-diagnostic",
    ]
    add_optional(preflight_cmd, "--expected-aij-case", args.expected_aij_case)
    add_optional(preflight_cmd, "--expected-wind-direction", args.expected_wind_direction)
    add_optional(preflight_cmd, "--expected-wind-vector", args.expected_wind_vector)
    add_optional(preflight_cmd, "--official", args.official)
    add_optional(preflight_cmd, "--official-condition-filter", args.official_condition_filter)
    add_optional(preflight_cmd, "--official-wind-filter", args.official_wind_filter)
    add_optional(preflight_cmd, "--af-csv", args.af_csv)
    add_optional(preflight_cmd, "--expected-probe-row-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
    add_optional(preflight_cmd, "--expected-probe-z", args.expected_probe_z)
    add_optional(preflight_cmd, "--expected-probe-z-min", args.expected_probe_z_min)
    add_optional(preflight_cmd, "--expected-probe-z-max", args.expected_probe_z_max)
    add_optional(preflight_cmd, "--z-ref", args.z_ref)
    add_optional(preflight_cmd, "--expected-uref", args.expected_uref)
    add_optional(preflight_cmd, "--vtk-save-start-step", args.vtk_save_start_step if args.vtk_save_start_step else None)
    if args.require_af_k:
        preflight_cmd.append("--require-af-k")

    inlet_diagnostics_cmd = [
        py,
        str(scripts / "audit_inlet_diagnostics_csv.py"),
        str(inlet_diagnostics_csv),
        "--out-json",
        str(inlet_diagnostics_json),
        "--out-csv",
        str(inlet_diagnostics_summary_csv),
        "--require-rms",
    ]
    if args.require_af_k:
        inlet_diagnostics_cmd.append("--require-k")

    profile_cmd = [
        py,
        str(scripts / "audit_inlet_profile_from_vtk.py"),
        str(vtk_dir),
        "--af-csv",
        args.af_csv or "<AF_profile_csv>",
        "--out-json",
        str(inlet_profile_json),
        "--out-csv",
        str(inlet_profile_csv),
        "--metadata",
        str(out_dir / "case_metadata.json"),
        "--pattern",
        args.vtk_pattern,
        "--average-last-n",
        str(args.average_last_n),
        "--min-frames",
        str(args.min_vtk_frames),
        "--min-step-span",
        str(args.min_vtk_step_span),
        "--wind-direction",
        args.expected_wind_vector or "1,0,0",
        "--plane-axis",
        "auto-inlet",
        "--velocity-scale",
        str(args.velocity_scale),
    ]

    correlation_cmd = [
        py,
        str(scripts / "audit_inlet_correlation_from_vtk.py"),
        str(vtk_dir),
        "--out-json",
        str(inlet_correlation_json),
        "--metadata",
        str(out_dir / "case_metadata.json"),
        "--pattern",
        args.vtk_pattern,
        "--average-last-n",
        str(args.average_last_n),
        "--min-frames",
        str(args.min_vtk_frames),
        "--min-step-span",
        str(args.min_vtk_step_span),
        "--wind-direction",
        args.expected_wind_vector or "1,0,0",
        "--plane-axis",
        "auto-inlet",
        "--velocity-scale",
        str(args.velocity_scale),
    ]
    if args.af_csv:
        correlation_cmd.extend(["--af-csv", args.af_csv])
    if args.require_af_k:
        correlation_cmd.append("--require-k-variance-check")

    validation_chain_cmd = [
        py,
        str(scripts / "run_native_validation_chain.py"),
        str(out_dir),
        "--native-manifest",
        str(native_manifest),
        "--metadata",
        str(out_dir / "case_metadata.json"),
        "--pattern",
        args.vtk_pattern,
        "--average-last-n",
        str(args.average_last_n),
        "--min-avg-frames",
        str(args.min_vtk_frames),
        "--min-avg-step-span",
        str(args.min_vtk_step_span),
        "--wind-vector",
        args.expected_wind_vector or "1,0,0",
        "--velocity-scale",
        str(args.velocity_scale),
    ]
    add_optional(validation_chain_cmd, "--case", args.expected_aij_case)
    add_optional(validation_chain_cmd, "--wind-direction-label", args.expected_wind_direction)
    add_optional(validation_chain_cmd, "--official", args.official)
    add_optional(validation_chain_cmd, "--official-condition-filter", args.official_condition_filter)
    add_optional(validation_chain_cmd, "--official-wind-filter", args.official_wind_filter)
    add_optional(validation_chain_cmd, "--af-csv", args.af_csv)
    add_optional(validation_chain_cmd, "--u-ref", args.expected_uref)
    add_optional(validation_chain_cmd, "--z-ref", args.z_ref)
    add_optional(validation_chain_cmd, "--vtk-save-start-step", args.vtk_save_start_step if args.vtk_save_start_step else None)

    return {
        "PreflightNoCfd": {"Argv": preflight_cmd, "Command": command_text(preflight_cmd)},
        "InstallBuildRunFluidX3D": {"Argv": run_cmd, "Command": command_text(run_cmd)},
        "RunnerPreflightOnly": {"Argv": runner_cmd, "Command": command_text(runner_cmd)},
        "AuditInletDiagnosticsCsvAfterRun": {"Argv": inlet_diagnostics_cmd, "Command": command_text(inlet_diagnostics_cmd)},
        "AuditInletProfileAfterRun": {"Argv": profile_cmd, "Command": command_text(profile_cmd)},
        "AuditInletCorrelationAfterRun": {"Argv": correlation_cmd, "Command": command_text(correlation_cmd)},
        "ValidationChainAfterRun": {"Argv": validation_chain_cmd, "Command": command_text(validation_chain_cmd)},
        "ManifestOut": str(manifest_out),
    }


def main() -> int:
    args = parse_args()
    validate_probe_z_args(args)
    repo = Path(__file__).resolve().parents[1]
    case_dir = Path(args.case_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    manifest_out = Path(args.manifest_out).expanduser().resolve() if args.manifest_out else out_dir / "empty_tunnel_manifest.json"

    if not case_dir.is_dir():
        raise SystemExit(f"case directory not found: {case_dir}")
    if out_dir.exists():
        raise SystemExit(f"destination already exists; choose a new output directory: {out_dir}")
    if manifest_out.exists():
        raise SystemExit(f"manifest already exists; choose a new manifest path: {manifest_out}")

    source_setup = first_existing(case_dir, ["src/setup.cpp", "setup.cpp"])
    if source_setup is None:
        raise SystemExit(f"setup.cpp not found under case directory: {case_dir}")

    source_defines = first_existing(case_dir, ["src/defines.hpp", "defines.hpp"])
    source_metadata = case_dir / "case_metadata.json"
    source_domain_origin = case_dir / "domain_origin.json"
    source_buildings = first_existing(case_dir, ["buildings.stl", "src/buildings.stl"])

    source_hashes = {
        "SetupCpp": sha256_or_empty(source_setup),
        "DefinesHpp": sha256_or_empty(source_defines),
        "CaseMetadata": sha256_or_empty(source_metadata),
        "DomainOrigin": sha256_or_empty(source_domain_origin),
        "BuildingsStl": sha256_or_empty(source_buildings),
    }

    shutil.copytree(case_dir, out_dir)
    copied_setup = first_existing(out_dir, ["src/setup.cpp", "setup.cpp"])
    if copied_setup is None:
        raise SystemExit(f"copied setup.cpp not found under output directory: {out_dir}")
    flag_status = patch_empty_tunnel_flag(copied_setup)

    copied_metadata = out_dir / "case_metadata.json"
    metadata = read_json(copied_metadata)
    inferred_defaults = fill_inferred_args(args, metadata, copied_setup)
    args.velocity_scale = resolve_velocity_scale(args, metadata)
    run_plan_patch = patch_setup_run_plan(
        copied_setup,
        args.time_steps,
        args.vtk_save_interval,
        max(args.vtk_save_start_step, 0),
    )
    metadata_run_plan = update_metadata_run_plan(metadata, args)
    metadata.setdefault("Validation", {})
    if isinstance(metadata["Validation"], dict):
        metadata["Validation"]["EmptyTunnelVariant"] = True
        metadata["Validation"]["ParentCaseDir"] = str(case_dir)
        metadata["Validation"]["ParentSetupSha256"] = source_hashes["SetupCpp"]
        metadata["Validation"]["VariantGeneratedAtUtc"] = utc_now()
        metadata["Validation"]["VariantPurpose"] = "native_empty_tunnel_inlet_preservation_before_building_validation"
    else:
        metadata["Validation"] = {
            "EmptyTunnelVariant": True,
            "ParentCaseDir": str(case_dir),
            "ParentSetupSha256": source_hashes["SetupCpp"],
            "VariantGeneratedAtUtc": utc_now(),
            "VariantPurpose": "native_empty_tunnel_inlet_preservation_before_building_validation",
        }
    write_json(copied_metadata, metadata)

    copied_defines = first_existing(out_dir, ["src/defines.hpp", "defines.hpp"])
    copied_domain_origin = out_dir / "domain_origin.json"
    copied_buildings = first_existing(out_dir, ["buildings.stl", "src/buildings.stl"])
    copied_hashes = {
        "SetupCpp": sha256_or_empty(copied_setup),
        "DefinesHpp": sha256_or_empty(copied_defines),
        "CaseMetadata": sha256_or_empty(copied_metadata),
        "DomainOrigin": sha256_or_empty(copied_domain_origin),
        "BuildingsStl": sha256_or_empty(copied_buildings),
    }

    commands = build_commands(args, repo, out_dir, manifest_out)
    manifest = {
        "Schema": "citylbm.native_empty_tunnel_case.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "accelerate_validation_by_isolating_inlet_u_k_preservation_before_building_flow_runs",
        "SourceCaseDir": str(case_dir),
        "EmptyTunnelCaseDir": str(out_dir),
        "SetupPath": str(copied_setup),
        "EmptyTunnelFlagStatus": flag_status,
        "RunPlanPatch": run_plan_patch,
        "MetadataRunPlanOverride": metadata_run_plan,
        "GeometryVoxelizationDisabledByEmptyTunnelFlag": True,
        "BuildingsStlRetainedForTraceability": copied_buildings is not None,
        "FluidX3DSource": str(Path(args.fluidx3d_source).expanduser().resolve()) if args.fluidx3d_source else "",
        "FluidX3DSolverWorkingDirectory": str(Path(args.solver_cwd).expanduser().resolve()) if args.solver_cwd else "",
        "BaselineId": args.baseline_id or f"native-empty-tunnel-{out_dir.name}",
        "Expected": {
            "AijCase": args.expected_aij_case,
            "WindDirection": args.expected_wind_direction,
            "WindVector": args.expected_wind_vector,
            "Official": args.official,
            "OfficialConditionFilter": args.official_condition_filter,
            "OfficialWindFilter": args.official_wind_filter,
            "AfCsv": args.af_csv,
            "RequireAfK": bool(args.require_af_k),
            "TimeSteps": args.time_steps,
            "VtkSaveInterval": args.vtk_save_interval,
            "VtkSaveStartStep": args.vtk_save_start_step,
            "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
            "AverageLastN": args.average_last_n,
            "MinVtkFrames": args.min_vtk_frames,
            "MinVtkStepSpan": args.min_vtk_step_span,
            "VelocityScale": str(args.velocity_scale),
            "Uref": args.expected_uref,
            "ZRef": args.z_ref,
            "ExpectedProbeZ": args.expected_probe_z,
            "ExpectedProbeZMin": args.expected_probe_z_min,
            "ExpectedProbeZMax": args.expected_probe_z_max,
            "VtkPattern": args.vtk_pattern,
        },
        "InferredDefaults": inferred_defaults,
        "SourceHashes": source_hashes,
        "CopiedHashes": copied_hashes,
        "Commands": commands,
        "NextAction": (
            "Run Commands.PreflightNoCfd first. If it is only diagnostic because no VTK exists, "
            "run Commands.InstallBuildRunFluidX3D on the workstation, then run the inlet diagnostics/VTK audits "
            "and Commands.ValidationChainAfterRun."
        ),
    }
    write_json(manifest_out, manifest)
    print(f"empty_tunnel_case={out_dir}; manifest={manifest_out}; flag={flag_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
