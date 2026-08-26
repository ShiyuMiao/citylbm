#!/usr/bin/env python3
"""Smoke-test native runner VTK disk-space preflight gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
RUNNER_SMOKE = REPO / "tests" / "native_fluidx3d_runner_smoke.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_native_fluidx3d_case", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import runner: {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner_smoke():
    spec = importlib.util.spec_from_file_location("native_fluidx3d_runner_smoke", RUNNER_SMOKE)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import runner smoke helpers: {RUNNER_SMOKE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cmd(args: list[str], expected_returncode: int) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def main() -> int:
    runner = load_runner()
    runner_smoke = load_runner_smoke()
    with tempfile.TemporaryDirectory(prefix="citylbm_disk_gate_") as raw:
        temp = Path(raw)
        defines = temp / "defines.hpp"
        defines.write_text("#define SX 547u\n#define SY 280u\n#define SZ 160u\n", encoding="utf-8")

        dimensions = runner.parse_grid_dimensions_from_defines(defines)
        if dimensions != (547, 280, 160):
            raise AssertionError(dimensions)

        estimate = runner.planned_vtk_bytes_for_grid(dimensions, 51)
        if estimate["EstimatedRequiredBytes"] <= 15_000_000_000:
            raise AssertionError(estimate)

        blocked = runner.audit_output_disk_space(
            temp / "output",
            dimensions,
            51,
            require_for_run=True,
            free_bytes_override=12_472_320,
        )
        if blocked["Gate"] != "blocked":
            raise AssertionError(blocked)
        if "below_estimated_vtk_bytes" not in blocked["ReasonsCsv"]:
            raise AssertionError(blocked)

        not_applicable = runner.audit_output_disk_space(
            temp / "output",
            dimensions,
            51,
            require_for_run=False,
            free_bytes_override=12_472_320,
        )
        if not_applicable["Gate"] != "not_applicable":
            raise AssertionError(not_applicable)

        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        runner_smoke.create_source(source_root)
        runner_smoke.create_case(case_dir)
        (case_dir / "src" / "defines.hpp").write_text(
            "#define SX 100000u\n#define SY 100000u\n#define SZ 1000u\n",
            encoding="utf-8",
        )
        manifest_path = temp / "disk_block_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(manifest_path),
                "--baseline-id",
                "smoke-disk-block",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--allow-diagnostic-execution",
                "--run",
            ],
            expected_returncode=2,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["OutputDiskSpaceGate"]["Gate"] != "blocked":
            raise AssertionError(manifest["OutputDiskSpaceGate"])
        if manifest["Run"]["Gate"] != "blocked":
            raise AssertionError(manifest["Run"])
        reasons_csv = manifest["RunnerGate"]["ReasonsCsv"]
        if "execution_requested_but_output_disk_space_blocked" not in reasons_csv:
            raise AssertionError(manifest["RunnerGate"])
        if "execution_requested_but_preflight_gate_diagnostic_only" in reasons_csv:
            raise AssertionError(manifest["RunnerGate"])

    print("native_runner_disk_space_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
