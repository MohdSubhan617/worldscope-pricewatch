"""Gradient-boosted classifier with isotonic calibration on a later time slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from pricewatch.features import FEATURE_COLUMNS

FloatArray = NDArray[np.float64]


@dataclass
class CalibratedModel:
    base: HistGradientBoostingClassifier
    calibrator: IsotonicRegression

    def predict_proba(self, frame: pd.DataFrame) -> FloatArray:
        raw = self.base.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
        return np.clip(np.asarray(self.calibrator.predict(raw), dtype=np.float64), 0.0, 1.0)


def brier(y: FloatArray, p: FloatArray) -> float:
    return float(np.mean((p - y) ** 2))


def reliability(y: FloatArray, p: FloatArray, bins: int = 10) -> list[dict[str, float]]:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    out: list[dict[str, float]] = []
    for b in range(bins):
        m = idx == b
        if m.any():
            out.append(
                {
                    "bin_low": float(edges[b]),
                    "bin_high": float(edges[b + 1]),
                    "mean_predicted": float(p[m].mean()),
                    "observed_rate": float(y[m].mean()),
                    "count": float(m.sum()),
                }
            )
    return out


def expected_calibration_error(rel: list[dict[str, float]]) -> float:
    total = sum(r["count"] for r in rel)
    if total == 0:
        return 0.0
    return float(
        sum(r["count"] * abs(r["mean_predicted"] - r["observed_rate"]) for r in rel) / total
    )


def split_by_time(
    labelled: pd.DataFrame, as_of: date, horizon: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train / calibration / test, separated by horizon-sized gaps to prevent label leakage."""
    usable_end = as_of - timedelta(days=horizon)
    days = pd.to_datetime(labelled["day"]).dt.date
    labelled = labelled[days <= usable_end]
    days = pd.to_datetime(labelled["day"]).dt.date
    span = (usable_end - days.min()).days
    t1 = usable_end - timedelta(days=int(span * 0.35))
    t2 = usable_end - timedelta(days=int(span * 0.15))
    gap = timedelta(days=horizon)
    train = labelled[days <= t1 - gap]
    cal = labelled[(days > t1) & (days <= t2 - gap)]
    test = labelled[days > t2]
    return train, cal, test


def fit(train: pd.DataFrame, cal: pd.DataFrame, seed: int) -> CalibratedModel:
    base = HistGradientBoostingClassifier(
        max_iter=150, learning_rate=0.06, max_depth=4, random_state=seed
    )
    base.fit(train[FEATURE_COLUMNS], train["label"].astype(int))
    raw = base.predict_proba(cal[FEATURE_COLUMNS])[:, 1]
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(raw, cal["label"].to_numpy(dtype=np.float64))
    return CalibratedModel(base=base, calibrator=iso)
