from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def upsert_csv(path: Path, key_field: str, item: dict[str, str], fieldnames: list[str]) -> None:
    rows = read_csv(path) if path.exists() else []
    updated = False
    for row in rows:
        if row.get(key_field) == item[key_field]:
            row.update(item)
            updated = True
            break
    if not updated:
        rows.append(item)
    write_csv(path, rows, fieldnames)


def value(matrix: list[dict[str, str]], claim_layer: str) -> str:
    for row in matrix:
        if row.get("claim_layer") == claim_layer:
            return row.get("value", "")
    return "[RESULT_NEEDED]"


def build_evidence_map(matrix: list[dict[str, str]]) -> list[dict[str, str]]:
    layers = {
        "P1_positioning": "Geometry-to-CFD readiness",
        "P2_protocol": "FluidX3D numerical protocol transparency",
        "P3_baseline": "S0 baseline pedestrian screening",
        "P4_vertical_climate": "Vertical recovery",
        "P5_morphology": "Building-form wind mechanism synthesis",
        "P6_design": "S1 design sensitivity",
        "P7_boundary": "Limitations and validation roadmap readiness",
    }
    rows: list[dict[str, str]] = []
    for paragraph_id, layer in layers.items():
        source_row = next((row for row in matrix if row.get("claim_layer") == layer), {})
        rows.append(
            {
                "paragraph_id": paragraph_id,
                "claim_layer": layer,
                "evidence_type": source_row.get("evidence_type", ""),
                "key_value": source_row.get("value", ""),
                "source_artifact": source_row.get("source_artifact", ""),
                "paper_safe_use": source_row.get("paper_safe_claim", ""),
                "blocked_wording": "不得写成实测验证、年度舒适/安全合规、污染物预测、GCBTE闭环、CityLBM-GH端到端完成或成功优化。",
            }
        )
    return rows


def build_clean_text(matrix: list[dict[str, str]]) -> tuple[str, str, str]:
    baseline = value(matrix, "S0 baseline pedestrian screening")
    vertical = value(matrix, "Vertical recovery")
    climate = value(matrix, "Climate-proxy sensitivity")
    gcri = value(matrix, "Geometry-to-CFD readiness")
    protocol = value(matrix, "FluidX3D numerical protocol transparency")
    mechanism = value(matrix, "Building-form wind mechanism synthesis")
    stage = value(matrix, "Morphology stage transition")
    fingerprint = value(matrix, "Morphology directional fingerprint")
    s1 = value(matrix, "S1 design sensitivity")
    s2 = value(matrix, "S2 design sensitivity")
    trade = value(matrix, "Directional local trade-off")

    title = "真实城市数字孪生数据到 CFD-ready 风环境筛查的应用转化：基于 TUM2TWIN 校园街区的 FluidX3D 实验"

    abstract = f"""# 实验3清洁中文 SCI 文本包

evidence_type: newly_run + preexisting_artifact + blocked

## 建议题名

{title}

## 中文摘要

本文面向真实城市数字孪生数据在城市风环境模拟中的应用落地问题，构建了一个基于 TUM2TWIN Downtown 校园街区的 FluidX3D-native 风环境筛查实验。与前序 AIJ Case A 和 Case E 的基准/验证定位不同，本实验不重新宣称求解器精度，而是评估视觉真实的数字孪生数据如何转化为可体素化、可复现、可审计的 CFD-ready 几何。研究将 UAS/photogrammetry/Rhino 资产用于场景范围、贴图外观和人工一致性审查，将 LoD/OBJ/CAD-derived 闭合几何用于刚性碰撞边界，并通过 Geometry-to-CFD Readiness Index 记录视觉模型与碰撞边界之间的可计算性差异。核心结果显示，研究区行人高度的主要问题是低风速和通风不足，而不是强风风险：S0 基准在 z~2 m 的 mean VR / 低风速比例为 {baseline}，z~40 m 则为 {vertical}。Open-Meteo 2024 方向代理加权后的 z~2 m 结果为 {climate}，支持方向权重敏感性讨论，但不构成年度舒适/安全合规评价。建筑形态分析进一步表明，风速恢复应被解释为“近立面低速饱和 - 20-50 m 局地恢复 - 风向扇区响应”的分阶段机制，而不是单一高度、占地面积或孔隙率变量的结果。S1/S2 设计敏感性结果为近零或负向，说明几何孔隙面积本身不足以恢复行人层通风，干预应与有效来流扇区、动量入口和压力交换路径耦合。本文贡献在于建立了真实数字孪生数据到 FluidX3D 风环境筛查的证据链，并将校园街区风环境问题转化为可解释的建筑形态诊断；当前证据不支持现场验证、年度规范合规、污染物扩散、GCBTE 闭环或 CityLBM-Grasshopper 端到端运行声明。

## 关键词

城市风环境；数字孪生；TUM2TWIN；FluidX3D；CFD-ready 几何；行人层通风；建筑形态参数
"""

    body = f"""# 实验3清洁中文 SCI 正文段落

evidence_type: newly_run + preexisting_artifact + blocked

## 研究定位

本实验位于 AIJ Case A 和 Case E 之后，其任务不是再次证明求解器精度，而是检验真实城市数字孪生数据能否被转化为风环境模拟和设计解释可使用的实验对象。TUM2TWIN Downtown 数据同时包含 photogrammetry/Rhino/OBJ 视觉资产、语义或 LoD 建筑几何、CAD-derived 模型和立面语义参考。本文将这些数据按功能分层：视觉资产用于真实场景核验和模型范围审查，语义/LoD/CAD-derived 闭合几何用于 CFD/LBM 刚性碰撞边界，FluidX3D 输出用于行人层风速比和形态响应筛查。这一分层是本文的方法核心，因为视觉真实并不等价于可计算、闭合、可体素化的碰撞边界。

## 数据到 CFD-ready 几何

几何准备结果显示，数字孪生底层模型存在明显的“视觉一致性 - CFD 就绪性”差异。GCRI 对 photogrammetry visual STL、core closed-prism collision 和 district prism collision 的评分为 {gcri}。这说明 photogrammetry 或 3DGS-like 资产适合用于场景真实性、贴图外观和分析对象一致性审查，但不应直接作为最终刚性碰撞边界。相反，经过 z0 对齐、闭合修复、语义分层和 STL/体素化检查的 LoD/OBJ/CAD-derived 几何更适合作为 FluidX3D 输入。由此，数字孪生在风环境研究中的价值不只是“更真实的可视化”，而是提供了可追溯的数据分层和几何转换路径。

## 数值协议

核心算例采用 FluidX3D 筛查协议，数值设定记录为 {protocol}。该协议足以支持筛查级复现和审稿核查，但不能替代残差收敛、完整网格无关性、现场验证或年度舒适概率评估。本文所有速度结果均以 VR = U/Uref 组织，并输出 mean、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 2024 仅作为方向权重代理，用于判断主要低速结论是否对方向权重敏感，不能写成正式风玫瑰或规范合规依据。

## 基准风环境结果

S0 基准结果表明，TUM Downtown 校园核心区的主要行人风环境问题是持续低速和通风不足，而不是强风危险。z~2 m 行人层 mean VR / 低速比例为 {baseline}，而 z~40 m 为 {vertical}。这说明上部流场已经恢复，但近地层仍被建筑围合、院落边界和街道连接关系强烈遮蔽。换言之，屋顶以上风速恢复不能被用来替代入口、院落、街道转角和步行路径的独立行人层评估。

## 气候代理权重

Open-Meteo 2024 方向代理加权后的 z~2 m mean VR / 低速比例为 {climate}，与八风向等权结果接近。这个结果可支持“当前低速格局对代理方向权重不敏感”的筛查级判断，但不能支持 Lawson、NEN 8100 或 AIJ 年度舒适/安全超越概率评价。若论文需要正式舒适分区，仍需接入校准风气候、阈值超越概率和现场或风洞验证。

## 建筑形态与风环境机制

建筑形态分析表明，该校园街区的风速恢复不宜用 LCZ 标签或单一形态变量概括，而应使用更基础、可迁移的建筑形态参数描述。当前证据支持的机制为 {mechanism}。更具体地说，{stage}；同时，{fingerprint}。这意味着 0-20 m 近立面带主要反映低速饱和，20-50 m 局地背景带才更能暴露建筑形态造成的恢复差异。有效通风恢复不仅表现为更高的局地 mean VR，还应表现为对不同来流扇区的响应能力。因而，建筑高度、平面延展、局地建成比例和 50 m 扇区围合度需要组合解释，而不能被简化为单一高度或孔隙率效应。

## 设计敏感性

S1/S2 干预结果提供的是负向设计证据，而不是优化成功。S1 的 z~2 m mean VR / 低速比例变化为 {s1}，S2 为 {s2}，方向性局部 trade-off 为 {trade}。这说明单条 relief corridor 或三通道 network porosity 均未恢复全局行人层通风；即使局部单元出现方向性响应，新开敞单元仍嵌在低速背景中。由此得到的设计认识是：校园核心区的通风改善不能停留在增加孔隙面积或通道数量，而应将开口布置、有效来流扇区、动量入口、压力交换路径和局地围合连续性共同设计。

## 结论

本实验证明，TUM2TWIN 真实校园数字孪生数据可以通过视觉审查、语义/LoD 几何重构、闭合碰撞体生成、FluidX3D 八风向筛查和 ParaView/Rhino 人工审核，形成可复现的城市风环境应用实验。最稳妥的论文定位是：FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation。当前证据支持数字孪生数据转换路径、行人层低速筛查、建筑形态机制解释和 S1/S2 负向设计敏感性结论；不支持现场验证、风洞闭环、年度舒适/安全合规、污染物扩散预测、GCBTE 误差闭合、CityLBM-Grasshopper 端到端执行或成功设计优化声明。
"""

    captions = """# 实验3清洁中文图表说明

evidence_type: newly_run + preexisting_artifact + blocked

## Fig. E3-1

TUM Downtown 校园核心区行人高度 FluidX3D/VTK 风速比筛查图。该图来自 dx=2 m、八个来流方向、三个后 spin-up 样本的 core closed-prism collision 算例，用于人工审查低速区、方向一致性和建筑周边滞风格局。该图支持筛查级低通风解释，不支持年度舒适合规、现场验证或污染物扩散结论。

## Fig. E3-2

基础建筑形态参数与 20-50 m 局地背景风速响应的多变量稳健性分析。图中排序回归系数和置换重要性用于说明局地围合、平均高度和综合围合指标比单体占地面积、延展率或紧凑度更适合解释样本内风速差异。由于交叉验证解释力有限，该图应作为可解释筛查证据，而不是高精度预测模型。

## Fig. E3-3

S1/S2 设计敏感性场景在行人高度的方向性局部 trade-off。该图比较不同来流方向下 common open cells 的风速比变化。S2 的局部正响应略强于 S1，但改善单元稀疏，新开敞单元仍处于低速状态。因此该图是负向设计证据，说明几何孔隙面积本身不足以恢复校园核心区行人层通风。

## Fig. E3-4

0-20 m 近立面带到 20-50 m 局地背景带的风速恢复阈值规则筛查。分析在同一组 101 个建筑构件上比较近立面与局地背景响应，并提取样本内 tertile 组合规则。该图只能支持数字孪生样本内设计筛查，不能作为通用规范阈值或现场验证结论。

## Fig. E3-S5

20-50 m 局地背景带的建筑形态方向性指纹分析。该图将 101 个保留建筑构件的八风向 mean VR 范围、方向响应比、最佳响应风向与基础形态参数和阶段转化类型关联起来。persistent shelter 构件同时具有较低 mean VR 和较低方向范围，而 near-to-context recovery 与 directionally reactive 构件表现出更强的来流扇区响应。该图支持数字孪生设计筛查，不支持现场验证的因果阈值或年度风玫瑰合规评价。

## Table E3-1

实验3面向论文的一页式关键结果矩阵。该表整合 S0 基准、垂向恢复、Open-Meteo 代理权重、S1/S2 设计敏感性、方向性 trade-off、形态稳健性、阶段转化、方向性指纹和 GCRI，并逐行给出 evidence_type、来源文件和论文安全表述。

## Table E3-2

实验3完成度与论文可用性审计矩阵。该表区分已完成、筛查级完成、需弱化和阻塞的模块，明确标注现场数据、年度舒适合规、污染物扩散、GCBTE 和 CityLBM-Grasshopper 端到端执行的缺口。

## Table E3-3

Geometry-to-CFD Readiness Index 评分表。该表比较 photogrammetry visual mesh、core closed-prism collision 和 district prism collision 在水密性、非流形错误、语义层完整性、坐标/单位一致性、STL 导出和体素化成功等方面的就绪度，说明视觉真实与 CFD 碰撞边界可用性是不同属性。
"""
    return abstract, body, captions


def main() -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    MAN.mkdir(parents=True, exist_ok=True)

    matrix = read_csv(FIG / "final_integrated_key_result_matrix.csv")
    evidence_map = build_evidence_map(matrix)
    abstract, body, captions = build_clean_text(matrix)

    write_csv(
        MAN / "experiment3_clean_chinese_manuscript_evidence_map.csv",
        evidence_map,
        [
            "paragraph_id",
            "claim_layer",
            "evidence_type",
            "key_value",
            "source_artifact",
            "paper_safe_use",
            "blocked_wording",
        ],
    )
    write_text(PAPER / "experiment3_clean_chinese_sci_package_zh.md", abstract + "\n" + body)
    write_text(PAPER / "experiment3_clean_chinese_core_paragraphs_zh.md", body)
    write_text(PAPER / "experiment3_clean_chinese_figure_table_captions_zh.md", captions)
    write_text(PAPER / "experiment3_final_sci_discussion_conclusion_zh.md", body)
    write_text(PAPER / "experiment3_sci_manuscript_module_zh.md", abstract + "\n" + body)

    report = """# Experiment 3 Clean Chinese Manuscript Pack Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This audit records a clean UTF-8 Chinese manuscript layer for Experiment 3.
It fixes the paper-facing writing surface by providing non-mojibake Chinese
title, abstract, methods, results, discussion, conclusion and figure/table
caption text while preserving the existing evidence boundaries.

## Outputs

- `paper_text/experiment3_clean_chinese_sci_package_zh.md`
- `paper_text/experiment3_clean_chinese_core_paragraphs_zh.md`
- `paper_text/experiment3_clean_chinese_figure_table_captions_zh.md`
- `paper_text/experiment3_final_sci_discussion_conclusion_zh.md`
- `paper_text/experiment3_sci_manuscript_module_zh.md`
- `manifests/experiment3_clean_chinese_manuscript_evidence_map.csv`

## Boundary

The clean Chinese text does not add new CFD evidence. It converts verified
Experiment 3 evidence into readable SCI-style Chinese and keeps blocked claims
explicit: field validation, annual comfort/safety compliance, pollutant
dispersion, GCBTE closure, CityLBM-Grasshopper end-to-end execution and
successful design optimization remain unsupported.
"""
    write_text(REP / "experiment3_clean_chinese_manuscript_pack_audit.md", report)

    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        "claim_layer",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Clean Chinese manuscript readiness",
            "metric": "clean UTF-8 Chinese paper package / evidence-mapped paragraphs / clean figure-table captions",
            "value": f"3 clean Chinese text files / {len(evidence_map)} evidence-mapped paragraph units",
            "source_artifact": "paper_text/experiment3_clean_chinese_sci_package_zh.md; manifests/experiment3_clean_chinese_manuscript_evidence_map.csv",
            "paper_safe_claim": "Experiment 3 has a readable clean-Chinese SCI manuscript layer that preserves evidence boundaries and avoids mojibake in the canonical Chinese discussion/module files.",
        },
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )
    upsert_csv(
        MAN / "evidence_inventory.csv",
        "claim",
        {
            "claim": "Clean UTF-8 Chinese SCI manuscript text was generated for Experiment 3 and mapped to the current evidence matrix.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/experiment3_clean_chinese_sci_package_zh.md; manifests/experiment3_clean_chinese_manuscript_evidence_map.csv; reports/experiment3_clean_chinese_manuscript_pack_audit.md",
        },
        ["claim", "evidence_type", "source"],
    )

    print("clean_chinese_evidence_units", len(evidence_map))
    print("wrote paper_text/experiment3_clean_chinese_sci_package_zh.md")
    print("wrote paper_text/experiment3_clean_chinese_core_paragraphs_zh.md")
    print("wrote paper_text/experiment3_clean_chinese_figure_table_captions_zh.md")
    print("wrote reports/experiment3_clean_chinese_manuscript_pack_audit.md")


if __name__ == "__main__":
    main()
