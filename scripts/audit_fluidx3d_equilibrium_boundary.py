#!/usr/bin/env python3
"""Audit native FluidX3D TYPE_E equilibrium-boundary source evidence.

This is a fast no-CFD audit. It proves what the selected local FluidX3D source
can do before a long validation run is launched, so the optimization loop does
not waste hours on cases whose native boundary route is not traceable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


SOURCE_FILES = ["src/defines.hpp", "src/kernel.cpp", "src/lbm.cpp", "src/lbm.hpp"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit FluidX3D TYPE_E equilibrium-boundary DDF evidence.")
    parser.add_argument("--fluidx3d-source", required=True, help="FluidX3D source root containing src/*.cpp/*.hpp.")
    parser.add_argument("--out", required=True, help="Output fluidx3d_equilibrium_boundary_audit.json.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace") if path.is_file() else ""


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL))


def collect_records(source_root: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for rel in SOURCE_FILES:
        path = source_root / rel
        record: Dict[str, Any] = {
            "Role": f"FluidX3D {rel}",
            "Path": str(path),
            "Exists": path.is_file(),
            "Sha256": sha256(path) if path.is_file() else "",
            "Bytes": path.stat().st_size if path.is_file() else 0,
        }
        records.append(record)
    return records


def missing_reasons(evidence: Dict[str, bool]) -> List[str]:
    labels = {
        "has_type_e_define": "type_e_define_missing",
        "has_equilibrium_boundaries_macro": "equilibrium_boundaries_macro_missing",
        "has_reconstruct_equilibrium_kernel": "reconstruct_equilibrium_kernel_missing",
        "has_reconstruct_type_e_guard": "reconstruct_type_e_guard_missing",
        "has_reconstruct_feq_from_rho_u": "reconstruct_feq_from_rho_u_missing",
        "has_reconstruct_store_f": "reconstruct_store_f_missing",
        "has_stream_collide_type_e_macro_velocity": "stream_collide_type_e_macro_velocity_missing",
        "has_stream_collide_type_e_feq_collision": "stream_collide_type_e_feq_collision_missing",
        "has_lbm_kernel_binding": "lbm_kernel_binding_missing",
        "has_lbm_public_call": "lbm_public_call_missing",
    }
    return [reason for key, reason in labels.items() if not evidence.get(key)]


def enabled_macros(defines_text: str) -> Dict[str, bool]:
    return {
        "EQUILIBRIUM_BOUNDARIES": has_regex(defines_text, r"^\s*#\s*define\s+EQUILIBRIUM_BOUNDARIES\b"),
        "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF": has_regex(
            defines_text,
            r"^\s*#\s*define\s+RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\b",
        ),
        "RECONSTRUCT_INLET_STRESS_DDF": has_regex(defines_text, r"^\s*#\s*define\s+RECONSTRUCT_INLET_STRESS_DDF\b"),
        "CASEA_DEVICE_SEM_INLET": has_regex(defines_text, r"^\s*#\s*define\s+CASEA_DEVICE_SEM_INLET\b"),
        "CASEA_DEVICE_SEM_STRESS_DDF": has_regex(defines_text, r"^\s*#\s*define\s+CASEA_DEVICE_SEM_STRESS_DDF\b"),
    }


def classify_gate(evidence: Dict[str, bool], macros: Dict[str, bool]) -> Dict[str, Any]:
    required_source = [
        "has_type_e_define",
        "has_equilibrium_boundaries_macro",
        "has_reconstruct_equilibrium_kernel",
        "has_reconstruct_type_e_guard",
        "has_reconstruct_feq_from_rho_u",
        "has_reconstruct_store_f",
        "has_stream_collide_type_e_macro_velocity",
        "has_stream_collide_type_e_feq_collision",
        "has_lbm_kernel_binding",
        "has_lbm_public_call",
    ]
    source_pass = all(evidence.get(key) for key in required_source)
    route_enabled = bool(macros.get("EQUILIBRIUM_BOUNDARIES"))
    explicit_reconstruct_enabled = bool(
        macros.get("RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF")
        or macros.get("RECONSTRUCT_INLET_STRESS_DDF")
        or macros.get("CASEA_DEVICE_SEM_STRESS_DDF")
    )

    reasons: List[str] = []
    if not source_pass:
        reasons.extend(missing_reasons(evidence))
    if source_pass and not route_enabled:
        reasons.append("equilibrium_boundaries_not_enabled_in_defines")
    if source_pass and route_enabled and not explicit_reconstruct_enabled:
        reasons.append("type_e_equilibrium_collision_available_but_no_explicit_boundary_ddf_reconstruct_macro_enabled")

    if source_pass and route_enabled and explicit_reconstruct_enabled:
        return {
            "Gate": "pass",
            "Reasons": [],
            "BoundaryRouteClass": "fluidx3d_type_e_equilibrium_or_inlet_stress_ddf_route_enabled",
            "DistributionConsistencyEvidence": "source_proves_TYPE_E_uses_rho_u_to_build_feq_and_store_DDFs",
        }
    if source_pass:
        return {
            "Gate": "diagnostic_only",
            "Reasons": reasons,
            "BoundaryRouteClass": "fluidx3d_type_e_equilibrium_source_available_but_not_fully_enabled",
            "DistributionConsistencyEvidence": "source_available_but_current_defines_do_not_enable_full_reconstruct_route",
        }
    return {
        "Gate": "fail",
        "Reasons": reasons,
        "BoundaryRouteClass": "type_e_distribution_route_not_proven",
        "DistributionConsistencyEvidence": "missing_or_ambiguous_source_evidence",
    }


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def main() -> int:
    args = parse_args()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    defines_text = read_text(source_root / "src" / "defines.hpp")
    kernel_text = read_text(source_root / "src" / "kernel.cpp")
    lbm_cpp_text = read_text(source_root / "src" / "lbm.cpp")
    lbm_hpp_text = read_text(source_root / "src" / "lbm.hpp")
    combined = "\n".join([defines_text, kernel_text, lbm_cpp_text, lbm_hpp_text])
    macros = enabled_macros(defines_text)

    evidence = {
        "has_type_e_define": has_regex(defines_text, r"^\s*#\s*define\s+TYPE_E\b"),
        "has_equilibrium_boundaries_macro": "EQUILIBRIUM_BOUNDARIES" in combined,
        "has_reconstruct_equilibrium_kernel": "kernel void reconstruct_equilibrium_boundaries" in kernel_text,
        "has_reconstruct_type_e_guard": has_regex(kernel_text, r"flags\s*\[\s*n\s*\]\s*&\s*TYPE_BO\s*\)\s*!=\s*TYPE_E"),
        "has_reconstruct_feq_from_rho_u": has_regex(
            kernel_text,
            r"calculate_f_eq\s*\(\s*rho\s*\[\s*n\s*\]\s*,\s*u\s*\[\s*n\s*\]\s*,\s*u\s*\[\s*def_N\s*\+\s*\(ulong\)\s*n\s*\]\s*,\s*u\s*\[\s*2ul\s*\*\s*def_N\s*\+\s*\(ulong\)\s*n\s*\]",
        ),
        "has_reconstruct_store_f": has_regex(kernel_text, r"store_f\s*\(\s*n\s*,\s*feq\s*,\s*fi\s*,\s*j\s*,\s*t\s*\)"),
        "has_stream_collide_type_e_macro_velocity": has_regex(
            kernel_text,
            r"if\s*\(\s*flagsn_bo\s*==\s*TYPE_E\s*\)\s*\{.{0,500}?rhon\s*=\s*rho\s*\[.{0,200}?uxn\s*=\s*u\s*\[",
        ),
        "has_stream_collide_type_e_feq_collision": has_regex(kernel_text, r"flagsn_bo\s*==\s*TYPE_E\s*\?\s*feq\s*\[\s*i\s*\]"),
        "has_lbm_kernel_binding": has_regex(lbm_cpp_text, r"Kernel\s*\([^;]*reconstruct_equilibrium_boundaries"),
        "has_lbm_public_call": has_regex(lbm_cpp_text + "\n" + lbm_hpp_text, r"LBM::reconstruct_equilibrium_boundaries|void\s+reconstruct_equilibrium_boundaries\s*\("),
    }
    classification = classify_gate(evidence, macros)
    reasons = unique(classification["Reasons"])
    output = {
        "Schema": "citylbm.fluidx3d_equilibrium_boundary_audit.v1",
        "GeneratedAtUtc": utc_now(),
        "FluidX3DSource": str(source_root),
        "Gate": classification["Gate"],
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "BoundaryRouteClass": classification["BoundaryRouteClass"],
        "DistributionConsistencyEvidence": classification["DistributionConsistencyEvidence"],
        "EnabledMacros": macros,
        "Evidence": evidence,
        "Counts": {
            "type_e_occurrences": count_regex(combined, r"\bTYPE_E\b"),
            "equilibrium_boundaries_occurrences": count_regex(combined, r"\bEQUILIBRIUM_BOUNDARIES\b"),
            "calculate_f_eq_occurrences": count_regex(kernel_text, r"\bcalculate_f_eq\s*\("),
            "store_f_occurrences": count_regex(kernel_text, r"\bstore_f\s*\("),
        },
        "SourceFiles": collect_records(source_root),
        "NextAction": (
            "Native TYPE_E DDF route is source-traceable; keep this audit with the exact run hashes."
            if classification["Gate"] == "pass"
            else "Do not launch a paper-grade run until the native TYPE_E/DDF route is enabled and hash-traceable."
        ),
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"fluidx3d_equilibrium_boundary_gate={output['Gate']}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if output["Gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
