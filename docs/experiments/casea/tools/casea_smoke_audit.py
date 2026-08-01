#!/usr/bin/env python3
"""Generate and audit a minimal AIJ Case A smoke-regression case."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[4]
CASEA_DIR = ROOT / "docs" / "experiments" / "casea"
RESULTS_DIR = CASEA_DIR / "results"
NATIVE_DIR = CASEA_DIR / "native_cases"
V020_CASEA = ROOT / "releases" / "v0.2.0" / "package" / "validation_experiments" / "AIJ_CaseA"
V020_EXAMPLE = ROOT / "releases" / "v0.2.0" / "package" / "examples" / "AIJ_CaseA"


DEFINES = """#pragma once

#define D3Q19
#define SRT
#define FP16S
#define EQUILIBRIUM_BOUNDARIES
#define SUBGRID

#define SX 229u
#define SY 115u
#define SZ 69u

#define TYPE_S 0b00000001
#define TYPE_E 0b00000010
#define TYPE_T 0b00000100
#define TYPE_F 0b00001000
#define TYPE_I 0b00010000
#define TYPE_G 0b00100000
#define TYPE_X 0b01000000
#define TYPE_Y 0b10000000

#if defined(FP16S) || defined(FP16C)
#define fpxx ushort
#else
#define fpxx float
#endif
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def file_record(path: Path, role: str, evidence_type: str) -> Dict[str, object]:
    actual_path = path if path.is_absolute() else ROOT / path
    exists = actual_path.exists()
    return {
        "role": role,
        "path": display_path(actual_path),
        "exists": exists,
        "size_bytes": actual_path.stat().st_size if exists else 0,
        "sha256": sha256(actual_path) if exists else "",
        "evidence_type": evidence_type,
    }


def external_file_record(path: Path, role: str, evidence_type: str) -> Dict[str, object]:
    exists = path.exists()
    return {
        "role": role,
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": sha256(path) if exists else "",
        "evidence_type": evidence_type,
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if exists else "",
    }


def binary_stl_triangle_count(path: Path) -> Optional[int]:
    if not path.exists() or path.stat().st_size < 84:
        return None
    with path.open("rb") as f:
        f.read(80)
        raw = f.read(4)
    if len(raw) != 4:
        return None
    return struct.unpack("<I", raw)[0]


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_text_fallback(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def generate_case(run_id: str) -> Path:
    case_dir = NATIVE_DIR / run_id
    case_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(V020_CASEA / "case" / "setup.cpp", case_dir / "setup.cpp")
    shutil.copy2(V020_EXAMPLE / "geometry" / "buildings.stl", case_dir / "buildings.stl")
    (case_dir / "defines.hpp").write_text(DEFINES, encoding="utf-8")
    shutil.copy2(V020_CASEA / "case" / "domain_origin.json", case_dir / "domain_origin.json")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "case": "AIJ Case A",
        "evidence_boundary": "generated smoke case only until FluidX3D run log and VTK output are verified",
        "source_setup": display_path(V020_CASEA / "case" / "setup.cpp"),
        "source_geometry": display_path(V020_EXAMPLE / "geometry" / "buildings.stl"),
        "steps": 2000,
        "dx_m": 3.5,
        "nx": 229,
        "ny": 115,
        "nz": 69,
        "geometry_triangles": binary_stl_triangle_count(case_dir / "buildings.stl"),
    }
    (case_dir / "citylbm_casea_smoke_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return case_dir


def deploy_case(case_dir: Path, fluidx3d_root: Path) -> None:
    src_dir = fluidx3d_root / "src"
    if not src_dir.exists():
        raise SystemExit(f"Missing FluidX3D src directory: {src_dir}")
    shutil.copy2(case_dir / "setup.cpp", src_dir / "setup.cpp")
    shutil.copy2(case_dir / "defines.hpp", src_dir / "defines.hpp")
    shutil.copy2(case_dir / "buildings.stl", fluidx3d_root / "buildings.stl")
    output_dir = fluidx3d_root / "output"
    output_dir.mkdir(exist_ok=True)


def audit(run_id: str, fluidx3d_root: Optional[Path], run_log: Optional[Path]) -> Dict[str, object]:
    case_dir = NATIVE_DIR / run_id
    records = [
        file_record(V020_CASEA / "case" / "setup.cpp", "v0.2.0_casea_setup", "preexisting_artifact"),
        file_record(V020_CASEA / "case" / "domain_origin.json", "v0.2.0_casea_domain_origin", "preexisting_artifact"),
        file_record(V020_CASEA / "excel" / "AIJ_CaseA_validation_from_existing_vtk.xlsx", "v0.2.0_casea_excel", "preexisting_artifact"),
        file_record(V020_CASEA / "screenshots" / "rhino_proof_AIJCASEA.png", "v0.2.0_casea_rhino_screenshot", "preexisting_artifact"),
        file_record(V020_EXAMPLE / "geometry" / "buildings.stl", "v0.2.0_casea_geometry", "preexisting_artifact"),
        file_record(case_dir / "setup.cpp", "generated_casea_setup", "newly_run"),
        file_record(case_dir / "defines.hpp", "generated_casea_defines", "newly_run"),
        file_record(case_dir / "buildings.stl", "generated_casea_geometry", "newly_run"),
    ]
    for row in records:
        if row["role"].endswith("geometry") and row["exists"]:
            row["binary_stl_triangles"] = binary_stl_triangle_count(Path(str(row["path"])))
        else:
            row["binary_stl_triangles"] = ""
    log_text = read_text_fallback(run_log) if run_log and run_log.exists() else ""
    vtk_output_paths: List[Path] = []
    if fluidx3d_root:
        vtk_output_paths = sorted((fluidx3d_root / "output").glob("*.vtk"))
    vtk_records = [
        external_file_record(path, f"fluidx3d_output_{path.name}", "newly_run")
        for path in vtk_output_paths
    ]
    if vtk_records:
        write_csv(
            RESULTS_DIR / "casea_vtk_manifest.csv",
            vtk_records,
            ["role", "path", "exists", "size_bytes", "sha256", "evidence_type", "modified_utc"],
        )
    complete_log = "Step: 2000 / 2000" in log_text
    has_vtk = any("000002000" in p.name or "2000" in p.name for p in vtk_output_paths)
    generated_ready = all((case_dir / name).exists() for name in ("setup.cpp", "defines.hpp", "buildings.stl"))
    geometry_triangles = binary_stl_triangle_count(case_dir / "buildings.stl")
    passed = bool(generated_ready and geometry_triangles and geometry_triangles > 0 and complete_log and has_vtk)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "status": "passed" if passed else "blocked",
        "evidence_type": "newly_run" if passed else "blocked",
        "generated_case_ready": generated_ready,
        "geometry_triangles": geometry_triangles,
        "run_log": str(run_log) if run_log else "",
        "run_log_complete_2000": complete_log,
        "vtk_manifest": display_path(RESULTS_DIR / "casea_vtk_manifest.csv") if vtk_records else "",
        "vtk_output_count": len(vtk_output_paths),
        "has_timestep_2000_vtk": has_vtk,
        "claim_readiness": "smoke_regression_guard" if passed else "blocked_current_smoke_regression",
        "blocking_reason": "" if passed else "Current Case A smoke regression requires a completed FluidX3D run log and timestep-2000 VTK output.",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "casea_smoke_regression.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    records.extend(
        [
            file_record(RESULTS_DIR / "casea_smoke_compile.log", "casea_compile_log", "newly_run"),
            file_record(RESULTS_DIR / "casea_smoke_deploy.log", "casea_deploy_log", "newly_run"),
            file_record(run_log, "casea_run_log", "newly_run") if run_log else file_record(RESULTS_DIR / "casea_smoke_run.log", "casea_run_log", "blocked"),
            file_record(RESULTS_DIR / "casea_smoke_regression.json", "casea_smoke_regression_json", "newly_run"),
            file_record(RESULTS_DIR / "casea_vtk_manifest.csv", "casea_vtk_manifest", "newly_run"),
        ]
    )
    for row in records:
        row.setdefault("binary_stl_triangles", "")
    write_csv(
        RESULTS_DIR / "casea_artifact_manifest.csv",
        records,
        ["role", "path", "exists", "size_bytes", "sha256", "evidence_type", "binary_stl_triangles"],
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="casea_smoke_dx3p5_steps2000")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--fluidx3d-root", type=Path)
    parser.add_argument("--run-log", type=Path)
    args = parser.parse_args()

    case_dir = NATIVE_DIR / args.run_id
    if args.generate:
        case_dir = generate_case(args.run_id)
    if args.deploy:
        if not args.fluidx3d_root:
            raise SystemExit("--deploy requires --fluidx3d-root")
        deploy_case(case_dir, args.fluidx3d_root)
    result = audit(args.run_id, args.fluidx3d_root, args.run_log)
    print(json.dumps({"case_dir": str(case_dir), **result}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
