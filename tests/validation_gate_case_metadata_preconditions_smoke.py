#!/usr/bin/env python3
"""Smoke-test case_metadata precondition gating in validation_gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_gate_module():
    path = REPO / "scripts" / "validation_gate.py"
    spec = importlib.util.spec_from_file_location("validation_gate", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pass_gate(module, key):
    return {
        "key": key,
        "status": module.PASS,
        "evidence": "smoke pass",
        "required_next_action": "none",
    }


def main() -> int:
    module = load_gate_module()

    passing = module.case_metadata_precondition_status(
        {
            "PaperGradeTurbulentInletPrerequisiteGate": "pass",
            "PaperGradeBoundaryPrerequisiteGate": "pass",
            "BoundaryConditionPaperGradeStatus": "paper_grade",
            "SyntheticTurbulentInletInjected": True,
            "InletDistributionFunctionReconstruction": True,
            "SyntheticTurbulentInletDistributionTreatment": "distribution_function_reconstructed",
            "BoundaryNonReflectingOutletImplemented": True,
            "BoundarySideTopWindTunnelEquivalentImplemented": True,
            "BoundaryRoughWallFunctionImplemented": True,
            "BoundaryPrecursorOrRecyclingImplemented": True,
            "BoundaryBlockageFetchEvidenceArchived": True,
        }
    )
    if not passing["ok"]:
        raise AssertionError(passing)

    diagnostic = module.case_metadata_precondition_status(
        {
            "PaperGradeTurbulentInletPrerequisiteGate": "fail",
            "PaperGradeBoundaryPrerequisiteGate": "fail",
            "BoundaryConditionPaperGradeStatus": "diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass",
            "SyntheticTurbulentInletInjected": True,
            "InletDistributionFunctionReconstruction": False,
            "SyntheticTurbulentInletDistributionTreatment": "velocity_field_only_no_distribution_function_reconstruction",
            "BoundaryNonReflectingOutletImplemented": False,
            "BoundarySideTopWindTunnelEquivalentImplemented": False,
            "BoundaryRoughWallFunctionImplemented": False,
            "BoundaryPrecursorOrRecyclingImplemented": False,
            "BoundaryBlockageFetchEvidenceArchived": False,
        }
    )
    if diagnostic["ok"]:
        raise AssertionError(diagnostic)
    for expected in [
        "paper_grade_turbulent_inlet_prerequisite_gate_not_pass:fail",
        "paper_grade_boundary_prerequisite_gate_not_pass:fail",
        "boundary_condition_paper_grade_status_not_pass:diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass",
        "synthetic_inlet_distribution_function_reconstruction_not_true:False",
        "synthetic_inlet_distribution_treatment_not_paper_grade:velocity_field_only_no_distribution_function_reconstruction",
        "BoundaryNonReflectingOutletImplemented_false",
        "BoundarySideTopWindTunnelEquivalentImplemented_false",
        "BoundaryRoughWallFunctionImplemented_false",
        "BoundaryPrecursorOrRecyclingImplemented_false",
        "BoundaryBlockageFetchEvidenceArchived_false",
    ]:
        if expected not in diagnostic["reasons"]:
            raise AssertionError(diagnostic["reasons"])

    missing = module.case_metadata_precondition_status({})
    if missing["ok"] or "case_metadata_missing" not in missing["reasons"]:
        raise AssertionError(missing)

    gates = [
        pass_gate(module, "validation_protocol_content"),
        {
            "key": "case_metadata_preconditions",
            "status": module.FAIL,
            "evidence": diagnostic["reasons_csv"],
            "required_next_action": "Regenerate metadata.",
        },
    ]
    priorities = module.build_diagnostic_priority(gates, {})
    metadata_priority = next(
        item for item in priorities if item["key"] == "case_metadata_preconditions"
    )
    if metadata_priority["rank"] != 0:
        raise AssertionError(metadata_priority)
    if metadata_priority["gate_status"] != module.FAIL:
        raise AssertionError(metadata_priority)
    if "paper-grade inlet distribution reconstruction" not in metadata_priority["next_action"]:
        raise AssertionError(metadata_priority)

    print("validation_gate_case_metadata_preconditions_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
