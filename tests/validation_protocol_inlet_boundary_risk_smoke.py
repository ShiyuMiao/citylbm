#!/usr/bin/env python3
"""Static guard for validation protocol risk classification."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src" / "Core" / "FluidX3DInterface.cs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_method(source: str, signature: str) -> str:
    start = source.find(signature)
    require(start >= 0, f"missing method signature: {signature}")
    next_method = source.find("\n        private ", start + len(signature))
    if next_method < 0:
        next_method = len(source)
    return source[start:next_method]


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    protocol = extract_method(
        source,
        "private IEnumerable<ValidationProtocolAuditItem> BuildValidationProtocolAuditItems",
    )

    require(
        'bool inletDistributionFunctionReconstruction = false;' in source,
        "metadata must not claim distribution-function reconstruction for current STG-lite inlet",
    )
    require(
        'PaperGradeTurbulentInletPrerequisiteGate = "fail"' in source,
        "case metadata must keep turbulent inlet paper-grade prerequisite failed",
    )
    require(
        'PaperGradeBoundaryPrerequisiteGate = "fail"' in source,
        "case metadata must keep simplified boundary paper-grade prerequisite failed",
    )
    require(
        'SyntheticTurbulentInletDistributionTreatment = syntheticActive' in source
        and "velocity_field_only_no_distribution_function_reconstruction" in source,
        "metadata must record current STG-lite as velocity-field-only without distribution reconstruction",
    )

    require(
        'Key = "inlet_distribution_consistency"' in protocol,
        "validation protocol must include inlet_distribution_consistency item",
    )
    require(
        'Status = "fail"' in protocol,
        "STG-lite inlet_distribution_consistency must be a formal validation blocker, not pass/risk",
    )
    require(
        "does not reconstruct FluidX3D distribution functions" in protocol,
        "inlet distribution evidence must state the missing distribution reconstruction",
    )
    require(
        "replace STG-lite with a validated DFM/SEM/precursor/recycling inlet" in protocol,
        "inlet distribution next action must require a distribution-consistent turbulent inlet for SCI-grade validation",
    )

    require(
        'Key = "boundary_conditions"' in protocol,
        "validation protocol must include boundary_conditions item",
    )
    require(
        'Status = "fail"' in protocol
        and "simplified TYPE_E boundary treatment" in protocol,
        "boundary_conditions must remain a formal validation blocker until AIJ-equivalent boundary evidence is archived",
    )
    require(
        'Key = "wall_roughness_model"' in protocol
        and 'Status = "fail"' in protocol,
        "wall roughness treatment must remain a formal validation blocker",
    )
    require(
        'Key = "inlet_temporal_sampling"' in protocol
        and 'expectedPaperAverageStgRefreshes >= PaperRecommendedStgRefreshes ? "partial" : "fail"' in protocol,
        "insufficient STG temporal sampling must be a formal validation blocker, not risk",
    )
    require(
        'Key = "time_averaging"' in protocol
        and 'expectedFrames >= PaperRecommendedAveragingFrames && expectedPaperAverageStepSpan >= PaperRecommendedAverageStepSpan ? "partial" : "fail"' in protocol,
        "short VTK time-averaging windows must be a formal validation blocker, not risk",
    )

    print("validation_protocol_inlet_boundary_risk_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
