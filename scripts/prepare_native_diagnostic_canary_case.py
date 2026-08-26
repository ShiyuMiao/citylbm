#!/usr/bin/env python3
"""Create a short native FluidX3D diagnostic canary case clone.

The clone is for runtime diagnostics only. It keeps the generated geometry,
inlet tables and probe metadata, but reduces the solver schedule so the native
runner can test the execution path without spending a paper-length run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


SKIP_DIR_NAMES = {"output", "preflight", "native_source_backups", "__pycache__"}
SKIP_SUFFIXES = {".vtk", ".pvd", ".pvtu", ".vtu", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone a generated native case and shorten it for a diagnostic canary.")
    parser.add_argument("--source-case-dir", required=True)
    parser.add_argument("--out-case-dir", required=True)
    parser.add_argument("--manifest-out", default="")
    parser.add_argument("--time-steps", type=int, default=2000)
    parser.add_argument("--spinup-steps", type=int, default=500)
    parser.add_argument("--vtk-save-interval", type=int, default=500)
    parser.add_argument("--average-last-n", type=int, default=5)
    parser.add_argument(
        "--synthetic-turbulence-update-interval",
        type=int,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_update_interval in setup.cpp.",
    )
    parser.add_argument(
        "--synthetic-turbulence-intensity-scale",
        type=float,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_scale in setup.cpp.",
    )
    parser.add_argument(
        "--synthetic-turbulence-temporal-step-scale",
        type=float,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_temporal_step_scale in setup.cpp.",
    )
    parser.add_argument("--allow-existing", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in SKIP_DIR_NAMES or part.lower().startswith("preflight") for part in rel.parts):
        return True
    return path.is_file() and path.suffix.lower() in SKIP_SUFFIXES


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def copy_case_tree(source: Path, target: Path, allow_existing: bool) -> Dict[str, Any]:
    if not source.is_dir():
        return {"Gate": "fail", "Reasons": ["source_case_dir_missing"], "FilesCopied": 0, "BytesCopied": 0}
    if target.exists() and not allow_existing and any(target.iterdir()):
        return {"Gate": "fail", "Reasons": ["target_case_dir_exists"], "FilesCopied": 0, "BytesCopied": 0}

    target_resolved = target.resolve()
    files_copied = 0
    bytes_copied = 0
    skipped = 0
    for dirpath, dirnames, filenames in os.walk(source):
        current = Path(dirpath)
        try:
            current_resolved = current.resolve()
        except OSError:
            skipped += 1
            continue

        kept_dirs: List[str] = []
        for dirname in dirnames:
            child = current / dirname
            if should_skip(child, source):
                skipped += 1
                continue
            try:
                if path_is_relative_to(child.resolve(), target_resolved):
                    skipped += 1
                    continue
            except OSError:
                skipped += 1
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        if path_is_relative_to(current_resolved, target_resolved):
            continue
        if current != source:
            (target / current.relative_to(source)).mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            src = current / filename
            if should_skip(src, source):
                skipped += 1
                continue
            try:
                if path_is_relative_to(src.resolve(), target_resolved):
                    skipped += 1
                    continue
            except OSError:
                skipped += 1
                continue
            rel = src.relative_to(source)
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            files_copied += 1
            bytes_copied += dst.stat().st_size
    return {
        "Gate": "pass",
        "Reasons": [],
        "FilesCopied": files_copied,
        "BytesCopied": bytes_copied,
        "SkippedItems": skipped,
    }


def first_existing(base: Path, names: Sequence[str]) -> Optional[Path]:
    for name in names:
        path = base / name
        if path.is_file():
            return path
    return None


def replace_required(source: str, pattern: str, replacement: str, reasons: List[str], label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.MULTILINE)
    if count != 1:
        reasons.append(f"setup_patch_missing:{label}")
    return updated


def replace_optional(source: str, pattern: str, replacement: str, count: int = 0) -> tuple[str, int]:
    return re.subn(pattern, replacement, source, count=count, flags=re.MULTILINE)


def normalize_cpp_float_literals(source: str) -> tuple[str, int]:
    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}.000000f"

    return re.subn(r"(?<![\w.+-])(\d+)f\b", repl, source)


def inject_vtk_output(source: str) -> tuple[str, int]:
    if "write_device_to_vtk" in source:
        return source, 0
    return re.subn(
        r"(\bsampleProbes\(\);\s*)",
        "\\1\n            lbm.u.write_device_to_vtk(\"output/\", true);\n",
        source,
        count=1,
    )


def patch_setup(
    setup: Path,
    time_steps: int,
    spinup_steps: int,
    save_interval: int,
    synthetic_turbulence_update_interval: Optional[int],
    synthetic_turbulence_intensity_scale: Optional[float],
    synthetic_turbulence_temporal_step_scale: Optional[float],
) -> Dict[str, Any]:
    if not setup.is_file():
        return {"Gate": "fail", "Reasons": ["setup_cpp_missing"], "Setup": str(setup)}
    before = setup.read_text(encoding="utf-8", errors="replace")
    reasons: List[str] = []
    after = before

    after, direct_run_count = replace_optional(
        after,
        r"\blbm\.run\(\s*(?!0u)(\d+)u?\s*\);",
        f"lbm.run({time_steps}u);",
        count=1,
    )
    after, loop_limit_count = replace_optional(
        after,
        r"\bwhile\s*\(\s*lbm\.get_t\(\)\s*<\s*\d+u?\s*\)",
        f"while(lbm.get_t() < {time_steps}u)",
    )
    after, remaining_count = replace_optional(
        after,
        r"\buint\s+remaining\s*=\s*\d+u?\s*-\s*\(uint\)lbm\.get_t\(\)\s*;",
        f"uint remaining = {time_steps}u - (uint)lbm.get_t();",
    )
    after, step_chunk_count = replace_optional(
        after,
        r"\buint\s+steps_to_run\s*=\s*remaining\s*<\s*\d+u?\s*\?\s*remaining\s*:\s*\d+u?\s*;",
        f"uint steps_to_run = remaining < {save_interval}u ? remaining : {save_interval}u;",
    )
    after, save_remainder_count = replace_optional(
        after,
        r"\buint\s+save_remainder\s*=\s*\(uint\)lbm\.get_t\(\)\s*%\s*\d+u?\s*;",
        f"uint save_remainder = (uint)lbm.get_t() % {save_interval}u;",
    )
    after, until_next_save_count = replace_optional(
        after,
        r"\buint\s+until_next_save\s*=\s*save_remainder\s*==\s*0u\s*\?\s*\d+u?\s*:\s*\d+u?\s*-\s*save_remainder\s*;",
        f"uint until_next_save = save_remainder == 0u ? {save_interval}u : {save_interval}u - save_remainder;",
    )
    save_start_schedule_present = "citylbm_next_vtk_save_step" in after and "citylbm_should_save_vtk" in after
    after, output_condition_count = replace_optional(
        after,
        r"\bif\s*\(\s*\(uint\)lbm\.get_t\(\)\s*%\s*\d+u?\s*==\s*0u\s*\|\|\s*\(uint\)lbm\.get_t\(\)\s*>=\s*\d+u?\s*\)",
        f"if((uint)lbm.get_t() % {save_interval}u == 0u || (uint)lbm.get_t() >= {time_steps}u)",
    )
    if output_condition_count == 0:
        after, output_condition_count = replace_optional(
            after,
            r"\bif\s*\(\s*\(\s*\(uint\)lbm\.get_t\(\)\s*>=\s*\d+u?\s*&&\s*\(uint\)lbm\.get_t\(\)\s*%\s*\d+u?\s*==\s*0u\s*\)\s*\|\|\s*\(uint\)lbm\.get_t\(\)\s*>=\s*\d+u?\s*\)",
            (
                f"if(((uint)lbm.get_t() >= {spinup_steps}u && "
                f"(uint)lbm.get_t() % {save_interval}u == 0u) || "
                f"(uint)lbm.get_t() >= {time_steps}u)"
            ),
        )

    after, total_steps_count = replace_optional(
        after,
        r"\bconst\s+uint\s+citylbm_total_steps\s*=\s*\d+u?\s*;",
        f"const uint citylbm_total_steps = {time_steps}u;",
    )
    after, spinup_count = replace_optional(
        after,
        r"\bconst\s+uint\s+citylbm_spinup_steps\s*=\s*\d+u?\s*;",
        f"const uint citylbm_spinup_steps = {spinup_steps}u;",
    )
    after, save_interval_count = replace_optional(
        after,
        r"\bconst\s+uint\s+citylbm_save_interval\s*=\s*\d+u?\s*;",
        f"const uint citylbm_save_interval = {save_interval}u;",
    )
    after, vtk_save_start_count = replace_optional(
        after,
        r"\bconst\s+uint\s+citylbm_vtk_save_start_step\s*=\s*\d+u?\s*;",
        f"const uint citylbm_vtk_save_start_step = {spinup_steps}u;",
    )
    stg_update_interval_count = 0
    if synthetic_turbulence_update_interval is not None:
        after, stg_update_interval_count = replace_optional(
            after,
            r"\bconst\s+uint\s+citylbm_stg_update_interval\s*=\s*\d+u?\s*;",
            f"const uint citylbm_stg_update_interval = {synthetic_turbulence_update_interval}u;",
        )
        if stg_update_interval_count != 1:
            reasons.append("setup_patch_missing:citylbm_stg_update_interval")
    stg_intensity_scale_count = 0
    if synthetic_turbulence_intensity_scale is not None:
        after, stg_intensity_scale_count = replace_optional(
            after,
            r"\bconst\s+float\s+citylbm_stg_scale\s*=\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?f?\s*;",
            f"const float citylbm_stg_scale = {synthetic_turbulence_intensity_scale:.6f}f;",
        )
        if stg_intensity_scale_count != 1:
            reasons.append("setup_patch_missing:citylbm_stg_scale")
    stg_temporal_step_scale_count = 0
    if synthetic_turbulence_temporal_step_scale is not None:
        after, stg_temporal_step_scale_count = replace_optional(
            after,
            r"\bconst\s+float\s+citylbm_stg_temporal_step_scale\s*=\s*[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?f?\s*;",
            f"const float citylbm_stg_temporal_step_scale = {synthetic_turbulence_temporal_step_scale:.6f}f;",
        )
        if stg_temporal_step_scale_count != 1:
            reasons.append("setup_patch_missing:citylbm_stg_temporal_step_scale")
    if direct_run_count == 0 and loop_limit_count == 0 and total_steps_count == 0:
        reasons.append("setup_patch_missing:solver_schedule")
    if loop_limit_count > 0 and (remaining_count == 0 or (output_condition_count == 0 and not save_start_schedule_present)):
        reasons.append("setup_patch_incomplete:loop_schedule")
    old_schedule_constant_count = total_steps_count + spinup_count + save_interval_count
    new_schedule_constant_count = total_steps_count + save_interval_count + vtk_save_start_count
    if old_schedule_constant_count not in (0, 3) and new_schedule_constant_count not in (0, 3):
        reasons.append("setup_patch_incomplete:citylbm_schedule_constants")
    after, normalized_float_literal_count = normalize_cpp_float_literals(after)
    after, vtk_output_injection_count = inject_vtk_output(after)
    after = re.sub(
        r'("Step: "\s*\+\s*to_string\(lbm\.get_t\(\)\)\s*\+\s*"\s*/\s*)\d+(")',
        rf"\g<1>{time_steps}\2",
        after,
    )
    if not reasons and after != before:
        setup.write_text(after, encoding="utf-8")
    elif after == before:
        reasons.append("setup_patch_no_change")
    return {
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons,
        "Setup": str(setup),
        "Changed": after != before and not reasons,
        "DirectRunReplacementCount": direct_run_count,
        "LoopLimitReplacementCount": loop_limit_count,
        "RemainingReplacementCount": remaining_count,
        "StepChunkReplacementCount": step_chunk_count,
        "SaveRemainderReplacementCount": save_remainder_count,
        "UntilNextSaveReplacementCount": until_next_save_count,
        "OutputConditionReplacementCount": output_condition_count,
        "ScheduleConstantReplacementCount": max(old_schedule_constant_count, new_schedule_constant_count),
        "VtkSaveStartReplacementCount": vtk_save_start_count,
        "SaveStartSchedulePresent": save_start_schedule_present,
        "StgUpdateIntervalReplacementCount": stg_update_interval_count,
        "StgIntensityScaleReplacementCount": stg_intensity_scale_count,
        "StgTemporalStepScaleReplacementCount": stg_temporal_step_scale_count,
        "NormalizedCppFloatLiteralCount": normalized_float_literal_count,
        "InjectedVtkOutputCount": vtk_output_injection_count,
        "BeforeSha256": hashlib.sha256(before.encode("utf-8")).hexdigest(),
        "AfterSha256": sha256(setup) if setup.is_file() else "",
    }


def frame_count(time_steps: int, save_interval: int, save_start_step: Optional[int]) -> int:
    first = save_interval if save_start_step is None or save_start_step <= 0 else save_start_step
    if first > time_steps:
        return 0
    return ((time_steps - first) // save_interval) + 1


def final_window_step_span(time_steps: int, save_interval: int, save_start_step: int, average_last_n: int) -> Optional[int]:
    first = save_interval if save_start_step <= 0 else save_start_step
    if save_interval <= 0 or first > time_steps:
        return None
    steps = list(range(first, time_steps + 1, save_interval))
    selected = steps[-max(1, average_last_n) :]
    if len(selected) < 2:
        return 0
    return selected[-1] - selected[0]


def as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def runtime_inlet_diagnostics_name(metadata: Dict[str, Any], setup_path: Path) -> str:
    for key in [
        "RuntimeInletDiagnosticsCsv",
        "runtime_inlet_diagnostics_csv",
        "InletDiagnosticsCsv",
        "inlet_diagnostics_csv",
    ]:
        value = str(metadata.get(key) or "").strip()
        if value:
            return value

    if setup_path.is_file():
        source = setup_path.read_text(encoding="utf-8-sig", errors="replace")
        match = re.search(r'citylbm_inlet_diagnostics_csv\s*=\s*"([^"]+)"', source)
        if match:
            return match.group(1).strip()

    return "citylbm_inlet_turbulence_stats.csv"


def update_metadata(
    metadata_path: Path,
    source_case: Path,
    target_case: Path,
    time_steps: int,
    spinup_steps: int,
    save_interval: int,
    average_last_n: int,
    synthetic_turbulence_update_interval: Optional[int],
    synthetic_turbulence_intensity_scale: Optional[float],
    synthetic_turbulence_temporal_step_scale: Optional[float],
) -> Dict[str, Any]:
    metadata = read_json(metadata_path)
    if not metadata:
        return {"Gate": "not_applicable", "Reasons": ["metadata_missing_or_invalid"], "Metadata": str(metadata_path)}

    expected_frames = frame_count(time_steps, save_interval, spinup_steps)
    setup_path = first_existing(target_case, ["src/setup.cpp", "setup.cpp"]) or target_case / "setup.cpp"
    metadata["TimeSteps"] = time_steps
    metadata["SimulationTimeSteps"] = time_steps
    metadata["SaveInterval"] = save_interval
    metadata["VtkSaveInterval"] = save_interval
    metadata["SaveStartStep"] = spinup_steps
    metadata["VtkSaveStartStep"] = spinup_steps
    metadata["ExpectedVtkFrameCount"] = expected_frames
    metadata["RuntimeInletDiagnosticsCsv"] = runtime_inlet_diagnostics_name(metadata, setup_path)
    if synthetic_turbulence_update_interval is not None:
        metadata["SyntheticTurbulenceUpdateInterval"] = synthetic_turbulence_update_interval
    if synthetic_turbulence_intensity_scale is not None:
        metadata["SyntheticTurbulenceIntensityScale"] = synthetic_turbulence_intensity_scale
    if synthetic_turbulence_temporal_step_scale is not None:
        metadata["SyntheticTurbulenceTemporalStepScale"] = synthetic_turbulence_temporal_step_scale
    update_interval = synthetic_turbulence_update_interval or as_int(metadata.get("SyntheticTurbulenceUpdateInterval"))
    step_span = final_window_step_span(time_steps, save_interval, spinup_steps, average_last_n)
    expected_refreshes = step_span // update_interval if step_span is not None and update_interval and update_interval > 0 else None
    if expected_refreshes is not None:
        metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] = expected_refreshes
    vtk = metadata.get("VtkOutput")
    if not isinstance(vtk, dict):
        vtk = {}
    vtk["SaveIntervalSteps"] = save_interval
    vtk["SaveStartStep"] = spinup_steps
    vtk["EstimatedPostSpinupFrameCount"] = expected_frames
    metadata["VtkOutput"] = vtk

    averaging = metadata.get("time_averaging")
    if not isinstance(averaging, dict):
        averaging = {}
    averaging["time_steps"] = time_steps
    averaging["spinup_steps"] = spinup_steps
    averaging["save_interval"] = save_interval
    averaging["expected_post_spinup_frames"] = expected_frames
    averaging["mode"] = "diagnostic_canary_runtime_only"
    metadata["time_averaging"] = averaging

    outputs = metadata.get("outputs")
    if isinstance(outputs, dict):
        outputs["case_dir"] = str(target_case)
        outputs["setup_cpp"] = str(setup_path)
        outputs["defines_hpp"] = str(first_existing(target_case, ["src/defines.hpp", "defines.hpp"]) or target_case / "defines.hpp")
        outputs["buildings_stl"] = str(first_existing(target_case, ["buildings.stl", "geometry/buildings.stl"]) or target_case / "buildings.stl")
        outputs["domain_origin_json"] = str(target_case / "domain_origin.json")

    metadata["DiagnosticCanary"] = {
        "GeneratedAtUtc": utc_now(),
        "SourceCaseDir": str(source_case),
        "CanaryCaseDir": str(target_case),
        "Purpose": "short_runtime_diagnostic_only_not_paper_grade_accuracy",
        "TimeSteps": time_steps,
        "SpinupSteps": spinup_steps,
        "VtkSaveInterval": save_interval,
        "ExpectedVtkFrameCount": expected_frames,
        "AverageLastN": average_last_n,
        "ExpectedFinalWindowStepSpan": step_span,
        "SyntheticTurbulenceExpectedFinalWindowRefreshCount": expected_refreshes,
        "SyntheticTurbulenceUpdateInterval": update_interval,
        "SyntheticTurbulenceUpdateIntervalOverride": synthetic_turbulence_update_interval,
        "SyntheticTurbulenceIntensityScaleOverride": synthetic_turbulence_intensity_scale,
        "SyntheticTurbulenceTemporalStepScaleOverride": synthetic_turbulence_temporal_step_scale,
    }
    write_json(metadata_path, metadata)
    return {
        "Gate": "pass",
        "Reasons": [],
        "Metadata": str(metadata_path),
        "TimeSteps": time_steps,
        "SpinupSteps": spinup_steps,
        "VtkSaveInterval": save_interval,
        "ExpectedVtkFrameCount": expected_frames,
        "AverageLastN": average_last_n,
        "ExpectedFinalWindowStepSpan": step_span,
        "SyntheticTurbulenceExpectedFinalWindowRefreshCount": expected_refreshes,
        "SyntheticTurbulenceUpdateInterval": update_interval,
        "SyntheticTurbulenceUpdateIntervalOverride": synthetic_turbulence_update_interval,
        "SyntheticTurbulenceIntensityScaleOverride": synthetic_turbulence_intensity_scale,
        "SyntheticTurbulenceTemporalStepScaleOverride": synthetic_turbulence_temporal_step_scale,
    }


def main() -> int:
    args = parse_args()
    source_case = Path(args.source_case_dir).expanduser().resolve()
    target_case = Path(args.out_case_dir).expanduser().resolve()
    manifest_out = Path(args.manifest_out).expanduser().resolve() if args.manifest_out else target_case / "diagnostic_canary_case_manifest.json"

    reasons: List[str] = []
    if args.time_steps <= 0:
        reasons.append("time_steps_must_be_positive")
    if args.spinup_steps < 0:
        reasons.append("spinup_steps_must_be_non_negative")
    if args.vtk_save_interval <= 0:
        reasons.append("vtk_save_interval_must_be_positive")
    if args.spinup_steps > args.time_steps:
        reasons.append("spinup_steps_exceeds_time_steps")
    if args.average_last_n <= 0:
        reasons.append("average_last_n_must_be_positive")
    if args.synthetic_turbulence_update_interval is not None and args.synthetic_turbulence_update_interval <= 0:
        reasons.append("synthetic_turbulence_update_interval_must_be_positive")
    if args.synthetic_turbulence_intensity_scale is not None and args.synthetic_turbulence_intensity_scale <= 0.0:
        reasons.append("synthetic_turbulence_intensity_scale_must_be_positive")
    if args.synthetic_turbulence_temporal_step_scale is not None and args.synthetic_turbulence_temporal_step_scale <= 0.0:
        reasons.append("synthetic_turbulence_temporal_step_scale_must_be_positive")

    copy_result = {"Gate": "not_run", "Reasons": []}
    setup_result = {"Gate": "not_run", "Reasons": []}
    metadata_result = {"Gate": "not_run", "Reasons": []}
    if not reasons:
        copy_result = copy_case_tree(source_case, target_case, args.allow_existing)
        reasons.extend(str(reason) for reason in copy_result.get("Reasons", []))
    if not reasons:
        setup_path = first_existing(target_case, ["src/setup.cpp", "setup.cpp"]) or target_case / "setup.cpp"
        setup_result = patch_setup(
            setup_path,
            args.time_steps,
            args.spinup_steps,
            args.vtk_save_interval,
            args.synthetic_turbulence_update_interval,
            args.synthetic_turbulence_intensity_scale,
            args.synthetic_turbulence_temporal_step_scale,
        )
        reasons.extend(str(reason) for reason in setup_result.get("Reasons", []))
    if not reasons:
        metadata_result = update_metadata(
            target_case / "case_metadata.json",
            source_case,
            target_case,
            args.time_steps,
            args.spinup_steps,
            args.vtk_save_interval,
            args.average_last_n,
            args.synthetic_turbulence_update_interval,
            args.synthetic_turbulence_intensity_scale,
            args.synthetic_turbulence_temporal_step_scale,
        )
        if metadata_result.get("Gate") == "fail":
            reasons.extend(str(reason) for reason in metadata_result.get("Reasons", []))

    manifest = {
        "Schema": "citylbm.native_diagnostic_canary_case.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "clone_generated_native_case_for_short_runtime_diagnostics_only",
        "SourceCaseDir": str(source_case),
        "CanaryCaseDir": str(target_case),
        "Gate": "pass" if not reasons else "fail",
        "Reasons": list(dict.fromkeys(reasons)),
        "ReasonsCsv": ";".join(dict.fromkeys(reasons)),
        "RequestedSchedule": {
            "TimeSteps": args.time_steps,
            "SpinupSteps": args.spinup_steps,
            "VtkSaveInterval": args.vtk_save_interval,
            "AverageLastN": args.average_last_n,
            "ExpectedVtkFrameCount": frame_count(args.time_steps, args.vtk_save_interval, args.spinup_steps),
            "SyntheticTurbulenceUpdateInterval": args.synthetic_turbulence_update_interval,
            "SyntheticTurbulenceIntensityScale": args.synthetic_turbulence_intensity_scale,
            "SyntheticTurbulenceTemporalStepScale": args.synthetic_turbulence_temporal_step_scale,
        },
        "Copy": copy_result,
        "SetupPatch": setup_result,
        "MetadataPatch": metadata_result,
        "PaperUsePolicy": "never_use_canary_case_for_paper_accuracy_claims",
    }
    write_json(manifest_out, manifest)
    print(f"native_diagnostic_canary_case_gate={manifest['Gate']}; manifest={manifest_out}")
    if manifest["Reasons"]:
        print("reasons=" + manifest["ReasonsCsv"])
    return 0 if manifest["Gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
