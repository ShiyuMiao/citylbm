#!/usr/bin/env python3
"""Smoke-test FluidX3D TYPE_E equilibrium-boundary source audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "scripts" / "audit_fluidx3d_equilibrium_boundary.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_audit(source_root: Path, out_path: Path, expected_returncode: int) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(AUDIT),
            "--fluidx3d-source",
            str(source_root),
            "--out",
            str(out_path),
        ],
        cwd=str(REPO),
        text=True,
        capture_output=True,
    )
    if completed.returncode != expected_returncode:
        raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
    return load_json(out_path)


def create_pass_source(root: Path) -> None:
    write(
        root / "src" / "defines.hpp",
        """
#define EQUILIBRIUM_BOUNDARIES
#define RECONSTRUCT_INLET_STRESS_DDF
#define TYPE_E 0x02
""".lstrip(),
    )
    write(
        root / "src" / "kernel.cpp",
        """
kernel void reconstruct_equilibrium_boundaries(global fpxx* fi, const global float* rho, const global float* u, const global uchar* flags, const ulong t) {
    const uxx n = get_global_id(0);
    if((flags[n]&TYPE_BO)!=TYPE_E) return;
    uxx j[def_velocity_set];
    float feq[def_velocity_set];
    calculate_f_eq(rho[n], u[n], u[def_N+(ulong)n], u[2ul*def_N+(ulong)n], feq);
    store_f(n, feq, fi, j, t);
}
kernel void stream_collide(global fpxx* fi, const global float* rho, const global float* u, const global uchar* flags) {
    uchar flagsn_bo = flags[0]&TYPE_BO;
    float rhon, uxn, uyn, uzn;
    if(flagsn_bo==TYPE_E) { rhon = rho[n]; uxn = u[n]; uyn = u[def_N+(ulong)n]; uzn = u[2ul*def_N+(ulong)n]; }
    float feq[def_velocity_set];
    for(uint i=0u; i<def_velocity_set; i++) fhn[i] = flagsn_bo==TYPE_E ? feq[i] : fhn[i];
}
""".lstrip(),
    )
    write(
        root / "src" / "lbm.cpp",
        """
kernel_reconstruct_equilibrium_boundaries = Kernel(device, N, "reconstruct_equilibrium_boundaries", fi, rho, u, flags, t);
void LBM_Domain::enqueue_reconstruct_equilibrium_boundaries() {}
void LBM::reconstruct_equilibrium_boundaries() {}
""".lstrip(),
    )
    write(root / "src" / "lbm.hpp", "void reconstruct_equilibrium_boundaries();\n")


def create_fail_source(root: Path) -> None:
    write(root / "src" / "defines.hpp", "#define TYPE_E 0x02\n")
    write(root / "src" / "kernel.cpp", "// TYPE_E token without DDF route\n")
    write(root / "src" / "lbm.cpp", "// no kernel binding\n")
    write(root / "src" / "lbm.hpp", "// no public call\n")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_fluidx3d_boundary_audit_") as raw:
        temp = Path(raw)
        pass_root = temp / "pass_source"
        fail_root = temp / "fail_source"
        create_pass_source(pass_root)
        create_fail_source(fail_root)

        passed = run_audit(pass_root, temp / "pass.json", 0)
        if passed["Gate"] != "pass":
            raise AssertionError(passed)
        if passed["BoundaryRouteClass"] != "fluidx3d_type_e_equilibrium_or_inlet_stress_ddf_route_enabled":
            raise AssertionError(passed)
        if not passed["Evidence"]["has_reconstruct_store_f"]:
            raise AssertionError(passed)

        failed = run_audit(fail_root, temp / "fail.json", 2)
        if failed["Gate"] != "fail":
            raise AssertionError(failed)
        if "reconstruct_equilibrium_kernel_missing" not in failed["Reasons"]:
            raise AssertionError(failed)

    print("fluidx3d_equilibrium_boundary_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
