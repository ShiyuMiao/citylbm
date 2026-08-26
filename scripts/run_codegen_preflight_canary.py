#!/usr/bin/env python3
"""Run the fastest current-codegen gate before starting long CFD runs.

The script builds CityLBM, regenerates the current smoke case from source, and
then runs the no-CFD native preflight pack on that freshly generated case. It is
an acceleration gate only: a pass/fail here decides whether a real native
FluidX3D canary is worth launching, not whether validation accuracy is proven.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


DEFAULT_CASE_TO_FAKE_SOURCE = {
    "stg_codegen_smoke": "fake_fluidx3d_source",
    "stg_measured_diagonal_rms": "fake_fluidx3d_source_measured_diagonal_rms",
    "stg_full_reynolds_stress_tensor": "fake_fluidx3d_source_full_reynolds_tensor",
    "casea_full_reynolds_stress_tensor": "fake_fluidx3d_source_casea_full_reynolds_tensor",
}
MIN_CODEGEN_BUILD_FREE_BYTES = 128 * 1024 * 1024
WARN_CODEGEN_BUILD_FREE_BYTES = 512 * 1024 * 1024
MIN_ACTUAL_VALIDATION_STL_BYTES = 512


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build current CityLBM codegen and run the fast native preflight canary gate."
    )
    parser.add_argument(
        "--case-name",
        default="stg_codegen_smoke",
        choices=sorted(DEFAULT_CASE_TO_FAKE_SOURCE),
        help="Fresh case directory emitted by CodegenSmoke under %%TEMP%%/CityLBM.",
    )
    parser.add_argument(
        "--case-dir",
        default="",
        help=(
            "Use an existing CityLBM-generated case directory instead of the %%TEMP%%/CityLBM case. "
            "This skips build/codegen and is intended for strict audits of real AIJ cases."
        ),
    )
    parser.add_argument(
        "--fluidx3d-source",
        default="",
        help="Explicit FluidX3D source root. Defaults to the matching CodegenSmoke fake source tree.",
    )
    parser.add_argument("--solver-cwd", default="", help="Optional future solver working directory for the preflight manifest.")
    parser.add_argument("--out-dir", default="", help="Output directory. Defaults to <case-dir>/preflight_codegen_canary.")
    parser.add_argument("--manifest-out", default="", help="Acceleration manifest path. Defaults to <out-dir>/codegen_preflight_canary_manifest.json.")
    parser.add_argument("--expected-aij-case", default="CaseA")
    parser.add_argument("--expected-wind-direction", default="N")
    parser.add_argument("--expected-wind-vector", default="0,-1,0")
    parser.add_argument("--official", default="", help="Optional official RS/probe CSV; leave empty for source-only codegen gate.")
    parser.add_argument("--af-csv", default="", help="Optional official AF inlet profile CSV.")
    parser.add_argument("--official-condition-filter", default="", help="Optional official RS condition/state filter, e.g. ac for AIJ Case E.")
    parser.add_argument("--official-wind-filter", default="", help="Optional official RS wind-direction filter. Defaults to --expected-wind-direction.")
    parser.add_argument("--length-scale-source", default="", help="Optional official, precursor or calibrated length-scale source file.")
    parser.add_argument(
        "--length-scale-source-type",
        default="official_aij",
        choices=[
            "digital_filter_calibration",
            "literature",
            "official_aij",
            "precursor",
            "recycling",
            "sem_calibration",
            "synthetic_eddy_calibration",
            "wind_tunnel_document",
        ],
        help="Traceable source type for turbulence length-scale evidence.",
    )
    parser.add_argument("--length-scale-source-note", default="", help="Short length-scale evidence provenance note.")
    parser.add_argument("--length-scale-paper-admissible", action="store_true")
    parser.add_argument("--expected-probe-row-count", type=int, default=0)
    parser.add_argument("--expected-probe-z", type=float, default=None)
    parser.add_argument("--expected-probe-z-min", type=float, default=None)
    parser.add_argument("--expected-probe-z-max", type=float, default=None)
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--expected-uref", type=float, default=None)
    parser.add_argument("--time-steps", type=int, default=40000)
    parser.add_argument("--vtk-save-interval", type=int, default=1000)
    parser.add_argument("--vtk-save-start-step", type=int, default=None)
    parser.add_argument("--expected-vtk-frame-count", type=int, default=40)
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-vtk-frames", type=int, default=40)
    parser.add_argument("--min-vtk-step-span", type=int, default=20000)
    parser.add_argument(
        "--diagnostic-canary-stg-update-interval",
        type=int,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_update_interval in the short canary clone.",
    )
    parser.add_argument(
        "--diagnostic-canary-stg-intensity-scale",
        type=float,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_scale in the short canary clone.",
    )
    parser.add_argument(
        "--diagnostic-canary-stg-temporal-step-scale",
        type=float,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_temporal_step_scale in the short canary clone.",
    )
    parser.add_argument("--require-af-k", action="store_true")
    parser.add_argument(
        "--require-actual-geometry",
        action="store_true",
        help=(
            "Require a non-smoke validation geometry before allowing the short native canary route. "
            "Use this when official AIJ probe/AF inputs are supplied."
        ),
    )
    parser.add_argument("--skip-build", action="store_true", help="Use an already built binary for a faster local rerun.")
    parser.add_argument("--skip-codegen", action="store_true", help="Use the existing temp case instead of regenerating it.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help=(
            "Fast iteration mode: skip build and codegen, then rerun the no-CFD preflight "
            "against the existing temp case. Use only after a full run has created that case."
        ),
    )
    parser.add_argument(
        "--allow-diagnostic",
        action="store_true",
        help="Return 0 even if the current codegen gate is diagnostic/fail.",
    )
    args = parser.parse_args()
    if args.diagnostic_canary_stg_update_interval is not None and args.diagnostic_canary_stg_update_interval <= 0:
        raise SystemExit("--diagnostic-canary-stg-update-interval must be positive")
    if args.diagnostic_canary_stg_intensity_scale is not None and args.diagnostic_canary_stg_intensity_scale <= 0.0:
        raise SystemExit("--diagnostic-canary-stg-intensity-scale must be positive")
    if (
        args.diagnostic_canary_stg_temporal_step_scale is not None
        and args.diagnostic_canary_stg_temporal_step_scale <= 0.0
    ):
        raise SystemExit("--diagnostic-canary-stg-temporal-step-scale must be positive")
    return args


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


def fresh_codegen_case_gate(case_dir: Path, required: bool, started_at: float) -> Dict[str, Any]:
    metadata = case_dir / "case_metadata.json"
    if not required:
        return {
            "Gate": "skipped",
            "Required": False,
            "Reasons": [],
            "MetadataPath": str(metadata),
        }

    reasons: List[str] = []
    mtime: Optional[float] = None
    if not metadata.is_file():
        reasons.append("fresh_codegen_case_metadata_missing")
    else:
        mtime = metadata.stat().st_mtime
        if mtime < started_at - 5.0:
            reasons.append("fresh_codegen_case_metadata_older_than_this_run")

    return {
        "Gate": "pass" if not reasons else "fail",
        "Required": True,
        "Reasons": reasons,
        "MetadataPath": str(metadata),
        "MetadataMTime": mtime,
        "RunStartedAt": started_at,
    }


def run_step(
    name: str,
    cmd: Sequence[str],
    cwd: Path,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    started = time.time()
    env = None
    if extra_env:
        env = dict(os.environ)
        env.update(extra_env)
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return {
        "Name": name,
        "Command": list(cmd),
        "ReturnCode": completed.returncode,
        "ElapsedSeconds": round(time.time() - started, 3),
        "Stdout": completed.stdout,
        "Stderr": completed.stderr,
    }


def gate_value(data: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            nested = value.get("Gate") or value.get("gate")
            if nested is not None:
                return str(nested).strip().lower()
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


def path_summary(path: Path) -> Dict[str, Any]:
    return {
        "Path": str(path),
        "Exists": path.exists(),
        "IsFile": path.is_file(),
        "IsDirectory": path.is_dir(),
        "MTimeUtc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
        if path.exists()
        else "",
    }


def nearest_existing_path(path: Path) -> Optional[Path]:
    current = path.expanduser().resolve()
    while not current.exists() and current != current.parent:
        current = current.parent
    return current if current.exists() else None


def net48_reference_assemblies_present() -> bool:
    candidates = [
        Path("C:/Program Files (x86)/Reference Assemblies/Microsoft/Framework/.NETFramework/v4.8"),
        Path("C:/Program Files/Reference Assemblies/Microsoft/Framework/.NETFramework/v4.8"),
    ]
    return any(path.is_dir() for path in candidates)


def audit_codegen_build_environment(repo: Path, require_build_or_codegen: bool) -> Dict[str, Any]:
    dotnet = shutil.which("dotnet") or ""
    measured_path = nearest_existing_path(repo)
    free_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    if measured_path is not None:
        try:
            usage = shutil.disk_usage(measured_path)
            free_bytes = usage.free
            total_bytes = usage.total
        except OSError:
            free_bytes = None
            total_bytes = None

    has_net48_refs = net48_reference_assemblies_present()
    reasons: List[str] = []
    warnings: List[str] = []
    if require_build_or_codegen:
        if not dotnet:
            reasons.append("dotnet_cli_missing")
        if free_bytes is None:
            reasons.append("codegen_build_disk_free_bytes_unavailable")
        elif free_bytes < MIN_CODEGEN_BUILD_FREE_BYTES:
            reasons.append(
                f"codegen_build_disk_free_bytes_{free_bytes}_below_required_{MIN_CODEGEN_BUILD_FREE_BYTES}"
            )
        elif free_bytes < WARN_CODEGEN_BUILD_FREE_BYTES:
            warnings.append(
                f"codegen_build_disk_free_bytes_{free_bytes}_below_warning_{WARN_CODEGEN_BUILD_FREE_BYTES}"
            )
        if not has_net48_refs:
            warnings.append("net48_reference_assemblies_not_found_in_standard_install_paths")

    return {
        "Gate": "not_applicable" if not require_build_or_codegen else ("pass" if not reasons else "blocked"),
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Warnings": warnings,
        "WarningsCsv": ";".join(warnings),
        "DotnetPath": dotnet,
        "RepoRoot": str(repo),
        "MeasuredPath": str(measured_path) if measured_path is not None else "",
        "FreeBytes": free_bytes,
        "TotalBytes": total_bytes,
        "MinimumRequiredFreeBytes": MIN_CODEGEN_BUILD_FREE_BYTES,
        "WarningFreeBytes": WARN_CODEGEN_BUILD_FREE_BYTES,
        "Net48ReferenceAssembliesPresent": has_net48_refs,
        "Net48ReferenceAssembliesHint": (
            "If dotnet build fails, install .NET Framework 4.8 Developer Pack/Targeting Pack or provide a repository-local reference-assemblies package."
        ),
    }


def binary_stl_summary(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {
            "Exists": False,
            "IsBinaryStl": False,
            "TriangleCount": 0,
            "Header": "",
            "Bounds": None,
            "Extents": None,
        }

    data = path.read_bytes()
    header = data[:80].decode("ascii", errors="replace").rstrip("\x00").strip() if len(data) >= 80 else ""
    if len(data) < 84:
        return {
            "Exists": True,
            "IsBinaryStl": False,
            "TriangleCount": 0,
            "Header": header,
            "Bounds": None,
            "Extents": None,
        }

    triangle_count = struct.unpack("<I", data[80:84])[0]
    expected_len = 84 + triangle_count * 50
    if expected_len != len(data):
        return {
            "Exists": True,
            "IsBinaryStl": False,
            "TriangleCount": triangle_count,
            "Header": header,
            "Bounds": None,
            "Extents": None,
        }

    vertices: List[Tuple[float, float, float]] = []
    offset = 84
    for _ in range(triangle_count):
        offset += 12
        for _vertex_index in range(3):
            vertices.append(struct.unpack("<fff", data[offset : offset + 12]))
            offset += 12
        offset += 2

    if not vertices:
        bounds = None
        extents = None
    else:
        mins = [min(vertex[i] for vertex in vertices) for i in range(3)]
        maxs = [max(vertex[i] for vertex in vertices) for i in range(3)]
        bounds = {
            "MinX": mins[0],
            "MinY": mins[1],
            "MinZ": mins[2],
            "MaxX": maxs[0],
            "MaxY": maxs[1],
            "MaxZ": maxs[2],
        }
        extents = {
            "X": maxs[0] - mins[0],
            "Y": maxs[1] - mins[1],
            "Z": maxs[2] - mins[2],
        }

    return {
        "Exists": True,
        "IsBinaryStl": True,
        "TriangleCount": triangle_count,
        "Header": header,
        "Bounds": bounds,
        "Extents": extents,
    }


def is_casea_standard_box(stl: Dict[str, Any], tolerance: float = 1.0e-5) -> bool:
    if not stl.get("IsBinaryStl") or int(stl.get("TriangleCount") or 0) != 12:
        return False
    extents = stl.get("Extents") if isinstance(stl.get("Extents"), dict) else {}
    try:
        sorted_extents = sorted(float(extents[axis]) for axis in ("X", "Y", "Z"))
    except (KeyError, TypeError, ValueError):
        return False
    expected = [0.08, 0.08, 0.16]
    return all(abs(actual - target) <= tolerance for actual, target in zip(sorted_extents, expected))


def infer_aij_case(metadata: Dict[str, Any], expected_aij_case: str) -> str:
    for key in ("AijCase", "CaseName", "Case"):
        value = str(metadata.get(key) or "").strip()
        if value:
            return value
    return expected_aij_case.strip()


def actual_validation_geometry_gate(case_dir: Path, require_actual_geometry: bool, expected_aij_case: str = "") -> Dict[str, Any]:
    metadata_path = case_dir / "case_metadata.json"
    stl_path = case_dir / "buildings.stl"
    metadata = read_json(metadata_path)
    stl_summary = binary_stl_summary(stl_path)
    reasons: List[str] = []
    warnings: List[str] = []

    if not metadata_path.is_file():
        reasons.append("case_metadata_missing")
    if not stl_path.is_file():
        reasons.append("buildings_stl_missing")
        stl_bytes = 0
    else:
        stl_bytes = stl_path.stat().st_size
        aij_case = infer_aij_case(metadata, expected_aij_case)
        casea_standard_box = aij_case.lower() == "casea" and is_casea_standard_box(stl_summary)
        if stl_bytes < MIN_ACTUAL_VALIDATION_STL_BYTES and not casea_standard_box:
            reasons.append(f"buildings_stl_too_small_for_actual_validation:{stl_bytes}")
    aij_case = infer_aij_case(metadata, expected_aij_case)
    casea_standard_box = aij_case.lower() == "casea" and is_casea_standard_box(stl_summary)

    building_count = metadata.get("GeometryBuildingCount")
    try:
        building_count_int = int(building_count)
    except (TypeError, ValueError):
        building_count_int = -1
    if building_count_int <= 0 and not casea_standard_box:
        reasons.append(f"geometry_building_count_not_positive:{building_count}")
    if building_count_int <= 0 and casea_standard_box:
        warnings.append("legacy_metadata_missing_geometry_building_count_but_casea_standard_box_stl_verified")

    dims: Dict[str, int] = {}
    for key in ["Nx", "Ny", "Nz"]:
        try:
            dims[key] = int(metadata.get(key))
        except (TypeError, ValueError):
            dims[key] = 0
    if all(value <= 16 for value in dims.values()):
        reasons.append(f"grid_matches_codegen_smoke_box:{dims.get('Nx')}x{dims.get('Ny')}x{dims.get('Nz')}")

    scene_name = str(metadata.get("SceneName") or "")
    profile_csv = str(metadata.get("WindProfileCsvPath") or "")
    if "smoke" in scene_name.lower() or "smoke" in profile_csv.lower():
        reasons.append("metadata_names_indicate_smoke_case")

    if not require_actual_geometry and reasons:
        warnings.extend(reasons)
        reasons = []

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Required": bool(require_actual_geometry),
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Warnings": warnings,
        "WarningsCsv": ";".join(warnings),
        "CaseMetadataPath": str(metadata_path),
        "BuildingsStlPath": str(stl_path),
        "BuildingsStlBytes": stl_bytes,
        "StlSummary": stl_summary,
        "AijCase": aij_case,
        "CaseAStandardBoxGeometry": bool(casea_standard_box),
        "GeometryBuildingCount": building_count,
        "Nx": dims.get("Nx", 0),
        "Ny": dims.get("Ny", 0),
        "Nz": dims.get("Nz", 0),
        "Interpretation": (
            "actual_geometry_ready_for_validation_preflight"
            if not reasons
            else "smoke_or_missing_geometry_do_not_run_accuracy_or_paper_validation"
        ),
    }


def main() -> int:
    args = parse_args()
    if args.quick:
        args.skip_build = True
        args.skip_codegen = True

    started_at = time.time()
    repo = Path(__file__).resolve().parents[1]
    py = sys.executable
    temp_citylbm = Path(tempfile.gettempdir()) / "CityLBM"
    using_existing_case_dir = bool(args.case_dir.strip())
    if using_existing_case_dir:
        args.skip_build = True
        args.skip_codegen = True
    case_dir = Path(args.case_dir).expanduser().resolve() if using_existing_case_dir else temp_citylbm / args.case_name
    fake_source_name = DEFAULT_CASE_TO_FAKE_SOURCE[args.case_name]
    source_root = Path(args.fluidx3d_source).expanduser().resolve() if args.fluidx3d_source else temp_citylbm / fake_source_name
    solver_cwd = Path(args.solver_cwd).expanduser().resolve() if args.solver_cwd.strip() else None
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else case_dir / "preflight_codegen_canary"
    manifest_out = (
        Path(args.manifest_out).expanduser().resolve()
        if args.manifest_out
        else out_dir / "codegen_preflight_canary_manifest.json"
    )
    route_check_manifest = out_dir / "short_canary_route_check.json"
    preflight_manifest = out_dir / "native_preflight_pack_manifest.json"
    native_runner_manifest = out_dir / "native_fluidx3d_baseline_manifest.json"
    custom_profile_af_fidelity_manifest = out_dir / "custom_profile_af_fidelity_audit.json"
    custom_profile_af_fidelity_csv = out_dir / "custom_profile_af_fidelity_audit.csv"

    steps: List[Dict[str, Any]] = []
    require_build_or_codegen = not args.skip_build or not args.skip_codegen
    codegen_build_environment = audit_codegen_build_environment(repo, require_build_or_codegen)
    build_environment_allows_fresh_codegen = codegen_build_environment["Gate"] != "blocked"
    if not args.skip_build and build_environment_allows_fresh_codegen:
        steps.append(run_step("dotnet_build_release", ["dotnet", "build", "-c", "Release"], repo))
    if not args.skip_codegen and build_environment_allows_fresh_codegen:
        codegen_env: Dict[str, str] = {}
        if args.case_name == "casea_full_reynolds_stress_tensor" and args.af_csv:
            codegen_env["CITYLBM_CODEGEN_CASEA_AF_CSV"] = str(Path(args.af_csv).expanduser().resolve())
        if args.case_name == "casea_full_reynolds_stress_tensor":
            if args.time_steps is not None:
                codegen_env["CITYLBM_CODEGEN_CASEA_TIME_STEPS"] = str(args.time_steps)
            if args.vtk_save_interval is not None:
                codegen_env["CITYLBM_CODEGEN_CASEA_SAVE_INTERVAL"] = str(args.vtk_save_interval)
        codegen_project = repo / "tests" / "CodegenSmoke" / "CodegenSmoke.csproj"
        codegen_exe = repo / "tests" / "CodegenSmoke" / "bin" / "Release" / "net48" / "CodegenSmoke.exe"
        codegen_build_step = run_step(
            "dotnet_build_codegen_smoke",
            ["dotnet", "build", str(codegen_project), "-c", "Release"],
            repo,
        )
        steps.append(codegen_build_step)
        if codegen_exe.is_file():
            steps.append(run_step("run_codegen_smoke_exe", [str(codegen_exe)], repo, codegen_env or None))
        else:
            steps.append(
                run_step(
                    "dotnet_run_codegen_smoke",
                    [
                        "dotnet",
                        "run",
                        "--project",
                        str(codegen_project),
                        "-c",
                        "Release",
                    ],
                    repo,
                    codegen_env or None,
                )
            )

    fresh_codegen = fresh_codegen_case_gate(case_dir, not args.skip_codegen, started_at)

    if args.af_csv and fresh_codegen["Gate"] != "fail":
        steps.append(
            run_step(
                "audit_custom_profile_against_af",
                [
                    py,
                    str(repo / "scripts" / "audit_custom_profile_against_af.py"),
                    "--metadata",
                    str(case_dir / "case_metadata.json"),
                    "--af-csv",
                    str(Path(args.af_csv).expanduser().resolve()),
                    "--out-json",
                    str(custom_profile_af_fidelity_manifest),
                    "--out-csv",
                    str(custom_profile_af_fidelity_csv),
                    "--require-k",
                ],
                repo,
            )
        )
    custom_profile_af_fidelity = read_json(custom_profile_af_fidelity_manifest)
    custom_profile_af_fidelity_gate = gate_value(custom_profile_af_fidelity, "Gate")
    codegen_exe_run_passed = any(
        step.get("Name") == "run_codegen_smoke_exe" and int(step.get("ReturnCode", 1)) == 0 for step in steps
    )

    def step_failed_blocks_preflight(step: Dict[str, Any]) -> bool:
        name = str(step.get("Name", ""))
        if codegen_exe_run_passed and name in {"dotnet_build_codegen_smoke", "dotnet_run_codegen_smoke"}:
            return False
        return int(step.get("ReturnCode", 1)) != 0

    prerequisites_ok = case_dir.is_dir() and source_root.is_dir()
    route_check_allowed = prerequisites_ok and not any(step_failed_blocks_preflight(step) for step in steps) and (
        build_environment_allows_fresh_codegen or not require_build_or_codegen
    ) and fresh_codegen["Gate"] != "fail" and (not args.af_csv or custom_profile_af_fidelity_gate == "pass")
    if route_check_allowed:
        steps.append(
            run_step(
                "check_short_canary_route",
                [
                    py,
                    str(repo / "scripts" / "check_short_canary_route.py"),
                    "--case-dir",
                    str(case_dir),
                    "--out",
                    str(route_check_manifest),
                ],
                repo,
            )
        )
    route_check = read_json(route_check_manifest)
    route_check_gate = gate_value(route_check, "Gate")
    preflight_allowed = route_check_allowed and route_check_gate == "pass"
    if preflight_allowed:
        preflight_cmd = [
            py,
            str(repo / "scripts" / "run_native_preflight_pack.py"),
            "--case-dir",
            str(case_dir),
            "--fluidx3d-source",
            str(source_root),
            "--out-dir",
            str(out_dir),
            "--manifest-out",
            str(native_runner_manifest),
            "--expected-aij-case",
            args.expected_aij_case,
            "--expected-wind-direction",
            args.expected_wind_direction,
            "--expected-wind-vector",
            args.expected_wind_vector,
            "--patch-metadata-identity",
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
            "--diagnostic-canary-time-steps",
            str(args.time_steps),
            "--diagnostic-canary-vtk-save-interval",
            str(args.vtk_save_interval),
            "--diagnostic-canary-average-last-n",
            str(args.average_last_n),
            "--diagnostic-canary-min-vtk-frames",
            str(args.min_vtk_frames),
            "--diagnostic-canary-min-step-span",
            str(args.min_vtk_step_span),
            "--allow-diagnostic",
        ]
        optional(preflight_cmd, "--solver-cwd", str(solver_cwd) if solver_cwd else "")
        optional(preflight_cmd, "--official", args.official)
        optional(preflight_cmd, "--af-csv", args.af_csv)
        optional(preflight_cmd, "--official-condition-filter", args.official_condition_filter)
        optional(preflight_cmd, "--official-wind-filter", args.official_wind_filter)
        optional(preflight_cmd, "--length-scale-source", args.length_scale_source)
        optional(preflight_cmd, "--length-scale-source-type", args.length_scale_source_type)
        optional(preflight_cmd, "--length-scale-source-note", args.length_scale_source_note)
        optional(preflight_cmd, "--expected-probe-row-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
        optional(preflight_cmd, "--expected-probe-z", args.expected_probe_z)
        optional(preflight_cmd, "--expected-probe-z-min", args.expected_probe_z_min)
        optional(preflight_cmd, "--expected-probe-z-max", args.expected_probe_z_max)
        optional(preflight_cmd, "--z-ref", args.z_ref)
        optional(preflight_cmd, "--expected-uref", args.expected_uref)
        optional(preflight_cmd, "--vtk-save-start-step", args.vtk_save_start_step)
        optional(preflight_cmd, "--diagnostic-canary-spinup-steps", args.vtk_save_start_step)
        optional(preflight_cmd, "--diagnostic-canary-stg-update-interval", args.diagnostic_canary_stg_update_interval)
        optional(preflight_cmd, "--diagnostic-canary-stg-intensity-scale", args.diagnostic_canary_stg_intensity_scale)
        optional(
            preflight_cmd,
            "--diagnostic-canary-stg-temporal-step-scale",
            args.diagnostic_canary_stg_temporal_step_scale,
        )
        if args.require_af_k:
            preflight_cmd.append("--require-af-k")
        if args.length_scale_paper_admissible:
            preflight_cmd.append("--length-scale-paper-admissible")
        steps.append(run_step("run_native_preflight_pack", preflight_cmd, repo))

    preflight = read_json(preflight_manifest)
    diagnostic_canary = preflight.get("DiagnosticCanaryGate") if isinstance(preflight.get("DiagnosticCanaryGate"), dict) else {}
    actual_geometry = actual_validation_geometry_gate(case_dir, args.require_actual_geometry, args.expected_aij_case)
    reasons = [
        f"step_failed:{step['Name']}:{step['ReturnCode']}"
        for step in steps
        if step_failed_blocks_preflight(step)
    ]
    if codegen_build_environment["Gate"] == "blocked":
        reasons.append("codegen_build_environment_blocked")
        reasons.extend(f"codegen_build_environment:{reason}" for reason in codegen_build_environment["Reasons"])
    if not case_dir.is_dir():
        reasons.append("fresh_codegen_case_dir_missing")
    if fresh_codegen["Gate"] == "fail":
        reasons.append("fresh_codegen_case_not_current")
        reasons.extend(f"fresh_codegen_case:{reason}" for reason in fresh_codegen["Reasons"])
    if not source_root.is_dir():
        reasons.append("fluidx3d_source_dir_missing")
    if route_check_allowed and route_check_gate != "pass":
        reasons.append(f"short_canary_route_check_not_pass:{route_check_gate or 'missing'}")
        for reason in route_check.get("Reasons", []):
            reasons.append(f"short_canary_route_check:{reason}")
    if args.af_csv and custom_profile_af_fidelity_gate != "pass":
        reasons.append(f"custom_profile_af_fidelity_not_pass:{custom_profile_af_fidelity_gate or 'missing'}")
        for reason in custom_profile_af_fidelity.get("Reasons", []):
            reasons.append(f"custom_profile_af_fidelity:{reason}")
    if preflight_allowed and preflight_manifest.is_file() is False:
        reasons.append("preflight_manifest_missing")
    if actual_geometry["Required"] and actual_geometry["Gate"] != "pass":
        reasons.append(f"actual_validation_geometry_not_pass:{actual_geometry['Gate']}")
        for reason in actual_geometry["Reasons"]:
            reasons.append(f"actual_validation_geometry:{reason}")
    preflight_gate = gate_value(preflight, "Gate")
    canary_gate = gate_value(diagnostic_canary, "Gate")
    if preflight_gate and preflight_gate != "pass":
        reasons.append(f"paper_preflight_not_pass:{preflight_gate}")
    if canary_gate and canary_gate != "pass":
        reasons.append(f"diagnostic_canary_not_pass:{canary_gate}")
    reasons = list(dict.fromkeys(reasons))

    gate = "pass" if not reasons else "diagnostic_only"
    manifest = {
        "Schema": "citylbm.codegen_preflight_canary.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": (
            "accelerate_citylbm_optimization_by_reusing_existing_codegen_and_running_no_cfd_gates"
            if args.quick
            else "accelerate_citylbm_optimization_by_regenerating_current_codegen_and_running_no_cfd_gates"
        ),
        "RepoRoot": str(repo),
        "CaseName": args.case_name,
        "ExpectedAijCase": args.expected_aij_case,
        "ExpectedWindDirection": args.expected_wind_direction,
        "ExpectedWindVector": args.expected_wind_vector,
        "OfficialConditionFilter": args.official_condition_filter,
        "OfficialWindFilter": args.official_wind_filter,
        "LengthScaleSource": args.length_scale_source,
        "LengthScaleSourceType": args.length_scale_source_type,
        "LengthScaleSourceNote": args.length_scale_source_note,
        "LengthScalePaperAdmissible": bool(args.length_scale_paper_admissible),
        "ExpectedProbeRowCount": args.expected_probe_row_count,
        "ExpectedProbeZ": args.expected_probe_z,
        "ExpectedProbeZMin": args.expected_probe_z_min,
        "ExpectedProbeZMax": args.expected_probe_z_max,
        "ZRef": args.z_ref,
        "ExpectedURef": args.expected_uref,
        "CaseDir": str(case_dir),
        "ExternalCaseDir": bool(using_existing_case_dir),
        "FluidX3DSource": str(source_root),
        "OutDir": str(out_dir),
        "QuickMode": bool(args.quick),
        "SkippedBuild": bool(args.skip_build),
        "SkippedCodegen": bool(args.skip_codegen),
        "EvidenceFreshness": (
            "existing_explicit_case_dir_no_new_build_or_codegen"
            if using_existing_case_dir
            else (
            "reused_existing_temp_case_no_new_build_or_codegen"
            if args.quick
            else (
                "case_regenerated_without_build"
                if args.skip_build and not args.skip_codegen
                else (
                    "existing_case_reused_after_build"
                    if args.skip_codegen and not args.skip_build
                    else "fresh_build_and_codegen"
                )
            )
            )
        ),
        "Gate": gate,
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "DiagnosticCanaryGate": diagnostic_canary,
        "ShortCanaryRouteCheckGate": route_check_gate,
        "ShortCanaryRouteCheckManifest": str(route_check_manifest),
        "CustomProfileAfFidelityGate": custom_profile_af_fidelity_gate,
        "CustomProfileAfFidelityManifest": str(custom_profile_af_fidelity_manifest),
        "CodegenBuildEnvironmentGate": codegen_build_environment,
        "FreshCodegenCaseGate": fresh_codegen,
        "ActualValidationGeometryGate": actual_geometry,
        "PreflightGate": preflight_gate,
        "NativePreflightPackManifest": str(preflight_manifest),
        "NativeRunnerManifest": str(native_runner_manifest),
        "FreshCaseFiles": {
            "setup_cpp": path_summary(case_dir / "setup.cpp"),
            "defines_hpp": path_summary(case_dir / "defines.hpp"),
            "case_metadata_json": path_summary(case_dir / "case_metadata.json"),
            "buildings_stl": path_summary(case_dir / "buildings.stl"),
        },
        "Steps": steps,
        "NextAction": (
            "Start a short native FluidX3D canary run under the same generated case and source hashes."
            if gate == "pass"
            else "Do not spend time on a long CFD run yet; fix the listed gate reasons first."
        ),
    }
    write_json(manifest_out, manifest)
    print(f"codegen_preflight_canary_gate={gate}; manifest={manifest_out}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate == "pass" or args.allow_diagnostic else 2


if __name__ == "__main__":
    raise SystemExit(main())
