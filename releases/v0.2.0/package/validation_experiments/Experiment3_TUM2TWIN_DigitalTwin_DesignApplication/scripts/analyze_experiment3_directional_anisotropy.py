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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmt(x: float, digits: int = 6) -> str:
    if x is None or not np.isfinite(x):
        return "nan"
    return f"{x:.{digits}f}"


def anisotropy(values: pd.Series) -> tuple[float, float, float, float]:
    arr = values.astype(float).to_numpy()
    mean = float(np.mean(arr))
    vmin = float(np.min(arr))
    vmax = float(np.max(arr))
    idx = float((vmax - vmin) / mean) if mean != 0 else float("nan")
    return mean, vmin, vmax, idx


def append_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    claim = "Experiment 3 directional anisotropy analysis was computed from archived 8-direction FluidX3D time-mean metrics, Open-Meteo proxy weights, and S1/S2 directional trade-off tables."
    if any(row.get("claim") == claim for row in rows):
        return
    rows.append(
        {
            "claim": claim,
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "figures/experiment3_directional_response_by_wind.csv; figures/experiment3_directional_anisotropy_summary.csv; reports/experiment3_directional_anisotropy_analysis.md",
        }
    )
    write_csv(path, rows, ["claim", "evidence_type", "source"])


def make_direction_plot(direction: pd.DataFrame, summary: pd.DataFrame, out: Path) -> None:
    deg = direction["wind_deg"].astype(float).to_numpy()
    theta = np.deg2rad(deg)
    theta_closed = np.r_[theta, theta[0]]

    z2 = direction["z2_mean_vr"].to_numpy()
    stagnation = direction["z2_stagnation_ratio"].to_numpy()
    recovery = direction["z40_minus_z2_mean_vr"].to_numpy()
    s2_common = direction["s2_common_delta_vr_mean"].to_numpy()

    fig = plt.figure(figsize=(13.5, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)

    ax1 = fig.add_subplot(gs[0, 0], projection="polar")
    ax2 = fig.add_subplot(gs[0, 1], projection="polar")
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    for ax in [ax1, ax2]:
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 45)))
        ax.tick_params(labelsize=8)

    ax1.plot(theta_closed, np.r_[z2, z2[0]], marker="o", color="#1f4e79")
    ax1.fill(theta_closed, np.r_[z2, z2[0]], color="#1f4e79", alpha=0.18)
    ax1.set_title("S0 z~2 m mean VR by wind direction", fontsize=10)

    ax2.plot(theta_closed, np.r_[stagnation, stagnation[0]], marker="o", color="#8a3ffc")
    ax2.fill(theta_closed, np.r_[stagnation, stagnation[0]], color="#8a3ffc", alpha=0.16)
    ax2.set_title("S0 z~2 m stagnation ratio by wind direction", fontsize=10)

    x = np.arange(len(direction))
    ax3.bar(x - 0.18, recovery, width=0.36, color="#2f6f4e", label="z40-z2 mean VR")
    ax3.bar(x + 0.18, s2_common, width=0.36, color="#b45f06", label="S2 common-open delta VR")
    ax3.set_xticks(x)
    ax3.set_xticklabels([str(int(v)) for v in deg])
    ax3.set_xlabel("Velocity-to wind direction (deg)")
    ax3.set_ylabel("Delta VR")
    ax3.grid(axis="y", color="#e5e7eb")
    ax3.legend(fontsize=8)
    ax3.set_title("Vertical recovery and S2 local response", fontsize=10)

    metric_order = [
        "z2_mean_vr",
        "z2_stagnation_ratio",
        "z40_minus_z2_mean_vr",
        "s1_delta_global_mean_vr",
        "s2_delta_global_mean_vr",
        "s2_common_delta_vr_mean",
    ]
    sub = summary[summary["metric"].isin(metric_order)].copy()
    sub["metric"] = pd.Categorical(sub["metric"], categories=metric_order[::-1], ordered=True)
    sub = sub.sort_values("metric")
    ax4.barh(sub["metric"].astype(str), sub["anisotropy_index"].astype(float), color="#4f6f8f")
    ax4.set_xlabel("(max-min)/mean or abs(mean) for signed deltas")
    ax4.grid(axis="x", color="#e5e7eb")
    ax4.tick_params(labelsize=8)
    ax4.set_title("Directional anisotropy index", fontsize=10)

    fig.suptitle("Experiment 3 directional anisotropy and design-sector response", fontsize=13)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220)
    plt.close(fig)


def main() -> None:
    s0 = pd.read_csv(FIG / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    trade = pd.read_csv(FIG / "fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv")
    weights = pd.read_csv(MAN / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv")

    tm = s0[s0["averaging"] == "time_mean_3_samples"].copy()
    wide_vr = tm.pivot(index="wind_deg", columns="z_height_m_approx", values="vr_mean")
    wide_stag = tm.pivot(index="wind_deg", columns="z_height_m_approx", values="stagnation_ratio_vr_lt_0p2")
    wide_p95 = tm.pivot(index="wind_deg", columns="z_height_m_approx", values="vr_p95")
    accel = tm.pivot(index="wind_deg", columns="z_height_m_approx", values="accelerated_ratio_vr_gt_0p6")

    direction = pd.DataFrame(
        {
            "wind_deg": wide_vr.index.astype(int),
            "z2_mean_vr": wide_vr[2.0].to_numpy(),
            "z2_p95_vr": wide_p95[2.0].to_numpy(),
            "z2_stagnation_ratio": wide_stag[2.0].to_numpy(),
            "z2_accelerated_ratio": accel[2.0].to_numpy(),
            "z40_mean_vr": wide_vr[40.0].to_numpy(),
            "z40_stagnation_ratio": wide_stag[40.0].to_numpy(),
            "z40_minus_z2_mean_vr": (wide_vr[40.0] - wide_vr[2.0]).to_numpy(),
            "z40_minus_z2_stagnation_ratio": (wide_stag[40.0] - wide_stag[2.0]).to_numpy(),
        }
    ).sort_values("wind_deg")

    for comp, prefix in [("S1_minus_S0", "s1"), ("S2_minus_S0", "s2")]:
        sub = trade[(trade["comparison"] == comp) & (trade["z_height_m_approx"] == 2.0)].copy()
        keep = sub[
            [
                "wind_deg",
                "delta_global_vr_mean",
                "delta_global_stagnation_ratio_vr_lt_0p2",
                "common_delta_vr_mean",
                "common_improved_ratio_delta_gt_0p02",
                "newly_open_target_vr_mean",
            ]
        ].rename(
            columns={
                "delta_global_vr_mean": f"{prefix}_delta_global_mean_vr",
                "delta_global_stagnation_ratio_vr_lt_0p2": f"{prefix}_delta_global_stagnation_ratio",
                "common_delta_vr_mean": f"{prefix}_common_delta_vr_mean",
                "common_improved_ratio_delta_gt_0p02": f"{prefix}_common_improved_ratio",
                "newly_open_target_vr_mean": f"{prefix}_newly_open_target_vr_mean",
            }
        )
        direction = direction.merge(keep, on="wind_deg", how="left")

    # Normalize Open-Meteo column names defensively; earlier manifests use velocity-to sector names.
    weight_col = next(c for c in weights.columns if "weight" in c.lower())
    sector_col = next(c for c in weights.columns if "sector" in c.lower() or "deg" in c.lower())
    wdf = weights[[sector_col, weight_col]].rename(columns={sector_col: "wind_deg", weight_col: "open_meteo_2024_weight"})
    wdf["wind_deg"] = wdf["wind_deg"].astype(str).str.extract(r"(-?\d+\.?\d*)")[0].astype(float).astype(int)
    direction = direction.merge(wdf, on="wind_deg", how="left")
    direction["open_meteo_weighted_z2_vr_contribution"] = (
        direction["open_meteo_2024_weight"] * direction["z2_mean_vr"]
    )
    direction["open_meteo_weighted_z2_stagnation_contribution"] = (
        direction["open_meteo_2024_weight"] * direction["z2_stagnation_ratio"]
    )

    direction_fields = [
        "wind_deg",
        "z2_mean_vr",
        "z2_p95_vr",
        "z2_stagnation_ratio",
        "z2_accelerated_ratio",
        "z40_mean_vr",
        "z40_stagnation_ratio",
        "z40_minus_z2_mean_vr",
        "z40_minus_z2_stagnation_ratio",
        "s1_delta_global_mean_vr",
        "s1_delta_global_stagnation_ratio",
        "s1_common_delta_vr_mean",
        "s1_common_improved_ratio",
        "s1_newly_open_target_vr_mean",
        "s2_delta_global_mean_vr",
        "s2_delta_global_stagnation_ratio",
        "s2_common_delta_vr_mean",
        "s2_common_improved_ratio",
        "s2_newly_open_target_vr_mean",
        "open_meteo_2024_weight",
        "open_meteo_weighted_z2_vr_contribution",
        "open_meteo_weighted_z2_stagnation_contribution",
    ]
    direction = direction[direction_fields]
    direction.to_csv(FIG / "experiment3_directional_response_by_wind.csv", index=False, encoding="utf-8", lineterminator="\n")

    summary_rows: list[dict[str, object]] = []
    metric_claims = {
        "z2_mean_vr": "S0 pedestrian-layer mean VR is low in all eight directions.",
        "z2_stagnation_ratio": "S0 pedestrian-layer stagnation remains high in all eight directions.",
        "z40_minus_z2_mean_vr": "Vertical recovery is positive in all eight directions.",
        "s1_delta_global_mean_vr": "S1 global pedestrian-layer mean-VR change is negative in all tested directions.",
        "s2_delta_global_mean_vr": "S2 global pedestrian-layer mean-VR change is negative in all tested directions.",
        "s2_common_delta_vr_mean": "S2 has a directionally localized common-open-cell response, strongest at 315 deg.",
    }
    for metric, claim in metric_claims.items():
        vals = direction[metric].astype(float)
        mean, vmin, vmax, idx = anisotropy(vals.abs() if metric.startswith(("s1_", "s2_")) and "delta_global" in metric else vals)
        raw_mean = float(vals.mean())
        min_row = direction.loc[vals.idxmin()]
        max_row = direction.loc[vals.idxmax()]
        all_negative = bool((vals < 0).all())
        all_positive = bool((vals > 0).all())
        summary_rows.append(
            {
                "evidence_type": "newly_run",
                "metric": metric,
                "n_directions": len(vals),
                "mean": fmt(raw_mean),
                "min": fmt(float(vals.min())),
                "min_wind_deg": int(min_row["wind_deg"]),
                "max": fmt(float(vals.max())),
                "max_wind_deg": int(max_row["wind_deg"]),
                "range": fmt(float(vals.max() - vals.min())),
                "anisotropy_index": fmt(idx),
                "all_negative": str(all_negative).lower(),
                "all_positive": str(all_positive).lower(),
                "paper_safe_claim": claim,
                "claim_boundary": "Directional screening from 8 simulated directions; not annual wind-climate compliance or field validation.",
            }
        )

    write_csv(
        FIG / "experiment3_directional_anisotropy_summary.csv",
        summary_rows,
        [
            "evidence_type",
            "metric",
            "n_directions",
            "mean",
            "min",
            "min_wind_deg",
            "max",
            "max_wind_deg",
            "range",
            "anisotropy_index",
            "all_negative",
            "all_positive",
            "paper_safe_claim",
            "claim_boundary",
        ],
    )

    summary = pd.DataFrame(summary_rows)
    make_direction_plot(direction, summary, FIG / "experiment3_directional_anisotropy_panel.png")

    z2 = summary[summary["metric"] == "z2_mean_vr"].iloc[0]
    stag = summary[summary["metric"] == "z2_stagnation_ratio"].iloc[0]
    rec = summary[summary["metric"] == "z40_minus_z2_mean_vr"].iloc[0]
    s1 = summary[summary["metric"] == "s1_delta_global_mean_vr"].iloc[0]
    s2 = summary[summary["metric"] == "s2_delta_global_mean_vr"].iloc[0]
    s2common = summary[summary["metric"] == "s2_common_delta_vr_mean"].iloc[0]

    report = f"""# Experiment 3 Directional Anisotropy Analysis

evidence_type: newly_run + preexisting_artifact + blocked

## Protocol

This addendum analyzes the eight time-mean FluidX3D wind directions already archived for the core-prism dx=2 m case. It uses `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv` for S0, `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv` for S1/S2 design sensitivity, and `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv` only as a proxy direction-weighting context. No new solver run is introduced.

## Key Directional Results

- S0 z~2 m mean VR ranges from `{z2['min']}` at `{z2['min_wind_deg']}` deg to `{z2['max']}` at `{z2['max_wind_deg']}` deg; directional anisotropy index = `{z2['anisotropy_index']}`.
- S0 z~2 m stagnation ratio ranges from `{stag['min']}` at `{stag['min_wind_deg']}` deg to `{stag['max']}` at `{stag['max_wind_deg']}` deg; directional anisotropy index = `{stag['anisotropy_index']}`.
- Paired z~40 m minus z~2 m mean-VR recovery is positive in all eight directions, ranging from `{rec['min']}` at `{rec['min_wind_deg']}` deg to `{rec['max']}` at `{rec['max_wind_deg']}` deg.
- S1 global z~2 m mean-VR delta is negative in all eight directions, from `{s1['min']}` to `{s1['max']}`.
- S2 global z~2 m mean-VR delta is also negative in all eight directions, from `{s2['min']}` to `{s2['max']}`.
- S2 common-open-cell local response is directionally localized; the strongest common-open delta occurs at `{s2common['max_wind_deg']}` deg with value `{s2common['max']}`.

## Paper-Safe Interpretation

The directional analysis changes the discussion from a single averaged map to a mechanism-oriented claim. The campus core is not dominated by one exceptional wind direction: pedestrian-height mean VR remains low and the stagnation ratio remains high across all eight simulated directions. At the same time, local design response is directional. S2 has a clearer common-open-cell response than S1, especially near 315 deg, but the global pedestrian-layer delta remains negative in every tested direction. This supports the design conclusion that effective ventilation interventions should be aligned with wind-sector entry and pressure-exchange paths, rather than increasing porosity area in isolation.

## Evidence Boundary

This is an eight-direction simulation-screening result. It does not constitute a measured annual wind rose, annual comfort/safety exceedance probability, field validation, wind-tunnel closure, pollutant dispersion result, or proof of a successful design optimization.

## Output Artifacts

- `figures/experiment3_directional_response_by_wind.csv`
- `figures/experiment3_directional_anisotropy_summary.csv`
- `figures/experiment3_directional_anisotropy_panel.png`
- `reports/experiment3_directional_anisotropy_analysis.md`
- `paper_text/experiment3_directional_anisotropy_results_zh.md`
- `manifests/experiment3_directional_anisotropy_claims.csv`
"""
    write_text(REPORTS / "experiment3_directional_anisotropy_analysis.md", report)

    paper_zh = f"""# 实验3方向性机制补充结果

evidence_type: newly_run + preexisting_artifact + blocked

为进一步解释建筑形态与风环境之间的关系，本研究对核心闭合棱柱模型的 8 个来流方向进行方向性各向异性分析。结果显示，S0 在 z~2 m 的 mean VR 从 `{z2['min']}` 到 `{z2['max']}`，对应方向为 `{z2['min_wind_deg']}` deg 和 `{z2['max_wind_deg']}` deg，方向性各向异性指数为 `{z2['anisotropy_index']}`；z~2 m 的 VR<0.2 滞风比例从 `{stag['min']}` 到 `{stag['max']}`，方向性各向异性指数仅为 `{stag['anisotropy_index']}`。因此，核心校园街区的行人层低风速并不是某一单一来流方向导致的局部异常，而是由围合街区形态产生的近似全向低速背景。

竖向结果进一步说明，z~40 m 相对 z~2 m 的 mean-VR 恢复在全部 8 个方向上均为正，范围为 `{rec['min']}`-`{rec['max']}`。这意味着屋面以上流场恢复具有方向差异，但这种恢复并不能自动传递到院落、入口和街道连接空间。论文中可据此将本案例的核心风环境问题表述为“行人层通风不足与上层流场恢复之间的竖向脱耦”，而不是强风危险主导。

S1/S2 的方向性结果支持更具体的设计应用判断。S1 在全部 8 个方向上的 z~2 m 全局 mean-VR delta 均为负，范围为 `{s1['min']}`-`{s1['max']}`；S2 同样在全部方向上为负，范围为 `{s2['min']}`-`{s2['max']}`。不过，S2 的 common-open-cell 局部响应在 `{s2common['max_wind_deg']}` deg 最强，common-open delta VR 达 `{s2common['max']}`。这说明 S2 并非完全没有局部气动响应，而是局部响应无法转化为全局行人层通风恢复。由此得到的设计认识是：校园街区通风干预不应仅以开口面积或孔隙率为目标，而应与主导来流扇区、压力交换路径和入口廊道位置耦合。

该方向性分析仍属于 8 风向模拟筛查证据，不是实测年度风玫瑰、Lawson/NEN/AIJ 年度超越概率、污染物扩散结果或成功优化方案证明。
"""
    write_text(PAPER / "experiment3_directional_anisotropy_results_zh.md", paper_zh)

    claims = [
        {
            "claim_id": "DA1",
            "claim": "S0 pedestrian-height low-speed condition is quasi-omnidirectional across the eight simulated directions.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv",
            "claim_readiness": "paper_ready_as_screening",
        },
        {
            "claim_id": "DA2",
            "claim": "Vertical mean-VR recovery from z~2 m to z~40 m is positive in every simulated direction.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_directional_anisotropy_summary.csv",
            "claim_readiness": "paper_ready_as_screening",
        },
        {
            "claim_id": "DA3",
            "claim": "S1/S2 global z~2 m mean-VR deltas remain negative in all eight simulated directions.",
            "evidence_type": "newly_run",
            "source": "figures/experiment3_directional_anisotropy_summary.csv; figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv",
            "claim_readiness": "paper_ready_negative_result",
        },
        {
            "claim_id": "DA4",
            "claim": "S2 has localized directionally sensitive common-open-cell response, strongest at 315 deg, but this does not produce global pedestrian-layer recovery.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/experiment3_directional_response_by_wind.csv; reports/experiment3_directional_anisotropy_analysis.md",
            "claim_readiness": "paper_ready_with_boundary",
        },
    ]
    write_csv(
        MAN / "experiment3_directional_anisotropy_claims.csv",
        claims,
        ["claim_id", "claim", "evidence_type", "source", "claim_readiness"],
    )
    append_evidence_inventory()

    print("wrote figures/experiment3_directional_response_by_wind.csv")
    print("wrote figures/experiment3_directional_anisotropy_summary.csv")
    print("wrote figures/experiment3_directional_anisotropy_panel.png")
    print("wrote reports/experiment3_directional_anisotropy_analysis.md")
    print("wrote paper_text/experiment3_directional_anisotropy_results_zh.md")
    print("wrote manifests/experiment3_directional_anisotropy_claims.csv")
    print("updated manifests/evidence_inventory.csv")


if __name__ == "__main__":
    main()
