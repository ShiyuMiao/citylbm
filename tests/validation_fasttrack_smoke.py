#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def load_module():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "run_validation_fasttrack.py"
    spec = importlib.util.spec_from_file_location("run_validation_fasttrack", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_validation_fasttrack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_bind_command_uses_fasttrack_out_root() -> None:
    module = load_module()
    case_dir = Path(r"F:\case root\case")
    out_root = Path(r"F:\case root\validation_runs\casea_fasttrack")
    args = SimpleNamespace(case_dir=str(case_dir))
    command = module.build_local_bind_command(args, out_root)
    expected_template = str(out_root / "inlet_reynolds_stress_tensor_template.csv")
    unexpected_template = str(case_dir / "preflight" / "inlet_reynolds_stress_tensor_template.csv")
    if expected_template not in command:
        raise AssertionError("fast-track bind command does not use the current output root template")
    if unexpected_template in command:
        raise AssertionError("fast-track bind command fell back to the case/preflight template")


def test_plan_command_uses_fasttrack_out_root_for_template_outputs() -> None:
    module = load_module()
    repo = Path(r"F:\repo")
    case_dir = Path(r"F:\case root\case")
    out_root = Path(r"F:\case root\validation_runs\casea_fasttrack")
    args = SimpleNamespace(
        case="casea",
        case_dir=str(case_dir),
        fluidx3d_source=r"F:\FluidX3D",
        solver_cwd="",
        official="",
        af_csv="",
    )
    command = module.build_plan_command(args, repo, out_root)
    joined = " ".join(command)
    if "--template-preflight-dir" not in command:
        raise AssertionError(command)
    if str(out_root) not in joined:
        raise AssertionError(command)


def test_default_out_root_uses_temp_when_repo_drive_is_low() -> None:
    module = load_module()
    repo = Path(__file__).resolve().parents[1]
    repo_default, repo_meta = module.default_out_root(repo, "casee", "STAMP", min_free_bytes=0)
    if repo_default != repo / "validation_runs" / "casee_fasttrack_STAMP":
        raise AssertionError((repo_default, repo_meta))
    temp_default, temp_meta = module.default_out_root(repo, "casee", "STAMP", min_free_bytes=10**20)
    if "CityLBM_validation_runs" not in str(temp_default):
        raise AssertionError((temp_default, temp_meta))
    if temp_meta["mode"] != "temp_due_to_low_repo_disk_free":
        raise AssertionError(temp_meta)


def test_diagnostic_canary_overrides_repeated_preflight_next_step() -> None:
    module = load_module()
    args = SimpleNamespace(case_dir=r"F:\cases\casea")
    summary = {
        "next_execution_policy": "run_no_cfd_preflight_first",
        "next_batch_name": "no_cfd_source_and_protocol_preflight",
        "next_command": "python run_native_preflight_pack.py",
        "long_cfd_allowed_now": False,
    }
    preflight_manifest = {
        "DevelopmentTriage": {
            "SuggestedCommands": [
                {
                    "Name": "run_native_diagnostic_canary",
                    "Command": ["python", "scripts\\run_native_fluidx3d_case.py", "--run"],
                    "UseClass": "diagnostic_only_not_for_paper_accuracy_claims",
                    "Prerequisite": "preflight passed diagnostic gate",
                },
                {
                    "Name": "audit_runtime_inlet_diagnostics_after_canary",
                    "Command": ["python", "scripts\\audit_inlet_diagnostics_csv.py", "stats.csv"],
                    "UseClass": "diagnostic_inlet_u_k_rms_preservation_check",
                    "Prerequisite": "canary output exists",
                },
                {
                    "Name": "audit_inlet_correlation_after_canary",
                    "Command": ["python", "scripts\\audit_inlet_correlation_from_vtk.py", "output"],
                    "UseClass": "diagnostic_inlet_time_space_correlation_and_k_tke_check",
                    "Prerequisite": "VTK output exists",
                },
            ]
        }
    }
    plan = module.build_next_step_plan(
        args=args,
        out_root=Path(r"F:\runs\casea_fasttrack"),
        summary=summary,
        preflight_manifest=preflight_manifest,
        diagnostic_canary_allowed=True,
        long_cfd_allowed=False,
    )
    if plan["next_execution_policy"] != "run_short_native_canary_then_post_audits":
        raise AssertionError(plan)
    if plan["next_batch_name"] != "short_native_canary":
        raise AssertionError(plan)
    if "run_native_fluidx3d_case.py" not in plan["next_command"]:
        raise AssertionError(plan)
    if len(plan["next_commands"]) != 4:
        raise AssertionError(plan)
    if len(plan["post_canary_audit_commands"]) != 3:
        raise AssertionError(plan)
    if plan["post_canary_audit_commands"][-1]["name"] != "bind_canary_runtime_evidence_after_audits":
        raise AssertionError(plan)
    if plan["original_next_execution_policy"] != "run_no_cfd_preflight_first":
        raise AssertionError(plan)


def main() -> int:
    test_local_bind_command_uses_fasttrack_out_root()
    test_plan_command_uses_fasttrack_out_root_for_template_outputs()
    test_default_out_root_uses_temp_when_repo_drive_is_low()
    test_diagnostic_canary_overrides_repeated_preflight_next_step()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
