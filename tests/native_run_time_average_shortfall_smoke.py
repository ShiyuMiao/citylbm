#!/usr/bin/env python3
"""Smoke-test native FluidX3D final-window averaging shortfall reporting."""

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

    print("native_run_time_average_shortfall_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
