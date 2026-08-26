#!/usr/bin/env python3
"""Audit whether a CityLBM validation row is comparable to a native FluidX3D row.

The script does not run CFD. It checks that the two archived metrics rows use
the same case, wind direction, grid, averaging, normalization, probe component
and core solver/boundary/inlet settings before a CityLBM result is interpreted
as inheriting native FluidX3D accuracy.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


TEXT_FIELDS = [
    "case",
    "wind_direction",
    "compared_component",
    "velocity_component",
    "compared_component_unique_values",
    "probe_component_fidelity_class",
    "probe_id_field",
    "probe_vtk_source_time_steps",
    "component_sensitivity_case",
    "component_sensitivity_wind_direction",
    "component_source_time_steps",
    "best_component_by_rmse",
    "probe_uref_values",
    "official_probe_ids_unique",
    "wind_vector",
    "inlet_face",
    "outlet_face",
    "lateral_faces",
    "time_averaging_fidelity_class",
    "requested_vtk_expected_final_window_time_steps",
    "source_time_steps",
    "selected_last_window",
    "source_steps_strictly_increasing",
    "source_step_spacing_uniform",
    "mean_speed_statistics_source",
    "velocity_set",
    "les_model",
    "synthetic_inlet_method",
    "inlet_distribution_treatment",
    "inlet_method_class",
    "inlet_source_method_class",
    "inlet_source_turbulent_inflow_fidelity_class",
    "inlet_source_distribution_consistent",
    "inlet_source_velocity_field_only",
    "inlet_source_requires_distribution_reconstruction",
    "inlet_source_correlation_model",
    "inlet_synthetic_correlation_model",
    "inlet_source_distribution_route",
    "inlet_source_reynolds_stress_treatment",
    "inlet_source_has_reynolds_stress_tensor_metadata_claim",
    "inlet_source_has_reynolds_stress_diagonal_source_evidence",
    "inlet_source_has_reynolds_stress_offdiagonal_source_evidence",
    "inlet_source_has_reynolds_stress_full_tensor_source_evidence",
    "inlet_source_has_reynolds_stress_diagonal_usage_evidence",
    "inlet_source_has_reynolds_stress_offdiagonal_usage_evidence",
    "inlet_source_has_reynolds_stress_full_tensor_usage_evidence",
    "inlet_source_has_sem_eddy_update_evidence",
    "inlet_source_has_sem_eddy_velocity_coupling_evidence",
    "inlet_source_has_three_component_velocity_write",
    "inlet_source_has_three_component_fluctuation_evidence",
    "inlet_source_has_k_driven_three_component_stg",
    "inlet_source_has_component_phase_decorrelation",
    "inlet_source_has_source_length_scale_evidence",
    "inlet_source_has_metadata_length_scale_evidence",
    "inlet_source_length_scale_evidence_basis",
    "inlet_source_has_temporal_filter_state",
    "inlet_source_has_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_rms_preserving_inlet_correction",
    "inlet_source_has_streamwise_clipping_control",
    "inlet_source_streamwise_clipping_enabled",
    "inlet_source_has_legacy_hardcoded_streamwise_clipping",
    "inlet_source_has_uncorrelated_random_inlet",
    "inlet_source_has_correlated_velocity_field_only",
    "inlet_source_has_uncorrelated_rms_velocity_field_only",
    "inlet_source_has_rms_k_velocity_surrogate",
    "inlet_source_rms_k_surrogate_reasons",
    "runtime_inlet_diagnostics_evidence_required",
    "runtime_inlet_diagnostics_evidence_required_basis_csv",
    "runtime_inlet_diagnostics_selected_steps_csv",
    "runtime_inlet_diagnostics_steps_cover_runtime_window",
    "wall_roughness_treatment",
    "boundary_equivalence_basis",
    "boundary_equivalence_supported",
    "boundary_evidence_class",
    "boundary_evidence_files_all_exist",
    "boundary_evidence_files_all_hashed",
    "boundary_condition_fields_supported",
    "boundary_condition_support_reasons",
    "inlet_boundary_supported",
    "outlet_boundary_supported",
    "lateral_boundary_supported",
    "top_boundary_supported",
    "ground_wall_treatment_supported",
    "roughness_treatment_supported",
    "floor_roughness_source_supported",
    "blockage_source_supported",
    "fetch_clearance_source_supported",
    "outlet_reflection_check_supported",
    "side_top_boundary_check_supported",
    "boundary_clearance_reasons",
    "boundary_source_method_class",
    "boundary_source_fidelity_class",
    "boundary_source_has_complete_wind_tunnel_evidence",
    "boundary_source_has_empty_advanced_method_stub_only",
    "boundary_source_wind_tunnel_equivalent",
    "boundary_source_simplified",
    "boundary_source_missing_paper_grade_source_evidence",
    "boundary_source_has_paper_grade_outlet_source",
    "boundary_source_has_paper_grade_side_top_source",
    "boundary_source_has_paper_grade_rough_wall_source",
    "boundary_source_has_paper_grade_development_source",
    "boundary_source_has_non_reflecting_outlet_method",
    "boundary_source_has_non_reflecting_outlet_state_evidence",
    "boundary_source_has_periodic_side_top_method",
    "boundary_source_has_periodic_pair_mapping_evidence",
    "boundary_source_has_rough_wall_function_method",
    "boundary_source_has_rough_wall_parameter_evidence",
    "boundary_source_has_rough_wall_action_evidence",
    "boundary_source_has_precursor_or_recycling_boundary_method",
    "boundary_source_has_precursor_or_recycling_boundary_field_evidence",
    "boundary_runtime_source_time_steps_csv",
    "boundary_runtime_source_time_steps_match_runtime",
    "boundary_runtime_source_vtk_sha256_match_runtime",
    "boundary_runtime_source_step_hash_pairs_match_runtime",
    "native_probe_component_fidelity_class",
    "native_probe_compared_component_values",
    "native_probe_expected_compared_component",
    "native_probe_official_coordinate_delta_source",
    "native_probe_component_source_time_steps_match_runtime",
    "native_probe_component_source_steps_strictly_increasing",
    "native_probe_component_source_step_spacing_uniform",
    "native_probe_component_source_vtk_sha256_match_runtime",
    "native_probe_source_step_hash_pairs_match_runtime",
    "native_probe_component_source_step_hash_pairs_match_runtime",
    "native_preconditions_time_averaging_fidelity_class",
    "native_preconditions_time_averaging_evidence_schema",
    "native_preconditions_time_averaging_evidence_bound",
    "native_preconditions_time_averaging_evidence_selected_steps",
    "native_preconditions_runtime_selected_last_window",
    "native_preconditions_runtime_mean_speed_statistics_source",
    "native_preconditions_runtime_mean_speed_statistics_cli_override",
]

GATE_FIELDS = [
    "native_preconditions_strict_native_run_gate",
    "requested_vtk_frame_gate",
    "run_freshness_gate",
    "time_averaging_gate",
    "final_window_stationarity_gate",
    "native_preconditions_time_average_gate",
    "native_preconditions_time_average_evidence_gate",
    "native_preconditions_time_averaging_evidence_file_gate",
    "native_preconditions_time_averaging_evidence_gate",
    "native_preconditions_time_averaging_evidence_actual_vtk_output_gate",
    "native_preconditions_runtime_final_window_frame_count_gate",
    "native_preconditions_runtime_final_window_stationarity_gate",
    "lbm_stability_gate",
    "normalization_valid",
    "compared_component_consistency_gate",
    "wind_direction_valid",
    "blockage_protocol_gate",
    "boundary_protocol_gate",
    "boundary_evidence_gate",
    "boundary_source_gate",
    "paper_grade_boundary_source_gate",
    "boundary_runtime_gate",
    "boundary_runtime_traceability_gate",
    "boundary_runtime_profile_preservation_gate",
    "boundary_runtime_inlet_gate",
    "boundary_runtime_side_top_gate",
    "boundary_runtime_side_top_normal_leakage_gate",
    "boundary_runtime_outlet_gate",
    "clearance_numeric_gate",
    "native_inlet_equivalence_gate",
    "native_probe_component_equivalence_gate",
    "native_probe_component_interpretation_gate",
    "native_probe_official_height_gate",
    "runtime_inlet_diagnostics_evidence_gate",
    "runtime_inlet_diagnostics_step_window_gate",
    "inlet_source_gate",
    "paper_grade_inlet_source_gate",
    "inlet_source_distribution_route_gate",
    "inlet_source_rms_k_surrogate_gate",
    "inlet_method_class_supported",
    "inlet_length_scale_gate",
    "inlet_correlation_gate",
    "inlet_profile_time_averaging_gate",
    "inlet_streamwise_direction_gate",
    "inlet_profile_gate",
    "inlet_u_profile_gate",
    "inlet_k_profile_gate",
    "empty_tunnel_gate",
    "probe_vtk_source_window_gate",
    "probe_grid_extent_gate",
    "official_probe_set_gate",
    "official_probe_height_gate",
    "component_source_window_gate",
    "component_normalization_gate",
    "component_sensitivity_gate",
    "normalization_scale_gate",
    "streamwise_sign_gate",
    "synthetic_temporal_sampling_gate",
]

HASH_FIELDS = [
    "profile_csv_sha256",
    "official_measurement_sha256",
    "probe_mapping_table_sha256",
    "component_sensitivity_probe_audit_sha256",
    "component_sensitivity_official_sha256",
    "component_source_sha256",
    "inlet_source_setup_sha256",
    "boundary_source_setup_sha256",
    "runtime_inlet_diagnostics_csv_sha256",
    "runtime_inlet_diagnostics_audit_json_sha256",
]

NUMERIC_FIELDS = [
    "dx_m",
    "steps",
    "save_interval",
    "averaging_window",
    "requested_time_steps",
    "requested_vtk_save_interval",
    "requested_vtk_save_start_step",
    "requested_vtk_frame_count",
    "requested_vtk_frame_shortfall",
    "requested_vtk_expected_final_window_step_span",
    "requested_vtk_averaging_window_shortfall",
    "requested_vtk_expected_final_window_step_span_shortfall",
    "requested_vtk_minimum_step_span",
    "source_step_span",
    "source_step_span_shortfall",
    "minimum_validation_average_step_span",
    "available_frame_count",
    "final_window_mean_speed_drift_ratio",
    "max_final_window_mean_speed_drift_ratio",
    "Uref_mps",
    "Zref_m",
    "geometry_scale",
    "smagorinsky_cs",
    "target_max_profile_velocity_lbm",
    "estimated_max_profile_mach",
    "lbm_tau",
    "physical_viscosity_m2s",
    "probe_tolerance_m",
    "mean_probe_distance_m",
    "max_probe_distance_m",
    "max_official_coordinate_delta_m",
    "official_coordinate_delta_count",
    "probe_vtk_source_step_span",
    "probe_vtk_minimum_step_span",
    "probe_vtk_source_hash_set_count",
    "probe_inside_vtk_grid_extent_count",
    "probe_outside_vtk_grid_extent_count",
    "probe_missing_vtk_grid_extent_count",
    "component_sensitivity_official_filtered_row_count",
    "component_sensitivity_official_id_count",
    "component_sensitivity_probe_row_count",
    "component_sensitivity_valid_probe_id_count",
    "component_sensitivity_matched_valid_probe_id_count",
    "component_sensitivity_unmatched_valid_probe_id_count",
    "component_sensitivity_missing_official_probe_id_count",
    "component_sensitivity_official_probe_coverage_ratio",
    "component_source_step_span",
    "component_minimum_source_step_span",
    "component_source_time_steps_unique_count",
    "component_source_hash_set_unique_count",
    "streamwise_negative_fraction",
    "streamwise_mean_ratio",
    "streamwise_sign_valid_n",
    "streamwise_negative_count",
    "selected_component_rmse_ratio",
    "selected_component_bias_ratio",
    "selected_component_scaled_bias_ratio",
    "selected_component_bias_abs_reduction_ratio",
    "selected_component_mean_sim_ratio",
    "selected_component_mean_exp_ratio",
    "selected_component_mean_sim_to_exp_ratio",
    "best_component_rmse_ratio",
    "component_rmse_improvement_ratio",
    "normalization_best_fit_scale",
    "normalization_scaled_improvement_ratio",
    "probe_uref_expected_mps",
    "probe_uref_mismatch_count",
    "official_measurement_count",
    "official_probe_coverage_ratio",
    "missing_official_probe_count",
    "official_probe_set_row_count",
    "official_expected_row_count",
    "official_missing_probe_id_count",
    "official_expected_z_m",
    "official_expected_z_tolerance_m",
    "official_z_match_count",
    "official_z_mismatch_count",
    "valid_n",
    "synthetic_mode_count",
    "synthetic_update_interval",
    "synthetic_minimum_recommended_refresh_count",
    "synthetic_expected_final_window_refresh_count",
    "synthetic_component_norm_x",
    "synthetic_component_norm_y",
    "synthetic_component_norm_z",
    "synthetic_correlation_length_m",
    "boundary_runtime_frame_count",
    "boundary_runtime_source_step_span",
    "boundary_runtime_max_u_mae_ratio",
    "boundary_runtime_max_side_top_normal_velocity_ratio",
    "native_probe_max_official_coordinate_delta_m",
    "native_probe_official_coordinate_delta_recomputed_count",
    "native_probe_missing_official_coordinate_delta_count",
    "native_probe_official_coordinate_delta_violation_count",
    "native_probe_uref_mismatch_count",
    "native_probe_out_of_tolerance_count",
    "native_preconditions_runtime_source_frame_count",
    "native_preconditions_runtime_source_vtk_sha256_count",
    "native_preconditions_runtime_source_vtk_sha256_unique_count",
    "native_preconditions_time_averaging_evidence_selected_hash_count",
    "native_preconditions_runtime_final_window_mean_speed_drift_ratio",
    "native_preconditions_runtime_max_final_window_mean_speed_drift_ratio",
]

CRITICAL_PARITY_FIELDS = [
    "case",
    "wind_direction",
    "dx_m",
    "steps",
    "save_interval",
    "averaging_window",
    "time_averaging_fidelity_class",
    "requested_time_steps",
    "requested_vtk_save_interval",
    "requested_vtk_save_start_step",
    "requested_vtk_frame_count",
    "requested_vtk_frame_shortfall",
    "requested_vtk_expected_final_window_time_steps",
    "requested_vtk_expected_final_window_step_span",
    "requested_vtk_averaging_window_shortfall",
    "requested_vtk_expected_final_window_step_span_shortfall",
    "requested_vtk_minimum_step_span",
    "source_time_steps",
    "source_step_span",
    "source_step_span_shortfall",
    "minimum_validation_average_step_span",
    "available_frame_count",
    "selected_last_window",
    "source_steps_strictly_increasing",
    "source_step_spacing_uniform",
    "final_window_stationarity_gate",
    "final_window_mean_speed_drift_ratio",
    "max_final_window_mean_speed_drift_ratio",
    "mean_speed_statistics_source",
    "Uref_mps",
    "Zref_m",
    "compared_component",
    "velocity_component",
    "compared_component_unique_values",
    "probe_component_fidelity_class",
    "probe_id_field",
    "probe_tolerance_m",
    "probe_mapping_table_sha256",
    "probe_vtk_source_time_steps",
    "probe_vtk_source_step_span",
    "probe_vtk_minimum_step_span",
    "probe_vtk_source_hash_set_count",
    "probe_grid_extent_gate",
    "probe_inside_vtk_grid_extent_count",
    "probe_outside_vtk_grid_extent_count",
    "probe_missing_vtk_grid_extent_count",
    "mean_probe_distance_m",
    "max_probe_distance_m",
    "max_official_coordinate_delta_m",
    "official_coordinate_delta_count",
    "official_measurement_count",
    "official_probe_coverage_ratio",
    "missing_official_probe_count",
    "official_probe_set_gate",
    "official_probe_height_gate",
    "official_probe_set_row_count",
    "official_expected_row_count",
    "official_probe_ids_unique",
    "official_missing_probe_id_count",
    "official_expected_z_m",
    "official_expected_z_tolerance_m",
    "official_z_match_count",
    "official_z_mismatch_count",
    "component_sensitivity_probe_audit_sha256",
    "component_sensitivity_case",
    "component_sensitivity_wind_direction",
    "component_sensitivity_official_filtered_row_count",
    "component_sensitivity_official_id_count",
    "component_sensitivity_probe_row_count",
    "component_sensitivity_valid_probe_id_count",
    "component_sensitivity_matched_valid_probe_id_count",
    "component_sensitivity_unmatched_valid_probe_id_count",
    "component_sensitivity_missing_official_probe_id_count",
    "component_sensitivity_official_probe_coverage_ratio",
    "component_source_window_gate",
    "component_source_time_steps",
    "component_source_step_span",
    "component_minimum_source_step_span",
    "component_source_sha256",
    "component_source_time_steps_unique_count",
    "component_source_hash_set_unique_count",
    "streamwise_negative_fraction",
    "streamwise_mean_ratio",
    "streamwise_sign_valid_n",
    "streamwise_negative_count",
    "best_component_by_rmse",
    "selected_component_rmse_ratio",
    "selected_component_bias_ratio",
    "selected_component_scaled_bias_ratio",
    "selected_component_bias_abs_reduction_ratio",
    "selected_component_mean_sim_ratio",
    "selected_component_mean_exp_ratio",
    "selected_component_mean_sim_to_exp_ratio",
    "best_component_rmse_ratio",
    "component_rmse_improvement_ratio",
    "normalization_best_fit_scale",
    "normalization_scaled_improvement_ratio",
    "probe_uref_expected_mps",
    "probe_uref_values",
    "probe_uref_mismatch_count",
    "wind_vector",
    "inlet_face",
    "outlet_face",
    "lateral_faces",
    "velocity_set",
    "les_model",
    "synthetic_inlet_method",
    "inlet_distribution_treatment",
    "inlet_method_class",
    "inlet_source_method_class",
    "inlet_source_turbulent_inflow_fidelity_class",
    "inlet_source_distribution_consistent",
    "inlet_source_velocity_field_only",
    "inlet_source_requires_distribution_reconstruction",
    "inlet_source_correlation_model",
    "inlet_synthetic_correlation_model",
    "inlet_source_distribution_route",
    "inlet_source_reynolds_stress_treatment",
    "inlet_source_has_reynolds_stress_tensor_metadata_claim",
    "inlet_source_has_reynolds_stress_diagonal_source_evidence",
    "inlet_source_has_reynolds_stress_offdiagonal_source_evidence",
    "inlet_source_has_reynolds_stress_full_tensor_source_evidence",
    "inlet_source_has_reynolds_stress_diagonal_usage_evidence",
    "inlet_source_has_reynolds_stress_offdiagonal_usage_evidence",
    "inlet_source_has_reynolds_stress_full_tensor_usage_evidence",
    "inlet_source_has_sem_eddy_update_evidence",
    "inlet_source_has_sem_eddy_velocity_coupling_evidence",
    "inlet_source_has_three_component_velocity_write",
    "inlet_source_has_three_component_fluctuation_evidence",
    "inlet_source_has_k_driven_three_component_stg",
    "inlet_source_has_component_phase_decorrelation",
    "inlet_source_has_source_length_scale_evidence",
    "inlet_source_has_metadata_length_scale_evidence",
    "inlet_source_length_scale_evidence_basis",
    "inlet_source_has_temporal_filter_state",
    "inlet_source_has_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_rms_preserving_inlet_correction",
    "inlet_source_has_streamwise_clipping_control",
    "inlet_source_streamwise_clipping_enabled",
    "inlet_source_has_legacy_hardcoded_streamwise_clipping",
    "inlet_source_has_uncorrelated_random_inlet",
    "inlet_source_has_correlated_velocity_field_only",
    "inlet_source_has_uncorrelated_rms_velocity_field_only",
    "inlet_source_has_rms_k_velocity_surrogate",
    "inlet_source_rms_k_surrogate_gate",
    "inlet_source_rms_k_surrogate_reasons",
    "runtime_inlet_diagnostics_evidence_required",
    "runtime_inlet_diagnostics_evidence_required_basis_csv",
    "runtime_inlet_diagnostics_evidence_gate",
    "runtime_inlet_diagnostics_step_window_gate",
    "runtime_inlet_diagnostics_selected_steps_csv",
    "runtime_inlet_diagnostics_steps_cover_runtime_window",
    "runtime_inlet_diagnostics_csv_sha256",
    "runtime_inlet_diagnostics_audit_json_sha256",
    "wall_roughness_treatment",
    "boundary_equivalence_basis",
    "boundary_equivalence_supported",
    "boundary_evidence_class",
    "boundary_evidence_files_all_exist",
    "boundary_evidence_files_all_hashed",
    "boundary_condition_fields_supported",
    "boundary_condition_support_reasons",
    "inlet_boundary_supported",
    "outlet_boundary_supported",
    "lateral_boundary_supported",
    "top_boundary_supported",
    "ground_wall_treatment_supported",
    "roughness_treatment_supported",
    "floor_roughness_source_supported",
    "blockage_source_supported",
    "fetch_clearance_source_supported",
    "outlet_reflection_check_supported",
    "side_top_boundary_check_supported",
    "boundary_clearance_reasons",
    "boundary_source_method_class",
    "boundary_source_fidelity_class",
    "boundary_source_has_complete_wind_tunnel_evidence",
    "boundary_source_has_empty_advanced_method_stub_only",
    "boundary_source_wind_tunnel_equivalent",
    "boundary_source_simplified",
    "boundary_source_missing_paper_grade_source_evidence",
    "boundary_source_has_paper_grade_outlet_source",
    "boundary_source_has_paper_grade_side_top_source",
    "boundary_source_has_paper_grade_rough_wall_source",
    "boundary_source_has_paper_grade_development_source",
    "boundary_source_has_non_reflecting_outlet_method",
    "boundary_source_has_non_reflecting_outlet_state_evidence",
    "boundary_source_has_periodic_side_top_method",
    "boundary_source_has_periodic_pair_mapping_evidence",
    "boundary_source_has_rough_wall_function_method",
    "boundary_source_has_rough_wall_parameter_evidence",
    "boundary_source_has_rough_wall_action_evidence",
    "boundary_source_has_precursor_or_recycling_boundary_method",
    "boundary_source_has_precursor_or_recycling_boundary_field_evidence",
    "boundary_runtime_source_time_steps_csv",
    "boundary_runtime_source_time_steps_match_runtime",
    "boundary_runtime_source_vtk_sha256_match_runtime",
    "boundary_runtime_source_step_hash_pairs_match_runtime",
    "native_probe_component_fidelity_class",
    "native_probe_compared_component_values",
    "native_probe_expected_compared_component",
    "native_probe_max_official_coordinate_delta_m",
    "native_probe_official_coordinate_delta_source",
    "native_probe_official_coordinate_delta_recomputed_count",
    "native_probe_missing_official_coordinate_delta_count",
    "native_probe_official_coordinate_delta_violation_count",
    "native_probe_uref_mismatch_count",
    "native_probe_out_of_tolerance_count",
    "native_probe_component_source_time_steps_match_runtime",
    "native_probe_component_source_steps_strictly_increasing",
    "native_probe_component_source_step_spacing_uniform",
    "native_probe_component_source_vtk_sha256_match_runtime",
    "native_probe_source_step_hash_pairs_match_runtime",
    "native_probe_component_source_step_hash_pairs_match_runtime",
    "native_preconditions_time_average_gate",
    "native_preconditions_time_average_evidence_gate",
    "native_preconditions_time_averaging_fidelity_class",
    "native_preconditions_time_averaging_evidence_file_gate",
    "native_preconditions_time_averaging_evidence_schema",
    "native_preconditions_time_averaging_evidence_gate",
    "native_preconditions_time_averaging_evidence_actual_vtk_output_gate",
    "native_preconditions_time_averaging_evidence_bound",
    "native_preconditions_time_averaging_evidence_selected_steps",
    "native_preconditions_time_averaging_evidence_selected_hash_count",
    "native_preconditions_runtime_selected_last_window",
    "native_preconditions_runtime_source_frame_count",
    "native_preconditions_runtime_source_vtk_sha256_count",
    "native_preconditions_runtime_source_vtk_sha256_unique_count",
    "native_preconditions_runtime_final_window_frame_count_gate",
    "native_preconditions_runtime_final_window_stationarity_gate",
    "native_preconditions_runtime_final_window_mean_speed_drift_ratio",
    "native_preconditions_runtime_max_final_window_mean_speed_drift_ratio",
    "native_preconditions_runtime_mean_speed_statistics_source",
    "native_preconditions_runtime_mean_speed_statistics_cli_override",
    "native_preconditions_strict_native_run_gate",
    "requested_vtk_frame_gate",
    "run_freshness_gate",
    "time_averaging_gate",
    "lbm_stability_gate",
    "normalization_valid",
    "compared_component_consistency_gate",
    "wind_direction_valid",
    "blockage_protocol_gate",
    "boundary_protocol_gate",
    "boundary_evidence_gate",
    "boundary_source_gate",
    "paper_grade_boundary_source_gate",
    "boundary_runtime_gate",
    "boundary_runtime_traceability_gate",
    "boundary_runtime_profile_preservation_gate",
    "boundary_runtime_inlet_gate",
    "boundary_runtime_side_top_gate",
    "boundary_runtime_side_top_normal_leakage_gate",
    "boundary_runtime_outlet_gate",
    "clearance_numeric_gate",
    "native_inlet_equivalence_gate",
    "native_probe_component_equivalence_gate",
    "native_probe_component_interpretation_gate",
    "native_probe_official_height_gate",
    "inlet_source_gate",
    "paper_grade_inlet_source_gate",
    "inlet_source_distribution_route_gate",
    "inlet_method_class_supported",
    "inlet_length_scale_gate",
    "inlet_correlation_gate",
    "inlet_profile_time_averaging_gate",
    "inlet_streamwise_direction_gate",
    "inlet_profile_gate",
    "inlet_u_profile_gate",
    "inlet_k_profile_gate",
    "probe_vtk_source_window_gate",
    "component_normalization_gate",
    "component_sensitivity_gate",
    "normalization_scale_gate",
    "streamwise_sign_gate",
    "synthetic_temporal_sampling_gate",
    "synthetic_mode_count",
    "synthetic_update_interval",
    "synthetic_minimum_recommended_refresh_count",
    "synthetic_expected_final_window_refresh_count",
    "synthetic_component_norm_x",
    "synthetic_component_norm_y",
    "synthetic_component_norm_z",
    "synthetic_correlation_length_m",
    "boundary_runtime_frame_count",
    "boundary_runtime_source_step_span",
    "boundary_runtime_max_u_mae_ratio",
    "boundary_runtime_max_side_top_normal_velocity_ratio",
    "profile_csv_sha256",
    "official_measurement_sha256",
    "component_sensitivity_official_sha256",
    "inlet_source_setup_sha256",
    "boundary_source_setup_sha256",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit paired native FluidX3D and CityLBM metrics parity.")
    parser.add_argument("--citylbm-metrics", required=True, help="CityLBM validation metrics CSV/JSON.")
    parser.add_argument("--native-metrics", required=True, help="Native FluidX3D validation metrics CSV/JSON.")
    parser.add_argument("--out", required=True, help="Output native_citylbm_parity_audit.json.")
    parser.add_argument("--case", default="", help="Optional case filter.")
    parser.add_argument("--wind-direction", default="", help="Optional wind-direction filter.")
    parser.add_argument("--citylbm-software", default="citylbm")
    parser.add_argument("--native-software", default="native-fluidx3d")
    parser.add_argument("--numeric-tolerance", type=float, default=1.0e-9)
    parser.add_argument(
        "--optional-field",
        action="append",
        default=[],
        help="Field allowed to be missing on both rows without failing the parity gate.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        parsed = float(value)
        return None if math.isnan(parsed) or math.isinf(parsed) else parsed
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return None if math.isnan(parsed) or math.isinf(parsed) else parsed


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("\\", "/").split())


def read_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        return [data] if isinstance(data, dict) else []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def text_matches(value: Any, expected: str) -> bool:
    return not expected or normalize_text(value) == normalize_text(expected)


def select_row(
    rows: List[Dict[str, Any]],
    software: str,
    case: str,
    wind_direction: str,
) -> Tuple[Optional[Dict[str, Any]], str]:
    candidates: List[Dict[str, Any]] = []
    for row in rows:
        if not text_matches(row.get("software"), software):
            continue
        if not text_matches(row.get("case"), case):
            continue
        if not text_matches(row.get("wind_direction"), wind_direction):
            continue
        candidates.append(row)
    if not candidates:
        return None, "no_matching_row"
    if len(candidates) > 1:
        return candidates[-1], f"multiple_matching_rows_selected_last:{len(candidates)}"
    return candidates[0], ""


def compare_text(field: str, city: Dict[str, Any], native: Dict[str, Any], optional: set[str]) -> Dict[str, Any]:
    city_value = normalize_text(city.get(field))
    native_value = normalize_text(native.get(field))
    missing = not city_value and not native_value
    match = city_value == native_value and (not missing or field in optional)
    return {
        "field": field,
        "kind": "text",
        "citylbm": city.get(field, ""),
        "native": native.get(field, ""),
        "match": match,
        "reason": "both_missing_optional" if missing and field in optional else ("match" if match else "mismatch_or_missing"),
    }


def normalize_hash(value: Any) -> str:
    return str(value or "").strip().lower()


def compare_hash(field: str, city: Dict[str, Any], native: Dict[str, Any], optional: set[str]) -> Dict[str, Any]:
    city_value = normalize_hash(city.get(field))
    native_value = normalize_hash(native.get(field))
    missing = not city_value and not native_value
    match = city_value == native_value and (not missing or field in optional)
    if missing and field not in optional:
        reason = "both_hashes_missing"
    elif not city_value:
        reason = "citylbm_hash_missing"
    elif not native_value:
        reason = "native_hash_missing"
    elif match:
        reason = "match"
    else:
        reason = "hash_mismatch"
    return {
        "field": field,
        "kind": "hash",
        "citylbm": city.get(field, ""),
        "native": native.get(field, ""),
        "match": match,
        "reason": "both_missing_optional" if missing and field in optional else reason,
    }


def compare_numeric(
    field: str,
    city: Dict[str, Any],
    native: Dict[str, Any],
    tolerance: float,
    optional: set[str],
) -> Dict[str, Any]:
    city_value = as_float(city.get(field))
    native_value = as_float(native.get(field))
    missing = city_value is None and native_value is None
    diff = abs(city_value - native_value) if city_value is not None and native_value is not None else None
    match = (diff is not None and diff <= tolerance) or (missing and field in optional)
    return {
        "field": field,
        "kind": "numeric",
        "citylbm": city.get(field, ""),
        "native": native.get(field, ""),
        "absolute_difference": diff,
        "tolerance": tolerance,
        "match": match,
        "reason": "both_missing_optional" if missing and field in optional else ("match" if match else "mismatch_or_missing"),
    }


def main() -> int:
    args = parse_args()
    city_path = Path(args.citylbm_metrics).expanduser().resolve()
    native_path = Path(args.native_metrics).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    optional = {field.strip() for field in args.optional_field if field.strip()}

    reasons: List[str] = []
    try:
        city_rows = read_rows(city_path)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        city_rows = []
        reasons.append(f"citylbm_metrics_unreadable:{exc}")
    try:
        native_rows = read_rows(native_path)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        native_rows = []
        reasons.append(f"native_metrics_unreadable:{exc}")

    city_row, city_select_reason = select_row(city_rows, args.citylbm_software, args.case, args.wind_direction)
    native_row, native_select_reason = select_row(native_rows, args.native_software, args.case, args.wind_direction)
    if city_select_reason and not city_select_reason.startswith("multiple_matching"):
        reasons.append("citylbm_" + city_select_reason)
    if native_select_reason and not native_select_reason.startswith("multiple_matching"):
        reasons.append("native_" + native_select_reason)

    comparisons: List[Dict[str, Any]] = []
    if city_row is not None and native_row is not None:
        comparisons.extend(compare_text(field, city_row, native_row, optional) for field in TEXT_FIELDS)
        comparisons.extend(compare_text(field, city_row, native_row, optional) for field in GATE_FIELDS)
        comparisons.extend(compare_hash(field, city_row, native_row, optional) for field in HASH_FIELDS)
        comparisons.extend(
            compare_numeric(field, city_row, native_row, args.numeric_tolerance, optional)
            for field in NUMERIC_FIELDS
        )

    mismatches = [item for item in comparisons if not item["match"]]
    if mismatches:
        reasons.append("paired_condition_mismatch:" + ",".join(item["field"] for item in mismatches))
    comparison_by_field = {str(item.get("field") or ""): item for item in comparisons}
    missing_critical_fields = [
        field
        for field in CRITICAL_PARITY_FIELDS
        if not comparison_by_field.get(field) or comparison_by_field[field].get("match") is not True
    ]
    matched_critical_fields = [
        field
        for field in CRITICAL_PARITY_FIELDS
        if comparison_by_field.get(field) and comparison_by_field[field].get("match") is True
    ]
    critical_field_gate = "pass" if not missing_critical_fields else "fail"
    if missing_critical_fields:
        reasons.append("critical_parity_field_missing_or_mismatch:" + ",".join(missing_critical_fields))

    gate = "pass" if not reasons else "fail"
    report = {
        "schema": "citylbm.native_citylbm_parity_audit.v1",
        "generated_at_utc": utc_now(),
        "native_citylbm_parity_gate": gate,
        "native_citylbm_parity_gate_reasons": reasons or ["native_citylbm_conditions_match"],
        "citylbm_metrics": str(city_path),
        "native_metrics": str(native_path),
        "case_filter": args.case,
        "wind_direction_filter": args.wind_direction,
        "citylbm_software_filter": args.citylbm_software,
        "native_software_filter": args.native_software,
        "citylbm_row_selection_warning": city_select_reason,
        "native_row_selection_warning": native_select_reason,
        "matched_field_count": sum(1 for item in comparisons if item["match"]),
        "mismatched_field_count": len(mismatches),
        "compared_text_field_count": len(TEXT_FIELDS),
        "compared_gate_field_count": len(GATE_FIELDS),
        "compared_hash_field_count": len(HASH_FIELDS),
        "compared_numeric_field_count": len(NUMERIC_FIELDS),
        "critical_parity_field_gate": critical_field_gate,
        "required_critical_fields": CRITICAL_PARITY_FIELDS,
        "required_critical_field_count": len(CRITICAL_PARITY_FIELDS),
        "matched_critical_fields": matched_critical_fields,
        "matched_critical_field_count": len(matched_critical_fields),
        "missing_critical_fields": missing_critical_fields,
        "missing_critical_field_count": len(missing_critical_fields),
        "mismatched_fields": [item["field"] for item in mismatches],
        "comparisons": comparisons,
        "recommended_next_action": (
            "Rerun the native and CityLBM cases with the same case, wind direction, dx, steps, VTK cadence, "
            "averaging window, Uref, inlet/boundary setup, source-audit hashes, official/probe/profile evidence, "
            "probe component and probe table before comparing accuracy."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"native_citylbm_parity_gate={gate}; reasons={';'.join(report['native_citylbm_parity_gate_reasons'])}")
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
