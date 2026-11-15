# 004 - Audit accepts GitHub noreply identities, not only the owner's address

Status: accepted

Step (d) requires every commit author and committer email to be a GitHub noreply address
(`<id>+<login>@users.noreply.github.com`, or `noreply@github.com` used by GitHub for web merges).
Daily data commits on the `data` branch are authored by `github-actions[bot]` with its noreply
address, so requiring the owner's single address would fail the audit by design. The audit prints
the distinct identities it saw so a reviewer can confirm them. Any non-noreply email fails.

Denylist terms are never echoed: hits are reported as `term #N` with commit and path only.
