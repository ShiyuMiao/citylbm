#!/usr/bin/env python3
"""Smoke-test CustomProfile vs official AF fidelity audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_custom_profile_against_af.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_cmd(cmd: list[str], expected_returncode: int) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != expected_returncode:
        raise AssertionError((completed.returncode, completed.stdout, completed.stderr, cmd))
    return completed


def metadata(rows: list[dict]) -> str:
    return json.dumps(
        {
            "CustomProfileRows": len(rows),
            "CustomProfile": rows,
        },
        indent=2,
    )


def profile_row(z: float, u: float, k: float) -> dict:
    return {
        "ZM": z,
        "UMps": u,
        "KM2s2": k,
        "R11M2s2": k,
        "R22M2s2": 0.6 * k,
        "R33M2s2": 0.4 * k,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_custom_profile_af_") as raw:
        temp = Path(raw)
        af_csv = temp / "AF_caseA.csv"
        write(
            af_csv,
            (
                "z(m),U(m/s),u_rms(m/s),v_rms(m/s),w_rms(m/s),k(m2/s2)\n"
                "0.01,2.9,0.5,0.4,0.3,0.25\n"
                "0.02,3.1,0.55,0.42,0.31,0.28745\n"
                "0.04,3.4,0.6,0.45,0.33,0.3357\n"
                "0.08,3.8,0.65,0.48,0.35,0.38765\n"
                "0.12,4.2,0.7,0.5,0.36,0.4348\n"
                "0.16,4.5,0.72,0.52,0.38,0.4666\n"
            ),
        )

        good_metadata = temp / "good_metadata.json"
        write(
            good_metadata,
            metadata(
                [
                    profile_row(0.01, 2.9, 0.25),
                    profile_row(0.02, 3.1, 0.28745),
                    profile_row(0.04, 3.4, 0.3357),
                    profile_row(0.08, 3.8, 0.38765),
                    profile_row(0.12, 4.2, 0.4348),
                    profile_row(0.16, 4.5, 0.4666),
                ]
            ),
        )
        good_json = temp / "good.json"
        good_csv = temp / "good.csv"
        run_cmd(
            [
                sys.executable,
                str(SCRIPT),
                "--metadata",
                str(good_metadata),
                "--af-csv",
                str(af_csv),
                "--out-json",
                str(good_json),
                "--out-csv",
                str(good_csv),
                "--require-k",
            ],
            expected_returncode=0,
        )
        good = load(good_json)
        if good["Gate"] != "pass":
            raise AssertionError(good)
        if good["Metrics"]["KFromRijVsK"]["mae_ratio"] > 1.0e-12:
            raise AssertionError(good)
        if not good_csv.is_file():
            raise AssertionError("comparison CSV missing")

        bad_metadata = temp / "bad_metadata.json"
        write(
            bad_metadata,
            metadata(
                [
                    profile_row(0.01, 2.7, 0.12),
                    profile_row(0.08, 3.6, 0.18),
                    profile_row(0.16, 4.1, 0.20),
                ]
            ),
        )
        bad_json = temp / "bad.json"
        run_cmd(
            [
                sys.executable,
                str(SCRIPT),
                "--metadata",
                str(bad_metadata),
                "--af-csv",
                str(af_csv),
                "--out-json",
                str(bad_json),
                "--require-k",
            ],
            expected_returncode=2,
        )
        bad = load(bad_json)
        reasons = ";".join(bad["Reasons"])
        if bad["Gate"] != "fail":
            raise AssertionError(bad)
        if "custom_profile_rows_below_minimum" not in reasons:
            raise AssertionError(bad)
        if "k_mae_ratio_above_threshold" not in reasons:
            raise AssertionError(bad)

    return 0


if __name__ == "__main__":
    sys.exit(main())
