from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from pricewatch.config import load_categories
from pricewatch.features import FEATURE_COLUMNS, build_features
from pricewatch.leakage import find_lookahead
from pricewatch.sales import load_calendar
from pricewatch.simulator import simulate_all

Builder = Callable[[pd.DataFrame], pd.DataFrame]
ROOT = Path(__file__).resolve().parent.parent
START = date(2024, 11, 1)
CUTOFFS = [START + timedelta(days=d) for d in (200, 420, 600)]


@pytest.fixture(scope="module")
def setup() -> tuple[pd.DataFrame, Builder]:
    cats = load_categories(ROOT / "configs" / "categories")
    events = load_calendar(ROOT / "configs" / "sale_calendar.yaml")
    products, prices = simulate_all(cats, 3, START, events)
    keep = [p for p in products if p.sku.endswith("-1")][:8]  # small, fast subset
    prices = prices[prices["day"] <= START + timedelta(days=730)]
    prices = prices[prices["sku"].isin([p.sku for p in keep])]

    def builder(p: pd.DataFrame) -> pd.DataFrame:
        return build_features(p, keep, cats, events, 14)

    return prices, builder


def test_real_features_have_no_lookahead(setup: tuple[pd.DataFrame, Builder]) -> None:
    prices, builder = setup
    assert find_lookahead(builder, prices, CUTOFFS, FEATURE_COLUMNS) == []


def test_label_and_price_are_not_model_inputs() -> None:
    assert "label" not in FEATURE_COLUMNS
    assert "price" not in FEATURE_COLUMNS


def test_detector_catches_a_deliberately_leaky_feature(setup: tuple[pd.DataFrame, Builder]) -> None:
    """Proof the detector works: a feature using tomorrow's price must be flagged."""
    prices, builder = setup

    def leaky(p: pd.DataFrame) -> pd.DataFrame:
        f = builder(p).copy()
        f["leak_next_ratio"] = f.groupby("sku")["price"].transform(lambda s: s.shift(-1) / s)
        return f

    problems = find_lookahead(leaky, prices, CUTOFFS, [*FEATURE_COLUMNS, "leak_next_ratio"])
    assert any(line.startswith("leak_next_ratio") for line in problems), problems
    # and only the leaky column is flagged
    assert all(line.startswith("leak_next_ratio") for line in problems)
