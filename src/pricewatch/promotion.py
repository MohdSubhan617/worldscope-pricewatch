"""Champion/challenger promotion policy.

The challenger is promoted only if the LOWER bound of a bootstrap confidence interval on the
Brier improvement (champion - challenger, positive = better) is at least `margin`. The bootstrap
resamples whole days (clusters), because rows on the same day are strongly dependent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    mean_improvement: float
    ci_low: float
    ci_high: float
    margin: float
    n_rows: int
    n_days: int
    reason: str


def decide_promotion(
    y: FloatArray,
    p_champion: FloatArray,
    p_challenger: FloatArray,
    groups: NDArray[np.int64],
    margin: float = 0.002,
    confidence: float = 0.95,
    n_boot: int = 2000,
    seed: int = 0,
) -> PromotionDecision:
    se_champ = (p_champion - y) ** 2
    se_chall = (p_challenger - y) ** 2
    uniq, inv = np.unique(groups, return_inverse=True)
    n_groups = len(uniq)
    diff_sum = np.bincount(inv, weights=se_champ - se_chall, minlength=n_groups)
    count = np.bincount(inv, minlength=n_groups).astype(np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_groups, size=(n_boot, n_groups))
    boot = diff_sum[idx].sum(axis=1) / count[idx].sum(axis=1)
    alpha = (1 - confidence) / 2
    lo, hi = (float(v) for v in np.quantile(boot, [alpha, 1 - alpha]))
    mean = float(diff_sum.sum() / count.sum())
    promote = lo >= margin
    if promote:
        reason = f"CI lower bound {lo:.5f} >= margin {margin}"
    elif mean > 0 and lo > 0:
        reason = f"better but not by the required margin (CI lower {lo:.5f} < {margin})"
    else:
        reason = f"no reliable improvement (CI [{lo:.5f}, {hi:.5f}] vs margin {margin})"
    return PromotionDecision(promote, mean, lo, hi, margin, len(y), n_groups, reason)
