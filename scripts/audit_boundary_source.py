#!/usr/bin/env python3
"""Audit generated setup.cpp boundary-condition implementation evidence.

This script does not run CFD. It checks the generated FluidX3D setup.cpp so a
validation package cannot rely only on boundary metadata or evidence labels
while the source still uses a simplified TYPE_E box-boundary setup.
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
    parser = argparse.ArgumentParser(description="Audit generated FluidX3D setup.cpp boundary implementation evidence.")
    parser.add_argument("--setup", required=True, help="Generated setup.cpp path.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--out", required=True, help="Output boundary_source_audit.json.")
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


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def strip_cpp_string_literals(text: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)


def find_type_e_velocity_initialization(code: str) -> Dict[str, Any]:
    guard_match = re.search(
        r"if\s*\(\s*lbm\.flags\s*\[\s*n\s*\]\s*!=\s*TYPE_E\s*\)\s*return\s*;",
        code,
        flags=re.IGNORECASE,
    )
    if not guard_match:
        return {
            "guard": False,
            "coordinates": False,
            "velocity_write": False,
            "profile": False,
            "uniform": False,
        }

    window = code[guard_match.start() : guard_match.start() + 1200]
    has_coordinates = bool(re.search(r"lbm\.coordinates\s*\(\s*n\s*,\s*x\s*,\s*y\s*,\s*z\s*\)", window))
    has_profile = bool(re.search(r"float3\s+u_e\s*=\s*windProfile\s*\(\s*z\s*\)", window))
    has_uniform = all(
        re.search(rf"lbm\.u\.{axis}\s*\[\s*n\s*\]\s*=\s*u_{axis}\s*;", window)
        for axis in ["x", "y", "z"]
    )
    has_profile_write = all(
        re.search(rf"lbm\.u\.{axis}\s*\[\s*n\s*\]\s*=\s*u_e\.{axis}\s*;", window)
        for axis in ["x", "y", "z"]
    )
    return {
        "guard": True,
        "coordinates": has_coordinates,
        "velocity_write": has_profile_write or has_uniform,
        "profile": has_profile and has_profile_write,
        "uniform": has_uniform,
    }


def strip_cpp_comments(text: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", without_block)


def extract_cpp_comments(text: str) -> str:
    comments = re.findall(r"/\*.*?\*/|//.*", text, flags=re.DOTALL)
    return "\n".join(comments)


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

    code = strip_cpp_comments(source)
    comments = extract_cpp_comments(source)
    implementation_code = strip_cpp_string_literals(code)
    lower = implementation_code.lower()
    boundary_summary = str(metadata.get("BoundaryConditionSummary") or "")
    boundary_types = nested(metadata, "BoundaryProtocolAudit", "BoundaryTypes")
    boundary_types_text = json.dumps(boundary_types, ensure_ascii=True) if isinstance(boundary_types, dict) else ""
    metadata_boundary_text = " ".join([boundary_summary, boundary_types_text]).lower()

    has_equilibrium_boundaries = "equilibrium_boundaries" in lower
    has_type_e_define = "#define type_e" in lower or "type_e 0x02" in lower
    has_type_s_define = "#define type_s" in lower or "type_s 0x01" in lower
    has_type_e_symbol = "type_e" in lower
    has_type_s_symbol = "type_s" in lower
    type_e_assignment_count = count_regex(implementation_code, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E")
    type_s_assignment_count = count_regex(implementation_code, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_S")
    has_ground_no_slip = "if(z == 0u)" in implementation_code and "TYPE_S" in implementation_code
    has_building_voxel_solid = "voxelize_stl" in lower and "type_s" in lower
    type_e_velocity_initialization = find_type_e_velocity_initialization(implementation_code)
    has_type_e_velocity_initialization = (
        type_e_velocity_initialization["guard"]
        and type_e_velocity_initialization["coordinates"]
        and type_e_velocity_initialization["velocity_write"]
    )
    has_profile_type_e_velocity_initialization = (
        has_type_e_velocity_initialization and type_e_velocity_initialization["profile"]
    )
    has_profile_inlet = contains_any(implementation_code, ["windProfile(z)", "profile_u_lbm", "profile_z_m"])
    has_outlet_type_e = bool(
        re.search(
            r"if\s*\([^)]*(Nx-1u|0u|Ny-1u)[^)]*\)\s*\{\s*lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E;\s*return;",
            implementation_code,
        )
    )
    has_lateral_type_e = contains_any(
        implementation_code,
        [
            "if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }",
            "if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }",
        ],
    )
    has_top_type_e = "if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }" in implementation_code
    has_non_reflecting_outlet_token = contains_any(
        code,
        [
            "non_reflecting",
            "non-reflecting",
            "convective_outlet",
            "convective outlet",
            "absorbing outlet",
            "sponge layer",
            "sponge_layer",
            "radiation boundary",
            "pressure outlet validated",
        ],
    )
    has_periodic_side_top_token = contains_any(code, ["periodic boundary", "periodic_x", "periodic_y", "periodic_z"])
    has_rough_wall_function_token = contains_any(
        code,
        [
            "rough_wall",
            "rough-wall",
            "wall_function",
            "log-law",
            "log_law",
            "aerodynamic roughness boundary",
        ],
    )
    has_precursor_or_recycling_token = contains_any(code, ["precursor", "recycling_rescaling", "recycling-rescaling"])
    has_non_reflecting_outlet_method = (
        has_regex(
            implementation_code,
            r"\b\w*(non_reflecting|nonReflecting|convective_outlet|convectiveOutlet|absorbing_outlet|absorbingOutlet|radiation_boundary|radiationBoundary)\w*\s*\(",
        )
        or has_regex(implementation_code, r"\b(sponge_layer|spongeLayer)\w*\s*(\[|=|\{|\()")
    )
    has_non_reflecting_outlet_state_evidence = contains_any(
        implementation_code,
        [
            "sponge_strength",
            "sponge_sigma",
            "sponge_start",
            "sponge_length",
            "outlet_sponge",
            "absorbing_zone",
            "damping_zone",
            "convective_speed",
            "outlet_buffer",
            "outlet_previous",
            "pressure_outlet",
            "rho_outlet",
            "radiation_coefficient",
            "characteristic_outlet",
        ],
    ) or has_regex(
        implementation_code,
        r"\b(sponge|absorbing|damping|radiation|convective)\w*\s*(\[|=|\{)",
    )
    has_non_reflecting_outlet = (
        has_non_reflecting_outlet_method and has_non_reflecting_outlet_state_evidence
    )
    has_periodic_side_top_method = has_regex(
        implementation_code,
        r"\b(periodic_[xyz]|periodicX|periodicY|periodicZ|set_periodic|setPeriodic|periodic_boundary|periodicBoundary)\w*\s*(\[|=|\{|\()",
    )
    has_periodic_pair_mapping_evidence = contains_any(
        implementation_code,
        [
            "periodic_pair",
            "periodicPair",
            "wrap_index",
            "wrapIndex",
            "wrapped_neighbor",
            "wrappedNeighbor",
            "opposite_face",
            "oppositeFace",
            "periodic_neighbor",
            "periodicNeighbor",
        ],
    ) or has_regex(
        implementation_code,
        r"%\s*N[xyz]\b|\(\s*\w+\s*\+\s*N[xyz]\s*[-+]",
    )
    has_periodic_side_top = has_periodic_side_top_method and has_periodic_pair_mapping_evidence
    has_rough_wall_function_method = has_regex(
        implementation_code,
        r"\b\w*(rough_wall|roughWall|wall_function|wallFunction|log_law|logLaw)\w*\s*(\[|=|\{|\()",
    )
    has_rough_wall_parameter_evidence = contains_any(
        implementation_code,
        [
            "roughness_height",
            "roughnessHeight",
            "roughness_length",
            "roughnessLength",
            "aerodynamic_roughness",
            "sand_grain",
            "ks_lbm",
            "ksLbm",
            "wall_shear",
            "wallShear",
            "friction_velocity",
            "frictionVelocity",
            "u_star",
            "uStar",
        ],
    )
    has_rough_wall_action_evidence = contains_any(
        implementation_code,
        [
            "rough_wall_drag",
            "roughWallDrag",
            "roughness_drag",
            "roughnessDrag",
            "wall_function_shear",
            "wallFunctionShear",
            "equivalent_rough_wall_drag",
            "equivalentRoughWallDrag",
            "wall_shear_force",
            "wallShearForce",
            "applyRoughWall",
            "apply_rough_wall",
        ],
    ) or has_regex(
        implementation_code,
        r"\blbm\.(force|F)\.[xyz]\s*\[\s*n\s*\]\s*[+\-]?=",
    )
    has_rough_wall_function = (
        has_rough_wall_function_method
        and has_rough_wall_parameter_evidence
        and has_rough_wall_action_evidence
    )
    has_precursor_or_recycling_method = has_regex(
        implementation_code,
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|recycleRescale)\w*\s*\(",
    )
    has_precursor_or_recycling_field_evidence = contains_any(
        implementation_code,
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
            "precursor_snapshot",
            "precursorSnapshot",
            "precursor_vtk",
            "precursorVtk",
        ],
    )
    has_precursor_or_recycling = (
        has_precursor_or_recycling_method and has_precursor_or_recycling_field_evidence
    )
    advanced_boundary_token_only = (
        (has_non_reflecting_outlet_token and not has_non_reflecting_outlet)
        or (has_periodic_side_top_token and not has_periodic_side_top)
        or (has_rough_wall_function_token and not has_rough_wall_function)
        or (has_precursor_or_recycling_token and not has_precursor_or_recycling)
    )
    has_boundary_source_comment = contains_any(comments, ["BoundaryProtocolAudit", "TYPE_E", "TYPE_S"])
    comments_contain_boundary_tokens = contains_any(
        comments,
        ["type_e", "type_s", "non_reflecting", "rough_wall", "precursor", "recycling_rescaling"],
    )

    simplified_type_e_box = (
        has_equilibrium_boundaries
        and type_e_assignment_count >= 3
        and has_outlet_type_e
        and (has_lateral_type_e or has_top_type_e)
        and not has_non_reflecting_outlet
        and not has_periodic_side_top
        and not has_precursor_or_recycling
    )
    no_slip_solid_only = has_ground_no_slip and has_building_voxel_solid and not has_rough_wall_function

    if has_precursor_or_recycling:
        source_class = "precursor_or_recycling_boundary"
    elif has_non_reflecting_outlet and (has_periodic_side_top or has_rough_wall_function):
        source_class = "advanced_boundary_source_evidence"
    elif (
        has_non_reflecting_outlet_method
        or has_periodic_side_top_method
        or has_rough_wall_function_method
        or has_precursor_or_recycling_method
    ):
        source_class = "named_boundary_method_without_field_evidence"
    elif simplified_type_e_box:
        source_class = "simplified_type_e_box"
    elif type_e_assignment_count > 0:
        source_class = "partial_type_e_boundary_source"
    elif type_s_assignment_count > 0:
        source_class = "solid_only_boundary_source"
    else:
        source_class = "none"

    source_boundary_coherent = (
        has_equilibrium_boundaries
        and has_type_e_symbol
        and has_type_s_symbol
        and type_e_assignment_count > 0
        and has_ground_no_slip
        and has_building_voxel_solid
    )
    source_wind_tunnel_equivalent = source_class in {
        "precursor_or_recycling_boundary",
        "advanced_boundary_source_evidence",
    }
    source_advanced_code_evidence = (
        (source_class == "precursor_or_recycling_boundary" and has_precursor_or_recycling)
        or (
            source_class == "advanced_boundary_source_evidence"
            and has_non_reflecting_outlet
            and (has_periodic_side_top or has_rough_wall_function)
        )
    )
    source_simplified = source_class in {
        "simplified_type_e_box",
        "partial_type_e_boundary_source",
        "solid_only_boundary_source",
        "none",
    }

    metadata_claims_advanced = any(
        token in metadata_boundary_text
        for token in [
            "non_reflecting",
            "non-reflecting",
            "validated_boundary_model",
            "wind_tunnel_protocol_matched",
            "rough_wall",
            "rough-wall",
            "precursor_boundary",
            "recycling_boundary",
        ]
    )

    if not source_boundary_coherent:
        reasons.append("boundary_source_missing_coherent_type_e_type_s_setup")
    if type_e_assignment_count > 0 and source_class in {"simplified_type_e_box", "partial_type_e_boundary_source"}:
        if not has_type_e_velocity_initialization:
            reasons.append("type_e_boundary_velocity_initialization_missing_or_incomplete")
        if has_profile_inlet and not has_profile_type_e_velocity_initialization:
            reasons.append("profile_type_e_boundary_velocity_initialization_missing")
    if metadata_claims_advanced and not source_wind_tunnel_equivalent:
        reasons.append("metadata_claims_advanced_boundary_without_source_evidence")
    if advanced_boundary_token_only:
        reasons.append("advanced_boundary_tokens_without_code_evidence")
    if has_non_reflecting_outlet_method and not has_non_reflecting_outlet_state_evidence:
        reasons.append("non_reflecting_boundary_source_missing_state_evidence")
    if has_periodic_side_top_method and not has_periodic_pair_mapping_evidence:
        reasons.append("periodic_boundary_source_missing_pair_mapping_evidence")
    if has_rough_wall_function_method and not has_rough_wall_parameter_evidence:
        reasons.append("rough_wall_boundary_source_missing_roughness_parameter_evidence")
    if has_rough_wall_function_method and not has_rough_wall_action_evidence:
        reasons.append("rough_wall_boundary_source_missing_wall_action_evidence")
    if has_precursor_or_recycling_method and not has_precursor_or_recycling_field_evidence:
        reasons.append("precursor_recycling_boundary_source_missing_recycled_field_evidence")

    source_gate = "pass" if not reasons else "fail"
    paper_reasons: List[str] = []
    if not source_wind_tunnel_equivalent:
        paper_reasons.append("boundary_source_not_wind_tunnel_equivalent")
    if source_simplified:
        paper_reasons.append("boundary_source_simplified_type_e_or_solid_only")
    if no_slip_solid_only:
        paper_reasons.append("ground_and_buildings_no_slip_without_rough_wall_or_precursor")
    if source_class == "named_boundary_method_without_field_evidence":
        paper_reasons.append("boundary_method_named_without_concrete_state_or_field_evidence")
    paper_gate = "pass" if not paper_reasons else "fail"

    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_source_audit.v1",
        "generated_at_utc": utc_now(),
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": setup_hash,
        "metadata": str(metadata_path) if metadata_path else "",
        "metadata_boundary_summary": boundary_summary,
        "metadata_boundary_types": boundary_types if isinstance(boundary_types, dict) else {},
        "metadata_claims_advanced_boundary": metadata_claims_advanced,
        "has_equilibrium_boundaries_define": has_equilibrium_boundaries,
        "has_type_e_define": has_type_e_define,
        "has_type_s_define": has_type_s_define,
        "has_type_e_symbol": has_type_e_symbol,
        "has_type_s_symbol": has_type_s_symbol,
        "type_e_assignment_count": type_e_assignment_count,
        "type_s_assignment_count": type_s_assignment_count,
        "has_profile_inlet": has_profile_inlet,
        "has_outlet_type_e": has_outlet_type_e,
        "has_lateral_type_e": has_lateral_type_e,
        "has_top_type_e": has_top_type_e,
        "has_type_e_velocity_initialization": has_type_e_velocity_initialization,
        "has_type_e_velocity_initialization_guard": type_e_velocity_initialization["guard"],
        "has_type_e_velocity_initialization_coordinates": type_e_velocity_initialization["coordinates"],
        "has_type_e_velocity_initialization_velocity_write": type_e_velocity_initialization["velocity_write"],
        "has_profile_type_e_velocity_initialization": has_profile_type_e_velocity_initialization,
        "has_uniform_type_e_velocity_initialization": (
            has_type_e_velocity_initialization and type_e_velocity_initialization["uniform"]
        ),
        "has_ground_no_slip": has_ground_no_slip,
        "has_building_voxel_solid": has_building_voxel_solid,
        "has_non_reflecting_outlet_evidence": has_non_reflecting_outlet,
        "has_non_reflecting_outlet_method": has_non_reflecting_outlet_method,
        "has_non_reflecting_outlet_state_evidence": has_non_reflecting_outlet_state_evidence,
        "has_non_reflecting_outlet_token": has_non_reflecting_outlet_token,
        "has_periodic_side_top_evidence": has_periodic_side_top,
        "has_periodic_side_top_method": has_periodic_side_top_method,
        "has_periodic_pair_mapping_evidence": has_periodic_pair_mapping_evidence,
        "has_periodic_side_top_token": has_periodic_side_top_token,
        "has_rough_wall_function_evidence": has_rough_wall_function,
        "has_rough_wall_function_method": has_rough_wall_function_method,
        "has_rough_wall_parameter_evidence": has_rough_wall_parameter_evidence,
        "has_rough_wall_action_evidence": has_rough_wall_action_evidence,
        "has_rough_wall_function_token": has_rough_wall_function_token,
        "has_precursor_or_recycling_boundary_evidence": has_precursor_or_recycling,
        "has_precursor_or_recycling_boundary_method": has_precursor_or_recycling_method,
        "has_precursor_or_recycling_boundary_field_evidence": has_precursor_or_recycling_field_evidence,
        "has_precursor_or_recycling_boundary_token": has_precursor_or_recycling_token,
        "advanced_boundary_token_only": advanced_boundary_token_only,
        "advanced_boundary_evidence_uses_comment_stripped_code": True,
        "all_boundary_implementation_evidence_uses_comment_stripped_code": True,
        "comments_contain_boundary_tokens": comments_contain_boundary_tokens,
        "boundary_source_advanced_code_evidence": source_advanced_code_evidence,
        "has_boundary_source_comment": has_boundary_source_comment,
        "boundary_source_method_class": source_class,
        "boundary_source_coherent": source_boundary_coherent,
        "boundary_source_simplified": source_simplified,
        "boundary_source_wind_tunnel_equivalent": source_wind_tunnel_equivalent,
        "boundary_source_gate": source_gate,
        "boundary_source_gate_reasons": reasons or ["boundary_source_consistent_with_declared_metadata"],
        "boundary_source_gate_reasons_csv": ";".join(reasons or ["boundary_source_consistent_with_declared_metadata"]),
        "paper_grade_boundary_source_gate": paper_gate,
        "paper_grade_boundary_source_gate_reasons": paper_reasons or ["boundary_source_wind_tunnel_equivalent"],
        "paper_grade_boundary_source_gate_reasons_csv": ";".join(paper_reasons or ["boundary_source_wind_tunnel_equivalent"]),
        "recommended_next_action": (
            "For paper-grade AIJ validation, replace or justify the simplified TYPE_E outlet/lateral/top setup "
            "with archived wind-tunnel-equivalent boundary evidence, non-reflecting/precursor/recycling boundaries, "
            "and a rough-wall or documented floor-roughness treatment."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "boundary_source_gate="
        f"{source_gate}; paper_grade_boundary_source_gate={paper_gate}; "
        f"method_class={source_class}; reasons={';'.join(report['boundary_source_gate_reasons'])}"
    )
    return 0 if source_gate == "pass" and paper_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
