from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"

for folder in [MAN, REP, PAPER, DRAFT]:
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def upsert(rows: list[dict[str, str]], key_field: str, item: dict[str, str]) -> list[dict[str, str]]:
    for row in rows:
        if row.get(key_field) == item.get(key_field):
            row.update(item)
            return rows
    rows.append(item)
    return rows


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("|" + "|".join(["---"] * len(fields)) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(out)


def protocol_value(protocol_rows: list[dict[str, str]], item: str) -> str:
    for row in protocol_rows:
        if row.get("protocol_item") == item:
            return row.get("value", "")
    return "AUTHOR_INPUT_NEEDED"


def build_statement_rows(
    key_matrix: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    protocol_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    grid = protocol_value(protocol_rows, "grid_and_domain")
    physical = protocol_value(protocol_rows, "physical_reference_values")
    lbm = protocol_value(protocol_rows, "lbm_conversion")
    sampling = protocol_value(protocol_rows, "sampling_protocol")

    return [
        {
            "statement_unit": "Data availability",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": "README.md; EXTERNAL_ARTIFACTS.md; manifests/data_manifest.csv; manifests/github_archive_manifest.csv",
            "paper_ready_statement": "Processed reports, manifests, scripts, selected geometry, figures, ParaView states and paper text are archived in the Experiment 3 GitHub package; full raw TUM2TWIN assets, texture folders, local ParaView, FluidX3D build files and full VTK outputs are external large artifacts documented in EXTERNAL_ARTIFACTS.md.",
            "boundary_or_author_input": "Authors should verify final journal-facing license wording against the original TUM2TWIN and Zenodo license records before submission.",
        },
        {
            "statement_unit": "Code availability",
            "evidence_type": "newly_run + preexisting_artifact",
            "source_artifact": "scripts/; cfd_ready/FluidX3D_case_template/; cfd_ready/CityLBM_GH_input_template/; scripts/rebuild_experiment3_paper_assets.ps1",
            "paper_ready_statement": "Postprocessing, morphology analysis, figure synthesis, claim-audit and manifest-refresh scripts are included; FluidX3D input templates and CityLBM-compatible geometry templates are archived for reproduction and interoperability review.",
            "boundary_or_author_input": "CityLBM-Grasshopper is an optional template in this archive and is not evidence of a completed end-to-end plugin run.",
        },
        {
            "statement_unit": "Reproducibility statement",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": "scripts/rebuild_experiment3_paper_assets.ps1; reports/github_archive_manifest_validation.md; manifests/evidence_inventory.csv",
            "paper_ready_statement": f"The canonical lightweight rebuild command is `& .\\scripts\\rebuild_experiment3_paper_assets.ps1`, which regenerates paper-facing CSV, report, paper-text and manifest assets from the archived processed evidence. Before this statement upsert the archive contained {len(key_matrix)} key-result rows and {len(evidence_rows)} evidence-inventory rows.",
            "boundary_or_author_input": "The GitHub package alone does not rerun full FluidX3D simulations unless external raw geometry, VTK outputs, FluidX3D binaries and the local solver environment are restored.",
        },
        {
            "statement_unit": "Computational resources and numerical protocol",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source_artifact": "manifests/fluidx3d_numerical_protocol_audit.csv; reports/fluidx3d_numerical_protocol_and_stability_audit.md",
            "paper_ready_statement": f"The core FluidX3D screening protocol records {grid}; {physical}; {lbm}; and {sampling}. These descriptors support screening-level reproduction and review of the numerical setup.",
            "boundary_or_author_input": "Do not invent GPU model, wall-clock time, residual convergence or complete grid-independence evidence; those remain absent or explicitly blocked unless separately measured.",
        },
        {
            "statement_unit": "Ethics and field-data statement",
            "evidence_type": "preexisting_artifact + blocked",
            "source_artifact": "manifests/data_manifest.csv; reports/claim_boundary.md; EXTERNAL_ARTIFACTS.md",
            "paper_ready_statement": "The current archive uses public/official digital-twin data records and locally generated CFD/postprocessing artifacts; it contains no newly collected human-subject data and no field wind-speed measurement campaign.",
            "boundary_or_author_input": "If the final paper reports institutional fieldwork, private imagery, or access-restricted data beyond this archive, authors must update this statement.",
        },
        {
            "statement_unit": "Funding, competing interests and author contributions",
            "evidence_type": "user_claim_needed",
            "source_artifact": "AUTHOR_INPUT_NEEDED",
            "paper_ready_statement": "AUTHOR_INPUT_NEEDED: funding, conflicts of interest, acknowledgements and CRediT author-contribution statements must be completed by the authors.",
            "boundary_or_author_input": "These statements cannot be inferred from the experiment archive and should not be fabricated.",
        },
    ]


def update_key_matrix(rows: list[dict[str, str]]) -> None:
    path = FIG / "final_integrated_key_result_matrix.csv"
    matrix = read_csv(path)
    item = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Submission statements readiness",
        "metric": "data/code availability / reproducibility / computational-resource / evidence-boundary statements",
        "value": f"{len(rows)} statement units / evidence-mapped journal-neutral package",
        "source_artifact": "manifests/experiment3_submission_statement_evidence_map.csv; reports/experiment3_submission_statement_package.md",
        "paper_safe_claim": "Experiment 3 has journal-neutral submission statements that distinguish archived GitHub files from external raw/VTK assets, solver-environment dependencies and blocked validation claims.",
    }
    matrix = upsert(matrix, "claim_layer", item)
    write_csv(path, matrix, ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"])


def update_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    evidence = read_csv(path)
    additions = [
        {
            "claim": "Journal-neutral data, code, reproducibility, computational-resource, ethics and author-input statements were generated from the current Experiment 3 archive.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "reports/experiment3_submission_statement_package.md; manifests/experiment3_submission_statement_evidence_map.csv",
        },
        {
            "claim": "Submission statements explicitly separate GitHub-embedded lightweight evidence from external TUM2TWIN raw assets, local FluidX3D/ParaView installations and full VTK outputs.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "EXTERNAL_ARTIFACTS.md; paper_text/experiment3_submission_statements_en.md; paper_text/experiment3_submission_statements_zh.md",
        },
    ]
    for item in additions:
        evidence = upsert(evidence, "claim", item)
    write_csv(path, evidence, ["claim", "evidence_type", "source"])


def update_claim_verification() -> None:
    path = DRAFT / "experiment3_claim_verification.csv"
    rows = read_csv(path)
    item = {
        "claim_or_asset": "module_claim_SUBMISSION_STATEMENTS",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source": "manifests/experiment3_submission_statement_evidence_map.csv; reports/experiment3_submission_statement_package.md",
        "value_or_status": "data/code/reproducibility/computational-resource statements complete with author-input placeholders",
        "paper_use": "Use as manuscript submission statements and reviewer-facing reproducibility boundary.",
        "verification_status": "paper_ready_with_boundary",
    }
    rows = upsert(rows, "claim_or_asset", item)
    write_csv(path, rows, ["claim_or_asset", "evidence_type", "source", "value_or_status", "paper_use", "verification_status"])


def write_reports(rows: list[dict[str, str]]) -> None:
    fields = ["statement_unit", "evidence_type", "source_artifact", "paper_ready_statement", "boundary_or_author_input"]
    write_csv(MAN / "experiment3_submission_statement_evidence_map.csv", rows, fields)

    report = f"""# Experiment 3 Submission Statement Package

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This package prepares journal-neutral submission statements for Experiment 3.
It does not add CFD results. It makes the final paper more auditable by
separating GitHub-embedded evidence, external large files, solver-environment
dependencies, and claims that remain blocked.

## Statement Evidence Map

{md_table(rows, fields)}

## Paper-Safe Use

Use these statements when the manuscript is framed as a FluidX3D-native
digital-twin-to-CFD wind-screening and building-form interpretation experiment
with a CityLBM-compatible geometry package. Do not use them to imply field
validation, annual comfort/safety compliance, pollutant dispersion, GCBTE
closure, CityLBM-Grasshopper end-to-end execution, or successful design
optimization.
"""
    write_text(REP / "experiment3_submission_statement_package.md", report)

    en = """# Experiment 3 Submission Statements

evidence_type: newly_run + preexisting_artifact + blocked

## Data Availability

The lightweight Experiment 3 archive contains processed reports, manifests, selected CFD-ready geometry, postprocessed statistical tables, paper-facing figures, ParaView state files, and manuscript text. Full raw TUM2TWIN downloads, complete texture folders, local ParaView installation files, local FluidX3D source/build files, and full VTK output matrices are not embedded in the GitHub package because of size and machine-specific environment constraints. Their provenance and local boundaries are recorded in `EXTERNAL_ARTIFACTS.md` and `manifests/data_manifest.csv`. License wording should be checked against the original TUM2TWIN and Zenodo records before journal submission.

## Code Availability

The archive includes the postprocessing, morphology-analysis, figure-generation, claim-audit and manifest-refresh scripts used to build the paper-facing outputs. The canonical lightweight rebuild command from the Experiment 3 release-package root is `& .\\scripts\\rebuild_experiment3_paper_assets.ps1`. FluidX3D case templates and CityLBM-compatible geometry templates are included, but the CityLBM-Grasshopper folder is an interoperability template rather than evidence of a completed end-to-end plugin execution.

## Reproducibility

The archived files are sufficient to audit the data-layer separation, CFD-ready geometry preparation, processed FluidX3D screening metrics, ParaView/manual-review assets, morphology-response analyses, figure/table narratives, and claim boundaries. Re-running the full CFD workflow requires re-downloading or restoring external TUM2TWIN assets, rebuilding or restoring FluidX3D, and regenerating the full VTK output set. The package does not claim field validation, formal annual comfort or safety compliance, pollutant dispersion, GCBTE closure, or successful design optimization.

## Computational Resources

The numerical protocol is recorded in `manifests/fluidx3d_numerical_protocol_audit.csv` and `reports/fluidx3d_numerical_protocol_and_stability_audit.md`, including dx, grid/domain size, reference velocity, air viscosity, LBM conversion, tau/Re descriptors, wind directions and sample steps. GPU model, wall-clock runtime, residual convergence and complete grid-independence evidence should not be invented and should be reported only if separately measured.

## Ethics, Funding and Competing Interests

The current archive contains no newly collected human-subject data and no site wind-measurement campaign. AUTHOR_INPUT_NEEDED: funding, competing interests, acknowledgements and CRediT author-contribution statements must be completed by the authors.
"""
    write_text(PAPER / "experiment3_submission_statements_en.md", en)

    zh = """# 实验3投稿声明文本

evidence_type: newly_run + preexisting_artifact + blocked

## 数据可用性

实验3的轻量化归档包包含已处理报告、清单、部分 CFD-ready 几何、后处理统计表、论文图件、ParaView 状态文件和论文文本。完整 TUM2TWIN 原始下载、完整贴图目录、本地 ParaView 安装文件、本地 FluidX3D 源码/构建目录和完整 VTK 输出矩阵未嵌入 GitHub 包，原因是文件体量和机器环境依赖；其来源和边界记录在 `EXTERNAL_ARTIFACTS.md` 与 `manifests/data_manifest.csv`。正式投稿前，许可表述应再次对照 TUM2TWIN 与 Zenodo 原始记录核验。

## 代码可用性

归档包包含用于生成论文结果的后处理、形态分析、图件生成、声明审计和 manifest 刷新脚本。实验3 release package 根目录下的规范重建命令为 `& .\\scripts\\rebuild_experiment3_paper_assets.ps1`。包内同时保留 FluidX3D case 模板和 CityLBM-compatible 几何模板，但 CityLBM-Grasshopper 文件夹属于互操作模板，不应写成已经完成端到端插件运行的证据。

## 可复现性

当前归档足以审计数据层分离、CFD-ready 几何准备、已处理 FluidX3D 筛查指标、ParaView/人工审图资产、形态响应分析、图表叙事链和声明边界。完整重跑 CFD 需要恢复或重新下载外部 TUM2TWIN 资产、构建或恢复 FluidX3D，并重新生成完整 VTK 输出。本文不宣称现场验证、正式年度舒适/安全合规、污染物扩散、GCBTE 闭环或成功设计优化。

## 计算资源与数值协议

数值协议记录在 `manifests/fluidx3d_numerical_protocol_audit.csv` 与 `reports/fluidx3d_numerical_protocol_and_stability_audit.md`，包括 dx、网格/计算域、参考风速、空气黏性、LBM 转换、tau/Re 描述、风向和采样步。GPU 型号、墙钟运行时间、残差收敛和完整网格无关性证据不得臆造，只有在后续实际测量后才能写入论文。

## 伦理、资金和利益冲突

当前归档不包含新采集的人类受试者数据，也不包含现场风速实测活动。AUTHOR_INPUT_NEEDED：资金来源、利益冲突、致谢和 CRediT 作者贡献声明需要由作者补充。
"""
    write_text(PAPER / "experiment3_submission_statements_zh.md", zh)


def main() -> None:
    key_matrix = read_csv(FIG / "final_integrated_key_result_matrix.csv")
    evidence_rows = read_csv(MAN / "evidence_inventory.csv")
    protocol_rows = read_csv(MAN / "fluidx3d_numerical_protocol_audit.csv")
    rows = build_statement_rows(key_matrix, evidence_rows, protocol_rows)

    write_reports(rows)
    update_key_matrix(rows)
    update_evidence_inventory()
    update_claim_verification()

    print("submission_statement_units", len(rows))
    print("wrote manifests/experiment3_submission_statement_evidence_map.csv")
    print("wrote reports/experiment3_submission_statement_package.md")
    print("wrote paper_text/experiment3_submission_statements_en.md")
    print("wrote paper_text/experiment3_submission_statements_zh.md")


if __name__ == "__main__":
    main()
