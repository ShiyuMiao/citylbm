#!/usr/bin/env python3
"""Smoke-test fast VTK time-averaging evidence generation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from native_fluidx3d_runner_smoke import load_json  # noqa: E402


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_time_averaging_evidence.py"


def run_case(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO),
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_time_average_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        case_dir.mkdir()

        passing_out = temp / "passing.json"
        passing = run_case(
            [
                "--case-dir",
                str(case_dir),
                "--out",
                str(passing_out),
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--average-last-n",
                "40",
                "--min-vtk-frames",
                "40",
                "--min-vtk-step-span",
                "20000",
            ]
        )
        if passing.returncode != 0:
            raise AssertionError((passing.returncode, passing.stdout, passing.stderr))
        passing_data = load_json(passing_out)
        if passing_data["Gate"] != "pass":
            raise AssertionError(passing_data)
        if passing_data["ActualVtkOutputGate"]["Gate"] != "not_applicable":
            raise AssertionError(passing_data["ActualVtkOutputGate"])
        if passing_data["PlannedSelectedFinalWindowSteps"][0] != 1000:
            raise AssertionError(passing_data["PlannedSelectedFinalWindowSteps"])
        if passing_data["PlannedSelectedFinalWindowSteps"][-1] != 40000:
            raise AssertionError(passing_data["PlannedSelectedFinalWindowSteps"])
        if passing_data["development_acceleration_stage"] != "eligible_for_short_native_canary":
            raise AssertionError(passing_data)
        if passing_data["development_acceleration_runs_cfd_next"] is not True:
            raise AssertionError(passing_data)
        if passing_data["long_cfd_allowed_by_time_averaging_evidence"] is not True:
            raise AssertionError(passing_data)

        short_out = temp / "short.json"
        short = run_case(
            [
                "--case-dir",
                str(case_dir),
                "--out",
                str(short_out),
                "--time-steps",
                "5000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--average-last-n",
                "4",
                "--min-vtk-frames",
                "40",
                "--min-vtk-step-span",
                "20000",
            ]
        )
        if short.returncode != 0:
            raise AssertionError((short.returncode, short.stdout, short.stderr))
        short_data = load_json(short_out)
        if short_data["Gate"] != "diagnostic_only":
            raise AssertionError(short_data)
        reasons = short_data["Reasons"]
        for expected in [
            "planned_vtk_schedule:planned_vtk_frame_count_5_below_minimum_40",
            "planned_vtk_schedule:expected_vtk_frame_count_40_does_not_match_computed_5",
            "planned_vtk_schedule:planned_final_window_step_span_3000_below_minimum_20000",
        ]:
            if expected not in reasons:
                raise AssertionError((expected, reasons))
        if short_data["development_acceleration_stage"] != "revise_time_averaging_schedule_before_cfd":
            raise AssertionError(short_data)
        if short_data["development_acceleration_runs_cfd_next"] is not False:
            raise AssertionError(short_data)
        if short_data["long_cfd_allowed_by_time_averaging_evidence"] is not False:
            raise AssertionError(short_data)

    print("time_averaging_evidence_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
