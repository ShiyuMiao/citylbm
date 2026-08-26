#!/usr/bin/env python3
"""Patch legacy generated setup.cpp files with runtime inlet diagnostics.

Older CityLBM-generated native cases can contain a digital-filter inlet but no
runtime CSV proving that the inlet preserves U, k and RMS statistics. This
script is deliberately narrow: it patches generated setup.cpp files that
already expose CustomTable profile arrays and a runtime inlet refresh loop.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


PATCH_MARKER = "citylbm_inlet_diagnostics_csv"
INSERT_MARKER = "    updateDigitalFilter(0u);"
RUNTIME_WRITE_MARKER = (
    "            lbm.u.write_to_device();\n"
    "            #if defined(RECONSTRUCT_INLET_STRESS_DDF)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch legacy FluidX3D setup.cpp runtime inlet diagnostics.")
    parser.add_argument("--case-dir", default="", help="Case directory containing setup.cpp or src/setup.cpp.")
    parser.add_argument("--setup", default="", help="Explicit generated setup.cpp path.")
    parser.add_argument("--out", required=True, help="Output JSON manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Report intended edits without writing setup.cpp.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def resolve_setup(args: argparse.Namespace) -> Path:
    if args.setup:
        return Path(args.setup).expanduser().resolve()
    if not args.case_dir:
        raise SystemExit("--case-dir or --setup is required")
    case_dir = Path(args.case_dir).expanduser().resolve()
    for candidate in (case_dir / "src" / "setup.cpp", case_dir / "setup.cpp"):
        if candidate.is_file():
            return candidate
    return case_dir / "src" / "setup.cpp"


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def line_ending(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def ensure_include(text: str, include: str) -> Tuple[str, bool]:
    if include in text:
        return text, False
    marker = '#include "lbm.hpp"'
    ending = line_ending(text)
    if marker in text:
        return text.replace(marker, marker + ending + include, 1), True
    return include + ending + text, True


def diagnostics_block(ending: str) -> str:
    lines = [
        "    // CityLBM runtime inlet diagnostics patch: records inlet U/k/RMS preservation during the native run.",
        '    const char* citylbm_inlet_diagnostics_csv = "citylbm_inlet_turbulence_stats.csv";',
        "    auto writeSyntheticTurbulentInletDiagnostics = [&](uint t_step) {",
        "        const double citylbm_velocity_scale_lbm_to_mps = (double)citylbm_u_ref_si / fmax((double)citylbm_u_ref_lbm, 1.0e-12);",
        "        const double citylbm_variance_scale_lbm_to_m2s2 = citylbm_velocity_scale_lbm_to_mps * citylbm_velocity_scale_lbm_to_mps;",
        "        if(t_step == 0u) {",
        "            std::ofstream citylbm_diag_header(citylbm_inlet_diagnostics_csv, std::ios::out);",
        '            citylbm_diag_header << "step,profile_index,z_m,z_cell,target_u_mps,target_u_rms_mps,target_v_rms_mps,target_w_rms_mps,target_k_m2s2,target_r11_m2s2,target_r22_m2s2,target_r33_m2s2,target_r12_m2s2,target_r13_m2s2,target_r23_m2s2,mean_u_mps,mean_v_mps,mean_w_mps,u_rms_mps,v_rms_mps,w_rms_mps,k_m2s2,mean_x_mps,mean_y_mps,mean_z_mps,x_rms_mps,y_rms_mps,z_rms_mps,measured_r11_m2s2,measured_r22_m2s2,measured_r33_m2s2,measured_r12_m2s2,measured_r13_m2s2,measured_r23_m2s2,samples_y,effective_sample_z_cell,effective_sample_z_m\\n";',
        "        }",
        "        std::ofstream citylbm_diag(citylbm_inlet_diagnostics_csv, std::ios::app);",
        "        for(int citylbm_pi=0; citylbm_pi<(int)profile_count; citylbm_pi++) {",
        "            int sample_z = (int)floorf((profile_z_m[citylbm_pi] - profile_origin_z_m) / citylbm_dx_m);",
        "            if(sample_z < 1) sample_z = 1;",
        "            if(sample_z > (int)Nz - 1) sample_z = (int)Nz - 1;",
        "            double sum_u = 0.0, sum_v = 0.0, sum_w = 0.0;",
        "            double sum_u2 = 0.0, sum_v2 = 0.0, sum_w2 = 0.0;",
        "            double sum_x = 0.0, sum_y = 0.0, sum_z = 0.0;",
        "            double sum_x2 = 0.0, sum_y2 = 0.0, sum_z2 = 0.0;",
        "            double sum_xy = 0.0, sum_xz = 0.0, sum_yz = 0.0;",
        "            ulong sample_count = 0ull;",
        "            for(ulong n=0ull; n<lbm.get_N(); n++) {",
        "                uint x=0u, y=0u, z=0u;",
        "                lbm.coordinates(n, x, y, z);",
        "                bool citylbm_is_inlet = false;",
        "                if(fabs(dir_x) >= fabs(dir_y)) {",
        "                    citylbm_is_inlet = dir_x > 0.0f ? x == 0u : x == Nx-1u;",
        "                } else {",
        "                    citylbm_is_inlet = dir_y > 0.0f ? y == 0u : y == Ny-1u;",
        "                }",
        "                if(citylbm_is_inlet && z == (uint)sample_z && (lbm.flags[n]&TYPE_S)!=TYPE_S) {",
        "                    double ux = (double)lbm.u.x[n] * citylbm_velocity_scale_lbm_to_mps;",
        "                    double uy = (double)lbm.u.y[n] * citylbm_velocity_scale_lbm_to_mps;",
        "                    double uz = (double)lbm.u.z[n] * citylbm_velocity_scale_lbm_to_mps;",
        "                    double stream = ux*(double)dir_x + uy*(double)dir_y + uz*(double)dir_z;",
        "                    double cross1 = ux*(double)lat_x + uy*(double)lat_y;",
        "                    double cross2 = uz;",
        "                    sum_u += stream; sum_v += cross1; sum_w += cross2;",
        "                    sum_u2 += stream*stream; sum_v2 += cross1*cross1; sum_w2 += cross2*cross2;",
        "                    sum_x += ux; sum_y += uy; sum_z += uz;",
        "                    sum_x2 += ux*ux; sum_y2 += uy*uy; sum_z2 += uz*uz;",
        "                    sum_xy += ux*uy; sum_xz += ux*uz; sum_yz += uy*uz;",
        "                    sample_count++;",
        "                }",
        "            }",
        "            if(sample_count > 0ull) {",
        "                double inv = 1.0 / (double)sample_count;",
        "                double mean_u = sum_u * inv, mean_v = sum_v * inv, mean_w = sum_w * inv;",
        "                double rms_u = sqrt(fmax(0.0, sum_u2 * inv - mean_u * mean_u));",
        "                double rms_v = sqrt(fmax(0.0, sum_v2 * inv - mean_v * mean_v));",
        "                double rms_w = sqrt(fmax(0.0, sum_w2 * inv - mean_w * mean_w));",
        "                double measured_k = 0.5 * (rms_u*rms_u + rms_v*rms_v + rms_w*rms_w);",
        "                double mean_x = sum_x * inv, mean_y = sum_y * inv, mean_z = sum_z * inv;",
        "                double measured_r11 = fmax(0.0, sum_x2 * inv - mean_x * mean_x);",
        "                double measured_r22 = fmax(0.0, sum_y2 * inv - mean_y * mean_y);",
        "                double measured_r33 = fmax(0.0, sum_z2 * inv - mean_z * mean_z);",
        "                double measured_r12 = sum_xy * inv - mean_x * mean_y;",
        "                double measured_r13 = sum_xz * inv - mean_x * mean_z;",
        "                double measured_r23 = sum_yz * inv - mean_y * mean_z;",
        "                double rms_x = sqrt(measured_r11), rms_y = sqrt(measured_r22), rms_z = sqrt(measured_r33);",
        "                double target_u = (double)profile_u_lbm[citylbm_pi] * citylbm_velocity_scale_lbm_to_mps;",
        "                double target_u_rms = (double)profile_u_rms_lbm[citylbm_pi] * citylbm_velocity_scale_lbm_to_mps;",
        "                double target_v_rms = (double)profile_v_rms_lbm[citylbm_pi] * citylbm_velocity_scale_lbm_to_mps;",
        "                double target_w_rms = (double)profile_w_rms_lbm[citylbm_pi] * citylbm_velocity_scale_lbm_to_mps;",
        "                double target_k = (double)profile_k_lbm[citylbm_pi] * citylbm_variance_scale_lbm_to_m2s2;",
        "                double target_r11 = target_u_rms * target_u_rms;",
        "                double target_r22 = target_v_rms * target_v_rms;",
        "                double target_r33 = target_w_rms * target_w_rms;",
        "                double sample_z_m = (double)profile_origin_z_m + ((double)sample_z + 0.5) * (double)citylbm_dx_m;",
        "                citylbm_diag << t_step << \",\" << citylbm_pi << \",\" << profile_z_m[citylbm_pi] << \",\" << sample_z",
        "                    << \",\" << target_u << \",\" << target_u_rms << \",\" << target_v_rms << \",\" << target_w_rms << \",\" << target_k",
        "                    << \",\" << target_r11 << \",\" << target_r22 << \",\" << target_r33 << \",\" << 0.0 << \",\" << 0.0 << \",\" << 0.0",
        "                    << \",\" << mean_u << \",\" << mean_v << \",\" << mean_w << \",\" << rms_u << \",\" << rms_v << \",\" << rms_w << \",\" << measured_k",
        "                    << \",\" << mean_x << \",\" << mean_y << \",\" << mean_z << \",\" << rms_x << \",\" << rms_y << \",\" << rms_z",
        "                    << \",\" << measured_r11 << \",\" << measured_r22 << \",\" << measured_r33 << \",\" << measured_r12 << \",\" << measured_r13 << \",\" << measured_r23",
        "                    << \",\" << sample_count << \",\" << sample_z << \",\" << sample_z_m << \"\\n\";",
        "            }",
        "        }",
        "    };",
        "",
    ]
    return ending.join(lines)


def patch_setup(text: str) -> Tuple[str, Dict[str, int], List[str]]:
    reasons: List[str] = []
    if PATCH_MARKER in text:
        return text, {"IncludeInsertions": 0, "DiagnosticsBlockInsertions": 0, "RuntimeCallInsertions": 0}, reasons
    for required in [
        "profile_z_m",
        "profile_u_lbm",
        "profile_k_lbm",
        "profile_u_rms_lbm",
        "profile_v_rms_lbm",
        "profile_w_rms_lbm",
        "profile_origin_z_m",
        "citylbm_dx_m",
        "dir_x",
        "dir_y",
        "lat_x",
        "lat_y",
    ]:
        if required not in text:
            reasons.append(f"required_symbol_missing:{required}")
    if INSERT_MARKER not in text:
        reasons.append("initial_digital_filter_marker_missing")

    ending = line_ending(text)
    runtime_marker = RUNTIME_WRITE_MARKER.replace("\n", ending)
    if runtime_marker not in text:
        reasons.append("runtime_velocity_upload_marker_missing")
    if reasons:
        return text, {"IncludeInsertions": 0, "DiagnosticsBlockInsertions": 0, "RuntimeCallInsertions": 0}, reasons

    updated, include_count = ensure_include(text, "#include <fstream>")
    block = diagnostics_block(ending)
    updated = updated.replace(INSERT_MARKER, block + INSERT_MARKER, 1)
    call = "            writeSyntheticTurbulentInletDiagnostics(tnow);" + ending
    updated = updated.replace(runtime_marker, call + runtime_marker, 1)
    return updated, {
        "IncludeInsertions": 1 if include_count else 0,
        "DiagnosticsBlockInsertions": 1,
        "RuntimeCallInsertions": 1,
    }, reasons


def main() -> int:
    args = parse_args()
    setup_path = resolve_setup(args)
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text = setup_path.read_text(encoding="utf-8-sig") if setup_path.is_file() else ""
    reasons: List[str] = []
    if not setup_path.is_file():
        reasons.append("setup_cpp_missing")

    old_hash = sha256_text(text) if text else ""
    updated, edits, patch_reasons = patch_setup(text) if text else (text, {}, [])
    reasons.extend(patch_reasons)
    already_patched = bool(text and PATCH_MARKER in text)
    changed = updated != text

    backup_path = ""
    if changed and not args.dry_run:
        candidate = setup_path.with_name(setup_path.name + ".before_runtime_inlet_diagnostics_patch")
        if not candidate.exists():
            candidate.write_text(text, encoding="utf-8")
            backup_path = str(candidate)
        setup_path.write_text(updated, encoding="utf-8")

    manifest = {
        "Schema": "citylbm.patch_legacy_runtime_inlet_diagnostics.v1",
        "GeneratedAtUtc": utc_now(),
        "Setup": str(setup_path),
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons,
        "AlreadyPatched": already_patched,
        "DryRun": bool(args.dry_run),
        "WouldChange": changed,
        "Changed": bool(changed and not args.dry_run),
        "Edits": edits,
        "Backup": backup_path,
        "Sha256Before": old_hash,
        "Sha256After": sha256_text(updated) if updated else "",
        "DiagnosticsCsv": "citylbm_inlet_turbulence_stats.csv" if not reasons else "",
    }
    write_json(out_path, manifest)
    print(f"runtime_inlet_diagnostics_patch_gate={manifest['Gate']}; changed={manifest['Changed']}; manifest={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if manifest["Gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
