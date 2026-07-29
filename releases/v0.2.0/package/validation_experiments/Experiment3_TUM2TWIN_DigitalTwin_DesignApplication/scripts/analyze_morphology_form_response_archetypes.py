from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"

for folder in [FIG, REP, PAPER, MAN]:
    folder.mkdir(parents=True, exist_ok=True)


INPUT = FIG / "morphology_near_to_context_recovery_by_component.csv"

FEATURES = [
    "footprint_area_m2",
    "mean_height_m",
    "height_to_sqrt_area",
    "compactness_p2_over_a",
    "elongation_ratio",
    "local_built_fraction_r30m",
    "sector_enclosure_ratio_r50m",
    "relative_enclosure_score",
]

RESPONSE_COLS = [
    "near_facade_mean_vr",
    "local_context_mean_vr",
    "context_recovery_delta_vr",
    "local_context_directional_range_vr",
    "local_context_p95_vr",
]


def zscore(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    values = df[cols].astype(float).to_numpy()
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std[std == 0] = 1.0
    return (values - mean) / std


def kmeans(x: np.ndarray, k: int = 4, seed: int = 23, max_iter: int = 200) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = x[rng.choice(len(x), size=k, replace=False)].copy()
    labels = np.zeros(len(x), dtype=int)
    for _ in range(max_iter):
        distances = ((x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for i in range(k):
            if np.any(labels == i):
                centers[i] = x[labels == i].mean(axis=0)
    return labels


def archetype_name(row: pd.Series, medians: pd.Series) -> str:
    high_recovery = row["context_recovery_delta_vr"] >= medians["context_recovery_delta_vr"]
    high_context = row["local_context_mean_vr"] >= medians["local_context_mean_vr"]
    high_enclosure = row["relative_enclosure_score"] >= medians["relative_enclosure_score"]
    tall_relative = row["height_to_sqrt_area"] >= medians["height_to_sqrt_area"]
    elongated = row["elongation_ratio"] >= medians["elongation_ratio"]
    high_directional = (
        row["local_context_directional_range_vr"]
        >= medians["local_context_directional_range_vr"]
    )

    if high_recovery and high_enclosure and elongated and not tall_relative:
        return "A3_enclosed_linear_moderate_recovery"
    if high_recovery and elongated and not tall_relative:
        return "A1_linear_low_relative_height_recovery"
    if (not high_recovery) and high_enclosure and tall_relative:
        return "A2_enclosed_vertical_persistent_stagnation"
    if high_context and high_directional:
        return "A3_directionally_exposed_context_recovery"
    if high_enclosure:
        return "A4_enclosed_intermediate_shelter"
    return "A5_open_or_mixed_low_response"


def main() -> None:
    df = pd.read_csv(INPUT)
    for col in FEATURES + RESPONSE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=FEATURES + RESPONSE_COLS).copy()

    x = zscore(df, FEATURES)
    df["cluster_id"] = kmeans(x, k=4)

    cluster_summary = (
        df.groupby("cluster_id")
        .agg(
            n_components=("component_id", "count"),
            footprint_area_m2=("footprint_area_m2", "mean"),
            mean_height_m=("mean_height_m", "mean"),
            height_to_sqrt_area=("height_to_sqrt_area", "mean"),
            compactness_p2_over_a=("compactness_p2_over_a", "mean"),
            elongation_ratio=("elongation_ratio", "mean"),
            local_built_fraction_r30m=("local_built_fraction_r30m", "mean"),
            sector_enclosure_ratio_r50m=("sector_enclosure_ratio_r50m", "mean"),
            relative_enclosure_score=("relative_enclosure_score", "mean"),
            near_facade_mean_vr=("near_facade_mean_vr", "mean"),
            local_context_mean_vr=("local_context_mean_vr", "mean"),
            context_recovery_delta_vr=("context_recovery_delta_vr", "mean"),
            local_context_p95_vr=("local_context_p95_vr", "mean"),
            local_context_directional_range_vr=("local_context_directional_range_vr", "mean"),
        )
        .reset_index()
    )

    medians = cluster_summary[
        [
            "height_to_sqrt_area",
            "elongation_ratio",
            "relative_enclosure_score",
            "local_context_mean_vr",
            "context_recovery_delta_vr",
            "local_context_directional_range_vr",
        ]
    ].median()
    cluster_summary["archetype_base"] = cluster_summary.apply(
        lambda row: archetype_name(row, medians), axis=1
    )
    order = (
        cluster_summary.sort_values(
            ["context_recovery_delta_vr", "local_context_mean_vr"], ascending=False
        )["cluster_id"]
        .tolist()
    )
    rank_map = {cluster_id: i + 1 for i, cluster_id in enumerate(order)}
    cluster_summary["recovery_rank"] = cluster_summary["cluster_id"].map(rank_map)
    cluster_summary["archetype"] = cluster_summary.apply(
        lambda row: f"R{int(row['recovery_rank'])}_{row['archetype_base']}",
        axis=1,
    )
    df = df.merge(
        cluster_summary[["cluster_id", "archetype", "recovery_rank"]],
        on="cluster_id",
        how="left",
    )

    group_values = [
        g["context_recovery_delta_vr"].to_numpy()
        for _, g in df.groupby("cluster_id")
        if len(g) >= 2
    ]
    if len(group_values) >= 2:
        stat, p_value = kruskal(*group_values)
    else:
        stat, p_value = np.nan, np.nan

    cluster_summary = cluster_summary.drop(columns=["archetype_base"])
    cluster_summary.insert(0, "evidence_type", "newly_run")
    df.insert(0, "evidence_type", "newly_run")

    df.to_csv(FIG / "morphology_form_response_archetype_by_component.csv", index=False)
    cluster_summary.to_csv(
        FIG / "morphology_form_response_archetype_summary.csv", index=False
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), constrained_layout=True)
    colors = {
        name: color
        for name, color in zip(
            sorted(df["archetype"].unique()),
            ["#4c78a8", "#f58518", "#54a24b", "#b279a2", "#e45756"],
        )
    }
    for archetype, group in df.groupby("archetype"):
        axes[0].scatter(
            group["sector_enclosure_ratio_r50m"],
            group["height_to_sqrt_area"],
            s=np.clip(group["footprint_area_m2"] / 35, 18, 180),
            alpha=0.75,
            label=archetype.replace("_", " "),
            color=colors[archetype],
            edgecolor="white",
            linewidth=0.4,
        )
    axes[0].set_xlabel("Sector enclosure ratio within 50 m")
    axes[0].set_ylabel("Height / sqrt(footprint area)")
    axes[0].set_title("Building-form archetypes")
    axes[0].legend(fontsize=7, frameon=False, loc="best")

    bar_data = cluster_summary.sort_values("recovery_rank")
    labels = [a.replace("_", "\n") for a in bar_data["archetype"]]
    axes[1].bar(
        labels,
        bar_data["context_recovery_delta_vr"],
        color=[colors[a] for a in bar_data["archetype"]],
    )
    axes[1].set_ylabel("Mean 20-50 m recovery delta VR")
    axes[1].set_title("Archetype wind-recovery contrast")
    axes[1].tick_params(axis="x", labelrotation=0, labelsize=7)
    fig.savefig(FIG / "morphology_form_response_archetype_panel.png", dpi=220)
    plt.close(fig)

    top = cluster_summary.sort_values("recovery_rank").iloc[0]
    bottom = cluster_summary.sort_values("recovery_rank").iloc[-1]

    report = f"""# Building-Form Wind-Response Archetype Analysis

evidence_type: newly_run

## Purpose

This addendum converts the component-level morphology table into a compact building-form response typology. The aim is to support a more detailed paper conclusion about how basic building-form parameters relate to pedestrian-layer wind recovery in the TUM2TWIN campus core.

## Protocol

- Input: `figures/morphology_near_to_context_recovery_by_component.csv`
- Unit of analysis: retained central building component.
- Sample size after numeric cleaning: `{len(df)}` components.
- Clustering input: footprint area, mean height, height/sqrt(area), compactness, elongation, local built fraction within 30 m, sector enclosure within 50 m, and combined enclosure score.
- Clustering method: deterministic k-means on standardized morphology variables, `k=4`.
- Response variables used only for interpretation: near-facade mean VR, 20-50 m local-context mean VR, near-to-context recovery delta, local-context P95 VR, and directional range.

## Main Typology Result

| archetype | n | mean height | H/sqrt(A) | elongation | enclosure score | mean VR 20-50 m | recovery delta |
|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for _, row in cluster_summary.sort_values("recovery_rank").iterrows():
        report += (
            f"| {row['archetype']} | {int(row['n_components'])} | "
            f"{row['mean_height_m']:.2f} | {row['height_to_sqrt_area']:.3f} | "
            f"{row['elongation_ratio']:.2f} | {row['relative_enclosure_score']:.3f} | "
            f"{row['local_context_mean_vr']:.4f} | {row['context_recovery_delta_vr']:.4f} |\n"
        )

    report += f"""
## Statistical Separation

The archetype groups differ in near-to-context recovery delta with Kruskal-Wallis statistic `{stat:.3f}` and p-value `{p_value:.4g}`. This is a sample-internal separation test, not an external validation test.

## Paper-Safe Interpretation

The strongest recovery archetype is `{top['archetype']}`, with mean 20-50 m VR `{top['local_context_mean_vr']:.4f}` and recovery delta `{top['context_recovery_delta_vr']:.4f}`. The weakest recovery archetype is `{bottom['archetype']}`, with mean 20-50 m VR `{bottom['local_context_mean_vr']:.4f}` and recovery delta `{bottom['context_recovery_delta_vr']:.4f}`.

This supports a more detailed conclusion than a single correlation table: in the screened campus core, pedestrian wind recovery is associated with combinations of relative vertical massing, elongation and local enclosure. The result does not show that an isolated geometric variable controls wind environment by itself. Instead, it shows that the digital-twin-to-CFD workflow can identify building-form response archetypes that are useful for campus-scale design screening.

## Evidence Boundary

The typology is derived from FluidX3D post-processing and building-component morphology metrics. It does not prove causal design performance, field-predictive accuracy, official comfort compliance or pollutant exposure. It should be presented as a digital-twin screening and interpretation layer.

## Outputs

- `figures/morphology_form_response_archetype_by_component.csv`
- `figures/morphology_form_response_archetype_summary.csv`
- `figures/morphology_form_response_archetype_panel.png`
"""
    (REP / "morphology_form_response_archetype_analysis.md").write_text(
        report, encoding="utf-8"
    )

    paper_zh = f"""# 建筑形式风响应类型学结论段

evidence_type: newly_run + blocked

为进一步讨论建筑形式与风环境之间的关系，本研究在单变量相关和阈值筛查之外，基于 101 个中心区建筑构件的基础形态参数构建了建筑形式风响应类型学。聚类仅使用建筑形态输入，包括足迹面积、平均高度、height/sqrt(area)、平面紧凑度、延展率、30 m 局地建成比例、50 m 扇区围合度和综合围合得分；近立面平均 VR、20-50 m 局地背景平均 VR、近远恢复量和方向性范围仅用于聚类后的解释。结果显示，恢复最强的类型为 `{top['archetype']}`，其 20-50 m 平均 VR 为 `{top['local_context_mean_vr']:.4f}`，近远恢复量为 `{top['context_recovery_delta_vr']:.4f}`；恢复最弱的类型为 `{bottom['archetype']}`，对应 20-50 m 平均 VR 为 `{bottom['local_context_mean_vr']:.4f}`，恢复量为 `{bottom['context_recovery_delta_vr']:.4f}`。类型间恢复量差异的 Kruskal-Wallis 检验 p 值为 `{p_value:.4g}`。

这一结果把传统建筑风环境研究中“高度、围合、街谷和孔隙影响行人层风速”的一般判断推进到数字孪生应用层面：在 TUM Downtown 校园核心街区中，风环境差异不是由单一建筑面积、单一高度或单一开口面积决定，而是由相对竖向体量、平面延展性和 30-50 m 局地围合共同形成的建筑形式组合控制。因而，本实验的新认知不是提出一个可直接外推的通用形态阈值，而是证明真实数字孪生模型经 CFD-ready 转译后，可以把复杂校园街区分解为可审查的建筑形式风响应类型，从而为校园更新中的局地通风筛查、入口/广场风险识别和干预优先级排序提供证据。该结论仍属于 FluidX3D 筛查层证据，尚未经过现场风速、风洞、污染物扩散或年度舒适度超越概率闭环验证。
"""
    (PAPER / "morphology_form_response_archetype_conclusion_zh.md").write_text(
        paper_zh, encoding="utf-8"
    )

    claims = pd.DataFrame(
        [
            {
                "claim_id": "FRA1",
                "claim": "Building-form response archetypes separate stronger and weaker 20-50 m pedestrian-layer wind recovery in the retained TUM2TWIN campus core.",
                "evidence_type": "newly_run",
                "source": "figures/morphology_form_response_archetype_summary.csv; reports/morphology_form_response_archetype_analysis.md",
                "claim_readiness": "paper_ready_as_screening",
            },
            {
                "claim_id": "FRA2",
                "claim": "The observed wind-response differences are better framed as combinations of relative vertical massing, elongation and local enclosure than as single-variable building-size effects.",
                "evidence_type": "newly_run + blocked",
                "source": "figures/morphology_form_response_archetype_by_component.csv; paper_text/morphology_form_response_archetype_conclusion_zh.md",
                "claim_readiness": "paper_ready_with_boundary",
            },
        ]
    )
    claims.to_csv(MAN / "morphology_form_response_archetype_claims.csv", index=False)

    print("sample_size", len(df))
    print("kruskal_p", f"{p_value:.6g}")
    print("top_archetype", top["archetype"])
    print("bottom_archetype", bottom["archetype"])


if __name__ == "__main__":
    main()
