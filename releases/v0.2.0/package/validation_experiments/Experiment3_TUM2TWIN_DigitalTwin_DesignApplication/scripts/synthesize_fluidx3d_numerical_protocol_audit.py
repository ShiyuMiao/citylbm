from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path.cwd()
MAN = ROOT / "manifests"
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def lookup(rows: list[dict[str, str]], field: str) -> str:
    for row in rows:
        if row.get("field") == field:
            return row.get("value", "")
    return ""


def upsert_csv(path: Path, rows_to_add: list[dict[str, str]], key: str, fieldnames: list[str]) -> None:
    rows = read_csv(path)
    by_key = {row.get(key, ""): row for row in rows}
    for row in rows_to_add:
        by_key[row[key]] = row
    write_csv(path, list(by_key.values()), fieldnames)


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |"]
    out.append("|" + "|".join(["---"] * len(fields)) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def build_protocol_rows(boundary: list[dict[str, str]]) -> list[dict[str, str]]:
    grid = lookup(boundary, "grid_Nx_Ny_Nz") or "320 x 390 x 60"
    dx = lookup(boundary, "dx") or "2.0"
    domain = lookup(boundary, "domain_size") or "640 x 780 x 120"
    uref = lookup(boundary, "reference_speed_Uref") or "5.0"
    nu_air = lookup(boundary, "air_kinematic_viscosity") or "1.5e-5"
    rho = lookup(boundary, "air_density") or "1.225"
    dt = lookup(boundary, "dt") or "0.02"
    tau = lookup(boundary, "relaxation_time_tau") or "0.52999996"
    lbm_nu = lookup(boundary, "lbm_nu_smoke") or "0.01000"
    re_dx = lookup(boundary, "physical_Re_dx") or "666667"
    re_reported = lookup(boundary, "FluidX3D_reported_Re") or "< 29331"
    wind_dirs = lookup(boundary, "wind_directions") or "0;45;90;135;180;225;270;315"
    sample_steps = lookup(boundary, "sample_steps") or "8000;10000;12000"
    spinup = lookup(boundary, "spinup_steps") or "6000"
    run_steps = lookup(boundary, "run_steps") or "12000"

    rows = [
        {
            "protocol_item": "collision_geometry",
            "status": "recorded_complete_for_screening",
            "value": "core_photogrammetry_extent_prism_collision_z0.stl",
            "unit_or_scope": "closed z0-aligned prism collision geometry",
            "evidence_type": "newly_run",
            "source_artifact": "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl; manifests/geometry_qa_core_photogrammetry_extent_prism.json",
            "paper_safe_use": "Use as the accepted S0 collision boundary for the core campus screening case.",
            "claim_boundary": "Do not describe the textured photogrammetry shell as the collision boundary.",
            "reviewer_risk": "low",
        },
        {
            "protocol_item": "grid_and_domain",
            "status": "recorded_complete_for_screening",
            "value": f"{grid}; dx={dx}; domain={domain}",
            "unit_or_scope": "lattice cells; m/cell; m",
            "evidence_type": "newly_run",
            "source_artifact": "manifests/fluidx3d_core_prism_boundary_condition_table.csv; reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md",
            "paper_safe_use": "Report as the core dx=2 m screening grid.",
            "claim_boundary": "Not a grid-independent final engineering simulation.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "physical_reference_values",
            "status": "recorded_complete_for_pilot_normalization",
            "value": f"Uref={uref}; nu_air={nu_air}; rho={rho}",
            "unit_or_scope": "m/s; m2/s; kg/m3",
            "evidence_type": "newly_run",
            "source_artifact": "cfd_ready/FluidX3D_case_template/setup_tum2twin_wind_pilot.cpp; manifests/fluidx3d_core_prism_boundary_condition_table.csv",
            "paper_safe_use": "Use to define the pilot velocity-ratio normalization and air-property conversion.",
            "claim_boundary": "Uref is not a measured site wind profile and does not establish annual comfort exceedance probability.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "lbm_conversion",
            "status": "recorded_with_boundary",
            "value": f"dt={dt}; lbm_nu={lbm_nu}; tau={tau}",
            "unit_or_scope": "s/time step; lattice units",
            "evidence_type": "newly_run",
            "source_artifact": "logs/run_core_prism_avg_wd000_dx2m_spin6k_s3.log; manifests/fluidx3d_core_prism_boundary_condition_table.csv",
            "paper_safe_use": "Report as archived solver-conversion evidence for the completed FluidX3D pilot.",
            "claim_boundary": "Tau is close to the low-relaxation stability side; this supports protocol transparency, not solver validation.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "reynolds_reporting",
            "status": "recorded_with_boundary",
            "value": f"Re_dx={re_dx}; FluidX3D_reported_Re={re_reported}",
            "unit_or_scope": "reported/computed values",
            "evidence_type": "newly_run",
            "source_artifact": "logs/run_core_prism_avg_wd000_dx2m_spin6k_s3.log; manifests/fluidx3d_core_prism_boundary_condition_table.csv",
            "paper_safe_use": "Use as a protocol descriptor, not as validation of Reynolds similarity.",
            "claim_boundary": "No wind-tunnel or field Reynolds-scaling closure is established.",
            "reviewer_risk": "high_if_overstated",
        },
        {
            "protocol_item": "wind_direction_protocol",
            "status": "recorded_complete_for_screening",
            "value": wind_dirs,
            "unit_or_scope": "velocity-to degrees",
            "evidence_type": "newly_run",
            "source_artifact": "scripts/run_fluidx3d_core_prism_timesampled_8dir_dx2m.ps1; figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_safe_use": "Use for eight-direction screening and equal-weighted aggregation.",
            "claim_boundary": "Open-Meteo weighting remains a climate proxy, not a formal measured wind rose.",
            "reviewer_risk": "low",
        },
        {
            "protocol_item": "sampling_protocol",
            "status": "recorded_complete_for_short_time_sampling",
            "value": f"spinup={spinup}; run_steps={run_steps}; samples={sample_steps}",
            "unit_or_scope": "FluidX3D time steps",
            "evidence_type": "newly_run",
            "source_artifact": "scripts/run_fluidx3d_core_prism_timesampled_8dir_dx2m.ps1; reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md",
            "paper_safe_use": "Use to support the internal time-sampled screening claim.",
            "claim_boundary": "This is not a long statistical averaging or residual-convergence proof.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "output_planes_and_metrics",
            "status": "recorded_complete_for_screening",
            "value": "z~2,4,10,20,40 m; mean/P75/P90/P95/max VR; VR<0.2, VR>0.6, VR>1.0",
            "unit_or_scope": "height planes and velocity-ratio metrics",
            "evidence_type": "newly_run",
            "source_artifact": "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
            "paper_safe_use": "Use for pedestrian-height and vertical-recovery interpretation.",
            "claim_boundary": "Thresholds are screening bins, not Lawson/NEN/AIJ annual classes.",
            "reviewer_risk": "low",
        },
        {
            "protocol_item": "solid_and_open_boundary_semantics",
            "status": "recorded_with_boundary",
            "value": "buildings/ground as TYPE_S; directional pilot forcing/velocity setup",
            "unit_or_scope": "FluidX3D mask and boundary-condition convention",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "manifests/fluidx3d_core_prism_boundary_condition_table.csv; cfd_ready/FluidX3D_case_template/setup_tum2twin_wind_pilot.cpp",
            "paper_safe_use": "Use to explain no-slip collision treatment and pilot inflow status.",
            "claim_boundary": "A measured atmospheric boundary-layer inlet profile is not established in the archive.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "temporal_stability",
            "status": "partial_screening_support",
            "value": "3 post-spin-up samples per direction; effect-size intervals available",
            "unit_or_scope": "8000/10000/12000 steps",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/experiment3_effect_size_uncertainty_summary.csv; reports/experiment3_effect_size_uncertainty_analysis.md",
            "paper_safe_use": "Use to say the main low-speed and vertical-recovery patterns are stable within archived samples.",
            "claim_boundary": "Do not call this formal convergence, stationarity or uncertainty quantification.",
            "reviewer_risk": "medium",
        },
        {
            "protocol_item": "grid_sensitivity",
            "status": "partial_support_outside_core_final_case",
            "value": "district coarse/medium and full-LoD2 coarse/medium audit files exist",
            "unit_or_scope": "selected comparison cases",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/fluidx3d_district_prism_grid_comparison_common_heights.csv; figures/fluidx3d_full_lod2_wd000_coarse_vs_medium_metrics.csv",
            "paper_safe_use": "Use only as a supporting sensitivity audit.",
            "claim_boundary": "The core dx=2 m S0/S1/S2 results are not a full grid-independence study.",
            "reviewer_risk": "high_if_overstated",
        },
        {
            "protocol_item": "residual_or_solver_convergence",
            "status": "blocked_not_recorded",
            "value": "[RESULT_NEEDED: residual/convergence monitor]",
            "unit_or_scope": "solver residual or statistical convergence record",
            "evidence_type": "blocked",
            "source_artifact": "reports/claim_boundary.md",
            "paper_safe_use": "State as a limitation and next rigor step.",
            "claim_boundary": "Do not claim formal numerical convergence.",
            "reviewer_risk": "high_if_overstated",
        },
        {
            "protocol_item": "field_validation_and_compliance",
            "status": "blocked_not_available",
            "value": "[RESULT_NEEDED: measured wind, wind tunnel, annual exceedance probabilities]",
            "unit_or_scope": "external validation and annual comfort protocol",
            "evidence_type": "blocked",
            "source_artifact": "reports/claim_boundary.md; reports/experiment3_reviewer_reproducibility_and_claim_audit.md",
            "paper_safe_use": "Keep the experiment framed as digital-twin screening and design interpretation.",
            "claim_boundary": "No field-validated prediction, annual Lawson/NEN/AIJ compliance or pollutant dispersion claim.",
            "reviewer_risk": "high_if_overstated",
        },
    ]
    return rows


def upsert_evidence_inventory() -> None:
    rows = [
        {
            "claim": "FluidX3D numerical protocol, conversion parameters, sampling, grid-sensitivity status and blocked convergence/compliance claims were audited as a paper-facing risk table.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/fluidx3d_numerical_protocol_audit.csv; reports/fluidx3d_numerical_protocol_and_stability_audit.md",
        },
        {
            "claim": "Numerical protocol paper paragraphs were drafted with explicit boundaries around Uref, tau/Re, time sampling, grid sensitivity, residual convergence and field validation.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/fluidx3d_numerical_protocol_methods_zh.md; paper_text/fluidx3d_numerical_protocol_methods_en.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", rows, "claim", ["claim", "evidence_type", "source"])


def upsert_key_result_matrix() -> None:
    row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "FluidX3D numerical protocol transparency",
        "metric": "dx / grid / Uref / nu_air / tau / samples / blocked convergence",
        "value": "2 m / 320x390x60 / 5 m s-1 / 1.5e-5 m2 s-1 / 0.52999996 / 8000-10000-12000 / residual not recorded",
        "source_artifact": "manifests/fluidx3d_numerical_protocol_audit.csv; manifests/fluidx3d_core_prism_boundary_condition_table.csv",
        "paper_safe_claim": "The FluidX3D case is transparent enough for screening-level reproduction, while formal convergence, field validation and annual compliance remain blocked.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [row],
        "claim_layer",
        [
            "evidence_type",
            "claim_layer",
            "metric",
            "value",
            "source_artifact",
            "paper_safe_claim",
        ],
    )


def upsert_claim_verification() -> None:
    path = DRAFT / "experiment3_claim_verification.csv"
    if not path.exists():
        return
    rows = read_csv(path)
    fieldnames = list(rows[0].keys()) if rows else ["claim_layer", "evidence_type", "source", "value", "paper_safe_claim", "claim_readiness"]
    row = {
        "claim_layer": "module_claim_R4",
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "source": "manifests/fluidx3d_numerical_protocol_audit.csv; reports/fluidx3d_numerical_protocol_and_stability_audit.md",
        "value": "paper_ready_with_boundary",
        "paper_safe_claim": "FluidX3D numerical parameters are archived for screening-level reproduction; residual convergence, field validation and annual compliance are not claimed.",
        "claim_readiness": "paper_ready_with_boundary",
    }
    normalized = {name: row.get(name, "") for name in fieldnames}
    rows = [item for item in rows if item.get("claim_layer") != "module_claim_R4"]
    rows.append(normalized)
    write_csv(path, rows, fieldnames)


def write_reports(protocol_rows: list[dict[str, str]]) -> None:
    table_fields = [
        "protocol_item",
        "status",
        "value",
        "evidence_type",
        "paper_safe_use",
        "claim_boundary",
    ]
    report = f"""# FluidX3D Numerical Protocol and Stability Audit

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This audit deepens the Experiment 3 evidence package by separating archived
FluidX3D protocol facts from numerical and validation claims that remain
unsupported. It adds no new CFD field and does not change the reported wind
maps. Its role is to make the dx=2 m, eight-direction, time-sampled screening
case reproducible enough for manuscript review while preventing overclaiming.

## Protocol Table

{md_table(protocol_rows, table_fields)}

## What This Adds to the Paper Conclusion

The strongest numerical conclusion is not that the simulation is a
field-validated prediction. The supported conclusion is narrower and more
useful for a digital-twin application paper: the TUM2TWIN core campus block can
be translated into an auditable FluidX3D-native screening case with recorded
geometry, grid, reference-speed, viscosity, LBM conversion, wind-direction and
sampling parameters. The resulting low pedestrian-layer VR pattern is stable
within the archived direction-sample evidence, while the same archive keeps
residual convergence, complete grid independence, field validation and annual
comfort compliance outside the claim boundary.

This strengthens the building-form discussion because it clarifies the scale of
the inference. The paper can interpret relative vertical massing, local
enclosure, plan continuity and wind-sector reactivity as screening descriptors
of a real campus block. It should not present these descriptors as universal
causal laws or code-compliance thresholds.

## Reviewer-Critical Boundaries

- The archived Uref and Open-Meteo weighting are protocol/proxy choices, not a
  measured site wind-climate closure.
- The tau/Re entries are transparent solver-conversion evidence, not a solver
  validation result.
- Three post-spin-up samples support internal pattern stability only.
- Coarse/medium comparisons support a sensitivity audit, not full grid
  independence of the core S0/S1/S2 conclusions.
- Residual convergence, field measurement, wind-tunnel closure, annual
  Lawson/NEN/AIJ compliance and pollutant dispersion remain blocked.
"""
    write_text(REP / "fluidx3d_numerical_protocol_and_stability_audit.md", report)

    en = """# FluidX3D Numerical Protocol Methods Paragraph

evidence_type: newly_run + preexisting_artifact + blocked

For Experiment 3, the TUM2TWIN core campus block was simulated as a FluidX3D-native screening case rather than as a solver-validation or annual comfort-compliance study. The accepted collision boundary was the closed z0-aligned core-prism geometry, not the textured photogrammetry shell. The archived protocol records a 320 x 390 x 60 lattice with dx = 2 m, Uref = 5 m/s, air kinematic viscosity = 1.5e-5 m2/s, dt = 0.02 s, LBM nu = 0.01000 and tau = 0.52999996. Eight velocity-to wind directions (0-315 deg at 45 deg intervals) were run with 6000 spin-up steps and three post-spin-up samples at 8000, 10000 and 12000 steps. Post-processing reports velocity-ratio metrics on z~2, 4, 10, 20 and 40 m planes. These parameters support reproducible screening-level interpretation of pedestrian low-speed regions and vertical recovery, but they do not constitute formal residual convergence, field validation, complete grid independence or annual Lawson/NEN/AIJ comfort assessment."""
    zh = """# FluidX3D 数值协议方法段落

evidence_type: newly_run + preexisting_artifact + blocked

实验 3 将 TUM2TWIN 核心校园街区作为 FluidX3D-native 筛查算例处理，而不是作为求解器精度验证或年度舒适度合规评价。被接受的碰撞边界为 z0 对齐的闭合核心棱柱几何，而不是带纹理摄影测量外壳。归档协议记录了 320 x 390 x 60 的计算格点、dx = 2 m、Uref = 5 m/s、空气运动黏度 1.5e-5 m2/s、dt = 0.02 s、LBM nu = 0.01000 和 tau = 0.52999996。算例包含 8 个 velocity-to 来流方向（0-315 deg，间隔 45 deg），每个方向先运行 6000 steps spin-up，并在 8000、10000 和 12000 steps 抽取 3 个后续样本。后处理在 z~2、4、10、20 和 40 m 高度层统计风速比指标。这些参数支持可复现的筛查性解释，包括行人层低风速区和上部风场恢复；但它们不构成正式残差收敛证明、实测验证、完整网格无关性或 Lawson/NEN/AIJ 年度舒适度评价。"""
    write_text(PAPER / "fluidx3d_numerical_protocol_methods_en.md", en)
    write_text(PAPER / "fluidx3d_numerical_protocol_methods_zh.md", zh)


def main() -> None:
    for folder in [MAN, FIG, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    boundary = read_csv(MAN / "fluidx3d_core_prism_boundary_condition_table.csv")
    protocol_rows = build_protocol_rows(boundary)
    write_csv(
        MAN / "fluidx3d_numerical_protocol_audit.csv",
        protocol_rows,
        [
            "protocol_item",
            "status",
            "value",
            "unit_or_scope",
            "evidence_type",
            "source_artifact",
            "paper_safe_use",
            "claim_boundary",
            "reviewer_risk",
        ],
    )
    write_reports(protocol_rows)
    upsert_evidence_inventory()
    upsert_key_result_matrix()
    upsert_claim_verification()
    print("fluidx3d_numerical_protocol_rows", len(protocol_rows))
    print("wrote numerical protocol audit")


if __name__ == "__main__":
    main()
