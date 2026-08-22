#!/usr/bin/env python3
"""Smoke-test AF CSV Uref binding in the native validation chain."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_chain_module():
    path = REPO / "scripts" / "run_native_validation_chain.py"
    spec = importlib.util.spec_from_file_location("run_native_validation_chain", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    module = load_chain_module()
    with tempfile.TemporaryDirectory(prefix="citylbm_af_uref_") as tmp:
        root = Path(tmp)
        af_csv = root / "AF.csv"
        official = root / "RS.csv"
        metadata = root / "case_metadata.json"
        run_dir = root / "run"
        run_dir.mkdir()
        write_text(af_csv, "z(m),U(m/s),k(m2/s2)\n10,3.0,0.1\n20,5.0,0.2\n")
        write_text(official, "No.,x,y,z,Velocity_Ratio\nP1,0,0,2,1\n")
        write_text(metadata, "{}\n")

        value = module.af_u_at_reference_height(af_csv, 15.0)
        if abs(value - 4.0) > 1.0e-12:
            raise AssertionError(value)

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "run_native_validation_chain.py"),
                str(run_dir),
                "--official",
                str(official),
                "--af-csv",
                str(af_csv),
                "--metadata",
                str(metadata),
                "--case",
                "casea",
                "--wind-vector",
                "1,0,0",
                "--u-ref",
                "3.0",
                "--z-ref",
                "15.0",
                "--out-dir",
                str(root / "chain"),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode == 0:
            raise AssertionError("Expected mismatched Uref to fail before VTK auditing.")
        if "Uref does not match AF CSV interpolation" not in completed.stderr:
            raise AssertionError(completed.stderr)

    print("native_validation_chain_af_uref_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
