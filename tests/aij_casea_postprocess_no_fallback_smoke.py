#!/usr/bin/env python3
"""Smoke-test that the legacy Case A postprocess does not zero-fill failed probes."""

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "src" / "Resources" / "Validation" / "AIJ_CaseA_PostProcess.py"


def require(text: str, expected: str) -> None:
    if expected not in text:
        raise AssertionError(f"Missing expected text: {expected}")


def require_absent(text: str, forbidden: str) -> None:
    if forbidden in text:
        raise AssertionError(f"Forbidden fallback remains: {forbidden}")


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    require_absent(source, "vx = 0.0")
    require(source, "failed_points += 1")
    require(source, '"SKIP"')
    require(source, "VALID POINTS")
    require(source, "FAILED POINTS")
    require(source, "Probe sampling failures are skipped, not replaced with zero velocity")
    print("aij_casea_postprocess_no_fallback_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
