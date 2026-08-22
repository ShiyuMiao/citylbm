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

    samples = [
        {"z": 0.0, "u": 1.0, "k": 0.6},
        {"z": 2.0, "u": 1.0, "k": 1.2},
    ]
    target, count = module.streamwise_variance_target_from_af_k(
        samples,
        [0, 1, 2],
        (1, 1, 3),
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
    )
    if count != 3:
        raise AssertionError(count)
    # z=0,1,2 gives k=0.6,0.9,1.2, so isotropic streamwise variance is
    # mean(2k/3)=0.6.
    if target is None or abs(target - 0.6) > 1.0e-12:
        raise AssertionError(target)

    gate, reasons, ratio = module.k_variance_gate(
        actual_variance=0.66,
        target_variance=target,
        min_ratio=0.5,
        max_ratio=1.5,
        require_check=True,
        af_csv_supplied=True,
    )
    if gate != module.PASS or abs(ratio - 1.1) > 1.0e-12:
        raise AssertionError((gate, reasons, ratio))

    gate, reasons, ratio = module.k_variance_gate(
        actual_variance=0.1,
        target_variance=target,
        min_ratio=0.5,
        max_ratio=1.5,
        require_check=True,
        af_csv_supplied=True,
    )
    if gate != module.FAIL or "k_variance_ratio_below_0.5" not in reasons or ratio is None:
        raise AssertionError((gate, reasons, ratio))

    print("inlet_correlation_integral_scale_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
