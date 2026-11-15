# 007 - Leakage test is truncation invariance, proven on a deliberate leak

Status: accepted

`pricewatch.leakage.find_lookahead` rebuilds features from prices truncated at several cutoffs and
requires every row at or before the cutoff to equal the same row built from the full series.

Proof it fails on a leak (captured 2026-11-14): a feature `leak_next_ratio = price[t+1]/price[t]`
was temporarily added to `FEATURE_COLUMNS` and the feature builder. Output:

```
>       assert find_lookahead(builder, prices, CUTOFFS, FEATURE_COLUMNS) == []
E       AssertionError: assert ['leak_next_r... are removed'] == []
E         Left contains 3 more items, first extra item: 'leak_next_ratio: 8 row(s) differ when prices after 2025-05-20 are removed'
FAILED tests/test_leakage.py::test_real_features_have_no_lookahead - Assertio...
1 failed in 2.03s
```

The leak was then removed (`git checkout -- src/pricewatch/features.py`; 0 occurrences) and the
suite passes. A permanent test (`test_detector_catches_a_deliberately_leaky_feature`) injects the
same kind of leak through a wrapper builder and asserts it is flagged, and only that column.
Limits: the check catches use of future prices; it does not catch leakage through labels or
splits (covered separately by the purge/embargo split tests).
