# Agent guide

- Read ENGINEERING_STANDARDS.md first. Update docs/PROGRESS.md as work lands.
- Run before committing: `python -m pytest`, `ruff check .`, `ruff format --check .`, `mypy`.
- Windows: use `.venv\Scripts\python.exe`. Refresh PATH before `gh`.
- Never commit data to `main`; never add real brands/prices; never add secrets.
- Enable the repo hook once per clone: `git config core.hooksPath .githooks`.
- Never add Co-Authored-By / Claude-Session trailers; never print the owner's private email.

