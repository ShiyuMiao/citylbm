from __future__ import annotations

import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patches


ROOT = Path.cwd()
FIG = ROOT / "figures"
OUT = FIG / "nature_style"
SRC = OUT / "source_data"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"

for folder in [OUT, SRC, MAN, REP, PAPER]:
    folder.mkdir(parents=True, exist_ok=True)


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 6.5,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.7,
        "axes.labelsize": 6.5,
        "axes.titlesize": 7,
        "xtick.labelsize": 5.8,
        "ytick.labelsize": 5.8,
        "legend.fontsize": 5.8,
        "legend.frameon": False,
        "figure.dpi": 180,
        "savefig.dpi": 600,
    }
)


NEUTRAL = "#4D4D4D"
LIGHT = "#E7E9ED"
MID = "#9AA3B2"
BLUE = "#4C78A8"
TEAL = "#4AA79B"
GOLD = "#C9A646"
RED = "#B85C5C"
PURPLE = "#7B6FAE"
GREEN = "#6AA76F"
PALE_BLUE = "#DCE8F4"
PALE_RED = "#F4DEDE"
PALE_GREEN = "#E3F0E5"


def mm_to_in(mm: float) -> float:
    return mm / 25.4


def panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.08) -> None:
    ax.text(x, y, label, transform=ax.transAxes, ha="left", va="bottom", fontsize=8, fontweight="bold")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def upsert_csv(path: Path, row: dict[str, object], fields: list[str], unique_field: str) -> None:
    rows = read_csv(path)
    rows = [item for item in rows if item.get(unique_field) != str(row[unique_field])]
    rows.append({field: row.get(field, "") for field in fields})
    write_csv(path, rows, fields)


def short_label(text: str) -> str:
    replacements = {
        "combined enclosure score": "combined\nenclosure",
        "local built fraction, r=30 m": "built\nfraction",
        "mean building height": "mean\nheight",
        "sector enclosure, r=50 m": "sector\nenclosure",
        "height / sqrt(area)": "relative\nheight",
        "footprint area": "footprint\narea",
        "persistent_shelter": "persistent\nshelter",
        "mixed_low_speed_context": "mixed low-\nspeed",
        "near_to_context_recovery": "near-to-context\nrecovery",
        "directionally_reactive": "directionally\nreactive",
        "user_photogrammetry_fullres_stl": "visual mesh",
        "core_photogrammetry_extent_prism_collision_z0": "core prism",
        "district_prism_collision_z0": "district prism",
        "lod3_direct_obj_collision_candidate": "LoD3 cand.",
        "lod2_or_lod3_derived_closed_prism": "target prism",
    }
    return replacements.get(text, text.replace("_", " "))


def load_panel_data() -> dict[str, pd.DataFrame]:
    metrics = pd.read_csv(FIG / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    baseline = metrics[metrics["averaging"] == "time_mean_3_samples_then_direction_mean"].copy()
    baseline = baseline.sort_values("z_height_m_approx")

    distance = pd.read_csv(FIG / "paraview_vtk_core_dx2m_building_distance_stats.csv")
    order = {"0-4m": 0, "4-10m": 1, "10-20m": 2, ">20m": 3}
    dist_rows = []
    for name, group in sorted(distance.groupby("distance_to_building_bin"), key=lambda item: order[item[0]]):
        weights = group["open_cells"].astype(float)
        dist_rows.append(
            {
                "distance_bin": name,
                "mean_vr": np.average(group["mean_vr"], weights=weights),
                "p95_vr": np.average(group["p95_vr"], weights=weights),
                "stagnation_ratio": np.average(group["stagnation_ratio_vr_lt_0p2"], weights=weights),
                "open_cells": int(group["open_cells"].sum()),
            }
        )
    dist = pd.DataFrame(dist_rows)

    morph = pd.read_csv(FIG / "experiment3_deep_conclusion_morphology_support.csv")
    morph = morph[morph["response_metric"].isin(["directional_mean_vr", "directional_range_mean_vr"])].copy()
    morph["abs_rho"] = morph["spearman_rho"].abs()
    morph = (
        morph.sort_values("abs_rho", ascending=False)
        .groupby("analysis_zone", group_keys=False)
        .head(3)
        .sort_values(["analysis_zone", "abs_rho"], ascending=[False, False])
    )

    stage = pd.read_csv(FIG / "morphology_directional_fingerprint_stage_summary.csv")
    stage_order = ["persistent_shelter", "mixed_low_speed_context", "near_to_context_recovery", "directionally_reactive"]
    stage["stage_transition_class"] = pd.Categorical(stage["stage_transition_class"], stage_order, ordered=True)
    stage = stage.sort_values("stage_transition_class")

    s1 = pd.read_csv(FIG / "fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv")
    s2 = pd.read_csv(FIG / "fluidx3d_s0_s2_network_porosity_metric_comparison.csv")
    design_rows = []
    for _, row in s1.iterrows():
        design_rows.append(
            {
                "scenario": "S1",
                "height_m": row["z_height_m_approx"],
                "delta_mean_vr": row["delta_vr_mean"],
                "delta_stagnation": row["delta_stagnation_ratio_vr_lt_0p2"],
            }
        )
    for _, row in s2.iterrows():
        design_rows.append(
            {
                "scenario": "S2",
                "height_m": row["z_height_m_approx"],
                "delta_mean_vr": row["delta_vr_mean"],
                "delta_stagnation": row["delta_stagnation_ratio_vr_lt_0p2"],
            }
        )
    design = pd.DataFrame(design_rows)

    gcri = pd.read_csv(MAN / "gcri_scoring_table.csv")
    keep = [
        "user_photogrammetry_fullres_stl",
        "lod3_direct_obj_collision_candidate",
        "core_photogrammetry_extent_prism_collision_z0",
        "district_prism_collision_z0",
        "lod2_or_lod3_derived_closed_prism",
    ]
    gcri = gcri[gcri["geometry_id"].isin(keep)].copy()
    gcri["geometry_id"] = pd.Categorical(gcri["geometry_id"], keep, ordered=True)
    gcri = gcri.sort_values("geometry_id")

    uncertainty = pd.read_csv(FIG / "experiment3_effect_size_uncertainty_summary.csv")
    return {
        "baseline": baseline,
        "distance": dist,
        "morphology": morph,
        "stage": stage,
        "design": design,
        "gcri": gcri,
        "uncertainty": uncertainty,
    }


def export_source_data(data: dict[str, pd.DataFrame]) -> None:
    rows: list[dict[str, object]] = []
    for panel, df in data.items():
        for _, record in df.iterrows():
            item = {"panel_data": panel}
            item.update(record.to_dict())
            rows.append(item)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    write_csv(SRC / "experiment3_conclusion_figure_source_data.csv", rows, fields)


def draw_workflow(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    panel_label(ax, "a", -0.03, 1.02)
    ax.text(0.00, 0.98, "Digital twin evidence chain", fontsize=7, fontweight="bold", va="top")

    nodes = [
        (0.04, 0.62, 0.17, 0.23, "Visual layer\nUAS mesh\nRhino audit", "", PALE_BLUE),
        (0.29, 0.62, 0.17, 0.23, "Collision layer\nclosed STL\nz0 aligned", "", PALE_GREEN),
        (0.54, 0.62, 0.17, 0.23, "Fluid layer\n8 directions\nFluidX3D", "", "#EFE7F4"),
        (0.79, 0.62, 0.17, 0.23, "Design layer\nmorphology\nS1/S2 test", "", PALE_RED),
    ]
    for x, y, w, h, title, subtitle, color in nodes:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=color, ec=MID, lw=0.8)
        ax.add_patch(box)
        ax.text(
            x + w / 2,
            y + h * 0.52,
            title,
            ha="center",
            va="center",
            fontsize=5.4,
            fontweight="bold",
            color=NEUTRAL,
            linespacing=1.05,
        )
    for x in [0.22, 0.47, 0.72]:
        ax.annotate("", xy=(x + 0.055, 0.735), xytext=(x, 0.735), arrowprops=dict(arrowstyle="-|>", lw=0.8, color=NEUTRAL))

    ax.text(0.04, 0.43, "Figure claim", fontsize=6.2, fontweight="bold", color=NEUTRAL)
    ax.text(
        0.04,
        0.31,
        "Wind-screening value appears after visual realism is\n"
        "converted into auditable collision geometry and\n"
        "interpreted through local building form.",
        fontsize=5.8,
        color=NEUTRAL,
        va="top",
        linespacing=1.15,
    )
    ax.text(0.61, 0.43, "Evidence boundary", fontsize=6.2, fontweight="bold", color=NEUTRAL)
    ax.text(
        0.61,
        0.31,
        "Screening CFD: supported\n"
        "Field validation: blocked\n"
        "Annual compliance / pollutant: blocked",
        fontsize=5.8,
        color=NEUTRAL,
        va="top",
        linespacing=1.15,
    )


def draw_gcri(ax: plt.Axes, gcri: pd.DataFrame) -> None:
    panel_label(ax, "b")
    colors = [RED, "#D8B365", TEAL, GREEN, "#5AAE61"]
    labels = [short_label(x) for x in gcri["geometry_id"].astype(str)]
    y = np.arange(len(gcri))
    ax.barh(y, gcri["GCRI"], color=colors, height=0.62)
    ax.axvline(0.8, color=NEUTRAL, lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("GCRI (0-1)")
    ax.set_title("Geometry readiness")
    for yi, val in zip(y, gcri["GCRI"]):
        ax.text(min(val + 0.025, 0.98), yi, f"{val:.3f}", va="center", fontsize=5.6, color=NEUTRAL)
    ax.invert_yaxis()


def draw_vertical(ax: plt.Axes, baseline: pd.DataFrame) -> None:
    panel_label(ax, "c")
    h = baseline["z_height_m_approx"].to_numpy()
    mean = baseline["vr_mean"].to_numpy()
    stag = baseline["stagnation_ratio_vr_lt_0p2"].to_numpy()
    ax.plot(mean, h, "-o", color=BLUE, ms=3, lw=1.1, label="mean VR")
    ax.set_xlabel("mean VR")
    ax.set_ylabel("height (m)")
    ax.set_ylim(0, 42)
    ax.set_xlim(0, 1.15)
    ax.grid(axis="x", color=LIGHT, lw=0.6)
    ax2 = ax.twiny()
    ax2.plot(stag, h, "-s", color=RED, ms=2.8, lw=1.0, label="VR<0.2")
    ax2.set_xlim(0, 1.0)
    ax2.set_xlabel("stagnation ratio")
    ax.set_title("Vertical recovery")
    lines = ax.get_lines() + ax2.get_lines()
    labels = [line.get_label() for line in lines]
    ax.legend(lines, labels, loc="lower right", handlelength=1.4)


def draw_distance(ax: plt.Axes, dist: pd.DataFrame) -> None:
    panel_label(ax, "d")
    x = np.arange(len(dist))
    ax.bar(x, dist["mean_vr"], color=TEAL, width=0.68)
    ax.set_xticks(x)
    ax.set_xticklabels(dist["distance_bin"])
    ax.set_ylim(0, 0.11)
    ax.set_ylabel("mean VR")
    ax.set_title("Distance-to-building gradient")
    ax.grid(axis="y", color=LIGHT, lw=0.6)
    ax2 = ax.twinx()
    ax2.plot(x, dist["stagnation_ratio"], color=RED, marker="o", ms=3, lw=1.0)
    ax2.set_ylim(0, 1.05)
    ax2.set_yticks([])
    ax2.spines["right"].set_visible(False)
    ax.text(0.03, 0.92, "bars: mean VR", transform=ax.transAxes, fontsize=5.4, color=TEAL)
    ax2.text(0.03, 0.80, "line: low-speed", transform=ax.transAxes, fontsize=5.4, color=RED)


def draw_morphology(ax: plt.Axes, morph: pd.DataFrame) -> None:
    panel_label(ax, "e")
    labels = []
    for _, row in morph.iterrows():
        parameter = str(row["parameter_label"])
        response = "range" if "range" in str(row["response_metric"]) else "mean"
        if "combined enclosure" in parameter:
            base = "enclosure"
        elif "built fraction" in parameter:
            base = "built fraction"
        elif "sector enclosure" in parameter:
            base = "sector enclosure"
        elif "height" in parameter:
            base = "height"
        else:
            base = parameter
        labels.append(f"{base} {response}")
    y = np.arange(len(morph))
    colors = [BLUE if z == "local_context_20_50m" else PURPLE for z in morph["analysis_zone"]]
    ax.barh(y, morph["spearman_rho"], color=colors, height=0.58)
    ax.axvline(0, color=NEUTRAL, lw=0.7)
    ax.set_yticks([])
    ax.set_xlim(-0.68, 0.18)
    ax.set_xlabel("Spearman rho")
    ax.set_title("Morphology-response signal")
    for yi, label in zip(y, labels):
        ax.text(-0.665, yi, label, ha="left", va="center", fontsize=5.4, color=NEUTRAL)
    ax.invert_yaxis()


def draw_stage(ax: plt.Axes, stage: pd.DataFrame) -> None:
    panel_label(ax, "f")
    x = np.arange(len(stage))
    ax.bar(x - 0.17, stage["mean_local_context_vr"], width=0.34, color=BLUE, label="local VR")
    ax.bar(x + 0.17, stage["mean_directional_range_vr"], width=0.34, color=GOLD, label="directional range")
    for xi, n in zip(x, stage["n_components"]):
        ax.text(xi, 0.023, f"n={int(n)}", ha="center", va="bottom", fontsize=5.2, rotation=90, color=NEUTRAL)
    ax.set_xticks(x)
    ax.set_xticklabels([short_label(s) for s in stage["stage_transition_class"].astype(str)], rotation=25, ha="right")
    ax.set_ylabel("VR")
    ax.set_title("Near-to-context classes")
    ax.set_ylim(0, max(stage["mean_directional_range_vr"].max(), stage["mean_local_context_vr"].max()) * 1.35)
    ax.legend(loc="upper left")
    ax.grid(axis="y", color=LIGHT, lw=0.6)


def draw_design(ax: plt.Axes, design: pd.DataFrame) -> None:
    panel_label(ax, "g")
    colors = {"S1": RED, "S2": PURPLE}
    heights = sorted(design["height_m"].unique())
    x_lookup = {height: i for i, height in enumerate(heights)}
    for scenario, group in design.groupby("scenario"):
        group = group.sort_values("height_m")
        x = [x_lookup[h] for h in group["height_m"]]
        ax.plot(x, group["delta_mean_vr"] * 1000, marker="o", ms=3, lw=1.1, color=colors[scenario], label=f"{scenario} mean VR")
    ax.axhline(0, color=NEUTRAL, lw=0.8)
    ax.set_xticks(range(len(heights)))
    ax.set_xticklabels([str(int(h)) for h in heights])
    ax.set_xlabel("height (m)")
    ax.set_ylabel("delta mean VR (x10^-3)")
    ax.set_title("Design sensitivity is near-null")
    ax.legend(loc="lower right")
    ax.grid(axis="y", color=LIGHT, lw=0.6)
    ax.margins(x=0.08)


def draw_evidence_boundary(ax: plt.Axes) -> None:
    panel_label(ax, "h")
    ax.set_axis_off()
    ax.set_title("Paper-safe conclusion", loc="left", pad=4)
    rows = [
        ("Supported", "data-to-CFD layer separation"),
        ("Supported", "campus-core low-speed screening"),
        ("Supported", "morphology as local-context response"),
        ("Supported", "S1/S2 negative sensitivity"),
        ("Blocked", "field / wind-tunnel validation"),
        ("Blocked", "annual comfort compliance"),
        ("Blocked", "pollutant dispersion / GCBTE"),
    ]
    for i, (status, text) in enumerate(rows):
        y = 0.90 - i * 0.12
        color = GREEN if status == "Supported" else RED
        ax.add_patch(patches.Circle((0.035, y), 0.018, fc=color, ec="none", transform=ax.transAxes))
        ax.text(0.075, y, status, transform=ax.transAxes, va="center", fontsize=5.7, color=color, fontweight="bold")
        ax.text(0.29, y, text, transform=ax.transAxes, va="center", fontsize=5.7, color=NEUTRAL)


def make_figure(data: dict[str, pd.DataFrame]) -> list[Path]:
    fig = plt.figure(figsize=(mm_to_in(183), mm_to_in(170)))
    gs = fig.add_gridspec(
        4,
        12,
        height_ratios=[0.95, 1.05, 1.05, 0.95],
        width_ratios=[1] * 12,
        hspace=0.78,
        wspace=0.95,
    )
    draw_workflow(fig.add_subplot(gs[0, :8]))
    draw_gcri(fig.add_subplot(gs[0, 8:]), data["gcri"])
    draw_vertical(fig.add_subplot(gs[1, 0:3]), data["baseline"])
    draw_distance(fig.add_subplot(gs[1, 3:6]), data["distance"])
    draw_morphology(fig.add_subplot(gs[1, 6:]), data["morphology"])
    draw_stage(fig.add_subplot(gs[2, 0:7]), data["stage"])
    draw_design(fig.add_subplot(gs[2, 7:]), data["design"])
    draw_evidence_boundary(fig.add_subplot(gs[3, :]))
    fig.suptitle(
        "Experiment 3 conclusion: from digital-twin readiness to campus wind-screening evidence",
        fontsize=7.4,
        fontweight="bold",
        x=0.02,
        ha="left",
        y=0.995,
    )
    stem = OUT / "experiment3_conclusion_figure_nature"
    outputs = []
    for ext, kwargs in [
        ("svg", {}),
        ("pdf", {}),
        ("png", {"dpi": 600}),
        ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}}),
    ]:
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, bbox_inches="tight", **kwargs)
        outputs.append(path)
    plt.close(fig)
    return outputs


def write_panel_map() -> list[dict[str, object]]:
    rows = [
        {
            "panel": "a",
            "content_to_express": "Overall evidence chain from TUM2TWIN visual data to CFD-ready collision geometry, FluidX3D simulation and design interpretation.",
            "recommended_form": "Schematic-led evidence-flow panel.",
            "source_data": "manuscript logic; reports/claim_boundary.md; manifests/experiment3_master_manuscript_assembly_map.csv",
            "paper_role": "Defines the logic of the whole conclusion figure.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
        },
        {
            "panel": "b",
            "content_to_express": "CFD readiness separates visual mesh from closed collision geometry.",
            "recommended_form": "Horizontal GCRI bar chart with readiness reference line.",
            "source_data": "manifests/gcri_scoring_table.csv",
            "paper_role": "Supports the digital-twin-to-CFD geometry conclusion.",
            "evidence_type": "newly_run + preexisting_artifact",
        },
        {
            "panel": "c",
            "content_to_express": "Pedestrian layer is low speed while flow recovers aloft.",
            "recommended_form": "Dual-axis vertical profile for mean VR and VR<0.2 ratio.",
            "source_data": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_role": "Quantifies vertical wind recovery.",
            "evidence_type": "newly_run",
        },
        {
            "panel": "d",
            "content_to_express": "Near-building zones are strongly sheltered; wind recovery is clearer in the wider local-context band.",
            "recommended_form": "Distance-band bar and line chart.",
            "source_data": "figures/paraview_vtk_core_dx2m_building_distance_stats.csv",
            "paper_role": "Connects wind response to building proximity.",
            "evidence_type": "newly_run",
        },
        {
            "panel": "e",
            "content_to_express": "Basic morphology parameters act as local-context screening descriptors.",
            "recommended_form": "Ranked Spearman correlation bars.",
            "source_data": "figures/experiment3_deep_conclusion_morphology_support.csv",
            "paper_role": "Replaces LCZ classification with more transferable morphology evidence.",
            "evidence_type": "newly_run",
        },
        {
            "panel": "f",
            "content_to_express": "Building response classes differ in local VR and directional reactivity.",
            "recommended_form": "Grouped bar chart by near-to-context response class.",
            "source_data": "figures/morphology_directional_fingerprint_stage_summary.csv",
            "paper_role": "Shows that wind response is classifiable as shelter, recovery or directional reactivity.",
            "evidence_type": "newly_run + blocked",
        },
        {
            "panel": "g",
            "content_to_express": "S1/S2 interventions are near-null or negative, so porosity alone is insufficient.",
            "recommended_form": "Height-wise delta line plot.",
            "source_data": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "paper_role": "Turns the design tests into a defensible negative design-sensitivity conclusion.",
            "evidence_type": "newly_run",
        },
        {
            "panel": "h",
            "content_to_express": "Separate manuscript-safe claims from blocked claim upgrades.",
            "recommended_form": "Compact evidence-boundary checklist.",
            "source_data": "manifests/experiment3_submission_debt_register.csv; reports/claim_boundary.md",
            "paper_role": "Prevents overclaiming in the conclusion.",
            "evidence_type": "newly_run + blocked",
        },
    ]
    write_csv(
        MAN / "experiment3_conclusion_figure_panel_map.csv",
        rows,
        ["panel", "content_to_express", "recommended_form", "source_data", "paper_role", "evidence_type"],
    )
    return rows


def write_text_outputs(panel_rows: list[dict[str, object]], outputs: list[Path]) -> None:
    panel_table = "\n".join(
        f"| {r['panel']} | {r['content_to_express']} | {r['recommended_form']} | {r['source_data']} | {r['evidence_type']} |"
        for r in panel_rows
    )
    report = f"""# Experiment 3 Conclusion Figure Plan

evidence_type: newly_run + preexisting_artifact + blocked

## Core Figure Contract

- Core conclusion: TUM2TWIN becomes useful for campus wind-environment design only after visual digital-twin data are converted into auditable CFD collision geometry; the resulting FluidX3D screening shows persistent pedestrian-layer low-speed conditions that are better interpreted through basic local building-form parameters than through LCZ classes or simple porosity alone.
- Figure archetype: asymmetric mixed-modality figure.
- Target journal/output: Nature-family double-column figure, 183 mm wide, 170 mm high before tight bounding-box export.
- Backend: Python / matplotlib only.
- Export bundle: SVG, PDF, PNG and LZW-compressed TIFF, with source data CSV.
- Reviewer risks: no field validation, no annual comfort/safety compliance, no pollutant dispersion, no GCBTE closure and no CityLBM-Grasshopper end-to-end execution.

## Panel Plan

| panel | content | figure form | source data | evidence_type |
|---|---|---|---|---|
{panel_table}

## Generated Files

- `figures/nature_style/experiment3_conclusion_figure_nature.svg`
- `figures/nature_style/experiment3_conclusion_figure_nature.pdf`
- `figures/nature_style/experiment3_conclusion_figure_nature.png`
- `figures/nature_style/experiment3_conclusion_figure_nature.tiff`
- `figures/nature_style/source_data/experiment3_conclusion_figure_source_data.csv`

## Nature-Style Checks

- Double-column width is used.
- Font family is sans-serif and text remains editable in SVG/PDF.
- Panel labels are lowercase bold letters.
- Quantitative panels are CSV-driven and no simulated or placeholder values are introduced.
- Red/green is not the only visual code; no rainbow colour map is used.
- Evidence boundaries are displayed as part of the figure instead of hidden in the caption.
"""
    (REP / "experiment3_conclusion_figure_plan.md").write_text(report, encoding="utf-8")

    zh = """# 图 E3：实验3结论组图图注

evidence_type: newly_run + preexisting_artifact + blocked

图 E3 | TUM2TWIN 数字孪生数据到校园风环境筛查结论的证据链。a，组图逻辑：摄影测量/UAS 可视化层首先用于场景核验，随后转化为 z0 对齐的封闭碰撞几何，再进入 FluidX3D 八风向模拟和建筑形态解释。b，GCRI 显示视觉网格与 CFD-ready 碰撞几何之间的可用性差异。c，垂直剖面显示行人高度低风速占优而高处流动恢复。d，建筑距离带统计显示近立面区域低速饱和，较宽的局地上下文带更适合讨论风恢复。e，形态参数相关性显示局地围合和建成比例是主要筛查信号。f，近立面到局地上下文的响应类别表明建筑单元可表现为持续遮蔽、低速混合、上下文恢复或方向敏感。g，S1/S2 设计敏感性为近零或负向，说明孔隙率不能单独作为通风优化目标。h，证据边界区分了本实验可支持的筛查结论与仍需实测、风洞、正式舒适评价、污染物扩散、GCBTE 或 CityLBM-GH 端到端证据支撑的主张。所有定量 panel 均由归档 CSV 复现；结果为筛查级 CFD 证据，不是正式年度舒适/安全合规评价。
"""
    (PAPER / "experiment3_conclusion_figure_legend_zh.md").write_text(zh, encoding="utf-8")

    en = """# Fig. E3 Legend

evidence_type: newly_run + preexisting_artifact + blocked

Fig. E3 | Evidence chain from TUM2TWIN digital-twin data to campus wind-environment screening conclusions. a, The figure logic separates the visual photogrammetry/UAS layer for scene audit, the z0-aligned closed collision layer for CFD, FluidX3D eight-direction simulation, and morphology-based design interpretation. b, GCRI contrasts visually faithful but CFD-fragile geometry with collision-ready geometries. c, Vertical profiles show low-speed dominance at the pedestrian layer and flow recovery aloft. d, Distance-to-building statistics show near-facade low-speed saturation and wider local-context wind recovery. e, Morphology correlations indicate that enclosure and local built fraction are the main screening signals. f, Near-to-context response classes separate persistent shelter, mixed low-speed context, recovery and directional reactivity. g, S1/S2 sensitivity remains near-null or negative, indicating that porosity alone is insufficient as a ventilation objective. h, The evidence-boundary panel separates supported screening claims from validation, annual comfort-compliance, pollutant, GCBTE and CityLBM-GH claims that remain blocked. Quantitative panels are reproduced from archived CSV files; the figure supports screening-level CFD conclusions rather than formal annual comfort or safety compliance.
"""
    (PAPER / "experiment3_conclusion_figure_legend_en.md").write_text(en, encoding="utf-8")

    key_fields = ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"]
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Nature-style conclusion figure package",
            "metric": "panels / source-data file / export formats",
            "value": f"{len(panel_rows)} / 1 / svg+pdf+png+tiff",
            "source_artifact": "manifests/experiment3_conclusion_figure_panel_map.csv; reports/experiment3_conclusion_figure_plan.md; figures/nature_style/experiment3_conclusion_figure_nature.svg; figures/nature_style/source_data/experiment3_conclusion_figure_source_data.csv",
            "paper_safe_claim": "The final Experiment 3 conclusion figure links digital-twin readiness, wind-screening metrics, morphology interpretation, design sensitivity and evidence boundaries in a reproducible Nature-style panel layout.",
        },
        key_fields,
        "claim_layer",
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        {
            "claim": "Experiment 3 conclusion figure package maps each panel to reproducible source data, manuscript claim and evidence boundary.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_conclusion_figure_panel_map.csv; reports/experiment3_conclusion_figure_plan.md; paper_text/experiment3_conclusion_figure_legend_zh.md; paper_text/experiment3_conclusion_figure_legend_en.md; figures/nature_style/experiment3_conclusion_figure_nature.svg; figures/nature_style/source_data/experiment3_conclusion_figure_source_data.csv",
        },
        ["claim", "evidence_type", "source"],
        "claim",
    )


def main() -> None:
    data = load_panel_data()
    export_source_data(data)
    panel_rows = write_panel_map()
    outputs = make_figure(data)
    write_text_outputs(panel_rows, outputs)
    print("conclusion_figure_panels", len(panel_rows))
    for path in outputs:
        print(path.as_posix(), path.stat().st_size)


if __name__ == "__main__":
    main()
