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
    audited_source_lower = audited_source.lower()
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

    has_custom_table = "profile_z_m" in audited_source_lower and "profile_u_lbm" in audited_source_lower
    has_k_profile = "profile_k_lbm" in audited_source_lower
    has_stg_function = "applysyntheticturbulentinlet" in audited_source_lower
    has_stg_refresh_loop = count_regex(audited_source, r"applySyntheticTurbulentInlet\s*\(") >= 2
    has_velocity_field_write = contains_any(audited_source, ["lbm.u.x", "lbm.u.y", "lbm.u.z"])
    has_distribution_write = contains_any(
        audited_source,
        [
            "lbm.f[",
            "lbm.f0",
            "lbm.feq",
            "calculate_f_eq",
            "device_sem_stress_ddf",
            "stress_ddf",
        ],
    )
    has_digital_filter = contains_any(audited_source, ["digital_filter", "digital-filter", "dfm", "filter kernel"])
    has_sem = contains_any(audited_source, ["synthetic_eddy_method", "sem_distribution", "synthetic eddy method"])
    has_precursor = contains_any(audited_source, ["precursor", "recycling_rescaling", "recycling-rescaling"])
    has_spectral_modes = contains_any(
        audited_source,
        [
            "citylbm_stg_mode_count",
            "citylbm_mode_wave",
            "citylbm_mode_amplitude",
        ],
    )
    has_taylor_advection = contains_any(audited_source, ["advected_x", "advected_y", "advected_z", "frozen-turbulence"])
    has_transverse_projection = contains_any(
        audited_source,
        [
            "ak*kx/kk",
            "ak * kx / kk",
            "projected normal to their wave vector",
            "divergence-reduced",
        ],
    )
    has_length_scale = contains_any(
        audited_source,
        [
            "correlation_length",
            "citylbm_stg_lx",
            "citylbm_stg_corr_cells",
            "length_scale",
            "correlation cells",
        ],
    )
    has_update_interval = "citylbm_stg_update_interval" in audited_source_lower
    refresh_current_time_calls = count_regex(
        audited_source,
        r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)",
    )
    has_stg_refresh_with_current_time = refresh_current_time_calls >= 1
    has_update_interval_run_control = has_regex(
        audited_source,
        r"steps_to_run\s*=\s*[^;\n]*citylbm_stg_update_interval",
    ) or has_regex(
        audited_source,
        r"steps_to_run\s*>\s*citylbm_stg_update_interval\s*\)\s*steps_to_run\s*=\s*citylbm_stg_update_interval",
    )
    has_segmented_stg_run_loop = (
        has_update_interval_run_control
        and has_regex(audited_source, r"lbm\.run\s*\(\s*steps_to_run\s*\)")
        and has_regex(
            audited_source,
            r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)\s*;\s*lbm\.run\s*\(\s*steps_to_run\s*\)",
        )
    )
    has_bounded_amplitude = contains_any(audited_source, ["citylbm_stg_max_fraction", "max_fraction", "amplitude cap"])

    source_method_class = "none"
    if has_precursor:
        source_method_class = "precursor_or_recycling"
    elif has_digital_filter and has_distribution_write:
        source_method_class = "digital_filter_distribution_consistent"
    elif has_sem and has_distribution_write:
        source_method_class = "synthetic_eddy_distribution_consistent"
    elif has_stg_function and has_velocity_field_write and (has_spectral_modes or has_taylor_advection or has_transverse_projection):
        source_method_class = "stg_lite_correlated_velocity_field_only"
    elif has_stg_function and has_velocity_field_write:
        source_method_class = "stg_lite_velocity_field_only"
    elif has_digital_filter or has_sem:
        source_method_class = "named_method_without_distribution_evidence"
    elif has_velocity_field_write:
        source_method_class = "mean_profile_velocity_field_only"

    source_distribution_consistent = source_method_class in {
        "precursor_or_recycling",
        "digital_filter_distribution_consistent",
        "synthetic_eddy_distribution_consistent",
    }
    advanced_code_evidence = has_digital_filter or has_sem or has_precursor
    source_velocity_only = source_method_class in {
        "stg_lite_velocity_field_only",
        "stg_lite_correlated_velocity_field_only",
        "mean_profile_velocity_field_only",
        "named_method_without_distribution_evidence",
    }

    if synthetic_requested and not has_stg_function and not has_digital_filter and not has_sem and not has_precursor:
        reasons.append("metadata_requests_turbulent_inlet_but_source_has_no_inlet_method")
    if synthetic_requested and has_stg_function and not has_k_profile:
        reasons.append("synthetic_inlet_source_missing_profile_k_lbm")
    if synthetic_requested and has_stg_function and not has_stg_refresh_loop:
        reasons.append("synthetic_inlet_not_refreshed_in_run_loop")
    if synthetic_requested and has_stg_function and not has_stg_refresh_with_current_time:
        reasons.append("synthetic_inlet_missing_refresh_with_current_solver_time")
    if synthetic_requested and has_stg_function and not has_length_scale:
        reasons.append("synthetic_inlet_missing_length_scale_source")
    if synthetic_requested and has_stg_function and not has_spectral_modes:
        reasons.append("synthetic_inlet_missing_spectral_modes")
    if synthetic_requested and has_stg_function and not has_taylor_advection:
        reasons.append("synthetic_inlet_missing_temporal_advection")
    if synthetic_requested and has_stg_function and not has_transverse_projection:
        reasons.append("synthetic_inlet_missing_transverse_projection")
    if synthetic_requested and has_stg_function and not has_update_interval:
        reasons.append("synthetic_inlet_missing_update_interval")
    if synthetic_requested and has_stg_function and has_update_interval and not has_update_interval_run_control:
        reasons.append("synthetic_inlet_update_interval_not_used_in_run_loop")
    if synthetic_requested and has_stg_function and not has_segmented_stg_run_loop:
        reasons.append("synthetic_inlet_refresh_not_coupled_to_segmented_lbm_run")
    if synthetic_requested and has_stg_function and not has_bounded_amplitude:
        reasons.append("synthetic_inlet_missing_amplitude_cap")

    metadata_claims_distribution = any(
        token in " ".join([metadata_treatment, metadata_class]).lower()
        for token in ["distribution_consistent", "digital_filter", "digital-filter", "sem", "dfm", "precursor", "recycling"]
    )
    if metadata_claims_distribution and not source_distribution_consistent:
        reasons.append("metadata_claims_distribution_consistency_without_source_evidence")

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
        "has_synthetic_inlet_function": has_stg_function,
        "has_synthetic_inlet_refresh_loop": has_stg_refresh_loop,
        "has_velocity_field_write": has_velocity_field_write,
        "has_distribution_function_write": has_distribution_write,
        "inlet_source_advanced_code_evidence": advanced_code_evidence,
        "has_digital_filter_evidence": has_digital_filter,
        "has_sem_evidence": has_sem,
        "has_precursor_or_recycling_evidence": has_precursor,
        "has_spectral_mode_evidence": has_spectral_modes,
        "has_taylor_advection_evidence": has_taylor_advection,
        "has_transverse_projection_evidence": has_transverse_projection,
        "has_length_scale_evidence": has_length_scale,
        "has_update_interval": has_update_interval,
        "stg_refresh_current_time_call_count": refresh_current_time_calls,
        "has_synthetic_inlet_refresh_with_current_time": has_stg_refresh_with_current_time,
        "has_update_interval_run_control": has_update_interval_run_control,
        "has_segmented_stg_run_loop": has_segmented_stg_run_loop,
        "has_bounded_amplitude": has_bounded_amplitude,
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
