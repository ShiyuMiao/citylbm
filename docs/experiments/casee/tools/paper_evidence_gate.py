#!/usr/bin/env python3
"""Audit whether Case E evidence and manuscript drafts stay within claim bounds."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PAPER_DRAFTS_DIR = ROOT / "academic-paper-writer" / "paper-drafts"

REQUIRED_ARTIFACTS = [
    "CityLBM/bin/CityLBM.gha",
    "docs/experiments/casee/results/release_gate.json",
    "docs/experiments/casee/results/casee_metrics.csv",
    "docs/experiments/casee/results/casee_validation_report.md",
    "docs/experiments/casee/results/casee_manuscript_claim_matrix.csv",
    "docs/experiments/casee/results/casee_paper_evidence_gate.json",
    "docs/experiments/casee/results/casee_paper_appendix_manifest.json",
    "docs/experiments/casee/results/casee_remaining_blockers.json",
    "docs/experiments/casee/results/casee_remaining_blockers.md",
    "docs/experiments/casee/results/casee_next_experiment_runbook.json",
    "docs/experiments/casee/results/casee_next_experiment_runbook.md",
    "docs/experiments/casee/results/build_chain_manifest.json",
    "docs/experiments/casee/results/build_chain_manifest.csv",
    "docs/experiments/casee/results/build_chain_manifest.md",
    "docs/experiments/casee/results/rhino_gha_load_gate.json",
    "docs/experiments/casee/results/rhino_gha_load_gate.md",
    "docs/experiments/casee/results/casee_official_run_preflight.json",
    "docs/experiments/casee/results/casee_official_run_preflight.md",
    "docs/experiments/casee/results/casee_dx1_readiness_audit.json",
    "docs/experiments/casee/results/casee_dx1_readiness_audit.csv",
    "docs/experiments/casee/results/casee_dx1_readiness_audit.md",
    "docs/experiments/casee/results/casee_environment_recovery_runbook.json",
    "docs/experiments/casee/results/casee_environment_recovery_runbook.md",
    "docs/experiments/casee/results/casee_failure_mode_atlas.json",
    "docs/experiments/casee/results/casee_failure_mode_atlas.md",
    "docs/experiments/casee/results/casee_failure_mode_atlas.png",
    "docs/experiments/casee/results/casee_zcenter_rerun_consistency.json",
    "docs/experiments/casee/results/casee_zcenter_rerun_consistency.md",
    "docs/experiments/casee/results/casee_c002_longer_mean_audit.json",
    "docs/experiments/casee/results/casee_c002_longer_mean_audit.md",
    "docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json",
    "docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.md",
    "docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json",
    "docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.md",
    "docs/experiments/casee/results/casee_c005_decomposition_audit.json",
    "docs/experiments/casee/results/casee_c005_decomposition_audit.md",
    "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json",
    "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md",
    "docs/experiments/casee/results/casee_c016_residual_target_leakage_guard.json",
    "docs/experiments/casee/results/casee_c016_residual_target_leakage_guard.md",
    "docs/experiments/casee/results/casee_solver_run_provenance_ledger.json",
    "docs/experiments/casee/results/casee_solver_run_provenance_ledger.md",
    "docs/experiments/casee/results/casee_candidate_sweep_plan.json",
    "docs/experiments/casee/results/casee_candidate_sweep_plan.md",
    "docs/experiments/casee/results/casee_default_policy_gate.json",
    "docs/experiments/casee/results/casee_default_policy_gate.md",
    "docs/experiments/casee/results/casee_manuscript_results_table.json",
    "docs/experiments/casee/results/casee_manuscript_results_table.md",
    "docs/experiments/casee/results/casee_manuscript_section_pack.json",
    "docs/experiments/casee/results/casee_manuscript_section_pack_qa.md",
    "academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md",
    "docs/experiments/casee/results/casee_paper_results_figure.svg",
    "docs/experiments/casee/results/casee_paper_results_figure.png",
    "docs/experiments/casee/results/casee_paper_results_figure_source.csv",
    "docs/experiments/casee/results/casee_paper_results_figure_qa.json",
    "docs/experiments/casee/results/casee_paper_results_figure_qa.md",
    "docs/experiments/casee/results/citylbm_paper_results_packet.json",
    "docs/experiments/casee/results/citylbm_paper_results_packet.md",
    "docs/experiments/casee/results/citylbm_manifest_output_gate.json",
    "docs/experiments/casee/results/citylbm_manifest_output_gate.md",
    "docs/experiments/casee/results/citylbm_manifest_schema_gate.json",
    "docs/experiments/casee/results/citylbm_manifest_schema_gate.md",
    "docs/experiments/casee/results/citylbm_software_feedback_matrix.json",
    "docs/experiments/casee/results/citylbm_software_feedback_matrix.md",
    "docs/experiments/casee/results/casee_claim_support_gate.json",
    "docs/experiments/casee/results/casee_claim_support_gate.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md",
    "docs/experiments/casee/results/plugin_identity_gate.json",
    "docs/releases/v0.4.0-rc52.md",
]

FORBIDDEN_SUCCESS_PATTERNS = [
    "has passed AIJ Case E accuracy validation",
    "validated predictive accuracy",
    "research-grade predictive accuracy",
    "LES improvement",
    "mesh independence",
    "official z=2 m validation result",
    "精度验证通过",
    "科研级预测精度",
    "已通过 AIJ Case E",
    "网格无关性",
]

NEGATION_MARKERS = [
    "not ",
    "cannot ",
    "should not ",
    "does not ",
    "do not ",
    "rather than ",
    "不能",
    "不应",
    "不可",
    "未",
    "不得",
    "不能写",
    "不满足",
]

FORBIDDEN_SECTION_MARKERS = [
    "## Forbidden",
    "## 禁止",
    "## 论文中不能写",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def metric_gate_status(gate: Dict[str, Any]) -> Dict[str, Any]:
    metrics = gate.get("metrics") or {}
    r2 = metrics.get("r2")
    mae = metrics.get("mae_pp")
    pearson = metrics.get("pearson")
    formal_allowed = bool(gate.get("formal_release_allowed", False))
    return {
        "formal_release_allowed": formal_allowed,
        "recommended_tag": gate.get("recommended_tag", ""),
        "official_z2m_r2": r2,
        "official_z2m_mae_pp": mae,
        "official_z2m_pearson": pearson,
        "formal_metric_is_negative_validation": bool(r2 is not None and float(r2) < 0.0),
    }


def claim_matrix_status(rows: List[Dict[str, str]], recommended_tag: str) -> Dict[str, Any]:
    readiness_counts: Dict[str, int] = {}
    for row in rows:
        readiness = row.get("claim_readiness", "unknown")
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1

    joined = "\n".join(" ".join(row.values()) for row in rows)
    overstated_paper_ready: List[str] = []
    for row in rows:
        readiness = row.get("claim_readiness", "")
        text = " ".join(row.values()).lower()
        if readiness == "paper_ready" and any(p.lower() in text for p in FORBIDDEN_SUCCESS_PATTERNS):
            overstated_paper_ready.append(row.get("claim_id", "unknown"))

    return {
        "claim_count": len(rows),
        "readiness_counts": readiness_counts,
        "blocked_release_claim_present": "Formal CityLBM v0.4.0 release is not allowed" in joined,
        "negative_validation_claim_present": "does not meet the release accuracy gate" in joined,
        "recommended_tag_present": recommended_tag in joined if recommended_tag else False,
        "no_overstated_paper_ready_claims": not overstated_paper_ready,
        "overstated_paper_ready_claim_ids": overstated_paper_ready,
    }


def in_forbidden_section(line: str, current_forbidden: bool) -> bool:
    stripped = line.strip()
    if stripped.startswith("## "):
        return any(stripped.startswith(marker) for marker in FORBIDDEN_SECTION_MARKERS)
    return current_forbidden


def line_is_negated(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in NEGATION_MARKERS)


def scan_draft(path: Path) -> Tuple[List[Dict[str, Any]], int]:
    violations: List[Dict[str, Any]] = []
    forbidden_section = False
    checked_lines = 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        forbidden_section = in_forbidden_section(line, forbidden_section)
        if not line.strip():
            continue
        checked_lines += 1
        lower = line.lower()
        for pattern in FORBIDDEN_SUCCESS_PATTERNS:
            if pattern.lower() not in lower:
                continue
            if forbidden_section or line_is_negated(line):
                continue
            violations.append(
                {
                    "path": display_path(path),
                    "line": lineno,
                    "pattern": pattern,
                    "text": line.strip(),
                }
            )
    return violations, checked_lines


def draft_status(paths: Iterable[Path]) -> Dict[str, Any]:
    all_violations: List[Dict[str, Any]] = []
    checked_files: List[str] = []
    checked_lines = 0
    for path in paths:
        if not path.exists():
            continue
        violations, n_lines = scan_draft(path)
        checked_files.append(display_path(path))
        checked_lines += n_lines
        all_violations.extend(violations)
    return {
        "checked_files": checked_files,
        "checked_nonblank_lines": checked_lines,
        "forbidden_success_claim_violations": all_violations,
        "draft_claim_boundary_passed": not all_violations and bool(checked_files),
    }


def artifact_index_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "artifact_index_found": False,
            "artifact_count": 0,
            "lightweight_release_asset_count": 0,
            "formal_accuracy_claim_supported": None,
            "required_artifacts_present": False,
            "missing_required_artifacts": REQUIRED_ARTIFACTS,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    artifacts = data.get("artifacts", [])
    paths = {str(row.get("path", "")) for row in artifacts}
    missing = [item for item in REQUIRED_ARTIFACTS if item not in paths]
    summary = data.get("summary", {})
    return {
        "artifact_index_found": True,
        "artifact_count": summary.get("artifact_count", len(artifacts)),
        "lightweight_release_asset_count": summary.get("lightweight_release_asset_count", 0),
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "required_artifacts_present": not missing,
        "missing_required_artifacts": missing,
    }


def rhino_gate_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "rhino_gate_found": False,
            "rhino_loaded_new_gha": False,
            "claim_readiness": "missing",
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    loaded = bool(data.get("rhino_loaded_new_gha"))
    return {
        "rhino_gate_found": True,
        "rhino_loaded_new_gha": loaded,
        "claim_readiness": readiness,
        "manual_manifest_present": bool(data.get("manual_manifest_present")),
        "claim_boundary_safe": loaded or readiness == "blocked_manual_rhino_load",
    }


def build_chain_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "build_chain_found": False,
            "build_chain_ready": False,
            "claim_readiness": "missing",
            "vs_cpp_status": "missing",
            "gpp_status": "missing",
            "native_source_compile_ready": False,
            "native_source_compile_path": "missing",
            "dotnet_status": "missing",
            "fluidx3d_status": "missing",
            "gpu_status": "missing",
            "uac_blocker_recorded": False,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    vs_status = str((data.get("visual_studio_build_tools_2022_cpp") or {}).get("status", ""))
    dotnet_status = str((data.get("dotnet_sdk") or {}).get("status", ""))
    gpp_status = str((data.get("mingw_gpp") or {}).get("status", ""))
    fluidx3d_status = str((data.get("fluidx3d") or {}).get("status", ""))
    gpu_status = str((data.get("gpu_runtime") or {}).get("status", ""))
    readiness = str(data.get("claim_readiness", ""))
    build_ready = bool(data.get("build_chain_ready"))
    native_source_compile_ready = bool(data.get("native_source_compile_ready"))
    return {
        "build_chain_found": True,
        "build_chain_ready": build_ready,
        "claim_readiness": readiness,
        "vs_cpp_status": vs_status,
        "gpp_status": gpp_status,
        "native_source_compile_ready": native_source_compile_ready,
        "native_source_compile_path": data.get("native_source_compile_path", ""),
        "dotnet_status": dotnet_status,
        "fluidx3d_status": fluidx3d_status,
        "gpu_status": gpu_status,
        "uac_blocker_recorded": any(
            "UAC" in item or "1602" in item
            for item in ((data.get("visual_studio_build_tools_2022_cpp") or {}).get("install_attempt") or {}).get("observed_blockers", [])
        ),
        "claim_boundary_safe": (
            readiness in {"build_chain_ready", "blocked_build_chain_diagnostic"}
            and dotnet_status == "ready"
            and fluidx3d_status == "ready_for_existing_binary"
            and gpu_status in {"ready", "blocked"}
            and (native_source_compile_ready or vs_status == "blocked")
        ),
    }


def preflight_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "preflight_found": False,
            "official_followup_run_allowed": None,
            "formal_release_allowed": None,
            "claim_readiness": "missing",
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "preflight_found": True,
        "official_followup_run_allowed": data.get("official_followup_run_allowed"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_readiness": readiness,
        "blocked_gates": data.get("blocked_gates", []),
        "claim_boundary_safe": readiness in {"blocked_official_followup_preflight", "ready_for_next_official_followup_run"},
    }


def dx1_readiness_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "dx1_readiness_found": False,
            "dx1_readiness_audit_passed": False,
            "claim_readiness": "missing",
            "dx1_readiness": "missing",
            "run_started": None,
            "formal_accuracy_claim_supported": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    summary = data.get("summary") or {}
    return {
        "dx1_readiness_found": True,
        "dx1_readiness_audit_passed": summary.get("dx1_readiness_audit_passed"),
        "claim_readiness": readiness,
        "dx1_readiness": summary.get("dx1_readiness"),
        "dx1_memory_headroom_ok": summary.get("dx1_memory_headroom_ok"),
        "run_started": summary.get("run_started"),
        "run_allowed_without_user_confirmation": summary.get("run_allowed_without_user_confirmation"),
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "claim_boundary_safe": (
            summary.get("dx1_readiness_audit_passed") is True
            and readiness == "limitations_ready_dx1_feasibility"
            and summary.get("run_started") is False
            and summary.get("formal_accuracy_claim_supported") is False
        ),
    }


def recovery_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "recovery_found": False,
            "formal_release_allowed": None,
            "claim_readiness": "missing",
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "recovery_found": True,
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_readiness": readiness,
        "blocked_gates": data.get("blocked_gates", []),
        "step_count": len(data.get("steps", [])),
        "claim_boundary_safe": readiness == "blocked_environment_recovery_runbook",
    }


def failure_atlas_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "atlas_found": False,
            "claim_readiness": "missing",
            "failure_mode_count": 0,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    release_gate = data.get("release_gate", {})
    return {
        "atlas_found": True,
        "claim_readiness": readiness,
        "failure_mode_count": len(data.get("failure_modes", [])),
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "claim_boundary_safe": readiness == "limitations_ready_failure_mode_atlas"
        and release_gate.get("formal_release_allowed") is False,
    }


def candidate_sweep_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "candidate_sweep_plan_found": False,
            "candidate_sweep_plan_generated": False,
            "claim_readiness": "missing",
            "candidate_count": 0,
            "executable_now_count": 0,
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "candidate_sweep_plan_found": True,
        "candidate_sweep_plan_generated": data.get("candidate_sweep_plan_generated"),
        "claim_readiness": readiness,
        "candidate_count": data.get("candidate_count"),
        "executable_now_count": data.get("executable_now_count"),
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_boundary_safe": data.get("candidate_sweep_plan_generated") is True
        and readiness == "paper_ready_followup_plan; blocked formal accuracy release"
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False,
    }


def zcenter_rerun_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "rerun_found": False,
            "status": "missing",
            "claim_readiness": "missing",
            "log_completed_48000": False,
            "csv_sha256_equal": False,
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "rerun_found": True,
        "status": data.get("status"),
        "claim_readiness": readiness,
        "log_completed_48000": data.get("log_completed_48000"),
        "csv_sha256_equal": data.get("csv_sha256_equal"),
        "rerun_metrics": data.get("rerun_metrics", {}),
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_boundary_safe": data.get("status") == "passed_reproduced_failed_metric"
        and readiness == "paper_ready_reproducibility; blocked formal accuracy release"
        and data.get("log_completed_48000") is True
        and data.get("csv_sha256_equal") is True
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False,
    }


def c002_longer_mean_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "c002_found": False,
            "status": "missing",
            "claim_readiness": "missing",
            "log_completed_96000": False,
            "pass_condition_met": None,
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "c002_found": True,
        "status": data.get("status"),
        "claim_readiness": readiness,
        "log_completed_96000": data.get("log_completed_96000"),
        "probe_count_ok": data.get("probe_count_ok"),
        "pass_condition_met": data.get("pass_condition_met"),
        "candidate_metrics": data.get("candidate_metrics", {}),
        "metric_delta_vs_baseline": data.get("metric_delta_vs_baseline", {}),
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_boundary_safe": data.get("status") in {"completed_no_improvement", "completed_improved_but_gate_blocked"}
        and readiness == "limitations_ready_candidate_result; blocked formal accuracy release"
        and data.get("log_completed_96000") is True
        and data.get("probe_count_ok") is True
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False,
    }


def c003_zorigin_ablation_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "c003_found": False,
            "status": "missing",
            "claim_readiness": "missing",
            "log_completed_48000": False,
            "pass_condition_met": None,
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "c003_found": True,
        "status": data.get("status"),
        "claim_readiness": readiness,
        "log_completed_48000": data.get("log_completed_48000"),
        "probe_count_ok": data.get("probe_count_ok"),
        "pass_condition_met": data.get("pass_condition_met"),
        "consistent_with_preexisting_no_zcenter": data.get("consistent_with_preexisting_no_zcenter"),
        "candidate_metrics": data.get("candidate_metrics", {}),
        "metric_delta_vs_zcenter_baseline": data.get("metric_delta_vs_zcenter_baseline", {}),
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_boundary_safe": data.get("status") in {"completed_ablation_supports_zorigin_sensitivity", "completed_ablation_inconclusive"}
        and readiness == "limitations_ready_zorigin_ablation; blocked formal accuracy release"
        and data.get("log_completed_48000") is True
        and data.get("probe_count_ok") is True
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False,
    }


def c004_dx3_low_cost_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "c004_found": False,
            "status": "missing",
            "claim_readiness": "missing",
            "log_completed_48000": False,
            "pass_condition_met": None,
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "c004_found": True,
        "status": data.get("status"),
        "claim_readiness": readiness,
        "log_completed_48000": data.get("log_completed_48000"),
        "probe_count_ok": data.get("probe_count_ok"),
        "manifest_protocol_ok": data.get("manifest_protocol_ok"),
        "pass_condition_met": data.get("pass_condition_met"),
        "pearson_positive": data.get("pearson_positive"),
        "candidate_metrics": data.get("candidate_metrics", {}),
        "metric_delta_vs_zcenter_baseline": data.get("metric_delta_vs_zcenter_baseline", {}),
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "claim_boundary_safe": data.get("status") in {"completed_low_cost_positive_correlation", "completed_low_cost_regression_warning"}
        and readiness == "limitations_ready_dx3_low_cost_regression; blocked formal accuracy release"
        and data.get("log_completed_48000") is True
        and data.get("probe_count_ok") is True
        and data.get("manifest_protocol_ok") is True
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False,
    }


def default_policy_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "default_policy_gate_found": False,
            "default_policy_gate_passed": False,
            "claim_readiness": "missing",
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "default_policy_gate_found": True,
        "default_policy_gate_passed": data.get("default_policy_gate_passed"),
        "claim_readiness": readiness,
        "formal_release_allowed": data.get("formal_release_allowed"),
        "check_count": len(data.get("checks", [])),
        "claim_boundary_safe": data.get("default_policy_gate_passed") is True
        and readiness == "paper_ready_default_policy_boundary"
        and data.get("formal_release_allowed") is False,
    }


def paper_results_packet_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "paper_results_packet_found": False,
            "paper_results_packet_passed": False,
            "claim_boundary_safe": False,
            "result_count": 0,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    rows = data.get("rows", [])
    result_ids = {str(row.get("result_id", "")) for row in rows}
    return {
        "paper_results_packet_found": True,
        "paper_results_packet_passed": summary.get("paper_results_packet_passed"),
        "result_count": summary.get("result_count", len(rows)),
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "formal_v0_4_0_allowed": summary.get("formal_v0_4_0_allowed"),
        "required_result_rows_present": {
            "casea_smoke_regression_guard": "casea_smoke_regression_guard" in result_ids,
            "official_z2m_negative_validation": "official_z2m_negative_validation" in result_ids,
            "module_claim_L1": "module_claim_L1" in result_ids,
            "formal_release_block": "formal_release_block" in result_ids,
        },
        "claim_boundary_safe": summary.get("paper_results_packet_passed") is True
        and summary.get("formal_accuracy_claim_supported") is False
        and summary.get("formal_v0_4_0_allowed") is False,
    }


def software_feedback_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "software_feedback_matrix_found": False,
            "software_feedback_matrix_passed": False,
            "claim_boundary_safe": False,
            "feedback_count": 0,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    return {
        "software_feedback_matrix_found": True,
        "software_feedback_matrix_passed": summary.get("software_feedback_matrix_passed"),
        "feedback_count": summary.get("feedback_count"),
        "all_source_paths_exist": summary.get("all_source_paths_exist"),
        "no_forbidden_default_promotion": summary.get("no_forbidden_default_promotion"),
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "formal_v0_4_0_allowed": summary.get("formal_v0_4_0_allowed"),
        "claim_boundary_safe": summary.get("software_feedback_matrix_passed") is True
        and summary.get("no_forbidden_default_promotion") is True
        and summary.get("formal_accuracy_claim_supported") is False
        and summary.get("formal_v0_4_0_allowed") is False,
    }


def claim_support_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "claim_support_gate_found": False,
            "claim_support_gate_passed": False,
            "claim_boundary_safe": False,
            "claim_count": 0,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    return {
        "claim_support_gate_found": True,
        "claim_support_gate_passed": summary.get("claim_support_gate_passed"),
        "claim_count": summary.get("claim_count"),
        "all_source_paths_exist": summary.get("all_source_paths_exist"),
        "no_formal_accuracy_claims": summary.get("no_formal_accuracy_claims"),
        "forbidden_success_patterns_blocked": summary.get("forbidden_success_patterns_blocked"),
        "formal_release_allowed": summary.get("formal_release_allowed"),
        "claim_readiness": summary.get("claim_readiness"),
        "claim_boundary_safe": summary.get("claim_support_gate_passed") is True
        and summary.get("no_formal_accuracy_claims") is True
        and summary.get("forbidden_success_patterns_blocked") is True
        and summary.get("formal_release_allowed") is False,
    }


def manifest_output_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "manifest_output_gate_found": False,
            "manifest_output_gate_passed": False,
            "claim_readiness": "missing",
            "formal_accuracy_claim_supported": None,
            "check_count": 0,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "manifest_output_gate_found": True,
        "manifest_output_gate_passed": data.get("manifest_output_gate_passed"),
        "claim_readiness": readiness,
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "check_count": len(data.get("checks", [])),
        "claim_boundary_safe": data.get("manifest_output_gate_passed") is True
        and readiness == "paper_ready_manifest_traceability"
        and data.get("formal_accuracy_claim_supported") is False,
    }


def manifest_schema_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "manifest_schema_gate_found": False,
            "manifest_schema_gate_passed": False,
            "claim_readiness": "missing",
            "formal_accuracy_claim_supported": None,
            "contract_version": "",
            "check_count": 0,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    return {
        "manifest_schema_gate_found": True,
        "manifest_schema_gate_passed": data.get("manifest_schema_gate_passed"),
        "claim_readiness": readiness,
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "contract_version": data.get("manifest_contract_version"),
        "check_count": len(data.get("checks", [])),
        "claim_boundary_safe": data.get("manifest_schema_gate_passed") is True
        and readiness == "paper_ready_manifest_schema_boundary"
        and data.get("formal_accuracy_claim_supported") is False,
    }


def manuscript_results_table_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "manuscript_results_table_found": False,
            "manuscript_results_table_passed": False,
            "claim_readiness": "missing",
            "row_count": 0,
            "diagnostic_rows_not_formal": False,
            "formal_r2_negative": False,
            "formal_accuracy_claim_supported": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    rows = data.get("rows", [])
    row_ids = {str(row.get("row_id", "")) for row in rows}
    diagnostic_safe = all(
        row.get("claim_boundary") != "formal_gate_input"
        for row in rows
        if row.get("result_role") == "diagnostic_only"
    )
    formal = next((row for row in rows if row.get("row_id") == "formal_official_z2m"), {})
    formal_r2_negative = False
    try:
        formal_r2_negative = float(formal.get("r2", "nan")) < 0.0
    except ValueError:
        formal_r2_negative = False
    return {
        "manuscript_results_table_found": True,
        "manuscript_results_table_passed": summary.get("manuscript_results_table_passed"),
        "claim_readiness": summary.get("claim_readiness"),
        "row_count": summary.get("row_count", len(rows)),
        "required_rows_present": {
            "formal_official_z2m": "formal_official_z2m" in row_ids,
            "best_diagnostic_sampling": "best_diagnostic_sampling" in row_ids,
            "near_wall_risk_gradient": "near_wall_risk_gradient" in row_ids,
            "release_boundary_status": "release_boundary_status" in row_ids,
        },
        "diagnostic_rows_not_formal": diagnostic_safe,
        "formal_r2_negative": formal_r2_negative,
        "formal_accuracy_claim_supported": summary.get("formal_accuracy_claim_supported"),
        "claim_boundary_safe": summary.get("manuscript_results_table_passed") is True
        and summary.get("claim_readiness") == "paper_ready_manuscript_results_table"
        and diagnostic_safe
        and formal_r2_negative
        and summary.get("formal_accuracy_claim_supported") is False,
    }


def manuscript_section_pack_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "manuscript_section_pack_found": False,
            "section_pack_passed": False,
            "claim_readiness": "missing",
            "formal_accuracy_claim_supported": None,
            "formal_release_allowed": None,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    checks = data.get("checks") or {}
    return {
        "manuscript_section_pack_found": True,
        "section_pack_passed": data.get("section_pack_passed"),
        "claim_readiness": readiness,
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "formal_release_allowed": data.get("formal_release_allowed"),
        "recommended_tag": data.get("recommended_tag"),
        "check_count": len(checks),
        "claim_boundary_safe": data.get("section_pack_passed") is True
        and readiness == "paper_ready_negative_validation_and_limitations"
        and data.get("formal_accuracy_claim_supported") is False
        and data.get("formal_release_allowed") is False
        and checks.get("forbidden_success_wording_absent") is True
        and checks.get("evidence_notes_present") is True,
    }


def paper_results_figure_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "paper_results_figure_found": False,
            "figure_gate_passed": False,
            "claim_readiness": "missing",
            "formal_accuracy_claim_supported": None,
            "export_bundle_complete": False,
            "claim_boundary_safe": False,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    readiness = str(data.get("claim_readiness", ""))
    bundle = (data.get("figure_contract") or {}).get("export_bundle") or {}
    required_bundle_keys = ["script", "source_csv", "svg", "png", "qa"]
    missing_bundle_paths = [
        str(bundle.get(key, ""))
        for key in required_bundle_keys
        if not bundle.get(key) or not (ROOT / str(bundle.get(key))).exists()
    ]
    return {
        "paper_results_figure_found": True,
        "figure_gate_passed": data.get("figure_gate_passed"),
        "claim_readiness": readiness,
        "formal_accuracy_claim_supported": data.get("formal_accuracy_claim_supported"),
        "export_bundle_complete": not missing_bundle_paths,
        "missing_bundle_paths": missing_bundle_paths,
        "claim_boundary_safe": data.get("figure_gate_passed") is True
        and readiness == "paper_ready_figure_for_negative_validation_and_limitations"
        and data.get("formal_accuracy_claim_supported") is False
        and not missing_bundle_paths,
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metric = payload["metric_gate"]
    claim = payload["claim_matrix"]
    draft = payload["draft_scan"]
    artifact = payload["artifact_index"]
    rhino = payload["rhino_gha_load_gate"]
    build_chain = payload["build_chain_manifest"]
    preflight = payload["casee_official_run_preflight"]
    dx1 = payload["casee_dx1_readiness_audit"]
    recovery = payload["casee_environment_recovery_runbook"]
    atlas = payload["casee_failure_mode_atlas"]
    zcenter_rerun = payload["casee_zcenter_rerun_consistency"]
    c002 = payload["casee_c002_longer_mean_audit"]
    c003 = payload["casee_c003_zorigin_ablation_audit"]
    c004 = payload["casee_c004_dx3_low_cost_audit"]
    candidate_sweep = payload["casee_candidate_sweep_plan"]
    default_policy = payload["casee_default_policy_gate"]
    paper_packet = payload["citylbm_paper_results_packet"]
    manifest_output = payload["citylbm_manifest_output_gate"]
    manifest_schema = payload["citylbm_manifest_schema_gate"]
    manuscript_table = payload["casee_manuscript_results_table"]
    section_pack = payload["casee_manuscript_section_pack"]
    paper_figure = payload["casee_paper_results_figure"]
    software_feedback = payload["citylbm_software_feedback_matrix"]
    claim_support = payload["casee_claim_support_gate"]
    lines = [
        "# Case E Paper Evidence Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Paper evidence gate passed: {payload['paper_evidence_gate_passed']}",
        f"- Formal v0.4.0 release allowed: {metric['formal_release_allowed']}",
        f"- Recommended tag: `{metric['recommended_tag']}`",
        "",
        "## Official z=2 m Metric",
        "",
        f"- MAE: {metric['official_z2m_mae_pp']} pp",
        f"- R2: {metric['official_z2m_r2']}",
        f"- Pearson: {metric['official_z2m_pearson']}",
        f"- Negative validation status: {metric['formal_metric_is_negative_validation']}",
        "",
        "## Claim Matrix",
        "",
        f"- Claims: {claim['claim_count']}",
        f"- Readiness counts: `{claim['readiness_counts']}`",
        f"- Blocked release claim present: {claim['blocked_release_claim_present']}",
        f"- Negative validation claim present: {claim['negative_validation_claim_present']}",
        f"- Recommended tag present: {claim['recommended_tag_present']}",
        f"- No overstated paper-ready claims: {claim['no_overstated_paper_ready_claims']}",
        "",
        "## Draft Scan",
        "",
        f"- Checked files: {len(draft['checked_files'])}",
        f"- Checked nonblank lines: {draft['checked_nonblank_lines']}",
        f"- Draft claim boundary passed: {draft['draft_claim_boundary_passed']}",
        "",
        "## Artifact Index",
        "",
        f"- Artifact index found: {artifact['artifact_index_found']}",
        f"- Artifact count: {artifact['artifact_count']}",
        f"- Lightweight release assets: {artifact['lightweight_release_asset_count']}",
        f"- Required artifacts present: {artifact['required_artifacts_present']}",
        f"- Formal accuracy claim supported by index: {artifact['formal_accuracy_claim_supported']}",
        "",
        "## Rhino/GHA Load Gate",
        "",
        f"- Gate found: {rhino['rhino_gate_found']}",
        f"- Rhino loaded new GHA: {rhino['rhino_loaded_new_gha']}",
        f"- Claim readiness: `{rhino['claim_readiness']}`",
        f"- Claim boundary safe: {rhino['claim_boundary_safe']}",
        "",
        "## Build Chain Manifest",
        "",
        f"- Manifest found: {build_chain['build_chain_found']}",
        f"- Build chain ready: {build_chain['build_chain_ready']}",
        f"- Claim readiness: `{build_chain['claim_readiness']}`",
        f"- VS Build Tools C++: `{build_chain['vs_cpp_status']}`",
        f"- MinGW/g++ fallback: `{build_chain['gpp_status']}`",
        f"- Native source compile ready: {build_chain['native_source_compile_ready']}",
        f"- Native source compile path: `{build_chain['native_source_compile_path']}`",
        f"- .NET SDK: `{build_chain['dotnet_status']}`",
        f"- FluidX3D: `{build_chain['fluidx3d_status']}`",
        f"- GPU runtime: `{build_chain['gpu_status']}`",
        f"- UAC/1602 blocker recorded: {build_chain['uac_blocker_recorded']}",
        f"- Claim boundary safe: {build_chain['claim_boundary_safe']}",
        "",
        "## Official Run Preflight",
        "",
        f"- Preflight found: {preflight['preflight_found']}",
        f"- Official follow-up run allowed: {preflight['official_followup_run_allowed']}",
        f"- Formal release allowed: {preflight['formal_release_allowed']}",
        f"- Claim readiness: `{preflight['claim_readiness']}`",
        f"- Claim boundary safe: {preflight['claim_boundary_safe']}",
        "",
        "## dx=1 Readiness Audit",
        "",
        f"- Audit found: {dx1['dx1_readiness_found']}",
        f"- Audit passed: {dx1['dx1_readiness_audit_passed']}",
        f"- dx=1 readiness: `{dx1['dx1_readiness']}`",
        f"- Memory headroom ok: {dx1.get('dx1_memory_headroom_ok')}",
        f"- Run started: {dx1['run_started']}",
        f"- Formal accuracy claim supported: {dx1['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {dx1['claim_boundary_safe']}",
        "",
        "## Environment Recovery Runbook",
        "",
        f"- Recovery runbook found: {recovery['recovery_found']}",
        f"- Formal release allowed: {recovery['formal_release_allowed']}",
        f"- Claim readiness: `{recovery['claim_readiness']}`",
        f"- Recovery steps: {recovery['step_count']}",
        f"- Claim boundary safe: {recovery['claim_boundary_safe']}",
        "",
        "## Failure-Mode Atlas",
        "",
        f"- Atlas found: {atlas['atlas_found']}",
        f"- Failure modes: {atlas['failure_mode_count']}",
        f"- Claim readiness: `{atlas['claim_readiness']}`",
        f"- Claim boundary safe: {atlas['claim_boundary_safe']}",
        "",
        "## z-center Rerun Consistency",
        "",
        f"- Rerun found: {zcenter_rerun['rerun_found']}",
        f"- Status: `{zcenter_rerun['status']}`",
        f"- 48000-step log complete: {zcenter_rerun['log_completed_48000']}",
        f"- CSV SHA256 equal: {zcenter_rerun['csv_sha256_equal']}",
        f"- R2: {zcenter_rerun.get('rerun_metrics', {}).get('r2')}",
        f"- Claim readiness: `{zcenter_rerun['claim_readiness']}`",
        f"- Claim boundary safe: {zcenter_rerun['claim_boundary_safe']}",
        "",
        "## C002 Longer Time-Mean Audit",
        "",
        f"- Audit found: {c002['c002_found']}",
        f"- Status: `{c002['status']}`",
        f"- 96000-step log complete: {c002['log_completed_96000']}",
        f"- Pass condition met: {c002['pass_condition_met']}",
        f"- R2: {c002.get('candidate_metrics', {}).get('r2')}",
        f"- R2 delta vs baseline: {c002.get('metric_delta_vs_baseline', {}).get('r2')}",
        f"- Claim readiness: `{c002['claim_readiness']}`",
        f"- Claim boundary safe: {c002['claim_boundary_safe']}",
        "",
        "## C003 Z-Origin Ablation Audit",
        "",
        f"- Audit found: {c003['c003_found']}",
        f"- Status: `{c003['status']}`",
        f"- 48000-step log complete: {c003['log_completed_48000']}",
        f"- Pass condition met: {c003['pass_condition_met']}",
        f"- Consistent with preexisting no-zcenter artifact: {c003['consistent_with_preexisting_no_zcenter']}",
        f"- R2: {c003.get('candidate_metrics', {}).get('r2')}",
        f"- R2 delta vs z-center baseline: {c003.get('metric_delta_vs_zcenter_baseline', {}).get('r2')}",
        f"- Claim readiness: `{c003['claim_readiness']}`",
        f"- Claim boundary safe: {c003['claim_boundary_safe']}",
        "",
        "## C004 dx=3 Low-Cost Direction Check",
        "",
        f"- Audit found: {c004['c004_found']}",
        f"- Status: `{c004['status']}`",
        f"- 48000-step log complete: {c004['log_completed_48000']}",
        f"- Manifest protocol ok: {c004['manifest_protocol_ok']}",
        f"- Pearson positive: {c004['pearson_positive']}",
        f"- Pass condition met: {c004['pass_condition_met']}",
        f"- R2: {c004.get('candidate_metrics', {}).get('r2')}",
        f"- R2 delta vs z-center baseline: {c004.get('metric_delta_vs_zcenter_baseline', {}).get('r2')}",
        f"- Claim readiness: `{c004['claim_readiness']}`",
        f"- Claim boundary safe: {c004['claim_boundary_safe']}",
        "",
        "## Candidate Sweep Plan",
        "",
        f"- Plan found: {candidate_sweep['candidate_sweep_plan_found']}",
        f"- Plan generated: {candidate_sweep['candidate_sweep_plan_generated']}",
        f"- Candidate count: {candidate_sweep['candidate_count']}",
        f"- Executable-now count: {candidate_sweep['executable_now_count']}",
        f"- Claim readiness: `{candidate_sweep['claim_readiness']}`",
        f"- Formal accuracy claim supported: {candidate_sweep['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {candidate_sweep['claim_boundary_safe']}",
        "",
        "## Default Policy Gate",
        "",
        f"- Gate found: {default_policy['default_policy_gate_found']}",
        f"- Default policy gate passed: {default_policy['default_policy_gate_passed']}",
        f"- Checks: {default_policy['check_count']}",
        f"- Claim readiness: `{default_policy['claim_readiness']}`",
        f"- Claim boundary safe: {default_policy['claim_boundary_safe']}",
        "",
        "## Cross-Experiment Paper Results Packet",
        "",
        f"- Packet found: {paper_packet['paper_results_packet_found']}",
        f"- Packet passed: {paper_packet['paper_results_packet_passed']}",
        f"- Result rows: {paper_packet['result_count']}",
        f"- Formal accuracy claim supported: {paper_packet['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {paper_packet['formal_v0_4_0_allowed']}",
        f"- Claim boundary safe: {paper_packet['claim_boundary_safe']}",
        "",
        "## Manifest Output Gate",
        "",
        f"- Gate found: {manifest_output['manifest_output_gate_found']}",
        f"- Gate passed: {manifest_output['manifest_output_gate_passed']}",
        f"- Checks: {manifest_output['check_count']}",
        f"- Claim readiness: `{manifest_output['claim_readiness']}`",
        f"- Formal accuracy claim supported: {manifest_output['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {manifest_output['claim_boundary_safe']}",
        "",
        "## Manifest Schema Gate",
        "",
        f"- Gate found: {manifest_schema['manifest_schema_gate_found']}",
        f"- Gate passed: {manifest_schema['manifest_schema_gate_passed']}",
        f"- Contract version: `{manifest_schema['contract_version']}`",
        f"- Checks: {manifest_schema['check_count']}",
        f"- Claim readiness: `{manifest_schema['claim_readiness']}`",
        f"- Formal accuracy claim supported: {manifest_schema['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {manifest_schema['claim_boundary_safe']}",
        "",
        "## Manuscript Results Table",
        "",
        f"- Table found: {manuscript_table['manuscript_results_table_found']}",
        f"- Table passed: {manuscript_table['manuscript_results_table_passed']}",
        f"- Rows: {manuscript_table['row_count']}",
        f"- Claim readiness: `{manuscript_table['claim_readiness']}`",
        f"- Diagnostic rows not formal: {manuscript_table['diagnostic_rows_not_formal']}",
        f"- Formal R2 negative: {manuscript_table['formal_r2_negative']}",
        f"- Formal accuracy claim supported: {manuscript_table['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {manuscript_table['claim_boundary_safe']}",
        "",
        "## Manuscript Section Pack",
        "",
        f"- Pack found: {section_pack['manuscript_section_pack_found']}",
        f"- Pack passed: {section_pack['section_pack_passed']}",
        f"- Checks: {section_pack['check_count']}",
        f"- Claim readiness: `{section_pack['claim_readiness']}`",
        f"- Formal release allowed: {section_pack['formal_release_allowed']}",
        f"- Formal accuracy claim supported: {section_pack['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {section_pack['claim_boundary_safe']}",
        "",
        "## Paper Results Figure",
        "",
        f"- Figure found: {paper_figure['paper_results_figure_found']}",
        f"- Figure gate passed: {paper_figure['figure_gate_passed']}",
        f"- Claim readiness: `{paper_figure['claim_readiness']}`",
        f"- Export bundle complete: {paper_figure['export_bundle_complete']}",
        f"- Formal accuracy claim supported: {paper_figure['formal_accuracy_claim_supported']}",
        f"- Claim boundary safe: {paper_figure['claim_boundary_safe']}",
        "",
        "## Software Feedback Matrix",
        "",
        f"- Matrix found: {software_feedback['software_feedback_matrix_found']}",
        f"- Matrix passed: {software_feedback['software_feedback_matrix_passed']}",
        f"- Feedback rows: {software_feedback['feedback_count']}",
        f"- All source paths exist: {software_feedback['all_source_paths_exist']}",
        f"- No forbidden default promotion: {software_feedback['no_forbidden_default_promotion']}",
        f"- Formal accuracy claim supported: {software_feedback['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {software_feedback['formal_v0_4_0_allowed']}",
        f"- Claim boundary safe: {software_feedback['claim_boundary_safe']}",
        "",
        "## Claim Support Gate",
        "",
        f"- Gate found: {claim_support['claim_support_gate_found']}",
        f"- Gate passed: {claim_support['claim_support_gate_passed']}",
        f"- Claims checked: {claim_support['claim_count']}",
        f"- No formal accuracy claims: {claim_support['no_formal_accuracy_claims']}",
        f"- Forbidden success patterns blocked: {claim_support['forbidden_success_patterns_blocked']}",
        f"- Claim readiness: `{claim_support['claim_readiness']}`",
        f"- Claim boundary safe: {claim_support['claim_boundary_safe']}",
    ]
    if artifact["missing_required_artifacts"]:
        lines += ["", "Missing required artifacts:"]
        for item in artifact["missing_required_artifacts"]:
            lines.append(f"- `{item}`")
    if draft["forbidden_success_claim_violations"]:
        lines += ["", "## Violations", ""]
        for item in draft["forbidden_success_claim_violations"]:
            lines.append(f"- `{item['path']}:{item['line']}` matched `{item['pattern']}`: {item['text']}")
    else:
        lines += ["", "No forbidden success-claim violations were found outside negated or forbidden-claim sections."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--claim-matrix", type=Path, default=RESULTS_DIR / "casee_manuscript_claim_matrix.csv")
    parser.add_argument("--artifact-index", type=Path, default=RESULTS_DIR / "casee_artifact_index.json")
    parser.add_argument("--rhino-gate", type=Path, default=RESULTS_DIR / "rhino_gha_load_gate.json")
    parser.add_argument("--build-chain", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    parser.add_argument("--preflight", type=Path, default=RESULTS_DIR / "casee_official_run_preflight.json")
    parser.add_argument("--dx1-readiness", type=Path, default=RESULTS_DIR / "casee_dx1_readiness_audit.json")
    parser.add_argument("--recovery", type=Path, default=RESULTS_DIR / "casee_environment_recovery_runbook.json")
    parser.add_argument("--failure-atlas", type=Path, default=RESULTS_DIR / "casee_failure_mode_atlas.json")
    parser.add_argument("--zcenter-rerun", type=Path, default=RESULTS_DIR / "casee_zcenter_rerun_consistency.json")
    parser.add_argument("--c002-longer-mean", type=Path, default=RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    parser.add_argument("--c003-zorigin-ablation", type=Path, default=RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    parser.add_argument("--c004-dx3-low-cost", type=Path, default=RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    parser.add_argument("--candidate-sweep", type=Path, default=RESULTS_DIR / "casee_candidate_sweep_plan.json")
    parser.add_argument("--default-policy", type=Path, default=RESULTS_DIR / "casee_default_policy_gate.json")
    parser.add_argument("--paper-results-packet", type=Path, default=RESULTS_DIR / "citylbm_paper_results_packet.json")
    parser.add_argument("--manifest-output", type=Path, default=RESULTS_DIR / "citylbm_manifest_output_gate.json")
    parser.add_argument("--manifest-schema", type=Path, default=RESULTS_DIR / "citylbm_manifest_schema_gate.json")
    parser.add_argument("--manuscript-results-table", type=Path, default=RESULTS_DIR / "casee_manuscript_results_table.json")
    parser.add_argument("--manuscript-section-pack", type=Path, default=RESULTS_DIR / "casee_manuscript_section_pack.json")
    parser.add_argument("--paper-results-figure", type=Path, default=RESULTS_DIR / "casee_paper_results_figure_qa.json")
    parser.add_argument("--software-feedback", type=Path, default=RESULTS_DIR / "citylbm_software_feedback_matrix.json")
    parser.add_argument("--claim-support", type=Path, default=RESULTS_DIR / "casee_claim_support_gate.json")
    parser.add_argument("--draft-glob", default="casee_v04_*.md")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_paper_evidence_gate.json")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_paper_evidence_gate.md")
    args = parser.parse_args()

    gate = json.loads(args.release_gate.read_text(encoding="utf-8"))
    metric = metric_gate_status(gate)
    claim = claim_matrix_status(read_csv(args.claim_matrix), str(metric["recommended_tag"]))
    draft = draft_status(sorted(PAPER_DRAFTS_DIR.glob(args.draft_glob)))
    artifact = artifact_index_status(args.artifact_index)
    rhino = rhino_gate_status(args.rhino_gate)
    build_chain = build_chain_status(args.build_chain)
    preflight = preflight_status(args.preflight)
    dx1_readiness = dx1_readiness_status(args.dx1_readiness)
    recovery = recovery_status(args.recovery)
    atlas = failure_atlas_status(args.failure_atlas)
    zcenter_rerun = zcenter_rerun_status(args.zcenter_rerun)
    c002_longer_mean = c002_longer_mean_status(args.c002_longer_mean)
    c003_zorigin_ablation = c003_zorigin_ablation_status(args.c003_zorigin_ablation)
    c004_dx3_low_cost = c004_dx3_low_cost_status(args.c004_dx3_low_cost)
    candidate_sweep = candidate_sweep_status(args.candidate_sweep)
    default_policy = default_policy_status(args.default_policy)
    paper_packet = paper_results_packet_status(args.paper_results_packet)
    manifest_output = manifest_output_status(args.manifest_output)
    manifest_schema = manifest_schema_status(args.manifest_schema)
    manuscript_table = manuscript_results_table_status(args.manuscript_results_table)
    section_pack = manuscript_section_pack_status(args.manuscript_section_pack)
    paper_figure = paper_results_figure_status(args.paper_results_figure)
    software_feedback = software_feedback_status(args.software_feedback)
    claim_support = claim_support_status(args.claim_support)
    passed = (
        metric["formal_metric_is_negative_validation"]
        and claim["blocked_release_claim_present"]
        and claim["negative_validation_claim_present"]
        and claim["recommended_tag_present"]
        and claim["no_overstated_paper_ready_claims"]
        and draft["draft_claim_boundary_passed"]
        and artifact["artifact_index_found"]
        and artifact["required_artifacts_present"]
        and artifact["formal_accuracy_claim_supported"] is False
        and rhino["rhino_gate_found"]
        and rhino["claim_boundary_safe"]
        and build_chain["build_chain_found"]
        and build_chain["claim_boundary_safe"]
        and preflight["preflight_found"]
        and preflight["claim_boundary_safe"]
        and preflight["formal_release_allowed"] is False
        and dx1_readiness["dx1_readiness_found"]
        and dx1_readiness["claim_boundary_safe"]
        and recovery["recovery_found"]
        and recovery["claim_boundary_safe"]
        and recovery["formal_release_allowed"] is False
        and atlas["atlas_found"]
        and atlas["claim_boundary_safe"]
        and zcenter_rerun["rerun_found"]
        and zcenter_rerun["claim_boundary_safe"]
        and c002_longer_mean["c002_found"]
        and c002_longer_mean["claim_boundary_safe"]
        and c003_zorigin_ablation["c003_found"]
        and c003_zorigin_ablation["claim_boundary_safe"]
        and c004_dx3_low_cost["c004_found"]
        and c004_dx3_low_cost["claim_boundary_safe"]
        and candidate_sweep["candidate_sweep_plan_found"]
        and candidate_sweep["claim_boundary_safe"]
        and default_policy["default_policy_gate_found"]
        and default_policy["claim_boundary_safe"]
        and paper_packet["paper_results_packet_found"]
        and paper_packet["claim_boundary_safe"]
        and manifest_output["manifest_output_gate_found"]
        and manifest_output["claim_boundary_safe"]
        and manifest_schema["manifest_schema_gate_found"]
        and manifest_schema["claim_boundary_safe"]
        and manuscript_table["manuscript_results_table_found"]
        and manuscript_table["claim_boundary_safe"]
        and section_pack["manuscript_section_pack_found"]
        and section_pack["claim_boundary_safe"]
        and paper_figure["paper_results_figure_found"]
        and paper_figure["claim_boundary_safe"]
        and software_feedback["software_feedback_matrix_found"]
        and software_feedback["claim_boundary_safe"]
        and claim_support["claim_support_gate_found"]
        and claim_support["claim_boundary_safe"]
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_evidence_gate_passed": passed,
        "metric_gate": metric,
        "claim_matrix": claim,
        "draft_scan": draft,
        "artifact_index": artifact,
        "rhino_gha_load_gate": rhino,
        "build_chain_manifest": build_chain,
        "casee_official_run_preflight": preflight,
        "casee_dx1_readiness_audit": dx1_readiness,
        "casee_environment_recovery_runbook": recovery,
        "casee_failure_mode_atlas": atlas,
        "casee_zcenter_rerun_consistency": zcenter_rerun,
        "casee_c002_longer_mean_audit": c002_longer_mean,
        "casee_c003_zorigin_ablation_audit": c003_zorigin_ablation,
        "casee_c004_dx3_low_cost_audit": c004_dx3_low_cost,
        "casee_candidate_sweep_plan": candidate_sweep,
        "casee_default_policy_gate": default_policy,
        "citylbm_paper_results_packet": paper_packet,
        "citylbm_manifest_output_gate": manifest_output,
        "citylbm_manifest_schema_gate": manifest_schema,
        "casee_manuscript_results_table": manuscript_table,
        "casee_manuscript_section_pack": section_pack,
        "casee_paper_results_figure": paper_figure,
        "citylbm_software_feedback_matrix": software_feedback,
        "casee_claim_support_gate": claim_support,
    }
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"paper_evidence_gate_passed": passed, "out_json": str(args.out_json)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
