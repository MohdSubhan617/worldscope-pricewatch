"""Pre-publish audit.

Steps (each prints PASS / FAIL / SKIP):
  (a) secrets in tracked files
  (b) real brand names in tracked data files, and "simulated" wording in README
  (c) denylist: terms from a local-only file, case-insensitive, over tracked files AND the full
      history of every branch (contents, paths, commit messages, author/committer fields).
      Skipped with a warning if the file is absent or --skip-denylist is given.
      Matching terms are never printed, only "term #N" with the path and commit.
  (d) every commit author and committer email is a GitHub noreply address
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
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
NOREPLY = re.compile(r"^(?:[0-9]+\+)?[A-Za-z0-9._\[\]-]+@users\.noreply\.github\.com$")
GITHUB_WEB_NOREPLY = "noreply@github.com"  # committer used by GitHub for web merges
DEFAULT_DENYLIST = Path(".local") / "denylist.txt"


@dataclass
class StepResult:
    name: str
    status: str  # PASS | FAIL | SKIP
    problems: list[str] = field(default_factory=list)
    note: str = ""


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def tracked_files(root: Path) -> list[Path]:
    out = _git(root, "ls-files", "-z").split("\0")
    return [root / f for f in out if f]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def step_secrets(root: Path) -> StepResult:
    problems: list[str] = []
    for path in tracked_files(root):
        if path.name.startswith(".env"):
            problems.append(f"{path.name}: env file is tracked")
            continue
        text = None if path.name in SKIP_FILES else _read(path)
        if text is None:
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                problems.append(f"{path.relative_to(root)}: possible secret ({pat.pattern[:24]})")
    return StepResult("a: secrets", "FAIL" if problems else "PASS", problems)


def step_brands(root: Path) -> StepResult:
    problems: list[str] = []
    for path in tracked_files(root):
        if path.name in SKIP_FILES:
            continue
        in_workflows = path.parent.name == "workflows"
        if path.suffix not in {".yaml", ".yml", ".json"} or in_workflows:
            continue
        text = _read(path)
        if text is None:
            continue
        low = text.lower()
        for brand in REAL_BRANDS:
            if re.search(rf"\b{brand}\b", low):
                problems.append(f"{path.relative_to(root)}: real brand name '{brand}'")
    readme = _read(root / "README.md")
    if readme is None or "simulated" not in readme.lower():
        problems.append("README.md: missing 'simulated' wording")
    return StepResult("b: brands + simulated wording", "FAIL" if problems else "PASS", problems)


def load_terms(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").lstrip("﻿")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def _history_hits(root: Path, term: str, n: int) -> list[str]:
    """Locations in the full history of every branch where `term` occurs (never prints it)."""
    low = term.lower()
    hits: list[str] = []
    label = f"term #{n}"
    # commit messages and author/committer fields
    for flag in ("--grep", "--author", "--committer"):
        shas = _git(root, "log", "--all", "-i", "-F", f"{flag}={term}", "--format=%H").split()
        hits += [f"{s[:10]}: {label} in commit {flag[2:]}" for s in shas]
    # paths ever present
    seen: set[tuple[str, str]] = set()
    sha = ""
    for line in _git(root, "log", "--all", "--name-only", "--format=COMMIT %H").splitlines():
        if line.startswith("COMMIT "):
            sha = line[7:]
        elif line and low in line.lower() and (sha, line) not in seen:
            seen.add((sha, line))
            hits.append(f"{sha[:10]}: {label} in path {line}")
    # contents (pickaxe finds commits that add or remove an occurrence)
    shas = _git(root, "log", "--all", "-i", "-F", f"-S{term}", "--format=%H").split()
    for s in shas:
        files = _git(root, "diff-tree", "--root", "-r", "-m", "--no-commit-id", "--name-only", s)
        for name in files.split("\n"):
            if not name:
                continue
            for rev in (s, f"{s}^"):
                try:
                    body = _git(root, "show", f"{rev}:{name}")
                except subprocess.CalledProcessError:
                    continue
                if low in body.lower():
                    hits.append(f"{s[:10]}: {label} in content of {name}")
                    break
    return list(dict.fromkeys(hits))


def step_denylist(root: Path, denylist: Path | None, skip: bool = False) -> StepResult:
    name = "c: denylist (files + full history, all branches)"
    if skip:
        return StepResult(name, "SKIP", note="WARNING: skipped by --skip-denylist")
    path = denylist if denylist is not None else root / DEFAULT_DENYLIST
    if not path.is_file():
        return StepResult(name, "SKIP", note=f"WARNING: denylist file not found: {path}")
    terms = load_terms(path)
    if not terms:
        return StepResult(name, "SKIP", note=f"WARNING: denylist file has no terms: {path}")
    problems: list[str] = []
    for n, term in enumerate(terms, 1):
        low = term.lower()
        for f in tracked_files(root):
            text = _read(f)
            rel = f.relative_to(root)
            if low in str(rel).lower():
                problems.append(f"working tree: term #{n} in path {rel}")
            elif text is not None and low in text.lower():
                problems.append(f"working tree: term #{n} in content of {rel}")
        problems += _history_hits(root, term, n)
    return StepResult(
        name, "FAIL" if problems else "PASS", problems, note=f"{len(terms)} term(s) checked"
    )


def step_emails(root: Path) -> StepResult:
    problems: list[str] = []
    identities: set[str] = set()
    for line in _git(root, "log", "--all", "--format=%H|%ae|%ce").splitlines():
        sha, ae, ce = line.split("|")
        for role, email in (("author", ae), ("committer", ce)):
            identities.add(email)
            if not (NOREPLY.match(email) or email == GITHUB_WEB_NOREPLY):
                domain = email.rsplit("@", 1)[-1]
                problems.append(
                    f"{sha[:10]}: {role} email is not a noreply address "
                    f"(domain {domain}; address withheld from logs)"
                )
    # Only noreply identities are listed; anything else is counted, never printed (logs are public).
    shown = sorted(e for e in identities if NOREPLY.match(e) or e == GITHUB_WEB_NOREPLY)
    hidden = len(identities) - len(shown)
    note = "identities: " + ", ".join(shown) + (f" (+{hidden} withheld)" if hidden else "")
    return StepResult(
        "d: author/committer emails are noreply", "FAIL" if problems else "PASS", problems, note
    )


def run_audit(
    root: Path, denylist: Path | None = None, skip_denylist: bool = False
) -> list[StepResult]:
    return [
        step_secrets(root),
        step_brands(root),
        step_denylist(root, denylist, skip_denylist),
        step_emails(root),
    ]


def audit(root: Path) -> list[str]:
    """Flat list of problems from steps a and b (kept for simple callers and tests)."""
    return step_secrets(root).problems + step_brands(root).problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    ap.add_argument(
        "--denylist", type=Path, default=None, help="default: <root>/.local/denylist.txt"
    )
    ap.add_argument("--skip-denylist", action="store_true")
    args = ap.parse_args(argv)
    results = run_audit(args.root, args.denylist, args.skip_denylist)
    failed = False
    for r in results:
        sys.stdout.write(f"[{r.status}] {r.name}" + (f" - {r.note}" if r.note else "") + "\n")
        for p in r.problems:
            sys.stdout.write(f"    {p}\n")
        failed |= r.status == "FAIL"
    sys.stdout.write("AUDIT " + ("FAILED" if failed else "PASSED") + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
