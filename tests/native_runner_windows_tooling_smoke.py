#!/usr/bin/env python3
"""Smoke-test Windows build-tool discovery and process failure reporting."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_native_fluidx3d_case", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import runner: {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    msbuild = runner.find_msbuild("")
    if sys.platform.startswith("win") and msbuild:
        path = Path(msbuild)
        if not path.is_file() or path.name.lower() != "msbuild.exe":
            raise AssertionError(msbuild)

    with tempfile.TemporaryDirectory(prefix="citylbm_missing_tool_") as raw:
        result = runner.run_process(["definitely_missing_citylbm_tool.exe"], Path(raw), 0)
        if result["Gate"] != "fail":
            raise AssertionError(result)
        if result["ReturnCode"] is not None:
            raise AssertionError(result)
        if "definitely_missing_citylbm_tool.exe" not in result["Stderr"]:
            raise AssertionError(result)

    with tempfile.TemporaryDirectory(prefix="citylbm_solver_cwd_inputs_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        source_root = temp / "source"
        solver_cwd = temp / "solver_cwd"
        case_dir.mkdir()
        source_root.mkdir()
        solver_cwd.mkdir()
        (case_dir / "buildings.stl").write_text("solid smoke\nendsolid smoke\n", encoding="utf-8")
        (case_dir / "case_metadata.json").write_text('{"AijCase":"CaseA"}\n', encoding="utf-8")
        records = runner.materialize_solver_workdir_inputs(case_dir, source_root, solver_cwd)
        roles = {record["Role"] for record in records}
        if "solver_cwd/buildings.stl" not in roles:
            raise AssertionError(records)
        if "solver_cwd/case_metadata.json" not in roles:
            raise AssertionError(records)
        if not (solver_cwd / "buildings.stl").is_file():
            raise AssertionError(records)

    with tempfile.TemporaryDirectory(prefix="citylbm_disable_graphics_") as raw:
        source_root = Path(raw)
        defines = source_root / "src" / "defines.hpp"
        defines.parent.mkdir(parents=True)
        defines.write_text(
            "#define GRAPHICS\n#define INTERACTIVE_GRAPHICS\n#define SX 16u\n",
            encoding="utf-8",
        )
        result = runner.disable_graphics_macros_for_run(source_root)
        updated = defines.read_text(encoding="utf-8")
        if result["Gate"] != "pass" or result["Modified"] is not True:
            raise AssertionError(result)
        enabled_macro_lines = [
            line for line in updated.splitlines()
            if line.strip() in {"#define GRAPHICS", "#define INTERACTIVE_GRAPHICS"}
        ]
        if enabled_macro_lines:
            raise AssertionError(updated)
        if set(result["DisabledMacros"]) != {"GRAPHICS", "INTERACTIVE_GRAPHICS"}:
            raise AssertionError(result)

    print("native_runner_windows_tooling_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
