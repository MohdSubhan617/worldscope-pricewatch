# Agent guide

- Read ENGINEERING_STANDARDS.md first. Update docs/PROGRESS.md as work lands.
- Run before committing: `python -m pytest`, `ruff check .`, `ruff format --check .`, `mypy`.
- Windows: use `.venv\Scripts\python.exe`. Refresh PATH before `gh`.
- Never commit data to `main`; never add real brands/prices; never add secrets.
