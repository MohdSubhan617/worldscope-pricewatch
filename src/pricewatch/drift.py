"""Feature drift detection: Population Stability Index and two-sample Kolmogorov-Smirnov test."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import stats

FloatArray = NDArray[np.float64]

PSI_THRESHOLD = 0.25  # conventional "major shift" cut-off
KS_ALPHA = 0.01
KS_MIN_STAT = 0.10  # ignore statistically-significant but tiny shifts on large samples


@dataclass(frozen=True)
class DriftResult:
    column: str
    psi: float
    ks_stat: float
    ks_pvalue: float
    drifted: bool


def psi(reference: FloatArray, current: FloatArray, bins: int = 10) -> float:
    """PSI with reference-quantile bins; open-ended outer bins; epsilon-smoothed."""
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:  # (near-)constant reference
        return 0.0 if np.allclose(reference.mean(), current.mean()) else float("inf")
    edges[0], edges[-1] = -np.inf, np.inf
    ref = np.histogram(reference, edges)[0] / len(reference)
    cur = np.histogram(current, edges)[0] / len(current)
    eps = 1e-4
    ref, cur = np.clip(ref, eps, None), np.clip(cur, eps, None)
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def detect_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    columns: Sequence[str],
    psi_threshold: float = PSI_THRESHOLD,
    ks_alpha: float = KS_ALPHA,
    ks_min_stat: float = KS_MIN_STAT,
) -> list[DriftResult]:
    out: list[DriftResult] = []
    for col in columns:
        a = reference[col].to_numpy(dtype=np.float64)
        b = current[col].to_numpy(dtype=np.float64)
        ks = stats.ks_2samp(a, b)
        p = psi(a, b)
        drifted = p >= psi_threshold or (ks.pvalue < ks_alpha and ks.statistic >= ks_min_stat)
        out.append(DriftResult(col, p, float(ks.statistic), float(ks.pvalue), bool(drifted)))
    return out
