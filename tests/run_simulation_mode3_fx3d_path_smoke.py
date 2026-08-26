#!/usr/bin/env python3
"""Static guard for controlled Mode 3 FluidX3D execution.

Mode 3 validation runs must not silently fall back to the old bundled solver.
The check is intentionally narrow: it only guards the Grasshopper component
dispatch and preflight text that controls the user-facing execution path.
"""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"


def extract_method(source: str, name: str) -> str:
    marker = f"private void {name}"
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"{name} method not found")

    brace = source.find("{", start)
    if brace < 0:
        raise AssertionError(f"{name} method body not found")

    depth = 0
    for index in range(brace, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    raise AssertionError(f"{name} method body is not balanced")


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8-sig")

    mode3_method = extract_method(source, "RunMode3_AsyncBackground")
    if "string.IsNullOrWhiteSpace(solver.FluidX3DPath)" not in mode3_method:
        raise AssertionError("Mode 3 must reject an empty FX3D path before starting a solver run")
    if 'RequireExplicitFluidX3DSourcePath(DA, solver, "Mode 3")' not in mode3_method:
        raise AssertionError("Mode 3 must validate an explicit native FluidX3D source path")
    if "solver.StartAsyncRun" not in mode3_method:
        raise AssertionError("Mode 3 async run call not found")
    if mode3_method.find("RequireExplicitFluidX3DSourcePath") > mode3_method.find("solver.StartAsyncRun"):
        raise AssertionError("Mode 3 path validation must happen before StartAsyncRun")

    switch_body = source[source.find("switch (mode)") : source.find("private void RunMode0_GenerateOnly")]
    if "case 3:" not in switch_body or "RunMode3_AsyncBackground" not in switch_body:
        raise AssertionError("Mode 3 must dispatch to the explicit-path async runner")
    if "case 3:" in switch_body and "RunMode3_BundledSolver" in switch_body:
        raise AssertionError("Mode 3 must not dispatch to the legacy bundled solver")

    if "[v0.5.0 Bundled]" in source:
        raise AssertionError("Run Simulation must not present v0.5.0 bundled solver as a v0.3.0 validation path")

    print("PASS run_simulation_mode3_fx3d_path_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
