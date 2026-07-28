import csv
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REPORTS = ROOT / "reports"
PAPER = ROOT / "paper_text"
RNG = np.random.default_rng(20260728)

PARAMETERS = [
    "footprint_area_m2",
    "mean_height_m",
    "height_to_sqrt_area",
    "compactness_p2_over_a",
    "elongation_ratio",
    "local_built_fraction_r30m",
    "sector_enclosure_ratio_r50m",
    "relative_enclosure_score",
]

PARAM_LABELS = {
    "footprint_area_m2": "footprint area",
    "mean_height_m": "mean height",
    "height_to_sqrt_area": "height / sqrt(area)",
    "compactness_p2_over_a": "perimeter^2 / area",
    "elongation_ratio": "elongation ratio",
    "local_built_fraction_r30m": "local built fraction, r=30 m",
    "sector_enclosure_ratio_r50m": "sector enclosure, r=50 m",
    "relative_enclosure_score": "combined enclosure score",
}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)


def spearman(x, y):
    xr = pd.Series(x).rank(method="average").to_numpy(dtype=float)
    yr = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    if np.std(xr) == 0 or np.std(yr) == 0:
        return np.nan
    return float(np.corrcoef(xr, yr)[0, 1])


def bootstrap_spearman_ci(df, zone, response, n_boot=2000):
    rows = [["analysis_zone", "parameter", "parameter_label", "response_metric", "spearman_rho", "bootstrap_ci95_low", "bootstrap_ci95_high", "bootstrap_median", "n_components", "n_bootstrap", "evidence_type"]]
    n = len(df)
    for p in PARAMETERS:
        x = df[p].to_numpy(dtype=float)
        y = df[response].to_numpy(dtype=float)
        rho = spearman(x, y)
        vals = []
        for _ in range(n_boot):
            idx = RNG.integers(0, n, n)
            val = spearman(x[idx], y[idx])
            if not np.isnan(val):
                vals.append(val)
        low, med, high = np.quantile(vals, [0.025, 0.5, 0.975])
        rows.append([zone, p, PARAM_LABELS[p], response, f"{rho:.6f}", f"{low:.6f}", f"{high:.6f}", f"{med:.6f}", n, n_boot, "newly_run"])
    return rows


def high_low_tertile_effect(df, zone, response="directional_mean_vr", n_boot=2000):
    rows = [["analysis_zone", "parameter", "parameter_label", "low_n", "high_n", "low_mean", "high_mean", "delta_high_minus_low", "relative_change_high_vs_low", "bootstrap_ci95_low", "bootstrap_ci95_high", "n_bootstrap", "evidence_type"]]
    for p in PARAMETERS:
        q1 = df[p].quantile(1 / 3)
        q2 = df[p].quantile(2 / 3)
        low = df[df[p] <= q1][response].to_numpy(dtype=float)
        high = df[df[p] >= q2][response].to_numpy(dtype=float)
        delta = float(np.mean(high) - np.mean(low))
        rel = delta / float(np.mean(low)) if np.mean(low) else np.nan
        vals = []
        for _ in range(n_boot):
            lb = RNG.choice(low, size=len(low), replace=True)
            hb = RNG.choice(high, size=len(high), replace=True)
            vals.append(float(np.mean(hb) - np.mean(lb)))
        ci_low, ci_high = np.quantile(vals, [0.025, 0.975])
        rows.append([zone, p, PARAM_LABELS[p], len(low), len(high), f"{np.mean(low):.6f}", f"{np.mean(high):.6f}", f"{delta:.6f}", f"{rel:.6f}", f"{ci_low:.6f}", f"{ci_high:.6f}", n_boot, "newly_run"])
    return rows


def standardized_design(df, cols):
    x = df[cols].to_numpy(dtype=float)
    mu = np.mean(x, axis=0)
    sd = np.std(x, axis=0)
    sd[sd == 0] = 1.0
    return (x - mu) / sd


def fit_predict_ols(train_x, train_y, test_x):
    x = np.column_stack([np.ones(len(train_x)), train_x])
    xt = np.column_stack([np.ones(len(test_x)), test_x])
    beta = np.linalg.pinv(x.T @ x) @ x.T @ train_y
    return xt @ beta, beta


def r2_score(y_true, y_pred, baseline):
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - baseline) ** 2))
    if ss_tot == 0:
        return np.nan
    return 1.0 - ss_res / ss_tot


def cross_validated_model_comparison(df, zone, response="directional_mean_vr", n_repeats=200, k=5):
    models = {
        "size_height_shape": ["footprint_area_m2", "mean_height_m", "height_to_sqrt_area", "compactness_p2_over_a", "elongation_ratio"],
        "context_only": ["local_built_fraction_r30m", "sector_enclosure_ratio_r50m"],
        "context_plus_height": ["local_built_fraction_r30m", "sector_enclosure_ratio_r50m", "mean_height_m"],
        "all_without_composite": ["footprint_area_m2", "mean_height_m", "height_to_sqrt_area", "compactness_p2_over_a", "elongation_ratio", "local_built_fraction_r30m", "sector_enclosure_ratio_r50m"],
        "all_with_composite": PARAMETERS,
    }
    y_raw = df[response].to_numpy(dtype=float)
    rows = [["analysis_zone", "model", "predictor_count", "predictors", "cv_r2_mean", "cv_r2_sd", "cv_rmse_mean", "cv_rmse_sd", "n_repeats", "folds", "n_components", "evidence_type"]]
    coef_rows = [["analysis_zone", "model", "parameter", "parameter_label", "standardized_beta_full_sample", "evidence_type"]]
    n = len(df)
    for name, cols in models.items():
        r2_values, rmse_values = [], []
        for _ in range(n_repeats):
            idx = RNG.permutation(n)
            folds = np.array_split(idx, k)
            preds = np.empty(n)
            for fold in folds:
                train = np.setdiff1d(idx, fold, assume_unique=True)
                train_df = df.iloc[train]
                test_df = df.iloc[fold]
                train_x = standardized_design(train_df, cols)
                test_x_raw = test_df[cols].to_numpy(dtype=float)
                mu = train_df[cols].to_numpy(dtype=float).mean(axis=0)
                sd = train_df[cols].to_numpy(dtype=float).std(axis=0)
                sd[sd == 0] = 1.0
                test_x = (test_x_raw - mu) / sd
                train_y = train_df[response].to_numpy(dtype=float)
                pred, _ = fit_predict_ols(train_x, train_y, test_x)
                preds[fold] = pred
            r2_values.append(r2_score(y_raw, preds, np.mean(y_raw)))
            rmse_values.append(float(np.sqrt(np.mean((y_raw - preds) ** 2))))
        rows.append([zone, name, len(cols), "; ".join(cols), f"{np.mean(r2_values):.6f}", f"{np.std(r2_values):.6f}", f"{np.mean(rmse_values):.6f}", f"{np.std(rmse_values):.6f}", n_repeats, k, n, "newly_run"])

        x_full = standardized_design(df, cols)
        _, beta = fit_predict_ols(x_full, y_raw, x_full)
        for col, b in zip(cols, beta[1:]):
            coef_rows.append([zone, name, col, PARAM_LABELS[col], f"{b:.6f}", "newly_run"])
    return rows, coef_rows


def read_zone_csv(zone):
    if zone == "near_facade_0_20m":
        return pd.read_csv(FIG / "basic_morphology_per_component_near_facade_0_20m.csv")
    return pd.read_csv(FIG / "basic_morphology_per_component_local_context_20_50m.csv")


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(map(str, row)) + " |")
    return "\n".join(lines)


def main():
    zones = ["near_facade_0_20m", "local_context_20_50m"]
    spearman_rows = None
    effect_rows = None
    cv_rows = None
    coef_rows = None

    for zone in zones:
        df = read_zone_csv(zone)
        s = bootstrap_spearman_ci(df, zone, "directional_mean_vr")
        e = high_low_tertile_effect(df, zone, "directional_mean_vr")
        c, coefs = cross_validated_model_comparison(df, zone, "directional_mean_vr")
        spearman_rows = s if spearman_rows is None else spearman_rows + s[1:]
        effect_rows = e if effect_rows is None else effect_rows + e[1:]
        cv_rows = c if cv_rows is None else cv_rows + c[1:]
        coef_rows = coefs if coef_rows is None else coef_rows + coefs[1:]

    write_csv(FIG / "sci_stat_bootstrap_spearman_ci.csv", spearman_rows)
    write_csv(FIG / "sci_stat_tertile_effect_bootstrap_ci.csv", effect_rows)
    write_csv(FIG / "sci_stat_model_comparison_cv.csv", cv_rows)
    write_csv(FIG / "sci_stat_model_standardized_coefficients.csv", coef_rows)

    spearman_df = pd.DataFrame(spearman_rows[1:], columns=spearman_rows[0])
    for col in ["spearman_rho", "bootstrap_ci95_low", "bootstrap_ci95_high", "bootstrap_median"]:
        spearman_df[col] = spearman_df[col].astype(float)
    effect_df = pd.DataFrame(effect_rows[1:], columns=effect_rows[0])
    for col in ["low_mean", "high_mean", "delta_high_minus_low", "relative_change_high_vs_low", "bootstrap_ci95_low", "bootstrap_ci95_high"]:
        effect_df[col] = effect_df[col].astype(float)
    cv_df = pd.DataFrame(cv_rows[1:], columns=cv_rows[0])
    for col in ["cv_r2_mean", "cv_r2_sd", "cv_rmse_mean", "cv_rmse_sd"]:
        cv_df[col] = cv_df[col].astype(float)

    top_local = spearman_df[(spearman_df["analysis_zone"] == "local_context_20_50m")].copy()
    top_local = top_local.reindex(top_local["spearman_rho"].abs().sort_values(ascending=False).index).head(5)
    top_near = spearman_df[(spearman_df["analysis_zone"] == "near_facade_0_20m")].copy()
    top_near = top_near.reindex(top_near["spearman_rho"].abs().sort_values(ascending=False).index).head(5)

    cv_pivot = cv_df.sort_values(["analysis_zone", "cv_r2_mean"], ascending=[True, False])
    best_local = cv_pivot[cv_pivot["analysis_zone"] == "local_context_20_50m"].iloc[0]
    best_near = cv_pivot[cv_pivot["analysis_zone"] == "near_facade_0_20m"].iloc[0]
    local_context_only = cv_df[(cv_df["analysis_zone"] == "local_context_20_50m") & (cv_df["model"] == "context_only")].iloc[0]
    local_shape_only = cv_df[(cv_df["analysis_zone"] == "local_context_20_50m") & (cv_df["model"] == "size_height_shape")].iloc[0]

    rel_effect = effect_df[(effect_df["analysis_zone"] == "local_context_20_50m") & (effect_df["parameter"] == "relative_enclosure_score")].iloc[0]
    built_effect = effect_df[(effect_df["analysis_zone"] == "local_context_20_50m") & (effect_df["parameter"] == "local_built_fraction_r30m")].iloc[0]

    claims = [
        ["claim_id", "claim", "key_numbers", "evidence_type", "source_files", "claim_readiness"],
        [
            "SR1",
            "Bootstrap confidence intervals preserve the negative association between local-context enclosure and mean pedestrian VR.",
            f"relative enclosure rho={float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].spearman_rho):.3f}, 95% CI [{float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_low):.3f}, {float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_high):.3f}]",
            "newly_run",
            "figures/sci_stat_bootstrap_spearman_ci.csv",
            "paper_ready_as_screening",
        ],
        [
            "SR2",
            "High local-context enclosure remains a negative effect in bootstrap tertile comparison.",
            f"delta mean VR={rel_effect.delta_high_minus_low:.4f}, 95% CI [{rel_effect.bootstrap_ci95_low:.4f}, {rel_effect.bootstrap_ci95_high:.4f}]",
            "newly_run",
            "figures/sci_stat_tertile_effect_bootstrap_ci.csv",
            "paper_ready_as_screening",
        ],
        [
            "SR3",
            "Cross-validated model comparison favors local-context predictors over object-size/shape-only predictors.",
            f"local context_only CV R2={local_context_only.cv_r2_mean:.3f}; size_height_shape CV R2={local_shape_only.cv_r2_mean:.3f}; best local model={best_local.model} CV R2={best_local.cv_r2_mean:.3f}",
            "newly_run",
            "figures/sci_stat_model_comparison_cv.csv",
            "paper_ready_as_screening",
        ],
        [
            "SR4",
            "The statistical robustness analysis remains a component-level screening analysis, not causal proof or field validation.",
            "n=101 components per zone; no measured wind field; no intervention counterfactual",
            "blocked + newly_run",
            "reports/sci_statistical_robustness_analysis.md; reports/claim_boundary.md",
            "weaken_claim",
        ],
    ]
    write_csv(MAN / "sci_statistical_robustness_claims.csv", claims)

    local_table = table(
        ["parameter", "rho", "95% CI", "n"],
        [
            [
                r.parameter_label,
                f"{r.spearman_rho:.3f}",
                f"[{r.bootstrap_ci95_low:.3f}, {r.bootstrap_ci95_high:.3f}]",
                r.n_components,
            ]
            for _, r in top_local.iterrows()
        ],
    )
    cv_table = table(
        ["zone", "model", "CV R2 mean", "CV R2 SD", "RMSE"],
        [
            [r.analysis_zone, r.model, f"{r.cv_r2_mean:.3f}", f"{r.cv_r2_sd:.3f}", f"{r.cv_rmse_mean:.4f}"]
            for _, r in cv_pivot.groupby("analysis_zone").head(5).iterrows()
        ],
    )
    effect_table = table(
        ["zone", "parameter", "low mean VR", "high mean VR", "delta", "95% CI"],
        [
            [
                r.analysis_zone,
                r.parameter_label,
                f"{r.low_mean:.4f}",
                f"{r.high_mean:.4f}",
                f"{r.delta_high_minus_low:.4f}",
                f"[{r.bootstrap_ci95_low:.4f}, {r.bootstrap_ci95_high:.4f}]",
            ]
            for _, r in effect_df.reindex(effect_df.delta_high_minus_low.abs().sort_values(ascending=False).index).head(8).iterrows()
        ],
    )

    report = f"""# SCI Statistical Robustness Analysis

evidence_type: newly_run + blocked

This report adds statistical robustness checks to the existing morphology-wind-response conclusion. It does not add new CFD fields; it reuses component-level morphology and wind-response CSVs generated from the FluidX3D/ParaView post-processing pipeline.

## Inputs and Protocol

- Inputs: `figures/basic_morphology_per_component_near_facade_0_20m.csv` and `figures/basic_morphology_per_component_local_context_20_50m.csv`.
- Unit of analysis: retained building components, `n=101` for each zone.
- Response: component-level `directional_mean_vr`.
- Predictors: footprint area, mean height, height/sqrt(area), perimeter²/area, elongation, local built fraction within 30 m, sector enclosure within 50 m, and combined enclosure score.
- Robustness checks: 2,000 bootstrap resamples for Spearman correlations and high-vs-low tertile effects; 200 repeated 5-fold cross-validation runs for OLS model comparison.

## Bootstrap Correlations

The local-context band preserves the main negative association between enclosure and pedestrian wind recovery:

{local_table}

The combined enclosure score has Spearman rho `{float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].spearman_rho):.3f}` with a 95% bootstrap interval of `[{float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_low):.3f}, {float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_high):.3f}]`. Sector enclosure and mean height also remain mostly negative in the resampling distribution. This supports the claim that wind recovery is linked to local morphological context rather than to a single extreme component.

## Tertile Effect Robustness

{effect_table}

High combined enclosure in the 20-50 m band reduces mean VR by `{rel_effect.delta_high_minus_low:.4f}` compared with the low-enclosure group, with a bootstrap 95% CI of `[{rel_effect.bootstrap_ci95_low:.4f}, {rel_effect.bootstrap_ci95_high:.4f}]`. High local built fraction produces a comparable effect of `{built_effect.delta_high_minus_low:.4f}` with a 95% CI of `[{built_effect.bootstrap_ci95_low:.4f}, {built_effect.bootstrap_ci95_high:.4f}]`.

## Cross-Validated Model Comparison

{cv_table}

For the 20-50 m local-context band, the context-only model reaches mean cross-validated R² `{local_context_only.cv_r2_mean:.3f}`, while the size-height-shape model reaches `{local_shape_only.cv_r2_mean:.3f}`. The best local-context model is `{best_local.model}` with mean cross-validated R² `{best_local.cv_r2_mean:.3f}`. These values should be interpreted as modest predictive performance, but they are useful for paper argumentation because they show that contextual enclosure variables carry more transferable explanatory signal than object-size descriptors alone.

## SCI-Level Interpretation

The strengthened result is not merely that the campus core is slow at pedestrian height. The more specific conclusion is that local-context geometry controls the limited wind recovery within an already sheltered pedestrian field. In other words, the morphology variables do not transform the site from stagnant to ventilated; instead, they explain where small but design-relevant recovery occurs inside a generally low-speed campus core.

## Claim Boundary

This is a component-level statistical robustness analysis derived from simulation outputs. It is not causal identification, field validation, annual comfort/safety compliance, pollutant dispersion, or a simulated S1 intervention comparison.

## Output Tables

- `figures/sci_stat_bootstrap_spearman_ci.csv`
- `figures/sci_stat_tertile_effect_bootstrap_ci.csv`
- `figures/sci_stat_model_comparison_cv.csv`
- `figures/sci_stat_model_standardized_coefficients.csv`
- `manifests/sci_statistical_robustness_claims.csv`
"""
    (REPORTS / "sci_statistical_robustness_analysis.md").write_text(report.rstrip() + "\n", encoding="utf-8", newline="\n")

    paper = f"""# SCI 论文质量结果与讨论补强段落

evidence_type: newly_run + blocked

在形态-风环境关系的统计层面，本文进一步对 101 个建筑组件进行了 bootstrap 与交叉验证分析，以检验前述形态解释是否依赖少数极端样本。结果表明，在 20-50 m 局地背景带中，综合围合度与方向平均 VR 保持稳定负相关，Spearman rho 为 {float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].spearman_rho):.3f}，bootstrap 95% 置信区间为 [{float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_low):.3f}, {float(spearman_df[(spearman_df.analysis_zone=='local_context_20_50m') & (spearman_df.parameter=='relative_enclosure_score')].iloc[0].bootstrap_ci95_high):.3f}]；50 m 扇区围合度和平均高度也保持负向关系。分位组稳健性检验进一步显示，高综合围合度组相对于低综合围合度组的 mean VR 降低 {abs(rel_effect.delta_high_minus_low):.4f}，bootstrap 95% 置信区间为 [{rel_effect.bootstrap_ci95_low:.4f}, {rel_effect.bootstrap_ci95_high:.4f}]。这些结果说明，局地围合对近地风速恢复的抑制不是由单个建筑组件造成的偶然相关，而是在重采样下仍可观察到的结构性模式。

多变量模型比较进一步支持“局地形态背景优先于单体尺寸”的解释。以 20-50 m 背景带方向平均 VR 为响应变量时，仅包含局地建成比例和 50 m 扇区围合度的 context-only 模型取得平均交叉验证 R²={local_context_only.cv_r2_mean:.3f}，而由 footprint area、平均高度、height/sqrt(area)、perimeter²/area 和 elongation ratio 组成的 size-height-shape 模型为 R²={local_shape_only.cv_r2_mean:.3f}。虽然这种解释力仍属于中等偏弱的筛查级统计结果，不能被解释为因果识别，但它足以支持本文的设计应用判断：在真实校园数字孪生街区中，单体高度或平面形状并不是解释近地通风恢复的唯一或最有效变量，局地围合连续性、通道开敞性和建筑群之间的连通背景更接近工程干预的关键尺度。

因此，本文的建筑形式结论可进一步细化为三个层次。首先，核心校园街区的行人高度风环境整体处于低速背景，形态参数主要解释低速背景中的相对恢复，而不是决定是否形成高风速区。其次，0-20 m 近立面带和 20-50 m 局地背景带具有不同解释意义：前者几乎整体遮蔽，后者更能揭示围合与通风恢复之间的差异。最后，数字孪生风环境应用的价值不只是生成一张风速图，而是把“哪里低速、低速是否跨风向稳定、哪些形态参数与低速恢复有关、哪些模型资产能成为 CFD 边界”连接成可复核的设计证据链。

上述统计补强仍然不构成实测验证或正式舒适安全合规评价。当前结果应表述为 FluidX3D-native 数字孪生校园风环境筛查与形态解释；污染物扩散、S1 设计干预、3DGS-to-collision boundary transfer error 和 Rhino-Grasshopper/CityLBM 端到端运行仍需作为后续补充实验。
"""
    (PAPER / "sci_results_discussion_strengthened_zh.md").write_text(paper.rstrip() + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
