#!/usr/bin/env python3
"""Smoke test for geometry scale assumptions in validation metadata."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    source = (repo / "src" / "Core" / "FluidX3DInterface.cs").read_text(encoding="utf-8-sig")
    metrics = (repo / "scripts" / "validation_metrics_from_probe_audit.py").read_text(encoding="utf-8-sig")

    require(
        "GeometryPhysicalUnitAssumption" in source,
        "case metadata must record the physical-unit assumption for Rhino geometry",
    )
    require(
        "Rhino_model_geometry_is_already_real_scale_meters_before_case_generation" in source,
        "case metadata must state that CityLBM expects real-scale meter geometry",
    )
    require(
        "GeometryScaleEvidenceGate" in source,
        "case metadata must expose a geometry-scale evidence gate",
    )
    require(
        "AIJ_CaseE_official_BD_caseE_stl_is_1_to_250_model_scale_and_must_be_scaled_by_250_before_Add_Buildings"
        in source,
        "case metadata must preserve the AIJ Case E 1:250 STL scaling requirement",
    )
    for field in [
        "geometry_unit_assumption",
        "geometry_scale_evidence_gate",
        "geometry_scale_expected_casee_note",
        "geometry_building_height_m",
    ]:
        require(field in metrics, f"metrics template/writer must include {field}")

    print("geometry_scale_metadata_smoke passed")
    return 0


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
