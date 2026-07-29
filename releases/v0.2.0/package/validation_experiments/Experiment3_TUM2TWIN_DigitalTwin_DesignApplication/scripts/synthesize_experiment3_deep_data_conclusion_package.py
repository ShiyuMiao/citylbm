from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"

KEY_FIELDS = [
    "evidence_type",
    "claim_layer",
    "metric",
    "value",
    "source_artifact",
    "paper_safe_claim",
]

CONCLUSION_FIELDS = [
    "conclusion_id",
    "conclusion_layer",
    "main_finding_zh",
    "key_numbers",
    "architectural_interpretation_zh",
    "novelty_over_traditional_claim_zh",
    "evidence_type",
    "source_artifacts",
    "claim_boundary",
    "paper_ready_wording_zh",
]


def fmt(value: object, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def pct(value: object, digits: int = 1) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_dict_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |"]
    lines.append("|" + "|".join(["---"] * len(fields)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    w = df[weight_col].astype(float)
    return float((df[value_col].astype(float) * w).sum() / w.sum())


def upsert_csv(path: Path, row: dict[str, object], fields: list[str], unique_field: str) -> None:
    rows = read_csv(path)
    rows = [item for item in rows if item.get(unique_field) != str(row[unique_field])]
    rows.append({field: row.get(field, "") for field in fields})
    write_dict_csv(path, rows, fields)


def collect_numbers() -> dict[str, object]:
    metrics = pd.read_csv(FIG / "fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    eq = metrics[metrics["averaging"] == "time_mean_3_samples_then_direction_mean"].copy()
    eq = eq.sort_values("z_height_m_approx")
    by_height = {float(r["z_height_m_approx"]): r for _, r in eq.iterrows()}

    directional = pd.read_csv(FIG / "fluidx3d_core_prism_deepened_directional_summary.csv")
    d2 = directional[directional["height_m"] == 2.0].copy()
    d40 = directional[directional["height_m"] == 40.0].copy()

    robustness = pd.read_csv(FIG / "fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv")
    rob = dict(zip(robustness["metric"], robustness["value"]))

    dist = pd.read_csv(FIG / "paraview_vtk_core_dx2m_building_distance_stats.csv")
    order = {"0-4m": 0, "4-10m": 1, "10-20m": 2, ">20m": 3}
    distance_rows = []
    for bin_name, group in sorted(dist.groupby("distance_to_building_bin"), key=lambda item: order[item[0]]):
        distance_rows.append(
            {
                "distance_bin": bin_name,
                "mean_vr": weighted_mean(group, "mean_vr", "open_cells"),
                "p95_vr": weighted_mean(group, "p95_vr", "open_cells"),
                "stagnation_ratio": weighted_mean(group, "stagnation_ratio_vr_lt_0p2", "open_cells"),
                "acceleration_ratio": weighted_mean(group, "acceleration_ratio_vr_gt_0p6", "open_cells"),
                "open_cells": int(group["open_cells"].sum()),
            }
        )

    corr = pd.read_csv(FIG / "basic_morphology_parameter_correlations.csv")
    corr = corr.dropna(subset=["spearman_rho"]).copy()
    corr["abs_rho"] = corr["spearman_rho"].abs()
    top_corr = corr.sort_values("abs_rho", ascending=False).head(12)

    tertile = pd.read_csv(FIG / "basic_morphology_parameter_tertile_wind_response.csv")
    tertile_records = []
    for (zone, parameter, label, tert), group in tertile.groupby(
        ["analysis_zone", "parameter", "parameter_label", "tertile"]
    ):
        tertile_records.append(
            {
                "analysis_zone": zone,
                "parameter": parameter,
                "parameter_label": label,
                "tertile": tert,
                "mean_vr": weighted_mean(group, "mean_vr", "sample_open_cells"),
                "p95_vr": weighted_mean(group, "p95_vr", "sample_open_cells"),
                "stagnation_ratio": weighted_mean(group, "stagnation_ratio_vr_lt_0p2", "sample_open_cells"),
                "open_cells": int(group["sample_open_cells"].sum()),
            }
        )
    tertile_agg = pd.DataFrame(tertile_records)
    effects = []
    for (zone, parameter, label), group in tertile_agg.groupby(["analysis_zone", "parameter", "parameter_label"]):
        if {"low", "high"}.issubset(set(group["tertile"])):
            low = group[group["tertile"] == "low"].iloc[0]
            high = group[group["tertile"] == "high"].iloc[0]
            delta = float(high["mean_vr"] - low["mean_vr"])
            effects.append(
                {
                    "analysis_zone": zone,
                    "parameter": parameter,
                    "parameter_label": label,
                    "low_mean_vr": float(low["mean_vr"]),
                    "high_mean_vr": float(high["mean_vr"]),
                    "delta_high_minus_low": delta,
                    "relative_change": delta / float(low["mean_vr"]) if float(low["mean_vr"]) else 0.0,
                    "low_p95_vr": float(low["p95_vr"]),
                    "high_p95_vr": float(high["p95_vr"]),
                }
            )
    effect_df = pd.DataFrame(effects).sort_values("delta_high_minus_low", key=lambda s: s.abs(), ascending=False)

    stage = pd.read_csv(FIG / "morphology_stage_transition_stage_summary.csv") if (FIG / "morphology_stage_transition_stage_summary.csv").exists() else None
    if stage is None:
        stage = pd.read_csv(FIG / "morphology_directional_fingerprint_stage_summary.csv")
    archetype = pd.read_csv(FIG / "morphology_form_response_archetype_summary.csv")
    s1 = pd.read_csv(FIG / "fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv")
    s2 = pd.read_csv(FIG / "fluidx3d_s0_s2_network_porosity_metric_comparison.csv")
    windrose = pd.read_csv(MAN / "open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv")
    gcri = pd.read_csv(MAN / "gcri_scoring_table.csv")
    uncertainty = pd.read_csv(FIG / "experiment3_effect_size_uncertainty_summary.csv")

    def metric_row(df: pd.DataFrame, metric: str) -> pd.Series:
        row = df[df["metric"] == metric]
        if row.empty:
            raise ValueError(f"Missing metric {metric}")
        return row.iloc[0]

    return {
        "by_height": by_height,
        "d2": d2,
        "d40": d40,
        "rob": rob,
        "distance_rows": distance_rows,
        "top_corr": top_corr,
        "effect_df": effect_df,
        "stage": stage,
        "archetype": archetype,
        "s1_z2": s1[s1["z_height_m_approx"] == 2.0].iloc[0],
        "s2_z2": s2[s2["z_height_m_approx"] == 2.0].iloc[0],
        "windrose": windrose,
        "gcri": gcri,
        "uncertainty": uncertainty,
        "unc_z2_vr": metric_row(uncertainty, "z2_mean_vr"),
        "unc_z2_stag": metric_row(uncertainty, "z2_stagnation_ratio"),
    }


def make_support_tables(n: dict[str, object]) -> None:
    by_height = n["by_height"]
    vertical_rows = []
    z2 = by_height[2.0]
    for h in [2.0, 4.0, 10.0, 20.0, 40.0]:
        row = by_height[h]
        vertical_rows.append(
            {
                "height_m": fmt(h, 1),
                "mean_vr": fmt(row["vr_mean"], 6),
                "p95_vr": fmt(row["vr_p95"], 6),
                "stagnation_ratio_vr_lt_0p2": fmt(row["stagnation_ratio_vr_lt_0p2"], 6),
                "accelerated_ratio_vr_gt_0p6": fmt(row["accelerated_ratio_vr_gt_0p6"], 6),
                "mean_vr_ratio_to_z2": fmt(float(row["vr_mean"]) / float(z2["vr_mean"]), 3),
            }
        )
    write_dict_csv(
        FIG / "experiment3_deep_conclusion_vertical_and_distance_support.csv",
        vertical_rows
        + [
            {
                "height_m": "distance:" + str(r["distance_bin"]),
                "mean_vr": fmt(r["mean_vr"], 6),
                "p95_vr": fmt(r["p95_vr"], 6),
                "stagnation_ratio_vr_lt_0p2": fmt(r["stagnation_ratio"], 6),
                "accelerated_ratio_vr_gt_0p6": fmt(r["acceleration_ratio"], 6),
                "mean_vr_ratio_to_z2": "",
            }
            for r in n["distance_rows"]
        ],
        [
            "height_m",
            "mean_vr",
            "p95_vr",
            "stagnation_ratio_vr_lt_0p2",
            "accelerated_ratio_vr_gt_0p6",
            "mean_vr_ratio_to_z2",
        ],
    )

    corr_rows = []
    for _, r in n["top_corr"].iterrows():
        corr_rows.append(
            {
                "analysis_zone": r["analysis_zone"],
                "parameter_label": r["parameter_label"],
                "response_metric": r["response_metric"],
                "spearman_rho": fmt(r["spearman_rho"], 6),
                "p_value": f"{float(r['p_value']):.3e}",
                "n_components": int(r["n_components"]),
            }
        )
    write_dict_csv(
        FIG / "experiment3_deep_conclusion_morphology_support.csv",
        corr_rows,
        ["analysis_zone", "parameter_label", "response_metric", "spearman_rho", "p_value", "n_components"],
    )


def make_conclusion_rows(n: dict[str, object]) -> list[dict[str, object]]:
    by_height = n["by_height"]
    z2 = by_height[2.0]
    z10 = by_height[10.0]
    z20 = by_height[20.0]
    z40 = by_height[40.0]
    d2 = n["d2"]
    d40 = n["d40"]
    rob = n["rob"]
    dist = {r["distance_bin"]: r for r in n["distance_rows"]}
    top_corr = n["top_corr"].iloc[0]
    effect_df = n["effect_df"]
    stage = n["stage"]
    archetype = n["archetype"]
    s1 = n["s1_z2"]
    s2 = n["s2_z2"]
    windrose = n["windrose"]
    gcri = n["gcri"]
    unc_vr = n["unc_z2_vr"]
    unc_stag = n["unc_z2_stag"]

    enclosure_effect = effect_df[
        (effect_df["analysis_zone"] == "local_context_20_50m")
        & (effect_df["parameter_label"] == "combined enclosure score")
    ].iloc[0]
    built_effect = effect_df[
        (effect_df["analysis_zone"] == "near_facade_0_20m")
        & (effect_df["parameter_label"] == "local built fraction, r=30 m")
    ].iloc[0]
    stage_counts = dict(zip(stage["stage_transition_class"], stage["n_components"])) if "stage_transition_class" in stage else {}
    recovery_stage = stage[stage["stage_transition_class"] == "near_to_context_recovery"].iloc[0]
    persistent_stage = stage[stage["stage_transition_class"] == "persistent_shelter"].iloc[0]
    top_archetype = archetype.sort_values("recovery_rank").iloc[0]
    weakest_archetype = archetype.sort_values("recovery_rank").iloc[-1]
    photo_gcri = float(gcri.loc[gcri["geometry_id"] == "user_photogrammetry_fullres_stl", "GCRI"].iloc[0])
    core_gcri = float(gcri.loc[gcri["geometry_id"] == "core_photogrammetry_extent_prism_collision_z0", "GCRI"].iloc[0])
    district_gcri = float(gcri.loc[gcri["geometry_id"] == "district_prism_collision_z0", "GCRI"].iloc[0])
    top_dirs = windrose.sort_values("weight", ascending=False).head(3)

    return [
        {
            "conclusion_id": "DC1",
            "conclusion_layer": "baseline_vertical_structure",
            "main_finding_zh": "校园核心区行人高度风速比处于强遮蔽状态，而上部流场在20-40 m高度恢复。",
            "key_numbers": f"2 m mean VR={fmt(z2['vr_mean'])}, VR<0.2={pct(z2['stagnation_ratio_vr_lt_0p2'])}; 20 m mean VR={fmt(z20['vr_mean'])}; 40 m mean VR={fmt(z40['vr_mean'])}, VR<0.2={pct(z40['stagnation_ratio_vr_lt_0p2'])}",
            "architectural_interpretation_zh": "高密度校园街区形成近地层遮蔽，上部来流恢复不能直接转化为步行层通风改善。",
            "novelty_over_traditional_claim_zh": "传统结论常强调街谷低风速或背风区，本实验进一步给出同一真实数字孪生街区内的垂向脱耦证据。",
            "evidence_type": "newly_run",
            "source_artifacts": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "claim_boundary": "筛查级FluidX3D结果；非实测验证或正式舒适合规评价。",
            "paper_ready_wording_zh": "结果表明，TUM Downtown校园核心区在2 m行人高度呈现强遮蔽状态，mean VR仅为0.076，VR<0.2区域约占93.4%；但20 m和40 m高度的mean VR分别升至0.602和1.049，说明该街区存在明显的行人层-上部流场脱耦。",
        },
        {
            "conclusion_id": "DC2",
            "conclusion_layer": "directional_robustness",
            "main_finding_zh": "2 m低风速格局不是单一风向造成，而是在八个风向下均较稳定。",
            "key_numbers": f"2 m mean VR range={fmt(d2['vr_mean'].max() - d2['vr_mean'].min(), 4)}; stagnation range={pct(d2['stagnation_ratio_vr_lt_0p2'].max() - d2['stagnation_ratio_vr_lt_0p2'].min(), 2)}; all-direction stagnation={pct(rob['all_direction_stagnation_ratio'])}",
            "architectural_interpretation_zh": "围合街区对行人层的削弱具有准全向性，设计判断不宜只围绕一个主导风向展开。",
            "novelty_over_traditional_claim_zh": "传统风环境常按主导风向解释风廊和背风区；本结果提示在校园围合街区中，主导问题可能是多风向共同存在的低通风底图。",
            "evidence_type": "newly_run",
            "source_artifacts": "figures/fluidx3d_core_prism_deepened_directional_summary.csv; figures/fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv",
            "claim_boundary": "八风向筛查，不等于年度超越概率。",
            "paper_ready_wording_zh": "八风向结果显示，2 m高度mean VR的风向范围仅为0.0060，VR<0.2面积比例的范围约1.74个百分点，且87.2%的行人层开放网格在所有风向下均保持低风速状态，说明该校园核心区的低通风问题具有明显方向鲁棒性。",
        },
        {
            "conclusion_id": "DC3",
            "conclusion_layer": "building_distance_gradient",
            "main_finding_zh": "风速恢复并不局限于离开立面几米后立即发生，低风速从近立面扩展到街区步行网络。",
            "key_numbers": f"0-4 m mean VR={fmt(dist['0-4m']['mean_vr'], 4)}, VR<0.2={pct(dist['0-4m']['stagnation_ratio'])}; >20 m mean VR={fmt(dist['>20m']['mean_vr'], 4)}, VR<0.2={pct(dist['>20m']['stagnation_ratio'])}",
            "architectural_interpretation_zh": "局部立面边界层只是表层现象，更关键的是建筑围合使开放空间本身也进入低风速状态。",
            "novelty_over_traditional_claim_zh": "传统讨论通常把问题划分为近墙区、背风区和开敞区；本实验显示真实校园街区内的开敞步行空间也可能被整体围合关系控制。",
            "evidence_type": "newly_run",
            "source_artifacts": "figures/paraview_vtk_core_dx2m_building_distance_stats.csv",
            "claim_boundary": "基于当前碰撞几何与VTK统计；未包含树冠、热浮力或实测行人路径。",
            "paper_ready_wording_zh": "按至建筑距离分组后，0-4 m近立面带mean VR仅为0.0021，4-10 m和10-20 m仍几乎全部低于VR=0.2；即使在>20 m区域，mean VR也仅为0.095，约90.8%的开放网格仍低于VR=0.2。这表明低通风并非单纯的近墙边界层，而是被街区围合扩展为步行网络尺度的问题。",
        },
        {
            "conclusion_id": "DC4",
            "conclusion_layer": "morphology_parameters",
            "main_finding_zh": "局地围合度和局地建成比例比单体尺度面积、细长度或紧凑度更能解释风响应差异。",
            "key_numbers": f"strongest rho={fmt(top_corr['spearman_rho'])} for {top_corr['parameter_label']} vs {top_corr['response_metric']}; 20-50 m enclosure high-low mean VR change={pct(enclosure_effect['relative_change'])}",
            "architectural_interpretation_zh": "对校园建筑群而言，能否形成通风恢复主要取决于20-50 m尺度的空间释放和通道连续性，而非单栋建筑的孤立形态。",
            "novelty_over_traditional_claim_zh": "传统建筑形态研究常强调H/W、建筑高度或密度；本实验在真实数字孪生街区中指出，基础参数中的局地围合与建成比例更适合作为应用筛查变量。",
            "evidence_type": "newly_run",
            "source_artifacts": "figures/basic_morphology_parameter_correlations.csv; figures/basic_morphology_parameter_tertile_wind_response.csv",
            "claim_boundary": "样本内部相关与分组差异；不写成普适因果阈值。",
            "paper_ready_wording_zh": "形态统计显示，近立面0-20 m带内combined enclosure score与directional mean VR的Spearman相关为-0.534，local built fraction的相关为-0.464；20-50 m带内sector enclosure仍为最清晰的抑制因子。高combined enclosure组相对低组的20-50 m mean VR降低约53.7%，提示局地围合度是比单体面积或细长度更有解释力的设计筛查参数。",
        },
        {
            "conclusion_id": "DC5",
            "conclusion_layer": "stage_and_archetype",
            "main_finding_zh": "建筑响应可分为持续遮蔽、低速混合、近-远恢复和方向敏感几类，而不是单一线性梯度。",
            "key_numbers": f"persistent shelter n={int(stage_counts.get('persistent_shelter', 0))}; near-to-context recovery n={int(stage_counts.get('near_to_context_recovery', 0))}; recovery-stage mean delta={fmt(recovery_stage['mean_recovery_delta_vr'], 4)}; persistent-stage mean delta={fmt(persistent_stage['mean_recovery_delta_vr'], 4)}",
            "architectural_interpretation_zh": "同一校园街区内部存在不同建筑群落响应型：有些位置从近立面到20-50 m出现恢复，有些位置始终被围合遮蔽。",
            "novelty_over_traditional_claim_zh": "传统结论常以街谷、广场或背风区进行类型描述；本实验把类型识别落实到数字孪生建筑组件及其局地形态上下文。",
            "evidence_type": "newly_run + blocked",
            "source_artifacts": "figures/morphology_directional_fingerprint_stage_summary.csv; figures/morphology_form_response_archetype_summary.csv",
            "claim_boundary": "聚类和阶段分类为样本内部解释工具；需要更多街区外推验证。",
            "paper_ready_wording_zh": "组件级阶段分析显示，23个建筑组件属于persistent shelter，26个属于near-to-context recovery，9个表现出directionally reactive特征。恢复型组件的局地恢复增量均值为0.0073，而持续遮蔽型为-0.0002，说明真实校园街区中的风环境响应更接近形态上下文驱动的多类型谱系，而非简单的随距离单调恢复。",
        },
        {
            "conclusion_id": "DC6",
            "conclusion_layer": "design_sensitivity",
            "main_finding_zh": "S1/S2增加开放网格或局部孔隙并未改善全局行人层mean VR，反而出现近零或轻微负响应。",
            "key_numbers": f"S1 z2 delta mean VR={fmt(s1['delta_vr_mean'], 6)}, delta stagnation={fmt(s1['delta_stagnation_ratio_vr_lt_0p2'], 6)}; S2 z2 delta mean VR={fmt(s2['delta_vr_mean'], 6)}, delta stagnation={fmt(s2['delta_stagnation_ratio_vr_lt_0p2'], 6)}",
            "architectural_interpretation_zh": "在强围合校园核心中，简单释放局部体量或增加小尺度连通并不必然形成有效压差通道。",
            "novelty_over_traditional_claim_zh": "传统设计建议常把开口、廊道或孔隙视为通风改善路径；本实验强调数字孪生模拟可用于筛掉无效甚至负效的直觉式干预。",
            "evidence_type": "newly_run",
            "source_artifacts": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "claim_boundary": "仅S1/S2两个方案；不能写成设计优化成功。",
            "paper_ready_wording_zh": "两个设计敏感性方案均未带来全局行人层改善：S1在2 m高度的mean VR变化为-0.000213，S2为-0.000466，且VR<0.2比例分别增加0.000233和0.000633。该负结果提示，在强围合校园核心中，设计干预需要围绕街区尺度通风路径和压力连通组织，而不是仅增加局部空隙。",
        },
        {
            "conclusion_id": "DC7",
            "conclusion_layer": "climate_proxy_and_uncertainty",
            "main_finding_zh": "Open-Meteo代理风向加权没有改变低风速主结论，但只能作为气候敏感性而非正式风玫瑰验证。",
            "key_numbers": f"top3 proxy directions={','.join(top_dirs['simulated_velocity_direction_deg'].astype(int).astype(str))}; top3 weight={pct(top_dirs['weight'].sum())}; z2 mean VR bootstrap CI=[{fmt(unc_vr['interval_low'])},{fmt(unc_vr['interval_high'])}]; z2 stagnation CI=[{fmt(unc_stag['interval_low'])},{fmt(unc_stag['interval_high'])}]",
            "architectural_interpretation_zh": "温带校园环境的年内风向偏置可用于筛查结果排序，但当前低风速结论主要由几何围合稳定性支撑。",
            "novelty_over_traditional_claim_zh": "本实验把气候代理作为证据边界内的敏感性层，而不是把短期数值结果包装成年舒适评价。",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifacts": "manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv; figures/experiment3_effect_size_uncertainty_summary.csv",
            "claim_boundary": "Open-Meteo为代理数据；非现场测风、非正式年度超越概率。",
            "paper_ready_wording_zh": f"Open-Meteo 2024代理风向加权显示前三个模拟风向合计权重约为{pct(top_dirs['weight'].sum())}，但2 m低速结论在方向样本bootstrap区间内保持稳定：mean VR为0.076，95%区间为0.076-0.077，VR<0.2比例为0.929，95%区间为0.926-0.932。因此，气候代理可用于情景权重敏感性讨论，但不能替代正式测风或年度舒适评价。",
        },
        {
            "conclusion_id": "DC8",
            "conclusion_layer": "digital_twin_model_performance",
            "main_finding_zh": "数字孪生底层模型的视觉真实性与CFD碰撞可用性明显分离。",
            "key_numbers": f"photogrammetry GCRI={fmt(photo_gcri)}; core prism GCRI={fmt(core_gcri)}; district prism GCRI={fmt(district_gcri)}",
            "architectural_interpretation_zh": "摄影测量/3DGS类资产适合范围和外观审查，闭合棱柱或语义LoD模型才适合进入LBM碰撞边界。",
            "novelty_over_traditional_claim_zh": "相较传统理想街谷模型，本实验的新增认知在于给出真实数字孪生资产落地到风环境模拟时的模型角色分工。",
            "evidence_type": "newly_run + preexisting_artifact",
            "source_artifacts": "manifests/gcri_scoring_table.csv; reports/rhino_geometry_conversion_report.md; reports/cfd_ready_geometry_qa.md",
            "claim_boundary": "GCRI为本研究定义的应用就绪指标；GCBTE尚未完成。",
            "paper_ready_wording_zh": "GCRI结果显示，用户摄影测量STL的就绪度仅为0.455，而经闭合、z0对齐并成功体素化的核心和街区棱柱碰撞几何分别达到0.925和0.918。这说明数字孪生底层模型在风环境应用中不能按视觉真实性直接等同于CFD边界质量，而应区分视觉参照、语义建筑层和碰撞几何层。",
        },
    ]


def write_outputs(rows: list[dict[str, object]], n: dict[str, object]) -> None:
    write_dict_csv(MAN / "experiment3_deep_data_conclusion_matrix.csv", rows, CONCLUSION_FIELDS)

    report = f"""# Experiment 3 Deep Data Conclusion Package

evidence_type: newly_run + preexisting_artifact + blocked

This file reorganizes the archived Experiment 3 data into paper-facing conclusions. It does not create new CFD results; it derives conclusion support from existing FluidX3D, ParaView, morphology, design-sensitivity, GCRI and Open-Meteo-proxy tables.

## Conclusion Matrix

{md_table(rows, ["conclusion_id", "conclusion_layer", "main_finding_zh", "key_numbers", "evidence_type", "claim_boundary"])}

## Paper-Level Interpretation

The data support a more detailed architectural reading than a generic "dense blocks reduce wind" statement. The strongest result is a three-level structure:

1. At pedestrian height, the whole campus core is strongly sheltered and the result is stable across eight wind directions.
2. At intermediate height and at distances beyond the immediate facade band, some recovery appears, but it remains controlled by local enclosure and built fraction.
3. Simple local porosity interventions did not improve the global pedestrian metric, so the design implication is to test connected block-scale ventilation paths instead of assuming that any local opening improves ventilation.

## Evidence Boundary

- Supported: digital-twin-to-CFD transformation, FluidX3D-native screening, ParaView/statistical review, vertical recovery, direction robustness, distance-to-building gradient, morphology-response interpretation, S1/S2 negative sensitivity, GCRI model-role separation.
- Not supported: measured validation, wind-tunnel validation, annual Lawson/NEN/AIJ compliance, pollutant dispersion, GCBTE, CityLBM-Grasshopper end-to-end execution, successful design optimization.
"""
    (REP / "experiment3_deep_data_conclusion_package.md").write_text(report, encoding="utf-8")

    paper_paragraphs = "\n\n".join(f"{row['conclusion_id']}. {row['paper_ready_wording_zh']}" for row in rows)
    paper_text = f"""# 实验3深度数据结论模块

evidence_type: newly_run + preexisting_artifact + blocked

{paper_paragraphs}

综合而言，本实验在传统城市风环境结论的基础上，把“建筑密集导致行人层低风速”的一般判断深化为一个可复现的数字孪生应用认识：在TUM Downtown校园核心区，低风速并非只由单一风向或近立面边界层造成，而是由围合校园形态在行人高度形成的准全向低通风底图控制。20-50 m局地形态上下文比单栋建筑的面积、细长度或紧凑度更能区分风速恢复潜力；局地建成比例和扇区围合度越高，mean VR越低，方向响应也越弱。由此，数字孪生风环境模拟的应用价值不只是产生风速云图，而是把真实校园空间转化为可审查的几何边界、形态参数、风向响应和设计敏感性证据链，用于识别哪些空间问题来自整体围合，哪些干预只是局部释放但不足以建立有效通风路径。

需要保留的边界是：上述结论属于FluidX3D-native筛查级实验，尚未完成现场风速或风洞验证，也没有污染物扩散、正式年度舒适安全评价、GCBTE或CityLBM-Grasshopper端到端运行证据。因此，论文中应将实验3定位为真实数字孪生城市数据的风环境应用落地与建筑形态解释实验，而不是完整预测精度验证或设计优化证明。
"""
    (PAPER / "experiment3_deep_data_conclusion_module_zh.md").write_text(paper_text, encoding="utf-8")

    key_value = "; ".join(
        [
            "z2 mean VR 0.076, stagnation 93.4%",
            "all-direction stagnation 87.2%",
            ">20 m distance band mean VR 0.095",
            "top morphology rho -0.534",
            "S1/S2 z2 delta mean VR negative",
            "GCRI 0.455 vs 0.925/0.918",
        ]
    )
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Deep data conclusion synthesis",
            "metric": "vertical decoupling / directional robustness / building-distance gradient / morphology signal / design sensitivity / GCRI",
            "value": key_value,
            "source_artifact": "manifests/experiment3_deep_data_conclusion_matrix.csv; reports/experiment3_deep_data_conclusion_package.md",
            "paper_safe_claim": "The experiment supports a detailed campus-core wind-screening conclusion: low-speed dominance is quasi-omnidirectional, extends beyond the immediate facade band, and is best interpreted through local enclosure and model-readiness evidence rather than through LCZ classes or single-building dimensions.",
        },
        KEY_FIELDS,
        "claim_layer",
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        {
            "claim": "Deep data conclusion synthesis reorganizes Experiment 3 FluidX3D, ParaView, morphology, design-sensitivity, climate-proxy and GCRI artifacts into paper-facing conclusions.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_deep_data_conclusion_matrix.csv; reports/experiment3_deep_data_conclusion_package.md; paper_text/experiment3_deep_data_conclusion_module_zh.md",
        },
        ["claim", "evidence_type", "source"],
        "claim",
    )


def main() -> None:
    numbers = collect_numbers()
    make_support_tables(numbers)
    rows = make_conclusion_rows(numbers)
    write_outputs(rows, numbers)
    print(f"deep_data_conclusion_rows {len(rows)}")


if __name__ == "__main__":
    main()
