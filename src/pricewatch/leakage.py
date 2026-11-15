"""Look-ahead (leakage) detector: truncation invariance.

A feature at day t must be identical whether or not prices after t exist. For each cutoff T we
rebuild features from prices truncated at T and compare every row with day <= T against the same
rows built from the full series. Any difference means a feature used information from after its
own day.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date

import numpy as np
import pandas as pd

Builder = Callable[[pd.DataFrame], pd.DataFrame]


def find_lookahead(
    builder: Builder, prices: pd.DataFrame, cutoffs: Sequence[date], columns: Sequence[str]
) -> list[str]:
    """Return a description for every (cutoff, column) whose past values changed."""
    full = builder(prices).set_index(["sku", "day"]).sort_index()
    problems: list[str] = []
    for cutoff in cutoffs:
        cut = builder(prices[prices["day"] <= cutoff]).set_index(["sku", "day"]).sort_index()
        past = full.loc[full.index.get_level_values("day") <= cutoff]
        past = past.loc[cut.index]
        for col in columns:
            a = past[col].to_numpy(dtype=float)
            b = cut[col].to_numpy(dtype=float)
            if not np.allclose(a, b, equal_nan=True, rtol=1e-9, atol=1e-12):
                bad = int((~np.isclose(a, b, equal_nan=True, rtol=1e-9, atol=1e-12)).sum())
                problems.append(
                    f"{col}: {bad} row(s) differ when prices after {cutoff} are removed"
                )
    return problems
