"""Environment-based settings (PRICEWATCH_* variables)."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    seed: int = 20240101
    start_date: date = date(2024, 11, 1)
    history_days: int = Field(default=730, ge=30)
    horizon_days: int = Field(default=14, ge=1)
    data_dir: Path = Path("work/data")
    config_dir: Path = Path("configs/categories")
    calendar_path: Path = Path("configs/sale_calendar.yaml")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        source = os.environ if env is None else env
        values: dict[str, str] = {}
        for name in cls.model_fields:
            raw = source.get(f"PRICEWATCH_{name.upper()}")
            if raw is not None:
                values[name] = raw
        return cls.model_validate(values)
