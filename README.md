# WorldScope PriceWatch

Calibrated probabilities that a **simulated** electronics item's price drops by at least 5%
within 14 days. Everything here is **simulated**: the catalogue is fictional (no real brands or
prices) and prices come from a seeded simulator whose parameters are documented assumptions, not
claims of calibration to real data. Not financial advice.

- Categories (YAML in `configs/categories/`): phones, laptops, earbuds/headphones, tablets,
  smartwatches.
- A virtual clock advances one simulated day per run, over 2 years of backfilled history.
- Model: scikit-learn `HistGradientBoostingClassifier` + isotonic calibration on a later time
  slice; metrics (Brier, ECE, reliability bins) are published in `metrics.json`.
- Static site (strict TypeScript, no runtime dependencies) on GitHub Pages. Data commits go to
  the orphan `data` branch, never `main`.

## Develop

```
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest
pricewatch run --out work/out        # advance one simulated day, export JSON
cd site && npm ci && npm test && npm run build
```

See `ENGINEERING_STANDARDS.md`, `AGENTS.md` and `docs/decisions/`.

License: Apache-2.0.
