import numpy as np
import pandas as pd
import pytest

from pricewatch.drift import detect_drift, psi
from pricewatch.promotion import decide_promotion

COLS = ["a", "b"]


def _frame(
    rng: np.random.Generator, n: int, shift: float = 0.0, scale: float = 1.0
) -> pd.DataFrame:
    return pd.DataFrame({"a": rng.normal(shift, scale, n), "b": rng.exponential(1.0, n)})


@pytest.mark.parametrize("seed", range(20))
def test_no_false_alarm_on_same_distribution(seed: int) -> None:
    rng = np.random.default_rng(seed)
    res = detect_drift(_frame(rng, 5000), _frame(rng, 5000), COLS)
    assert not any(r.drifted for r in res), res


def test_planted_mean_shift_is_detected_only_on_shifted_column() -> None:
    rng = np.random.default_rng(1)
    res = {r.column: r for r in detect_drift(_frame(rng, 5000), _frame(rng, 5000, shift=1.0), COLS)}
    assert res["a"].drifted
    assert res["a"].psi > 0.25
    assert res["a"].ks_pvalue < 0.01
    assert not res["b"].drifted


def test_planted_variance_shift_is_detected() -> None:
    rng = np.random.default_rng(2)
    res = detect_drift(_frame(rng, 5000), _frame(rng, 5000, scale=2.5), ["a"])
    assert res[0].drifted


def test_psi_is_zero_for_identical_and_grows_with_shift() -> None:
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, 20000)
    assert psi(x, x) < 1e-6
    assert psi(x, x + 0.2) < psi(x, x + 1.0)


def _scores(seed: int, gain: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n_days, per_day = 60, 40
    groups = np.repeat(np.arange(n_days), per_day).astype(np.int64)
    truth = rng.random(n_days * per_day) < 0.3
    y = truth.astype(np.float64)
    champ = np.clip(0.3 + 0.2 * (y - 0.3) + rng.normal(0, 0.1, y.size), 0.01, 0.99)
    chall = np.clip(0.3 + (0.2 + gain) * (y - 0.3) + rng.normal(0, 0.1, y.size), 0.01, 0.99)
    return y, champ, chall, groups


def test_identical_models_are_not_promoted() -> None:
    y, champ, _, groups = _scores(0, 0.0)
    d = decide_promotion(y, champ, champ.copy(), groups)
    assert not d.promote
    assert d.mean_improvement == 0.0


def test_clearly_better_challenger_is_promoted() -> None:
    y, champ, chall, groups = _scores(1, 0.4)
    d = decide_promotion(y, champ, chall, groups)
    assert d.promote, d
    assert d.ci_low >= d.margin


def test_worse_challenger_is_not_promoted() -> None:
    y, champ, chall, groups = _scores(2, 0.4)
    d = decide_promotion(y, chall, champ, groups)  # roles swapped: challenger is worse
    assert not d.promote
    assert d.mean_improvement < 0


def test_small_but_real_gain_needs_to_clear_the_margin() -> None:
    y, champ, chall, groups = _scores(3, 0.4)
    d_low = decide_promotion(y, champ, chall, groups, margin=0.0)
    d_high = decide_promotion(y, champ, chall, groups, margin=d_low.ci_high + 0.01)
    assert d_low.promote
    assert not d_high.promote
