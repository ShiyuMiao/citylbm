#!/usr/bin/env python3
"""Smoke-test Grasshopper time-averaging thresholds and Read VTK audit fields."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"Missing {label}: {needle}")


def main() -> int:
    read_vtk = (REPO / "src" / "Components" / "Results" / "ReadVTKComponent.cs").read_text(
        encoding="utf-8"
    )
    run_sim = (
        REPO / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
    ).read_text(encoding="utf-8")

    require(read_vtk, "private const int MinimumValidationAverageFrames = 40;", "Read VTK frame threshold")
    require(read_vtk, "private const int MinimumValidationAverageStepSpan = 20000;", "Read VTK step-span threshold")
    require(read_vtk, '{ "source_step_span", sourceStepSpan }', "Read VTK source_step_span audit")
    require(
        read_vtk,
        '{ "source_step_span_shortfall", sourceStepSpanShortfall }',
        "Read VTK source_step_span_shortfall audit",
    )
    require(
        read_vtk,
        '{ "minimum_validation_average_step_span", MinimumValidationAverageStepSpan }',
        "Read VTK minimum step-span audit",
    )
    require(read_vtk, 'reasons.Add("source_step_span_missing");', "Read VTK missing span reason")
    require(
        read_vtk,
        'reasons.Add($"source_step_span_below_{MinimumValidationAverageStepSpan}");',
        "Read VTK short span reason",
    )
    require(
        read_vtk,
        "averagedFrameCount >= MinimumValidationAverageFrames",
        "Read VTK candidate hint threshold",
    )

    require(run_sim, "private const int MinimumValidationAveragingFrames = 40;", "Run Simulation frame threshold")
    require(
        run_sim,
        "private const int MinimumValidationAveragingStepSpan = 20000;",
        "Run Simulation step-span threshold",
    )

    print("read_vtk_time_average_thresholds_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
