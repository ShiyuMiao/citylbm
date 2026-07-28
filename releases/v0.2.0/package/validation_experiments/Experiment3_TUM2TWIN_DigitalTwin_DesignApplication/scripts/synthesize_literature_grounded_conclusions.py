from __future__ import annotations

import csv
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]


REFERENCES = [
    {
        "ref_id": "R1",
        "status": "verified_crossref",
        "authors": "Blocken; Stathopoulos; van Beeck",
        "year": "2016",
        "title": "Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment",
        "source": "Building and Environment, 100, 50-81",
        "doi": "10.1016/j.buildenv.2016.02.004",
        "url": "https://doi.org/10.1016/j.buildenv.2016.02.004",
        "used_for_claim": "Pedestrian wind studies commonly combine wind tunnel/CFD with velocity ratios or amplification factors; claim strength should account for simulation uncertainty.",
    },
    {
        "ref_id": "R2",
        "status": "verified_crossref",
        "authors": "Oke",
        "year": "1988",
        "title": "Street design and urban canopy layer climate",
        "source": "Energy and Buildings, 11, 103-113",
        "doi": "10.1016/0378-7788(88)90026-6",
        "url": "https://doi.org/10.1016/0378-7788(88)90026-6",
        "used_for_claim": "Street-canyon geometry and H/W logic provide the traditional canopy-layer explanation for sheltering and ventilation exchange.",
    },
    {
        "ref_id": "R3",
        "status": "verified_crossref",
        "authors": "Cheng; Liu; Leung",
        "year": "2009",
        "title": "On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number",
        "source": "Building Simulation, 2, 53-61",
        "doi": "10.1007/S12273-008-8332-4",
        "url": "https://doi.org/10.1007/s12273-008-8332-4",
        "used_for_claim": "Canyon aspect ratio affects ventilation performance and exchange in street-canyon settings.",
    },
    {
        "ref_id": "R4",
        "status": "verified_crossref",
        "authors": "Tsang; Kwok; Hitchcock",
        "year": "2012",
        "title": "Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium",
        "source": "Building and Environment, 49, 167-181",
        "doi": "10.1016/j.buildenv.2011.08.014",
        "url": "https://doi.org/10.1016/j.buildenv.2011.08.014",
        "used_for_claim": "Building dimensions, separation and podium/continuous massing can alter pedestrian-level air movement.",
    },
    {
        "ref_id": "R5",
        "status": "verified_crossref",
        "authors": "Janssen; Blocken; van Hooff",
        "year": "2013",
        "title": "Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study",
        "source": "Building and Environment, 59, 547-562",
        "doi": "10.1016/j.buildenv.2012.10.012",
        "url": "https://doi.org/10.1016/j.buildenv.2012.10.012",
        "used_for_claim": "Formal wind-comfort conclusions require meteorological statistics and selected comfort criteria, so this archive remains a screening study.",
    },
    {
        "ref_id": "R6",
        "status": "verified_crossref",
        "authors": "Blocken; Janssen; van Hooff",
        "year": "2012",
        "title": "CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus",
        "source": "Environmental Modelling and Software, 30, 15-34",
        "doi": "10.1016/j.envsoft.2011.11.009",
        "url": "https://doi.org/10.1016/j.envsoft.2011.11.009",
        "used_for_claim": "Campus-scale pedestrian wind studies can be framed as decision-support workflows, but comfort/safety compliance still needs the full assessment chain.",
    },
    {
        "ref_id": "R7",
        "status": "verified_crossref",
        "authors": "Hagbo; Giljarhus",
        "year": "2022",
        "title": "Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions",
        "source": "Frontiers in Built Environment, 8",
        "doi": "10.3389/fbuil.2022.858067",
        "url": "https://doi.org/10.3389/fbuil.2022.858067",
        "used_for_claim": "The number of simulated wind directions can affect comfort assessment, supporting the 8-direction robustness framing here.",
    },
    {
        "ref_id": "R8",
        "status": "verified_crossref",
        "authors": "Peel; Finlayson; McMahon",
        "year": "2007",
        "title": "Updated world map of the Koppen-Geiger climate classification",
        "source": "Hydrology and Earth System Sciences, 11, 1633-1644",
        "doi": "10.5194/hess-11-1633-2007",
        "url": "https://doi.org/10.5194/hess-11-1633-2007",
        "used_for_claim": "Munich climate context can be discussed through broad temperate-climate framing, but not used as a local measured wind rose.",
    },
    {
        "ref_id": "R9",
        "status": "verified_crossref",
        "authors": "Beck et al.",
        "year": "2018",
        "title": "Present and future Koppen-Geiger climate classification maps at 1-km resolution",
        "source": "Scientific Data, 5",
        "doi": "10.1038/sdata.2018.214",
        "url": "https://doi.org/10.1038/sdata.2018.214",
        "used_for_claim": "Climate-zone statements should remain contextual and separate from annual wind-comfort exceedance evaluation.",
    },
    {
        "ref_id": "R10",
        "status": "verified_crossref",
        "authors": "Fadl; Karadelis",
        "year": "2013",
        "title": "CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus",
        "source": "International Journal of Architecture, Engineering and Construction, 2, 131-143",
        "doi": "10.7492/IJAEC.2013.013",
        "url": "https://doi.org/10.7492/ijaec.2013.013",
        "used_for_claim": "University-campus wind studies provide an application precedent for this campus-core digital-twin screening experiment.",
    },
    {
        "ref_id": "R11",
        "status": "verified_official_url",
        "authors": "TUM2TWIN project",
        "year": "2025",
        "title": "TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks",
        "source": "Official TUM2TWIN website",
        "doi": "",
        "url": "https://tum2t.win/datasets",
        "used_for_claim": "The experiment uses a multimodal campus digital-twin source whose layers should be functionally separated for visualization, semantics and CFD collision.",
    },
    {
        "ref_id": "R12",
        "status": "verified_url_pending_bibliographic_form",
        "authors": "Hagbo; Giljarhus; Hjertager",
        "year": "2020",
        "title": "Influence of geometry acquisition method on pedestrian wind simulations",
        "source": "arXiv:2010.12371",
        "doi": "",
        "url": "https://arxiv.org/abs/2010.12371",
        "used_for_claim": "Geometry acquisition and representation can influence pedestrian-wind simulation, matching the photogrammetry-versus-closed-collision boundary finding.",
    },
]


CLAIMS = [
    {
        "claim_id": "C1",
        "claim": "本实验应定位为真实数字孪生街区的风环境筛查与设计解释，而非实测验证或法规级舒适度判定。",
        "inline_marker": "[R1,R5,R6]",
        "reference_ids": "R1;R5;R6",
        "claim_support_type": "literature_boundary + newly_run_screening",
        "experiment_support": "FluidX3D 8-direction time-mean VR fields; no field or wind-tunnel closure.",
        "evidence_boundary": "Do not claim field-validated prediction accuracy or formal Lawson/NEN/AIJ compliance.",
    },
    {
        "claim_id": "C2",
        "claim": "TUM Downtown core block is better described as a sheltered campus/block canopy than as an isolated high-rise downwash case.",
        "inline_marker": "[R2,R3,R4]",
        "reference_ids": "R2;R3;R4",
        "claim_support_type": "traditional_theory_consistency + newly_run",
        "experiment_support": "z=2 m mean VR=0.076; VR<0.2 ratio=93.35%; repeated acceleration is sparse.",
        "evidence_boundary": "Consistent with canopy/canyon sheltering, not a causal proof of every individual form mechanism.",
    },
    {
        "claim_id": "C3",
        "claim": "主结论应从强风危险转向通风不足：低速区跨风向稳定，而高风速加速区很少。",
        "inline_marker": "[R1,R7]",
        "reference_ids": "R1;R7",
        "claim_support_type": "newly_run_directional_robustness + literature_context",
        "experiment_support": "87.25% of pedestrian open cells stagnant under all 8 directions; 91.49% stagnant under >=6/8 directions.",
        "evidence_boundary": "Supports aerodynamic screening, not pollutant or thermal-risk quantification.",
    },
    {
        "claim_id": "C4",
        "claim": "20-50 m local-context morphology explains wind recovery better than single-building footprint/shape descriptors.",
        "inline_marker": "[R2,R3,R4]",
        "reference_ids": "R2;R3;R4",
        "claim_support_type": "newly_run_statistical_analysis + traditional_form_logic",
        "experiment_support": "context-only CV R2=0.325 versus size-height-shape CV R2=-0.130; sector enclosure rho=-0.396.",
        "evidence_boundary": "Component-level association; do not write as causal identification.",
    },
    {
        "claim_id": "C5",
        "claim": "数字孪生底层模型的表现是本实验的方法贡献：视觉真实不等于 CFD-ready。",
        "inline_marker": "[R11,R12]",
        "reference_ids": "R11;R12",
        "claim_support_type": "digital_twin_method + geometry_QA",
        "experiment_support": "photogrammetry visual STL GCRI=0.455; accepted core/district prism GCRI=0.925/0.918; LoD/closed-prism geometry simulated in FluidX3D.",
        "evidence_boundary": "No computed GCBTE because no independent 3DGS-derived collision extraction was available.",
    },
    {
        "claim_id": "C6",
        "claim": "气候区与校园建筑类型可用于解释应用场景，但 Open-Meteo 2024 代理不能替代正式风玫瑰。",
        "inline_marker": "[R5,R8,R9,R10]",
        "reference_ids": "R5;R8;R9;R10",
        "claim_support_type": "contextualization + proxy_sensitivity",
        "experiment_support": "Open-Meteo weighting changes z=2 m mean VR by only 0.0004 relative to equal-weighted 8-direction average.",
        "evidence_boundary": "Use as climate proxy sensitivity only; no annual exceedance probability comfort classification.",
    },
]


EVIDENCE_ROWS = [
    {
        "claim": "Verified reference manifest and citation-to-claim map were generated for the literature-grounded SCI discussion.",
        "evidence_type": "preexisting_artifact + newly_run",
        "source": "manifests/verified_references_for_sci_discussion.csv; manifests/citation_to_claim_map_sci_discussion.csv",
    },
    {
        "claim": "Literature-grounded SCI discussion connects traditional pedestrian wind conclusions with the TUM2TWIN FluidX3D morphology results.",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source": "reports/literature_grounded_sci_discussion.md",
    },
    {
        "claim": "Manuscript-ready Chinese and English discussion paragraphs were drafted with conservative claim boundaries.",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source": "paper_text/literature_grounded_discussion_sci_zh.md; paper_text/literature_grounded_discussion_sci_en.md",
    },
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_first_matching(path: Path, predicate) -> dict[str, str] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if predicate(row):
                return row
    return None


def load_numbers() -> dict[str, str]:
    vertical = ROOT / "figures" / "detailed_conclusion_vertical_gradient.csv"
    distance = ROOT / "figures" / "detailed_conclusion_building_distance_gradient.csv"
    correlations = ROOT / "figures" / "detailed_conclusion_top_morphology_correlations.csv"
    bootstrap = ROOT / "figures" / "sci_stat_bootstrap_spearman_ci.csv"
    models = ROOT / "figures" / "sci_stat_model_comparison_cv.csv"
    gcri = ROOT / "manifests" / "gcri_scoring_table.csv"

    z2 = read_first_matching(vertical, lambda r: r["height_m"] == "2.0") or {}
    z40 = read_first_matching(vertical, lambda r: r["height_m"] == "40.0") or {}
    far = read_first_matching(distance, lambda r: r["distance_bin"] == ">20m") or {}
    corr = read_first_matching(
        correlations,
        lambda r: r["analysis_zone"] == "local_context_20_50m"
        and r["parameter_label"] == "sector enclosure, r=50 m"
        and r["response_metric"] == "directional_mean_vr",
    ) or {}
    boot = read_first_matching(
        bootstrap,
        lambda r: r["analysis_zone"] == "local_context_20_50m"
        and r["parameter_label"] == "combined enclosure score",
    ) or {}
    context_model = read_first_matching(
        models,
        lambda r: r["analysis_zone"] == "local_context_20_50m"
        and r["model"] == "context_only",
    ) or {}
    size_model = read_first_matching(
        models,
        lambda r: r["analysis_zone"] == "local_context_20_50m"
        and r["model"] == "size_height_shape",
    ) or {}
    photogram = read_first_matching(gcri, lambda r: r["geometry_id"] == "user_photogrammetry_fullres_stl") or {}
    core = read_first_matching(gcri, lambda r: r["geometry_id"] == "core_photogrammetry_extent_prism_collision_z0") or {}
    district = read_first_matching(gcri, lambda r: r["geometry_id"] == "district_prism_collision_z0") or {}

    return {
        "z2_mean": f'{float(z2.get("vr_mean", 0)):.3f}',
        "z2_stag": f'{100 * float(z2.get("stagnation_ratio", 0)):.2f}%',
        "z2_accel": f'{100 * float(z2.get("acceleration_ratio_gt_0p6", 0)):.2f}%',
        "z40_mean": f'{float(z40.get("vr_mean", 0)):.3f}',
        "far_mean": f'{float(far.get("weighted_mean_vr", 0)):.3f}',
        "far_stag": f'{100 * float(far.get("weighted_stagnation_ratio", 0)):.2f}%',
        "sector_rho": f'{float(corr.get("spearman_rho", 0)):.3f}',
        "boot_rho": f'{float(boot.get("spearman_rho", 0)):.3f}',
        "boot_low": f'{float(boot.get("bootstrap_ci95_low", 0)):.3f}',
        "boot_high": f'{float(boot.get("bootstrap_ci95_high", 0)):.3f}',
        "context_r2": f'{float(context_model.get("cv_r2_mean", 0)):.3f}',
        "size_r2": f'{float(size_model.get("cv_r2_mean", 0)):.3f}',
        "photogram_gcri": f'{float(photogram.get("GCRI", 0)):.3f}',
        "core_gcri": f'{float(core.get("GCRI", 0)):.3f}',
        "district_gcri": f'{float(district.get("GCRI", 0)):.3f}',
    }


def md_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(col, "") for col in columns) + " |")
    return "\n".join(out)


def normalize_generated_markdown(text: str) -> str:
    lines = []
    for line in text.splitlines():
        lines.append(line[8:] if line.startswith("        ") else line)
    return "\n".join(lines).strip() + "\n"


def write_markdown(numbers: dict[str, str]) -> None:
    report = dedent(
        f"""
        # Literature-Grounded SCI Discussion for Experiment 3

        evidence_type: newly_run + preexisting_artifact + blocked

        This report deepens the Experiment 3 conclusion by binding each manuscript claim to verified literature, archived FluidX3D/ParaView statistics, geometry QA, and explicit evidence boundaries. It does not introduce new CFD results.

        ## 1. Verified Reference Layer

        {md_table(REFERENCES, ["ref_id", "status", "authors", "year", "title", "source", "doi", "url"])}

        ## 2. Citation-to-Claim Map

        {md_table(CLAIMS, ["claim_id", "claim", "inline_marker", "reference_ids", "claim_support_type", "experiment_support", "evidence_boundary"])}

        ## 3. Data-Driven Conclusion Synthesis

        The most defensible conclusion is not that the real campus block has been field-validated, but that a multimodal digital twin can be converted into a simulation-ready urban-wind screening workflow. Traditional pedestrian-wind literature shows that building geometry, spacing, canyon aspect ratio, podium continuity and surrounding obstacles shape near-ground airflow [R1-R4]. The TUM2TWIN result is consistent with that tradition, but its added value is the real-block translation: visual photogrammetry, semantic building data, Rhino/OBJ management and closed-prism STL collision boundaries are separated into different functional layers before FluidX3D simulation.

        The aerodynamic pattern is dominated by low-speed sheltering rather than high-speed danger. At z=2 m, mean VR is {numbers["z2_mean"]}, the VR<0.2 stagnation ratio is {numbers["z2_stag"]}, and the VR>0.6 acceleration ratio is only {numbers["z2_accel"]}. By z=40 m, mean VR recovers to {numbers["z40_mean"]}. This vertical gradient supports a canopy-decoupling interpretation: the upper flow recovers above roof scale, while pedestrian paths inside the block remain weakly ventilated.

        The building-form conclusion can now be written more sharply. The near-facade 0-20 m band is almost uniformly sheltered, so it is less useful for distinguishing design mechanisms. The 20-50 m local-context band is more diagnostic: the sector-enclosure correlation with mean VR is rho={numbers["sector_rho"]}; combined enclosure remains negative under bootstrap resampling (rho={numbers["boot_rho"]}, 95% CI [{numbers["boot_low"]}, {numbers["boot_high"]}]); and the context-only model reaches cross-validated R2={numbers["context_r2"]}, compared with R2={numbers["size_r2"]} for the size-height-shape-only model. The stronger design reading is therefore about local enclosure, passage continuity and neighborhood porosity, not about isolated footprint size or elongation alone.

        The distance gradient strengthens this interpretation. Even cells more than 20 m from the nearest building have mean VR={numbers["far_mean"]} and a low-speed ratio of {numbers["far_stag"]}. The stagnation problem is therefore not merely a facade boundary-layer artifact; it propagates across the campus pedestrian network.

        The digital-twin model result is a separate methodological contribution. The textured photogrammetry visual mesh has GCRI={numbers["photogram_gcri"]}, while the accepted core and district closed-prism collision geometries have GCRI={numbers["core_gcri"]} and {numbers["district_gcri"]}. This supports the claim that visual fidelity and CFD readiness are different properties. In this experiment, photogrammetry is valuable for scope audit and scene consistency, but semantic/closed geometry is the defensible collision-boundary route.

        ## 4. What Is New Relative to Traditional Conclusions

        1. The experiment translates traditional canyon/block-wind reasoning from idealized geometry into a real, visually auditable campus digital-twin block.
        2. It reframes the site problem from strong-wind safety to persistent ventilation insufficiency, which is more relevant for dense campus courtyards and pedestrian networks.
        3. It shows that local-context morphology is more explanatory than individual-building size descriptors within this low-speed background.
        4. It makes geometry readiness an explicit wind-environment variable: the same urban scene can be visually credible but physically unsuitable for LBM collision until repaired or semantically reconstructed.

        ## 5. Claim Boundary

        These conclusions are paper-ready as simulation-based design-screening and morphology-interpretation claims. They are not field validation, wind-tunnel validation, formal annual wind-comfort/safety compliance, pollutant dispersion prediction, successful intervention optimization, S2-Sn intervention proof, CityLBM-GH end-to-end execution, or a computed 3DGS-to-collision transfer-error result.
        """
    )

    zh = dedent(
        f"""
        # 文献锚定的 SCI 讨论段落（中文）

        evidence_type: newly_run + preexisting_artifact + blocked

        传统行人风环境研究已经指出，建筑高度、体量、间距、街谷高宽比、裙房或连续基座以及周边障碍物会共同改变近地风速分布；风舒适评价还需要把空气动力场、气象统计和具体舒适度准则结合起来使用[R1-R7]。因此，本文不把 TUM2TWIN 实验表述为求解器精度或法规舒适度的再次验证，而将其定位为真实城市数字孪生数据进入风环境模拟的设计应用实验。其核心贡献在于：将摄影测量/纹理网格、语义建筑模型、Rhino/OBJ 可视化管理和封闭 STL 碰撞边界分层处理，使真实校园街区能够进入 FluidX3D 并在 ParaView 中进行可审查的风场筛查。

        从风环境结果看，TUM Downtown 核心区更接近遮蔽型校园街区/街谷冠层，而不是典型孤立高层建筑下洗加速场景。行人高度 z=2 m 的平均 VR 仅为 {numbers["z2_mean"]}，VR<0.2 的低速比例达到 {numbers["z2_stag"]}，而 VR>0.6 的加速比例只有 {numbers["z2_accel"]}；到 z=40 m，平均 VR 恢复到 {numbers["z40_mean"]}。这一垂直梯度说明，屋顶以上风场恢复并不会自动转化为行人层通风改善，校园内部 courtyard、连续界面和通道开敞度共同形成了明显的近地遮蔽背景。

        建筑形态与风环境之间的关系也可以比“建筑越密风越小”写得更细。在 0-20 m 近立面带，低速几乎是整体背景，因此它更适合表征遮蔽强度；而 20-50 m 局地背景带更能揭示形态差异。该带内，50 m 扇区围合度与 mean VR 的相关系数为 {numbers["sector_rho"]}；综合围合度在 bootstrap 后仍保持负相关（rho={numbers["boot_rho"]}，95% CI [{numbers["boot_low"]}, {numbers["boot_high"]}]）；仅包含局地建成比例和扇区围合度的 context-only 模型交叉验证 R2 为 {numbers["context_r2"]}，高于单体尺度与形状模型的 R2={numbers["size_r2"]}。因此，本实验在传统街谷与建筑体量结论之上获得的新认知是：对于真实校园街区，解释行人层通风恢复的关键并非单栋建筑面积、长宽比或轮廓紧凑度，而是 20-50 m 范围内的围合连续性、通道连通性和局地孔隙度。

        该结论仍需保持证据边界。Open-Meteo 2024 只能作为气候代理权重，不能替代正式年度风玫瑰；当前结果没有污染物扩散、实测风速或风洞闭环。S1 设计敏感性场景已经实跑，但结果为近零/负向，不能写成成功优化。因此，最稳妥的论文表述是：本实验展示并复核了 TUM2TWIN 数字孪生数据在校园风环境筛查中的落地路径，并显示核心校园街区存在跨风向稳定的低通风风险；建筑形态层面的可操作解释应优先关注局地围合与通道开敞，而不是只讨论单体高度或平面形状。
        """
    )

    en = dedent(
        f"""
        # Literature-Grounded SCI Discussion Paragraphs (English)

        evidence_type: newly_run + preexisting_artifact + blocked

        Previous pedestrian-wind studies have shown that building height, massing, spacing, street-canyon aspect ratio, podium continuity and surrounding obstacles jointly affect near-ground wind distributions, while formal comfort assessment requires the aerodynamic field to be combined with meteorological statistics and selected comfort criteria [R1-R7]. Accordingly, the TUM2TWIN experiment is not framed as a new validation of solver accuracy or as a regulatory wind-comfort assessment. It is positioned as a real digital-twin design-application experiment that separates photogrammetric/texture meshes, semantic building data, Rhino/OBJ visual management and closed STL collision boundaries before FluidX3D simulation and ParaView review.

        The simulated wind response indicates that the TUM Downtown core behaves more like a sheltered campus-block canopy than an isolated high-rise downwash case. At z=2 m, the mean velocity ratio is {numbers["z2_mean"]}, the VR<0.2 stagnation ratio is {numbers["z2_stag"]}, and the VR>0.6 acceleration ratio is only {numbers["z2_accel"]}. At z=40 m, mean VR recovers to {numbers["z40_mean"]}. This vertical contrast suggests a pedestrian/upper-flow decoupling: above-roof wind recovery does not directly resolve the low-ventilation condition of courtyard and passage spaces at pedestrian height.

        The morphology-wind relationship can therefore be stated more precisely than a generic density effect. The 0-20 m facade-adjacent band is almost uniformly sheltered, whereas the 20-50 m local-context band better reveals morphology-dependent wind recovery. In that band, sector enclosure within 50 m correlates negatively with mean VR (rho={numbers["sector_rho"]}), the combined enclosure score remains negative under bootstrap resampling (rho={numbers["boot_rho"]}, 95% CI [{numbers["boot_low"]}, {numbers["boot_high"]}]), and a context-only model using local built fraction and sector enclosure reaches cross-validated R2={numbers["context_r2"]}, compared with R2={numbers["size_r2"]} for the size-height-shape-only model. The added insight is that, within this real campus block, local enclosure continuity, passage connectivity and neighborhood porosity carry more explanatory value for pedestrian wind recovery than isolated footprint size, elongation or compactness descriptors.

        These findings remain bounded by the available evidence. The Open-Meteo 2024 weighting is a climate proxy rather than a formal measured wind rose, and the archive does not yet include pollutant dispersion, field measurements, wind-tunnel closure, or a completed CityLBM-Grasshopper end-to-end run. S1 has been simulated as a design-sensitivity scenario, but its near-null/negative result cannot be written as a successful optimization. The defensible conclusion is therefore that TUM2TWIN supports a reproducible digital-twin-to-FluidX3D screening workflow for campus wind applications, and that the most actionable architectural interpretation is to evaluate local enclosure and passage openness before relying on single-building height or plan-form descriptors.
        """
    )

    (ROOT / "reports" / "literature_grounded_sci_discussion.md").write_text(
        normalize_generated_markdown(report), encoding="utf-8", newline="\n"
    )
    (ROOT / "paper_text" / "literature_grounded_discussion_sci_zh.md").write_text(
        normalize_generated_markdown(zh), encoding="utf-8", newline="\n"
    )
    (ROOT / "paper_text" / "literature_grounded_discussion_sci_en.md").write_text(
        normalize_generated_markdown(en), encoding="utf-8", newline="\n"
    )


def update_evidence_inventory() -> None:
    path = ROOT / "manifests" / "evidence_inventory.csv"
    rows: list[dict[str, str]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    existing = {(row.get("claim", ""), row.get("source", "")) for row in rows}
    for row in EVIDENCE_ROWS:
        key = (row["claim"], row["source"])
        if key not in existing:
            rows.append(row)
    write_csv(path, rows)


def add_section_once(path: Path, title: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    if title in text:
        return
    text = text.rstrip() + "\n\n" + title + "\n\n" + body.strip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def update_indexes() -> None:
    readme_body = """
The latest addendum links the FluidX3D/ParaView outputs to verified pedestrian-wind, campus-CFD, climate-context and digital-twin geometry literature. It adds:

- `reports/literature_grounded_sci_discussion.md`
- `manifests/verified_references_for_sci_discussion.csv`
- `manifests/citation_to_claim_map_sci_discussion.csv`
- `paper_text/literature_grounded_discussion_sci_zh.md`
- `paper_text/literature_grounded_discussion_sci_en.md`

Use these files when writing the final SCI discussion because they explicitly separate paper-ready claims from blocked claims.
"""
    index_body = """
New literature-grounded synthesis files:

- Literature-grounded SCI discussion: `reports/literature_grounded_sci_discussion.md`
- Verified references: `manifests/verified_references_for_sci_discussion.csv`
- Citation-to-claim map: `manifests/citation_to_claim_map_sci_discussion.csv`
- Chinese paper text: `paper_text/literature_grounded_discussion_sci_zh.md`
- English paper text: `paper_text/literature_grounded_discussion_sci_en.md`

These files should be read after `reports/sci_statistical_robustness_analysis.md` and before final manuscript polishing.
"""
    add_section_once(ROOT / "README.md", "## Latest Literature-Grounded Synthesis", readme_body)
    add_section_once(ROOT / "reports" / "final_experiment_package_index.md", "## Literature-Grounded SCI Discussion Addendum", index_body)


def main() -> None:
    numbers = load_numbers()
    write_csv(ROOT / "manifests" / "verified_references_for_sci_discussion.csv", REFERENCES)
    write_csv(ROOT / "manifests" / "citation_to_claim_map_sci_discussion.csv", CLAIMS)
    write_markdown(numbers)
    update_evidence_inventory()
    update_indexes()
    print("Generated literature-grounded SCI discussion package.")


if __name__ == "__main__":
    main()
