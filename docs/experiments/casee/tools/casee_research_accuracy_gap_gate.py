#!/usr/bin/env python3
"""Quantify the Case E gap to the current paper/release accuracy threshold."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
C014_AUDIT = RESULTS_DIR / "casee_c014_residual_structure_audit.json"
MANUSCRIPT_TABLE = RESULTS_DIR / "casee_manuscript_results_table.csv"
DEFAULT_PROMOTION_GATE = RESULTS_DIR / "casee_default_promotion_gate.json"
RHINO_LOAD_GATE = RESULTS_DIR / "rhino_gha_load_gate.json"
PREFLIGHT = RESULTS_DIR / "casee_official_run_preflight.json"
OUT_JSON = RESULTS_DIR / "casee_research_accuracy_gap_gate.json"
OUT_CSV = RESULTS_DIR / "casee_research_accuracy_gap_gate.csv"
OUT_MD = RESULTS_DIR / "casee_research_accuracy_gap_gate.md"

THRESHOLDS = {
    "n": 80,
    "height_m": 2.0,
    "sampling_mode": "raw_trilinear",
    "mae_pp_max_exclusive": 15.0,
    "r2_min_exclusive": 0.0,
    "pearson_min_exclusive": 0.0,
}


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


def as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_passes(metrics: Dict[str, Any], *, formal_protocol_required: bool) -> Dict[str, Any]:
    n = int(as_float(metrics.get("n")) or 0)
    height = as_float(metrics.get("height_m"))
    sampling = str(metrics.get("sampling_mode") or "")
    mae = as_float(metrics.get("mae_pp"))
    r2 = as_float(metrics.get("r2"))
    pearson = as_float(metrics.get("pearson"))
    protocol_ok = (
        n == THRESHOLDS["n"]
        and height == THRESHOLDS["height_m"]
        and (sampling == THRESHOLDS["sampling_mode"] or not formal_protocol_required)
    )
    return {
        "protocol_ok": protocol_ok,
        "n_ok": n == THRESHOLDS["n"],
        "height_ok": height == THRESHOLDS["height_m"] if height is not None else not formal_protocol_required,
        "sampling_ok": sampling == THRESHOLDS["sampling_mode"] if sampling else not formal_protocol_required,
        "mae_gate_passed": mae is not None and mae < THRESHOLDS["mae_pp_max_exclusive"],
        "r2_gate_passed": r2 is not None and r2 > THRESHOLDS["r2_min_exclusive"],
        "pearson_gate_passed": pearson is not None and pearson > THRESHOLDS["pearson_min_exclusive"],
        "mae_gap_to_threshold_pp": None if mae is None else max(0.0, mae - THRESHOLDS["mae_pp_max_exclusive"]),
        "r2_gap_to_positive": None if r2 is None else max(0.0, THRESHOLDS["r2_min_exclusive"] - r2),
        "pearson_gap_to_positive": None if pearson is None else max(0.0, THRESHOLDS["pearson_min_exclusive"] - pearson),
    }


def row(
    *,
    candidate_id: str,
    evidence_type: str,
    protocol_role: str,
    metrics: Dict[str, Any],
    source_paths: Iterable[Path],
    default_setting_allowed: bool,
    paper_use: str,
    limitations: str,
) -> Dict[str, Any]:
    formal_protocol_required = protocol_role == "formal_official_gate"
    gates = metric_passes(metrics, formal_protocol_required=formal_protocol_required)
    metric_ready = (
        gates["protocol_ok"]
        and gates["mae_gate_passed"]
        and gates["r2_gate_passed"]
        and gates["pearson_gate_passed"]
    )
    return {
        "candidate_id": candidate_id,
        "evidence_type": evidence_type,
        "protocol_role": protocol_role,
        "n": metrics.get("n", ""),
        "height_m": metrics.get("height_m", ""),
        "sampling_mode": metrics.get("sampling_mode", ""),
        "mae_pp": metrics.get("mae_pp", ""),
        "r2": metrics.get("r2", ""),
        "pearson": metrics.get("pearson", ""),
        "mae_gap_to_15pp": gates["mae_gap_to_threshold_pp"],
        "r2_gap_to_positive": gates["r2_gap_to_positive"],
        "pearson_gap_to_positive": gates["pearson_gap_to_positive"],
        "metric_gate_passed": metric_ready,
        "default_setting_allowed": default_setting_allowed,
        "source_paths": "; ".join(rel(path) for path in source_paths),
        "paper_use": paper_use,
        "limitations": limitations,
    }


def manuscript_row(rows: List[Dict[str, str]], row_id: str) -> Dict[str, str]:
    for item in rows:
        if item.get("row_id") == row_id:
            return item
    return {}


def build_payload() -> Dict[str, Any]:
    release_gate = read_json(RELEASE_GATE)
    c014 = read_json(C014_AUDIT)
    default_promotion = read_json(DEFAULT_PROMOTION_GATE)
    rhino = read_json(RHINO_LOAD_GATE)
    preflight = read_json(PREFLIGHT)
    manuscript_rows = read_csv(MANUSCRIPT_TABLE)

    formal_metrics = dict(release_gate.get("metrics") or {})
    c014_metrics = dict(c014.get("c014_metrics") or {})
    if c014_metrics:
        c014_metrics.setdefault("height_m", 2.0)
        c014_metrics.setdefault("sampling_mode", "raw_trilinear")
    affine_metrics = dict((c014.get("affine_upper_bound") or {}).get("metrics") or {})
    if affine_metrics:
        affine_metrics.setdefault("height_m", 2.0)
        affine_metrics.setdefault("sampling_mode", "post_hoc_affine_diagnostic")
    diagnostic_sampling = manuscript_row(manuscript_rows, "best_diagnostic_sampling")
    diagnostic_metrics = {
        "n": diagnostic_sampling.get("n", ""),
        "height_m": 2.0,
        "sampling_mode": "vertical_valid_above",
        "mae_pp": diagnostic_sampling.get("mae_pp", ""),
        "r2": diagnostic_sampling.get("r2", ""),
        "pearson": diagnostic_sampling.get("pearson", ""),
    }

    rows = [
        row(
            candidate_id="formal_official_z2m_current",
            evidence_type=str(release_gate.get("evidence_type") or "newly_run"),
            protocol_role="formal_official_gate",
            metrics=formal_metrics,
            source_paths=[RELEASE_GATE, RESULTS_DIR / "casee_metrics.csv", RESULTS_DIR / "casee_validation_report.md"],
            default_setting_allowed=False,
            paper_use="Use as the official negative validation result and primary accuracy gap.",
            limitations="Fails MAE and R2 gates; formal v0.4.0 must remain blocked.",
        )
    ]
    if c014_metrics:
        rows.append(
            row(
                candidate_id="best_diagnostic_c014_no_sgs_afk_s2p0",
                evidence_type=str(c014.get("evidence_type") or "preexisting_artifact"),
                protocol_role="diagnostic_candidate",
                metrics=c014_metrics,
                source_paths=[C014_AUDIT, RESULTS_DIR / "casee_c014_residual_structure_audit.csv"],
                default_setting_allowed=False,
                paper_use="Use as the strongest official-height diagnostic improvement direction.",
                limitations="R2 remains negative and the no-SGS/AF-k scale combination is a diagnostic sweep, not a validated default model.",
            )
        )
    if diagnostic_sampling.get("row_id"):
        rows.append(
            row(
                candidate_id="best_diagnostic_sampling_vertical_valid_above",
                evidence_type=diagnostic_sampling.get("evidence_type", "newly_run"),
                protocol_role="diagnostic_sampling_only",
                metrics=diagnostic_metrics,
                source_paths=[MANUSCRIPT_TABLE, RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv"],
                default_setting_allowed=False,
                paper_use="Use as near-wall/probe-protocol sensitivity evidence only.",
                limitations="Diagnostic sampling cannot replace official z=2 m raw_trilinear validation.",
            )
        )
    if affine_metrics:
        rows.append(
            row(
                candidate_id="post_hoc_affine_upper_bound_c014",
                evidence_type="preexisting_artifact",
                protocol_role="post_hoc_upper_bound_only",
                metrics=affine_metrics,
                source_paths=[C014_AUDIT],
                default_setting_allowed=False,
                paper_use="Use only to show that calibration would be a weak post-hoc upper bound.",
                limitations="Post-hoc affine fitting is not a predictive validation result and cannot justify default promotion.",
            )
        )

    formal = rows[0]
    formal_metric_ready = bool(formal["metric_gate_passed"])
    blockers = {
        "formal_metric_gate_passed": formal_metric_ready,
        "formal_release_allowed": release_gate.get("formal_release_allowed") is True,
        "rhino_loaded_new_gha": rhino.get("rhino_loaded_new_gha") is True,
        "diagnostic_default_promotion_allowed": default_promotion.get("any_diagnostic_default_promotion_allowed") is True,
        "official_followup_run_allowed": preflight.get("official_followup_run_allowed") is True,
    }
    gate_passed = (
        not formal_metric_ready
        and release_gate.get("formal_release_allowed") is False
        and default_promotion.get("any_diagnostic_default_promotion_allowed") is False
        and rhino.get("rhino_loaded_new_gha") is False
        and all(not bool(item["default_setting_allowed"]) for item in rows)
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "research_accuracy_gap_gate_passed": gate_passed,
        "claim_readiness": "limitations_ready_research_accuracy_gap; blocked formal accuracy release",
        "threshold_source": "docs/experiments/casee/tools/casee_audit.py build_release_gate metric gate",
        "thresholds": THRESHOLDS,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "recommended_tag": release_gate.get("recommended_tag"),
        "rows": rows,
        "summary": {
            "formal_official_mae_gap_to_15pp": formal["mae_gap_to_15pp"],
            "formal_official_r2_gap_to_positive": formal["r2_gap_to_positive"],
            "formal_official_pearson_gap_to_positive": formal["pearson_gap_to_positive"],
            "best_diagnostic_metric_gate_passed": any(
                item["metric_gate_passed"] for item in rows if item["protocol_role"].startswith("diagnostic")
            ),
            "post_hoc_upper_bound_metric_gate_passed": any(
                item["metric_gate_passed"] for item in rows if item["protocol_role"] == "post_hoc_upper_bound_only"
            ),
            "blockers": blockers,
        },
        "boundary": (
            "This gate quantifies the gap to the current project release metric threshold. "
            "It does not create new CFD output, does not improve official z=2 m metrics, "
            "does not authorize diagnostic sampling or post-hoc calibration as validation, "
            "and does not permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "candidate_id",
        "evidence_type",
        "protocol_role",
        "n",
        "height_m",
        "sampling_mode",
        "mae_pp",
        "r2",
        "pearson",
        "mae_gap_to_15pp",
        "r2_gap_to_positive",
        "pearson_gap_to_positive",
        "metric_gate_passed",
        "default_setting_allowed",
        "source_paths",
        "paper_use",
        "limitations",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow({key: item.get(key, "") for key in fields})


def fmt(value: Any, digits: int = 6) -> str:
    numeric = as_float(value)
    if numeric is None:
        return ""
    return f"{numeric:.{digits}f}"


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Case E Research Accuracy Gap Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gap gate passed: {payload['research_accuracy_gap_gate_passed']}",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        f"- Recommended tag: `{payload['recommended_tag']}`",
        "",
        "## Formal Gap",
        "",
        f"- MAE gap to <15 pp: {fmt(summary['formal_official_mae_gap_to_15pp'], 3)} pp",
        f"- R2 gap to >0: {fmt(summary['formal_official_r2_gap_to_positive'], 6)}",
        f"- Pearson gap to >0: {fmt(summary['formal_official_pearson_gap_to_positive'], 6)}",
        "",
        "## Candidate Rows",
        "",
        "| candidate | role | MAE pp | R2 | Pearson | metric gate | default? |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload["rows"]:
        lines.append(
            f"| `{item['candidate_id']}` | `{item['protocol_role']}` | {fmt(item['mae_pp'], 3)} | "
            f"{fmt(item['r2'], 6)} | {fmt(item['pearson'], 6)} | {item['metric_gate_passed']} | "
            f"{item['default_setting_allowed']} |"
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
                "research_accuracy_gap_gate_passed": payload["research_accuracy_gap_gate_passed"],
                "formal_mae_gap_to_15pp": payload["summary"]["formal_official_mae_gap_to_15pp"],
                "formal_r2_gap_to_positive": payload["summary"]["formal_official_r2_gap_to_positive"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["research_accuracy_gap_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
