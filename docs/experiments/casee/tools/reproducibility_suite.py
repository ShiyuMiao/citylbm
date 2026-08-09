#!/usr/bin/env python3
"""Run the lightweight Case E reproducibility suite for the current rc branch."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
DEFAULT_PREDICTED = RESULTS_DIR / "casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv"
DEFAULT_DOTNET = Path(r"E:\citylbm_buildchain\dotnet\dotnet.exe")
DEFAULT_FLUIDX3D = Path(r"E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe")
BUILD_LOG = RESULTS_DIR / "citylbm_build_check.log"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
RELEASE_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha"
OUT_JSON = RESULTS_DIR / "casee_reproducibility_suite.json"
OUT_MD = RESULTS_DIR / "casee_reproducibility_suite.md"


def run_command(
    name: str,
    args: List[str],
    *,
    stdout_path: Optional[Path] = None,
    expect_release_gate_block: bool = False,
) -> Dict[str, Any]:
    start = datetime.now(timezone.utc)
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        encoding="utf-8",
        errors="replace",
    )
    end = datetime.now(timezone.utc)
    stdout = proc.stdout
    stderr = proc.stderr
    if stdout_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(stdout + stderr, encoding="utf-8")
    passed = proc.returncode == 0
    if expect_release_gate_block:
        passed = proc.returncode != 0 and "formal_release_allowed=False" in stdout
    return {
        "name": name,
        "command": " ".join(args),
        "started_at": start.isoformat(),
        "ended_at": end.isoformat(),
        "returncode": proc.returncode,
        "passed": passed,
        "stdout_tail": "\n".join(stdout.splitlines()[-12:]),
        "stderr_tail": "\n".join(stderr.splitlines()[-12:]),
        "stdout_path": "" if stdout_path is None else str(stdout_path.relative_to(ROOT).as_posix()),
        "expected_release_gate_block": expect_release_gate_block,
    }


def copy_release_gha() -> Dict[str, Any]:
    if not RELEASE_GHA.exists():
        return {
            "name": "sync_tracked_gha",
            "passed": False,
            "message": f"Missing Release GHA: {RELEASE_GHA}",
        }
    TRACKED_GHA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RELEASE_GHA, TRACKED_GHA)
    return {
        "name": "sync_tracked_gha",
        "passed": TRACKED_GHA.exists(),
        "source": str(RELEASE_GHA.relative_to(ROOT).as_posix()),
        "destination": str(TRACKED_GHA.relative_to(ROOT).as_posix()),
    }


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_markdown(payload: Dict[str, Any]) -> None:
    gate = payload.get("release_gate", {})
    metrics = gate.get("metrics") or {}
    artifact = payload.get("artifact_index", {}).get("summary", {})
    lines = [
        "# Case E Reproducibility Suite",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Suite passed: {payload['suite_passed']}",
        f"- Formal v0.4.0 allowed: {gate.get('formal_release_allowed')}",
        f"- Recommended tag: `{gate.get('recommended_tag')}`",
        "",
        "## Official z=2 m Metric",
        "",
        f"- MAE: {metrics.get('mae_pp')} pp",
        f"- R2: {metrics.get('r2')}",
        f"- Pearson: {metrics.get('pearson')}",
        "",
        "## Artifact Index",
        "",
        f"- Artifact count: {artifact.get('artifact_count')}",
        f"- Lightweight release assets: {artifact.get('lightweight_release_asset_count')}",
        f"- Formal accuracy claim supported: {artifact.get('formal_accuracy_claim_supported')}",
        "",
        "## Commands",
        "",
        "| step | returncode | passed |",
        "|---|---:|---:|",
    ]
    for step in payload["steps"]:
        lines.append(f"| {step['name']} | {step.get('returncode', '')} | {step['passed']} |")
    lines += [
        "",
        "## Boundary",
        "",
        "This suite proves that the current rc evidence chain is reproducible and claim-safe. It intentionally treats the formal release gate as blocked while official z=2 m R2 remains negative.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicted", type=Path, default=DEFAULT_PREDICTED)
    parser.add_argument("--release-target", default="v0.4.0")
    parser.add_argument("--dotnet-command", default=str(DEFAULT_DOTNET))
    parser.add_argument("--fluidx3d-exe", type=Path, default=DEFAULT_FLUIDX3D)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    steps: List[Dict[str, Any]] = []
    python = "python"

    if not args.skip_build:
        steps.append(
            run_command(
                "citylbm_release_build",
                [args.dotnet_command, "build", str(ROOT / "CityLBM" / "CityLBM.csproj"), "-c", "Release"],
                stdout_path=BUILD_LOG,
            )
        )
        steps.append(copy_release_gha())

    steps.append(
        run_command(
            "casee_audit",
            [
                python,
                str(CASE_DIR / "tools" / "casee_audit.py"),
                "--predicted",
                str(args.predicted),
                "--release-target",
                args.release_target,
                "--dotnet-command",
                args.dotnet_command,
                "--fluidx3d-exe",
                str(args.fluidx3d_exe),
            ],
        )
    )
    for name, script in [
        ("manuscript_evidence_summary", "manuscript_evidence_summary.py"),
        ("plugin_identity_gate", "plugin_identity_gate.py"),
        ("rhino_gha_load_gate", "rhino_gha_load_gate.py"),
        ("casee_official_run_preflight", "casee_official_run_preflight.py"),
        ("casee_environment_recovery_runbook", "casee_environment_recovery_runbook.py"),
        ("casee_failure_mode_atlas", "casee_failure_mode_atlas.py"),
        ("casee_default_policy_gate", "casee_default_policy_gate.py"),
        ("citylbm_paper_results_packet", "citylbm_paper_results_packet.py"),
        ("citylbm_manifest_output_gate", "citylbm_manifest_output_gate.py"),
        ("casee_manuscript_results_table", "casee_manuscript_results_table.py"),
        ("casee_manuscript_section_pack", "casee_manuscript_section_pack.py"),
        ("casee_paper_results_figure", "casee_paper_results_figure.py"),
        ("citylbm_software_feedback_matrix", "citylbm_software_feedback_matrix.py"),
        ("artifact_index_pre_appendix", "artifact_index.py"),
        ("paper_appendix_generator", "paper_appendix_generator.py"),
        ("casee_blocker_remediation_plan", "casee_blocker_remediation_plan.py"),
        ("casee_next_experiment_runbook", "casee_next_experiment_runbook.py"),
        ("artifact_index", "artifact_index.py"),
        ("paper_evidence_gate", "paper_evidence_gate.py"),
    ]:
        steps.append(run_command(name, [python, str(CASE_DIR / "tools" / script)]))
    steps.append(run_command("formal_release_gate_expected_block", [python, str(CASE_DIR / "tools" / "release_gate.py")], expect_release_gate_block=True))

    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    paper_gate = read_json(RESULTS_DIR / "casee_paper_evidence_gate.json")
    plugin_gate = read_json(RESULTS_DIR / "plugin_identity_gate.json")
    rhino_gate = read_json(RESULTS_DIR / "rhino_gha_load_gate.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    recovery = read_json(RESULTS_DIR / "casee_environment_recovery_runbook.json")
    failure_atlas = read_json(RESULTS_DIR / "casee_failure_mode_atlas.json")
    default_policy = read_json(RESULTS_DIR / "casee_default_policy_gate.json")
    paper_results_packet = read_json(RESULTS_DIR / "citylbm_paper_results_packet.json")
    manifest_output_gate = read_json(RESULTS_DIR / "citylbm_manifest_output_gate.json")
    manuscript_results_table = read_json(RESULTS_DIR / "casee_manuscript_results_table.json")
    manuscript_section_pack = read_json(RESULTS_DIR / "casee_manuscript_section_pack.json")
    paper_results_figure = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    software_feedback_matrix = read_json(RESULTS_DIR / "citylbm_software_feedback_matrix.json")
    artifact_index = read_json(RESULTS_DIR / "casee_artifact_index.json")
    suite_passed = all(bool(step.get("passed")) for step in steps) and not bool(release_gate.get("formal_release_allowed"))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite_passed": suite_passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready reproducibility chain; blocked formal accuracy release",
        "steps": steps,
        "release_gate": release_gate,
        "paper_evidence_gate": paper_gate,
        "plugin_identity_gate": plugin_gate,
        "rhino_gha_load_gate": rhino_gate,
        "casee_official_run_preflight": preflight,
        "casee_environment_recovery_runbook": recovery,
        "casee_failure_mode_atlas": failure_atlas,
        "casee_default_policy_gate": default_policy,
        "citylbm_paper_results_packet": paper_results_packet,
        "citylbm_manifest_output_gate": manifest_output_gate,
        "casee_manuscript_results_table": manuscript_results_table,
        "casee_manuscript_section_pack": manuscript_section_pack,
        "casee_paper_results_figure": paper_results_figure,
        "citylbm_software_feedback_matrix": software_feedback_matrix,
        "artifact_index": artifact_index,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload)
    print(json.dumps({"suite_passed": suite_passed, "out_json": str(OUT_JSON)}, indent=2))
    return 0 if suite_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
