"""Virtual clock: one simulated day per run, with a backfilled history window."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from pricewatch.settings import Settings


def initial_day(settings: Settings) -> date:
    """Day the history ends after backfill (start + history_days)."""
    return settings.start_date + timedelta(days=settings.history_days)


def read_clock(path: Path, settings: Settings) -> date:
    if not path.exists():
        return initial_day(settings)
    return date.fromisoformat(json.loads(path.read_text(encoding="utf-8"))["today"])


def advance_clock(path: Path, settings: Settings) -> date:
    """Advance exactly one simulated day and persist it."""
    today = read_clock(path, settings) + timedelta(days=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"simulated": True, "today": today.isoformat()}), encoding="utf-8")
    return today
