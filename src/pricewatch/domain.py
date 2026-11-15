"""Domain schemas. All data is simulated; the flag is part of every record."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CategoryConfig(Frozen):
    """Config-driven category definition (loaded from YAML)."""

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    brands: list[str] = Field(min_length=1)
    models_per_brand: int = Field(ge=1)
    launch_price_min: float = Field(gt=0)
    launch_price_max: float = Field(gt=0)
    annual_depreciation: float = Field(ge=0, lt=1)
    promo_rate_per_month: float = Field(ge=0, le=1)
    promo_depth_mean: float = Field(gt=0, lt=1)
    refresh_cycle_days: int = Field(ge=30)


class Product(Frozen):
    simulated: Literal[True] = True
    sku: str
    category: str
    brand: str
    name: str
    launch_date: date
    launch_price: float = Field(gt=0)


class PricePoint(Frozen):
    simulated: Literal[True] = True
    sku: str
    day: date
    price: float = Field(gt=0)


class Prediction(Frozen):
    simulated: Literal[True] = True
    sku: str
    as_of: date
    horizon_days: int = Field(ge=1)
    probability: float = Field(ge=0, le=1)
