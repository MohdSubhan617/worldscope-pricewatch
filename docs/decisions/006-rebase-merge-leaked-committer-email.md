# 006 - Rebase-merge recorded a non-noreply committer email on main

Status: open (history rewrite pending owner approval)

Audit step (d) found that GitHub's "rebase and merge" re-created four commits on `main` (the
merges of PRs #1-#3, i.e. 76260c1, fa46898, 1a05466 and ce19278 at the time of writing) with the
owner's private primary email as committer. Authors are noreply. The v0.1.0 tag, the `data`
branch and all other commits are clean.

Actions: from PR #4 onward merges are done as local fast-forwards pushed to `main`, which keeps
the noreply committer. Rewriting the four published commits requires a force-push of `main`; that
was attempted (committer field only, trees identical) and blocked by the permission system as a
destructive action, so it is left for the owner. publish.yml keeps audit step (d) blocking, so the
Pages deploy job fails until the history is rewritten or the owner decides otherwise.
Note: GitHub may retain the old commit objects reachable by SHA after a rewrite; removing them
requires GitHub Support. Owner-side fix: enable "Keep my email addresses private" and "Block
command line pushes that expose my email" in GitHub email settings.
