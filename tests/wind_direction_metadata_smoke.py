#!/usr/bin/env python3
"""Smoke-test wind-direction identity fields in validation metadata."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src" / "Core" / "FluidX3DInterface.cs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8-sig")
    require(
        "GetWindFromDirectionLabel(scene.WindDirection)" in source,
        "case metadata must record an AIJ/meteorological from-direction label",
    )
    require(
        "GetWindFlowDirectionLabel(scene.WindDirection)" in source,
        "case metadata must record the actual Rhino-world flow-direction label",
    )
    require(
        "N wind uses vector (0,-1,0)" in source,
        "metadata must document the N-wind vector convention used for AIJ validation",
    )
    require(
        'string ns = dir.Y < -eps ? "N" : dir.Y > eps ? "S" : "";' in source,
        "from-direction mapping must classify vector (0,-1,0) as N",
    )
    require(
        'string ns = dir.Y < -eps ? "S" : dir.Y > eps ? "N" : "";' in source,
        "flow-direction mapping must classify vector (0,-1,0) as flow toward S",
    )
    print("wind_direction_metadata_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
