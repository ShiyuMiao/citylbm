#!/usr/bin/env python3
"""Smoke test for boundary-source audit classification."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    audit_script = repo / "scripts" / "audit_boundary_source.py"

    with tempfile.TemporaryDirectory(prefix="citylbm_boundary_audit_") as tmp:
        tmp_dir = Path(tmp)
        setup = tmp_dir / "setup.cpp"
        metadata = tmp_dir / "case_metadata.json"
        report = tmp_dir / "boundary_source_audit.json"

        setup.write_text(
            """
void main_setup() {
    parallel_for(lbm.get_N(), [&](ulong n) {
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);
        if(z == 0u) { lbm.flags[n] = TYPE_S; return; }
        if(y == Ny-1u) {
            lbm.flags[n] = TYPE_E;
            float3 u_in = windProfile(z);
            lbm.u.x[n] = u_in.x; lbm.u.y[n] = u_in.y; lbm.u.z[n] = u_in.z;
            return;
        }
        if(y == 0u)  { lbm.flags[n] = TYPE_E; return; }
        if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }
        if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }
    });
    lbm.voxelize_stl(get_exe_path()+"../buildings.stl", TYPE_S);
    parallel_for(lbm.get_N(), [&](ulong n) {
        if(lbm.flags[n] != TYPE_E) return;
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);
        float3 u_e = windProfile(z);
        lbm.u.x[n] = u_e.x;
        lbm.u.y[n] = u_e.y;
        lbm.u.z[n] = u_e.z;
    });
}
""",
            encoding="utf-8",
        )
        metadata.write_text(
            json.dumps(
                {
                    "BoundaryConditionSummary": (
                        "dominant_axis=Y; inlet=Y+ TYPE_E velocity profile (CustomTable); "
                        "outlet=Y- TYPE_E pressure/free-outflow approximation; "
                        "lateral=X-/X+ TYPE_E slip/free approximation; top=TYPE_E; "
                        "ground/buildings=TYPE_S no-slip"
                    ),
                    "BoundaryProtocolAudit": {
                        "BoundaryTypes": {
                            "Inlet": "TYPE_E velocity profile",
                            "Outlet": "TYPE_E pressure/free-outflow approximation",
                            "Lateral": "TYPE_E slip/free approximation",
                            "Top": "TYPE_E",
                            "Ground": "TYPE_S no-slip; no rough-wall function",
                            "Buildings": "TYPE_S no-slip",
                        }
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--setup",
                str(setup),
                "--metadata",
                str(metadata),
                "--out",
                str(report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if completed.returncode == 0:
            raise AssertionError("Simplified boundary source should keep paper-grade gate failing.")
        if not report.exists():
            raise AssertionError("Boundary source audit report was not written.\n" + completed.stderr)

        data = json.loads(report.read_text(encoding="utf-8"))
        require(data.get("boundary_source_gate") == "pass", data)
        require(data.get("paper_grade_boundary_source_gate") == "fail", data)
        require(data.get("boundary_source_method_class") == "simplified_type_e_box", data)
        require(data.get("boundary_source_coherent") is True, data)
        require(data.get("boundary_source_simplified") is True, data)
        require(data.get("metadata_claims_advanced_boundary") is False, data)
        require(data.get("has_type_e_velocity_initialization") is True, data)
        require(data.get("has_profile_type_e_velocity_initialization") is True, data)

    print("boundary_source_audit_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
