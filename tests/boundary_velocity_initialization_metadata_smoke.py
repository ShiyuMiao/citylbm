#!/usr/bin/env python3
"""Smoke test for Type-E boundary velocity-initialization evidence."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "src" / "Core" / "FluidX3DInterface.cs").read_text(encoding="utf-8-sig")
    metrics = (repo / "scripts" / "validation_metrics_from_probe_audit.py").read_text(encoding="utf-8-sig")

    require(
        "AppendEquilibriumBoundaryVelocityInitialization(sb, scene.WindProfile)" in source,
        "setup.cpp generation must call the Type-E velocity initialization pass",
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
        "BoundaryVelocityInitializationPaperGradeStatus = \"diagnostic_damping_mitigation_not_wind_tunnel_equivalent_boundary\""
        in source,
        "metadata must not overstate Type-E velocity initialization as paper-grade boundary equivalence",
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
