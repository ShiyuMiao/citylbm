#!/usr/bin/env python3
"""Smoke-test coordinate delta recomputation from the current official CSV."""

from __future__ import annotations

import importlib.util
import tempfile
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    module = load_gate_module()
    with tempfile.TemporaryDirectory(prefix="citylbm_coordinate_recompute_") as tmp:
        root = Path(tmp)
        official = root / "official.csv"
        probe = root / "probe_audit.csv"
        write_text(
            official,
            """No.,case,wind_direction,x,y,z,Velocity_Ratio
P1,ac,N,0,0,2,0.50
""",
        )
        write_text(
            probe,
            """probe_id,x,y,z,failed,validation_status,inside_vtk_grid_extent,normalization_valid,wind_direction_valid,Uref,wind_x,wind_y,wind_z,official_coordinate_delta
P1,9,0,2,false,pass,true,true,true,3.928296,0,-1,0,0
""",
        )

        status = module.read_probe_coordinate_normalization_audit(
            probe,
            expected_uref=3.928296,
            uref_tolerance=1.0e-6,
            expected_wind_vector=(0.0, -1.0, 0.0),
            wind_vector_tolerance=1.0e-6,
            official_path=official,
            case="ac",
            wind_direction="N",
        )
        if status["official_coordinate_error"] is not None:
            raise AssertionError(status)
        if status["official_coordinate_source"] != "current_official_csv_recomputed":
            raise AssertionError(status)
        if status["official_coordinate_recomputed_count"] != 1:
            raise AssertionError(status)
        if status["max_official_coordinate_delta_m"] != 9.0:
            raise AssertionError(status)
        if status["missing_official_coordinate_delta_count"] != 0:
            raise AssertionError(status)

    print("validation_gate_coordinate_recompute_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
