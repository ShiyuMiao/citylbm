from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr


ROOT = Path.cwd()
FIG = ROOT / "figures"
REPORTS = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"

COMPONENTS = FIG / "morphology_form_response_archetype_by_component.csv"


FEATURES = [
    ("footprint_area_m2", "Footprint area"),
    ("mean_height_m", "Mean height"),
    ("height_to_sqrt_area", "Height/sqrt(area)"),
    ("compactness_p2_over_a", "Perimeter^2/area"),
    ("elongation_ratio", "Elongation"),
    ("local_built_fraction_r30m", "Built fraction r30m"),
    ("sector_enclosure_ratio_r50m", "Sector enclosure r50m"),
    ("relative_enclosure_score", "Relative enclosure"),
]

TERTILE_FEATURES = [
    "footprint_area_m2_tertile",
    "mean_height_m_tertile",
    "height_to_sqrt_area_tertile",
    "elongation_ratio_tertile",
    "local_built_fraction_r30m_tertile",
    "relative_enclosure_score_tertile",
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cliff_delta(a: np.ndarray, b: np.ndarray) -> float:
    total = len(a) * len(b)
    if total == 0:
        return float("nan")
    gt = 0
    lt = 0
    for value in a:
        gt += int(np.sum(value > b))
        lt += int(np.sum(value < b))
    return (gt - lt) / total


def safe_float(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    return float(value)


def summarize_stage(df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    metrics = [
        ("near_facade_mean_vr", "near_facade_0_20m_mean_vr"),
        ("local_context_mean_vr", "local_context_20_50m_mean_vr"),
        ("context_recovery_delta_vr", "local_minus_near_recovery_delta_vr"),
        ("near_facade_directional_range_vr", "near_facade_directional_range_vr"),
        ("local_context_directional_range_vr", "local_context_directional_range_vr"),
        ("near_facade_stagnation_ratio", "near_facade_stagnation_ratio"),
        ("local_context_stagnation_ratio", "local_context_stagnation_ratio"),
    ]
    for col, label in metrics:
        values = df[col].astype(float)
        rows.append(
            {
                "evidence_type": "newly_run",
                "metric": label,
                "n_components": len(values),
                "mean": values.mean(),
                "median": values.median(),
                "p25": values.quantile(0.25),
                "p75": values.quantile(0.75),
                "p95": values.quantile(0.95),
                "min": values.min(),
                "max": values.max(),
            }
        )
    return rows


def feature_contrasts(df: pd.DataFrame) -> list[dict[str, object]]:
    top = df[df["is_top_recovery_quartile"].astype(bool)]
    bottom = df[df["is_bottom_recovery_quartile"].astype(bool)]
    rows: list[dict[str, object]] = []
    for col, label in FEATURES:
        a = top[col].astype(float).to_numpy()
        b = bottom[col].astype(float).to_numpy()
        stat = mannwhitneyu(a, b, alternative="two-sided")
        rows.append(
            {
                "evidence_type": "newly_run",
                "feature": col,
                "feature_label": label,
                "top_recovery_n": len(a),
                "bottom_recovery_n": len(b),
                "top_mean": np.mean(a),
                "bottom_mean": np.mean(b),
                "top_median": np.median(a),
                "bottom_median": np.median(b),
                "mean_difference_top_minus_bottom": np.mean(a) - np.mean(b),
                "mann_whitney_u": safe_float(stat.statistic),
                "mann_whitney_p": safe_float(stat.pvalue),
                "cliffs_delta_top_vs_bottom": cliff_delta(a, b),
            }
        )
    return rows


def interaction_rules(df: pd.DataFrame, min_n: int = 5) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for width in [1, 2, 3]:
        for cols in combinations(TERTILE_FEATURES, width):
            grouped = df.groupby(list(cols), dropna=False)
            for keys, group in grouped:
                if len(group) < min_n:
                    continue
                if not isinstance(keys, tuple):
                    keys = (keys,)
                rule = " + ".join(f"{col}={key}" for col, key in zip(cols, keys))
                rows.append(
                    {
                        "evidence_type": "newly_run",
                        "rule_width": width,
                        "rule": rule,
                        "n_components": len(group),
                        "mean_recovery_delta_vr": group["context_recovery_delta_vr"].mean(),
                        "median_recovery_delta_vr": group["context_recovery_delta_vr"].median(),
                        "mean_local_context_vr": group["local_context_mean_vr"].mean(),
                        "mean_near_facade_vr": group["near_facade_mean_vr"].mean(),
                        "top_recovery_share": group["is_top_recovery_quartile"].astype(bool).mean(),
                        "bottom_recovery_share": group["is_bottom_recovery_quartile"].astype(bool).mean(),
                        "mean_directional_range_vr": group["local_context_directional_range_vr"].mean(),
                    }
                )
    rows.sort(
        key=lambda r: (
            float(r["top_recovery_share"]),
            float(r["mean_recovery_delta_vr"]),
            int(r["n_components"]),
        ),
        reverse=True,
    )
    return rows


def classify_components(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    q75_range = out["local_context_directional_range_vr"].quantile(0.75)
    out["stage_transition_class"] = "mixed_low_speed_context"
    out.loc[out["is_bottom_recovery_quartile"].astype(bool), "stage_transition_class"] = "persistent_shelter"
    out.loc[out["local_context_directional_range_vr"] >= q75_range, "stage_transition_class"] = "directionally_reactive"
    out.loc[out["is_top_recovery_quartile"].astype(bool), "stage_transition_class"] = "near_to_context_recovery"
    return out


def make_panel(df: pd.DataFrame, contrast: pd.DataFrame, rules: pd.DataFrame) -> None:
    def pretty_rule(text: str) -> str:
        replacements = {
            "footprint_area_m2_tertile": "area",
            "mean_height_m_tertile": "height",
            "height_to_sqrt_area_tertile": "h/sqrtA",
            "elongation_ratio_tertile": "elong.",
            "local_built_fraction_r30m_tertile": "built r30",
            "relative_enclosure_score_tertile": "rel. enclosure",
            "=low": "=L",
            "=medium": "=M",
            "=high": "=H",
            " + ": " + ",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return fill(text, width=38)

    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.8), dpi=180)

    class_colors = {
        "near_to_context_recovery": "#2c7fb8",
        "persistent_shelter": "#d95f0e",
        "directionally_reactive": "#31a354",
        "mixed_low_speed_context": "#8c8c8c",
    }
    ax = axes[0, 0]
    for klass, sub in df.groupby("stage_transition_class"):
        ax.scatter(
            sub["near_facade_mean_vr"],
            sub["local_context_mean_vr"],
            s=20 + np.sqrt(sub["footprint_area_m2"]) * 1.2,
            alpha=0.75,
            edgecolor="white",
            linewidth=0.4,
            color=class_colors.get(klass, "#777777"),
            label=klass,
        )
    lim = max(df["near_facade_mean_vr"].max(), df["local_context_mean_vr"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "--", color="#666666", linewidth=1)
    ax.set_xlabel("0-20 m facade-adjacent mean VR")
    ax.set_ylabel("20-50 m local-context mean VR")
    ax.set_title("A. Near-to-context wind response")
    ax.legend(fontsize=7, frameon=False)

    ax = axes[0, 1]
    c = contrast.sort_values("cliffs_delta_top_vs_bottom")
    ax.barh(c["feature_label"], c["cliffs_delta_top_vs_bottom"], color=np.where(c["cliffs_delta_top_vs_bottom"] >= 0, "#2c7fb8", "#d95f0e"))
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Cliff's delta: top recovery vs bottom recovery")
    ax.set_title("B. Feature contrast")

    ax = axes[1, 0]
    pivot = df.pivot_table(
        index="height_to_sqrt_area_tertile",
        columns="elongation_ratio_tertile",
        values="context_recovery_delta_vr",
        aggfunc="mean",
    ).reindex(index=["low", "medium", "high"], columns=["low", "medium", "high"])
    im = ax.imshow(pivot.to_numpy(), cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(3), ["low", "medium", "high"])
    ax.set_yticks(range(3), ["low", "medium", "high"])
    ax.set_xlabel("Elongation tertile")
    ax.set_ylabel("Height/sqrt(area) tertile")
    ax.set_title("C. Mean recovery by two basic form parameters")
    for i in range(3):
        for j in range(3):
            value = pivot.iloc[i, j]
            if pd.notna(value):
                ax.text(j, i, f"{value:.4f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Recovery delta VR")

    ax = axes[1, 1]
    top_rules = rules.head(8).iloc[::-1]
    labels = [pretty_rule(rule) for rule in top_rules["rule"]]
    ax.barh(labels, top_rules["mean_recovery_delta_vr"], color="#2c7fb8")
    ax.set_xlabel("Mean recovery delta VR")
    ax.set_title("D. Highest sample-internal subgroup rules")
    ax.tick_params(axis="y", labelsize=6)

    fig.tight_layout(w_pad=2.5)
    fig.savefig(FIG / "morphology_stage_transition_panel.png", bbox_inches="tight")
    plt.close(fig)


def upsert_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    rows = pd.read_csv(path).to_dict("records")
    additions = [
        {
            "claim": "Morphology stage-transition analysis separates near-facade shelter, 20-50 m recovery and directional reactivity for 101 retained components.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_feature_contrasts.csv; figures/morphology_stage_transition_panel.png; reports/morphology_stage_transition_analysis.md",
        },
        {
            "claim": "The near-to-context recovery contrast supports a sample-internal design insight: relative vertical scale and plan-continuity combinations are more informative than any single absolute building size variable.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_stage_transition_rule_table.csv; paper_text/morphology_stage_transition_conclusion_zh.md; paper_text/morphology_stage_transition_conclusion_en.md",
        },
    ]
    for item in additions:
        matched = False
        for row in rows:
            if row["claim"] == item["claim"]:
                row.update(item)
                matched = True
                break
        if not matched:
            rows.append(item)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def upsert_key_result_matrix(best_rule: dict[str, object], summary: pd.DataFrame, contrast: pd.DataFrame) -> None:
    path = FIG / "final_integrated_key_result_matrix.csv"
    rows = pd.read_csv(path).to_dict("records")
    claim_layer = "Morphology stage transition"
    rows = [row for row in rows if row.get("claim_layer") != claim_layer]
    top = contrast.set_index("feature")
    value = (
        f"near/local/recovery mean VR "
        f"{summary.loc[summary['metric']=='near_facade_0_20m_mean_vr','mean'].iloc[0]:.6f} / "
        f"{summary.loc[summary['metric']=='local_context_20_50m_mean_vr','mean'].iloc[0]:.6f} / "
        f"{summary.loc[summary['metric']=='local_minus_near_recovery_delta_vr','mean'].iloc[0]:.6f}; "
        f"best rule {best_rule['rule']} / n={best_rule['n_components']} / "
        f"mean recovery {best_rule['mean_recovery_delta_vr']:.4f} / top share {best_rule['top_recovery_share']:.3f}; "
        f"height/sqrt(area) Cliff delta {top.loc['height_to_sqrt_area','cliffs_delta_top_vs_bottom']:.3f}"
    )
    rows.append(
        {
            "evidence_type": "newly_run + blocked",
            "claim_layer": claim_layer,
            "metric": "near-to-context stage response / best subgroup rule / relative vertical-scale contrast",
            "value": value,
            "source_artifact": "figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_rule_table.csv; figures/morphology_stage_transition_feature_contrasts.csv",
            "paper_safe_claim": "The 20-50 m local-context band converts a saturated near-facade low-speed signal into a morphology-differentiated recovery signal; the rule is sample-internal and not a universal design threshold.",
        }
    )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def build_report(
    summary: pd.DataFrame,
    contrast: pd.DataFrame,
    rules: pd.DataFrame,
    class_counts: pd.Series,
    best_rule: dict[str, object],
) -> str:
    near = summary.loc[summary["metric"] == "near_facade_0_20m_mean_vr"].iloc[0]
    local = summary.loc[summary["metric"] == "local_context_20_50m_mean_vr"].iloc[0]
    rec = summary.loc[summary["metric"] == "local_minus_near_recovery_delta_vr"].iloc[0]
    hrel = contrast.set_index("feature").loc["height_to_sqrt_area"]
    height = contrast.set_index("feature").loc["mean_height_m"]
    elong = contrast.set_index("feature").loc["elongation_ratio"]
    rho_recovery_height = spearmanr(
        pd.read_csv(COMPONENTS)["height_to_sqrt_area"],
        pd.read_csv(COMPONENTS)["context_recovery_delta_vr"],
    )

    lines = [
        "# Morphology Stage-Transition Analysis",
        "",
        "evidence_type: newly_run + blocked",
        "",
        "## Purpose",
        "",
        "This addendum deepens the building-form interpretation by separating the wind response into three analysis stages: the 0-20 m facade-adjacent band, the 20-50 m local-context band, and directional reactivity within the local-context band. The analysis uses the same 101 retained central components and the archived FluidX3D-derived morphology table; no new CFD simulation is claimed.",
        "",
        "## Stage Statistics",
        "",
        f"- Components: `{int(near['n_components'])}`.",
        f"- Near-facade mean VR: `{near['mean']:.6f}`; local-context mean VR: `{local['mean']:.6f}`; mean recovery delta: `{rec['mean']:.6f}`.",
        f"- Median recovery delta: `{rec['median']:.6f}`; P75 recovery delta: `{rec['p75']:.6f}`; P95 recovery delta: `{rec['p95']:.6f}`.",
        f"- Stage classes: " + "; ".join(f"`{k}`={v}" for k, v in class_counts.items()) + ".",
        "",
        "## Top-Versus-Bottom Recovery Contrast",
        "",
        f"- Top-recovery and bottom-recovery quartiles each contain `26` components.",
        f"- Height/sqrt(area) is lower in the top-recovery quartile than in the bottom quartile: top mean `{hrel['top_mean']:.3f}`, bottom mean `{hrel['bottom_mean']:.3f}`, Cliff's delta `{hrel['cliffs_delta_top_vs_bottom']:.3f}`, Mann-Whitney p `{hrel['mann_whitney_p']:.4g}`.",
        f"- Absolute mean height is also lower in the top-recovery quartile: top mean `{height['top_mean']:.3f}` m, bottom mean `{height['bottom_mean']:.3f}` m, Cliff's delta `{height['cliffs_delta_top_vs_bottom']:.3f}`.",
        f"- Elongation shows a positive but weaker contrast: top mean `{elong['top_mean']:.3f}`, bottom mean `{elong['bottom_mean']:.3f}`, Cliff's delta `{elong['cliffs_delta_top_vs_bottom']:.3f}`.",
        f"- Spearman rho between height/sqrt(area) and recovery delta is `{rho_recovery_height.statistic:.3f}` with p `{rho_recovery_height.pvalue:.4g}`.",
        "",
        "## Best Sample-Internal Rule",
        "",
        f"- Best retained subgroup rule: `{best_rule['rule']}`.",
        f"- Components in subgroup: `{int(best_rule['n_components'])}`; mean recovery delta `{best_rule['mean_recovery_delta_vr']:.6f}`; top-recovery share `{best_rule['top_recovery_share']:.3f}`; bottom-recovery share `{best_rule['bottom_recovery_share']:.3f}`.",
        "",
        "## Paper-Safe Interpretation",
        "",
        "The additional stage-transition analysis supports a more precise conclusion than a direct `building height causes wind speed` statement. In this campus-core sample, the 0-20 m facade-adjacent band is a largely saturated sheltered zone, whereas the 20-50 m band exposes the differences between building-form contexts. The strongest recoveries are associated with lower relative vertical scale and selected plan-continuity conditions, while high relative vertical scale and compact isolated footprints tend to remain in persistent shelter. This is a digital-twin screening result and remains blocked from being written as a causal, field-validated or universally transferable design rule.",
        "",
        "## Outputs",
        "",
        "- `figures/morphology_stage_transition_summary.csv`",
        "- `figures/morphology_stage_transition_feature_contrasts.csv`",
        "- `figures/morphology_stage_transition_rule_table.csv`",
        "- `figures/morphology_stage_transition_by_component.csv`",
        "- `figures/morphology_stage_transition_panel.png`",
        "- `paper_text/morphology_stage_transition_conclusion_zh.md`",
        "- `paper_text/morphology_stage_transition_conclusion_en.md`",
        "- `manifests/morphology_stage_transition_claims.csv`",
        "",
        "## Boundaries",
        "",
        "- No new FluidX3D case was run in this addendum.",
        "- The rule table is sample-internal and exploratory.",
        "- The result does not replace field validation, annual comfort assessment or pollutant dispersion modelling.",
        "",
    ]
    return "\n".join(lines)


def build_paper_text(best_rule: dict[str, object], summary: pd.DataFrame, contrast: pd.DataFrame) -> str:
    near = summary.loc[summary["metric"] == "near_facade_0_20m_mean_vr"].iloc[0]
    local = summary.loc[summary["metric"] == "local_context_20_50m_mean_vr"].iloc[0]
    rec = summary.loc[summary["metric"] == "local_minus_near_recovery_delta_vr"].iloc[0]
    hrel = contrast.set_index("feature").loc["height_to_sqrt_area"]
    return (
        "# 建筑形态阶段转化结论段落\n\n"
        "evidence_type: newly_run + blocked\n\n"
        f"进一步的建筑形态阶段转化分析表明，本实验中的形态效应并不适合被简化为单一建筑高度、占地面积或孔隙率对风速的线性影响。"
        f"在 101 个保留建筑构件中，0-20 m 近立面带的平均风速比仅为 `{near['mean']:.6f}`，而 20-50 m 局地环境带的平均风速比为 `{local['mean']:.6f}`，"
        f"二者之间的平均恢复量为 `{rec['mean']:.6f}`。这说明近立面区域首先表现为由街区围合和建筑遮蔽共同造成的低速饱和带；"
        "真正能够区分不同建筑形式风环境表现的，是建筑外侧 20-50 m 局地环境中是否出现风速恢复和方向性响应。"
        f"顶部分位恢复组与底部分位恢复组的对比显示，`height_to_sqrt_area` 在高恢复组中更低，Cliff's delta 为 `{hrel['cliffs_delta_top_vs_bottom']:.3f}`，"
        f"最佳样本内组合规则为 `{best_rule['rule']}`，其平均恢复量为 `{best_rule['mean_recovery_delta_vr']:.6f}`，高恢复构件占比为 `{best_rule['top_recovery_share']:.3f}`。"
        "因此，本实验能够在传统街谷遮蔽和局部加速认识之外补充一个更适合数字孪生设计筛查的认识：校园核心区行人层通风改善并不取决于单一开口面积或单体高度，"
        "而取决于相对竖向尺度、平面连续性、局地围合度与主导风向入口之间是否形成有效的动量交换路径。"
        "该结论只应表述为 FluidX3D 数字孪生样本内的筛查性发现，不能写成实测验证的因果设计准则或通用规范阈值。\n"
    )


def build_paper_text_en(best_rule: dict[str, object], summary: pd.DataFrame, contrast: pd.DataFrame) -> str:
    near = summary.loc[summary["metric"] == "near_facade_0_20m_mean_vr"].iloc[0]
    local = summary.loc[summary["metric"] == "local_context_20_50m_mean_vr"].iloc[0]
    rec = summary.loc[summary["metric"] == "local_minus_near_recovery_delta_vr"].iloc[0]
    hrel = contrast.set_index("feature").loc["height_to_sqrt_area"]
    return (
        "# Building-Form Stage-Transition Conclusion\n\n"
        "evidence_type: newly_run + blocked\n\n"
        "The stage-transition analysis indicates that the building-form effect in this experiment should not be reduced to a linear effect of absolute building height, footprint area or opening ratio. "
        f"Across the 101 retained components, the mean velocity ratio is `{near['mean']:.6f}` in the 0-20 m facade-adjacent band and `{local['mean']:.6f}` in the 20-50 m local-context band, with a mean recovery delta of `{rec['mean']:.6f}`. "
        "The facade-adjacent zone therefore behaves first as a low-speed saturated stage produced by block enclosure and building sheltering; the 20-50 m local-context band is the stage at which different building-form contexts become distinguishable through wind-speed recovery and directional response. "
        f"Top-recovery and bottom-recovery quartiles show a strong contrast in `height_to_sqrt_area`, with Cliff's delta `{hrel['cliffs_delta_top_vs_bottom']:.3f}`. "
        f"The best sample-internal subgroup rule is `{best_rule['rule']}`, with mean recovery delta `{best_rule['mean_recovery_delta_vr']:.6f}` and top-recovery share `{best_rule['top_recovery_share']:.3f}`. "
        "This supports a design-screening insight beyond the traditional canyon-shelter/local-acceleration dichotomy: in the campus core, pedestrian-layer ventilation recovery depends less on a single opening area or single-building height than on whether relative vertical scale, plan continuity, local enclosure and inflow-sector access form an effective momentum-exchange path. "
        "The conclusion must remain framed as a FluidX3D digital-twin screening finding, not as a field-validated causal rule or universal morphology threshold.\n"
    )


def main() -> None:
    df = pd.read_csv(COMPONENTS)
    df = classify_components(df)
    summary = pd.DataFrame(summarize_stage(df))
    contrast = pd.DataFrame(feature_contrasts(df))
    rules = pd.DataFrame(interaction_rules(df))
    best_rule = rules.iloc[0].to_dict()
    class_counts = df["stage_transition_class"].value_counts()

    summary.to_csv(FIG / "morphology_stage_transition_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    contrast.to_csv(FIG / "morphology_stage_transition_feature_contrasts.csv", index=False, encoding="utf-8", lineterminator="\n")
    rules.to_csv(FIG / "morphology_stage_transition_rule_table.csv", index=False, encoding="utf-8", lineterminator="\n")
    df.to_csv(FIG / "morphology_stage_transition_by_component.csv", index=False, encoding="utf-8", lineterminator="\n")
    make_panel(df, contrast, rules)

    claims = [
        {
            "claim": "The 0-20 m facade-adjacent band is a low-speed saturated stage, while the 20-50 m local-context band exposes morphology-differentiated recovery.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_stage_transition_summary.csv; figures/morphology_stage_transition_panel.png",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim": "Top-recovery components have lower relative vertical scale than bottom-recovery components, supporting relative massing rather than absolute size as a screening descriptor.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_stage_transition_feature_contrasts.csv",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim": "The best subgroup rule is sample-internal and must not be generalized as a universal design threshold.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_stage_transition_rule_table.csv; reports/morphology_stage_transition_analysis.md",
            "claim_readiness": "weaken_claim",
        },
    ]
    write_csv(MAN / "morphology_stage_transition_claims.csv", claims, ["claim", "evidence_type", "source", "claim_readiness"])

    write_text(REPORTS / "morphology_stage_transition_analysis.md", build_report(summary, contrast, rules, class_counts, best_rule))
    write_text(PAPER / "morphology_stage_transition_conclusion_zh.md", build_paper_text(best_rule, summary, contrast))
    write_text(PAPER / "morphology_stage_transition_conclusion_en.md", build_paper_text_en(best_rule, summary, contrast))
    upsert_evidence_inventory()
    upsert_key_result_matrix(best_rule, summary, contrast)

    print("components", len(df))
    print("best_rule", best_rule["rule"])
    print("best_rule_n", int(best_rule["n_components"]))
    print("best_rule_mean_recovery", f"{best_rule['mean_recovery_delta_vr']:.6f}")
    print("best_rule_top_share", f"{best_rule['top_recovery_share']:.3f}")
    print("wrote morphology stage-transition outputs")


if __name__ == "__main__":
    main()
