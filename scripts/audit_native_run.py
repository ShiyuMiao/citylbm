#!/usr/bin/env python3
"""Create a machine-readable audit for a native FluidX3D validation run.

The script does not run CFD and does not judge AIJ accuracy. It inspects a run
directory after the solver has produced files and emits a JSON record that can
be passed to validation_metrics_from_probe_audit.py as --read-vtk-audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


RISK_PATTERNS = [
    ("nan", re.compile(r"\bnan\b", re.IGNORECASE)),
    ("inf", re.compile(r"\binf(?:inity)?\b", re.IGNORECASE)),
    ("diverg", re.compile(r"diverg", re.IGNORECASE)),
    ("unstable", re.compile(r"unstable", re.IGNORECASE)),
    ("instability", re.compile(r"instability", re.IGNORECASE)),
    ("blow up", re.compile(r"blow\s+up", re.IGNORECASE)),
    ("blow-up", re.compile(r"blow-up", re.IGNORECASE)),
    ("overflow", re.compile(r"overflow", re.IGNORECASE)),
    ("cuda error", re.compile(r"cuda\s+error", re.IGNORECASE)),
    ("opencl error", re.compile(r"opencl\s+error", re.IGNORECASE)),
    ("segmentation fault", re.compile(r"segmentation\s+fault", re.IGNORECASE)),
    ("exception", re.compile(r"exception", re.IGNORECASE)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit native FluidX3D VTK frames and solver log evidence."
    )
    parser.add_argument("run_dir", help="Native FluidX3D case/output directory.")
    parser.add_argument("--metadata", help="Optional case_metadata.json to copy stability settings from.")
    parser.add_argument("--solver-log", help="Optional solver stdout/stderr log path.")
    parser.add_argument("--out", required=True, help="Output audit JSON path.")
    parser.add_argument("--average-last-n", type=int, default=10)
    parser.add_argument("--min-avg-frames", type=int, default=10)
    parser.add_argument("--max-mean-speed-stddev-ratio", type=float, default=0.05)
    parser.add_argument("--max-point-speed-stddev-ratio", type=float, default=0.20)
    parser.add_argument("--mean-speed-mps", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-mps", type=float, default=None)
    parser.add_argument("--max-speed-stddev-mps", type=float, default=None)
    parser.add_argument("--mean-speed-stddev-ratio", type=float, default=None)
    parser.add_argument("--max-speed-stddev-ratio", type=float, default=None)
    return parser.parse_args()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def extract_time_step(path: Path) -> Optional[int]:
    matches = re.findall(r"\d+", path.stem)
    if not matches:
        return None
    return int(matches[-1])


def find_vtk_files(run_dir: Path) -> List[Path]:
    candidates = list(run_dir.glob("*.vtk"))
    output_dir = run_dir / "output"
    if output_dir.exists():
        candidates.extend(output_dir.glob("*.vtk"))
    unique = {str(path.resolve()).lower(): path for path in candidates}
    return sorted(unique.values(), key=lambda p: (extract_time_step(p) is None, extract_time_step(p) or 0, p.name))


def is_strictly_increasing(values: List[int]) -> bool:
    return bool(values) and all(values[i] > values[i - 1] for i in range(1, len(values)))


def has_uniform_spacing(values: List[int]) -> bool:
    if not values:
        return False
    if len(values) < 3:
        return True
    spacing = values[1] - values[0]
    return spacing > 0 and all(values[i] - values[i - 1] == spacing for i in range(2, len(values)))


def read_text_lossy(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def audit_solver_log(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {
            "solver_log_found": False,
            "solver_stability_warnings": "missing_solver_log",
            "lbm_stability_gate": "missing_solver_log",
            "solver_warning_matches": [],
        }
    text = read_text_lossy(path)
    matches = [label for label, pattern in RISK_PATTERNS if pattern.search(text)]
    return {
        "solver_log_found": True,
        "solver_log_path": str(path),
        "solver_log_sha256": sha256(path),
        "solver_stability_warnings": "none" if not matches else ";".join(matches),
        "lbm_stability_gate": "solver_log_no_stability_warnings" if not matches else "solver_log_stability_warnings",
        "solver_warning_matches": matches,
    }


def finite(value: Optional[float]) -> bool:
    return value is not None and not math.isnan(value) and not math.isinf(value)


def metadata_value(metadata: Dict[str, Any], key: str) -> Any:
    value = metadata.get(key)
    return "" if value is None else value


def build_audit(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir).resolve()
    metadata = read_json(Path(args.metadata).resolve() if args.metadata else None)
    vtk_files = find_vtk_files(run_dir)
    steps = [extract_time_step(path) for path in vtk_files]
    known_steps = sorted(step for step in steps if step is not None)
    selected_steps = known_steps[-args.average_last_n :] if args.average_last_n > 0 else []
    selected_last_window = bool(selected_steps) and selected_steps == known_steps[-len(selected_steps) :]
    increasing = is_strictly_increasing(selected_steps)
    uniform = has_uniform_spacing(selected_steps)

    reasons: List[str] = []
    if args.average_last_n <= 0:
        reasons.append("averaging_disabled")
    if len(selected_steps) < args.min_avg_frames:
        reasons.append(f"averaged_frame_count_below_{args.min_avg_frames}")
    if not selected_last_window:
        reasons.append("not_last_available_window")
    if not increasing:
        reasons.append("source_steps_not_strictly_increasing")
    if not uniform:
        reasons.append("source_step_spacing_not_uniform")
    if not finite(args.mean_speed_stddev_ratio):
        reasons.append("missing_mean_speed_stddev_ratio")
    elif args.mean_speed_stddev_ratio > args.max_mean_speed_stddev_ratio:
        reasons.append("mean_speed_stddev_ratio_above_0.05")
    if not finite(args.max_speed_stddev_ratio):
        reasons.append("missing_max_speed_stddev_ratio")
    elif args.max_speed_stddev_ratio > args.max_point_speed_stddev_ratio:
        reasons.append("max_speed_stddev_ratio_above_0.20")

    log_audit = audit_solver_log(Path(args.solver_log).resolve() if args.solver_log else None)
    audit: Dict[str, Any] = {
        "schema_version": 1,
        "component": "Native FluidX3D run audit",
        "run_dir": str(run_dir),
        "average_last_n_requested": args.average_last_n,
        "averaging_enabled": args.average_last_n > 0,
        "averaged_frame_count": len(selected_steps),
        "available_frame_count": len(known_steps),
        "all_available_time_steps": known_steps,
        "all_available_time_steps_csv": ",".join(str(step) for step in known_steps),
        "source_time_steps": selected_steps,
        "source_time_steps_csv": ",".join(str(step) for step in selected_steps),
        "source_first_time_step": selected_steps[0] if selected_steps else None,
        "source_last_time_step": selected_steps[-1] if selected_steps else None,
        "latest_available_time_step": known_steps[-1] if known_steps else None,
        "selected_last_window": selected_last_window,
        "source_steps_strictly_increasing": increasing,
        "source_step_spacing_uniform": uniform,
        "mean_speed_mps": args.mean_speed_mps,
        "mean_speed_stddev_mps": args.mean_speed_stddev_mps,
        "max_speed_stddev_mps": args.max_speed_stddev_mps,
        "mean_speed_stddev_ratio": args.mean_speed_stddev_ratio,
        "max_speed_stddev_ratio": args.max_speed_stddev_ratio,
        "minimum_validation_average_frames": args.min_avg_frames,
        "max_mean_speed_stddev_ratio": args.max_mean_speed_stddev_ratio,
        "max_point_speed_stddev_ratio": args.max_point_speed_stddev_ratio,
        "time_averaging_gate": "pass" if not reasons else "diagnostic_only",
        "time_averaging_gate_reasons": reasons,
        "time_averaging_gate_reasons_csv": ";".join(reasons),
        "vtk_files": [
            {
                "path": str(path),
                "time_step": extract_time_step(path),
                "sha256": sha256(path),
            }
            for path in vtk_files
        ],
        "target_max_profile_velocity_lbm": metadata_value(metadata, "TargetMaxProfileVelocityLbm"),
        "estimated_max_profile_mach": metadata_value(metadata, "EstimatedMaxProfileMach"),
        "lbm_tau": metadata_value(metadata, "LbmTau"),
        "lbm_nu": metadata_value(metadata, "LbmNu"),
        "physical_viscosity_m2s": metadata_value(metadata, "PhysicalViscosityM2s"),
        "estimated_reynolds_number": metadata_value(metadata, "EstimatedReynoldsNumber"),
        "velocity_set": metadata_value(metadata, "VelocitySet"),
        "les_model": metadata_value(metadata, "LesModel"),
        "smagorinsky_cs": metadata_value(metadata, "SmagorinskyCs"),
    }
    audit.update(log_audit)
    return audit


def main() -> int:
    args = parse_args()
    audit = build_audit(args)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote native run audit: {out_path}")
    print(
        "frames={}; selected={}; time_gate={}; lbm_stability_gate={}; solver_warnings={}".format(
            audit["available_frame_count"],
            audit["source_time_steps_csv"],
            audit["time_averaging_gate"],
            audit["lbm_stability_gate"],
            audit["solver_stability_warnings"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
