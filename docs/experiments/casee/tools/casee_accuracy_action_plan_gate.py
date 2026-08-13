#!/usr/bin/env python3
"""Prioritize next Case E actions from the quantified accuracy gap."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"

RELEASE_GATE = RESULTS_DIR / "release_gate.json"
ACCURACY_GAP = RESULTS_DIR / "casee_research_accuracy_gap_gate.json"
CANDIDATE_SWEEP = RESULTS_DIR / "casee_candidate_sweep_plan.json"
RUNBOOK = RESULTS_DIR / "casee_next_experiment_runbook.json"
C014_AUDIT = RESULTS_DIR / "casee_c014_residual_structure_audit.json"
PREFLIGHT = RESULTS_DIR / "casee_official_run_preflight.json"
GPU_FAILFAST = RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json"
RHINO_PACKET = RESULTS_DIR / "casee_rhino_load_evidence_packet_gate.json"
DEFAULT_PROMOTION = RESULTS_DIR / "casee_default_promotion_gate.json"

OUT_JSON = RESULTS_DIR / "casee_accuracy_action_plan_gate.json"
OUT_CSV = RESULTS_DIR / "casee_accuracy_action_plan_gate.csv"
OUT_MD = RESULTS_DIR / "casee_accuracy_action_plan_gate.md"

FIELDNAMES = [
    "action_id",
    "priority",
    "action_class",
    "enabled_now",
    "blocked_by",
    "source_evidence_type",
    "source_paths",
    "command_or_operator_action",
    "expected_artifacts",
    "metric_target",
    "default_setting_allowed",
    "paper_use",
    "limitations",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def find_runbook_command(runbook: Dict[str, Any], runbook_id: str) -> Dict[str, Any]:
    for item in runbook.get("commands", []):
        if item.get("runbook_id") == runbook_id:
            return item
    return {}


def find_candidate(sweep: Dict[str, Any], candidate_id: str) -> Dict[str, Any]:
    for item in sweep.get("candidates", []):
        if item.get("candidate_id") == candidate_id:
            return item
    return {}


def action(
    *,
    action_id: str,
    priority: int,
    action_class: str,
    enabled_now: bool,
    blocked_by: Iterable[str],
    source_evidence_type: str,
    source_paths: Iterable[Path],
    command_or_operator_action: str,
    expected_artifacts: Iterable[str],
    metric_target: str,
    default_setting_allowed: bool,
    paper_use: str,
    limitations: str,
) -> Dict[str, Any]:
    return {
        "action_id": action_id,
        "priority": priority,
        "action_class": action_class,
        "enabled_now": enabled_now,
        "blocked_by": ";".join(blocked_by),
        "source_evidence_type": source_evidence_type,
        "source_paths": "; ".join(rel(path) for path in source_paths),
        "command_or_operator_action": command_or_operator_action,
        "expected_artifacts": "; ".join(expected_artifacts),
        "metric_target": metric_target,
        "default_setting_allowed": default_setting_allowed,
        "paper_use": paper_use,
        "limitations": limitations,
    }


def build_rows() -> List[Dict[str, Any]]:
    release_gate = read_json(RELEASE_GATE)
    gap = read_json(ACCURACY_GAP)
    sweep = read_json(CANDIDATE_SWEEP)
    runbook = read_json(RUNBOOK)
    c014 = read_json(C014_AUDIT)
    preflight = read_json(PREFLIGHT)
    gpu = read_json(GPU_FAILFAST)
    rhino_packet = read_json(RHINO_PACKET)
    default_promotion = read_json(DEFAULT_PROMOTION)

    gap_summary = gap.get("summary") or {}
    blockers = gap_summary.get("blockers") or {}
    blocked_gates = list(preflight.get("blocked_gates") or [])
    gpu_ready = gpu.get("gpu_runtime_ready") is True or gpu.get("claim_readiness") == "gpu_ready"
    rhino_claim_ready = rhino_packet.get("manual_rhino_load_claim_ready") is True
    official_followup_allowed = preflight.get("official_followup_run_allowed") is True
    c014_metrics = c014.get("c014_metrics") or {}
    affine = (c014.get("affine_upper_bound") or {}).get("metrics") or {}

    r004 = find_runbook_command(runbook, "R004_rhino_gha_load_check")
    r006 = find_runbook_command(runbook, "R006_wall_model_followup")
    r007 = find_runbook_command(runbook, "R007_inlet_turbulence_followup")
    r009 = find_runbook_command(runbook, "R009_postrun_official_audit")
    r010 = find_runbook_command(runbook, "R010_c016_residual_channel_response_followup")
    c014_candidate = find_candidate(sweep, "C014_inlet_k_synthetic_fullplane_s2p00_no_sgs")

    return [
        action(
            action_id="A001_keep_formal_release_blocked",
            priority=1,
            action_class="release_safety",
            enabled_now=True,
            blocked_by=[],
            source_evidence_type="newly_run",
            source_paths=[RELEASE_GATE, ACCURACY_GAP, DEFAULT_PROMOTION],
            command_or_operator_action="python docs/experiments/casee/tools/release_gate.py",
            expected_artifacts=[rel(RELEASE_GATE), rel(ACCURACY_GAP), rel(DEFAULT_PROMOTION)],
            metric_target=(
                f"Current gap: MAE +{gap_summary.get('formal_official_mae_gap_to_15pp')} pp over threshold; "
                f"R2 gap {gap_summary.get('formal_official_r2_gap_to_positive')}."
            ),
            default_setting_allowed=False,
            paper_use="Use as release-boundary and limitations evidence.",
            limitations="Safety action only; it does not improve the simulation.",
        ),
        action(
            action_id="A002_complete_rhino_gha_manual_load_packet",
            priority=2,
            action_class="software_load_evidence",
            enabled_now=not rhino_claim_ready,
            blocked_by=[] if not rhino_claim_ready else ["already_claim_ready"],
            source_evidence_type=str(rhino_packet.get("evidence_type") or "newly_run"),
            source_paths=[RHINO_PACKET],
            command_or_operator_action=r004.get("command", "Manual Rhino/Grasshopper Plugin Identity capture."),
            expected_artifacts=[str(r004.get("expected_artifact") or "docs/experiments/casee/results/rhino_gha_load_manifest.json")],
            metric_target="Close Rhino/GHA load blocker before formal release; no CFD metric change expected.",
            default_setting_allowed=False,
            paper_use="Use as software identity/load evidence after real manifest and screenshots exist.",
            limitations="Manual software-load evidence only; not accuracy validation.",
        ),
        action(
            action_id="A003_recover_gpu_and_preflight",
            priority=3,
            action_class="environment_recovery",
            enabled_now=not official_followup_allowed,
            blocked_by=[] if not gpu_ready else blocked_gates,
            source_evidence_type="newly_run",
            source_paths=[GPU_FAILFAST, PREFLIGHT, RUNBOOK],
            command_or_operator_action="nvidia-smi; python docs/experiments/casee/tools/casee_official_run_preflight.py",
            expected_artifacts=[rel(GPU_FAILFAST), rel(PREFLIGHT)],
            metric_target="Enable official follow-up scheduling; no CFD metric change expected until FluidX3D completes.",
            default_setting_allowed=False,
            paper_use="Use as remaining-blocker evidence.",
            limitations="Environment readiness only.",
        ),
        action(
            action_id="A004_run_wall_model_followup_first",
            priority=4,
            action_class="official_cfd_followup_after_recovery",
            enabled_now=official_followup_allowed,
            blocked_by=[] if official_followup_allowed else blocked_gates,
            source_evidence_type=str(r006.get("evidence_type") or "blocked_until_gpu_ready"),
            source_paths=[RUNBOOK, CANDIDATE_SWEEP, ACCURACY_GAP],
            command_or_operator_action=str(r006.get("command") or ""),
            expected_artifacts=r006.get("expected_artifact", "").split("; ") if r006.get("expected_artifact") else [],
            metric_target="Official raw_trilinear z=2 m: MAE <15 pp, R2 >0, Pearson >0.",
            default_setting_allowed=False,
            paper_use="Use only after completed FluidX3D output is audited by casee_audit.py.",
            limitations="Generated input or planned action is not a result; wall model remains default-off until gates pass.",
        ),
        action(
            action_id="A005_run_afk_nosgs_inlet_followup_second",
            priority=5,
            action_class="official_cfd_followup_after_recovery",
            enabled_now=official_followup_allowed,
            blocked_by=[] if official_followup_allowed else blocked_gates,
            source_evidence_type=str(c014.get("solver_output_evidence_type") or r007.get("evidence_type") or "preexisting_artifact"),
            source_paths=[C014_AUDIT, RUNBOOK, CANDIDATE_SWEEP],
            command_or_operator_action=str(r007.get("command") or ""),
            expected_artifacts=r007.get("expected_artifact", "").split("; ") if r007.get("expected_artifact") else [],
            metric_target=(
                f"C014 diagnostic: MAE={c014_metrics.get('mae_pp')}, R2={c014_metrics.get('r2')}; "
                "follow-up must turn official R2 positive without diagnostic sampling."
            ),
            default_setting_allowed=False,
            paper_use="Use as the strongest diagnostic direction, not as a validated default.",
            limitations="C014 remains negative R2 and default-off; preexisting diagnostic evidence only.",
        ),
        action(
            action_id="A006_run_c016_channel_response_only_after_leakage_guard",
            priority=6,
            action_class="official_cfd_followup_after_recovery",
            enabled_now=official_followup_allowed,
            blocked_by=[] if official_followup_allowed else blocked_gates,
            source_evidence_type=str(r010.get("evidence_type") or "blocked_until_gpu_ready"),
            source_paths=[RUNBOOK, RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json", ACCURACY_GAP],
            command_or_operator_action=str(r010.get("command") or ""),
            expected_artifacts=r010.get("expected_artifact", "").split("; ") if r010.get("expected_artifact") else [],
            metric_target="R2 >0 and MAE below C014 without fitting RS_caseE target values.",
            default_setting_allowed=False,
            paper_use="Use as pre-registered follow-up only after official audit.",
            limitations="Residual-target logic is experimental and cannot be default-promoted without formal gates.",
        ),
        action(
            action_id="A007_audit_any_new_probe_csv_immediately",
            priority=7,
            action_class="postrun_audit",
            enabled_now=False,
            blocked_by=["awaiting_completed_fluidx3d_probe_csv"],
            source_evidence_type=str(r009.get("evidence_type") or "newly_run_when_executed"),
            source_paths=[RUNBOOK, RELEASE_GATE],
            command_or_operator_action=str(r009.get("command") or "python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <csv>"),
            expected_artifacts=[rel(RELEASE_GATE), rel(RESULTS_DIR / "casee_validation_report.md")],
            metric_target="Only audited n=80 official z=2 m raw_trilinear CSV can update release_gate.json.",
            default_setting_allowed=False,
            paper_use="Use as the sole path for future official paper metrics.",
            limitations="No unaudited CSV can be cited.",
        ),
        action(
            action_id="A008_reject_post_hoc_affine_as_default",
            priority=8,
            action_class="claim_boundary",
            enabled_now=True,
            blocked_by=[],
            source_evidence_type=str(c014.get("evidence_type") or "newly_run"),
            source_paths=[C014_AUDIT, ACCURACY_GAP],
            command_or_operator_action="No run. Keep post-hoc affine upper bound in limitations only.",
            expected_artifacts=[rel(C014_AUDIT), rel(ACCURACY_GAP)],
            metric_target=f"Affine upper-bound R2={affine.get('r2')} is diagnostic-only and cannot validate prediction.",
            default_setting_allowed=False,
            paper_use="Use as limitations evidence against calibration-as-validation.",
            limitations="Post-hoc fit is not a predictive solver result.",
        ),
    ]


def build_payload() -> Dict[str, Any]:
    release_gate = read_json(RELEASE_GATE)
    gap = read_json(ACCURACY_GAP)
    default_promotion = read_json(DEFAULT_PROMOTION)
    rows = build_rows()
    enabled = [row for row in rows if row["enabled_now"]]
    official_actions = [row for row in rows if row["action_class"] == "official_cfd_followup_after_recovery"]
    gate_passed = (
        bool(rows)
        and release_gate.get("formal_release_allowed") is False
        and gap.get("research_accuracy_gap_gate_passed") is True
        and default_promotion.get("any_diagnostic_default_promotion_allowed") is False
        and not any(bool(row["default_setting_allowed"]) for row in rows)
        and any(row["action_id"] == "A004_run_wall_model_followup_first" for row in official_actions)
        and any(row["action_id"] == "A005_run_afk_nosgs_inlet_followup_second" for row in official_actions)
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "accuracy_action_plan_gate_passed": gate_passed,
        "claim_readiness": "paper_ready_action_plan; blocked formal accuracy release",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "recommended_tag": release_gate.get("recommended_tag"),
        "enabled_now_count": len(enabled),
        "official_followup_action_count": len(official_actions),
        "rows": rows,
        "summary": {
            "next_enabled_actions": [row["action_id"] for row in enabled],
            "official_followups_after_recovery": [row["action_id"] for row in official_actions],
            "all_default_setting_allowed_false": not any(bool(row["default_setting_allowed"]) for row in rows),
            "formal_metric_gap": (gap.get("summary") or {}),
        },
        "boundary": (
            "This action plan prioritizes next steps from existing evidence. It does not run FluidX3D, "
            "does not update official metrics, does not promote diagnostic settings to defaults, and does not permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Accuracy Action Plan Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Action plan gate passed: {payload['accuracy_action_plan_gate_passed']}",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        f"- Recommended tag: `{payload['recommended_tag']}`",
        f"- Enabled-now actions: {payload['enabled_now_count']}",
        "",
        "## Actions",
        "",
        "| priority | action | class | enabled | blocked by | default? |",
        "|---:|---|---|---:|---|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['priority']} | `{row['action_id']}` | `{row['action_class']}` | "
            f"{row['enabled_now']} | {row['blocked_by']} | {row['default_setting_allowed']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["rows"])
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "accuracy_action_plan_gate_passed": payload["accuracy_action_plan_gate_passed"],
                "enabled_now_count": payload["enabled_now_count"],
                "official_followup_action_count": payload["official_followup_action_count"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["accuracy_action_plan_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
