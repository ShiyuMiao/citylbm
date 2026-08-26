#!/usr/bin/env python3
"""Patch FluidX3D source with an explicit TYPE_E DDF reconstruction route.

This is a no-CFD development accelerator. It makes the native source route
auditable before a long validation run is launched, instead of discovering the
missing boundary distribution update after hours of simulation.
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

from audit_fluidx3d_equilibrium_boundary import classify_gate, enabled_macros, read_text  # noqa: E402
from enable_fluidx3d_ddf_reconstruction_route import source_evidence  # noqa: E402


KERNEL_BLOCK = r'''
)+"#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"+R(
)+R(kernel void reconstruct_equilibrium_boundaries(global fpxx* fi, const global float* rho, const global float* u, const global uchar* flags, const ulong t) { // rebuild TYPE_E boundary DDFs from prescribed rho/u
	const uxx n = get_global_id(0);
	if(n>=(uxx)def_N||is_halo(n)) return;
	if((flags[n]&TYPE_BO)!=TYPE_E) return;
	uxx j[def_velocity_set];
	neighbors(n, j);
	float feq[def_velocity_set];
	calculate_f_eq(rho[n], u[n], u[def_N+(ulong)n], u[2ul*def_N+(ulong)n], feq);
	store_f(n, feq, fi, j, t);
} // reconstruct_equilibrium_boundaries()
)+"#endif"+R( // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF
'''


DEVICE_DEFINE_BLOCK = '''
#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF
	"\\n	#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"
#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch FluidX3D native source for explicit TYPE_E DDF reconstruction.")
    parser.add_argument("--fluidx3d-source", required=True, help="FluidX3D source root containing src/kernel.cpp.")
    parser.add_argument("--out", required=True, help="Output patch manifest JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Report intended edits without writing files.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def file_record(path: Path, before: str, after: str, changed: bool) -> Dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.is_file(),
        "changed": changed,
        "before_sha256": sha256_text(before),
        "after_sha256": sha256_text(after),
    }


def replace_once(text: str, old: str, new: str) -> Tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def insert_kernel_block(text: str) -> Tuple[str, bool, str]:
    if "kernel void reconstruct_equilibrium_boundaries" in text:
        return text, False, ""
    anchor = ")+R(kernel void initialize)+\"(\"+R(global fpxx* fi"
    if anchor not in text:
        return text, False, "kernel_initialize_anchor_missing"
    return text.replace(anchor, KERNEL_BLOCK + "\n" + anchor, 1), True, ""


def insert_domain_kernel_member(text: str) -> Tuple[str, bool, str]:
    if "kernel_reconstruct_equilibrium_boundaries" in text:
        return text, False, ""
    old = "\tKernel kernel_update_fields; // reads DDFs and updates (rho, u, T) in device memory\n"
    new = old + "#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n\tKernel kernel_reconstruct_equilibrium_boundaries; // rebuild TYPE_E boundary DDFs from prescribed rho/u\n#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_hpp_kernel_member_anchor_missing"


def insert_domain_enqueue_decl(text: str) -> Tuple[str, bool, str]:
    if re.search(r"void\s+enqueue_reconstruct_equilibrium_boundaries\s*\(", text):
        return text, False, ""
    old = "\tvoid enqueue_update_fields(); // update fields (rho, u, T) manually\n"
    new = old + "#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n\tvoid enqueue_reconstruct_equilibrium_boundaries(); // rebuild TYPE_E boundary DDFs after host-side rho/u edits\n#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_hpp_enqueue_decl_anchor_missing"


def insert_lbm_public_decl(text: str) -> Tuple[str, bool, str]:
    if re.search(r"void\s+reconstruct_equilibrium_boundaries\s*\(", text):
        return text, False, ""
    old = "\tvoid update_fields(); // update fields (rho, u, T) manually\n"
    new = old + "#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n\tvoid reconstruct_equilibrium_boundaries(); // rebuild TYPE_E boundary DDFs from current rho/u fields\n#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_hpp_lbm_public_decl_anchor_missing"


def patch_lbm_hpp(text: str) -> Tuple[str, bool, List[str]]:
    reasons: List[str] = []
    changed_any = False
    for patcher in [insert_domain_kernel_member, insert_domain_enqueue_decl, insert_lbm_public_decl]:
        text, changed, reason = patcher(text)
        changed_any = changed_any or changed
        if reason:
            reasons.append(reason)
    return text, changed_any, reasons


def insert_kernel_binding(text: str) -> Tuple[str, bool, str]:
    if re.search(r"Kernel\s*\([^;]*reconstruct_equilibrium_boundaries", text, flags=re.DOTALL):
        return text, False, ""
    old = '\tkernel_update_fields = Kernel(device, N, "update_fields", fi, rho, u, flags, t, fx, fy, fz);\n'
    new = old + '#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n\tkernel_reconstruct_equilibrium_boundaries = Kernel(device, N, "reconstruct_equilibrium_boundaries", fi, rho, u, flags, t);\n#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n'
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_cpp_kernel_binding_anchor_missing"


def insert_domain_enqueue_impl(text: str) -> Tuple[str, bool, str]:
    if re.search(r"LBM_Domain::enqueue_reconstruct_equilibrium_boundaries\s*\(", text):
        return text, False, ""
    old = "#endif // UPDATE_FIELDS\n}\n"
    new = (
        old
        + "#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
        + "void LBM_Domain::enqueue_reconstruct_equilibrium_boundaries() { // rebuild TYPE_E boundary DDFs after host-side rho/u edits\n"
        + "\tkernel_reconstruct_equilibrium_boundaries.set_parameters(4u, t).enqueue_run();\n"
        + "\tt_last_update_fields = max_ulong;\n"
        + "}\n"
        + "#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
    )
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_cpp_domain_enqueue_impl_anchor_missing"


def insert_lbm_public_impl(text: str) -> Tuple[str, bool, str]:
    if re.search(r"LBM::reconstruct_equilibrium_boundaries\s*\(", text):
        return text, False, ""
    old = "void LBM::reset() { // reset simulation (takes effect in following run() call)\n\tinitialized = false;\n}\n"
    new = (
        "void LBM::reset() { // reset simulation (takes effect in following run() call)\n"
        "\tinitialized = false;\n"
        "}\n\n"
        "#ifdef RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
        "void LBM::reconstruct_equilibrium_boundaries() { // rebuild TYPE_E boundary DDFs from current rho/u fields\n"
        "\tfor(uint d=0u; d<get_D(); d++) lbm_domain[d]->enqueue_reconstruct_equilibrium_boundaries();\n"
        "\tfor(uint d=0u; d<get_D(); d++) lbm_domain[d]->finish_queue();\n"
        "}\n"
        "#endif // RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
    )
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_cpp_lbm_public_impl_anchor_missing"


def insert_device_define_forwarder(text: str) -> Tuple[str, bool, str]:
    if '"\\n\t#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"' in text:
        return text, False, ""
    old = '#endif // EQUILIBRIUM_BOUNDARIES\n'
    new = old + "\n" + DEVICE_DEFINE_BLOCK
    patched, changed = replace_once(text, old, new)
    return patched, changed, "" if changed else "lbm_cpp_device_define_anchor_missing"


def patch_lbm_cpp(text: str) -> Tuple[str, bool, List[str]]:
    reasons: List[str] = []
    changed_any = False
    for patcher in [insert_kernel_binding, insert_domain_enqueue_impl, insert_lbm_public_impl, insert_device_define_forwarder]:
        text, changed, reason = patcher(text)
        changed_any = changed_any or changed
        if reason:
            reasons.append(reason)
    return text, changed_any, reasons


def main() -> int:
    args = parse_args()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    paths = {
        "kernel": source_root / "src" / "kernel.cpp",
        "lbm_cpp": source_root / "src" / "lbm.cpp",
        "lbm_hpp": source_root / "src" / "lbm.hpp",
        "defines": source_root / "src" / "defines.hpp",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    before = {key: read_text(path) for key, path in paths.items()}

    reasons: List[str] = []
    if missing:
        reasons.extend(f"missing_source_file:{path}" for path in missing)

    after = dict(before)
    changes: Dict[str, bool] = {key: False for key in paths}
    if not reasons:
        after["kernel"], changes["kernel"], reason = insert_kernel_block(before["kernel"])
        if reason:
            reasons.append(reason)
        after["lbm_hpp"], changes["lbm_hpp"], hpp_reasons = patch_lbm_hpp(before["lbm_hpp"])
        reasons.extend(hpp_reasons)
        after["lbm_cpp"], changes["lbm_cpp"], cpp_reasons = patch_lbm_cpp(before["lbm_cpp"])
        reasons.extend(cpp_reasons)

    changed = any(changes.values())
    if not reasons and changed and not args.dry_run:
        for key in ["kernel", "lbm_cpp", "lbm_hpp"]:
            if changes[key]:
                paths[key].write_text(after[key], encoding="utf-8")

    evidence_after = source_evidence(source_root) if not reasons and not args.dry_run else {}
    macros_after = enabled_macros(read_text(paths["defines"])) if paths["defines"].is_file() else {}
    classification = classify_gate(evidence_after, macros_after) if evidence_after else {"Gate": "dry_run" if not reasons else "fail", "Reasons": reasons}
    gate = "pass" if not reasons else "fail"
    if not args.dry_run and gate == "pass" and classification.get("Gate") == "fail":
        gate = "fail"
        reasons.extend(classification.get("Reasons", []))

    records = {
        key: file_record(paths[key], before.get(key, ""), after.get(key, ""), bool(changes.get(key)))
        for key in ["kernel", "lbm_cpp", "lbm_hpp", "defines"]
    }
    output: Dict[str, Any] = {
        "Schema": "citylbm.patch_fluidx3d_equilibrium_boundary_source.v1",
        "GeneratedAtUtc": utc_now(),
        "FluidX3DSource": str(source_root),
        "DryRun": bool(args.dry_run),
        "Gate": gate,
        "Reasons": reasons,
        "Changed": bool(changed and not args.dry_run and not reasons),
        "WouldChange": bool(changed),
        "Files": records,
        "EvidenceAfter": evidence_after,
        "MacroForwarderAdded": '"\\n\t#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"' in after.get("lbm_cpp", ""),
        "NextAction": (
            "Run audit_fluidx3d_equilibrium_boundary.py, then enable_fluidx3d_ddf_reconstruction_route.py on the generated case."
            if gate == "pass"
            else "Do not launch CFD; inspect Reasons and patch the source layout explicitly."
        ),
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"patch_fluidx3d_equilibrium_boundary_source_gate={gate}; changed={output['Changed']}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
