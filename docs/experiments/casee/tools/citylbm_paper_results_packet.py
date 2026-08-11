#!/usr/bin/env python3
"""Build a manuscript-facing results packet across CityLBM Experiments 1, 2, and 3."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASEE_DIR = ROOT / "docs" / "experiments" / "casee"
CASEE_RESULTS = CASEE_DIR / "results"
CASEA_RESULTS = ROOT / "docs" / "experiments" / "casea" / "results"
PAPER_DRAFTS = ROOT / "academic-paper-writer" / "paper-drafts"
EXP3_ROOT = ROOT / "releases" / "v0.2.0" / "package" / "validation_experiments" / "Experiment3_TUM2TWIN_DigitalTwin_DesignApplication"

OUT_JSON = CASEE_RESULTS / "citylbm_paper_results_packet.json"
OUT_CSV = CASEE_RESULTS / "citylbm_paper_results_packet.csv"
OUT_MD = CASEE_RESULTS / "citylbm_paper_results_packet.md"

FIELDNAMES = [
    "experiment",
    "result_id",
    "claim_readiness",
    "evidence_type",
    "source_paths",
    "metric_or_status",
    "paper_use",
    "limitations",
    "software_feedback",
]


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


def row(
    *,
    experiment: str,
    result_id: str,
    claim_readiness: str,
    evidence_type: str,
    source_paths: Iterable[str],
    metric_or_status: str,
    paper_use: str,
    limitations: str,
    software_feedback: str = "",
) -> Dict[str, str]:
    return {
        "experiment": experiment,
        "result_id": result_id,
        "claim_readiness": claim_readiness,
        "evidence_type": evidence_type,
        "source_paths": "; ".join(source_paths),
        "metric_or_status": metric_or_status,
        "paper_use": paper_use,
        "limitations": limitations,
        "software_feedback": software_feedback,
    }


def exp3_claim(rows: List[Dict[str, str]], claim_id: str) -> Dict[str, str]:
    for item in rows:
        if item.get("claim_or_asset") == claim_id:
            return item
    return {}


def build_rows() -> List[Dict[str, str]]:
    casea = read_json(CASEA_RESULTS / "casea_smoke_regression.json")
    release_gate = read_json(CASEE_RESULTS / "release_gate.json")
    default_policy = read_json(CASEE_RESULTS / "casee_default_policy_gate.json")
    failure_atlas = read_json(CASEE_RESULTS / "casee_failure_mode_atlas.json")
    preflight = read_json(CASEE_RESULTS / "casee_official_run_preflight.json")
    dx1_readiness = read_json(CASEE_RESULTS / "casee_dx1_readiness_audit.json")
    candidate_sweep = read_json(CASEE_RESULTS / "casee_candidate_sweep_plan.json")
    zcenter_rerun = read_json(CASEE_RESULTS / "casee_zcenter_rerun_consistency.json")
    c002_longer_mean = read_json(CASEE_RESULTS / "casee_c002_longer_mean_audit.json")
    c003_zorigin_ablation = read_json(CASEE_RESULTS / "casee_c003_zorigin_ablation_audit.json")
    c004_dx3_low_cost = read_json(CASEE_RESULTS / "casee_c004_dx3_low_cost_audit.json")
    c005_decomposition = read_json(CASEE_RESULTS / "casee_c005_decomposition_audit.json")
    c008_c009_inlet = read_json(CASEE_RESULTS / "casee_c008_c009_inlet_turbulence_audit.json")
    c014_residual = read_json(CASEE_RESULTS / "casee_c014_residual_structure_audit.json")
    solver_ledger = read_json(CASEE_RESULTS / "casee_solver_run_provenance_ledger.json")
    claim_support = read_json(CASEE_RESULTS / "casee_claim_support_gate.json")
    build_chain = read_json(CASEE_RESULTS / "build_chain_manifest.json")
    section_pack = read_json(CASEE_RESULTS / "casee_manuscript_section_pack.json")
    exp3_rows = read_csv(PAPER_DRAFTS / "experiment3_claim_verification.csv")

    metrics = release_gate.get("metrics") or {}
    out: List[Dict[str, str]] = []

    out.append(
        row(
            experiment="Experiment 1 / AIJ Case A",
            result_id="casea_smoke_regression_guard",
            claim_readiness="paper_ready_workflow_guard" if casea.get("status") == "passed" else "blocked",
            evidence_type=str(casea.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEA_RESULTS / "casea_smoke_regression.json"),
                rel(CASEA_RESULTS / "casea_vtk_manifest.csv"),
            ],
            metric_or_status=(
                f"status={casea.get('status')}; steps_complete={casea.get('run_log_complete_2000')}; "
                f"vtk_outputs={casea.get('vtk_output_count')}; timestep_2000_vtk={casea.get('has_timestep_2000_vtk')}"
            ),
            paper_use="Use as workflow non-regression evidence for the CityLBM/FluidX3D chain.",
            limitations="Smoke regression only; it is not benchmark accuracy validation.",
            software_feedback="Keep Case A smoke as a required regression guard before stronger Case E claims.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="official_z2m_negative_validation",
            claim_readiness="limitations_ready_negative_validation",
            evidence_type="newly_run",
            source_paths=[
                rel(CASEE_RESULTS / "release_gate.json"),
                rel(CASEE_RESULTS / "casee_metrics.csv"),
                rel(CASEE_RESULTS / "casee_validation_report.md"),
            ],
            metric_or_status=(
                f"MAE={metrics.get('mae_pp')} pp; RMSE={metrics.get('rmse_pp')} pp; "
                f"bias={metrics.get('bias_pp')} pp; R2={metrics.get('r2')}; Pearson={metrics.get('pearson')}"
            ),
            paper_use="Use as transparent negative validation of the current official z=2 m Case E result.",
            limitations="Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness.",
            software_feedback="Accuracy-improvement work should target near-wall, wall-model, inlet turbulence, voxelization, and official probe protocol fidelity.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="solver_run_provenance_ledger",
            claim_readiness=str(solver_ledger.get("claim_readiness", "blocked_provenance_ledger")),
            evidence_type=str(solver_ledger.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_solver_run_provenance_ledger.json"),
                rel(CASEE_RESULTS / "casee_solver_run_provenance_ledger.csv"),
                rel(CASEE_RESULTS / "casee_solver_run_provenance_ledger.md"),
            ],
            metric_or_status=(
                f"ledger_passed={solver_ledger.get('ledger_passed')}; "
                f"row_count={solver_ledger.get('row_count')}; "
                f"solver_run_count={solver_ledger.get('solver_run_count')}; "
                f"completed_solver_run_count={solver_ledger.get('completed_solver_run_count')}; "
                f"release_gate_input_count={solver_ledger.get('release_gate_input_count')}"
            ),
            paper_use="Use as the appendix-level provenance table linking Case E metrics to commands, logs, CSVs, and claim boundaries.",
            limitations="The ledger consolidates existing outputs only; it does not add a new CFD run or change official metrics.",
            software_feedback="Keep command/log/CSV provenance as a required paper evidence layer for every future Case E candidate.",
        )
    )

    claim_support_summary = claim_support.get("summary") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="claim_support_gate",
            claim_readiness=str(claim_support_summary.get("claim_readiness", "blocked_claim_support_gate")),
            evidence_type=str(claim_support_summary.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_claim_support_gate.json"),
                rel(CASEE_RESULTS / "casee_claim_support_gate.csv"),
                rel(CASEE_RESULTS / "casee_claim_support_gate.md"),
            ],
            metric_or_status=(
                f"claim_support_gate_passed={claim_support_summary.get('claim_support_gate_passed')}; "
                f"claim_count={claim_support_summary.get('claim_count')}; "
                f"no_formal_accuracy_claims={claim_support_summary.get('no_formal_accuracy_claims')}; "
                f"forbidden_success_patterns_blocked={claim_support_summary.get('forbidden_success_patterns_blocked')}"
            ),
            paper_use="Use as a manuscript claim-triage table that separates method/protocol, negative validation, limitations-only diagnostics, and blocked release claims.",
            limitations="Claim triage only; it does not add CFD output, improve official metrics, or permit formal v0.4.0.",
            software_feedback="Keep claim-support checks downstream of release_gate and solver provenance before paper drafting.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="casee_software_policy_boundary",
            claim_readiness=str(default_policy.get("claim_readiness", "blocked_default_policy_boundary")),
            evidence_type=str(default_policy.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_default_policy_gate.json"),
                rel(CASEE_RESULTS / "casee_failure_mode_atlas.json"),
            ],
            metric_or_status=(
                f"default_policy_gate_passed={default_policy.get('default_policy_gate_passed')}; "
                f"failure_modes={len(failure_atlas.get('failure_modes', []))}; formal_allowed={release_gate.get('formal_release_allowed')}"
            ),
            paper_use="Use to explain which CityLBM settings are formal defaults and which are diagnostic switches.",
            limitations="Default-policy evidence does not improve or replace the official z=2 m metric.",
            software_feedback="Keep raw_trilinear official z=2 m as formal output; keep nuLBM, zOff and non-raw sampling diagnostic-only.",
        )
    )

    rerun_metrics = zcenter_rerun.get("rerun_metrics") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="zcenter_rerun_reproduced_failed_metric",
            claim_readiness=str(zcenter_rerun.get("claim_readiness", "blocked_rerun_consistency")),
            evidence_type=str(zcenter_rerun.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_zcenter_rerun_consistency.json"),
                rel(CASEE_RESULTS / "casee_zcenter_rerun_consistency.md"),
                str((zcenter_rerun.get("rerun_csv") or {}).get("path", "")),
                str((zcenter_rerun.get("rerun_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={zcenter_rerun.get('status')}; log_completed_48000={zcenter_rerun.get('log_completed_48000')}; "
                f"csv_sha256_equal={zcenter_rerun.get('csv_sha256_equal')}; MAE={rerun_metrics.get('mae_pp')} pp; "
                f"R2={rerun_metrics.get('r2')}; Pearson={rerun_metrics.get('pearson')}"
            ),
            paper_use="Use as newly-run reproducibility evidence that the current compiled z-center Case E setup reproduces the same negative official z=2 m metric.",
            limitations="This reinforces repeatability of the failure; it is not an accuracy improvement and cannot support formal v0.4.0.",
            software_feedback="Prioritize physical wall/inlet/voxelization changes over more repeats of the same compiled baseline.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="next_official_run_readiness",
            claim_readiness=str(preflight.get("claim_readiness", "blocked_official_followup_preflight")),
            evidence_type=str(preflight.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_official_run_preflight.json"),
                rel(CASEE_RESULTS / "casee_environment_recovery_runbook.json"),
            ],
            metric_or_status=(
                f"official_followup_run_allowed={preflight.get('official_followup_run_allowed')}; "
                f"blocked_gates={','.join(preflight.get('blocked_gates', []))}"
            ),
            paper_use="Use to document whether the next long official validation run is schedulable on this machine.",
            limitations="Runtime readiness evidence only; no new solver output is produced.",
            software_feedback="Keep Rhino new-GHA loading and native source compile evidence as operational gates before new formal Case E sweeps.",
        )
    )

    dx1_summary = dx1_readiness.get("summary") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="dx1_high_resolution_readiness",
            claim_readiness=str(dx1_readiness.get("claim_readiness", "limitations_ready_dx1_feasibility")),
            evidence_type=str(dx1_readiness.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_dx1_readiness_audit.json"),
                rel(CASEE_RESULTS / "casee_dx1_readiness_audit.md"),
                rel(CASEE_RESULTS / "casee_dx1_readiness_audit.csv"),
            ],
            metric_or_status=(
                f"dx1_readiness={dx1_summary.get('dx1_readiness')}; "
                f"memory_headroom_ok={dx1_summary.get('dx1_memory_headroom_ok')}; "
                f"run_started={dx1_summary.get('run_started')}; "
                f"required_per_gpu_gib={dx1_summary.get('generator_moderate_required_per_gpu_gib')}; "
                f"min_free_gib={dx1_summary.get('gpu_min_free_gib')}"
            ),
            paper_use="Use as a limitations/future-work statement for high-resolution official Case E follow-up planning.",
            limitations="No dx=1 FluidX3D solver output was produced; do not claim mesh independence or improved official z=2 m accuracy.",
            software_feedback="Keep dx=1 as a user-confirmed high-resolution follow-up path, not a default validation claim.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="candidate_sweep_followup_plan",
            claim_readiness=str(candidate_sweep.get("claim_readiness", "paper_ready_followup_plan; blocked formal accuracy release")),
            evidence_type=str(candidate_sweep.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_candidate_sweep_plan.json"),
                rel(CASEE_RESULTS / "casee_candidate_sweep_plan.md"),
                rel(CASEE_RESULTS / "casee_candidate_sweep_plan.csv"),
            ],
            metric_or_status=(
                f"candidate_count={candidate_sweep.get('candidate_count')}; "
                f"executable_now_count={candidate_sweep.get('executable_now_count')}; "
                f"formal_accuracy_claim_supported={candidate_sweep.get('formal_accuracy_claim_supported')}"
            ),
            paper_use="Use as a pre-registered follow-up sweep plan for improving the official z=2 m R2.",
            limitations="Planning evidence only; it does not add solver output or justify changing CityLBM defaults.",
            software_feedback="Run candidates in priority order and promote settings only after official raw_trilinear metrics pass the release gate.",
        )
    )

    c002_metrics = c002_longer_mean.get("candidate_metrics") or {}
    c002_delta = c002_longer_mean.get("metric_delta_vs_baseline") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c002_longer_mean_completed_no_improvement",
            claim_readiness=str(c002_longer_mean.get("claim_readiness", "blocked_c002_audit")),
            evidence_type=str(c002_longer_mean.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c002_longer_mean_audit.json"),
                rel(CASEE_RESULTS / "casee_c002_longer_mean_audit.md"),
                str((c002_longer_mean.get("candidate_csv") or {}).get("path", "")),
                str((c002_longer_mean.get("run_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={c002_longer_mean.get('status')}; log_completed_96000={c002_longer_mean.get('log_completed_96000')}; "
                f"MAE={c002_metrics.get('mae_pp')} pp; R2={c002_metrics.get('r2')}; Pearson={c002_metrics.get('pearson')}; "
                f"delta_MAE={c002_delta.get('mae_pp')} pp; delta_R2={c002_delta.get('r2')}; pass_condition_met={c002_longer_mean.get('pass_condition_met')}"
            ),
            paper_use="Use as candidate-run evidence that extending the averaging window alone did not improve the official z=2 m metric.",
            limitations="Completed candidate result only; it worsened the formal raw_trilinear metric and cannot be used for formal v0.4.0.",
            software_feedback="Do not promote longer averaging as a default accuracy fix; prioritize wall/inlet/voxelization changes.",
        )
    )

    c003_metrics = c003_zorigin_ablation.get("candidate_metrics") or {}
    c003_delta = c003_zorigin_ablation.get("metric_delta_vs_zcenter_baseline") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c003_zorigin_ablation_supports_sensitivity",
            claim_readiness=str(c003_zorigin_ablation.get("claim_readiness", "blocked_c003_audit")),
            evidence_type=str(c003_zorigin_ablation.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c003_zorigin_ablation_audit.json"),
                rel(CASEE_RESULTS / "casee_c003_zorigin_ablation_audit.md"),
                str((c003_zorigin_ablation.get("candidate_csv") or {}).get("path", "")),
                str((c003_zorigin_ablation.get("run_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={c003_zorigin_ablation.get('status')}; log_completed_48000={c003_zorigin_ablation.get('log_completed_48000')}; "
                f"MAE={c003_metrics.get('mae_pp')} pp; R2={c003_metrics.get('r2')}; Pearson={c003_metrics.get('pearson')}; "
                f"delta_MAE_vs_zcenter={c003_delta.get('mae_pp')} pp; delta_R2_vs_zcenter={c003_delta.get('r2')}; "
                f"consistent_with_preexisting_no_zcenter={c003_zorigin_ablation.get('consistent_with_preexisting_no_zcenter')}"
            ),
            paper_use="Use as ablation evidence that z-origin placement changes the official z=2 m metric and should be discussed as near-wall/probe-protocol sensitivity.",
            limitations="The no-z-center ablation worsened the formal metric; it cannot support formal accuracy or a default z-origin model.",
            software_feedback="Keep z-origin alignment as a diagnostic switch and prioritize physical wall/inlet/voxelization work before default promotion.",
        )
    )

    c004_metrics = c004_dx3_low_cost.get("candidate_metrics") or {}
    c004_delta = c004_dx3_low_cost.get("metric_delta_vs_zcenter_baseline") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c004_dx3_low_cost_positive_but_worse",
            claim_readiness=str(c004_dx3_low_cost.get("claim_readiness", "blocked_c004_audit")),
            evidence_type=str(c004_dx3_low_cost.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c004_dx3_low_cost_audit.json"),
                rel(CASEE_RESULTS / "casee_c004_dx3_low_cost_audit.md"),
                str((c004_dx3_low_cost.get("candidate_csv") or {}).get("path", "")),
                str((c004_dx3_low_cost.get("run_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={c004_dx3_low_cost.get('status')}; log_completed_48000={c004_dx3_low_cost.get('log_completed_48000')}; "
                f"manifest_protocol_ok={c004_dx3_low_cost.get('manifest_protocol_ok')}; MAE={c004_metrics.get('mae_pp')} pp; "
                f"R2={c004_metrics.get('r2')}; Pearson={c004_metrics.get('pearson')}; "
                f"delta_MAE_vs_zcenter={c004_delta.get('mae_pp')} pp; delta_R2_vs_zcenter={c004_delta.get('r2')}"
            ),
            paper_use="Use as low-cost dx=3 control evidence that protocol direction remains positively correlated but coarse-grid accuracy is worse.",
            limitations="Positive Pearson is not enough for formal validation; R2 remains negative and worse than the current z-center baseline.",
            software_feedback="Do not promote dx=3 coarse-grid settings as an accuracy fix; use it as a quick regression/control path.",
        )
    )

    c005_metrics = c005_decomposition.get("candidate_metrics") or {}
    c005_delta = c005_decomposition.get("metric_delta_vs_zcenter_baseline") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c005_decomposition_improves_mae_r2_but_unstable",
            claim_readiness=str(c005_decomposition.get("claim_readiness", "blocked_c005_audit")),
            evidence_type=str(c005_decomposition.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c005_decomposition_audit.json"),
                rel(CASEE_RESULTS / "casee_c005_decomposition_audit.md"),
                str((c005_decomposition.get("candidate_csv") or {}).get("path", "")),
                str((c005_decomposition.get("run_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={c005_decomposition.get('status')}; log_completed_48000={c005_decomposition.get('log_completed_48000')}; "
                f"manifest_protocol_ok={c005_decomposition.get('manifest_protocol_ok')}; MAE={c005_metrics.get('mae_pp')} pp; "
                f"R2={c005_metrics.get('r2')}; Pearson={c005_metrics.get('pearson')}; "
                f"delta_MAE_vs_zcenter={c005_delta.get('mae_pp')} pp; delta_R2_vs_zcenter={c005_delta.get('r2')}; "
                f"delta_Pearson_vs_zcenter={c005_delta.get('pearson')}; pass_condition_met={c005_decomposition.get('pass_condition_met')}"
            ),
            paper_use="Use as decomposition/runtime sensitivity evidence and as the current best negative MAE/R2 diagnostic candidate.",
            limitations="R2 remains negative, Pearson decreased versus the z-center baseline, and decomposition consistency thresholds failed; no default promotion or formal v0.4.0 claim is supported.",
            software_feedback="Record domain decomposition in generated run IDs/manifests and treat 4x1x1 as an experimental switch, not a default accuracy setting.",
        )
    )

    inlet_best = c008_c009_inlet.get("best_candidate") or {}
    inlet_metrics = inlet_best.get("candidate_metrics") or {}
    inlet_delta = inlet_best.get("delta_vs_zcenter_baseline") or {}
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c008_c015_inlet_turbulence_sgs_best_negative_candidate",
            claim_readiness=str(c008_c009_inlet.get("claim_readiness", "blocked_inlet_turbulence_audit")),
            evidence_type=str(c008_c009_inlet.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c008_c009_inlet_turbulence_audit.json"),
                rel(CASEE_RESULTS / "casee_c008_c009_inlet_turbulence_audit.md"),
                str((inlet_best.get("csv") or {}).get("path", "")),
                str((inlet_best.get("run_log") or {}).get("path", "")),
            ],
            metric_or_status=(
                f"status={c008_c009_inlet.get('status')}; best={inlet_best.get('candidate_id')}; "
                f"MAE={inlet_metrics.get('mae_pp')} pp; R2={inlet_metrics.get('r2')}; Pearson={inlet_metrics.get('pearson')}; "
                f"delta_MAE_vs_zcenter={inlet_delta.get('mae_pp')} pp; delta_R2_vs_zcenter={inlet_delta.get('r2')}; "
                f"metric_gate_passed={c008_c009_inlet.get('metric_gate_passed')}"
            ),
            paper_use="Use as the strongest current Case E diagnostic improvement and as evidence that inlet turbulence and SGS treatment are major remaining software targets.",
            limitations="R2 remains negative and the AF-k synthetic inlet/no-SGS combination is a diagnostic sweep parameter; it cannot support formal v0.4.0, predictive accuracy, LES improvement, mesh independence, or default promotion.",
            software_feedback="Keep AF-k inlet turbulence and SGS/no-SGS choices default-safe until a physically validated model reproduces positive R2 without benchmark-specific scale tuning.",
        )
    )

    c014_metrics = c014_residual.get("c014_metrics") or {}
    affine_metrics = (c014_residual.get("affine_upper_bound") or {}).get("metrics") or {}
    residual_groups = {item.get("group"): item for item in c014_residual.get("groups", [])}
    high_group = residual_groups.get("official_high_ge_0p6", {})
    downstream_group = residual_groups.get("downstream_y_lt_0_inferred", {})
    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="c014_residual_structure_blocks_accuracy_claim",
            claim_readiness=str(c014_residual.get("claim_readiness", "limitations_ready_residual_structure")),
            evidence_type=str(c014_residual.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_c014_residual_structure_audit.json"),
                rel(CASEE_RESULTS / "casee_c014_residual_structure_audit.md"),
                rel(CASEE_RESULTS / "casee_c014_residual_structure_audit.csv"),
                rel(CASEE_RESULTS / "casee_c014_residual_top_probes.csv"),
            ],
            metric_or_status=(
                f"C014_MAE={c014_metrics.get('mae_pp')} pp; C014_R2={c014_metrics.get('r2')}; "
                f"affine_upper_bound_R2={affine_metrics.get('r2')}; "
                f"downstream_R2={downstream_group.get('r2')}; high_official_bias={high_group.get('bias_pp')} pp"
            ),
            paper_use="Use as the main residual-structure explanation for why the best C014 diagnostic candidate is not yet paper-grade validation.",
            limitations="This is a newly-run audit over preexisting C014 solver output; it does not add a new FluidX3D run, change release_gate.json, or justify post-hoc calibration as validation.",
            software_feedback="Prioritize default-off wall/inlet/channel-response candidates that recover high-speed probes without overpredicting sheltered low-speed probes.",
        )
    )

    build_vs = build_chain.get("visual_studio_build_tools_2022_cpp") or {}
    build_gpu = build_chain.get("gpu_runtime") or {}
    build_gpp = build_chain.get("mingw_gpp") or {}
    out.append(
        row(
            experiment="Build-chain recovery / AIJ Case E follow-up",
            result_id="build_chain_recovery_status",
            claim_readiness=str(build_chain.get("claim_readiness", "blocked_build_chain_diagnostic")),
            evidence_type=str(build_chain.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "build_chain_manifest.json"),
                rel(CASEE_RESULTS / "build_chain_manifest.md"),
                rel(CASEE_RESULTS / "casee_official_run_preflight.json"),
            ],
            metric_or_status=(
                f"build_chain_ready={build_chain.get('build_chain_ready')}; "
                f"operational_with_fallback={build_chain.get('build_chain_operational_with_fallback')}; "
                f"vs_cpp={build_vs.get('status')}; gpp={build_gpp.get('status')}; "
                f"native_source_compile_path={build_chain.get('native_source_compile_path')}; gpu={build_gpu.get('status')}; "
                f"dotnet={(build_chain.get('dotnet_sdk') or {}).get('status')}; "
                f"fluidx3d={(build_chain.get('fluidx3d') or {}).get('status')}"
            ),
            paper_use="Use as environment/build-chain status for explaining remaining official follow-up requirements.",
            limitations="Build-chain status is not solver-output evidence and cannot support formal accuracy.",
            software_feedback="Keep VS C++ Build Tools recovery and Rhino/GHA load evidence as required operational gates before stronger software-release claims.",
        )
    )

    out.append(
        row(
            experiment="Experiment 2 / AIJ Case E",
            result_id="casee_manuscript_section_pack",
            claim_readiness=str(section_pack.get("claim_readiness", "blocked_manuscript_section_pack")),
            evidence_type=str(section_pack.get("evidence_type", "missing")),
            source_paths=[
                rel(CASEE_RESULTS / "casee_manuscript_section_pack.json"),
                rel(CASEE_RESULTS / "casee_manuscript_section_pack_qa.md"),
                rel(PAPER_DRAFTS / "casee_v04_manuscript_section_pack_en.md"),
            ],
            metric_or_status=(
                f"section_pack_passed={section_pack.get('section_pack_passed')}; "
                f"formal_accuracy_claim_supported={section_pack.get('formal_accuracy_claim_supported')}; "
                f"formal_release_allowed={section_pack.get('formal_release_allowed')}"
            ),
            paper_use="Use as ready-to-edit Methods, Results, Diagnostics, Limitations, Software implications, and Release-boundary prose for the negative-validation Case E result.",
            limitations="Generated prose only; it does not add CFD output, improve official z=2 m metrics, or support formal accuracy.",
            software_feedback="Keep manuscript prose generation downstream of release_gate and manuscript_results_table so claim boundaries stay synchronized.",
        )
    )

    selected_exp3 = [
        "module_claim_M1",
        "module_claim_R1",
        "module_claim_R2",
        "module_claim_R3",
        "module_claim_R4",
        "module_claim_L1",
        "module_claim_NUMERICAL_PROTOCOL",
        "module_claim_FINAL_DISCUSSION",
    ]
    for claim_id in selected_exp3:
        claim = exp3_claim(exp3_rows, claim_id)
        if not claim:
            out.append(
                row(
                    experiment="Experiment 3 / TUM2TWIN digital-twin application",
                    result_id=claim_id,
                    claim_readiness="blocked",
                    evidence_type="missing",
                    source_paths=[rel(PAPER_DRAFTS / "experiment3_claim_verification.csv")],
                    metric_or_status="missing from claim verification table",
                    paper_use="Do not use until the source claim row is restored.",
                    limitations="Missing source row.",
                )
            )
            continue
        readiness = claim.get("verification_status") or claim.get("paper_use") or "unknown"
        out.append(
            row(
                experiment="Experiment 3 / TUM2TWIN digital-twin application",
                result_id=claim_id,
                claim_readiness=readiness,
                evidence_type=claim.get("evidence_type", ""),
                source_paths=[claim.get("source", "")],
                metric_or_status=claim.get("value_or_status", ""),
                paper_use=claim.get("paper_use", ""),
                limitations=(
                    "Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, "
                    "GCBTE and CityLBM-GH end-to-end execution remain unsupported."
                    if "blocked" in claim.get("evidence_type", "") or "boundary" in readiness or claim_id == "module_claim_L1"
                    else "Use within the archived Experiment 3 scope."
                ),
                software_feedback="Use as design-application workflow evidence, not as Case E accuracy evidence.",
            )
        )

    figure_rows = [
        item
        for item in exp3_rows
        if item.get("claim_or_asset", "").startswith(("Fig.", "Table "))
        and item.get("verification_status") == "available_for_manual_review"
    ]
    out.append(
        row(
            experiment="Experiment 3 / TUM2TWIN digital-twin application",
            result_id="figure_table_manual_review_packet",
            claim_readiness="available_for_manual_review" if figure_rows else "blocked",
            evidence_type="newly_run + preexisting_artifact",
            source_paths=[rel(PAPER_DRAFTS / "experiment3_claim_verification.csv")],
            metric_or_status=f"available_figure_table_callouts={len(figure_rows)}",
            paper_use="Use as a checklist for manual figure/table selection in the manuscript.",
            limitations="Figure/table availability is not independent validation of CFD accuracy.",
            software_feedback="Keep release assets lightweight and hash-indexed; large VTK/3DM files should remain external or release assets.",
        )
    )

    out.append(
        row(
            experiment="CityLBM v0.4.0 release boundary",
            result_id="manifest_schema_traceability",
            claim_readiness="paper_ready_manifest_schema_boundary",
            evidence_type="newly_run",
            source_paths=[
                rel(CASEE_RESULTS / "citylbm_manifest_schema_gate.json"),
                rel(CASEE_RESULTS / "citylbm_manifest_schema_gate.md"),
            ],
            metric_or_status="manifest_schema_gate_passed=true; formal_accuracy_claim_supported=false",
            paper_use="Use to state that generated run manifests have an auditable Case E protocol and claim-boundary schema.",
            limitations="Manifest schema evidence does not add CFD output or improve official z=2 m metrics.",
            software_feedback="Keep manifest schema checks in the release-candidate evidence chain before stronger paper claims.",
        )
    )

    out.append(
        row(
            experiment="CityLBM v0.4.0 release boundary",
            result_id="formal_release_block",
            claim_readiness="blocked_formal_release_gate",
            evidence_type="newly_run",
            source_paths=[rel(CASEE_RESULTS / "release_gate.json")],
            metric_or_status=f"formal_release_allowed={release_gate.get('formal_release_allowed')}; recommended_tag={release_gate.get('recommended_tag')}",
            paper_use="Use to state that this is an rc diagnostic line, not formal v0.4.0.",
            limitations="Formal v0.4.0 remains prohibited until the official z=2 m metric gate and Rhino/GHA loading gate pass.",
            software_feedback="Version software as release candidates until the formal gate passes.",
        )
    )

    return out


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in rows:
            writer.writerow(item)


def summarize(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    readiness_counts: Dict[str, int] = {}
    evidence_counts: Dict[str, int] = {}
    for item in rows:
        readiness = item["claim_readiness"]
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
        evidence = item["evidence_type"]
        evidence_counts[evidence] = evidence_counts.get(evidence, 0) + 1
    forbidden_claims_blocked = any(item["result_id"] == "formal_release_block" for item in rows)
    casee_negative = any(item["result_id"] == "official_z2m_negative_validation" for item in rows)
    exp3_boundary = any(item["result_id"] == "module_claim_L1" for item in rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(rows),
        "readiness_counts": readiness_counts,
        "evidence_type_counts": evidence_counts,
        "paper_results_packet_passed": forbidden_claims_blocked and casee_negative and exp3_boundary,
        "formal_accuracy_claim_supported": False,
        "formal_v0_4_0_allowed": False,
        "boundary": (
            "The packet is a manuscript organization and claim-control artifact. "
            "It preserves negative-validation and limitations boundaries and does not add new CFD results."
        ),
    }


def write_markdown(path: Path, rows: List[Dict[str, str]], summary: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Paper Results Packet",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Packet passed: {summary['paper_results_packet_passed']}",
        f"- Result rows: {summary['result_count']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {summary['formal_v0_4_0_allowed']}",
        "",
        "## Readiness Counts",
        "",
    ]
    for key in sorted(summary["readiness_counts"]):
        lines.append(f"- {key}: {summary['readiness_counts'][key]}")

    lines += [
        "",
        "## Paper-Ready Or Usable Results",
        "",
        "| experiment | result | readiness | metric/status | paper use |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        if item["claim_readiness"].startswith(("paper_ready", "usable", "available")):
            lines.append(
                f"| {item['experiment']} | `{item['result_id']}` | {item['claim_readiness']} | {item['metric_or_status']} | {item['paper_use']} |"
            )

    lines += [
        "",
        "## Limitations And Blocked Claims",
        "",
        "| experiment | result | readiness | limitation | software feedback |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        if "limitations" in item["claim_readiness"] or "blocked" in item["claim_readiness"] or item["limitations"]:
            lines.append(
                f"| {item['experiment']} | `{item['result_id']}` | {item['claim_readiness']} | {item['limitations']} | {item['software_feedback']} |"
            )

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
            rel(CASEE_RESULTS / "release_gate.json"),
            rel(CASEE_RESULTS / "casee_default_policy_gate.json"),
            rel(CASEE_RESULTS / "casee_failure_mode_atlas.json"),
            rel(CASEE_RESULTS / "casee_official_run_preflight.json"),
            rel(CASEE_RESULTS / "casee_dx1_readiness_audit.json"),
            rel(CASEE_RESULTS / "build_chain_manifest.json"),
            rel(CASEE_RESULTS / "casee_c005_decomposition_audit.json"),
            rel(CASEE_RESULTS / "casee_c008_c009_inlet_turbulence_audit.json"),
            rel(CASEE_RESULTS / "casee_c014_residual_structure_audit.json"),
            rel(CASEE_RESULTS / "casee_claim_support_gate.json"),
            rel(CASEE_RESULTS / "casee_manuscript_section_pack.json"),
            rel(PAPER_DRAFTS / "experiment3_claim_verification.csv"),
            rel(PAPER_DRAFTS / "casee_v04_manuscript_section_pack_en.md"),
            rel(PAPER_DRAFTS / "experiment3_publication_readiness_checklist.md"),
            rel(EXP3_ROOT),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"paper_results_packet_passed": summary["paper_results_packet_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["paper_results_packet_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
