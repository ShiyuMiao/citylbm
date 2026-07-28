from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
REPO_ROOT = ROOT.parents[4]
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
PAPER = ROOT / "paper_text"
REPORTS = ROOT / "reports"
DRAFT_DIR = REPO_ROOT / "academic-paper-writer" / "paper-drafts"


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def read_matrix_value(matrix: pd.DataFrame, layer: str) -> str:
    row = matrix[matrix["claim_layer"] == layer]
    if row.empty:
        raise ValueError(f"missing claim layer: {layer}")
    return str(row.iloc[0]["value"])


def ref_number(ref_id: str) -> str:
    return f"[{int(ref_id[1:])}]"


def ref_marker(*ids: str) -> str:
    return ",".join(ref_number(rid).strip("[]") for rid in ids).join(["[", "]"])


def reference_lines(refs: pd.DataFrame) -> list[str]:
    ordered = refs.copy()
    ordered["ref_num"] = ordered["ref_id"].str[1:].astype(int)
    ordered = ordered.sort_values("ref_num")
    lines: list[str] = []
    for _, row in ordered.iterrows():
        num = int(str(row["ref_id"])[1:])
        doi = "" if pd.isna(row.get("doi")) or not str(row.get("doi")).strip() else f" doi:{row['doi']}."
        url = "" if pd.isna(row.get("url")) or not str(row.get("url")).strip() else f" {row['url']}"
        lines.append(
            f"[{num}] {row['authors']} ({row['year']}). {row['title']}. {row['source']}.{doi}{url}"
        )
    return lines


def build_claim_verification(matrix: pd.DataFrame, claims: pd.DataFrame, figure_plan: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in matrix.iterrows():
        rows.append(
            {
                "claim_or_asset": row["claim_layer"],
                "evidence_type": row["evidence_type"],
                "source": row["source_artifact"],
                "value_or_status": row["value"],
                "paper_use": row["paper_safe_claim"],
                "verification_status": "usable_in_generic_sci_section",
            }
        )
    for _, row in claims.iterrows():
        rows.append(
            {
                "claim_or_asset": f"module_claim_{row['claim_id']}",
                "evidence_type": row["evidence_type"],
                "source": row["source"],
                "value_or_status": row["claim_readiness"],
                "paper_use": row["claim"],
                "verification_status": row["claim_readiness"],
            }
        )
    for _, row in figure_plan.iterrows():
        rows.append(
            {
                "claim_or_asset": row["callout_id"],
                "evidence_type": "newly_run + preexisting_artifact",
                "source": row["recommended_file"],
                "value_or_status": "figure_or_table_callout",
                "paper_use": row["purpose"],
                "verification_status": "available_for_manual_review",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    refs = pd.read_csv(MAN / "verified_references_for_sci_discussion.csv")
    claims = pd.read_csv(MAN / "experiment3_manuscript_module_claims.csv")
    figure_plan = pd.read_csv(MAN / "experiment3_manuscript_figure_table_plan.csv")
    audit = pd.read_csv(FIG / "experiment3_completion_audit_matrix.csv")

    baseline = read_matrix_value(matrix, "S0 baseline pedestrian screening")
    vertical = read_matrix_value(matrix, "Vertical recovery")
    climate = read_matrix_value(matrix, "Climate-proxy sensitivity")
    morph = read_matrix_value(matrix, "Morphology robustness")
    threshold = read_matrix_value(matrix, "Morphology threshold design rule")
    s1 = read_matrix_value(matrix, "S1 design sensitivity")
    s2 = read_matrix_value(matrix, "S2 design sensitivity")
    trade = read_matrix_value(matrix, "Directional local trade-off")
    gcri = read_matrix_value(matrix, "Geometry-to-CFD readiness")

    refs_text = "\n".join(reference_lines(refs))

    blueprint = f"""# Section Blueprint: Experiment 3 TUM2TWIN Digital-Twin Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Section Contract

- Reader state before section: the reader has seen AIJ Case A and Case E as benchmark/validation support and now needs to understand why a real digital-twin case is needed.
- Required move 1: distinguish visual digital-twin assets from CFD collision geometry.
- Required move 2: state FluidX3D setup, aggregation level, directions, samples and metrics before reporting values.
- Required move 3: report baseline low-speed pattern, vertical recovery and climate-proxy sensitivity without claiming annual comfort compliance.
- Required move 4: connect building form to wind response using basic morphology descriptors and the near-to-context threshold rule.
- Required move 5: interpret S1/S2 as negative design-sensitivity evidence, not successful optimization.
- Required move 6: close with digital-twin application value and explicit blockers.

## Evidence Hooks

- Baseline: `{baseline}`
- Vertical recovery: `{vertical}`
- Climate proxy: `{climate}`
- Morphology robustness: `{morph}`
- Threshold screening: `{threshold}`
- S1/S2: `{s1}`; `{s2}`; `{trade}`
- GCRI: `{gcri}`

## Figure and Table Callouts

{figure_plan.to_markdown(index=False)}

## Failure Checks

- Do not write field validation, wind-tunnel closure, annual Lawson/NEN/AIJ compliance, pollutant dispersion, GCBTE closure or CityLBM-GH end-to-end execution as completed.
- Do not write the morphology threshold rule as a universal design threshold.
- Do not use Open-Meteo 2024 as a measured site wind rose.
"""

    paper_zh = f"""# 实验3论文正文草稿：TUM2TWIN 数字孪生校园风环境应用

evidence_type: newly_run + preexisting_artifact + blocked

## 研究目的与定位

在前序 AIJ Case A 与 Case E 已用于求解器基准和工作流验证的前提下，实验3的目标不是再次证明求解器精度，而是检验真实城市数字孪生数据能否被可靠转化为风环境模拟和设计解释所需的 CFD-ready 输入。TUM2TWIN 数据包含 UAS 影像/摄影测量网格、纹理化三维模型、语义建筑数据、CAD/OBJ/Rhino 几何以及立面语义基准等多类资产；这些资产在风环境研究中的功能并不相同。摄影测量或 3DGS-like 资产具有真实外观和场景一致性审查价值，但不应直接等同于封闭刚性碰撞边界；真正进入 FluidX3D/CityLBM 的固体边界需要由语义 LoD 或 CAD-derived 闭合几何生成。这一定位与行人风环境 CFD 研究对不确定性、舒适评价链条和校园尺度决策支持的要求一致 {ref_marker('R1','R5','R6')}。

## 数据分层与 CFD-ready 几何构建

本研究将 TUM2TWIN 数据按照“视觉参照、语义/几何管理、碰撞边界、求解输入”四个层次组织。UAS photogrammetry mesh 与纹理化 OBJ/MTL/JPG 用于核验研究范围和真实外观；用户提供的 Rhino photogrammetry 模型用于确认分析对象与 TUM Downtown 校园街区视觉范围一致；LoD/OBJ/CAD-derived 几何用于构建 z0 对齐的闭合 STL 碰撞体；FluidX3D 输入则使用经过 QA 的 core closed-prism collision。几何就绪性通过 GCRI 记录，photogrammetry visual STL、core closed-prism collision 与 district prism collision 的得分分别为 `{gcri}`。这说明数字孪生底层模型的主要方法贡献不是简单提供“更漂亮”的模型，而是揭示视觉真实性与 CFD-ready 刚性边界之间的差异，并提供从真实场景到可计算几何的证据链 {ref_marker('R11','R12')}。

## FluidX3D 模拟与后处理协议

核心子域采用 dx=2 m 的 FluidX3D 设置，包含 8 个来流方向。每个方向在 spin-up 后抽取 8000、10000 和 12000 steps 三个样本，后处理先进行同风向时间平均，再计算八风向等权平均、Open-Meteo 2024 方向代理加权、竖向 VR 剖面、建筑形态响应和 S1/S2 设计敏感性。主要指标包括 mean VR、P75/P90/P95、VR<0.2 低速比例、VR>0.6 加速比例和 VR>1.0 高速比例。Open-Meteo 2024 仅作为方向权重敏感性层，不作为现场实测风玫瑰，也不用于正式年度舒适/安全合规评价 {ref_marker('R5','R7','R8','R9')}。

## 基准风环境结果

S0 基准结果显示，该校园核心区的主导问题不是强风危险，而是稳定的近地通风不足。z≈2 m 行人层 mean VR / 低速比例为 `{baseline}`，而 z≈40 m mean VR / 低速比例为 `{vertical}`。这一竖向差异说明，屋面以上流场恢复不能替代入口、院落、街道连通空间和行人路径的独立评价。Open-Meteo 2024 方向代理加权后，z≈2 m mean VR / 低速比例为 `{climate}`，与八风向等权结果非常接近。因此，本文可以写成“低速格局对该代理方向权重不敏感”，但不能写成年度 Lawson/NEN/AIJ 舒适或安全合规结论 {ref_marker('R5','R7','R10')}。

## 建筑形态与风速恢复机制

建筑形态分析将传统“围合街谷削弱通风”的认识推进到可定位的校园尺度诊断 {ref_marker('R2','R3','R4')}。0-20 m 近立面带几乎普遍滞风，难以区分不同建筑形式的影响；20-50 m 局地环境带更能反映风速恢复差异。多变量稳健性结果为 `{morph}`，说明基础形态参数具有解释价值，但不能被写成高精度预测模型。进一步的阈值规则分析将同一批 101 个建筑单元的 0-20 m 与 20-50 m 响应配对，结果为 `{threshold}`。因此，本实验在传统结论基础上提供的新认知是：在校园型连续街区中，风环境改善不宜只看单体建筑面积、伸长率或孔隙面积，而应在 20-50 m 尺度上同时识别局地暴露度、相对竖向尺度、平面连续性和外部动量进入条件。该规则是样本内数字孪生筛查证据，不是可直接外推的通用设计阈值。

## S1/S2 设计敏感性与负结果价值

为检验“增加孔隙是否能缓解低速”的设计假设，本研究构建了 S1 single light relief corridor 和 S2 three-corridor network porosity 两个几何敏感性场景，并使用与 S0 相同的 dx=2 m、8 风向、三样本后处理协议。S1 在 z≈2 m 的 mean VR / 低速比例变化为 `{s1}`，S2 为 `{s2}`。方向性 trade-off 进一步显示 `{trade}`。这些结果说明，S1/S2 不能作为成功优化方案；其论文价值在于提供负向设计证据，即几何孔隙面积如果没有与有效来流扇区、动量入口和压力交换路径耦合，就可能只是在低速背景中增加开敞空间，而不能恢复行人层通风。

## 讨论与应用意义

实验3的关键贡献在于建立了真实数字孪生数据到 CFD-ready 风环境筛查的落地链条，并把校园风环境问题从“是否出现强风区”转向“是否存在稳定通风不足及其形态原因”。相较理想街谷或简化建筑群模型，TUM2TWIN 案例保留了真实校园街区的复杂围合、入口、院落和街道连通关系，使风环境分析能够服务于前期筛查、问题定位和设计假设排除。S1/S2 的负结果并不削弱实验价值，反而说明数字孪生工作流可用于在投入更精细 CFD、风洞或现场监测前筛掉低效干预，并将后续设计聚焦到风向扇区耦合的入口廊道、围合解除和压力交换连续性。

## 局限性与证据边界

本文不宣称 TUM Downtown 实测风场验证、风洞闭环、正式年度舒适/安全合规、污染物扩散预测、S3-Sn 正向优化、GCBTE 误差闭合或 CityLBM-Grasshopper 端到端运行。Open-Meteo 2024 是方向权重代理，不是现场风玫瑰；S1/S2 是负向设计敏感性证据，不是最终设计方案；形态统计是解释性筛查，不是可替代 CFD 或现场测量的预测模型。后续若要进入合规评价，需要补充校准风玫瑰、阈值超越概率、网格/时间敏感性、实测或风洞闭环以及必要的污染物或热舒适耦合模拟。

## References

{refs_text}

## 待补充清单

- AUTHOR_INPUT_NEEDED: target journal and formatting/citation style.
- RESULT_NEEDED: onsite or wind-tunnel validation if field-validated accuracy is claimed.
- RESULT_NEEDED: annual comfort/safety exceedance calculation with calibrated wind climate if Lawson/NEN/AIJ compliance is claimed.
- RESULT_NEEDED: pollutant scalar transport if exposure or concentration hotspots are claimed.
- RESULT_NEEDED: CityLBM-Grasshopper end-to-end screenshot/logs if the final method title foregrounds CityLBM-GH rather than FluidX3D-native simulation.
"""

    paper_en = f"""# Experiment 3 Draft Section: TUM2TWIN Digital-Twin Campus Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Study Aim and Positioning

Following AIJ Cases A and E as the benchmark layer, Experiment 3 evaluates whether real urban digital-twin data can be translated into CFD-ready geometry and used for campus wind-screening and design interpretation. TUM2TWIN provides visual photogrammetry, semantic/CAD-derived geometry and Rhino/OBJ management assets. These layers are functionally different: photogrammetry and 3DGS-like assets are useful for visual audit and scene consistency, whereas FluidX3D/CityLBM collision boundaries require closed semantic or CAD-derived geometry. This boundary follows established pedestrian-wind CFD practice, where simulation uncertainty and comfort assessment chains must be stated before compliance claims are made {ref_marker('R1','R5','R6')}.

## Data-to-CFD Workflow

The workflow separates visual reference, semantic geometry, collision geometry and solver input. The textured photogrammetry mesh is used to audit the study extent; the user Rhino model confirms consistency with the TUM Downtown visual block; LoD/OBJ/CAD-derived data provide z0-aligned closed STL collision bodies; and the accepted core closed-prism geometry is used in FluidX3D. GCRI scores for the photogrammetry visual STL, core prism and district prism are `{gcri}`, showing that visual fidelity and CFD readiness are separable properties of the same digital twin {ref_marker('R11','R12')}.

## Simulation Protocol

The FluidX3D core-domain simulation uses dx=2 m, eight inflow directions and three post-spin-up samples at 8000, 10000 and 12000 steps. Metrics include mean VR, P75/P90/P95, VR<0.2 low-speed ratio, VR>0.6 acceleration ratio and VR>1.0 high-speed ratio. Open-Meteo 2024 is used only as a proxy directional weighting layer and not as a measured site wind rose or annual comfort-compliance input {ref_marker('R5','R7','R8','R9')}.

## Results

The S0 baseline indicates persistent pedestrian-layer ventilation insufficiency rather than a strong-wind hazard. At z~2 m, mean VR / low-speed ratio is `{baseline}`; at z~40 m it becomes `{vertical}`. Thus, above-roof recovery cannot substitute for pedestrian-space assessment in campus courtyards, entrances and connecting streets. The Open-Meteo proxy-weighted z~2 m mean VR / low-speed ratio is `{climate}`, close to the equal-weighted result, supporting the stability of the low-speed screening conclusion but not formal Lawson/NEN/AIJ compliance {ref_marker('R5','R7','R10')}.

Morphology analysis converts traditional canopy and canyon reasoning into a local digital-twin diagnosis {ref_marker('R2','R3','R4')}. The 0-20 m facade-adjacent band is almost uniformly sheltered, whereas the 20-50 m local-context band reveals morphology-dependent recovery. The multivariate robustness result is `{morph}`, so morphology variables should be treated as interpretable screening descriptors rather than a high-accuracy surrogate model. The threshold-rule addendum gives `{threshold}`, moving the design interpretation from isolated building size or opening area toward combined local exposure, relative vertical scale and plan continuity. The rule remains sample-internal and should not be generalized as a field-validated design threshold.

The S1/S2 design-sensitivity sequence tests whether additional porosity can relieve the low-speed condition. S1 changes z~2 m mean VR / low-speed ratio by `{s1}`, and S2 changes them by `{s2}`. Directional local response is `{trade}`. S1/S2 therefore provide negative design evidence: geometric porosity alone is insufficient unless coupled to effective inflow sectors, momentum entry and pressure-exchange paths.

## Discussion and Evidence Boundary

The main contribution of Experiment 3 is a traceable digital-twin-to-CFD application chain and a morphology-informed campus wind-screening interpretation. It does not claim field validation, wind-tunnel closure, annual comfort/safety compliance, pollutant dispersion, successful S3-Sn optimization, GCBTE closure or CityLBM-Grasshopper end-to-end execution. Future compliance work requires a calibrated wind rose, threshold exceedance probabilities, grid/time sensitivity, field or wind-tunnel closure and additional scalar or thermal coupling where relevant.

## References

{refs_text}
"""

    verification = build_claim_verification(matrix, claims, figure_plan)
    verification_path = DRAFT_DIR / "experiment3_claim_verification.csv"
    verification.to_csv(verification_path, index=False, encoding="utf-8-sig", lineterminator="\n")

    checklist = f"""# Experiment 3 Draft Verification Report

evidence_type: newly_run + preexisting_artifact + blocked

## Verification Summary

- Draft status: generic SCI section draft generated from archived Experiment 3 evidence.
- Evidence rows used: `{len(verification)}`
- References used: `{len(refs)}`
- Key result matrix rows: `{len(matrix)}`
- Figure/table callouts: `{len(figure_plan)}`
- Claim inventory rows: `{len(claims)}`

## Passed Checks

- Quantitative claims in the draft come from `figures/final_integrated_key_result_matrix.csv`.
- References are drawn from `manifests/verified_references_for_sci_discussion.csv`.
- Blocked claims remain explicit: field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution.
- The morphology threshold rule is framed as sample-internal screening evidence.
- The draft contains a single References section and a synchronized pending-debt list.

## Remaining Publication Debts

- AUTHOR_INPUT_NEEDED: target journal and final reference style.
- AUTHOR_INPUT_NEEDED: whether the paper title should say FluidX3D-native or CityLBM-compatible geometry package.
- RESULT_NEEDED: field/wind-tunnel validation before predictive-accuracy claims.
- RESULT_NEEDED: calibrated wind climate before annual comfort/safety compliance.
- RESULT_NEEDED: pollutant simulation before concentration or exposure claims.

## Output Files

- `academic-paper-writer/paper-drafts/paper_draft.md`
- `academic-paper-writer/paper-drafts/paper_draft_en.md`
- `academic-paper-writer/paper-drafts/section_blueprint.md`
- `academic-paper-writer/paper-drafts/experiment3_claim_verification.csv`
- `academic-paper-writer/paper-drafts/experiment3_publication_readiness_checklist.md`
- `paper_text/experiment3_sci_section_paper_draft_zh.md`
- `paper_text/experiment3_sci_section_paper_draft_en.md`
- `reports/experiment3_paper_draft_verification.md`
"""

    write_text_lf(DRAFT_DIR / "section_blueprint.md", blueprint)
    write_text_lf(DRAFT_DIR / "paper_draft.md", paper_zh)
    write_text_lf(DRAFT_DIR / "paper_draft_en.md", paper_en)
    write_text_lf(DRAFT_DIR / "experiment3_publication_readiness_checklist.md", checklist)
    write_text_lf(PAPER / "experiment3_sci_section_paper_draft_zh.md", paper_zh)
    write_text_lf(PAPER / "experiment3_sci_section_paper_draft_en.md", paper_en)
    write_text_lf(REPORTS / "experiment3_paper_draft_verification.md", checklist)

    print("wrote", DRAFT_DIR / "section_blueprint.md")
    print("wrote", DRAFT_DIR / "paper_draft.md")
    print("wrote", DRAFT_DIR / "paper_draft_en.md")
    print("wrote", verification_path)
    print("wrote", DRAFT_DIR / "experiment3_publication_readiness_checklist.md")
    print("wrote", PAPER / "experiment3_sci_section_paper_draft_zh.md")
    print("wrote", PAPER / "experiment3_sci_section_paper_draft_en.md")
    print("wrote", REPORTS / "experiment3_paper_draft_verification.md")


if __name__ == "__main__":
    main()
