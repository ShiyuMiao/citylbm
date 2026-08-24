#!/usr/bin/env python3
"""Smoke test for Type-E boundary velocity-initialization evidence."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "src" / "Core" / "FluidX3DInterface.cs").read_text(encoding="utf-8-sig")
    metrics = (repo / "scripts" / "validation_metrics_from_probe_audit.py").read_text(encoding="utf-8-sig")

    require(
        "AppendEquilibriumBoundaryVelocityInitialization(sb, scene.WindProfile, syntheticInletActive, windDir)" in source,
        "setup.cpp generation must call the Type-E velocity initialization pass",
    )
    require(
        "Synthetic turbulent inlet nodes keep the t=0 STG-lite velocity" in source
        and "float3 u_e = syntheticTurbulentInlet(x, y, z, 0u);" in source,
        "Type-E velocity initialization must not overwrite synthetic turbulent inlet nodes with the mean profile",
    )
    require(
        "lbm.flags.write_to_device();" in source and "lbm.u.write_to_device();" in source,
        "setup.cpp generation must write initialized flags and velocity to the device",
    )
    require(
        "BoundaryTypeEVelocityInitializationApplied = true" in source,
        "case metadata must record that Type-E velocity initialization is applied",
    )
    require(
        "BoundaryTypeEVelocityInitializationTreatment" in source,
        "case metadata must record how Type-E velocity initialization is applied",
    )
    require(
        "TYPE_E_inlet_preserves_synthetic_turbulent_velocity_t0" in source,
        "case metadata must record the synthetic-inlet-preserving initialization path",
    )
    require(
        "BoundaryVelocityInitializationPaperGradeStatus = \"diagnostic_damping_mitigation_not_wind_tunnel_equivalent_boundary\""
        in source,
        "metadata must not overstate Type-E velocity initialization as paper-grade boundary equivalence",
    )
    require(
        "BoundaryVelocityInitializationMethod = \"fixed_mean_velocity_equilibrium_for_all_TYPE_E_faces\"" in source,
        "metadata must identify fixed-mean Type-E boundary velocity initialization explicitly",
    )
    require(
        "BoundaryOutletTreatment = \"TYPE_E_fixed_mean_velocity_equilibrium_not_non_reflecting_or_validated_pressure_outlet\""
        in source,
        "metadata must identify the fixed-mean outlet treatment as non-paper-grade",
    )
    require(
        "BoundarySideTopTreatment = \"TYPE_E_fixed_mean_velocity_equilibrium_not_periodic_or_wind_tunnel_equivalent\""
        in source,
        "metadata must identify the side/top treatment as non wind-tunnel-equivalent",
    )
    require(
        "boundary_velocity_initialization_metadata_paper_grade_status" in metrics,
        "metrics output must preserve the metadata paper-grade status",
    )
    require(
        "boundary_velocity_initialization_metadata_device_upload_order" in metrics,
        "metrics output must preserve the device-upload ordering evidence",
    )

    print("boundary_velocity_initialization_metadata_smoke passed")
    return 0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
