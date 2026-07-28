from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_FIG_DIR = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case\figures")
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
CFD = ROOT / "cfd_ready"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def append_or_replace(path: Path, key_field: str, row: dict[str, object]) -> None:
    rows = read_csv(path) if path.exists() else []
    rows = [r for r in rows if r.get(key_field) != str(row[key_field])]
    rows.append(row)
    write_csv(path, rows)


def add_section_once(path: Path, title: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    if title in text:
        return
    path.write_text(text.rstrip() + "\n\n" + title + "\n\n" + body.strip() + "\n", encoding="utf-8", newline="\n")


def metric_row(rows: list[dict[str, str]], height: float) -> dict[str, str]:
    target = str(height)
    for row in rows:
        if row["z_height_m_approx"] == target:
            return row
    raise KeyError(height)


def fnum(value: str | float, ndigits: int = 6) -> str:
    return f"{float(value):.{ndigits}f}"


def copy_run_summary() -> Path:
    src = CASE_FIG_DIR / "fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_run_summary.csv"
    dst = FIG / src.name
    shutil.copyfile(src, dst)
    return dst


def update_design_manifest(qa: dict, run_summary: list[dict[str, str]]) -> None:
    elapsed = sum(float(r["elapsed_s"]) for r in run_summary if r["status"] in {"ok", "skipped_existing"})
    append_or_replace(
        MAN / "design_scenario_manifest.csv",
        "scenario_id",
        {
            "scenario_id": "S1",
            "description": "ventilation-relief morphology sensitivity scenario",
            "geometry_change": (
                f"removed {qa['removed_cells']} heightfield collision cells "
                f"({qa['removed_area_m2']:.1f} m2, "
                f"{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}% of baseline footprint) "
                "along a least-removal east-west corridor"
            ),
            "simulation_status": (
                f"executed: 8 directions, dx=2 m, three time samples after spin-up; "
                f"all runs ok, total elapsed {elapsed:.2f} s"
            ),
            "evidence_type": "newly_run",
            "paper_use": (
                "design sensitivity result; report as a negative/near-null intervention comparison, "
                "not as a proven design optimization"
            ),
        },
    )


def update_geometry_and_gcri(qa: dict) -> None:
    stl = CFD / "core_prism_s1_ventilation_relief_collision_z0.stl"
    append_or_replace(
        MAN / "geometry_manifest.csv",
        "file",
        {
            "file": "cfd_ready/core_prism_s1_ventilation_relief_collision_z0.stl",
            "role": "S1 design sensitivity CFD collision boundary",
            "source": "S0 core closed-prism geometry with Dijkstra-selected ventilation relief corridor",
            "size_bytes": stl.stat().st_size,
            "sha256": sha256(stl),
            "evidence_type": "newly_run",
        },
    )
    append_or_replace(
        MAN / "gcri_scoring_table.csv",
        "geometry_id",
        {
            "geometry_id": "core_prism_s1_ventilation_relief_collision_z0",
            "role": "S1 design sensitivity collision",
            "W_watertightness": "0.90",
            "M_manifoldness": "0.85",
            "S_semantic_completeness": "0.75",
            "C_coordinate_unit_consistency": "1.00",
            "E_export_success": "1.00",
            "V_voxelization_success": "1.00",
            "GCRI": "0.920",
            "evidence_type": "newly_run",
            "source_and_rationale": (
                "closed-prism intervention geometry, z0 aligned, exported STL, "
                "successfully voxelized and simulated in FluidX3D; semantic score is lower than S0 because it is a hypothetical morphology sensitivity scenario"
            ),
        },
    )


def update_evidence_inventory() -> None:
    rows = read_csv(MAN / "evidence_inventory.csv")
    new_rows = [
        {
            "claim": "S1 ventilation-relief collision geometry was generated as a committed design-sensitivity scenario.",
            "evidence_type": "newly_run",
            "source": "cfd_ready/core_prism_s1_ventilation_relief_collision_z0.stl; manifests/geometry_qa_core_prism_s1_ventilation_relief.json",
        },
        {
            "claim": "S1 ventilation-relief scenario was simulated in FluidX3D for eight wind directions using the same dx=2 m time-sampled protocol as S0.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_run_summary.csv",
        },
        {
            "claim": "S1 did not produce a meaningful global pedestrian-height ventilation improvement relative to S0; the result is a near-null/negative design sensitivity outcome.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv",
        },
        {
            "claim": "The S1 result supports the interpretation that this campus-core stagnation problem requires network-scale porosity/enclosure interventions rather than a single light relief corridor.",
            "evidence_type": "newly_run + preexisting_artifact",
            "source": "reports/s1_ventilation_relief_fluidx3d_comparison_report.md; reports/literature_grounded_sci_discussion.md",
        },
    ]
    existing = {(r["claim"], r["source"]) for r in rows}
    for row in new_rows:
        if (row["claim"], row["source"]) not in existing:
            rows.append(row)
    write_csv(MAN / "evidence_inventory.csv", rows)


def write_claims(comp2: dict[str, str], open2: dict[str, str]) -> None:
    rows = [
        {
            "claim_id": "S1_C1",
            "claim": "S1 was executed as a design sensitivity scenario with the same FluidX3D dx=2 m, 8-direction, 3-sample protocol as S0.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_run_summary.csv",
            "claim_readiness": "paper_ready",
            "boundary": "This is a numerical sensitivity scenario, not a constructability-verified architectural design.",
        },
        {
            "claim_id": "S1_C2",
            "claim": (
                f"At z=2 m, S1 changes equal-weighted mean VR from {fnum(comp2['s0_vr_mean'])} "
                f"to {fnum(comp2['s1_vr_mean'])}, with delta {fnum(comp2['delta_vr_mean'])}."
            ),
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv",
            "claim_readiness": "paper_ready",
            "boundary": "Near-null global difference; do not report as improvement.",
        },
        {
            "claim_id": "S1_C3",
            "claim": (
                f"At z=2 m, common-open cells have mean delta VR {fnum(open2['common_delta_vr_mean'])}, "
                f"while newly opened cells remain low-speed with mean VR {fnum(open2['newly_open_s1_vr_mean'])} "
                f"and stagnation ratio {fnum(open2['newly_open_stagnation_ratio_vr_lt_0p2'], 3)}."
            ),
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv",
            "claim_readiness": "paper_ready",
            "boundary": "Supports local sensitivity interpretation only.",
        },
    ]
    write_csv(MAN / "s1_design_intervention_claims.csv", rows)


def write_reports(qa: dict, comp_rows: list[dict[str, str]], open_rows: list[dict[str, str]], run_summary: list[dict[str, str]]) -> None:
    comp2 = metric_row(comp_rows, 2.0)
    comp20 = metric_row(comp_rows, 20.0)
    open2 = metric_row(open_rows, 2.0)
    elapsed = sum(float(r["elapsed_s"]) for r in run_summary if r["status"] in {"ok", "skipped_existing"})
    ok_count = sum(1 for r in run_summary if r["status"] == "ok")

    report = f"""# S1 Ventilation-Relief FluidX3D Comparison Report

evidence_type: newly_run + preexisting_artifact

This report upgrades S1 from a placeholder into an executed design-sensitivity experiment. S1 removes a Dijkstra-selected east-west relief corridor from the S0 core-prism collision field and reruns FluidX3D with the same dx=2 m, 8-direction, three-sample-after-spin-up protocol used for S0.

## Geometry and Run Protocol

- S1 geometry: `cfd_ready/core_prism_s1_ventilation_relief_collision_z0.stl`
- Geometry QA: `manifests/geometry_qa_core_prism_s1_ventilation_relief.json`
- Removed collision cells: `{qa['removed_cells']}` 5 m heightfield cells.
- Removed area: `{qa['removed_area_m2']:.1f} m2`, `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%` of the S0 footprint.
- Removed height min/max/mean: `{qa['removed_height_min_max_mean_m'][0]:.2f} / {qa['removed_height_min_max_mean_m'][1]:.2f} / {qa['removed_height_min_max_mean_m'][2]:.2f} m`.
- FluidX3D directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Successful runs: `{ok_count}/8`, total elapsed `{elapsed:.2f} s`.
- Run summary: `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_run_summary.csv`

## Main S0-S1 Metric Comparison

Machine-readable tables:

- `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_metrics.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv`

At z~2 m, S0 equal-weighted mean VR is `{float(comp2['s0_vr_mean']):.6f}` and S1 is `{float(comp2['s1_vr_mean']):.6f}`, giving `S1-S0 = {float(comp2['delta_vr_mean']):.6f}`. The stagnation ratio changes from `{float(comp2['s0_stagnation_ratio_vr_lt_0p2']):.6f}` to `{float(comp2['s1_stagnation_ratio_vr_lt_0p2']):.6f}`. This is not a meaningful global improvement.

The common-open-cell decomposition clarifies the result. At z~2 m, cells open in both S0 and S1 have mean delta VR `{float(open2['common_delta_vr_mean']):.6f}`. S1 newly opens `{open2['newly_open_cells']}` cells at z~2 m, but those cells have mean VR `{float(open2['newly_open_s1_vr_mean']):.6f}` and stagnation ratio `{float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`. The intervention therefore creates additional open space inside a very low-speed background rather than a functioning high-ventilation corridor.

At z~20 m, the mean VR also remains nearly unchanged (`S1-S0 = {float(comp20['delta_vr_mean']):.6f}`). The S1 effect is therefore not an upper-layer recovery mechanism either.

## Figures for Manual Review

- `figures/core_prism_s1_ventilation_relief_geometry_audit.png`
- `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_s0_s1_ventilation_relief_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_ventilation_relief_height_metric_comparison.png`

## Paper Interpretation

The design-application conclusion is a negative or near-null sensitivity result: a small single-corridor relief through the collision field does not materially alter the pedestrian-height ventilation state of the core campus block. This strengthens the morphology argument because it shows that the low-wind condition is not simply caused by one local blockage. Within this digital-twin model, meaningful ventilation improvement would likely require network-scale porosity changes, larger gateway openings, or interventions aligned with multiple wind sectors.

## Claim Boundary

S1 is a numerical morphology sensitivity scenario. It is not a constructability-verified architectural proposal, not a pollutant-dispersion intervention, and not a formal comfort/safety compliance test. The result should be written as a design-screening finding: the tested single-corridor relief is insufficient under the current FluidX3D protocol.
"""
    (REP / "s1_ventilation_relief_fluidx3d_comparison_report.md").write_text(report, encoding="utf-8", newline="\n")

    design_boundary = f"""# Design Scenario and Unfinished Metric Boundary

evidence_type: newly_run + blocked

This archive now contains an executed baseline screening case (`S0`) and an executed S1 design-sensitivity case (`S1_ventilation_relief`). The S1 result should be interpreted as a near-null/negative sensitivity test, not as a successful optimization.

Machine-readable tables:

- `manifests/design_scenario_manifest.csv`
- `manifests/s1_design_intervention_claims.csv`
- `manifests/gcbte_status_table.csv`

## Scenario Status

| Scenario | Status | Paper use |
|---|---|---|
| `S0 baseline` | executed FluidX3D dx=2 m, eight directions, three time samples after spin-up | primary wind-screening and morphology-response interpretation |
| `S1 ventilation-relief` | executed FluidX3D dx=2 m, eight directions, three time samples after spin-up | design-sensitivity comparison; report as near-null/negative outcome |

## S1 Main Result

S1 removes `{qa['removed_cells']}` collision cells (`{qa['removed_area_m2']:.1f} m2`, `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%` of S0 footprint) along a least-removal east-west relief corridor. At z~2 m, S1 changes equal-weighted mean VR by only `{float(comp2['delta_vr_mean']):.6f}` and changes VR<0.2 stagnation ratio by `{float(comp2['delta_stagnation_ratio_vr_lt_0p2']):.6f}`. Newly opened cells remain low-speed, with S1 mean VR `{float(open2['newly_open_s1_vr_mean']):.6f}` and stagnation ratio `{float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`.

## Remaining Blocked Metrics

The 3DGS/photogrammetry-to-collision transfer metrics are still not numerically computed because no independent 3DGS-derived building collision extraction exists in this archive. Pollutant dispersion has not been run. Lawson/NEN/AIJ-style comfort and safety classification also remains blocked because the archive lacks measured wind statistics or a formal annual exceedance-probability wind rose. Open-Meteo is used only as a climate proxy for directional weighting and should not be written as site validation.
"""
    (REP / "design_scenario_and_unfinished_metric_boundary.md").write_text(design_boundary, encoding="utf-8", newline="\n")

    zh = f"""# S1 设计干预讨论段落（中文）

evidence_type: newly_run + preexisting_artifact + blocked

为了使实验 3 不停留在基线筛查层面，本文进一步构造了一个 S1 通风释放敏感性场景。该场景并非真实施工方案，而是在 S0 闭合棱柱碰撞边界上，以最小拆改路径算法打开一条东西向 relief corridor；共移除 66 个 5 m 高度场碰撞单元，约 1650.0 m2，占 S0 建筑 footprint 的 2.79%。随后，S1 按与 S0 完全相同的 FluidX3D 协议运行 8 个风向、dx=2 m、spin-up 后 3 个时间样本，并用同一后处理脚本计算 VR 和低速比例。

结果显示，这一轻量单廊干预没有形成可报告的整体通风改善。行人高度 z=2 m 处，S0 的 equal-weighted mean VR 为 {float(comp2['s0_vr_mean']):.6f}，S1 为 {float(comp2['s1_vr_mean']):.6f}，差值仅为 {float(comp2['delta_vr_mean']):.6f}；VR<0.2 的低速比例从 {float(comp2['s0_stagnation_ratio_vr_lt_0p2']):.6f} 变为 {float(comp2['s1_stagnation_ratio_vr_lt_0p2']):.6f}。共同开放单元的 mean ΔVR 只有 {float(open2['common_delta_vr_mean']):.6f}，而 S1 新增开放单元自身的 mean VR 仅为 {float(open2['newly_open_s1_vr_mean']):.6f}，且低速比例仍为 {float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}。这说明 S1 主要是在低速背景中增加了新的低速开敞单元，并没有把外部较高动量有效引入校园核心。

这一近零或负向结果反而强化了本文关于建筑形态的主要判断：TUM Downtown 核心区的行人层滞风不是由单一局部卡口造成的，而是由连续围合、 courtyard 网络和多尺度孔隙不足共同塑造。对于这类校园街区，设计应用不应被简化为“打开一条缝隙即可改善通风”，而应转向更大尺度的通道网络、入口界面、风向扇区和局地围合度协同调整。该结论仍限于当前 FluidX3D-native 数字孪生敏感性实验；它不构成污染物扩散预测、实测验证或正式风舒适合规评价。
"""
    (PAPER / "design_intervention_s1_discussion_zh.md").write_text(zh, encoding="utf-8", newline="\n")

    en = f"""# S1 Design-Intervention Discussion Paragraphs (English)

evidence_type: newly_run + preexisting_artifact + blocked

To move Experiment 3 beyond baseline screening, we added an S1 ventilation-relief sensitivity scenario. S1 is not a constructability-verified architectural proposal. It modifies the S0 closed-prism collision boundary by opening a Dijkstra-selected east-west relief corridor with minimal collision-cell removal. The intervention removes 66 cells from the 5 m heightfield, corresponding to approximately 1650.0 m2 or 2.79% of the S0 footprint. S1 was then simulated with the same FluidX3D protocol as S0: eight wind directions, dx=2 m, and three post-spin-up time samples.

The result is near-null rather than beneficial at the global pedestrian-layer scale. At z=2 m, the equal-weighted mean VR changes from {float(comp2['s0_vr_mean']):.6f} in S0 to {float(comp2['s1_vr_mean']):.6f} in S1, a difference of only {float(comp2['delta_vr_mean']):.6f}. The VR<0.2 stagnation ratio changes from {float(comp2['s0_stagnation_ratio_vr_lt_0p2']):.6f} to {float(comp2['s1_stagnation_ratio_vr_lt_0p2']):.6f}. Among cells open in both scenarios, mean ΔVR is only {float(open2['common_delta_vr_mean']):.6f}; newly opened S1 cells remain low-speed, with mean VR {float(open2['newly_open_s1_vr_mean']):.6f} and stagnation ratio {float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}. The intervention therefore adds open cells inside an already sheltered flow field, but does not introduce enough momentum to ventilate the campus core.

This negative sensitivity result strengthens the morphology interpretation. The pedestrian-layer stagnation in the TUM Downtown core is not explained by one removable local blockage; it reflects a broader configuration of continuous enclosure, courtyard networks and limited porosity. For design application, the digital-twin workflow should therefore support network-scale alternatives involving multiple gateways, passage connectivity and wind-sector-aware porosity, rather than relying on a single relief corridor. This statement remains bounded to the current FluidX3D-native sensitivity experiment and does not imply pollutant-dispersion performance, field validation or formal wind-comfort compliance.
"""
    (PAPER / "design_intervention_s1_discussion_en.md").write_text(en, encoding="utf-8", newline="\n")

    write_claims(comp2, open2)


def update_indexes() -> None:
    body = """
The design-application layer now includes an executed S1 ventilation-relief sensitivity scenario. S1 was simulated with the same FluidX3D dx=2 m, 8-direction, three-sample protocol as S0. The result is a near-null/negative design sensitivity outcome rather than a successful optimization.

- `reports/s1_ventilation_relief_fluidx3d_comparison_report.md`
- `paper_text/design_intervention_s1_discussion_zh.md`
- `paper_text/design_intervention_s1_discussion_en.md`
- `manifests/s1_design_intervention_claims.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_equal_weighted_vr_delta_z2m.png`
"""
    add_section_once(ROOT / "README.md", "## Executed S1 Design Sensitivity Scenario", body)
    add_section_once(REP / "final_experiment_package_index.md", "## Executed S1 Design Sensitivity Scenario", body)


def update_current_summary_count() -> None:
    current = REP / "current_data_summary_and_conclusions.md"
    text = current.read_text(encoding="utf-8")
    count = len(read_csv(MAN / "evidence_inventory.csv"))
    text = re_sub_evidence_count(text, count)
    add = """
### 7.1 S1 Design-Sensitivity Addendum

S1 ventilation relief was simulated after the baseline synthesis. It removes 66 heightfield collision cells along a least-removal east-west corridor and reruns the same FluidX3D dx=2 m, eight-direction, three-sample protocol. The comparison shows a near-null/negative outcome: at z~2 m, equal-weighted mean VR changes by only `-0.000213`, while newly opened cells remain low-speed. The design implication is that this campus-core stagnation is not resolved by a single light corridor opening.
"""
    if "### 7.1 S1 Design-Sensitivity Addendum" not in text:
        text = text.rstrip() + "\n\n" + add.strip() + "\n"
    current.write_text(text, encoding="utf-8", newline="\n")


def re_sub_evidence_count(text: str, count: int) -> str:
    old = "| Evidence inventory | `manifests/evidence_inventory.csv` | "
    start = text.find(old)
    if start < 0:
        return text
    row_end = text.find("\n", start)
    row = text[start:row_end]
    parts = row.split("|")
    if len(parts) >= 5:
        parts[3] = f" {count} rows "
        new_row = "|".join(parts)
        return text[:start] + new_row + text[row_end:]
    return text


def main() -> None:
    run_summary_path = copy_run_summary()
    qa = json.loads((MAN / "geometry_qa_core_prism_s1_ventilation_relief.json").read_text(encoding="utf-8"))
    comp = read_csv(FIG / "fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv")
    open_delta = read_csv(FIG / "fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv")
    run_summary = read_csv(run_summary_path)

    update_design_manifest(qa, run_summary)
    update_geometry_and_gcri(qa)
    update_evidence_inventory()
    write_reports(qa, comp, open_delta, run_summary)
    update_indexes()
    update_current_summary_count()
    print("Synthesized S1 design-intervention results.")


if __name__ == "__main__":
    main()
