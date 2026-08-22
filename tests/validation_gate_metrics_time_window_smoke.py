#!/usr/bin/env python3
"""Smoke-test metrics/read-VTK time-window consistency gating."""

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
    runtime_audit = {
        "time_averaging_gate": "pass",
        "source_time_steps": ",".join(str(step) for step in range(1000, 41000, 1000)),
        "source_step_span": 39000,
        "available_frame_count": 40,
        "minimum_validation_average_step_span": 20000,
    }
    stale_metrics = {
        "time_averaging_gate": "diagnostic_only",
        "source_time_steps": "37000,38000,39000,40000",
        "source_step_span": 3000,
        "averaged_frame_count": 4,
        "available_frame_count": 40,
        "minimum_validation_average_step_span": 20000,
    }

    failed = module.metrics_time_averaging_consistency_status(
        stale_metrics,
        runtime_audit,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if failed["ok"]:
        raise AssertionError(failed)
    reasons = failed["reasons_csv"]
    for expected in (
        "metrics_time_averaging_gate_not_pass:diagnostic_only",
        "metrics_averaged_frame_count_below_40",
        "metrics_source_step_span_below_20000",
        "metrics_source_time_steps_do_not_match_runtime_audit",
    ):
        if expected not in reasons:
            raise AssertionError((expected, reasons))

    aligned_metrics = dict(stale_metrics)
    aligned_metrics.update(
        {
            "time_averaging_gate": "pass",
            "source_time_steps": runtime_audit["source_time_steps"],
            "source_step_span": runtime_audit["source_step_span"],
            "averaged_frame_count": 40,
        }
    )
    passed = module.metrics_time_averaging_consistency_status(
        aligned_metrics,
        runtime_audit,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if not passed["ok"]:
        raise AssertionError(passed)

    print("validation_gate_metrics_time_window_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
