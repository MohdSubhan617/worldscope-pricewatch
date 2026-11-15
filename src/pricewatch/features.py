"""Leakage-safe features and labels. Features at day t use only prices up to t."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pricewatch.domain import CategoryConfig, Product, SaleEvent
from pricewatch.sales import days_to_next_sale, in_sale

DROP_THRESHOLD = 0.05  # a "drop" = price falls >=5% below today's price within the horizon

FEATURE_COLUMNS = [
    "ratio_max90",
    "ratio_min90",
    "ret_7",
    "vol_30",
    "promo_days_90",
    "days_since_promo",
    "age_days",
    "cycle_frac",
    "days_to_next_sale",
    "in_sale",
    "doy_sin",
    "doy_cos",
    "category_code",
]


def build_features(
    prices: pd.DataFrame,
    products: list[Product],
    configs: list[CategoryConfig],
    events: tuple[SaleEvent, ...],
    horizon: int,
) -> pd.DataFrame:
    """Return one row per (sku, day) with features and the label (NaN if horizon unobserved).

    Every feature at day t uses only prices up to t, the public sale calendar and product
    metadata known at launch (launch date, category refresh cycle).
    """
    category_by_sku = {p.sku: p.category for p in products}
    launch_by_sku = {p.sku: p.launch_date for p in products}
    cycle_by_cat = {c.id: c.refresh_cycle_days for c in configs}
    categories = sorted({c.id for c in configs})
    code = {c: i for i, c in enumerate(categories)}
    cal_cache: dict[object, tuple[float, float]] = {}

    def calendar(day: object) -> tuple[float, float]:
        if day not in cal_cache:
            d = pd.Timestamp(str(day)).date()
            cal_cache[day] = (float(days_to_next_sale(d, events)), float(in_sale(d, events)))
        return cal_cache[day]

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
        sku_s = str(sku)
        age = np.array([(d - launch_by_sku[sku_s]).days for d in g["day"]], dtype=float)
        cal = np.array([calendar(d) for d in g["day"]])
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
                "age_days": age,
                "cycle_frac": age / cycle_by_cat[category_by_sku[sku_s]],
                "days_to_next_sale": cal[:, 0],
                "in_sale": cal[:, 1],
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
