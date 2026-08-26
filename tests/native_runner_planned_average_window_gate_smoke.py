"""Smoke-test planned averaging window gate in the native runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_native_fluidx3d_case", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import runner: {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    short_average = runner.audit_planned_vtk_schedule(
        time_steps=400000,
        save_interval=10000,
        save_start_step=None,
        expected_frame_count=40,
        average_last_n=4,
        min_frames=40,
        min_step_span=20000,
    )
    if short_average["Gate"] != "diagnostic_only":
        raise AssertionError(short_average)
    if short_average["ComputedFrameCount"] != 40:
        raise AssertionError(short_average)
    if short_average["FinalWindowStepSpan"] != 30000:
        raise AssertionError(short_average)
    if "average_last_n_4_below_minimum_40" not in short_average["Reasons"]:
        raise AssertionError(short_average)

    passing = runner.audit_planned_vtk_schedule(
        time_steps=400000,
        save_interval=10000,
        save_start_step=None,
        expected_frame_count=40,
        average_last_n=40,
        min_frames=40,
        min_step_span=20000,
    )
    if passing["Gate"] != "pass":
        raise AssertionError(passing)

    print("native_runner_planned_average_window_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
