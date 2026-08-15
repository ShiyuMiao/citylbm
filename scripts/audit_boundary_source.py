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

    lower = source.lower()
    boundary_summary = str(metadata.get("BoundaryConditionSummary") or "")
    boundary_types = nested(metadata, "BoundaryProtocolAudit", "BoundaryTypes")
    boundary_types_text = json.dumps(boundary_types, ensure_ascii=True) if isinstance(boundary_types, dict) else ""
    metadata_boundary_text = " ".join([boundary_summary, boundary_types_text]).lower()

    has_equilibrium_boundaries = "equilibrium_boundaries" in lower
    has_type_e_define = "#define type_e" in lower or "type_e 0x02" in lower
    has_type_s_define = "#define type_s" in lower or "type_s 0x01" in lower
    has_type_e_symbol = "type_e" in lower
    has_type_s_symbol = "type_s" in lower
    type_e_assignment_count = count_regex(source, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E")
    type_s_assignment_count = count_regex(source, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_S")
    has_ground_no_slip = "if(z == 0u)" in source and "TYPE_S" in source
    has_building_voxel_solid = "voxelize_stl" in lower and "type_s" in lower
    has_type_e_velocity_initialization = contains_any(
        source,
        [
            "initialize all TYPE_E boundary velocities",
            "lbm.flags[n] != TYPE_E",
            "float3 u_e = windProfile(z)",
        ],
    )
    has_profile_inlet = contains_any(source, ["windProfile(z)", "profile_u_lbm", "profile_z_m"])
    has_outlet_type_e = bool(
        re.search(r"if\s*\([^)]*(Nx-1u|0u|Ny-1u)[^)]*\)\s*\{\s*lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E;\s*return;", source)
    )
    has_lateral_type_e = contains_any(
        source,
        [
            "if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }",
            "if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }",
        ],
    )
    has_top_type_e = "if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }" in source
    has_non_reflecting_outlet = contains_any(
        source,
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
    has_periodic_side_top = contains_any(source, ["periodic boundary", "periodic_x", "periodic_y", "periodic_z"])
    has_rough_wall_function = contains_any(
        source,
        [
            "rough_wall",
            "rough-wall",
            "wall_function",
            "log-law",
            "log_law",
            "aerodynamic roughness boundary",
        ],
    )
    has_precursor_or_recycling = contains_any(source, ["precursor", "recycling_rescaling", "recycling-rescaling"])
    has_boundary_source_comment = contains_any(source, ["BoundaryProtocolAudit", "TYPE_E", "TYPE_S"])

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
    if metadata_claims_advanced and not source_wind_tunnel_equivalent:
        reasons.append("metadata_claims_advanced_boundary_without_source_evidence")

    source_gate = "pass" if not reasons else "fail"
    paper_reasons: List[str] = []
    if not source_wind_tunnel_equivalent:
        paper_reasons.append("boundary_source_not_wind_tunnel_equivalent")
    if source_simplified:
        paper_reasons.append("boundary_source_simplified_type_e_or_solid_only")
    if no_slip_solid_only:
        paper_reasons.append("ground_and_buildings_no_slip_without_rough_wall_or_precursor")
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
        "has_ground_no_slip": has_ground_no_slip,
        "has_building_voxel_solid": has_building_voxel_solid,
        "has_non_reflecting_outlet_evidence": has_non_reflecting_outlet,
        "has_periodic_side_top_evidence": has_periodic_side_top,
        "has_rough_wall_function_evidence": has_rough_wall_function,
        "has_precursor_or_recycling_boundary_evidence": has_precursor_or_recycling,
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
