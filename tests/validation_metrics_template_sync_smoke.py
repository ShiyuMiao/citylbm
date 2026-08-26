#!/usr/bin/env python3
"""Ensure the validation metrics CSV template matches the writer fields."""

from __future__ import annotations

import ast
import csv
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def template_fields_from_script() -> list[str]:
    source = (REPO / "scripts" / "validation_metrics_from_probe_audit.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "TEMPLATE_FIELDS":
                fields = ast.literal_eval(node.value)
                if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
                    raise AssertionError("TEMPLATE_FIELDS must be a list of strings.")
                return fields
    raise AssertionError("TEMPLATE_FIELDS was not found.")


def main() -> int:
    expected = template_fields_from_script()
    template_path = REPO / "docs" / "validation_metrics_template.csv"
    with template_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) != 1:
        raise AssertionError(f"Expected one header row in {template_path}, got {len(rows)} rows.")
    actual = rows[0]
    missing = [field for field in expected if field not in actual]
    extra = [field for field in actual if field not in expected]
    if missing or extra:
        raise AssertionError(f"Template mismatch. missing={missing}; extra={extra}")
    if actual != expected:
        raise AssertionError("Template fields match by set but not by order.")
    print("validation_metrics_template_sync_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
