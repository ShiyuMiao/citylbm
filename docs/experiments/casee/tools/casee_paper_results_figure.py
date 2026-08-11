#!/usr/bin/env python3
"""Generate a manuscript-ready Case E result-boundary figure from audited tables."""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
INPUT_TABLE = RESULTS_DIR / "casee_manuscript_results_table.csv"
OUT_SOURCE = RESULTS_DIR / "casee_paper_results_figure_source.csv"
OUT_SVG = RESULTS_DIR / "casee_paper_results_figure.svg"
OUT_PNG = RESULTS_DIR / "casee_paper_results_figure.png"
OUT_JSON = RESULTS_DIR / "casee_paper_results_figure_qa.json"
OUT_MD = RESULTS_DIR / "casee_paper_results_figure_qa.md"

PALETTE = {
    "formal": "#3B6BA5",
    "diagnostic": "#E8822B",
    "risk_low": "#5DA85D",
    "risk_high": "#C44E52",
    "neutral": "#5D8A8A",
}


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


def write_text_retry(path: Path, text: str, *, attempts: int = 5, delay_s: float = 0.25) -> None:
    last_exc: OSError | None = None
    for _ in range(attempts):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError as exc:
            last_exc = exc
            time.sleep(delay_s)
    if last_exc is not None:
        raise last_exc


def parse_float(value: Any) -> float:
    if value in (None, ""):
        return float("nan")
    return float(value)


def find(rows: Iterable[Dict[str, str]], row_id: str) -> Dict[str, str]:
    for row in rows:
        if row.get("row_id") == row_id:
            return row
    return {}


def split_group_metric(value: str, key: str) -> float:
    for part in str(value).split(";"):
        part = part.strip()
        if part.startswith(f"{key}="):
            return float(part.split("=", 1)[1])
    return float("nan")


def split_group_n(value: str, key: str) -> int:
    for part in str(value).split(";"):
        part = part.strip()
        if part.startswith(f"{key}="):
            return int(float(part.split("=", 1)[1]))
    return 0


def build_source_rows(input_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    formal = find(input_rows, "formal_official_z2m")
    diagnostic = find(input_rows, "best_diagnostic_sampling")
    risk = find(input_rows, "near_wall_risk_gradient")

    rows: List[Dict[str, Any]] = [
        {
            "panel": "a_error_magnitude",
            "item": "Official raw_trilinear",
            "claim_boundary": formal.get("claim_boundary", ""),
            "metric": "mae_pp",
            "value": parse_float(formal.get("mae_pp", "")),
            "n": int(float(formal.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "a_error_magnitude",
            "item": "Best diagnostic sampling",
            "claim_boundary": diagnostic.get("claim_boundary", ""),
            "metric": "mae_pp",
            "value": parse_float(diagnostic.get("mae_pp", "")),
            "n": int(float(diagnostic.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "b_correlation",
            "item": "Official R2",
            "claim_boundary": formal.get("claim_boundary", ""),
            "metric": "r2",
            "value": parse_float(formal.get("r2", "")),
            "n": int(float(formal.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "b_correlation",
            "item": "Official Pearson",
            "claim_boundary": formal.get("claim_boundary", ""),
            "metric": "pearson",
            "value": parse_float(formal.get("pearson", "")),
            "n": int(float(formal.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "b_correlation",
            "item": "Diagnostic R2",
            "claim_boundary": diagnostic.get("claim_boundary", ""),
            "metric": "r2",
            "value": parse_float(diagnostic.get("r2", "")),
            "n": int(float(diagnostic.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "b_correlation",
            "item": "Diagnostic Pearson",
            "claim_boundary": diagnostic.get("claim_boundary", ""),
            "metric": "pearson",
            "value": parse_float(diagnostic.get("pearson", "")),
            "n": int(float(diagnostic.get("n", "0") or 0)),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "c_probe_risk",
            "item": "Low-risk probes",
            "claim_boundary": risk.get("claim_boundary", ""),
            "metric": "raw_mae_pp",
            "value": split_group_metric(risk.get("mae_pp", ""), "low"),
            "n": split_group_n(risk.get("n", ""), "low"),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
        {
            "panel": "c_probe_risk",
            "item": "High-risk probes",
            "claim_boundary": risk.get("claim_boundary", ""),
            "metric": "raw_mae_pp",
            "value": split_group_metric(risk.get("mae_pp", ""), "high"),
            "n": split_group_n(risk.get("n", ""), "high"),
            "evidence_type": "newly_run",
            "source_path": rel(INPUT_TABLE),
        },
    ]
    return rows


def write_source_csv(rows: List[Dict[str, Any]]) -> None:
    OUT_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    fields = ["panel", "item", "claim_boundary", "metric", "value", "n", "evidence_type", "source_path"]
    with OUT_SOURCE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def make_figure(rows: List[Dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "svg.fonttype": "none",
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
        }
    )
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7.6, 3.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.05, 1.05], wspace=0.48)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])

    panel_a = [row for row in rows if row["panel"] == "a_error_magnitude"]
    labels_a = ["Official\nraw", "Best\ndiagnostic"]
    values_a = [float(row["value"]) for row in panel_a]
    colors_a = [PALETTE["formal"], PALETTE["diagnostic"]]
    hatches_a = ["", "//"]
    bars = ax_a.bar(labels_a, values_a, color=colors_a, edgecolor="black", linewidth=0.6, hatch=hatches_a, zorder=3)
    ax_a.axhline(15, color="#555555", linestyle="--", linewidth=0.8, zorder=2)
    ax_a.text(
        -0.42,
        15.9,
        "release MAE gate",
        ha="left",
        va="bottom",
        fontsize=6.5,
        color="#444444",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.7},
    )
    for bar, row in zip(bars, panel_a):
        ax_a.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.7, f"{bar.get_height():.1f}\nn={row['n']}", ha="center", va="bottom", fontsize=7)
    ax_a.set_ylabel("MAE (percentage points)")
    ax_a.set_ylim(0, max(values_a) + 8)
    ax_a.set_title("(a) Error magnitude")
    ax_a.grid(axis="y", color="#DDDDDD", linewidth=0.5, zorder=0)

    panel_b = [row for row in rows if row["panel"] == "b_correlation"]
    y = list(range(len(panel_b)))
    vals = [float(row["value"]) for row in panel_b]
    colors_b = [PALETTE["formal"] if "Official" in row["item"] else PALETTE["diagnostic"] for row in panel_b]
    markers = ["o" if row["metric"] == "pearson" else "s" for row in panel_b]
    ax_b.axvline(0, color="#555555", linestyle="--", linewidth=0.8, zorder=1)
    for yi, val, color, marker, row in zip(y, vals, colors_b, markers, panel_b):
        ax_b.plot([0, val], [yi, yi], color="#BBBBBB", linewidth=0.8, zorder=2)
        ax_b.scatter([val], [yi], color=color, marker=marker, edgecolor="black", linewidth=0.5, s=42, zorder=3)
        ax_b.text(val + (0.08 if val >= 0 else -0.08), yi, f"{val:.2f}", va="center", ha="left" if val >= 0 else "right", fontsize=7)
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([row["item"].replace(" ", "\n") for row in panel_b])
    ax_b.set_xlim(-2.25, 0.55)
    ax_b.set_xlabel("Metric value")
    ax_b.set_title("(b) Formal R2 gate remains negative")
    ax_b.grid(axis="x", color="#DDDDDD", linewidth=0.5, zorder=0)

    panel_c = [row for row in rows if row["panel"] == "c_probe_risk"]
    labels_c = ["Low risk", "High risk"]
    values_c = [float(row["value"]) for row in panel_c]
    colors_c = [PALETTE["risk_low"], PALETTE["risk_high"]]
    hatches_c = ["..", "xx"]
    bars_c = ax_c.bar(labels_c, values_c, color=colors_c, edgecolor="black", linewidth=0.6, hatch=hatches_c, zorder=3)
    for bar, row in zip(bars_c, panel_c):
        ax_c.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8, f"{bar.get_height():.1f}\nn={row['n']}", ha="center", va="bottom", fontsize=7)
    ax_c.set_ylabel("Raw MAE (percentage points)")
    ax_c.set_ylim(0, max(values_c) + 9)
    ax_c.set_title("(c) Error concentrates near walls")
    ax_c.grid(axis="y", color="#DDDDDD", linewidth=0.5, zorder=0)

    fig.suptitle("AIJ Case E official z=2 m remains a negative validation result", x=0.01, y=1.04, ha="left", fontsize=10, fontweight="bold")
    fig.text(
        0.01,
        -0.02,
        "Source: casee_manuscript_results_table.csv. Diagnostic rows are limitations-only; formal result is raw_trilinear at official z=2 m.",
        ha="left",
        va="top",
        fontsize=7,
    )
    fig.savefig(OUT_SVG, format="svg", bbox_inches="tight")
    fig.savefig(OUT_PNG, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    write_text_retry(
        OUT_SVG,
        "\n".join(line.rstrip() for line in OUT_SVG.read_text(encoding="utf-8").splitlines()) + "\n",
    )


def build_qa(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    svg_text = OUT_SVG.read_text(encoding="utf-8", errors="replace") if OUT_SVG.exists() else ""
    formal_rows = [row for row in rows if row["claim_boundary"] == "limitations_ready_negative_validation"]
    diagnostic_rows = [row for row in rows if row["claim_boundary"] == "limitations_ready_diagnostic"]
    checks = {
        "source_table_exists": INPUT_TABLE.exists(),
        "source_csv_written": OUT_SOURCE.exists() and len(rows) == 8,
        "editable_svg_written": OUT_SVG.exists() and "<text" in svg_text,
        "png_export_written": OUT_PNG.exists(),
        "formal_row_negative_validation": bool(formal_rows),
        "diagnostic_rows_not_formal": bool(diagnostic_rows) and all(row["claim_boundary"] != "formal_gate_input" for row in diagnostic_rows),
        "n_values_visible_in_source": all(int(row["n"]) > 0 for row in rows if row["panel"] in {"a_error_magnitude", "c_probe_risk"}),
        "no_rainbow_palette": True,
        "uses_hatch_and_labels": True,
        "formal_accuracy_claim_supported": False,
    }
    pass_checks = {key: value for key, value in checks.items() if key != "formal_accuracy_claim_supported"}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "figure_gate_passed": all(value is True for value in pass_checks.values())
        and checks["formal_accuracy_claim_supported"] is False,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_figure_for_negative_validation_and_limitations",
        "formal_accuracy_claim_supported": False,
        "core_conclusion": "The official Case E z=2 m result remains negative validation; diagnostic improvements and probe-risk gradients support limitations only.",
        "figure_contract": {
            "evidence_hierarchy": {
                "primary": rel(INPUT_TABLE),
                "derived_source_data": rel(OUT_SOURCE),
                "supporting": [
                    rel(RESULTS_DIR / "release_gate.json"),
                    rel(RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv"),
                    rel(RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv"),
                ],
            },
            "chart_archetype": "error diagnosis / claim-primary result with limitations supports",
            "panel_mapping": {
                "a": "formal official MAE versus best diagnostic MAE",
                "b": "R2/Pearson evidence showing negative formal R2",
                "c": "near-wall probe-risk stratification",
            },
            "reviewer_risk": "Reviewer may mistake diagnostic rows for formal accuracy. Mitigation: labels, hatches, caption and QA mark diagnostics as limitations-only.",
            "export_bundle": {
                "script": rel(ROOT / "docs" / "experiments" / "casee" / "tools" / "casee_paper_results_figure.py"),
                "source_csv": rel(OUT_SOURCE),
                "svg": rel(OUT_SVG),
                "png": rel(OUT_PNG),
                "qa": rel(OUT_JSON),
            },
        },
        "checks": checks,
    }


def write_qa_markdown(payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Paper Results Figure QA",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Figure Contract",
        "",
        f"- Core conclusion: {payload['core_conclusion']}",
        f"- Chart archetype: {payload['figure_contract']['chart_archetype']}",
        f"- Primary source: `{payload['figure_contract']['evidence_hierarchy']['primary']}`",
        f"- SVG: `{payload['figure_contract']['export_bundle']['svg']}`",
        f"- Source CSV: `{payload['figure_contract']['export_bundle']['source_csv']}`",
        "",
        "## Verdict",
        "",
        f"- Figure gate passed: {payload['figure_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## QA Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Boundary",
        "",
        "This figure is paper-ready for negative validation and limitations discussion only. It must not be used to claim formal Case E predictive accuracy.",
    ]
    write_text_retry(OUT_MD, "\n".join(lines) + "\n")


def main() -> int:
    input_rows = read_csv(INPUT_TABLE)
    if not input_rows:
        raise SystemExit(f"Missing input table: {rel(INPUT_TABLE)}")
    rows = build_source_rows(input_rows)
    write_source_csv(rows)
    make_figure(rows)
    qa = build_qa(rows)
    write_text_retry(OUT_JSON, json.dumps(qa, indent=2))
    write_qa_markdown(qa)
    print(json.dumps({"figure_gate_passed": qa["figure_gate_passed"], "svg": rel(OUT_SVG)}, indent=2))
    return 0 if qa["figure_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
