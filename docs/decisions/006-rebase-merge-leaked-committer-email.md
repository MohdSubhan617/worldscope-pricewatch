# 006 - Rebase-merge recorded a non-noreply committer email; history rewritten

Status: history rewritten and force-pushed; exposure NOT confirmed resolved (see below)

## What happened
GitHub's "rebase and merge" re-created four commits on `main` (PRs #1-#3) with the owner's
private email as committer. Authors were noreply. Audit step (d) caught it; the audit also
printed the address into public Actions logs, so eight runs were deleted (see the checklist).
Separately, commits carried Co-Authored-By / Claude-Session trailers, which made Claude appear in
the repository's contributors list.

## Fix (single rewrite, git-filter-repo, installed only in the project .venv)
- Every author, committer and tagger email on `main`, `data`, `v0.1.0` and `v0.1.1` was set to
  the owner's GitHub noreply address; no names, timestamps or trees were changed
  (per-commit tree hashes and `git diff` against the backup are identical).
- All Co-Authored-By and Claude-Session trailer lines were removed (case-insensitive).
- `main`, `data` and both tags were force-pushed by name (backup branches were not pushed).
- Releases v0.1.0 and v0.1.1 still exist, are not drafts, and point at the rewritten tags.
  The v0.1.1 release notes were regenerated because their short SHAs referred to old commits.
- The bot identity on `data` commits was also replaced by the owner's noreply email, as the
  task required ("wherever either is anything else"); names are unchanged.

## NOT resolved - do not treat as done
- Old commits may stay reachable by SHA, and through `refs/pull/*/head` and `refs/pull/*/merge`,
  until GitHub purges them. A force-push does not delete them from GitHub.
- The owner must ask GitHub Support to purge the old commits and the cached pull-request refs.
- The contributors list can take hours to refresh; it has not been observed to update.
- The local branches `backup-before-rewrite` and `backup-before-rewrite-data` contain the old
  commits (including the private email). They are local only, were never pushed, and should be
  deleted by the owner after confirming the result.
- Owner-side: enable "Keep my email addresses private" and "Block command line pushes that
  expose my email" in GitHub email settings.

## Preventing recurrence
- Merge only by local `git merge --ff-only <branch>` then `git push origin main`; GitHub's
  squash and rebase buttons are disabled in the repository settings.
- `.claude/settings.json` blanks commit/PR attribution; `.githooks/commit-msg` rejects
  trailers (enable with `git config core.hooksPath .githooks`); audit step (e) fails on any
  Co-Authored-By / Claude-Session trailer on any branch; audit step (d) never prints addresses.
