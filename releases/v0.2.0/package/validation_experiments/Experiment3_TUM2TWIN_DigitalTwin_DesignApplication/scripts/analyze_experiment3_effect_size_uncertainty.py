from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
REPORTS = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"

N_BOOT = 10000
SEED = 20260728


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bootstrap_mean_ci(values: np.ndarray, seed_offset: int = 0) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(SEED + seed_offset)
    samples = rng.choice(values, size=(N_BOOT, values.size), replace=True)
    boot = samples.mean(axis=1)
    return float(values.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def fmt(x: float, digits: int = 6) -> str:
    if not np.isfinite(x):
        return "nan"
    return f"{x:.{digits}f}"


def add_row(
    rows: list[dict[str, object]],
    *,
    layer: str,
    metric: str,
    n: int,
    estimate: float,
    low: float,
    high: float,
    interval_type: str,
    units: str,
    source: str,
    claim: str,
    boundary: str,
) -> None:
    rows.append(
        {
            "evidence_type": "newly_run",
            "analysis_layer": layer,
            "metric": metric,
            "n": n,
            "estimate": fmt(estimate),
            "interval_low": fmt(low),
            "interval_high": fmt(high),
            "interval_type": interval_type,
            "units": units,
            "source_artifact": source,
            "paper_safe_claim": claim,
            "claim_boundary": boundary,
        }
    )


def append_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    claim = "Experiment 3 effect-size and uncertainty analysis was computed from archived FluidX3D direction/sample metrics, S1/S2 trade-off tables, and building-component morphology recovery data."
    if any(row.get("claim") == claim for row in rows):
        return
    rows.append(
        {
            "claim": claim,
            "evidence_type": "newly_run + blocked",
            "source": "figures/experiment3_effect_size_uncertainty_summary.csv; reports/experiment3_effect_size_uncertainty_analysis.md; paper_text/experiment3_effect_size_uncertainty_results_zh.md",
        }
    )
    write_csv(path, rows, ["claim", "evidence_type", "source"])


def make_plot(rows: list[dict[str, object]], out: Path) -> None:
    df = pd.DataFrame(rows)
    df[["estimate", "interval_low", "interval_high"]] = df[["estimate", "interval_low", "interval_high"]].astype(float)

    vr_metrics = [
        "z2_mean_vr",
        "z40_mean_vr",
        "z40_minus_z2_mean_vr",
        "s1_z2_delta_global_mean_vr",
        "s2_z2_delta_global_mean_vr",
        "morphology_context_recovery_delta_vr",
    ]
    ratio_metrics = [
        "z2_stagnation_ratio",
        "z40_stagnation_ratio",
        "z40_minus_z2_stagnation_ratio",
        "s1_z2_delta_global_stagnation_ratio",
        "s2_z2_delta_global_stagnation_ratio",
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    for ax, metrics, title in [
        (axes[0], vr_metrics, "Velocity-ratio and delta-VR effects"),
        (axes[1], ratio_metrics, "Stagnation-ratio effects"),
    ]:
        sub = df[df["metric"].isin(metrics)].copy()
        sub["metric"] = pd.Categorical(sub["metric"], categories=metrics, ordered=True)
        sub = sub.sort_values("metric", ascending=False)
        y = np.arange(len(sub))
        x = sub["estimate"].to_numpy()
        xerr = np.vstack([x - sub["interval_low"].to_numpy(), sub["interval_high"].to_numpy() - x])
        ax.errorbar(x, y, xerr=xerr, fmt="o", color="#202124", ecolor="#58708a", elinewidth=1.8, capsize=4)
        ax.axvline(0, color="#9aa0a6", linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(sub["metric"].tolist(), fontsize=8)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle("Experiment 3 effect-size and uncertainty addendum", fontsize=13)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220)
    plt.close(fig)


def main() -> None:
    s0 = pd.read_csv(FIG / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    trade = pd.read_csv(FIG / "fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv")
    morph = pd.read_csv(FIG / "morphology_near_to_context_recovery_by_component.csv")

    rows: list[dict[str, object]] = []

    individual = s0[s0["averaging"] == "individual_sample"].copy()
    source_s0 = "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv"

    for i, height in enumerate([2.0, 40.0]):
        sub = individual[individual["z_height_m_approx"] == height]
        est, lo, hi = bootstrap_mean_ci(sub["vr_mean"].to_numpy(), i)
        add_row(
            rows,
            layer="S0 baseline direction-sample uncertainty",
            metric=f"z{int(height)}_mean_vr",
            n=len(sub),
            estimate=est,
            low=lo,
            high=hi,
            interval_type="bootstrap_95_ci_across_8_directions_x_3_samples",
            units="VR",
            source=source_s0,
            claim=f"At z~{int(height)} m, S0 mean VR is estimated from 24 direction-sample units.",
            boundary="Screening-level numerical uncertainty only; not measurement uncertainty or grid-convergence proof.",
        )
        est, lo, hi = bootstrap_mean_ci(sub["stagnation_ratio_vr_lt_0p2"].to_numpy(), 10 + i)
        add_row(
            rows,
            layer="S0 baseline direction-sample uncertainty",
            metric=f"z{int(height)}_stagnation_ratio",
            n=len(sub),
            estimate=est,
            low=lo,
            high=hi,
            interval_type="bootstrap_95_ci_across_8_directions_x_3_samples",
            units="ratio",
            source=source_s0,
            claim=f"At z~{int(height)} m, S0 VR<0.2 ratio is estimated from 24 direction-sample units.",
            boundary="Screening-level numerical uncertainty only; not annual exceedance probability.",
        )

    pivot_vr = individual.pivot_table(index=["wind_deg", "sample_index"], columns="z_height_m_approx", values="vr_mean")
    pivot_stag = individual.pivot_table(
        index=["wind_deg", "sample_index"], columns="z_height_m_approx", values="stagnation_ratio_vr_lt_0p2"
    )
    delta_vr = (pivot_vr[40.0] - pivot_vr[2.0]).dropna().to_numpy()
    delta_stag = (pivot_stag[40.0] - pivot_stag[2.0]).dropna().to_numpy()
    est, lo, hi = bootstrap_mean_ci(delta_vr, 20)
    add_row(
        rows,
        layer="vertical paired recovery",
        metric="z40_minus_z2_mean_vr",
        n=len(delta_vr),
        estimate=est,
        low=lo,
        high=hi,
        interval_type="paired_bootstrap_95_ci_across_8_directions_x_3_samples",
        units="delta_VR",
        source=source_s0,
        claim="The 40 m layer recovers strongly relative to the 2 m pedestrian layer.",
        boundary="Vertical contrast is based on modeled layers and does not replace pedestrian-height assessment.",
    )
    est, lo, hi = bootstrap_mean_ci(delta_stag, 21)
    add_row(
        rows,
        layer="vertical paired recovery",
        metric="z40_minus_z2_stagnation_ratio",
        n=len(delta_stag),
        estimate=est,
        low=lo,
        high=hi,
        interval_type="paired_bootstrap_95_ci_across_8_directions_x_3_samples",
        units="delta_ratio",
        source=source_s0,
        claim="The modeled stagnation ratio drops from pedestrian height to the upper layer.",
        boundary="Not a formal comfort/safety exceedance analysis.",
    )

    source_trade = "figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv"
    for i, comp in enumerate(["S1_minus_S0", "S2_minus_S0"]):
        sub = trade[(trade["comparison"] == comp) & (trade["z_height_m_approx"] == 2.0)]
        est = float(sub["delta_global_vr_mean"].mean())
        lo = float(sub["delta_global_vr_mean"].min())
        hi = float(sub["delta_global_vr_mean"].max())
        add_row(
            rows,
            layer="design sensitivity directional range",
            metric=f"{comp.split('_')[0].lower()}_z2_delta_global_mean_vr",
            n=len(sub),
            estimate=est,
            low=lo,
            high=hi,
            interval_type="8_direction_min_max_range",
            units="delta_VR",
            source=source_trade,
            claim=f"{comp} remains globally near-null/negative at z~2 m across the tested directions.",
            boundary="Negative sensitivity evidence, not a final design optimization result.",
        )
        est = float(sub["delta_global_stagnation_ratio_vr_lt_0p2"].mean())
        lo = float(sub["delta_global_stagnation_ratio_vr_lt_0p2"].min())
        hi = float(sub["delta_global_stagnation_ratio_vr_lt_0p2"].max())
        add_row(
            rows,
            layer="design sensitivity directional range",
            metric=f"{comp.split('_')[0].lower()}_z2_delta_global_stagnation_ratio",
            n=len(sub),
            estimate=est,
            low=lo,
            high=hi,
            interval_type="8_direction_min_max_range",
            units="delta_ratio",
            source=source_trade,
            claim=f"{comp} does not reduce the global z~2 m stagnation ratio in this screened setup.",
            boundary="Negative sensitivity evidence, not a final design optimization result.",
        )

    source_morph = "figures/morphology_near_to_context_recovery_by_component.csv"
    est, lo, hi = bootstrap_mean_ci(morph["context_recovery_delta_vr"].to_numpy(), 40)
    add_row(
        rows,
        layer="morphology near-to-context recovery",
        metric="morphology_context_recovery_delta_vr",
        n=len(morph),
        estimate=est,
        low=lo,
        high=hi,
        interval_type="bootstrap_95_ci_across_101_components",
        units="delta_VR",
        source=source_morph,
        claim="The 20-50 m local-context band shows a small but positive recovery over the 0-20 m near-facade band.",
        boundary="Sample-internal morphology screening only; not a universal or field-validated threshold.",
    )
    top = morph[morph["is_top_recovery_quartile"]]["context_recovery_delta_vr"].to_numpy()
    bottom = morph[morph["is_bottom_recovery_quartile"]]["context_recovery_delta_vr"].to_numpy()
    rng = np.random.default_rng(SEED + 41)
    top_boot = rng.choice(top, size=(N_BOOT, len(top)), replace=True).mean(axis=1)
    bottom_boot = rng.choice(bottom, size=(N_BOOT, len(bottom)), replace=True).mean(axis=1)
    diff_boot = top_boot - bottom_boot
    diff = float(top.mean() - bottom.mean())
    add_row(
        rows,
        layer="morphology near-to-context recovery",
        metric="top_minus_bottom_recovery_quartile_delta_vr",
        n=len(top) + len(bottom),
        estimate=diff,
        low=float(np.percentile(diff_boot, 2.5)),
        high=float(np.percentile(diff_boot, 97.5)),
        interval_type="bootstrap_95_ci_top_vs_bottom_recovery_quartiles",
        units="delta_VR",
        source=source_morph,
        claim="Top-recovery components have a larger near-to-context recovery than bottom-recovery components.",
        boundary="Descriptive subgroup contrast only; not causal proof.",
    )

    fields = [
        "evidence_type",
        "analysis_layer",
        "metric",
        "n",
        "estimate",
        "interval_low",
        "interval_high",
        "interval_type",
        "units",
        "source_artifact",
        "paper_safe_claim",
        "claim_boundary",
    ]
    write_csv(FIG / "experiment3_effect_size_uncertainty_summary.csv", rows, fields)
    make_plot(rows, FIG / "experiment3_effect_size_uncertainty_forest.png")

    df = pd.DataFrame(rows)
    lookup = {row["metric"]: row for row in rows}
    report = f"""# Experiment 3 Effect-Size and Uncertainty Analysis

evidence_type: newly_run + blocked

## Protocol

This addendum recomputes paper-facing effect sizes from archived Experiment 3 CSV outputs. It does not run a new CFD solver case. The S0 baseline uncertainty uses the `individual_sample` rows of `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`, giving 8 wind directions x 3 post-spin-up samples = 24 direction-sample units per height. Vertical recovery uses paired direction-sample differences between z~40 m and z~2 m. S1/S2 design sensitivity uses the 8-direction min-max range at z~2 m from `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`. Morphology recovery uses the 101 retained building components in `figures/morphology_near_to_context_recovery_by_component.csv`.

## Key Effect Sizes

- S0 z~2 m mean VR: `{lookup['z2_mean_vr']['estimate']}` with bootstrap 95% CI `{lookup['z2_mean_vr']['interval_low']}` to `{lookup['z2_mean_vr']['interval_high']}`.
- S0 z~2 m VR<0.2 ratio: `{lookup['z2_stagnation_ratio']['estimate']}` with bootstrap 95% CI `{lookup['z2_stagnation_ratio']['interval_low']}` to `{lookup['z2_stagnation_ratio']['interval_high']}`.
- Paired z~40 m minus z~2 m mean VR: `{lookup['z40_minus_z2_mean_vr']['estimate']}` with bootstrap 95% CI `{lookup['z40_minus_z2_mean_vr']['interval_low']}` to `{lookup['z40_minus_z2_mean_vr']['interval_high']}`.
- S1 z~2 m global mean-VR delta: `{lookup['s1_z2_delta_global_mean_vr']['estimate']}` with 8-direction range `{lookup['s1_z2_delta_global_mean_vr']['interval_low']}` to `{lookup['s1_z2_delta_global_mean_vr']['interval_high']}`.
- S2 z~2 m global mean-VR delta: `{lookup['s2_z2_delta_global_mean_vr']['estimate']}` with 8-direction range `{lookup['s2_z2_delta_global_mean_vr']['interval_low']}` to `{lookup['s2_z2_delta_global_mean_vr']['interval_high']}`.
- Mean near-to-context morphology recovery delta: `{lookup['morphology_context_recovery_delta_vr']['estimate']}` with bootstrap 95% CI `{lookup['morphology_context_recovery_delta_vr']['interval_low']}` to `{lookup['morphology_context_recovery_delta_vr']['interval_high']}`.

## Paper-Safe Interpretation

The added uncertainty layer strengthens three conservative conclusions. First, the pedestrian-height low-speed state is not a single-sample artifact: the z~2 m mean VR remains low and the VR<0.2 ratio remains high across direction-sample bootstrap resampling. Second, the vertical contrast is large and consistently positive for mean VR, confirming that above-roof flow recovery cannot be substituted for pedestrian-layer assessment. Third, S1/S2 remain near-null or negative in global z~2 m metrics across the eight tested directions, so their role is negative design-sensitivity evidence rather than successful optimization.

For morphology, the 20-50 m local-context band shows a small positive recovery relative to the 0-20 m near-facade band, and the top-versus-bottom recovery quartile contrast is descriptive evidence for sample-internal design screening. These results remain bounded: they are not field measurement uncertainty, not grid-convergence proof, not annual comfort/safety exceedance probabilities, and not causal design thresholds.

## Output Artifacts

- `figures/experiment3_effect_size_uncertainty_summary.csv`
- `figures/experiment3_effect_size_uncertainty_forest.png`
- `reports/experiment3_effect_size_uncertainty_analysis.md`
- `paper_text/experiment3_effect_size_uncertainty_results_zh.md`
- `manifests/experiment3_effect_size_uncertainty_claims.csv`
"""
    write_text(REPORTS / "experiment3_effect_size_uncertainty_analysis.md", report)

    paper_zh = f"""# 实验3效应量与不确定性补充结果

evidence_type: newly_run + blocked

为避免将单个均值误写为稳定规律，本研究在既有 FluidX3D 输出基础上增加了效应量与不确定性统计。S0 基准结果使用 dx=2 m 核心闭合棱柱模型的 8 个风向和 3 个后旋起采样时刻，共 24 个方向-采样单元；竖向恢复采用同一方向-采样单元下 z~40 m 与 z~2 m 的成对差值；S1/S2 设计敏感性采用 z~2 m 的 8 风向范围；形态恢复采用 101 个保留建筑单元的 0-20 m 近立面带与 20-50 m 局地环境带配对结果。

补充统计显示，S0 在 z~2 m 的 mean VR 为 `{lookup['z2_mean_vr']['estimate']}`，bootstrap 95% CI 为 `{lookup['z2_mean_vr']['interval_low']}`-`{lookup['z2_mean_vr']['interval_high']}`；VR<0.2 滞风比例为 `{lookup['z2_stagnation_ratio']['estimate']}`，bootstrap 95% CI 为 `{lookup['z2_stagnation_ratio']['interval_low']}`-`{lookup['z2_stagnation_ratio']['interval_high']}`。这说明核心校园街区的行人层低速状态不是单个风向或单个采样时刻造成的偶然结果。与之相比，z~40 m 相对 z~2 m 的 mean VR 成对增量为 `{lookup['z40_minus_z2_mean_vr']['estimate']}`，bootstrap 95% CI 为 `{lookup['z40_minus_z2_mean_vr']['interval_low']}`-`{lookup['z40_minus_z2_mean_vr']['interval_high']}`，说明屋面以上恢复和行人层滞风之间存在显著的竖向脱耦。

设计敏感性补充统计进一步支持负结果解释。S1 在 z~2 m 的全局 mean-VR 变化均值为 `{lookup['s1_z2_delta_global_mean_vr']['estimate']}`，8 风向范围为 `{lookup['s1_z2_delta_global_mean_vr']['interval_low']}`-`{lookup['s1_z2_delta_global_mean_vr']['interval_high']}`；S2 对应值为 `{lookup['s2_z2_delta_global_mean_vr']['estimate']}`，8 风向范围为 `{lookup['s2_z2_delta_global_mean_vr']['interval_low']}`-`{lookup['s2_z2_delta_global_mean_vr']['interval_high']}`。因此，S1/S2 不应写成成功优化方案，而应写成说明“单纯增加孔隙率不足以恢复行人层通风”的设计筛查证据。

建筑形态层面，20-50 m 局地环境带相对 0-20 m 近立面带的平均恢复增量为 `{lookup['morphology_context_recovery_delta_vr']['estimate']}`，bootstrap 95% CI 为 `{lookup['morphology_context_recovery_delta_vr']['interval_low']}`-`{lookup['morphology_context_recovery_delta_vr']['interval_high']}`。这支持论文中较谨慎的新认识：在该校园核心样本内，近立面带过于一致地滞风，难以区分建筑形式影响；20-50 m 局地环境尺度更适合识别围合、相对高度和动量进入条件对风速恢复的影响。该结论仍是数字孪生样本内筛查结论，不是实测验证的普适设计阈值。
"""
    write_text(PAPER / "experiment3_effect_size_uncertainty_results_zh.md", paper_zh)

    claims = [
        {
            "claim_id": "EU1",
            "claim": "S0 pedestrian-height low-speed conclusion remains stable under direction-sample bootstrap resampling.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_effect_size_uncertainty_summary.csv",
            "claim_readiness": "paper_ready_as_screening",
        },
        {
            "claim_id": "EU2",
            "claim": "The modeled upper layer shows strong paired VR recovery relative to the pedestrian layer.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_effect_size_uncertainty_summary.csv",
            "claim_readiness": "paper_ready_as_screening",
        },
        {
            "claim_id": "EU3",
            "claim": "S1/S2 are globally near-null or negative across the tested z~2 m directions.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_effect_size_uncertainty_summary.csv; figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv",
            "claim_readiness": "paper_ready_negative_result",
        },
        {
            "claim_id": "EU4",
            "claim": "The 20-50 m local-context band shows sample-internal near-to-context recovery, but not a universal design threshold.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/experiment3_effect_size_uncertainty_summary.csv; figures/morphology_near_to_context_recovery_by_component.csv",
            "claim_readiness": "paper_ready_with_boundary",
        },
    ]
    write_csv(
        MAN / "experiment3_effect_size_uncertainty_claims.csv",
        claims,
        ["claim_id", "claim", "evidence_type", "source", "claim_readiness"],
    )
    append_evidence_inventory()

    print("wrote figures/experiment3_effect_size_uncertainty_summary.csv")
    print("wrote figures/experiment3_effect_size_uncertainty_forest.png")
    print("wrote reports/experiment3_effect_size_uncertainty_analysis.md")
    print("wrote paper_text/experiment3_effect_size_uncertainty_results_zh.md")
    print("wrote manifests/experiment3_effect_size_uncertainty_claims.csv")
    print("updated manifests/evidence_inventory.csv")


if __name__ == "__main__":
    main()
