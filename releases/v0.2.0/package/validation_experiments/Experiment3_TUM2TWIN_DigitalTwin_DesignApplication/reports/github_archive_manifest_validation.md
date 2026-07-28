# GitHub Archive Manifest Validation

evidence_type: newly_run

## Status

- Validation status: `passed`
- Manifest rows: `487`
- Missing files: `0`
- SHA256 mismatches: `0`
- LF-normalized text hashes: `338`
- Raw-byte hashes: `149`

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
