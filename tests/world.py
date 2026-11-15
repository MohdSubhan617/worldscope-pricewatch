"""Shared test world: simulate, featurise, split, fit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from pricewatch.config import load_categories
from pricewatch.features import build_features
from pricewatch.model import CalibratedModel, brier, fit, split_by_time
from pricewatch.sales import load_calendar
from pricewatch.simulator import simulate_all

ROOT = Path(__file__).resolve().parent.parent
START = date(2024, 11, 1)
HORIZON = 14
AS_OF = START + timedelta(days=730)


@dataclass
class World:
    feats: pd.DataFrame
    train: pd.DataFrame
    cal: pd.DataFrame
    test: pd.DataFrame
    model: CalibratedModel
    probs: NDArray[np.float64]

    @property
    def y(self) -> NDArray[np.float64]:
        return self.test["label"].to_numpy(dtype=np.float64)

    def relative_brier_gain(self) -> float:
        """Relative Brier reduction vs the stricter oracle constant (test-set base rate)."""
        base = brier(self.y, np.full_like(self.y, self.y.mean()))
        return (base - brier(self.y, self.probs)) / base


def make_world(seed: int, planted: bool = True) -> World:
    cats = load_categories(ROOT / "configs" / "categories")
    if not planted:
        cats = [c.model_copy(update={"sale_depth": 0.0, "cycle_cut": 0.0}) for c in cats]
    events = load_calendar(ROOT / "configs" / "sale_calendar.yaml")
    products, prices = simulate_all(cats, seed, START, events)
    prices = prices[prices["day"] <= AS_OF]
    feats = build_features(prices, products, cats, events, HORIZON)
    train, cal, test = split_by_time(feats.dropna(subset=["label"]), AS_OF, HORIZON)
    model = fit(train, cal, seed)
    return World(feats, train, cal, test, model, model.predict_proba(test))
