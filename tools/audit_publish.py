"""Pre-publish audit: no secrets, no real brand names, simulated wording present."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]
REAL_BRANDS = [
    "apple",
    "samsung",
    "google",
    "sony",
    "bose",
    "dell",
    "lenovo",
    "microsoft",
    "huawei",
    "xiaomi",
    "oneplus",
    "garmin",
    "fitbit",
    "iphone",
    "galaxy",
    "pixel",
    "macbook",
    "ipad",
]
SKIP_FILES = {"audit_publish.py", "package-lock.json", "LICENSE"}


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [root / f for f in out]


def audit(root: Path) -> list[str]:
    problems: list[str] = []
    for path in tracked_files(root):
        if path.name in SKIP_FILES or path.name.startswith(".env"):
            if path.name.startswith(".env"):
                problems.append(f"{path.name}: env file is tracked")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                problems.append(f"{path.relative_to(root)}: possible secret ({pat.pattern[:24]})")
        if path.suffix in {".yaml", ".yml", ".json"} and path.parts[-3:-1] != ("workflows",):
            low = text.lower()
            for brand in REAL_BRANDS:
                if re.search(rf"\b{brand}\b", low):
                    problems.append(f"{path.relative_to(root)}: real brand name '{brand}'")
    readme = (root / "README.md").read_text(encoding="utf-8").lower()
    if "simulated" not in readme:
        problems.append("README.md: missing 'simulated' wording")
    return problems


if __name__ == "__main__":
    found = audit(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
    for p in found:
        sys.stderr.write(p + "\n")
    raise SystemExit(1 if found else 0)
