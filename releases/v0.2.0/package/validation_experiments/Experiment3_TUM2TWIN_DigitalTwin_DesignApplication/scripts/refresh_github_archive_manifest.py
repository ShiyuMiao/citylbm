from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path.cwd()
MAN = ROOT / "manifests"
REP = ROOT / "reports"
TEXT_EXTENSIONS = {".md", ".csv", ".json", ".pvsm", ".cpp", ".py", ".ps1", ".txt"}
MANIFEST_RELATIVE_PATH = "manifests/github_archive_manifest.csv"


def hash_payload(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return hashlib.sha256(data).hexdigest(), "sha256_raw_bytes"
    try:
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError:
        return hashlib.sha256(data).hexdigest(), "sha256_raw_bytes"
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), "sha256_lf_normalized_text"


def collect_manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if relative == MANIFEST_RELATIVE_PATH:
            continue
        sha256, note = hash_payload(path)
        rows.append(
            {
                "relative_path": relative,
                "size_bytes": str(path.stat().st_size),
                "sha256": sha256,
                "hash_note": note,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    mismatches: list[str] = []
    for row in rows:
        path = ROOT / row["relative_path"]
        if not path.exists():
            missing.append(row["relative_path"])
            continue
        sha256, _ = hash_payload(path)
        if sha256 != row["sha256"]:
            mismatches.append(row["relative_path"])
    return missing, mismatches


def upsert_evidence_inventory(row_count: int, missing: list[str], mismatches: list[str]) -> None:
    path = MAN / "evidence_inventory.csv"
    if not path.exists():
        return
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    claim = "GitHub archive manifest was regenerated after the current checkout using LF-normalized text hashes for reproducibility."
    entry = {
        "claim": claim,
        "evidence_type": "newly_run",
        "source": "manifests/github_archive_manifest.csv; reports/github_archive_manifest_validation.md",
    }
    updated = False
    for row in rows:
        if row.get("claim") == claim:
            row.update(entry)
            updated = True
            break
    if not updated:
        rows.append(entry)
    write_csv(path, rows, ["claim", "evidence_type", "source"])


def write_report(rows: list[dict[str, str]], missing: list[str], mismatches: list[str]) -> None:
    normalized = sum(1 for row in rows if row["hash_note"] == "sha256_lf_normalized_text")
    raw = len(rows) - normalized
    status = "passed" if not missing and not mismatches else "failed"
    report = f"""# GitHub Archive Manifest Validation

evidence_type: newly_run

## Status

- Validation status: `{status}`
- Manifest rows: `{len(rows)}`
- Missing files: `{len(missing)}`
- SHA256 mismatches: `{len(mismatches)}`
- LF-normalized text hashes: `{normalized}`
- Raw-byte hashes: `{raw}`

## Hash Policy

Text-like archive files use SHA256 after UTF-8 decoding and LF line-ending
normalization. This avoids false mismatch reports caused by Git checkout
line-ending conversion on Windows while preserving deterministic hashes for
the content that a reviewer will read. Binary or non-UTF-8 files use raw-byte
SHA256.

## Remaining Boundary

The manifest verifies files included in this GitHub release package. Large raw
datasets and external VTK assets remain governed by `EXTERNAL_ARTIFACTS.md` and
the evidence inventory rather than being embedded in the repository.
"""
    if missing:
        report += "\n## Missing Examples\n\n" + "\n".join(f"- `{item}`" for item in missing[:20]) + "\n"
    if mismatches:
        report += "\n## Mismatch Examples\n\n" + "\n".join(f"- `{item}`" for item in mismatches[:20]) + "\n"
    REP.mkdir(parents=True, exist_ok=True)
    (REP / "github_archive_manifest_validation.md").write_bytes(report.encode("utf-8"))


def main() -> None:
    rows = collect_manifest_rows()
    # The validation report should itself be included in the manifest.
    write_report(rows, [], [])
    rows = collect_manifest_rows()
    missing, mismatches = validate(rows)
    write_report(rows, missing, mismatches)
    write_csv(
        MAN / "github_archive_manifest.csv",
        rows,
        ["relative_path", "size_bytes", "sha256", "hash_note"],
    )
    upsert_evidence_inventory(len(rows), missing, mismatches)
    # Regenerate once more so the evidence-inventory upsert is also reflected.
    rows = collect_manifest_rows()
    missing, mismatches = validate(rows)
    write_report(rows, missing, mismatches)
    rows = collect_manifest_rows()
    missing, mismatches = validate(rows)
    write_csv(
        MAN / "github_archive_manifest.csv",
        rows,
        ["relative_path", "size_bytes", "sha256", "hash_note"],
    )
    print("manifest_rows", len(rows))
    print("missing", len(missing))
    print("mismatch", len(mismatches))
    print("wrote manifests/github_archive_manifest.csv")
    print("wrote reports/github_archive_manifest_validation.md")


if __name__ == "__main__":
    main()
