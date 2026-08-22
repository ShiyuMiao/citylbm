#!/usr/bin/env python3
"""Smoke-test inlet correlation integral-lag helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module():
    scripts_dir = REPO / "scripts"
    sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "audit_inlet_correlation_from_vtk.py"
    spec = importlib.util.spec_from_file_location("audit_inlet_correlation_from_vtk", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()

    alternating = {0: [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]}
    alternating_lags = module.temporal_lag_correlations(alternating, 3)
    if module.positive_integral_lag_count(alternating_lags) != 0:
        raise AssertionError(alternating_lags)

    persistent = {
        0: [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        1: [0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
    }
    persistent_lags = module.temporal_lag_correlations(persistent, 3)
    if module.positive_integral_lag_count(persistent_lags) != 3:
        raise AssertionError(persistent_lags)

    selected = list(range(16))
    streamwise_series = {
        idx: [float(t + idx * 0.1) for t in range(6)]
        for idx in selected
    }
    spatial_lags, pair_counts = module.spatial_lag_correlations(
        streamwise_series,
        selected,
        (4, 4, 1),
        "z",
        3,
    )
    if not all(count > 0 for count in pair_counts[:3]):
        raise AssertionError(pair_counts)
    if module.positive_integral_lag_count(spatial_lags) != 3:
        raise AssertionError(spatial_lags)

    print("inlet_correlation_integral_scale_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
