import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REPORTS = ROOT / "reports"
PAPER = ROOT / "paper_text"


def pct(x):
    return f"{100.0 * x:.2f}%"


def num(x, digits=4):
    return f"{x:.{digits}f}"


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(map(str, row)) + " |")
    return "\n".join(lines)


def weighted_mean(df, value_col, weight_col="open_cells"):
    total = df[weight_col].sum()
    return (df[value_col] * df[weight_col]).sum() / total


def main():
    metrics = pd.read_csv(FIG / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    eq = metrics[metrics["averaging"] == "time_mean_3_samples_then_direction_mean"].copy()
    eq = eq.sort_values("z_height_m_approx")
    weighted = pd.read_csv(FIG / "fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv")
    directional = pd.read_csv(FIG / "fluidx3d_core_prism_deepened_directional_summary.csv")
    robustness = pd.read_csv(FIG / "fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv")
    dist = pd.read_csv(FIG / "paraview_vtk_core_dx2m_building_distance_stats.csv")
    corr = pd.read_csv(FIG / "basic_morphology_parameter_correlations.csv")
    tert = pd.read_csv(FIG / "basic_morphology_parameter_tertile_wind_response.csv")
    windrose = pd.read_csv(MAN / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv")
    gcri = pd.read_csv(MAN / "gcri_scoring_table.csv")

    # Vertical structure.
    vrows = [["height_m", "vr_mean", "vr_p95", "stagnation_ratio", "acceleration_ratio_gt_0p6", "mean_vr_gain_vs_2m", "stagnation_drop_vs_2m"]]
    base_vr = eq.iloc[0]["vr_mean"]
    base_stag = eq.iloc[0]["stagnation_ratio_vr_lt_0p2"]
    for _, r in eq.iterrows():
        vrows.append([
            num(r["z_height_m_approx"], 1),
            num(r["vr_mean"], 6),
            num(r["vr_p95"], 6),
            num(r["stagnation_ratio_vr_lt_0p2"], 6),
            num(r["accelerated_ratio_vr_gt_0p6"], 6),
            num(r["vr_mean"] / base_vr, 3),
            num(base_stag - r["stagnation_ratio_vr_lt_0p2"], 6),
        ])
    write_csv(FIG / "detailed_conclusion_vertical_gradient.csv", vrows)

    # Equal vs climate-proxy weighted comparison.
    cw = eq.merge(weighted, on="z_height_m_approx", suffixes=("_equal8", "_openmeteo"))
    crows = [["height_m", "vr_mean_equal8", "vr_mean_openmeteo", "delta_vr_mean", "delta_vr_mean_pct_of_equal", "stagnation_equal8", "stagnation_openmeteo", "delta_stagnation"]]
    for _, r in cw.iterrows():
        delta = r["vr_mean_openmeteo"] - r["vr_mean_equal8"]
        crows.append([
            num(r["z_height_m_approx"], 1),
            num(r["vr_mean_equal8"], 6),
            num(r["vr_mean_openmeteo"], 6),
            num(delta, 6),
            num(delta / r["vr_mean_equal8"], 4),
            num(r["stagnation_ratio_vr_lt_0p2_equal8"], 6),
            num(r["stagnation_ratio_vr_lt_0p2_openmeteo"], 6),
            num(r["stagnation_ratio_vr_lt_0p2_openmeteo"] - r["stagnation_ratio_vr_lt_0p2_equal8"], 6),
        ])
    write_csv(FIG / "detailed_conclusion_climate_weighting_delta.csv", crows)

    # Directional extremes by height.
    drows = [["height_m", "metric", "min_wind_deg", "min_value", "max_wind_deg", "max_value", "absolute_range"]]
    for height, group in directional.groupby("height_m"):
        for col in ["vr_mean", "vr_p95", "stagnation_ratio_vr_lt_0p2", "accelerated_ratio_vr_gt_0p6"]:
            mn = group.loc[group[col].idxmin()]
            mx = group.loc[group[col].idxmax()]
            drows.append([num(height, 1), col, int(mn["wind_deg"]), num(mn[col], 6), int(mx["wind_deg"]), num(mx[col], 6), num(mx[col] - mn[col], 6)])
    write_csv(FIG / "detailed_conclusion_directional_extremes.csv", drows)

    # Building-distance gradient at pedestrian height.
    order = {"0-4m": 0, "4-10m": 1, "10-20m": 2, ">20m": 3}
    grows = [["distance_bin", "weighted_mean_vr", "weighted_p95_vr", "weighted_stagnation_ratio", "weighted_acceleration_ratio", "open_cells_total"]]
    distance_summary = []
    for b, group in sorted(dist.groupby("distance_to_building_bin"), key=lambda item: order.get(item[0], 99)):
        total = int(group["open_cells"].sum())
        row = {
            "distance_bin": b,
            "weighted_mean_vr": weighted_mean(group, "mean_vr"),
            "weighted_p95_vr": weighted_mean(group, "p95_vr"),
            "weighted_stagnation_ratio": weighted_mean(group, "stagnation_ratio_vr_lt_0p2"),
            "weighted_acceleration_ratio": weighted_mean(group, "acceleration_ratio_vr_gt_0p6"),
            "open_cells_total": total,
        }
        distance_summary.append(row)
        grows.append([b, num(row["weighted_mean_vr"], 6), num(row["weighted_p95_vr"], 6), num(row["weighted_stagnation_ratio"], 6), num(row["weighted_acceleration_ratio"], 6), total])
    write_csv(FIG / "detailed_conclusion_building_distance_gradient.csv", grows)

    # Morphology effects: strongest correlations and high-low tertile effect.
    corr_nonnull = corr.dropna(subset=["spearman_rho"]).copy()
    corr_nonnull["abs_rho"] = corr_nonnull["spearman_rho"].abs()
    top_corr = corr_nonnull.sort_values("abs_rho", ascending=False).head(16)
    cor_rows = [["analysis_zone", "parameter_label", "response_metric", "spearman_rho", "p_value", "n_components"]]
    for _, r in top_corr.iterrows():
        cor_rows.append([r["analysis_zone"], r["parameter_label"], r["response_metric"], num(r["spearman_rho"], 6), f"{r['p_value']:.3e}", int(r["n_components"])])
    write_csv(FIG / "detailed_conclusion_top_morphology_correlations.csv", cor_rows)

    agg_rows = []
    for (zone, parameter, label, tertile_name), group in tert.groupby(["analysis_zone", "parameter", "parameter_label", "tertile"]):
        total = group["sample_open_cells"].sum()
        agg_rows.append({
            "analysis_zone": zone,
            "parameter": parameter,
            "parameter_label": label,
            "tertile": tertile_name,
            "mean_vr": weighted_mean(group, "mean_vr", "sample_open_cells"),
            "p95_vr": weighted_mean(group, "p95_vr", "sample_open_cells"),
            "stagnation_ratio": weighted_mean(group, "stagnation_ratio_vr_lt_0p2", "sample_open_cells"),
            "sample_open_cells": int(total),
        })
    agg = pd.DataFrame(agg_rows)
    effect_rows = [["analysis_zone", "parameter_label", "low_mean_vr", "high_mean_vr", "delta_high_minus_low", "relative_change_high_vs_low", "low_p95_vr", "high_p95_vr"]]
    effect_records = []
    for (zone, parameter, label), group in agg.groupby(["analysis_zone", "parameter", "parameter_label"]):
        if {"low", "high"}.issubset(set(group["tertile"])):
            low = group[group["tertile"] == "low"].iloc[0]
            high = group[group["tertile"] == "high"].iloc[0]
            delta = high["mean_vr"] - low["mean_vr"]
            rel = delta / low["mean_vr"] if low["mean_vr"] else 0.0
            effect_records.append({
                "analysis_zone": zone,
                "parameter_label": label,
                "low_mean_vr": low["mean_vr"],
                "high_mean_vr": high["mean_vr"],
                "delta_high_minus_low": delta,
                "relative_change_high_vs_low": rel,
                "low_p95_vr": low["p95_vr"],
                "high_p95_vr": high["p95_vr"],
            })
    effect = pd.DataFrame(effect_records).sort_values("delta_high_minus_low", key=lambda s: s.abs(), ascending=False)
    for _, r in effect.iterrows():
        effect_rows.append([r["analysis_zone"], r["parameter_label"], num(r["low_mean_vr"], 6), num(r["high_mean_vr"], 6), num(r["delta_high_minus_low"], 6), num(r["relative_change_high_vs_low"], 4), num(r["low_p95_vr"], 6), num(r["high_p95_vr"], 6)])
    write_csv(FIG / "detailed_conclusion_morphology_tertile_effects.csv", effect_rows)

    # Geometry readiness.
    photo_gcri = float(gcri.loc[gcri["geometry_id"] == "user_photogrammetry_fullres_stl", "GCRI"].iloc[0])
    core_gcri = float(gcri.loc[gcri["geometry_id"] == "core_photogrammetry_extent_prism_collision_z0", "GCRI"].iloc[0])
    district_gcri = float(gcri.loc[gcri["geometry_id"] == "district_prism_collision_z0", "GCRI"].iloc[0])
    lod3_direct = float(gcri.loc[gcri["geometry_id"] == "lod3_direct_obj_collision_candidate", "GCRI"].iloc[0])

    # Pull named robustness metrics.
    rob = dict(zip(robustness["metric"], robustness["value"]))
    top3_weight = windrose.sort_values("weight", ascending=False).head(3)["weight"].sum()
    top2_weight = windrose.sort_values("weight", ascending=False).head(2)["weight"].sum()
    dominant_dirs = ", ".join(map(str, windrose.sort_values("weight", ascending=False).head(3)["simulated_velocity_direction_deg"].astype(int).tolist()))

    claim_rows = [
        ["conclusion_id", "paper_ready_claim", "key_numbers", "evidence_type", "source_files", "claim_readiness"],
        ["C1", "The campus core has a strongly sheltered pedestrian layer, with low-speed areas dominating the z≈2 m plane.", f"z=2 m mean VR={num(eq.iloc[0]['vr_mean'],3)}, stagnation={pct(eq.iloc[0]['stagnation_ratio_vr_lt_0p2'])}", "newly_run", "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv", "paper_ready_as_screening"],
        ["C2", "Wind-speed recovery is strongly vertical: meaningful recovery appears above the pedestrian layer and becomes dominant around 20-40 m.", f"mean VR: 2 m {num(eq.iloc[0]['vr_mean'],3)}; 10 m {num(eq[eq['z_height_m_approx']==10]['vr_mean'].iloc[0],3)}; 20 m {num(eq[eq['z_height_m_approx']==20]['vr_mean'].iloc[0],3)}; 40 m {num(eq.iloc[-1]['vr_mean'],3)}", "newly_run", "detailed_conclusion_vertical_gradient.csv", "paper_ready_as_screening"],
        ["C3", "At pedestrian height, the stagnation pattern is directionally robust rather than controlled by a single dominant wind direction.", f"all-direction stagnation area={pct(rob['all_direction_stagnation_ratio'])}; robust-stagnation frequency>=0.75 area={pct(rob['robust_stagnation_ratio_freq_ge_0p75'])}", "newly_run", "fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv", "paper_ready_as_screening"],
        ["C4", "Open-Meteo weighting changes the screened mean VR only slightly, so it is useful as a climate-proxy sensitivity layer but not formal validation.", f"top-3 proxy directions {dominant_dirs} sum={pct(top3_weight)}; z=2 m delta mean VR={num(cw.iloc[0]['vr_mean_openmeteo']-cw.iloc[0]['vr_mean_equal8'],4)}", "newly_run + preexisting_artifact", "open_meteo weights and weighted metrics", "weaken_claim"],
        ["C5", "The immediate facade band is almost fully sheltered; distance from buildings controls recovery but does not remove low-speed dominance within the modeled campus core.", f"0-4 m mean VR={num(distance_summary[0]['weighted_mean_vr'],4)}, stagnation={pct(distance_summary[0]['weighted_stagnation_ratio'])}; >20 m mean VR={num(distance_summary[-1]['weighted_mean_vr'],4)}, stagnation={pct(distance_summary[-1]['weighted_stagnation_ratio'])}", "newly_run", "detailed_conclusion_building_distance_gradient.csv", "paper_ready_as_screening"],
        ["C6", "Local enclosure and local built fraction explain wind-response differences better than footprint area, elongation, or compactness in this cropped campus model.", "20-50 m sector enclosure rho=-0.396; relative enclosure high-vs-low mean VR change=-53.7%", "newly_run", "basic_morphology_parameter_correlations.csv; detailed_conclusion_morphology_tertile_effects.csv", "paper_ready_as_screening"],
        ["C7", "The digital-twin workflow shows a geometry-readiness gap: visual photogrammetry and CFD collision geometry must be separated.", f"GCRI photogrammetry={num(photo_gcri,3)}; core prism={num(core_gcri,3)}; district prism={num(district_gcri,3)}; LoD3 direct={num(lod3_direct,3)}", "newly_run", "gcri_scoring_table.csv", "paper_ready_as_method_contribution"],
        ["C8", "Pollutant dispersion, successful S1/S2 design improvement, GCBTE, and formal comfort/safety exceedance remain unsupported.", "no scalar transport; S1/S2 are simulated but near-null/negative; no 3DGS boundary extraction; no measured wind rose", "blocked", "design_scenario_manifest.csv; s1_design_intervention_claims.csv; s2_design_intervention_claims.csv; gcbte_status_table.csv; claim_boundary.md", "blocked"],
    ]
    write_csv(MAN / "detailed_conclusion_claims.csv", claim_rows)

    vertical_table = md_table(
        ["高度", "mean VR", "P95 VR", "滞风比例", "VR>0.6比例", "相对2 m均值倍数"],
        [[r[0], r[1], r[2], pct(float(r[3])), pct(float(r[4])), r[5]] for r in vrows[1:]],
    )
    climate_table = md_table(
        ["高度", "8风向mean VR", "Open-Meteo mean VR", "均值差", "滞风比例差"],
        [[r[0], r[1], r[2], r[3], r[7]] for r in crows[1:]],
    )
    distance_table = md_table(
        ["距建筑", "mean VR", "P95 VR", "滞风比例", "VR>0.6比例"],
        [[r[0], r[1], r[2], pct(float(r[3])), pct(float(r[4]))] for r in grows[1:]],
    )
    morph_table = md_table(
        ["分析带", "形态参数", "响应指标", "Spearman rho", "p值"],
        [[r[0], r[1], r[2], r[3], r[4]] for r in cor_rows[1:9]],
    )
    effect_table = md_table(
        ["分析带", "参数", "低组mean VR", "高组mean VR", "高-低变化", "相对变化"],
        [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in effect_rows[1:9]],
    )

    report = f"""# Detailed Data Synthesis for Paper Conclusions

evidence_type: newly_run + preexisting_artifact + blocked

This report consolidates the existing FluidX3D, ParaView, morphology, Open-Meteo proxy, and geometry-readiness artifacts into paper-ready conclusions. No new CFD field is invented here; all numbers are derived from archived CSV artifacts.

## 1. Vertical Wind-Response Structure

{vertical_table}

Interpretation: the strongest manuscript conclusion is a vertical decoupling between the pedestrian layer and the upper flow. At z≈2 m, mean VR is only `{num(eq.iloc[0]['vr_mean'], 3)}` and `{pct(eq.iloc[0]['stagnation_ratio_vr_lt_0p2'])}` of open cells fall below VR<0.2. By z≈20 m, mean VR rises to `{num(eq[eq['z_height_m_approx']==20]['vr_mean'].iloc[0], 3)}`, while at z≈40 m the open layer is essentially above the low-speed threshold. This supports a campus-canyon interpretation: above-canopy flow recovery does not directly translate into pedestrian ventilation.

## 2. Directional Robustness

At z≈2 m, the directional mean VR range is only `{num(directional[directional['height_m']==2]['vr_mean'].max() - directional[directional['height_m']==2]['vr_mean'].min(), 4)}`, while the stagnation ratio varies by only `{pct(directional[directional['height_m']==2]['stagnation_ratio_vr_lt_0p2'].max() - directional[directional['height_m']==2]['stagnation_ratio_vr_lt_0p2'].min())}` across eight wind directions. The spatial robustness table further shows all-direction stagnation over `{pct(rob['all_direction_stagnation_ratio'])}` of the pedestrian plane and robust stagnation frequency >=0.75 over `{pct(rob['robust_stagnation_ratio_freq_ge_0p75'])}`.

This means that the main z≈2 m conclusion is not a single-wind-direction artifact. The campus core geometry produces a stable low-ventilation footprint across wind directions.

## 3. Climate-Proxy Weighting

{climate_table}

Open-Meteo 2024 proxy data concentrate `{pct(top2_weight)}` of hours in the two largest velocity-to sectors and `{pct(top3_weight)}` in the three largest sectors (`{dominant_dirs}` degrees). However, applying those weights changes the z≈2 m mean VR by only `{num(cw.iloc[0]['vr_mean_openmeteo'] - cw.iloc[0]['vr_mean_equal8'], 4)}` and the z≈2 m stagnation ratio by `{num(cw.iloc[0]['stagnation_ratio_vr_lt_0p2_openmeteo'] - cw.iloc[0]['stagnation_ratio_vr_lt_0p2_equal8'], 4)}`. The proxy weighting is therefore useful for sensitivity discussion, but not a substitute for measured wind rose or formal exceedance-probability comfort assessment.

## 4. Distance-to-Building Gradient

{distance_table}

The distance-gradient result sharpens the architectural conclusion. The 0-4 m, 4-10 m, and 10-20 m bands are almost fully low-speed zones, while the >20 m band recovers to mean VR `{num(distance_summary[-1]['weighted_mean_vr'], 3)}` but still keeps `{pct(distance_summary[-1]['weighted_stagnation_ratio'])}` below VR<0.2. Thus, the wind-environment issue is not restricted to an immediate facade boundary layer; it propagates into the block-scale pedestrian network.

## 5. Building-Morphology Explanation

{morph_table}

The strongest shape-response relationships come from local context parameters rather than from simple object dimensions. In the 20-50 m band, sector enclosure has Spearman rho `-0.396` with mean VR, while mean height has rho `-0.351` and combined enclosure has rho `-0.302`. Footprint area, elongation, and perimeter-area compactness are weak for mean VR in this cropped campus setting.

{effect_table}

The high-vs-low tertile table gives the most intuitive design reading: high combined enclosure in the 20-50 m band reduces mean VR from `{num(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['low_mean_vr'].iloc[0], 4)}` to `{num(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['high_mean_vr'].iloc[0], 4)}`, a relative change of `{pct(abs(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['relative_change_high_vs_low'].iloc[0]))}`. High local built fraction produces a similarly strong reduction. The paper should therefore discuss courtyard enclosure, passage continuity, and near-ground porosity before treating height or footprint as primary explanatory variables.

## 6. Digital-Twin Model Performance

The GCRI table supports a separate digital-twin conclusion. The visual photogrammetry STL scores `{num(photo_gcri, 3)}`, while the accepted core and district prism collision geometries score `{num(core_gcri, 3)}` and `{num(district_gcri, 3)}`. The direct LoD3 OBJ candidate scores `{num(lod3_direct, 3)}` before repair. This shows that visual fidelity and CFD readiness are not equivalent: a digital twin can be visually consistent with the study block but still fail as a closed, voxelizable collision boundary.

## 7. Detailed Paper Conclusions

1. The current TUM2TWIN campus-core result should be framed as a robust low-ventilation screening result: z≈2 m low-speed dominance persists across all eight wind directions.
2. The vertical profile indicates a strong pedestrian/upper-flow decoupling. Wind recovery appears at 10-20 m and becomes dominant by 40 m, but that recovery does not solve pedestrian-layer stagnation.
3. Building distance matters, but the recovery length is larger than the immediate facade zone. Even cells farther than 20 m from buildings remain mostly below VR<0.2 in this cropped core.
4. Local enclosure and built fraction are more explanatory than footprint area, elongation, or compactness. The practical design target is therefore releasing enclosure and improving passage connectivity, not only reducing isolated building height.
5. Open-Meteo weighting barely changes the main screening result. This strengthens the internal robustness of the geometric interpretation but must not be written as measured climate validation.
6. The digital-twin contribution is methodological: the study demonstrates a separation between visual digital-twin assets and CFD-ready collision assets, quantified through GCRI.

## 8. Claims That Must Stay Limited

- No field-measured or wind-tunnel validation is available.
- No formal Lawson/NEN/AIJ comfort-safety exceedance assessment is supported.
- No pollutant dispersion result is available.
- S1 ventilation-relief and S2 network-porosity have been simulated, but both are near-null/negative design-sensitivity results rather than proof of successful optimization; S3-Sn interventions remain future work.
- No GCBTE value is computed because no independent 3DGS-derived collision boundary extraction exists.
- No completed Rhino-Grasshopper/CityLBM end-to-end run is claimed; the current positioning remains FluidX3D-native with a CityLBM-compatible geometry package.

## Output Tables

- `figures/detailed_conclusion_vertical_gradient.csv`
- `figures/detailed_conclusion_climate_weighting_delta.csv`
- `figures/detailed_conclusion_directional_extremes.csv`
- `figures/detailed_conclusion_building_distance_gradient.csv`
- `figures/detailed_conclusion_top_morphology_correlations.csv`
- `figures/detailed_conclusion_morphology_tertile_effects.csv`
- `manifests/detailed_conclusion_claims.csv`
"""
    (REPORTS / "detailed_data_synthesis_for_paper_conclusions.md").write_text(report.rstrip() + "\n", encoding="utf-8", newline="\n")

    paper = f"""# 详细论文结论段落

evidence_type: newly_run + preexisting_artifact + blocked

本实验的结果表明，TUM2TWIN 校园核心街区的近地风环境主要表现为方向稳健的低通风格局，而不是由单一来流方向造成的局部偶发现象。在 dx=2 m 的 FluidX3D 八风向时间平均结果中，z≈2 m 行人高度的平均风速比仅为 {num(eq.iloc[0]['vr_mean'], 3)}，VR<0.2 的低风速面积比例达到 {pct(eq.iloc[0]['stagnation_ratio_vr_lt_0p2'])}。进一步的方向鲁棒性统计显示，八个风向之间 z≈2 m mean VR 的绝对范围仅为 {num(directional[directional['height_m']==2]['vr_mean'].max() - directional[directional['height_m']==2]['vr_mean'].min(), 4)}，且 {pct(rob['all_direction_stagnation_ratio'])} 的行人平面在所有风向下均保持低风速状态。这说明该区域的核心问题并非某个主导风向下的孤立涡区，而是由校园街区围合、连续建筑边界和近地通道连通性不足共同形成的稳定遮蔽结构。

竖向结果进一步揭示了行人层与上部流场的脱耦关系。平均 VR 从 z≈2 m 的 {num(eq.iloc[0]['vr_mean'], 3)} 增至 z≈10 m 的 {num(eq[eq['z_height_m_approx']==10]['vr_mean'].iloc[0], 3)}、z≈20 m 的 {num(eq[eq['z_height_m_approx']==20]['vr_mean'].iloc[0], 3)}，并在 z≈40 m 达到 {num(eq.iloc[-1]['vr_mean'], 3)}；与此同时，VR<0.2 的面积比例由 {pct(eq.iloc[0]['stagnation_ratio_vr_lt_0p2'])} 降至 z≈10 m 的 {pct(eq[eq['z_height_m_approx']==10]['stagnation_ratio_vr_lt_0p2'].iloc[0])}，到 z≈40 m 已接近 0。该结果说明，上部或屋面高度的风速恢复并不能直接代表行人高度通风改善；对于校园步行空间、入口广场和院落界面，仍需单独评价近地层的通风连通。

从建筑距离看，风速恢复不是简单发生在离开立面后的短距离内。距建筑 0-4 m、4-10 m 和 10-20 m 的平均 VR 分别只有 {num(distance_summary[0]['weighted_mean_vr'], 4)}、{num(distance_summary[1]['weighted_mean_vr'], 4)} 和 {num(distance_summary[2]['weighted_mean_vr'], 4)}，低风速比例几乎为 100%；即使在 >20 m 的开放单元中，平均 VR 也仅恢复到 {num(distance_summary[-1]['weighted_mean_vr'], 3)}，仍有 {pct(distance_summary[-1]['weighted_stagnation_ratio'])} 的区域低于 VR<0.2。这一发现把传统“街谷遮蔽”判断推进到更具体的设计尺度：校园核心区的风环境改善不应只处理贴近建筑的立面边界，而应关注院落、连廊、街道转角与开放空间之间 20-50 m 尺度的通风路径组织。

建筑形态统计进一步表明，在该尺度下，局地围合和建成比例比单体几何尺寸更能解释风环境差异。在 20-50 m 局地背景带中，50 m 扇区围合度与 mean VR 的 Spearman 相关系数为 -0.396，平均高度为 -0.351，综合围合度为 -0.302；相比之下，建筑 footprint area、elongation ratio 和 perimeter-area compactness 对 mean VR 的解释力较弱。分位组比较也显示，高综合围合度组的 mean VR 从低组的 {num(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['low_mean_vr'].iloc[0], 4)} 降至 {num(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['high_mean_vr'].iloc[0], 4)}，相对降低约 {pct(abs(effect[(effect['analysis_zone']=='local_context_20_50m') & (effect['parameter_label']=='combined enclosure score')]['relative_change_high_vs_low'].iloc[0]))}。因此，本实验在传统“高密度、围合街谷容易形成低风速”的认识基础上进一步指出：对于真实校园数字孪生街区，更有解释力的不是抽象的 LCZ 类别或单体高度，而是局地建成比例、围合连续性和近地通风路径是否被切断。

Open-Meteo 2024 方向权重仅作为气候代理使用。虽然 90°、45° 和 270° 三个 velocity-to 方向合计占 {pct(top3_weight)}，但与八风向等权平均相比，Open-Meteo 加权后 z≈2 m mean VR 只改变 {num(cw.iloc[0]['vr_mean_openmeteo'] - cw.iloc[0]['vr_mean_equal8'], 4)}，低风速比例只改变 {num(cw.iloc[0]['stagnation_ratio_vr_lt_0p2_openmeteo'] - cw.iloc[0]['stagnation_ratio_vr_lt_0p2_equal8'], 4)}。这说明当前低通风结论对方向权重不敏感，但该数据仍不能替代实测风玫瑰，也不能支持正式年度超越概率舒适评价。

数字孪生底层模型的表现可概括为“视觉一致性”和“CFD 就绪性”的分离。用户 photogrammetry STL 能较好对应 TUM Downtown 街区视觉范围，但 GCRI 仅为 {num(photo_gcri, 3)}；经语义/棱柱化处理后的 core collision 和 district collision 分别达到 {num(core_gcri, 3)} 和 {num(district_gcri, 3)}。这说明无人机摄影测量或 3DGS 类视觉资产适合用于场景核验、贴图浏览和空间范围审查，但若要进入 FluidX3D/CityLBM 作为刚性碰撞边界，必须经过语义分层、闭合修复、z0 对齐和体素化检查。该发现构成本实验相对于传统理想化街谷模拟的主要增量：真实数字孪生数据的风环境应用价值不仅来自“更真实的外观”，而来自可追踪地把视觉资产、语义城市模型和 CFD-ready 几何分工组合起来。

上述结论仍属于数字孪生到 CFD 的应用筛查证据。本文不应宣称已完成实测验证、风洞闭环、正式风舒适安全合规评价、污染物扩散预测、S1/S2 设计干预性能提升或 3DGS 边界传递误差实测；S1/S2 已完成数值敏感性比较，但结果均为近零/负向，只能用于说明单条轻量开廊和简单网络孔隙均不足以解决核心区滞风。当前最稳妥的论文定位是：基于 TUM2TWIN 的 FluidX3D-native 校园风环境筛查、建筑形态解释与设计敏感性分析，并附带 CityLBM-compatible 几何准备包。
"""
    (PAPER / "detailed_paper_conclusions_zh.md").write_text(paper.rstrip() + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
