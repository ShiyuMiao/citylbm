from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, rows_to_add: list[dict[str, str]], key: str, fieldnames: list[str]) -> None:
    rows = read_csv_rows(path)
    current = {row.get(key, ""): row for row in rows}
    for row in rows_to_add:
        current[row[key]] = row
    write_csv(path, list(current.values()), fieldnames)


def build_rows() -> list[dict[str, str]]:
    return [
        {
            "limitation_id": "L1",
            "limitation": "No field or wind-tunnel validation for the TUM2TWIN campus case.",
            "current_evidence": "FluidX3D eight-direction screening, geometry QA, ParaView/Rhino visual audit and Cases A/E as preceding benchmark context.",
            "claim_boundary": "Do not claim field-validated predictive accuracy for Experiment 3.",
            "required_next_evidence": "Install temporary anemometers or use wind-tunnel/PIV testing for selected pedestrian points; compare U/Uref, directionality and uncertainty against FluidX3D outputs.",
            "upgrade_path": "screening-level result -> measured or wind-tunnel-supported validation case",
            "priority": "high_for_prediction_claims",
            "evidence_type": "blocked",
            "source_artifact": "reports/claim_boundary.md; manifests/experiment3_final_requirement_coverage.csv",
        },
        {
            "limitation_id": "L2",
            "limitation": "Open-Meteo 2024 is a proxy directional weighting layer, not a calibrated site wind climate.",
            "current_evidence": "Equal-weighted and Open-Meteo-weighted z~2 m low-speed conclusions are close, supporting proxy sensitivity only.",
            "claim_boundary": "Do not claim annual Lawson/NEN/AIJ comfort or safety compliance.",
            "required_next_evidence": "Acquire calibrated multi-year wind rose or local station data, define exceedance thresholds by activity category, and compute annual threshold probabilities at pedestrian receptors.",
            "upgrade_path": "directional screening -> formal annual comfort/safety assessment",
            "priority": "high_for_compliance_claims",
            "evidence_type": "blocked",
            "source_artifact": "figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv; reports/claim_boundary.md",
        },
        {
            "limitation_id": "L3",
            "limitation": "Residual convergence and complete grid-independence evidence are not available.",
            "current_evidence": "dx=2 m protocol, three post-spin-up samples and partial direction-sample uncertainty support screening stability, but residuals are not recorded.",
            "claim_boundary": "Do not frame the FluidX3D result as final numerical convergence proof.",
            "required_next_evidence": "Run dx sensitivity such as 3 m/2 m/1 m where feasible, store residual or monitor-point histories, and report grid-convergence index or uncertainty bands.",
            "upgrade_path": "screening protocol transparency -> numerically stronger CFD protocol",
            "priority": "medium_high_for_method_review",
            "evidence_type": "blocked",
            "source_artifact": "manifests/fluidx3d_numerical_protocol_audit.csv; reports/fluidx3d_numerical_protocol_and_stability_audit.md",
        },
        {
            "limitation_id": "L4",
            "limitation": "CityLBM-Grasshopper end-to-end execution has not been completed.",
            "current_evidence": "CityLBM-compatible geometry template exists, while the completed solver path is FluidX3D-native.",
            "claim_boundary": "Use 'FluidX3D-native simulation with CityLBM-compatible geometry preparation' unless GH evidence is added.",
            "required_next_evidence": "Open Rhino/Grasshopper, load CityLBM template, run a small end-to-end case, archive GH file, screenshots, exported inputs, logs and output fields.",
            "upgrade_path": "CityLBM-compatible package -> CityLBM-GH executed workflow",
            "priority": "medium_if_title_mentions_CityLBM",
            "evidence_type": "blocked",
            "source_artifact": "cfd_ready/CityLBM_GH_input_template/README.md; reports/claim_boundary.md",
        },
        {
            "limitation_id": "L5",
            "limitation": "Pollutant dispersion was not simulated.",
            "current_evidence": "Pollutant metrics and source templates are defined, but no scalar transport outputs exist.",
            "claim_boundary": "Do not claim C/C0, exposure integral or pollutant hotspot results.",
            "required_next_evidence": "Add scalar transport or passive tracer simulation with road/point/area source definitions, validate source normalization, and postprocess C/C0 and path exposure at pedestrian height.",
            "upgrade_path": "ventilation screening -> pollutant-dispersion application case",
            "priority": "medium_for_environmental_health_extension",
            "evidence_type": "blocked",
            "source_artifact": "reports/metric_system_for_digital_twin_wind_application.md; reports/claim_boundary.md",
        },
        {
            "limitation_id": "L6",
            "limitation": "GCBTE is defined but not computed because no independent 3DGS-derived collision extraction exists.",
            "current_evidence": "The study demonstrates why photogrammetry/3DGS-like visual geometry should not be used directly as final collision geometry, but does not quantify transfer error.",
            "claim_boundary": "Do not claim completed 3DGS-to-collision transfer accuracy.",
            "required_next_evidence": "Generate an independent 3DGS-derived solid mask or boundary extraction, compare against CityGML/LoD3 or closed-prism ground truth using IoU, Chamfer/Hausdorff distance and voxel-mask agreement.",
            "upgrade_path": "conceptual boundary-transfer metric -> quantified GCBTE validation",
            "priority": "medium_for_digital_twin_novelty",
            "evidence_type": "blocked",
            "source_artifact": "manifests/gcbte_status_table.csv; reports/metric_system_for_digital_twin_wind_application.md",
        },
        {
            "limitation_id": "L7",
            "limitation": "S1/S2 are negative sensitivity tests, not optimized design proposals.",
            "current_evidence": "S1 and S2 reduce or fail to improve global z~2 m mean VR while only producing sparse local directional response.",
            "claim_boundary": "Do not write S1/S2 as successful interventions.",
            "required_next_evidence": "Design S3-Sn wind-sector-coupled interventions using inlet-sector alignment, pressure-exchange paths and local enclosure continuity; rerun the same FluidX3D protocol and compare S0/S1/S2/Sn.",
            "upgrade_path": "negative design sensitivity -> positive design optimization evidence",
            "priority": "high_for_design_application_claims",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv; reports/claim_boundary.md",
        },
        {
            "limitation_id": "L8",
            "limitation": "Morphology rules are sample-internal screening descriptors.",
            "current_evidence": "101-component morphology analysis supports staged near-to-context recovery and directional fingerprints, but model explanatory power remains limited.",
            "claim_boundary": "Do not present morphology thresholds as universal causal laws.",
            "required_next_evidence": "Replicate the same morphology pipeline across additional campus blocks, seasons, grid levels and design variants; test out-of-sample performance and robustness.",
            "upgrade_path": "sample-internal descriptor -> transferable morphology rule",
            "priority": "medium_for_generalization_claims",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "reports/basic_morphology_multivariate_robustness.md; reports/building_form_wind_mechanism_synthesis.md",
        },
    ]


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    escaped = [
        {field: str(row.get(field, "")).replace("|", "\\|") for field in fields}
        for row in rows
    ]
    return pd.DataFrame(escaped)[fields].to_markdown(index=False)


def write_reports(rows: list[dict[str, str]]) -> None:
    fields = [
        "limitation_id",
        "limitation",
        "claim_boundary",
        "required_next_evidence",
        "upgrade_path",
        "priority",
    ]
    report = f"""# Experiment 3 Limitations and Future Validation Roadmap

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This roadmap turns the remaining Experiment 3 claim boundaries into a
reviewer-facing validation plan. It does not add new CFD, field, wind-tunnel,
pollutant or CityLBM-Grasshopper results. It specifies what evidence would be
needed to upgrade the current screening study into stronger engineering or
regulatory claims.

## Limitation-to-Validation Matrix

{md_table(rows, fields)}

## Manuscript Positioning

The current manuscript can confidently state a FluidX3D-native
digital-twin-to-CFD screening workflow and a staged building-form
interpretation for the TUM2TWIN campus core. The next experimental stage should
prioritize field/wind-tunnel validation and calibrated wind-climate coupling if
the target claim is predictive accuracy or comfort compliance. If the target
claim is design application, the highest-yield next experiment is not another
simple porosity opening but an S3-Sn set of wind-sector-coupled interventions.
"""
    write_text(REP / "experiment3_limitations_future_validation_roadmap.md", report)

    zh = """# 实验 3 局限性与后续验证路线图段落

evidence_type: newly_run + preexisting_artifact + blocked

本研究的局限性不是实验失败，而是筛查型数字孪生风环境研究与工程合规评价之间的证据边界。当前 TUM2TWIN 实验已经完成数据层分离、CFD-ready 几何准备、FluidX3D 八风向筛查、ParaView/Rhino 审查资产、建筑形态机制解释和 S1/S2 设计敏感性测试，但尚未形成现场实测或风洞闭环。因此，本文只能主张校园核心区存在行人层低速与通风不足的筛查证据，不能主张实测验证后的预测精度。

第二个边界来自气候输入。Open-Meteo 2024 方向权重用于检验低速结论对代理风向权重的敏感性，但它不是校准后的场地风玫瑰，也不能支撑 Lawson、NEN 8100 或 AIJ 年度超越概率评价。若后续论文或工程报告需要转向正式舒适/安全合规，必须接入多年气象站或现场风观测，定义活动类型阈值，并计算行人高度受体点的年度超越概率。

第三个边界来自数值协议。dx = 2 m、八风向和三个后 spin-up 样本足以支持筛查级复现，但 residual history、完整网格无关性和更长时间统计尚未闭合。后续工作应保存监测点时间序列，补充 3 m/2 m/1 m 或等效分辨率敏感性，并报告网格收敛或不确定性范围。只有在这一步之后，数值方法部分才适合从“透明筛查协议”升级为“更强数值收敛证据”。

第四个边界与设计应用有关。S1/S2 给出的不是优化成功，而是有价值的负向敏感性证据：单通道 relief corridor 与 network porosity 均未改善全局行人层风速。这提示后续 S3-Sn 不应继续机械增加孔隙面积，而应围绕有效来流扇区、动量入口、压力交换路径和局地围合连续性设计风向耦合干预。若这些方案能够在同一 FluidX3D 协议下改善 mean VR 并降低低速比例，设计应用结论才可以从“筛除无效假设”升级为“提出有效干预策略”。

第五个边界是数字孪生模型本身。本文已经证明视觉真实与 CFD 碰撞就绪不同，但 GCBTE 尚未被计算，CityLBM-Grasshopper 端到端也尚未实跑。因此，当前最稳妥的论文定位仍是 FluidX3D-native digital-twin-to-CFD screening with CityLBM-compatible geometry preparation。若要进一步强化数字孪生创新性，需要从 3DGS 或影像重建结果中提取独立碰撞边界，并以 LoD3/闭合棱柱为 ground truth 计算 IoU、Chamfer/Hausdorff 和 voxel-mask agreement；若要强化 CityLBM 应用性，则需要补充 Grasshopper 文件、运行截图、输入输出日志和结果图像。
"""
    write_text(PAPER / "experiment3_limitations_future_validation_roadmap_zh.md", zh)

    en = """# Experiment 3 Limitations and Future Validation Roadmap Paragraphs

evidence_type: newly_run + preexisting_artifact + blocked

The limitations of this study are not treated as experimental failure, but as the evidence boundary between digital-twin wind screening and engineering compliance assessment. The current TUM2TWIN experiment completes data-layer separation, CFD-ready geometry preparation, FluidX3D eight-direction screening, ParaView/Rhino review assets, building-form mechanism interpretation and S1/S2 design-sensitivity tests. It does not close a field-measurement or wind-tunnel validation loop. The manuscript can therefore claim screening evidence for pedestrian-layer low-speed and ventilation insufficiency, but not measured predictive accuracy.

A second boundary concerns wind-climate input. Open-Meteo 2024 directional weighting is used to test whether the low-speed conclusion is sensitive to a proxy wind-direction layer. It is not a calibrated site wind rose and cannot support Lawson, NEN 8100 or AIJ annual exceedance-probability assessment. To upgrade the study to formal comfort or safety compliance, future work must introduce multi-year weather-station or on-site wind observations, define activity-specific thresholds and compute annual exceedance probabilities at pedestrian receptors.

A third boundary concerns numerical evidence. The dx = 2 m, eight-direction and three post-spin-up-sample protocol is sufficient for screening-level reproduction, but residual histories, full grid independence and longer temporal statistics are not closed. Future work should archive monitor-point histories, add 3 m/2 m/1 m or equivalent resolution sensitivity and report grid-convergence or uncertainty ranges. Only after this step should the numerical method claim be upgraded from transparent screening protocol to stronger convergence evidence.

The fourth boundary concerns design application. S1/S2 are not successful optimizations; they are useful negative sensitivity evidence. Neither the relief corridor nor the network-porosity intervention improves the global pedestrian-layer speed field. This indicates that S3-Sn should not simply increase opening area. Future interventions should be coupled to effective inflow sectors, momentum-entry paths, pressure-exchange routes and local enclosure continuity. If these interventions improve mean VR and reduce low-speed ratio under the same FluidX3D protocol, the design claim could be upgraded from rejecting ineffective hypotheses to proposing effective strategies.

The fifth boundary concerns the digital-twin model itself. The study demonstrates that visual realism and CFD collision readiness are separable, but GCBTE has not been computed and the CityLBM-Grasshopper chain has not been executed end-to-end. The safest manuscript positioning remains FluidX3D-native digital-twin-to-CFD screening with CityLBM-compatible geometry preparation. To strengthen digital-twin novelty, future work should extract an independent collision boundary from 3DGS or image-reconstruction outputs and compare it with LoD3/closed-prism ground truth using IoU, Chamfer/Hausdorff distance and voxel-mask agreement. To strengthen CityLBM application evidence, the archive would need a Grasshopper file, execution screenshots, input-output logs and result images.
"""
    write_text(PAPER / "experiment3_limitations_future_validation_roadmap_en.md", en)


def upsert_outputs(rows: list[dict[str, str]], key_count: int) -> None:
    write_csv(
        MAN / "experiment3_limitations_future_validation_roadmap.csv",
        rows,
        [
            "limitation_id",
            "limitation",
            "current_evidence",
            "claim_boundary",
            "required_next_evidence",
            "upgrade_path",
            "priority",
            "evidence_type",
            "source_artifact",
        ],
    )

    evidence_rows = [
        {
            "claim": "Experiment 3 limitations and future validation roadmap was generated from the current blocked claims and evidence boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_limitations_future_validation_roadmap.csv; reports/experiment3_limitations_future_validation_roadmap.md",
        },
        {
            "claim": "Bilingual limitations and future-work paragraphs were drafted without upgrading blocked claims into completed results.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_limitations_future_validation_roadmap_zh.md; paper_text/experiment3_limitations_future_validation_roadmap_en.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Limitations and validation roadmap readiness",
        "metric": "limitation-to-validation matrix / bilingual limitation paragraphs / claim-upgrade conditions",
        "value": f"{len(rows)} limitations / {key_count} source key-result rows before roadmap upsert",
        "source_artifact": "manifests/experiment3_limitations_future_validation_roadmap.csv; reports/experiment3_limitations_future_validation_roadmap.md",
        "paper_safe_claim": "Experiment 3 has a reviewer-facing limitation and validation roadmap that keeps stronger claims conditional on future evidence.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [key_row],
        "claim_layer",
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )

    claim_path = DRAFT / "experiment3_claim_verification.csv"
    if claim_path.exists():
        claim_rows = read_csv_rows(claim_path)
        fieldnames = list(claim_rows[0].keys()) if claim_rows else [
            "claim_layer",
            "evidence_type",
            "source",
            "value",
            "paper_safe_claim",
            "claim_readiness",
        ]
        row = {
            "claim_layer": "module_claim_LIMITATIONS_ROADMAP",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_limitations_future_validation_roadmap.csv; reports/experiment3_limitations_future_validation_roadmap.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Limitations and future validation roadmap preserve blocked claims and define evidence needed for claim upgrades.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        claim_rows = [item for item in claim_rows if item.get("claim_layer") != "module_claim_LIMITATIONS_ROADMAP"]
        claim_rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(claim_path, claim_rows, fieldnames)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    key_count = len(pd.read_csv(FIG / "final_integrated_key_result_matrix.csv"))
    rows = build_rows()
    write_reports(rows)
    upsert_outputs(rows, key_count)
    print("limitation_rows", len(rows))
    print("key_result_rows_before_roadmap_upsert", key_count)
    print("wrote limitations and validation roadmap")


if __name__ == "__main__":
    main()
