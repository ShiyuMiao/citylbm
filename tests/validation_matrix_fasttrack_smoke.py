#!/usr/bin/env python3
"""Smoke-test the multi-case validation fast-track wrapper."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from native_fluidx3d_runner_smoke import create_case, create_source  # noqa: E402


def load_module():
    script = REPO / "scripts" / "run_validation_matrix_fasttrack.py"
    spec = importlib.util.spec_from_file_location("run_validation_matrix_fasttrack", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_validation_matrix_fasttrack.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_selected_cases_and_commands() -> None:
    module = load_module()
    args = SimpleNamespace(
        fluidx3d_source=r"F:\FluidX3D",
        casea_dir=r"F:\cases\case a",
        casee_dir=r"F:\cases\case e",
        casea_official=r"F:\official\RS_caseA.csv",
        casea_af_csv=r"F:\official\AF_caseA.csv",
        casee_official=r"F:\official\RS_caseE.csv",
        casee_af_csv=r"F:\official\AF_caseE.csv",
        solver_root=r"C:\CityLBM_native_runs",
        child_jobs=3,
        serial_child=False,
        patch_metadata_identity=True,
        fail_on_long_cfd_blocked=False,
    )
    cases = module.selected_cases(args)
    if [item["case"] for item in cases] != ["casea", "casee"]:
        raise AssertionError(cases)
    command = module.build_case_command(
        repo=Path(r"F:\repo"),
        args=args,
        case_spec=cases[1],
        out_root=Path(r"C:\out"),
    )
    joined = " ".join(command)
    for expected in [
        "run_validation_fasttrack.py",
        "--case casee",
        r"F:\official\RS_caseE.csv",
        r"F:\official\AF_caseE.csv",
        r"C:\CityLBM_native_runs\casee",
        "--jobs 3",
        "--patch-metadata-identity",
    ]:
        if expected not in joined:
            raise AssertionError(command)


def test_aggregate_summary_prefers_first_blocker() -> None:
    module = load_module()
    summary = module.aggregate_summary(
        [
            {
                "case": "casea",
                "return_code": 0,
                "diagnostic_canary_allowed_now": True,
                "long_cfd_allowed_now": False,
                "next_execution_policy": "run_short_native_canary_only",
                "next_batch_name": "short_native_canary",
                "next_command": "python canary",
                "preflight_reasons": ["time_window_short"],
            },
            {
                "case": "casee",
                "return_code": 0,
                "diagnostic_canary_allowed_now": False,
                "long_cfd_allowed_now": True,
                "next_execution_policy": "paper_candidate_only_after_prior_gates_pass",
                "next_batch_name": "paper_candidate_native_run",
                "next_command": "python paper",
                "preflight_reasons": [],
            },
        ]
    )
    if summary["diagnostic_canary_ready_cases"] != ["casea"]:
        raise AssertionError(summary)
    if summary["long_cfd_ready_cases"] != ["casee"]:
        raise AssertionError(summary)
    if summary["long_cfd_blocked_cases"] != ["casea"]:
        raise AssertionError(summary)
    if summary["first_blocker"]["case"] != "casea":
        raise AssertionError(summary)
    if summary["all_long_cfd_ready"] is not False:
        raise AssertionError(summary)


def test_end_to_end_with_stubbed_child_fasttrack() -> None:
    with tempfile.TemporaryDirectory(prefix="citylbm_matrix_fasttrack_") as raw:
        temp = Path(raw)
        source = temp / "FluidX3D"
        casea = temp / "casea"
        casee = temp / "casee"
        create_source(source)
        create_case(casea)
        create_case(casee)
        out_root = temp / "out"
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "run_validation_matrix_fasttrack.py"),
                "--fluidx3d-source",
                str(source),
                "--casea-dir",
                str(casea),
                "--casee-dir",
                str(casee),
                "--out-root",
                str(out_root),
                "--child-jobs",
                "1",
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        manifest = json.loads((out_root / "validation_matrix_fasttrack_manifest.json").read_text(encoding="utf-8"))
        if manifest["summary"]["long_cfd_ready_cases"] != []:
            raise AssertionError(manifest)
        if manifest["summary"]["long_cfd_blocked_cases"] != ["casea", "casee"]:
            raise AssertionError(manifest)
        if not manifest["summary"]["first_blocker"].get("next_command"):
            raise AssertionError(manifest)
        if manifest["case_workers"] != 2:
            raise AssertionError(manifest)
        for case in manifest["cases"]:
            if not case["manifest_found"]:
                raise AssertionError(case)
            if case["return_code"] != 0:
                raise AssertionError(case)
            if not case["artifacts"].get("acceleration_plan_json"):
                raise AssertionError(case)


def main() -> int:
    test_selected_cases_and_commands()
    test_aggregate_summary_prefers_first_blocker()
    test_end_to_end_with_stubbed_child_fasttrack()
    print("validation_matrix_fasttrack_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
