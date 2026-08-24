#!/usr/bin/env python3
"""Smoke-test strict native baseline manifest promotion gates."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CHAIN = REPO / "scripts" / "run_native_validation_chain.py"


def load_chain_module():
    spec = importlib.util.spec_from_file_location("run_native_validation_chain", CHAIN)
    if spec is None or spec.loader is None:
        raise AssertionError("failed to load run_native_validation_chain.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def source_record(role: str, path: Path) -> dict:
    return {
        "Role": role,
        "Path": str(path),
        "Exists": True,
        "HashAlgorithm": "SHA256",
        "Sha256": sha256_file(path),
    }


def create_source(root: Path) -> list[dict]:
    files = {
        "Native FluidX3D original setup": root / "src" / "setup.cpp",
        "Native FluidX3D original defines": root / "src" / "defines.hpp",
        "Native FluidX3D lbm.hpp": root / "src" / "lbm.hpp",
        "Native FluidX3D lbm.cpp": root / "src" / "lbm.cpp",
    }
    for role, path in files.items():
        write(path, f"// {role}\n")
    return [source_record(role, path) for role, path in files.items()]


def complete_manifest(required_files: list[dict]) -> dict:
    return {
        "BaselineId": "native-fluidx3d-casea-smoke",
        "NativeFluidX3DPathExplicitlyProvided": True,
        "NativeFluidX3DSourceValidation": {"IsValid": True},
        "PreExecutionGate": {"Gate": "pass"},
        "RunnerGate": {"Gate": "pass"},
        "Run": {"Requested": True, "Gate": "pass"},
        "ActualVtkOutputGate": {"Gate": "pass", "ActualFrameCount": 40},
        "RequiredSourceFiles": required_files,
    }


def assert_gate(module, manifest: dict, expected: str, manifest_path: Path) -> None:
    actual = module.native_baseline_gate_from_manifest(manifest, manifest_path)
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual}")


def main() -> int:
    module = load_chain_module()
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        manifest_path = temp / "native_fluidx3d_baseline_manifest.json"
        base = complete_manifest(create_source(source_root))

        assert_gate(module, base, "pass", manifest_path)

        dry = copy.deepcopy(base)
        dry["Run"]["Requested"] = False
        dry["Run"]["Gate"] = "not_requested"
        dry["ActualVtkOutputGate"]["Gate"] = "not_applicable"
        assert_gate(module, dry, "native_run_not_requested", manifest_path)

        blocked_preflight = copy.deepcopy(base)
        blocked_preflight["PreExecutionGate"]["Gate"] = "diagnostic_only"
        assert_gate(
            module,
            blocked_preflight,
            "native_pre_execution_gate_not_pass:diagnostic_only",
            manifest_path,
        )

        blocked_run = copy.deepcopy(base)
        blocked_run["Run"]["Gate"] = "blocked"
        assert_gate(module, blocked_run, "native_run_gate_not_pass:blocked", manifest_path)

        stale_or_short_vtk = copy.deepcopy(base)
        stale_or_short_vtk["ActualVtkOutputGate"]["Gate"] = "diagnostic_only"
        assert_gate(
            module,
            stale_or_short_vtk,
            "native_actual_vtk_output_gate_not_pass:diagnostic_only",
            manifest_path,
        )

        legacy_manifest = copy.deepcopy(base)
        legacy_manifest.pop("PreExecutionGate")
        assert_gate(module, legacy_manifest, "native_pre_execution_gate_missing", manifest_path)

    print("native_validation_chain_manifest_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
