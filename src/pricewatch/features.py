"""Leakage-safe features and labels. Features at day t use only prices up to t."""

from __future__ import annotations

import numpy as np
import pandas as pd

DROP_THRESHOLD = 0.05  # a "drop" = price falls >=5% below today's price within the horizon

FEATURE_COLUMNS = [
    "ratio_max90",
    "ratio_min90",
    "ret_7",
    "vol_30",
    "promo_days_90",
    "days_since_promo",
    "age_days",
    "doy_sin",
    "doy_cos",
    "category_code",
]


def build_features(
    prices: pd.DataFrame, category_by_sku: dict[str, str], horizon: int
) -> pd.DataFrame:
    """Return one row per (sku, day) with features and the label (NaN if horizon unobserved)."""
    categories = sorted(set(category_by_sku.values()))
    code = {c: i for i, c in enumerate(categories)}
    parts: list[pd.DataFrame] = []
    for sku, grp in prices.sort_values("day").groupby("sku"):
        g = grp.reset_index(drop=True)
        p = g["price"].astype(float)
        base = p.rolling(90, min_periods=1).max()
        promo = (p < base * 0.95).astype(float)
        since = np.zeros(len(g))
        counter = 365.0
        for i, flag in enumerate(promo.to_numpy()):
            counter = 0.0 if flag else counter + 1
            since[i] = counter
        future_min = p[::-1].shift(1).rolling(horizon, min_periods=horizon).min()[::-1]
        days = pd.to_datetime(g["day"])
        doy = days.dt.dayofyear.to_numpy() / 365.25 * 2 * np.pi
        feat = pd.DataFrame(
            {
                "sku": sku,
                "day": g["day"],
                "price": p,
                "ratio_max90": p / base,
                "ratio_min90": p / p.rolling(90, min_periods=1).min(),
                "ret_7": p.pct_change(7).fillna(0.0),
                "vol_30": p.pct_change().rolling(30, min_periods=2).std().fillna(0.0),
                "promo_days_90": promo.rolling(90, min_periods=1).sum(),
                "days_since_promo": since,
                "age_days": np.arange(len(g), dtype=float),
                "doy_sin": np.sin(doy),
                "doy_cos": np.cos(doy),
                "category_code": float(code[category_by_sku[str(sku)]]),
                "label": (future_min < p * (1 - DROP_THRESHOLD))
                .astype(float)
                .where(future_min.notna()),
            }
        )
        parts.append(feat)
    return pd.concat(parts, ignore_index=True)
