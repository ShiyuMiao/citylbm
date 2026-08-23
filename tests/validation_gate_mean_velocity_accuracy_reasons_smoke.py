#!/usr/bin/env python3
"""Smoke-test mean-velocity accuracy reasons beyond R2."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_gate_module():
    path = REPO / "scripts" / "validation_gate.py"
    spec = importlib.util.spec_from_file_location("validation_gate", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_gate_module()
    reasons = module.mean_velocity_accuracy_failure_reasons(
        u_bias=-0.34,
        u_rmse=0.42,
        u_r2=0.96,
        slope=0.55,
        intercept=0.28,
        max_u_bias_ratio=0.15,
        max_u_rmse_ratio=0.30,
        min_u_r2=0.70,
        min_slope=0.70,
        max_slope=1.30,
        max_intercept_abs=0.20,
    )
    expected = [
        "U_bias_ratio_abs_above_0.15:-0.34",
        "U_RMSE_ratio_above_0.3:0.42",
        "U_regression_slope_outside_0.7_1.3:0.55",
        "U_regression_intercept_abs_above_0.2:0.28",
    ]
    if reasons != expected:
        raise AssertionError(reasons)
    if any("U_R2" in reason for reason in reasons):
        raise AssertionError("High R2 should not mask other failed accuracy criteria.")

    missing = module.mean_velocity_accuracy_failure_reasons(
        u_bias=None,
        u_rmse=None,
        u_r2=None,
        slope=None,
        intercept=None,
        max_u_bias_ratio=0.15,
        max_u_rmse_ratio=0.30,
        min_u_r2=0.70,
        min_slope=0.70,
        max_slope=1.30,
        max_intercept_abs=0.20,
    )
    for expected_missing in (
        "U_bias_ratio_missing",
        "U_RMSE_ratio_missing",
        "U_R2_missing",
        "U_regression_slope_missing",
        "U_regression_intercept_missing",
    ):
        if expected_missing not in missing:
            raise AssertionError((expected_missing, missing))

    print("validation_gate_mean_velocity_accuracy_reasons_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
