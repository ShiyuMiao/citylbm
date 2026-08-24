#!/usr/bin/env python3
"""Smoke-test that a four-frame runtime VTK window cannot pass native preconditions."""

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
    runtime_audit = case_dir / "native_run_four_frame_window_smoke.json"
    report = case_dir / "native_preconditions_runtime_four_frame_window_audit.json"
    require(metadata.exists(), {"missing": str(metadata), "stdout": codegen.stdout})
    require(manifest.exists(), {"missing": str(manifest), "stdout": codegen.stdout})

    steps = [700, 800, 900, 1000]
    hashes = [f"{index:064x}" for index in range(1, len(steps) + 1)]
    runtime_audit.write_text(
        json.dumps(
            {
                "vtk_pattern": "u-*.vtk",
                "average_last_n_requested": 4,
                "averaged_frame_count": 4,
                "available_frame_count": 4,
                "requested_vtk_frame_count": 4,
                "requested_vtk_frame_gate": "diagnostic_only",
                "requested_vtk_save_start_step": 100,
                "source_time_steps": steps,
                "source_step_span": 300,
                "source_steps_strictly_increasing": True,
                "source_step_spacing_uniform": True,
                "selected_last_window": True,
                "freshness_selected_vtk_files": [
                    {
                        "time_step": step,
                        "path": str(case_dir / "output" / f"u-{step:010d}.vtk"),
                        "sha256": digest,
                    }
                    for step, digest in zip(steps, hashes)
                ],
                "time_averaging_gate": "diagnostic_only",
                "time_averaging_gate_reasons": [
                    "averaged_frame_count_below_40",
                    "source_step_span_below_20000",
                    "requested_vtk_frame_preflight_not_pass",
                ],
                "final_window_stationarity_gate": "pass",
                "final_window_stationarity_gate_reasons": [],
                "final_window_mean_speed_drift_ratio": 0.01,
                "max_final_window_mean_speed_drift_ratio": 0.03,
                "mean_speed_statistics_source": "sampled_vtk",
                "mean_speed_statistics_cli_override": False,
                "mean_speed_statistics_cli_override_fields_csv": "",
                "strict_native_run_gate": "fail",
                "strict_native_run_gate_reasons": [
                    "requested_vtk_frame_gate_not_pass:diagnostic_only",
                    "time_averaging_gate_not_pass:diagnostic_only",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_native_preconditions.py"),
            str(case_dir),
            "--manifest",
            str(manifest),
            "--metadata",
            str(metadata),
            "--runtime-audit",
            str(runtime_audit),
            "--out",
            str(report),
        ]
    )
    require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
    data = json.loads(report.read_text(encoding="utf-8"))
    reasons = data.get("native_preconditions_gate_reasons", [])
    time_reasons = data.get("native_preconditions_time_average_evidence_gate_reasons", [])

    require(data.get("runtime_average_last_n") == 4, data)
    require(data.get("runtime_source_frame_count") == 4, data)
    require(data.get("runtime_source_step_span") == 300, data)
    require(data.get("runtime_source_step_span_from_time_steps") == 300, data)
    require(data.get("runtime_selected_last_window") is True, data)
    require(data.get("runtime_source_vtk_sha256_count") == 4, data)
    require(data.get("runtime_source_vtk_sha256_unique_count") == 4, data)
    require(data.get("runtime_final_window_frame_count_gate") == "fail", data)
    require(data.get("native_preconditions_time_average_evidence_gate") == "fail", data)
    require(data.get("time_averaging_fidelity_class") == "short_diagnostic_average_window", data)

    for expected in [
        "runtime_average_window_mismatch_or_too_short",
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_average_step_span_too_short",
        "runtime_average_step_span_300_below_minimum_20000",
        "runtime_source_vtk_hash_count_below_min_avg_frames",
        "runtime_time_averaging_gate_not_pass",
        "strict_native_run_gate_not_pass:fail",
        "native_time_average_evidence_gate_not_pass",
    ]:
        require(expected in reasons, data)

    for expected in [
        "runtime_reported_time_averaging_gate_not_pass:fail",
        "runtime_time_averaging_gate_not_pass:diagnostic_only",
        "runtime_requested_vtk_frame_gate_not_pass:diagnostic_only",
        "runtime_average_window_shortfall:runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_step_span_shortfall:runtime_average_step_span_300_below_minimum_20000",
        "runtime_average_window_4_does_not_match_required_40",
        "runtime_source_vtk_hash_count_4_below_minimum_40",
    ]:
        require(expected in time_reasons, data)

    frame_reasons = data.get("runtime_final_window_frame_count_gate_reasons", [])
    for expected in [
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_source_frame_count_4_below_minimum_40",
        "runtime_source_vtk_sha256_count_4_below_minimum_40",
    ]:
        require(expected in frame_reasons, data)

    print("native_preconditions_runtime_four_frame_window_smoke passed")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
