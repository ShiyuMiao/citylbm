#!/usr/bin/env python3
"""Smoke-test native inlet precondition field propagation into metrics CSV."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_native_inlet_metrics_") as tmp:
        work = Path(tmp)
        official = work / "official.csv"
        probe = work / "probe.csv"
        read_vtk_audit = work / "read_vtk_audit.json"
        inlet_source_audit = work / "inlet_source_audit.json"
        native_audit = work / "native_preconditions_audit.json"
        metrics = work / "metrics.csv"

        write_csv(
            official,
            [
                {
                    "case": "AIJ_CaseA",
                    "wind_direction": "N",
                    "No.": "1",
                    "Velocity_Ratio": "1.0",
                    "x": "0.0",
                    "y": "0.0",
                    "z": "2.0",
                }
            ],
        )
        write_csv(
            probe,
            [
                {
                    "probe_id": "1",
                    "compared_value": "0.9",
                    "failed": "false",
                    "validation_status": "pass",
                    "inside_vtk_grid_extent": "true",
                    "x": "0.0",
                    "y": "0.0",
                    "z": "2.0",
                    "nearest_distance": "0.1",
                    "normalization_valid": "true",
                    "wind_direction_valid": "true",
                    "Uref": "1.0",
                    "compared_component": "speed_ratio",
                    "tolerance": "0.5",
                    "vtk_source_time_steps": "1000;2000;3000",
                    "vtk_source_step_span": "2000",
                    "minimum_validation_average_step_span": "2000",
                    "vtk_source_sha256": "a;b;c",
                }
            ],
        )
        read_vtk_audit.write_text(
            json.dumps(
                {
                    "final_window_stationarity_gate": "diagnostic_only",
                    "final_window_stationarity_gate_reasons_csv": (
                        "final_window_mean_speed_drift_above_threshold"
                    ),
                    "final_window_mean_speed_drift_ratio": 0.12,
                    "max_final_window_mean_speed_drift_ratio": 0.18,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        inlet_source_audit.write_text(
            json.dumps(
                {
                    "inlet_source_gate": "pass",
                    "inlet_source_gate_reasons": [
                        "inlet_source_consistent_with_declared_metadata",
                    ],
                    "paper_grade_inlet_source_gate": "fail",
                    "paper_grade_inlet_source_gate_reasons": [
                        "source_velocity_field_only",
                    ],
                    "inlet_source_method_class": "stg_lite_correlated_velocity_field_only",
                    "inlet_source_distribution_consistent": False,
                    "inlet_source_velocity_field_only": True,
                    "defines_hpp": "run/defines.hpp",
                    "defines_hpp_sha256": "ABC123",
                    "defines_hpp_audited": True,
                    "has_equilibrium_boundaries_define": True,
                    "has_type_e_equilibrium_boundary_route": True,
                    "inlet_distribution_route": "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u",
                    "inlet_distribution_route_gate": "pass",
                    "has_streamwise_clipping_control": True,
                    "has_component_phase_decorrelation": True,
                    "has_temporal_filter_state": True,
                    "streamwise_min_fraction": 0.0,
                    "streamwise_clipping_enabled": False,
                    "has_legacy_hardcoded_streamwise_clipping": False,
                    "recommended_next_action": "Use source evidence plus final-window VTK inlet profile/correlation audits.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        native_audit.write_text(
            json.dumps(
                {
                    "native_preconditions_gate": "fail",
                    "native_preconditions_time_average_gate": "fail",
                    "strict_native_run_gate": "fail",
                    "strict_native_run_gate_reasons_csv": (
                        "time_averaging_gate_not_pass:diagnostic_only;"
                        "final_window_stationarity_gate_not_pass:diagnostic_only"
                    ),
                    "native_preconditions_time_average_evidence_gate": "fail",
                    "native_preconditions_time_average_evidence_gate_reasons_csv": (
                        "runtime_average_window_frame_count_4_below_minimum_40;"
                        "runtime_final_window_stationarity_gate_not_pass:diagnostic_only"
                    ),
                    "runtime_source_frame_count": 4,
                    "runtime_source_vtk_sha256_count": 4,
                    "runtime_source_vtk_sha256_unique_count": 4,
                    "runtime_final_window_frame_count_gate": "fail",
                    "runtime_final_window_frame_count_gate_reasons_csv": (
                        "runtime_average_window_frame_count_4_below_minimum_40;"
                        "runtime_source_frame_count_4_below_minimum_40;"
                        "runtime_source_vtk_sha256_count_4_below_minimum_40"
                    ),
                    "planned_synthetic_inlet_sampling_gate": "diagnostic_only",
                    "planned_synthetic_inlet_sampling_gate_reasons_csv": (
                        "planned_stg_refresh_count_40_below_minimum_200"
                    ),
                    "planned_synthetic_inlet_sampling_active": True,
                    "planned_synthetic_inlet_update_interval": 100,
                    "planned_synthetic_inlet_final_window_step_span": 4000,
                    "planned_synthetic_inlet_refresh_count": 40,
                    "planned_synthetic_inlet_metadata_expected_refresh_count": 390,
                    "planned_synthetic_inlet_minimum_refresh_count": 200,
                    "native_boundary_equivalence_gate": "fail",
                    "native_boundary_equivalence_gate_reasons_csv": (
                        "boundary_source_simplified_not_false:True;"
                        "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail"
                    ),
                    "boundary_source_gate": "fail",
                    "paper_grade_boundary_source_gate": "fail",
                    "boundary_source_method_class": "simplified_type_e_box",
                    "boundary_source_wind_tunnel_equivalent": False,
                    "boundary_source_simplified": True,
                    "boundary_source_setup_cpp_sha256_matches_current": False,
                    "boundary_source_missing_paper_grade_source_evidence_csv": (
                        "non_reflecting_or_validated_outlet_state;"
                        "side_top_boundary_pair_mapping;"
                        "rough_wall_or_wall_function_action;"
                        "precursor_or_recycling_development_field"
                    ),
                    "boundary_source_has_paper_grade_outlet_source": False,
                    "boundary_source_has_paper_grade_side_top_source": False,
                    "boundary_source_has_paper_grade_rough_wall_source": False,
                    "boundary_source_has_paper_grade_development_source": False,
                    "boundary_source_has_non_reflecting_outlet_method": False,
                    "boundary_source_has_non_reflecting_outlet_state_evidence": False,
                    "boundary_source_has_periodic_side_top_method": False,
                    "boundary_source_has_periodic_pair_mapping_evidence": False,
                    "boundary_source_has_rough_wall_function_method": False,
                    "boundary_source_has_rough_wall_parameter_evidence": False,
                    "boundary_source_has_rough_wall_action_evidence": False,
                    "boundary_source_has_precursor_or_recycling_boundary_method": False,
                    "boundary_source_has_precursor_or_recycling_boundary_field_evidence": False,
                    "boundary_runtime_source_time_steps_match_runtime": False,
                    "boundary_runtime_source_steps_strictly_increasing": True,
                    "boundary_runtime_source_step_spacing_uniform": True,
                    "boundary_runtime_source_vtk_sha256_match_runtime": False,
                    "boundary_runtime_source_step_hash_pairs_match_runtime": False,
                    "native_inlet_equivalence_gate": "fail",
                    "native_inlet_equivalence_gate_reasons_csv": (
                        "inlet_source_velocity_field_only_not_false:True;"
                        "inlet_tke_gate_not_pass:fail"
                    ),
                    "native_probe_component_equivalence_gate": "fail",
                    "native_probe_component_equivalence_gate_reasons_csv": (
                        "probe_uref_mismatch_count_80;"
                        "normalization_scale_gate_not_pass:fail"
                    ),
                    "probe_official_height_gate": "fail",
                    "probe_official_height_gate_reasons_csv": "official_z_mismatch_count:80",
                    "component_source_time_steps_match_runtime": False,
                    "component_source_steps_strictly_increasing": True,
                    "component_source_step_spacing_uniform": True,
                    "component_source_vtk_sha256_match_runtime": False,
                    "component_normalization_gate": "fail",
                    "component_sensitivity_gate": "pass",
                    "component_sensitivity_gate_reasons_csv": "selected_component_not_worse_than_alternatives",
                    "normalization_scale_gate": "fail",
                    "normalization_scale_gate_reasons_csv": (
                        "best_fit_scale_1.25_suggests_uref_or_unit_error"
                    ),
                    "component_selected_component": "speed_ratio",
                    "component_selected_component_source": "valid_probe_rows",
                    "component_best_component_by_rmse": "speed_ratio",
                    "component_official_probe_coverage_ratio": 1.0,
                    "component_selected_component_rmse": 0.21,
                    "component_selected_component_bias": -0.18,
                    "component_selected_component_scaled_bias": -0.03,
                    "component_selected_component_bias_abs_reduction_ratio": 0.8333333333,
                    "component_selected_component_mean_sim": 0.72,
                    "component_selected_component_mean_exp": 0.90,
                    "component_selected_component_mean_sim_to_exp_ratio": 0.8,
                    "component_best_component_rmse": 0.21,
                    "component_rmse_improvement_ratio": 0.0,
                    "component_normalization_best_fit_scale": 1.25,
                    "component_normalization_scaled_improvement_ratio": 0.42,
                    "expected_uref_mps": 3.93,
                    "actual_uref_mps": 3.90,
                    "expected_zref_m": 15.9,
                    "af_uref_at_zref_mps": 3.928296,
                    "uref_af_profile_delta_mps": 0.001704,
                    "metadata_uref_af_profile_delta_mps": 0.028296,
                    "runtime_final_window_stationarity_gate": "diagnostic_only",
                    "runtime_final_window_stationarity_gate_reasons_csv": (
                        "final_window_mean_speed_drift_above_threshold"
                    ),
                    "runtime_final_window_mean_speed_drift_ratio": 0.12,
                    "runtime_max_final_window_mean_speed_drift_ratio": 0.18,
                    "inlet_profile_audit": "run/inlet_profile_audit.json",
                    "inlet_profile_gate": "FAIL",
                    "inlet_u_profile_gate": "PASS",
                    "inlet_k_profile_gate": "FAIL",
                    "inlet_profile_time_averaging_gate": "FAIL",
                    "inlet_profile_af_csv_sha256_matches_expected": False,
                    "inlet_profile_source_time_steps_match_runtime": True,
                    "inlet_profile_source_vtk_sha256_match_runtime": False,
                    "inlet_profile_source_step_hash_pairs_match_runtime": False,
                    "inlet_profile_source_step_span": 2000,
                    "inlet_profile_minimum_step_span": 20000,
                    "inlet_correlation_audit": "run/inlet_correlation_audit.json",
                    "inlet_correlation_gate": "FAIL",
                    "inlet_k_variance_gate": "FAIL",
                    "inlet_streamwise_variance_target_from_k": 0.42,
                    "inlet_streamwise_variance_to_k_ratio": 0.31,
                    "inlet_tke_gate": "FAIL",
                    "inlet_tke_target_from_af_k": 0.63,
                    "inlet_tke_to_k_ratio": 0.22,
                    "inlet_mean_turbulent_kinetic_energy_from_components": 0.14,
                    "inlet_correlation_source_time_steps_match_runtime": True,
                    "inlet_correlation_source_vtk_sha256_match_runtime": False,
                    "inlet_correlation_source_step_hash_pairs_match_runtime": False,
                    "inlet_correlation_source_step_span": 2000,
                    "inlet_correlation_minimum_step_span": 20000,
                    "native_precondition_closure_gate": "fail",
                    "native_precondition_closed_stage_count": 2,
                    "native_precondition_failed_stage_count": 4,
                    "native_precondition_failed_stage_keys": [
                        "turbulent_inlet_method_and_u_k_preservation",
                        "time_averaging_stationarity",
                    ],
                    "native_precondition_top_blocking_stage_key": "turbulent_inlet_method_and_u_k_preservation",
                    "native_precondition_top_blocking_stage_rank": 1,
                    "native_precondition_top_blocking_stage_reason_count": 2,
                    "native_precondition_top_blocking_stage_reasons": [
                        "inlet_k_profile_gate_not_pass",
                        "inlet_correlation_gate_not_pass",
                    ],
                    "inlet_source_has_mean_preserving_inlet_correction": True,
                    "inlet_source_has_layerwise_mean_preserving_inlet_correction": True,
                    "inlet_source_has_component_phase_decorrelation": True,
                    "inlet_source_has_temporal_filter_state": True,
                    "inlet_source_method_class": "stg_lite_velocity_field_only",
                    "inlet_synthetic_correlation_model": "uncorrelated_random_rms_velocity_field_only",
                    "inlet_source_distribution_route": "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u",
                    "inlet_source_distribution_route_gate": "pass",
                    "inlet_source_has_equilibrium_boundaries_define": True,
                    "inlet_source_has_type_e_equilibrium_boundary_route": True,
                    "inlet_source_has_streamwise_clipping_control": True,
                    "inlet_source_streamwise_min_fraction": 0.0,
                    "inlet_source_streamwise_clipping_enabled": False,
                    "inlet_source_has_legacy_hardcoded_streamwise_clipping": False,
                    "inlet_source_has_uncorrelated_random_inlet": True,
                    "inlet_source_uncorrelated_random_patterns_csv": r"\bstd\s*::\s*mt19937\b",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        command = [
            sys.executable,
            str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
            "--probe-audit",
            str(probe),
            "--official",
            str(official),
            "--out",
            str(metrics),
            "--case",
            "AIJ_CaseA",
            "--wind-direction",
            "N",
            "--source-time-steps",
            "1000;2000;3000",
            "--read-vtk-audit",
            str(read_vtk_audit),
            "--inlet-source-audit",
            str(inlet_source_audit),
            "--native-preconditions-audit",
            str(native_audit),
        ]
        subprocess.run(command, cwd=str(REPO), check=True)

        with metrics.open("r", encoding="utf-8", newline="") as handle:
            row = next(csv.DictReader(handle))

    expected = {
        "official_probe_height_gate": "not_recorded_or_fail",
        "official_probe_height_gate_reasons": (
            "official_expected_z_missing;"
            "official_z_match_count_missing;"
            "official_z_mismatch_count_missing"
        ),
        "native_inlet_profile_audit": "run/inlet_profile_audit.json",
        "native_inlet_profile_gate": "fail",
        "native_inlet_u_profile_gate": "pass",
        "native_inlet_k_profile_gate": "fail",
        "native_inlet_profile_time_averaging_gate": "fail",
        "native_inlet_profile_af_csv_sha256_matches_expected": "false",
        "native_inlet_profile_source_time_steps_match_runtime": "true",
        "native_inlet_profile_source_vtk_sha256_match_runtime": "false",
        "native_inlet_profile_source_step_hash_pairs_match_runtime": "false",
        "native_inlet_profile_source_step_span": "2000",
        "native_inlet_profile_minimum_step_span": "20000",
        "native_inlet_correlation_audit": "run/inlet_correlation_audit.json",
        "native_inlet_correlation_gate": "fail",
        "native_inlet_k_variance_gate": "fail",
        "native_inlet_streamwise_variance_target_from_k": "0.42",
        "native_inlet_streamwise_variance_to_k_ratio": "0.31",
        "native_inlet_tke_gate": "fail",
        "native_inlet_tke_target_from_af_k": "0.63",
        "native_inlet_tke_to_k_ratio": "0.22",
        "native_inlet_mean_turbulent_kinetic_energy_from_components": "0.14",
        "native_inlet_correlation_source_time_steps_match_runtime": "true",
        "native_inlet_correlation_source_vtk_sha256_match_runtime": "false",
        "native_inlet_correlation_source_step_hash_pairs_match_runtime": "false",
        "native_inlet_correlation_source_step_span": "2000",
        "native_inlet_correlation_minimum_step_span": "20000",
        "native_preconditions_time_average_evidence_gate": "fail",
        "native_preconditions_time_average_evidence_gate_reasons": (
            "runtime_average_window_frame_count_4_below_minimum_40;"
            "runtime_final_window_stationarity_gate_not_pass:diagnostic_only"
        ),
        "native_preconditions_runtime_source_frame_count": "4",
        "native_preconditions_runtime_source_vtk_sha256_count": "4",
        "native_preconditions_runtime_source_vtk_sha256_unique_count": "4",
        "native_preconditions_runtime_final_window_frame_count_gate": "fail",
        "native_preconditions_runtime_final_window_frame_count_gate_reasons": (
            "runtime_average_window_frame_count_4_below_minimum_40;"
            "runtime_source_frame_count_4_below_minimum_40;"
            "runtime_source_vtk_sha256_count_4_below_minimum_40"
        ),
        "native_preconditions_planned_synthetic_inlet_sampling_gate": "diagnostic_only",
        "native_preconditions_planned_synthetic_inlet_sampling_gate_reasons": (
            "planned_stg_refresh_count_40_below_minimum_200"
        ),
        "native_preconditions_planned_synthetic_inlet_sampling_active": "true",
        "native_preconditions_planned_synthetic_inlet_update_interval": "100",
        "native_preconditions_planned_synthetic_inlet_final_window_step_span": "4000",
        "native_preconditions_planned_synthetic_inlet_refresh_count": "40",
        "native_preconditions_planned_synthetic_inlet_metadata_expected_refresh_count": "390",
        "native_preconditions_planned_synthetic_inlet_minimum_refresh_count": "200",
        "native_boundary_equivalence_gate": "fail",
        "native_boundary_equivalence_gate_reasons": (
            "boundary_source_simplified_not_false:True;"
            "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail"
        ),
        "native_boundary_source_gate": "fail",
        "native_paper_grade_boundary_source_gate": "fail",
        "native_boundary_source_method_class": "simplified_type_e_box",
        "native_boundary_source_wind_tunnel_equivalent": "false",
        "native_boundary_source_simplified": "true",
        "native_boundary_source_setup_cpp_sha256_matches_current": "false",
        "native_boundary_source_missing_paper_grade_source_evidence": (
            "non_reflecting_or_validated_outlet_state;"
            "side_top_boundary_pair_mapping;"
            "rough_wall_or_wall_function_action;"
            "precursor_or_recycling_development_field"
        ),
        "native_boundary_source_has_paper_grade_outlet_source": "false",
        "native_boundary_source_has_paper_grade_side_top_source": "false",
        "native_boundary_source_has_paper_grade_rough_wall_source": "false",
        "native_boundary_source_has_paper_grade_development_source": "false",
        "native_boundary_source_has_non_reflecting_outlet_method": "false",
        "native_boundary_source_has_non_reflecting_outlet_state_evidence": "false",
        "native_boundary_source_has_periodic_side_top_method": "false",
        "native_boundary_source_has_periodic_pair_mapping_evidence": "false",
        "native_boundary_source_has_rough_wall_function_method": "false",
        "native_boundary_source_has_rough_wall_parameter_evidence": "false",
        "native_boundary_source_has_rough_wall_action_evidence": "false",
        "native_boundary_source_has_precursor_or_recycling_boundary_method": "false",
        "native_boundary_source_has_precursor_or_recycling_boundary_field_evidence": "false",
        "native_boundary_runtime_source_time_steps_match_runtime": "false",
        "native_boundary_runtime_source_steps_strictly_increasing": "true",
        "native_boundary_runtime_source_step_spacing_uniform": "true",
        "native_boundary_runtime_source_vtk_sha256_match_runtime": "false",
        "native_boundary_runtime_source_step_hash_pairs_match_runtime": "false",
        "native_inlet_equivalence_gate": "fail",
        "native_inlet_equivalence_gate_reasons": (
            "inlet_source_velocity_field_only_not_false:True;"
            "inlet_tke_gate_not_pass:fail"
        ),
        "native_probe_component_equivalence_gate": "fail",
        "native_probe_component_equivalence_gate_reasons": (
            "probe_uref_mismatch_count_80;"
            "normalization_scale_gate_not_pass:fail"
        ),
        "native_probe_official_height_gate": "fail",
        "native_probe_official_height_gate_reasons": "official_z_mismatch_count:80",
        "native_probe_component_source_time_steps_match_runtime": "false",
        "native_probe_component_source_steps_strictly_increasing": "true",
        "native_probe_component_source_step_spacing_uniform": "true",
        "native_probe_component_source_vtk_sha256_match_runtime": "false",
        "native_component_normalization_gate": "fail",
        "native_component_sensitivity_gate": "pass",
        "native_component_sensitivity_gate_reasons": "selected_component_not_worse_than_alternatives",
        "native_component_normalization_scale_gate": "fail",
        "native_component_normalization_scale_gate_reasons": (
            "best_fit_scale_1.25_suggests_uref_or_unit_error"
        ),
        "native_component_selected_component": "speed_ratio",
        "native_component_selected_component_source": "valid_probe_rows",
        "native_component_best_component_by_rmse": "speed_ratio",
        "native_component_official_probe_coverage_ratio": "1",
        "native_component_selected_component_rmse_ratio": "0.21",
        "native_component_selected_component_bias_ratio": "-0.18",
        "native_component_selected_component_scaled_bias_ratio": "-0.03",
        "native_component_selected_component_bias_abs_reduction_ratio": "0.8333333333",
        "native_component_selected_component_mean_sim_ratio": "0.72",
        "native_component_selected_component_mean_exp_ratio": "0.9",
        "native_component_selected_component_mean_sim_to_exp_ratio": "0.8",
        "native_component_best_component_rmse_ratio": "0.21",
        "native_component_rmse_improvement_ratio": "0",
        "native_component_normalization_best_fit_scale": "1.25",
        "native_component_normalization_scaled_improvement_ratio": "0.42",
        "native_preconditions_expected_uref_mps": "3.93",
        "native_preconditions_actual_uref_mps": "3.9",
        "native_preconditions_expected_zref_m": "15.9",
        "native_preconditions_af_uref_at_zref_mps": "3.928296",
        "native_preconditions_uref_af_profile_delta_mps": "0.001704",
        "native_preconditions_metadata_uref_af_profile_delta_mps": "0.028296",
        "native_preconditions_strict_native_run_gate": "fail",
        "native_preconditions_strict_native_run_gate_reasons": (
            "time_averaging_gate_not_pass:diagnostic_only;"
            "final_window_stationarity_gate_not_pass:diagnostic_only"
        ),
        "final_window_stationarity_gate": "diagnostic_only",
        "final_window_stationarity_gate_reasons": "final_window_mean_speed_drift_above_threshold",
        "final_window_mean_speed_drift_ratio": "0.12",
        "max_final_window_mean_speed_drift_ratio": "0.18",
        "native_preconditions_runtime_final_window_stationarity_gate": "diagnostic_only",
        "native_preconditions_runtime_final_window_stationarity_gate_reasons": (
            "final_window_mean_speed_drift_above_threshold"
        ),
        "native_preconditions_runtime_final_window_mean_speed_drift_ratio": "0.12",
        "native_preconditions_runtime_max_final_window_mean_speed_drift_ratio": "0.18",
        "native_precondition_closure_gate": "fail",
        "native_precondition_closed_stage_count": "2",
        "native_precondition_failed_stage_count": "4",
        "native_precondition_failed_stage_keys": "turbulent_inlet_method_and_u_k_preservation;time_averaging_stationarity",
        "native_precondition_top_blocking_stage_key": "turbulent_inlet_method_and_u_k_preservation",
        "native_precondition_top_blocking_stage_rank": "1",
        "native_precondition_top_blocking_stage_reason_count": "2",
        "native_precondition_top_blocking_stage_reasons": "inlet_k_profile_gate_not_pass;inlet_correlation_gate_not_pass",
        "inlet_source_defines_hpp": "run/defines.hpp",
        "inlet_source_defines_hpp_sha256": "ABC123",
        "inlet_source_defines_hpp_audited": "true",
        "inlet_source_has_equilibrium_boundaries_define": "true",
        "inlet_source_has_type_e_equilibrium_boundary_route": "true",
        "inlet_source_distribution_route": "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u",
        "inlet_source_distribution_route_gate": "pass",
        "native_inlet_source_distribution_route": "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u",
        "native_inlet_source_distribution_route_gate": "pass",
        "native_inlet_source_method_class": "stg_lite_velocity_field_only",
        "native_inlet_source_correlation_model": "uncorrelated_random_rms_velocity_field_only",
        "native_inlet_source_has_equilibrium_boundaries_define": "true",
        "native_inlet_source_has_type_e_equilibrium_boundary_route": "true",
        "native_inlet_source_has_mean_preserving_inlet_correction": "true",
        "native_inlet_source_has_layerwise_mean_preserving_inlet_correction": "true",
        "native_inlet_source_has_component_phase_decorrelation": "true",
        "native_inlet_source_has_temporal_filter_state": "true",
        "native_inlet_source_has_streamwise_clipping_control": "true",
        "native_inlet_source_streamwise_min_fraction": "0.0",
        "native_inlet_source_streamwise_clipping_enabled": "false",
        "native_inlet_source_has_legacy_hardcoded_streamwise_clipping": "false",
        "native_inlet_source_has_uncorrelated_random_inlet": "true",
        "native_inlet_source_uncorrelated_random_patterns": r"\bstd\s*::\s*mt19937\b",
        "inlet_source_has_streamwise_clipping_control": "true",
        "inlet_source_has_temporal_filter_state": "true",
        "inlet_source_streamwise_min_fraction": "0.0",
        "inlet_source_streamwise_clipping_enabled": "false",
        "inlet_source_has_legacy_hardcoded_streamwise_clipping": "false",
        "synthetic_min_streamwise_fraction": "0.0",
        "synthetic_streamwise_clipping_enabled": "false",
        "synthetic_legacy_hardcoded_streamwise_clipping": "false",
    }
    for field, value in expected.items():
        if row.get(field) != value:
            raise AssertionError(f"{field}: expected {value!r}, got {row.get(field)!r}")

    print("native_inlet_metrics_fields_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
