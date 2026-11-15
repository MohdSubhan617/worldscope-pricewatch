# 001 - Brief was truncated; build from product, data and stack sections

Status: accepted

The task brief ended mid-list at build step 1: the Definition of Done and build steps 2-43 were
not delivered. Decision: treat the PRODUCT, DATA and STACK sections as the specification, derive
the remaining build order from them (simulator, features, model, calibration, export, site, CI,
Pages, release), and define "done" as: tests/ruff/mypy-strict green, site builds, `data` branch
publishes, Pages live, v0.1.0 tagged. Every deviation is recorded under docs/decisions/.
