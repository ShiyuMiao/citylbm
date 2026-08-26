#!/usr/bin/env python3
"""Smoke-test enabling FluidX3D DDF reconstruction macros."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "enable_fluidx3d_ddf_reconstruction_route.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_source(root: Path) -> None:
    write(root / "src" / "defines.hpp", "#define TYPE_E 2u\n#define EQUILIBRIUM_BOUNDARIES\n")
    write(
        root / "src" / "kernel.cpp",
        """
kernel void reconstruct_equilibrium_boundaries(global fpxx* fi, global float* rho, global float* u, const global uchar* flags, const ulong t) {
    const uxx n = get_global_id(0);
    if((flags[n]&TYPE_BO)!=TYPE_E) return;
    float feq[def_velocity_set];
    uxx j[def_velocity_set];
    calculate_f_eq(rho[n], u[n], u[def_N+(ulong)n], u[2ul*def_N+(ulong)n], feq);
    store_f(n, feq, fi, j, t);
}
kernel void stream_collide(global fpxx* fi, global float* rho, global float* u, const global uchar* flags, const ulong t) {
    if(flagsn_bo==TYPE_E) { rhon = rho[n]; uxn = u[n]; }
    for(uint i=0u; i<def_velocity_set; i++) fhn[i] = flagsn_bo==TYPE_E ? feq[i] : fhn[i];
}
#ifdef CASEA_DEVICE_SEM_STRESS_DDF
void casea_add_sem_stress_fneq() {}
#endif
""",
    )
    write(
        root / "src" / "lbm.cpp",
        'auto k = Kernel(device, N, "reconstruct_equilibrium_boundaries", fi, rho, u, flags, t);\n'
        "void LBM::reconstruct_equilibrium_boundaries() {}\n",
    )
    write(root / "src" / "lbm.hpp", "void reconstruct_equilibrium_boundaries();\n")


def write_setup(path: Path) -> None:
    write(
        path,
        "void main_setup() {\n"
        "    lbm.flags.write_to_device();\n"
        "    lbm.u.write_to_device();\n"
        "    lbm.run(100u);\n"
        "}\n",
    )


def assert_setup_patched(path: Path, expected_call: str) -> None:
    text = path.read_text(encoding="utf-8")
    if expected_call not in text:
        raise AssertionError(text)
    if text.count("lbm.u.write_to_device();") != text.count(expected_call):
        raise AssertionError(text)


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source = temp / "FluidX3D"
        write_source(source)

        casea = temp / "casea"
        casea_defines = casea / "src" / "defines.hpp"
        casea_setup = casea / "src" / "setup.cpp"
        write(
            casea_defines,
            "#define EQUILIBRIUM_BOUNDARIES\n"
            "// #define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n"
            "#define RECONSTRUCT_INLET_STRESS_DDF\n"
            "#define CASEA_DEVICE_SEM_INLET\n"
            "// #define CASEA_DEVICE_SEM_STRESS_DDF\n",
        )
        write_setup(casea_setup)
        casea_out = temp / "casea_manifest.json"
        casea_run = run_tool("--case-dir", str(casea), "--fluidx3d-source", str(source), "--out", str(casea_out))
        if casea_run.returncode != 0:
            raise AssertionError((casea_run.returncode, casea_run.stdout, casea_run.stderr))
        casea_manifest = load(casea_out)
        if casea_manifest["SelectedMacro"] != "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" or not casea_manifest["Changed"]:
            raise AssertionError(casea_manifest)
        casea_defines_text = casea_defines.read_text(encoding="utf-8")
        if "#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" not in casea_defines_text:
            raise AssertionError(casea_defines_text)
        if re.search(r"^\s*#\s*define\s+RECONSTRUCT_INLET_STRESS_DDF\b", casea_defines_text, re.MULTILINE):
            raise AssertionError(casea_defines_text)
        if "RECONSTRUCT_INLET_STRESS_DDF" not in casea_manifest["DeactivatedMacros"]:
            raise AssertionError(casea_manifest)
        assert_setup_patched(casea_setup, "lbm.reconstruct_equilibrium_boundaries();")
        if casea_manifest["ReconstructionCallInsertions"] != 1 or not casea_manifest["SetupChanged"]:
            raise AssertionError(casea_manifest)

        generic = temp / "generic"
        generic_defines = generic / "src" / "defines.hpp"
        generic_setup = generic / "src" / "setup.cpp"
        write(
            generic_defines,
            "#define EQUILIBRIUM_BOUNDARIES\n"
            "// #define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n",
        )
        write_setup(generic_setup)
        generic_out = temp / "generic_manifest.json"
        generic_run = run_tool("--case-dir", str(generic), "--fluidx3d-source", str(source), "--out", str(generic_out))
        if generic_run.returncode != 0:
            raise AssertionError((generic_run.returncode, generic_run.stdout, generic_run.stderr))
        generic_manifest = load(generic_out)
        if generic_manifest["SelectedMacro"] != "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" or not generic_manifest["Changed"]:
            raise AssertionError(generic_manifest)
        if "#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" not in generic_defines.read_text(encoding="utf-8"):
            raise AssertionError(generic_defines.read_text(encoding="utf-8"))
        assert_setup_patched(generic_setup, "lbm.reconstruct_equilibrium_boundaries();")

        root_layout = temp / "root_layout"
        root_defines = root_layout / "defines.hpp"
        root_setup = root_layout / "setup.cpp"
        write(
            root_defines,
            "#define EQUILIBRIUM_BOUNDARIES\n"
            "// #define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n",
        )
        write_setup(root_setup)
        root_out = temp / "root_manifest.json"
        root_run = run_tool("--case-dir", str(root_layout), "--fluidx3d-source", str(source), "--out", str(root_out))
        if root_run.returncode != 0:
            raise AssertionError((root_run.returncode, root_run.stdout, root_run.stderr))
        root_manifest = load(root_out)
        if root_manifest["DefinesPath"] != str(root_defines.resolve()):
            raise AssertionError(root_manifest)
        if not root_manifest["Changed"]:
            raise AssertionError(root_manifest)
        if "#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" not in root_defines.read_text(encoding="utf-8"):
            raise AssertionError(root_defines.read_text(encoding="utf-8"))
        if root_manifest["SetupPath"] != str(root_setup.resolve()):
            raise AssertionError(root_manifest)
        assert_setup_patched(root_setup, "lbm.reconstruct_equilibrium_boundaries();")

        broken = temp / "broken"
        write(broken / "src" / "defines.hpp", "#define EQUILIBRIUM_BOUNDARIES\n")
        broken_out = temp / "broken_manifest.json"
        broken_run = run_tool("--case-dir", str(broken), "--fluidx3d-source", str(temp / "missing"), "--out", str(broken_out))
        if broken_run.returncode != 2:
            raise AssertionError((broken_run.returncode, broken_run.stdout, broken_run.stderr))
        if load(broken_out)["Gate"] != "fail":
            raise AssertionError(load(broken_out))

    print("enable_fluidx3d_ddf_reconstruction_route_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
