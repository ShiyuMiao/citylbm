#!/usr/bin/env python3
"""Smoke-test native FluidX3D final-window averaging shortfall reporting."""

from __future__ import annotations

import importlib.util
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

    print("native_run_time_average_shortfall_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
