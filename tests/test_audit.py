import subprocess
from pathlib import Path

import pytest
from tools.audit_publish import audit, run_audit, step_denylist, step_emails

NOREPLY = "1+tester@users.noreply.github.com"
ENV = {
    "GIT_AUTHOR_NAME": "tester",
    "GIT_AUTHOR_EMAIL": NOREPLY,
    "GIT_COMMITTER_NAME": "tester",
    "GIT_COMMITTER_EMAIL": NOREPLY,
}


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    import os

    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env={**os.environ, **ENV, **(env or {})},
    )


def _repo(tmp: Path, files: dict[str, str], commit: bool = True) -> Path:
    _git(tmp, "init", "-q", "-b", "main")
    for name, body in files.items():
        (tmp / name).write_text(body, encoding="utf-8")
    _git(tmp, "add", "-A")
    if commit:
        _git(tmp, "commit", "-q", "-m", "init")
    return tmp


def _denylist(tmp: Path, *terms: str) -> Path:
    path = tmp / "outside" / "denylist.txt"
    path.parent.mkdir()
    path.write_text("\n".join(terms) + "\n", encoding="utf-8")
    return path


def test_clean_repo_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "All data is simulated.", "a.yaml": "brands: [Voltrix]"})
    assert audit(repo) == []


def test_detects_secret_and_real_brand(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {"README.md": "simulated", "x.txt": "token ghp_" + "a" * 30, "b.yaml": "brands: [Samsung]"},
    )
    found = " ".join(audit(repo))
    assert "possible secret" in found
    assert "real brand" in found


def test_denylist_fails_on_planted_term_in_tracked_file(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated", "n.txt": "hello ZEBRAFISH-42 there"})
    deny = _denylist(tmp_path, "zebrafish-42")  # case-insensitive match
    result = step_denylist(repo, deny)
    assert result.status == "FAIL"
    text = " ".join(result.problems)
    assert "n.txt" in text
    assert "term #1" in text
    assert "zebrafish" not in text.lower()  # the term itself is never printed
    assert any(r.status == "FAIL" for r in run_audit(repo, deny))


def test_denylist_finds_term_only_present_in_history(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated", "n.txt": "secret-ish PLANTEDTERM here"})
    (repo / "n.txt").write_text("clean now", encoding="utf-8")
    _git(repo, "commit", "-qam", "scrub")
    deny = _denylist(tmp_path, "plantedterm")
    result = step_denylist(repo, deny)
    assert result.status == "FAIL"
    assert any("n.txt" in p and len(p.split(":")[0]) == 10 for p in result.problems)


def test_denylist_finds_term_on_other_branch(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated"})
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "z.txt").write_text("OtherBranchTerm", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "side")
    _git(repo, "checkout", "-q", "main")
    deny = _denylist(tmp_path, "otherbranchterm")
    assert step_denylist(repo, deny).status == "FAIL"


def test_denylist_passes_when_term_absent_and_skips_when_file_missing(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated"})
    assert step_denylist(repo, _denylist(tmp_path, "nothere")).status == "PASS"
    missing = step_denylist(repo, tmp_path / "nope.txt")
    assert missing.status == "SKIP"
    assert "WARNING" in missing.note
    assert step_denylist(repo, None, skip=True).status == "SKIP"


def test_email_check_flags_non_noreply_committer(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated"})
    assert step_emails(repo).status == "PASS"
    (repo / "q.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "bad", env={"GIT_COMMITTER_EMAIL": "real.person@example.com"})
    result = step_emails(repo)
    assert result.status == "FAIL"
    text = " ".join(result.problems) + result.note
    assert "committer" in text
    assert "real.person" not in text  # the address itself must never reach (public) logs
    assert "withheld" in text


@pytest.mark.parametrize(
    "email", ["noreply@github.com", "41898282+github-actions[bot]@users.noreply.github.com"]
)
def test_email_check_accepts_github_noreply_identities(tmp_path: Path, email: str) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _repo(repo, {"README.md": "simulated"})
    (repo / "q.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "ok", env={"GIT_COMMITTER_EMAIL": email})
    assert step_emails(repo).status == "PASS"
