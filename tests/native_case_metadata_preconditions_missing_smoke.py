#!/usr/bin/env python3
"""Smoke-test strict missing-field case metadata preconditions for native runs."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_runner_module():
    path = REPO / "scripts" / "run_native_fluidx3d_case.py"
    spec = importlib.util.spec_from_file_location("run_native_fluidx3d_case", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, detail) -> None:
    if not condition:
        raise AssertionError(detail)


def main() -> int:
    module = load_runner_module()

    passing = module.audit_case_metadata_preconditions(
        {
            "PaperGradeTurbulentInletPrerequisiteGate": "ready_for_validation_run",
            "PaperGradeBoundaryPrerequisiteGate": "ready_for_validation_run",
            "SyntheticTurbulentInletInjected": False,
            "BoundaryNonReflectingOutletImplemented": True,
            "BoundarySideTopWindTunnelEquivalentImplemented": True,
            "BoundaryRoughWallFunctionImplemented": True,
            "BoundaryPrecursorOrRecyclingImplemented": True,
            "BoundaryBlockageFetchEvidenceArchived": True,
        }
    )
    require(passing["Gate"] == "pass", passing)

    incomplete = module.audit_case_metadata_preconditions(
        {
            "PaperGradeTurbulentInletPrerequisiteGate": "ready_for_validation_run",
            "BoundaryNonReflectingOutletImplemented": True,
        }
    )
    require(incomplete["Gate"] == "diagnostic_only", incomplete)
    for expected in [
        "case_metadata_paper_grade_boundary_prerequisite_missing",
        "case_metadata_synthetic_turbulent_inlet_injected_missing",
        "case_metadata_boundary_evidence_missing:side_top_wind_tunnel_equivalence",
        "case_metadata_boundary_evidence_missing:rough_wall_function",
        "case_metadata_boundary_evidence_missing:precursor_or_recycling",
        "case_metadata_boundary_evidence_missing:blockage_fetch_evidence",
    ]:
        require(expected in incomplete["Reasons"], incomplete["Reasons"])

    missing = module.audit_case_metadata_preconditions({})
    require(missing["Gate"] == "diagnostic_only", missing)
    for expected in [
        "case_metadata_paper_grade_turbulent_inlet_prerequisite_missing",
        "case_metadata_paper_grade_boundary_prerequisite_missing",
        "case_metadata_synthetic_turbulent_inlet_injected_missing",
        "case_metadata_boundary_evidence_missing:non_reflecting_outlet",
    ]:
        require(expected in missing["Reasons"], missing["Reasons"])

    synthetic_missing_reconstruction = module.audit_case_metadata_preconditions(
        {
            "PaperGradeTurbulentInletPrerequisiteGate": "ready_for_validation_run",
            "PaperGradeBoundaryPrerequisiteGate": "ready_for_validation_run",
            "SyntheticTurbulentInletInjected": True,
            "SyntheticTurbulentInletDistributionTreatment": "distribution_function_reconstructed",
            "BoundaryNonReflectingOutletImplemented": True,
            "BoundarySideTopWindTunnelEquivalentImplemented": True,
            "BoundaryRoughWallFunctionImplemented": True,
            "BoundaryPrecursorOrRecyclingImplemented": True,
            "BoundaryBlockageFetchEvidenceArchived": True,
        }
    )
    require(
        "case_metadata_synthetic_inlet_without_distribution_reconstruction"
        in synthetic_missing_reconstruction["Reasons"],
        synthetic_missing_reconstruction,
    )

    print("native_case_metadata_preconditions_missing_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
