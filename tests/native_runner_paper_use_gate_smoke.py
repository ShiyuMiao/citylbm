#!/usr/bin/env python3
"""Smoke-test the native runner paper-use gate."""

from __future__ import annotations

import importlib.util
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


def gate(name: str = "pass") -> dict:
    return {"Gate": name, "Reasons": [] if name == "pass" else [f"{name}_reason"]}


def main() -> int:
    runner = load_runner()

    passed = runner.paper_use_gate(
        official_input=gate(),
        inlet_source=gate(),
        boundary_source=gate(),
        coordinate_probe_protocol=gate(),
        inlet_correlation=gate(),
        planned_vtk_schedule=gate(),
        flow_through_time=gate(),
        actual_vtk_output=gate(),
        runtime_inlet_diagnostics=gate(),
        native_accuracy_gate=gate(),
        diagnostic_override_allowed=False,
    )
    if passed["Gate"] != "pass" or passed["PaperUsable"] is not True:
        raise AssertionError(passed)

    dry_run = runner.paper_use_gate(
        official_input=gate(),
        inlet_source=gate(),
        boundary_source=gate(),
        coordinate_probe_protocol=gate(),
        inlet_correlation=gate(),
        planned_vtk_schedule=gate(),
        flow_through_time=gate(),
        actual_vtk_output={"Gate": "not_applicable", "Reasons": ["actual_output_not_required"]},
        runtime_inlet_diagnostics={"Gate": "not_applicable", "Reasons": ["runtime_inlet_diagnostics_not_requested"]},
        native_accuracy_gate={"Gate": "fail", "Reasons": ["native_run_not_requested"]},
        diagnostic_override_allowed=False,
    )
    for reason in [
        "actual_vtk_output_gate_not_pass:not_applicable",
        "actual_vtk_output:actual_output_not_required",
        "runtime_inlet_diagnostics_gate_not_pass:not_applicable",
        "runtime_inlet_diagnostics:runtime_inlet_diagnostics_not_requested",
        "native_accuracy_evidence_gate_not_pass:fail",
        "native_accuracy_evidence:native_run_not_requested",
    ]:
        if reason not in dry_run["Reasons"]:
            raise AssertionError(dry_run)
    if dry_run["PaperUsable"] is not False:
        raise AssertionError(dry_run)

    override = runner.paper_use_gate(
        official_input=gate(),
        inlet_source=gate(),
        boundary_source=gate(),
        coordinate_probe_protocol=gate(),
        inlet_correlation=gate(),
        planned_vtk_schedule=gate(),
        flow_through_time=gate(),
        actual_vtk_output=gate(),
        runtime_inlet_diagnostics=gate(),
        native_accuracy_gate=gate(),
        diagnostic_override_allowed=True,
    )
    if override["Gate"] != "fail" or "diagnostic_execution_override_used" not in override["Reasons"]:
        raise AssertionError(override)
    if override["Interpretation"] != "debug_or_diagnostic_only_do_not_use_for_r2_or_paper_accuracy_claim":
        raise AssertionError(override)

    print("native_runner_paper_use_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
