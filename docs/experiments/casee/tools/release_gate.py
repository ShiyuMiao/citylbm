#!/usr/bin/env python3
"""Fail closed unless the Case E release gate allows the formal target release."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
GATE = ROOT / "docs" / "experiments" / "casee" / "results" / "release_gate.json"


def main() -> int:
    if not GATE.exists():
        print(f"Missing release gate: {GATE}")
        return 2
    data = json.loads(GATE.read_text(encoding="utf-8"))
    allowed = bool(data.get("formal_release_allowed", data.get("formal_v0_3_0_allowed")))
    print(f"release_target={data.get('release_target')}")
    print(f"formal_release_allowed={allowed}")
    print(f"recommended_tag={data.get('recommended_tag')}")
    if not allowed:
        print(data.get("blocking_reason", "Release gate failed."))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
