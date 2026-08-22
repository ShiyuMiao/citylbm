#!/usr/bin/env python3
"""Build a CityLBM validation metrics row from Data Probe audit output.

Inputs:
  - Data Probe audit CSV from Grasshopper.
  - Official measurement CSV, e.g. AIJ Case E RS_caseE.csv.

The output follows docs/validation_metrics_template.csv and is designed to feed
scripts/validation_gate.py. It focuses on traceable probe matching, selected
velocity component, Uref normalization, and systematic-bias detection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


TEMPLATE_FIELDS = [
    "case",
    "wind_direction",
    "software",
    "version",
    "dx_m",
    "steps",
    "save_interval",
    "averaging_window",
    "averaged_frame_shortfall",
    "available_frame_count",
    "vtk_pattern",
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
    "requested_vtk_frame_gate",
    "requested_vtk_frame_gate_reasons",
    "run_freshness_gate",
    "run_freshness_gate_reasons",
    "latest_reference_mtime_utc",
    "oldest_selected_vtk_mtime_utc",
    "source_time_steps",
    "source_first_time_step",
    "source_last_time_step",
    "source_step_span",
    "source_step_span_shortfall",
    "minimum_validation_average_step_span",
    "latest_available_time_step",
    "selected_last_window",
    "source_steps_strictly_increasing",
    "source_step_spacing_uniform",
    "time_averaging_gate",
    "time_averaging_gate_reasons",
    "mean_speed_mps",
    "mean_speed_stddev_mps",
    "max_speed_stddev_mps",
    "mean_speed_stddev_ratio",
    "max_speed_stddev_ratio",
    "final_window_stationarity_gate",
    "final_window_mean_speed_drift_ratio",
    "max_final_window_mean_speed_drift_ratio",
    "mean_speed_statistics_source",
    "profile_csv",
    "profile_csv_sha256",
    "custom_profile_rows",
    "custom_profile_k_rows",
    "custom_profile_k_complete",
    "profile_first_z_m",
    "profile_last_z_m",
    "profile_k_min_m2s2",
    "profile_k_max_m2s2",
    "profile_k_min_lbm",
    "profile_k_max_lbm",
    "geometry_scale",
    "geometry_unit_assumption",
    "geometry_scale_evidence_gate",
    "geometry_scale_expected_casee_note",
    "geometry_building_count",
    "geometry_building_height_m",
    "Uref_mps",
    "Zref_m",
    "target_max_profile_velocity_lbm",
    "estimated_max_profile_mach",
    "lbm_tau",
    "lbm_nu",
    "physical_viscosity_m2s",
    "estimated_reynolds_number",
    "velocity_set",
    "les_model",
    "smagorinsky_cs",
    "solver_stability_warnings",
    "lbm_stability_gate",
    "normalization_valid",
    "velocity_component",
    "compared_component_consistency_gate",
    "compared_component_unique_values",
    "wind_vector",
    "wind_direction_valid",
    "inlet_face",
    "outlet_face",
    "lateral_faces",
    "domain_size_x_m",
    "domain_size_y_m",
    "domain_size_z_m",
    "max_building_height_m",
    "upstream_clearance_h",
    "downstream_clearance_h",
    "min_lateral_clearance_h",
    "top_clearance_h",
    "approx_frontal_blockage_ratio",
    "approx_plan_blockage_ratio",
    "blockage_protocol_gate",
    "boundary_protocol_gate",
    "boundary_evidence_source",
    "boundary_evidence_gate",
    "boundary_protocol_audit",
    "boundary_protocol_metadata_sha256",
    "boundary_evidence_json_sha256",
    "boundary_run_identity_gate",
    "boundary_run_identity_gate_reasons",
    "boundary_expected_aij_case",
    "boundary_expected_wind_direction",
    "boundary_evidence_aij_case",
    "boundary_evidence_wind_direction",
    "boundary_evidence_case_metadata_sha256",
    "boundary_evidence_metadata_sha256_matches_current",
    "boundary_missing_evidence_fields",
    "boundary_equivalence_basis",
    "boundary_equivalence_supported",
    "boundary_evidence_class",
    "boundary_evidence_class_supported",
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
    "clearance_numeric_gate",
    "boundary_clearance_reasons",
    "boundary_summary",
    "boundary_source_audit",
    "boundary_source_gate",
    "boundary_source_gate_reasons",
    "paper_grade_boundary_source_gate",
    "paper_grade_boundary_source_gate_reasons",
    "boundary_source_method_class",
    "boundary_source_coherent",
    "boundary_source_simplified",
    "boundary_source_wind_tunnel_equivalent",
    "boundary_source_advanced_code_evidence",
    "boundary_source_comment_stripped_code_audit",
    "boundary_source_has_non_reflecting_outlet_method",
    "boundary_source_has_non_reflecting_outlet_state_evidence",
    "boundary_source_has_periodic_side_top_method",
    "boundary_source_has_periodic_pair_mapping_evidence",
    "boundary_source_has_rough_wall_function_method",
    "boundary_source_has_rough_wall_parameter_evidence",
    "boundary_source_has_rough_wall_action_evidence",
    "boundary_source_has_precursor_or_recycling_boundary_method",
    "boundary_source_has_precursor_or_recycling_boundary_field_evidence",
    "boundary_source_has_empty_advanced_boundary_method_stub",
    "boundary_source_empty_advanced_boundary_method_stub_count",
    "boundary_source_has_paper_grade_outlet_source",
    "boundary_source_has_paper_grade_side_top_source",
    "boundary_source_has_paper_grade_rough_wall_source",
    "boundary_source_has_paper_grade_development_source",
    "boundary_source_missing_paper_grade_source_evidence",
    "boundary_type_e_velocity_initialization",
    "boundary_type_e_velocity_initialization_guard",
    "boundary_type_e_velocity_initialization_coordinates",
    "boundary_type_e_velocity_initialization_velocity_write",
    "boundary_type_e_velocity_initialization_before_device_upload",
    "boundary_flags_device_upload_after_type_e_velocity_initialization",
    "boundary_u_device_upload_after_type_e_velocity_initialization",
    "boundary_profile_type_e_velocity_initialization",
    "boundary_uniform_type_e_velocity_initialization",
    "boundary_velocity_initialization_metadata_applied",
    "boundary_velocity_initialization_metadata_treatment",
    "boundary_velocity_initialization_metadata_profile_aware",
    "boundary_velocity_initialization_metadata_device_upload_order",
    "boundary_velocity_initialization_metadata_paper_grade_status",
    "boundary_source_setup_sha256",
    "boundary_runtime_audit",
    "boundary_runtime_gate",
    "boundary_runtime_gate_reasons",
    "boundary_runtime_traceability_gate",
    "boundary_runtime_profile_preservation_gate",
    "boundary_runtime_inlet_gate",
    "boundary_runtime_side_top_gate",
    "boundary_runtime_side_top_normal_leakage_gate",
    "boundary_runtime_outlet_gate",
    "boundary_runtime_max_u_mae_ratio",
    "boundary_runtime_inlet_u_mae_ratio",
    "boundary_runtime_outlet_u_mae_ratio",
    "boundary_runtime_side_top_max_u_mae_ratio",
    "boundary_runtime_max_side_top_normal_velocity_ratio",
    "boundary_runtime_max_side_top_normal_abs_mps",
    "boundary_runtime_max_negative_streamwise_fraction",
    "boundary_runtime_source_step_span",
    "boundary_runtime_frame_count",
    "inlet_source_audit",
    "inlet_source_gate",
    "inlet_source_gate_reasons",
    "paper_grade_inlet_source_gate",
    "paper_grade_inlet_source_gate_reasons",
    "inlet_source_method_class",
    "inlet_source_distribution_consistent",
    "inlet_source_velocity_field_only",
    "inlet_source_advanced_code_evidence",
    "inlet_source_comment_stripped_code_audit",
    "inlet_source_defines_hpp",
    "inlet_source_defines_hpp_sha256",
    "inlet_source_defines_hpp_audited",
    "inlet_source_has_equilibrium_boundaries_define",
    "inlet_source_has_type_e_equilibrium_boundary_route",
    "inlet_source_distribution_route",
    "inlet_source_distribution_route_gate",
    "inlet_source_has_distribution_function_write",
    "inlet_source_distribution_function_write_count",
    "inlet_source_has_inlet_distribution_reconstruction",
    "inlet_source_inlet_distribution_reconstruction_count",
    "inlet_source_has_inlet_length_scale_evidence",
    "inlet_source_metadata_length_scale_gate",
    "inlet_source_has_reynolds_stress_tensor_evidence",
    "inlet_source_has_documented_isotropic_k_assumption",
    "inlet_source_reynolds_stress_treatment",
    "inlet_source_metadata_reynolds_stress_treatment",
    "inlet_source_has_digital_filter_evidence",
    "inlet_source_has_digital_filter_kernel_evidence",
    "inlet_source_has_digital_filter_state_evidence",
    "inlet_source_has_sem_evidence",
    "inlet_source_has_sem_eddy_population_evidence",
    "inlet_source_has_precursor_or_recycling_evidence",
    "inlet_source_has_precursor_recycling_field_evidence",
    "inlet_source_distribution_consistency_basis",
    "inlet_source_setup_sha256",
    "inlet_source_synthetic_requested",
    "inlet_source_has_synthetic_function",
    "inlet_source_has_three_component_velocity_write",
    "inlet_source_has_three_component_fluctuation_evidence",
    "inlet_source_has_k_driven_three_component_stg",
    "inlet_source_has_mean_preserving_inlet_correction",
    "inlet_source_has_layerwise_mean_preserving_inlet_correction",
    "inlet_source_spectral_mode_count",
    "inlet_source_refresh_with_current_time",
    "inlet_source_update_interval_run_control",
    "inlet_source_segmented_stg_run_loop",
    "inlet_source_has_streamwise_clipping_control",
    "inlet_source_streamwise_min_fraction",
    "inlet_source_streamwise_clipping_enabled",
    "inlet_source_has_legacy_hardcoded_streamwise_clipping",
    "inlet_source_has_uncorrelated_random_inlet",
    "inlet_source_uncorrelated_random_patterns",
    "inlet_source_correlation_model",
    "inlet_source_recommended_next_action",
    "synthetic_inlet_method",
    "inlet_distribution_treatment",
    "inlet_method_class",
    "inlet_method_class_supported",
    "wall_roughness_treatment",
    "synthetic_mode_count",
    "synthetic_update_interval",
    "synthetic_minimum_recommended_refresh_count",
    "synthetic_expected_final_window_refresh_count",
    "synthetic_temporal_sampling_gate",
    "synthetic_max_fraction",
    "synthetic_min_streamwise_fraction",
    "synthetic_streamwise_clipping_enabled",
    "synthetic_legacy_hardcoded_streamwise_clipping",
    "synthetic_component_norm_x",
    "synthetic_component_norm_y",
    "synthetic_component_norm_z",
    "synthetic_correlation_length_m",
    "inlet_length_scale_source",
    "inlet_length_scale_gate",
    "inlet_correlation_audit",
    "inlet_correlation_gate",
    "inlet_temporal_lag1_correlation",
    "inlet_temporal_lag1_abs_correlation",
    "inlet_spatial_adjacent_correlation",
    "inlet_temporal_integral_positive_lag_count",
    "inlet_temporal_integral_time_steps",
    "inlet_spatial_integral_positive_lag_count",
    "inlet_spatial_integral_length_cells",
    "inlet_spatial_integral_length_m",
    "inlet_min_temporal_integral_lag_count",
    "inlet_min_spatial_integral_lag_count",
    "inlet_streamwise_fluctuation_variance",
    "inlet_k_variance_gate",
    "inlet_streamwise_variance_target_from_k",
    "inlet_streamwise_variance_to_k_ratio",
    "inlet_tke_gate",
    "inlet_tke_target_from_af_k",
    "inlet_tke_to_k_ratio",
    "inlet_mean_turbulent_kinetic_energy_from_components",
    "inlet_temporal_finite_correlation_fraction",
    "inlet_spatial_finite_correlation_fraction",
    "inlet_correlation_frame_count",
    "inlet_correlation_source_time_steps",
    "inlet_correlation_source_step_span",
    "inlet_correlation_minimum_step_span",
    "inlet_correlation_selected_last_window",
    "inlet_correlation_source_steps_strictly_increasing",
    "inlet_correlation_source_step_spacing_uniform",
    "inlet_profile_audit",
    "inlet_profile_available_frame_count",
    "inlet_profile_frame_count",
    "inlet_profile_source_time_steps",
    "inlet_profile_source_first_time_step",
    "inlet_profile_source_last_time_step",
    "inlet_profile_source_step_span",
    "inlet_profile_minimum_step_span",
    "inlet_profile_latest_available_time_step",
    "inlet_profile_selected_last_window",
    "inlet_profile_source_steps_strictly_increasing",
    "inlet_profile_source_step_spacing_uniform",
    "inlet_profile_time_averaging_gate",
    "inlet_profile_time_averaging_gate_reasons",
    "inlet_negative_streamwise_fraction",
    "inlet_streamwise_direction_gate",
    "inlet_profile_gate",
    "inlet_u_profile_gate",
    "inlet_u_mae_ratio",
    "inlet_u_rmse_ratio",
    "inlet_k_profile_gate",
    "inlet_k_mae_ratio",
    "inlet_k_rmse_ratio",
    "empty_tunnel_gate",
    "empty_tunnel_U_bias_ratio",
    "empty_tunnel_k_bias_ratio",
    "native_fluidx3d_baseline_id",
    "native_baseline_gate",
    "native_preconditions_audit",
    "native_preconditions_gate",
    "native_preconditions_gate_reasons",
    "native_preconditions_protocol_identity_gate",
    "native_preconditions_time_average_gate",
    "native_preconditions_time_average_evidence_gate",
    "native_preconditions_time_average_evidence_gate_reasons",
    "native_preconditions_expected_uref_mps",
    "native_preconditions_actual_uref_mps",
    "native_preconditions_expected_zref_m",
    "native_preconditions_af_uref_at_zref_mps",
    "native_preconditions_uref_af_profile_delta_mps",
    "native_preconditions_metadata_uref_af_profile_delta_mps",
    "native_preconditions_runtime_selected_last_window",
    "native_preconditions_runtime_source_vtk_sha256_count",
    "native_preconditions_runtime_source_vtk_sha256_unique_count",
    "native_preconditions_runtime_final_window_stationarity_gate",
    "native_preconditions_runtime_final_window_mean_speed_drift_ratio",
    "native_preconditions_runtime_max_final_window_mean_speed_drift_ratio",
    "native_component_sensitivity_hash_traceability_gate",
    "native_component_sensitivity_hash_traceability_gate_reasons",
    "native_component_sensitivity_probe_audit_sha256_matches_current",
    "native_component_sensitivity_official_sha256_matches_current",
    "native_component_sensitivity_probe_audit_sha256",
    "native_component_sensitivity_official_sha256",
    "native_preconditions_probe_audit_sha256",
    "native_preconditions_official_measurement_sha256",
    "native_inlet_equivalence_gate",
    "native_inlet_equivalence_gate_reasons",
    "native_inlet_profile_audit",
    "native_inlet_profile_gate",
    "native_inlet_u_profile_gate",
    "native_inlet_k_profile_gate",
    "native_inlet_profile_time_averaging_gate",
    "native_inlet_profile_af_csv_sha256_matches_expected",
    "native_inlet_profile_source_time_steps_match_runtime",
    "native_inlet_profile_source_vtk_sha256_match_runtime",
    "native_inlet_profile_source_step_span",
    "native_inlet_profile_minimum_step_span",
    "native_inlet_correlation_audit",
    "native_inlet_correlation_gate",
    "native_inlet_k_variance_gate",
    "native_inlet_streamwise_variance_target_from_k",
    "native_inlet_streamwise_variance_to_k_ratio",
    "native_inlet_tke_gate",
    "native_inlet_tke_target_from_af_k",
    "native_inlet_tke_to_k_ratio",
    "native_inlet_mean_turbulent_kinetic_energy_from_components",
    "native_inlet_correlation_source_time_steps_match_runtime",
    "native_inlet_correlation_source_vtk_sha256_match_runtime",
    "native_inlet_correlation_source_step_span",
    "native_inlet_correlation_minimum_step_span",
    "native_inlet_source_stg_evidence_required",
    "native_inlet_source_distribution_route",
    "native_inlet_source_distribution_route_gate",
    "native_inlet_source_has_equilibrium_boundaries_define",
    "native_inlet_source_has_type_e_equilibrium_boundary_route",
    "native_inlet_source_has_three_component_velocity_write",
    "native_inlet_source_has_three_component_fluctuation_evidence",
    "native_inlet_source_has_k_driven_three_component_stg",
    "native_inlet_source_has_mean_preserving_inlet_correction",
    "native_inlet_source_has_layerwise_mean_preserving_inlet_correction",
    "native_inlet_source_has_streamwise_clipping_control",
    "native_inlet_source_streamwise_min_fraction",
    "native_inlet_source_streamwise_clipping_enabled",
    "native_inlet_source_has_legacy_hardcoded_streamwise_clipping",
    "native_inlet_source_uncorrelated_random_patterns",
    "native_inlet_source_recommended_next_action",
    "native_probe_component_equivalence_gate",
    "native_probe_component_equivalence_gate_reasons",
    "native_probe_compared_component_values",
    "native_probe_expected_compared_component",
    "native_probe_compared_component_mismatch_reason",
    "native_probe_official_coverage_reason",
    "native_probe_missing_official_probe_ids",
    "native_probe_unmatched_probe_ids",
    "native_probe_duplicate_ids",
    "native_probe_max_official_coordinate_delta_m",
    "native_probe_official_coordinate_delta_source",
    "native_probe_official_coordinate_delta_recomputed_count",
    "native_probe_official_coordinate_delta_recompute_error",
    "native_probe_missing_official_coordinate_delta_count",
    "native_probe_official_coordinate_delta_violation_count",
    "native_probe_uref_mismatch_count",
    "native_probe_out_of_tolerance_count",
    "native_probe_projection_issue_reason",
    "native_probe_component_uref_issue_reason",
    "native_probe_component_source_time_steps_match_runtime",
    "native_probe_component_source_steps_strictly_increasing",
    "native_probe_component_source_step_spacing_uniform",
    "native_probe_component_source_vtk_sha256_match_runtime",
    "native_boundary_equivalence_gate",
    "native_boundary_equivalence_gate_reasons",
    "native_boundary_protocol_gate",
    "native_boundary_evidence_gate",
    "native_boundary_run_identity_gate",
    "native_boundary_run_identity_gate_reasons",
    "native_boundary_evidence_metadata_sha256_matches_current",
    "native_boundary_evidence_aij_case",
    "native_boundary_evidence_wind_direction",
    "native_boundary_protocol_gate_reasons",
    "native_boundary_missing_evidence_fields",
    "native_boundary_unsupported_condition_fields",
    "native_boundary_required_support_fields_missing_or_false",
    "native_boundary_equivalence_supported",
    "native_boundary_evidence_class_supported",
    "native_boundary_evidence_files_all_hashed",
    "native_boundary_condition_fields_supported",
    "native_boundary_clearance_numeric_gate",
    "native_boundary_clearance_numeric_gate_reasons",
    "native_boundary_blockage_gate",
    "native_boundary_runtime_gate",
    "native_boundary_runtime_gate_reasons",
    "native_boundary_runtime_traceability_gate",
    "native_boundary_runtime_profile_preservation_gate",
    "native_boundary_runtime_inlet_gate",
    "native_boundary_runtime_side_top_gate",
    "native_boundary_runtime_side_top_normal_leakage_gate",
    "native_boundary_runtime_outlet_gate",
    "native_boundary_runtime_max_u_mae_ratio",
    "native_boundary_runtime_max_side_top_normal_velocity_ratio",
    "native_boundary_runtime_max_side_top_normal_abs_mps",
    "native_boundary_runtime_source_step_span",
    "native_top_blocking_priority_rank",
    "native_top_blocking_priority_key",
    "native_top_blocking_priority_reason_count",
    "native_top_blocking_priority_reasons",
    "native_top_blocking_priority_diagnosis",
    "native_top_blocking_priority_next_action",
    "native_rerun_prescription_gate",
    "native_rerun_prescription_top_key",
    "native_rerun_prescription_experiment",
    "native_rerun_prescription_required_controls",
    "native_rerun_prescription_minimum_final_window",
    "native_rerun_prescription_accuracy_interpretation_allowed",
    "native_rerun_prescription_summary",
    "native_precondition_closure_gate",
    "native_precondition_closed_stage_count",
    "native_precondition_failed_stage_count",
    "native_precondition_failed_stage_keys",
    "native_precondition_top_blocking_stage_key",
    "native_precondition_top_blocking_stage_rank",
    "native_precondition_top_blocking_stage_reason_count",
    "native_precondition_top_blocking_stage_reasons",
    "native_preconditions_manifest_sha256",
    "native_preconditions_setup_sha256",
    "native_preconditions_metadata_sha256",
    "native_preconditions_runtime_audit_sha256",
    "native_citylbm_parity_audit",
    "native_citylbm_parity_gate",
    "native_citylbm_parity_gate_reasons",
    "native_citylbm_parity_native_metrics",
    "native_citylbm_parity_matched_field_count",
    "native_citylbm_parity_mismatched_field_count",
    "native_citylbm_parity_mismatched_fields",
    "native_citylbm_parity_compared_text_field_count",
    "native_citylbm_parity_compared_gate_field_count",
    "native_citylbm_parity_compared_hash_field_count",
    "native_citylbm_parity_compared_numeric_field_count",
    "native_citylbm_parity_critical_field_gate",
    "native_citylbm_parity_required_critical_field_count",
    "native_citylbm_parity_matched_critical_field_count",
    "native_citylbm_parity_missing_critical_field_count",
    "native_citylbm_parity_missing_critical_fields",
    "native_citylbm_accuracy_delta_audit",
    "native_citylbm_accuracy_delta_gate",
    "native_citylbm_accuracy_delta_gate_reasons",
    "native_citylbm_accuracy_interpretation",
    "native_citylbm_additional_error_flag",
    "native_citylbm_additional_error_reasons",
    "native_preconditions_accuracy_gate",
    "native_preconditions_accuracy_gate_reasons",
    "native_preconditions_accuracy_top_blocker",
    "native_accuracy_gate",
    "native_accuracy_gate_reasons",
    "native_citylbm_U_RMSE_delta",
    "native_citylbm_U_abs_bias_delta",
    "native_citylbm_U_R2_drop",
    "native_citylbm_U_slope_abs_delta",
    "native_citylbm_U_intercept_abs_delta",
    "probe_mapping_table",
    "probe_mapping_table_sha256",
    "official_measurement_sha256",
    "probe_vtk_source_window_gate",
    "probe_vtk_source_window_reasons",
    "probe_vtk_source_time_steps",
    "probe_vtk_source_step_span",
    "probe_vtk_minimum_step_span",
    "probe_vtk_source_hash_set_count",
    "probe_id_field",
    "probe_tolerance_m",
    "probe_grid_extent_gate",
    "probe_inside_vtk_grid_extent_count",
    "probe_outside_vtk_grid_extent_count",
    "probe_missing_vtk_grid_extent_count",
    "compared_component",
    "component_sensitivity_audit",
    "component_sensitivity_probe_audit_sha256",
    "component_sensitivity_official_sha256",
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
    "component_source_window_gate_reasons",
    "component_source_time_steps",
    "component_source_step_span",
    "component_minimum_source_step_span",
    "component_source_sha256",
    "component_source_time_steps_unique_count",
    "component_source_hash_set_unique_count",
    "component_normalization_gate",
    "component_sensitivity_gate",
    "normalization_scale_gate",
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
    "grid_sensitivity_audit",
    "grid_sensitivity_gate",
    "grid_sensitivity_gate_reasons",
    "grid_sensitivity_run_count",
    "grid_sensitivity_finest_dx_m",
    "grid_sensitivity_next_coarse_dx_m",
    "grid_sensitivity_refinement_ratio",
    "grid_sensitivity_rmse_change_ratio",
    "grid_sensitivity_bias_change_ratio",
    "failed_probe_count_by_tolerance",
    "valid_n",
    "failed_n",
    "official_measurement_count",
    "official_probe_coverage_ratio",
    "missing_official_probe_count",
    "mean_probe_distance_m",
    "max_probe_distance_m",
    "max_official_coordinate_delta_m",
    "official_coordinate_delta_count",
    "U_MAE_ratio",
    "U_RMSE_ratio",
    "U_bias_ratio",
    "U_R2",
    "U_regression_slope",
    "U_regression_intercept",
    "U_max_abs_error",
    "U_mean_sim",
    "U_mean_exp",
    "U_mean_ratio_sim_to_exp",
    "U_mean_relative_bias_ratio",
    "U_best_fit_scale_to_exp",
    "U_best_fit_scale_deviation_ratio",
    "U_scaled_MAE_ratio",
    "U_scaled_RMSE_ratio",
    "U_scaled_improvement_ratio",
    "U_scaled_bias_ratio",
    "U_abs_bias_ratio",
    "U_scale_like_error_flag",
    "bias_diagnosis",
    "k_MAE_m2s2",
    "k_RMSE_m2s2",
    "k_RMSE_ratio",
    "k_bias_m2s2",
    "k_bias_ratio",
    "systematic_bias_flag",
    "protocol_gate",
    "validation_gate_report",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge Data Probe audit rows with official AIJ measurements and compute validation metrics."
    )
    parser.add_argument("--probe-audit", required=True, help="Data Probe audit CSV.")
    parser.add_argument("--official", required=True, help="Official RS/measurement CSV.")
    parser.add_argument("--out", required=True, help="Output metrics CSV path.")
    parser.add_argument("--comparison-out", help="Optional per-probe comparison CSV.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--read-vtk-audit", help="Optional Read VTK Averaging Audit JSON.")
    parser.add_argument("--inlet-profile-audit", help="Optional inlet/empty-tunnel profile audit JSON from audit_inlet_profile_from_vtk.py.")
    parser.add_argument("--inlet-correlation-audit", help="Optional inlet correlation audit JSON from audit_inlet_correlation_from_vtk.py.")
    parser.add_argument("--inlet-source-audit", help="Optional inlet_source_audit.json from audit_inlet_source.py.")
    parser.add_argument("--boundary-source-audit", help="Optional boundary_source_audit.json from audit_boundary_source.py.")
    parser.add_argument("--boundary-protocol-audit", help="Optional boundary_protocol_audit.json from audit_boundary_protocol.py.")
    parser.add_argument("--boundary-runtime-audit", help="Optional boundary_runtime_audit.json from audit_boundary_runtime_from_vtk.py.")
    parser.add_argument("--component-sensitivity-audit", help="Optional component/Uref sensitivity JSON from audit_component_sensitivity.py.")
    parser.add_argument("--grid-sensitivity-audit", help="Optional grid_sensitivity_audit.json from audit_grid_sensitivity.py.")
    parser.add_argument("--native-preconditions-audit", help="Optional native_preconditions_audit.json from audit_native_preconditions.py.")
    parser.add_argument("--native-citylbm-parity-audit", help="Optional native_citylbm_parity_audit.json from audit_native_citylbm_parity.py.")
    parser.add_argument("--native-citylbm-accuracy-delta-audit", help="Optional native_citylbm_accuracy_delta_audit.json from audit_native_citylbm_accuracy_delta.py.")
    parser.add_argument("--case", default="", help="Case label to write and optionally filter official rows.")
    parser.add_argument("--wind-direction", default="", help="Wind direction label to write and optionally filter official rows.")
    parser.add_argument("--software", default="citylbm")
    parser.add_argument("--version", default="0.3.0")
    parser.add_argument("--official-id-column", default="", help="Official probe ID column. Auto-detected when omitted.")
    parser.add_argument("--official-value-column", default="", help="Official measured value column. Auto-detected when omitted.")
    parser.add_argument("--probe-id-column", default="probe_id")
    parser.add_argument("--sim-value-column", default="compared_value")
    parser.add_argument("--u-ref", type=float, default=None, help="Reference velocity, used only for metadata checks.")
    parser.add_argument("--u-ref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--dx", type=float, default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--save-interval", type=int, default=None)
    parser.add_argument("--averaging-window", type=int, default=None)
    parser.add_argument("--source-time-steps", default="")
    parser.add_argument("--mean-speed", type=float, default=None)
    parser.add_argument("--mean-speed-stddev", type=float, default=None)
    parser.add_argument("--max-speed-stddev", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--max-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--profile-csv", default="")
    parser.add_argument("--geometry-scale", default="")
    parser.add_argument("--empty-tunnel-gate", default="")
    parser.add_argument("--empty-tunnel-u-bias-ratio", default="")
    parser.add_argument("--empty-tunnel-k-bias-ratio", default="")
    parser.add_argument("--native-baseline-id", default="")
    parser.add_argument("--native-baseline-gate", default="")
    parser.add_argument(
        "--lbm-stability-gate",
        default="",
        help="Runtime LBM stability evidence gate, e.g. solver_log_no_stability_warnings.",
    )
    parser.add_argument(
        "--solver-stability-warnings",
        default="",
        help="Solver log stability warning summary, e.g. none or no_stability_warnings.",
    )
    parser.add_argument("--k-mae", default="")
    parser.add_argument("--k-rmse", default="")
    parser.add_argument("--k-bias", default="")
    parser.add_argument("--k-bias-ratio", default="")
    parser.add_argument("--systematic-bias-threshold", type=float, default=0.15)
    parser.add_argument("--append", action="store_true", help="Append to metrics CSV if it exists.")
    return parser.parse_args()


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def normalized_probe_id(value: Any) -> str:
    return "".join(ch for ch in str(value).strip().lower() if ch.isalnum())


def find_column(rows: Sequence[Dict[str, str]], candidates: Iterable[str]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    normalized = {norm_key(column): column for column in columns}
    for candidate in candidates:
        found = normalized.get(norm_key(candidate))
        if found:
            return found
    for column in columns:
        ncol = norm_key(column)
        for candidate in candidates:
            if norm_key(candidate) in ncol:
                return column
    return ""


def get_value(row: Dict[str, str], column: str) -> str:
    if not column:
        return ""
    if column in row:
        return row[column]
    target = norm_key(column)
    for key, value in row.items():
        if norm_key(key) == target:
            return value
    return ""


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def as_bool(value: Any) -> Optional[bool]:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "ok", "pass"}:
        return True
    if text in {"false", "0", "no", "n", "fail"}:
        return False
    return None


def as_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def csv_bool(value: Optional[bool]) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return f"{value:.10g}"
    return str(value)


def filter_official(rows: List[Dict[str, str]], case: str, wind_direction: str) -> List[Dict[str, str]]:
    if not rows:
        return rows
    filtered = rows
    case_text = str(case or "").strip().lower()
    wind_text = str(wind_direction or "").strip().lower()
    if case_text:
        case_col = find_column(filtered, ["case", "Case", "condition", "Condition", "bcac"])
        if not case_col:
            raise SystemExit("Official CSV case filter requested, but no case/condition column was detected.")
        filtered = [row for row in filtered if get_value(row, case_col).strip().lower() == case_text]
        if not filtered:
            raise SystemExit(f"Official CSV case filter selected no rows: {case}")
    if wind_text:
        wind_col = find_column(
            filtered,
            ["Wind_direction", "wind_direction", "direction", "Direction", "wind", "Wind"],
        )
        if not wind_col:
            raise SystemExit(
                "Official CSV wind-direction filter requested, but no wind-direction column was detected."
            )
        filtered = [
            row
            for row in filtered
            if get_value(row, wind_col).strip().lower() == wind_text
        ]
        if not filtered:
            raise SystemExit(f"Official CSV wind-direction filter selected no rows: {wind_direction}")
    return filtered


def build_official_lookup(rows: List[Dict[str, str]], id_column: str) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for row in rows:
        probe_id = get_value(row, id_column).strip()
        key = normalized_probe_id(probe_id)
        if not key:
            continue
        if key in lookup:
            raise SystemExit(f"Duplicate official probe ID after normalization: {probe_id}")
        lookup[key] = row
    return lookup


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def rmse(errors: Sequence[float]) -> Optional[float]:
    if not errors:
        return None
    return math.sqrt(sum(error * error for error in errors) / len(errors))


def r2(sim: Sequence[float], exp: Sequence[float]) -> Optional[float]:
    if len(sim) < 2 or len(sim) != len(exp):
        return None
    exp_mean = sum(exp) / len(exp)
    ss_tot = sum((value - exp_mean) ** 2 for value in exp)
    if ss_tot <= 1.0e-15:
        return None
    ss_res = sum((s - e) ** 2 for s, e in zip(sim, exp))
    return 1.0 - ss_res / ss_tot


def regression(sim: Sequence[float], exp: Sequence[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(sim) < 2 or len(sim) != len(exp):
        return None, None
    x_mean = sum(exp) / len(exp)
    y_mean = sum(sim) / len(sim)
    denom = sum((x - x_mean) ** 2 for x in exp)
    if denom <= 1.0e-15:
        return None, None
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(exp, sim)) / denom
    intercept = y_mean - slope * x_mean
    return slope, intercept


def best_scale_to_exp(sim: Sequence[float], exp: Sequence[float]) -> Optional[float]:
    if len(sim) == 0 or len(sim) != len(exp):
        return None
    denom = sum(s * s for s in sim)
    if denom <= 1.0e-15:
        return None
    return sum(s * e for s, e in zip(sim, exp)) / denom


def diagnose_bias(
    u_bias: Optional[float],
    u_rmse: Optional[float],
    scaled_rmse: Optional[float],
    scale: Optional[float],
    slope: Optional[float],
    systematic_threshold: float,
) -> str:
    if u_bias is None or abs(u_bias) < systematic_threshold:
        return ""
    direction = "systematic_underprediction" if u_bias < 0 else "systematic_overprediction"
    scale_text = "" if scale is None else f"best_scale={scale:.6g}"
    if u_rmse is not None and scaled_rmse is not None and u_rmse > 1.0e-12:
        improvement = 1.0 - scaled_rmse / u_rmse
        if improvement >= 0.50 and scale is not None and (scale < 0.80 or scale > 1.20):
            return f"{direction}; scale_like_error; {scale_text}; audit_Uref_units_velocity_component"
        if improvement >= 0.25:
            return f"{direction}; mixed_scale_and_protocol_error; {scale_text}; audit_normalization_then_boundary_inlet"
    if slope is not None and (slope < 0.70 or slope > 1.30):
        return f"{direction}; regression_slope_out_of_range; {scale_text}; audit_component_probe_mapping_boundary"
    return f"{direction}; protocol_or_physics_error_likely; {scale_text}; audit_inlet_boundary_roughness_time_average"


def metadata_field(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def vector_field(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, dict):
            x = value.get("X")
            y = value.get("Y")
            z = value.get("Z")
            if x is not None and y is not None and z is not None:
                return f"({x},{y},{z})"
        if value not in (None, ""):
            return str(value)
    return ""


def nested(metadata: Dict[str, Any], parent: str, key: str) -> str:
    value = metadata.get(parent)
    if isinstance(value, dict):
        child = value.get(key)
        if child not in (None, ""):
            return str(child)
    return ""


def infer_synthetic_inlet_method(metadata: Dict[str, Any]) -> str:
    method = metadata_field(metadata, "SyntheticTurbulentInletMethod", "TurbulenceMethod")
    if method:
        return method
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True:
        return "synthetic-eddy"
    if as_bool(nested(metadata, "RecyclingRescaling", "Enabled")) is True:
        return "recycling-rescaling"
    return ""


def infer_inlet_distribution_treatment(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletDistributionTreatment")
    if explicit:
        return explicit
    method = infer_synthetic_inlet_method(metadata).lower()
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True or "synthetic" in method:
        if as_bool(nested(metadata, "SyntheticEddy", "DeviceSemStressDdf")) is True:
            return "synthetic_eddy_stress_ddf_diagnostic_unverified"
        if as_bool(nested(metadata, "SyntheticEddy", "DeviceSideInlet")) is True:
            return "synthetic_eddy_velocity_field_only"
        return "synthetic_eddy_host_velocity_field_only"
    if "digital" in method:
        return "digital_filter_velocity_field_only_unless_distribution_evidence_archived"
    if "recycling" in method:
        return "recycling_rescaling_velocity_field_only_unless_precursor_evidence_archived"
    if "hash" in method or "random" in method:
        return "uncorrelated_rms_k_velocity_field_only"
    return ""


def infer_inlet_method_class(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "PaperGradeInletMethodClass", "InletMethodClass")
    if explicit:
        return explicit
    method = infer_synthetic_inlet_method(metadata).lower()
    treatment = infer_inlet_distribution_treatment(metadata).lower()
    text = f"{method} {treatment}"
    if "velocity_field_only" in text or "stg-lite" in text or "diagnostic" in text:
        return "diagnostic_velocity_field_only"
    if "precursor" in text:
        return "precursor"
    if "recycling" in text:
        return "recycling_rescaling"
    if "digital_filter" in text or "digital-filter" in text:
        return "digital_filter"
    if "sem_distribution" in text or "synthetic_eddy_distribution_consistent" in text:
        return "synthetic_eddy_distribution_consistent"
    if "dfm_distribution" in text:
        return "dfm"
    return ""


def infer_inlet_method_class_supported(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "InletMethodClassSupported", "PaperGradeInletMethodClassSupported")
    if explicit:
        return explicit
    method_class = infer_inlet_method_class(metadata).lower()
    if not method_class:
        return ""
    supported = any(
        token in method_class
        for token in [
            "digital_filter",
            "dfm",
            "sem",
            "synthetic_eddy_distribution_consistent",
            "precursor",
            "recycling_rescaling",
        ]
    ) and "diagnostic" not in method_class and "velocity_field_only" not in method_class
    return "true" if supported else "false"


def infer_synthetic_update_interval(metadata: Dict[str, Any]) -> str:
    return metadata_field(metadata, "SyntheticTurbulenceUpdateInterval", "InletUpdateInterval")


def infer_synthetic_minimum_recommended_refresh_count(metadata: Dict[str, Any]) -> str:
    return metadata_field(metadata, "SyntheticTurbulenceMinimumRecommendedRefreshes")


def infer_synthetic_expected_final_window_refresh_count(metadata: Dict[str, Any]) -> str:
    return metadata_field(metadata, "SyntheticTurbulenceExpectedFinalWindowRefreshCount")


def infer_synthetic_temporal_sampling_gate(metadata: Dict[str, Any]) -> str:
    return metadata_field(metadata, "SyntheticTurbulentInletTemporalSamplingGate")


def infer_synthetic_correlation_length_m(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulenceCorrelationLengthM")
    if explicit:
        return explicit
    dx = as_float(metadata.get("Dx"))
    lx_cells = as_float(nested(metadata, "SyntheticEddy", "LxCells"))
    if dx is not None and lx_cells is not None:
        return fmt(dx * lx_cells)
    return ""


def infer_inlet_length_scale_source(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletLengthScaleSource")
    if explicit:
        return explicit
    if as_bool(nested(metadata, "SyntheticEddy", "Enabled")) is True:
        return "synthetic_eddy_case_parameter_no_external_length_scale_source"
    if "digital" in infer_synthetic_inlet_method(metadata).lower():
        return "digital_filter_case_parameter_no_external_length_scale_source"
    return ""


def infer_inlet_length_scale_gate(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "SyntheticTurbulentInletLengthScaleGate")
    if explicit:
        return explicit
    source = infer_inlet_length_scale_source(metadata)
    if source:
        return "diagnostic_missing_validated_length_scale_source"
    return ""


def infer_wall_roughness_treatment(metadata: Dict[str, Any]) -> str:
    explicit = metadata_field(metadata, "WallRoughnessTreatment")
    if explicit:
        return explicit
    if as_bool(nested(metadata, "RoughnessLayout", "Enabled")) is False:
        return "roughness_layout_disabled_no_wind_tunnel_source"
    rough_wall = metadata.get("RoughWallDrag") if isinstance(metadata.get("RoughWallDrag"), dict) else {}
    if as_bool(rough_wall.get("VolumeForceEnabled")) is True:
        return "equivalent_rough_wall_drag_diagnostic"
    return ""


def audit_float(audit: Dict[str, Any], key: str) -> Optional[float]:
    return as_float(audit.get(key))


def audit_int(audit: Dict[str, Any], key: str) -> Optional[int]:
    value = audit.get(key)
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def audit_source_steps(audit: Dict[str, Any]) -> str:
    csv_value = audit.get("source_time_steps_csv")
    if csv_value not in (None, ""):
        return str(csv_value)
    steps = audit.get("source_time_steps")
    if isinstance(steps, list):
        return ",".join(str(step) for step in steps)
    return ""


def audit_field(audit: Dict[str, Any], key: str) -> str:
    value = audit.get(key)
    if value not in (None, ""):
        return str(value)
    return ""


def audit_list_field(audit: Dict[str, Any], key: str) -> str:
    value = audit.get(key)
    if isinstance(value, list):
        return ";".join(str(item) for item in value if str(item).strip())
    if value not in (None, ""):
        return str(value)
    return ""


def normalize_source_steps_text(text: Any) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    parts = [part for part in raw.replace(";", ",").replace(" ", ",").split(",") if part.strip()]
    return ",".join(parts)


def source_step_count(text: str) -> int:
    normalized = normalize_source_steps_text(text)
    return len([part for part in normalized.split(",") if part.strip()])


def source_step_span_from_text(text: str) -> Optional[int]:
    normalized = normalize_source_steps_text(text)
    steps = [as_int(part) for part in normalized.split(",") if part.strip()]
    if len(steps) < 2 or any(step is None for step in steps):
        return None
    return int(steps[-1]) - int(steps[0])


def audit_gate(audit: Dict[str, Any], key: str) -> str:
    value = audit.get(key)
    return str(value).strip().lower() if value not in (None, "") else ""


def first_int(*values: Optional[int]) -> Optional[int]:
    for value in values:
        if value is not None:
            return value
    return None


def first_float(*values: Optional[float]) -> Optional[float]:
    for value in values:
        if value is not None:
            return value
    return None


def first_text(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def first_bool_text(*values: Any) -> str:
    for value in values:
        parsed = as_bool(value)
        if parsed is not None:
            return csv_bool(parsed)
    return ""


def main() -> int:
    args = parse_args()
    probe_path = Path(args.probe_audit).resolve()
    official_path = Path(args.official).resolve()
    out_path = Path(args.out).resolve()
    comparison_path = Path(args.comparison_out).resolve() if args.comparison_out else None
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
    read_vtk_audit = read_json(Path(args.read_vtk_audit).resolve() if args.read_vtk_audit else None)
    inlet_profile_audit = read_json(Path(args.inlet_profile_audit).resolve() if args.inlet_profile_audit else None)
    inlet_correlation_audit = read_json(Path(args.inlet_correlation_audit).resolve() if args.inlet_correlation_audit else None)
    inlet_source_audit = read_json(Path(args.inlet_source_audit).resolve() if args.inlet_source_audit else None)
    boundary_source_audit = read_json(Path(args.boundary_source_audit).resolve() if args.boundary_source_audit else None)
    boundary_protocol_audit = read_json(Path(args.boundary_protocol_audit).resolve() if args.boundary_protocol_audit else None)
    boundary_runtime_audit = read_json(Path(args.boundary_runtime_audit).resolve() if args.boundary_runtime_audit else None)
    component_sensitivity_audit = read_json(Path(args.component_sensitivity_audit).resolve() if args.component_sensitivity_audit else None)
    grid_sensitivity_audit = read_json(Path(args.grid_sensitivity_audit).resolve() if args.grid_sensitivity_audit else None)
    native_preconditions_audit = read_json(Path(args.native_preconditions_audit).resolve() if args.native_preconditions_audit else None)
    native_citylbm_parity_audit = read_json(Path(args.native_citylbm_parity_audit).resolve() if args.native_citylbm_parity_audit else None)
    native_citylbm_accuracy_delta_audit = read_json(Path(args.native_citylbm_accuracy_delta_audit).resolve() if args.native_citylbm_accuracy_delta_audit else None)

    probe_rows = read_csv(probe_path)
    official_rows = filter_official(read_csv(official_path), args.case, args.wind_direction)
    if not probe_rows:
        raise SystemExit("Probe audit CSV has no rows.")
    if not official_rows:
        raise SystemExit("Official measurement CSV has no matching rows.")

    official_id_col = args.official_id_column or find_column(official_rows, ["No.", "No", "probe_id", "id", "point"])
    official_value_col = args.official_value_column or find_column(
        official_rows,
        ["Velocity_Ratio", "velocity_ratio", "V_exp_ratio", "U_exp_ratio", "U", "Velocity", "WindSpeed"],
    )
    if not official_id_col:
        raise SystemExit("Could not detect official probe ID column. Use --official-id-column.")
    if not official_value_col:
        raise SystemExit("Could not detect official measured value column. Use --official-value-column.")

    source_time_steps = audit_source_steps(read_vtk_audit)
    if not source_time_steps:
        source_time_steps = audit_source_steps(inlet_profile_audit)
    if not source_time_steps:
        source_time_steps = args.source_time_steps
    minimum_average_step_span = first_int(
        audit_int(read_vtk_audit, "minimum_validation_average_step_span"),
        audit_int(inlet_profile_audit, "minimum_validation_average_step_span"),
    )

    official = build_official_lookup(official_rows, official_id_col)
    sim_values: List[float] = []
    exp_values: List[float] = []
    errors: List[float] = []
    abs_errors: List[float] = []
    distances: List[float] = []
    official_coordinate_deltas: List[float] = []
    comparison_rows: List[Dict[str, Any]] = []
    failed = 0
    normalization_values: List[bool] = []
    wind_values: List[bool] = []
    probe_urefs: List[float] = []
    compared_component = ""
    compared_components: List[str] = []
    tolerance = ""
    probe_source_steps_values: List[str] = []
    probe_source_step_spans: List[int] = []
    probe_minimum_step_spans: List[int] = []
    probe_source_hash_sets: List[str] = []
    probe_missing_source_steps = 0
    probe_missing_source_step_spans = 0
    probe_missing_minimum_step_spans = 0
    probe_missing_source_hashes = 0
    probe_hash_count_mismatches = 0
    probe_inside_grid_extent_count = 0
    probe_outside_grid_extent_count = 0
    probe_missing_grid_extent_count = 0
    matched_official_probe_ids = set()

    for row in probe_rows:
        probe_id = get_value(row, args.probe_id_column).strip()
        probe_key = normalized_probe_id(probe_id)
        official_row = official.get(probe_key)
        status = get_value(row, "failed").strip().lower()
        validation_status = get_value(row, "validation_status").strip().lower()
        if not official_row:
            failed += 1
            continue
        inside_grid = as_bool(get_value(row, "inside_vtk_grid_extent"))
        if inside_grid is True:
            probe_inside_grid_extent_count += 1
        elif inside_grid is False:
            probe_outside_grid_extent_count += 1
        else:
            probe_missing_grid_extent_count += 1
        sim = as_float(get_value(row, args.sim_value_column))
        exp = as_float(get_value(official_row, official_value_col))
        failed_flag = as_bool(status)
        if failed_flag is True or "fail" in validation_status or sim is None or exp is None:
            failed += 1
            continue
        matched_official_probe_ids.add(probe_key)
        sim_values.append(sim)
        exp_values.append(exp)
        error = sim - exp
        errors.append(error)
        abs_errors.append(abs(error))
        distance = as_float(get_value(row, "nearest_distance"))
        if distance is not None:
            distances.append(distance)
        coord_deltas = []
        for coord in ["x", "y", "z"]:
            sim_coord = as_float(get_value(row, coord))
            official_coord = as_float(get_value(official_row, coord))
            if sim_coord is not None and official_coord is not None:
                coord_deltas.append(abs(sim_coord - official_coord))
        coordinate_delta = max(coord_deltas) if coord_deltas else None
        if coordinate_delta is not None:
            official_coordinate_deltas.append(coordinate_delta)
        normalized = as_bool(get_value(row, "normalization_valid"))
        wind_valid = as_bool(get_value(row, "wind_direction_valid"))
        if normalized is not None:
            normalization_values.append(normalized)
        if wind_valid is not None:
            wind_values.append(wind_valid)
        row_uref = as_float(get_value(row, "Uref"))
        if row_uref is not None:
            probe_urefs.append(row_uref)
        if not compared_component:
            compared_component = get_value(row, "compared_component")
        row_compared_component = get_value(row, "compared_component").strip().lower()
        if row_compared_component:
            compared_components.append(row_compared_component)
        if not tolerance:
            tolerance = get_value(row, "tolerance")
        probe_source_steps = normalize_source_steps_text(get_value(row, "vtk_source_time_steps"))
        if probe_source_steps:
            probe_source_steps_values.append(probe_source_steps)
        else:
            probe_missing_source_steps += 1
        probe_source_step_span = as_int(get_value(row, "vtk_source_step_span"))
        if probe_source_step_span is None:
            probe_missing_source_step_spans += 1
        else:
            probe_source_step_spans.append(probe_source_step_span)
        probe_minimum_step_span = as_int(get_value(row, "minimum_validation_average_step_span"))
        if probe_minimum_step_span is None:
            probe_missing_minimum_step_spans += 1
        else:
            probe_minimum_step_spans.append(probe_minimum_step_span)
        probe_source_hashes = [
            part.strip()
            for part in get_value(row, "vtk_source_sha256").replace(",", ";").split(";")
            if part.strip()
        ]
        if probe_source_hashes:
            probe_source_hash_sets.append(";".join(probe_source_hashes))
        else:
            probe_missing_source_hashes += 1
        if probe_source_steps and probe_source_hashes and len(probe_source_hashes) != source_step_count(probe_source_steps):
            probe_hash_count_mismatches += 1
        comparison_rows.append(
            {
                "probe_id": probe_id,
                "sim_value": sim,
                "official_value": exp,
                "error": error,
                "abs_error": abs(error),
                "nearest_distance": distance,
                "official_coordinate_delta": coordinate_delta,
                "compared_component": get_value(row, "compared_component"),
                "normalization_valid": get_value(row, "normalization_valid"),
                "wind_direction_valid": get_value(row, "wind_direction_valid"),
            }
        )

    valid_n = len(sim_values)
    if valid_n == 0:
        raise SystemExit("No valid matched probes after filtering failed rows.")
    official_probe_ids = set(official.keys())
    official_measurement_count = len(official_probe_ids)
    missing_official_probe_count = len(official_probe_ids - matched_official_probe_ids)
    official_probe_coverage_ratio = (
        len(matched_official_probe_ids) / official_measurement_count
        if official_measurement_count
        else None
    )

    u_mae = mean(abs_errors)
    u_rmse = rmse(errors)
    u_bias = mean(errors)
    u_r2 = r2(sim_values, exp_values)
    slope, intercept = regression(sim_values, exp_values)
    max_abs = max(abs_errors) if abs_errors else None
    mean_sim = mean(sim_values)
    mean_exp = mean(exp_values)
    mean_ratio = mean_sim / mean_exp if mean_sim is not None and mean_exp is not None and abs(mean_exp) > 1.0e-15 else None
    mean_relative_bias = mean_ratio - 1.0 if mean_ratio is not None else None
    best_scale = best_scale_to_exp(sim_values, exp_values)
    best_scale_deviation = best_scale - 1.0 if best_scale is not None else None
    scaled_errors = [best_scale * s - e for s, e in zip(sim_values, exp_values)] if best_scale is not None else []
    scaled_abs_errors = [abs(error) for error in scaled_errors]
    scaled_mae = mean(scaled_abs_errors)
    scaled_rmse = rmse(scaled_errors)
    scaled_bias = mean(scaled_errors)
    scaled_improvement = (
        1.0 - scaled_rmse / u_rmse
        if scaled_rmse is not None and u_rmse is not None and u_rmse > 1.0e-12
        else None
    )
    abs_bias = abs(u_bias) if u_bias is not None else None
    scale_like_error = (
        scaled_improvement is not None
        and scaled_improvement >= 0.25
        and best_scale_deviation is not None
        and abs(best_scale_deviation) > 0.20
    )
    bias_diagnosis = diagnose_bias(u_bias, u_rmse, scaled_rmse, best_scale, slope, args.systematic_bias_threshold)
    systematic_flag = ""
    if u_bias is not None and abs(u_bias) >= args.systematic_bias_threshold:
        systematic_flag = "underprediction" if u_bias < 0 else "overprediction"
    unique_compared_components = sorted(set(compared_components))
    component_consistency_gate = (
        "pass"
        if len(unique_compared_components) == 1 and bool(unique_compared_components[0])
        else "fail_mixed_or_missing_compared_component"
    )
    normalization_gate_value = all(normalization_values) if normalization_values else None
    wind_gate_value = all(wind_values) if wind_values else None
    unique_probe_urefs = sorted({round(value, 12) for value in probe_urefs})
    probe_uref_mismatch_count = 0
    if args.u_ref is not None:
        probe_uref_mismatch_count = sum(
            1 for value in probe_urefs if abs(value - args.u_ref) > args.u_ref_tolerance
        )
    inferred_uref = args.u_ref
    if inferred_uref is None:
        if len(unique_probe_urefs) == 1:
            inferred_uref = probe_urefs[0]
        else:
            inferred_uref = as_float(
                metadata_field(metadata, "ReferenceWindSpeedMps", "ReferenceWindSpeed", "UrefMps", "Uref")
            )
    inferred_zref = args.z_ref
    if inferred_zref is None:
        inferred_zref = as_float(metadata_field(metadata, "ReferenceHeightM", "ZrefM", "ReferenceHeight"))
    coordinate_delta_count = len(official_coordinate_deltas)
    max_coordinate_delta = max(official_coordinate_deltas) if official_coordinate_deltas else None
    unique_probe_source_steps = sorted(set(probe_source_steps_values))
    unique_probe_source_step_spans = sorted(set(probe_source_step_spans))
    unique_probe_minimum_step_spans = sorted(set(probe_minimum_step_spans))
    unique_probe_source_hash_sets = sorted(set(probe_source_hash_sets))
    expected_probe_source_steps = normalize_source_steps_text(source_time_steps)
    expected_probe_source_step_span = source_step_span_from_text(expected_probe_source_steps)
    probe_source_reasons: List[str] = []
    if not expected_probe_source_steps:
        probe_source_reasons.append("missing_expected_source_time_steps")
    if expected_probe_source_step_span is None:
        probe_source_reasons.append("missing_expected_source_step_span")
    if probe_missing_source_steps:
        probe_source_reasons.append(f"missing_probe_source_steps:{probe_missing_source_steps}")
    if probe_missing_source_step_spans:
        probe_source_reasons.append(f"missing_probe_source_step_spans:{probe_missing_source_step_spans}")
    if probe_missing_minimum_step_spans:
        probe_source_reasons.append(f"missing_probe_minimum_step_spans:{probe_missing_minimum_step_spans}")
    if len(unique_probe_source_steps) != 1:
        probe_source_reasons.append(f"mixed_probe_source_steps:{len(unique_probe_source_steps)}")
    elif expected_probe_source_steps and unique_probe_source_steps[0] != expected_probe_source_steps:
        probe_source_reasons.append("probe_source_steps_do_not_match_metrics_source_time_steps")
    if len(unique_probe_source_step_spans) != 1:
        probe_source_reasons.append(f"mixed_probe_source_step_spans:{len(unique_probe_source_step_spans)}")
    elif expected_probe_source_step_span is not None and unique_probe_source_step_spans[0] != expected_probe_source_step_span:
        probe_source_reasons.append("probe_source_step_span_does_not_match_metrics_source_time_steps")
    elif minimum_average_step_span is not None and unique_probe_source_step_spans[0] < minimum_average_step_span:
        probe_source_reasons.append("probe_source_step_span_below_minimum_validation_average_step_span")
    if len(unique_probe_minimum_step_spans) != 1:
        probe_source_reasons.append(f"mixed_probe_minimum_step_spans:{len(unique_probe_minimum_step_spans)}")
    elif minimum_average_step_span is not None and unique_probe_minimum_step_spans[0] != minimum_average_step_span:
        probe_source_reasons.append("probe_minimum_step_span_does_not_match_metrics_minimum_step_span")
    if probe_missing_source_hashes:
        probe_source_reasons.append(f"missing_probe_source_hashes:{probe_missing_source_hashes}")
    if probe_hash_count_mismatches:
        probe_source_reasons.append(f"probe_source_hash_count_mismatch:{probe_hash_count_mismatches}")
    if len(unique_probe_source_hash_sets) != 1:
        probe_source_reasons.append(f"mixed_probe_source_hash_sets:{len(unique_probe_source_hash_sets)}")
    probe_source_window_gate = "pass" if not probe_source_reasons else "fail"
    probe_grid_extent_gate = (
        "pass"
        if probe_outside_grid_extent_count == 0 and probe_missing_grid_extent_count == 0
        else "fail"
    )
    protocol_failures: List[str] = []
    if probe_source_window_gate != "pass":
        protocol_failures.append("fail_probe_vtk_source_window")
    if probe_grid_extent_gate != "pass":
        protocol_failures.append("fail_probe_vtk_grid_extent")
    if args.u_ref is None and len(unique_probe_urefs) > 1:
        protocol_failures.append("fail_mixed_probe_uref")
    if args.u_ref is not None and probe_uref_mismatch_count > 0:
        protocol_failures.append("fail_probe_uref_mismatch")
    if component_consistency_gate != "pass":
        protocol_failures.append(component_consistency_gate)
    if normalization_gate_value is not True:
        protocol_failures.append("fail_missing_or_invalid_uref_normalization")
    if wind_gate_value is not True:
        protocol_failures.append("fail_missing_or_invalid_wind_direction")
    if coordinate_delta_count != valid_n:
        protocol_failures.append("fail_incomplete_official_coordinate_audit")
    elif max_coordinate_delta is None or max_coordinate_delta > 1.0e-6:
        protocol_failures.append("fail_probe_coordinate_mismatch")
    if missing_official_probe_count > 0 or valid_n != official_measurement_count:
        protocol_failures.append("fail_incomplete_official_probe_coverage")
    if failed > 0:
        protocol_failures.append("fail_unmatched_or_failed_probes")
    metrics_protocol_gate = (
        "metrics_ready_for_validation_gate"
        if not protocol_failures
        else ";".join(protocol_failures)
    )

    boundary_audit = metadata.get("BoundaryProtocolAudit") if isinstance(metadata.get("BoundaryProtocolAudit"), dict) else {}
    blockage_audit = boundary_audit.get("BlockageDiagnostics") if isinstance(boundary_audit.get("BlockageDiagnostics"), dict) else {}
    boundary_missing_fields = boundary_protocol_audit.get("missing_evidence_fields")
    if isinstance(boundary_missing_fields, list):
        boundary_missing_fields_text = ";".join(str(field) for field in boundary_missing_fields)
    else:
        boundary_missing_fields_text = str(boundary_missing_fields or "")
    averaging_window = first_int(
        audit_int(read_vtk_audit, "averaged_frame_count"),
        audit_int(inlet_profile_audit, "frame_count"),
        args.averaging_window,
    )
    averaged_frame_shortfall = first_int(
        audit_int(read_vtk_audit, "averaged_frame_shortfall"),
        audit_int(inlet_profile_audit, "averaged_frame_shortfall"),
    )
    available_frame_count = first_int(
        audit_int(read_vtk_audit, "available_frame_count"),
        audit_int(inlet_profile_audit, "available_frame_count"),
    )
    requested_time_steps = audit_int(read_vtk_audit, "requested_time_steps")
    requested_vtk_save_interval = audit_int(read_vtk_audit, "requested_vtk_save_interval")
    requested_vtk_save_start_step = audit_int(read_vtk_audit, "requested_vtk_save_start_step")
    requested_vtk_frame_count = audit_int(read_vtk_audit, "requested_vtk_frame_count")
    requested_vtk_frame_shortfall = audit_int(read_vtk_audit, "requested_vtk_frame_shortfall")
    requested_vtk_expected_final_window_time_steps = first_text(
        read_vtk_audit.get("requested_vtk_expected_final_window_time_steps_csv")
    )
    requested_vtk_expected_final_window_step_span = audit_int(
        read_vtk_audit, "requested_vtk_expected_final_window_step_span"
    )
    requested_vtk_averaging_window_shortfall = audit_int(
        read_vtk_audit, "requested_vtk_averaging_window_shortfall"
    )
    requested_vtk_expected_final_window_step_span_shortfall = audit_int(
        read_vtk_audit, "requested_vtk_expected_final_window_step_span_shortfall"
    )
    requested_vtk_minimum_step_span = audit_int(read_vtk_audit, "requested_vtk_minimum_step_span")
    requested_vtk_frame_gate = first_text(read_vtk_audit.get("requested_vtk_frame_gate"))
    requested_vtk_frame_gate_reasons = first_text(read_vtk_audit.get("requested_vtk_frame_gate_reasons_csv"))
    run_freshness_gate = first_text(read_vtk_audit.get("run_freshness_gate"))
    run_freshness_gate_reasons = first_text(read_vtk_audit.get("run_freshness_gate_reasons_csv"))
    source_first_time_step = first_int(
        audit_int(read_vtk_audit, "source_first_time_step"),
        audit_int(inlet_profile_audit, "source_first_time_step"),
    )
    source_last_time_step = first_int(
        audit_int(read_vtk_audit, "source_last_time_step"),
        audit_int(inlet_profile_audit, "source_last_time_step"),
    )
    source_step_span = first_int(
        audit_int(read_vtk_audit, "source_step_span"),
        audit_int(inlet_profile_audit, "source_step_span"),
    )
    if source_step_span is None and source_first_time_step is not None and source_last_time_step is not None:
        source_step_span = source_last_time_step - source_first_time_step
    source_step_span_shortfall = first_int(
        audit_int(read_vtk_audit, "source_step_span_shortfall"),
        audit_int(inlet_profile_audit, "source_step_span_shortfall"),
    )
    minimum_average_step_span = first_int(
        audit_int(read_vtk_audit, "minimum_validation_average_step_span"),
        audit_int(inlet_profile_audit, "minimum_validation_average_step_span"),
    )
    latest_available_time_step = first_int(
        audit_int(read_vtk_audit, "latest_available_time_step"),
        audit_int(inlet_profile_audit, "latest_available_time_step"),
    )
    selected_last_window = first_bool_text(
        read_vtk_audit.get("selected_last_window"),
        inlet_profile_audit.get("selected_last_window"),
    )
    source_steps_strictly_increasing = first_bool_text(
        read_vtk_audit.get("source_steps_strictly_increasing"),
        inlet_profile_audit.get("source_steps_strictly_increasing"),
    )
    source_step_spacing_uniform = first_bool_text(
        read_vtk_audit.get("source_step_spacing_uniform"),
        inlet_profile_audit.get("source_step_spacing_uniform"),
    )
    time_averaging_gate = first_text(
        read_vtk_audit.get("time_averaging_gate"),
        inlet_profile_audit.get("time_averaging_gate"),
    )
    time_averaging_gate_reasons = first_text(
        read_vtk_audit.get("time_averaging_gate_reasons_csv"),
        inlet_profile_audit.get("time_averaging_gate_reasons_csv"),
    )
    mean_speed = args.mean_speed if args.mean_speed is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_mps"),
        audit_float(inlet_profile_audit, "mean_speed_mps"),
    )
    mean_speed_stddev = args.mean_speed_stddev if args.mean_speed_stddev is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_stddev_mps"),
        audit_float(inlet_profile_audit, "mean_speed_stddev_mps"),
    )
    max_speed_stddev = args.max_speed_stddev if args.max_speed_stddev is not None else first_float(
        audit_float(read_vtk_audit, "max_speed_stddev_mps"),
        audit_float(inlet_profile_audit, "max_speed_stddev_mps"),
    )
    mean_speed_stddev_ratio = args.mean_speed_stddev_ratio if args.mean_speed_stddev_ratio is not None else first_float(
        audit_float(read_vtk_audit, "mean_speed_stddev_ratio"),
        audit_float(inlet_profile_audit, "mean_speed_stddev_ratio"),
    )
    max_speed_stddev_ratio = args.max_speed_stddev_ratio if args.max_speed_stddev_ratio is not None else first_float(
        audit_float(read_vtk_audit, "max_speed_stddev_ratio"),
        audit_float(inlet_profile_audit, "max_speed_stddev_ratio"),
    )
    final_window_stationarity_gate = first_text(
        read_vtk_audit.get("final_window_stationarity_gate"),
        inlet_profile_audit.get("final_window_stationarity_gate"),
    )
    final_window_mean_speed_drift_ratio = first_float(
        audit_float(read_vtk_audit, "final_window_mean_speed_drift_ratio"),
        audit_float(inlet_profile_audit, "final_window_mean_speed_drift_ratio"),
    )
    max_final_window_mean_speed_drift_ratio = first_float(
        audit_float(read_vtk_audit, "max_final_window_mean_speed_drift_ratio"),
        audit_float(inlet_profile_audit, "max_final_window_mean_speed_drift_ratio"),
    )
    speed_statistics_cli_override = any(
        value is not None
        for value in [
            args.mean_speed_stddev,
            args.max_speed_stddev,
            args.mean_speed_stddev_ratio,
            args.max_speed_stddev_ratio,
        ]
    )
    audit_speed_statistics_source = first_text(
        read_vtk_audit.get("mean_speed_statistics_source"),
        inlet_profile_audit.get("mean_speed_statistics_source"),
    )
    if speed_statistics_cli_override:
        mean_speed_statistics_source = "cli"
    elif audit_speed_statistics_source:
        mean_speed_statistics_source = audit_speed_statistics_source
    elif mean_speed_stddev_ratio is not None and max_speed_stddev_ratio is not None and (read_vtk_audit or inlet_profile_audit):
        mean_speed_statistics_source = "sampled_vtk"
    else:
        mean_speed_statistics_source = ""
    inlet_profile_gate = audit_gate(inlet_profile_audit, "inlet_profile_gate")
    inlet_u_profile_gate = audit_gate(inlet_profile_audit, "inlet_u_profile_gate")
    inlet_k_profile_gate = audit_gate(inlet_profile_audit, "inlet_k_profile_gate")
    inlet_streamwise_direction_gate = audit_gate(inlet_profile_audit, "inlet_streamwise_direction_gate")
    inlet_negative_streamwise_fraction = audit_float(inlet_profile_audit, "negative_streamwise_fraction")
    inlet_u_mae_ratio = audit_float(inlet_profile_audit, "U_MAE_ratio")
    inlet_u_rmse_ratio = audit_float(inlet_profile_audit, "U_RMSE_ratio")
    inlet_k_mae_ratio = audit_float(inlet_profile_audit, "k_MAE_ratio")
    inlet_k_rmse_ratio = audit_float(inlet_profile_audit, "k_RMSE_ratio")
    inlet_u_bias_ratio = audit_float(inlet_profile_audit, "U_bias_ratio")
    inlet_k_bias_ratio = audit_float(inlet_profile_audit, "k_bias_ratio")
    inlet_k_mae = audit_float(inlet_profile_audit, "k_MAE_m2s2")
    inlet_k_rmse = audit_float(inlet_profile_audit, "k_RMSE_m2s2")
    inlet_k_bias = audit_float(inlet_profile_audit, "k_bias_m2s2")
    profile_csv_sha256 = metadata_field(metadata, "WindProfileCsvSha256")
    if not profile_csv_sha256 and args.profile_csv:
        profile_path = Path(args.profile_csv).expanduser()
        if profile_path.exists():
            profile_csv_sha256 = sha256_file(profile_path.resolve())
    metrics = {field: "" for field in TEMPLATE_FIELDS}
    metrics.update(
        {
            "case": args.case,
            "wind_direction": args.wind_direction,
            "software": args.software,
            "version": args.version,
            "dx_m": fmt(args.dx),
            "steps": fmt(args.steps),
            "save_interval": fmt(args.save_interval),
            "averaging_window": fmt(averaging_window),
            "averaged_frame_shortfall": fmt(averaged_frame_shortfall),
            "available_frame_count": fmt(available_frame_count),
            "vtk_pattern": audit_field(read_vtk_audit, "vtk_pattern") or audit_field(inlet_profile_audit, "vtk_pattern"),
            "requested_time_steps": fmt(requested_time_steps),
            "requested_vtk_save_interval": fmt(requested_vtk_save_interval),
            "requested_vtk_save_start_step": fmt(requested_vtk_save_start_step),
            "requested_vtk_frame_count": fmt(requested_vtk_frame_count),
            "requested_vtk_frame_shortfall": fmt(requested_vtk_frame_shortfall),
            "requested_vtk_expected_final_window_time_steps": requested_vtk_expected_final_window_time_steps,
            "requested_vtk_expected_final_window_step_span": fmt(requested_vtk_expected_final_window_step_span),
            "requested_vtk_averaging_window_shortfall": fmt(requested_vtk_averaging_window_shortfall),
            "requested_vtk_expected_final_window_step_span_shortfall": fmt(requested_vtk_expected_final_window_step_span_shortfall),
            "requested_vtk_minimum_step_span": fmt(requested_vtk_minimum_step_span),
            "requested_vtk_frame_gate": requested_vtk_frame_gate,
            "requested_vtk_frame_gate_reasons": requested_vtk_frame_gate_reasons,
            "run_freshness_gate": run_freshness_gate,
            "run_freshness_gate_reasons": run_freshness_gate_reasons,
            "latest_reference_mtime_utc": first_text(read_vtk_audit.get("latest_reference_mtime_utc")),
            "oldest_selected_vtk_mtime_utc": first_text(read_vtk_audit.get("oldest_selected_vtk_mtime_utc")),
            "source_time_steps": source_time_steps,
            "source_first_time_step": fmt(source_first_time_step),
            "source_last_time_step": fmt(source_last_time_step),
            "source_step_span": fmt(source_step_span),
            "source_step_span_shortfall": fmt(source_step_span_shortfall),
            "minimum_validation_average_step_span": fmt(minimum_average_step_span),
            "latest_available_time_step": fmt(latest_available_time_step),
            "selected_last_window": selected_last_window,
            "source_steps_strictly_increasing": source_steps_strictly_increasing,
            "source_step_spacing_uniform": source_step_spacing_uniform,
            "time_averaging_gate": time_averaging_gate,
            "time_averaging_gate_reasons": time_averaging_gate_reasons,
            "mean_speed_mps": fmt(mean_speed),
            "mean_speed_stddev_mps": fmt(mean_speed_stddev),
            "max_speed_stddev_mps": fmt(max_speed_stddev),
            "mean_speed_stddev_ratio": fmt(mean_speed_stddev_ratio),
            "max_speed_stddev_ratio": fmt(max_speed_stddev_ratio),
            "final_window_stationarity_gate": final_window_stationarity_gate,
            "final_window_mean_speed_drift_ratio": fmt(final_window_mean_speed_drift_ratio),
            "max_final_window_mean_speed_drift_ratio": fmt(max_final_window_mean_speed_drift_ratio),
            "mean_speed_statistics_source": mean_speed_statistics_source,
            "profile_csv": args.profile_csv,
            "profile_csv_sha256": profile_csv_sha256,
            "custom_profile_rows": metadata_field(metadata, "CustomProfileRows"),
            "custom_profile_k_rows": metadata_field(metadata, "CustomProfileKRows"),
            "custom_profile_k_complete": metadata_field(metadata, "CustomProfileKComplete"),
            "profile_first_z_m": metadata_field(metadata, "ProfileFirstZM"),
            "profile_last_z_m": metadata_field(metadata, "ProfileLastZM"),
            "profile_k_min_m2s2": metadata_field(metadata, "KMinM2s2"),
            "profile_k_max_m2s2": metadata_field(metadata, "KMaxM2s2"),
            "profile_k_min_lbm": metadata_field(metadata, "KMinLbm"),
            "profile_k_max_lbm": metadata_field(metadata, "KMaxLbm"),
            "geometry_scale": args.geometry_scale,
            "geometry_unit_assumption": metadata_field(metadata, "GeometryPhysicalUnitAssumption"),
            "geometry_scale_evidence_gate": metadata_field(metadata, "GeometryScaleEvidenceGate"),
            "geometry_scale_expected_casee_note": metadata_field(metadata, "GeometryScaleExpectedCaseENote"),
            "geometry_building_count": metadata_field(metadata, "GeometryBuildingCount"),
            "geometry_building_height_m": metadata_field(metadata, "GeometryBuildingHeightM"),
            "Uref_mps": fmt(inferred_uref),
            "Zref_m": fmt(inferred_zref),
            "target_max_profile_velocity_lbm": metadata_field(metadata, "TargetMaxProfileVelocityLbm"),
            "estimated_max_profile_mach": metadata_field(metadata, "EstimatedMaxProfileMach"),
            "lbm_tau": metadata_field(metadata, "LbmTau"),
            "lbm_nu": metadata_field(metadata, "LbmNu"),
            "physical_viscosity_m2s": metadata_field(metadata, "PhysicalViscosityM2s"),
            "estimated_reynolds_number": metadata_field(metadata, "EstimatedReynoldsNumber"),
            "velocity_set": metadata_field(metadata, "VelocitySet"),
            "les_model": metadata_field(metadata, "LesModel"),
            "smagorinsky_cs": metadata_field(metadata, "SmagorinskyCs"),
            "solver_stability_warnings": args.solver_stability_warnings or audit_field(read_vtk_audit, "solver_stability_warnings") or metadata_field(metadata, "SolverStabilityWarnings"),
            "lbm_stability_gate": args.lbm_stability_gate or audit_field(read_vtk_audit, "lbm_stability_gate") or metadata_field(metadata, "LbmStabilityGate"),
            "normalization_valid": csv_bool(normalization_gate_value),
            "velocity_component": compared_component,
            "compared_component_consistency_gate": component_consistency_gate,
            "compared_component_unique_values": ";".join(unique_compared_components),
            "wind_vector": vector_field(metadata, "WindDirectionUnitVector", "WindDirection", "wind_vector"),
            "wind_direction_valid": csv_bool(wind_gate_value),
            "inlet_face": nested(metadata, "BoundaryProtocolAudit", "InletFace"),
            "outlet_face": nested(metadata, "BoundaryProtocolAudit", "OutletFace"),
            "lateral_faces": nested(metadata, "BoundaryProtocolAudit", "LateralFaces"),
            "domain_size_x_m": nested(boundary_audit, "DomainSizeM", "X"),
            "domain_size_y_m": nested(boundary_audit, "DomainSizeM", "Y"),
            "domain_size_z_m": nested(boundary_audit, "DomainSizeM", "Z"),
            "max_building_height_m": nested(boundary_audit, "BuildingBoundsM", "Height"),
            "upstream_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Upstream"),
            "downstream_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Downstream"),
            "min_lateral_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "MinLateral"),
            "top_clearance_h": nested(boundary_audit, "ClearanceByBuildingHeight", "Top"),
            "approx_frontal_blockage_ratio": blockage_audit.get("ApproxFrontalBlockageRatio", ""),
            "approx_plan_blockage_ratio": blockage_audit.get("ApproxPlanBlockageRatio", ""),
            "blockage_protocol_gate": blockage_audit.get("Gate", ""),
            "boundary_protocol_gate": str(boundary_protocol_audit.get("boundary_protocol_gate", "")) or str(boundary_audit.get("Gate", "")),
            "boundary_evidence_source": str(boundary_protocol_audit.get("boundary_evidence_source", "")) or metadata_field(metadata, "BoundaryProtocolEvidenceSource") or boundary_audit.get("ProtocolEvidenceSource", ""),
            "boundary_evidence_gate": str(boundary_protocol_audit.get("boundary_evidence_gate", "")) or metadata_field(metadata, "BoundaryProtocolEvidenceGate") or boundary_audit.get("ProtocolEvidenceGate", ""),
            "boundary_protocol_audit": str(Path(args.boundary_protocol_audit).resolve()) if args.boundary_protocol_audit else "",
            "boundary_protocol_metadata_sha256": str(boundary_protocol_audit.get("metadata_sha256", "")),
            "boundary_evidence_json_sha256": str(boundary_protocol_audit.get("boundary_evidence_json_sha256", "")),
            "boundary_run_identity_gate": str(boundary_protocol_audit.get("boundary_run_identity_gate", "")),
            "boundary_run_identity_gate_reasons": ";".join(
                str(reason) for reason in boundary_protocol_audit.get("boundary_run_identity_gate_reasons", [])
            )
            if isinstance(boundary_protocol_audit.get("boundary_run_identity_gate_reasons"), list)
            else str(boundary_protocol_audit.get("boundary_run_identity_gate_reasons", "")),
            "boundary_expected_aij_case": str(boundary_protocol_audit.get("expected_aij_case", "")),
            "boundary_expected_wind_direction": str(boundary_protocol_audit.get("expected_wind_direction", "")),
            "boundary_evidence_aij_case": str(boundary_protocol_audit.get("evidence_aij_case", "")),
            "boundary_evidence_wind_direction": str(boundary_protocol_audit.get("evidence_wind_direction", "")),
            "boundary_evidence_case_metadata_sha256": str(boundary_protocol_audit.get("evidence_case_metadata_sha256", "")),
            "boundary_evidence_metadata_sha256_matches_current": csv_bool(
                boundary_protocol_audit.get("evidence_metadata_sha256_matches_current")
            ),
            "boundary_missing_evidence_fields": boundary_missing_fields_text,
            "boundary_equivalence_basis": str(boundary_protocol_audit.get("boundary_equivalence_basis", "")),
            "boundary_equivalence_supported": csv_bool(boundary_protocol_audit.get("boundary_equivalence_supported")),
            "boundary_evidence_class": str(boundary_protocol_audit.get("boundary_evidence_class", "")),
            "boundary_evidence_class_supported": csv_bool(boundary_protocol_audit.get("boundary_evidence_class_supported")),
            "boundary_evidence_files_all_exist": csv_bool(boundary_protocol_audit.get("boundary_evidence_files_all_exist")),
            "boundary_evidence_files_all_hashed": csv_bool(boundary_protocol_audit.get("boundary_evidence_files_all_hashed")),
            "boundary_condition_fields_supported": csv_bool(boundary_protocol_audit.get("boundary_condition_fields_supported")),
            "boundary_condition_support_reasons": ";".join(
                str(reason) for reason in boundary_protocol_audit.get("boundary_condition_support_reasons", [])
            )
            if isinstance(boundary_protocol_audit.get("boundary_condition_support_reasons"), list)
            else str(boundary_protocol_audit.get("boundary_condition_support_reasons", "")),
            "inlet_boundary_supported": csv_bool(boundary_protocol_audit.get("inlet_boundary_supported")),
            "outlet_boundary_supported": csv_bool(boundary_protocol_audit.get("outlet_boundary_supported")),
            "lateral_boundary_supported": csv_bool(boundary_protocol_audit.get("lateral_boundary_supported")),
            "top_boundary_supported": csv_bool(boundary_protocol_audit.get("top_boundary_supported")),
            "ground_wall_treatment_supported": csv_bool(boundary_protocol_audit.get("ground_wall_treatment_supported")),
            "roughness_treatment_supported": csv_bool(boundary_protocol_audit.get("roughness_treatment_supported")),
            "floor_roughness_source_supported": csv_bool(boundary_protocol_audit.get("floor_roughness_source_supported")),
            "blockage_source_supported": csv_bool(boundary_protocol_audit.get("blockage_source_supported")),
            "fetch_clearance_source_supported": csv_bool(boundary_protocol_audit.get("fetch_clearance_source_supported")),
            "outlet_reflection_check_supported": csv_bool(boundary_protocol_audit.get("outlet_reflection_check_supported")),
            "side_top_boundary_check_supported": csv_bool(boundary_protocol_audit.get("side_top_boundary_check_supported")),
            "clearance_numeric_gate": str(boundary_protocol_audit.get("clearance_numeric_gate", "")),
            "boundary_clearance_reasons": ";".join(
                str(reason) for reason in boundary_protocol_audit.get("clearance_numeric_gate_reasons", [])
            )
            if isinstance(boundary_protocol_audit.get("clearance_numeric_gate_reasons"), list)
            else str(boundary_protocol_audit.get("clearance_numeric_gate_reasons", "")),
            "boundary_summary": metadata_field(metadata, "BoundaryConditionSummary"),
            "boundary_source_audit": str(Path(args.boundary_source_audit).resolve()) if args.boundary_source_audit else "",
            "boundary_source_gate": audit_gate(boundary_source_audit, "boundary_source_gate"),
            "boundary_source_gate_reasons": ";".join(
                str(reason) for reason in boundary_source_audit.get("boundary_source_gate_reasons", [])
            )
            if isinstance(boundary_source_audit.get("boundary_source_gate_reasons"), list)
            else audit_field(boundary_source_audit, "boundary_source_gate_reasons_csv"),
            "paper_grade_boundary_source_gate": audit_gate(boundary_source_audit, "paper_grade_boundary_source_gate"),
            "paper_grade_boundary_source_gate_reasons": ";".join(
                str(reason) for reason in boundary_source_audit.get("paper_grade_boundary_source_gate_reasons", [])
            )
            if isinstance(boundary_source_audit.get("paper_grade_boundary_source_gate_reasons"), list)
            else audit_field(boundary_source_audit, "paper_grade_boundary_source_gate_reasons_csv"),
            "boundary_source_method_class": audit_field(boundary_source_audit, "boundary_source_method_class"),
            "boundary_source_coherent": first_bool_text(boundary_source_audit.get("boundary_source_coherent")),
            "boundary_source_simplified": first_bool_text(boundary_source_audit.get("boundary_source_simplified")),
            "boundary_source_wind_tunnel_equivalent": first_bool_text(
                boundary_source_audit.get("boundary_source_wind_tunnel_equivalent")
            ),
            "boundary_source_advanced_code_evidence": first_bool_text(
                boundary_source_audit.get("boundary_source_advanced_code_evidence")
            ),
            "boundary_source_comment_stripped_code_audit": first_bool_text(
                boundary_source_audit.get("advanced_boundary_evidence_uses_comment_stripped_code")
            ),
            "boundary_source_has_non_reflecting_outlet_method": first_bool_text(
                boundary_source_audit.get("has_non_reflecting_outlet_method")
            ),
            "boundary_source_has_non_reflecting_outlet_state_evidence": first_bool_text(
                boundary_source_audit.get("has_non_reflecting_outlet_state_evidence")
            ),
            "boundary_source_has_periodic_side_top_method": first_bool_text(
                boundary_source_audit.get("has_periodic_side_top_method")
            ),
            "boundary_source_has_periodic_pair_mapping_evidence": first_bool_text(
                boundary_source_audit.get("has_periodic_pair_mapping_evidence")
            ),
            "boundary_source_has_rough_wall_function_method": first_bool_text(
                boundary_source_audit.get("has_rough_wall_function_method")
            ),
            "boundary_source_has_rough_wall_parameter_evidence": first_bool_text(
                boundary_source_audit.get("has_rough_wall_parameter_evidence")
            ),
            "boundary_source_has_rough_wall_action_evidence": first_bool_text(
                boundary_source_audit.get("has_rough_wall_action_evidence")
            ),
            "boundary_source_has_precursor_or_recycling_boundary_method": first_bool_text(
                boundary_source_audit.get("has_precursor_or_recycling_boundary_method")
            ),
            "boundary_source_has_precursor_or_recycling_boundary_field_evidence": first_bool_text(
                boundary_source_audit.get("has_precursor_or_recycling_boundary_field_evidence")
            ),
            "boundary_source_has_empty_advanced_boundary_method_stub": first_bool_text(
                boundary_source_audit.get("has_empty_advanced_boundary_method_stub")
            ),
            "boundary_source_empty_advanced_boundary_method_stub_count": fmt(
                audit_int(boundary_source_audit, "empty_advanced_boundary_method_stub_count")
            ),
            "boundary_source_has_paper_grade_outlet_source": first_bool_text(
                boundary_source_audit.get("has_paper_grade_outlet_source")
            ),
            "boundary_source_has_paper_grade_side_top_source": first_bool_text(
                boundary_source_audit.get("has_paper_grade_side_top_source")
            ),
            "boundary_source_has_paper_grade_rough_wall_source": first_bool_text(
                boundary_source_audit.get("has_paper_grade_rough_wall_source")
            ),
            "boundary_source_has_paper_grade_development_source": first_bool_text(
                boundary_source_audit.get("has_paper_grade_development_source")
            ),
            "boundary_source_missing_paper_grade_source_evidence": ";".join(
                str(reason) for reason in boundary_source_audit.get("missing_paper_grade_source_evidence", [])
            )
            if isinstance(boundary_source_audit.get("missing_paper_grade_source_evidence"), list)
            else audit_field(boundary_source_audit, "missing_paper_grade_source_evidence"),
            "boundary_type_e_velocity_initialization": first_bool_text(
                boundary_source_audit.get("has_type_e_velocity_initialization")
            ),
            "boundary_type_e_velocity_initialization_guard": first_bool_text(
                boundary_source_audit.get("has_type_e_velocity_initialization_guard")
            ),
            "boundary_type_e_velocity_initialization_coordinates": first_bool_text(
                boundary_source_audit.get("has_type_e_velocity_initialization_coordinates")
            ),
            "boundary_type_e_velocity_initialization_velocity_write": first_bool_text(
                boundary_source_audit.get("has_type_e_velocity_initialization_velocity_write")
            ),
            "boundary_type_e_velocity_initialization_before_device_upload": first_bool_text(
                boundary_source_audit.get("has_type_e_velocity_initialization_before_device_upload")
            ),
            "boundary_flags_device_upload_after_type_e_velocity_initialization": first_bool_text(
                boundary_source_audit.get("has_flags_device_upload_after_type_e_velocity_initialization")
            ),
            "boundary_u_device_upload_after_type_e_velocity_initialization": first_bool_text(
                boundary_source_audit.get("has_u_device_upload_after_type_e_velocity_initialization")
            ),
            "boundary_profile_type_e_velocity_initialization": first_bool_text(
                boundary_source_audit.get("has_profile_type_e_velocity_initialization")
            ),
            "boundary_uniform_type_e_velocity_initialization": first_bool_text(
                boundary_source_audit.get("has_uniform_type_e_velocity_initialization")
            ),
            "boundary_velocity_initialization_metadata_applied": metadata_field(
                metadata, "BoundaryTypeEVelocityInitializationApplied"
            ),
            "boundary_velocity_initialization_metadata_treatment": metadata_field(
                metadata, "BoundaryTypeEVelocityInitializationTreatment"
            ),
            "boundary_velocity_initialization_metadata_profile_aware": metadata_field(
                metadata, "BoundaryTypeEVelocityInitializationProfileAware"
            ),
            "boundary_velocity_initialization_metadata_device_upload_order": metadata_field(
                metadata, "BoundaryTypeEVelocityInitializationDeviceUploadOrder"
            ),
            "boundary_velocity_initialization_metadata_paper_grade_status": metadata_field(
                metadata, "BoundaryVelocityInitializationPaperGradeStatus"
            ),
            "boundary_source_setup_sha256": audit_field(boundary_source_audit, "setup_cpp_sha256"),
            "boundary_runtime_audit": str(Path(args.boundary_runtime_audit).resolve()) if args.boundary_runtime_audit else "",
            "boundary_runtime_gate": audit_gate(boundary_runtime_audit, "boundary_runtime_gate"),
            "boundary_runtime_gate_reasons": ";".join(
                str(reason) for reason in boundary_runtime_audit.get("boundary_runtime_gate_reasons", [])
            )
            if isinstance(boundary_runtime_audit.get("boundary_runtime_gate_reasons"), list)
            else audit_field(boundary_runtime_audit, "boundary_runtime_gate_reasons"),
            "boundary_runtime_traceability_gate": audit_gate(boundary_runtime_audit, "boundary_runtime_traceability_gate"),
            "boundary_runtime_profile_preservation_gate": audit_gate(
                boundary_runtime_audit, "boundary_runtime_profile_preservation_gate"
            ),
            "boundary_runtime_inlet_gate": audit_gate(boundary_runtime_audit, "boundary_runtime_inlet_gate"),
            "boundary_runtime_side_top_gate": audit_gate(boundary_runtime_audit, "boundary_runtime_side_top_gate"),
            "boundary_runtime_side_top_normal_leakage_gate": audit_gate(
                boundary_runtime_audit, "boundary_runtime_side_top_normal_leakage_gate"
            ),
            "boundary_runtime_outlet_gate": audit_gate(boundary_runtime_audit, "boundary_runtime_outlet_gate"),
            "boundary_runtime_max_u_mae_ratio": audit_field(boundary_runtime_audit, "max_boundary_u_mae_ratio"),
            "boundary_runtime_inlet_u_mae_ratio": audit_field(boundary_runtime_audit, "inlet_u_mae_ratio"),
            "boundary_runtime_outlet_u_mae_ratio": audit_field(boundary_runtime_audit, "outlet_u_mae_ratio"),
            "boundary_runtime_side_top_max_u_mae_ratio": audit_field(boundary_runtime_audit, "side_top_max_u_mae_ratio"),
            "boundary_runtime_max_side_top_normal_velocity_ratio": audit_field(
                boundary_runtime_audit, "max_side_top_normal_velocity_ratio"
            ),
            "boundary_runtime_max_side_top_normal_abs_mps": audit_field(
                boundary_runtime_audit, "max_side_top_normal_abs_mps"
            ),
            "boundary_runtime_max_negative_streamwise_fraction": audit_field(
                boundary_runtime_audit, "max_boundary_negative_streamwise_fraction"
            ),
            "boundary_runtime_source_step_span": audit_field(boundary_runtime_audit, "source_step_span"),
            "boundary_runtime_frame_count": audit_field(boundary_runtime_audit, "frame_count"),
            "inlet_source_audit": str(Path(args.inlet_source_audit).resolve()) if args.inlet_source_audit else "",
            "inlet_source_gate": audit_gate(inlet_source_audit, "inlet_source_gate"),
            "inlet_source_gate_reasons": ";".join(
                str(reason) for reason in inlet_source_audit.get("inlet_source_gate_reasons", [])
            )
            if isinstance(inlet_source_audit.get("inlet_source_gate_reasons"), list)
            else audit_field(inlet_source_audit, "inlet_source_gate_reasons_csv"),
            "paper_grade_inlet_source_gate": audit_gate(inlet_source_audit, "paper_grade_inlet_source_gate"),
            "paper_grade_inlet_source_gate_reasons": ";".join(
                str(reason) for reason in inlet_source_audit.get("paper_grade_inlet_source_gate_reasons", [])
            )
            if isinstance(inlet_source_audit.get("paper_grade_inlet_source_gate_reasons"), list)
            else audit_field(inlet_source_audit, "paper_grade_inlet_source_gate_reasons_csv"),
            "inlet_source_method_class": audit_field(inlet_source_audit, "inlet_source_method_class"),
            "inlet_source_distribution_consistent": first_bool_text(
                inlet_source_audit.get("inlet_source_distribution_consistent")
            ),
            "inlet_source_velocity_field_only": first_bool_text(
                inlet_source_audit.get("inlet_source_velocity_field_only")
            ),
            "inlet_source_advanced_code_evidence": first_bool_text(
                inlet_source_audit.get("inlet_source_advanced_code_evidence")
            ),
            "inlet_source_comment_stripped_code_audit": first_bool_text(
                inlet_source_audit.get("inlet_source_comment_stripped_code_audit")
            ),
            "inlet_source_defines_hpp": audit_field(inlet_source_audit, "defines_hpp"),
            "inlet_source_defines_hpp_sha256": audit_field(inlet_source_audit, "defines_hpp_sha256"),
            "inlet_source_defines_hpp_audited": first_bool_text(
                inlet_source_audit.get("defines_hpp_audited")
            ),
            "inlet_source_has_equilibrium_boundaries_define": first_bool_text(
                inlet_source_audit.get("has_equilibrium_boundaries_define")
            ),
            "inlet_source_has_type_e_equilibrium_boundary_route": first_bool_text(
                inlet_source_audit.get("has_type_e_equilibrium_boundary_route")
            ),
            "inlet_source_distribution_route": audit_field(inlet_source_audit, "inlet_distribution_route"),
            "inlet_source_distribution_route_gate": audit_gate(inlet_source_audit, "inlet_distribution_route_gate"),
            "inlet_source_has_distribution_function_write": first_bool_text(
                inlet_source_audit.get("has_distribution_function_write")
            ),
            "inlet_source_distribution_function_write_count": audit_field(
                inlet_source_audit, "distribution_function_write_count"
            ),
            "inlet_source_has_inlet_distribution_reconstruction": first_bool_text(
                inlet_source_audit.get("has_inlet_distribution_reconstruction")
            ),
            "inlet_source_inlet_distribution_reconstruction_count": audit_field(
                inlet_source_audit, "inlet_distribution_reconstruction_count"
            ),
            "inlet_source_has_inlet_length_scale_evidence": first_bool_text(
                inlet_source_audit.get("has_inlet_length_scale_evidence")
            ),
            "inlet_source_metadata_length_scale_gate": audit_field(
                inlet_source_audit, "metadata_length_scale_gate"
            ),
            "inlet_source_has_reynolds_stress_tensor_evidence": first_bool_text(
                inlet_source_audit.get("has_reynolds_stress_tensor_evidence")
            ),
            "inlet_source_has_documented_isotropic_k_assumption": first_bool_text(
                inlet_source_audit.get("has_documented_isotropic_k_assumption")
            ),
            "inlet_source_reynolds_stress_treatment": audit_field(
                inlet_source_audit, "reynolds_stress_treatment"
            ),
            "inlet_source_metadata_reynolds_stress_treatment": audit_field(
                inlet_source_audit, "metadata_reynolds_stress_treatment"
            ),
            "inlet_source_has_digital_filter_evidence": first_bool_text(
                inlet_source_audit.get("has_digital_filter_evidence")
            ),
            "inlet_source_has_digital_filter_kernel_evidence": first_bool_text(
                inlet_source_audit.get("has_digital_filter_kernel_evidence")
            ),
            "inlet_source_has_digital_filter_state_evidence": first_bool_text(
                inlet_source_audit.get("has_digital_filter_state_evidence")
            ),
            "inlet_source_has_sem_evidence": first_bool_text(
                inlet_source_audit.get("has_sem_evidence")
            ),
            "inlet_source_has_sem_eddy_population_evidence": first_bool_text(
                inlet_source_audit.get("has_sem_eddy_population_evidence")
            ),
            "inlet_source_has_precursor_or_recycling_evidence": first_bool_text(
                inlet_source_audit.get("has_precursor_or_recycling_evidence")
            ),
            "inlet_source_has_precursor_recycling_field_evidence": first_bool_text(
                inlet_source_audit.get("has_precursor_recycling_field_evidence")
            ),
            "inlet_source_distribution_consistency_basis": audit_field(
                inlet_source_audit, "distribution_consistency_basis"
            ),
            "inlet_source_setup_sha256": audit_field(inlet_source_audit, "setup_cpp_sha256"),
            "inlet_source_synthetic_requested": first_bool_text(
                inlet_source_audit.get("synthetic_inlet_requested")
            ),
            "inlet_source_has_synthetic_function": first_bool_text(
                inlet_source_audit.get("has_synthetic_inlet_function")
            ),
            "inlet_source_has_three_component_velocity_write": first_bool_text(
                inlet_source_audit.get("has_three_component_velocity_write")
            ),
            "inlet_source_has_three_component_fluctuation_evidence": first_bool_text(
                inlet_source_audit.get("has_three_component_fluctuation_evidence")
            ),
            "inlet_source_has_k_driven_three_component_stg": first_bool_text(
                inlet_source_audit.get("has_k_driven_three_component_stg")
            ),
            "inlet_source_has_mean_preserving_inlet_correction": first_bool_text(
                inlet_source_audit.get("has_mean_preserving_inlet_correction")
            ),
            "inlet_source_has_layerwise_mean_preserving_inlet_correction": first_bool_text(
                inlet_source_audit.get("has_layerwise_mean_preserving_inlet_correction")
            ),
            "inlet_source_spectral_mode_count": audit_field(
                inlet_source_audit, "synthetic_inlet_spectral_mode_count"
            ),
            "inlet_source_refresh_with_current_time": first_bool_text(
                inlet_source_audit.get("has_synthetic_inlet_refresh_with_current_time")
            ),
            "inlet_source_update_interval_run_control": first_bool_text(
                inlet_source_audit.get("has_update_interval_run_control")
            ),
            "inlet_source_segmented_stg_run_loop": first_bool_text(
                inlet_source_audit.get("has_segmented_stg_run_loop")
            ),
            "inlet_source_has_streamwise_clipping_control": first_bool_text(
                inlet_source_audit.get("has_streamwise_clipping_control")
            ),
            "inlet_source_streamwise_min_fraction": audit_field(
                inlet_source_audit, "streamwise_min_fraction"
            ),
            "inlet_source_streamwise_clipping_enabled": first_bool_text(
                inlet_source_audit.get("streamwise_clipping_enabled")
            ),
            "inlet_source_has_legacy_hardcoded_streamwise_clipping": first_bool_text(
                inlet_source_audit.get("has_legacy_hardcoded_streamwise_clipping")
            ),
            "inlet_source_has_uncorrelated_random_inlet": first_bool_text(
                inlet_source_audit.get("has_uncorrelated_random_inlet")
            ),
            "inlet_source_uncorrelated_random_patterns": audit_list_field(
                inlet_source_audit, "uncorrelated_random_inlet_patterns"
            ),
            "inlet_source_correlation_model": audit_field(
                inlet_source_audit, "synthetic_inlet_correlation_model"
            ),
            "inlet_source_recommended_next_action": audit_field(
                inlet_source_audit, "recommended_next_action"
            ),
            "synthetic_inlet_method": infer_synthetic_inlet_method(metadata),
            "inlet_distribution_treatment": infer_inlet_distribution_treatment(metadata),
            "inlet_method_class": infer_inlet_method_class(metadata),
            "inlet_method_class_supported": infer_inlet_method_class_supported(metadata),
            "wall_roughness_treatment": infer_wall_roughness_treatment(metadata),
            "synthetic_mode_count": metadata_field(metadata, "SyntheticTurbulenceModeCount"),
            "synthetic_update_interval": infer_synthetic_update_interval(metadata),
            "synthetic_minimum_recommended_refresh_count": infer_synthetic_minimum_recommended_refresh_count(metadata),
            "synthetic_expected_final_window_refresh_count": infer_synthetic_expected_final_window_refresh_count(metadata),
            "synthetic_temporal_sampling_gate": infer_synthetic_temporal_sampling_gate(metadata),
            "synthetic_max_fraction": metadata_field(metadata, "SyntheticTurbulenceMaxFractionOfMean"),
            "synthetic_min_streamwise_fraction": first_text(
                metadata_field(metadata, "SyntheticTurbulenceMinStreamwiseFraction"),
                audit_field(inlet_source_audit, "streamwise_min_fraction"),
            ),
            "synthetic_streamwise_clipping_enabled": first_bool_text(
                metadata.get("SyntheticTurbulenceStreamwiseClippingEnabled"),
                inlet_source_audit.get("streamwise_clipping_enabled"),
            ),
            "synthetic_legacy_hardcoded_streamwise_clipping": first_bool_text(
                inlet_source_audit.get("has_legacy_hardcoded_streamwise_clipping")
            ),
            "synthetic_component_norm_x": nested(metadata, "SyntheticTurbulentInletComponentRmsNormalization", "X"),
            "synthetic_component_norm_y": nested(metadata, "SyntheticTurbulentInletComponentRmsNormalization", "Y"),
            "synthetic_component_norm_z": nested(metadata, "SyntheticTurbulentInletComponentRmsNormalization", "Z"),
            "synthetic_correlation_length_m": infer_synthetic_correlation_length_m(metadata),
            "inlet_length_scale_source": infer_inlet_length_scale_source(metadata),
            "inlet_length_scale_gate": infer_inlet_length_scale_gate(metadata),
            "inlet_correlation_audit": str(Path(args.inlet_correlation_audit).resolve()) if args.inlet_correlation_audit else "",
            "inlet_correlation_gate": audit_gate(inlet_correlation_audit, "inlet_correlation_gate"),
            "inlet_temporal_lag1_correlation": fmt(audit_float(inlet_correlation_audit, "temporal_lag1_mean_correlation")),
            "inlet_temporal_lag1_abs_correlation": fmt(audit_float(inlet_correlation_audit, "temporal_lag1_abs_mean_correlation")),
            "inlet_spatial_adjacent_correlation": fmt(audit_float(inlet_correlation_audit, "spatial_adjacent_mean_correlation")),
            "inlet_temporal_integral_positive_lag_count": fmt(audit_int(inlet_correlation_audit, "temporal_integral_positive_lag_count")),
            "inlet_temporal_integral_time_steps": fmt(audit_int(inlet_correlation_audit, "temporal_integral_time_steps")),
            "inlet_spatial_integral_positive_lag_count": fmt(audit_int(inlet_correlation_audit, "spatial_integral_positive_lag_count")),
            "inlet_spatial_integral_length_cells": fmt(audit_int(inlet_correlation_audit, "spatial_integral_length_cells")),
            "inlet_spatial_integral_length_m": fmt(audit_float(inlet_correlation_audit, "spatial_integral_length_m")),
            "inlet_min_temporal_integral_lag_count": fmt(audit_int(inlet_correlation_audit, "min_temporal_integral_lag_count")),
            "inlet_min_spatial_integral_lag_count": fmt(audit_int(inlet_correlation_audit, "min_spatial_integral_lag_count")),
            "inlet_streamwise_fluctuation_variance": fmt(audit_float(inlet_correlation_audit, "mean_streamwise_fluctuation_variance")),
            "inlet_k_variance_gate": audit_gate(inlet_correlation_audit, "inlet_k_variance_gate"),
            "inlet_streamwise_variance_target_from_k": fmt(audit_float(inlet_correlation_audit, "inlet_streamwise_variance_target_from_k")),
            "inlet_streamwise_variance_to_k_ratio": fmt(audit_float(inlet_correlation_audit, "inlet_streamwise_variance_to_k_ratio")),
            "inlet_tke_gate": audit_gate(inlet_correlation_audit, "inlet_tke_gate"),
            "inlet_tke_target_from_af_k": fmt(audit_float(inlet_correlation_audit, "inlet_tke_target_from_af_k")),
            "inlet_tke_to_k_ratio": fmt(audit_float(inlet_correlation_audit, "inlet_tke_to_k_ratio")),
            "inlet_mean_turbulent_kinetic_energy_from_components": fmt(
                audit_float(inlet_correlation_audit, "mean_turbulent_kinetic_energy_from_components")
            ),
            "inlet_temporal_finite_correlation_fraction": fmt(audit_float(inlet_correlation_audit, "temporal_finite_correlation_fraction")),
            "inlet_spatial_finite_correlation_fraction": fmt(audit_float(inlet_correlation_audit, "spatial_finite_correlation_fraction")),
            "inlet_correlation_frame_count": fmt(audit_int(inlet_correlation_audit, "frame_count")),
            "inlet_correlation_source_time_steps": audit_source_steps(inlet_correlation_audit),
            "inlet_correlation_source_step_span": fmt(audit_int(inlet_correlation_audit, "source_step_span")),
            "inlet_correlation_minimum_step_span": fmt(audit_int(inlet_correlation_audit, "minimum_validation_average_step_span")),
            "inlet_correlation_selected_last_window": first_bool_text(inlet_correlation_audit.get("selected_last_window")),
            "inlet_correlation_source_steps_strictly_increasing": first_bool_text(inlet_correlation_audit.get("source_steps_strictly_increasing")),
            "inlet_correlation_source_step_spacing_uniform": first_bool_text(inlet_correlation_audit.get("source_step_spacing_uniform")),
            "inlet_profile_audit": str(Path(args.inlet_profile_audit).resolve()) if args.inlet_profile_audit else "",
            "inlet_profile_available_frame_count": fmt(audit_int(inlet_profile_audit, "available_frame_count")),
            "inlet_profile_frame_count": fmt(audit_int(inlet_profile_audit, "frame_count")),
            "inlet_profile_source_time_steps": audit_source_steps(inlet_profile_audit),
            "inlet_profile_source_first_time_step": fmt(audit_int(inlet_profile_audit, "source_first_time_step")),
            "inlet_profile_source_last_time_step": fmt(audit_int(inlet_profile_audit, "source_last_time_step")),
            "inlet_profile_source_step_span": fmt(audit_int(inlet_profile_audit, "source_step_span")),
            "inlet_profile_minimum_step_span": fmt(audit_int(inlet_profile_audit, "minimum_validation_average_step_span")),
            "inlet_profile_latest_available_time_step": fmt(audit_int(inlet_profile_audit, "latest_available_time_step")),
            "inlet_profile_selected_last_window": first_bool_text(inlet_profile_audit.get("selected_last_window")),
            "inlet_profile_source_steps_strictly_increasing": first_bool_text(inlet_profile_audit.get("source_steps_strictly_increasing")),
            "inlet_profile_source_step_spacing_uniform": first_bool_text(inlet_profile_audit.get("source_step_spacing_uniform")),
            "inlet_profile_time_averaging_gate": audit_gate(inlet_profile_audit, "time_averaging_gate"),
            "inlet_profile_time_averaging_gate_reasons": ";".join(
                str(reason) for reason in inlet_profile_audit.get("time_averaging_gate_reasons", [])
            )
            if isinstance(inlet_profile_audit.get("time_averaging_gate_reasons"), list)
            else str(inlet_profile_audit.get("time_averaging_gate_reasons", "")),
            "inlet_negative_streamwise_fraction": fmt(inlet_negative_streamwise_fraction),
            "inlet_streamwise_direction_gate": inlet_streamwise_direction_gate,
            "inlet_profile_gate": inlet_profile_gate,
            "inlet_u_profile_gate": inlet_u_profile_gate,
            "inlet_u_mae_ratio": fmt(inlet_u_mae_ratio),
            "inlet_u_rmse_ratio": fmt(inlet_u_rmse_ratio),
            "inlet_k_profile_gate": inlet_k_profile_gate,
            "inlet_k_mae_ratio": fmt(inlet_k_mae_ratio),
            "inlet_k_rmse_ratio": fmt(inlet_k_rmse_ratio),
            "empty_tunnel_gate": args.empty_tunnel_gate or inlet_profile_gate,
            "empty_tunnel_U_bias_ratio": args.empty_tunnel_u_bias_ratio or fmt(inlet_u_bias_ratio),
            "empty_tunnel_k_bias_ratio": args.empty_tunnel_k_bias_ratio or fmt(inlet_k_bias_ratio),
            "native_fluidx3d_baseline_id": args.native_baseline_id,
            "native_baseline_gate": args.native_baseline_gate,
            "native_preconditions_audit": str(Path(args.native_preconditions_audit).resolve()) if args.native_preconditions_audit else "",
            "native_preconditions_gate": audit_gate(native_preconditions_audit, "native_preconditions_gate"),
            "native_preconditions_gate_reasons": ";".join(
                str(reason) for reason in native_preconditions_audit.get("native_preconditions_gate_reasons", [])
            )
            if isinstance(native_preconditions_audit.get("native_preconditions_gate_reasons"), list)
            else audit_field(native_preconditions_audit, "native_preconditions_gate_reasons_csv"),
            "native_preconditions_protocol_identity_gate": audit_gate(
                native_preconditions_audit, "native_preconditions_protocol_identity_gate"
            ),
            "native_preconditions_time_average_gate": audit_gate(
                native_preconditions_audit, "native_preconditions_time_average_gate"
            ),
            "native_preconditions_time_average_evidence_gate": audit_gate(
                native_preconditions_audit, "native_preconditions_time_average_evidence_gate"
            ),
            "native_preconditions_time_average_evidence_gate_reasons": audit_field(
                native_preconditions_audit, "native_preconditions_time_average_evidence_gate_reasons_csv"
            ),
            "native_preconditions_expected_uref_mps": fmt(
                audit_float(native_preconditions_audit, "expected_uref_mps")
            ),
            "native_preconditions_actual_uref_mps": fmt(
                audit_float(native_preconditions_audit, "actual_uref_mps")
            ),
            "native_preconditions_expected_zref_m": fmt(
                audit_float(native_preconditions_audit, "expected_zref_m")
            ),
            "native_preconditions_af_uref_at_zref_mps": fmt(
                audit_float(native_preconditions_audit, "af_uref_at_zref_mps")
            ),
            "native_preconditions_uref_af_profile_delta_mps": fmt(
                audit_float(native_preconditions_audit, "uref_af_profile_delta_mps")
            ),
            "native_preconditions_metadata_uref_af_profile_delta_mps": fmt(
                audit_float(native_preconditions_audit, "metadata_uref_af_profile_delta_mps")
            ),
            "native_preconditions_runtime_selected_last_window": first_bool_text(
                native_preconditions_audit.get("runtime_selected_last_window")
            ),
            "native_preconditions_runtime_source_vtk_sha256_count": fmt(
                audit_int(native_preconditions_audit, "runtime_source_vtk_sha256_count")
            ),
            "native_preconditions_runtime_source_vtk_sha256_unique_count": fmt(
                audit_int(native_preconditions_audit, "runtime_source_vtk_sha256_unique_count")
            ),
            "native_preconditions_runtime_final_window_stationarity_gate": audit_gate(
                native_preconditions_audit, "runtime_final_window_stationarity_gate"
            ),
            "native_preconditions_runtime_final_window_mean_speed_drift_ratio": audit_field(
                native_preconditions_audit, "runtime_final_window_mean_speed_drift_ratio"
            ),
            "native_preconditions_runtime_max_final_window_mean_speed_drift_ratio": audit_field(
                native_preconditions_audit, "runtime_max_final_window_mean_speed_drift_ratio"
            ),
            "native_component_sensitivity_hash_traceability_gate": audit_gate(
                native_preconditions_audit, "component_sensitivity_hash_traceability_gate"
            ),
            "native_component_sensitivity_hash_traceability_gate_reasons": audit_field(
                native_preconditions_audit, "component_sensitivity_hash_traceability_gate_reasons_csv"
            ),
            "native_component_sensitivity_probe_audit_sha256_matches_current": first_bool_text(
                native_preconditions_audit.get("component_sensitivity_probe_audit_sha256_matches_current")
            ),
            "native_component_sensitivity_official_sha256_matches_current": first_bool_text(
                native_preconditions_audit.get("component_sensitivity_official_sha256_matches_current")
            ),
            "native_component_sensitivity_probe_audit_sha256": audit_field(
                native_preconditions_audit, "component_sensitivity_probe_audit_sha256"
            ),
            "native_component_sensitivity_official_sha256": audit_field(
                native_preconditions_audit, "component_sensitivity_official_sha256"
            ),
            "native_preconditions_probe_audit_sha256": audit_field(
                native_preconditions_audit, "probe_audit_sha256"
            ),
            "native_preconditions_official_measurement_sha256": audit_field(
                native_preconditions_audit, "official_measurement_sha256"
            ),
            "native_inlet_equivalence_gate": audit_gate(
                native_preconditions_audit, "native_inlet_equivalence_gate"
            ),
            "native_inlet_equivalence_gate_reasons": audit_field(
                native_preconditions_audit, "native_inlet_equivalence_gate_reasons_csv"
            ),
            "native_inlet_profile_audit": audit_field(native_preconditions_audit, "inlet_profile_audit"),
            "native_inlet_profile_gate": audit_gate(native_preconditions_audit, "inlet_profile_gate"),
            "native_inlet_u_profile_gate": audit_gate(native_preconditions_audit, "inlet_u_profile_gate"),
            "native_inlet_k_profile_gate": audit_gate(native_preconditions_audit, "inlet_k_profile_gate"),
            "native_inlet_profile_time_averaging_gate": audit_gate(
                native_preconditions_audit, "inlet_profile_time_averaging_gate"
            ),
            "native_inlet_profile_af_csv_sha256_matches_expected": first_bool_text(
                native_preconditions_audit.get("inlet_profile_af_csv_sha256_matches_expected")
            ),
            "native_inlet_profile_source_time_steps_match_runtime": first_bool_text(
                native_preconditions_audit.get("inlet_profile_source_time_steps_match_runtime")
            ),
            "native_inlet_profile_source_vtk_sha256_match_runtime": first_bool_text(
                native_preconditions_audit.get("inlet_profile_source_vtk_sha256_match_runtime")
            ),
            "native_inlet_profile_source_step_span": fmt(
                audit_int(native_preconditions_audit, "inlet_profile_source_step_span")
            ),
            "native_inlet_profile_minimum_step_span": fmt(
                audit_int(native_preconditions_audit, "inlet_profile_minimum_step_span")
            ),
            "native_inlet_correlation_audit": audit_field(native_preconditions_audit, "inlet_correlation_audit"),
            "native_inlet_correlation_gate": audit_gate(native_preconditions_audit, "inlet_correlation_gate"),
            "native_inlet_k_variance_gate": audit_gate(native_preconditions_audit, "inlet_k_variance_gate"),
            "native_inlet_streamwise_variance_target_from_k": fmt(
                audit_float(native_preconditions_audit, "inlet_streamwise_variance_target_from_k")
            ),
            "native_inlet_streamwise_variance_to_k_ratio": fmt(
                audit_float(native_preconditions_audit, "inlet_streamwise_variance_to_k_ratio")
            ),
            "native_inlet_tke_gate": audit_gate(native_preconditions_audit, "inlet_tke_gate"),
            "native_inlet_tke_target_from_af_k": fmt(
                audit_float(native_preconditions_audit, "inlet_tke_target_from_af_k")
            ),
            "native_inlet_tke_to_k_ratio": fmt(
                audit_float(native_preconditions_audit, "inlet_tke_to_k_ratio")
            ),
            "native_inlet_mean_turbulent_kinetic_energy_from_components": fmt(
                audit_float(native_preconditions_audit, "inlet_mean_turbulent_kinetic_energy_from_components")
            ),
            "native_inlet_correlation_source_time_steps_match_runtime": first_bool_text(
                native_preconditions_audit.get("inlet_correlation_source_time_steps_match_runtime")
            ),
            "native_inlet_correlation_source_vtk_sha256_match_runtime": first_bool_text(
                native_preconditions_audit.get("inlet_correlation_source_vtk_sha256_match_runtime")
            ),
            "native_inlet_correlation_source_step_span": fmt(
                audit_int(native_preconditions_audit, "inlet_correlation_source_step_span")
            ),
            "native_inlet_correlation_minimum_step_span": fmt(
                audit_int(native_preconditions_audit, "inlet_correlation_minimum_step_span")
            ),
            "native_inlet_source_stg_evidence_required": first_bool_text(
                native_preconditions_audit.get("inlet_source_stg_evidence_required")
            ),
            "native_inlet_source_distribution_route": audit_field(
                native_preconditions_audit, "inlet_source_distribution_route"
            ),
            "native_inlet_source_distribution_route_gate": audit_gate(
                native_preconditions_audit, "inlet_source_distribution_route_gate"
            ),
            "native_inlet_source_has_equilibrium_boundaries_define": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_equilibrium_boundaries_define")
            ),
            "native_inlet_source_has_type_e_equilibrium_boundary_route": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_type_e_equilibrium_boundary_route")
            ),
            "native_inlet_source_has_three_component_velocity_write": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_three_component_velocity_write")
            ),
            "native_inlet_source_has_three_component_fluctuation_evidence": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_three_component_fluctuation_evidence")
            ),
            "native_inlet_source_has_k_driven_three_component_stg": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_k_driven_three_component_stg")
            ),
            "native_inlet_source_has_mean_preserving_inlet_correction": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_mean_preserving_inlet_correction")
            ),
            "native_inlet_source_has_layerwise_mean_preserving_inlet_correction": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_layerwise_mean_preserving_inlet_correction")
            ),
            "native_inlet_source_has_streamwise_clipping_control": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_streamwise_clipping_control")
            ),
            "native_inlet_source_streamwise_min_fraction": audit_field(
                native_preconditions_audit, "inlet_source_streamwise_min_fraction"
            ),
            "native_inlet_source_streamwise_clipping_enabled": first_bool_text(
                native_preconditions_audit.get("inlet_source_streamwise_clipping_enabled")
            ),
            "native_inlet_source_has_legacy_hardcoded_streamwise_clipping": first_bool_text(
                native_preconditions_audit.get("inlet_source_has_legacy_hardcoded_streamwise_clipping")
            ),
            "native_inlet_source_uncorrelated_random_patterns": audit_field(
                native_preconditions_audit, "inlet_source_uncorrelated_random_patterns_csv"
            ),
            "native_inlet_source_recommended_next_action": audit_field(
                native_preconditions_audit, "inlet_source_recommended_next_action"
            ),
            "native_probe_component_equivalence_gate": audit_gate(
                native_preconditions_audit, "native_probe_component_equivalence_gate"
            ),
            "native_probe_component_equivalence_gate_reasons": audit_field(
                native_preconditions_audit, "native_probe_component_equivalence_gate_reasons_csv"
            ),
            "native_probe_compared_component_values": audit_field(
                native_preconditions_audit, "probe_audit_compared_components_csv"
            ),
            "native_probe_expected_compared_component": audit_field(
                native_preconditions_audit, "expected_compared_component"
            ),
            "native_probe_compared_component_mismatch_reason": audit_field(
                native_preconditions_audit, "probe_compared_component_mismatch_reason"
            ),
            "native_probe_official_coverage_reason": audit_field(
                native_preconditions_audit, "probe_official_coverage_reason"
            ),
            "native_probe_missing_official_probe_ids": audit_field(
                native_preconditions_audit, "missing_official_probe_ids_csv"
            ),
            "native_probe_unmatched_probe_ids": audit_field(native_preconditions_audit, "unmatched_probe_ids_csv"),
            "native_probe_duplicate_ids": audit_field(native_preconditions_audit, "probe_duplicate_ids_csv"),
            "native_probe_max_official_coordinate_delta_m": fmt(
                audit_float(native_preconditions_audit, "probe_max_official_coordinate_delta_m")
            ),
            "native_probe_official_coordinate_delta_source": audit_field(
                native_preconditions_audit, "probe_official_coordinate_delta_source"
            ),
            "native_probe_official_coordinate_delta_recomputed_count": audit_field(
                native_preconditions_audit, "probe_official_coordinate_delta_recomputed_count"
            ),
            "native_probe_official_coordinate_delta_recompute_error": audit_field(
                native_preconditions_audit, "probe_official_coordinate_delta_recompute_error"
            ),
            "native_probe_missing_official_coordinate_delta_count": audit_field(
                native_preconditions_audit, "probe_missing_official_coordinate_delta_count"
            ),
            "native_probe_official_coordinate_delta_violation_count": audit_field(
                native_preconditions_audit, "probe_official_coordinate_delta_violation_count"
            ),
            "native_probe_uref_mismatch_count": audit_field(native_preconditions_audit, "probe_uref_mismatch_count"),
            "native_probe_out_of_tolerance_count": audit_field(
                native_preconditions_audit, "probe_out_of_tolerance_count"
            ),
            "native_probe_projection_issue_reason": audit_field(
                native_preconditions_audit, "probe_projection_issue_reason"
            ),
            "native_probe_component_uref_issue_reason": audit_field(
                native_preconditions_audit, "probe_component_uref_issue_reason"
            ),
            "native_probe_component_source_time_steps_match_runtime": first_bool_text(
                native_preconditions_audit.get("component_source_time_steps_match_runtime")
            ),
            "native_probe_component_source_steps_strictly_increasing": first_bool_text(
                native_preconditions_audit.get("component_source_steps_strictly_increasing")
            ),
            "native_probe_component_source_step_spacing_uniform": first_bool_text(
                native_preconditions_audit.get("component_source_step_spacing_uniform")
            ),
            "native_probe_component_source_vtk_sha256_match_runtime": first_bool_text(
                native_preconditions_audit.get("component_source_vtk_sha256_match_runtime")
            ),
            "native_boundary_equivalence_gate": audit_gate(
                native_preconditions_audit, "native_boundary_equivalence_gate"
            ),
            "native_boundary_equivalence_gate_reasons": audit_field(
                native_preconditions_audit, "native_boundary_equivalence_gate_reasons_csv"
            ),
            "native_boundary_protocol_gate": audit_gate(native_preconditions_audit, "boundary_protocol_gate"),
            "native_boundary_evidence_gate": audit_gate(native_preconditions_audit, "boundary_evidence_gate"),
            "native_boundary_run_identity_gate": audit_gate(native_preconditions_audit, "boundary_run_identity_gate"),
            "native_boundary_run_identity_gate_reasons": audit_field(
                native_preconditions_audit, "boundary_run_identity_gate_reasons_csv"
            ),
            "native_boundary_evidence_metadata_sha256_matches_current": first_bool_text(
                native_preconditions_audit.get("boundary_evidence_metadata_sha256_matches_current")
            ),
            "native_boundary_evidence_aij_case": audit_field(
                native_preconditions_audit, "boundary_evidence_aij_case"
            ),
            "native_boundary_evidence_wind_direction": audit_field(
                native_preconditions_audit, "boundary_evidence_wind_direction"
            ),
            "native_boundary_protocol_gate_reasons": audit_field(
                native_preconditions_audit, "boundary_protocol_gate_reasons_csv"
            ),
            "native_boundary_missing_evidence_fields": audit_field(
                native_preconditions_audit, "boundary_missing_evidence_fields_csv"
            ),
            "native_boundary_unsupported_condition_fields": audit_field(
                native_preconditions_audit, "boundary_unsupported_condition_fields_csv"
            ),
            "native_boundary_required_support_fields_missing_or_false": audit_field(
                native_preconditions_audit, "boundary_required_support_fields_missing_or_false_csv"
            ),
            "native_boundary_equivalence_supported": first_bool_text(
                native_preconditions_audit.get("boundary_equivalence_supported")
            ),
            "native_boundary_evidence_class_supported": first_bool_text(
                native_preconditions_audit.get("boundary_evidence_class_supported")
            ),
            "native_boundary_evidence_files_all_hashed": first_bool_text(
                native_preconditions_audit.get("boundary_evidence_files_all_hashed")
            ),
            "native_boundary_condition_fields_supported": first_bool_text(
                native_preconditions_audit.get("boundary_condition_fields_supported")
            ),
            "native_boundary_clearance_numeric_gate": audit_gate(
                native_preconditions_audit, "boundary_clearance_numeric_gate"
            ),
            "native_boundary_clearance_numeric_gate_reasons": audit_field(
                native_preconditions_audit, "boundary_clearance_numeric_gate_reasons_csv"
            ),
            "native_boundary_blockage_gate": audit_gate(native_preconditions_audit, "boundary_blockage_gate"),
            "native_boundary_runtime_gate": audit_gate(native_preconditions_audit, "boundary_runtime_gate"),
            "native_boundary_runtime_gate_reasons": audit_field(
                native_preconditions_audit, "boundary_runtime_gate_reasons_csv"
            ),
            "native_boundary_runtime_traceability_gate": audit_gate(
                native_preconditions_audit, "boundary_runtime_traceability_gate"
            ),
            "native_boundary_runtime_profile_preservation_gate": audit_gate(
                native_preconditions_audit, "boundary_runtime_profile_preservation_gate"
            ),
            "native_boundary_runtime_inlet_gate": audit_gate(native_preconditions_audit, "boundary_runtime_inlet_gate"),
            "native_boundary_runtime_side_top_gate": audit_gate(
                native_preconditions_audit, "boundary_runtime_side_top_gate"
            ),
            "native_boundary_runtime_side_top_normal_leakage_gate": audit_gate(
                native_preconditions_audit, "boundary_runtime_side_top_normal_leakage_gate"
            ),
            "native_boundary_runtime_outlet_gate": audit_gate(native_preconditions_audit, "boundary_runtime_outlet_gate"),
            "native_boundary_runtime_max_u_mae_ratio": audit_field(
                native_preconditions_audit, "boundary_runtime_max_u_mae_ratio"
            ),
            "native_boundary_runtime_max_side_top_normal_velocity_ratio": audit_field(
                native_preconditions_audit, "boundary_runtime_max_side_top_normal_velocity_ratio"
            ),
            "native_boundary_runtime_max_side_top_normal_abs_mps": audit_field(
                native_preconditions_audit, "boundary_runtime_max_side_top_normal_abs_mps"
            ),
            "native_boundary_runtime_source_step_span": audit_field(
                native_preconditions_audit, "boundary_runtime_source_step_span"
            ),
            "native_top_blocking_priority_rank": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_rank"
            ),
            "native_top_blocking_priority_key": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_key"
            ),
            "native_top_blocking_priority_reason_count": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_reason_count"
            ),
            "native_top_blocking_priority_reasons": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_reasons_csv"
            ),
            "native_top_blocking_priority_diagnosis": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_diagnosis"
            ),
            "native_top_blocking_priority_next_action": audit_field(
                native_preconditions_audit, "native_top_blocking_priority_next_action"
            ),
            "native_rerun_prescription_gate": audit_gate(
                native_preconditions_audit, "native_rerun_prescription_gate"
            ),
            "native_rerun_prescription_top_key": audit_field(
                native_preconditions_audit, "native_rerun_prescription_top_key"
            ),
            "native_rerun_prescription_experiment": audit_field(
                native_preconditions_audit, "native_rerun_prescription_experiment"
            ),
            "native_rerun_prescription_required_controls": audit_list_field(
                native_preconditions_audit, "native_rerun_prescription_required_controls"
            ),
            "native_rerun_prescription_minimum_final_window": audit_field(
                native_preconditions_audit, "native_rerun_prescription_minimum_final_window"
            ),
            "native_rerun_prescription_accuracy_interpretation_allowed": first_bool_text(
                native_preconditions_audit.get("native_rerun_prescription_accuracy_interpretation_allowed")
            ),
            "native_rerun_prescription_summary": audit_field(
                native_preconditions_audit, "native_rerun_prescription_summary"
            ),
            "native_precondition_closure_gate": audit_gate(
                native_preconditions_audit, "native_precondition_closure_gate"
            ),
            "native_precondition_closed_stage_count": audit_field(
                native_preconditions_audit, "native_precondition_closed_stage_count"
            ),
            "native_precondition_failed_stage_count": audit_field(
                native_preconditions_audit, "native_precondition_failed_stage_count"
            ),
            "native_precondition_failed_stage_keys": audit_list_field(
                native_preconditions_audit, "native_precondition_failed_stage_keys"
            ),
            "native_precondition_top_blocking_stage_key": audit_field(
                native_preconditions_audit, "native_precondition_top_blocking_stage_key"
            ),
            "native_precondition_top_blocking_stage_rank": audit_field(
                native_preconditions_audit, "native_precondition_top_blocking_stage_rank"
            ),
            "native_precondition_top_blocking_stage_reason_count": audit_field(
                native_preconditions_audit, "native_precondition_top_blocking_stage_reason_count"
            ),
            "native_precondition_top_blocking_stage_reasons": audit_list_field(
                native_preconditions_audit, "native_precondition_top_blocking_stage_reasons"
            ),
            "native_preconditions_manifest_sha256": audit_field(
                native_preconditions_audit, "native_preconditions_manifest_sha256"
            ),
            "native_preconditions_setup_sha256": audit_field(
                native_preconditions_audit, "native_preconditions_setup_sha256"
            ),
            "native_preconditions_metadata_sha256": audit_field(
                native_preconditions_audit, "native_preconditions_metadata_sha256"
            ),
            "native_preconditions_runtime_audit_sha256": audit_field(
                native_preconditions_audit, "native_preconditions_runtime_audit_sha256"
            ),
            "native_citylbm_parity_audit": str(Path(args.native_citylbm_parity_audit).resolve()) if args.native_citylbm_parity_audit else "",
            "native_citylbm_parity_gate": audit_gate(native_citylbm_parity_audit, "native_citylbm_parity_gate"),
            "native_citylbm_parity_gate_reasons": ";".join(
                str(reason) for reason in native_citylbm_parity_audit.get("native_citylbm_parity_gate_reasons", [])
            )
            if isinstance(native_citylbm_parity_audit.get("native_citylbm_parity_gate_reasons"), list)
            else str(native_citylbm_parity_audit.get("native_citylbm_parity_gate_reasons", "")),
            "native_citylbm_parity_native_metrics": audit_field(native_citylbm_parity_audit, "native_metrics"),
            "native_citylbm_parity_matched_field_count": audit_field(native_citylbm_parity_audit, "matched_field_count"),
            "native_citylbm_parity_mismatched_field_count": audit_field(native_citylbm_parity_audit, "mismatched_field_count"),
            "native_citylbm_parity_mismatched_fields": ";".join(
                str(field) for field in native_citylbm_parity_audit.get("mismatched_fields", [])
            )
            if isinstance(native_citylbm_parity_audit.get("mismatched_fields"), list)
            else str(native_citylbm_parity_audit.get("mismatched_fields", "")),
            "native_citylbm_parity_compared_text_field_count": audit_field(native_citylbm_parity_audit, "compared_text_field_count"),
            "native_citylbm_parity_compared_gate_field_count": audit_field(native_citylbm_parity_audit, "compared_gate_field_count"),
            "native_citylbm_parity_compared_hash_field_count": audit_field(native_citylbm_parity_audit, "compared_hash_field_count"),
            "native_citylbm_parity_compared_numeric_field_count": audit_field(native_citylbm_parity_audit, "compared_numeric_field_count"),
            "native_citylbm_parity_critical_field_gate": audit_field(native_citylbm_parity_audit, "critical_parity_field_gate"),
            "native_citylbm_parity_required_critical_field_count": audit_field(native_citylbm_parity_audit, "required_critical_field_count"),
            "native_citylbm_parity_matched_critical_field_count": audit_field(native_citylbm_parity_audit, "matched_critical_field_count"),
            "native_citylbm_parity_missing_critical_field_count": audit_field(native_citylbm_parity_audit, "missing_critical_field_count"),
            "native_citylbm_parity_missing_critical_fields": ";".join(
                str(field) for field in native_citylbm_parity_audit.get("missing_critical_fields", [])
            )
            if isinstance(native_citylbm_parity_audit.get("missing_critical_fields"), list)
            else str(native_citylbm_parity_audit.get("missing_critical_fields", "")),
            "native_citylbm_accuracy_delta_audit": str(Path(args.native_citylbm_accuracy_delta_audit).resolve()) if args.native_citylbm_accuracy_delta_audit else "",
            "native_citylbm_accuracy_delta_gate": audit_gate(
                native_citylbm_accuracy_delta_audit, "native_citylbm_accuracy_delta_gate"
            ),
            "native_citylbm_accuracy_delta_gate_reasons": audit_list_field(
                native_citylbm_accuracy_delta_audit, "native_citylbm_accuracy_delta_gate_reasons"
            ),
            "native_citylbm_accuracy_interpretation": audit_field(
                native_citylbm_accuracy_delta_audit, "accuracy_interpretation"
            ),
            "native_citylbm_additional_error_flag": first_bool_text(
                native_citylbm_accuracy_delta_audit.get("citylbm_additional_error_flag")
            ),
            "native_citylbm_additional_error_reasons": audit_list_field(
                native_citylbm_accuracy_delta_audit, "citylbm_additional_error_reasons"
            ),
            "native_preconditions_accuracy_gate": audit_gate(
                native_citylbm_accuracy_delta_audit, "native_preconditions_accuracy_gate"
            ),
            "native_preconditions_accuracy_gate_reasons": audit_list_field(
                native_citylbm_accuracy_delta_audit, "native_preconditions_accuracy_gate_reasons"
            ),
            "native_preconditions_accuracy_top_blocker": audit_field(
                native_citylbm_accuracy_delta_audit, "native_precondition_top_blocking_stage_key"
            ),
            "native_accuracy_gate": audit_gate(
                native_citylbm_accuracy_delta_audit, "native_accuracy_gate"
            ),
            "native_accuracy_gate_reasons": audit_list_field(
                native_citylbm_accuracy_delta_audit, "native_accuracy_gate_reasons"
            ),
            "native_citylbm_U_RMSE_delta": fmt(
                audit_float(native_citylbm_accuracy_delta_audit, "U_RMSE_delta_city_minus_native")
            ),
            "native_citylbm_U_abs_bias_delta": fmt(
                audit_float(native_citylbm_accuracy_delta_audit, "U_abs_bias_delta_city_minus_native")
            ),
            "native_citylbm_U_R2_drop": fmt(
                audit_float(native_citylbm_accuracy_delta_audit, "U_R2_drop_native_minus_city")
            ),
            "native_citylbm_U_slope_abs_delta": fmt(
                audit_float(native_citylbm_accuracy_delta_audit, "U_slope_abs_delta")
            ),
            "native_citylbm_U_intercept_abs_delta": fmt(
                audit_float(native_citylbm_accuracy_delta_audit, "U_intercept_abs_delta")
            ),
            "probe_mapping_table": str(probe_path),
            "probe_mapping_table_sha256": sha256_file(probe_path),
            "official_measurement_sha256": sha256_file(official_path),
            "probe_vtk_source_window_gate": probe_source_window_gate,
            "probe_vtk_source_window_reasons": ";".join(probe_source_reasons),
            "probe_vtk_source_time_steps": ";".join(unique_probe_source_steps),
            "probe_vtk_source_step_span": fmt(unique_probe_source_step_spans[0] if len(unique_probe_source_step_spans) == 1 else None),
            "probe_vtk_minimum_step_span": fmt(unique_probe_minimum_step_spans[0] if len(unique_probe_minimum_step_spans) == 1 else None),
            "probe_vtk_source_hash_set_count": fmt(len(unique_probe_source_hash_sets)),
            "probe_id_field": args.probe_id_column,
            "probe_tolerance_m": tolerance,
            "probe_grid_extent_gate": probe_grid_extent_gate,
            "probe_inside_vtk_grid_extent_count": probe_inside_grid_extent_count,
            "probe_outside_vtk_grid_extent_count": probe_outside_grid_extent_count,
            "probe_missing_vtk_grid_extent_count": probe_missing_grid_extent_count,
            "compared_component": compared_component,
            "component_sensitivity_audit": str(Path(args.component_sensitivity_audit).resolve()) if args.component_sensitivity_audit else "",
            "component_sensitivity_probe_audit_sha256": audit_field(component_sensitivity_audit, "probe_audit_sha256"),
            "component_sensitivity_official_sha256": audit_field(component_sensitivity_audit, "official_sha256"),
            "component_sensitivity_case": audit_field(component_sensitivity_audit, "case"),
            "component_sensitivity_wind_direction": audit_field(component_sensitivity_audit, "wind_direction"),
            "component_sensitivity_official_filtered_row_count": fmt(
                audit_int(component_sensitivity_audit, "official_filtered_row_count")
            ),
            "component_sensitivity_official_id_count": fmt(
                audit_int(component_sensitivity_audit, "official_id_count")
            ),
            "component_sensitivity_probe_row_count": fmt(
                audit_int(component_sensitivity_audit, "probe_row_count")
            ),
            "component_sensitivity_valid_probe_id_count": fmt(
                audit_int(component_sensitivity_audit, "valid_probe_id_count")
            ),
            "component_sensitivity_matched_valid_probe_id_count": fmt(
                audit_int(component_sensitivity_audit, "matched_valid_probe_id_count")
            ),
            "component_sensitivity_unmatched_valid_probe_id_count": fmt(
                audit_int(component_sensitivity_audit, "unmatched_valid_probe_id_count")
            ),
            "component_sensitivity_missing_official_probe_id_count": fmt(
                audit_int(component_sensitivity_audit, "missing_official_probe_id_count")
            ),
            "component_sensitivity_official_probe_coverage_ratio": fmt(
                audit_float(component_sensitivity_audit, "official_probe_coverage_ratio")
            ),
            "component_source_window_gate": audit_gate(component_sensitivity_audit, "component_source_window_gate"),
            "component_source_window_gate_reasons": ";".join(
                str(reason) for reason in component_sensitivity_audit.get("component_source_window_gate_reasons", [])
            )
            if isinstance(component_sensitivity_audit.get("component_source_window_gate_reasons"), list)
            else str(component_sensitivity_audit.get("component_source_window_gate_reasons", "")),
            "component_source_time_steps": audit_field(component_sensitivity_audit, "component_source_time_steps"),
            "component_source_step_span": fmt(audit_int(component_sensitivity_audit, "component_source_step_span")),
            "component_minimum_source_step_span": fmt(
                audit_int(component_sensitivity_audit, "component_minimum_source_step_span")
            ),
            "component_source_sha256": audit_field(component_sensitivity_audit, "component_source_sha256"),
            "component_source_time_steps_unique_count": fmt(
                audit_int(component_sensitivity_audit, "component_source_time_steps_unique_count")
            ),
            "component_source_hash_set_unique_count": fmt(
                audit_int(component_sensitivity_audit, "component_source_hash_set_unique_count")
            ),
            "component_normalization_gate": audit_gate(component_sensitivity_audit, "component_normalization_gate"),
            "component_sensitivity_gate": audit_gate(component_sensitivity_audit, "component_sensitivity_gate"),
            "normalization_scale_gate": audit_gate(component_sensitivity_audit, "normalization_scale_gate"),
            "best_component_by_rmse": audit_field(component_sensitivity_audit, "best_component_by_rmse"),
            "selected_component_rmse_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_rmse")),
            "selected_component_bias_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_bias")),
            "selected_component_scaled_bias_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_scaled_bias")),
            "selected_component_bias_abs_reduction_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_bias_abs_reduction_ratio")),
            "selected_component_mean_sim_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_mean_sim")),
            "selected_component_mean_exp_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_mean_exp")),
            "selected_component_mean_sim_to_exp_ratio": fmt(audit_float(component_sensitivity_audit, "selected_component_mean_sim_to_exp_ratio")),
            "best_component_rmse_ratio": fmt(audit_float(component_sensitivity_audit, "best_component_rmse")),
            "component_rmse_improvement_ratio": fmt(audit_float(component_sensitivity_audit, "component_rmse_improvement_ratio")),
            "normalization_best_fit_scale": fmt(audit_float(component_sensitivity_audit, "selected_best_fit_scale_to_exp")),
            "normalization_scaled_improvement_ratio": fmt(audit_float(component_sensitivity_audit, "selected_scaled_improvement_ratio")),
            "probe_uref_expected_mps": fmt(args.u_ref),
            "probe_uref_values": ";".join(fmt(value) for value in unique_probe_urefs),
            "probe_uref_mismatch_count": probe_uref_mismatch_count,
            "grid_sensitivity_audit": str(Path(args.grid_sensitivity_audit).resolve()) if args.grid_sensitivity_audit else "",
            "grid_sensitivity_gate": audit_gate(grid_sensitivity_audit, "grid_sensitivity_gate"),
            "grid_sensitivity_gate_reasons": ";".join(
                str(reason) for reason in grid_sensitivity_audit.get("grid_sensitivity_gate_reasons", [])
            )
            if isinstance(grid_sensitivity_audit.get("grid_sensitivity_gate_reasons"), list)
            else str(grid_sensitivity_audit.get("grid_sensitivity_gate_reasons", "")),
            "grid_sensitivity_run_count": audit_field(grid_sensitivity_audit, "grid_sensitivity_run_count"),
            "grid_sensitivity_finest_dx_m": fmt(audit_float(grid_sensitivity_audit, "grid_sensitivity_finest_dx_m")),
            "grid_sensitivity_next_coarse_dx_m": fmt(audit_float(grid_sensitivity_audit, "grid_sensitivity_next_coarse_dx_m")),
            "grid_sensitivity_refinement_ratio": fmt(audit_float(grid_sensitivity_audit, "grid_sensitivity_refinement_ratio")),
            "grid_sensitivity_rmse_change_ratio": fmt(audit_float(grid_sensitivity_audit, "grid_sensitivity_rmse_change_ratio")),
            "grid_sensitivity_bias_change_ratio": fmt(audit_float(grid_sensitivity_audit, "grid_sensitivity_bias_change_ratio")),
            "failed_probe_count_by_tolerance": failed,
            "valid_n": valid_n,
            "failed_n": failed,
            "official_measurement_count": official_measurement_count,
            "official_probe_coverage_ratio": fmt(official_probe_coverage_ratio),
            "missing_official_probe_count": missing_official_probe_count,
            "mean_probe_distance_m": fmt(mean(distances)),
            "max_probe_distance_m": fmt(max(distances) if distances else None),
            "max_official_coordinate_delta_m": fmt(max_coordinate_delta),
            "official_coordinate_delta_count": coordinate_delta_count,
            "U_MAE_ratio": fmt(u_mae),
            "U_RMSE_ratio": fmt(u_rmse),
            "U_bias_ratio": fmt(u_bias),
            "U_R2": fmt(u_r2),
            "U_regression_slope": fmt(slope),
            "U_regression_intercept": fmt(intercept),
            "U_max_abs_error": fmt(max_abs),
            "U_mean_sim": fmt(mean_sim),
            "U_mean_exp": fmt(mean_exp),
            "U_mean_ratio_sim_to_exp": fmt(mean_ratio),
            "U_mean_relative_bias_ratio": fmt(mean_relative_bias),
            "U_best_fit_scale_to_exp": fmt(best_scale),
            "U_best_fit_scale_deviation_ratio": fmt(best_scale_deviation),
            "U_scaled_MAE_ratio": fmt(scaled_mae),
            "U_scaled_RMSE_ratio": fmt(scaled_rmse),
            "U_scaled_improvement_ratio": fmt(scaled_improvement),
            "U_scaled_bias_ratio": fmt(scaled_bias),
            "U_abs_bias_ratio": fmt(abs_bias),
            "U_scale_like_error_flag": csv_bool(scale_like_error),
            "bias_diagnosis": bias_diagnosis,
            "k_MAE_m2s2": args.k_mae or fmt(inlet_k_mae),
            "k_RMSE_m2s2": args.k_rmse or fmt(inlet_k_rmse),
            "k_RMSE_ratio": fmt(inlet_k_rmse_ratio),
            "k_bias_m2s2": args.k_bias or fmt(inlet_k_bias),
            "k_bias_ratio": args.k_bias_ratio or fmt(inlet_k_bias_ratio),
            "systematic_bias_flag": systematic_flag,
            "protocol_gate": metrics_protocol_gate,
            "notes": (
                f"official_id_column={official_id_col}; official_value_column={official_value_col}; "
                f"matched={valid_n}; official_filtered={len(official_rows)}; "
                f"missing_official_probe_count={missing_official_probe_count}; "
                f"official_probe_coverage_ratio={fmt(official_probe_coverage_ratio)}; "
                f"probe_uref_expected_mps={fmt(args.u_ref) or 'not_set'}; "
                f"probe_uref_values={';'.join(fmt(value) for value in unique_probe_urefs) or 'none'}; "
                f"probe_uref_mismatch_count={probe_uref_mismatch_count}; "
                f"metrics_protocol_failures={';'.join(protocol_failures) or 'none'}"
            ),
        }
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not args.append or not out_path.exists()
    with out_path.open("a" if args.append else "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(metrics)

    if comparison_path:
        comparison_path.parent.mkdir(parents=True, exist_ok=True)
        with comparison_path.open("w", encoding="utf-8", newline="") as handle:
            fields = [
                "probe_id",
                "sim_value",
                "official_value",
                "error",
                "abs_error",
                "nearest_distance",
                "official_coordinate_delta",
                "compared_component",
                "normalization_valid",
                "wind_direction_valid",
            ]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in comparison_rows:
                writer.writerow(row)

    print(f"Wrote metrics: {out_path}")
    print(f"valid_n={valid_n}; failed_n={failed}; U_bias_ratio={fmt(u_bias)}; U_R2={fmt(u_r2)}; systematic_bias_flag={systematic_flag or 'false'}; bias_diagnosis={bias_diagnosis or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
