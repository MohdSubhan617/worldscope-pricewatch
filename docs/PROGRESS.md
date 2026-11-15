# Progress

| Step | Status |
|------|--------|
| Scaffold, tooling, CI, standards, schemas, settings, 5 category configs | done |
| Simulator + virtual clock | done |
| Features, gradient boosting, isotonic calibration | done |
| Pipeline, CLI, JSON export, simulated-marker check | done |
| Static TypeScript site | done |
| publish workflow (data branch + Pages), LICENSE, audit tool | done |
| GitHub repo, push, audit, public, Pages, first workflow run, v0.1.0 | done |

The brief was truncated after step 1 (decisions/001), so the ~43-commit plan was condensed into
fewer, larger commits.

Known limitation: see decisions/003 (calibrated, but no skill over base rate on published run).
Live: https://mohdsubhan617.github.io/worldscope-pricewatch/

## v0.1.1 (2026-11-14)
| Item | Status |
|------|--------|
| 1 Planted effects + recovery test (margin 0.25) | done, verified |
| 2 Rolling-origin backtest + BENCHMARKS.md | done, verified |
| 3 Leakage test proven on a deliberate leak | done, verified |
| 4 Drift (PSI/KS), promotion policy, weekly-retrain.yml | done, verified (workflow run on GitHub) |
| 5 Daily digest comment + failure-only notification | done, verified live |
| 6 Playwright + axe in CI | done, verified local + CI |
| 7 Audit denylist + history + emails; test | done; step (d) FAILS on 4 leaked commits, see decisions/006 |
| 8 RELEASE_CHECKLIST.md, v0.1.1 | done; see checklist for open items |

