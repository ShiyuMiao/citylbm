#!/usr/bin/env python3
"""Generate paper-facing reproducibility appendices for AIJ Case E."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PAPER_DIR = ROOT / "academic-paper-writer" / "paper-drafts"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "NA"
    return f"{float(value):.{digits}f}"


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def command_lines(suite: Dict[str, Any]) -> List[str]:
    display_commands = {
        "citylbm_release_build": r"E:\citylbm_buildchain\dotnet\dotnet.exe build CityLBM/CityLBM.csproj -c Release",
        "casee_audit": "python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe",
        "manuscript_evidence_summary": "python docs/experiments/casee/tools/manuscript_evidence_summary.py",
        "plugin_identity_gate": "python docs/experiments/casee/tools/plugin_identity_gate.py",
        "rhino_gha_load_gate": "python docs/experiments/casee/tools/rhino_gha_load_gate.py",
        "casee_official_run_preflight": "python docs/experiments/casee/tools/casee_official_run_preflight.py",
        "casee_environment_recovery_runbook": "python docs/experiments/casee/tools/casee_environment_recovery_runbook.py",
        "casee_failure_mode_atlas": "python docs/experiments/casee/tools/casee_failure_mode_atlas.py",
        "casee_default_policy_gate": "python docs/experiments/casee/tools/casee_default_policy_gate.py",
        "citylbm_paper_results_packet": "python docs/experiments/casee/tools/citylbm_paper_results_packet.py",
        "citylbm_manifest_output_gate": "python docs/experiments/casee/tools/citylbm_manifest_output_gate.py",
        "casee_manuscript_results_table": "python docs/experiments/casee/tools/casee_manuscript_results_table.py",
        "casee_paper_results_figure": "python docs/experiments/casee/tools/casee_paper_results_figure.py",
        "citylbm_software_feedback_matrix": "python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py",
        "artifact_index_pre_appendix": "python docs/experiments/casee/tools/artifact_index.py",
        "paper_appendix_generator": "python docs/experiments/casee/tools/paper_appendix_generator.py",
        "artifact_index": "python docs/experiments/casee/tools/artifact_index.py",
        "paper_evidence_gate": "python docs/experiments/casee/tools/paper_evidence_gate.py",
        "formal_release_gate_expected_block": "python docs/experiments/casee/tools/release_gate.py",
    }
    lines: List[str] = []
    for step in suite.get("steps", []):
        name = str(step.get("name", ""))
        command = display_commands.get(name, step.get("command"))
        if not command:
            continue
        status = "passed" if step.get("passed") else "failed"
        lines.append(f"- `{name}` ({status}, returncode={step.get('returncode')}): `{command}`")
    return lines


def artifact_rows(artifact_index: Dict[str, Any], limit: int = 18) -> List[Dict[str, Any]]:
    rows = artifact_index.get("artifacts", [])
    priority = {
        "CityLBM/bin/CityLBM.gha",
        "docs/experiments/casee/results/release_gate.json",
        "docs/experiments/casee/results/casee_metrics.csv",
        "docs/experiments/casee/results/casee_validation_report.md",
        "docs/experiments/casee/results/casee_manuscript_claim_matrix.csv",
        "docs/experiments/casee/results/casee_paper_evidence_gate.json",
        "docs/experiments/casee/results/casee_reproducibility_suite.json",
        "docs/experiments/casee/results/plugin_identity_gate.json",
        "docs/experiments/casee/results/rhino_gha_load_gate.json",
        "docs/experiments/casee/results/casee_official_run_preflight.json",
        "docs/experiments/casee/results/casee_environment_recovery_runbook.json",
        "docs/experiments/casee/results/casee_failure_mode_atlas.json",
        "docs/experiments/casee/results/casee_default_policy_gate.json",
        "docs/experiments/casee/results/casee_manuscript_results_table.json",
        "docs/experiments/casee/results/citylbm_paper_results_packet.json",
        "docs/experiments/casee/results/citylbm_manifest_output_gate.json",
        "docs/experiments/casee/results/citylbm_software_feedback_matrix.json",
        "docs/experiments/casee/results/casee_paper_results_figure.svg",
        "docs/experiments/casee/results/casee_paper_results_figure_source.csv",
        "docs/experiments/casee/results/casee_paper_results_figure_qa.json",
        "docs/experiments/casee/results/casee_artifact_index.json",
        "docs/experiments/casee/results/build_chain_manifest.json",
        "docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv",
        "docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv",
    }
    picked = [row for row in rows if row.get("path") in priority]
    if len(picked) < limit:
        picked.extend(row for row in rows if row not in picked and row.get("release_asset_role") == "lightweight_release_asset")
    return picked[:limit]


def claim_counts(claim_rows: Iterable[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in claim_rows:
        readiness = row.get("claim_readiness", "unknown")
        counts[readiness] = counts.get(readiness, 0) + 1
    return counts


def en_appendix(
    *,
    generated_at: str,
    gate: Dict[str, Any],
    suite: Dict[str, Any],
    artifact_index: Dict[str, Any],
    paper_gate: Dict[str, Any],
    plugin_gate: Dict[str, Any],
    claim_rows: List[Dict[str, str]],
) -> str:
    metrics = gate.get("metrics", {})
    checks = gate.get("checks", {})
    artifact_summary = artifact_index.get("summary", {})
    counts = claim_counts(claim_rows)
    commands = command_lines(suite)
    artifacts = artifact_rows(artifact_index)

    lines = [
        "# AIJ Case E Reproducibility Appendix",
        "",
        f"Generated: {generated_at}",
        "",
        "## Section Contract",
        "",
        "Reader state before: the reader has seen the CityLBM workflow and needs enough detail to audit the Case E validation protocol.",
        "Reader state after: the reader can identify the exact official protocol, the available evidence chain, the release boundary, and the remaining blockers.",
        "Required moves: protocol definition, command provenance, artifact provenance, metric scope, software identity, and limitations boundary.",
        "Evidence hooks: release gate JSON, reproducibility suite JSON, artifact index, claim matrix, plugin identity gate, and official Case E metric CSV.",
        "",
        "## Protocol Scope",
        "",
        "- Benchmark: AIJ Case E.",
        "- Condition: `ac`.",
        "- Wind direction: `N`; wind vector convention recorded as `(0, -1, 0)` in the Case E protocol.",
        "- Geometry: official `BD_caseE.stl`, scale factor 250.",
        "- Reference speed and height: Uref = 3.928296 m/s, zref = 15.9 m.",
        "- Formal validation height: official z = 2 m.",
        "- Formal probe set: 80 probes filtered from `RS_caseE.csv` by `case=ac` and `Wind_direction=N`.",
        "- Formal sampling mode: `raw_trilinear` only.",
        "",
        "## Current Official Metric",
        "",
        f"The current official z = 2 m Case E result is MAE = {fmt(metrics.get('mae_pp'))} percentage points, "
        f"RMSE = {fmt(metrics.get('rmse_pp'))} percentage points, bias = {fmt(metrics.get('bias_pp'))} percentage points, "
        f"R2 = {fmt(metrics.get('r2'), 6)}, and Pearson = {fmt(metrics.get('pearson'), 6)} "
        "(newly_run; source: `docs/experiments/casee/results/release_gate.json`). "
        "Because the formal R2 remains negative and the release gate is closed, this is a negative-validation result, not an accuracy-success result.",
        "",
        "## Reproducibility Chain",
        "",
        f"- Suite passed: {suite.get('suite_passed')}.",
        f"- Paper evidence gate passed: {paper_gate.get('paper_evidence_gate_passed')}.",
        f"- Plugin identity gate passed: {plugin_gate.get('plugin_identity_gate_passed')}.",
        f"- Formal v0.4.0 release allowed: {gate.get('formal_release_allowed')}.",
        f"- Recommended tag: `{gate.get('recommended_tag')}`.",
        f"- CityLBM build passed: {checks.get('citylbm_build_passed')}.",
        f"- Case A smoke regression passed: {checks.get('casea_smoke_regression_passed')}.",
        f"- Rhino loaded new GHA: {checks.get('rhino_loaded_new_gha')}.",
        f"- Official z = 2 m metric gate passed: {checks.get('official_z2m_metric_gate')}.",
        "",
        "## Commands Used For Traceability",
        "",
    ]
    lines.extend(commands or ["- No command trace was available in the suite JSON."])
    lines += [
        "",
        "## Key Artifacts",
        "",
        "| artifact | role | readiness | sha256 |",
        "|---|---|---|---|",
    ]
    for row in artifacts:
        lines.append(
            f"| `{row.get('path')}` | {row.get('release_asset_role')} | {row.get('claim_readiness')} | `{row.get('sha256')}` |"
        )
    lines += [
        "",
        "## Claim Readiness Summary",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines += [
        "",
        "## Manuscript-Allowed Claims",
        "",
        "- The Case E official protocol and 80-probe filtering are reproducible from the archived inputs.",
        "- The current CityLBM release-candidate build and tracked GHA are identifiable by hash.",
        "- The official z = 2 m result is a transparent negative validation result.",
        "- Near-wall, solid-corner, voxelization, and probe-sampling effects are supported as limitations diagnostics.",
        "",
        "## Forbidden Claims",
        "",
        "- CityLBM v0.4.0 has validated predictive accuracy for AIJ Case E.",
        "- A diagnostic z-offset, `z_plus_half`, or `vertical_valid_above` result is the formal official z = 2 m result.",
        "- The current evidence proves mesh independence or LES improvement.",
        "- The current evidence proves that Rhino/Grasshopper has loaded the newly built GHA.",
        "",
        "## Remaining Blockers",
        "",
        "- Improve the official z = 2 m `raw_trilinear` metric until MAE is clearly below the previous near-20 pp level and R2/Pearson are positive.",
        "- Independently verify that Rhino/Grasshopper loads the new GHA instead of an old plugin copy.",
        "- Recover the GPU runtime before additional long native FluidX3D runs; the latest `nvidia-smi` evidence reports a lost GPU.",
        "- Complete the Visual Studio Build Tools 2022 C++ installation or continue with documented fallback build paths.",
        "",
    ]
    return "\n".join(lines)


def zh_appendix(
    *,
    generated_at: str,
    gate: Dict[str, Any],
    suite: Dict[str, Any],
    artifact_index: Dict[str, Any],
    paper_gate: Dict[str, Any],
    plugin_gate: Dict[str, Any],
    claim_rows: List[Dict[str, str]],
) -> str:
    metrics = gate.get("metrics", {})
    checks = gate.get("checks", {})
    artifact_summary = artifact_index.get("summary", {})
    counts = claim_counts(claim_rows)
    commands = command_lines(suite)
    artifacts = artifact_rows(artifact_index)

    lines = [
        "# AIJ Case E 可复现性附录",
        "",
        f"生成时间: {generated_at}",
        "",
        "## 章节契约",
        "",
        "读者进入本附录前应已了解 CityLBM 的总体工作流；读完后应能够审计 Case E 的官方协议、命令来源、产物哈希、版本边界和剩余阻塞项。",
        "本附录只使用已有门控与产物索引，不引入新的 CFD 精度结论。",
        "",
        "## 协议范围",
        "",
        "- 基准案例: AIJ Case E。",
        "- 工况: `ac`。",
        "- 风向: `N`；风向量约定在协议中记录为 `(0, -1, 0)`。",
        "- 几何: 官方 `BD_caseE.stl`，比例因子 250。",
        "- 参考风速和高度: Uref = 3.928296 m/s，zref = 15.9 m。",
        "- 正式验证高度: 官方 z = 2 m。",
        "- 正式测点: `RS_caseE.csv` 中 `case=ac` 且 `Wind_direction=N` 的 80 个测点。",
        "- 正式采样: 仅 `raw_trilinear`。",
        "",
        "## 当前官方指标",
        "",
        f"当前 official z = 2 m Case E 结果为 MAE = {fmt(metrics.get('mae_pp'))} 个百分点，"
        f"RMSE = {fmt(metrics.get('rmse_pp'))} 个百分点，bias = {fmt(metrics.get('bias_pp'))} 个百分点，"
        f"R2 = {fmt(metrics.get('r2'), 6)}，Pearson = {fmt(metrics.get('pearson'), 6)} "
        "（newly_run；来源: `docs/experiments/casee/results/release_gate.json`）。"
        "由于正式 R2 仍为负且 release gate 关闭，该结果只能写成负向验证或局限性结果，不能写成精度验证成功。",
        "",
        "## 可复现链",
        "",
        f"- 一键复现套件通过: {suite.get('suite_passed')}。",
        f"- 论文证据门控通过: {paper_gate.get('paper_evidence_gate_passed')}。",
        f"- 插件身份门控通过: {plugin_gate.get('plugin_identity_gate_passed')}。",
        f"- 正式 v0.4.0 是否允许发布: {gate.get('formal_release_allowed')}。",
        f"- 推荐标签: `{gate.get('recommended_tag')}`。",
        f"- CityLBM 构建通过: {checks.get('citylbm_build_passed')}。",
        f"- Case A smoke regression 通过: {checks.get('casea_smoke_regression_passed')}。",
        f"- Rhino 是否已加载新 GHA: {checks.get('rhino_loaded_new_gha')}。",
        f"- official z = 2 m 指标门槛是否通过: {checks.get('official_z2m_metric_gate')}。",
        "",
        "## 可追溯命令",
        "",
    ]
    lines.extend(commands or ["- suite JSON 中没有可用命令记录。"])
    lines += [
        "",
        "## 关键产物",
        "",
        "| artifact | role | readiness | sha256 |",
        "|---|---|---|---|",
    ]
    for row in artifacts:
        lines.append(
            f"| `{row.get('path')}` | {row.get('release_asset_role')} | {row.get('claim_readiness')} | `{row.get('sha256')}` |"
        )
    lines += [
        "",
        "## 论文章节可用性",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines += [
        "",
        "## 允许写入论文的表述",
        "",
        "- Case E 官方协议和 80 测点过滤过程可由归档输入复现。",
        "- 当前 CityLBM release-candidate 构建和跟踪版 GHA 可由哈希识别。",
        "- official z = 2 m 结果是透明的负向验证结果。",
        "- near-wall、solid-corner、voxelization 和 probe-sampling 影响可作为局限性诊断讨论。",
        "",
        "## 禁止写入论文的表述",
        "",
        "- CityLBM v0.4.0 已完成 AIJ Case E 预测精度验证。",
        "- 诊断性 z-offset、`z_plus_half` 或 `vertical_valid_above` 是正式 official z = 2 m 结果。",
        "- 当前证据证明网格无关性或 LES 改善。",
        "- 当前证据证明 Rhino/Grasshopper 已加载新构建的 GHA。",
        "",
        "## 剩余阻塞",
        "",
        "- official z = 2 m `raw_trilinear` 指标仍需进一步改善，至少要使 MAE 明显低于既有接近 20 pp 的水平，并使 R2 和 Pearson 为正。",
        "- 需要独立验证 Rhino/Grasshopper 加载的是新 GHA，而不是旧插件副本。",
        "- 继续长时间 native FluidX3D 前需要恢复 GPU runtime；最新 `nvidia-smi` 证据显示 GPU lost。",
        "- 需要完成 Visual Studio Build Tools 2022 C++ 安装，或继续记录可复现的 fallback 构建路径。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--suite", type=Path, default=RESULTS_DIR / "casee_reproducibility_suite.json")
    parser.add_argument("--artifact-index", type=Path, default=RESULTS_DIR / "casee_artifact_index.json")
    parser.add_argument("--paper-gate", type=Path, default=RESULTS_DIR / "casee_paper_evidence_gate.json")
    parser.add_argument("--plugin-gate", type=Path, default=RESULTS_DIR / "plugin_identity_gate.json")
    parser.add_argument("--claim-matrix", type=Path, default=RESULTS_DIR / "casee_manuscript_claim_matrix.csv")
    parser.add_argument("--out-en", type=Path, default=PAPER_DIR / "casee_v04_reproducibility_appendix_en.md")
    parser.add_argument("--out-zh", type=Path, default=PAPER_DIR / "casee_v04_reproducibility_appendix_zh.md")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_paper_appendix_manifest.json")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    gate = read_json(args.release_gate)
    suite = read_json(args.suite)
    artifact_index = read_json(args.artifact_index)
    paper_gate = read_json(args.paper_gate)
    plugin_gate = read_json(args.plugin_gate)
    claim_rows = read_csv(args.claim_matrix)

    args.out_en.parent.mkdir(parents=True, exist_ok=True)
    args.out_zh.parent.mkdir(parents=True, exist_ok=True)
    args.out_en.write_text(
        en_appendix(
            generated_at=generated_at,
            gate=gate,
            suite=suite,
            artifact_index=artifact_index,
            paper_gate=paper_gate,
            plugin_gate=plugin_gate,
            claim_rows=claim_rows,
        )
        + "\n",
        encoding="utf-8",
    )
    args.out_zh.write_text(
        zh_appendix(
            generated_at=generated_at,
            gate=gate,
            suite=suite,
            artifact_index=artifact_index,
            paper_gate=paper_gate,
            plugin_gate=plugin_gate,
            claim_rows=claim_rows,
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "generated_at": generated_at,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_reproducibility_appendix; blocked formal accuracy release",
        "outputs": {
            "en": display_path(args.out_en),
            "zh": display_path(args.out_zh),
        },
        "source_artifacts": [
            display_path(args.release_gate),
            display_path(args.suite),
            display_path(args.artifact_index),
            display_path(args.paper_gate),
            display_path(args.plugin_gate),
            display_path(args.claim_matrix),
        ],
        "formal_release_allowed": gate.get("formal_release_allowed"),
        "recommended_tag": gate.get("recommended_tag"),
        "official_z2m_metrics": gate.get("metrics", {}),
        "boundary": "Appendix supports reproducibility and claim control only; it does not support formal accuracy success.",
    }
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out_en": display_path(args.out_en), "out_zh": display_path(args.out_zh)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
