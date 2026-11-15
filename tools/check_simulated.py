"""Fail unless every JSON file under a directory is marked simulated."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def check(root: Path) -> list[str]:
    bad: list[str] = []
    for path in sorted(root.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("simulated") is not True:
            bad.append(str(path))
    return bad


if __name__ == "__main__":
    problems = check(Path(sys.argv[1]))
    for p in problems:
        sys.stderr.write(f"not marked simulated: {p}\n")
    raise SystemExit(1 if problems else 0)
