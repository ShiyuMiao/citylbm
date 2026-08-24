#!/usr/bin/env python3
"""Smoke-test native FluidX3D final-window averaging shortfall reporting."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_native_run_module():
    path = REPO / "scripts" / "audit_native_run.py"
    spec = importlib.util.spec_from_file_location("audit_native_run", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_vtk(path: Path, speed: float) -> None:
    nx, ny, nz = 2, 2, 2
    payload = "\n".join(f"{speed:.6f} 0.000000 0.000000" for _ in range(nx * ny * nz))
    path.write_text(
        "\n".join(
            [
                "# vtk DataFile Version 3.0",
                "CityLBM native run stationarity smoke",
                "ASCII",
                "DATASET STRUCTURED_POINTS",
                f"DIMENSIONS {nx} {ny} {nz}",
                "ORIGIN 0 0 0",
                "SPACING 1 1 1",
                f"POINT_DATA {nx * ny * nz}",
                "VECTORS velocity float",
                payload,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    module = load_native_run_module()
    preflight = module.expected_vtk_frame_preflight(
        metadata={},
        time_steps=4000,
        save_interval=1000,
        save_start_step=1000,
        average_last_n=4,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if preflight["requested_vtk_frame_count"] != 4:
        raise AssertionError(preflight)
    if preflight["requested_vtk_frame_shortfall"] != 36:
        raise AssertionError(preflight)
    if preflight["requested_vtk_averaging_window_shortfall"] != 36:
        raise AssertionError(preflight)
    if preflight["requested_vtk_expected_final_window_step_span"] != 3000:
        raise AssertionError(preflight)
    if preflight["requested_vtk_expected_final_window_step_span_shortfall"] != 17000:
        raise AssertionError(preflight)
    reasons = ";".join(preflight["requested_vtk_frame_gate_reasons"])
    for expected in (
        "requested_vtk_frame_count_below_40",
        "requested_averaging_window_below_40",
        "requested_vtk_expected_final_window_step_span_below_20000",
    ):
        if expected not in reasons:
            raise AssertionError(preflight)

    with tempfile.TemporaryDirectory(prefix="citylbm_native_run_stationarity_") as tmp:
        tmp_dir = Path(tmp)
        steady = []
        drifting = []
        for index, speed in enumerate([1.0, 1.0, 1.0, 1.0], start=1):
            path = tmp_dir / f"steady-{index}.vtk"
            write_vtk(path, speed)
            steady.append(path)
        for index, speed in enumerate([1.0, 1.0, 2.0, 2.0], start=1):
            path = tmp_dir / f"drift-{index}.vtk"
            write_vtk(path, speed)
            drifting.append(path)

        steady_stats = module.compute_sampled_vtk_stability(steady, sample_limit=100)
        if steady_stats["final_window_mean_speed_drift_ratio"] != 0.0:
            raise AssertionError(steady_stats)
        drifting_stats = module.compute_sampled_vtk_stability(drifting, sample_limit=100)
        if drifting_stats["final_window_mean_speed_drift_ratio"] <= 0.03:
            raise AssertionError(drifting_stats)

        run_dir = tmp_dir / "native_run"
        run_dir.mkdir()
        metadata = run_dir / "case_metadata.json"
        metadata.write_text(
            json.dumps(
                {
                    "TimeSteps": 4000,
                    "SaveInterval": 1000,
                    "ExpectedVtkFrameCount": 4,
                }
            ),
            encoding="utf-8",
        )
        for step in [1000, 2000, 3000, 4000]:
            write_vtk(run_dir / f"u-{step:010d}.vtk", 1.0)
        out_json = tmp_dir / "native_run_audit.json"
        script = REPO / "scripts" / "audit_native_run.py"
        default_result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(run_dir),
                "--metadata",
                str(metadata),
                "--out",
                str(out_json),
                "--average-last-n",
                "4",
                "--time-steps",
                "4000",
                "--vtk-save-interval",
                "1000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if default_result.returncode != 0:
            raise AssertionError(default_result.stderr or default_result.stdout)
        default_audit = json.loads(out_json.read_text(encoding="utf-8"))
        if default_audit["strict_native_run_gate"] != "fail":
            raise AssertionError(default_audit)
        if "time_averaging_gate_not_pass" not in default_audit["strict_native_run_gate_reasons_csv"]:
            raise AssertionError(default_audit)
        strict_result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(run_dir),
                "--metadata",
                str(metadata),
                "--out",
                str(out_json),
                "--average-last-n",
                "4",
                "--time-steps",
                "4000",
                "--vtk-save-interval",
                "1000",
                "--strict",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if strict_result.returncode != 2:
            raise AssertionError(strict_result.stderr or strict_result.stdout)

        mismatch_dir = tmp_dir / "native_run_mismatched_final_window"
        mismatch_dir.mkdir()
        mismatch_metadata = mismatch_dir / "case_metadata.json"
        mismatch_metadata.write_text(
            json.dumps(
                {
                    "TimeSteps": 80000,
                    "SaveInterval": 1000,
                    "ExpectedVtkFrameCount": 80,
                }
            ),
            encoding="utf-8",
        )
        for step in range(1000, 41000, 1000):
            write_vtk(mismatch_dir / f"u-{step:010d}.vtk", 1.0)
        mismatch_out = tmp_dir / "native_run_mismatched_final_window_audit.json"
        mismatch_result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(mismatch_dir),
                "--metadata",
                str(mismatch_metadata),
                "--out",
                str(mismatch_out),
                "--average-last-n",
                "40",
                "--min-avg-frames",
                "40",
                "--min-avg-step-span",
                "20000",
                "--time-steps",
                "80000",
                "--vtk-save-interval",
                "1000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if mismatch_result.returncode != 0:
            raise AssertionError(mismatch_result.stderr or mismatch_result.stdout)
        mismatch_audit = json.loads(mismatch_out.read_text(encoding="utf-8"))
        if mismatch_audit["requested_vtk_frame_gate"] != "pass":
            raise AssertionError(mismatch_audit)
        if mismatch_audit["time_averaging_gate"] != "diagnostic_only":
            raise AssertionError(mismatch_audit)
        if mismatch_audit["actual_final_window_match_gate"] != "diagnostic_only":
            raise AssertionError(mismatch_audit)
        if mismatch_audit["actual_final_window_matches_requested"] is not False:
            raise AssertionError(mismatch_audit)
        if mismatch_audit["requested_vtk_expected_final_window_time_steps"][0] != 41000:
            raise AssertionError(mismatch_audit)
        if mismatch_audit["source_time_steps"][0] != 1000:
            raise AssertionError(mismatch_audit)
        if "actual_final_window_time_steps_mismatch_requested" not in mismatch_audit["time_averaging_gate_reasons_csv"]:
            raise AssertionError(mismatch_audit)

    print("native_run_time_average_shortfall_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
