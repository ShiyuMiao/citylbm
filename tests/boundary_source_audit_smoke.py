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
    const char* ui_label = "non_reflecting outlet periodic boundary rough_wall precursor recycling_rescaling";
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
    lbm.flags.write_to_device();
    lbm.u.write_to_device();
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
        require(data.get("boundary_source_fidelity_class") == "simplified_type_e_box", data)
        require(data.get("boundary_source_coherent") is True, data)
        require(data.get("boundary_source_simplified") is True, data)
        require(data.get("boundary_source_wind_tunnel_equivalent") is False, data)
        require(data.get("boundary_source_has_complete_wind_tunnel_evidence") is False, data)
        require(data.get("boundary_source_has_empty_advanced_method_stub_only") is False, data)
        require(data.get("metadata_claims_advanced_boundary") is False, data)
        require(data.get("has_type_e_velocity_initialization") is True, data)
        require(data.get("has_profile_type_e_velocity_initialization") is True, data)
        require(data.get("has_type_e_velocity_initialization_before_device_upload") is True, data)
        require(data.get("has_u_device_upload_after_type_e_velocity_initialization") is True, data)
        require(data.get("has_fixed_mean_type_e_boundary_velocity") is True, data)
        require(data.get("has_fixed_mean_outlet_lateral_top_treatment") is True, data)
        require(data.get("fixed_mean_outlet_lateral_top_treatment_gate") == "diagnostic_only", data)
        require(data.get("has_paper_grade_outlet_source") is False, data)
        require(data.get("has_paper_grade_side_top_source") is False, data)
        require(data.get("has_paper_grade_rough_wall_source") is False, data)
        require(data.get("has_paper_grade_development_source") is False, data)
        require(data.get("has_non_reflecting_outlet_token") is False, data)
        require(data.get("has_periodic_side_top_token") is False, data)
        require(data.get("has_rough_wall_function_token") is False, data)
        require(data.get("has_precursor_or_recycling_boundary_token") is False, data)
        require(data.get("advanced_boundary_token_only") is False, data)
        require(
            "non_reflecting_or_validated_outlet_state"
            in data.get("missing_paper_grade_source_evidence", []),
            data,
        )
        require(
            "outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary"
            in data.get("paper_grade_boundary_source_gate_reasons", []),
            data,
        )

        late_upload_setup = tmp_dir / "late_upload_setup.cpp"
        late_upload_report = tmp_dir / "late_upload_boundary_source_audit.json"
        late_upload_setup.write_text(
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
    lbm.flags.write_to_device();
    lbm.u.write_to_device();
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
        completed = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--setup",
                str(late_upload_setup),
                "--metadata",
                str(metadata),
                "--out",
                str(late_upload_report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode == 0:
            raise AssertionError("Type-E velocity initialization after device upload must fail source audit.")
        late_upload = json.loads(late_upload_report.read_text(encoding="utf-8"))
        require(late_upload.get("boundary_source_gate") == "fail", late_upload)
        require(late_upload.get("has_type_e_velocity_initialization") is True, late_upload)
        require(late_upload.get("has_type_e_velocity_initialization_before_device_upload") is False, late_upload)
        require(
            "type_e_boundary_velocity_initialization_not_uploaded_after_initialization"
            in late_upload.get("boundary_source_gate_reasons", []),
            late_upload,
        )

        advanced_setup = tmp_dir / "advanced_setup.cpp"
        advanced_report = tmp_dir / "advanced_boundary_source_audit.json"
        advanced_setup.write_text(
            """
void non_reflecting_outlet(float sponge_strength, float convective_speed) {}
void periodic_boundary(uint periodic_pair, uint wrap_index) {}
void rough_wall_function(float roughness_height, float friction_velocity) {}
void apply_rough_wall(float rough_wall_drag) {}
void precursor_boundary(float3 precursor_velocity, uint recycling_plane) {}
void main_setup() {
    parallel_for(lbm.get_N(), [&](ulong n) {
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);
        if(z == 0u) { lbm.flags[n] = TYPE_S; return; }
        if(y == Ny-1u) {
            lbm.flags[n] = TYPE_E;
            non_reflecting_outlet(sponge_strength, convective_speed);
            return;
        }
        if(x == 0u || x == Nx-1u || z == Nz-1u) {
            lbm.flags[n] = TYPE_E;
            periodic_boundary(periodic_pair, wrap_index);
            return;
        }
    });
    lbm.voxelize_stl(get_exe_path()+"../buildings.stl", TYPE_S);
    rough_wall_function(roughness_height, friction_velocity);
    apply_rough_wall(rough_wall_drag);
    precursor_boundary(precursor_velocity, recycling_plane);
}
""",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--setup",
                str(advanced_setup),
                "--metadata",
                str(metadata),
                "--out",
                str(advanced_report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode == 0:
            raise AssertionError("Empty advanced boundary stubs must not pass paper-grade source audit.")
        advanced = json.loads(advanced_report.read_text(encoding="utf-8"))
        require(advanced.get("paper_grade_boundary_source_gate") == "fail", advanced)
        require(advanced.get("boundary_source_method_class") == "advanced_boundary_empty_stub_only", advanced)
        require(advanced.get("boundary_source_fidelity_class") == "advanced_boundary_empty_stub_only", advanced)
        require(advanced.get("boundary_source_wind_tunnel_equivalent") is False, advanced)
        require(advanced.get("boundary_source_advanced_code_evidence") is False, advanced)
        require(advanced.get("boundary_source_has_complete_wind_tunnel_evidence") is False, advanced)
        require(advanced.get("boundary_source_has_empty_advanced_method_stub_only") is True, advanced)
        require(advanced.get("has_empty_advanced_boundary_method_stub") is True, advanced)
        require(advanced.get("empty_advanced_boundary_method_stub_count") == 5, advanced)
        require("advanced_boundary_method_empty_stub_definition" in advanced.get("boundary_source_gate_reasons", []), advanced)
        require(
            "advanced_boundary_method_empty_stub_definition"
            in advanced.get("paper_grade_boundary_source_gate_reasons", []),
            advanced,
        )

        advanced_defined_not_applied_setup = tmp_dir / "advanced_defined_not_applied_setup.cpp"
        advanced_defined_not_applied_report = tmp_dir / "advanced_defined_not_applied_boundary_source_audit.json"
        advanced_defined_not_applied_setup.write_text(
            """
float outlet_buffer[4] = {0.0f, 0.0f, 0.0f, 0.0f};
void non_reflecting_outlet(float sponge_strength, float convective_speed) {
    outlet_buffer[0] = sponge_strength * convective_speed;
}
uint periodic_boundary(uint periodic_pair, uint wrap_index) {
    return periodic_pair + wrap_index;
}
float rough_wall_function(float roughness_height, float friction_velocity) {
    float wall_function_shear = roughness_height * friction_velocity;
    return wall_function_shear;
}
float apply_rough_wall(float rough_wall_drag) {
    float wall_shear_force = rough_wall_drag;
    return wall_shear_force;
}
void precursor_boundary(float3 precursor_velocity, uint recycling_plane) {
    outlet_buffer[1] = precursor_velocity.y + (float)recycling_plane;
}
void main_setup() {
    parallel_for(lbm.get_N(), [&](ulong n) {
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);
        if(z == 0u) { lbm.flags[n] = TYPE_S; return; }
        if(y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }
        if(x == 0u || x == Nx-1u || z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }
    });
    lbm.voxelize_stl(get_exe_path()+"../buildings.stl", TYPE_S);
}
""",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--setup",
                str(advanced_defined_not_applied_setup),
                "--metadata",
                str(metadata),
                "--out",
                str(advanced_defined_not_applied_report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode == 0:
            raise AssertionError("Defined but unapplied advanced boundary methods unexpectedly passed.")
        unapplied = json.loads(advanced_defined_not_applied_report.read_text(encoding="utf-8"))
        require(unapplied.get("boundary_source_gate") == "fail", unapplied)
        require(unapplied.get("paper_grade_boundary_source_gate") == "fail", unapplied)
        require(unapplied.get("has_non_reflecting_outlet_application_evidence") is False, unapplied)
        require(unapplied.get("has_periodic_side_top_application_evidence") is False, unapplied)
        require(unapplied.get("has_rough_wall_application_evidence") is False, unapplied)
        require(unapplied.get("has_precursor_or_recycling_boundary_application_evidence") is False, unapplied)
        for reason in [
            "non_reflecting_boundary_source_missing_application_evidence",
            "periodic_boundary_source_missing_application_evidence",
            "rough_wall_boundary_source_missing_application_evidence",
            "precursor_recycling_boundary_source_missing_application_evidence",
        ]:
            require(reason in unapplied.get("boundary_source_gate_reasons", []), unapplied)

        advanced_real_setup = tmp_dir / "advanced_real_setup.cpp"
        advanced_real_report = tmp_dir / "advanced_real_boundary_source_audit.json"
        advanced_real_setup.write_text(
            """
float outlet_buffer[4] = {0.0f, 0.0f, 0.0f, 0.0f};
void non_reflecting_outlet(float sponge_strength, float convective_speed) {
    outlet_buffer[0] = sponge_strength * convective_speed;
}
uint periodic_boundary(uint periodic_pair, uint wrap_index) {
    return periodic_pair + wrap_index;
}
float rough_wall_function(float roughness_height, float friction_velocity) {
    float wall_function_shear = roughness_height * friction_velocity;
    return wall_function_shear;
}
float apply_rough_wall(float rough_wall_drag) {
    float wall_shear_force = rough_wall_drag;
    return wall_shear_force;
}
void precursor_boundary(float3 precursor_velocity, uint recycling_plane) {
    outlet_buffer[1] = precursor_velocity.y + (float)recycling_plane;
}
void main_setup() {
    parallel_for(lbm.get_N(), [&](ulong n) {
        uint x=0u, y=0u, z=0u;
        lbm.coordinates(n, x, y, z);
        if(z == 0u) { lbm.flags[n] = TYPE_S; return; }
        if(y == Ny-1u) {
            lbm.flags[n] = TYPE_E;
            non_reflecting_outlet(sponge_strength, convective_speed);
            return;
        }
        if(x == 0u || x == Nx-1u || z == Nz-1u) {
            lbm.flags[n] = TYPE_E;
            periodic_boundary(periodic_pair, wrap_index);
            return;
        }
    });
    lbm.voxelize_stl(get_exe_path()+"../buildings.stl", TYPE_S);
    rough_wall_function(roughness_height, friction_velocity);
    apply_rough_wall(rough_wall_drag);
    precursor_boundary(precursor_velocity, recycling_plane);
}
""",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--setup",
                str(advanced_real_setup),
                "--metadata",
                str(metadata),
                "--out",
                str(advanced_real_report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + "\n" + completed.stderr)
        advanced = json.loads(advanced_real_report.read_text(encoding="utf-8"))
        require(advanced.get("paper_grade_boundary_source_gate") == "pass", advanced)
        require(advanced.get("boundary_source_method_class") == "wind_tunnel_equivalent_boundary_source", advanced)
        require(advanced.get("boundary_source_fidelity_class") == "wind_tunnel_equivalent_complete", advanced)
        require(advanced.get("boundary_source_wind_tunnel_equivalent") is True, advanced)
        require(advanced.get("boundary_source_advanced_code_evidence") is True, advanced)
        require(advanced.get("boundary_source_has_complete_wind_tunnel_evidence") is True, advanced)
        require(advanced.get("boundary_source_has_empty_advanced_method_stub_only") is False, advanced)
        require(advanced.get("has_empty_advanced_boundary_method_stub") is False, advanced)
        require(advanced.get("empty_advanced_boundary_method_stub_count") == 0, advanced)
        require(advanced.get("has_non_reflecting_outlet_application_evidence") is True, advanced)
        require(advanced.get("has_periodic_side_top_application_evidence") is True, advanced)
        require(advanced.get("has_rough_wall_application_evidence") is True, advanced)
        require(advanced.get("has_precursor_or_recycling_boundary_application_evidence") is True, advanced)
        require(advanced.get("missing_paper_grade_source_evidence") == [], advanced)

    print("boundary_source_audit_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
