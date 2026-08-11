#!/usr/bin/env python3
"""Audit residual structure for the current best Case E diagnostic candidate.

This script does not change the formal AIJ Case E metric.  It turns the
C014 probe CSV into paper-facing limitation evidence and a follow-up target
for physics/software work.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
C014_CSV = RESULTS_DIR / "casee_c014_inlet_k_synthetic_s2p0_nosgs_20260809_235100_probe_time_mean.csv"
INLET_AUDIT = RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
OUT_JSON = RESULTS_DIR / "casee_c014_residual_structure_audit.json"
OUT_CSV = RESULTS_DIR / "casee_c014_residual_structure_audit.csv"
OUT_TOP_CSV = RESULTS_DIR / "casee_c014_residual_top_probes.csv"
OUT_MD = RESULTS_DIR / "casee_c014_residual_structure_audit.md"
OUT_PNG = RESULTS_DIR / "casee_c014_residual_structure_audit.png"


NUMERIC_COLUMNS = {
    "No.",
    "x_m",
    "y_m",
    "z_m",
    "official_velocity_ratio",
    "predicted_velocity_ratio",
    "speed_lbm",
    "solid_corner_neighbors_max",
    "nearest_valid_velocity_ratio",
    "fluid_weighted_velocity_ratio",
    "vertical_valid_above_velocity_ratio",
    "z_plus_half_velocity_ratio",
    "fluid_weighted_solid_neighbors_max",
    "nearest_valid_search_radius_max",
    "vertical_valid_above_dz_max",
    "samples",
}


def read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows: List[Dict[str, Any]] = []
        for row in csv.DictReader(f):
            out: Dict[str, Any] = {}
            for key, value in row.items():
                if key in NUMERIC_COLUMNS:
                    out[key] = float(value)
                else:
                    out[key] = value
            rows.append(out)
        return rows


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0.0 or vy <= 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def metric_summary(rows: List[Dict[str, Any]], pred_col: str = "predicted_velocity_ratio") -> Dict[str, Any]:
    if not rows:
        return {
            "n": 0,
            "mae_pp": None,
            "rmse_pp": None,
            "bias_pp": None,
            "r2": None,
            "pearson": None,
            "pred_mean": None,
            "official_mean": None,
        }
    obs = [float(r["official_velocity_ratio"]) for r in rows]
    pred = [float(r[pred_col]) for r in rows]
    residuals = [p - o for p, o in zip(pred, obs)]
    mean_obs = sum(obs) / len(obs)
    sse = sum(e * e for e in residuals)
    sst = sum((o - mean_obs) ** 2 for o in obs)
    return {
        "n": len(rows),
        "mae_pp": 100.0 * sum(abs(e) for e in residuals) / len(residuals),
        "rmse_pp": 100.0 * math.sqrt(sse / len(residuals)),
        "bias_pp": 100.0 * sum(residuals) / len(residuals),
        "r2": None if sst <= 0.0 else 1.0 - sse / sst,
        "pearson": pearson(pred, obs),
        "pred_mean": sum(pred) / len(pred),
        "official_mean": mean_obs,
    }


def affine_upper_bound(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    x = [float(r["predicted_velocity_ratio"]) for r in rows]
    y = [float(r["official_velocity_ratio"]) for r in rows]
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    var_x = sum((v - mx) ** 2 for v in x)
    if var_x <= 0.0:
        return {"slope": None, "intercept": None, "metrics": metric_summary(rows)}
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    slope = cov / var_x
    intercept = my - slope * mx
    adjusted = []
    for row in rows:
        adjusted.append({**row, "affine_predicted_velocity_ratio": slope * float(row["predicted_velocity_ratio"]) + intercept})
    return {
        "slope": slope,
        "intercept": intercept,
        "metrics": metric_summary(adjusted, "affine_predicted_velocity_ratio"),
        "interpretation": "This is a post-hoc diagnostic upper bound only; it is not a formal validation result.",
    }


def classify_solid(row: Dict[str, Any]) -> str:
    n = int(float(row["solid_corner_neighbors_max"]))
    if n <= 0:
        return "solid0_low_risk"
    if n <= 2:
        return "solid1_2_moderate_risk"
    return "solid3_4_high_risk"


def official_bin(row: Dict[str, Any]) -> str:
    value = float(row["official_velocity_ratio"])
    if value < 0.3:
        return "official_low_lt_0p3"
    if value < 0.6:
        return "official_mid_0p3_0p6"
    return "official_high_ge_0p6"


def pred_bin(row: Dict[str, Any]) -> str:
    value = float(row["predicted_velocity_ratio"])
    if value < 0.3:
        return "pred_low_lt_0p3"
    if value < 0.6:
        return "pred_mid_0p3_0p6"
    return "pred_high_ge_0p6"


def group_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groupers: List[tuple[str, Callable[[Dict[str, Any]], bool]]] = [
        ("all", lambda r: True),
        ("upstream_y_ge_0_inferred", lambda r: float(r["y_m"]) >= 0.0),
        ("downstream_y_lt_0_inferred", lambda r: float(r["y_m"]) < 0.0),
        ("x_west_lt_0", lambda r: float(r["x_m"]) < 0.0),
        ("x_east_ge_0", lambda r: float(r["x_m"]) >= 0.0),
        ("solid0_low_risk", lambda r: classify_solid(r) == "solid0_low_risk"),
        ("solid1_2_moderate_risk", lambda r: classify_solid(r) == "solid1_2_moderate_risk"),
        ("solid3_4_high_risk", lambda r: classify_solid(r) == "solid3_4_high_risk"),
        ("official_low_lt_0p3", lambda r: official_bin(r) == "official_low_lt_0p3"),
        ("official_mid_0p3_0p6", lambda r: official_bin(r) == "official_mid_0p3_0p6"),
        ("official_high_ge_0p6", lambda r: official_bin(r) == "official_high_ge_0p6"),
        ("pred_low_lt_0p3", lambda r: pred_bin(r) == "pred_low_lt_0p3"),
        ("pred_mid_0p3_0p6", lambda r: pred_bin(r) == "pred_mid_0p3_0p6"),
        ("pred_high_ge_0p6", lambda r: pred_bin(r) == "pred_high_ge_0p6"),
    ]
    out = []
    for group, predicate in groupers:
        subset = [row for row in rows if predicate(row)]
        metrics = metric_summary(subset)
        out.append(
            {
                "group": group,
                **metrics,
                "claim_readiness": "limitations_ready_residual_structure" if subset else "blocked_empty_group",
                "paper_use": paper_use_for_group(group, metrics),
            }
        )
    return out


def paper_use_for_group(group: str, metrics: Dict[str, Any]) -> str:
    if metrics["n"] == 0:
        return "Do not cite; no probes in this group."
    if group == "all":
        return "Use as the C014 official-height negative-improvement summary."
    if "official_high" in group:
        return "Use to explain that high-speed official probes remain under-recovered."
    if "official_low" in group:
        return "Use to explain overprediction in sheltered official low-speed probes."
    if "downstream" in group:
        return "Use to identify the downstream half as a priority residual region."
    if "solid" in group:
        return "Use as near-wall and solid-corner limitation evidence."
    return "Use as residual-structure diagnostic evidence only."


def top_probe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    total_sse = 0.0
    for row in rows:
        residual = float(row["predicted_velocity_ratio"]) - float(row["official_velocity_ratio"])
        sse = residual * residual
        total_sse += sse
        enriched.append(
            {
                "No.": int(float(row["No."])),
                "x_m": row["x_m"],
                "y_m": row["y_m"],
                "official_velocity_ratio": row["official_velocity_ratio"],
                "predicted_velocity_ratio": row["predicted_velocity_ratio"],
                "residual_pp": 100.0 * residual,
                "abs_error_pp": 100.0 * abs(residual),
                "sse_share": 0.0,
                "solid_corner_neighbors_max": int(float(row["solid_corner_neighbors_max"])),
                "solid_risk_group": classify_solid(row),
                "official_bin": official_bin(row),
                "diagnostic_z_plus_half_ratio": row["z_plus_half_velocity_ratio"],
                "diagnostic_vertical_valid_above_ratio": row["vertical_valid_above_velocity_ratio"],
            }
        )
    for row in enriched:
        row["sse_share"] = 0.0 if total_sse <= 0.0 else (row["residual_pp"] / 100.0) ** 2 / total_sse
    return sorted(enriched, key=lambda r: float(r["abs_error_pp"]), reverse=True)


def diagnostic_mode_metrics(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    modes = [
        ("raw_trilinear", "predicted_velocity_ratio", "formal"),
        ("nearest_valid", "nearest_valid_velocity_ratio", "diagnostic_only"),
        ("fluid_weighted", "fluid_weighted_velocity_ratio", "diagnostic_only"),
        ("vertical_valid_above", "vertical_valid_above_velocity_ratio", "diagnostic_only"),
        ("z_plus_half", "z_plus_half_velocity_ratio", "diagnostic_only"),
    ]
    out = []
    for mode, col, boundary in modes:
        metrics = metric_summary(rows, col)
        out.append({"sampling_mode": mode, "claim_boundary": boundary, **metrics})
    return out


def write_plot(rows: List[Dict[str, Any]], groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"created": False, "reason": f"matplotlib unavailable: {exc}"}

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    ax = axes[0]
    residual_pp = [
        100.0 * (float(r["predicted_velocity_ratio"]) - float(r["official_velocity_ratio"]))
        for r in rows
    ]
    sc = ax.scatter(
        [float(r["x_m"]) for r in rows],
        [float(r["y_m"]) for r in rows],
        c=residual_pp,
        cmap="coolwarm",
        vmin=-45,
        vmax=45,
        s=42,
        edgecolors="black",
        linewidths=0.25,
    )
    ax.axhline(0.0, color="#555555", linewidth=0.8)
    ax.axvline(0.0, color="#555555", linewidth=0.8)
    ax.set_title("C014 residuals at official z=2 m")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    fig.colorbar(sc, ax=ax, label="predicted - official (pp)")

    selected = [
        "all",
        "upstream_y_ge_0_inferred",
        "downstream_y_lt_0_inferred",
        "official_low_lt_0p3",
        "official_mid_0p3_0p6",
        "official_high_ge_0p6",
        "solid0_low_risk",
        "solid3_4_high_risk",
    ]
    lookup = {row["group"]: row for row in groups}
    vals = [lookup[key]["mae_pp"] for key in selected]
    labels = [
        "all",
        "y>=0",
        "y<0",
        "obs<0.3",
        "0.3-0.6",
        "obs>=0.6",
        "solid0",
        "solid3-4",
    ]
    axes[1].barh(labels, vals, color="#4c78a8")
    axes[1].axvline(15.0, color="#b2182b", linestyle="--", linewidth=1.2)
    axes[1].set_title("Residual groups")
    axes[1].set_xlabel("MAE (percentage points)")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=180)
    plt.close(fig)
    return {"created": True, "path": OUT_PNG.resolve().relative_to(ROOT).as_posix()}


def recommendations(groups: List[Dict[str, Any]], affine: Dict[str, Any]) -> List[Dict[str, str]]:
    lookup = {row["group"]: row for row in groups}
    high = lookup.get("official_high_ge_0p6", {})
    low = lookup.get("official_low_lt_0p3", {})
    downstream = lookup.get("downstream_y_lt_0_inferred", {})
    affine_r2 = ((affine.get("metrics") or {}).get("r2"))
    return [
        {
            "id": "C016_channel_response_wall_inlet_candidate",
            "priority": "1",
            "status": "implementation_then_native_run",
            "rationale": (
                f"C014 high-speed official probes have MAE={high.get('mae_pp')} pp and "
                f"bias={high.get('bias_pp')} pp, while low-speed probes have bias={low.get('bias_pp')} pp. "
                "The model compresses the observed velocity-ratio range."
            ),
            "minimum_evidence_needed": "Completed official z=2 m raw_trilinear 80-probe CSV, complete FluidX3D log, and Case A smoke regression.",
            "default_policy": "default_off_until_metric_gate_passes",
        },
        {
            "id": "C017_downstream_residual_followup",
            "priority": "2",
            "status": "candidate_generation_after_gpu_recovery",
            "rationale": (
                f"The inferred downstream half has R2={downstream.get('r2')} and "
                f"Pearson={downstream.get('pearson')}, so global MAE improvement is not enough."
            ),
            "minimum_evidence_needed": "A targeted run that changes physics rather than post-processing and improves downstream raw_trilinear metrics.",
            "default_policy": "diagnostic_only",
        },
        {
            "id": "reject_posthoc_affine_accuracy_claim",
            "priority": "0",
            "status": "claim_boundary",
            "rationale": f"Even a post-hoc affine fit only reaches R2={affine_r2}, so calibration cannot justify paper-grade accuracy.",
            "minimum_evidence_needed": "None; this is a prohibition from the residual audit.",
            "default_policy": "forbidden_as_validation",
        },
    ]


def write_markdown(payload: Dict[str, Any], groups: List[Dict[str, Any]], top_rows: List[Dict[str, Any]], modes: List[Dict[str, Any]]) -> None:
    best = payload["c014_metrics"]
    affine = payload["affine_upper_bound"]["metrics"]
    lines = [
        "# C014 Residual Structure Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        "- Evidence type: `newly_run` audit over `preexisting_artifact` C014 solver output",
        f"- C014 MAE: {best['mae_pp']:.3f} pp",
        f"- C014 R2: {best['r2']:.6f}",
        f"- C014 Pearson: {best['pearson']:.6f}",
        f"- Post-hoc affine upper-bound R2: {affine['r2']:.6f}",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## Residual Groups",
        "",
        "| group | n | MAE pp | bias pp | R2 | Pearson | paper use |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in groups:
        lines.append(
            f"| `{row['group']}` | {row['n']} | {fmt(row['mae_pp'])} | {fmt(row['bias_pp'])} | "
            f"{fmt(row['r2'], 6)} | {fmt(row['pearson'], 6)} | {row['paper_use']} |"
        )
    lines += [
        "",
        "## Diagnostic Sampling Check",
        "",
        "| mode | boundary | MAE pp | R2 | Pearson |",
        "|---|---|---:|---:|---:|",
    ]
    for row in modes:
        lines.append(
            f"| `{row['sampling_mode']}` | {row['claim_boundary']} | {fmt(row['mae_pp'])} | "
            f"{fmt(row['r2'], 6)} | {fmt(row['pearson'], 6)} |"
        )
    lines += [
        "",
        "## Largest Absolute Residuals",
        "",
        "| No. | x | y | official | predicted | residual pp | solid | bin |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in top_rows[:12]:
        lines.append(
            f"| {row['No.']} | {float(row['x_m']):.1f} | {float(row['y_m']):.1f} | "
            f"{float(row['official_velocity_ratio']):.3f} | {float(row['predicted_velocity_ratio']):.3f} | "
            f"{float(row['residual_pp']):.2f} | {row['solid_corner_neighbors_max']} | {row['official_bin']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def main() -> int:
    if not C014_CSV.exists():
        raise SystemExit(f"Missing C014 CSV: {C014_CSV}")
    rows = read_csv(C014_CSV)
    if len(rows) != 80:
        raise SystemExit(f"Expected 80 C014 probe rows, found {len(rows)}")
    groups = group_rows(rows)
    top_rows = top_probe_rows(rows)
    modes = diagnostic_mode_metrics(rows)
    c014_metrics = metric_summary(rows)
    affine = affine_upper_bound(rows)
    release_gate = read_json(RELEASE_GATE)
    inlet_audit = read_json(INLET_AUDIT)
    plot = write_plot(rows, groups)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_id": "casee_c014_residual_structure_audit",
        "status": "completed_residual_structure_audit",
        "evidence_type": "newly_run",
        "solver_output_evidence_type": "preexisting_artifact",
        "claim_readiness": "limitations_ready_residual_structure; blocked formal accuracy release",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "source_csv": C014_CSV.resolve().relative_to(ROOT).as_posix(),
        "source_candidate": "C014_inlet_k_synthetic_fullplane_s2p00_no_sgs",
        "source_candidate_metric_gate_passed": inlet_audit.get("metric_gate_passed"),
        "current_release_gate_official_metrics": release_gate.get("metrics"),
        "c014_metrics": c014_metrics,
        "affine_upper_bound": affine,
        "groups": groups,
        "diagnostic_sampling_modes": modes,
        "top_abs_residual_probes": top_rows[:20],
        "recommendations": recommendations(groups, affine),
        "plot": plot,
        "boundary": (
            "This audit explains why the best C014 diagnostic candidate is still not paper-grade validation. "
            "It uses official z=2 m raw_trilinear C014 rows for residual analysis, but it does not add a new "
            "FluidX3D run, does not alter release_gate.json official metrics, and does not justify formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(
        OUT_CSV,
        groups,
        ["group", "n", "mae_pp", "rmse_pp", "bias_pp", "r2", "pearson", "pred_mean", "official_mean", "claim_readiness", "paper_use"],
    )
    write_csv(
        OUT_TOP_CSV,
        top_rows,
        [
            "No.",
            "x_m",
            "y_m",
            "official_velocity_ratio",
            "predicted_velocity_ratio",
            "residual_pp",
            "abs_error_pp",
            "sse_share",
            "solid_corner_neighbors_max",
            "solid_risk_group",
            "official_bin",
            "diagnostic_z_plus_half_ratio",
            "diagnostic_vertical_valid_above_ratio",
        ],
    )
    write_markdown(payload, groups, top_rows, modes)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "c014_r2": c014_metrics["r2"],
                "affine_upper_bound_r2": affine["metrics"]["r2"],
                "out_json": OUT_JSON.resolve().relative_to(ROOT).as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
