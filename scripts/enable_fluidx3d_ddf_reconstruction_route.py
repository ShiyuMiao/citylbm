#!/usr/bin/env python3
"""Enable the fastest safe FluidX3D DDF reconstruction route for a case.

This script edits the generated case ``defines.hpp`` and, when present,
``setup.cpp`` after checking that the selected FluidX3D source exposes the
required reconstruction hooks. It avoids another Grasshopper/Rhino generation
round when the case is already source-complete but the relevant macro or
runtime reconstruction call is still missing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_fluidx3d_equilibrium_boundary import (  # noqa: E402
    classify_gate,
    enabled_macros,
    has_regex,
    read_text,
)


REQUIRED_SOURCE_EVIDENCE = [
    "has_reconstruct_equilibrium_kernel",
    "has_reconstruct_feq_from_rho_u",
    "has_reconstruct_store_f",
    "has_lbm_kernel_binding",
    "has_lbm_public_call",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enable a case-level FluidX3D DDF reconstruction macro.")
    parser.add_argument("--case-dir", default="", help="Case directory containing src/defines.hpp or defines.hpp.")
    parser.add_argument("--defines", default="", help="Explicit generated defines.hpp path.")
    parser.add_argument("--setup", default="", help="Explicit generated setup.cpp path.")
    parser.add_argument("--fluidx3d-source", required=True, help="FluidX3D source root containing src/*.cpp/*.hpp.")
    parser.add_argument("--out", required=True, help="Output JSON manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Audit and report the intended change without editing.")
    parser.add_argument(
        "--skip-setup-patch",
        action="store_true",
        help="Only enable the macro; do not patch generated setup.cpp reconstruction calls.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def resolve_defines(args: argparse.Namespace) -> Path:
    if args.defines:
        return Path(args.defines).expanduser().resolve()
    if not args.case_dir:
        raise SystemExit("--case-dir or --defines is required")
    case_dir = Path(args.case_dir).expanduser().resolve()
    for candidate in [case_dir / "src" / "defines.hpp", case_dir / "defines.hpp"]:
        if candidate.is_file():
            return candidate
    return case_dir / "src" / "defines.hpp"


def resolve_setup(args: argparse.Namespace) -> Path | None:
    if args.setup:
        return Path(args.setup).expanduser().resolve()
    if not args.case_dir:
        return None
    case_dir = Path(args.case_dir).expanduser().resolve()
    for candidate in [case_dir / "src" / "setup.cpp", case_dir / "setup.cpp"]:
        if candidate.is_file():
            return candidate
    return None


def source_evidence(source_root: Path) -> Dict[str, bool]:
    defines_text = read_text(source_root / "src" / "defines.hpp")
    kernel_text = read_text(source_root / "src" / "kernel.cpp")
    lbm_cpp_text = read_text(source_root / "src" / "lbm.cpp")
    lbm_hpp_text = read_text(source_root / "src" / "lbm.hpp")
    combined = "\n".join([defines_text, kernel_text, lbm_cpp_text, lbm_hpp_text])
    return {
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
        "has_lbm_public_call": has_regex(
            lbm_cpp_text + "\n" + lbm_hpp_text,
            r"LBM::reconstruct_equilibrium_boundaries|void\s+reconstruct_equilibrium_boundaries\s*\(",
        ),
        "has_reconstruct_inlet_stress_kernel": "kernel void reconstruct_inlet_stress_boundaries" in kernel_text,
        "has_lbm_inlet_stress_public_call": has_regex(
            lbm_cpp_text + "\n" + lbm_hpp_text,
            r"LBM::reconstruct_inlet_stress_boundaries|void\s+reconstruct_inlet_stress_boundaries\s*\(",
        ),
        "has_casea_sem_stress_route": "CASEA_DEVICE_SEM_STRESS_DDF" in kernel_text,
    }


def uncomment_or_insert_define(text: str, macro: str, insert_after: str) -> Tuple[str, bool]:
    active = re.compile(rf"^\s*#\s*define\s+{re.escape(macro)}\b", re.MULTILINE)
    if active.search(text):
        return text, False
    commented = re.compile(rf"^(\s*)//\s*#\s*define\s+{re.escape(macro)}\b(.*)$", re.MULTILINE)
    if commented.search(text):
        return commented.sub(rf"\1#define {macro}\2", text, count=1), True
    anchor = re.compile(rf"^(\s*#\s*define\s+{re.escape(insert_after)}\b.*)$", re.MULTILINE)
    if anchor.search(text):
        return anchor.sub(rf"\1\n#define {macro}", text, count=1), True
    return text + f"\n#define {macro}\n", True


def comment_out_define(text: str, macro: str) -> Tuple[str, bool]:
    active = re.compile(rf"^(\s*)#\s*define\s+{re.escape(macro)}\b(.*)$", re.MULTILINE)
    if not active.search(text):
        return text, False
    return active.sub(rf"\1// #define {macro}\2", text), True


def choose_macro(defines_text: str, evidence: Dict[str, bool]) -> str:
    macros = enabled_macros(defines_text)
    stress_route_ready = (
        macros.get("CASEA_DEVICE_SEM_INLET")
        and evidence.get("has_casea_sem_stress_route")
        and evidence.get("has_reconstruct_inlet_stress_kernel")
        and evidence.get("has_lbm_inlet_stress_public_call")
    )
    if stress_route_ready:
        return "CASEA_DEVICE_SEM_STRESS_DDF"
    return "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"


def incompatible_macros(selected_macro: str) -> List[str]:
    if selected_macro == "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF":
        return ["RECONSTRUCT_INLET_STRESS_DDF", "CASEA_DEVICE_SEM_STRESS_DDF"]
    if selected_macro == "CASEA_DEVICE_SEM_STRESS_DDF":
        return ["RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"]
    return []


def has_reconstruction_call_nearby(lines: List[str], index: int) -> bool:
    window = "\n".join(lines[index + 1 : index + 9])
    return bool(
        re.search(
            r"\blbm\s*\.\s*reconstruct_(?:inlet_stress|equilibrium)_boundaries\s*\(",
            window,
        )
    )


def patch_setup_reconstruction_calls(text: str) -> Tuple[str, int]:
    if "lbm.u.write_to_device();" not in text:
        return text, 0

    lines = text.splitlines(keepends=True)
    patched: List[str] = []
    insertions = 0
    for index, line in enumerate(lines):
        patched.append(line)
        if "lbm.u.write_to_device();" not in line:
            continue
        if has_reconstruction_call_nearby(lines, index):
            continue
        indent_match = re.match(r"^(\s*)", line)
        indent = indent_match.group(1) if indent_match else ""
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        patched.extend(
            [
                f"{indent}#if defined(RECONSTRUCT_INLET_STRESS_DDF){newline}",
                f"{indent}    lbm.reconstruct_inlet_stress_boundaries();{newline}",
                f"{indent}#elif defined(RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF){newline}",
                f"{indent}    lbm.reconstruct_equilibrium_boundaries();{newline}",
                f"{indent}#endif{newline}",
            ]
        )
        insertions += 1
    return "".join(patched), insertions


def main() -> int:
    args = parse_args()
    defines_path = resolve_defines(args)
    setup_path = resolve_setup(args)
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    defines_text = defines_path.read_text(encoding="utf-8-sig") if defines_path.is_file() else ""
    setup_text = setup_path.read_text(encoding="utf-8-sig") if setup_path and setup_path.is_file() else ""
    evidence = source_evidence(source_root)
    source_ready = all(evidence.get(key) for key in REQUIRED_SOURCE_EVIDENCE)
    before_macros = enabled_macros(defines_text)
    selected_macro = choose_macro(defines_text, evidence)
    updated_text, would_change = uncomment_or_insert_define(defines_text, selected_macro, "EQUILIBRIUM_BOUNDARIES")
    deactivated_macros: List[str] = []
    for macro in incompatible_macros(selected_macro):
        updated_text, deactivated = comment_out_define(updated_text, macro)
        if deactivated:
            deactivated_macros.append(macro)
            would_change = True
    updated_setup_text, setup_insertions = (
        (setup_text, 0) if args.skip_setup_patch else patch_setup_reconstruction_calls(setup_text)
    )
    setup_would_change = bool(setup_insertions)
    after_macros = enabled_macros(updated_text)
    classification = classify_gate(evidence, after_macros)

    reasons: List[str] = []
    if not defines_path.is_file():
        reasons.append("defines_hpp_missing")
    if not source_ready:
        reasons.append("fluidx3d_source_reconstruction_hook_not_proven")
    if classification.get("Gate") != "pass":
        reasons.extend(classification.get("Reasons", []))

    if not reasons and would_change and not args.dry_run:
        defines_path.write_text(updated_text, encoding="utf-8")
    if not reasons and setup_path and setup_would_change and not args.dry_run:
        setup_path.write_text(updated_setup_text, encoding="utf-8")

    output: Dict[str, Any] = {
        "Schema": "citylbm.enable_fluidx3d_ddf_reconstruction_route.v1",
        "GeneratedAtUtc": utc_now(),
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons,
        "DryRun": bool(args.dry_run),
        "DefinesPath": str(defines_path),
        "SetupPath": str(setup_path) if setup_path else "",
        "FluidX3DSource": str(source_root),
        "SelectedMacro": selected_macro,
        "Changed": bool((would_change or setup_would_change) and not args.dry_run and not reasons),
        "WouldChange": bool(would_change),
        "BeforeSha256": sha256_text(defines_text),
        "AfterSha256": sha256_text(updated_text),
        "SetupChanged": bool(setup_would_change and not args.dry_run and not reasons),
        "SetupWouldChange": setup_would_change,
        "SetupBeforeSha256": sha256_text(setup_text) if setup_text else "",
        "SetupAfterSha256": sha256_text(updated_setup_text) if updated_setup_text else "",
        "ReconstructionCallInsertions": setup_insertions,
        "BeforeMacros": before_macros,
        "AfterMacros": after_macros,
        "DeactivatedMacros": deactivated_macros,
        "SourceEvidence": evidence,
        "NextAction": (
            "Re-run the no-CFD preflight, then build/run only if the DDF route gate passes."
            if not reasons
            else "Do not edit the case automatically; fix missing source evidence or case defines first."
        ),
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"enable_fluidx3d_ddf_reconstruction_route_gate={output['Gate']}; changed={output['Changed']}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if output["Gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
