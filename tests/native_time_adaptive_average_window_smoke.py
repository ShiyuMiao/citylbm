#!/usr/bin/env python3
"""Smoke-test adaptive average-window recommendations for native run audits."""

from __future__ import annotations

import importlib.util
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


def main() -> int:
    module = load_native_run_module()
    preflight = module.expected_vtk_frame_preflight(
        metadata={},
        time_steps=40000,
        save_interval=100,
        save_start_step=100,
        average_last_n=40,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if preflight["requested_vtk_frame_count"] != 400:
        raise AssertionError(preflight)
    if preflight["requested_vtk_expected_final_window_step_span"] != 3900:
        raise AssertionError(preflight)
    if preflight["recommended_average_last_n_for_step_span"] != 201:
        raise AssertionError(preflight)
    if preflight["recommended_minimum_time_steps_for_current_save_interval"] != 20100:
        raise AssertionError(preflight)
    if preflight["requested_vtk_frame_gate"] != "diagnostic_only":
        raise AssertionError(preflight)
    if "requested_vtk_expected_final_window_step_span_below_20000" not in preflight["requested_vtk_frame_gate_reasons_csv"]:
        raise AssertionError(preflight)

    passing = module.expected_vtk_frame_preflight(
        metadata={},
        time_steps=40000,
        save_interval=100,
        save_start_step=100,
        average_last_n=201,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if passing["requested_vtk_frame_gate"] != "pass":
        raise AssertionError(passing)
    if passing["requested_vtk_expected_final_window_step_span"] != 20000:
        raise AssertionError(passing)

    print("native_time_adaptive_average_window_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
