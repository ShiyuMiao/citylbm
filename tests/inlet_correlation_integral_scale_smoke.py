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

    persistent_spatial_frames = [
        {0: (-1.0, 0.0, 0.0), 1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0)}
        for _ in range(3)
    ]
    spatial_streamwise_var, spatial_component_vars, spatial_tke = module.spatial_energy_metrics(
        persistent_spatial_frames,
        [0, 1, 2],
        (1, 1, 3),
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        {},
        (1.0, 0.0, 0.0),
        [{"z": 0.0, "u": 0.0}, {"z": 2.0, "u": 0.0}],
    )
    if spatial_streamwise_var is None or abs(spatial_streamwise_var - (2.0 / 3.0)) > 1.0e-12:
        raise AssertionError(spatial_streamwise_var)
    if spatial_component_vars[0] is None or abs(spatial_component_vars[0] - (2.0 / 3.0)) > 1.0e-12:
        raise AssertionError(spatial_component_vars)
    if spatial_tke is None or abs(spatial_tke - (1.0 / 3.0)) > 1.0e-12:
        raise AssertionError(spatial_tke)

    inlet_plane_indices = [0 + 4 * y + 16 * z for z in range(4) for y in range(4)]
    sampled_plane = module.select_deterministic_subset(inlet_plane_indices, 6)
    sampled_pairs = module.adjacent_pairs(sampled_plane, (4, 4, 4), "x")
    if not sampled_pairs:
        raise AssertionError(sampled_plane)

    full_x_plane = [0 + 4 * y + 40 * z for z in range(20) for y in range(10)]
    balanced_plane = module.select_balanced_plane_subset(full_x_plane, 50, (4, 10, 20), "x")
    balanced_z_values = sorted({idx // (4 * 10) for idx in balanced_plane})
    if min(balanced_z_values) != 0 or max(balanced_z_values) != 19:
        raise AssertionError(balanced_z_values)
    if not module.adjacent_pairs(balanced_plane, (4, 10, 20), "x"):
        raise AssertionError(balanced_plane)

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

    tke_target, tke_count = module.tke_target_from_af_k(
        samples,
        [0, 1, 2],
        (1, 1, 3),
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
    )
    if tke_count != 3:
        raise AssertionError(tke_count)
    if tke_target is None or abs(tke_target - 0.9) > 1.0e-12:
        raise AssertionError(tke_target)

    mapped_target, mapped_count = module.streamwise_variance_target_from_af_k(
        [
            {"z": -3.0, "u": 1.0, "k": 0.3},
            {"z": -1.0, "u": 1.0, "k": 0.6},
            {"z": 1.0, "u": 1.0, "k": 0.9},
        ],
        [0, 1, 2],
        (1, 1, 3),
        (-1.0, -1.0, -1.0),
        (1.0, 1.0, 1.0),
        {"ProfileOriginZM": -4.0, "DxM": 2.0},
    )
    if mapped_count != 3:
        raise AssertionError(mapped_count)
    # Cell indices 0,1,2 map to z=-3,-1,1 m, not to the centered VTK
    # coordinates -1,0,1. This guards FluidX3D VTK lattice-coordinate output.
    if mapped_target is None or abs(mapped_target - 0.4) > 1.0e-12:
        raise AssertionError(mapped_target)

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

    selected_variance, variance_source = module.select_k_variance_gate_input(0.66, 9.9)
    if selected_variance != 0.66 or variance_source != "fixed_point_temporal_streamwise_variance":
        raise AssertionError((selected_variance, variance_source))
    selected_variance, variance_source = module.select_k_variance_gate_input(None, 0.66)
    if selected_variance != 0.66 or variance_source != "per_frame_inlet_plane_spatial_variance":
        raise AssertionError((selected_variance, variance_source))

    gate, reasons, ratio = module.tke_gate(
        actual_tke=0.99,
        target_k=tke_target,
        min_ratio=0.5,
        max_ratio=1.5,
        require_check=True,
        af_csv_supplied=True,
    )
    if gate != module.PASS or abs(ratio - 1.1) > 1.0e-12:
        raise AssertionError((gate, reasons, ratio))

    gate, reasons, ratio = module.tke_gate(
        actual_tke=0.2,
        target_k=tke_target,
        min_ratio=0.5,
        max_ratio=1.5,
        require_check=True,
        af_csv_supplied=True,
    )
    if gate != module.FAIL or "tke_to_k_ratio_below_0.5" not in reasons or ratio is None:
        raise AssertionError((gate, reasons, ratio))

    gate, reasons = module.turbulence_target_source_gate(
        "af_csv_isotropic_k",
        k_target_count=3,
        tke_target_count=3,
        require_check=True,
    )
    if gate != module.PASS or reasons != ["af_csv_isotropic_k"]:
        raise AssertionError((gate, reasons))

    gate, reasons = module.turbulence_target_source_gate(
        "metadata_full_tensor_active_target",
        k_target_count=3,
        tke_target_count=3,
        require_check=True,
    )
    if gate != module.PASS or reasons != ["metadata_full_tensor_active_target"]:
        raise AssertionError((gate, reasons))

    gate, reasons = module.turbulence_target_source_gate(
        "not_checked",
        k_target_count=0,
        tke_target_count=0,
        require_check=True,
    )
    if gate != module.FAIL or "inlet_turbulence_target_source_missing" not in reasons:
        raise AssertionError((gate, reasons))

    gate, reasons = module.turbulence_target_source_gate(
        "not_checked",
        k_target_count=0,
        tke_target_count=0,
        require_check=False,
    )
    if gate != "not_checked" or "inlet_turbulence_target_source_missing" not in reasons:
        raise AssertionError((gate, reasons))

    print("inlet_correlation_integral_scale_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
