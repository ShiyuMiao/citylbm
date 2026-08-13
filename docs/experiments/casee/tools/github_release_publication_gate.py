#!/usr/bin/env python3
"""Audit GitHub tag and Release publication state for the current Case E rc tag."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
RELEASE_BUNDLE = RESULTS_DIR / "casee_release_bundle_manifest.json"
OUT_JSON = RESULTS_DIR / "github_release_publication_gate.json"
OUT_CSV = RESULTS_DIR / "github_release_publication_gate.csv"
OUT_MD = RESULTS_DIR / "github_release_publication_gate.md"
OWNER = "ShiyuMiao"
REPO = "citylbm"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_git(args: list[str]) -> Dict[str, Any]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        encoding="utf-8",
        errors="replace",
    )
    return {"returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def latest_local_rc_tag(prefix: str) -> str:
    tags = run_git(["tag", "--list", f"{prefix}*"])
    numbers: list[tuple[int, str]] = []
    for tag in tags.get("stdout", "").splitlines():
        suffix = tag.strip()[len(prefix) :]
        if suffix.isdigit():
            numbers.append((int(suffix), tag.strip()))
    if not numbers:
        return ""
    return sorted(numbers)[-1][1]


def gh_status() -> Dict[str, Any]:
    exe = shutil.which("gh")
    if not exe:
        return {"gh_cli_available": False, "path": "", "auth_status_returncode": None, "auth_status": ""}
    proc = subprocess.run(
        [exe, "auth", "status"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "gh_cli_available": True,
        "path": exe,
        "auth_status_returncode": proc.returncode,
        "auth_status": (proc.stdout + proc.stderr).strip(),
    }


def github_get(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "citylbm-release-publication-gate"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            text = response.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": response.status, "json": json.loads(text), "error": ""}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "json": {}, "error": body[:500]}
    except Exception as exc:
        return {"ok": False, "status": None, "json": {}, "error": f"{type(exc).__name__}: {exc}"}


def remote_tag_status(tag: str) -> Dict[str, Any]:
    if not tag:
        return {"visible": False, "method": "", "returncode": None, "stdout": "", "stderr": ""}
    proc = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        encoding="utf-8",
        errors="replace",
    )
    stdout = proc.stdout.strip()
    return {
        "visible": bool(proc.returncode == 0 and f"refs/tags/{tag}" in stdout),
        "method": "git_ls_remote",
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": proc.stderr.strip(),
    }


def write_csv(payload: Dict[str, Any]) -> None:
    fields = [
        "recommended_tag",
        "audited_tag",
        "local_head",
        "local_tag_commit",
        "local_tag_resolves",
        "remote_tag_visible",
        "github_release_exists",
        "github_release_url",
        "gh_cli_available",
        "can_create_release_now",
        "formal_release_allowed",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow({key: payload.get(key, "") for key in fields})


def write_md(payload: Dict[str, Any]) -> None:
    lines = [
        "# GitHub Release Publication Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['github_release_publication_gate_passed']}",
        f"- Recommended tag: `{payload['recommended_tag']}`",
        f"- Audited tag: `{payload['audited_tag']}`",
        f"- Local audited tag resolves: {payload['local_tag_resolves']}",
        f"- Remote tag visible: {payload['remote_tag_visible']}",
        f"- GitHub Release exists: {payload['github_release_exists']}",
        f"- GitHub Release URL: `{payload['github_release_url']}`",
        f"- gh CLI available: {payload['gh_cli_available']}",
        f"- Can create release now: {payload['can_create_release_now']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    release_gate = read_json(RELEASE_GATE)
    bundle = read_json(RELEASE_BUNDLE)
    recommended_tag = str(release_gate.get("recommended_tag") or "")
    release_target = str(release_gate.get("release_target") or "v0.4.0")
    audited_tag = latest_local_rc_tag(f"{release_target}-rc") or recommended_tag
    head = run_git(["rev-parse", "HEAD"])
    tag_commit = (
        run_git(["rev-list", "-n", "1", audited_tag])
        if audited_tag
        else {"returncode": 1, "stdout": "", "stderr": "missing tag"}
    )
    gh = gh_status()
    tag_api = github_get(f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/{audited_tag}") if audited_tag else {}
    release_api = github_get(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{audited_tag}") if audited_tag else {}
    release_json = release_api.get("json") or {}
    release_exists = bool(release_api.get("ok") and release_json.get("html_url"))
    remote_fallback = remote_tag_status(audited_tag)
    remote_tag_visible_api = bool(tag_api.get("ok") and (tag_api.get("json") or {}).get("ref") == f"refs/tags/{audited_tag}")
    remote_tag_visible = bool(remote_tag_visible_api or remote_fallback.get("visible"))
    local_tag_resolves = bool(tag_commit.get("stdout"))
    gh_available = bool(gh.get("gh_cli_available"))
    gh_authed = bool(gh_available and gh.get("auth_status_returncode") == 0)
    bundle_ready = bool((bundle.get("summary") or {}).get("casee_release_bundle_gate_passed") is True)
    formal_allowed = bool(release_gate.get("formal_release_allowed"))
    can_create_release_now = bool(gh_available and gh_authed and bundle_ready and remote_tag_visible)
    gate_passed = bool(local_tag_resolves and remote_tag_visible and bundle_ready)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_github_tag; release_creation_blocked_or_absent",
        "github_release_publication_gate_passed": gate_passed,
        "recommended_tag": recommended_tag,
        "audited_tag": audited_tag,
        "local_head": head.get("stdout", ""),
        "local_tag_commit": tag_commit.get("stdout", ""),
        "local_tag_resolves": local_tag_resolves,
        "remote_tag_visible": remote_tag_visible,
        "remote_tag_visible_api": remote_tag_visible_api,
        "remote_tag_visible_fallback": remote_fallback.get("visible"),
        "remote_tag_fallback_method": remote_fallback.get("method"),
        "remote_tag_fallback_returncode": remote_fallback.get("returncode"),
        "remote_tag_fallback_stdout": remote_fallback.get("stdout", ""),
        "remote_tag_fallback_stderr": remote_fallback.get("stderr", ""),
        "remote_tag_api_status": tag_api.get("status"),
        "github_release_exists": release_exists,
        "github_release_url": release_json.get("html_url", ""),
        "github_release_api_status": release_api.get("status"),
        "gh_cli_available": gh_available,
        "gh_auth_ready": gh_authed,
        "can_create_release_now": can_create_release_now,
        "release_bundle_ready": bundle_ready,
        "release_bundle_path": (bundle.get("summary") or {}).get("bundle_path", ""),
        "release_bundle_sha256": (bundle.get("summary") or {}).get("bundle_sha256", ""),
        "formal_release_allowed": formal_allowed,
        "formal_accuracy_claim_supported": False,
        "tag_url": f"https://github.com/{OWNER}/{REPO}/tree/{audited_tag}" if audited_tag else "",
        "release_create_command": (
            f"gh release create {recommended_tag} --title \"CityLBM {recommended_tag}\" --notes-file docs/releases/{recommended_tag}.md "
            "docs/experiments/casee/results/casee_release_bundle.zip"
        )
        if recommended_tag
        else "",
        "boundary": (
            "This gate audits GitHub tag and Release publication state only. It does not create a GitHub "
            "Release, does not upload additional assets, does not run CFD, and does not support formal "
            "accuracy claims. A missing GitHub Release must not be described as a completed release."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(payload)
    write_md(payload)
    print(json.dumps({"github_release_publication_gate_passed": gate_passed, "release_exists": release_exists, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
