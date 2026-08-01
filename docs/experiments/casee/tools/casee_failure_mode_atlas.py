#!/usr/bin/env python3
"""Summarize AIJ Case E failure modes from audited diagnostic artifacts."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_failure_mode_atlas.json"
OUT_CSV = RESULTS_DIR / "casee_failure_mode_atlas.csv"
OUT_MD = RESULTS_DIR / "casee_failure_mode_atlas.md"
OUT_PNG = RESULTS_DIR / "casee_failure_mode_atlas.png"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get_row(rows: Iterable[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def as_float(row: Dict[str, Any], key: str) -> Optional[float]:
    value = row.get(key)
    if value in (None, ""):
        return None
    return float(value)


def fmt(value: Any, digits: int = 3) -> str:
    if value in (None, ""):
        return "NA"
    return f"{float(value):.{digits}f}"


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = [
        "failure_mode_id",
        "status",
        "severity",
        "primary_evidence",
        "quantitative_signal",
        "paper_use",
        "software_feedback",
        "default_policy",
        "next_verification",
        "forbidden_claim",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_rows() -> Dict[str, Any]:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    metrics = release_gate.get("metrics", {})
    native = read_csv(RESULTS_DIR / "casee_native_metric_comparison.csv")
    ground_nu = read_csv(RESULTS_DIR / "casee_ground_nu_diagnostic_comparison.csv")
    zcenter_modes = read_csv(RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv")
    voxel_groups = read_csv(RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv")
    solid_groups = read_csv(RESULTS_DIR / "casee_solid_corner_group_metrics.csv")
    spatial = read_csv(RESULTS_DIR / "casee_spatial_alignment_diagnostic.csv")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")

    dx2_base = get_row(native, "run_id", "dx2_yn_sgs_sampledt2000")
    dx2_best = get_row(ground_nu, "run_id", "dx2_gshift1_nu001")
    z_raw = get_row(zcenter_modes, "sampling_mode", "raw_trilinear")
    z_vertical = get_row(zcenter_modes, "sampling_mode", "vertical_valid_above")
    z_plus = get_row(zcenter_modes, "sampling_mode", "z_plus_half")
    low = get_row(voxel_groups, "group", "low")
    high = get_row(voxel_groups, "group", "high")
    solid0 = get_row(solid_groups, "solid_corner_neighbors_max", "0")
    solid4 = get_row(solid_groups, "solid_corner_neighbors_max", "4")
    identity = get_row(spatial, "transform", "identity")
    best_r2 = min(spatial, key=lambda r: abs(as_float(r, "r2") or -999.0), default={})

    rows = [
        {
            "failure_mode_id": "FM001_official_metric_gate",
            "status": "blocked",
            "severity": "critical",
            "primary_evidence": "docs/experiments/casee/results/release_gate.json",
            "quantitative_signal": (
                f"official raw_trilinear z=2 m n={metrics.get('n')}; "
                f"MAE={fmt(metrics.get('mae_pp'))} pp; R2={fmt(metrics.get('r2'), 6)}; "
                f"Pearson={fmt(metrics.get('pearson'), 6)}"
            ),
            "paper_use": "Use as negative validation and release-boundary evidence.",
            "software_feedback": "Do not promote diagnostic settings to defaults until this gate improves on official raw_trilinear output.",
            "default_policy": "No formal v0.4.0 default accuracy model.",
            "next_verification": "casee_audit.py on a completed official z=2 m 80-probe CSV.",
            "forbidden_claim": "Do not claim predictive accuracy or formal v0.4.0 readiness.",
        },
        {
            "failure_mode_id": "FM002_underprediction_bias",
            "status": "active_limitation",
            "severity": "critical",
            "primary_evidence": "docs/experiments/casee/results/casee_ground_nu_diagnostic_comparison.csv",
            "quantitative_signal": (
                f"dx2 base bias={fmt(dx2_base.get('bias_pp'))} pp and best gshift/nu diagnostic "
                f"bias={fmt(dx2_best.get('bias_pp'))} pp; z-center official bias={fmt(metrics.get('bias_pp'))} pp"
            ),
            "paper_use": "Use to explain systematic low-speed prediction at official pedestrian probes.",
            "software_feedback": "Prioritize near-ground velocity recovery, wall treatment, and inlet turbulence diagnostics.",
            "default_policy": "Keep nu_lbm and z-origin changes default-off.",
            "next_verification": "Repeat official raw_trilinear metrics after a physically justified wall/inlet change.",
            "forbidden_claim": "Do not treat reduced bias alone as accuracy validation.",
        },
        {
            "failure_mode_id": "FM003_probe_sampling_sensitivity",
            "status": "diagnostic_only",
            "severity": "major",
            "primary_evidence": "docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv",
            "quantitative_signal": (
                f"raw MAE={fmt(z_raw.get('mae_pp'))} pp, R2={fmt(z_raw.get('r2'), 6)}; "
                f"vertical_valid_above MAE={fmt(z_vertical.get('mae_pp'))} pp, R2={fmt(z_vertical.get('r2'), 6)}; "
                f"z_plus_half MAE={fmt(z_plus.get('mae_pp'))} pp, R2={fmt(z_plus.get('r2'), 6)}"
            ),
            "paper_use": "Use only as a probe-protocol sensitivity limitation.",
            "software_feedback": "Expose sampling modes as diagnostics while preserving raw_trilinear as the formal metric.",
            "default_policy": "Diagnostic modes remain non-default and non-formal.",
            "next_verification": "Only raw_trilinear z=2 m can update release_gate.json.",
            "forbidden_claim": "Do not substitute z_plus_half or vertical_valid_above for official z=2 m.",
        },
        {
            "failure_mode_id": "FM004_near_wall_solid_corner_risk",
            "status": "active_limitation",
            "severity": "critical",
            "primary_evidence": "docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv",
            "quantitative_signal": (
                f"low-risk raw MAE={fmt(low.get('raw_mae_pp'))} pp (n={low.get('n')}); "
                f"high-risk raw MAE={fmt(high.get('raw_mae_pp'))} pp (n={high.get('n')}); "
                f"solid0 MAE={fmt(solid0.get('mae_pp'))} pp; solid4 MAE={fmt(solid4.get('mae_pp'))} pp"
            ),
            "paper_use": "Use as the main limitations evidence for near-wall and solid-corner protocol risk.",
            "software_feedback": "Add default-off wall/roughness/voxelization follow-up switches and retain per-probe risk metadata.",
            "default_policy": "No promotion without official raw_trilinear improvement and Case A smoke regression.",
            "next_verification": "Compare low/moderate/high risk residuals after the next completed official run.",
            "forbidden_claim": "Do not claim the solver is validated for pedestrian-height corner probes.",
        },
        {
            "failure_mode_id": "FM005_spatial_alignment_unlikely",
            "status": "diagnostic_checked",
            "severity": "moderate",
            "primary_evidence": "docs/experiments/casee/results/casee_spatial_alignment_diagnostic.csv",
            "quantitative_signal": (
                f"identity Pearson={fmt(identity.get('pearson'), 6)}, R2={fmt(identity.get('r2'), 6)}; "
                f"best available transform `{best_r2.get('transform')}` still has R2={fmt(best_r2.get('r2'), 6)}"
            ),
            "paper_use": "Use to narrow the error explanation away from a simple x/y convention mistake.",
            "software_feedback": "Keep wind-direction and lattice-convention audits in the Case E preset.",
            "default_policy": "No coordinate transform becomes default from this diagnostic.",
            "next_verification": "Rerun spatial audit only if coordinate mapping code changes.",
            "forbidden_claim": "Do not claim all coordinate conventions are exhausted beyond the tested transforms.",
        },
        {
            "failure_mode_id": "FM006_runtime_preflight_blocked",
            "status": "blocked",
            "severity": "critical",
            "primary_evidence": "docs/experiments/casee/results/casee_official_run_preflight.json",
            "quantitative_signal": f"official_followup_run_allowed={preflight.get('official_followup_run_allowed')}; blocked={','.join(preflight.get('blocked_gates', []))}",
            "paper_use": "Use to explain why no new long-run result was added in this release candidate.",
            "software_feedback": "Keep launch preflight gates before scheduling long official runs.",
            "default_policy": "Do not run or publish new official results while preflight is blocked.",
            "next_verification": "Clear GPU, VS C++ and Rhino/GHA evidence, then rerun preflight.",
            "forbidden_claim": "Do not describe the current environment as ready for more long native validation.",
        },
    ]
    return {
        "release_gate": release_gate,
        "failure_modes": rows,
        "plot_values": {
            "official_raw_mae_pp": as_float(metrics, "mae_pp"),
            "low_risk_raw_mae_pp": as_float(low, "raw_mae_pp"),
            "high_risk_raw_mae_pp": as_float(high, "raw_mae_pp"),
            "vertical_valid_above_mae_pp": as_float(z_vertical, "mae_pp"),
            "z_plus_half_mae_pp": as_float(z_plus, "mae_pp"),
        },
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metrics = payload["release_gate"].get("metrics", {})
    lines = [
        "# Case E Failure-Mode Atlas",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Formal v0.4.0 release allowed: {payload['release_gate'].get('formal_release_allowed')}",
        f"- Official z=2 m MAE: {metrics.get('mae_pp')} pp",
        f"- Official z=2 m R2: {metrics.get('r2')}",
        f"- Official z=2 m Pearson: {metrics.get('pearson')}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        "",
        "## Failure Modes",
        "",
        "| id | status | severity | quantitative signal | paper use |",
        "|---|---|---|---|---|",
    ]
    for row in payload["failure_modes"]:
        lines.append(
            f"| `{row['failure_mode_id']}` | {row['status']} | {row['severity']} | "
            f"{row['quantitative_signal']} | {row['paper_use']} |"
        )
    lines += [
        "",
        "## Software Feedback",
        "",
    ]
    for row in payload["failure_modes"]:
        lines += [
            f"### {row['failure_mode_id']}",
            "",
            f"- Primary evidence: `{row['primary_evidence']}`",
            f"- Software feedback: {row['software_feedback']}",
            f"- Default policy: {row['default_policy']}",
            f"- Next verification: {row['next_verification']}",
            f"- Forbidden claim: {row['forbidden_claim']}",
            "",
        ]
    lines += [
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plot(path: Path, values: Dict[str, Optional[float]]) -> Dict[str, Any]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"created": False, "reason": f"matplotlib unavailable: {exc}"}

    labels = [
        "official raw",
        "low-risk raw",
        "high-risk raw",
        "vertical valid above",
        "z plus half",
    ]
    keys = [
        "official_raw_mae_pp",
        "low_risk_raw_mae_pp",
        "high_risk_raw_mae_pp",
        "vertical_valid_above_mae_pp",
        "z_plus_half_mae_pp",
    ]
    vals = [values.get(key) for key in keys]
    if any(v is None for v in vals):
        return {"created": False, "reason": "missing one or more plot values"}
    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = ["#444444", "#2c7fb8", "#d95f0e", "#756bb1", "#969696"]
    ax.barh(labels, vals, color=colors)
    ax.set_xlabel("MAE (percentage points)")
    ax.set_title("AIJ Case E z=2 m Diagnostic MAE Boundaries")
    ax.axvline(15.0, color="#b2182b", linestyle="--", linewidth=1.2, label="release target")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {"created": True, "path": path.resolve().relative_to(ROOT).as_posix()}


def main() -> int:
    built = build_rows()
    plot = write_plot(OUT_PNG, built["plot_values"])
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "limitations_ready_failure_mode_atlas",
        "release_gate": built["release_gate"],
        "failure_modes": built["failure_modes"],
        "plot": plot,
        "boundary": (
            "This atlas organizes existing negative-validation and diagnostic evidence. "
            "It does not add a new CFD run, does not change official z=2 m metrics, and does not allow formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(OUT_CSV, built["failure_modes"])
    write_markdown(OUT_MD, payload)
    print(json.dumps({"failure_modes": len(built["failure_modes"]), "plot_created": plot.get("created"), "out_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
