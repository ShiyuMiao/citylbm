#!/usr/bin/env python3
"""Audit generated setup.cpp inlet-method evidence.

This script does not run CFD. It prevents paper-grade validation from relying
only on metadata labels such as "synthetic-eddy" or "digital-filter" by
checking whether the generated source contains the expected inlet code and
whether that code is distribution-consistent or only velocity-field forcing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated FluidX3D setup.cpp inlet implementation evidence.")
    parser.add_argument("--setup", required=True, help="Generated setup.cpp path.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--out", required=True, help="Output inlet_source_audit.json.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def metadata_value(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def nested_bool(metadata: Dict[str, Any], *keys: str) -> Optional[bool]:
    current: Any = metadata
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    if isinstance(current, bool):
        return current
    if isinstance(current, (int, float)):
        return bool(current)
    text = str(current).strip().lower()
    if text in {"true", "1", "yes", "y", "pass", "enabled"}:
        return True
    if text in {"false", "0", "no", "n", "fail", "disabled"}:
        return False
    return None


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def first_int_regex(text: str, pattern: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def strip_cpp_string_literals(text: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)


def distribution_reconstruction_evidence(code: str) -> Dict[str, Any]:
    distribution_pattern = re.compile(
        r"lbm\.f\s*\[|lbm\.f0|lbm\.feq|calculate_f_eq|device_sem_stress_ddf|stress_ddf",
        flags=re.IGNORECASE,
    )
    contextual_count = 0
    generic_count = 0
    for match in distribution_pattern.finditer(code):
        generic_count += 1
        window = code[max(0, match.start() - 700) : min(len(code), match.end() + 900)]
        has_inlet_context = contains_any(
            window,
            [
                "TYPE_E",
                "syntheticTurbulentInlet",
                "windProfile",
                "inlet",
                "side_inlet",
                "sideInlet",
            ],
        )
        has_reconstruction_context = contains_any(
            window,
            [
                "calculate_f_eq",
                "feq",
                "stress_ddf",
                "distribution_consistent",
                "reconstruct",
                "reconstruction",
                "equilibrium distribution",
            ],
        )
        if has_inlet_context and has_reconstruction_context:
            contextual_count += 1
    return {
        "distribution_write_count": generic_count,
        "inlet_distribution_reconstruction_count": contextual_count,
        "has_distribution_function_write": generic_count > 0,
        "has_inlet_distribution_reconstruction": contextual_count > 0,
    }


def strip_cpp_comments(text: str) -> str:
    """Remove C/C++ comments while preserving strings and line structure."""
    output: List[str] = []
    index = 0
    in_string = False
    in_char = False
    escaped = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if in_char:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_char = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue

        if char == "'":
            in_char = True
            output.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            output.append("\n")
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                if text[index] in "\r\n":
                    output.append("\n")
                index += 1
            index += 2
            continue

        output.append(char)
        index += 1

    return "".join(output)


def main() -> int:
    args = parse_args()
    setup_path = Path(args.setup).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else None
    out_path = Path(args.out).expanduser().resolve()
    metadata = read_json(metadata_path)

    reasons: List[str] = []
    if not setup_path.exists():
        reasons.append("setup_cpp_missing")
        source = ""
        setup_hash = ""
    else:
        source = setup_path.read_text(encoding="utf-8-sig", errors="replace")
        setup_hash = sha256(setup_path)

    audited_source = strip_cpp_comments(source)
    implementation_source = strip_cpp_string_literals(audited_source)
    audited_source_lower = audited_source.lower()
    implementation_source_lower = implementation_source.lower()
    audited_source_hash = hashlib.sha256(audited_source.encode("utf-8")).hexdigest().upper() if audited_source else ""
    metadata_method = metadata_value(metadata, "SyntheticTurbulentInletMethod", "TurbulenceMethod")
    metadata_treatment = metadata_value(metadata, "SyntheticTurbulentInletDistributionTreatment")
    metadata_class = metadata_value(metadata, "PaperGradeInletMethodClass", "InletMethodClass")
    synthetic_requested = any(
        token in " ".join([metadata_method, metadata_treatment, metadata_class]).lower()
        for token in ["synthetic", "stg", "digital", "filter", "sem", "dfm", "precursor", "recycling"]
    )
    synthetic_enabled = nested_bool(metadata, "SyntheticEddy", "Enabled")
    if synthetic_enabled is True:
        synthetic_requested = True

    selected_method_text = " ".join([metadata_method, metadata_treatment, metadata_class]).lower()
    synthetic_eddy_selected = (
        "synthetic-eddy" in selected_method_text
        or "synthetic_eddy" in selected_method_text
        or has_regex(implementation_source, r"\bconst\s+uint\s+turbulence_method\s*=\s*5u\b")
    )
    digital_filter_selected = (
        "digital-filter" in selected_method_text
        or "digital_filter" in selected_method_text
        or "dfm" in selected_method_text
        or has_regex(implementation_source, r"\bconst\s+uint\s+turbulence_method\s*=\s*(3u|4u|7u)\b")
    )

    has_custom_table = "profile_z_m" in implementation_source_lower and "profile_u_lbm" in implementation_source_lower
    has_k_profile = "profile_k_lbm" in implementation_source_lower
    has_profile_origin_z_m = "profile_origin_z_m" in implementation_source_lower
    has_origin_aware_profile_height = (
        has_profile_origin_z_m
        and has_regex(
            implementation_source,
            r"z_m\s*=\s*profile_origin_z_m\s*\+\s*\(\s*\(?\s*float\s*\)?\s*z_cell\s*\+\s*0\.5f\s*\)\s*\*",
        )
    )
    has_native_synthetic_eddy_function = (
        has_regex(implementation_source, r"\bupdateSyntheticEddyPlane\s*=\s*\[")
        or has_regex(implementation_source, r"\bupdateSyntheticEddyPlane\s*\(")
    )
    has_native_turbulent_wind_function = has_regex(implementation_source, r"\bturbulentWind\s*=\s*\[")
    has_native_apply_inlet_function = (
        has_regex(implementation_source, r"\bapplyInlet\s*=\s*\[")
        or has_regex(implementation_source, r"\bapplyInlet\s*\(")
    )
    has_native_synthetic_eddy_population = contains_any(
        implementation_source,
        [
            "synthetic_eddy_count",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
            "synthetic_eddy_recycle_lx_cells",
        ],
    )
    has_native_synthetic_eddy_shape = contains_any(
        implementation_source,
        ["compactCosine", "periodicDistance", "signedHash", "hash01"],
    )
    has_native_synthetic_eddy_refresh = (
        has_regex(implementation_source, r"updateSyntheticEddyPlane\s*\(\s*t_step\s*\)")
        and has_regex(implementation_source, r"updateDigitalFilter\s*\(\s*t_step\s*\)")
    )
    native_stg_mode_count = first_int_regex(
        implementation_source,
        r"synthetic_eddy_count\s*=\s*(\d+)",
    )
    has_native_synthetic_eddy_evidence = (
        synthetic_eddy_selected
        and has_native_synthetic_eddy_function
        and has_native_turbulent_wind_function
        and has_native_apply_inlet_function
        and has_native_synthetic_eddy_population
        and has_native_synthetic_eddy_shape
    )
    has_stg_function = "applysyntheticturbulentinlet" in implementation_source_lower or has_native_synthetic_eddy_evidence
    has_stg_refresh_loop = (
        count_regex(implementation_source, r"applySyntheticTurbulentInlet\s*\(") >= 2
        or (has_native_apply_inlet_function and has_native_synthetic_eddy_refresh)
    )
    has_velocity_field_write = contains_any(implementation_source, ["lbm.u.x", "lbm.u.y", "lbm.u.z"])
    distribution_evidence = distribution_reconstruction_evidence(implementation_source)
    has_distribution_write = distribution_evidence["has_distribution_function_write"]
    has_inlet_distribution_reconstruction = distribution_evidence["has_inlet_distribution_reconstruction"]
    has_digital_filter_token = contains_any(implementation_source, ["digital_filter", "digital-filter", "dfm", "filter kernel"])
    has_sem_token = contains_any(
        implementation_source,
        [
            "synthetic_eddy_method",
            "sem_distribution",
            "synthetic eddy method",
            "synthetic_eddy_count",
            "updateSyntheticEddyPlane",
        ],
    )
    has_precursor_token = contains_any(implementation_source, ["precursor", "recycling_rescaling", "recycling-rescaling"])
    has_digital_filter = (
        has_regex(implementation_source, r"\b\w*(digital_filter|digitalfilter|dfm)\w*\s*\(")
        or has_regex(implementation_source, r"\b(filter_kernel|filterKernel)\w*\s*(\[|=|\{)")
    )
    has_digital_filter_kernel = has_regex(
        implementation_source,
        r"\b\w*(digital_filter_kernel|digitalFilterKernel|filter_kernel|filterKernel|dfm_kernel|dfmKernel)\w*\s*(\[|=|\{|\()",
    )
    has_digital_filter_state = contains_any(
        implementation_source,
        [
            "filtered_random_field",
            "filter_state",
            "digital_filter_state",
            "temporal_filter",
            "spatial_filter",
            "inlet_fluctuation_field",
            "streamwise_filter_buffer",
            "filter_history",
        ],
    )
    has_sem = (
        has_regex(implementation_source, r"\b\w*(synthetic_eddy|syntheticEddy|sem_distribution|semDistribution)\w*\s*\(")
        or has_regex(implementation_source, r"\b(sem_eddy|semEddy|eddy_center|eddyCenter)\w*\s*(\[|=|\{)")
        or has_native_synthetic_eddy_evidence
    )
    has_sem_eddy_population = contains_any(
        implementation_source,
        [
            "eddy_center",
            "eddyCenter",
            "eddy_radius",
            "eddyRadius",
            "eddy_strength",
            "eddyStrength",
            "eddy_lifetime",
            "eddyLifetime",
            "sem_eddy",
            "semEddy",
            "synthetic_eddy_count",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
        ],
    )
    has_precursor = has_regex(
        implementation_source,
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|recycleRescale)\w*\s*\(",
    )
    has_precursor_recycling_field = contains_any(
        implementation_source,
        [
            "precursor_velocity",
            "precursorVelocity",
            "precursor_field",
            "precursorField",
            "recycling_plane",
            "recyclingPlane",
            "recycle_plane",
            "recyclePlane",
            "recycling_buffer",
            "recyclingBuffer",
            "rescale_profile",
            "rescaleProfile",
            "inflow_database",
            "inflowDatabase",
            "stored_inflow",
            "storedInflow",
            "precursor_vtk",
            "precursorVtk",
        ],
    )
    has_distribution_consistent_digital_filter = (
        has_digital_filter
        and has_digital_filter_kernel
        and has_digital_filter_state
        and has_inlet_distribution_reconstruction
    )
    has_distribution_consistent_sem = (
        has_sem
        and has_sem_eddy_population
        and has_inlet_distribution_reconstruction
    )
    has_distribution_consistent_precursor = has_precursor and has_precursor_recycling_field
    advanced_token_only = (
        (has_digital_filter_token and not has_digital_filter)
        or (has_sem_token and not has_sem)
        or (has_precursor_token and not has_precursor)
    )
    has_spectral_modes = contains_any(
        implementation_source,
        [
            "citylbm_stg_mode_count",
            "citylbm_mode_wave",
            "citylbm_mode_amplitude",
        ],
    )
    stg_mode_count = first_int_regex(
        implementation_source,
        r"citylbm_stg_mode_count\s*=\s*(\d+)",
    )
    effective_stg_mode_count = stg_mode_count if stg_mode_count is not None else native_stg_mode_count
    has_taylor_advection = contains_any(
        implementation_source,
        ["advected_x", "advected_y", "advected_z", "frozen-turbulence", "x0 - adv"],
    )
    has_transverse_projection = contains_any(
        implementation_source,
        [
            "ak*kx/kk",
            "ak * kx / kk",
            "projected normal to their wave vector",
            "divergence-reduced",
        ],
    )
    has_length_scale = contains_any(
        implementation_source,
        [
            "correlation_length",
            "citylbm_stg_lx",
            "citylbm_stg_corr_cells",
            "length_scale",
            "correlation cells",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
        ],
    )
    has_update_interval = (
        "citylbm_stg_update_interval" in implementation_source_lower
        or "inlet_update_interval" in implementation_source_lower
    )
    refresh_current_time_calls = count_regex(
        implementation_source,
        r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)",
    )
    has_stg_refresh_with_current_time = refresh_current_time_calls >= 1
    native_refresh_current_time_calls = count_regex(
        implementation_source,
        r"applyInlet\s*\(\s*(current|t_step|step|now)\s*\)",
    )
    if native_refresh_current_time_calls >= 1:
        has_stg_refresh_with_current_time = True
    has_update_interval_run_control = has_regex(
        implementation_source,
        r"steps_to_run\s*=\s*[^;\n]*citylbm_stg_update_interval",
    ) or has_regex(
        implementation_source,
        r"steps_to_run\s*>\s*citylbm_stg_update_interval\s*\)\s*steps_to_run\s*=\s*citylbm_stg_update_interval",
    ) or has_regex(
        implementation_source,
        r"run_chunk\s*=\s*[^;\n]*inlet_update_interval",
    )
    has_segmented_stg_run_loop = (
        has_update_interval_run_control
        and has_regex(implementation_source, r"lbm\.run\s*\(\s*steps_to_run\s*\)")
        and (
            has_regex(
                implementation_source,
                r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)\s*;\s*lbm\.run\s*\(\s*steps_to_run\s*\)",
            )
            or has_regex(
                implementation_source,
                r"applyInlet\s*\(\s*current\s*\).*?lbm\.run\s*\(\s*steps_to_run\s*\)",
            )
        )
    )
    has_bounded_amplitude = contains_any(
        implementation_source,
        ["citylbm_stg_max_fraction", "max_fraction", "amplitude cap"],
    )
    random_source_tokens = [
        r"\brand\s*\(",
        r"\brandom\s*\(",
        r"\bstd\s*::\s*rand\s*\(",
        r"\bcurand\w*\s*\(",
        r"\bwhite_noise\b",
        r"\bper_node_random\b",
        r"\bnode_random\b",
        r"\buncorrelated_random\b",
        r"\brms_random\b",
    ]
    random_source_matches = [
        pattern for pattern in random_source_tokens if has_regex(implementation_source, pattern)
    ]
    random_inlet_context = has_regex(
        implementation_source,
        r"(applySyntheticTurbulentInlet|syntheticTurbulentInlet|TYPE_E|profile_k_lbm|sigma)\b",
    )
    has_uncorrelated_random_inlet = (
        bool(random_source_matches)
        and random_inlet_context
        and has_velocity_field_write
        and not (
            (has_spectral_modes and has_taylor_advection and has_transverse_projection)
            or has_native_synthetic_eddy_evidence
        )
    )
    if has_distribution_consistent_precursor:
        synthetic_correlation_model = "precursor_or_recycling"
    elif has_distribution_consistent_digital_filter:
        synthetic_correlation_model = "digital_filter_distribution_consistent"
    elif has_distribution_consistent_sem:
        synthetic_correlation_model = "synthetic_eddy_distribution_consistent"
    elif has_spectral_modes and has_taylor_advection and has_transverse_projection:
        synthetic_correlation_model = "spectral_taylor_projected_velocity_field_only"
    elif has_native_synthetic_eddy_evidence and has_taylor_advection:
        synthetic_correlation_model = "native_synthetic_eddy_velocity_field_only"
    elif has_uncorrelated_random_inlet:
        synthetic_correlation_model = "uncorrelated_random_rms_velocity_field_only"
    elif has_stg_function and has_velocity_field_write:
        synthetic_correlation_model = "velocity_field_only_without_correlation_evidence"
    else:
        synthetic_correlation_model = "none"

    source_method_class = "none"
    if has_distribution_consistent_precursor:
        source_method_class = "precursor_or_recycling"
    elif has_distribution_consistent_digital_filter:
        source_method_class = "digital_filter_distribution_consistent"
    elif has_distribution_consistent_sem:
        source_method_class = "synthetic_eddy_distribution_consistent"
    elif has_stg_function and has_velocity_field_write and (
        has_spectral_modes
        or has_taylor_advection
        or has_transverse_projection
        or has_native_synthetic_eddy_evidence
    ):
        source_method_class = "stg_lite_correlated_velocity_field_only"
    elif has_stg_function and has_velocity_field_write:
        source_method_class = "stg_lite_velocity_field_only"
    elif has_precursor:
        source_method_class = "named_method_without_precursor_recycling_field_evidence"
    elif has_digital_filter or has_sem:
        source_method_class = "named_method_without_distribution_evidence"
    elif has_velocity_field_write:
        source_method_class = "mean_profile_velocity_field_only"

    source_distribution_consistent = source_method_class in {
        "precursor_or_recycling",
        "digital_filter_distribution_consistent",
        "synthetic_eddy_distribution_consistent",
    }
    advanced_code_evidence = (
        has_distribution_consistent_digital_filter
        or has_distribution_consistent_sem
        or has_distribution_consistent_precursor
    )
    source_velocity_only = source_method_class in {
        "stg_lite_velocity_field_only",
        "stg_lite_correlated_velocity_field_only",
        "mean_profile_velocity_field_only",
        "named_method_without_distribution_evidence",
        "named_method_without_precursor_recycling_field_evidence",
    }

    if synthetic_requested and not has_stg_function and not has_digital_filter and not has_sem and not has_precursor:
        reasons.append("metadata_requests_turbulent_inlet_but_source_has_no_inlet_method")
    if has_custom_table and not has_profile_origin_z_m:
        reasons.append("custom_table_source_missing_profile_origin_z_m")
    if has_custom_table and not has_origin_aware_profile_height:
        reasons.append("custom_table_source_not_origin_aware_for_profile_height")
    if advanced_token_only:
        reasons.append("advanced_inlet_method_tokens_without_code_evidence")
    if has_digital_filter and digital_filter_selected and not has_digital_filter_kernel:
        reasons.append("digital_filter_source_missing_filter_kernel")
    if has_digital_filter and digital_filter_selected and not has_digital_filter_state:
        reasons.append("digital_filter_source_missing_spatiotemporal_filter_state")
    if has_sem and not has_sem_eddy_population:
        reasons.append("sem_source_missing_eddy_population")
    if has_precursor and not has_precursor_recycling_field:
        reasons.append("precursor_recycling_source_missing_recycled_field_evidence")
    if synthetic_requested and has_stg_function and not has_k_profile:
        reasons.append("synthetic_inlet_source_missing_profile_k_lbm")
    if synthetic_requested and has_stg_function and not has_stg_refresh_loop:
        reasons.append("synthetic_inlet_not_refreshed_in_run_loop")
    if synthetic_requested and has_stg_function and not has_stg_refresh_with_current_time:
        reasons.append("synthetic_inlet_missing_refresh_with_current_solver_time")
    if synthetic_requested and has_stg_function and not has_length_scale:
        reasons.append("synthetic_inlet_missing_length_scale_source")
    if synthetic_requested and has_stg_function and not (has_spectral_modes or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_spectral_modes")
    if synthetic_requested and has_stg_function and effective_stg_mode_count is not None and effective_stg_mode_count < 32:
        reasons.append("synthetic_inlet_too_few_spectral_modes")
    if synthetic_requested and has_stg_function and not has_taylor_advection:
        reasons.append("synthetic_inlet_missing_temporal_advection")
    if synthetic_requested and has_stg_function and not (has_transverse_projection or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_transverse_projection")
    if synthetic_requested and has_stg_function and not has_update_interval:
        reasons.append("synthetic_inlet_missing_update_interval")
    if synthetic_requested and has_stg_function and has_update_interval and not has_update_interval_run_control:
        reasons.append("synthetic_inlet_update_interval_not_used_in_run_loop")
    if synthetic_requested and has_stg_function and not has_segmented_stg_run_loop:
        reasons.append("synthetic_inlet_refresh_not_coupled_to_segmented_lbm_run")
    if synthetic_requested and has_stg_function and not (has_bounded_amplitude or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_amplitude_cap")
    if synthetic_requested and has_uncorrelated_random_inlet:
        reasons.append("synthetic_inlet_uses_uncorrelated_random_rms")

    metadata_claims_distribution = any(
        token in " ".join([metadata_treatment, metadata_class]).lower()
        for token in ["distribution_consistent", "digital_filter", "digital-filter", "sem", "dfm", "precursor", "recycling"]
    )
    if metadata_claims_distribution and not source_distribution_consistent:
        reasons.append("metadata_claims_distribution_consistency_without_source_evidence")
    if metadata_claims_distribution and has_distribution_write and not has_inlet_distribution_reconstruction and not has_precursor:
        reasons.append("distribution_function_write_not_tied_to_inlet_reconstruction")

    source_gate = "pass" if not reasons else "fail"
    paper_gate_reasons: List[str] = []
    if not source_distribution_consistent:
        paper_gate_reasons.append("source_not_distribution_consistent")
    if source_velocity_only:
        paper_gate_reasons.append("source_velocity_field_only")
    paper_gate = "pass" if not paper_gate_reasons else "fail"

    report: Dict[str, Any] = {
        "schema": "citylbm.inlet_source_audit.v1",
        "generated_at_utc": utc_now(),
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": setup_hash,
        "comment_stripped_setup_cpp_sha256": audited_source_hash,
        "inlet_source_comment_stripped_code_audit": True,
        "advanced_inlet_evidence_uses_comment_stripped_code": True,
        "metadata": str(metadata_path) if metadata_path else "",
        "metadata_method": metadata_method,
        "metadata_distribution_treatment": metadata_treatment,
        "metadata_method_class": metadata_class,
        "metadata_synthetic_eddy_enabled": synthetic_enabled,
        "synthetic_inlet_requested": synthetic_requested,
        "has_custom_table_profile": has_custom_table,
        "has_profile_k_lbm": has_k_profile,
        "has_profile_origin_z_m": has_profile_origin_z_m,
        "has_origin_aware_profile_height": has_origin_aware_profile_height,
        "has_synthetic_inlet_function": has_stg_function,
        "has_synthetic_inlet_refresh_loop": has_stg_refresh_loop,
        "has_native_synthetic_eddy_evidence": has_native_synthetic_eddy_evidence,
        "has_native_synthetic_eddy_function": has_native_synthetic_eddy_function,
        "has_native_turbulent_wind_function": has_native_turbulent_wind_function,
        "has_native_apply_inlet_function": has_native_apply_inlet_function,
        "has_native_synthetic_eddy_population": has_native_synthetic_eddy_population,
        "has_native_synthetic_eddy_shape": has_native_synthetic_eddy_shape,
        "has_native_synthetic_eddy_refresh": has_native_synthetic_eddy_refresh,
        "has_velocity_field_write": has_velocity_field_write,
        "has_distribution_function_write": has_distribution_write,
        "distribution_function_write_count": distribution_evidence["distribution_write_count"],
        "has_inlet_distribution_reconstruction": has_inlet_distribution_reconstruction,
        "inlet_distribution_reconstruction_count": distribution_evidence["inlet_distribution_reconstruction_count"],
        "inlet_source_advanced_code_evidence": advanced_code_evidence,
        "has_digital_filter_evidence": has_digital_filter,
        "has_digital_filter_token": has_digital_filter_token,
        "has_digital_filter_kernel_evidence": has_digital_filter_kernel,
        "has_digital_filter_state_evidence": has_digital_filter_state,
        "has_sem_evidence": has_sem,
        "has_sem_token": has_sem_token,
        "has_sem_eddy_population_evidence": has_sem_eddy_population,
        "has_precursor_or_recycling_evidence": has_precursor,
        "has_precursor_or_recycling_token": has_precursor_token,
        "has_precursor_recycling_field_evidence": has_precursor_recycling_field,
        "distribution_consistency_basis": (
            "precursor_or_recycling_field"
            if has_distribution_consistent_precursor
            else "digital_filter_kernel_state_distribution_reconstruction"
            if has_distribution_consistent_digital_filter
            else "sem_eddy_population_distribution_reconstruction"
            if has_distribution_consistent_sem
            else "missing"
        ),
        "advanced_inlet_method_token_only": advanced_token_only,
        "has_spectral_mode_evidence": has_spectral_modes,
        "synthetic_inlet_spectral_mode_count": effective_stg_mode_count,
        "citylbm_stg_spectral_mode_count": stg_mode_count,
        "native_synthetic_eddy_count": native_stg_mode_count,
        "minimum_recommended_spectral_mode_count": 32,
        "has_taylor_advection_evidence": has_taylor_advection,
        "has_transverse_projection_evidence": has_transverse_projection,
        "has_length_scale_evidence": has_length_scale,
        "has_update_interval": has_update_interval,
        "stg_refresh_current_time_call_count": refresh_current_time_calls,
        "native_refresh_current_time_call_count": native_refresh_current_time_calls,
        "has_synthetic_inlet_refresh_with_current_time": has_stg_refresh_with_current_time,
        "has_update_interval_run_control": has_update_interval_run_control,
        "has_segmented_stg_run_loop": has_segmented_stg_run_loop,
        "has_bounded_amplitude": has_bounded_amplitude,
        "has_uncorrelated_random_inlet": has_uncorrelated_random_inlet,
        "uncorrelated_random_inlet_patterns": random_source_matches,
        "synthetic_inlet_correlation_model": synthetic_correlation_model,
        "inlet_source_method_class": source_method_class,
        "inlet_source_distribution_consistent": source_distribution_consistent,
        "inlet_source_velocity_field_only": source_velocity_only,
        "inlet_source_gate": source_gate,
        "inlet_source_gate_reasons": reasons or ["inlet_source_consistent_with_declared_metadata"],
        "paper_grade_inlet_source_gate": paper_gate,
        "paper_grade_inlet_source_gate_reasons": paper_gate_reasons or ["source_distribution_consistent"],
        "recommended_next_action": (
            "Use source evidence plus final-window VTK inlet profile/correlation audits. Do not describe a velocity-field "
            "STG-lite source as digital-filter, SEM, precursor, recycling or distribution-consistent inlet."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "inlet_source_gate={gate}; paper_grade_inlet_source_gate={paper}; method_class={method}; reasons={reasons}".format(
            gate=source_gate,
            paper=paper_gate,
            method=source_method_class,
            reasons=";".join(report["inlet_source_gate_reasons"]),
        )
    )
    return 0 if source_gate == "pass" and paper_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
