from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(FIG / name)


def f(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def find_row(df: pd.DataFrame, **conditions: object) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for key, value in conditions.items():
        mask &= df[key].astype(str) == str(value)
    matched = df[mask]
    if matched.empty:
        raise ValueError(f"No row found for {conditions}")
    return matched.iloc[0]


def write_text_lf(path: Path, text: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def normalize_text_file(path: Path) -> None:
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if normalized != data:
        path.write_bytes(normalized)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    PAPER.mkdir(parents=True, exist_ok=True)

    baseline = read_csv("fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv")
    climate = read_csv("fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv")
    s1 = read_csv("fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv")
    s2 = read_csv("fluidx3d_s0_s2_network_porosity_metric_comparison.csv")
    trade = read_csv("fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv")
    morph = read_csv("basic_morphology_multivariate_robustness.csv")
    morph_cv = read_csv("basic_morphology_rank_model_cv_summary.csv")
    gcri = pd.read_csv(ROOT / "manifests" / "gcri_scoring_table.csv")

    b2 = find_row(baseline, case="equal_weighted_8dir", z_height_m_approx="2.0")
    b40 = find_row(baseline, case="equal_weighted_8dir", z_height_m_approx="40.0")
    c2 = find_row(climate, case="open_meteo_2024_weighted_8dir", z_height_m_approx="2.0")
    s1_2 = find_row(s1, comparison="S1_minus_S0", z_height_m_approx="2.0")
    s2_2 = find_row(s2, comparison="S2_minus_S0", z_height_m_approx="2.0")
    tr_s2 = find_row(trade, comparison="S2_minus_S0")
    morph_cv_mean = find_row(morph_cv, analysis_zone="local_context_20_50m", target="directional_mean_vr")
    sector = find_row(
        morph,
        analysis_zone="local_context_20_50m",
        target="directional_mean_vr",
        feature="sector_enclosure_ratio_r50m",
    )
    mean_height = find_row(
        morph,
        analysis_zone="local_context_20_50m",
        target="directional_mean_vr",
        feature="mean_height_m",
    )
    photo_gcri = find_row(gcri, geometry_id="user_photogrammetry_fullres_stl")
    core_gcri = find_row(gcri, geometry_id="core_photogrammetry_extent_prism_collision_z0")
    district_gcri = find_row(gcri, geometry_id="district_prism_collision_z0")

    matrix_rows = [
        {
            "evidence_type": "newly_run",
            "claim_layer": "S0 baseline pedestrian screening",
            "metric": "z~2 m mean VR / stagnation ratio",
            "value": f"{f(b2['vr_mean'])} / {f(b2['stagnation_ratio_vr_lt_0p2'])}",
            "source_artifact": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_safe_claim": "The baseline campus core is dominated by low pedestrian-height speed ratios.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "Vertical recovery",
            "metric": "z~40 m mean VR / stagnation ratio",
            "value": f"{f(b40['vr_mean'])} / {f(b40['stagnation_ratio_vr_lt_0p2'])}",
            "source_artifact": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_safe_claim": "Upper-layer flow recovers while pedestrian-layer flow remains sheltered.",
        },
        {
            "evidence_type": "newly_run + preexisting_artifact",
            "claim_layer": "Climate-proxy sensitivity",
            "metric": "Open-Meteo weighted z~2 m mean VR / stagnation ratio",
            "value": f"{f(c2['vr_mean'])} / {f(c2['stagnation_ratio_vr_lt_0p2'])}",
            "source_artifact": "figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv",
            "paper_safe_claim": "The low-speed conclusion is stable under the proxy direction weighting, but this is not annual comfort compliance.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "S1 design sensitivity",
            "metric": "delta z~2 m mean VR / delta stagnation ratio",
            "value": f"{f(s1_2['delta_vr_mean'], 6)} / {f(s1_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}",
            "source_artifact": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv",
            "paper_safe_claim": "A single light corridor opening is insufficient and slightly negative in the global pedestrian layer.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "S2 design sensitivity",
            "metric": "delta z~2 m mean VR / delta stagnation ratio",
            "value": f"{f(s2_2['delta_vr_mean'], 6)} / {f(s2_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}",
            "source_artifact": "figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "paper_safe_claim": "A stronger network-porosity opening remains near-null/negative without effective momentum-entry alignment.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "Directional local trade-off",
            "metric": "S2 best common-open direction / improved-cell share / newly opened max mean VR",
            "value": f"{int(tr_s2['best_common_wind_deg'])} deg / {f(tr_s2['mean_common_improved_ratio_delta_gt_0p02'], 6)} / {f(tr_s2['max_newly_open_target_vr_mean'], 6)}",
            "source_artifact": "figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv",
            "paper_safe_claim": "S2 creates sparse local response, but newly opened cells remain low speed.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "Morphology robustness",
            "metric": "rank-ridge CV R2 / sector-enclosure coefficient / permutation importance",
            "value": f"{f(morph_cv_mean['ridge_cv_r2_mean'])}+/-{f(morph_cv_mean['ridge_cv_r2_std'])} / {f(sector['ridge_standardized_coef'])} / {f(sector['permutation_r2_drop'])}",
            "source_artifact": "figures/basic_morphology_rank_model_cv_summary.csv; figures/basic_morphology_multivariate_robustness.csv",
            "paper_safe_claim": "Morphology variables are interpretable screening descriptors, not high-accuracy predictors.",
        },
        {
            "evidence_type": "newly_run",
            "claim_layer": "Geometry-to-CFD readiness",
            "metric": "photogrammetry GCRI / core prism GCRI / district prism GCRI",
            "value": f"{f(photo_gcri['GCRI'])} / {f(core_gcri['GCRI'])} / {f(district_gcri['GCRI'])}",
            "source_artifact": "manifests/gcri_scoring_table.csv",
            "paper_safe_claim": "Visual fidelity and collision-boundary readiness are separable properties in the digital twin workflow.",
        },
    ]
    matrix = pd.DataFrame(matrix_rows)
    matrix_path = FIG / "final_integrated_key_result_matrix.csv"
    matrix.to_csv(matrix_path, index=False, encoding="utf-8-sig", lineterminator="\n")
    normalize_text_file(matrix_path)

    audit_rows = [
        ("TUM2TWIN source/layer verification", "complete", "reports/data_source_and_download_manifest.md; manifests/data_manifest.csv", "Official dataset pages, source URLs, checksums and license/citation records are archived."),
        ("Rhino/OBJ visual consistency", "complete", "reports/rhino_geometry_conversion_report.md; reports/current_data_summary_and_conclusions.md", "The user photogrammetry block and core CFD extent are documented as the same study-scale object."),
        ("CFD-ready closed geometry", "complete", "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl; manifests/geometry_qa_core_photogrammetry_extent_prism.json", "Closed-prism geometry is z0-aligned, QA-recorded and accepted by FluidX3D."),
        ("FluidX3D baseline simulation", "complete", "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv", "Eight directions, three post-spin-up samples, z-level metrics and ParaView review artifacts exist."),
        ("ParaView/manual visual audit", "complete", "reports/paraview_vtk_core_wind_statistics_and_building_analysis.md; paraview_states/", "ParaView states and rendered statistical maps exist for manual review."),
        ("Climate/context sensitivity", "complete_with_boundary", "figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv", "Open-Meteo is a proxy weighting layer, not a measured annual comfort wind rose."),
        ("Morphology-form relation", "complete_with_boundary", "reports/basic_morphology_wind_response_analysis.md; reports/basic_morphology_multivariate_robustness.md", "The result supports interpretable local-context diagnosis, not causal prediction."),
        ("Design sensitivity S1/S2", "complete_negative_result", "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv", "Both interventions are near-null/negative and therefore support design-boundary reasoning rather than an optimization claim."),
        ("Directional local trade-off", "complete", "reports/design_sensitivity_directional_tradeoff_analysis.md", "Local response exists but is sparse; newly opened cells remain low-speed."),
        ("CityLBM-GH end-to-end run", "blocked", "reports/claim_boundary.md; cfd_ready/CityLBM_GH_input_template/", "Only a CityLBM-compatible template is archived; no Grasshopper plugin run evidence is present."),
        ("Pollutant dispersion", "blocked", "reports/design_scenario_and_unfinished_metric_boundary.md", "No scalar transport outputs exist."),
        ("Measured or wind-tunnel validation", "blocked", "reports/claim_boundary.md", "No onsite measured wind field or wind-tunnel closure exists."),
        ("Formal Lawson/NEN/AIJ compliance", "blocked", "reports/claim_boundary.md", "Annual threshold exceedance evaluation with calibrated wind climate is not available."),
        ("GCBTE 3DGS collision-transfer error", "blocked", "reports/claim_boundary.md", "No independent 3DGS-derived collision extraction is available for error computation."),
    ]
    audit = pd.DataFrame(audit_rows, columns=["requirement", "status", "evidence_artifact", "interpretation"])
    audit_path = FIG / "experiment3_completion_audit_matrix.csv"
    audit.to_csv(audit_path, index=False, encoding="utf-8-sig", lineterminator="\n")
    normalize_text_file(audit_path)

    audit_md = "# Experiment 3 Completion Audit and Paper Readiness\n\n"
    audit_md += "evidence_type: newly_run + preexisting_artifact + blocked\n\n"
    audit_md += "This audit checks whether the TUM2TWIN Experiment 3 package is ready for manuscript use and where claim boundaries must remain explicit.\n\n"
    audit_md += "## Key Result Matrix\n\n"
    audit_md += matrix.to_markdown(index=False)
    audit_md += "\n\n## Requirement Coverage\n\n"
    audit_md += audit.to_markdown(index=False)
    audit_md += "\n\n## Paper-Ready Positioning\n\n"
    audit_md += (
        "The experiment is paper-ready as a FluidX3D-native digital-twin wind-environment screening and design-interpretation case. "
        "Its strongest claims concern data-layer separation, CFD-ready geometry construction, pedestrian-layer low-speed screening, "
        "local morphology diagnosis and negative S1/S2 design-sensitivity evidence. It is not ready for claims of field-validated accuracy, "
        "annual comfort/safety compliance, pollutant dispersion, successful design optimization, or CityLBM-GH end-to-end execution.\n"
    )
    write_text_lf(REP / "experiment3_completion_audit_and_paper_readiness.md", audit_md)

    zh = f"""# 实验3最终整合结果与讨论段落

evidence_type: newly_run + preexisting_artifact + blocked

本实验应被定位为 TUM2TWIN 真实校园数字孪生街区的 FluidX3D-native 风环境筛查与设计解释，而不是实测验证或法规级舒适度判定。已有行人风研究通常以 CFD/风洞和速度比、舒适阈值或超越概率构建评价链条，且正式舒适结论需要气象统计和评价准则闭合 [R1,R5-R7]。在这一边界内，本文完成了从 TUM2TWIN 视觉/语义/几何数据到 CFD-ready 碰撞边界、FluidX3D 八风向模拟、ParaView 审核和形态解释的应用转化。

基准结果显示，研究区的主要风环境问题不是强风危险，而是方向稳健的近地通风不足。在 dx=2 m、8 风向、spin-up 后 3 时间样本平均协议下，z≈2 m 行人层 mean VR 为 {f(b2['vr_mean'])}，P95 为 {f(b2['vr_p95'])}，VR<0.2 低速比例为 {f(b2['stagnation_ratio_vr_lt_0p2'])}；到 z≈40 m，mean VR 恢复到 {f(b40['vr_mean'])}，低速比例降至 {f(b40['stagnation_ratio_vr_lt_0p2'])}。这说明屋面以上流场恢复并不自动代表步行层通风恢复，校园院落、入口和街道连通空间需要单独评价。

Open-Meteo 2024 方向权重只作为气候代理，而非正式实测风玫瑰。加权后 z≈2 m mean VR 为 {f(c2['vr_mean'])}，低速比例为 {f(c2['stagnation_ratio_vr_lt_0p2'])}，与 8 风向等权平均非常接近。由此可写的结论是：当前低速格局对该代理方向权重不敏感；不可写成年度 Lawson/NEN/AIJ 舒适安全合规评价 [R5,R8-R10]。

建筑形式分析进一步把传统“高密度、围合街谷削弱通风”的认识推进到可定位的校园尺度诊断 [R2-R4]。0-20 m 近立面带几乎普遍滞风，难以区分不同形态的设计机制；20-50 m 局地环境带更能体现风速恢复差异。在 101 个建筑单元的多变量稳健性复核中，20-50 m mean VR 的 rank-regression 交叉验证 R2 仅为 {f(morph_cv_mean['ridge_cv_r2_mean'])}±{f(morph_cv_mean['ridge_cv_r2_std'])}，说明形态参数不能被写成强预测模型；但变量排序仍有解释价值，50 m 扇区围合度的标准化系数为 {f(sector['ridge_standardized_coef'])}，置换重要性为 {f(sector['permutation_r2_drop'])}，平均高度的标准化系数为 {f(mean_height['ridge_standardized_coef'])}。因此，本文的形态结论应写为局地围合、动量入口和院落-街道压力交换的筛查诊断，而不是由单体 footprint、elongation 或 perimeter-area compactness 单独决定风环境。

S1/S2 设计敏感性实验把这一解释进一步收敛。S1 单条 light relief corridor 在 z≈2 m 使 mean VR 变化 {f(s1_2['delta_vr_mean'], 6)}，低速比例变化 {f(s1_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}；S2 三通道 network porosity 使 mean VR 变化 {f(s2_2['delta_vr_mean'], 6)}，低速比例变化 {f(s2_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}。方向性 trade-off 显示 S2 在 315° 共同开放单元中有最佳局部响应，mean ΔVR 为 {f(tr_s2['best_common_delta_vr_mean'], 6)}，但 ΔVR>0.02 的共同开放单元比例均值仅 {f(tr_s2['mean_common_improved_ratio_delta_gt_0p02'], 6)}，新增开放单元最高 mean VR 仅 {f(tr_s2['max_newly_open_target_vr_mean'], 6)} 且低速比例仍为 {f(tr_s2['min_newly_open_stagnation_ratio'])}。因此，S1/S2 不能作为成功优化方案，而应作为负向设计证据：几何孔隙如果没有与有效来流扇区、动量入口和压力交换路径耦合，就可能只是低速背景中的新增开敞空间。

数字孪生底层模型的主要方法贡献在于揭示“视觉真实”和“CFD 就绪”并不等同。photogrammetry visual STL 的 GCRI 为 {f(photo_gcri['GCRI'])}，而 core closed-prism collision 和 district prism collision 分别达到 {f(core_gcri['GCRI'])} 与 {f(district_gcri['GCRI'])}。这支持本文的核心技术路线：UAS/photogrammetry/3DGS-like 资产适合视觉审查和场景一致性核验，但最终 FluidX3D/CityLBM 碰撞边界应由语义 LoD/CAD-derived 闭合几何生成 [R11,R12]。

综上，实验3最稳妥的 SCI 结论是：TUM2TWIN 数字孪生数据能够被转化为真实校园街区的 CFD-ready 风环境筛查流程；该区域在模拟中表现为行人层持续低速、上部流场恢复、局地围合控制有限风速恢复的格局；S1/S2 负向敏感性说明设计应用不能停留在增加孔隙面积，而应转向风向扇区耦合的入口廊道、围合解除和压力交换连续性。本文不宣称实测验证、污染物扩散、正式舒适安全合规、S3-Sn 正向优化、GCBTE 误差闭合或 CityLBM-GH 端到端实跑。
"""
    write_text_lf(PAPER / "final_integrated_results_discussion_zh.md", zh)

    en = f"""# Final Integrated Results and Discussion for Experiment 3

evidence_type: newly_run + preexisting_artifact + blocked

Experiment 3 should be positioned as a FluidX3D-native digital-twin wind screening and design-interpretation case for the TUM2TWIN campus block, not as field validation or formal comfort-code compliance. Within this boundary, the experiment establishes a complete application chain from visual/semantic/geometric TUM2TWIN layers to CFD-ready collision geometry, eight-direction FluidX3D simulation, ParaView inspection and morphology-based interpretation [R1,R5-R7].

The baseline result indicates persistent pedestrian-layer ventilation insufficiency rather than a strong-wind hazard. Under the dx=2 m, eight-direction, three-sample post-spin-up protocol, the z~2 m mean VR is {f(b2['vr_mean'])}, the P95 VR is {f(b2['vr_p95'])}, and the VR<0.2 low-speed ratio is {f(b2['stagnation_ratio_vr_lt_0p2'])}. At z~40 m, the mean VR recovers to {f(b40['vr_mean'])}, while the low-speed ratio falls to {f(b40['stagnation_ratio_vr_lt_0p2'])}. The vertical contrast shows that above-roof flow recovery cannot be used as a surrogate for pedestrian-space ventilation in courtyards, entrances and campus pedestrian routes.

The Open-Meteo 2024 direction weighting is used only as a climate proxy. It gives a z~2 m mean VR of {f(c2['vr_mean'])} and a low-speed ratio of {f(c2['stagnation_ratio_vr_lt_0p2'])}, close to the equal-weighted result. Therefore, the paper can claim sensitivity of the low-speed conclusion to a proxy directional weighting, but not annual Lawson/NEN/AIJ comfort or safety compliance [R5,R8-R10].

The morphology analysis translates traditional canopy and canyon reasoning into a local digital-twin diagnosis [R2-R4]. The 0-20 m facade-adjacent band is almost uniformly sheltered, whereas the 20-50 m local-context band better reveals morphology-dependent recovery. In the conservative multivariate robustness check over 101 building components, the rank-regression CV R2 for 20-50 m mean VR is only {f(morph_cv_mean['ridge_cv_r2_mean'])}+/-{f(morph_cv_mean['ridge_cv_r2_std'])}, so morphology variables should not be treated as a high-accuracy surrogate model. Nevertheless, their ordering is interpretable: the 50 m sector-enclosure coefficient is {f(sector['ridge_standardized_coef'])} with permutation importance {f(sector['permutation_r2_drop'])}, stronger than footprint area, elongation and perimeter-area compactness. The paper-safe interpretation is that local enclosure, wind-entry opportunity and pressure-exchange continuity are more useful screening descriptors than isolated building size or shape.

The S1/S2 design-sensitivity sequence further narrows the design claim. S1 changes z~2 m mean VR by {f(s1_2['delta_vr_mean'], 6)} and the low-speed ratio by {f(s1_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}. S2 changes z~2 m mean VR by {f(s2_2['delta_vr_mean'], 6)} and the low-speed ratio by {f(s2_2['delta_stagnation_ratio_vr_lt_0p2'], 6)}. Directional trade-off analysis shows that S2 has its best common-open response at 315 deg, but the mean share of common-open cells with Delta VR>0.02 is only {f(tr_s2['mean_common_improved_ratio_delta_gt_0p02'], 6)}, and newly opened cells reach a maximum direction-wise mean VR of only {f(tr_s2['max_newly_open_target_vr_mean'], 6)}. S1/S2 are therefore negative design evidence: geometric porosity alone does not recover pedestrian ventilation unless coupled to effective inflow sectors, momentum entry and pressure-exchange paths.

The digital-twin modelling contribution is the separation between visual realism and CFD readiness. The photogrammetry visual STL has GCRI={f(photo_gcri['GCRI'])}, while the accepted core and district closed-prism collision geometries reach GCRI={f(core_gcri['GCRI'])} and {f(district_gcri['GCRI'])}. This supports the workflow claim that UAS/photogrammetry/3DGS-like assets are valuable for visual audit and scene consistency, whereas FluidX3D/CityLBM collision boundaries require semantic LoD/CAD-derived closed geometry [R11,R12].

Overall, Experiment 3 supports a digital-twin-to-CFD application workflow and a morphology-informed campus wind-screening conclusion. It does not support field-validated accuracy, pollutant dispersion, annual comfort/safety compliance, successful S3-Sn optimization, GCBTE closure or a CityLBM-GH end-to-end execution claim.
"""
    write_text_lf(PAPER / "final_integrated_results_discussion_en.md", en)

    print("wrote", FIG / "final_integrated_key_result_matrix.csv")
    print("wrote", FIG / "experiment3_completion_audit_matrix.csv")
    print("wrote", REP / "experiment3_completion_audit_and_paper_readiness.md")
    print("wrote", PAPER / "final_integrated_results_discussion_zh.md")
    print("wrote", PAPER / "final_integrated_results_discussion_en.md")


if __name__ == "__main__":
    main()
