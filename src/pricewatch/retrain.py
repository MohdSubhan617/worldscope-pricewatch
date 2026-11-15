"""Weekly retrain: fit a challenger, compare with the champion, promote only by policy."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from pricewatch.clock import read_clock
from pricewatch.drift import DriftResult, detect_drift
from pricewatch.model import CalibratedModel, brier, fit
from pricewatch.pipeline import DISCLAIMER, labelled_features
from pricewatch.promotion import PromotionDecision, decide_promotion
from pricewatch.settings import Settings

DRIFT_COLUMNS = [
    "ratio_max90",
    "ratio_min90",
    "ret_7",
    "vol_30",
    "promo_days_90",
    "days_since_promo",
]
CHAMPION_FILE = "champion.joblib"
REPORT_FILE = "last_retrain.json"


@dataclass
class Champion:
    model: CalibratedModel
    trained_through: date


def load_champion(models_dir: Path) -> Champion | None:
    path = models_dir / CHAMPION_FILE
    if not path.exists():
        return None
    obj = joblib.load(path)  # trusted: written only by this pipeline into our own data branch
    return Champion(obj["model"], obj["trained_through"])


def save_champion(models_dir: Path, champion: Champion) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": champion.model, "trained_through": champion.trained_through},
        models_dir / CHAMPION_FILE,
    )


@dataclass
class RetrainReport:
    as_of: str
    action: str  # "promoted-initial" | "promoted" | "kept-champion"
    challenger_trained_through: str
    champion_trained_through: str | None
    decision: PromotionDecision | None
    drift: list[DriftResult]
    holdout_brier_champion: float | None
    holdout_brier_challenger: float


def _days(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["day"]).dt.date


def retrain(
    settings: Settings,
    state_dir: Path,
    holdout_days: int = 60,
    embargo: int = 7,
    cal_days: int = 90,
    margin: float = 0.002,
    n_boot: int = 2000,
) -> RetrainReport:
    models_dir = state_dir / "models"
    today = read_clock(state_dir / "clock.json", settings)
    h = settings.horizon_days
    labelled = labelled_features(settings, today)
    d = _days(labelled)
    last_label = d.max()
    holdout_start = last_label - timedelta(days=holdout_days)
    train_end = holdout_start - timedelta(days=h + embargo)
    cal_start = train_end - timedelta(days=cal_days)
    fit_part = labelled[d <= cal_start - timedelta(days=h)]
    cal = labelled[(d >= cal_start) & (d <= train_end)]
    holdout = labelled[d > holdout_start]
    challenger = Champion(fit(fit_part, cal, settings.seed), train_end)

    y = holdout["label"].to_numpy(dtype=np.float64)
    p_new = challenger.model.predict_proba(holdout)
    champion = load_champion(models_dir)
    ref = labelled[
        (d >= (champion.trained_through if champion else cal_start) - timedelta(days=holdout_days))
        & (d <= (champion.trained_through if champion else train_end))
    ]
    drift = detect_drift(ref, holdout, DRIFT_COLUMNS)

    decision: PromotionDecision | None = None
    champ_brier: float | None = None
    if champion is None:
        action = "promoted-initial"
        save_champion(models_dir, challenger)
    else:
        p_old = champion.model.predict_proba(holdout)
        champ_brier = brier(y, p_old)
        groups = np.array([x.toordinal() for x in _days(holdout)], dtype=np.int64)
        decision = decide_promotion(
            y, p_old, p_new, groups, margin=margin, n_boot=n_boot, seed=settings.seed
        )
        action = "promoted" if decision.promote else "kept-champion"
        if decision.promote:
            save_champion(models_dir, challenger)
    report = RetrainReport(
        as_of=today.isoformat(),
        action=action,
        challenger_trained_through=train_end.isoformat(),
        champion_trained_through=champion.trained_through.isoformat() if champion else None,
        decision=decision,
        drift=drift,
        holdout_brier_champion=champ_brier,
        holdout_brier_challenger=brier(y, p_new),
    )
    payload: dict[str, Any] = {"simulated": True, "disclaimer": DISCLAIMER, **asdict(report)}
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / REPORT_FILE).write_text(
        json.dumps(payload, indent=1, default=str), encoding="utf-8"
    )
    return report
