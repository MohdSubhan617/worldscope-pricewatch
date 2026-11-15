# Engineering standards

- Python 3.11+, `mypy --strict`, `ruff check` and `ruff format --check` clean.
- Tests green at every commit; one logical change per Conventional Commit.
- Everything is SIMULATED: fictional catalogue, no real brands or prices. Every JSON file and
  page carries `"simulated": true` / visible "simulated" wording; a test enforces it.
- Deterministic: all randomness derives from the configured seed.
- No secrets, no external APIs, no API server. Static output only.
- Data commits go to the orphan `data` branch, never `main`.
- Simulator parameters are documented assumptions, not claims of calibration to real data.
- Decisions that deviate from or fill gaps in the brief go in `docs/decisions/NNN-title.md`.
- Commits carry no Co-Authored-By / Claude-Session trailers (`.claude/settings.json` blanks the
  attribution; `.githooks/commit-msg` rejects them; audit step (e) fails on them).
- Merge by local `git merge --ff-only <branch>` then `git push origin main`. Never use GitHub's
  "rebase and merge" or "squash" buttons: they stamp a non-noreply committer (decision 006).

