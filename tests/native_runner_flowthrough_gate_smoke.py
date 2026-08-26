#!/usr/bin/env python3
"""Smoke-test planned domain flow-through gate in the native runner."""

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
    metadata = {
        "WindDirectionUnitVector": [0.0, -1.0, 0.0],
        "ReferenceWindSpeedMps": 4.0,
        "VelocityScaleMpsToLbm": 0.02,
    }

    short_run = runner.audit_planned_flow_through_time(
        metadata,
        grid_dimensions=(100, 250, 50),
        time_steps=9000,
        minimum_flow_throughs=3.0,
    )
    if short_run["Gate"] != "diagnostic_only":
        raise AssertionError(short_run)
    if short_run["DominantAxis"] != "y":
        raise AssertionError(short_run)
    if short_run["EstimatedOneFlowThroughSteps"] != 3125:
        raise AssertionError(short_run)
    if short_run["RecommendedMinimumTimeStepsForFlowThrough"] != 9375:
        raise AssertionError(short_run)
    if "planned_time_steps_9000_below_minimum_flowthrough_steps_9375" not in short_run["Reasons"]:
        raise AssertionError(short_run)

    passing = runner.audit_planned_flow_through_time(
        metadata,
        grid_dimensions=(100, 250, 50),
        time_steps=10000,
        minimum_flow_throughs=3.0,
    )
    if passing["Gate"] != "pass":
        raise AssertionError(passing)
    if abs(passing["PlannedFlowThroughCount"] - 3.2) > 1.0e-12:
        raise AssertionError(passing)

    missing_vector = runner.audit_planned_flow_through_time(
        {"ReferenceWindSpeedMps": 4.0, "VelocityScaleMpsToLbm": 0.02},
        grid_dimensions=(100, 250, 50),
        time_steps=10000,
        minimum_flow_throughs=3.0,
    )
    if missing_vector["Gate"] != "diagnostic_only":
        raise AssertionError(missing_vector)
    if "flow_through_wind_vector_missing_using_max_dimension" not in missing_vector["Reasons"]:
        raise AssertionError(missing_vector)

    print("native_runner_flowthrough_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
