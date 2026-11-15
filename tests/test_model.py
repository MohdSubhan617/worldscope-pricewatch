from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pricewatch.config import load_categories
from pricewatch.features import FEATURE_COLUMNS, build_features
from pricewatch.model import brier, expected_calibration_error, fit, reliability, split_by_time
from pricewatch.simulator import simulate_all

ROOT = Path(__file__).resolve().parent.parent
START = date(2024, 11, 1)
HORIZON = 14


def _days(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["day"]).dt.date


@pytest.fixture(scope="module")
def world() -> tuple[pd.DataFrame, date]:
    cats = load_categories(ROOT / "configs" / "categories")
    products, prices = simulate_all(cats, 5, START)
    as_of = START + timedelta(days=730)
    prices = prices[prices["day"] <= as_of]
    feats = build_features(prices, {p.sku: p.category for p in products}, HORIZON)
    return feats, as_of


def test_features_have_no_future_leak(world: tuple[pd.DataFrame, date]) -> None:
    feats, as_of = world
    tail = feats[_days(feats) > as_of - timedelta(days=HORIZON)]
    assert tail["label"].isna().all()
    assert not feats[FEATURE_COLUMNS].isna().any().any()


def test_split_is_chronological_and_gapped(world: tuple[pd.DataFrame, date]) -> None:
    feats, as_of = world
    train, cal, test = split_by_time(feats.dropna(subset=["label"]), as_of, HORIZON)
    assert _days(train).max() + timedelta(days=HORIZON) <= _days(cal).min()
    assert _days(cal).max() + timedelta(days=HORIZON) <= _days(test).min()


@pytest.mark.slow
def test_model_is_calibrated_and_beats_base_rate(world: tuple[pd.DataFrame, date]) -> None:
    feats, as_of = world
    train, cal, test = split_by_time(feats.dropna(subset=["label"]), as_of, HORIZON)
    model = fit(train, cal, seed=5)
    p = model.predict_proba(test)
    y = test["label"].to_numpy(dtype=np.float64)
    assert brier(y, p) < brier(y, np.full_like(y, y.mean()))
    assert expected_calibration_error(reliability(y, p)) < 0.08
