from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from pricewatch.config import load_categories
from pricewatch.domain import Prediction, PricePoint
from pricewatch.settings import Settings

ROOT = Path(__file__).resolve().parent.parent


def test_five_categories_load() -> None:
    cats = load_categories(ROOT / "configs" / "categories")
    assert {c.id for c in cats} == {"phones", "laptops", "audio", "tablets", "smartwatches"}
    assert all(c.launch_price_min < c.launch_price_max for c in cats)


def test_records_are_always_simulated() -> None:
    p = PricePoint(sku="x", day=date(2024, 1, 1), price=10.0)
    assert p.simulated is True
    with pytest.raises(ValidationError):
        PricePoint.model_validate({"sku": "x", "day": "2024-01-01", "price": 1, "simulated": False})


def test_probability_bounds() -> None:
    with pytest.raises(ValidationError):
        Prediction(sku="x", as_of=date(2024, 1, 1), horizon_days=14, probability=1.5)


def test_settings_from_env() -> None:
    s = Settings.from_env({"PRICEWATCH_SEED": "7", "PRICEWATCH_HISTORY_DAYS": "60"})
    assert (s.seed, s.history_days, s.horizon_days) == (7, 60, 14)
