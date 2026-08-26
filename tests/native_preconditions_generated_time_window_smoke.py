#!/usr/bin/env python3
"""Smoke-test native preconditions against generated short-window metadata."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(REPO),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require(condition: bool, data: object) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> int:
    build = run_command(["dotnet", "build", "-c", "Release"])
    if build.returncode != 0:
        raise AssertionError(build.stdout + "\n" + build.stderr)

    codegen = run_command(
        [
            "dotnet",
            "run",
            "--project",
            str(REPO / "tests" / "CodegenSmoke" / "CodegenSmoke.csproj"),
            "-c",
            "Release",
        ]
    )
    if codegen.returncode != 0:
        raise AssertionError(codegen.stdout + "\n" + codegen.stderr)

    case_dir = Path(tempfile.gettempdir()) / "CityLBM" / "stg_codegen_smoke"
    metadata = case_dir / "case_metadata.json"
    manifest = case_dir / "native_fluidx3d_baseline_manifest.json"
    report = case_dir / "native_preconditions_generated_time_window_audit.json"
    require(metadata.exists(), {"missing": str(metadata), "stdout": codegen.stdout})
    require(manifest.exists(), {"missing": str(manifest), "stdout": codegen.stdout})

    audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_native_preconditions.py"),
            str(case_dir),
            "--manifest",
            str(manifest),
            "--metadata",
            str(metadata),
            "--out",
            str(report),
        ]
    )
    require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
    data = json.loads(report.read_text(encoding="utf-8"))
    reasons = data.get("native_preconditions_gate_reasons", [])
    require(data.get("planned_frame_count_min") == 10, data)
    require(data.get("planned_frame_count_shortfall_reason") == "planned_vtk_frame_count_10_below_minimum_40", data)
    require(data.get("planned_final_window_step_span") == 900, data)
    require(
        data.get("planned_average_step_span_shortfall_reason")
        == "planned_average_step_span_900_below_minimum_20000",
        data,
    )
    require(data.get("native_preconditions_time_average_evidence_gate") == "fail", data)
    require(data.get("time_averaging_fidelity_class") == "short_diagnostic_average_window", data)
    require(data.get("native_accuracy_evidence_gate") in {"", "fail"}, data)
    require(
        any(
            str(reason).startswith("native_accuracy_evidence_gate_not_pass:")
            for reason in reasons
        ),
        data,
    )
    require(data.get("planned_synthetic_inlet_sampling_source") == "case_metadata_fallback", data)
    require(data.get("planned_synthetic_inlet_sampling_gate") == "diagnostic_only", data)
    require(data.get("planned_synthetic_inlet_sampling_active") is True, data)
    require(data.get("planned_synthetic_inlet_update_interval") == 7, data)
    require(data.get("planned_synthetic_inlet_final_window_step_span") == 900, data)
    require(data.get("planned_synthetic_inlet_refresh_count") == 128, data)
    require(data.get("planned_synthetic_inlet_metadata_expected_refresh_count") == 128, data)
    require(data.get("planned_synthetic_inlet_minimum_refresh_count") == 200, data)
    require(
        "planned_stg_refresh_count_128_below_minimum_200"
        in data.get("planned_synthetic_inlet_sampling_gate_reasons", []),
        data,
    )
    require("planned_vtk_frame_count_below_minimum" in reasons, data)
    require("planned_vtk_frame_count_10_below_minimum_40" in reasons, data)
    require("planned_synthetic_inlet_sampling_gate_not_pass:diagnostic_only" in reasons, data)
    require(
        "planned_synthetic_inlet_sampling_reason:planned_stg_refresh_count_128_below_minimum_200"
        in reasons,
        data,
    )
    require("planned_average_step_span_too_short" in reasons, data)
    require("planned_average_step_span_900_below_minimum_20000" in reasons, data)
    require("native_time_average_evidence_gate_not_pass" in reasons, data)

    time_reasons = data.get("native_preconditions_time_average_evidence_gate_reasons", [])
    for expected in [
        "runtime_audit_missing",
        "planned_frame_shortfall:planned_vtk_frame_count_10_below_minimum_40",
        "planned_step_span_shortfall:planned_average_step_span_900_below_minimum_20000",
        "runtime_average_window_missing",
        "runtime_source_time_steps_missing",
        "runtime_source_vtk_hashes_missing",
    ]:
        require(expected in time_reasons, data)

    print("native_preconditions_generated_time_window_smoke passed")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
