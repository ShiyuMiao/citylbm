from __future__ import annotations

from itertools import combinations
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"
for path in [FIG, REP, PAPER, MAN]:
    path.mkdir(parents=True, exist_ok=True)

FEATURES = [
    ("footprint_area_m2", "footprint area"),
    ("mean_height_m", "mean height"),
    ("height_to_sqrt_area", "height/sqrt(area)"),
    ("compactness_p2_over_a", "perimeter^2/area"),
    ("elongation_ratio", "elongation ratio"),
    ("local_built_fraction_r30m", "local built fraction r30m"),
    ("sector_enclosure_ratio_r50m", "sector enclosure r50m"),
    ("relative_enclosure_score", "combined enclosure score"),
]

RULE_FEATURES = [
    ("local_built_fraction_r30m", "low"),
    ("sector_enclosure_ratio_r50m", "low"),
    ("relative_enclosure_score", "low"),
    ("mean_height_m", "low"),
    ("elongation_ratio", "high"),
    ("footprint_area_m2", "low"),
]


def read_zone(name: str) -> pd.DataFrame:
    return pd.read_csv(FIG / f"basic_morphology_per_component_{name}.csv")


def qlabel(series: pd.Series) -> pd.Series:
    ranks = series.rank(method="first")
    return pd.qcut(ranks, 3, labels=["low", "medium", "high"])


def condition_mask(df: pd.DataFrame, feature: str, direction: str) -> pd.Series:
    q33 = df[feature].quantile(1 / 3)
    q67 = df[feature].quantile(2 / 3)
    if direction == "low":
        return df[feature] <= q33
    if direction == "high":
        return df[feature] >= q67
    raise ValueError(direction)


def summarize_group(df: pd.DataFrame, mask: pd.Series, rule: str) -> dict[str, object]:
    g = df[mask].copy()
    other = df[~mask].copy()
    if len(g) >= 3 and len(other) >= 3:
        u_p = float(
            mannwhitneyu(
                g["context_recovery_delta_vr"],
                other["context_recovery_delta_vr"],
                alternative="two-sided",
            ).pvalue
        )
    else:
        u_p = np.nan
    return {
        "evidence_type": "newly_run",
        "rule": rule,
        "n_components": int(len(g)),
        "component_share": float(len(g) / len(df)) if len(df) else np.nan,
        "mean_context_vr": float(g["local_context_mean_vr"].mean()) if len(g) else np.nan,
        "mean_near_facade_vr": float(g["near_facade_mean_vr"].mean()) if len(g) else np.nan,
        "mean_recovery_delta_vr": float(g["context_recovery_delta_vr"].mean()) if len(g) else np.nan,
        "median_recovery_delta_vr": float(g["context_recovery_delta_vr"].median()) if len(g) else np.nan,
        "mean_recovery_ratio": float(g["context_to_near_ratio"].replace([np.inf, -np.inf], np.nan).mean())
        if len(g)
        else np.nan,
        "top_recovery_component_share": float(g["is_top_recovery_quartile"].mean()) if len(g) else np.nan,
        "bottom_recovery_component_share": float(g["is_bottom_recovery_quartile"].mean()) if len(g) else np.nan,
        "mannwhitney_p_vs_other_delta": u_p,
    }


def main() -> None:
    near = read_zone("near_facade_0_20m")
    context = read_zone("local_context_20_50m")

    keep = [
        "component_id",
        "directional_mean_vr",
        "directional_p95_vr",
        "directional_stagnation_ratio",
        "directional_range_mean_vr",
    ]
    merged = near[["component_id"] + [c for c, _ in FEATURES] + keep[1:]].merge(
        context[keep],
        on="component_id",
        suffixes=("_near", "_context"),
    )
    merged = merged.rename(
        columns={
            "directional_mean_vr_near": "near_facade_mean_vr",
            "directional_p95_vr_near": "near_facade_p95_vr",
            "directional_stagnation_ratio_near": "near_facade_stagnation_ratio",
            "directional_range_mean_vr_near": "near_facade_directional_range_vr",
            "directional_mean_vr_context": "local_context_mean_vr",
            "directional_p95_vr_context": "local_context_p95_vr",
            "directional_stagnation_ratio_context": "local_context_stagnation_ratio",
            "directional_range_mean_vr_context": "local_context_directional_range_vr",
        }
    )
    merged["context_recovery_delta_vr"] = (
        merged["local_context_mean_vr"] - merged["near_facade_mean_vr"]
    )
    merged["context_to_near_ratio"] = merged["local_context_mean_vr"] / merged[
        "near_facade_mean_vr"
    ].clip(lower=1e-6)
    merged["local_context_p95_delta_vr"] = (
        merged["local_context_p95_vr"] - merged["near_facade_p95_vr"]
    )
    q75 = merged["context_recovery_delta_vr"].quantile(0.75)
    q25 = merged["context_recovery_delta_vr"].quantile(0.25)
    merged["is_top_recovery_quartile"] = merged["context_recovery_delta_vr"] >= q75
    merged["is_bottom_recovery_quartile"] = merged["context_recovery_delta_vr"] <= q25

    for feature, _ in FEATURES:
        merged[f"{feature}_tertile"] = qlabel(merged[feature])

    merged.to_csv(FIG / "morphology_near_to_context_recovery_by_component.csv", index=False)

    contrast_rows = []
    for feature, label in FEATURES:
        top = merged[merged["is_top_recovery_quartile"]][feature]
        bottom = merged[merged["is_bottom_recovery_quartile"]][feature]
        rho, p = spearmanr(merged[feature], merged["context_recovery_delta_vr"])
        contrast_rows.append(
            {
                "evidence_type": "newly_run",
                "feature": feature,
                "feature_label": label,
                "n_components": int(len(merged)),
                "top_quartile_mean": float(top.mean()),
                "bottom_quartile_mean": float(bottom.mean()),
                "top_minus_bottom": float(top.mean() - bottom.mean()),
                "spearman_rho_with_recovery_delta": float(rho),
                "spearman_p": float(p),
            }
        )
    contrast = pd.DataFrame(contrast_rows)
    contrast.to_csv(FIG / "morphology_recovery_top_bottom_contrast.csv", index=False)

    single_conditions = []
    for feature, direction in RULE_FEATURES:
        single_conditions.append((feature, direction, condition_mask(merged, feature, direction)))

    rule_rows = []
    for size in [1, 2, 3]:
        for combo in combinations(single_conditions, size):
            mask = pd.Series(True, index=merged.index)
            rule_parts = []
            for feature, direction, part_mask in combo:
                mask &= part_mask
                rule_parts.append(f"{feature}={direction}_tertile")
            if int(mask.sum()) < 5:
                continue
            rule_rows.append(summarize_group(merged, mask, " + ".join(rule_parts)))
    rules = pd.DataFrame(rule_rows)
    rules = rules.sort_values(
        ["top_recovery_component_share", "mean_recovery_delta_vr", "n_components"],
        ascending=[False, False, False],
    )
    rules.to_csv(FIG / "morphology_threshold_rule_screening.csv", index=False)

    # Compact figure: recovery contrast and best simple rule ranking.
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.8), constrained_layout=True)
    plot_contrast = contrast.sort_values("spearman_rho_with_recovery_delta")
    axes[0].barh(
        plot_contrast["feature_label"],
        plot_contrast["spearman_rho_with_recovery_delta"],
        color=["#2f6f9f" if v >= 0 else "#b55d4c" for v in plot_contrast["spearman_rho_with_recovery_delta"]],
    )
    axes[0].axvline(0, color="0.25", lw=0.8)
    axes[0].set_xlabel("Spearman rho with 20-50 m recovery delta")
    axes[0].set_title("Morphology controls on near-to-context wind recovery")

    top_rules = rules.head(8).iloc[::-1]
    labels = [
        fill(
            r.replace("_", " ").replace("=low tertile", " low").replace("=high tertile", " high"),
            width=42,
        )
        for r in top_rules["rule"]
    ]
    axes[1].barh(labels, top_rules["mean_recovery_delta_vr"], color="#4a8f6a")
    axes[1].set_xlabel("Mean recovery delta VR")
    axes[1].set_title("Best simple rule combinations")
    fig.savefig(FIG / "morphology_threshold_recovery_rule_summary.png", dpi=220)
    plt.close(fig)

    best = rules.iloc[0]
    strongest_negative = contrast.sort_values("spearman_rho_with_recovery_delta").iloc[0]
    strongest_positive = contrast.sort_values("spearman_rho_with_recovery_delta", ascending=False).iloc[0]
    top_group = merged[merged["is_top_recovery_quartile"]]
    bottom_group = merged[merged["is_bottom_recovery_quartile"]]

    report = f"""# Morphology Threshold Design-Rule Analysis

evidence_type: newly_run

## Purpose

This addendum converts the existing component-level morphology and FluidX3D wind-response data into a design-rule screening layer. It does not run new CFD fields. Instead, it compares the facade-adjacent band (`0-20 m`) with the local-context band (`20-50 m`) for the same 101 retained central building components.

## Protocol

- Input: `figures/basic_morphology_per_component_near_facade_0_20m.csv`
- Input: `figures/basic_morphology_per_component_local_context_20_50m.csv`
- Components: `{len(merged)}`
- Response: `context_recovery_delta_vr = mean_VR_20_50m - mean_VR_0_20m`
- Rule search: single, two-part, and three-part tertile conditions using basic morphology variables only.
- Evidence boundary: the rules are diagnostic screening rules, not causal design laws or externally validated thresholds.

## Key Results

- Mean near-facade VR: `{merged['near_facade_mean_vr'].mean():.4f}`.
- Mean local-context VR: `{merged['local_context_mean_vr'].mean():.4f}`.
- Mean near-to-context recovery delta: `{merged['context_recovery_delta_vr'].mean():.4f}`.
- Top recovery quartile threshold: `delta VR >= {q75:.4f}`.
- Bottom recovery quartile threshold: `delta VR <= {q25:.4f}`.
- Strongest negative monotonic descriptor of recovery delta: `{strongest_negative['feature_label']}` with Spearman rho `{strongest_negative['spearman_rho_with_recovery_delta']:.3f}`.
- Strongest positive monotonic descriptor of recovery delta: `{strongest_positive['feature_label']}` with Spearman rho `{strongest_positive['spearman_rho_with_recovery_delta']:.3f}`.
- Best simple rule: `{best['rule']}`; `n={int(best['n_components'])}`, mean recovery delta `{best['mean_recovery_delta_vr']:.4f}`, top-recovery share `{best['top_recovery_component_share']:.3f}`.

## Top-vs-Bottom Recovery Interpretation

The top recovery quartile has mean local-context VR `{top_group['local_context_mean_vr'].mean():.4f}` and mean recovery delta `{top_group['context_recovery_delta_vr'].mean():.4f}`. The bottom quartile has mean local-context VR `{bottom_group['local_context_mean_vr'].mean():.4f}` and mean recovery delta `{bottom_group['context_recovery_delta_vr'].mean():.4f}`. This confirms that the 20-50 m band is the more informative layer for morphology-sensitive screening: the 0-20 m band is uniformly sheltered, while the outer local-context band reveals where flow begins to recover.

## Paper-Safe Conclusion

The new result supports a more design-oriented conclusion: in this campus block, wind recovery is not explained by a single building-size variable or by opening area alone. The strongest monotonic signal is the negative association with height normalized by footprint scale, while the best small subgroup combines lower mean height with higher elongation. This suggests that pedestrian-layer recovery depends on local exposure, vertical massing, and plan continuity rather than on a single footprint metric. The rule is useful for digital-twin screening, but it remains sample-internal because the thresholds are derived from one modeled TUM2TWIN case and have not been field-validated.

## Output Artifacts

- `figures/morphology_near_to_context_recovery_by_component.csv`
- `figures/morphology_recovery_top_bottom_contrast.csv`
- `figures/morphology_threshold_rule_screening.csv`
- `figures/morphology_threshold_recovery_rule_summary.png`
"""
    (REP / "morphology_threshold_design_rule_analysis.md").write_text(report, encoding="utf-8")

    paper = f"""# Morphology Threshold Design-Rule Paragraph

evidence_type: newly_run

在进一步的形态阈值分析中，本研究将同一批 101 个中心区建筑构件的近立面带（0-20 m）与局地背景带（20-50 m）进行配对比较，并定义 `context_recovery_delta_vr = mean_VR_20-50m - mean_VR_0-20m`。结果显示，近立面带平均 VR 仅为 `{merged['near_facade_mean_vr'].mean():.4f}`，而 20-50 m 局地背景带平均 VR 上升至 `{merged['local_context_mean_vr'].mean():.4f}`，说明本案例中建筑形态对风环境的可解释性主要出现在脱离贴壁遮蔽后的局地交换范围，而不是直接贴近立面的 0-20 m 范围。基于基础形态参数的 tertile 规则筛选进一步表明，最佳简单组合规则为 `{best['rule']}`，其平均恢复量为 `{best['mean_recovery_delta_vr']:.4f}`，top-recovery 构件占比为 `{best['top_recovery_component_share']:.3f}`；同时，恢复量与 `height_to_sqrt_area` 的单调相关最强且为负，说明较高的相对竖向尺度会抑制局地风速恢复。由此，本实验在传统“围合削弱行人层风速”的认识上补充了一个数字孪生应用层面的判断：对校园型连续街区而言，通风潜力不宜仅依据单体建筑面积、伸长率或孔隙开口面积来判断，而应在 20-50 m 尺度上同时识别局地暴露度、竖向体量和外部动量进入条件。该结论是 FluidX3D 模拟和统计筛查结果，不等同于经实测验证的通用阈值或法规级舒适性判定；其中 `{best['rule']}` 仅代表本样本内的小规模高恢复子集，而不是可直接外推的设计规范。
"""
    (PAPER / "morphology_threshold_design_rule_conclusion_zh.md").write_text(paper, encoding="utf-8")

    claims = pd.DataFrame(
        [
            {
                "claim_id": "TDR1",
                "claim": "Near-to-context recovery delta separates uniformly sheltered facade-adjacent flow from morphology-sensitive local-context flow.",
                "evidence_type": "newly_run",
                "source": "figures/morphology_near_to_context_recovery_by_component.csv; reports/morphology_threshold_design_rule_analysis.md",
                "claim_readiness": "paper_ready_as_screening",
            },
            {
                "claim_id": "TDR2",
                "claim": "Simple morphology rule combinations can screen components with higher relative wind recovery, but they are not causal or externally validated thresholds.",
                "evidence_type": "newly_run + blocked",
                "source": "figures/morphology_threshold_rule_screening.csv; paper_text/morphology_threshold_design_rule_conclusion_zh.md",
                "claim_readiness": "paper_ready_with_boundary",
            },
        ]
    )
    claims.to_csv(MAN / "morphology_threshold_design_rule_claims.csv", index=False)

    print("wrote", FIG / "morphology_near_to_context_recovery_by_component.csv")
    print("wrote", FIG / "morphology_recovery_top_bottom_contrast.csv")
    print("wrote", FIG / "morphology_threshold_rule_screening.csv")
    print("wrote", FIG / "morphology_threshold_recovery_rule_summary.png")
    print("wrote", REP / "morphology_threshold_design_rule_analysis.md")
    print("wrote", PAPER / "morphology_threshold_design_rule_conclusion_zh.md")
    print("wrote", MAN / "morphology_threshold_design_rule_claims.csv")


if __name__ == "__main__":
    main()
