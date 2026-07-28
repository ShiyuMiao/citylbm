from __future__ import annotations

import csv
import hashlib
import json
import re
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


def replace_or_append_section(path: Path, title: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = rf"(?ms)^{re.escape(title)}\n\n.*?(?=^## |\Z)"
    replacement = title + "\n\n" + body.strip() + "\n\n"
    if re.search(pattern, text):
        text = re.sub(pattern, replacement, text).rstrip() + "\n"
    else:
        text = text.rstrip() + "\n\n" + replacement
    path.write_text(text, encoding="utf-8", newline="\n")


def metric_row(rows: list[dict[str, str]], height: float) -> dict[str, str]:
    for row in rows:
        if float(row["z_height_m_approx"]) == height:
            return row
    raise KeyError(height)


def fnum(value: str | float, ndigits: int = 6) -> str:
    return f"{float(value):.{ndigits}f}"


def copy_run_summary() -> Path:
    src = CASE_FIG_DIR / "fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_run_summary.csv"
    dst = FIG / src.name
    shutil.copyfile(src, dst)
    return dst


def update_manifests(qa: dict, run_summary: list[dict[str, str]], comp2: dict[str, str], open2: dict[str, str]) -> None:
    elapsed = sum(float(r["elapsed_s"]) for r in run_summary if r["status"] in {"ok", "skipped_existing"})
    append_or_replace(
        MAN / "design_scenario_manifest.csv",
        "scenario_id",
        {
            "scenario_id": "S2",
            "description": "network-porosity morphology sensitivity scenario",
            "geometry_change": (
                f"removed {qa['removed_cells']} heightfield collision cells "
                f"({qa['removed_area_m2']:.1f} m2, "
                f"{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}% of baseline footprint) "
                "along two east-west and one north-south least-removal corridors"
            ),
            "simulation_status": (
                f"executed: 8 directions, dx=2 m, three time samples after spin-up; "
                f"all runs ok, total elapsed {elapsed:.2f} s"
            ),
            "evidence_type": "newly_run",
            "paper_use": (
                "network-scale design sensitivity result; report as a second negative/near-null intervention comparison, "
                "showing that geometric porosity alone does not guarantee pedestrian-layer ventilation recovery"
            ),
        },
    )

    stl = CFD / "core_prism_s2_network_porosity_collision_z0.stl"
    append_or_replace(
        MAN / "geometry_manifest.csv",
        "file",
        {
            "file": "cfd_ready/core_prism_s2_network_porosity_collision_z0.stl",
            "role": "S2 network-scale design sensitivity CFD collision boundary",
            "source": "S0 core closed-prism geometry with three Dijkstra-selected network porosity corridors",
            "size_bytes": stl.stat().st_size,
            "sha256": sha256(stl),
            "evidence_type": "newly_run",
        },
    )
    append_or_replace(
        MAN / "gcri_scoring_table.csv",
        "geometry_id",
        {
            "geometry_id": "core_prism_s2_network_porosity_collision_z0",
            "role": "S2 network porosity collision",
            "W_watertightness": "0.90",
            "M_manifoldness": "0.85",
            "S_semantic_completeness": "0.70",
            "C_coordinate_unit_consistency": "1.00",
            "E_export_success": "1.00",
            "V_voxelization_success": "1.00",
            "GCRI": "0.908",
            "evidence_type": "newly_run",
            "source_and_rationale": (
                "closed-prism network intervention geometry, z0 aligned, exported STL, successfully voxelized and simulated in FluidX3D; "
                "semantic score is lower than S0/S1 because the multi-corridor geometry is a stronger hypothetical sensitivity case"
            ),
        },
    )

    evidence = read_csv(MAN / "evidence_inventory.csv")
    new_rows = [
        {
            "claim": "S2 network-porosity collision geometry was generated as a stronger multi-corridor design-sensitivity scenario.",
            "evidence_type": "newly_run",
            "source": "cfd_ready/core_prism_s2_network_porosity_collision_z0.stl; manifests/geometry_qa_core_prism_s2_network_porosity.json",
        },
        {
            "claim": "S2 network-porosity scenario was simulated in FluidX3D for eight wind directions using the same dx=2 m time-sampled protocol as S0 and S1.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_run_summary.csv",
        },
        {
            "claim": "S2 also does not produce a meaningful global pedestrian-height ventilation improvement relative to S0; geometric porosity alone is insufficient in this screened campus core.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_common_open_delta_summary.csv",
        },
    ]
    existing = {(r["claim"], r["source"]) for r in evidence}
    for row in new_rows:
        if (row["claim"], row["source"]) not in existing:
            evidence.append(row)
    write_csv(MAN / "evidence_inventory.csv", evidence)

    claims = [
        {
            "claim_id": "S2_C1",
            "claim": "S2 was executed as a network-scale porosity sensitivity scenario with the same FluidX3D dx=2 m, 8-direction, 3-sample protocol as S0 and S1.",
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_run_summary.csv",
            "claim_readiness": "paper_ready",
            "boundary": "Numerical morphology sensitivity case, not a constructability-verified architectural proposal.",
        },
        {
            "claim_id": "S2_C2",
            "claim": (
                f"At z=2 m, S2 changes equal-weighted mean VR from {fnum(comp2['reference_vr_mean'])} "
                f"to {fnum(comp2['target_vr_mean'])}, with delta {fnum(comp2['delta_vr_mean'])}."
            ),
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv",
            "claim_readiness": "paper_ready",
            "boundary": "Do not report as an improvement; this is a near-null/negative global response.",
        },
        {
            "claim_id": "S2_C3",
            "claim": (
                f"At z=2 m, S2 newly opened cells have mean VR {fnum(open2['newly_open_target_vr_mean'])} "
                f"and stagnation ratio {fnum(open2['newly_open_stagnation_ratio_vr_lt_0p2'], 3)}, while common-open cells show only mean delta VR {fnum(open2['common_delta_vr_mean'])}."
            ),
            "evidence_type": "newly_run",
            "source": "figures/fluidx3d_s0_s2_network_porosity_common_open_delta_summary.csv",
            "claim_readiness": "paper_ready",
            "boundary": "Supports a morphology-screening conclusion, not causal optimization proof.",
        },
    ]
    write_csv(MAN / "s2_design_intervention_claims.csv", claims)


def write_reports_and_paper(qa: dict, run_summary: list[dict[str, str]], comp_rows: list[dict[str, str]], open_rows: list[dict[str, str]]) -> None:
    comp2 = metric_row(comp_rows, 2.0)
    comp10 = metric_row(comp_rows, 10.0)
    comp20 = metric_row(comp_rows, 20.0)
    open2 = metric_row(open_rows, 2.0)
    open10 = metric_row(open_rows, 10.0)
    elapsed = sum(float(r["elapsed_s"]) for r in run_summary if r["status"] in {"ok", "skipped_existing"})
    ok_count = sum(1 for r in run_summary if r["status"] == "ok")

    report = f"""# S2 Network-Porosity FluidX3D Comparison Report

evidence_type: newly_run + preexisting_artifact

S2 is a stronger network-scale sensitivity experiment added after the near-null S1 result. It tests whether multiple connected porosity releases, rather than a single relief corridor, can alter the pedestrian-height wind response in the TUM Downtown campus core.

## Geometry and Run Protocol

- S2 geometry: `cfd_ready/core_prism_s2_network_porosity_collision_z0.stl`
- Geometry QA: `manifests/geometry_qa_core_prism_s2_network_porosity.json`
- Removed collision cells: `{qa['removed_cells']}` 5 m heightfield cells.
- Removed area: `{qa['removed_area_m2']:.1f} m2`, `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%` of the S0 footprint.
- Removed height min/max/mean: `{qa['removed_height_min_max_mean_m'][0]:.2f} / {qa['removed_height_min_max_mean_m'][1]:.2f} / {qa['removed_height_min_max_mean_m'][2]:.2f} m`.
- FluidX3D directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Successful runs: `{ok_count}/8`, total elapsed `{elapsed:.2f} s`.
- Run summary: `figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_run_summary.csv`

## Main S0-S2 Metric Comparison

At z~2 m, S0 equal-weighted mean VR is `{float(comp2['reference_vr_mean']):.6f}` and S2 is `{float(comp2['target_vr_mean']):.6f}`, giving `S2-S0 = {float(comp2['delta_vr_mean']):.6f}`. The VR<0.2 stagnation ratio changes from `{float(comp2['reference_stagnation_ratio_vr_lt_0p2']):.6f}` to `{float(comp2['target_stagnation_ratio_vr_lt_0p2']):.6f}`. This remains a near-null/negative global response.

The common-open-cell decomposition is more diagnostic. At z~2 m, cells open in both S0 and S2 have mean delta VR `{float(open2['common_delta_vr_mean']):.6f}`, but the `{open2['newly_open_cells']}` newly opened cells have mean VR only `{float(open2['newly_open_target_vr_mean']):.6f}` and stagnation ratio `{float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`. At z~10 m, the common-open mean delta rises to `{float(open10['common_delta_vr_mean']):.6f}`, but newly opened cells are still mostly stagnant with ratio `{float(open10['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`. At z~20 m, the global mean VR change is `{float(comp20['delta_vr_mean']):.6f}`.

## Paper Interpretation

S2 strengthens the design conclusion by converting the S1 observation into a two-level sensitivity result. S1 shows that a single light relief corridor is insufficient. S2 shows that a stronger multi-corridor porosity release still does not guarantee pedestrian-layer ventilation recovery when the released spaces are embedded in a deep sheltered campus-core flow field. The more defensible architectural conclusion is therefore not simply "increase porosity", but "increase wind-sector-coupled porosity at effective momentum-entry positions and reduce local enclosure where the external flow can actually enter".

## Figures for Manual Review

- `figures/core_prism_s2_network_porosity_geometry_audit.png`
- `figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_s0_s2_network_porosity_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_s2_design_sensitivity_height_metric_comparison.png`

## Claim Boundary

S2 is a numerical morphology sensitivity scenario. It is not a constructability-verified campus proposal, not a pollutant-dispersion intervention, not a formal comfort/safety compliance test, and not proof that all porosity changes fail. It shows only that the tested network-porosity release does not materially improve the equal-weighted FluidX3D pedestrian-layer screening metrics under the current dx=2 m, 8-direction protocol.
"""
    (REP / "s2_network_porosity_fluidx3d_comparison_report.md").write_text(report, encoding="utf-8", newline="\n")

    zh = f"""# S2 网络孔隙设计敏感性讨论段落

evidence_type: newly_run + preexisting_artifact + blocked

在 S1 单廊通风释放未能带来整体改善之后，本文进一步构造 S2 网络孔隙敏感性实验，以检验更强的多通道连通性干预是否能够改变校园核心区的行人层风环境。S2 并不是实际校园改造方案，而是在 S0 闭合棱柱碰撞边界上打开两条东西向和一条南北向最小拆改通道。该场景共移除 {qa['removed_cells']} 个 5 m 高度场碰撞单元，约 {qa['removed_area_m2']:.1f} m2，占 S0 footprint 的 {100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%；随后按与 S0/S1 完全相同的 FluidX3D dx=2 m、8 风向、spin-up 后 3 时间样本协议运行。

结果显示，S2 仍未形成全局意义上的行人层通风改善。z=2 m 处，S0 的 equal-weighted mean VR 为 {float(comp2['reference_vr_mean']):.6f}，S2 为 {float(comp2['target_vr_mean']):.6f}，差值为 {float(comp2['delta_vr_mean']):.6f}；VR<0.2 的低速比例从 {float(comp2['reference_stagnation_ratio_vr_lt_0p2']):.6f} 变为 {float(comp2['target_stagnation_ratio_vr_lt_0p2']):.6f}。共同开放单元的 mean ΔVR 为 {float(open2['common_delta_vr_mean']):.6f}，说明局部已有空间存在很弱的正向响应；但 S2 新增开放单元自身 mean VR 仅为 {float(open2['newly_open_target_vr_mean']):.6f}，且低速比例仍为 {float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}。因此，S2 的主要作用仍是在低动量背景中增加新的开敞单元，而不是形成能够贯通外部来流和校园核心的有效通风网络。

S1 与 S2 共同给出的新认知是：在 TUM Downtown 这类围合校园核心区，通风改善不能被简化为“增加几何孔隙率”。单条廊道不足以改变滞风状态，而更强的多通道孔隙释放也可能因为缺少有效动量入口和风向耦合而失效。建筑形态与风环境之间更可写入论文的关系是：行人层风环境受局地围合、通道连通性、开口位置和外部来流可进入性共同控制；其中，孔隙是否位于有效风向扇区和压力交换路径上，比单纯移除多少建筑 footprint 更关键。该结论仍限定于当前 FluidX3D-native 数字孪生敏感性实验，不构成实测验证、污染物扩散预测或正式风舒适合规评价。
"""
    (PAPER / "design_intervention_s2_discussion_zh.md").write_text(zh, encoding="utf-8", newline="\n")

    en = f"""# S2 Network-Porosity Design-Sensitivity Discussion Paragraphs

evidence_type: newly_run + preexisting_artifact + blocked

After the near-null S1 response, we added an S2 network-porosity sensitivity experiment to test whether a stronger multi-corridor connectivity intervention can alter the pedestrian-layer wind field in the campus core. S2 is not a constructability-verified proposal. It opens two east-west least-removal corridors and one north-south least-removal corridor in the S0 closed-prism collision boundary. The scenario removes {qa['removed_cells']} cells from the 5 m heightfield, corresponding to {qa['removed_area_m2']:.1f} m2 or {100.0*qa['removed_fraction_of_baseline_footprint']:.2f}% of the S0 footprint, and is simulated with the same FluidX3D dx=2 m, eight-direction, three-sample protocol as S0 and S1.

S2 still does not produce a global pedestrian-layer ventilation improvement. At z=2 m, equal-weighted mean VR changes from {float(comp2['reference_vr_mean']):.6f} in S0 to {float(comp2['target_vr_mean']):.6f} in S2, with ΔVR={float(comp2['delta_vr_mean']):.6f}; the VR<0.2 stagnation ratio changes from {float(comp2['reference_stagnation_ratio_vr_lt_0p2']):.6f} to {float(comp2['target_stagnation_ratio_vr_lt_0p2']):.6f}. Common-open cells have a weak positive mean ΔVR of {float(open2['common_delta_vr_mean']):.6f}, but newly opened S2 cells have mean VR only {float(open2['newly_open_target_vr_mean']):.6f} and stagnation ratio {float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}. The intervention therefore adds open cells within a low-momentum background rather than establishing an effective ventilation network between the external flow and the campus core.

Together, S1 and S2 refine the architectural interpretation. For the TUM Downtown campus core, ventilation improvement should not be reduced to increasing geometric porosity. A single corridor is insufficient, and even a stronger multi-corridor release can remain ineffective if it is not coupled to effective momentum-entry locations and wind-sector pressure exchange. The more defensible conclusion is that pedestrian-level wind conditions are jointly controlled by local enclosure, passage connectivity, opening position and the ability of external flow to enter the block. This statement remains bounded to the current FluidX3D-native digital-twin sensitivity experiments and does not imply field validation, pollutant-dispersion performance or formal comfort compliance.
"""
    (PAPER / "design_intervention_s2_discussion_en.md").write_text(en, encoding="utf-8", newline="\n")

    design_boundary = REP / "design_scenario_and_unfinished_metric_boundary.md"
    replace_or_append_section(
        design_boundary,
        "## S2 Main Result",
        f"""S2 removes `{qa['removed_cells']}` collision cells (`{qa['removed_area_m2']:.1f} m2`, `{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%` of S0 footprint) along two east-west and one north-south least-removal corridors. At z~2 m, S2 changes equal-weighted mean VR by `{float(comp2['delta_vr_mean']):.6f}` and changes VR<0.2 stagnation ratio by `{float(comp2['delta_stagnation_ratio_vr_lt_0p2']):.6f}`. Newly opened cells remain low-speed, with S2 mean VR `{float(open2['newly_open_target_vr_mean']):.6f}` and stagnation ratio `{float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`.

The S1-S2 sequence should be written as a design-screening finding: increasing geometric porosity alone did not recover pedestrian-layer ventilation in this campus-core configuration. The next design hypothesis should focus on wind-sector-coupled gateways, edge permeability and enclosure reduction at effective momentum-entry positions, not arbitrary footprint removal."""
    )

    claim_boundary = REP / "claim_boundary.md"
    add_section_once(
        claim_boundary,
        "## S2 Claim Boundary Addendum",
        """- `newly_run`: S2 geometry was generated, voxelized, simulated in FluidX3D for eight wind directions, and compared with S0/S1 using the same postprocessing protocol.
- Supported claim: S2 does not produce meaningful global pedestrian-layer ventilation recovery under the current dx=2 m, 8-direction protocol.
- Unsupported claim: S2 proves that all porosity interventions fail, or that the tested geometry is a constructable campus design.
- Paper-safe interpretation: S1 and S2 jointly suggest that effective ventilation improvement in this campus core requires wind-sector-coupled porosity and momentum-entry positioning rather than simple geometric opening area."""
    )

    s2_index = """
The design-application layer now includes a second executed sensitivity case, `S2_network_porosity`. S2 tests two east-west plus one north-south least-removal porosity corridors. It was simulated with the same FluidX3D dx=2 m, 8-direction, three-sample protocol as S0/S1. The result remains near-null/negative at the global pedestrian layer, refining the conclusion from "single corridor is insufficient" to "geometric porosity alone is insufficient unless coupled to effective wind-entry positions".

- `reports/s2_network_porosity_fluidx3d_comparison_report.md`
- `paper_text/design_intervention_s2_discussion_zh.md`
- `paper_text/design_intervention_s2_discussion_en.md`
- `manifests/s2_design_intervention_claims.csv`
- `figures/fluidx3d_s0_s2_network_porosity_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_s2_design_sensitivity_height_metric_comparison.png`
"""
    add_section_once(ROOT / "README.md", "## Executed S2 Network-Porosity Sensitivity Scenario", s2_index)
    add_section_once(REP / "final_experiment_package_index.md", "## Executed S2 Network-Porosity Sensitivity Scenario", s2_index)

    current = REP / "current_data_summary_and_conclusions.md"
    add_section_once(
        current,
        "### 7.2 S2 Network-Porosity Addendum",
        f"""S2 network porosity was simulated as a stronger follow-up to S1. It removes `{qa['removed_cells']}` heightfield collision cells (`{100.0*qa['removed_fraction_of_baseline_footprint']:.2f}%` of S0 footprint) along three least-removal corridors and reruns the same FluidX3D dx=2 m, eight-direction, three-sample protocol. At z~2 m, equal-weighted mean VR changes by `{float(comp2['delta_vr_mean']):.6f}`, while newly opened cells have mean VR `{float(open2['newly_open_target_vr_mean']):.6f}` and stagnation ratio `{float(open2['newly_open_stagnation_ratio_vr_lt_0p2']):.3f}`. This extends the design conclusion: simple geometric porosity, even at a network scale, is insufficient unless located where external momentum can enter the campus core."""
    )


def update_current_summary_count() -> None:
    current = REP / "current_data_summary_and_conclusions.md"
    text = current.read_text(encoding="utf-8")
    count = len(read_csv(MAN / "evidence_inventory.csv"))
    old = "| Evidence inventory | `manifests/evidence_inventory.csv` | "
    start = text.find(old)
    if start >= 0:
        row_end = text.find("\n", start)
        row = text[start:row_end]
        parts = row.split("|")
        if len(parts) >= 5:
            parts[3] = f" {count} rows "
            text = text[:start] + "|".join(parts) + text[row_end:]
            current.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    run_summary_path = copy_run_summary()
    qa = json.loads((MAN / "geometry_qa_core_prism_s2_network_porosity.json").read_text(encoding="utf-8"))
    comp = read_csv(FIG / "fluidx3d_s0_s2_network_porosity_metric_comparison.csv")
    open_delta = read_csv(FIG / "fluidx3d_s0_s2_network_porosity_common_open_delta_summary.csv")
    run_summary = read_csv(run_summary_path)
    comp2 = metric_row(comp, 2.0)
    open2 = metric_row(open_delta, 2.0)

    update_manifests(qa, run_summary, comp2, open2)
    write_reports_and_paper(qa, run_summary, comp, open_delta)
    update_current_summary_count()
    print("Synthesized S2 design-intervention results.")


if __name__ == "__main__":
    main()
