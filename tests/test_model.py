from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from pricewatch.features import FEATURE_COLUMNS
from pricewatch.model import expected_calibration_error, reliability, split_by_time
from tests.world import AS_OF, HORIZON, World, make_world

# Stated margin: with the planted effects present, the model must cut the Brier score by at
# least this fraction relative to the oracle constant (test-set base rate) predictor.
MIN_RELATIVE_BRIER_GAIN = 0.25


def _days(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["day"]).dt.date


@pytest.fixture(scope="module")
def world() -> World:
    return make_world(5)


def test_features_have_no_future_leak(world: World) -> None:
    tail = world.feats[_days(world.feats) > AS_OF - timedelta(days=HORIZON)]
    assert tail["label"].isna().all()
    assert not world.feats[FEATURE_COLUMNS].isna().any().any()


def test_split_is_chronological_and_gapped(world: World) -> None:
    train, cal, test = split_by_time(world.feats.dropna(subset=["label"]), AS_OF, HORIZON)
    assert _days(train).max() + timedelta(days=HORIZON) <= _days(cal).min()
    assert _days(cal).max() + timedelta(days=HORIZON) <= _days(test).min()


@pytest.mark.slow
def test_planted_effects_are_recovered_by_stated_margin(world: World) -> None:
    gain = world.relative_brier_gain()
    assert gain >= MIN_RELATIVE_BRIER_GAIN, (
        f"planted effects NOT recovered: relative Brier gain {gain:.3f} "
        f"< required {MIN_RELATIVE_BRIER_GAIN}"
    )
    assert expected_calibration_error(reliability(world.y, world.probs)) < 0.05


@pytest.mark.slow
def test_model_predicts_a_drop_before_scheduled_sales(world: World) -> None:
    t = world.test.assign(p=world.probs)
    before = t[(t["in_sale"] == 0) & t["days_to_next_sale"].between(1, 10)]
    far = t[(t["in_sale"] == 0) & (t["days_to_next_sale"] > 60)]
    assert len(before) > 100
    assert len(far) > 100
    assert before["p"].mean() > 1.5 * far["p"].mean()


@pytest.mark.slow
def test_recovery_check_fails_without_planted_effects() -> None:
    """Negative control: with the effects switched off the same margin must NOT be met."""
    control = make_world(5, planted=False)
    assert control.relative_brier_gain() < MIN_RELATIVE_BRIER_GAIN
    assert np.isfinite(control.relative_brier_gain())
