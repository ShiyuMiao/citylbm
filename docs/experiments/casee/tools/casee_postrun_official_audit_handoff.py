#!/usr/bin/env python3
"""Create a fail-closed handoff for newly completed Case E probe CSVs.

The handoff is deliberately conservative: it prepares the official z=2 m audit
path, records whether a candidate CSV is structurally admissible, and never
promotes a candidate to paper evidence without the release gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
RUNBOOK = RESULTS_DIR / "casee_next_experiment_runbook.json"
ORPHAN_AUDIT = RESULTS_DIR / "casee_orphan_candidate_csv_audit.json"
OUT_JSON = RESULTS_DIR / "casee_postrun_official_audit_handoff.json"
OUT_CSV = RESULTS_DIR / "casee_postrun_official_audit_handoff.csv"
OUT_MD = RESULTS_DIR / "casee_postrun_official_audit_handoff.md"

REQUIRED_COLUMNS = {"No.", "official_velocity_ratio", "predicted_velocity_ratio"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def git_tracked(path: Path) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode == 0


def git_status_code(path: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--short", "--", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        encoding="utf-8",
        errors="replace",
    )
    return proc.stdout[:2] if proc.stdout.strip() else "clean"


def candidate_csv_status(path: Path | None) -> Dict[str, Any]:
    if path is None:
        return {
            "candidate_supplied": False,
            "candidate_exists": False,
            "path": "",
            "sha256": "",
            "size_bytes": None,
            "git_tracked": False,
            "git_status_code": "",
            "row_count": 0,
            "columns": [],
            "required_columns_present": False,
            "probe_count_ok": False,
            "all_probe_ids_present": False,
            "numeric_values_ok": False,
        }
    p = path.resolve()
    if not p.exists():
        return {
            "candidate_supplied": True,
            "candidate_exists": False,
            "path": str(path),
            "sha256": "",
            "size_bytes": None,
            "git_tracked": False,
            "git_status_code": "",
            "row_count": 0,
            "columns": [],
            "required_columns_present": False,
            "probe_count_ok": False,
            "all_probe_ids_present": False,
            "numeric_values_ok": False,
        }
    rows = read_csv(p)
    columns = list(rows[0].keys()) if rows else []
    required_present = REQUIRED_COLUMNS.issubset(set(columns))
    probe_ids: List[int] = []
    numeric_ok = bool(rows) and required_present
    if required_present:
        for row in rows:
            try:
                probe_ids.append(int(float(row["No."])))
                float(row["official_velocity_ratio"])
                float(row["predicted_velocity_ratio"])
            except Exception:
                numeric_ok = False
                break
    expected_ids = set(range(1, 81))
    return {
        "candidate_supplied": True,
        "candidate_exists": True,
        "path": rel(p),
        "sha256": sha256(p),
        "size_bytes": p.stat().st_size,
        "git_tracked": git_tracked(p),
        "git_status_code": git_status_code(p),
        "row_count": len(rows),
        "columns": columns,
        "required_columns_present": required_present,
        "probe_count_ok": len(rows) == 80,
        "all_probe_ids_present": set(probe_ids) == expected_ids,
        "numeric_values_ok": numeric_ok,
    }


def manifest_status(candidate: Path | None) -> Dict[str, Any]:
    if candidate is None:
        return {
            "manifest_expected": False,
            "manifest_exists": False,
            "path": "",
            "protocol_fields_ok": False,
            "steps_ok": False,
            "spinup_ok": False,
            "manifest": {},
        }
    manifest_path = candidate.resolve().parent / "citylbm_native_case_manifest.json"
    manifest = read_json(manifest_path)
    return {
        "manifest_expected": True,
        "manifest_exists": manifest_path.exists(),
        "path": rel(manifest_path),
        "protocol_fields_ok": (
            manifest.get("validation_height_m") == 2.0
            and manifest.get("probe_count") == 80
            and manifest.get("formal_sampling_mode") == "raw_trilinear"
        ),
        "steps_ok": int(manifest.get("steps") or 0) >= 48000,
        "spinup_ok": int(manifest.get("spinup") or 0) >= 12000,
        "manifest": manifest,
    }


def log_status(candidate: Path | None, steps: int | None) -> Dict[str, Any]:
    if candidate is None:
        return {"log_expected": False, "log_count": 0, "logs": [], "complete_log_found": False}
    directory = candidate.resolve().parent
    logs = sorted(set(directory.glob("*.log")) | set(directory.glob("*run*.txt")) | set(directory.glob("*run*.log")))
    complete = False
    if steps:
        pattern = re.compile(rf"CaseE step\s+{int(steps)}\s*/\s*{int(steps)}")
        for log in logs:
            try:
                if pattern.search(log.read_text(encoding="utf-8", errors="replace")):
                    complete = True
                    break
            except OSError:
                continue
    return {
        "log_expected": True,
        "log_count": len(logs),
        "logs": [rel(item) for item in logs],
        "complete_log_found": complete,
    }


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    fields = ["item", "status", "evidence", "claim_boundary"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_md(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    candidate = payload["candidate_csv"]
    manifest = payload["manifest"]
    logs = payload["run_logs"]
    lines = [
        "# Case E Post-run Official Audit Handoff",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {summary['postrun_official_audit_handoff_passed']}",
        f"- Candidate supplied: {candidate['candidate_supplied']}",
        f"- Candidate structurally admissible: {summary['candidate_structurally_admissible']}",
        f"- Ready to run official audit: {summary['ready_to_run_official_audit']}",
        f"- Formal result allowed now: {summary['formal_result_allowed_now']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        "",
        "## Candidate",
        "",
        f"- Path: `{candidate['path']}`",
        f"- SHA256: `{candidate['sha256']}`",
        f"- Rows: {candidate['row_count']}",
        f"- Required columns present: {candidate['required_columns_present']}",
        f"- 80 official probe ids present: {candidate['all_probe_ids_present']}",
        "",
        "## Run Evidence",
        "",
        f"- Manifest: `{manifest['path']}`",
        f"- Protocol fields ok: {manifest['protocol_fields_ok']}",
        f"- Steps ok: {manifest['steps_ok']}",
        f"- Spinup ok: {manifest['spinup_ok']}",
        f"- Logs: {logs['log_count']}",
        f"- Complete log found: {logs['complete_log_found']}",
        "",
        "## Official Audit Command",
        "",
        "```powershell",
        summary["official_audit_command"],
        "```",
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--release-target", default="v0.4.0")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    candidate = candidate_csv_status(args.candidate)
    manifest = manifest_status(args.candidate)
    steps = None
    if manifest.get("manifest"):
        try:
            steps = int(manifest["manifest"].get("steps") or 0)
        except Exception:
            steps = None
    logs = log_status(args.candidate, steps)
    release_gate = read_json(RELEASE_GATE)
    runbook = read_json(RUNBOOK)
    orphan = read_json(ORPHAN_AUDIT)

    candidate_ok = bool(
        candidate["candidate_exists"]
        and candidate["required_columns_present"]
        and candidate["probe_count_ok"]
        and candidate["all_probe_ids_present"]
        and candidate["numeric_values_ok"]
        and manifest["manifest_exists"]
        and manifest["protocol_fields_ok"]
        and manifest["steps_ok"]
        and manifest["spinup_ok"]
        and logs["complete_log_found"]
    )
    audit_command = (
        "python docs/experiments/casee/tools/casee_audit.py "
        f"--release-target {args.release_target} --predicted "
        + ("<new_casee_probe_time_mean.csv>" if not candidate["candidate_exists"] else candidate["path"])
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "postrun_official_audit_handoff_passed": True,
        "candidate_structurally_admissible": candidate_ok,
        "ready_to_run_official_audit": candidate_ok,
        "official_audit_command": audit_command,
        "formal_result_allowed_now": False,
        "formal_accuracy_claim_supported": False,
        "release_gate_recommended_tag": release_gate.get("recommended_tag"),
        "release_gate_formal_allowed": release_gate.get("formal_release_allowed"),
        "runbook_postrun_policy_present": any(
            row.get("runbook_id") == "R009_postrun_official_audit"
            and "only" in str(row.get("formal_result_policy", "")).lower()
            for row in runbook.get("commands", [])
        ),
        "orphan_audit_candidate_count": (orphan.get("summary") or {}).get("candidate_csv_count"),
        "claim_readiness": "armed_no_candidate" if not candidate["candidate_supplied"] else (
            "ready_for_official_audit_only" if candidate_ok else "blocked_candidate_incomplete"
        ),
        "boundary": (
            "This handoff validates whether a newly completed Case E probe CSV is ready for the official "
            "z=2 m raw_trilinear audit command. It does not run FluidX3D, does not replace release_gate.json "
            "unless the audit command is explicitly executed, does not promote diagnostic columns, and does not "
            "support formal v0.4.0 or predictive-accuracy claims by itself."
        ),
    }
    rows = [
        {
            "item": "candidate_csv",
            "status": candidate["candidate_exists"],
            "evidence": candidate["path"],
            "claim_boundary": "Candidate presence only; not formal evidence.",
        },
        {
            "item": "candidate_structure",
            "status": candidate_ok,
            "evidence": f"rows={candidate['row_count']}; columns={';'.join(candidate['columns'])}",
            "claim_boundary": "Structural admissibility only; official audit still required.",
        },
        {
            "item": "official_audit_command",
            "status": bool(audit_command),
            "evidence": audit_command,
            "claim_boundary": "Only this command can update the formal release gate for a candidate CSV.",
        },
        {
            "item": "formal_result_allowed_now",
            "status": False,
            "evidence": "handoff_only",
            "claim_boundary": "No formal result is allowed from the handoff alone.",
        },
    ]
    payload = {
        "summary": summary,
        "candidate_csv": candidate,
        "manifest": manifest,
        "run_logs": logs,
        "source_artifacts": [rel(Path(__file__)), rel(RELEASE_GATE), rel(RUNBOOK), rel(ORPHAN_AUDIT)],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, payload)
    print(json.dumps({"postrun_official_audit_handoff_passed": True, "ready_to_run_official_audit": candidate_ok, "out_json": rel(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
