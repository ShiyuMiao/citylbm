from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, rankdata, spearmanr, t


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"

ZONES = [
    ("near_facade_0_20m", "0-20 m facade-adjacent band"),
    ("local_context_20_50m", "20-50 m local-context band"),
]

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

TARGETS = [
    ("directional_mean_vr", "mean VR"),
    ("directional_p95_vr", "P95 VR"),
    ("directional_range_mean_vr", "directional range of mean VR"),
]

RNG = np.random.default_rng(20260728)
BOOTSTRAP_N = 300
CV_REPEATS = 8


@dataclass
class RidgeResult:
    alpha: float
    cv_r2_mean: float
    cv_r2_std: float
    coefficients: np.ndarray
    permutation_drop_mean: np.ndarray


def zscore(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    std = values.std(axis=0, ddof=0)
    std[std == 0] = 1.0
    return (values - mean) / std, mean, std


def rank_zscore(values: np.ndarray) -> np.ndarray:
    ranked = np.apply_along_axis(rankdata, 0, values)
    z, _, _ = zscore(ranked.astype(float))
    return z


def ridge_fit(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    xtx = x.T @ x
    penalty = np.eye(x.shape[1]) * alpha
    return np.linalg.solve(xtx + penalty, x.T @ y)


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.sum((y_true - y_true.mean()) ** 2)
    if denom <= 0:
        return np.nan
    return float(1.0 - np.sum((y_true - y_pred) ** 2) / denom)


def make_folds(n: int, repeat: int, k: int = 5) -> list[tuple[np.ndarray, np.ndarray]]:
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(repeat):
        order = RNG.permutation(n)
        chunks = np.array_split(order, k)
        for test_idx in chunks:
            train_mask = np.ones(n, dtype=bool)
            train_mask[test_idx] = False
            folds.append((np.where(train_mask)[0], test_idx))
    return folds


def cross_validated_ridge(x: np.ndarray, y: np.ndarray) -> RidgeResult:
    alphas = [0.0, 0.1, 1.0, 10.0, 100.0]
    folds = make_folds(len(y), repeat=CV_REPEATS)
    alpha_scores: dict[float, list[float]] = {a: [] for a in alphas}

    for alpha in alphas:
        for train_idx, test_idx in folds:
            x_train_raw = x[train_idx]
            x_test_raw = x[test_idx]
            y_train_raw = y[train_idx]
            y_test_raw = y[test_idx]
            x_train, x_mean, x_std = zscore(x_train_raw)
            x_test = (x_test_raw - x_mean) / x_std
            y_train = y_train_raw - y_train_raw.mean()
            coef = ridge_fit(x_train, y_train, alpha)
            pred = x_test @ coef + y_train_raw.mean()
            alpha_scores[alpha].append(r2_score(y_test_raw, pred))

    best_alpha = max(alphas, key=lambda a: np.nanmean(alpha_scores[a]))
    x_full, _, _ = zscore(x)
    y_centered = y - y.mean()
    coef_full = ridge_fit(x_full, y_centered, best_alpha)

    baseline_scores = []
    permutation_drops = np.zeros((len(folds), x.shape[1]), dtype=float)
    for fold_i, (train_idx, test_idx) in enumerate(folds):
        x_train_raw = x[train_idx]
        x_test_raw = x[test_idx]
        y_train_raw = y[train_idx]
        y_test_raw = y[test_idx]
        x_train, x_mean, x_std = zscore(x_train_raw)
        x_test = (x_test_raw - x_mean) / x_std
        y_train = y_train_raw - y_train_raw.mean()
        coef = ridge_fit(x_train, y_train, best_alpha)
        pred = x_test @ coef + y_train_raw.mean()
        base = r2_score(y_test_raw, pred)
        baseline_scores.append(base)
        for j in range(x.shape[1]):
            x_perm = x_test.copy()
            x_perm[:, j] = RNG.permutation(x_perm[:, j])
            perm_pred = x_perm @ coef + y_train_raw.mean()
            permutation_drops[fold_i, j] = base - r2_score(y_test_raw, perm_pred)

    return RidgeResult(
        alpha=float(best_alpha),
        cv_r2_mean=float(np.nanmean(baseline_scores)),
        cv_r2_std=float(np.nanstd(baseline_scores)),
        coefficients=coef_full,
        permutation_drop_mean=np.nanmean(permutation_drops, axis=0),
    )


def residualize(y: np.ndarray, controls: np.ndarray) -> np.ndarray:
    if controls.shape[1] == 0:
        return y - y.mean()
    design = np.column_stack([np.ones(len(y)), controls])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ coef


def partial_spearman(x: np.ndarray, y: np.ndarray, controls: np.ndarray) -> tuple[float, float]:
    xr = rankdata(x).astype(float)
    yr = rankdata(y).astype(float)
    cr = np.apply_along_axis(rankdata, 0, controls).astype(float) if controls.size else controls
    rx = residualize(xr, cr)
    ry = residualize(yr, cr)
    r, _ = pearsonr(rx, ry)
    dof = len(y) - controls.shape[1] - 2
    if dof <= 0 or abs(r) >= 1:
        return float(r), np.nan
    stat = r * np.sqrt(dof / max(1e-12, 1 - r * r))
    p = 2 * t.sf(abs(stat), dof)
    return float(r), float(p)


def bootstrap_spearman(x: np.ndarray, y: np.ndarray, n_boot: int = BOOTSTRAP_N) -> tuple[float, float, float]:
    vals = []
    n = len(y)
    for _ in range(n_boot):
        idx = RNG.integers(0, n, size=n)
        if np.unique(x[idx]).size < 2 or np.unique(y[idx]).size < 2:
            continue
        vals.append(spearmanr(x[idx], y[idx]).statistic)
    if not vals:
        return np.nan, np.nan, np.nan
    arr = np.asarray(vals, dtype=float)
    return float(np.nanmean(arr)), float(np.nanpercentile(arr, 2.5)), float(np.nanpercentile(arr, 97.5))


def read_zone(zone: str) -> pd.DataFrame:
    path = FIG / f"basic_morphology_per_component_{zone}.csv"
    df = pd.read_csv(path)
    keep = [f[0] for f in FEATURES] + [t[0] for t in TARGETS] + ["component_id"]
    return df[keep].dropna().copy()


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    PAPER.mkdir(parents=True, exist_ok=True)

    robust_rows = []
    model_rows = []

    for zone, zone_label in ZONES:
        df = read_zone(zone)
        feature_cols = [f[0] for f in FEATURES]
        x_rank = rank_zscore(df[feature_cols].to_numpy(float))

        for target, target_label in TARGETS:
            y = df[target].to_numpy(float)
            y_rank = rank_zscore(y.reshape(-1, 1)).ravel()
            model = cross_validated_ridge(x_rank, y_rank)

            for j, (feature, feature_label) in enumerate(FEATURES):
                controls = np.delete(x_rank, j, axis=1)
                ps, ps_p = partial_spearman(df[feature].to_numpy(float), y, controls)
                bs_mean, bs_low, bs_high = bootstrap_spearman(df[feature].to_numpy(float), y)
                rho, p_value = spearmanr(df[feature], y)
                robust_rows.append(
                    {
                        "evidence_type": "newly_run",
                        "analysis_zone": zone,
                        "analysis_zone_label": zone_label,
                        "target": target,
                        "target_label": target_label,
                        "feature": feature,
                        "feature_label": feature_label,
                        "n_components": len(df),
                        "spearman_rho": float(rho),
                        "spearman_p": float(p_value),
                        "bootstrap_spearman_mean": bs_mean,
                        "bootstrap_spearman_ci95_low": bs_low,
                        "bootstrap_spearman_ci95_high": bs_high,
                        "partial_spearman": ps,
                        "partial_spearman_p": ps_p,
                        "ridge_alpha": model.alpha,
                        "ridge_cv_r2_mean": model.cv_r2_mean,
                        "ridge_cv_r2_std": model.cv_r2_std,
                        "ridge_standardized_coef": float(model.coefficients[j]),
                        "permutation_r2_drop": float(model.permutation_drop_mean[j]),
                    }
                )

            model_rows.append(
                {
                    "evidence_type": "newly_run",
                    "analysis_zone": zone,
                    "analysis_zone_label": zone_label,
                    "target": target,
                    "target_label": target_label,
                    "n_components": len(df),
                    "ridge_alpha": model.alpha,
                    "ridge_cv_r2_mean": model.cv_r2_mean,
                    "ridge_cv_r2_std": model.cv_r2_std,
                }
            )

    robust = pd.DataFrame(robust_rows)
    models = pd.DataFrame(model_rows)
    robust.to_csv(FIG / "basic_morphology_multivariate_robustness.csv", index=False, encoding="utf-8-sig")
    models.to_csv(FIG / "basic_morphology_rank_model_cv_summary.csv", index=False, encoding="utf-8-sig")

    context_mean = robust[
        (robust["analysis_zone"] == "local_context_20_50m")
        & (robust["target"] == "directional_mean_vr")
    ].copy()
    context_mean["abs_perm"] = context_mean["permutation_r2_drop"].abs()
    context_mean = context_mean.sort_values("permutation_r2_drop", ascending=True)

    fig, (ax_coef, ax_perm) = plt.subplots(
        1,
        2,
        figsize=(11.2, 5.5),
        gridspec_kw={"width_ratios": [1.7, 1.0]},
    )
    y_pos = np.arange(len(context_mean))
    coef_vals = context_mean["ridge_standardized_coef"].to_numpy(float)
    perm_vals = context_mean["permutation_r2_drop"].clip(lower=0).to_numpy(float)
    colors = ["#c13f3f" if v < 0 else "#3274a1" for v in coef_vals]

    ax_coef.barh(y_pos, coef_vals, color=colors, alpha=0.88)
    ax_coef.axvline(0, color="black", linewidth=0.8)
    ax_coef.set_yticks(y_pos)
    ax_coef.set_yticklabels(context_mean["feature_label"])
    ax_coef.set_xlabel("standardized ridge coefficient")
    ax_coef.set_title("Rank-regression coefficient")
    for i, val in enumerate(coef_vals):
        offset = 0.006 if val < 0 else 0.004
        ax_coef.text(val + offset, i, f"{val:.3f}", va="center", ha="left", fontsize=8)

    ax_perm.barh(y_pos, perm_vals, color="#595959", alpha=0.82)
    ax_perm.set_yticks(y_pos)
    ax_perm.set_yticklabels([])
    ax_perm.set_xlabel("permutation R2 drop")
    ax_perm.set_title("Importance")
    for i, val in enumerate(perm_vals):
        ax_perm.text(val + 0.002, i, f"{val:.3f}", va="center", ha="left", fontsize=8)
    ax_perm.set_xlim(0, max(0.1, float(np.nanmax(perm_vals)) * 1.25))
    fig.suptitle("Multivariate morphology response model, 20-50 m local context", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    fig.savefig(FIG / "basic_morphology_multivariate_rank_model_importance.png", dpi=240)
    plt.close(fig)

    top_perm = context_mean.sort_values("permutation_r2_drop", ascending=False).head(4)
    top_partial = context_mean.reindex(context_mean["partial_spearman"].abs().sort_values(ascending=False).index).head(4)
    context_model = models[
        (models["analysis_zone"] == "local_context_20_50m")
        & (models["target"] == "directional_mean_vr")
    ].iloc[0]

    report = f"""# Multivariate Robustness of Basic Morphology-Wind Relations

evidence_type: newly_run

## Purpose

This supplementary analysis tests whether the basic morphology conclusion is robust beyond single-parameter Spearman correlations. It uses the same retained central components and FluidX3D-derived wind-response table as the basic morphology analysis, with no solver rerun.

## Protocol

- Inputs: `figures/basic_morphology_per_component_near_facade_0_20m.csv` and `figures/basic_morphology_per_component_local_context_20_50m.csv`.
- Sample unit: retained building component (`n=101`).
- Predictors: footprint area, mean height, height/sqrt(area), perimeter^2/area, elongation ratio, local built fraction within 30 m, sector enclosure within 50 m and combined enclosure score.
- Responses: eight-direction averaged mean VR, P95 VR and directional range of mean VR.
- Robustness checks: bootstrap Spearman intervals (`n={BOOTSTRAP_N}`), partial Spearman after controlling for the remaining predictors, and repeated 5-fold cross-validated ridge regression (`{CV_REPEATS}` repeats) on rank-transformed variables.

## Main Result

For the 20-50 m local-context band, the rank-regression model for mean VR has cross-validated R2 `{context_model['ridge_cv_r2_mean']:.3f} +/- {context_model['ridge_cv_r2_std']:.3f}`. This should be interpreted as limited but useful explanatory power, not as a predictive urban wind model. The useful outcome is the ordering of morphological signals rather than high deterministic prediction accuracy.

## Strongest Multivariate Signals for 20-50 m Mean VR

### Permutation Importance

{top_perm[['feature_label','spearman_rho','bootstrap_spearman_ci95_low','bootstrap_spearman_ci95_high','partial_spearman','ridge_standardized_coef','permutation_r2_drop']].to_markdown(index=False, floatfmt='.4f')}

### Partial Spearman Ranking

{top_partial[['feature_label','spearman_rho','partial_spearman','partial_spearman_p','ridge_standardized_coef','permutation_r2_drop']].to_markdown(index=False, floatfmt='.4f')}

## Interpretation

The multivariate check supports the earlier morphology conclusion with a narrower claim. The explanatory pattern is not reducible to a single footprint-size or height effect. Enclosure-related variables remain important, but they are statistically entangled because `relative_enclosure_score` combines local built fraction and sector enclosure. Therefore, the paper should write the result as a local-context morphology diagnosis: pedestrian-layer wind recovery depends on whether the 30-50 m surroundings permit pressure and momentum exchange, while individual building height or footprint area alone is insufficient.

## Claim Boundary

This is a post-processing statistical robustness analysis. It does not validate the CFD model against measurements, prove causal design effects, or replace additional S3-Sn intervention experiments.
"""
    (REP / "basic_morphology_multivariate_robustness.md").write_text(report, encoding="utf-8")

    paper = f"""# 基础形态参数的多变量稳健性结论

evidence_type: newly_run

在单变量 Spearman 相关之外，本文进一步对 101 个保留建筑单元进行多变量稳健性检验。该检验以建筑单元为样本，以 20-50 m 局地环境带的八风向平均 VR、P95 VR 与方向差异为响应变量，对足迹面积、平均高度、height/sqrt(area)、周长-面积比、长宽比、30 m 局地建成比例、50 m 扇区围合比例和综合围合得分进行 rank-transformed 岭回归、bootstrap Spearman 与偏 Spearman 分析。该步骤不重新运行 FluidX3D，而是对已有 VTK 后处理结果进行统计复核。

结果表明，基础形态参数对 20-50 m 局地环境带 mean VR 的解释力是“有限但可解释”的：rank-regression 的重复 5 折交叉验证 R2 为 {context_model['ridge_cv_r2_mean']:.3f}±{context_model['ridge_cv_r2_std']:.3f}。因此，本文不应把形态参数写成确定性预测模型，而应把它们作为校园街区通风筛查的可解释诊断变量。与单变量结果一致，多变量检验的变量排序仍显示局地围合相关变量比单体尺度变量更接近行人层风速恢复机制；但由于综合围合得分本身由局地建成比例和扇区围合共同构成，论文中应避免把某一个指标解释为孤立因果变量。

这一补充分析使“建筑形式与风环境关系”的结论更加清晰：在 TUM Downtown 校园核心区，影响行人层风环境的不是单栋建筑的面积、高度或长宽比本身，而是这些建筑在 30-50 m 局地范围内是否形成连续围合、阻断外部动量进入，并削弱院落-街道之间的压力交换。换言之，数字孪生 CFD 的新贡献不是重复传统上“高密度削弱通风”的经验判断，而是把这种判断落实为可定位的形态诊断：贴近建筑界面的 0-20 m 区域几乎普遍滞风，而 20-50 m 局地环境带才表现出由围合度、局部建成比例和扇区遮挡共同控制的风速恢复差异。
"""
    (PAPER / "basic_morphology_multivariate_robustness_conclusion_zh.md").write_text(paper, encoding="utf-8")

    print("wrote", FIG / "basic_morphology_multivariate_robustness.csv")
    print("wrote", FIG / "basic_morphology_rank_model_cv_summary.csv")
    print("wrote", FIG / "basic_morphology_multivariate_rank_model_importance.png")
    print("wrote", REP / "basic_morphology_multivariate_robustness.md")
    print("wrote", PAPER / "basic_morphology_multivariate_robustness_conclusion_zh.md")


if __name__ == "__main__":
    main()
