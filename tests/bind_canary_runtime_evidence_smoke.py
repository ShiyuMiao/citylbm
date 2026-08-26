#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="citylbm_canary_bind_") as temp_dir:
        run_dir = Path(temp_dir)
        native = run_dir / "native_diagnostic_canary_manifest.json"
        diagnostics = run_dir / "runtime_inlet_diagnostics_csv_audit.json"
        correlation = run_dir / "inlet_correlation_audit.json"
        out = run_dir / "canary_runtime_evidence_manifest.json"

        native.write_text(
            json.dumps(
                {
                    "Run": {"Gate": "pass"},
                    "NativeAccuracyEvidenceGate": {
                        "Gate": "pass",
                        "RunGate": "pass",
                        "ActualVtkOutputGate": "pass",
                        "ActualFrameCount": 5,
                        "SelectedFinalWindowVtkSha256Count": 5,
                    },
                    "VtkFileCount": 5,
                    "VtkFiles": [
                        {"Path": f"u-{idx:09d}.vtk", "Exists": True, "Sha256": f"HASH{idx}"}
                        for idx in range(1, 6)
                    ],
                }
            ),
            encoding="utf-8",
        )
        diagnostics.write_text(
            json.dumps(
                {
                    "Gate": "pass",
                    "CsvPath": "stats.csv",
                    "CsvSha256": "CSVHASH",
                    "SelectedSteps": [300, 400, 500],
                    "Metrics": {"MaxMeanURelError": 0.01},
                }
            ),
            encoding="utf-8",
        )
        correlation.write_text(
            json.dumps(
                {
                    "inlet_correlation_gate": "pass",
                    "inlet_k_variance_gate": "pass",
                    "inlet_tke_gate": "pass",
                    "source_time_steps": [100, 200, 300, 400, 500],
                    "source_step_span": 400,
                    "temporal_lag1_mean_correlation": 0.8,
                    "spatial_adjacent_mean_correlation": 0.7,
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "bind_canary_runtime_evidence.py"),
                "--run-dir",
                str(run_dir),
                "--out",
                str(out),
            ],
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"binder failed: {completed.stdout}\n{completed.stderr}")
        data = json.loads(out.read_text(encoding="utf-8"))
        if data["Gate"] != "pass":
            raise AssertionError(data)
        if data["PaperUseGate"] != "fail":
            raise AssertionError(data)
        if data["NativeRun"]["SelectedFinalWindowVtkSha256Count"] != 5:
            raise AssertionError(data["NativeRun"])
        if data["InletCorrelation"]["TemporalLag1MeanCorrelation"] != 0.8:
            raise AssertionError(data["InletCorrelation"])
    print("bind_canary_runtime_evidence_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
