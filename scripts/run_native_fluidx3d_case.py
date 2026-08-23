#!/usr/bin/env python3
"""Prepare and optionally run a strict native FluidX3D validation case.

This runner is intentionally conservative. By default it only validates the
FluidX3D source root and CityLBM-generated case package, then writes a manifest.
Use --install, --build, and --run explicitly on the experiment workstation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


REQUIRED_SOURCE_FILES = [
    ("Native FluidX3D original setup", Path("src") / "setup.cpp"),
    ("Native FluidX3D original defines", Path("src") / "defines.hpp"),
    ("Native FluidX3D lbm.hpp", Path("src") / "lbm.hpp"),
    ("Native FluidX3D lbm.cpp", Path("src") / "lbm.cpp"),
]

REQUIRED_CASE_FILES = [
    ("FluidX3D setup", Path("src") / "setup.cpp"),
    ("FluidX3D defines", Path("src") / "defines.hpp"),
    ("Case metadata", Path("case_metadata.json")),
    ("Domain origin", Path("domain_origin.json")),
    ("Validation protocol audit", Path("validation_protocol_audit.json")),
]

OPTIONAL_CASE_FILES = [
    ("Buildings STL", Path("buildings.stl")),
    ("Boundary evidence", Path("boundary_conditions.json")),
    ("Roughness layout", Path("roughness_layout.csv")),
    ("Equivalent precursor evidence", Path("equivalent_precursor_evidence.json")),
]

REQUIRED_PROTOCOL_ITEM_KEYS = [
    "inlet_mean_profile",
    "inlet_turbulence_k",
    "inlet_turbulence_length_scale",
    "inlet_reynolds_stress_tensor",
    "inlet_temporal_sampling",
    "inlet_distribution_consistency",
    "native_fluidx3d_baseline",
    "boundary_conditions",
    "wall_roughness_model",
    "lbm_stability_scaling",
    "time_averaging",
    "wind_direction_sign",
    "coordinate_transform",
    "probe_projection",
    "normalization_basis",
    "systematic_bias_gate",
    "grid_resolution",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a strict native FluidX3D run manifest, with optional install/build/run steps."
    )
    parser.add_argument("--case-dir", required=True, help="CityLBM-generated native case directory.")
    parser.add_argument("--fluidx3d-source", required=True, help="Explicit native FluidX3D source root.")
    parser.add_argument("--out", required=True, help="Output native_fluidx3d_baseline_manifest.json path.")
    parser.add_argument("--baseline-id", default="", help="Stable ID for this native baseline.")
    parser.add_argument("--install", action="store_true", help="Replace FluidX3D src/setup.cpp and src/defines.hpp from case.")
    parser.add_argument("--build", action="store_true", help="Build the native FluidX3D source tree after install/preflight.")
    parser.add_argument("--run", action="store_true", help="Run FluidX3D.exe after build/preflight.")
    parser.add_argument("--msbuild", default="", help="Optional MSBuild executable path.")
    parser.add_argument("--configuration", default="Release", help="MSBuild configuration.")
    parser.add_argument("--platform", default="x64", help="MSBuild platform.")
    parser.add_argument("--exe", default="", help="Optional FluidX3D executable path.")
    parser.add_argument("--timeout-seconds", type=int, default=0, help="Optional solver timeout, 0 disables timeout.")
    parser.add_argument("--expected-aij-case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--expected-wind-direction", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument("--time-steps", type=int, default=None, help="Planned solver steps recorded in SharedRunConditions.")
    parser.add_argument("--vtk-save-interval", type=int, default=None, help="Planned VTK save interval.")
    parser.add_argument("--expected-vtk-frame-count", type=int, default=None, help="Planned VTK frame count.")
    parser.add_argument("--average-last-n", type=int, default=40, help="Required final VTK averaging-window frame count.")
    parser.add_argument("--min-vtk-frames", type=int, default=40, help="Minimum planned VTK frames for strict validation.")
    parser.add_argument("--min-vtk-step-span", type=int, default=20000, help="Minimum planned final-window solver-step span.")
    parser.add_argument("--min-stg-refreshes", type=int, default=200, help="Minimum planned synthetic-inlet refreshes in the final averaging window.")
    parser.add_argument("--output-dir", default="", help="Directory to inspect for u-*.vtk after run.")
    parser.add_argument("--vtk-pattern", default="u-*.vtk", help="VTK glob pattern.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_or_empty(path: Optional[Path]) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    return sha256(path)


def json_load(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return None


def as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if not parsed.is_integer():
            return None
        return int(parsed)


def metadata_value(metadata: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in metadata:
            return metadata.get(key)
    return None


def metadata_bool(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[bool]:
    return as_bool(metadata_value(metadata, keys))


def metadata_int(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[int]:
    return as_int(metadata_value(metadata, keys))


def protocol_items(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["Items", "items", "ProtocolItems", "protocol_items"]:
        value = audit.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def protocol_item_key(item: Dict[str, Any]) -> str:
    return str(item.get("Key") or item.get("key") or "").strip()


def protocol_item_status(item: Dict[str, Any]) -> str:
    return str(item.get("Status") or item.get("status") or "").strip().lower()


def audit_validation_protocol(path: Path) -> Dict[str, Any]:
    audit = json_load(path)
    items = protocol_items(audit)
    by_key = {protocol_item_key(item): protocol_item_status(item) for item in items if protocol_item_key(item)}
    missing_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key not in by_key]
    empty_status_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key in by_key and not by_key[key]]
    fail_keys = [key for key, status in by_key.items() if status == "fail"]
    risk_keys = [key for key, status in by_key.items() if status == "risk"]
    partial_keys = [key for key, status in by_key.items() if status == "partial"]
    reasons = []
    if not audit or not items:
        reasons.append("validation_protocol_audit_missing_or_empty")
    reasons.extend(f"validation_protocol_item_missing:{key}" for key in missing_keys)
    reasons.extend(f"validation_protocol_item_status_missing:{key}" for key in empty_status_keys)
    reasons.extend(f"validation_protocol_item_fail:{key}" for key in fail_keys)
    return {
        "Path": str(path.resolve()),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "AuditGate": str(audit.get("Gate") or audit.get("gate") or ""),
        "ItemCount": len(items),
        "RequiredItemKeys": REQUIRED_PROTOCOL_ITEM_KEYS,
        "Statuses": by_key,
        "MissingKeys": missing_keys,
        "EmptyStatusKeys": empty_status_keys,
        "FailKeys": fail_keys,
        "RiskKeys": risk_keys,
        "PartialKeys": partial_keys,
    }


def path_record(role: str, path: Path) -> Dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "Role": role,
        "Path": str(path.resolve()),
        "Exists": exists,
        "HashAlgorithm": "SHA256",
        "Sha256": sha256(path) if exists else "",
    }


def optional_path_record(role: str, path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return None
    return path_record(role, path)


def detect_build_system(source_root: Path) -> Dict[str, Any]:
    solution_files = sorted(source_root.glob("*.sln"))
    has_makefile = (source_root / "Makefile").exists()
    has_cmake = (source_root / "CMakeLists.txt").exists()
    return {
        "HasSolution": bool(solution_files),
        "SolutionFiles": [str(path.resolve()) for path in solution_files],
        "HasMakefile": has_makefile,
        "MakefilePath": str((source_root / "Makefile").resolve()) if has_makefile else "",
        "HasCMakeLists": has_cmake,
        "CMakeListsPath": str((source_root / "CMakeLists.txt").resolve()) if has_cmake else "",
    }


def validate_source_root(source_root: Path) -> Dict[str, Any]:
    missing: List[str] = []
    for _, rel in REQUIRED_SOURCE_FILES:
        if not (source_root / rel).is_file():
            missing.append(rel.as_posix())
    build = detect_build_system(source_root)
    if not (build["HasSolution"] or build["HasMakefile"] or build["HasCMakeLists"]):
        missing.append("FluidX3D.sln|Makefile|CMakeLists.txt")
    return {
        **build,
        "HasSrcDirectory": (source_root / "src").is_dir(),
        "HasSetupCpp": (source_root / "src" / "setup.cpp").is_file(),
        "HasDefinesHpp": (source_root / "src" / "defines.hpp").is_file(),
        "HasLbmHpp": (source_root / "src" / "lbm.hpp").is_file(),
        "HasLbmCpp": (source_root / "src" / "lbm.cpp").is_file(),
        "MissingRequiredItems": missing,
        "IsValid": not missing,
    }


def collect_required_files(source_root: Path, case_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for role, rel in REQUIRED_SOURCE_FILES:
        records.append(path_record(role, source_root / rel))
    for role, rel in REQUIRED_CASE_FILES:
        records.append(path_record(role, case_dir / rel))
    for role, rel in OPTIONAL_CASE_FILES:
        record = optional_path_record(role, case_dir / rel)
        if record is not None:
            records.append(record)
    return records


def read_case_value(metadata: Dict[str, Any], keys: Sequence[str]) -> str:
    for key in keys:
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def case_identity(metadata: Dict[str, Any]) -> Tuple[str, str]:
    case = read_case_value(metadata, ["AijCase", "AIJCase", "case", "Case", "CaseName"])
    wind = read_case_value(metadata, ["WindDirection", "WindDirectionLabel", "wind_direction", "windDirection"])
    return case, wind


def identity_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def identity_matches(expected: str, actual: str) -> bool:
    expected_token = identity_token(expected)
    actual_token = identity_token(actual)
    if not expected_token:
        return True
    if not actual_token:
        return False
    return expected_token == actual_token or expected_token in actual_token


def copy_if_present(src: Path, dst: Path) -> Optional[Dict[str, Any]]:
    if not src.exists() or not src.is_file():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return {
        "Source": str(src.resolve()),
        "Target": str(dst.resolve()),
        "Sha256": sha256(dst),
    }


def install_case(case_dir: Path, source_root: Path, backup_root: Path) -> Dict[str, Any]:
    backup_root.mkdir(parents=True, exist_ok=True)
    backups: List[Dict[str, Any]] = []
    installed: List[Dict[str, Any]] = []
    for rel in [Path("src") / "setup.cpp", Path("src") / "defines.hpp"]:
        src = case_dir / rel
        dst = source_root / rel
        if dst.exists():
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(dst), str(backup))
            backups.append({"Role": rel.as_posix(), "Path": str(backup.resolve()), "Sha256": sha256(backup)})
        copied = copy_if_present(src, dst)
        if copied is not None:
            copied["Role"] = rel.as_posix()
            installed.append(copied)
    for name in ["case_metadata.json", "domain_origin.json", "buildings.stl", "roughness_layout.csv", "equivalent_precursor_evidence.json"]:
        copied = copy_if_present(case_dir / name, source_root / name)
        if copied is not None:
            copied["Role"] = name
            installed.append(copied)
    return {"Backups": backups, "InstalledFiles": installed}


def find_msbuild(explicit: str) -> str:
    if explicit:
        return explicit
    found = shutil.which("msbuild")
    return found or ""


def build_command(source_root: Path, msbuild: str, configuration: str, platform: str) -> List[str]:
    solutions = sorted(source_root.glob("*.sln"))
    if msbuild and solutions:
        return [msbuild, str(solutions[0]), f"/p:Configuration={configuration}", f"/p:Platform={platform}"]
    if (source_root / "Makefile").exists():
        return ["make"]
    return []


def run_process(command: Sequence[str], cwd: Path, timeout: int) -> Dict[str, Any]:
    if not command:
        return {
            "Command": [],
            "ReturnCode": None,
            "ElapsedSeconds": 0.0,
            "Stdout": "",
            "Stderr": "",
            "TimedOut": False,
            "Gate": "not_requested",
        }
    start = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout if timeout > 0 else None,
            check=False,
        )
        elapsed = time.monotonic() - start
        return {
            "Command": list(command),
            "ReturnCode": completed.returncode,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": completed.stdout,
            "Stderr": completed.stderr,
            "TimedOut": False,
            "Gate": "pass" if completed.returncode == 0 else "fail",
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        return {
            "Command": list(command),
            "ReturnCode": None,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": exc.stdout or "",
            "Stderr": exc.stderr or "",
            "TimedOut": True,
            "Gate": "fail",
        }


def find_executable(source_root: Path, explicit: str) -> Optional[Path]:
    if explicit:
        path = Path(explicit).expanduser()
        return path.resolve() if path.exists() else path
    candidates = [
        source_root / "bin" / "FluidX3D.exe",
        source_root / "x64" / "Release" / "FluidX3D.exe",
        source_root / "Release" / "FluidX3D.exe",
        source_root / "FluidX3D.exe",
    ]
    return next((path.resolve() for path in candidates if path.exists()), candidates[0].resolve())


def collect_vtk_files(output_dir: Path, pattern: str) -> List[Dict[str, Any]]:
    if not output_dir.exists():
        return []
    files = sorted(output_dir.glob(pattern))
    nested = output_dir / "output"
    if nested.exists():
        files.extend(sorted(nested.glob(pattern)))
    unique = {str(path.resolve()).lower(): path for path in files}
    return [path_record("VTK velocity field", path) for path in unique.values() if path.is_file()]


def planned_frame_count(time_steps: Optional[int], save_interval: Optional[int]) -> Optional[int]:
    if time_steps is None or save_interval is None or time_steps <= 0 or save_interval <= 0:
        return None
    return time_steps // save_interval


def planned_final_window_span(
    time_steps: Optional[int],
    save_interval: Optional[int],
    average_last_n: int,
) -> Optional[int]:
    frame_count = planned_frame_count(time_steps, save_interval)
    if frame_count is None or frame_count <= 0:
        return None
    selected = min(frame_count, max(average_last_n, 1))
    if selected <= 1:
        return 0
    return (selected - 1) * save_interval


def audit_planned_vtk_schedule(
    time_steps: Optional[int],
    save_interval: Optional[int],
    expected_frame_count: Optional[int],
    average_last_n: int,
    min_frames: int,
    min_step_span: int,
) -> Dict[str, Any]:
    computed_frame_count = planned_frame_count(time_steps, save_interval)
    final_window_span = planned_final_window_span(time_steps, save_interval, average_last_n)
    reasons: List[str] = []
    if time_steps is None or time_steps <= 0:
        reasons.append("time_steps_missing_or_invalid")
    if save_interval is None or save_interval <= 0:
        reasons.append("vtk_save_interval_missing_or_invalid")
    if computed_frame_count is None:
        reasons.append("planned_vtk_frame_count_unavailable")
    elif computed_frame_count < min_frames:
        reasons.append(f"planned_vtk_frame_count_{computed_frame_count}_below_minimum_{min_frames}")
    if expected_frame_count is None:
        reasons.append("expected_vtk_frame_count_missing")
    elif computed_frame_count is not None and expected_frame_count != computed_frame_count:
        reasons.append(f"expected_vtk_frame_count_{expected_frame_count}_does_not_match_computed_{computed_frame_count}")
    if final_window_span is None:
        reasons.append("planned_final_window_step_span_unavailable")
    elif final_window_span < min_step_span:
        reasons.append(f"planned_final_window_step_span_{final_window_span}_below_minimum_{min_step_span}")
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "ComputedFrameCount": computed_frame_count,
        "AverageLastN": average_last_n,
        "MinimumFrameCount": min_frames,
        "FinalWindowStepSpan": final_window_span,
        "MinimumStepSpan": min_step_span,
    }


def audit_planned_synthetic_inlet_sampling(
    metadata: Dict[str, Any],
    final_window_step_span: Optional[int],
    default_min_refreshes: int,
) -> Dict[str, Any]:
    requested = metadata_bool(metadata, ["SyntheticTurbulentInletRequested", "SyntheticTurbulenceRequested"])
    injected = metadata_bool(metadata, ["SyntheticTurbulentInletInjected", "SyntheticTurbulenceInjected"])
    active = requested is True or injected is True
    update_interval = metadata_int(metadata, ["SyntheticTurbulenceUpdateInterval", "SyntheticTurbulentInletUpdateInterval"])
    metadata_minimum = metadata_int(metadata, ["SyntheticTurbulenceMinimumRecommendedRefreshes"])
    minimum_refreshes = metadata_minimum if metadata_minimum is not None and metadata_minimum > 0 else max(default_min_refreshes, 0)
    metadata_expected = metadata_int(metadata, ["SyntheticTurbulenceExpectedFinalWindowRefreshCount"])
    computed_refreshes: Optional[int] = None
    reasons: List[str] = []

    if not active:
        return {
            "Gate": "not_applicable",
            "Reasons": [],
            "ReasonsCsv": "",
            "SyntheticInletRequested": requested,
            "SyntheticInletInjected": injected,
            "SyntheticInletActive": False,
            "UpdateInterval": update_interval,
            "FinalWindowStepSpan": final_window_step_span,
            "ComputedRefreshCount": computed_refreshes,
            "MetadataExpectedRefreshCount": metadata_expected,
            "MinimumRefreshCount": minimum_refreshes,
        }

    if update_interval is None or update_interval <= 0:
        reasons.append("synthetic_inlet_update_interval_missing_or_invalid")
    elif final_window_step_span is None:
        reasons.append("planned_stg_final_window_step_span_unavailable")
    else:
        computed_refreshes = final_window_step_span // update_interval
        if computed_refreshes < minimum_refreshes:
            reasons.append(f"planned_stg_refresh_count_{computed_refreshes}_below_minimum_{minimum_refreshes}")

    if metadata_expected is not None and computed_refreshes is not None and metadata_expected != computed_refreshes:
        reasons.append(f"metadata_stg_refresh_count_{metadata_expected}_does_not_match_computed_{computed_refreshes}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "SyntheticInletRequested": requested,
        "SyntheticInletInjected": injected,
        "SyntheticInletActive": True,
        "UpdateInterval": update_interval,
        "FinalWindowStepSpan": final_window_step_span,
        "ComputedRefreshCount": computed_refreshes,
        "MetadataExpectedRefreshCount": metadata_expected,
        "MinimumRefreshCount": minimum_refreshes,
    }


def runner_gate(reasons: Iterable[str]) -> Dict[str, Any]:
    reason_list = [reason for reason in reasons if reason]
    return {
        "Gate": "pass" if not reason_list else "diagnostic_only",
        "Reasons": reason_list,
        "ReasonsCsv": ";".join(reason_list),
    }


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_path = case_dir / "case_metadata.json"
    metadata = json_load(metadata_path)
    case_label, wind_label = case_identity(metadata)
    validation_protocol = audit_validation_protocol(case_dir / "validation_protocol_audit.json")
    expected_case = args.expected_aij_case.strip()
    expected_wind = args.expected_wind_direction.strip()
    source_validation = validate_source_root(source_root)

    reasons: List[str] = []
    if not case_dir.is_dir():
        reasons.append("case_dir_missing")
    if not source_root.is_dir():
        reasons.append("native_source_root_missing")
    if not source_validation["IsValid"]:
        reasons.append("native_source_validation_failed")
    for role, rel in REQUIRED_CASE_FILES:
        if not (case_dir / rel).is_file():
            reasons.append(f"case_required_file_missing:{role}")
    if validation_protocol["Gate"] != "pass":
        reasons.extend(str(reason) for reason in validation_protocol["Reasons"])
    if expected_case and not case_label:
        reasons.append("case_label_missing_in_metadata")
    elif not identity_matches(expected_case, case_label):
        reasons.append(f"case_label_mismatch:{case_label}")
    if expected_wind and not wind_label:
        reasons.append("wind_direction_missing_in_metadata")
    elif not identity_matches(expected_wind, wind_label):
        reasons.append(f"wind_direction_mismatch:{wind_label}")

    install_record: Dict[str, Any] = {"Requested": args.install, "Performed": False, "Backups": [], "InstalledFiles": []}
    if args.install:
        if source_validation["IsValid"] and case_dir.is_dir():
            install_data = install_case(case_dir, source_root, out_path.parent / "native_source_backups")
            install_record.update(install_data)
            install_record["Performed"] = True
        else:
            reasons.append("install_requested_but_preflight_failed")

    msbuild = find_msbuild(args.msbuild)
    command = build_command(source_root, msbuild, args.configuration, args.platform)
    build_record: Dict[str, Any] = {
        "Requested": args.build,
        "MSBuild": msbuild,
        "Command": command,
        "ReturnCode": None,
        "ElapsedSeconds": 0.0,
        "Stdout": "",
        "Stderr": "",
        "TimedOut": False,
        "Gate": "not_requested",
    }
    if args.build:
        if not command:
            build_record["Gate"] = "fail"
            reasons.append("build_requested_but_no_build_command")
        else:
            build_record.update(run_process(command, source_root, args.timeout_seconds))
            if build_record["Gate"] != "pass":
                reasons.append("build_failed")

    exe_path = find_executable(source_root, args.exe)
    run_record: Dict[str, Any] = {
        "Requested": args.run,
        "Executable": str(exe_path) if exe_path is not None else "",
        "ExecutableSha256": sha256_or_empty(exe_path),
        "Command": [str(exe_path)] if exe_path is not None else [],
        "ReturnCode": None,
        "ElapsedSeconds": 0.0,
        "Stdout": "",
        "Stderr": "",
        "TimedOut": False,
        "Gate": "not_requested",
    }
    if args.run:
        if exe_path is None or not exe_path.exists():
            run_record["Gate"] = "fail"
            reasons.append("run_requested_but_executable_missing")
        else:
            run_record.update(run_process([str(exe_path)], source_root, args.timeout_seconds))
            if run_record["Gate"] != "pass":
                reasons.append("run_failed")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else case_dir
    vtk_records = collect_vtk_files(output_dir, args.vtk_pattern)
    if args.run and not vtk_records:
        reasons.append("run_requested_but_no_vtk_output_found")

    vtk_schedule = audit_planned_vtk_schedule(
        args.time_steps,
        args.vtk_save_interval,
        args.expected_vtk_frame_count,
        args.average_last_n,
        args.min_vtk_frames,
        args.min_vtk_step_span,
    )
    if vtk_schedule["Gate"] != "pass":
        reasons.extend(str(reason) for reason in vtk_schedule["Reasons"])
    synthetic_sampling = audit_planned_synthetic_inlet_sampling(
        metadata,
        vtk_schedule["FinalWindowStepSpan"],
        args.min_stg_refreshes,
    )
    if synthetic_sampling["Gate"] == "diagnostic_only":
        reasons.extend(str(reason) for reason in synthetic_sampling["Reasons"])

    source_validation = validate_source_root(source_root)
    required_files = collect_required_files(source_root, case_dir)
    baseline_id = args.baseline_id.strip() or f"native-fluidx3d-{case_label or 'case'}-{wind_label or 'wind'}-{utc_now()}"
    manifest = {
        "Schema": "citylbm.native_fluidx3d_run_manifest.v1",
        "GeneratedAtUtc": utc_now(),
        "BaselineId": baseline_id,
        "Gate": "required_before_paper_grade_accuracy_claim",
        "NativeFluidX3DPathExplicitlyProvided": True,
        "NativeFluidX3DSourcePath": str(source_root),
        "NativeFluidX3DSourceValidation": source_validation,
        "CaseDir": str(case_dir),
        "CaseMetadataPath": str(metadata_path.resolve()),
        "CaseMetadataSha256": sha256_or_empty(metadata_path),
        "CaseMetadataAijCase": case_label,
        "CaseMetadataWindDirection": wind_label,
        "ExpectedAijCase": expected_case,
        "ExpectedWindDirection": expected_wind,
        "RequiredSourceFiles": required_files,
        "ValidationProtocolAuditGate": validation_protocol,
        "Install": install_record,
        "Build": build_record,
        "Run": run_record,
        "SharedRunConditions": {
            "TimeSteps": args.time_steps,
            "SaveInterval": args.vtk_save_interval,
            "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
            "ComputedVtkFrameCount": vtk_schedule["ComputedFrameCount"],
            "AverageLastN": args.average_last_n,
            "ExpectedFinalWindowStepSpan": vtk_schedule["FinalWindowStepSpan"],
            "MinimumValidationAverageFrames": args.min_vtk_frames,
            "MinimumValidationAverageStepSpan": args.min_vtk_step_span,
            "MinimumSyntheticInletRefreshes": args.min_stg_refreshes,
            "VtkPattern": args.vtk_pattern,
        },
        "PlannedVtkScheduleGate": vtk_schedule,
        "PlannedSyntheticInletSamplingGate": synthetic_sampling,
        "OutputDir": str(output_dir),
        "VtkPattern": args.vtk_pattern,
        "VtkFiles": vtk_records,
        "VtkFileCount": len(vtk_records),
        "RunnerGate": runner_gate(reasons),
    }
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"wrote {out_path}")
    gate = manifest["RunnerGate"]["Gate"]
    if gate != "pass":
        print(f"runner gate: {gate} ({manifest['RunnerGate']['ReasonsCsv']})")
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
