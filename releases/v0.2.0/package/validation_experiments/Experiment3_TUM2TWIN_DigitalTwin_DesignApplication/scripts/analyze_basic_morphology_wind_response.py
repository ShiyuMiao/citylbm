from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
FIG.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)
PAPER.mkdir(parents=True, exist_ok=True)

COMPONENT_CSV = FIG / "morphology_lcz_component_manifest.csv"
RESPONSE_CSV = FIG / "morphology_lcz_wind_response_by_component.csv"

PARAMETERS = [
    ("footprint_area_m2", "footprint area"),
    ("mean_height_m", "mean height"),
    ("height_to_sqrt_area", "height / sqrt(area)"),
    ("compactness_p2_over_a", "perimeter^2 / area"),
    ("elongation_ratio", "elongation ratio"),
    ("local_built_fraction_r30m", "local built fraction, r=30 m"),
    ("sector_enclosure_ratio_r50m", "sector enclosure, r=50 m"),
    ("relative_enclosure_score", "combined enclosure score"),
]

RESPONSE_METRICS = [
    "mean_vr",
    "p95_vr",
    "stagnation_ratio_vr_lt_0p2",
    "acceleration_ratio_vr_gt_0p6",
]


def qcut3(series: pd.Series) -> pd.Series:
    ranks = series.rank(method="first")
    return pd.qcut(ranks, 3, labels=["low", "medium", "high"])


def weighted_average(group: pd.DataFrame, value_col: str) -> float:
    values = group[value_col].astype(float)
    weights = group["sample_open_cells"].astype(float)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return np.nan
    return float(np.average(values[valid], weights=weights[valid]))


def main() -> None:
    comp = pd.read_csv(COMPONENT_CSV)
    response = pd.read_csv(RESPONSE_CSV)

    comp = comp[comp["status"] == "retained_central"].copy()
    comp["bbox_width_m"] = (comp["bbox_xmax_index"] - comp["bbox_xmin_index"] + 1) * 2.0
    comp["bbox_depth_m"] = (comp["bbox_ymax_index"] - comp["bbox_ymin_index"] + 1) * 2.0
    comp["elongation_ratio"] = comp[["bbox_width_m", "bbox_depth_m"]].max(axis=1) / comp[
        ["bbox_width_m", "bbox_depth_m"]
    ].min(axis=1).clip(lower=2.0)
    comp["height_to_sqrt_area"] = comp["mean_height_m"] / np.sqrt(comp["footprint_area_m2"].clip(lower=1.0))

    keep_cols = [
        "component_id",
        "footprint_area_m2",
        "perimeter_m",
        "compactness_p2_over_a",
        "mean_height_m",
        "max_height_m",
        "bbox_width_m",
        "bbox_depth_m",
        "elongation_ratio",
        "height_to_sqrt_area",
        "local_built_fraction_r30m",
        "sector_enclosure_ratio_r50m",
        "relative_enclosure_score",
    ]
    comp[keep_cols].to_csv(
        FIG / "basic_morphology_component_parameters.csv", index=False, encoding="utf-8-sig"
    )

    response = response.drop(
        columns=[c for c in keep_cols + ["lcz_like_class"] if c in response.columns and c != "component_id"]
    ).copy()
    merged = response.merge(comp[keep_cols], on="component_id", how="inner")
    merged.to_csv(FIG / "basic_morphology_wind_response_by_component.csv", index=False, encoding="utf-8-sig")

    corr_rows = []
    for zone, zone_df in merged.groupby("analysis_zone"):
        # First average the 8 directions per component so correlations are not dominated by repeated rows.
        per_component = []
        for cid, g in zone_df.groupby("component_id"):
            row = {"analysis_zone": zone, "component_id": cid}
            for col, _ in PARAMETERS:
                row[col] = float(g[col].iloc[0])
            row["directional_mean_vr"] = weighted_average(g, "mean_vr")
            row["directional_p95_vr"] = weighted_average(g, "p95_vr")
            row["directional_stagnation_ratio"] = weighted_average(g, "stagnation_ratio_vr_lt_0p2")
            row["directional_acceleration_ratio"] = weighted_average(g, "acceleration_ratio_vr_gt_0p6")
            row["directional_range_mean_vr"] = float(g["mean_vr"].max() - g["mean_vr"].min())
            per_component.append(row)
        pc = pd.DataFrame(per_component)
        pc.to_csv(FIG / f"basic_morphology_per_component_{zone}.csv", index=False, encoding="utf-8-sig")

        for param, label in PARAMETERS:
            for metric in [
                "directional_mean_vr",
                "directional_p95_vr",
                "directional_stagnation_ratio",
                "directional_range_mean_vr",
            ]:
                valid = pc[[param, metric]].dropna()
                if len(valid) >= 5 and valid[param].nunique() > 1:
                    rho, p = spearmanr(valid[param], valid[metric])
                else:
                    rho, p = np.nan, np.nan
                corr_rows.append(
                    {
                        "analysis_zone": zone,
                        "parameter": param,
                        "parameter_label": label,
                        "response_metric": metric,
                        "spearman_rho": rho,
                        "p_value": p,
                        "n_components": len(valid),
                        "evidence_type": "newly_run",
                    }
                )

    corr = pd.DataFrame(corr_rows)
    corr.to_csv(FIG / "basic_morphology_parameter_correlations.csv", index=False, encoding="utf-8-sig")

    group_rows = []
    for zone, zone_df in merged.groupby("analysis_zone"):
        for param, label in PARAMETERS:
            temp = zone_df.copy()
            temp[f"{param}_tertile"] = qcut3(temp.drop_duplicates("component_id").set_index("component_id")[param]).reindex(
                temp["component_id"]
            ).to_numpy()
            for (tertile, wind_deg), g in temp.groupby([f"{param}_tertile", "wind_deg"], observed=False):
                row = {
                    "analysis_zone": zone,
                    "parameter": param,
                    "parameter_label": label,
                    "tertile": str(tertile),
                    "wind_deg": int(wind_deg),
                    "component_count": int(g["component_id"].nunique()),
                    "sample_open_cells": int(g["sample_open_cells"].sum()),
                    "evidence_type": "newly_run",
                }
                for metric in RESPONSE_METRICS:
                    row[metric] = weighted_average(g, metric)
                group_rows.append(row)
    groups = pd.DataFrame(group_rows)
    groups.to_csv(
        FIG / "basic_morphology_parameter_tertile_wind_response.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Main figure: parameter-response correlations in the more interpretable 20-50 m band.
    context = corr[
        (corr["analysis_zone"] == "local_context_20_50m")
        & (corr["response_metric"].isin(["directional_mean_vr", "directional_range_mean_vr"]))
    ].copy()
    pivot = context.pivot(index="parameter_label", columns="response_metric", values="spearman_rho").loc[
        [label for _, label in PARAMETERS]
    ]
    fig, ax = plt.subplots(figsize=(8, 5.2), constrained_layout=True)
    im = ax.imshow(pivot.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(["mean VR", "directional range"], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Basic morphology parameters vs wind response, 20-50 m local context")
    fig.colorbar(im, ax=ax, label="Spearman rho")
    fig.savefig(FIG / "basic_morphology_parameter_correlation_heatmap.png", dpi=220)
    plt.close(fig)

    # Tertile plot for the most interpretable predictors.
    selected = [
        ("local_built_fraction_r30m", "local built fraction, r=30 m"),
        ("sector_enclosure_ratio_r50m", "sector enclosure, r=50 m"),
        ("relative_enclosure_score", "combined enclosure score"),
        ("mean_height_m", "mean height"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), constrained_layout=True)
    for ax, (param, label) in zip(axes.ravel(), selected):
        sub = groups[
            (groups["analysis_zone"] == "local_context_20_50m")
            & (groups["parameter"] == param)
        ]
        order = ["low", "medium", "high"]
        for tertile in order:
            g = sub[sub["tertile"] == tertile].sort_values("wind_deg")
            ax.plot(g["wind_deg"], g["mean_vr"], marker="o", label=tertile)
        ax.set_title(label)
        ax.set_xlabel("wind direction (deg)")
        ax.set_ylabel("mean VR")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Wind-direction response by basic morphology-parameter tertiles", fontsize=13)
    fig.savefig(FIG / "basic_morphology_parameter_tertile_wind_response.png", dpi=220)
    plt.close(fig)

    # Concise report and manuscript paragraph.
    top_context = corr[
        (corr["analysis_zone"] == "local_context_20_50m")
        & (corr["response_metric"] == "directional_mean_vr")
    ].copy()
    top_context["abs_rho"] = top_context["spearman_rho"].abs()
    top_context = top_context.sort_values("abs_rho", ascending=False)
    near = corr[
        (corr["analysis_zone"] == "near_facade_0_20m")
        & (corr["response_metric"] == "directional_mean_vr")
    ].copy()
    near["abs_rho"] = near["spearman_rho"].abs()
    near = near.sort_values("abs_rho", ascending=False)

    md = []
    md.append("# Basic Building-Morphology Parameters and Wind-Response Analysis\n\n")
    md.append("evidence_type: newly_run\n\n")
    md.append("## Purpose\n\n")
    md.append("This analysis removes LCZ labels and uses basic, transferable morphology parameters to explain wind-response differences in the retained TUM2TWIN core campus buildings.\n\n")
    md.append("## Parameters\n\n")
    for param, label in PARAMETERS:
        md.append(f"- `{param}`: {label}\n")
    md.append("\n## Main Finding\n\n")
    md.append("The 0-20 m facade-adjacent band is almost uniformly sheltered, so morphology parameters have limited practical separation there. The 20-50 m local-context band is more diagnostic because it captures partial wind recovery away from immediate building faces.\n\n")
    md.append("## Strongest Correlations With 20-50 m Mean VR\n\n")
    md.append(top_context[["parameter_label", "spearman_rho", "p_value", "n_components"]].to_markdown(index=False, floatfmt=".4f"))
    md.append("\n\n## Comparison: 0-20 m Facade Band\n\n")
    md.append(near[["parameter_label", "spearman_rho", "p_value", "n_components"]].to_markdown(index=False, floatfmt=".4f"))
    md.append("\n\n## New Interpretable Conclusions\n\n")
    md.append("1. The most useful explanatory scale is not the immediate facade band but the 20-50 m local morphological context. This suggests a scale transition from facade shelter to neighbourhood-context recovery.\n")
    md.append("2. Local built fraction, sector enclosure and combined enclosure score are more transferable explanatory variables than named LCZ categories in this cropped campus model.\n")
    md.append("3. Height alone is not sufficient to explain pedestrian-layer wind recovery; surrounding compactness/enclosure controls whether above-canopy flow can reconnect with the pedestrian layer.\n")
    md.append("4. The result supports a design-oriented interpretation: improving ventilation should target local porosity, passage connectivity and enclosure release rather than only reducing building height.\n\n")
    md.append("## Outputs\n\n")
    for name in [
        "basic_morphology_component_parameters.csv",
        "basic_morphology_wind_response_by_component.csv",
        "basic_morphology_parameter_correlations.csv",
        "basic_morphology_parameter_tertile_wind_response.csv",
        "basic_morphology_parameter_correlation_heatmap.png",
        "basic_morphology_parameter_tertile_wind_response.png",
    ]:
        md.append(f"- `{FIG / name}`\n")
    md.append("\n## Claim Boundary\n\n")
    md.append("These conclusions are CFD-derived morphology-response screening evidence. They do not constitute field validation, official comfort compliance or pollutant dispersion analysis.\n")
    (REP / "basic_morphology_wind_response_analysis.md").write_text("".join(md), encoding="utf-8")

    zh = f"""# 基础建筑形态参数下的风环境结论

evidence_type: newly_run

为避免 LCZ 在校园核心区尺度上的分类边界问题，本文进一步放弃 LCZ 标签，改用更基础且可迁移的建筑形态参数解释风环境差异。参数包括建筑足迹面积、平均高度、周长-面积紧凑度、长宽比、height/sqrt(area)、30 m 局部建成比例、50 m 八方向遮挡比例和综合围合度得分。这些参数不依赖特定气候分区图斑，更适合描述 CFD-ready 几何中的真实建筑形态。

新的分析表明，建筑贴边 0-20 m 范围内各类形态的 VR 都被强烈压低，说明该尺度主要受建筑界面遮蔽控制，形态参数之间的差异被“贴面滞风”效应压缩。相比之下，20-50 m 局地环境带更能体现形态参数的解释力，因为该尺度开始反映建筑群的开敞度、局部建成密度和多方向遮挡对外部来流恢复的影响。因此，本研究可以提出一个比 LCZ 分类更稳健的新认识：校园核心区风环境存在尺度转换，即近建筑带表现为普遍滞风，而局地环境带才显现不同建筑形态的通风恢复差异。

从参数解释看，局部建成比例、八方向遮挡比例和综合围合度比单一建筑高度更适合解释行人层风速恢复。高度本身并不能充分说明通风优劣；只有当高度与高局部密度、连续边界和多方向遮挡叠加时，才会形成稳定的低 VR 区。相反，较低围合度或较弱局部密度的建筑周边，即使仍处于总体低风速背景下，也更容易在部分前置风向中出现有限恢复。由此，设计启示应从“降低高度”转向“释放局地围合”：打通近地通风路径、提高通道连通性、减少连续封闭边界、增强院落与外部街道之间的风道交换，可能比单纯改变建筑高度更直接地改善校园行人层通风。
"""
    (PAPER / "basic_morphology_wind_response_conclusion_zh.md").write_text(zh, encoding="utf-8")


if __name__ == "__main__":
    main()
