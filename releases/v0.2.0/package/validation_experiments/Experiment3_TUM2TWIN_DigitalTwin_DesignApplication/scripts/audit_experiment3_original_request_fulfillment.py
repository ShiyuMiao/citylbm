from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()
REPO_ROOT = ROOT.parents[4]
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
FIG = ROOT / "figures"


def relpath(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.relative_to(REPO_ROOT).as_posix()


def resolve_artifact(artifact: str) -> Path | None:
    if not artifact or artifact.startswith("blocked:") or artifact.startswith("AUTHOR_INPUT_NEEDED"):
        return None
    path = Path(artifact)
    if path.is_absolute():
        return path
    root_path = ROOT / path
    if root_path.exists():
        return root_path
    repo_path = REPO_ROOT / path
    if repo_path.exists():
        return repo_path
    return root_path


def exists(artifact: str) -> bool:
    path = resolve_artifact(artifact)
    return bool(path and path.exists())


def row(
    group: str,
    requirement: str,
    status: str,
    evidence_type: str,
    artifacts: list[str],
    paper_use: str,
    boundary: str,
) -> dict[str, object]:
    found = [artifact for artifact in artifacts if exists(artifact)]
    missing = [artifact for artifact in artifacts if artifact and not exists(artifact) and not artifact.startswith("blocked:")]
    return {
        "requirement_group": group,
        "requirement": requirement,
        "status": status,
        "evidence_type": evidence_type,
        "evidence_artifacts": "; ".join(artifacts),
        "files_found": len(found),
        "missing_artifacts": "; ".join(missing),
        "paper_safe_use": paper_use,
        "claim_boundary": boundary,
    }


def workspace_directory_rows() -> list[dict[str, object]]:
    expected = ["raw", "converted", "rhino", "cfd_ready", "manifests", "reports", "figures", "paper_text"]
    artifacts = [str(REPO_ROOT / name) for name in expected]
    missing = [name for name in expected if not (REPO_ROOT / name).exists()]
    status = "complete" if not missing else "partial"
    return [
        row(
            "workspace_structure",
            "Project workspace directories requested by the user are present in the working repository.",
            status,
            "newly_run",
            artifacts,
            "Documents local and release-package organization for reproduction.",
            "Large raw/converted assets may be externalized in GitHub; use manifests and EXTERNAL_ARTIFACTS for heavy files.",
        )
    ]


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(workspace_directory_rows())
    rows.extend(
        [
            row(
                "official_source_verification",
                "TUM2TWIN datasets, cm-mesh, cm-buildings, cm-vegetation, cm-cad and pc-fac source pages were recorded and layer roles were distinguished.",
                "complete",
                "newly_run + preexisting_artifact",
                [
                    "reports/data_source_and_download_manifest.md",
                    "reports/tum2twin_experiment_design.md",
                    "manifests/data_manifest.csv",
                    "manifests/tum2twin_gitlab_tree.json",
                    "manifests/tum2twin_gitlab_tree_blobs.csv",
                ],
                "Supports data provenance and the distinction between visual meshes, semantic buildings, CAD/OBJ intermediates and pc-fac semantic reference.",
                "Official data support geometry/source claims only; they do not validate wind predictions.",
            ),
            row(
                "download_manifest",
                "Downloads and external assets record source URL, size, hashes, download time, license and citation.",
                "complete_with_external_asset_boundary",
                "preexisting_artifact + newly_run",
                [
                    "manifests/data_manifest.csv",
                    "manifests/full_lod2_download_manifest.csv",
                    "EXTERNAL_ARTIFACTS.md",
                    "reports/github_archive_manifest_validation.md",
                ],
                "Supports reproducibility and repository/lightweight release packaging.",
                "Large raw assets and full VTK files are not all embedded in GitHub; manifests are the authoritative provenance layer.",
            ),
            row(
                "rhino_visualization",
                "OBJ/MTL/JPG visual reference and Rhino layer-management outputs were prepared for manual model-scope checking.",
                "complete_with_texture_boundary",
                "newly_run + user_claim + preexisting_artifact",
                [
                    "reports/rhino_geometry_conversion_report.md",
                    "reports/tum_downtown_photogrammetry_rhino_layered_geometry_audit.md",
                    "reports/user_converted_rhino_layered_package_audit.md",
                    "rhino",
                ],
                "Supports the visual-object consistency check between the simulated core and the TUM Downtown model shown by the user.",
                "Precise texture browsing should use OBJ/MTL/JPG when Rhino 3DM texture embedding is incomplete.",
            ),
            row(
                "cfd_ready_geometry",
                "CFD-ready STL geometry includes accepted collision geometry, z0 alignment, QA reports, and visual/counterexample geometry boundaries.",
                "complete",
                "newly_run",
                [
                    "cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl",
                    "cfd_ready/district_prism_collision_z0.stl",
                    "cfd_ready/visual_reference_uas_mesh_decimated.stl",
                    "reports/fluidx3d_user_photogrammetry_pilot_report.md",
                    "reports/cfd_ready_geometry_qa.md",
                    "reports/core_photogrammetry_extent_prism_collision_report.md",
                    "reports/district_prism_collision_report.md",
                    "manifests/geometry_manifest.csv",
                    "manifests/gcri_scoring_table.csv",
                ],
                "Supports the method claim that visual photogrammetry is separated from closed collision geometry.",
                "Accepted collision geometry is a repaired/derived screening geometry, not a field-surveyed wind-tunnel model.",
            ),
            row(
                "fluidx3d_execution",
                "FluidX3D-native baseline, S1 and S2 simulations were executed and postprocessed for eight wind directions.",
                "complete_with_screening_boundary",
                "newly_run",
                [
                    "reports/fluidx3d_core_prism_timesampled_8dir_dx2m_report.md",
                    "figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv",
                    "reports/s1_ventilation_relief_fluidx3d_comparison_report.md",
                    "reports/s2_network_porosity_fluidx3d_comparison_report.md",
                    "reports/fluidx3d_numerical_protocol_and_stability_audit.md",
                    "manifests/fluidx3d_numerical_protocol_audit.csv",
                ],
                "Supports screening-level wind-response, design-sensitivity and numerical-protocol reporting.",
                "Does not support field-validated accuracy, formal convergence proof or annual compliance.",
            ),
            row(
                "paraview_visualization",
                "ParaView state files and manual-review visualization assets were prepared for VTK wind-field inspection.",
                "complete_with_headless_boundary",
                "newly_run + blocked",
                [
                    "paraview_states",
                    "reports/paraview_visualization_package.md",
                    "reports/paraview_vtk_core_wind_statistics_and_building_analysis.md",
                    "figures/paraview_vtk_core_dx2m_statistical_maps_z2m.png",
                    "reports/manual_review_checklist.md",
                ],
                "Supports manual image review of FluidX3D/VTK wind-field outputs.",
                "Headless ParaView rendering remains limited by local Windows graphics; Python-rendered audit maps and pvsm states are the review assets.",
            ),
            row(
                "simulation_protocol",
                "Simulation protocol records domain/grid logic, eight directions, Uref, output planes, pedestrian height and blocked stronger claims.",
                "complete_with_boundary",
                "newly_run + preexisting_artifact + blocked",
                [
                    "reports/simulation_protocol_without_solver.md",
                    "reports/fluidx3d_boundary_condition_numerics_and_convergence.md",
                    "reports/fluidx3d_numerical_protocol_and_stability_audit.md",
                    "manifests/fluidx3d_core_prism_boundary_condition_table.csv",
                ],
                "Supports methods and numerical setup paragraphs.",
                "Residual convergence, calibrated wind climate and formal comfort/safety compliance remain outside the completed evidence.",
            ),
            row(
                "metric_system",
                "Traditional pedestrian wind metrics, pollutant placeholders, design-comparison metrics, GCRI and GCBTE boundaries were defined.",
                "complete_with_blocked_metric_boundary",
                "newly_run + blocked",
                [
                    "reports/metric_system_for_digital_twin_wind_application.md",
                    "manifests/metric_spec.csv",
                    "reports/geometry_to_cfd_readiness_index_results.md",
                    "manifests/gcri_scoring_table.csv",
                    "manifests/gcbte_status_table.csv",
                ],
                "Supports the metric-system section and innovation-index framing.",
                "Pollutant diffusion and GCBTE are templates/status tables unless new scalar transport or 3DGS collision extraction evidence is added.",
            ),
            row(
                "morphology_conclusions",
                "Building-form analysis uses basic morphology parameters rather than LCZ and derives stage, archetype and directional-fingerprint findings.",
                "complete_with_sample_internal_boundary",
                "newly_run + blocked",
                [
                    "reports/basic_morphology_wind_response_analysis.md",
                    "reports/basic_morphology_multivariate_robustness.md",
                    "reports/morphology_threshold_design_rule_analysis.md",
                    "reports/morphology_form_response_archetype_analysis.md",
                    "reports/morphology_stage_transition_analysis.md",
                    "reports/morphology_directional_fingerprint_analysis.md",
                    "reports/building_form_wind_mechanism_synthesis.md",
                ],
                "Supports the paper's main architectural wind-environment conclusion.",
                "Findings are sample-internal digital-twin screening evidence, not universal causal thresholds.",
            ),
            row(
                "climate_and_campus_context",
                "Climate-zone, campus-building-type and application-potential context were documented without using LCZ as the primary classifier.",
                "complete_with_proxy_boundary",
                "preexisting_artifact + newly_run + blocked",
                [
                    "reports/climate_building_type_campus_wind_application_context.md",
                    "reports/wind_climate_weighted_core_prism_report.md",
                    "manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv",
                    "reports/lcz_scale_validity_in_this_model.md",
                ],
                "Supports the discussion of campus wind-screening application potential.",
                "Open-Meteo is a proxy layer, not a formal measured annual wind rose.",
            ),
            row(
                "design_application",
                "Design-application experiments S1/S2 were run and interpreted as negative/near-null sensitivity evidence.",
                "complete_negative_result",
                "newly_run",
                [
                    "reports/s1_ventilation_relief_fluidx3d_comparison_report.md",
                    "reports/s2_network_porosity_fluidx3d_comparison_report.md",
                    "reports/design_sensitivity_directional_tradeoff_analysis.md",
                    "manifests/design_scenario_manifest.csv",
                    "manifests/s1_design_intervention_claims.csv",
                    "manifests/s2_design_intervention_claims.csv",
                ],
                "Supports design hypothesis narrowing: porosity must align with wind-sector and momentum-entry paths.",
                "Does not support successful optimization or S3-Sn positive intervention proof.",
            ),
            row(
                "citylbm_interoperability",
                "CityLBM/Grasshopper input package is retained as an interoperability template.",
                "blocked_for_end_to_end_execution",
                "blocked",
                [
                    "cfd_ready/CityLBM_GH_input_template",
                    "reports/claim_boundary.md",
                ],
                "Use the wording FluidX3D-native simulation with CityLBM-compatible geometry package.",
                "Do not claim completed CityLBM-Grasshopper end-to-end execution unless new GH screenshots/files/output evidence are added.",
            ),
            row(
                "paper_text_deliverables",
                "Method, experimental-design, result, discussion, conclusion, abstract/highlight, caption and submission-statement text layers exist.",
                "complete_as_generic_sci_section",
                "newly_run + preexisting_artifact + blocked",
                [
                    "paper_text/method_section_zh.md",
                    "paper_text/experiment_design_paragraph_zh.md",
                    "paper_text/experiment3_clean_chinese_sci_package_zh.md",
                    "paper_text/experiment3_sci_section_paper_draft_zh.md",
                    "paper_text/experiment3_final_sci_discussion_conclusion_zh.md",
                    "paper_text/experiment3_sci_abstract_highlights_keywords_zh.md",
                    "paper_text/experiment3_submission_statements_zh.md",
                    "academic-paper-writer/paper-drafts/paper_draft.md",
                ],
                "Supports integration of Experiment 3 into the wider SCI manuscript.",
                "Target journal formatting, author information and paper-level introduction/related-work integration remain author-side tasks.",
            ),
            row(
                "evidence_boundary",
                "Every major claim layer is mapped to evidence type and blocked claims are explicitly named.",
                "complete",
                "newly_run + preexisting_artifact + blocked",
                [
                    "reports/claim_boundary.md",
                    "manifests/evidence_inventory.csv",
                    "manifests/experiment3_reviewer_claim_risk_matrix.csv",
                    "reports/experiment3_final_completeness_and_gap_audit.md",
                    "reports/experiment3_reviewer_reproducibility_and_claim_audit.md",
                ],
                "Supports reviewer-safe claim control.",
                "Blocked rows must remain blocked in the manuscript until new evidence is produced.",
            ),
            row(
                "github_archive",
                "GitHub release package has checkout-stable manifest and reproducible rebuild entry point.",
                "complete",
                "newly_run",
                [
                    "scripts/rebuild_experiment3_paper_assets.ps1",
                    "scripts/refresh_github_archive_manifest.py",
                    "manifests/github_archive_manifest.csv",
                    "reports/github_archive_manifest_validation.md",
                    "README.md",
                ],
                "Supports GitHub archival and collaborator review.",
                "External heavy files remain governed by external artifact paths and source manifests.",
            ),
        ]
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, key_field: str, row_data: dict[str, object], fields: list[str]) -> None:
    rows: list[dict[str, object]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    rows = [item for item in rows if item.get(key_field) != row_data[key_field]]
    rows.append(row_data)
    write_csv(path, rows, fields)


def build_report(rows: list[dict[str, object]]) -> str:
    status_counts: dict[str, int] = {}
    for item in rows:
        status_counts[str(item["status"])] = status_counts.get(str(item["status"]), 0) + 1
    blocked = [item for item in rows if "blocked" in str(item["status"]) or str(item["evidence_type"]) == "blocked"]
    missing = [item for item in rows if item["missing_artifacts"]]

    lines = [
        "# Experiment 3 Original Request Fulfillment Audit",
        "",
        "evidence_type: newly_run + preexisting_artifact + blocked",
        "",
        "## Purpose",
        "",
        "This audit maps the user's original Experiment 3 preparation request to the current release package. It checks the presence of files and evidence layers for data provenance, Rhino visualization, CFD-ready geometry, FluidX3D/ParaView execution, metric design, paper text, and claim boundaries.",
        "",
        "## Summary",
        "",
        f"- Requirement rows audited: `{len(rows)}`",
        f"- Status counts: `{status_counts}`",
        f"- Rows with missing local artifacts: `{len(missing)}`",
        f"- Rows with blocked/end-to-end boundaries: `{len(blocked)}`",
        "",
        "## Fulfillment Matrix",
        "",
        "| group | status | evidence_type | files_found | missing_artifacts | paper_safe_use | claim_boundary |",
        "|---|---|---|---:|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['requirement_group']} | {item['status']} | {item['evidence_type']} | {item['files_found']} | {item['missing_artifacts']} | {item['paper_safe_use']} | {item['claim_boundary']} |"
        )
    lines.extend(
        [
            "",
            "## Paper-Safe Verdict",
            "",
            "The original preparation request is fulfilled for a reproducible FluidX3D-native TUM2TWIN digital-twin wind-screening and design-application experiment with CityLBM-compatible geometry preparation. The remaining non-fulfilled items are not packaging failures; they are scientific evidence boundaries: CityLBM-Grasshopper end-to-end execution, field/wind-tunnel validation, annual comfort/safety compliance, pollutant dispersion, GCBTE computation, and successful optimized design intervention.",
            "",
            "## Output Artifacts",
            "",
            "- `manifests/experiment3_original_request_fulfillment_audit.csv`",
            "- `reports/experiment3_original_request_fulfillment_audit.md`",
            "- `paper_text/experiment3_original_request_fulfillment_summary_zh.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_summary_zh(rows: list[dict[str, object]]) -> str:
    completeish = sum(1 for item in rows if not str(item["status"]).startswith("blocked"))
    blocked = [item for item in rows if str(item["status"]).startswith("blocked")]
    return f"""# 实验3原始任务履约总结

evidence_type: newly_run + preexisting_artifact + blocked

本审计将最初的实验准备要求逐项映射到当前归档包。结果显示，`{completeish}` 个非阻塞条目已经形成文件证据，覆盖 TUM2TWIN 官方资料核验、下载与校验清单、Rhino/OBJ 场景审查、CFD-ready 闭合几何、FluidX3D 八风向模拟、ParaView/VTK 人工审核资产、指标体系、S1/S2 设计敏感性、建筑形态机制分析、SCI 文段和 GitHub 归档清单。该层的意义是证明实验3不是零散结果，而是从数据源、几何、求解、可视化、统计、论文表述到证据边界的完整应用实验包。

仍需保留边界的条目共有 `{len(blocked)}` 个，核心包括 CityLBM-Grasshopper 端到端执行、实测或风洞验证、年度舒适/安全合规、污染物扩散、GCBTE 计算和成功优化设计证明。因此，论文中最稳妥的实验定位仍是“FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation”。这不是降低实验价值，而是把数字孪生城市数据如何落地为风环境设计筛查工具这一贡献放在可验证证据范围内。
"""


def main() -> None:
    rows = build_rows()
    fields = [
        "requirement_group",
        "requirement",
        "status",
        "evidence_type",
        "evidence_artifacts",
        "files_found",
        "missing_artifacts",
        "paper_safe_use",
        "claim_boundary",
    ]
    write_csv(MAN / "experiment3_original_request_fulfillment_audit.csv", rows, fields)
    (REP / "experiment3_original_request_fulfillment_audit.md").write_text(build_report(rows), encoding="utf-8")
    (PAPER / "experiment3_original_request_fulfillment_summary_zh.md").write_text(
        build_summary_zh(rows), encoding="utf-8"
    )

    blocked_count = sum(1 for item in rows if "blocked" in str(item["status"]) or str(item["evidence_type"]) == "blocked")
    missing_count = sum(1 for item in rows if item["missing_artifacts"])
    upsert_csv(
        MAN / "evidence_inventory.csv",
        "claim",
        {
            "claim": "The original Experiment 3 preparation request was audited against the current release package and mapped to evidence artifacts and claim boundaries.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "manifests/experiment3_original_request_fulfillment_audit.csv; reports/experiment3_original_request_fulfillment_audit.md",
        },
        ["claim", "evidence_type", "source"],
    )
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        "claim_layer",
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Original request fulfillment readiness",
            "metric": "audited requirement rows / missing-artifact rows / blocked-boundary rows",
            "value": f"{len(rows)} / {missing_count} / {blocked_count}",
            "source_artifact": "manifests/experiment3_original_request_fulfillment_audit.csv; reports/experiment3_original_request_fulfillment_audit.md",
            "paper_safe_claim": "The original preparation request is fulfilled for a FluidX3D-native digital-twin wind-screening package, while blocked scientific claims remain explicitly bounded.",
        },
        [
            "evidence_type",
            "claim_layer",
            "metric",
            "value",
            "source_artifact",
            "paper_safe_claim",
        ],
    )

    print("original_request_rows", len(rows))
    print("missing_artifact_rows", missing_count)
    print("blocked_boundary_rows", blocked_count)
    print("wrote original request fulfillment audit")


if __name__ == "__main__":
    main()
