from datetime import date, timedelta
from pathlib import Path

from pricewatch.clock import advance_clock, initial_day, read_clock
from pricewatch.config import load_categories
from pricewatch.settings import Settings
from pricewatch.simulator import build_catalogue, simulate_all

ROOT = Path(__file__).resolve().parent.parent
CATS = load_categories(ROOT / "configs" / "categories")
START = date(2024, 11, 1)


def test_catalogue_is_fictional_and_sized() -> None:
    products = build_catalogue(CATS, 1, START)
    assert len(products) == sum(len(c.brands) * c.models_per_brand for c in CATS)
    assert len({p.sku for p in products}) == len(products)
    assert all(p.simulated for p in products)


def test_deterministic_and_seed_sensitive() -> None:
    _, a = simulate_all(CATS, 1, START)
    _, b = simulate_all(CATS, 1, START)
    _, c = simulate_all(CATS, 2, START)
    assert a.equals(b)
    assert not a["price"].equals(c["price"])


def test_prices_positive_and_promos_occur() -> None:
    _, frame = simulate_all(CATS, 1, START)
    assert (frame["price"] > 0).all()
    one = frame[frame["sku"] == frame["sku"].iloc[0]]
    assert one["price"].min() < one["price"].rolling(30).max().max() * 0.95


def test_clock_advances_one_day(tmp_path: Path) -> None:
    s = Settings()
    path = tmp_path / "clock.json"
    assert read_clock(path, s) == initial_day(s)
    assert advance_clock(path, s) == initial_day(s) + timedelta(days=1)
    assert advance_clock(path, s) == initial_day(s) + timedelta(days=2)
