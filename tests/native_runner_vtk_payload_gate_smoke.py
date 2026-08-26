#!/usr/bin/env python3
"""Smoke-test native runner VTK payload completeness gate."""

from __future__ import annotations

import importlib.util
import struct
import tempfile
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


def vtk_header(step: int) -> bytes:
    return (
        "# vtk DataFile Version 3.0\n"
        f"FluidX3D u-{step:09d}.vtk\n"
        "BINARY\n"
        "DATASET STRUCTURED_POINTS\n"
        "DIMENSIONS 1 1 1\n"
        "ORIGIN 0 0 0\n"
        "SPACING 1 1 1\n"
        "POINT_DATA 1\n"
        "SCALARS data float 3\n"
        "LOOKUP_TABLE default\n"
    ).encode("ascii")


def main() -> int:
    runner = load_runner()
    with tempfile.TemporaryDirectory(prefix="citylbm_vtk_payload_") as raw:
        output = Path(raw)
        (output / "u-000001000.vtk").write_bytes(vtk_header(1000) + struct.pack(">fff", 1.0, 0.0, 0.0))
        (output / "u-000002000.vtk").write_bytes(vtk_header(2000))

        records = runner.collect_vtk_files(output, "u-*.vtk")
        result = runner.audit_actual_vtk_output(
            records,
            expected_frame_count=2,
            expected_steps=[1000, 2000],
            average_last_n=2,
            min_frames=2,
            min_step_span=1000,
            require_actual_output=True,
        )
        if result["Gate"] != "diagnostic_only":
            raise AssertionError(result)
        if result["VtkPayloadIncompleteTimeSteps"] != [2000]:
            raise AssertionError(result)
        if result["SelectedFinalWindowPayloadIncompleteTimeSteps"] != [2000]:
            raise AssertionError(result)
        for reason in [
            "actual_vtk_payload_incomplete_count_1",
            "actual_vtk_final_window_payload_incomplete_count_1",
        ]:
            if reason not in result["Reasons"]:
                raise AssertionError(result)

    print("native_runner_vtk_payload_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
