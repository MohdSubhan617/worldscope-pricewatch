"""Scheduled sale calendar (a planted, documented simulator effect) and its derived features."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml
from numpy.typing import NDArray

from pricewatch.domain import SaleEvent

CAP_DAYS = 365


def load_calendar(path: Path) -> tuple[SaleEvent, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return tuple(SaleEvent.model_validate(e) for e in raw["events"])


def _starts_near(day: date, events: tuple[SaleEvent, ...]) -> list[date]:
    out: list[date] = []
    for year in (day.year - 1, day.year, day.year + 1):
        out += [date(year, e.month, e.day) for e in events]
    return out


def in_sale(day: date, events: tuple[SaleEvent, ...]) -> bool:
    return any(
        s <= day < s + timedelta(days=e.duration_days)
        for e in events
        for s in [date(y, e.month, e.day) for y in (day.year - 1, day.year)]
    )


def days_to_next_sale(day: date, events: tuple[SaleEvent, ...]) -> int:
    """Days until the next sale starts (0 on a start day); 0 while inside a sale."""
    if in_sale(day, events):
        return 0
    gaps = [(s - day).days for s in _starts_near(day, events) if s >= day]
    return min(min(gaps, default=CAP_DAYS), CAP_DAYS)


@dataclass(frozen=True)
class Timeline:
    days: tuple[date, ...]
    in_sale: NDArray[np.bool_]
    to_next: NDArray[np.float64]
    season_boost: NDArray[np.float64]


@lru_cache(maxsize=8)
def timeline(start: date, length: int, events: tuple[SaleEvent, ...]) -> Timeline:
    days = tuple(start + timedelta(days=i) for i in range(length))
    flags = np.array([in_sale(d, events) for d in days], dtype=np.bool_)
    gaps = np.array([days_to_next_sale(d, events) for d in days], dtype=np.float64)
    boost = np.array([2.5 if d.month == 11 else 1.4 if d.month == 7 else 1.0 for d in days])
    return Timeline(days, flags, gaps, boost)
