"""Seeded price simulator over a FICTIONAL catalogue.

Documented assumptions (not calibrated to any real market):
- Price = launch price * (1 - annual_depreciation) ** (age_years), times (1 - promo depth)
  while a promotion is active, times small daily noise.
- Promotions start as a Bernoulli process whose rate is category_rate/30 per day, boosted in
  November (sale season) and mildly in July.
- Promotion depth ~ Beta around the category mean; duration is 3-10 days.
- PLANTED EFFECT 1 (scheduled sales): during the public sale calendar windows every product gets an
  extra markdown of `sale_depth`, so a drop is predictable from the calendar.
- PLANTED EFFECT 2 (age-based decay): permanent cuts of `cycle_cut` at ~85% and ~100% of the
  category refresh cycle (jittered +-5 days per product), as a successor model nears.
- Each product's series is a pure function of (seed, sku), so advancing the virtual clock
  only reveals more of a fixed series.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, timedelta

import numpy as np
import pandas as pd

from pricewatch.domain import CategoryConfig, PricePoint, Product, SaleEvent
from pricewatch.sales import timeline

TIMELINE_DAYS = 4000  # fixed generation length so series never depend on the clock


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _rng(seed: int, key: str) -> np.random.Generator:
    digest = hashlib.sha256(key.encode()).digest()
    return np.random.default_rng([seed, int.from_bytes(digest[:8], "big")])


def build_catalogue(configs: list[CategoryConfig], seed: int, start: date) -> list[Product]:
    """Fictional products; launch dates staggered so some predate the history window."""
    products: list[Product] = []
    for cfg in configs:
        for brand in cfg.brands:
            for n in range(1, cfg.models_per_brand + 1):
                sku = f"{cfg.id}-{_slug(brand)}-{n}"
                rng = _rng(seed, f"catalogue:{sku}")
                offset = int(rng.integers(-cfg.refresh_cycle_days, 120))
                price = float(rng.uniform(cfg.launch_price_min, cfg.launch_price_max))
                products.append(
                    Product(
                        sku=sku,
                        category=cfg.id,
                        brand=brand,
                        name=f"{brand} {cfg.name.split()[0].rstrip('s')} Sim-{n}",
                        launch_date=start + timedelta(days=offset),
                        launch_price=round(price, 2),
                    )
                )
    return products


def simulate_series(
    product: Product,
    cfg: CategoryConfig,
    seed: int,
    timeline_start: date,
    events: tuple[SaleEvent, ...] = (),
) -> pd.DataFrame:
    """Daily prices from launch date onward, over the fixed timeline."""
    rng = _rng(seed, f"prices:{product.sku}")
    tl = timeline(timeline_start, TIMELINE_DAYS, events)
    days = list(tl.days)
    boost = tl.season_boost
    base_rate = cfg.promo_rate_per_month / 30.0
    starts = rng.random(TIMELINE_DAYS) < np.minimum(base_rate * boost, 1.0)
    depth = np.zeros(TIMELINE_DAYS)
    a = 2.0
    b = a * (1 - cfg.promo_depth_mean) / cfg.promo_depth_mean
    for i in np.flatnonzero(starts):
        length = int(rng.integers(3, 11))
        d = float(rng.beta(a, b))
        end = min(i + length, TIMELINE_DAYS)
        depth[i:end] = np.maximum(depth[i:end], d)
    depth = np.where(tl.in_sale, np.maximum(depth, cfg.sale_depth), depth)
    age_days = np.array([(d - product.launch_date).days for d in days])
    age_years = age_days / 365.0
    base = product.launch_price * (1 - cfg.annual_depreciation) ** np.maximum(age_years, 0)
    cut1 = round(cfg.refresh_cycle_days * 0.85) + int(rng.integers(-5, 6))
    cut2 = cfg.refresh_cycle_days + int(rng.integers(-5, 6))
    cycle = np.where(age_days >= cut1, 1 - cfg.cycle_cut, 1.0) * np.where(
        age_days >= cut2, 1 - cfg.cycle_cut, 1.0
    )
    noise = 1 + rng.normal(0, 0.002, TIMELINE_DAYS)
    price = np.round(base * cycle * (1 - depth) * noise, 2)
    frame = pd.DataFrame({"sku": product.sku, "day": days, "price": price})
    return frame[frame["day"] >= product.launch_date].reset_index(drop=True)


def simulate_all(
    configs: list[CategoryConfig],
    seed: int,
    timeline_start: date,
    events: tuple[SaleEvent, ...] = (),
) -> tuple[list[Product], pd.DataFrame]:
    by_id = {c.id: c for c in configs}
    products = build_catalogue(configs, seed, timeline_start)
    frames = [simulate_series(p, by_id[p.category], seed, timeline_start, events) for p in products]
    return products, pd.concat(frames, ignore_index=True)


def to_price_points(frame: pd.DataFrame) -> list[PricePoint]:
    return [
        PricePoint(sku=str(sku), day=day, price=float(price))
        for sku, day, price in zip(
            frame["sku"].tolist(),
            frame["day"].tolist(),
            frame["price"].astype(float).tolist(),
            strict=True,
        )
    ]
