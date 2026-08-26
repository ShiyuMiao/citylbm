#!/usr/bin/env python3
"""Smoke-test validation acceleration command templates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}")


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="citylbm_plan_smoke_") as temp_dir:
        out_json = Path(temp_dir) / "plan.json"
        out_md = Path(temp_dir) / "plan.md"
        completed = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "plan_validation_acceleration.py"),
                "--case",
                "casea",
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"planner failed: rc={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        text = out_md.read_text(encoding="utf-8")
        require(text, "## Development Time Compression")
        require(text, "Next execution policy: run_no_cfd_preflight_first")
        require(text, "Long CFD allowed now: false")
        require(text, "Canary runtime evidence gate: missing")
        require(text, "### Next Command To Run First")
        require(text, "### diagnostic_canary_cfd")
        require(text, '"--metadata" "<case_dir>\\case_metadata.json"')
        require(text, '"--time-steps" "5000"')
        require(text, '"--expected-probe-row-count" "186"')
        require(text, '"--expected-probe-z-min" "0.01"')
        require(text, '"--expected-probe-z-max" "0.28"')
        require(text, '"--z-ref" "0.16"')
        require(text, '"--expected-uref" "4.491"')
        require(text, '"--expected-vtk-frame-count" "5"')
        require(text, '"--average-last-n" "5"')
        require(text, '"--min-vtk-frames" "1"')
        require(text, '"--min-vtk-step-span" "0"')
        require(text, "### paper_candidate_cfd")
        require(text, '"--time-steps" "40000"')
        require(text, '"--expected-vtk-frame-count" "40"')
        require(text, '"--average-last-n" "40"')
        require(text, '"--min-vtk-frames" "40"')
        require(text, '"--min-vtk-step-span" "20000"')
        require(text, "scripts\\audit_inlet_diagnostics_csv.py")
        require(text, "runtime_inlet_diagnostics_csv_missing_or_failed")
        require(text, "scripts\\summarize_validation_blockers.py")

        case_dir = Path(temp_dir) / "case"
        preflight_dir = case_dir / "preflight"
        preflight_dir.mkdir(parents=True)
        (case_dir / "case_metadata.json").write_text("{}", encoding="utf-8")
        bound_metadata = preflight_dir / "case_metadata.inlet_bound.json"
        bound_metadata.write_text("{}", encoding="utf-8")
        (preflight_dir / "native_preflight_pack_manifest.json").write_text(
            json.dumps(
                {
                    "Gate": "diagnostic_only",
                    "Artifacts": {
                        "InletBoundMetadata": str(bound_metadata),
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        bound_out_json = Path(temp_dir) / "bound_plan.json"
        bound_out_md = Path(temp_dir) / "bound_plan.md"
        completed = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "plan_validation_acceleration.py"),
                "--case",
                "casea",
                "--case-dir",
                str(case_dir),
                "--run-dir",
                str(preflight_dir),
                "--out-json",
                str(bound_out_json),
                "--out-md",
                str(bound_out_md),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"planner with bound metadata failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        bound_plan = json.loads(bound_out_json.read_text(encoding="utf-8"))
        canary = bound_plan["command_templates"]["diagnostic_canary_cfd"]
        paper = bound_plan["command_templates"]["paper_candidate_cfd"]
        require(canary, f'"--metadata" "{bound_metadata.resolve()}"')
        require(paper, f'"--metadata" "{bound_metadata.resolve()}"')

        canary_run_dir = Path(temp_dir) / "canary_run"
        canary_run_dir.mkdir()
        (canary_run_dir / "native_preflight_pack_manifest.json").write_text(
            json.dumps(
                {
                    "Gate": "diagnostic_only",
                    "Reasons": [
                        "inlet_correlation_audit_missing",
                        "inlet_correlation_frame_count_below_minimum",
                        "source_missing_turbulent_length_scale_evidence",
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (canary_run_dir / "canary_runtime_evidence_manifest.json").write_text(
            json.dumps({"Gate": "pass", "Reasons": ["canary_runtime_evidence_present"]}, indent=2),
            encoding="utf-8",
        )
        canary_out_json = Path(temp_dir) / "canary_plan.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "plan_validation_acceleration.py"),
                "--case",
                "casea",
                "--run-dir",
                str(canary_run_dir),
                "--out-json",
                str(canary_out_json),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"planner with canary evidence failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        canary_plan = json.loads(canary_out_json.read_text(encoding="utf-8"))
        failures = "\n".join(canary_plan["runs"][0]["failures"])
        if "inlet_correlation_audit_missing" in failures:
            raise AssertionError(failures)
        if "inlet_correlation_frame_count_below_minimum" in failures:
            raise AssertionError(failures)
        if "source_missing_turbulent_length_scale_evidence" not in failures:
            raise AssertionError(failures)
        if canary_plan["acceleration_summary"]["canary_runtime_evidence_gate"] != "pass":
            raise AssertionError(canary_plan["acceleration_summary"])

        boundary_patch_dir = Path(temp_dir) / "boundary_patch_run"
        boundary_patch_dir.mkdir()
        (boundary_patch_dir / "fluidx3d_equilibrium_boundary_audit.json").write_text(
            json.dumps(
                {
                    "Gate": "fail",
                    "Evidence": {
                        "has_type_e_define": True,
                        "has_equilibrium_boundaries_macro": True,
                        "has_reconstruct_feq_from_rho_u": True,
                        "has_reconstruct_store_f": True,
                        "has_stream_collide_type_e_macro_velocity": True,
                        "has_stream_collide_type_e_feq_collision": True,
                        "has_reconstruct_equilibrium_kernel": False,
                        "has_lbm_kernel_binding": False,
                        "has_lbm_public_call": False,
                    },
                    "EnabledMacros": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        boundary_out_json = Path(temp_dir) / "boundary_plan.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "plan_validation_acceleration.py"),
                "--case",
                "casea",
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(Path(temp_dir) / "FluidX3D"),
                "--run-dir",
                str(boundary_patch_dir),
                "--out-json",
                str(boundary_out_json),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"planner with boundary patch evidence failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        boundary_plan = json.loads(boundary_out_json.read_text(encoding="utf-8"))
        boundary_summary = boundary_plan["acceleration_summary"]
        if boundary_summary["fastest_phase"] != "patch_fluidx3d_equilibrium_boundary_source":
            raise AssertionError(boundary_summary)
        if "patch_fluidx3d_equilibrium_boundary_source.py" not in boundary_summary["next_command"]:
            raise AssertionError(boundary_summary)
    print("plan_validation_acceleration_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
