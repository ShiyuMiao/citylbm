#!/usr/bin/env python3
"""Map Experiments 1-3 evidence into CityLBM software-feedback decisions."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASEE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASEE_DIR / "results"
CASEA_RESULTS = ROOT / "docs" / "experiments" / "casea" / "results"
PAPER_DRAFTS = ROOT / "academic-paper-writer" / "paper-drafts"
FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
POSTRUN_AUDIT_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "CaseEPostRunAuditComponent.cs"
REPRO_SUITE = CASEE_DIR / "tools" / "reproducibility_suite.py"
RELEASE_GATE_SCRIPT = CASEE_DIR / "tools" / "casee_audit.py"

OUT_JSON = RESULTS_DIR / "citylbm_software_feedback_matrix.json"
OUT_CSV = RESULTS_DIR / "citylbm_software_feedback_matrix.csv"
OUT_MD = RESULTS_DIR / "citylbm_software_feedback_matrix.md"

FIELDNAMES = [
    "feedback_id",
    "experiment",
    "finding",
    "evidence_type",
    "source_paths",
    "decision_class",
    "citylbm_status",
    "implementation_evidence",
    "default_setting_allowed",
    "paper_use",
    "limitations",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def exists_all(paths: Iterable[Path]) -> bool:
    return all(path.exists() for path in paths)


def row(
    *,
    feedback_id: str,
    experiment: str,
    finding: str,
    evidence_type: str,
    source_paths: Iterable[Path],
    decision_class: str,
    citylbm_status: str,
    implementation_evidence: str,
    default_setting_allowed: bool,
    paper_use: str,
    limitations: str,
) -> Dict[str, Any]:
    paths = list(source_paths)
    return {
        "feedback_id": feedback_id,
        "experiment": experiment,
        "finding": finding,
        "evidence_type": evidence_type,
        "source_paths": "; ".join(rel(path) for path in paths),
        "source_paths_exist": exists_all(paths),
        "decision_class": decision_class,
        "citylbm_status": citylbm_status,
        "implementation_evidence": implementation_evidence,
        "default_setting_allowed": default_setting_allowed,
        "paper_use": paper_use,
        "limitations": limitations,
    }


def exp3_claim(rows: List[Dict[str, str]], claim_id: str) -> Dict[str, str]:
    for item in rows:
        if item.get("claim_or_asset") == claim_id:
            return item
    return {}


def build_rows() -> List[Dict[str, Any]]:
    fluidx = read_text(FLUIDX)
    run_component = read_text(RUN_COMPONENT)
    postrun_audit_component = read_text(POSTRUN_AUDIT_COMPONENT)
    suite = read_text(REPRO_SUITE)
    audit = read_text(RELEASE_GATE_SCRIPT)
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    default_policy = read_json(RESULTS_DIR / "casee_default_policy_gate.json")
    paper_packet = read_json(RESULTS_DIR / "citylbm_paper_results_packet.json")
    manifest_output = read_json(RESULTS_DIR / "citylbm_manifest_output_gate.json")
    manuscript_table = read_json(RESULTS_DIR / "casee_manuscript_results_table.json")
    section_pack = read_json(RESULTS_DIR / "casee_manuscript_section_pack.json")
    paper_figure = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    build_chain = read_json(RESULTS_DIR / "build_chain_manifest.json")
    dx1_readiness = read_json(RESULTS_DIR / "casee_dx1_readiness_audit.json")
    candidate_sweep = read_json(RESULTS_DIR / "casee_candidate_sweep_plan.json")
    wall_followup_codegen = read_json(RESULTS_DIR / "casee_wall_followup_codegen_gate.json")
    postrun_handoff = read_json(RESULTS_DIR / "casee_postrun_official_audit_handoff.json")
    zcenter_rerun = read_json(RESULTS_DIR / "casee_zcenter_rerun_consistency.json")
    c002_longer_mean = read_json(RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    c003_zorigin_ablation = read_json(RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    c004_dx3_low_cost = read_json(RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    c005_decomposition = read_json(RESULTS_DIR / "casee_c005_decomposition_audit.json")
    c008_c009_inlet = read_json(RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json")
    c014_residual = read_json(RESULTS_DIR / "casee_c014_residual_structure_audit.json")
    orphan_candidate_csv_audit = read_json(RESULTS_DIR / "casee_orphan_candidate_csv_audit.json")
    c016_leakage_guard = read_json(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json")
    solver_ledger = read_json(RESULTS_DIR / "casee_solver_run_provenance_ledger.json")
    claim_support = read_json(RESULTS_DIR / "casee_claim_support_gate.json")
    release_assets = read_json(RESULTS_DIR / "casee_release_asset_manifest.json")
    release_bundle = read_json(RESULTS_DIR / "casee_release_bundle_manifest.json")
    github_publication = read_json(RESULTS_DIR / "github_release_publication_gate.json")
    workspace_hygiene = read_json(RESULTS_DIR / "casee_workspace_hygiene_gate.json")
    vs_cpp_recovery = read_json(RESULTS_DIR / "vs_cpp_recovery_gate.json")
    vs_cpp_system_drive_space = read_json(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json")
    vs_cpp_elevated_launcher = read_json(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json")
    operational_recovery_dashboard = read_json(RESULTS_DIR / "casee_operational_recovery_dashboard.json")
    build_hash_stability = read_json(RESULTS_DIR / "citylbm_build_hash_stability_gate.json")
    gha_install = read_json(RESULTS_DIR / "citylbm_gha_install_audit.json")
    rhino_evidence_kit = read_json(RESULTS_DIR / "casee_rhino_load_evidence_kit.json")
    rhino_manifest_schema_gate = read_json(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json")
    identity_component_gate = read_json(RESULTS_DIR / "citylbm_plugin_identity_component_gate.json")
    identity_binary_gate = read_json(RESULTS_DIR / "citylbm_plugin_identity_binary_gate.json")
    postrun_audit_component_gate = read_json(RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.json")
    postrun_audit_binary_gate = read_json(RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.json")
    portable_toolchain_gate = read_json(RESULTS_DIR / "citylbm_portable_toolchain_gate.json")
    gpu_failfast_gate = read_json(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json")
    exp3_rows = read_csv(PAPER_DRAFTS / "experiment3_claim_verification.csv")

    metrics = release_gate.get("metrics") or {}
    rows: List[Dict[str, Any]] = []

    rows.append(
        row(
            feedback_id="SF001",
            experiment="Experiment 1 / AIJ Case A",
            finding="Case A smoke regression guards the Rhino/GH -> FluidX3D -> VTK workflow but is not accuracy validation.",
            evidence_type="newly_run",
            source_paths=[
                CASEA_RESULTS / "casea_smoke_regression.json",
                CASEA_RESULTS / "casea_vtk_manifest.csv",
                CASEE_DIR / "tools" / "reproducibility_suite.py",
            ],
            decision_class="default_quality_gate",
            citylbm_status="implemented_as_release_gate_requirement"
            if (release_gate.get("checks") or {}).get("casea_smoke_regression_passed") is True
            and "casea_smoke_regression_passed" in audit
            else "missing_release_gate_integration",
            implementation_evidence="release_gate and reproducibility_suite require Case A smoke regression before formal release.",
            default_setting_allowed=True,
            paper_use="Use as workflow non-regression evidence.",
            limitations="Do not use as wind-field accuracy validation.",
        )
    )

    rows.append(
        row(
            feedback_id="SF002",
            experiment="Experiment 2 / AIJ Case E",
            finding=(
                f"Official z=2 m validation remains negative: MAE={metrics.get('mae_pp')} pp, "
                f"R2={metrics.get('r2')}, Pearson={metrics.get('pearson')}."
            ),
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "release_gate.json",
                RESULTS_DIR / "casee_metrics.csv",
                RESULTS_DIR / "casee_validation_report.md",
            ],
            decision_class="blocked_default_accuracy_upgrade",
            citylbm_status="formal_release_blocked" if release_gate.get("formal_release_allowed") is False else "formal_release_allowed",
            implementation_evidence="release_gate.json and paper_evidence_gate keep formal v0.4.0 blocked.",
            default_setting_allowed=False,
            paper_use="Use as negative validation and motivation for limitations.",
            limitations="Cannot claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF003",
            experiment="Experiment 2 / AIJ Case E",
            finding="The formal Case E protocol must remain z=2 m, 80 ac+N probes, and raw_trilinear sampling.",
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "casee_preset.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
                FLUIDX,
            ],
            decision_class="formal_protocol_default",
            citylbm_status="implemented" if default_policy.get("default_policy_gate_passed") is True else "blocked",
            implementation_evidence="SimulationSettings.FormalSamplingMode defaults to raw_trilinear and manifests block diagnostic substitutes.",
            default_setting_allowed=True,
            paper_use="Use as method/protocol policy.",
            limitations="Protocol correctness alone is not accuracy evidence.",
        )
    )

    rows.append(
        row(
            feedback_id="SF004",
            experiment="Experiment 2 / AIJ Case E",
            finding="Diagnostic nu_lbm sensitivity is useful for investigation but has not produced a formal official z=2 m pass.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_ground_nu_diagnostic_comparison.csv",
            ],
            decision_class="diagnostic_switch",
            citylbm_status="implemented_default_off"
            if "Diagnostic LBM Nu Override" in run_component and "DiagnosticNuLbmOverride { get; set; } = 0.0" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence="Grasshopper nuLBM input defaults to 0 and SimulationSettings defaults to 0.0.",
            default_setting_allowed=False,
            paper_use="Use as sensitivity diagnostic evidence.",
            limitations="Do not promote tuned nu_lbm as a default accuracy model.",
        )
    )

    rows.append(
        row(
            feedback_id="SF005",
            experiment="Experiment 2 / AIJ Case E",
            finding="Vertical-origin and probe sampling diagnostics expose near-wall/protocol sensitivity but remain non-formal.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv",
                RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv",
            ],
            decision_class="diagnostic_switch",
            citylbm_status="implemented_default_off"
            if "Diagnostic Z Origin Offset" in run_component
            and "DiagnosticZOriginOffsetM { get; set; } = 0.0" in fluidx
            and "z_plus_half_allowed_as_formal_result" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence="Grasshopper zOff defaults to 0 and run manifests forbid z_plus_half as formal output.",
            default_setting_allowed=False,
            paper_use="Use for near-wall/probe-protocol limitations.",
            limitations="Do not report z_plus_half, vertical_valid_above, or z-offset results as official validation.",
        )
    )

    rows.append(
        row(
            feedback_id="SF006",
            experiment="Experiment 2 / AIJ Case E",
            finding="The next official Case E run is blocked by runtime and load-identity gates.",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "casee_official_run_preflight.json",
                RESULTS_DIR / "casee_environment_recovery_runbook.json",
                RESULTS_DIR / "rhino_gha_load_gate.json",
            ],
            decision_class="blocked_followup_run",
            citylbm_status="blocked_until_external_recovery"
            if preflight.get("official_followup_run_allowed") is False
            else "ready_for_next_official_run",
            implementation_evidence=f"blocked_gates={','.join(preflight.get('blocked_gates', []))}",
            default_setting_allowed=False,
            paper_use="Use to explain why no new official long run is reported in this rc.",
            limitations="Operational readiness evidence only; not solver-output evidence.",
        )
    )

    rows.append(
        row(
            feedback_id="SF007",
            experiment="Experiment 3 / TUM2TWIN digital-twin application",
            finding=exp3_claim(exp3_rows, "module_claim_M1").get(
                "paper_use",
                "Digital-twin layers should remain separated into visual, semantic/collision, and CFD/LBM inputs.",
            ),
            evidence_type=exp3_claim(exp3_rows, "module_claim_M1").get("evidence_type", "preexisting_artifact"),
            source_paths=[
                PAPER_DRAFTS / "experiment3_claim_verification.csv",
                ROOT / "releases" / "v0.2.0" / "package" / "validation_experiments" / "Experiment3_TUM2TWIN_DigitalTwin_DesignApplication",
            ],
            decision_class="application_workflow_policy",
            citylbm_status="paper_ready_workflow_guidance",
            implementation_evidence="Experiment 3 archive and claim verification document the layer separation policy.",
            default_setting_allowed=True,
            paper_use="Use as CityLBM-compatible digital-twin workflow evidence.",
            limitations="Does not prove Case E benchmark accuracy or CityLBM-GH end-to-end execution for Experiment 3.",
        )
    )

    rows.append(
        row(
            feedback_id="SF008",
            experiment="Experiment 3 / TUM2TWIN digital-twin application",
            finding=exp3_claim(exp3_rows, "module_claim_R3").get(
                "paper_use",
                "Morphology variables are screening descriptors rather than high-accuracy predictors.",
            ),
            evidence_type=exp3_claim(exp3_rows, "module_claim_R3").get("evidence_type", "preexisting_artifact"),
            source_paths=[
                PAPER_DRAFTS / "experiment3_claim_verification.csv",
                RESULTS_DIR / "citylbm_paper_results_packet.json",
            ],
            decision_class="paper_interpretation_layer",
            citylbm_status="paper_ready_with_boundary"
            if (paper_packet.get("summary") or {}).get("paper_results_packet_passed") is True
            else "blocked",
            implementation_evidence="citylbm_paper_results_packet keeps Experiment 3 screening evidence separate from Case E accuracy evidence.",
            default_setting_allowed=False,
            paper_use="Use as design-screening interpretation evidence.",
            limitations="Sample-internal screening only; no field validation or annual comfort compliance.",
        )
    )

    rows.append(
        row(
            feedback_id="SF009",
            experiment="CityLBM traceability layer",
            finding="Run Simulation exposes the generated citylbm_run_manifest.json path as a Grasshopper output for direct reviewer tracing.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if manifest_output.get("manifest_output_gate_passed") is True
            and 'AddTextParameter("Manifest Path", "Man"' in run_component
            else "blocked",
            implementation_evidence="Manifest Path output points to citylbm_run_manifest.json and the manifest records formal/diagnostic claim boundaries.",
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence for run manifests and protocol metadata.",
            limitations="Traceability output only; does not prove Rhino loaded the new GHA or improve official z=2 m accuracy.",
        )
    )

    rows.append(
        row(
            feedback_id="SF010",
            experiment="Experiment 2 / AIJ Case E paper-readiness layer",
            finding="Run manifests and manuscript result rows now record allowed paper uses and forbidden accuracy claims.",
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_manuscript_results_table.json",
            ],
            decision_class="paper_traceability_output",
            citylbm_status="implemented"
            if manifest_output.get("manifest_output_gate_passed") is True
            and (manuscript_table.get("summary") or {}).get("manuscript_results_table_passed") is True
            and "paper_readiness" in fluidx
            else "blocked",
            implementation_evidence="citylbm_run_manifest.json includes paper_readiness fields and casee_manuscript_results_table separates formal and diagnostic rows.",
            default_setting_allowed=True,
            paper_use="Use to move Case E results into manuscript tables without overstating formal accuracy.",
            limitations="Paper-readiness metadata does not change the official z=2 m metric or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF011",
            experiment="Experiment 2 / AIJ Case E paper-figure layer",
            finding="The manuscript result table is exported as an editable SVG/PNG/source-CSV figure bundle with QA checks.",
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "tools" / "casee_paper_results_figure.py",
                RESULTS_DIR / "casee_paper_results_figure_qa.json",
                RESULTS_DIR / "casee_paper_results_figure.svg",
                RESULTS_DIR / "casee_paper_results_figure_source.csv",
            ],
            decision_class="paper_figure_output",
            citylbm_status="implemented"
            if paper_figure.get("figure_gate_passed") is True
            and paper_figure.get("formal_accuracy_claim_supported") is False
            else "blocked",
            implementation_evidence="casee_paper_results_figure_qa.json verifies source CSV, editable SVG, PNG export, and negative-validation claim boundary.",
            default_setting_allowed=True,
            paper_use="Use as a paper figure for negative validation and limitations only.",
            limitations="Figure output does not add CFD results, improve official z=2 m metrics, or justify formal accuracy claims.",
        )
    )

    rows.append(
        row(
            feedback_id="SF012",
            experiment="Experiment 2 / AIJ Case E manifest gate contract",
            finding="Generated run manifests now encode the formal v0.4.0 accuracy-gate contract and keep manifest-only accuracy claims blocked.",
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if "formal_accuracy_gate" in fluidx
            and "formal_accuracy_claim_allowed_from_manifest_alone" in fluidx
            and manifest_output.get("manifest_output_gate_passed") is True
            and default_policy.get("default_policy_gate_passed") is True
            else "blocked",
            implementation_evidence="WriteRunManifest emits formal_accuracy_gate with required official protocol, release-gate, Case A, Rhino/GHA, R2/Pearson, and diagnostic-substitute constraints.",
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence that each generated case records the formal release-gate contract.",
            limitations="Manifest-gate metadata does not add solver output, improve official z=2 m metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF013",
            experiment="Experiment 2 / AIJ Case E Grasshopper claim boundary",
            finding="Run Simulation now exposes a Claim Gate output so users can see the formal accuracy boundary beside run status and manifest path.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if 'AddTextParameter("Claim Gate", "Gate"' in run_component
            and "ClaimGateSummary" in run_component
            and manifest_output.get("manifest_output_gate_passed") is True
            and default_policy.get("default_policy_gate_passed") is True
            else "blocked",
            implementation_evidence="RunSimulationComponent adds Claim Gate output index 7 and sets it in generate, deploy, full-auto, async, cancelled, running, and no-run states.",
            default_setting_allowed=True,
            paper_use="Use as software misuse-prevention evidence: successful execution is separated from formal benchmark accuracy.",
            limitations="UI claim-boundary text does not add solver output, improve official z=2 m metrics, or prove Rhino loaded the new GHA.",
        )
    )

    rows.append(
        row(
            feedback_id="SF014",
            experiment="Experiment 2 / AIJ Case E manuscript prose layer",
            finding="The generated section pack converts gated Case E rows into Methods, Results, Diagnostics, Limitations, Software implications, and Release-boundary prose with explicit evidence notes.",
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "tools" / "casee_manuscript_section_pack.py",
                RESULTS_DIR / "casee_manuscript_section_pack.json",
                RESULTS_DIR / "casee_manuscript_section_pack_qa.md",
                PAPER_DRAFTS / "casee_v04_manuscript_section_pack_en.md",
            ],
            decision_class="paper_traceability_output",
            citylbm_status="implemented"
            if section_pack.get("section_pack_passed") is True
            and section_pack.get("formal_accuracy_claim_supported") is False
            and section_pack.get("formal_release_allowed") is False
            else "blocked",
            implementation_evidence="casee_manuscript_section_pack.py emits a claim-safe English manuscript section pack and QA manifest from the gated results table and release gate.",
            default_setting_allowed=True,
            paper_use="Use as ready-to-edit manuscript prose for negative validation, diagnostic interpretation, limitations, and release-boundary text.",
            limitations="Generated prose does not add CFD output, improve official z=2 m metrics, or support a formal predictive-accuracy claim.",
        )
    )

    build_vs = build_chain.get("visual_studio_build_tools_2022_cpp") or {}
    build_gpu = build_chain.get("gpu_runtime") or {}
    build_script = build_chain.get("citylbm_build_script") or {}
    rows.append(
        row(
            feedback_id="SF015",
            experiment="Build-chain recovery / Case E follow-up readiness",
            finding=(
                "The current build-chain audit records .NET and FluidX3D as available, GPU runtime as "
                f"{build_gpu.get('status')}, and VS Build Tools C++ as {build_vs.get('status')} after a winget "
                "BuildTools attempt exited 1602 with UAC-related bootstrapper evidence."
            ),
            evidence_type="newly_run",
            source_paths=[
                ROOT / "CityLBM" / "build.ps1",
                CASEE_DIR / "tools" / "build_chain_audit.py",
                RESULTS_DIR / "build_chain_manifest.json",
                RESULTS_DIR / "build_chain_manifest.md",
                RESULTS_DIR / "casee_official_run_preflight.json",
            ],
            decision_class="blocked_followup_run",
            citylbm_status="blocked_vs_cpp_build_tools"
            if build_vs.get("status") != "ready"
            else "build_chain_ready",
            implementation_evidence="build_chain_audit.py now captures latest winget/VS installer logs, vswhere VC detection, GPU status, .NET status, FluidX3D binary status, and disk state.",
            default_setting_allowed=False,
            paper_use="Use as environment/build-chain evidence explaining why another full software/native validation loop still requires manual VS C++ recovery.",
            limitations="Build-chain readiness does not add CFD output, improve official z=2 m metrics, prove Rhino loaded the new GHA, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF033",
            experiment="CityLBM portable plugin build script",
            finding=(
                "The CityLBM build script now supports -DotNetPath, CITYLBM_DOTNET, the audited local "
                "E: build-chain .NET SDK, and -NoPause so the Grasshopper plugin can be rebuilt on the new computer "
                "even when dotnet is not on PATH."
            ),
            evidence_type="newly_run",
            source_paths=[
                ROOT / "CityLBM" / "build.ps1",
                CASEE_DIR / "tools" / "build_chain_audit.py",
                RESULTS_DIR / "build_chain_manifest.json",
            ],
            decision_class="portable_plugin_build_script",
            citylbm_status="implemented_portable_plugin_build"
            if build_script.get("status") == "ready"
            and build_script.get("supports_portable_dotnet") is True
            and build_script.get("supports_no_pause") is True
            else "portable_plugin_build_missing_or_failed",
            implementation_evidence=(
                f"build_script_status={build_script.get('status')}; "
                f"smoke_returncode={(build_script.get('smoke_build') or {}).get('returncode')}; "
                f"packaged_gha_found={((build_script.get('packaged_gha') or {}).get('found'))}"
            ),
            default_setting_allowed=True,
            paper_use="Use as reproducible software-build evidence for the CityLBM plugin package.",
            limitations="Plugin build reproducibility only; it does not install VS C++ Build Tools, recover GPU runtime, add CFD output, or improve official Case E metrics.",
        )
    )

    dx1_summary = dx1_readiness.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF016",
            experiment="Experiment 2 / AIJ Case E dx=1 follow-up readiness",
            finding=(
                "The dx=1 m high-resolution official follow-up is a high-risk long-run candidate: "
                f"readiness={dx1_summary.get('dx1_readiness')}, "
                f"memory_headroom_ok={dx1_summary.get('dx1_memory_headroom_ok')}, "
                f"moderate required per GPU={dx1_summary.get('generator_moderate_required_per_gpu_gib')} GiB, "
                f"minimum free GPU memory={dx1_summary.get('gpu_min_free_gib')} GiB."
            ),
            evidence_type=str(dx1_readiness.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_dx1_readiness_audit.py",
                RESULTS_DIR / "casee_dx1_readiness_audit.json",
                RESULTS_DIR / "casee_dx1_readiness_audit.md",
                RESULTS_DIR / "casee_dx1_readiness_audit.csv",
            ],
            decision_class="blocked_followup_run",
            citylbm_status="blocked_until_user_confirmed_dx1_dry_run"
            if dx1_summary.get("dx1_memory_headroom_ok") is not True
            else "ready_for_user_confirmed_dx1_dry_run",
            implementation_evidence="casee_dx1_readiness_audit.py records the audited dx=1 command, generated-domain dimensions, GPU free memory, memory scenarios, and no-run claim boundary.",
            default_setting_allowed=False,
            paper_use="Use as high-resolution follow-up feasibility and limitations evidence.",
            limitations="Readiness evidence only; no dx=1 solver output, no official z=2 m metric improvement, and no mesh-independence claim.",
        )
    )

    rows.append(
        row(
            feedback_id="SF017",
            experiment="Experiment 2 / AIJ Case E wall and roughness follow-up",
            finding=(
                "Near-wall underprediction and solid-corner diagnostics justify a default-off "
                "wall/roughness follow-up interface, but the official z=2 m raw_trilinear metric "
                "has not improved enough to promote any wall model as a default accuracy setting."
            ),
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_failure_mode_atlas.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
            ],
            decision_class="diagnostic_switch",
            citylbm_status="implemented_default_off"
            if "Diagnostic Wall Model" in run_component
            and "Diagnostic Roughness Length" in run_component
            and "DiagnosticWallModel" in fluidx
            and "DiagnosticRoughnessLengthM { get; set; } = 0.0" in fluidx
            and "diagnostic_wall_model_allowed_as_default_accuracy_model" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence="Grasshopper wallModel defaults to none, z0Wall defaults to 0.0, generated setup.cpp records audit constants only, and run manifests block default accuracy promotion.",
            default_setting_allowed=False,
            paper_use="Use as software-feedback evidence that Case E diagnostics were converted into controlled follow-up interfaces.",
            limitations="No wall-model or roughness setting is a formal validation result until completed official z=2 m raw_trilinear runs pass the release gate.",
        )
    )

    rows.append(
        row(
            feedback_id="SF018",
            experiment="Experiment 2 / AIJ Case E manifest schema traceability",
            finding=(
                "Generated run manifests need a stable reader-facing schema so Case E protocol fields, "
                "diagnostic substitute blockers, and paper-forbidden claim classes can be audited without "
                "reinterpreting solver logs."
            ),
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "tools" / "citylbm_manifest_schema_gate.py",
                RESULTS_DIR / "citylbm_manifest_schema_gate.json",
                RESULTS_DIR / "citylbm_manifest_schema_gate.md",
                FLUIDX,
                RUN_COMPONENT,
            ],
            decision_class="software_traceability_gate",
            citylbm_status="implemented_schema_gate",
            implementation_evidence="citylbm_manifest_schema_gate.py verifies required manifest sections, official Case E contract fields, diagnostic blockers, wall/roughness default-safety fields, and paper-forbidden claims.",
            default_setting_allowed=False,
            paper_use="Use as reviewer-facing manifest schema and claim-boundary evidence.",
            limitations="Schema traceability does not add CFD output, improve official z=2 m metrics, or permit a formal accuracy claim.",
        )
    )

    rows.append(
        row(
            feedback_id="SF020",
            experiment="Experiment 2 / AIJ Case E z-center rerun",
            finding=(
                "A newly-run 48000-step rerun of the currently compiled z-center Case E setup reproduced the same "
                "official z=2 m raw_trilinear failure metric, so repeating the baseline is not an accuracy-improvement path."
            ),
            evidence_type=str(zcenter_rerun.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_zcenter_rerun_consistency.py",
                RESULTS_DIR / "casee_zcenter_rerun_consistency.json",
                RESULTS_DIR / "casee_zcenter_rerun_consistency.md",
                Path(str((zcenter_rerun.get("rerun_csv") or {}).get("path", ""))),
                Path(str((zcenter_rerun.get("rerun_log") or {}).get("path", ""))),
            ],
            decision_class="rerun_reproducibility_guard",
            citylbm_status="baseline_failure_reproduced"
            if zcenter_rerun.get("status") == "passed_reproduced_failed_metric"
            else "missing_or_inconsistent_rerun",
            implementation_evidence=(
                f"log_completed_48000={zcenter_rerun.get('log_completed_48000')}; "
                f"csv_sha256_equal={zcenter_rerun.get('csv_sha256_equal')}; "
                f"r2={(zcenter_rerun.get('rerun_metrics') or {}).get('r2')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as reproducibility evidence that the current best compiled diagnostic repeats the negative official z=2 m result.",
            limitations="Does not improve accuracy, does not support formal v0.4.0, and does not justify promoting diagnostic settings.",
        )
    )

    rows.append(
        row(
            feedback_id="SF021",
            experiment="Experiment 2 / AIJ Case E C002 longer mean",
            finding=(
                "The completed 96000-step C002 longer-time-mean candidate worsened the official z=2 m raw_trilinear metric, "
                "so longer averaging alone should not be promoted as a CityLBM accuracy fix."
            ),
            evidence_type=str(c002_longer_mean.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c002_longer_mean_audit.py",
                RESULTS_DIR / "casee_c002_longer_mean_audit.json",
                RESULTS_DIR / "casee_c002_longer_mean_audit.md",
                Path(str((c002_longer_mean.get("candidate_csv") or {}).get("path", ""))),
                Path(str((c002_longer_mean.get("run_log") or {}).get("path", ""))),
            ],
            decision_class="completed_candidate_no_default_promotion",
            citylbm_status="candidate_completed_no_improvement"
            if c002_longer_mean.get("status") == "completed_no_improvement"
            else "candidate_audit_missing_or_improved_but_blocked",
            implementation_evidence=(
                f"pass_condition_met={c002_longer_mean.get('pass_condition_met')}; "
                f"r2={(c002_longer_mean.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_r2={(c002_longer_mean.get('metric_delta_vs_baseline') or {}).get('r2')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as candidate-run evidence that longer time averaging did not solve the official z=2 m accuracy failure.",
            limitations="Single candidate run; useful for narrowing the failure mode, not for formal accuracy or mesh-independence claims.",
        )
    )

    rows.append(
        row(
            feedback_id="SF022",
            experiment="Experiment 2 / AIJ Case E C003 z-origin ablation",
            finding=(
                "The completed C003 no-z-center ablation worsened the official z=2 m raw_trilinear metric relative to "
                "the z-center baseline, so z-origin alignment remains a diagnostic sensitivity rather than a validated default model."
            ),
            evidence_type=str(c003_zorigin_ablation.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c003_zorigin_ablation_audit.py",
                RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json",
                RESULTS_DIR / "casee_c003_zorigin_ablation_audit.md",
                Path(str((c003_zorigin_ablation.get("candidate_csv") or {}).get("path", ""))),
                Path(str((c003_zorigin_ablation.get("run_log") or {}).get("path", ""))),
            ],
            decision_class="diagnostic_ablation_no_default_promotion",
            citylbm_status="zorigin_sensitivity_confirmed"
            if c003_zorigin_ablation.get("status") == "completed_ablation_supports_zorigin_sensitivity"
            else "zorigin_ablation_missing_or_inconclusive",
            implementation_evidence=(
                f"pass_condition_met={c003_zorigin_ablation.get('pass_condition_met')}; "
                f"r2={(c003_zorigin_ablation.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_r2_vs_zcenter={(c003_zorigin_ablation.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}; "
                f"consistent_with_preexisting_no_zcenter={c003_zorigin_ablation.get('consistent_with_preexisting_no_zcenter')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as ablation evidence that z-origin placement affects near-wall/probe-protocol metrics.",
            limitations="Single ablation run; it worsens the formal metric and cannot support formal v0.4.0 or a default z-origin model.",
        )
    )

    rows.append(
        row(
            feedback_id="SF023",
            experiment="Experiment 2 / AIJ Case E C004 dx=3 control",
            finding=(
                "The completed C004 dx=3 low-cost control kept positive Pearson correlation but worsened MAE and R2, "
                "so it is useful as a quick protocol/direction regression rather than an accuracy default."
            ),
            evidence_type=str(c004_dx3_low_cost.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c004_dx3_low_cost_audit.py",
                RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json",
                RESULTS_DIR / "casee_c004_dx3_low_cost_audit.md",
                Path(str((c004_dx3_low_cost.get("candidate_csv") or {}).get("path", ""))),
                Path(str((c004_dx3_low_cost.get("run_log") or {}).get("path", ""))),
            ],
            decision_class="low_cost_regression_no_default_promotion",
            citylbm_status="dx3_control_completed_positive_correlation"
            if c004_dx3_low_cost.get("status") == "completed_low_cost_positive_correlation"
            else "dx3_control_missing_or_warning",
            implementation_evidence=(
                f"pass_condition_met={c004_dx3_low_cost.get('pass_condition_met')}; "
                f"manifest_protocol_ok={c004_dx3_low_cost.get('manifest_protocol_ok')}; "
                f"r2={(c004_dx3_low_cost.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_r2_vs_zcenter={(c004_dx3_low_cost.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as low-cost regression evidence that the wind-direction/protocol chain remains positively correlated at dx=3.",
            limitations="R2 remains negative and worse than the current baseline; this does not prove accuracy or mesh independence.",
        )
    )

    rows.append(
        row(
            feedback_id="SF024",
            experiment="Experiment 2 / AIJ Case E C005 domain decomposition",
            finding=(
                "The completed C005 dx=2 m 4x1x1 domain-decomposition ablation improved MAE and R2 versus the "
                "z-center baseline, but R2 stayed negative, Pearson decreased, and reproducibility-consistency thresholds failed."
            ),
            evidence_type=str(c005_decomposition.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c005_decomposition_audit.py",
                RESULTS_DIR / "casee_c005_decomposition_audit.json",
                RESULTS_DIR / "casee_c005_decomposition_audit.md",
                Path(str((c005_decomposition.get("candidate_csv") or {}).get("path", ""))),
                Path(str((c005_decomposition.get("run_log") or {}).get("path", ""))),
            ],
            decision_class="runtime_decomposition_sensitivity_no_default_promotion",
            citylbm_status="decomposition_sensitivity_detected"
            if c005_decomposition.get("status") == "completed_decomposition_sensitivity_warning"
            else "decomposition_audit_missing_or_inconclusive",
            implementation_evidence=(
                f"pass_condition_met={c005_decomposition.get('pass_condition_met')}; "
                f"manifest_protocol_ok={c005_decomposition.get('manifest_protocol_ok')}; "
                f"mae={(c005_decomposition.get('candidate_metrics') or {}).get('mae_pp')}; "
                f"r2={(c005_decomposition.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_r2_vs_zcenter={(c005_decomposition.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as runtime/decomposition sensitivity evidence and as a limited negative diagnostic improvement result.",
            limitations="Single decomposition ablation; R2 remains negative and consistency thresholds failed, so it cannot support formal v0.4.0 or default promotion.",
        )
    )

    inlet_best = c008_c009_inlet.get("best_candidate") or {}
    inlet_metrics = inlet_best.get("candidate_metrics") or {}
    inlet_delta = inlet_best.get("delta_vs_zcenter_baseline") or {}
    rows.append(
        row(
            feedback_id="SF025",
            experiment="Experiment 2 / AIJ Case E C008-C015 inlet turbulence and SGS ablation",
            finding=(
                "The C008-C015 AF-k synthetic full-plane inlet and no-SGS ablation candidates produced the largest official-height improvement so far, "
                f"with best MAE={inlet_metrics.get('mae_pp')} pp, R2={inlet_metrics.get('r2')}, and Pearson={inlet_metrics.get('pearson')}, "
                "but R2 remained negative."
            ),
            evidence_type=str(c008_c009_inlet.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "generate_native_casee.py",
                CASEE_DIR / "tools" / "casee_c008_c009_inlet_turbulence_audit.py",
                RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json",
                RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.md",
                Path(str((inlet_best.get("csv") or {}).get("path", ""))),
                Path(str((inlet_best.get("run_log") or {}).get("path", ""))),
            ],
            decision_class="inlet_turbulence_diagnostic_no_default_promotion",
            citylbm_status="inlet_turbulence_candidate_improved_but_blocked"
            if c008_c009_inlet.get("status") == "completed_inlet_turbulence_improved_but_negative_r2"
            and "Diagnostic Inlet Turbulence Mode" in run_component
            and "DiagnosticInletTurbulenceMode" in fluidx
            and "DiagnosticInletTurbulenceScale { get; set; } = 0.0" in fluidx
            else "inlet_turbulence_audit_missing_or_inconclusive",
            implementation_evidence=(
                f"pass_condition_met={c008_c009_inlet.get('pass_condition_met')}; "
                f"metric_gate_passed={c008_c009_inlet.get('metric_gate_passed')}; "
                f"delta_mae_vs_zcenter={inlet_delta.get('mae_pp')}; "
                f"delta_r2_vs_zcenter={inlet_delta.get('r2')}; "
                f"delta_pearson_vs_zcenter={inlet_delta.get('pearson')}; "
                "citylbm_default_off_controls=inletT/inletS"
            ),
            default_setting_allowed=False,
            paper_use="Use as evidence that AF k, full-plane inlet turbulence, and SGS treatment are the strongest current improvement directions.",
            limitations="Diagnostic sweep on one benchmark; C014 no-SGS scale 2.00 is best but R2 remains negative, C015 rolls back, and the result cannot support formal v0.4.0, LES improvement, or a default accuracy model.",
        )
    )

    c014_metrics = c014_residual.get("c014_metrics") or {}
    affine_metrics = (c014_residual.get("affine_upper_bound") or {}).get("metrics") or {}
    residual_groups = {item.get("group"): item for item in c014_residual.get("groups", [])}
    high_group = residual_groups.get("official_high_ge_0p6", {})
    downstream_group = residual_groups.get("downstream_y_lt_0_inferred", {})
    rows.append(
        row(
            feedback_id="SF026",
            experiment="Experiment 2 / AIJ Case E C014 residual structure",
            finding=(
                "The C014 residual audit shows velocity-ratio range compression: high official-speed probes remain underpredicted, "
                f"downstream R2={downstream_group.get('r2')}, and even a post-hoc affine upper bound only reaches R2={affine_metrics.get('r2')}."
            ),
            evidence_type=str(c014_residual.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c014_residual_structure_audit.py",
                RESULTS_DIR / "casee_c014_residual_structure_audit.json",
                RESULTS_DIR / "casee_c014_residual_structure_audit.md",
                RESULTS_DIR / "casee_c014_residual_structure_audit.csv",
                RESULTS_DIR / "casee_c014_residual_top_probes.csv",
            ],
            decision_class="residual_structure_no_default_promotion",
            citylbm_status="residual_structure_identifies_next_physics_target"
            if c014_residual.get("status") == "completed_residual_structure_audit"
            and c014_residual.get("formal_accuracy_claim_supported") is False
            else "residual_structure_audit_missing_or_inconclusive",
            implementation_evidence=(
                f"c014_mae={c014_metrics.get('mae_pp')}; "
                f"c014_r2={c014_metrics.get('r2')}; "
                f"affine_upper_bound_r2={affine_metrics.get('r2')}; "
                f"high_official_bias_pp={high_group.get('bias_pp')}; "
                f"downstream_r2={downstream_group.get('r2')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as residual-structure evidence explaining why the best C014 diagnostic candidate is still not paper-grade validation.",
            limitations="Audit over preexisting C014 solver output; it does not add a new FluidX3D run, change release_gate.json, or justify post-hoc calibration/default promotion.",
        )
    )

    rows.append(
        row(
            feedback_id="SF027",
            experiment="Experiment 2 / AIJ Case E C016 residual-target software hook",
            finding=(
                "The C014 residual-structure audit is now represented in CityLBM as a default-off residual-target "
                "diagnostic hook (residT/residS) for reproducible follow-up planning, without changing default solver behavior."
            ),
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_c014_residual_structure_audit.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
                RESULTS_DIR / "citylbm_manifest_schema_gate.json",
            ],
            decision_class="residual_target_hook_no_default_promotion",
            citylbm_status="implemented_default_off"
            if "Diagnostic Residual Target Mode" in run_component
            and "DiagnosticResidualTargetMode" in fluidx
            and "DiagnosticResidualTargetScale { get; set; } = 0.0" in fluidx
            and "diagnostic_residual_target_allowed_as_default_accuracy_model" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence=(
                "Grasshopper exposes residT/residS with defaults none/0, SimulationSettings defaults remain none/0, "
                "generated setup.cpp only records constants, and run manifests set diagnostic_residual_target_changes_solver_defaults=false."
            ),
            default_setting_allowed=False,
            paper_use="Use as software-feedback traceability from C014 residual diagnosis to a reproducible C016 follow-up interface.",
            limitations="No new FluidX3D run is added here; residual-target controls are not validation results and cannot justify formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF028",
            experiment="Experiment 2 / AIJ Case E C016 calibration-leakage guard",
            finding=(
                "C016 residual-target work is now protected by a protocol-risk guard: C014 residuals may motivate "
                "pre-registered physics hypotheses, but the official 80 RS_caseE targets cannot be used for post-hoc fitting "
                "and then reported as validation."
            ),
            evidence_type=str(c016_leakage_guard.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_c016_residual_target_leakage_guard.py",
                RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json",
                RESULTS_DIR / "casee_c016_residual_target_leakage_guard.md",
                RESULTS_DIR / "casee_c014_residual_structure_audit.json",
                RESULTS_DIR / "release_gate.json",
            ],
            decision_class="calibration_leakage_guard_no_default_promotion",
            citylbm_status="implemented_protocol_guard"
            if c016_leakage_guard.get("guard_passed") is True
            and c016_leakage_guard.get("formal_accuracy_claim_supported") is False
            else "guard_missing_or_failed",
            implementation_evidence=(
                f"guard_passed={c016_leakage_guard.get('guard_passed')}; "
                f"claim_readiness={c016_leakage_guard.get('claim_readiness')}; "
                "RS_caseE official targets are blocked as C016 fitting data."
            ),
            default_setting_allowed=False,
            paper_use="Use as protocol-risk control for residual-target follow-up design.",
            limitations="This guard adds no new CFD metric; it prevents calibration leakage and keeps formal v0.4.0 blocked until an independent official run passes.",
        )
    )

    rows.append(
        row(
            feedback_id="SF029",
            experiment="Experiment 2 / AIJ Case E solver-run provenance ledger",
            finding=(
                "The Case E solver-result evidence now has a consolidated provenance ledger mapping each official-height "
                "candidate to its command/config, CSV, log, metric values, evidence type, and claim boundary."
            ),
            evidence_type=str(solver_ledger.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_solver_run_provenance_ledger.py",
                RESULTS_DIR / "casee_solver_run_provenance_ledger.json",
                RESULTS_DIR / "casee_solver_run_provenance_ledger.csv",
                RESULTS_DIR / "casee_solver_run_provenance_ledger.md",
                RESULTS_DIR / "release_gate.json",
            ],
            decision_class="paper_provenance_ledger",
            citylbm_status="implemented_paper_traceability"
            if solver_ledger.get("ledger_passed") is True
            and solver_ledger.get("formal_accuracy_claim_supported") is False
            else "ledger_missing_or_failed",
            implementation_evidence=(
                f"ledger_passed={solver_ledger.get('ledger_passed')}; "
                f"row_count={solver_ledger.get('row_count')}; "
                f"solver_run_count={solver_ledger.get('solver_run_count')}; "
                f"release_gate_input_count={solver_ledger.get('release_gate_input_count')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as the manuscript appendix table linking Case E metrics to commands, logs, CSVs, and claim boundaries.",
            limitations="The ledger consolidates existing evidence only; it does not add a new solver run or make formal v0.4.0 pass.",
        )
    )

    claim_support_summary = claim_support.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF030",
            experiment="Experiment 2 / AIJ Case E manuscript claim support",
            finding=(
                "The Case E manuscript claim matrix is now checked by a claim-support gate that separates "
                "methods/protocol claims, negative validation, limitations-only diagnostics, reproducibility context, "
                "and blocked formal-release claims."
            ),
            evidence_type=str(claim_support_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_claim_support_gate.py",
                RESULTS_DIR / "casee_claim_support_gate.json",
                RESULTS_DIR / "casee_claim_support_gate.csv",
                RESULTS_DIR / "casee_claim_support_gate.md",
                RESULTS_DIR / "casee_manuscript_claim_matrix.csv",
            ],
            decision_class="paper_claim_support_gate",
            citylbm_status="implemented_paper_claim_boundary"
            if claim_support_summary.get("claim_support_gate_passed") is True
            and claim_support_summary.get("no_formal_accuracy_claims") is True
            else "claim_support_gate_missing_or_failed",
            implementation_evidence=(
                f"claim_support_gate_passed={claim_support_summary.get('claim_support_gate_passed')}; "
                f"claim_count={claim_support_summary.get('claim_count')}; "
                f"forbidden_success_patterns_blocked={claim_support_summary.get('forbidden_success_patterns_blocked')}; "
                f"formal_release_allowed={claim_support_summary.get('formal_release_allowed')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as the manuscript claim-support gate before turning Case E evidence into Results, Discussion, or Limitations text.",
            limitations="Claim boundary evidence only; it does not add solver output, improve official metrics, or allow formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF031",
            experiment="CityLBM manifest publication-readiness contract",
            finding=(
                "Generated citylbm_run_manifest.json files now include a publication_readiness_contract "
                "that records required external gates and artifacts before a generated case can support manuscript use."
            ),
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                CASEE_DIR / "tools" / "citylbm_manifest_output_gate.py",
                CASEE_DIR / "tools" / "citylbm_manifest_schema_gate.py",
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "citylbm_manifest_schema_gate.json",
            ],
            decision_class="software_publication_readiness_contract",
            citylbm_status="implemented_manifest_publication_boundary"
            if "publication_readiness_contract" in fluidx
            and "requires_publication_readiness_gate_json" in fluidx
            and manifest_output.get("manifest_output_gate_passed") is True
            else "publication_contract_missing_or_failed",
            implementation_evidence=(
                "citylbm_run_manifest.json records publication_readiness_contract, required publication/claim/provenance/figure/suite gates, "
                "allowed publication roles, and forbidden publication claims."
            ),
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence that CityLBM generated cases carry publication-readiness dependencies in the manifest.",
            limitations="Manifest contract only; it does not add solver output, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF032",
            experiment="CityLBM Run Simulation publication gate output",
            finding=(
                "Run Simulation now exposes a Publication Gate output beside the Claim Gate so "
                "Grasshopper users see manuscript-readiness dependencies at the point of case generation."
            ),
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                CASEE_DIR / "tools" / "citylbm_manifest_output_gate.py",
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
            ],
            decision_class="software_publication_gate_output",
            citylbm_status="implemented_publication_gate_output"
            if "Publication Gate" in run_component
            and "PublicationGateSummary" in run_component
            and manifest_output.get("manifest_output_gate_passed") is True
            else "publication_gate_output_missing_or_failed",
            implementation_evidence=(
                "Run Simulation output index 8 records the publication gate and points users to "
                "casee_publication_readiness_gate.json, casee_claim_support_gate.json, solver-run provenance ledger, "
                "paper figure QA, and the reproducibility suite."
            ),
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence that CityLBM surfaces manuscript-readiness boundaries in the plugin UI.",
            limitations="UI traceability only; it does not add solver output, improve official metrics, change defaults, or permit formal v0.4.0.",
        )
    )

    release_asset_summary = release_assets.get("summary") or {}
    release_asset_checks = release_asset_summary.get("checks") or {}
    rows.append(
        row(
            feedback_id="SF034",
            experiment="Case E release asset manifest",
            finding=(
                "The release upload asset manifest separates compiled GHA, validation reports, CSV/XLSX summaries, "
                "figures, data/environment manifests, and paper gates from raw or large hash-only files."
            ),
            evidence_type=str(release_asset_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_release_asset_manifest.py",
                RESULTS_DIR / "casee_release_asset_manifest.json",
                RESULTS_DIR / "casee_release_asset_manifest.csv",
                RESULTS_DIR / "casee_release_asset_manifest.md",
                RESULTS_DIR / "casee_artifact_index.json",
            ],
            decision_class="paper_release_asset_manifest",
            citylbm_status="implemented_release_asset_manifest"
            if release_asset_summary.get("release_asset_manifest_passed") is True
            and release_asset_summary.get("formal_accuracy_claim_supported") is False
            and release_asset_checks.get("excludes_raw_geometry_and_vtk") is True
            else "release_asset_manifest_missing_or_failed",
            implementation_evidence=(
                f"upload_asset_count={release_asset_summary.get('upload_asset_count')}; "
                f"excluded_or_hash_only_count={release_asset_summary.get('excluded_or_hash_only_count')}; "
                f"upload_total_size_bytes={release_asset_summary.get('upload_total_size_bytes')}; "
                f"recommended_tag={release_asset_summary.get('recommended_tag')}"
            ),
            default_setting_allowed=True,
            paper_use="Use for release/data-availability traceability and reviewer artifact checks.",
            limitations="Release planning only; it does not create a GitHub Release, add CFD output, or permit formal v0.4.0.",
        )
    )

    vs_cpp_summary = vs_cpp_recovery.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF035",
            experiment="CityLBM VS C++ Build Tools recovery gate",
            finding=(
                "The Windows native C++ build-chain recovery path is now scripted and audited, with explicit guards for "
                "manual -Install use, elevation, system-drive free space, winget availability, and required VC workload components."
            ),
            evidence_type=str(vs_cpp_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "vs_cpp_buildtools_recovery.ps1",
                CASEE_DIR / "tools" / "vs_cpp_recovery_gate.py",
                RESULTS_DIR / "vs_cpp_recovery_gate.json",
                RESULTS_DIR / "vs_cpp_recovery_gate.csv",
                RESULTS_DIR / "vs_cpp_recovery_gate.md",
            ],
            decision_class="build_chain_recovery_gate",
            citylbm_status="implemented_vs_cpp_recovery_gate"
            if vs_cpp_summary.get("vs_cpp_recovery_gate_passed") is True
            and vs_cpp_summary.get("formal_accuracy_claim_supported") is False
            else "vs_cpp_recovery_gate_missing_or_failed",
            implementation_evidence=(
                f"vs_cpp_ready={vs_cpp_summary.get('vs_cpp_ready')}; "
                f"can_attempt_install_now={vs_cpp_summary.get('can_attempt_install_now')}; "
                f"blocker_count={len(vs_cpp_summary.get('blockers') or [])}; "
                f"claim_readiness={vs_cpp_summary.get('claim_readiness')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as build-chain recovery evidence and to explain why VS C++ remains an operational blocker.",
            limitations="Build-chain recovery only; default script mode does not install tools, recover GPU, run CFD, improve metrics, or permit formal v0.4.0.",
        )
    )

    vs_cpp_launcher_summary = vs_cpp_elevated_launcher.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF044",
            experiment="CityLBM VS C++ Build Tools elevated launcher",
            finding=(
                "A default-audit, explicit-UAC launcher now connects the VS C++ recovery script to an administrator "
                "install path and records the post-install verifier. The current machine still blocks launch because "
                "system-drive free space is below the configured threshold."
            ),
            evidence_type=str(vs_cpp_launcher_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "vs_cpp_buildtools_elevated_launcher.ps1",
                CASEE_DIR / "tools" / "vs_cpp_elevated_launcher_gate.py",
                CASEE_DIR / "tools" / "vs_cpp_buildtools_recovery.ps1",
                RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json",
                RESULTS_DIR / "vs_cpp_elevated_launcher_gate.csv",
                RESULTS_DIR / "vs_cpp_elevated_launcher_gate.md",
                RESULTS_DIR / "vs_cpp_buildtools_elevated_launcher_probe.json",
            ],
            decision_class="build_chain_uac_launcher_gate",
            citylbm_status="implemented_vs_cpp_elevated_launcher_gate"
            if vs_cpp_launcher_summary.get("vs_cpp_elevated_launcher_gate_passed") is True
            and vs_cpp_launcher_summary.get("launch_attempted") is False
            and vs_cpp_launcher_summary.get("formal_accuracy_claim_supported") is False
            else "vs_cpp_elevated_launcher_gate_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={vs_cpp_launcher_summary.get('vs_cpp_elevated_launcher_gate_passed')}; "
                f"can_launch_elevated_install_now={vs_cpp_launcher_summary.get('can_launch_elevated_install_now')}; "
                f"launch_attempted={vs_cpp_launcher_summary.get('launch_attempted')}; "
                f"blocker_count={len(vs_cpp_launcher_summary.get('blockers') or [])}; "
                f"post_install_verification={vs_cpp_launcher_summary.get('post_install_verification')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as build-chain recovery traceability and operational-readiness evidence.",
            limitations="UAC launcher only; it does not install VS C++ during the suite, recover GPU runtime, run CFD, improve metrics, or permit formal v0.4.0.",
        )
    )

    vs_cpp_space_summary = vs_cpp_system_drive_space.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF045",
            experiment="CityLBM VS C++ system-drive space preflight",
            finding=(
                "The VS C++ recovery chain now has a no-delete system-drive space audit. It records the current "
                "C: free-space shortfall, manual cleanup candidates, and the post-cleanup launcher verifier before "
                "any elevated installation attempt."
            ),
            evidence_type=str(vs_cpp_space_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "vs_cpp_system_drive_space_gate.py",
                RESULTS_DIR / "vs_cpp_system_drive_space_gate.json",
                RESULTS_DIR / "vs_cpp_system_drive_space_gate.csv",
                RESULTS_DIR / "vs_cpp_system_drive_space_gate.md",
                RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json",
            ],
            decision_class="build_chain_system_drive_space_gate",
            citylbm_status="implemented_vs_cpp_system_drive_space_gate"
            if vs_cpp_space_summary.get("vs_cpp_system_drive_space_gate_passed") is True
            and vs_cpp_space_summary.get("deletion_attempted") is False
            and vs_cpp_space_summary.get("formal_accuracy_claim_supported") is False
            else "vs_cpp_system_drive_space_gate_missing_or_failed",
            implementation_evidence=(
                f"system_drive_free_gb={vs_cpp_space_summary.get('system_drive_free_gb')}; "
                f"additional_free_needed_gb={vs_cpp_space_summary.get('additional_free_needed_gb')}; "
                f"low_risk_candidate_total_gb={vs_cpp_space_summary.get('low_risk_candidate_total_gb')}; "
                f"space_ready_for_vs_cpp_launcher={vs_cpp_space_summary.get('space_ready_for_vs_cpp_launcher')}; "
                f"deletion_attempted={vs_cpp_space_summary.get('deletion_attempted')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as build-chain operational evidence explaining why VS C++ recovery remains space-blocked.",
            limitations="System-drive space audit only; it does not delete files, install VS C++, recover GPU runtime, run CFD, improve metrics, or permit formal v0.4.0.",
        )
    )

    operational_recovery_summary = operational_recovery_dashboard.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF046",
            experiment="Experiment 2 / operational recovery dashboard",
            finding=(
                "The blocked Case E recovery path is now consolidated into an ordered dashboard across C: space, "
                "VS C++ install readiness, UAC launch, GPU recovery, Rhino load evidence, official preflight, "
                "and the formal metric gate. Long FluidX3D runs remain disallowed until the long-run blockers clear."
            ),
            evidence_type=str(operational_recovery_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_operational_recovery_dashboard.py",
                RESULTS_DIR / "casee_operational_recovery_dashboard.json",
                RESULTS_DIR / "casee_operational_recovery_dashboard.csv",
                RESULTS_DIR / "casee_operational_recovery_dashboard.md",
                RESULTS_DIR / "casee_official_run_preflight.json",
                RESULTS_DIR / "release_gate.json",
            ],
            decision_class="operational_recovery_dashboard_gate",
            citylbm_status="implemented_operational_recovery_dashboard"
            if operational_recovery_summary.get("operational_recovery_dashboard_passed") is True
            and operational_recovery_summary.get("long_fluidx3d_run_allowed") is False
            and operational_recovery_summary.get("formal_accuracy_claim_supported") is False
            else "operational_recovery_dashboard_missing_or_failed",
            implementation_evidence=(
                f"blocking_step_count={operational_recovery_summary.get('blocking_step_count')}; "
                f"long_fluidx3d_run_allowed={operational_recovery_summary.get('long_fluidx3d_run_allowed')}; "
                f"long_run_blockers={operational_recovery_summary.get('long_run_blockers')}; "
                f"formal_release_allowed={operational_recovery_summary.get('formal_release_allowed')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as ordered operational blocker evidence for limitations and reproducibility planning.",
            limitations="Recovery dashboard only; it does not recover environment state, run CFD, improve metrics, change defaults, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF047",
            experiment="CityLBM nullable-clean plugin rebuild",
            finding=(
                "The rc70 plugin rebuild removes C# nullable warnings and hardens FluidX3D discovery, "
                "result DTOs, and VTK readers while keeping Case E diagnostic controls default-off and non-formal."
            ),
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                ROOT / "CityLBM" / "src" / "Components" / "Results" / "ReadVTKComponent.cs",
                ROOT / "CityLBM" / "src" / "Components" / "Results" / "VTKCloudVisualizationComponent.cs",
                ROOT / "docs" / "releases" / "v0.4.0-rc70.md",
                RESULTS_DIR / "casee_default_policy_gate.json",
                RESULTS_DIR / "citylbm_manifest_schema_gate.json",
                RESULTS_DIR / "citylbm_plugin_identity_binary_gate.json",
            ],
            decision_class="software_quality_no_default_promotion",
            citylbm_status="implemented_warning_clean_rebuild",
            implementation_evidence=(
                "rebuild_warnings=0; rebuild_errors=0; "
                "packaged_gha_sha256=ea6717db0226f4cd1a95f515cb4556604db6f6b59daf452b9d9bb39abc3e9af3; "
                "default_policy_gate_passed=True; manifest_schema_gate_passed=True"
            ),
            default_setting_allowed=True,
            paper_use="Use as software-quality and reproducibility evidence that the plugin builds cleanly before further Case E follow-up runs.",
            limitations="Build-quality evidence only; it does not recover GPU, run FluidX3D, improve official z2m metrics, prove Rhino loaded the new GHA, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF048",
            experiment="CityLBM canonical GHA packaging path",
            finding=(
                "The rc71 build script packages the merged Release GHA and synchronizes the tracked "
                "distributable from that canonical artifact, eliminating the earlier unmerged nested GHA ambiguity."
            ),
            evidence_type="newly_run",
            source_paths=[
                ROOT / "CityLBM" / "build.ps1",
                CASEE_DIR / "tools" / "build_chain_audit.py",
                CASEE_DIR / "tools" / "citylbm_gha_install_audit.py",
                ROOT / "CityLBM" / "bin" / "CityLBM.gha",
                ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha",
                ROOT / "docs" / "releases" / "v0.4.0-rc71.md",
                RESULTS_DIR / "plugin_identity_gate.json",
                RESULTS_DIR / "citylbm_gha_install_audit.json",
            ],
            decision_class="software_packaging_traceability_no_accuracy_promotion",
            citylbm_status="implemented_canonical_gha_packaging_path",
            implementation_evidence=(
                "build_ps1_uses_merged_release_gha=True; tracked_release_nested_sha_equal=True; "
                "packaged_gha_sha256=79ee34f1ef7632404944943c897e7dbedaa2b1262686651027ff0482dfd85118"
            ),
            default_setting_allowed=True,
            paper_use="Use as software-distribution traceability evidence for the exact GHA artifact used in reviewer-facing installation steps.",
            limitations="Packaging-path evidence only; it does not stage the GHA, prove Rhino loaded it, run CFD, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF049",
            experiment="CityLBM staged Grasshopper GHA artifact",
            finding=(
                "The current tracked CityLBM.gha has been staged into the user's Grasshopper Libraries "
                "directory with a SHA256 match to the canonical tracked GHA, closing the install-staging "
                "gap while keeping Rhino process-load evidence fail-closed."
            ),
            evidence_type=str(gha_install.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "citylbm_gha_install_audit.py",
                RESULTS_DIR / "citylbm_gha_install_audit.json",
                RESULTS_DIR / "citylbm_gha_install_audit.csv",
                RESULTS_DIR / "citylbm_gha_install_audit.md",
                RESULTS_DIR / "rhino_gha_load_gate.json",
                ROOT / "docs" / "releases" / "v0.4.0-rc72.md",
            ],
            decision_class="software_staged_gha_traceability_no_accuracy_promotion",
            citylbm_status="implemented_staged_gha_traceability"
            if gha_install.get("matching_gha_already_staged") is True
            and gha_install.get("rhino_loaded_new_gha") is False
            and gha_install.get("formal_accuracy_claim_supported") is False
            else "staged_gha_traceability_missing_or_failed",
            implementation_evidence=(
                f"matching_gha_already_staged={gha_install.get('matching_gha_already_staged')}; "
                f"recommended_library_dir={gha_install.get('recommended_library_dir')}; "
                f"tracked_sha={gha_install.get('expected_tracked_gha_sha256')}; "
                f"rhino_loaded_new_gha={gha_install.get('rhino_loaded_new_gha')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as reviewer-facing software installation traceability before manual Rhino/Grasshopper process-load verification.",
            limitations="Staged-GHA evidence only; it does not prove Rhino loaded the plugin, run CFD, improve metrics, change defaults, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF050",
            experiment="CityLBM deterministic GHA build stability",
            finding=(
                "The rc73 build path now enables deterministic compiler metadata and uses a serial ILRepack "
                "merge so two consecutive Release builds produce the same packaged CityLBM.gha SHA256."
            ),
            evidence_type=str(build_hash_stability.get("evidence_type", "missing")),
            source_paths=[
                ROOT / "CityLBM" / "CityLBM.csproj",
                CASEE_DIR / "tools" / "citylbm_build_hash_stability_gate.py",
                RESULTS_DIR / "citylbm_build_hash_stability_gate.json",
                RESULTS_DIR / "citylbm_build_hash_stability_gate.csv",
                RESULTS_DIR / "citylbm_build_hash_stability_gate.md",
                ROOT / "docs" / "releases" / "v0.4.0-rc73.md",
            ],
            decision_class="software_build_hash_stability_no_accuracy_promotion",
            citylbm_status="implemented_build_hash_stability_gate"
            if build_hash_stability.get("citylbm_build_hash_stability_gate_passed") is True
            and build_hash_stability.get("repeated_build_hash_stable") is True
            and build_hash_stability.get("formal_accuracy_claim_supported") is False
            else "build_hash_stability_missing_or_failed",
            implementation_evidence=(
                f"build_repeat_count={build_hash_stability.get('build_repeat_count')}; "
                f"repeated_build_hash_stable={build_hash_stability.get('repeated_build_hash_stable')}; "
                f"final_tracked_gha_sha256={build_hash_stability.get('final_tracked_gha_sha256')}; "
                f"grasshopper_staged={((build_hash_stability.get('grasshopper_staging') or {}).get('staged'))}"
            ),
            default_setting_allowed=True,
            paper_use="Use as software-package reproducibility evidence for reviewer installation and artifact traceability.",
            limitations="Build-hash stability evidence only; it does not prove Rhino loaded the plugin, run CFD, improve metrics, change physics defaults, or permit formal v0.4.0.",
        )
    )

    release_bundle_summary = release_bundle.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF051",
            experiment="Case E lightweight release bundle",
            finding=(
                "The rc74 release bundle gate packages the curated lightweight upload assets into a "
                "deterministic zip and verifies each bundled file against the release asset manifest hash."
            ),
            evidence_type=str(release_bundle_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_release_bundle_gate.py",
                RESULTS_DIR / "casee_release_bundle_manifest.json",
                RESULTS_DIR / "casee_release_bundle_manifest.csv",
                RESULTS_DIR / "casee_release_bundle_manifest.md",
                RESULTS_DIR / "casee_release_bundle.zip",
                ROOT / "docs" / "releases" / "v0.4.0-rc74.md",
            ],
            decision_class="paper_release_bundle_no_accuracy_promotion",
            citylbm_status="implemented_release_bundle_gate"
            if release_bundle_summary.get("casee_release_bundle_gate_passed") is True
            and release_bundle_summary.get("raw_or_large_files_excluded") is True
            and release_bundle_summary.get("formal_accuracy_claim_supported") is False
            else "release_bundle_gate_missing_or_failed",
            implementation_evidence=(
                f"bundled_asset_count={release_bundle_summary.get('bundled_asset_count')}; "
                f"bundle_size_bytes={release_bundle_summary.get('bundle_size_bytes')}; "
                f"bundle_sha256={release_bundle_summary.get('bundle_sha256')}; "
                f"raw_or_large_files_excluded={release_bundle_summary.get('raw_or_large_files_excluded')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as reviewer-facing release packaging evidence for the lightweight Case E artifact set.",
            limitations="Release-bundle evidence only; it does not create a GitHub Release, run CFD, improve metrics, change physics defaults, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF052",
            experiment="GitHub publication state gate",
            finding=(
                "The rc75 publication gate records the latest completed local rc tag, confirms whether it is "
                "visible on GitHub, checks GitHub Release existence, and records whether the local gh CLI can "
                "create a release from the lightweight bundle."
            ),
            evidence_type=str(github_publication.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "github_release_publication_gate.py",
                RESULTS_DIR / "github_release_publication_gate.json",
                RESULTS_DIR / "github_release_publication_gate.csv",
                RESULTS_DIR / "github_release_publication_gate.md",
                ROOT / "docs" / "releases" / "v0.4.0-rc75.md",
            ],
            decision_class="github_publication_state_no_accuracy_promotion",
            citylbm_status="implemented_github_publication_state_gate"
            if github_publication.get("github_release_publication_gate_passed") is True
            and github_publication.get("formal_accuracy_claim_supported") is False
            else "github_publication_state_gate_missing_or_failed",
            implementation_evidence=(
                f"audited_tag={github_publication.get('audited_tag')}; "
                f"recommended_tag={github_publication.get('recommended_tag')}; "
                f"remote_tag_visible={github_publication.get('remote_tag_visible')}; "
                f"github_release_exists={github_publication.get('github_release_exists')}; "
                f"gh_cli_available={github_publication.get('gh_cli_available')}; "
                f"can_create_release_now={github_publication.get('can_create_release_now')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as publication-state traceability for the accuracy-diagnostic rc artifact chain.",
            limitations="Publication-state evidence only; it does not create a GitHub Release, run CFD, improve metrics, change physics defaults, or permit formal v0.4.0.",
        )
    )

    hygiene_summary = workspace_hygiene.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF053",
            experiment="Case E workspace hygiene gate",
            finding=(
                "The rc76 workspace hygiene gate classifies ignored local build caches, native candidate CSVs, "
                "runtime logs, and visualization scratch files so they cannot be mistaken for curated release "
                "assets or paper-ready official results."
            ),
            evidence_type=str(hygiene_summary.get("evidence_type", "missing")),
            source_paths=[
                ROOT / ".gitignore",
                CASEE_DIR / "tools" / "casee_workspace_hygiene_gate.py",
                RESULTS_DIR / "casee_workspace_hygiene_gate.json",
                RESULTS_DIR / "casee_workspace_hygiene_gate.csv",
                RESULTS_DIR / "casee_workspace_hygiene_gate.md",
                ROOT / "docs" / "releases" / "v0.4.0-rc76.md",
            ],
            decision_class="workspace_hygiene_no_accuracy_promotion",
            citylbm_status="implemented_workspace_hygiene_gate"
            if hygiene_summary.get("workspace_hygiene_gate_passed") is True
            and hygiene_summary.get("formal_accuracy_claim_supported") is False
            else "workspace_hygiene_gate_missing_or_failed",
            implementation_evidence=(
                f"ignored_local_artifact_count={hygiene_summary.get('ignored_local_artifact_count')}; "
                f"allowed_untracked_local_artifact_count={hygiene_summary.get('allowed_untracked_local_artifact_count')}; "
                f"unexpected_untracked_count={hygiene_summary.get('unexpected_untracked_count')}; "
                f"tracked_forbidden_count={hygiene_summary.get('tracked_forbidden_count')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as release and manuscript hygiene evidence that local scratch results remain separated from curated paper evidence.",
            limitations="Workspace-hygiene evidence only; it does not delete files, run CFD, improve metrics, change physics defaults, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF036",
            experiment="CityLBM GHA staging/install audit",
            finding=(
                "The tracked CityLBM.gha can now be audited against common Grasshopper Libraries locations, "
                "with exact SHA256 matching and an explicit manual copy command before any Rhino load claim is made."
            ),
            evidence_type=str(gha_install.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "citylbm_gha_install_audit.py",
                RESULTS_DIR / "citylbm_gha_install_audit.json",
                RESULTS_DIR / "citylbm_gha_install_audit.csv",
                RESULTS_DIR / "citylbm_gha_install_audit.md",
                RESULTS_DIR / "rhino_gha_load_gate.json",
            ],
            decision_class="software_gha_staging_audit",
            citylbm_status="implemented_gha_staging_audit"
            if gha_install.get("install_audit_passed") is True
            and gha_install.get("formal_accuracy_claim_supported") is False
            and gha_install.get("rhino_loaded_new_gha") is False
            else "gha_staging_audit_missing_or_failed",
            implementation_evidence=(
                f"matching_gha_already_staged={gha_install.get('matching_gha_already_staged')}; "
                f"recommended_library_dir={gha_install.get('recommended_library_dir')}; "
                f"tracked_sha={gha_install.get('expected_tracked_gha_sha256')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as software delivery traceability before manual Rhino/Grasshopper load verification.",
            limitations="Staging audit only; it does not prove Rhino loaded the GHA, run CFD, improve metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF037",
            experiment="CityLBM Rhino/GHA load evidence kit",
            finding=(
                "Rhino/Grasshopper load verification now has a fail-closed evidence kit that detects Rhino, "
                "checks the staged GHA hash, and writes a manual manifest template without claiming that Rhino loaded the plugin."
            ),
            evidence_type=str(rhino_evidence_kit.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_rhino_load_evidence_kit.py",
                RESULTS_DIR / "casee_rhino_load_evidence_kit.json",
                RESULTS_DIR / "casee_rhino_load_evidence_kit.csv",
                RESULTS_DIR / "casee_rhino_load_evidence_kit.md",
                RESULTS_DIR / "rhino_gha_load_manifest.template.json",
                RESULTS_DIR / "rhino_gha_load_gate.json",
            ],
            decision_class="manual_rhino_load_evidence_kit",
            citylbm_status="implemented_rhino_load_evidence_kit"
            if rhino_evidence_kit.get("rhino_load_evidence_kit_ready") is True
            and rhino_evidence_kit.get("formal_accuracy_claim_supported") is False
            else "rhino_load_evidence_kit_missing_or_failed",
            implementation_evidence=(
                f"kit_ready={rhino_evidence_kit.get('rhino_load_evidence_kit_ready')}; "
                f"rhino_detected={(rhino_evidence_kit.get('checks') or {}).get('rhino_executable_detected')}; "
                f"matching_gha_staged={(rhino_evidence_kit.get('checks') or {}).get('matching_gha_staged')}; "
                f"expected_sha={rhino_evidence_kit.get('expected_tracked_gha_sha256')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as manual software-load evidence collection protocol before closing the Rhino/GHA load gate.",
            limitations="Manual evidence kit only; it does not prove Rhino loaded the plugin, run CFD, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF038",
            experiment="CityLBM Plugin Identity Grasshopper component",
            finding=(
                "CityLBM now exposes a Plugin Identity component that reports the loaded plugin version, assembly version, "
                "GHA path, SHA256, manifest template, and explicit claim boundary inside Grasshopper."
            ),
            evidence_type=str(identity_component_gate.get("evidence_type", "missing")),
            source_paths=[
                ROOT / "CityLBM" / "src" / "Components" / "Results" / "PluginIdentityComponent.cs",
                CASEE_DIR / "tools" / "citylbm_plugin_identity_component_gate.py",
                RESULTS_DIR / "citylbm_plugin_identity_component_gate.json",
                RESULTS_DIR / "citylbm_plugin_identity_component_gate.csv",
                RESULTS_DIR / "citylbm_plugin_identity_component_gate.md",
            ],
            decision_class="software_identity_component",
            citylbm_status="implemented_plugin_identity_component"
            if identity_component_gate.get("plugin_identity_component_gate_passed") is True
            and identity_component_gate.get("formal_accuracy_claim_supported") is False
            else "plugin_identity_component_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={identity_component_gate.get('plugin_identity_component_gate_passed')}; "
                f"plugin_version={identity_component_gate.get('plugin_public_version')}; "
                f"assembly_version={identity_component_gate.get('plugin_assembly_version')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as in-Grasshopper software identity evidence for manual Rhino/GHA load verification screenshots.",
            limitations="Software identity component only; it does not prove CFD accuracy, run FluidX3D, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF039",
            experiment="CityLBM packaged GHA identity-component gate",
            finding=(
                "The tracked packaged CityLBM.gha is now audited for Plugin Identity component markers, "
                "including the component name, GHA SHA256 output, manifest-template output, GUID, and accuracy-claim boundary."
            ),
            evidence_type=str(identity_binary_gate.get("evidence_type", "missing")),
            source_paths=[
                ROOT / "CityLBM" / "bin" / "CityLBM.gha",
                CASEE_DIR / "tools" / "citylbm_plugin_identity_binary_gate.py",
                RESULTS_DIR / "citylbm_plugin_identity_binary_gate.json",
                RESULTS_DIR / "citylbm_plugin_identity_binary_gate.csv",
                RESULTS_DIR / "citylbm_plugin_identity_binary_gate.md",
            ],
            decision_class="packaged_gha_identity_component_gate",
            citylbm_status="implemented_packaged_gha_identity_component_gate"
            if identity_binary_gate.get("plugin_identity_binary_gate_passed") is True
            and identity_binary_gate.get("formal_accuracy_claim_supported") is False
            else "packaged_gha_identity_component_gate_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={identity_binary_gate.get('plugin_identity_binary_gate_passed')}; "
                f"tracked_sha={identity_binary_gate.get('tracked_gha_sha256')}; "
                f"size_bytes={identity_binary_gate.get('tracked_gha_size_bytes')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as packaged-plugin software identity evidence before manual Rhino/GHA load verification.",
            limitations="Packaged GHA string audit only; it does not prove Rhino loaded the plugin, run CFD, improve official metrics, or permit formal v0.4.0.",
        )
    )

    portable_activation = portable_toolchain_gate.get("activation") or {}
    rows.append(
        row(
            feedback_id="SF040",
            experiment="CityLBM portable .NET / FluidX3D / MinGW toolchain activation",
            finding=(
                "The local portable toolchain can now be activated and audited without changing system PATH: "
                "portable .NET, the existing FluidX3D binary, and MinGW/g++ are verified while VS C++ and GPU "
                "runtime remain explicit blockers."
            ),
            evidence_type=str(portable_toolchain_gate.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "citylbm_portable_toolchain_activate.ps1",
                CASEE_DIR / "tools" / "citylbm_portable_toolchain_gate.py",
                RESULTS_DIR / "citylbm_portable_toolchain_activation.json",
                RESULTS_DIR / "citylbm_portable_toolchain_gate.json",
                RESULTS_DIR / "citylbm_portable_toolchain_gate.csv",
                RESULTS_DIR / "citylbm_portable_toolchain_gate.md",
                RESULTS_DIR / "build_chain_manifest.json",
            ],
            decision_class="portable_toolchain_activation_gate",
            citylbm_status="implemented_portable_toolchain_activation_gate"
            if portable_toolchain_gate.get("portable_toolchain_gate_passed") is True
            and portable_toolchain_gate.get("formal_accuracy_claim_supported") is False
            else "portable_toolchain_activation_gate_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={portable_toolchain_gate.get('portable_toolchain_gate_passed')}; "
                f"portable_toolchain_ready={portable_activation.get('portable_toolchain_ready')}; "
                f"dotnet={((portable_activation.get('dotnet') or {}).get('ready'))}; "
                f"fluidx3d={((portable_activation.get('fluidx3d') or {}).get('ready_for_existing_binary'))}; "
                f"gpp={((portable_activation.get('mingw_gpp') or {}).get('ready'))}; "
                f"gpu={((portable_activation.get('gpu_runtime') or {}).get('ready'))}"
            ),
            default_setting_allowed=True,
            paper_use="Use as build-chain reproducibility evidence for the local portable toolchain.",
            limitations="Toolchain activation only; it does not install VS C++, recover GPU, run FluidX3D, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF041",
            experiment="CityLBM GPU runtime fail-fast gate",
            finding=(
                "Long native FluidX3D scheduling is now guarded by a newly-run nvidia-smi fail-fast gate. "
                "When the GPU reports a lost device, the gate passes only by keeping long FluidX3D runs blocked."
            ),
            evidence_type=str(gpu_failfast_gate.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "citylbm_gpu_runtime_failfast_gate.py",
                RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json",
                RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.csv",
                RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.md",
                RESULTS_DIR / "casee_official_run_preflight.json",
                RESULTS_DIR / "build_chain_manifest.json",
            ],
            decision_class="gpu_runtime_failfast_gate",
            citylbm_status="implemented_gpu_runtime_failfast_gate"
            if gpu_failfast_gate.get("gpu_runtime_failfast_gate_passed") is True
            and gpu_failfast_gate.get("long_fluidx3d_run_allowed") is False
            and gpu_failfast_gate.get("formal_accuracy_claim_supported") is False
            else "gpu_runtime_failfast_gate_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={gpu_failfast_gate.get('gpu_runtime_failfast_gate_passed')}; "
                f"gpu_ready={gpu_failfast_gate.get('gpu_runtime_ready')}; "
                f"gpu_lost_detected={gpu_failfast_gate.get('gpu_lost_detected')}; "
                f"long_run_allowed={gpu_failfast_gate.get('long_fluidx3d_run_allowed')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as runtime safety and reproducibility evidence explaining why no new long FluidX3D run is scheduled while GPU runtime is blocked.",
            limitations="Runtime fail-fast gate only; it does not recover GPU, run FluidX3D, add solver output, improve official metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF042",
            experiment="CityLBM Rhino/GHA manual load manifest schema gate",
            finding=(
                "The manual Rhino/GHA load manifest now has a schema gate that checks required fields, "
                "expected plugin version, expected GHA SHA256, and evidence-artifact requirements without treating "
                "the template itself as load evidence."
            ),
            evidence_type=str(rhino_manifest_schema_gate.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "rhino_gha_load_manifest_schema_gate.py",
                RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json",
                RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.csv",
                RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.md",
                RESULTS_DIR / "rhino_gha_load_manifest.template.json",
                RESULTS_DIR / "rhino_gha_load_gate.json",
            ],
            decision_class="manual_rhino_load_manifest_schema_gate",
            citylbm_status="implemented_rhino_load_manifest_schema_gate"
            if rhino_manifest_schema_gate.get("rhino_load_manifest_schema_gate_passed") is True
            and rhino_manifest_schema_gate.get("manual_manifest_claim_ready") is False
            and rhino_manifest_schema_gate.get("formal_accuracy_claim_supported") is False
            else "rhino_load_manifest_schema_gate_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={rhino_manifest_schema_gate.get('rhino_load_manifest_schema_gate_passed')}; "
                f"manual_manifest_present={rhino_manifest_schema_gate.get('manual_manifest_present')}; "
                f"manual_manifest_claim_ready={rhino_manifest_schema_gate.get('manual_manifest_claim_ready')}; "
                f"rhino_loaded_new_gha={rhino_manifest_schema_gate.get('rhino_loaded_new_gha')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as reviewer-facing schema evidence for the manual Rhino/GHA load manifest contract.",
            limitations="Schema gate only; it does not create manual evidence, prove Rhino loaded the plugin, run CFD, improve metrics, or permit formal v0.4.0.",
        )
    )

    orphan_summary = orphan_candidate_csv_audit.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF043",
            experiment="Experiment 2 / local orphan native candidate CSV audit",
            finding=(
                "Local untracked native candidate CSVs are now inventoried by hash and metric summary before any "
                "paper use. The best raw candidate remains negative, and no candidate is formal-result eligible "
                "because complete run logs are absent."
            ),
            evidence_type=str(orphan_summary.get("evidence_type", orphan_candidate_csv_audit.get("evidence_type", "missing"))),
            source_paths=[
                CASEE_DIR / "tools" / "casee_orphan_candidate_csv_audit.py",
                RESULTS_DIR / "casee_orphan_candidate_csv_audit.json",
                RESULTS_DIR / "casee_orphan_candidate_csv_audit.csv",
                RESULTS_DIR / "casee_orphan_candidate_csv_audit.md",
                RESULTS_DIR / "casee_candidate_sweep_plan.json",
            ],
            decision_class="local_orphan_candidate_no_default_promotion",
            citylbm_status="implemented_orphan_candidate_csv_audit"
            if orphan_summary.get("orphan_candidate_csv_audit_passed") is True
            and orphan_summary.get("any_formal_result_allowed") is False
            and orphan_summary.get("formal_accuracy_claim_supported") is False
            else "orphan_candidate_csv_audit_missing_or_failed",
            implementation_evidence=(
                f"candidate_csv_count={orphan_summary.get('candidate_csv_count')}; "
                f"best_raw_mae_pp={orphan_summary.get('best_raw_mae_pp')}; "
                f"best_raw_r2={orphan_summary.get('best_raw_r2')}; "
                f"formal_raw_candidates_with_logs={orphan_summary.get('formal_raw_candidates_with_logs')}; "
                f"any_formal_result_allowed={orphan_summary.get('any_formal_result_allowed')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as local candidate inventory and protocol-risk evidence only.",
            limitations="The raw candidate CSVs are local/untracked and lack complete run logs; do not use them as formal validation, default-promotion evidence, or formal v0.4.0 support.",
        )
    )

    rows.append(
        row(
            feedback_id="SF019",
            experiment="Experiment 2 / AIJ Case E official z=2 m follow-up planning",
            finding=(
                "The candidate sweep plan converts the current negative official metric and failure-mode evidence "
                "into prioritized follow-up runs with explicit commands, blockers, pass conditions, and default-promotion boundaries."
            ),
            evidence_type=str(candidate_sweep.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_candidate_sweep_plan.py",
                RESULTS_DIR / "casee_candidate_sweep_plan.json",
                RESULTS_DIR / "casee_candidate_sweep_plan.md",
                RESULTS_DIR / "release_gate.json",
                RESULTS_DIR / "casee_official_run_preflight.json",
            ],
            decision_class="followup_sweep_plan",
            citylbm_status="planned_candidate_matrix"
            if candidate_sweep.get("candidate_sweep_plan_generated") is True
            else "missing_candidate_matrix",
            implementation_evidence=f"candidate_count={candidate_sweep.get('candidate_count')}; executable_now_count={candidate_sweep.get('executable_now_count')}; recommended_tag={candidate_sweep.get('recommended_tag')}",
            default_setting_allowed=False,
            paper_use="Use as a pre-registered follow-up experiment plan for improving official z=2 m R2.",
            limitations="Planning evidence only; no candidate has produced new official metrics and no default can be promoted from the plan alone.",
        )
    )

    postrun_summary = postrun_handoff.get("summary") or {}
    rows.append(
        row(
            feedback_id="SF054",
            experiment="Experiment 2 / Case E post-run official audit handoff",
            finding=(
                "A fail-closed post-run handoff now checks any newly completed Case E probe CSV for "
                "official z=2 m raw_trilinear audit readiness before it can be used in paper or release evidence."
            ),
            evidence_type=str(postrun_summary.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "casee_postrun_official_audit_handoff.py",
                RESULTS_DIR / "casee_postrun_official_audit_handoff.json",
                RESULTS_DIR / "casee_postrun_official_audit_handoff.csv",
                RESULTS_DIR / "casee_postrun_official_audit_handoff.md",
                RESULTS_DIR / "casee_next_experiment_runbook.json",
            ],
            decision_class="postrun_official_audit_handoff_no_default_promotion",
            citylbm_status="implemented_postrun_official_audit_handoff"
            if postrun_summary.get("postrun_official_audit_handoff_passed") is True
            and postrun_summary.get("formal_accuracy_claim_supported") is False
            and postrun_summary.get("formal_result_allowed_now") is False
            else "postrun_official_audit_handoff_missing_or_failed",
            implementation_evidence=(
                f"ready_to_run_official_audit={postrun_summary.get('ready_to_run_official_audit')}; "
                f"claim_readiness={postrun_summary.get('claim_readiness')}; "
                f"runbook_postrun_policy_present={postrun_summary.get('runbook_postrun_policy_present')}; "
                f"official_audit_command={postrun_summary.get('official_audit_command')}"
            ),
            default_setting_allowed=True,
            paper_use="Use as protocol-control evidence for accepting future post-run Case E CSVs into the formal audit path.",
            limitations="Handoff evidence only; it does not run FluidX3D, update official metrics, promote diagnostics, change defaults, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF055",
            experiment="Experiment 2 / CityLBM plugin Case E post-run audit component",
            finding=(
                "CityLBM now exposes a Grasshopper Case E Post-run Audit component that checks completed "
                "probe CSV readiness and prints the official casee_audit.py command before any accuracy claim."
            ),
            evidence_type=str(postrun_audit_component_gate.get("evidence_type", "missing")),
            source_paths=[
                POSTRUN_AUDIT_COMPONENT,
                CASEE_DIR / "tools" / "citylbm_casee_postrun_audit_component_gate.py",
                CASEE_DIR / "tools" / "citylbm_casee_postrun_audit_binary_gate.py",
                RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.json",
                RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.csv",
                RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.md",
                RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.json",
                RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.csv",
                RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.md",
            ],
            decision_class="software_postrun_audit_component_no_accuracy_promotion",
            citylbm_status="implemented_packaged_casee_postrun_audit_component"
            if postrun_audit_component_gate.get("casee_postrun_audit_component_gate_passed") is True
            and postrun_audit_binary_gate.get("casee_postrun_audit_binary_gate_passed") is True
            and postrun_audit_component_gate.get("formal_accuracy_claim_supported") is False
            and postrun_audit_binary_gate.get("formal_accuracy_claim_supported") is False
            else "casee_postrun_audit_component_missing_or_failed",
            implementation_evidence=(
                f"source_gate_passed={postrun_audit_component_gate.get('casee_postrun_audit_component_gate_passed')}; "
                f"binary_gate_passed={postrun_audit_binary_gate.get('casee_postrun_audit_binary_gate_passed')}; "
                f"component_has_casee_audit_command={'casee_audit.py' in postrun_audit_component}; "
                f"component_forces_formal_false={'DA.SetData(3, false)' in postrun_audit_component}"
            ),
            default_setting_allowed=True,
            paper_use="Use as software protocol-control evidence that post-run Case E candidates are gated before paper claims.",
            limitations="Plugin component evidence only; it does not run FluidX3D, compute R2, update official metrics, improve z2m accuracy, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF056",
            experiment="Experiment 2 / native Case E wall and ground follow-up codegen",
            finding=(
                "The native Case E generator now provides default-off voxel-dilation and ground-damping "
                "wall/ground follow-up options, replacing the earlier physical-wall-model implementation placeholder."
            ),
            evidence_type=str(wall_followup_codegen.get("evidence_type", "missing")),
            source_paths=[
                CASEE_DIR / "tools" / "generate_native_casee.py",
                CASEE_DIR / "tools" / "casee_wall_followup_codegen_gate.py",
                CASEE_DIR / "tools" / "casee_candidate_sweep_plan.py",
                CASEE_DIR / "tools" / "casee_next_experiment_runbook.py",
                RESULTS_DIR / "casee_wall_followup_codegen_gate.json",
                RESULTS_DIR / "casee_wall_followup_codegen_gate.csv",
                RESULTS_DIR / "casee_wall_followup_codegen_gate.md",
                RESULTS_DIR / "casee_candidate_sweep_plan.json",
                RESULTS_DIR / "casee_next_experiment_runbook.json",
            ],
            decision_class="native_wall_followup_codegen_no_accuracy_promotion",
            citylbm_status="implemented_default_off_native_wall_followup_codegen"
            if wall_followup_codegen.get("wall_followup_codegen_gate_passed") is True
            and wall_followup_codegen.get("formal_accuracy_claim_supported") is False
            else "native_wall_followup_codegen_missing_or_failed",
            implementation_evidence=(
                f"gate_passed={wall_followup_codegen.get('wall_followup_codegen_gate_passed')}; "
                f"candidate_count={candidate_sweep.get('candidate_count')}; "
                f"executable_now_count={candidate_sweep.get('executable_now_count')}; "
                f"recommended_tag={candidate_sweep.get('recommended_tag')}"
            ),
            default_setting_allowed=False,
            paper_use="Use as pre-registered software implementation evidence for the next wall/ground official follow-up.",
            limitations="Code-generation evidence only; no wall/ground follow-up run has completed, no R2 changed, and no wall setting can be promoted before an official z2m release-gate pass.",
        )
    )

    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in rows:
            writer.writerow({key: item[key] for key in FIELDNAMES})


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_decision: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for item in rows:
        by_decision[item["decision_class"]] = by_decision.get(item["decision_class"], 0) + 1
        by_status[item["citylbm_status"]] = by_status.get(item["citylbm_status"], 0) + 1
    required_ids = {"SF001", "SF002", "SF003", "SF004", "SF005", "SF006", "SF007", "SF008", "SF009", "SF010", "SF011", "SF012", "SF013", "SF014", "SF015", "SF016", "SF017", "SF018", "SF019", "SF020", "SF021", "SF022", "SF023", "SF024", "SF025", "SF026", "SF027", "SF028", "SF029", "SF030", "SF031", "SF032", "SF033", "SF034", "SF035", "SF036", "SF037", "SF038", "SF039", "SF040", "SF041", "SF042", "SF043", "SF044", "SF045", "SF046", "SF047", "SF048", "SF049", "SF050", "SF051", "SF052", "SF053", "SF054", "SF055", "SF056"}
    found_ids = {str(item["feedback_id"]) for item in rows}
    sources_exist = all(bool(item["source_paths_exist"]) for item in rows)
    no_forbidden_default = all(
        bool(item["default_setting_allowed"])
        for item in rows
        if item["decision_class"] in {"default_quality_gate", "formal_protocol_default", "application_workflow_policy", "software_traceability_output", "paper_traceability_output", "paper_figure_output", "paper_provenance_ledger", "paper_claim_support_gate", "software_publication_readiness_contract", "software_publication_gate_output", "portable_plugin_build_script", "paper_release_asset_manifest", "paper_release_bundle_no_accuracy_promotion", "github_publication_state_no_accuracy_promotion", "workspace_hygiene_no_accuracy_promotion", "postrun_official_audit_handoff_no_default_promotion", "build_chain_recovery_gate", "build_chain_uac_launcher_gate", "build_chain_system_drive_space_gate", "operational_recovery_dashboard_gate", "portable_toolchain_activation_gate", "gpu_runtime_failfast_gate", "software_gha_staging_audit", "manual_rhino_load_evidence_kit", "manual_rhino_load_manifest_schema_gate", "software_identity_component", "packaged_gha_identity_component_gate", "software_packaging_traceability_no_accuracy_promotion", "software_staged_gha_traceability_no_accuracy_promotion", "software_build_hash_stability_no_accuracy_promotion", "software_postrun_audit_component_no_accuracy_promotion"}
    ) and not any(
        bool(item["default_setting_allowed"])
        for item in rows
        if item["decision_class"] in {"diagnostic_switch", "blocked_default_accuracy_upgrade", "blocked_followup_run", "paper_interpretation_layer", "followup_sweep_plan", "rerun_reproducibility_guard", "completed_candidate_no_default_promotion", "diagnostic_ablation_no_default_promotion", "low_cost_regression_no_default_promotion", "runtime_decomposition_sensitivity_no_default_promotion", "inlet_turbulence_diagnostic_no_default_promotion", "residual_structure_no_default_promotion", "local_orphan_candidate_no_default_promotion", "residual_target_hook_no_default_promotion", "calibration_leakage_guard_no_default_promotion", "native_wall_followup_codegen_no_accuracy_promotion"}
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feedback_count": len(rows),
        "decision_class_counts": by_decision,
        "citylbm_status_counts": by_status,
        "required_feedback_rows_present": required_ids.issubset(found_ids),
        "all_source_paths_exist": sources_exist,
        "no_forbidden_default_promotion": no_forbidden_default,
        "software_feedback_matrix_passed": required_ids.issubset(found_ids) and sources_exist and no_forbidden_default,
        "formal_accuracy_claim_supported": False,
        "formal_v0_4_0_allowed": False,
        "boundary": (
            "This matrix converts audited experiment findings into software policy, diagnostic switch, "
            "and blocker decisions. It does not add CFD results or upgrade the official Case E metric."
        ),
    }


def write_markdown(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Software Feedback Matrix",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Matrix passed: {summary['software_feedback_matrix_passed']}",
        f"- Feedback rows: {summary['feedback_count']}",
        f"- All source paths exist: {summary['all_source_paths_exist']}",
        f"- No forbidden default promotion: {summary['no_forbidden_default_promotion']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {summary['formal_v0_4_0_allowed']}",
        "",
        "## Decision Counts",
        "",
    ]
    for key in sorted(summary["decision_class_counts"]):
        lines.append(f"- {key}: {summary['decision_class_counts'][key]}")
    lines += [
        "",
        "## Feedback Rows",
        "",
        "| id | experiment | decision | status | default? | finding |",
        "|---|---|---|---|---:|---|",
    ]
    for item in rows:
        lines.append(
            f"| `{item['feedback_id']}` | {item['experiment']} | {item['decision_class']} | "
            f"{item['citylbm_status']} | {item['default_setting_allowed']} | {item['finding']} |"
        )
    lines += [
        "",
        "## Paper Boundary",
        "",
        "| id | paper use | limitations |",
        "|---|---|---|",
    ]
    for item in rows:
        lines.append(f"| `{item['feedback_id']}` | {item['paper_use']} | {item['limitations']} |")
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = summarize(rows)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": [
            rel(CASEA_RESULTS / "casea_smoke_regression.json"),
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "casee_default_policy_gate.json"),
            rel(RESULTS_DIR / "casee_official_run_preflight.json"),
            rel(RESULTS_DIR / "build_chain_manifest.json"),
            rel(RESULTS_DIR / "vs_cpp_system_drive_space_gate.json"),
            rel(RESULTS_DIR / "casee_operational_recovery_dashboard.json"),
            rel(RESULTS_DIR / "vs_cpp_elevated_launcher_gate.json"),
            rel(RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json"),
            rel(RESULTS_DIR / "citylbm_portable_toolchain_gate.json"),
            rel(RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json"),
            rel(RESULTS_DIR / "casee_dx1_readiness_audit.json"),
            rel(RESULTS_DIR / "casee_candidate_sweep_plan.json"),
            rel(RESULTS_DIR / "casee_wall_followup_codegen_gate.json"),
            rel(RESULTS_DIR / "casee_orphan_candidate_csv_audit.json"),
            rel(RESULTS_DIR / "casee_zcenter_rerun_consistency.json"),
            rel(RESULTS_DIR / "casee_c002_longer_mean_audit.json"),
            rel(RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json"),
            rel(RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json"),
            rel(RESULTS_DIR / "casee_c005_decomposition_audit.json"),
            rel(RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json"),
            rel(RESULTS_DIR / "casee_claim_support_gate.json"),
            rel(RESULTS_DIR / "citylbm_paper_results_packet.json"),
            rel(RESULTS_DIR / "citylbm_manifest_output_gate.json"),
            rel(RESULTS_DIR / "citylbm_manifest_schema_gate.json"),
            rel(RESULTS_DIR / "citylbm_casee_postrun_audit_component_gate.json"),
            rel(RESULTS_DIR / "citylbm_casee_postrun_audit_binary_gate.json"),
            rel(RESULTS_DIR / "github_release_publication_gate.json"),
            rel(RESULTS_DIR / "casee_workspace_hygiene_gate.json"),
            rel(RESULTS_DIR / "casee_manuscript_results_table.json"),
            rel(RESULTS_DIR / "casee_manuscript_section_pack.json"),
            rel(RESULTS_DIR / "casee_paper_results_figure_qa.json"),
            rel(PAPER_DRAFTS / "experiment3_claim_verification.csv"),
            rel(PAPER_DRAFTS / "casee_v04_manuscript_section_pack_en.md"),
            rel(FLUIDX),
            rel(RUN_COMPONENT),
            rel(POSTRUN_AUDIT_COMPONENT),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"software_feedback_matrix_passed": summary["software_feedback_matrix_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["software_feedback_matrix_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
