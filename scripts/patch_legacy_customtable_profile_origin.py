#!/usr/bin/env python3
"""Patch legacy generated CustomTable setup.cpp to sample AF profiles in metres.

Older generated Case E setups stored both ``profile_z_m`` and
``profile_z_cells`` but interpolated the inlet profile against cell indices.
That makes a domain-origin dependent AF table behave like a lattice-height
table. This script is intentionally narrow: it only patches legacy generated
setup files that already contain CustomTable profile arrays and a
``domain_origin.json`` with ``DomainMin`` and ``Dx``.
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch legacy CustomTable setup.cpp profile height sampling.")
    parser.add_argument("--case-dir", default="", help="Case directory containing setup.cpp or src/setup.cpp.")
    parser.add_argument("--setup", default="", help="Explicit generated setup.cpp path.")
    parser.add_argument("--domain-origin", default="", help="Explicit domain_origin.json path.")
    parser.add_argument("--origin-z", type=float, default=None, help="Override physical domain origin z in metres.")
    parser.add_argument("--dx", type=float, default=None, help="Override grid spacing in metres.")
    parser.add_argument("--out", required=True, help="Output JSON manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Report intended edits without writing setup.cpp.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def format_float(value: float) -> str:
    return f"{value:.8f}"


def resolve_setup(args: argparse.Namespace) -> Path:
    if args.setup:
        return Path(args.setup).expanduser().resolve()
    if not args.case_dir:
        raise SystemExit("--case-dir or --setup is required")
    case_dir = Path(args.case_dir).expanduser().resolve()
    for candidate in [case_dir / "src" / "setup.cpp", case_dir / "setup.cpp"]:
        if candidate.is_file():
            return candidate
    return case_dir / "src" / "setup.cpp"


def resolve_domain_origin(args: argparse.Namespace, setup_path: Path) -> Path:
    if args.domain_origin:
        return Path(args.domain_origin).expanduser().resolve()
    if args.case_dir:
        return Path(args.case_dir).expanduser().resolve() / "domain_origin.json"
    candidates = [
        setup_path.parent / "domain_origin.json",
        setup_path.parent.parent / "domain_origin.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def read_domain_origin(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def domain_origin_z(data: Dict[str, Any]) -> float | None:
    domain_min = data.get("DomainMin")
    if isinstance(domain_min, list) and len(domain_min) >= 3:
        try:
            return float(domain_min[2])
        except (TypeError, ValueError):
            return None
    for key in ["OriginZ", "origin_z_m", "ProfileOriginZM", "profile_origin_z_m"]:
        if key in data:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                return None
    return None


def domain_dx(data: Dict[str, Any]) -> float | None:
    for key in ["Dx", "dx", "DxM", "dx_m"]:
        if key in data:
            try:
                return float(data[key])
            except (TypeError, ValueError):
                return None
    return None


def parse_float_array(text: str, name: str) -> List[float]:
    match = re.search(rf"\b{name}\s*\[[^\]]*\]\s*=\s*\{{([^}}]+)\}}", text)
    if not match:
        return []
    values: List[float] = []
    for raw in match.group(1).split(","):
        token = raw.strip().rstrip("fF")
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            return []
    return values


def infer_dx_from_arrays(text: str) -> float | None:
    z_m = parse_float_array(text, "profile_z_m")
    z_cells = parse_float_array(text, "profile_z_cells")
    pairs = [(m, c) for m, c in zip(z_m, z_cells) if abs(c) > 1.0e-9]
    if not pairs:
        return None
    ratios = [m / c for m, c in pairs[: min(len(pairs), 4)]]
    avg = sum(ratios) / len(ratios)
    if avg > 0.0:
        return avg
    return None


def insert_constants(text: str, origin_z: float, dx: float) -> Tuple[str, int]:
    if "profile_origin_z_m" in text and "profile_dx_m" in text:
        return text, 0
    line_ending = "\r\n" if "\r\n" in text else "\n"
    insertion = (
        f"    const float profile_origin_z_m = {format_float(origin_z)}f;{line_ending}"
        f"    const float profile_dx_m = {format_float(dx)}f;{line_ending}"
    )
    pattern = re.compile(r"(^\s*const\s+uint\s+profile_count\s*=\s*[^;]+;\s*\r?\n)", re.MULTILINE)
    updated, count = pattern.subn(r"\1" + insertion, text, count=1)
    return updated, count


def patch_interpolator(text: str) -> Tuple[str, int]:
    replacements = [
        (r"auto\s+interpProfile\s*=\s*\[\&\]\s*\(\s*const\s+float\*\s+values\s*,\s*float\s+z_cell\s*\)\s*->\s*float\s*\{",
         "auto interpProfile = [&](const float* values, float z_m) -> float {"),
        (r"\bz_cell\s*<=\s*profile_z_cells\[0\]", "z_m <= profile_z_m[0]"),
        (r"\bz_cell\s*>=\s*profile_z_cells\[profile_count-1\]", "z_m >= profile_z_m[profile_count-1]"),
        (r"\bz_cell\s*<=\s*profile_z_cells\[i\+1\]", "z_m <= profile_z_m[i+1]"),
        (r"profile_z_cells\[i\+1\]\s*-\s*profile_z_cells\[i\]", "profile_z_m[i+1] - profile_z_m[i]"),
        (r"\(z_cell\s*-\s*profile_z_cells\[i\]\)", "(z_m - profile_z_m[i])"),
    ]
    total = 0
    updated = text
    for pattern, replacement in replacements:
        updated, count = re.subn(pattern, replacement, updated)
        total += count
    return updated, total


def patch_profile_calls(text: str) -> Tuple[str, int]:
    replacements = [
        (
            r"const\s+float\s+z\s*=\s*\(float\)z_cell\s*\+\s*0\.5f;\s*\n\s*const\s+float\s+u_mag\s*=\s*interpProfile\(profile_u_lbm,\s*z\);",
            "const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;\n        const float u_mag = interpProfile(profile_u_lbm, z_m);",
        ),
        (
            r"const\s+float\s+z\s*=\s*\(float\)z_cell\s*\+\s*0\.5f;\s*\n\s*const\s+float\s+mean_u\s*=\s*interpProfile\(profile_u_lbm,\s*z\);",
            "const float z_m = profile_origin_z_m + ((float)z_cell + 0.5f) * profile_dx_m;\n        const float mean_u = interpProfile(profile_u_lbm, z_m);",
        ),
        (r"interpProfile\(profile_u_rms_lbm,\s*z\)", "interpProfile(profile_u_rms_lbm, z_m)"),
        (r"interpProfile\(profile_v_rms_lbm,\s*z\)", "interpProfile(profile_v_rms_lbm, z_m)"),
        (r"interpProfile\(profile_w_rms_lbm,\s*z\)", "interpProfile(profile_w_rms_lbm, z_m)"),
        (r"interpProfile\(profile_k_lbm,\s*z\)", "interpProfile(profile_k_lbm, z_m)"),
    ]
    total = 0
    updated = text
    for pattern, replacement in replacements:
        updated, count = re.subn(pattern, replacement, updated)
        total += count
    return updated, total


def patch_setup(text: str, origin_z: float, dx: float) -> Tuple[str, Dict[str, int]]:
    updated, constant_count = insert_constants(text, origin_z, dx)
    updated, interpolator_count = patch_interpolator(updated)
    updated, call_count = patch_profile_calls(updated)
    return updated, {
        "ProfileOriginInsertions": constant_count,
        "InterpolatorRewrites": interpolator_count,
        "ProfileCallRewrites": call_count,
    }


def main() -> int:
    args = parse_args()
    setup_path = resolve_setup(args)
    domain_path = resolve_domain_origin(args, setup_path)
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text = setup_path.read_text(encoding="utf-8-sig") if setup_path.is_file() else ""
    domain_data = read_domain_origin(domain_path)
    origin_z = args.origin_z if args.origin_z is not None else domain_origin_z(domain_data)
    dx = args.dx if args.dx is not None else domain_dx(domain_data)
    if dx is None:
        dx = infer_dx_from_arrays(text)

    reasons: List[str] = []
    if not setup_path.is_file():
        reasons.append("setup_cpp_missing")
    if "profile_z_m" not in text or "profile_u_lbm" not in text:
        reasons.append("custom_table_profile_arrays_missing")
    if "profile_z_cells" not in text:
        reasons.append("legacy_profile_z_cells_missing_or_already_new_style")
    if origin_z is None:
        reasons.append("domain_origin_z_missing")
    if dx is None or dx <= 0.0:
        reasons.append("dx_m_missing_or_invalid")

    if reasons:
        updated = text
        metrics = {"ProfileOriginInsertions": 0, "InterpolatorRewrites": 0, "ProfileCallRewrites": 0}
    else:
        updated, metrics = patch_setup(text, float(origin_z), float(dx))
        if updated == text:
            reasons.append("no_legacy_customtable_origin_patch_applied")

    changed = bool(updated != text and not reasons and not args.dry_run)
    if changed:
        setup_path.write_text(updated, encoding="utf-8")

    output: Dict[str, Any] = {
        "Schema": "citylbm.patch_legacy_customtable_profile_origin.v1",
        "GeneratedAtUtc": utc_now(),
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons,
        "DryRun": bool(args.dry_run),
        "SetupPath": str(setup_path),
        "DomainOriginPath": str(domain_path),
        "OriginZ": origin_z,
        "DxM": dx,
        "Changed": changed,
        "WouldChange": bool(updated != text and not reasons),
        "BeforeSha256": sha256_text(text),
        "AfterSha256": sha256_text(updated),
        **metrics,
        "NextAction": (
            "Re-run audit_inlet_source.py and the no-CFD preflight before any solver run."
            if not reasons
            else "Regenerate the case from the current CityLBM code or provide domain_origin.json with Dx/DomainMin."
        ),
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"patch_legacy_customtable_profile_origin_gate={output['Gate']}; changed={output['Changed']}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if output["Gate"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
