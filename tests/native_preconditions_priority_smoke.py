#!/usr/bin/env python3
"""Smoke-test native precondition diagnostic priority ordering."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_audit_module():
    path = REPO / "scripts" / "audit_native_preconditions.py"
    spec = importlib.util.spec_from_file_location("audit_native_preconditions", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_audit_module()
    if module.count_below_minimum_reason("runtime_average_window_frame_count", 4, 40) != (
        "runtime_average_window_frame_count_4_below_minimum_40"
    ):
        raise AssertionError("frame shortfall reason did not preserve the actual count")
    if module.count_below_minimum_reason("runtime_average_step_span", 3000, 20000) != (
        "runtime_average_step_span_3000_below_minimum_20000"
    ):
        raise AssertionError("step-span shortfall reason did not preserve the actual span")
    if module.reason_token("abs streamwise ratio; speed") != "abs_streamwise_ratio_speed":
        raise AssertionError("reason token did not normalize component labels")
    if module.count_reason("probe_uref_mismatch_count", 80) != "probe_uref_mismatch_count_80":
        raise AssertionError("count reason did not preserve the failing row count")
    passing_height_gate = module.build_probe_official_height_gate(
        official_expected_z="2",
        official_z_match_count=80,
        official_z_mismatch_count=0,
        official_probe_set_row_count=80,
    )
    if passing_height_gate["gate"] != "pass":
        raise AssertionError(passing_height_gate)
    missing_height_gate = module.build_probe_official_height_gate(
        official_expected_z="",
        official_z_match_count=None,
        official_z_mismatch_count=None,
        official_probe_set_row_count=80,
    )
    for expected_reason in [
        "official_expected_z_missing",
        "official_z_match_count_missing",
        "official_z_mismatch_count_missing",
    ]:
        if expected_reason not in missing_height_gate["reasons"]:
            raise AssertionError(missing_height_gate)
    mismatched_height_gate = module.build_probe_official_height_gate(
        official_expected_z="2",
        official_z_match_count=79,
        official_z_mismatch_count=1,
        official_probe_set_row_count=80,
    )
    for expected_reason in [
        "official_z_mismatch_count:1",
        "official_z_match_count_79_does_not_match_official_row_count_80",
    ]:
        if expected_reason not in mismatched_height_gate["reasons"]:
            raise AssertionError(mismatched_height_gate)
    passing_probe_interpretation = module.build_probe_component_interpretation_gate("pass", [])
    if passing_probe_interpretation["gate"] != "pass" or passing_probe_interpretation["allowed"] is not True:
        raise AssertionError(passing_probe_interpretation)
    coordinate_probe_interpretation = module.build_probe_component_interpretation_gate(
        "fail",
        ["probe_official_coordinate_delta_violation_count_80"],
    )
    if coordinate_probe_interpretation["blocker"] != "official_probe_mapping":
        raise AssertionError(coordinate_probe_interpretation)
    domain_origin_probe_interpretation = module.build_probe_component_interpretation_gate(
        "fail",
        ["coordinate_probe_domain_origin_not_valid"],
    )
    if domain_origin_probe_interpretation["blocker"] != "probe_projection":
        raise AssertionError(domain_origin_probe_interpretation)
    domain_origin_reasons = module.coordinate_protocol_reasons(
        {
            "coordinate_probe_protocol_gate": "fail",
            "Reasons": ["domain_origin_json_missing"],
            "CoordinateProtocol": {
                "ProbeProjection": {"Formula": "(coordinate_m - DomainMin) / dx"},
                "DomainOrigin": {"valid": False, "dx_m": None, "domain_min_m": []},
            },
        }
    )
    for expected_reason in [
        "coordinate_probe_protocol_gate_not_pass:fail",
        "coordinate_probe_protocol:domain_origin_json_missing",
        "coordinate_probe_domain_origin_not_valid",
        "coordinate_probe_domain_origin_dx_m_missing",
        "coordinate_probe_domain_origin_min_m_missing",
    ]:
        if expected_reason not in domain_origin_reasons:
            raise AssertionError(domain_origin_reasons)
    source_window_probe_interpretation = module.build_probe_component_interpretation_gate(
        "fail",
        ["component_source_step_hash_pairs_mismatch_runtime"],
    )
    if source_window_probe_interpretation["blocker"] != "probe_component_window_traceability":
        raise AssertionError(source_window_probe_interpretation)
    passing_inlet_interpretation = module.build_inlet_turbulence_interpretation_gate("pass", [])
    if passing_inlet_interpretation["gate"] != "pass" or passing_inlet_interpretation["allowed"] is not True:
        raise AssertionError(passing_inlet_interpretation)
    source_inlet_interpretation = module.build_inlet_turbulence_interpretation_gate(
        "fail",
        ["inlet_source_velocity_field_only_not_false:True"],
    )
    if source_inlet_interpretation["blocker"] != "inlet_turbulence_source_implementation":
        raise AssertionError(source_inlet_interpretation)
    profile_inlet_interpretation = module.build_inlet_turbulence_interpretation_gate(
        "fail",
        ["inlet_k_profile_gate_not_pass:fail"],
    )
    if profile_inlet_interpretation["blocker"] != "inlet_profile_u_k_preservation":
        raise AssertionError(profile_inlet_interpretation)
    statistics_inlet_interpretation = module.build_inlet_turbulence_interpretation_gate(
        "fail",
        ["inlet_tke_gate_not_pass:fail"],
    )
    if statistics_inlet_interpretation["blocker"] != "inlet_turbulence_statistics_preservation":
        raise AssertionError(statistics_inlet_interpretation)

    source_window_reasons = []
    source_window = module.append_source_window_reasons(
        source_window_reasons,
        "inlet_profile",
        {
            "source_time_steps": [1000, 2000],
            "source_vtk_sha256": ["b" * 64, "a" * 64],
        },
        [1000, 2000],
        ["a" * 64, "b" * 64],
    )
    if source_window["inlet_profile_source_time_steps_match_runtime"] is not True:
        raise AssertionError(source_window)
    if source_window["inlet_profile_source_vtk_sha256_match_runtime"] is not True:
        raise AssertionError(source_window)
    if source_window["inlet_profile_source_step_hash_pairs_match_runtime"] is not False:
        raise AssertionError(source_window)
    if "inlet_profile_source_step_hash_pairs_mismatch" not in source_window_reasons:
        raise AssertionError(source_window_reasons)

    passing_time_reasons = module.build_time_average_evidence_reasons(
        runtime_audit_present=True,
        runtime_reported_time_average_gate="pass",
        time_gate="pass",
        requested_frame_gate="pass",
        final_window_frame_count_gate="pass",
        final_window_frame_count_reasons=[],
        stationarity_gate="pass",
        stationarity_reasons=[],
        planned_frame_shortfall_reason=None,
        runtime_average_shortfall_reason=None,
        planned_step_shortfall_reason=None,
        runtime_step_shortfall_reason=None,
        runtime_avg=40,
        required_average_last_n=40,
        runtime_selected_last_window=True,
        runtime_step_span=39000,
        runtime_step_span_reported=39000,
        runtime_step_span_from_steps=39000,
        runtime_steps=list(range(1000, 41000, 1000)),
        runtime_steps_increasing=True,
        runtime_steps_uniform=True,
        runtime_hashes=[f"{idx:064x}" for idx in range(40)],
        runtime_hash_count=40,
        runtime_hash_unique_count=40,
        min_avg_frames=40,
        time_averaging_evidence_file_gate="pass",
        time_averaging_evidence_file_reasons=[],
        time_averaging_evidence_selected_steps_csv=";".join(str(step) for step in range(1000, 41000, 1000)),
        time_averaging_evidence_selected_hash_count=40,
    )
    if passing_time_reasons:
        raise AssertionError(passing_time_reasons)

    mismatched_time_evidence_reasons = module.build_time_average_evidence_reasons(
        runtime_audit_present=True,
        runtime_reported_time_average_gate="pass",
        time_gate="pass",
        requested_frame_gate="pass",
        final_window_frame_count_gate="pass",
        final_window_frame_count_reasons=[],
        stationarity_gate="pass",
        stationarity_reasons=[],
        planned_frame_shortfall_reason=None,
        runtime_average_shortfall_reason=None,
        planned_step_shortfall_reason=None,
        runtime_step_shortfall_reason=None,
        runtime_avg=40,
        required_average_last_n=40,
        runtime_selected_last_window=True,
        runtime_step_span=39000,
        runtime_step_span_reported=39000,
        runtime_step_span_from_steps=39000,
        runtime_steps=list(range(1000, 41000, 1000)),
        runtime_steps_increasing=True,
        runtime_steps_uniform=True,
        runtime_hashes=[f"{idx:064x}" for idx in range(40)],
        runtime_hash_count=40,
        runtime_hash_unique_count=40,
        min_avg_frames=40,
        time_averaging_evidence_file_gate="pass",
        time_averaging_evidence_file_reasons=[],
        time_averaging_evidence_selected_steps_csv="2000;3000;4000;5000",
        time_averaging_evidence_selected_hash_count=39,
    )
    for expected_reason in [
        "time_averaging_evidence_selected_final_window_steps_mismatch_runtime",
        "time_averaging_evidence_selected_final_window_vtk_sha256_count_mismatch_runtime",
        "time_averaging_evidence_selected_final_window_vtk_sha256_count_39_below_minimum_40",
    ]:
        if expected_reason not in mismatched_time_evidence_reasons:
            raise AssertionError((expected_reason, mismatched_time_evidence_reasons))

    short_time_reasons = module.build_time_average_evidence_reasons(
        runtime_audit_present=True,
        runtime_reported_time_average_gate="fail",
        time_gate="pass",
        requested_frame_gate="fail",
        final_window_frame_count_gate="fail",
        final_window_frame_count_reasons=["final_window_frame_count_4_below_minimum_40"],
        stationarity_gate="diagnostic_only",
        stationarity_reasons=["final_window_mean_speed_drift_ratio_above_threshold"],
        planned_frame_shortfall_reason="planned_vtk_frame_count_4_below_minimum_40",
        runtime_average_shortfall_reason="runtime_average_window_frame_count_4_below_minimum_40",
        planned_step_shortfall_reason="planned_average_step_span_3000_below_minimum_20000",
        runtime_step_shortfall_reason="runtime_average_step_span_3000_below_minimum_20000",
        runtime_avg=4,
        required_average_last_n=40,
        runtime_selected_last_window=False,
        runtime_step_span=3000,
        runtime_step_span_reported=3000,
        runtime_step_span_from_steps=3000,
        runtime_steps=[1000, 2000, 3000, 4000],
        runtime_steps_increasing=True,
        runtime_steps_uniform=True,
        runtime_hashes=[f"{idx:064x}" for idx in range(4)],
        runtime_hash_count=4,
        runtime_hash_unique_count=4,
        min_avg_frames=40,
        time_averaging_evidence_file_gate="pass",
        time_averaging_evidence_file_reasons=[],
        time_averaging_evidence_selected_steps_csv="1000;2000;3000;4000",
        time_averaging_evidence_selected_hash_count=4,
    )
    for expected_reason in [
        "runtime_reported_time_averaging_gate_not_pass:fail",
        "runtime_requested_vtk_frame_gate_not_pass:fail",
        "runtime_final_window_stationarity_gate_not_pass:diagnostic_only",
        "runtime_average_window_shortfall:runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_step_span_shortfall:runtime_average_step_span_3000_below_minimum_20000",
        "runtime_average_window_4_does_not_match_required_40",
        "runtime_selected_last_window_not_true:False",
        "runtime_source_vtk_hash_count_4_below_minimum_40",
    ]:
        if expected_reason not in short_time_reasons:
            raise AssertionError((expected_reason, short_time_reasons))

    passing_time_interpretation = module.build_time_averaging_interpretation_gate("pass", [])
    if passing_time_interpretation["gate"] != "pass" or passing_time_interpretation["allowed"] is not True:
        raise AssertionError(passing_time_interpretation)
    short_time_interpretation = module.build_time_averaging_interpretation_gate(
        "fail",
        short_time_reasons,
    )
    if short_time_interpretation["blocker"] != "insufficient_final_window_frame_count":
        raise AssertionError(short_time_interpretation)
    if short_time_interpretation["status"] != "blocked_until_long_stationary_final_window_average_closed":
        raise AssertionError(short_time_interpretation)
    stationarity_time_interpretation = module.build_time_averaging_interpretation_gate(
        "fail",
        ["runtime_final_window_stationarity_gate_not_pass:diagnostic_only"],
    )
    if stationarity_time_interpretation["blocker"] != "nonstationary_final_window":
        raise AssertionError(stationarity_time_interpretation)

    passing_lbm_reasons = module.build_lbm_stability_reasons(
        target_velocity_lbm=0.08,
        estimated_mach=0.14,
        lbm_tau=0.56,
        lbm_nu=0.02,
        physical_viscosity=1.5e-5,
        estimated_reynolds=22000.0,
        velocity_set="D3Q19",
        les_model="Smagorinsky Cs=0.12",
        solver_warnings="no_stability_warnings",
        lbm_stability_gate="pass",
        protocol_status="pass",
        max_estimated_mach=0.2,
        min_lbm_tau=0.500001,
        max_lbm_tau=2.0,
    )
    if passing_lbm_reasons:
        raise AssertionError(passing_lbm_reasons)
    failing_lbm_reasons = module.build_lbm_stability_reasons(
        target_velocity_lbm=0.16,
        estimated_mach=0.24,
        lbm_tau=0.5,
        lbm_nu=0.0,
        physical_viscosity=None,
        estimated_reynolds=None,
        velocity_set="",
        les_model="",
        solver_warnings="nan_detected",
        lbm_stability_gate="fail",
        protocol_status="partial",
        max_estimated_mach=0.2,
        min_lbm_tau=0.500001,
        max_lbm_tau=2.0,
    )
    for expected_reason in [
        "target_max_profile_velocity_lbm_above_0.1:0.16",
        "estimated_max_profile_mach_above_0.2:0.24",
        "lbm_tau_outside_0.500001_2.0:0.5",
        "lbm_nu_not_positive:0.0",
        "physical_viscosity_m2s_missing",
        "estimated_reynolds_number_missing",
        "velocity_set_missing",
        "les_model_missing",
        "solver_stability_warnings_not_clear:nan_detected",
        "runtime_lbm_stability_gate_not_pass:fail",
    ]:
        if expected_reason not in failing_lbm_reasons:
            raise AssertionError((expected_reason, failing_lbm_reasons))

    passing_final_window_gate = module.build_final_window_frame_count_gate(
        runtime_avg=40,
        runtime_source_frame_count=40,
        runtime_hash_count=40,
        runtime_hash_unique_count=40,
        runtime_selected_last_window=True,
        min_avg_frames=40,
    )
    if passing_final_window_gate["gate"] != "pass":
        raise AssertionError(passing_final_window_gate)
    short_final_window_gate = module.build_final_window_frame_count_gate(
        runtime_avg=4,
        runtime_source_frame_count=4,
        runtime_hash_count=4,
        runtime_hash_unique_count=4,
        runtime_selected_last_window=False,
        min_avg_frames=40,
    )
    if short_final_window_gate["gate"] != "fail":
        raise AssertionError(short_final_window_gate)
    for expected_reason in [
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_source_frame_count_4_below_minimum_40",
        "runtime_source_vtk_sha256_count_4_below_minimum_40",
        "runtime_selected_last_window_not_true:False",
    ]:
        if expected_reason not in short_final_window_gate["reasons"]:
            raise AssertionError((expected_reason, short_final_window_gate))

    passing_inlet_source = {
        "inlet_source_gate": "pass",
        "paper_grade_inlet_source_gate": "pass",
        "inlet_source_distribution_consistent": True,
        "inlet_source_velocity_field_only": False,
        "inlet_source_comment_stripped_code_audit": True,
        "has_uncorrelated_random_inlet": False,
        "inlet_source_method_class": "synthetic_eddy_distribution_consistent",
        "inlet_source_turbulent_inflow_fidelity_class": "distribution_consistent_synthetic_eddy",
        "inlet_source_has_correlated_velocity_field_only": False,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": False,
        "synthetic_inlet_correlation_model": "synthetic_eddy_distribution_consistent",
        "inlet_distribution_route": "direct_setup_distribution_write",
        "inlet_distribution_route_gate": "pass",
        "has_equilibrium_boundaries_define": False,
        "has_type_e_equilibrium_boundary_route": False,
        "has_inlet_length_scale_evidence": True,
        "has_source_length_scale_evidence": True,
        "has_metadata_length_scale_evidence": True,
        "inlet_length_scale_evidence_basis": "source_and_metadata_gate",
        "metadata_length_scale_gate": "pass",
        "has_reynolds_stress_full_tensor_source_evidence": True,
        "has_measured_or_precursor_reynolds_stress_tensor_evidence": True,
        "has_reynolds_stress_tensor_evidence": True,
        "reynolds_stress_treatment": "measured_or_precursor_full_tensor",
        "has_three_component_velocity_write": True,
        "has_three_component_fluctuation_evidence": True,
        "has_k_driven_three_component_stg": True,
        "has_component_phase_decorrelation": True,
        "has_temporal_filter_state": True,
        "has_mean_preserving_inlet_correction": True,
        "has_layerwise_mean_preserving_inlet_correction": True,
        "has_layerwise_rms_preserving_inlet_correction": True,
        "has_streamwise_clipping_control": True,
        "streamwise_clipping_enabled": False,
        "has_legacy_hardcoded_streamwise_clipping": False,
        "inlet_source_has_rms_k_velocity_surrogate": False,
        "inlet_source_rms_k_surrogate_gate": "pass",
        "inlet_source_gate_reasons": ["inlet_source_consistent_with_declared_metadata"],
        "paper_grade_inlet_source_gate_reasons": ["source_distribution_consistent"],
    }
    passing_inlet_profile = {
        "inlet_profile_gate": "PASS",
        "inlet_u_profile_gate": "PASS",
        "inlet_k_profile_gate": "PASS",
        "time_averaging_gate": "PASS",
        "frame_count": 40,
        "source_time_steps": list(range(1000, 41000, 1000)),
    }
    passing_inlet_correlation = {
        "inlet_correlation_gate": "PASS",
        "inlet_k_variance_gate": "PASS",
        "inlet_tke_gate": "PASS",
        "frame_count": 40,
        "source_time_steps": list(range(1000, 41000, 1000)),
        "inlet_correlation_gate_reasons": ["inlet_correlation_evidence_present"],
        "inlet_k_variance_gate_reasons": ["k_variance_matches_af_profile"],
        "inlet_tke_gate_reasons": ["tke_matches_af_profile"],
    }
    passing_window_profile = {
        "inlet_profile_source_time_steps_match_runtime": True,
        "inlet_profile_source_vtk_sha256_match_runtime": True,
        "inlet_profile_source_step_hash_pairs_match_runtime": True,
    }
    passing_window_correlation = {
        "inlet_correlation_source_time_steps_match_runtime": True,
        "inlet_correlation_source_vtk_sha256_match_runtime": True,
        "inlet_correlation_source_step_hash_pairs_match_runtime": True,
    }
    passing_inlet_reasons = module.build_inlet_equivalence_evidence_reasons(
        inlet_source_audit=passing_inlet_source,
        inlet_source_hash_check={"inlet_source_setup_cpp_sha256_matches_current": True},
        inlet_profile_audit=passing_inlet_profile,
        inlet_profile_af_hash_matches=True,
        inlet_profile_window_check=passing_window_profile,
        inlet_correlation_audit=passing_inlet_correlation,
        inlet_correlation_window_check=passing_window_correlation,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if passing_inlet_reasons:
        raise AssertionError(passing_inlet_reasons)

    failing_inlet_source = dict(passing_inlet_source)
    failing_inlet_source.update(
        {
            "paper_grade_inlet_source_gate": "fail",
            "inlet_source_distribution_consistent": False,
            "inlet_source_velocity_field_only": True,
            "inlet_source_method_class": "stg_lite_correlated_velocity_field_only",
            "inlet_source_turbulent_inflow_fidelity_class": "correlated_velocity_field_only",
            "inlet_source_has_correlated_velocity_field_only": True,
            "inlet_source_has_uncorrelated_rms_velocity_field_only": False,
            "synthetic_inlet_correlation_model": "spectral_taylor_projected_velocity_field_only",
            "inlet_distribution_route": "velocity_field_only_without_equilibrium_boundary_define",
            "inlet_distribution_route_gate": "fail",
            "has_equilibrium_boundaries_define": False,
            "has_type_e_equilibrium_boundary_route": False,
            "has_inlet_length_scale_evidence": True,
            "has_source_length_scale_evidence": False,
            "has_metadata_length_scale_evidence": True,
            "inlet_length_scale_evidence_basis": "metadata_gate_only",
            "metadata_length_scale_gate": "diagnostic_only_missing_official_or_precursor_length_scale",
            "has_reynolds_stress_tensor_evidence": False,
            "reynolds_stress_treatment": "documented_isotropic_k_only",
            "has_temporal_filter_state": False,
            "has_layerwise_rms_preserving_inlet_correction": False,
            "streamwise_clipping_enabled": True,
            "paper_grade_inlet_source_gate_reasons": [
                "source_not_distribution_consistent",
                "source_velocity_field_only",
            ],
        }
    )
    failing_inlet_profile = dict(passing_inlet_profile)
    failing_inlet_profile.update({"frame_count": 4, "source_time_steps": [1000, 2000, 3000, 4000]})
    failing_inlet_correlation = dict(passing_inlet_correlation)
    failing_inlet_correlation.update(
        {
            "inlet_tke_gate": "FAIL",
            "frame_count": 4,
            "source_time_steps": [1000, 2000, 3000, 4000],
            "inlet_tke_gate_reasons": ["tke_ratio_outside_tolerance"],
        }
    )
    failing_inlet_reasons = module.build_inlet_equivalence_evidence_reasons(
        inlet_source_audit=failing_inlet_source,
        inlet_source_hash_check={"inlet_source_setup_cpp_sha256_matches_current": False},
        inlet_profile_audit=failing_inlet_profile,
        inlet_profile_af_hash_matches=False,
        inlet_profile_window_check={
            "inlet_profile_source_time_steps_match_runtime": True,
            "inlet_profile_source_vtk_sha256_match_runtime": False,
            "inlet_profile_source_step_hash_pairs_match_runtime": False,
        },
        inlet_correlation_audit=failing_inlet_correlation,
        inlet_correlation_window_check={
            "inlet_correlation_source_time_steps_match_runtime": True,
            "inlet_correlation_source_vtk_sha256_match_runtime": False,
            "inlet_correlation_source_step_hash_pairs_match_runtime": False,
        },
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    for expected_reason in [
        "paper_grade_inlet_source_gate_not_pass:fail",
        "inlet_source_distribution_consistent_not_true:False",
        "inlet_source_velocity_field_only_not_false:True",
        "inlet_distribution_route_gate_not_pass:fail",
        "inlet_distribution_route_missing_equilibrium_boundaries_define",
        "inlet_source_has_equilibrium_boundaries_define_not_true:False",
        "inlet_source_has_type_e_equilibrium_boundary_route_not_true:False",
        "inlet_source_method_class_not_paper_grade:stg_lite_correlated_velocity_field_only",
        "inlet_source_turbulent_inflow_fidelity_class_not_paper_grade:correlated_velocity_field_only",
        "inlet_source_has_correlated_velocity_field_only_not_false:True",
        "inlet_source_has_source_length_scale_evidence_not_true:False",
        "inlet_source_length_scale_evidence_basis_metadata_gate_only",
        "inlet_source_metadata_length_scale_gate_not_pass:diagnostic_only_missing_official_or_precursor_length_scale",
        "inlet_source_has_reynolds_stress_tensor_evidence_not_true:False",
        "inlet_source_reynolds_stress_treatment_not_full_tensor:documented_isotropic_k_only",
        "inlet_source_has_temporal_filter_state_not_true:False",
        "inlet_source_has_layerwise_rms_preserving_inlet_correction_not_true:False",
        "inlet_source_streamwise_clipping_enabled_not_false:True",
        "inlet_source_setup_cpp_sha256_matches_current_not_true:False",
        "inlet_profile_af_csv_sha256_matches_expected_not_true",
        "inlet_profile_frame_count_4_below_minimum_40",
        "inlet_profile_source_step_span_3000_below_minimum_20000",
        "inlet_profile_source_vtk_sha256_match_runtime_not_true:False",
        "inlet_profile_source_step_hash_pairs_match_runtime_not_true:False",
        "inlet_tke_gate_not_pass:fail",
        "inlet_correlation_frame_count_4_below_minimum_40",
        "inlet_correlation_source_step_span_3000_below_minimum_20000",
        "inlet_correlation_source_vtk_sha256_match_runtime_not_true:False",
        "inlet_correlation_source_step_hash_pairs_match_runtime_not_true:False",
        "inlet_tke_reason:tke_ratio_outside_tolerance",
    ]:
        if expected_reason not in failing_inlet_reasons:
            raise AssertionError((expected_reason, failing_inlet_reasons))

    passing_boundary_source = {
        "boundary_source_gate": "pass",
        "paper_grade_boundary_source_gate": "pass",
        "boundary_source_method_class": "wind_tunnel_equivalent_boundary_source",
        "boundary_source_wind_tunnel_equivalent": True,
        "boundary_source_simplified": False,
        "boundary_source_has_simplified_wind_tunnel_surrogate": False,
        "boundary_source_simplified_wind_tunnel_surrogate_gate": "pass",
        "boundary_source_simplified_wind_tunnel_surrogate_reasons": [],
        "boundary_source_fidelity_class": "wind_tunnel_equivalent_complete",
        "boundary_source_has_complete_wind_tunnel_evidence": True,
        "boundary_source_has_empty_advanced_method_stub_only": False,
        "boundary_source_advanced_code_evidence": True,
        "missing_paper_grade_source_evidence": [],
    }
    passing_boundary_protocol = {
        "boundary_protocol_gate": "pass",
        "boundary_evidence_gate": "pass",
        "boundary_run_identity_gate": "pass",
        "evidence_metadata_sha256_matches_current": True,
        "boundary_evidence_files_all_hashed": True,
        "boundary_equivalence_supported": True,
        "boundary_evidence_class_supported": True,
        "boundary_condition_fields_supported": True,
        "clearance_numeric_gate": "pass",
        "blockage_gate": "pass",
        "boundary_protocol_gate_reasons": ["boundary_protocol_pass"],
        "boundary_condition_support_reasons": ["all_boundary_condition_fields_supported"],
        "clearance_numeric_gate_reasons": ["clearance_numeric_evidence_complete"],
        "boundary_run_identity_gate_reasons": ["boundary_evidence_bound_to_current_run"],
    }
    for field in module.REQUIRED_BOUNDARY_SUPPORT_FIELDS:
        passing_boundary_protocol[field] = True
    passing_boundary_runtime = {
        "boundary_runtime_gate": "pass",
        "boundary_runtime_traceability_gate": "pass",
        "boundary_runtime_profile_preservation_gate": "pass",
        "boundary_runtime_inlet_gate": "pass",
        "boundary_runtime_side_top_gate": "pass",
        "boundary_runtime_side_top_normal_leakage_gate": "pass",
        "boundary_runtime_outlet_gate": "pass",
        "boundary_runtime_gate_reasons": ["boundary_runtime_faces_preserve_af_profile"],
        "boundary_runtime_traceability_gate_reasons": ["boundary_runtime_window_traceable"],
        "frame_count": 40,
        "selected_last_window": True,
        "source_time_steps": list(range(1000, 41000, 1000)),
        "source_vtk_sha256": [f"{idx:064x}" for idx in range(40)],
    }
    passing_boundary_reasons = module.build_boundary_equivalence_evidence_reasons(
        boundary_source_audit=passing_boundary_source,
        boundary_source_hash_check={"boundary_source_setup_cpp_sha256_matches_current": True},
        boundary_protocol_audit=passing_boundary_protocol,
        boundary_runtime_audit=passing_boundary_runtime,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    if passing_boundary_reasons:
        raise AssertionError(passing_boundary_reasons)

    failing_boundary_source = dict(passing_boundary_source)
    failing_boundary_source.update(
        {
            "paper_grade_boundary_source_gate": "fail",
            "boundary_source_method_class": "simplified_type_e_box",
            "boundary_source_wind_tunnel_equivalent": False,
            "boundary_source_simplified": True,
            "boundary_source_has_simplified_wind_tunnel_surrogate": True,
            "boundary_source_simplified_wind_tunnel_surrogate_gate": "fail",
            "boundary_source_simplified_wind_tunnel_surrogate_reasons": ["simplified_type_e_box"],
            "boundary_source_fidelity_class": "simplified_type_e_box",
            "boundary_source_has_complete_wind_tunnel_evidence": False,
            "boundary_source_advanced_code_evidence": False,
            "missing_paper_grade_source_evidence": ["floor_roughness_source"],
        }
    )
    failing_boundary_protocol = dict(passing_boundary_protocol)
    failing_boundary_protocol.update(
        {
            "boundary_protocol_gate": "fail",
            "boundary_evidence_gate": "fail",
            "evidence_metadata_sha256_matches_current": False,
            "roughness_treatment_supported": False,
            "clearance_numeric_gate": "fail",
            "blockage_gate": "fail",
            "missing_evidence_fields": ["roughness_length_m"],
        }
    )
    failing_boundary_runtime = dict(passing_boundary_runtime)
    failing_boundary_runtime.update(
        {
            "boundary_runtime_side_top_normal_leakage_gate": "fail",
            "frame_count": 4,
            "selected_last_window": False,
            "source_time_steps": [1000, 2000, 3000, 4000],
            "source_vtk_sha256": ["a", "b", "c", "d"],
        }
    )
    failing_boundary_reasons = module.build_boundary_equivalence_evidence_reasons(
        boundary_source_audit=failing_boundary_source,
        boundary_source_hash_check={"boundary_source_setup_cpp_sha256_matches_current": False},
        boundary_protocol_audit=failing_boundary_protocol,
        boundary_runtime_audit=failing_boundary_runtime,
        min_avg_frames=40,
        min_avg_step_span=20000,
    )
    for expected_reason in [
        "paper_grade_boundary_source_gate_not_pass:fail",
        "boundary_source_wind_tunnel_equivalent_not_true:False",
        "boundary_source_simplified_not_false:True",
        "boundary_source_fidelity_class_not_paper_grade:simplified_type_e_box",
        "boundary_source_has_complete_wind_tunnel_evidence_not_true:False",
        "boundary_source_advanced_code_evidence_not_true:False",
        "boundary_source_missing_paper_grade_evidence:floor_roughness_source",
        "boundary_source_setup_cpp_sha256_matches_current_not_true:False",
        "boundary_protocol_gate_not_pass:fail",
        "boundary_evidence_metadata_sha256_matches_current_not_true:False",
        "boundary_required_support_field_not_true:roughness_treatment_supported",
        "boundary_clearance_numeric_gate_not_pass:fail",
        "boundary_blockage_gate_not_pass:fail",
        "boundary_runtime_side_top_normal_leakage_gate_not_pass:fail",
        "boundary_runtime_frame_count_4_below_minimum_40",
        "boundary_runtime_source_step_span_3000_below_minimum_20000",
        "boundary_runtime_selected_last_window_not_true:False",
    ]:
        if expected_reason not in failing_boundary_reasons:
            raise AssertionError((expected_reason, failing_boundary_reasons))

    reasons = [
        "runtime_average_step_span_too_short",
        "runtime_average_window_frame_count_4_below_minimum_40",
        "runtime_average_step_span_3000_below_minimum_20000",
        "probe_uref_mismatch",
        "probe_uref_mismatch_count_80",
        "probe_out_of_tolerance_count_12",
        "probe_compared_component_speed_expected_abs_streamwise_ratio",
        "probe_official_coverage_72_of_80",
        "paper_grade_boundary_source_gate_not_pass",
        "boundary_missing_evidence_field_floor_roughness_source",
        "boundary_required_support_field_outlet_reflection_check_supported_not_supported",
        "lbm_stability_reason:estimated_max_profile_mach_above_0.2:0.24",
        "lbm_stability_reason:runtime_lbm_stability_gate_not_pass:fail",
        "inlet_source_velocity_field_only",
        "inlet_source_uses_uncorrelated_random_rms",
        "inlet_source_missing_three_component_fluctuation_evidence",
        "inlet_source_missing_k_driven_three_component_stg_evidence",
        "systematic_bias_after_prerequisites",
    ]
    priorities = module.build_native_diagnostic_priority(reasons)
    keys = [item["key"] for item in priorities]
    expected = [
        "turbulent_inlet_method_and_u_k_preservation",
        "boundary_roughness_blockage",
        "time_averaging_stationarity",
        "coordinate_component_normalization",
        "lbm_stability_scaling",
        "systematic_bias_after_prerequisites",
    ]
    if keys[:6] != expected:
        raise AssertionError(keys)

    top = priorities[0]
    if top["rank"] != 0:
        raise AssertionError(top)
    if top["key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(top)
    if "RMS/k velocity perturbations alone remain diagnostic" not in top["diagnosis"]:
        raise AssertionError(top["diagnosis"])
    if "inlet_source_uses_uncorrelated_random_rms" not in top["reasons"]:
        raise AssertionError(top)
    if "inlet_source_missing_k_driven_three_component_stg_evidence" not in top["reasons"]:
        raise AssertionError(top)

    closure = module.build_native_precondition_closure(reasons)
    expected_closure_keys = [
        "turbulent_inlet_method_and_u_k_preservation",
        "boundary_roughness_blockage",
        "time_averaging_stationarity",
        "coordinate_component_normalization",
        "lbm_stability_scaling",
        "grid_resolution_and_systematic_bias",
    ]
    if closure["gate"] != "fail":
        raise AssertionError(closure)
    if closure["failed_stage_keys"] != expected_closure_keys:
        raise AssertionError(closure["failed_stage_keys"])
    if closure["top_blocking_stage_key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(closure)
    if closure["top_blocking_stage_reason_count"] <= 0:
        raise AssertionError(closure)

    synthetic_only_closure = module.build_native_precondition_closure(
        [
            "planned_synthetic_inlet_sampling_gate_not_pass:diagnostic_only",
            "planned_synthetic_inlet_sampling_reason:planned_stg_refresh_count_40_below_minimum_200",
        ]
    )
    if synthetic_only_closure["top_blocking_stage_key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(synthetic_only_closure)
    if synthetic_only_closure["failed_stage_keys"] != ["turbulent_inlet_method_and_u_k_preservation"]:
        raise AssertionError(synthetic_only_closure)

    actual_vtk_only_closure = module.build_native_precondition_closure(
        [
            "actual_vtk_output_reason:actual_vtk_frame_count_1_below_minimum_40",
            "native_runner_reason:actual_vtk_frame_count_1_does_not_match_expected_40",
        ]
    )
    if actual_vtk_only_closure["top_blocking_stage_key"] != "time_averaging_stationarity":
        raise AssertionError(actual_vtk_only_closure)
    if actual_vtk_only_closure["failed_stage_keys"] != ["time_averaging_stationarity"]:
        raise AssertionError(actual_vtk_only_closure)

    strict_runtime_only_closure = module.build_native_precondition_closure(
        [
            "strict_native_run_gate_not_pass:fail",
            "strict_native_run_reason:run_freshness_gate_not_pass:diagnostic_only",
        ]
    )
    if strict_runtime_only_closure["top_blocking_stage_key"] != "time_averaging_stationarity":
        raise AssertionError(strict_runtime_only_closure)
    if strict_runtime_only_closure["failed_stage_keys"] != ["time_averaging_stationarity"]:
        raise AssertionError(strict_runtime_only_closure)

    prescription = module.build_native_rerun_prescription(
        priorities,
        closure,
        min_avg_frames=40,
        min_avg_step_span=20000,
        average_last_n=40,
    )
    if prescription["gate"] != "fail":
        raise AssertionError(prescription)
    if prescription["top_key"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(prescription)
    if prescription["experiment"] != "native_empty_tunnel_inlet_preservation_first":
        raise AssertionError(prescription)
    for control in [
        "use_customtable_af_u_and_k_profile",
        "prove_final_window_inlet_u_profile_gate_pass",
        "prove_final_window_inlet_k_profile_gate_pass",
        "prove_inlet_correlation_and_tke_gates_pass",
        "prove_planned_synthetic_inlet_sampling_gate_pass",
    ]:
        if control not in prescription["required_controls"]:
            raise AssertionError(prescription)
    if "average_last_n=40" not in prescription["minimum_final_window"]:
        raise AssertionError(prescription)
    if prescription["accuracy_interpretation_allowed"] is not False:
        raise AssertionError(prescription)
    if prescription["accuracy_interpretation_gate"] != "fail":
        raise AssertionError(prescription)
    if prescription["accuracy_interpretation_status"] != "blocked_until_native_preconditions_closed":
        raise AssertionError(prescription)
    if prescription["accuracy_interpretation_blocker"] != "turbulent_inlet_method_and_u_k_preservation":
        raise AssertionError(prescription)
    if prescription["accuracy_interpretation_required_experiment"] != "native_empty_tunnel_inlet_preservation_first":
        raise AssertionError(prescription)
    if "Do not interpret probe accuracy yet" not in prescription["summary"]:
        raise AssertionError(prescription)

    empty_closure = module.build_native_precondition_closure([])
    if empty_closure["gate"] != "pass":
        raise AssertionError(empty_closure)
    if empty_closure["failed_stage_count"] != 0:
        raise AssertionError(empty_closure)
    if empty_closure["closed_stage_count"] != empty_closure["stage_count"]:
        raise AssertionError(empty_closure)

    empty_prescription = module.build_native_rerun_prescription([], empty_closure, 40, 20000, 40)
    if empty_prescription["gate"] != "pass":
        raise AssertionError(empty_prescription)
    if empty_prescription["experiment"] != "accuracy_interpretation_ready":
        raise AssertionError(empty_prescription)
    if empty_prescription["accuracy_interpretation_allowed"] is not True:
        raise AssertionError(empty_prescription)
    if empty_prescription["accuracy_interpretation_gate"] != "pass":
        raise AssertionError(empty_prescription)
    if empty_prescription["accuracy_interpretation_status"] != "allowed_after_native_preconditions_closed":
        raise AssertionError(empty_prescription)

    time_priority = next(item for item in priorities if item["key"] == "time_averaging_stationarity")
    if "runtime_average_window_frame_count_4_below_minimum_40" not in time_priority["reasons"]:
        raise AssertionError(time_priority)
    if "runtime_average_step_span_3000_below_minimum_20000" not in time_priority["reasons"]:
        raise AssertionError(time_priority)

    coordinate_priority = next(item for item in priorities if item["key"] == "coordinate_component_normalization")
    for reason in [
        "probe_uref_mismatch_count_80",
        "probe_out_of_tolerance_count_12",
        "probe_compared_component_speed_expected_abs_streamwise_ratio",
        "probe_official_coverage_72_of_80",
    ]:
        if reason not in coordinate_priority["reasons"]:
            raise AssertionError(coordinate_priority)

    boundary_only = module.build_native_diagnostic_priority(
        [
            "boundary_source_simplified",
            "blockage_gate_not_pass",
            "boundary_missing_evidence_field_floor_roughness_source",
        ]
    )
    if boundary_only[0]["key"] != "boundary_roughness_blockage":
        raise AssertionError(boundary_only)
    if "boundary_missing_evidence_field_floor_roughness_source" not in boundary_only[0]["reasons"]:
        raise AssertionError(boundary_only)

    print("native_preconditions_priority_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
