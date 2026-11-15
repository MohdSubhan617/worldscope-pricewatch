import subprocess
from pathlib import Path

from tools.audit_publish import audit


def _repo(tmp: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    for name, body in files.items():
        (tmp / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    return tmp


def test_clean_repo_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"README.md": "All data is simulated.", "a.yaml": "brands: [Voltrix]"})
    assert audit(repo) == []


def test_detects_secret_and_real_brand(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path,
        {
            "README.md": "simulated",
            "x.txt": "token ghp_" + "a" * 30,
            "b.yaml": "brands: [Samsung]",
        },
    )
    found = " ".join(audit(repo))
    assert "possible secret" in found
    assert "real brand" in found
