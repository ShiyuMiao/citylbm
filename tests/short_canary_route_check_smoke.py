#!/usr/bin/env python3
"""Smoke-test the fast short-canary route checker."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHECK = REPO / "scripts" / "check_short_canary_route.py"


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(REPO),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    codegen = run_command(
        [
            "dotnet",
            "run",
            "--project",
            str(REPO / "tests" / "CodegenSmoke" / "CodegenSmoke.csproj"),
            "-c",
            "Release",
        ]
    )
    if codegen.returncode != 0:
        raise AssertionError(codegen.stdout + "\n" + codegen.stderr)

    current_case = Path(tempfile.gettempdir()) / "CityLBM" / "stg_codegen_smoke"
    current_report = current_case / "short_canary_route_check.json"
    current = run_command([sys.executable, str(CHECK), "--case-dir", str(current_case), "--out", str(current_report)])
    if current.returncode != 0:
        raise AssertionError(current.stdout + "\n" + current.stderr)
    current_data = load_json(current_report)
    if current_data["Gate"] != "pass" or current_data["ShortDiagnosticCanaryAllowed"] is not True:
        raise AssertionError(json.dumps(current_data, indent=2))
    if current_data["InletSourceAudit"]["setup_inlet_codegen_route"] != "current_citylbm_stg_layerwise_type_e_route":
        raise AssertionError(json.dumps(current_data["InletSourceAudit"], indent=2))
    if current_data["ElapsedSeconds"] > 15:
        raise AssertionError(json.dumps(current_data, indent=2))

    with tempfile.TemporaryDirectory(prefix="citylbm_short_route_") as raw:
        legacy_case = Path(raw) / "legacy_case"
        (legacy_case / "src").mkdir(parents=True)
        (legacy_case / "src" / "setup.cpp").write_text(
            """
// legacy route fixture
float3 turbulentWind(uint x, uint y, uint z, uint t) { return float3(0.01f, 0.0f, 0.0f); }
void main_setup() {
    // CityLBM runtime inlet diagnostics patch
    LBM lbm(SX, SY, SZ, 0.01666667f);
}
""".lstrip(),
            encoding="utf-8",
        )
        (legacy_case / "src" / "defines.hpp").write_text("#define SX 32u\n#define SY 32u\n#define SZ 16u\n", encoding="utf-8")
        legacy_report = legacy_case / "short_canary_route_check.json"
        legacy = run_command([sys.executable, str(CHECK), "--case-dir", str(legacy_case), "--out", str(legacy_report)])
        if legacy.returncode != 2:
            raise AssertionError(legacy.stdout + "\n" + legacy.stderr)
        legacy_data = load_json(legacy_report)
        if legacy_data["Gate"] != "fail" or legacy_data["ShortDiagnosticCanaryAllowed"] is not False:
            raise AssertionError(json.dumps(legacy_data, indent=2))
        if not any(str(reason).startswith("setup_codegen_route_not_current_citylbm") for reason in legacy_data["Reasons"]):
            raise AssertionError(json.dumps(legacy_data, indent=2))

    print("short_canary_route_check_smoke passed")
    print(current_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
