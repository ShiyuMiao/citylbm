#!/usr/bin/env python3
"""Run the lightweight Case E reproducibility suite for the current rc branch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
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


def write_text_retry(path: Path, text: str, *, encoding: str = "utf-8", attempts: int = 6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Optional[OSError] = None
    for attempt in range(attempts):
        try:
            path.write_text(text, encoding=encoding)
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.2 * (attempt + 1))
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp_path.write_text(text, encoding=encoding)
        tmp_path.replace(path)
        return
    except OSError:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if last_error is not None:
            raise last_error
        raise


def run_command(
    name: str,
    args: List[str],
    *,
    stdout_path: Optional[Path] = None,
    expect_release_gate_block: bool = False,
) -> Dict[str, Any]:
    start = datetime.now(timezone.utc)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
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
        write_text_retry(stdout_path, stdout + stderr)
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
    source_sha = sha256(RELEASE_GHA)
    if TRACKED_GHA.exists() and sha256(TRACKED_GHA) == source_sha:
        return {
            "name": "sync_tracked_gha",
            "passed": True,
            "source": str(RELEASE_GHA.relative_to(ROOT).as_posix()),
            "destination": str(TRACKED_GHA.relative_to(ROOT).as_posix()),
            "source_sha256": source_sha,
            "destination_sha256": source_sha,
            "message": "Tracked GHA already matches Release build; copy skipped.",
        }
    last_error = ""
    for _ in range(5):
        try:
            shutil.copy2(RELEASE_GHA, TRACKED_GHA)
            break
        except OSError as exc:
            last_error = str(exc)
            time.sleep(0.5)
    else:
        return {
            "name": "sync_tracked_gha",
            "passed": False,
            "source": str(RELEASE_GHA.relative_to(ROOT).as_posix()),
            "destination": str(TRACKED_GHA.relative_to(ROOT).as_posix()),
            "message": f"Could not copy Release GHA after retries: {last_error}",
        }
    return {
        "name": "sync_tracked_gha",
        "passed": TRACKED_GHA.exists(),
        "source": str(RELEASE_GHA.relative_to(ROOT).as_posix()),
        "destination": str(TRACKED_GHA.relative_to(ROOT).as_posix()),
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def grasshopper_library_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA", ""))
    if appdata:
        return appdata / "Grasshopper" / "Libraries"
    return Path.home() / "AppData" / "Roaming" / "Grasshopper" / "Libraries"


def stage_tracked_gha_for_grasshopper() -> Dict[str, Any]:
    if not TRACKED_GHA.exists():
        return {
            "name": "stage_tracked_gha_for_grasshopper",
            "passed": False,
            "message": f"Missing tracked GHA: {TRACKED_GHA}",
        }
    target_dir = grasshopper_library_dir()
    target = target_dir / "CityLBM.gha"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TRACKED_GHA, target)
    source_sha = sha256(TRACKED_GHA)
    target_sha = sha256(target)
    return {
        "name": "stage_tracked_gha_for_grasshopper",
        "passed": source_sha == target_sha,
        "source": str(TRACKED_GHA.relative_to(ROOT).as_posix()),
        "destination": str(target),
        "source_sha256": source_sha,
        "target_sha256": target_sha,
        "boundary": "Staging only; Rhino/Grasshopper load evidence remains controlled by rhino_gha_load_gate.py.",
    }


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def write_publication_gate_provisional_suite(steps: List[Dict[str, Any]]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite_passed": all(bool(step.get("passed")) for step in steps),
        "publication_gate_provisional": True,
        "evidence_type": "newly_run",
        "claim_readiness": "provisional self-reference for publication gate; overwritten by final suite payload",
        "steps_completed_before_publication_gate": [step.get("name") for step in steps],
        "boundary": (
            "This temporary payload lets casee_publication_readiness_gate.py evaluate the current suite "
            "run instead of a stale previous suite result. It is overwritten by the final full suite output."
        ),
    }
    write_text_retry(OUT_JSON, json.dumps(payload, indent=2))


def write_markdown(payload: Dict[str, Any]) -> None:
    gate = payload.get("release_gate", {})
    metrics = gate.get("metrics") or {}
    artifact = payload.get("artifact_index", {}).get("summary", {})
    build_chain = payload.get("build_chain_manifest", {})
    vs = build_chain.get("visual_studio_build_tools_2022_cpp", {})
    gpu = build_chain.get("gpu_runtime", {})
    dx1 = payload.get("casee_dx1_readiness_audit", {}).get("summary", {})
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
        "## Build Chain",
        "",
        f"- Build chain ready: {build_chain.get('build_chain_ready')}",
        f"- VS Build Tools C++: `{vs.get('status')}`",
        f"- GPU runtime: `{gpu.get('status')}`",
        f"- dx=1 readiness: `{dx1.get('dx1_readiness')}`",
        f"- dx=1 memory headroom ok: {dx1.get('dx1_memory_headroom_ok')}",
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
    write_text_retry(OUT_MD, "\n".join(lines) + "\n")


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
        ("build_chain_audit", "build_chain_audit.py"),
        ("citylbm_build_hash_stability_gate", "citylbm_build_hash_stability_gate.py"),
        ("citylbm_portable_toolchain_gate", "citylbm_portable_toolchain_gate.py"),
        ("plugin_identity_gate", "plugin_identity_gate.py"),
        ("citylbm_plugin_identity_component_gate", "citylbm_plugin_identity_component_gate.py"),
        ("citylbm_plugin_identity_binary_gate", "citylbm_plugin_identity_binary_gate.py"),
        ("citylbm_casee_postrun_audit_component_gate", "citylbm_casee_postrun_audit_component_gate.py"),
        ("citylbm_casee_postrun_audit_binary_gate", "citylbm_casee_postrun_audit_binary_gate.py"),
        ("rhino_gha_load_gate", "rhino_gha_load_gate.py"),
        ("citylbm_gha_install_audit", "citylbm_gha_install_audit.py"),
        ("casee_rhino_load_evidence_kit", "casee_rhino_load_evidence_kit.py"),
        ("rhino_gha_load_manifest_schema_gate", "rhino_gha_load_manifest_schema_gate.py"),
        ("casee_rhino_load_evidence_packet_gate", "casee_rhino_load_evidence_packet_gate.py"),
        ("manuscript_evidence_summary", "manuscript_evidence_summary.py"),
        ("vs_cpp_recovery_gate", "vs_cpp_recovery_gate.py"),
        ("vs_cpp_system_drive_space_gate", "vs_cpp_system_drive_space_gate.py"),
        ("vs_cpp_elevated_launcher_gate", "vs_cpp_elevated_launcher_gate.py"),
        ("casee_official_run_preflight", "casee_official_run_preflight.py"),
        ("citylbm_gpu_runtime_failfast_gate", "citylbm_gpu_runtime_failfast_gate.py"),
        ("casee_dx1_readiness_audit", "casee_dx1_readiness_audit.py"),
        ("casee_environment_recovery_runbook", "casee_environment_recovery_runbook.py"),
        ("casee_operational_recovery_dashboard", "casee_operational_recovery_dashboard.py"),
        ("casee_failure_mode_atlas", "casee_failure_mode_atlas.py"),
        ("casee_zcenter_rerun_consistency", "casee_zcenter_rerun_consistency.py"),
        ("casee_c002_longer_mean_audit", "casee_c002_longer_mean_audit.py"),
        ("casee_c003_zorigin_ablation_audit", "casee_c003_zorigin_ablation_audit.py"),
        ("casee_c004_dx3_low_cost_audit", "casee_c004_dx3_low_cost_audit.py"),
        ("casee_c005_decomposition_audit", "casee_c005_decomposition_audit.py"),
        ("casee_c008_c009_inlet_turbulence_audit", "casee_c008_c009_inlet_turbulence_audit.py"),
        ("casee_c014_residual_structure_audit", "casee_c014_residual_structure_audit.py"),
        ("casee_orphan_candidate_csv_audit", "casee_orphan_candidate_csv_audit.py"),
        ("casee_c016_residual_target_leakage_guard", "casee_c016_residual_target_leakage_guard.py"),
        ("casee_solver_run_provenance_ledger", "casee_solver_run_provenance_ledger.py"),
        ("casee_claim_support_gate", "casee_claim_support_gate.py"),
        ("casee_research_accuracy_gap_gate", "casee_research_accuracy_gap_gate.py"),
        ("casee_candidate_sweep_plan", "casee_candidate_sweep_plan.py"),
        ("casee_default_policy_gate", "casee_default_policy_gate.py"),
        ("casee_default_promotion_gate", "casee_default_promotion_gate.py"),
        ("casee_wall_followup_codegen_gate", "casee_wall_followup_codegen_gate.py"),
        ("casee_inlet_followup_codegen_gate", "casee_inlet_followup_codegen_gate.py"),
        ("casee_c016_codegen_gate", "casee_c016_codegen_gate.py"),
        ("casee_native_codegen_smoke_gate", "casee_native_codegen_smoke_gate.py"),
        ("casee_runbook_codegen_preflight", "casee_runbook_codegen_preflight.py"),
        ("citylbm_paper_results_packet", "citylbm_paper_results_packet.py"),
        ("citylbm_manifest_output_gate", "citylbm_manifest_output_gate.py"),
        ("citylbm_manifest_schema_gate", "citylbm_manifest_schema_gate.py"),
        ("casee_manuscript_results_table", "casee_manuscript_results_table.py"),
        ("casee_manuscript_section_pack", "casee_manuscript_section_pack.py"),
        ("casee_paper_results_figure", "casee_paper_results_figure.py"),
        ("github_release_publication_gate_pre_release_assets", "github_release_publication_gate.py"),
        ("casee_workspace_hygiene_gate_pre_release_assets", "casee_workspace_hygiene_gate.py"),
        ("artifact_index_pre_release_assets", "artifact_index.py"),
        ("casee_release_asset_manifest", "casee_release_asset_manifest.py"),
        ("casee_release_bundle_gate", "casee_release_bundle_gate.py"),
        ("github_release_publication_gate", "github_release_publication_gate.py"),
        ("casee_workspace_hygiene_gate", "casee_workspace_hygiene_gate.py"),
        ("citylbm_software_feedback_matrix", "citylbm_software_feedback_matrix.py"),
        ("artifact_index_pre_appendix", "artifact_index.py"),
        ("paper_appendix_generator", "paper_appendix_generator.py"),
        ("casee_blocker_remediation_plan", "casee_blocker_remediation_plan.py"),
        ("casee_next_experiment_runbook", "casee_next_experiment_runbook.py"),
        ("casee_postrun_official_audit_handoff", "casee_postrun_official_audit_handoff.py"),
        ("artifact_index", "artifact_index.py"),
        ("casee_release_asset_manifest_final", "casee_release_asset_manifest.py"),
        ("casee_release_bundle_gate_final", "casee_release_bundle_gate.py"),
        ("github_release_publication_gate_final", "github_release_publication_gate.py"),
        ("casee_workspace_hygiene_gate_final", "casee_workspace_hygiene_gate.py"),
        ("paper_evidence_gate", "paper_evidence_gate.py"),
        ("casee_publication_readiness_gate", "casee_publication_readiness_gate.py"),
        ("artifact_index_final", "artifact_index.py"),
    ]:
        if name == "casee_publication_readiness_gate":
            write_publication_gate_provisional_suite(steps)
        steps.append(run_command(name, [python, str(CASE_DIR / "tools" / script)]))
        if name == "build_chain_audit":
            steps.append(copy_release_gha())
            steps.append(stage_tracked_gha_for_grasshopper())
    steps.append(run_command("formal_release_gate_expected_block", [python, str(CASE_DIR / "tools" / "release_gate.py")], expect_release_gate_block=True))

    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    paper_gate = read_json(RESULTS_DIR / "casee_paper_evidence_gate.json")
    plugin_gate = read_json(RESULTS_DIR / "plugin_identity_gate.json")
    plugin_identity_component_gate = read_json(RESULTS_DIR / "citylbm_plugin_identity_component_gate.json")
    plugin_identity_binary_gate = read_json(RESULTS_DIR / "citylbm_plugin_identity_binary_gate.json")
    casee_postrun_audit_component_gate = read_json(RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.json")
    casee_postrun_audit_binary_gate = read_json(RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.json")
    rhino_gate = read_json(RESULTS_DIR / "rhino_gha_load_gate.json")
    gha_install_audit = read_json(RESULTS_DIR / "citylbm_gha_install_audit.json")
    rhino_evidence_kit = read_json(RESULTS_DIR / "casee_rhino_load_evidence_kit.json")
    rhino_manifest_schema_gate = read_json(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json")
    rhino_evidence_packet_gate = read_json(RESULTS_DIR / "casee_rhino_load_evidence_packet_gate.json")
    build_chain = read_json(RESULTS_DIR / "build_chain_manifest.json")
    build_hash_stability = read_json(RESULTS_DIR / "citylbm_build_hash_stability_gate.json")
    portable_toolchain_gate = read_json(RESULTS_DIR / "citylbm_portable_toolchain_gate.json")
    vs_cpp_recovery = read_json(RESULTS_DIR / "vs_cpp_recovery_gate.json")
    vs_cpp_system_drive_space = read_json(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json")
    vs_cpp_elevated_launcher = read_json(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    gpu_failfast = read_json(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json")
    dx1_readiness = read_json(RESULTS_DIR / "casee_dx1_readiness_audit.json")
    recovery = read_json(RESULTS_DIR / "casee_environment_recovery_runbook.json")
    operational_recovery_dashboard = read_json(RESULTS_DIR / "casee_operational_recovery_dashboard.json")
    failure_atlas = read_json(RESULTS_DIR / "casee_failure_mode_atlas.json")
    zcenter_rerun = read_json(RESULTS_DIR / "casee_zcenter_rerun_consistency.json")
    c002_longer_mean = read_json(RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    c003_zorigin_ablation = read_json(RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    c004_dx3_low_cost = read_json(RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    research_accuracy_gap = read_json(RESULTS_DIR / "casee_research_accuracy_gap_gate.json")
    candidate_sweep_plan = read_json(RESULTS_DIR / "casee_candidate_sweep_plan.json")
    wall_followup_codegen = read_json(RESULTS_DIR / "casee_wall_followup_codegen_gate.json")
    inlet_followup_codegen = read_json(RESULTS_DIR / "casee_inlet_followup_codegen_gate.json")
    c016_codegen = read_json(RESULTS_DIR / "casee_c016_codegen_gate.json")
    native_codegen_smoke = read_json(RESULTS_DIR / "casee_native_codegen_smoke_gate.json")
    runbook_codegen_preflight = read_json(RESULTS_DIR / "casee_runbook_codegen_preflight.json")
    c014_residual_structure = read_json(RESULTS_DIR / "casee_c014_residual_structure_audit.json")
    orphan_candidate_csv_audit = read_json(RESULTS_DIR / "casee_orphan_candidate_csv_audit.json")
    default_policy = read_json(RESULTS_DIR / "casee_default_policy_gate.json")
    default_promotion = read_json(RESULTS_DIR / "casee_default_promotion_gate.json")
    paper_results_packet = read_json(RESULTS_DIR / "citylbm_paper_results_packet.json")
    manifest_output_gate = read_json(RESULTS_DIR / "citylbm_manifest_output_gate.json")
    manifest_schema_gate = read_json(RESULTS_DIR / "citylbm_manifest_schema_gate.json")
    manuscript_results_table = read_json(RESULTS_DIR / "casee_manuscript_results_table.json")
    manuscript_section_pack = read_json(RESULTS_DIR / "casee_manuscript_section_pack.json")
    paper_results_figure = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    software_feedback_matrix = read_json(RESULTS_DIR / "citylbm_software_feedback_matrix.json")
    artifact_index = read_json(RESULTS_DIR / "casee_artifact_index.json")
    release_asset_manifest = read_json(RESULTS_DIR / "casee_release_asset_manifest.json")
    release_bundle = read_json(RESULTS_DIR / "casee_release_bundle_manifest.json")
    github_release_publication = read_json(RESULTS_DIR / "github_release_publication_gate.json")
    workspace_hygiene = read_json(RESULTS_DIR / "casee_workspace_hygiene_gate.json")
    postrun_handoff = read_json(RESULTS_DIR / "casee_postrun_official_audit_handoff.json")
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
        "citylbm_plugin_identity_component_gate": plugin_identity_component_gate,
        "citylbm_plugin_identity_binary_gate": plugin_identity_binary_gate,
        "citylbm_casee_postrun_audit_component_gate": casee_postrun_audit_component_gate,
        "citylbm_casee_postrun_audit_binary_gate": casee_postrun_audit_binary_gate,
        "rhino_gha_load_gate": rhino_gate,
        "citylbm_gha_install_audit": gha_install_audit,
        "casee_rhino_load_evidence_kit": rhino_evidence_kit,
        "rhino_gha_load_manifest_schema_gate": rhino_manifest_schema_gate,
        "casee_rhino_load_evidence_packet_gate": rhino_evidence_packet_gate,
        "build_chain_manifest": build_chain,
        "citylbm_build_hash_stability_gate": build_hash_stability,
        "citylbm_portable_toolchain_gate": portable_toolchain_gate,
        "vs_cpp_recovery_gate": vs_cpp_recovery,
        "vs_cpp_system_drive_space_gate": vs_cpp_system_drive_space,
        "vs_cpp_elevated_launcher_gate": vs_cpp_elevated_launcher,
        "casee_official_run_preflight": preflight,
        "citylbm_gpu_runtime_failfast_gate": gpu_failfast,
        "casee_dx1_readiness_audit": dx1_readiness,
        "casee_environment_recovery_runbook": recovery,
        "casee_operational_recovery_dashboard": operational_recovery_dashboard,
        "casee_failure_mode_atlas": failure_atlas,
        "casee_zcenter_rerun_consistency": zcenter_rerun,
        "casee_c002_longer_mean_audit": c002_longer_mean,
        "casee_c003_zorigin_ablation_audit": c003_zorigin_ablation,
        "casee_c004_dx3_low_cost_audit": c004_dx3_low_cost,
        "casee_c014_residual_structure_audit": c014_residual_structure,
        "casee_orphan_candidate_csv_audit": orphan_candidate_csv_audit,
        "casee_research_accuracy_gap_gate": research_accuracy_gap,
        "casee_candidate_sweep_plan": candidate_sweep_plan,
        "casee_wall_followup_codegen_gate": wall_followup_codegen,
        "casee_inlet_followup_codegen_gate": inlet_followup_codegen,
        "casee_c016_codegen_gate": c016_codegen,
        "casee_native_codegen_smoke_gate": native_codegen_smoke,
        "casee_runbook_codegen_preflight": runbook_codegen_preflight,
        "casee_default_policy_gate": default_policy,
        "casee_default_promotion_gate": default_promotion,
        "citylbm_paper_results_packet": paper_results_packet,
        "citylbm_manifest_output_gate": manifest_output_gate,
        "citylbm_manifest_schema_gate": manifest_schema_gate,
        "casee_manuscript_results_table": manuscript_results_table,
        "casee_manuscript_section_pack": manuscript_section_pack,
        "casee_paper_results_figure": paper_results_figure,
        "citylbm_software_feedback_matrix": software_feedback_matrix,
        "artifact_index": artifact_index,
        "casee_release_asset_manifest": release_asset_manifest,
        "casee_release_bundle": release_bundle,
        "github_release_publication_gate": github_release_publication,
        "casee_workspace_hygiene_gate": workspace_hygiene,
        "casee_postrun_official_audit_handoff": postrun_handoff,
    }
    write_text_retry(OUT_JSON, json.dumps(payload, indent=2))
    write_markdown(payload)
    print(json.dumps({"suite_passed": suite_passed, "out_json": str(OUT_JSON)}, indent=2))
    return 0 if suite_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
