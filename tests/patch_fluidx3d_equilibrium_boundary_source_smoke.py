#!/usr/bin/env python3
"""Smoke-test FluidX3D source patching for TYPE_E DDF reconstruction."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "scripts" / "patch_fluidx3d_equilibrium_boundary_source.py"
AUDIT = REPO / "scripts" / "audit_fluidx3d_equilibrium_boundary.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(script: Path, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    if completed.returncode != expected:
        raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
    return completed


def create_patchable_source(root: Path) -> None:
    write(root / "src" / "defines.hpp", "#define EQUILIBRIUM_BOUNDARIES\n#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\n#define TYPE_E 0x02\n")
    write(
        root / "src" / "kernel.cpp",
        """
)+R(void calculate_f_eq(const float rho, float ux, float uy, float uz, float* feq) {
}
)+R(void store_f(const uxx n, const float* fhn, global fpxx* fi, const uxx* j, const ulong t) {
}
)+R(kernel void initialize)+"("+R(global fpxx* fi, const global float* rho, global float* u, global uchar* flags // ) {
}
)+R(kernel void stream_collide)+"("+R(global fpxx* fi, global float* rho, global float* u, global uchar* flags, const ulong t, const float fx, const float fy, const float fz // ) {
	const uchar flagsn_bo = flags[n]&TYPE_BO;
	float rhon, uxn, uyn, uzn;
	if(flagsn_bo==TYPE_E) {
		rhon = rho[n];
		uxn = u[n];
		uyn = u[def_N+(ulong)n];
		uzn = u[2ul*def_N+(ulong)n];
	}
	float feq[def_velocity_set];
	for(uint i=0u; i<def_velocity_set; i++) fhn[i] = flagsn_bo==TYPE_E ? feq[i] : fhn[i];
}
""".lstrip(),
    )
    write(
        root / "src" / "lbm.cpp",
        """
void LBM_Domain::allocate(Device& device) {
	kernel_update_fields = Kernel(device, N, "update_fields", fi, rho, u, flags, t, fx, fy, fz);
}
void LBM_Domain::enqueue_update_fields() { // update fields (rho, u, T) manually
#ifndef UPDATE_FIELDS
	if(t!=t_last_update_fields) {
		kernel_update_fields.set_parameters(4u, t, fx, fy, fz).enqueue_run();
		t_last_update_fields = t;
	}
#endif // UPDATE_FIELDS
}
string LBM_Domain::device_defines(const Device_Info& device_info) const {
	return string()
#ifdef EQUILIBRIUM_BOUNDARIES
	"\\n	#define EQUILIBRIUM_BOUNDARIES"
#endif // EQUILIBRIUM_BOUNDARIES
	;
}
void LBM::reset() { // reset simulation (takes effect in following run() call)
	initialized = false;
}
void LBM::update_fields() {}
""".lstrip(),
    )
    write(
        root / "src" / "lbm.hpp",
        """
class LBM_Domain {
private:
	Kernel kernel_update_fields; // reads DDFs and updates (rho, u, T) in device memory
public:
	void enqueue_update_fields(); // update fields (rho, u, T) manually
};
class LBM {
public:
	void update_fields(); // update fields (rho, u, T) manually
};
""".lstrip(),
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_patch_fluidx3d_source_") as raw:
        temp = Path(raw)
        source = temp / "FluidX3D"
        create_patchable_source(source)

        dry_manifest = temp / "dry.json"
        run_script(PATCHER, "--fluidx3d-source", str(source), "--out", str(dry_manifest), "--dry-run")
        dry = load(dry_manifest)
        if dry["Gate"] != "pass" or not dry["WouldChange"] or dry["Changed"]:
            raise AssertionError(dry)
        if "kernel void reconstruct_equilibrium_boundaries" in (source / "src" / "kernel.cpp").read_text(encoding="utf-8"):
            raise AssertionError("dry run modified source")

        patch_manifest = temp / "patch.json"
        run_script(PATCHER, "--fluidx3d-source", str(source), "--out", str(patch_manifest))
        patched = load(patch_manifest)
        if patched["Gate"] != "pass" or not patched["Changed"]:
            raise AssertionError(patched)

        audit_manifest = temp / "audit.json"
        run_script(AUDIT, "--fluidx3d-source", str(source), "--out", str(audit_manifest))
        audited = load(audit_manifest)
        if audited["Gate"] != "pass":
            raise AssertionError(audited)

        second_manifest = temp / "second.json"
        run_script(PATCHER, "--fluidx3d-source", str(source), "--out", str(second_manifest))
        second = load(second_manifest)
        if second["Gate"] != "pass" or second["Changed"] or second["WouldChange"]:
            raise AssertionError(second)

        broken = temp / "broken"
        write(broken / "src" / "defines.hpp", "#define TYPE_E 0x02\n")
        write(broken / "src" / "kernel.cpp", "// no anchors\n")
        write(broken / "src" / "lbm.cpp", "// no anchors\n")
        write(broken / "src" / "lbm.hpp", "// no anchors\n")
        broken_manifest = temp / "broken.json"
        run_script(PATCHER, "--fluidx3d-source", str(broken), "--out", str(broken_manifest), expected=2)
        failed = load(broken_manifest)
        if failed["Gate"] != "fail" or "kernel_initialize_anchor_missing" not in failed["Reasons"]:
            raise AssertionError(failed)

    print("patch_fluidx3d_equilibrium_boundary_source_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
