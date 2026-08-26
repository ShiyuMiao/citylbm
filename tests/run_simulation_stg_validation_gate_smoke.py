#!/usr/bin/env python3
"""Static guard for STG-lite validation preflight in Run Simulation."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"


def extract_method(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise AssertionError(f"{signature} not found")

    brace = source.find("{", start)
    if brace < 0:
        raise AssertionError(f"{signature} body not found")

    depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    raise AssertionError(f"{signature} body is not balanced")


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8-sig")
    validate = extract_method(source, "private bool ValidateRunWindow")
    length_gate = extract_method(source, "private static bool HasSupportedSyntheticTurbulenceLengthScaleSource")

    required_validation_tokens = [
        "syntheticRequestedForCustomTable",
        "completeK",
        "hasSupportedLengthScaleSource",
        "Mode 0 will generate a diagnostic case only: Synthetic Inlet is requested",
        "Mode 0 will generate a diagnostic STG-lite case only: STG Length Source",
        "Mode 0 will generate a diagnostic STG-lite case only: STG Modes",
        "validation run blocked: Synthetic Inlet is requested for a CustomTable profile",
        "validation run blocked: Synthetic Inlet is active, but STG Length Source",
        "validation run blocked: Synthetic Inlet is active but STG Modes",
        "Mode 0 may still be used for diagnostic case generation",
    ]
    for token in required_validation_tokens:
        if token not in validate:
            raise AssertionError(f"missing STG validation token: {token}")

    mode0_return = validate.find("return true;")
    first_block = validate.find("validation run blocked: Synthetic Inlet is requested for a CustomTable profile")
    if mode0_return < 0 or first_block < 0 or mode0_return > first_block:
        raise AssertionError("Mode 0 diagnostic warnings must remain non-blocking before Mode 1/2/3 validation blocks")

    for token in [
        "aij_length_scale_verified",
        "official_length_scale_verified",
        "precursor_length_scale",
        "recycling_length_scale",
        "digital_filter_length_scale",
        "synthetic_eddy_length_scale",
        "sem_length_scale",
        "dfm_length_scale",
        "validated_length_scale_model",
    ]:
        if token not in length_gate:
            raise AssertionError(f"missing accepted length-scale evidence token: {token}")

    print("PASS run_simulation_stg_validation_gate_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
