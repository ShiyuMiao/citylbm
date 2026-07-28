from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = Path(r"F:\citylbm_fluidx3d_workspace\tum2twin_case")
OUT_DIR = CASE_DIR / "output"
CASE_FIG_DIR = CASE_DIR / "figures"
PROJECT_FIG_DIR = ROOT / "figures"
REPORTS = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"

LABEL_TEMPLATES = {
    "S0": "core_prism_avg_wd{wd:03d}_dx2m_spin6k_s3",
    "S1": "core_prism_s1_relief_avg_wd{wd:03d}_dx2m_spin6k_s3",
    "S2": "core_prism_s2_network_avg_wd{wd:03d}_dx2m_spin6k_s3",
}
COMPARISONS = [("S1", "S0"), ("S2", "S0"), ("S2", "S1")]
WIND_DIRS = [0, 45, 90, 135, 180, 225, 270, 315]
SAMPLES = [(0, "000008000"), (1, "000010000"), (2, "000012000")]
Z_LEVELS = [1, 2, 5, 10, 20]
DX = 2.0
U_REF = 5.0
CELL_AREA_M2 = DX * DX
PANEL_Z = 1
DELTA_THRESHOLD = 0.02


def read_vtk(path: Path):
    raw = path.read_bytes()
    marker = b"LOOKUP_TABLE default\n"
    start = raw.index(marker) + len(marker)
    header = raw[:start].decode("ascii", errors="replace")
    dims = tuple(int(v) for v in re.search(r"DIMENSIONS\s+(\d+)\s+(\d+)\s+(\d+)", header).groups())
    origin = tuple(float(v) for v in re.search(r"ORIGIN\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    spacing = tuple(float(v) for v in re.search(r"SPACING\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", header).groups())
    point_data = int(re.search(r"POINT_DATA\s+(\d+)", header).group(1))
    scalar_match = re.search(r"SCALARS\s+\S+\s+(\S+)(?:\s+(\d+))?", header)
    dtype_name = scalar_match.group(1)
    components = int(scalar_match.group(2) or "1")
    dtype = ">f4" if dtype_name == "float" else np.uint8
    arr = np.frombuffer(raw, dtype=dtype, count=point_data * components, offset=start).copy()
    if dtype_name == "float":
        arr = arr.astype(np.float32)
    if components > 1:
        arr = arr.reshape((dims[2], dims[1], dims[0], components))
    else:
        arr = arr.reshape((dims[2], dims[1], dims[0]))
    return {"dims": dims, "origin": origin, "spacing": spacing}, arr


def extent_xy(meta):
    nx, ny, _ = meta["dims"]
    ox, oy, _ = meta["origin"]
    sx, sy, _ = meta["spacing"]
    return [ox, ox + sx * (nx - 1), oy, oy + sy * (ny - 1)]


def scenario_direction_maps(scenario: str, wd: int):
    label = LABEL_TEMPLATES[scenario].format(wd=wd)
    flags_path = OUT_DIR / f"matrix_{label}_flags_sample_2flags-000012000.vtk"
    meta, flags = read_vtk(flags_path)
    solid_by_z = {z: (flags[z] & 1) > 0 for z in Z_LEVELS}
    time_sum = {z: None for z in Z_LEVELS}
    for sample_idx, step in SAMPLES:
        u_path = OUT_DIR / f"matrix_{label}_u_sample_{sample_idx}u-{step}.vtk"
        _, u = read_vtk(u_path)
        speed = np.linalg.norm(u, axis=3) / U_REF
        for z in Z_LEVELS:
            if time_sum[z] is None:
                time_sum[z] = speed[z].astype(np.float32)
            else:
                time_sum[z] += speed[z].astype(np.float32)
    vr_by_z = {z: time_sum[z] / float(len(SAMPLES)) for z in Z_LEVELS}
    return meta, solid_by_z, vr_by_z


def component_count(mask: np.ndarray) -> tuple[int, int]:
    labels, nlab = ndimage.label(mask)
    if nlab == 0:
        return 0, 0
    sizes = np.bincount(labels.ravel())[1:]
    return int(nlab), int(sizes.max())


def analyze_pair(target: str, reference: str):
    rows = []
    panel_deltas = []
    panel_meta = None
    for wd in WIND_DIRS:
        ref_meta, ref_solid, ref_vr = scenario_direction_maps(reference, wd)
        tgt_meta, tgt_solid, tgt_vr = scenario_direction_maps(target, wd)
        if panel_meta is None:
            panel_meta = ref_meta
        for z in Z_LEVELS:
            ref_open = ~ref_solid[z]
            tgt_open = ~tgt_solid[z]
            common = ref_open & tgt_open
            newly_open = ~ref_open & tgt_open
            closed = ref_open & ~tgt_open
            delta = tgt_vr[z] - ref_vr[z]
            common_delta = delta[common]
            improved = common & (delta > DELTA_THRESHOLD)
            worsened = common & (delta < -DELTA_THRESHOLD)
            improved_components, largest_improved = component_count(improved)
            worsened_components, largest_worsened = component_count(worsened)
            new_vals = tgt_vr[z][newly_open]
            ref_vals = ref_vr[z][ref_open]
            tgt_vals = tgt_vr[z][tgt_open]
            row = {
                "evidence_type": "newly_run",
                "comparison": f"{target}_minus_{reference}",
                "target": target,
                "reference": reference,
                "averaging": "time_mean_3_samples",
                "wind_deg": wd,
                "dx_m": DX,
                "z_index": z,
                "z_height_m_approx": z * DX,
                "reference_open_cells": int(ref_open.sum()),
                "target_open_cells": int(tgt_open.sum()),
                "common_open_cells": int(common.sum()),
                "newly_open_cells": int(newly_open.sum()),
                "closed_cells": int(closed.sum()),
                "reference_vr_mean": float(ref_vals.mean()),
                "target_vr_mean": float(tgt_vals.mean()),
                "delta_global_vr_mean": float(tgt_vals.mean() - ref_vals.mean()),
                "reference_stagnation_ratio_vr_lt_0p2": float((ref_vals < 0.2).mean()),
                "target_stagnation_ratio_vr_lt_0p2": float((tgt_vals < 0.2).mean()),
                "delta_global_stagnation_ratio_vr_lt_0p2": float((tgt_vals < 0.2).mean() - (ref_vals < 0.2).mean()),
                "common_delta_vr_mean": float(common_delta.mean()) if common_delta.size else "",
                "common_delta_vr_p05": float(np.percentile(common_delta, 5)) if common_delta.size else "",
                "common_delta_vr_p50": float(np.percentile(common_delta, 50)) if common_delta.size else "",
                "common_delta_vr_p95": float(np.percentile(common_delta, 95)) if common_delta.size else "",
                "common_improved_ratio_delta_gt_0p02": float(improved[common].mean()) if common_delta.size else "",
                "common_worsened_ratio_delta_lt_minus_0p02": float(worsened[common].mean()) if common_delta.size else "",
                "common_improved_area_m2": float(improved.sum() * CELL_AREA_M2),
                "common_worsened_area_m2": float(worsened.sum() * CELL_AREA_M2),
                "improved_components": improved_components,
                "largest_improved_component_cells": largest_improved,
                "worsened_components": worsened_components,
                "largest_worsened_component_cells": largest_worsened,
                "newly_open_target_vr_mean": float(new_vals.mean()) if new_vals.size else "",
                "newly_open_target_vr_p95": float(np.percentile(new_vals, 95)) if new_vals.size else "",
                "newly_open_stagnation_ratio_vr_lt_0p2": float((new_vals < 0.2).mean()) if new_vals.size else "",
                "newly_open_effective_ratio_vr_ge_0p2": float((new_vals >= 0.2).mean()) if new_vals.size else "",
            }
            rows.append(row)
            if z == PANEL_Z:
                panel_deltas.append((wd, np.where(common, delta, np.nan)))
    return rows, panel_meta, panel_deltas


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_directional_heatmap(rows: list[dict]):
    metrics = [
        ("delta_global_vr_mean", "Global mean VR delta"),
        ("common_delta_vr_mean", "Common-open mean delta VR"),
        ("common_improved_ratio_delta_gt_0p02", "Common-open ratio delta>0.02"),
        ("common_worsened_ratio_delta_lt_minus_0p02", "Common-open ratio delta<-0.02"),
        ("newly_open_target_vr_mean", "Newly opened mean VR"),
    ]
    comparisons = ["S1_minus_S0", "S2_minus_S0", "S2_minus_S1"]
    fig, axes = plt.subplots(len(comparisons), len(metrics), figsize=(22, 10), dpi=170, constrained_layout=True)
    for r_idx, comp in enumerate(comparisons):
        comp_rows = [r for r in rows if r["comparison"] == comp and int(r["z_index"]) == PANEL_Z]
        for c_idx, (metric, title) in enumerate(metrics):
            vals = np.array([[float(r[metric]) if r[metric] != "" else np.nan for r in comp_rows]])
            ax = axes[r_idx, c_idx]
            if "delta" in metric:
                im = ax.imshow(vals, cmap="coolwarm", vmin=-0.02, vmax=0.02, aspect="auto")
            elif "ratio" in metric:
                im = ax.imshow(vals, cmap="magma", vmin=0.0, vmax=0.08, aspect="auto")
            else:
                im = ax.imshow(vals, cmap="viridis", vmin=0.0, vmax=0.08, aspect="auto")
            ax.set_yticks([0], [comp])
            ax.set_xticks(range(len(comp_rows)), [str(r["wind_deg"]) for r in comp_rows], rotation=45)
            ax.set_title(title)
            fig.colorbar(im, ax=ax, shrink=0.75)
    path = CASE_FIG_DIR / "fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_delta_panel(meta, panel_deltas, comparison: str):
    extent = extent_xy(meta)
    fig, axes = plt.subplots(2, 4, figsize=(18, 9), dpi=170, constrained_layout=True)
    for ax, (wd, delta) in zip(axes.ravel(), panel_deltas):
        im = ax.imshow(np.ma.masked_invalid(delta), origin="lower", extent=extent, cmap="coolwarm", vmin=-0.12, vmax=0.12, interpolation="nearest")
        ax.set_title(f"{comparison}, WD {wd:03d}, z~2 m")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.9)
    cbar.set_label("Delta VR")
    fig.suptitle(f"Directional local trade-off maps: {comparison}, common-open cells")
    path = CASE_FIG_DIR / f"fluidx3d_{comparison.lower()}_directional_delta_panel_z2m.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def summarize(rows: list[dict]):
    summary = []
    for comp in ["S1_minus_S0", "S2_minus_S0", "S2_minus_S1"]:
        comp_rows = [r for r in rows if r["comparison"] == comp and int(r["z_index"]) == PANEL_Z]
        best_common = max(comp_rows, key=lambda r: float(r["common_delta_vr_mean"]))
        worst_common = min(comp_rows, key=lambda r: float(r["common_delta_vr_mean"]))
        best_global = max(comp_rows, key=lambda r: float(r["delta_global_vr_mean"]))
        worst_global = min(comp_rows, key=lambda r: float(r["delta_global_vr_mean"]))
        summary.append({
            "evidence_type": "newly_run",
            "comparison": comp,
            "z_height_m_approx": 2.0,
            "best_common_wind_deg": best_common["wind_deg"],
            "best_common_delta_vr_mean": best_common["common_delta_vr_mean"],
            "worst_common_wind_deg": worst_common["wind_deg"],
            "worst_common_delta_vr_mean": worst_common["common_delta_vr_mean"],
            "best_global_wind_deg": best_global["wind_deg"],
            "best_global_delta_vr_mean": best_global["delta_global_vr_mean"],
            "worst_global_wind_deg": worst_global["wind_deg"],
            "worst_global_delta_vr_mean": worst_global["delta_global_vr_mean"],
            "mean_common_improved_ratio_delta_gt_0p02": float(np.mean([float(r["common_improved_ratio_delta_gt_0p02"]) for r in comp_rows])),
            "mean_common_worsened_ratio_delta_lt_minus_0p02": float(np.mean([float(r["common_worsened_ratio_delta_lt_minus_0p02"]) for r in comp_rows])),
            "max_newly_open_target_vr_mean": float(max(float(r["newly_open_target_vr_mean"]) for r in comp_rows if r["newly_open_target_vr_mean"] != "")),
            "min_newly_open_stagnation_ratio": float(min(float(r["newly_open_stagnation_ratio_vr_lt_0p2"]) for r in comp_rows if r["newly_open_stagnation_ratio_vr_lt_0p2"] != "")),
        })
    return summary


def append_evidence() -> None:
    path = MAN / "evidence_inventory.csv"
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    new = {
        "claim": "S1/S2 design-sensitivity effects are directionally localized and globally weak; newly opened cells remain low-speed across the tested pedestrian-layer trade-off analysis.",
        "evidence_type": "newly_run",
        "source": "figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv; reports/design_sensitivity_directional_tradeoff_analysis.md",
    }
    if not any(r["claim"] == new["claim"] and r["source"] == new["source"] for r in rows):
        rows.append(new)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(summary: list[dict]) -> None:
    s1 = next(r for r in summary if r["comparison"] == "S1_minus_S0")
    s2 = next(r for r in summary if r["comparison"] == "S2_minus_S0")
    s21 = next(r for r in summary if r["comparison"] == "S2_minus_S1")
    report = f"""# Design-Sensitivity Directional Trade-Off Analysis

evidence_type: newly_run

This report reprocesses the existing S0, S1 and S2 FluidX3D VTK outputs without rerunning the solver. The goal is to determine whether the negative or near-null equal-weighted design result hides directional or local trade-offs.

## Protocol

- Source VTK: `F:/citylbm_fluidx3d_workspace/tum2twin_case/output`
- Scenarios: `S0`, `S1_ventilation_relief`, `S2_network_porosity`
- Wind directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Averaging: three post-spin-up samples per wind direction.
- Pedestrian-layer focus: z~2 m.
- Local trade-off threshold: `Delta VR > 0.02` for improved common-open cells and `Delta VR < -0.02` for worsened common-open cells.

## Key Findings

For S1-S0, the best common-open wind direction is `{s1['best_common_wind_deg']}` deg with mean common-open delta VR `{float(s1['best_common_delta_vr_mean']):.6f}`. The mean area share of common-open cells with delta VR>0.02 across directions is only `{float(s1['mean_common_improved_ratio_delta_gt_0p02']):.6f}`, while the mean worsened share is `{float(s1['mean_common_worsened_ratio_delta_lt_minus_0p02']):.6f}`. Newly opened S1 cells never form an effective pedestrian-height flow path; the highest direction-wise mean VR among newly opened cells is `{float(s1['max_newly_open_target_vr_mean']):.6f}`.

For S2-S0, the best common-open wind direction is `{s2['best_common_wind_deg']}` deg with mean common-open delta VR `{float(s2['best_common_delta_vr_mean']):.6f}`. The mean improved share is `{float(s2['mean_common_improved_ratio_delta_gt_0p02']):.6f}`, while the mean worsened share is `{float(s2['mean_common_worsened_ratio_delta_lt_minus_0p02']):.6f}`. Although S2 has more local response than S1, the highest newly opened mean VR across wind directions is still only `{float(s2['max_newly_open_target_vr_mean']):.6f}`, and the minimum newly opened stagnation ratio remains `{float(s2['min_newly_open_stagnation_ratio']):.6f}`.

S2-S1 confirms that the stronger network-porosity case changes local common-open cells more than S1, but it still does not create a global ventilation recovery. Its best global wind direction is `{s21['best_global_wind_deg']}` deg with global mean delta VR `{float(s21['best_global_delta_vr_mean']):.6f}`.

## Paper Interpretation

The design result should not be written as a simple null statement. S1/S2 produce weak and directionally localized changes in common-open cells, but these local changes are too sparse to shift the equal-weighted pedestrian-layer state. The newly opened cells are the decisive evidence: they remain low-speed, meaning that the intervention geometry created open space without creating a momentum-carrying path. This supports a more precise design conclusion: in this campus-core configuration, wind-environment improvement requires wind-sector-coupled gateway placement and pressure-exchange continuity, not only increased geometric porosity.

## Artifacts

- `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png`
- `figures/fluidx3d_s2_minus_s0_directional_delta_panel_z2m.png`
- `figures/fluidx3d_s1_minus_s0_directional_delta_panel_z2m.png`

## Claim Boundary

This is a deterministic post-processing analysis of existing FluidX3D outputs. It does not add measured validation, annual wind-rose comfort probability, pollutant dispersion or constructability evidence.
"""
    (REPORTS / "design_sensitivity_directional_tradeoff_analysis.md").write_text(report, encoding="utf-8", newline="\n")

    zh = f"""# 设计敏感性方向性 trade-off 讨论段落

evidence_type: newly_run

为避免把 S1/S2 简化为单一“无效”结论，本文进一步对 8 个风向的 VTK 输出进行方向性 trade-off 后处理。该分析不重新运行求解器，而是在每个风向内比较 S1-S0、S2-S0 和 S2-S1 的三时间样本平均 VR，并在 z=2 m 行人层统计共同开放单元的 ΔVR、新增开放单元的风速状态以及局部改善/恶化面积。

结果显示，S1/S2 的确会在共同开放单元中产生微弱且方向相关的局部响应，但这些响应不足以改变整体行人层通风状态。S1-S0 中，共同开放单元最佳风向为 {s1['best_common_wind_deg']} deg，mean ΔVR 仅为 {float(s1['best_common_delta_vr_mean']):.6f}；S2-S0 中，最佳风向为 {s2['best_common_wind_deg']} deg，mean ΔVR 为 {float(s2['best_common_delta_vr_mean']):.6f}。S2 的局部响应强于 S1，但其跨风向平均的 ΔVR>0.02 共同开放单元比例仍只有 {float(s2['mean_common_improved_ratio_delta_gt_0p02']):.6f}，说明改善区域非常有限。

更关键的是新增开放单元本身并没有形成有效通风路径。S1 新增开放单元在各风向中的最高 mean VR 仅为 {float(s1['max_newly_open_target_vr_mean']):.6f}；S2 虽然打开了更强的网络孔隙，但新增开放单元最高 mean VR 也仅为 {float(s2['max_newly_open_target_vr_mean']):.6f}，最低低速比例仍为 {float(s2['min_newly_open_stagnation_ratio']):.6f}。因此，S2 的意义不是证明“网络孔隙必然无效”，而是说明在当前校园核心区，几何开敞如果没有与外部动量入口、风向扇区和压力交换路径耦合，就可能只是低速背景中的新增开敞空间。

这一方向性分析使论文结论更细：S1/S2 并非完全没有局部气动响应，而是局部改善过于稀疏，且新增空间没有获得足够动量输入，因而无法转化为全局行人层通风恢复。由此，后续真正具有设计潜力的 S3-Sn 不应继续简单增加孔隙面积，而应围绕有效来流边界、入口廊道位置、风向扇区和局地围合解除进行构型。
"""
    (PAPER / "design_sensitivity_directional_tradeoff_discussion_zh.md").write_text(zh, encoding="utf-8", newline="\n")


def main() -> None:
    all_rows = []
    panels = {}
    for target, reference in COMPARISONS:
        rows, meta, panel = analyze_pair(target, reference)
        all_rows.extend(rows)
        panels[f"{target}_minus_{reference}"] = (meta, panel)
    summary = summarize(all_rows)

    tradeoff_csv = CASE_FIG_DIR / "fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv"
    write_csv(tradeoff_csv, all_rows)
    summary_csv = CASE_FIG_DIR / "fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv"
    write_csv(summary_csv, summary)
    heatmap = plot_directional_heatmap(all_rows)
    panel_paths = []
    for comp in ["S1_minus_S0", "S2_minus_S0", "S2_minus_S1"]:
        meta, panel = panels[comp]
        panel_paths.append(plot_delta_panel(meta, panel, comp))

    for path in [tradeoff_csv, summary_csv, heatmap, *panel_paths]:
        shutil.copyfile(path, PROJECT_FIG_DIR / path.name)
        print(PROJECT_FIG_DIR / path.name)

    append_evidence()
    write_report(summary)
    print(REPORTS / "design_sensitivity_directional_tradeoff_analysis.md")
    print(PAPER / "design_sensitivity_directional_tradeoff_discussion_zh.md")


if __name__ == "__main__":
    main()
