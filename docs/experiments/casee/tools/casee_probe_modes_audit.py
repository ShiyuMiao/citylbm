#!/usr/bin/env python3
"""Audit the native Case E probe-mode diagnostic runner without claiming accuracy."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PMODES_CASE_DIR = CASE_DIR / "native_cases" / "casee_native_dx2_yn_sgs_gshift1_nu0p001_pmodes_steps48000_spin12000"


REQUIRED_SETUP_MARKERS = [
    "sample_u_raw_trilinear",
    "sample_u_nearest_valid",
    "sample_u_fluid_weighted",
    "sample_u_vertical_valid_above",
    "z_plus_half_velocity_ratio",
    "nearest_valid_velocity_ratio",
    "fluid_weighted_velocity_ratio",
    "vertical_valid_above_velocity_ratio",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def file_status(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        return {"found": False, "path": "", "sha256": "", "size_bytes": 0, "mtime_utc": ""}
    actual = path if path.is_absolute() else ROOT / path
    if not actual.exists():
        return {"found": False, "path": display_path(actual), "sha256": "", "size_bytes": 0, "mtime_utc": ""}
    return {
        "found": True,
        "path": display_path(actual),
        "sha256": sha256(actual),
        "size_bytes": actual.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(actual.stat().st_mtime, timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, default=PMODES_CASE_DIR)
    parser.add_argument("--compile-log", type=Path, default=RESULTS_DIR / "fluidx3d_dx2_pmodes_compile.log")
    parser.add_argument("--run-log", type=Path)
    parser.add_argument("--probe-csv", type=Path)
    parser.add_argument("--fluidx3d-exe", type=Path, default=Path(r"E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe"))
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_probe_modes_compile_manifest.json")
    args = parser.parse_args()

    setup_path = args.case_dir / "setup.cpp"
    manifest_path = args.case_dir / "citylbm_native_case_manifest.json"
    setup_text = setup_path.read_text(encoding="utf-8") if setup_path.exists() else ""
    marker_status = {marker: (marker in setup_text) for marker in REQUIRED_SETUP_MARKERS}

    setup_info = file_status(setup_path)
    manifest_info = file_status(manifest_path)
    compile_log_info = file_status(args.compile_log)
    run_log_info = file_status(args.run_log)
    probe_csv_info = file_status(args.probe_csv)
    exe_info = file_status(args.fluidx3d_exe)

    exe_after_setup = False
    if setup_path.exists() and args.fluidx3d_exe.exists():
        exe_after_setup = args.fluidx3d_exe.stat().st_mtime >= setup_path.stat().st_mtime

    passed = (
        setup_info["found"]
        and manifest_info["found"]
        and compile_log_info["found"]
        and exe_info["found"]
        and exe_after_setup
        and all(marker_status.values())
    )
    run_text = args.run_log.read_text(encoding="utf-8", errors="ignore") if args.run_log and args.run_log.exists() else ""
    full_run_completed = "CaseE step 48000 / 48000" in run_text and bool(probe_csv_info["found"])
    status = "passed_full_run" if passed and full_run_completed else ("passed_compile_only" if passed else "blocked")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "evidence_type": "newly_run" if passed else "blocked",
        "claim_readiness": "diagnostic_metrics_available" if full_run_completed else ("compile_only_no_accuracy_metric" if passed else "blocked_probe_modes_compile_audit"),
        "case_dir": display_path(args.case_dir),
        "setup": setup_info,
        "case_manifest": manifest_info,
        "compile_log": compile_log_info,
        "run_log": run_log_info,
        "probe_csv": probe_csv_info,
        "fluidx3d_executable": exe_info,
        "executable_mtime_after_setup": exe_after_setup,
        "full_run_completed": full_run_completed,
        "required_setup_markers": marker_status,
        "blocking_reason": "" if passed else "Probe-mode runner requires generated setup, manifest, compile log, executable, and all diagnostic output markers.",
        "accuracy_boundary": "Diagnostic probe-mode metrics are limitations evidence; formal release still uses raw_trilinear official z=2 m metrics.",
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
