import itertools
from datetime import timedelta

import pandas as pd
import pytest

from pricewatch.backtest import (
    FoldResult,
    log_loss,
    plan_folds,
    render_markdown,
    run_backtest,
)
from tests.world import AS_OF, HORIZON, START, World, make_world

EMBARGO = 7


def _days(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["day"]).dt.date


def test_plan_has_purge_and_embargo_and_ordered_disjoint_tests() -> None:
    last = AS_OF - timedelta(days=HORIZON)
    plans = plan_folds(last, START, folds=6, test_days=45, purge=HORIZON, embargo=EMBARGO)
    assert len(plans) == 6
    for p in plans:
        assert p.train_end + timedelta(days=HORIZON + EMBARGO) < p.test_start
    for a, b in itertools.pairwise(plans):
        assert a.test_end < b.test_start
    assert plans[-1].test_end == last


def test_plan_rejects_too_little_training_data() -> None:
    with pytest.raises(ValueError, match="training days"):
        plan_folds(START + timedelta(days=200), START, folds=6)


def test_log_loss_is_finite_at_extremes() -> None:
    import numpy as np

    y = np.array([0.0, 1.0])
    assert log_loss(y, np.array([0.0, 1.0])) < 1e-4


@pytest.fixture(scope="module")
def results() -> tuple[World, list[FoldResult]]:
    w = make_world(5)
    return w, run_backtest(w.feats.dropna(subset=["label"]), seed=5, embargo=EMBARGO)


@pytest.mark.slow
def test_backtest_beats_base_rate_in_every_fold_on_planted_world(
    results: tuple[World, list[FoldResult]],
) -> None:
    _, res = results
    assert len(res) == 6
    assert all(r.model.brier < r.base_rate.brier for r in res)
    assert all(r.rows_test > 500 for r in res)


@pytest.mark.slow
def test_backtest_folds_never_train_on_test_labels(
    results: tuple[World, list[FoldResult]],
) -> None:
    w, res = results
    feats = w.feats.dropna(subset=["label"])
    d = _days(feats)
    for r in res:
        train_rows = feats[d <= r.plan.train_end]
        assert _days(train_rows).max() + timedelta(days=HORIZON + EMBARGO) < r.plan.test_start


@pytest.mark.slow
def test_markdown_is_generated_from_results(results: tuple[World, list[FoldResult]]) -> None:
    _, res = results
    md = render_markdown(res, seed=5, horizon=HORIZON, embargo=EMBARGO, elapsed=1.0)
    assert "SIMULATED" in md
    assert f"{res[0].model.brier:.4f}" in md
    assert md.count("\n| ") >= len(res)
